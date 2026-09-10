# -*- coding: utf-8 -*-
"""tools/codex_worker_launch.py の fake Codex executable 回帰。"""
from __future__ import annotations

import importlib.util
import fcntl
import hashlib
import inspect
import json
import math
import os
import queue
import re
import signal
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_LAUNCHER = _ROOT / "tools" / "codex_worker_launch.py"
_REAL_EVENT_FIXTURES = (
    _ROOT / "orchestrator" / "tests" / "fixtures" / "codex_worker_launch"
)
_BASE_COMMIT = subprocess.run(
    ["git", "-C", os.fspath(_ROOT), "rev-parse", "HEAD"],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
).stdout.strip()
_SPEC = importlib.util.spec_from_file_location(
    "codex_worker_launch_under_test", _LAUNCHER
)
assert _SPEC and _SPEC.loader
LAUNCHER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = LAUNCHER
_SPEC.loader.exec_module(LAUNCHER)

_DIAGNOSTIC_MAX_BYTES = 16 * 1024
_STREAM_EXCERPT_BYTES = 2048
_STREAM_READ_MAX_BYTES = 64 * 1024
_RECEIPT_MAX_BYTES = LAUNCHER._MAX_JSON_BYTES
_TRUTH_SUMMARY_MAX_BYTES = 4096
_EXPECTED_TRUST_BYPASS_FLAG = "--dangerously-bypass-hook-trust"
_FAILURE_ARTIFACT_ROOT = _ROOT / "output/runs/pytest-launcher-failures"
_SNAPSHOT_MAX_FILES = 4096
_SNAPSHOT_MAX_BYTES = 256 * 1024 * 1024
_FAILURE_RUN_MAX_BUNDLES = 21
_FAILURE_RUN_MAX_ENTRIES = 16 * 1024
_FAILURE_RUN_MAX_BYTES = 512 * 1024 * 1024
_FAILURE_BUNDLE_METADATA_RESERVE_BYTES = 64 * 1024
_EXCEPTION_MESSAGE_MAX_CHARS = 2048
_LIVE_WIRING_PROBE_ENV = "IZANAGI_LAUNCHER_FAILURE_LIVE_PROBE"
_LIVE_ARCHIVE_FAILURE_PROBE_ENV = (
    "IZANAGI_LAUNCHER_FAILURE_ARCHIVE_ERROR_PROBE"
)


class LauncherReturncodeMismatch(AssertionError):
    """launcher の一次 rc 不一致を診断生成エラーから区別する。"""


class _DiagnosticFileError(RuntimeError):
    """診断対象を blocking/無制限 I/O なしには読めない。"""

    def __init__(self, reason: str, *, total_bytes: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.total_bytes = total_bytes


def _archive_component(value: str) -> str:
    rendered = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return (rendered or "unknown")[:128]


def _failure_run_directory() -> Path:
    pbs_job_id = os.environ.get("PBS_JOBID", "local")
    return _FAILURE_ARTIFACT_ROOT / (
        f"{_archive_component(pbs_job_id)}--"
        f"{_archive_component(socket.gethostname())}"
    )


def _paths_have_ancestor_relationship(first: Path, second: Path) -> bool:
    first_resolved = first.resolve()
    second_resolved = second.resolve()
    return (
        first_resolved == second_resolved
        or first_resolved in second_resolved.parents
        or second_resolved in first_resolved.parents
    )


def _write_archive_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def _snapshot_tmp_path(
    source: Path,
    destination: Path,
    *,
    max_files: int | None = None,
    max_bytes: int | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    if _paths_have_ancestor_relationship(source, destination):
        raise ValueError("snapshot source/destination ancestor relationship")
    if max_files is None:
        max_files = _SNAPSHOT_MAX_FILES
    if max_bytes is None:
        max_bytes = _SNAPSHOT_MAX_BYTES
    if max_files < 0 or max_bytes < 0:
        raise ValueError("snapshot limits must be non-negative")
    snapshot_root = destination / "tmp_path"
    snapshot_root.mkdir(mode=0o700)
    entries: list[dict[str, Any]] = []
    path_map = {os.fspath(source.absolute()): "tmp_path"}
    files_seen = 0
    bytes_copied = 0
    search_complete = True
    candidates: list[
        tuple[int, str, Path, Path, os.stat_result, dict[str, Any], str | None]
    ] = []
    pending_directories: list[tuple[Path, Path]] = [(source, Path())]

    def critical_kind(relative: Path, metadata: os.stat_result) -> str | None:
        if not stat.S_ISREG(metadata.st_mode):
            return None
        name = relative.name
        if name.startswith("launcher-diagnostics.") and name.endswith(".json"):
            return "launcher-sidecar"
        if re.fullmatch(r"attempt-[0-9]+\.events\.jsonl", name):
            return "attempt-events"
        if re.fullmatch(r"attempt-[0-9]+\.stderr\.log", name):
            return "attempt-stderr"
        if re.fullmatch(r"attempt-[0-9]+\.output\.md", name):
            return "attempt-output"
        if name.startswith("receipt") and name.endswith(".json"):
            return "receipt"
        if name.startswith("manifest") and name.endswith(".json"):
            return "manifest"
        return None

    while pending_directories and files_seen < max_files:
        source_dir, relative_dir = pending_directories.pop()
        remaining = max_files - files_seen
        try:
            with os.scandir(source_dir) as iterator:
                children = []
                for child in iterator:
                    children.append(child)
                    if len(children) > remaining:
                        break
        except OSError as exc:
            search_complete = False
            entries.append(
                {
                    "path": relative_dir.as_posix(),
                    "kind": "directory",
                    "status": "omitted",
                    "reason": f"scandir-error:{type(exc).__name__}",
                }
            )
            continue
        over_limit = len(children) > remaining
        selected_children = sorted(
            children, key=lambda item: item.name
        )[:remaining]
        for child in selected_children:
            files_seen += 1
            source_path = source_dir / child.name
            relative = relative_dir / child.name
            try:
                metadata = child.stat(follow_symlinks=False)
            except OSError as exc:
                search_complete = False
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "kind": "unknown",
                        "status": "omitted",
                        "reason": f"lstat-error:{type(exc).__name__}",
                    }
                )
                continue
            if stat.S_ISDIR(metadata.st_mode):
                pending_directories.append((source_path, relative))
                continue
            kind = (
                "regular"
                if stat.S_ISREG(metadata.st_mode)
                else "symlink"
                if stat.S_ISLNK(metadata.st_mode)
                else "special-file"
            )
            record: dict[str, Any] = {
                "path": relative.as_posix(),
                "kind": kind,
                "status": "omitted",
            }
            if kind == "special-file":
                record["reason"] = "special-file"
            else:
                critical = critical_kind(relative, metadata)
                candidates.append(
                    (
                        0 if critical is not None else 1,
                        relative.as_posix(),
                        source_path,
                        relative,
                        metadata,
                        record,
                        critical,
                    )
                )
            entries.append(record)
        if over_limit:
            search_complete = False
            pending_directories.clear()
            entries.append(
                {
                    "path": relative_dir.as_posix() or ".",
                    "kind": "subtree",
                    "status": "omitted",
                    "reason": "file-count-limit",
                }
            )

    if pending_directories:
        search_complete = False
        entries.append(
            {
                "path": ".",
                "kind": "subtree",
                "status": "omitted",
                "reason": "file-count-limit",
            }
        )

    critical_seen = 0
    critical_copied = 0
    critical_kinds_seen: set[str] = set()
    for (
        _priority,
        _sort_path,
        source_path,
        relative,
        metadata,
        record,
        critical,
    ) in sorted(candidates, key=lambda item: (item[0], item[1])):
        if critical is not None:
            critical_seen += 1
            critical_kinds_seen.add(critical)
        if stat.S_ISREG(metadata.st_mode) and (
            bytes_copied + metadata.st_size > max_bytes
        ):
            record["reason"] = "total-bytes-limit"
            continue
        destination_path = snapshot_root / relative
        try:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            if stat.S_ISLNK(metadata.st_mode):
                os.symlink(os.readlink(source_path), destination_path)
            else:
                shutil.copyfile(
                    source_path,
                    destination_path,
                    follow_symlinks=False,
                )
                bytes_copied += metadata.st_size
            record["status"] = "copied"
            record["bytes"] = metadata.st_size
            mapped = (Path("tmp_path") / relative).as_posix()
            path_map[os.fspath(source_path.absolute())] = mapped
            if critical is not None:
                critical_copied += 1
        except BaseException as exc:
            record["reason"] = f"copy-error:{type(exc).__name__}"

    omitted = sum(item["status"] != "copied" for item in entries)
    return (
        {
            "schema": "pytest-launcher-failure-snapshot-manifest/v1",
            "limits": {
                "max_files": max_files,
                "max_bytes": max_bytes,
            },
            "files_seen": files_seen,
            "bytes_copied": bytes_copied,
            "omitted_count": omitted,
            "entries": entries,
            "search_complete": search_complete,
            "critical_set_complete": (
                search_complete and critical_seen == critical_copied
            ),
            "critical_files_seen": critical_seen,
            "critical_files_copied": critical_copied,
            "critical_kinds_seen": sorted(critical_kinds_seen),
            "diagnostics_present": "launcher-sidecar" in critical_kinds_seen,
            "launcher_artifacts_present": bool(critical_kinds_seen),
        },
        path_map,
    )


