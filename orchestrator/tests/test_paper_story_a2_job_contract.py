import hashlib
import inspect
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

from orchestrator.campaign import paper_story_a2_certification as A2


REPO = Path(__file__).resolve().parents[2]
JOB = REPO / "tools/pegasus/paper_story_a2_certification.sh"
SUBMITTER = REPO / "tools/pegasus/submit_paper_story_a2_certification.sh"
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
        "workload-input": "IZANAGI_A2_WORKLOAD",
        "workload-enum": "rr5|rr50",
        "job-root": 'job_root=$attempt/jobs/$workload',
        "dependency-stage": "cp -a \"$dependency_source\"/. \"$dependency_prefix\"/",
        "fresh-raw": "if [[ -e \"$raw_root\" || -L \"$raw_root\" ]]",
        "preflight": "compute-preflight",
        "interpreter-candidates": (
            "for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do"),
        "interpreter-version": "sys.version_info >= (3, 10)",
        "interpreter-import": (
            "import orchestrator.campaign.paper_story_a2_certification"),
        "interpreter-fail-closed": "resolve_python || exit 2",
        "interpreter-path": 'export PATH="$(dirname "$selected"):$PATH"',
        "scratch-sanitize": 'pbs_jobid_path_component=${PBS_JOBID//:/_}',
        "scratch-path": 'scratch=$scratch_base/${pbs_jobid_path_component}',
    }
    missing = [label for label, fragment in required.items() if fragment not in source]
    if missing:
        raise AssertionError("job contract missing: " + ",".join(missing))
    if "q" + "sub" in source:
        raise AssertionError("compute job body must not submit another job")
    if "scratch=$scratch_base/${PBS_JOBID}" in source:
        raise AssertionError("PBS_JOBID must not be a literal scratch path element")
    if source.count('"$PY" - "') != 2:
        raise AssertionError("both inline Python launches must use the selected path")
    driver_launch = (
        '"$PY" -B -m orchestrator.campaign.paper_story_a2_certification')
    if source.count(driver_launch) != 2:
        raise AssertionError("both driver launches must use the selected path")
    resolver_call = source.index("resolve_python || exit 2")
    first_python_use = source.index('"$PY" - "')
    if resolver_call >= first_python_use:
        raise AssertionError("interpreter resolution must precede Python use")
    if source.count('--workload "$workload"') != 2:
        raise AssertionError("preflight and run must use the selected workload")
    if "finalize-raw" in source:
        raise AssertionError("compute body must not finalize the group manifest")


def test_job_body_is_compute_only_sequential_and_never_submits():
    _assert_static_job_contract(JOB.read_text(encoding="utf-8"))
    submitter = SUBMITTER.read_text(encoding="utf-8")
    assert "WORKLOADS=(rr5 rr50)" in submitter
    assert "IZANAGI_A2_WORKLOAD=$workload" in submitter
    assert "ratified-qsub -- qsub" in submitter
    assert "finish-group" in submitter
    assert submitter.index("submission-precheck") < submitter.index("check_quota")
    assert submitter.index("submission-precheck") < submitter.index(
        "ratified-qsub -- qsub")
    finish_start = submitter.index('if [[ "$MODE" == finish-group ]]')
    finish_exit = submitter.index("  exit 0", finish_start)
    for submit_only_gate in (
            "for command_name in git qsub", "check_quota >/dev/null",
            "QUEUE_STATE=$(qstat -Q)",
            'git status --porcelain --untracked-files=no'):
        assert finish_exit < submitter.index(submit_only_gate)
    precheck = inspect.getsource(A2.submission_ratification_precheck)
    assert precheck.index("capture_contract_loader_binding()") < precheck.index(
        "verify_ratified_contract_loader_binding(binding)")


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
    assert 'qstat_jobid=${PBS_JOBID#0:}' in source
    assert '"$workload" "$rc" "$PBS_JOBID" "$IZANAGI_A2_CURRENT_PIN"' in source


def _resolver_snippet(source):
    start = source.index("resolve_python() {")
    call = "resolve_python || exit 2"
    end = source.index(call, start) + len(call)
    return source[start:end]


