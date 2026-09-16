#!/usr/bin/env python3
"""Visualize commits that can lose their last durable root after cleanup.

This command is read-only.  It models all ``--branch`` and
``--retire-worktree`` inputs as one cleanup operation, reports facts needed by
a human decision, and never authorizes deletion.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Sequence


SCHEMA = "izanagi-branch-rescue-v1"
LEDGER_SCHEMA = "izanagi-unreachable-object-ledger-v1"
LANDED_SCHEMA = "izanagi-branch-landed-v1"
ENCODED_GIT_VERSION = "2.34.1"
DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_ASSESSMENT_TIMEOUT_SECONDS = 8.0
DEFAULT_MAX_DELETION_LOSS_COMMITS = 4096
DEFAULT_MAX_ASSESSMENTS = 64
COMMAND_TIMEOUT_SECONDS = 8.0
OID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
PRIVATE_REF_PREFIXES = ("refs/bisect/", "refs/worktree/", "refs/rewritten/")
PSEUDOREFS = (
    "ORIG_HEAD", "FETCH_HEAD", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD",
)
GIT_COMMAND_ALLOWLIST = frozenset({
    "cat-file", "check-ref-format", "config", "count-objects", "for-each-ref", "ls-files",
    "rev-list", "rev-parse", "verify-pack", "version", "worktree",
})
GIT_CONFIG_BASE = (
    "-c", "core.hooksPath=/dev/null",
    "-c", "credential.helper=",
    "-c", "diff.external=",
    "-c", "core.fsmonitor=false",
)
AUTO_MAINTENANCE_OFF = (
    "-c", "maintenance.auto=false",
    "-c", "gc.auto=0",
)
LANDED_CHECKER_PATH = Path(__file__).with_name("check_branch_landed.py")
AUDIT_TOOL_PATH = Path(__file__).with_name("audit_dangling_commits.py")
NEVER_LOSS_FLOOR = dt.datetime.max.replace(
    hour=23, minute=59, second=59, microsecond=0, tzinfo=dt.timezone.utc,
)
COVERAGE_BOUNDARY = {
    "guarantee": "/cleanup-branches dispatcher cleanup visualization",
    "does_not_cover": [
        "manual git branch -d",
        "DW-O28 automatic retirement",
        "D978 unenacted deletion paths",
    ],
}
LEDGER_FIELDS: dict[str, object] = {
    "schema": str,
    "entry_id": str,
    "recorded_at": str,
    "source_refs": list,
    "source_tips": dict,
    "assessment_report_sha256": str,
    "object_oid": str,
    "object_type": str,
    "assessment_schema": str,
    "assessment_verdict": str,
    "assessment_reason": str,
    "storage_kind": str,
    "object_mtime": (str, type(None)),
    "loss_possible_not_before": str,
    "lower_bound_basis": str,
    "gc_auto_threshold": (int, type(None)),
    "gc_auto_sample_fanout": str,
    "gc_auto_sample_count": (int, type(None)),
    "gc_auto_sample_threshold": (int, type(None)),
    "gc_auto_heuristic_version": str,
    "loose_count_at_loss": (int, type(None)),
    "status": str,
    "resolved_at": (str, type(None)),
    "rescue_ref": (str, type(None)),
    "resolution_note": (str, type(None)),
    "object_retention_provided": bool,
}


class RescueError(Exception):
    def __init__(self, code: str, message: str, *, scope: str = "repository",
                 subject: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.scope = scope
        self.subject = subject


class CliParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self._print_message(f"{self.prog}: error: {message}\n", sys.stderr)
        raise SystemExit(64)


@dataclass(frozen=True)
class Worktree:
    path: Path
    head: str | None
    branch: str | None
    detached: bool
    bare: bool
    locked: bool
    locked_reason: str | None
    prunable: bool
    prunable_reason: str | None
    admin_dir: Path | None
    unknown_fields: tuple[str, ...]


@dataclass
class Snapshot:
    digest: str
    roots: list[dict[str, Any]]
    excluded: list[dict[str, Any]]
    worktrees: list[dict[str, Any]]
    refs: list[dict[str, str]]
    permanent_oids: set[str]
    temporary_roots: list[dict[str, Any]]
    removed_source_oids: list[tuple[str, str]]
    candidates: list[dict[str, Any]]
    complete: bool
    issues: list[dict[str, Any]]
    reflog_summary: dict[str, Any]
    index_summary: dict[str, Any]
    alternates: dict[str, Any]


def _utc_text(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _parse_now(value: str) -> dt.datetime:
    if not value.endswith("Z"):
        raise argparse.ArgumentTypeError("must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a valid RFC3339 UTC timestamp") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise argparse.ArgumentTypeError("must use UTC")
    return parsed


def _current_assessment_time() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _bounded_float(low: float, high: float):
    def parse(value: str) -> float:
        try:
            result = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a number") from exc
        if not low <= result <= high:
            raise argparse.ArgumentTypeError(f"must be between {low:g} and {high:g}")
        return result
    return parse


def _bounded_int(low: int, high: int):
    def parse(value: str) -> int:
        try:
            result = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if not low <= result <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return result
    return parse


def _issue(code: str, phase: str, message: str, *, scope: str = "repository",
           subject: str | None = None,
           affects_completeness: bool = True) -> dict[str, Any]:
    return {
        "code": code,
        "phase": phase,
        "scope": scope,
        "subject": subject,
        "message": message,
        "affects_completeness": affects_completeness,
    }


def _child_env() -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    }
    for key in (
        "HOME", "XDG_CONFIG_HOME", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_NOSYSTEM", "IZANAGI_DEV_WAVE_JOBS_DIR",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


@contextlib.contextmanager
def _no_lazy_fetch_child_env() -> Iterator[dict[str, str]]:
    env = _child_env()
    located_git = shutil.which("git", path=env["PATH"])
    if located_git is None:
        raise OSError("git executable is unavailable")
    real_git = str(Path(located_git).resolve(strict=True))
    interpreter = str(Path(sys.executable).resolve(strict=True))
    if (not Path(interpreter).is_absolute()
            or any(character.isspace() for character in interpreter)):
        raise OSError("current Python interpreter path is not usable as a shebang")
    with tempfile.TemporaryDirectory(prefix="izanagi-branch-rescue-git-") as directory:
        wrapper = Path(directory) / "git"
        wrapper.write_text(
            f"#!{interpreter}\n"
            "import os\n"
            "import sys\n"
            "os.environ['GIT_NO_LAZY_FETCH'] = '1'\n"
            f"os.execv({str(real_git)!r}, [{str(real_git)!r}, *sys.argv[1:]])\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o700)
        env["PATH"] = directory + os.pathsep + env["PATH"]
        yield env


class Git:
    """Read-only Git runner with a command allowlist checked at runtime."""

    def __init__(self, repo: Path, deadline: float) -> None:
        self.repo = repo
        self.deadline = deadline
        self.command_count = 0
        self.argv_log: list[list[str]] = []

    def remaining(self) -> float:
        return self.deadline - time.monotonic()

    def run(self, args: Sequence[str], *, allowed: Iterable[int] = (0,),
            input_data: bytes | None = None, cwd: Path | None = None,
            extra_env: dict[str, str] | None = None,
            timeout: float = COMMAND_TIMEOUT_SECONDS) -> subprocess.CompletedProcess[bytes]:
        if not args or args[0] not in GIT_COMMAND_ALLOWLIST:
            command = args[0] if args else "<empty>"
            raise RescueError("git-command-not-allowed", f"Git command is not allowed: {command}")
        if args[0] == "worktree" and list(args[1:2]) != ["list"]:
            raise RescueError("git-command-not-allowed", "only worktree list is allowed")
        remaining = self.remaining()
        if remaining <= 0:
            raise RescueError("assessment-timeout", "overall assessment deadline expired")
        env = _child_env()
        if extra_env:
            env.update(extra_env)
        observation_overrides = () if args[0] == "config" else AUTO_MAINTENANCE_OFF
        argv = ["git", *GIT_CONFIG_BASE, *observation_overrides, *args]
        self.argv_log.append(argv)
        self.command_count += 1
        try:
            result = subprocess.run(
                argv,
                cwd=cwd or self.repo,
                env=env,
                input=input_data,
                stdin=subprocess.DEVNULL if input_data is None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=min(timeout, remaining),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RescueError("git-command-timeout", f"Git command timed out: {args[0]}") from exc
        if result.returncode not in set(allowed):
            diagnostic = result.stderr.decode("utf-8", "replace").strip().splitlines()
            suffix = diagnostic[-1] if diagnostic else f"exit {result.returncode}"
            raise RescueError("git-command-error", f"{args[0]} failed: {suffix}")
        return result


def _strict_text(raw: bytes, code: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RescueError(code, "Git output is not UTF-8") from exc


def _one_path(raw: bytes, base: Path, code: str) -> Path:
    value = raw[:-1] if raw.endswith(b"\n") else raw
    if not value or b"\n" in value:
        raise RescueError(code, "Git returned an invalid path")
    text = os.fsdecode(value)
    path = Path(text)
    return (base / path).resolve() if not path.is_absolute() else path.resolve()


def _one_oid(raw: bytes, code: str) -> str:
    try:
        value = raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise RescueError(code, "Git returned a non-ASCII object id") from exc
    if OID_RE.fullmatch(value) is None:
        raise RescueError(code, "Git returned an invalid object id")
    return value


def _repo_paths(git: Git) -> tuple[Path, Path, Path, str, str]:
    root = _one_path(git.run(["rev-parse", "--show-toplevel"]).stdout, git.repo,
                     "repository-root-invalid")
    git.repo = root
    common = _one_path(git.run(["rev-parse", "--git-common-dir"]).stdout, root,
                       "common-dir-invalid")
    objects = _one_path(git.run(["rev-parse", "--git-path", "objects"]).stdout, root,
                        "objects-dir-invalid")
    object_format_raw = git.run(["rev-parse", "--show-object-format"], allowed=(0, 129)).stdout
    object_format = object_format_raw.decode("ascii", "replace").strip()
    if object_format not in {"sha1", "sha256"}:
        object_format = "sha256" if len(_one_oid(
            git.run(["rev-parse", "HEAD"]).stdout, "object-format-probe-invalid"
        )) == 64 else "sha1"
    version_text = _strict_text(git.run(["version"]).stdout, "git-version-invalid").strip()
    match = re.fullmatch(r"git version ([0-9]+(?:\.[0-9]+)+(?:\.[A-Za-z0-9.-]+)?)", version_text)
    if match is None:
        raise RescueError("git-version-invalid", "cannot parse git version")
    return root, common, objects, object_format, match.group(1)


def _parse_refs(git: Git) -> list[dict[str, str]]:
    raw = git.run([
        "for-each-ref", "--format=%(refname)%00%(objectname)%00%(objecttype)%00%(symref)%00",
    ]).stdout
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"\n":
        fields.pop()
    if len(fields) % 4:
        raise RescueError("ref-list-parse-error", "ref inventory has an incomplete record")
    refs: list[dict[str, str]] = []
    for offset in range(0, len(fields), 4):
        try:
            name = os.fsdecode(fields[offset])
            oid = fields[offset + 1].decode("ascii")
            object_type = fields[offset + 2].decode("ascii")
            symref = os.fsdecode(fields[offset + 3])
        except UnicodeDecodeError as exc:
            raise RescueError("ref-list-parse-error", "ref inventory has invalid ASCII fields") from exc
        name = name.lstrip("\n")
        if not name.startswith("refs/") or OID_RE.fullmatch(oid) is None:
            raise RescueError("ref-list-parse-error", "ref inventory has invalid fields")
        refs.append({"name": name, "oid": oid, "object_type": object_type, "symref": symref})
    return sorted(refs, key=lambda item: item["name"])


def _decode_git_quoted_path(raw: bytes) -> str:
    if not raw.startswith(b'"'):
        return os.fsdecode(raw)
    if len(raw) < 2 or not raw.endswith(b'"'):
        raise RescueError("worktree-list-parse-error", "unterminated C-quoted worktree path")
    decoded = bytearray()
    index = 1
    escapes = {
        ord("a"): 7, ord("b"): 8, ord("t"): 9, ord("n"): 10,
        ord("v"): 11, ord("f"): 12, ord("r"): 13,
        ord('"'): 34, ord("\\"): 92,
    }
    while index < len(raw) - 1:
        value = raw[index]
        if value != 92:
            decoded.append(value)
            index += 1
            continue
        index += 1
        if index >= len(raw) - 1:
            raise RescueError("worktree-list-parse-error", "invalid C-quoted worktree path")
        value = raw[index]
        if value in escapes:
            decoded.append(escapes[value])
            index += 1
            continue
        if 48 <= value <= 55:
            end = index
            while end < min(index + 3, len(raw) - 1) and 48 <= raw[end] <= 55:
                end += 1
            decoded.append(int(raw[index:end], 8))
            index = end
            continue
        raise RescueError("worktree-list-parse-error", "invalid C escape in worktree path")
    return os.fsdecode(bytes(decoded))


def _parse_worktrees(git: Git, common: Path, root: Path) -> list[Worktree]:
    raw = git.run(["worktree", "list", "--porcelain"]).stdout
    blocks = [block for block in raw.split(b"\n\n") if block.strip()]
    result: list[Worktree] = []
    for block in blocks:
        fields: dict[str, str] = {}
        detached = False
        bare = False
        unknown_fields: list[str] = []
        for raw_line in block.splitlines():
            raw_key, separator, raw_value = raw_line.partition(b" ")
            try:
                key = raw_key.decode("ascii")
            except UnicodeDecodeError:
                key = os.fsdecode(raw_key)
                unknown_fields.append(key)
                continue
            if key == "detached" and not separator:
                detached = True
            elif key == "bare" and not separator:
                bare = True
            elif key in {"worktree", "HEAD", "branch", "locked", "prunable"}:
                if key in fields:
                    raise RescueError("worktree-list-parse-error", "duplicate worktree field")
                if key in {"worktree", "HEAD", "branch"} and not separator:
                    raise RescueError("worktree-list-parse-error", f"{key} field has no value")
                fields[key] = (
                    _decode_git_quoted_path(raw_value) if key == "worktree"
                    else os.fsdecode(raw_value)
                )
            else:
                unknown_fields.append(key)
        if "worktree" not in fields or ("HEAD" not in fields and not bare):
            raise RescueError("worktree-list-parse-error", "worktree record is incomplete")
        path = Path(fields["worktree"])
        if (not path.is_absolute()
                or ("HEAD" in fields and OID_RE.fullmatch(fields["HEAD"]) is None)
                or (bare and "HEAD" in fields)):
            raise RescueError("worktree-list-parse-error", "worktree record has invalid fields")
        path = path.resolve()
        admin_dir: Path | None = None
        dotgit = path / ".git"
        try:
            if dotgit.is_file():
                first = dotgit.read_text(encoding="utf-8").strip()
                if first.startswith("gitdir: "):
                    candidate = Path(first[8:])
                    admin_dir = (path / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        except OSError:
            admin_dir = None
        if admin_dir is None and path != root:
            for candidate in sorted((common / "worktrees").glob("*")) if (common / "worktrees").is_dir() else []:
                try:
                    gitdir = Path(candidate.joinpath("gitdir").read_text(encoding="utf-8").strip()).parent.resolve()
                except (OSError, UnicodeDecodeError):
                    continue
                if gitdir == path:
                    admin_dir = candidate.resolve()
                    break
        result.append(Worktree(
            path=path,
            head=fields.get("HEAD"),
            branch=fields.get("branch"),
            detached=detached,
            bare=bare,
            locked="locked" in fields,
            locked_reason=fields.get("locked"),
            prunable="prunable" in fields,
            prunable_reason=fields.get("prunable"),
            admin_dir=admin_dir,
            unknown_fields=tuple(sorted(set(unknown_fields))),
        ))
    return sorted(result, key=lambda item: str(item.path))


def _admin_inventory(common: Path, worktrees: Sequence[Worktree], root: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    entries: list[dict[str, str]] = []
    admin_root = common / "worktrees"
    try:
        directories = sorted(path for path in admin_root.iterdir() if path.is_dir()) if admin_root.is_dir() else []
    except OSError as exc:
        return [], [_issue("worktree-admin-unreadable", "root-snapshot", str(exc))]
    listed_admin = {item.admin_dir.resolve() for item in worktrees if item.admin_dir is not None}
    disk_admin = {item.resolve() for item in directories}
    for missing in sorted(listed_admin - disk_admin):
        issues.append(_issue("worktree-admin-missing", "root-snapshot",
                             "listed worktree has no administrative entry", subject=str(missing)))
    for extra in sorted(disk_admin - listed_admin):
        issues.append(_issue("worktree-admin-unlisted", "root-snapshot",
                             "administrative entry is absent from worktree list", subject=str(extra)))
    for directory in directories:
        record = {"path": str(directory.resolve()), "head": "", "gitdir": ""}
        try:
            record["head"] = directory.joinpath("HEAD").read_text(encoding="utf-8").strip()
            record["gitdir"] = directory.joinpath("gitdir").read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(_issue("worktree-admin-unreadable", "root-snapshot", str(exc),
                                 subject=str(directory)))
        for namespace in PRIVATE_REF_PREFIXES:
            relative = namespace.removeprefix("refs/").rstrip("/")
            private_dir = directory / "refs" / relative
            try:
                private_present = private_dir.is_dir() and any(
                    path.is_file() for path in private_dir.rglob("*")
                )
            except OSError as exc:
                issues.append(_issue("private-ref-unreadable", "root-snapshot", str(exc),
                                     subject=str(private_dir)))
                private_present = False
            if private_present:
                issues.append(_issue(
                    "private-ref-present", "root-snapshot",
                    "worktree-private ref cannot be verified",
                    subject=f"{directory}:{namespace}",
                ))
        entries.append(record)
    return entries, issues


def _cat_types(git: Git, oids: Iterable[str]) -> dict[str, str | None]:
    unique = sorted(set(oids))
    if not unique:
        return {}
    request = b"".join(oid.encode("ascii") + b"\n" for oid in unique)
    raw = git.run(
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"], input_data=request,
    ).stdout
    rows = raw.decode("ascii", "strict").splitlines()
    if len(rows) != len(unique):
        raise RescueError("cat-file-parse-error", "cat-file returned the wrong row count")
    result: dict[str, str | None] = {}
    for expected, row in zip(unique, rows):
        fields = row.split()
        if fields == [expected, "missing"]:
            result[expected] = None
        elif len(fields) == 2 and fields[0] == expected:
            result[expected] = fields[1]
        else:
            raise RescueError("cat-file-parse-error", "cat-file returned an invalid row")
    return result


def _commit_oid_for_ref(git: Git, refname: str) -> str | None:
    result = git.run(
        ["rev-parse", "--verify", "--end-of-options", f"{refname}^{{commit}}"],
        allowed=(0, 128),
    )
    return _one_oid(result.stdout, "ref-peel-invalid") if result.returncode == 0 else None


def _parse_index(git: Git, worktree: Worktree) -> tuple[list[str], list[str]]:
    extra_env: dict[str, str] | None = None
    cwd = worktree.path
    if not cwd.is_dir() and worktree.admin_dir is not None:
        cwd = git.repo
        extra_env = {
            "GIT_DIR": str(worktree.admin_dir),
            "GIT_WORK_TREE": str(worktree.path),
        }
    raw = git.run(["ls-files", "--stage", "-z"], cwd=cwd, extra_env=extra_env).stdout
    object_oids: list[str] = []
    for row in (item for item in raw.split(b"\0") if item):
        try:
            meta, _path = row.split(b"\t", 1)
            _mode, oid_raw, stage = meta.split(b" ")
            oid = oid_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RescueError("index-parse-error", "index record is malformed",
                              scope="repository", subject=str(worktree.path)) from exc
        if OID_RE.fullmatch(oid) is None or stage not in {b"0", b"1", b"2", b"3"}:
            raise RescueError("index-parse-error", "index record has invalid fields",
                              subject=str(worktree.path))
        object_oids.append(oid)
    types = _cat_types(git, object_oids)
    commits = sorted(oid for oid in set(object_oids) if types.get(oid) == "commit")
    return sorted(set(object_oids)), commits


def _config_value(git: Git, key: str, default: str) -> dict[str, Any]:
    result = git.run(["config", "--show-origin", "--get-all", key], allowed=(0, 1))
    if result.returncode == 1:
        return {"raw": None, "effective": default, "source": "git-2.34.1-default",
                "default_used": True, "parsed": True}
    rows = _strict_text(result.stdout, "config-parse-error").splitlines()
    if not rows:
        raise RescueError("config-parse-error", f"cannot parse {key}")
    origin, separator, value = rows[-1].partition("\t")
    if not separator:
        fields = rows[-1].split(None, 1)
        if len(fields) != 2:
            raise RescueError("config-parse-error", f"cannot parse {key}")
        origin, value = fields
    return {"raw": value, "effective": value, "source": origin,
            "default_used": False, "parsed": True}


def _parse_integer_config(item: dict[str, Any]) -> int | None:
    try:
        value = int(str(item["effective"]))
    except ValueError:
        item["parsed"] = False
        return None
    return value


def _duration(value: str) -> dt.timedelta | None:
    normalized = value.strip().lower().replace(".", " ")
    if normalized in {"now", "now ago"}:
        return dt.timedelta(0)
    if normalized == "never":
        return None
    match = re.fullmatch(
        r"([0-9]+)\s*(seconds?|minutes?|hours?|days?|weeks?|months?)(?:\s+ago)?",
        normalized,
    )
    if match is None:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    seconds = {
        "second": 1, "seconds": 1,
        "minute": 60, "minutes": 60,
        "hour": 3600, "hours": 3600,
        "day": 86400, "days": 86400,
        "week": 604800, "weeks": 604800,
        "month": 2592000, "months": 2592000,
    }[unit]
    return dt.timedelta(seconds=amount * seconds)


def _absolute_prune_expiry(git: Git, value: str) -> dt.datetime | None:
    candidate = value.strip()
    date_only = re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", candidate)
    date_time = re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt ][0-9]{2}:[0-9]{2}"
        r"(?::[0-9]{2})?(?:Z|[+-][0-9]{2}:?[0-9]{2})?",
        candidate,
    )
    try:
        if date_only is not None:
            dt.date.fromisoformat(candidate)
        elif date_time is not None:
            normalized = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate
            dt.datetime.fromisoformat(normalized)
        else:
            return None
    except ValueError:
        return None
    result = git.run(["rev-parse", f"--since={candidate}"], allowed=(0, 128, 129))
    if result.returncode != 0:
        return None
    try:
        parsed = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise RescueError("config-parse-error", "Git returned a non-ASCII absolute expiry") from exc
    match = re.fullmatch(r"--max-age=(-?[0-9]+)", parsed)
    if match is None:
        raise RescueError("config-parse-error", "Git returned an invalid absolute expiry")
    try:
        return dt.datetime.fromtimestamp(int(match.group(1)), tz=dt.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _scoped_reflog_config(git: Git) -> list[dict[str, str]]:
    result = git.run([
        "config", "--show-origin", "--get-regexp",
        r"^gc\..*\.reflogExpire(Unreachable)?$",
    ], allowed=(0, 1))
    if result.returncode == 1:
        return []
    values: list[dict[str, str]] = []
    for line in _strict_text(result.stdout, "config-parse-error").splitlines():
        match = re.match(
            r"^(\S+)\s+gc\.(.+)\.(reflogexpire(?:unreachable)?)\s+(.*)$",
            line,
            re.IGNORECASE,
        )
        if match is None:
            raise RescueError("config-parse-error", "cannot parse scoped reflog expiry")
        setting = (
            "unreachable"
            if match.group(3).lower() == "reflogexpireunreachable"
            else "ordinary"
        )
        values.append({
            "source": match.group(1),
            "pattern": match.group(2),
            "setting": setting,
            "effective": match.group(4),
        })
    return values


def _reflog_expiry(refname: str, timestamp: dt.datetime, now: dt.datetime,
                    config: dict[str, dict[str, Any]],
                    scoped: Sequence[dict[str, str]]) -> tuple[str, str, str, str]:
    unreachable = {
        "effective": str(config["gc_reflog_expire_unreachable"]["effective"]),
        "source": str(config["gc_reflog_expire_unreachable"]["source"]),
        "name": "gc.reflogExpireUnreachable",
    }
    ordinary = {
        "effective": str(config["gc_reflog_expire"]["effective"]),
        "source": str(config["gc_reflog_expire"]["source"]),
        "name": "gc.reflogExpire",
    }
    for item in scoped:
        if not fnmatch.fnmatchcase(refname, item["pattern"]):
            continue
        suffix = (
            "reflogExpireUnreachable"
            if item["setting"] == "unreachable"
            else "reflogExpire"
        )
        selected = {
            "effective": item["effective"],
            "source": item["source"],
            "name": f"gc.{item['pattern']}.{suffix}",
        }
        if item["setting"] == "unreachable":
            unreachable = selected
        else:
            ordinary = selected
    candidates = []
    for item in (ordinary, unreachable):
        if item["effective"].strip().lower() == "never":
            continue
        span = _duration(item["effective"])
        if span is None:
            return _utc_text(now), item["name"], item["source"], "indeterminate"
        candidates.append((span, item))
    if not candidates:
        return _utc_text(NEVER_LOSS_FLOOR), "gc.reflogExpire=never", "effective-config", "determinate"
    span, chosen = min(candidates, key=lambda pair: pair[0])
    raw_deadline = timestamp + span
    return _utc_text(max(now, raw_deadline)), chosen["name"], chosen["source"], "determinate"


def _worktree_expiry(now: dt.datetime) -> tuple[str, str]:
    return _utc_text(now), "conservative-floor"


def _read_reflog(path: Path, name: str, now: dt.datetime,
                 config: dict[str, dict[str, Any]],
                 scoped: Sequence[dict[str, str]]) -> list[dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RescueError("reflog-unreadable", f"cannot read reflog: {exc}", subject=str(path)) from exc
    roots: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        meta = line.split(b"\t", 1)[0]
        fields = meta.split()
        if len(fields) < 6:
            raise RescueError("reflog-parse-error", "reflog record is malformed", subject=str(path))
        try:
            old = fields[0].decode("ascii")
            new = fields[1].decode("ascii")
            timestamp = int(fields[-2].decode("ascii"))
            timezone = fields[-1].decode("ascii")
        except (UnicodeDecodeError, ValueError) as exc:
            raise RescueError("reflog-parse-error", "reflog record has invalid fields",
                              subject=f"{path}:{line_number}") from exc
        if (OID_RE.fullmatch(old) is None or OID_RE.fullmatch(new) is None
                or re.fullmatch(r"[+-][0-9]{4}", timezone) is None):
            raise RescueError("reflog-parse-error", "reflog record has invalid ids/timezone",
                              subject=f"{path}:{line_number}")
        try:
            timestamp_value = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (ValueError, OverflowError, OSError) as exc:
            raise RescueError(
                "reflog-parse-error", "reflog timestamp is outside the supported range",
                subject=f"{path}:{line_number}",
            ) from exc
        try:
            deadline, setting, source, deadline_status = _reflog_expiry(
                name, timestamp_value, now, config, scoped,
            )
        except (OverflowError, ValueError) as exc:
            raise RescueError(
                "reflog-parse-error", "reflog expiry is outside the supported range",
                subject=f"{path}:{line_number}",
            ) from exc
        for kind, oid in (("reflog-old", old), ("reflog-new", new)):
            if set(oid) == {"0"}:
                continue
            roots.append({
                "kind": kind,
                "name": name,
                "oid": oid,
                "worktree": None,
                "reflog_timestamp": _utc_text(timestamp_value),
                "classification": "time-limited",
                "loss_possible_not_before": deadline,
                "expiry_setting": setting,
                "expiry_source": source,
                "deadline_status": deadline_status,
            })
    return roots


def _alternates(objects: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = objects / "info" / "alternates"
    issues: list[dict[str, Any]] = []
    directories: list[str] = []
    if path.exists():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                candidate = Path(line)
                resolved = (objects / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
                directories.append(str(resolved))
                if not resolved.is_dir():
                    issues.append(_issue("alternate-object-directory-unreadable", "root-snapshot",
                                         "alternate object directory is not readable", subject=str(resolved)))
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(_issue("alternates-unreadable", "root-snapshot", str(exc), subject=str(path)))
    return {
        "present": bool(directories),
        "object_directories": directories,
        "alternate_refs_used_as_roots": False,
        "inspection_complete": not issues,
    }, issues


def _config_snapshot(git: Git) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    config = {
        "gc_auto": _config_value(git, "gc.auto", "6700"),
        "gc_auto_pack_limit": _config_value(git, "gc.autoPackLimit", "50"),
        "gc_prune_expire": _config_value(git, "gc.pruneExpire", "2.weeks.ago"),
        "gc_reflog_expire": _config_value(git, "gc.reflogExpire", "90.days.ago"),
        "gc_reflog_expire_unreachable": _config_value(
            git, "gc.reflogExpireUnreachable", "30.days.ago"
        ),
        "gc_worktree_prune_expire": _config_value(
            git, "gc.worktreePruneExpire", "3.months.ago"
        ),
    }
    return config, _scoped_reflog_config(git)


def _snapshot(git: Git, root: Path, common: Path, objects: Path,
              branches: Sequence[str], retired: set[Path], now: dt.datetime,
              config: dict[str, dict[str, Any]],
              scoped: Sequence[dict[str, str]]) -> Snapshot:
    issues: list[dict[str, Any]] = []
    roots: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    permanent_oids: set[str] = set()
    temporary_roots: list[dict[str, Any]] = []
    removed_source_oids: list[tuple[str, str]] = []
    refs = _parse_refs(git)
    worktrees = _parse_worktrees(git, common, root)
    admin, admin_issues = _admin_inventory(common, worktrees, root)
    issues.extend(admin_issues)
    branch_refnames = {f"refs/heads/{name}" for name in branches}
    candidate_map: dict[str, dict[str, Any]] = {}

    for name in branches:
        refname = f"refs/heads/{name}"
        matching = [item for item in refs if item["name"] == refname]
        if len(matching) != 1:
            issues.append(_issue("candidate-ref-missing", "root-snapshot",
                                 "candidate local branch does not exist", scope="branch", subject=name))
            continue
        tip = _commit_oid_for_ref(git, refname)
        if tip is None:
            issues.append(_issue("candidate-not-commit", "root-snapshot",
                                 "candidate ref does not resolve to a commit", scope="branch", subject=name))
            continue
        candidate_map[name] = {
            "input": name,
            "refname": refname,
            "start_tip": tip,
            "end_tip": None,
            "checked_out_worktrees": [],
        }
        removed_source_oids.append((refname, tip))

    for item in refs:
        refname = item["name"]
        if refname in branch_refnames:
            excluded.append({
                "kind": "candidate-ref", "name": refname, "oid": item["oid"],
                "reason": "candidate branch ref is removed by the modeled cleanup",
                "wrong_inclusion_bias": "under-report",
            })
            continue
        if refname.startswith(PRIVATE_REF_PREFIXES):
            excluded.append({
                "kind": "worktree-private-ref", "name": refname, "oid": item["oid"],
                "reason": "private ref root semantics cannot be verified from this invocation",
                "wrong_inclusion_bias": "under-report",
            })
            issues.append(_issue("private-ref-present", "root-snapshot",
                                 "worktree-private ref cannot be verified", subject=refname))
            continue
        if refname.startswith("refs/replace/"):
            issues.append(_issue("replace-ref-present", "root-snapshot",
                                 "replacement refs make the commit graph non-canonical", subject=refname))
            continue
        commit_oid = _commit_oid_for_ref(git, refname)
        if commit_oid is not None:
            permanent_oids.add(commit_oid)
            roots.append({
                "kind": "ref", "name": refname, "oid": commit_oid,
                "worktree": None, "reflog_timestamp": None,
                "classification": "permanent",
                "loss_possible_not_before": None,
                "expiry_setting": None, "expiry_source": None,
                "deadline_status": "not-applicable",
            })

    worktree_rows: list[dict[str, Any]] = []
    all_index_oids: set[str] = set()
    all_index_commits: set[str] = set()
    for worktree in worktrees:
        is_retired = worktree.path in retired
        checked_out_name = (
            worktree.branch.removeprefix("refs/heads/") if worktree.branch else None
        )
        if checked_out_name in candidate_map:
            candidate_map[checked_out_name]["checked_out_worktrees"].append(str(worktree.path))
        if worktree.unknown_fields:
            issues.append(_issue(
                "worktree-record-unknown-field", "root-snapshot",
                "worktree record contains unknown fields: "
                + ", ".join(worktree.unknown_fields),
                subject=str(worktree.path),
                affects_completeness=is_retired,
            ))
        if worktree.bare:
            index_oids, index_commits = [], []
            inspection_complete = not worktree.unknown_fields
        else:
            try:
                index_oids, index_commits = _parse_index(git, worktree)
                inspection_complete = not worktree.unknown_fields
            except RescueError as exc:
                index_oids, index_commits, inspection_complete = [], [], False
                issues.append(_issue(exc.code, "root-snapshot", exc.message,
                                     subject=str(worktree.path)))
        all_index_oids.update(index_oids)
        all_index_commits.update(index_commits)
        classification = (
            "permanent" if worktree.unknown_fields else
            "removed" if is_retired else
            "time-limited" if worktree.prunable else "permanent"
        )
        worktree_rows.append({
            "path": str(worktree.path), "head": worktree.head,
            "branch": worktree.branch, "detached": worktree.detached,
            "bare": worktree.bare,
            "locked": worktree.locked, "locked_reason": worktree.locked_reason,
            "prunable": worktree.prunable, "prunable_reason": worktree.prunable_reason,
            "retired": is_retired, "unknown_fields": list(worktree.unknown_fields),
            "root_classification": classification,
            "index_object_count": len(index_oids),
            "index_commit_root_count": len(index_commits),
            "inspection_complete": inspection_complete,
        })
        if worktree.bare:
            continue
        assert worktree.head is not None
        if worktree.unknown_fields:
            for kind, oid in [
                ("worktree-head", worktree.head),
                *[("index-commit", value) for value in index_commits],
            ]:
                permanent_oids.add(oid)
                roots.append({
                    "kind": kind, "name": str(worktree.path), "oid": oid,
                    "worktree": str(worktree.path), "reflog_timestamp": None,
                    "classification": "permanent", "loss_possible_not_before": None,
                    "expiry_setting": None, "expiry_source": None,
                    "deadline_status": "not-applicable",
                })
        elif is_retired:
            removed_source_oids.append((f"worktree:{worktree.path}", worktree.head))
            removed_source_oids.extend(
                (f"worktree-index:{worktree.path}", oid) for oid in index_commits
            )
            excluded.append({
                "kind": "retired-worktree-head", "name": str(worktree.path),
                "oid": worktree.head,
                "reason": "retired worktree HEAD is removed by the modeled cleanup",
                "wrong_inclusion_bias": "under-report",
            })
            excluded.extend({
                "kind": "retired-worktree-index", "name": str(worktree.path),
                "oid": oid,
                "reason": "retired worktree index is removed by the modeled cleanup",
                "wrong_inclusion_bias": "under-report",
            } for oid in index_commits)
        elif worktree.prunable:
            deadline, deadline_status = _worktree_expiry(now)
            for kind, oid in [("worktree-head", worktree.head), *[("index-commit", value) for value in index_commits]]:
                entry = {
                    "kind": kind, "name": str(worktree.path), "oid": oid,
                    "worktree": str(worktree.path), "reflog_timestamp": None,
                    "classification": "time-limited",
                    "loss_possible_not_before": deadline,
                    "expiry_setting": "gc.worktreePruneExpire",
                    "expiry_source": config["gc_worktree_prune_expire"]["source"],
                    "deadline_status": deadline_status,
                }
                roots.append(entry)
                temporary_roots.append(entry)
        else:
            for kind, oid in [("worktree-head", worktree.head), *[("index-commit", value) for value in index_commits]]:
                permanent_oids.add(oid)
                roots.append({
                    "kind": kind, "name": str(worktree.path), "oid": oid,
                    "worktree": str(worktree.path), "reflog_timestamp": None,
                    "classification": "permanent", "loss_possible_not_before": None,
                    "expiry_setting": None, "expiry_source": None,
                    "deadline_status": "not-applicable",
                })

    listed_paths = {item.path for item in worktrees}
    for path in sorted(retired - listed_paths):
        issues.append(_issue("retire-worktree-not-registered", "root-snapshot",
                             "retirement target is not a registered worktree", subject=str(path)))

    reflog_file_count = 0
    excluded_candidate_file_count = 0
    reflog_root_count = 0
    logs_refs = common / "logs" / "refs"
    if logs_refs.exists():
        try:
            reflog_paths = sorted(path for path in logs_refs.rglob("*") if path.is_file())
        except OSError as exc:
            reflog_paths = []
            issues.append(_issue("reflog-enumeration-error", "root-snapshot", str(exc)))
        for path in reflog_paths:
            refname = "refs/" + path.relative_to(logs_refs).as_posix()
            if refname in branch_refnames:
                excluded_candidate_file_count += 1
                try:
                    entries = _read_reflog(path, refname, now, config, scoped)
                    types = _cat_types(git, (entry["oid"] for entry in entries))
                except RescueError as exc:
                    issues.append(_issue(exc.code, "root-snapshot", exc.message,
                                         subject=exc.subject))
                    continue
                for entry in entries:
                    oid = entry["oid"]
                    excluded.append({
                        "kind": "candidate-reflog", "name": refname, "oid": oid,
                        "reason": "candidate branch reflog is removed with its ref",
                        "wrong_inclusion_bias": "under-report",
                    })
                    object_type = types.get(oid)
                    if object_type is None:
                        issues.append(_issue(
                            "removed-reflog-object-missing", "root-snapshot",
                            "candidate reflog object is missing and cannot be classified",
                            subject=f"{refname}:{oid}",
                        ))
                    elif object_type == "commit":
                        removed_source_oids.append((f"candidate-reflog:{refname}", oid))
                continue
            reflog_file_count += 1
            try:
                entries = _read_reflog(path, refname, now, config, scoped)
            except RescueError as exc:
                issues.append(_issue(exc.code, "root-snapshot", exc.message, subject=exc.subject))
                continue
            if any(entry["deadline_status"] == "indeterminate" for entry in entries):
                issues.append(_issue(
                    "reflog-expiry-indeterminate", "root-snapshot",
                    "reflog expiry lower bound could not be parsed", subject=refname,
                ))
            roots.extend(entries)
            temporary_roots.extend(entries)
            reflog_root_count += len(entries)

    for worktree in worktrees:
        if worktree.bare:
            continue
        head_log = (
            worktree.admin_dir / "logs" / "HEAD" if worktree.admin_dir is not None
            else common / "logs" / "HEAD"
        )
        if not head_log.exists():
            continue
        reflog_file_count += 1
        try:
            entries = _read_reflog(
                head_log, f"worktree:{worktree.path}:HEAD", now, config, scoped,
            )
        except RescueError as exc:
            issues.append(_issue(exc.code, "root-snapshot", exc.message, subject=exc.subject))
            continue
        for entry in entries:
            entry["worktree"] = str(worktree.path)
        if worktree.path in retired:
            types = _cat_types(git, (entry["oid"] for entry in entries))
            for entry in entries:
                oid = entry["oid"]
                object_type = types.get(oid)
                if object_type is None:
                    issues.append(_issue(
                        "removed-reflog-object-missing", "root-snapshot",
                        "retired worktree reflog object is missing and cannot be classified",
                        subject=f"{worktree.path}:{oid}",
                    ))
                elif object_type == "commit":
                    removed_source_oids.append((f"worktree-reflog:{worktree.path}", oid))
                excluded.append({
                    "kind": "retired-worktree-reflog", "name": entry["name"],
                    "oid": oid,
                    "reason": "retired worktree reflog is removed by the modeled cleanup",
                    "wrong_inclusion_bias": "under-report",
                })
            continue
        if worktree.prunable:
            worktree_deadline, worktree_status = _worktree_expiry(now)
            for entry in entries:
                if worktree_deadline <= entry["loss_possible_not_before"]:
                    entry["loss_possible_not_before"] = worktree_deadline
                    entry["deadline_status"] = worktree_status
                    entry["expiry_setting"] = "gc.worktreePruneExpire"
                    entry["expiry_source"] = config["gc_worktree_prune_expire"]["source"]
        if any(entry["deadline_status"] == "indeterminate" for entry in entries):
            issues.append(_issue(
                "worktree-reflog-expiry-indeterminate", "root-snapshot",
                "worktree reflog expiry lower bound could not be parsed",
                subject=str(worktree.path),
            ))
        roots.extend(entries)
        temporary_roots.extend(entries)
        reflog_root_count += len(entries)

    for pseudoref in PSEUDOREFS:
        path = common / pseudoref
        if path.exists():
            oid: str | None = None
            try:
                candidate = path.read_text(encoding="ascii").strip()
                oid = candidate if OID_RE.fullmatch(candidate) else None
            except (OSError, UnicodeDecodeError):
                pass
            excluded.append({
                "kind": "non-root-pseudoref", "name": pseudoref, "oid": oid,
                "reason": "non-ref pseudoref is outside the verified durable root set",
                "wrong_inclusion_bias": "under-report",
            })

    shallow = common / "shallow"
    grafts = common / "info" / "grafts"
    try:
        if shallow.is_file() and shallow.stat().st_size:
            issues.append(_issue("shallow-repository", "root-snapshot",
                                 "shallow history makes the closure indeterminate", subject=str(shallow)))
        if grafts.is_file() and grafts.stat().st_size:
            issues.append(_issue("grafts-present", "root-snapshot",
                                 "grafts make the commit graph non-canonical", subject=str(grafts)))
    except OSError as exc:
        issues.append(_issue("repository-preflight-error", "root-snapshot", str(exc)))

    alternates, alternate_issues = _alternates(objects)
    issues.extend(alternate_issues)
    canonical = {
        "refs": refs,
        "worktrees": worktree_rows,
        "admin": admin,
        "roots": roots,
        "excluded": excluded,
        "alternates": alternates,
    }
    digest = hashlib.sha256(json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()
    return Snapshot(
        digest=digest,
        roots=roots,
        excluded=excluded,
        worktrees=worktree_rows,
        refs=refs,
        permanent_oids=permanent_oids,
        temporary_roots=temporary_roots,
        removed_source_oids=removed_source_oids,
        candidates=[candidate_map[name] for name in branches if name in candidate_map],
        complete=not any(item["affects_completeness"] for item in issues),
        issues=issues,
        reflog_summary={
            "included_file_count": reflog_file_count,
            "excluded_candidate_file_count": excluded_candidate_file_count,
            "root_oid_count": reflog_root_count,
            "inspection_complete": not any(item["code"].startswith("reflog-") for item in issues),
        },
        index_summary={
            "object_count": len(all_index_oids),
            "commit_root_count": len(all_index_commits),
            "inspection_complete": all(row["inspection_complete"] for row in worktree_rows),
        },
        alternates=alternates,
    )


def _closure(git: Git, snapshot: Snapshot, limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    positive = []
    positive_names: list[str] = []
    seen_positive: set[str] = set()
    for name, oid in snapshot.removed_source_oids:
        if oid not in seen_positive:
            positive.append(oid)
            seen_positive.add(oid)
        positive_names.append(name)
    if not positive:
        return [], {
            "definition": "reachable-from-all-candidate-tips-minus-post-delete-gc-commit-roots",
            "complete": True, "limit": limit, "observed_commit_count": 0,
            "commit_count": 0, "commits": [], "stdin_positive_oids": [],
            "stdin_negative_oids": sorted(snapshot.permanent_oids),
        }
    stdin_lines = [*positive, *(f"^{oid}" for oid in sorted(snapshot.permanent_oids))]
    result = git.run([
        "rev-list", "--topo-order", "--reverse", "--parents",
        f"--max-count={limit + 1}", "--stdin",
    ], input_data=("\n".join(stdin_lines) + "\n").encode("ascii"))
    try:
        rows = result.stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise RescueError("closure-parse-error", "closure output is not ASCII") from exc
    commits: list[dict[str, Any]] = []
    for row in rows:
        fields = row.split()
        if not fields or any(OID_RE.fullmatch(value) is None for value in fields):
            raise RescueError("closure-parse-error", "closure row is malformed")
        commits.append({
            "oid": fields[0], "parents": fields[1:],
            "source_candidate_refs": sorted(set(positive_names)),
        })
    complete = len(commits) <= limit
    return commits, {
        "definition": "reachable-from-all-candidate-tips-minus-post-delete-gc-commit-roots",
        "complete": complete,
        "limit": limit,
        "observed_commit_count": len(commits),
        "commit_count": len(commits) if complete else None,
        "commits": commits,
        "stdin_positive_oids": positive,
        "stdin_negative_oids": sorted(snapshot.permanent_oids),
    }


def _count_objects(git: Git) -> dict[str, Any]:
    text = _strict_text(git.run(["count-objects", "-v"]).stdout, "count-objects-parse-error")
    values: dict[str, int] = {}
    for line in text.splitlines():
        key, separator, raw = line.partition(": ")
        if separator and re.fullmatch(r"[0-9]+", raw):
            values[key] = int(raw)
    mapping = {
        "count": "count", "size_kib": "size", "in_pack": "in-pack",
        "packs": "packs", "size_pack_kib": "size-pack",
        "prune_packable": "prune-packable", "garbage": "garbage",
        "size_garbage_kib": "size-garbage",
    }
    result = {out: values.get(source) for out, source in mapping.items()}
    result["parsed_complete"] = all(value is not None for value in result.values())
    return result


def _gc_observation(git: Git, objects: Path, git_version: str,
                    config: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    count = _count_objects(git)
    auto = _parse_integer_config(config["gc_auto"])
    pack_limit = _parse_integer_config(config["gc_auto_pack_limit"])
    sample_path = objects / "17"
    try:
        sample_count = sum(1 for _ in sample_path.iterdir()) if sample_path.is_dir() else 0
    except OSError as exc:
        sample_count = None
        issues.append(_issue("gc-auto-sample-unreadable", "gc", str(exc), subject=str(sample_path)))
    threshold = math.ceil(auto / 256) if auto is not None and auto > 0 else 0 if auto is not None else None
    if auto is not None and auto <= 0:
        proximity = "disabled"
        may_trigger = False
    elif git_version != ENCODED_GIT_VERSION or sample_count is None or threshold is None:
        proximity = "indeterminate"
        may_trigger: bool | None = None
    elif sample_count >= threshold:
        proximity = "at-or-above"
        may_trigger = True
    elif sample_count * 10 >= threshold * 9:
        proximity = "within-10-percent"
        may_trigger = False
    else:
        proximity = "below-90-percent"
        may_trigger = False
    if auto is None or pack_limit is None or not count["parsed_complete"]:
        issues.append(_issue("gc-config-indeterminate", "gc", "gc configuration could not be parsed"))
    if git_version != ENCODED_GIT_VERSION:
        issues.append(_issue(
            "gc-auto-version-mismatch", "gc",
            "running Git version does not match the encoded sample heuristic",
            subject=git_version,
        ))
    return {
        "config": config,
        "count_objects": count,
        "auto_trigger": {
            "heuristic": "git-2.34.1-fanout-17-sample",
            "encoded_git_version": ENCODED_GIT_VERSION,
            "running_git_version": git_version,
            "version_matches": git_version == ENCODED_GIT_VERSION,
            "enabled": None if auto is None else auto > 0,
            "sample_fanout": "17",
            "sample_entry_count": sample_count,
            "threshold": threshold,
            "headroom": None if threshold is None or sample_count is None else max(threshold - sample_count, 0),
            "total_loose_count_observation": count["count"],
            "proximity": proximity,
            "next_eligible_git_command_may_trigger": may_trigger,
            "caveat": "fanout sample heuristic is not a time or object-retention guarantee",
        },
        "auto_pack": {
            "threshold": pack_limit,
            "pack_count": count["packs"],
            "at_or_above": None if pack_limit is None else count["packs"] >= pack_limit,
        },
    }, issues


def _pack_index(git: Git, object_directories: Sequence[Path]) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    result: dict[str, Path] = {}
    issues: list[dict[str, Any]] = []
    for directory in object_directories:
        pack_dir = directory / "pack"
        try:
            indexes = sorted(pack_dir.glob("*.idx")) if pack_dir.is_dir() else []
        except OSError as exc:
            issues.append(_issue("pack-enumeration-error", "retention", str(exc), subject=str(pack_dir)))
            continue
        for index in indexes:
            try:
                output = git.run(["verify-pack", "-v", str(index)]).stdout.decode("ascii", "strict")
            except (RescueError, UnicodeDecodeError) as exc:
                issues.append(_issue("pack-index-unreadable", "retention", str(exc), subject=str(index)))
                continue
            pack_path = index.with_suffix(".pack")
            for line in output.splitlines():
                fields = line.split()
                if fields and OID_RE.fullmatch(fields[0]):
                    result.setdefault(fields[0], pack_path)
    return result, issues


def _retention(git: Git, oid: str, now: dt.datetime, objects: Path,
               alternate_dirs: Sequence[Path], pack_map: dict[str, Path],
               prune_config: dict[str, Any], temporary_roots: Sequence[dict[str, Any]],
               *, absolute_prune_expiry: dt.datetime | None = None) -> tuple[dict[str, Any], bool]:
    object_type = _cat_types(git, [oid]).get(oid)
    loose = objects / oid[:2] / oid[2:]
    alternate_loose = next((directory / oid[:2] / oid[2:] for directory in alternate_dirs
                            if (directory / oid[:2] / oid[2:]).is_file()), None)
    pack = pack_map.get(oid)
    loose_exists = loose.is_file()
    if loose_exists and pack is not None:
        storage = "loose-and-packed"
    elif loose_exists:
        storage = "loose"
    elif pack is not None and (pack == objects or objects in pack.parents):
        storage = "packed"
    elif alternate_loose is not None or pack is not None or (object_type is not None and alternate_dirs):
        storage = "alternate"
    elif object_type is None:
        storage = "missing"
    else:
        storage = "indeterminate"
    loose_mtime: dt.datetime | None = None
    if loose_exists:
        try:
            before = loose.stat()
            after = loose.stat()
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
            ):
                raise OSError("loose object changed during inspection")
            loose_mtime = dt.datetime.fromtimestamp(before.st_mtime, tz=dt.timezone.utc)
        except OSError:
            storage = "indeterminate"
            loose_mtime = None
    pack_mtime: dt.datetime | None = None
    if pack is not None:
        try:
            pack_mtime = dt.datetime.fromtimestamp(pack.stat().st_mtime, tz=dt.timezone.utc)
        except OSError:
            pack_mtime = None
    prune_value = str(prune_config["effective"]).strip().lower()
    span = _duration(prune_value)
    lower_bound: dt.datetime | None
    if object_type != "commit" or storage in {"missing", "indeterminate"}:
        lower_bound = None
        basis = "unavailable"
        status = "indeterminate"
        reason = (
            "cat-file did not classify the object as a commit" if object_type != "commit"
            else "object storage could not be classified"
        )
    elif storage == "loose" and loose_mtime is not None and prune_value == "never":
        lower_bound = NEVER_LOSS_FLOOR
        basis = "gc-prune-expire-never"
        status = "determinate"
        reason = "gc.pruneExpire=never makes the storage lower bound unbounded"
    elif storage == "loose" and loose_mtime is not None and span is not None:
        lower_bound = max(now, loose_mtime + span)
        basis = "loose-object-mtime-plus-prune-expire"
        status = "determinate"
        reason = "loose object mtime and gc.pruneExpire provide a lower bound"
    elif storage == "loose" and loose_mtime is not None and absolute_prune_expiry is not None:
        lower_bound = now if loose_mtime <= absolute_prune_expiry else NEVER_LOSS_FLOOR
        basis = "loose-object-mtime-vs-absolute-prune-expire"
        status = "determinate"
        reason = "loose object mtime and absolute gc.pruneExpire cutoff provide a lower bound"
    else:
        lower_bound = now
        basis = (
            "alternate-object-database-assessment-time-conservative-floor"
            if storage == "alternate" else "assessment-time-conservative-floor"
        )
        status = "conservative-floor"
        reason = {
            "packed": "pack mtime is not an object-specific unreachable time",
            "loose-and-packed": "packed copy prevents a determinate object-specific deadline",
            "alternate": "alternate object retention is controlled outside this repository",
            "loose": "gc.pruneExpire could not be parsed",
        }.get(storage, "object-specific retention cannot be observed")
    additional = [
        {
            "kind": item["kind"], "name": item["name"], "oid": item["oid"],
            "loss_possible_not_before": item["loss_possible_not_before"],
            "expiry_setting": item["expiry_setting"],
            "expiry_source": item["expiry_source"],
            "deadline_status": item["deadline_status"],
        }
        for item in temporary_roots if item["oid"] == oid
    ]
    usable_additional = [
        item for item in additional
        if item["deadline_status"] != "indeterminate"
        and item["loss_possible_not_before"] is not None
    ]
    if lower_bound is not None and usable_additional:
        source_floor = max(
            dt.datetime.fromisoformat(
                item["loss_possible_not_before"][:-1] + "+00:00"
            )
            for item in usable_additional
        )
        lower_bound = max(lower_bound, source_floor)
    complete = status != "indeterminate"
    return {
        "storage_kind": storage,
        "cat_file_type": object_type if object_type == "commit" else None,
        "loose_path": str(loose) if loose_exists else None,
        "loose_mtime": _utc_text(loose_mtime) if loose_mtime else None,
        "pack_path": str(pack) if pack is not None else None,
        "pack_mtime_observed": _utc_text(pack_mtime) if pack_mtime else None,
        "loss_possible_not_before": _utc_text(lower_bound) if lower_bound is not None else None,
        "lower_bound_basis": basis,
        "deadline_status": status,
        "reason": reason,
        "additional_sources": additional,
    }, complete


def _empty_landed(reason: str, elapsed: float = 0.0) -> dict[str, Any]:
    return {
        "schema": LANDED_SCHEMA,
        "verdict": "indeterminate",
        "reason": reason,
        "conclusive": False,
        "checker_rc": None,
        "elapsed_seconds": round(elapsed, 6),
        "corpus_bytes_read": None,
        "report_sha256": None,
        "manual_review_required": True,
        "complete": False,
        "unproven_unit_details": _unproven_unit_details(None),
    }


def _unproven_unit_details(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Bounded explanation only; never contributes to the assessment decision."""
    limit = 100
    result: dict[str, Any] = {
        "units": [], "reason_counts": {}, "unit_limit": limit,
        "unproven_count": None, "truncated": False, "complete": False,
        "missing_reason": "child-report-unavailable",
    }
    if payload is None:
        return result
    units = payload.get("proof_units")
    summary = payload.get("summary")
    if not isinstance(units, list):
        result["missing_reason"] = "proof-units-unavailable"
        return result
    valid = True
    count = 0
    for unit in units:
        if not isinstance(unit, dict) or not isinstance(unit.get("decision"), dict):
            valid = False
            continue
        if unit["decision"].get("verdict") == "landed":
            continue
        count += 1
        reason = unit["decision"].get("reason")
        if not isinstance(reason, str):
            valid = False
            reason = "unit-reason-unavailable"
        result["reason_counts"][reason] = result["reason_counts"].get(reason, 0) + 1
        evidence = unit.get("evidence")
        if not isinstance(evidence, list):
            valid = False
            evidence = []
        layers = [
            {key: layer.get(key) for key in (
                "layer", "decisive", "outcome", "reason", "candidate_count", "candidate_limit",
                "matched_commit",
            )}
            for layer in evidence if isinstance(layer, dict) and (
                layer.get("decisive") is True
                or (layer.get("layer") == "exact-tree-state"
                    and layer.get("outcome") != "not-applicable")
            )
        ]
        if not layers or any(key not in unit for key in ("commit", "path", "change", "required_state")):
            valid = False
        if len(result["units"]) < limit:
            result["units"].append({
                **{key: unit.get(key) for key in ("commit", "path", "change", "required_state")},
                "decision": {"reason": reason}, "evidence": layers,
            })
    result["unproven_count"] = count
    result["truncated"] = count > limit
    enumerated = (isinstance(summary, dict) and summary.get("files_enumerated") is True
                  and summary.get("proof_units") == len(units))
    result["complete"] = valid and enumerated and not result["truncated"]
    result["missing_reason"] = (
        None if result["complete"] else "unit-output-limit" if result["truncated"]
        else "proof-unit-details-incomplete"
    )
    return result


