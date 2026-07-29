# -*- coding: utf-8 -*-
"""tools/codex_worker_launch.py の fake Codex executable 回帰。"""
from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_LAUNCHER = _ROOT / "tools" / "codex_worker_launch.py"
_BASE_COMMIT = subprocess.run(
    ["git", "-C", os.fspath(_ROOT), "rev-parse", "HEAD"],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
).stdout.strip()
_SPEC = importlib.util.spec_from_file_location(
    "codex_worker_launch_under_test", _LAUNCHER
)
assert _SPEC and _SPEC.loader
LAUNCHER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = LAUNCHER
_SPEC.loader.exec_module(LAUNCHER)


def _write_fake_codex(path: Path) -> Path:
    """実 Codex を呼ばず、CLI 0.146.0 の stdout/rollout seam を再現する。"""
    source = r'''#!/usr/bin/env python3
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

if sys.argv[1:] == ["--version"]:
    time.sleep(float(os.environ.get("FAKE_VERSION_DELAY", "0")))
    print("codex-cli 0.146.0-fake")
    raise SystemExit(0)
if len(sys.argv) < 2 or sys.argv[1] != "exec":
    raise SystemExit(64)
if "--json" not in sys.argv or "--ephemeral" in sys.argv:
    raise SystemExit(66)
if os.read(0, 1) != b"":
    raise SystemExit(67)

pid_dir = Path(os.environ["FAKE_PID_DIR"])
pid_dir.mkdir(parents=True, exist_ok=True)
(pid_dir / f"leader-{os.getpid()}.pid").write_text(str(os.getpid()), encoding="ascii")
(pid_dir / f"argv-{os.getpid()}.json").write_text(
    json.dumps(sys.argv[1:]), encoding="utf-8"
)
counter_path = Path(os.environ.get("FAKE_COUNTER", pid_dir / "counter"))
counter_path.parent.mkdir(parents=True, exist_ok=True)
with counter_path.open("a+", encoding="ascii") as counter:
    fcntl.flock(counter.fileno(), fcntl.LOCK_EX)
    counter.seek(0)
    raw = counter.read().strip()
    invocation = int(raw or "0") + 1
    counter.seek(0)
    counter.truncate()
    counter.write(str(invocation))
    counter.flush()
    os.fsync(counter.fileno())
sequence = os.environ.get("FAKE_SEQUENCE", os.environ.get("FAKE_MODE", "normal")).split(",")
mode = sequence[min(invocation - 1, len(sequence) - 1)]

barrier = os.environ.get("FAKE_BARRIER_DIR")
if barrier:
    barrier_path = Path(barrier)
    barrier_path.mkdir(parents=True, exist_ok=True)
    (barrier_path / f"ready-{os.getpid()}").write_text("1", encoding="ascii")
    deadline = time.monotonic() + 5
    wanted = int(os.environ.get("FAKE_BARRIER_COUNT", "2"))
    while len(list(barrier_path.glob("ready-*"))) < wanted:
        if time.monotonic() >= deadline:
            raise SystemExit(65)
        time.sleep(0.005)

output = Path(sys.argv[sys.argv.index("-o") + 1])
model = sys.argv[sys.argv.index("-m") + 1]
reasoning_arg = sys.argv[sys.argv.index("-c") + 1]
reasoning = reasoning_arg.split("=", 1)[1].strip('"')
session_root = Path(os.environ["CODEX_HOME"]) / "sessions" / "2026" / "07" / "29"
session_root.mkdir(parents=True, exist_ok=True)
valid_output = ("十分な検査本文です。" * 80) + "\n## 総括\nfake Codex 完了\n"

def emit(value):
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    os.fsync(sys.stdout.fileno())

def write_line(stream, value):
    stream.write(json.dumps(value, separators=(",", ":")) + "\n")
    stream.flush()
    os.fsync(stream.fileno())

def usage(input_tokens=100, cached=20, output_tokens=10, total=110):
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": 0,
        "total_tokens": total,
    }

def create_rollout(session_id):
    path = session_root / f"rollout-2026-07-29T00-00-00-{session_id}.jsonl"
    with path.open("w", encoding="utf-8") as stream:
        write_line(stream, {
            "type": "session_meta",
            "payload": {"session_id": session_id, "cwd": sys.argv[sys.argv.index("-C") + 1]},
        })
        write_line(stream, {
            "type": "turn_context",
            "payload": {"model": model, "effort": reasoning},
        })
    return path

def append_token(path, total_usage):
    with path.open("a", encoding="utf-8") as stream:
        write_line(stream, {
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": (
                    None
                    if total_usage is None
                    else {
                        "total_token_usage": total_usage,
                        "last_token_usage": total_usage,
                    }
                ),
            },
        })

def terminal(total_usage):
    emit({
        "type": "turn.completed",
        "usage": {
            "input_tokens": total_usage["input_tokens"],
            "cached_input_tokens": total_usage["cached_input_tokens"],
            "cache_write_input_tokens": 0,
            "output_tokens": total_usage["output_tokens"],
            "reasoning_output_tokens": total_usage.get("reasoning_output_tokens", 0),
        },
    })

def child_sleep(*, escaped=False, ignore_term=False):
    code = (
        "import os,signal,time,pathlib;"
        + ("os.setsid();" if escaped else "")
        + ("signal.signal(signal.SIGTERM,signal.SIG_IGN);" if ignore_term else "")
        + "pathlib.Path(os.environ['FAKE_CHILD_PID']).write_text(str(os.getpid()));"
        + "time.sleep(30)"
    )
    child_env = dict(os.environ)
    child_env["FAKE_CHILD_PID"] = str(pid_dir / ("escaped.pid" if escaped else "child.pid"))
    return subprocess.Popen([sys.executable, "-c", code], env=child_env)

if mode == "no_thread":
    child_sleep(ignore_term=True)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
    raise SystemExit(0)

if mode == "delayed_thread":
    time.sleep(0.12)

session_id = str(uuid.uuid4())
if mode != "cli_exact":
    emit({"type": "thread.started", "thread_id": session_id})
emit({"type": "turn.started"})
emit({
    "type": "item.started",
    "item": {
        "id": "item_0",
        "type": "command_execution",
        "status": "in_progress",
    },
})

if mode == "no_rollout":
    terminal(usage())
    output.write_text(valid_output, encoding="utf-8")
    time.sleep(30)
    raise SystemExit(0)

if mode == "cached_bad":
    selected_usage = usage(input_tokens=100, cached=101, output_tokens=1, total=101)
elif mode in ("cli_exact", "token_wait"):
    selected_usage = usage(input_tokens=1000, cached=950, output_tokens=10, total=1010)
elif mode in ("retry_reject", "retry_wait"):
    selected_usage = usage(input_tokens=10, cached=0, output_tokens=0, total=10)
elif mode == "final_drain":
    selected_usage = usage(input_tokens=90, cached=0, output_tokens=0, total=90)
else:
    selected_usage = usage()

rollout_path = create_rollout(session_id)
time.sleep(0.04)
if mode == "rollback":
    append_token(
        rollout_path,
        usage(input_tokens=1000, cached=0, output_tokens=0, total=1000),
    )
    append_token(
        rollout_path,
        usage(input_tokens=1000, cached=999, output_tokens=1, total=1001),
    )
    selected_usage = usage(
        input_tokens=1000, cached=999, output_tokens=1, total=1001
    )
elif mode == "rollback_equal_cli":
    append_token(
        rollout_path,
        usage(input_tokens=100, cached=0, output_tokens=0, total=100),
    )
    append_token(
        rollout_path,
        usage(input_tokens=99, cached=0, output_tokens=1, total=100),
    )
    # peak latch と terminal mismatch を発火させず、rollback gate だけを負にする。
    selected_usage = usage(
        input_tokens=100, cached=0, output_tokens=0, total=100
    )
elif mode == "null_info":
    append_token(rollout_path, None)
    append_token(rollout_path, selected_usage)
elif mode != "no_token":
    append_token(rollout_path, selected_usage)
if mode == "final_drain":
    time.sleep(0.15)
    selected_usage = usage(
        input_tokens=110, cached=0, output_tokens=0, total=110
    )
    append_token(rollout_path, selected_usage)

if mode in ("id_change", "multiple_sessions", "id_change_wait"):
    if mode == "id_change_wait":
        child_sleep(ignore_term=True)
        child_pid_path = pid_dir / "child.pid"
        deadline = time.monotonic() + 2
        while not child_pid_path.exists():
            if time.monotonic() >= deadline:
                raise SystemExit(68)
            time.sleep(0.005)
    second = str(uuid.uuid4())
    emit({"type": "thread.started", "thread_id": second})
    second_path = create_rollout(second)
    append_token(
        second_path,
        usage(input_tokens=0, cached=0, output_tokens=0, total=0),
    )

if mode == "inconsistent":
    terminal(usage(input_tokens=101, cached=20, output_tokens=10, total=111))
elif mode != "token_wait":
    terminal(selected_usage)

emit({
    "type": "item.completed",
    "item": {
        "id": "item_0",
        "type": "command_execution",
        "status": "completed",
        "exit_code": 0,
    },
})

if mode in ("retry_reject",):
    output.write_text("短い失敗", encoding="utf-8")
else:
    output.write_text(valid_output, encoding="utf-8")

if mode == "cli_exact":
    # stdout thread ID を最後に flush して即終了し、同一 poll の自然終了
    # と actual == limit 境界を決定的に作る。
    emit({"type": "thread.started", "thread_id": session_id})
elif mode == "term_success":
    def finish(_signum, _frame):
        output.write_text(valid_output, encoding="utf-8")
        terminal(selected_usage)
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, finish)
    time.sleep(30)
elif mode == "sigterm_ignore":
    child_sleep(ignore_term=True)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
elif mode in ("token_wait", "retry_wait"):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
elif mode == "setsid_escape":
    child_sleep(escaped=True)
    time.sleep(0.05)
elif mode == "manifest_while_running":
    time.sleep(0.5)
elif mode == "id_change_wait":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)
elif mode == "late_writer":
    child = os.fork()
    if child == 0:
        os.setsid()
        (pid_dir / "late.pid").write_text(str(os.getpid()), encoding="ascii")
        time.sleep(0.5)
        with rollout_path.open("a", encoding="utf-8") as stream:
            write_line(stream, {"type": "event_msg", "payload": {"type": "late"}})
        os._exit(0)
else:
    time.sleep(0.04)
'''
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


