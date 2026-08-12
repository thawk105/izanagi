from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from orchestrator.campaign import reflux_source_closure as closure
from orchestrator.campaign.reflux_origin_ledger import AUTHORITY_RELATIVE_PATH
from orchestrator.campaign.s8b_descriptor import (
    canonical_descriptor_bytes,
    projection_record,
)
from orchestrator.tests.reflux_origin_fixture_builder import (
    build_authority_manifest,
    build_fixture_repository,
    build_source_closure_record,
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _manifest_origin_id(manifest: dict) -> str:
    return _digest(b"izanagi-reflux-origin-manifest/v2\0" + _canonical(manifest))


def _manifest_cell_key(manifest: dict) -> str:
    preimage = [
        manifest["workload"]["descriptor_sha256"],
        manifest["axis_semantics_sha256"],
        manifest["verifier_policy_sha256"],
        manifest["environment_contract_sha256"],
    ]
    return _digest(b"izanagi-reflux-origin-cell/v1\0" + _canonical(preimage))


def _authority_bytes(manifest: dict) -> bytes:
    return _canonical({
        "authority_schema": "izanagi-reflux-origin-authority/v2",
        "origins": [{
            "cell_key": _manifest_cell_key(manifest),
            "manifest": manifest,
            "origin_id": _manifest_origin_id(manifest),
        }],
    }) + b"\n"


def _run_git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repo), *arguments),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


@dataclass
class _Case:
    repo: Path
    raw_record: bytes
    record: dict
    manifest: dict
    report_cell: dict
    authority_blob_sha256: str
    receipt: dict
    artifact_paths: dict[str, Path]


_REFERENT_FILES = {
    "authority.workload.descriptor_sha256": "workload-descriptor.json",
    "axis_semantics_sha256": "axis-semantics.json",
    "verifier_policy_sha256": "verifier-policy.json",
    "environment_contract_sha256": "environment-contract.json",
}


def _make_case(
    tmp_path: Path,
    *,
    artifact_objects: dict[str, dict] | None = None,
    missing_artifacts: frozenset[str] = frozenset(),
    captured_contains_candidate: bool = False,
) -> _Case:
    fixture = build_fixture_repository(tmp_path / "f0")
    artifact_raw = {
        name: (fixture.root / "artifacts" / filename).read_bytes()
        for name, filename in _REFERENT_FILES.items()
    }
    for name, value in (artifact_objects or {}).items():
        artifact_raw[name] = _canonical(value)

    manifest = build_authority_manifest(
        workload__descriptor_sha256=_digest(
            artifact_raw["authority.workload.descriptor_sha256"]
        ),
        axis_semantics_sha256=_digest(artifact_raw["axis_semantics_sha256"]),
        verifier_policy_sha256=_digest(artifact_raw["verifier_policy_sha256"]),
        environment_contract_sha256=_digest(
            artifact_raw["environment_contract_sha256"]
        ),
    )
    origin_id = _manifest_origin_id(manifest)
    cell_key = _manifest_cell_key(manifest)
    candidate_authority = _authority_bytes(manifest)

    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.name", "fixture")
    _run_git(repo, "config", "user.email", "fixture@example.invalid")
    authority_path = repo / AUTHORITY_RELATIVE_PATH
    authority_path.parent.mkdir(parents=True)
    authority_path.write_bytes(
        candidate_authority
        if captured_contains_candidate
        else _canonical({
            "authority_schema": "izanagi-reflux-origin-authority/v2",
            "origins": [],
        }) + b"\n"
    )
    artifact_paths: dict[str, Path] = {}
    for name, filename in _REFERENT_FILES.items():
        path = repo / "artifacts" / filename
        artifact_paths[name] = path
        if name not in missing_artifacts:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(artifact_raw[name])
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "fixture source preimages")
    captured_oid = _run_git(repo, "rev-parse", "HEAD")

    overrides: dict[str, object] = {
        "captured_commit_oid": captured_oid,
        "authority_series_id": manifest["authority_series_id"],
        "origin_id": origin_id,
        "cell_key": cell_key,
    }
    for name in _REFERENT_FILES:
        overrides[f"referents__{name}__preimage_ref__sha256"] = _digest(
            artifact_raw[name]
        )
    record = build_source_closure_record(**overrides)
    raw_record = _canonical(record)
    descriptor = json.loads(
        artifact_raw["authority.workload.descriptor_sha256"].decode("utf-8")
    )
    report_cell = {
        "descriptor": descriptor,
        "descriptor_binding": {
            "output_sha256": manifest["workload"]["descriptor_sha256"]
        },
    }
    authority_blob_sha256 = _digest(candidate_authority)
    receipt = {
        "authority_blob_sha256": authority_blob_sha256,
        "origin_id": origin_id,
        "cell_key": cell_key,
        "source_closure_sha256": _digest(raw_record),
    }
    return _Case(
        repo=repo,
        raw_record=raw_record,
        record=record,
        manifest=manifest,
        report_cell=report_cell,
        authority_blob_sha256=authority_blob_sha256,
        receipt=receipt,
        artifact_paths=artifact_paths,
    )


