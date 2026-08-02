"""Allowlisted Git observation and exact worktree construction."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .schema import DevWavesError, ReasonCode, strict_loads


_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_RUN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_BRANCH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,180}\Z")
_SUPERVISED_RUN_RE = re.compile(r"dw-[0-9a-f]{32}\Z")
_SUPERVISED_SLUG_RE = re.compile(
    r"dev-wave-(?P<run>dw-[0-9a-f]{32})-w(?P<wave>[0-9]{3,})\Z"
)
_FRAGMENT_PATH_RE = re.compile(
    r"docs/spool/(?:worklog|decisions|failures)/"
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*-[1-9][0-9]*\.md\Z"
)
_ROTATION_PATH_RE = re.compile(
    r"docs/archive/worklog-phase3-[0-9]{4}-[1-9][0-9]*"
    r"(?:-(?:[1-9][0-9]*|[0-9]{4}-[1-9][0-9]*))?\.md\Z"
)
_IDENTITY_RE = re.compile(
    r"(?P<identity>[^<>\n]+ <[^<>\n]+>) (?P<timestamp>0|[1-9][0-9]*) "
    r"(?P<sign>[+-])(?P<hour>[0-9]{2})(?P<minute>[0-9]{2})\Z"
)
_SNAPSHOT_RETRIES = 4
_GIT_TIMEOUT_S = 30
GIT_HARDENING_CONFIG = (
    "-c", "core.hooksPath=/dev/null",
    "-c", "core.fsmonitor=false",
    "-c", "core.useBuiltinFSMonitor=false",
    "-c", "maintenance.auto=false",
    "-c", "gc.auto=0",
)

FOLD_COMMIT_MESSAGE = b"Fold landed documentation fragments\n\nAI-Agent: none\n"
FOLD_AUTHOR_IDENTITY = "Izanagi Dev Wave <dev-wave@izanagi.invalid>"
_FOLD_MODIFIED_EXACT = frozenset({
    "docs/worklog.md", "docs/decisions.md", "docs/failures.md",
    "docs/phase3.md", "docs/spool/FOLDED.md",
})


def _deadline(timeout_s: float) -> int:
    if timeout_s <= 0:
        raise DevWavesError(ReasonCode.INVALID_RUN, {"label": "git", "kind": "timeout"})
    return time.clock_gettime_ns(time.CLOCK_BOOTTIME) + int(timeout_s * 1_000_000_000)


def _left(deadline_ns: int) -> float:
    remaining = (deadline_ns - time.clock_gettime_ns(time.CLOCK_BOOTTIME)) / 1e9
    if remaining <= 0:
        raise DevWavesError(ReasonCode.INVALID_RUN, {"label": "git", "kind": "timeout"})
    return remaining

# Every Git invocation is selected by name from this table. In particular it
# contains no push, merge, rebase, reset, fetch, remote mutation, branch delete,
# worktree remove, or submodule deinit operation.
GIT_COMMANDS: Mapping[str, tuple[str, ...]] = {
    "common-dir": ("rev-parse", "--path-format=absolute", "--git-common-dir"),
    "toplevel": ("rev-parse", "--path-format=absolute", "--show-toplevel"),
    "head": ("rev-parse", "--verify", "HEAD"),
    "branch": ("symbolic-ref", "--quiet", "--short", "HEAD"),
    "shallow": ("rev-parse", "--is-shallow-repository"),
    "replace-refs": ("for-each-ref", "--format=%(refname)", "refs/replace"),
    "remote-refs": ("for-each-ref", "--format=%(refname)%00%(objectname)", "refs/remotes"),
    "remote-config": ("config", "--null", "--get-regexp", r"^remote\..*"),
    "status": ("status", "--porcelain=v2", "-z", "--untracked-files=all", "--ignore-submodules=none"),
    "worktree-list": ("worktree", "list", "--porcelain"),
    "submodule-config": ("config", "--file", ".gitmodules", "--null", "--get-regexp", r"^submodule\..*\.url$"),
    "submodule-status": ("submodule", "status", "--recursive"),
    "ls-trust-root": ("ls-tree", "-r", "-z"),
    "worktree-add": ("worktree", "add", "--no-checkout", "-b"),
    "checkout-detach": ("checkout", "--detach"),
    "switch": ("switch",),
    "submodule-update": ("-c", "protocol.file.allow=always", "submodule", "update", "--init", "--recursive", "--no-fetch"),
    "is-ancestor": ("merge-base", "--is-ancestor"),
    "rev-list": ("rev-list", "--reverse"),
    "branch-tip": ("rev-parse", "--verify"),
    "commit-object": ("cat-file", "commit"),
    "commit-diff": (
        "diff-tree", "--root", "-r", "-m", "--no-commit-id",
        "--name-status", "-z", "-M", "-C",
    ),
    "tree-paths": ("ls-tree", "-r", "-z", "--name-only"),
    "clone-isolated": ("-c", "protocol.file.allow=always", "clone", "--no-local", "--no-checkout", "--quiet"),
}


@dataclass(frozen=True)
class RepoIdentity:
    common_dir: str
    main_worktree: str
    digest: str


@dataclass(frozen=True)
class WorktreeRecord:
    path: str
    head_sha: str
    branch: Optional[str]


@dataclass(frozen=True)
class RepoSnapshot:
    head_sha: str
    branch: Optional[str]
    main_dirty: bool
    submodule_dirty: bool
    status_entries: tuple[str, ...]
    submodule_entries: tuple[str, ...]
    remote_refs: tuple[tuple[str, str], ...]
    remote_config_sha256: str


@dataclass(frozen=True)
class WaveWorktree:
    path: str
    branch: str
    base_sha: str


@dataclass(frozen=True)
class FFChainVerification:
    ok: bool
    reason: Optional[ReasonCode]
    observed_commits: tuple[str, ...]


@dataclass(frozen=True)
class DeclaredFoldVerification:
    ok: bool
    reason: Optional[ReasonCode]
    detail: str


@dataclass(frozen=True)
class GitTraceReport:
    push_attempted: bool
    malformed: bool
    event_count: int


@dataclass(frozen=True)
class TrustRoot:
    entries: tuple[tuple[str, str, str], ...]
    digest: str


def _git_env() -> dict[str, str]:
    result = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TZ") if key in os.environ}
    result.update({
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PROTOCOL_FROM_USER": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
    })
    return result


def _run(
    repo: os.PathLike[str] | str,
    operation: str,
    *,
    extra: Sequence[str] = (),
    timeout_s: float = _GIT_TIMEOUT_S,
    allowed_returncodes: Sequence[int] = (0,),
) -> subprocess.CompletedProcess[bytes]:
    if operation not in GIT_COMMANDS:
        raise ValueError("Git operation is not allowlisted")
    if isinstance(extra, (str, bytes)) or not all(isinstance(value, str) for value in extra):
        raise TypeError("extra must be a string sequence")
    command = ["git", *GIT_HARDENING_CONFIG, *GIT_COMMANDS[operation], *extra]
    try:
        result = subprocess.run(
            command, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=os.fspath(repo), env=_git_env(),
            timeout=timeout_s, check=False,
        )
    except subprocess.TimeoutExpired:
        raise DevWavesError(ReasonCode.INVALID_RUN, {
            "label": "git", "kind": "timeout",
        }) from None
    if result.returncode not in allowed_returncodes:
        raise DevWavesError(ReasonCode.INVALID_RUN, {
            "label": "git", "kind": operation, "return_code": result.returncode,
        })
    return result


def _text(result: subprocess.CompletedProcess[bytes]) -> str:
    try:
        return result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise DevWavesError(ReasonCode.INVALID_RUN, {
            "label": "git", "kind": "non-utf8-output",
        }) from None


def _sha(value: str, *, label: str) -> str:
    value = value.strip()
    if _SHA_RE.fullmatch(value) is None:
        raise DevWavesError(ReasonCode.INVALID_RUN, {"label": label, "kind": "sha"})
    return value


def resolve_repo_identity(repo_root: os.PathLike[str] | str) -> RepoIdentity:
    common = os.path.realpath(_text(_run(repo_root, "common-dir")).strip())
    main = os.path.realpath(_text(_run(repo_root, "toplevel")).strip())
    info = os.stat(common, follow_symlinks=False)
    raw = f"{common}\0{info.st_dev}\0{info.st_ino}".encode("utf-8")
    return RepoIdentity(common, main, hashlib.sha256(raw).hexdigest())


def _worktrees(repo_root: os.PathLike[str] | str) -> tuple[WorktreeRecord, ...]:
    raw = _text(_run(repo_root, "worktree-list"))
    records = []
    current: dict[str, str] = {}
    for field in raw.splitlines():
        if not field:
            if current:
                path = current.get("worktree")
                head = current.get("HEAD")
                if path is None or head is None:
                    raise DevWavesError(ReasonCode.INVALID_RUN, {
                        "label": "worktree-list", "kind": "record",
                    })
                branch = current.get("branch")
                if branch and branch.startswith("refs/heads/"):
                    branch = branch[len("refs/heads/"):]
                records.append(WorktreeRecord(path, _sha(head, label="worktree-head"), branch))
                current = {}
            continue
        key, separator, value = field.partition(" ")
        if not separator:
            current[key] = ""
        else:
            current[key] = value
    if current:
        raise DevWavesError(ReasonCode.INVALID_RUN, {
            "label": "worktree-list", "kind": "unterminated-record",
        })
    return tuple(records)


def resolve_main_worktree(
    repo_root: os.PathLike[str] | str,
    *,
    main_branch: str = "main",
) -> WorktreeRecord:
    matches = [record for record in _worktrees(repo_root) if record.branch == main_branch]
    if len(matches) != 1:
        raise DevWavesError(ReasonCode.MAIN_NOT_FOUND, {
            "label": "main-worktree", "kind": "not-unique",
        })
    return matches[0]


def _parse_status(raw: bytes) -> tuple[bool, bool, tuple[str, ...], tuple[str, ...]]:
    main_entries = []
    submodule_entries = []
    records = raw.split(b"\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        text = record.decode("utf-8", errors="strict")
        tag = text[:1]
        if tag in ("?", "!"):
            if tag == "?":
                main_entries.append(text)
            continue
        fields = text.split(" ")
        if tag in ("1", "2") and len(fields) >= 4:
            xy, sub = fields[1], fields[2]
            if tag == "2":
                # -z rename/copy records carry the original path as the next
                # NUL field, without a porcelain record tag.
                if index >= len(records) or not records[index]:
                    raise DevWavesError(ReasonCode.INVALID_RUN, {
                        "label": "status", "kind": "rename-origin",
                    })
                index += 1
        elif tag == "u" and len(fields) >= 4:
            xy, sub = fields[1], fields[2]
        else:
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "label": "status", "kind": "porcelain-v2",
            })
        if sub != "N..." and sub.startswith("S"):
            if any(flag != "." for flag in sub[1:]):
                submodule_entries.append(text)
            # Porcelain reports XY=.M for submodule content dirt alone. That is
            # a distinct submodule fact; staged gitlinks or a changed submodule
            # commit remain a main-tree fact as well.
            if xy[0] != "." or sub[1] != ".":
                main_entries.append(text)
        elif xy != "..":
            main_entries.append(text)
    return bool(main_entries), bool(submodule_entries), tuple(main_entries), tuple(submodule_entries)


def _remote_state(
    repo_root: os.PathLike[str] | str, *, timeout_s: float = _GIT_TIMEOUT_S,
) -> tuple[tuple[tuple[str, str], ...], str]:
    deadline_ns = _deadline(timeout_s)
    refs = []
    for record in _run(repo_root, "remote-refs", timeout_s=_left(deadline_ns)).stdout.splitlines():
        if not record:
            continue
        name, separator, sha_raw = record.partition(b"\0")
        if not separator:
            raise DevWavesError(ReasonCode.INVALID_RUN, {"label": "remote-ref", "kind": "record"})
        refs.append((name.decode("utf-8"), _sha(sha_raw.decode("ascii"), label="remote-ref")))
    config = _run(
        repo_root, "remote-config", timeout_s=_left(deadline_ns), allowed_returncodes=(0, 1),
    ).stdout
    return tuple(sorted(refs)), hashlib.sha256(config).hexdigest()


def _reject_shallow_or_replace(
    repo_root: os.PathLike[str] | str, *, timeout_s: float = _GIT_TIMEOUT_S,
) -> None:
    deadline_ns = _deadline(timeout_s)
    shallow = _text(_run(repo_root, "shallow", timeout_s=_left(deadline_ns))).strip()
    replacements = _text(_run(repo_root, "replace-refs", timeout_s=_left(deadline_ns))).strip()
    if shallow != "false" or replacements:
        raise DevWavesError(ReasonCode.INVALID_RUN, {
            "label": "repository", "kind": "shallow-or-replace",
        })


def snapshot_repo(
    repo_root: os.PathLike[str] | str,
    *,
    max_attempts: int = _SNAPSHOT_RETRIES,
    timeout_s: float = _GIT_TIMEOUT_S,
) -> RepoSnapshot:
    """Take a stable HEAD-before/observation/HEAD-after repository snapshot."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    deadline_ns = _deadline(timeout_s)
    _reject_shallow_or_replace(repo_root, timeout_s=_left(deadline_ns))
    for _attempt in range(max_attempts):
        before = _sha(_text(_run(repo_root, "head", timeout_s=_left(deadline_ns))), label="head-before")
        branch_result = _run(
            repo_root, "branch", timeout_s=_left(deadline_ns), allowed_returncodes=(0, 1),
        )
        branch = _text(branch_result).strip() or None
        main_dirty, sub_dirty, main_entries, sub_entries = _parse_status(
            _run(repo_root, "status", timeout_s=_left(deadline_ns)).stdout
        )
        remote_refs, remote_digest = _remote_state(repo_root, timeout_s=_left(deadline_ns))
        after = _sha(
            _text(_run(repo_root, "head", timeout_s=_left(deadline_ns))), label="head-after",
        )
        if before == after:
            return RepoSnapshot(
                after, branch, main_dirty, sub_dirty, main_entries, sub_entries,
                remote_refs, remote_digest,
            )
    raise DevWavesError(ReasonCode.MAIN_MOVED, {
        "label": "snapshot", "kind": "unstable",
    })