def _base_command(
    tmp_path: Path,
    *,
    fake: Path,
    job_id: str = "job-a",
    wave_id: str = "wave-a",
    sandbox: str = "read-only",
    max_attempts: int = 1,
    max_wall: str = "3",
    max_calls: int = 100,
    max_tokens: int = 100000,
    suffix: str = "",
) -> tuple[list[str], dict[str, str], dict[str, Path]]:
    prompt = tmp_path / f"prompt{suffix}.txt"
    prompt.write_text("fake prompt\n", encoding="utf-8")
    codex_home = tmp_path / f"codex-home{suffix}"
    pid_dir = tmp_path / f"pids{suffix}"
    artifact = tmp_path / f"artifacts{suffix}"
    paths = {
        "prompt": prompt,
        "codex_home": codex_home,
        "pid_dir": pid_dir,
        "artifact": artifact,
        "output": tmp_path / f"output{suffix}.md",
        "receipt": tmp_path / f"receipt{suffix}.json",
        "manifest": tmp_path / "manifest.json",
        "counter": tmp_path / f"counter{suffix}",
    }
    command = [
        sys.executable,
        os.fspath(_LAUNCHER),
        "run",
        "--job-id",
        job_id,
        "--wave-id",
        wave_id,
        "--repo-root",
        os.fspath(_ROOT),
        "--base-commit",
        _BASE_COMMIT,
        "--prompt-file",
        os.fspath(prompt),
        "--cwd",
        os.fspath(_ROOT),
        "--sandbox",
        sandbox,
        "--model",
        "gpt-5.6-sol",
        "--reasoning",
        "high",
        "--max-wall-clock-s",
        max_wall,
        "--max-model-calls",
        str(max_calls),
        "--max-cli-reported-tokens",
        str(max_tokens),
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
        os.fspath(codex_home / "sessions"),
        "--codex-bin",
        os.fspath(fake),
        "--evidence-grace-s",
        "1.0",
        "--termination-grace-s",
        "0.05",
        "--poll-interval-s",
        "0.01",
    ]
    env = dict(os.environ)
    env.update(
        {
            "CODEX_HOME": os.fspath(codex_home),
            "FAKE_PID_DIR": os.fspath(pid_dir),
            "FAKE_COUNTER": os.fspath(paths["counter"]),
        }
    )
    return command, env, paths


