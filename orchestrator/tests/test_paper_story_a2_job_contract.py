import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

from orchestrator.campaign import paper_story_a2_certification as A2
from orchestrator.campaign import pin


REPO = Path(__file__).resolve().parents[2]
JOB = REPO / "tools/pegasus/paper_story_a2_certification.sh"
SUBMITTER = REPO / "tools/pegasus/submit_paper_story_a2_certification.sh"
REGISTRY = REPO / "tools/pegasus/admission_registry.json"
CANONICAL_PIN = pin.CURRENT_PIN


def _policy(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(tmp_path / "durable-a2")
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return A2.load_policy(path)


def _a6_policy(tmp_path):
    document = json.loads(A2.A6_POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(tmp_path / "durable-a6")
    path = tmp_path / "a6-policy.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return A2.load_policy(path)


def _assert_static_job_contract(source):
    required = {
        "compute-only": "^bnode[0-9]+([.].*)?$",
        "expected-head": "git rev-parse HEAD",
        "ccbench-head": (
            "git -C \"$ccbench_root\" rev-parse --verify 'HEAD^{commit}'"),
        "ccbench-pin-resolver": (
            'git -C "$ccbench_root" rev-parse --verify '
            '"${IZANAGI_A2_CURRENT_PIN}^{commit}"'),
        "repository-canonical-pin": (
            "'from orchestrator.campaign.pin import CURRENT_PIN; "
            "print(CURRENT_PIN)'"),
        "ccbench-short-pin": (
            '"$IZANAGI_A2_CURRENT_PIN" =~ ^[0-9a-f]{7}$'),
        "ccbench-repository-pin": (
            '"$IZANAGI_A2_CURRENT_PIN" != "$repository_current_pin"'),
        "ccbench-exact-pin": (
            '"$ccbench_full_head" != "$resolved_current_pin"'),
        "ccbench-literal-prefix": (
            '"$ccbench_full_head" != "$IZANAGI_A2_CURRENT_PIN"*'),
        "clean-tree": "git status --porcelain --untracked-files=no",
        "pbs-job": "PBS_JOBID PBS_NODEFILE PBS_O_WORKDIR",
        "pbs-job-number-shape": (
            'if [[ ! "$PBS_JOBID" =~ ^(0|[1-9][0-9]*):(.+)$ ]]; then'),
        "pbs-primary-job-number": (
            'if [[ "$pbs_job_number" != 0 ]]; then'),
        "pbs-secondary-job-exit": (
            'echo "nonzero PBS job number exits without running compute body" '
            '>&2\n  exit 0'),
        "reservation": 'export IZANAGI_RESERVATION_DEADLINE_EPOCH="$deadline_epoch"',
        "scheduler-start": 'qstat -f "$qstat_jobid"',
        "reservation-result": "paper-story-a2-reservation-result/v1",
        "dependency-source": "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE",
        "third-party-source": "IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT",
        "workload-input": "IZANAGI_A2_WORKLOAD",
        "workload-membership": "a2.workload_ids(policy).count(workload) != 1",
        "job-root": 'job_root=$attempt/jobs/$workload',
        "dependency-stage": "cp -a \"$dependency_source\"/. \"$dependency_prefix\"/",
        "masstree-stage": (
            "cp -a \"$third_party_source/masstree\" "
            "\"$third_party_root/masstree-src\""),
        "mimalloc-stage": (
            "cp -a \"$third_party_source/mimalloc\" "
            "\"$third_party_root/mimalloc-src\""),
        "googletest-stage": (
            "cp -a \"$third_party_source/googletest\" "
            "\"$third_party_root/googletest-src\""),
        "third-party-run-argument": (
            '--third-party-source-root "$third_party_root"'),
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
        "policy-node-count": 'print(policy.document["scheduler"]["nodes"])',
        "nodefile-regular": 'if [[ ! -f "$PBS_NODEFILE" || -L "$PBS_NODEFILE" ]]',
        "nodefile-unique-siblings": 'sibling_hosts+=("$node")',
        "nodefile-policy-count": (
            '${#sibling_hosts[@]} != expected_siblings'),
        "nodefile-fatal": (
            'echo "PBS node allocation differs from scheduler policy"'),
        "fanout-only-multinode": 'if (( SCHEDULER_NODES > 1 )); then',
        "fanout-cli": 'VERIFY_FANOUT_ARGS=(--verify-fanout-hosts',
        "fanout-forward": '"${VERIFY_FANOUT_ARGS[@]}"',
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
    job_root_check = source.index('if [[ ! -d "$repo"')
    job_number_gate = source.index(
        'if [[ ! "$PBS_JOBID" =~ ^(0|[1-9][0-9]*):(.+)$ ]]; then')
    nonzero_job_exit = source.index(
        'if [[ "$pbs_job_number" != 0 ]]; then\n'
        '  echo "nonzero PBS job number exits without running compute body" '
        '>&2\n'
        '  exit 0\n'
        'fi')
    host_gate = source.index("host=$(hostname")
    trap_install = source.index("trap finish EXIT")
    policy_resolution = source.index("readarray -t POLICY_VALUES")
    if not job_number_gate < nonzero_job_exit < host_gate < job_root_check:
        raise AssertionError(
            "job number gate and nonzero exit must precede compute and "
            "durable path checks")
    if not job_root_check < trap_install < resolver_call < policy_resolution:
        raise AssertionError(
            "job root must precede the recovery trap, which must cover "
            "interpreter and policy resolution")
    if source.count('--workload "$workload"') != 2:
        raise AssertionError("preflight and run must use the selected workload")
    if "finalize-raw" in source:
        raise AssertionError("compute body must not finalize the group manifest")


def _assert_static_submitter_pin_contract(source):
    required = {
        "canonical-pin": (
            "CURRENT_PIN=$(\"$PYTHON_BIN\" -B -c "
            "'from orchestrator.campaign.pin import CURRENT_PIN; "
            "print(CURRENT_PIN)')"),
        "short-pin": '"$CURRENT_PIN" =~ ^[0-9a-f]{7}$',
        "full-head": (
            "git -C \"$CCBENCH_ROOT\" rev-parse --verify 'HEAD^{commit}'"),
        "pin-resolver": (
            'git -C "$CCBENCH_ROOT" rev-parse --verify '
            '"${CURRENT_PIN}^{commit}"'),
        "exact-resolution": (
            '"$CCBENCH_FULL_HEAD" == "$CANONICAL_FULL_HEAD"'),
        "literal-prefix": '"$CCBENCH_FULL_HEAD" == "$CURRENT_PIN"*',
        "prereg-short": '--current-pin "$CURRENT_PIN"',
        "qsub-short": "IZANAGI_A2_CURRENT_PIN=$CURRENT_PIN",
        "receipt-short": '"current_pin": current',
    }
    missing = [label for label, fragment in required.items() if fragment not in source]
    if missing:
        raise AssertionError(
            "submitter pin contract missing: " + ",".join(missing))


def test_job_body_is_compute_only_sequential_and_never_submits():
    _assert_static_job_contract(JOB.read_text(encoding="utf-8"))
    submitter = SUBMITTER.read_text(encoding="utf-8")
    _assert_static_submitter_pin_contract(submitter)
    assert 'WORKLOADS=("${POLICY_VALUES[@]:8}")' in submitter
    assert "for workload in a2.workload_ids(policy):" in submitter
    assert 'JOB_NAME=${POLICY_VALUES[2]}' in submitter
    assert 'SCHEDULER_WALLTIME=${POLICY_VALUES[6]}' in submitter
    assert "IZANAGI_A2_WORKLOAD=$workload" in submitter
    assert "exact-qsub -- qsub" in submitter
    assert "set -o noclobber" in submitter
    assert 'exec {qsub_stdout_fd}>"$qsub_stdout_path"' in submitter
    assert 'exec {qsub_stderr_fd}>"$qsub_stderr_path"' in submitter
    assert submitter.index("durabilize-qsub-diagnostics") < submitter.index(
        'request_id=$("$PYTHON_BIN"')
    assert "finish-group" in submitter
    assert "submission-precheck" not in submitter
    finish_start = submitter.index('if [[ "$MODE" == finish-group ]]')
    finish_exit = submitter.index("  exit 0", finish_start)
    for submit_only_gate in (
            "for command_name in git qsub", "check_quota >/dev/null",
            "QUEUE_STATE=$(qstat -Q)",
            'git status --porcelain --untracked-files=no'):
        assert finish_exit < submitter.index(submit_only_gate)
    assert not hasattr(A2, "submission_ratification_precheck")


def test_m8_full_pin_forwarding_and_missing_exact_resolver_are_killed():
    submitter = SUBMITTER.read_text(encoding="utf-8")
    _assert_static_submitter_pin_contract(submitter)
    full_pin_mutant = submitter.replace(
        "CURRENT_PIN=$(\"$PYTHON_BIN\" -B -c "
        "'from orchestrator.campaign.pin import CURRENT_PIN; "
        "print(CURRENT_PIN)')",
        'CURRENT_PIN=$(git -C "$CCBENCH_ROOT" rev-parse --verify '
        "'HEAD^{commit}')",
        1,
    )
    with pytest.raises(AssertionError, match="canonical-pin"):
        _assert_static_submitter_pin_contract(full_pin_mutant)
    submitter_prefix_mutant = submitter.replace(
        '    && "$CCBENCH_FULL_HEAD" == "$CURRENT_PIN"*',
        "",
        1,
    )
    with pytest.raises(AssertionError, match="literal-prefix"):
        _assert_static_submitter_pin_contract(submitter_prefix_mutant)

    job = JOB.read_text(encoding="utf-8")
    _assert_static_job_contract(job)
    resolver_mutant = job.replace(
        'git -C "$ccbench_root" rev-parse --verify '
        '"${IZANAGI_A2_CURRENT_PIN}^{commit}"',
        'printf "%s\\n" "$IZANAGI_A2_CURRENT_PIN"',
        1,
    )
    with pytest.raises(AssertionError, match="ccbench-pin-resolver"):
        _assert_static_job_contract(resolver_mutant)

    prefix_mutant = job.replace(
        '   || "$ccbench_full_head" != "$IZANAGI_A2_CURRENT_PIN"*',
        "",
        1,
    )
    with pytest.raises(AssertionError, match="ccbench-literal-prefix"):
        _assert_static_job_contract(prefix_mutant)


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
        "reason": "PBS paper-story A-2/A-6 policy-selected certification job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }
    assert registry["tools/pegasus/submit_paper_story_a2_certification.sh"] == {
        "class": "local-ok",
        "reason": (
            "login-side PBS paper-story A-2/A-6 policy-selected submitter and finisher"),
        "primary_gate": (
            "policy-scoped precheck then qsub fan-out; compute work stays in "
            "independent job bodies"),
        "evidence": "static login-side submitter classification",
    }


def _completed(command, stdout="", returncode=0):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="")


def _write_executable(path, source):
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)


def _write_qstat_inventory_fixture(tmp_path, request_names):
    base = (
        REPO / "orchestrator/tests/fixtures/paper_story_a2"
        / "qstat-visibility-fanout-945411.stdout"
    ).read_text(encoding="utf-8")
    records = []
    for index, request_name in enumerate(request_names):
        request_id = f"{945410 + index}.nqsv"
        record = base.replace(
            "Request ID: 945411.nqsv", f"Request ID: {request_id}", 1)
        record = record.replace(
            "    Request Name = paper-a2-cert",
            f"    Request Name = {request_name}",
            1,
        )
        records.append(record.rstrip("\n"))
    path = tmp_path / "qstat-inventory.stdout"
    path.write_text("\n\n".join(records) + ("\n" if records else ""),
                    encoding="utf-8")
    return path


def _run_submitter_harness(
        tmp_path, *, inventory_rc=0, stop_at_preregister=False,
        visibility_rc=23, visibility_fail_workload="rr5",
        inventory_names=(), inventory_stderr="", queue_state="gen_S ENA ACT\n",
        qsub_fail_workload="", qsub_rc=29,
        qsub_stderr_workload="", qsub_stderr_text="qsub diagnostic\n",
        precreate_diagnostic="", ccbench_head=None, resolved_pin=None,
        resolver_rc=0, tracked_dirty=False, study="a2",
        exercise_finish_group=False, third_party_argument=None,
        third_party_mutation=None):
    a2_policy = _policy(tmp_path)
    a6_policy = _a6_policy(tmp_path)
    policy = a6_policy if study == "a6" else a2_policy
    workloads = A2.workload_ids(policy)
    first_workload = workloads[0]
    attempt_id = "submitter-harness"
    attempt_root = policy.durable_base / attempt_id
    ccbench = tmp_path / "ccbench"
    dependency = tmp_path / "dependency"
    third_party = tmp_path / "third-party"
    ccbench.mkdir()
    dependency.mkdir()
    third_party.mkdir()
    for name in ("masstree", "mimalloc", "googletest"):
        (third_party / name).mkdir()
    if third_party_mutation == "missing-child":
        (third_party / "googletest").rmdir()
    elif third_party_mutation == "symlink-child":
        (third_party / "googletest").rmdir()
        (third_party / "googletest").symlink_to(
            third_party / "masstree", target_is_directory=True)
    elif third_party_mutation == "symlink-root":
        link = tmp_path / "third-party-link"
        link.symlink_to(third_party, target_is_directory=True)
        third_party_argument = link
    elif third_party_mutation == "canonical-comma":
        unsafe_parent = tmp_path / "actual,parent"
        unsafe_parent.mkdir()
        third_party.rename(unsafe_parent / "third-party")
        safe_alias = tmp_path / "safe-alias"
        safe_alias.symlink_to(unsafe_parent, target_is_directory=True)
        third_party_argument = safe_alias / "third-party"
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    driver_log = tmp_path / "driver.log"
    event_log = tmp_path / "event.log"
    qsub_log_dir = tmp_path / "qsub-log"
    qsub_log_dir.mkdir()
    inventory_fixture = _write_qstat_inventory_fixture(
        tmp_path, inventory_names)
    driver_log.touch()
    event_log.touch()
    if ccbench_head is None:
        ccbench_head = CANONICAL_PIN + "1" * (40 - len(CANONICAL_PIN))
    if resolved_pin is None:
        resolved_pin = ccbench_head

    _write_executable(binary_dir / "hostname", r"""#!/bin/bash
printf '%s\n' pegasus01
""")
    _write_executable(binary_dir / "check_quota", r"""#!/bin/bash
exit 0
""")
    _write_executable(binary_dir / "git", fr"""#!/bin/bash
if [[ ${{1:-}} == -C && ${{3:-}} == rev-parse && ${{4:-}} == --verify \
    && ${{5:-}} == 'HEAD^{{commit}}' ]]; then
  printf '%s\n' "$A2_TEST_CCBENCH_HEAD"
  exit 0
fi
if [[ ${{1:-}} == -C && ${{3:-}} == rev-parse && ${{4:-}} == --verify \
    && ${{5:-}} == '{CANONICAL_PIN}^{{commit}}' ]]; then
  if [[ "$A2_TEST_RESOLVER_RC" -ne 0 ]]; then
    exit "$A2_TEST_RESOLVER_RC"
  fi
  printf '%s\n' "$A2_TEST_RESOLVED_PIN"
  exit 0
fi
if [[ ${{1:-}} == rev-parse && ${{2:-}} == HEAD ]]; then
  printf '%s\n' {'2' * 40}
  exit 0
fi
if [[ $* == *status* ]]; then
  if [[ ${{1:-}} == -C && "$A2_TEST_TRACKED_DIRTY" == 1 ]]; then
    printf '%s\n' ' M tracked.cc'
  fi
  exit 0
fi
exit 97
""")
    _write_executable(binary_dir / "grep", r"""#!/bin/bash
exit 77
""")
    _write_executable(binary_dir / "qsub", r"""#!/bin/bash
workload=""
previous=""
for argument in "$@"; do
  if [[ "$previous" == -v ]]; then
    case "$argument" in
      *IZANAGI_A2_WORKLOAD=rr5,*) workload=rr5 ;;
      *IZANAGI_A2_WORKLOAD=rr50,*) workload=rr50 ;;
      *IZANAGI_A2_WORKLOAD=rr95,*) workload=rr95 ;;
    esac
  fi
  previous=$argument
done
[[ -n "$workload" ]] || exit 93
printf 'qsub:%s\n' "$workload" >>"$A2_TEST_EVENT_LOG"
printf '%s\0' "$@" >"$A2_TEST_QSUB_LOG_DIR/$workload.argv"
scheduler="$A2_TEST_ATTEMPT_ROOT/jobs/$workload/scheduler"
[[ -f "$scheduler/qsub.stdout" && ! -L "$scheduler/qsub.stdout" \
    && -f "$scheduler/qsub.stderr" && ! -L "$scheduler/qsub.stderr" \
    && /proc/$$/fd/1 -ef "$scheduler/qsub.stdout" \
    && /proc/$$/fd/2 -ef "$scheduler/qsub.stderr" ]] || exit 92
if [[ "$A2_TEST_QSUB_FAIL_WORKLOAD" == "$workload" ]]; then
  printf '%s' "$A2_TEST_QSUB_STDERR_TEXT" >&2
  exit "$A2_TEST_QSUB_RC"
fi
request=945411.nqsv
[[ "$workload" == rr50 ]] && request=945412.nqsv
[[ "$workload" == rr95 ]] && request=945413.nqsv
printf 'Request %s submitted\n' "$request"
if [[ "$A2_TEST_QSUB_STDERR_WORKLOAD" == "$workload" ]]; then
  printf '%s' "$A2_TEST_QSUB_STDERR_TEXT" >&2
fi
exit 0
""")
    _write_executable(binary_dir / "qstat", r"""#!/bin/bash
if [[ ${1:-} == -Q ]]; then
  printf '%s' "$A2_TEST_QUEUE_STATE"
  exit 0
fi
if [[ $# -eq 1 && ${1:-} == -f ]]; then
  printf '%s\n' inventory >>"$A2_TEST_EVENT_LOG"
  /bin/cat "$A2_TEST_INVENTORY_FIXTURE"
  printf '%s' "$A2_TEST_INVENTORY_STDERR" >&2
  exit "$A2_TEST_INVENTORY_RC"
fi
if [[ $# -eq 2 && ${1:-} == -f ]]; then
  request=${2#0:}
  request=${request%.}
  workload=rr5
  if [[ "$request" == 945412.nqsv ]]; then
    workload=rr50
  elif [[ "$request" == 945413.nqsv ]]; then
    workload=rr95
  elif [[ "$request" != 945411.nqsv ]]; then
    exit 89
  fi
  scheduler="$A2_TEST_ATTEMPT_ROOT/jobs/$workload/scheduler"
  sidecar="$scheduler/request-id"
  if [[ ! -f "$sidecar" || -L "$sidecar" ]]; then
    printf '%s\n' 'request ID sidecar was absent before visibility' >&2
    exit 91
  fi
  if [[ ! -f "$scheduler/qsub.stdout" || ! -f "$scheduler/qsub.stderr" ]]; then
    printf '%s\n' 'qsub diagnostics were absent before visibility' >&2
    exit 90
  fi
  printf 'visibility:%s\n' "$workload" >>"$A2_TEST_EVENT_LOG"
  if [[ "$A2_TEST_VISIBILITY_FAIL_WORKLOAD" == "$workload" ]]; then
    printf '%s\n' 'visibility unavailable' >&2
    exit "$A2_TEST_VISIBILITY_RC"
  fi
  exec /bin/cat \
    "$A2_TEST_QSTAT_FIXTURES/qstat-visibility-fanout-${request%%.*}.stdout"
fi
exit 96
""")
    python_wrapper = binary_dir / "a2-python"
    _write_executable(python_wrapper, r"""#!/usr/bin/env python3
import os
import sys
from pathlib import Path

args = sys.argv[1:]
with Path(os.environ["A2_TEST_DRIVER_LOG"]).open("a", encoding="utf-8") as stream:
    stream.write(" ".join(args) + "\n")

def production_a2():
    from dataclasses import replace
    sys.path.insert(0, os.environ["A2_TEST_REPO"])
    from orchestrator.campaign import paper_story_a2_certification as a2
    original_load_policy = a2.load_policy
    loaded_a2 = replace(
        original_load_policy(Path(os.environ["A2_TEST_A2_POLICY"])),
        path=a2.POLICY_PATH,
    )
    loaded_a6 = replace(
        original_load_policy(Path(os.environ["A2_TEST_A6_POLICY"])),
        path=a2.A6_POLICY_PATH,
    )

    def load_fixture_policy(path=a2.POLICY_PATH):
        selected = Path(path).resolve()
        if selected == a2.POLICY_PATH.resolve():
            return loaded_a2
        if selected == a2.A6_POLICY_PATH.resolve():
            return loaded_a6
        return original_load_policy(path)

    a2.load_policy = load_fixture_policy
    a2.socket.gethostname = lambda: "pegasus01"
    return a2

if "-m" in args:
    module_index = args.index("-m")
    if (module_index + 1 < len(args) and args[module_index + 1]
            == "orchestrator.campaign.paper_story_a2_certification"):
        command_argv = args[module_index + 2:]
        if ("preregister" in command_argv
                and os.environ["A2_TEST_STOP_AT_PREREGISTER"] == "1"):
            raise SystemExit(37)
        a2 = production_a2()
        rc = a2.main(command_argv)
        if (rc == 0 and "preregister" in command_argv
                and os.environ["A2_TEST_PRECREATE_DIAGNOSTIC"]):
            target = (Path(os.environ["A2_TEST_ATTEMPT_ROOT"])
                      / "jobs" / os.environ["A2_TEST_FIRST_WORKLOAD"] / "scheduler"
                      / os.environ["A2_TEST_PRECREATE_DIAGNOSTIC"])
            target.write_text("sentinel\n", encoding="utf-8")
        raise SystemExit(rc)

if "-" in args:
    script_index = args.index("-")
    if any(value.endswith("/qsub.stdout") for value in args[script_index + 1:]):
        driver_lines = Path(os.environ["A2_TEST_DRIVER_LOG"]).read_text(
            encoding="utf-8").splitlines()
        if (len(driver_lines) < 2
                or "durabilize-qsub-diagnostics" not in driver_lines[-2]):
            raise SystemExit(94)
    source = sys.stdin.read()
    production_a2()
    sys.argv = ["-", *args[script_index + 1:]]
    namespace = {"__name__": "__main__", "__file__": "<stdin>"}
    exec(compile(source, "<stdin>", "exec"), namespace, namespace)
    raise SystemExit(0)

os.execv(sys.executable, [sys.executable, *args])
""")
    environment = dict(os.environ)
    environment.update({
        "PATH": str(binary_dir) + os.pathsep + environment["PATH"],
        "PYTHON": str(python_wrapper),
        "PYTHONDONTWRITEBYTECODE": "1",
        "A2_TEST_REPO": str(REPO),
        "A2_TEST_A2_POLICY": str(a2_policy.path),
        "A2_TEST_A6_POLICY": str(a6_policy.path),
        "A2_TEST_ATTEMPT_ROOT": str(attempt_root),
        "A2_TEST_FIRST_WORKLOAD": first_workload,
        "A2_TEST_STUDY": study,
        "A2_TEST_DRIVER_LOG": str(driver_log),
        "A2_TEST_INVENTORY_RC": str(inventory_rc),
        "A2_TEST_INVENTORY_FIXTURE": str(inventory_fixture),
        "A2_TEST_INVENTORY_STDERR": inventory_stderr,
        "A2_TEST_QUEUE_STATE": queue_state,
        "A2_TEST_STOP_AT_PREREGISTER": (
            "1" if stop_at_preregister else "0"),
        "A2_TEST_VISIBILITY_RC": str(visibility_rc),
        "A2_TEST_VISIBILITY_FAIL_WORKLOAD": visibility_fail_workload,
        "A2_TEST_QSTAT_FIXTURES": str(
            REPO / "orchestrator/tests/fixtures/paper_story_a2"),
        "A2_TEST_QSUB_FAIL_WORKLOAD": qsub_fail_workload,
        "A2_TEST_QSUB_RC": str(qsub_rc),
        "A2_TEST_QSUB_STDERR_WORKLOAD": qsub_stderr_workload,
        "A2_TEST_QSUB_STDERR_TEXT": qsub_stderr_text,
        "A2_TEST_QSUB_LOG_DIR": str(qsub_log_dir),
        "A2_TEST_EVENT_LOG": str(event_log),
        "A2_TEST_PRECREATE_DIAGNOSTIC": precreate_diagnostic,
        "A2_TEST_CCBENCH_HEAD": ccbench_head,
        "A2_TEST_RESOLVED_PIN": resolved_pin,
        "A2_TEST_RESOLVER_RC": str(resolver_rc),
        "A2_TEST_TRACKED_DIRTY": "1" if tracked_dirty else "0",
    })
    command = [str(SUBMITTER)]
    if study == "a6":
        command.extend(["--policy", str(A2.A6_POLICY_PATH)])
    command.extend([
        "--attempt-id", attempt_id,
        "--ccbench-root", str(ccbench),
        "--dependency-prefix-source", str(dependency),
        "--third-party-source-root", str(
            third_party if third_party_argument is None
            else third_party_argument
        ),
    ])
    completed = subprocess.run(
        command,
        cwd=REPO, env=environment, capture_output=True, text=True, check=False,
    )
    if exercise_finish_group and completed.returncode == 0:
        finish_command = [str(SUBMITTER), "finish-group"]
        if study == "a6":
            finish_command.extend(["--policy", str(A2.A6_POLICY_PATH)])
        finish_command.extend(["--attempt-id", attempt_id])
        subprocess.run(
            finish_command, cwd=REPO, env=environment,
            capture_output=True, text=True, check=False,
        )
    return completed, attempt_root, driver_log.read_text(encoding="utf-8")


def _run_compute_pin_harness(
        tmp_path, *, ccbench_head=None, resolved_pin=None, resolver_rc=0,
        tracked_dirty=False, current_pin=CANONICAL_PIN, study="a2",
        policy_selection=None, nodefile_hosts=None, omit_nodefile=False,
        pbs_jobid="0:945411.nqsv"):
    workload = "rr95" if study == "a6" else "rr5"
    attempt_root = tmp_path / "attempt"
    job_root = attempt_root / "jobs" / workload
    for child in (
            job_root, job_root / "campaigns", job_root / "cache",
            job_root / "scheduler"):
        child.mkdir(parents=True, exist_ok=True)
    ccbench = tmp_path / "ccbench"
    dependency = tmp_path / "dependency"
    third_party = tmp_path / "third-party"
    ccbench.mkdir()
    dependency.mkdir()
    third_party.mkdir()
    for name in ("masstree", "mimalloc", "googletest"):
        (third_party / name).mkdir()
    nodefile = tmp_path / "nodefile"
    if nodefile_hosts is None:
        nodefile_hosts = (
            "bnode001", "bnode002", "bnode003", "bnode004", "bnode005"
        )
    if not omit_nodefile:
        nodefile.write_text("".join(host + "\n" for host in nodefile_hosts),
                            encoding="ascii")
    binary_dir = tmp_path / "compute-bin"
    binary_dir.mkdir()
    if ccbench_head is None:
        ccbench_head = CANONICAL_PIN + "1" * (40 - len(CANONICAL_PIN))
    if resolved_pin is None:
        resolved_pin = ccbench_head

    _write_executable(binary_dir / "hostname", r"""#!/bin/bash
printf '%s\n' bnode001
""")
    _write_executable(binary_dir / "qstat", r"""#!/bin/bash
[[ ${1:-} == -f ]] || exit 91
printf '%s\n' \
  'Request ID: 945411.nqsv' \
  "(Per-Req) Elapse Time Limit = Max: ${A2_TEST_REQUESTED_S}S" \
  'Started Request Time = 1700000000'
""")
    _write_executable(binary_dir / "git", fr"""#!/bin/bash
if [[ ${{1:-}} == rev-parse && ${{2:-}} == HEAD ]]; then
  printf '%s\n' {'2' * 40}
  exit 0
fi
if [[ ${{1:-}} == -C && ${{3:-}} == rev-parse && ${{4:-}} == --verify \
    && ${{5:-}} == 'HEAD^{{commit}}' ]]; then
  printf '%s\n' "$A2_TEST_CCBENCH_HEAD"
  exit 0
fi
if [[ ${{1:-}} == -C && ${{3:-}} == rev-parse && ${{4:-}} == --verify \
    && ${{5:-}} == '{CANONICAL_PIN}^{{commit}}' ]]; then
  if [[ "$A2_TEST_RESOLVER_RC" -ne 0 ]]; then
    exit "$A2_TEST_RESOLVER_RC"
  fi
  printf '%s\n' "$A2_TEST_RESOLVED_PIN"
  exit 0
fi
if [[ $* == *status* ]]; then
  if [[ ${{1:-}} == -C && "$A2_TEST_TRACKED_DIRTY" == 1 ]]; then
    printf '%s\n' ' M tracked.cc'
  fi
  exit 0
fi
exit 97
""")
    _write_executable(binary_dir / "python3.10", (
        "#!/bin/bash\n"
        f"exec {shlex.quote(sys.executable)} \"$@\"\n"
    ))
    _write_executable(binary_dir / "mkdir", r"""#!/bin/bash
printf 'mkdir' >>"$A2_TEST_COMPUTE_STAGE_LOG"
printf ' <%s>' "$@" >>"$A2_TEST_COMPUTE_STAGE_LOG"
printf '\n' >>"$A2_TEST_COMPUTE_STAGE_LOG"
exit 0
""")
    _write_executable(binary_dir / "cp", r"""#!/bin/bash
printf 'cp' >>"$A2_TEST_COMPUTE_STAGE_LOG"
printf ' <%s>' "$@" >>"$A2_TEST_COMPUTE_STAGE_LOG"
printf '\n' >>"$A2_TEST_COMPUTE_STAGE_LOG"
exit 0
""")
    environment = dict(os.environ)
    environment.update({
        "PATH": str(binary_dir) + os.pathsep + environment["PATH"],
        "PYTHONDONTWRITEBYTECODE": "1",
        "PBS_JOBID": pbs_jobid,
        "PBS_NODEFILE": str(nodefile),
        "PBS_O_WORKDIR": str(REPO),
        "IZANAGI_A2_REPO_ROOT": str(REPO),
        "IZANAGI_A2_EXPECTED_HEAD": "2" * 40,
        "IZANAGI_A2_CURRENT_PIN": current_pin,
        "IZANAGI_A2_CCBENCH_ROOT": str(ccbench),
        "IZANAGI_A2_ATTEMPT_ROOT": str(attempt_root),
        "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE": str(dependency),
        "IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT": str(third_party),
        "IZANAGI_A2_WORKLOAD": workload,
        "A2_TEST_COMPUTE_STAGE_LOG": str(tmp_path / "compute-stage.log"),
        "A2_TEST_REQUESTED_S": "43200" if study == "a6" else "21600",
        "A2_TEST_CCBENCH_HEAD": ccbench_head,
        "A2_TEST_RESOLVED_PIN": resolved_pin,
        "A2_TEST_RESOLVER_RC": str(resolver_rc),
        "A2_TEST_TRACKED_DIRTY": "1" if tracked_dirty else "0",
    })
    if study == "a6":
        environment["IZANAGI_A2_POLICY_PATH"] = str(A2.A6_POLICY_PATH)
    if policy_selection is not None:
        environment["IZANAGI_A2_POLICY_PATH"] = policy_selection
    completed = subprocess.run(
        [str(JOB)], cwd=REPO, env=environment,
        capture_output=True, text=True, check=False,
    )
    return completed, job_root


@pytest.mark.parametrize(
    "pbs_jobid", ("1:945411.nqsv", "4:945411.nqsv"),
    ids=("rank-1", "observed-rank-4"),
)
def test_job_body_nonzero_job_number_exits_without_durable_output(
        tmp_path, pbs_jobid):
    completed, job_root = _run_compute_pin_harness(
        tmp_path, study="a6", pbs_jobid=pbs_jobid)

    assert completed.returncode == 0
    assert completed.stderr == (
        "nonzero PBS job number exits without running compute body\n")
    assert {
        path.relative_to(job_root).as_posix()
        for path in job_root.rglob("*")
    } == {"cache", "campaigns", "scheduler"}


@pytest.mark.parametrize(
    "pbs_jobid", ("945411.nqsv", "rank:945411.nqsv", "0:",
                  "00:945411.nqsv"),
    ids=("missing-job-number", "nondecimal-job-number", "empty-request-id",
         "leading-zero-job-number"),
)
def test_job_body_rejects_malformed_pbs_jobid_without_durable_output(
        tmp_path, pbs_jobid):
    completed, job_root = _run_compute_pin_harness(
        tmp_path, study="a6", pbs_jobid=pbs_jobid)

    assert completed.returncode == 2
    assert completed.stderr == "PBS_JOBID is not a numbered request ID\n"
    assert not (job_root / "compute-result.json").exists()
    assert not (job_root / "scheduler" / "allocation-qstat.stdout").exists()
    assert not (job_root / "raw").exists()


@pytest.mark.parametrize("mutation", ("wrong-prefix", "resolver-failure", "dirty"))
def test_submitter_production_path_rejects_noncanonical_ccbench_source(
        tmp_path, mutation):
    kwargs = {}
    if mutation == "wrong-prefix":
        wrong = ("0" if CANONICAL_PIN[0] != "0" else "1") * 40
        kwargs.update(ccbench_head=wrong, resolved_pin=wrong)
    elif mutation == "resolver-failure":
        kwargs["resolver_rc"] = 41
    else:
        kwargs["tracked_dirty"] = True
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, **kwargs)
    assert completed.returncode == 2
    assert " preregister " not in " " + driver_log
    assert not attempt_root.exists()


