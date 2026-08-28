from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import ident, site_policy
from orchestrator.campaign import paper_story_a1_paired as paired
from orchestrator.campaign.build_admission import GeneratorId, build_run_context


REPO_ROOT = Path(__file__).resolve().parents[2]
JOB = REPO_ROOT / "tools/pegasus/paper_story_a1_paired.sh"
REGISTRY = REPO_ROOT / "tools/pegasus/admission_registry.json"
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


def test_non_certifying_source_closure_matches_shell_and_preserves_legacy_set() -> None:
    assert paired.SOURCE_RELATIVE_PATHS == (
        "orchestrator/campaign/paper_story_a1_paired.py",
        "orchestrator/campaign/paper_story_a1_paired.v2.json",
        "orchestrator/campaign/pipeline.py",
        "tools/pegasus/paper_story_a1_paired.sh",
    )
    script = JOB.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^NON_CERTIFYING_SOURCE_RELATIVE_PATHS=\(\n(?P<body>.*?)^\)\s*$",
        script,
    )
    assert match is not None
    shell_paths = tuple(re.findall(r'^\s*"([^"]+)"\s*$', match["body"], re.M))
    assert shell_paths == paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    assert len(shell_paths) == 9


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
    qstat_stdout = f"Job Id: {request_id}\n    job_state = F\n"

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
    assert source.count(
        'EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"'
    ) == 1
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
    for marker in required:
        assert source.count(marker) == 1, marker
    assert _shell_submitter_violations(source) == []
    assert "dispatch_compute.py" not in source
    assert "PBS_O_QUEUE" not in source
    assert re.findall(r"/proc/[A-Za-z0-9_./-]+", source) == [
        "/proc/sys/kernel/random/boot_id"
    ]
    assert "os.readlink" not in source
    assert 're.fullmatch(r"[A-Z]", visibility["state"])' not in source
    assert source.count("status --porcelain --untracked-files=all") == 3


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
    gflags_source = (tmp_path / "gflags-source").resolve()
    glog_source = (tmp_path / "glog-source").resolve()
    gflags_source.mkdir()
    glog_source.mkdir()
    gflags_expected_head = "c" * 40
    glog_expected_head = "d" * 40
    pegasus_policy = repo / "tools/pegasus/policy.json"
    pegasus_policy.parent.mkdir(parents=True, exist_ok=True)
    pegasus_policy.write_text(
        json.dumps({
            "gflags_source_path": os.fspath(gflags_source),
            "gflags_expected_head": gflags_expected_head,
            "glog_source_path": os.fspath(glog_source),
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
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    head = "a" * 40
    git_stub = bin_dir / "git"
    git_stub.write_text(
        "#!/bin/bash\n"
        "if [[ \"$*\" == *\"rev-parse HEAD\"* ]]; then\n"
        "  if [[ \"$*\" == *\"gflags-source\"* ]]; then echo \"$FAKE_GFLAGS_HEAD\"; "
        "elif [[ \"$*\" == *\"glog-source\"* ]]; then echo \"$FAKE_GLOG_HEAD\"; "
        "else echo \"$FAKE_HEAD\"; fi; exit 0\n"
        "fi\n"
        "if [[ \"$*\" == *\"status --porcelain\"* ]]; then\n"
        "  if [[ \"$*\" == *\"gflags-source\"* ]]; then "
        "[[ \"${FAKE_GFLAGS_DIRTY:-0}\" == 1 ]] && echo ' M gflags.cc'; "
        "elif [[ \"$*\" == *\"glog-source\"* ]]; then "
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
    assert "cmake -S " in logged and "gflags-source" in logged
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
    assert "run_campaign" in called
    assert "evaluate" not in imported
    assert "evaluate" not in called


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
) -> tuple[Path, Path, str]:
    policy, policy_sha = paired.load_policy()
    repo = tmp_path / "submit-repo"
    for relative in paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS:
        source = repo / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"fixture source: {relative}\n", encoding="utf-8")
    base = (tmp_path / "measurement-submit").resolve()
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
            return subprocess.CompletedProcess(argv, 0, "12345.nqsv\n", "")
        assert argv[:2] == ["qstat", "-f"]
        return subprocess.CompletedProcess(
            argv,
            0,
            "Request ID: 12345.nqsv\nState: QUE\nQueue: gen_S\n",
            "",
        )

    monkeypatch.setattr(paired.subprocess, "run", run)
    assert paired.run_submit(SimpleNamespace(
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
    assert paired.run_complete(SimpleNamespace(
        expected_head=head, attempt_root=str(attempt),
    )) == 0
    completion = json.loads(Path(evidence["completion_receipt"]).read_bytes())
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


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