def _validate_base(base_sha: str) -> str:
    if _SHA_RE.fullmatch(base_sha) is None:
        raise ValueError("base_sha must be a full lowercase SHA")
    return base_sha


def supervised_spool_wave_slug(run_id: str, wave_index: int) -> str:
    """daemon 生成の run/wave identity だけを spool-safe slug へ写す。"""
    if _SUPERVISED_RUN_RE.fullmatch(run_id) is None:
        raise ValueError("run_id is not a canonical supervised run id")
    if not isinstance(wave_index, int) or isinstance(wave_index, bool) or wave_index < 1:
        raise ValueError("wave_index must be a positive integer")
    return f"dev-wave-{run_id}-w{wave_index:03d}"


def supervised_spool_wave_identity(slug: str) -> tuple[str, int]:
    """正規 slug を run/wave identity へ逆写像し、非正規形を拒否する。"""
    if not isinstance(slug, str):
        raise ValueError("slug must be text")
    match = _SUPERVISED_SLUG_RE.fullmatch(slug)
    if match is None:
        raise ValueError("slug is not a canonical supervised spool wave")
    wave_index = int(match.group("wave"))
    run_id = match.group("run")
    if supervised_spool_wave_slug(run_id, wave_index) != slug:
        raise ValueError("slug is not in canonical generated form")
    return run_id, wave_index


