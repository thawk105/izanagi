# -*- coding: utf-8 -*-
"""codex worker launcher の3区間 admission budget 回帰。"""
from __future__ import annotations

import argparse
import configparser
import copy
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


_ROOT = Path(__file__).resolve().parents[2]
if os.fspath(_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_ROOT))

from tools import codex_worker_launch as LAUNCHER  # noqa: E402
from tools import dev_wave_codex as WRAPPER  # noqa: E402
from orchestrator.tests.growth_test_holds import GROWTH_TEST_HOLDS  # noqa: E402


_LAUNCHER = _ROOT / "tools" / "codex_worker_launch.py"
_WRAPPER = _ROOT / "tools" / "dev_wave_codex.py"
# 親の 1281 件実測 max は準備 3.792 s、最終化 4.940 s。正例は
# それぞれ 8 s (2.11x) と 10 s (2.02x) を確保する。最終化 10 s は
# S->R、すなわち seal と receipt staging/atomic publication の双方を含む。
# 8 + 2 + 10 + 5 (process 終了余裕) = 25 < 外側 watchdog 30 を保つ。
_POSITIVE_PREPARATION_S = Decimal("8")
_POSITIVE_ATTEMPT_S = Decimal("2")
_POSITIVE_FINALIZATION_S = Decimal("10")
_SHUTDOWN_MARGIN_S = Decimal("5")
_OUTER_TIMEOUT_S = Decimal("30")

_HARNESS_SOURCE = r'''#!/usr/bin/env python3
import importlib.util
import os
import sys
import time
from pathlib import Path

target = Path(os.environ["BUDGET_LAUNCHER_TARGET"])
root = target.parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("budget_launcher_under_test", target)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

preparation_delay = float(os.environ.get("BUDGET_PREPARATION_DELAY", "0"))
if preparation_delay:
    original_hook_check = module._require_attempt_hook_installation
    def delayed_hook_check(*args, **kwargs):
        time.sleep(preparation_delay)
        return original_hook_check(*args, **kwargs)
    module._require_attempt_hook_installation = delayed_hook_check

finalization_delay = float(os.environ.get("BUDGET_FINALIZATION_DELAY", "0"))
if finalization_delay:
    original_stage = module._stage_receipt_write
    def delayed_stage(*args, **kwargs):
        time.sleep(finalization_delay)
        return original_stage(*args, **kwargs)
    module._stage_receipt_write = delayed_stage

publication_delay = float(os.environ.get("BUDGET_PUBLICATION_DELAY", "0"))
if publication_delay:
    original_publish = module._atomic_create_json_reserved
    def delayed_publish(*args, **kwargs):
        time.sleep(publication_delay)
        return original_publish(*args, **kwargs)
    module._atomic_create_json_reserved = delayed_publish

raise SystemExit(module.main(sys.argv[1:]))
'''

