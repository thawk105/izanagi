#!/usr/bin/env python3
"""Assess D720 condition 1 for one branch or commit-ish without changing the repository.

The only positive content proof used here is an exact tree-entry state already
reachable from ``main``.  Patch-id, task/ledger hits, and verbatim text matches
are observations.  This tool never authorizes landing or branch deletion.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


SCHEMA = "izanagi-branch-landed-v1"
ASSESSMENT_SCOPE = "D720-condition-1-only"
EXIT_BY_VERDICT = {"landed": 0, "not-landed": 1, "indeterminate": 2}
OUTCOMES = {
    "matched", "not-matched", "not-applicable", "not-run", "error", "truncated"
}
PROBE_SIGNAL_STRENGTHS = {"strong", "weak-positive", "weak"}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_LEDGER_HITS = 100
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_FILES = 256
DEFAULT_HISTORY_CANDIDATES = 1_024
DEFAULT_HISTORY_SCAN_COMMITS = 20_000
DEFAULT_MAX_CLOSURE_COMMITS = 4_096
# T-2706 / D2104 item 24: 30 unreachable commits measured on the login node (main 11,246 commits, load 24-92):
# max per git command 26.9s (find-object; path log 21.3s, repeat check 35.9s); max x1.5 -> 45, <= DEFAULT_TIMEOUT_SECONDS.
COMMAND_TIMEOUT_SECONDS = 45.0
OID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
MODE_RE = re.compile(r"[0-7]{6}\Z")
TASK_ID_RE = re.compile(r"(?i)(?:^|[-_/])t(\d+)(?=$|[-_/])")
LOCAL_BRANCH_RE = re.compile(r"(?!-)(?!.*\.\.)(?!.*(?:^|/)\.lock(?:/|$))[A-Za-z0-9._/-]+\Z")
SPOOL_RE = re.compile(r"\Adocs/spool/(?:worklog|decisions|failures)/.+\.md\Z")
SPOOL_ID_RE = re.compile(
    r"\Adocs/spool/(?P<ledger>worklog|decisions|failures)/"
    r"(?P<authored>\d{4}-\d{2}-\d{2})-"
    r"(?P<wave>[a-z0-9]+(?:-[a-z0-9]+)*)-(?P<seq>[1-9][0-9]*)\.md\Z"
)
WAVE_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
REF_RE = re.compile(r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
REPLACE_BASE_RE = re.compile(r"refs/[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
LEGACY_RECEIPT_FIELDS = frozenset({
    "allocations", "authored", "content_sha256", "seq", "wave",
})
RECEIPT_V2_FIELDS = frozenset({
    "allocations", "authored", "base", "content_sha256", "seq",
    "tested_tip", "wave", "wave_ref",
})
LEDGER_EXACT = (
    "docs/worklog.md", "docs/decisions.md", "docs/failures.md", "docs/phase3.md",
)
LEDGER_ARCHIVE_PREFIX = "docs/archive/"
GIT_CONFIG = (
    "-c", "core.hooksPath=/dev/null",
    "-c", "protocol.file.allow=never",
    "-c", "credential.helper=",
    "-c", "diff.external=",
    "-c", "core.fsmonitor=false",
)


class AssessmentError(Exception):
    def __init__(self, code: str, message: str, *, outcome: str = "error") -> None:
        super().__init__(message)
        if outcome not in OUTCOMES:
            raise ValueError(f"invalid outcome: {outcome}")
        self.code = code
        self.message = message
        self.outcome = outcome


class CliParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self._print_message(f"{self.prog}: error: {message}\n", sys.stderr)
        raise SystemExit(64)


@dataclass(frozen=True)
class TreeEntry:
    path: str
    mode: str
    object_type: str
    oid: str

    @property
    def missing(self) -> bool:
        return self.object_type == "missing"

    def as_json(self) -> dict[str, str]:
        return {
            "path": self.path,
            "mode": self.mode,
            "object_type": self.object_type,
            "oid": self.oid,
        }


@dataclass(frozen=True)
class ClosureCommit:
    oid: str
    parents: tuple[str, ...]

    @property
    def is_merge(self) -> bool:
        return len(self.parents) > 1


@dataclass(frozen=True)
class TargetResolution:
    local_branch_oid: str | None
    commitish_oid: str | None
    abbreviated_commit_oids: tuple[str, ...]


@dataclass(frozen=True)
class IntroducedState:
    commit: str
    parent: str | None
    change: str
    old: TreeEntry
    required: TreeEntry


@dataclass
class SearchResult:
    outcome: str
    reason: str
    matched_commit: str | None
    candidate_count: int
    candidate_limit: int
    elapsed_seconds: float

    @property
    def incomplete(self) -> bool:
        return self.outcome in {"error", "truncated", "not-run"}

    def as_json(self) -> dict[str, Any]:
        return {
            "layer": "exact-tree-state",
            "decisive": True,
            "outcome": self.outcome,
            "reason": self.reason,
            "matched_commit": self.matched_commit,
            "candidate_count": self.candidate_count,
            "candidate_limit": self.candidate_limit,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
        }


@dataclass(frozen=True)
class ReceiptRegistry:
    outcome: str
    reason: str
    records_by_hash: dict[str, tuple[dict[str, object], ...]]
    record_count: int


@dataclass(frozen=True)
class CorpusResult:
    texts: dict[str, str]
    outcome: str
    files_enumerated: int
    files_read: int
    bytes_read: int
    skipped: int
    errors: tuple[dict[str, str], ...]
    complete: bool
    elapsed_seconds: float

    def as_json(self) -> dict[str, Any]:
        return {
            "decisive": False,
            "outcome": self.outcome,
            "files_enumerated": self.files_enumerated,
            "files_read": self.files_read,
            "bytes_read": self.bytes_read,
            "skipped": self.skipped,
            "errors": list(self.errors),
            "complete": self.complete,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
        }


class Git:
    def __init__(self, repo: Path, deadline: float) -> None:
        self.repo = repo
        self.deadline = deadline
        self.requested_replace_ref_base = os.environ.get("GIT_REPLACE_REF_BASE")
        self.command_count = 0

    def remaining(self) -> float:
        return self.deadline - time.monotonic()

    def run(
        self,
        args: Sequence[str],
        *,
        allowed: Iterable[int] = (0,),
        command_timeout: float = COMMAND_TIMEOUT_SECONDS,
        input_data: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        remaining = self.remaining()
        if remaining <= 0:
            raise AssessmentError("assessment-timeout", "assessment deadline expired", outcome="truncated")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
        timeout = min(command_timeout, remaining)
        self.command_count += 1
        try:
            result = subprocess.run(
                ["git", *GIT_CONFIG, *args],
                cwd=self.repo,
                env=env,
                input=input_data,
                stdin=subprocess.DEVNULL if input_data is None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AssessmentError(
                "assessment-timeout", f"git command timed out: {args[0]}", outcome="truncated"
            ) from exc
        if result.returncode not in set(allowed):
            diagnostic = result.stderr.decode("utf-8", "replace").strip().splitlines()
            suffix = diagnostic[-1] if diagnostic else f"exit {result.returncode}"
            raise AssessmentError("git-command-error", f"{args[0]} failed: {suffix}")
        return result


def _decision(verdict: str, reason: str) -> dict[str, Any]:
    values = {
        "landed": (True, True),
        "not-landed": (False, True),
        "indeterminate": (None, False),
    }
    if verdict not in values:
        raise ValueError(f"invalid verdict: {verdict}")
    landed, conclusive = values[verdict]
    return {
        "verdict": verdict,
        "landed": landed,
        "conclusive": conclusive,
        "reason": reason,
    }


def _issue(code: str, message: str, *, path: str | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "scope": "file" if path is not None else "branch",
        "path": path,
        "affects_verdict": True,
        "message": message,
    }


def _empty_observations() -> dict[str, Any]:
    return {
        "patch_id": {
            "decisive": False,
            "outcome": "not-run",
            "status": "not-run",
            "closure_commit_count": 0,
            "reported_commit_count": 0,
            "omitted_merge_count": 0,
            "unreported_commit_count": 0,
            "commits": [],
        },
        "task_index": {
            "decisive": False,
            "outcome": "not-run",
            "task_ids": [],
            "hits": [],
            "truncated": False,
            "elapsed_seconds": 0.0,
        },
        "ledger_probe": {
            "decisive": False,
            "outcome": "not-run",
            "signal_strength": None,
            "probes": [],
        },
        "ledger_corpus": {
            "decisive": False,
            "outcome": "not-run",
            "files_enumerated": 0,
            "files_read": 0,
            "bytes_read": 0,
            "skipped": 0,
            "errors": [],
            "complete": False,
            "elapsed_seconds": 0.0,
        },
        "verbatim": {
            "decisive": False,
            "outcome": "not-run",
            "entries": [],
        },
    }


def _safety_contract() -> dict[str, Any]:
    return {
        "assessment_scope": ASSESSMENT_SCOPE,
        "condition2": {"status": "not-checked"},
        "land_authorized": False,
    }


def _base_payload(repo: Path, branch: str, main: str, limits: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        # M7: the complete D720 scope contract is injected at this single point.
        **_safety_contract(),
        "branch_delete_authorized": False,
        "manual_review_required": True,
        "unproven_paths": [],
        "negative_paths": [],
        "receipt_missing_paths": [],
        "unresolved_fragment_candidates": [],
        "decision": _decision("indeterminate", "assessment-not-complete"),
        "repository": {"root": str(repo)},
        "branch": {
            "name": branch,
            "input": branch,
            "resolution_order": ["local-branch", "commit-ish"],
            "resolved_as": None,
            "resolution_candidates": {
                "local_branch": None,
                "commit_ish": [],
            },
            "tip": None,
        },
        "main": {"name": main, "tip": None},
        "merge_base": {"status": "not-required-for-closure"},
        "closure": {
            "outcome": "not-run",
            "commit_count": None,
            "merge_commit_count": None,
            "commits": None,
            "observed_commit_count": 0,
            "limit": limits["max_closure_commits"],
            "complete": False,
            "elapsed_seconds": 0.0,
        },
        "summary": {
            "changed_files": None,
            "changed_files_definition": "unique-paths-in-all-parent-difference-proof-units",
            "introduced_path_count": None,
            "tip_net_changed_files": None,
            "files_enumerated": False,
            "proof_units": None,
            "landed": 0,
            "not_landed": 0,
            "indeterminate": 0,
        },
        "proof_units": [],
        "files": [],
        "observations": _empty_observations(),
        "history_scan": {
            "outcome": "not-run",
            "commits_scanned": 0,
            "scan_limit": limits["history_scan_commits"],
            "elapsed_seconds": 0.0,
            "complete": False,
            "reason": "not-run",
        },
        "phase_outcomes": {
            "preflight": "not-run",
            "closure": "not-run",
            "proof": "not-run",
            "history_scan": "not-run",
            "observations": "not-run",
            "ref_snapshot": "not-run",
        },
        "limits": limits,
        "timing": {"total_elapsed_seconds": 0.0, "git_child_processes": 0},
        "ref_snapshot": {
            "verdict_bound_to_start_snapshot": True,
            "continuous_stability_proven": False,
            "matches_start_at_end": None,
            "end_branch_tip": None,
            "end_resolved_as": None,
            "end_main_tip": None,
        },
        "issues": [],
    }


def _valid_local_branch(name: str) -> bool:
    return bool(name and LOCAL_BRANCH_RE.fullmatch(name) and not name.endswith(("/", ".")))


def _decode_one_oid(raw: bytes, code: str) -> str:
    try:
        value = raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise AssessmentError(code, "git returned a non-ASCII object id") from exc
    if not OID_RE.fullmatch(value):
        raise AssessmentError(code, "git returned an invalid object id")
    return value


def _resolve_ref(git: Git, name: str) -> str:
    if not _valid_local_branch(name):
        raise AssessmentError("invalid-local-branch", f"invalid local branch name: {name!r}")
    result = git.run(
        ["rev-parse", "--verify", "--end-of-options", f"refs/heads/{name}^{{commit}}"],
        allowed=(0, 128),
    )
    if result.returncode:
        raise AssessmentError("branch-not-found", f"local branch does not exist: {name!r}")
    return _decode_one_oid(result.stdout, "invalid-ref-output")


def _try_resolve_commitish(git: Git, value: str) -> str | None:
    result = git.run(
        ["rev-parse", "--verify", "--end-of-options", f"{value}^{{commit}}"],
        allowed=(0, 128),
    )
    if result.returncode:
        return None
    return _decode_one_oid(result.stdout, "invalid-commit-ish-output")


def _abbreviated_commit_oids(git: Git, value: str) -> tuple[str, ...]:
    if re.fullmatch(r"[0-9a-fA-F]{4,63}", value) is None:
        return ()
    result = git.run(["rev-parse", f"--disambiguate={value.lower()}"])
    try:
        object_oids = result.stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise AssessmentError(
            "invalid-commit-ish-output", "git returned a non-ASCII disambiguation result",
        ) from exc
    commit_oids: set[str] = set()
    for oid in object_oids:
        if not OID_RE.fullmatch(oid):
            raise AssessmentError(
                "invalid-commit-ish-output", "git returned an invalid disambiguation result",
            )
        if len(value) >= len(oid):
            continue
        commit_oid = _try_resolve_commitish(git, oid)
        if commit_oid is not None:
            commit_oids.add(commit_oid)
    return tuple(sorted(commit_oids))


def _target_resolution_candidates(git: Git, value: str) -> TargetResolution:
    local_branch_oid: str | None = None
    if _valid_local_branch(value):
        try:
            local_branch_oid = _resolve_ref(git, value)
        except AssessmentError as exc:
            if exc.code != "branch-not-found":
                raise
    abbreviated_commit_oids = (
        _abbreviated_commit_oids(git, value)
        if local_branch_oid is not None else ()
    )
    commitish_oid = (
        _try_resolve_commitish(git, value)
        if local_branch_oid is None else None
    )
    return TargetResolution(
        local_branch_oid, commitish_oid, abbreviated_commit_oids,
    )


def _record_target_resolution(
    branch_payload: dict[str, Any], resolution: TargetResolution,
) -> None:
    commitish_candidates = set(resolution.abbreviated_commit_oids)
    if resolution.commitish_oid is not None:
        commitish_candidates.add(resolution.commitish_oid)
    branch_payload["resolution_candidates"] = {
        "local_branch": resolution.local_branch_oid,
        "commit_ish": sorted(commitish_candidates),
    }


def _select_target_resolution(
    value: str, resolution: TargetResolution,
) -> tuple[str, str]:
    # M11: ambiguous local-branch/abbreviated-SHA input is rejected only here.
    if resolution.local_branch_oid is not None and resolution.abbreviated_commit_oids:
        raise AssessmentError(
            "ambiguous-branch-commit-ish",
            f"input resolves as both a local branch and an abbreviated commit id: {value!r}",
        )
    if resolution.local_branch_oid is not None:
        return resolution.local_branch_oid, "local-branch"
    if resolution.commitish_oid is not None:
        return resolution.commitish_oid, "commit-ish"
    raise AssessmentError(
        "branch-not-found",
        f"neither refs/heads/{value} nor the commit-ish {value!r} resolves to a commit",
    )


def _repo_root(git: Git) -> Path:
    result = git.run(["rev-parse", "--show-toplevel"])
    try:
        return Path(result.stdout.decode("utf-8").strip()).resolve()
    except UnicodeDecodeError as exc:
        raise AssessmentError("invalid-repository-path", "repository path is not UTF-8") from exc


def _repository_preflight(git: Git) -> None:
    shallow = git.run(["rev-parse", "--is-shallow-repository"]).stdout.strip()
    if shallow == b"true":
        raise AssessmentError("shallow-repository", "shallow history cannot prove closure", outcome="truncated")
    if shallow != b"false":
        raise AssessmentError("shallow-parse-error", "cannot parse shallow repository status")
    replacements = git.run(["for-each-ref", "--format=%(refname)", "refs/replace/"]).stdout
    if replacements.strip():
        raise AssessmentError("replace-refs-present", "replace refs make object history non-canonical")
    graft_raw = git.run(["rev-parse", "--git-path", "info/grafts"]).stdout
    try:
        graft_text = graft_raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise AssessmentError("grafts-path-invalid", "grafts path is not UTF-8") from exc
    graft_path = Path(graft_text)
    if not graft_path.is_absolute():
        graft_path = git.repo / graft_path
    try:
        graft_nonempty = graft_path.is_file() and graft_path.stat().st_size > 0
    except OSError as exc:
        raise AssessmentError("grafts-inspection-error", "cannot inspect info/grafts") from exc
    if graft_nonempty:
        raise AssessmentError("grafts-present", "info/grafts makes commit history non-canonical")
    replace_base = git.requested_replace_ref_base
    if replace_base:
        if REPLACE_BASE_RE.fullmatch(replace_base) is None:
            raise AssessmentError(
                "replace-ref-base-invalid", "GIT_REPLACE_REF_BASE is not a canonical ref namespace"
            )
        custom = git.run(["for-each-ref", "--format=%(refname)", replace_base]).stdout
        if custom.strip():
            raise AssessmentError(
                "custom-replace-refs-present",
                "GIT_REPLACE_REF_BASE points to non-canonical replacement refs",
            )


def _enumerate_closure(
    git: Git, branch_oid: str, main_oid: str, limit: int,
) -> tuple[list[ClosureCommit], dict[str, Any]]:
    started = time.monotonic()
    # M3: rev-list is the sole closure rule and deliberately keeps intermediate commits.
    result = git.run([
        "rev-list", "--topo-order", "--reverse", "--parents", f"--max-count={limit + 1}",
        branch_oid, "--not", main_oid,
    ])
    rows = [row for row in result.stdout.decode("ascii", "strict").splitlines() if row]
    commits: list[ClosureCommit] = []
    for row in rows:
        fields = row.split()
        if not fields or any(not OID_RE.fullmatch(field) for field in fields):
            raise AssessmentError("closure-parse-error", "cannot parse branch-only closure")
        commits.append(ClosureCommit(fields[0], tuple(fields[1:])))
    truncated = len(commits) > limit
    observation = {
        "outcome": "truncated" if truncated else "matched",
        "commit_count": None if truncated else len(commits),
        "merge_commit_count": None if truncated else sum(item.is_merge for item in commits),
        "commits": [
            {"sha": item.oid, "parents": list(item.parents), "is_merge": item.is_merge}
            for item in commits
        ],
        "observed_commit_count": len(commits),
        "limit": limit,
        "complete": not truncated,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    return commits[:limit], observation


def _mode_type(mode: str) -> str:
    if mode == "000000":
        return "missing"
    if mode == "160000":
        return "commit"
    if mode.startswith(("100", "120")):
        return "blob"
    if mode == "040000":
        return "tree"
    raise AssessmentError("tree-mode-parse-error", f"unsupported tree mode: {mode}")


def _missing_entry(path: str, oid_length: int = 40) -> TreeEntry:
    return TreeEntry(path, "000000", "missing", "0" * oid_length)


def _parse_raw_diff(raw: bytes, commit: str, parent: str | None) -> list[IntroducedState]:
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 2:
        raise AssessmentError("diff-parse-error", "raw diff has an incomplete record")
    result: list[IntroducedState] = []
    for offset in range(0, len(fields), 2):
        header, path_raw = fields[offset], fields[offset + 1]
        try:
            header_text = header.decode("ascii")
            path = path_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssessmentError("diff-parse-error", "raw diff is not strict UTF-8/ASCII") from exc
        match = re.fullmatch(
            r":([0-7]{6}) ([0-7]{6}) ((?:[0-9a-f]{40}|[0-9a-f]{64})) ((?:[0-9a-f]{40}|[0-9a-f]{64})) ([AMDT])",
            header_text,
        )
        if match is None:
            raise AssessmentError("diff-parse-error", "raw diff record has an unknown shape")
        old_mode, new_mode, old_oid, new_oid, change = match.groups()
        if len(old_oid) != len(new_oid) or not path:
            raise AssessmentError("diff-parse-error", "raw diff record has invalid ids/path")
        old = TreeEntry(path, old_mode, _mode_type(old_mode), old_oid)
        new = TreeEntry(path, new_mode, _mode_type(new_mode), new_oid)
        result.append(IntroducedState(commit, parent, change, old, new))
    return result


def _introduced_states(git: Git, commits: Sequence[ClosureCommit]) -> list[IntroducedState]:
    states: list[IntroducedState] = []
    for item in commits:
        parents: tuple[str | None, ...] = item.parents or (None,)
        edge_states: list[dict[str, IntroducedState]] = []
        for parent in parents:
            if parent is None:
                args = ["diff-tree", "--root", "-r", "--no-commit-id", "--raw", "-z", "--no-abbrev", "--no-renames", item.oid]
            else:
                args = ["diff-tree", "-r", "--no-commit-id", "--raw", "-z", "--no-abbrev", "--no-renames", parent, item.oid]
            parsed = _parse_raw_diff(git.run(args).stdout, item.oid, parent)
            edge_states.append({state.required.path: state for state in parsed})
        # M4': a merge contributes only paths changed relative to every parent.
        common_paths = set.intersection(*(set(edge) for edge in edge_states))
        for edge in edge_states:
            states.extend(edge[path] for path in sorted(common_paths))
    return states


def _tip_net_path_count(git: Git, main_oid: str, branch_oid: str) -> int:
    raw = git.run([
        "diff", "--name-only", "-z", "--no-renames", main_oid, branch_oid,
    ]).stdout
    paths: set[str] = set()
    for item in (value for value in raw.split(b"\0") if value):
        try:
            paths.add(item.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise AssessmentError("tip-net-path-parse-error", "tip net path is not UTF-8") from exc
    return len(paths)


def _parse_ls_tree_record(raw: bytes, expected_path: str | None = None) -> TreeEntry:
    try:
        meta, path_raw = raw.split(b"\t", 1)
        mode_raw, type_raw, oid_raw = meta.split(b" ", 2)
        path = path_raw.decode("utf-8")
        mode = mode_raw.decode("ascii")
        object_type = type_raw.decode("ascii")
        oid = oid_raw.decode("ascii")
    except (ValueError, UnicodeDecodeError) as exc:
        raise AssessmentError("ls-tree-parse-error", "cannot parse ls-tree record") from exc
    if not MODE_RE.fullmatch(mode) or object_type not in {"blob", "tree", "commit"} or not OID_RE.fullmatch(oid):
        raise AssessmentError("ls-tree-parse-error", "ls-tree record has invalid fields")
    if expected_path is not None and path != expected_path:
        raise AssessmentError("ls-tree-path-mismatch", "ls-tree returned another path")
    return TreeEntry(path, mode, object_type, oid)


def _tree_entry(git: Git, commit: str, path: str, oid_length: int) -> TreeEntry:
    raw = git.run(["ls-tree", "-z", "--full-tree", commit, "--", path]).stdout
    rows = [row for row in raw.split(b"\0") if row]
    if not rows:
        return _missing_entry(path, oid_length)
    if len(rows) != 1:
        raise AssessmentError("ls-tree-parse-error", "ls-tree returned multiple exact-path entries")
    return _parse_ls_tree_record(rows[0], path)


def _entry_matches(required: TreeEntry, observed: TreeEntry) -> bool:
    # M5: mode, object type, and oid are one indivisible proof state.
    return (
        required.path, required.mode, required.object_type, required.oid
    ) == (
        observed.path, observed.mode, observed.object_type, observed.oid
    )


def _scan_main_history(git: Git, main_oid: str, scan_limit: int) -> dict[str, Any]:
    started = time.monotonic()
    result = git.run(["rev-list", "--topo-order", f"--max-count={scan_limit + 1}", main_oid])
    rows = [row for row in result.stdout.decode("ascii", "strict").splitlines() if row]
    elapsed = time.monotonic() - started
    if any(not OID_RE.fullmatch(row) for row in rows):
        raise AssessmentError("history-scan-parse-error", "cannot parse main history scan")
    truncated = len(rows) > scan_limit
    return {
        "outcome": "truncated" if truncated else "matched",
        "commits_scanned": len(rows),
        "scan_limit": scan_limit,
        "elapsed_seconds": round(elapsed, 6),
        "complete": not truncated,
        "reason": "history-scan-limit-exceeded" if truncated else "main-history-fully-scanned",
    }


def _batch_check_path_candidates(
    git: Git, candidates: Sequence[str], path: str,
) -> list[tuple[str, str] | None]:
    """Validate the entire tagged chunk before exposing any positive candidate."""
    if not candidates:
        raise AssessmentError("path-batch-parse-error", "empty candidate batch")
    expressions = [f"{commit}:{path}".encode("utf-8") for commit in candidates]
    data = b"".join(expr + f" {index}\n".encode("ascii")
                    for index, expr in enumerate(expressions))
    raw = git.run([
        "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)",
    ], input_data=data).stdout
    rows = raw.split(b"\n")
    if rows[-1] != b"" or len(rows) != len(candidates) + 1:
        raise AssessmentError("path-batch-parse-error", "candidate batch line count or terminator invalid")
    parsed: list[tuple[str, str] | None] = []
    for index, (expr, row) in enumerate(zip(expressions, rows[:-1])):
        if git.remaining() <= 0:
            raise AssessmentError("assessment-timeout", "candidate batch deadline expired", outcome="truncated")
        if row == expr + b" missing":
            parsed.append(None)
            continue
        try:
            oid, object_type, size, tag = row.decode("ascii").split(" ")
        except (UnicodeDecodeError, ValueError) as exc:
            raise AssessmentError("path-batch-parse-error", "invalid candidate batch row") from exc
        if (not OID_RE.fullmatch(oid) or len(oid) != len(candidates[index])
                or object_type not in {"blob", "tree", "commit", "tag"}
                or re.fullmatch(r"[0-9]+", size) is None or tag != str(index)):
            raise AssessmentError("path-batch-parse-error", "invalid candidate batch fields or order")
        parsed.append((oid, object_type))
    return parsed


def _find_exact_state(
    git: Git,
    main_oid: str,
    required: TreeEntry,
    candidate_limit: int,
) -> SearchResult:
    started = time.monotonic()
    tip_entry = _tree_entry(git, main_oid, required.path, len(required.oid))
    if _entry_matches(required, tip_entry):
        return SearchResult("matched", "exact-state-at-main-tip", main_oid, 1, candidate_limit, time.monotonic() - started)
    log = git.run([
        "log", "--full-history", "--format=%H", f"--max-count={candidate_limit + 1}",
        main_oid, "--", required.path,
    ])
    candidates = [row for row in log.stdout.decode("ascii", "strict").splitlines() if row]
    if any(not OID_RE.fullmatch(row) for row in candidates):
        raise AssessmentError("history-candidate-parse-error", "cannot parse history candidates")
    # Positive proof is checked before a candidate-limit truncation is reported.
    batch_safe = (
        not required.missing and required.object_type == "blob"
        and required.mode in {"100644", "100755"}
        and not any(char.isspace() for char in required.path)
    )
    for offset in range(0, len(candidates), 1024):
        chunk = candidates[offset:offset + 1024]
        metadata = _batch_check_path_candidates(git, chunk, required.path) if batch_safe else None
        for index, commit in enumerate(chunk):
            if metadata is not None and metadata[index] != (required.oid, required.object_type):
                continue
            observed = _tree_entry(git, commit, required.path, len(required.oid))
            if _entry_matches(required, observed):
                return SearchResult(
                    "matched", "exact-state-in-main-history", commit, len(candidates),
                    candidate_limit, time.monotonic() - started,
                )
    if len(candidates) > candidate_limit:
        return SearchResult(
            "truncated", "history-candidate-limit-exceeded", None, len(candidates),
            candidate_limit, time.monotonic() - started,
        )
    return SearchResult(
        "not-matched", "exact-state-absent-from-main-history", None, len(candidates),
        candidate_limit, time.monotonic() - started,
    )


def _find_object_any_path(git: Git, main_oid: str, oid: str) -> SearchResult:
    """Observe an object anywhere in main history; never use it as positive proof."""
    started = time.monotonic()
    result = git.run([
        "log", "--full-history", "--format=%H", "--max-count=1",
        f"--find-object={oid}", main_oid,
    ])
    rows = [row for row in result.stdout.decode("ascii", "strict").splitlines() if row]
    if len(rows) > 1 or any(not OID_RE.fullmatch(row) for row in rows):
        raise AssessmentError("object-search-parse-error", "cannot parse object search")
    return SearchResult(
        "matched" if rows else "not-matched",
        "exact-object-seen-at-some-path" if rows else "exact-object-absent-from-main-history",
        rows[0] if rows else None,
        len(rows),
        1,
        time.monotonic() - started,
    )


def _cat_object(git: Git, oid: str) -> bytes:
    size_raw = git.run(["cat-file", "-s", oid]).stdout
    try:
        size = int(size_raw.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise AssessmentError("cat-file-size-parse-error", "invalid object size") from exc
    if size < 0 or size > MAX_TEXT_BYTES:
        raise AssessmentError("blob-size-limit-exceeded", "blob exceeds text observation limit", outcome="truncated")
    return git.run(["cat-file", "blob", oid]).stdout


def _show_optional(git: Git, commit: str, path: str) -> bytes | None:
    result = git.run(["show", f"{commit}:{path}"], allowed=(0, 128))
    return result.stdout if result.returncode == 0 else None


class _DuplicateJsonKey(ValueError):
    pass


def _json_object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateJsonKey(key)
        value[key] = item
    return value


def _valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _valid_allocations(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    for key, allocation in value.items():
        namespace = key.split(":", 1)[0] if isinstance(key, str) and ":" in key else ""
        if (
            not isinstance(key, str)
            or re.fullmatch(r"[TDF]:[a-z][a-z0-9]*(?:-[a-z0-9]+)*", key) is None
            or not isinstance(allocation, str)
            or (
                (namespace == "T" and re.fullmatch(r"\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\]", allocation) is None)
                or (namespace == "D" and re.fullmatch(r"D[1-9][0-9]*", allocation) is None)
                or (namespace == "F" and re.fullmatch(r"F[1-9][0-9]*", allocation) is None)
            )
        ):
            return False
    return True


def _receipt_record_valid(record: dict[str, object], *, v2_seen: bool) -> tuple[bool, bool]:
    fields = frozenset(record)
    is_v2 = fields == RECEIPT_V2_FIELDS
    if not is_v2 and (fields != LEGACY_RECEIPT_FIELDS or v2_seen):
        return False, v2_seen
    if (
        not _valid_date(record.get("authored"))
        or not isinstance(record.get("wave"), str)
        or WAVE_RE.fullmatch(str(record.get("wave"))) is None
        or type(record.get("seq")) is not int
        or int(record.get("seq", 0)) <= 0
        or not isinstance(record.get("content_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", str(record.get("content_sha256"))) is None
        or not _valid_allocations(record.get("allocations"))
    ):
        return False, v2_seen
    if is_v2 and (
        type(record.get("base")) is not str
        or OID_RE.fullmatch(str(record.get("base"))) is None
        or type(record.get("tested_tip")) is not str
        or OID_RE.fullmatch(str(record.get("tested_tip"))) is None
        or type(record.get("wave_ref")) is not str
        or REF_RE.fullmatch(str(record.get("wave_ref"))) is None
    ):
        return False, v2_seen
    return True, v2_seen or is_v2


def _read_receipts(git: Git, main_oid: str) -> ReceiptRegistry:
    raw = _show_optional(git, main_oid, "docs/spool/FOLDED.md")
    if raw is None:
        return ReceiptRegistry("not-matched", "folded-receipt-file-absent", {}, 0)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ReceiptRegistry("error", "folded-receipt-not-utf8", {}, 0)
    records_by_hash: dict[str, list[dict[str, object]]] = {}
    seen_content: set[str] = set()
    seen_identity: set[tuple[str, str, str]] = set()
    v2_seen = False
    record_count = 0
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        if not line.startswith("- {"):
            return ReceiptRegistry("error", "folded-receipt-bullet-invalid", {}, record_count)
        try:
            item = json.loads(line[2:], object_pairs_hook=_json_object_without_duplicate_keys)
        except _DuplicateJsonKey:
            return ReceiptRegistry("error", "folded-receipt-duplicate-json-key", {}, record_count)
        except (json.JSONDecodeError, TypeError):
            return ReceiptRegistry("error", "folded-receipt-json-invalid", {}, record_count)
        if not isinstance(item, dict):
            return ReceiptRegistry("error", "folded-receipt-not-object", {}, record_count)
        valid, v2_seen = _receipt_record_valid(item, v2_seen=v2_seen)
        if not valid:
            return ReceiptRegistry("error", "folded-receipt-schema-invalid", {}, record_count)
        digest = str(item["content_sha256"])
        allocation_identities = {
            (str(item["wave"]), key.split(":", 1)[0], key.split(":", 1)[1])
            for key in dict(item["allocations"])
        }
        if digest in seen_content or any(value in seen_identity for value in allocation_identities):
            return ReceiptRegistry("error", "folded-receipt-duplicate", {}, record_count)
        seen_content.add(digest)
        seen_identity.update(allocation_identities)
        records_by_hash.setdefault(digest, []).append(item)
        record_count += 1
    return ReceiptRegistry(
        "not-matched", "folded-receipts-parsed",
        {key: tuple(value) for key, value in records_by_hash.items()}, record_count,
    )


def _fragment_frontmatter(blob: bytes) -> dict[str, str]:
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AssessmentError("fragment-body-not-utf8", "fragment is not UTF-8") from exc
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssessmentError("fragment-frontmatter-invalid", "fragment frontmatter is absent")
    fields: dict[str, str] = {}
    end = None
    for index, line in enumerate(lines[1:], 1):
        if line == "---":
            end = index
            break
        field = re.fullmatch(r"([a-z][a-z0-9_-]*): (.*)", line)
        if field is None or field.group(1) in fields:
            raise AssessmentError("fragment-frontmatter-invalid", "fragment frontmatter is malformed")
        fields[field.group(1)] = field.group(2)
    if end is None:
        raise AssessmentError("fragment-frontmatter-invalid", "fragment frontmatter is unterminated")
    return fields


def _fragment_identity(path: str, blob: bytes) -> tuple[str, str, int]:
    match = SPOOL_ID_RE.fullmatch(path)
    if match is None:
        raise AssessmentError("fragment-identity-invalid", "fragment path has no canonical identity")
    fields = _fragment_frontmatter(blob)
    required = {"schema", "ledger", "authored", "wave", "seq"}
    if match.group("ledger") == "worklog":
        required.add("title")
    allowed = set(required)
    if set(fields) - allowed or not required <= set(fields):
        raise AssessmentError("fragment-frontmatter-invalid", "fragment frontmatter fields are invalid")
    if (
        fields["schema"] != "izanagi-spool-v1"
        or fields["ledger"] != match.group("ledger")
        or fields["authored"] != match.group("authored")
        or fields["wave"] != match.group("wave")
        or fields["seq"] != match.group("seq")
        or not _valid_date(fields["authored"])
    ):
        raise AssessmentError("fragment-identity-invalid", "fragment identity is not canonical")
    return fields["authored"], fields["wave"], int(fields["seq"])


def _receipt_match(
    registry: ReceiptRegistry, digest: str, identity: tuple[str, str, int],
) -> tuple[bool, str]:
    records = registry.records_by_hash.get(digest, ())
    if not records:
        return False, "folded-receipt-absent"
    if any(
        (record["authored"], record["wave"], record["seq"]) == identity
        for record in records
    ):
        return True, "folded-receipt-exact-hash-and-identity"
    return False, "folded-receipt-identity-mismatch"


def _strip_frontmatter(blob: bytes) -> str | None:
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        return None
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1:]
                break
        else:
            return None
    return "\n".join(lines).strip()


def _structural_units(blob: bytes) -> list[str] | None:
    body = _strip_frontmatter(blob)
    if body is None:
        return None
    units = [part.strip() for part in re.split(r"\n[ \t]*\n+", body) if part.strip()]
    return units


def _fragment_identity_spec(path: str, blob: bytes) -> dict[str, str]:
    ledger_match = SPOOL_ID_RE.fullmatch(path)
    if ledger_match is None:
        return {
            "kind": "none",
            "value": "",
            "reason": "fragment-path-has-no-ledger-identity",
        }
    fields = _fragment_frontmatter(blob)
    ledger = ledger_match.group("ledger")
    if ledger == "worklog":
        title = fields.get("title", "")
        if title:
            return {
                "kind": "frontmatter-title",
                "value": title,
                "reason": "worklog-frontmatter-title",
            }
        return {
            "kind": "none",
            "value": "",
            "reason": "worklog-frontmatter-title-empty",
        }

    namespace = {"decisions": "D", "failures": "F"}[ledger]
    body = _strip_frontmatter(blob)
    if body is not None:
        heading = re.search(
            rf"^##[ \t]+\{{\{{{namespace}:[a-z][a-z0-9]*(?:-[a-z0-9]+)*\}}\}}(?P<text>.*)$",
            body,
            re.MULTILINE,
        )
        if heading is not None:
            text = re.sub(
                r"^[ \t]*(?:[.:：]|[-–—])[ \t]*", "", heading.group("text"),
            ).strip()
            if text:
                return {
                    "kind": "placeholder-heading-text",
                    "value": text,
                    "reason": f"{ledger}-placeholder-heading-text",
                }
    return {
        "kind": "none",
        "value": "",
        "reason": f"{ledger}-fragment-has-no-usable-placeholder-heading",
    }


def _identity_line_match(kind: str, value: str, line: str) -> bool:
    if kind == "frontmatter-title":
        return re.fullmatch(
            rf"## \d{{4}}-\d{{2}}-\d{{2}} \([1-9][0-9]*\) — {re.escape(value)}",
            line,
        ) is not None
    return line.startswith("## ") and line.endswith(value)


def _probe_signal_strength(
    identity_outcome: str, structural_unit_count: int, single_file_max: int,
) -> str:
    # M12: identity precedence enters probe strength at this single decision point.
    if identity_outcome == "matched":
        return "strong"
    if structural_unit_count and single_file_max * 2 > structural_unit_count:
        return "weak-positive"
    return "weak"


def _ledger_paths(git: Git, main_oid: str) -> list[TreeEntry]:
    result = git.run([
        "ls-tree", "-r", "-z", "--full-tree", main_oid, "--",
        *LEDGER_EXACT, LEDGER_ARCHIVE_PREFIX,
    ])
    entries: list[TreeEntry] = []
    for row in (item for item in result.stdout.split(b"\0") if item):
        entry = _parse_ls_tree_record(row)
        if entry.object_type != "blob":
            continue
        if entry.path in LEDGER_EXACT or entry.path.startswith(LEDGER_ARCHIVE_PREFIX):
            entries.append(entry)
    return entries


def _ledger_corpus(git: Git, main_oid: str) -> CorpusResult:
    started = time.monotonic()
    entries = _ledger_paths(git, main_oid)
    if not entries:
        return CorpusResult({}, "matched", 0, 0, 0, 0, (), True, time.monotonic() - started)
    request = b"".join(entry.oid.encode("ascii") + b"\n" for entry in entries)
    result = git.run(["cat-file", "--batch"], input_data=request)
    cursor = 0
    texts: dict[str, str] = {}
    errors: list[dict[str, str]] = []
    bytes_read = 0
    truncated = False
    for entry in entries:
        if git.remaining() <= 0:
            raise AssessmentError("assessment-timeout", "ledger corpus deadline expired", outcome="truncated")
        newline = result.stdout.find(b"\n", cursor)
        if newline < 0:
            raise AssessmentError("cat-file-batch-parse-error", "batch header is incomplete")
        header = result.stdout[cursor:newline]
        cursor = newline + 1
        fields = header.split()
        if len(fields) != 3 or fields[0].decode("ascii", "replace") != entry.oid:
            raise AssessmentError("cat-file-batch-parse-error", "batch header has an invalid object")
        try:
            object_type = fields[1].decode("ascii")
            size = int(fields[2].decode("ascii"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise AssessmentError("cat-file-batch-parse-error", "batch size/type is invalid") from exc
        end = cursor + size
        if object_type != "blob" or size < 0 or end >= len(result.stdout) or result.stdout[end:end + 1] != b"\n":
            raise AssessmentError("cat-file-batch-parse-error", "batch body has an invalid shape")
        raw = result.stdout[cursor:end]
        cursor = end + 1
        bytes_read += size
        if size > MAX_TEXT_BYTES:
            errors.append({"path": entry.path, "code": "blob-size-limit-exceeded"})
            truncated = True
            continue
        try:
            texts[entry.path] = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append({"path": entry.path, "code": "ledger-blob-not-utf8"})
    if cursor != len(result.stdout):
        raise AssessmentError("cat-file-batch-parse-error", "batch output has trailing data")
    outcome = "error" if any(item["code"] == "ledger-blob-not-utf8" for item in errors) else "truncated" if truncated else "matched"
    return CorpusResult(
        texts, outcome, len(entries), len(texts), bytes_read, len(errors),
        tuple(errors), not errors, time.monotonic() - started,
    )


def _probe_hit_targets(
    units_by_file: dict[str, set[int]], identity_hits: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    identity_paths = {str(item["path"]) for item in identity_hits}
    return [{
        "path": target_path,
        "matched_units": len(units_by_file.get(target_path, set())) + int(
            target_path in identity_paths
        ),
        "matched_structural_units": len(units_by_file.get(target_path, set())),
        "identity_unit_matched": target_path in identity_paths,
    } for target_path in sorted(set(units_by_file) | identity_paths)]


def _ledger_probe(git: Git, path: str, blob: bytes, corpus: CorpusResult) -> dict[str, Any]:
    started = time.monotonic()
    units = _structural_units(blob)
    if units is None:
        return {
            "decisive": False, "path": path, "outcome": "error",
            "reason": "fragment-body-parse-error", "unit_count": None, "hits": [],
            "matched_unit_count": None, "all_units_matched": False,
            "single_file_max_matched_unit_count": None, "truncated": False,
            "signal_strength": None, "hit_targets": [],
            "identity_unit": {
                "kind": "none", "value": None, "outcome": "not-applicable",
                "reason": "fragment-body-parse-error", "hit_targets": [],
            },
            "elapsed_seconds": round(time.monotonic() - started, 6),
        }
    identity_spec = _fragment_identity_spec(path, blob)
    identity_hits: list[dict[str, Any]] = []
    if identity_spec["kind"] != "none":
        for ledger_path, text in corpus.texts.items():
            if git.remaining() <= 0:
                raise AssessmentError(
                    "assessment-timeout", "ledger probe deadline expired",
                    outcome="truncated",
                )
            count = sum(
                _identity_line_match(identity_spec["kind"], identity_spec["value"], line)
                for line in text.splitlines()
            )
            if count:
                identity_hits.append({"path": ledger_path, "count": count})
    identity_outcome = (
        "not-applicable" if identity_spec["kind"] == "none" else
        "matched" if identity_hits else "not-matched"
    )
    identity_unit = {
        "kind": identity_spec["kind"],
        "value": identity_spec["value"] or None,
        "outcome": identity_outcome,
        "reason": identity_spec["reason"],
        "hit_targets": identity_hits,
    }

    hits: list[dict[str, Any]] = []
    matched_units: set[int] = set()
    units_by_file: dict[str, set[int]] = {}
    for index, unit in enumerate(units):
        if git.remaining() <= 0:
            raise AssessmentError("assessment-timeout", "ledger probe deadline expired", outcome="truncated")
        for ledger_path, text in corpus.texts.items():
            if git.remaining() <= 0:
                raise AssessmentError("assessment-timeout", "ledger probe deadline expired", outcome="truncated")
            count = text.count(unit)
            if count:
                hits.append({"unit": index, "path": ledger_path, "count": count})
                matched_units.add(index)
                units_by_file.setdefault(ledger_path, set()).add(index)
                if len(hits) >= MAX_LEDGER_HITS:
                    single_file_max = max(
                        (len(value) for value in units_by_file.values()), default=0,
                    )
                    return {
                        "decisive": False, "path": path, "outcome": "truncated",
                        "reason": "ledger-hit-output-limit", "unit_count": len(units),
                        "matched_unit_count": len(matched_units),
                        "all_units_matched": len(matched_units) == len(units),
                        "single_file_max_matched_unit_count": single_file_max,
                        "signal_strength": _probe_signal_strength(
                            identity_outcome, len(units), single_file_max,
                        ),
                        "identity_unit": identity_unit,
                        "hit_targets": _probe_hit_targets(units_by_file, identity_hits),
                        "hits": hits, "truncated": True,
                        "elapsed_seconds": round(time.monotonic() - started, 6),
                    }
    single_file_max = max((len(value) for value in units_by_file.values()), default=0)
    signal_strength = _probe_signal_strength(
        identity_outcome, len(units), single_file_max,
    )
    complete_outcome = "matched" if signal_strength == "strong" else "not-matched"
    if corpus.outcome in {"error", "truncated"}:
        complete_outcome = corpus.outcome
    return {
        "decisive": False,
        "path": path,
        "outcome": complete_outcome,
        "reason": (
            "ledger-corpus-incomplete" if not corpus.complete else
            "identity-unit-match" if signal_strength == "strong" else
            "single-file-majority-structural-match" if signal_strength == "weak-positive" else
            "weak-structural-coverage" if hits else "no-structural-unit-hit"
        ),
        "unit_count": len(units),
        "matched_unit_count": len(matched_units),
        "all_units_matched": bool(units) and len(matched_units) == len(units),
        "single_file_max_matched_unit_count": single_file_max,
        "signal_strength": signal_strength,
        "identity_unit": identity_unit,
        "hit_targets": _probe_hit_targets(units_by_file, identity_hits),
        "hits": hits,
        "truncated": False,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }


def _verbatim_observation(
    git: Git, main_oid: str, required: TreeEntry, tip_entry: TreeEntry
) -> dict[str, Any]:
    base = {"decisive": False, "path": required.path, "commit": main_oid}
    if required.object_type != "blob" or tip_entry.object_type != "blob":
        return {**base, "outcome": "not-applicable", "reason": "non-blob-state"}
    try:
        wanted = _cat_object(git, required.oid)
        current = _cat_object(git, tip_entry.oid)
    except AssessmentError as exc:
        return {**base, "outcome": exc.outcome, "reason": exc.code}
    if b"\0" in wanted or b"\0" in current:
        return {**base, "outcome": "not-applicable", "reason": "binary-content"}
    matched = bool(wanted) and wanted in current
    return {
        **base,
        "outcome": "matched" if matched else "not-matched",
        "reason": "verbatim-content-observed" if matched else "verbatim-content-not-observed",
    }


def _spool_decision(registry: ReceiptRegistry, receipt_match: bool, receipt_reason: str) -> tuple[dict[str, Any], bool]:
    if registry.outcome == "error":
        return _decision("indeterminate", registry.reason), True
    if receipt_match:
        return _decision("landed", receipt_reason), False
    # M1: a missing exact receipt has exactly one verdict rule.
    return _decision("indeterminate", receipt_reason), False


def _spool_exact_positive_decision(
    search: SearchResult, receipt_reason: str,
) -> tuple[dict[str, Any], bool]:
    if search.outcome == "matched":
        return _decision("landed", search.reason), False
    if search.incomplete:
        return _decision("indeterminate", search.reason), True
    return _decision("indeterminate", receipt_reason), False


def _regular_decision(
    state: IntroducedState,
    search: SearchResult,
    any_path: SearchResult | None,
) -> tuple[dict[str, Any], bool]:
    if search.outcome == "matched":
        return _decision("landed", search.reason), False
    # M6: an incomplete candidate search has exactly one unit-verdict rule.
    if search.incomplete:
        return _decision("indeterminate", search.reason), True
    if state.change == "A" and state.old.missing and search.candidate_count == 0:
        if any_path is None:
            return _decision("indeterminate", "any-path-object-search-not-run"), True
        if any_path.incomplete:
            return _decision("indeterminate", any_path.reason), True
        # M8': an object observed at another path is not exact path/state proof.
        if any_path.outcome == "matched":
            return _decision("indeterminate", "exact-object-seen-at-another-path"), False
        return _decision("not-landed", "pure-add-path-never-present"), False
    return _decision("indeterminate", "exact-state-not-proven"), False


def _proof_unit(
    git: Git,
    state: IntroducedState,
    main_oid: str,
    candidate_limit: int,
    receipt_registry: ReceiptRegistry,
) -> tuple[dict[str, Any], bool, dict[str, Any] | None]:
    is_spool = bool(SPOOL_RE.fullmatch(state.required.path))
    spool_exact_decisive = False
    if is_spool:
        search = SearchResult(
            "not-applicable", "spool-uses-folded-receipt", None, 0,
            candidate_limit, 0.0,
        )
    else:
        search = _find_exact_state(git, main_oid, state.required, candidate_limit)
    any_path: SearchResult | None = None
    if (
        not is_spool
        and search.outcome == "not-matched"
        and state.change == "A"
        and state.old.missing
        and search.candidate_count == 0
        and not state.required.missing
    ):
        any_path = _find_object_any_path(git, main_oid, state.required.oid)
    tip_entry = _tree_entry(git, main_oid, state.required.path, len(state.required.oid))
    exact_receipt: str | None = None
    pending_probe: dict[str, Any] | None = None
    if is_spool:
        receipt_entry = state.old if state.required.missing else state.required
        receipt_match = False
        receipt_reason = receipt_registry.reason
        receipt_outcome = receipt_registry.outcome
        try:
            if receipt_entry.object_type != "blob" or receipt_entry.missing:
                raise AssessmentError("spool-receipt-entry-invalid", "spool proof entry is not a blob")
            blob = _cat_object(git, receipt_entry.oid)
            exact_receipt = hashlib.sha256(blob).hexdigest()
            identity = _fragment_identity(state.required.path, blob)
        except AssessmentError as exc:
            decision, incomplete = _decision("indeterminate", exc.code), True
            receipt_outcome = exc.outcome
            receipt_reason = exc.code
        else:
            receipt_match, receipt_reason = _receipt_match(
                receipt_registry, exact_receipt, identity,
            )
            decision, incomplete = _spool_decision(
                receipt_registry, receipt_match, receipt_reason,
            )
            if receipt_registry.outcome == "error":
                receipt_reason = receipt_registry.reason
            receipt_outcome = (
                "error" if receipt_registry.outcome == "error" else
                "matched" if receipt_match else "not-matched"
            )
            if (not receipt_match and receipt_registry.outcome != "error"
                    and not state.required.missing and state.required.object_type == "blob"
                    and state.required.mode in {"100644", "100755"}):
                try:
                    search = _find_exact_state(git, main_oid, state.required, candidate_limit)
                except AssessmentError as exc:
                    search = SearchResult(exc.outcome, exc.code, None, 0, candidate_limit, 0.0)
                decision, incomplete = _spool_exact_positive_decision(search, receipt_reason)
                spool_exact_decisive = search.outcome == "matched" or search.incomplete
            if (not receipt_match and receipt_registry.outcome != "error"
                    and decision["verdict"] == "indeterminate"):
                body = _strip_frontmatter(blob)
                pending_probe = {
                    "path": state.required.path,
                    "blob": blob,
                    "whole_file_sha256": exact_receipt,
                    "canonical_body_sha256": (
                        hashlib.sha256(body.encode("utf-8")).hexdigest()
                        if body is not None else None
                    ),
                    "receipt_present": False,
                }
        receipt_evidence = {
            "layer": "folded-receipt",
            "decisive": not spool_exact_decisive,
            "outcome": receipt_outcome,
            "reason": receipt_reason,
            "content_sha256": exact_receipt,
            "identity_matched": receipt_match,
        }
    else:
        decision, incomplete = _regular_decision(state, search, any_path)
        receipt_evidence = {
            "layer": "folded-receipt", "decisive": True, "outcome": "not-applicable",
            "reason": "not-spool-fragment", "content_sha256": None,
        }
    unit = {
        "commit": state.commit,
        "parent": state.parent,
        "path": state.required.path,
        "change": state.change,
        "old_state": state.old.as_json(),
        "required_state": state.required.as_json(),
        "decision": decision,
        "evidence": [
            {**search.as_json(), "decisive": spool_exact_decisive if is_spool else True},
            receipt_evidence,
            ({
                **any_path.as_json(),
                "layer": "any-path-object-observation",
                "decisive": False,
            } if any_path is not None else {
                "layer": "any-path-object-observation",
                "outcome": "not-run",
                "reason": "not-needed",
                "decisive": False,
                "matched_commit": None,
                "candidate_count": 0,
                "candidate_limit": 1,
                "elapsed_seconds": 0.0,
            }),
        ],
        "integrity_incomplete": incomplete,
    }
    # Verbatim matching is recorded only below observations, never consumed above.
    unit["verbatim_observation"] = _verbatim_observation(git, main_oid, state.required, tip_entry)
    return unit, incomplete, pending_probe


def _patch_observation(
    git: Git, main_oid: str, branch_oid: str, closure: Sequence[ClosureCommit]
) -> dict[str, Any]:
    result = git.run(["cherry", "-v", main_oid, branch_oid])
    rows: list[dict[str, str]] = []
    reported: set[str] = set()
    for raw in result.stdout.splitlines():
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssessmentError("patch-id-parse-error", "git cherry output is not UTF-8") from exc
        match = re.fullmatch(r"([+-]) ([0-9a-f]{40,64})(?: (.*))?", line)
        if match is None:
            raise AssessmentError("patch-id-parse-error", "cannot parse git cherry output")
        marker, oid, subject = match.groups()
        reported.add(oid)
        rows.append({
            "sha": oid,
            "relation": "equivalent" if marker == "-" else "unmatched",
            "subject": subject or "",
        })
    closure_oids = {item.oid for item in closure}
    omitted_merges = sum(item.is_merge and item.oid not in reported for item in closure)
    incomplete = len(rows) < len(closure)
    return {
        "decisive": False,
        "outcome": (
            "truncated" if incomplete else
            "matched" if any(row["relation"] == "equivalent" for row in rows) else
            "not-matched" if rows else "not-applicable"
        ),
        "status": "incomplete" if incomplete else "complete",
        "closure_commit_count": len(closure),
        "reported_commit_count": len(rows),
        "omitted_merge_count": omitted_merges,
        "unreported_commit_count": len(closure_oids - reported),
        "commits": rows,
    }


def _task_observation(git: Git, branch: str, corpus: CorpusResult) -> dict[str, Any]:
    started = time.monotonic()
    task_ids = sorted({f"T-{value}" for value in TASK_ID_RE.findall(branch)}, key=lambda item: int(item[2:]))
    hits: list[dict[str, Any]] = []
    truncated = False
    for task_id in task_ids:
        if git.remaining() <= 0:
            raise AssessmentError("assessment-timeout", "task index deadline expired", outcome="truncated")
        for path, text in corpus.texts.items():
            if git.remaining() <= 0:
                raise AssessmentError("assessment-timeout", "task index deadline expired", outcome="truncated")
            for line_number, line in enumerate(text.splitlines(), 1):
                if line_number % 256 == 0 and git.remaining() <= 0:
                    raise AssessmentError("assessment-timeout", "task index deadline expired", outcome="truncated")
                if task_id in line:
                    hits.append({"task_id": task_id, "path": path, "line": line_number})
                    if len(hits) >= MAX_LEDGER_HITS:
                        truncated = True
                        break
            if truncated:
                break
        if truncated:
            break
    outcome = (
        "truncated" if truncated else "matched" if hits else
        "not-matched" if task_ids else "not-applicable"
    )
    if task_ids and corpus.outcome in {"error", "truncated"}:
        outcome = corpus.outcome
    return {
        "decisive": False,
        "outcome": outcome,
        "task_ids": task_ids,
        "hits": hits,
        "truncated": truncated,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }


def _refs_moved(
    start_branch: str,
    start_resolved_as: str,
    start_main: str,
    end_branch: str,
    end_resolved_as: str,
    end_main: str,
) -> bool:
    # M9: the start/end ref comparison exists only here.
    return (start_branch, start_resolved_as, start_main) != (
        end_branch, end_resolved_as, end_main,
    )


def _aggregate_verdict(
    units: Sequence[dict[str, Any]],
    closure_count: int,
    *,
    refs_moved: bool,
    ledger_probe_outcome: str,
) -> dict[str, Any]:
    if refs_moved:
        return _decision("indeterminate", "refs-moved")
    if closure_count == 0:
        return _decision("landed", "branch-closure-empty")
    if not units:
        return _decision("indeterminate", "closure-has-no-introduced-state")
    # M2': this single disabled gate keeps ledger_probe non-decisive.
    if False and ledger_probe_outcome == "matched":
        return _decision("landed", "ledger-probe-observation")
    verdicts = [unit["decision"]["verdict"] for unit in units]
    # M10: any indeterminate unit propagates; landed requires an all-landed conjunction.
    if any(verdict == "indeterminate" for verdict in verdicts):
        return _decision("indeterminate", "one-or-more-states-unproven")
    if all(verdict == "landed" for verdict in verdicts):
        return _decision("landed", "all-introduced-states-proven")
    if any(verdict == "not-landed" for verdict in verdicts):
        return _decision("not-landed", "closed-world-negative-proof")
    return _decision("indeterminate", "one-or-more-states-unproven")


def _conjoin_file_decisions(units: Sequence[dict[str, Any]]) -> dict[str, Any]:
    verdicts = [unit["decision"]["verdict"] for unit in units]
    if any(value == "indeterminate" for value in verdicts):
        return _decision("indeterminate", "one-or-more-proof-units-unproven")
    if all(value == "landed" for value in verdicts):
        return _decision("landed", "all-proof-units-proven")
    if any(value == "not-landed" for value in verdicts):
        return _decision("not-landed", "closed-world-negative-proof")
    return _decision("indeterminate", "one-or-more-proof-units-unproven")


def _aggregate_files(units: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, unit in enumerate(units):
        by_path.setdefault(unit["path"], []).append((index, unit))
    files: list[dict[str, Any]] = []
    for path in sorted(by_path):
        indexed = by_path[path]
        path_units = [unit for _, unit in indexed]
        files.append({
            "path": path,
            "decision": _conjoin_file_decisions(path_units),
            "proof_unit_count": len(path_units),
            "proof_unit_indices": [index for index, _ in indexed],
        })
    return files


def _limits_dict(
    timeout_seconds: float,
    max_files: int,
    history_candidates: int,
    history_scan_commits: int,
    max_closure_commits: int,
) -> dict[str, Any]:
    return {
        "timeout_seconds": timeout_seconds,
        "max_files": max_files,
        "history_candidates": history_candidates,
        "history_scan_commits": history_scan_commits,
        "max_closure_commits": max_closure_commits,
        "max_text_bytes": MAX_TEXT_BYTES,
        "max_ledger_hits": MAX_LEDGER_HITS,
    }


def assess(
    repo: Path,
    branch: str,
    *,
    main: str = "main",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_files: int = DEFAULT_MAX_FILES,
    history_candidates: int = DEFAULT_HISTORY_CANDIDATES,
    history_scan_commits: int = DEFAULT_HISTORY_SCAN_COMMITS,
    max_closure_commits: int = DEFAULT_MAX_CLOSURE_COMMITS,
) -> dict[str, Any]:
    assess_started = time.monotonic()
    repo = repo.resolve()
    limits = _limits_dict(
        timeout_seconds, max_files, history_candidates, history_scan_commits,
        max_closure_commits,
    )
    payload = _base_payload(repo, branch, main, limits)
    git = Git(repo, time.monotonic() + timeout_seconds)
    active_phase = "preflight"
    try:
        actual_root = _repo_root(git)
        payload["repository"]["root"] = str(actual_root)
        git.repo = actual_root
        start_resolution = _target_resolution_candidates(git, branch)
        _record_target_resolution(payload["branch"], start_resolution)
        start_branch, start_resolved_as = _select_target_resolution(
            branch, start_resolution,
        )
        start_main = _resolve_ref(git, main)
        payload["branch"]["tip"] = start_branch
        payload["branch"]["resolved_as"] = start_resolved_as
        payload["main"]["tip"] = start_main
        _repository_preflight(git)
        payload["phase_outcomes"]["preflight"] = "matched"

        active_phase = "closure"
        closure, closure_observation = _enumerate_closure(
            git, start_branch, start_main, max_closure_commits,
        )
        payload["closure"] = closure_observation
        payload["phase_outcomes"]["closure"] = closure_observation["outcome"]
        if closure_observation["outcome"] == "truncated":
            raise AssessmentError(
                "closure-limit-exceeded", "branch-only commit closure exceeded limit",
                outcome="truncated",
            )

        active_phase = "proof"
        states = _introduced_states(git, closure)
        paths = {state.required.path for state in states}
        if len(paths) > max_files:
            raise AssessmentError("file-limit-exceeded", "introduced path count exceeded limit", outcome="truncated")
        payload["summary"]["changed_files"] = len(paths)
        payload["summary"]["introduced_path_count"] = len(paths)
        payload["summary"]["tip_net_changed_files"] = _tip_net_path_count(
            git, start_main, start_branch,
        )
        payload["summary"]["files_enumerated"] = True
        payload["summary"]["proof_units"] = len(states)

        receipt_registry = _read_receipts(git, start_main) if any(
            SPOOL_RE.fullmatch(state.required.path) for state in states
        ) else ReceiptRegistry("not-matched", "no-spool-fragment", {}, 0)
        units: list[dict[str, Any]] = []
        pending_probes: list[dict[str, Any]] = []
        verbatim_observations: list[dict[str, Any]] = []
        for state in states:
            unit, _unit_incomplete, pending = _proof_unit(
                git, state, start_main, history_candidates, receipt_registry,
            )
            units.append(unit)
            verbatim_observations.append(unit.pop("verbatim_observation"))
            if pending is not None:
                pending_probes.append(pending)
        payload["phase_outcomes"]["proof"] = "matched"

        active_phase = "history_scan"
        negative_units = [unit for unit in units if unit["decision"]["verdict"] == "not-landed"]
        if negative_units:
            try:
                payload["history_scan"] = _scan_main_history(
                    git, start_main, history_scan_commits,
                )
            except AssessmentError as exc:
                payload["history_scan"].update({
                    "outcome": exc.outcome,
                    "complete": False,
                    "reason": exc.code,
                })
            payload["phase_outcomes"]["history_scan"] = payload["history_scan"]["outcome"]
            history_evidence = {
                "layer": "closed-world-history-scan",
                "decisive": True,
                **payload["history_scan"],
            }
            for unit in negative_units:
                unit["evidence"].append(history_evidence.copy())
            if not payload["history_scan"]["complete"]:
                for unit in negative_units:
                    unit["decision"] = _decision(
                        "indeterminate", payload["history_scan"]["reason"],
                    )
                    unit["integrity_incomplete"] = True
        else:
            payload["history_scan"].update({
                "outcome": "not-applicable",
                "complete": False,
                "reason": "positive-proof-does-not-require-full-history-scan",
            })
            payload["phase_outcomes"]["history_scan"] = "not-applicable"

        active_phase = "observations"
        task_ids_present = bool(TASK_ID_RE.search(branch))
        corpus: CorpusResult | None = None
        if pending_probes or task_ids_present:
            try:
                corpus = _ledger_corpus(git, start_main)
            except AssessmentError as exc:
                corpus = CorpusResult(
                    {}, exc.outcome, 0, 0, 0, 1,
                    ({"path": "*", "code": exc.code},), False, 0.0,
                )
            payload["observations"]["ledger_corpus"] = corpus.as_json()
        else:
            payload["observations"]["ledger_corpus"]["outcome"] = "not-applicable"

        ledger_observations: list[dict[str, Any]] = []
        probe_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        if corpus is not None:
            for pending in pending_probes:
                try:
                    probe = _ledger_probe(git, pending["path"], pending["blob"], corpus)
                except AssessmentError as exc:
                    probe = {
                        "decisive": False,
                        "path": pending["path"],
                        "outcome": exc.outcome,
                        "reason": exc.code,
                        "unit_count": None,
                        "matched_unit_count": None,
                        "all_units_matched": False,
                        "single_file_max_matched_unit_count": None,
                        "signal_strength": None,
                        "identity_unit": {
                            "kind": "none",
                            "value": None,
                            "outcome": "not-applicable",
                            "reason": exc.code,
                            "hit_targets": [],
                        },
                        "hit_targets": [],
                        "hits": [],
                        "truncated": exc.outcome == "truncated",
                        "elapsed_seconds": 0.0,
                    }
                ledger_observations.append(probe)
                probe_by_key[(pending["path"], pending["whole_file_sha256"])] = probe
        payload["proof_units"] = units
        payload["files"] = _aggregate_files(units)
        ledger_outcomes = {item["outcome"] for item in ledger_observations}
        payload["observations"]["ledger_probe"] = {
            "decisive": False,
            "outcome": (
                "error" if "error" in ledger_outcomes else
                "truncated" if "truncated" in ledger_outcomes else
                "matched" if "matched" in ledger_outcomes else
                "not-matched" if ledger_observations else "not-applicable"
            ),
            "signal_strength": next((
                strength for strength in ("strong", "weak-positive", "weak")
                if any(
                    item.get("signal_strength") == strength
                    for item in ledger_observations
                )
            ), None),
            "probes": ledger_observations,
        }

        unresolved_by_path: dict[str, list[dict[str, Any]]] = {}
        for pending in pending_probes:
            unresolved_by_path.setdefault(pending["path"], []).append(pending)
        unresolved: list[dict[str, Any]] = []
        for path in sorted(unresolved_by_path):
            items = unresolved_by_path[path]
            digests = sorted({str(item["whole_file_sha256"]) for item in items})
            body_digests = sorted({
                str(item["canonical_body_sha256"])
                for item in items if item["canonical_body_sha256"] is not None
            })
            probes = [
                probe_by_key[(path, str(item["whole_file_sha256"]))]
                for item in items
                if (path, str(item["whole_file_sha256"])) in probe_by_key
            ]
            target_paths = sorted({
                target["path"]
                for probe in probes for target in probe.get("hit_targets", [])
            })
            hit_targets = [{
                "path": target_path,
                "matched_units": max(
                    target["matched_units"]
                    for probe in probes for target in probe.get("hit_targets", [])
                    if target["path"] == target_path
                ),
                "matched_structural_units": max(
                    target["matched_structural_units"]
                    for probe in probes for target in probe.get("hit_targets", [])
                    if target["path"] == target_path
                ),
                "identity_unit_matched": any(
                    target["identity_unit_matched"]
                    for probe in probes for target in probe.get("hit_targets", [])
                    if target["path"] == target_path
                ),
            } for target_path in target_paths]
            signal_strength = next((
                strength for strength in ("strong", "weak-positive", "weak")
                if any(probe.get("signal_strength") == strength for probe in probes)
            ), None)
            identity_unit = next((
                probe["identity_unit"]
                for outcome in ("matched", "not-matched", "not-applicable")
                for probe in probes
                if probe.get("identity_unit", {}).get("outcome") == outcome
            ), {
                "kind": "none",
                "value": None,
                "outcome": "not-applicable",
                "reason": "probe-not-run",
                "hit_targets": [],
            })
            unresolved.append({
                "path": path,
                "whole_file_sha256": digests[0] if len(digests) == 1 else None,
                "whole_file_sha256s": digests,
                "canonical_body_sha256": body_digests[0] if len(body_digests) == 1 else None,
                "receipt_present": False,
                "matched_unit_count": max(
                    (probe.get("matched_unit_count") or 0 for probe in probes), default=0,
                ),
                "unit_count": max(
                    (probe.get("unit_count") or 0 for probe in probes), default=0,
                ),
                "signal_strength": signal_strength,
                "identity_unit": identity_unit,
                "hit_targets": hit_targets,
            })
        payload["unresolved_fragment_candidates"] = unresolved

        verbatim_outcomes = {item["outcome"] for item in verbatim_observations}
        payload["observations"]["verbatim"] = {
            "decisive": False,
            "outcome": (
                "truncated" if "truncated" in verbatim_outcomes else
                "error" if "error" in verbatim_outcomes else
                "matched" if "matched" in verbatim_outcomes else
                "not-matched" if "not-matched" in verbatim_outcomes else
                "not-applicable"
            ),
            "entries": verbatim_observations,
        }
        try:
            payload["observations"]["patch_id"] = _patch_observation(
                git, start_main, start_branch, closure
            )
        except AssessmentError as exc:
            payload["observations"]["patch_id"].update({
                "outcome": exc.outcome, "status": "incomplete", "reason": exc.code,
            })
        if corpus is not None:
            try:
                payload["observations"]["task_index"] = _task_observation(
                    git, branch, corpus,
                )
            except AssessmentError as exc:
                payload["observations"]["task_index"].update({
                    "outcome": exc.outcome, "reason": exc.code, "elapsed_seconds": 0.0,
                })
        else:
            payload["observations"]["task_index"]["outcome"] = "not-applicable"
        payload["phase_outcomes"]["observations"] = "matched"

        active_phase = "ref_snapshot"
        end_resolution = _target_resolution_candidates(git, branch)
        end_branch, end_resolved_as = _select_target_resolution(
            branch, end_resolution,
        )
        end_main = _resolve_ref(git, main)
        moved = _refs_moved(
            start_branch, start_resolved_as, start_main,
            end_branch, end_resolved_as, end_main,
        )
        payload["ref_snapshot"].update({
            "matches_start_at_end": not moved,
            "end_branch_tip": end_branch,
            "end_resolved_as": end_resolved_as,
            "end_main_tip": end_main,
        })
        payload["phase_outcomes"]["ref_snapshot"] = "matched"
        if moved:
            payload["issues"].append(_issue("refs-moved", "branch or main ref moved during assessment"))

        counts = {name: 0 for name in ("landed", "not-landed", "indeterminate")}
        for unit in units:
            counts[unit["decision"]["verdict"]] += 1
        payload["summary"].update({
            "landed": counts["landed"],
            "not_landed": counts["not-landed"],
            "indeterminate": counts["indeterminate"],
        })
        payload["unproven_paths"] = sorted({
            file["path"] for file in payload["files"]
            if file["decision"]["verdict"] == "indeterminate"
        })
        payload["negative_paths"] = sorted({
            file["path"] for file in payload["files"]
            if file["decision"]["verdict"] == "not-landed"
        })
        payload["receipt_missing_paths"] = sorted({
            unit["path"] for unit in units
            if any(
                evidence["layer"] == "folded-receipt"
                and evidence["outcome"] == "not-matched"
                for evidence in unit["evidence"]
            )
        })
        payload["decision"] = _aggregate_verdict(
            units, len(closure), refs_moved=moved,
            ledger_probe_outcome=payload["observations"]["ledger_probe"]["outcome"],
        )
    except (AssessmentError, UnicodeDecodeError) as exc:
        if isinstance(exc, AssessmentError):
            code, message, outcome = exc.code, exc.message, exc.outcome
        else:
            code, message, outcome = "git-output-decode-error", "git output could not be parsed", "error"
        payload["phase_outcomes"][active_phase] = outcome
        if active_phase == "closure" and payload["closure"]["outcome"] == "not-run":
            payload["closure"]["outcome"] = outcome
        if active_phase == "history_scan":
            payload["history_scan"].update({
                "outcome": outcome, "complete": False, "reason": code,
            })
        payload["issues"].append(_issue(code, message))
        payload["decision"] = _decision("indeterminate", code)
        if not payload["summary"]["files_enumerated"]:
            payload["summary"]["changed_files"] = None
            payload["summary"]["introduced_path_count"] = None
            payload["summary"]["proof_units"] = None
    payload["timing"]["total_elapsed_seconds"] = round(
        time.monotonic() - assess_started, 6,
    )
    payload["timing"]["git_child_processes"] = git.command_count
    return payload


def _bounded_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not (0.0 < parsed <= 300.0):
        raise argparse.ArgumentTypeError("must be greater than 0 and at most 300")
    return parsed


def _bounded_int(low: int, high: int):
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if not low <= parsed <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return parsed
    return parse


def _parser() -> CliParser:
    parser = CliParser(description=__doc__)
    parser.add_argument(
        "branch_or_commit",
        metavar="BRANCH_OR_COMMIT",
        help="local branch name or commit-ish resolving to a commit",
    )
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--main", default="main", help="local main branch name")
    parser.add_argument("--timeout-seconds", type=_bounded_float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-files", type=_bounded_int(1, 4096), default=DEFAULT_MAX_FILES)
    parser.add_argument(
        "--history-candidates", type=_bounded_int(1, 100_000),
        default=DEFAULT_HISTORY_CANDIDATES,
    )
    parser.add_argument(
        "--history-scan-commits", type=_bounded_int(1, 1_000_000),
        default=DEFAULT_HISTORY_SCAN_COMMITS,
    )
    parser.add_argument(
        "--max-closure-commits", type=_bounded_int(1, 100_000),
        default=DEFAULT_MAX_CLOSURE_COMMITS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    payload = assess(
        args.repo,
        args.branch_or_commit,
        main=args.main,
        timeout_seconds=args.timeout_seconds,
        max_files=args.max_files,
        history_candidates=args.history_candidates,
        history_scan_commits=args.history_scan_commits,
        max_closure_commits=args.max_closure_commits,
    )
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return EXIT_BY_VERDICT[payload["decision"]["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