@pytest.mark.parametrize(
    "mutation",
    ("comma", "equals", "newline", "symlink-root", "symlink-child", "missing-child"),
)
def test_submitter_rejects_unsafe_or_nonphysical_third_party_source_root(
        tmp_path, mutation):
    kwargs = {}
    if mutation == "comma":
        kwargs["third_party_argument"] = str(tmp_path / "third-party") + ",bad"
    elif mutation == "equals":
        kwargs["third_party_argument"] = str(tmp_path / "third-party") + "=bad"
    elif mutation == "newline":
        kwargs["third_party_argument"] = str(tmp_path / "third-party") + "\nbad"
    else:
        kwargs["third_party_mutation"] = mutation

    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, **kwargs)
    assert completed.returncode == 2
    assert " preregister " not in " " + driver_log
    assert not attempt_root.exists()


def test_submitter_rejects_unsafe_path_after_canonicalization(tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, third_party_mutation="canonical-comma")

    assert completed.returncode == 2
    assert (
        "qsub environment path is not a safe absolute value" in completed.stderr
    )
    assert " preregister " not in " " + driver_log
    assert not attempt_root.exists()


@pytest.mark.parametrize(
    "mutation", ("wrong-prefix", "resolver-failure", "dirty", "ambient-pin"),
)
def test_compute_job_production_path_rejects_noncanonical_ccbench_source(
        tmp_path, mutation):
    kwargs = {}
    if mutation == "wrong-prefix":
        wrong = ("0" if CANONICAL_PIN[0] != "0" else "1") * 40
        kwargs.update(ccbench_head=wrong, resolved_pin=wrong)
    elif mutation == "resolver-failure":
        kwargs["resolver_rc"] = 42
    elif mutation == "ambient-pin":
        kwargs["current_pin"] = (
            ("0" if CANONICAL_PIN[0] != "0" else "1") + CANONICAL_PIN[1:]
        )
    else:
        kwargs["tracked_dirty"] = True
    completed, job_root = _run_compute_pin_harness(tmp_path, **kwargs)
    assert completed.returncode == 2
    result = json.loads((job_root / "compute-result.json").read_text())
    assert result["driver_rc"] == 2
    assert not (job_root / "raw").exists()