def _exception_chain_contains_timeout(exc: BaseException | None) -> bool:
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if isinstance(exc, subprocess.TimeoutExpired):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def _append_failure_index(run_dir: Path, value: dict[str, Any]) -> None:
    raw = (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    index_path = run_dir / "index.jsonl"
    fd = os.open(
        index_path,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        0o600,
    )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _failure_run_usage(run_dir: Path) -> tuple[int, int, int, str | None]:
    """Return bundle/entry/byte usage, stopping as soon as a cap is crossed."""
    bundles = 0
    entries_seen = 0
    total_bytes = 0
    if bundles >= _FAILURE_RUN_MAX_BUNDLES:
        return bundles, entries_seen, total_bytes, "run-bundle-limit"
    pending = [(run_dir, 0)]
    while pending:
        directory, depth = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                for child in iterator:
                    entries_seen += 1
                    if entries_seen >= _FAILURE_RUN_MAX_ENTRIES:
                        return (
                            bundles,
                            entries_seen,
                            total_bytes,
                            "run-entry-limit",
                        )
                    try:
                        metadata = child.stat(follow_symlinks=False)
                    except OSError:
                        return (
                            bundles,
                            entries_seen,
                            total_bytes,
                            "run-usage-unreadable",
                        )
                    if stat.S_ISDIR(metadata.st_mode):
                        if depth == 1:
                            bundles += 1
                            if bundles >= _FAILURE_RUN_MAX_BUNDLES:
                                return (
                                    bundles,
                                    entries_seen,
                                    total_bytes,
                                    "run-bundle-limit",
                                )
                        pending.append((Path(child.path), depth + 1))
                    elif stat.S_ISREG(metadata.st_mode):
                        total_bytes += metadata.st_size
                        if total_bytes >= _FAILURE_RUN_MAX_BYTES:
                            return (
                                bundles,
                                entries_seen,
                                total_bytes,
                                "run-byte-limit",
                            )
        except OSError:
            return bundles, entries_seen, total_bytes, "run-usage-unreadable"
    return bundles, entries_seen, total_bytes, None


def _metadata_only_snapshot(reason: str) -> tuple[dict[str, Any], dict[str, str]]:
    return (
        {
            "schema": "pytest-launcher-failure-snapshot-manifest/v1",
            "limits": {
                "max_files": _SNAPSHOT_MAX_FILES,
                "max_bytes": _SNAPSHOT_MAX_BYTES,
            },
            "files_seen": 0,
            "bytes_copied": 0,
            "omitted_count": 1,
            "entries": [
                {
                    "path": ".",
                    "kind": "subtree",
                    "status": "omitted",
                    "reason": reason,
                }
            ],
            "search_complete": False,
            "critical_set_complete": False,
            "critical_files_seen": 0,
            "critical_files_copied": 0,
            "critical_kinds_seen": [],
            "diagnostics_present": False,
            "launcher_artifacts_present": False,
        },
        {},
    )


def _bounded_exception_fields(
    exception: BaseException | None,
) -> tuple[str | None, str | None, bool]:
    if exception is None:
        return None, None, False
    exception_type = (
        f"{type(exception).__module__}.{type(exception).__qualname__}"[:256]
    )
    try:
        message = str(exception)
    except BaseException as exc:
        message = f"<message-unavailable:{type(exc).__name__}>"
    truncated = len(message) > _EXCEPTION_MESSAGE_MAX_CHARS
    if truncated:
        message = message[:_EXCEPTION_MESSAGE_MAX_CHARS]
    return exception_type, message, truncated


def _diagnostics_absence_reason(
    *,
    source_live: bool,
    manifest: dict[str, Any],
) -> str | None:
    if manifest["diagnostics_present"]:
        return None
    if source_live:
        return "call-timeout-before-diagnostics"
    if not manifest["search_complete"]:
        return "diagnostics-search-incomplete"
    if manifest["launcher_artifacts_present"]:
        return "launcher-artifacts-without-diagnostics"
    return "no-launcher-artifacts-observed"


def _archive_launcher_failure(
    *,
    nodeid: str,
    tmp_path: Path,
    exception: BaseException | None,
    call_duration_s: float | None = None,
) -> Path:
    run_dir = _failure_run_directory()
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    run_dir.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(
        run_dir / ".archive.lock", os.O_WRONLY | os.O_CREAT, 0o600
    )
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        _bundles, run_entries, run_bytes, budget_reason = (
            _failure_run_usage(run_dir)
        )
        if (
            budget_reason is None
            and run_entries + 8 >= _FAILURE_RUN_MAX_ENTRIES
        ):
            budget_reason = "run-entry-limit"
        if (
            budget_reason is None
            and run_bytes + _FAILURE_BUNDLE_METADATA_RESERVE_BYTES
            >= _FAILURE_RUN_MAX_BYTES
        ):
            budget_reason = "run-byte-limit"
        worker_dir = run_dir / _archive_component(worker)
        worker_dir.mkdir(parents=True, exist_ok=True)
        node_digest = hashlib.sha256(nodeid.encode("utf-8")).hexdigest()[:16]
        leaf = Path(
            tempfile.mkdtemp(
                prefix=(
                    f"{node_digest}--pid{os.getpid()}--{time.time_ns()}--"
                ),
                dir=worker_dir,
            )
        )
        if budget_reason is None:
            available_entries = _FAILURE_RUN_MAX_ENTRIES - run_entries - 8
            available_bytes = (
                _FAILURE_RUN_MAX_BYTES
                - run_bytes
                - _FAILURE_BUNDLE_METADATA_RESERVE_BYTES
            )
            manifest, path_map = _snapshot_tmp_path(
                tmp_path,
                leaf,
                max_files=min(_SNAPSHOT_MAX_FILES, available_entries),
                max_bytes=min(_SNAPSHOT_MAX_BYTES, available_bytes),
            )
        else:
            manifest, path_map = _metadata_only_snapshot(budget_reason)
        source_live = _exception_chain_contains_timeout(exception)
        incomplete = source_live or manifest["omitted_count"] != 0
        exception_type, exception_message, message_truncated = (
            _bounded_exception_fields(exception)
        )
        duration = (
            call_duration_s
            if isinstance(call_duration_s, (int, float))
            and not isinstance(call_duration_s, bool)
            and math.isfinite(call_duration_s)
            and call_duration_s >= 0
            else None
        )
        metadata = {
            "schema": "pytest-launcher-failure-metadata/v1",
            "nodeid": nodeid,
            "worker": worker,
            "pbs_jobid": os.environ.get("PBS_JOBID"),
            "hostname": socket.gethostname(),
            "source_live": source_live,
            "snapshot_consistency": (
                "incomplete" if incomplete else "best-effort"
            ),
            "run_budget_mode": (
                "metadata-only" if budget_reason is not None else "snapshot"
            ),
            "run_budget_reason": budget_reason,
            "critical_set_complete": manifest["critical_set_complete"],
            "diagnostics_present": manifest["diagnostics_present"],
            "diagnostics_absence_reason": _diagnostics_absence_reason(
                source_live=source_live, manifest=manifest
            ),
            "exception_type": exception_type,
            "exception_message": exception_message,
            "exception_message_truncated": message_truncated,
            "call_duration_s": duration,
        }
        _write_archive_json(leaf / "metadata.json", metadata)
        _write_archive_json(leaf / "snapshot-manifest.json", manifest)
        _write_archive_json(
            leaf / "path-map.json",
            {
                "schema": "pytest-launcher-failure-path-map/v1",
                "paths": path_map,
            },
        )
        bundle_relative = leaf.relative_to(run_dir).as_posix()
        _append_failure_index(
            run_dir,
            {
                "nodeid": nodeid,
                "worker": worker,
                "pbs_jobid": os.environ.get("PBS_JOBID"),
                "bundle": bundle_relative,
                "time_ns": time.time_ns(),
            },
        )
        (leaf / ".complete").write_bytes(b"complete\n")
        return leaf
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def _archive_launcher_failure_without_masking(
    *,
    nodeid: str,
    tmp_path: Path,
    exception: BaseException | None,
    call_duration_s: float | None = None,
) -> str:
    try:
        bundle = _archive_launcher_failure(
            nodeid=nodeid,
            tmp_path=tmp_path,
            exception=exception,
            call_duration_s=call_duration_s,
        )
    except BaseException as exc:
        return f"archive_status=failed:{type(exc).__name__}"
    return f"archive_status=complete bundle={bundle}"


class _LauncherFailureArtifactPlugin:
    def __init__(self, tmp_path: Path | None = None) -> None:
        self.tmp_path = tmp_path

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_makereport(self, item: Any, call: Any) -> None:
        if call.when != "call" or call.excinfo is None:
            return
        tmp_path = self.tmp_path or item.funcargs.get("tmp_path")
        if not isinstance(tmp_path, Path):
            return
        exception = call.excinfo.value
        status = _archive_launcher_failure_without_masking(
            nodeid=item.nodeid,
            tmp_path=tmp_path,
            exception=exception,
            call_duration_s=getattr(call, "duration", None),
        )
        item.add_report_section("call", "launcher-failure-artifact", status)


@pytest.fixture(autouse=True)
def _launcher_failure_artifact_reporter(
    request: pytest.FixtureRequest,
) -> Any:
    plugin = _LauncherFailureArtifactPlugin()
    name = f"launcher-failure-artifact-{uuid.uuid4().hex}"
    request.config.pluginmanager.register(plugin, name)
    try:
        yield plugin
    finally:
        request.config.pluginmanager.unregister(plugin)


def _short_repr(value: Any, limit: int = 160) -> str:
    rendered = repr(value)
    if len(rendered) <= limit:
        return rendered
    return rendered[: limit - 3] + "..."


def _excerpt_bytes(
    payload: bytes, limit: int = _STREAM_EXCERPT_BYTES
) -> tuple[bytes, int]:
    if len(payload) <= limit:
        return payload, 0
    head = limit // 2
    tail = limit - head
    return payload[:head] + payload[-tail:], len(payload) - limit


def _stream_diagnostic_from_bytes(label: str, payload: bytes, path: str) -> str:
    excerpt, truncated = _excerpt_bytes(payload)
    rendered = excerpt.decode("utf-8", errors="backslashreplace")
    return (
        f"{label}: path={path!r} total_bytes={len(payload)} "
        f"sha256={hashlib.sha256(payload).hexdigest()} "
        f"truncated_bytes={truncated} excerpt={rendered!r}"
    )


def _read_regular_file_bounded(path: Path, *, max_bytes: int) -> bytes:
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode):
        raise _DiagnosticFileError("symlink", total_bytes=metadata.st_size)
    if not stat.S_ISREG(metadata.st_mode):
        raise _DiagnosticFileError("non-regular", total_bytes=metadata.st_size)
    if metadata.st_size > max_bytes:
        raise _DiagnosticFileError("too-large", total_bytes=metadata.st_size)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino)
            != (metadata.st_dev, metadata.st_ino)
        ):
            raise _DiagnosticFileError(
                "changed-or-non-regular", total_bytes=opened.st_size
            )
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(fd, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > max_bytes:
            raise _DiagnosticFileError(
                "too-large", total_bytes=max(metadata.st_size, len(payload))
            )
        return payload
    finally:
        os.close(fd)


def _stream_diagnostic_from_path(
    label: str,
    raw_path: Any,
    artifact_dir: Path,
) -> str:
    if not isinstance(raw_path, str):
        return (
            f"{label}: path={_short_repr(raw_path)} total_bytes=unavailable "
            "sha256=unavailable truncated_bytes=unavailable "
            "stream_status=invalid-path"
        )
    path = Path(raw_path)
    try:
        candidate = path.parent.resolve() / path.name
        candidate.relative_to(artifact_dir.resolve())
    except (OSError, ValueError):
        return (
            f"{label}: path={_short_repr(raw_path)} total_bytes=unavailable "
            "sha256=unavailable truncated_bytes=unavailable "
            "stream_status=outside-artifact-dir"
        )
    try:
        payload = _read_regular_file_bounded(
            path, max_bytes=_STREAM_READ_MAX_BYTES
        )
        return _stream_diagnostic_from_bytes(label, payload, raw_path)
    except _DiagnosticFileError as exc:
        return (
            f"{label}: path={_short_repr(raw_path)} "
            f"total_bytes={_short_repr(exc.total_bytes)} "
            "sha256=unavailable truncated_bytes=unavailable "
            f"stream_status=unreadable:{exc.reason}"
        )
    except Exception as exc:
        return (
            f"{label}: path={_short_repr(raw_path)} total_bytes=unavailable "
            "sha256=unavailable truncated_bytes=unavailable "
            f"stream_status=unreadable:{type(exc).__name__}"
        )


def _failed_predicates(attempt: dict[str, Any]) -> list[str]:
    failed: list[str] = []
    if attempt.get("limit_trigger") is not None:
        failed.append("limit_trigger")
    for field, accepted_value in (
        ("evidence_status", "complete"),
        ("metering_status", "complete"),
        ("codex_exit_code", 0),
        ("validator_rc", 0),
        ("process_group_residual", 0),
        ("termination_verified", True),
    ):
        if attempt.get(field) != accepted_value:
            failed.append(field)
    if attempt["accepted"] is False and not failed:
        failed.append("unrecorded_acceptance_guard")
    return failed


def _truth_summary(receipt: dict[str, Any]) -> str:
    attempts = receipt["attempts"]
    compact: list[str] = []
    for index, attempt in enumerate(attempts, 1):
        failed = json.dumps(
            _failed_predicates(attempt), ensure_ascii=True, separators=(",", ":")
        )
        compact.append(
            f"attempt[{index}] accepted={attempt['accepted']!r} "
            f"failed_predicates={failed}"
        )
    prefix = (
        "truth_summary: "
        f"outcome={receipt['outcome']!r} "
        f"stop_reason={receipt['stop_reason']!r} "
        f"launcher_rc={receipt['launcher_rc']!r}; "
    )
    selected_indexes: set[int] = set()
    # 最終 attempt を先に予約し、16 KiB message の末尾へ必ず残す。
    order = ([len(compact) - 1] if compact else []) + list(
        range(max(0, len(compact) - 1))
    )
    for index in order:
        trial_indexes = sorted(selected_indexes | {index})
        trial = prefix + "; ".join(compact[item] for item in trial_indexes)
        if len(trial.encode("utf-8")) <= _TRUTH_SUMMARY_MAX_BYTES:
            selected_indexes.add(index)
    selected = [compact[index] for index in sorted(selected_indexes)]
    omitted = len(compact) - len(selected)
    if omitted:
        selected.append(f"omitted_attempts={omitted}")
    return prefix + "; ".join(selected)


def _receipt_diagnostic(
    paths: dict[str, Path],
) -> tuple[list[str], str, dict[str, Any] | None]:
    receipt_path = paths["receipt"]
    try:
        raw = _read_regular_file_bounded(
            receipt_path, max_bytes=_RECEIPT_MAX_BYTES
        )
    except FileNotFoundError:
        summary = "truth_summary: receipt_status=missing attempts=unavailable"
        return [
            f"receipt_status=missing path={os.fspath(receipt_path)!r}",
            "observability_status=insufficient",
            summary,
        ], summary, None
    except _DiagnosticFileError as exc:
        status = (
            "invalid:too-large"
            if exc.reason == "too-large"
            else f"unreadable:{exc.reason}"
        )
        summary = f"truth_summary: receipt_status={status} attempts=unavailable"
        return [
            f"receipt_status={status} path={os.fspath(receipt_path)!r} "
            f"total_bytes={_short_repr(exc.total_bytes)} "
            f"max_bytes={_RECEIPT_MAX_BYTES}",
            "observability_status=insufficient",
            summary,
        ], summary, None
    except OSError as exc:
        status = f"unreadable:{type(exc).__name__}"
        summary = f"truth_summary: receipt_status={status} attempts=unavailable"
        return [
            f"receipt_status={status} path={os.fspath(receipt_path)!r}",
            "observability_status=insufficient",
            summary,
        ], summary, None
    try:
        parsed = LAUNCHER.strict_loads(
            raw, label="receipt diagnostic", max_bytes=_RECEIPT_MAX_BYTES
        )
    except LAUNCHER.DevWavesError:
        raw_line = _stream_diagnostic_from_bytes(
            "receipt_raw", raw, os.fspath(receipt_path)
        )
        status = "invalid:strict-json"
        summary = f"truth_summary: receipt_status={status} attempts=unavailable"
        return [
            f"receipt_status={status}",
            "observability_status=insufficient",
            raw_line,
            summary,
        ], summary, None
    try:
        receipt = LAUNCHER._validate_receipt(parsed)
    except LAUNCHER.LaunchError as exc:
        raw_line = _stream_diagnostic_from_bytes(
            "receipt_raw", raw, os.fspath(receipt_path)
        )
        reason = str(exc).replace("\n", " ")
        status = f"invalid:schema-or-semantic:{reason[:240]}"
        summary = f"truth_summary: receipt_status={status} attempts=unavailable"
        return [
            f"receipt_status={status}",
            "observability_status=insufficient",
            raw_line,
            summary,
        ], summary, None

    summary = _truth_summary(receipt)
    lines = [summary]
    lines.append(
        "receipt: "
        f"outcome={receipt['outcome']!r} "
        f"stop_reason={receipt['stop_reason']!r} "
        f"launcher_rc={receipt['launcher_rc']!r}"
    )
    artifact_dir = paths["artifact"]
    fields = (
        "accepted",
        "limit_trigger",
        "evidence_status",
        "metering_status",
        "codex_exit_code",
        "validator_rc",
        "process_group_residual",
        "termination_verified",
        "wall_clock_s",
    )
    for index, attempt in enumerate(receipt["attempts"], 1):
        values = " ".join(
            f"{field}={_short_repr(attempt[field])}" for field in fields
        )
        failed = json.dumps(
            _failed_predicates(attempt), ensure_ascii=True, separators=(",", ":")
        )
        lines.append(
            f"attempt[{index}]: {values} 不成立だったゲート "
            f"failed_predicates={failed}"
        )
        lines.append(
            _stream_diagnostic_from_path(
                f"attempt[{index}].stdout",
                attempt["stdout_path"],
                artifact_dir,
            )
        )
        lines.append(
            _stream_diagnostic_from_path(
                f"attempt[{index}].stderr",
                attempt["stderr_path"],
                artifact_dir,
            )
        )
    lines.append(summary)
    return lines, summary, receipt


def _launcher_command(
    result: (
        subprocess.CompletedProcess[Any]
        | subprocess.Popen[Any]
        | subprocess.TimeoutExpired
        | int
    ),
    explicit: list[str] | None,
) -> list[str] | None:
    if explicit is not None:
        return explicit
    candidate = getattr(result, "args", None)
    if candidate is None:
        candidate = getattr(result, "cmd", None)
    if isinstance(candidate, (list, tuple)) and all(
        isinstance(item, str) for item in candidate
    ):
        return list(candidate)
    return None


def _command_option(command: list[str] | None, name: str) -> str:
    if command is None:
        return "<unavailable>"
    try:
        return command[command.index(name) + 1]
    except (ValueError, IndexError):
        return "<unavailable>"


def _runtime_context_lines(
    receipt: dict[str, Any] | None,
    command: list[str] | None,
) -> list[str]:
    try:
        load_average: object = os.getloadavg()
    except OSError as exc:
        load_average = f"unavailable:{type(exc).__name__}"
    worker = os.environ.get("PYTEST_XDIST_WORKER", "<unset>")
    pbs_job_id = os.environ.get("PBS_JOBID", "<unset>")
    lines = [
        "runtime_context: "
        f"hostname={socket.gethostname()!r} "
        f"PYTEST_XDIST_WORKER={worker!r} PBS_JOBID={pbs_job_id!r} "
        f"test_pid={os.getpid()} loadavg={load_average!r}",
        "launcher_budgets: "
        f"wall={_command_option(command, '--wall-clock-admission-bound-s')!r} "
        f"evidence={_command_option(command, '--evidence-grace-s')!r} "
        f"termination={_command_option(command, '--termination-grace-s')!r} "
        f"poll={_command_option(command, '--poll-interval-s')!r}",
    ]
    if receipt is None:
        lines.extend(("receipt_limits=unavailable", "receipt_actuals=unavailable"))
    else:
        lines.extend(
            (
                f"receipt_limits={receipt['limits']!r}",
                f"receipt_actuals={receipt['actuals']!r}",
            )
        )
    return lines


def _launcher_failure_message(
    result: (
        subprocess.CompletedProcess[Any]
        | subprocess.Popen[Any]
        | subprocess.TimeoutExpired
        | int
    ),
    *,
    paths: dict[str, Path],
    stdout: str | bytes | None = None,
    stderr: str | bytes | None = None,
    command: list[str] | None = None,
) -> str:
    lines, _summary, receipt = _receipt_diagnostic(paths)
    if isinstance(result, int):
        unavailable = (
            "total_bytes=unavailable sha256=unavailable "
            "truncated_bytes=unavailable stream_status=unavailable "
            "path=<in-process>"
        )
        lines.insert(1, f"stdout: {unavailable}")
        lines.insert(2, f"stderr: {unavailable}")
    else:
        captured_stdout = (
            stdout if stdout is not None else getattr(result, "stdout", None)
        )
        captured_stderr = (
            stderr if stderr is not None else getattr(result, "stderr", None)
        )
        for offset, (label, captured) in enumerate(
            (
                ("launcher.stdout", captured_stdout),
                ("launcher.stderr", captured_stderr),
            ),
            1,
        ):
            if captured is None:
                line = (
                    f"{label}: total_bytes=unavailable sha256=unavailable "
                    "truncated_bytes=unavailable stream_status=unavailable "
                    "path=<captured>"
                )
            else:
                payload = (
                    captured
                    if isinstance(captured, bytes)
                    else captured.encode("utf-8")
                )
                line = _stream_diagnostic_from_bytes(label, payload, "<captured>")
            lines.insert(offset, line)
    lines[-1:-1] = _runtime_context_lines(
        receipt, _launcher_command(result, command)
    )
    return "\n".join(lines)


def _returncode_value(
    result: (
        subprocess.CompletedProcess[Any]
        | subprocess.Popen[Any]
        | subprocess.TimeoutExpired
        | int
    ),
) -> int | str | None:
    if isinstance(result, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(result, int):
        return result
    return result.returncode


def _bounded_failure_message(prefix: str, body: str) -> str:
    message = f"{prefix}\n{body}"
    encoded = message.encode("utf-8")
    if len(encoded) <= _DIAGNOSTIC_MAX_BYTES:
        return message
    final_line = body.splitlines()[-1] if body else "truth_summary: unavailable"
    final_line = final_line.encode("utf-8")[:2048].decode(
        "utf-8", errors="ignore"
    )
    suffix = f"\ndiagnostic_message_truncated=true\n{final_line}"
    fixed = f"{prefix}\n"
    budget = _DIAGNOSTIC_MAX_BYTES - len(fixed.encode()) - len(suffix.encode())
    clipped = body.encode("utf-8")[: max(0, budget)].decode("utf-8", errors="ignore")
    return fixed + clipped + suffix


def _assert_launcher_returncode(
    result: (
        subprocess.CompletedProcess[Any]
        | subprocess.Popen[Any]
        | subprocess.TimeoutExpired
        | int
    ),
    expected_returncode: int,
    *,
    paths: dict[str, Path],
    stdout: str | bytes | None = None,
    stderr: str | bytes | None = None,
    label: str = "launcher",
    command: list[str] | None = None,
) -> None:
    actual = _returncode_value(result)
    if actual == expected_returncode:
        return
    prefix = (
        f"actual rc {actual} != expected rc {expected_returncode}; "
        f"label={label}"
    )
    try:
        body = _launcher_failure_message(
            result,
            paths=paths,
            stdout=stdout,
            stderr=stderr,
            command=command,
        )
    except Exception as exc:
        body = (
            f"diagnostic_status=failed:{type(exc).__name__}\n"
            f"truth_summary: diagnostic_status=failed:{type(exc).__name__}"
        )
    raise LauncherReturncodeMismatch(_bounded_failure_message(prefix, body))


def _run_launcher_subprocess(
    command: list[str],
    *,
    env: dict[str, str],
    paths: dict[str, Path],
    expected_returncode: int,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            env=env,
            text=True,
            errors="backslashreplace",
            capture_output=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired as exc:
        _assert_launcher_returncode(
            exc, expected_returncode, paths=paths, command=command
        )
        raise AssertionError("unreachable")
    _assert_launcher_returncode(
        completed, expected_returncode, paths=paths, command=command
    )
    return completed


def _communicate_launcher(
    process: subprocess.Popen[str],
    *,
    paths: dict[str, Path],
    expected_returncode: int,
    label: str,
) -> tuple[str, str]:
    try:
        stdout, stderr = process.communicate(timeout=10)
    except subprocess.TimeoutExpired as exc:
        _assert_launcher_returncode(exc, expected_returncode, paths=paths, label=label)
        raise AssertionError("unreachable")
    _assert_launcher_returncode(
        process,
        expected_returncode,
        paths=paths,
        stdout=stdout,
        stderr=stderr,
        label=label,
    )
    return stdout, stderr


def _assert_unordered_launcher_returncodes(
    processes: list[
        tuple[str, subprocess.Popen[str], tuple[str, str], dict[str, Path]]
    ],
    expected_returncodes: list[int],
) -> None:
    actual = sorted(
        process.returncode
        for _label, process, _output, _paths in processes
    )
    if actual == sorted(expected_returncodes):
        return
    prefix = (
        f"actual rc {actual} != expected rc {sorted(expected_returncodes)}; "
        "labels=" + ",".join(label for label, *_rest in processes)
    )
    bodies: list[str] = []
    for label, process, (stdout, stderr), paths in processes:
        try:
            bodies.append(
                f"[{label}]\n"
                + _launcher_failure_message(
                    process, paths=paths, stdout=stdout, stderr=stderr
                )
            )
        except Exception as exc:
            bodies.append(f"[{label}] diagnostic_status=failed:{type(exc).__name__}")
    raise LauncherReturncodeMismatch(
        _bounded_failure_message(prefix, "\n".join(bodies))
    )


def _communicate_unordered_launcher(
    process: subprocess.Popen[str],
    *,
    paths: dict[str, Path],
    expected_returncodes: list[int],
    label: str,
) -> tuple[str, str]:
    try:
        return process.communicate(timeout=10)
    except subprocess.TimeoutExpired as exc:
        prefix = (
            f"actual rc timeout != expected rc one-of "
            f"{sorted(expected_returncodes)}; label={label}"
        )
        try:
            body = _launcher_failure_message(exc, paths=paths)
        except Exception as diagnostic_exc:
            body = (
                f"diagnostic_status=failed:{type(diagnostic_exc).__name__}\n"
                "truth_summary: diagnostic_status="
                f"failed:{type(diagnostic_exc).__name__}"
            )
        raise LauncherReturncodeMismatch(_bounded_failure_message(prefix, body))


def _write_fake_codex(path: Path) -> Path:
    """実 Codex を呼ばず、CLI 0.146.0 の stdout/rollout seam を再現する。"""
    source = r'''#!/usr/bin/env python3
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

if sys.argv[1:] == ["--version"]:
    time.sleep(float(os.environ.get("FAKE_VERSION_DELAY", "0")))
    print("codex-cli 0.146.0-fake")
    raise SystemExit(0)
if len(sys.argv) < 2 or sys.argv[1] != "exec":
    raise SystemExit(64)
if "--json" not in sys.argv or "--ephemeral" in sys.argv:
    raise SystemExit(66)
if os.read(0, 1) != b"":
    raise SystemExit(67)

pid_dir = Path(os.environ["FAKE_PID_DIR"])
pid_dir.mkdir(parents=True, exist_ok=True)
(pid_dir / f"leader-{os.getpid()}.pid").write_text(str(os.getpid()), encoding="ascii")
(pid_dir / f"argv-{os.getpid()}.json").write_text(
    json.dumps(sys.argv[1:]), encoding="utf-8"
)
counter_path = Path(os.environ.get("FAKE_COUNTER", pid_dir / "counter"))
counter_path.parent.mkdir(parents=True, exist_ok=True)
with counter_path.open("a+", encoding="ascii") as counter:
    fcntl.flock(counter.fileno(), fcntl.LOCK_EX)
    counter.seek(0)
    raw = counter.read().strip()
    invocation = int(raw or "0") + 1
    counter.seek(0)
    counter.truncate()
    counter.write(str(invocation))
    counter.flush()
    os.fsync(counter.fileno())
sequence = os.environ.get("FAKE_SEQUENCE", os.environ.get("FAKE_MODE", "normal")).split(",")
mode = sequence[min(invocation - 1, len(sequence) - 1)]

barrier = os.environ.get("FAKE_BARRIER_DIR")
if barrier:
    barrier_path = Path(barrier)
    barrier_path.mkdir(parents=True, exist_ok=True)
    (barrier_path / f"ready-{os.getpid()}").write_text("1", encoding="ascii")
    deadline = time.monotonic() + 5
    wanted = int(os.environ.get("FAKE_BARRIER_COUNT", "2"))
    while len(list(barrier_path.glob("ready-*"))) < wanted:
        if time.monotonic() >= deadline:
            raise SystemExit(65)
        time.sleep(0.005)

output = Path(sys.argv[sys.argv.index("-o") + 1])
model = sys.argv[sys.argv.index("-m") + 1]
reasoning_arg = sys.argv[sys.argv.index("-c") + 1]
reasoning = reasoning_arg.split("=", 1)[1].strip('"')
session_root = Path(os.environ["CODEX_HOME"]) / "sessions" / "2026" / "07" / "29"
session_root.mkdir(parents=True, exist_ok=True)
valid_output = ("十分な検査本文です。" * 80) + "\n## 総括\nfake Codex 完了\n"

def emit(value):
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    os.fsync(sys.stdout.fileno())

def emit_raw(value):
    sys.stdout.write(value + "\n")
    sys.stdout.flush()
    os.fsync(sys.stdout.fileno())

def write_line(stream, value):
    stream.write(json.dumps(value, separators=(",", ":")) + "\n")
    stream.flush()
    os.fsync(stream.fileno())

def write_raw(stream, value):
    stream.write(value + "\n")
    stream.flush()
    os.fsync(stream.fileno())

def usage(input_tokens=100, cached=20, output_tokens=10, total=110):
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": 0,
        "total_tokens": total,
    }

def create_rollout(session_id):
    path = session_root / f"rollout-2026-07-29T00-00-00-{session_id}.jsonl"
    with path.open("w", encoding="utf-8") as stream:
        meta_payload = {"session_id": session_id}
        if mode != "cwd_missing":
            meta_payload["cwd"] = sys.argv[sys.argv.index("-C") + 1]
        write_line(stream, {
            "type": "session_meta",
            "payload": meta_payload,
        })
        if mode == "payload_decoy":
            write_line(stream, {
                "type": "turn_context",
                "model": model,
                "effort": reasoning,
                "payload": {},
                "collaboration_mode": {
                    "settings": {"model": model, "effort": reasoning}
                },
            })
        else:
            write_line(stream, {
                "type": "turn_context",
                "payload": {"model": model, "effort": reasoning},
            })
        if mode == "rollout_duplicate_key":
            write_raw(
                stream,
                '{"type":"event_msg","payload":{"type":"ignored",'
                '"id":"first","id":"second"}}',
            )
    return path

def append_token(path, total_usage):
    with path.open("a", encoding="utf-8") as stream:
        write_line(stream, {
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": (
                    None
                    if total_usage is None
                    else {
                        "total_token_usage": total_usage,
                        "last_token_usage": total_usage,
                    }
                ),
            },
        })

def terminal(total_usage):
    emit({
        "type": "turn.completed",
        "usage": {
            "input_tokens": total_usage["input_tokens"],
            "cached_input_tokens": total_usage["cached_input_tokens"],
            "cache_write_input_tokens": 0,
            "output_tokens": total_usage["output_tokens"],
            "reasoning_output_tokens": total_usage.get("reasoning_output_tokens", 0),
        },
    })

def child_sleep(*, escaped=False, ignore_term=False):
    code = (
        "import os,signal,time,pathlib;"
        + ("os.setsid();" if escaped else "")
        + ("signal.signal(signal.SIGTERM,signal.SIG_IGN);" if ignore_term else "")
        + "pathlib.Path(os.environ['FAKE_CHILD_PID']).write_text(str(os.getpid()));"
        + "time.sleep(30)"
    )
    child_env = dict(os.environ)
    child_env["FAKE_CHILD_PID"] = str(pid_dir / ("escaped.pid" if escaped else "child.pid"))
    return subprocess.Popen([sys.executable, "-c", code], env=child_env)

if mode == "no_thread":
    child_sleep(ignore_term=True)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
    raise SystemExit(0)

if mode == "delayed_thread":
    time.sleep(0.12)

session_id = str(uuid.uuid4())
if mode != "cli_exact":
    emit({"type": "thread.started", "thread_id": session_id})
emit({"type": "turn.started"})
emit({
    "type": "item.started",
    "item": {
        "id": "item_0",
        "type": "command_execution",
        "status": "in_progress",
    },
})
if mode == "web_search_duplicate_stdout":
    emit_raw(
        '{"type":"item.started","item":{"id":"item_40",'
        '"type":"web_search",'
        '"id":"exec-f3ed5b5c-aa7d-4450-a1d8-44232d49c1e9",'
        '"query":"","action":{"type":"other"}}}'
    )

if mode == "no_rollout":
    terminal(usage())
    output.write_text(valid_output, encoding="utf-8")
    time.sleep(30)
    raise SystemExit(0)

if mode == "cached_bad":
    selected_usage = usage(input_tokens=100, cached=101, output_tokens=1, total=101)
elif mode in ("cli_exact", "token_wait"):
    selected_usage = usage(input_tokens=1000, cached=950, output_tokens=10, total=1010)
elif mode in ("retry_reject", "retry_wait"):
    selected_usage = usage(input_tokens=10, cached=0, output_tokens=0, total=10)
elif mode == "final_drain":
    selected_usage = usage(input_tokens=90, cached=0, output_tokens=0, total=90)
else:
    selected_usage = usage()

rollout_path = create_rollout(session_id)
time.sleep(0.04)
if mode == "rollback":
    append_token(
        rollout_path,
        usage(input_tokens=1000, cached=0, output_tokens=0, total=1000),
    )
    append_token(
        rollout_path,
        usage(input_tokens=1000, cached=999, output_tokens=1, total=1001),
    )
    selected_usage = usage(
        input_tokens=1000, cached=999, output_tokens=1, total=1001
    )
elif mode == "rollback_equal_cli":
    append_token(
        rollout_path,
        usage(input_tokens=100, cached=0, output_tokens=0, total=100),
    )
    append_token(
        rollout_path,
        usage(input_tokens=99, cached=0, output_tokens=1, total=100),
    )
    # peak latch と terminal mismatch を発火させず、rollback gate だけを負にする。
    selected_usage = usage(
        input_tokens=100, cached=0, output_tokens=0, total=100
    )
elif mode == "null_info":
    append_token(rollout_path, None)
    append_token(rollout_path, selected_usage)
elif mode not in ("no_token", "term_success"):
    append_token(rollout_path, selected_usage)
# fsync 済み rollout evidence を親の論理時計へ通知する。
if (
    mode != "term_success"
    and invocation == 1
    and (ready := os.environ.get("FAKE_EVIDENCE_READY"))
):
    Path(ready).write_text("1", encoding="ascii")
if mode == "final_drain":
    time.sleep(0.15)
    selected_usage = usage(
        input_tokens=110, cached=0, output_tokens=0, total=110
    )
    append_token(rollout_path, selected_usage)

if mode in ("id_change", "multiple_sessions", "id_change_wait"):
    if mode == "id_change_wait":
        child_sleep(ignore_term=True)
        child_pid_path = pid_dir / "child.pid"
        deadline = time.monotonic() + 2
        while not child_pid_path.exists():
            if time.monotonic() >= deadline:
                raise SystemExit(68)
            time.sleep(0.005)
    second = str(uuid.uuid4())
    emit({"type": "thread.started", "thread_id": second})
    second_path = create_rollout(second)
    append_token(
        second_path,
        usage(input_tokens=0, cached=0, output_tokens=0, total=0),
    )

if mode == "inconsistent":
    terminal(usage(input_tokens=101, cached=20, output_tokens=10, total=111))
elif mode != "token_wait":
    terminal(selected_usage)

emit({
    "type": "item.completed",
    "item": {
        "id": "item_0",
        "type": "command_execution",
        "status": "completed",
        "exit_code": 0,
    },
})

if mode == "non_utf8":
    output.write_bytes(b"\xff" + (b"x" * 600))
elif mode == "oversized":
    output.write_bytes(b"x" * (10 * 1024 * 1024 + 1))
elif mode == "heading_missing":
    output.write_text(("十分な検査本文です。" * 80) + "\n", encoding="utf-8")
elif mode in ("empty_output",):
    output.write_bytes(b"")
elif mode in ("missing_output",):
    pass
elif mode in ("retry_reject",):
    output.write_text("短い失敗", encoding="utf-8")
else:
    output.write_text(valid_output, encoding="utf-8")

if mode in ("child_error", "empty_output", "missing_output"):
    raise SystemExit(7)

if mode == "cli_exact":
    # stdout thread ID を最後に flush して即終了し、同一 poll の自然終了
    # と actual == limit 境界を決定的に作る。
    emit({"type": "thread.started", "thread_id": session_id})
elif mode == "term_success":
    def finish(_signum, _frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, finish)
    # Publish the counted event only after output/terminal I/O and handler setup.
    # SIGTERM can interrupt this append without reentering any I/O in finish.
    append_token(rollout_path, selected_usage)
    if invocation == 1 and (ready := os.environ.get("FAKE_EVIDENCE_READY")):
        Path(ready).write_text("1", encoding="ascii")
    time.sleep(30)
elif mode == "sigterm_ignore":
    child_sleep(ignore_term=True)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
elif mode in ("token_wait", "retry_wait"):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
elif mode == "setsid_escape":
    child_sleep(escaped=True)
    time.sleep(0.05)
elif mode == "manifest_while_running":
    time.sleep(0.5)
elif mode == "id_change_wait":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
elif mode == "late_writer":
    child = os.fork()
    if child == 0:
        os.setsid()
        (pid_dir / "late.pid").write_text(str(os.getpid()), encoding="ascii")
        time.sleep(0.5)
        with rollout_path.open("a", encoding="utf-8") as stream:
            write_line(stream, {"type": "event_msg", "payload": {"type": "late"}})
        os._exit(0)
else:
    time.sleep(0.04)
'''
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


def _base_command(
    tmp_path: Path,
    *,
    fake: Path,
    job_id: str = "job-a",
    wave_id: str = "wave-a",
    stage: str = "author",
    lane: str | None = None,
    sandbox: str = "read-only",
    reasoning: str | None = None,
    max_attempts: int = 1,
    max_wall: str = "3",
    evidence_grace: str = "1.0",
    max_calls: int = 100,
    max_tokens: int = 100000,
    suffix: str = "",
    repo_root: Path = _ROOT,
    base_commit: str | None = None,
    cwd: Path | None = None,
    manifest_path: Path | None = None,
) -> tuple[list[str], dict[str, str], dict[str, Path]]:
    if base_commit is None:
        base_commit = subprocess.run(
            ["git", "-C", os.fspath(repo_root), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
    if cwd is None:
        cwd = repo_root
    if manifest_path is None:
        manifest_path = tmp_path / "manifest.json"
    prompt = tmp_path / f"prompt{suffix}.txt"
    prompt.write_text("fake prompt\n", encoding="utf-8")
    codex_home = tmp_path / f"codex-home{suffix}"
    pid_dir = tmp_path / f"pids{suffix}"
    artifact = tmp_path / f"artifacts{suffix}"
    paths = {
        "prompt": prompt,
        "codex_home": codex_home,
        "pid_dir": pid_dir,
        "artifact": artifact,
        "output": tmp_path / f"output{suffix}.md",
        "receipt": tmp_path / f"receipt{suffix}.json",
        "manifest": manifest_path,
        "counter": tmp_path / f"counter{suffix}",
    }
    command = [
        sys.executable,
        os.fspath(_LAUNCHER),
        "run",
        "--stage",
        stage,
        "--job-id",
        job_id,
        "--wave-id",
        wave_id,
        "--repo-root",
        os.fspath(repo_root),
        "--base-commit",
        base_commit,
        "--prompt-file",
        os.fspath(prompt),
        "--cwd",
        os.fspath(cwd),
        "--sandbox",
        sandbox,
        "--wall-clock-admission-bound-s",
        max_wall,
        "--max-model-calls",
        str(max_calls),
        "--max-cli-reported-tokens",
        str(max_tokens),
        "--max-attempts",
        str(max_attempts),
        "--artifact-dir",
        os.fspath(artifact),
        "--output-file",
        os.fspath(paths["output"]),
        "--receipt",
        os.fspath(paths["receipt"]),
        "--manifest",
        os.fspath(paths["manifest"]),
        "--sessions-root",
        os.fspath(codex_home / "sessions"),
        "--codex-bin",
        os.fspath(fake),
        "--evidence-grace-s",
        evidence_grace,
        "--termination-grace-s",
        "0.05",
        "--poll-interval-s",
        "0.01",
    ]
    if reasoning is not None:
        command.extend(("--reasoning", reasoning))
    elif stage not in ("review", "focus", "author", "fix"):
        command.extend(("--reasoning", "high"))
    if lane is not None:
        command[5:5] = ["--lane", lane]
    env = dict(os.environ)
    env.update(
        {
            "CODEX_HOME": os.fspath(codex_home),
            "FAKE_PID_DIR": os.fspath(pid_dir),
            "FAKE_COUNTER": os.fspath(paths["counter"]),
        }
    )
    return command, env, paths


def _run_case(
    tmp_path: Path,
    mode: str,
    *,
    expected_returncode: int,
    fake_sequence: str | None = None,
    **kwargs: Any,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None, dict[str, Path]]:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake, **kwargs)
    env["FAKE_MODE"] = mode
    if fake_sequence is not None:
        env["FAKE_SEQUENCE"] = fake_sequence
    completed = _run_launcher_subprocess(
        command,
        env=env,
        paths=paths,
        expected_returncode=expected_returncode,
    )
    receipt = (
        json.loads(paths["receipt"].read_text(encoding="utf-8"))
        if paths["receipt"].exists()
        else None
    )
    return completed, receipt, paths


def _read_launcher_diagnostics(paths: dict[str, Path]) -> dict[str, Any]:
    candidates = list(
        paths["artifact"].glob("launcher-diagnostics.*.json")
    )
    assert len(candidates) == 1
    document = json.loads(candidates[0].read_text(encoding="utf-8"))
    assert document["schema"] == "codex-worker-launch-diagnostics/v1"
    return document


def _diagnostic_snapshots(
    paths: dict[str, Path], site: str
) -> list[dict[str, Any]]:
    diagnostics = _read_launcher_diagnostics(paths)
    return [
        item
        for attempt in diagnostics["attempts"]
        for item in attempt["limit_condition_snapshots"]
        if item["site"] == site
    ]


def test_launcher_failure_artifact_reporter_hook_is_tryfirst() -> None:
    hook = _LauncherFailureArtifactPlugin.pytest_runtest_makereport

    assert hook.pytest_impl["tryfirst"] is True
    assert hook.pytest_impl.get("trylast", False) is False


def test_launcher_failure_artifact_fixture_does_not_request_tmp_path() -> None:
    parameters = inspect.signature(
        _launcher_failure_artifact_reporter
    ).parameters

    assert list(parameters) == ["request"]


def test_launcher_failure_artifact_hook_ignores_item_without_tmp_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "archive-root"
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )

    class Item:
        nodeid = "module.py::test_without_tmp_path"
        funcargs: dict[str, Any] = {}

        def add_report_section(self, *_args: Any) -> None:
            pytest.fail("tmp_path の無い item を archive してはならない")

    class ExcInfo:
        value = AssertionError("unhandled")

    call = type("Call", (), {"when": "call", "excinfo": ExcInfo()})()
    _LauncherFailureArtifactPlugin().pytest_runtest_makereport(Item(), call)

    assert not root.exists()


def _create_failure_archive_for_test(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, bytes, type[Any]]:
    root = tmp_path / "empty-archive-root"
    source = tmp_path / "source"
    source.mkdir()
    receipt = source / "receipt.json"
    receipt_bytes = b'{"path":"/original/path"}\n'
    receipt.write_bytes(receipt_bytes)
    nested = source / "nested"
    nested.mkdir()
    sentinel = nested / "sentinel.bin"
    sentinel.write_bytes(b"sentinel-exact-bytes\x00")
    diagnostics = source / "launcher-diagnostics.1.abc.json"
    diagnostics.write_bytes(b"{}\n")
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )
    monkeypatch.setenv("PBS_JOBID", "archive-unit")
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw-test")

    class Item:
        nodeid = "module.py::test_failure"
        sections: list[tuple[str, str, str]] = []

        def add_report_section(
            self, when: str, key: str, content: str
        ) -> None:
            self.sections.append((when, key, content))

    class ExcInfo:
        value = AssertionError("unhandled")

    call = type(
        "Call",
        (),
        {"when": "call", "excinfo": ExcInfo(), "duration": 1.25},
    )()
    plugin = _LauncherFailureArtifactPlugin(source)

    assert not root.exists()
    plugin.pytest_runtest_makereport(Item(), call)

    complete = list(root.rglob(".complete"))
    assert len(complete) == 1
    return complete[0].parent, receipt, receipt_bytes, Item


def test_failure_archive_copies_exact_bytes_from_new_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, _receipt, receipt_bytes, _item = _create_failure_archive_for_test(
        tmp_path, monkeypatch
    )

    assert (bundle / "tmp_path/nested/sentinel.bin").read_bytes() == (
        b"sentinel-exact-bytes\x00"
    )
    assert (bundle / "tmp_path/receipt.json").read_bytes() == receipt_bytes
    metadata = json.loads((bundle / "metadata.json").read_text())
    assert metadata["diagnostics_present"] is True
    assert metadata["diagnostics_absence_reason"] is None
    assert metadata["source_live"] is False
    assert metadata["snapshot_consistency"] == "best-effort"
    assert metadata["critical_set_complete"] is True
    assert metadata["exception_type"] == "builtins.AssertionError"
    assert metadata["exception_message"] == "unhandled"
    assert metadata["exception_message_truncated"] is False
    assert metadata["call_duration_s"] == 1.25
    manifest = json.loads(
        (bundle / "snapshot-manifest.json").read_text()
    )
    assert manifest["omitted_count"] == 0


def test_failure_archive_writes_path_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, receipt, _receipt_bytes, _item = _create_failure_archive_for_test(
        tmp_path, monkeypatch
    )

    path_map = json.loads((bundle / "path-map.json").read_text())["paths"]
    assert path_map[os.fspath(receipt.absolute())] == "tmp_path/receipt.json"


def test_failure_archive_appends_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, _receipt, _receipt_bytes, item = _create_failure_archive_for_test(
        tmp_path, monkeypatch
    )
    run_dir = bundle.parents[1]
    index_lines = list(run_dir.glob("index.jsonl"))
    assert len(index_lines) == 1
    index = [json.loads(line) for line in index_lines[0].read_text().splitlines()]
    assert len(index) == 1
    assert index[0]["nodeid"] == item.nodeid


def test_launcher_failure_artifact_reporter_ignores_handled_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "empty-archive-root"
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )

    class Item:
        nodeid = "module.py::test_handled"

        def add_report_section(self, *_args: Any) -> None:
            pytest.fail("handled failure must not archive")

    call = type("Call", (), {"when": "call", "excinfo": None})()

    _LauncherFailureArtifactPlugin(source).pytest_runtest_makereport(
        Item(), call
    )

    assert not root.exists()


def test_launcher_failure_artifact_paths_are_collision_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "empty-archive-root"
    source = tmp_path / "source"
    source.mkdir()
    sentinel = source / "sentinel.bin"
    sentinel.write_bytes(b"first")
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )
    monkeypatch.setenv("PBS_JOBID", "collision-unit")

    _archive_launcher_failure(
        nodeid="same.py::test_node",
        tmp_path=source,
        exception=AssertionError("first"),
    )
    sentinel.write_bytes(b"second")
    _archive_launcher_failure(
        nodeid="same.py::test_node",
        tmp_path=source,
        exception=AssertionError("second"),
    )

    complete = sorted(root.rglob(".complete"))
    assert len(complete) == 2
    payloads = {
        marker.parent.joinpath("tmp_path/sentinel.bin").read_bytes()
        for marker in complete
    }
    assert payloads == {b"first", b"second"}