_FAKE_CODEX_SOURCE = r'''#!/usr/bin/env python3
import fcntl
import json
import os
import signal
import sys
import time
import uuid
from pathlib import Path

if sys.argv[1:] == ["--version"]:
    if os.environ.get("FAKE_VERSION_DETACH") == "1":
        child_pid = os.fork()
        if child_pid == 0:
            marker = Path(os.environ["FAKE_VERSION_CHILD_MARKER"])
            exit_marker = Path(os.environ["FAKE_VERSION_CHILD_EXIT_MARKER"])
            def terminate(_signum, _frame):
                exit_marker.write_text("terminated\n", encoding="ascii")
                raise SystemExit(0)
            signal.signal(signal.SIGTERM, terminate)
            marker.write_text(str(os.getpid()), encoding="ascii")
            devnull = os.open(os.devnull, os.O_RDWR)
            for descriptor in (0, 1, 2):
                os.dup2(devnull, descriptor)
            os.close(devnull)
            time.sleep(30)
            raise SystemExit(0)
        child_marker = Path(os.environ["FAKE_VERSION_CHILD_MARKER"])
        child_ready_deadline = time.monotonic() + 1
        while (
            not child_marker.exists()
            and time.monotonic() < child_ready_deadline
        ):
            time.sleep(0.01)
    time.sleep(float(os.environ.get("FAKE_VERSION_DELAY", "0")))
    print("codex-cli 0.999.0-budget-fake")
    raise SystemExit(0)
if len(sys.argv) < 2 or sys.argv[1] != "exec":
    raise SystemExit(64)

marker = Path(os.environ["FAKE_EXEC_MARKER"])
marker.parent.mkdir(parents=True, exist_ok=True)
with marker.open("a", encoding="ascii") as stream:
    stream.write("spawned\n")
    stream.flush()
    os.fsync(stream.fileno())

counter_path = Path(os.environ["FAKE_COUNTER"])
counter_path.parent.mkdir(parents=True, exist_ok=True)
with counter_path.open("a+", encoding="ascii") as counter:
    fcntl.flock(counter.fileno(), fcntl.LOCK_EX)
    counter.seek(0)
    invocation = int(counter.read().strip() or "0") + 1
    counter.seek(0)
    counter.truncate()
    counter.write(str(invocation))
    counter.flush()
    os.fsync(counter.fileno())

sequence = os.environ.get("FAKE_SEQUENCE", "normal").split(",")
mode = sequence[min(invocation - 1, len(sequence) - 1)]
delays = os.environ.get("FAKE_ATTEMPT_DELAYS", "0").split(",")
delay = float(delays[min(invocation - 1, len(delays) - 1)])
if mode == "runaway":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
    raise SystemExit(0)
time.sleep(delay)

output = Path(sys.argv[sys.argv.index("-o") + 1])
model = sys.argv[sys.argv.index("-m") + 1]
reasoning = sys.argv[sys.argv.index("-c") + 1].split("=", 1)[1].strip('"')
cwd = sys.argv[sys.argv.index("-C") + 1]
session_id = str(uuid.uuid4())
session_root = Path(os.environ["CODEX_HOME"]) / "sessions" / "2026" / "08" / "23"
session_root.mkdir(parents=True, exist_ok=True)
rollout = session_root / f"rollout-2026-08-23T00-00-00-{session_id}.jsonl"

def line(stream, value):
    stream.write(json.dumps(value, separators=(",", ":")) + "\n")
    stream.flush()
    os.fsync(stream.fileno())

usage = {
    "input_tokens": 100,
    "cached_input_tokens": 20,
    "output_tokens": 10,
    "reasoning_output_tokens": 0,
    "total_tokens": 110,
}
with rollout.open("w", encoding="utf-8") as stream:
    line(stream, {"type": "session_meta", "payload": {"session_id": session_id, "cwd": cwd}})
    line(stream, {"type": "turn_context", "payload": {"model": model, "effort": reasoning}})
    line(stream, {
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {"total_token_usage": usage, "last_token_usage": usage},
        },
    })

line(sys.stdout, {"type": "thread.started", "thread_id": session_id})
line(sys.stdout, {"type": "turn.started"})
line(sys.stdout, {
    "type": "item.started",
    "item": {"id": "item_0", "type": "command_execution", "status": "in_progress"},
})
line(sys.stdout, {
    "type": "turn.completed",
    "usage": {
        "input_tokens": usage["input_tokens"],
        "cached_input_tokens": usage["cached_input_tokens"],
        "cache_write_input_tokens": 0,
        "output_tokens": usage["output_tokens"],
        "reasoning_output_tokens": usage["reasoning_output_tokens"],
    },
})
line(sys.stdout, {
    "type": "item.completed",
    "item": {
        "id": "item_0",
        "type": "command_execution",
        "status": "completed",
        "exit_code": 0,
    },
})
if mode == "retry":
    output.write_text("short\n", encoding="utf-8")
else:
    output.write_text(("budget test body " * 80) + "\n## 総括\n完了\n", encoding="utf-8")
'''


def _assert_outer_budget(
    preparation: str, attempt: str, finalization: str
) -> None:
    total = (
        Decimal(preparation)
        + Decimal(attempt)
        + Decimal(finalization)
        + _SHUTDOWN_MARGIN_S
    )
    assert total < _OUTER_TIMEOUT_S, (
        "production 3区間と終了処理余裕の和が外側 timeout 未満でない: "
        f"{total} >= {_OUTER_TIMEOUT_S}"
    )


def _write_executable(path: Path, source: str) -> Path:
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


