from __future__ import annotations

import asyncio
import concurrent.futures
import copy
import json
import multiprocessing
import multiprocessing.context
import os
from pathlib import Path
import pty
import subprocess
import sys

import pytest

from tools.pegasus import run_acceptance_nproc_study as study


_HEAD = "1" * 40
_SUBMODULE_STATUS = f" {_HEAD} external/ccbench\n"
_GITLINK = f"160000 commit {_HEAD}\texternal/ccbench"
_JUNIT = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="2" failures="0" errors="0" skipped="0">
  <testcase classname="suite.test_fast" name="test_a" time="0.5" />
  <testcase classname="suite.test_repo" name="test_b@real_repo" time="0.25" />
</testsuite>
"""
_JUNIT_REVERSED = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="2" failures="0" errors="0" skipped="0">
  <testcase classname="suite.test_repo" name="test_b@real_repo" time="0.25" />
  <testcase classname="suite.test_fast" name="test_a" time="0.5" />
</testsuite>
"""
_JUNIT_ONE_TEST = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="1" failures="0" errors="0" skipped="0">
  <testcase classname="suite.test_fast" name="test_a" time="0.5" />
</testsuite>
"""


def _cleanup(*, residual: list[int] | None = None) -> dict[str, object]:
    return {
        "kill_sent": False,
        "reaped": not residual,
        "residual_pids": [] if residual is None else residual,
        "term_sent": False,
    }


def _isolation(host: str) -> dict[str, object]:
    return {
        "disturbance_candidates": [],
        "disturbance_rule": "non-exempt process CPU delta >=2 ticks over continuous samples",
        "disturbed": False,
        "host_end": host,
        "host_match": True,
        "host_start": host,
        "interval_s": 1.0,
        "max_gap_s": 1.0,
        "processes": [],
        "read_errors": [],
        "sample_count": 2,
        "valid": True,
    }


class FakeExecutor:
    def __init__(
        self, root: Path, host: str, *, dirty_after_measurement: bool = False,
        junit_by_nproc: dict[str, bytes] | None = None,
    ):
        self.root = root
        self.host = host
        self.dirty_after_measurement = dirty_after_measurement
        self.junit_by_nproc = {} if junit_by_nproc is None else dict(junit_by_nproc)
        self.measurement_seen = False
        self.requests: list[study.ExecRequest] = []

    def __call__(self, request: study.ExecRequest) -> study.ExecResult:
        self.requests.append(request)
        stdout = b""
        if request.purpose.startswith("qstat:"):
            stdout = (
                "(Per-Req) Elapse Time Limit = Max: 14400S\n"
                "Remaining Elapse = 14399S\n"
                f"Execution Host = {self.host}/0\n"
            ).encode()
        elif request.purpose == "clone-superproject":
            destination = Path(request.argv[-1])
            (destination / "tools/pegasus").mkdir(parents=True)
        elif request.purpose.startswith("materialize-submodule:"):
            Path(request.argv[-1]).mkdir(parents=True, exist_ok=True)
        elif request.purpose == "create-acceptance-shard-session":
            session = self.root / "sessions" / f"session-{len(self.requests):04d}"
            for index in range(2):
                (session / f"shard-{index}").mkdir(parents=True)
            stdout = f"{session}\n".encode()
        elif request.purpose.startswith("measurement:"):
            self.measurement_seen = True
            session_token = next(
                token for token in request.argv
                if token.startswith("--izanagi-acceptance-shard-session=")
            )
            shard_token = next(
                token for token in request.argv
                if token.startswith("--izanagi-acceptance-shard-index=")
            )
            session = Path(session_token.split("=", 1)[1])
            shard = int(shard_token.split("=", 1)[1])
            junit = self.junit_by_nproc.get(request.env["IZANAGI_TEST_NPROC"], _JUNIT)
            (session / f"shard-{shard}" / "junit.xml").write_bytes(junit)
            return study.ExecResult(
                returncode=0,
                stdout=b"measurement stdout",
                stderr=b"",
                duration_s=1.0 + shard / 10,
                timed_out=False,
                stdout_sha256=study._sha256(b"measurement stdout"),
                stderr_sha256=study._sha256(b""),
                isolation=_isolation(self.host),
                process_cleanup=_cleanup(),
            )
        elif len(request.argv) >= 4 and request.argv[0:2] == ("git", "-C"):
            args = request.argv[3:]
            if args == ("rev-parse", "HEAD"):
                stdout = f"{_HEAD}\n".encode()
            elif args == ("submodule", "status", "--recursive"):
                stdout = _SUBMODULE_STATUS.encode()
            elif args == ("ls-tree", "HEAD", "external/ccbench"):
                stdout = f"{_GITLINK}\n".encode()
            elif args and args[0] == "status":
                if (
                    self.dirty_after_measurement
                    and self.measurement_seen
                    and "after:status" in request.purpose
                ):
                    stdout = b" M orchestrator/tests/example.py\n"
            elif args and args[0] == "diff":
                stdout = b""
        return study.ExecResult(
            returncode=0,
            stdout=stdout,
            stderr=b"",
            duration_s=0.001,
            timed_out=False,
            stdout_sha256=study._sha256(stdout),
            stderr_sha256=study._sha256(b""),
            isolation=_isolation(self.host),
            process_cleanup=_cleanup(),
        )


def _config(tmp_path: Path) -> study.StudyConfig:
    repo = tmp_path / "repo"
    scratch = tmp_path / "scratch"
    output_root = tmp_path / "receipts"
    (repo / "external/ccbench").mkdir(parents=True)
    scratch.mkdir()
    output_root.mkdir()
    return study.StudyConfig(
        repo_root=repo,
        output=output_root / "receipt.json",
        scratch_root=scratch,
        mode="smoke",
        seed="unit-seed",
        requested_elapstim_s=14400,
        setup_cap_s=900,
        arm_timeout_s={16: 600, 32: 600, 48: 600},
        finalize_reserve_s=300,
        margin_s=60,
    )


def _failed_schema_fixture(tmp_path: Path) -> dict[str, object]:
    config = _config(tmp_path)
    receipt = study._new_receipt(
        config, study.build_schedule("smoke", "unit-seed"), planned_total_s=3000
    )
    receipt["status"] = "failed"
    receipt["failure"] = {"message": "fixture", "stage": "unit", "type": "ContractError"}
    receipt["completed_epoch_s"] = 1
    return receipt


def _manifest_runs(
    schedule: tuple[study.ScheduleBlock, ...],
) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for expected in study._expected_run_manifest(schedule):
        runs.append({
            **expected,
            "session_root": (
                f"/sessions/block-{expected['global_block_index']}"
                f"-arm-{expected['arm']}"
            ),
        })
    return runs


def _poison_process_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    def poison(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("real process creation escaped the injected fake executor")

    for name in (
        "Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput",
    ):
        monkeypatch.setattr(subprocess, name, poison)
    for name in (
        "system", "popen", "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv",
        "spawnve", "spawnvp", "spawnvpe", "posix_spawn", "posix_spawnp", "fork", "forkpty",
        "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
    ):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, poison)
    monkeypatch.setattr(multiprocessing, "Process", poison)
    context_types = {
        value
        for value in vars(multiprocessing.context).values()
        if (
            isinstance(value, type)
            and issubclass(value, multiprocessing.context.BaseContext)
            and "Process" in vars(value)
        )
    }
    for context_type in context_types:
        monkeypatch.setattr(context_type, "Process", poison)
    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", poison)
    monkeypatch.setattr(pty, "fork", poison)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", poison)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", poison)


def test_process_creation_tripwire_fires_on_every_multiprocessing_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    process_factories = [
        multiprocessing.Process,
        multiprocessing.context._default_context.Process,
        *(
            multiprocessing.get_context(method).Process
            for method in multiprocessing.get_all_start_methods()
        ),
    ]
    for process_factory in process_factories:
        with pytest.raises(
            AssertionError,
            match="real process creation escaped the injected fake executor",
        ):
            process_factory()


def test_full_schedule_uses_each_permutation_once_and_excludes_warmup() -> None:
    schedule = study.build_schedule("full", "seed-a")
    assert len(schedule) == 7
    assert schedule[0].phase == "warmup"
    assert schedule[0].analysis_block_index is None
    measured = [block for block in schedule if block.phase == "measurement"]
    assert len(measured) == 6
    assert len({block.arm_order for block in measured}) == 6
    assert {arm for block in measured for arm in block.arm_order} == {16, 32, 48}
    assert study.build_schedule("full", "seed-a") == schedule
    assert study._rank("seed-a", "measurement-0", (16, 32, 48)) != study._rank(
        "seed-b", "measurement-0", (16, 32, 48)
    )


def test_smoke_has_one_measured_block_and_no_warmup() -> None:
    schedule = study.build_schedule("smoke", "seed-a")
    assert len(schedule) == 1
    assert schedule[0].phase == "measurement"
    assert schedule[0].analysis_block_index == 0


def test_run_manifest_rejects_warmup_measurement_swap_with_same_analysis_count() -> None:
    schedule = study.build_schedule("full", "seed-a")
    runs = _manifest_runs(schedule)
    study.validate_run_manifest(runs, schedule)
    for run in runs[:6]:
        run["analysis_block_index"] = 0
        run["analysis_included"] = True
    for run in runs[6:12]:
        run["analysis_block_index"] = None
        run["analysis_included"] = False
    assert sum(run["analysis_included"] is True for run in runs) == 36
    with pytest.raises(study.ContractError, match="run manifest differs from schedule"):
        study.validate_run_manifest(runs, schedule)


def test_run_manifest_rejects_fixed_arm_order_behind_balanced_schedule() -> None:
    schedule = study.build_schedule("full", "seed-a")
    block = next(
        block for block in schedule
        if block.phase == "measurement" and block.arm_order != study.ARMS
    )
    runs = _manifest_runs(schedule)
    start = block.global_block_index * len(study.ARMS) * study.SHARD_COUNT
    for order_index, arm in enumerate(study.ARMS):
        for shard_index in range(study.SHARD_COUNT):
            run = runs[start + order_index * study.SHARD_COUNT + shard_index]
            run["arm"] = arm
            run["session_root"] = f"/sessions/fixed-arm-{arm}"
    with pytest.raises(study.ContractError, match="field arm"):
        study.validate_run_manifest(runs, schedule)


def test_run_manifest_rejects_cross_block_shard_label_and_split_session() -> None:
    schedule = study.build_schedule("full", "seed-a")
    cross_block = _manifest_runs(schedule)
    cross_block[1]["global_block_index"] = 1
    with pytest.raises(study.ContractError, match="field global_block_index"):
        study.validate_run_manifest(cross_block, schedule)

    split_session = _manifest_runs(schedule)
    split_session[1]["session_root"] = "/sessions/different-arm-pair"
    with pytest.raises(study.ContractError, match="different session_root"):
        study.validate_run_manifest(split_session, schedule)


def test_budget_strictly_rejects_equality() -> None:
    with pytest.raises(study.ContractError, match="strictly"):
        study.validate_budget(
            setup_cap_s=1,
            block_count=1,
            arm_timeout_s={16: 1, 32: 1, 48: 1},
            finalize_reserve_s=1,
            requested_elapstim_s=5,
        )
    assert study.validate_budget(
        setup_cap_s=1,
        block_count=1,
        arm_timeout_s={16: 1, 32: 1, 48: 1},
        finalize_reserve_s=1,
        requested_elapstim_s=6,
    ) == 5


def test_remaining_budget_strictly_rejects_equality() -> None:
    with pytest.raises(study.ContractError, match="strictly"):
        study.validate_remaining_budget(
            remaining_s=10, remaining_arm_timeout_s=5,
            finalize_reserve_s=3, margin_s=2,
        )


def test_arm_timeout_preserves_every_postrun_fingerprint_window() -> None:
    assert study.allocate_shard_timeout(arm_remaining_s=600.0, remaining_shards=2) == 270.0
    with pytest.raises(study.ContractError, match="postrun fingerprint"):
        study.allocate_shard_timeout(arm_remaining_s=60.0, remaining_shards=2)


def test_junit_diagnostics_record_serial_work_and_real_repo_chain() -> None:
    result = study.analyze_junit(_JUNIT)
    assert result["test_count"] == 2
    assert result["serial_work_sum_s"] == pytest.approx(0.75)
    assert result["real_repo_exclusive_chain_s"] == pytest.approx(0.25)
    assert result["real_repo_test_count"] == 1


def test_junit_identity_set_digest_is_order_independent() -> None:
    original = study.analyze_junit(_JUNIT)
    reversed_order = study.analyze_junit(_JUNIT_REVERSED)
    assert original["nodeids_sha256"] != reversed_order["nodeids_sha256"]
    assert (
        original["testcase_identity_set_sha256"]
        == reversed_order["testcase_identity_set_sha256"]
    )


def test_continuous_isolation_detects_middle_only_same_uid_consumer() -> None:
    identity = (9001, 321)
    process = {"command": "compiler", "pgroup": 700, "ticks": 8, "uid": 42}
    samples = [
        {"hostname": "bnode001", "monotonic_s": 0.0, "processes": {}, "read_errors": []},
        {"hostname": "bnode001", "monotonic_s": 1.0,
         "processes": {identity: process}, "read_errors": []},
        {"hostname": "bnode001", "monotonic_s": 2.0, "processes": {}, "read_errors": []},
    ]
    result = study.summarize_isolation_samples(
        samples, own_uid=42, exempt_pgroups={100, 200}, expected_host="bnode001"
    )
    assert result["valid"] is True
    assert result["disturbed"] is True
    assert result["disturbance_candidates"][0]["uid_relation"] == "same"
    assert result["disturbance_candidates"][0]["created"] is True
    assert result["disturbance_candidates"][0]["disappeared"] is True


def test_sampler_gap_or_read_failure_is_invalid() -> None:
    samples = [
        {"hostname": "bnode001", "monotonic_s": 0.0, "processes": {}, "read_errors": []},
        {"hostname": "bnode001", "monotonic_s": 2.0, "processes": {},
         "read_errors": ["77:PermissionError"]},
    ]
    result = study.summarize_isolation_samples(
        samples, own_uid=42, exempt_pgroups=set(), expected_host="bnode001"
    )
    assert result["valid"] is False


def test_internal_shard_argv_rejects_any_extra_n_option(tmp_path: Path) -> None:
    clone = tmp_path / "clone"
    session = tmp_path / "session"
    argv = [
        "python3.10", str(clone / "tools/run_tests.py"),
        f"--izanagi-acceptance-shard-session={session}",
        "--izanagi-acceptance-shard-count=2",
        "--izanagi-acceptance-shard-index=0",
        "-n", "32",
    ]
    with pytest.raises(study.ContractError, match="pinned empty-argv"):
        study.validate_measurement_argv(
            argv, clone=clone, session=session, shard_index=0,
            python_command="python3.10",
        )


def test_process_cleanup_rejects_residual_group_member() -> None:
    with pytest.raises(study.ContractError, match="fully reaped"):
        study.validate_process_cleanup(_cleanup(residual=[1234]))


def test_analysis_rejects_warmup_leaking_into_smoke_estimand() -> None:
    runs = []
    for phase, included in (("measurement", True), ("warmup", False)):
        for arm in (16, 32, 48):
            for shard in (0, 1):
                runs.append({
                    "analysis_block_index": 0,
                    "analysis_included": included,
                    "arm": arm,
                    "junit": {
                        "real_repo_exclusive_chain_s": 0.2,
                        "serial_work_sum_s": 1.0,
                    },
                    "phase": phase,
                    "shard_index": shard,
                    "wall_s": 2.0,
                })
    outcomes, contrasts = study._derive_analysis(runs, mode="smoke")
    assert len(outcomes) == 3
    assert len(contrasts) == 2
    for run in runs:
        run["analysis_included"] = True
    with pytest.raises(study.ContractError, match="measured run count"):
        study._derive_analysis(runs, mode="smoke")


def test_receipt_schema_rejects_missing_excluded_estimand_and_unknown_field(
    tmp_path: Path,
) -> None:
    receipt = _failed_schema_fixture(tmp_path)
    study.validate_receipt(receipt, expected_mode="smoke", require_complete=False)
    missing = copy.deepcopy(receipt)
    missing.pop("excluded_estimands")
    with pytest.raises(study.ContractError, match="closed map"):
        study.validate_receipt(missing, expected_mode="smoke", require_complete=False)
    unknown = copy.deepcopy(receipt)
    unknown["unexpected"] = True
    with pytest.raises(study.ContractError, match="unknown"):
        study.validate_receipt(unknown, expected_mode="smoke", require_complete=False)


def test_job_failure_schema_is_closed() -> None:
    receipt = {
        "message": "failed",
        "mode": "smoke",
        "pbs_jobid": "0:1.nqsv",
        "recorded_epoch_s": 1,
        "returncode": 2,
        "schema_version": study.JOB_FAILURE_SCHEMA_VERSION,
        "stage": "bootstrap",
    }
    study.validate_job_failure_receipt(receipt)
    receipt["unknown"] = True
    with pytest.raises(study.ContractError, match="unknown"):
        study.validate_job_failure_receipt(receipt)


def test_fake_executor_is_the_only_process_surface_and_smoke_receipt_is_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode999"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:123.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host)
    rc, receipt = study.run_study(config, executor)
    assert rc == 0
    assert receipt["status"] == "complete"
    assert len(receipt["runs"]) == 6
    assert all(run["analysis_included"] for run in receipt["runs"])
    assert receipt["design"]["primary_contrast"] == {"arm": 32, "reference_arm": 48}
    assert {row["priority"] for row in receipt["contrasts"]} == {"primary", "secondary"}
    measurement_requests = [
        request for request in executor.requests if request.purpose.startswith("measurement:")
    ]
    assert len(measurement_requests) == 6
    for request in measurement_requests:
        assert "-n" not in request.argv
        assert request.env["IZANAGI_TEST_NPROC"] in {"16", "32", "48"}
        assert request.env["HOME"].startswith(str(config.scratch_root))
        assert not any(key.startswith(("CCACHE_", "SCCACHE_")) for key in request.env)
    study.validate_receipt(receipt, expected_mode="smoke", require_complete=True)

    different_set = copy.deepcopy(receipt)
    different_set["runs"][2]["junit"]["testcase_identity_set_sha256"] = study._sha256(
        b"different-testcase-set"
    )
    with pytest.raises(study.ContractError, match="JUnit testcase identity set differs"):
        study.validate_receipt(
            different_set, expected_mode="smoke", require_complete=True
        )

    wrong_manifest = copy.deepcopy(receipt)
    wrong_manifest["runs"][0]["order_index"] = 2
    with pytest.raises(study.ContractError, match="run manifest differs from schedule"):
        study.validate_receipt(
            wrong_manifest, expected_mode="smoke", require_complete=True
        )

    split_session = copy.deepcopy(receipt)
    split_root = str(config.scratch_root / "different-session")
    split_session["runs"][1]["session_root"] = split_root
    split_session["runs"][1]["argv"][2] = (
        f"--izanagi-acceptance-shard-session={split_root}"
    )
    with pytest.raises(study.ContractError, match="different session_root"):
        study.validate_receipt(
            split_session, expected_mode="smoke", require_complete=True
        )


def test_postrun_dirt_overrides_a_green_child(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode999"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:124.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, dirty_after_measurement=True)
    rc, receipt = study.run_study(config, executor)
    assert rc == 1
    assert receipt["status"] == "failed"
    assert receipt["failure"]["type"] == "PostrunDirt"
    assert receipt["failure"]["stage"].endswith("shard-0")


def test_arm_specific_deselection_prevents_complete_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _poison_process_creation(monkeypatch)
    config = _config(tmp_path)
    host = "bnode999"
    monkeypatch.setattr(study.socket, "gethostname", lambda: host)
    nodefile = tmp_path / "pbs-nodefile"
    nodefile.write_text(host + "\n", encoding="utf-8")
    monkeypatch.setenv("PBS_JOBID", "0:125.nqsv")
    monkeypatch.setenv("PBS_NODEFILE", str(nodefile))
    executor = FakeExecutor(tmp_path, host, junit_by_nproc={"32": _JUNIT_ONE_TEST})
    rc, receipt = study.run_study(config, executor)
    assert rc == 1
    assert receipt["status"] == "failed"
    assert receipt["invariant_checks"]["junit_identity_sets_match_by_shard"] is False
    assert receipt["failure"]["type"] == "ContractError"
    assert "JUnit testcase identity set differs" in receipt["failure"]["message"]


def test_static_contract_has_signal_traps_exact_registry_and_no_red_checker() -> None:
    repo = Path(__file__).resolve().parents[2]
    shell_text = (repo / "tools/pegasus/acceptance_nproc_study.sh").read_text(encoding="utf-8")
    driver_text = (repo / "tools/pegasus/run_acceptance_nproc_study.py").read_text(encoding="utf-8")
    assert "#PBS -b 1" in shell_text
    for signal_name in ("ERR", "TERM", "HUP", "INT", "EXIT"):
        assert f" {signal_name}" in shell_text or f"{signal_name} " in shell_text
    forbidden = "tools/" + "check_acceptance_reds.py"
    assert forbidden not in shell_text
    assert forbidden not in driver_text
    registry = json.loads(
        (repo / "tools/pegasus/admission_registry.json").read_text(encoding="utf-8")
    )["entries"]
    expected = {
        "tools/pegasus/acceptance_nproc_study.sh",
        "tools/pegasus/run_acceptance_nproc_study.py",
    }
    assert expected <= set(registry)
    assert all(registry[path]["class"] == "dispatch-required" for path in expected)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
