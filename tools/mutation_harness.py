#!/usr/bin/env python3
"""Versioned JSON spec に従い、固定 HEAD へ一時変異を注入して検査する。"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import difflib
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if os.fspath(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_REPO_ROOT))

from orchestrator.campaign import mutation_attempt_marker, site_policy  # noqa: E402


SPEC_SCHEMA = "izanagi-dev-wave-mutation-spec/v1"
LEDGER_SCHEMA = "izanagi-dev-wave-mutation/v4"
ATTEMPT_SCHEMA = "izanagi-dev-wave-mutation-attempts/v1"
LOCAL_ATTEMPT_SCHEMA = "izanagi-dev-wave-mutation-attempts-local/v1"
ORPHAN_STOP_SCHEMA = "izanagi-dev-wave-mutation-orphan-stop/v1"
ORPHAN_HOLD_SCHEMA = "pegasus-orphan-hold/v1"
ORPHAN_HOLD_NAME = "orphan-hold.json"
ORPHAN_HOLD_DIR_NAME = "orphan-holds"
_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV = (
    "IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE"
)
_DISPATCH_OVERALL_GRACE_OVERRIDE_ENV = (
    "IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE"
)
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
RECEIPT_LINE_RE = re.compile(
    r"^\[Pegasus dispatch\] receipt を (.+) へ保存しました \(child rc=(-?\d+)\)$"
)
JOB_STDOUT_RE = re.compile(r"^izdw-[A-Za-z0-9._-]+\.o\S+$")
TERMINAL_STATUSES = frozenset({"KILLED", "SURVIVED", "MISMATCH", "TIMEOUT"})
EXPECTED_STATUSES = frozenset({"KILLED", "SURVIVED", "TIMEOUT"})
CATEGORIES = frozenset({"negative", "positive", "both-layers"})
PYTEST_NORMAL_RCS = frozenset({0, 1})
ARTIFACT_FIELDS = frozenset(
    {"runner_mode", "receipt_path", "job_stdout_path", "stdout", "stdout_sha256"}
)
COLLECTION_FIELDS = frozenset(
    {
        "status",
        "rc",
        "collected_nodes",
        "duration_s",
        "artifact",
        "repo_head",
        "spec_sha256",
        "runner_sha256",
        "tool_sha256",
    }
)
BASELINE_FIELDS = frozenset(
    {
        "status",
        "rc",
        "failed_nodes",
        "timed_out",
        "duration_s",
        "artifact_error",
        "artifact",
        "test_output_sha256",
        "test_output_tail",
        "repo_head",
        "spec_sha256",
        "registration_sha256",
        "runner_sha256",
        "tool_sha256",
        "collection_sha256",
    }
)
MUTATION_RECORD_FIELDS = frozenset(
    {
        "id",
        "category",
        "replacements",
        "expected_nodes",
        "expected_status",
        "hang_risk",
        "status",
        "matches_expectation",
        "rc",
        "failed_nodes",
        "timed_out",
        "duration_s",
        "artifact_error",
        "artifact",
        "anchor_counts",
        "injection_diff_sha256",
        "test_output_sha256",
        "test_output_tail",
        "repo_head",
        "spec_sha256",
        "registration_sha256",
        "runner_sha256",
        "tool_sha256",
        "collection_sha256",
    }
)
ATTEMPT_FIELDS = frozenset(
    {
        "run_attempt_ordinal",
        "wrapper_attempt_ordinal",
        "phase",
        "mutation_id",
        "state",
        "started_at",
        "finished_at",
        "rc",
        "timed_out",
        "artifact_error",
        "console_sha256",
        "request",
    }
)
ATTEMPT_REQUEST_FIELDS = frozenset(
    {"request_id", "submission_dir", "receipt_path", "job_stdout_path", "outcome_rc"}
)


class HarnessError(RuntimeError):
    """検査の信頼性を維持できない場合の fail-closed 停止。"""


class OrphanHoldStop(HarnessError):
    """dispatch job が残り得るため source を保全して停止する。"""

    def __init__(
        self,
        *,
        phase: str,
        mutation_id: str | None,
        hold_path: Path,
        source_state: str,
        dirty_paths: Sequence[str],
        active_record: dict[str, Any] | None = None,
        reason_code: str = "orphan-hold",
        hold_latched: bool = True,
        hold_error: str | None = None,
        origin_error_type: str | None = None,
        origin_error_message: str | None = None,
        verification_error_type: str | None = None,
        verification_error_message: str | None = None,
    ) -> None:
        self.phase = phase
        self.mutation_id = mutation_id
        self.hold_path = hold_path
        self.source_state = source_state
        self.dirty_paths = tuple(sorted(dirty_paths))
        self.active_record = active_record
        self.reason_code = reason_code
        self.hold_latched = hold_latched
        self.hold_error = hold_error
        self.origin_error_type = origin_error_type
        self.origin_error_message = origin_error_message
        self.verification_error_type = verification_error_type
        self.verification_error_message = verification_error_message
        super().__init__(f"orphan hold: phase={phase}, hold={hold_path}")

    def record_origin_error(self, exc: BaseException) -> None:
        self.origin_error_type = type(exc).__name__
        self.origin_error_message = str(exc)

    def record_verification_error(self, exc: BaseException) -> None:
        self.verification_error_type = type(exc).__name__
        self.verification_error_message = str(exc)


class SignalAbort(BaseException):
    """SIGINT/SIGTERM を unwind へ変換し、親側の復元判断を必ず通す。"""

    def __init__(self, signum: int) -> None:
        self.signum = signum
        self.orphan_stop: OrphanHoldStop | None = None
        super().__init__(f"signal {signum}")


def _dispatch_orphan_hold_path(repo: Path) -> Path:
    return repo / "output" / "pegasus-dispatch" / ORPHAN_HOLD_NAME


def _dispatch_orphan_hold_present(repo: Path) -> bool:
    """canonical control root 内の aggregate/request ledger を fail-closed で調べる。"""

    control_root = repo / "output" / "pegasus-dispatch"
    if _path_present_fail_closed(control_root / ORPHAN_HOLD_NAME):
        return True
    ledger = control_root / ORPHAN_HOLD_DIR_NAME
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        return True
    try:
        descriptor = os.open(
            ledger,
            os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0),
        )
    except FileNotFoundError:
        return False
    except OSError:
        return True
    blocker = False
    try:
        with os.scandir(descriptor) as entries:
            blocker = any(entry.name.endswith(".json") for entry in entries)
    except OSError:
        blocker = True
    try:
        os.close(descriptor)
    except OSError:
        blocker = True
    return blocker


def _path_present_fail_closed(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _write_json_create_only(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            json.dump(document, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _latch_dispatch_orphan_hold(
    repo: Path,
    *,
    phase: str,
    mutation_id: str | None,
    result: dict[str, Any],
    reason: str,
) -> tuple[Path, str | None]:
    path = _dispatch_orphan_hold_path(repo)
    request = result.get("request")
    request = request if isinstance(request, dict) else {}
    payload = {
        "schema_version": ORPHAN_HOLD_SCHEMA,
        "reason": reason,
        "submission_dir": request.get("submission_dir"),
        "request_id": request.get("request_id"),
        "job_name": None,
        "qdel": {
            "job_may_remain": True,
            "attempted": False,
            "returncode": None,
            "exception": None,
            "gate": {"reason": reason},
        },
        "source": {
            "producer": "mutation-harness",
            "phase": phase,
            "mutation_id": mutation_id,
        },
        "recovery": {
            "order": (
                "qstat で対象の不在または終端を確認し、dirty source を復元し、"
                "clean/HEAD を確認してから hold を手動削除する"
            ),
            "manual-qdel-warning": (
                "手動 qdel は F47 の submission-disabled.json を武装させ、"
                "その解除もユーザー手番になる"
            ),
        },
    }
    try:
        _write_json_create_only(path, payload)
    except FileExistsError:
        return path, None
    except OSError as exc:
        return path, f"{type(exc).__name__}: {exc}"
    return path, None


def _dispatch_orphan_stop(
    repo: Path,
    *,
    runner_mode: str,
    phase: str,
    mutation_id: str | None,
    source_state: str,
    dirty_paths: Sequence[str],
    result: dict[str, Any] | None = None,
) -> OrphanHoldStop | None:
    timed_out = result is not None and result.get("timed_out") is True
    hold = _dispatch_orphan_hold_path(repo)
    if runner_mode != "dispatch":
        if _dispatch_orphan_hold_present(repo):
            return OrphanHoldStop(
                phase=phase,
                mutation_id=mutation_id,
                hold_path=hold,
                source_state=source_state,
                dirty_paths=dirty_paths,
                active_record=result,
            )
        submission_state = (
            result.get("dispatch_submission", {}).get("state")
            if isinstance(result, dict)
            and isinstance(result.get("dispatch_submission"), dict)
            else None
        )
        if submission_state is None and isinstance(result, dict):
            if result.get("new_dispatch_submission") is True:
                submission_state = "matched"
        if not timed_out or submission_state not in {"matched", "indeterminate"}:
            return None
        return OrphanHoldStop(
            phase=phase,
            mutation_id=mutation_id,
            hold_path=hold,
            source_state=source_state,
            dirty_paths=dirty_paths,
            active_record=result,
            reason_code=(
                "runner-mode-violation"
                if submission_state == "matched"
                else "runner-mode-evidence-unavailable"
            ),
            hold_latched=False,
        )
    hold_error: str | None = None
    receipt_requires_hold = result is not None and (
        result.get("job_may_remain") is True
        or result.get("hold_error") is not None
    )
    if timed_out or receipt_requires_hold:
        if timed_out:
            hold_reason = "dispatch-runner-timeout"
        else:
            hold_reason = "dispatch-receipt-job-may-remain"
        if not _dispatch_orphan_hold_present(repo):
            hold, hold_error = _latch_dispatch_orphan_hold(
                repo,
                phase=phase,
                mutation_id=mutation_id,
                result=result,
                reason=hold_reason,
            )
        return OrphanHoldStop(
            phase=phase,
            mutation_id=mutation_id,
            hold_path=hold,
            source_state=source_state,
            dirty_paths=dirty_paths,
            active_record=result,
            hold_error=hold_error,
        )
    if _dispatch_orphan_hold_present(repo):
        return OrphanHoldStop(
            phase=phase,
            mutation_id=mutation_id,
            hold_path=hold,
            source_state=source_state,
            dirty_paths=dirty_paths,
            active_record=result,
        )
    return None


@dataclasses.dataclass(frozen=True)
class Replacement:
    file: str
    old: str
    new: str


@dataclasses.dataclass(frozen=True)
class Mutation:
    id: str
    category: str
    replacements: tuple[Replacement, ...]
    expected_nodes: tuple[str, ...]
    expected_status: str
    hang_risk: bool


@dataclasses.dataclass(frozen=True)
class MutationSpec:
    mutations: tuple[Mutation, ...]
    estimated_run_seconds: float
    timeout_seconds: float
    hang_timeout_seconds: float


@dataclasses.dataclass
class AttemptRecorder:
    """invocation と scheduler request を atomic sidecar へ保存する。"""

    path: Path
    wrapper_attempt_ordinal: int
    document: dict[str, Any]

    def started(self, *, phase: str, mutation_id: str | None) -> int:
        ordinal = len(self.document["attempts"]) + 1
        self.document["attempts"].append(
            {
                "run_attempt_ordinal": ordinal,
                "wrapper_attempt_ordinal": self.wrapper_attempt_ordinal,
                "phase": phase,
                "mutation_id": mutation_id,
                "state": "started",
                "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "finished_at": None,
                "rc": None,
                "timed_out": False,
                "artifact_error": None,
                "console_sha256": None,
                "request": None,
            }
        )
        _write_json_atomic(self.path, self.document)
        return ordinal

    def finished(self, ordinal: int, result: dict[str, Any]) -> None:
        attempts = self.document["attempts"]
        if ordinal < 1 or ordinal > len(attempts):
            raise HarnessError("attempt ordinal が sidecar 範囲外")
        entry = attempts[ordinal - 1]
        if entry["run_attempt_ordinal"] != ordinal or entry["state"] != "started":
            raise HarnessError("attempt の started→finished 遷移が不正")
        output = result.get("output", "")
        if not isinstance(output, str):
            raise HarnessError("attempt console output が文字列でない")
        entry.update(
            {
                "state": "finished",
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "rc": result.get("rc"),
                "timed_out": result.get("timed_out", False),
                "artifact_error": result.get("artifact_error"),
                "console_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                "request": result.get("request"),
            }
        )
        _write_json_atomic(self.path, self.document)


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise HarnessError(
            f"{label} の field 集合が不正: missing={missing}, unknown={unknown}"
        )


def _positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise HarnessError(f"{label} は正の数でなければならない")
    return float(value)


def _safe_relpath(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise HarnessError(f"{label} は非空の POSIX 相対 path でなければならない")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise HarnessError(f"{label} が安全な正規相対 path でない: {value!r}")
    return value


def _json_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path, label: str) -> str:
    try:
        if path.is_symlink() or not path.is_file():
            raise HarnessError(f"{label} は symlink でない通常 file でなければならない")
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except HarnessError:
        raise
    except OSError as exc:
        raise HarnessError(f"{label} を hash できない: {exc}") from exc


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise HarnessError(f"{label} は小文字 hex の SHA-256 でなければならない")
    return value


def _load_spec(path: Path) -> tuple[MutationSpec, str]:
    try:
        if path.is_symlink() or not path.is_file():
            raise HarnessError("--spec は symlink でない通常ファイルでなければならない")
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except HarnessError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarnessError(f"spec JSON を読めない: {exc}") from exc
    if not isinstance(document, dict):
        raise HarnessError("spec JSON の root が object でない")
    _require_exact_keys(
        document,
        {
            "schema",
            "estimated_run_seconds",
            "timeout_seconds",
            "hang_timeout_seconds",
            "mutations",
        },
        "spec",
    )
    if document["schema"] != SPEC_SCHEMA:
        raise HarnessError(f"未知の spec schema: {document['schema']!r}")
    raw_mutations = document["mutations"]
    if not isinstance(raw_mutations, list) or not raw_mutations:
        raise HarnessError("spec.mutations は非空 list でなければならない")

    mutations: list[Mutation] = []
    ids: set[str] = set()
    for index, raw_mutation in enumerate(raw_mutations):
        label = f"mutations[{index}]"
        if not isinstance(raw_mutation, dict):
            raise HarnessError(f"{label} が object でない")
        _require_exact_keys(
            raw_mutation,
            {
                "id",
                "category",
                "replacements",
                "expected_nodes",
                "expected_status",
                "hang_risk",
            },
            label,
        )
        mutation_id = raw_mutation["id"]
        if (
            not isinstance(mutation_id, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", mutation_id) is None
        ):
            raise HarnessError(f"{label}.id が安全な非空 ID でない")
        if mutation_id in ids:
            raise HarnessError(f"変異 ID が重複: {mutation_id}")
        ids.add(mutation_id)
        category = raw_mutation["category"]
        if category not in CATEGORIES:
            raise HarnessError(f"{mutation_id}: category が未知: {category!r}")
        expected_status = raw_mutation["expected_status"]
        if expected_status not in EXPECTED_STATUSES:
            raise HarnessError(f"{mutation_id}: expected_status が未知: {expected_status!r}")
        hang_risk = raw_mutation["hang_risk"]
        if not isinstance(hang_risk, bool):
            raise HarnessError(f"{mutation_id}: hang_risk が bool でない")
        if expected_status == "TIMEOUT" and not hang_risk:
            raise HarnessError(f"{mutation_id}: TIMEOUT 期待には hang_risk=true が必要")

        raw_nodes = raw_mutation["expected_nodes"]
        if not isinstance(raw_nodes, list) or any(
            not isinstance(node, str) or not node.strip() for node in raw_nodes
        ):
            raise HarnessError(f"{mutation_id}: expected_nodes が文字列 list でない")
        expected_nodes = tuple(raw_nodes)
        if len(set(expected_nodes)) != len(expected_nodes):
            raise HarnessError(f"{mutation_id}: expected_nodes が重複")
        if expected_status == "KILLED" and not expected_nodes:
            raise HarnessError(f"{mutation_id}: KILLED 期待には expected_nodes が必要")
        if expected_status in {"SURVIVED", "TIMEOUT"} and expected_nodes:
            raise HarnessError(
                f"{mutation_id}: {expected_status} 期待では expected_nodes は空でなければならない"
            )

        raw_replacements = raw_mutation["replacements"]
        if not isinstance(raw_replacements, list) or not raw_replacements:
            raise HarnessError(f"{mutation_id}: replacements は非空 list でなければならない")
        replacements: list[Replacement] = []
        for replacement_index, raw_replacement in enumerate(raw_replacements):
            replacement_label = f"{label}.replacements[{replacement_index}]"
            if not isinstance(raw_replacement, dict):
                raise HarnessError(f"{replacement_label} が object でない")
            _require_exact_keys(raw_replacement, {"file", "old", "new"}, replacement_label)
            old = raw_replacement["old"]
            new = raw_replacement["new"]
            if not isinstance(old, str) or not old:
                raise HarnessError(f"{replacement_label}.old は非空文字列必須")
            if not isinstance(new, str) or new == old:
                raise HarnessError(f"{replacement_label}.new は old と異なる文字列必須")
            replacements.append(
                Replacement(
                    file=_safe_relpath(raw_replacement["file"], f"{replacement_label}.file"),
                    old=old,
                    new=new,
                )
            )
        mutations.append(
            Mutation(
                id=mutation_id,
                category=category,
                replacements=tuple(replacements),
                expected_nodes=expected_nodes,
                expected_status=expected_status,
                hang_risk=hang_risk,
            )
        )

    spec = MutationSpec(
        mutations=tuple(mutations),
        estimated_run_seconds=_positive_number(
            document["estimated_run_seconds"], "estimated_run_seconds"
        ),
        timeout_seconds=_positive_number(document["timeout_seconds"], "timeout_seconds"),
        hang_timeout_seconds=_positive_number(
            document["hang_timeout_seconds"], "hang_timeout_seconds"
        ),
    )
    return spec, hashlib.sha256(raw).hexdigest()


def _git_env() -> dict[str, str]:
    allowed = {"GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT"}
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") or key in allowed
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        env=_git_env(),
        text=text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _repo_head(repo: Path) -> str:
    root = _git(repo, "rev-parse", "--show-toplevel")
    if root.returncode != 0:
        raise HarnessError(f"repo root を確認できない: {root.stderr.strip()}")
    try:
        actual_root = Path(root.stdout.strip()).resolve(strict=True)
    except OSError as exc:
        raise HarnessError(f"repo root を解決できない: {exc}") from exc
    if actual_root != repo:
        raise HarnessError("--repo は git worktree root そのものを指定する必要がある")
    result = _git(repo, "rev-parse", "--verify", "HEAD")
    if result.returncode != 0:
        raise HarnessError(f"repo HEAD を取得できない: {result.stderr.strip()}")
    return result.stdout.strip()


def _assert_clean_tracked(repo: Path) -> None:
    status = _git(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=none",
    )
    if status.returncode != 0:
        raise HarnessError(f"tracked/index cleanliness を確認できない: {status.stderr.strip()}")
    if status.stdout:
        paths = [line.rstrip() for line in status.stdout.splitlines()]
        raise HarnessError(f"tracked/index dirt または untracked file があるため停止: {paths}")


def _assert_only_expected_dirt(
    repo: Path, head: str, allowed_dirty: Sequence[str]
) -> None:
    pathspecs = [".", *(f":(exclude){rel}" for rel in allowed_dirty)]
    diff = _git(repo, "diff", "--quiet", head, "--", *pathspecs)
    if diff.returncode == 1:
        raise HarnessError("runner/test bytes に固定 HEAD 外の変更を検出")
    if diff.returncode != 0:
        raise HarnessError(f"runner/test bytes を固定 HEAD と照合できない: {diff.stderr.strip()}")
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard")
    if untracked.returncode != 0:
        raise HarnessError(f"untracked runner/test input を照合できない: {untracked.stderr.strip()}")
    if untracked.stdout:
        raise HarnessError(
            "runner/test 実行前に untracked file を検出: "
            f"{untracked.stdout.splitlines()}"
        )


def _head_blob_sha256(repo: Path, head: str, rel: str, label: str) -> str:
    result = _git(repo, "show", f"{head}:{rel}", text=False)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise HarnessError(f"{label} の固定 HEAD blob を取得できない: {stderr}")
    return hashlib.sha256(result.stdout).hexdigest()


def _resolve_command_path(value: str, repo: Path, label: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute() and candidate.parent == Path("."):
        located = shutil.which(value)
        if located is not None:
            candidate = Path(located)
        else:
            candidate = repo / candidate
    elif not candidate.is_absolute():
        candidate = repo / candidate
    try:
        return candidate.resolve(strict=True)
    except OSError as exc:
        raise HarnessError(f"{label} を解決できない: {exc}") from exc


def _tool_identity(repo: Path, head: str) -> dict[str, Any]:
    tool = Path(__file__).resolve(strict=True)
    identity: dict[str, Any] = {
        "path": str(tool),
        "sha256": _file_sha256(tool, "mutation harness tool"),
        "repo_path": None,
        "head_blob_sha256": None,
    }
    if _path_within(tool, repo):
        rel = tool.relative_to(repo).as_posix()
        head_sha = _head_blob_sha256(repo, head, rel, "mutation harness tool")
        if identity["sha256"] != head_sha:
            raise HarnessError("mutation harness tool が固定 HEAD blob と不一致")
        identity["repo_path"] = rel
        identity["head_blob_sha256"] = head_sha
    return identity


def _runner_identity(
    repo: Path, head: str, runner_mode: str, command: Sequence[str]
) -> dict[str, Any]:
    if len(command) < 3:
        raise HarnessError("test runner argv が短すぎる")
    executable = _resolve_command_path(command[0], repo, "runner Python")
    current_python = Path(sys.executable).resolve(strict=True)
    if executable != current_python:
        raise HarnessError("runner は harness と同じ Python executable に束縛する必要がある")

    entrypoint_kind: str
    entrypoint_path: Path
    repo_path: str | None = None
    head_blob_sha256: str | None = None
    if list(command[1:3]) == ["-m", "pytest"]:
        if runner_mode != "local":
            raise HarnessError("python -m pytest は --runner-mode local でのみ許可する")
        pytest_spec = importlib.util.find_spec("pytest")
        if pytest_spec is None or pytest_spec.origin is None:
            raise HarnessError("pytest module identity を解決できない")
        entrypoint_kind = "python-m-pytest"
        entrypoint_path = Path(pytest_spec.origin).resolve(strict=True)
        pytest_args = list(command[3:])
    else:
        entrypoint_path = _resolve_command_path(command[1], repo, "runner entrypoint")
        expected = (repo / "tools" / "run_tests.py").resolve(strict=False)
        if entrypoint_path != expected:
            raise HarnessError(
                "runner entrypoint は python -m pytest または固定 HEAD の tools/run_tests.py に限る"
            )
        entrypoint_kind = "izanagi-run-tests"
        pytest_args = list(command[2:])
        repo_path = "tools/run_tests.py"
        head_blob_sha256 = _head_blob_sha256(repo, head, repo_path, "runner entrypoint")
        if _file_sha256(entrypoint_path, "runner entrypoint") != head_blob_sha256:
            raise HarnessError("runner entrypoint が固定 HEAD blob と不一致")

    _assert_tracked_test_arguments(repo, head, pytest_args)

    dispatch_entrypoint_path: str | None = None
    dispatch_entrypoint_sha256: str | None = None
    dispatch_head_blob_sha256: str | None = None
    if runner_mode == "dispatch":
        dispatch_rel = "tools/pegasus/dispatch_compute.py"
        dispatch_path = (repo / dispatch_rel).resolve(strict=True)
        dispatch_head_blob_sha256 = _head_blob_sha256(
            repo, head, dispatch_rel, "dispatch collection entrypoint"
        )
        dispatch_entrypoint_sha256 = _file_sha256(
            dispatch_path, "dispatch collection entrypoint"
        )
        if dispatch_entrypoint_sha256 != dispatch_head_blob_sha256:
            raise HarnessError("dispatch collection entrypoint が固定 HEAD blob と不一致")
        dispatch_entrypoint_path = str(dispatch_path)

    tree = _git(repo, "rev-parse", f"{head}^{{tree}}")
    if tree.returncode != 0:
        raise HarnessError(f"固定 HEAD tree を取得できない: {tree.stderr.strip()}")
    return {
        "runner_mode": runner_mode,
        "command": list(command),
        "entrypoint_kind": entrypoint_kind,
        "executable_path": str(executable),
        "executable_sha256": _file_sha256(executable, "runner Python"),
        "entrypoint_path": str(entrypoint_path),
        "entrypoint_sha256": _file_sha256(entrypoint_path, "runner entrypoint"),
        "pytest_distribution_sha256": _pytest_distribution_sha256(),
        "dispatch_entrypoint_path": dispatch_entrypoint_path,
        "dispatch_entrypoint_sha256": dispatch_entrypoint_sha256,
        "dispatch_head_blob_sha256": dispatch_head_blob_sha256,
        "repo_path": repo_path,
        "head_blob_sha256": head_blob_sha256,
        "repo_tree": tree.stdout.strip(),
    }


def _pytest_distribution_sha256() -> str:
    try:
        distribution = metadata.distribution("pytest")
    except metadata.PackageNotFoundError as exc:
        raise HarnessError("pytest distribution identity を解決できない") from exc
    files = distribution.files
    if files is None:
        raise HarnessError("pytest distribution file manifest がない")
    digest = hashlib.sha256()
    included = 0
    for entry in sorted(files, key=str):
        if entry.suffix == ".pyc" or "__pycache__" in entry.parts:
            continue
        path = Path(distribution.locate_file(entry))
        try:
            if path.is_symlink() or not path.is_file():
                raise HarnessError(f"pytest distribution file が通常 file でない: {entry}")
            payload = path.read_bytes()
        except HarnessError:
            raise
        except OSError as exc:
            raise HarnessError(f"pytest distribution file を読めない: {entry}: {exc}") from exc
        digest.update(str(entry).encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
        included += 1
    if included == 0:
        raise HarnessError("pytest distribution identity に file がない")
    return digest.hexdigest()


def _assert_tracked_test_arguments(repo: Path, head: str, args: Sequence[str]) -> None:
    value_options = {
        "-k",
        "-m",
        "-n",
        "--numprocesses",
        "--dist",
        "--tb",
        "--maxfail",
        "--rootdir",
        "--confcutdir",
        "--basetemp",
        "-o",
        "-p",
    }
    index = 0
    while index < len(args):
        token = args[index]
        option = token.partition("=")[0]
        if option in value_options:
            index += 1 if "=" in token else 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        path_text = token.partition("::")[0]
        candidate = Path(path_text)
        if not candidate.is_absolute():
            candidate = repo / candidate
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise HarnessError(f"runner test target が実在しない: {token!r}: {exc}") from exc
        if not _path_within(resolved, repo):
            raise HarnessError(f"runner test target が checkout 外: {token!r}")
        rel = resolved.relative_to(repo).as_posix()
        tracked = _git(repo, "cat-file", "-e", f"{head}:{rel}")
        if tracked.returncode != 0:
            raise HarnessError(f"runner test target が固定 HEAD に存在しない: {token!r}")
        index += 1


def _assert_runtime_artifacts_outside_repo(
    repo: Path, *, spec_path: Path, out: Path, attempt_out: Path | None = None
) -> None:
    temp_root = Path(tempfile.gettempdir()).resolve()
    lock_path = _lock_path_for(repo).resolve()
    candidates = {
        "--spec": spec_path,
        "--out": out,
        "--out temporary directory": out.parent,
        "temporary root": temp_root,
        "lock": lock_path,
    }
    if attempt_out is not None:
        candidates["--attempt-out"] = attempt_out
        if attempt_out == out:
            raise HarnessError("--attempt-out と --out は異なる path でなければならない")
    inside = [label for label, path in candidates.items() if _path_within(path, repo)]
    if inside:
        raise HarnessError(
            "runtime artifact は試験対象 checkout 外でなければならない: "
            + ", ".join(sorted(inside))
        )


def _new_attempt_recorder(
    path: Path,
    *,
    resume: bool,
    wrapper_attempt_ordinal: int,
    head: str,
    spec: MutationSpec,
    spec_sha256: str,
    runner_sha256: str,
    tool_sha256: str,
    local_authorization: dict[str, Any] | None,
) -> AttemptRecorder:
    expected = {
        "schema": (
            LOCAL_ATTEMPT_SCHEMA
            if local_authorization is not None
            else ATTEMPT_SCHEMA
        ),
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "runner_sha256": runner_sha256,
        "tool_sha256": tool_sha256,
        "expected_initial_requests": len(spec.mutations) + 2,
    }
    if local_authorization is not None:
        expected["local_authorization"] = local_authorization
    if resume:
        try:
            if path.is_symlink() or not path.is_file():
                raise HarnessError(
                    "--resume + --attempt-out には既存の symlink でない通常 file が必要"
                )
            document = json.loads(path.read_text(encoding="utf-8"))
        except HarnessError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HarnessError(f"attempt sidecar を読めない: {exc}") from exc
        if not isinstance(document, dict):
            raise HarnessError("attempt sidecar root が object でない")
        _require_exact_keys(document, {*expected, "attempts"}, "attempt sidecar")
        for key, value in expected.items():
            if document[key] != value:
                raise HarnessError(f"attempt sidecar の {key} が現行 run と不一致")
        attempts = document["attempts"]
        if not isinstance(attempts, list):
            raise HarnessError("attempt sidecar attempts が list でない")
        for index, attempt in enumerate(attempts):
            if not isinstance(attempt, dict):
                raise HarnessError(f"attempt sidecar attempts[{index}] が object でない")
            _require_exact_keys(attempt, set(ATTEMPT_FIELDS), f"attempts[{index}]")
            if attempt["run_attempt_ordinal"] != index + 1:
                raise HarnessError("attempt sidecar ordinal が連続でない")
            if (
                isinstance(attempt["wrapper_attempt_ordinal"], bool)
                or not isinstance(attempt["wrapper_attempt_ordinal"], int)
                or attempt["wrapper_attempt_ordinal"] < 1
            ):
                raise HarnessError("attempt sidecar wrapper ordinal が不正")
            if attempt.get("state") != "finished":
                raise HarnessError(
                    f"attempt sidecar attempts[{index}] が finished でない; resume 不能"
                )
            if attempt["phase"] not in {"collection", "baseline", "mutation"}:
                raise HarnessError("attempt sidecar phase が未知")
            if (attempt["phase"] == "mutation") is not isinstance(
                attempt["mutation_id"], str
            ):
                raise HarnessError("attempt sidecar phase/mutation_id が不整合")
            if not isinstance(attempt["timed_out"], bool):
                raise HarnessError("attempt sidecar timed_out が bool でない")
            request = attempt["request"]
            if request is not None:
                if not isinstance(request, dict):
                    raise HarnessError("attempt sidecar request が object/null でない")
                _require_exact_keys(
                    request, set(ATTEMPT_REQUEST_FIELDS), f"attempts[{index}].request"
                )
    else:
        if path.exists() or path.is_symlink():
            raise HarnessError("fresh --attempt-out が既に存在する")
        document = {**expected, "attempts": []}
    return AttemptRecorder(
        path=path,
        wrapper_attempt_ordinal=wrapper_attempt_ordinal,
        document=document,
    )


def _assert_head(repo: Path, expected_head: str) -> None:
    current = _repo_head(repo)
    if current != expected_head:
        raise HarnessError(f"run 中に HEAD が変化: expected={expected_head}, actual={current}")


def _read_head_sources(
    repo: Path, head: str, spec: MutationSpec
) -> dict[str, str]:
    files = sorted(
        {replacement.file for mutation in spec.mutations for replacement in mutation.replacements}
    )
    sources: dict[str, str] = {}
    for rel in files:
        result = _git(repo, "show", f"{head}:{rel}", text=False)
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise HarnessError(f"対象の固定 HEAD blob を取得できない: {rel}: {stderr}")
        try:
            source = result.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HarnessError(f"対象が UTF-8 text でない: {rel}: {exc}") from exc
        target = repo / rel
        try:
            if target.is_symlink() or not target.is_file():
                raise HarnessError(f"対象が symlink でない通常ファイルでない: {rel}")
            current = target.read_text(encoding="utf-8")
        except HarnessError:
            raise
        except (OSError, UnicodeDecodeError) as exc:
            raise HarnessError(f"対象 working tree を読めない: {rel}: {exc}") from exc
        if current != source:
            raise HarnessError(
                f"対象が固定 HEAD blob と不一致: {rel}; 残留変異または未統合変更のため停止"
            )
        sources[rel] = source
    _assert_head(repo, head)
    return sources


def _mutated_sources(
    mutation: Mutation, originals: dict[str, str]
) -> tuple[dict[str, str], str, dict[str, int]]:
    current = {rel: originals[rel] for rel in {item.file for item in mutation.replacements}}
    counts: dict[str, int] = {}
    for index, replacement in enumerate(mutation.replacements):
        source = current[replacement.file]
        count = source.count(replacement.old)
        counts[str(index)] = count
        if count != 1:
            raise HarnessError(
                f"{mutation.id} replacement[{index}] {replacement.file}: "
                f"累積 source の anchor count={count}; exactly one required"
            )
        updated = source.replace(replacement.old, replacement.new, 1)
        if updated == source:
            raise HarnessError(f"{mutation.id} replacement[{index}]: 注入が実在しない")
        current[replacement.file] = updated

    diff_parts: list[str] = []
    for rel in sorted(current):
        diff_parts.extend(
            difflib.unified_diff(
                originals[rel].splitlines(keepends=True),
                current[rel].splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
        )
    diff = "".join(diff_parts)
    if not diff:
        raise HarnessError(f"{mutation.id}: 累積注入 diff が空")
    return current, diff, counts


def _validate_registrations(
    repo: Path, spec: MutationSpec, originals: dict[str, str]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for mutation in spec.mutations:
        normalized_nodes = [_normalize_node(node, repo) for node in mutation.expected_nodes]
        _reject_flaky_hold_expected_nodes(normalized_nodes, repo)
        _mutated, diff, counts = _mutated_sources(mutation, originals)
        if len({_match_key(node, repo) for node in normalized_nodes}) != len(normalized_nodes):
            raise HarnessError(f"{mutation.id}: expected_nodes が正規化後に重複")
        result[mutation.id] = {
            "anchor_counts": counts,
            "injection_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
            "expected_nodes": normalized_nodes,
            "expected_status": mutation.expected_status,
            "replacements": [dataclasses.asdict(item) for item in mutation.replacements],
        }
    return result


def _verify_originals(repo: Path, originals: dict[str, str]) -> None:
    errors: list[str] = []
    for rel, original in originals.items():
        target = repo / rel
        try:
            if target.is_symlink() or not target.is_file():
                errors.append(f"{rel}: symlink でない通常ファイルでない")
            elif target.read_text(encoding="utf-8") != original:
                errors.append(f"{rel}: read_text() が固定 HEAD blob と不一致")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: 復元内容を読めない: {exc}")
    if errors:
        raise HarnessError("復元検査に失敗: " + "; ".join(errors))


def _purge_pycache(repo: Path, rels: Sequence[str]) -> None:
    for parent in {str((repo / rel).parent) for rel in rels}:
        cache = Path(parent) / "__pycache__"
        if not cache.exists():
            continue
        try:
            if cache.is_symlink() or not cache.is_dir():
                raise HarnessError(f"cache path が通常 directory でない: {cache}")
            for entry in cache.iterdir():
                if entry.is_symlink() or not entry.is_file():
                    raise HarnessError(f"cache entry が通常 file でない: {entry}")
                entry.unlink()
            cache.rmdir()
        except HarnessError:
            raise
        except OSError as exc:
            raise HarnessError(f"stale bytecode cache を除去できない: {cache}: {exc}") from exc


@contextlib.contextmanager
def _defer_cleanup_signals() -> Any:
    guarded = (signal.SIGINT, signal.SIGTERM)
    if not hasattr(signal, "pthread_sigmask"):
        raise HarnessError("signal-safe restoration には pthread_sigmask が必要")
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, guarded)
    old_handlers: dict[int, Any] = {}
    pending_signum: int | None = None

    def defer_handler(signum: int, _frame: Any) -> None:
        nonlocal pending_signum
        if pending_signum is None:
            pending_signum = signum

    try:
        for signum in guarded:
            old_handlers[signum] = signal.signal(signum, defer_handler)
    except BaseException:
        for signum, old_handler in old_handlers.items():
            signal.signal(signum, old_handler)
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        raise
    try:
        yield
    finally:
        try:
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        finally:
            for signum, old_handler in old_handlers.items():
                signal.signal(signum, old_handler)
        if pending_signum is not None:
            raise SignalAbort(pending_signum)


def _restore_targets(repo: Path, originals: dict[str, str]) -> None:
    with _defer_cleanup_signals():
        errors: list[str] = []
        for rel, original in originals.items():
            target = repo / rel
            try:
                if target.is_symlink() or (target.exists() and not target.is_file()):
                    errors.append(f"{rel}: 復元先が symlink でない file path でない")
                    continue
                target.write_text(original, encoding="utf-8")
            except OSError as exc:
                errors.append(f"{rel}: 固定 HEAD 内容を書き戻せない: {exc}")
        try:
            _purge_pycache(repo, tuple(originals))
        except HarnessError as exc:
            errors.append(str(exc))
        try:
            _verify_originals(repo, originals)
        except HarnessError as exc:
            errors.append(str(exc))
        if errors:
            raise HarnessError("復元に失敗: " + "; ".join(errors))


def _strip_relay_prefix(line: str) -> str:
    line = ANSI_RE.sub("", line).lstrip()
    while line.startswith("|"):
        line = line[1:].lstrip()
    return line


def _normalize_node(node: str, repo: Path) -> str:
    value = node.strip().replace("\\", "/")
    repo_prefix = repo.as_posix().rstrip("/") + "/"
    if value.startswith(repo_prefix):
        value = value[len(repo_prefix):]
    while value.startswith("./"):
        value = value[2:]
    path_part, separator, test_part = value.partition("::")
    if not separator or not path_part or not test_part:
        raise HarnessError(f"pytest node が <path>::<name> 形式でない: {node!r}")
    path_part = _safe_relpath(path_part, "pytest node path")
    return f"{path_part}::{test_part.strip()}"


def _match_key(node: str, repo: Path) -> str:
    normalized = _normalize_node(node, repo)
    path_part, separator, test_part = normalized.partition("::")
    suffix_start = test_part.rfind("@")
    if suffix_start > test_part.rfind("]"):
        test_part = test_part[:suffix_start]
    return f"{path_part}{separator}{test_part}"


def _failed_nodes(output: str, repo: Path) -> list[str]:
    found: list[str] = []
    for raw_line in output.splitlines():
        line = _strip_relay_prefix(raw_line)
        if not line.startswith("FAILED "):
            continue
        remainder = line[len("FAILED "):]
        node, separator, _detail = remainder.partition(" - ")
        if not separator:
            node = remainder
        if not node.strip():
            continue
        normalized = _normalize_node(node, repo)
        if normalized not in found:
            found.append(normalized)
    return found


def _collected_nodes(output: str, repo: Path) -> list[str]:
    found: list[str] = []
    for raw_line in output.splitlines():
        line = _strip_relay_prefix(raw_line).strip()
        if "::" not in line or line.startswith("FAILED "):
            continue
        try:
            normalized = _normalize_node(line, repo)
        except HarnessError:
            continue
        if normalized not in found:
            found.append(normalized)
    return found


def _flaky_hold_node_ids_for_policy(repo: Path) -> frozenset[str]:
    """Load the current checkout's exact flaky-node set for the policy guard."""
    registry_path = repo / "orchestrator" / "tests" / "flaky_test_holds.py"
    if not registry_path.is_file():
        # A different checkout may legitimately predate the quarantine
        # registry.  Its mutations cannot intersect this checkout's holds.
        return frozenset()
    module_name = (
        "_izanagi_flaky_test_holds_"
        + hashlib.sha256(str(registry_path).encode("utf-8")).hexdigest()[:16]
    )
    module = sys.modules.get(module_name)
    if module is None:
        spec = importlib.util.spec_from_file_location(module_name, registry_path)
        if spec is None or spec.loader is None:
            raise HarnessError("flaky hold registry cannot be loaded")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(module_name, None)
            raise
    node_ids = getattr(module, "FLAKY_TEST_HOLD_NODE_IDS", None)
    if not isinstance(node_ids, frozenset) or any(
        not isinstance(node_id, str) for node_id in node_ids
    ):
        raise HarnessError("flaky hold registry node set is invalid")
    return node_ids


