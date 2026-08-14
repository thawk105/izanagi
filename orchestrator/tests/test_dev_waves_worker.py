"""Real-process tests for the fake-only dev-wave worker."""
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from unittest import mock
from decimal import Decimal
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from tools.dev_waves.receipt import load_receipt_schema
from tools.dev_waves.schema import DevWavesError, ReasonCode, WorkerSpec, canonical_bytes
from tools.dev_waves.worker import (
    PidIdentity,
    build_child_argv,
    load_worker_spec,
    pid_identity_digest,
    read_pid_identity,
    run_worker,
    spawn_worker,
    terminate_verified_group,
)
import tools.dev_waves.worker as worker_mod


def _fake(root: Path, body: str) -> Path:
    path = root / "fake.py"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os,resource,signal,sys,time\n"
        "if sys.argv[1:2] == ['--dev-waves-fake-handshake']:\n"
        " print('dev-waves-fake/v1 '+sys.argv[2]); raise SystemExit(0)\n" + body,
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _spec(root: Path, fake: Path, *, effort: str = "high", timeout: int = 3,
          output_cap: int = 100_000, file_cap: int = 100_000) -> WorkerSpec:
    schema_text = canonical_bytes(load_receipt_schema()).decode("utf-8")
    return WorkerSpec(
        1, "run-1", 1, str(fake), hashlib.sha256(fake.read_bytes()).hexdigest(),
        str(root), (("PATH", os.environ.get("PATH", "/usr/bin")),),
        "claude-test-20260721", effort, str(root), str(root / "manifest.json"),
        schema_text, hashlib.sha256(schema_text.encode()).hexdigest(), Decimal("1"),
        timeout, output_cap, file_cap, str(root / "stdout.json"),
        str(root / "stderr.log"), str(root / "child-start.json"),
        str(root / "worker-exit.json"),
    )


def _fresh_dir() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="test-dev-waves-worker-")


def _group_live(pgid: int) -> bool:
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "stat").read_text()
            fields = raw[raw.rfind(")") + 2:].split()
            if int(fields[2]) == pgid and fields[0] != "Z":
                return True
        except (OSError, ValueError, IndexError):
            pass
    return False


def test_exact_argv_comes_from_schema_grammar_and_has_no_forbidden_token():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        spec = _spec(root, _fake(root, "print('{}',end='')\n"))
        argv = build_child_argv(spec)
        assert argv[0] == "-p" and argv[-1].endswith(str(root / "manifest.json"))
        assert len(argv) == 9
        assert "--continue" not in argv and "--dangerously-skip-permissions" not in argv


def test_persisted_unknown_effort_is_rejected_by_child_argv_path():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        spec_path = root / "worker-spec.json"
        spec_path.write_bytes(canonical_bytes(
            _spec(root, _fake(root, "print('{}',end='')\n"), effort="none")
        ))
        try:
            build_child_argv(load_worker_spec(spec_path))
        except DevWavesError as exc:
            assert exc.code is ReasonCode.INVALID_ARGS
            assert exc.detail == {"label": "effort", "kind": "unknown"}
        else:
            raise AssertionError("child argv path accepted persisted unknown effort")


def test_sigstop_identity_is_durable_before_fake_exec_and_environment_is_closed():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        marker = root / "invoked.json"
        fake = _fake(root,
            f"assert 'CLAUDECODE' not in os.environ\n"
            f"p={str(marker)!r}\n"
            "with open(p,'w') as f:\n"
            " json.dump({'pid':os.getpid(),'start':open('/proc/self/stat').read().rsplit(') ',1)[1].split()[19]},f); f.flush(); os.fsync(f.fileno())\n"
            "print('{}',end='')\n")
        os.environ["CLAUDECODE"] = "1"
        try:
            result = run_worker(_spec(root, fake), termination_grace_s=0.05)
        finally:
            os.environ.pop("CLAUDECODE", None)
        start = json.loads((root / "child-start.json").read_text())
        invoked = json.loads(marker.read_text())
        assert result.reason is None and start["pid"] == invoked["pid"]
        assert str(start["start_ticks"]) == invoked["start"]
        assert (root / "child-start.json").stat().st_mtime_ns <= marker.stat().st_mtime_ns


