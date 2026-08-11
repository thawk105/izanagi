#!/usr/bin/env python3
"""Mutation harness の N-shard fan-out 専用 driver。

この tool は汎用の並行投入 gate ではない。親 spec から単位 A の契約で
導出した shard 群だけを、事前計測 receipt と login headroom reservation の
両方が一致するときに起動する。
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import dataclasses
import datetime as dt
import getpass
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from mutation_fanout_contract import (
    GROUP_SCHEMA,
    FanoutContractError,
    canonical_json_bytes,
    derive_split,
    merge_group,
    write_split,
)


ADMISSION_SCHEMA = "izanagi-dev-wave-mutation-fanout-admission/v1"
DRIVER_SCHEMA = "izanagi-dev-wave-mutation-fanout-driver/v1"
CANCELLATION_SCHEMA = "izanagi-dev-wave-mutation-fanout-cancellation/v1"
CONTAINER_NAME = ".izanagi-mutation-worktree"
CHECKOUT_NAME = "repo"
MIN_CERTIFICATION_REPETITIONS = 3
CERTIFICATION_MIN_MARGIN_BYTES = 128 * 1024**2
INFRA_RC = 2
LAUNCHER_FAILURE_RC = 125
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_REQUEST_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")

_ADMISSION_FIELDS = {
    "schema",
    "measured_at",
    "commit",
    "parent_spec_sha256",
    "assignment_sha256",
    "shard_count",
    "runner_argv",
    "input_bytes",
    "input_count",
    "memory_max_bytes",
    "repetitions",
    "memory_current_peak_bytes",
    "certified_peak_bytes",
}


class FanoutDriverError(RuntimeError):
    """投入前または driver 管理面を証明できないときの停止。"""


@dataclasses.dataclass(frozen=True)
class FanoutConfig:
    source_repo: Path
    commit: str
    parent_spec: Path
    expected_parent_sha256: str
    shard_count: int
    group_root: Path
    admission_receipt: Path
    runner_argv: tuple[str, ...]
    poll_interval_s: float = 0.05
    barrier_timeout_s: float = 120.0


@dataclasses.dataclass
class Child:
    index: int
    shard_id: str
    process: subprocess.Popen[Any]
    pid: int
    starttime: int
    pgid: int
    log_stream: Any
    rc_path: Path
    done_path: Path
    rc: int | None = None


@dataclasses.dataclass
class SignalLatch:
    signum: int | None = None


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FanoutDriverError(f"{label} が object でない")
    actual = set(value)
    if actual != fields:
        raise FanoutDriverError(
            f"{label} の key が不一致: missing={sorted(fields - actual)}, "
            f"unknown={sorted(actual - fields)}"
        )
    return value


def _strict_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FanoutDriverError(f"{label} が正の int でない")
    return value


def _read_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink():
        raise FanoutDriverError(f"{label} に symlink を指定してはならない")
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FanoutDriverError(f"{label} を読めない: {exc}") from exc
    if not isinstance(value, dict):
        raise FanoutDriverError(f"{label} root が object でない")
    return value, payload


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _create_only(path: Path, payload: bytes, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError as exc:
        raise FanoutDriverError(f"{label} を create-only で作れない: {exc}") from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    _sync_directory(path.parent)


def _atomic_replace(path: Path, payload: bytes, label: str) -> None:
    if path.is_symlink():
        raise FanoutDriverError(f"{label} の置換先が symlink")
    nonce = f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}"
    temporary = path.parent / nonce
    _create_only(temporary, payload, f"{label} temporary")
    try:
        os.replace(temporary, path)
        _sync_directory(path.parent)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def _write_json_create_only(path: Path, value: Any, label: str) -> None:
    _create_only(path, canonical_json_bytes(value), label)


def _write_json_replace(path: Path, value: Any, label: str) -> None:
    _atomic_replace(path, canonical_json_bytes(value), label)


def _git(source: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(source), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _resolved_commit(source: Path, commit: str) -> str:
    result = _git(source, "rev-parse", "--verify", f"{commit}^{{commit}}")
    value = result.stdout.strip()
    if result.returncode != 0 or _COMMIT_RE.fullmatch(value) is None:
        raise FanoutDriverError(f"commit を full object ID へ解決できない: {result.stderr.strip()}")
    return value


def _worktree_snapshot(source: Path) -> tuple[tuple[str, ...], str]:
    result = _git(source, "worktree", "list", "--porcelain")
    if result.returncode != 0:
        raise FanoutDriverError(
            f"git worktree list --porcelain に失敗: {result.stderr.strip()}"
        )
    roots: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            roots.append(str(Path(line[9:]).resolve(strict=False)))
    if not roots:
        raise FanoutDriverError("registered worktree 一覧が空")
    return tuple(roots), result.stdout


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_group_root(path: Path, registered: Sequence[str]) -> Path:
    if path.exists() or path.is_symlink():
        raise FanoutDriverError("--group-root は fresh path でなければならない")
    try:
        parent = path.parent.resolve(strict=True)
    except OSError as exc:
        raise FanoutDriverError(f"--group-root の親を解決できない: {exc}") from exc
    root = parent / path.name
    for raw in registered:
        worktree = Path(raw)
        if _within(root, worktree) or _within(worktree, root):
            raise FanoutDriverError(
                "--group-root は親 repo と全 registered worktree の外でなければならない"
            )
    return root


def _validate_external_file(path: Path, registered: Sequence[str], label: str) -> Path:
    if path.is_symlink():
        raise FanoutDriverError(f"{label} に symlink を指定してはならない")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise FanoutDriverError(f"{label} を解決できない: {exc}") from exc
    if not resolved.is_file():
        raise FanoutDriverError(f"{label} が通常 file でない")
    if any(_within(resolved, Path(raw)) for raw in registered):
        raise FanoutDriverError(f"{label} は全 registered worktree の外でなければならない")
    return resolved


def _input_binding(
    assignment: Mapping[str, Any], shard_payloads: Sequence[bytes]
) -> tuple[int, int]:
    mutation_count = sum(len(shard["mutation_ids"]) for shard in assignment["shards"])
    return sum(len(payload) for payload in shard_payloads), mutation_count


def validate_admission_receipt(
    value: Any,
    *,
    commit: str,
    parent_spec_sha256: str,
    assignment_sha256: str,
    shard_count: int,
    runner_argv: Sequence[str],
    input_bytes: int,
    input_count: int,
    memory_max_bytes: int,
) -> int:
    """exact-N cgroup peak receipt を現在の投入 binding と照合する。"""

    receipt = _exact_object(value, _ADMISSION_FIELDS, "admission receipt")
    if receipt["schema"] != ADMISSION_SCHEMA:
        raise FanoutDriverError("admission receipt schema が未知")
    measured_at = receipt["measured_at"]
    if not isinstance(measured_at, str):
        raise FanoutDriverError("admission receipt.measured_at が文字列でない")
    try:
        parsed_date = dt.datetime.fromisoformat(measured_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FanoutDriverError("admission receipt.measured_at が ISO-8601 でない") from exc
    if parsed_date.tzinfo is None:
        raise FanoutDriverError("admission receipt.measured_at に timezone がない")
    exact = {
        "commit": commit,
        "parent_spec_sha256": parent_spec_sha256,
        "assignment_sha256": assignment_sha256,
        "shard_count": shard_count,
        "runner_argv": list(runner_argv),
        "input_bytes": input_bytes,
        "input_count": input_count,
        "memory_max_bytes": memory_max_bytes,
    }
    for key, expected in exact.items():
        if receipt[key] != expected:
            raise FanoutDriverError(f"admission receipt.{key} が現在の投入 binding と不一致")
    repetitions = _strict_positive_int(receipt["repetitions"], "admission repetitions")
    peaks = receipt["memory_current_peak_bytes"]
    if (
        not isinstance(peaks, list)
        or len(peaks) != repetitions
        or repetitions < MIN_CERTIFICATION_REPETITIONS
    ):
        raise FanoutDriverError("admission receipt は memory.current の3反復以上を要する")
    measured_peaks = [
        _strict_positive_int(item, f"memory_current_peak_bytes[{index}]")
        for index, item in enumerate(peaks)
    ]
    observed_peak = max(measured_peaks)
    margin = max((observed_peak + 3) // 4, CERTIFICATION_MIN_MARGIN_BYTES)
    certified = _strict_positive_int(
        receipt["certified_peak_bytes"], "certified_peak_bytes"
    )
    if certified != observed_peak + margin:
        raise FanoutDriverError(
            "certified_peak_bytes が max(25%, 128 MiB) margin 付き peak と不一致"
        )
    return certified


def _expected_invocations(assignment: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    ordinal = 0
    for shard in assignment["shards"]:
        for phase, mutation_id in (
            ("collection", None),
            ("baseline", None),
            *(("mutation", item) for item in shard["mutation_ids"]),
        ):
            ordinal += 1
            result.append(
                {
                    "ordinal": ordinal,
                    "shard_id": shard["shard_id"],
                    "phase": phase,
                    "mutation_id": mutation_id,
                }
            )
    return result


def _shard_documents(
    root: Path,
    assignment: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    group_shards: list[dict[str, Any]] = []
    driver_shards: list[dict[str, Any]] = []
    all_resources: list[Path] = []
    for shard in assignment["shards"]:
        shard_id = shard["shard_id"]
        runtime = root / "runtime" / shard_id
        scratch = runtime / "scratch"
        ledger = runtime / "ledger.json"
        attempt = runtime / "attempts.json"
        receipt = Path(f"{ledger}.wrapper-receipt.json")
        evidence = Path(f"{ledger}.dispatch-evidence")
        lock = Path(f"{ledger}.lock")
        container = scratch / CONTAINER_NAME
        checkout = container / CHECKOUT_NAME
        spec = root / shard["relative_spec_path"]
        log = runtime / "launcher.log"
        rc_path = runtime / "rc.json"
        done_path = runtime / "done"
        resources = (scratch, ledger, attempt, receipt, evidence, lock, log, rc_path, done_path)
        all_resources.extend(resources)
        group_shards.append(
            {
                "index": shard["index"],
                "shard_id": shard_id,
                "spec_path": str(spec),
                "ledger_path": str(ledger),
                "wrapper_receipt_path": str(receipt),
                "attempt_path": str(attempt),
                "wrapper_attempt_ordinal": 1,
                "wrapper_rc": None,
                "expected_paths": {
                    "scratch_root": str(scratch),
                    "container_path": str(container),
                    "lock_path": str(lock),
                    "runner_entrypoint_path": str(checkout / "tools" / "run_tests.py"),
                    "dispatch_entrypoint_path": str(
                        checkout / "tools" / "pegasus" / "dispatch_compute.py"
                    ),
                    "tool_path": str(checkout / "tools" / "mutation_harness.py"),
                },
            }
        )
        driver_shards.append(
            {
                "index": shard["index"],
                "shard_id": shard_id,
                "mutation_ids": list(shard["mutation_ids"]),
                "expected_request_count": len(shard["mutation_ids"]) + 2,
                "pid": None,
                "starttime": None,
                "pgid": None,
                "log_path": str(log),
                "rc_path": str(rc_path),
                "done_path": str(done_path),
                "rc": None,
            }
        )
    if len({str(path) for path in all_resources}) != len(all_resources):
        raise FanoutDriverError("shard resource path が重複")
    return group_shards, driver_shards


def _wrapper_argv(
    config: FanoutConfig,
    *,
    commit: str,
    assignment_shard: Mapping[str, Any],
    group_shard: Mapping[str, Any],
) -> list[str]:
    expected = group_shard["expected_paths"]
    return [
        sys.executable,
        str(config.source_repo.resolve() / "tools" / "mutation_worktree.py"),
        "--source-repo",
        str(config.source_repo.resolve()),
        "--commit",
        commit,
        "--scratch-root",
        expected["scratch_root"],
        "--spec",
        group_shard["spec_path"],
        "--expected-spec-sha256",
        assignment_shard["shard_spec_sha256"],
        "--out",
        group_shard["ledger_path"],
        "--attempt-out",
        group_shard["attempt_path"],
        "--wrapper-attempt",
        "1",
        "--runner-mode",
        "dispatch",
        "--detached",
        "--",
        *config.runner_argv,
    ]


def _process_starttime(pid: int) -> int | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        close = raw.rfind(")")
        if close < 0:
            return None
        return int(raw[close + 2 :].split()[19])
    except (OSError, UnicodeDecodeError, ValueError, IndexError):
        return None


def _process_identity_alive(pid: int, starttime: int) -> bool:
    return _process_starttime(pid) == starttime


def _mapped_returncode(returncode: int) -> int:
    return 128 + (-returncode) if returncode < 0 else returncode


def _install_signal_handlers(latch: SignalLatch) -> Iterator[None]:
    @contextlib.contextmanager
    def scope() -> Iterator[None]:
        previous: dict[int, Any] = {}

        def handle(signum: int, _frame: Any) -> None:
            if latch.signum is None:
                latch.signum = signum

        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handle)
        try:
            yield
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)

    return scope()


def _forward_signal(children: Sequence[Child], signum: int) -> None:
    for child in children:
        if child.rc is not None or not _process_identity_alive(child.pid, child.starttime):
            continue
        try:
            os.killpg(child.pgid, signum)
        except ProcessLookupError:
            pass


def _wait_for_children(
    children: Sequence[Child],
    *,
    report: dict[str, Any],
    report_path: Path,
    group: dict[str, Any],
    group_path: Path,
    latch: SignalLatch,
    poll_interval_s: float,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """全 producer を driver 自身のこの 1 ループだけで回収する。"""

    forwarded = False
    remaining = len(children)
    while remaining:
        if latch.signum is not None and not forwarded:
            _forward_signal(children, latch.signum)
            forwarded = True
        progress = False
        for child in children:
            if child.rc is not None:
                continue
            raw_rc = child.process.poll()
            if raw_rc is None:
                continue
            child.rc = _mapped_returncode(raw_rc)
            child.log_stream.close()
            rc_document = {
                "pid": child.pid,
                "starttime": child.starttime,
                "process_returncode": raw_rc,
                "rc": child.rc,
                "terminal": child.rc in {0, 1},
            }
            _write_json_create_only(child.rc_path, rc_document, f"{child.shard_id} rc")
            _create_only(child.done_path, b"done\n", f"{child.shard_id} done")
            report["shards"][child.index]["rc"] = child.rc
            group["shards"][child.index]["wrapper_rc"] = child.rc
            _write_json_replace(report_path, report, "driver report")
            remaining -= 1
            progress = True
        if remaining and not progress:
            sleep(poll_interval_s)
    _write_json_replace(group_path, group, "final group manifest")


def _set_parent_death_signal(signum: int) -> None:
    if sys.platform != "linux":
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signum, 0, 0, 0) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def _launcher_main(args: argparse.Namespace) -> int:
    try:
        _set_parent_death_signal(signal.SIGTERM)
        if (
            os.getppid() != args.parent_pid
            or not _process_identity_alive(args.parent_pid, args.parent_starttime)
        ):
            return LAUNCHER_FAILURE_RC
        deadline = time.monotonic() + args.barrier_timeout
        barrier = args.barrier
        while not barrier.exists():
            if (
                not _process_identity_alive(args.parent_pid, args.parent_starttime)
                or time.monotonic() >= deadline
            ):
                return LAUNCHER_FAILURE_RC
            time.sleep(0.02)
        command = list(args.command)
        if command and command[0] == "--":
            command.pop(0)
        if not command:
            return LAUNCHER_FAILURE_RC
        os.execv(command[0], command)
    except BaseException as exc:
        print(f"fan-out launcher failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return LAUNCHER_FAILURE_RC
    return LAUNCHER_FAILURE_RC


def _parse_attempt_claims(group: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for shard in group.get("shards", []):
        attempt_path = Path(str(shard.get("attempt_path", "")))
        try:
            sidecar = json.loads(attempt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        attempts = sidecar.get("attempts") if isinstance(sidecar, dict) else None
        if not isinstance(attempts, list):
            continue
        for attempt in attempts:
            request = attempt.get("request") if isinstance(attempt, dict) else None
            if not isinstance(request, dict):
                continue
            claims.append(
                {
                    "shard_id": shard.get("shard_id"),
                    "run_attempt_ordinal": attempt.get("run_attempt_ordinal"),
                    "request_id": request.get("request_id"),
                    "receipt_path": request.get("receipt_path"),
                    "wrapper_receipt_path": shard.get("wrapper_receipt_path"),
                }
            )
    return claims


def _effective_receipt_path(claim: Mapping[str, Any]) -> Path:
    raw = claim.get("receipt_path")
    if not isinstance(raw, str):
        raise FanoutDriverError("attempt request receipt path が不明")
    original_receipt = Path(raw)
    if original_receipt.is_file() and not original_receipt.is_symlink():
        return original_receipt.resolve(strict=True)
    wrapper_raw = claim.get("wrapper_receipt_path")
    if not isinstance(wrapper_raw, str):
        raise FanoutDriverError("wrapper receipt path が不明")
    wrapper, _ = _read_json(Path(wrapper_raw), "wrapper receipt")
    evidence = wrapper.get("dispatch_evidence")
    if not isinstance(evidence, dict):
        raise FanoutDriverError("wrapper receipt の dispatch_evidence が不明")
    try:
        original = Path(evidence["original_path"])
        relocated = Path(evidence["relocated_path"])
        relative = original_receipt.relative_to(original)
        effective = (relocated / relative).resolve(strict=True)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise FanoutDriverError("receipt の evidence prefix remap に失敗") from exc
    if effective.is_symlink() or not effective.is_file():
        raise FanoutDriverError("relocated receipt が通常 file でない")
    return effective


def _scheduler_run(command: Sequence[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )


def _qstat_identity(output: str, request_id: str) -> tuple[str | None, str | None]:
    job_id: str | None = None
    owner: str | None = None
    state: str | None = None
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Job Id:"):
            job_id = stripped.partition(":")[2].strip()
        elif stripped.startswith("Job_Owner ="):
            owner = stripped.partition("=")[2].strip().partition("@")[0]
        elif stripped.startswith("job_state ="):
            raw_state = stripped.partition("=")[2].strip()
            state = {"Q": "QUE", "H": "HLD", "R": "RUN"}.get(raw_state, raw_state)
    if job_id != request_id:
        return None, None
    return state, owner


def inspect_or_cancel_owned_requests(
    group: Mapping[str, Any],
    *,
    cwd: Path,
    cancel: bool,
    expected_owner: str | None = None,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = _scheduler_run,
) -> list[dict[str, Any]]:
    """receipt と fresh qstat の双方が束縛した QUE/HLD だけを取消す。"""

    owner = getpass.getuser() if expected_owner is None else expected_owner
    claims = _parse_attempt_claims(group)
    counts = Counter(claim.get("request_id") for claim in claims)
    actions: list[dict[str, Any]] = []
    for claim in claims:
        request_id = claim.get("request_id")
        action = dict(claim)
        action.update({"qstat_attempted": False, "qdel_attempted": False})
        if (
            not isinstance(request_id, str)
            or _REQUEST_ID_RE.fullmatch(request_id) is None
            or counts[request_id] != 1
        ):
            action["reason"] = "request-id-missing-malformed-or-ambiguous"
            actions.append(action)
            continue
        try:
            receipt_path = _effective_receipt_path(claim)
            receipt, _ = _read_json(receipt_path, "dispatch receipt")
        except FanoutDriverError as exc:
            action["reason"] = f"receipt-unavailable: {exc}"
            actions.append(action)
            continue
        if receipt.get("request_id") != request_id:
            action["reason"] = "receipt-request-id-mismatch"
            actions.append(action)
            continue
        action["receipt_path_effective"] = str(receipt_path)
        try:
            qstat = run_command(["qstat", "-f", request_id], cwd=cwd)
        except BaseException as exc:
            action.update(
                {
                    "qstat_attempted": True,
                    "reason": f"qstat-exception: {type(exc).__name__}: {exc}",
                }
            )
            actions.append(action)
            continue
        action.update(
            {
                "qstat_attempted": True,
                "qstat_rc": qstat.returncode,
                "qstat_stdout": (qstat.stdout or "")[-65536:],
                "qstat_stderr": (qstat.stderr or "")[-65536:],
            }
        )
        if qstat.returncode != 0:
            action["reason"] = "request-not-visible"
            actions.append(action)
            continue
        state, observed_owner = _qstat_identity(qstat.stdout or "", request_id)
        action.update({"scheduler_state": state, "observed_owner": observed_owner})
        if state not in {"QUE", "HLD"}:
            action["reason"] = "state-not-cancellable"
            actions.append(action)
            continue
        if observed_owner is None or observed_owner != owner:
            action["reason"] = "owner-unknown-or-mismatch"
            actions.append(action)
            continue
        if not cancel:
            action["reason"] = "report-only"
            actions.append(action)
            continue
        try:
            qdel = run_command(["qdel", request_id], cwd=cwd)
        except BaseException as exc:
            action.update(
                {
                    "qdel_attempted": True,
                    "reason": f"qdel-exception: {type(exc).__name__}: {exc}",
                }
            )
        else:
            action.update(
                {
                    "qdel_attempted": True,
                    "qdel_rc": qdel.returncode,
                    "qdel_stdout": (qdel.stdout or "")[-65536:],
                    "qdel_stderr": (qdel.stderr or "")[-65536:],
                    "reason": "qdel-requested" if qdel.returncode == 0 else "qdel-failed",
                }
            )
        actions.append(action)
    return actions


def _reservation_factory(estimate: int, *, scope_cgroup: Path) -> Any:
    from orchestrator.campaign import login_headroom

    return login_headroom.reserve(estimate, scope_cgroup=scope_cgroup)


def _headroom_observation() -> Any:
    from orchestrator.campaign import login_headroom

    return login_headroom.login_headroom()


def _preserved_containers(group: Mapping[str, Any]) -> list[dict[str, Any]]:
    preserved: list[dict[str, Any]] = []
    for shard in group["shards"]:
        container = Path(shard["expected_paths"]["container_path"])
        receipt_value: bool | None = None
        receipt_path = Path(shard["wrapper_receipt_path"])
        try:
            receipt, _ = _read_json(receipt_path, "wrapper receipt")
            raw = receipt.get("container_preserved")
            receipt_value = raw if isinstance(raw, bool) else None
        except FanoutDriverError:
            pass
        if container.exists() or receipt_value is True:
            preserved.append(
                {
                    "shard_id": shard["shard_id"],
                    "container_path": str(container),
                    "exists": container.exists(),
                    "wrapper_receipt_container_preserved": receipt_value,
                    "owner": "human-direction-required",
                }
            )
    return preserved


def run_fanout(
    config: FanoutConfig,
    *,
    observation: Callable[[], Any] = _headroom_observation,
    reserve_factory: Callable[..., Any] = _reservation_factory,
    popen_factory: Callable[..., subprocess.Popen[Any]] = subprocess.Popen,
    snapshot: Callable[[Path], tuple[tuple[str, ...], str]] = _worktree_snapshot,
    merger: Callable[..., dict[str, Any]] = merge_group,
    scheduler_run: Callable[..., subprocess.CompletedProcess[str]] = _scheduler_run,
) -> int:
    """fresh group を計画し、exact-N admission 下で一度だけ投入する。"""

    source = config.source_repo.resolve(strict=True)
    initial_roots, initial_porcelain = snapshot(source)
    root = _validate_group_root(config.group_root, initial_roots)
    admission_path = _validate_external_file(
        config.admission_receipt, initial_roots, "--admission-receipt"
    )
    if not config.runner_argv:
        raise FanoutDriverError("runner argv を -- の後へ指定する必要がある")
    if config.poll_interval_s <= 0 or config.barrier_timeout_s <= 0:
        raise FanoutDriverError("poll/barrier timeout は正でなければならない")
    commit = _resolved_commit(source, config.commit)
    parent_bytes = config.parent_spec.read_bytes()
    assignment, shard_payloads = derive_split(
        parent_bytes,
        expected_parent_sha256=config.expected_parent_sha256,
        shard_count=config.shard_count,
    )
    assignment_bytes = canonical_json_bytes(assignment)
    assignment_sha256 = _sha256(assignment_bytes)
    input_bytes, input_count = _input_binding(assignment, shard_payloads)

    root.mkdir(mode=0o700)
    write_split(
        config.parent_spec,
        expected_parent_sha256=config.expected_parent_sha256,
        shard_count=config.shard_count,
        group_root=root,
    )
    group_shards, driver_shards = _shard_documents(root, assignment)
    for shard in group_shards:
        Path(shard["expected_paths"]["scratch_root"]).mkdir(parents=True, mode=0o700)
    group = {
        "schema": GROUP_SCHEMA,
        "parent_spec_sha256": config.expected_parent_sha256,
        "assignment_sha256": assignment_sha256,
        "shards": group_shards,
    }
    group_path = root / "group.json"
    _write_json_create_only(group_path, group, "initial group manifest")
    expected_invocations = _expected_invocations(assignment)
    expected_invocation_count = input_count + 2 * config.shard_count
    if len(expected_invocations) != expected_invocation_count:
        raise FanoutDriverError("期待 invocation 集合の件数が変異数 + 2N と不一致")
    report = {
        "schema": DRIVER_SCHEMA,
        "state": "planned",
        "source_repo": str(source),
        "commit": commit,
        "parent_spec_path": str(config.parent_spec.resolve()),
        "parent_spec_sha256": config.expected_parent_sha256,
        "assignment_path": str((root / "assignment.json").resolve()),
        "assignment_sha256": assignment_sha256,
        "group_manifest_path": str(group_path),
        "shard_count": config.shard_count,
        "expected_invocation_count": expected_invocation_count,
        "expected_invocations": expected_invocations,
        "runner_argv": list(config.runner_argv),
        "input_bytes": input_bytes,
        "admission_receipt_path": str(admission_path),
        "admission_receipt_sha256": None,
        "certified_peak_bytes": None,
        "admission": {"decision": "unknown", "reason": None},
        "initial_worktree_registry": list(initial_roots),
        "initial_worktree_porcelain": initial_porcelain,
        "final_worktree_registry": None,
        "final_worktree_porcelain": None,
        "unexpected_worktrees": [],
        "missing_initial_worktrees": [],
        "shards": driver_shards,
        "signal": None,
        "preserved_containers": [],
        "remote_jobs": [],
        "merge_index_path": str(root / "merge-index.json"),
        "result_rc": None,
        "failure": None,
    }
    report_path = root / "driver-report.json"
    _write_json_create_only(report_path, report, "initial driver report")

    def stop(reason: str) -> int:
        report["state"] = "stopped"
        report["failure"] = reason
        report["result_rc"] = INFRA_RC
        try:
            final_roots, final_porcelain = snapshot(source)
            report["final_worktree_registry"] = list(final_roots)
            report["final_worktree_porcelain"] = final_porcelain
            report["unexpected_worktrees"] = sorted(set(final_roots) - set(initial_roots))
            report["missing_initial_worktrees"] = sorted(set(initial_roots) - set(final_roots))
        except FanoutDriverError as exc:
            report["failure"] += f"; final worktree registry unreadable: {exc}"
        _write_json_replace(report_path, report, "stopped driver report")
        return INFRA_RC

    try:
        receipt, receipt_bytes = _read_json(admission_path, "admission receipt")
        observed = observation()
        if observed is None:
            return stop("login cgroup memory.current/memory.max を観測できない")
        certified_peak = validate_admission_receipt(
            receipt,
            commit=commit,
            parent_spec_sha256=config.expected_parent_sha256,
            assignment_sha256=assignment_sha256,
            shard_count=config.shard_count,
            runner_argv=config.runner_argv,
            input_bytes=input_bytes,
            input_count=input_count,
            memory_max_bytes=observed.memory_max_bytes,
        )
        report["admission_receipt_sha256"] = _sha256(receipt_bytes)
        report["certified_peak_bytes"] = certified_peak
    except (FanoutDriverError, OSError) as exc:
        return stop(f"admission unknown: {exc}")

    latch = SignalLatch()
    children: list[Child] = []
    barrier = root / "start.barrier"
    parent_starttime = _process_starttime(os.getpid())
    if parent_starttime is None:
        return stop("driver PID starttime を取得できない")
    with reserve_factory(certified_peak, scope_cgroup=observed.cgroup_path) as decision:
        admission_value = getattr(decision[0], "value", decision[0])
        report["admission"] = {"decision": str(admission_value), "reason": decision[1]}
        if admission_value != "local":
            return stop(f"login_headroom.reserve が投入を拒否: {decision[1]}")
        report["state"] = "launching"
        _write_json_replace(report_path, report, "launching driver report")
        try:
            with _install_signal_handlers(latch):
                for assignment_shard, group_shard in zip(
                    assignment["shards"], group["shards"], strict=True
                ):
                    index = assignment_shard["index"]
                    runtime = root / "runtime" / assignment_shard["shard_id"]
                    log_path = Path(report["shards"][index]["log_path"])
                    log_stream = log_path.open("xb")
                    wrapper = _wrapper_argv(
                        config,
                        commit=commit,
                        assignment_shard=assignment_shard,
                        group_shard=group_shard,
                    )
                    launcher = [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "_launch",
                        "--barrier",
                        str(barrier),
                        "--barrier-timeout",
                        str(config.barrier_timeout_s),
                        "--parent-pid",
                        str(os.getpid()),
                        "--parent-starttime",
                        str(parent_starttime),
                        "--",
                        *wrapper,
                    ]
                    try:
                        process = popen_factory(
                            launcher,
                            stdin=subprocess.DEVNULL,
                            stdout=log_stream,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                            shell=False,
                        )
                    except BaseException:
                        log_stream.close()
                        raise
                    starttime = _process_starttime(process.pid)
                    if starttime is None:
                        try:
                            os.killpg(process.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                        raise FanoutDriverError(
                            f"{assignment_shard['shard_id']} PID starttime を取得できない"
                        )
                    child = Child(
                        index=index,
                        shard_id=assignment_shard["shard_id"],
                        process=process,
                        pid=process.pid,
                        starttime=starttime,
                        pgid=process.pid,
                        log_stream=log_stream,
                        rc_path=Path(report["shards"][index]["rc_path"]),
                        done_path=Path(report["shards"][index]["done_path"]),
                    )
                    children.append(child)
                    report["shards"][index].update(
                        {"pid": child.pid, "starttime": starttime, "pgid": child.pgid}
                    )
                report["state"] = "running"
                _write_json_replace(report_path, report, "running driver report")
                _create_only(barrier, b"go\n", "start barrier")
                _wait_for_children(
                    children,
                    report=report,
                    report_path=report_path,
                    group=group,
                    group_path=group_path,
                    latch=latch,
                    poll_interval_s=config.poll_interval_s,
                )
        except BaseException as exc:
            if latch.signum is None:
                latch.signum = signal.SIGTERM
            _forward_signal(children, latch.signum)
            for child in children:
                raw_rc = child.process.returncode
                if child.rc is None:
                    try:
                        raw_rc = child.process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(child.pgid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        raw_rc = child.process.wait()
                    except BaseException:
                        raw_rc = LAUNCHER_FAILURE_RC
                    child.rc = _mapped_returncode(raw_rc)
                if raw_rc is None:
                    raw_rc = child.rc
                if not child.log_stream.closed:
                    child.log_stream.close()
                if not child.rc_path.exists():
                    _write_json_create_only(
                        child.rc_path,
                        {
                            "pid": child.pid,
                            "starttime": child.starttime,
                            "process_returncode": raw_rc,
                            "rc": child.rc,
                            "terminal": child.rc in {0, 1},
                        },
                        f"{child.shard_id} failed rc",
                    )
                if not child.done_path.exists():
                    _create_only(child.done_path, b"done\n", f"{child.shard_id} failed done")
                report["shards"][child.index]["rc"] = child.rc
                group["shards"][child.index]["wrapper_rc"] = child.rc
            _write_json_replace(group_path, group, "failed group manifest")
            report["failure"] = f"driver launch/wait failure: {type(exc).__name__}: {exc}"

    report["signal"] = latch.signum
    report["preserved_containers"] = _preserved_containers(group)
    terminal = len(children) == config.shard_count and all(
        child.rc in {0, 1} for child in children
    )
    final_roots: tuple[str, ...] = ()
    registry_clean = False
    try:
        final_roots, final_porcelain = snapshot(source)
        report["final_worktree_registry"] = list(final_roots)
        report["final_worktree_porcelain"] = final_porcelain
        report["unexpected_worktrees"] = sorted(set(final_roots) - set(initial_roots))
        report["missing_initial_worktrees"] = sorted(set(initial_roots) - set(final_roots))
        registry_clean = Counter(final_roots) == Counter(initial_roots)
    except FanoutDriverError as exc:
        report["failure"] = (
            f"{report['failure']}; " if report["failure"] else ""
        ) + f"final worktree registry unreadable: {exc}"
    if not terminal or latch.signum is not None or not registry_clean:
        report["remote_jobs"] = inspect_or_cancel_owned_requests(
            group,
            cwd=source,
            cancel=latch.signum is not None,
            run_command=scheduler_run,
        )
        report["state"] = "stopped"
        report["result_rc"] = 128 + latch.signum if latch.signum is not None else INFRA_RC
        if not registry_clean:
            residue = report["unexpected_worktrees"] or report["missing_initial_worktrees"]
            report["failure"] = (
                f"{report['failure']}; " if report["failure"] else ""
            ) + f"worktree registry residue/change: {residue}"
        elif not terminal and report["failure"] is None:
            report["failure"] = "nonterminal shard rc; successful shards were not retried"
        _write_json_replace(report_path, report, "terminal failure driver report")
        return int(report["result_rc"])

    try:
        index = merger(
            config.parent_spec,
            expected_parent_sha256=config.expected_parent_sha256,
            assignment_path=root / "assignment.json",
            group_manifest_path=group_path,
            output_path=root / "merge-index.json",
        )
    except (FanoutContractError, OSError) as exc:
        report["state"] = "stopped"
        report["failure"] = f"fan-out merge rejected: {exc}"
        report["result_rc"] = INFRA_RC
        report["remote_jobs"] = inspect_or_cancel_owned_requests(
            group,
            cwd=source,
            cancel=False,
            run_command=scheduler_run,
        )
    else:
        result_rc = index.get("result_rc")
        merge_path = root / "merge-index.json"
        if merge_path.is_symlink() or not merge_path.is_file():
            report["state"] = "stopped"
            report["failure"] = "merge が create-only index を生成しなかった"
            report["result_rc"] = INFRA_RC
        elif isinstance(result_rc, bool) or result_rc not in {0, 1}:
            report["state"] = "stopped"
            report["failure"] = "merge result_rc が terminal rc でない"
            report["result_rc"] = INFRA_RC
        else:
            report["state"] = "finished"
            report["result_rc"] = result_rc
    _write_json_replace(report_path, report, "final driver report")
    return int(report["result_rc"])


def cancel_group(
    group_manifest: Path,
    *,
    output_path: Path,
    cwd: Path,
    expected_owner: str | None = None,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = _scheduler_run,
) -> dict[str, Any]:
    group, _ = _read_json(group_manifest, "group manifest")
    actions = inspect_or_cancel_owned_requests(
        group,
        cwd=cwd,
        cancel=True,
        expected_owner=expected_owner,
        run_command=run_command,
    )
    result = {"schema": CANCELLATION_SCHEMA, "group_manifest": str(group_manifest), "actions": actions}
    _write_json_create_only(output_path, result, "cancellation receipt")
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--source-repo", required=True, type=Path)
    run.add_argument("--commit", required=True)
    run.add_argument("--parent-spec", required=True, type=Path)
    run.add_argument("--expected-parent-sha256", required=True)
    run.add_argument("--shard-count", required=True, type=int)
    run.add_argument("--group-root", required=True, type=Path)
    run.add_argument("--admission-receipt", required=True, type=Path)
    run.add_argument("--poll-interval", type=float, default=0.05)
    run.add_argument("--barrier-timeout", type=float, default=120.0)
    run.add_argument("command", nargs=argparse.REMAINDER)
    cancel = subparsers.add_parser("cancel")
    cancel.add_argument("--group-manifest", required=True, type=Path)
    cancel.add_argument("--out", required=True, type=Path)
    cancel.add_argument("--cwd", required=True, type=Path)
    launcher = subparsers.add_parser("_launch")
    launcher.add_argument("--barrier", required=True, type=Path)
    launcher.add_argument("--barrier-timeout", required=True, type=float)
    launcher.add_argument("--parent-pid", required=True, type=int)
    launcher.add_argument("--parent-starttime", required=True, type=int)
    launcher.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.operation == "_launch":
        return _launcher_main(args)
    if args.operation == "cancel":
        cancel_group(args.group_manifest, output_path=args.out, cwd=args.cwd.resolve(strict=True))
        return 0
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    config = FanoutConfig(
        source_repo=args.source_repo,
        commit=args.commit,
        parent_spec=args.parent_spec,
        expected_parent_sha256=args.expected_parent_sha256,
        shard_count=args.shard_count,
        group_root=args.group_root,
        admission_receipt=args.admission_receipt,
        runner_argv=tuple(command),
        poll_interval_s=args.poll_interval,
        barrier_timeout_s=args.barrier_timeout,
    )
    return run_fanout(config)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FanoutDriverError, FanoutContractError, OSError) as exc:
        print(f"mutation fan-out refused: {exc}", file=sys.stderr)
        raise SystemExit(INFRA_RC)
