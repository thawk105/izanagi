"""Independent-order tests for the dev-wave checker."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from tools.dev_waves.checker import (
    CheckSpec,
    VerificationInput,
    extract_latest_next_action_ids,
    run_check_specs,
    verify_task_run_finished,
    verify_wave,
)
from tools.dev_waves.git_state import snapshot_repo
from tools.dev_waves.schema import ReasonCode, canonical_bytes
from tools.task_runs import finish_run, init_pilot, start_run


def _git(repo: Path, *args: str) -> str:
    env = dict(os.environ)
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})
    result = subprocess.run(
        ["git", *args], cwd=repo, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode == 0, (args, result.stderr)
    return result.stdout.strip()


def _fresh() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="test-dev-waves-checker-")


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_bytes(value) + b"\n")


def _rebind_stdout_size(spec: VerificationInput) -> None:
    exit_path = Path(spec.worker_exit_path)
    exit_record = json.loads(exit_path.read_text(encoding="utf-8"))
    exit_record["stdout_bytes"] = Path(spec.stdout_path).stat().st_size
    _write_json(exit_path, exit_record)


def _fixture(
    root: Path, *, probe_marker: Path | None = None, mutate_main: bool = False,
) -> VerificationInput:
    repo = root / "repo"
    _git(root, "init", "-b", "main", str(repo))
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / ".gitignore").write_text("\n", encoding="utf-8")
    (repo / "tools").mkdir()
    shutil.copytree(_ROOT / "tools" / "task_runs", repo / "tools" / "task_runs")
    (repo / "tools/check_docs.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (repo / "tools/run_tests.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    (repo / "tools/task_run_check.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    if probe_marker is not None or mutate_main:
        target = (repo / "outside.txt") if mutate_main else probe_marker
        assert target is not None
        (repo / "tools/check_probe.py").write_text(
            f"from pathlib import Path\nPath({str(target)!r}).write_text('ran')\n",
            encoding="utf-8",
        )
    (repo / "orchestrator/tests").mkdir(parents=True)
    (repo / "orchestrator/tests/test_guard.py").write_text("def test_guard(): assert True\n")
    (repo / "docs/handoff").mkdir(parents=True)
    (repo / "docs/handoff/README.md").write_text("handoff\n")
    before_worklog = "## 2026-07-21 before\n\n### 次の一手\n\n1. [T-076] selected\n"
    (repo / "docs/worklog.md").write_text(before_worklog)
    (repo / "base.txt").write_text("base\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    before = _git(repo, "rev-parse", "HEAD")
    before_snapshot = snapshot_repo(repo)

    task_root = repo / "output/task-runs"
    init_pilot(task_root)
    task_id = start_run(
        task_root, slug="child", objective="fixture", task_class=2,
        task_kind="implementation",
    )
    finish_run(task_root, task_id, "completed")
    (repo / "docs/worklog.md").write_text(
        before_worklog +
        "\n## 2026-07-21 after\n\n### 次の一手\n\n1. [T-077] continue\n",
        encoding="utf-8",
    )
    (repo / "base.txt").write_text("landed\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "land wave")
    after = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "wave/run-1", after)

    runtime = root / "runtime"
    runtime.mkdir()
    start_record = {"pid": 12345, "boot_id": "boot-fixture", "start_ticks": 99, "pgid": 12345}
    exit_record = {
        "child": {"pid": 12345, "boot_id": "boot-fixture", "start_ticks": 99},
        "return_code": 0, "reason": None, "timed_out": False,
        "log_limit_exceeded": False, "process_group_residual": False,
        "stdout_bytes": 1, "stderr_bytes": 0,
        "started_boottime_ns": 1, "finished_boottime_ns": 2,
    }
    _write_json(runtime / "child-start.json", start_record)
    _write_json(runtime / "worker-exit.json", exit_record)
    receipt = {
        "schema_version": 1, "supervisor_run_id": "run-1", "wave_index": 1,
        "outcome": "completed", "stop_reason": "wave-completed",
        "base_main_sha": before, "landed_main_sha": after,
        "selected_task_ids": ["T-076"], "next_task_ids": ["T-077"],
        "landed_commits": [after], "child_task_run_id": task_id,
    }
    envelope = {
        "type": "result", "subtype": "success", "is_error": False,
        "permission_denials": [], "result": "ignore this prose",
        "total_cost_usd": 0, "structured_output": receipt,
    }
    _write_json(runtime / "stdout.json", envelope)
    (runtime / "stderr.log").write_bytes(b"")
    exit_record["stdout_bytes"] = (runtime / "stdout.json").stat().st_size
    _write_json(runtime / "worker-exit.json", exit_record)
    (runtime / "git-trace.jsonl").write_bytes(b"")
    checks = [CheckSpec("docs", (sys.executable, "tools/check_docs.py"), 5)]
    if probe_marker is not None or mutate_main:
        checks.append(CheckSpec("probe", (sys.executable, "tools/check_probe.py"), 5))
    return VerificationInput(
        "run-1", 1, str(repo), str(repo), str(repo), "wave/run-1",
        before, before_snapshot, str(runtime / "stdout.json"), str(runtime / "stderr.log"), 100_000,
        str(runtime / "child-start.json"), str(runtime / "worker-exit.json"),
        str(runtime / "git-trace.jsonl"), Decimal("1"), ("T-076",),
        hashlib.sha256(before_worklog.encode()).hexdigest(),
        str(repo / "docs/worklog.md"), str(task_root), str(repo / "docs/handoff"),
        tuple(checks), time.clock_gettime_ns(time.CLOCK_BOOTTIME) + 10_000_000_000,
        (("schema", "same"),), (("schema", "same"),),
    )


def test_extract_latest_next_action_ids_is_ordered_strict_and_latest_only():
    text = (
        "## old\n### 次の一手\n1. [T-001] old\n"
        "## new\n### 次の一手\n1. [T-010] first\n2. [T-011] second\n"
    )
    assert extract_latest_next_action_ids(text) == ("T-010", "T-011")
    try:
        extract_latest_next_action_ids("## bad\n### 次の一手\n1. missing\n")
    except ValueError:
        pass
    else:
        raise AssertionError("non-ID next action was accepted")


def test_fully_valid_wave_runs_active_checks_in_isolated_checkout():
    with _fresh() as tmp:
        marker = Path(tmp) / "probe-ran"
        spec = _fixture(Path(tmp), probe_marker=marker)
        report = verify_wave(spec)
        assert report.ok, report.findings
        assert report.reason is None and report.active_checks_started
        assert marker.read_text() == "ran"
        assert all(item.status == "pass" for item in report.findings)


def test_any_passive_failure_prevents_every_active_subprocess():
    with _fresh() as tmp:
        marker = Path(tmp) / "must-not-run"
        spec = _fixture(Path(tmp), probe_marker=marker)
        Path(spec.main_worktree, "untracked.txt").write_text("dirty\n")
        report = verify_wave(spec)
        assert report.reason is ReasonCode.MAIN_DIRTY
        assert not report.active_checks_started and not marker.exists()
        assert next(item for item in report.findings if item.name == "fixed-checks").status == "not-evaluated"


def test_first_reason_is_worker_even_when_later_passive_gates_also_fail():
    with _fresh() as tmp:
        spec = _fixture(Path(tmp))
        exit_path = Path(spec.worker_exit_path)
        value = json.loads(exit_path.read_text())
        value["return_code"] = 7
        _write_json(exit_path, value)
        Path(spec.main_worktree, "dirty.txt").write_text("dirty\n")
        report = verify_wave(spec)
        assert report.reason is ReasonCode.NONZERO_EXIT
        failed = [item.name for item in report.findings if item.status == "fail"]
        assert failed[:2] == ["worker", "main-state"]


def test_trust_root_change_blocks_checks_without_being_masked_by_code_digest():
    with _fresh() as tmp:
        marker = Path(tmp) / "must-not-run"
        spec = _fixture(Path(tmp), probe_marker=marker)
        repo = Path(spec.repo_root)
        (repo / "tools/check_docs.py").write_text("raise SystemExit(1)\n")
        _git(repo, "commit", "-am", "tamper trust root")
        tampered = _git(repo, "rev-parse", "HEAD")
        _git(repo, "branch", "-f", spec.wave_branch, tampered)
        # Bind the receipt/chain to the extra commit so trust-root is the sole
        # intended trust failure rather than a hidden-commit mismatch.
        envelope = json.loads(Path(spec.stdout_path).read_text())
        envelope["structured_output"]["landed_main_sha"] = tampered
        envelope["structured_output"]["landed_commits"].append(tampered)
        _write_json(Path(spec.stdout_path), envelope)
        _rebind_stdout_size(spec)
        report = verify_wave(spec)
        assert any(item.reason is ReasonCode.TRUST_ROOT_CHANGED for item in report.findings)
        assert not report.active_checks_started and not marker.exists()


def _assert_runner_tamper_is_trust_root_changed(runner: str) -> None:
    with _fresh() as tmp:
        marker = Path(tmp) / "must-not-run"
        spec = _fixture(Path(tmp), probe_marker=marker)
        repo = Path(spec.repo_root)
        (repo / runner).write_text("raise SystemExit(0)\n", encoding="utf-8")
        _git(repo, "add", runner)
        _git(repo, "commit", "-m", "tamper production check runner")
        tampered = _git(repo, "rev-parse", "HEAD")
        _git(repo, "branch", "-f", spec.wave_branch, tampered)
        envelope = json.loads(Path(spec.stdout_path).read_text())
        envelope["structured_output"]["landed_main_sha"] = tampered
        envelope["structured_output"]["landed_commits"].append(tampered)
        _write_json(Path(spec.stdout_path), envelope)
        _rebind_stdout_size(spec)
        report = verify_wave(spec)
        trust = next(item for item in report.findings if item.name == "trust-root")
        assert trust.reason is ReasonCode.TRUST_ROOT_CHANGED
        assert [item.name for item in report.findings if item.status == "fail"] == [
            "trust-root",
        ]
        assert not report.active_checks_started and not marker.exists()


def test_landed_run_tests_runner_tamper_is_trust_root_changed() -> None:
    _assert_runner_tamper_is_trust_root_changed("tools/run_tests.py")


def test_landed_task_run_check_runner_tamper_is_trust_root_changed() -> None:
    _assert_runner_tamper_is_trust_root_changed("tools/task_run_check.py")


def test_completed_receipt_requires_main_landed_last_commit_and_branch_tip_equal() -> None:
    with _fresh() as tmp:
        spec = _fixture(Path(tmp))
        path = Path(spec.stdout_path)
        original = json.loads(path.read_text())
        before = spec.before_main_sha
        mutations = (
            ("landed-main", lambda value: value["structured_output"].update(
                landed_main_sha=before,
            )),
            ("last-commit", lambda value: value["structured_output"].update(
                landed_commits=[before],
            )),
        )
        for _label, mutate in mutations:
            value = json.loads(json.dumps(original))
            mutate(value)
            _write_json(path, value)
            report = verify_wave(spec)
            assert report.reason is ReasonCode.COMMIT_MISMATCH


def test_task_run_terminal_outcome_must_be_completed() -> None:
    with _fresh() as tmp:
        spec = _fixture(Path(tmp))
        root = Path(spec.task_runs_root)
        task_id = start_run(
            root, slug="blocked", objective="fixture", task_class=2,
            task_kind="implementation",
        )
        finish_run(root, task_id, "blocked")
        assert not verify_task_run_finished(root, task_id)


def test_check_docs_must_appear_exactly_once():
    with _fresh() as tmp:
        spec = _fixture(Path(tmp))
        duplicate = spec.check_specs + spec.check_specs
        report = verify_wave(replace(spec, check_specs=duplicate))
        assert report.reason is ReasonCode.CHECK_FAILED
        docs = next(item for item in report.findings if item.name == "check-docs")
        assert docs.detail == "must-occur-exactly-once" and not report.active_checks_started


def test_active_check_timeout_is_clipped_to_total_remaining():
    with _fresh() as tmp:
        checkout = Path(tmp)
        (checkout / "tools").mkdir()
        sleeper = checkout / "tools/check_sleep.py"
        sleeper.write_text("import time\ntime.sleep(5)\n")
        deadline = time.clock_gettime_ns(time.CLOCK_BOOTTIME) + 100_000_000
        started = time.monotonic()
        result = run_check_specs(
            (CheckSpec("sleep", (sys.executable, "tools/check_sleep.py"), 5),), checkout,
            total_deadline_boottime_ns=deadline,
        )
        assert time.monotonic() - started < 1
        assert result[0].reason is ReasonCode.CHECK_FAILED


def test_active_check_side_effect_on_main_is_found_by_reobservation():
    with _fresh() as tmp:
        root = Path(tmp)
        spec = _fixture(root, mutate_main=True)
        report = verify_wave(spec)
        reobserved = next(item for item in report.findings if item.name == "active-reobservation")
        assert reobserved.reason is ReasonCode.CHECK_FAILED


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