def _expected_worktree_path(repo_root: str, run_id: str, wave_index: int) -> str:
    if _RUN_RE.fullmatch(run_id) is None or not isinstance(wave_index, int) or wave_index < 1:
        raise ValueError("invalid run or wave identity")
    return os.path.abspath(os.path.join(
        repo_root, "output", "dev-wave-supervisor", "runtime", run_id,
        "worktrees", f"w{wave_index:03d}",
    ))


def create_exact_worktree(
    repo_root: os.PathLike[str] | str,
    run_id: str,
    wave_index: int,
    base_sha: str,
    *,
    branch: Optional[str] = None,
    timeout_s: float = _GIT_TIMEOUT_S,
) -> WaveWorktree:
    """Create the supervised branch/worktree only at the runtime-owned path."""
    root = os.path.abspath(os.fspath(repo_root))
    base = _validate_base(base_sha)
    destination = _expected_worktree_path(root, run_id, wave_index)
    branch_name = branch or f"dev-wave/{run_id}/w{wave_index:03d}"
    if _BRANCH_RE.fullmatch(branch_name) is None or ".." in branch_name or branch_name.endswith("/"):
        raise ValueError("invalid branch name")
    if os.path.lexists(destination):
        raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
            "label": "worktree", "kind": "destination-exists",
        })
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    deadline_ns = _deadline(timeout_s)
    try:
        _run(
            root, "worktree-add", extra=(branch_name, destination, base),
            timeout_s=_left(deadline_ns),
        )
        _run(
            destination, "checkout-detach", extra=(base,),
            timeout_s=_left(deadline_ns),
        )
    except DevWavesError:
        raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
            "label": "git", "kind": "worktree-add",
        }) from None
    # Restore the intended branch without accepting caller-controlled Git argv.
    try:
        _run(
            destination, "switch", extra=(branch_name,),
            timeout_s=_left(deadline_ns),
        )
    except DevWavesError:
        raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
            "label": "git", "kind": "worktree-attach",
        }) from None
    observed = snapshot_repo(destination, timeout_s=_left(deadline_ns))
    if observed.head_sha != base or observed.branch != branch_name or observed.main_dirty:
        raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
            "label": "worktree", "kind": "exact-base-mismatch",
        })
    return WaveWorktree(destination, branch_name, base)


