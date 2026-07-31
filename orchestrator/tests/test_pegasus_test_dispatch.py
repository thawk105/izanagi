# -*- coding: utf-8 -*-
"""Adversarial contract tests for the Pegasus pytest dispatcher."""
from __future__ import annotations

from collections import deque
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from pegasus import test_dispatch as TD
import pegasus_policy


FIXED_CLOSURE = (
    "tools/run_tests.py",
    "tools/ruleops.py",
    "tools/pegasus_policy.py",
    "tools/pegasus/test_dispatch.py",
    "tools/pegasus/submit_tests.py",
    "tools/pegasus/run_tests_job.sh",
)
DISPATCH_ID = "20260730010203-0123456789abcdef"
JOB_ID_RAW = "0:123.nqsv"
JOB_ID = "123.nqsv"
AUTH_SHA = "a" * 64
REQUEST_SHA = "b" * 64
QSUB_RESULT_SHA = "c" * 64
SUBMIT_SHA = "d" * 64


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.trace: list[float] = []

    def __call__(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.trace.append(seconds)
        self.value += seconds


class FakeScheduler:
    """Exact ordered scheduler script with no prefix or environment matching."""

    def __init__(self, script) -> None:
        self.script = deque(script)
        self.trace: list[tuple[str, ...]] = []

    def run(self, argv, *, timeout, environment=None):
        actual = tuple(argv)
        if not self.script:
            raise AssertionError(
                f"fatal scheduler sentinel: unexpected call {actual!r}"
            )
        step = self.script.popleft()
        if len(step) == 2:
            expected, scripted = step
            expected_timeout = None
        else:
            expected, scripted, expected_timeout = step
        assert actual == tuple(expected)
        if expected_timeout is not None:
            assert timeout == expected_timeout
        assert environment == TD.scheduler_environment()
        self.trace.append(actual)
        if isinstance(scripted, BaseException):
            raise scripted
        return dataclasses.replace(scripted, argv=actual)

    def assert_drained(self) -> None:
        assert not self.script, f"scheduler steps not reached: {list(self.script)!r}"


def _result(
    rc=0,
    stdout="",
    stderr="",
    *,
    timed_out=False,
    output_limited=False,
    process_signal=None,
    completion_unknown=None,
):
    if completion_unknown is None:
        completion_unknown = (
            timed_out or output_limited or process_signal is not None
        )
    return TD.CommandResult(
        (),
        rc,
        stdout,
        stderr,
        timed_out=timed_out,
        output_limited=output_limited,
        signal=process_signal,
        completion_unknown=completion_unknown,
    )


class FakeFilesystem:
    """Raw-byte filesystem fake; JSON must traverse the canonical parser."""

    def __init__(
        self,
        files=None,
        *,
        delayed_paths=None,
        fail_publish_count=0,
    ) -> None:
        self.files = {
            Path(path): bytes(raw) for path, raw in (files or {}).items()
        }
        self.delayed_paths = {
            Path(path): count for path, count in (delayed_paths or {}).items()
        }
        self.final = None
        self.fail_publish_count = fail_publish_count
        self.trace: list[str] = []

    def exists(self, path):
        path = Path(path)
        remaining = self.delayed_paths.get(path, 0)
        if remaining:
            self.delayed_paths[path] = remaining - 1
            return False
        return path in self.files

    def receipt(self, path):
        path = Path(path)
        raw = self.files.get(path)
        if raw is None:
            return None
        self.trace.append(f"receipt:{path.name}")
        return {
            "path": str(path),
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    def load_object(self, path):
        path = Path(path)
        try:
            raw = self.files[path]
            value = json.loads(raw)
        except (KeyError, json.JSONDecodeError) as exc:
            raise AssertionError(
                f"fatal filesystem sentinel: invalid/missing {path}"
            ) from exc
        assert type(value) is dict
        assert raw == TD._canonical_json(value)
        self.trace.append(f"load:{path.name}")
        return value

    def publish_final(self, snapshot, document):
        if self.fail_publish_count:
            self.fail_publish_count -= 1
            raise OSError("injected final publication crash")
        if self.final is not None:
            raise AssertionError("fatal filesystem sentinel: duplicate final")
        raw = TD._canonical_json(dict(document))
        parsed = json.loads(raw)
        assert raw == TD._canonical_json(parsed)
        TD.validate_final_receipt_object(
            parsed,
            snapshot=snapshot,
            verify_files=False,
        )
        self.files[snapshot.dispatch_dir / "final-receipt.json"] = raw
        self.final = parsed
        self.trace.append("publish:final")

    def stage_final(self, snapshot, document):
        raw = TD._canonical_json(dict(document))
        parsed = json.loads(raw)
        TD.validate_final_receipt_object(
            parsed,
            snapshot=snapshot,
            verify_files=False,
        )
        path = snapshot.dispatch_dir / "final-pending.json"
        existing = self.files.get(path)
        if existing is not None:
            assert existing == raw
        self.files[path] = raw
        self.trace.append("stage:final")

    def replay(self, path, destination, byte_limit):
        path = Path(path)
        if path not in self.files:
            raise AssertionError(f"fatal filesystem sentinel: replay missing {path}")
        self.trace.append(f"replay:{path.name}:{byte_limit}")
        return min(len(self.files[path]), byte_limit)

    def read_bytes(self, path, byte_limit):
        path = Path(path)
        if path not in self.files:
            raise TD.DispatchError(f"fake file unavailable: {path.name}")
        raw = self.files[path]
        if len(raw) > byte_limit:
            raise TD.DispatchError(f"fake file exceeds limit: {path.name}")
        return raw

    def size(self, path):
        raw = self.files.get(Path(path))
        return None if raw is None else len(raw)

    def record_command(self, directory, label, sequence, result):
        receipts = {}
        for suffix, raw in (
            ("stdout", result.stdout.encode("utf-8")),
            ("stderr", result.stderr.encode("utf-8")),
            ("rc", f"{result.returncode}\n".encode("ascii")),
        ):
            path = Path(directory) / f"{sequence:05d}-{label}.{suffix}"
            self.files[path] = raw
            receipts[suffix] = self.receipt(path)
        return {
            "stdout": receipts["stdout"],
            "stderr": receipts["stderr"],
            "returncode": receipts["rc"],
        }

    def next_sequence(self, _directory):
        return 0


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _policy_document(**overrides):
    value = json.loads(
        (REPO / "tools" / "pegasus" / "test_dispatch_policy.json").read_bytes()
    )
    value.update(overrides)
    return value


def _write_policy(source_root: Path, **overrides) -> TD.DispatchPolicy:
    path = source_root / "tools" / "pegasus" / "test_dispatch_policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(TD._canonical_json(_policy_document(**overrides)))
    return TD.load_policy(path)


def _seed_source(
    root: Path,
    *,
    policy_overrides=None,
) -> tuple[Path, TD.DispatchPolicy]:
    source = root / "repo"
    source.mkdir()
    for relative in FIXED_CLOSURE:
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)
    target = source / "orchestrator" / "tests" / "test_sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("VALUE = 'base'\n", encoding="utf-8")
    policy = _write_policy(source, **(policy_overrides or {}))
    _git(source, "init", "-q")
    _git(source, "config", "user.email", "dispatch@example.invalid")
    _git(source, "config", "user.name", "Dispatch Test")
    _git(source, "add", ".")
    _git(source, "commit", "-qm", "base")
    return source, policy


def _preflight_script(policy: TD.DispatchPolicy):
    return [
        (
            ("qstat", "-Q"),
            _result(stdout=f"{policy.queue} available\n"),
            policy.command_timeout_s,
        ),
        (("pegasusinfo",), _result(stdout="available\n"), policy.command_timeout_s),
        (("rbudgetcheck",), _result(stdout="budget ok\n"), policy.command_timeout_s),
        (("check_quota",), _result(stdout="quota ok\n"), policy.command_timeout_s),
    ]


def _synthetic_snapshot(
    tmp_path: Path,
    *,
    policy_overrides=None,
    runner_environment=None,
) -> tuple[TD.Snapshot, TD.DispatchPolicy]:
    dispatch = (tmp_path / DISPATCH_ID).resolve()
    source = dispatch / "source"
    source.mkdir(parents=True)
    for relative in FIXED_CLOSURE:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith("run_tests_job.sh"):
            path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            path.chmod(0o755)
        else:
            path.write_text(f"# synthetic {relative}\n", encoding="utf-8")
    target = source / "orchestrator" / "tests" / "test_sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("def test_sample(): pass\n", encoding="utf-8")
    defaults = {
        "poll_interval_s": 1,
        "visibility_grace_s": 4,
        "queue_timeout_s": 4,
        "held_timeout_s": 4,
        "prerun_timeout_s": 4,
        "run_timeout_s": 4,
        "global_deadline_s": 30,
        "log_grace_s": 2,
        "accounting_grace_s": 2,
        "stderr_stable_polls": 2,
        "qstat_transient_limit": 2,
        "qdel_attempts": 2,
        "qdel_retry_interval_s": 1,
        "min_free_bytes": 1,
    }
    defaults.update(policy_overrides or {})
    policy = _write_policy(source, **defaults)
    encoded = (
        {
            "kind": "repo_path",
            "path": "orchestrator/tests/test_sample.py",
        },
    )
    bound_environment = dict(runner_environment or {})
    closure, closure_sha = TD._execution_closure(
        source,
        encoded,
        bound_environment,
        policy,
    )
    tree = TD._tree_summary(source, policy)
    manifest = {
        "schema": "izanagi-test-snapshot-v2",
        "dispatch_id": DISPATCH_ID,
        "head": "0" * 40,
        "source_state": {
            "head": "0" * 40,
            "status_v2_sha256": "0" * 64,
            "cached_diff_sha256": "0" * 64,
            "unstaged_diff_sha256": "0" * 64,
        },
        "cached_patch_sha256": hashlib.sha256(b"").hexdigest(),
        "unstaged_patch_sha256": hashlib.sha256(b"").hexdigest(),
        "untracked": [],
        "ignored_inputs": [],
        "submodules": [],
        "pytest_argv": list(encoded),
        "runner_environment": bound_environment,
        "preflight": [],
        "policy": {
            "path": "tools/pegasus/test_dispatch_policy.json",
            "sha256": policy.policy_sha256,
        },
        "execution_closure": list(closure),
        "execution_closure_sha256": closure_sha,
        "snapshot_tree": tree,
        "snapshot_semantics": "synthetic exact-file fixture",
    }
    manifest_path = dispatch / "snapshot-manifest.json"
    manifest_raw = TD._canonical_json(manifest)
    TD.create_file(manifest_path, manifest_raw)
    snapshot = TD.Snapshot(
        dispatch_id=DISPATCH_ID,
        dispatch_dir=dispatch,
        snapshot_root=source,
        manifest_path=manifest_path,
        manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        encoded_argv=encoded,
        runner_environment=bound_environment,
        execution_closure_sha256=closure_sha,
        policy_sha256=policy.policy_sha256,
        snapshot_tree_sha256=str(tree["sha256"]),
    )
    assert TD.snapshot_from_dispatch(dispatch) == snapshot
    return snapshot, policy


def _accounting(job_id=JOB_ID, *, group="SFC") -> bytes:
    return (
        "============================================================\n"
        f"Request ID:             {job_id}\n"
        "Request Name:           test_dispatch.sh\n"
        "Queue:                  gen_S@nqsv\n"
        "Number of Jobs:         1\n"
        f"User Name:              {TD.scheduler_user_name()}\n"
        f"Group Name:             {group}\n"
        "Created Request Time:   Thu Jan 01 00:00:00 1970\n"
        "Started Request Time:   Thu Jan 01 00:00:01 1970\n"
        "Ended Request Time:     Thu Jan 01 00:00:02 1970\n"
        "Resources Information:\n"
        "  Elapse:               2S\n"
        "  Remaining Elapse:     1798S\n"
        "============================================================\n"
    ).encode("utf-8")


def _qstat(
    state: str,
    host: str | None = None,
    *,
    request_id: str = JOB_ID,
    group: str = "SFC",
) -> str:
    output = (
        f"Request ID: {request_id}\n"
        f"    Group Name = {group}\n"
        f"    Current State = {state}\n"
    )
    if host is not None:
        output += f"Execution Hosts(JSVNO):\n  {host}(0)\n"
    return output


def _qstat_listing(*requests) -> str:
    documents = []
    for request in requests:
        request_id, request_name, state, *overrides = request
        values = {
            "user": TD.scheduler_user_name(),
            "group": "SFC",
            "queue": "gen_S@nqsv",
            "account": "SFC",
            "created": "Thu Jan 01 00:00:00 1970",
            "host": "bnode114" if str(state).lower() == "running" else None,
        }
        if overrides:
            values.update(overrides[0])
        document = (
            f"Request ID: {request_id}\n"
            f"    Request Name = {request_name}\n"
            f"    User  Name = {values['user']}\n"
            f"    Group Name = {values['group']}\n"
            f"    Current State = {state}\n"
            f"    Queue = {values['queue']} (Execution Queue)\n"
            f"    Account Code = {values['account']}\n"
            f"    Created Request Time = {values['created']}\n"
        )
        if values["host"] is not None:
            document += (
                "  Execution Hosts(JSVNO):\n"
                f"    {values['host']}(0)\n"
            )
        documents.append(document)
    return "".join(documents)


def _submission_argv(snapshot, policy):
    job = snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    return job, TD.qsub_argv(
        snapshot=snapshot,
        policy=policy,
        authorization_path=(
            snapshot.dispatch_dir / "pre-submit-authorization.json"
        ),
        runner_result_path=snapshot.dispatch_dir / "runner-result.json",
        job_script=job,
    )


def _runner_result(
    snapshot: TD.Snapshot,
    *,
    worker_environment_sha256: str,
    runner_claim_sha256: str,
    rc=0,
    authorization_sha256=AUTH_SHA,
    qsub_request_sha256=REQUEST_SHA,
    qsub_result_sha256=QSUB_RESULT_SHA,
    submit_receipt_sha256=SUBMIT_SHA,
):
    return {
        "schema": "izanagi-test-runner-result-v2",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "authorization_sha256": authorization_sha256,
        "qsub_request_sha256": qsub_request_sha256,
        "qsub_result_sha256": qsub_result_sha256,
        "submit_receipt_sha256": submit_receipt_sha256,
        "runner_claim_sha256": runner_claim_sha256,
        "worker_environment_sha256": worker_environment_sha256,
        "pbs_job_id_raw": JOB_ID_RAW,
        "job_id_normalized": JOB_ID,
        "hostname_raw": "bnode114",
        "hostname_canonical": "bnode114",
        "affinity_cpus": [0, 1, 2, 3],
        "runner_exit_status": rc,
        "runner_signal": None,
        "pytest_exit_status": rc,
        "pytest_signal": None,
        "runner_stage": "pytest",
        "task_run_attempted": False,
        "task_run_event_id": None,
        "task_run_event": None,
    }


def _monitor_files(
    snapshot: TD.Snapshot,
    *,
    stderr=None,
    rc=0,
    authorization_sha256=AUTH_SHA,
    qsub_request_sha256=REQUEST_SHA,
    qsub_result_sha256=QSUB_RESULT_SHA,
    submit_receipt_sha256=SUBMIT_SHA,
):
    worker_raw = TD._canonical_json({"schema": "worker-fixture"})
    claim_raw = TD._canonical_json({"schema": "claim-fixture"})
    runner = _runner_result(
        snapshot,
        worker_environment_sha256=hashlib.sha256(worker_raw).hexdigest(),
        runner_claim_sha256=hashlib.sha256(claim_raw).hexdigest(),
        rc=rc,
        authorization_sha256=authorization_sha256,
        qsub_request_sha256=qsub_request_sha256,
        qsub_result_sha256=qsub_result_sha256,
        submit_receipt_sha256=submit_receipt_sha256,
    )
    return {
        snapshot.dispatch_dir / "runner-result.json": TD._canonical_json(runner),
        snapshot.dispatch_dir / "worker-environment.json": worker_raw,
        snapshot.dispatch_dir / "runner-claim.json": claim_raw,
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout": b"pytest output\n",
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr": (
            _accounting() if stderr is None else stderr
        ),
    }


