#!/usr/bin/env python3
"""land 済み dev-wave の linked worktree と local branch を安全に撤去する。"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Sequence

import check_worktree_occupancy as occupancy


RC_USAGE = 2
RC_REJECTED = 20
RC_OCCUPIED = 21
RC_OCCUPANCY_INDETERMINATE = 22
RC_PARTIAL = 30

_REPO = Path(__file__).resolve().parent.parent
_SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_PRUNE_LINE_RE = re.compile(r"^Removing worktrees/([^:]+): .+$")


@dataclass(frozen=True)
class Args:
    main_worktree: Path
    wave_worktree: Path
    wave_branch: str
    tested_wave_tip_sha: str


@dataclass(frozen=True)
class WorktreeRecord:
    path_raw: bytes
    path: Path
    head: str
    branch: str | None
    detached: bool
    locked: bool
    prunable: bool


@dataclass(frozen=True)
class DirectoryIdentity:
    dev: int
    ino: int
    gitfile_dev: int
    gitfile_ino: int
    gitdir: Path


@dataclass(frozen=True)
class VerifiedWavePath:
    path: Path
    identity: DirectoryIdentity


@dataclass(frozen=True)
class OccupancyDiagnostics:
    cwd_permission: object
    same_uid_cwd_unreachable: object


@dataclass(frozen=True)
class OccupancyObservation:
    phase: str
    diagnostics: OccupancyDiagnostics


@dataclass(frozen=True)
class CleanupResult:
    outcome: str
    occupancy: tuple[OccupancyObservation, ...]


class CleanupFailure(Exception):
    def __init__(self, rc: int, status: str, phase: str, reason: str) -> None:
        super().__init__(reason)
        self.rc = rc
        self.status = status
        self.phase = phase
        self.reason = reason


class GitFailure(Exception):
    def __init__(self, args: Sequence[str], result: subprocess.CompletedProcess[bytes]) -> None:
        detail = (result.stderr or result.stdout).decode("utf-8", "replace").strip()
        super().__init__(f"git {args[0]} rc={result.returncode}: {detail or 'no diagnostic'}")


def _sanitize(value: object, *, limit: int = 500) -> str:
    text = " ".join(str(value).replace("\x00", " ").split()) or "unspecified"
    raw = text.encode("utf-8", "replace")[:limit]
    while True:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raw = raw[:exc.start]


def _usage(reason: str) -> CleanupFailure:
    return CleanupFailure(RC_USAGE, "rejected", "argv", reason)


def _reject(phase: str, reason: str, rc: int = RC_REJECTED) -> CleanupFailure:
    return CleanupFailure(rc, "rejected", phase, reason)


def _partial(phase: str, reason: object) -> CleanupFailure:
    return CleanupFailure(RC_PARTIAL, "partial", phase, str(reason))


def _parse_argv(argv: Sequence[str]) -> Args:
    expected = {
        "--main-worktree": "main",
        "--wave-worktree": "wave",
        "--wave-branch": "branch",
        "--tested-wave-tip-sha": "tip",
    }
    if len(argv) != 8:
        raise _usage("exactly four option-value pairs are required")
    values: dict[str, str] = {}
    for index in range(0, len(argv), 2):
        option = argv[index]
        if option not in expected:
            raise _usage(f"unknown option {option}")
        key = expected[option]
        if key in values:
            raise _usage(f"duplicate option {option}")
        value = argv[index + 1]
        if not value or "\x00" in value:
            raise _usage(f"invalid value for {option}")
        values[key] = value
    if set(values) != set(expected.values()):
        raise _usage("all four options are required")
    if not _SHA_RE.fullmatch(values["tip"]):
        raise _usage("tested tip must be a full lowercase 40- or 64-digit sha")
    main = _validate_path_spelling(values["main"], "main-worktree", must_exist=True)
    wave = _validate_path_spelling(values["wave"], "wave-worktree", must_exist=False)
    return Args(main, wave, values["branch"], values["tip"])


def _validate_path_spelling(raw: str, label: str, *, must_exist: bool) -> Path:
    if not raw.startswith("/") or not PurePath(raw).is_absolute():
        raise _usage(f"{label} must be lexical absolute")
    if raw != "/" and raw.endswith("/"):
        raise _usage(f"{label} has trailing slash")
    if ".." in PurePath(raw).parts:
        raise _usage(f"{label} contains dot-dot component")
    if os.path.normpath(raw) != raw:
        raise _usage(f"{label} is not a normalized lexical path")
    path = Path(raw)
    cursor = Path("/")
    missing = False
    for part in path.parts[1:]:
        cursor = cursor / part
        if missing:
            continue
        try:
            mode = os.lstat(cursor).st_mode
        except FileNotFoundError:
            missing = True
            continue
        except OSError as exc:
            raise _usage(f"{label} component cannot be inspected: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise _usage(f"{label} contains symlink component")
    if must_exist and missing:
        raise _usage(f"{label} does not exist")
    try:
        if missing:
            existing = path
            suffix: list[str] = []
            while not existing.exists():
                suffix.append(existing.name)
                existing = existing.parent
            rebuilt = existing.resolve(strict=True).joinpath(*reversed(suffix))
            if rebuilt != path:
                raise _usage(f"{label} realpath differs")
        elif path.resolve(strict=True) != path:
            raise _usage(f"{label} realpath differs")
    except (OSError, RuntimeError) as exc:
        raise _usage(f"{label} realpath cannot be established: {exc}") from exc
    return path


def _validate_git_argv(args: Sequence[str]) -> None:
    if not args:
        raise RuntimeError("empty git command")
    argv = tuple(args)
    if argv in {
        ("rev-parse", "--git-common-dir"),
        ("rev-parse", "--git-dir"),
        ("rev-parse", "--git-path", "izanagi-spool-fold-state.json"),
        ("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"),
        ("symbolic-ref", "--quiet", "HEAD"),
        ("worktree", "list", "--porcelain"),
        ("worktree", "prune", "--dry-run", "--verbose", "--expire=now"),
        ("worktree", "prune", "--expire=now"),
        ("checkout", "--detach"),
    }:
        return
    if (
        len(argv) == 3
        and argv[:2] in {
            ("cat-file", "-e"),
            ("check-ref-format", "--branch"),
            ("rev-list", "--walk-reflogs"),
            ("rev-parse", "--verify"),
            ("worktree", "unlock"),
        }
        and argv[2]
        and not argv[2].startswith("-")
    ):
        return
    if (
        len(argv) == 4
        and argv[:2] == ("merge-base", "--is-ancestor")
        and argv[2]
        and not argv[2].startswith("-")
        and argv[3] == "refs/heads/main"
    ):
        return
    if (
        len(argv) == 4
        and argv[:3] == ("branch", "-d", "--")
        and argv[3]
        and not argv[3].startswith("-")
    ):
        return
    raise RuntimeError(f"git argv is not allowlisted: {argv!r}")


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    _validate_git_argv(args)
    return subprocess.run(
        ["git", "-C", os.fspath(cwd), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
    )


def _must_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    result = _git(cwd, *args)
    if result.returncode != 0:
        raise GitFailure(args, result)
    return result


def _one_line(result: subprocess.CompletedProcess[bytes], what: str) -> str:
    raw = result.stdout
    if not raw or b"\x00" in raw or raw.count(b"\n") > 1:
        raise ValueError(f"{what} did not return one line")
    return raw.rstrip(b"\n").decode("utf-8", "strict")


def _git_path(cwd: Path, *args: str, must_exist: bool = True) -> Path:
    value = _one_line(_must_git(cwd, *args), args[-1])
    path = Path(value)
    if not path.is_absolute():
        path = cwd / path
    if must_exist:
        return path.resolve(strict=True)
    return path.parent.resolve(strict=True) / path.name


def _parse_worktree_records(raw: bytes) -> list[WorktreeRecord]:
    if b"\x00" in raw:
        raise ValueError("line porcelain contains NUL")
    if not raw.endswith(b"\n\n"):
        raise ValueError("line porcelain lacks record terminator")
    records: list[WorktreeRecord] = []
    for record_raw in raw[:-2].split(b"\n\n"):
        if not record_raw:
            raise ValueError("empty porcelain record")
        fields: dict[bytes, bytes] = {}
        flags: set[bytes] = set()
        for item in record_raw.split(b"\n"):
            key, sep, value = item.partition(b" ")
            if key not in {b"worktree", b"HEAD", b"branch", b"detached", b"bare", b"locked", b"prunable"}:
                raise ValueError(f"unknown porcelain field {key!r}")
            if key in fields or key in flags:
                raise ValueError(f"duplicate porcelain field {key!r}")
            if key in {b"detached", b"bare"}:
                if sep:
                    raise ValueError(f"flag field has value {key!r}")
                flags.add(key)
            else:
                if not sep and key not in {b"locked", b"prunable"}:
                    raise ValueError(f"field lacks value {key!r}")
                fields[key] = value if sep else b""
        if b"worktree" not in fields or b"HEAD" not in fields:
            raise ValueError("porcelain record lacks worktree or HEAD")
        if b"branch" in fields and b"detached" in flags:
            raise ValueError("record is both attached and detached")
        if b"bare" in flags:
            raise ValueError("bare worktree record is unsupported")
        path_raw = fields[b"worktree"]
        if not path_raw.startswith(b"/") or any(byte < 0x20 or byte == 0x7f for byte in path_raw):
            raise ValueError("porcelain worktree path is not absolute")
        try:
            head = fields[b"HEAD"].decode("ascii")
            branch = fields.get(b"branch")
            branch_text = branch.decode("utf-8", "strict") if branch is not None else None
        except UnicodeDecodeError as exc:
            raise ValueError("porcelain identity is not valid text") from exc
        records.append(WorktreeRecord(
            path_raw=path_raw,
            path=Path(os.fsdecode(path_raw)),
            head=head,
            branch=branch_text,
            detached=b"detached" in flags,
            locked=b"locked" in fields,
            prunable=b"prunable" in fields,
        ))
    paths = [record.path_raw for record in records]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate worktree path records")
    return records


def _worktree_records(main: Path) -> list[WorktreeRecord]:
    result = _must_git(main, "worktree", "list", "--porcelain")
    return _parse_worktree_records(result.stdout)


def _record_for(records: Sequence[WorktreeRecord], path: Path) -> WorktreeRecord | None:
    raw = os.fsencode(path)
    matches = [record for record in records if record.path_raw == raw]
    if len(matches) > 1:
        raise ValueError("multiple records for target path")
    return matches[0] if matches else None


def _resolve_commit(cwd: Path, expression: str) -> str | None:
    result = _git(cwd, "rev-parse", "--verify", expression)
    if result.returncode != 0:
        diagnostic = result.stderr.decode("utf-8", "replace")
        if result.returncode == 128 and "Needed a single revision" in diagnostic:
            return None
        raise GitFailure(("rev-parse", "--verify", expression), result)
    value = _one_line(result, expression)
    if not _SHA_RE.fullmatch(value):
        raise ValueError(f"{expression} did not resolve to a full sha")
    return value


def _directory_identity(path: Path, common: Path) -> DirectoryIdentity:
    root_stat = os.stat(path, follow_symlinks=False)
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("wave path is not a directory")
    gitfile = path / ".git"
    git_stat = os.stat(gitfile, follow_symlinks=False)
    if not stat.S_ISREG(git_stat.st_mode):
        raise ValueError("linked worktree .git binding is not a regular file")
    content = gitfile.read_bytes()
    if not content.startswith(b"gitdir: ") or b"\x00" in content or content.count(b"\n") > 1:
        raise ValueError("linked worktree .git binding is malformed")
    gitdir = Path(os.fsdecode(content[len(b"gitdir: "):].rstrip(b"\n")))
    if not gitdir.is_absolute():
        gitdir = gitfile.parent / gitdir
    gitdir = gitdir.resolve(strict=True)
    worktrees_dir = (common / "worktrees").resolve(strict=True)
    try:
        gitdir.relative_to(worktrees_dir)
    except ValueError as exc:
        raise ValueError("linked worktree gitdir is outside common registry") from exc
    return DirectoryIdentity(
        root_stat.st_dev,
        root_stat.st_ino,
        git_stat.st_dev,
        git_stat.st_ino,
        gitdir,
    )


def _assert_identity(path: Path, common: Path, expected: DirectoryIdentity) -> None:
    if _directory_identity(path, common) != expected:
        raise ValueError("wave dev/ino or gitdir binding changed")


def _assert_cwd_outside(wave: Path) -> None:
    def inside(candidate: Path) -> bool:
        try:
            candidate.relative_to(wave)
            return True
        except ValueError:
            return False

    actual = Path(os.getcwd()).resolve(strict=True)
    lexical_raw = os.environ.get("PWD")
    if not lexical_raw or not lexical_raw.startswith("/"):
        raise ValueError("lexical cwd is unavailable or not absolute")
    lexical = Path(os.path.abspath(lexical_raw))
    if inside(actual) or inside(lexical):
        raise ValueError("cwd is inside target worktree")


def _occupancy_payload(path: Path) -> tuple[int, dict[str, object]]:
    report = occupancy.scan_worktree_occupancy(path, self_pid=os.getpid())
    payload = occupancy._report_payload(report)
    rc = {
        "unoccupied": occupancy.UNOCCUPIED_RC,
        "occupied": occupancy.OCCUPIED_RC,
        "indeterminate": occupancy.INDETERMINATE_RC,
    }[report.status]
    # Exercise the same JSON boundary as the standalone checker without exposing
    # this process's target-bearing argv to a second /proc scan.
    payload = json.loads(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return rc, payload


def _assert_unoccupied(path: Path) -> OccupancyDiagnostics:
    try:
        rc, payload = _occupancy_payload(path)
    except CleanupFailure:
        raise
    except Exception as exc:  # noqa: BLE001 - checker failures are indeterminate
        raise _reject(
            "occupancy", f"occupancy checker failed: {exc}",
            RC_OCCUPANCY_INDETERMINATE,
        ) from exc
    expected_keys = {
        "issues", "occupants", "same_uid_cwd_unreachable", "status", "unreachable", "worktree",
    }
    if not isinstance(payload, dict) or not expected_keys <= set(payload):
        raise _reject("occupancy", "occupancy payload lacks required fields", RC_OCCUPANCY_INDETERMINATE)
    if payload.get("worktree") != os.fspath(path):
        raise _reject("occupancy", "occupancy payload target mismatch", RC_OCCUPANCY_INDETERMINATE)
    occupants = payload.get("occupants")
    if (
        rc == occupancy.OCCUPIED_RC
        or payload.get("status") == "occupied"
        or (isinstance(occupants, list) and bool(occupants))
    ):
        raise _reject("occupancy", "target worktree is occupied", RC_OCCUPIED)
    unreachable = payload.get("unreachable")
    valid = (
        rc == occupancy.UNOCCUPIED_RC
        and payload.get("status") == "unoccupied"
        and occupants == []
        and payload.get("issues") == []
    )
    if not valid:
        raise _reject("occupancy", "occupancy result is indeterminate or inconsistent", RC_OCCUPANCY_INDETERMINATE)
    if not isinstance(unreachable, dict) or "cwd_permission" not in unreachable:
        raise _reject(
            "occupancy", "unreachable process diagnostics are malformed",
            RC_OCCUPANCY_INDETERMINATE,
        )
    unreachable_same_uid = payload.get("same_uid_cwd_unreachable")
    if not isinstance(unreachable_same_uid, list):
        raise _reject(
            "occupancy", "same-uid unreachable process diagnostics are malformed",
            RC_OCCUPANCY_INDETERMINATE,
        )
    return OccupancyDiagnostics(
        cwd_permission=unreachable["cwd_permission"],
        same_uid_cwd_unreachable=unreachable_same_uid,
    )


def _assert_clean_and_head(path: Path, tip: str) -> None:
    status_result = _must_git(
        path,
        "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none",
    )
    if status_result.stdout:
        raise ValueError("wave worktree is dirty")
    if _resolve_commit(path, "HEAD^{commit}") != tip:
        raise ValueError("wave HEAD differs from tested tip")


def _assert_reflog_commits_reachable(main: Path, shas: Sequence[str], label: str) -> None:
    for sha in shas:
        if not _SHA_RE.fullmatch(sha):
            raise ValueError(f"{label} contains a malformed commit id")
        reachable = _git(main, "merge-base", "--is-ancestor", sha, "refs/heads/main")
        if reachable.returncode == 1:
            raise ValueError(f"{label} contains a commit not reachable from main")
        if reachable.returncode != 0:
            raise ValueError(f"{label} ancestry check rc={reachable.returncode}")


def _head_reflog_shas(administrative_gitdir: Path) -> tuple[str, ...]:
    raw = (administrative_gitdir / "logs" / "HEAD").read_bytes()
    if not raw or b"\x00" in raw or not raw.endswith(b"\n"):
        raise ValueError("worktree HEAD reflog is missing or malformed")
    shas: list[str] = []
    for line in raw.splitlines():
        fields = line.split(b" ", 2)
        if len(fields) != 3:
            raise ValueError("worktree HEAD reflog line is malformed")
        for raw_sha in fields[:2]:
            try:
                sha = raw_sha.decode("ascii", "strict")
            except UnicodeDecodeError as exc:
                raise ValueError("worktree HEAD reflog commit id is not ASCII") from exc
            if set(sha) == {"0"} and len(sha) in {40, 64}:
                continue
            if not _SHA_RE.fullmatch(sha):
                raise ValueError("worktree HEAD reflog contains a malformed commit id")
            shas.append(sha)
    unique = tuple(dict.fromkeys(shas))
    if not unique:
        raise ValueError("worktree HEAD reflog has no inspectable commits")
    return unique


def _administrative_gitdirs_for_wave(common: Path, wave: Path) -> tuple[Path, ...]:
    registry = common / "worktrees"
    if not registry.exists():
        return ()
    if not registry.is_dir():
        raise ValueError("worktree administrative registry is not a directory")
    matches: list[Path] = []
    for candidate in registry.iterdir():
        try:
            candidate_resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"worktree administrative entry cannot be resolved: {exc}") from exc
        if candidate_resolved != candidate or not candidate.is_dir():
            raise ValueError("worktree administrative entry is not a direct directory")
        binding_path = candidate / "gitdir"
        try:
            raw = binding_path.read_bytes()
        except FileNotFoundError:
            continue
        if not raw or b"\x00" in raw or raw.count(b"\n") > 1:
            raise ValueError("worktree administrative gitdir binding is malformed")
        binding = Path(os.fsdecode(raw.rstrip(b"\n")))
        if not binding.is_absolute():
            binding = candidate / binding
        binding = Path(os.path.abspath(binding))
        if binding == wave / ".git":
            matches.append(candidate)
    return tuple(matches)


def _stale_administrative_gitdir(common: Path, wave: Path) -> Path:
    matches = _administrative_gitdirs_for_wave(common, wave)
    if len(matches) != 1:
        raise ValueError("target stale worktree administrative gitdir is not unique")
    return matches[0]


def _assert_branch_safety(
    main: Path,
    ref: str,
    administrative_gitdir: Path | None,
) -> None:
    ancestry = _git(main, "merge-base", "--is-ancestor", ref, "refs/heads/main")
    if ancestry.returncode != 0:
        raise ValueError(f"branch ancestry check rc={ancestry.returncode}")
    reflog = _git(main, "rev-list", "--walk-reflogs", ref)
    if reflog.returncode != 0:
        raise ValueError(f"branch reflog cannot be inspected rc={reflog.returncode}")
    try:
        reflog_shas = tuple(dict.fromkeys(reflog.stdout.decode("ascii", "strict").splitlines()))
    except UnicodeDecodeError as exc:
        raise ValueError("branch reflog output is not ASCII") from exc
    if not reflog_shas:
        raise ValueError("branch reflog is unavailable")
    _assert_reflog_commits_reachable(main, reflog_shas, "branch reflog")
    if administrative_gitdir is not None:
        _assert_reflog_commits_reachable(
            main,
            _head_reflog_shas(administrative_gitdir),
            "worktree HEAD reflog",
        )


def _assert_no_other_holder(
    records: Sequence[WorktreeRecord], target: Path, ref: str,
) -> None:
    if any(record.path != target and record.branch == ref for record in records):
        raise ValueError("another worktree holds the wave branch")


def _classify(
    record: WorktreeRecord | None,
    directory_exists: bool,
    branch_tip: str | None,
    ref: str,
    tested_tip: str,
) -> str:
    if (
        directory_exists
        and record is not None
        and record.branch == ref
        and record.detached is False
        and record.head == tested_tip
        and branch_tip == tested_tip
    ):
        return "a"
    if (
        directory_exists
        and record is not None
        and record.branch is None
        and record.detached is True
        and record.head == tested_tip
        and branch_tip == tested_tip
    ):
        return "b"
    if (
        not directory_exists
        and record is not None
        and record.branch is None
        and record.detached is True
        and record.head == tested_tip
        and branch_tip == tested_tip
    ):
        return "c"
    if not directory_exists and record is None and branch_tip == tested_tip:
        return "d"
    if not directory_exists and record is None and branch_tip is None:
        return "e"
    raise ValueError("target does not match one cleanup state")


def _preflight(
    args: Args,
) -> tuple[
    str,
    Path,
    str,
    WorktreeRecord | None,
    VerifiedWavePath | None,
    OccupancyDiagnostics | None,
]:
    branch_check = _git(args.main_worktree, "check-ref-format", "--branch", args.wave_branch)
    if branch_check.returncode != 0:
        raise _usage("wave branch is not a valid local branch name")
    try:
        normalized_branch = _one_line(branch_check, "branch")
    except (UnicodeError, ValueError) as exc:
        raise _usage(f"wave branch validation output is malformed: {exc}") from exc
    if normalized_branch != args.wave_branch:
        raise _usage("branch normalization changed input")

    common = _git_path(args.main_worktree, "rev-parse", "--git-common-dir")
    main_gitdir = _git_path(args.main_worktree, "rev-parse", "--git-dir")
    if main_gitdir != common:
        raise ValueError("main-worktree is not the primary checkout")
    tool_common = _git_path(_REPO, "rev-parse", "--git-common-dir")
    if tool_common != common:
        raise ValueError("tool repository and main-worktree common git-dir differ")
    if _one_line(_must_git(args.main_worktree, "symbolic-ref", "--quiet", "HEAD"), "main HEAD") != "refs/heads/main":
        raise ValueError("main-worktree HEAD is not refs/heads/main")
    commit_check = _git(args.main_worktree, "cat-file", "-e", f"{args.tested_wave_tip_sha}^{{commit}}")
    if commit_check.returncode != 0:
        raise ValueError("tested tip is not an existing commit object")

    records = _worktree_records(args.main_worktree)
    if not records or records[0].path_raw != os.fsencode(args.main_worktree):
        raise ValueError("main-worktree is not the primary porcelain record")
    main_record = _record_for(records, args.main_worktree)
    if main_record is None or main_record.branch != "refs/heads/main":
        raise ValueError("main-worktree porcelain identity mismatch")
    record = _record_for(records, args.wave_worktree)
    path_present = os.path.lexists(args.wave_worktree)
    directory_exists = args.wave_worktree.is_dir()
    if path_present and not directory_exists:
        raise ValueError("wave path exists but is not a directory")
    ref = f"refs/heads/{args.wave_branch}"
    branch_tip = _resolve_commit(args.main_worktree, f"{ref}^{{commit}}")
    state = _classify(
        record,
        directory_exists,
        branch_tip,
        ref,
        args.tested_wave_tip_sha,
    )
    _assert_cwd_outside(args.wave_worktree)
    fold_path = _git_path(
        args.main_worktree,
        "rev-parse", "--git-path", "izanagi-spool-fold-state.json",
        must_exist=False,
    )
    if os.path.lexists(fold_path):
        raise ValueError("active fold state exists")
    if state in {"d", "e"} and _administrative_gitdirs_for_wave(common, args.wave_worktree):
        raise ValueError("target administrative gitdir exists without a porcelain record")
    if state == "e":
        return state, common, ref, record, None, None
    if record is not None:
        _assert_no_other_holder(records, args.wave_worktree, ref)

    verified: VerifiedWavePath | None = None
    administrative_gitdir: Path | None = None
    if directory_exists:
        identity = _directory_identity(args.wave_worktree, common)
        verified = VerifiedWavePath(args.wave_worktree, identity)
        administrative_gitdir = identity.gitdir
        if _git_path(args.wave_worktree, "rev-parse", "--git-common-dir") != common:
            raise ValueError("wave worktree belongs to another common git-dir")
        _assert_clean_and_head(args.wave_worktree, args.tested_wave_tip_sha)
    elif state == "c":
        administrative_gitdir = _stale_administrative_gitdir(common, args.wave_worktree)
    _assert_branch_safety(args.main_worktree, ref, administrative_gitdir)
    occupancy_diagnostics: OccupancyDiagnostics | None = None
    if directory_exists:
        occupancy_diagnostics = _assert_unoccupied(args.wave_worktree)
        assert verified is not None
        _assert_identity(args.wave_worktree, common, verified.identity)
    return state, common, ref, record, verified, occupancy_diagnostics


def _remove_verified_tree(verified: VerifiedWavePath, common: Path) -> None:
    _assert_identity(verified.path, common, verified.identity)
    shutil.rmtree(verified.path)


def _dry_run_candidates(main: Path, common: Path) -> list[Path]:
    result = _must_git(main, "worktree", "prune", "--dry-run", "--verbose", "--expire=now")
    text = (result.stdout + result.stderr).decode("utf-8", "replace")
    candidates: list[Path] = []
    for line in text.splitlines():
        match = _PRUNE_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"unrecognized prune dry-run output: {line}")
        name = match.group(1)
        if not name or "/" in name or name in {".", ".."}:
            raise ValueError("invalid prune candidate name")
        admin = common / "worktrees" / name
        gitdir_file = admin / "gitdir"
        raw = gitdir_file.read_bytes()
        if b"\x00" in raw or raw.count(b"\n") > 1:
            raise ValueError("prune candidate gitdir binding is malformed")
        gitfile = Path(os.fsdecode(raw.rstrip(b"\n")))
        if not gitfile.is_absolute():
            gitfile = admin / gitfile
        candidates.append(gitfile.parent)
    return candidates


def _verify_record_state(
    main: Path,
    wave: Path,
    *,
    detached: bool | None = None,
    locked: bool | None = None,
    absent: bool = False,
) -> WorktreeRecord | None:
    record = _record_for(_worktree_records(main), wave)
    if absent:
        if record is not None:
            raise ValueError("target worktree record still exists")
        return None
    if record is None:
        raise ValueError("target worktree record disappeared")
    if detached is not None and record.detached != detached:
        raise ValueError("target detached state mismatch")
    if locked is not None and record.locked != locked:
        raise ValueError("target lock state mismatch")
    return record


def _delete_branch(main: Path, branch: str, tip: str) -> None:
    result = _must_git(main, "branch", "-d", "--", branch)
    output = (result.stdout + result.stderr).decode("utf-8", "replace").strip()
    match = re.fullmatch(
        rf"Deleted branch {re.escape(branch)} \(was ([0-9a-f]+)\)\.",
        output,
    )
    if match is None:
        raise ValueError("branch deletion diagnostic is malformed")
    reported = match.group(1)
    resolved = _resolve_commit(main, f"{reported}^{{commit}}")
    if resolved != tip:
        raise ValueError("branch deletion diagnostic sha differs from tested tip")


def _mutate(
    args: Args,
    state: str,
    common: Path,
    ref: str,
    initial_record: WorktreeRecord | None,
    verified: VerifiedWavePath | None,
) -> OccupancyDiagnostics | None:
    phase = "unlock"
    recheck_diagnostics: OccupancyDiagnostics | None = None
    try:
        if state in {"a", "b", "c"} and initial_record is not None and initial_record.locked:
            _must_git(args.main_worktree, "worktree", "unlock", os.fspath(args.wave_worktree))
            _verify_record_state(args.main_worktree, args.wave_worktree, locked=False)

        phase = "detach"
        if state == "a":
            _must_git(args.wave_worktree, "checkout", "--detach")
            detached_record = _verify_record_state(
                args.main_worktree, args.wave_worktree, detached=True, locked=False,
            )
            assert detached_record is not None
            if detached_record.head != args.tested_wave_tip_sha:
                raise ValueError("detached record HEAD differs from tested tip")

        phase = "recheck"
        if state in {"a", "b"}:
            assert verified is not None
            _assert_clean_and_head(args.wave_worktree, args.tested_wave_tip_sha)
            _assert_identity(args.wave_worktree, common, verified.identity)
            recheck_diagnostics = _assert_unoccupied(args.wave_worktree)

        phase = "remove-directory"
        if state in {"a", "b"}:
            assert verified is not None
            _remove_verified_tree(verified, common)
            if os.path.lexists(args.wave_worktree):
                raise ValueError("wave directory still exists")

        if state in {"a", "b", "c"}:
            phase = "prune-dry-run"
            candidates = _dry_run_candidates(args.main_worktree, common)
            existing = [path for path in candidates if path.is_dir()]
            if existing:
                raise ValueError(f"prune candidate directory still exists: {existing[0]}")
            phase = "prune"
            _must_git(args.main_worktree, "worktree", "prune", "--expire=now")
            phase = "registry"
            _verify_record_state(args.main_worktree, args.wave_worktree, absent=True)

        phase = "branch-recheck"
        if _resolve_commit(args.main_worktree, f"{ref}^{{commit}}") != args.tested_wave_tip_sha:
            raise ValueError("wave branch changed before deletion")
        ancestry = _git(args.main_worktree, "merge-base", "--is-ancestor", ref, "refs/heads/main")
        if ancestry.returncode != 0:
            raise ValueError(f"branch ancestry recheck rc={ancestry.returncode}")

        phase = "branch-delete"
        _delete_branch(args.main_worktree, args.wave_branch, args.tested_wave_tip_sha)

        phase = "postcondition"
        if os.path.lexists(args.wave_worktree):
            raise ValueError("wave path exists after cleanup")
        _verify_record_state(args.main_worktree, args.wave_worktree, absent=True)
        if _resolve_commit(args.main_worktree, f"{ref}^{{commit}}") is not None:
            raise ValueError("wave branch exists after cleanup")
        return recheck_diagnostics
    except BaseException as exc:  # noqa: BLE001 - interruption is also a partial mutation
        raise _partial(phase, exc) from exc


def _assert_already_clean(args: Args, common: Path, ref: str) -> None:
    if os.path.lexists(args.wave_worktree):
        raise ValueError("wave path appeared before already-clean result")
    if _record_for(_worktree_records(args.main_worktree), args.wave_worktree) is not None:
        raise ValueError("worktree record appeared before already-clean result")
    if _administrative_gitdirs_for_wave(common, args.wave_worktree):
        raise ValueError("worktree administrative gitdir appeared before already-clean result")
    if _resolve_commit(args.main_worktree, f"{ref}^{{commit}}") is not None:
        raise ValueError("wave branch appeared before already-clean result")


def run(argv: Sequence[str]) -> CleanupResult:
    args = _parse_argv(argv)
    try:
        state, common, ref, record, verified, preflight_diagnostics = _preflight(args)
        if state == "e":
            _assert_already_clean(args, common, ref)
    except CleanupFailure:
        raise
    except Exception as exc:  # noqa: BLE001 - fixed rejection CLI contract
        raise _reject("preflight", str(exc)) from exc
    if state == "e":
        return CleanupResult("already-clean", ())
    recheck_diagnostics = _mutate(args, state, common, ref, record, verified)
    observations: list[OccupancyObservation] = []
    if preflight_diagnostics is not None:
        observations.append(OccupancyObservation("preflight", preflight_diagnostics))
    if recheck_diagnostics is not None:
        observations.append(OccupancyObservation("recheck", recheck_diagnostics))
    return CleanupResult("removed", tuple(observations))


def _print_occupancy_diagnostic(observation: OccupancyObservation) -> None:
    diagnostics = observation.diagnostics
    print(
        "dev-wave-cleanup: diagnostic=occupancy "
        f"phase={_sanitize(observation.phase)} "
        f"cwd_permission={_sanitize(diagnostics.cwd_permission)} "
        "same_uid_cwd_unreachable="
        f"{_sanitize(json.dumps(diagnostics.same_uid_cwd_unreachable, ensure_ascii=False, sort_keys=True))}",
        file=sys.stderr,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(sys.argv[1:] if argv is None else argv)
    except CleanupFailure as exc:
        print(
            "dev-wave-cleanup: "
            f"status={exc.status} phase={_sanitize(exc.phase)} reason={_sanitize(exc.reason)}",
            file=sys.stderr,
        )
        return exc.rc
    except Exception as exc:  # noqa: BLE001 - never expose a traceback or multi-line error
        print(
            "dev-wave-cleanup: "
            f"status=rejected phase=internal reason={_sanitize(exc)}",
            file=sys.stderr,
        )
        return RC_REJECTED
    for observation in result.occupancy:
        _print_occupancy_diagnostic(observation)
    print(result.outcome)
    return 0


if __name__ == "__main__":
    sys.exit(main())