def test_launcher_failure_artifact_copy_error_does_not_mask_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "empty-archive-root"
    source = tmp_path / "source"
    source.mkdir()
    (source / "sentinel.bin").write_bytes(b"sentinel")
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )
    monkeypatch.setattr(
        shutil,
        "copyfile",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("synthetic copy failure")
        ),
    )
    original = AssertionError("original test failure")

    status = _archive_launcher_failure_without_masking(
        nodeid="module.py::test_failure",
        tmp_path=source,
        exception=original,
    )

    assert status.startswith("archive_status=complete")
    assert str(original) == "original test failure"
    complete = list(root.rglob(".complete"))
    assert len(complete) == 1
    bundle = complete[0].parent
    metadata = json.loads((bundle / "metadata.json").read_text())
    assert metadata["snapshot_consistency"] == "incomplete"
    assert metadata["diagnostics_absence_reason"] == (
        "no-launcher-artifacts-observed"
    )
    manifest = json.loads(
        (bundle / "snapshot-manifest.json").read_text()
    )
    assert manifest["omitted_count"] == 1
    assert manifest["entries"][0]["reason"] == "copy-error:OSError"


def test_launcher_failure_artifact_limits_record_omission_reasons(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "one").write_bytes(b"1")
    (source / "two").write_bytes(b"22")
    monkeypatch.setattr(sys.modules[__name__], "_SNAPSHOT_MAX_FILES", 1)
    monkeypatch.setattr(sys.modules[__name__], "_SNAPSHOT_MAX_BYTES", 1)

    manifest, _path_map = _snapshot_tmp_path(source, destination)

    reasons = {
        item.get("reason")
        for item in manifest["entries"]
        if item["status"] == "omitted"
    }
    assert reasons == {"file-count-limit"}
    assert manifest["bytes_copied"] == 1


def test_launcher_failure_artifact_byte_limit_records_omission_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "large").write_bytes(b"12")
    monkeypatch.setattr(sys.modules[__name__], "_SNAPSHOT_MAX_FILES", 10)
    monkeypatch.setattr(sys.modules[__name__], "_SNAPSHOT_MAX_BYTES", 1)

    manifest, _path_map = _snapshot_tmp_path(source, destination)

    assert manifest["omitted_count"] == 1
    assert manifest["entries"][0]["reason"] == "total-bytes-limit"


def test_failure_archive_stops_descent_for_directory_heavy_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    for index in range(20):
        (source / f"directory-{index:02d}" / "nested").mkdir(parents=True)
    monkeypatch.setattr(sys.modules[__name__], "_SNAPSHOT_MAX_FILES", 4)

    manifest, _path_map = _snapshot_tmp_path(source, destination)

    assert manifest["files_seen"] == 4
    assert manifest["search_complete"] is False
    assert manifest["omitted_count"] == 1
    assert manifest["entries"] == [
        {
            "path": ".",
            "kind": "subtree",
            "status": "omitted",
            "reason": "file-count-limit",
        }
    ]
    assert list((destination / "tmp_path").iterdir()) == []


def test_failure_archive_copies_critical_set_before_optional_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "aaa-optional.bin").write_bytes(b"optional")
    receipt = source / "receipt.json"
    receipt.write_bytes(b"critical")

    manifest, _path_map = _snapshot_tmp_path(
        source, destination, max_files=10, max_bytes=len(b"critical")
    )

    assert (destination / "tmp_path/receipt.json").read_bytes() == b"critical"
    assert not (destination / "tmp_path/aaa-optional.bin").exists()
    assert manifest["critical_set_complete"] is True
    assert manifest["critical_kinds_seen"] == ["receipt"]


def test_failure_archive_run_budget_leaves_metadata_only_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "archive-root"
    source = tmp_path / "source"
    source.mkdir()
    (source / "receipt.json").write_bytes(b"critical")
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_RUN_MAX_BUNDLES", 0
    )
    monkeypatch.setenv("PBS_JOBID", "run-budget-unit")

    bundle = _archive_launcher_failure(
        nodeid="module.py::test_budget",
        tmp_path=source,
        exception=AssertionError("failure"),
    )

    metadata = json.loads((bundle / "metadata.json").read_text())
    manifest = json.loads((bundle / "snapshot-manifest.json").read_text())
    assert metadata["run_budget_mode"] == "metadata-only"
    assert metadata["run_budget_reason"] == "run-bundle-limit"
    assert metadata["critical_set_complete"] is False
    assert not (bundle / "tmp_path").exists()
    assert manifest["entries"][0]["reason"] == "run-bundle-limit"


def test_failure_archive_bounds_exception_message_and_absence_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "archive-root"
    source = tmp_path / "source"
    source.mkdir()
    (source / "receipt.json").write_bytes(b"{}\n")
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )
    monkeypatch.setenv("PBS_JOBID", "metadata-unit")

    bundle = _archive_launcher_failure(
        nodeid="module.py::test_metadata",
        tmp_path=source,
        exception=AssertionError("x" * (_EXCEPTION_MESSAGE_MAX_CHARS + 10)),
        call_duration_s=0.75,
    )

    metadata = json.loads((bundle / "metadata.json").read_text())
    assert metadata["exception_type"] == "builtins.AssertionError"
    assert len(metadata["exception_message"]) == _EXCEPTION_MESSAGE_MAX_CHARS
    assert metadata["exception_message_truncated"] is True
    assert metadata["call_duration_s"] == 0.75
    assert metadata["diagnostics_absence_reason"] == (
        "launcher-artifacts-without-diagnostics"
    )


def test_launcher_failure_artifact_special_file_is_not_opened(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    fifo = source / "fifo"
    os.mkfifo(fifo)

    manifest, path_map = _snapshot_tmp_path(source, destination)

    assert manifest["omitted_count"] == 1
    assert manifest["entries"] == [
        {
            "path": "fifo",
            "kind": "special-file",
            "status": "omitted",
            "reason": "special-file",
        }
    ]
    assert os.fspath(fifo.absolute()) not in path_map


def test_launcher_failure_artifact_rejects_ancestor_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    destination = source / "archive"
    destination.mkdir()

    with pytest.raises(ValueError, match="ancestor relationship"):
        _snapshot_tmp_path(source, destination)


def test_launcher_failure_artifact_marks_timeout_source_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "empty-archive-root"
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", root
    )

    _archive_launcher_failure(
        nodeid="module.py::test_timeout",
        tmp_path=source,
        exception=subprocess.TimeoutExpired(["launcher"], 10),
    )

    complete = list(root.rglob(".complete"))
    assert len(complete) == 1
    metadata = json.loads(
        (complete[0].parent / "metadata.json").read_text()
    )
    assert metadata["source_live"] is True
    assert metadata["snapshot_consistency"] == "incomplete"
    assert metadata["diagnostics_present"] is False
    assert metadata["diagnostics_absence_reason"] == (
        "call-timeout-before-diagnostics"
    )


def test_launcher_failure_artifact_live_wiring_probe(tmp_path: Path) -> None:
    if os.environ.get(_LIVE_WIRING_PROBE_ENV) != "1":
        return
    sentinel = tmp_path / "live-wiring-sentinel.bin"
    sentinel.write_bytes(b"live-wiring-sentinel-exact\x00")
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"
    _run_launcher_subprocess(
        command,
        env=env,
        paths=paths,
        expected_returncode=999,
    )


def test_launcher_failure_artifact_reporter_live_wiring() -> None:
    pbs_job_id = f"live-wiring-{uuid.uuid4().hex}"
    run_dir = _FAILURE_ARTIFACT_ROOT / (
        f"{_archive_component(pbs_job_id)}--"
        f"{_archive_component(socket.gethostname())}"
    )
    assert not run_dir.exists()
    env = dict(os.environ)
    env[_LIVE_WIRING_PROBE_ENV] = "1"
    env["PBS_JOBID"] = pbs_job_id
    env["PYTEST_XDIST_WORKER"] = "live-probe"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    nodeid = (
        os.fspath(Path(__file__).resolve())
        + "::test_launcher_failure_artifact_live_wiring_probe"
    )
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", nodeid],
            cwd=_ROOT,
            env=env,
            text=True,
            errors="backslashreplace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        combined = completed.stdout + completed.stderr
        assert "LauncherReturncodeMismatch" in combined
        assert "expected rc 999" in combined
        complete = list(run_dir.rglob(".complete"))
        assert len(complete) == 1
        bundle = complete[0].parent
        sentinels = list(
            bundle.glob("tmp_path/**/live-wiring-sentinel.bin")
        )
        assert len(sentinels) == 1
        assert sentinels[0].read_bytes() == (
            b"live-wiring-sentinel-exact\x00"
        )
    finally:
        if run_dir.is_dir():
            shutil.rmtree(run_dir)


def test_launcher_failure_artifact_archive_error_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(_LIVE_ARCHIVE_FAILURE_PROBE_ENV) != "1":
        return
    blocked_root = tmp_path / "archive-root-is-a-file"
    blocked_root.write_text("not a directory\n", encoding="utf-8")
    monkeypatch.setattr(
        sys.modules[__name__], "_FAILURE_ARTIFACT_ROOT", blocked_root
    )
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"
    _run_launcher_subprocess(
        command,
        env=env,
        paths=paths,
        expected_returncode=999,
    )


def test_launcher_failure_artifact_exception_safety_live() -> None:
    env = dict(os.environ)
    env[_LIVE_ARCHIVE_FAILURE_PROBE_ENV] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    nodeid = (
        os.fspath(Path(__file__).resolve())
        + "::test_launcher_failure_artifact_archive_error_probe"
    )

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", nodeid],
        cwd=_ROOT,
        env=env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )

    combined = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "LauncherReturncodeMismatch" in combined
    assert "expected rc 999" in combined
    assert "INTERNALERROR" not in combined


def _remove_option(command: list[str], option: str) -> None:
    index = command.index(option)
    del command[index : index + 2]


