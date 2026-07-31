#!/usr/bin/env python3
"""監査済み dev-wave tip を local main へ一度だけ fast-forward する。

この helper は協調する dev-wave manager 間の事故防止用であり、同一 UID の
非協調 writer や悪意ある Git admin 改変に対する sandbox ではない。caller が渡す
tested SHA / audited commit 列を受入証明とはみなさず、観測後の stale/race を防ぐ
operation guard として exact に再検査する。
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


RC_OK = 0
RC_STALE_MAIN = 10
RC_LOCK_BUSY = 11
RC_DIRT = 20
RC_CONTROL_PLANE = 21
RC_IDENTITY = 22
RC_AUDIT = 23
RC_NOT_LANDED = 24
RC_LANDED_POSTCONDITION_FAILED = 25

_GIT_EXE = "/usr/bin/git"
_LOCK_NAME = b"dev-wave-land.lock"
_MAX_METADATA_BYTES = 16 * 1024
_MAX_HANDOFF_BYTES = 2 * 1024 * 1024
_SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_SAFE_ADMIN_RE = re.compile(rb"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SAFE_CHILD_RE = re.compile(rb"(?!\.{1,2}\Z)[^/\x00]{1,128}\Z")
_SAFE_HANDOFF_RE = re.compile(
    rb"[0-9A-Za-z][0-9A-Za-z._-]{0,191}\.md\Z"
)
_HANDOFF_STATES = {"作業中", "計測中", "中断"}
_CONTROL_CONTAINERS = (b".claude/worktrees", b".codex/worktrees")
_GIT_CONFIG = (
    "-c", "core.hooksPath=/dev/null",
    "-c", "core.fsmonitor=false",
    "-c", "core.useBuiltinFSMonitor=false",
    "-c", "merge.autoStash=false",
    "-c", "rebase.autoStash=false",
    "-c", "merge.verifySignatures=false",
    "-c", "maintenance.auto=false",
    "-c", "gc.auto=0",
    "-c", "fetch.writeCommitGraph=false",
    "-c", "submodule.recurse=false",
    "-c", "protocol.file.allow=never",
)


@dataclass(frozen=True)
class LandRequest:
    main_worktree: Path
    wave_worktree: Path
    tested_main_sha: str
    tested_wave_tip_sha: str
    audited_commits: tuple[str, ...]


@dataclass(frozen=True)
class LandResult:
    rc: int
    status: str
    reason: str
    main_before: str | None = None
    main_after: str | None = None
    wave_tip: str | None = None

    def as_json(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "main_before": self.main_before,
            "main_after": self.main_after,
            "wave_tip": self.wave_tip,
        }


class _Reject(Exception):
    def __init__(self, rc: int, reason: str):
        super().__init__(reason)
        self.rc = rc
        self.reason = reason


@dataclass
class _Repository:
    main: Path
    wave: Path
    common: Path
    main_fd: int
    wave_fd: int
    common_fd: int

    def close(self) -> None:
        for fd in (self.common_fd, self.wave_fd, self.main_fd):
            try:
                os.close(fd)
            except OSError:
                pass


@dataclass(frozen=True)
class _GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class _ControlSnapshot:
    handoffs: frozenset[bytes]
    worktree_prefixes: tuple[bytes, ...]
    identities: tuple[tuple[bytes, tuple[object, ...]], ...]


def _git_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C",
    })
    return env


def _git(repo: Path, *args: str, pass_fds: tuple[int, ...] = ()) -> _GitResult:
    try:
        completed = subprocess.run(
            [_GIT_EXE, *_GIT_CONFIG, "-C", str(repo), *args],
            env=_git_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            close_fds=True,
            pass_fds=pass_fds,
        )
    except OSError as exc:
        return _GitResult(127, b"", str(exc).encode("utf-8", "replace"))
    return _GitResult(completed.returncode, completed.stdout, completed.stderr)


def _detail(data: bytes) -> str:
    return data.decode("utf-8", "backslashreplace").strip().replace("\n", " ")[:500]


def _require_git(result: _GitResult, label: str, rc: int = RC_AUDIT) -> bytes:
    if result.returncode != 0:
        raise _Reject(rc, f"{label}: git failed ({_detail(result.stderr) or 'no detail'})")
    return result.stdout


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        stat.S_IFMT(left.st_mode),
    ) == (
        right.st_dev,
        right.st_ino,
        stat.S_IFMT(right.st_mode),
    )


def _identity(metadata: os.stat_result) -> tuple[int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
    )


def _open_dir(path: Path, label: str) -> int:
    raw = os.fsencode(path)
    try:
        before = os.lstat(raw)
        fd = os.open(raw, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        after = os.fstat(fd)
    except OSError as exc:
        raise _Reject(RC_IDENTITY, f"{label}: directory open failed ({exc})") from exc
    if not stat.S_ISDIR(after.st_mode) or not _same_inode(before, after):
        os.close(fd)
        raise _Reject(RC_IDENTITY, f"{label}: symlink/race/non-directory")
    return fd


def _openat_dir(parent_fd: int, name: bytes, label: str, *, rc: int) -> int:
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        fd = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
        after = os.fstat(fd)
    except OSError as exc:
        raise _Reject(rc, f"{label}: directory open failed ({exc})") from exc
    if not stat.S_ISDIR(after.st_mode) or not _same_inode(before, after):
        os.close(fd)
        raise _Reject(rc, f"{label}: symlink/race/non-directory")
    return fd


def _read_regular_at(
    parent_fd: int,
    name: bytes,
    label: str,
    *,
    rc: int,
    limit: int = _MAX_METADATA_BYTES,
    require_one_link: bool = False,
) -> tuple[bytes, os.stat_result]:
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        fd = os.open(
            name,
            os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise _Reject(rc, f"{label}: regular file open failed ({exc})") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or not _same_inode(before, opened):
            raise _Reject(rc, f"{label}: symlink/race/non-regular")
        if require_one_link and opened.st_nlink != 1:
            raise _Reject(rc, f"{label}: hard-linked handoff is unsupported")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise _Reject(rc, f"{label}: file exceeds {limit} bytes")
        after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        final = os.fstat(fd)
        if not _same_inode(opened, after) or not _same_inode(opened, final):
            raise _Reject(rc, f"{label}: inode changed while reading")
        return b"".join(chunks), opened
    finally:
        os.close(fd)


def _canonical_absolute(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise _Reject(RC_IDENTITY, f"{label}: path must be absolute")
    raw = os.fsencode(path)
    if b"\0" in raw or b"\n" in raw or os.path.normpath(raw) != raw:
        raise _Reject(RC_IDENTITY, f"{label}: path is not canonical")
    try:
        resolved = Path(os.fsdecode(os.path.realpath(raw, strict=True)))
    except OSError as exc:
        raise _Reject(RC_IDENTITY, f"{label}: path resolution failed ({exc})") from exc
    if os.fsencode(resolved) != raw:
        raise _Reject(RC_IDENTITY, f"{label}: symlinked or aliased path is unsupported")
    return resolved


def _parse_gitdir_file(data: bytes, label: str) -> bytes:
    prefix = b"gitdir: "
    if not data.startswith(prefix) or not data.endswith(b"\n"):
        raise _Reject(RC_IDENTITY, f"{label}: malformed gitdir file")
    target = data[len(prefix):-1]
    if (
        not target.startswith(b"/")
        or b"\0" in target
        or b"\n" in target
        or os.path.normpath(target) != target
    ):
        raise _Reject(RC_IDENTITY, f"{label}: gitdir target must be canonical absolute bytes")
    return target


def _validate_admin_binding(
    *,
    child_fd: int,
    child_path: bytes,
    common_fd: int,
    common_path: bytes,
    label: str,
    rc: int,
) -> tuple[object, ...]:
    child_identity = _identity(os.fstat(child_fd))
    dotgit, dotgit_stat = _read_regular_at(
        child_fd, b".git", f"{label}/.git", rc=rc
    )
    admin_path = _parse_gitdir_file(dotgit, f"{label}/.git")
    expected_prefix = common_path + b"/worktrees/"
    if not admin_path.startswith(expected_prefix):
        raise _Reject(rc, f"{label}: gitdir is outside common worktrees registry")
    admin_name = admin_path[len(expected_prefix):]
    if not _SAFE_ADMIN_RE.fullmatch(admin_name) or b"/" in admin_name:
        raise _Reject(rc, f"{label}: unsafe or nested admin name")

    worktrees_fd = _openat_dir(
        common_fd, b"worktrees", "common/worktrees", rc=rc
    )
    try:
        admin_fd = _openat_dir(
            worktrees_fd, admin_name, f"common/worktrees/{admin_name!r}", rc=rc
        )
    finally:
        os.close(worktrees_fd)
    try:
        try:
            path_stat = os.stat(admin_path, follow_symlinks=False)
        except OSError as exc:
            raise _Reject(rc, f"{label}: admin path stat failed ({exc})") from exc
        if not _same_inode(path_stat, os.fstat(admin_fd)):
            raise _Reject(rc, f"{label}: admin pathname/inode mismatch")
        admin_identity = _identity(os.fstat(admin_fd))
        backpointer, backpointer_stat = _read_regular_at(
            admin_fd, b"gitdir", f"{label} admin gitdir", rc=rc
        )
        if backpointer != child_path + b"/.git\n":
            raise _Reject(rc, f"{label}: admin gitdir backpointer mismatch")
        commondir, commondir_stat = _read_regular_at(
            admin_fd, b"commondir", f"{label} admin commondir", rc=rc
        )
        if commondir != b"../..\n":
            raise _Reject(rc, f"{label}: unsupported common-dir metadata")
        return (
            child_identity,
            _identity(dotgit_stat),
            hashlib.sha256(dotgit).digest(),
            admin_identity,
            _identity(backpointer_stat),
            hashlib.sha256(backpointer).digest(),
            _identity(commondir_stat),
            hashlib.sha256(commondir).digest(),
        )
    finally:
        os.close(admin_fd)


def _verify_repository(request: LandRequest) -> _Repository:
    main = _canonical_absolute(request.main_worktree, "main worktree")
    wave = _canonical_absolute(request.wave_worktree, "wave worktree")
    if main == wave:
        raise _Reject(RC_IDENTITY, "main and wave worktrees must differ")
    main_fd = _open_dir(main, "main worktree")
    try:
        wave_fd = _open_dir(wave, "wave worktree")
    except Exception:
        os.close(main_fd)
        raise
    common_fd = -1
    try:
        cwd = os.stat(b".", follow_symlinks=False)
        if not _same_inode(cwd, os.fstat(wave_fd)):
            raise _Reject(RC_IDENTITY, "cwd must be the exact wave worktree")

        wave_dotgit, _ = _read_regular_at(
            wave_fd, b".git", "wave .git", rc=RC_IDENTITY
        )
        admin_path = _parse_gitdir_file(wave_dotgit, "wave .git")
        if not admin_path.endswith(b"/worktrees/" + admin_path.rsplit(b"/", 1)[-1]):
            raise _Reject(RC_IDENTITY, "wave admin path is not a direct registry child")
        common_path = admin_path.rsplit(b"/worktrees/", 1)[0]
        if common_path.rsplit(b"/", 1)[-1] != b".git":
            raise _Reject(RC_IDENTITY, "common git-dir is not primary .git")
        derived_main = common_path.rsplit(b"/", 1)[0]
        if derived_main != os.fsencode(main):
            raise _Reject(RC_IDENTITY, "main worktree does not own common git-dir")
        common = Path(os.fsdecode(common_path))
        common_fd = _open_dir(common, "common git-dir")
        main_git_fd = _openat_dir(
            main_fd, b".git", "primary main .git", rc=RC_IDENTITY
        )
        try:
            if not _same_inode(os.fstat(main_git_fd), os.fstat(common_fd)):
                raise _Reject(RC_IDENTITY, "primary .git/common git-dir inode mismatch")
        finally:
            os.close(main_git_fd)
        _validate_admin_binding(
            child_fd=wave_fd,
            child_path=os.fsencode(wave),
            common_fd=common_fd,
            common_path=common_path,
            label="wave worktree",
            rc=RC_IDENTITY,
        )
        return _Repository(main, wave, common, main_fd, wave_fd, common_fd)
    except Exception:
        if common_fd >= 0:
            os.close(common_fd)
        os.close(wave_fd)
        os.close(main_fd)
        raise


def _sha(value: str, label: str) -> str:
    if _SHA_RE.fullmatch(value) is None:
        raise _Reject(RC_AUDIT, f"{label}: full lowercase object id required")
    return value


def _decode_sha(data: bytes, label: str, rc: int = RC_AUDIT) -> str:
    try:
        value = data.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise _Reject(rc, f"{label}: non-ASCII object id") from exc
    if _SHA_RE.fullmatch(value) is None:
        raise _Reject(rc, f"{label}: unexpected object id {value!r}")
    return value


def _head(repo: Path, label: str) -> str:
    return _decode_sha(
        _require_git(
            _git(repo, "rev-parse", "--verify", "HEAD"),
            f"{label} HEAD",
            RC_IDENTITY,
        ),
        f"{label} HEAD",
        RC_IDENTITY,
    )


def _symbolic_head(repo: Path, label: str) -> str:
    raw = _require_git(
        _git(repo, "symbolic-ref", "--quiet", "HEAD"),
        f"{label} symbolic HEAD",
        RC_IDENTITY,
    )
    try:
        ref = raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise _Reject(RC_IDENTITY, f"{label}: non-ASCII branch ref") from exc
    if (
        not ref.startswith("refs/heads/")
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in ref)
        or ".." in ref
        or "@{" in ref
        or ref.endswith(("/", "."))
    ):
        raise _Reject(RC_IDENTITY, f"{label}: unsafe branch ref")
    return ref


def _ref_sha(repo: Path, ref: str, label: str) -> str:
    return _decode_sha(
        _require_git(
            _git(repo, "rev-parse", "--verify", ref),
            label,
            RC_IDENTITY,
        ),
        label,
        RC_IDENTITY,
    )


def _verify_heads(repository: _Repository, tested_tip: str) -> tuple[str, str]:
    main_ref = _symbolic_head(repository.main, "main")
    if main_ref != "refs/heads/main":
        raise _Reject(RC_IDENTITY, "primary worktree HEAD must be refs/heads/main")
    main_head = _head(repository.main, "main")
    if _ref_sha(repository.main, main_ref, "main branch") != main_head:
        raise _Reject(RC_IDENTITY, "main HEAD/ref mismatch")

    wave_ref = _symbolic_head(repository.wave, "wave")
    wave_head = _head(repository.wave, "wave")
    if _ref_sha(repository.wave, wave_ref, "wave branch") != wave_head:
        raise _Reject(RC_IDENTITY, "wave HEAD/ref mismatch")
    if wave_head != tested_tip:
        raise _Reject(RC_AUDIT, "wave HEAD/ref moved from tested wave tip")
    return main_head, wave_ref


def _verify_history_modifiers(repository: _Repository) -> None:
    for relative, label in (
        (b"shallow", "shallow repository"),
        (b"info/grafts", "graft file"),
    ):
        try:
            os.stat(relative, dir_fd=repository.common_fd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise _Reject(RC_AUDIT, f"{label}: cannot inspect ({exc})") from exc
        raise _Reject(RC_AUDIT, f"{label} is unsupported")
    replace = _require_git(
        _git(repository.wave, "for-each-ref", "--format=%(refname)", "refs/replace/"),
        "replace refs",
    )
    if replace.strip():
        raise _Reject(RC_AUDIT, "replace refs are unsupported")


def _verify_effective_config(repository: _Repository) -> None:
    checks = (
        (r"^filter\.", "local filter configuration"),
        (
            r"^(extensions\.partialclone|remote\..*\.promisor|"
            r"remote\..*\.partialclonefilter)$",
            "partial-clone/lazy-fetch configuration",
        ),
    )
    for pattern, label in checks:
        result = _git(
            repository.main,
            "config", "--includes", "--null", "--name-only", "--get-regexp", pattern,
        )
        if result.returncode not in (0, 1):
            raise _Reject(
                RC_AUDIT,
                f"{label}: config inspection failed ({_detail(result.stderr)})",
            )
        if result.returncode == 0 and result.stdout:
            raise _Reject(RC_AUDIT, f"{label} is unsupported")


def _validate_handoff_at(
    handoff_fd: int, name: bytes
) -> tuple[object, ...]:
    if (
        b"/" in name
        or _SAFE_HANDOFF_RE.fullmatch(name) is None
        or name == b"README.md"
    ):
        raise _Reject(RC_CONTROL_PLANE, "handoff must be a safe direct-child .md")
    data, metadata = _read_regular_at(
        handoff_fd,
        name,
        f"handoff {name!r}",
        rc=RC_CONTROL_PLANE,
        limit=_MAX_HANDOFF_BYTES,
        require_one_link=True,
    )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _Reject(RC_CONTROL_PLANE, "handoff is not valid UTF-8") from exc
    lines = text.splitlines()
    if len(lines) < 5 or not lines[0].startswith("# ") or not lines[0][2:].strip():
        raise _Reject(RC_CONTROL_PLANE, "handoff title/header is malformed")
    required_prefixes = ("- 目的: ", "- 状態: ", "- 最終更新: ", "- 基準コミット: ")
    if any(not lines[i + 1].startswith(prefix) for i, prefix in enumerate(required_prefixes)):
        raise _Reject(RC_CONTROL_PLANE, "handoff four-line header is malformed")
    if not lines[1].removeprefix("- 目的: ").strip():
        raise _Reject(RC_CONTROL_PLANE, "handoff purpose is empty")
    state = lines[2].removeprefix("- 状態: ").strip()
    if state not in _HANDOFF_STATES:
        raise _Reject(RC_CONTROL_PLANE, "handoff state is unknown")
    if not lines[3].removeprefix("- 最終更新: ").strip():
        raise _Reject(RC_CONTROL_PLANE, "handoff update time is empty")
    base = lines[4].removeprefix("- 基準コミット: ").strip().split(maxsplit=1)[0]
    if _SHA_RE.fullmatch(base) is None:
        raise _Reject(RC_CONTROL_PLANE, "handoff base commit is not a full SHA")
    headings = [
        line.split("   ", 1)[0].rstrip()
        for line in lines
        if line.startswith("## ")
    ]
    for heading in (
        "## 完了した中間成果",
        "## 未完の作業と次の一手",
        "## 落とし穴・気づき",
    ):
        if headings.count(heading) != 1:
            raise _Reject(RC_CONTROL_PLANE, f"handoff heading missing/duplicate: {heading}")
    return (
        _identity(metadata),
        hashlib.sha256(data).digest(),
    )


def _handoff_snapshot(
    repository: _Repository,
) -> tuple[frozenset[bytes], tuple[tuple[bytes, tuple[object, ...]], ...]]:
    docs_fd = _openat_dir(repository.main_fd, b"docs", "main/docs", rc=RC_CONTROL_PLANE)
    try:
        handoff_fd = _openat_dir(
            docs_fd, b"handoff", "main/docs/handoff", rc=RC_CONTROL_PLANE
        )
    finally:
        os.close(docs_fd)
    try:
        directory_before = os.fstat(handoff_fd)
        try:
            names_before = sorted(os.fsencode(name) for name in os.listdir(handoff_fd))
        except OSError as exc:
            raise _Reject(
                RC_CONTROL_PLANE, f"main/docs/handoff: list failed ({exc})"
            ) from exc
        validated: set[bytes] = set()
        identities: list[tuple[bytes, tuple[object, ...]]] = [
            (b"docs/handoff", _identity(directory_before))
        ]
        for name in names_before:
            if name == b"README.md":
                continue
            relative = b"docs/handoff/" + name
            identities.append((relative, _validate_handoff_at(handoff_fd, name)))
            validated.add(relative)
        try:
            names_after = sorted(os.fsencode(name) for name in os.listdir(handoff_fd))
        except OSError as exc:
            raise _Reject(
                RC_CONTROL_PLANE, f"main/docs/handoff: relist failed ({exc})"
            ) from exc
        if (
            names_after != names_before
            or not _same_inode(directory_before, os.fstat(handoff_fd))
        ):
            raise _Reject(RC_CONTROL_PLANE, "handoff directory changed while validating")
        return frozenset(validated), tuple(identities)
    finally:
        os.close(handoff_fd)


def _open_container(
    repository: _Repository, relative: bytes
) -> tuple[int, bytes] | None:
    first, second = relative.split(b"/", 1)
    try:
        first_fd = _openat_dir(
            repository.main_fd, first, f"main/{first!r}", rc=RC_CONTROL_PLANE
        )
    except _Reject as exc:
        if isinstance(exc.__cause__, FileNotFoundError):
            return None
        raise
    try:
        try:
            second_fd = _openat_dir(
                first_fd, second, f"main/{relative!r}", rc=RC_CONTROL_PLANE
            )
        except _Reject as exc:
            if isinstance(exc.__cause__, FileNotFoundError):
                return None
            raise
    finally:
        os.close(first_fd)
    return second_fd, os.fsencode(repository.main) + b"/" + relative


def _worktree_snapshot(
    repository: _Repository,
) -> tuple[tuple[bytes, ...], tuple[tuple[bytes, tuple[object, ...]], ...]]:
    prefixes: list[bytes] = []
    identities: list[tuple[bytes, tuple[object, ...]]] = []
    common_path = os.fsencode(repository.common)
    for relative in _CONTROL_CONTAINERS:
        opened = _open_container(repository, relative)
        if opened is None:
            identities.append((relative, (None,)))
            continue
        container_fd, container_path = opened
        try:
            container_before = os.fstat(container_fd)
            try:
                names_before = sorted(
                    os.fsencode(name) for name in os.listdir(container_fd)
                )
            except OSError as exc:
                raise _Reject(
                    RC_CONTROL_PLANE,
                    f"container {relative!r}: list failed ({exc})",
                ) from exc
            identities.append((relative, _identity(container_before)))
            for name in names_before:
                if _SAFE_CHILD_RE.fullmatch(name) is None:
                    raise _Reject(RC_CONTROL_PLANE, "unsafe worktree child name")
                child_fd = _openat_dir(
                    container_fd,
                    name,
                    f"container child {relative + b'/' + name!r}",
                    rc=RC_CONTROL_PLANE,
                )
                try:
                    child_path = container_path + b"/" + name
                    binding = _validate_admin_binding(
                        child_fd=child_fd,
                        child_path=child_path,
                        common_fd=repository.common_fd,
                        common_path=common_path,
                        label=f"registered child {relative + b'/' + name!r}",
                        rc=RC_CONTROL_PLANE,
                    )
                finally:
                    os.close(child_fd)
                child_relative = relative + b"/" + name
                identities.append((child_relative, binding))
                prefixes.append(child_relative + b"/")
            try:
                names_after = sorted(
                    os.fsencode(name) for name in os.listdir(container_fd)
                )
            except OSError as exc:
                raise _Reject(
                    RC_CONTROL_PLANE,
                    f"container {relative!r}: relist failed ({exc})",
                ) from exc
            if (
                names_after != names_before
                or not _same_inode(container_before, os.fstat(container_fd))
            ):
                raise _Reject(
                    RC_CONTROL_PLANE,
                    f"container {relative!r} changed while validating",
                )
        finally:
            os.close(container_fd)
    return tuple(prefixes), tuple(identities)


def _control_snapshot(repository: _Repository) -> _ControlSnapshot:
    handoffs, handoff_identities = _handoff_snapshot(repository)
    prefixes, worktree_identities = _worktree_snapshot(repository)
    return _ControlSnapshot(
        handoffs=handoffs,
        worktree_prefixes=prefixes,
        identities=handoff_identities + worktree_identities,
    )


def _status_records(repo: Path, label: str) -> list[bytes]:
    raw = _require_git(
        _git(
            repo,
            "status", "--porcelain=v1", "-z",
            "--untracked-files=all", "--ignore-submodules=none",
        ),
        f"{label} status",
        RC_DIRT,
    )
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise _Reject(RC_DIRT, f"{label} status is not NUL terminated")
    return raw[:-1].split(b"\0")


def _verify_main_clean(
    repository: _Repository,
    collision_paths: Sequence[bytes] | None = None,
) -> _ControlSnapshot:
    before = _control_snapshot(repository)
    records = _status_records(repository.main, "main")
    after = _control_snapshot(repository)
    if before != after:
        raise _Reject(
            RC_CONTROL_PLANE,
            "control-plane identity/binding changed around main status",
        )
    for record in records:
        if not record.startswith(b"?? "):
            raise _Reject(RC_DIRT, "main tracked/index/submodule dirt is forbidden")
        relative = record[3:]
        if relative.startswith(b"docs/handoff/"):
            if relative not in after.handoffs:
                raise _Reject(
                    RC_CONTROL_PLANE,
                    "untracked handoff status is not an exact validated direct child",
                )
            continue
        if any(
            relative == prefix[:-1] or relative.startswith(prefix)
            for prefix in after.worktree_prefixes
        ):
            continue
        if collision_paths is not None and any(
            _paths_overlap(relative, target) for target in collision_paths
        ):
            raise _Reject(
                RC_DIRT,
                f"main untracked path collides with land target: {relative!r}",
            )
    return after


def _verify_wave_clean(repository: _Repository) -> None:
    if _status_records(repository.wave, "wave"):
        raise _Reject(RC_DIRT, "wave worktree must be completely clean")


def _nul_records(raw: bytes, label: str, rc: int) -> list[bytes]:
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise _Reject(rc, f"{label} is not NUL terminated")
    return raw[:-1].split(b"\0")


def _ignored_paths_for_target(
    repository: _Repository, target: bytes
) -> tuple[bytes, ...]:
    raw = _require_git(
        _git(
            repository.main,
            "status", "--porcelain=v1", "-z",
            "--untracked-files=all", "--ignored=matching",
            "--ignore-submodules=none",
            "--", os.fsdecode(target),
        ),
        f"main ignored-path status for {target!r}",
        RC_DIRT,
    )
    return tuple(
        record[3:].rstrip(b"/")
        for record in _nul_records(
            raw, f"main ignored-path status for {target!r}", RC_DIRT
        )
        if record.startswith(b"!! ")
    )


def _target_paths(
    repository: _Repository, current: str, tested_tip: str
) -> tuple[bytes, ...]:
    raw = _require_git(
        _git(
            repository.wave,
            "diff", "--name-only", "-z", "--no-renames", current, tested_tip,
        ),
        "target path closure",
    )
    paths = tuple(_nul_records(raw, "target path closure", RC_AUDIT))
    for path in paths:
        if (
            not path
            or path.startswith(b"/")
            or b"\0" in path
            or any(part in (b"", b".", b"..") for part in path.split(b"/"))
        ):
            raise _Reject(RC_AUDIT, f"unsafe target path: {path!r}")
    return paths


def _paths_overlap(left: bytes, right: bytes) -> bool:
    return (
        left == right
        or left.startswith(right + b"/")
        or right.startswith(left + b"/")
    )


def _existing_ignored_target_or_ancestor(
    repository: _Repository, target: bytes
) -> bytes | None:
    parts = target.split(b"/")
    for index in range(1, len(parts) + 1):
        ancestor = b"/".join(parts[:index])
        try:
            metadata = os.stat(
                ancestor,
                dir_fd=repository.main_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise _Reject(
                RC_DIRT,
                f"target ancestor inspection failed for {ancestor!r} ({exc})",
            ) from exc
        if stat.S_ISDIR(metadata.st_mode) and index < len(parts):
            continue
        ignored = _git(
            repository.main,
            "check-ignore", "--quiet", "--", os.fsdecode(ancestor),
        )
        if ignored.returncode == 0:
            return ancestor
        if ignored.returncode != 1:
            raise _Reject(
                RC_DIRT,
                f"target ancestor ignore inspection failed for {ancestor!r} "
                f"({_detail(ignored.stderr) or 'no detail'})",
            )
        return None
    return None


def _verify_target_collisions(
    repository: _Repository,
    *,
    current: str,
    tested_tip: str,
    control: _ControlSnapshot,
) -> None:
    targets = _target_paths(repository, current, tested_tip)
    protected = tuple(control.handoffs) + _CONTROL_CONTAINERS + tuple(
        prefix[:-1] for prefix in control.worktree_prefixes
    )
    for target in targets:
        if any(_paths_overlap(target, path) for path in protected):
            raise _Reject(
                RC_CONTROL_PLANE,
                f"target collides with validated foreign control-plane path: {target!r}",
            )
        ignored = tuple(
            path
            for path in _ignored_paths_for_target(repository, target)
            if path == target or path.startswith(target + b"/")
        )
        ancestor = _existing_ignored_target_or_ancestor(repository, target)
        if ignored or ancestor is not None:
            collision = ignored[0] if ignored else ancestor
            raise _Reject(
                RC_DIRT,
                f"target collides with an existing ignored path: "
                f"target={target!r}, existing={collision!r}",
            )


def _is_ancestor(repo: Path, older: str, newer: str) -> bool:
    result = _git(repo, "merge-base", "--is-ancestor", older, newer)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise _Reject(
        RC_AUDIT,
        f"ancestry inspection failed ({_detail(result.stderr) or 'no detail'})",
    )


def _verify_audit(
    repository: _Repository,
    tested_main: str,
    tested_tip: str,
    audited: tuple[str, ...],
) -> tuple[str, ...]:
    for index, commit in enumerate(audited):
        _sha(commit, f"audited commit {index}")
    for value, label in (
        (tested_main, "tested main"),
        (tested_tip, "tested wave tip"),
    ):
        resolved = _decode_sha(
            _require_git(
                _git(repository.wave, "rev-parse", "--verify", f"{value}^{{commit}}"),
                label,
            ),
            label,
        )
        if resolved != value:
            raise _Reject(RC_AUDIT, f"{label}: object does not resolve exactly")
    if not _is_ancestor(repository.wave, tested_main, tested_tip):
        raise _Reject(RC_AUDIT, "tested main is not an ancestor of tested wave tip")
    raw = _require_git(
        _git(repository.wave, "rev-list", "--reverse", f"{tested_main}..{tested_tip}"),
        "audited commit closure",
    )
    try:
        actual = tuple(line for line in raw.decode("ascii").splitlines() if line)
    except UnicodeDecodeError as exc:
        raise _Reject(RC_AUDIT, "audited commit closure is non-ASCII") from exc
    if actual != audited:
        raise _Reject(RC_AUDIT, "audited commit sequence is not exact A..T closure")
    return actual


def _gitlink_map(repo: Path, commit: str) -> dict[bytes, str]:
    raw = _require_git(
        _git(repo, "ls-tree", "-r", "-z", commit),
        f"gitlink map at {commit}",
    )
    records = raw[:-1].split(b"\0") if raw.endswith(b"\0") else ([] if not raw else None)
    if records is None:
        raise _Reject(RC_AUDIT, "gitlink map is not NUL terminated")
    gitlinks: dict[bytes, str] = {}
    for record in records:
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.split(b" ", 2)
        except ValueError as exc:
            raise _Reject(RC_AUDIT, "gitlink map record is malformed") from exc
        if mode != b"160000":
            continue
        if object_type != b"commit":
            raise _Reject(RC_AUDIT, "gitlink entry has unexpected object type")
        oid = _decode_sha(object_id + b"\n", "gitlink object")
        if path in gitlinks:
            raise _Reject(RC_AUDIT, "duplicate gitlink path")
        gitlinks[path] = oid
    return gitlinks


def _normal_entry_paths(repo: Path, commit: str) -> frozenset[bytes]:
    raw = _require_git(
        _git(repo, "ls-tree", "-r", "-t", "-z", commit),
        f"normal entry map at {commit}",
    )
    records = raw[:-1].split(b"\0") if raw.endswith(b"\0") else ([] if not raw else None)
    if records is None:
        raise _Reject(RC_AUDIT, "normal entry map is not NUL terminated")
    paths: set[bytes] = set()
    for record in records:
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, _object_id = metadata.split(b" ", 2)
        except ValueError as exc:
            raise _Reject(RC_AUDIT, "normal entry map record is malformed") from exc
        if mode == b"160000":
            continue
        if object_type not in (b"blob", b"tree"):
            raise _Reject(RC_AUDIT, "normal entry has unexpected object type")
        if path in paths:
            raise _Reject(RC_AUDIT, "duplicate normal entry path")
        paths.add(path)
    return frozenset(paths)


def _validate_gitlink_path(relative: bytes) -> None:
    if (
        relative.startswith(b"/")
        or any(part in (b"", b".", b"..") for part in relative.split(b"/"))
    ):
        raise _Reject(RC_AUDIT, f"unsafe gitlink path: {relative!r}")


def _removed_gitlinks_absent(
    repository: _Repository,
    base: dict[bytes, str],
    target: dict[bytes, str],
    target_normal_entries: frozenset[bytes],
) -> bool:
    for relative in base.keys() - target.keys():
        _validate_gitlink_path(relative)
        candidates = [(repository.common_fd, b"modules/" + relative)]
        if relative in target_normal_entries:
            candidates.append((repository.main_fd, relative + b"/.git"))
        else:
            candidates.append((repository.main_fd, relative))
        for parent_fd, candidate in candidates:
            try:
                os.stat(candidate, dir_fd=parent_fd, follow_symlinks=False)
            except (FileNotFoundError, NotADirectoryError):
                continue
            except OSError:
                return False
            return False
    return True


def _gitlinks_synchronized(
    repository: _Repository,
    base: dict[bytes, str],
    target: dict[bytes, str],
    target_normal_entries: frozenset[bytes],
) -> bool:
    main_bytes = os.fsencode(repository.main)
    for relative, expected_head in target.items():
        _validate_gitlink_path(relative)
        candidate = repository.main / os.fsdecode(relative)
        try:
            canonical = _canonical_absolute(candidate, f"submodule {relative!r}")
        except _Reject:
            return False
        top = _git(canonical, "rev-parse", "--show-toplevel")
        superproject = _git(
            canonical, "rev-parse", "--show-superproject-working-tree"
        )
        head = _git(canonical, "rev-parse", "--verify", "HEAD")
        if any(result.returncode != 0 for result in (top, superproject, head)):
            return False
        if (
            os.path.normpath(top.stdout.strip()) != os.fsencode(canonical)
            or os.path.normpath(superproject.stdout.strip()) != main_bytes
        ):
            return False
        try:
            actual_head = _decode_sha(head.stdout, f"submodule {relative!r} HEAD")
        except _Reject:
            return False
        if actual_head != expected_head:
            return False
    return _removed_gitlinks_absent(
        repository,
        base,
        target,
        target_normal_entries,
    )


def _main_tracked_or_index_dirty(repository: _Repository) -> bool:
    for args, label in (
        (("diff", "--quiet", "--ignore-submodules=none"), "main worktree diff"),
        (
            ("diff", "--cached", "--quiet", "--ignore-submodules=none"),
            "main index diff",
        ),
    ):
        result = _git(repository.main, *args)
        if result.returncode == 1:
            return True
        if result.returncode != 0:
            raise _Reject(
                RC_LANDED_POSTCONDITION_FAILED,
                f"{label} inspection failed ({_detail(result.stderr) or 'no detail'})",
            )
    return False


def _main_is_allowed(
    repository: _Repository,
    current: str,
    tested_main: str,
    tested_tip: str,
    audited: tuple[str, ...],
) -> bool:
    if current == tested_main:
        return True
    return (
        current in audited
        and _is_ancestor(repository.wave, tested_main, current)
        and _is_ancestor(repository.wave, current, tested_tip)
    )


def _open_lock(repository: _Repository) -> int:
    try:
        fd = os.open(
            _LOCK_NAME,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
            0o600,
            dir_fd=repository.common_fd,
        )
    except OSError as exc:
        raise _Reject(RC_IDENTITY, f"land lock open failed ({exc})") from exc
    metadata = os.fstat(fd)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_nlink != 1
        or metadata.st_mode & 0o022
    ):
        os.close(fd)
        raise _Reject(RC_IDENTITY, "land lock has unsafe metadata")
    return fd


def _postcondition(
    repository: _Repository,
    *,
    tested_tip: str,
    wave_ref: str,
    merge_rc: int,
    main_before: str,
    gitlinks_changed: bool,
) -> LandResult:
    try:
        main_after = _head(repository.main, "main post-land")
    except _Reject as exc:
        return LandResult(
            RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
            f"main HEAD cannot be observed after merge: {exc.reason}",
            main_before,
            None,
            tested_tip,
        )
    if main_after != tested_tip:
        failures: list[str] = []
        if main_after != main_before:
            failures.append("main HEAD changed but did not reach tested tip")
        if merge_rc == 0:
            failures.append("merge reported success without reaching tested tip")
        try:
            if _main_tracked_or_index_dirty(repository):
                failures.append(
                    "merge left tracked/index/worktree changes without reaching tested tip"
                )
            _verify_main_clean(repository)
        except _Reject as exc:
            failures.append(exc.reason)
        if failures:
            return LandResult(
                RC_LANDED_POSTCONDITION_FAILED,
                "landed-postcondition-failed",
                "; ".join(failures),
                main_before,
                main_after,
                tested_tip,
            )
        return LandResult(
            RC_NOT_LANDED,
            "not-landed",
            f"merge rc={merge_rc}; main HEAD did not reach tested tip",
            main_before,
            main_after,
            tested_tip,
        )
    failures: list[str] = []
    if merge_rc != 0:
        failures.append(f"merge returned rc={merge_rc}")
    if gitlinks_changed:
        failures.append(
            "tested range changes gitlinks; D16 post-land submodule synchronization "
            "remains required"
        )
    try:
        if _symbolic_head(repository.main, "main post-land") != "refs/heads/main":
            failures.append("main symbolic HEAD moved")
        if _ref_sha(repository.main, "refs/heads/main", "main post-land ref") != tested_tip:
            failures.append("main ref does not equal tested tip")
        if _head(repository.wave, "wave post-land") != tested_tip:
            failures.append("wave HEAD moved")
        if _symbolic_head(repository.wave, "wave post-land") != wave_ref:
            failures.append("wave symbolic ref moved")
        if _ref_sha(repository.wave, wave_ref, "wave post-land ref") != tested_tip:
            failures.append("wave ref moved")
        _verify_main_clean(repository)
        _verify_wave_clean(repository)
    except _Reject as exc:
        failures.append(exc.reason)
    if failures:
        return LandResult(
            RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
            "; ".join(failures),
            main_before,
            main_after,
            tested_tip,
        )
    return LandResult(
        RC_OK,
        "landed",
        "main fast-forwarded to the tested wave tip",
        main_before,
        main_after,
        tested_tip,
    )


def land(request: LandRequest) -> LandResult:
    repository: _Repository | None = None
    main_before: str | None = None
    tested_tip: str | None = None
    try:
        tested_main = _sha(request.tested_main_sha, "tested main")
        tested_tip = _sha(request.tested_wave_tip_sha, "tested wave tip")
        requested_audit = tuple(
            _sha(commit, f"audited commit {index}")
            for index, commit in enumerate(request.audited_commits)
        )
        repository = _verify_repository(request)
        lock_fd = _open_lock(repository)
        try:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return LandResult(
                    RC_LOCK_BUSY,
                    "lock-busy",
                    "another cooperative land operation holds the common lock",
                    None,
                    None,
                    tested_tip,
                )
            _verify_history_modifiers(repository)
            _verify_effective_config(repository)
            target_paths = _target_paths(repository, tested_main, tested_tip)
            control = _verify_main_clean(
                repository,
                collision_paths=target_paths,
            )
            _verify_wave_clean(repository)
            audited = _verify_audit(
                repository,
                tested_main,
                tested_tip,
                requested_audit,
            )
            base_gitlinks = _gitlink_map(repository.wave, tested_main)
            target_gitlinks = _gitlink_map(repository.wave, tested_tip)
            target_normal_entries = _normal_entry_paths(
                repository.wave,
                tested_tip,
            )
            gitlinks_changed = base_gitlinks != target_gitlinks
            locked_main, wave_ref = _verify_heads(repository, tested_tip)
            main_before = locked_main
            if not _main_is_allowed(
                repository, locked_main, tested_main, tested_tip, audited
            ):
                return LandResult(
                    RC_STALE_MAIN,
                    "stale-main",
                    "main moved outside the tested audited closure while locking",
                    main_before,
                    locked_main,
                    tested_tip,
                )
            if locked_main == tested_tip:
                if gitlinks_changed and not _gitlinks_synchronized(
                    repository,
                    base_gitlinks,
                    target_gitlinks,
                    target_normal_entries,
                ):
                    return LandResult(
                        RC_LANDED_POSTCONDITION_FAILED,
                        "landed-postcondition-failed",
                        "main is at a gitlink-changing tested tip; D16 post-land "
                        "submodule synchronization remains required",
                        main_before,
                        locked_main,
                        tested_tip,
                    )
                return LandResult(
                    RC_OK,
                    "already-landed",
                    "another lander reached the tested tip first",
                    main_before,
                    locked_main,
                    tested_tip,
                )
            _verify_target_collisions(
                repository,
                current=locked_main,
                tested_tip=tested_tip,
                control=control,
            )
            if _control_snapshot(repository) != control:
                raise _Reject(
                    RC_CONTROL_PLANE,
                    "control-plane identity/binding changed before main mutation",
                )
            merge = _git(
                repository.main,
                "merge", "--ff-only", "--no-stat", "--no-progress", tested_tip,
                pass_fds=(lock_fd,),
            )
            return _postcondition(
                repository,
                tested_tip=tested_tip,
                wave_ref=wave_ref,
                merge_rc=merge.returncode,
                main_before=locked_main,
                gitlinks_changed=gitlinks_changed,
            )
        finally:
            os.close(lock_fd)
    except _Reject as exc:
        return LandResult(
            exc.rc,
            "rejected",
            exc.reason,
            main_before,
            main_before,
            tested_tip,
        )
    finally:
        if repository is not None:
            repository.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="tested dev-wave tip を cooperative local main へ ff-only land する"
    )
    parser.add_argument("--main-worktree", type=Path, required=True)
    parser.add_argument("--wave-worktree", type=Path, required=True)
    parser.add_argument("--tested-main-sha", required=True)
    parser.add_argument("--tested-wave-tip-sha", required=True)
    parser.add_argument(
        "--audited-commit",
        action="append",
        default=[],
        help="git rev-list --reverse A..T と同順に反復指定する",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = land(LandRequest(
        main_worktree=args.main_worktree,
        wave_worktree=args.wave_worktree,
        tested_main_sha=args.tested_main_sha,
        tested_wave_tip_sha=args.tested_wave_tip_sha,
        audited_commits=tuple(args.audited_commit),
    ))
    print(json.dumps(result.as_json(), ensure_ascii=False, sort_keys=True))
    return result.rc


if __name__ == "__main__":
    sys.exit(main())