def test_a6_compute_job_accepts_rr95_membership_before_source_gate(tmp_path):
    completed, job_root = _run_compute_pin_harness(
        tmp_path, study="a6", tracked_dirty=True)

    assert completed.returncode == 2
    result = json.loads((job_root / "compute-result.json").read_text())
    assert result["workload"] == "rr95"
    assert result["driver_rc"] == 2
    assert not (job_root / "raw").exists()


@pytest.mark.parametrize(
    "nodefile_hosts",
    (
        ("bnode001", "bnode002", "bnode003", "bnode004"),
        ("bnode001", "bnode002", "bnode003", "bnode004", "bnode005",
         "bnode006"),
        ("bnode001", "bnode002", "bnode002", "bnode003", "bnode004"),
    ),
    ids=("too-few", "too-many", "duplicate-sibling"),
)
@pytest.mark.parametrize("study", ("a2", "a6"))
def test_m9_job_body_rejects_nodefile_sibling_count_mismatch(
        tmp_path, nodefile_hosts, study):
    completed, job_root = _run_compute_pin_harness(
        tmp_path, study=study, tracked_dirty=True,
        nodefile_hosts=nodefile_hosts)

    assert completed.returncode == 2
    assert "PBS node allocation differs from scheduler policy" in completed.stderr
    assert "CCBench source tree is not clean" not in completed.stderr
    assert json.loads((job_root / "compute-result.json").read_text())[
        "driver_rc"] == 2