def _base_command(
    case_root: Path,
    *,
    preparation: str = str(_POSITIVE_PREPARATION_S),
    attempt: str = str(_POSITIVE_ATTEMPT_S),
    finalization: str = str(_POSITIVE_FINALIZATION_S),
    max_attempts: int = 1,
    sandbox: str = "read-only",
) -> tuple[list[str], dict[str, str], dict[str, Path]]:
    _assert_outer_budget(preparation, attempt, finalization)
    case_root.mkdir(parents=True, exist_ok=True)
    prompt = case_root / "prompt.txt"
    prompt.write_text("budget fake prompt\n", encoding="utf-8")
    harness = _write_executable(case_root / "launcher-harness.py", _HARNESS_SOURCE)
    fake = _write_executable(case_root / "fake-codex", _FAKE_CODEX_SOURCE)
    artifact = case_root / "artifacts"
    paths = {
        "prompt": prompt,
        "artifact": artifact,
        "output": case_root / "output.md",
        "receipt": case_root / "receipt.json",
        "manifest": case_root / "manifest.json",
        "marker": case_root / "exec.marker",
        "counter": case_root / "counter",
        "codex_home": case_root / "codex-home",
        "fake": fake,
    }
    base_commit = subprocess.run(
        ["git", "-C", os.fspath(_ROOT), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        timeout=5,
    ).stdout.strip()
    command = [
        sys.executable,
        os.fspath(harness),
        "run",
        "--stage",
        "author",
        "--job-id",
        "budget-job",
        "--wave-id",
        "budget-wave",
        "--repo-root",
        os.fspath(_ROOT),
        "--base-commit",
        base_commit,
        "--prompt-file",
        os.fspath(prompt),
        "--cwd",
        os.fspath(_ROOT),
        "--sandbox",
        sandbox,
        "--preparation-admission-bound-s",
        preparation,
        "--wall-clock-admission-bound-s",
        attempt,
        "--finalization-admission-bound-s",
        finalization,
        "--max-model-calls",
        "100",
        "--max-cli-reported-tokens",
        "100000",
        "--max-attempts",
        str(max_attempts),
        "--artifact-dir",
        os.fspath(artifact),
        "--output-file",
        os.fspath(paths["output"]),
        "--receipt",
        os.fspath(paths["receipt"]),
        "--manifest",
        os.fspath(paths["manifest"]),
        "--sessions-root",
        os.fspath(paths["codex_home"] / "sessions"),
        "--codex-bin",
        os.fspath(fake),
        "--evidence-grace-s",
        attempt,
        "--termination-grace-s",
        "0.05",
        "--poll-interval-s",
        "0.01",
    ]
    env = dict(os.environ)
    env.update(
        {
            "BUDGET_LAUNCHER_TARGET": os.fspath(_LAUNCHER),
            "BUDGET_PREPARATION_DELAY": "0",
            "BUDGET_FINALIZATION_DELAY": "0",
            "BUDGET_PUBLICATION_DELAY": "0",
            "CODEX_HOME": os.fspath(paths["codex_home"]),
            "FAKE_EXEC_MARKER": os.fspath(paths["marker"]),
            "FAKE_COUNTER": os.fspath(paths["counter"]),
            "FAKE_SEQUENCE": "normal",
            "FAKE_ATTEMPT_DELAYS": "0",
            "FAKE_VERSION_DELAY": "0",
            "FAKE_VERSION_DETACH": "0",
            "FAKE_VERSION_CHILD_MARKER": os.fspath(
                case_root / "version-child.pid"
            ),
            "FAKE_VERSION_CHILD_EXIT_MARKER": os.fspath(
                case_root / "version-child.exited"
            ),
        }
    )
    return command, env, paths


def _run_case(
    case_root: Path,
    *,
    expected_rc: int,
    preparation: str = str(_POSITIVE_PREPARATION_S),
    attempt: str = str(_POSITIVE_ATTEMPT_S),
    finalization: str = str(_POSITIVE_FINALIZATION_S),
    max_attempts: int = 1,
    sandbox: str = "read-only",
    env_updates: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], dict[str, Path]]:
    command, env, paths = _base_command(
        case_root,
        preparation=preparation,
        attempt=attempt,
        finalization=finalization,
        max_attempts=max_attempts,
        sandbox=sandbox,
    )
    if env_updates:
        env.update(env_updates)
    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
        timeout=float(_OUTER_TIMEOUT_S),
    )
    assert completed.returncode == expected_rc, (
        f"rc={completed.returncode}, expected={expected_rc}, "
        f"stdout={completed.stdout!r}, stderr={completed.stderr!r}"
    )
    assert paths["receipt"].is_file(), completed.stderr
    receipt = LAUNCHER._load_json(paths["receipt"], label="budget receipt")
    assert isinstance(receipt, dict)
    return completed, receipt, paths


