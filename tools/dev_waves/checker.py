"""Side-effect-free dev-wave verification with passive-before-active ordering."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Optional, Sequence

from .git_state import (
    RepoSnapshot,
    branch_tip,
    create_isolated_checkout,
    read_child_git_trace,
    snapshot_repo,
    trust_root,
    verify_ff_chain,
)
from .receipt import (
    ParsedChildResult, ReceiptBinding, parse_claude_result,
    permission_abort_from_envelope,
)
from .schema import (
    DevWavesError,
    Outcome,
    ReasonCode,
    Receipt,
    strict_loads,
)
from .worker import PidIdentity


_TASK_RE = re.compile(r"\[?(T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,}))\]?")
_NEXT_HEADING_RE = re.compile(r"^### 次の一手(?:[ \t].*)?$", re.MULTILINE)
_TOP_ITEM_RE = re.compile(r"^(?:[1-9][0-9]*\.|-)[ \t]+(.+)$", re.MULTILINE)
_CHECK_OUTPUT_LIMIT = 1 << 20


@dataclass(frozen=True)
class CheckSpec:
    name: str
    argv: tuple[str, ...]
    timeout_s: int

    def __post_init__(self) -> None:
        if (not self.name or "\x00" in self.name or not self.argv or
                any(not token or "\x00" in token for token in self.argv)):
            raise ValueError("invalid fixed check specification")
        if not isinstance(self.timeout_s, int) or isinstance(self.timeout_s, bool) or self.timeout_s < 1:
            raise ValueError("check timeout must be a positive integer")
        if re.fullmatch(r"python(?:3(?:\.\d+)?)?", os.path.basename(self.argv[0])) is None:
            raise ValueError("fixed checks must use the Python interpreter")
        if len(self.argv) >= 3 and self.argv[1:3] == ("-m", "pytest"):
            if not any(
                token == "orchestrator/tests" or token.startswith("orchestrator/tests/")
                for token in self.argv[3:]
            ):
                raise ValueError("pytest check must bind the trusted test tree")
        else:
            if len(self.argv) < 2:
                raise ValueError("fixed check script is missing")
            script = self.argv[1]
            if (os.path.isabs(script) or ".." in Path(script).parts or
                    script not in {"tools/run_tests.py", "tools/task_run_check.py"} and
                    (not script.startswith("tools/check_") or not script.endswith(".py"))):
                raise ValueError("fixed check script is outside the trust root")


@dataclass(frozen=True)
class VerificationInput:
    run_id: str
    wave_index: int
    repo_root: str
    main_worktree: str
    wave_worktree: str
    wave_branch: str
    before_main_sha: str
    before_snapshot: RepoSnapshot
    stdout_path: str
    stderr_path: str
    max_output_bytes: int
    child_start_path: str
    worker_exit_path: str
    git_trace_path: str
    per_wave_budget_usd: Decimal
    before_next_task_ids: tuple[str, ...]
    before_worklog_sha256: str
    worklog_path: str
    task_runs_root: str
    handoff_dir: str
    check_specs: tuple[CheckSpec, ...]
    total_deadline_boottime_ns: int
    immutable_digests_before: tuple[tuple[str, str], ...]
    immutable_digests_after: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class InvariantResult:
    name: str
    status: str
    reason: Optional[ReasonCode]
    detail: str


@dataclass(frozen=True)
class VerificationReport:
    ok: bool
    reason: Optional[ReasonCode]
    findings: tuple[InvariantResult, ...]
    receipt: Optional[Receipt]
    after_snapshot: Optional[RepoSnapshot]
    active_checks_started: bool


def _boottime_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_BOOTTIME)


def _remaining_s(deadline_ns: int, individual_s: int) -> float:
    remaining = (deadline_ns - _boottime_ns()) / 1_000_000_000
    if remaining <= 0:
        raise subprocess.TimeoutExpired("total-deadline", 0)
    return min(float(individual_s), remaining)


def _pass(name: str, detail: str = "ok") -> InvariantResult:
    return InvariantResult(name, "pass", None, detail)


def _fail(name: str, reason: ReasonCode, detail: str) -> InvariantResult:
    return InvariantResult(name, "fail", reason, detail)


def _skip(name: str, detail: str) -> InvariantResult:
    return InvariantResult(name, "not-evaluated", None, detail)


def _latest_entry(text: str) -> str:
    starts = [match.start() for match in re.finditer(r"^## [^#].*$", text, re.MULTILINE)]
    if not starts:
        raise ValueError("worklog has no entry")
    return text[starts[-1]:]


def extract_latest_next_action_ids(source: os.PathLike[str] | str) -> tuple[str, ...]:
    """Extract ordered IDs from the sole latest-entry `次の一手` section."""
    if isinstance(source, Path) or (isinstance(source, str) and os.path.exists(source)):
        text = Path(source).read_text(encoding="utf-8")
    elif isinstance(source, str):
        text = source
    else:
        raise TypeError("source must be text or a path")
    entry = _latest_entry(text)
    headings = list(_NEXT_HEADING_RE.finditer(entry))
    if len(headings) != 1:
        raise ValueError("latest entry must contain one next-action section")
    body = entry[headings[0].end():]
    next_heading = re.search(r"^### ", body, re.MULTILINE)
    if next_heading:
        body = body[:next_heading.start()]
    ids = []
    for item in _TOP_ITEM_RE.finditer(body):
        match = _TASK_RE.match(item.group(1).strip())
        if match is None:
            raise ValueError("top-level next action lacks canonical task ID")
        ids.append(match.group(1))
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("next-action IDs must be nonempty and unique")
    return tuple(ids)


def verify_task_run_finished(
    task_runs_root: os.PathLike[str] | str, task_run_id: str,
    *, validator_checkout: Optional[os.PathLike[str] | str] = None,
    total_deadline_boottime_ns: Optional[int] = None,
) -> bool:
    """Validate the bound task-run using the repository's strict read-only API."""
    if validator_checkout is not None:
        script = (
            "import pathlib,sys\n"
            "from tools.task_runs import validate_run\n"
            "v=validate_run(pathlib.Path(sys.argv[1])/sys.argv[2],require_finished=True)\n"
            "ends=[e for e in v.events if e.get('event')=='task_end']\n"
            "raise SystemExit(0 if v.task.get('task_run_id')==sys.argv[2] and "
            "len(ends)==1 and ends[0].get('outcome')=='completed' else 1)\n"
        )
        environment = _check_env()
        environment["PYTHONPATH"] = os.path.abspath(os.fspath(validator_checkout))
        try:
            timeout = (
                10.0 if total_deadline_boottime_ns is None
                else _remaining_s(total_deadline_boottime_ns, 10)
            )
            result = subprocess.run(
                [sys.executable, "-c", script, os.path.abspath(os.fspath(task_runs_root)),
                 task_run_id], cwd=os.fspath(validator_checkout), env=environment,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=timeout, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0
    try:
        from tools.task_runs import validate_run
        validated = validate_run(Path(task_runs_root) / task_run_id, require_finished=True)
    except Exception:
        return False
    endings = [event for event in validated.events if event.get("event") == "task_end"]
    return bool(
        validated.is_finished and validated.task.get("task_run_id") == task_run_id
        and len(endings) == 1 and endings[0].get("outcome") == "completed"
    )


def _strict_record(path: str, label: str, fields: frozenset[str]) -> dict[str, object]:
    raw = Path(path).read_bytes()
    value = strict_loads(raw, label=label, max_bytes=_CHECK_OUTPUT_LIMIT, allowed_fields=fields)
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("record field set")
    return value


_START_FIELDS = frozenset({"pid", "boot_id", "start_ticks", "pgid"})
_EXIT_FIELDS = frozenset({
    "child", "return_code", "reason", "timed_out", "log_limit_exceeded",
    "process_group_residual", "stdout_bytes", "stderr_bytes",
    "started_boottime_ns", "finished_boottime_ns",
})


def _pid_identity(value: object) -> PidIdentity:
    if not isinstance(value, dict) or set(value) != {"pid", "boot_id", "start_ticks"}:
        raise ValueError("pid identity fields")
    pid, boot, ticks = value["pid"], value["boot_id"], value["start_ticks"]
    if (not isinstance(pid, int) or isinstance(pid, bool) or pid < 1 or
            not isinstance(ticks, int) or isinstance(ticks, bool) or ticks < 1 or
            not isinstance(boot, str) or not boot):
        raise ValueError("pid identity values")
    return PidIdentity(pid, boot, ticks)


def _worker_gate(spec: VerificationInput) -> tuple[InvariantResult, Optional[dict[str, object]]]:
    try:
        exit_record = _strict_record(spec.worker_exit_path, "worker-exit", _EXIT_FIELDS)
        if exit_record["child"] is None:
            if (exit_record["return_code"] is not None or
                    exit_record["reason"] != ReasonCode.FAKE_HANDSHAKE_FAILED.value or
                    any(exit_record[field] is not False for field in (
                        "timed_out", "log_limit_exceeded", "process_group_residual",
                    )) or any(exit_record[field] != 0 for field in (
                        "stdout_bytes", "stderr_bytes",
                    ))):
                raise ValueError("invalid pre-spawn failure")
            return _fail(
                "worker", ReasonCode.FAKE_HANDSHAKE_FAILED,
                "worker-recorded-handshake-failure",
            ), exit_record
        start = _strict_record(spec.child_start_path, "child-start", _START_FIELDS)
        identity = _pid_identity(exit_record["child"])
        start_identity = _pid_identity({
            "pid": start["pid"], "boot_id": start["boot_id"],
            "start_ticks": start["start_ticks"],
        })
        pgid = start["pgid"]
        if (not isinstance(pgid, int) or isinstance(pgid, bool) or
                start_identity != identity or pgid != identity.pid):
            raise ValueError("identity mismatch")
        return_code = exit_record["return_code"]
        if not isinstance(return_code, int) or isinstance(return_code, bool):
            raise ValueError("return code type")
        for field in ("timed_out", "log_limit_exceeded", "process_group_residual"):
            if not isinstance(exit_record[field], bool):
                raise ValueError("worker boolean type")
        for field in ("stdout_bytes", "stderr_bytes", "started_boottime_ns", "finished_boottime_ns"):
            if (not isinstance(exit_record[field], int) or isinstance(exit_record[field], bool) or
                    exit_record[field] < 0):
                raise ValueError("worker integer type")
        if exit_record["finished_boottime_ns"] < exit_record["started_boottime_ns"]:
            raise ValueError("worker clock order")
        if (os.stat(spec.stdout_path).st_size != exit_record["stdout_bytes"] or
                os.stat(spec.stderr_path).st_size != exit_record["stderr_bytes"] or
                exit_record["stdout_bytes"] + exit_record["stderr_bytes"] > spec.max_output_bytes):
            raise ValueError("worker output size")
        if exit_record["process_group_residual"] is not False:
            return _fail("worker", ReasonCode.NONZERO_EXIT, "process-group-residual"), exit_record
        reason_raw = exit_record["reason"]
        reason = None if reason_raw is None else ReasonCode(reason_raw)
        if reason is not None:
            return _fail("worker", reason, "worker-recorded-stop"), exit_record
        if return_code != 0:
            return _fail("worker", ReasonCode.NONZERO_EXIT, "nonzero-return-code"), exit_record
        return _pass("worker"), exit_record
    except (OSError, ValueError, TypeError, DevWavesError):
        return _fail("worker", ReasonCode.SPAWN_FAILED, "invalid-worker-record"), None


def _check_env() -> dict[str, str]:
    environment = {
        key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TZ") if key in os.environ
    }
    environment.update({
        "LC_ALL": "C", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0", "PYTHONDONTWRITEBYTECODE": "1",
    })
    return environment


def run_check_specs(
    specs: Sequence[CheckSpec],
    checkout: os.PathLike[str] | str,
    *,
    total_deadline_boottime_ns: int,
) -> tuple[InvariantResult, ...]:
    """Run fixed check argv with every timeout clipped to total remaining time."""
    results = []
    for spec in specs:
        try:
            timeout = _remaining_s(total_deadline_boottime_ns, spec.timeout_s)
            process = subprocess.run(
                list(spec.argv), shell=False, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=os.fspath(checkout), env=_check_env(), timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            results.append(_fail(spec.name, ReasonCode.CHECK_FAILED, "timeout-or-exec"))
            continue
        if process.returncode == 0:
            results.append(_pass(spec.name))
        else:
            reason = (
                # rc=16 は Pegasus dispatch の infra 失敗であって check の判定結果ではない。
                ReasonCode.CHECK_FAILED if process.returncode == 16
                else ReasonCode.PROVENANCE_FAILED if "provenance" in spec.name
                else ReasonCode.CODE_DIRTY if spec.name in {"code-clean", "codex-agents"}
                else ReasonCode.CHECK_FAILED
            )
            results.append(_fail(spec.name, reason, "nonzero"))
    return tuple(results)


def _check_docs_spec(specs: Sequence[CheckSpec]) -> tuple[Optional[CheckSpec], tuple[CheckSpec, ...]]:
    docs = []
    others = []
    for spec in specs:
        if (any(os.path.basename(token) == "check_docs.py" for token in spec.argv) or
                any(os.path.basename(token) == "task_run_check.py" for token in spec.argv)
                and "docs-check" in spec.argv):
            docs.append(spec)
        else:
            others.append(spec)
    return (docs[0] if len(docs) == 1 else None), tuple(others)


def _active_reobserve(
    spec: VerificationInput,
    before_active: RepoSnapshot,
    wave_tip_before: Optional[str],
) -> InvariantResult:
    try:
        main = snapshot_repo(
            spec.main_worktree, timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
        )
        wave = snapshot_repo(
            spec.wave_worktree, timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
        )
        tip = branch_tip(
            spec.repo_root, spec.wave_branch,
            timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
        )
    except (DevWavesError, OSError, ValueError, subprocess.TimeoutExpired):
        return _fail("active-reobservation", ReasonCode.CHECK_FAILED, "snapshot-failed")
    if (main != before_active or wave.main_dirty or wave.submodule_dirty or
            wave_tip_before != tip):
        return _fail("active-reobservation", ReasonCode.CHECK_FAILED, "repository-changed")
    return _pass("active-reobservation")


_ORDER = (
    "worker", "output", "receipt", "cost-permission", "main-state", "ff-chain",
    "commit-chain", "wave-branch", "git-trace", "selected-task", "worklog",
    "check-docs", "task-run", "handoff", "fixed-checks", "trust-root",
    "remote-state", "active-reobservation",
)


def verify_wave(spec: VerificationInput) -> VerificationReport:
    """Evaluate every passive fact first and start no subprocess on passive failure."""
    if not isinstance(spec, VerificationInput):
        raise TypeError("spec must be VerificationInput")
    slots: dict[str, InvariantResult] = {}
    receipt_result: Optional[ParsedChildResult] = None
    receipt: Optional[Receipt] = None

    slots["worker"], _exit = _worker_gate(spec)
    try:
        receipt_result = parse_claude_result(
            spec.stdout_path, max_bytes=spec.max_output_bytes,
            binding=ReceiptBinding(spec.run_id, spec.wave_index, spec.before_main_sha),
        )
        receipt = receipt_result.receipt
        slots["output"] = _pass("output")
        slots["receipt"] = _pass("receipt")
    except DevWavesError as exc:
        if exc.code is ReasonCode.OUTPUT_INVALID:
            slots["output"] = _fail("output", ReasonCode.OUTPUT_INVALID, "invalid-envelope")
            slots["receipt"] = _skip("receipt", "output-invalid")
        else:
            slots["output"] = _pass("output", "envelope-decoded")
            slots["receipt"] = _fail("receipt", ReasonCode.RECEIPT_INVALID, "invalid-receipt")

    permission_abort = False
    if receipt_result is None:
        try:
            permission_abort = permission_abort_from_envelope(
                spec.stdout_path, max_bytes=spec.max_output_bytes,
            )
        except DevWavesError:
            pass

    if permission_abort:
        slots["cost-permission"] = _fail(
            "cost-permission", ReasonCode.PERMISSION_ABORT, "permission-denial",
        )
    elif receipt_result is None:
        slots["cost-permission"] = _skip("cost-permission", "receipt-unavailable")
    elif receipt_result.permission_abort:
        slots["cost-permission"] = _fail(
            "cost-permission", ReasonCode.PERMISSION_ABORT, "permission-denial",
        )
    elif receipt_result.total_cost_usd > spec.per_wave_budget_usd:
        slots["cost-permission"] = _fail(
            "cost-permission", ReasonCode.BUDGET_INVALID, "wave-budget-exceeded",
        )
    else:
        slots["cost-permission"] = _pass("cost-permission")

    after_snapshot: Optional[RepoSnapshot]
    try:
        after_snapshot = snapshot_repo(
            spec.main_worktree,
            timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
        )
        if (after_snapshot.branch != spec.before_snapshot.branch or
                spec.before_snapshot.head_sha != spec.before_main_sha):
            slots["main-state"] = _fail("main-state", ReasonCode.MAIN_MOVED, "branch-or-base")
        elif after_snapshot.main_dirty:
            slots["main-state"] = _fail("main-state", ReasonCode.MAIN_DIRTY, "main-dirty")
        elif after_snapshot.submodule_dirty:
            slots["main-state"] = _fail("main-state", ReasonCode.SUBMODULE_DIRTY, "submodule-dirty")
        else:
            slots["main-state"] = _pass("main-state")
    except (DevWavesError, OSError, subprocess.TimeoutExpired):
        after_snapshot = None
        slots["main-state"] = _fail("main-state", ReasonCode.MAIN_MOVED, "snapshot-failed")

    completed = receipt is not None and receipt.outcome is Outcome.COMPLETED
    if after_snapshot is None or receipt is None:
        slots["ff-chain"] = _skip("ff-chain", "git-or-receipt-unavailable")
        slots["commit-chain"] = _skip("commit-chain", "git-or-receipt-unavailable")
    else:
        try:
            ff = verify_ff_chain(
                spec.repo_root, spec.before_main_sha, after_snapshot.head_sha,
                receipt.landed_commits, completed=completed,
                timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
            )
            if ff.ok:
                slots["ff-chain"] = _pass("ff-chain")
                slots["commit-chain"] = _pass("commit-chain")
            elif ff.reason is ReasonCode.COMMIT_MISMATCH:
                slots["ff-chain"] = _pass("ff-chain", "ancestor-only")
                slots["commit-chain"] = _fail("commit-chain", ff.reason, "sequence-mismatch")
            else:
                slots["ff-chain"] = _fail("ff-chain", ff.reason or ReasonCode.MAIN_NOT_FF, "relation")
                slots["commit-chain"] = _skip("commit-chain", "ff-failed")
        except (DevWavesError, ValueError, subprocess.TimeoutExpired):
            slots["ff-chain"] = _fail("ff-chain", ReasonCode.MAIN_NOT_FF, "git-error")
            slots["commit-chain"] = _skip("commit-chain", "ff-failed")

    wave_tip_before: Optional[str] = None
    try:
        wave_tip_before = branch_tip(
            spec.repo_root, spec.wave_branch,
            timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
        )
        if completed and (
            receipt is None or after_snapshot is None or not receipt.landed_commits or
            after_snapshot.head_sha != receipt.landed_main_sha or
            receipt.landed_main_sha != receipt.landed_commits[-1] or
            wave_tip_before != receipt.landed_main_sha
        ):
            slots["wave-branch"] = _fail("wave-branch", ReasonCode.COMMIT_MISMATCH, "tip-mismatch")
        elif not completed and wave_tip_before != spec.before_main_sha:
            slots["wave-branch"] = _fail(
                "wave-branch", ReasonCode.COMMIT_MISMATCH, "noncompleted-tip-moved",
            )
        else:
            slots["wave-branch"] = _pass("wave-branch")
    except (DevWavesError, ValueError, subprocess.TimeoutExpired):
        slots["wave-branch"] = _fail("wave-branch", ReasonCode.COMMIT_MISMATCH, "tip-unavailable")

    trace = read_child_git_trace(spec.git_trace_path)
    if trace.malformed or trace.push_attempted:
        slots["git-trace"] = _fail("git-trace", ReasonCode.REMOTE_REF_CHANGED, "push-or-malformed")
    else:
        slots["git-trace"] = _pass("git-trace")

    if receipt is None:
        slots["selected-task"] = _skip("selected-task", "receipt-unavailable")
    elif completed and not receipt.selected_task_ids:
        slots["selected-task"] = _fail(
            "selected-task", ReasonCode.WORKLOG_INVALID, "completed-selection-empty",
        )
    elif completed and any(
        task not in spec.before_next_task_ids for task in receipt.selected_task_ids
    ):
        slots["selected-task"] = _fail("selected-task", ReasonCode.WORKLOG_INVALID, "not-in-before-next")
    else:
        slots["selected-task"] = _pass("selected-task")

    if receipt is not None and not completed:
        slots["worklog"] = _pass("worklog", "not-required-for-noncompleted")
    else:
        try:
            worklog_raw = Path(spec.worklog_path).read_bytes()
            worklog_ids = extract_latest_next_action_ids(worklog_raw.decode("utf-8", errors="strict"))
            digest = hashlib.sha256(worklog_raw).hexdigest()
            if (receipt is None or digest == spec.before_worklog_sha256 or
                    worklog_ids != receipt.next_task_ids):
                slots["worklog"] = _fail("worklog", ReasonCode.WORKLOG_INVALID, "conservation")
            else:
                slots["worklog"] = _pass("worklog")
        except (OSError, UnicodeDecodeError, ValueError):
            slots["worklog"] = _fail("worklog", ReasonCode.WORKLOG_INVALID, "parse")

    if receipt is not None and not completed:
        slots["task-run"] = _pass("task-run", "not-required-for-noncompleted")
    elif receipt is None:
        slots["task-run"] = _skip("task-run", "receipt-unavailable")
    else:
        slots["task-run"] = _skip("task-run", "deferred-to-before-sha-validator")

    try:
        leaked = sorted(
            entry.name for entry in os.scandir(spec.handoff_dir)
            if entry.name != "README.md"
        )
        slots["handoff"] = (
            _fail("handoff", ReasonCode.HANDOFF_LEAKED, "active-handoff") if leaked
            else _pass("handoff")
        )
    except OSError:
        slots["handoff"] = _fail("handoff", ReasonCode.HANDOFF_LEAKED, "unreadable")

    try:
        before_trust = trust_root(
            spec.repo_root, spec.before_main_sha,
            timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
        )
        after_sha = after_snapshot.head_sha if after_snapshot else spec.before_main_sha
        after_trust = trust_root(
            spec.repo_root, after_sha,
            timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
        )
        if spec.immutable_digests_before != spec.immutable_digests_after:
            slots["trust-root"] = _fail("trust-root", ReasonCode.CODE_DIRTY, "supervisor-changed")
        elif before_trust != after_trust:
            slots["trust-root"] = _fail("trust-root", ReasonCode.TRUST_ROOT_CHANGED, "digest-changed")
        else:
            slots["trust-root"] = _pass("trust-root")
    except (DevWavesError, OSError, subprocess.TimeoutExpired):
        slots["trust-root"] = _fail("trust-root", ReasonCode.TRUST_ROOT_CHANGED, "unavailable")

    if after_snapshot is None:
        slots["remote-state"] = _fail("remote-state", ReasonCode.REMOTE_REF_CHANGED, "unavailable")
    elif (after_snapshot.remote_refs != spec.before_snapshot.remote_refs or
          after_snapshot.remote_config_sha256 != spec.before_snapshot.remote_config_sha256):
        slots["remote-state"] = _fail("remote-state", ReasonCode.REMOTE_REF_CHANGED, "changed")
    else:
        slots["remote-state"] = _pass("remote-state")

    docs_spec, other_specs = _check_docs_spec(spec.check_specs)
    if docs_spec is None:
        slots["check-docs"] = _fail("check-docs", ReasonCode.CHECK_FAILED, "must-occur-exactly-once")
    passive_failed = any(result.status == "fail" for result in slots.values())
    active_started = False
    if receipt is not None and not completed and not passive_failed:
        slots["check-docs"] = _pass("check-docs", "not-required-for-noncompleted")
        slots["fixed-checks"] = _pass("fixed-checks", "not-required-for-noncompleted")
        slots["active-reobservation"] = _pass(
            "active-reobservation", "not-required-for-noncompleted",
        )
    elif passive_failed:
        slots.setdefault("check-docs", _skip("check-docs", "passive-failure"))
        slots["fixed-checks"] = _skip("fixed-checks", "passive-failure")
        slots["active-reobservation"] = _skip("active-reobservation", "active-not-started")
    else:
        active_started = True
        try:
            with tempfile.TemporaryDirectory(prefix="dev-waves-check-") as temporary:
                validator_checkout = create_isolated_checkout(
                    spec.repo_root, spec.before_main_sha,
                    os.path.join(temporary, "validator"),
                    timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
                )
                assert receipt is not None
                slots["task-run"] = (
                    _pass("task-run") if verify_task_run_finished(
                        spec.task_runs_root, receipt.child_task_run_id,
                        validator_checkout=validator_checkout,
                        total_deadline_boottime_ns=spec.total_deadline_boottime_ns,
                    ) else _fail(
                        "task-run", ReasonCode.TASK_RUN_INCOMPLETE,
                        "not-completed-by-before-sha-validator",
                    )
                )
                checkout = create_isolated_checkout(
                    spec.repo_root, after_snapshot.head_sha, os.path.join(temporary, "repo"),
                    timeout_s=_remaining_s(spec.total_deadline_boottime_ns, 30),
                )
                docs_result = run_check_specs(
                    (docs_spec,), checkout,
                    total_deadline_boottime_ns=spec.total_deadline_boottime_ns,
                )[0]
                slots["check-docs"] = InvariantResult(
                    "check-docs", docs_result.status, docs_result.reason, docs_result.detail,
                )
                other_results = run_check_specs(
                    other_specs, checkout,
                    total_deadline_boottime_ns=spec.total_deadline_boottime_ns,
                )
                failed = [result for result in other_results if result.status == "fail"]
                slots["fixed-checks"] = (
                    _fail(
                        "fixed-checks",
                        failed[0].reason or ReasonCode.CHECK_FAILED,
                        failed[0].name,
                    )
                    if failed else _pass("fixed-checks")
                )
        except (DevWavesError, OSError, subprocess.TimeoutExpired, ValueError):
            slots.setdefault("check-docs", _fail("check-docs", ReasonCode.CHECK_FAILED, "checkout-or-timeout"))
            slots["fixed-checks"] = _fail("fixed-checks", ReasonCode.CHECK_FAILED, "checkout-or-timeout")
        slots["active-reobservation"] = _active_reobserve(
            spec, after_snapshot, wave_tip_before,
        )

    findings = tuple(slots[name] for name in _ORDER)
    permission = slots.get("cost-permission")
    first = (
        permission if permission is not None and
        permission.reason is ReasonCode.PERMISSION_ABORT else
        next((finding for finding in findings if finding.status == "fail"), None)
    )
    return VerificationReport(
        first is None, first.reason if first else None, findings, receipt,
        after_snapshot, active_started,
    )


__all__ = [
    "CheckSpec", "InvariantResult", "VerificationInput", "VerificationReport",
    "extract_latest_next_action_ids", "run_check_specs",
    "verify_task_run_finished", "verify_wave",
]
