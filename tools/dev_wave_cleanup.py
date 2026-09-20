#!/usr/bin/env python3
"""land 済み dev-wave の linked worktree と local branch を安全に撤去する。

子木 manifest は親が repo 外に書く未署名の信頼済み入力:
{"schema": "izanagi-dev-wave-child-worktrees/v1", "wave_worktree": "/absolute/wave",
 "entries": [{"path": "/absolute/child", "purpose": "author",
              "branch": "refs/heads/author", "owned_paths": ["relative/file"]}]}
path と wave_worktree は絶対・正規 path。purpose は自由文字列、branch は
refs/heads/... または null (detached)。owned_paths は repo 相対 file の閉集合で、
rename は旧新両 path を含める。exact path は作成世代を証明しない。
親は producer の終端と再投入禁止を保証する。

remove-child は統合証明済みの子 branch を専用経路の -D で削除する。
証明不能は rc=20 で木も branch も残す。wave 本体は -d のみ。
内容統合 (所有 path の tree 一致) は子 commit の main 祖先性を意味しない。
所有内容は main、所有外の最終差分は証拠 dir、中間版は同 dir の history.bundle
が担う。Git object は延命しない。撤去開始後の失敗は rc=30。
HEAD が main の祖先なら履歴は main にあるため bundle は作らない。
detached 子は bundle を作らず、木の撤去で reflog は失われる (現行どおり)。

remove-child の argv は次の4組 (path は絶対):
--main-worktree <MAIN> --manifest <MANIFEST>
--child-worktree <CHILD> --evidence-dir <EVIDENCE>
"""

from __future__ import annotations

import json
import io
import tarfile
import secrets
import hashlib
import fcntl
from contextlib import ExitStack
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, replace
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
_OCCUPANCY_MAX_SCANS = 3
_OCCUPANCY_ISSUE_FIELD_BYTES = 24
_OCCUPANCY_ISSUE_MAX_ITEMS = 3
_OCCUPANCY_ISSUE_SUMMARY_BYTES = 380


@dataclass(frozen=True)
class Args:
    main_worktree: Path
    wave_worktree: Path
    wave_branch: str
    tested_wave_tip_sha: str
    landing_wave_tip_sha: str | None


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
    cwd_deleted: object
    same_uid_cwd_unreachable: object
    retry_count: int


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
        "--landing-wave-tip-sha": "landing_tip",
    }
    if len(argv) not in {8, 10}:
        raise _usage("four required and at most one optional option-value pair are allowed")
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
    required = {"main", "wave", "branch", "tip"}
    if not required <= set(values) or set(values) - set(expected.values()):
        raise _usage("all four options are required")
    if not _SHA_RE.fullmatch(values["tip"]):
        raise _usage("tested tip must be a full lowercase 40- or 64-digit sha")
    landing_tip = values.get("landing_tip")
    if landing_tip is not None and not _SHA_RE.fullmatch(landing_tip):
        raise _usage("landing tip must be a full lowercase 40- or 64-digit sha")
    main = _validate_path_spelling(values["main"], "main-worktree", must_exist=True)
    wave = _validate_path_spelling(values["wave"], "wave-worktree", must_exist=False)
    return Args(main, wave, values["branch"], values["tip"], landing_tip)


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