def test_job_body_rejects_missing_nodefile(tmp_path):
    completed, job_root = _run_compute_pin_harness(
        tmp_path, study="a6", tracked_dirty=True, omit_nodefile=True)

    assert completed.returncode == 2
    assert "PBS node allocation is unavailable" in completed.stderr
    assert json.loads((job_root / "compute-result.json").read_text())[
        "driver_rc"] == 2


@pytest.mark.parametrize("study", ("a2", "a6"))
def test_job_body_accepts_exact_policy_nodefile_before_source_gate(
        tmp_path, study):
    completed, _job_root = _run_compute_pin_harness(
        tmp_path, study=study, tracked_dirty=True)

    assert completed.returncode == 2
    assert "PBS node allocation" not in completed.stderr
    assert "CCBench source tree is not clean" in completed.stderr


def test_job_body_stages_exact_three_src_suffixed_dependencies(tmp_path):
    completed, _job_root = _run_compute_pin_harness(tmp_path)
    assert completed.returncode != 0
    scratch = Path(
        f"/scr/{os.environ['USER']}/paper-story-a2-certification/"
        "0_945411.nqsv"
    )
    dependency = tmp_path / "dependency"
    third_party = tmp_path / "third-party"
    assert (tmp_path / "compute-stage.log").read_text(
        encoding="utf-8"
    ).splitlines() == [
        f"mkdir <-p> <{scratch.parent}>",
        f"mkdir <{scratch}>",
        f"mkdir <{scratch / 'dependencies'}>",
        f"mkdir <{scratch / 'fetchcontent'}>",
        f"cp <-a> <{dependency}/.> <{scratch / 'dependencies'}/>",
        f"cp <-a> <{third_party / 'masstree'}> "
        f"<{scratch / 'fetchcontent/masstree-src'}>",
        f"cp <-a> <{third_party / 'mimalloc'}> "
        f"<{scratch / 'fetchcontent/mimalloc-src'}>",
        f"cp <-a> <{third_party / 'googletest'}> "
        f"<{scratch / 'fetchcontent/googletest-src'}>",
    ]