def _monitor(
    snapshot,
    policy,
    scheduler,
    filesystem,
    clock,
    *,
    authorization_sha256=AUTH_SHA,
    qsub_request_sha256=REQUEST_SHA,
    qsub_result_sha256=QSUB_RESULT_SHA,
    submit_receipt_sha256=SUBMIT_SHA,
):
    return TD.monitor_job(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        authorization_sha256=authorization_sha256,
        qsub_request_sha256=qsub_request_sha256,
        qsub_result_sha256=qsub_result_sha256,
        submit_receipt_sha256=submit_receipt_sha256,
        qsub_request_id_raw=JOB_ID_RAW,
        job_id_normalized=JOB_ID,
        qsub_started_epoch_s=0.0,
        absolute_deadline_epoch_s=float(policy.global_deadline_s),
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=filesystem,
    )


def test_dirty_snapshot_binds_execution_closure_and_detects_mode_drift(tmp_path):
    source, policy = _seed_source(
        tmp_path,
        policy_overrides={
            "max_total_bytes": 64 * 1024 * 1024,
            "max_retained_bytes": 128 * 1024 * 1024,
            "max_spool_bytes": 4 * 1024 * 1024,
            "min_free_bytes": 1,
        },
    )
    target = source / "orchestrator" / "tests" / "test_sample.py"
    delete_me = source / "delete_me"
    delete_me.write_text("remove\n", encoding="utf-8")
    _git(source, "add", "delete_me")
    _git(source, "commit", "-qm", "add deletion fixture")
    target.write_text("VALUE = 'cached'\n", encoding="utf-8")
    _git(source, "add", str(target.relative_to(source)))
    target.write_text("VALUE = 'unstaged'\n", encoding="utf-8")
    _git(source, "rm", "-q", "delete_me")
    executable = source / "untracked-tool"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    (source / "untracked-link").symlink_to(
        "orchestrator/tests/test_sample.py"
    )
    production_import = source / "orchestrator" / "campaign" / "buildcache.py"
    production_import.parent.mkdir(parents=True)
    production_import.write_text("TRUSTED = True\n", encoding="utf-8")
    scheduler = FakeScheduler(_preflight_script(policy))

    snapshot = TD.create_snapshot(
        source_root=source,
        caller_cwd=source,
        raw_args=["orchestrator/tests/test_sample.py"],
        policy=policy,
        scheduler=scheduler,
        dispatch_id="20260730010203-fedcba9876543210",
        environ={"PATH": os.environ["PATH"]},
    )
    scheduler.assert_drained()
    manifest_raw = snapshot.manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    assert manifest_raw == TD._canonical_json(manifest)
    assert str(source).encode() not in manifest_raw
    assert (snapshot.snapshot_root / target.relative_to(source)).read_text(
        encoding="utf-8"
    ) == "VALUE = 'unstaged'\n"
    assert not (snapshot.snapshot_root / "delete_me").exists()
    entries = {item["path"]: item for item in manifest["untracked"]}
    assert entries["untracked-tool"]["mode"] == 0o755
    assert entries["untracked-link"]["kind"] == "symlink"
    closure = {item["path"]: item for item in manifest["execution_closure"]}
    execution_tree = {
        item["path"]: item for item in manifest["snapshot_tree"]["entries"]
    }
    assert (
        execution_tree["orchestrator/campaign/buildcache.py"]["sha256"]
        == hashlib.sha256(b"TRUSTED = True\n").hexdigest()
    )
    assert "orchestrator/campaign/buildcache.py" not in closure
    for relative in (*FIXED_CLOSURE, "tools/pegasus/test_dispatch_policy.json"):
        assert closure[relative]["kind"] == "file"
        assert len(closure[relative]["sha256"]) == 64
    assert TD.verify_execution_closure(snapshot) == (
        snapshot.execution_closure_sha256
    )
    copied_import = (
        snapshot.snapshot_root / "orchestrator" / "campaign" / "buildcache.py"
    )
    copied_import.write_text("TRUSTED = False\n", encoding="utf-8")
    assert TD.verify_execution_closure(snapshot) == (
        snapshot.execution_closure_sha256
    )
    with pytest.raises(TD.DispatchError, match="source tree drifted"):
        TD.verify_snapshot_tree(snapshot, policy)
    copied_import.write_text("TRUSTED = True\n", encoding="utf-8")
    job = snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    job.chmod(0o644)
    with pytest.raises(TD.DispatchError, match="closure drift"):
        TD.verify_execution_closure(snapshot)


@pytest.mark.parametrize(
    "poison",
    ["fsmonitor", "filter", "info-attributes", "worktree-attributes"],
)
def test_snapshot_refuses_local_git_execution_and_filter_surfaces(
    tmp_path, poison,
):
    source, policy = _seed_source(tmp_path)
    if poison == "fsmonitor":
        _git(source, "config", "core.fsmonitor", "/tmp/evil-fsmonitor")
    elif poison == "filter":
        _git(source, "config", "filter.evil.clean", "/tmp/evil-filter")
    elif poison == "info-attributes":
        path = source / ".git" / "info" / "attributes"
        path.write_text("*.py filter=evil\n", encoding="utf-8")
    else:
        (source / ".gitattributes").write_text(
            "*.py filter=evil\n", encoding="utf-8"
        )
    scheduler = FakeScheduler([])
    with pytest.raises(TD.DispatchError, match="Git|attributes|configuration"):
        TD.create_snapshot(
            source_root=source,
            caller_cwd=source,
            raw_args=["orchestrator/tests/test_sample.py"],
            policy=policy,
            scheduler=scheduler,
            environ={"PATH": os.environ["PATH"]},
        )
    scheduler.assert_drained()


def test_snapshot_quota_is_aggregate_across_all_categories(tmp_path):
    source, policy = _seed_source(
        tmp_path,
        policy_overrides={
            "max_file_bytes": 1_100_000,
            "max_total_bytes": 1_500_000,
            "max_spool_bytes": 500_000,
            "max_retained_bytes": 3_000_000,
            "replay_bytes": 100_000,
            "min_free_bytes": 1,
        },
    )
    (source / "tracked-large.bin").write_bytes(os.urandom(900_000))
    _git(source, "add", "tracked-large.bin")
    _git(source, "commit", "-qm", "tracked quota fixture")
    (source / "untracked-large.bin").write_bytes(os.urandom(900_000))
    scheduler = FakeScheduler(_preflight_script(policy))
    with pytest.raises(TD.DispatchError, match="aggregate"):
        TD.create_snapshot(
            source_root=source,
            caller_cwd=source,
            raw_args=["orchestrator/tests/test_sample.py"],
            policy=policy,
            scheduler=scheduler,
            environ={"PATH": os.environ["PATH"]},
        )
    scheduler.assert_drained()


def test_tracked_file_obeys_max_file_bytes(tmp_path):
    source, policy = _seed_source(
        tmp_path,
        policy_overrides={
            "max_file_bytes": 1_000_000,
            "max_total_bytes": 8_000_000,
            "max_spool_bytes": 500_000,
            "max_retained_bytes": 16_000_000,
            "replay_bytes": 100_000,
            "min_free_bytes": 1,
        },
    )
    (source / "tracked-too-large.bin").write_bytes(os.urandom(1_000_001))
    _git(source, "add", "tracked-too-large.bin")
    _git(source, "commit", "-qm", "oversized tracked fixture")
    scheduler = FakeScheduler(_preflight_script(policy))
    with pytest.raises(TD.DispatchError, match="size limit"):
        TD.create_snapshot(
            source_root=source,
            caller_cwd=source,
            raw_args=["orchestrator/tests/test_sample.py"],
            policy=policy,
            scheduler=scheduler,
            environ={"PATH": os.environ["PATH"]},
        )
    scheduler.assert_drained()


