from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe


REPO_ROOT = Path(probe.__file__).resolve().parents[3]
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
            probe.SUBMISSION_NONCE: HEX_A,
            probe.APPROVAL: HEX_A,
            probe.EVIDENCE_ROOT: str(evidence_dir),
        },
        "R2": {
            probe.SUBMISSION_NONCE: HEX_B,
            probe.SECOND_HEX: HEX_C,
            probe.EVIDENCE_ROOT: str(evidence_dir),
        },
        "R3": {
            probe.SUBMISSION_NONCE: HEX_E,
            probe.EVIDENCE_ROOT: str(evidence_dir),
        },
    }[request_id]
    ordered = [
        {
            "name": name,
            "value": values[name],
            "value_byte_length": len(values[name].encode("utf-8")),
        }
        for name in probe.REQUEST_ENV_NAMES[request_id]
    ]
    export_spec = ",".join(f"{row['name']}={row['value']}" for row in ordered)
    caller = {name: _state(None) for name in probe.TARGET_ENV_NAMES}
    caller[probe.AMBIENT_SENTINEL] = _state(SENTINEL)
    if request_id == "R2":
        caller[probe.SECOND_HEX] = _state(HEX_D)
    elif request_id == "R3":
        caller[probe.APPROVAL] = _state(probe.AMBIENT_APPROVAL_LITERAL)
    document = {
        "schema_version": probe.SUBMISSION_MANIFEST_SCHEMA,
        "authority": probe.AUTHORITY,
        "request_id": request_id,
        "request_label": probe.REQUEST_LABELS[request_id],
        "repo_head": HEAD,
        "probe_script_path": probe.PROBE_RELATIVE_PATH,
        "probe_script_sha256": probe._sha256_file(
            REPO_ROOT / probe.PROBE_RELATIVE_PATH
        ),
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
    (evidence_dir / probe.SUBMISSION_MANIFEST_NAME).write_text(
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
        environment[probe.AMBIENT_SENTINEL] = SENTINEL
    if ambient_approval:
        environment[probe.APPROVAL] = probe.AMBIENT_APPROVAL_LITERAL
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
        environ=environment,
        python_executable=sys.executable,
    )
    assert result_evidence == evidence
    return result


def test_r1_binds_all_three_explicit_values_and_skips_real_driver(
    tmp_path: Path,
) -> None:
    result = _observe(tmp_path, "R1", ambient_sentinel=True)

    assert result["ok"] is True
    assert [row["name"] for row in result["explicit_env_comparisons"]] == list(
        probe.REQUEST_ENV_NAMES["R1"]
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
    "missing_name",
    [probe.SUBMISSION_NONCE, probe.APPROVAL, probe.EVIDENCE_ROOT],
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
        environ=environment,
    )

    assert result["ok"] is False
    if missing_name == probe.EVIDENCE_ROOT:
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
    environment[probe.SUBMISSION_NONCE] = HEX_C
    environment[probe.SECOND_HEX] = HEX_B

    result, _ = probe.observe(
        repo_root=REPO_ROOT,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
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
        probe.PROBE_RELATIVE_PATH,
        probe.PBS_RELATIVE_PATH,
        probe.CAMPAIGN_RELATIVE_PATH,
    ):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    snapshot = {
        "head": "1" * 40,
        "tracked_status": "",
        "untracked_paths": [],
    }
    monkeypatch.setattr(probe, "_repo_snapshot", lambda _root: dict(snapshot))

    result, accepted_evidence = probe.observe(
        repo_root=repository,
        scratch_dir=scratch,
        pbs_job_id="12345.nqsv",
        environ={probe.EVIDENCE_ROOT: str(evidence)},
    )

    assert accepted_evidence is None
    assert result["ok"] is False
    assert any("outside the repository" in error for error in result["errors"])


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
    )

    assert observed["executed"] is True
    assert observed["timed_out"] is True
    assert observed["returncode"] is None
    assert observed["accepted_as_expected_refusal"] is False


def test_atomic_result_publish_is_create_only(tmp_path: Path) -> None:
    destination = tmp_path / probe.RESULT_NAME
    probe._write_atomic_create_only(destination, {"ok": True})
    original = destination.read_bytes()

    with pytest.raises(FileExistsError):
        probe._write_atomic_create_only(destination, {"ok": False})

    assert destination.read_bytes() == original
    assert [path.name for path in tmp_path.iterdir()] == [probe.RESULT_NAME]


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
    for name in probe.TARGET_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    rc = probe.main([
        "--repo-root", str(REPO_ROOT),
        "--scratch-dir", str(scratch),
        "--pbs-job-id", "0:12345.nqsv",
    ])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    assert len(captured.out.splitlines()) == 1
    assert captured.out.startswith(probe.RESULT_PREFIX)
    stdout_result = json.loads(captured.out[len(probe.RESULT_PREFIX):])
    file_result = json.loads((evidence / probe.RESULT_NAME).read_text(encoding="utf-8"))
    assert stdout_result == file_result
    assert stdout_result["ok"] is True


def test_pbs_contract_uses_scratch_and_stdout_without_fd_directory_assumption() -> None:
    pbs = (REPO_ROOT / probe.PBS_RELATIVE_PATH).read_text(encoding="utf-8")

    assert "#PBS -q gen_S" in pbs
    assert "#PBS -b 1" in pbs
    assert "#PBS -l elapstim_req=00:10:00" in pbs
    assert pbs.index("export GIT_OPTIONAL_LOCKS=0") < pbs.index("set -Eeuo pipefail")
    assert pbs.index("ulimit -c 0") < pbs.index("set -Eeuo pipefail")
    assert "^bnode[0-9]+" in pbs
    assert 'cd "$TMPDIR"' in pbs
    assert pbs.index('cd "$TMPDIR"') < pbs.index('"$PY" -I -B -u')
    assert probe.RESULT_PREFIX in pbs
    assert "/proc/$$/fd/" not in pbs
    assert '--pbs-job-id "$PBS_JOBID"' in pbs


def test_submitter_has_exact_three_request_design_and_create_only_witnesses() -> None:
    submitter = (
        REPO_ROOT / "tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh"
    ).read_text(encoding="utf-8")

    assert submitter.count("\nsubmit_request \\\n") == 3
    assert "qstat -Q" in submitter
    assert "pegasusinfo" in submitter
    assert "submission-manifest.json" in submitter
    assert 'with target.open("x"' in submitter
    assert '-v "$export_spec"' in submitter
    assert "T1259_NQSV_AMBIENT_SENTINEL" in submitter
    assert "t1259-ambient-approval-must-not-match" in submitter
    assert "T1259_QSUB_SECOND_HEX \"$R2_EXPLICIT_SECOND\"" in submitter
    assert "export T1259_QSUB_SECOND_HEX=\"$R2_AMBIENT_SECOND\"" in submitter
    for name in probe.TARGET_ENV_NAMES:
        assert f"unset {name}" in submitter
    marker = "submit_request " + "\\" + "\n  R3"
    r3_call = submitter.split(marker, 1)[1]
    assert "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" not in r3_call.split(
        '"$PY" -I -B -', 1
    )[0]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