def test_compute_job_trap_records_policy_resolution_failure(tmp_path):
    completed, job_root = _run_compute_pin_harness(
        tmp_path, study="a6",
        policy_selection=str(tmp_path / "not-a-canonical-policy.json"))

    assert completed.returncode == 2
    result = json.loads((job_root / "compute-result.json").read_text())
    assert result["workload"] == "rr95"
    assert result["driver_rc"] == 2
    assert not (job_root / "raw").exists()


def test_prereg_m1_submitter_fails_closed_when_inventory_qstat_fails(tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, inventory_rc=19)
    assert completed.returncode == 2
    assert "cannot inventory existing certification" in completed.stderr
    assert " preregister " not in " " + driver_log
    assert not attempt_root.exists()


def test_submitter_fails_closed_when_inventory_qstat_writes_stderr(tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, inventory_stderr="partial inventory warning\n")
    assert completed.returncode == 2
    assert "cannot inventory existing certification" in completed.stderr
    assert " preregister " not in " " + driver_log
    assert not attempt_root.exists()


def test_submitter_requires_selected_queue_line_to_be_enabled_and_active(tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, queue_state="gen_S DIS INA\ngen_L ENA ACT\n")

    assert completed.returncode == 2
    assert "gen_S is not ENA/ACT" in completed.stderr
    assert " preregister " not in " " + driver_log
    assert not attempt_root.exists()