def test_projected_quota_skips_gitlinks_and_keeps_regular_index_paths():
    raw = (
        b"100644 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 0\ttracked.py\0"
        b"160000 bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 0\texternal/ccbench\0"
    )
    assert TD._tracked_regular_paths(raw) == ("tracked.py",)
    with pytest.raises(TD.DispatchError, match="malformed"):
        TD._tracked_regular_paths(
            b"100644 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 1\tstaged.py\0"
        )


def test_partial_snapshot_is_removed_after_copy_failure(tmp_path, monkeypatch):
    source, policy = _seed_source(
        tmp_path,
        policy_overrides={"min_free_bytes": 1},
    )
    dispatch_id = "20260730010203-fedcba9876543210"

    def fail_after_directory(_source, destination, _template):
        destination.mkdir()
        raise TD.DispatchError("injected copy failure")

    monkeypatch.setattr(TD, "_clone_without_external_git_state", fail_after_directory)
    scheduler = FakeScheduler(_preflight_script(policy))
    with pytest.raises(TD.DispatchError, match="injected copy failure"):
        TD.create_snapshot(
            source_root=source,
            caller_cwd=source,
            raw_args=["orchestrator/tests/test_sample.py"],
            policy=policy,
            scheduler=scheduler,
            dispatch_id=dispatch_id,
            environ={"PATH": os.environ["PATH"]},
        )
    scheduler.assert_drained()
    assert not (source.parent / policy.dispatch_root_name / dispatch_id).exists()


def test_safe_pytest_addopts_and_core_help_are_bound_and_unsafe_inputs_rejected(
    tmp_path,
):
    source = tmp_path / "repo"
    caller = source / "nested"
    target = source / "orchestrator" / "tests" / "test_one.py"
    caller.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    target.write_text("def test_one(): pass\n", encoding="utf-8")
    environment = {"PYTEST_ADDOPTS": "-q -k smoke --strict-config"}
    encoded = TD.encode_pytest_argv(
        ["-h", str(target) + "::test_one", "-n0"],
        source_root=source,
        caller_cwd=caller,
        environ=environment,
    )
    assert encoded[0] == {"kind": "literal", "value": "-h"}
    assert encoded[1] == {
        "kind": "repo_path",
        "path": "orchestrator/tests/test_one.py",
        "node": "test_one",
    }
    assert TD._runner_environment(environment, source)["PYTEST_ADDOPTS"] == (
        environment["PYTEST_ADDOPTS"]
    )
    outside = tmp_path / "outside.py"
    outside.write_text("pass\n", encoding="utf-8")
    cases = (
        ([str(outside)], {}),
        (["@args.txt"], {}),
        (["-p", "evil"], {}),
        (["--rootdir", str(source)], {}),
        (["-h"], {"PYTEST_PLUGINS": "evil"}),
        (["-h"], {"PYTHONPATH": "/tmp/evil"}),
        (["-h"], {"PYTEST_ADDOPTS": "-p evil"}),
        (["-h"], {"PYTEST_ADDOPTS": str(outside)}),
        (["--unknown-plugin-option"], {}),
    )
    for args, environ in cases:
        with pytest.raises(TD.DispatchError):
            TD.encode_pytest_argv(
                args,
                source_root=source,
                caller_cwd=caller,
                environ=environ,
            )