def _validate_git_argv(args: Sequence[str], *, evidence: Path | None = None) -> None:
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
        ("checkout", "--detach"),
    }:
        return
    if argv in {
        ("ls-files", "--stage", "-z"), ("ls-files", "-v"),
        ("ls-files", "-z"),
        ("check-attr", "--stdin", "-z", "--all", "--"),
        ("config", "--get", "core.autocrlf"),
        ("submodule", "status", "--recursive"),
        ("status", "--porcelain", "--ignored"),
        ("status", "--porcelain=v1", "-z", "--ignored", "--untracked-files=all"),
        ("diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--no-renames", "HEAD", "--"),
        ("diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--no-renames", "--cached", "HEAD", "--"),
    }:
        return
    if (len(argv) == 3 and argv[0] == "merge-base"
            and all(_SHA_RE.fullmatch(sha) for sha in argv[1:])):
        return
    if (len(argv) == 4 and argv[:2] == ("branch", "--contains")
            and _SHA_RE.fullmatch(argv[2]) and argv[3] == "--format=%(refname)"):
        return
    if (len(argv) == 9 and argv[:6] == _CHILD_DIFF
            and all(_SHA_RE.fullmatch(sha) for sha in argv[6:8]) and argv[8] == "--"):
        return
    if (len(argv) == 4 and argv[0].startswith("--git-dir=/")
            and argv[1:3] == ("cat-file", "-e") and argv[3].endswith("^{commit}")
            and _SHA_RE.fullmatch(argv[3][:-9])):
        return
    if (len(argv) == 5 and argv[:2] == ("ls-tree", "-z")
            and _SHA_RE.fullmatch(argv[2]) and argv[3] == "--"
            and argv[4].startswith(":(literal)") and len(argv[4]) > 10):
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
        and (
            argv[3] == "refs/heads/main"
            or _SHA_RE.fullmatch(argv[3]) is not None
        )
    ):
        return
    if (
        len(argv) == 4
        and argv[:3] in {("branch", "-d", "--"), ("branch", "-D", "--")}
        and argv[3]
        and not argv[3].startswith("-")
    ):
        return
    if (len(argv) in {3, 5} and argv[0] == "bundle"
            and evidence is not None and evidence.is_absolute()
            and Path(argv[2]) == evidence / "history.bundle"
            and Path(argv[2]).is_absolute()
            and os.path.normpath(argv[2]) == argv[2]):
        if len(argv) == 3 and argv[1] == "verify":
            return
        if (len(argv) == 5 and argv[1] == "create"
                and argv[3].startswith("refs/heads/")
                and argv[3][11:] != "HEAD" and not argv[3][11:].startswith("-")
                and all(part and not part.startswith(".") and not part.endswith(".lock")
                        for part in argv[3][11:].split("/"))
                and not argv[3].endswith(".")
                and ".." not in argv[3] and "@{" not in argv[3]
                and re.search(r"[\x00-\x20\x7f~^:?*\[\\]", argv[3]) is None
                and argv[4].startswith("^") and _SHA_RE.fullmatch(argv[4][1:])):
            return
    raise RuntimeError(f"git argv is not allowlisted: {argv!r}")


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    _validate_git_argv(args)
    if tuple(args[:3]) == ("branch", "-D", "--"):
        raise RuntimeError("force deletion is reserved for integrated child removal")
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
    if gitdir.resolve(strict=True) != gitdir:
        raise ValueError("linked worktree gitdir contains symlink or noncanonical component")
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
        "invalid-target": occupancy.INDETERMINATE_RC,
    }[report.status]
    # Exercise the same JSON boundary as the standalone checker without exposing
    # this process's target-bearing argv to a second /proc scan.
    payload = json.loads(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return rc, payload


def _occupancy_issue_field(issue: object, field: str, *, limit: int) -> str:
    if type(issue) is not dict:
        return "unspecified"
    value = issue.get(field)
    if type(value) is str:
        return _sanitize(value, limit=limit)
    if field == "pid" and type(value) is int and value.bit_length() <= 80:
        return _sanitize(value, limit=limit)
    return "unspecified"


def _occupancy_issue_summary(issues: object) -> str:
    if type(issues) is list:
        issue_items = issues
        total = len(issues)
    else:
        issue_items = [None]
        total = 1
    selected = issue_items[:_OCCUPANCY_ISSUE_MAX_ITEMS]
    omitted = max(total - len(selected), 0)

    def render(field_limit: int) -> str:
        items = [
            {
                "error": _occupancy_issue_field(issue, "error", limit=field_limit),
                "source": _occupancy_issue_field(issue, "source", limit=field_limit),
                "pid": _occupancy_issue_field(issue, "pid", limit=field_limit),
            }
            for issue in selected
        ]
        encoded = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
        return (
            f"issues_total={total} issues={encoded} "
            f"issues_omitted={omitted}"
        )

    for field_limit in range(_OCCUPANCY_ISSUE_FIELD_BYTES, 11, -1):
        summary = render(field_limit)
        if len(summary.encode("utf-8")) <= _OCCUPANCY_ISSUE_SUMMARY_BYTES:
            return summary
    return f"issues_total={total} issues=[] issues_omitted={total}"


def _assert_unoccupied(path: Path) -> OccupancyDiagnostics:
    for attempt in range(1, _OCCUPANCY_MAX_SCANS + 1):
        retry_count = attempt - 1
        attempt_diagnostic = f"attempts={attempt} retry_count={retry_count}"
        try:
            rc, payload = _occupancy_payload(path)
        except CleanupFailure:
            raise
        except Exception as exc:  # noqa: BLE001 - checker failures are indeterminate
            raise _reject(
                "occupancy", f"occupancy checker failed: {exc}; {attempt_diagnostic}",
                RC_OCCUPANCY_INDETERMINATE,
            ) from exc
        expected_keys = {
            "issues", "occupants", "same_uid_cwd_unreachable", "status", "unreachable", "worktree",
        }
        if not isinstance(payload, dict) or not expected_keys <= set(payload):
            raise _reject(
                "occupancy", f"occupancy payload lacks required fields; {attempt_diagnostic}",
                RC_OCCUPANCY_INDETERMINATE,
            )
        if payload.get("worktree") != os.fspath(path):
            raise _reject(
                "occupancy", f"occupancy payload target mismatch; {attempt_diagnostic}",
                RC_OCCUPANCY_INDETERMINATE,
            )
        occupants = payload.get("occupants")
        if (
            rc == occupancy.OCCUPIED_RC
            or payload.get("status") == "occupied"
            or (isinstance(occupants, list) and bool(occupants))
        ):
            raise _reject(
                "occupancy", f"target worktree is occupied; {attempt_diagnostic}",
                RC_OCCUPIED,
            )
        issues = payload.get("issues")
        retryable = (
            payload.get("status") == "indeterminate"
            and occupants == []
            and bool(issues)
        )
        if retryable and attempt < _OCCUPANCY_MAX_SCANS:
            continue
        unreachable = payload.get("unreachable")
        valid = (
            rc == occupancy.UNOCCUPIED_RC
            and payload.get("status") == "unoccupied"
            and occupants == []
            and issues == []
        )
        if not valid:
            raise _reject(
                "occupancy",
                "occupancy result is indeterminate or inconsistent; "
                f"{attempt_diagnostic} {_occupancy_issue_summary(issues)}",
                RC_OCCUPANCY_INDETERMINATE,
            )
        if not isinstance(unreachable, dict) or "cwd_permission" not in unreachable:
            raise _reject(
                "occupancy",
                f"unreachable process diagnostics are malformed; {attempt_diagnostic}",
                RC_OCCUPANCY_INDETERMINATE,
            )
        unreachable_same_uid = payload.get("same_uid_cwd_unreachable")
        if not isinstance(unreachable_same_uid, list):
            raise _reject(
                "occupancy",
                f"same-uid unreachable process diagnostics are malformed; {attempt_diagnostic}",
                RC_OCCUPANCY_INDETERMINATE,
            )
        return OccupancyDiagnostics(
            cwd_permission=unreachable["cwd_permission"],
            cwd_deleted=unreachable.get("cwd_deleted", 0),
            same_uid_cwd_unreachable=unreachable_same_uid,
            retry_count=retry_count,
        )
    raise AssertionError("occupancy scan loop exhausted")


def _assert_clean_and_head(path: Path, tip: str) -> None:
    status_result = _must_git(
        path,
        "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none",
    )
    if status_result.stdout:
        raise ValueError("wave worktree is dirty")
    if _resolve_commit(path, "HEAD^{commit}") != tip:
        raise ValueError("wave HEAD differs from derived landing tip")


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
    return _parse_head_reflog((administrative_gitdir / "logs" / "HEAD").read_bytes())


def _parse_head_reflog(raw: bytes) -> tuple[str, ...]:
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
    if not os.path.lexists(registry):
        return ()
    if registry.resolve(strict=True) != registry or not registry.is_dir():
        raise ValueError("worktree administrative registry is not a directory")
    matches: list[Path] = []
    for candidate in registry.iterdir():
        try:
            candidate_resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"worktree administrative entry cannot be resolved: {exc}") from exc
        if candidate_resolved != candidate or not candidate.is_dir():
            raise ValueError("worktree administrative entry is not a direct directory")
        try:
            with ExitStack() as stack:
                fd = _open_directory(candidate, stack)
                raw = _read_admin_file(fd, "gitdir")
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
    landing_tip: str,
) -> str:
    if (
        directory_exists
        and record is not None
        and record.branch == ref
        and record.detached is False
        and record.head == landing_tip
        and branch_tip == landing_tip
    ):
        return "a"
    if (
        directory_exists
        and record is not None
        and record.branch is None
        and record.detached is True
        and record.head == landing_tip
        and branch_tip == landing_tip
    ):
        return "b"
    if (
        not directory_exists
        and record is not None
        and record.branch is None
        and record.detached is True
        and record.head == landing_tip
        and branch_tip == landing_tip
    ):
        return "c"
    if not directory_exists and record is None and branch_tip == landing_tip:
        return "d"
    if not directory_exists and record is None and branch_tip is None:
        return "e"
    raise ValueError("target does not match one cleanup state")


@dataclass(frozen=True)
class AdminBinding:
    common_fd: int
    registry_fd: int
    admin_fd: int | None
    name: str
    identity: tuple[int, int]
    backpointer: bytes
    commondir: bytes
    tip: str
    journal: str
    bindings: dict
    snapshot: dict
    recovery: dict | None = None
    child_proof: ChildProof | None = None


def _inode(st: os.stat_result) -> tuple[int, int]:
    return st.st_dev, st.st_ino


def _open_directory(path: str | Path, stack: ExitStack, *, parent: int | None = None) -> int:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    stack.callback(os.close, fd)
    return fd


_OBJECT_FANOUT_RE = re.compile(r"[0-9a-f]{2}\Z")
_LOOSE_OBJECT_RE = re.compile(r"(?:[0-9a-f]{38}|[0-9a-f]{62})\Z")
_PACK_OBJECT_RE = re.compile(r"pack-(?:[0-9a-f]{40}|[0-9a-f]{64})\.[a-z]+\Z")
_REGISTRY_TREE_NAMES = frozenset({"refs", "logs"})


def _is_shared_object_path(prefix: str, name: str) -> bool:
    parts = (prefix + name).split("/")
    if parts[0] != "modules" or len(parts) < 5 or parts[-3] != "objects":
        return False
    # Fail closed (rc=20) even for real stores in submodule paths containing refs/logs.
    if _REGISTRY_TREE_NAMES.intersection(parts[1:-3]):
        return False
    return bool((_OBJECT_FANOUT_RE.fullmatch(parts[-2]) and _LOOSE_OBJECT_RE.fullmatch(name))
                or (parts[-2] == "pack" and _PACK_OBJECT_RE.fullmatch(name)))