def _slow_child_stop(seconds: float):
    """Widen the window between the child closing its exec pipe and stopping.

    ``Popen`` returns once ``_preexec`` has closed the exec-error pipe, several
    statements before it raises ``SIGSTOP`` on itself.  Delaying only the
    child's own stop makes that window deterministic without changing when the
    parent is released, which is exactly the race the parent must survive.
    """
    parent = os.getpid()
    real_kill = os.kill

    def slow_kill(pid: int, sig: int) -> None:
        if os.getpid() != parent and sig == signal.SIGSTOP:
            time.sleep(seconds)
        return real_kill(pid, sig)

    return mock.patch.object(worker_mod.os, "kill", slow_kill)


def test_cont_waits_for_the_child_to_be_observed_stopped():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root, "print('{}',end='')\n")
        with _slow_child_stop(1.0):
            result = run_worker(_spec(root, fake), termination_grace_s=0.05)
        # Without the wait the SIGCONT lands before the stop, is discarded, and
        # the child sits stopped with no output until the wave deadline.
        assert result.reason is None, result.reason
        assert result.timed_out is False and result.stdout_bytes == 2
        assert (root / "stdout.json").read_text() == "{}"


def test_observed_stop_precedes_every_cont_signal():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root, "print('{}',end='')\n")
        order: list[str] = []
        real_await = worker_mod._await_stopped_child
        real_kill = os.kill
        parent = os.getpid()

        def recording_await(identity, *args, **kwargs):
            state = real_await(identity, *args, **kwargs)
            order.append(f"observed:{state}")
            return state

        def recording_kill(pid: int, sig: int) -> None:
            if os.getpid() == parent and sig == signal.SIGCONT:
                order.append("cont")
            elif os.getpid() != parent and sig == signal.SIGSTOP:
                time.sleep(0.2)
            return real_kill(pid, sig)

        with mock.patch.object(worker_mod, "_await_stopped_child", recording_await), \
                mock.patch.object(worker_mod.os, "kill", recording_kill):
            result = run_worker(_spec(root, fake), termination_grace_s=0.05)
        assert result.reason is None, result.reason
        assert order == ["observed:T", "cont"], order


def test_stop_handshake_is_bounded_and_fails_closed_when_no_stop_arrives():
    identity = PidIdentity(os.getpid(), "boot-a", 1)
    with mock.patch.object(worker_mod, "_verified_state", return_value="R"):
        started = time.monotonic()
        try:
            worker_mod._await_stopped_child(identity, timeout_s=0.05)
        except DevWavesError as exc:
            elapsed = time.monotonic() - started
            assert exc.code is ReasonCode.AMBIGUOUS_RECOVERY
            assert exc.detail["kind"] == "stop-handshake-timeout"
            assert elapsed < 5.0, elapsed
        else:
            raise AssertionError("a child that never stops was resumed")


def test_stop_handshake_rejects_a_child_whose_identity_stopped_matching():
    with mock.patch.object(worker_mod, "_verified_state", return_value=None):
        try:
            worker_mod._await_stopped_child(PidIdentity(os.getpid(), "boot-a", 1))
        except DevWavesError as exc:
            assert exc.code is ReasonCode.AMBIGUOUS_RECOVERY
            assert exc.detail["kind"] == "identity-mismatch-before-cont"
        else:
            raise AssertionError("an unverified pid was resumed")


def test_child_that_died_before_stopping_is_not_signalled():
    for state in ("Z", "X"):
        killed = []
        real_kill = os.kill

        def recording_kill(pid: int, sig: int) -> None:
            killed.append(sig)
            return real_kill(pid, sig)

        with mock.patch.object(worker_mod, "_verified_state", return_value=state), \
                mock.patch.object(worker_mod.os, "kill", recording_kill):
            worker_mod._signal_cont_verified(PidIdentity(os.getpid(), "boot-a", 1))
        assert killed == [], (state, killed)