def test_qsub_resource_flags_match_dispatch_policy_exactly(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job = snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    authorization = snapshot.dispatch_dir / "pre-submit-authorization.json"
    result = snapshot.dispatch_dir / "runner-result.json"
    argv = TD.qsub_argv(
        snapshot=snapshot,
        policy=policy,
        authorization_path=authorization,
        runner_result_path=result,
        job_script=job,
    )
    exports = (
        f"IZANAGI_TEST_DISPATCH_ID={snapshot.dispatch_id},"
        f"IZANAGI_TEST_DISPATCH_DIR={snapshot.dispatch_dir},"
        f"IZANAGI_TEST_SNAPSHOT_ROOT={snapshot.snapshot_root},"
        f"IZANAGI_TEST_WORKER_AUTH={authorization},"
        f"IZANAGI_TEST_RUNNER_RESULT={result}"
    )
    assert argv == (
        "qsub",
        "-A", policy.account,
        "-q", policy.queue,
        "-b", str(policy.nodes),
        "-l", f"elapstim_req={policy.walltime}",
        "-N", f"izt-{snapshot.dispatch_id}",
        "-o", str(snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout"),
        "-e", str(snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr"),
        "-v", exports,
        str(job),
    )


def test_qsub_rejects_job_script_symlink_escape(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job = snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    job.unlink()
    job.symlink_to("/tmp/evil-job.sh")
    with pytest.raises(TD.DispatchError, match="regular file|closure"):
        TD.qsub_argv(
            snapshot=snapshot,
            policy=policy,
            authorization_path=(
                snapshot.dispatch_dir / "pre-submit-authorization.json"
            ),
            runner_result_path=snapshot.dispatch_dir / "runner-result.json",
            job_script=job,
        )


def test_transient_after_runner_result_recovers_running(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Running", "bnode114"))),
        (("qstat", "-f", JOB_ID), _result(rc=1, stderr="temporary")),
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Running", "bnode114"))),
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot, rc=7))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 7
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "CHILD_RESULT"
    assert filesystem.final["child_exit_status"] == 7
    assert filesystem.final["accounting"]["job_id_normalized"] == JOB_ID
    assert all(call[:2] != ("qstat", "-x") for call in scheduler.trace)
    tampered = dict(filesystem.final)
    tampered["accounting"] = dict(tampered["accounting"])
    tampered["accounting"]["lines_sha256"] = "0" * 64
    with pytest.raises(TD.DispatchError, match="accounting schema"):
        TD.validate_final_receipt_object(
            tampered,
            snapshot=snapshot,
            verify_files=False,
        )


@pytest.mark.parametrize(
    "stderr",
    [
        b"ordinary stderr only\n",
        (
            b"Request ID: 0:999.nqsv\n"
            b"Started Request Time: now\n"
            b"Ended Request Time: later\n"
            b"Elapse: 1\n"
        ),
        b"Request ID: 0:123.nqsv\nStarted Request Time: now\n",
        _accounting() + b"trailing garbage\n",
        (
            b"test forged fields\n"
            b"Request ID: 0:123.nqsv\n"
            b"Started Request Time: now\n"
            b"Ended Request Time: later\n"
            b"Elapse: 1\n"
            b"ordinary stderr after forged fields\n"
        ),
    ],
)
def test_monitor_rejects_missing_or_wrong_nqsv_accounting_footer(
    tmp_path, stderr,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot, stderr=stderr))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "ACCOUNTING_INCOMPLETE"
    assert filesystem.final["accounting"] is None


def test_monitor_rejects_accounting_group_other_than_policy_account(tmp_path):
    """R3: a terminal footer naming a foreign scheduler group is fail-closed.

    Every other token is the accepted fixture and the per-job qstat still
    reports the policy group, so the accounting group binding is the only
    check that can reject this input.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    assert policy.account == "SFC"
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(
        _monitor_files(snapshot, stderr=_accounting(group="OTHER")),
    )
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert all(call[0] != "qdel" for call in scheduler.trace)
    assert filesystem.final["dispatch_outcome"] == "ACCOUNTING_INCOMPLETE"
    assert filesystem.final["accounting"] is None
    assert (
        "accounting Group Name mismatch"
        in filesystem.final["failure_reason"]
    )


def test_monitor_accepts_accounting_group_equal_to_policy_account(tmp_path):
    """R5 positive control: the binding is the account, not another field."""
    snapshot, policy = _synthetic_snapshot(tmp_path)
    assert policy.account == "SFC"
    assert policy.queue != policy.account
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 0
    scheduler.assert_drained()
    assert all(call[0] != "qdel" for call in scheduler.trace)
    assert filesystem.final["dispatch_outcome"] == "CHILD_RESULT"
    assert filesystem.final["accounting"]["job_id_normalized"] == JOB_ID
    group_lines = [
        line for line in filesystem.final["accounting"]["lines"]
        if line.startswith("Group Name:")
    ]
    assert len(group_lines) == 1
    assert group_lines[0].split()[-1] == policy.account


def test_monitor_refuses_a_caller_policy_whose_group_left_the_snapshot(
    tmp_path,
):
    """R8: the caller cannot choose the group a final receipt is sealed with.

    `validate_final_receipt_object` re-checks the accounting footer against
    `bound_policy.account`, which is loaded from the snapshot tree. If monitor
    sealed against a different group, the sealed final would be rejected by
    every later re-validation, `_completed_dispatch` would stay false, the
    dispatch would never become a prune victim, and the retention limit would
    eventually block new dispatches. Monitor therefore refuses a caller policy
    that has left the snapshot-bound one before it polls anything.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    assert policy.account == "SFC"
    foreign = dataclasses.replace(policy, account="OTHER")
    assert foreign.policy_sha256 == snapshot.policy_sha256
    scheduler = FakeScheduler([])
    filesystem = FakeFilesystem(_monitor_files(snapshot))
    with pytest.raises(
        TD.DispatchError,
        match="monitor policy differs from snapshot-bound policy",
    ):
        _monitor(snapshot, foreign, scheduler, filesystem, FakeClock())
    assert scheduler.trace == []
    assert filesystem.final is None


def test_monitor_seals_accounting_against_the_snapshot_bound_group(
    tmp_path, monkeypatch,
):
    """R8 pin: record which policy object supplies monitor's `expected_group`.

    The registered R8 red (revert `expected_group` to the caller's `policy`)
    is not constructible through `monitor_job`: the entry binding refuses any
    caller policy that differs from the snapshot-bound one, so no input can
    separate `policy.account` from `snapshot_policy.account`. What is
    observable is the value monitor actually passes, so this records it and
    compares it against the policy document inside the snapshot tree.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    observed = []
    bound = TD.validate_nqsv_accounting

    def _record(stderr_text, job_id_normalized, *, expected_group):
        observed.append(expected_group)
        return bound(
            stderr_text, job_id_normalized, expected_group=expected_group,
        )

    monkeypatch.setattr(TD, "validate_nqsv_accounting", _record)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 0
    scheduler.assert_drained()
    snapshot_policy = TD.load_policy(
        snapshot.snapshot_root / "tools" / "pegasus" / "test_dispatch_policy.json"
    )
    assert snapshot_policy.policy_sha256 == snapshot.policy_sha256
    assert observed
    assert set(observed) == {snapshot_policy.account}


def test_missing_runner_result_is_infrastructure_failure_not_zero(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended"))),
    ])
    filesystem = FakeFilesystem({
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout": b"done\n",
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr": _accounting(),
    })
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "INFRA_FAILURE"
    assert filesystem.final["child_exit_status"] is None
    assert filesystem.final["runner_result"] is None


def test_green_task_run_event_cannot_mask_accounting_failure(tmp_path):
    durable_root = tmp_path / "task-runs"
    durable_root.mkdir()
    task_run_id = "20260730-review-fix-01234567"
    snapshot, policy = _synthetic_snapshot(
        tmp_path,
        runner_environment={
            "IZANAGI_TASK_RUN_ID": task_run_id,
            "IZANAGI_TASK_RUNS_ROOT": str(durable_root),
        },
    )
    event_id = "0123456789abcdef"
    ledger = durable_root / task_run_id / "events.jsonl"
    ledger.parent.mkdir()
    ledger_raw = TD._canonical_json({
        "event_id": event_id,
        "returncode": 0,
    })
    ledger.write_bytes(ledger_raw)
    files = _monitor_files(snapshot, stderr=b"ordinary stderr\n")
    result_path = snapshot.dispatch_dir / "runner-result.json"
    runner = json.loads(files[result_path])
    runner.update({
        "task_run_attempted": True,
        "task_run_event_id": event_id,
        "task_run_event": {
            "path": str(ledger),
            "size": len(ledger_raw),
            "sha256": hashlib.sha256(ledger_raw).hexdigest(),
            "event_id": event_id,
        },
    })
    files[result_path] = TD._canonical_json(runner)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended"))),
    ])
    filesystem = FakeFilesystem(files)
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "ACCOUNTING_INCOMPLETE"
    assert filesystem.final["task_run_event_id"] == event_id


def test_unknown_qstat_state_fails_closed_and_qdels_exact_id(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (
            ("qstat", "-f", JOB_ID),
            _result(stdout=_qstat("UnauthorizedButContainsEnded")),
        ),
        (("qdel", JOB_ID), _result()),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "CANCELED"
    assert scheduler.trace[-1] == ("qdel", JOB_ID)


def test_per_job_qstat_rejects_wrong_request_id_before_terminal_success(
    tmp_path,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (
            ("qstat", "-f", JOB_ID),
            _result(stdout=_qstat(
                "Ended",
                "bnode114",
                request_id="999.nqsv",
            )),
        ),
        (("qdel", JOB_ID), _result()),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "CANCELED"
    assert "Request ID mismatch" in filesystem.final["failure_reason"]


def test_per_job_qstat_rejects_wrong_group_before_terminal_success(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (
            ("qstat", "-f", JOB_ID),
            _result(stdout=_qstat(
                "Ended",
                "bnode114",
                group="OTHER",
            )),
        ),
        (("qdel", JOB_ID), _result()),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "CANCELED"
    assert "Group Name mismatch" in filesystem.final["failure_reason"]


def test_running_qstat_host_must_match_runner_claim_host(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Running", "bnode115"))),
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode115"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(snapshot))
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "INFRA_FAILURE"
    assert filesystem.final["child_exit_status"] is None
    assert "runner host does not match qstat" in filesystem.final["failure_reason"]


def test_state_flapping_hits_qsub_absolute_deadline_and_qdel(tmp_path):
    snapshot, policy = _synthetic_snapshot(
        tmp_path,
        policy_overrides={
            "queue_timeout_s": 10,
            "held_timeout_s": 10,
            "run_timeout_s": 5,
            "global_deadline_s": 5,
        },
    )
    scheduler = FakeScheduler([
        (
            ("qstat", "-f", JOB_ID),
            _result(stdout=_qstat("Queued" if index % 2 == 0 else "Held")),
        )
        for index in range(5)
    ] + [(("qdel", JOB_ID), _result())])
    filesystem = FakeFilesystem({
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout": b"",
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr": b"",
    })
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 124
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "CANCELED"
    assert filesystem.final["terminal_phase"] == "global-deadline"


def test_combined_spool_quota_cancels_before_another_qstat(tmp_path):
    snapshot, policy = _synthetic_snapshot(
        tmp_path,
        policy_overrides={
            "max_spool_bytes": 32,
            "replay_bytes": 16,
        },
    )
    scheduler = FakeScheduler([
        (("qdel", JOB_ID), _result()),
    ])
    filesystem = FakeFilesystem({
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout": b"x" * 20,
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr": b"y" * 20,
    })
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "CANCELED"
    assert filesystem.final["terminal_phase"] == "spool-limit"
    assert all(call[0] != "qstat" for call in scheduler.trace)


def test_qdel_retries_after_first_failure_and_latches_second_success(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    scheduler = FakeScheduler([
        (("qdel", JOB_ID), _result(rc=1, stderr="temporary")),
        (("qdel", JOB_ID), _result()),
    ])
    clock = FakeClock()
    assert TD.cancel_job(
        scheduler=scheduler,
        job_id_normalized=JOB_ID,
        policy=policy,
        journal_path=journal,
        clock=clock,
        sleep=clock.sleep,
        reason="mutation-m14",
    )
    scheduler.assert_drained()
    assert scheduler.trace.count(("qdel", JOB_ID)) == 2
    payloads = TD._journal_payloads(journal)
    assert [
        payload["attempt"]
        for payload in payloads
        if payload.get("event") == "qdel-attempt"
    ] == [1, 2]
    assert [
        payload["attempt"]
        for payload in payloads
        if payload.get("event") == "qdel-succeeded"
    ] == [2]


def test_qdel_success_before_latch_crash_resumes_without_second_qdel(
    tmp_path,
    monkeypatch,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    scheduler = FakeScheduler([(("qdel", JOB_ID), _result())])
    original_append = TD.append_journal

    def crash_before_latch(path, event, **kwargs):
        if event.get("event") == "qdel-succeeded":
            raise RuntimeError("injected crash before qdel latch")
        return original_append(path, event, **kwargs)

    monkeypatch.setattr(TD, "append_journal", crash_before_latch)
    with pytest.raises(RuntimeError, match="before qdel latch"):
        TD.cancel_job(
            scheduler=scheduler,
            job_id_normalized=JOB_ID,
            policy=policy,
            journal_path=journal,
            clock=FakeClock(),
            sleep=lambda _seconds: None,
            reason="resume-latch",
        )
    scheduler.assert_drained()
    monkeypatch.setattr(TD, "append_journal", original_append)

    resumed_scheduler = FakeScheduler([])
    assert TD.cancel_job(
        scheduler=resumed_scheduler,
        job_id_normalized=JOB_ID,
        policy=policy,
        journal_path=journal,
        clock=FakeClock(),
        sleep=lambda _seconds: None,
        reason="outer-controller-failure",
    )
    resumed_scheduler.assert_drained()
    assert len([
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "qdel-succeeded"
    ]) == 1


def test_qdel_latch_without_paired_successful_attempt_is_rejected(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    TD.append_journal(journal, {
        "event": "qdel-succeeded",
        "cancel_id": "forged",
        "job_id_normalized": JOB_ID,
        "attempt": 1,
        "monotonic_s": 0.0,
    })
    scheduler = FakeScheduler([])
    with pytest.raises(TD.DispatchError, match="success latch"):
        TD.cancel_job(
            scheduler=scheduler,
            job_id_normalized=JOB_ID,
            policy=policy,
            journal_path=journal,
            clock=FakeClock(),
            sleep=lambda _seconds: None,
            reason="must-not-be-suppressed",
        )
    scheduler.assert_drained()


def test_post_terminal_combined_spool_growth_cannot_return_child_result(
    tmp_path,
):
    snapshot, policy = _synthetic_snapshot(
        tmp_path,
        policy_overrides={"max_spool_bytes": 32},
    )
    stdout_path = (
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout"
    )
    stderr_path = (
        snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr"
    )
    files = _monitor_files(snapshot)
    files[stdout_path] = b"x" * 10
    files[stderr_path] = b"y" * 10

    class GrowingSpool(FakeFilesystem):
        def __init__(self, initial):
            super().__init__(initial)
            self.size_calls = {stdout_path: 0, stderr_path: 0}

        def size(self, path):
            path = Path(path)
            if path in self.size_calls:
                self.size_calls[path] += 1
                if self.size_calls[path] >= 2:
                    self.files[path] = (
                        b"x" * 20 if path == stdout_path else b"y" * 20
                    )
            return super().size(path)

    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended"))),
    ])
    filesystem = GrowingSpool(files)
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "INFRA_FAILURE"
    assert filesystem.final["child_exit_status"] is None
    assert "combined PBS spool" in filesystem.final["failure_reason"]


def test_retention_prunes_only_completed_exact_dispatch_directory(
    tmp_path, monkeypatch,
):
    policy_root = tmp_path / "policy-root"
    policy_root.mkdir()
    policy = _write_policy(
        policy_root,
        max_file_bytes=2048,
        max_total_bytes=4096,
        max_spool_bytes=2048,
        max_retained_bytes=8192,
        max_retained_dispatches=2,
        replay_bytes=1024,
        min_free_bytes=1,
    )
    dispatch_root = tmp_path / "dispatches"
    dispatch_root.mkdir()
    identifiers = (
        "20260730010201-0123456789abcdef",
        "20260730010202-0123456789abcdef",
    )
    for identifier in identifiers:
        directory = dispatch_root / identifier
        directory.mkdir()
        (directory / "payload").write_bytes(b"x" * 128)
        (directory / "final-receipt.json").write_bytes(TD._canonical_json({
            "dispatch_id": identifier,
            "dispatch_outcome": "CHILD_RESULT",
        }))
    assert not TD._completed_dispatch(dispatch_root / identifiers[0])
    monkeypatch.setattr(
        TD,
        "_completed_dispatch",
        lambda path: path.name == identifiers[0],
    )
    TD._prune_retention(dispatch_root, policy, projected_bytes=128)
    assert not (dispatch_root / identifiers[0]).exists()
    assert (dispatch_root / identifiers[1]).is_dir()


def test_monitor_rejects_worker_environment_hash_substitution(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    files = _monitor_files(snapshot)
    result_path = snapshot.dispatch_dir / "runner-result.json"
    result = json.loads(files[result_path])
    result["worker_environment_sha256"] = "f" * 64
    files[result_path] = TD._canonical_json(result)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(files)
    clock = FakeClock()
    assert _monitor(
        snapshot, policy, scheduler, filesystem, clock,
    ) == 125
    assert filesystem.final["dispatch_outcome"] == "INFRA_FAILURE"


def _timed_out_qsub(argv):
    """A qsub whose completion is unknown; `clean_return` is False on resume."""
    return TD.CommandResult(
        argv,
        124,
        "",
        "qsub timed out",
        timed_out=True,
        completion_unknown=True,
    )


def _unparsable_qsub_stdout(argv):
    """A clean rc 0 qsub whose stdout carries no NQSV request ID."""
    return TD.CommandResult(argv, 0, "qsub: request accepted\n", "")


def _qsub_artifacts(snapshot, policy, *, qsub_result=None):
    job = snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    authorization_path = snapshot.dispatch_dir / "pre-submit-authorization.json"
    runner_result_path = snapshot.dispatch_dir / "runner-result.json"
    argv = TD.qsub_argv(
        snapshot=snapshot,
        policy=policy,
        authorization_path=authorization_path,
        runner_result_path=runner_result_path,
        job_script=job,
    )
    _, request_sha, deadline = TD.create_qsub_request(
        snapshot,
        policy=policy,
        argv=argv,
        environment=TD.scheduler_environment(),
        job_script=job,
        qsub_started_epoch_s=0.0,
    )
    marker, authorization_sha = TD.create_pre_submit_authorization(
        snapshot,
        qsub_request_sha256=request_sha,
    )
    _, result_sha = TD.create_qsub_result(
        snapshot,
        qsub_request_sha256=request_sha,
        result=(
            TD.CommandResult(argv, 0, f"{JOB_ID_RAW}\n", "")
            if qsub_result is None else qsub_result(argv)
        ),
    )
    _, submit_sha = TD.create_submit_receipt(
        snapshot,
        authorization_sha256=authorization_sha,
        qsub_request_sha256=request_sha,
        qsub_result_sha256=result_sha,
        qsub_request_id_raw=JOB_ID_RAW,
        job_id_normalized=JOB_ID,
    )
    return {
        "job": job,
        "argv": argv,
        "marker": marker,
        "request_sha": request_sha,
        "authorization_sha": authorization_sha,
        "result_sha": result_sha,
        "submit_sha": submit_sha,
        "deadline": deadline,
    }


def _append_pre_submit_and_qsub_intent(snapshot, artifacts):
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    TD.append_journal(journal, {
        "event": "pre-submit-authorized",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "qsub_request_sha256": artifacts["request_sha"],
        "authorization_sha256": artifacts["authorization_sha"],
        "monotonic_s": 0.0,
    })
    TD.append_journal(journal, {
        "event": "qsub-intent",
        "qsub_request_sha256": artifacts["request_sha"],
        "monotonic_s": 0.0,
    })
    return journal


def _append_qsub_return(journal, snapshot, artifacts):
    result, _ = TD._load_exact_json(
        snapshot.dispatch_dir / "qsub-result.json"
    )
    TD.append_journal(journal, {
        "event": "qsub-return",
        "qsub_result_sha256": artifacts["result_sha"],
        "returncode": result["returncode"],
        "signal": result["signal"],
        "timed_out": result["timed_out"],
        "output_limited": result["output_limited"],
        "completion_unknown": result["completion_unknown"],
        "monotonic_s": 0.0,
    })


def _append_submit_identified(journal, snapshot, artifacts, *, source):
    submit, _ = TD._load_exact_json(
        snapshot.dispatch_dir / "submit-receipt.json"
    )
    TD.append_journal(journal, {
        "event": "submit-identified",
        "identification_source": source,
        "qsub_request_sha256": artifacts["request_sha"],
        "qsub_result_sha256": artifacts["result_sha"],
        "qsub_request_id_raw": submit["qsub_request_id_raw"],
        "job_id_normalized": submit["job_id_normalized"],
        "submit_receipt_sha256": artifacts["submit_sha"],
        "monotonic_s": 0.0,
    })


def _reseal_submit_receipt(
    snapshot,
    artifacts,
    *,
    qsub_request_id_raw,
    job_id_normalized,
):
    """Replace the sealed submit receipt with another internally valid one."""
    (snapshot.dispatch_dir / "submit-receipt.json").unlink()
    _, submit_sha = TD.create_submit_receipt(
        snapshot,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        qsub_request_id_raw=qsub_request_id_raw,
        job_id_normalized=job_id_normalized,
    )
    artifacts["submit_sha"] = submit_sha
    return submit_sha


def _append_matched_lookup_result(journal, snapshot, artifacts, *, group):
    """Append one matched scheduler-lookup-result; only the group is free.

    The row carries the fields `resume_dispatch` actually reads. The full
    `scheduler-lookup-result` schema (raw command receipts included) is only
    re-derived by `_validate_scheduler_lookup_chain`, which runs under
    `verify_files=True`; these fixtures publish through `FakeFilesystem` and
    never reach it.
    """
    TD.append_journal(journal, {
        "event": "scheduler-lookup-result",
        "schema": "izanagi-test-scheduler-lookup-v1",
        "attempt": 1,
        "argv": ["qstat", "-f"],
        "job_name": TD.scheduler_job_name(snapshot),
        "qsub_request_sha256": artifacts["request_sha"],
        "qsub_result_sha256": artifacts["result_sha"],
        "qsub_started_epoch_s": 0.0,
        "absolute_deadline_epoch_s": artifacts["deadline"],
        "disposition": "matched",
        "reason": "scheduler lookup matched one exact job",
        "candidates": [{
            "request_id_raw": JOB_ID_RAW,
            "job_id_normalized": JOB_ID,
            "request_name": TD.scheduler_job_name(snapshot),
            "user_name": TD.scheduler_user_name(),
            "group_name": group,
            "queue": "gen_S@nqsv",
            "account": "SFC",
            "created_epoch_s": 0,
            "state": "running",
            "execution_hosts": ["bnode114"],
        }],
        "monotonic_s": 0.0,
    })


def _write_real_dispatch_files(files):
    """Materialise monitor fixtures on the real filesystem, not in a fake."""
    for path, raw in files.items():
        TD.create_file(Path(path), raw)


def test_final_binds_exact_qsub_request_policy_job_and_raw_result(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    request_raw = (snapshot.dispatch_dir / "qsub-request.json").read_bytes()
    request = json.loads(request_raw)
    result_raw = (snapshot.dispatch_dir / "qsub-result.json").read_bytes()
    result = json.loads(result_raw)
    assert request_raw == TD._canonical_json(request)
    assert request["argv"] == list(artifacts["argv"])
    assert request["environment"] == TD.scheduler_environment()
    closure = {
        item["path"]: item
        for item in json.loads(snapshot.manifest_path.read_bytes())[
            "execution_closure"
        ]
    }
    assert request["policy"] == closure[
        "tools/pegasus/test_dispatch_policy.json"
    ]
    assert request["job_script"] == closure[
        "tools/pegasus/run_tests_job.sh"
    ]
    assert result_raw == TD._canonical_json(result)
    assert result["argv"] == request["argv"]
    assert result["stdout"]["sha256"] == hashlib.sha256(
        f"{JOB_ID_RAW}\n".encode()
    ).hexdigest()
    assert result["stderr"]["sha256"] == hashlib.sha256(b"").hexdigest()
    assert (snapshot.dispatch_dir / "qsub.rc").read_bytes() == b"0\n"


def test_worker_claim_binds_closed_environment_and_rejects_affinity_drift(
    tmp_path,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    observation = pegasus_policy.classify_site(
        "bnode114", JOB_ID_RAW, range(4)
    )
    environment = {
        "PATH": os.environ["PATH"],
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PIP_NO_INDEX": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PBS_JOBID": JOB_ID_RAW,
        "IZANAGI_TEST_DISPATCH_ID": snapshot.dispatch_id,
        "IZANAGI_TEST_DISPATCH_DIR": str(snapshot.dispatch_dir),
        "IZANAGI_TEST_SNAPSHOT_ROOT": str(snapshot.snapshot_root),
        "IZANAGI_TEST_WORKER_AUTH": str(artifacts["marker"]),
        "IZANAGI_TEST_RUNNER_RESULT": str(
            snapshot.dispatch_dir / "runner-result.json"
        ),
    }
    dependency = {
        "name": "pytest",
        "version": "1",
        "root": "/tmp",
        "distribution_files": "1",
        "distribution_files_sha256": "e" * 64,
    }
    worker = {
        "schema": "izanagi-test-worker-environment-v2",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "python_executable": sys.executable,
        "python_realpath": str(Path(sys.executable).resolve()),
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "python_flags": ["-B", "-s"],
        "sys_path": list(sys.path),
        "pytest_plugin_autoload": False,
        "environment": environment,
        "pytest": dependency,
        "pytest_xdist": {**dependency, "name": "pytest-xdist"},
        "site": {
            "hostname_raw": observation.hostname_raw,
            "hostname_canonical": observation.hostname_canonical,
            "pbs_job_id_raw": observation.pbs_job_id_raw,
            "pbs_job_id_normalized": observation.pbs_job_id_normalized,
            "affinity_cpus": list(observation.affinity_cpus),
            "site_kind": observation.site_kind.value,
        },
    }
    worker_raw = TD._canonical_json(worker)
    TD.create_file(
        snapshot.dispatch_dir / "worker-environment.json",
        worker_raw,
    )
    TD.claim_worker(
        marker_path=artifacts["marker"],
        observation=observation,
        repo_root=snapshot.snapshot_root,
        worker_environment_sha256=hashlib.sha256(worker_raw).hexdigest(),
    )
    assert not {
        "LD_PRELOAD", "PYTHONUSERBASE", "HTTP_PROXY", "HTTPS_PROXY",
    } & environment.keys()
    drifted = pegasus_policy.classify_site(
        "bnode114", JOB_ID_RAW, range(3)
    )
    with pytest.raises(TD.DispatchError, match="affinity"):
        TD.authorize_runner(
            marker_path=artifacts["marker"],
            observation=drifted,
            repo_root=snapshot.snapshot_root,
        )
    authorized = TD.authorize_runner(
        marker_path=artifacts["marker"],
        observation=observation,
        repo_root=snapshot.snapshot_root,
    )
    assert authorized["affinity_cpus"] == [0, 1, 2, 3]


def test_task_run_attempt_without_durable_event_remains_valid_child_evidence(
    tmp_path,
):
    durable_root = tmp_path / "task-runs"
    durable_root.mkdir()
    snapshot, _policy = _synthetic_snapshot(
        tmp_path,
        runner_environment={
            "IZANAGI_TASK_RUN_ID": "20260730-review-fix-01234567",
            "IZANAGI_TASK_RUNS_ROOT": str(durable_root),
        },
    )
    result = _runner_result(
        snapshot,
        worker_environment_sha256="e" * 64,
        runner_claim_sha256="f" * 64,
    )
    result["task_run_attempted"] = True
    assert TD.validate_runner_result_object(
        result,
        snapshot=snapshot,
        authorization_sha256=AUTH_SHA,
        pbs_job_id_raw=JOB_ID_RAW,
        job_id_normalized=JOB_ID,
        qsub_request_sha256=REQUEST_SHA,
        qsub_result_sha256=QSUB_RESULT_SHA,
        submit_receipt_sha256=SUBMIT_SHA,
    )["runner_exit_status"] == 0
    result["task_run_attempted"] = False
    result["task_run_event_id"] = "0123456789abcdef"
    with pytest.raises(TD.DispatchError, match="without an attempt"):
        TD.validate_runner_result_object(
            result,
            snapshot=snapshot,
            authorization_sha256=AUTH_SHA,
            pbs_job_id_raw=JOB_ID_RAW,
            job_id_normalized=JOB_ID,
        )


def test_task_run_growth_still_hashes_producer_receipt_prefix(tmp_path):
    durable_root = tmp_path / "task-runs"
    durable_root.mkdir()
    task_run_id = "20260730-review-fix-01234567"
    snapshot, _policy = _synthetic_snapshot(
        tmp_path,
        runner_environment={
            "IZANAGI_TASK_RUN_ID": task_run_id,
            "IZANAGI_TASK_RUNS_ROOT": str(durable_root),
        },
    )
    event_id = "0123456789abcdef"
    original = TD._canonical_json({
        "event_id": event_id,
        "value": "trusted",
    })
    replacement = TD._canonical_json({
        "event_id": "fedcba9876543210",
        "value": "trusted",
    })
    assert len(original) == len(replacement)
    ledger = durable_root / task_run_id / "events.jsonl"
    ledger.parent.mkdir()
    ledger.write_bytes(replacement + original)
    result = _runner_result(
        snapshot,
        worker_environment_sha256="e" * 64,
        runner_claim_sha256="f" * 64,
    )
    result.update({
        "task_run_attempted": True,
        "task_run_event_id": event_id,
        "task_run_event": {
            "path": str(ledger),
            "size": len(original),
            "sha256": hashlib.sha256(original).hexdigest(),
            "event_id": event_id,
        },
    })
    with pytest.raises(TD.DispatchError, match="ledger hash mismatch"):
        TD.validate_runner_result_object(
            result,
            snapshot=snapshot,
            authorization_sha256=AUTH_SHA,
            pbs_job_id_raw=JOB_ID_RAW,
            job_id_normalized=JOB_ID,
            qsub_request_sha256=REQUEST_SHA,
            qsub_result_sha256=QSUB_RESULT_SHA,
            submit_receipt_sha256=SUBMIT_SHA,
        )


def test_qsub_rc0_unparseable_id_recovers_single_exact_name_and_monitors(
    tmp_path,
    monkeypatch,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    job_name = TD.scheduler_job_name(snapshot)
    scheduler = FakeScheduler([
        (
            expected,
            _result(stdout="accepted without a parseable request ID\nextra\n"),
            policy.command_timeout_s,
        ),
        (
            ("qstat", "-f"),
            _result(stdout=_qstat_listing(
                ("999.nqsv", "unrelated", "Running"),
                (
                    "998.nqsv",
                    job_name,
                    "Ended",
                    {
                        "created": "Wed Dec 31 23:59:59 1969",
                    },
                ),
                (
                    "997.nqsv",
                    job_name,
                    "Queued",
                    {"user": "same-name-decoy"},
                ),
                (
                    "996.nqsv",
                    job_name,
                    "Pre-running",
                    {"group": "OTHER"},
                ),
                (JOB_ID, job_name, "Pre-running"),
            )),
            policy.command_timeout_s,
        ),
    ])
    observed = {}

    def monitor(**kwargs):
        observed.update(kwargs)
        return 0

    monkeypatch.setattr(TD, "monitor_job", monitor)
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 0
    scheduler.assert_drained()
    assert observed["qsub_request_id_raw"] == JOB_ID
    assert observed["job_id_normalized"] == JOB_ID
    assert (snapshot.dispatch_dir / "submit-receipt.json").is_file()
    payloads = TD._journal_payloads(
        snapshot.dispatch_dir / "dispatch-journal.jsonl"
    )
    lookup = [
        payload for payload in payloads
        if payload.get("event") == "scheduler-lookup-result"
    ]
    assert len(lookup) == 1
    assert lookup[0]["argv"] == ["qstat", "-f"]
    assert lookup[0]["job_name"] == job_name
    assert lookup[0]["disposition"] == "matched"
    raw = lookup[0]["raw"]
    assert set(raw) == {"stdout", "stderr", "returncode"}
    assert all(Path(receipt["path"]).is_file() for receipt in raw.values())

    submit, submit_raw = TD._load_exact_json(
        snapshot.dispatch_dir / "submit-receipt.json"
    )
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    payloads = TD._journal_payloads(journal)
    journal.unlink()
    for payload in payloads:
        rewritten = dict(payload)
        if rewritten.get("event") == "submit-identified":
            rewritten["qsub_request_id_raw"] = "999.nqsv"
            rewritten["job_id_normalized"] = "999.nqsv"
        TD.append_journal(journal, rewritten)
    with pytest.raises(TD.DispatchError, match="submit identity WAL binding"):
        TD._validate_scheduler_lookup_chain(
            snapshot=snapshot,
            policy=policy,
            qsub_request_sha256=str(submit["qsub_request_sha256"]),
            qsub_result_sha256=str(submit["qsub_result_sha256"]),
            submit=submit,
            final={"submit_receipt_sha256": hashlib.sha256(submit_raw).hexdigest()},
        )


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    (
        (
            "missing-intent",
            "scheduler lookup intent/result cardinality is invalid",
        ),
        (
            "missing-result",
            "scheduler lookup intent/result cardinality is invalid",
        ),
        (
            "duplicate-intent",
            "scheduler lookup intent/result cardinality is invalid",
        ),
        (
            "duplicate-result",
            "scheduler lookup intent/result cardinality is invalid",
        ),
        (
            "result-before-intent",
            "scheduler lookup attempt order is invalid",
        ),
        (
            "matched-id-mismatch",
            "scheduler lookup candidate is not the submitted identity",
        ),
    ),
)
def test_scheduler_lookup_chain_rejects_broken_pairing_and_identity(
    tmp_path,
    monkeypatch,
    mutation,
    expected_reason,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    job_name = TD.scheduler_job_name(snapshot)
    scheduler = FakeScheduler([
        (
            expected,
            _result(stdout="accepted without a parseable request ID\nextra\n"),
            policy.command_timeout_s,
        ),
        (
            ("qstat", "-f"),
            _result(stdout=_qstat_listing(
                (JOB_ID, job_name, "Pre-running"),
            )),
            policy.command_timeout_s,
        ),
    ])
    monkeypatch.setattr(TD, "monitor_job", lambda **_kwargs: 0)
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 0
    scheduler.assert_drained()

    submit, submit_raw = TD._load_exact_json(
        snapshot.dispatch_dir / "submit-receipt.json"
    )
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    payloads = list(TD._journal_payloads(journal))
    intent_index = next(
        index for index, payload in enumerate(payloads)
        if payload.get("event") == "scheduler-lookup-intent"
    )
    result_index = next(
        index for index, payload in enumerate(payloads)
        if payload.get("event") == "scheduler-lookup-result"
    )
    if mutation == "missing-intent":
        del payloads[intent_index]
    elif mutation == "missing-result":
        del payloads[result_index]
    elif mutation == "duplicate-intent":
        payloads.insert(intent_index + 1, dict(payloads[intent_index]))
    elif mutation == "duplicate-result":
        payloads.insert(result_index + 1, dict(payloads[result_index]))
    elif mutation == "result-before-intent":
        payloads[intent_index], payloads[result_index] = (
            payloads[result_index],
            payloads[intent_index],
        )
    else:
        assert mutation == "matched-id-mismatch"
        submit = {
            **submit,
            "qsub_request_id_raw": "999.nqsv",
            "job_id_normalized": "999.nqsv",
        }
        for index, payload in enumerate(payloads):
            if payload.get("event") == "submit-identified":
                payloads[index] = {
                    **payload,
                    "qsub_request_id_raw": "999.nqsv",
                    "job_id_normalized": "999.nqsv",
                }

    journal.unlink()
    for payload in payloads:
        TD.append_journal(journal, payload)
    final = {
        "submit_receipt_sha256": hashlib.sha256(submit_raw).hexdigest(),
        "qsub_request_id_raw": submit["qsub_request_id_raw"],
        "job_id_normalized": submit["job_id_normalized"],
    }
    with pytest.raises(TD.DispatchError, match=f"^{expected_reason}$"):
        TD._validate_scheduler_lookup_chain(
            snapshot=snapshot,
            policy=policy,
            qsub_request_sha256=str(submit["qsub_request_sha256"]),
            qsub_result_sha256=str(submit["qsub_result_sha256"]),
            submit=submit,
            final=final,
        )


def test_qsub_unknown_zero_match_retries_then_seals_submit_unknown(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    scheduler = FakeScheduler([
        (
            expected,
            _result(rc=124, timed_out=True),
            policy.command_timeout_s,
        ),
        *[
            (
                ("qstat", "-f"),
                _result(stdout=""),
                policy.command_timeout_s,
            )
            for _ in range(policy.qstat_transient_limit + 1)
        ],
    ])
    clock = FakeClock()
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=clock,
        wall_clock=lambda: 0.0,
        sleep=clock.sleep,
    ) == 125
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "SUBMIT_UNKNOWN"
    assert final["qsub_request_id_raw"] is None
    assert scheduler.trace.count(("qstat", "-f")) == (
        policy.qstat_transient_limit + 1
    )
    resumed_scheduler = FakeScheduler([])
    with pytest.raises(TD.DispatchError, match="will not re-qsub"):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=resumed_scheduler,
            policy=policy,
        )
    resumed_scheduler.assert_drained()


def test_qsub_unknown_multiple_exact_names_fails_closed(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    job_name = TD.scheduler_job_name(snapshot)
    scheduler = FakeScheduler([
        (expected, _result(stdout="not-a-job-id\nextra\n")),
        (("qstat", "-f"), _result(stdout=_qstat_listing(
            ("123.nqsv", job_name, "Queued"),
            ("124.nqsv", job_name, "Running"),
        ))),
    ])
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 125
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "SUBMIT_UNKNOWN"
    assert "multiple exact jobs" in final["failure_reason"]
    assert all(call[0] != "qdel" for call in scheduler.trace)


@pytest.mark.parametrize("lookup_output", [
    "not an NQSV qstat detail document\n",
    _qstat_listing((JOB_ID, f"izt-{DISPATCH_ID}", "UnknownState")),
])
def test_qsub_unknown_malformed_or_unknown_state_fails_closed(
    tmp_path,
    lookup_output,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    scheduler = FakeScheduler([
        (expected, _result(stdout="not-a-job-id\nextra\n")),
        (("qstat", "-f"), _result(stdout=lookup_output)),
    ])
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 125
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "SUBMIT_UNKNOWN"
    assert final["qsub_request_id_raw"] is None
    assert scheduler.trace.count(("qstat", "-f")) == 1


def test_qsub_lookup_transients_exhaust_budget_before_submit_unknown(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    scheduler = FakeScheduler([
        (expected, _result(stdout="not-a-job-id\nextra\n")),
        *[
            (("qstat", "-f"), _result(rc=1, stderr="temporary"))
            for _ in range(policy.qstat_transient_limit + 1)
        ],
    ])
    clock = FakeClock()
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=clock,
        wall_clock=lambda: 0.0,
        sleep=clock.sleep,
    ) == 125
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "SUBMIT_UNKNOWN"
    assert "transient budget exhausted" in final["failure_reason"]


def test_qsub_lookup_command_receipts_obey_scheduler_output_bound(tmp_path):
    snapshot, policy = _synthetic_snapshot(
        tmp_path,
        policy_overrides={"max_scheduler_output_bytes": 64},
    )
    job, expected = _submission_argv(snapshot, policy)
    scheduler = FakeScheduler([
        (expected, _result(stdout="not-a-job-id\nextra\n")),
        *[
            (("qstat", "-f"), _result(stdout="x" * 65, stderr="y" * 65))
            for _ in range(policy.qstat_transient_limit + 1)
        ],
    ])
    clock = FakeClock()
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=clock,
        wall_clock=lambda: 0.0,
        sleep=clock.sleep,
    ) == 125
    scheduler.assert_drained()
    payloads = TD._journal_payloads(
        snapshot.dispatch_dir / "dispatch-journal.jsonl"
    )
    results = [
        payload for payload in payloads
        if payload.get("event") == "scheduler-lookup-result"
    ]
    assert len(results) == policy.qstat_transient_limit + 1
    for result in results:
        assert result["output_limited"] is True
        assert sum(
            result["raw"][name]["size"] for name in ("stdout", "stderr")
        ) <= policy.max_scheduler_output_bytes
        assert result["raw"]["returncode"]["size"] <= len("255\n")


def test_qsub_timeout_recovers_exact_id_and_qdels_once(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    job_name = TD.scheduler_job_name(snapshot)
    scheduler = FakeScheduler([
        (expected, _result(rc=124, timed_out=True)),
        (("qstat", "-f"), _result(stdout=_qstat_listing(
            (JOB_ID, job_name, "Queued"),
        ))),
        (("qdel", JOB_ID), _result()),
    ])
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 124
    scheduler.assert_drained()
    assert scheduler.trace.count(("qdel", JOB_ID)) == 1
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "CANCELED"
    assert final["job_id_normalized"] == JOB_ID


def test_qsub_oserror_is_unknown_and_reconciled_before_cancel(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    job_name = TD.scheduler_job_name(snapshot)
    scheduler = FakeScheduler([
        (expected, OSError("accepted state is unknown")),
        (("qstat", "-f"), _result(stdout=_qstat_listing(
            (JOB_ID, job_name, "Queued"),
        ))),
        (("qdel", JOB_ID), _result()),
    ])
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 124
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "CANCELED"
    qsub_result = json.loads(
        (snapshot.dispatch_dir / "qsub-result.json").read_bytes()
    )
    assert qsub_result["returncode"] == 126
    assert qsub_result["completion_unknown"] is True


def test_real_qsub_rc126_is_definite_submit_failure_without_lookup(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    scheduler = FakeScheduler([
        (expected, _result(rc=126, stderr="qsub refused execution")),
    ])
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 125
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "SUBMIT_FAILED"
    assert scheduler.trace == [expected]


def test_qsub_stdout_id_success_path_never_invokes_lookup(tmp_path, monkeypatch):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    scheduler = FakeScheduler([
        (expected, _result(stdout=f"{JOB_ID_RAW}\n")),
    ])
    observed = {}

    def monitor(**kwargs):
        observed.update(kwargs)
        return 0

    monkeypatch.setattr(TD, "monitor_job", monitor)
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 0
    scheduler.assert_drained()
    assert observed["qsub_request_id_raw"] == JOB_ID_RAW
    assert scheduler.trace == [expected]
    assert not list(
        snapshot.dispatch_dir.glob("*-scheduler-lookup.*")
    )


def test_signal_during_qsub_recovers_exact_id_and_qdels_once(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, expected = _submission_argv(snapshot, policy)
    job_name = TD.scheduler_job_name(snapshot)
    scheduler = FakeScheduler([
        (expected, TD.ControllerSignal(signal.SIGTERM)),
        (("qstat", "-f"), _result(stdout=_qstat_listing(
            (JOB_ID, job_name, "Running"),
        ))),
        (("qdel", JOB_ID), _result()),
    ])
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 128 + signal.SIGTERM
    scheduler.assert_drained()
    assert scheduler.trace.count(("qdel", JOB_ID)) == 1
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "INTERRUPTED"
    assert final["controller_signal"] == signal.SIGTERM


def test_resume_after_submit_receipt_crash_seals_wal_and_monitors_without_qsub(
    tmp_path,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    files = _monitor_files(
        snapshot,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
    )
    clock = FakeClock()
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=FakeFilesystem(files),
    ) == 0
    scheduler.assert_drained()
    assert all(call[0] != "qsub" for call in scheduler.trace)
    submit_events = [
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "submit-identified"
    ]
    assert len(submit_events) == 1
    assert set(submit_events[0]) == {
        "event", "identification_source", "qsub_request_sha256",
        "qsub_result_sha256", "qsub_request_id_raw", "job_id_normalized",
        "submit_receipt_sha256", "monotonic_s",
    }
    assert submit_events[0]["identification_source"] == "qsub-result-resume"


def test_resume_rejects_submit_receipt_job_id_absent_from_qsub_stdout(tmp_path):
    """R1: a receipt naming a foreign NQSV request cannot drive qdel/monitor.

    The receipt is internally consistent (`normalize_job_id(raw) == normalized`)
    and every hash in its chain is the real one, so `_validate_submit_object`
    accepts it. Only the comparison against the hash-bound `qsub.stdout`
    receipt can reject it.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    _reseal_submit_receipt(
        snapshot,
        artifacts,
        qsub_request_id_raw="0:999.nqsv",
        job_id_normalized="999.nqsv",
    )
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    assert (snapshot.dispatch_dir / "qsub.stdout").read_text(
        encoding="utf-8",
    ) == f"{JOB_ID_RAW}\n"
    scheduler = FakeScheduler([])
    with pytest.raises(TD.DispatchError, match="differs from the qsub.stdout"):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=scheduler,
            policy=policy,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
            filesystem=FakeFilesystem({}),
        )
    assert scheduler.trace == []
    assert not (snapshot.dispatch_dir / "final-receipt.json").exists()
    assert not [
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "submit-identified"
    ]


def test_resume_rejects_submit_receipt_raw_prefix_absent_from_qsub_stdout(
    tmp_path,
):
    """R2: the raw request ID is compared too, not only its normalisation."""
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    _reseal_submit_receipt(
        snapshot,
        artifacts,
        qsub_request_id_raw=JOB_ID,
        job_id_normalized=JOB_ID,
    )
    assert TD.normalize_job_id(JOB_ID_RAW) == TD.normalize_job_id(JOB_ID)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    scheduler = FakeScheduler([])
    with pytest.raises(TD.DispatchError, match="differs from the qsub.stdout"):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=scheduler,
            policy=policy,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
            filesystem=FakeFilesystem({}),
        )
    assert scheduler.trace == []
    assert not (snapshot.dispatch_dir / "final-receipt.json").exists()