def _read_admin_file(fd: int, name: str, *, allow_shared_object: bool = False) -> bytes:
    child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        metadata = os.fstat(child)
        if (not stat.S_ISREG(metadata.st_mode)
                or (metadata.st_nlink != 1
                    and not (allow_shared_object and metadata.st_nlink > 1))):
            raise ValueError("admin entry is not a single regular file")
        with os.fdopen(os.dup(child), "rb") as stream:
            raw = stream.read()
        def stable(st):
            if allow_shared_object:
                return (st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns)
            return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_size,
                    st.st_mtime_ns, st.st_ctime_ns)

        if (stable(os.fstat(child)) != stable(metadata)
                or stable(os.stat(name, dir_fd=fd, follow_symlinks=False)) != stable(metadata)):
            raise ValueError("admin entry changed while reading")
        return raw
    finally:
        os.close(child)


def _admin_content(raw: bytes, *, semantic: bool = False) -> dict:
    content = {"length": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if semantic:
        content["raw"] = raw.hex()
    return content


def _admin_snapshot(fd: int, *, allow_locked: bool = False, prefix: str = "") -> dict:
    result = {}
    for name in sorted(os.listdir(fd)):
        if name.endswith(".lock") or name in {"locked", "MERGE_HEAD", "CHERRY_PICK_HEAD",
                                               "REVERT_HEAD", "REBASE_HEAD", "AUTO_MERGE", "MERGE_MSG",
                                               "MERGE_MODE", "SQUASH_MSG", "BISECT_START",
                                               "BISECT_LOG", "rebase-apply",
                                               "rebase-merge", "sequencer"}:
            if not (name == "locked" and allow_locked):
                raise ValueError(f"admin operation marker remains: {name}")
        metadata = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISDIR(metadata.st_mode):
            with ExitStack() as stack:
                child = _open_directory(name, stack, parent=fd)
                if _inode(os.fstat(child)) != _inode(metadata):
                    raise ValueError("admin child directory changed")
                content = _admin_snapshot(child, prefix=prefix + name + "/")
            kind = "directory"
        elif stat.S_ISREG(metadata.st_mode):
            content = _admin_content(
                _read_admin_file(
                    fd, name, allow_shared_object=_is_shared_object_path(prefix, name)),
                semantic=prefix + name in {
                    "gitdir", "commondir", "HEAD", "logs/HEAD"})
            kind = "file"
        else:
            raise ValueError("admin contains symlink or special entry")
        result[name] = [kind, list(_inode(metadata)), content]
    return result


def _journal_name(wave: Path) -> str:
    return "dev-wave-cleanup-" + hashlib.sha256(os.fsencode(wave)).hexdigest() + ".json"


def _bind_admin(args: Args, common: Path, path: Path, stack: ExitStack,
                recovery: dict | None = None) -> AdminBinding:
    if path.parent != common / "worktrees" or path.name in {"", ".", ".."}:
        raise ValueError("admin is not a single direct registry child")
    if common.resolve(strict=True) != common:
        raise ValueError("common path contains symlink")
    common_fd = _open_directory(common, stack)
    registry_fd = _open_directory("worktrees", stack, parent=common_fd)
    try:
        fd = _open_directory(path.name, stack, parent=registry_fd)
    except FileNotFoundError:
        if recovery is None:
            raise
        fd = None
    if fd is not None:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if recovery is None:
        assert fd is not None
        snapshot = _admin_snapshot(fd, allow_locked=True)
        backpointer = _read_admin_file(fd, "gitdir")
        commondir = _read_admin_file(fd, "commondir")
        identity = _inode(os.fstat(fd))
        tip = args.landing_wave_tip_sha
        assert tip is not None
    else:
        snapshot = recovery["snapshot"]
        backpointer = bytes.fromhex(snapshot["gitdir"][2]["raw"])
        commondir = bytes.fromhex(snapshot["commondir"][2]["raw"])
        identity = tuple(recovery["admin_inode"])
        tip = recovery["tip"]
        if (list(_inode(os.fstat(common_fd))) != recovery["common_inode"]
                or list(_inode(os.fstat(registry_fd))) != recovery["registry_inode"]
                or (fd is not None and _inode(os.fstat(fd)) != identity)):
            raise ValueError("recovery directory identity changed")
    for raw in (backpointer, commondir):
        if not raw or b"\x00" in raw or raw.count(b"\n") > 1:
            raise ValueError("admin binding is malformed")
    if Path(os.path.abspath(path / os.fsdecode(backpointer.rstrip(b"\n")))) != args.wave_worktree / ".git":
        raise ValueError("admin backpointer differs from wave")
    if Path(os.path.abspath(path / os.fsdecode(commondir.rstrip(b"\n")))) != common:
        raise ValueError("admin commondir differs from common")
    return AdminBinding(common_fd, registry_fd, fd, path.name, identity,
                        backpointer, commondir, tip, _journal_name(args.wave_worktree),
                        {key: snapshot[key] for key in ("gitdir", "commondir")},
                        {key: entry for key, entry in snapshot.items() if key != "locked"},
                        recovery)


def _load_admin_recovery(args: Args, common: Path, stack: ExitStack) -> AdminBinding | None:
    name = _journal_name(args.wave_worktree)
    with ExitStack() as temporary:
        fd = _open_directory(common, temporary)
        try:
            published = os.stat(name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        if (not stat.S_ISREG(published.st_mode) or published.st_uid != os.getuid()
                or published.st_mode & 0o077):
            raise ValueError("unsafe admin recovery journal")
        # Complete an interrupted link/unlink publication, only for this wave's
        # temporary names that are hard links to the published inode.
        for candidate in os.listdir(fd):
            if not candidate.startswith(name + ".tmp-"):
                continue
            metadata = os.stat(candidate, dir_fd=fd, follow_symlinks=False)
            if _inode(metadata) == _inode(published):
                os.unlink(candidate, dir_fd=fd)
                os.fsync(fd)
        raw = _read_admin_file(fd, name)
        metadata = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if (_inode(metadata) != _inode(published)
                or metadata.st_uid != os.getuid() or metadata.st_mode & 0o077):
            raise ValueError("unsafe admin recovery journal")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid admin recovery journal: incomplete or malformed JSON") from exc
    if (data["wave"] != os.fspath(args.wave_worktree) or data["branch"] != args.wave_branch
            or data["tested_tip"] != args.tested_wave_tip_sha or data["common"] != os.fspath(common)
            or not _SHA_RE.fullmatch(data["tip"])):
        raise ValueError("admin recovery request differs")
    return _bind_admin(args, common, common / "worktrees" / data["name"], stack, data)


def _assert_admin_binding(common: Path, admin: AdminBinding) -> None:
    if (_inode(os.stat(common, follow_symlinks=False)) != _inode(os.fstat(admin.common_fd))
            or _inode(os.stat("worktrees", dir_fd=admin.common_fd, follow_symlinks=False))
            != _inode(os.fstat(admin.registry_fd))):
        raise ValueError("common or registry inode changed")
    try:
        metadata = os.stat(admin.name, dir_fd=admin.registry_fd, follow_symlinks=False)
    except FileNotFoundError:
        if admin.admin_fd is None and admin.recovery is not None:
            return
        raise
    if not stat.S_ISDIR(metadata.st_mode) or _inode(metadata) != admin.identity:
        raise ValueError("admin inode changed")
    if admin.admin_fd is None or _inode(os.fstat(admin.admin_fd)) != admin.identity:
        raise ValueError("admin FD identity differs")


def _assert_snapshot_subset(current: dict, expected: dict) -> None:
    for name, entry in current.items():
        if name not in expected or entry[:2] != expected[name][:2]:
            raise ValueError("admin recovery entry identity changed")
        if entry[0] == "directory":
            _assert_snapshot_subset(entry[2], expected[name][2])
        elif entry != expected[name]:
            raise ValueError("admin recovery entry bytes changed")


def _recheck_admin(args: Args, common: Path, admin: AdminBinding) -> dict:
    _assert_admin_binding(common, admin)
    if os.path.lexists(args.wave_worktree):
        raise ValueError("wave path exists before admin removal")
    path = common / "worktrees" / admin.name
    matches = _administrative_gitdirs_for_wave(common, args.wave_worktree)
    if any(match != path for match in matches):
        raise ValueError("target administrative gitdir is not unique")
    current = _admin_snapshot(admin.admin_fd) if admin.admin_fd is not None else {}
    if admin.recovery is None:
        if matches != (path,):
            raise ValueError("admin backpointer disappeared")
        snapshot = admin.snapshot
        if current != snapshot:
            raise ValueError("admin snapshot changed since safety check")
        if any(current.get(key) != entry for key, entry in admin.bindings.items()):
            raise ValueError("admin binding inode or bytes changed since preflight")
    else:
        snapshot = admin.recovery["snapshot"]
        _assert_snapshot_subset(current, snapshot)
    if (bytes.fromhex(snapshot["gitdir"][2]["raw"]) != admin.backpointer
            or bytes.fromhex(snapshot["commondir"][2]["raw"]) != admin.commondir):
        raise ValueError("admin binding changed since preflight")
    if bytes.fromhex(snapshot["HEAD"][2]["raw"]) != (admin.tip + "\n").encode():
        raise ValueError("admin HEAD differs from detached landing tip")
    shas = _parse_head_reflog(bytes.fromhex(snapshot["logs"][2]["HEAD"][2]["raw"]))
    if admin.child_proof is None:
        _assert_reflog_commits_reachable(args.main_worktree, shas, "worktree HEAD reflog")
    else:
        _assert_child_integration(args.main_worktree, admin.child_proof, shas)
    _assert_admin_binding(common, admin)
    if admin.admin_fd is not None and _admin_snapshot(admin.admin_fd) != current:
        raise ValueError("admin changed during reachability check")
    return current


def _remove_admin_entries(fd: int, snapshot: dict, recheck, *, prefix: str = "") -> None:
    for name, (kind, identity, content) in snapshot.items():
        recheck()
        if list(_inode(os.stat(name, dir_fd=fd, follow_symlinks=False))) != identity:
            raise ValueError("admin entry changed before removal")
        if kind == "directory":
            with ExitStack() as stack:
                child = _open_directory(name, stack, parent=fd)
                if list(_inode(os.fstat(child))) != identity:
                    raise ValueError("admin child changed before removal")
                _remove_admin_entries(child, content, recheck, prefix=prefix + name + "/")
                if list(_inode(os.stat(name, dir_fd=fd, follow_symlinks=False))) != identity:
                    raise ValueError("admin child replaced during removal")
                os.rmdir(name, dir_fd=fd)
        else:
            raw = _read_admin_file(
                fd, name, allow_shared_object=_is_shared_object_path(prefix, name))
            if _admin_content(raw, semantic="raw" in content) != content:
                raise ValueError("admin file changed before removal")
            os.unlink(name, dir_fd=fd)
        os.fsync(fd)


def _rename_journal(fd: int, temporary: str, final: str) -> None:
    """Publish a complete journal atomically without replacing an existing final.

    Recovery completes interrupted link/unlink before the nlink == 1 read;
    the admin flock serializes same-wave mutation.
    """
    os.link(temporary, final, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
    os.unlink(temporary, dir_fd=fd)


def _remove_admin(args: Args, common: Path, admin: AdminBinding, snapshot: dict) -> None:
    # Persist the exact deletion set before removing HEAD/gitdir. On reentry only
    # missing entries are allowed; surviving bytes and inodes must still match.
    if _recheck_admin(args, common, admin) != snapshot:
        raise ValueError("admin changed before removal")
    data = admin.recovery or {
        "wave": os.fspath(args.wave_worktree), "branch": args.wave_branch,
        "tested_tip": args.tested_wave_tip_sha, "tip": admin.tip,
        "common": os.fspath(common), "name": admin.name,
        "common_inode": list(_inode(os.fstat(admin.common_fd))),
        "registry_inode": list(_inode(os.fstat(admin.registry_fd))),
        "admin_inode": list(admin.identity), "snapshot": snapshot,
    }
    raw = json.dumps(data, sort_keys=True).encode()
    if admin.recovery is None:
        # Unpublished temporary files are ignored on reentry. A fresh suffix
        # avoids collisions with remnants, including those from a reused PID.
        temporary = f"{admin.journal}.tmp-{os.getpid()}-{secrets.token_hex(8)}"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=admin.common_fd)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _rename_journal(admin.common_fd, temporary, admin.journal)
        os.fsync(admin.common_fd)
    if _read_admin_file(admin.common_fd, admin.journal) != raw:
        raise ValueError("admin recovery journal changed")
    _assert_admin_binding(common, admin)
    if os.path.lexists(args.wave_worktree):
        raise ValueError("wave path reappeared before admin removal")
    if admin.admin_fd is not None:
        if _admin_snapshot(admin.admin_fd) != snapshot:
            raise ValueError("admin changed before deletion")
        def recheck_remaining():
            _assert_admin_binding(common, admin)
            if os.path.lexists(args.wave_worktree):
                raise ValueError("wave path reappeared during admin removal")
            _assert_snapshot_subset(_admin_snapshot(admin.admin_fd), snapshot)

        _remove_admin_entries(admin.admin_fd, snapshot, recheck_remaining, prefix="")
        recheck_remaining()
        _assert_admin_binding(common, admin)
        os.rmdir(admin.name, dir_fd=admin.registry_fd)
        os.fsync(admin.registry_fd)
    if _record_for(_worktree_records(args.main_worktree), args.wave_worktree) is not None:
        raise ValueError("target worktree record remains after admin removal")
    if _read_admin_file(admin.common_fd, admin.journal) != raw:
        raise ValueError("admin recovery journal changed during deletion")
    os.unlink(admin.journal, dir_fd=admin.common_fd)
    os.fsync(admin.common_fd)


def _preflight(
    args: Args,
    stack: ExitStack,
) -> tuple[
    Args,
    str,
    Path,
    str,
    WorktreeRecord | None,
    VerifiedWavePath | None,
    OccupancyDiagnostics | None,
    AdminBinding | None,
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
    commit_check = _git(
        args.main_worktree,
        "cat-file",
        "-e",
        f"{args.tested_wave_tip_sha}^{{commit}}",
    )
    if commit_check.returncode != 0:
        raise ValueError("tested tip is not an existing commit object")
    if args.landing_wave_tip_sha is not None:
        optional_tip_check = _git(
            args.main_worktree,
            "cat-file",
            "-e",
            f"{args.landing_wave_tip_sha}^{{commit}}",
        )
        if optional_tip_check.returncode != 0:
            raise ValueError("optional landing tip is not an existing commit object")

    records = _worktree_records(args.main_worktree)
    if not records or records[0].path_raw != os.fsencode(args.main_worktree):
        raise ValueError("main-worktree is not the primary porcelain record")
    main_record = _record_for(records, args.main_worktree)
    if main_record is None or main_record.branch != "refs/heads/main":
        raise ValueError("main-worktree porcelain identity mismatch")
    record = _record_for(records, args.wave_worktree)
    recovery = _load_admin_recovery(args, common, stack)
    if recovery is not None:
        if os.path.lexists(args.wave_worktree):
            raise ValueError("wave path exists during admin recovery")
        record = WorktreeRecord(os.fsencode(args.wave_worktree), args.wave_worktree,
                                recovery.tip, None, True, False, True)
    path_present = os.path.lexists(args.wave_worktree)
    directory_exists = args.wave_worktree.is_dir()
    if path_present and not directory_exists:
        raise ValueError("wave path exists but is not a directory")
    ref = f"refs/heads/{args.wave_branch}"
    branch_tip = _resolve_commit(args.main_worktree, f"{ref}^{{commit}}")

    verified: VerifiedWavePath | None = None
    administrative_gitdir: Path | None = None
    if directory_exists:
        identity = _directory_identity(args.wave_worktree, common)
        verified = VerifiedWavePath(args.wave_worktree, identity)
        administrative_gitdir = identity.gitdir
        if _git_path(args.wave_worktree, "rev-parse", "--git-common-dir") != common:
            raise ValueError("wave worktree belongs to another common git-dir")
        landing_tip = _resolve_commit(args.wave_worktree, "HEAD^{commit}")
    elif record is not None:
        landing_tip = record.head
    else:
        landing_tip = branch_tip
    if landing_tip is not None and _SHA_RE.fullmatch(landing_tip) is None:
        raise ValueError("derived landing tip is not a full commit id")
    if (
        args.landing_wave_tip_sha is not None
        and landing_tip is not None
        and args.landing_wave_tip_sha != landing_tip
    ):
        raise ValueError("optional landing tip differs from derived wave HEAD")
    effective_landing_tip = landing_tip or args.tested_wave_tip_sha
    state = _classify(
        record,
        directory_exists,
        branch_tip,
        ref,
        effective_landing_tip,
    )
    verified_args = replace(args, landing_wave_tip_sha=effective_landing_tip)
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
        return verified_args, state, common, ref, record, None, None, None
    if record is not None:
        _assert_no_other_holder(records, args.wave_worktree, ref)

    assert landing_tip is not None
    commit_check = _git(
        args.main_worktree,
        "cat-file",
        "-e",
        f"{landing_tip}^{{commit}}",
    )
    if commit_check.returncode != 0:
        raise ValueError("derived landing tip is not an existing commit object")
    tested_ancestry = _git(
        args.main_worktree,
        "merge-base",
        "--is-ancestor",
        args.tested_wave_tip_sha,
        landing_tip,
    )
    if tested_ancestry.returncode != 0:
        raise ValueError(
            "tested tip is not an ancestor of the derived landing tip "
            f"(rc={tested_ancestry.returncode})"
        )
    if directory_exists:
        _assert_clean_and_head(args.wave_worktree, landing_tip)
    elif state == "c" and recovery is None:
        administrative_gitdir = _stale_administrative_gitdir(common, args.wave_worktree)
    _assert_branch_safety(args.main_worktree, ref, administrative_gitdir)
    admin = recovery
    if administrative_gitdir is not None:
        if _administrative_gitdirs_for_wave(common, args.wave_worktree) != (administrative_gitdir,):
            raise ValueError("target administrative gitdir is not unique")
        admin = _bind_admin(verified_args, common, administrative_gitdir, stack)
    if recovery is not None:
        _recheck_admin(verified_args, common, recovery)
    occupancy_diagnostics: OccupancyDiagnostics | None = None
    if directory_exists:
        occupancy_diagnostics = _assert_unoccupied(args.wave_worktree)
        assert verified is not None
        _assert_identity(args.wave_worktree, common, verified.identity)
    return (
        verified_args,
        state,
        common,
        ref,
        record,
        verified,
        occupancy_diagnostics,
        admin,
    )


def _remove_verified_tree(verified: VerifiedWavePath, common: Path) -> None:
    _assert_identity(verified.path, common, verified.identity)
    shutil.rmtree(verified.path)


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
        raise ValueError("branch deletion diagnostic sha differs from landing tip")


def _mutate(
    args: Args,
    state: str,
    common: Path,
    ref: str,
    initial_record: WorktreeRecord | None,
    verified: VerifiedWavePath | None,
    admin: AdminBinding | None,
) -> OccupancyDiagnostics | None:
    assert args.landing_wave_tip_sha is not None
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
            if detached_record.head != args.landing_wave_tip_sha:
                label = (
                    "tested tip"
                    if args.landing_wave_tip_sha == args.tested_wave_tip_sha
                    else "landing tip"
                )
                raise ValueError(f"detached record HEAD differs from {label}")

        phase = "recheck"
        if state in {"a", "b"}:
            assert verified is not None
            _assert_clean_and_head(args.wave_worktree, args.landing_wave_tip_sha)
            _assert_identity(args.wave_worktree, common, verified.identity)
            recheck_diagnostics = _assert_unoccupied(args.wave_worktree)
            assert admin is not None and admin.admin_fd is not None
            _assert_admin_binding(common, admin)
            admin = replace(admin, snapshot=_admin_snapshot(admin.admin_fd))

        phase = "remove-directory"
        if state in {"a", "b"}:
            assert verified is not None
            _remove_verified_tree(verified, common)
            if os.path.lexists(args.wave_worktree):
                raise ValueError("wave directory still exists")

        if state in {"a", "b", "c"}:
            assert admin is not None
            phase = "admin-recheck"
            snapshot = _recheck_admin(args, common, admin)
            phase = "admin-remove"
            _remove_admin(args, common, admin, snapshot)
            phase = "registry"
            _verify_record_state(args.main_worktree, args.wave_worktree, absent=True)

        phase = "branch-recheck"
        if _resolve_commit(args.main_worktree, f"{ref}^{{commit}}") != args.landing_wave_tip_sha:
            raise ValueError("wave branch changed before deletion")
        ancestry = _git(args.main_worktree, "merge-base", "--is-ancestor", ref, "refs/heads/main")
        if ancestry.returncode != 0:
            raise ValueError(f"branch ancestry recheck rc={ancestry.returncode}")

        phase = "branch-delete"
        _delete_branch(args.main_worktree, args.wave_branch, args.landing_wave_tip_sha)

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


@dataclass(frozen=True)
class ChildProof:
    head: str
    main_tip: str
    branch: str | None
    owned: tuple[str, ...]


@dataclass(frozen=True)
class ChildArgs:
    main: Path
    manifest: Path
    child: Path
    evidence: Path


def _parse_child_argv(argv: Sequence[str]) -> ChildArgs:
    names = ("--main-worktree", "--manifest", "--child-worktree", "--evidence-dir")
    if len(argv) != 8:
        raise _usage("remove-child requires four option-value pairs")
    values = {}
    for option, value in zip(argv[::2], argv[1::2]):
        if option not in names or option in values or not value or "\x00" in value:
            raise _usage("invalid or duplicate remove-child option")
        values[option] = _validate_path_spelling(value, option, must_exist=option == names[0])
    return ChildArgs(*(values[name] for name in names))


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _manifest_path(raw: object) -> Path:
    if type(raw) is not str or "\x00" in raw:
        raise ValueError("manifest path must be a string")
    try:
        return _validate_path_spelling(raw, "manifest path", must_exist=False)
    except CleanupFailure as exc:
        raise ValueError(exc.reason) from exc


def _owned_file(path: object) -> str:
    if (type(path) is not str or not path or "\x00" in path
            or path.startswith(("/", ":")) or os.path.normpath(path) != path
            or any(part in {"..", ".git"} for part in path.split("/"))
            or any(char in path for char in "*?[]") or path == "."):
        raise ValueError(f"invalid owned file: {path!r}")
    return path


def _outside_roots(path: Path, roots: Sequence[Path]) -> None:
    if any(path == root or root in path.parents for root in roots):
        raise ValueError("storage must be outside repository and registered worktrees")


def _child_manifest(args: ChildArgs, records: Sequence[WorktreeRecord], common: Path):
    """Manifest is trusted, unsigned input written by the same principal (parent).

    Exact paths are not a signed creation-generation or ownership attestation.
    Producers must have terminated and must not restart during removal.
    """
    _outside_roots(args.manifest, [common, _REPO, *(r.path for r in records)])
    raw = args.manifest.read_bytes()
    data = json.loads(raw, object_pairs_hook=_unique_json)
    if (type(data) is not dict or set(data) != {"schema", "wave_worktree", "entries"}
            or data["schema"] != "izanagi-dev-wave-child-worktrees/v1"
            or type(data["entries"]) is not list):
        raise ValueError("invalid manifest schema or fields")
    wave = _manifest_path(data["wave_worktree"])
    paths = set()
    selected = None
    for entry in data["entries"]:
        if type(entry) is not dict or set(entry) != {"path", "purpose", "branch", "owned_paths"}:
            raise ValueError("invalid manifest entry fields")
        path = _manifest_path(entry["path"])
        if path in paths:
            raise ValueError("duplicate manifest path")
        paths.add(path)
        if type(entry["purpose"]) is not str or type(entry["owned_paths"]) is not list:
            raise ValueError("invalid purpose or owned_paths type")
        branch = entry["branch"]
        if branch is not None:
            if type(branch) is not str or not branch.startswith("refs/heads/"):
                raise ValueError("invalid manifest branch")
            checked = _must_git(args.main, "check-ref-format", "--branch", branch[11:])
            if _one_line(checked, "branch") != branch[11:]:
                raise ValueError("branch normalization changed input")
        owned = tuple(_owned_file(item) for item in entry["owned_paths"])
        if len(set(owned)) != len(owned):
            raise ValueError("duplicate owned file")
        if any((path / item).is_dir() for item in owned):
            raise ValueError("owned_paths contains directory")
        if path == args.child:
            selected = entry
        elif path == wave:
            raise ValueError("manifest entry equals wave_worktree")
    if selected is None:
        raise ValueError("child path is not registered in manifest")
    return wave, selected


def _ancestor(repo: Path, sha: str, tip: str) -> bool:
    result = _git(repo, "merge-base", "--is-ancestor", sha, tip)
    if result.returncode not in {0, 1}:
        raise GitFailure(("merge-base", "--is-ancestor", sha, tip), result)
    return result.returncode == 0


def _tree_entry(repo: Path, tip: str, path: str) -> bytes:
    raw = _must_git(repo, "ls-tree", "-z", tip, "--", ":(literal)" + path).stdout
    if raw and (raw.count(b"\x00") != 1 or not raw.endswith(b"\x00")):
        raise ValueError("ambiguous tree entry")
    if raw.startswith(b"040000 "):
        raise ValueError(f"owned path is a tree: {path}")
    return raw


def _assert_child_integration(repo: Path, proof: ChildProof, shas: Sequence[str]) -> None:
    if _resolve_commit(repo, "refs/heads/main^{commit}") != proof.main_tip:
        raise ValueError("main changed since integration proof")
    if proof.branch is not None and _resolve_commit(repo, proof.branch + "^{commit}") != proof.head:
        raise ValueError("child branch changed since integration proof")
    history = tuple(dict.fromkeys((*shas, proof.head)))
    ancestry = all(_ancestor(repo, sha, proof.main_tip) for sha in history)
    mismatches = [path for path in proof.owned
                  if _tree_entry(repo, proof.head, path) != _tree_entry(repo, proof.main_tip, path)]
    owned_equal = bool(proof.owned) and not mismatches
    if not (ancestry or owned_equal):
        raise ValueError("child is not integrated; mismatched paths: " + ", ".join(mismatches)
                         + (" (empty owned_paths)" if not proof.owned else ""))
    _assert_child_history(repo, proof, history)


def _assert_child_history(repo: Path, proof: ChildProof, history: Sequence[str]) -> None:
    for sha in history:
        if not (_ancestor(repo, sha, proof.main_tip)
                or (proof.branch is not None and _ancestor(repo, sha, proof.head))):
            if _must_git(repo, "branch", "--contains", sha, "--format=%(refname)").stdout.strip():
                continue
            raise ValueError("HEAD reflog history is unreachable from main and retained branch")


def _assert_child_index(child: Path) -> None:
    flags = _must_git(child, "ls-files", "-v").stdout.splitlines()
    if any(line[:1].islower() or line[:1] == b"S" for line in flags):
        raise ValueError("assume-unchanged or skip-worktree index flag")
    for record in _must_git(child, "ls-files", "--stage", "-z").stdout.split(b"\x00"):
        if record and record.split(b"\t", 1)[0].split()[-1] != b"0":
            raise ValueError("unresolved index stage")


def _assert_child_no_conversion(child: Path) -> None:
    paths = _must_git(child, "ls-files", "-z").stdout
    argv = ("check-attr", "--stdin", "-z", "--all", "--")
    _validate_git_argv(argv)
    result = subprocess.run(["git", "-C", os.fspath(child), *argv], input=paths,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise GitFailure(argv, result)
    fields = result.stdout.split(b"\x00")
    if fields[-1] != b"" or (len(fields) - 1) % 3:
        raise ValueError("malformed conversion attributes")
    for attribute, value in zip(fields[1::3], fields[2::3]):
        if (attribute in {b"filter", b"eol", b"working-tree-encoding"}
                or (attribute == b"text" and value in {b"set", b"auto"})):
            raise ValueError("tracked file has conversion attributes")
    config = _git(child, "config", "--get", "core.autocrlf")
    if config.returncode not in {0, 1}:
        raise GitFailure(("config", "--get", "core.autocrlf"), config)
    if config.stdout.strip().lower() in {b"true", b"input"}:
        raise ValueError("core.autocrlf enables conversion")


def _assert_child_submodules(child: Path, common: Path, admin: Path,
                             primary_store: Path | None = None) -> None:
    if primary_store is None:
        primary_store = common / "modules"
    status = None
    # Enumerate pins with NUL-delimited index paths, including nested modules.
    for record in _must_git(child, "ls-files", "--stage", "-z").stdout.split(b"\x00"):
        if not record:
            continue
        metadata, rawpath = record.split(b"\t", 1)
        mode, pin, stage = metadata.split()
        if mode != b"160000":
            continue
        module = child / os.fsdecode(rawpath)
        if not os.path.lexists(module / ".git"):
            if module.exists() and any(module.iterdir()):
                raise ValueError("uninitialized submodule contains files")
            continue
        if status is None:
            status = _must_git(child, "submodule", "status", "--recursive").stdout.splitlines()
        if any(line[:1] not in {b" ", b"-"} for line in status):
            raise ValueError("submodule does not match gitlink pin")
        if _resolve_commit(module, "HEAD^{commit}") != pin.decode():
            raise ValueError("submodule HEAD differs from gitlink pin")
        if _must_git(module, "status", "--porcelain", "--ignored").stdout:
            raise ValueError("submodule contains dirty or ignored files")
        gitdir = _git_path(module, "rev-parse", "--git-dir")
        store = primary_store / os.fsdecode(rawpath)
        if gitdir == admin or admin in gitdir.parents:
            result = _git(child, "--git-dir=" + os.fspath(store), "cat-file", "-e",
                          pin.decode() + "^{commit}")
            if result.returncode != 0:
                raise ValueError("submodule pin is absent from primary module store")
        for sha in _head_reflog_shas(gitdir):
            if not _ancestor(module, sha, pin.decode()):
                if store.exists() and _git(
                        child, "--git-dir=" + os.fspath(store), "cat-file", "-e",
                        sha + "^{commit}").returncode == 0:
                    continue
                raise ValueError("submodule reflog is unreachable from gitlink pin")
        _assert_child_index(module)
        _assert_child_submodules(module, common, admin, store / "modules")


_CHILD_STATUS = ("status", "--porcelain=v1", "-z", "--ignored", "--untracked-files=all")
_CHILD_DIFF = ("diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--no-renames")


def _dirty_paths(raw: bytes) -> tuple[str, ...]:
    entries = iter(raw.split(b"\x00")[:-1])
    paths = []
    for entry in entries:
        if len(entry) < 4 or entry[2:3] != b" ":
            raise ValueError("malformed status entry")
        paths.append(os.fsdecode(entry[3:]))
        if b"R" in entry[:2] or b"C" in entry[:2]:
            paths.append(os.fsdecode(next(entries)))
    return tuple(dict.fromkeys(paths))


def _dirty_bytes(child: Path, status: bytes) -> dict[str, tuple[int, bytes]]:
    saved = {}

    def visit(relative: str):
        path = child / relative
        if path == child or child not in path.parents or ".." in path.parts:
            raise ValueError("unsafe dirty path")
        # Never traverse symlink parents, even for a path emitted by Git.
        for parent in path.parents:
            if parent == child:
                break
            if parent.is_symlink():
                raise ValueError("dirty path has symlink parent")
        try:
            st = path.lstat()
        except FileNotFoundError:
            return  # Deletions are represented in patches/status.
        if stat.S_ISDIR(st.st_mode):
            for item in sorted(path.iterdir()):
                visit(os.fspath(item.relative_to(child)))
        elif stat.S_ISLNK(st.st_mode):
            saved[relative] = (st.st_mode, os.fsencode(os.readlink(path)))
        elif stat.S_ISREG(st.st_mode):
            saved[relative] = (st.st_mode, path.read_bytes())
        else:
            raise ValueError("dirty path is a special file")

    for path in _dirty_paths(status):
        visit(path)
    return saved


def _child_payload(child: Path, proof: ChildProof):
    status = _must_git(child, *_CHILD_STATUS).stdout
    base = _one_line(_must_git(child, "merge-base", proof.main_tip, proof.head), "merge-base")
    files = {
        "committed.patch": _must_git(child, *_CHILD_DIFF, base, proof.head, "--").stdout,
        "status.txt": status,
        "tracked.patch": _must_git(child, *_CHILD_DIFF, "HEAD", "--").stdout,
        "index.patch": _must_git(child, *_CHILD_DIFF, "--cached", "HEAD", "--").stdout,
        "head-sha.txt": (proof.head + "\n").encode(),
        "branch.txt": ((proof.branch or "detached") + "\n").encode(),
    }
    return files, _dirty_bytes(child, status)


def _sync_file(path: Path, raw: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != raw:
        raise ValueError("evidence bytes differ after fsync")


def _backup_child(args: ChildArgs, proof: ChildProof, payload) -> dict[str, str]:
    """Save raw dirty bytes without following symlinks; empty directories are omitted."""
    args.evidence.mkdir(parents=True, exist_ok=True)
    files, dirty = payload
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", dereference=False) as archive:
        for name, (mode, raw) in sorted(dirty.items()):
            info = tarfile.TarInfo(name)
            info.mode = stat.S_IMODE(mode)
            if stat.S_ISLNK(mode):
                info.type = tarfile.SYMTYPE
                info.linkname = os.fsdecode(raw)
                archive.addfile(info)
            else:
                info.size = len(raw)
                archive.addfile(info, io.BytesIO(raw))
    files = {**files, "dirty.tar.gz": buffer.getvalue()}
    for name, raw in files.items():
        _sync_file(args.evidence / name, raw)
    with ExitStack() as stack:
        os.fsync(_open_directory(args.evidence, stack))
    if _child_payload(args.child, proof) != payload:
        raise ValueError("child content changed during backup")
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}


def _child_absent(args: ChildArgs, common: Path) -> None:
    if (os.path.lexists(args.child)
            or _record_for(_worktree_records(args.main), args.child) is not None
            or _administrative_gitdirs_for_wave(common, args.child)):
        raise ValueError("child path, record or admin remains")


def _child_receipt(args: ChildArgs, common: Path, entry: dict) -> bool:
    receipt = args.evidence / "removed.json"
    if not os.path.lexists(receipt):
        return False
    data = json.loads(receipt.read_bytes(), object_pairs_hook=_unique_json)
    if (data["path"] != os.fspath(args.child) or data["branch"] != entry["branch"]
            or not _SHA_RE.fullmatch(data["HEAD"])):
        raise ValueError("receipt identity mismatch")
    admin = _manifest_path(data["admin_gitdir"])
    if admin.parent != common / "worktrees" or os.path.lexists(admin):
        raise ValueError("receipt admin remains or is invalid")
    _child_absent(args, common)
    expected = {"committed.patch", "dirty.tar.gz", "tracked.patch", "index.patch", "status.txt", "head-sha.txt", "branch.txt"}
    if set(data["files"]) != expected:
        raise ValueError("receipt evidence set mismatch")
    for name, digest in data["files"].items():
        if hashlib.sha256((args.evidence / name).read_bytes()).hexdigest() != digest:
            raise ValueError("receipt evidence digest mismatch")
    if data.get("branch_deleted") is True:
        if not data["branch"] or _git(args.main, "rev-parse", "--verify",
                                       data["branch"] + "^{commit}").returncode != 128:
            raise ValueError("deleted child branch reappeared or absence is unproven")
    if data.get("history_bundle") is not None:
        bundle = args.evidence / "history.bundle"
        if (data["history_bundle"] != os.fspath(bundle)
                or hashlib.sha256(bundle.read_bytes()).hexdigest() != data["history_bundle_sha256"]):
            raise ValueError("receipt history bundle digest mismatch")
    return True


def _run_child(argv: Sequence[str], stack: ExitStack) -> CleanupResult:
    args = _parse_child_argv(argv)
    phase = "manifest"
    try:
        common = _git_path(args.main, "rev-parse", "--git-common-dir")
        records = _worktree_records(args.main)
        wave, entry = _child_manifest(args, records, common)
        phase = "evidence"
        if _child_receipt(args, common, entry):
            return CleanupResult("already-clean", ())
        phase = "preflight"
        if args.child in {args.main, wave}:
            raise ValueError("target is primary or header wave_worktree")
        if (_git_path(args.main, "rev-parse", "--git-dir") != common
                or _git_path(_REPO, "rev-parse", "--git-common-dir") != common
                or _one_line(_must_git(args.main, "symbolic-ref", "--quiet", "HEAD"), "main") != "refs/heads/main"):
            raise ValueError("main or tool common gitdir mismatch")
        record = _record_for(records, args.child)
        if record is None or record.branch != entry["branch"] or record.detached != (entry["branch"] is None):
            raise ValueError("child record or branch mismatch")
        identity = _directory_identity(args.child, common)
        if _git_path(args.child, "rev-parse", "--git-common-dir") != common:
            raise ValueError("child common gitdir mismatch")
        head = _resolve_commit(args.child, "HEAD^{commit}")
        if head != record.head:
            raise ValueError("child HEAD record mismatch")
        adapter = Args(args.main, args.child, entry["branch"] or "detached", head, head)
        admin = _bind_admin(adapter, common, identity.gitdir, stack)
        if _administrative_gitdirs_for_wave(common, args.child) != (identity.gitdir,):
            raise ValueError("child admin is not unique")
        _assert_cwd_outside(args.child)
        if any(args.child in r.path.parents for r in records):
            raise ValueError("child contains another registered worktree")
        for root in (args.main, args.child):
            fold = _git_path(root, "rev-parse", "--git-path", "izanagi-spool-fold-state.json", must_exist=False)
            if os.path.lexists(fold):
                raise ValueError("active fold state exists")
        phase = "occupancy"
        before = _assert_unoccupied(args.child)
        phase = "backup-precheck"
        _assert_child_index(args.child)
        _assert_child_no_conversion(args.child)
        _assert_child_submodules(args.child, common, identity.gitdir)
        proof = ChildProof(head, _resolve_commit(args.main, "refs/heads/main^{commit}"), entry["branch"], tuple(entry["owned_paths"]))
        payload = _child_payload(args.child, proof)
        phase = "integration"
        history = tuple(dict.fromkeys((*_head_reflog_shas(identity.gitdir), proof.head)))
        _assert_child_integration(args.main, proof, history)
        ancestry = all(_ancestor(args.main, sha, proof.main_tip) for sha in history)
        admin = replace(admin, child_proof=proof)
        phase = "evidence"
        _outside_roots(args.evidence, [common, _REPO, *(r.path for r in records)])
        if os.path.lexists(args.evidence) and (not args.evidence.is_dir() or any(args.evidence.iterdir())):
            raise ValueError("evidence directory is not empty")
    except CleanupFailure:
        raise
    except Exception as exc:
        raise _reject(phase, str(exc)) from exc
    phase = "backup"
    try:
        hashes = _backup_child(args, proof, payload)
        phase = "history-bundle"
        bundle = None
        bundle_digest = None
        bundle_reason = None
        if proof.branch is None:
            bundle_reason = "detached child has no branch ref to bundle"
        elif _ancestor(args.main, proof.head, proof.main_tip):
            bundle_reason = "child HEAD is a main ancestor"
        else:
            bundle = args.evidence / "history.bundle"
            for bundle_argv in (
                ("bundle", "create", os.fspath(bundle), proof.branch, "^" + proof.main_tip),
                ("bundle", "verify", os.fspath(bundle)),
            ):
                _validate_git_argv(bundle_argv, evidence=args.evidence)
                result = subprocess.run(
                    ["git", "-C", os.fspath(args.main), *bundle_argv],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, check=False, shell=False,
                )
                if result.returncode:
                    raise GitFailure(bundle_argv, result)
            with bundle.open("rb") as stream:
                os.fsync(stream.fileno())
            bundle_digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
            os.fsync(_open_directory(args.evidence, stack))
        phase = "unlock"
        if record.locked:
            _must_git(args.main, "worktree", "unlock", os.fspath(args.child))
            _verify_record_state(args.main, args.child, locked=False)
        phase = "detach"
        if record.branch is not None:
            _must_git(args.child, "checkout", "--detach")
        phase = "recheck"
        current = _verify_record_state(args.main, args.child, detached=True, locked=False)
        if current.head != head or _resolve_commit(args.child, "HEAD^{commit}") != head:
            raise ValueError("child HEAD changed")
        _assert_identity(args.child, common, identity)
        after = _assert_unoccupied(args.child)
        _assert_admin_binding(common, admin)
        _assert_child_index(args.child)
        if _child_payload(args.child, proof) != payload:
            raise ValueError("child content changed after backup")
        _assert_child_no_conversion(args.child)
        _assert_child_submodules(args.child, common, identity.gitdir)
        admin = replace(admin, snapshot=_admin_snapshot(admin.admin_fd))
        phase = "remove-directory"
        _remove_verified_tree(VerifiedWavePath(args.child, identity), common)
        phase = "admin-recheck"
        snapshot = _recheck_admin(adapter, common, admin)
        phase = "admin-remove"
        _remove_admin(adapter, common, admin, snapshot)
        phase = "registry"
        _verify_record_state(args.main, args.child, absent=True)
        phase = "postcondition"
        _child_absent(args, common)
        def _delete_integrated_child_branch() -> None:
            assert proof.branch is not None
            if _resolve_commit(args.main, "refs/heads/main^{commit}") != proof.main_tip:
                raise ValueError("main changed since integration proof")
            if _resolve_commit(args.main, proof.branch + "^{commit}") != proof.head:
                raise ValueError("child branch changed since integration proof")
            name = proof.branch[11:]
            argv = ("branch", "-D", "--", name)
            _validate_git_argv(argv)
            result = subprocess.run(
                ["git", "-C", os.fspath(args.main), *argv], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, shell=False,
            )
            if result.returncode:
                raise GitFailure(argv, result)
            output = (result.stdout + result.stderr).decode("utf-8", "replace").strip()
            match = re.fullmatch(rf"Deleted branch {re.escape(name)} \(was ([0-9a-f]+)\)\.", output)
            if match is None:
                raise ValueError("branch deletion diagnostic is malformed")
            if _resolve_commit(args.main, match.group(1) + "^{commit}") != proof.head:
                raise ValueError("branch deletion diagnostic sha differs from child HEAD")
            if _git(args.main, "rev-parse", "--verify", proof.branch + "^{commit}").returncode != 128:
                raise ValueError("deleted child branch remains or absence is unproven")

        if proof.branch is not None:
            phase = "branch-delete"
            _delete_integrated_child_branch()
        phase = "receipt"
        receipt = {"path": os.fspath(args.child), "branch": proof.branch, "HEAD": head,
                   "admin_gitdir": os.fspath(identity.gitdir), "files": hashes,
                   "branch_deleted": proof.branch is not None,
                   "deleted_branch_tip": proof.head if proof.branch is not None else None,
                   "integration_main_tip": proof.main_tip,
                   "integration_basis": "ancestry" if ancestry else "owned-tree-match",
                   "history_bundle": os.fspath(bundle) if bundle is not None else None,
                   "history_bundle_sha256": bundle_digest,
                   "history_bundle_reason": bundle_reason}
        temporary = args.evidence / "removed.json.tmp"
        _sync_file(temporary, json.dumps(receipt, sort_keys=True).encode() + b"\n")
        os.link(temporary, args.evidence / "removed.json")
        temporary.unlink()
        os.fsync(_open_directory(args.evidence, stack))
    except BaseException as exc:
        raise _partial(phase, exc) from exc
    return CleanupResult("removed", (OccupancyObservation("preflight", before), OccupancyObservation("recheck", after)))


def run(argv: Sequence[str]) -> CleanupResult:
    with ExitStack() as stack:
        return _run_with_stack(argv, stack)


def _run_with_stack(argv: Sequence[str], stack: ExitStack) -> CleanupResult:
    if argv and argv[0] == "remove-child":
        return _run_child(argv[1:], stack)
    args = _parse_argv(argv)
    try:
        (
            args,
            state,
            common,
            ref,
            record,
            verified,
            preflight_diagnostics,
            admin,
        ) = _preflight(args, stack)
        if state == "e":
            _assert_already_clean(args, common, ref)
    except CleanupFailure:
        raise
    except Exception as exc:  # noqa: BLE001 - fixed rejection CLI contract
        raise _reject("preflight", str(exc)) from exc
    if state == "e":
        return CleanupResult("already-clean", ())
    recheck_diagnostics = _mutate(args, state, common, ref, record, verified, admin)
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
        f"cwd_deleted={_sanitize(diagnostics.cwd_deleted)} "
        "same_uid_cwd_unreachable="
        f"{_sanitize(json.dumps(diagnostics.same_uid_cwd_unreachable, ensure_ascii=False, sort_keys=True))} "
        f"retry_count={diagnostics.retry_count}",
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