def test_interpreter_resolver_prepends_selected_path_for_child_processes(tmp_path):
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    selected = binary_dir / "python3.10"
    selected.symlink_to(Path(sys.executable))
    bare = binary_dir / "python3"
    bare.symlink_to(selected)
    source = JOB.read_text(encoding="utf-8")
    script = (
        "set -euo pipefail\n"
        f"repo={shlex.quote(str(REPO))}\n"
        + _resolver_snippet(source)
        + "\nprintf '%s\\n' \"$PY\"\n"
        + "command -v python3\n"
        + "\"$PY\" -c 'import sys; print(sys.executable)'\n"
    )
    environment = dict(os.environ)
    environment["PATH"] = str(binary_dir) + os.pathsep + environment["PATH"]
    completed = subprocess.run(
        ["bash", "-c", script], cwd=REPO, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    selected_line, bare_line, executable_line = completed.stdout.splitlines()
    assert Path(selected_line) == selected
    assert Path(selected_line).samefile(bare_line)
    assert Path(selected_line).samefile(executable_line)


def test_interpreter_resolver_rejects_version_ok_but_a2_unimportable_candidate(
        tmp_path):
    wrapper = tmp_path / "python3.10"
    wrapper.write_text(
        "#!/bin/bash\n"
        f"exec {shlex.quote(sys.executable)} -I \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    source = JOB.read_text(encoding="utf-8")
    snippet = _resolver_snippet(source).replace(
        "for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do",
        f"for candidate in {shlex.quote(str(wrapper))}; do",
        1,
    )
    script = (
        "set -euo pipefail\n"
        f"repo={shlex.quote(str(REPO))}\n"
        + snippet
        + "\nprintf 'unexpected:%s\\n' \"${PY:-bare-python3}\"\n"
    )
    completed = subprocess.run(
        ["bash", "-c", script], cwd=REPO,
        env=dict(os.environ), capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert (
        "no Python 3.10+ interpreter can import the A-2 driver"
        in completed.stderr
    )


def test_interpreter_resolver_call_precedes_first_python_use():
    source = JOB.read_text(encoding="utf-8")
    resolver_call = "resolve_python || exit 2"
    assert source.index(resolver_call) < source.index('"$PY" - "')
    mutant = source.replace(resolver_call, "", 1) + "\n" + resolver_call + "\n"
    with pytest.raises(AssertionError, match="resolution must precede"):
        _assert_static_job_contract(mutant)


def test_pbs_jobid_path_sanitization_is_load_bearing():
    source = JOB.read_text(encoding="utf-8")
    _assert_static_job_contract(source)
    mutant = source.replace(
        'pbs_jobid_path_component=${PBS_JOBID//:/_}',
        'pbs_jobid_path_component=$PBS_JOBID',
        1,
    )
    with pytest.raises(AssertionError, match="scratch-sanitize"):
        _assert_static_job_contract(mutant)
    completed = subprocess.run(
        ["bash", "-c", (
            'PBS_JOBID="0:945411.nqsv"; '
            'pbs_jobid_path_component=${PBS_JOBID//:/_}; '
            'printf "%s\\n" "$pbs_jobid_path_component"')],
        capture_output=True, text=True, check=True,
    )
    assert completed.stdout == "0_945411.nqsv\n"
    assert ":" not in completed.stdout


@pytest.mark.parametrize("fragment", (
    "^bnode[0-9]+([.].*)?$",
    "git rev-parse HEAD",
    "git status --porcelain --untracked-files=no",
    "if [[ -e \"$raw_root\" || -L \"$raw_root\" ]]",
    "sys.version_info >= (3, 10)",
    "import orchestrator.campaign.paper_story_a2_certification",
    'export PATH="$(dirname "$selected"):$PATH"',
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
    assert registry["tools/pegasus/submit_paper_story_a2_certification.sh"] == {
        "class": "local-ok",
        "reason": (
            "login-side PBS paper-story A-2 two-workload submitter and finisher"),
        "primary_gate": (
            "ratification precheck then qsub fan-out; compute work stays in "
            "independent job bodies"),
        "evidence": "static login-side submitter classification",
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
    attempt = A2.preregister_attempt(policy, "compute-positive", "1" * 40)
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
        policy, workload_id="rr5", attempt_root=attempt,
        raw_root=attempt / "jobs" / "rr5" / "raw",
        expected_head="head-1", repo_root=repo,
        dependency_prefix=dependency, environ=environment,
        hostname="bnode001")
    assert raw == attempt / "jobs" / "rr5" / "raw"
    assert (attempt / "jobs" / "rr50").is_dir()
    assert raw.is_dir()
    assert calls == [
        ["git", "rev-parse", "HEAD"],
        ["git", "status", "--porcelain", "--untracked-files=no"],
    ]


@pytest.mark.parametrize("mutation", ("login-host", "wrong-head", "dirty", "stale-raw"))
def test_compute_preflight_rejects_each_m7_boundary(tmp_path, monkeypatch, mutation):
    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(
        policy, "compute-" + mutation, "1" * 40)
    dependency = tmp_path / ("deps-" + mutation)
    dependency.mkdir()
    repo = REPO
    race_target = attempt / "jobs" / "rr5" / "raw"
    if mutation == "stale-raw":
        original_mkdir = Path.mkdir

        def racing_mkdir(path, *args, **kwargs):
            if path == race_target:
                original_mkdir(path, mode=0o700)
            return original_mkdir(path, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", racing_mkdir)

    def run(command, **kwargs):
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            value = "wrong\n" if mutation == "wrong-head" else "head-1\n"
            return _completed(command, value)
        if command[:3] == ["git", "status", "--porcelain"]:
            return _completed(command, " M tracked\n" if mutation == "dirty" else "")
        raise AssertionError(command)

    monkeypatch.setattr(A2.subprocess, "run", run)
    environment = _reservation_environment(repo)
    with pytest.raises(A2.CertificationError) as error:
        A2.compute_preflight(
            policy, workload_id="rr5", attempt_root=attempt,
            raw_root=attempt / "jobs" / "rr5" / "raw",
            expected_head="head-1", repo_root=repo,
            dependency_prefix=dependency, environ=environment,
            hostname="pegasus01" if mutation == "login-host" else "bnode001")
    if mutation == "stale-raw":
        assert isinstance(error.value.__cause__, FileExistsError)
        assert race_target.is_dir()


def test_compute_preflight_requires_real_pbs_and_reservation_bindings(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(policy, "compute-env", "1" * 40)
    dependency = tmp_path / "deps-env"
    dependency.mkdir()
    repo = REPO
    monkeypatch.setattr(
        A2.subprocess, "run",
        lambda command, **kwargs: _completed(command, "head-1\n"),
    )
    with pytest.raises(A2.CertificationError, match="PBS environment"):
        A2.compute_preflight(
            policy, workload_id="rr5", attempt_root=attempt,
            raw_root=attempt / "jobs" / "rr5" / "raw",
            expected_head="head-1", repo_root=repo,
            dependency_prefix=dependency, environ={}, hostname="bnode001")


def test_job_body_mode_is_executable():
    assert os.stat(JOB).st_mode & 0o111
    assert os.stat(SUBMITTER).st_mode & 0o111


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
