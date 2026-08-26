# -*- coding: utf-8 -*-
"""Frozen predicates and closure tests for the MoCC G2 study ledger."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign import mocc_g2_repro_ledger as LEDGER  # noqa: E402

FROZEN_PREREGISTRATION = (
    REPO_ROOT
    / "output/insights/2026-08-26_mocc-g2-repro/pre-registration.md"
)


def _write_json(path: Path, value: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    path.write_bytes(raw)
    return raw


def _verifier_result(
    *,
    verdict: str = "serializable",
    total_cycles: int = 0,
    phenomena: tuple[str, ...] = (),
    clean: bool = True,
    txns: int = 1000,
) -> dict[str, object]:
    return {
        "results": [
            {
                "verdict": verdict,
                "total_cycles": total_cycles,
                "anomaly_count": len(phenomena),
                "anomalies": [
                    {"phenomenon": phenomenon} for phenomenon in phenomena
                ],
                "stats": {"txns": txns},
                "integrity": {"clean": clean},
            }
        ]
    }


def _nonce(ordinal: int) -> str:
    return f"{ordinal:032x}"


def _submit_receipt(
    *, nonce: str, request_id: str, source_commit: str, dry_run: bool = False
) -> dict[str, object]:
    return {
        "schema_version": LEDGER.SUBMIT_RECEIPT_SCHEMA_VERSION,
        "submission_nonce": nonce,
        "source_commit": source_commit,
        "dry_run": dry_run,
        "qsub": {"request_id": request_id, "submit_epoch": 100000},
    }


def _pilot_receipt(*, request_id: str, host: str) -> dict[str, object]:
    return {
        "schema_version": LEDGER.PILOT_RECEIPT_SCHEMA_VERSION,
        "pbs": {"hostname": host, "jobid": f"0:{request_id}"},
        "source": {"outer_repo_commit": LEDGER.FROZEN_COMMIT},
    }


def _make_study(root: Path, *, count: int = LEDGER.PLANNED_N) -> Path:
    root.mkdir(parents=True)
    (root / "pre-registration.md").write_bytes(
        FROZEN_PREREGISTRATION.read_bytes()
    )
    lines = ["\t".join(LEDGER.LEDGER_COLUMNS)]
    for ordinal in range(1, count + 1):
        batch = (ordinal - 1) // 6 + 1
        nonce = _nonce(ordinal)
        request_id = f"job-{ordinal}"
        lines.append(
            "\t".join(
                (
                    str(ordinal),
                    str(batch),
                    nonce,
                    request_id,
                    str(100000 + ordinal),
                    LEDGER.FROZEN_COMMIT,
                )
            )
        )
        run = root / "runs" / str(ordinal)
        submit_receipt = _submit_receipt(
            nonce=nonce,
            request_id=request_id,
            source_commit=LEDGER.FROZEN_COMMIT,
        )
        _write_json(run / "submit-receipt.json", submit_receipt)
        _write_json(
            root / "submissions" / nonce / "submit-receipt.json",
            submit_receipt,
        )
        _write_json(run / "verifier.json", _verifier_result())
        host = f"host-{batch % 2}"
        _write_json(
            run / "reservation.json",
            {"host": host, "nonce": nonce, "job_id": f"0:{request_id}"},
        )
        completed_raw = _write_json(
            run / "mocc-trace-pilot-receipt.json",
            _pilot_receipt(request_id=request_id, host=host),
        )
        _write_json(
            run / "job-result.json",
            {
                "schema_version": LEDGER.JOB_RESULT_SCHEMA_VERSION,
                "pbs_jobid": f"0:{request_id}",
                "receipt_sha256": hashlib.sha256(completed_raw).hexdigest(),
            },
        )
    for offset, dry_run in enumerate((True, False), start=1):
        nonce = f"e{offset:031x}"
        _write_json(
            root / "submissions" / nonce / "submit-receipt.json",
            _submit_receipt(
                nonce=nonce,
                request_id=(f"dry-run-{nonce}" if dry_run else "probe-job"),
                source_commit="0" * 40,
                dry_run=dry_run,
            ),
        )
    (root / "submission-ledger.tsv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return root


def _configure_branch(
    root: Path,
    *,
    branch: str,
    verdict: str = "non-serializable",
    total_cycles: int = 1,
    phenomena: tuple[str, ...] = ("G2",),
    clean: bool = True,
) -> None:
    run = root / "runs" / "1"
    completed = run / "mocc-trace-pilot-receipt.json"
    job_result = run / "job-result.json"
    failure = run / "failure.json"
    if branch != "certified":
        completed.unlink()
        job_result.unlink()
    if branch == "certified":
        return
    if branch == "non_serializable":
        _write_json(
            failure,
            {
                "schema_version": LEDGER.FAILURE_SCHEMA_VERSION,
                "stage": "verifier",
                "rc": 1,
                "pbs_jobid": "0:job-1",
            },
        )
    elif branch == "indeterminate":
        _write_json(
            failure,
            {
                "schema_version": LEDGER.FAILURE_SCHEMA_VERSION,
                "stage": "verifier",
                "rc": 3,
                "pbs_jobid": "0:job-1",
            },
        )
        verdict = "indeterminate"
    elif branch == "verifier_infra":
        _write_json(
            failure,
            {
                "schema_version": LEDGER.FAILURE_SCHEMA_VERSION,
                "stage": "verifier",
                "rc": 2,
                "pbs_jobid": "0:job-1",
            },
        )
        verdict = "unknown"
    elif branch == "stage_failure":
        _write_json(
            failure,
            {
                "schema_version": LEDGER.FAILURE_SCHEMA_VERSION,
                "stage": "build",
                "rc": 17,
                "pbs_jobid": "0:job-1",
            },
        )
        (run / "verifier.json").unlink()
        return
    elif branch == "no_verdict":
        (run / "verifier.json").unlink()
        return
    else:  # pragma: no cover - fixture misuse
        raise AssertionError(branch)
    _write_json(
        run / "verifier.json",
        _verifier_result(
            verdict=verdict,
            total_cycles=total_cycles,
            phenomena=phenomena,
            clean=clean,
        ),
    )


@pytest.mark.parametrize(
    "branch",
    [
        "certified",
        "non_serializable",
        "indeterminate",
        "verifier_infra",
        "stage_failure",
        "no_verdict",
    ],
    ids=[
        "certified",
        "non-serializable",
        "indeterminate",
        "verifier-infra",
        "stage-failure",
        "no-verdict",
    ],
)
def test_classification_enum_all_branches(tmp_path: Path, branch: str) -> None:
    root = _make_study(tmp_path / "study")
    _configure_branch(root, branch=branch)
    payload = LEDGER.build_ledger(root)
    row = payload["runs"][0]
    assert row["classification"] == branch
    expected_count = LEDGER.PLANNED_N if branch == "certified" else 1
    assert payload["summary"]["classification_counts"][branch] == expected_count
    if branch == "stage_failure":
        assert row["failure_stage"] == "build"
        assert row["failure_rc"] == 17
    if branch in LEDGER.EXCLUDED_CLASSIFICATIONS:
        assert payload["summary"]["exclusions"][branch] == {
            "count": 1,
            "ordinals": [1],
        }


def test_rc1_g2_without_completed_receipt_enters_m_and_k(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    _configure_branch(root, branch="non_serializable")
    payload = LEDGER.build_ledger(root)
    row = payload["runs"][0]
    assert not (root / "runs/1/mocc-trace-pilot-receipt.json").exists()
    assert row["classification"] == "non_serializable"
    assert row["in_denominator"] is True
    assert row["in_numerator"] is True
    assert row["host"] == "host-1"
    assert payload["summary"]["m"] == 42
    assert payload["summary"]["k"] == 1
    assert payload["estimates"]["k_over_N"] == {
        "numerator": 1,
        "denominator": 42,
        "value": 1 / 42,
    }
    assert (
        payload["study"]["preregistration_sha256"]
        == LEDGER.FROZEN_PREREGISTRATION_SHA256
    )
    assert row["artifact_sha256"]["submit-receipt.json"] == hashlib.sha256(
        (root / "runs/1/submit-receipt.json").read_bytes()
    ).hexdigest()
    assert set(row["artifact_sha256"]) == {
        "failure.json",
        "reservation.json",
        "submit-receipt.json",
        "verifier.json",
    }
    by_host = {
        entry["host"]: (entry["k"], entry["m"])
        for entry in payload["secondary_analysis_e"]["by_host"]
    }
    assert by_host["host-1"] == (1, 24)


def test_g0_g1c_only_enters_m_but_not_k(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    _configure_branch(
        root,
        branch="non_serializable",
        total_cycles=2,
        phenomena=("G0", "G1c"),
    )
    payload = LEDGER.build_ledger(root)
    row = payload["runs"][0]
    assert row["in_denominator"] is True
    assert row["in_numerator"] is False
    assert payload["summary"]["m"] == 42
    assert payload["summary"]["k"] == 0
    assert payload["summary"]["g0_g1c_only"] == {
        "count": 1,
        "ordinals": [1],
    }
    assert payload["summary"]["reported_phenomena_counts"] == {
        "G0": 1,
        "G1c": 1,
    }


@pytest.mark.parametrize(
    ("verdict", "total_cycles"),
    [
        ("serializable", 1),
        ("non-serializable", 0),
    ],
    ids=["wrong-verdict", "zero-cycles"],
)
def test_each_other_numerator_conjunct_is_required(
    verdict: str, total_cycles: int
) -> None:
    result = {
        "verdict": verdict,
        "total_cycles": total_cycles,
    }
    assert not LEDGER.is_g2_numerator(
        "non_serializable", result, ("G2",)
    )


def test_unclean_nonserializable_g2_still_enters_k(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    _configure_branch(root, branch="non_serializable", clean=False)
    payload = LEDGER.build_ledger(root)
    row = payload["runs"][0]
    assert row["integrity_clean"] is False
    assert row["in_denominator"] is True
    assert row["in_numerator"] is True
    assert payload["summary"]["k"] == 1


def test_multiple_g2_witnesses_count_once_per_run(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    _configure_branch(
        root,
        branch="non_serializable",
        total_cycles=3,
        phenomena=("G2", "G2", "G0"),
    )
    payload = LEDGER.build_ledger(root)
    assert payload["runs"][0]["anomaly_count"] == 3
    assert payload["summary"]["reported_phenomena_counts"] == {"G0": 1, "G2": 2}
    assert payload["summary"]["k"] == 1


def test_closure_accepts_42_frozen_and_reports_two_exclusions(
    tmp_path: Path,
) -> None:
    root = _make_study(tmp_path / "study")
    payload = LEDGER.build_ledger(root)
    closure = payload["submission_closure"]
    assert closure["enumerated_submission_count"] == 44
    assert closure["frozen_commit_submission_count"] == 42
    assert set(closure["frozen_commit_nonces"]) == {
        _nonce(ordinal) for ordinal in range(1, 43)
    }
    assert len(closure["excluded_submissions"]) == 2
    assert {
        tuple(excluded.keys()) for excluded in closure["excluded_submissions"]
    } == {("nonce", "source_commit", "reason")}
    assert all(
        excluded["source_commit"] == "0" * 40
        and "source_commit differs" in excluded["reason"]
        for excluded in closure["excluded_submissions"]
    )


def test_closure_rejects_missing_canonical_submissions(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    (root / "submissions").rename(root / "not-submissions")
    with pytest.raises(
        LEDGER.LedgerError, match="canonical submissions directory is required"
    ):
        LEDGER.build_ledger(root)


def test_closure_rejects_43rd_frozen_submission(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    nonce = "f" * 32
    _write_json(
        root / "submissions" / nonce / "submit-receipt.json",
        _submit_receipt(
            nonce=nonce,
            request_id="job-43",
            source_commit=LEDGER.FROZEN_COMMIT,
        ),
    )
    with pytest.raises(
        LEDGER.LedgerError,
        match="frozen commit must contain exactly 42 receipts, got 43",
    ):
        LEDGER.build_ledger(root)


def test_closure_rejects_nonce_set_mismatch(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    ledger_path = root / "submission-ledger.tsv"
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    fields = lines[1].split("\t")
    fields[2] = "f" * 32
    lines[1] = "\t".join(fields)
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(
        LEDGER.LedgerError,
        match="ledger and frozen canonical submission nonce sets must match exactly",
    ):
        LEDGER.build_ledger(root)


def test_closure_rejects_source_commit_mismatch(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    receipt = root / "runs/1/submit-receipt.json"
    value = json.loads(receipt.read_text(encoding="utf-8"))
    value["source_commit"] = "0" * 40
    _write_json(receipt, value)
    with pytest.raises(
        LEDGER.LedgerError, match="source_commit must equal frozen commit"
    ):
        LEDGER.build_ledger(root)


def test_closure_rejects_ledger_row_shortage(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    path = root / "submission-ledger.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(
        LEDGER.LedgerError, match="row count must be exactly 42, got 41"
    ):
        LEDGER.build_ledger(root)


def test_preregistration_pin_accepts_frozen_bytes(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    payload = LEDGER.build_ledger(root)
    assert (
        payload["study"]["preregistration_sha256"]
        == LEDGER.FROZEN_PREREGISTRATION_SHA256
    )


def test_preregistration_pin_rejects_modified_bytes(tmp_path: Path) -> None:
    root = _make_study(tmp_path / "study")
    path = root / "pre-registration.md"
    path.write_bytes(path.read_bytes() + b"modified\n")
    with pytest.raises(
        LEDGER.LedgerError, match="pre-registration SHA-256 must equal frozen pin"
    ):
        LEDGER.build_ledger(root)


def test_denominator_accepts_consistent_verdicts_and_exact_schemas(
    tmp_path: Path,
) -> None:
    root = _make_study(tmp_path / "study")
    _configure_branch(root, branch="non_serializable")
    payload = LEDGER.build_ledger(root)
    assert payload["summary"]["m"] == 42
    assert payload["runs"][0]["verdict"] == "non-serializable"
    assert payload["runs"][1]["verdict"] == "serializable"


@pytest.mark.parametrize(
    ("artifact", "branch", "message"),
    [
        ("mocc-trace-pilot-receipt.json", "certified", "pilot receipt"),
        ("job-result.json", "certified", "job-result"),
        ("failure.json", "non_serializable", "failure"),
    ],
    ids=["pilot-v3", "job-result-v2", "failure-v1"],
)
def test_exact_study_schema_versions_are_required(
    tmp_path: Path, artifact: str, branch: str, message: str
) -> None:
    root = _make_study(tmp_path / "study")
    if branch != "certified":
        _configure_branch(root, branch=branch)
    path = root / "runs" / "1" / artifact
    value = json.loads(path.read_text(encoding="utf-8"))
    value["schema_version"] = "unknown/v999"
    _write_json(path, value)
    with pytest.raises(LEDGER.LedgerError, match=f"{message} schema_version"):
        LEDGER.build_ledger(root)


@pytest.mark.parametrize(
    "case",
    ["completed-nonserial", "rc1-unknown", "rc3-terminal"],
    ids=["completed-nonserial", "rc1-unknown", "rc3-terminal"],
)
def test_verdict_and_artifact_contradictions_fail_closed(
    tmp_path: Path, case: str
) -> None:
    root = _make_study(tmp_path / "study")
    if case == "completed-nonserial":
        _write_json(
            root / "runs/1/verifier.json",
            _verifier_result(
                verdict="non-serializable", total_cycles=1, phenomena=("G2",)
            ),
        )
        message = "completed pilot receipt requires verifier verdict serializable"
    elif case == "rc1-unknown":
        _configure_branch(root, branch="non_serializable", verdict="unknown")
        message = "verifier rc=1 requires no completed receipt"
    else:
        _configure_branch(root, branch="indeterminate")
        _write_json(root / "runs/1/verifier.json", _verifier_result())
        message = "verifier failure other than rc=1 contradicts a terminal verdict"
    with pytest.raises(LEDGER.LedgerError, match=message):
        LEDGER.build_ledger(root)


def test_identity_accepts_bound_ordinal_batch_request_and_host(
    tmp_path: Path,
) -> None:
    root = _make_study(tmp_path / "study")
    payload = LEDGER.build_ledger(root)
    batches = payload["secondary_analysis_e"]["by_batch"]
    assert [entry["batch"] for entry in batches] == list(range(1, 8))
    assert all(
        entry["m"] == 6
        for entry in payload["secondary_analysis_e"]["by_batch"]
    )
    assert payload["runs"][0]["request_id"] == "job-1"
    assert payload["runs"][0]["host"] == "host-1"


@pytest.mark.parametrize(
    "case",
    ["request", "batch", "ordinal-dir", "host", "job-result"],
    ids=["request", "batch", "ordinal-dir", "host", "job-result"],
)
def test_identity_mismatches_fail_closed(tmp_path: Path, case: str) -> None:
    root = _make_study(tmp_path / "study")
    if case in {"request", "batch"}:
        path = root / "submission-ledger.tsv"
        lines = path.read_text(encoding="utf-8").splitlines()
        fields = lines[1].split("\t")
        fields[3 if case == "request" else 1] = (
            "wrong-request" if case == "request" else "2"
        )
        lines[1] = "\t".join(fields)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        message = "request_id must equal" if case == "request" else "six runs each"
    elif case == "ordinal-dir":
        (root / "runs/42").rename(root / "runs/43")
        message = "run directories must be exactly ordinals 1..42"
    elif case == "host":
        path = root / "runs/1/mocc-trace-pilot-receipt.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["pbs"]["hostname"] = "wrong-host"
        _write_json(path, value)
        message = "reservation host must equal pilot receipt"
    else:
        path = root / "runs/1/job-result.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["receipt_sha256"] = "0" * 64
        _write_json(path, value)
        message = "job-result receipt_sha256 must bind"
    with pytest.raises(LEDGER.LedgerError, match=message):
        LEDGER.build_ledger(root)


def test_clopper_pearson_known_values() -> None:
    lower_42, upper_42 = LEDGER.clopper_pearson(0, 42)
    assert lower_42 == 0.0
    assert upper_42 == pytest.approx(1.0 - 0.025 ** (1.0 / 42), abs=1e-15)
    lower_30, upper_30 = LEDGER.clopper_pearson(0, 30)
    assert lower_30 == 0.0
    assert upper_30 == pytest.approx(0.11570330822202779, abs=1e-15)
    assert LEDGER.clopper_pearson(9, 9)[1] == 1.0


def test_cli_stdout_and_output_are_create_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_study(tmp_path / "study")
    assert LEDGER.main(["--root", str(root)]) == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    assert stdout_payload["schema_version"] == LEDGER.SCHEMA_VERSION

    output = tmp_path / "ledger.json"
    assert LEDGER.main(["--root", str(root), "--output", str(output)]) == 0
    original = output.read_bytes()
    assert LEDGER.main(["--root", str(root), "--output", str(output)]) == 2
    assert output.read_bytes() == original
    assert "File exists" in capsys.readouterr().err


def _run() -> int:
    """Keep this new test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
