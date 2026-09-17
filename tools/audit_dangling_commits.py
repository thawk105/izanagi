#!/usr/bin/env python3
"""要確認の到達不能変更を検出する。

到達不能 commit が変更した path のうち、main にも他の local branch tip にも
存在しないものだけを報告する。fold が消費する tree は既定で除外する。

exit code: 0 = repo 外の同一実体による抑止後に取り残しなし / 1 = 取り残しあり / 2 = 実行不能
"""

from __future__ import annotations

import argparse
import queue
import hashlib
import os
import re
import stat
import subprocess
import sys
import time
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXCLUDED_PREFIXES = ("docs/spool/", "docs/archive/")
DEFAULT_REGENERABLE_PREFIXES = ("output/s8b-build-cache/",)
DEFAULT_REPO = Path(__file__).resolve().parents[1]
OFFREPO_SCAN_WORKERS = 16
OFFREPO_SCAN_WORKERS_ENV = "IZANAGI_AUDIT_SCAN_WORKERS"
OFFREPO_ROOT_ENV = "IZANAGI_DEV_WAVE_JOBS_DIR"
MAX_BLOB_SIZE = 32 * 1024 * 1024
AUDIT_ELAPSED_LIMIT_SECONDS = 300.0
HEARTBEAT_INTERVAL_SECONDS = 15.0
CAT_FILE_CLOSE_TIMEOUT_SECONDS = 15.0
# 100 ms caps zero-interval polling at 10 Hz; 1 s bounds overdue heartbeat lag.
POLL_FLOOR_SECONDS = 0.1
POLL_CEILING_SECONDS = 1.0
# 計測環境向けの保守値であり、environment と pointer table を含まないため
# execve 成功を保証する上限ではない。
GIT_GREP_BATCH_MAX_PATTERNS = 512
GIT_GREP_BATCH_MAX_ARGV_BYTES = 128 * 1024
LS_TREE_BATCH_MAX_PATHS = 512
LS_TREE_BATCH_MAX_ARGV_BYTES = 128 * 1024
READ_CHUNK_SIZE = 1024 * 1024
_PATH_BOUNDARY_BYTES = frozenset(b" \t\n\r\"'`()[]{}<>")
_PATH_BOUNDARY_PATTERN = re.compile(
    b"[" + re.escape(bytes(sorted(_PATH_BOUNDARY_BYTES))) + b"]"
)
_BULK_LOG_RECORD_MARKER = b"\0\0"
_BULK_LOG_RECORD_BOUNDARY = re.compile(
    rb"\0\0(?=(?:[0-9a-f]{40}|[0-9a-f]{64})\0)"
)
_BULK_LOG_FORMAT = "%x00%x00%H%x00%P%x00%s"

Finding = tuple[str, str, list[str]]
Suppression = tuple[str, str, Path]
ExternalCopy = tuple[str, str, Path]
RootRejection = tuple[Path, str]
OversizeBlob = tuple[str, str, int]
RegenerableOnlyCommit = tuple[str, str, int]
ProgressCallback = Callable[[str], None]
LIMITATION_NOTICE = (
    "検出対象外: 既存ファイルへの変更・削除・同名別内容・gitlink 更新"
)


@dataclass(frozen=True)
class AuditReport:
    findings: list[Finding]
    suppressions: list[Suppression]
    unreferenced_copies: list[ExternalCopy]
    requested_roots: tuple[Path, ...]
    accepted_roots: tuple[Path, ...]
    rejected_roots: tuple[RootRejection, ...]
    scan_performed: bool
    blob_failures: int
    scan_failures: int
    oversize_blobs: tuple[OversizeBlob, ...]
    reference_failure: str | None
    regenerable_excluded_pairs: int
    regenerable_only_commits: tuple[RegenerableOnlyCommit, ...]
    offrepo_scan: str = "full"


@dataclass(frozen=True)
class _CommitRecord:
    commit: str
    parents: tuple[str, ...]
    subject: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class _CoreAudit:
    findings: list[Finding]
    regenerable_excluded_pairs: int
    regenerable_only_commits: tuple[RegenerableOnlyCommit, ...]


@dataclass(frozen=True)
class _BlobMetadata:
    commit: str
    path: str
    basename: str
    executable: bool
    object_id: str
    size: int


@dataclass(frozen=True)
class _ExternalMatch:
    path: Path
    root: Path


@dataclass(frozen=True)
class _ExternalCandidate:
    path: Path
    root: Path
    initial_stat: os.stat_result


@dataclass
class _ExternalCandidateGroup:
    external: _ExternalCandidate
    metadata: _BlobMetadata
    owners: set[tuple[str, str]]
    aliases: set[_ExternalMatch]


@dataclass
class _LandedReferenceStats:
    match_keys: int = 0
    external_matches: int = 0
    generated_patterns: int = 0
    patterns: int = 0
    grep_batches: int = 0
    metadata_batches: int = 0
    contents_read: int = 0
    bytes_read: int = 0