def test_resume_accepts_submit_receipt_identity_equal_to_qsub_stdout(tmp_path):
    """R1/R2 positive control: the sealed identity still resumes into monitor."""
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(
        snapshot,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
    ))
    clock = FakeClock()
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=filesystem,
    ) == 0
    scheduler.assert_drained()
    assert all(call[0] != "qdel" for call in scheduler.trace)
    assert filesystem.final["dispatch_outcome"] == "CHILD_RESULT"
    assert filesystem.final["qsub_request_id_raw"] == JOB_ID_RAW
    assert filesystem.final["job_id_normalized"] == JOB_ID
    assert len([
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "submit-identified"
    ]) == 1


def test_resume_rejects_submit_receipt_absent_from_submit_identified_wal(
    tmp_path,
):
    """R7: the unknown-completion branch is bound to the WAL identity row.

    `qsub` timed out, so `completion_unknown` is true, `clean_return` is false
    and `qsub.stdout` is empty: the qsub.stdout comparison cannot see this
    input at all. What survives is the `submit-identified` row that
    `_recover_submission_identity` appended before it sealed the receipt, and
    that is the same row `_validate_scheduler_lookup_chain` already compares
    against the receipt at publish time. The receipt is replaced afterwards,
    exactly as an attacker with one artifact write would leave it.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy, qsub_result=_timed_out_qsub)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_submit_identified(
        journal,
        snapshot,
        artifacts,
        source="scheduler-lookup",
    )
    _reseal_submit_receipt(
        snapshot,
        artifacts,
        qsub_request_id_raw="0:999.nqsv",
        job_id_normalized="999.nqsv",
    )
    qsub_result = json.loads(
        (snapshot.dispatch_dir / "qsub-result.json").read_bytes()
    )
    assert qsub_result["completion_unknown"] is True
    assert (snapshot.dispatch_dir / "qsub.stdout").read_text(
        encoding="utf-8",
    ) == ""
    scheduler = FakeScheduler([])
    with pytest.raises(
        TD.DispatchError,
        match="differs from the submit-identified WAL receipt",
    ):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=scheduler,
            policy=policy,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
            filesystem=FakeFilesystem({}),
        )
    assert scheduler.trace == []
    assert not (snapshot.dispatch_dir / "final-receipt.json").exists()


def test_resume_accepts_unknown_completion_receipt_bound_by_the_wal(tmp_path):
    """R7 positive control: the sealed identity still reaches its one qdel.

    Same branch and same fixture as the red above, with the receipt left
    alone. An unknown qsub completion must still be reconciled and canceled,
    so a rejection here would be a liveness regression rather than a closure.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy, qsub_result=_timed_out_qsub)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_submit_identified(
        journal,
        snapshot,
        artifacts,
        source="scheduler-lookup",
    )
    scheduler = FakeScheduler([(("qdel", JOB_ID), _result())])
    filesystem = FakeFilesystem({})
    clock = FakeClock()
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=filesystem,
    ) == 124
    scheduler.assert_drained()
    assert scheduler.trace == [("qdel", JOB_ID)]
    assert filesystem.final["dispatch_outcome"] == "CANCELED"
    assert filesystem.final["job_id_normalized"] == JOB_ID
    assert filesystem.final["qsub_request_id_raw"] == JOB_ID_RAW
    assert len([
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "submit-identified"
    ]) == 1


