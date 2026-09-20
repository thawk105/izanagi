from __future__ import annotations

import ast
import errno
import hashlib
import json
import os
import re
import shlex
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import ident, site_policy
from orchestrator.campaign import paper_story_a1_paired as paired
from orchestrator.campaign.build_admission import GeneratorId, build_run_context


REPO_ROOT = Path(__file__).resolve().parents[2]
JOB = REPO_ROOT / "tools/pegasus/paper_story_a1_paired.sh"
REGISTRY = REPO_ROOT / "tools/pegasus/admission_registry.json"
A1_QSTAT_FIXTURES = REPO_ROOT / "orchestrator/tests/fixtures/paper_story_a1"
EXPECTED_NQSV_QSTAT_STATES = (
    "ARR",
    "WAI",
    "QUE",
    "PRR",
    "RUN",
    "POR",
    "EXT",
    "HLD",
    "HOL",
    "SUS",
    "MIG",
    "STG",
)
EXPECTED_RESERVATION_EXPORTS = {
    "IZANAGI_RESERVATION_JOB_ID": "$PBS_JOBID",
    "IZANAGI_RESERVATION_REQUESTED_S": "$REQUESTED_S",
    "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": "$SCHEDULER_STARTED_EPOCH",
    "IZANAGI_RESERVATION_DEADLINE_EPOCH": "$DEADLINE_EPOCH",
    "IZANAGI_RESERVATION_HOST": "$RESERVATION_HOST",
    "IZANAGI_RESERVATION_BOOT_ID": "$BOOT_ID",
    "IZANAGI_RESERVATION_SCRIPT_SHA256": "$CURRENT_SCRIPT_SHA",
    "IZANAGI_RESERVATION_NONCE": "$IZANAGI_SUBMISSION_NONCE",
}
EXPECTED_NON_CERTIFYING_SOURCE_RELATIVE_PATHS = frozenset({
    "orchestrator/campaign/paper_story_a1_paired.py",
    "orchestrator/campaign/paper_story_a1_paired.v2.json",
    "orchestrator/campaign/pipeline.py",
    "tools/pegasus/paper_story_a1_paired.sh",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/trial_registry.py",
})
EXPECTED_V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS = (
    EXPECTED_NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    | {"orchestrator/calibrator/runner.py"}
)


def _gate_args(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    attempt = tmp_path / "attempt"
    return {
        "repo_root": repo,
        "expected_head": "a" * 40,
        "output_root": attempt / "raw" / "campaign-output",
        "cache_root": attempt / "cache",
        "result_root": attempt / "raw" / "results",
        "pbs_jobid": "12345.nqsv",
        "site": site_policy.PEGASUS_COMPUTE,
        "observed_head": "a" * 40,
        "porcelain": "",
        "attempt_root": attempt,
    }


def test_clean_h0_compute_fresh_roots_positive_contract(tmp_path: Path) -> None:
    args = _gate_args(tmp_path)
    roots = paired.validate_measure_environment(**args)
    assert roots == {
        "output_root": os.fspath((tmp_path / "attempt/raw/campaign-output").resolve()),
        "cache_root": os.fspath((tmp_path / "attempt/cache").resolve()),
        "result_root": os.fspath((tmp_path / "attempt/raw/results").resolve()),
    }
    assert not any(Path(path).exists() for path in roots.values())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("site", site_policy.PEGASUS_LOGIN, "Pegasus compute"),
        ("site", site_policy.PEGASUS_SUSPECT, "Pegasus compute"),
        ("observed_head", "b" * 40, "HEAD differs"),
        ("porcelain", " M tracked.py", "dirty"),
        ("pbs_jobid", "bad job id", "PBS_JOBID"),
    ],
    ids=["M12-login", "M12-suspect", "M12-head-mismatch", "M12-dirty", "bad-pbs"],
)
def test_measure_environment_rejects_site_head_dirty_and_pbs(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    args = _gate_args(tmp_path)
    args[field] = value
    with pytest.raises(paired.PaperStoryError, match=message):
        paired.validate_measure_environment(**args)


@pytest.mark.parametrize("root_name", ["output_root", "cache_root", "result_root"])
def test_measure_environment_rejects_every_existing_root(
    tmp_path: Path, root_name: str
) -> None:
    args = _gate_args(tmp_path)
    Path(args[root_name]).mkdir(parents=True)
    with pytest.raises(paired.PaperStoryError, match="must not already exist"):
        paired.validate_measure_environment(**args)


def test_measure_environment_rejects_repo_internal_or_aliased_roots(tmp_path: Path) -> None:
    args = _gate_args(tmp_path)
    args["output_root"] = args["repo_root"] / "raw"
    with pytest.raises(paired.PaperStoryError, match="outside the repository"):
        paired.validate_measure_environment(**args)

    args = _gate_args(tmp_path / "nested")
    args["cache_root"] = args["output_root"] / "cache"
    with pytest.raises(paired.PaperStoryError, match="overlap"):
        paired.validate_measure_environment(**args)

    args = _gate_args(tmp_path / "second")
    args["cache_root"] = args["output_root"]
    with pytest.raises(paired.PaperStoryError, match="distinct"):
        paired.validate_measure_environment(**args)


def _policy_for_base(base: Path) -> dict:
    policy = json.loads(json.dumps(paired.load_policy()[0]))
    policy["execution"]["durable_measurement_base"] = os.fspath(base)
    return policy


def _qstat_fixture(name: str) -> str:
    return (A1_QSTAT_FIXTURES / name).read_bytes().decode("utf-8")


def _acquisition(
    attempt_root: Path,
    repo_root: Path,
    *,
    request_id: str = "12345.nqsv",
    qsub_stdout: str | None = None,
    submit_host: str = "pegasus01",
    qstat_state: str = "QUE",
) -> dict:
    job = repo_root / paired.JOB_RELATIVE_PATH
    if not job.exists():
        job.parent.mkdir(parents=True, exist_ok=True)
        job.write_text("# receipt job fixture\n", encoding="utf-8")
    argv, options = paired._canonical_qsub_contract(
        repo_root=repo_root.resolve(),
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        attempt=attempt_root,
    )
    qsub_stdout = qsub_stdout if qsub_stdout is not None else f"{request_id}\n"
    qsub_stderr = ""
    evidence = paired._attempt_evidence_paths(attempt_root)
    return {
        "schema_version": paired.SUBMISSION_SCHEMA,
        "route": "direct-qsub",
        "study_id": paired.STUDY_ID,
        "source_commit": "a" * 40,
        "attempt_root": os.fspath(attempt_root),
        "request_id": request_id,
        "submission_receipt_path": evidence["submission_receipt"],
        "completion_receipt_path": evidence["completion_receipt"],
        "qsub_argv": argv,
        "qsub_options": options,
        "submit_observation": {
            "submit_host": submit_host,
            "qsub_stdout": qsub_stdout,
            "qsub_stdout_sha256": hashlib.sha256(qsub_stdout.encode()).hexdigest(),
            "qsub_stderr": qsub_stderr,
            "qsub_stderr_sha256": hashlib.sha256(qsub_stderr.encode()).hexdigest(),
            "qstat_visibility": {
                "request_id": request_id,
                "visible": True,
                "state": qstat_state,
                "queue": "gen_S",
                "observed_epoch": 1,
            },
        },
    }


def _pbs_observation(
    attempt_root: Path,
    repo_root: Path,
    *,
    host: str = "pegasus01",
    pbs_jobid: str = "12345.nqsv",
) -> dict[str, str]:
    del attempt_root
    return {
        "pbs_jobid": pbs_jobid,
        "pbs_o_host": host,
        "pbs_o_workdir": os.fspath(repo_root.resolve()),
    }


@pytest.mark.parametrize(
    "state",
    EXPECTED_NQSV_QSTAT_STATES,
)
def test_acquisition_receipt_accepts_exact_nqsv_qstat_state_vocabulary(
    tmp_path: Path, state: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo, qstat_state=state)
    roots = paired.validate_acquisition_receipt(
        receipt,
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        pbs_observation=_pbs_observation(attempt, repo),
        policy=_policy_for_base(base),
    )
    assert roots["attempt_root"] == os.fspath(attempt)


def test_nqsv_qstat_state_allowlist_is_exact() -> None:
    assert paired.NQSV_QSTAT_STATES == frozenset(EXPECTED_NQSV_QSTAT_STATES)
    assert paired.NQSV_QSTAT_TERMINAL_STATES == frozenset({"C", "F", "EXT"})


@pytest.mark.parametrize(
    ("fixture_name", "request_id", "expected_state"),
    [
        ("qstat-f-980043.nqsv.txt", "980043.nqsv", "RUN"),
        ("qstat-f-980062.nqsv.txt", "980062.nqsv", "RUN"),
        ("qstat-f-queued-978193.excerpt.txt", "978193.nqsv", "QUE"),
    ],
    ids=["M8-running", "M8-pre-running", "M8-queued"],
)
def test_real_nqsv_visibility_flows_through_acquisition_validator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_name: str,
    request_id: str,
    expected_state: str,
) -> None:
    stdout = _qstat_fixture(fixture_name)
    monkeypatch.setattr(
        paired.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout, "",
        ),
    )
    monkeypatch.setattr(paired.time, "time", lambda: 2)
    visibility = paired._observe_qstat_visibility(request_id)

    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo, request_id=request_id)
    receipt["submit_observation"]["qstat_visibility"] = visibility
    roots = paired.validate_acquisition_receipt(
        receipt,
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id=request_id,
        pbs_observation=_pbs_observation(
            attempt, repo, pbs_jobid=request_id,
        ),
        policy=_policy_for_base(base),
    )

    assert visibility == {
        "request_id": request_id,
        "visible": True,
        "state": expected_state,
        "queue": "gen_S",
        "observed_epoch": 2,
    }
    assert roots["attempt_root"] == os.fspath(attempt)


@pytest.mark.parametrize(
    ("mutation", "returncode", "stderr"),
    [
        ("held", 0, ""),
        ("queue-before-id", 0, ""),
        ("only-queue-before-id", 0, ""),
        ("wrong-queue", 0, ""),
        ("missing-execution-queue-marker", 0, ""),
        ("wrong-server", 0, ""),
        ("missing-queue", 0, ""),
        ("duplicate-queue-after-id", 0, ""),
        ("second-queue-other-server", 0, ""),
        ("second-queue-other-name", 0, ""),
        ("disappeared", 0, ""),
        ("unchanged", 1, ""),
        ("unchanged", 0, "qstat warning\n"),
        ("unknown-state", 0, ""),
    ],
    ids=[
        "M1-held",
        "M2-queue-before-id",
        "queue-position-before-id",
        "M3-wrong-queue",
        "M4-missing-marker",
        "wrong-server",
        "queue-count-zero",
        "queue-count-two-after-id",
        "M11-second-queue-other-server",
        "queue-count-two-other-name",
        "rc0-disappeared-request",
        "nonzero-rc",
        "M7-nonempty-stderr",
        "M9-unknown-state",
    ],
)
def test_visibility_rejects_each_noncanonical_observation(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    returncode: int,
    stderr: str,
) -> None:
    stdout = _qstat_fixture("qstat-f-980043.nqsv.txt")
    queue_line = "    Queue = gen_S@nqsv (Execution Queue)\n"
    if mutation == "held":
        stdout = stdout.replace(
            "    Current State           = Running\n",
            "    Current State           = Held\n",
        )
    elif mutation == "queue-before-id":
        stdout = queue_line + stdout
    elif mutation == "only-queue-before-id":
        stdout = queue_line + stdout.replace(queue_line, "")
    elif mutation == "wrong-queue":
        stdout = stdout.replace(
            queue_line,
            "    Queue = other@nqsv (Execution Queue)\n",
        )
    elif mutation == "missing-execution-queue-marker":
        stdout = stdout.replace(queue_line, "    Queue = gen_S@nqsv\n")
    elif mutation == "wrong-server":
        stdout = stdout.replace(
            queue_line,
            "    Queue = gen_S@other (Execution Queue)\n",
        )
    elif mutation == "missing-queue":
        stdout = stdout.replace(queue_line, "")
    elif mutation == "duplicate-queue-after-id":
        stdout = stdout.replace(queue_line, queue_line + queue_line)
    elif mutation == "second-queue-other-server":
        stdout = stdout.replace(
            queue_line,
            queue_line + "    Queue = other@other (Execution Queue)\n",
        )
    elif mutation == "second-queue-other-name":
        stdout = stdout.replace(
            queue_line,
            queue_line + "    Queue = other@nqsv (Execution Queue)\n",
        )
    elif mutation == "disappeared":
        stdout = _qstat_fixture("qstat-f-absent-900001.stdout")
    elif mutation == "unknown-state":
        stdout = stdout.replace(
            "    Current State           = Running\n",
            "    Current State           = Launching\n",
        )
    elif mutation != "unchanged":
        raise AssertionError(f"unhandled test mutation: {mutation}")

    monkeypatch.setattr(
        paired.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], returncode, stdout, stderr,
        ),
    )
    with pytest.raises(
        paired.PaperStoryError,
        match="qstat did not visibly bind the submitted request",
    ):
        paired._observe_qstat_visibility("980043.nqsv")


def test_non_certifying_source_closure_matches_shell_and_preserves_legacy_set() -> None:
    assert paired.SOURCE_RELATIVE_PATHS == (
        "orchestrator/campaign/paper_story_a1_paired.py",
        "orchestrator/campaign/paper_story_a1_paired.v2.json",
        "orchestrator/campaign/pipeline.py",
        "tools/pegasus/paper_story_a1_paired.sh",
    )
    assert frozenset(paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS) == (
        EXPECTED_NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    )
    assert len(paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS) == 9
    assert frozenset(paired.V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS) == (
        EXPECTED_V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    )
    assert len(paired.V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS) == 10
    script = JOB.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^NON_CERTIFYING_SOURCE_RELATIVE_PATHS=\(\n(?P<body>.*?)^\)\s*$",
        script,
    )
    assert match is not None
    shell_paths = tuple(re.findall(r'^\s*"([^"]+)"\s*$', match["body"], re.M))
    assert shell_paths == paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    assert frozenset(shell_paths) == EXPECTED_NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    assert len(shell_paths) == 9
    assert script.count(
        'NON_CERTIFYING_SOURCE_RELATIVE_PATHS+=("orchestrator/calibrator/runner.py")'
    ) == 1
    for relative in paired.a1_source.SOURCE_PATHS:
        assert script.count(f'"{relative}"') == 3
    legacy = paired.load_policy()[0]
    pilot = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]
    assert paired._source_relative_paths(
        legacy, non_certifying=True,
    ) == paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    assert paired._source_relative_paths(
        pilot, non_certifying=True,
    ) == tuple(
        paired.V3_PILOT_POLICY_RELATIVE_PATH
        if item == paired.POLICY_RELATIVE_PATH else item
        for item in (*paired.V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS, *paired.a1_source.SOURCE_PATHS)
    )