def _prepare_authority_repo(path: Path) -> tuple[Path, str]:
    root = path
    (root / "docs/dev-wave").mkdir(parents=True)
    for name in ("operations.md", "workers.md"):
        (root / "docs/dev-wave" / name).write_bytes(
            (_ROOT / "docs/dev-wave" / name).read_bytes()
        )
    for relative in (
        Path(".codex/hooks.json"),
        Path("hooks/codex_guard.sh"),
        Path("hooks/guard_write.py"),
        Path("hooks/guard_bash.py"),
        Path("tools/pegasus_admission_registry.py"),
        Path("tools/pegasus/admission_registry.json"),
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((_ROOT / relative).read_bytes())
    subprocess.run(["git", "-C", os.fspath(root), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", os.fspath(root), "config", "user.name", "launcher-test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(root), "config", "user.email", "launcher-test@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(root), "add", "docs", ".codex", "hooks", "tools"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(root), "commit", "-qm", "authority fixture"],
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", os.fspath(root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    return root, commit


def _prepare_authority_worktree(
    main: Path, path: Path
) -> tuple[Path, str]:
    commit = subprocess.run(
        ["git", "-C", os.fspath(main), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    subprocess.run(
        [
            "git",
            "-C",
            os.fspath(main),
            "worktree",
            "add",
            "--detach",
            "-q",
            os.fspath(path),
            commit,
        ],
        check=True,
    )
    return path, commit


def _remove_authority_worktree(main: Path, path: Path) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            os.fspath(main),
            "worktree",
            "remove",
            "--force",
            os.fspath(path),
        ],
        check=True,
    )


def _assert_pid_gone(pid: int) -> None:
    deadline = time.monotonic() + 3
    while Path(f"/proc/{pid}").exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not Path(f"/proc/{pid}").exists(), f"PID {pid} survived"


def _leader_pids(paths: dict[str, Path]) -> list[int]:
    return [
        int(path.read_text(encoding="ascii"))
        for path in paths["pid_dir"].glob("leader-*.pid")
    ]


def _check_command(paths: dict[str, Path]) -> list[str]:
    return [
        sys.executable,
        os.fspath(_LAUNCHER),
        "check-receipt",
        "--receipt",
        os.fspath(paths["receipt"]),
        "--manifest",
        os.fspath(paths["manifest"]),
    ]


def _minimal_v3_receipt(
    *, stage: str, effort_authority: str, section_count: int
) -> dict[str, Any]:
    section_ids = ["DW-O01", "DW-S06-A", "DW-S06-C", "DW-S05-A"]
    sections = [
        {
            "path": "docs/dev-wave/operations.md"
            if index == 0
            else "docs/dev-wave/workers.md",
            "section": section_ids[index],
            "sha256": "a" * 64,
        }
        for index in range(section_count)
    ]
    return {
        "schema_version": 3,
        "job_id": "receipt-compatibility-test",
        "stage": stage,
        "lane": None,
        "prompt_sha256": "b" * 64,
        "requested_model": "gpt-5.6-luna",
        "requested_effort": "max",
        "effort_authority": effort_authority,
        "recorded_model": None,
        "recorded_effort": None,
        "recorded_turn_context_count": 0,
        "recorded_values_semantics": LAUNCHER._RECORDED_VALUES_SEMANTICS,
        "sandbox": "read-only",
        "requested_cwd": os.fspath(_ROOT),
        "recorded_cwd": None,
        "repo_root": os.fspath(_ROOT),
        "base_commit": _BASE_COMMIT,
        "sessions_root": os.fspath(_ROOT / "sessions"),
        "artifact_dir": os.fspath(_ROOT / "artifact"),
        "output_path": os.fspath(_ROOT / "output.md"),
        "output_sha256": None,
        "manifest_path": os.fspath(_ROOT / "manifest.json"),
        "receipt_path": os.fspath(_ROOT / "receipt.json"),
        "manifest_wave_id": "receipt-compatibility-wave",
        "authority_snapshot": {
            "authority_commit": _BASE_COMMIT,
            "sections": sections,
            "digest": "c" * 64,
        },
        "codex_version": "fake-codex",
        "codex_executable_path": os.fspath(_LAUNCHER),
        "codex_executable_sha256": "d" * 64,
        "model_calls_semantics": "observed_token_count_events",
        "possible_unobserved_overshoot": False,
        "limits_assertion": "self_asserted",
        "wall_clock_scope": "launcher_start_to_receipt_fields_finalized",
        "retry_classification": "none",
        "escaped_process_containment": "not_attempted",
        "limits": {
            "wall_clock_admission_bound_s": 1,
            "max_model_calls": 1,
            "max_cli_reported_tokens": 1,
            "max_attempts": 1,
        },
        "actuals": {
            "wall_clock_s": 0,
            "attempt_count": 0,
            "model_calls": 0,
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "total_tokens_raw": 0,
            "cli_reported": 0,
        },
        "outcome": "launcher_error",
        "stop_reason": "launcher_error",
        "launcher_rc": 2,
        "codex_exit_code": None,
        "validator_rc": None,
        "attempts": [],
    }


@pytest.mark.parametrize(
    ("stage", "effort_authority", "section_count", "accepted"),
    (
        ("author", "unbound", 3, True),
        ("author", "docs", 4, True),
        ("review", "unbound", 4, False),
        ("plan", "docs", 3, False),
    ),
)
def test_validate_receipt_preserves_effort_authority_compatibility(
    stage: str, effort_authority: str, section_count: int, accepted: bool
) -> None:
    receipt = _minimal_v3_receipt(
        stage=stage,
        effort_authority=effort_authority,
        section_count=section_count,
    )
    if accepted:
        assert LAUNCHER._validate_receipt(receipt)["stage"] == stage
    else:
        with pytest.raises(LAUNCHER.LaunchError, match="effort authority"):
            LAUNCHER._validate_receipt(receipt)


def _write_legacy_v2_evidence(
    receipt_v3: dict[str, Any],
    paths: dict[str, Path],
    *,
    include_failure_class: bool = False,
) -> dict[str, Any]:
    common = {
        field: receipt_v3[field]
        for field in LAUNCHER._RECEIPT_FIELDS_V2
        if field
        not in {
            "schema_version",
            "model",
            "reasoning",
            "cwd",
            "manifest_repo_root",
            "manifest_base_commit",
        }
    }
    receipt_v2 = {
        **common,
        "schema_version": 2,
        "model": receipt_v3["requested_model"],
        "reasoning": receipt_v3["requested_effort"],
        "cwd": receipt_v3["requested_cwd"],
        "manifest_repo_root": receipt_v3["repo_root"],
        "manifest_base_commit": receipt_v3["base_commit"],
    }
    receipt_v2["attempts"] = []
    for raw_attempt in receipt_v3["attempts"]:
        attempt = dict(raw_attempt)
        attempt.pop("evidence_issues", None)
        if not include_failure_class:
            attempt.pop("failure_class")
        receipt_v2["attempts"].append(attempt)
    manifest_v2 = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    manifest_v1 = {
        "schema_version": 1,
        "wave_id": manifest_v2["wave_id"],
        "repo_root": receipt_v3["repo_root"],
        "base_commit": receipt_v3["base_commit"],
        "sessions": [
            {
                "job_id": entry["job_id"],
                "attempt_index": entry["attempt_index"],
                "session_id": entry["session_id"],
            }
            for entry in manifest_v2["sessions"]
        ],
    }
    paths["manifest"].write_text(
        json.dumps(manifest_v1, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return receipt_v2


def _run_main_in_process(
    command: list[str],
    env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    paths: dict[str, Path],
    expected_returncode: int,
) -> int:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        LAUNCHER, "_LAUNCHER_PROCESS_STARTED_NS", time.monotonic_ns()
    )
    rc = LAUNCHER.main(command[2:])
    _assert_launcher_returncode(
        rc,
        expected_returncode,
        paths=paths,
        command=command,
        label="in-process launcher",
    )
    return rc


def _write_valid_diagnostic_receipt(
    paths: dict[str, Path],
    attempt_overrides: list[dict[str, Any]],
    *,
    codex_version_padding: int = 0,
) -> dict[str, Any]:
    artifact = paths["artifact"]
    artifact.mkdir(parents=True, exist_ok=True)
    empty_sha = hashlib.sha256(b"").hexdigest()
    attempts: list[dict[str, Any]] = []
    for index, overrides in enumerate(attempt_overrides, 1):
        stdout_path = artifact / f"attempt-{index:04d}.stdout"
        stderr_path = artifact / f"attempt-{index:04d}.stderr"
        output_path = artifact / f"attempt-{index:04d}.output"
        for path in (stdout_path, stderr_path):
            if not path.exists():
                path.write_bytes(b"")
        attempt = {
            "attempt_index": index,
            "accepted": False,
            "failure_class": "other",
            "evidence_status": "complete",
            "metering_status": "complete",
            "limit_trigger": None,
            "wall_clock_s": 1,
            "session_ids": [],
            "rollouts": [],
            "stdout_path": os.fspath(stdout_path),
            "stdout_sha256": empty_sha,
            "stdout_bytes": 0,
            "stderr_path": os.fspath(stderr_path),
            "stderr_sha256": empty_sha,
            "stderr_bytes": 0,
            "output_path": os.fspath(output_path),
            "output_sha256": None,
            "output_bytes": 0,
            "model_calls": 0,
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "total_tokens_raw": 0,
            "cli_reported": 0,
            "codex_exit_code": 0,
            "validator_rc": 0,
            "process_group_residual": 0,
            "termination_verified": True,
        }
        attempt.update(overrides)
        if "failure_class" not in overrides:
            sealed_output_path = Path(attempt["output_path"])
            validator_failures = (
                LAUNCHER._validator_failures(sealed_output_path)
                if sealed_output_path.exists()
                else None
            )
            attempt["failure_class"] = LAUNCHER._classify_failure(
                attempt["codex_exit_code"],
                attempt["output_bytes"],
                validator_failures,
            )
        attempts.append(attempt)
    actuals = {
        "wall_clock_s": sum(item["wall_clock_s"] for item in attempts),
        "attempt_count": len(attempts),
        "model_calls": sum(item["model_calls"] for item in attempts),
        "input_tokens": sum(item["input_tokens"] for item in attempts),
        "cached_input_tokens": sum(
            item["cached_input_tokens"] for item in attempts
        ),
        "output_tokens": sum(item["output_tokens"] for item in attempts),
        "reasoning_output_tokens": sum(
            item["reasoning_output_tokens"] for item in attempts
        ),
        "total_tokens_raw": sum(
            item["total_tokens_raw"] for item in attempts
        ),
        "cli_reported": sum(item["cli_reported"] for item in attempts),
    }
    triggered = [
        item["limit_trigger"]
        for item in attempts
        if item["limit_trigger"] is not None
    ]
    last = attempts[-1]
    receipt = {
        "schema_version": 2,
        "job_id": "diagnostic-job",
        "prompt_sha256": "1" * 64,
        "model": "gpt-5.6-sol",
        "reasoning": "high",
        "sandbox": "read-only",
        "cwd": os.fspath(_ROOT),
        "artifact_dir": os.fspath(artifact),
        "output_path": os.fspath(artifact / "published-output.md"),
        "output_sha256": None,
        "manifest_path": os.fspath(artifact / "manifest.json"),
        "manifest_wave_id": "diagnostic-wave",
        "manifest_repo_root": os.fspath(_ROOT),
        "manifest_base_commit": _BASE_COMMIT,
        "codex_version": "fake" + "x" * codex_version_padding,
        "codex_executable_path": os.fspath(_LAUNCHER),
        "codex_executable_sha256": "2" * 64,
        "model_calls_semantics": "observed_token_count_events",
        "possible_unobserved_overshoot": any(
            item["metering_status"] != "complete"
            or item["limit_trigger"] is not None
            for item in attempts
        ),
        "limits_assertion": "self_asserted",
        "wall_clock_scope": "launcher_start_to_receipt_fields_finalized",
        "retry_classification": "none",
        "escaped_process_containment": "not_attempted",
        "limits": {
            "wall_clock_admission_bound_s": max(100, len(attempts) + 1),
            "max_model_calls": 100,
            "max_cli_reported_tokens": 100000,
            "max_attempts": len(attempts),
        },
        "actuals": actuals,
        "outcome": "not_accepted",
        "stop_reason": triggered[0] if triggered else "max_attempts",
        "launcher_rc": 1,
        "codex_exit_code": last["codex_exit_code"],
        "validator_rc": last["validator_rc"],
        "attempts": attempts,
    }
    LAUNCHER._validate_receipt(receipt)
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return receipt


def test_launcher_failure_diagnostic_reports_failed_predicates(
    tmp_path: Path,
) -> None:
    with pytest.raises(LauncherReturncodeMismatch) as caught:
        _run_case(tmp_path, "no_token", expected_returncode=99, max_wall="11")

    message = str(caught.value)
    first_line = message.splitlines()[0]
    assert first_line.startswith("actual rc ")
    assert first_line.endswith(
        " != expected rc 99; label=launcher"
    )
    observed_rc = first_line.removeprefix("actual rc ").split(" != ", 1)[0]
    assert "accepted=False" in message
    assert 'failed_predicates=["metering_status"]' in message
    assert "不成立だったゲート" in message
    assert "receipt: outcome=" in message
    assert " stop_reason=" in message
    assert f" launcher_rc={observed_rc}" in message
    assert f"hostname={socket.gethostname()!r}" in message
    assert f"test_pid={os.getpid()}" in message
    assert "loadavg=" in message
    assert (
        f"PYTEST_XDIST_WORKER="
        f"{os.environ.get('PYTEST_XDIST_WORKER', '<unset>')!r}"
    ) in message
    assert f"PBS_JOBID={os.environ.get('PBS_JOBID', '<unset>')!r}" in message
    assert "launcher_budgets: wall='11' evidence='1.0'" in message
    assert "termination='0.05' poll='0.01'" in message
    assert "receipt_limits={" in message
    assert "'wall_clock_admission_bound_s'" in message
    assert "receipt_actuals={" in message
    assert "'attempt_count'" in message


def test_launcher_failure_diagnostic_reports_nonzero_codex_exit_code(
    tmp_path: Path,
) -> None:
    with pytest.raises(LauncherReturncodeMismatch) as caught:
        _run_case(tmp_path, "child_error", expected_returncode=99)

    message = str(caught.value)
    assert "codex_exit_code=7" in message
    assert 'failed_predicates=["codex_exit_code"]' in message


def test_launcher_failure_diagnostic_reports_validator_rejection(
    tmp_path: Path,
) -> None:
    with pytest.raises(LauncherReturncodeMismatch) as caught:
        _run_case(tmp_path, "retry_reject", expected_returncode=99)

    message = str(caught.value)
    assert "validator_rc=1" in message
    assert 'failed_predicates=["validator_rc"]' in message


def test_launcher_failure_diagnostic_reports_incomplete_evidence(
    tmp_path: Path,
) -> None:
    with pytest.raises(LauncherReturncodeMismatch) as caught:
        _run_case(tmp_path, "no_rollout", expected_returncode=99, max_wall="11")

    message = str(caught.value)
    assert "evidence_status='missing'" in message
    truth_lines = [
        line for line in message.splitlines() if line.startswith("truth_summary:")
    ]
    assert len(truth_lines) == 2
    assert "evidence_status" in truth_lines[-1]


def test_launcher_failure_diagnostic_survives_missing_or_invalid_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = {
        "receipt": tmp_path / "receipt.json",
        "artifact": tmp_path / "artifacts",
    }
    completed = subprocess.CompletedProcess(
        args=["launcher"], returncode=1, stdout="", stderr=""
    )

    with pytest.raises(LauncherReturncodeMismatch) as missing:
        _assert_launcher_returncode(completed, 0, paths=paths)
    missing_message = str(missing.value)
    assert missing_message.splitlines()[0] == (
        "actual rc 1 != expected rc 0; label=launcher"
    )
    assert "receipt_status=missing" in missing_message

    paths["receipt"].write_bytes(b'{"attempts":')
    with pytest.raises(LauncherReturncodeMismatch) as invalid:
        _assert_launcher_returncode(completed, 0, paths=paths)
    invalid_message = str(invalid.value)
    assert "receipt_status=invalid:strict-json" in invalid_message
    assert "observability_status=insufficient" in invalid_message
    assert "receipt_raw:" in invalid_message
    assert "failed_predicates" not in invalid_message
    assert "不成立だったゲート" not in invalid_message

    invalid_payloads = {
        "missing-field": b'{"schema_version":2,"attempts":[]}',
        "duplicate-key": b'{"schema_version":2,"schema_version":2}',
        "non-finite": b'{"schema_version":2,"wall_clock_s":NaN}',
    }
    for label, raw in invalid_payloads.items():
        paths["receipt"].write_bytes(raw)
        with pytest.raises(LauncherReturncodeMismatch) as structural:
            _assert_launcher_returncode(completed, 0, paths=paths, label=label)
        structural_message = str(structural.value)
        assert structural_message.splitlines()[0] == (
            f"actual rc 1 != expected rc 0; label={label}"
        )
        assert "receipt_status=invalid:" in structural_message
        assert "observability_status=insufficient" in structural_message
        assert "receipt_raw:" in structural_message
        assert "failed_predicates" not in structural_message
        assert "不成立だったゲート" not in structural_message

    receipt = _write_valid_diagnostic_receipt(paths, [{}])
    receipt["attempts"][0]["accepted"] = 0
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    with pytest.raises(LauncherReturncodeMismatch) as wrong_type:
        _assert_launcher_returncode(completed, 0, paths=paths, label="wrong-type")
    wrong_type_message = str(wrong_type.value)
    assert "receipt_status=invalid:schema-or-semantic:" in wrong_type_message
    assert "observability_status=insufficient" in wrong_type_message
    assert "receipt_raw:" in wrong_type_message
    assert "failed_predicates" not in wrong_type_message
    assert "不成立だったゲート" not in wrong_type_message

    timeout = subprocess.TimeoutExpired(
        cmd=["launcher"], timeout=10, output=b"\xffstdout", stderr=b"stderr"
    )
    with pytest.raises(LauncherReturncodeMismatch) as timed_out:
        _assert_launcher_returncode(timeout, 0, paths=paths)
    timeout_message = str(timed_out.value)
    assert timeout_message.splitlines()[0] == (
        "actual rc timeout != expected rc 0; label=launcher"
    )
    assert "\\xffstdout" in timeout_message

    with pytest.raises(LauncherReturncodeMismatch) as in_process:
        _assert_launcher_returncode(1, 0, paths=paths)
    in_process_message = str(in_process.value)
    assert "stdout: total_bytes=unavailable" in in_process_message
    assert "stderr: total_bytes=unavailable" in in_process_message
    assert in_process_message.count("path=<in-process>") == 2

    def fail_diagnostic(*_args: Any, **_kwargs: Any) -> str:
        raise OSError("synthetic diagnostic failure")

    monkeypatch.setattr(
        sys.modules[__name__], "_launcher_failure_message", fail_diagnostic
    )
    with pytest.raises(LauncherReturncodeMismatch) as diagnostic_failure:
        _assert_launcher_returncode(completed, 0, paths=paths)
    failure_message = str(diagnostic_failure.value)
    assert failure_message.splitlines()[0] == (
        "actual rc 1 != expected rc 0; label=launcher"
    )
    assert "diagnostic_status=failed:OSError" in failure_message


def test_launcher_failure_diagnostic_is_wired_to_the_returncode_assertion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = "formatter-sentinel-7d231d\ntruth_summary: sentinel-7d231d"
    calls: list[object] = []

    def sentinel_formatter(*args: Any, **_kwargs: Any) -> str:
        calls.append(args[0])
        return sentinel

    monkeypatch.setattr(
        sys.modules[__name__], "_launcher_failure_message", sentinel_formatter
    )

    subprocess_root = tmp_path / "subprocess-run"
    subprocess_root.mkdir()
    with pytest.raises(LauncherReturncodeMismatch) as run_case:
        _run_case(
            subprocess_root, "normal", expected_returncode=99, max_wall="11"
        )

    popen_root = tmp_path / "direct-popen"
    popen_root.mkdir()
    fake = _write_fake_codex(popen_root / "fake-codex")
    command, env, paths = _base_command(
        popen_root, fake=fake, max_wall="11"
    )
    env["FAKE_MODE"] = "normal"
    process = subprocess.Popen(
        command,
        env=env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    with pytest.raises(LauncherReturncodeMismatch) as direct_popen:
        _communicate_launcher(
            process,
            paths=paths,
            expected_returncode=99,
            label="direct-popen sentinel",
        )

    in_process_root = tmp_path / "in-process"
    in_process_root.mkdir()
    in_process_fake = _write_fake_codex(in_process_root / "fake-codex")
    in_process_command, in_process_env, in_process_paths = _base_command(
        in_process_root, fake=in_process_fake, max_wall="11"
    )
    in_process_env["FAKE_MODE"] = "normal"
    with pytest.raises(LauncherReturncodeMismatch) as in_process:
        _run_main_in_process(
            in_process_command,
            in_process_env,
            monkeypatch,
            paths=in_process_paths,
            expected_returncode=99,
        )

    for caught, label in (
        (run_case, "launcher"),
        (direct_popen, "direct-popen sentinel"),
        (in_process, "in-process launcher"),
    ):
        lines = str(caught.value).splitlines()
        assert lines[0].startswith("actual rc ")
        assert lines[0].endswith(f" != expected rc 99; label={label}")
        assert lines[1:] == [
            "formatter-sentinel-7d231d",
            "truth_summary: sentinel-7d231d",
        ]
    assert len(calls) == 3
    assert isinstance(calls[0], subprocess.CompletedProcess)
    assert calls[1] is process
    assert isinstance(calls[2], int)


def test_launcher_failure_diagnostic_is_bounded_and_repeats_summary_at_end(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "artifacts"
    artifact.mkdir()
    stdout_path = artifact / "stdout.bin"
    stderr_path = artifact / "stderr.bin"
    stdout_payload = b"head-\xff" + b"x" * 30000 + b"-tail"
    stderr_payload = b"error-head" + b"y" * 30000 + b"error-tail"
    stdout_path.write_bytes(stdout_payload)
    stderr_path.write_bytes(stderr_payload)
    receipt_path = tmp_path / "receipt.json"
    paths = {"receipt": receipt_path, "artifact": artifact}
    _write_valid_diagnostic_receipt(
        paths,
        [
            {
                "evidence_status": "missing",
                "wall_clock_s": 1,
                "stdout_path": os.fspath(stdout_path),
                "stderr_path": os.fspath(stderr_path),
            }
            for _ in range(6)
        ],
    )
    completed = subprocess.CompletedProcess(
        args=["launcher"],
        returncode=1,
        stdout="z" * 30000,
        stderr="w" * 30000,
    )

    with pytest.raises(LauncherReturncodeMismatch) as caught:
        _assert_launcher_returncode(completed, 0, paths=paths)

    message = str(caught.value)
    lines = message.splitlines()
    assert len(message.encode("utf-8")) <= _DIAGNOSTIC_MAX_BYTES
    assert lines[0] == "actual rc 1 != expected rc 0; label=launcher"
    assert "total_bytes=30011" in message
    assert f"sha256={hashlib.sha256(stdout_payload).hexdigest()}" in message
    assert "truncated_bytes=27963" in message
    assert "\\xff" in message
    assert lines[-1].startswith("truth_summary:")
    assert lines.count(lines[-1]) == 2


def test_launcher_failure_diagnostic_reports_all_visible_failures_and_guard(
    tmp_path: Path,
) -> None:
    paths = {
        "receipt": tmp_path / "receipt.json",
        "artifact": tmp_path / "artifacts",
    }
    completed = subprocess.CompletedProcess(
        args=["launcher"], returncode=1, stdout="", stderr=""
    )
    _write_valid_diagnostic_receipt(
        paths,
        [
            {
                "limit_trigger": "max_model_calls",
                "evidence_status": "missing",
                "metering_status": "incomplete",
                "codex_exit_code": 7,
                "validator_rc": 1,
                "process_group_residual": 2,
                "termination_verified": False,
            }
        ],
    )
    with pytest.raises(LauncherReturncodeMismatch) as multiple:
        _assert_launcher_returncode(completed, 0, paths=paths)
    multiple_message = str(multiple.value)
    assert (
        'failed_predicates=["limit_trigger","evidence_status",'
        '"metering_status","codex_exit_code","validator_rc",'
        '"process_group_residual","termination_verified"]'
    ) in multiple_message

    _write_valid_diagnostic_receipt(paths, [{}])
    with pytest.raises(LauncherReturncodeMismatch) as hidden_guard:
        _assert_launcher_returncode(completed, 0, paths=paths)
    hidden_guard_message = str(hidden_guard.value)
    assert 'failed_predicates=["unrecorded_acceptance_guard"]' in (
        hidden_guard_message
    )
    assert 'failed_predicates=["accepted"]' not in hidden_guard_message


def test_missing_output_failure_class_recomputation_skips_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = {
        "receipt": tmp_path / "receipt.json",
        "artifact": tmp_path / "artifacts",
    }

    def unexpected_validator_call(_path: Path) -> list[str]:
        raise AssertionError("missing output must not be passed to the validator")

    monkeypatch.setattr(
        LAUNCHER, "_validator_failures", unexpected_validator_call
    )
    receipt = _write_valid_diagnostic_receipt(paths, [{}])

    assert receipt["attempts"][0]["output_sha256"] is None
    assert receipt["attempts"][0]["failure_class"] == "other"


def test_launcher_failure_diagnostic_rejects_fifo_and_over_limit_streams(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "artifacts"
    artifact.mkdir()
    fifo = artifact / "stdout.fifo"
    os.mkfifo(fifo)
    oversized = artifact / "stderr.large"
    oversized.write_bytes(b"x" * (_STREAM_READ_MAX_BYTES + 1))
    paths = {"receipt": tmp_path / "receipt.json", "artifact": artifact}
    _write_valid_diagnostic_receipt(
        paths,
        [
            {
                "evidence_status": "missing",
                "stdout_path": os.fspath(fifo),
                "stderr_path": os.fspath(oversized),
            }
        ],
    )
    completed = subprocess.CompletedProcess(
        args=["launcher"], returncode=1, stdout="", stderr=""
    )
    with pytest.raises(LauncherReturncodeMismatch) as stream_failure:
        _assert_launcher_returncode(completed, 0, paths=paths)
    stream_message = str(stream_failure.value)
    assert stream_message.splitlines()[0] == (
        "actual rc 1 != expected rc 0; label=launcher"
    )
    assert "attempt[1].stdout:" in stream_message
    assert "stream_status=unreadable:non-regular" in stream_message
    assert "attempt[1].stderr:" in stream_message
    assert "stream_status=unreadable:too-large" in stream_message

    paths["receipt"].unlink()
    os.mkfifo(paths["receipt"])
    with pytest.raises(LauncherReturncodeMismatch) as fifo_receipt:
        _assert_launcher_returncode(completed, 0, paths=paths)
    fifo_message = str(fifo_receipt.value)
    assert fifo_message.splitlines()[0] == (
        "actual rc 1 != expected rc 0; label=launcher"
    )
    assert "receipt_status=unreadable:non-regular" in fifo_message
    assert "observability_status=insufficient" in fifo_message


def test_launcher_failure_diagnostic_preserves_last_of_many_large_attempts(
    tmp_path: Path,
) -> None:
    paths = {
        "receipt": tmp_path / "receipt.json",
        "artifact": tmp_path / "artifacts",
    }
    attempts = [{} for _ in range(9)] + [{"evidence_status": "missing"}]
    _write_valid_diagnostic_receipt(
        paths, attempts, codex_version_padding=600 * 1024
    )
    assert _RECEIPT_MAX_BYTES == 16 * 1024 * 1024
    assert 512 * 1024 < paths["receipt"].stat().st_size < _RECEIPT_MAX_BYTES
    completed = subprocess.CompletedProcess(
        args=["launcher"], returncode=1, stdout="", stderr=""
    )
    with pytest.raises(LauncherReturncodeMismatch) as caught:
        _assert_launcher_returncode(completed, 0, paths=paths)
    message = str(caught.value)
    lines = message.splitlines()
    assert len(message.encode("utf-8")) <= _DIAGNOSTIC_MAX_BYTES
    assert "receipt_status=invalid:too-large" not in message
    assert "attempt[9] accepted=False" in lines[-1]
    assert "attempt[10] accepted=False" in lines[-1]
    assert 'attempt[10] accepted=False failed_predicates=["evidence_status"]' in (
        lines[-1]
    )
    assert lines[-1].startswith("truth_summary:")


def test_positive_p1_normal_job_is_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )

    assert receipt is not None
    assert receipt["outcome"] == "accepted"
    assert receipt["stop_reason"] == "completed"
    assert receipt["launcher_rc"] == 0
    assert receipt["model_calls_semantics"] == "observed_token_count_events"
    assert receipt["schema_version"] == 5
    assert receipt["limits_assertion"] == "self_asserted"
    assert (
        receipt["wall_clock_scope"]
        == "launcher_start_to_receipt_fields_finalized"
    )
    assert receipt["repo_root"] == os.fspath(_ROOT)
    assert receipt["base_commit"] == _BASE_COMMIT
    derived = LAUNCHER.derive_launch(
        LAUNCHER.snapshot_authority(_ROOT), stage="author", lane=None
    )
    assert receipt["requested_model"] == derived.model
    assert receipt["requested_effort"] == derived.effort
    assert receipt["requested_effort"] == receipt["recorded_effort"]
    assert receipt["recorded_model"] == derived.model
    assert receipt["recorded_turn_context_count"] >= 1
    assert receipt["possible_unobserved_overshoot"] is False
    assert receipt["retry_classification"] == "none"
    assert receipt["escaped_process_containment"] == "not_attempted"
    assert receipt["attempts"][0]["accepted"] is True
    assert receipt["attempts"][0]["failure_class"] is None
    assert receipt["attempts"][0]["metering_status"] == "complete"
    assert receipt["attempts"][0]["process_group_residual"] == 0
    assert receipt["attempts"][0]["termination_verified"] is True
    assert paths["output"].read_text(encoding="utf-8").endswith(
        "fake Codex 完了\n"
    )
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert set(manifest) == {
        "schema_version",
        "wave_id",
        "sessions",
    }
    assert manifest["schema_version"] == 2
    assert manifest["wave_id"] == "wave-a"
    assert len(manifest["sessions"]) == 1
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_f43_fragment_is_classified_and_retried(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "retry_reject",
        expected_returncode=0,
        fake_sequence="retry_reject,normal",
        max_attempts=2,
        max_wall="10",
        evidence_grace="3",
        sandbox="read-only",
    )
    assert receipt is not None
    assert completed.returncode == 0
    assert [item["failure_class"] for item in receipt["attempts"]] == [
        "f43_fragment",
        None,
    ]
    assert paths["counter"].read_text(encoding="ascii") == "2"
    assert receipt["outcome"] == "accepted"


def test_f43_heading_missing_is_classified(tmp_path: Path) -> None:
    _completed, receipt, _paths = _run_case(
        tmp_path,
        "heading_missing",
        expected_returncode=1,
        max_wall="10",
        evidence_grace="3",
    )
    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["codex_exit_code"] == 0
    assert attempt["validator_rc"] == 1
    assert attempt["failure_class"] == "f43_fragment"


@pytest.mark.parametrize("mode", ["non_utf8", "oversized"])
def test_f43_fragment_excludes_non_utf8_and_oversized_output(
    tmp_path: Path, mode: str
) -> None:
    _completed, receipt, _paths = _run_case(
        tmp_path,
        mode,
        expected_returncode=1,
        max_wall="10",
        evidence_grace="3",
    )
    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["codex_exit_code"] == 0
    assert attempt["validator_rc"] == 1
    assert attempt["failure_class"] == "other"


@pytest.mark.parametrize("mode", ["missing_output", "empty_output"])
def test_f45_zero_or_missing_output_fails_closed_without_retry(
    tmp_path: Path, mode: str
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        mode,
        expected_returncode=2,
        max_attempts=3,
        max_wall="10",
        evidence_grace="3",
        sandbox="read-only",
    )
    assert receipt is not None
    assert completed.returncode == 2
    assert receipt["outcome"] == "launcher_error"
    assert receipt["attempts"][0]["failure_class"] == "f45_missing_output"
    assert len(receipt["attempts"]) == 1
    assert paths["counter"].read_text(encoding="ascii") == "1"
    assert not paths["output"].exists()


def test_positive_accepted_attempt_has_no_failure_class_and_no_retry(
    tmp_path: Path,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path,
        "normal",
        expected_returncode=0,
        max_attempts=2,
        max_wall="10",
        evidence_grace="3",
        sandbox="read-only",
    )
    assert receipt is not None
    assert receipt["attempts"][-1]["accepted"] is True
    assert receipt["attempts"][-1]["failure_class"] is None
    assert len(receipt["attempts"]) == 1
    assert paths["counter"].read_text(encoding="ascii") == "1"


@pytest.mark.parametrize("mode", ["normal", "retry_reject", "child_error"])
def test_workspace_write_failure_classification_is_sandbox_independent(
    tmp_path: Path, mode: str
) -> None:
    expected = {
        "normal": (0, None),
        "retry_reject": (1, "f43_fragment"),
        "child_error": (1, "other"),
    }
    expected_returncode, failure_class = expected[mode]
    _completed, receipt, _paths = _run_case(
        tmp_path,
        mode,
        expected_returncode=expected_returncode,
        max_wall="10",
        evidence_grace="3",
        sandbox="workspace-write",
    )
    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["failure_class"] == failure_class
    if mode == "normal":
        assert attempt["accepted"] is True


@pytest.mark.parametrize("mode", ["missing_output", "empty_output"])
def test_workspace_write_f45_is_classified_without_retry(
    tmp_path: Path, mode: str
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path,
        mode,
        expected_returncode=1,
        max_wall="10",
        evidence_grace="3",
        sandbox="workspace-write",
    )
    assert receipt is not None
    assert receipt["outcome"] == "not_accepted"
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["launcher_rc"] == 1
    assert receipt["attempts"][0]["failure_class"] == "f45_missing_output"
    assert len(receipt["attempts"]) == 1
    assert paths["counter"].read_text(encoding="ascii") == "1"


def test_default_max_attempts_observes_failure_class_without_retry(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        sandbox="read-only",
        max_wall="10",
        evidence_grace="3",
    )
    _remove_option(command, "--max-attempts")
    env["FAKE_MODE"] = "missing_output"
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    assert receipt["limits"]["max_attempts"] == 1
    assert receipt["outcome"] == "not_accepted"
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["launcher_rc"] == 1
    assert receipt["attempts"][0]["failure_class"] == "f45_missing_output"
    assert paths["counter"].read_text(encoding="ascii") == "1"


def test_failure_class_enum_and_receipt_recomputation_are_closed(
    tmp_path: Path,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path,
        "retry_reject",
        expected_returncode=1,
        max_wall="10",
        evidence_grace="3",
    )
    assert receipt is not None
    attempt = receipt["attempts"][0]

    attempt["failure_class"] = "forged-class"
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    invalid = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert invalid.returncode == 2

    attempt["failure_class"] = None
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    forged = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert forged.returncode == 2
    assert "failure_class" in forged.stderr

    attempt.pop("failure_class")
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    missing = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert missing.returncode == 2

    accepted_root = tmp_path / "accepted"
    accepted_root.mkdir()
    _completed, _accepted_receipt, accepted_paths = _run_case(
        accepted_root,
        "normal",
        expected_returncode=0,
        max_wall="10",
        evidence_grace="3",
    )
    assert _accepted_receipt is not None
    validated_accepted = LAUNCHER._validate_receipt(
        LAUNCHER._load_json(accepted_paths["receipt"], label="test receipt")
    )
    accepted_attempt = dict(validated_accepted["attempts"][0])
    invalid_output = tmp_path / "accepted-invalid-output.md"
    invalid_output.write_text(
        ("十分な検査本文です。" * 80) + "\n", encoding="utf-8"
    )
    accepted_attempt["output_path"] = str(invalid_output)
    accepted_attempt["failure_class"] = "f43_fragment"
    with pytest.raises(
        LAUNCHER.LaunchError, match="accepted attempt.failure_class"
    ):
        LAUNCHER._validate_attempt(accepted_attempt, index=0)


def _consume_real_stdout_fixture(
    name: str, *, omitted_line_indexes: frozenset[int] = frozenset()
) -> LAUNCHER.AttemptState:
    path = _REAL_EVENT_FIXTURES / name
    state = LAUNCHER.AttemptState(
        attempt_index=1,
        started_ns=0,
        stdout_path=path,
        stderr_path=path.with_suffix(".stderr"),
        output_path=path.with_suffix(".output"),
    )
    for index, line in enumerate(path.read_bytes().splitlines()):
        if index in omitted_line_indexes:
            continue
        event = json.loads(line)
        assert isinstance(event, dict)
        LAUNCHER._consume_stdout_event(state, event)
    return state


def test_real_accepted_stdout_ignores_pre_turn_hook_trust_diagnostics() -> None:
    with_diagnostics = _consume_real_stdout_fixture(
        "probe-inturn.events.jsonl"
    )
    without_diagnostics = _consume_real_stdout_fixture(
        "probe-inturn.events.jsonl",
        omitted_line_indexes=frozenset({1, 2}),
    )

    assert with_diagnostics == without_diagnostics
    assert with_diagnostics.session_ids == [
        "019ffa55-8dc0-72e1-b93b-d2d33690c668"
    ]
    assert with_diagnostics.terminal_usage is not None


def test_real_pre_turn_only_stdout_has_session_without_terminal_usage() -> None:
    state = _consume_real_stdout_fixture(
        "rulings-small6-failed.events.jsonl"
    )

    assert state.session_ids == ["019ff8f3-6c4d-7751-92c9-c45f9ad00ab0"]
    assert state.terminal_usage is None


@pytest.mark.parametrize(
    "value",
    (
        "0",
        "-1",
        "NaN",
        "Infinity",
        "1e-10000",
        "9.999999999999999999999999999999999999e-10",
        "1e10000",
    ),
)
def test_launcher_rejects_unsafe_evidence_grace_before_child_launch(
    tmp_path: Path, value: str
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    command[command.index("--evidence-grace-s") + 1] = value

    completed = _run_launcher_subprocess(
        command,
        env=env,
        paths=paths,
        expected_returncode=2,
    )

    assert completed.returncode == 2
    assert "正の有限数で nanosecond へ安全に変換" in completed.stderr
    assert not paths["receipt"].exists()


def test_unknown_reasoning_is_rejected_before_child_launch(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        reasoning="none",
    )

    completed = _run_launcher_subprocess(
        command,
        env=env,
        paths=paths,
        expected_returncode=2,
    )

    assert "invalid choice" in completed.stderr
    assert "--reasoning" in completed.stderr
    assert not paths["receipt"].exists()
    assert not paths["manifest"].exists()
    assert not paths["pid_dir"].exists()
    assert not paths["counter"].exists()
    assert not paths["artifact"].exists()
    assert not paths["output"].exists()
    assert not paths["codex_home"].exists()


@pytest.mark.parametrize(
    "reasoning",
    ("low", "medium", "high", "xhigh", "max"),
)
def test_all_repo_policy_reasoning_values_are_accepted(
    tmp_path: Path,
    reasoning: str,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "normal",
        expected_returncode=0,
        stage="plan",
        reasoning=reasoning,
    )

    assert receipt is not None
    assert receipt["requested_effort"] == reasoning


def test_authority_bound_reasoning_is_rejected_before_all_side_effects(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, stage="review", reasoning="high"
    )
    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=2
    )
    assert "--reasoning" in completed.stderr
    for key in (
        "receipt",
        "manifest",
        "pid_dir",
        "counter",
        "artifact",
        "output",
        "codex_home",
    ):
        assert not paths[key].exists()


@pytest.mark.parametrize("stage", ("author", "fix"))
def test_author_and_fix_reasoning_is_rejected_before_all_side_effects(
    tmp_path: Path,
    stage: str,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, stage=stage, reasoning="high"
    )
    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=2
    )
    assert "--reasoning" in completed.stderr
    for key in (
        "receipt",
        "manifest",
        "pid_dir",
        "counter",
        "artifact",
        "output",
        "codex_home",
    ):
        assert not paths[key].exists()


@pytest.mark.parametrize(
    ("stage", "lane"),
    (("consult", None), ("author", "sol")),
)
def test_stage_lane_contract_fails_before_side_effects(
    tmp_path: Path, stage: str, lane: str | None
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, stage=stage, lane=lane
    )
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=2
    )
    assert not paths["artifact"].exists()
    assert not paths["receipt"].exists()
    assert not paths["manifest"].exists()
    assert not paths["pid_dir"].exists()


def test_run_cli_has_no_model_override(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    command.extend(("--model", "decoy-model"))
    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=2
    )
    assert "unrecognized arguments" in completed.stderr
    assert not paths["artifact"].exists()


def test_authority_bound_launch_uses_derived_model_and_effort(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, stage="review"
    )
    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=0
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    derived = LAUNCHER.derive_launch(
        LAUNCHER.snapshot_authority(_ROOT), stage="review", lane=None
    )
    assert receipt["requested_model"] == derived.model
    assert receipt["requested_effort"] == derived.effort
    assert receipt["effort_authority"] == derived.effort_authority
    argv_path = next(paths["pid_dir"].glob("argv-*.json"))
    argv = json.loads(argv_path.read_text(encoding="utf-8"))
    assert argv[argv.index("-m") + 1] == derived.model
    assert argv[argv.index("-c") + 1] == (
        f'model_reasoning_effort="{derived.effort}"'
    )
    assert completed.returncode == 0


def test_codex_argv_has_exact_trust_bypass_without_sandbox_bypass(
    tmp_path: Path,
) -> None:
    _completed, _receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0, sandbox="read-only"
    )
    argv = json.loads(
        next(paths["pid_dir"].glob("argv-*.json")).read_text(encoding="utf-8")
    )
    assert (
        LAUNCHER._hook_checker.TRUST_BYPASS_FLAG
        == _EXPECTED_TRUST_BYPASS_FLAG
    )
    assert argv.count(_EXPECTED_TRUST_BYPASS_FLAG) == 1
    assert LAUNCHER._hook_checker.SANDBOX_BYPASS_FLAG not in argv
    assert argv[argv.index("-s") + 1] == "read-only"


def test_clean_committed_hook_fixture_allows_launcher_to_spawn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _prepare_authority_repo(tmp_path / "authority-repo")
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        repo_root=repo,
        cwd=repo,
        base_commit=commit,
    )
    env["FAKE_MODE"] = "normal"
    assert _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=0
    ) == 0
    assert paths["counter"].read_text(encoding="ascii") == "1"


def test_guard_bytes_mismatch_is_launch_error(tmp_path: Path) -> None:
    repo, _commit = _prepare_authority_repo(tmp_path / "authority-repo")
    relative = Path("tools/pegasus/admission_registry.json")
    with (repo / relative).open("ab") as stream:
        stream.write(b"\n ")
    with pytest.raises(
        LAUNCHER.LaunchError,
        match=r"tools/pegasus/admission_registry\.json.*HEAD blob",
    ):
        LAUNCHER._require_attempt_hook_installation(repo, repo)


def test_guard_bytes_mismatch_prevents_codex_popen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _prepare_authority_repo(tmp_path / "authority-repo")
    relative = Path("hooks/guard_bash.py")
    with (repo / relative).open("ab") as stream:
        stream.write(b"\n# inert drift\n")
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        repo_root=repo,
        cwd=repo,
        base_commit=commit,
    )
    env["FAKE_MODE"] = "normal"
    real_popen = subprocess.Popen
    codex_spawns = []

    def popen_spy(argv, *args, **kwargs):
        if kwargs.get("start_new_session") is True:
            codex_spawns.append(list(argv))
        return real_popen(argv, *args, **kwargs)

    monkeypatch.setattr(LAUNCHER.subprocess, "Popen", popen_spy)
    assert _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=2
    ) == 2
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    assert receipt["outcome"] == "launcher_error"
    assert receipt["attempts"] == []
    assert codex_spawns == []
    assert not paths["pid_dir"].exists()