def _run_case(
    tmp_path: Path,
    mode: str,
    **kwargs: Any,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None, dict[str, Path]]:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake, **kwargs)
    env["FAKE_MODE"] = mode
    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )
    receipt = (
        json.loads(paths["receipt"].read_text(encoding="utf-8"))
        if paths["receipt"].exists()
        else None
    )
    return completed, receipt, paths


def _assert_pid_gone(pid: int) -> None:
    deadline = time.monotonic() + 3
    while Path(f"/proc/{pid}").exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not Path(f"/proc/{pid}").exists(), f"PID {pid} survived"


def _leader_pids(paths: dict[str, Path]) -> list[int]:
    return [
        int(path.read_text(encoding="ascii"))
        for path in paths["pid_dir"].glob("leader-*.pid")
    ]


def _check_command(paths: dict[str, Path]) -> list[str]:
    return [
        sys.executable,
        os.fspath(_LAUNCHER),
        "check-receipt",
        "--receipt",
        os.fspath(paths["receipt"]),
        "--manifest",
        os.fspath(paths["manifest"]),
    ]


def _run_main_in_process(
    command: list[str],
    env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> int:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        LAUNCHER, "_LAUNCHER_PROCESS_STARTED_NS", time.monotonic_ns()
    )
    return LAUNCHER.main(command[2:])


def test_positive_p1_normal_job_is_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")

    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    assert receipt["outcome"] == "accepted"
    assert receipt["stop_reason"] == "completed"
    assert receipt["launcher_rc"] == 0
    assert receipt["model_calls_semantics"] == "observed_token_count_events"
    assert receipt["schema_version"] == 2
    assert receipt["limits_assertion"] == "self_asserted"
    assert (
        receipt["wall_clock_scope"]
        == "launcher_start_to_receipt_fields_finalized"
    )
    assert receipt["manifest_repo_root"] == os.fspath(_ROOT)
    assert receipt["manifest_base_commit"] == _BASE_COMMIT
    assert receipt["possible_unobserved_overshoot"] is False
    assert receipt["retry_classification"] == "none"
    assert receipt["escaped_process_containment"] == "not_attempted"
    assert receipt["attempts"][0]["accepted"] is True
    assert receipt["attempts"][0]["metering_status"] == "complete"
    assert receipt["attempts"][0]["process_group_residual"] == 0
    assert receipt["attempts"][0]["termination_verified"] is True
    assert paths["output"].read_text(encoding="utf-8").endswith(
        "fake Codex 完了\n"
    )
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert set(manifest) == {
        "schema_version",
        "wave_id",
        "repo_root",
        "base_commit",
        "sessions",
    }
    assert manifest["wave_id"] == "wave-a"
    assert len(manifest["sessions"]) == 1
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_limit_stop_is_never_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "term_success",
        max_calls=1,
        max_tokens=100000,
        max_wall="3",
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "max_model_calls"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] == "max_model_calls"
    assert receipt["attempts"][0]["codex_exit_code"] == 0
    assert receipt["attempts"][0]["validator_rc"] == 0
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["outcome"] == "not_accepted"
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_missing_metering_evidence_is_not_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "no_token",
        max_calls=100,
        max_tokens=100000,
        max_wall="3",
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["metering_status"] == "missing"
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_token_cap_uses_cli_reported_definition(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "cli_exact",
        max_calls=100,
        max_tokens=61,
        max_wall="3",
    )

    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "completed"
    assert receipt["actuals"]["input_tokens"] == 1000
    assert receipt["actuals"]["cached_input_tokens"] == 950
    assert receipt["actuals"]["output_tokens"] == 10
    assert receipt["actuals"]["cli_reported"] == 60
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["accepted"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_cli_reported_token_limit_stops_process(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "token_wait",
        max_calls=100,
        max_tokens=50,
        max_wall="3",
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "max_cli_reported_tokens"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["actuals"]["cli_reported"] == 60
    assert (
        receipt["attempts"][0]["limit_trigger"]
        == "max_cli_reported_tokens"
    )
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_positive_p3_exact_limit_natural_exit_is_accepted(
    tmp_path: Path,
) -> None:
    completed, receipt, _paths = _run_case(
        tmp_path,
        "cli_exact",
        max_calls=1,
        max_tokens=60,
        max_wall="3",
    )

    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "completed"
    assert receipt["actuals"]["model_calls"] == 1
    assert receipt["actuals"]["cli_reported"] == 60
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["accepted"] is True


def test_sigterm_ignoring_child_is_killed(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        max_wall="3",
        max_calls=100,
        max_tokens=100000,
    )
    env["FAKE_MODE"] = "sigterm_ignore"
    process = subprocess.Popen(
        command,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    child_pid_path = paths["pid_dir"] / "child.pid"
    deadline = time.monotonic() + 2
    while (
        not child_pid_path.exists()
        and process.poll() is None
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    child_pid_registered = child_pid_path.exists()
    stdout, stderr = process.communicate(timeout=10)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert child_pid_registered, (
        f"child.pid was not registered before deadline; stderr={stderr!r}"
    )
    assert process.returncode == 1, (stdout, stderr)
    assert receipt["stop_reason"] == "max_wall_clock_s"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] == "max_wall_clock_s"
    assert receipt["attempts"][0]["process_group_residual"] == 0
    assert receipt["possible_unobserved_overshoot"] is True
    child_pid = int(child_pid_path.read_text(encoding="ascii"))
    _assert_pid_gone(child_pid)
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_proc_scan_and_missing_identity_are_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_scan(_path: str) -> Any:
        raise OSError("synthetic /proc failure")

    assert LAUNCHER._group_member_count(None) is None
    monkeypatch.setattr(LAUNCHER.os, "scandir", fail_scan)
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )
    assert LAUNCHER._group_member_count(identity) is None


def test_individual_proc_read_failure_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Entry:
        name = str(os.getpid())

    class Entries:
        def __enter__(self) -> list[Entry]:
            return [Entry()]

        def __exit__(self, *_args: Any) -> None:
            return None

        def __iter__(self) -> Any:
            return iter([Entry()])

    monkeypatch.setattr(LAUNCHER.os, "scandir", lambda _path: Entries())
    monkeypatch.setattr(
        LAUNCHER.Path,
        "read_text",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("synthetic")),
    )
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )

    assert LAUNCHER._group_member_count(identity) is None