def _landed_assessment(repo: Path, checker: Path, oid: str, timeout: float,
                       overall_remaining: float) -> dict[str, Any]:
    started = time.monotonic()
    if overall_remaining <= 0:
        return _empty_landed("overall-timeout")
    try:
        with _no_lazy_fetch_child_env() as child_env:
            python_env = {
                **child_env,
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            result = subprocess.run(
                [sys.executable, str(checker), "--repo", str(repo),
                 "--timeout-seconds", str(timeout), oid],
                cwd=repo,
                env=python_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=min(timeout, overall_remaining),
                check=False,
            )
    except subprocess.TimeoutExpired:
        return _empty_landed("checker-timeout", time.monotonic() - started)
    except OSError:
        return _empty_landed("checker-launch-error", time.monotonic() - started)
    elapsed = time.monotonic() - started
    if result.returncode not in {0, 1, 2} or result.stdout.count(b"\n") != 1:
        return _empty_landed("checker-contract-invalid", elapsed)
    try:
        payload = json.loads(result.stdout)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _empty_landed("checker-json-invalid", elapsed)
    if not isinstance(payload, dict) or payload.get("schema") != LANDED_SCHEMA:
        return _empty_landed("checker-schema-invalid", elapsed)
    decision = payload.get("decision")
    if not isinstance(decision, dict):
        return _empty_landed("checker-decision-invalid", elapsed)
    verdict = decision.get("verdict")
    expected = {"landed": 0, "not-landed": 1, "indeterminate": 2}
    if (not isinstance(verdict, str)
            or verdict not in expected
            or expected[verdict] != result.returncode):
        return _empty_landed("checker-rc-verdict-mismatch", elapsed)
    branch = payload.get("branch")
    if (not isinstance(branch, dict)
            or branch.get("input") != oid
            or branch.get("tip") != oid):
        return _empty_landed("checker-target-contract-invalid", elapsed)
    expected_conclusive = verdict != "indeterminate"
    if decision.get("conclusive") is not expected_conclusive:
        return _empty_landed("checker-conclusive-contract-invalid", elapsed)
    if payload.get("branch_delete_authorized") is not False:
        return _empty_landed("checker-authorization-contract-invalid", elapsed)
    observations = payload.get("observations", {})
    corpus = observations.get("ledger_corpus", {}) if isinstance(observations, dict) else {}
    return {
        "schema": LANDED_SCHEMA,
        "verdict": verdict,
        "reason": str(decision.get("reason", "")),
        "conclusive": expected_conclusive,
        "checker_rc": result.returncode,
        "elapsed_seconds": round(elapsed, 6),
        "corpus_bytes_read": corpus.get("bytes_read") if isinstance(corpus, dict) else None,
        "report_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "manual_review_required": payload.get("manual_review_required") is not False,
        "complete": expected_conclusive,
        "unproven_unit_details": _unproven_unit_details(payload),
    }


class _DuplicateKey(ValueError):
    pass


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def _valid_full_refname(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("refs/"):
        return False
    if (value.endswith(("/", ".")) or "//" in value or ".." in value
            or "@{" in value):
        return False
    if any(ord(character) < 32 or ord(character) == 127
           or character in " ~^:?*[\\" for character in value):
        return False
    components = value.split("/")
    return all(
        component
        and not component.startswith(".")
        and not component.endswith(".lock")
        for component in components
    )


def _validate_ledger_entry(entry: object) -> tuple[bool, str]:
    if not isinstance(entry, dict) or set(entry) != set(LEDGER_FIELDS):
        return False, "ledger-entry-fields-invalid"
    integer_fields = {
        "gc_auto_threshold", "gc_auto_sample_count", "gc_auto_sample_threshold",
        "loose_count_at_loss",
    }
    for field, expected in LEDGER_FIELDS.items():
        if field in integer_fields:
            valid_type = entry[field] is None or type(entry[field]) is int
        elif field == "object_retention_provided":
            valid_type = type(entry[field]) is bool
        else:
            valid_type = isinstance(entry[field], expected)
        if not valid_type:
            return False, f"ledger-entry-type-invalid:{field}"
    if entry["schema"] != LEDGER_SCHEMA or entry["object_type"] != "commit":
        return False, "ledger-entry-schema-invalid"
    if entry["assessment_schema"] != LANDED_SCHEMA:
        return False, "ledger-entry-assessment-schema-invalid"
    if entry["assessment_verdict"] not in {"landed", "not-landed", "indeterminate"}:
        return False, "ledger-entry-verdict-invalid"
    if entry["status"] not in {
        "pending", "rescued", "accepted-loss", "reachable-again", "object-missing",
    }:
        return False, "ledger-entry-status-invalid"
    if entry["object_retention_provided"] is not False:
        return False, "ledger-entry-retention-claim-invalid"
    auto = entry["gc_auto_threshold"]
    sample_threshold = entry["gc_auto_sample_threshold"]
    if ((auto is None) != (sample_threshold is None)
            or (auto is not None and sample_threshold != (auto + 255) // 256)):
        return False, "ledger-entry-gc-sample-threshold-invalid"
    if entry["gc_auto_sample_fanout"] != "17":
        return False, "ledger-entry-gc-sample-fanout-invalid"
    if entry["gc_auto_heuristic_version"] != "git-2.34.1-fanout-17-sample":
        return False, "ledger-entry-gc-heuristic-version-invalid"
    if OID_RE.fullmatch(str(entry["object_oid"])) is None:
        return False, "ledger-entry-oid-invalid"
    if not all(isinstance(value, str) for value in entry["source_refs"]):
        return False, "ledger-entry-source-refs-invalid"
    if not all(isinstance(key, str) and isinstance(value, str) and OID_RE.fullmatch(value)
               for key, value in entry["source_tips"].items()):
        return False, "ledger-entry-source-tips-invalid"
    for field in ("recorded_at", "loss_possible_not_before"):
        if not _valid_timestamp(entry[field]):
            return False, f"ledger-entry-timestamp-invalid:{field}"
    if entry["resolved_at"] is not None and not _valid_timestamp(entry["resolved_at"]):
        return False, "ledger-entry-timestamp-invalid:resolved_at"
    status = entry["status"]
    resolved_at = entry["resolved_at"]
    rescue_ref = entry["rescue_ref"]
    resolution_note = entry["resolution_note"]
    if status == "pending":
        coherent = resolved_at is None and rescue_ref is None and resolution_note is None
    elif status == "rescued":
        coherent = (
            resolved_at is not None
            and _valid_full_refname(rescue_ref)
            and isinstance(resolution_note, str)
            and bool(resolution_note.strip())
        )
    else:
        coherent = (
            resolved_at is not None
            and rescue_ref is None
            and isinstance(resolution_note, str)
            and bool(resolution_note.strip())
        )
    if not coherent:
        return False, "ledger-entry-resolution-fields-invalid"
    return True, "ok"


def _read_ledger(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        return [], []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [_issue("ledger-unreadable", "ledger", str(exc), scope="ledger", subject=str(path))]
    entries: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_oids: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("- "):
            continue
        if not line.startswith("- {"):
            issues.append(_issue("ledger-bullet-invalid", "ledger", "ledger bullet is not JSON",
                                 scope="ledger", subject=f"{path}:{line_number}"))
            continue
        try:
            item = json.loads(line[2:], object_pairs_hook=_no_duplicate_keys)
        except (_DuplicateKey, json.JSONDecodeError, TypeError) as exc:
            issues.append(_issue("ledger-json-invalid", "ledger", str(exc), scope="ledger",
                                 subject=f"{path}:{line_number}"))
            continue
        valid, reason = _validate_ledger_entry(item)
        if not valid:
            issues.append(_issue(reason, "ledger", "ledger entry violates the fixed schema",
                                 scope="ledger", subject=f"{path}:{line_number}"))
            continue
        if item["entry_id"] in seen_ids or item["object_oid"] in seen_oids:
            issues.append(_issue("ledger-entry-duplicate", "ledger", "ledger entry is duplicated",
                                 scope="ledger", subject=f"{path}:{line_number}"))
            continue
        seen_ids.add(item["entry_id"])
        seen_oids.add(item["object_oid"])
        entries.append(item)
    return entries, issues


def _audit(repo: Path, audit_tool: Path, timeout: float) -> tuple[list[str], dict[str, Any], list[dict[str, Any]]]:
    python_env = {
        **_child_env(),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    try:
        result = subprocess.run(
            [sys.executable, str(audit_tool), "--repo", str(repo)],
            cwd=repo, env=python_env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=max(0.001, timeout), check=False,
        )
    except subprocess.TimeoutExpired:
        return [], {"complete": False, "returncode": None, "reported_commit_count": None,
                    "commits": []}, [_issue("audit-timeout", "ledger", "dangling audit timed out",
                                             scope="ledger")]
    try:
        stdout = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return [], {"complete": False, "returncode": result.returncode,
                    "reported_commit_count": None, "commits": []}, [
            _issue("audit-output-invalid", "ledger", "dangling audit output is not UTF-8", scope="ledger")
        ]
    commits = re.findall(r"^\s+commit ((?:[0-9a-f]{40}|[0-9a-f]{64})) \(", stdout, re.MULTILINE)
    summaries = re.findall(r"要確認の到達不能変更 ([0-9]+) commit", stdout)
    zero_summaries = re.findall(r"要確認 0 件", stdout)
    reported_count = (
        int(summaries[0]) if len(summaries) == 1 and not zero_summaries else
        0 if len(zero_summaries) == 1 and not summaries else None
    )
    expected_rc = 0 if reported_count == 0 else 1 if reported_count is not None else None
    terminal_pattern = re.compile(
        r"audit_dangling_commits: elapsed_seconds=(?:[0-9]+(?:\.[0-9]+)?)"
    )
    output_lines = stdout.splitlines()
    terminal_lines = [line for line in output_lines if terminal_pattern.fullmatch(line)]
    complete = (
        result.returncode == expected_rc
        and reported_count is not None
        and reported_count == len(commits)
        and len(terminal_lines) == 1
        and bool(output_lines)
        and terminal_pattern.fullmatch(output_lines[-1]) is not None
    )
    issues = [] if complete else [
        _issue("audit-contract-invalid", "ledger",
               "dangling audit return code or report shape is outside its public contract",
               scope="ledger")
    ]
    return sorted(set(commits)), {
        "complete": complete, "returncode": result.returncode,
        "reported_commit_count": reported_count,
        "commits": sorted(set(commits)),
        "report_sha256": hashlib.sha256(result.stdout).hexdigest(),
    }, issues


def _ledger_check(repo: Path, ledger_path: Path, audit_tool: Path, now: dt.datetime,
                  timeout: float) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    entries, issues = _read_ledger(ledger_path)
    audit_commits, audit_summary, audit_issues = _audit(repo, audit_tool, timeout)
    issues.extend(audit_issues)
    by_oid = {entry["object_oid"]: entry for entry in entries}
    missing = [oid for oid in audit_commits if oid not in by_oid]
    notifications: list[dict[str, Any]] = [
        {"kind": "unledgered-audit-finding", "object_oid": oid,
         "entry_id": None, "urgency": "due",
         "message": "audit reported an unreachable commit with no ledger entry"}
        for oid in missing
    ]
    for oid in audit_commits:
        entry = by_oid.get(oid)
        if entry is None or entry["status"] not in {
            "rescued", "reachable-again", "object-missing",
        }:
            continue
        notifications.append({
            "kind": "stale-ledger-resolution",
            "object_oid": oid,
            "entry_id": entry["entry_id"],
            "urgency": "due",
            "status": entry["status"],
            "message": "audit re-reported an unreachable commit with a stale ledger resolution",
        })
    seven_days = now + dt.timedelta(days=7)
    for entry in entries:
        if entry["status"] != "pending":
            continue
        deadline = dt.datetime.fromisoformat(entry["loss_possible_not_before"][:-1] + "+00:00")
        if deadline <= now:
            urgency = "deadline-passed"
        elif deadline <= seven_days:
            urgency = "urgent"
        else:
            continue
        notifications.append({
            "kind": "pending-ledger-entry", "object_oid": entry["object_oid"],
            "entry_id": entry["entry_id"], "urgency": urgency,
            "message": "pending ledger entry is at or near its retention lower bound",
        })
    return {
        "path": str(ledger_path),
        "schema": LEDGER_SCHEMA,
        "object_retention_provided": False,
        "file_present": ledger_path.exists(),
        "parse_complete": not any(item["phase"] == "ledger" for item in issues if item["code"].startswith("ledger-")),
        "entry_count": len(entries),
        "pending_count": sum(entry["status"] == "pending" for entry in entries),
        "audit": audit_summary,
        "unledgered_commits": missing,
        "notifications": notifications,
    }, issues, bool(notifications)


def _base_payload(repo: Path, now: dt.datetime, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "mode": "preview" if args.branch or args.retire_worktree else "ledger-check",
        "generated_at": _utc_text(now),
        "object_retention_provided": False,
        "coverage_boundary": COVERAGE_BOUNDARY,
        "repository": {
            "root": str(repo.resolve()), "common_dir": None, "objects_dir": None,
            "object_format": None, "git_version": None,
        },
        "candidates": [],
        "retire_worktrees": [str(path) for path in args.retire_worktree],
        "root_snapshot": {
            "complete": False, "stable": False,
            "started_at": _utc_text(now), "completed_at": None,
            "start_digest": None, "end_digest": None,
            "roots": [], "excluded": [], "worktrees": [],
            "reflogs": {"included_file_count": 0, "excluded_candidate_file_count": 0,
                         "root_oid_count": 0, "inspection_complete": False},
            "indexes": {"object_count": 0, "commit_root_count": 0,
                        "inspection_complete": False},
            "alternates": {"present": False, "object_directories": [],
                           "alternate_refs_used_as_roots": False,
                           "inspection_complete": False},
        },
        "deletion_loss_closure": {
            "definition": "reachable-from-all-candidate-tips-minus-post-delete-gc-commit-roots",
            "complete": False, "limit": args.max_deletion_loss_commits,
            "observed_commit_count": 0, "commit_count": None, "commits": [],
            "stdin_positive_oids": [], "stdin_negative_oids": [],
        },
        "gc": None,
        "ledger": {
            "path": str(args.ledger), "schema": LEDGER_SCHEMA,
            "object_retention_provided": False, "file_present": False,
            "parse_complete": True, "entry_count": 0, "pending_count": 0,
            "audit": None, "unledgered_commits": [], "notifications": [],
        },
        "decision_inputs": {
            "visualization_complete": False,
            "landed": 0, "not_landed": 0, "indeterminate": 0,
            "ledger_notification_due": False,
        },
        "limits": {
            "timeout_seconds": args.timeout_seconds,
            "assessment_timeout_seconds": args.assessment_timeout_seconds,
            "max_deletion_loss_commits": args.max_deletion_loss_commits,
            "max_assessments": args.max_assessments,
        },
        "timing": {"total_elapsed_seconds": 0.0, "landed_assessment_seconds": 0.0,
                   "git_child_processes": 0},
        "issues": [],
    }


def assess(
    args: argparse.Namespace,
    *,
    assessment_time: dt.datetime | None = None,
    landed_checker: Path = LANDED_CHECKER_PATH,
    audit_tool: Path = AUDIT_TOOL_PATH,
) -> tuple[int, dict[str, Any]]:
    started = time.monotonic()
    assessment_time_error: str | None = None
    try:
        now = assessment_time or _current_assessment_time()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("assessment time must be timezone-aware")
        now = now.astimezone(dt.timezone.utc)
    except (OSError, OverflowError, RuntimeError, ValueError) as exc:
        now = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
        assessment_time_error = str(exc)
    payload = _base_payload(args.repo, now, args)
    if assessment_time_error is not None:
        payload["issues"].append(_issue(
            "assessment-time-indeterminate", "assessment",
            "assessment time could not be established: " + assessment_time_error,
        ))
        payload["timing"]["total_elapsed_seconds"] = round(time.monotonic() - started, 6)
        return 2, payload
    git = Git(args.repo.resolve(), started + args.timeout_seconds)
    technical_incomplete = False
    notification_due = False
    try:
        root, common, objects, object_format, git_version = _repo_paths(git)
        payload["repository"] = {
            "root": str(root), "common_dir": str(common), "objects_dir": str(objects),
            "object_format": object_format, "git_version": git_version,
        }
        ledger_path = args.ledger if args.ledger.is_absolute() else root / args.ledger
        ledger_path = ledger_path.resolve()
        try:
            ledger_path.relative_to(root)
        except ValueError as exc:
            raise RescueError("ledger-outside-repository", "ledger path must be inside the repository",
                              scope="ledger", subject=str(ledger_path)) from exc
        payload["ledger"]["path"] = str(ledger_path)
        config, scoped = _config_snapshot(git)
        absolute_prune_expiry = _absolute_prune_expiry(
            git, str(config["gc_prune_expire"]["effective"]),
        )

        if args.branch or args.retire_worktree:
            start_snapshot = _snapshot(
                git, root, common, objects, args.branch, set(args.retire_worktree), now,
                config, scoped,
            )
            payload["candidates"] = start_snapshot.candidates
            payload["root_snapshot"].update({
                "start_digest": start_snapshot.digest,
                "roots": start_snapshot.roots,
                "excluded": start_snapshot.excluded,
                "worktrees": start_snapshot.worktrees,
                "reflogs": start_snapshot.reflog_summary,
                "indexes": start_snapshot.index_summary,
                "alternates": start_snapshot.alternates,
            })
            payload["issues"].extend(start_snapshot.issues)
            technical_incomplete |= not start_snapshot.complete
            commits, closure = _closure(git, start_snapshot, args.max_deletion_loss_commits)
            payload["deletion_loss_closure"] = closure
            if not closure["complete"]:
                technical_incomplete = True
                payload["issues"].append(_issue(
                    "closure-limit-exceeded", "closure",
                    "deletion loss closure exceeded the configured output limit",
                ))
            gc_payload, gc_issues = _gc_observation(git, objects, git_version, config)
            payload["gc"] = gc_payload
            payload["issues"].extend(gc_issues)
            technical_incomplete |= bool(gc_issues)

            alternate_dirs = [Path(value) for value in start_snapshot.alternates["object_directories"]]
            pack_map, pack_issues = _pack_index(git, [objects, *alternate_dirs])
            payload["issues"].extend(pack_issues)
            technical_incomplete |= bool(pack_issues)
            assessment_seconds = 0.0
            for index, commit in enumerate(commits):
                retention, retention_complete = _retention(
                    git, commit["oid"], now, objects, alternate_dirs, pack_map,
                    config["gc_prune_expire"], start_snapshot.temporary_roots,
                    absolute_prune_expiry=absolute_prune_expiry,
                )
                commit["retention"] = retention
                if not retention_complete:
                    technical_incomplete = True
                    payload["issues"].append(_issue(
                        "retention-deadline-indeterminate", "retention",
                        "commit retention lower bound is indeterminate",
                        scope="commit", subject=commit["oid"],
                    ))
                if index >= args.max_assessments:
                    commit["landed_assessment"] = _empty_landed("assessment-limit-exceeded")
                    technical_incomplete = True
                    payload["issues"].append(_issue(
                        "assessment-limit-exceeded", "landed-assessment",
                        "commit was retained in output but not sent to the landed checker",
                        scope="commit", subject=commit["oid"],
                    ))
                else:
                    assessment = _landed_assessment(
                        root, landed_checker, commit["oid"],
                        args.assessment_timeout_seconds, git.remaining(),
                    )
                    commit["landed_assessment"] = assessment
                    assessment_seconds += assessment["elapsed_seconds"]
                    if not assessment["complete"]:
                        technical_incomplete = True
                        payload["issues"].append(_issue(
                            "landed-assessment-indeterminate", "landed-assessment",
                            assessment["reason"], scope="commit", subject=commit["oid"],
                        ))
            payload["timing"]["landed_assessment_seconds"] = round(assessment_seconds, 6)

            end_snapshot = _snapshot(
                git, root, common, objects, args.branch, set(args.retire_worktree), now,
                config, scoped,
            )
            end_by_ref = {item["refname"]: item["start_tip"] for item in end_snapshot.candidates}
            for candidate in payload["candidates"]:
                candidate["end_tip"] = end_by_ref.get(candidate["refname"])
            stable = start_snapshot.digest == end_snapshot.digest
            payload["root_snapshot"].update({
                "complete": start_snapshot.complete and end_snapshot.complete and stable,
                "stable": stable,
                "completed_at": _utc_text(now),
                "end_digest": end_snapshot.digest,
            })
            payload["issues"].extend(end_snapshot.issues)
            if not stable:
                payload["issues"].append(_issue(
                    "root-snapshot-moved", "root-snapshot",
                    "root inventory changed between the start and end snapshots",
                ))
            technical_incomplete |= not end_snapshot.complete or not stable
        else:
            payload["root_snapshot"].update({
                "complete": True, "stable": True, "completed_at": _utc_text(now),
                "start_digest": hashlib.sha256(b"ledger-check").hexdigest(),
                "end_digest": hashlib.sha256(b"ledger-check").hexdigest(),
            })
            payload["deletion_loss_closure"].update({
                "complete": True, "commit_count": 0,
            })

        if args.ledger_check:
            ledger, ledger_issues, notification_due = _ledger_check(
                root, ledger_path, audit_tool, now, git.remaining(),
            )
            payload["ledger"] = ledger
            payload["issues"].extend(ledger_issues)
            technical_incomplete |= bool(ledger_issues)
        verdicts = [
            item["landed_assessment"]["verdict"]
            for item in payload["deletion_loss_closure"]["commits"]
            if "landed_assessment" in item
        ]
        payload["decision_inputs"].update({
            "landed": verdicts.count("landed"),
            "not_landed": verdicts.count("not-landed"),
            "indeterminate": verdicts.count("indeterminate"),
            "ledger_notification_due": notification_due,
        })
    except (RescueError, UnicodeDecodeError, OSError) as exc:
        technical_incomplete = True
        if isinstance(exc, RescueError):
            payload["issues"].append(_issue(
                exc.code, "assessment", exc.message, scope=exc.scope, subject=exc.subject,
            ))
        else:
            payload["issues"].append(_issue(
                "assessment-error", "assessment", str(exc),
            ))
    payload["decision_inputs"]["visualization_complete"] = not technical_incomplete
    payload["timing"]["total_elapsed_seconds"] = round(time.monotonic() - started, 6)
    payload["timing"]["git_child_processes"] = git.command_count
    if technical_incomplete:
        return 2, payload
    if notification_due:
        return 3, payload
    return 0, payload


def _parser() -> CliParser:
    parser = CliParser(description=__doc__)
    parser.add_argument("--branch", action="append", default=[], metavar="NAME",
                        help="local branch removed by the modeled cleanup; repeatable")
    parser.add_argument("--retire-worktree", action="append", default=[], type=Path,
                        metavar="ABSOLUTE_PATH",
                        help="worktree removed by the modeled cleanup; repeatable")
    parser.add_argument("--ledger-check", action="store_true",
                        help="compare the unreachable-object ledger with the dangling audit")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ledger", type=Path, default=Path("docs/unreachable-object-ledger.md"))
    parser.add_argument("--timeout-seconds", type=_bounded_float(1, 900),
                        default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--assessment-timeout-seconds", type=_bounded_float(1, 60),
                        default=DEFAULT_ASSESSMENT_TIMEOUT_SECONDS)
    parser.add_argument("--max-deletion-loss-commits", type=_bounded_int(1, 100_000),
                        default=DEFAULT_MAX_DELETION_LOSS_COMMITS)
    parser.add_argument("--max-assessments", type=_bounded_int(1, 4096),
                        default=DEFAULT_MAX_ASSESSMENTS)
    return parser


def _validate_cli(parser: CliParser, args: argparse.Namespace) -> None:
    if not (args.branch or args.retire_worktree or args.ledger_check):
        parser.error("at least one --branch, --retire-worktree, or --ledger-check is required")
    if len(args.branch) != len(set(args.branch)):
        parser.error("duplicate --branch input")
    for name in args.branch:
        if not name:
            parser.error("invalid local branch name")
        result = subprocess.run(
            ["git", *GIT_CONFIG_BASE, "check-ref-format", "--branch", name],
            cwd=args.repo if args.repo.is_dir() else None,
            env=_child_env(), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=COMMAND_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            parser.error("invalid local branch name")
    normalized: list[Path] = []
    for path in args.retire_worktree:
        if not path.is_absolute():
            parser.error("--retire-worktree must be an absolute path")
        normalized.append(path.resolve())
    if len(normalized) != len(set(normalized)):
        parser.error("duplicate --retire-worktree input")
    args.retire_worktree = normalized


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    _validate_cli(parser, args)
    rc, payload = assess(args)
    sys.stdout.write(json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ) + "\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