def test_hook_preflight_rejection_prevents_codex_exec_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    monkeypatch.setattr(
        LAUNCHER._hook_checker,
        "validate_installation",
        lambda _root: ["synthetic drift"],
    )
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        LAUNCHER, "_LAUNCHER_PROCESS_STARTED_NS", time.monotonic_ns()
    )
    LAUNCHER.main(command[2:])
    assert not paths["pid_dir"].exists()


def test_hook_preflight_rejection_returns_launcher_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    monkeypatch.setattr(
        LAUNCHER._hook_checker,
        "validate_installation",
        lambda _root: ["synthetic drift"],
    )
    assert _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=2
    ) == 2


def test_hook_preflight_validates_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots = []
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, cwd=_ROOT / "orchestrator" / "tests"
    )

    def validator(root):
        roots.append(root)
        return []

    monkeypatch.setattr(
        LAUNCHER._hook_checker, "validate_installation", validator
    )
    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=0
    )
    assert roots == [_ROOT]


def test_hook_preflight_wraps_validator_exception_as_launch_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_root):
        raise RuntimeError("validator failure")

    monkeypatch.setattr(
        LAUNCHER._hook_checker, "validate_installation", fail
    )
    with pytest.raises(LAUNCHER.LaunchError, match="validator failure"):
        LAUNCHER._require_attempt_hook_installation(_ROOT, _ROOT)


@pytest.mark.parametrize(
    "exception_type", (KeyboardInterrupt, SystemExit, GeneratorExit)
)
def test_attempt_loop_propagates_non_exception_baseexceptions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[BaseException],
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)

    def interrupt(_root: Path) -> None:
        raise exception_type()

    monkeypatch.setattr(
        LAUNCHER._hook_checker, "validate_installation", interrupt
    )
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        LAUNCHER, "_LAUNCHER_PROCESS_STARTED_NS", time.monotonic_ns()
    )
    with pytest.raises(exception_type):
        LAUNCHER.main(command[2:])
    assert not paths["pid_dir"].exists()


def test_hook_preflight_is_rechecked_before_each_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots = []
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, sandbox="read-only", max_attempts=2,
    )
    env["FAKE_SEQUENCE"] = "retry_reject,normal"

    def validator(root):
        roots.append(root)
        return [] if len(roots) == 1 else ["retry drift"]

    monkeypatch.setattr(
        LAUNCHER._hook_checker, "validate_installation", validator
    )
    rc = _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=2
    )
    assert rc == 2
    assert roots == [_ROOT, _ROOT]
    assert paths["counter"].read_text(encoding="ascii") == "1"


def test_attempt_preflight_rejects_nested_linked_worktree_top_level(
    tmp_path: Path,
) -> None:
    main, _commit = _prepare_authority_repo(tmp_path / "main-repo")
    nested = main / "nested-worktree"
    subprocess.run(
        [
            "git", "-C", os.fspath(main), "worktree", "add", "--detach", "-q",
            os.fspath(nested),
        ],
        check=True,
    )
    try:
        with pytest.raises(LAUNCHER.LaunchError, match="top-level"):
            LAUNCHER._require_attempt_hook_installation(main, nested)
    finally:
        _remove_authority_worktree(main, nested)


@pytest.mark.parametrize(
    "stdout", ("", "/repo/one\n/repo/two\n", "relative/repo\n"),
    ids=("empty", "multiple-lines", "non-absolute"),
)
def test_attempt_preflight_rejects_malformed_git_top_level_stdout(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
) -> None:
    completed = subprocess.CompletedProcess(
        args=["git"], returncode=0, stdout=stdout, stderr=""
    )
    monkeypatch.setattr(
        LAUNCHER.subprocess, "run", lambda *_args, **_kwargs: completed
    )
    monkeypatch.setattr(
        LAUNCHER._hook_checker,
        "validate_installation",
        lambda _root: pytest.fail("malformed top-level 後に validator を呼んだ"),
    )
    with pytest.raises(LAUNCHER.LaunchError, match="top-level"):
        LAUNCHER._require_attempt_hook_installation(_ROOT, _ROOT)


def test_attempt_preflight_delay_exhausts_wall_clock_before_spawn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, max_wall="3"
    )
    command.extend(("--preparation-admission-bound-s", "3"))
    clock_ns = time.monotonic_ns()
    offset_ns = 0

    def logical_clock() -> int:
        return clock_ns + offset_ns

    def delayed_validator(_root: Path) -> list[str]:
        nonlocal offset_ns
        offset_ns += 4_000_000_000
        return []

    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(LAUNCHER, "_LAUNCHER_PROCESS_STARTED_NS", clock_ns)
    monkeypatch.setattr(LAUNCHER, "_monotonic_ns", logical_clock)
    monkeypatch.setattr(
        LAUNCHER._hook_checker,
        "validate_installation",
        delayed_validator,
    )
    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    assert receipt["outcome"] == "not_accepted"
    assert receipt["stop_reason"] == "preparation_admission_bound_s"
    assert receipt["launcher_rc"] == 1
    assert (
        receipt["actuals"]["preparation_wall_clock_s"]
        >= receipt["limits"]["preparation_admission_bound_s"]
    )
    assert receipt["attempts"] == []
    assert not paths["pid_dir"].exists()


def _install_evidence_origin_logical_clock(
    monkeypatch: pytest.MonkeyPatch,
    *,
    first_attempt_evidence_ready: Path | None = None,
) -> None:
    clock_ns = time.monotonic_ns()
    polling = False
    spawn_sample_pending = False
    original_validator = LAUNCHER._hook_checker.validate_installation
    original_read_pid_identity = LAUNCHER.read_pid_identity

    def logical_clock() -> int:
        nonlocal clock_ns, polling, spawn_sample_pending
        if spawn_sample_pending:
            spawn_sample_pending = False
            polling = True
        elif polling:
            # 子が最初の evidence を確定するまでの scheduler 遅延は、test の
            # grace 用論理時間へ算入しない。retry では既存 marker により進む。
            first_attempt_evidence_pending = (
                first_attempt_evidence_ready is not None
                and not first_attempt_evidence_ready.exists()
            )
            if not first_attempt_evidence_pending:
                clock_ns += 10_000_000
        return clock_ns

    def delayed_validator(root: Path) -> list[str]:
        nonlocal clock_ns, polling, spawn_sample_pending
        result = original_validator(root)
        polling = False
        spawn_sample_pending = False
        clock_ns += 100_000_000
        return result

    def delayed_read_pid_identity(pid: int) -> LAUNCHER.PidIdentity:
        nonlocal clock_ns, spawn_sample_pending
        try:
            return original_read_pid_identity(pid)
        finally:
            clock_ns += 20_000_000
            spawn_sample_pending = True

    monkeypatch.setattr(LAUNCHER, "_monotonic_ns", logical_clock)
    monkeypatch.setattr(
        LAUNCHER._hook_checker,
        "validate_installation",
        delayed_validator,
    )
    monkeypatch.setattr(
        LAUNCHER, "read_pid_identity", delayed_read_pid_identity
    )


def _assert_spawn_origin_phase_durations(
    diagnostics: dict[str, Any], *, attempt_index: int
) -> None:
    phases = diagnostics["attempts"][attempt_index]["phase_duration_s"]
    expected_preflight = (
        Decimal("0.01") if attempt_index == 0 else Decimal("0.10")
    )
    assert Decimal(str(phases["attempt_preflight"])) == expected_preflight
    assert Decimal(str(phases["spawn"])) == Decimal("0.02")
    assert Decimal(str(phases["supervision_drain"])) == Decimal("0.05")


def test_evidence_grace_starts_at_spawn_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        evidence_grace="0.05",
        max_wall="11",
    )
    env["FAKE_MODE"] = "no_rollout"
    _install_evidence_origin_logical_clock(monkeypatch)

    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=1
    )

    diagnostics = _read_launcher_diagnostics(paths)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    assert Decimal(
        str(receipt["actuals"]["preparation_wall_clock_s"])
    ) >= Decimal("0.10")
    assert diagnostics["attempts"][0]["evidence_forced_stop"] is True
    _assert_spawn_origin_phase_durations(diagnostics, attempt_index=0)


def test_evidence_grace_starts_at_spawn_completed_on_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        evidence_grace="0.05",
        max_attempts=2,
        max_wall="11",
    )
    env["FAKE_SEQUENCE"] = "retry_reject,no_rollout"
    first_attempt_evidence_ready = tmp_path / "first-attempt-evidence-ready"
    env["FAKE_EVIDENCE_READY"] = os.fspath(first_attempt_evidence_ready)
    _install_evidence_origin_logical_clock(
        monkeypatch,
        first_attempt_evidence_ready=first_attempt_evidence_ready,
    )

    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=1
    )

    diagnostics = _read_launcher_diagnostics(paths)
    assert len(diagnostics["attempts"]) == 2
    assert diagnostics["attempts"][1]["evidence_forced_stop"] is True
    _assert_spawn_origin_phase_durations(diagnostics, attempt_index=1)


def test_turn_context_top_level_and_collaboration_decoys_are_rejected(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "payload_decoy", expected_returncode=1
    )
    assert receipt is not None
    assert completed.returncode == 1
    assert receipt["attempts"][0]["evidence_status"] == "invalid"
    assert receipt["recorded_model"] is None
    assert receipt["recorded_effort"] is None
    assert receipt["recorded_turn_context_count"] == 1
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert [entry["session_id"] for entry in manifest["sessions"]] == (
        receipt["attempts"][0]["session_ids"]
    )


def test_invalid_evidence_reason_is_recorded(tmp_path: Path) -> None:
    _completed, receipt, _paths = _run_case(
        tmp_path, "payload_decoy", expected_returncode=1
    )
    assert receipt is not None
    issues = receipt["attempts"][0]["evidence_issues"]
    assert any(
        issue["reason"] == "turn_context_invalid"
        and issue["count"] == 1
        and issue["source"] != "stdout"
        for issue in issues
    )


def test_correlated_authority_invalid_session_uses_nullable_manifest_value(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "cwd_missing", expected_returncode=1
    )
    assert receipt is not None
    assert completed.returncode == 1
    assert receipt["attempts"][0]["evidence_status"] == "invalid"
    assert receipt["recorded_cwd"] is None
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["sessions"][0]["recorded_cwd"] is None
    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 1, checked.stderr


def test_authority_bound_job_rejects_prior_invalid_attempt(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        stage="review",
        max_attempts=2,
        sandbox="read-only",
    )
    env["FAKE_SEQUENCE"] = "payload_decoy,normal"
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    assert [item["evidence_status"] for item in receipt["attempts"]] == [
        "invalid",
        "complete",
    ]
    assert receipt["attempts"][-1]["accepted"] is True
    assert receipt["outcome"] == "not_accepted"
    assert receipt["launcher_rc"] == 1


@pytest.mark.parametrize(
    ("stage", "lane"),
    [("author", None), ("consult", "sol")],
)
def test_all_v3_stages_reject_prior_invalid_attempt(
    stage: str,
    lane: str | None,
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        stage=stage,
        lane=lane,
        max_attempts=2,
        sandbox="read-only",
    )
    env["FAKE_SEQUENCE"] = "payload_decoy,normal"
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    assert [item["evidence_status"] for item in receipt["attempts"]] == [
        "invalid",
        "complete",
    ]
    assert receipt["attempts"][-1]["accepted"] is True
    assert receipt["outcome"] == "not_accepted"
    assert receipt["launcher_rc"] == 1


def test_checker_rejects_v3_acceptance_with_prior_invalid_attempt(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        stage="author",
        max_attempts=2,
        sandbox="read-only",
    )
    env["FAKE_SEQUENCE"] = "payload_decoy,normal"
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    final_attempt = receipt["attempts"][-1]
    receipt.update(
        {
            "outcome": "accepted",
            "stop_reason": "completed",
            "launcher_rc": 0,
            "output_sha256": final_attempt["output_sha256"],
        }
    )
    paths["output"].write_bytes(Path(final_attempt["output_path"]).read_bytes())
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n", encoding="utf-8"
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 2
    assert "truth table" in checked.stderr


def test_limit_stop_is_never_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "term_success",
        expected_returncode=1,
        max_calls=1,
        max_tokens=100000,
        max_wall="11",
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "max_model_calls"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] == "max_model_calls"
    assert receipt["attempts"][0]["codex_exit_code"] == 0
    assert receipt["attempts"][0]["validator_rc"] == 0
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["outcome"] == "not_accepted"
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_missing_metering_evidence_is_not_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "no_token",
        expected_returncode=1,
        max_calls=100,
        max_tokens=100000,
        max_wall="11",
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["metering_status"] == "missing"
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_token_cap_uses_cli_reported_definition(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "cli_exact",
        expected_returncode=0,
        max_calls=100,
        max_tokens=61,
        max_wall="11",
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "completed"
    assert receipt["actuals"]["input_tokens"] == 1000
    assert receipt["actuals"]["cached_input_tokens"] == 950
    assert receipt["actuals"]["output_tokens"] == 10
    assert receipt["actuals"]["cli_reported"] == 60
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["accepted"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_cli_reported_token_limit_stops_process(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "token_wait",
        expected_returncode=1,
        max_calls=100,
        max_tokens=50,
        max_wall="11",
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "max_cli_reported_tokens"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["actuals"]["cli_reported"] == 60
    assert (
        receipt["attempts"][0]["limit_trigger"]
        == "max_cli_reported_tokens"
    )
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_positive_p3_exact_limit_natural_exit_is_accepted(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "cli_exact",
        expected_returncode=0,
        max_calls=1,
        max_tokens=60,
        max_wall="11",
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "completed"
    assert receipt["actuals"]["model_calls"] == 1
    assert receipt["actuals"]["cli_reported"] == 60
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["accepted"] is True
    diagnostics = _read_launcher_diagnostics(paths)
    diagnostic_attempt = diagnostics["attempts"][0]
    assert diagnostics["receipt_binding"]["status"] == "sealed"
    assert diagnostic_attempt["evidence_forced_stop"] is False
    assert set(diagnostic_attempt["phase_duration_s"]) == {
        "attempt_preflight",
        "spawn",
        "supervision_drain",
        "process_reap",
        "final_drain",
        "artifact_handle_close",
        "attempt_wall_clock_sample",
        "attempt_seal",
    }
    assert (
        diagnostic_attempt["job_elapsed_s_at"]["attempt_state_created"]
        > diagnostic_attempt["attempt_elapsed_s_at"][
            "attempt_state_created"
        ]
    )
    assert "receipt_published" in diagnostics["job_elapsed_s_at"]
    natural_exit = [
        item
        for item in diagnostic_attempt["limit_condition_snapshots"]
        if item["site"] == "natural_exit"
    ]
    assert natural_exit[-1]["comparison"] == ">"
    assert natural_exit[-1]["conditions_met"] == []


def test_sigterm_ignoring_child_is_killed(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        max_wall="3",
        max_calls=100,
        max_tokens=100000,
    )
    env["FAKE_MODE"] = "sigterm_ignore"
    process = subprocess.Popen(
        command,
        env=env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    child_pid_path = paths["pid_dir"] / "child.pid"
    stdout, stderr = _communicate_launcher(
        process,
        paths=paths,
        expected_returncode=1,
        label="sigterm-ignoring launcher",
    )
    assert child_pid_path.exists(), (
        f"child.pid was not registered before launcher exit; stderr={stderr!r}"
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["stop_reason"] == "wall_clock_admission_bound_s"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] == "wall_clock_admission_bound_s"
    assert receipt["attempts"][0]["process_group_residual"] == 0
    assert receipt["possible_unobserved_overshoot"] is True
    child_pid = int(child_pid_path.read_text(encoding="ascii"))
    _assert_pid_gone(child_pid)
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def _uses_post_exit_child_pid_evidence(source: str) -> bool:
    launcher_exit = source.find("_communicate_launcher(")
    registration_check = source.find("assert child_pid_path.exists()")
    diagnostic = source.find("stderr={stderr!r}", registration_check)
    return (
        launcher_exit >= 0
        and registration_check > launcher_exit
        and diagnostic > registration_check
        and "deadline" not in source
        and "time.monotonic" not in source
    )


def test_sigterm_child_pid_registration_regression_detector() -> None:
    """Do not restore an absolute-time deadline for child.pid registration."""
    absolute_deadline_old_way = """
deadline = time.monotonic() + 2
while not child_pid_path.exists() and time.monotonic() < deadline:
    time.sleep(0.005)
child_pid_registered = child_pid_path.exists()
stdout, stderr = _communicate_launcher(process)
assert child_pid_registered, f"child.pid was not registered; stderr={stderr!r}"
"""
    post_exit_positive = """
stdout, stderr = _communicate_launcher(process)
assert child_pid_path.exists(), (
    f"child.pid was not registered before launcher exit; stderr={stderr!r}"
)
"""
    current = inspect.getsource(test_sigterm_ignoring_child_is_killed)

    assert not _uses_post_exit_child_pid_evidence(absolute_deadline_old_way)
    assert _uses_post_exit_child_pid_evidence(post_exit_positive)
    assert _uses_post_exit_child_pid_evidence(current)


def test_group_member_count_reports_identity_missing_source() -> None:
    reasons: list[str] = []

    assert (
        LAUNCHER._group_member_count(None, on_unknown=reasons.append) is None
    )
    assert reasons == ["pid_identity_unavailable"]


def test_group_member_count_reports_scandir_failure_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_scan(_path: str) -> Any:
        raise OSError("synthetic /proc failure")

    monkeypatch.setattr(LAUNCHER.os, "scandir", fail_scan)
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )
    reasons: list[str] = []
    assert (
        LAUNCHER._group_member_count(identity, on_unknown=reasons.append)
        is None
    )
    assert reasons == ["proc_scandir_oserror"]


def test_group_member_count_reports_stat_read_failure_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Entry:
        name = str(os.getpid())

    class Entries:
        def __enter__(self) -> list[Entry]:
            return [Entry()]

        def __exit__(self, *_args: Any) -> None:
            return None

        def __iter__(self) -> Any:
            return iter([Entry()])

    monkeypatch.setattr(LAUNCHER.os, "scandir", lambda _path: Entries())
    monkeypatch.setattr(
        LAUNCHER.Path,
        "read_text",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("synthetic")),
    )
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )

    reasons: list[str] = []
    assert (
        LAUNCHER._group_member_count(identity, on_unknown=reasons.append)
        is None
    )
    assert reasons == ["proc_stat_read_error"]


def test_group_member_count_reports_stat_parse_failure_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Entry:
        name = str(os.getpid())

    class Entries:
        def __enter__(self) -> list[Entry]:
            return [Entry()]

        def __exit__(self, *_args: Any) -> None:
            return None

        def __iter__(self) -> Any:
            return iter([Entry()])

    monkeypatch.setattr(LAUNCHER.os, "scandir", lambda _path: Entries())
    monkeypatch.setattr(
        LAUNCHER.Path,
        "read_text",
        lambda *_args, **_kwargs: "1 (fake) S 2 not-an-integer",
    )
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )
    reasons: list[str] = []
    attempt = LAUNCHER.AttemptDiagnosticsState(
        attempt_index=1, job_started_ns=0, attempt_started_ns=0
    )

    assert (
        LAUNCHER._group_member_count(
            identity,
            on_unknown=reasons.append,
            on_malformed=attempt.note_malformed,
        )
        is None
    )
    assert reasons == ["proc_stat_parse_error"]
    assert attempt.as_document()["residual_observation"][
        "proc_stat_malformed"
    ] is True


def test_group_member_count_records_malformed_without_changing_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Entry:
        name = str(os.getpid())

    class Entries:
        def __enter__(self) -> list[Entry]:
            return [Entry()]

        def __exit__(self, *_args: Any) -> None:
            return None

        def __iter__(self) -> Any:
            return iter([Entry()])

    attempt = LAUNCHER.AttemptDiagnosticsState(
        attempt_index=1, job_started_ns=0, attempt_started_ns=0
    )
    monkeypatch.setattr(LAUNCHER.os, "scandir", lambda _path: Entries())
    monkeypatch.setattr(
        LAUNCHER.Path,
        "read_text",
        lambda *_args, **_kwargs: "malformed stat",
    )
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )

    assert (
        LAUNCHER._group_member_count(
            identity, on_malformed=attempt.note_malformed
        )
        == 0
    )
    document = attempt.as_document()
    assert document["residual_observation"]["final_count"] is None
    assert document["residual_observation"]["proc_stat_malformed"] is True