def test_verified_state_reads_state_and_identity_from_one_stat():
    process = subprocess.Popen(
        ["/bin/sleep", "5"], start_new_session=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        identity = read_pid_identity(process.pid)
        # A just-spawned child is running or sleeping; neither is a stop.
        assert worker_mod._verified_state(identity) in ("R", "S", "D")
        os.kill(process.pid, signal.SIGSTOP)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if worker_mod._verified_state(identity) == "T":
                break
            time.sleep(0.005)
        assert worker_mod._verified_state(identity) == "T"
        reused = PidIdentity(identity.pid, identity.boot_id, identity.start_ticks + 1)
        assert worker_mod._verified_state(reused) is None
        assert worker_mod._verified_state(
            PidIdentity(identity.pid, "0" * 36, identity.start_ticks)
        ) is None
    finally:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def test_a_child_that_never_led_its_own_group_is_never_signalled():
    """The PID must also be the PGID before any group-wide signal.

    ``_preexec`` calls ``setpgid(0, 0)`` before it stops, so a verified child
    always leads its own group.  Without that binding the recorded PID doubles
    as a PGID that belongs to somebody else, and resuming or terminating
    "the child" would signal an unrelated group.
    """
    process = subprocess.Popen(
        ["/bin/sleep", "5"], start_new_session=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        identity = read_pid_identity(process.pid)
        _state, pgid, _start = worker_mod._proc_stat(process.pid)
        assert pgid != process.pid, "fixture failed to inherit a foreign group"
        assert worker_mod._verified_state(identity) is None
        assert worker_mod._identity_matches(identity) is False
        assert terminate_verified_group(identity, 0.01) is False
        assert process.poll() is None
    finally:
        process.kill()
        process.wait()


def test_worker_process_spawn_is_noninteractive_and_runs_one_spec():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root, "print('{}',end='')\n")
        spec = _spec(root, fake)
        spec_path = root / "worker-spec.json"
        spec_path.write_bytes(canonical_bytes(spec))
        process = spawn_worker(spec_path, termination_grace_s=0.05)
        assert process.wait(timeout=5) == 0
        assert (root / "worker-exit.json").exists()
        assert (root / "stdout.json").read_text() == "{}"


def test_worker_process_spawn_forces_no_bytecode_environment() -> None:
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root, "print('{}',end='')\n")
        spec_path = root / "worker-spec.json"
        spec_path.write_bytes(canonical_bytes(_spec(root, fake)))
        captured = []

        def capture(*args, **kwargs):
            captured.append((args, kwargs))
            return object()

        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(worker_mod.subprocess, "Popen", side_effect=capture):
            worker_mod.spawn_worker(spec_path, termination_grace_s=0.05)
        environment = captured.pop()[1]["env"]
        assert environment["PYTHONDONTWRITEBYTECODE"] == "1"


def test_worker_and_child_popen_flags_include_containment_preexec() -> None:
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root, "print('{}',end='')\n")
        spec = _spec(root, fake)
        captured = []

        def capture(*args, **kwargs):
            captured.append((args, kwargs))
            return object()

        with mock.patch.object(worker_mod.subprocess, "Popen", side_effect=capture):
            worker_mod._spawn_stopped(spec, 9)
        child = captured.pop()[1]
        assert child["shell"] is False and child["stdin"] is subprocess.DEVNULL
        assert child["close_fds"] is True and child["start_new_session"] is False
        assert child["pass_fds"] == (9,) and callable(child["preexec_fn"])

        spec_path = root / "worker-spec.json"
        spec_path.write_bytes(canonical_bytes(spec))
        with mock.patch.object(worker_mod.subprocess, "Popen", side_effect=capture):
            worker_mod.spawn_worker(spec_path, termination_grace_s=0.05)
        wrapper = captured.pop()[1]
        assert wrapper["shell"] is False and wrapper["stdin"] is subprocess.DEVNULL
        assert wrapper["close_fds"] is True and wrapper["start_new_session"] is True
        assert callable(wrapper["preexec_fn"])