def _as_v3(receipt_v4: dict[str, Any]) -> dict[str, Any]:
    receipt = copy.deepcopy(receipt_v4)
    receipt["schema_version"] = 3
    receipt["limits"].pop("preparation_admission_bound_s")
    receipt["limits"].pop("finalization_admission_bound_s")
    receipt["actuals"].pop("preparation_wall_clock_s")
    receipt["actuals"].pop("finalization_wall_clock_s")
    receipt["limits"]["wall_clock_admission_bound_s"] = (
        receipt["actuals"]["wall_clock_s"] + 1
    )
    return receipt


def _as_v2(receipt_v4: dict[str, Any]) -> dict[str, Any]:
    v3 = _as_v3(receipt_v4)
    return {
        "schema_version": 2,
        "job_id": v3["job_id"],
        "prompt_sha256": v3["prompt_sha256"],
        "model": v3["requested_model"],
        "reasoning": v3["requested_effort"],
        "sandbox": v3["sandbox"],
        "cwd": v3["requested_cwd"],
        "artifact_dir": v3["artifact_dir"],
        "output_path": v3["output_path"],
        "output_sha256": v3["output_sha256"],
        "manifest_path": v3["manifest_path"],
        "manifest_wave_id": v3["manifest_wave_id"],
        "manifest_repo_root": v3["repo_root"],
        "manifest_base_commit": v3["base_commit"],
        "codex_version": v3["codex_version"],
        "codex_executable_path": v3["codex_executable_path"],
        "codex_executable_sha256": v3["codex_executable_sha256"],
        "model_calls_semantics": v3["model_calls_semantics"],
        "possible_unobserved_overshoot": v3["possible_unobserved_overshoot"],
        "limits_assertion": v3["limits_assertion"],
        "wall_clock_scope": v3["wall_clock_scope"],
        "retry_classification": v3["retry_classification"],
        "escaped_process_containment": v3["escaped_process_containment"],
        "limits": v3["limits"],
        "actuals": v3["actuals"],
        "outcome": v3["outcome"],
        "stop_reason": v3["stop_reason"],
        "launcher_rc": v3["launcher_rc"],
        "codex_exit_code": v3["codex_exit_code"],
        "validator_rc": v3["validator_rc"],
        "attempts": v3["attempts"],
    }


def _accepted_case(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    _completed, receipt, paths = _run_case(
        tmp_path / "accepted", expected_rc=0
    )
    assert receipt["schema_version"] == 4
    assert receipt["outcome"] == "accepted"
    return receipt, paths


def _net_attempt_wall(receipt: dict[str, Any]) -> Decimal:
    return (
        Decimal(str(receipt["actuals"]["wall_clock_s"]))
        - Decimal(str(receipt["actuals"]["preparation_wall_clock_s"]))
        - Decimal(str(receipt["actuals"]["finalization_wall_clock_s"]))
    )


def _launcher_diagnostics(paths: dict[str, Path]) -> dict[str, Any]:
    matches = list(paths["artifact"].glob("launcher-diagnostics.*.json"))
    assert len(matches) == 1, matches
    value = LAUNCHER._load_json(matches[0], label="budget diagnostics")
    assert isinstance(value, dict)
    return value


def test_three_budget_operational_defaults_are_finite_and_independent() -> None:
    run_parser = LAUNCHER._parser()._subparsers._group_actions[0].choices["run"]
    defaults = {action.dest: action.default for action in run_parser._actions}

    assert defaults["preparation_admission_bound_s"] == Decimal("60")
    assert defaults["finalization_admission_bound_s"] == Decimal("60")
    assert WRAPPER.DEFAULT_PREPARATION_ADMISSION_BOUND_S == 60
    assert WRAPPER.DEFAULT_WALL_CLOCK_ADMISSION_BOUND_S == 3600
    assert WRAPPER.DEFAULT_FINALIZATION_ADMISSION_BOUND_S == 60
    assert _POSITIVE_PREPARATION_S >= Decimal("3.792") * 2
    assert _POSITIVE_FINALIZATION_S >= Decimal("4.940") * 2
    # finalization は S->R なので seal と最終 atomic publication を含む。
    _assert_outer_budget(
        str(_POSITIVE_PREPARATION_S),
        str(_POSITIVE_ATTEMPT_S),
        str(_POSITIVE_FINALIZATION_S),
    )


def test_direct_attempt_loop_namespace_defaults_are_fail_closed() -> None:
    args = argparse.Namespace()
    LAUNCHER._ensure_attempt_loop_budget_state(
        args, job_started_ns=1_000_000_000
    )

    assert args.launcher_started_ns == 1_000_000_000
    assert args.codex_version_wall_clock_s == 0
    assert args.attempt_budget_started_ns is None
    assert LAUNCHER._preparation_admission_elapsed_s(
        args, 1_500_000_000
    ) == Decimal("0.5")


def test_version_is_not_double_counted_across_preparation_and_attempt() -> None:
    args = argparse.Namespace(
        launcher_started_ns=1_000_000_000,
        codex_version_wall_clock_s=Decimal("0.4"),
        attempt_budget_started_ns=None,
        attempt_budget_completed_ns=None,
    )
    boundary_ns = 2_000_000_000
    LAUNCHER._start_attempt_budget_once(args, now_ns=boundary_ns)
    preparation = LAUNCHER._preparation_admission_elapsed_s(
        args, boundary_ns
    )
    attempt = LAUNCHER._attempt_admission_elapsed_s(
        args, 2_100_000_000
    )

    assert preparation == Decimal("0.6")
    assert attempt == Decimal("0.5")
    assert preparation + attempt == Decimal("1.1")


def test_slow_preparation_longer_than_attempt_budget_is_accepted(
    tmp_path: Path,
) -> None:
    _completed, receipt, _paths = _run_case(
        tmp_path,
        expected_rc=0,
        preparation="8",
        attempt="1.5",
        finalization="10",
        env_updates={"BUDGET_PREPARATION_DELAY": "2"},
    )

    assert receipt["outcome"] == "accepted"
    assert receipt["actuals"]["preparation_wall_clock_s"] > Decimal("1.5")
    assert receipt["actuals"]["preparation_wall_clock_s"] < 8


def test_preparation_bound_stops_before_spawn(tmp_path: Path) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path,
        expected_rc=1,
        preparation="0.5",
        attempt="1",
        finalization="10",
        env_updates={"BUDGET_PREPARATION_DELAY": "0.8"},
    )

    assert receipt["outcome"] == "not_accepted"
    assert receipt["stop_reason"] == "preparation_admission_bound_s"
    assert receipt["attempts"] == []
    assert not paths["marker"].exists()