def update_submodules_no_fetch(
    worktree: os.PathLike[str] | str, *, timeout_s: float = _GIT_TIMEOUT_S,
) -> None:
    """Initialize local-only submodules, with fetch structurally disabled."""
    root = os.path.abspath(os.fspath(worktree))
    deadline_ns = _deadline(timeout_s)
    config = _run(
        root, "submodule-config", timeout_s=_left(deadline_ns),
        allowed_returncodes=(0, 1),
    ).stdout
    records = [field for field in config.split(b"\0") if field]
    for record in records:
        _key, separator, url_raw = record.partition(b"\n")
        if not separator:
            raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
                "label": "submodule", "kind": "config-record",
            })
        url = url_raw.decode("utf-8", errors="strict")
        if not (os.path.isabs(url) or url.startswith("file://")):
            raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
                "label": "submodule", "kind": "nonlocal-url",
            })
    try:
        _run(root, "submodule-update", timeout_s=_left(deadline_ns))
    except DevWavesError:
        raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
            "label": "submodule", "kind": "update-no-fetch",
        }) from None


def _is_ancestor(
    repo_root: os.PathLike[str] | str, before: str, after: str,
    *, timeout_s: float = _GIT_TIMEOUT_S,
) -> bool:
    result = _run(
        repo_root, "is-ancestor", extra=(before, after), timeout_s=timeout_s,
        allowed_returncodes=(0, 1),
    )
    if result.returncode not in (0, 1):
        raise DevWavesError(ReasonCode.INVALID_RUN, {
            "label": "git", "kind": "is-ancestor", "return_code": result.returncode,
        })
    return result.returncode == 0


