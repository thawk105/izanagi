from __future__ import annotations

import copy
import hashlib
import json
import shlex
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.tests import t1259_scan_bound
from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe


REPO_ROOT = Path(probe.__file__).resolve().parents[3]
PROBE_PATH = "tools/pegasus/probes/t1259_qsub_env_delivery_probe.py"
PBS_PATH = "tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs"
CAMPAIGN_PATH = "orchestrator/campaign/s8b_floor_campaign.py"
SUBMITTER_TEXT_PATH = (
    "tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh.txt"
)
SUBMISSION_MANIFEST_NAME = "submission-manifest.json"
SUBMISSION_MANIFEST_SCHEMA = "izanagi-t1259-qsub-submission-manifest/v1"
AUTHORITY = "diagnostic-only"
RESULT_PREFIX = "T1259_QSUB_ENV_DELIVERY_RESULT "
RESULT_NAME = "result.json"
SUBMISSION_NONCE = "IZANAGI_SUBMISSION_NONCE"
APPROVAL = "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN"
EVIDENCE_ROOT = "IZANAGI_FLOOR_JOB_EVIDENCE_ROOT"
SECOND_HEX = "T1259_QSUB_SECOND_HEX"
AMBIENT_SENTINEL = "T1259_NQSV_AMBIENT_SENTINEL"
AMBIENT_APPROVAL_LITERAL = "t1259-ambient-approval-must-not-match"
TARGET_ENV_NAMES = (
    SUBMISSION_NONCE,
    APPROVAL,
    EVIDENCE_ROOT,
    SECOND_HEX,
    AMBIENT_SENTINEL,
)
REQUEST_ENV_NAMES = {
    "R1": (SUBMISSION_NONCE, APPROVAL, EVIDENCE_ROOT),
    "R2": (SUBMISSION_NONCE, SECOND_HEX, EVIDENCE_ROOT),
    "R3": (SUBMISSION_NONCE, EVIDENCE_ROOT),
}
REQUEST_LABELS = {
    "R1": "with-explicit-approval",
    "R2": "without-approval-with-duplicate-second-name",
    "R3": "ambient-approval-name-only",
}
HEAD = subprocess.run(
    ["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
HEX_A = "a" * 32
HEX_B = "b" * 32
HEX_C = "c" * 32
HEX_D = "d" * 32
HEX_E = "e" * 32
SENTINEL = "f" * 32


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


EXECUTING_PBS_SHA256 = _sha256(REPO_ROOT / PBS_PATH)


@pytest.fixture(scope="module")
def _clean_detached_source_snapshot_template() -> dict[str, object]:
    """Capture the real submit-tree identity once, before modelling cleanliness."""
    snapshot = t1259_scan_bound.fixture_repo_snapshot(REPO_ROOT)
    snapshot["detached"] = True
    snapshot["tracked_status"] = ""
    snapshot["untracked_paths"] = []
    return snapshot


@pytest.fixture(autouse=True)
def _clean_detached_source_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    _clean_detached_source_snapshot_template: dict[str, object],
) -> None:
    """Give every test an isolated clean detached submit-tree snapshot."""
    original = probe._repo_snapshot
    snapshot = copy.deepcopy(_clean_detached_source_snapshot_template)

    def clean_snapshot(root: Path) -> dict[str, object]:
        if Path(root) == REPO_ROOT:
            return copy.deepcopy(snapshot)
        return original(root)

    monkeypatch.setattr(probe, "_repo_snapshot", clean_snapshot)


def _state(value: str | None) -> dict[str, object]:
    return {
        "present": value is not None,
        "value": value,
        "value_byte_length": len(value.encode("utf-8")) if value is not None else None,
    }


def _manifest(
    evidence_dir: Path,
    request_id: str,
) -> tuple[dict[str, object], dict[str, str]]:
    values = {
        "R1": {
            SUBMISSION_NONCE: HEX_A,
            APPROVAL: HEX_A,
            EVIDENCE_ROOT: str(evidence_dir),
        },
        "R2": {
            SUBMISSION_NONCE: HEX_B,
            SECOND_HEX: HEX_C,
            EVIDENCE_ROOT: str(evidence_dir),
        },
        "R3": {
            SUBMISSION_NONCE: HEX_E,
            EVIDENCE_ROOT: str(evidence_dir),
        },
    }[request_id]
    ordered = [
        {
            "name": name,
            "value": values[name],
            "value_byte_length": len(values[name].encode("utf-8")),
        }
        for name in REQUEST_ENV_NAMES[request_id]
    ]
    export_spec = ",".join(f"{row['name']}={row['value']}" for row in ordered)
    caller = {name: _state(None) for name in TARGET_ENV_NAMES}
    caller[AMBIENT_SENTINEL] = _state(SENTINEL)
    if request_id == "R2":
        caller[SECOND_HEX] = _state(HEX_D)
    elif request_id == "R3":
        caller[APPROVAL] = _state(AMBIENT_APPROVAL_LITERAL)
    document = {
        "schema_version": SUBMISSION_MANIFEST_SCHEMA,
        "authority": AUTHORITY,
        "request_id": request_id,
        "request_label": REQUEST_LABELS[request_id],
        "repo_head": HEAD,
        "probe_script_path": PROBE_PATH,
        "probe_script_sha256": _sha256(REPO_ROOT / PROBE_PATH),
        "pbs_script_path": PBS_PATH,
        "pbs_script_sha256": _sha256(REPO_ROOT / PBS_PATH),
        "campaign_script_path": CAMPAIGN_PATH,
        "campaign_script_sha256": _sha256(REPO_ROOT / CAMPAIGN_PATH),
        "ordered_explicit_env": ordered,
        "qsub_v_exact": export_spec,
        "qsub_v_byte_length": len(export_spec.encode("utf-8")),
        "qsub_caller_environment": caller,
        "qsub_caller_pid": 12345,
        "qsub_caller_observed_utc": "2026-09-07T00:00:00+00:00",
        "qsub_hostname": "pegasus02",
    }
    return document, values


def _write_manifest(
    evidence_dir: Path,
    request_id: str,
) -> dict[str, str]:
    document, values = _manifest(evidence_dir, request_id)
    (evidence_dir / SUBMISSION_MANIFEST_NAME).write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return values


def _job_environment(
    evidence_dir: Path,
    request_id: str,
    *,
    ambient_sentinel: bool = False,
    ambient_approval: bool = False,
) -> dict[str, str]:
    values = _write_manifest(evidence_dir, request_id)
    environment = dict(values)
    if ambient_sentinel:
        environment[AMBIENT_SENTINEL] = SENTINEL
    if ambient_approval:
        environment[APPROVAL] = AMBIENT_APPROVAL_LITERAL
    return environment


def _observe(
    tmp_path: Path,
    request_id: str,
    *,
    ambient_sentinel: bool = False,
    ambient_approval: bool = False,
) -> dict[str, object]:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(
        evidence,
        request_id,
        ambient_sentinel=ambient_sentinel,
        ambient_approval=ambient_approval,
    )
    result, result_evidence = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="0:12345.nqsv",
        executing_pbs_sha256=EXECUTING_PBS_SHA256,
        environ=environment,
        python_executable=sys.executable,
    )
    assert result_evidence == evidence
    return result