def test_preparation_stop_receipt_still_passes_finalization_gate(
    tmp_path: Path,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path,
        expected_rc=1,
        preparation="0.3",
        attempt="2",
        finalization="0.1",
        env_updates={
            "BUDGET_PREPARATION_DELAY": "0.6",
            "BUDGET_FINALIZATION_DELAY": "0.2",
        },
    )

    assert receipt["stop_reason"] == "finalization_admission_bound_s"
    assert receipt["attempts"] == []
    assert receipt["actuals"]["preparation_wall_clock_s"] >= Decimal("0.3")
    assert receipt["actuals"]["finalization_wall_clock_s"] >= Decimal("0.1")
    assert not paths["marker"].exists()


@pytest.mark.parametrize(
    ("finalization_delay", "finalization_bound", "expected_rc", "expected_reason"),
    [
        ("0.2", "10", 0, "completed"),
        ("0.2", "0.1", 1, "finalization_admission_bound_s"),
    ],
)
def test_finalization_bound_has_positive_and_negative_controls(
    tmp_path: Path,
    finalization_delay: str,
    finalization_bound: str,
    expected_rc: int,
    expected_reason: str,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path,
        expected_rc=expected_rc,
        preparation="8",
        attempt="1",
        finalization=finalization_bound,
        env_updates={"BUDGET_FINALIZATION_DELAY": finalization_delay},
    )

    assert receipt["stop_reason"] == expected_reason
    if expected_rc == 0:
        assert receipt["actuals"]["finalization_wall_clock_s"] < Decimal(
            finalization_bound
        )
        assert paths["output"].is_file()
    else:
        assert receipt["actuals"]["finalization_wall_clock_s"] >= Decimal(
            finalization_bound
        )
        assert receipt["attempts"][0]["limit_trigger"] is None
        assert not paths["output"].exists()


def test_runaway_still_hits_attempt_bound_after_slow_preparation(
    tmp_path: Path,
) -> None:
    _completed, receipt, paths = _run_case(
        tmp_path,
        expected_rc=1,
        preparation="8",
        attempt="0.4",
        finalization="10",
        env_updates={
            "BUDGET_PREPARATION_DELAY": "0.6",
            "FAKE_SEQUENCE": "runaway",
        },
    )

    assert paths["marker"].is_file()
    assert receipt["attempts"][0]["limit_trigger"] == (
        "wall_clock_admission_bound_s"
    )
    assert receipt["actuals"]["preparation_wall_clock_s"] > Decimal("0.4")