def _rev_list(
    repo_root: os.PathLike[str] | str, before: str, after: str,
    *, timeout_s: float = _GIT_TIMEOUT_S,
) -> tuple[str, ...]:
    result = _run(
        repo_root, "rev-list", extra=(f"{before}..{after}",), timeout_s=timeout_s,
    )
    return tuple(_sha(line, label="commit") for line in _text(result).splitlines())


def verify_ff_chain(
    repo_root: os.PathLike[str] | str,
    before_sha: str,
    after_sha: str,
    landed_commits: Sequence[str],
    *,
    completed: bool,
    timeout_s: float = _GIT_TIMEOUT_S,
) -> FFChainVerification:
    before = _validate_base(before_sha)
    after = _validate_base(after_sha)
    commits = tuple(_validate_base(value) for value in landed_commits)
    deadline_ns = _deadline(timeout_s)
    if not completed:
        reason = None if before == after else ReasonCode.MAIN_MOVED
        return FFChainVerification(reason is None, reason, ())
    if before == after:
        return FFChainVerification(False, ReasonCode.MAIN_UNCHANGED, ())
    if not _is_ancestor(repo_root, before, after, timeout_s=_left(deadline_ns)):
        return FFChainVerification(False, ReasonCode.MAIN_NOT_FF, ())
    observed = _rev_list(repo_root, before, after, timeout_s=_left(deadline_ns))
    if observed != commits:
        return FFChainVerification(False, ReasonCode.COMMIT_MISMATCH, observed)
    return FFChainVerification(True, None, observed)