def test_unknown_residual_source_propagates_without_verifying_normal_reap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        def wait(self) -> int:
            return 0

    monkeypatch.setattr(
        LAUNCHER, "_group_member_count", lambda _identity, **_kwargs: None
    )
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )

    residual, verified = LAUNCHER._normal_reap(Process(), identity)

    assert residual is None
    assert verified is False


def test_unknown_residual_source_propagates_through_terminate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        def poll(self) -> None:
            return None

        def kill(self) -> None:
            return None

        def wait(self, timeout: float | None = None) -> int:
            return 0

    clock = iter((0.0, 2.0))
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: next(clock))
    attempt = LAUNCHER.AttemptDiagnosticsState(
        attempt_index=1,
        job_started_ns=0,
        attempt_started_ns=0,
    )

    residual, verified = LAUNCHER._terminate(
        Process(),
        None,
        grace_s=0.05,
        on_unknown=attempt.note_unknown,
        on_malformed=attempt.note_malformed,
        on_signal=attempt.note_signal,
    )

    assert residual is None
    assert verified is False
    assert attempt.residual_final_unknown_source == "pid_identity_unavailable"
    assert [item["signal"] for item in attempt.termination_signals_sent] == [
        "SIGKILL"
    ]


def test_concurrent_termination_observers_keep_signal_attribution_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker_module = sys.modules["tools.dev_waves.worker"]
    original_worker_os = worker_module.os
    barrier = threading.Barrier(2)
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )
    observed: list[list[str]] = [[], []]
    results: list[bool | None] = [None, None]

    monkeypatch.setattr(
        LAUNCHER._worker_module,
        "_verified_group_exists",
        lambda _identity: True,
    )
    monkeypatch.setattr(
        LAUNCHER._worker_module, "_boottime_ns", lambda: 0
    )
    monkeypatch.setattr(
        LAUNCHER._worker_module, "_group_members", lambda _pgid: ()
    )

    def observe_killpg(_pgid: int, _signum: int) -> None:
        barrier.wait(timeout=2)

    monkeypatch.setattr(LAUNCHER.os, "killpg", observe_killpg)

    def run(index: int) -> None:
        results[index] = LAUNCHER._terminate_verified_group_observed(
            identity,
            0.05,
            lambda name, _now_ns: observed[index].append(name),
        )

    threads = [threading.Thread(target=run, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert not any(thread.is_alive() for thread in threads)
    assert results == [True, True]
    assert observed == [["SIGTERM"], ["SIGTERM"]]
    assert worker_module.os is original_worker_os


def _diagnostic_attempt_loop_args(tmp_path: Path, fake: Path) -> Any:
    command, _env, _paths = _base_command(
        tmp_path, fake=fake, max_wall="100"
    )
    args = LAUNCHER._parser().parse_args(command[2:])
    args.prompt_text = "fake prompt\n"
    args.launch_requirement = type(
        "Requirement",
        (),
        {"model": "gpt-5.6-sol", "effort": "high", "stage": "author", "lane": None},
    )()
    args.authority_snapshot = type(
        "Authority", (), {"authority_commit": _BASE_COMMIT, "digest": "synthetic"}
    )()
    args.artifact_dir.mkdir()
    return args


def test_forced_stop_without_signal_is_not_launcher_initiated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = tmp_path / "fake-codex"
    fake.write_bytes(b"fake")
    args = _diagnostic_attempt_loop_args(tmp_path, fake)
    diagnostics = LAUNCHER.LauncherDiagnosticsState(
        job_id="job-a", job_started_ns=0, receipt_path=args.receipt
    )

    class Process:
        pid = 12345
        returncode = 0

        def __init__(self) -> None:
            self.poll_count = 0

        def poll(self) -> int | None:
            self.poll_count += 1
            return None if self.poll_count == 1 else 0

        def wait(self, timeout: float | None = None) -> int:
            return 0

        def kill(self) -> None:
            pytest.fail("終了済み process へ signal を送ってはならない")

    clock_ns = 0

    def logical_clock() -> int:
        nonlocal clock_ns
        clock_ns += 1_000_000_000
        return clock_ns

    monkeypatch.setattr(LAUNCHER, "_monotonic_ns", logical_clock)
    monkeypatch.setattr(
        LAUNCHER, "_require_attempt_hook_installation", lambda *_args: None
    )
    monkeypatch.setattr(
        LAUNCHER.subprocess, "Popen", lambda *_args, **_kwargs: Process()
    )
    monkeypatch.setattr(LAUNCHER, "read_pid_identity", lambda _pid: None)
    monkeypatch.setattr(LAUNCHER, "_drain_stdout", lambda _state: None)
    monkeypatch.setattr(
        LAUNCHER, "_discover_rollouts", lambda _state, _root: None
    )
    monkeypatch.setattr(
        LAUNCHER, "_group_member_count", lambda _identity, **_kwargs: 0
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_seal_attempt",
        lambda *_args, **_kwargs: {"limit_trigger": None},
    )

    LAUNCHER._attempt_loop(
        args,
        attempt_index=1,
        job_started_ns=0,
        prior_actuals={"model_calls": 0, "cli_reported": 0},
        codex_path=fake,
        expected_binary_sha256=hashlib.sha256(b"fake").hexdigest(),
        diagnostics=diagnostics,
    )

    document = diagnostics.attempts[0].as_document()
    assert document["evidence_forced_stop"] is True
    assert document["termination_signals_sent"] == []
    assert document["termination_initiated_by_launcher"] is False


def test_evidence_deadline_origin_is_diagnostics_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = tmp_path / "fake-codex"
    fake.write_bytes(b"fake")
    args = _diagnostic_attempt_loop_args(tmp_path, fake)
    args.evidence_grace_s = Decimal("0.05")

    class Process:
        pid = 12345
        returncode: int | None = None

        def __init__(self) -> None:
            self.poll_count = 0

        def poll(self) -> int | None:
            self.poll_count += 1
            return self.returncode

    process = Process()
    clock_ns = 0
    polling = False
    spawn_sample_pending = False
    sealed_state: LAUNCHER.AttemptState | None = None

    def logical_clock() -> int:
        nonlocal clock_ns, polling, spawn_sample_pending
        if spawn_sample_pending:
            spawn_sample_pending = False
            polling = True
        elif polling:
            clock_ns += 10_000_000
        return clock_ns

    def delayed_preflight(*_args: Any) -> None:
        nonlocal clock_ns, polling, spawn_sample_pending
        polling = False
        spawn_sample_pending = False
        clock_ns += 100_000_000

    def delayed_read_pid_identity(_pid: int) -> None:
        nonlocal clock_ns, spawn_sample_pending
        clock_ns += 20_000_000
        spawn_sample_pending = True
        return None

    def terminate(
        selected_process: Process,
        _identity: None,
        **_kwargs: Any,
    ) -> tuple[int, bool]:
        selected_process.returncode = -signal.SIGKILL
        return 0, True

    def seal_attempt(
        state: LAUNCHER.AttemptState, *_args: Any, **_kwargs: Any
    ) -> dict[str, Any]:
        nonlocal sealed_state
        sealed_state = state
        return {"limit_trigger": None}

    monkeypatch.setattr(LAUNCHER, "_monotonic_ns", logical_clock)
    monkeypatch.setattr(
        LAUNCHER, "_require_attempt_hook_installation", delayed_preflight
    )
    monkeypatch.setattr(
        LAUNCHER.subprocess, "Popen", lambda *_args, **_kwargs: process
    )
    monkeypatch.setattr(
        LAUNCHER, "read_pid_identity", delayed_read_pid_identity
    )
    monkeypatch.setattr(LAUNCHER, "_drain_stdout", lambda _state: None)
    monkeypatch.setattr(
        LAUNCHER, "_discover_rollouts", lambda _state, _root: None
    )
    monkeypatch.setattr(LAUNCHER, "_terminate", terminate)
    monkeypatch.setattr(LAUNCHER, "_seal_attempt", seal_attempt)

    LAUNCHER._attempt_loop(
        args,
        attempt_index=1,
        job_started_ns=0,
        prior_actuals={"model_calls": 0, "cli_reported": 0},
        codex_path=fake,
        expected_binary_sha256=hashlib.sha256(b"fake").hexdigest(),
        diagnostics=None,
    )

    assert process.poll_count == 5
    assert sealed_state is not None
    assert sealed_state.evidence_forced_stop is True


def test_evidence_forced_stop_propagates_unknown_residual_to_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, evidence_grace="0.3"
    )
    env["FAKE_MODE"] = "no_rollout"
    monkeypatch.setattr(LAUNCHER, "read_pid_identity", lambda _pid: None)

    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    diagnostics = _read_launcher_diagnostics(paths)
    attempt = diagnostics["attempts"][0]

    assert receipt["attempts"][0]["session_ids"]
    assert attempt["evidence_forced_stop"] is True
    assert attempt["termination_initiated_by_launcher"] is True
    assert attempt["residual_observation"] == {
        "final_count": None,
        "final_unknown_source": "pid_identity_unavailable",
        "unknown_sources_seen": ["pid_identity_unavailable"],
        "proc_stat_malformed": False,
    }
    assert [item["signal"] for item in attempt["termination_signals_sent"]] == [
        "SIGKILL"
    ]


def test_launcher_diagnostics_phase_durations_use_distinct_boundaries() -> None:
    attempt = LAUNCHER.AttemptDiagnosticsState(
        attempt_index=1,
        job_started_ns=0,
        attempt_started_ns=1_000_000_000,
    )
    names = (
        "attempt_state_created",
        "attempt_preflight_completed",
        "spawn_completed",
        "supervision_drain_completed",
        "process_reap_completed",
        "final_drain_completed",
        "artifact_handles_closed",
        "attempt_wall_clock_sampled",
        "attempt_sealed",
    )
    for index, name in enumerate(names, 1):
        attempt.note_boundary(name, index * 1_000_000_000)

    document = attempt.as_document()

    assert document["attempt_elapsed_s_at"] == {
        name: index - 1 for index, name in enumerate(names, 1)
    }
    assert document["phase_duration_s"] == {
        "attempt_preflight": 1,
        "spawn": 1,
        "supervision_drain": 1,
        "process_reap": 1,
        "final_drain": 1,
        "artifact_handle_close": 1,
        "attempt_wall_clock_sample": 1,
        "attempt_seal": 1,
    }
    pending: list[Any] = [document]
    keys: set[str] = set()
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            keys.update(value)
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    assert "wall_clock_s" not in keys


def test_launcher_diagnostics_production_phase_wiring_has_exact_durations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = tmp_path / "fake-codex"
    fake.write_bytes(b"fake")
    args = _diagnostic_attempt_loop_args(tmp_path, fake)
    diagnostics = LAUNCHER.LauncherDiagnosticsState(
        job_id="job-a", job_started_ns=0, receipt_path=args.receipt
    )

    class Process:
        pid = 12345
        returncode = 0

        def poll(self) -> int:
            return 0

    clock_ns = 0

    def logical_clock() -> int:
        nonlocal clock_ns
        clock_ns += 1_000_000_000
        return clock_ns

    monkeypatch.setattr(LAUNCHER, "_monotonic_ns", logical_clock)
    monkeypatch.setattr(
        LAUNCHER, "_require_attempt_hook_installation", lambda *_args: None
    )
    monkeypatch.setattr(
        LAUNCHER.subprocess, "Popen", lambda *_args, **_kwargs: Process()
    )
    monkeypatch.setattr(LAUNCHER, "read_pid_identity", lambda _pid: None)
    monkeypatch.setattr(LAUNCHER, "_drain_stdout", lambda _state: None)
    monkeypatch.setattr(
        LAUNCHER, "_discover_rollouts", lambda _state, _root: None
    )
    monkeypatch.setattr(
        LAUNCHER, "_normal_reap", lambda *_args, **_kwargs: (0, True)
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_seal_attempt",
        lambda *_args, **_kwargs: {"limit_trigger": None},
    )

    LAUNCHER._attempt_loop(
        args,
        attempt_index=1,
        job_started_ns=0,
        prior_actuals={"model_calls": 0, "cli_reported": 0},
        codex_path=fake,
        expected_binary_sha256=hashlib.sha256(b"fake").hexdigest(),
        diagnostics=diagnostics,
    )

    assert diagnostics.attempts[0].as_document()["phase_duration_s"] == {
        "attempt_preflight": 1,
        "spawn": 1,
        "supervision_drain": 2,
        "process_reap": 1,
        "final_drain": 1,
        "artifact_handle_close": 1,
        "attempt_wall_clock_sample": 1,
        "attempt_seal": 2,
    }


def test_launcher_diagnostics_limit_conditions_negative_and_exact_boundary() -> None:
    limits = type(
        "Limits",
        (),
        {
            "wall_clock_admission_bound_s": 3,
            "max_model_calls": 5,
            "max_cli_reported_tokens": 7,
        },
    )()

    comparison, below = LAUNCHER._limit_conditions_met(
        site="running_poll",
        elapsed=2,
        model_calls=4,
        cli_reported=6,
        limits=limits,
    )
    exact_comparison, exact = LAUNCHER._limit_conditions_met(
        site="natural_exit",
        elapsed=3,
        model_calls=5,
        cli_reported=7,
        limits=limits,
    )

    assert comparison == ">="
    assert below == []
    assert exact_comparison == ">"
    assert exact == []


def test_launcher_diagnostics_records_all_conditions_and_site_values() -> None:
    limits = type(
        "Limits",
        (),
        {
            "wall_clock_admission_bound_s": 3,
            "max_model_calls": 5,
            "max_cli_reported_tokens": 7,
        },
    )()
    cases = {
        "running_poll": (3, 4, 6, ["wall_clock_admission_bound_s"]),
        "natural_exit": (2, 6, 6, ["max_model_calls"]),
        "attempt_seal": (2, 4, 8, ["max_cli_reported_tokens"]),
        "retry_admission": (
            3,
            5,
            7,
            list(LAUNCHER._LIMIT_REASONS),
        ),
    }

    observed = {
        site: LAUNCHER._limit_conditions_met(
            site=site,
            elapsed=elapsed,
            model_calls=model_calls,
            cli_reported=tokens,
            limits=limits,
        )[1]
        for site, (elapsed, model_calls, tokens, _expected) in cases.items()
    }

    assert observed == {
        site: expected for site, (*_values, expected) in cases.items()
    }


def test_launcher_diagnostics_keeps_control_trigger_separate_from_all_conditions() -> None:
    limits = type(
        "Limits",
        (),
        {
            "wall_clock_admission_bound_s": 3,
            "max_model_calls": 5,
            "max_cli_reported_tokens": 7,
        },
    )()
    attempt = LAUNCHER.AttemptDiagnosticsState(
        attempt_index=1, job_started_ns=0, attempt_started_ns=0
    )

    LAUNCHER._record_limit_conditions(
        attempt,
        site="running_poll",
        elapsed=3,
        model_calls=5,
        cli_reported=7,
        limits=limits,
    )
    attempt.control_limit_trigger = "wall_clock_admission_bound_s"
    document = attempt.as_document()

    assert document["control_limit_trigger"] == "wall_clock_admission_bound_s"
    assert document["limit_condition_snapshots"] == [
        {
            "site": "running_poll",
            "comparison": ">=",
            "conditions_met": list(LAUNCHER._LIMIT_REASONS),
            "elapsed_s": 3,
            "model_calls": 5,
            "cli_reported": 7,
            "wall_clock_admission_bound_s": 3,
            "max_model_calls": 5,
            "max_cli_reported_tokens": 7,
            "job_elapsed_s_at": 3,
        }
    ]


def test_transient_unknown_residual_requires_later_exact_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        def wait(self) -> int:
            return 0

    observations: Any = iter([None, 1, 0])
    monkeypatch.setattr(
        LAUNCHER,
        "_group_member_count",
        lambda _identity, **_kwargs: next(observations),
    )
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )

    residual, verified = LAUNCHER._normal_reap(Process(), identity)

    assert residual == 0
    assert verified is True


def test_cumulative_limits_do_not_reset_between_attempts(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        sandbox="read-only",
        max_attempts=2,
        max_calls=2,
        max_tokens=100000,
        max_wall="11",
    )
    env["FAKE_SEQUENCE"] = "retry_reject,retry_wait"
    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["stop_reason"] == "max_model_calls"
    assert receipt["actuals"]["attempt_count"] == 2
    assert receipt["actuals"]["model_calls"] == 2
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][1]["limit_trigger"] == "max_model_calls"
    assert receipt["attempts"][1]["accepted"] is False
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_retry_admission_exact_model_call_limit_is_not_accepted(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        sandbox="read-only",
        max_attempts=3,
        max_calls=1,
        max_tokens=100000,
        max_wall="11",
    )
    env["FAKE_MODE"] = "retry_reject"
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["outcome"] == "not_accepted"
    assert receipt["stop_reason"] == "max_model_calls"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["actuals"]["model_calls"] == 1
    assert receipt["attempts"][0]["limit_trigger"] == "max_model_calls"
    assert paths["counter"].read_text(encoding="ascii") == "1"


def test_max_attempts_never_spawns_extra_attempt(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        sandbox="read-only",
        max_attempts=2,
        max_calls=100,
        max_tokens=100000,
        max_wall="11",
    )
    env["FAKE_MODE"] = "retry_reject"
    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 2
    assert paths["counter"].read_text(encoding="ascii") == "2"
    assert len(_leader_pids(paths)) == 2
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_workspace_write_retry_is_refused(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "normal",
        expected_returncode=2,
        sandbox="workspace-write",
        max_attempts=2,
    )

    assert receipt is None
    assert "read-only" in completed.stderr
    assert not paths["pid_dir"].exists()


def test_launcher_process_wall_clock_includes_version_preflight(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        max_wall="0.1",
    )
    env["FAKE_VERSION_DELAY"] = "0.2"
    env["FAKE_MODE"] = "normal"

    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=2
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["outcome"] == "launcher_error"
    assert (
        receipt["wall_clock_scope"]
        == "launcher_start_to_receipt_fields_finalized"
    )
    assert receipt["actuals"]["wall_clock_s"] >= 0.2
    assert receipt["attempts"] == []
    assert not paths["pid_dir"].exists()


def test_seal_failure_still_writes_launcher_error_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"

    def fail_seal(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise LAUNCHER.LaunchError("synthetic seal failure")

    monkeypatch.setattr(LAUNCHER, "_seal_attempt", fail_seal)
    rc = _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=2
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert not paths["output"].exists()
    diagnostics = _read_launcher_diagnostics(paths)
    assert diagnostics["receipt_binding"]["status"] == "sealed"


def test_launcher_diagnostics_write_failure_does_not_change_control_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"
    receipt_bytes_before_failure: list[bytes] = []

    def fail_diagnostics(
        args: Any, _diagnostics: Any, **_kwargs: Any
    ) -> None:
        receipt_bytes_before_failure.append(args.receipt.read_bytes())
        raise OSError("synthetic diagnostics failure")

    monkeypatch.setattr(
        LAUNCHER, "_publish_launcher_diagnostics", fail_diagnostics
    )

    rc = _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=0
    )
    receipt_bytes = paths["receipt"].read_bytes()
    receipt = json.loads(receipt_bytes)

    assert rc == 0
    assert receipt["outcome"] == "accepted"
    assert receipt["attempts"][0]["accepted"] is True
    assert receipt_bytes_before_failure == [receipt_bytes]
    assert list(paths["artifact"].glob("launcher-diagnostics.*.json")) == []


def test_launcher_diagnostics_sidecar_write_does_not_fsync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    receipt = tmp_path / "receipt.json"
    receipt.write_bytes(b"{}\n")
    args = type("Args", (), {"artifact_dir": artifact})()
    diagnostics = LAUNCHER.LauncherDiagnosticsState(
        job_id="job-a", job_started_ns=0, receipt_path=receipt
    )
    monkeypatch.setattr(
        LAUNCHER.os,
        "fsync",
        lambda _fd: pytest.fail("diagnostics sidecar must not fsync"),
    )

    path = LAUNCHER._publish_launcher_diagnostics(
        args, diagnostics, receipt_attempts=[]
    )

    assert path.read_bytes().endswith(b"\n")


def test_launcher_diagnostics_sidecar_is_outside_receipt_schema(
    tmp_path: Path,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )

    assert receipt is not None
    assert _read_launcher_diagnostics(paths)["attempts"]
    assert LAUNCHER._check_receipt_paths(
        paths["receipt"], paths["manifest"], expectations={}, report=False
    ) == 0
    receipt["launcher_diagnostics"] = {"forbidden": True}
    with pytest.raises(LAUNCHER.LaunchError, match="field set"):
        LAUNCHER._validate_receipt(receipt)


def test_post_attempt_audit_failure_still_writes_launcher_error_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"

    def fail_audit(*_args: Any, **_kwargs: Any) -> Any:
        raise LAUNCHER.LaunchError("synthetic audit failure")

    monkeypatch.setattr(LAUNCHER, "_audit_receipt_value", fail_audit)
    rc = _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=2
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert not paths["output"].exists()


def test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    command.extend(("--finalization-admission-bound-s", "3"))
    env["FAKE_MODE"] = "normal"
    clock_offset_ns = 0
    original_stage = LAUNCHER._stage_receipt_write
    stage_calls = 0

    def logical_clock() -> int:
        return time.monotonic_ns() + clock_offset_ns

    def delayed_stage(path: Path, receipt: Any) -> Path:
        nonlocal clock_offset_ns, stage_calls
        temporary = original_stage(path, receipt)
        stage_calls += 1
        if stage_calls == 1:
            assert paths["output"].exists()
            clock_offset_ns += 4_000_000_000
        return temporary

    monkeypatch.setattr(LAUNCHER, "_monotonic_ns", logical_clock)
    monkeypatch.setattr(LAUNCHER, "_stage_receipt_write", delayed_stage)
    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert stage_calls == 2
    assert receipt["outcome"] == "not_accepted"
    assert receipt["stop_reason"] == "finalization_admission_bound_s"
    assert receipt["launcher_rc"] == 1
    assert receipt["attempts"][-1]["accepted"] is True
    assert receipt["attempts"][-1]["failure_class"] is None
    assert receipt["attempts"][-1]["limit_trigger"] is None
    assert (
        receipt["actuals"]["finalization_wall_clock_s"]
        >= receipt["limits"]["finalization_admission_bound_s"]
    )
    assert not paths["output"].exists()
    assert list(tmp_path.glob(".receipt.json.tmp.*")) == []
    diagnostics = _read_launcher_diagnostics(paths)
    assert (
        diagnostics["finalization_publication"]["gate_elapsed_s"] >= 3
    )