def test_prereg_pc1_submitter_continues_after_empty_request_inventory(tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, inventory_rc=0, stop_at_preregister=True)
    assert completed.returncode == 37
    assert "preregister --attempt-id submitter-harness" in driver_log
    assert "cannot inventory existing certification" not in completed.stderr
    assert not attempt_root.exists()


def test_submitter_rejects_an_existing_a2_request_before_preregistration(
        tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, inventory_names=("paper-a2-cert",))
    assert completed.returncode == 2
    assert "already visible" in completed.stderr
    assert " preregister " not in " " + driver_log
    assert not attempt_root.exists()


@pytest.mark.parametrize(
    "study,inventory_names,expected_rc",
    (
        pytest.param("a2", ("paper-a2-cert",), 2, id="a2-same-study"),
        pytest.param("a2", ("paper-a6-cert",), 37, id="a2-other-study"),
        pytest.param(
            "a6", ("paper-a2-cert", "izdw-b51"), 37,
            id="p4-a6-other-study-and-unrelated",
        ),
        pytest.param(
            "a6", ("paper-a6-cert-x",), 37,
            id="p5-a6-prefix-collision",
        ),
        pytest.param(
            "a6", ("paper-a6-cert",), 2,
            id="p6-a6-same-study",
        ),
    ),
)
def test_m6_submitter_duplicate_detection_is_study_scoped(
        tmp_path, study, inventory_names, expected_rc):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, study=study, inventory_names=inventory_names,
        stop_at_preregister=True,
    )

    assert completed.returncode == expected_rc
    if expected_rc == 2:
        assert "same-study certification request" in completed.stderr
        assert " preregister " not in " " + driver_log
        assert not attempt_root.exists()
    else:
        assert "preregister" in driver_log