def test_resume_rejects_forged_receipt_when_qsub_stdout_cannot_be_parsed(
    tmp_path,
):
    """R7: the rc 0 / unparsable-stdout branch is bound to the WAL row too.

    `parse_qsub_id` fails on this `qsub.stdout`, so the stdout comparison
    returns without an opinion. This is a state the controller really reaches
    (`submit_and_monitor` runs `_recover_submission_identity` whenever
    `parse_qsub_id` fails on a clean return), and before this binding the
    receipt identity was adopted there without any comparison at all.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(
        snapshot,
        policy,
        qsub_result=_unparsable_qsub_stdout,
    )
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_submit_identified(
        journal,
        snapshot,
        artifacts,
        source="scheduler-lookup",
    )
    _reseal_submit_receipt(
        snapshot,
        artifacts,
        qsub_request_id_raw="0:999.nqsv",
        job_id_normalized="999.nqsv",
    )
    qsub_result = json.loads(
        (snapshot.dispatch_dir / "qsub-result.json").read_bytes()
    )
    assert qsub_result["returncode"] == 0
    assert qsub_result["completion_unknown"] is False
    with pytest.raises(TD.DispatchError):
        TD.parse_qsub_id(
            (snapshot.dispatch_dir / "qsub.stdout").read_text(encoding="utf-8")
        )
    scheduler = FakeScheduler([])
    with pytest.raises(
        TD.DispatchError,
        match="differs from the submit-identified WAL receipt",
    ):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=scheduler,
            policy=policy,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
            filesystem=FakeFilesystem({}),
        )
    assert scheduler.trace == []
    assert not (snapshot.dispatch_dir / "final-receipt.json").exists()


def test_resume_accepts_unparsable_qsub_stdout_receipt_bound_by_the_wal(
    tmp_path,
):
    """R7 positive control: an unparsable `qsub.stdout` still resumes.

    The stdout witness abstains here, so acceptance rests entirely on the WAL
    row agreeing with the receipt. Rejecting this input would strand every
    dispatch whose request ID was recovered by lookup on a clean return.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(
        snapshot,
        policy,
        qsub_result=_unparsable_qsub_stdout,
    )
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_submit_identified(
        journal,
        snapshot,
        artifacts,
        source="scheduler-lookup",
    )
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(
        snapshot,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
    ))
    clock = FakeClock()
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=filesystem,
    ) == 0
    scheduler.assert_drained()
    assert all(call[0] != "qdel" for call in scheduler.trace)
    assert filesystem.final["dispatch_outcome"] == "CHILD_RESULT"
    assert filesystem.final["job_id_normalized"] == JOB_ID


