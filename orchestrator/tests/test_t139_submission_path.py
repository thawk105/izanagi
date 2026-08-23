"""T-139 private receipt admission/publish authority integration tests."""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from orchestrator.preregistration import approval_payload as approval
from orchestrator.preregistration.blobref import BlobRef, BlobRefError, read_pinned_blob
from orchestrator.submission_gate import _binding, _manifest


_ROOT = Path(__file__).resolve().parents[2]
_UNIT3 = importlib.import_module("orchestrator.tests.test_t338_submission_gate_unit3")


def _clone_repository(tmp_path: Path) -> Path:
    root = tmp_path / "authority-repo"
    subprocess.run(
        ["/usr/bin/git", "clone", "--no-local", "-q", os.fspath(_ROOT), os.fspath(root)],
        env=_UNIT3._git_env(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return root


def _authority_fixture(tmp_path: Path) -> SimpleNamespace:
    seed_parent = tmp_path / "seed"
    seed_parent.mkdir()
    seed = _UNIT3._make_git_fixture(seed_parent)
    root = _clone_repository(tmp_path)
    approved = _manifest._load_approved_manifest(os.fspath(root))
    content_commit = _UNIT3._run(root, "rev-parse", "HEAD")
    (root / "t139-test-effective.txt").write_bytes(b"effective\n")
    effective_commit = _UNIT3._commit(root, "effective", "t139-test-effective.txt")
    for path, data in seed.tree_files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    _UNIT3._run(root, "add", "-f", *seed.tree_files)
    _UNIT3._run(root, "commit", "-m", "measurement artifacts")
    head_commit = _UNIT3._run(root, "rev-parse", "HEAD")
    core_ref = BlobRef(approved.target_core.path, content_commit, approved.target_core.sha256)
    addendum_ref = BlobRef(
        approved.approved_blobs["addendum_a"].path,
        content_commit,
        approved.approved_blobs["addendum_a"].sha256,
    )
    binding = _binding._resolve_effective_preregistration(
        root,
        core_ref=core_ref,
        addendum_a=addendum_ref,
        addendum_b=None,
        prereg_effective_commit=effective_commit,
    )
    schema_alias = root / "prereg/receipt-schema.json"
    schema_alias.parent.mkdir(exist_ok=True)
    schema_alias.write_bytes(read_pinned_blob(root, binding.record.receipt_schema))
    return SimpleNamespace(
        root=root,
        content_commit=content_commit,
        effective_commit=effective_commit,
        head_commit=head_commit,
        tree_sha=_UNIT3._run(root, "rev-parse", f"{head_commit}^{{tree}}"),
        record=binding.record,
        binding=binding,
        tree_files=seed.tree_files,
    )


def _mutated_ref(root: Path, ref: BlobRef, path: tuple[str, ...], value: object) -> BlobRef:
    document = json.loads(read_pinned_blob(root, ref))
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    destination = root / ref.path
    destination.write_bytes(raw)
    commit = _UNIT3._commit(root, f"mutate {ref.path}", ref.path)
    return BlobRef(ref.path, commit, hashlib.sha256(raw).hexdigest())


def _projection_bytes() -> bytes:
    return read_pinned_blob(_ROOT, approval.T139_VECTOR_APPROVAL_REF)


def test_fixed_real_repository_loader_seals_effective_authority() -> None:
    approved = _manifest._load_approved_manifest(os.fspath(_ROOT))
    assert _manifest._is_sealed_approved_manifest(approved)
    assert approved.approval_ref == approval.D282_DECISIONS_REF
    assert approved.manifest_ref == approval.T139_APPROVAL_MANIFEST_REF
    assert approved.projection_ref == approval.T139_VECTOR_APPROVAL_REF
    assert approved.base_approval_fold_commit == approval.D282_DECISIONS_REF.commit
    assert approved.effective_approval_fold_commit == "b261b293f40548d7fc44293df3806df69acb7bc9"
    assert approved.vector_index == approval.load_effective_approval_projections(_ROOT)[1].vector_index
    assert len(json.loads(read_pinned_blob(_ROOT, approved.vector_index))["vectors"]) == 46


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda raw: raw.replace(b'{\n  "schema_version":', b'{\n  "schema_version":"t139-vector-approval/v1",\n  "schema_version":', 1), "duplicate_key"),
        (lambda raw: raw.replace(b'{\n', b'{\n  "unknown":true,\n', 1), "exact_keys"),
        (lambda raw: raw.replace(b'  "decision_kind": "t139-vector-approval/v1",\n', b"", 1), "exact_keys"),
        (lambda raw: raw.replace(b'"base_approval_fold_commit": "39d760985a5e37d20464c394760bf65596156566"', b'"base_approval_fold_commit": 1', 1), "invalid_structure"),
        (lambda raw: raw.replace(b'{\n', b'{\n  "non_finite":NaN,\n', 1), "non_finite"),
    ],
    ids=["duplicate", "unknown", "missing", "type", "nonfinite"],
)
def test_projection_parser_rejects_nonexact_json(mutation, reason: str) -> None:
    with pytest.raises(approval.ApprovalProjectionError) as caught:
        approval._parse_vector_approval_projection(mutation(_projection_bytes()))
    assert caught.value.reason_code == reason


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b'"commit": "6d431a60acc709832513440266c84ad86ea5ebc9"', b'"commit": "X6d431a60acc709832513440266c84ad86ea5ebc"'),
        (b'"sha256": "b4a86912212e9350c37c15c1c4eeabf7f9ce71e4806bec7d2e4cf491b2d39099"', b'"sha256": "B4a86912212e9350c37c15c1c4eeabf7f9ce71e4806bec7d2e4cf491b2d39099"'),
        (b'"path": "orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v2.json"', b'"path": "../index-v2.json"'),
    ],
    ids=["commit", "sha256", "path"],
)
def test_projection_parser_rejects_invalid_blobref_fields(old: bytes, new: bytes) -> None:
    raw = _projection_bytes()
    assert raw.count(old) == 1
    with pytest.raises(approval.ApprovalProjectionError):
        approval._parse_vector_approval_projection(raw.replace(old, new, 1))


