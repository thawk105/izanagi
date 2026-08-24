import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from orchestrator.campaign import paper_story_a2_certification as A2


REPO = Path(__file__).resolve().parents[2]
JOB = REPO / "tools/pegasus/paper_story_a2_certification.sh"
REGISTRY = REPO / "tools/pegasus/admission_registry.json"


def _policy(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(tmp_path / "durable-a2")
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return A2.load_policy(path)


def _assert_static_job_contract(source):
    required = {
        "compute-only": "^bnode[0-9]+([.].*)?$",
        "expected-head": "git rev-parse HEAD",
        "ccbench-pin": "git -C \"$ccbench_root\" rev-parse HEAD",
        "clean-tree": "git status --porcelain --untracked-files=no",
        "pbs-job": "PBS_JOBID PBS_NODEFILE PBS_O_WORKDIR",
        "reservation": 'export IZANAGI_RESERVATION_DEADLINE_EPOCH="$deadline_epoch"',
        "scheduler-start": 'qstat -f "$qstat_jobid"',
        "reservation-result": "paper-story-a2-reservation-result/v1",
        "dependency-source": "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE",
        "dependency-stage": "cp -a \"$dependency_source\"/. \"$dependency_prefix\"/",
        "fresh-raw": "if [[ -e \"$raw_root\" || -L \"$raw_root\" ]]",
        "preflight": "compute-preflight",
    }
    missing = [label for label, fragment in required.items() if fragment not in source]
    if missing:
        raise AssertionError("job contract missing: " + ",".join(missing))
    if "q" + "sub" in source:
        raise AssertionError("compute job body must not submit another job")
    rr5 = source.index("--workload rr5")
    rr50 = source.index("--workload rr50")
    if rr5 >= rr50:
        raise AssertionError("workload order must be rr5 then rr50")


def test_job_body_is_compute_only_sequential_and_never_submits():
    _assert_static_job_contract(JOB.read_text(encoding="utf-8"))


def test_job_body_exports_the_exact_reservation_schema_from_job_observations():
    source = JOB.read_text(encoding="utf-8")
    expected = {
        'IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"',
        'IZANAGI_RESERVATION_REQUESTED_S="$requested_s"',
        'IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$scheduler_started_epoch"',
        'IZANAGI_RESERVATION_DEADLINE_EPOCH="$deadline_epoch"',
        'IZANAGI_RESERVATION_HOST="$host"',
        'IZANAGI_RESERVATION_BOOT_ID="$boot_id"',
        'IZANAGI_RESERVATION_SCRIPT_SHA256="$script_sha256"',
        'IZANAGI_RESERVATION_NONCE="$PBS_JOBID"',
    }
    assert all(f"export {fragment}" in source for fragment in expected)
    assert "IZANAGI_RESERVATION_DEADLINE=" not in source


@pytest.mark.parametrize("fragment", (
    "^bnode[0-9]+([.].*)?$",
    "git rev-parse HEAD",
    "git status --porcelain --untracked-files=no",
    "if [[ -e \"$raw_root\" || -L \"$raw_root\" ]]",
))
def test_m7_each_expected_head_compute_only_clean_and_fresh_gate_is_load_bearing(
        fragment):
    source = JOB.read_text(encoding="utf-8")
    assert fragment in source
    mutant = source.replace(fragment, "", 1)
    with pytest.raises(AssertionError, match="job contract missing"):
        _assert_static_job_contract(mutant)


def test_job_body_is_registered_only_as_dispatch_required():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    entry = registry["tools/pegasus/paper_story_a2_certification.sh"]
    assert entry == {
        "class": "dispatch-required",
        "reason": "PBS paper-story A-2 certification job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }


def _completed(command, stdout="", returncode=0):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="")


def _reservation_environment(repo, *, job_id="123.nqsv"):
    started = int(time.time()) - 1
    requested = 6 * 3600
    return {
        "PBS_JOBID": job_id,
        "PBS_NODEFILE": "/nodefile",
        "PBS_O_WORKDIR": str(repo),
        "IZANAGI_RESERVATION_JOB_ID": job_id,
        "IZANAGI_RESERVATION_REQUESTED_S": str(requested),
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested),
        "IZANAGI_RESERVATION_HOST": "bnode001",
        "IZANAGI_RESERVATION_BOOT_ID": Path(
            "/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
        "IZANAGI_RESERVATION_SCRIPT_SHA256": hashlib.sha256(JOB.read_bytes()).hexdigest(),
        "IZANAGI_RESERVATION_NONCE": job_id,
    }


def test_compute_preflight_accepts_exact_compute_head_and_fresh_raw(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    attempt = A2.create_attempt_root(policy, "compute-positive")
    dependency = tmp_path / "dependency-prefix"
    dependency.mkdir()
    repo = REPO
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return _completed(command, "head-1\n")
        if command[:3] == ["git", "status", "--porcelain"]:
            return _completed(command, "")
        raise AssertionError(command)

    monkeypatch.setattr(A2.subprocess, "run", run)
    environment = _reservation_environment(repo)
    raw = A2.compute_preflight(
        policy, attempt_root=attempt, raw_root=attempt / "raw",
        expected_head="head-1", repo_root=repo,
        dependency_prefix=dependency, environ=environment,
        hostname="bnode001")
    assert raw == attempt / "raw"
    assert raw.is_dir()
    assert calls == [
        ["git", "rev-parse", "HEAD"],
        ["git", "status", "--porcelain", "--untracked-files=no"],
    ]


@pytest.mark.parametrize("mutation", ("login-host", "wrong-head", "dirty", "stale-raw"))
def test_compute_preflight_rejects_each_m7_boundary(tmp_path, monkeypatch, mutation):
    policy = _policy(tmp_path)
    attempt = A2.create_attempt_root(policy, "compute-" + mutation)
    dependency = tmp_path / ("deps-" + mutation)
    dependency.mkdir()
    repo = REPO
    if mutation == "stale-raw":
        (attempt / "raw").mkdir()

    def run(command, **kwargs):
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            value = "wrong\n" if mutation == "wrong-head" else "head-1\n"
            return _completed(command, value)
        if command[:3] == ["git", "status", "--porcelain"]:
            return _completed(command, " M tracked\n" if mutation == "dirty" else "")
        raise AssertionError(command)

    monkeypatch.setattr(A2.subprocess, "run", run)
    environment = _reservation_environment(repo)
    with pytest.raises(A2.CertificationError):
        A2.compute_preflight(
            policy, attempt_root=attempt, raw_root=attempt / "raw",
            expected_head="head-1", repo_root=repo,
            dependency_prefix=dependency, environ=environment,
            hostname="pegasus01" if mutation == "login-host" else "bnode001")


def test_compute_preflight_requires_real_pbs_and_reservation_bindings(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    attempt = A2.create_attempt_root(policy, "compute-env")
    dependency = tmp_path / "deps-env"
    dependency.mkdir()
    repo = REPO
    monkeypatch.setattr(
        A2.subprocess, "run",
        lambda command, **kwargs: _completed(command, "head-1\n"),
    )
    with pytest.raises(A2.CertificationError, match="PBS environment"):
        A2.compute_preflight(
            policy, attempt_root=attempt, raw_root=attempt / "raw",
            expected_head="head-1", repo_root=repo,
            dependency_prefix=dependency, environ={}, hostname="bnode001")


def test_job_body_mode_is_executable():
    assert os.stat(JOB).st_mode & 0o111