def _assert_projection_is_internally_consistent(
    projection: dict[str, object],
) -> None:
    categorical_bound = projection["projected_outcome"] == "approval-bound"
    assert categorical_bound is projection["official_approval_bound"]
    assert projection["confirm_flag_would_be_appended"] is categorical_bound


def test_r1_binds_all_three_explicit_values_and_skips_real_driver(
    tmp_path: Path,
) -> None:
    result = _observe(tmp_path, "R1", ambient_sentinel=True)

    assert result["ok"] is True
    assert [row["name"] for row in result["explicit_env_comparisons"]] == list(
        REQUEST_ENV_NAMES["R1"]
    )
    assert all(row["exact_match"] for row in result["explicit_env_comparisons"])
    assert result["floor_section8_source_projection"] == {
        "kind": "source-projection-from-measured-environment",
        "floor_campaign_shell_section8_executed": False,
        "driver_argv_executed_by_floor_campaign_shell": False,
        "approval_present": True,
        "approval_value": HEX_A,
        "submission_nonce_value": HEX_A,
        "projected_outcome": "approval-bound",
        "official_approval_bound": True,
        "confirm_flag_would_be_appended": True,
    }
    assert result["unapproved_driver_cli"]["executed"] is False
    assert result["official_campaign_executed"] is False
    assert result["submission_manifest"]["source_identity"] == {
        "repo_head": HEAD,
        "probe_script_path": PROBE_PATH,
        "probe_script_sha256": _sha256(REPO_ROOT / PROBE_PATH),
        "pbs_script_path": PBS_PATH,
        "pbs_script_sha256": EXECUTING_PBS_SHA256,
        "executing_pbs_sha256": EXECUTING_PBS_SHA256,
        "campaign_script_path": CAMPAIGN_PATH,
        "campaign_script_sha256": _sha256(REPO_ROOT / CAMPAIGN_PATH),
    }


def test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal(
    tmp_path: Path,
) -> None:
    result = _observe(tmp_path, "R2")

    assert result["ok"] is True, result["errors"]
    assert result["duplicate_name_precedence"] == {
        "explicit_value": HEX_C,
        "ambient_value": HEX_D,
        "job_value": HEX_C,
        "explicit_value_won": True,
        "ambient_value_won": False,
    }
    driver = result["unapproved_driver_cli"]
    assert driver["executed"] is True
    assert driver["timed_out"] is False
    assert driver["returncode"] == 2
    assert driver["accepted_as_expected_refusal"] is True
    assert driver["argv_exact_match"] is True
    assert driver["campaign_source_sha256_before"] == _sha256(
        REPO_ROOT / CAMPAIGN_PATH
    )
    assert driver["campaign_source_sha256_after"] == (
        driver["campaign_source_sha256_before"]
    )
    assert driver["argv"] == [
        sys.executable,
        "-I",
        "-B",
        str(REPO_ROOT / "orchestrator/campaign/s8b_floor_campaign.py"),
        "--mode",
        "official",
        "--protocol",
        str(tmp_path / "scratch" / "protocol-loader-must-not-run.json"),
    ]
    assert driver["approval_flag_absent"] is True
    assert "--confirm-official-floor-run" not in driver["argv"]
    assert driver["protocol_existed_before"] is False
    assert driver["protocol_exists_after"] is False
    assert driver["scratch_entries_before"] == driver["scratch_entries_after"]


@pytest.mark.parametrize(
    ("ambient_approval", "expected_outcome"),
    [
        (False, "ambient-approval-not-delivered-unbound"),
        (True, "ambient-approval-delivered-submit-binding-rejects-mismatch"),
    ],
    ids=["not-delivered", "delivered-mismatching-literal"],
)
def test_r3_records_only_the_observed_ambient_approval_condition(
    tmp_path: Path,
    ambient_approval: bool,
    expected_outcome: str,
) -> None:
    result = _observe(
        tmp_path,
        "R3",
        ambient_sentinel=ambient_approval,
        ambient_approval=ambient_approval,
    )

    assert result["ok"] is True
    assert len(result["explicit_env_comparisons"]) == 2
    assert result["ambient_approval_name_delivery"]["job_present"] is ambient_approval
    projection = result["floor_section8_source_projection"]
    assert projection["kind"] == "source-projection-from-measured-environment"
    assert projection["floor_campaign_shell_section8_executed"] is False
    assert projection["projected_outcome"] == expected_outcome
    assert projection["official_approval_bound"] is False
    assert result["unapproved_driver_cli"]["executed"] is False


