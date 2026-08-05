# -*- coding: utf-8 -*-
"""T-470 canonical acceptance receipt parser and tracked-byte verifier."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign import s8c_acceptance_receipt as receipt


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _head(repo: Path) -> str:
    result = _run(repo, "rev-parse", "HEAD")
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    assert _run(repo, "add", "-A").returncode == 0
    result = _run(repo, "commit", "-q", "-m", message)
    assert result.returncode == 0, result.stderr
    return _head(repo)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _run(repo, "init", "-q").returncode == 0
    assert _run(repo, "config", "user.email", "fixture@example.invalid").returncode == 0
    assert _run(repo, "config", "user.name", "Fixture").returncode == 0
    return repo


def _write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _receipt_fixture(
    tmp_path: Path,
    *,
    commit_receipt: bool,
) -> tuple[Path, Path, dict]:
    repo = _init_repo(tmp_path)
    manifest = repo / "input" / "manifest.json"
    manifest_sha = _write(manifest, b'{"fixture":"manifest"}\n')
    registry = repo / "output" / "s8c-trial-registry" / "registry.jsonl"
    registry_sha = _write(registry, b'{"fixture":"registry"}\n')
    lifecycle = repo / "output" / "s8c-trial-registry" / "lifecycle.jsonl"
    lifecycle_sha = _write(lifecycle, b'{"fixture":"lifecycle"}\n')

    trial_rows = []
    arms = ("on", "off", "swapped")
    for index in range(6):
        trial_id = f"trial-{index}"
        run = repo / "runs" / trial_id
        report_path = run / "report.json"
        journal_path = run / "attempts.jsonl"
        report_sha = _write(report_path, f"report-{index}\n".encode())
        journal_sha = _write(journal_path, f"journal-{index}\n".encode())
        trial_rows.append({
            "trial_id": trial_id,
            "arm": arms[index % 3],
            "holdout": "H1" if index < 3 else "H2",
            "campaign_id": f"campaign-{index}",
            "status": "complete",
            "measurement_head": "1" * 40,
            "report_path": report_path.relative_to(repo).as_posix(),
            "report_sha256": report_sha,
            "attempt_journal_path": journal_path.relative_to(repo).as_posix(),
            "attempt_journal_sha256": journal_sha,
        })
    introduction = _commit_all(repo, "referenced bytes")
    value = {
        "schema_version": receipt.SCHEMA_VERSION,
        "manifest_path": manifest.relative_to(repo).as_posix(),
        "manifest_sha256": manifest_sha,
        "prereg_commit": introduction,
        "activation_report_digest_sha256": "2" * 64,
        "registry_path": registry.relative_to(repo).as_posix(),
        "registry_blob_sha256": registry_sha,
        "registry_introduction_commit": introduction,
        "lifecycle_path": lifecycle.relative_to(repo).as_posix(),
        "lifecycle_prefix_bytes": len(lifecycle.read_bytes()),
        "lifecycle_prefix_sha256": lifecycle_sha,
        "certifying": False,
        "non_certifying_reason_codes": sorted(
            receipt.MANDATORY_NON_CERTIFYING_REASONS
        ),
        "trials": trial_rows,
    }
    receipt_path = repo.joinpath(
        *receipt.DEFAULT_RECEIPT_DIR.parts, f"{manifest_sha}.json"
    )
    _write(receipt_path, _canonical(value))
    if commit_receipt:
        _commit_all(repo, "acceptance receipt")
    return repo, receipt_path, value


def test_schema_parse_positive_is_canonical_and_exact(tmp_path: Path) -> None:
    _repo, path, value = _receipt_fixture(tmp_path, commit_receipt=False)
    parsed = receipt.parse_acceptance_receipt_bytes(path.read_bytes())
    assert parsed.schema_version == receipt.SCHEMA_VERSION
    assert parsed.manifest_sha256 == value["manifest_sha256"]
    assert [trial.trial_id for trial in parsed.trials] == [
        f"trial-{index}" for index in range(6)
    ]


@pytest.mark.parametrize(
    "mutation",
    ["unknown-key", "duplicate-key", "nan", "noncanonical-path"],
)
def test_strict_parse_rejects_schema_json_and_path_mutations(
    tmp_path: Path,
    mutation: str,
) -> None:
    _repo, path, value = _receipt_fixture(tmp_path, commit_receipt=False)
    if mutation == "unknown-key":
        value["unknown"] = True
        raw = _canonical(value)
    elif mutation == "duplicate-key":
        raw = path.read_bytes().replace(
            b'{"activation_report_digest_sha256":',
            b'{"schema_version":"decoy","activation_report_digest_sha256":',
            1,
        )
    elif mutation == "nan":
        raw = path.read_bytes().replace(b'"certifying":false', b'"certifying":NaN')
    else:
        value["registry_path"] = "output/../registry.jsonl"
        raw = _canonical(value)
    with pytest.raises(receipt.AcceptanceReceiptError):
        receipt.parse_acceptance_receipt_bytes(raw)


def test_tracked_receipt_and_all_referenced_bytes_verify_positive(
    tmp_path: Path,
) -> None:
    repo, path, _value = _receipt_fixture(tmp_path, commit_receipt=True)
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.path == path
    assert verified.raw_bytes == path.read_bytes()
    assert verified.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert receipt.require_current_verified_receipt(verified).sha256 == verified.sha256


def test_m12_untracked_receipt_is_rejected(tmp_path: Path) -> None:
    repo, path, _value = _receipt_fixture(tmp_path, commit_receipt=False)
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-untracked\] receipt is not tracked at Git HEAD$",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_receipt_path_must_match_manifest_sha256(tmp_path: Path) -> None:
    repo, path, value = _receipt_fixture(tmp_path, commit_receipt=False)
    value["manifest_sha256"] = "f" * 64
    path.write_bytes(_canonical(value))
    with pytest.raises(
        receipt.AcceptanceReceiptError, match=r"\[receipt-path\] "
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


@pytest.mark.parametrize(
    "reference", ["manifest", "registry", "lifecycle", "report", "journal"],
)
def test_m13_reference_bytes_are_rehashed_not_self_compared(
    tmp_path: Path,
    reference: str,
) -> None:
    repo, path, value = _receipt_fixture(tmp_path, commit_receipt=True)
    if reference in {"manifest", "registry", "lifecycle"}:
        target = repo / value[f"{reference}_path"]
    else:
        selected = value["trials"][0]
        key = "report_path" if reference == "report" else "attempt_journal_path"
        target = repo / selected[key]
    original = target.read_bytes()
    if reference == "lifecycle":
        appended = original + b'{"later":"trial"}\n'
        target.write_bytes(appended)
        value["lifecycle_prefix_bytes"] = len(appended)
        value["lifecycle_prefix_sha256"] = hashlib.sha256(appended).hexdigest()
        path.write_bytes(_canonical(value))
        assert _run(
            repo, "add", "--", path.relative_to(repo).as_posix(),
        ).returncode == 0
        committed = _run(repo, "commit", "-q", "-m", "extend receipt prefix")
        assert committed.returncode == 0, committed.stderr
        target.write_bytes(original + b'{"later":"triaz"}\n')
    else:
        target.write_bytes(b"x" + original[1:])
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"\[receipt-reference-prefix\] "
            if reference == "lifecycle"
            else r"\[receipt-reference-hash\] "
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_working_receipt_bytes_must_equal_tracked_head_bytes(tmp_path: Path) -> None:
    repo, path, value = _receipt_fixture(tmp_path, commit_receipt=True)
    value["non_certifying_reason_codes"].append("working-only-change")
    value["non_certifying_reason_codes"].sort()
    path.write_bytes(_canonical(value))
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-head-mismatch\] working receipt bytes "
               r"differ from Git HEAD$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_m15_empty_non_certifying_reason_codes_are_rejected(
    tmp_path: Path,
) -> None:
    _repo, _path, value = _receipt_fixture(tmp_path, commit_receipt=False)
    value["non_certifying_reason_codes"] = []
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-reason-list\] ",
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical(value))


def test_m15_nonempty_reason_validator_is_independent() -> None:
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-reason-list\] reason codes must be a non-empty "
               r"sorted unique string list$"),
    ):
        receipt._require_nonempty_reason_codes([])


def test_m15_mandatory_reason_validator_is_independent() -> None:
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-mandatory-reasons\] mandatory unresolved-authority "
               r"reason codes are absent$"),
    ):
        receipt._require_mandatory_reason_codes(("some-other-reason",))


def test_lifecycle_append_after_receipt_keeps_prefix_valid(tmp_path: Path) -> None:
    repo, path, value = _receipt_fixture(tmp_path, commit_receipt=True)
    lifecycle = repo / value["lifecycle_path"]
    lifecycle.write_bytes(lifecycle.read_bytes() + b'{"later":"trial"}\n')
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.lifecycle_prefix_bytes < lifecycle.stat().st_size


@pytest.mark.parametrize("history_attack", ["delete-recreate", "modify-revert"])
def test_lifecycle_committed_history_attack_invalidates_receipt(
    tmp_path: Path,
    history_attack: str,
) -> None:
    repo, path, value = _receipt_fixture(tmp_path, commit_receipt=True)
    lifecycle = repo / value["lifecycle_path"]
    original = lifecycle.read_bytes()
    if history_attack == "delete-recreate":
        lifecycle.unlink()
        _commit_all(repo, "delete lifecycle")
    else:
        lifecycle.write_bytes(b"x" + original[1:])
        _commit_all(repo, "modify lifecycle")
    lifecycle.write_bytes(original)
    _commit_all(repo, "restore lifecycle")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-history\] lifecycle ",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v1_contract_has_no_synthetic_certifying_positive(tmp_path: Path) -> None:
    _repo, _path, value = _receipt_fixture(tmp_path, commit_receipt=False)
    value["certifying"] = True
    with pytest.raises(
        receipt.AcceptanceReceiptError, match=r"\[receipt-certifying\] "
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical(value))