def test_version_time_consumes_attempt_not_preparation_budget(
    tmp_path: Path,
) -> None:
    command, env, paths = _base_command(
        tmp_path,
        preparation="8",
        attempt="1.2",
        finalization="10",
    )
    env["FAKE_VERSION_DELAY"] = "1.4"
    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
        timeout=float(_OUTER_TIMEOUT_S),
    )

    assert completed.returncode == 2
    assert "wall_clock_admission_bound_s" in completed.stderr
    assert "preparation_admission_bound_s" not in completed.stderr
    assert not paths["marker"].exists()
    # V4 は控除後 attempt wall を全 outcome で検査するため、上限超過を
    # accepted と偽装した receipt の公開を許さない。
    assert paths["receipt"].is_file()
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    assert receipt["outcome"] == "launcher_error"
    assert receipt["outcome"] != "accepted"
    assert receipt["attempts"] == []


def test_version_process_group_rejects_and_reaps_detached_child(
    tmp_path: Path,
) -> None:
    command, env, paths = _base_command(tmp_path)
    child_marker = tmp_path / "version-child.pid"
    child_exit_marker = tmp_path / "version-child.exited"
    env.update(
        {
            "FAKE_VERSION_DETACH": "1",
            "FAKE_VERSION_CHILD_MARKER": os.fspath(child_marker),
            "FAKE_VERSION_CHILD_EXIT_MARKER": os.fspath(child_exit_marker),
        }
    )
    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
        timeout=float(_OUTER_TIMEOUT_S),
    )

    assert completed.returncode == 2
    assert "残留子孫 process" in completed.stderr
    assert child_marker.is_file()
    assert int(child_marker.read_text(encoding="ascii")) > 0
    assert child_exit_marker.read_text(encoding="ascii") == "terminated\n"
    assert not paths["receipt"].exists()


def test_retry_attempt_clock_is_cumulative_under_logical_time() -> None:
    args = argparse.Namespace(
        attempt_budget_started_ns=None,
        attempt_budget_completed_ns=None,
        codex_version_wall_clock_s=Decimal("0.2"),
    )
    LAUNCHER._start_attempt_budget_once(args, now_ns=1_000_000_000)
    first = LAUNCHER._attempt_admission_elapsed_s(args, 1_400_000_000)
    LAUNCHER._start_attempt_budget_once(args, now_ns=1_400_000_000)
    second = LAUNCHER._attempt_admission_elapsed_s(args, 1_800_000_000)

    assert args.attempt_budget_started_ns == 1_000_000_000
    assert first == Decimal("0.6")
    assert second == Decimal("1.0")
    assert first < Decimal("0.8")
    assert second > Decimal("0.8")


def test_retry_subprocess_hits_only_cumulative_attempt_bound(
    tmp_path: Path,
) -> None:
    _completed, receipt, _paths = _run_case(
        tmp_path,
        expected_rc=1,
        preparation="8",
        attempt="1",
        finalization="10",
        max_attempts=2,
        env_updates={
            "FAKE_SEQUENCE": "retry,normal",
            "FAKE_ATTEMPT_DELAYS": "0.35,0.8",
        },
    )

    assert len(receipt["attempts"]) == 2
    assert all(item["wall_clock_s"] < 1 for item in receipt["attempts"])
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][1]["limit_trigger"] == (
        "wall_clock_admission_bound_s"
    )


def test_v4_truth_table_rejects_interval_mutations(tmp_path: Path) -> None:
    receipt, _paths = _accepted_case(tmp_path)
    mutations: list[dict[str, Any]] = []

    preparation_over_total = copy.deepcopy(receipt)
    preparation_over_total["actuals"]["preparation_wall_clock_s"] = (
        preparation_over_total["actuals"]["wall_clock_s"] + 1
    )
    mutations.append(preparation_over_total)

    preparation_at_bound = copy.deepcopy(receipt)
    preparation_at_bound["limits"]["preparation_admission_bound_s"] = (
        preparation_at_bound["actuals"]["preparation_wall_clock_s"]
    )
    mutations.append(preparation_at_bound)

    net_wall_over_bound = copy.deepcopy(receipt)
    adjusted = (
        Decimal(str(net_wall_over_bound["actuals"]["wall_clock_s"]))
        - Decimal(str(net_wall_over_bound["actuals"]["preparation_wall_clock_s"]))
        - Decimal(str(net_wall_over_bound["actuals"]["finalization_wall_clock_s"]))
    )
    net_wall_over_bound["limits"]["wall_clock_admission_bound_s"] = adjusted / 2
    mutations.append(net_wall_over_bound)

    for mutation in mutations:
        with pytest.raises(LAUNCHER.LaunchError):
            LAUNCHER._validate_receipt(mutation)