@pytest.mark.parametrize(
    ("approval_value", "expected_outcome"),
    [
        (None, "approval-unset-unbound"),
        (HEX_B, "approval-present-submit-binding-rejects-mismatch"),
    ],
    ids=["approval-missing", "approval-mismatch"],
)
def test_r1_projection_follows_observed_approval_not_request_identity(
    tmp_path: Path,
    approval_value: str | None,
    expected_outcome: str,
) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(evidence, "R1")
    if approval_value is None:
        environment.pop(APPROVAL)
    else:
        environment[APPROVAL] = approval_value

    result, _ = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256=EXECUTING_PBS_SHA256,
        environ=environment,
    )

    projection = result["floor_section8_source_projection"]
    assert result["ok"] is False
    assert projection["projected_outcome"] == expected_outcome
    assert projection["official_approval_bound"] is False
    _assert_projection_is_internally_consistent(projection)


def test_r2_unexpected_approval_presence_is_unbound_and_not_green(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(evidence, "R2")
    environment[APPROVAL] = HEX_A

    result, _ = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256=EXECUTING_PBS_SHA256,
        environ=environment,
        python_executable=sys.executable,
    )

    projection = result["floor_section8_source_projection"]
    assert result["ok"] is False
    assert any("unexpectedly received" in error for error in result["errors"])
    assert projection["approval_present"] is True
    assert projection["projected_outcome"] == (
        "approval-present-submit-binding-rejects-mismatch"
    )
    assert projection["official_approval_bound"] is False
    _assert_projection_is_internally_consistent(projection)


@pytest.mark.parametrize(
    "missing_name",
    [SUBMISSION_NONCE, APPROVAL, EVIDENCE_ROOT],
)
def test_missing_r1_explicit_value_cannot_be_green(
    tmp_path: Path,
    missing_name: str,
) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(evidence, "R1")
    environment.pop(missing_name)

    result, _ = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256=EXECUTING_PBS_SHA256,
        environ=environment,
    )

    assert result["ok"] is False
    if missing_name == EVIDENCE_ROOT:
        assert result["request_id"] is None
        assert any("was not delivered" in error for error in result["errors"])
    else:
        comparison = {
            row["name"]: row for row in result["explicit_env_comparisons"]
        }[missing_name]
        assert comparison["observed_present"] is False
        assert comparison["exact_match"] is False


def test_swapped_r2_hex_values_fail_exact_binding(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(evidence, "R2")
    environment[SUBMISSION_NONCE] = HEX_C
    environment[SECOND_HEX] = HEX_B

    result, _ = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256=EXECUTING_PBS_SHA256,
        environ=environment,
        python_executable=sys.executable,
    )

    assert result["ok"] is False
    assert [row["exact_match"] for row in result["explicit_env_comparisons"]] == [
        False,
        False,
        True,
    ]


def test_repository_local_evidence_directory_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    scratch = tmp_path / "scratch"
    evidence = repository / "evidence"
    scratch.mkdir()
    evidence.mkdir(parents=True)
    for relative in (
        PROBE_PATH,
        PBS_PATH,
        CAMPAIGN_PATH,
    ):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    snapshot = {
        "head": "1" * 40,
        "detached": True,
        "tracked_status": "",
        "untracked_paths": [],
        "source_sha256": {
            PROBE_PATH: _sha256(repository / PROBE_PATH),
            PBS_PATH: _sha256(repository / PBS_PATH),
            CAMPAIGN_PATH: _sha256(repository / CAMPAIGN_PATH),
        },
    }
    monkeypatch.setattr(probe, "_repo_snapshot", lambda _root: dict(snapshot))

    result, accepted_evidence = probe.observe(
        repo_root=repository,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256="0" * 64,
        environ={EVIDENCE_ROOT: str(evidence)},
    )

    assert accepted_evidence is None
    assert result["ok"] is False
    assert any("outside the repository" in error for error in result["errors"])


@pytest.mark.parametrize(
    ("field", "executing_pbs_sha256"),
    [
        ("campaign_script_sha256", EXECUTING_PBS_SHA256),
        ("pbs_script_sha256", EXECUTING_PBS_SHA256),
        (None, "0" * 64),
    ],
    ids=["campaign-bytes", "repo-pbs-bytes", "executing-pbs-bytes"],
)
def test_submission_source_digests_are_bound_to_runtime_bytes(
    tmp_path: Path,
    field: str | None,
    executing_pbs_sha256: str,
) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    document, environment = _manifest(evidence, "R1")
    if field is not None:
        document[field] = "0" * 64
    (evidence / SUBMISSION_MANIFEST_NAME).write_text(
        json.dumps(document, sort_keys=True) + "\n", encoding="utf-8"
    )

    result, accepted_evidence = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256=executing_pbs_sha256,
        environ=environment,
    )

    assert accepted_evidence is None
    assert result["ok"] is False
    assert result["unapproved_driver_cli"]["executed"] is False
    assert any("sha256" in error or "PBS bytes" in error for error in result["errors"])