def _fold_fail(detail: str) -> DeclaredFoldVerification:
    return DeclaredFoldVerification(False, ReasonCode.COMMIT_MISMATCH, detail)


def _landed_fold_output_path(status: str, paths: tuple[str, ...]) -> bool:
    """landed 区間に現れてはならない fold の署名だけを分類する。"""
    if "docs/spool/FOLDED.md" in paths:
        return True
    deleted_path = paths[0] if status == "D" or status.startswith("R") else None
    return deleted_path is not None and _FRAGMENT_PATH_RE.fullmatch(deleted_path) is not None


def _diff_entries(raw: bytes) -> tuple[tuple[str, tuple[str, ...]], ...]:
    records = raw.split(b"\0")
    if records and records[-1] == b"":
        records.pop()
    entries = []
    index = 0
    while index < len(records):
        try:
            status = records[index].decode("ascii", errors="strict")
        except UnicodeDecodeError:
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "label": "fold-diff", "kind": "status-encoding",
            }) from None
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(records):
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "label": "fold-diff", "kind": "record",
            })
        try:
            paths = tuple(
                record.decode("utf-8", errors="strict")
                for record in records[index:index + path_count]
            )
        except UnicodeDecodeError:
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "label": "fold-diff", "kind": "path-encoding",
            }) from None
        if not status or any(not path or "\x00" in path for path in paths):
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "label": "fold-diff", "kind": "record",
            })
        entries.append((status, paths))
        index += path_count
    return tuple(entries)


def _commit_diff(
    repo_root: os.PathLike[str] | str,
    commit_sha: str,
    *,
    timeout_s: float,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return _diff_entries(
        _run(repo_root, "commit-diff", extra=(commit_sha,), timeout_s=timeout_s).stdout
    )


def _identity_line_valid(line: bytes, *, fixed_identity: Optional[str] = None) -> bool:
    try:
        text = line.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    match = _IDENTITY_RE.fullmatch(text)
    if match is None or (fixed_identity is not None and match.group("identity") != fixed_identity):
        return False
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    return minute <= 59 and (hour < 14 or hour == 14 and minute == 0)


def _commit_shape(
    repo_root: os.PathLike[str] | str,
    fold_sha: str,
    *,
    timeout_s: float,
) -> tuple[Optional[str], Optional[str]]:
    raw = _run(repo_root, "commit-object", extra=(fold_sha,), timeout_s=timeout_s).stdout
    header, separator, message = raw.partition(b"\n\n")
    if not separator or message != FOLD_COMMIT_MESSAGE:
        return None, "message"
    headers: dict[bytes, list[bytes]] = {}
    for line in header.splitlines():
        key, space, value = line.partition(b" ")
        if not space or key not in {
            b"tree", b"parent", b"author", b"committer", b"encoding",
        }:
            return None, "header"
        headers.setdefault(key, []).append(value)
    if (
        len(headers.get(b"tree", ())) != 1
        or len(headers.get(b"parent", ())) != 1
        or len(headers.get(b"author", ())) != 1
        or len(headers.get(b"committer", ())) != 1
        or len(headers.get(b"encoding", ())) > 1
    ):
        return None, "header"
    if headers.get(b"encoding"):
        encoding = headers[b"encoding"][0]
        if not encoding or any(byte < 0x21 or byte > 0x7e for byte in encoding):
            return None, "header"
    try:
        parent = headers[b"parent"][0].decode("ascii", errors="strict")
    except UnicodeDecodeError:
        return None, "parent"
    if _SHA_RE.fullmatch(parent) is None:
        return None, "parent"
    if not _identity_line_valid(headers[b"author"][0], fixed_identity=FOLD_AUTHOR_IDENTITY):
        return None, "author"
    if not _identity_line_valid(headers[b"committer"][0]):
        return None, "committer"
    return parent, None


def _pending_fragment_paths(
    repo_root: os.PathLike[str] | str,
    head_sha: str,
    *,
    timeout_s: float,
) -> tuple[str, ...]:
    result = _run(
        repo_root,
        "tree-paths",
        extra=(
            head_sha, "--", "docs/spool/worklog", "docs/spool/decisions",
            "docs/spool/failures",
        ),
        timeout_s=timeout_s,
    )
    paths = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            path = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "label": "fold-pending", "kind": "path-encoding",
            }) from None
        if not path.endswith("/README.md"):
            paths.append(path)
    return tuple(paths)


