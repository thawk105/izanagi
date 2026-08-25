# -*- coding: utf-8 -*-
"""T-822 receipt-v2 descriptor proof and reason-drop controls."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign import s8c_acceptance_receipt as receipt


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_line(value: object) -> bytes:
    return _canonical(value) + b"\n"


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _commit_all(repo: Path, message: str) -> str:
    assert _run(repo, "add", "-A").returncode == 0
    committed = _run(repo, "commit", "-q", "-m", message)
    assert committed.returncode == 0, committed.stderr
    head = _run(repo, "rev-parse", "HEAD")
    assert head.returncode == 0, head.stderr
    return head.stdout.strip()


def _write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _binding_digest(*, holdout: str, arm: str, content_digest: str) -> str:
    return hashlib.sha256(
        b"izanagi-s8c-arm-binding/v1\0"
        + holdout.encode("ascii")
        + arm.encode("ascii")
        + content_digest.encode("ascii")
    ).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict]:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _run(repo, "init", "-q").returncode == 0
    assert _run(repo, "config", "user.email", "fixture@example.invalid").returncode == 0
    assert _run(repo, "config", "user.name", "Fixture").returncode == 0

    manifest_path = repo / "input" / "manifest.json"
    manifest_sha = _write(manifest_path, b'{"fixture":"manifest"}\n')
    registry_path = repo / "output" / "s8c-trial-registry" / "registry.jsonl"
    registry_sha = _write(registry_path, b'{"fixture":"registry"}\n')
    lifecycle_path = repo / "output" / "s8c-trial-registry" / "lifecycle.jsonl"
    lifecycle_sha = _write(lifecycle_path, b'{"fixture":"lifecycle"}\n')

    trial_rows = []
    for holdout in ("H1", "H2"):
        for arm in ("on", "off", "swapped"):
            trial_id = f"trial-{holdout.lower()}-{arm}"
            campaign_id = f"campaign-{holdout.lower()}-{arm}"
            workload = f"workload-{holdout.lower()}"
            descriptor = {
                "schema_version": "8b-v1",
                "fixture": {"holdout": holdout, "arm": arm},
            }
            content_digest = hashlib.sha256(_canonical(descriptor)).hexdigest()
            arm_execution = {
                "input_schema_version": "8b-v1",
                "content_digest_sha256": content_digest,
                "arm_binding_digest_sha256": _binding_digest(
                    holdout=holdout, arm=arm, content_digest=content_digest,
                ),
            }
            report = {
                "trial_id": trial_id,
                "measurement_head": "1" * 40,
                "status": "complete",
                "arm_execution": arm_execution,
                "launch_admission": {
                    "binding": {
                        "arm": arm,
                        "holdout": holdout,
                        "campaign_id": campaign_id,
                        "workload": workload,
                    },
                },
                "cells": [{"workload": workload, "descriptor": descriptor}],
            }
            journal = _canonical_line({
                "event": "run-start",
                "trial_id": trial_id,
                "arm_execution": arm_execution,
            })
            run = repo / "runs" / trial_id
            report_path = run / "report.json"
            journal_path = run / "attempts.jsonl"
            report_sha = _write(report_path, _canonical(report))
            journal_sha = _write(journal_path, journal)
            trial_rows.append({
                "trial_id": trial_id,
                "arm": arm,
                "holdout": holdout,
                "campaign_id": campaign_id,
                "status": "complete",
                "measurement_head": "1" * 40,
                "report_path": report_path.relative_to(repo).as_posix(),
                "report_sha256": report_sha,
                "attempt_journal_path": journal_path.relative_to(repo).as_posix(),
                "attempt_journal_sha256": journal_sha,
                "arm_execution": copy.deepcopy(arm_execution),
            })

    introduction = _commit_all(repo, "receipt references")
    value = {
        "schema_version": receipt.PREVIOUS_SCHEMA_VERSION,
        "manifest_path": manifest_path.relative_to(repo).as_posix(),
        "manifest_sha256": manifest_sha,
        "prereg_commit": introduction,
        "activation_report_digest_sha256": "2" * 64,
        "registry_path": registry_path.relative_to(repo).as_posix(),
        "registry_blob_sha256": registry_sha,
        "registry_introduction_commit": introduction,
        "lifecycle_path": lifecycle_path.relative_to(repo).as_posix(),
        "lifecycle_prefix_bytes": len(lifecycle_path.read_bytes()),
        "lifecycle_prefix_sha256": lifecycle_sha,
        "certifying": False,
        "non_certifying_reason_codes": ["t468-approval-authority-absent"],
        "trials": sorted(trial_rows, key=lambda row: row["trial_id"]),
    }
    receipt_path = repo.joinpath(
        *receipt.DEFAULT_RECEIPT_DIR.parts, f"{manifest_sha}.json",
    )
    _write(receipt_path, _canonical_line(value))
    _commit_all(repo, "receipt v2")
    return repo, receipt_path, value


def _rewrite_receipt(repo: Path, path: Path, value: dict, message: str) -> None:
    path.write_bytes(_canonical_line(value))
    _commit_all(repo, message)


def _trial(value: dict, holdout: str, arm: str) -> dict:
    return next(
        row for row in value["trials"]
        if row["holdout"] == holdout and row["arm"] == arm
    )


def _cross_binding_aggregate_for_schema(value: dict, schema_version: str) -> str:
    leaves = [
        {
            "trial_id": row["trial_id"],
            "receipt_sha256": row["cross_binding_receipt_sha256"],
        }
        for row in value["trials"]
    ]
    payload = {
        "schema_version": schema_version,
        "trials": sorted(leaves, key=lambda leaf: leaf["trial_id"]),
    }
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _upgrade_to_current(value: dict) -> None:
    value["schema_version"] = receipt.SCHEMA_VERSION
    for index, row in enumerate(value["trials"]):
        row["cross_binding_receipt_sha256"] = hashlib.sha256(
            f"cross-binding-leaf-{index}".encode("ascii")
        ).hexdigest()
    value["cross_binding_receipt_sha256"] = (
        receipt.cross_binding_aggregate_sha256([
            {
                "trial_id": row["trial_id"],
                "receipt_sha256": row["cross_binding_receipt_sha256"],
            }
            for row in value["trials"]
        ])
    )


def _synchronize_arm_execution(
    repo: Path,
    row: dict,
    *,
    descriptor: dict | None = None,
) -> None:
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["arm_execution"] = copy.deepcopy(row["arm_execution"])
    if descriptor is not None:
        report["cells"][0]["descriptor"] = copy.deepcopy(descriptor)
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()

    journal_path = repo / row["attempt_journal_path"]
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
    run_start = next(event for event in events if event.get("event") == "run-start")
    run_start["arm_execution"] = copy.deepcopy(row["arm_execution"])
    journal_bytes = b"".join(_canonical_line(event) for event in events)
    journal_path.write_bytes(journal_bytes)
    row["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()


def _origin_projection(*, arm_binding_digest: str) -> dict:
    return {
        "schema_version": "OriginTerminalProjection/v1",
        "reason_code": "P6Unavailable",
        "formal_receipt_sha256": "7" * 64,
        "evidence_root_sha256": "8" * 64,
        "authority_blob_sha256": "9" * 64,
        "origin_id": "fixture-origin",
        "cell_key": "fixture-cell",
        "terminal_payload_sha256": "a" * 64,
        "arm_binding_digest_sha256": arm_binding_digest,
    }


def test_verifier_keeps_registry_and_layer3_import_independence() -> None:
    tree = ast.parse(Path(receipt.__file__).read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for name in (node.module or "", *(alias.name for alias in node.names))
    }
    assert not any(
        name.endswith("trial_registry") or name.endswith("layer3_report")
        for name in imported
    )


def test_v2_producer_equivalent_full_verify_drops_only_c02(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.PREVIOUS_SCHEMA_VERSION
    assert verified.receipt.certifying is False
    assert verified.receipt.non_certifying_reason_codes == (
        "t468-approval-authority-absent",
    )
    assert all(trial.arm_execution is not None for trial in verified.trials)
    value["certifying"] = True
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-certifying\] receipts are structurally non-certifying$",
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical_line(value))


def test_pairwise_collision_is_rejected_after_binding_recalculation(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    source = _trial(value, "H1", "on")
    target = _trial(value, "H1", "off")
    collided = source["arm_execution"]["content_digest_sha256"]
    target["arm_execution"]["content_digest_sha256"] = collided
    target["arm_execution"]["arm_binding_digest_sha256"] = _binding_digest(
        holdout="H1", arm="off", content_digest=collided,
    )
    source_report = json.loads((repo / source["report_path"]).read_bytes())
    _synchronize_arm_execution(
        repo,
        target,
        descriptor=source_report["cells"][0]["descriptor"],
    )
    _rewrite_receipt(repo, path, value, "coherent pairwise collision")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-arm-binding\] H1 content digests are not "
               r"pairwise distinct$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_receipt_digest_divergence_is_attributed_to_report_descriptor(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H1", "on")
    row["arm_execution"]["content_digest_sha256"] = "f" * 64
    row["arm_execution"]["arm_binding_digest_sha256"] = _binding_digest(
        holdout="H1", arm="on", content_digest="f" * 64,
    )
    _synchronize_arm_execution(repo, row)
    _rewrite_receipt(repo, path, value, "coherent digest descriptor divergence")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-arm-binding\] cell descriptor content digest "
               r"differs from receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    assert all(set(row["arm_execution"]) == {
        "input_schema_version",
        "content_digest_sha256",
        "arm_binding_digest_sha256",
    } for row in value["trials"])
    row = _trial(value, "H2", "off")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["cells"] = []
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "partial receipt without descriptor proof")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-mandatory-reasons\] c02-arm-binding-unproven "
               r"was dropped without descriptor proof$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_origin_terminal_projection_is_retained_and_reverified(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "on")
    projection = _origin_projection(
        arm_binding_digest=row["arm_execution"]["arm_binding_digest_sha256"],
    )
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["origin_terminal_projection"] = copy.deepcopy(projection)
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    row["origin_terminal_projection"] = copy.deepcopy(projection)
    _rewrite_receipt(repo, path, value, "matching origin terminal projection")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    parsed_row = next(
        trial for trial in verified.trials if trial.trial_id == row["trial_id"]
    )
    assert parsed_row.origin_terminal_projection == projection

    row["origin_terminal_projection"]["formal_receipt_sha256"] = "b" * 64
    _rewrite_receipt(repo, path, value, "divergent origin terminal projection")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-origin-projection\] trial report "
               r"origin_terminal_projection differs from receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_run_start_mismatch_is_rejected_after_reference_hashes_match(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "swapped")
    journal_path = repo / row["attempt_journal_path"]
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
    events[0]["arm_execution"]["content_digest_sha256"] = "e" * 64
    journal_bytes = b"".join(_canonical_line(event) for event in events)
    journal_path.write_bytes(journal_bytes)
    row["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "run-start mismatch")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-arm-binding\] run-start arm_execution differs "
               r"from report and receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_trial_report_arm_execution_mismatch_is_rejected_after_reference_hashes_match(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "swapped")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["arm_execution"]["content_digest_sha256"] = "e" * 64
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "trial report arm_execution mismatch")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"^\[receipt-arm-binding\] trial report arm_execution differs "
               r"from receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v2_never_routes_through_v1_mandatory_reason_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, path, _value = _fixture(tmp_path)

    def reject_legacy_path(_reasons: object) -> None:
        raise AssertionError("v2 bytes reached the v1 mandatory-reason path")

    monkeypatch.setattr(
        receipt, "_require_legacy_mandatory_reason_codes", reject_legacy_path,
    )
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.PREVIOUS_SCHEMA_VERSION


def test_v3_requires_cross_binding_receipt_sha256(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(value)
    _rewrite_receipt(repo, path, value, "receipt v4")
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.SCHEMA_VERSION
    assert verified.receipt.cross_binding_receipt_sha256 == value[
        "cross_binding_receipt_sha256"
    ]

    value.pop("cross_binding_receipt_sha256")
    _rewrite_receipt(repo, path, value, "receipt v4 missing aggregate")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-schema\] receipt key set differs: ",
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical_line(value))


@pytest.mark.parametrize(
    "schema_version",
    [
        receipt.LEGACY_SCHEMA_VERSION,
        receipt.PREVIOUS_SCHEMA_VERSION,
        receipt.CROSS_BINDING_V1_SCHEMA_VERSION,
        receipt.SCHEMA_VERSION,
    ],
)
def test_missing_schema_version_is_acceptance_receipt_error(
    tmp_path: Path, schema_version: str,
) -> None:
    _repo, _path, value = _fixture(tmp_path)
    value["schema_version"] = schema_version
    value.pop("schema_version")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"^\[receipt-schema\] receipt\.schema_version is missing$",
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical_line(value))


def test_v3_aggregate_is_recomputed_from_trial_leaves(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(value)
    _rewrite_receipt(repo, path, value, "receipt v4 aggregate")
    value["cross_binding_receipt_sha256"] = "f" * 64
    _rewrite_receipt(repo, path, value, "receipt v4 forged aggregate")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"\[receipt-cross-binding\] top-level cross-binding aggregate "
            r"differs from trial leaves$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v3_remains_bound_to_cross_binding_v1_domain(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    value["schema_version"] = receipt.CROSS_BINDING_V1_SCHEMA_VERSION
    for index, row in enumerate(value["trials"]):
        row["cross_binding_receipt_sha256"] = hashlib.sha256(
            f"legacy-cross-binding-leaf-{index}".encode("ascii")
        ).hexdigest()
    legacy_aggregate = _cross_binding_aggregate_for_schema(
        value, receipt.LEGACY_CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
    )
    current_aggregate = _cross_binding_aggregate_for_schema(
        value, receipt.CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
    )
    assert legacy_aggregate != current_aggregate
    value["cross_binding_receipt_sha256"] = legacy_aggregate
    _rewrite_receipt(repo, path, value, "legacy receipt v3 domain")
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.CROSS_BINDING_V1_SCHEMA_VERSION

    value["cross_binding_receipt_sha256"] = current_aggregate
    _rewrite_receipt(repo, path, value, "legacy receipt v3 with v2 domain")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-cross-binding\] top-level cross-binding aggregate differs",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_binding_digest_is_rederived_from_self_consistent_three_way_claim(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "off")
    forged = "d" * 64
    row["arm_execution"]["arm_binding_digest_sha256"] = forged
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["arm_execution"]["arm_binding_digest_sha256"] = forged
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    journal_path = repo / row["attempt_journal_path"]
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
    events[0]["arm_execution"]["arm_binding_digest_sha256"] = forged
    journal_bytes = b"".join(_canonical_line(event) for event in events)
    journal_path.write_bytes(journal_bytes)
    row["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "self-consistent forged binding")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-arm-binding\] arm binding digest differs from receipt inputs$",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