def test_fake_handshake_rejects_version_style_response_before_child_spawn():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = root / "not-fake.py"
        fake.write_text("#!/usr/bin/env python3\nprint('2.1.214')\n", encoding="utf-8")
        fake.chmod(0o700)
        try:
            run_worker(_spec(root, fake))
        except DevWavesError as exc:
            assert exc.code is ReasonCode.FAKE_HANDSHAKE_FAILED
        else:
            raise AssertionError("version-like executable was accepted")
        assert not (root / "child-start.json").exists()
        record = json.loads((root / "worker-exit.json").read_text())
        assert record["child"] is None
        assert record["reason"] == ReasonCode.FAKE_HANDSHAKE_FAILED.value


def test_typed_pid_identity_digest_binds_every_field() -> None:
    base = PidIdentity(123, "boot-a", 456)
    digests = {
        pid_identity_digest(base),
        pid_identity_digest(PidIdentity(124, base.boot_id, base.start_ticks)),
        pid_identity_digest(PidIdentity(base.pid, "boot-b", base.start_ticks)),
        pid_identity_digest(PidIdentity(base.pid, base.boot_id, 457)),
    }
    assert len(digests) == 4


def test_pid_reuse_mismatch_causes_no_signal():
    process = subprocess.Popen(
        ["/bin/sleep", "5"], start_new_session=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        identity = read_pid_identity(process.pid)
        wrong = PidIdentity(identity.pid, identity.boot_id, identity.start_ticks + 1)
        assert terminate_verified_group(wrong, 0.01) is False
        assert process.poll() is None
    finally:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def test_timeout_sends_term_then_kill_to_verified_process_group():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root,
            "child=os.fork()\n"
            "if child==0:\n"
            " signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30); raise SystemExit\n"
            "signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)\n")
        result = run_worker(_spec(root, fake, timeout=1), termination_grace_s=0.05)
        assert result.reason is ReasonCode.TIMEOUT and result.timed_out
        assert result.child is not None and not _group_live(result.child.pid)


def test_timeout_still_applies_after_child_closes_both_output_pipes():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root, "os.close(1); os.close(2); time.sleep(30)\n")
        started = time.monotonic()
        result = run_worker(_spec(root, fake, timeout=1), termination_grace_s=0.05)
        assert result.reason is ReasonCode.TIMEOUT
        assert time.monotonic() - started < 2


def test_leader_exit_with_live_group_is_rejected_and_group_terminated():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root,
            "child=os.fork()\n"
            "if child==0:\n"
            " os.close(1); os.close(2); time.sleep(30); raise SystemExit\n"
            "print('{}',end='')\n")
        result = run_worker(_spec(root, fake), termination_grace_s=0.05)
        assert result.process_group_residual and result.reason is ReasonCode.NONZERO_EXIT
        assert result.child is not None and not _group_live(result.child.pid)


def test_rlimit_fsize_is_measured_in_child():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        target = root / "large.bin"
        fake = _fake(root,
            f"p={str(target)!r}\n"
            "try:\n"
            " open(p,'wb').write(b'x'*10000)\n"
            "except OSError:\n"
            " pass\n"
            "print('{}',end='')\n")
        result = run_worker(_spec(root, fake, file_cap=1024), termination_grace_s=0.05)
        assert target.stat().st_size <= 1024
        assert result.return_code in (0, -signal.SIGXFSZ)