def verify_declared_fold_commit(
    repo_root: os.PathLike[str] | str,
    *,
    fold_commit_sha: Optional[str],
    landed_main_sha: str,
    landed_commits: Sequence[str],
    wave_tip: str,
    timeout_s: float = _GIT_TIMEOUT_S,
) -> DeclaredFoldVerification:
    """申告された fold slot の graph・identity・変更 path の形を検査する。

    FoldPlan との blob 単位照合は行わない。ここで扱うのは commit の形と、
    landed 区間に fragment 削除・FOLDED receipt 変更がないことまでである。
    """
    landed_main = _validate_base(landed_main_sha)
    tip = _validate_base(wave_tip)
    commits = tuple(_validate_base(value) for value in landed_commits)
    if not commits:
        return _fold_fail("landed-commits-empty")
    if fold_commit_sha is not None:
        fold_sha = _validate_base(fold_commit_sha)
    else:
        fold_sha = None
    deadline_ns = _deadline(timeout_s)
    head = _sha(
        _text(_run(repo_root, "head", timeout_s=_left(deadline_ns))),
        label="fold-main-head",
    )
    if commits[-1] != tip:
        return _fold_fail("wave-tip")

    for commit in commits:
        for status, paths in _commit_diff(
            repo_root, commit, timeout_s=_left(deadline_ns),
        ):
            if _landed_fold_output_path(status, paths):
                return _fold_fail("landed-fold-owned-path")

    if fold_sha is None:
        if head != landed_main or landed_main != tip:
            return _fold_fail("null-head")
        if _pending_fragment_paths(
            repo_root, head, timeout_s=_left(deadline_ns),
        ):
            return _fold_fail("null-pending-fragment")
        return DeclaredFoldVerification(True, None, "no-fold")

    if head != landed_main or landed_main != fold_sha:
        return _fold_fail("declared-head")
    parent, shape_error = _commit_shape(
        repo_root, fold_sha, timeout_s=_left(deadline_ns),
    )
    if shape_error is not None:
        return _fold_fail(shape_error)
    if parent != commits[-1] or parent != tip:
        return _fold_fail("parent")

    deleted_fragments = 0
    folded_modified = False
    archive_adds = 0
    archive_readme_modified = False
    for status, paths in _commit_diff(
        repo_root, fold_sha, timeout_s=_left(deadline_ns),
    ):
        if status.startswith(("R", "C")) or status not in {"M", "D", "A"}:
            return _fold_fail("path-status")
        path = paths[0]
        if status == "M":
            if path == "docs/archive/README.md":
                archive_readme_modified = True
            elif path not in _FOLD_MODIFIED_EXACT:
                return _fold_fail("modified-path")
            if path == "docs/spool/FOLDED.md":
                folded_modified = True
        elif status == "D":
            if _FRAGMENT_PATH_RE.fullmatch(path) is None:
                return _fold_fail("deleted-path")
            deleted_fragments += 1
        else:
            if _ROTATION_PATH_RE.fullmatch(path) is None:
                return _fold_fail("added-path")
            archive_adds += 1
            if archive_adds > 1:
                return _fold_fail("archive-count")
    if archive_readme_modified and archive_adds != 1:
        return _fold_fail("archive-readme")
    if deleted_fragments < 1 or not folded_modified:
        return _fold_fail("minimum-shape")
    return DeclaredFoldVerification(True, None, "fold-shape")


def branch_tip(
    repo_root: os.PathLike[str] | str, branch: str, *, timeout_s: float = _GIT_TIMEOUT_S,
) -> str:
    if _BRANCH_RE.fullmatch(branch) is None:
        raise ValueError("invalid branch name")
    result = _run(
        repo_root, "branch-tip", extra=(f"refs/heads/{branch}",), timeout_s=timeout_s,
    )
    return _sha(_text(result), label="branch-tip")