def test_manifest_parser_rejects_unknown_key_and_invalid_index_path() -> None:
    raw = read_pinned_blob(_ROOT, approval.T139_APPROVAL_MANIFEST_REF)
    with pytest.raises(approval.ApprovalProjectionError) as unknown:
        approval._parse_approval_manifest_projection(raw.replace(b"{\n", b'{\n  "unknown":true,\n', 1))
    assert unknown.value.reason_code == "exact_keys"
    old = b'"path": "orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v2.json"'
    with pytest.raises(approval.ApprovalProjectionError):
        approval._parse_approval_manifest_projection(raw.replace(old, b'"path": "/index-v2.json"', 1))


def test_projection_values_are_immutable() -> None:
    manifest, projection = approval.load_effective_approval_projections(_ROOT)
    with pytest.raises((AttributeError, TypeError)):
        projection.vector_index = manifest.vector_index  # type: ignore[misc]


@pytest.mark.parametrize("target", ["manifest", "payload"])
def test_fixed_projection_blob_hashes_fail_closed(tmp_path: Path, target: str) -> None:
    root = _clone_repository(tmp_path)
    manifest_ref = approval.T139_APPROVAL_MANIFEST_REF
    projection_ref = approval.T139_VECTOR_APPROVAL_REF
    original = manifest_ref if target == "manifest" else projection_ref
    wrong = BlobRef(original.path, original.commit, "0" * 64)
    if target == "manifest":
        manifest_ref = wrong
    else:
        projection_ref = wrong
    with pytest.raises(BlobRefError):
        _manifest._load_approved_manifest_from_refs(
            os.fspath(root),
            manifest_ref=manifest_ref,
            projection_ref=projection_ref,
        )


@pytest.mark.parametrize(
    ("target", "path", "code"),
    [
        ("projection", ("forward_supersedes", "approval", "sha256"), "d282_predecessor_mismatch"),
        ("projection", ("canonical_authority", "sha256"), "effective_authority_mismatch"),
    ],
)
def test_predecessor_and_d574_authority_are_exact(
    tmp_path: Path, target: str, path: tuple[str, ...], code: str
) -> None:
    root = _clone_repository(tmp_path)
    assert target == "projection"
    projection_ref = _mutated_ref(root, approval.T139_VECTOR_APPROVAL_REF, path, "f" * 64)
    with pytest.raises(_manifest.VectorAuthorityMismatchError) as caught:
        _manifest._load_approved_manifest_from_refs(
            os.fspath(root),
            manifest_ref=approval.T139_APPROVAL_MANIFEST_REF,
            projection_ref=projection_ref,
        )
    assert caught.value.reason_code == code


def test_head_same_name_replacement_is_not_authority(tmp_path: Path) -> None:
    root = _clone_repository(tmp_path)
    approved = _manifest._load_approved_manifest(os.fspath(root))
    for ref in (approved.manifest_ref, approved.projection_ref, approved.vector_index):
        (root / ref.path).write_bytes(b'{"attacker":true}\n')
    reloaded = _manifest._load_approved_manifest(os.fspath(root))
    assert reloaded.vector_index == approved.vector_index


def test_fixed_wrapper_accepts_no_caller_ref_or_digest() -> None:
    assert set(inspect.signature(_manifest._load_approved_manifest).parameters) == {"repository_root"}
    assert inspect.getsource(_manifest._load_approved_manifest_from_refs).count(
        "load_approval_payload(repository_root)"
    ) == 1
    with pytest.raises(TypeError):
        _manifest._load_approved_manifest(_ROOT, projection_ref=approval.T139_VECTOR_APPROVAL_REF)


def test_approved_manifest_and_binding_reject_unsealed_authority(tmp_path: Path) -> None:
    approved = _manifest._load_approved_manifest(os.fspath(_ROOT))
    values = {
        name: getattr(approved, name)
        for name in inspect.signature(_manifest.ApprovedManifest).parameters
        if name != "token"
    }
    with pytest.raises(TypeError):
        _manifest.ApprovedManifest(token=object(), **values)
    fixture = _UNIT3._make_git_fixture(tmp_path)
    with pytest.raises(TypeError):
        _binding._PreregBinding._issue(
            record=fixture.record, approved_manifest=object(), repository_root=fixture.root,
            measurement_head=fixture.head_commit, prereg_commit=fixture.root_commit,
            prereg_content_commit=fixture.content_commit,
            prereg_effective_commit=fixture.effective_commit,
            root_identity=(fixture.root.stat().st_dev, fixture.root.stat().st_ino),
            token=_binding._CAPABILITY_TOKEN,
        )


def test_normal_resolver_binding_rechecks_projection_blobs(tmp_path: Path) -> None:
    fixture = _authority_fixture(tmp_path)
    fixture.binding.assert_intact(fixture.root)
    object.__setattr__(fixture.binding.approved_manifest, "vector_index", BlobRef(
        fixture.binding.approved_manifest.vector_index.path,
        fixture.binding.approved_manifest.vector_index.commit,
        "f" * 64,
    ))
    with pytest.raises(_manifest.VectorAuthorityMismatchError):
        fixture.binding.assert_intact(fixture.root)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