@pytest.mark.parametrize(
    "field_name",
    ("preparation_wall_clock_s", "finalization_wall_clock_s"),
)
def test_v4_truth_table_rejects_negative_interval_actuals(
    tmp_path: Path, field_name: str
) -> None:
    receipt, _paths = _accepted_case(tmp_path)
    receipt["actuals"][field_name] = Decimal("-0.001")

    with pytest.raises(LAUNCHER.LaunchError):
        LAUNCHER._validate_receipt(receipt)


def test_v4_job_stops_cannot_mask_attempt_wall_overrun(
    tmp_path: Path,
) -> None:
    _completed, preparation_receipt, _paths = _run_case(
        tmp_path / "preparation",
        expected_rc=1,
        preparation="0.3",
        attempt="2",
        finalization="10",
        env_updates={"BUDGET_PREPARATION_DELAY": "0.6"},
    )
    _completed, finalization_receipt, _paths = _run_case(
        tmp_path / "finalization",
        expected_rc=1,
        preparation="8",
        attempt="2",
        finalization="0.1",
        env_updates={"BUDGET_FINALIZATION_DELAY": "0.2"},
    )

    for receipt in (preparation_receipt, finalization_receipt):
        mutation = copy.deepcopy(receipt)
        net_wall = _net_attempt_wall(mutation)
        assert net_wall > 0
        mutation["limits"]["wall_clock_admission_bound_s"] = net_wall / 2
        with pytest.raises(LAUNCHER.LaunchError):
            LAUNCHER._validate_receipt(mutation)


def test_atomic_publication_overrun_is_visible_in_rc_and_diagnostics(
    tmp_path: Path,
) -> None:
    # 実測 finalization max 4.940 s より十分広い 10 s を gate 前に確保し、
    # atomic helper だけへ 10.2 s を注入して publication tail に照準する。
    completed, receipt, paths = _run_case(
        tmp_path,
        expected_rc=1,
        preparation="8",
        attempt="2",
        finalization="10",
        env_updates={"BUDGET_PUBLICATION_DELAY": "10.2"},
    )
    diagnostics = _launcher_diagnostics(paths)
    publication = diagnostics["finalization_publication"]

    # Gate 時点では内側で、atomic publication だけが上限をまたぐ。
    assert publication["gate_elapsed_s"] < Decimal("10")
    assert publication["completed_elapsed_s"] >= Decimal("10")
    assert publication["limit_exceeded_after_publication"] is True
    assert receipt["outcome"] == "accepted"
    assert receipt["launcher_rc"] == 0
    assert completed.returncode != receipt["launcher_rc"]


def test_check_receipt_accepts_v4_and_binds_all_three_limits(
    tmp_path: Path,
) -> None:
    preparation, attempt, finalization = "8", "2", "10"
    _assert_outer_budget(preparation, attempt, finalization)
    _receipt, paths = _accepted_case(tmp_path)
    command = [
        sys.executable,
        os.fspath(_LAUNCHER),
        "check-receipt",
        "--receipt",
        os.fspath(paths["receipt"]),
        "--manifest",
        os.fspath(paths["manifest"]),
        "--expect-preparation-admission-bound-s",
        preparation,
        "--expect-wall-clock-admission-bound-s",
        attempt,
        "--expect-finalization-admission-bound-s",
        finalization,
        "--expect-max-model-calls",
        "100",
        "--expect-max-cli-reported-tokens",
        "100000",
        "--expect-max-attempts",
        "1",
    ]
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=float(_OUTER_TIMEOUT_S),
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["schema_version"] == 4
    assert report["limits_self_asserted"] == []


def test_v1_v2_v3_closed_receipts_remain_valid(tmp_path: Path) -> None:
    receipt, _paths = _accepted_case(tmp_path)
    v2 = _as_v2(receipt)
    v1 = copy.deepcopy(v2)
    v1["schema_version"] = 1
    for field_name in (
        "limits_assertion",
        "wall_clock_scope",
        "manifest_repo_root",
        "manifest_base_commit",
    ):
        v1.pop(field_name)

    for old_receipt in (v1, v2, _as_v3(receipt)):
        validated = LAUNCHER._validate_receipt(old_receipt)
        assert validated["schema_version"] == old_receipt["schema_version"]