def trust_root(
    repo_root: os.PathLike[str] | str, sha: str, *, timeout_s: float = _GIT_TIMEOUT_S,
) -> TrustRoot:
    revision = _validate_base(sha)
    result = _run(
        repo_root, "ls-trust-root",
        extra=(revision, "--", "tools", "orchestrator/tests"),
        timeout_s=timeout_s,
    )
    entries = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, path_raw = record.partition(b"\t")
        parts = metadata.decode("ascii").split()
        if not separator or len(parts) != 3:
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "label": "trust-root", "kind": "ls-tree-record",
            })
        mode, kind, object_sha = parts
        path = path_raw.decode("utf-8", errors="strict")
        if ((path.startswith("tools/check_") and path.endswith(".py")) or
                path in {"tools/run_tests.py", "tools/task_run_check.py"} or
                path.startswith("tools/task_runs/") or
                path.startswith("orchestrator/tests/")):
            entries.append((path, mode, _sha(object_sha, label="trust-root-object")))
    ordered = tuple(sorted(entries))
    digest = hashlib.sha256(
        b"\0".join(f"{path}\0{mode}\0{obj}".encode() for path, mode, obj in ordered)
    ).hexdigest()
    return TrustRoot(ordered, digest)


def create_isolated_checkout(
    repo_root: os.PathLike[str] | str,
    sha: str,
    destination: os.PathLike[str] | str,
    *,
    timeout_s: float,
) -> str:
    """Clone locally and detach at an audited SHA for active checks."""
    revision = _validate_base(sha)
    source = os.path.abspath(os.fspath(repo_root))
    target = os.path.abspath(os.fspath(destination))
    if os.path.lexists(target):
        raise FileExistsError(target)
    deadline_ns = _deadline(timeout_s)
    try:
        _run(
            os.path.dirname(target), "clone-isolated", extra=(source, target),
            timeout_s=_left(deadline_ns),
        )
    except DevWavesError:
        raise DevWavesError(ReasonCode.CHECK_FAILED, {
            "label": "isolated-checkout", "kind": "clone",
        }) from None
    try:
        _run(target, "checkout-detach", extra=(revision,), timeout_s=_left(deadline_ns))
    except DevWavesError:
        raise DevWavesError(ReasonCode.CHECK_FAILED, {
            "label": "isolated-checkout", "kind": "checkout",
        }) from None
    return target


def read_child_git_trace(
    path: os.PathLike[str] | str,
    *,
    max_bytes: int = 8 * 1024 * 1024,
) -> GitTraceReport:
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return GitTraceReport(False, True, 0)
    if len(raw) > max_bytes or (raw and not raw.endswith(b"\n")):
        return GitTraceReport(False, True, 0)
    attempted = False
    count = 0
    for line in raw.splitlines():
        if not line:
            return GitTraceReport(attempted, True, count)
        try:
            event = strict_loads(line, label="git-trace", max_bytes=max_bytes)
        except DevWavesError:
            return GitTraceReport(attempted, True, count)
        if not isinstance(event, dict):
            return GitTraceReport(attempted, True, count)
        count += 1
        argv = event.get("argv")
        hierarchy = event.get("cmd_hierarchy")
        name = event.get("name") or event.get("cmd_name")
        if ((isinstance(argv, list) and any(token == "push" for token in argv)) or
                (isinstance(hierarchy, str) and "push" in hierarchy.split("/")) or
                name == "push"):
            attempted = True
    return GitTraceReport(attempted, False, count)


__all__ = [
    "DeclaredFoldVerification", "FFChainVerification", "FOLD_AUTHOR_IDENTITY",
    "FOLD_COMMIT_MESSAGE", "GIT_COMMANDS", "GIT_HARDENING_CONFIG", "GitTraceReport", "RepoIdentity",
    "RepoSnapshot", "TrustRoot", "WaveWorktree", "WorktreeRecord", "branch_tip",
    "create_exact_worktree", "create_isolated_checkout", "read_child_git_trace",
    "resolve_main_worktree", "resolve_repo_identity", "snapshot_repo",
    "supervised_spool_wave_identity", "supervised_spool_wave_slug", "trust_root",
    "update_submodules_no_fetch", "verify_declared_fold_commit", "verify_ff_chain",
]