def test_prereg_m2_m3_request_is_durable_before_visibility_failure(tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, inventory_rc=0, visibility_rc=23)
    scheduler = attempt_root / "jobs" / "rr5" / "scheduler"
    sidecar = scheduler / "request-id"
    assert completed.returncode == 23
    assert (scheduler / "qsub.stdout").read_bytes() == (
        b"Request 945411.nqsv submitted\n")
    assert (scheduler / "qsub.stderr").read_bytes() == b""
    assert sidecar.is_file() and not sidecar.is_symlink()
    assert sidecar.read_bytes() == b"945411.nqsv\n"
    assert "exact-qsub -- qsub" in driver_log
    assert driver_log.index("durabilize-qsub-diagnostics") < driver_log.index(
        "record-request-id")
    assert not (
        attempt_root / "jobs" / "rr50" / "scheduler" / "request-id"
    ).exists()
    assert not (attempt_root / "receipts" / "submission.json").exists()


def test_submitter_retains_both_sidecars_on_rr50_visibility_failure(tmp_path):
    completed, attempt_root, _ = _run_submitter_harness(
        tmp_path, visibility_fail_workload="rr50", visibility_rc=31)
    assert completed.returncode == 31
    for workload, request_id in (
            ("rr5", "945411.nqsv"), ("rr50", "945412.nqsv")):
        scheduler = attempt_root / "jobs" / workload / "scheduler"
        assert (scheduler / "qsub.stdout").read_bytes() == (
            f"Request {request_id} submitted\n".encode("ascii"))
        assert (scheduler / "qsub.stderr").read_bytes() == b""
        assert (scheduler / "request-id").read_bytes() == (
            f"{request_id}\n".encode("ascii"))
    assert not (attempt_root / "receipts" / "submission.json").exists()
    assert (tmp_path / "event.log").read_text(encoding="utf-8").splitlines() == [
        "inventory", "qsub:rr5", "visibility:rr5", "qsub:rr50",
        "visibility:rr50",
    ]


@pytest.mark.parametrize("workload", ("rr5", "rr50"))
def test_submitter_durably_records_each_qsub_failure_before_stopping(
        tmp_path, workload):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, visibility_fail_workload="", qsub_fail_workload=workload,
        qsub_rc=29, qsub_stderr_text="scheduler rejected request\n")
    scheduler = attempt_root / "jobs" / workload / "scheduler"
    assert completed.returncode == 29
    assert (scheduler / "qsub.stdout").is_file()
    assert (scheduler / "qsub.stderr").read_bytes() == (
        b"scheduler rejected request\n")
    assert not (scheduler / "request-id").exists()
    assert driver_log.rindex("durabilize-qsub-diagnostics") < len(driver_log)
    if workload == "rr50":
        assert (attempt_root / "jobs" / "rr5" / "scheduler"
                / "request-id").read_bytes() == b"945411.nqsv\n"
    assert not (attempt_root / "receipts" / "submission.json").exists()