def _reject_flaky_hold_expected_nodes(
    expected: Sequence[str],
    repo: Path,
) -> None:
    expected_keys = {_match_key(node, repo) for node in expected}
    held_keys = {
        _match_key(node, repo) for node in _flaky_hold_node_ids_for_policy(repo)
    }
    held = expected_keys.intersection(held_keys)
    if held:
        raise HarnessError(
            "policy mismatch: mutation expected failure node is isolated: "
            f"{sorted(held)!r}"
        )


def _artifact(result: dict[str, Any], output: str, runner_mode: str) -> dict[str, Any]:
    return {
        "runner_mode": runner_mode,
        "receipt_path": result.get("receipt_path"),
        "job_stdout_path": result.get("job_stdout_path"),
        "stdout": output,
        "stdout_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }


def _validate_artifact(
    artifact: Any,
    *,
    repo: Path,
    runner_mode: str,
    label: str,
    allow_incomplete_dispatch: bool = False,
) -> str:
    if not isinstance(artifact, dict):
        raise HarnessError(f"{label}.artifact が object でない")
    _require_exact_keys(artifact, set(ARTIFACT_FIELDS), f"{label}.artifact")
    if artifact["runner_mode"] != runner_mode:
        raise HarnessError(f"{label}.artifact runner_mode が不一致")
    stdout = artifact["stdout"]
    if not isinstance(stdout, str):
        raise HarnessError(f"{label}.artifact stdout が文字列でない")
    if artifact["stdout_sha256"] != hashlib.sha256(stdout.encode("utf-8")).hexdigest():
        raise HarnessError(f"{label}.artifact stdout hash が不一致")
    receipt_value = artifact["receipt_path"]
    stdout_value = artifact["job_stdout_path"]
    if runner_mode == "local":
        if receipt_value is not None or stdout_value is not None:
            raise HarnessError(f"{label}.artifact local path field は null 必須")
        return stdout
    if allow_incomplete_dispatch and receipt_value is None and stdout_value is None:
        return stdout
    if not isinstance(receipt_value, str) or not isinstance(stdout_value, str):
        raise HarnessError(f"{label}.artifact dispatch path field が文字列でない")
    dispatch_root = (repo / "output" / "pegasus-dispatch").resolve()
    try:
        receipt = Path(receipt_value).resolve(strict=True)
        stdout_path = Path(stdout_value).resolve(strict=True)
    except OSError as exc:
        raise HarnessError(f"{label}.artifact dispatch path を再検証できない: {exc}") from exc
    if (
        receipt.is_symlink()
        or stdout_path.is_symlink()
        or not receipt.is_file()
        or not stdout_path.is_file()
        or not _path_within(receipt, dispatch_root)
        or not _path_within(stdout_path, dispatch_root)
    ):
        raise HarnessError(f"{label}.artifact dispatch path 束縛が不正")
    try:
        current = stdout_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise HarnessError(f"{label}.artifact stdout を再読できない: {exc}") from exc
    if current != stdout:
        raise HarnessError(f"{label}.artifact stdout bytes が保存済み証拠と不一致")
    return stdout


def _dispatch_timeout_overrides(
    *, environ: Mapping[str, str]
) -> dict[str, float]:
    """D612 の opt-in dispatch timeout 上書きを純粋に解釈する。"""

    # tools/check_ai_provenance.py の同名実装と同値
    # (test_t2337_dispatch_timeout_overrides.py の meta-test で照合する)。
    overrides: dict[str, float] = {}
    for env_name, keyword in (
        (_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV, "queue_wait_timeout_s"),
        (_DISPATCH_OVERALL_GRACE_OVERRIDE_ENV, "overall_grace_s"),
    ):
        raw_value = environ.get(env_name)
        if not raw_value:
            continue
        value = float(raw_value)
        if (
            not math.isfinite(value)
            or value < 0
            or math.copysign(1.0, value) < 0
        ):
            raise ValueError(f"{env_name} は有限な非負数でなければなりません")
        overrides[keyword] = value
    return overrides


def _effective_timeout(
    spec: MutationSpec,
    runner_mode: str,
    *,
    collection: bool = False,
    hang_risk: bool = False,
) -> float:
    """D2148: dispatch 全区間の運用予算。厳密な実行上限ではない。"""
    if runner_mode == "local":
        return spec.hang_timeout_seconds if hang_risk else spec.timeout_seconds
    from tools.pegasus import dispatch_compute

    try:
        overrides = _dispatch_timeout_overrides(environ=os.environ)
    except (TypeError, ValueError) as exc:
        # 新しい拒否 gate にしない。collection / dispatcher の既存拒否へ渡す。
        print(f"[mutation timeout] Q/G override 不正: {exc}; 予算は既定値", file=sys.stderr)
        overrides = {}
    walltime = dispatch_compute._walltime_seconds(dispatch_compute.DEFAULT_WALLTIME)
    raw_walltime = None if collection else os.environ.get("IZANAGI_DISPATCH_WALLTIME_OVERRIDE")
    if not collection and raw_walltime:
        try:
            walltime = dispatch_compute._walltime_seconds(raw_walltime)
        except ValueError as exc:
            print(f"[mutation timeout] W override 不正: {exc}; 予算は既定値", file=sys.stderr)
    # 前段実測 max 15.9s に10倍以上の余裕。harness 起動・観測・終端も含む暫定値。
    preparation = 180.0
    queue = overrides.get("queue_wait_timeout_s", dispatch_compute.DEFAULT_QUEUE_WAIT_TIMEOUT_S)
    grace = overrides.get("overall_grace_s", dispatch_compute.DEFAULT_OVERALL_GRACE_S)
    accounting = dispatch_compute.DEFAULT_ACCOUNTING_GRACE_S
    cleanup = dispatch_compute.DEFAULT_CLEANUP_BUDGET_S
    budget = preparation + queue + walltime + grace + accounting + cleanup
    effective = max(spec.timeout_seconds, budget)
    print(
        f"[mutation timeout] {'collection' if collection else 'execution'}: "
        f"spec={spec.timeout_seconds}, P={preparation}, Q={queue}, W={walltime}, "
        f"G={grace}, A={accounting}, C={cleanup}, budget={budget}, effective={effective}; "
        "全区間を覆うため max(spec, 運用予算) を使用（厳密上限ではない）。"
        "dispatch hang は内側 walltime に委ね、短い hang timeout は外側に使わない",
        file=sys.stderr,
        flush=True,
    )
    return effective


def _collection_command(
    repo: Path,
    command: Sequence[str],
    runner_mode: str,
    *,
    outer_timeout_s: float | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    forbidden = {"--collect-only", "--co", "--fixtures", "--fixtures-per-test"}
    if any(token in forbidden for token in command):
        raise HarnessError("runner command に no-execution/collection option を事前指定してはならない")
    # pytest --collect-only -q は canonical nodeid を 1 行ずつ出すが、quiet flag が
    # 重なると -qq 相当になり nodeid 行自体が消える。選択・設定引数は保ったまま、
    # collection の verbosity だけを exactly one に固定する。
    def collection_args(args: Sequence[str]) -> list[str]:
        return [
            token
            for token in args
            if token not in {"--quiet", "--verbose"}
            and re.fullmatch(r"-(?:q+|v+)", token) is None
        ]

    if runner_mode == "local":
        return [*collection_args(command), "--collect-only", "-q"]
    try:
        timeout_overrides = _dispatch_timeout_overrides(
            environ=os.environ if environ is None else environ
        )
    except (TypeError, ValueError) as exc:
        raise HarnessError(f"D612 dispatch timeout 上書きが不正: {exc}") from exc
    if timeout_overrides and outer_timeout_s is not None:
        from tools.pegasus import dispatch_compute

        queue_wait_timeout_s = timeout_overrides.get(
            "queue_wait_timeout_s",
            dispatch_compute.DEFAULT_QUEUE_WAIT_TIMEOUT_S,
        )
        overall_grace_s = timeout_overrides.get(
            "overall_grace_s",
            dispatch_compute.DEFAULT_OVERALL_GRACE_S,
        )
        if outer_timeout_s < queue_wait_timeout_s + overall_grace_s:
            raise HarnessError(
                "mutation collection の外側 timeout が明示された dispatch "
                "待機契約より短い: "
                f"timeout_seconds={outer_timeout_s}, "
                f"queue_wait_timeout_s={queue_wait_timeout_s}, "
                f"overall_grace_s={overall_grace_s}"
            )
    timeout_args: list[str] = []
    if "queue_wait_timeout_s" in timeout_overrides:
        timeout_args.extend(
            ["--queue-wait-timeout", str(timeout_overrides["queue_wait_timeout_s"])]
        )
    if "overall_grace_s" in timeout_overrides:
        timeout_args.extend(
            ["--overall-grace", str(timeout_overrides["overall_grace_s"])]
        )
    pytest_args = collection_args(command[2:])
    return [
        command[0],
        str(repo / "tools" / "pegasus" / "dispatch_compute.py"),
        "--task",
        "tests",
        *timeout_args,
        "--",
        *pytest_args,
        "-n",
        "0",
        "--collect-only",
        "-q",
    ]


def _collect_expected_nodes(
    repo: Path,
    spec: MutationSpec,
    command: Sequence[str],
    runner_mode: str,
    *,
    head: str,
    spec_sha256: str,
    runner_sha256: str,
    tool_sha256: str,
    attempt_recorder: AttemptRecorder | None = None,
) -> dict[str, Any]:
    _assert_only_expected_dirt(repo, head, ())
    stop = _dispatch_orphan_stop(
        repo,
        runner_mode=runner_mode,
        phase="collection",
        mutation_id=None,
        source_state="unchanged",
        dirty_paths=(),
    )
    if stop is not None:
        raise stop
    result = _run_tests(
        repo,
        _collection_command(
            repo,
            command,
            runner_mode,
            outer_timeout_s=spec.timeout_seconds,
        ),
        timeout_s=_effective_timeout(spec, runner_mode, collection=True),
        runner_mode=runner_mode,
        attempt_recorder=attempt_recorder,
        attempt_phase="collection" if attempt_recorder is not None else None,
    )
    stop = _dispatch_orphan_stop(
        repo,
        runner_mode=runner_mode,
        phase="collection",
        mutation_id=None,
        source_state="unchanged",
        dirty_paths=(),
        result=result,
    )
    if stop is not None:
        raise stop
    output = result.get("job_stdout", "")
    collected = _collected_nodes(output, repo)
    if (
        result["timed_out"]
        or result.get("artifact_error") is not None
        or result["rc"] != 0
        or not collected
    ):
        raise HarnessError(
            "pytest collection が正常完了せず、期待 node の実在を証明できない: "
            f"rc={result['rc']}, collected={len(collected)}, "
            f"artifact_error={result.get('artifact_error')!r}"
        )
    collected_set = {_match_key(node, repo) for node in collected}
    missing = sorted(
        {
            _match_key(node, repo)
            for mutation in spec.mutations
            for node in mutation.expected_nodes
        }
        - collected_set
    )
    if missing:
        raise HarnessError(f"期待 node が pytest collection に実在しない: {missing}")
    return {
        "status": "PASSED",
        "rc": 0,
        "collected_nodes": collected,
        "duration_s": result["duration_s"],
        "artifact": _artifact(result, output, runner_mode),
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "runner_sha256": runner_sha256,
        "tool_sha256": tool_sha256,
    }


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _read_dispatch_stdout(console_output: str, repo: Path, rc: int) -> dict[str, Any]:
    matches: list[tuple[str, int]] = []
    for raw_line in console_output.splitlines():
        line = ANSI_RE.sub("", raw_line).strip()
        match = RECEIPT_LINE_RE.fullmatch(line)
        if match is not None:
            matches.append((match.group(1), int(match.group(2))))
    if len(matches) != 1:
        return {"artifact_error": f"receipt 表示行が exactly one でない: {len(matches)}"}
    receipt_text, reported_rc = matches[0]
    if reported_rc != rc:
        return {"artifact_error": f"表示 child rc={reported_rc} と subprocess rc={rc} が不一致"}

    dispatch_root = (repo / "output" / "pegasus-dispatch").resolve()
    raw_receipt = Path(receipt_text)
    try:
        if raw_receipt.is_symlink():
            raise OSError("receipt が symlink")
        receipt_path = raw_receipt.resolve(strict=True)
    except OSError as exc:
        return {"artifact_error": f"receipt を開けない: {exc}"}
    if not receipt_path.is_file() or not _path_within(receipt_path, dispatch_root):
        return {"artifact_error": "receipt が dispatch root 配下の通常 file でない"}
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"artifact_error": f"receipt JSON を読めない: {exc}"}
    if not isinstance(receipt, dict):
        return {"artifact_error": "receipt JSON root が object でない"}

    qdel = receipt.get("qdel")
    qdel = qdel if isinstance(qdel, dict) else {}
    orphan_fields = {
        "job_may_remain": qdel.get("job_may_remain"),
        "hold_error": qdel.get("hold_error"),
    }

    def artifact_error(message: str) -> dict[str, Any]:
        return {"artifact_error": message, **orphan_fields}

    submission_value = receipt.get("submission_dir")
    if not isinstance(submission_value, str):
        return artifact_error("receipt.submission_dir が文字列でない")
    try:
        submission_dir = Path(submission_value).resolve(strict=True)
    except OSError as exc:
        return artifact_error(f"submission_dir を開けない: {exc}")
    if (
        not submission_dir.is_dir()
        or not _path_within(submission_dir, dispatch_root)
        or (receipt_path.name == "receipt.json" and receipt_path.parent != submission_dir)
    ):
        return artifact_error("receipt と submission_dir の束縛が不正")
    outcome = receipt.get("outcome")
    receipt_rc = outcome.get("rc") if isinstance(outcome, dict) else None
    if receipt_rc != rc:
        return artifact_error(f"receipt outcome rc={receipt_rc!r} と rc={rc} が不一致")
    request = receipt.get("request")
    request_id = receipt.get("request_id")
    if not isinstance(request, dict) or not isinstance(request_id, str):
        return artifact_error("receipt request/request_id が不正")
    job_name = request.get("job_name")
    if not isinstance(job_name, str) or re.fullmatch(r"izdw-[A-Za-z0-9._-]+", job_name) is None:
        return artifact_error("receipt request.job_name が不正")
    numeric_request_id = request_id.rstrip(".").split(".", 1)[0]
    expected_names = {
        f"{job_name}.o{numeric_request_id}",
        f"{job_name}.o{request_id.rstrip('.')}",
    }
    logs = receipt.get("scheduler_logs")
    stdout_record = logs.get("stdout") if isinstance(logs, dict) else None
    stdout_value = stdout_record.get("path") if isinstance(stdout_record, dict) else None
    if not isinstance(stdout_value, str):
        return artifact_error("receipt scheduler_logs.stdout.path がない")
    raw_stdout = Path(stdout_value)
    try:
        if raw_stdout.is_symlink():
            raise OSError("job stdout が symlink")
        stdout_path = raw_stdout.resolve(strict=True)
    except OSError as exc:
        return artifact_error(f"job stdout を開けない: {exc}")
    if (
        not stdout_path.is_file()
        or stdout_path.parent != submission_dir
        or JOB_STDOUT_RE.fullmatch(stdout_path.name) is None
        or stdout_path.name not in expected_names
    ):
        return artifact_error(f"job stdout の path/name 束縛が不正: {stdout_path}")
    try:
        job_stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return artifact_error(f"job stdout を読めない: {exc}")
    return {
        "artifact_error": None,
        **orphan_fields,
        "receipt_path": str(receipt_path),
        "job_stdout_path": str(stdout_path),
        "job_stdout": job_stdout,
        "request": {
            "request_id": request_id,
            "submission_dir": str(submission_dir),
            "receipt_path": str(receipt_path),
            "job_stdout_path": str(stdout_path),
            "outcome_rc": receipt_rc,
        },
    }


def _dispatch_submission_inventory(repo: Path) -> set[Path]:
    root = (repo / "output" / "pegasus-dispatch").resolve()
    if not root.exists():
        return set()
    if root.is_symlink() or not root.is_dir():
        raise HarnessError("dispatch evidence root が通常 directory でない")
    try:
        return {
            entry.resolve(strict=True)
            for entry in root.iterdir()
            if entry.is_dir() and not entry.is_symlink()
        }
    except OSError as exc:
        raise HarnessError(f"dispatch submission inventory を取得できない: {exc}") from exc


def _canonical_dispatch_arg(repo: Path, value: str) -> str:
    option, separator, option_value = value.partition("=")
    if separator and option_value:
        canonical = _canonical_dispatch_arg(repo, option_value)
        return f"{option}={canonical}"
    path_value, node_separator, node = value.partition("::")
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = repo / candidate
    try:
        if not candidate.exists():
            return value
        path_value = str(candidate.resolve(strict=True))
    except OSError:
        return value
    return path_value + (node_separator + node if node_separator else "")


def _runner_dispatch_args(repo: Path, command: Sequence[str]) -> list[str] | None:
    if list(command[1:3]) == ["-m", "pytest"]:
        values = list(command[3:])
    elif len(command) >= 2:
        try:
            entrypoint = Path(command[1])
            if not entrypoint.is_absolute():
                entrypoint = repo / entrypoint
            if entrypoint.resolve(strict=False) != (
                repo / "tools" / "run_tests.py"
            ).resolve(strict=False):
                return None
        except OSError:
            return None
        values = list(command[2:])
    else:
        return None
    return [
        _canonical_dispatch_arg(repo, value)
        for value in values
        if value != "--force-dispatch"
    ]


def _classify_local_dispatch_submissions(
    repo: Path,
    submissions: set[Path],
    command: Sequence[str],
    dispatch_id: str,
) -> dict[str, Any]:
    if not submissions:
        return {
            "state": "none",
            "matched_submission_dirs": [],
            "unrelated_submission_dirs": [],
            "corroboration": [],
            "errors": [],
        }
    expected_args = _runner_dispatch_args(repo, command)
    matched: list[str] = []
    unrelated: list[str] = []
    corroboration: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for submission in sorted(submissions):
        request_path = submission / "request.json"
        try:
            if request_path.is_symlink() or not request_path.is_file():
                raise HarnessError("request.json が通常 file でない")
            request = json.loads(request_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, HarnessError) as exc:
            errors.append(
                {
                    "submission_dir": str(submission),
                    "code": "request-unreadable",
                    "error_type": type(exc).__name__,
                }
            )
            continue
        if not isinstance(request, dict):
            errors.append(
                {
                    "submission_dir": str(submission),
                    "code": "request-not-object",
                    "error_type": type(request).__name__,
                }
            )
            continue
        environment = request.get("environment")
        request_args = request.get("args")
        repo_root = request.get("repo_root")
        if (
            request.get("schema_version")
            not in {"pegasus-dispatch-request/v1", "pegasus-dispatch-request/v2"}
            or not isinstance(environment, dict)
            or not isinstance(repo_root, str)
            or not isinstance(request.get("task"), str)
            or not isinstance(request_args, list)
            or not all(isinstance(value, str) for value in request_args)
        ):
            errors.append(
                {
                    "submission_dir": str(submission),
                    "code": "request-invalid",
                    "error_type": "ValidationError",
                }
            )
            continue
        try:
            bound_repo = (
                Path(repo_root).resolve(strict=False) == repo.resolve(strict=True)
            )
        except (OSError, ValueError):
            bound_repo = False
        bound_args = expected_args is not None and (
            [
                _canonical_dispatch_arg(repo, value)
                for value in request_args
            ]
            == expected_args
        )
        token_matches = environment.get("PYTHONDONTWRITEBYTECODE") == dispatch_id
        corroboration.append(
            {
                "submission_dir": str(submission),
                "nonce_matches": token_matches,
                "repo_matches": bound_repo,
                "task_matches": request.get("task") == "tests",
                "args_match": bound_args,
            }
        )
        if token_matches:
            matched.append(str(submission))
        else:
            unrelated.append(str(submission))
    if matched:
        state = "matched"
    elif errors:
        state = "indeterminate"
    else:
        state = "unrelated"
    return {
        "state": state,
        "matched_submission_dirs": matched,
        "unrelated_submission_dirs": unrelated,
        "corroboration": corroboration,
        "errors": errors,
    }


def _recover_dispatch_request(
    repo: Path, before: set[Path]
) -> dict[str, Any] | None:
    """final receipt 行が無い TIMEOUT でも新規 request identity を回収する。"""

    root = (repo / "output" / "pegasus-dispatch").resolve()
    after = _dispatch_submission_inventory(repo)
    created = sorted(after - before)
    if len(created) != 1:
        return None
    submission = created[0]
    candidates = [submission / "receipt.json"]
    try:
        candidates.extend(
            path for path in root.glob("receipt-fallback-*.json")
            if path.is_file() and not path.is_symlink()
        )
    except OSError:
        return None
    for candidate in candidates:
        try:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            receipt = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(receipt, dict) or receipt.get("submission_dir") != str(submission):
            continue
        request_id = receipt.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            continue
        outcome = receipt.get("outcome")
        outcome_rc = outcome.get("rc") if isinstance(outcome, dict) else None
        logs = receipt.get("scheduler_logs")
        stdout_record = logs.get("stdout") if isinstance(logs, dict) else None
        stdout_path = stdout_record.get("path") if isinstance(stdout_record, dict) else None
        return {
            "request_id": request_id,
            "submission_dir": str(submission),
            "receipt_path": str(candidate.resolve()),
            "job_stdout_path": stdout_path if isinstance(stdout_path, str) else None,
            "outcome_rc": outcome_rc if isinstance(outcome_rc, int) else None,
        }
    return None


def _stop_process(process: subprocess.Popen[str]) -> None:
    with _defer_cleanup_signals():
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass


def _run_tests(
    repo: Path,
    command: Sequence[str],
    *,
    timeout_s: float,
    runner_mode: str,
    attempt_recorder: AttemptRecorder | None = None,
    attempt_phase: str | None = None,
    mutation_id: str | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    runner_env = os.environ.copy()
    for key in (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONPYCACHEPREFIX",
    ):
        runner_env.pop(key, None)
    runner_env["PYTHONDONTWRITEBYTECODE"] = "1"
    dispatch_id: str | None = None
    if runner_mode == "local":
        dispatch_id = secrets.token_hex(16)
        runner_env["PYTHONDONTWRITEBYTECODE"] = dispatch_id
    attempt_ordinal: int | None = None
    if attempt_recorder is not None:
        if attempt_phase not in {"collection", "baseline", "mutation"}:
            raise HarnessError("attempt recorder には phase が必要")
        if (attempt_phase == "mutation") is not (mutation_id is not None):
            raise HarnessError("attempt phase と mutation_id の対応が不正")
        attempt_ordinal = attempt_recorder.started(
            phase=attempt_phase, mutation_id=mutation_id
        )
    dispatch_before: set[Path] | None
    dispatch_before_error: dict[str, str] | None = None
    if runner_mode == "local":
        try:
            dispatch_before = _dispatch_submission_inventory(repo)
        except Exception as exc:
            dispatch_before = None
            dispatch_before_error = {
                "code": "before-inventory-failed",
                "error_type": type(exc).__name__,
            }
    else:
        dispatch_before = _dispatch_submission_inventory(repo)
    try:
        process = subprocess.Popen(
            list(command),
            cwd=repo,
            env=runner_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        result = {
            "rc": None,
            "timed_out": False,
            "output": f"{type(exc).__name__}: {exc}",
            "artifact_error": f"test runner を起動できない: {exc}",
            "duration_s": round(time.monotonic() - started, 3),
        }
        if attempt_recorder is not None and attempt_ordinal is not None:
            attempt_recorder.finished(attempt_ordinal, result)
        return result
    try:
        try:
            output, _stderr = process.communicate(timeout=timeout_s)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            _stop_process(process)
            output, _stderr = process.communicate()
        rc = None if timed_out else process.returncode
        result: dict[str, Any] = {
            "rc": rc,
            "timed_out": timed_out,
            "output": output or "",
            "duration_s": round(time.monotonic() - started, 3),
        }
        if timed_out:
            result["artifact_error"] = None
            result["job_stdout"] = output or ""
            if runner_mode == "dispatch":
                assert dispatch_before is not None
                dispatch_after = _dispatch_submission_inventory(repo)
                result["new_dispatch_submission"] = bool(
                    dispatch_after - dispatch_before
                )
                result["request"] = _recover_dispatch_request(repo, dispatch_before)
            else:
                assert dispatch_id is not None
                if dispatch_before_error is not None:
                    evidence = {
                        "state": "indeterminate",
                        "matched_submission_dirs": [],
                        "unrelated_submission_dirs": [],
                        "corroboration": [],
                        "errors": [dispatch_before_error],
                    }
                else:
                    assert dispatch_before is not None
                    try:
                        dispatch_after = _dispatch_submission_inventory(repo)
                    except Exception as exc:
                        evidence = {
                            "state": "indeterminate",
                            "matched_submission_dirs": [],
                            "unrelated_submission_dirs": [],
                            "corroboration": [],
                            "errors": [
                                {
                                    "code": "after-inventory-failed",
                                    "error_type": type(exc).__name__,
                                }
                            ],
                        }
                    else:
                        try:
                            evidence = _classify_local_dispatch_submissions(
                                repo,
                                dispatch_after - dispatch_before,
                                command,
                                dispatch_id,
                            )
                        except Exception as exc:
                            evidence = {
                                "state": "indeterminate",
                                "matched_submission_dirs": [],
                                "unrelated_submission_dirs": [],
                                "corroboration": [],
                                "errors": [
                                    {
                                        "code": "request-inspection-failed",
                                        "error_type": type(exc).__name__,
                                    }
                                ],
                            }
                result["dispatch_submission"] = evidence
                result["new_dispatch_submission"] = (
                    True
                    if evidence["state"] == "matched"
                    else None if evidence["state"] == "indeterminate" else False
                )
                result["request"] = None
        elif runner_mode == "dispatch":
            result.update(_read_dispatch_stdout(output or "", repo, int(rc)))
        else:
            result.update({"artifact_error": None, "job_stdout": output or ""})
        if attempt_recorder is not None and attempt_ordinal is not None:
            attempt_recorder.finished(attempt_ordinal, result)
        return result
    finally:
        _stop_process(process)


def _observed_status(
    *, result: dict[str, Any], failed: Sequence[str], expected: Sequence[str], repo: Path
) -> str:
    if result["timed_out"]:
        return "TIMEOUT"
    rc = result["rc"]
    if rc is None or result.get("artifact_error") is not None:
        return "PARSE_ERROR"
    if rc not in PYTEST_NORMAL_RCS:
        return "PARSE_ERROR"
    if rc != 0 and not failed:
        return "PARSE_ERROR"
    if rc == 0:
        return "SURVIVED" if not failed else "MISMATCH"
    expected_keys = {_match_key(node, repo) for node in expected}
    failed_keys = {_match_key(node, repo) for node in failed}
    return "KILLED" if failed_keys == expected_keys else "MISMATCH"


def _baseline(
    repo: Path,
    spec: MutationSpec,
    command: Sequence[str],
    runner_mode: str,
    *,
    head: str,
    spec_sha256: str,
    registration_sha256: str,
    runner_sha256: str,
    tool_sha256: str,
    collection_sha256: str,
    attempt_recorder: AttemptRecorder | None = None,
) -> dict[str, Any]:
    _assert_only_expected_dirt(repo, head, ())
    stop = _dispatch_orphan_stop(
        repo,
        runner_mode=runner_mode,
        phase="baseline",
        mutation_id=None,
        source_state="unchanged",
        dirty_paths=(),
    )
    if stop is not None:
        raise stop
    result = _run_tests(
        repo,
        command,
        timeout_s=_effective_timeout(spec, runner_mode),
        runner_mode=runner_mode,
        attempt_recorder=attempt_recorder,
        attempt_phase="baseline" if attempt_recorder is not None else None,
    )
    stop = _dispatch_orphan_stop(
        repo,
        runner_mode=runner_mode,
        phase="baseline",
        mutation_id=None,
        source_state="unchanged",
        dirty_paths=(),
        result=result,
    )
    if stop is not None:
        raise stop
    output = result.get("job_stdout", "")
    try:
        failed = _failed_nodes(output, repo)
    except HarnessError as exc:
        result["artifact_error"] = str(exc)
        failed = []
    rc = result["rc"]
    if result["timed_out"]:
        status = "TIMEOUT"
    elif (
        result.get("artifact_error") is not None
        or rc not in PYTEST_NORMAL_RCS
        or (rc != 0 and not failed)
    ):
        status = "PARSE_ERROR"
    elif rc == 0 and not failed:
        status = "PASSED"
    else:
        status = "FAILED"
    return {
        "status": status,
        "rc": rc,
        "failed_nodes": failed,
        "timed_out": result["timed_out"],
        "duration_s": result["duration_s"],
        "artifact_error": result.get("artifact_error"),
        "artifact": _artifact(result, output, runner_mode),
        "test_output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "test_output_tail": output.splitlines()[-80:] if status != "PASSED" else [],
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "registration_sha256": registration_sha256,
        "runner_sha256": runner_sha256,
        "tool_sha256": tool_sha256,
        "collection_sha256": collection_sha256,
    }


def _apply_mutation(
    repo: Path,
    head: str,
    originals: dict[str, str],
    mutation: Mutation,
    spec: MutationSpec,
    command: Sequence[str],
    runner_mode: str,
    registration: dict[str, Any],
    *,
    spec_sha256: str,
    runner_sha256: str,
    tool_sha256: str,
    collection_sha256: str,
    attempt_recorder: AttemptRecorder | None = None,
) -> dict[str, Any]:
    _assert_head(repo, head)
    _verify_originals(repo, originals)
    stop = _dispatch_orphan_stop(
        repo,
        runner_mode=runner_mode,
        phase="mutation",
        mutation_id=mutation.id,
        source_state="unchanged",
        dirty_paths=(),
    )
    if stop is not None:
        raise stop
    mutated, diff, counts = _mutated_sources(mutation, originals)
    diff_sha256 = hashlib.sha256(diff.encode("utf-8")).hexdigest()
    if (
        counts != registration["anchor_counts"]
        or diff_sha256 != registration["injection_diff_sha256"]
    ):
        raise HarnessError(f"{mutation.id}: preflight と実適用の injection evidence が不一致")
    touched = tuple(sorted(mutated))
    pending_stop: OrphanHoldStop | None = None
    signal_abort: SignalAbort | None = None
    origin_error: BaseException | None = None
    injection_complete = False
    result: dict[str, Any] | None = None
    try:
        for rel in touched:
            target = repo / rel
            if target.is_symlink() or not target.is_file():
                raise HarnessError(f"{mutation.id}: 注入先が通常 file でない: {rel}")
            target.write_text(mutated[rel], encoding="utf-8")
        for rel in touched:
            if (repo / rel).read_text(encoding="utf-8") != mutated[rel]:
                raise HarnessError(f"{mutation.id}: 注入 read-back が不一致: {rel}")
        _purge_pycache(repo, touched)
        _assert_only_expected_dirt(repo, head, touched)
        injection_complete = True
        pending_stop = _dispatch_orphan_stop(
            repo,
            runner_mode=runner_mode,
            phase="mutation",
            mutation_id=mutation.id,
            source_state="mutation-left-in-place",
            dirty_paths=touched,
        )
        if pending_stop is not None:
            raise pending_stop
        timeout_s = _effective_timeout(
            spec, runner_mode, hang_risk=mutation.hang_risk
        )
        result = _run_tests(
            repo,
            command,
            timeout_s=timeout_s,
            runner_mode=runner_mode,
            attempt_recorder=attempt_recorder,
            attempt_phase="mutation" if attempt_recorder is not None else None,
            mutation_id=mutation.id if attempt_recorder is not None else None,
        )
        pending_stop = _dispatch_orphan_stop(
            repo,
            runner_mode=runner_mode,
            phase="mutation",
            mutation_id=mutation.id,
            source_state="mutation-left-in-place",
            dirty_paths=touched,
            result=result,
        )
        if pending_stop is not None:
            raise pending_stop
        output = result.get("job_stdout", "")
        try:
            failed = _failed_nodes(output, repo)
            expected = [_normalize_node(node, repo) for node in mutation.expected_nodes]
        except HarnessError as exc:
            result["artifact_error"] = str(exc)
            failed = []
            expected = list(mutation.expected_nodes)
        status = _observed_status(
            result=result, failed=failed, expected=expected, repo=repo
        )
        return {
            "id": mutation.id,
            "category": mutation.category,
            "replacements": [dataclasses.asdict(item) for item in mutation.replacements],
            "expected_nodes": expected,
            "expected_status": mutation.expected_status,
            "hang_risk": mutation.hang_risk,
            "status": status,
            "matches_expectation": status == mutation.expected_status,
            "rc": result["rc"],
            "failed_nodes": failed,
            "timed_out": result["timed_out"],
            "duration_s": result["duration_s"],
            "artifact_error": result.get("artifact_error"),
            "artifact": _artifact(result, output, runner_mode),
            "anchor_counts": counts,
            "injection_diff_sha256": diff_sha256,
            "test_output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
            "test_output_tail": (
                output.splitlines()[-80:] if status in {"MISMATCH", "PARSE_ERROR"} else []
            ),
            "repo_head": head,
            "spec_sha256": spec_sha256,
            "registration_sha256": _json_sha256(registration),
            "runner_sha256": runner_sha256,
            "tool_sha256": tool_sha256,
            "collection_sha256": collection_sha256,
        }
    except BaseException as exc:
        if isinstance(exc, SignalAbort):
            signal_abort = exc
        if exc is not pending_stop:
            origin_error = exc
        raise
    finally:
        hold_present = (
            runner_mode == "dispatch"
            and _dispatch_orphan_hold_present(repo)
        )
        preserve = pending_stop is not None or hold_present
        if preserve:
            verification_error: BaseException | None = None
            try:
                _assert_only_expected_dirt(repo, head, touched)
                _assert_head(repo, head)
                if injection_complete:
                    for rel in touched:
                        if (repo / rel).read_text(encoding="utf-8") != mutated[rel]:
                            raise HarnessError(
                                f"{mutation.id}: orphan hold 後の変異 bytes が不一致: {rel}"
                            )
            except BaseException as exc:
                verification_error = exc
            had_pending_stop = pending_stop is not None
            if pending_stop is None:
                pending_stop = OrphanHoldStop(
                    phase="mutation",
                    mutation_id=mutation.id,
                    hold_path=_dispatch_orphan_hold_path(repo),
                    source_state="mutation-left-in-place",
                    dirty_paths=touched,
                    active_record=result,
                )
            if origin_error is not None:
                pending_stop.record_origin_error(origin_error)
            if verification_error is not None:
                pending_stop.record_verification_error(verification_error)
            if signal_abort is not None:
                signal_abort.orphan_stop = pending_stop
            elif origin_error is not None:
                raise pending_stop from origin_error
            elif verification_error is not None:
                raise pending_stop from verification_error
            elif not had_pending_stop:
                raise pending_stop
        else:
            _restore_targets(repo, {rel: originals[rel] for rel in touched})
            _assert_head(repo, head)


def _summary(spec: MutationSpec, records: Sequence[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "registered": len(spec.mutations),
        "recorded": len(records),
        "completed": 0,
        "matching": 0,
        "KILLED": 0,
        "SURVIVED": 0,
        "MISMATCH": 0,
        "TIMEOUT": 0,
        "PARSE_ERROR": 0,
    }
    for record in records:
        status = record.get("status")
        if status not in TERMINAL_STATUSES | {"PARSE_ERROR"}:
            raise HarnessError(f"ledger mutation status が未知: {status!r}")
        summary[status] += 1
        if status in TERMINAL_STATUSES:
            summary["completed"] += 1
        if record.get("matches_expectation") is True:
            summary["matching"] += 1
    return summary


def _runner_sha256(identity: dict[str, Any]) -> str:
    return _json_sha256(identity)


def _new_ledger(
    *,
    head: str,
    spec: MutationSpec,
    spec_sha256: str,
    runner_sha256: str,
    runner_identity: dict[str, Any],
    tool_sha256: str,
    tool_identity: dict[str, Any],
    runner_mode: str,
    command: Sequence[str],
    registration: dict[str, Any],
    collection: dict[str, Any],
) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    return {
        "schema": LEDGER_SCHEMA,
        "date": now,
        "updated_at": now,
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "runner_sha256": runner_sha256,
        "runner_identity": runner_identity,
        "tool_sha256": tool_sha256,
        "tool_identity": tool_identity,
        "procedure": {
            "runner_mode": runner_mode,
            "test_command": list(command),
            "timeout_seconds": spec.timeout_seconds,
            "hang_timeout_seconds": spec.hang_timeout_seconds,
            "source_policy": "fixed repo_head blob plus startup/read-back equality",
            "restore_policy": "write fixed repo_head text then exact read_text equality",
            "node_policy": "trusted pytest collection plus parameter-exact failed-node set",
            "registration_preflight": registration,
            "registration_sha256": _json_sha256(registration),
            "collection": collection,
        },
        "baseline": None,
        "summary": _summary(spec, records),
        "mutations": records,
        "nonterminal_history": [],
    }


def _validate_collection_record(
    value: Any,
    *,
    repo: Path,
    spec: MutationSpec,
    head: str,
    spec_sha256: str,
    runner_sha256: str,
    tool_sha256: str,
    runner_mode: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HarnessError("resume ledger collection record が object でない")
    _require_exact_keys(value, set(COLLECTION_FIELDS), "collection record")
    expected = {
        "status": "PASSED",
        "rc": 0,
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "runner_sha256": runner_sha256,
        "tool_sha256": tool_sha256,
    }
    for key, expected_value in expected.items():
        if value[key] != expected_value:
            raise HarnessError(f"collection record の {key} が不一致")
    output = _validate_artifact(
        value["artifact"], repo=repo, runner_mode=runner_mode, label="collection"
    )
    collected = _collected_nodes(output, repo)
    if not collected or value["collected_nodes"] != collected:
        raise HarnessError("collection record の collected_nodes が artifact と不一致")
    missing = sorted(
        {
            _match_key(node, repo)
            for mutation in spec.mutations
            for node in mutation.expected_nodes
        }
        - {_match_key(node, repo) for node in collected}
    )
    if missing:
        raise HarnessError(f"collection record に期待 node がない: {missing}")
    if (
        isinstance(value["duration_s"], bool)
        or not isinstance(value["duration_s"], (int, float))
        or value["duration_s"] < 0
    ):
        raise HarnessError("collection record duration_s が非負数でない")
    return value


def _validate_baseline_record(
    value: Any,
    *,
    repo: Path,
    head: str,
    spec_sha256: str,
    registration_sha256: str,
    runner_sha256: str,
    tool_sha256: str,
    collection_sha256: str,
    runner_mode: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HarnessError("resume ledger baseline record が object でない")
    _require_exact_keys(value, set(BASELINE_FIELDS), "baseline record")
    _validate_run_record_types(value, "baseline record")
    expected = {
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "registration_sha256": registration_sha256,
        "runner_sha256": runner_sha256,
        "tool_sha256": tool_sha256,
        "collection_sha256": collection_sha256,
    }
    for key, expected_value in expected.items():
        if value[key] != expected_value:
            raise HarnessError(f"baseline record の {key} が不一致")
    output = _validate_artifact(
        value["artifact"],
        repo=repo,
        runner_mode=runner_mode,
        label="baseline",
        allow_incomplete_dispatch=value["artifact_error"] is not None,
    )
    if value["test_output_sha256"] != hashlib.sha256(output.encode("utf-8")).hexdigest():
        raise HarnessError("baseline record の test_output_sha256 が不一致")
    failed = _failed_nodes(output, repo)
    if value["failed_nodes"] != failed:
        raise HarnessError("baseline record の failed_nodes が artifact と不一致")
    rc = value["rc"]
    if value["timed_out"]:
        status = "TIMEOUT"
    elif (
        value["artifact_error"] is not None
        or rc not in PYTEST_NORMAL_RCS
        or (rc != 0 and not failed)
    ):
        status = "PARSE_ERROR"
    elif rc == 0 and not failed:
        status = "PASSED"
    else:
        status = "FAILED"
    if value["status"] != status:
        raise HarnessError("baseline record の status が evidence と不一致")
    tail = output.splitlines()[-80:] if status != "PASSED" else []
    if value["test_output_tail"] != tail:
        raise HarnessError("baseline record の test_output_tail が artifact と不一致")
    return value


def _validate_mutation_record(
    value: Any,
    *,
    repo: Path,
    mutation: Mutation,
    registration: dict[str, Any],
    head: str,
    spec_sha256: str,
    runner_sha256: str,
    tool_sha256: str,
    collection_sha256: str,
    runner_mode: str,
) -> dict[str, Any]:
    label = f"mutation record {mutation.id}"
    if not isinstance(value, dict):
        raise HarnessError(f"{label} が object でない")
    _require_exact_keys(value, set(MUTATION_RECORD_FIELDS), label)
    _validate_run_record_types(value, label)
    static = {
        "id": mutation.id,
        "category": mutation.category,
        "replacements": [dataclasses.asdict(item) for item in mutation.replacements],
        "expected_nodes": registration["expected_nodes"],
        "expected_status": mutation.expected_status,
        "hang_risk": mutation.hang_risk,
        "anchor_counts": registration["anchor_counts"],
        "injection_diff_sha256": registration["injection_diff_sha256"],
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "registration_sha256": _json_sha256(registration),
        "runner_sha256": runner_sha256,
        "tool_sha256": tool_sha256,
        "collection_sha256": collection_sha256,
    }
    for key, expected_value in static.items():
        if value[key] != expected_value:
            raise HarnessError(f"{label} の {key} が現 spec/evidence と不一致")
    artifact_error = value["artifact_error"]
    output = _validate_artifact(
        value["artifact"],
        repo=repo,
        runner_mode=runner_mode,
        label=label,
        allow_incomplete_dispatch=artifact_error is not None,
    )
    if value["test_output_sha256"] != hashlib.sha256(output.encode("utf-8")).hexdigest():
        raise HarnessError(f"{label} の test_output_sha256 が不一致")
    parser_error: str | None = None
    try:
        failed = _failed_nodes(output, repo)
    except HarnessError as exc:
        parser_error = str(exc)
        failed = []
    if value["failed_nodes"] != failed:
        raise HarnessError(f"{label} の failed_nodes が artifact と不一致")
    effective_error = artifact_error if artifact_error is not None else parser_error
    status = _observed_status(
        result={
            "timed_out": value["timed_out"],
            "rc": value["rc"],
            "artifact_error": effective_error,
        },
        failed=failed,
        expected=registration["expected_nodes"],
        repo=repo,
    )
    if value["status"] != status:
        raise HarnessError(f"{label} の status が rc/node/artifact evidence と不一致")
    if value["matches_expectation"] is not (status == mutation.expected_status):
        raise HarnessError(f"{label} の matches_expectation が不一致")
    tail = output.splitlines()[-80:] if status in {"MISMATCH", "PARSE_ERROR"} else []
    if value["test_output_tail"] != tail:
        raise HarnessError(f"{label} の test_output_tail が artifact と不一致")
    return value


def _validate_run_record_types(value: dict[str, Any], label: str) -> None:
    if not isinstance(value["timed_out"], bool):
        raise HarnessError(f"{label} timed_out が bool でない")
    rc = value["rc"]
    if rc is not None and (isinstance(rc, bool) or not isinstance(rc, int)):
        raise HarnessError(f"{label} rc が int/null でない")
    duration = value["duration_s"]
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or duration < 0
    ):
        raise HarnessError(f"{label} duration_s が非負数でない")
    artifact_error = value["artifact_error"]
    if artifact_error is not None and not isinstance(artifact_error, str):
        raise HarnessError(f"{label} artifact_error が string/null でない")
    for key in ("failed_nodes", "test_output_tail"):
        field = value[key]
        if not isinstance(field, list) or any(not isinstance(item, str) for item in field):
            raise HarnessError(f"{label} {key} が文字列 list でない")
    _require_sha256(value["test_output_sha256"], f"{label}.test_output_sha256")


def _load_resume_ledger(
    path: Path,
    *,
    repo: Path,
    head: str,
    spec: MutationSpec,
    spec_sha256: str,
    runner_sha256: str,
    runner_identity: dict[str, Any],
    tool_sha256: str,
    tool_identity: dict[str, Any],
    registration: dict[str, Any],
    runner_mode: str,
) -> dict[str, Any]:
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarnessError(f"resume ledger を読めない: {exc}") from exc
    if not isinstance(ledger, dict):
        raise HarnessError("resume ledger root が object でない")
    _require_exact_keys(
        ledger,
        {
            "schema",
            "date",
            "updated_at",
            "repo_head",
            "spec_sha256",
            "runner_sha256",
            "runner_identity",
            "tool_sha256",
            "tool_identity",
            "procedure",
            "baseline",
            "summary",
            "mutations",
            "nonterminal_history",
        },
        "resume ledger",
    )
    expected = {
        "schema": LEDGER_SCHEMA,
        "repo_head": head,
        "spec_sha256": spec_sha256,
        "runner_sha256": runner_sha256,
        "runner_identity": runner_identity,
        "tool_sha256": tool_sha256,
        "tool_identity": tool_identity,
    }
    for key, value in expected.items():
        if ledger.get(key) != value:
            raise HarnessError(f"resume ledger の {key} が現行 run と不一致")
    procedure = ledger["procedure"]
    if not isinstance(procedure, dict):
        raise HarnessError("resume ledger procedure が object でない")
    _require_exact_keys(
        procedure,
        {
            "runner_mode",
            "test_command",
            "timeout_seconds",
            "hang_timeout_seconds",
            "source_policy",
            "restore_policy",
            "node_policy",
            "registration_preflight",
            "registration_sha256",
            "collection",
        },
        "resume ledger procedure",
    )
    if procedure["runner_mode"] != runner_mode:
        raise HarnessError("resume ledger procedure runner_mode が不一致")
    procedure_expected = {
        "test_command": runner_identity["command"],
        "timeout_seconds": spec.timeout_seconds,
        "hang_timeout_seconds": spec.hang_timeout_seconds,
        "source_policy": "fixed repo_head blob plus startup/read-back equality",
        "restore_policy": "write fixed repo_head text then exact read_text equality",
        "node_policy": "trusted pytest collection plus parameter-exact failed-node set",
    }
    for key, expected_value in procedure_expected.items():
        if procedure[key] != expected_value:
            raise HarnessError(f"resume ledger procedure {key} が不一致")
    if procedure["registration_preflight"] != registration:
        raise HarnessError("resume ledger registration_preflight が現 spec と不一致")
    registration_sha256 = _json_sha256(registration)
    if procedure["registration_sha256"] != registration_sha256:
        raise HarnessError("resume ledger registration_sha256 が不一致")
    collection = _validate_collection_record(
        procedure["collection"],
        repo=repo,
        spec=spec,
        head=head,
        spec_sha256=spec_sha256,
        runner_sha256=runner_sha256,
        tool_sha256=tool_sha256,
        runner_mode=runner_mode,
    )
    collection_sha256 = _json_sha256(collection)
    _validate_baseline_record(
        ledger["baseline"],
        repo=repo,
        head=head,
        spec_sha256=spec_sha256,
        registration_sha256=registration_sha256,
        runner_sha256=runner_sha256,
        tool_sha256=tool_sha256,
        collection_sha256=collection_sha256,
        runner_mode=runner_mode,
    )
    records = ledger["mutations"]
    history = ledger["nonterminal_history"]
    if not isinstance(records, list) or not isinstance(history, list):
        raise HarnessError("resume ledger mutations/nonterminal_history が list でない")
    mutation_by_id = {mutation.id: mutation for mutation in spec.mutations}
    known_ids = set(mutation_by_id)
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or record.get("id") not in known_ids:
            raise HarnessError("resume ledger mutation record の field 集合が不正または ID が未知である")
        mutation_id = record["id"]
        if mutation_id in seen:
            raise HarnessError(f"resume ledger の mutation ID が重複: {mutation_id}")
        seen.add(mutation_id)
        mutation = mutation_by_id[mutation_id]
        _validate_mutation_record(
            record,
            repo=repo,
            mutation=mutation,
            registration=registration[mutation_id],
            head=head,
            spec_sha256=spec_sha256,
            runner_sha256=runner_sha256,
            tool_sha256=tool_sha256,
            collection_sha256=collection_sha256,
            runner_mode=runner_mode,
        )
        status = record["status"]
        if status == "PARSE_ERROR":
            history.append(record)
            continue
        if status not in TERMINAL_STATUSES:
            raise HarnessError(f"resume ledger の {mutation_id} status が不正: {status!r}")
        kept.append(record)
    for record in history:
        if not isinstance(record, dict) or record.get("id") not in known_ids:
            raise HarnessError("resume ledger history に未知または不正な record がある")
        mutation = mutation_by_id[record["id"]]
        _validate_mutation_record(
            record,
            repo=repo,
            mutation=mutation,
            registration=registration[mutation.id],
            head=head,
            spec_sha256=spec_sha256,
            runner_sha256=runner_sha256,
            tool_sha256=tool_sha256,
            collection_sha256=collection_sha256,
            runner_mode=runner_mode,
        )
        if record["status"] != "PARSE_ERROR":
            raise HarnessError("resume ledger history は PARSE_ERROR record のみ許可する")
    ledger["mutations"] = kept
    ledger["nonterminal_history"] = history
    expected_summary = _summary(spec, kept)
    if ledger["summary"] != _summary(spec, records):
        raise HarnessError("resume ledger summary が保存 record と不一致")
    ledger["summary"] = expected_summary
    return ledger


def _write_json_atomic(path: Path, document: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_ledger(path: Path, ledger: dict[str, Any]) -> None:
    _write_json_atomic(path, ledger)


def _orphan_stop_path(ledger_path: Path) -> Path:
    return Path(f"{ledger_path}.orphan-stop.json")


def _orphan_stop_gate_message(path: Path) -> str:
    hold_error: str | None = None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        document = None
    if isinstance(document, dict):
        reason = document.get("reason")
        if isinstance(reason, dict) and reason.get("hold_error") is not None:
            hold_error = str(reason["hold_error"])
    hold_error_detail = (
        f"、reason.hold_error={hold_error}" if hold_error is not None else ""
    )
    return (
        "orphan-stop sidecar が存在または判定不能のため停止: "
        f"sidecar path={path}{hold_error_detail}。"
        "復旧順序: 対象の不在または終端を確認 → dirty path の復元 → "
        "clean/HEAD 確認 → hold と sidecar の手動削除"
    )


def _orphan_recovery(stop: OrphanHoldStop) -> str:
    dirty = " ".join(stop.dirty_paths) if stop.dirty_paths else "<なし>"
    if not stop.hold_latched:
        return (
            "job が投入された可能性を scheduler 上で確認し、"
            f"dirty path ({dirty}) を安全確認後に復元し、"
            "clean/HEAD を確認してから sidecar を手動削除する。"
            "D454 orphan hold latch は作成していない。"
        )
    return (
        "qstat で対象の不在または終端を確認し、"
        f"dirty path ({dirty}) を git checkout -- で復元し、"
        "clean/HEAD を確認してから hold と sidecar を手動削除する。"
        "手動 qdel は F47 ラッチを武装させ、その解除もユーザー手番になる。"
    )


def _write_orphan_stop_ledger(
    path: Path,
    *,
    stop: OrphanHoldStop,
    head: str,
    spec_sha256: str,
    ledger_path: Path,
) -> None:
    reason = {
        "code": stop.reason_code,
        "phase": stop.phase,
        "mutation_id": stop.mutation_id,
        "hold_path": str(stop.hold_path),
        "source_state": stop.source_state,
        "dirty_paths": list(stop.dirty_paths),
        "recovery": _orphan_recovery(stop),
    }
    if not stop.hold_latched:
        submission = (
            stop.active_record.get("dispatch_submission")
            if isinstance(stop.active_record, dict)
            else None
        )
        reason.update(
            {
                "hold_latched": False,
                "job_may_have_been_submitted": True,
                "verification_required": True,
                "dispatch_submission_state": (
                    submission.get("state")
                    if isinstance(submission, dict)
                    else "indeterminate"
                ),
            }
        )
    if stop.hold_error is not None:
        reason["hold_error"] = stop.hold_error
    if stop.origin_error_type is not None:
        reason["origin_error_type"] = stop.origin_error_type
        reason["origin_error_message"] = stop.origin_error_message
    if stop.verification_error_type is not None:
        reason["verification_error_type"] = stop.verification_error_type
        reason["verification_error_message"] = stop.verification_error_message
    _write_ledger(
        path,
        {
            "schema": ORPHAN_STOP_SCHEMA,
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_head": head,
            "spec_sha256": spec_sha256,
            "reason": reason,
            "ledger_path": str(ledger_path),
            "active_record": stop.active_record,
        },
    )


def _print_orphan_stop(stop: OrphanHoldStop) -> None:
    dirty = ", ".join(stop.dirty_paths) if stop.dirty_paths else "なし"
    if not stop.hold_latched:
        print(
            f"mutation harness aborted: {stop.reason_code}。"
            f"変異を残した状態={stop.source_state}、dirty path={dirty}。"
            f"復旧順序: {_orphan_recovery(stop)}",
            file=sys.stderr,
            flush=True,
        )
        return
    print(
        f"mutation harness aborted: {stop.reason_code}。"
        f"変異を残した状態={stop.source_state}、dirty path={dirty}、"
        f"hold path={stop.hold_path}。復旧順序: {_orphan_recovery(stop)}",
        file=sys.stderr,
        flush=True,
    )


def _lock_path_for(repo: Path) -> Path:
    key = hashlib.sha256(str(repo).encode("utf-8")).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / f"izanagi-mutation-{key}.lock"


def _lock_for(repo: Path) -> Any:
    lock_path = _lock_path_for(repo)
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_RDWR | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError as exc:
        raise HarnessError(f"mutation harness lock を安全に開けない: {exc}") from exc
    stream = os.fdopen(descriptor, "a+", encoding="utf-8")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        stream.close()
        raise HarnessError("別の mutation harness が同じ repo で走行中") from exc
    return stream


def _install_signal_handlers() -> dict[int, Any]:
    old_handlers: dict[int, Any] = {}

    def handler(signum: int, _frame: Any) -> None:
        for guarded in (signal.SIGINT, signal.SIGTERM):
            signal.signal(guarded, signal.SIG_IGN)
        raise SignalAbort(signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, handler)
    return old_handlers


def _restore_signal_handlers(old_handlers: dict[int, Any]) -> None:
    for signum, old_handler in old_handlers.items():
        signal.signal(signum, old_handler)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--expected-spec-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--attempt-out", type=Path)
    parser.add_argument("--wrapper-attempt", type=int)
    parser.add_argument("--runner-mode", required=True, choices=("local", "dispatch"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--detached",
        action="store_true",
        help="外側の時間上限に掛からない detached 経路からの起動であると確認する",
    )
    parser.add_argument(
        "--plan-only", action="store_true", help="preflight と所要見積りだけを行い書き込まない"
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="-- に続けて渡す test runner argv。shell expansion は行わない",
    )
    return parser


def _refusing_local_site(runner_mode: str) -> str | None:
    if runner_mode != "local":
        return None
    site = site_policy.current_site(require_evidence=True)
    if site in {site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT}:
        return site
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if (args.attempt_out is None) is not (args.wrapper_attempt is None):
        raise HarnessError("--attempt-out と --wrapper-attempt は同時指定が必要")
    if args.wrapper_attempt is not None and (
        isinstance(args.wrapper_attempt, bool) or args.wrapper_attempt < 1
    ):
        raise HarnessError("--wrapper-attempt は 1 以上の int でなければならない")
    local_authorization: dict[str, Any] | None = None
    if args.attempt_out is not None and args.runner_mode == "local":
        try:
            from tools.pegasus import dispatch_compute

            local_authorization = mutation_attempt_marker.require_local_attempt_marker(
                normalize_request_id=dispatch_compute._normalize_request_id,
                is_regular_pbs_jobid=dispatch_compute._is_regular_pbs_jobid,
            )
        except mutation_attempt_marker.MutationAttemptMarkerError as exc:
            raise HarnessError(
                f"local attempt authorization が不正です: {exc}"
            ) from exc
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        raise HarnessError("test runner argv を -- の後へ指定する必要がある")
    if "-rf" not in command:
        raise HarnessError("test runner argv は DW-M08 の -rf を含まなければならない")
    if not any(
        command[index : index + 2] == ["-p", "no:cacheprovider"]
        for index in range(len(command) - 1)
    ):
        command.extend(["-p", "no:cacheprovider"])
    if not args.plan_only and not args.detached:
        raise HarnessError("実走は外側上限外の detached 経路から --detached を付けて起動する")

    if args.spec.is_symlink():
        raise HarnessError("--spec に symlink を指定してはならない")
    if args.out.is_symlink():
        raise HarnessError("--out に symlink を指定してはならない")
    if args.attempt_out is not None and args.attempt_out.is_symlink():
        raise HarnessError("--attempt-out に symlink を指定してはならない")
    try:
        repo = args.repo.resolve(strict=True)
    except OSError as exc:
        raise HarnessError(f"--repo を解決できない: {exc}") from exc
    refusing_site = _refusing_local_site(args.runner_mode)
    if refusing_site is not None:
        print(
            "mutation harness aborted: --runner-mode local は "
            f"{refusing_site} で実行できない",
            file=sys.stderr,
            flush=True,
        )
        return 2
    out = args.out.resolve()
    orphan_stop = _orphan_stop_path(out)
    if _path_present_fail_closed(orphan_stop):
        raise HarnessError(_orphan_stop_gate_message(orphan_stop))
    spec_path = args.spec.resolve()
    attempt_out = args.attempt_out.resolve() if args.attempt_out is not None else None
    _assert_runtime_artifacts_outside_repo(
        repo, spec_path=spec_path, out=out, attempt_out=attempt_out
    )
    spec, spec_sha256 = _load_spec(spec_path)
    expected_spec_sha256 = _require_sha256(
        args.expected_spec_sha256, "--expected-spec-sha256"
    )
    if spec_sha256 != expected_spec_sha256:
        raise HarnessError(
            "spec SHA-256 が段 4 の事前登録値と不一致: "
            f"expected={expected_spec_sha256}, actual={spec_sha256}"
        )
    lock_stream = _lock_for(repo)
    ledger: dict[str, Any] | None = None
    head = ""
    try:
        head = _repo_head(repo)
        originals = _read_head_sources(repo, head, spec)
        _assert_clean_tracked(repo)
        registration = _validate_registrations(repo, spec, originals)
        runner_identity = _runner_identity(repo, head, args.runner_mode, command)
        runner_sha256 = _runner_sha256(runner_identity)
        tool_identity = _tool_identity(repo, head)
        tool_sha256 = _json_sha256(tool_identity)
        attempt_recorder = (
            _new_attempt_recorder(
                attempt_out,
                resume=args.resume,
                wrapper_attempt_ordinal=args.wrapper_attempt,
                head=head,
                spec=spec,
                spec_sha256=spec_sha256,
                runner_sha256=runner_sha256,
                tool_sha256=tool_sha256,
                local_authorization=local_authorization,
            )
            if attempt_out is not None and not args.plan_only
            else None
        )
        if args.resume:
            if out.is_symlink() or not out.is_file():
                raise HarnessError("--resume には既存の symlink でない通常 --out file が必要")
            ledger = _load_resume_ledger(
                out,
                repo=repo,
                head=head,
                spec=spec,
                spec_sha256=spec_sha256,
                runner_sha256=runner_sha256,
                runner_identity=runner_identity,
                tool_sha256=tool_sha256,
                tool_identity=tool_identity,
                registration=registration,
                runner_mode=args.runner_mode,
            )
            collection = ledger["procedure"]["collection"]
        else:
            if out.exists():
                raise HarnessError("--out が既に存在する; 続行は --resume を明示する")
            collection = None

        completed_ids = (
            {record["id"] for record in ledger["mutations"]} if ledger is not None else set()
        )
        pending = [mutation for mutation in spec.mutations if mutation.id not in completed_ids]
        baseline_runs = 1 if ledger is None or ledger.get("baseline") is None else 0
        total_runs = baseline_runs + len(pending)
        estimate = total_runs * spec.estimated_run_seconds
        print(
            f"mutation estimate: {len(pending)} mutation(s) x "
            f"{spec.estimated_run_seconds:.3f}s, baseline={baseline_runs} run(s), "
            f"total={total_runs} run(s)/{estimate:.3f}s; "
            "actual execution requires an outer-limit-free detached path",
            flush=True,
        )
        if args.plan_only:
            return 0

        if ledger is None:
            collection = _collect_expected_nodes(
                repo,
                spec,
                command,
                args.runner_mode,
                head=head,
                spec_sha256=spec_sha256,
                runner_sha256=runner_sha256,
                tool_sha256=tool_sha256,
                attempt_recorder=attempt_recorder,
            )
            _validate_collection_record(
                collection,
                repo=repo,
                spec=spec,
                head=head,
                spec_sha256=spec_sha256,
                runner_sha256=runner_sha256,
                tool_sha256=tool_sha256,
                runner_mode=args.runner_mode,
            )
            ledger = _new_ledger(
                head=head,
                spec=spec,
                spec_sha256=spec_sha256,
                runner_sha256=runner_sha256,
                runner_identity=runner_identity,
                tool_sha256=tool_sha256,
                tool_identity=tool_identity,
                runner_mode=args.runner_mode,
                command=command,
                registration=registration,
                collection=collection,
            )
        assert collection is not None
        registration_sha256 = _json_sha256(registration)
        collection_sha256 = _json_sha256(collection)

        old_handlers = _install_signal_handlers()
        try:
            records = ledger["mutations"]
            baseline = ledger.get("baseline")
            if baseline is None:
                if records:
                    raise HarnessError("baseline のない ledger に terminal mutation record がある")
                baseline = _baseline(
                    repo,
                    spec,
                    command,
                    args.runner_mode,
                    head=head,
                    spec_sha256=spec_sha256,
                    registration_sha256=registration_sha256,
                    runner_sha256=runner_sha256,
                    tool_sha256=tool_sha256,
                    collection_sha256=collection_sha256,
                    attempt_recorder=attempt_recorder,
                )
                _validate_baseline_record(
                    baseline,
                    repo=repo,
                    head=head,
                    spec_sha256=spec_sha256,
                    registration_sha256=registration_sha256,
                    runner_sha256=runner_sha256,
                    tool_sha256=tool_sha256,
                    collection_sha256=collection_sha256,
                    runner_mode=args.runner_mode,
                )
                ledger["baseline"] = baseline
                ledger["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                ledger["summary"] = _summary(spec, records)
                _write_ledger(out, ledger)
            if not isinstance(baseline, dict) or baseline.get("status") != "PASSED":
                raise HarnessError(
                    "baseline が緑でないため production write を開始しない: "
                    f"status={baseline.get('status') if isinstance(baseline, dict) else None}"
                )
            if baseline.get("rc") != 0 or baseline.get("failed_nodes") != []:
                raise HarnessError("baseline PASSED record の rc/failed_nodes が不整合")

            for mutation in pending:
                record = _apply_mutation(
                    repo,
                    head,
                    originals,
                    mutation,
                    spec,
                    command,
                    args.runner_mode,
                    registration[mutation.id],
                    spec_sha256=spec_sha256,
                    runner_sha256=runner_sha256,
                    tool_sha256=tool_sha256,
                    collection_sha256=collection_sha256,
                    attempt_recorder=attempt_recorder,
                )
                _validate_mutation_record(
                    record,
                    repo=repo,
                    mutation=mutation,
                    registration=registration[mutation.id],
                    head=head,
                    spec_sha256=spec_sha256,
                    runner_sha256=runner_sha256,
                    tool_sha256=tool_sha256,
                    collection_sha256=collection_sha256,
                    runner_mode=args.runner_mode,
                )
                records.append(record)
                ledger["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                ledger["summary"] = _summary(spec, records)
                _write_ledger(out, ledger)
                if record["status"] == "PARSE_ERROR":
                    raise HarnessError(
                        f"{mutation.id}: rc={record['rc']} だが canonical stdout から "
                        "failed node を確実に抽出できないため停止"
                    )
        finally:
            _restore_signal_handlers(old_handlers)
        _verify_originals(repo, originals)
        _assert_head(repo, head)
        return 0 if all(record["matches_expectation"] for record in ledger["mutations"]) else 1
    except OrphanHoldStop as stop:
        _write_orphan_stop_ledger(
            _orphan_stop_path(out),
            stop=stop,
            head=head,
            spec_sha256=spec_sha256,
            ledger_path=out,
        )
        _print_orphan_stop(stop)
        return 2
    except SignalAbort as exc:
        if exc.orphan_stop is not None:
            _write_orphan_stop_ledger(
                _orphan_stop_path(out),
                stop=exc.orphan_stop,
                head=head,
                spec_sha256=spec_sha256,
                ledger_path=out,
            )
            _print_orphan_stop(exc.orphan_stop)
        raise
    finally:
        lock_stream.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SignalAbort as exc:
        if exc.orphan_stop is None:
            print(
                f"mutation harness interrupted by signal {exc.signum}; "
                "active mutation restore attempted",
                file=sys.stderr,
            )
        else:
            print(
                f"mutation harness interrupted by signal {exc.signum}; "
                "orphan hold のため復元を意図的に見送り、変異を残した",
                file=sys.stderr,
            )
        raise SystemExit(128 + exc.signum)
    except HarnessError as exc:
        print(f"mutation harness aborted: {exc}", file=sys.stderr)
        raise SystemExit(2)
