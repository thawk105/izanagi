import ast
import json
import re
import shlex
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
JOB = REPO / "tools/pegasus/a5_second_boot_backoff_sweep.sh"
SUBMITTER = REPO / "tools/pegasus/submit_a5_second_boot_backoff_sweep.sh"
REGISTRY = REPO / "tools/pegasus/admission_registry.json"
EXPECTED_WORKLOADS = ("write-heavy", "balanced")


def _shell_array(source: str, name: str) -> tuple[str, ...]:
    match = re.search(rf"(?m)^{re.escape(name)}=\(([^\n()]*)\)$", source)
    if match is None:
        raise AssertionError(f"missing literal shell array: {name}")
    return tuple(shlex.split(match.group(1)))


def _job_workload_case(source: str) -> tuple[str, ...]:
    match = re.search(
        r'case "\$WORKLOAD" in\n(?P<body>.*?)\n(?:\s*)esac',
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("missing literal WORKLOAD case gate")
    accepted = []
    for line in match.group("body").splitlines():
        candidate = line.strip()
        if candidate.startswith("*") or not candidate.endswith(") ;;"):
            continue
        accepted.extend(candidate[:-4].split("|"))
    return tuple(accepted)


def _python_literal(source: str, name: str):
    match = re.search(rf"(?m)^{re.escape(name)} = (.+)$", source)
    if match is None:
        raise AssertionError(f"missing finalizer literal: {name}")
    return ast.literal_eval(match.group(1))


def _integer_assignment(source: str, name: str) -> int:
    match = re.search(rf"(?m)^{re.escape(name)}=([0-9]+)$", source)
    if match is None:
        raise AssertionError(f"missing integer shell assignment: {name}")
    return int(match.group(1))


def _pbs_walltime_seconds(source: str) -> int:
    match = re.search(
        r"(?m)^#PBS -l elapstim_req=([0-9]{2}):([0-9]{2}):([0-9]{2})$",
        source,
    )
    if match is None:
        raise AssertionError("missing canonical PBS elapstim_req")
    hours, minutes, seconds = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _assert_submitter_workloads(source: str) -> None:
    assert _shell_array(source, "WORKLOADS") == EXPECTED_WORKLOADS


def _assert_job_workloads(source: str) -> None:
    assert _job_workload_case(source) == EXPECTED_WORKLOADS


def _assert_no_backoff_denominator(source: str) -> None:
    assert _python_literal(source, "BASELINE_FLAGS") == {
        "BACK_OFF": 0,
        "BACKOFF_FIXED": -1,
    }
    assert (
        'baseline = selected_by_flags(BASELINE_FLAGS)'
        in source
    )
    assert (
        'target = selected_by_flags({"BACK_OFF": 1, "BACKOFF_FIXED": target_fixed_us})'
        in source
    )


def _assert_complete_committed_sweep(source: str) -> None:
    required = {
        "eight-genome-literal": "EXPECTED_GENOME_COUNT = 8",
        "expected-genomes": (
            "expected_genomes = {genome.canonical() for genome in "
            "expected_genome_objects}"
        ),
        "all-genomes": "if committed_genomes != expected_genomes:",
        "abort-count": 'abort_count = sum(record.stage == "abort" for record in records)',
        "abort-zero": "or abort_count != 0",
        "all-committed": (
            "or any(not state.committed or state.aborted for state in "
            "states.values())"
        ),
        "five-tps": "EXPECTED_TPS_COUNT = 5",
        "wal-replay": "states = wal.replay(layout, admission_policy=policy)",
    }
    missing = [label for label, fragment in required.items() if fragment not in source]
    if missing:
        raise AssertionError("incomplete A-5 finalizer contract: " + ",".join(missing))


def _assert_walltime_budget(source: str) -> None:
    assert "#PBS -A SFC" in source
    assert "#PBS -q gen_S" in source
    assert "#PBS -b 1" in source
    walltime = _pbs_walltime_seconds(source)
    cap_names = (
        "QSTAT_CAP_S",
        "WORKTREE_SETUP_CAP_S",
        "DEPENDENCY_BUILD_CAP_S",
        "SWEEP_CAP_S",
        "WORKTREE_CLEANUP_CAP_S",
        "FINALIZE_CAP_S",
    )
    caps = {name: _integer_assignment(source, name) for name in cap_names}
    margin = _integer_assignment(source, "FINAL_MARGIN_S")
    assert caps["SWEEP_CAP_S"] == 5400
    assert sum(caps.values()) + margin < walltime
    assert _integer_assignment(source, "EXPECTED_WALLTIME_S") == walltime
    assert (
        '[[ $((INNER_CAP_TOTAL_S + FINAL_MARGIN_S)) -lt "$EXPECTED_WALLTIME_S" ]]'
        in source
    )


def _assert_execution_shape(job: str, submitter: str) -> None:
    normalized_job = re.sub(r"\\\n\s*", " ", job)
    normalized_submitter = re.sub(r"\\\n\s*", " ", submitter)
    normalized_job = re.sub(r"[ \t]+", " ", normalized_job)
    normalized_submitter = re.sub(r"[ \t]+", " ", normalized_submitter)
    driver = (
        'timeout "$SWEEP_CAP_S" "$PY" -I -B '
        '"$JOB_REPO/orchestrator/campaign/backoff_sweep.py" "$WORKLOAD"'
    )
    assert normalized_job.count(driver) == 1
    assert "read-heavy" not in job
    assert "read-heavy" not in submitter
    assert "--screening" not in job
    assert "--screening-fixed-us" not in job
    assert "--confirm-each-candidate" not in job
    assert (
        "export IZANAGI_PEGASUS_THIRDPARTY_CACHE="
        "/work/1/SFC/tanab/izanagi-thirdparty-cache"
    ) in job
    assert 'JOB_REPO="$TMPDIR/job-repo"' in job
    assert 'JOB_CCBENCH="$JOB_REPO/external/ccbench"' in job
    assert 'mkdir -m 0700 "$OUTPUT_ROOT/env/pegasus" "$OUTPUT_ROOT/env/pegasus/claims"' in job
    assert 'destination = base / "result.json"' in job
    assert 'os.O_WRONLY | os.O_CREAT | os.O_EXCL' in job
    assert 'A5_EXPECTED_HEAD=$EXPECTED_HEAD' in submitter
    assert '-o "$stdout" -e "$stderr" "$JOB_SCRIPT"' in normalized_submitter
    for fragment in (
        '"hostname": hostname',
        '"fqdn": fqdn',
        '"boot_id": boot_id',
        '"boot_epoch": int(boot_epoch)',
        '"pbs_jobid": pbs_jobid',
        '"repository_commit": repository_commit',
        '"ccbench_commit": ccbench_commit',
        '"toolchain": toolchains[0]',
        '"perf_preflight": preflights[0]',
        '"wal_sha256": hashlib.sha256(wal_after).hexdigest()',
        '"lock_sha256": hashlib.sha256(lock_after).hexdigest()',
        'improvement_percent = (target["median"] / baseline["median"] - 1) * 100',
    ):
        assert fragment in job


def _assert_current_pair_contract() -> None:
    job = JOB.read_text(encoding="utf-8")
    submitter = SUBMITTER.read_text(encoding="utf-8")
    _assert_submitter_workloads(submitter)
    _assert_job_workloads(job)
    _assert_no_backoff_denominator(job)
    _assert_complete_committed_sweep(job)
    _assert_walltime_budget(job)
    _assert_execution_shape(job, submitter)


def test_submitter_workload_set_is_exactly_the_two_adopted_values():
    _assert_submitter_workloads(SUBMITTER.read_text(encoding="utf-8"))


def test_job_body_accepts_exactly_the_two_adopted_workloads():
    _assert_job_workloads(JOB.read_text(encoding="utf-8"))


def test_finalizer_denominator_is_exactly_no_backoff():
    _assert_no_backoff_denominator(JOB.read_text(encoding="utf-8"))


def test_finalizer_requires_all_eight_commits_and_zero_aborts():
    _assert_complete_committed_sweep(JOB.read_text(encoding="utf-8"))


def test_inner_caps_and_final_margin_fit_strictly_inside_pbs_walltime():
    _assert_walltime_budget(JOB.read_text(encoding="utf-8"))


def test_job_body_is_registered_only_as_dispatch_required():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    assert registry["tools/pegasus/a5_second_boot_backoff_sweep.sh"] == {
        "class": "dispatch-required",
        "reason": "PBS A-5 second-boot backoff sweep measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }
    assert registry["tools/pegasus/submit_a5_second_boot_backoff_sweep.sh"] == {
        "class": "local-ok",
        "reason": "login-side PBS A-5 two-workload fan-out submitter",
        "primary_gate": (
            "qsub submission; compute work stays in independent job bodies"
        ),
        "evidence": "static login-side submitter classification",
    }


def test_current_scripts_are_a_positive_example_of_the_complete_contract():
    _assert_current_pair_contract()