def test_submitter_rejects_clean_rc_with_qsub_stderr_after_durability(tmp_path):
    completed, attempt_root, _ = _run_submitter_harness(
        tmp_path, visibility_fail_workload="", qsub_stderr_workload="rr5",
        qsub_stderr_text="qsub warning\n")
    scheduler = attempt_root / "jobs" / "rr5" / "scheduler"
    assert completed.returncode == 2
    assert (scheduler / "qsub.stdout").read_bytes() == (
        b"Request 945411.nqsv submitted\n")
    assert (scheduler / "qsub.stderr").read_bytes() == b"qsub warning\n"
    assert not (scheduler / "request-id").exists()
    assert not (attempt_root / "receipts" / "submission.json").exists()


def test_submitter_qsub_diagnostics_are_create_only(tmp_path):
    completed, attempt_root, _ = _run_submitter_harness(
        tmp_path, visibility_fail_workload="",
        precreate_diagnostic="qsub.stdout")
    diagnostic = (
        attempt_root / "jobs" / "rr5" / "scheduler" / "qsub.stdout")
    assert completed.returncode == 2
    assert "qsub diagnostics already exist for rr5" in completed.stderr
    assert diagnostic.read_bytes() == b"sentinel\n"
    assert not (tmp_path / "qsub-log" / "rr5.argv").exists()


def test_submitter_success_uses_production_cli_qsub_and_exact_stdout_contract(
        tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, visibility_fail_workload="")
    receipt_path = attempt_root / "receipts" / "submission.json"
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert completed.stdout.splitlines() == [
        str(receipt_path), "945411.nqsv", "945412.nqsv"]
    assert receipt_path.is_file()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["current_pin"] == CANONICAL_PIN
    assert len(receipt["current_pin"]) < 40
    assert (tmp_path / "event.log").read_text(encoding="utf-8").splitlines() == [
        "inventory", "qsub:rr5", "visibility:rr5", "qsub:rr50",
        "visibility:rr50",
    ]
    cli_commands = []
    module = "orchestrator.campaign.paper_story_a2_certification "
    for line in driver_log.splitlines():
        if module in line:
            cli_commands.append(line.split(module, 1)[1].split()[0])
    assert cli_commands == [
        "preregister",
        "exact-qsub", "durabilize-qsub-diagnostics", "record-request-id",
        "exact-qsub", "durabilize-qsub-diagnostics", "record-request-id",
        "record-submission",
    ]
    for workload, request_id in (
            ("rr5", "945411.nqsv"), ("rr50", "945412.nqsv")):
        scheduler = attempt_root / "jobs" / workload / "scheduler"
        assert (scheduler / "qsub.stdout").read_bytes() == (
            f"Request {request_id} submitted\n".encode("ascii"))
        assert (scheduler / "qsub.stderr").read_bytes() == b""
        assert (scheduler / "request-id").read_bytes() == (
            f"{request_id}\n".encode("ascii"))
        argv = (tmp_path / "qsub-log" / f"{workload}.argv").read_bytes()
        argv = [part.decode("utf-8") for part in argv.split(b"\0") if part]
        variable_arg = (
            f"IZANAGI_A2_ATTEMPT_ROOT={attempt_root},"
            f"IZANAGI_A2_WORKLOAD={workload},"
            f"IZANAGI_A2_EXPECTED_HEAD={'2' * 40},"
            f"IZANAGI_A2_CURRENT_PIN={CANONICAL_PIN},"
            f"IZANAGI_A2_CCBENCH_ROOT={tmp_path / 'ccbench'},"
            f"IZANAGI_A2_REPO_ROOT={REPO},"
            f"IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE={tmp_path / 'dependency'},"
            f"IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT={tmp_path / 'third-party'}")
        assert argv == [
            "-A", "SFC", "-q", "gen_S", "-b", "5", "-l",
            "elapstim_req=06:00:00", "-N", "paper-a2-cert", "-v",
            variable_arg, "-o", str(scheduler / "job.stdout"), "-e",
            str(scheduler / "job.stderr"), str(
                REPO / "tools/pegasus/paper_story_a2_certification.sh"),
        ]
    receipt_text = receipt_path.read_text(encoding="utf-8")
    assert str(attempt_root / "jobs" / "rr5" / "scheduler" / "qsub.stdout") \
        not in receipt_text


def test_p3_a6_submitter_uses_one_rr95_job_and_policy_scheduler(tmp_path):
    completed, attempt_root, driver_log = _run_submitter_harness(
        tmp_path, study="a6", visibility_fail_workload="",
        exercise_finish_group=True)
    receipt_path = attempt_root / "receipts" / "submission.json"

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines() == [str(receipt_path), "945413.nqsv"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["study"] == "paper-story-a6-certification"
    assert [job["workload"] for job in receipt["jobs"]] == ["rr95"]
    environment = receipt["jobs"][0]["qsub_environment"]
    assert environment["IZANAGI_A2_POLICY_PATH"] == str(A2.A6_POLICY_PATH)
    assert set(environment) == A2._QSUB_ENV_KEYS | {"IZANAGI_A2_POLICY_PATH"}
    argv = receipt["jobs"][0]["qsub_argv"]
    assert argv[5:7] == ["-b", "5"]
    assert argv[7:11] == [
        "-l", "elapstim_req=12:00:00", "-N", "paper-a6-cert"]
    assert (tmp_path / "event.log").read_text(encoding="utf-8").splitlines() == [
        "inventory", "qsub:rr95", "visibility:rr95",
        "visibility:rr95",  # finish-group terminal-state inspection
    ]
    driver_invocations = []
    module = "orchestrator.campaign.paper_story_a2_certification"
    for line in driver_log.splitlines():
        tokens = shlex.split(line)
        if module not in tokens:
            continue
        command_args = tokens[tokens.index(module) + 1:]
        assert command_args[:2] == ["--policy", str(A2.A6_POLICY_PATH)]
        driver_invocations.append(command_args[2])
    assert driver_invocations == [
        "preregister", "exact-qsub", "durabilize-qsub-diagnostics",
        "record-request-id", "record-submission", "finish-group",
    ]
    assert receipt["jobs"][0]["qstat_visibility"]["stdout"] == (
        REPO / "orchestrator/tests/fixtures/paper_story_a2"
        / "qstat-visibility-fanout-945413.stdout"
    ).read_text(encoding="utf-8")
    assert "rr50" not in json.dumps(receipt)


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