def test_resume_refuses_a_submit_receipt_no_hash_bound_evidence_witnesses(
    tmp_path,
):
    """The receipt is never adopted on its own word; fail-closed by default.

    Every writer of `submit-receipt.json` leaves a witness behind first: a
    matched `scheduler-lookup-result` row (`_recover_submission_identity`) or
    a `qsub.stdout` that `parse_qsub_id` accepted. A dispatch with neither is
    not a state the controller can produce, so this pins the fail-closed
    default rather than a reachable series; no artifact impact is claimed.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(
        snapshot,
        policy,
        qsub_result=_unparsable_qsub_stdout,
    )
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    assert not [
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") in {
            "submit-identified", "scheduler-lookup-result",
        }
    ]
    scheduler = FakeScheduler([])
    with pytest.raises(TD.DispatchError, match="no hash-bound witness"):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=scheduler,
            policy=policy,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
            filesystem=FakeFilesystem({}),
        )
    assert scheduler.trace == []
    assert not (snapshot.dispatch_dir / "final-receipt.json").exists()


def test_resume_rejects_lookup_wal_candidate_from_another_group(tmp_path):
    """R6: resume reads the matched WAL row as strictly as lookup replay does.

    The candidate is correct in every term but `group_name`; `account` is kept
    at the policy value so the group term is isolated, and the group mismatch
    carries its own message so no other term can turn this red green.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_matched_lookup_result(journal, snapshot, artifacts, group="OTHER")
    scheduler = FakeScheduler([])
    with pytest.raises(
        TD.DispatchError,
        match="candidate group is not the policy account",
    ):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=scheduler,
            policy=policy,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
            filesystem=FakeFilesystem({}),
        )
    assert scheduler.trace == []
    assert not (snapshot.dispatch_dir / "final-receipt.json").exists()
    assert not [
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "submit-identified"
    ]


def test_resume_accepts_lookup_wal_candidate_from_the_policy_group(tmp_path):
    """R6 positive control: the same candidate at the policy group is adopted."""
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_matched_lookup_result(journal, snapshot, artifacts, group="SFC")
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(_monitor_files(
        snapshot,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
    ))
    clock = FakeClock()
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=filesystem,
    ) == 0
    scheduler.assert_drained()
    assert scheduler.trace == [("qstat", "-f", JOB_ID)]
    assert filesystem.final["dispatch_outcome"] == "CHILD_RESULT"
    submit_events = [
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "submit-identified"
    ]
    assert len(submit_events) == 1
    assert submit_events[0]["identification_source"] == "scheduler-lookup"