def test_stdout_stderr_have_one_combined_cap():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root,
            "os.write(1,b'a'*8000); os.write(2,b'b'*8000); time.sleep(.2)\n")
        result = run_worker(_spec(root, fake, output_cap=4096), termination_grace_s=0.05)
        assert result.log_limit_exceeded and result.reason is ReasonCode.LOG_LIMIT
        assert result.stdout_bytes + result.stderr_bytes == 4096


def test_stdout_stderr_combined_cap_minus_exact_plus_one_boundaries():
    cap = 4096
    for total, limited in ((cap - 1, False), (cap, False), (cap + 1, True)):
        with _fresh_dir() as tmp:
            root = Path(tmp)
            fake = _fake(root, f"os.write(1,b'a'*{total // 2}); os.write(2,b'b'*{total - total // 2})\n")
            result = run_worker(_spec(root, fake, output_cap=cap), termination_grace_s=0.05)
            assert result.log_limit_exceeded is limited
            assert result.stdout_bytes + result.stderr_bytes == min(total, cap)


def test_crash_injection_before_cont_leaves_only_stopped_inactive_child():
    for point, child_start_expected in (
        ("before-spawn", False), ("after-spawn", False),
        ("before-identity-fsync", False), ("after-identity-fsync", True),
    ):
        with _fresh_dir() as tmp:
            root = Path(tmp)
            marker = root / "body-ran"
            fake = _fake(root, f"open({str(marker)!r},'w').write('bad')\n")
            crash_info = root / "crash-info"
            worker_pid = os.fork()
            if worker_pid == 0:
                signal.signal(signal.SIGHUP, signal.SIG_IGN)
                def crash(observed: str) -> None:
                    if observed == point:
                        children = Path(
                            f"/proc/self/task/{os.getpid()}/children"
                        ).read_text().strip()
                        with crash_info.open("w") as output:
                            output.write(children)
                            output.flush()
                            os.fsync(output.fileno())
                        os._exit(73)
                try:
                    run_worker(_spec(root, fake), termination_grace_s=0.05, crash_hook=crash)
                except BaseException:
                    os._exit(74)
                os._exit(75)
            waited, status = os.waitpid(worker_pid, 0)
            assert waited == worker_pid and os.WIFEXITED(status)
            assert os.WEXITSTATUS(status) == 73
            child_text = crash_info.read_text().strip()
            deadline = time.monotonic() + 0.5
            while time.monotonic() < deadline:
                assert not marker.exists()
                time.sleep(0.01)
            assert (root / "child-start.json").exists() is child_start_expected
            if child_text:
                # worker 死亡で child の process group は孤児化し、SIGSTOP 中の
                # メンバーには POSIX 規定で SIGHUP+SIGCONT が配送される。したがって
                # 「exec 前で停止したまま残る」か「kernel に回収されて消える」の
                # 両方が正しい終状態 — どちらでも payload 非実行が不変条件。
                child_pid = int(child_text.split()[0])
                try:
                    raw = Path(f"/proc/{child_pid}/stat").read_text()
                except FileNotFoundError:
                    raw = None
                if raw is not None:
                    fields = raw[raw.rfind(")") + 2:].split()
                    assert fields[0] in ("Z", "X")
                    try:
                        os.killpg(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                assert not marker.exists()


def test_worker_exit_is_create_only_and_parent_directory_fsynced():
    with _fresh_dir() as tmp:
        root = Path(tmp)
        fake = _fake(root, "print('{}',end='')\n")
        spec = _spec(root, fake)
        (root / "worker-exit.json").write_text("sentinel", encoding="utf-8")
        try:
            run_worker(spec, termination_grace_s=0.05)
        except FileExistsError:
            pass
        else:
            raise AssertionError("worker exit was replaced")
        assert (root / "worker-exit.json").read_text() == "sentinel"


def _run():
    functions = [value for name, value in sorted(globals().items())
                 if name.startswith("test_") and callable(value)]
    passed = failed = errors = 0
    for function in functions:
        try:
            function()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {function.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {function.__name__}:")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed, {errors} errors (of {len(functions)})")
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