def test_receipt_audit_wall_overrun_flips_to_not_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    command.extend(("--finalization-admission-bound-s", "3"))
    env["FAKE_MODE"] = "normal"
    clock_offset_ns = 0
    original_audit = LAUNCHER._audit_receipt_value
    published_audits = 0

    def logical_clock() -> int:
        return time.monotonic_ns() + clock_offset_ns

    def delayed_audit(*args: Any, **kwargs: Any) -> Any:
        nonlocal clock_offset_ns, published_audits
        result = original_audit(*args, **kwargs)
        if kwargs.get("check_published_output") is True:
            published_audits += 1
            assert paths["output"].exists()
            clock_offset_ns += 4_000_000_000
        return result

    monkeypatch.setattr(LAUNCHER, "_monotonic_ns", logical_clock)
    monkeypatch.setattr(LAUNCHER, "_audit_receipt_value", delayed_audit)
    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=1
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert published_audits == 1
    assert receipt["outcome"] == "not_accepted"
    assert receipt["stop_reason"] == "finalization_admission_bound_s"
    assert receipt["launcher_rc"] == 1
    assert receipt["attempts"][-1]["accepted"] is True
    assert receipt["attempts"][-1]["failure_class"] is None
    assert receipt["attempts"][-1]["limit_trigger"] is None
    assert (
        receipt["actuals"]["finalization_wall_clock_s"]
        >= receipt["limits"]["finalization_admission_bound_s"]
    )
    assert not paths["output"].exists()
    diagnostics = _read_launcher_diagnostics(paths)
    assert (
        diagnostics["finalization_publication"]["gate_elapsed_s"] >= 3
    )


def test_accepted_publication_reuses_the_staged_receipt_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"
    original_write = LAUNCHER._write_json_temp
    receipt_temp_writes: list[tuple[Path, tuple[int, int]]] = []

    def recording_write(path: Path, value: object) -> Path:
        temporary = original_write(path, value)
        if path == paths["receipt"]:
            metadata = temporary.stat()
            receipt_temp_writes.append(
                (temporary, (metadata.st_dev, metadata.st_ino))
            )
        return temporary

    monkeypatch.setattr(LAUNCHER, "_write_json_temp", recording_write)
    _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=0
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["outcome"] == "accepted"
    assert len(receipt_temp_writes) == 1
    temporary, staged_inode = receipt_temp_writes[0]
    receipt_metadata = paths["receipt"].stat()
    assert (receipt_metadata.st_dev, receipt_metadata.st_ino) == staged_inode
    assert not temporary.exists()