def _validate(case: _Case) -> closure.ValidatedSourceClosure:
    return closure.validate_source_closure(
        case.raw_record,
        repo_root=case.repo,
        authority_manifest=case.manifest,
        report_cell=case.report_cell,
        candidate_authority_blob_sha256=case.authority_blob_sha256,
        human_approval_receipt=case.receipt,
    )


@pytest.fixture(autouse=True)
def _resolve_fixture_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    def resolve(contract_sha256: str):
        assert len(contract_sha256) == 64
        return object()

    monkeypatch.setattr(closure, "resolve_by_contract_sha256", resolve)


def test_positive_fixture_validates_all_issuance_checks(tmp_path: Path) -> None:
    case = _make_case(tmp_path)
    case.artifact_paths["axis_semantics_sha256"].write_bytes(b"working-tree poison")

    issued = _validate(case)

    assert issued.source_closure_sha256 == _digest(case.raw_record)
    assert issued.origin_id == case.record["origin_id"]
    assert issued.cell_key == case.record["cell_key"]
    assert closure.assert_issued_validated_source_closure(issued) is issued
    with pytest.raises(TypeError):
        replace(issued, cell_key="e" * 64)


def test_step1_resolves_full_commit_once_and_rejects_self_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    negative = _make_case(tmp_path, captured_contains_candidate=True)
    original_run = closure.subprocess.run
    resolution_calls = 0

    def counting_run(*args, **kwargs):
        nonlocal resolution_calls
        command = args[0]
        if "rev-parse" in command:
            resolution_calls += 1
        return original_run(*args, **kwargs)

    monkeypatch.setattr(closure.subprocess, "run", counting_run)
    with pytest.raises(closure.SourceClosureError, match="self-reference"):
        _validate(negative)
    assert resolution_calls == 1


def test_step2_rejects_blob_digest_mismatch_with_record(tmp_path: Path) -> None:
    case = _make_case(tmp_path)
    broken = copy.deepcopy(case.record)
    broken["referents"]["authority.workload.descriptor_sha256"]["preimage_ref"][
        "sha256"
    ] = "e" * 64
    case.raw_record = _canonical(broken)
    case.receipt["source_closure_sha256"] = _digest(case.raw_record)

    with pytest.raises(closure.SourceClosureError, match="closure record"):
        _validate(case)


def test_step2_rejects_blob_digest_mismatch_with_manifest(tmp_path: Path) -> None:
    case = _make_case(tmp_path)
    case.manifest = build_authority_manifest(workload__descriptor_sha256="e" * 64)

    with pytest.raises(closure.SourceClosureError, match="authority manifest"):
        _validate(case)


def test_step3_rejects_report_descriptor_projection_mismatch(tmp_path: Path) -> None:
    case = _make_case(tmp_path)
    case.report_cell["descriptor"]["workload"] = "different-cell"

    with pytest.raises(closure.SourceClosureError, match="report cell descriptor"):
        _validate(case)


def test_step4_rejects_axis_reason_order_even_with_matching_digest(
    tmp_path: Path,
) -> None:
    axis = {
        "schema_version": "izanagi-axis-semantics/v1",
        "marker": "trigger-gating",
        "reasons": [
            "update-absent",
            "lock-conflict",
            "readvali-tid",
            "readvali-locked",
            "node-vali",
        ],
        "wire": {"width": 5, "bit_order": "lsb-first", "masks": [0, 31]},
        "sentinel": "kUnset",
    }
    case = _make_case(
        tmp_path,
        artifact_objects={"axis_semantics_sha256": axis},
    )

    with pytest.raises(closure.SourceClosureError, match="axis.*semantics"):
        _validate(case)


def test_step5_rejects_verifier_pass_order_even_with_matching_digest(
    tmp_path: Path,
) -> None:
    verifier = {
        "schema_version": "izanagi-verifier-policy/v1",
        "ordered_passes": ["s2", "legacy"],
        "accepted": "all-passes-complete",
        "candidate_attributable_rejected": "single-normalized-witness-class",
        "fail_closed": True,
        "witness_class_cardinality": 1,
    }
    case = _make_case(
        tmp_path,
        artifact_objects={"verifier_policy_sha256": verifier},
    )

    with pytest.raises(closure.SourceClosureError, match="verifier.*policy"):
        _validate(case)