def test_r1_manifest_rejects_approval_that_does_not_equal_nonce(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    document, _ = _manifest(evidence, "R1")
    approval_row = next(
        row for row in document["ordered_explicit_env"]
        if row["name"] == APPROVAL
    )
    approval_row["value"] = HEX_B
    approval_row["value_byte_length"] = len(HEX_B.encode("utf-8"))
    export_spec = ",".join(
        f"{row['name']}={row['value']}"
        for row in document["ordered_explicit_env"]
    )
    document["qsub_v_exact"] = export_spec
    document["qsub_v_byte_length"] = len(export_spec.encode("utf-8"))
    manifest_path = evidence / SUBMISSION_MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(document, sort_keys=True) + "\n", encoding="utf-8"
    )

    with pytest.raises(
        probe.ProbeError,
        match="R1 approval is not exactly bound to its nonce",
    ):
        probe._validate_submission_manifest(
            manifest_path,
            evidence_dir=evidence,
            repo_snapshot=probe._repo_snapshot(REPO_ROOT),
            executing_pbs_sha256=EXECUTING_PBS_SHA256,
        )


def test_r3_manifest_rejects_nonliteral_ambient_approval(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    document, _ = _manifest(evidence, "R3")
    document["qsub_caller_environment"][APPROVAL] = _state(
        "different-ambient-approval"
    )
    manifest_path = evidence / SUBMISSION_MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(document, sort_keys=True) + "\n", encoding="utf-8"
    )

    with pytest.raises(
        probe.ProbeError,
        match="R3 qsub caller did not carry the fixed mismatching approval literal",
    ):
        probe._validate_submission_manifest(
            manifest_path,
            evidence_dir=evidence,
            repo_snapshot=probe._repo_snapshot(REPO_ROOT),
            executing_pbs_sha256=EXECUTING_PBS_SHA256,
        )


@pytest.mark.parametrize(
    ("snapshot_field", "bad_value"),
    [
        ("head", "0" * 40),
        ("detached", False),
        ("tracked_status", " M orchestrator/campaign/s8b_floor_campaign.py\n"),
        ("untracked_paths", ["unexpected"]),
    ],
)
def test_job_start_requires_manifest_head_detached_and_clean_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    snapshot_field: str,
    bad_value: object,
) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(evidence, "R1")
    snapshot = probe._repo_snapshot(REPO_ROOT)
    snapshot[snapshot_field] = bad_value
    monkeypatch.setattr(
        probe, "_repo_snapshot", lambda _root: copy.deepcopy(snapshot)
    )

    result, accepted_evidence = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256=EXECUTING_PBS_SHA256,
        environ=environment,
    )

    assert accepted_evidence is None
    assert result["ok"] is False
    assert result["unapproved_driver_cli"]["executed"] is False


def test_repo_unchanged_claim_compares_target_content_digests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(evidence, "R1")
    before = probe._repo_snapshot(REPO_ROOT)
    after = copy.deepcopy(before)
    after["source_sha256"][CAMPAIGN_PATH] = "0" * 64
    snapshots = iter((before, after))
    monkeypatch.setattr(
        probe, "_repo_snapshot", lambda _root: copy.deepcopy(next(snapshots))
    )

    result, _ = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        executing_pbs_sha256=EXECUTING_PBS_SHA256,
        environ=environment,
    )

    assert result["ok"] is False
    assert result["repo_working_tree_unchanged"] is False
    assert result["repo_state_before"]["tracked_status"] == (
        result["repo_state_after"]["tracked_status"]
    )
    assert result["repo_state_before"]["source_sha256"] != (
        result["repo_state_after"]["source_sha256"]
    )