def test_receipt_publication_failure_removes_output_and_writes_error_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"
    original_link = LAUNCHER.os.link
    receipt_link_calls = 0

    def fail_receipt_link_once(
        source: Path, destination: Path, *args: Any, **kwargs: Any
    ) -> None:
        nonlocal receipt_link_calls
        if destination == paths["receipt"]:
            receipt_link_calls += 1
            if receipt_link_calls == 1:
                raise OSError("synthetic publication failure")
        original_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(LAUNCHER.os, "link", fail_receipt_link_once)
    rc = _run_main_in_process(
        command, env, monkeypatch, paths=paths, expected_returncode=2
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt_link_calls == 2
    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert not paths["output"].exists()
    assert list(tmp_path.glob(".receipt.json.tmp.*")) == []


def test_help_does_not_claim_job_wide_hard_cap() -> None:
    completed = subprocess.run(
        [sys.executable, os.fspath(_LAUNCHER), "--help"],
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert completed.returncode == 0
    assert "hard cap" not in completed.stdout.lower()
    assert "launcher process" in completed.stdout


def test_parallel_jobs_preserve_both_manifest_entries(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    barrier = tmp_path / "barrier"
    first_command, first_env, first_paths = _base_command(
        tmp_path,
        fake=fake,
        job_id="job-a",
        suffix="-a",
    )
    second_command, second_env, second_paths = _base_command(
        tmp_path,
        fake=fake,
        job_id="job-b",
        suffix="-b",
    )
    for env in (first_env, second_env):
        env["FAKE_MODE"] = "normal"
        env["FAKE_BARRIER_DIR"] = os.fspath(barrier)
        env["FAKE_BARRIER_COUNT"] = "2"
    first = subprocess.Popen(
        first_command,
        env=first_env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    second = subprocess.Popen(
        second_command,
        env=second_env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    first_stdout, first_stderr = _communicate_launcher(
        first,
        paths=first_paths,
        expected_returncode=0,
        label="first launcher",
    )
    second_stdout, second_stderr = _communicate_launcher(
        second,
        paths=second_paths,
        expected_returncode=0,
        label="second launcher",
    )
    manifest = json.loads(
        first_paths["manifest"].read_text(encoding="utf-8")
    )
    assert [(item["job_id"], item["attempt_index"]) for item in manifest["sessions"]] == [
        ("job-a", 1),
        ("job-b", 1),
    ]
    assert first_paths["receipt"].exists()
    assert second_paths["receipt"].exists()


def test_manifest_v2_accepts_two_sibling_worktree_repo_roots(
    tmp_path: Path,
) -> None:
    repo_a, commit_a = _prepare_authority_repo(tmp_path / "repo-a")
    repo_b, commit_b = _prepare_authority_repo(tmp_path / "repo-b")
    fake = _write_fake_codex(tmp_path / "fake-codex")
    shared_manifest = tmp_path / "shared-manifest.json"
    commands: list[tuple[list[str], dict[str, str], dict[str, Path]]] = []
    for index, (repo, commit) in enumerate(
        ((repo_a, commit_a), (repo_b, commit_b)), 1
    ):
        job_root = tmp_path / f"job-{index}"
        job_root.mkdir()
        commands.append(
            _base_command(
                job_root,
                fake=fake,
                job_id=f"job-{index}",
                suffix=f"-{index}",
                repo_root=repo,
                base_commit=commit,
                manifest_path=shared_manifest,
            )
        )
    for command, env, paths in commands:
        _run_launcher_subprocess(
            command, env=env, paths=paths, expected_returncode=0
        )
    manifest = json.loads(shared_manifest.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert {entry["repo_root"] for entry in manifest["sessions"]} == {
        os.fspath(repo_a),
        os.fspath(repo_b),
    }


_MID_MERGE_CAPABILITY_CASES = tuple(
    (stage, sandbox, stage == "author" and sandbox == "workspace-write")
    for stage in LAUNCHER.STAGES
    for sandbox in ("read-only", "workspace-write")
)


@pytest.mark.parametrize(
    ("stage", "sandbox", "expected"), _MID_MERGE_CAPABILITY_CASES
)
def test_preflight_passes_mid_merge_capability_only_to_author_workspace_write(
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    sandbox: str,
    expected: bool,
) -> None:
    calls: list[tuple[Path, bool]] = []

    class SnapshotCaptured(Exception):
        pass

    def capture_snapshot(
        repo_root: Path, *, allow_mid_merge: bool = False
    ) -> None:
        calls.append((repo_root, allow_mid_merge))
        raise SnapshotCaptured

    monkeypatch.setattr(LAUNCHER, "snapshot_authority", capture_snapshot)
    args = LAUNCHER.argparse.Namespace(
        repo_root=_ROOT,
        stage=stage,
        sandbox=sandbox,
    )

    with pytest.raises(SnapshotCaptured):
        LAUNCHER._preflight_run(args)

    assert calls == [(_ROOT.resolve(), expected)]


def test_preflight_mid_merge_capability_case_registration_is_complete() -> None:
    assert _MID_MERGE_CAPABILITY_CASES == (
        ("plan", "read-only", False),
        ("plan", "workspace-write", False),
        ("consult", "read-only", False),
        ("consult", "workspace-write", False),
        ("author", "read-only", False),
        ("author", "workspace-write", True),
        ("review", "read-only", False),
        ("review", "workspace-write", False),
        ("fix", "read-only", False),
        ("fix", "workspace-write", False),
        ("focus", "read-only", False),
        ("focus", "workspace-write", False),
    )


def test_preflight_real_mid_merge_allows_only_author_workspace_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main, _base_commit = _prepare_authority_repo(tmp_path / "main-repo")
    branch = subprocess.run(
        ["git", "-C", os.fspath(main), "branch", "--show-current"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    operations = main / "docs/dev-wave/operations.md"
    workers = main / "docs/dev-wave/workers.md"
    base_operations = operations.read_text(encoding="utf-8")
    base_workers = workers.read_text(encoding="utf-8")
    subprocess.run(
        ["git", "-C", os.fspath(main), "checkout", "-qb", "incoming"],
        check=True,
    )
    operations.write_text(
        base_operations + "\nincoming authority note\n", encoding="utf-8"
    )
    subprocess.run(
        ["git", "-C", os.fspath(main), "add", "docs/dev-wave/operations.md"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(main), "commit", "-qm", "incoming authority"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(main), "checkout", "-q", branch],
        check=True,
    )
    workers.write_text(
        base_workers + "\nwave authority note\n", encoding="utf-8"
    )
    subprocess.run(
        ["git", "-C", os.fspath(main), "add", "docs/dev-wave/workers.md"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(main), "commit", "-qm", "wave authority"],
        check=True,
    )
    repo, head = _prepare_authority_worktree(
        main, tmp_path / "mid-merge-worktree"
    )
    try:
        subprocess.run(
            [
                "git",
                "-C",
                os.fspath(repo),
                "merge",
                "--no-commit",
                "--no-ff",
                "incoming",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        git_dir = Path(
            subprocess.run(
                [
                    "git",
                    "-C",
                    os.fspath(repo),
                    "rev-parse",
                    "--absolute-git-dir",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
        )
        assert (git_dir / "MERGE_HEAD").is_file()
        assert (repo / "docs/dev-wave/operations.md").read_bytes() != (
            subprocess.run(
                [
                    "git",
                    "-C",
                    os.fspath(repo),
                    "show",
                    f"{head}:docs/dev-wave/operations.md",
                ],
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
        )
        monkeypatch.setattr(LAUNCHER, "_ROOT", main)
        fake = _write_fake_codex(tmp_path / "fake-codex")

        author_job = tmp_path / "author-job"
        author_job.mkdir()
        author_command, _author_env, author_paths = _base_command(
            author_job,
            fake=fake,
            stage="author",
            sandbox="workspace-write",
            repo_root=repo,
            cwd=repo,
            base_commit=head,
        )
        author_args = LAUNCHER._parser().parse_args(author_command[2:])
        assert LAUNCHER._preflight_run(author_args)[-1] is None
        assert author_args.authority_snapshot == LAUNCHER.snapshot_authority(
            repo, commit=head
        )
        assert author_paths["artifact"].is_dir()

        review_job = tmp_path / "review-job"
        review_job.mkdir()
        review_command, _review_env, _review_paths = _base_command(
            review_job,
            fake=fake,
            stage="review",
            sandbox="workspace-write",
            repo_root=repo,
            cwd=repo,
            base_commit=head,
        )
        review_args = LAUNCHER._parser().parse_args(review_command[2:])
        with pytest.raises(LAUNCHER.AuthorityError, match="working tree"):
            LAUNCHER._preflight_run(review_args)
    finally:
        _remove_authority_worktree(main, repo)


def test_preflight_accepts_sibling_worktree_with_same_git_common_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main, _main_commit = _prepare_authority_repo(tmp_path / "main-repo")
    repo, commit = _prepare_authority_worktree(
        main, tmp_path / "sibling-worktree"
    )
    try:
        monkeypatch.setattr(LAUNCHER, "_ROOT", main)
        fake = _write_fake_codex(tmp_path / "fake-codex")
        job_root = tmp_path / "job"
        job_root.mkdir()
        command, env, paths = _base_command(
            job_root,
            fake=fake,
            repo_root=repo,
            base_commit=commit,
        )
        env["FAKE_MODE"] = "normal"
        _run_main_in_process(
            command,
            env,
            monkeypatch,
            paths=paths,
            expected_returncode=0,
        )
        assert paths["receipt"].exists()
    finally:
        _remove_authority_worktree(main, repo)


def test_manifest_v1_cannot_receive_new_stage_bound_session(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    legacy = {
        "schema_version": 1,
        "wave_id": "wave-a",
        "repo_root": os.fspath(_ROOT),
        "base_commit": _BASE_COMMIT,
        "sessions": [
            {
                "job_id": "legacy-job",
                "attempt_index": 1,
                "session_id": "00000000-0000-0000-0000-000000000001",
            }
        ],
    }
    paths["manifest"].write_text(
        json.dumps(legacy, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    before = paths["manifest"].read_bytes()
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=2
    )
    assert paths["manifest"].read_bytes() == before
    assert not paths["receipt"].exists()
    assert not paths["pid_dir"].exists()


def test_manifest_lock_covers_load_replace_critical_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The contender fd must conflict before the critical-order guard proceeds."""
    manifest_path = tmp_path / "manifest.json"
    first_inside = threading.Event()
    release_first = threading.Event()
    second_lock_conflict_observed = threading.Event()
    second_inside = threading.Event()
    second_done = threading.Event()
    errors: list[BaseException] = []
    second_thread_ids: set[int] = set()
    causal_trace: list[str] = []
    coordination: queue.SimpleQueue[str] = queue.SimpleQueue()
    original_flock = LAUNCHER.fcntl.flock

    def observe_flock(fd: int, operation: int) -> None:
        if (
            threading.get_ident() in second_thread_ids
            and operation == LAUNCHER.fcntl.LOCK_EX
        ):
            try:
                original_flock(fd, operation | LAUNCHER.fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                original_flock(fd, LAUNCHER.fcntl.LOCK_UN)
                raise AssertionError(
                    "job-b manifest contender fd did not conflict with job-a"
                )
            causal_trace.append("second-lock-attempt")
            second_lock_conflict_observed.set()
            coordination.put("second-lock-attempt")
        original_flock(fd, operation)

    def wait_for_coordination(reason: str) -> str:
        # Two seconds matches the existing wait/join watchdogs and only bounds
        # failure recovery; it is not a scheduling expectation.
        try:
            return coordination.get(timeout=2)
        except queue.Empty:
            pytest.fail(f"timed out waiting for {reason}", pytrace=False)

    def first_hook() -> None:
        causal_trace.append("first-critical-enter")
        first_inside.set()
        assert release_first.wait(2), (
            "job-a timed out waiting for the manifest conflict probe to finish"
        )
        causal_trace.append("first-critical-exit")

    def second_hook() -> None:
        causal_trace.append("second-critical-enter")
        second_inside.set()
        coordination.put("second-critical-enter")

    def append(job_id: str, session_id: str, hook: Any = None) -> None:
        if job_id == "job-b":
            second_thread_ids.add(threading.get_ident())
        try:
            snapshot = LAUNCHER.snapshot_authority(_ROOT)
            LAUNCHER._append_manifest(
                manifest_path,
                wave_id="wave-a",
                entry={
                    "job_id": job_id,
                    "attempt_index": 1,
                    "session_id": session_id,
                    "stage": "author",
                    "lane": None,
                    "repo_root": os.fspath(_ROOT),
                    "base_commit": _BASE_COMMIT,
                    "requested_cwd": os.fspath(_ROOT),
                    "recorded_cwd": os.fspath(_ROOT),
                    "sessions_root": os.fspath(tmp_path / "sessions"),
                    "receipt_path": os.fspath(tmp_path / f"{job_id}.json"),
                    "authority_commit": snapshot.authority_commit,
                    "authority_digest": snapshot.digest,
                },
                critical_section_hook=hook,
            )
        except BaseException as exc:
            errors.append(exc)
        finally:
            if job_id == "job-b":
                second_done.set()
                coordination.put("second-done")

    first = threading.Thread(
        target=append,
        args=("job-a", "aaaaaaaa-0000-4000-8000-000000000001", first_hook),
    )
    second = threading.Thread(
        target=append,
        args=(
            "job-b",
            "bbbbbbbb-0000-4000-8000-000000000002",
            second_hook,
        ),
    )
    monkeypatch.setattr(LAUNCHER.fcntl, "flock", observe_flock)
    first.start()
    assert first_inside.wait(2), "job-a did not enter the manifest critical section"
    second.start()
    assert wait_for_coordination(
        "job-b manifest fd to observe a real lock conflict"
    ) == "second-lock-attempt"
    assert second_lock_conflict_observed.is_set()
    probe_fd = os.open(
        manifest_path.with_name(manifest_path.name + ".lock"),
        os.O_RDWR | os.O_CREAT,
        0o600,
    )
    try:
        with pytest.raises(BlockingIOError):
            fcntl.flock(probe_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(probe_fd)
    assert causal_trace == ["first-critical-enter", "second-lock-attempt"]
    assert not second_inside.is_set()
    assert not second_done.is_set()
    release_first.set()
    first.join(2)
    second.join(2)

    assert not first.is_alive(), "job-a did not leave the manifest critical section"
    assert not second.is_alive(), "job-b did not finish after the manifest lock release"
    assert errors == []
    assert causal_trace == [
        "first-critical-enter",
        "second-lock-attempt",
        "first-critical-exit",
        "second-critical-enter",
    ]
    assert second_inside.is_set()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["job_id"] for item in manifest["sessions"]] == [
        "job-a",
        "job-b",
    ]


def test_complete_receipt_publication_is_atomic_create_only_at_run_callsite(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    barrier = tmp_path / "receipt-race"
    first_command, first_env, first_paths = _base_command(
        tmp_path, fake=fake, job_id="job-a", suffix="-a"
    )
    second_command, second_env, second_paths = _base_command(
        tmp_path, fake=fake, job_id="job-b", suffix="-b"
    )
    receipt_index = second_command.index("--receipt") + 1
    second_command[receipt_index] = os.fspath(first_paths["receipt"])
    second_paths["receipt"] = first_paths["receipt"]
    for env in (first_env, second_env):
        env["FAKE_MODE"] = "normal"
        env["FAKE_BARRIER_DIR"] = os.fspath(barrier)
        env["FAKE_BARRIER_COUNT"] = "2"
    first = subprocess.Popen(
        first_command,
        env=first_env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    second = subprocess.Popen(
        second_command,
        env=second_env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    first_output = _communicate_unordered_launcher(
        first,
        paths=first_paths,
        expected_returncodes=[0, 2],
        label="first launcher",
    )
    second_output = _communicate_unordered_launcher(
        second,
        paths=second_paths,
        expected_returncodes=[0, 2],
        label="second launcher",
    )

    _assert_unordered_launcher_returncodes(
        [
            ("first launcher", first, first_output, first_paths),
            ("second launcher", second, second_output, second_paths),
        ],
        [0, 2],
    )
    receipt = json.loads(
        first_paths["receipt"].read_text(encoding="utf-8")
    )
    assert receipt["job_id"] in {"job-a", "job-b"}
    assert receipt["outcome"] == "accepted"
    winner_paths = (
        first_paths if receipt["job_id"] == "job-a" else second_paths
    )
    loser_paths = (
        second_paths if receipt["job_id"] == "job-a" else first_paths
    )
    assert winner_paths["output"].exists()
    assert not loser_paths["output"].exists()
    manifest = json.loads(
        first_paths["manifest"].read_text(encoding="utf-8")
    )
    # manifest は receipt の勝敗でなく、実際に費消した両 session を保持する。
    assert {item["job_id"] for item in manifest["sessions"]} == {
        "job-a",
        "job-b",
    }
    first_diagnostics = _read_launcher_diagnostics(first_paths)
    second_diagnostics = _read_launcher_diagnostics(second_paths)
    by_status = {
        item["receipt_binding"]["status"]: item
        for item in (first_diagnostics, second_diagnostics)
    }
    assert set(by_status) == {"sealed", "foreign"}
    assert by_status["sealed"]["job_id"] == receipt["job_id"]
    assert by_status["foreign"]["job_id"] != receipt["job_id"]
    expected_hash = hashlib.sha256(
        first_paths["receipt"].read_bytes()
    ).hexdigest()
    assert by_status["sealed"]["receipt_binding"]["sha256"] == expected_hash
    assert by_status["foreign"]["receipt_binding"]["sha256"] == expected_hash


def test_partial_receipt_never_visible_at_final_path(tmp_path: Path) -> None:
    final = tmp_path / "receipt.json"

    def crash(_temporary: Path) -> None:
        raise RuntimeError("synthetic crash before replace")

    with pytest.raises(RuntimeError, match="synthetic crash"):
        LAUNCHER._atomic_replace_json(
            final,
            {"schema_version": 1, "payload": "x" * 10000},
            before_replace=crash,
        )

    assert not final.exists()
    assert list(tmp_path.glob(".receipt.json.tmp.*")) == []


def test_check_receipt_detects_output_tampering(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None

    paths["output"].write_text("tampered", encoding="utf-8")
    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2


def test_check_receipt_reconstructs_authority_from_recorded_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main, _main_commit = _prepare_authority_repo(tmp_path / "main-repo")
    repo, commit = _prepare_authority_worktree(
        main, tmp_path / "authority-worktree"
    )
    try:
        monkeypatch.setattr(LAUNCHER, "_ROOT", main)
        fake = _write_fake_codex(tmp_path / "fake-codex")
        job_root = tmp_path / "job"
        job_root.mkdir()
        command, env, paths = _base_command(
            job_root,
            fake=fake,
            repo_root=repo,
            base_commit=commit,
        )
        _run_main_in_process(
            command,
            env,
            monkeypatch,
            paths=paths,
            expected_returncode=0,
        )
        operations = repo / "docs/dev-wave/operations.md"
        text = operations.read_text(encoding="utf-8")
        line = next(item for item in text.splitlines() if "`<model>`:" in item)
        recorded_authority = LAUNCHER.snapshot_authority(repo, commit=commit)
        models = tuple(dict.fromkeys(re.findall(r"gpt-[A-Za-z0-9._-]+", line)))
        replacement_models = tuple(
            f"gpt-5.6-authority-alt-{index}" for index in range(len(models))
        )
        replacement_by_model = dict(zip(models, replacement_models))
        assert set(models).isdisjoint(replacement_models)
        changed_line = re.sub(
            r"gpt-[A-Za-z0-9._-]+",
            lambda match: replacement_by_model[match.group(0)],
            line,
        )
        assert changed_line != line
        operations.write_text(
            text.replace(line, changed_line, 1), encoding="utf-8"
        )
        subprocess.run(
            ["git", "-C", os.fspath(repo), "add", "docs/dev-wave/operations.md"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", os.fspath(repo), "commit", "-qm", "new authority"],
            check=True,
        )
        changed_commit = subprocess.run(
            ["git", "-C", os.fspath(repo), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        changed_authority = LAUNCHER.snapshot_authority(
            repo, commit=changed_commit
        )
        assert (
            changed_authority.model_authority_version
            == recorded_authority.model_authority_version
        )
        checked = subprocess.run(
            _check_command(paths), text=True, capture_output=True, timeout=10
        )
        assert checked.returncode == 0, checked.stderr
    finally:
        _remove_authority_worktree(main, repo)


def test_docs_authority_alone_rejects_consistent_effort_mutation(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path, fake=fake, stage="review"
    )
    _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=0
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    derived = LAUNCHER.derive_launch(
        LAUNCHER.snapshot_authority(_ROOT), stage="review", lane=None
    )
    alternative = next(
        value
        for value in LAUNCHER.CODEX_REASONING_EFFORTS
        if value != derived.effort
    )
    rollout_record = receipt["attempts"][0]["rollouts"][0]
    rollout_path = Path(rollout_record["path"])
    events = [
        json.loads(line)
        for line in rollout_path.read_text(encoding="utf-8").splitlines()
    ]
    for event in events:
        if event.get("type") == "turn_context":
            event["payload"]["effort"] = alternative
    raw = (
        "\n".join(json.dumps(event, separators=(",", ":")) for event in events)
        + "\n"
    ).encode("utf-8")
    rollout_path.write_bytes(raw)
    rollout_record["sha256"] = hashlib.sha256(raw).hexdigest()
    rollout_record["bytes"] = len(raw)
    receipt["requested_effort"] = alternative
    receipt["recorded_effort"] = alternative
    assert receipt["attempts"][0]["evidence_status"] == "complete"
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 2
    assert "docs authority" in checked.stderr


def test_check_receipt_marks_self_asserted_limits_and_accepts_external_expectations(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None

    self_checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert self_checked.returncode == 0, self_checked.stderr
    summary = json.loads(self_checked.stdout)
    assert summary["limits_self_asserted"] == [
        "preparation_admission_bound_s",
        "wall_clock_admission_bound_s",
        "finalization_admission_bound_s",
        "max_model_calls",
        "max_cli_reported_tokens",
        "max_attempts",
    ]
    exact = subprocess.run(
        _check_command(paths)
        + [
            "--expect-prompt-sha256",
            receipt["prompt_sha256"],
            "--expect-preparation-admission-bound-s",
            str(receipt["limits"]["preparation_admission_bound_s"]),
            "--expect-wall-clock-admission-bound-s",
            "3",
            "--expect-finalization-admission-bound-s",
            str(receipt["limits"]["finalization_admission_bound_s"]),
            "--expect-max-model-calls",
            "100",
            "--expect-max-cli-reported-tokens",
            "100000",
            "--expect-max-attempts",
            "1",
        ],
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert exact.returncode == 0, exact.stderr
    assert json.loads(exact.stdout)["limits_self_asserted"] == []


@pytest.mark.parametrize("legacy_field_set", [True, False])
def test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics(
    tmp_path: Path,
    legacy_field_set: bool,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0, max_wall="100"
    )
    assert receipt is not None
    # 互換テストの admission 上限は判定の律速にせず、全 node 共通の
    # launcher subprocess watchdog だけを律速にする。
    assert receipt["limits"]["wall_clock_admission_bound_s"] > 10
    receipt = _write_legacy_v2_evidence(receipt, paths)
    receipt["limits"].pop("preparation_admission_bound_s")
    receipt["limits"].pop("finalization_admission_bound_s")
    receipt["actuals"].pop("preparation_wall_clock_s")
    receipt["actuals"].pop("finalization_wall_clock_s")
    receipt["schema_version"] = 1
    if legacy_field_set:
        for field_name in (
            "limits_assertion",
            "wall_clock_scope",
            "manifest_repo_root",
            "manifest_base_commit",
        ):
            receipt.pop(field_name)
    else:
        receipt["wall_clock_scope"] = "launcher_process"
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 0, checked.stderr
    diagnostics = json.loads(checked.stdout)
    assert diagnostics["schema_version"] == 1
    assert len(diagnostics["compatibility_skips"]) == (
        4 if legacy_field_set else 0
    )
    if legacy_field_set:
        assert all(
            item.startswith("v1_missing_")
            and item.endswith("_check_skipped")
            for item in diagnostics["compatibility_skips"]
        )


@pytest.mark.parametrize(
    "include_failure_class",
    [False, True],
    ids=("main-parent", "wave-parent"),
)
def test_check_receipt_reads_v2_parent_attempt_field_sets_without_upgrade(
    tmp_path: Path, include_failure_class: bool,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0, max_wall="100"
    )
    assert receipt is not None
    # 互換テストの admission 上限は判定の律速にせず、全 node 共通の
    # launcher subprocess watchdog だけを律速にする。
    assert receipt["limits"]["wall_clock_admission_bound_s"] > 10
    receipt_v2 = _write_legacy_v2_evidence(
        receipt,
        paths,
        include_failure_class=include_failure_class,
    )
    receipt_v2["limits"].pop("preparation_admission_bound_s")
    receipt_v2["limits"].pop("finalization_admission_bound_s")
    receipt_v2["actuals"].pop("preparation_wall_clock_s")
    receipt_v2["actuals"].pop("finalization_wall_clock_s")
    paths["receipt"].write_text(
        json.dumps(receipt_v2, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    before = paths["receipt"].read_bytes()

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["schema_version"] == 2
    assert paths["receipt"].read_bytes() == before


@pytest.mark.parametrize(
    ("wall_clock_s", "expected_returncode"),
    ((100, 0), (100.001, 2)),
    ids=("at-bound", "over-bound"),
)
def test_check_receipt_enforces_v2_wall_clock_admission_boundary(
    tmp_path: Path,
    wall_clock_s: float,
    expected_returncode: int,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0, max_wall="100"
    )
    assert receipt is not None
    receipt_v2 = _write_legacy_v2_evidence(receipt, paths)
    receipt_v2["limits"].pop("preparation_admission_bound_s")
    receipt_v2["limits"].pop("finalization_admission_bound_s")
    receipt_v2["actuals"].pop("preparation_wall_clock_s")
    receipt_v2["actuals"].pop("finalization_wall_clock_s")
    assert receipt_v2["limits"]["wall_clock_admission_bound_s"] == 100
    assert Decimal(str(wall_clock_s)) >= sum(
        (
            Decimal(str(attempt["wall_clock_s"]))
            for attempt in receipt_v2["attempts"]
        ),
        Decimal(0),
    )
    receipt_v2["actuals"]["wall_clock_s"] = wall_clock_s
    paths["receipt"].write_text(
        json.dumps(receipt_v2, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == expected_returncode, checked.stderr
    if expected_returncode == 0:
        assert json.loads(checked.stdout)["schema_version"] == 2
    else:
        assert checked.stdout == ""
        assert "NG: receipt truth table が不正" in checked.stderr


@pytest.mark.parametrize(
    "include_failure_class",
    [False, True],
    ids=("main-parent", "wave-parent"),
)
def test_check_receipt_reads_v3_parent_attempt_field_sets_without_upgrade(
    tmp_path: Path, include_failure_class: bool,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0, max_wall="100"
    )
    assert receipt is not None
    # 互換テストの admission 上限は判定の律速にせず、全 node 共通の
    # launcher subprocess watchdog だけを律速にする。
    assert receipt["limits"]["wall_clock_admission_bound_s"] > 10
    receipt["schema_version"] = 3
    receipt["recorded_values_semantics"] = LAUNCHER._RECORDED_VALUES_SEMANTICS
    receipt["limits"].pop("preparation_admission_bound_s")
    receipt["limits"].pop("finalization_admission_bound_s")
    receipt["actuals"].pop("preparation_wall_clock_s")
    receipt["actuals"].pop("finalization_wall_clock_s")
    for attempt in receipt["attempts"]:
        attempt.pop("evidence_issues")
    if not include_failure_class:
        for attempt in receipt["attempts"]:
            attempt.pop("failure_class")
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    before = paths["receipt"].read_bytes()

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["schema_version"] == 3
    assert paths["receipt"].read_bytes() == before


def test_check_receipt_reads_v4_without_evidence_issues(tmp_path: Path) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    receipt["schema_version"] = 4
    receipt["recorded_values_semantics"] = LAUNCHER._RECORDED_VALUES_SEMANTICS
    for attempt in receipt["attempts"]:
        attempt.pop("evidence_issues")
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    before = paths["receipt"].read_bytes()

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["schema_version"] == 4
    assert paths["receipt"].read_bytes() == before


def test_recompute_attempt_missing_precedes_fatal_stdout_issue_for_all_schemas(
    tmp_path: Path,
) -> None:
    stdout_path = tmp_path / "stdout.jsonl"
    stderr_path = tmp_path / "stderr.txt"
    output_path = tmp_path / "output.md"
    stdout_path.write_bytes(b"not-json\n")
    stderr_path.write_bytes(b"")
    output_path.write_bytes(b"")
    attempt = {
        "attempt_index": 1,
        "stdout_path": os.fspath(stdout_path),
        "stderr_path": os.fspath(stderr_path),
        "output_path": os.fspath(output_path),
        "session_ids": [],
        "rollouts": [],
    }

    for schema_version in (4, 5):
        evidence, _metering, issues, _actuals, _recorded_cwds = (
            LAUNCHER._recompute_attempt_metering(
                attempt,
                schema_version=schema_version,
                model="test-model",
                reasoning="high",
                cwd=os.fspath(tmp_path),
            )
        )

        assert issues[0]["reason"] == "event_invalid"
        assert evidence == "missing"


def test_check_receipt_external_limit_detects_self_asserted_limit_tampering(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    receipt["limits"]["max_model_calls"] = 101
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    without_external = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    with_external = subprocess.run(
        _check_command(paths) + ["--expect-max-model-calls", "100"],
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert without_external.returncode == 0, without_external.stderr
    assert "max_model_calls" in json.loads(
        without_external.stdout
    )["limits_self_asserted"]
    assert with_external.returncode == 2


def test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    receipt["attempts"][0]["model_calls"] = 0
    receipt["actuals"]["model_calls"] = 0
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2
    assert "sealed artifact" in checked.stderr or "再計算" in checked.stderr


def test_check_receipt_recomputes_attempt_output_hash(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    Path(receipt["attempts"][0]["output_path"]).write_text(
        "tampered attempt output", encoding="utf-8"
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2


def test_manifest_refuses_foreign_wave_id(tmp_path: Path) -> None:
    first, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    fake = tmp_path / "fake-codex"
    command, env, second_paths = _base_command(
        tmp_path,
        fake=fake,
        job_id="job-foreign",
        wave_id="wave-foreign",
        suffix="-foreign",
    )
    env["FAKE_MODE"] = "normal"
    second = _run_launcher_subprocess(
        command, env=env, paths=second_paths, expected_returncode=2
    )

    assert "wave_id" in second.stderr
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["wave_id"] == "wave-a"
    assert len(manifest["sessions"]) == 1
    assert not second_paths["receipt"].exists()
    assert not second_paths["pid_dir"].exists()


def test_preflight_rejects_cwd_outside_repo_and_unknown_base(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    outside_command, outside_env, outside_paths = _base_command(
        tmp_path, fake=fake, suffix="-outside"
    )
    outside_command[outside_command.index("--cwd") + 1] = os.fspath(tmp_path)
    outside_env["FAKE_MODE"] = "normal"
    outside = _run_launcher_subprocess(
        outside_command,
        env=outside_env,
        paths=outside_paths,
        expected_returncode=2,
    )

    unknown_command, unknown_env, unknown_paths = _base_command(
        tmp_path, fake=fake, suffix="-unknown"
    )
    unknown_command[unknown_command.index("--base-commit") + 1] = "f" * 40
    unknown_env["FAKE_MODE"] = "normal"
    unknown = _run_launcher_subprocess(
        unknown_command,
        env=unknown_env,
        paths=unknown_paths,
        expected_returncode=2,
    )

    assert "--cwd" in outside.stderr
    assert not outside_paths["receipt"].exists()
    assert "--base-commit" in unknown.stderr
    assert not unknown_paths["receipt"].exists()


def test_preflight_rejects_foreign_repo_before_artifact_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    launcher_repo, _launcher_commit = _prepare_authority_repo(
        tmp_path / "launcher-repo"
    )
    repo, _commit = _prepare_authority_repo(tmp_path / "outer-repo")
    foreign_repo, _foreign_commit = _prepare_authority_repo(
        tmp_path / "foreign-repo"
    )
    nested_submodule = repo / "nested-submodule"
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "-C",
            os.fspath(repo),
            "submodule",
            "add",
            "-q",
            os.fspath(foreign_repo),
            os.fspath(nested_submodule),
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(repo), "commit", "-qam", "add submodule"],
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", os.fspath(repo), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    monkeypatch.setattr(LAUNCHER, "_ROOT", launcher_repo)
    fake = _write_fake_codex(tmp_path / "fake-codex")
    job_root = tmp_path / "job"
    job_root.mkdir()
    command, env, paths = _base_command(
        job_root,
        fake=fake,
        repo_root=repo,
        base_commit=commit,
        cwd=nested_submodule,
    )

    _run_main_in_process(
        command,
        env,
        monkeypatch,
        paths=paths,
        expected_returncode=2,
    )

    captured = capsys.readouterr()
    assert "git common-dir" in captured.err
    assert not paths["artifact"].exists()
    assert not paths["receipt"].exists()
    assert not paths["manifest"].exists()


def test_preflight_rejects_nested_foreign_repo_as_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main, _main_commit = _prepare_authority_repo(tmp_path / "main-repo")
    repo, commit = _prepare_authority_worktree(
        main, tmp_path / "outer-worktree"
    )
    try:
        monkeypatch.setattr(LAUNCHER, "_ROOT", main)
        nested = repo / "nested-repo"
        nested.mkdir()
        subprocess.run(
            ["git", "-C", os.fspath(nested), "init", "-q"], check=True
        )
        fake = _write_fake_codex(tmp_path / "fake-codex")
        job_root = tmp_path / "job"
        job_root.mkdir()
        command, env, paths = _base_command(
            job_root,
            fake=fake,
            repo_root=repo,
            base_commit=commit,
            cwd=nested,
        )

        _run_main_in_process(
            command,
            env,
            monkeypatch,
            paths=paths,
            expected_returncode=2,
        )

        captured = capsys.readouterr()
        assert "git common-dir" in captured.err
        assert not paths["artifact"].exists()
        assert not paths["receipt"].exists()
        assert not paths["manifest"].exists()
    finally:
        _remove_authority_worktree(main, repo)


@pytest.mark.parametrize("field", ["wave_id", "repo_root", "base_commit"])
def test_check_receipt_rechecks_all_manifest_header_fields(
    tmp_path: Path,
    field: str,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0, max_wall="11"
    )
    assert receipt is not None
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    replacements = {
        "wave_id": "wave-tampered",
        "repo_root": "/tmp",
        "base_commit": "f" * 40,
    }
    if field == "wave_id":
        manifest[field] = replacements[field]
    else:
        manifest["sessions"][0][field] = replacements[field]
    paths["manifest"].write_text(
        json.dumps(manifest, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2


def test_append_manifest_header_gate_fails_without_checker_mask(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    snapshot = LAUNCHER.snapshot_authority(_ROOT)

    def entry(job_id: str, session_id: str) -> dict[str, Any]:
        return {
            "job_id": job_id,
            "attempt_index": 1,
            "session_id": session_id,
            "stage": "author",
            "lane": None,
            "repo_root": os.fspath(_ROOT),
            "base_commit": _BASE_COMMIT,
            "requested_cwd": os.fspath(_ROOT),
            "recorded_cwd": os.fspath(_ROOT),
            "sessions_root": os.fspath(tmp_path / "sessions"),
            "receipt_path": os.fspath(tmp_path / f"{job_id}.json"),
            "authority_commit": snapshot.authority_commit,
            "authority_digest": snapshot.digest,
        }

    LAUNCHER._append_manifest(
        manifest_path,
        wave_id="wave-a",
        entry=entry(
            "job-a", "aaaaaaaa-0000-4000-8000-000000000001"
        ),
    )

    with pytest.raises(LAUNCHER.LaunchError, match="wave_id"):
        LAUNCHER._append_manifest(
            manifest_path,
            wave_id="wave-b",
            entry=entry(
                "job-b", "bbbbbbbb-0000-4000-8000-000000000002"
            ),
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["job_id"] for item in manifest["sessions"]] == ["job-a"]


def test_inconsistent_metering_is_not_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "inconsistent", expected_returncode=1
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["metering_status"] == "inconsistent"
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_cli_reported_running_max_latches_usage_rollback(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "rollback",
        expected_returncode=1,
        max_calls=100,
        max_tokens=100,
        max_wall="11",
    )

    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["cli_reported"] == 1000
    assert attempt["limit_trigger"] == "max_cli_reported_tokens"
    assert attempt["metering_status"] == "inconsistent"
    assert attempt["accepted"] is False


def test_usage_rollback_alone_is_rejected_without_peak_or_terminal_mask(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "rollback_equal_cli",
        expected_returncode=1,
        max_calls=100,
        max_tokens=100000,
        max_wall="11",
    )

    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["cli_reported"] == 100
    assert attempt["limit_trigger"] is None
    assert attempt["metering_status"] == "inconsistent"
    assert attempt["accepted"] is False
    assert receipt["stop_reason"] == "max_attempts"


def test_null_token_count_is_observed_and_makes_metering_incomplete(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "null_info",
        expected_returncode=1,
        max_calls=100,
        max_tokens=100000,
        max_wall="11",
    )

    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["model_calls"] == 2
    assert attempt["metering_status"] == "incomplete"
    assert attempt["limit_trigger"] is None
    assert attempt["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True


def test_delayed_thread_and_rollout_are_read_from_byte_zero(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "delayed_thread", expected_returncode=0, max_wall="8"
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "completed"
    assert receipt["actuals"]["model_calls"] == 1
    assert receipt["attempts"][0]["evidence_status"] == "complete"


def test_manifest_is_appended_while_correlated_session_is_running(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake, max_wall="8")
    env["FAKE_MODE"] = "manifest_while_running"
    process = subprocess.Popen(
        command,
        env=env,
        text=True,
        errors="backslashreplace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + 3
    manifest: dict[str, Any] | None = None
    launcher_output: tuple[str, str] | None = None
    while time.monotonic() < deadline:
        if paths["manifest"].exists():
            manifest = json.loads(
                paths["manifest"].read_text(encoding="utf-8")
            )
            if manifest["sessions"]:
                break
        if process.poll() is not None:
            launcher_output = _communicate_launcher(
                process,
                paths=paths,
                expected_returncode=0,
                label="correlated-session launcher",
            )
            break
        time.sleep(0.01)

    if (
        (manifest is None or not manifest["sessions"])
        and process.poll() is not None
        and launcher_output is None
    ):
        launcher_output = _communicate_launcher(
            process,
            paths=paths,
            expected_returncode=0,
            label="correlated-session launcher",
        )
    if (
        (manifest is None or not manifest["sessions"])
        and launcher_output is not None
        and paths["manifest"].exists()
    ):
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert manifest is not None and len(manifest["sessions"]) == 1
    leader_pid = int(
        next(paths["pid_dir"].glob("leader-*.pid")).read_text(
            encoding="ascii"
        )
    )
    assert Path(f"/proc/{leader_pid}").exists()
    if launcher_output is None:
        launcher_output = _communicate_launcher(
            process,
            paths=paths,
            expected_returncode=0,
            label="correlated-session launcher",
        )
    stdout, stderr = launcher_output


def test_spawned_process_group_is_cleaned_on_manifest_append_failure(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "id_change_wait", expected_returncode=2
    )

    assert receipt is not None
    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert receipt["attempts"][0]["accepted"] is False
    child_pid = int((paths["pid_dir"] / "child.pid").read_text(encoding="ascii"))
    _assert_pid_gone(child_pid)
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_final_drain_actuals_are_rechecked_before_acceptance(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "final_drain",
        expected_returncode=1,
        max_calls=100,
        max_tokens=100,
        max_wall="11",
    )

    assert receipt is not None
    assert receipt["actuals"]["cli_reported"] == 110
    assert receipt["attempts"][0]["limit_trigger"] == (
        "max_cli_reported_tokens"
    )
    assert receipt["attempts"][0]["accepted"] is False
    assert not paths["output"].exists()


def test_fake_stdout_matches_observed_cli_event_shape(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    events = [
        json.loads(line)
        for line in Path(
            receipt["attempts"][0]["stdout_path"]
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert {"turn.started", "item.started", "item.completed"} <= {
        event["type"] for event in events
    }
    terminal = [event for event in events if event["type"] == "turn.completed"]
    assert terminal[0]["usage"]["cache_write_input_tokens"] == 0


def test_web_search_duplicate_stdout_is_accepted_and_auditable(
    tmp_path: Path,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path, "web_search_duplicate_stdout", expected_returncode=0
    )
    assert receipt is not None
    raw_line = (
        b'{"type":"item.started","item":{"id":"item_40",'
        b'"type":"web_search",'
        b'"id":"exec-f3ed5b5c-aa7d-4450-a1d8-44232d49c1e9",'
        b'"query":"","action":{"type":"other"}}}'
    )
    stdout = Path(receipt["attempts"][0]["stdout_path"]).read_bytes()
    assert raw_line + b"\n" in stdout
    attempt = receipt["attempts"][0]
    assert receipt["schema_version"] == 5
    assert attempt["evidence_status"] == "complete"
    assert attempt["accepted"] is True
    assert attempt["failure_class"] is None
    assert attempt["evidence_issues"] == [
        {
            "source": "stdout",
            "reason": "duplicate_key",
            "count": 1,
            "first_line": 4,
            "detail": None,
        }
    ]
    assert receipt["outcome"] == "accepted"
    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 0, checked.stderr


def test_check_receipt_rejects_non_string_evidence_issue_reason_with_rc2(
    tmp_path: Path,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    receipt["attempts"][0]["evidence_issues"] = [
        {
            "source": "stdout",
            "reason": ["event_invalid"],
            "count": 1,
            "first_line": 1,
            "detail": None,
        }
    ]
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2
    assert "attempt.evidence_issues[].reason が不正" in checked.stderr


def test_rollout_duplicate_key_remains_invalid(tmp_path: Path) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path, "rollout_duplicate_key", expected_returncode=1
    )
    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["evidence_status"] == "invalid"
    assert attempt["accepted"] is False
    assert any(
        issue["reason"] == "event_invalid"
        and issue["source"] != "stdout"
        for issue in attempt["evidence_issues"]
    )
    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 1, checked.stderr


def test_rollout_missing_after_grace_is_stopped_and_not_accepted(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "no_rollout",
        expected_returncode=1,
        max_wall="11",
        evidence_grace="0.3",
        max_calls=100,
        max_tokens=100000,
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["evidence_status"] == "missing"
    assert receipt["attempts"][0]["session_ids"]
    assert receipt["attempts"][0]["accepted"] is False
    diagnostics = _read_launcher_diagnostics(paths)
    diagnostic_attempt = diagnostics["attempts"][0]
    assert diagnostic_attempt["evidence_forced_stop"] is True
    assert diagnostic_attempt["termination_initiated_by_launcher"] is True
    assert diagnostic_attempt["termination_signals_sent"]
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_thread_missing_after_grace_kills_process_group(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "no_thread",
        expected_returncode=1,
        max_wall="11",
        evidence_grace="0.3",
        max_calls=100,
        max_tokens=100000,
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["evidence_status"] == "missing"
    diagnostics = _read_launcher_diagnostics(paths)
    diagnostic_attempt = diagnostics["attempts"][0]
    assert diagnostic_attempt["evidence_forced_stop"] is True
    assert diagnostic_attempt["termination_initiated_by_launcher"] is True
    assert [
        item["signal"]
        for item in diagnostic_attempt["termination_signals_sent"]
    ][0] == "SIGTERM"
    first_signal = diagnostic_attempt["termination_signals_sent"][0]
    assert set(first_signal) == {
        "signal",
        "job_elapsed_s_at",
        "attempt_elapsed_s_at",
    }
    assert first_signal["job_elapsed_s_at"] >= 0
    assert first_signal["attempt_elapsed_s_at"] >= 0
    child_pid = int((paths["pid_dir"] / "child.pid").read_text(encoding="ascii"))
    _assert_pid_gone(child_pid)
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_cached_exceeding_input_is_malformed(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "cached_bad", expected_returncode=1
    )

    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["attempts"][0]["evidence_status"] == "invalid"
    assert receipt["attempts"][0]["metering_status"] == "incomplete"
    assert receipt["attempts"][0]["accepted"] is False


def test_late_rollout_writer_does_not_change_sealed_receipt(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "late_writer", expected_returncode=0
    )
    assert receipt is not None
    rollout = receipt["attempts"][0]["rollouts"][0]
    sealed_bytes = rollout["bytes"]
    deadline = time.monotonic() + 3
    while (
        Path(rollout["path"]).stat().st_size == sealed_bytes
        and time.monotonic() < deadline
    ):
        time.sleep(0.02)
    assert Path(rollout["path"]).stat().st_size > sealed_bytes

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["rollout_grew_since_seal"] is True
    late_pid = int((paths["pid_dir"] / "late.pid").read_text(encoding="ascii"))
    _assert_pid_gone(late_pid)


def test_setsid_escape_is_not_claimed_as_contained(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "setsid_escape", expected_returncode=0
    )
    assert receipt is not None
    assert receipt["escaped_process_containment"] == "not_attempted"
    escaped_pid = int(
        (paths["pid_dir"] / "escaped.pid").read_text(encoding="ascii")
    )
    assert Path(f"/proc/{escaped_pid}").exists()
    os.kill(escaped_pid, signal.SIGKILL)
    _assert_pid_gone(escaped_pid)


def test_check_receipt_rejects_unknown_and_duplicate_fields(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None

    unknown = dict(receipt)
    unknown["unexpected"] = True
    paths["receipt"].write_text(
        json.dumps(unknown, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    checked_unknown = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked_unknown.returncode == 2

    raw = json.dumps(receipt, separators=(",", ":"))
    duplicate = raw[:-1] + ',"schema_version":1}\n'
    paths["receipt"].write_text(duplicate, encoding="utf-8")
    checked_duplicate = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked_duplicate.returncode == 2


def test_check_receipt_rejects_impossible_truth_table(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0
    )
    assert receipt is not None
    receipt["attempts"][0]["limit_trigger"] = "max_model_calls"
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 2


def test_check_receipt_detects_executable_identity_change(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path, "normal", expected_returncode=0, max_wall="8"
    )
    assert receipt is not None
    with (tmp_path / "fake-codex").open("a", encoding="utf-8") as stream:
        stream.write("\n# changed after receipt\n")

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 2


def test_partial_existing_receipt_is_atomically_replaced(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    paths["receipt"].write_bytes(b'{"schema_version":')
    env["FAKE_MODE"] = "normal"

    completed = _run_launcher_subprocess(
        command, env=env, paths=paths, expected_returncode=0
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert receipt["outcome"] == "accepted"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda manifest: manifest.update({"sessions": []}),
        lambda manifest: manifest["sessions"][0].update(
            {"attempt_index": True}
        ),
        lambda manifest: manifest["sessions"][0].update({"unknown": 1}),
        lambda manifest: manifest["sessions"][0].update(
            {"session_id": manifest["sessions"][0]["session_id"].upper()}
        ),
    ],
)
def test_frozen_manifest_schema_is_closed(
    mutate: Any,
) -> None:
    manifest = {
        "schema_version": 1,
        "wave_id": "wave-a",
        "repo_root": os.fspath(_ROOT),
        "base_commit": "a" * 40,
        "sessions": [
            {
                "job_id": "job-a",
                "attempt_index": 1,
                "session_id": "aaaaaaaa-0000-4000-8000-000000000001",
            }
        ],
    }
    mutate(manifest)

    with pytest.raises(LAUNCHER.LaunchError):
        LAUNCHER._validate_manifest(manifest)


def test_fake_can_reproduce_thread_id_change_and_multiple_sessions(
    tmp_path: Path,
) -> None:
    # 凍結 manifest は (job_id, attempt_index) を一意にするため、複数
    # session を receipt/manifest に同時表現できず launcher integrity error になる。
    completed, receipt, paths = _run_case(
        tmp_path, "id_change", expected_returncode=2
    )

    assert receipt is not None
    assert receipt["outcome"] == "launcher_error"
    assert receipt["stop_reason"] == "launcher_error"
    assert len(receipt["attempts"][0]["session_ids"]) == 2
    assert receipt["attempts"][0]["accepted"] is False
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert len(manifest["sessions"]) == 1
    assert len(list((paths["codex_home"] / "sessions").rglob("rollout-*.jsonl"))) == 2


def _run() -> int:
    """pytest fixture/parametrize を含む全 node を直接起動でも実走する。"""
    return int(pytest.main(["-q", os.fspath(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