def test_step6_requires_unique_environment_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _make_case(tmp_path)

    def reject(_digest_value: str):
        raise RuntimeError("not unique")

    monkeypatch.setattr(closure, "resolve_by_contract_sha256", reject)
    with pytest.raises(closure.SourceClosureError, match="environment.*uniquely"):
        _validate(case)


def test_step7_rejects_rederived_cell_key_mismatch(tmp_path: Path) -> None:
    case = _make_case(tmp_path)
    broken = copy.deepcopy(case.record)
    broken["cell_key"] = "e" * 64
    case.raw_record = _canonical(broken)
    case.receipt["cell_key"] = "e" * 64
    case.receipt["source_closure_sha256"] = _digest(case.raw_record)

    with pytest.raises(closure.SourceClosureError, match="cell-key"):
        _validate(case)


def test_step8_rejects_approval_receipt_with_open_shape(tmp_path: Path) -> None:
    case = _make_case(tmp_path)
    case.receipt["approved_by"] = "self-asserted"

    with pytest.raises(closure.SourceClosureError, match="approval-receipt"):
        _validate(case)


@pytest.mark.parametrize(
    "missing",
    ["axis_semantics_sha256", "verifier_policy_sha256"],
)
def test_missing_axis_or_verifier_artifact_never_uses_fallback_digest(
    tmp_path: Path, missing: str,
) -> None:
    case = _make_case(tmp_path, missing_artifacts=frozenset({missing}))

    with pytest.raises(closure.SourceClosureError, match="artifact-absent"):
        _validate(case)


@pytest.mark.parametrize(
    ("target", "extra_key", "required_key"),
    [
        ("top", "sha256", "schema_version"),
        ("referents", "unexpected", "axis_semantics_sha256"),
        ("referent", "unexpected", "digest_rule"),
        ("preimage_ref", "unexpected", "sha256"),
    ],
)
def test_source_closure_exact_key_sets_reject_additions_and_removals(
    tmp_path: Path, target: str, extra_key: str, required_key: str,
) -> None:
    case = _make_case(tmp_path)
    broken = copy.deepcopy(case.record)
    referent = broken["referents"]["axis_semantics_sha256"]
    if target == "top":
        broken[extra_key] = "e" * 64
    elif target == "referents":
        broken["referents"][extra_key] = copy.deepcopy(referent)
    elif target == "referent":
        referent[extra_key] = "value"
    else:
        referent["preimage_ref"][extra_key] = "value"
    case.raw_record = _canonical(broken)

    with pytest.raises(closure.SourceClosureError, match="key set"):
        _validate(case)

    broken = copy.deepcopy(case.record)
    referent = broken["referents"]["axis_semantics_sha256"]
    if target == "top":
        del broken[required_key]
    elif target == "referents":
        del broken["referents"][required_key]
    elif target == "referent":
        del referent[required_key]
    else:
        del referent["preimage_ref"][required_key]
    case.raw_record = _canonical(broken)
    with pytest.raises(closure.SourceClosureError, match="key set"):
        _validate(case)


def test_source_closure_record_requires_exact_canonical_bytes(tmp_path: Path) -> None:
    case = _make_case(tmp_path)
    case.raw_record += b"\n"

    with pytest.raises(closure.SourceClosureError, match="canonical JSON"):
        _validate(case)


def test_validated_source_closure_cannot_be_plainly_constructed() -> None:
    with pytest.raises(TypeError, match="issuer-only"):
        closure.ValidatedSourceClosure(
            source_closure_sha256="a" * 64,
            captured_commit_oid="b" * 40,
            authority_series_id="series",
            origin_id="c" * 64,
            cell_key="d" * 64,
            referent_sha256s={},
            record_bytes=b"{}",
        )


def test_public_descriptor_canonicalizer_preserves_existing_projection_bytes() -> None:
    value = {"日本語": "値", "a": [True, None], "z": {"b": 2, "a": 1}}
    expected = '{"a":[true,null],"z":{"a":1,"b":2},"日本語":"値"}'.encode("utf-8")
    assert canonical_descriptor_bytes(value) == expected

    search_config = {"threads": 4, "records": 100_000}
    descriptor = {"schema_version": "fixture", "scale": {"threads": 4}}
    projected = projection_record(search_config, descriptor)
    assert projected["input_sha256"] == _digest(_canonical(search_config))
    assert projected["output_sha256"] == _digest(_canonical(descriptor))