def test_real_filesystem_final_receipt_rechecks_accounting_group_on_resume(
    tmp_path,
):
    """R4: cover the published-final accounting re-check on a real filesystem.

    `validate_final_receipt_object` only re-parses the accounting footer when
    `verify_files=True` and `accounting` is not None. No other test reaches
    that pair, so this drives a real `PathMonitorFilesystem` monitor to a
    sealed `final-receipt.json` and resumes the same dispatch directory.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    assert policy.account == "SFC"
    artifacts = _qsub_artifacts(snapshot, policy)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_submit_identified(
        journal,
        snapshot,
        artifacts,
        source="qsub-result",
    )
    _write_real_dispatch_files(_monitor_files(
        snapshot,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
    ))
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    clock = FakeClock()
    assert TD.monitor_job(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
        qsub_request_id_raw=JOB_ID_RAW,
        job_id_normalized=JOB_ID,
        qsub_started_epoch_s=0.0,
        absolute_deadline_epoch_s=artifacts["deadline"],
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
    ) == 0
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "CHILD_RESULT"
    assert final["accounting"]["job_id_normalized"] == JOB_ID
    group_lines = [
        line for line in final["accounting"]["lines"]
        if line.startswith("Group Name:")
    ]
    assert len(group_lines) == 1
    assert group_lines[0].split()[-1] == policy.account

    resumed = FakeScheduler([])
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=resumed,
        policy=policy,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 0
    assert resumed.trace == []


def test_resume_rejects_published_final_sealed_with_a_foreign_group(
    tmp_path, monkeypatch,
):
    """R4 site: an already-sealed foreign-group receipt cannot be re-adopted.

    Monitor is driven with a stand-in for a controller that predates the group
    binding, so a wrong-group footer reaches `final-receipt.json` with an
    otherwise exact hash chain. Resume then re-validates it for real.
    """
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_submit_identified(
        journal,
        snapshot,
        artifacts,
        source="qsub-result",
    )
    _write_real_dispatch_files(_monitor_files(
        snapshot,
        stderr=_accounting(group="OTHER"),
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
    ))
    bound = TD.validate_nqsv_accounting

    def _seal_without_group_binding(
        stderr_text, job_id_normalized, *, expected_group,
    ):
        return bound(stderr_text, job_id_normalized, expected_group="OTHER")

    monkeypatch.setattr(
        TD, "validate_nqsv_accounting", _seal_without_group_binding,
    )
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    clock = FakeClock()
    assert TD.monitor_job(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
        qsub_request_id_raw=JOB_ID_RAW,
        job_id_normalized=JOB_ID,
        qsub_started_epoch_s=0.0,
        absolute_deadline_epoch_s=artifacts["deadline"],
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
    ) == 0
    scheduler.assert_drained()
    monkeypatch.undo()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "CHILD_RESULT"
    group_lines = [
        line for line in final["accounting"]["lines"]
        if line.startswith("Group Name:")
    ]
    assert group_lines[0].split()[-1] == "OTHER"

    resumed = FakeScheduler([])
    with pytest.raises(
        TD.DispatchError,
        match="accounting Group Name mismatch",
    ):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=resumed,
            policy=policy,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
        )
    assert resumed.trace == []


def test_resume_after_qsub_result_crash_seals_return_and_submit(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    (snapshot.dispatch_dir / "submit-receipt.json").unlink()
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    files = _monitor_files(
        snapshot,
        authorization_sha256=artifacts["authorization_sha"],
        qsub_request_sha256=artifacts["request_sha"],
        qsub_result_sha256=artifacts["result_sha"],
        submit_receipt_sha256=artifacts["submit_sha"],
    )
    clock = FakeClock()
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=FakeFilesystem(files),
    ) == 0
    scheduler.assert_drained()
    events = TD._journal_payloads(journal)
    assert len([
        event for event in events if event.get("event") == "qsub-return"
    ]) == 1
    submit_events = [
        event for event in events if event.get("event") == "submit-identified"
    ]
    assert len(submit_events) == 1
    assert submit_events[0]["identification_source"] == "qsub-result-resume"
    assert (
        TD.sha256_file(snapshot.dispatch_dir / "submit-receipt.json")
        == artifacts["submit_sha"]
    )


def test_resume_after_qsub_intent_crash_looks_up_and_qdels_without_re_qsub(
    tmp_path,
):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, argv = _submission_argv(snapshot, policy)
    _, request_sha, _ = TD.create_qsub_request(
        snapshot,
        policy=policy,
        argv=argv,
        environment=TD.scheduler_environment(),
        job_script=job,
        qsub_started_epoch_s=0.0,
    )
    _, authorization_sha = TD.create_pre_submit_authorization(
        snapshot,
        qsub_request_sha256=request_sha,
    )
    artifacts = {
        "request_sha": request_sha,
        "authorization_sha": authorization_sha,
    }
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    scheduler = FakeScheduler([
        (("qstat", "-f"), _result(stdout=_qstat_listing(
            (JOB_ID, TD.scheduler_job_name(snapshot), "Queued"),
        ))),
        (("qdel", JOB_ID), _result()),
    ])
    clock = FakeClock()
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
    ) == 124
    scheduler.assert_drained()
    assert all(call[0] != "qsub" for call in scheduler.trace)
    assert scheduler.trace.count(("qdel", JOB_ID)) == 1
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "CANCELED"
    assert final["job_id_normalized"] == JOB_ID
    result = json.loads(
        (snapshot.dispatch_dir / "qsub-result.json").read_bytes()
    )
    assert result["returncode"] == 126
    assert result["completion_unknown"] is True
    assert len([
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "qsub-return"
    ]) == 1


def test_resume_lookup_cannot_reset_qsub_absolute_deadline(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job, argv = _submission_argv(snapshot, policy)
    _, request_sha, deadline = TD.create_qsub_request(
        snapshot,
        policy=policy,
        argv=argv,
        environment=TD.scheduler_environment(),
        job_script=job,
        qsub_started_epoch_s=0.0,
    )
    _, authorization_sha = TD.create_pre_submit_authorization(
        snapshot,
        qsub_request_sha256=request_sha,
    )
    journal = _append_pre_submit_and_qsub_intent(snapshot, {
        "request_sha": request_sha,
        "authorization_sha": authorization_sha,
    })
    scheduler = FakeScheduler([])
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=FakeClock(),
        wall_clock=lambda: deadline + 1,
        sleep=lambda _seconds: None,
    ) == 125
    scheduler.assert_drained()
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "SUBMIT_UNKNOWN"
    assert "absolute/visibility deadline exhausted" in final["failure_reason"]
    assert not [
        payload for payload in TD._journal_payloads(journal)
        if payload.get("event") == "scheduler-lookup-intent"
    ]


def test_resume_after_cancel_intent_crash_completes_one_qdel(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    artifacts = _qsub_artifacts(snapshot, policy)
    journal = _append_pre_submit_and_qsub_intent(snapshot, artifacts)
    _append_qsub_return(journal, snapshot, artifacts)
    _append_submit_identified(
        journal,
        snapshot,
        artifacts,
        source="qsub-result",
    )
    recovery = {
        "success_outcome": "CONTROLLER_FAILURE",
        "failure_outcome": "CONTROLLER_CANCEL_FAILED",
        "success_status": 125,
        "failure_status": 125,
        "success_signal": None,
        "failure_signal": None,
        "terminal_phase": "controller",
        "failure_reason": "injected controller crash",
    }
    crashing_scheduler = FakeScheduler([
        (("qdel", JOB_ID), RuntimeError("crash before qdel result")),
    ])
    with pytest.raises(RuntimeError, match="before qdel result"):
        TD.cancel_job(
            scheduler=crashing_scheduler,
            job_id_normalized=JOB_ID,
            policy=policy,
            journal_path=journal,
            clock=FakeClock(),
            sleep=lambda _seconds: None,
            reason="controller-failure",
            recovery=recovery,
        )
    crashing_scheduler.assert_drained()

    scheduler = FakeScheduler([(("qdel", JOB_ID), _result())])
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=scheduler,
        policy=policy,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 125
    scheduler.assert_drained()
    assert scheduler.trace.count(("qdel", JOB_ID)) == 1
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "CONTROLLER_FAILURE"


def test_receipt_write_failure_after_job_id_qdels(tmp_path, monkeypatch):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job = snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    expected = TD.qsub_argv(
        snapshot=snapshot,
        policy=policy,
        authorization_path=(
            snapshot.dispatch_dir / "pre-submit-authorization.json"
        ),
        runner_result_path=snapshot.dispatch_dir / "runner-result.json",
        job_script=job,
    )
    scheduler = FakeScheduler([
        (expected, _result(stdout=f"{JOB_ID_RAW}\n")),
        (("qdel", JOB_ID), _result()),
    ])

    def fail_result(*_args, **_kwargs):
        raise OSError("injected ENOSPC")

    monkeypatch.setattr(TD, "create_qsub_result", fail_result)
    with pytest.raises(TD.DispatchError, match="receipt sealing failure"):
        TD.submit_and_monitor(
            snapshot=snapshot,
            scheduler=scheduler,
            policy=policy,
            job_script=job,
            clock=FakeClock(),
            wall_clock=lambda: 0.0,
            sleep=lambda _seconds: None,
        )
    scheduler.assert_drained()
    assert scheduler.trace.count(("qdel", JOB_ID)) == 1


def test_sigterm_after_submit_qdels_once(tmp_path, monkeypatch):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    job = snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    expected = TD.qsub_argv(
        snapshot=snapshot,
        policy=policy,
        authorization_path=(
            snapshot.dispatch_dir / "pre-submit-authorization.json"
        ),
        runner_result_path=snapshot.dispatch_dir / "runner-result.json",
        job_script=job,
    )
    scheduler = FakeScheduler([
        (expected, _result(stdout=f"{JOB_ID_RAW}\n")),
        (("qdel", JOB_ID), _result()),
    ])

    def interrupted_monitor(**_kwargs):
        raise TD.ControllerSignal(signal.SIGTERM)

    monkeypatch.setattr(TD, "monitor_job", interrupted_monitor)
    assert TD.submit_and_monitor(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        job_script=job,
        clock=FakeClock(),
        wall_clock=lambda: 0.0,
        sleep=lambda _seconds: None,
    ) == 128 + signal.SIGTERM
    scheduler.assert_drained()
    assert scheduler.trace.count(("qdel", JOB_ID)) == 1
    final = json.loads(
        (snapshot.dispatch_dir / "final-receipt.json").read_bytes()
    )
    assert final["dispatch_outcome"] == "INTERRUPTED"
    assert final["controller_signal"] == signal.SIGTERM


def test_resume_after_final_publish_crash_uses_pending_document(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    scheduler = FakeScheduler([
        (("qstat", "-f", JOB_ID), _result(stdout=_qstat("Ended", "bnode114"))),
    ])
    filesystem = FakeFilesystem(
        _monitor_files(snapshot),
        fail_publish_count=1,
    )
    clock = FakeClock()
    with pytest.raises(OSError, match="final publication crash"):
        _monitor(snapshot, policy, scheduler, filesystem, clock)
    scheduler.assert_drained()
    assert filesystem.exists(snapshot.dispatch_dir / "final-pending.json")
    assert not filesystem.exists(snapshot.dispatch_dir / "final-receipt.json")

    resumed_scheduler = FakeScheduler([])
    assert TD.resume_dispatch(
        dispatch_dir=snapshot.dispatch_dir,
        scheduler=resumed_scheduler,
        policy=policy,
        clock=clock,
        wall_clock=clock,
        sleep=clock.sleep,
        filesystem=filesystem,
    ) == 0
    resumed_scheduler.assert_drained()
    assert filesystem.final["dispatch_outcome"] == "CHILD_RESULT"


def test_journal_hash_chain_detects_rewrite(tmp_path):
    journal = tmp_path / "dispatch-journal.jsonl"
    TD.append_journal(journal, {"event": "one"})
    TD.append_journal(journal, {"event": "two"})
    lines = journal.read_bytes().splitlines(keepends=True)
    first = json.loads(lines[0])
    first["payload"]["event"] = "rewritten"
    lines[0] = TD._canonical_json(first)
    journal.write_bytes(b"".join(lines))
    with pytest.raises(TD.DispatchError, match="hash chain"):
        TD.journal_head_sha256(journal)


def test_append_journal_requires_injected_durability_sync(tmp_path):
    journal = tmp_path / "dispatch-journal.jsonl"
    synced = []

    def sync(fd):
        synced.append(fd)

    head = TD.append_journal(
        journal,
        {"event": "durability-m10"},
        sync=sync,
    )
    assert len(synced) == 1
    assert isinstance(synced[0], int)
    assert head == TD.journal_head_sha256(journal)


def test_resume_rejects_incomplete_final_status_zero(tmp_path):
    snapshot, policy = _synthetic_snapshot(tmp_path)
    TD.create_file(
        snapshot.dispatch_dir / "final-receipt.json",
        TD._canonical_json({"controller_exit_status": 0}),
    )
    scheduler = FakeScheduler([])
    with pytest.raises(TD.DispatchError, match="schema|identity"):
        TD.resume_dispatch(
            dispatch_dir=snapshot.dispatch_dir,
            scheduler=scheduler,
            policy=policy,
        )
    scheduler.assert_drained()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-x"]))