def _clone_canonical_ccbench(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    target = repo / "external" / "ccbench"
    target.parent.mkdir(parents=True)
    subprocess.run(
        ["git", "clone", "--quiet", os.fspath(REPO_ROOT / "external/ccbench"),
         os.fspath(target)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", os.fspath(target), "checkout", "--quiet", "--detach",
         "511c9538e4e8efa54b45cda62e72389ed3b706ec"],
        check=True,
    )
    assert subprocess.run(
        ["git", "-C", os.fspath(target), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip() == "511c9538e4e8efa54b45cda62e72389ed3b706ec"
    return repo


@pytest.mark.parametrize(
    "boundary", ("login-submit", "driver-measurement", "artifact-consumer"),
)
def test_v3_ccbench_tracked_clean_gate_is_real_and_reason_is_layer_specific_M10(
    tmp_path: Path, boundary: str,
) -> None:
    """Acceptance implication: canonical HEAD plus tracked-clean accepts untracked output.
    Rejection implication: one tracked edit rejects with this boundary's unique reason.
    """
    repo = _clone_canonical_ccbench(tmp_path)
    policy = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]
    ccbench = repo / "external" / "ccbench"
    (ccbench / "untracked-generated-output").write_text("ignored\n", encoding="utf-8")
    paired._assert_ccbench_acceptance(repo, policy, boundary=boundary)
    # M3: real fixed-patch acceptance, with only one reason changed per rejection.
    from orchestrator.campaign import pipeline
    with paired.a1_source.materialized(REPO_ROOT, base=ccbench) as (context, stock):
        root = os.fspath(context.root)
        for kind in ("trace", "perf"):
            pipeline._require_canonical_build_source_state(
                root, context.pin, build_kind=kind, a1_source_context=context,
            )
            with pytest.raises(pipeline._CanonicalBuildSourceStateError, match="not clean"):
                pipeline._require_canonical_build_source_state(root, context.pin, build_kind=kind)
            with pytest.raises(pipeline._CanonicalBuildSourceStateError, match="root or canonical pin"):
                pipeline._require_canonical_build_source_state(
                    os.fspath(stock), context.pin, build_kind=kind, a1_source_context=context,
                )
            extra = context.root / "unexpected-source"
            extra.write_text("one undeclared file")
            try:
                with pytest.raises(pipeline._CanonicalBuildSourceStateError, match="tree-digest-mismatch"):
                    pipeline._require_canonical_build_source_state(
                        root, context.pin, build_kind=kind, a1_source_context=context,
                    )
            finally:
                extra.unlink()
            with pytest.raises(pipeline._CanonicalBuildSourceStateError, match="root or canonical pin"):
                pipeline._require_canonical_build_source_state(
                    root, "0" * 40, build_kind=kind, a1_source_context=context,
                )
    tracked = subprocess.run(
        ["git", "-C", os.fspath(ccbench), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    tracked_path = ccbench / tracked
    tracked_path.write_bytes(tracked_path.read_bytes() + b"\ntracked-drift\n")
    with pytest.raises(
        paired.PaperStoryError,
        match=rf"CCBench {re.escape(boundary)}: tracked files are dirty",
    ):
        paired._assert_ccbench_acceptance(repo, policy, boundary=boundary)


def test_v3_ccbench_five_boundary_wiring_is_exact_M10() -> None:
    """Acceptance implication: all five registered boundaries retain their exact wiring.
    Rejection implication: deleting any unit-C call or build policy bit breaks this signature.
    """
    source = Path(paired.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    def boundary_literals(function_name: str) -> list[str]:
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == function_name
        )
        return [
            keyword.value.value
            for call in ast.walk(function)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "_assert_ccbench_acceptance"
            for keyword in call.keywords
            if keyword.arg == "boundary"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        ]

    assert boundary_literals("run_submit") == ["login-submit"]
    assert boundary_literals("run_measurement") == ["driver-measurement"]
    assert boundary_literals("validate_workload_evidence") == [
        "artifact-consumer"
    ]
    policy = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]
    assert policy["ccbench_acceptance"]["boundaries"] == [
        "login-submit-before-intent-and-qsub",
        "compute-job-body-preflight",
        "driver-measurement-start",
        "before-each-trace-and-perf-build",
        "artifact-consumer-arm-validation-and-materializer-raw-recollection",
    ]
    assert policy["ccbench_acceptance"]["build_preflight_required"] is True
    job_source = JOB.read_text(encoding="utf-8")
    assert job_source.count(
        'CCBENCH_TRACKED_STATUS=$(git -C "$CCBENCH_ROOT" status'
    ) == 1
    assert job_source.count("--porcelain --untracked-files=no)") == 1
    assert job_source.count("--ignore-submodules=all") == 3
    assert job_source.count(
        'refuse "CCBench job-preflight tracked files are dirty"'
    ) == 1


@pytest.mark.parametrize("relative", paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS)
@pytest.mark.parametrize("mutation", ("missing", "oid", "working-sha"))
def test_non_certifying_source_closure_rejects_each_file_drift(
    relative: str, mutation: str,
) -> None:
    head = paired._run_git(REPO_ROOT, "rev-parse", "HEAD")
    binding = paired._non_certifying_source_binding(REPO_ROOT, head)
    if mutation == "missing":
        binding["files"].pop(relative)
    elif mutation == "oid":
        binding["files"][relative]["git_blob_oid"] = "0" * 40
    else:
        binding["files"][relative]["working_sha256"] = "0" * 64
    assert paired._validate_non_certifying_source_binding(binding) is (
        mutation != "missing"
    )
    with pytest.raises(paired.PaperStoryError, match="source binding"):
        paired._verify_current_source_paths(
            REPO_ROOT,
            head,
            binding,
            relative_paths=paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS,
            label="test non-certifying",
        )


@pytest.mark.parametrize(
    "state",
    ["Q", "queue", "XXX"],
    ids=["pbs-pro-Q", "lowercase-queue", "M23-outside-XXX"],
)
def test_acquisition_receipt_rejects_non_nqsv_qstat_state_M23(
    tmp_path: Path, state: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo, qstat_state=state)
    with pytest.raises(paired.PaperStoryError, match="qstat"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=_policy_for_base(base),
        )


def test_acquisition_receipt_binds_request_and_fixed_topology(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "trusted-attempt"
    attempt.mkdir()
    policy = _policy_for_base(base)
    roots = paired.validate_acquisition_receipt(
        _acquisition(attempt, repo),
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        pbs_observation=_pbs_observation(attempt, repo),
        policy=policy,
    )
    assert roots["raw_root"] == os.fspath(attempt / "raw")
    assert roots["cache_root"] == os.fspath(attempt / "cache")
    assert Path(roots["raw_root"]).parent == Path(roots["cache_root"]).parent

    with pytest.raises(paired.PaperStoryError, match="request ID"):
        paired.validate_acquisition_receipt(
            _acquisition(attempt, repo),
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="99999.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=policy,
        )


def test_request_id_normalization_accepts_nqsv_zero_prefix_M21(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(
        attempt,
        repo,
        request_id="944076.nqsv",
        qsub_stdout="944076.nqsv\n",
    )
    roots = paired.validate_acquisition_receipt(
        receipt,
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="0:944076.nqsv",
        pbs_observation=_pbs_observation(
            attempt, repo, pbs_jobid="0:944076.nqsv"
        ),
        policy=_policy_for_base(base),
    )
    assert receipt["request_id"] == "944076.nqsv"
    assert roots["attempt_root"] == os.fspath(attempt)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" 944076.nqsv ", "944076.nqsv"),
        ("944076.nqsv.", "944076.nqsv"),
        ("0:944076.nqsv", "944076.nqsv"),
    ],
)
def test_request_id_normalization_matches_dispatcher(
    raw: str, expected: str
) -> None:
    assert paired._normalize_request_id(raw) == expected


def test_qsub_stdout_parser_accepts_nqsv_sentence_M22(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(
        attempt,
        repo,
        request_id="944076.nqsv",
        qsub_stdout="Request 944076.nqsv submitted to queue: gen_S.\n",
    )
    paired.validate_acquisition_receipt(
        receipt,
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="944076.nqsv",
        pbs_observation=_pbs_observation(
            attempt, repo, pbs_jobid="944076.nqsv"
        ),
        policy=_policy_for_base(base),
    )


def test_real_nqsv_probe_values_positive_contract(tmp_path: Path) -> None:
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "probe-attempt"
    attempt.mkdir()
    probe = {
        "PBS_JOBID": "0:944076.nqsv",
        "PBS_O_HOST": "pegasus02",
        "PBS_O_WORKDIR": os.fspath(REPO_ROOT),
        "FD1": "pipe:[46452536]",
        "FD2": "/var/opt/nec/nqsv/jsv/jobfile/0.944076.10/stderr",
        "qsub_stdout": "Request 944076.nqsv submitted to queue: gen_S.\n",
        "qstat_state": "QUE",
    }
    receipt = _acquisition(
        attempt,
        REPO_ROOT,
        request_id="944076.nqsv",
        qsub_stdout=probe["qsub_stdout"],
        submit_host="pegasus02",
        qstat_state=probe["qstat_state"],
    )
    observation = {
        "pbs_jobid": probe["PBS_JOBID"],
        "pbs_o_host": probe["PBS_O_HOST"],
        "pbs_o_workdir": probe["PBS_O_WORKDIR"],
    }
    roots = paired.validate_acquisition_receipt(
        receipt,
        repo_root=REPO_ROOT,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id=probe["PBS_JOBID"],
        pbs_observation=observation,
        policy=_policy_for_base(base),
    )
    assert roots["attempt_root"] == os.fspath(attempt)
    assert "PBS_O_QUEUE" not in probe
    assert probe["FD1"].startswith("pipe:[")
    assert probe["FD2"].startswith("/var/opt/nec/nqsv/jsv/jobfile/")
    assert set(observation) == paired._PBS_OBSERVATION_KEYS


def test_request_id_rejects_nonzero_colon_prefix(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo, request_id="1:944076.nqsv")
    with pytest.raises(paired.PaperStoryError, match="unsafe"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="1:944076.nqsv",
            pbs_observation=_pbs_observation(
                attempt, repo, pbs_jobid="1:944076.nqsv"
            ),
            policy=_policy_for_base(base),
        )


@pytest.mark.parametrize(
    "qsub_stdout",
    [
        "unparseable qsub output\n",
        "Request 999999.nqsv submitted to queue: gen_S.\n",
    ],
    ids=["unparseable", "different-request"],
)
def test_qsub_stdout_parser_rejects_missing_or_different_request(
    tmp_path: Path, qsub_stdout: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo, qsub_stdout=qsub_stdout)
    with pytest.raises(paired.PaperStoryError, match="qsub stdout"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=_policy_for_base(base),
        )


@pytest.mark.parametrize(
    "field",
    [
        "pbs_jobid",
        "pbs_o_host",
        "pbs_o_workdir",
    ],
)
def test_pbs_environment_cross_bind_rejects_each_mismatch_M19(
    tmp_path: Path, field: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo)
    observation = _pbs_observation(attempt, repo)
    observation[field] += "-wrong"
    with pytest.raises(
        paired.PaperStoryError,
        match="PBS environment observation does not cross-bind receipt",
    ):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=observation,
            policy=_policy_for_base(base),
        )


def test_queue_binding_remains_in_submission_qstat_visibility(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo)
    receipt["submit_observation"]["qstat_visibility"]["queue"] = "other_queue"
    with pytest.raises(paired.PaperStoryError, match="qstat"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=_policy_for_base(base),
        )


def test_attempt_root_inode_revalidation_rejects_replacement_M20(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    trusted = paired.validate_acquisition_receipt(
        _acquisition(attempt, repo),
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        pbs_observation=_pbs_observation(attempt, repo),
        policy=_policy_for_base(base),
    )
    paired._revalidate_attempt_root(trusted)
    attempt.rename(base / "original-attempt")
    attempt.mkdir()
    with pytest.raises(paired.PaperStoryError, match="inode binding differs"):
        paired._revalidate_attempt_root(trusted)


def test_materializer_keeps_attempt_inode_revalidation_call_M20() -> None:
    source = (REPO_ROOT / paired.DRIVER_RELATIVE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    materializer = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_materialize"
    )
    calls = {
        node.func.id
        for node in ast.walk(materializer)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_revalidate_attempt_root" in calls


def test_submission_receipt_rejects_handmade_six_field_json(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    complete = _acquisition(attempt, repo)
    handmade = {
        key: complete[key]
        for key in (
            "schema_version", "route", "study_id", "source_commit",
            "attempt_root", "request_id",
        )
    }
    with pytest.raises(paired.PaperStoryError, match="submission receipt shape"):
        paired.validate_acquisition_receipt(
            handmade,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=_policy_for_base(base),
        )


def test_submission_receipt_rejects_noncanonical_qsub_argv_M15(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo)
    receipt["qsub_argv"][-1] = os.fspath(repo / "wrong-job.sh")
    with pytest.raises(paired.PaperStoryError, match="canonical qsub argv"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=_policy_for_base(base),
        )


def test_acquisition_receipt_requires_direct_durable_child_M16(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    policy = _policy_for_base(base)
    for attempt in (base, tmp_path / "outside", base / "parent" / "grandchild"):
        receipt = _acquisition(attempt, repo)
        with pytest.raises(paired.PaperStoryError, match="direct durable-base child"):
            paired.validate_acquisition_receipt(
                receipt,
                repo_root=repo,
                study_id=paired.STUDY_ID,
                source_commit="a" * 40,
                request_id="12345.nqsv",
                pbs_observation=_pbs_observation(attempt, repo),
                policy=policy,
            )

    target = tmp_path / "symlink-target"
    target.mkdir()
    alias = base / "alias"
    alias.symlink_to(target, target_is_directory=True)
    receipt = _acquisition(alias, repo)
    with pytest.raises(paired.PaperStoryError, match="canonical absolute"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(alias, repo),
            policy=policy,
        )


def _scheduler_completion_fixture(
    tmp_path: Path,
    *,
    request_id: str = "12345.nqsv",
    qsub_stdout: str | None = None,
) -> tuple[dict, dict, dict, bytes, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    submission = _acquisition(
        attempt,
        repo,
        request_id=request_id,
        qsub_stdout=qsub_stdout,
        qstat_state="QUE",
    )
    trusted = paired.validate_acquisition_receipt(
        submission,
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id=request_id,
        pbs_observation=_pbs_observation(
            attempt, repo, pbs_jobid=request_id
        ),
        policy=_policy_for_base(base),
    )
    submission_raw = (json.dumps(submission, sort_keys=True) + "\n").encode()
    Path(trusted["submission_receipt"]).write_bytes(submission_raw)
    Path(trusted["stdout_path"]).write_bytes(b"job stdout\n")
    Path(trusted["stderr_path"]).write_bytes(b"")
    terminal_path = Path(trusted["raw_root"]) / "job-terminal.json"
    terminal_path.parent.mkdir(parents=True)
    terminal_path.write_bytes(b"terminal\n")
    qstat_stdout = (
        f"Request ID: {request_id}\n"
        "    job_state = F\n"
        "    exit_status = 0\n"
    )

    def binding(path: str | Path) -> dict:
        candidate = Path(path)
        return {
            "path": os.fspath(candidate),
            "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        }

    completion = {
        "schema_version": paired.COMPLETION_SCHEMA,
        "study_id": paired.STUDY_ID,
        "source_commit": "a" * 40,
        "attempt_root": trusted["attempt_root"],
        "request_id": request_id,
        "submission_receipt": binding(trusted["submission_receipt"]),
        "scheduler_terminal": {
            "terminal_reason": "scheduler-end-state",
            "qstat_visible": True,
            "qstat_rc": 0,
            "state": {"observed": True, "value": "F"},
            "exit_status": {"observed": True, "value": 0},
            "observed_epoch": 2,
            "qstat_stdout": qstat_stdout,
            "qstat_stdout_sha256": hashlib.sha256(qstat_stdout.encode()).hexdigest(),
        },
        "stdout": binding(trusted["stdout_path"]),
        "stderr": binding(trusted["stderr_path"]),
        "job_terminal": binding(terminal_path),
    }
    return completion, submission, trusted, submission_raw, terminal_path


def test_scheduler_completion_receipt_cross_binds_terminal_and_logs(
    tmp_path: Path,
) -> None:
    completion, submission, trusted, submission_raw, terminal_path = (
        _scheduler_completion_fixture(tmp_path)
    )
    assert paired.validate_completion_receipt(
        completion,
        trusted_roots=trusted,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        submission_receipt=submission,
        submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
        job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
    ) == completion
    assert paired.validate_completion_receipt(
        completion,
        trusted_roots=trusted,
        source_commit="a" * 40,
        request_id="0:12345.nqsv",
        submission_receipt=submission,
        submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
        job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
    ) == completion

    incomplete = json.loads(json.dumps(completion))
    incomplete["stdout"].pop("sha256")
    with pytest.raises(paired.PaperStoryError, match="stdout binding"):
        paired.validate_completion_receipt(
            incomplete,
            trusted_roots=trusted,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            submission_receipt=submission,
            submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
            job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
        )

    Path(trusted["stdout_path"]).write_bytes(b"tampered scheduler stdout\n")
    with pytest.raises(paired.PaperStoryError, match="stdout hash"):
        paired.validate_completion_receipt(
            completion,
            trusted_roots=trusted,
            source_commit="a" * 40,
            request_id="0:12345.nqsv",
            submission_receipt=submission,
            submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
            job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
        )
    Path(trusted["stdout_path"]).write_bytes(b"job stdout\n")

    wrong_terminal_binding = json.loads(json.dumps(completion))
    wrong_terminal_binding["job_terminal"]["sha256"] = "0" * 64
    with pytest.raises(paired.PaperStoryError, match="job_terminal hash"):
        paired.validate_completion_receipt(
            wrong_terminal_binding,
            trusted_roots=trusted,
            source_commit="a" * 40,
            request_id="0:12345.nqsv",
            submission_receipt=submission,
            submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
            job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
        )


def test_scheduler_terminal_ext_flows_from_producer_to_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    completion, submission, trusted, submission_raw, terminal_path = (
        _scheduler_completion_fixture(tmp_path)
    )
    request_id = submission["request_id"]
    stdout = (
        f"Request ID: {request_id}\n"
        "State: EXT\n"
        "Exit Status: 0\n"
    )
    monkeypatch.setattr(
        paired.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout, "",
        ),
    )
    observed = paired._observe_scheduler_terminal(request_id, submission)
    assert observed["state"] == {"observed": True, "value": "EXT"}
    completion["scheduler_terminal"] = observed
    assert paired.validate_completion_receipt(
        completion,
        trusted_roots=trusted,
        source_commit="a" * 40,
        request_id=request_id,
        submission_receipt=submission,
        submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
        job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
    ) == completion


def _disappeared_completion_fixture(
    tmp_path: Path,
) -> tuple[dict, dict, dict, bytes, Path]:
    request_id = "944956.nqsv"
    values = _scheduler_completion_fixture(
        tmp_path,
        request_id=request_id,
        qsub_stdout=f"Request {request_id} submitted to queue: gen_S.\n",
    )
    completion, submission, trusted, submission_raw, terminal_path = values
    qstat_stdout = (
        f"Batch Request: {request_id} does not exist on nqsv.\n"
    )
    completion["scheduler_terminal"] = {
        "terminal_reason": "request-disappeared-after-visibility",
        "qstat_visible": False,
        "qstat_rc": 0,
        "state": {"observed": False},
        "exit_status": {"observed": False},
        "observed_epoch": 2,
        "qstat_stdout": qstat_stdout,
        "qstat_stdout_sha256": hashlib.sha256(qstat_stdout.encode()).hexdigest(),
    }
    return completion, submission, trusted, submission_raw, terminal_path


def test_scheduler_completion_accepts_disappearance_after_submission_visibility(
    tmp_path: Path,
) -> None:
    completion, submission, trusted, submission_raw, terminal_path = (
        _disappeared_completion_fixture(tmp_path)
    )
    assert submission["submit_observation"]["qstat_visibility"] == {
        "request_id": "944956.nqsv",
        "visible": True,
        "state": "QUE",
        "queue": "gen_S",
        "observed_epoch": 1,
    }
    assert paired.validate_completion_receipt(
        completion,
        trusted_roots=trusted,
        source_commit="a" * 40,
        request_id="0:944956.nqsv",
        submission_receipt=submission,
        submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
        job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
    ) == completion
    assert completion["scheduler_terminal"]["state"] == {"observed": False}
    assert completion["scheduler_terminal"]["exit_status"] == {"observed": False}


def test_real_nqsv_disappearance_flows_from_producer_to_completion_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_id = "900001.nqsv"
    completion, submission, trusted, submission_raw, terminal_path = (
        _scheduler_completion_fixture(tmp_path, request_id=request_id)
    )
    stdout = _qstat_fixture("qstat-f-absent-900001.stdout")
    stderr = _qstat_fixture("qstat-f-absent-900001.stderr")
    monkeypatch.setattr(
        paired.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout, stderr,
        ),
    )
    monkeypatch.setattr(paired.time, "time", lambda: 2)

    completion["scheduler_terminal"] = paired._observe_scheduler_terminal(
        request_id, submission,
    )
    assert paired.validate_completion_receipt(
        completion,
        trusted_roots=trusted,
        source_commit="a" * 40,
        request_id=request_id,
        submission_receipt=submission,
        submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
        job_terminal_sha256=hashlib.sha256(
            terminal_path.read_bytes()
        ).hexdigest(),
    ) == completion


@pytest.mark.parametrize(
    ("mutation", "request_id", "returncode", "stderr", "message"),
    [
        ("other-id", "900002.nqsv", 0, "", "observation failed"),
        ("diagnostic", "900001.nqsv", 0, "", "observation failed"),
        (
            "unchanged", "900001.nqsv", 0, "qstat warning\n",
            "observation failed",
        ),
        ("unchanged", "900001.nqsv", 1, "", "observation failed"),
        ("visible-run", "980043.nqsv", 0, "", "visible scheduler request"),
    ],
    ids=[
        "M5-other-request",
        "M6-nonsignature",
        "M7-nonempty-stderr",
        "nonzero-rc",
        "real-running-is-not-terminal",
    ],
)
def test_terminal_observer_rejects_nonterminal_nqsv_observations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    request_id: str,
    returncode: int,
    stderr: str,
    message: str,
) -> None:
    _completion, submission, _trusted, _submission_raw, _terminal_path = (
        _scheduler_completion_fixture(tmp_path, request_id=request_id)
    )
    if mutation == "visible-run":
        stdout = _qstat_fixture("qstat-f-980043.nqsv.txt")
    else:
        stdout = _qstat_fixture("qstat-f-absent-900001.stdout")
    if mutation == "diagnostic":
        stdout = "qstat: scheduler lookup returned no request\n"
    elif mutation not in {"other-id", "unchanged", "visible-run"}:
        raise AssertionError(f"unhandled test mutation: {mutation}")
    monkeypatch.setattr(
        paired.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], returncode, stdout, stderr,
        ),
    )
    monkeypatch.setattr(paired.time, "time", lambda: 2)

    with pytest.raises(paired.PaperStoryError, match=message):
        paired._observe_scheduler_terminal(request_id, submission)


@pytest.mark.parametrize(
    "mutation",
    ["other-id", "diagnostic"],
    ids=["M10-other-request", "M10-nonsignature"],
)
def test_completion_validator_reparses_disappearance_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    request_id = "900001.nqsv"
    completion, submission, trusted, submission_raw, terminal_path = (
        _scheduler_completion_fixture(tmp_path, request_id=request_id)
    )
    stdout = _qstat_fixture("qstat-f-absent-900001.stdout")
    monkeypatch.setattr(
        paired.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout, "",
        ),
    )
    monkeypatch.setattr(paired.time, "time", lambda: 2)
    completion["scheduler_terminal"] = paired._observe_scheduler_terminal(
        request_id, submission,
    )
    validation_kwargs = {
        "trusted_roots": trusted,
        "source_commit": "a" * 40,
        "request_id": request_id,
        "submission_receipt": submission,
        "submission_receipt_sha256": hashlib.sha256(submission_raw).hexdigest(),
        "job_terminal_sha256": hashlib.sha256(
            terminal_path.read_bytes()
        ).hexdigest(),
    }
    assert paired.validate_completion_receipt(
        completion, **validation_kwargs,
    ) == completion

    terminal = completion["scheduler_terminal"]
    if mutation == "other-id":
        terminal["qstat_stdout"] = stdout.replace("900001", "900002")
    elif mutation == "diagnostic":
        terminal["qstat_stdout"] = "qstat: scheduler lookup returned no request\n"
    else:
        raise AssertionError(f"unhandled test mutation: {mutation}")
    terminal["qstat_stdout_sha256"] = hashlib.sha256(
        terminal["qstat_stdout"].encode("utf-8")
    ).hexdigest()
    with pytest.raises(
        paired.PaperStoryError,
        match="disappeared scheduler terminal observation differs",
    ):
        paired.validate_completion_receipt(completion, **validation_kwargs)


def test_scheduler_completion_rejects_disappearance_without_prior_visibility_M32(
    tmp_path: Path,
) -> None:
    completion, submission, trusted, submission_raw, terminal_path = (
        _disappeared_completion_fixture(tmp_path)
    )
    submission["submit_observation"]["qstat_visibility"]["visible"] = False
    submission_raw = (json.dumps(submission, sort_keys=True) + "\n").encode()
    Path(trusted["submission_receipt"]).write_bytes(submission_raw)
    completion["submission_receipt"]["sha256"] = hashlib.sha256(
        submission_raw
    ).hexdigest()
    with pytest.raises(
        paired.PaperStoryError,
        match="disappearance lacks prior submission visibility",
    ):
        paired.validate_completion_receipt(
            completion,
            trusted_roots=trusted,
            source_commit="a" * 40,
            request_id="944956.nqsv",
            submission_receipt=submission,
            submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
            job_terminal_sha256=hashlib.sha256(
                terminal_path.read_bytes()
            ).hexdigest(),
        )


def test_scheduler_completion_rejects_fabricated_exit_zero_for_disappearance_M33(
    tmp_path: Path,
) -> None:
    completion, submission, trusted, submission_raw, terminal_path = (
        _disappeared_completion_fixture(tmp_path)
    )
    completion["scheduler_terminal"]["exit_status"] = {
        "observed": True,
        "value": 0,
    }
    with pytest.raises(
        paired.PaperStoryError,
        match="disappeared scheduler terminal observation differs",
    ):
        paired.validate_completion_receipt(
            completion,
            trusted_roots=trusted,
            source_commit="a" * 40,
            request_id="944956.nqsv",
            submission_receipt=submission,
            submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
            job_terminal_sha256=hashlib.sha256(
                terminal_path.read_bytes()
            ).hexdigest(),
        )


def _shell_body_without_heredocs(source: str) -> str:
    output = []
    delimiter = None
    opener = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
    for line in source.splitlines(keepends=True):
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        match = opener.search(line)
        if match is None:
            output.append(line)
            continue
        delimiter = match.group(2)
        output.append(line[:match.start()] + "<<< ''" + line[match.end():])
    if delimiter is not None:
        raise AssertionError("unterminated shell heredoc")
    return "".join(output)


def _shell_submitter_violations(source: str) -> list[str]:
    body = _shell_body_without_heredocs(source)
    syntax = subprocess.run(
        ["bash", "-n"], input=body, text=True, capture_output=True, check=False
    )
    if syntax.returncode != 0:
        raise AssertionError(f"heredoc-free shell syntax is invalid: {syntax.stderr}")
    violations = []
    declaration = re.compile(
        r"(?m)(?:^|[;{}&|])\s*(?:function\s+)?"
        r"(submit[A-Za-z0-9_]*)\s*(?:\(\s*\))?\s*\{"
    )
    violations.extend(
        f"submitter-function:{match.group(1)}" for match in declaration.finditer(body)
    )

    lexer = shlex.shlex(body, posix=True, punctuation_chars=";&|(){}\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = "#"
    command_position = True
    wrapper = False
    indirect_qsub = set()
    separators = {";", ";;", "&", "&&", "|", "||", "(", ")", "{", "}", "\n"}
    reserved = {"if", "then", "elif", "else", "while", "until", "do"}
    for token in lexer:
        if token in separators or set(token) <= set(";&|(){}\n"):
            command_position = True
            wrapper = False
            continue
        if not command_position:
            continue
        assignment = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", token)
        if assignment is not None:
            name, value = assignment.groups()
            if Path(value).name == "qsub" or "QSUB" in name.upper():
                indirect_qsub.add(name)
            continue
        if token in reserved or token == "!":
            continue
        if token in {"command", "exec", "builtin"}:
            wrapper = True
            continue
        if wrapper and token == "--":
            continue
        variable = re.fullmatch(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", token)
        if Path(token).name == "qsub":
            violations.append(f"qsub-invocation:{token}")
        elif variable is not None and (
            variable.group(1) in indirect_qsub
            or "QSUB" in variable.group(1).upper()
        ):
            violations.append(f"qsub-indirect:{token}")
        command_position = False
        wrapper = False
    return violations


@pytest.mark.parametrize(
    "source",
    [
        "submit_job() { qsub job.sh; }\n",
        "function submit_job { :; }\n",
        "command qsub job.sh\n",
        "/usr/bin/qsub job.sh\n",
        "QSUB=/usr/bin/qsub\n$QSUB job.sh\n",
    ],
)
def test_submitter_guard_detects_bash_syntax_variants(source: str) -> None:
    assert _shell_submitter_violations(source)


def test_submitter_guard_ignores_python_heredoc_receipt_keys() -> None:
    source = """#!/bin/bash
python3 - <<'PY'
document = {"submit_observation": {"submit_host": "pegasus01"}}
PY
"""
    assert _shell_submitter_violations(source) == []


def test_job_body_contains_all_m12_gates_and_no_submitter() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert 'EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"' not in source
    assert source.count('EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"') == 3
    assert source.count(
        'POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v2.json"'
    ) == 1
    required = (
        '[[ -n "${PBS_JOBID:-}" ]]',
        '[[ -n "${PBS_O_HOST:-}" ]]',
        '[[ -n "${PBS_O_WORKDIR:-}" ]]',
        '[[ -n "${IZANAGI_A1_ACQUISITION_RECEIPT:-}" ]]',
        '[[ -n "${IZANAGI_A1_COMPLETION_RECEIPT:-}" ]]',
        '[[ "$CURRENT_HEAD" == "$IZANAGI_EXPECTED_HEAD" ]]',
        "site_policy.PEGASUS_COMPUTE",
        "for ((WAITED=0; WAITED<60; WAITED++))",
        'mkdir -- "$ATTEMPT_ROOT"',
        'mkdir -- "$RAW_ROOT"',
        '--study-id "$EXPECTED_STUDY_ID"',
        '--expected-head "$IZANAGI_EXPECTED_HEAD"',
        '--acquisition-receipt "$IZANAGI_A1_ACQUISITION_RECEIPT"',
        '--acquisition-receipt-sha256 "$ACQUISITION_SHA"',
        '--output-root "$OUTPUT_ROOT"',
        '--cache-root "$CACHE_ROOT"',
        '--result-root "$RESULT_ROOT"',
        'export IZANAGI_EXPLORATION_OUTPUT_ROOT="$OUTPUT_ROOT"',
        "os.O_EXCL",
        'observation["submit_host"] != pbs_o_host',
        'normalized.startswith("0:")',
        'request_pattern = re.compile(r"Request\\s+(\\S+)\\s+submitted")',
        "from orchestrator.campaign.paper_story_a1_paired import NQSV_QSTAT_STATES",
        'visibility["state"] not in NQSV_QSTAT_STATES',
        'visibility["queue"] != expected_queue',
        '"pbs_observation": {',
        '"reservation_binding": reservation_binding,',
        '"attempt_identity": {',
        "/proc/sys/kernel/random/boot_id",
        'PEGASUS_POLICY_RELATIVE="tools/pegasus/policy.json"',
        'DEPENDENCY_SCRATCH_PARENT=/scr',
        'DEPENDENCY_SCRATCH_PARENT=${TMPDIR:-}',
        '[[ -n "$DEPENDENCY_SCRATCH_PARENT" ]]',
        '[[ -d "$DEPENDENCY_SCRATCH_PARENT" ]]',
        'DEPENDENCY_ROOT=$(mktemp -d --',
        '"$DEPENDENCY_SCRATCH_PARENT/${PBS_JOBID//:/_}.',
        '${IZANAGI_SUBMISSION_NONCE}.XXXXXXXX")',
        'DEPENDENCY_ROOT_OWNED=1',
        '/bin/rm -rf -- "$DEPENDENCY_ROOT"',
        'if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]',
        'if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]',
        '"-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"',
        'DEPENDENCY_PREFIX="$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"',
        '--dependency-prefix "$DEPENDENCY_PREFIX"',
    )
    repeated_for_v3_failure_terminal = {
        "os.O_EXCL": 2,
        '"pbs_observation": {': 2,
        '"attempt_identity": {': 2,
    }
    for marker in required:
        assert source.count(marker) == repeated_for_v3_failure_terminal.get(
            marker, 1,
        ), marker
    assert _shell_submitter_violations(source) == []
    assert "dispatch_compute.py" not in source
    assert "PBS_O_QUEUE" not in source
    proc_paths = re.findall(r"/proc/[A-Za-z0-9_./-]+", source)
    assert proc_paths.count("/proc/sys/kernel/random/boot_id") == 1
    assert proc_paths.count("/proc/uptime") == 2
    assert source.count(
        'for candidate in pathlib.Path("/proc").iterdir():'
    ) == 2
    assert 'print("single-tenant-same-uid-process-set/v1")' in source
    assert 'method = "single-tenant-same-uid-process-set/v1"' in source
    assert "created_during_job = process_identity not in baseline" in source
    assert "os.readlink" not in source
    assert 're.fullmatch(r"[A-Z]", visibility["state"])' not in source
    assert source.count("status --porcelain --untracked-files=all") == 3


def test_job_body_dispatches_legacy_pilot_and_future_sized_studies() -> None:
    """Acceptance: the case statement selects each policy and one v3 bit.
    Rejection: the terminal consumer may not re-select by enumerating study IDs.
    """
    source = JOB.read_text(encoding="utf-8")
    assert source.count("paper-story-a1-20260826-sized-v1") == 1
    assert source.count("paper-story-a1-20260901-balanced5-pilot-v1") == 1
    assert source.count("paper-story-a1-20260901-balanced5-sized-v1") == 1
    assert source.count(
        'POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v3-pilot.json"'
    ) == 1
    assert source.count(
        'POLICY_RELATIVE="orchestrator/campaign/paper_story_a1_paired.v3-sized.json"'
    ) == 1
    assert source.count('V3_STUDY=1') == 2
    assert source.count(
        '"$V3_STUDY" "$PBS_JOBID" "$IZANAGI_EXPECTED_HEAD"'
    ) == 1
    assert source.count(
        'if v3_study_raw not in {"0", "1"}:'
    ) == 1
    assert source.count('v3_study = v3_study_raw == "1"') == 1
    assert source.count("if v3_study:") == 4
    assert 'study_id != "paper-story-a1-20260826-sized-v1"' not in source
    assert 'refuse "study ID differs"' in source


def _fixture_job_source(source: str) -> str:
    production = "DEPENDENCY_SCRATCH_PARENT=/scr\n"
    assert source.count(production) == 1
    return source.replace(
        production,
        "DEPENDENCY_SCRATCH_PARENT=${TMPDIR:-}\n",
        1,
    )


def _shell_fixture(tmp_path: Path, *, dirty: bool = False, mode: str = "ok"):
    repo = tmp_path / "repo"
    driver = repo / paired.DRIVER_RELATIVE_PATH
    driver.parent.mkdir(parents=True)
    (driver.parents[1] / "__init__.py").write_text("", encoding="utf-8")
    (driver.parent / "__init__.py").write_text("", encoding="utf-8")
    driver.write_text(
        "NQSV_QSTAT_STATES = frozenset("
        f"{tuple(sorted(paired.NQSV_QSTAT_STATES))!r})\n",
        encoding="utf-8",
    )
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    policy_path = repo / paired.POLICY_RELATIVE_PATH
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        json.dumps(_policy_for_base(base), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    staging = repo / "output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
    gflags_source = staging / "gflags"
    glog_source = staging / "glog"
    gflags_source.mkdir(parents=True)
    glog_source.mkdir()
    gflags_expected_head = "c" * 40
    glog_expected_head = "d" * 40
    pegasus_policy = repo / "tools/pegasus/policy.json"
    pegasus_policy.parent.mkdir(parents=True, exist_ok=True)
    pegasus_policy.write_text(
        json.dumps({
            "gflags_expected_head": gflags_expected_head,
            "glog_expected_head": glog_expected_head,
        }, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    job = repo / paired.JOB_RELATIVE_PATH
    job.parent.mkdir(parents=True, exist_ok=True)
    job.write_text(
        _fixture_job_source(JOB.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    job.chmod(JOB.stat().st_mode & 0o777)
    for relative in paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS:
        fixture_source = repo / relative
        if fixture_source.exists():
            continue
        fixture_source.parent.mkdir(parents=True, exist_ok=True)
        fixture_source.write_bytes((REPO_ROOT / relative).read_bytes())
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    head = "a" * 40
    git_stub = bin_dir / "git"
    git_stub.write_text(
        "#!/bin/bash\n"
        "if [[ \"$*\" == *\"rev-parse HEAD\"* ]]; then\n"
        f"  if [[ \"$1\" == -C && \"$2\" == {shlex.quote(str(gflags_source))} ]]; then echo \"$FAKE_GFLAGS_HEAD\"; "
        f"elif [[ \"$1\" == -C && \"$2\" == {shlex.quote(str(glog_source))} ]]; then echo \"$FAKE_GLOG_HEAD\"; "
        "else echo \"$FAKE_HEAD\"; fi; exit 0\n"
        "fi\n"
        "if [[ \"$*\" == *\"status --porcelain\"* ]]; then\n"
        f"  if [[ \"$1\" == -C && \"$2\" == {shlex.quote(str(gflags_source))} ]]; then "
        "[[ \"${FAKE_GFLAGS_DIRTY:-0}\" == 1 ]] && echo ' M gflags.cc'; "
        f"elif [[ \"$1\" == -C && \"$2\" == {shlex.quote(str(glog_source))} ]]; then "
        "[[ \"${FAKE_GLOG_DIRTY:-0}\" == 1 ]] && echo ' M glog.cc'; "
        "elif [[ \"${FAKE_DIRTY:-0}\" == 1 ]]; then echo ' M tracked.py'; fi; exit 0\n"
        "fi\n"
        "echo \"${FAKE_BLOB:-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb}\"\n",
        encoding="utf-8",
    )
    git_stub.chmod(0o755)
    qstat_stub = bin_dir / "qstat"
    qstat_stub.write_text(
        "#!/bin/bash\n"
        "printf 'exec_host = compute01\\nstart_time = %s\\n' \"$(/bin/date +%s)\"\n",
        encoding="utf-8",
    )
    qstat_stub.chmod(0o755)
    hostname_stub = bin_dir / "hostname"
    hostname_stub.write_text(
        "#!/bin/bash\n"
        "if [[ \"${1:-}\" == '-f' ]]; then echo compute01.example; "
        "else echo compute01; fi\n",
        encoding="utf-8",
    )
    hostname_stub.chmod(0o755)
    cmake_stub = bin_dir / "cmake"
    cmake_stub.write_text(
        "#!/bin/bash\n"
        "printf 'cmake %s\\n' \"$*\" >> \"$STUB_LOG\"\n"
        "exit \"${FAKE_CMAKE_RC:-0}\"\n",
        encoding="utf-8",
    )
    cmake_stub.chmod(0o755)
    python_stub_source = (
        "#!/bin/bash\n"
        "printf '%s\\n' \"$*\" >> \"$STUB_LOG\"\n"
        "if [[ \"$1\" == '-c' ]]; then exec /usr/bin/python3 \"$@\"; fi\n"
        "if [[ \"$1\" == '-' && \"$2\" == *.submission.json ]]; then "
        "exec /usr/bin/python3 \"$@\"; fi\n"
        "if [[ \"$1\" == '-' && \"$2\" == *qstat-f.stdout ]]; then "
        "exec /usr/bin/python3 \"$@\"; fi\n"
        "if [[ \"$1\" == '-' && \"$2\" == */tools/pegasus/policy.json ]]; then "
        "exec /usr/bin/python3 \"$@\"; fi\n"
        "if [[ \"$1\" == '-' && \"$2\" == *job-terminal.json ]]; then\n"
        "  [[ \"$STUB_MODE\" == writer-fail ]] && exit 9\n"
        "  : > \"$2\"; exit 0\n"
        "fi\n"
        "if [[ \"$1\" == '-' ]]; then exit 0; fi\n"
        "if [[ \"$1\" == *.py ]]; then\n"
        "  if [[ \"$STUB_MODE\" == require-reservation ]]; then\n"
        "    /usr/bin/python3 -c 'import os; "
        "from orchestrator.campaign import paper_story_a1_paired as p; "
        "binding = p._reservation_binding_from_environment(os.environ); "
        "[print(\"IZANAGI_RESERVATION_\" + key.upper() + \"=\" + str(value)) "
        "for key, value in binding.items()]' >> \"$STUB_LOG\" || exit 27\n"
        "  fi\n"
        "  if [[ \"$STUB_MODE\" == existing-terminal ]]; then "
        ": > \"$IZANAGI_A1_ATTEMPT_ROOT/raw/job-terminal.json\"; fi\n"
        "  exit 0\n"
        "fi\n"
        "exit 8\n"
    )
    for name in ("python3.10", "python3.11", "python3.12", "python3"):
        stub = bin_dir / name
        stub.write_text(python_stub_source, encoding="utf-8")
        stub.chmod(0o755)
    attempt = base / "attempt"
    acquisition = Path(paired._attempt_evidence_paths(attempt)["submission_receipt"])
    acquisition.write_text(
        json.dumps(_acquisition(attempt, repo), sort_keys=True) + "\n", encoding="utf-8"
    )
    completion = Path(paired._attempt_evidence_paths(attempt)["completion_receipt"])
    log = tmp_path / "stub.log"
    dependency_scratch_parent = (tmp_path / "dependency-scratch").resolve()
    dependency_scratch_parent.mkdir()
    environment = {
        **os.environ,
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "TMPDIR": os.fspath(dependency_scratch_parent),
        "PBS_JOBID": "12345.nqsv",
        "PBS_O_HOST": "pegasus01",
        "PBS_O_WORKDIR": os.fspath(repo),
        "IZANAGI_A1_STUDY_ID": paired.STUDY_ID,
        "IZANAGI_EXPECTED_HEAD": head,
        "IZANAGI_A1_ATTEMPT_ROOT": os.fspath(attempt),
        "IZANAGI_A1_ACQUISITION_RECEIPT": os.fspath(acquisition),
        "IZANAGI_A1_COMPLETION_RECEIPT": os.fspath(completion),
        "IZANAGI_SUBMISSION_NONCE": attempt.name,
        "FAKE_HEAD": head,
        "FAKE_GFLAGS_HEAD": gflags_expected_head,
        "FAKE_GLOG_HEAD": glog_expected_head,
        "FAKE_DIRTY": "1" if dirty else "0",
        "STUB_LOG": os.fspath(log),
        "STUB_MODE": mode,
    }
    return environment, attempt, log


def _run_shell_job(
    environment: dict[str, str],
    *,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
    job_path: Path | None = None,
):
    attempt = Path(environment["IZANAGI_A1_ATTEMPT_ROOT"])
    evidence = paired._attempt_evidence_paths(attempt)
    stdout_path = stdout_path or Path(evidence["stdout_path"])
    stderr_path = stderr_path or Path(evidence["stderr_path"])
    job_path = job_path or (
        Path(environment["PBS_O_WORKDIR"]) / paired.JOB_RELATIVE_PATH
    )
    with stdout_path.open("w", encoding="utf-8") as stdout_stream, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_stream:
        completed = subprocess.run(
            [os.fspath(job_path)],
            env=environment,
            text=True,
            stdout=stdout_stream,
            stderr=stderr_stream,
            check=False,
        )
    return completed, stderr_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "field",
    ["pbs_jobid", "pbs_o_host", "pbs_o_workdir"],
)
def test_production_job_rejects_pbs_environment_cross_bind_M19(
    tmp_path: Path, field: str
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path)
    if field == "pbs_jobid":
        environment["PBS_JOBID"] = "99999.nqsv"
    elif field == "pbs_o_host":
        environment["PBS_O_HOST"] = "other-submit-host"
    else:
        alias = tmp_path / "repo-alias"
        alias.symlink_to(environment["PBS_O_WORKDIR"], target_is_directory=True)
        environment["PBS_O_WORKDIR"] = os.fspath(alias)
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "acquisition receipt validation failed" in stderr
    assert not attempt.exists()


def test_production_job_subprocess_rejects_dirty_before_creating_roots(
    tmp_path: Path,
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path, dirty=True)
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "working tree is dirty" in stderr
    assert not attempt.exists()


def test_production_job_rejects_missing_study_id_before_creating_roots(
    tmp_path: Path,
) -> None:
    """Acceptance: an explicit supported study ID can reach later job gates.
    Rejection: a missing study ID fails closed before creating the attempt root.
    """
    environment, attempt, _ = _shell_fixture(tmp_path)
    environment.pop("IZANAGI_A1_STUDY_ID")
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "study ID differs" in stderr
    assert not attempt.exists()


def test_production_job_rejects_noncanonical_qsub_argv_M15(
    tmp_path: Path,
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path)
    receipt_path = Path(environment["IZANAGI_A1_ACQUISITION_RECEIPT"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["qsub_argv"][-1] = os.fspath(tmp_path / "wrong-job.sh")
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "acquisition receipt validation failed" in stderr
    assert not attempt.exists()


def test_production_job_narrow_stub_reaches_site_and_driver(tmp_path: Path) -> None:
    environment, attempt, log = _shell_fixture(tmp_path)
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 0, stderr
    assert (attempt / "raw/tmp").is_dir()
    logged = log.read_text(encoding="utf-8")
    assert paired.DRIVER_RELATIVE_PATH in logged
    staging = (tmp_path / "repo"
               / "output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src")
    assert f"cmake -S {staging / 'gflags'} " in logged
    assert f"cmake -S {staging / 'glog'} " in logged
    assert "cmake --install " in logged
    assert "-DCMAKE_PREFIX_PATH=" in logged
    assert "--dependency-prefix " in logged
    scratch_match = re.search(r" -B (\S+)/gflags-build(?:\s|$)", logged)
    assert scratch_match is not None
    assert not Path(scratch_match.group(1)).exists()


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("FAKE_GFLAGS_DIRTY", "gflags working tree is dirty"),
        ("FAKE_GLOG_DIRTY", "glog working tree is dirty"),
    ],
    ids=["gflags", "glog"],
)
def test_production_job_rejects_dirty_dependency_source(
    tmp_path: Path, field: str, message: str
) -> None:
    environment, _, _ = _shell_fixture(tmp_path)
    environment[field] = "1"
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert message in stderr


def test_production_job_rejects_dependency_source_head_mismatch_M28(
    tmp_path: Path,
) -> None:
    environment, attempt, log = _shell_fixture(tmp_path)
    environment["FAKE_GFLAGS_HEAD"] = "e" * 40
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert stderr.splitlines() == [
        "paper-story A-1 job refused: gflags source HEAD mismatch"
    ]
    assert (attempt / "raw/job-terminal.json").exists()
    assert paired.DRIVER_RELATIVE_PATH not in log.read_text(encoding="utf-8")


def test_production_job_does_not_reuse_or_remove_unowned_dependency_scratch_M38(
    tmp_path: Path,
) -> None:
    environment, _, _ = _shell_fixture(tmp_path)
    existing = tmp_path / "preexisting-dependency-scratch"
    existing.mkdir()
    marker = existing / "owned-by-someone-else"
    marker.write_text("keep\n", encoding="utf-8")
    bin_dir = Path(environment["PATH"].split(":", 1)[0])
    mktemp_stub = bin_dir / "mktemp"
    mktemp_stub.write_text(
        "#!/bin/bash\n"
        "printf '%s\\n' \"$FAKE_EXISTING_DEPENDENCY_ROOT\"\n"
        "exit 1\n",
        encoding="utf-8",
    )
    mktemp_stub.chmod(0o755)
    environment["FAKE_EXISTING_DEPENDENCY_ROOT"] = os.fspath(existing)

    completed, stderr = _run_shell_job(environment)

    assert completed.returncode == 2
    assert stderr.splitlines() == [
        "paper-story A-1 job refused: "
        "dependency scratch root cannot be exclusive-created"
    ]
    assert marker.read_text(encoding="utf-8") == "keep\n"


def test_production_job_rejects_missing_dependency_scratch_parent_before_mktemp(
    tmp_path: Path,
) -> None:
    environment, _, _ = _shell_fixture(tmp_path)
    missing_parent = tmp_path / "missing-dependency-scratch"
    environment["TMPDIR"] = os.fspath(missing_parent)
    mktemp_called = tmp_path / "mktemp-called"
    bin_dir = Path(environment["PATH"].split(":", 1)[0])
    mktemp_stub = bin_dir / "mktemp"
    mktemp_stub.write_text(
        "#!/bin/bash\n"
        ": > \"$FAKE_MKTEMP_CALLED\"\n"
        "exit 88\n",
        encoding="utf-8",
    )
    mktemp_stub.chmod(0o755)
    environment["FAKE_MKTEMP_CALLED"] = os.fspath(mktemp_called)

    completed, stderr = _run_shell_job(environment)

    assert completed.returncode == 2
    assert stderr.splitlines() == [
        "paper-story A-1 job refused: dependency scratch parent is unavailable"
    ]
    assert not mktemp_called.exists()


def test_job_body_exports_complete_reservation_and_rejects_missing_one_M27(
    tmp_path: Path,
) -> None:
    source = JOB.read_text(encoding="utf-8")
    observed = dict(re.findall(
        r'^export (IZANAGI_RESERVATION_[A-Z0-9_]+)="([^"\n]+)"$',
        source,
        flags=re.MULTILINE,
    ))
    assert observed == EXPECTED_RESERVATION_EXPORTS

    positive_env, _, positive_log = _shell_fixture(
        tmp_path / "positive", mode="require-reservation"
    )
    positive_env["PBS_JOBID"] = "0:12345.nqsv"
    positive_job = (
        Path(positive_env["PBS_O_WORKDIR"]) / paired.JOB_RELATIVE_PATH
    )
    positive_job.write_text(_fixture_job_source(source), encoding="utf-8")
    positive_job.chmod(0o755)
    completed, stderr = _run_shell_job(positive_env, job_path=positive_job)
    assert completed.returncode == 0, stderr
    reservation = dict(
        line.split("=", 1)
        for line in positive_log.read_text(encoding="utf-8").splitlines()
        if line.startswith("IZANAGI_RESERVATION_")
    )
    assert set(reservation) == set(EXPECTED_RESERVATION_EXPORTS)
    assert reservation["IZANAGI_RESERVATION_JOB_ID"] == positive_env["PBS_JOBID"]
    assert reservation["IZANAGI_RESERVATION_REQUESTED_S"] == "21600"
    assert int(float(reservation["IZANAGI_RESERVATION_DEADLINE_EPOCH"])) == (
        int(float(reservation["IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH"]))
        + 21600
    )

    missing = "IZANAGI_RESERVATION_NONCE"
    export_line = f'export {missing}="{EXPECTED_RESERVATION_EXPORTS[missing]}"\n'
    assert source.count(export_line) == 1
    mutant = source.replace(export_line, "", 1)
    mutant_env, _, _ = _shell_fixture(
        tmp_path / "mutant", mode="require-reservation"
    )
    mutant_env["PBS_JOBID"] = "0:12345.nqsv"
    mutant_job = Path(mutant_env["PBS_O_WORKDIR"]) / paired.JOB_RELATIVE_PATH
    mutant_job.write_text(_fixture_job_source(mutant), encoding="utf-8")
    mutant_job.chmod(0o755)
    completed, _ = _run_shell_job(mutant_env, job_path=mutant_job)
    assert completed.returncode == 27


def test_production_job_rejects_missing_elapstim_req_declaration(
    tmp_path: Path,
) -> None:
    environment, _, _ = _shell_fixture(tmp_path)
    job = Path(environment["PBS_O_WORKDIR"]) / paired.JOB_RELATIVE_PATH
    source = job.read_text(encoding="utf-8")
    declarations = re.findall(
        r"^#PBS[ \t]+-l[ \t]+elapstim_req=[0-9]{2}:[0-9]{2}:[0-9]{2}[ \t]*$",
        source,
        flags=re.MULTILINE,
    )
    assert len(declarations) == 1
    job.write_text(source.replace(declarations[0], "", 1), encoding="utf-8")

    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "job body must declare exactly one HH:MM:SS elapstim_req" in stderr


def test_production_job_does_not_gate_on_nqsv_fd_targets(tmp_path: Path) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path)
    completed, stderr = _run_shell_job(
        environment,
        stdout_path=tmp_path / "nqsv-pipe-surrogate.stdout",
        stderr_path=tmp_path / "nqsv-spool-surrogate.stderr",
    )
    assert completed.returncode == 0, stderr
    assert (attempt / "raw/tmp").is_dir()


def test_production_job_accepts_nqsv_request_and_stdout_M21_M22(
    tmp_path: Path,
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path)
    environment["PBS_JOBID"] = "0:944076.nqsv"
    receipt_path = Path(environment["IZANAGI_A1_ACQUISITION_RECEIPT"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    qsub_stdout = "Request 944076.nqsv submitted to queue: gen_S.\n"
    receipt["request_id"] = "944076.nqsv"
    receipt["submit_observation"]["qsub_stdout"] = qsub_stdout
    receipt["submit_observation"]["qsub_stdout_sha256"] = hashlib.sha256(
        qsub_stdout.encode()
    ).hexdigest()
    receipt["submit_observation"]["qstat_visibility"]["request_id"] = (
        "944076.nqsv"
    )
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 0, stderr
    assert (attempt / "raw/tmp").is_dir()


@pytest.mark.parametrize(
    "state",
    ["Q", "queue", "XXX"],
    ids=["pbs-pro-Q", "lowercase-queue", "M23-outside-XXX"],
)
def test_production_job_rejects_non_nqsv_qstat_state_M23(
    tmp_path: Path, state: str
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path)
    receipt_path = Path(environment["IZANAGI_A1_ACQUISITION_RECEIPT"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["submit_observation"]["qstat_visibility"]["state"] = state
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "acquisition receipt validation failed" in stderr
    assert not attempt.exists()


@pytest.mark.parametrize("mode", ["writer-fail", "existing-terminal"])
def test_production_job_terminal_writer_failures_are_nonzero(
    tmp_path: Path, mode: str
) -> None:
    environment, _, _ = _shell_fixture(tmp_path, mode=mode)
    completed, _ = _run_shell_job(environment)
    assert completed.returncode == 70


def test_job_body_is_executable_and_registry_is_exact_dispatch_required() -> None:
    assert JOB.stat().st_mode & 0o111
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    assert registry["tools/pegasus/paper_story_a1_paired.sh"] == {
        "class": "dispatch-required",
        "reason": "PBS paper-story A-1 paired measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }


def test_driver_reuses_run_campaign_without_direct_evaluate_call() -> None:
    source = (REPO_ROOT / paired.DRIVER_RELATIVE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "run_campaign" in imported
    assert "BalancedScheduleConfig" in imported
    assert "run_campaign" in called
    assert "_campaign_execution_options" in called
    assert "_require_registered_execution_options" in called
    assert "evaluate" not in imported
    assert "evaluate" not in called
    measurement = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_measurement"
    )
    production_calls = [
        node for node in ast.walk(measurement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_campaign"
    ]
    assert len(production_calls) == 1
    assert [
        keyword.value.id
        for keyword in production_calls[0].keywords
        if keyword.arg is None and isinstance(keyword.value, ast.Name)
    ] == ["execution_options"]
    policy = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]
    options = paired._campaign_execution_options(policy, "write-heavy")
    schedule = options["balanced_schedule"]
    assert type(schedule) is paired.BalancedScheduleConfig
    assert options["bench_max_rounds"] == 1
    assert schedule.arm_names == paired._workload_arm_order(
        policy, "write-heavy",
    )
    cfg = paired.campaign_config(policy, "write-heavy")
    assert cfg.search_config["arm_order"] == list(schedule.arm_names)
    assert cfg.ccbench_commit == paired.CANONICAL_CCBENCH_OID


def test_v3_measurement_runs_one_selected_campaign_but_registers_exact_triple() -> None:
    tree = ast.parse(
        (REPO_ROOT / paired.DRIVER_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    producer = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_run_measurement_v3"
    )
    calls = [
        node for node in ast.walk(producer)
        if isinstance(node, ast.Call)
    ]
    assert sum(
        isinstance(node.func, ast.Name) and node.func.id == "run_campaign"
        for node in calls
    ) == 1
    assert sum(
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "issue_a1_registered_noncertifying_projection"
        for node in calls
    ) == 1
    projection_call = next(
        node for node in calls
        if isinstance(node.func, ast.Attribute)
        and node.func.attr == "issue_a1_registered_noncertifying_projection"
    )
    keyword_values = {keyword.arg: keyword.value for keyword in projection_call.keywords}
    assert isinstance(keyword_values["workloads"], ast.Name)
    assert keyword_values["workloads"].id == "WORKLOAD_ORDER"
    assert isinstance(keyword_values["campaign_ids"], ast.Name)
    assert keyword_values["campaign_ids"].id == "campaign_ids"
    gate_wrapper = next(
        node for node in ast.walk(producer)
        if isinstance(node, ast.FunctionDef)
        and node.name == "gated_balanced_executor"
    )
    materializer = next(node for node in ast.walk(producer) if isinstance(node, ast.With)
                        and "a1_source.materialized" in ast.unparse(node.items[0].context_expr))
    inner_calls = [node for node in ast.walk(materializer) if isinstance(node, ast.Call)]
    assert {k.arg: ast.unparse(k.value) for k in materializer.items[0].context_expr.keywords} == {
        "study_id": "study_id",
    }
    by_name = {ast.unparse(node.func): node for node in inner_calls}
    gate_args = {k.arg: ast.unparse(k.value) for k in by_name["_require_v3_backoff_fixed_condition_gate"].keywords}
    campaign_args = {k.arg: ast.unparse(k.value) for k in by_name["run_campaign"].keywords if k.arg}
    assert gate_args["source_root"] == "source_context.root"
    assert gate_args["dependency_prefix"] == "dependency_prefix"
    assert campaign_args["ccbench_dir"] == "os.fspath(source_context.root)"
    assert campaign_args["a1_source_context"] == "source_context"
    assert "collect_workload" in by_name
    assert isinstance(gate_wrapper.body[0], ast.Expr)
    assert isinstance(gate_wrapper.body[0].value, ast.Call)
    assert isinstance(gate_wrapper.body[0].value.func, ast.Name)
    assert gate_wrapper.body[0].value.func.id == "_v3_barrier_before_bench"
    assert isinstance(gate_wrapper.body[1], ast.Return)
    assert isinstance(gate_wrapper.body[1].value, ast.Call)
    assert isinstance(gate_wrapper.body[1].value.func, ast.Name)
    assert gate_wrapper.body[1].value.func.id == "original_balanced_executor"


def test_exact_two_arm_three_workload_campaign_ids_are_distinct_and_bound() -> None:
    policy = paired.load_policy()[0]
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    ids = [
        str(ident.campaign_id(ident.bind_admission_policy(
            paired.campaign_config(policy, workload), context.policy
        )))
        for workload in paired.WORKLOAD_ORDER
    ]
    assert len(set(ids)) == 3
    assert len(paired.genomes(policy)) == 2
    expected_reps = {
        "write-heavy": 72,
        "balanced": 205,
        "read-heavy": 28,
    }
    for workload in paired.WORKLOAD_ORDER:
        cfg = ident.bind_admission_policy(
            paired.campaign_config(policy, workload), context.policy
        )
        assert cfg.search_config["study_id"] == paired.STUDY_ID
        assert cfg.search_config["arm_order"] == ["adaptive", "static10"]
        assert cfg.search_config["scale"] == {
            "records": 1_000_000,
            "threads": 48,
            "ycsb_zipf_skew": "0.9",
            "ycsb_rmw": "0",
            "ycsb_max_ope": "10",
            "extime_s": 3,
            "reps": expected_reps[workload],
            "expected_verify_configs": ["legacy"],
        }
        assert cfg.search_config["build_admission"] == json.loads(
            context.policy._preimage_json
        )


def _submit_cli_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    *, create_base: bool = True,
) -> tuple[Path, Path, str]:
    policy, policy_sha = paired.load_policy()
    repo = tmp_path / "submit-repo"
    for relative in paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS:
        source = repo / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"fixture source: {relative}\n", encoding="utf-8")
    base = (tmp_path / "measurement-submit").resolve()
    if create_base:
        base.mkdir()
    attempt = base / "attempt"
    head = "a" * 40
    monkeypatch.setattr(paired, "_repo_root", lambda: repo)
    monkeypatch.setattr(
        paired, "load_policy", lambda: (policy, policy_sha),
    )
    monkeypatch.setattr(paired, "_durable_measurement_base", lambda _policy: base)
    def run_git(_repo, *args):
        if args == ("rev-parse", "HEAD"):
            return head
        if len(args) == 2 and args[0] == "rev-parse" and ":" in args[1]:
            return "b" * 40
        if args == ("status", "--porcelain", "--untracked-files=all"):
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(paired, "_run_git", run_git)
    return repo, attempt, head


def _stub_successful_submit(
    monkeypatch: pytest.MonkeyPatch, calls: list[list[str]],
) -> None:
    def qsub(argv, *, cwd):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, "12345.nqsv\n", "")

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(
        paired,
        "_observe_qstat_visibility",
        lambda request_id: {
            "request_id": request_id,
            "visible": True,
            "state": "QUE",
            "queue": "gen_S",
            "observed_epoch": 2,
        },
    )


def test_m1_submission_receipt_is_complete_before_final_path_is_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: complete staged receipt bytes publish successfully.
    Rejection implication: direct final-path writing cannot satisfy the publish boundary.
    """
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    evidence = paired._attempt_evidence_paths(attempt)
    submission_path = Path(evidence["submission_receipt"])
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)
    real_link = paired.os.link
    publish_boundaries: list[tuple[Path, Path]] = []

    def inspect_publish(
        staging: Path,
        destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        if destination == submission_path:
            raw = staging.read_bytes()
            document = json.loads(raw)
            assert staging != destination
            assert not os.path.lexists(destination)
            assert raw == paired._canonical_json_bytes(document)
            assert set(document) == paired._SUBMISSION_RECEIPT_KEYS
            assert follow_symlinks is False
            publish_boundaries.append((staging, destination))
        real_link(staging, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(paired.os, "link", inspect_publish)
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    assert len(publish_boundaries) == 1
    assert len(qsub_calls) == 1
    assert json.loads(submission_path.read_bytes())["request_id"] == "12345.nqsv"
    assert not os.path.lexists(paired._receipt_staging_path(
        submission_path, receipt_kind="submission",
    ))


def test_m2_submission_receipt_publish_is_no_replace(
    tmp_path: Path,
) -> None:
    """Acceptance implication: an unused final path accepts one complete receipt.
    Rejection implication: an existing final path is never replaced by publication.
    """
    occupied = tmp_path / "occupied.submission.json"
    original = b"existing receipt\n"
    occupied.write_bytes(original)
    occupied_staging = paired._receipt_staging_path(
        occupied, receipt_kind="submission",
    )
    with pytest.raises(
        paired.PaperStoryError,
        match=r"^no-replace submission receipt publish failed: ",
    ):
        paired._publish_submission_receipt(occupied, {"value": "replacement"})
    assert occupied.read_bytes() == original
    assert not os.path.lexists(occupied_staging)

    clean = tmp_path / "clean.submission.json"
    clean_staging = paired._receipt_staging_path(
        clean, receipt_kind="submission",
    )
    paired._publish_submission_receipt(clean, {"value": "accepted"})
    assert clean.read_bytes() == paired._canonical_json_bytes({"value": "accepted"})
    assert not os.path.lexists(clean_staging)


def test_completion_receipt_publish_boundary_and_no_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Completion publishes only canonical staging bytes through a real hard link."""
    occupied = tmp_path / "occupied.completion.json"
    original = b"existing completion\n"
    occupied.write_bytes(original)
    occupied_staging = paired._receipt_staging_path(
        occupied, receipt_kind="completion",
    )
    with pytest.raises(paired.PaperStoryError):
        paired._publish_completion_receipt(
            occupied, {"value": "replacement"},
        )
    assert occupied.read_bytes() == original
    assert not os.path.lexists(occupied_staging)

    clean = tmp_path / "clean.completion.json"
    value = {"value": "accepted"}
    expected = paired._canonical_json_bytes(value)
    clean_staging = paired._receipt_staging_path(
        clean, receipt_kind="completion",
    )
    real_link = paired.os.link
    publish_boundaries: list[tuple[Path, Path]] = []

    def inspect_publish(
        staging: Path,
        destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert staging == clean_staging
        assert destination == clean
        assert staging.read_bytes() == expected
        assert not os.path.lexists(destination)
        assert follow_symlinks is False
        publish_boundaries.append((staging, destination))
        real_link(staging, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(paired.os, "link", inspect_publish)
    paired._publish_completion_receipt(clean, value)
    assert publish_boundaries == [(clean_staging, clean)]
    assert clean.read_bytes() == expected
    assert not os.path.lexists(clean_staging)


def test_m3_submit_rejects_existing_completion_before_intent_and_qsub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: a clean sibling attempt still submits successfully.
    Rejection implication: an existing completion receipt blocks intent and qsub.
    """
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    evidence = paired._attempt_evidence_paths(attempt)
    Path(evidence["completion_receipt"]).write_text("stale\n", encoding="utf-8")
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)
    with pytest.raises(paired.PaperStoryError, match="completion receipt already exists"):
        paired.run_submit(SimpleNamespace(
            study_id=paired.STUDY_ID,
            expected_head=head, attempt_root=str(attempt),
        ))
    assert not paired._attempt_intent_path(attempt).exists()
    assert qsub_calls == []

    clean = attempt.with_name("clean-completion-positive")
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(clean),
    )) == 0
    assert len(qsub_calls) == 1


def test_m4_submit_rejects_existing_stdout_before_intent_and_qsub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: a clean sibling attempt still submits successfully.
    Rejection implication: an existing stdout path blocks intent and qsub.
    """
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    evidence = paired._attempt_evidence_paths(attempt)
    Path(evidence["stdout_path"]).write_text("stale\n", encoding="utf-8")
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)
    with pytest.raises(paired.PaperStoryError, match="stdout already exists"):
        paired.run_submit(SimpleNamespace(
            study_id=paired.STUDY_ID,
            expected_head=head, attempt_root=str(attempt),
        ))
    assert not paired._attempt_intent_path(attempt).exists()
    assert qsub_calls == []

    clean = attempt.with_name("clean-stdout-positive")
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(clean),
    )) == 0
    assert len(qsub_calls) == 1


def test_m5_submit_rejects_existing_stderr_before_intent_and_qsub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: a clean sibling attempt still submits successfully.
    Rejection implication: an existing stderr path blocks intent and qsub.
    """
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    evidence = paired._attempt_evidence_paths(attempt)
    Path(evidence["stderr_path"]).write_text("stale\n", encoding="utf-8")
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)
    with pytest.raises(paired.PaperStoryError, match="stderr already exists"):
        paired.run_submit(SimpleNamespace(
            study_id=paired.STUDY_ID,
            expected_head=head, attempt_root=str(attempt),
        ))
    assert not paired._attempt_intent_path(attempt).exists()
    assert qsub_calls == []

    clean = attempt.with_name("clean-stderr-positive")
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(clean),
    )) == 0
    assert len(qsub_calls) == 1


def test_m6_submit_accepts_clean_evidence_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: a wholly unused evidence namespace submits once.
    Rejection implication: an unconditional freshness refusal fails this positive case.
    """
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    evidence = paired._attempt_evidence_paths(attempt)
    assert all(not os.path.lexists(path) for path in evidence.values())
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)

    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    assert len(qsub_calls) == 1
    assert paired._attempt_intent_path(attempt).is_file()
    assert Path(evidence["submission_receipt"]).is_file()


def test_m7_submit_creates_missing_durable_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: submit creates a missing durable base before intent.
    Rejection implication: omitting base creation prevents the first valid submit.
    Positive example: a clean attempt below an absent base submits once.
    """
    _repo, attempt, head = _submit_cli_fixture(
        tmp_path, monkeypatch, create_base=False,
    )
    assert not attempt.parent.exists()
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)

    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    assert attempt.parent.is_dir()
    assert not attempt.exists()
    assert paired._attempt_intent_path(attempt).is_file()
    assert Path(
        paired._attempt_evidence_paths(attempt)["submission_receipt"]
    ).is_file()
    assert len(qsub_calls) == 1


@pytest.mark.parametrize(
    "link_failure",
    [
        FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST)),
        OSError(errno.EIO, os.strerror(errno.EIO)),
    ],
    ids=("file-exists", "other-oserror"),
)
def test_submission_receipt_link_failure_removes_owned_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    link_failure: OSError,
) -> None:
    """Acceptance implication: cleanup leaves the namespace reusable after failure.
    Rejection implication: both link failure paths must remove their owned staging file.
    Positive example: a later clean destination publishes after the failed attempt.
    """
    destination = tmp_path / "failed.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )

    def fail_link(
        _staging: Path,
        _destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert follow_symlinks is False
        raise link_failure

    with monkeypatch.context() as patch:
        patch.setattr(paired.os, "link", fail_link)
        with pytest.raises(paired.PaperStoryError):
            paired._publish_submission_receipt(destination, {"value": "failed"})
    assert not os.path.lexists(staging)
    assert not os.path.lexists(destination)

    clean = tmp_path / "clean-after-failure.submission.json"
    paired._publish_submission_receipt(clean, {"value": "accepted"})
    assert clean.read_bytes() == paired._canonical_json_bytes(
        {"value": "accepted"}
    )


def test_submission_receipt_cleanup_preserves_replaced_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: owned staging cleanup remains available after failure.
    Rejection implication: cleanup must not unlink a different inode at the staging path.
    Positive example: an unrelated clean destination still publishes normally.
    """
    destination = tmp_path / "replaced.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )
    replacement = tmp_path / "foreign-staging"
    replacement.write_bytes(b"foreign staging\n")

    def replace_then_fail(
        active_staging: Path,
        _destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert follow_symlinks is False
        active_staging.unlink()
        replacement.rename(active_staging)
        raise OSError(errno.EIO, os.strerror(errno.EIO))

    with monkeypatch.context() as patch:
        patch.setattr(paired.os, "link", replace_then_fail)
        with pytest.raises(
            paired.PaperStoryError, match="staging cleanup identity differs",
        ):
            paired._publish_submission_receipt(destination, {"value": "failed"})
    assert staging.read_bytes() == b"foreign staging\n"

    clean = tmp_path / "clean-after-replacement.submission.json"
    paired._publish_submission_receipt(clean, {"value": "accepted"})
    assert clean.is_file()


def test_published_receipt_cleanup_preserves_same_inode_after_destination_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cleanup fails closed if the published link moves back over staging.

    Acceptance implication: the same publisher succeeds without the injected move.
    Rejection implication: the move is injected after exactly one real hard link,
    and cleanup preserves the only remaining name instead of repairing publication.
    """
    destination = tmp_path / "moved.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )
    value = {"value": "published"}
    expected = paired._canonical_json_bytes(value)
    real_link = paired.os.link
    link_calls: list[tuple[Path, Path]] = []

    def link_then_move_destination(
        active_staging: Path,
        active_destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert follow_symlinks is False
        link_calls.append((active_staging, active_destination))
        real_link(
            active_staging,
            active_destination,
            follow_symlinks=follow_symlinks,
        )
        active_staging.unlink()
        active_destination.rename(active_staging)

    with monkeypatch.context() as patch:
        patch.setattr(paired.os, "link", link_then_move_destination)
        with pytest.raises(paired._PublishedReceiptCleanupError):
            paired._publish_submission_receipt(destination, value)

    assert link_calls == [(staging, destination)]
    assert staging.read_bytes() == expected
    assert not os.path.lexists(destination)

    clean = tmp_path / "clean-after-move.submission.json"
    clean_staging = paired._receipt_staging_path(
        clean, receipt_kind="submission",
    )
    paired._publish_submission_receipt(clean, value)
    assert clean.read_bytes() == expected
    assert not os.path.lexists(clean_staging)


def test_published_receipt_cleanup_preserves_staging_when_destination_disappears(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing published destination alone blocks owned staging cleanup."""
    destination = tmp_path / "missing-destination.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )
    value = {"value": "published"}
    expected = paired._canonical_json_bytes(value)
    real_link = paired.os.link
    link_calls: list[tuple[Path, Path]] = []

    def link_then_remove_destination(
        active_staging: Path,
        active_destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert follow_symlinks is False
        link_calls.append((active_staging, active_destination))
        real_link(
            active_staging,
            active_destination,
            follow_symlinks=follow_symlinks,
        )
        active_destination.unlink()

    monkeypatch.setattr(paired.os, "link", link_then_remove_destination)
    with pytest.raises(paired._PublishedReceiptCleanupError):
        paired._publish_submission_receipt(destination, value)

    assert link_calls == [(staging, destination)]
    assert staging.read_bytes() == expected
    assert not os.path.lexists(destination)


def test_published_receipt_cleanup_requires_destination_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Published cleanup preserves staging when the destination inode changes."""
    destination = tmp_path / "foreign-destination.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )
    value = {"value": "published"}
    expected = paired._canonical_json_bytes(value)
    foreign = b"foreign destination\n"
    real_link = paired.os.link

    def link_then_replace_destination(
        active_staging: Path,
        active_destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        real_link(
            active_staging,
            active_destination,
            follow_symlinks=follow_symlinks,
        )
        active_destination.unlink()
        active_destination.write_bytes(foreign)

    monkeypatch.setattr(paired.os, "link", link_then_replace_destination)
    with pytest.raises(paired.PaperStoryError):
        paired._publish_submission_receipt(destination, value)

    assert staging.read_bytes() == expected
    assert destination.read_bytes() == foreign


def test_receipt_publish_orders_link_fsync_unlink_fsync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The final link is durable before staging is removed and made durable."""
    destination = tmp_path / "ordered.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )
    events: list[tuple[str, Path, Path | None]] = []
    real_link = paired.os.link
    real_unlink = paired.os.unlink

    def observe_link(
        source: Path,
        target: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        events.append(("link", source, target))
        real_link(source, target, follow_symlinks=follow_symlinks)

    def observe_fsync(directory: Path) -> None:
        events.append(("fsync", directory, None))

    def observe_unlink(path: Path) -> None:
        events.append(("unlink", path, None))
        real_unlink(path)

    monkeypatch.setattr(paired.os, "link", observe_link)
    monkeypatch.setattr(paired.os, "unlink", observe_unlink)
    monkeypatch.setattr(paired, "_fsync_directory", observe_fsync)
    paired._publish_submission_receipt(destination, {"value": "ordered"})

    assert events == [
        ("link", staging, destination),
        ("fsync", destination.parent, None),
        ("unlink", staging, None),
        ("fsync", destination.parent, None),
    ]


def test_submit_rejects_foreign_staging_before_intent_and_qsub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: removing a foreign staging collision permits submit.
    Rejection implication: an existing unowned staging path blocks intent and qsub.
    Positive example: the same clean attempt submits once after the collision is removed.
    """
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    evidence = paired._attempt_evidence_paths(attempt)
    staging = paired._receipt_staging_path(
        Path(evidence["submission_receipt"]),
        receipt_kind="submission",
    )
    staging.write_bytes(b"foreign staging\n")
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)

    with pytest.raises(
        paired.PaperStoryError, match="submission receipt staging already exists",
    ):
        paired.run_submit(SimpleNamespace(
            study_id=paired.STUDY_ID,
            expected_head=head, attempt_root=str(attempt),
        ))
    assert not paired._attempt_intent_path(attempt).exists()
    assert qsub_calls == []

    staging.unlink()
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    assert len(qsub_calls) == 1


def test_submit_accepts_clean_evidence_and_staging_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: unused evidence and staging paths permit one submit.
    Rejection implication: a blanket staging refusal would reject this clean namespace.
    Positive example: the clean attempt creates intent and a final receipt once.
    """
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    evidence = paired._attempt_evidence_paths(attempt)
    staging = paired._receipt_staging_path(
        Path(evidence["submission_receipt"]),
        receipt_kind="submission",
    )
    assert all(not os.path.lexists(path) for path in evidence.values())
    assert not os.path.lexists(staging)
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)

    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    assert len(qsub_calls) == 1
    assert paired._attempt_intent_path(attempt).is_file()
    assert Path(evidence["submission_receipt"]).is_file()
    assert not os.path.lexists(staging)


def test_submit_accepts_name_max_submission_basename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance implication: a valid NAME_MAX final receipt name remains submittable.
    Rejection implication: staging suffix growth must not reject that valid final name.
    Positive example: an ASCII attempt at the final-name boundary submits once.
    """
    _repo, seed_attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    final_suffix = ".submission.json"
    name_max = os.pathconf(seed_attempt.parent, "PC_NAME_MAX")
    attempt = seed_attempt.with_name("a" * (name_max - len(final_suffix)))
    evidence = paired._attempt_evidence_paths(attempt)
    submission = Path(evidence["submission_receipt"])
    staging = paired._receipt_staging_path(
        submission, receipt_kind="submission",
    )
    assert len(os.fsencode(submission.name)) == name_max
    assert len(os.fsencode(staging.name)) <= name_max
    qsub_calls: list[list[str]] = []
    _stub_successful_submit(monkeypatch, qsub_calls)

    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    assert len(qsub_calls) == 1
    assert submission.is_file()
    assert not os.path.lexists(staging)


def test_submit_create_only_intent_precedes_qsub_and_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    observed = []

    def qsub(argv, *, cwd):
        observed.append(("qsub", list(argv)))
        assert cwd == repo.resolve()
        assert paired._attempt_intent_path(attempt).is_file()
        return subprocess.CompletedProcess(argv, 0, "12345.nqsv\n", "")

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(
        paired,
        "_observe_qstat_visibility",
        lambda request_id: {
            "request_id": request_id,
            "visible": True,
            "state": "QUE",
            "queue": "gen_S",
            "observed_epoch": 2,
        },
    )
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    intent = json.loads(paired._attempt_intent_path(attempt).read_bytes())
    receipt_path = Path(paired._attempt_evidence_paths(attempt)["submission_receipt"])
    receipt = json.loads(receipt_path.read_bytes())
    assert observed and observed[0][0] == "qsub"
    assert intent["schema_version"] == paired.SUBMISSION_INTENT_SCHEMA
    assert receipt["schema_version"] == paired.SUBMISSION_SCHEMA
    assert set(receipt) == paired._SUBMISSION_RECEIPT_KEYS
    assert receipt["qsub_argv"] == intent["qsub_argv"]
    assert receipt["qsub_options"] == intent["qsub_options"]
    assert receipt["qsub_argv"][-1] == str((repo / paired.JOB_RELATIVE_PATH).resolve())
    assert set(intent) == {
        "schema_version", "study_id", "source_commit", "attempt_root",
        "qsub_argv", "qsub_options", "source_binding", "intent_sha256",
    }
    assert "created_epoch" not in intent


def test_submit_runs_real_qsub_call_from_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    outside = tmp_path / "outside-caller"
    outside.mkdir()
    monkeypatch.chdir(outside)
    calls = []

    def run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs), Path.cwd()))
        if argv[0] == "qsub":
            return subprocess.CompletedProcess(argv, 0, "980043.nqsv\n", "")
        assert argv[:2] == ["qstat", "-f"]
        return subprocess.CompletedProcess(
            argv,
            0,
            _qstat_fixture("qstat-f-980043.nqsv.txt"),
            "",
        )

    monkeypatch.setattr(paired.subprocess, "run", run)
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.STUDY_ID,
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    qsub_call = next(item for item in calls if item[0][0] == "qsub")
    assert qsub_call[1]["cwd"] == repo.resolve()
    assert qsub_call[2] == outside
    receipt = json.loads(Path(
        paired._attempt_evidence_paths(attempt)["submission_receipt"]
    ).read_bytes())
    assert set(receipt) == paired._SUBMISSION_RECEIPT_KEYS
    assert len(receipt) == 11


def test_m_nc09_intent_without_submission_never_repeats_qsub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    argv, options = paired._canonical_qsub_contract(
        repo_root=repo.resolve(),
        study_id=paired.STUDY_ID,
        source_commit=head,
        attempt=attempt,
    )
    intent = {
        "schema_version": paired.SUBMISSION_INTENT_SCHEMA,
        "study_id": paired.STUDY_ID,
        "source_commit": head,
        "attempt_root": str(attempt),
        "qsub_argv": argv,
        "qsub_options": options,
        "source_binding": paired._non_certifying_source_binding(repo, head),
    }
    intent["intent_sha256"] = paired._submission_intent_digest(intent)
    paired._exclusive_write(paired._attempt_intent_path(attempt), intent)
    attempt.mkdir()
    calls = []
    monkeypatch.setattr(
        paired, "_run_qsub", lambda _argv, *, cwd: calls.append((_argv, cwd)),
    )
    with pytest.raises(paired.PaperStoryError, match="indeterminate"):
        paired.run_submit(SimpleNamespace(
            study_id=paired.STUDY_ID,
            expected_head=head, attempt_root=str(attempt),
        ))
    assert calls == []
    assert not Path(
        paired._attempt_evidence_paths(attempt)["submission_receipt"]
    ).exists()


def test_m_nc01_submit_rejects_marker_drift_before_intent_and_qsub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        paired,
        "_a1_noncertifying_marker_fields",
        lambda: {
            "formal": False,
            "promotion_prohibited": False,
            "non_certifying_mode": "registered-formal-non-certifying",
        },
    )
    qsub_calls = []
    monkeypatch.setattr(
        paired, "_run_qsub", lambda argv, *, cwd: qsub_calls.append((argv, cwd)),
    )
    with pytest.raises(paired.PaperStoryError, match="marker differs before submit"):
        paired.run_submit(SimpleNamespace(
            study_id=paired.STUDY_ID,
            expected_head=head, attempt_root=str(attempt),
        ))
    assert qsub_calls == []
    assert not paired._attempt_intent_path(attempt).exists()


def test_complete_only_issues_completion_receipt_without_materialize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, attempt, head = _submit_cli_fixture(tmp_path, monkeypatch)
    attempt.mkdir()
    argv, options = paired._canonical_qsub_contract(
        repo_root=repo.resolve(), study_id=paired.STUDY_ID,
        source_commit=head, attempt=attempt,
    )
    intent = {
        "schema_version": paired.SUBMISSION_INTENT_SCHEMA,
        "study_id": paired.STUDY_ID,
        "source_commit": head,
        "attempt_root": str(attempt),
        "qsub_argv": argv,
        "qsub_options": options,
        "source_binding": paired._non_certifying_source_binding(repo, head),
    }
    intent["intent_sha256"] = paired._submission_intent_digest(intent)
    paired._exclusive_write(paired._attempt_intent_path(attempt), intent)
    evidence = paired._attempt_evidence_paths(attempt)
    submission = _acquisition(attempt, repo)
    Path(evidence["submission_receipt"]).write_bytes(
        paired._canonical_json_bytes(submission)
    )
    Path(evidence["stdout_path"]).write_bytes(b"stdout\n")
    Path(evidence["stderr_path"]).write_bytes(b"")
    terminal = attempt / "raw" / "job-terminal.json"
    terminal.parent.mkdir()
    terminal.write_bytes(b"{}\n")
    monkeypatch.setattr(
        paired,
        "_observe_scheduler_terminal",
        lambda *_args: {
            "terminal_reason": "scheduler-end-state",
            "qstat_visible": True,
            "qstat_rc": 0,
            "state": {"observed": True, "value": "F"},
            "exit_status": {"observed": True, "value": 0},
            "observed_epoch": 2,
            "qstat_stdout": "Request ID: 12345.nqsv\n",
            "qstat_stdout_sha256": hashlib.sha256(
                b"Request ID: 12345.nqsv\n"
            ).hexdigest(),
        },
    )
    monkeypatch.setattr(
        paired, "run_materialize",
        lambda _args: pytest.fail("complete called materialize"),
    )
    validated_sidecars = []
    monkeypatch.setattr(
        paired,
        "_validate_raw_non_certifying_observation_for_completion",
        lambda path, **kwargs: validated_sidecars.append((path, kwargs)),
    )
    completion_path = Path(evidence["completion_receipt"])
    completion_staging = paired._receipt_staging_path(
        completion_path, receipt_kind="completion",
    )
    real_link = paired.os.link
    publish_boundaries: list[tuple[Path, Path]] = []

    def inspect_completion_publish(
        staging: Path,
        destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        if destination == completion_path:
            raw = staging.read_bytes()
            document = json.loads(raw)
            assert staging == completion_staging
            assert not os.path.lexists(destination)
            assert raw == paired._canonical_json_bytes(document)
            assert document["schema_version"] == paired.COMPLETION_SCHEMA
            assert follow_symlinks is False
            publish_boundaries.append((staging, destination))
        real_link(staging, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(paired.os, "link", inspect_completion_publish)
    assert paired.run_complete(SimpleNamespace(
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    assert publish_boundaries == [(completion_staging, completion_path)]
    assert not os.path.lexists(completion_staging)
    completion = json.loads(completion_path.read_bytes())
    assert completion["schema_version"] == paired.COMPLETION_SCHEMA
    assert "materialization" not in completion
    assert validated_sidecars == [(
        attempt / "raw" / "results" / paired.NON_CERTIFYING_OBSERVATION_FILENAME,
        {
            "expected_head": head,
            "attempt": attempt,
            "request_id": submission["request_id"],
        },
    )]


def _v3_submit_cli_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    *, study_id: str = paired.V3_PILOT_STUDY_ID, attempt_name: str = "attempt-0004",
) -> tuple[Path, Path, str, dict]:
    policy, policy_sha = paired.load_policy(study_id)
    repo = tmp_path / "v3-submit-repo"
    for relative in paired.V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS:
        active = (
            paired._policy_relative_path(policy)
            if relative == paired.POLICY_RELATIVE_PATH else relative
        )
        source = repo / active
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"fixture source: {active}\n", encoding="utf-8")
    base = (tmp_path / "v3-measurement").resolve()
    base.mkdir()
    for relative in (*paired.a1_source.CONTRACTS[study_id][2],
                     paired._policy_relative_path(policy),
                     policy["preregistration"]["path"],
                     *(item["path"] for item in policy.get("sizing_inputs", {}).values())):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    (repo / "hydrated").mkdir()
    attempt = base / attempt_name
    head = "a" * 40
    monkeypatch.setattr(paired, "_repo_root", lambda: repo)
    monkeypatch.setattr(
        paired, "_load_policy_for_study", lambda _study_id: (policy, policy_sha),
    )
    monkeypatch.setattr(
        paired, "_require_policy_ready_for_execution", lambda _policy: None,
    )
    monkeypatch.setattr(
        paired, "_assert_ccbench_acceptance", lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(paired, "_durable_measurement_base", lambda _policy: base)

    def run_git(_repo, *args):
        if args == ("rev-parse", "HEAD"):
            return head
        if len(args) == 2 and args[0] == "rev-parse" and ":" in args[1]:
            return "b" * 40
        if args[-2:] == ("--porcelain", "--untracked-files=all"):
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(paired, "_run_git", run_git)
    monkeypatch.setattr(paired.socket, "gethostname", lambda: "submit.example")
    return repo, attempt, head, policy


def test_sized_source_closures_match_job_and_driver(monkeypatch):
    script = JOB.read_text()
    shell = script[script.index("NON_CERTIFYING_SOURCE_RELATIVE_PATHS=("):
                   script.index('[[ -n "${PBS_JOBID:-}" ]]')]
    first_start = script.index("source_paths = (")
    first = script[first_start:script.index("files = {}", first_start)]
    last_start = script.index("source_paths = [")
    last = script[last_start:script.index("driver_rc = int", last_start)]
    for study, policy_path, extras in (
        (paired.a1_source.PILOT_STUDY_ID, paired.V3_PILOT_POLICY_RELATIVE_PATH, (
            "orchestrator/campaign/paper_story_a1_source.v1.json",
            "orchestrator/campaign/paper_story_a1_source.py",
            "patches/silo-backoff-fixed.patch",
            "output/insights/2026-09-11/t2397-a1-source-amendment/README.md")),
        (paired.a1_source.SIZED_STUDY_ID, paired.V3_SIZED_POLICY_RELATIVE_PATH, (
            "orchestrator/campaign/paper_story_a1_source.v2.json",
            "orchestrator/campaign/paper_story_a1_source.py",
            "patches/silo-backoff-fixed.patch",
            "output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md")),
    ):
        policy = paired.load_policy(study)[0]
        for relative in extras:
            assert script.count(f'"{relative}"') == 3
        expected = (
            "orchestrator/campaign/paper_story_a1_paired.py", policy_path,
            "orchestrator/campaign/pipeline.py", "tools/pegasus/paper_story_a1_paired.sh",
            "orchestrator/calibrator/runner.py", *extras,
        )
        expected_noncert = (
            *expected[:4], "orchestrator/campaign/campaign_lock.py",
            "orchestrator/campaign/ident.py", "orchestrator/campaign/wal.py",
            "orchestrator/campaign/loop.py", "orchestrator/campaign/trial_registry.py",
            expected[4], *extras,
        )
        assert paired._source_relative_paths(policy, non_certifying=False) == expected
        assert paired._source_relative_paths(policy, non_certifying=True) == expected_noncert
        result = subprocess.run(
            ["bash", "-c", shell + '\nprintf "%s\\n" "${NON_CERTIFYING_SOURCE_RELATIVE_PATHS[@]}"'],
            env={**os.environ, "V3_STUDY": "1", "POLICY_RELATIVE": policy_path},
            text=True, capture_output=True, check=True,
        )
        assert tuple(result.stdout.splitlines()) == expected_noncert
        namespace = {"policy_relative": policy_path}
        exec(first, namespace)
        assert tuple(namespace["source_paths"]) == expected
        for key, value in zip(("DRIVER", "POLICY", "PIPELINE", "JOB", "RUNNER"), expected[:5]):
            monkeypatch.setenv("IZANAGI_A1_TERMINAL_" + key + "_RELATIVE", value)
        namespace = {"os": os, "v3_study": True}
        exec(last, namespace)
        assert tuple(namespace["source_paths"]) == expected


def test_sized_submit_requires_hydrate_and_preserves_attempt_names(tmp_path, monkeypatch):
    study = paired.a1_source.SIZED_STUDY_ID
    for index, supply in enumerate(("ok", "ok", None, "missing", "file")):
        with monkeypatch.context() as mp:
            repo, attempt, head, policy = _v3_submit_cli_fixture(
                tmp_path / str(index), mp, study_id=study,
                attempt_name=f"attempt-{index + 1:04d}")
            calls = []
            def qsub(argv, *, cwd):
                calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, f"{122 + len(calls)}.server\n", "")
            mp.setattr(paired, "_run_qsub", qsub)
            mp.setattr(paired, "_observe_qstat_visibility", _v3_visibility)
            supplied = repo / "hydrated"
            if supply in ("missing", "file"):
                supplied = repo / supply
                if supply == "file":
                    supplied.write_text("not a directory")
            args = SimpleNamespace(study_id=study, expected_head=head, attempt_root=str(attempt),
                                   third_party_source_root=None if supply is None else str(supplied))
            if supply == "ok":
                assert paired.run_submit(args) == 0
                assert len(calls) == 3
            else:
                with pytest.raises(paired.PaperStoryError, match="hydrated third-party source root is unavailable"):
                    paired.run_submit(args)
                assert calls == []
                assert not paired._attempt_intent_path(attempt).exists()


def _v3_rerun_submit_evidence(attempt, *, record_source=None):
    # Share data builders only; reader, gate, intent and destination stay real.
    from orchestrator.tests.test_paper_story_a1_paired import (
        _rerun_prior_barrier_fixture, _rerun_record, _rerun_save,
    )
    _rerun_prior_barrier_fixture(attempt.parent)
    if record_source is not None:
        _rerun_save(attempt, _rerun_record(attempt, source=record_source))


def test_v3_submit_reaches_qsub_with_exact_rerun_authorization(tmp_path, monkeypatch):
    """受理: 一致 record で実 gate と intent を経て qsub に三回届く。拒否: 再使用は許さない。"""
    repo, attempt, head, policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch, study_id=paired.V3_SIZED_STUDY_ID,
        attempt_name="attempt-0002",
    )
    _v3_rerun_submit_evidence(attempt, record_source=head)
    calls = []

    def qsub(argv, *, cwd):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, f"{122 + len(calls)}.server\n", "")

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(paired, "_observe_qstat_visibility", _v3_visibility)
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.V3_SIZED_STUDY_ID, expected_head=head,
        attempt_root=str(attempt), third_party_source_root=str(repo / "hydrated"),
    )) == 0
    assert len(calls) == 3
    assert paired._attempt_intent_path(attempt).is_file()


@pytest.mark.parametrize("kind,message", [
    ("absent", "group rerun is prohibited"),
    ("source", "rerun authorization record differs: source_commit"),
    ("intent", "intent exists without group receipt"),
    ("attempt", "submit attempt root must not already exist"),
])
def test_v3_submit_refuses_rerun_without_or_with_mismatched_authorization(
    tmp_path, monkeypatch, kind, message,
):
    """受理: 一致 record と新規 namespace は qsub に進む。拒否: 不一致や再使用では intent を作らない。"""
    repo, attempt, head, policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch, study_id=paired.V3_SIZED_STUDY_ID,
        attempt_name="attempt-0002",
    )
    source = None if kind == "absent" else ("b" * 40 if kind == "source" else head)
    _v3_rerun_submit_evidence(attempt, record_source=source)
    intent = paired._attempt_intent_path(attempt)
    if kind == "intent":
        intent.write_bytes(b"preserve existing intent")
    elif kind == "attempt":
        attempt.mkdir()
    calls = []
    def qsub(argv, *, cwd):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, f"{122 + len(calls)}.server\n", "")

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(paired, "_observe_qstat_visibility", _v3_visibility)
    with pytest.raises(paired.PaperStoryError, match=message):
        paired.run_submit(SimpleNamespace(
            study_id=paired.V3_SIZED_STUDY_ID, expected_head=head,
            attempt_root=str(attempt), third_party_source_root=str(repo / "hydrated"),
        ))
    assert calls == []
    if kind == "intent":
        assert intent.read_bytes() == b"preserve existing intent"
    else:
        assert not intent.exists()


def test_sized_group_intent_requires_hydrate(tmp_path, monkeypatch):
    repo, attempt, head, policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch, study_id=paired.a1_source.SIZED_STUDY_ID,
        attempt_name="attempt-0001")
    kwargs = dict(repo_root=repo, policy=policy, source_commit=head, attempt=attempt)
    with pytest.raises(paired.PaperStoryError, match="requires hydrated"):
        paired._v3_group_intent(**kwargs)
    supplied = str(repo / "hydrated")
    intent = paired._v3_group_intent(**kwargs, third_party_source_root=supplied)
    assert len(intent["jobs"]) == 3
    assert all(job["qsub_options"]["variables"]["IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT"] == supplied
               for job in intent["jobs"])
    attempt.mkdir()
    paired._attempt_intent_path(attempt).write_text(json.dumps(intent))
    assert paired._v3_group_intent(**kwargs) == intent


def test_sized_job_stages_hydrate_for_measurement(tmp_path):
    script = JOB.read_text()
    start = script.index("THIRD_PARTY_ARGS=()")
    body = script[start:script.index("\nset +e", start)]
    hydrated, dependency = tmp_path / "hydrated", tmp_path / "dependencies"
    dependency.mkdir()
    for name in ("masstree", "mimalloc", "googletest"):
        directory = hydrated / name
        directory.mkdir(parents=True)
        (directory / "marker").write_text(name)
    result = subprocess.run(["bash", "-eu", "-c",
        'refuse() { echo "$1" >&2; exit 1; }\n' + body +
        '\nprintf "%s\\n" "${THIRD_PARTY_ARGS[@]}"'],
        env={**os.environ, "POLICY_RELATIVE": paired.V3_SIZED_POLICY_RELATIVE_PATH,
             "DEPENDENCY_ROOT": str(dependency), "IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT": str(hydrated)},
        text=True, capture_output=True, check=True)
    assert result.stdout.splitlines() == ["--third-party-source-root", str(dependency / "fetchcontent")]
    for name in ("masstree", "mimalloc", "googletest"):
        assert (dependency / "fetchcontent" / (name + "-src") / "marker").read_text() == name


def test_sized_ccbench_acceptance_rejects_dirty_source(tmp_path, monkeypatch):
    policy = paired.load_policy(paired.a1_source.SIZED_STUDY_ID)[0]
    for boundary in ("login-submit", "driver-measurement", "artifact-consumer"):
        for mode, error in (("clean", None), ("dirty", "tracked files are dirty"),
                            ("wrong", "canonical HEAD mismatch"), ("unresolved", "cannot resolve submodule HEAD")):
            calls = []
            def git(root, *args):
                calls.append((root, args))
                if root == tmp_path:
                    assert args == ("status", "--ignore-submodules=all", "--porcelain", "--untracked-files=all")
                    return ""
                assert root == tmp_path / "external/ccbench"
                if args == ("rev-parse", "HEAD"):
                    if mode == "unresolved":
                        raise paired.PaperStoryError("unresolved")
                    return "0" * 40 if mode == "wrong" else paired.CANONICAL_CCBENCH_OID
                assert args == ("status", "--porcelain", "--untracked-files=no")
                return " M tracked" if mode == "dirty" else ""
            monkeypatch.setattr(paired, "_run_git", git)
            assert paired._parent_porcelain(tmp_path, policy) == ""
            if error:
                with pytest.raises(paired.PaperStoryError, match=f"CCBench {boundary}: {error}"):
                    paired._assert_ccbench_acceptance(tmp_path, policy, boundary=boundary)
            else:
                paired._assert_ccbench_acceptance(tmp_path, policy, boundary=boundary)
                assert len(calls) == 3


def test_sized_source_context_reaches_trace_and_perf_validation(tmp_path, monkeypatch):
    from orchestrator.campaign import pipeline
    source = paired.a1_source
    observed = []
    monkeypatch.setattr(source.patchharness, "assert_pinned_clean", lambda *args: None)
    def produce(**kwargs):
        assert kwargs["configuration"] == "a1-balanced5-sized-v1"
        return "a" * 64
    monkeypatch.setattr(source.s8b_expected_materialization,
                        "produce_expected_materialization_sha256", produce)
    context = source.SourceContext(REPO_ROOT, tmp_path, tmp_path,
                                   study_id=source.SIZED_STUDY_ID)
    monkeypatch.setattr(source.patchharness, "_git",
                        lambda *args: SimpleNamespace(returncode=0, stdout=context.pin))
    monkeypatch.setattr(source.s8b_expected_materialization, "assert_expected_materialization",
                        lambda root, expected: observed.append((root, expected)))
    for kind in ("trace", "perf"):
        pipeline._require_canonical_build_source_state(str(tmp_path), context.pin,
            build_kind=kind, a1_source_context=context)
    assert observed == [(tmp_path, "a" * 64)] * 2
    for kind in ("trace", "perf"):
        with pytest.raises(RuntimeError, match="root or canonical pin differs"):
            pipeline._require_canonical_build_source_state(str(tmp_path), "0" * 40,
                build_kind=kind, a1_source_context=context)


def _amended_measurement_fixture(tmp_path, monkeypatch, *, study_id, attempt_name):
    loader = paired._load_policy_for_study
    repo, attempt, head, policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch, study_id=study_id, attempt_name=attempt_name)
    monkeypatch.setattr(paired, "_load_policy_for_study", loader)
    policy, policy_sha = paired._load_policy_for_study(study_id)
    attempt.mkdir()
    hydrate = str(repo / "hydrated")
    intent = paired._v3_group_intent(repo_root=repo, policy=policy,
        source_commit=head, attempt=attempt, third_party_source_root=hydrate)
    paired._attempt_intent_path(attempt).write_text(json.dumps(intent))
    acquisition = dict(intent, jobs=[dict(job, request_id=f"{123 + i}.server")
                                    for i, job in enumerate(intent["jobs"])])
    receipt = attempt / "acquisition.json"
    receipt.write_text(json.dumps(acquisition))
    roots = {key: str(attempt / key) for key in
             ("output_root", "cache_root", "result_root", "raw_root")}
    roots.update(attempt_root=str(attempt), submission_receipt=str(receipt))
    scratch = tmp_path / "dependency-scratch"
    staged = scratch / "fetchcontent"
    staged.mkdir(parents=True)
    args = SimpleNamespace(workload=paired.WORKLOAD_ORDER[0], study_id=study_id,
        acquisition_receipt=str(receipt), acquisition_receipt_sha256=paired._sha256_file(receipt),
        expected_head=head, pbs_jobid="123.server", output_root=roots["output_root"],
        cache_root=roots["cache_root"], result_root=roots["result_root"],
        dependency_prefix=f"{scratch / 'gflags-install'};{scratch / 'glog-install'}",
        third_party_source_root=str(staged))
    # Scheduler, runtime admission and persistence are outside this route test.
    # Intent reconstruction, source hashes, policy and hydrate checks stay real.
    monkeypatch.setattr(paired, "validate_acquisition_receipt", lambda *a, **kw: roots)
    monkeypatch.setattr(paired, "validate_measure_environment", lambda **kw: roots)
    monkeypatch.setattr(paired, "_pbs_environment_observation", lambda: {})
    monkeypatch.setattr(paired.site_policy, "current_site", lambda: site_policy.PEGASUS_COMPUTE)
    monkeypatch.setattr(paired, "_under_scr", lambda path: True)
    monkeypatch.setattr(paired, "_reservation_binding_from_environment", lambda env: {
        "nonce": f"{attempt.name}.{args.workload}", "job_id": args.pbs_jobid})
    contract = paired.p2_2._legacy_linux_contract()
    monkeypatch.setattr(paired.p2_2, "resolve_site_runtime",
                        lambda: (site_policy.PEGASUS_COMPUTE, contract, None))
    monkeypatch.setattr(paired.p2_2, "_assert_matches_calibration", lambda c: None)
    monkeypatch.setattr(paired.p2_2, "_campaign_cfg_for_site", lambda cfg, *a: cfg)
    monkeypatch.setattr(paired, "_prepare_runtime_roots", lambda *a: None)
    monkeypatch.setattr(paired.buildcache, "compilers_for_current_site", lambda: ("cc", "c++"))
    monkeypatch.setattr(paired.buildcache, "observed_toolchain_manifest", lambda *a: {})
    monkeypatch.setattr(paired, "_preseed_v3_workload_lock",
                        lambda **kw: SimpleNamespace(root=attempt))
    monkeypatch.setattr(paired, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(paired, "collect_workload", lambda *a, **kw: {})
    monkeypatch.setattr(paired, "_workload_has_terminal_result", lambda result: True)
    monkeypatch.setattr(paired, "_revalidate_attempt_root", lambda roots: None)
    Path(roots["result_root"]).mkdir()
    context = SimpleNamespace(root=tmp_path / "amended-source")
    observed = {"materialized": [], "dependencies": [], "gate": [], "campaign": []}
    @contextmanager
    def materializer(root, *, study_id=paired.a1_source.PILOT_STUDY_ID):
        observed["materialized"].append((root, study_id))
        yield context, tmp_path / "stock"
    def dependencies(**kwargs):
        observed["dependencies"].append(kwargs)
        return {}
    def campaign(*args, **kwargs):
        observed["campaign"].append(kwargs)
        return SimpleNamespace(campaign_id="fixture", layout_root=attempt,
                               balanced_schedule_receipt=None)
    monkeypatch.setattr(paired.a1_source, "materialized", materializer)
    monkeypatch.setattr(paired.a1_source, "prepare_dependencies", dependencies)
    monkeypatch.setattr(paired, "_require_v3_backoff_fixed_condition_gate",
                        lambda **kw: observed["gate"].append(kw))
    monkeypatch.setattr(paired, "run_campaign", campaign)
    monkeypatch.setenv("IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT", hydrate)
    return args, dict(repo_root=repo, policy=policy, policy_sha=policy_sha), context, observed


def test_sized_measurement_routes_amended_source_and_hydrate(tmp_path, monkeypatch):
    study = paired.a1_source.SIZED_STUDY_ID
    for mode in ("ok", "env", "scratch"):
        with monkeypatch.context() as mp:
            args, kwargs, context, observed = _amended_measurement_fixture(
                tmp_path / mode, mp, study_id=study, attempt_name="attempt-0002")
            if mode == "env":
                mp.setenv("IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT", str(tmp_path / "other"))
            if mode == "scratch":
                args.third_party_source_root = str(kwargs["repo_root"] / "hydrated")
            if mode != "ok":
                message = ("third-party source origin differs from intent" if mode == "env"
                           else "third-party staged root differs from dependency scratch")
                with pytest.raises(paired.PaperStoryError, match=message):
                    paired._run_measurement_v3(args, **kwargs)
                assert observed == {key: [] for key in observed}
                continue
            assert paired._run_measurement_v3(args, **kwargs) == 0
            assert observed["materialized"] == [(kwargs["repo_root"], study)]
            assert len(observed["dependencies"]) == len(observed["gate"]) == len(observed["campaign"]) == 1
            assert observed["dependencies"][0]["root"] == Path(args.third_party_source_root)
            assert observed["dependencies"][0]["source"] == context.root
            assert observed["gate"][0]["source_root"] == context.root
            assert observed["campaign"][0]["ccbench_dir"] == str(context.root)
            assert observed["campaign"][0]["a1_source_context"] is context


def test_pilot_measurement_attempt_pin_remains_enforced(tmp_path, monkeypatch):
    args, kwargs, context, observed = _amended_measurement_fixture(
        tmp_path, monkeypatch, study_id=paired.V3_PILOT_STUDY_ID,
        attempt_name="attempt-0001")
    with pytest.raises(paired.PaperStoryError,
                       match="A1 source amendment requires pilot attempt-0004"):
        paired._run_measurement_v3(args, **kwargs)
    assert observed == {key: [] for key in observed}


def test_pilot_attempt_pin_remains_enforced(tmp_path, monkeypatch):
    repo, attempt, head, policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch, attempt_name="attempt-0001")
    def unexpected_qsub(*args, **kwargs):
        raise AssertionError("rejected pilot attempt reached qsub")
    monkeypatch.setattr(paired, "_run_qsub", unexpected_qsub)
    with pytest.raises(paired.PaperStoryError, match="new pilot submission requires source amendment attempt-0004"):
        paired.run_submit(SimpleNamespace(study_id=paired.V3_PILOT_STUDY_ID,
            expected_head=head, attempt_root=str(attempt), third_party_source_root=str(repo / "hydrated")))
    assert not paired._attempt_intent_path(attempt).exists()


def _v3_visibility(request_id: str) -> dict:
    return {
        "request_id": request_id,
        "visible": True,
        "state": "QUE",
        "queue": "gen_S",
        "observed_epoch": 2,
    }


def test_v3_complete_publishes_canonical_group_receipt_through_link_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """V3 completion reaches the create-only hard-link publication boundary."""
    _repo, attempt, head, _policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch,
    )
    evidence = paired._v3_attempt_evidence_paths(attempt)
    attempt.mkdir()
    (attempt / "receipts").mkdir()
    (attempt / "raw").mkdir()
    intent_sha = "1" * 64
    submission = {
        "intent_sha256": intent_sha,
        "jobs": [
            {
                "request_id": f"{123 + ordinal}.server",
                "submit_observation": {},
            }
            for ordinal, _workload in enumerate(paired.WORKLOAD_ORDER)
        ],
    }
    submission_raw = paired._canonical_json_bytes(submission)
    Path(evidence["submission_receipt"]).write_bytes(submission_raw)
    intent = {"intent_sha256": intent_sha}
    paired._attempt_intent_path(attempt).write_bytes(
        paired._canonical_json_bytes(intent)
    )

    campaign_ids = [f"campaign-{ordinal}" for ordinal in range(3)]
    common_record = {"fixture": "common"}
    source_binding = {"fixture": "source"}
    non_certifying_source_binding = {"fixture": "non-certifying-source"}
    terminal_by_workload = {}
    for ordinal, workload in enumerate(paired.WORKLOAD_ORDER):
        roots = paired._v3_job_roots(attempt, workload)
        Path(roots["scheduler_root"]).mkdir(parents=True)
        result_root = Path(roots["result_root"])
        result_root.mkdir(parents=True)
        result_path = result_root / "result.json"
        receipt_path = result_root / "receipt.json"
        terminal_path = Path(roots["job_terminal"])
        result_path.write_bytes(b"{}\n")
        receipt_path.write_bytes(b"{}\n")
        terminal_path.write_bytes(b"{}\n")
        Path(roots["stdout_path"]).write_bytes(
            f"{workload} stdout\n".encode()
        )
        Path(roots["stderr_path"]).write_bytes(b"")
        terminal_by_workload[workload] = {
            "reservation_binding": {"fixture": f"reservation-{ordinal}"},
            "accounting": {"fixture": f"accounting-{ordinal}"},
            "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        }

    monkeypatch.setattr(
        paired,
        "_validate_v3_group_submission",
        lambda *_args, **_kwargs: submission,
    )
    monkeypatch.setattr(
        paired,
        "_validate_submission_intent",
        lambda *_args, **_kwargs: intent,
    )

    def validate_workload_shard(
        _shard: object,
        _receipt: object,
        _terminal: object,
        **kwargs,
    ):
        workload = kwargs["workload"]
        return (
            {
                "common_record": common_record,
                "campaign_ids": campaign_ids,
                "source_binding": source_binding,
                "non_certifying_source_binding": (
                    non_certifying_source_binding
                ),
                "workload_result": {"workload": workload},
            },
            {},
            terminal_by_workload[workload],
        )

    monkeypatch.setattr(
        paired, "_validate_v3_workload_shard", validate_workload_shard,
    )
    monkeypatch.setattr(
        paired,
        "_observe_scheduler_terminal",
        lambda *_args, **_kwargs: {
            "terminal_reason": "scheduler-end-state",
            "exit_status": {"observed": True, "value": 0},
        },
    )
    monkeypatch.setattr(
        paired,
        "_validate_v3_barrier_for_completion",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        paired,
        "assemble_result",
        lambda *_args, **_kwargs: {
            "complete": True,
            "all_workloads_terminal": True,
        },
    )
    sidecar = Path(evidence["result_root"]) / "fixture-sidecar.json"
    monkeypatch.setattr(
        paired,
        "_issue_non_certifying_observation",
        lambda **_kwargs: sidecar,
    )
    monkeypatch.setattr(
        paired,
        "_validate_non_certifying_observation_contents",
        lambda path: {"sidecar_path": path},
    )

    completion_path = Path(evidence["completion_receipt"])
    completion_staging = paired._receipt_staging_path(
        completion_path, receipt_kind="completion",
    )
    real_link = paired.os.link
    publish_boundaries: list[tuple[Path, Path]] = []
    published_raw: list[bytes] = []

    def inspect_completion_publish(
        staging: Path,
        destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        raw = staging.read_bytes()
        document = json.loads(raw)
        assert staging == completion_staging
        assert destination == completion_path
        assert not os.path.lexists(destination)
        assert raw == paired._canonical_json_bytes(document)
        assert document["schema_version"] == paired.V3_GROUP_COMPLETION_SCHEMA
        assert [job["workload"] for job in document["jobs"]] == list(
            paired.WORKLOAD_ORDER
        )
        assert follow_symlinks is False
        publish_boundaries.append((staging, destination))
        published_raw.append(raw)
        real_link(staging, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(paired.os, "link", inspect_completion_publish)
    assert paired.run_complete(SimpleNamespace(
        study_id=paired.V3_PILOT_STUDY_ID,
        third_party_source_root=os.fspath(paired._repo_root() / "hydrated"),
        expected_head=head,
        attempt_root=os.fspath(attempt),
    )) == 0

    assert publish_boundaries == [(completion_staging, completion_path)]
    assert completion_path.read_bytes() == published_raw[0]
    assert not os.path.lexists(completion_staging)


def test_v3_submit_fans_out_exact_workload_triple_and_publishes_group_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repo, attempt, head, _policy = _v3_submit_cli_fixture(tmp_path, monkeypatch)
    calls = []

    def qsub(argv, *, cwd):
        ordinal = len(calls)
        calls.append(list(argv))
        return subprocess.CompletedProcess(
            argv, 0, f"{123 + ordinal}.server\n", "",
        )

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(paired, "_observe_qstat_visibility", _v3_visibility)
    assert paired.run_submit(SimpleNamespace(
        study_id=paired.V3_PILOT_STUDY_ID,
        third_party_source_root=os.fspath(paired._repo_root() / "hydrated"),
        expected_head=head,
        attempt_root=os.fspath(attempt),
    )) == 0
    assert len(calls) == 3
    receipt_path = Path(
        paired._v3_attempt_evidence_paths(attempt)["submission_receipt"]
    )
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt["schema_version"] == paired.V3_GROUP_SUBMISSION_SCHEMA
    assert [item["workload"] for item in receipt["jobs"]] == list(
        paired.WORKLOAD_ORDER
    )
    assert [
        item["qsub_options"]["variables"]["IZANAGI_A1_WORKLOAD"]
        for item in receipt["jobs"]
    ] == list(paired.WORKLOAD_ORDER)
    assert all(
        Path(paired._v3_job_roots(attempt, workload)["request_id_path"]).is_file()
        for workload in paired.WORKLOAD_ORDER
    )


def test_v3_published_cleanup_failure_does_not_write_failure_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A cleanup failure reports nonzero without publishing a false failure ledger."""
    _repo, attempt, head, _policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch,
    )
    qsub_calls: list[list[str]] = []

    def qsub(argv, *, cwd):
        ordinal = len(qsub_calls)
        qsub_calls.append(list(argv))
        return subprocess.CompletedProcess(
            argv, 0, f"{123 + ordinal}.server\n", "",
        )

    def refuse_cleanup(
        staging: Path,
        identity: tuple[int, int],
        *,
        destination: Path,
        published: bool,
    ) -> None:
        assert published is True
        assert (staging.stat().st_dev, staging.stat().st_ino) == identity
        assert (destination.stat().st_dev, destination.stat().st_ino) == identity
        raise paired.PaperStoryError(
            "receipt staging cleanup failed: injected",
        )

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(paired, "_observe_qstat_visibility", _v3_visibility)
    monkeypatch.setattr(paired, "_remove_receipt_staging", refuse_cleanup)
    with pytest.raises(paired._PublishedReceiptCleanupError) as raised:
        paired.run_submit(SimpleNamespace(
            study_id=paired.V3_PILOT_STUDY_ID,
            third_party_source_root=os.fspath(paired._repo_root() / "hydrated"),
            expected_head=head,
            attempt_root=os.fspath(attempt),
        ))

    evidence = paired._v3_attempt_evidence_paths(attempt)
    submission_path = Path(evidence["submission_receipt"])
    failure_path = Path(evidence["submission_failure"])
    staging_path = paired._receipt_staging_path(
        submission_path, receipt_kind="submission",
    )
    submission_raw = submission_path.read_bytes()
    submission = json.loads(submission_raw)
    assert "already published" in str(raised.value)
    assert len(qsub_calls) == 3
    assert submission["schema_version"] == paired.V3_GROUP_SUBMISSION_SCHEMA
    assert submission_raw == paired._canonical_json_bytes(submission)
    assert staging_path.read_bytes() == submission_raw
    assert not failure_path.exists()


def test_v3_submit_second_qsub_failure_stops_third_and_retry_before_qsub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repo, attempt, head, _policy = _v3_submit_cli_fixture(tmp_path, monkeypatch)
    calls = []

    def qsub(argv, *, cwd):
        ordinal = len(calls)
        calls.append(list(argv))
        if ordinal == 1:
            return subprocess.CompletedProcess(argv, 1, "", "scheduler failed\n")
        return subprocess.CompletedProcess(argv, 0, "123.server\n", "")

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(paired, "_observe_qstat_visibility", _v3_visibility)
    args = SimpleNamespace(
        study_id=paired.V3_PILOT_STUDY_ID,
        third_party_source_root=os.fspath(paired._repo_root() / "hydrated"),
        expected_head=head,
        attempt_root=os.fspath(attempt),
    )
    with pytest.raises(paired.PaperStoryError, match="group submission failed"):
        paired.run_submit(args)
    assert len(calls) == 2
    evidence = paired._v3_attempt_evidence_paths(attempt)
    assert not Path(evidence["submission_receipt"]).exists()
    failure = json.loads(Path(evidence["submission_failure"]).read_bytes())
    assert [item["status"] for item in failure["jobs"]] == [
        "accepted", "failed", "not-attempted",
    ]
    with pytest.raises(paired.PaperStoryError, match="intent exists"):
        paired.run_submit(args)
    assert len(calls) == 2


def test_v3_submit_rejects_normalized_request_alias_before_group_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repo, attempt, head, _policy = _v3_submit_cli_fixture(tmp_path, monkeypatch)
    outputs = iter(("123.server\n", "0:123.server\n"))
    calls = []

    def qsub(argv, *, cwd):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, next(outputs), "")

    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(paired, "_observe_qstat_visibility", _v3_visibility)
    with pytest.raises(paired.PaperStoryError, match="normalized request IDs"):
        paired.run_submit(SimpleNamespace(
            study_id=paired.V3_PILOT_STUDY_ID,
            third_party_source_root=os.fspath(paired._repo_root() / "hydrated"),
            expected_head=head,
            attempt_root=os.fspath(attempt),
        ))
    assert len(calls) == 2
    assert not Path(
        paired._v3_attempt_evidence_paths(attempt)["submission_receipt"]
    ).exists()


def test_v3_submit_rejects_prior_same_study_bench_start_before_intent_M4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repo, attempt, head, _policy = _v3_submit_cli_fixture(tmp_path, monkeypatch)
    prior = attempt.parent / "prior-attempt"
    start_root = prior / "barrier" / "bench-start"
    start_root.mkdir(parents=True)
    paired._exclusive_write(start_root / "write-heavy.json", {
        "schema_version": paired.V3_BENCH_START_SCHEMA,
        "study_id": paired.V3_PILOT_STUDY_ID,
        "source_commit": "f" * 40,
        "attempt_root": os.fspath(prior),
        "workload": "write-heavy",
        "ordinal": 0,
        "request_id": "100.server",
        "bench_go_sha256": "1" * 64,
        "ready_sha256": "2" * 64,
        "recorded_epoch": 1,
    })
    qsub_calls = []
    monkeypatch.setattr(
        paired, "_run_qsub",
        lambda argv, *, cwd: qsub_calls.append((argv, cwd)),
    )
    with pytest.raises(paired.PaperStoryError, match="group rerun is prohibited"):
        paired.run_submit(SimpleNamespace(
            study_id=paired.V3_PILOT_STUDY_ID,
            third_party_source_root=os.fspath(paired._repo_root() / "hydrated"),
            expected_head=head,
            attempt_root=os.fspath(attempt),
        ))
    assert qsub_calls == []
    assert not paired._attempt_intent_path(attempt).exists()


def test_v3_job_body_accounting_window_and_descendant_gate_are_literal() -> None:
    source = JOB.read_text(encoding="utf-8")
    required = (
        'ACCOUNTING_STARTED_EPOCH_S=$(date +%s.%N)',
        'LC_ALL=C times >"$ACCOUNTING_TIMES_BASELINE_PATH" 2>&1',
        'LC_ALL=C times >"$ACCOUNTING_TIMES_FINAL_PATH" 2>&1',
        'deltas = [end - start for start, end in zip(baseline, final)]',
        '"method": "bash-times-delta-reaped-descendants/v1"',
        '"unreaped_descendants": []',
        'accounting-session-baseline.pids',
        'if os.getsid(pid) == job_session:',
        'if [[ -n "$survivors" ]]',
        'exit 70',
        '"${MEASURE_WORKLOAD_ARGS[@]}"',
    )
    for marker in required:
        assert marker in source, marker
    assert source.index('ACCOUNTING_STARTED_EPOCH_S=$(date +%s.%N)') < source.index(
        'CCBENCH_CANONICAL_PIN=$("$PYTHON_BIN"'
    )
    assert source.index(
        'LC_ALL=C times >"$ACCOUNTING_TIMES_BASELINE_PATH" 2>&1'
    ) < source.index("for ((WAITED=0; WAITED<60; WAITED++))")


def test_f2_job_process_set_catches_a_reparentable_setsid_process_M9(
    tmp_path: Path,
) -> None:
    source = JOB.read_text(encoding="utf-8")

    def heredoc_after(marker: str) -> str:
        marker_offset = source.index(marker)
        start = source.index("<<'PY'", marker_offset) + len("<<'PY'\n")
        end = source.index("\nPY\n", start)
        return source[start:end]

    def process_starttime(pid: int) -> int | None:
        try:
            raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        closing = raw.rfind(")")
        fields = raw[closing + 2:].split() if closing >= 0 else []
        if len(fields) <= 19:
            raise AssertionError(f"cannot parse cleanup identity for pid {pid}")
        return int(fields[19])

    baseline_program = heredoc_after(
        '>"$ACCOUNTING_SESSION_BASELINE_PATH"'
    )
    audit_program = heredoc_after("audit_v3_job_process_set()")
    baseline = tmp_path / "process-set-baseline"
    completed = subprocess.run(
        [os.sys.executable, "-", str(os.getpid())],
        input=baseline_program,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    baseline.write_text(completed.stdout, encoding="utf-8")
    escaped = subprocess.Popen(["sleep", "60"], start_new_session=True)
    primary_error: BaseException | None = None
    escaped_starttime: int | None = None
    try:
        escaped_starttime = process_starttime(escaped.pid)
        assert escaped_starttime is not None
        observed = subprocess.run(
            [os.sys.executable, "-", str(os.getpid()), os.fspath(baseline)],
            input=audit_program,
            text=True,
            capture_output=True,
            check=False,
        )
        assert observed.returncode == 0, observed.stderr
        assert any(
            row.split()[0] == str(escaped.pid)
            for row in observed.stdout.splitlines()
            if row.split()
        )
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        cleanup_failures = []
        cleanup_race: ProcessLookupError | None = None
        try:
            escaped.kill()
        except ProcessLookupError as exc:
            cleanup_race = exc
        except OSError as exc:
            cleanup_failures.append(f"SIGKILL failed: {exc!r}")
        try:
            escaped.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                current_starttime = process_starttime(escaped.pid)
            except (OSError, ValueError, AssertionError) as exc:
                cleanup_failures.append(
                    f"cannot verify escaped process cleanup: {exc!r}"
                )
            else:
                if current_starttime == escaped_starttime:
                    cleanup_failures.append(
                        "escaped process remained after SIGKILL: "
                        f"pid={escaped.pid} starttime={escaped_starttime}"
                    )
        if cleanup_failures:
            if cleanup_race is not None:
                cleanup_failures.append(
                    f"process disappeared before SIGKILL: {cleanup_race!r}"
                )
            cleanup_error = AssertionError("; ".join(cleanup_failures))
            if primary_error is None:
                raise cleanup_error
            print(
                f"cleanup failure while preserving primary error: {cleanup_error}",
                file=os.sys.stderr,
            )
    assert "single-tenant-same-uid-process-set/v1" in source
    assert "created_during_job = process_identity not in baseline" in source
    assert "accounting-process-set-audit.error" in source
    assert source.index("audit_v3_job_process_set || exit 70") < source.index(
        'write_terminal "$shell_rc"'
    )


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