_ExternalIdentity = tuple[int, int]
_PossibleCandidates = dict[
    str, dict[_ExternalIdentity, _ExternalCandidateGroup]
]


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    env.update({"GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})
    return env


def _git_argv(repo: Path, args: Sequence[str]) -> list[str]:
    return ["git", "-C", str(repo), *args]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """対象 repo に対して読み取り専用の git command を実行する。"""
    return subprocess.run(
        _git_argv(repo, args),
        env=_git_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_bytes(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """対象 repo に対して raw bytes を返す読み取り専用 git command を実行する。"""
    return subprocess.run(
        _git_argv(repo, args),
        env=_git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_bytes_input(
    repo: Path,
    args: Sequence[str],
    input_bytes: bytes,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        _git_argv(repo, args),
        env=_git_env(),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _checked_git(repo: Path, *args: str) -> str:
    completed = _git(repo, *args)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"git {' '.join(args)} に失敗した (rc={completed.returncode}): {detail}"
        )
    return completed.stdout


def _progress(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)


class _ProgressRateLimiter:
    """file / chunk loop で共有する wall-clock 基準の heartbeat。"""

    def __init__(
        self,
        progress: ProgressCallback | None,
        stage: str,
    ) -> None:
        self._progress = progress
        self._stage = stage
        self._next = (
            time.monotonic() + HEARTBEAT_INTERVAL_SECONDS
            if progress is not None
            else None
        )

    def pulse(self, detail: str) -> None:
        if self._progress is None or self._next is None:
            return
        now = time.monotonic()
        if now < self._next:
            return
        _progress(self._progress, f"{self._stage} heartbeat {detail}")
        self._next = now + HEARTBEAT_INTERVAL_SECONDS


def _git_with_heartbeat(
    repo: Path,
    args: Sequence[str],
    *,
    stage: str,
    progress: ProgressCallback,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        _git_argv(repo, args),
        env=_git_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    poll_timeout = max(
        POLL_FLOOR_SECONDS,
        min(HEARTBEAT_INTERVAL_SECONDS, POLL_CEILING_SECONDS),
    )
    started = time.monotonic()
    next_report = started + HEARTBEAT_INTERVAL_SECONDS
    while True:
        try:
            stdout, stderr = process.communicate(timeout=poll_timeout)
        except subprocess.TimeoutExpired:
            now = time.monotonic()
            if now < next_report:
                continue
            _progress(
                progress,
                f"{stage} heartbeat elapsed_seconds="
                f"{now - started:.3f}",
            )
            next_report = now + HEARTBEAT_INTERVAL_SECONDS
            continue
        return subprocess.CompletedProcess(
            _git_argv(repo, args), process.returncode, stdout, stderr
        )


def unreachable_commits(
    repo: Path,
    *,
    progress: ProgressCallback | None = None,
) -> list[str]:
    """reflog を到達性の根に含めず、到達不能 commit の object ID を返す。"""
    args = (
        "fsck",
        "--unreachable",
        "--no-reflogs",
        "--no-progress",
        "--connectivity-only",
    )
    if progress is None:
        completed = _git(repo, *args)
    else:
        completed = _git_with_heartbeat(
            repo, args, stage="fsck", progress=progress
        )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"git {' '.join(args)} に失敗した "
            f"(rc={completed.returncode}): {detail}"
        )
    output = completed.stdout
    if output and not output.endswith("\n"):
        raise RuntimeError("git fsck の出力が終端 LF より前で切れた")
    commits: list[str] = []
    for line in output.splitlines():
        if not line.startswith("unreachable commit"):
            continue
        fields = line.split()
        if (
            len(fields) != 3
            or fields[:2] != ["unreachable", "commit"]
            or not _valid_object_id(os.fsencode(fields[2]))
        ):
            raise RuntimeError("git fsck の unreachable commit 行が不正")
        commits.append(fields[2])
    return sorted(set(commits))


def _valid_object_id(value: bytes) -> bool:
    return len(value) in {40, 64} and all(
        byte in b"0123456789abcdef" for byte in value
    )


def _parse_bulk_commit_records(
    output: bytes,
    requested_commits: Sequence[str],
) -> dict[str, _CommitRecord]:
    expected = set(requested_commits)
    if len(expected) != len(requested_commits):
        raise RuntimeError("bulk log の入力 commit が重複している")
    if not output.startswith(_BULK_LOG_RECORD_MARKER):
        raise RuntimeError("bulk log の先頭 record marker が不正")
    chunks = _BULK_LOG_RECORD_BOUNDARY.split(
        output[len(_BULK_LOG_RECORD_MARKER) :]
    )

    records: dict[str, _CommitRecord] = {}
    for chunk in chunks:
        try:
            commit_raw, parents_raw, remainder = chunk.split(b"\0", 2)
        except ValueError as exc:
            raise RuntimeError("bulk log の commit record を解釈できない") from exc
        subject_raw, subject_separator, paths_raw = remainder.partition(b"\0")
        if not subject_separator:
            raise RuntimeError("bulk log の subject 終端が不正")
        if not _valid_object_id(commit_raw):
            raise RuntimeError("bulk log の commit OID が不正")
        commit = commit_raw.decode("ascii")
        if commit not in expected:
            raise RuntimeError(f"bulk log に入力外 commit が現れた: {commit}")
        if commit in records:
            raise RuntimeError(f"bulk log の commit が重複した: {commit}")

        parent_fields = tuple(field for field in parents_raw.split(b" ") if field)
        if any(not _valid_object_id(parent) for parent in parent_fields):
            raise RuntimeError(f"bulk log の parent OID が不正: {commit}")
        parents = tuple(parent.decode("ascii") for parent in parent_fields)
        subject = subject_raw.decode("utf-8").strip()

        path_fields: list[bytes] = []
        # 区切り無しの空 block は単親の空 commit の正規形である。途中の record は
        # marker 先読みで確定し、末尾を含む欠落は git rc=0 と要求 OID の
        # 一意完全性検査で別層から担保する。
        if paths_raw:
            if paths_raw[:1] not in (b"\n", b"\0"):
                raise RuntimeError(
                    f"bulk log の header/path 境界が不正: {commit}"
                )
            path_block = paths_raw[1:]
            if path_block:
                if not path_block.endswith(b"\0"):
                    raise RuntimeError(
                        f"bulk log の header/path 境界が不正: {commit}"
                    )
                path_fields = path_block[:-1].split(b"\0")
                if not path_fields or any(not field for field in path_fields):
                    raise RuntimeError(f"bulk log の path block が不正: {commit}")
        paths = tuple(sorted({os.fsdecode(path) for path in path_fields}))
        records[commit] = _CommitRecord(commit, parents, subject, paths)

    missing = expected - records.keys()
    extra = records.keys() - expected
    if missing or extra or len(records) != len(requested_commits):
        raise RuntimeError(
            "bulk log の完全性検査に失敗した "
            f"(missing={len(missing)}, extra={len(extra)})"
        )
    return records


def bulk_commit_records(
    repo: Path,
    commits: Sequence[str],
) -> dict[str, _CommitRecord]:
    """全 commit の親、subject、combined changed paths を 1 fork で返す。"""
    if not commits:
        return {}
    arguments = (
        "log",
        "--no-walk=unsorted",
        "--stdin",
        f"--format={_BULK_LOG_FORMAT}",
        "--name-only",
        "-z",
        "-r",
        "--no-renames",
        "--no-ext-diff",
        "--no-textconv",
        "-m",
        "-c",
        "--root",
    )
    input_bytes = b"".join(os.fsencode(commit) + b"\n" for commit in commits)
    completed = _git_bytes_input(repo, arguments, input_bytes)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise RuntimeError(
            f"bulk git log に失敗した (rc={completed.returncode}): {detail}"
        )
    return _parse_bulk_commit_records(completed.stdout, commits)


def tree_paths(repo: Path, ref: str) -> set[str]:
    """ref の tree に存在する全 path を返す。"""
    completed = _git_bytes(repo, "ls-tree", "-r", "--name-only", "-z", ref)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise RuntimeError(f"git ls-tree に失敗した (rc={completed.returncode}): {detail}")
    return {os.fsdecode(path) for path in completed.stdout.split(b"\0") if path}


def branch_tip_commits(repo: Path) -> list[str]:
    """local branch tips の commit object ID を返す。"""
    output = _checked_git(
        repo,
        "for-each-ref",
        "--format=%(objectname)",
        "refs/heads/",
    )
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def _ls_tree_argv_size(repo: Path, commit: str, paths: Sequence[str]) -> int:
    arguments = _git_argv(
        repo,
        (
            "--literal-pathspecs",
            "ls-tree",
            "-z",
            "-l",
            "--full-tree",
            commit,
            "--",
            *paths,
        ),
    )
    return sum(len(os.fsencode(argument)) + 1 for argument in arguments)


def _ls_tree_path_batches(
    repo: Path,
    commit: str,
    paths: Sequence[str],
    *,
    max_paths_per_batch: int = LS_TREE_BATCH_MAX_PATHS,
    max_argv_bytes: int = LS_TREE_BATCH_MAX_ARGV_BYTES,
) -> tuple[tuple[str, ...], ...]:
    if max_paths_per_batch <= 0:
        raise ValueError("max_paths_per_batch は正でなければならない")
    if max_argv_bytes <= 0:
        raise ValueError("max_argv_bytes は正でなければならない")
    batches: list[tuple[str, ...]] = []
    current: list[str] = []
    for path in paths:
        candidate = (*current, path)
        if current and (
            len(candidate) > max_paths_per_batch
            or _ls_tree_argv_size(repo, commit, candidate) > max_argv_bytes
        ):
            batches.append(tuple(current))
            current = []
        current.append(path)
    if current:
        batches.append(tuple(current))
    return tuple(batches)


def _git_ls_tree_batch(
    repo: Path,
    commit: str,
    paths: Sequence[str],
) -> subprocess.CompletedProcess[bytes]:
    return _git_bytes(
        repo,
        "--literal-pathspecs",
        "ls-tree",
        "-z",
        "-l",
        "--full-tree",
        commit,
        "--",
        *paths,
    )


def _parse_ls_tree_batch(
    commit: str,
    requested_paths: Sequence[str],
    output: bytes,
) -> dict[str, _BlobMetadata]:
    requested_by_bytes = {os.fsencode(path): path for path in requested_paths}
    if len(requested_by_bytes) != len(requested_paths):
        raise RuntimeError("ls-tree batch の入力 path が重複している")
    parsed: dict[str, _BlobMetadata] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        if b"\t" not in record:
            raise RuntimeError("ls-tree batch の record を解釈できない")
        metadata, raw_path = record.split(b"\t", 1)
        path = requested_by_bytes.get(raw_path)
        if path is None or path in parsed:
            raise RuntimeError("ls-tree batch の path が入力と一致しない")
        fields = metadata.split()
        if len(fields) != 4:
            raise RuntimeError("ls-tree batch の metadata を解釈できない")
        mode, object_type, object_id, size_raw = fields
        if mode not in {b"100644", b"100755"} or object_type != b"blob":
            continue
        if not _valid_object_id(object_id):
            raise RuntimeError("ls-tree batch の blob OID が不正")
        try:
            size = int(size_raw)
        except ValueError as exc:
            raise RuntimeError("ls-tree batch の blob size が不正") from exc
        if size < 0:
            raise RuntimeError("ls-tree batch の blob size が負")
        parsed[path] = _BlobMetadata(
            commit=commit,
            path=path,
            basename=Path(path).name,
            executable=mode == b"100755",
            object_id=object_id.decode("ascii"),
            size=size,
        )
    return parsed


def _load_blob_metadata(
    repo: Path,
    findings: Sequence[Finding],
) -> tuple[list[_BlobMetadata], int, tuple[OversizeBlob, ...]]:
    candidates: list[_BlobMetadata] = []
    failures = 0
    oversize: list[OversizeBlob] = []
    for commit, _subject, paths in findings:
        for batch in _ls_tree_path_batches(repo, commit, paths):
            completed = _git_ls_tree_batch(repo, commit, batch)
            if completed.returncode != 0:
                failures += len(batch)
                continue
            try:
                parsed = _parse_ls_tree_batch(commit, batch, completed.stdout)
            except (OSError, RuntimeError, UnicodeError):
                failures += len(batch)
                continue
            for path in batch:
                metadata = parsed.get(path)
                if metadata is None:
                    continue
                if metadata.size > MAX_BLOB_SIZE:
                    oversize.append((commit, path, metadata.size))
                else:
                    candidates.append(metadata)
    return candidates, failures, tuple(oversize)


def _validate_offrepo_roots(
    repo: Path,
    roots: Sequence[Path | str],
    *,
    worktree: Path | None = None,
) -> tuple[tuple[Path, ...], tuple[Path, ...], tuple[RootRejection, ...]]:
    """探索根を絶対 path 化し、worktree と重なる root を拒否する。"""
    if not roots:
        return (), (), ()
    if worktree is None:
        worktree = Path(
            _checked_git(repo, "rev-parse", "--show-toplevel").strip()
        ).resolve()
    requested: list[Path] = []
    accepted: list[Path] = []
    rejected: list[RootRejection] = []
    seen: set[Path] = set()
    for raw_root in roots:
        try:
            root = Path(raw_root).resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            fallback = Path(raw_root).absolute()
            rejected.append((fallback, f"絶対 path 化不能: {exc}"))
            if fallback not in seen:
                requested.append(fallback)
                seen.add(fallback)
            continue
        if root in seen:
            continue
        seen.add(root)
        requested.append(root)
        if root == Path(root.anchor):
            rejected.append((root, "filesystem root は探索範囲が広すぎる"))
        elif root == worktree:
            rejected.append((root, "対象 worktree と同一"))
        elif root.is_relative_to(worktree):
            rejected.append((root, "対象 worktree の子孫"))
        elif worktree.is_relative_to(root):
            rejected.append((root, "対象 worktree の祖先"))
        else:
            accepted.append(root)
    return tuple(requested), tuple(accepted), tuple(rejected)


def _start_cat_file_batch(repo: Path) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        _git_argv(repo, ("cat-file", "--batch")),
        env=_git_env(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )


class _CatFileBatch:
    """1 本の cat-file process と逐次照合する protocol client。"""

    def __init__(
        self,
        repo: Path,
        *,
        progress: ProgressCallback | None = None,
    ) -> None:
        self._process = _start_cat_file_batch(repo)
        self._error: str | None = None
        self._closed = False
        self._read_chunks = 0
        self._heartbeat = _ProgressRateLimiter(progress, "cat-file read")
        self.requested_object_ids: list[str] = []

    @property
    def error(self) -> str | None:
        return self._error

    def _fail(self, detail: str) -> RuntimeError:
        if self._error is None:
            self._error = detail
        return RuntimeError(self._error)

    def read_blob(self, object_id: str, expected_size: int) -> bytes:
        if self._closed:
            raise self._fail("cat-file --batch は既に終了している")
        if self._error is not None:
            raise RuntimeError(self._error)
        stdin = self._process.stdin
        stdout = self._process.stdout
        if stdin is None or stdout is None:
            raise self._fail("cat-file --batch の pipe を確立できない")
        self.requested_object_ids.append(object_id)
        try:
            stdin.write(object_id.encode("ascii") + b"\n")
            stdin.flush()
            header = stdout.readline()
        except (BrokenPipeError, OSError) as exc:
            raise self._fail(f"cat-file --batch の入出力に失敗した: {exc}") from exc
        if not header.endswith(b"\n"):
            raise self._fail("cat-file --batch の応答 header が途中で切れた")
        fields = header[:-1].split()
        expected_oid = object_id.encode("ascii")
        if len(fields) != 3:
            raise self._fail("cat-file --batch の応答 header が不正")
        echoed_oid, object_type, size_raw = fields
        try:
            response_size = int(size_raw)
        except ValueError as exc:
            raise self._fail("cat-file --batch の応答 size が不正") from exc
        if echoed_oid != expected_oid:
            raise self._fail(
                "cat-file --batch の echoed OID が要求と一致しない"
            )
        if object_type != b"blob":
            raise self._fail("cat-file --batch の応答 type が blob でない")
        if response_size != expected_size:
            raise self._fail("cat-file --batch の応答 size が metadata と一致しない")

        chunks: list[bytes] = []
        remaining = expected_size
        try:
            while remaining:
                chunk = stdout.read(min(READ_CHUNK_SIZE, remaining))
                if not chunk:
                    raise self._fail(
                        "cat-file --batch の blob content が途中で切れた"
                    )
                chunks.append(chunk)
                remaining -= len(chunk)
                self._read_chunks += 1
                self._heartbeat.pulse(f"chunks={self._read_chunks}")
            if stdout.read(1) != b"\n":
                raise self._fail("cat-file --batch の blob 終端 LF が不正")
        except OSError as exc:
            raise self._fail(f"cat-file --batch の読出しに失敗した: {exc}") from exc
        return b"".join(chunks)

    def _signal_child(self, signal_name: str) -> None:
        try:
            getattr(self._process, signal_name)()
        except ProcessLookupError:
            pass
        except OSError as exc:
            self._fail(
                f"cat-file --batch の {signal_name} に失敗した: {exc}"
            )

    def _communicate_and_reap(self, *, abort: bool) -> tuple[bytes, bytes] | None:
        if abort:
            self._signal_child("terminate")
        close_timeout = max(
            POLL_FLOOR_SECONDS, CAT_FILE_CLOSE_TIMEOUT_SECONDS
        )
        try:
            return self._process.communicate(timeout=close_timeout)
        except subprocess.TimeoutExpired:
            self._fail("cat-file --batch の終了確認が timeout した")
            if not abort:
                self._signal_child("terminate")
            try:
                return self._process.communicate(timeout=close_timeout)
            except subprocess.TimeoutExpired:
                self._signal_child("kill")
                try:
                    return self._process.communicate(timeout=close_timeout)
                except subprocess.TimeoutExpired:
                    self._fail("cat-file --batch を kill 後も reap できない")
                    return None
                except (OSError, ValueError) as exc:
                    self._fail(
                        f"cat-file --batch の kill 後の終了確認に失敗した: {exc}"
                    )
                    return None
            except (OSError, ValueError) as exc:
                self._fail(f"cat-file --batch の終了確認に失敗した: {exc}")
                return None
        except (OSError, ValueError) as exc:
            self._fail(f"cat-file --batch の終了確認に失敗した: {exc}")
            return None

    def close(self) -> str | None:
        if self._closed:
            return self._error
        self._closed = True
        completed = self._communicate_and_reap(abort=self._error is not None)
        if completed is None:
            return self._error
        trailing, stderr_bytes = completed
        if trailing:
            self._fail("cat-file --batch の全応答後に余分な stdout がある")
        if self._process.returncode != 0:
            detail = stderr_bytes.decode("utf-8", errors="replace").strip()
            self._fail(
                "cat-file --batch が非 0 終了した "
                f"(rc={self._process.returncode}): {detail}"
            )
        return self._error


def _compare_regular_candidate(
    path: Path,
    initial_stat: os.stat_result,
    metadata: _BlobMetadata,
    content: bytes,
    digest_bytes: bytes,
    *,
    heartbeat: Callable[[str], None] | None = None,
) -> tuple[bool, bool]:
    """外部 regular file を全体保持せず 1 pass で hash と bytes を比較する。"""
    if not stat.S_ISREG(initial_stat.st_mode):
        return False, False
    if initial_stat.st_size != metadata.size or metadata.size != len(content):
        return False, False
    if bool(initial_stat.st_mode & stat.S_IXUSR) != metadata.executable:
        return False, False
    nofollow = getattr(os, "O_NOFOLLOW", None)
    cloexec = getattr(os, "O_CLOEXEC", None)
    if nofollow is None or cloexec is None:
        return False, True

    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | cloexec | nofollow)
        opened_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_stat.st_mode)
            or opened_stat.st_dev != initial_stat.st_dev
            or opened_stat.st_ino != initial_stat.st_ino
            or opened_stat.st_size != metadata.size
            or bool(opened_stat.st_mode & stat.S_IXUSR) != metadata.executable
        ):
            return False, True

        digest = hashlib.sha256()
        offset = 0
        chunks_read = 0
        while offset < metadata.size:
            chunk = os.read(
                descriptor,
                min(READ_CHUNK_SIZE, metadata.size - offset),
            )
            if not chunk:
                return False, True
            if chunk != content[offset : offset + len(chunk)]:
                return False, False
            digest.update(chunk)
            offset += len(chunk)
            chunks_read += 1
            if heartbeat is not None:
                heartbeat(f"read_chunks={chunks_read}")
        if os.read(descriptor, 1):
            return False, True
        if digest.digest() != digest_bytes:
            return False, False
        final_stat = os.fstat(descriptor)
        if (
            final_stat.st_size,
            final_stat.st_mtime_ns,
            final_stat.st_ctime_ns,
            final_stat.st_ino,
            final_stat.st_mode,
        ) != (
            opened_stat.st_size,
            opened_stat.st_mtime_ns,
            opened_stat.st_ctime_ns,
            opened_stat.st_ino,
            opened_stat.st_mode,
        ):
            return False, True
        return True, False
    except OSError:
        return False, True
    finally:
        if descriptor is not None:
            os.close(descriptor)


_WalkKey = tuple[tuple[int, str], ...]
_OffrepoKeys = dict[tuple[str, _ExternalIdentity], tuple[_WalkKey, int]]
_OffrepoIndex = dict[str, dict[int, dict[bool, list[_BlobMetadata]]]]


@dataclass
class _OffrepoCounts:
    directories: int = 0
    files: int = 0
    failures: int = 0

    def record_error(self, _error: OSError) -> None:
        self.failures += 1


class _OffrepoCountSlot:
    """A worker publishes cumulative counts; only the caller emits progress."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts = (0, 0, 0)

    def publish(self, counts: _OffrepoCounts) -> None:
        with self._lock:
            self._counts = (counts.directories, counts.files, counts.failures)

    def read(self) -> tuple[int, int, int]:
        with self._lock:
            return self._counts


def _offrepo_scan_workers() -> int:
    raw = os.environ.get(OFFREPO_SCAN_WORKERS_ENV)
    try:
        workers = OFFREPO_SCAN_WORKERS if raw is None else int(raw)
    except ValueError:
        raise RuntimeError(f"{OFFREPO_SCAN_WORKERS_ENV} must be a positive integer") from None
    if not isinstance(workers, int) or isinstance(workers, bool) or workers <= 0:
        raise RuntimeError(f"{OFFREPO_SCAN_WORKERS_ENV} must be a positive integer")
    return workers


def _process_offrepo_iteration(
    root: Path,
    iteration: tuple[str, list[str], list[str]],
    by_basename: _OffrepoIndex,
    possible: _PossibleCandidates,
    counts: _OffrepoCounts,
    notify: Callable[[], None],
    keys: _OffrepoKeys | None = None,
    key_prefix: _WalkKey = (),
) -> None:
    directory, dirnames, filenames = iteration
    counts.directories += 1
    dirnames.sort()
    filenames.sort()
    notify()
    for filename in filenames:
        counts.files += 1
        notify()
        size_index = by_basename.get(filename)
        if size_index is None:
            continue
        path = Path(directory) / filename
        try:
            candidate_stat = path.lstat()
        except OSError:
            counts.failures += 1
            continue
        if not stat.S_ISREG(candidate_stat.st_mode):
            continue
        executable = bool(candidate_stat.st_mode & stat.S_IXUSR)
        same_prefilter = size_index.get(
            candidate_stat.st_size, {}
        ).get(executable, ())
        for position, candidate in enumerate(same_prefilter):
            absolute_path = path.absolute()
            external = _ExternalCandidate(
                path=absolute_path,
                root=root,
                initial_stat=candidate_stat,
            )
            identity = (
                candidate_stat.st_dev,
                candidate_stat.st_ino,
            )
            groups = possible.setdefault(candidate.object_id, {})
            group = groups.get(identity)
            if group is None:
                group = _ExternalCandidateGroup(
                    external=external,
                    metadata=candidate,
                    owners=set(),
                    aliases=set(),
                )
                groups[identity] = group
            if keys is not None:
                key = (key_prefix + ((0, filename),), position)
                group_key = (candidate.object_id, identity)
                if group_key not in keys or key < keys[group_key]:
                    group.external = external
                    group.metadata = candidate
                    keys[group_key] = key
            group.owners.add((candidate.commit, candidate.path))
            group.aliases.add(
                _ExternalMatch(path=absolute_path, root=root)
            )


def _scan_offrepo_directory(
    directory: Path,
    key_prefix: _WalkKey,
    root: Path,
    by_basename: _OffrepoIndex,
    possible: _PossibleCandidates,
    keys: _OffrepoKeys,
    counts: _OffrepoCounts,
    notify: Callable[[], None],
) -> list[tuple[Path, _WalkKey]]:
    """Process one walk yield; the queue owns recursion."""
    walk = os.walk(
        directory, topdown=True, onerror=counts.record_error, followlinks=False
    )
    try:
        iteration = next(walk, None)
        if iteration is None:
            return []
        _process_offrepo_iteration(
            root, iteration, by_basename, possible, counts, notify, keys, key_prefix
        )
        return [
            (Path(os.path.join(directory, name)), key_prefix + ((1, name),))
            for name in iteration[1]
            if not os.path.islink(os.path.join(directory, name))
        ]
    finally:
        walk.close()


def _run_offrepo_queue(
    tasks: list[tuple[Path, _WalkKey]],
    root: Path,
    by_basename: _OffrepoIndex,
    workers: int,
    possible: _PossibleCandidates,
    keys: _OffrepoKeys,
    counts: _OffrepoCounts,
    heartbeat: _ProgressRateLimiter,
) -> None:
    pending = len(tasks)
    work = queue.Queue()
    for task in tasks:
        work.put(task)
    lock = threading.Lock()
    stopped = threading.Event()
    done = threading.Event()
    errors: list[BaseException] = []
    slots = [_OffrepoCountSlot() for _ in range(workers)]
    results = [({}, {}) for _ in range(workers)]

    def worker(index: int) -> None:
        nonlocal pending
        local = _OffrepoCounts()
        found, found_keys = results[index]
        slot = slots[index]

        def publish() -> None:
            if local.files % 256 == 0:
                slot.publish(local)

        try:
            while True:
                task = work.get()
                if task is None or stopped.is_set():
                    return
                children = _scan_offrepo_directory(
                    *task, root, by_basename, found, found_keys, local, publish
                )
                slot.publish(local)
                with lock:
                    for child in children:
                        work.put(child)
                    pending += len(children) - 1
                    if pending == 0:
                        done.set()
                        return
        except BaseException as error:
            with lock:
                if not errors:
                    errors.append(error)
                stopped.set()
                done.set()
        finally:
            slot.publish(local)

    threads = []
    try:
        for index in range(workers):
            thread = threading.Thread(target=worker, args=(index,), daemon=False)
            thread.start()
            threads.append(thread)
        while True:
            finished = done.wait(timeout=POLL_CEILING_SECONDS)
            totals = [slot.read() for slot in slots]
            heartbeat.pulse(
                f"directories={counts.directories + sum(t[0] for t in totals)} "
                f"files={counts.files + sum(t[1] for t in totals)}"
            )
            if finished:
                break
    finally:
        stopped.set()
        for _ in threads:
            work.put(None)
        for thread in threads:
            thread.join()
    if errors:
        raise errors[0]
    for (found, found_keys), slot in zip(results, slots):
        _merge_offrepo_candidates(possible, found, keys, found_keys)
        directories, files, failures = slot.read()
        counts.directories += directories
        counts.files += files
        counts.failures += failures


def _merge_offrepo_candidates(
    possible: _PossibleCandidates, incoming: _PossibleCandidates,
    keys: _OffrepoKeys | None = None, incoming_keys: _OffrepoKeys | None = None,
) -> None:
    for object_id, groups in incoming.items():
        destination = possible.setdefault(object_id, {})
        for identity, group in groups.items():
            existing = destination.get(identity)
            if keys is not None and incoming_keys is not None:
                group_key = (object_id, identity)
                key = incoming_keys[group_key]
                if group_key not in keys or key < keys[group_key]:
                    keys[group_key] = key
                    if existing is not None:
                        existing.external = group.external
                        existing.metadata = group.metadata
            if existing is None:
                destination[identity] = group
            else:
                existing.owners.update(group.owners)
                existing.aliases.update(group.aliases)


def _enumerate_offrepo_candidates(
    roots: Sequence[Path],
    candidates: Sequence[_BlobMetadata],
    *,
    progress: ProgressCallback | None = None,
) -> tuple[_PossibleCandidates, int, bool]:
    """blob を読まず basename・size・mode が一致する外部実体を列挙する。"""
    if not candidates:
        return {}, 0, False
    workers = _offrepo_scan_workers()
    by_basename: _OffrepoIndex = {}
    for candidate in candidates:
        by_basename.setdefault(candidate.basename, {}).setdefault(
            candidate.size, {}
        ).setdefault(candidate.executable, []).append(candidate)

    possible: _PossibleCandidates = {}
    counts = _OffrepoCounts()
    heartbeat = _ProgressRateLimiter(progress, "repo 外走査")

    def pulse() -> None:
        heartbeat.pulse(f"directories={counts.directories} files={counts.files}")

    for root in sorted(roots):
        try:
            root_stat = root.lstat()
        except OSError:
            counts.failures += 1
            continue
        permission_bits = stat.S_IMODE(root_stat.st_mode)
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or permission_bits & 0o444 == 0
            or permission_bits & 0o111 == 0
        ):
            counts.failures += 1
            continue

        if workers == 1:
            walk = os.walk(
                root, topdown=True, onerror=counts.record_error, followlinks=False
            )
            for iteration in walk:
                _process_offrepo_iteration(
                    root, iteration, by_basename, possible, counts, pulse
                )
            continue

        found: _PossibleCandidates = {}
        keys: _OffrepoKeys = {}
        tasks = _scan_offrepo_directory(
            root, (), root, by_basename, found, keys, counts, pulse
        )
        if tasks:
            _run_offrepo_queue(
                tasks, root, by_basename, workers, found, keys, counts, heartbeat
            )
        # Restore DFS insertion order, then retain representatives from earlier roots.
        ordered: _PossibleCandidates = {}
        for object_id, identity in sorted(keys, key=keys.__getitem__):
            ordered.setdefault(object_id, {})[identity] = found[object_id][identity]
        _merge_offrepo_candidates(possible, ordered)
    return possible, counts.failures, True


def _compare_offrepo_candidates(
    cat_file: _CatFileBatch,
    possible: _PossibleCandidates,
    *,
    progress: ProgressCallback | None = None,
) -> tuple[dict[tuple[str, str], list[_ExternalMatch]], set[tuple[str, str]], int]:
    match_sets: dict[tuple[str, str], set[_ExternalMatch]] = {}
    failed_keys: set[tuple[str, str]] = set()
    failures = 0
    heartbeat = _ProgressRateLimiter(progress, "候補比較")
    comparisons = 0
    for object_id in sorted(possible):
        groups = list(possible[object_id].values())
        size = groups[0].metadata.size
        affected = {
            owner for group in groups for owner in group.owners
        }
        try:
            content = cat_file.read_blob(object_id, size)
        except (OSError, RuntimeError):
            failed_keys.update(affected)
            continue
        digest_bytes = hashlib.sha256(content).digest()
        for group in groups:
            comparisons += 1
            heartbeat.pulse(f"files={comparisons}")
            identical, failed = _compare_regular_candidate(
                group.external.path,
                group.external.initial_stat,
                group.metadata,
                content,
                digest_bytes,
                heartbeat=heartbeat.pulse,
            )
            if failed:
                failures += 1
            if identical:
                for key in group.owners:
                    match_sets.setdefault(key, set()).update(group.aliases)
    matches = {
        key: sorted(found, key=lambda item: (str(item.path), str(item.root)))
        for key, found in match_sets.items()
    }
    return matches, failed_keys, failures


def _reference_patterns(match: _ExternalMatch) -> tuple[str, ...]:
    patterns = [str(match.path)]
    ancestor = match.path.parent
    while ancestor != match.root:
        patterns.append(str(ancestor))
        if ancestor.parent == ancestor:
            break
        ancestor = ancestor.parent
    return tuple(patterns)


def _build_pattern_owners(
    matches: dict[tuple[str, str], list[_ExternalMatch]],
    *,
    progress: ProgressCallback | None = None,
) -> tuple[
    dict[str, list[tuple[tuple[str, str], Path]]], int, int
]:
    """pattern ごとの owner を初出順・重複なしで構築する。"""
    pattern_owners: dict[str, list[tuple[tuple[str, str], Path]]] = {}
    pattern_owner_seen: dict[
        str, set[tuple[tuple[str, str], Path]]
    ] = {}
    processed_matches = 0
    generated_patterns = 0
    heartbeat = _ProgressRateLimiter(progress, "landed 参照")
    for key, external_matches in matches.items():
        for match in external_matches:
            processed_matches += 1
            # key は str の tuple、Path は immutable かつ hashable である。
            owner = (key, match.path)
            for pattern in _reference_patterns(match):
                generated_patterns += 1
                seen = pattern_owner_seen.setdefault(pattern, set())
                if owner not in seen:
                    seen.add(owner)
                    pattern_owners.setdefault(pattern, []).append(owner)
            heartbeat.pulse(
                f"pattern_owners processed_matches={processed_matches} "
                f"generated_patterns={generated_patterns}"
            )
    return pattern_owners, processed_matches, generated_patterns


def _has_bounded_path_reference(content: bytes, pattern: bytes) -> bool:
    """pattern が前後の path 境界を満たす出現を 1 つでも持つか返す。"""
    if not pattern:
        return False
    start = 0
    while True:
        index = content.find(pattern, start)
        if index < 0:
            return False
        end = index + len(pattern)
        left_bounded = index == 0 or content[index - 1] in _PATH_BOUNDARY_BYTES
        right_bounded = (
            end == len(content) or content[end] in _PATH_BOUNDARY_BYTES
        )
        # 未知 byte（非 ASCII を含む）は path の延長として扱い、抑止しない。
        if left_bounded and right_bounded:
            return True
        start = index + 1


def _bounded_path_reference_matches(
    content: bytes,
    patterns: set[bytes],
    accepted_roots: set[bytes],
    *,
    heartbeat: Callable[[int], None] | None = None,
) -> set[bytes]:
    """探索根ごとの単一走査で、境界を満たす pattern の集合を返す。"""
    if not content or not patterns:
        return set()

    matched: set[bytes] = set()
    for root in sorted(accepted_roots):
        if not root:
            continue
        chunk_start = 0
        while chunk_start < len(content):
            chunk_end = min(chunk_start + READ_CHUNK_SIZE, len(content))
            search_start = chunk_start
            search_end = min(len(content), chunk_end + len(root) - 1)
            while True:
                index = content.find(root, search_start, search_end)
                if index < 0 or index >= chunk_end:
                    break
                left_bounded = (
                    index == 0 or content[index - 1] in _PATH_BOUNDARY_BYTES
                )
                if left_bounded:
                    boundary = _PATH_BOUNDARY_PATTERN.search(
                        content, index + len(root)
                    )
                    end = boundary.start() if boundary is not None else len(content)
                    token = content[index:end]
                    # D248 は pattern の左右が境界 byte なら path として完結とする。
                    # 左境界から次の右境界までの token は、その位置で唯一の完結候補である。
                    # よって token の set 一致は、pattern の境界付き出現と同値である。
                    if token in patterns:
                        matched.add(token)
                search_start = index + 1
            if heartbeat is not None:
                heartbeat(chunk_end - chunk_start)
            chunk_start = chunk_end
    return matched


def _git_grep_argv_size(
    repo: Path,
    main_ref: str,
    patterns: Sequence[str],
) -> int:
    """``_git_bytes`` が実行する完全な git-grep argv の byte 数を返す。

    各 argv 要素の filesystem encoding と終端 NUL を数える。environment と
    pointer table は含めず、この値だけで execve 成功を保証しない。
    """
    arguments = ["git", "-C", str(repo), "grep", "-F", "-l", "-z"]
    for pattern in patterns:
        arguments.extend(("-e", pattern))
    arguments.extend((main_ref, "--"))
    return sum(len(os.fsencode(argument)) + 1 for argument in arguments)


def _git_grep_pattern_batches(
    repo: Path,
    main_ref: str,
    patterns: Sequence[str],
    *,
    max_patterns_per_batch: int = GIT_GREP_BATCH_MAX_PATTERNS,
    max_argv_bytes: int = GIT_GREP_BATCH_MAX_ARGV_BYTES,
) -> tuple[tuple[str, ...], ...]:
    """入力を欠落・複製せず、順序と二つの上限を保って分割する。"""
    if max_patterns_per_batch <= 0:
        raise ValueError("max_patterns_per_batch は正でなければならない")
    if max_argv_bytes <= 0:
        raise ValueError("max_argv_bytes は正でなければならない")

    batches: list[tuple[str, ...]] = []
    current: list[str] = []
    base_argv_bytes = _git_grep_argv_size(repo, main_ref, ())
    current_argv_bytes = base_argv_bytes
    encoded_e_bytes = len(os.fsencode("-e")) + 1
    for pattern in patterns:
        pattern_argv_bytes = encoded_e_bytes + len(os.fsencode(pattern)) + 1
        exceeds_count = len(current) + 1 > max_patterns_per_batch
        exceeds_bytes = current_argv_bytes + pattern_argv_bytes > max_argv_bytes
        if current and (exceeds_count or exceeds_bytes):
            batches.append(tuple(current))
            current = []
            current_argv_bytes = base_argv_bytes
        current.append(pattern)
        current_argv_bytes += pattern_argv_bytes
    if current:
        batches.append(tuple(current))
    return tuple(batches)


def _landed_reference_matches(
    repo: Path,
    main_ref: str,
    matches: dict[tuple[str, str], list[_ExternalMatch]],
    *,
    max_patterns_per_batch: int = GIT_GREP_BATCH_MAX_PATTERNS,
    max_argv_bytes: int = GIT_GREP_BATCH_MAX_ARGV_BYTES,
    cat_file: _CatFileBatch | None = None,
    progress: ProgressCallback | None = None,
    stats: _LandedReferenceStats | None = None,
) -> tuple[dict[tuple[str, str], list[Path]], str | None]:
    """bytes 一致候補を上限つき git grep へ分け、landed 参照を確認する。"""
    if stats is None:
        stats = _LandedReferenceStats()
    stats.match_keys = len(matches)
    pattern_owners, stats.external_matches, stats.generated_patterns = (
        _build_pattern_owners(matches, progress=progress)
    )
    stats.patterns = len(pattern_owners)
    if not pattern_owners:
        return {}, None

    grep_roots = sorted(
        {
            str(match.root)
            for external_matches in matches.values()
            for match in external_matches
        }
    )
    # 各 exact pattern は必ず受理済み探索根の文字列で始まるため、根で grep した
    # file 集合は exact pattern で grep した集合の上位集合になる。増えた file は
    # 下流の境界付き exact-pattern 集合照合で落ちるので、最終抑止集合は変わらない。
    batches = _git_grep_pattern_batches(
        repo,
        main_ref,
        grep_roots,
        max_patterns_per_batch=max_patterns_per_batch,
        max_argv_bytes=max_argv_bytes,
    )
    stats.grep_batches = len(batches)
    prefix = os.fsencode(main_ref) + b":"
    matched_tree_paths: list[str] = []
    seen_tree_paths: set[str] = set()
    heartbeat = _ProgressRateLimiter(progress, "landed 参照")
    for batch_index, batch in enumerate(batches, start=1):
        arguments = ["grep", "-F", "-l", "-z"]
        for pattern in batch:
            arguments.extend(("-e", pattern))
        arguments.extend((main_ref, "--"))
        _progress(
            progress,
            f"landed 参照 heartbeat grep_batches="
            f"{batch_index}/{len(batches)} phase=start",
        )
        grep_result = _git_bytes(repo, *arguments)
        _progress(
            progress,
            f"landed 参照 heartbeat grep_batches="
            f"{batch_index}/{len(batches)} phase=complete "
            f"rc={grep_result.returncode}",
        )
        if grep_result.returncode == 1:
            continue
        if grep_result.returncode != 0:
            stderr_detail = grep_result.stderr.decode(
                "utf-8", errors="replace"
            ).strip()
            stdout_detail = grep_result.stdout.decode(
                "utf-8", errors="replace"
            ).strip()
            return {}, (
                f"git grep batch {batch_index}/{len(batches)} "
                f"rc={grep_result.returncode}: "
                f"stderr={stderr_detail!r}; stdout={stdout_detail!r}"
            )
        for record in grep_result.stdout.split(b"\0"):
            if not record:
                continue
            if not record.startswith(prefix):
                return {}, "git grep の path 出力を解釈できない"
            tree_path = os.fsdecode(record[len(prefix) :])
            if tree_path not in seen_tree_paths:
                seen_tree_paths.add(tree_path)
                matched_tree_paths.append(tree_path)

    if not matched_tree_paths:
        return {}, None

    tree_metadata: dict[str, _BlobMetadata] = {}
    metadata_batches = _ls_tree_path_batches(
        repo, main_ref, matched_tree_paths
    )
    stats.metadata_batches = len(metadata_batches)
    for batch_index, batch in enumerate(metadata_batches, start=1):
        _progress(
            progress,
            f"landed 参照 heartbeat ls_tree_batches="
            f"{batch_index}/{len(metadata_batches)} phase=start",
        )
        completed = _git_ls_tree_batch(repo, main_ref, batch)
        _progress(
            progress,
            f"landed 参照 heartbeat ls_tree_batches="
            f"{batch_index}/{len(metadata_batches)} phase=complete "
            f"rc={completed.returncode}",
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).decode(
                "utf-8", errors="replace"
            ).strip()
            return {}, f"landed file の metadata 確認不能: {detail}"
        try:
            parsed = _parse_ls_tree_batch(main_ref, batch, completed.stdout)
        except (OSError, RuntimeError, UnicodeError) as exc:
            return {}, f"landed file の metadata 確認不能: {exc}"
        if set(parsed) != set(batch):
            return {}, "landed file の metadata が欠落した"
        tree_metadata.update(parsed)

    owned_cat_file = cat_file is None
    if cat_file is None:
        cat_file = _CatFileBatch(repo, progress=progress)
    patterns_by_encoded = {
        os.fsencode(pattern): pattern for pattern in pattern_owners
    }
    encoded_roots = {
        os.fsencode(str(match.root))
        for external_matches in matches.values()
        for match in external_matches
    }
    matched_patterns: set[str] = set()
    unmatched_patterns = set(patterns_by_encoded)
    metadata_by_oid: dict[str, _BlobMetadata] = {}
    for metadata in tree_metadata.values():
        metadata_by_oid.setdefault(metadata.object_id, metadata)
    scanned_bytes = 0

    def report_scan_progress(count: int) -> None:
        nonlocal scanned_bytes
        scanned_bytes += count
        heartbeat.pulse(
            f"scanned_bytes={scanned_bytes} contents={stats.contents_read}"
        )

    try:
        for object_id in sorted(metadata_by_oid):
            metadata = metadata_by_oid[object_id]
            content = cat_file.read_blob(object_id, metadata.size)
            stats.contents_read += 1
            stats.bytes_read += len(content)
            heartbeat.pulse(
                f"contents={stats.contents_read}/{len(metadata_by_oid)} "
                f"bytes_read={stats.bytes_read}"
            )
            found = _bounded_path_reference_matches(
                content,
                unmatched_patterns,
                encoded_roots,
                heartbeat=report_scan_progress,
            )
            unmatched_patterns.difference_update(found)
            matched_patterns.update(
                patterns_by_encoded[pattern] for pattern in found
            )
    except (OSError, RuntimeError) as exc:
        if owned_cat_file:
            cat_file.close()
        return {}, f"landed file の参照確認不能: {exc}"

    if owned_cat_file:
        close_failure = cat_file.close()
        if close_failure is not None:
            return {}, f"landed file の参照確認不能: {close_failure}"

    referenced: dict[tuple[str, str], list[Path]] = {}
    referenced_seen: dict[tuple[str, str], set[Path]] = {}
    for pattern in matched_patterns:
        for key, external_path in pattern_owners[pattern]:
            paths = referenced.setdefault(key, [])
            seen = referenced_seen.setdefault(key, set())
            if external_path not in seen:
                seen.add(external_path)
                paths.append(external_path)
    for paths in referenced.values():
        paths.sort(key=str)
    return referenced, None


def _stage_complete(
    progress: ProgressCallback | None,
    stage: str,
    started: float,
    detail: str = "",
) -> None:
    suffix = f" {detail}" if detail else ""
    _progress(
        progress,
        f"{stage} 完了 elapsed_seconds={time.monotonic() - started:.3f}{suffix}",
    )


def _audit_snapshot(
    root: Path,
    main_commit: str,
    excluded_prefixes: tuple[str, ...],
    regenerable_prefixes: tuple[str, ...],
    *,
    progress: ProgressCallback | None = None,
) -> _CoreAudit:
    stage_started = time.monotonic()
    _progress(progress, "fsck 開始")
    unreachable = unreachable_commits(root, progress=progress)
    _stage_complete(progress, "fsck", stage_started, f"commits={len(unreachable)}")

    stage_started = time.monotonic()
    _progress(progress, "bulk log 開始")
    records = bulk_commit_records(root, unreachable)
    changed_pairs = sum(len(record.paths) for record in records.values())
    _stage_complete(
        progress,
        "bulk log",
        stage_started,
        f"commits={len(records)} changed_pairs={changed_pairs}",
    )

    stage_started = time.monotonic()
    _progress(progress, "main・tip tree 開始")
    main_paths = tree_paths(root, main_commit)
    other_tip_paths: set[str] = set()
    tips = branch_tip_commits(root)
    for tip in tips:
        if tip != main_commit:
            other_tip_paths.update(tree_paths(root, tip))

    findings: list[Finding] = []
    regenerable_excluded_pairs = 0
    regenerable_only: list[RegenerableOnlyCommit] = []
    for commit in sorted(records):
        record = records[commit]
        lost_paths: list[str] = []
        excluded_regenerable: list[str] = []
        lost_regenerable: list[str] = []
        for path in record.paths:
            if any(path.startswith(prefix) for prefix in excluded_prefixes):
                continue
            if any(path.startswith(prefix) for prefix in regenerable_prefixes):
                excluded_regenerable.append(path)
                if path not in main_paths and path not in other_tip_paths:
                    lost_regenerable.append(path)
                continue
            if path in main_paths or path in other_tip_paths:
                continue
            lost_paths.append(path)
        regenerable_excluded_pairs += len(excluded_regenerable)
        if lost_paths:
            findings.append((commit, record.subject, lost_paths))
        elif lost_regenerable:
            regenerable_only.append(
                (commit, record.subject, len(excluded_regenerable))
            )
    finding_pairs = sum(len(paths) for _commit, _subject, paths in findings)
    _stage_complete(
        progress,
        "main・tip tree",
        stage_started,
        f"tips={len(tips)} finding_commits={len(findings)} "
        f"finding_pairs={finding_pairs}",
    )
    return _CoreAudit(
        findings=findings,
        regenerable_excluded_pairs=regenerable_excluded_pairs,
        regenerable_only_commits=tuple(regenerable_only),
    )


def audit(
    repo: Path | str,
    main_ref: str = "main",
    excluded_prefixes: tuple[str, ...] = DEFAULT_EXCLUDED_PREFIXES,
    regenerable_prefixes: tuple[str, ...] = DEFAULT_REGENERABLE_PREFIXES,
    *,
    progress: ProgressCallback | None = None,
) -> list[Finding]:
    """3 条件をすべて満たす commit と、その失われた path を返す。"""
    stage_started = time.monotonic()
    _progress(progress, "root 検証 開始")
    root = Path(repo).resolve()
    main_commit = _checked_git(
        root, "rev-parse", "--verify", f"{main_ref}^{{commit}}"
    ).strip()
    _stage_complete(progress, "root 検証", stage_started)
    return _audit_snapshot(
        root,
        main_commit,
        excluded_prefixes,
        regenerable_prefixes,
        progress=progress,
    ).findings


def audit_with_offrepo(
    repo: Path | str,
    main_ref: str = "main",
    excluded_prefixes: tuple[str, ...] = DEFAULT_EXCLUDED_PREFIXES,
    *,
    regenerable_prefixes: tuple[str, ...] = DEFAULT_REGENERABLE_PREFIXES,
    offrepo_roots: Sequence[Path | str] = (),
    offrepo_scan: str | None = None,
    progress: ProgressCallback | None = None,
) -> AuditReport:
    """既存 findings に repo 外の同一実体による抑止を後段適用する。"""
    if offrepo_scan not in (None, "off", "full"):
        raise RuntimeError(f"未知の repo 外走査 mode: {offrepo_scan}")
    if offrepo_scan == "full" and not offrepo_roots:
        raise RuntimeError(
            "--offrepo-scan full には --offrepo-root または "
            "IZANAGI_DEV_WAVE_JOBS_DIR が必要です"
        )
    stage_started = time.monotonic()
    _progress(progress, "root 検証 開始")
    root = Path(repo).resolve()
    main_commit = _checked_git(
        root, "rev-parse", "--verify", f"{main_ref}^{{commit}}"
    ).strip()
    if offrepo_scan == "off":
        requested = accepted = rejected = ()
    else:
        requested, accepted, rejected = _validate_offrepo_roots(
            root, offrepo_roots, worktree=root
        )
    _stage_complete(
        progress,
        "root 検証",
        stage_started,
        f"requested={len(requested)} accepted={len(accepted)}",
    )
    core = _audit_snapshot(
        root,
        main_commit,
        excluded_prefixes,
        regenerable_prefixes,
        progress=progress,
    )
    original_findings = core.findings
    if offrepo_scan == "off" or not requested or not accepted:
        now = time.monotonic()
        _progress(progress, "blob metadata 開始")
        _stage_complete(progress, "blob metadata", now, "candidates=0")
        now = time.monotonic()
        _progress(progress, "repo 外走査の列挙 開始")
        _stage_complete(progress, "repo 外走査の列挙", now, "scan_performed=false")
        now = time.monotonic()
        _progress(progress, "候補比較 開始")
        _stage_complete(
            progress,
            "候補比較",
            now,
            "candidate_oids=0 matched_keys=0 external_files=0 "
            "external_matches=0 max_matches_per_key=0",
        )
        now = time.monotonic()
        _progress(progress, "landed 参照 開始")
        _stage_complete(
            progress,
            "landed 参照",
            now,
            "matches=0 match_keys=0 external_matches=0 patterns=0 "
            "generated_patterns=0 grep_batches=0 metadata_batches=0 "
            "contents_read=0 bytes_read=0",
        )
        now = time.monotonic()
        _progress(progress, "抑止集約 開始")
        _stage_complete(progress, "抑止集約", now, "suppressions=0")
        return AuditReport(
            findings=original_findings,
            suppressions=[],
            unreferenced_copies=[],
            requested_roots=requested,
            accepted_roots=accepted,
            rejected_roots=rejected,
            scan_performed=False,
            blob_failures=0,
            scan_failures=0,
            oversize_blobs=(),
            reference_failure=None,
            regenerable_excluded_pairs=core.regenerable_excluded_pairs,
            regenerable_only_commits=core.regenerable_only_commits,
            offrepo_scan="off" if offrepo_scan == "off" else "full",
        )

    stage_started = time.monotonic()
    _progress(progress, "blob metadata 開始")
    candidates, metadata_failures, oversize = _load_blob_metadata(
        root, original_findings
    )
    _stage_complete(
        progress,
        "blob metadata",
        stage_started,
        f"candidates={len(candidates)} failures={metadata_failures}",
    )

    stage_started = time.monotonic()
    _progress(progress, "repo 外走査の列挙 開始")
    possible, scan_failures, scan_performed = _enumerate_offrepo_candidates(
        accepted, candidates, progress=progress
    )
    _stage_complete(
        progress,
        "repo 外走査の列挙",
        stage_started,
        f"candidate_oids={len(possible)} scan_performed={str(scan_performed).lower()}",
    )

    cat_file: _CatFileBatch | None = None
    matches: dict[tuple[str, str], list[_ExternalMatch]] = {}
    referenced: dict[tuple[str, str], list[Path]] = {}
    reference_failure: str | None = None
    blob_failed_keys: set[tuple[str, str]] = set()
    stage_started = time.monotonic()
    _progress(progress, "候補比較 開始")
    session_keys = {
        owner
        for groups in possible.values()
        for group in groups.values()
        for owner in group.owners
    }
    if possible:
        cat_file = _CatFileBatch(root, progress=progress)
        matches, failed_keys, comparison_failures = _compare_offrepo_candidates(
            cat_file, possible, progress=progress
        )
        blob_failed_keys.update(failed_keys)
        scan_failures += comparison_failures
    external_matches = sum(
        len(external_matches) for external_matches in matches.values()
    )
    external_files = len(
        {
            match.path
            for matched_external in matches.values()
            for match in matched_external
        }
    )
    max_matches_per_key = max(
        (len(external_matches) for external_matches in matches.values()),
        default=0,
    )
    _stage_complete(
        progress,
        "候補比較",
        stage_started,
        f"candidate_oids={len(possible)} matched_keys={len(matches)} "
        f"external_files={external_files} "
        f"external_matches={external_matches} "
        f"max_matches_per_key={max_matches_per_key}",
    )

    stage_started = time.monotonic()
    _progress(progress, "landed 参照 開始")
    landed_stats = _LandedReferenceStats()
    if matches:
        referenced, reference_failure = _landed_reference_matches(
            root,
            main_commit,
            matches,
            cat_file=cat_file,
            progress=progress,
            stats=landed_stats,
        )
    if cat_file is not None:
        close_failure = cat_file.close()
        if close_failure is not None:
            blob_failed_keys.update(session_keys)
            matches = {}
            referenced = {}
            reference_failure = f"cat-file --batch 終了確認不能: {close_failure}"
    _stage_complete(
        progress,
        "landed 参照",
        stage_started,
        f"matches={len(referenced)} match_keys={landed_stats.match_keys} "
        f"external_matches={landed_stats.external_matches} "
        f"patterns={landed_stats.patterns} "
        f"generated_patterns={landed_stats.generated_patterns} "
        f"grep_batches={landed_stats.grep_batches} "
        f"metadata_batches={landed_stats.metadata_batches} "
        f"contents_read={landed_stats.contents_read} "
        f"bytes_read={landed_stats.bytes_read}",
    )

    stage_started = time.monotonic()
    _progress(progress, "抑止集約 開始")
    suppressions: list[Suppression] = []
    unreferenced: list[ExternalCopy] = []
    remaining: list[Finding] = []
    for commit, subject, paths in original_findings:
        remaining_paths: list[str] = []
        for path in paths:
            key = (commit, path)
            referenced_paths = referenced.get(key, ()) if reference_failure is None else ()
            if referenced_paths:
                suppressions.append((commit, path, referenced_paths[0]))
                continue
            remaining_paths.append(path)
            if reference_failure is None and matches.get(key):
                unreferenced.append((commit, path, matches[key][0].path))
        if remaining_paths:
            remaining.append((commit, subject, remaining_paths))
    _stage_complete(
        progress,
        "抑止集約",
        stage_started,
        f"suppressions={len(suppressions)} findings={len(remaining)}",
    )

    return AuditReport(
        findings=remaining,
        suppressions=suppressions,
        unreferenced_copies=unreferenced,
        requested_roots=requested,
        accepted_roots=accepted,
        rejected_roots=rejected,
        scan_performed=scan_performed,
        blob_failures=metadata_failures + len(blob_failed_keys),
        scan_failures=scan_failures,
        oversize_blobs=oversize,
        reference_failure=reference_failure,
        regenerable_excluded_pairs=core.regenerable_excluded_pairs,
        regenerable_only_commits=core.regenerable_only_commits,
    )


def _print_offrepo_report(report: AuditReport) -> None:
    if report.offrepo_scan == "off":
        print(
            "audit_dangling_commits: repo 外走査は明示 off"
            f"（{OFFREPO_ROOT_ENV} の指定も無視）；repo 外の同一実体は未確認のため、"
            "findings は full なら抑止されうる (commit, path) 対を含みうる。"
            "救出 triage は --offrepo-scan full --offrepo-root <root> を指定して単独実行する"
        )
    elif not report.requested_roots:
        print("audit_dangling_commits: repo 外の同一実体の探索を未実施")
        print(f"  --offrepo-root / {OFFREPO_ROOT_ENV} が未指定")
    else:
        print(
            "audit_dangling_commits: repo 外の同一実体の探索根 "
            f"{len(report.requested_roots)} 件"
        )
        for root in report.accepted_roots:
            print(f"  探索根: {root}")
        for root, reason in report.rejected_roots:
            print(f"  探索根を拒否 (抑止せず): {root} ({reason})")
        if report.accepted_roots and not report.scan_performed:
            print("  照合可能な候補 basename 0 件のため走査省略")
    for commit, path, size in report.oversize_blobs:
        print(
            f"  oversize (抑止せず): commit {commit}: {path} "
            f"({size} bytes; 上限 {MAX_BLOB_SIZE} bytes)"
        )
    if report.blob_failures:
        print(f"  blob 確認不能 {report.blob_failures} 件 (抑止せず)")
    if report.scan_failures:
        print(f"  repo 外候補の確認不能 {report.scan_failures} 件 (抑止せず)")
    if report.reference_failure is not None:
        print(f"  landed 参照確認不能 (抑止せず): {report.reference_failure}")

    print(
        "audit_dangling_commits: repo 外の同一実体で抑止 "
        f"{len(report.suppressions)} (commit, path) 対"
    )
    for commit, path, external_copy_path in report.suppressions:
        print(f"  commit {commit}: {path}")
        print(f"    repo 外の同一実体: {external_copy_path}")


def _print_regenerable_exclusions(report: AuditReport) -> None:
    print(
        "audit_dangling_commits: 再生成可能物として除外 "
        f"{report.regenerable_excluded_pairs} (commit, path) 対"
    )
    for commit, subject, path_count in report.regenerable_only_commits:
        print(
            "  派生物のみのため詳細監査を省略: "
            f"commit {commit} ({subject}) — 除外 path {path_count} 件"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="要確認の到達不能変更を検出する",
        epilog=(
            f"所要上限: {AUDIT_ELAPSED_LIMIT_SECONDS:.3f} 秒。"
            "超過は stdout へ開示するが rc には混ぜない。\n"
            f"{LIMITATION_NOTICE}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=DEFAULT_REPO,
        help=f"対象 repo (既定: {DEFAULT_REPO})",
    )
    parser.add_argument("--ref", default="main", help="取り込み先 ref (既定: main)")
    parser.add_argument(
        "--offrepo-scan",
        choices=("off", "full"),
        default=None,
        help="repo 外走査: off は環境変数の探索根も無視、full は探索根必須",
    )
    parser.add_argument(
        "--offrepo-root",
        type=Path,
        action="append",
        default=None,
        metavar="PATH",
        help=(
            "repo 外の同一実体の探索根。複数指定可。指定時は "
            f"{OFFREPO_ROOT_ENV} を完全に上書きする"
        ),
    )
    parser.add_argument(
        "--include-fold-trees",
        action="store_true",
        help="docs/spool/ と docs/archive/ も判定対象に含める",
    )
    parser.add_argument(
        "--include-regenerable-artifacts",
        action="store_true",
        help=(
            "再生成可能物 output/s8b-build-cache/ を検証用に監査へ戻す"
        ),
    )
    args = parser.parse_args(argv)
    if args.offrepo_scan == "off" and args.offrepo_root is not None:
        parser.error("--offrepo-scan off と --offrepo-root は併用できません")

    excluded = () if args.include_fold_trees else DEFAULT_EXCLUDED_PREFIXES
    regenerable = (
        ()
        if args.include_regenerable_artifacts
        else DEFAULT_REGENERABLE_PREFIXES
    )
    roots: Sequence[Path | str]
    if args.offrepo_scan == "off":
        roots = ()
    elif args.offrepo_root is not None:
        roots = tuple(args.offrepo_root)
    else:
        environment_root = os.environ.get(OFFREPO_ROOT_ENV, "")
        roots = (environment_root,) if environment_root else ()
    started = time.monotonic()
    return_code = 2

    def report_progress(message: str) -> None:
        print(f"audit_dangling_commits: 進捗 {message}", flush=True)

    try:
        report = audit_with_offrepo(
            args.repo,
            args.ref,
            excluded,
            regenerable_prefixes=regenerable,
            offrepo_roots=roots,
            offrepo_scan=args.offrepo_scan,
            progress=report_progress,
        )
    except (OSError, RuntimeError, UnicodeError) as exc:
        report_started = time.perf_counter()
        report_progress("最終報告 開始")
        print(f"audit_dangling_commits: 実行できません: {exc}", file=sys.stderr)
        report_progress(
            "最終報告 完了 elapsed_seconds="
            f"{time.perf_counter() - report_started:.3f}"
        )
    else:
        report_started = time.perf_counter()
        report_progress("最終報告 開始")
        _print_regenerable_exclusions(report)
        _print_offrepo_report(report)
        if not report.findings:
            print(f"audit_dangling_commits: 要確認 0 件 ({LIMITATION_NOTICE})")
            return_code = 0
        else:
            notes = {
                (commit, path): external_copy_path
                for commit, path, external_copy_path in report.unreferenced_copies
            }
            print(
                "audit_dangling_commits: 要確認の到達不能変更 "
                f"{len(report.findings)} commit"
            )
            for commit, subject, paths in report.findings:
                print(f"  commit {commit} ({subject})")
                for path in paths:
                    external_copy_path = notes.get((commit, path))
                    note = ""
                    if external_copy_path is not None:
                        note = (
                            " — repo 外に同一 bytes の実体あり "
                            f"(landed 参照なし): {external_copy_path}"
                        )
                    print(f"    main・全 local branch tip に不在: {path}{note}")
            return_code = 1
        report_progress(
            "最終報告 完了 elapsed_seconds="
            f"{time.perf_counter() - report_started:.3f}"
        )
    finally:
        elapsed = time.monotonic() - started
        if elapsed > AUDIT_ELAPSED_LIMIT_SECONDS:
            print(
                "audit_dangling_commits: 所要上限超過 "
                f"elapsed_seconds={elapsed:.3f} "
                f"limit_seconds={AUDIT_ELAPSED_LIMIT_SECONDS:.3f}"
            )
        print(f"audit_dangling_commits: elapsed_seconds={elapsed:.3f}")
    return return_code


if __name__ == "__main__":
    sys.exit(main())