def test_r2_timeout_is_not_accepted_as_refusal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    def timeout(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired(args[0], probe.DRIVER_TIMEOUT_SECONDS)

    monkeypatch.setattr(probe.subprocess, "run", timeout)
    observed = probe._unapproved_driver_observation(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        python_executable=sys.executable,
        expected_campaign_sha256=_sha256(REPO_ROOT / CAMPAIGN_PATH),
    )

    assert observed["executed"] is True
    assert observed["timed_out"] is True
    assert observed["returncode"] is None
    assert observed["accepted_as_expected_refusal"] is False


def test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract(
    tmp_path: Path,
) -> None:
    expected_argv = (
        sys.executable,
        "-I",
        "-B",
        str(REPO_ROOT / CAMPAIGN_PATH),
        "--mode",
        "official",
        "--protocol",
        str(tmp_path / "protocol-loader-must-not-run.json"),
    )
    argv = [*expected_argv, "--resume", str(tmp_path / "unexpected-resume.json")]

    with pytest.raises(
        probe.ProbeError,
        match="R2 unapproved driver argv differs from the fixed contract",
    ):
        probe._validated_unapproved_driver_environment(argv, expected_argv)


def test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match(
    tmp_path: Path,
) -> None:
    argv = (
        sys.executable,
        "-I",
        "-B",
        str(REPO_ROOT / CAMPAIGN_PATH),
        "--mode",
        "official",
        "--protocol",
        str(tmp_path / "protocol-loader-must-not-run.json"),
        "--confirm-official-floor-run",
    )

    with pytest.raises(
        probe.ProbeError,
        match="R2 unapproved driver argv unexpectedly carries approval",
    ):
        probe._validated_unapproved_driver_environment(argv, argv)


@pytest.mark.parametrize(
    "mutation",
    [
        "extra-argv",
        "wrong-mode",
        "approval-flag",
    ],
)
def test_r2_refusal_rejects_any_driver_argv_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    def refused(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if mutation == "extra-argv":
            argv.extend(["--resume", str(tmp_path / "unexpected-resume.json")])
        elif mutation == "wrong-mode":
            argv[argv.index("official")] = "diagnostic"
        else:
            argv.append("--confirm-official-floor-run")
        return subprocess.CompletedProcess(
            argv,
            2,
            stdout=json.dumps({
                "status": "refused",
                "reason": "--confirm-official-floor-run is required",
            }) + "\n",
            stderr="",
        )

    monkeypatch.setattr(probe.subprocess, "run", refused)
    observed = probe._unapproved_driver_observation(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        python_executable=sys.executable,
        expected_campaign_sha256=_sha256(REPO_ROOT / CAMPAIGN_PATH),
    )

    assert observed["returncode"] == 2
    assert observed["argv_exact_match"] is False
    assert observed["accepted_as_expected_refusal"] is False
    if mutation == "approval-flag":
        assert observed["approval_flag_absent"] is False


def test_atomic_result_publish_is_create_only(tmp_path: Path) -> None:
    destination = tmp_path / RESULT_NAME
    probe._write_atomic_create_only(destination, {"ok": True})
    original = destination.read_bytes()

    with pytest.raises(FileExistsError):
        probe._write_atomic_create_only(destination, {"ok": False})

    assert destination.read_bytes() == original
    assert [path.name for path in tmp_path.iterdir()] == [RESULT_NAME]


def test_main_emits_one_prefixed_stdout_line_and_auxiliary_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()
    environment = _job_environment(evidence, "R1")
    for name in TARGET_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    rc = probe.main([
        "--repo-root", str(REPO_ROOT),
        "--scratch-dir", str(scratch),
        "--pbs-job-id", "0:12345.nqsv",
        "--executing-pbs-sha256", EXECUTING_PBS_SHA256,
    ])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    assert len(captured.out.splitlines()) == 1
    assert captured.out.startswith(RESULT_PREFIX)
    stdout_result = json.loads(captured.out[len(RESULT_PREFIX):])
    file_result = json.loads((evidence / RESULT_NAME).read_text(encoding="utf-8"))
    assert stdout_result == file_result
    assert stdout_result["ok"] is True


def _marked_block(source: str, label: str) -> str:
    start = f"# BEGIN T1259 {label}\n"
    end = f"# END T1259 {label}\n"
    assert source.count(start) == 1
    assert source.count(end) == 1
    return source.split(start, 1)[1].split(end, 1)[0]


def _shell_function_body(source: str, name: str, next_name: str) -> str:
    start = f"{name}() {{\n"
    end = f"}}\n\n{next_name}()"
    assert source.count(start) == 1
    assert source.count(end) == 1
    body_start = source.index(start) + len(start)
    body_end = source.index(end, body_start)
    body = source[body_start:body_end]
    assert body.endswith("\n")
    return body


def _heredoc_python(shell_block: str) -> str:
    marker = "<<'PY'\n"
    assert shell_block.count(marker) == 1
    body = shell_block.split(marker, 1)[1]
    assert body.count("\nPY\n") == 1
    return body.split("\nPY\n", 1)[0] + "\n"


def _run_pbs_observer_harness(
    tmp_path: Path,
    stub_body: str,
) -> subprocess.CompletedProcess[str]:
    pbs = (REPO_ROOT / PBS_PATH).read_text(encoding="utf-8")
    functions = _marked_block(pbs, "PBS RESULT FUNCTIONS")
    stub = tmp_path / "observer-stub"
    stub.write_text(stub_body, encoding="utf-8")
    output = tmp_path / "observer.stdout"
    harness = f"""
set -Eeuo pipefail
PY={shlex.quote(sys.executable)}
{functions}
if run_observer {shlex.quote(str(output))} bash {shlex.quote(str(stub))}; then
  harness_rc=0
else
  harness_rc=$?
fi
printf 'HARNESS_RC=%s\\n' "$harness_rc" >&2
"""
    return subprocess.run(
        ["bash", "-c", harness],
        check=True,
        capture_output=True,
        text=True,
    )


def test_pbs_contract_runs_observer_through_single_result_call_block() -> None:
    pbs = (REPO_ROOT / PBS_PATH).read_text(encoding="utf-8")
    observer_call = _marked_block(pbs, "PBS OBSERVER CALL")
    result_functions = _marked_block(pbs, "PBS RESULT FUNCTIONS")
    initialization = _marked_block(pbs, "PBS SHELL INITIALIZATION")

    assert "#PBS -q gen_S" in pbs
    assert "#PBS -b 1" in pbs
    assert "#PBS -l elapstim_req=00:10:00" in pbs
    assert pbs.count('#   qsub -o "$ATTEMPT_ROOT/') == 3
    assert pbs.index("RESULT_PREFIX=") < pbs.index("ulimit -c 0")
    assert pbs.index("trap 'fail_pbs unhandled-shell-error' ERR") < pbs.index(
        "ulimit -c 0"
    )
    assert pbs.index("export GIT_OPTIONAL_LOCKS=0") < pbs.index("set -Eeuo pipefail")
    assert pbs.index("ulimit -c 0 || fail_pbs core-dump-disable-failed") < pbs.index(
        "set -Eeuo pipefail"
    )
    assert "ulimit -c 0 || fail_pbs core-dump-disable-failed" in initialization
    assert "^bnode[0-9]+" in pbs
    assert 'cd "$TMPDIR"' in pbs
    assert pbs.index('cd "$TMPDIR"') < pbs.index("# BEGIN T1259 PBS OBSERVER CALL")
    assert "/proc/$$/fd/" not in pbs
    assert 'PROBE_STDOUT="$TMPDIR/observer.stdout"' in observer_call
    assert 'if run_observer "$PROBE_STDOUT" \\' in observer_call
    assert '"$PY" -I -B -u "$REPO_ROOT/$DRIVER_REL"' in observer_call
    assert '--pbs-job-id "$PBS_JOBID" \\' in observer_call
    assert '--executing-pbs-sha256 "$EXECUTING_PBS_SHA256"' in observer_call
    assert 'if "$@" >"$output_path"; then' in result_functions
    assert 'if ! validate_observer_stdout "$output_path"; then' in result_functions
    assert 'printf \'%s\\n\' "$result_line"' in result_functions
    assert "set +e" not in observer_call


def test_pbs_early_ulimit_failure_emits_one_prefixed_result() -> None:
    pbs = (REPO_ROOT / PBS_PATH).read_text(encoding="utf-8")
    functions = _marked_block(pbs, "PBS RESULT FUNCTIONS")
    initialization = _marked_block(pbs, "PBS SHELL INITIALIZATION")
    harness = f"""
{functions}
ulimit() {{ return 9; }}
{initialization}
printf 'unreachable\\n'
"""

    completed = subprocess.run(
        ["bash", "-c", harness],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    lines = completed.stdout.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith(RESULT_PREFIX)
    payload = json.loads(lines[0][len(RESULT_PREFIX):])
    assert payload["ok"] is False
    assert payload["errors"] == ["pbs-shell:core-dump-disable-failed"]


def test_pbs_preserves_one_valid_negative_observer_result(tmp_path: Path) -> None:
    detailed = RESULT_PREFIX + '{"authority":"diagnostic-only","ok":false}'
    completed = _run_pbs_observer_harness(
        tmp_path,
        f"printf '%s\\n' {shlex.quote(detailed)}\nexit 1\n",
    )

    assert completed.stdout.splitlines() == [detailed]
    assert completed.stderr == "HARNESS_RC=1\n"


@pytest.mark.parametrize(
    "stub_body",
    [
        "exit 7\n",
        (
            "printf '%s\\n' "
            + shlex.quote(RESULT_PREFIX + '{"ok":false}')
            + " "
            + shlex.quote(RESULT_PREFIX + '{"ok":false}')
            + "\nexit 1\n"
        ),
        "printf '%s\\n' " + shlex.quote(RESULT_PREFIX + "not-json") + "\nexit 1\n",
    ],
    ids=["no-output-nonzero", "two-prefixed-lines", "unparseable-json"],
)
def test_pbs_replaces_invalid_observer_stdout_with_one_fallback(
    tmp_path: Path,
    stub_body: str,
) -> None:
    completed = _run_pbs_observer_harness(tmp_path, stub_body)

    lines = completed.stdout.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith(RESULT_PREFIX)
    payload = json.loads(lines[0][len(RESULT_PREFIX):])
    assert payload["ok"] is False
    assert payload["errors"] == ["pbs-shell:invalid-observer-stdout"]
    assert completed.stderr == "HARNESS_RC=2\n"


def test_submitter_text_is_outside_execution_inventory() -> None:
    submitter_path = REPO_ROOT / SUBMITTER_TEXT_PATH

    assert submitter_path.is_file()
    assert not (REPO_ROOT / "tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh").exists()
    assert submitter_path.read_bytes()[:2] != b"#!"
    assert submitter_path.suffix == ".txt"
    assert submitter_path.stat().st_mode & (
        stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    ) == 0


def test_submitter_has_exact_three_request_design_and_create_only_witnesses() -> None:
    submitter = (REPO_ROOT / SUBMITTER_TEXT_PATH).read_text(encoding="utf-8")
    preflight = _marked_block(submitter, "PREFLIGHT CALLS AND SEMANTIC CHECK")
    qsub_call = _marked_block(submitter, "QSUB CALL")
    group_calls = _marked_block(submitter, "GROUP INTENT AND REQUEST CALLS")
    manifest_writer = _shell_function_body(
        submitter, "write_submission_manifest", "write_group_intent"
    )
    group_intent_writer = _shell_function_body(
        submitter, "write_group_intent", "write_request_receipt"
    )
    request_receipt_writer = _shell_function_body(
        submitter, "write_request_receipt", "submit_request"
    )
    request_function = submitter.split(
        "submit_request() (", 1
    )[1].split("# BEGIN T1259 GROUP INTENT", 1)[0]

    assert group_calls.count("\nsubmit_request \\\n") == 3
    assert group_calls.index("write_group_intent") < group_calls.index("submit_request")
    assert "capture_preflight qstat-queues qstat -Q" in preflight
    assert "capture_preflight pegasusinfo pegasusinfo" in preflight
    assert 'fields[0] == "gen_S"' in preflight
    assert 'queue_state == "ENA"' in preflight
    assert 'qsub \\\n      -o "$evidence_dir/pbs.stdout"' in qsub_call
    assert '-v "$export_spec"' in qsub_call
    assert 'qstat "$scheduler_request_id" \\' in request_function
    assert "line.startswith(scheduler_id)" in request_receipt_writer
    assert 'fields[1].startswith(expected_job_name_prefix)' in request_receipt_writer
    assert "observed_owner == expected_owner" in request_receipt_writer
    assert "observed_state in accepted_states" in request_receipt_writer
    assert (
        'accepted_states = ("STG", "ARR", "WAI", "QUE", "PRR", "RUN")'
        in request_receipt_writer
    )
    assert "write_request_receipt" in request_function
    assert 'with target.open("x"' in manifest_writer
    assert 'with target.open("x"' in group_intent_writer
    assert '"expected_request_count": 3' in group_intent_writer
    assert '"attempt_id": attempt_id' in group_intent_writer
    assert '"started_utc": started_utc' in group_intent_writer
    assert '"repo_head": repo_head' in group_intent_writer
    assert "terminal_state" not in submitter
    assert "result_sha256" not in submitter
    assert "submission-group-manifest.json" not in submitter
    assert submitter.index("ulimit -c 0") < submitter.index("SCRIPT_SOURCE=")
    assert 'RUNNING_SUBMITTER_SHA256=$(sha256sum -- "$SCRIPT_PATH"' in submitter
    assert '"$RUNNING_SUBMITTER_SHA256" != "$SUBMITTER_SHA256"' in submitter
    assert submitter.index('cd "$ATTEMPT_ROOT"') < submitter.index(
        "# BEGIN T1259 PREFLIGHT"
    )
    assert 'verify_repo_unchanged "before $request_id qsub"' in request_function
    assert 'verify_repo_unchanged "at submitter exit"' in submitter
    assert "T1259_QSUB_SECOND_HEX \"$R2_EXPLICIT_SECOND\"" in group_calls
    assert "export T1259_QSUB_SECOND_HEX=\"$R2_AMBIENT_SECOND\"" in request_function
    for name in TARGET_ENV_NAMES:
        assert f"unset {name}" in request_function
    r3_call = group_calls.split("submit_request \\\n  R3", 1)[1]
    assert APPROVAL not in r3_call


@pytest.mark.parametrize(
    ("queue_row", "expected_rc", "expected_state", "expected_usable"),
    [
        ("gen_S 0 0 ENA\n", 0, "ENA", True),
        ("gen_S 0 0 DIS\n", 3, "DIS", False),
        ("other 0 0 ENA\n", 3, None, False),
    ],
    ids=["enabled", "disabled", "missing-gen-s"],
)
def test_submitter_preflight_parses_gen_s_semantic_state(
    tmp_path: Path,
    queue_row: str,
    expected_rc: int,
    expected_state: str | None,
    expected_usable: bool,
) -> None:
    submitter = (REPO_ROOT / SUBMITTER_TEXT_PATH).read_text(encoding="utf-8")
    code = _heredoc_python(
        _marked_block(submitter, "PREFLIGHT CALLS AND SEMANTIC CHECK")
    )
    preflight = tmp_path / "preflight"
    preflight.mkdir()
    for name in ("qstat-queues", "pegasusinfo", "own-requests"):
        stdout = queue_row if name == "qstat-queues" else "fixture\n"
        (preflight / f"{name}.stdout").write_text(stdout, encoding="utf-8")
        (preflight / f"{name}.stderr").write_text("", encoding="utf-8")
        (preflight / f"{name}.rc").write_text("0\n", encoding="ascii")

    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-", str(preflight), "1" * 40],
        input=code,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == expected_rc
    document = json.loads((preflight / "preflight.json").read_text())
    assert document["gen_s_queue"]["state"] == expected_state
    assert document["gen_s_queue"]["usable"] is expected_usable


@pytest.mark.parametrize(
    ("qstat_rc", "qstat_body", "expected_rc", "expected_visible"),
    [
        (
            0,
            "RequestID ReqName UserName Queue STT\n"
            "12345.nqsv izanagi- owner gen_S STG\n",
            0,
            True,
        ),
        (
            0,
            "RequestID ReqName UserName Queue STT\n"
            "12345.nqsv izanagi- owner gen_S RUN\n",
            0,
            True,
        ),
        (
            0,
            "RequestID ReqName UserName Queue STT\n"
            "12345.nqsv izanagi- owner gen_S QUE\n",
            0,
            True,
        ),
        (0, "Request ID Name User Queue STT\n", 5, False),
        (
            1,
            "RequestID ReqName UserName Queue STT\n"
            "12345.nqsv izanagi- owner gen_S RUN\n",
            5,
            True,
        ),
    ],
    ids=[
        "visible-immediate-staging",
        "visible-eight-char-name",
        "visible-eight-char-name-queued",
        "rc-zero-but-absent",
        "body-present-rc-failed",
    ],
)
def test_request_receipt_binds_qstat_body_visibility(
    tmp_path: Path,
    qstat_rc: int,
    qstat_body: str,
    expected_rc: int,
    expected_visible: bool,
) -> None:
    submitter = (REPO_ROOT / SUBMITTER_TEXT_PATH).read_text(encoding="utf-8")
    function_block = _shell_function_body(
        submitter, "write_request_receipt", "submit_request"
    )
    code = _heredoc_python(function_block)
    manifest = tmp_path / SUBMISSION_MANIFEST_NAME
    receipt = tmp_path / "qsub-request.json"
    qstat_stdout = tmp_path / "qstat-after-submit.stdout"
    qstat_stderr = tmp_path / "qstat-after-submit.stderr"
    manifest.write_text("{}\n", encoding="utf-8")
    qstat_stdout.write_text(qstat_body, encoding="utf-8")
    qstat_stderr.write_text("", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-",
            str(manifest),
            str(receipt),
            str(qstat_stdout),
            str(qstat_stderr),
            "R1",
            "with-explicit-approval",
            "12345.nqsv",
            "2026-09-08T00:00:00Z",
            str(qstat_rc),
            "owner",
        ],
        input=code,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == expected_rc
    document = json.loads(receipt.read_text(encoding="utf-8"))
    assert document["qstat_visibility"]["request_line_visible"] is expected_visible
    assert document["qstat_visibility"]["accepted"] is (expected_rc == 0)
    assert document["qstat_visibility"]["accepted_states"] == [
        "STG",
        "ARR",
        "WAI",
        "QUE",
        "PRR",
        "RUN",
    ]


def test_request_receipt_accepts_measured_qstat_layout(tmp_path: Path) -> None:
    submitter = (REPO_ROOT / SUBMITTER_TEXT_PATH).read_text(encoding="utf-8")
    function_block = _shell_function_body(
        submitter, "write_request_receipt", "submit_request"
    )
    code = _heredoc_python(function_block)
    manifest = tmp_path / SUBMISSION_MANIFEST_NAME
    receipt = tmp_path / "qsub-request.json"
    qstat_stdout = tmp_path / "qstat-after-submit.stdout"
    qstat_stderr = tmp_path / "qstat-after-submit.stderr"
    manifest.write_text("{}\n", encoding="utf-8")
    qstat_stdout.write_text(
        "RequestID       ReqName  UserName Queue     Pri STT S   Memory      CPU   Elapse R H M Jobs\n"
        "--------------- -------- -------- -------- ---- --- - -------- -------- -------- - - - ----\n"
        "982450.nqsv     izanagi- tanab    gen_S       0 STG -    0.00B     0.00        0 N Y Y    1\n",
        encoding="utf-8",
    )
    qstat_stderr.write_text("", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-",
            str(manifest),
            str(receipt),
            str(qstat_stdout),
            str(qstat_stderr),
            "R1",
            "with-explicit-approval",
            "982450.nqsv",
            "2026-09-08T00:00:00Z",
            "0",
            "tanab",
        ],
        input=code,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    visibility = json.loads(receipt.read_text(encoding="utf-8"))["qstat_visibility"]
    assert visibility["observed_state"] == "STG"
    assert visibility["observed_owner"] == "tanab"
    assert visibility["accepted"] is True


@pytest.mark.parametrize(
    ("qstat_body", "rejected_field", "observed_value"),
    [
        (
            "RequestID ReqName UserName Queue STT\n"
            "12345.nqsv izanagi- different-owner gen_S RUN\n",
            "owner_matches",
            "different-owner",
        ),
        (
            "RequestID ReqName UserName Queue STT\n"
            "12345.nqsv izanagi- owner gen_S HLD\n",
            "state_accepted",
            "HLD",
        ),
        (
            "RequestID ReqName UserName Queue STT\n"
            "12345.nqsv izanagi- owner gen_S EXT\n",
            "state_accepted",
            "EXT",
        ),
    ],
    ids=["different-owner", "non-active-state", "terminal-state"],
)
def test_request_receipt_rejects_wrong_owner_or_non_active_state(
    tmp_path: Path,
    qstat_body: str,
    rejected_field: str,
    observed_value: str,
) -> None:
    submitter = (REPO_ROOT / SUBMITTER_TEXT_PATH).read_text(encoding="utf-8")
    function_block = _shell_function_body(
        submitter, "write_request_receipt", "submit_request"
    )
    code = _heredoc_python(function_block)
    manifest = tmp_path / SUBMISSION_MANIFEST_NAME
    receipt = tmp_path / "qsub-request.json"
    qstat_stdout = tmp_path / "qstat-after-submit.stdout"
    qstat_stderr = tmp_path / "qstat-after-submit.stderr"
    manifest.write_text("{}\n", encoding="utf-8")
    qstat_stdout.write_text(qstat_body, encoding="utf-8")
    qstat_stderr.write_text("", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-",
            str(manifest),
            str(receipt),
            str(qstat_stdout),
            str(qstat_stderr),
            "R1",
            "with-explicit-approval",
            "12345.nqsv",
            "2026-09-08T00:00:00Z",
            "0",
            "owner",
        ],
        input=code,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 5
    document = json.loads(receipt.read_text(encoding="utf-8"))
    visibility = document["qstat_visibility"]
    assert visibility["request_line_visible"] is True
    assert visibility["accepted"] is False
    assert visibility[rejected_field] is False
    observed_field = (
        "observed_owner"
        if rejected_field == "owner_matches"
        else "observed_state"
    )
    assert visibility[observed_field] == observed_value


def test_group_intent_is_create_only_and_has_no_completion_fields(
    tmp_path: Path,
) -> None:
    submitter = (REPO_ROOT / SUBMITTER_TEXT_PATH).read_text(encoding="utf-8")
    function_block = _shell_function_body(
        submitter, "write_group_intent", "write_request_receipt"
    )
    code = _heredoc_python(function_block)
    (tmp_path / "preflight").mkdir()
    (tmp_path / "preflight" / "preflight.json").write_text(
        "{}\n", encoding="utf-8"
    )
    target = tmp_path / "submission-group-intent.json"
    argv = [
        sys.executable,
        "-I",
        "-B",
        "-",
        str(target),
        "a" * 32,
        "2026-09-08T00:00:00Z",
        "1" * 40,
        "2" * 64,
        "3" * 64,
        "4" * 64,
        "5" * 64,
    ]

    first = subprocess.run(
        argv, input=code, capture_output=True, text=True, check=False
    )
    original = target.read_bytes()
    second = subprocess.run(
        argv, input=code, capture_output=True, text=True, check=False
    )

    assert first.returncode == 0
    assert second.returncode != 0
    assert target.read_bytes() == original
    document = json.loads(original)
    assert document["attempt_id"] == "a" * 32
    assert document["expected_request_count"] == 3
    assert [row["request_label"] for row in document["requests"]] == [
        "with-explicit-approval",
        "without-approval-with-duplicate-second-name",
        "ambient-approval-name-only",
    ]
    assert "terminal_state" not in document
    assert "result_sha256" not in document


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