def test_complete_v3_receipt_blocks_v4_writer_without_byte_change(
    tmp_path: Path,
) -> None:
    receipt, _paths = _accepted_case(tmp_path / "source")
    command, env, blocked_paths = _base_command(tmp_path / "blocked")
    v3_bytes = LAUNCHER._json_bytes(_as_v3(receipt))
    blocked_paths["receipt"].write_bytes(v3_bytes)

    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
        timeout=float(_OUTER_TIMEOUT_S),
    )

    assert completed.returncode == 2
    assert blocked_paths["receipt"].read_bytes() == v3_bytes
    assert not blocked_paths["marker"].exists()


def test_job_stop_reasons_never_become_attempt_limit_triggers(
    tmp_path: Path,
) -> None:
    _completed, preparation_receipt, _paths = _run_case(
        tmp_path / "preparation",
        expected_rc=1,
        preparation="0.3",
        attempt="1",
        finalization="10",
        env_updates={"BUDGET_PREPARATION_DELAY": "0.6"},
    )
    _completed, finalization_receipt, _paths = _run_case(
        tmp_path / "finalization",
        expected_rc=1,
        preparation="8",
        attempt="1",
        finalization="0.1",
        env_updates={"BUDGET_FINALIZATION_DELAY": "0.2"},
    )

    assert preparation_receipt["attempts"] == []
    assert finalization_receipt["attempts"][0]["limit_trigger"] is None
    for reason in (
        "preparation_admission_bound_s",
        "finalization_admission_bound_s",
    ):
        assert reason not in LAUNCHER._LIMIT_REASONS
        invalid = copy.deepcopy(finalization_receipt)
        invalid["attempts"][0]["limit_trigger"] = reason
        with pytest.raises(LAUNCHER.LaunchError):
            LAUNCHER._validate_receipt(invalid)


def test_wrapper_forwards_both_new_limits_independently(tmp_path: Path) -> None:
    preparation, attempt, finalization = "8", "2", "10"
    _assert_outer_budget(preparation, attempt, finalization)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("wrapper budget prompt\n", encoding="utf-8")
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    output = tmp_path / "output.md"
    command = [
        sys.executable,
        os.fspath(_WRAPPER),
        "--stage",
        "plan",
        "--wave",
        "budget-wrapper",
        "--prompt-file",
        os.fspath(prompt),
        "--artifact-root",
        os.fspath(artifact_root),
        "--output-file",
        os.fspath(output),
        "--reasoning",
        "high",
        "--sandbox",
        "read-only",
        "--repo-root",
        os.fspath(_ROOT),
        "--preparation-admission-bound-s",
        preparation,
        "--wall-clock-admission-bound-s",
        attempt,
        "--finalization-admission-bound-s",
        finalization,
        "--evidence-grace-s",
        "1",
        "--dry-run",
    ]
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=float(_OUTER_TIMEOUT_S),
    )

    assert completed.returncode == 0, completed.stderr
    argv = completed.stdout.splitlines()
    for option, expected in (
        ("--preparation-admission-bound-s", preparation),
        ("--wall-clock-admission-bound-s", attempt),
        ("--finalization-admission-bound-s", finalization),
    ):
        assert argv.count(option) == 1
        assert argv[argv.index(option) + 1] == expected


def test_wrapper_help_describes_version_and_final_publication_boundaries() -> None:
    actions = {action.dest: action for action in WRAPPER._parser()._actions}

    assert "--version の実測時間" in actions[
        "wall_clock_admission_bound_s"
    ].help
    assert "version と spawn" in actions["evidence_grace_s"].help
    assert "atomic 公開" in actions["finalization_admission_bound_s"].help


def test_new_file_is_collected_and_not_held_by_meta_contracts() -> None:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(_ROOT / "pytest.ini", encoding="utf-8")
    assert parser["pytest"]["testpaths"] == "orchestrator/tests"
    assert Path(__file__).name.startswith("test_")
    assert Path(__file__).suffix == ".py"
    assert not any(
        nodeid.startswith(f"{Path(__file__).name}::")
        for nodeid in GROWTH_TEST_HOLDS
    )


def _run() -> int:
    """新設 file を直接起動しても全 node を pytest で自己検査する。"""
    return int(pytest.main(["-q", os.fspath(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