def test_unknown_residual_never_verifies_normal_reap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        def wait(self) -> int:
            return 0

    monkeypatch.setattr(
        LAUNCHER, "_group_member_count", lambda _identity: None
    )
    identity = LAUNCHER.PidIdentity(
        pid=os.getpid(), boot_id="synthetic", start_ticks=1
    )

    residual, verified = LAUNCHER._normal_reap(Process(), identity)

    assert residual is None
    assert verified is False


def test_cumulative_limits_do_not_reset_between_attempts(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        sandbox="read-only",
        max_attempts=2,
        max_calls=2,
        max_tokens=100000,
        max_wall="3",
    )
    env["FAKE_SEQUENCE"] = "retry_reject,retry_wait"
    completed = subprocess.run(
        command, env=env, text=True, capture_output=True, timeout=10
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert completed.returncode == 1, completed.stderr
    assert receipt["stop_reason"] == "max_model_calls"
    assert receipt["actuals"]["attempt_count"] == 2
    assert receipt["actuals"]["model_calls"] == 2
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][1]["limit_trigger"] == "max_model_calls"
    assert receipt["attempts"][1]["accepted"] is False
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_max_attempts_never_spawns_extra_attempt(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        sandbox="read-only",
        max_attempts=2,
        max_calls=100,
        max_tokens=100000,
        max_wall="3",
    )
    env["FAKE_MODE"] = "retry_reject"
    completed = subprocess.run(
        command, env=env, text=True, capture_output=True, timeout=10
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert completed.returncode == 1, completed.stderr
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 2
    assert paths["counter"].read_text(encoding="ascii") == "2"
    assert len(_leader_pids(paths)) == 2
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_workspace_write_retry_is_refused(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "normal",
        sandbox="workspace-write",
        max_attempts=2,
    )

    assert completed.returncode == 2
    assert receipt is None
    assert "read-only" in completed.stderr
    assert not paths["pid_dir"].exists()


def test_launcher_process_wall_clock_includes_version_preflight(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(
        tmp_path,
        fake=fake,
        max_wall="0.1",
    )
    env["FAKE_VERSION_DELAY"] = "0.2"
    env["FAKE_MODE"] = "normal"

    completed = subprocess.run(
        command, env=env, text=True, capture_output=True, timeout=10
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert completed.returncode == 2
    assert receipt["outcome"] == "launcher_error"
    assert (
        receipt["wall_clock_scope"]
        == "launcher_start_to_receipt_fields_finalized"
    )
    assert receipt["actuals"]["wall_clock_s"] >= 0.2
    assert receipt["attempts"] == []
    assert not paths["pid_dir"].exists()


def test_seal_failure_still_writes_launcher_error_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"

    def fail_seal(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise LAUNCHER.LaunchError("synthetic seal failure")

    monkeypatch.setattr(LAUNCHER, "_seal_attempt", fail_seal)
    rc = _run_main_in_process(command, env, monkeypatch)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert rc == 2
    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert not paths["output"].exists()


def test_post_attempt_audit_failure_still_writes_launcher_error_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"

    def fail_audit(*_args: Any, **_kwargs: Any) -> Any:
        raise LAUNCHER.LaunchError("synthetic audit failure")

    monkeypatch.setattr(LAUNCHER, "_audit_receipt_value", fail_audit)
    rc = _run_main_in_process(command, env, monkeypatch)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert rc == 2
    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert not paths["output"].exists()


def test_receipt_publication_failure_removes_output_and_writes_error_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "normal"
    original = LAUNCHER._atomic_create_json_reserved
    calls = 0

    def fail_once(*args: Any, **kwargs: Any) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("synthetic publication failure")
        original(*args, **kwargs)

    monkeypatch.setattr(
        LAUNCHER, "_atomic_create_json_reserved", fail_once
    )
    rc = _run_main_in_process(command, env, monkeypatch)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert rc == 2
    assert calls == 2
    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert not paths["output"].exists()


def test_help_does_not_claim_job_wide_hard_cap() -> None:
    completed = subprocess.run(
        [sys.executable, os.fspath(_LAUNCHER), "--help"],
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert completed.returncode == 0
    assert "hard cap" not in completed.stdout.lower()
    assert "launcher process" in completed.stdout


def test_parallel_jobs_preserve_both_manifest_entries(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    barrier = tmp_path / "barrier"
    first_command, first_env, first_paths = _base_command(
        tmp_path,
        fake=fake,
        job_id="job-a",
        suffix="-a",
    )
    second_command, second_env, second_paths = _base_command(
        tmp_path,
        fake=fake,
        job_id="job-b",
        suffix="-b",
    )
    for env in (first_env, second_env):
        env["FAKE_MODE"] = "normal"
        env["FAKE_BARRIER_DIR"] = os.fspath(barrier)
        env["FAKE_BARRIER_COUNT"] = "2"
    first = subprocess.Popen(
        first_command,
        env=first_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    second = subprocess.Popen(
        second_command,
        env=second_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    first_stdout, first_stderr = first.communicate(timeout=10)
    second_stdout, second_stderr = second.communicate(timeout=10)

    assert first.returncode == 0, (first_stdout, first_stderr)
    assert second.returncode == 0, (second_stdout, second_stderr)
    manifest = json.loads(
        first_paths["manifest"].read_text(encoding="utf-8")
    )
    assert [(item["job_id"], item["attempt_index"]) for item in manifest["sessions"]] == [
        ("job-a", 1),
        ("job-b", 1),
    ]
    assert first_paths["receipt"].exists()
    assert second_paths["receipt"].exists()


def test_manifest_lock_covers_load_replace_critical_section(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    first_inside = threading.Event()
    release_first = threading.Event()
    second_done = threading.Event()
    errors: list[BaseException] = []

    def first_hook() -> None:
        first_inside.set()
        assert release_first.wait(2)

    def append(job_id: str, session_id: str, hook: Any = None) -> None:
        try:
            LAUNCHER._append_manifest(
                manifest_path,
                wave_id="wave-a",
                repo_root=os.fspath(_ROOT),
                base_commit=_BASE_COMMIT,
                entry={
                    "job_id": job_id,
                    "attempt_index": 1,
                    "session_id": session_id,
                },
                critical_section_hook=hook,
            )
        except BaseException as exc:
            errors.append(exc)
        finally:
            if job_id == "job-b":
                second_done.set()

    first = threading.Thread(
        target=append,
        args=("job-a", "aaaaaaaa-0000-4000-8000-000000000001", first_hook),
    )
    second = threading.Thread(
        target=append,
        args=("job-b", "bbbbbbbb-0000-4000-8000-000000000002"),
    )
    first.start()
    assert first_inside.wait(2)
    second.start()
    assert not second_done.wait(0.2)
    release_first.set()
    first.join(2)
    second.join(2)

    assert errors == []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["job_id"] for item in manifest["sessions"]] == [
        "job-a",
        "job-b",
    ]


def test_complete_receipt_publication_is_atomic_create_only_at_run_callsite(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    barrier = tmp_path / "receipt-race"
    first_command, first_env, first_paths = _base_command(
        tmp_path, fake=fake, job_id="job-a", suffix="-a"
    )
    second_command, second_env, second_paths = _base_command(
        tmp_path, fake=fake, job_id="job-b", suffix="-b"
    )
    receipt_index = second_command.index("--receipt") + 1
    second_command[receipt_index] = os.fspath(first_paths["receipt"])
    second_paths["receipt"] = first_paths["receipt"]
    for env in (first_env, second_env):
        env["FAKE_MODE"] = "normal"
        env["FAKE_BARRIER_DIR"] = os.fspath(barrier)
        env["FAKE_BARRIER_COUNT"] = "2"
    first = subprocess.Popen(
        first_command,
        env=first_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    second = subprocess.Popen(
        second_command,
        env=second_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    first_output = first.communicate(timeout=10)
    second_output = second.communicate(timeout=10)

    assert sorted([first.returncode, second.returncode]) == [0, 2], (
        first_output,
        second_output,
    )
    receipt = json.loads(
        first_paths["receipt"].read_text(encoding="utf-8")
    )
    assert receipt["job_id"] in {"job-a", "job-b"}
    assert receipt["outcome"] == "accepted"
    winner_paths = (
        first_paths if receipt["job_id"] == "job-a" else second_paths
    )
    loser_paths = (
        second_paths if receipt["job_id"] == "job-a" else first_paths
    )
    assert winner_paths["output"].exists()
    assert not loser_paths["output"].exists()
    manifest = json.loads(
        first_paths["manifest"].read_text(encoding="utf-8")
    )
    # manifest は receipt の勝敗でなく、実際に費消した両 session を保持する。
    assert {item["job_id"] for item in manifest["sessions"]} == {
        "job-a",
        "job-b",
    }


def test_partial_receipt_never_visible_at_final_path(tmp_path: Path) -> None:
    final = tmp_path / "receipt.json"

    def crash(_temporary: Path) -> None:
        raise RuntimeError("synthetic crash before replace")

    with pytest.raises(RuntimeError, match="synthetic crash"):
        LAUNCHER._atomic_replace_json(
            final,
            {"schema_version": 1, "payload": "x" * 10000},
            before_replace=crash,
        )

    assert not final.exists()
    assert list(tmp_path.glob(".receipt.json.tmp.*")) == []


def test_check_receipt_detects_output_tampering(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None

    paths["output"].write_text("tampered", encoding="utf-8")
    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2


def test_check_receipt_marks_self_asserted_limits_and_accepts_external_expectations(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None

    self_checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    summary = json.loads(self_checked.stdout)
    assert self_checked.returncode == 0, self_checked.stderr
    assert summary["limits_self_asserted"] == [
        "max_wall_clock_s",
        "max_model_calls",
        "max_cli_reported_tokens",
        "max_attempts",
    ]
    exact = subprocess.run(
        _check_command(paths)
        + [
            "--expect-prompt-sha256",
            receipt["prompt_sha256"],
            "--expect-max-wall-clock-s",
            "3",
            "--expect-max-model-calls",
            "100",
            "--expect-max-cli-reported-tokens",
            "100000",
            "--expect-max-attempts",
            "1",
        ],
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert exact.returncode == 0, exact.stderr
    assert json.loads(exact.stdout)["limits_self_asserted"] == []


@pytest.mark.parametrize("legacy_field_set", [True, False])
def test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics(
    tmp_path: Path,
    legacy_field_set: bool,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    receipt["schema_version"] = 1
    if legacy_field_set:
        for field_name in (
            "limits_assertion",
            "wall_clock_scope",
            "manifest_repo_root",
            "manifest_base_commit",
        ):
            receipt.pop(field_name)
    else:
        receipt["wall_clock_scope"] = "launcher_process"
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    diagnostics = json.loads(checked.stdout)

    assert checked.returncode == 0, checked.stderr
    assert diagnostics["schema_version"] == 1
    assert len(diagnostics["compatibility_skips"]) == (
        4 if legacy_field_set else 0
    )
    if legacy_field_set:
        assert all(
            item.startswith("v1_missing_")
            and item.endswith("_check_skipped")
            for item in diagnostics["compatibility_skips"]
        )


def test_check_receipt_external_limit_detects_self_asserted_limit_tampering(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    receipt["limits"]["max_model_calls"] = 101
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    without_external = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    with_external = subprocess.run(
        _check_command(paths) + ["--expect-max-model-calls", "100"],
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert without_external.returncode == 0, without_external.stderr
    assert "max_model_calls" in json.loads(
        without_external.stdout
    )["limits_self_asserted"]
    assert with_external.returncode == 2


def test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    receipt["attempts"][0]["model_calls"] = 0
    receipt["actuals"]["model_calls"] = 0
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2
    assert "sealed artifact" in checked.stderr or "再計算" in checked.stderr


def test_check_receipt_recomputes_attempt_output_hash(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    Path(receipt["attempts"][0]["output_path"]).write_text(
        "tampered attempt output", encoding="utf-8"
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2


def test_manifest_refuses_foreign_wave_id(tmp_path: Path) -> None:
    first, receipt, paths = _run_case(tmp_path, "normal")
    assert first.returncode == 0, first.stderr
    assert receipt is not None
    fake = tmp_path / "fake-codex"
    command, env, second_paths = _base_command(
        tmp_path,
        fake=fake,
        job_id="job-foreign",
        wave_id="wave-foreign",
        suffix="-foreign",
    )
    env["FAKE_MODE"] = "normal"
    second = subprocess.run(
        command, env=env, text=True, capture_output=True, timeout=10
    )

    assert second.returncode == 2
    assert "manifest header" in second.stderr
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["wave_id"] == "wave-a"
    assert len(manifest["sessions"]) == 1
    assert not second_paths["receipt"].exists()
    assert not second_paths["pid_dir"].exists()


def test_preflight_rejects_cwd_outside_repo_and_unknown_base(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    outside_command, outside_env, outside_paths = _base_command(
        tmp_path, fake=fake, suffix="-outside"
    )
    outside_command[outside_command.index("--cwd") + 1] = os.fspath(tmp_path)
    outside_env["FAKE_MODE"] = "normal"
    outside = subprocess.run(
        outside_command,
        env=outside_env,
        text=True,
        capture_output=True,
        timeout=10,
    )

    unknown_command, unknown_env, unknown_paths = _base_command(
        tmp_path, fake=fake, suffix="-unknown"
    )
    unknown_command[unknown_command.index("--base-commit") + 1] = "f" * 40
    unknown_env["FAKE_MODE"] = "normal"
    unknown = subprocess.run(
        unknown_command,
        env=unknown_env,
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert outside.returncode == 2
    assert "--cwd" in outside.stderr
    assert not outside_paths["receipt"].exists()
    assert unknown.returncode == 2
    assert "--base-commit" in unknown.stderr
    assert not unknown_paths["receipt"].exists()


@pytest.mark.parametrize("field", ["wave_id", "repo_root", "base_commit"])
def test_check_receipt_rechecks_all_manifest_header_fields(
    tmp_path: Path,
    field: str,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    replacements = {
        "wave_id": "wave-tampered",
        "repo_root": "/tmp",
        "base_commit": "f" * 40,
    }
    manifest[field] = replacements[field]
    paths["manifest"].write_text(
        json.dumps(manifest, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )

    assert checked.returncode == 2


def test_append_manifest_header_gate_fails_without_checker_mask(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    LAUNCHER._append_manifest(
        manifest_path,
        wave_id="wave-a",
        repo_root=os.fspath(_ROOT),
        base_commit=_BASE_COMMIT,
        entry={
            "job_id": "job-a",
            "attempt_index": 1,
            "session_id": "aaaaaaaa-0000-4000-8000-000000000001",
        },
    )

    with pytest.raises(LAUNCHER.LaunchError, match="wave_id"):
        LAUNCHER._append_manifest(
            manifest_path,
            wave_id="wave-b",
            repo_root=os.fspath(_ROOT),
            base_commit=_BASE_COMMIT,
            entry={
                "job_id": "job-b",
                "attempt_index": 1,
                "session_id": "bbbbbbbb-0000-4000-8000-000000000002",
            },
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["job_id"] for item in manifest["sessions"]] == ["job-a"]


def test_inconsistent_metering_is_not_accepted(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(tmp_path, "inconsistent")

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["metering_status"] == "inconsistent"
    assert receipt["attempts"][0]["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_cli_reported_running_max_latches_usage_rollback(
    tmp_path: Path,
) -> None:
    completed, receipt, _paths = _run_case(
        tmp_path,
        "rollback",
        max_calls=100,
        max_tokens=100,
        max_wall="3",
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["cli_reported"] == 1000
    assert attempt["limit_trigger"] == "max_cli_reported_tokens"
    assert attempt["metering_status"] == "inconsistent"
    assert attempt["accepted"] is False


def test_usage_rollback_alone_is_rejected_without_peak_or_terminal_mask(
    tmp_path: Path,
) -> None:
    completed, receipt, _paths = _run_case(
        tmp_path,
        "rollback_equal_cli",
        max_calls=100,
        max_tokens=100000,
        max_wall="3",
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["cli_reported"] == 100
    assert attempt["limit_trigger"] is None
    assert attempt["metering_status"] == "inconsistent"
    assert attempt["accepted"] is False
    assert receipt["stop_reason"] == "max_attempts"


def test_null_token_count_is_observed_and_makes_metering_incomplete(
    tmp_path: Path,
) -> None:
    completed, receipt, _paths = _run_case(
        tmp_path,
        "null_info",
        max_calls=100,
        max_tokens=100000,
        max_wall="3",
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    attempt = receipt["attempts"][0]
    assert attempt["model_calls"] == 2
    assert attempt["metering_status"] == "incomplete"
    assert attempt["limit_trigger"] is None
    assert attempt["accepted"] is False
    assert receipt["possible_unobserved_overshoot"] is True


def test_delayed_thread_and_rollout_are_read_from_byte_zero(
    tmp_path: Path,
) -> None:
    completed, receipt, _paths = _run_case(tmp_path, "delayed_thread")

    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "completed"
    assert receipt["actuals"]["model_calls"] == 1
    assert receipt["attempts"][0]["evidence_status"] == "complete"


def test_manifest_is_appended_while_correlated_session_is_running(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    env["FAKE_MODE"] = "manifest_while_running"
    process = subprocess.Popen(
        command,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + 3
    manifest: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        if paths["manifest"].exists():
            manifest = json.loads(
                paths["manifest"].read_text(encoding="utf-8")
            )
            if manifest["sessions"]:
                break
        time.sleep(0.01)

    assert manifest is not None and len(manifest["sessions"]) == 1
    leader_pid = int(
        next(paths["pid_dir"].glob("leader-*.pid")).read_text(
            encoding="ascii"
        )
    )
    assert Path(f"/proc/{leader_pid}").exists()
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0, (stdout, stderr)


def test_spawned_process_group_is_cleaned_on_manifest_append_failure(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "id_change_wait")

    assert completed.returncode == 2
    assert receipt is not None
    assert receipt["outcome"] == "launcher_error"
    assert receipt["launcher_rc"] == 2
    assert receipt["attempts"][0]["accepted"] is False
    child_pid = int((paths["pid_dir"] / "child.pid").read_text(encoding="ascii"))
    _assert_pid_gone(child_pid)
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_final_drain_actuals_are_rechecked_before_acceptance(
    tmp_path: Path,
) -> None:
    completed, receipt, _paths = _run_case(
        tmp_path,
        "final_drain",
        max_calls=100,
        max_tokens=100,
        max_wall="3",
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["actuals"]["cli_reported"] == 110
    assert receipt["attempts"][0]["limit_trigger"] == (
        "max_cli_reported_tokens"
    )
    assert receipt["attempts"][0]["accepted"] is False
    assert not _paths["output"].exists()


def test_fake_stdout_matches_observed_cli_event_shape(tmp_path: Path) -> None:
    completed, receipt, _paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    events = [
        json.loads(line)
        for line in Path(
            receipt["attempts"][0]["stdout_path"]
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert {"turn.started", "item.started", "item.completed"} <= {
        event["type"] for event in events
    }
    terminal = [event for event in events if event["type"] == "turn.completed"]
    assert terminal[0]["usage"]["cache_write_input_tokens"] == 0


def test_rollout_missing_after_grace_is_stopped_and_not_accepted(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "no_rollout",
        max_wall="3",
        max_calls=100,
        max_tokens=100000,
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["limit_trigger"] is None
    assert receipt["attempts"][0]["evidence_status"] == "missing"
    assert receipt["attempts"][0]["accepted"] is False
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_thread_missing_after_grace_kills_process_group(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(
        tmp_path,
        "no_thread",
        max_wall="3",
        max_calls=100,
        max_tokens=100000,
    )

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["actuals"]["attempt_count"] == 1
    assert receipt["attempts"][0]["evidence_status"] == "missing"
    child_pid = int((paths["pid_dir"] / "child.pid").read_text(encoding="ascii"))
    _assert_pid_gone(child_pid)
    for pid in _leader_pids(paths):
        _assert_pid_gone(pid)


def test_cached_exceeding_input_is_malformed(tmp_path: Path) -> None:
    completed, receipt, _paths = _run_case(tmp_path, "cached_bad")

    assert completed.returncode == 1, completed.stderr
    assert receipt is not None
    assert receipt["stop_reason"] == "max_attempts"
    assert receipt["attempts"][0]["evidence_status"] == "invalid"
    assert receipt["attempts"][0]["metering_status"] == "incomplete"
    assert receipt["attempts"][0]["accepted"] is False


def test_late_rollout_writer_does_not_change_sealed_receipt(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "late_writer")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    rollout = receipt["attempts"][0]["rollouts"][0]
    sealed_bytes = rollout["bytes"]
    deadline = time.monotonic() + 3
    while (
        Path(rollout["path"]).stat().st_size == sealed_bytes
        and time.monotonic() < deadline
    ):
        time.sleep(0.02)
    assert Path(rollout["path"]).stat().st_size > sealed_bytes

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["rollout_grew_since_seal"] is True
    late_pid = int((paths["pid_dir"] / "late.pid").read_text(encoding="ascii"))
    _assert_pid_gone(late_pid)


def test_setsid_escape_is_not_claimed_as_contained(tmp_path: Path) -> None:
    completed, receipt, paths = _run_case(tmp_path, "setsid_escape")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    assert receipt["escaped_process_containment"] == "not_attempted"
    escaped_pid = int(
        (paths["pid_dir"] / "escaped.pid").read_text(encoding="ascii")
    )
    assert Path(f"/proc/{escaped_pid}").exists()
    os.kill(escaped_pid, signal.SIGKILL)
    _assert_pid_gone(escaped_pid)


def test_check_receipt_rejects_unknown_and_duplicate_fields(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None

    unknown = dict(receipt)
    unknown["unexpected"] = True
    paths["receipt"].write_text(
        json.dumps(unknown, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    checked_unknown = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked_unknown.returncode == 2

    raw = json.dumps(receipt, separators=(",", ":"))
    duplicate = raw[:-1] + ',"schema_version":1}\n'
    paths["receipt"].write_text(duplicate, encoding="utf-8")
    checked_duplicate = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked_duplicate.returncode == 2


def test_check_receipt_rejects_impossible_truth_table(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    receipt["attempts"][0]["limit_trigger"] = "max_model_calls"
    paths["receipt"].write_text(
        json.dumps(receipt, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 2


def test_check_receipt_detects_executable_identity_change(
    tmp_path: Path,
) -> None:
    completed, receipt, paths = _run_case(tmp_path, "normal")
    assert completed.returncode == 0, completed.stderr
    assert receipt is not None
    with (tmp_path / "fake-codex").open("a", encoding="utf-8") as stream:
        stream.write("\n# changed after receipt\n")

    checked = subprocess.run(
        _check_command(paths), text=True, capture_output=True, timeout=10
    )
    assert checked.returncode == 2


def test_partial_existing_receipt_is_atomically_replaced(
    tmp_path: Path,
) -> None:
    fake = _write_fake_codex(tmp_path / "fake-codex")
    command, env, paths = _base_command(tmp_path, fake=fake)
    paths["receipt"].write_bytes(b'{"schema_version":')
    env["FAKE_MODE"] = "normal"

    completed = subprocess.run(
        command, env=env, text=True, capture_output=True, timeout=10
    )
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert receipt["outcome"] == "accepted"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda manifest: manifest.update({"sessions": []}),
        lambda manifest: manifest["sessions"][0].update(
            {"attempt_index": True}
        ),
        lambda manifest: manifest["sessions"][0].update({"unknown": 1}),
        lambda manifest: manifest["sessions"][0].update(
            {"session_id": manifest["sessions"][0]["session_id"].upper()}
        ),
    ],
)
def test_frozen_manifest_schema_is_closed(
    mutate: Any,
) -> None:
    manifest = {
        "schema_version": 1,
        "wave_id": "wave-a",
        "repo_root": os.fspath(_ROOT),
        "base_commit": "a" * 40,
        "sessions": [
            {
                "job_id": "job-a",
                "attempt_index": 1,
                "session_id": "aaaaaaaa-0000-4000-8000-000000000001",
            }
        ],
    }
    mutate(manifest)

    with pytest.raises(LAUNCHER.LaunchError):
        LAUNCHER._validate_manifest(manifest)


def test_fake_can_reproduce_thread_id_change_and_multiple_sessions(
    tmp_path: Path,
) -> None:
    # 凍結 manifest は (job_id, attempt_index) を一意にするため、複数
    # session を receipt/manifest に同時表現できず launcher integrity error になる。
    completed, receipt, paths = _run_case(tmp_path, "id_change")

    assert completed.returncode == 2
    assert receipt is not None
    assert receipt["outcome"] == "launcher_error"
    assert receipt["stop_reason"] == "launcher_error"
    assert len(receipt["attempts"][0]["session_ids"]) == 2
    assert receipt["attempts"][0]["accepted"] is False
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert len(manifest["sessions"]) == 1
    assert len(list((paths["codex_home"] / "sessions").rglob("rollout-*.jsonl"))) == 2


def _run() -> int:
    """pytest fixture/parametrize を含む全 node を直接起動でも実走する。"""
    return int(pytest.main(["-q", os.fspath(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
