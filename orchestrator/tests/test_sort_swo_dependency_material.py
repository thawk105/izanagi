# -*- coding: utf-8 -*-
"""Production sort SWO canonical dependency material regression tests."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH.parent))

from orchestrator.campaign import sort_swo_dependency_material as material  # noqa: E402
from orchestrator.campaign import sort_swo_oracle  # noqa: E402


_FIXTURE = _HERE / "fixtures" / "sort_swo_masstree"
_PINNED_HEAD = "b3c5d054b66b08374d7a6ff5a0faeaf28b041a38"


def _fixture_entries() -> tuple[str, ...]:
    return tuple(
        line.split("  ", 1)[1]
        for line in (_FIXTURE / "SHA256SUMS").read_text(
            encoding="utf-8"
        ).splitlines()
    )


def _synthetic_source(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    source = tmp_path / "masstree-src"
    source.mkdir()
    entries = _fixture_entries()
    tracked = tuple(sorted(set(entries) - {"PIN", "config.h"}))
    for relative in (*tracked, "config.h"):
        destination = source.joinpath(*relative.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_FIXTURE / relative, destination)
    (source / "PIN").write_text("source PIN must not be read\n", encoding="utf-8")
    return source.resolve(), tracked


def _install_source_probe(monkeypatch, source: Path, tracked: tuple[str, ...]):
    state = material._GitSourceState(
        root=source, head=_PINNED_HEAD, tracked_paths=tracked,
    )

    def probe(observed: Path):
        assert Path(observed).resolve() == source
        return state

    monkeypatch.setattr(material, "_probe_git_source", probe)


def test_materialize_uses_rule_derived_inventory_and_generated_pin(
        tmp_path, monkeypatch):
    source, tracked = _synthetic_source(tmp_path)
    _install_source_probe(monkeypatch, source, tracked)

    first = material.materialize_canonical_dependency(
        source, lease_parent=tmp_path, expected_head=_PINNED_HEAD,
    )
    try:
        assert first.manifest_sha256 == (
            sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
        )
        assert first.config_sha256 == (
            "e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a"
        )
        assert len(first.files) == 101
        assert (first.root / "PIN").read_bytes() == (
            f"{_PINNED_HEAD}\n".encode("ascii")
        )
        manifest_bytes = (first.root / "SHA256SUMS").read_bytes()
        assert manifest_bytes.endswith(b"\n")
        lines = manifest_bytes.decode("utf-8").splitlines()
        assert [line[66:] for line in lines] == sorted(first.files)
        assert all(line[64:66] == "  " for line in lines)
        assert not (first.lease_root / "generated").exists()
    finally:
        material.cleanup_canonical_dependency(first)

    (source / "PIN").write_text(
        "a different source PIN is still ignored\n", encoding="utf-8",
    )
    second = material.materialize_canonical_dependency(
        source, lease_parent=tmp_path, expected_head=_PINNED_HEAD,
    )
    try:
        assert second.manifest_sha256 == (
            sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
        )
        assert second.lease_root != first.lease_root
    finally:
        material.cleanup_canonical_dependency(second)
    assert not first.lease_root.exists()
    assert not second.lease_root.exists()


def test_materialize_manifest_mismatch_has_fixed_reason_and_bounded_hashes(
        tmp_path, monkeypatch):
    source, tracked = _synthetic_source(tmp_path)
    _install_source_probe(monkeypatch, source, tracked)
    (source / "config.h").write_text("machine-local config drift\n", encoding="utf-8")

    with pytest.raises(
            material.CanonicalDependencyMaterialError) as caught:
        material.materialize_canonical_dependency(
            source, lease_parent=tmp_path, expected_head=_PINNED_HEAD,
        )
    error = caught.value
    assert error.detail_code == "canonical-manifest-mismatch"
    assert error.expected_manifest_sha256 == (
        sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
    )
    assert error.generated_manifest_sha256 is not None
    assert len(error.generated_manifest_sha256) == 64
    assert error.generated_manifest_sha256 != error.expected_manifest_sha256
    assert list(tmp_path.glob(".sort-swo-dependency-*")) == []


def test_empty_tracked_list_is_rejected_instead_of_becoming_empty_inventory(
        tmp_path, monkeypatch):
    source = (tmp_path / "masstree-src")
    source.mkdir()
    responses = iter((
        f"{source.resolve()}\n{_PINNED_HEAD}\n".encode("utf-8"),
        b"",
    ))
    monkeypatch.setattr(
        material, "_run_git", lambda *_args, **_kwargs: next(responses),
    )

    with pytest.raises(
            material.CanonicalDependencyMaterialError) as caught:
        material._probe_git_source(source.resolve())
    assert caught.value.detail_code == "canonical-tracked-list-invalid"


@pytest.mark.parametrize("relative", ("../escape", "/absolute", "PIN", "a\\b"))
def test_tracked_path_normalization_is_fail_closed(tmp_path, relative):
    with pytest.raises(
            material.CanonicalDependencyMaterialError) as caught:
        material._normalize_tracked_path(
            relative.encode("utf-8"), root=tmp_path,
        )
    assert caught.value.detail_code == "canonical-tracked-list-invalid"


def test_source_symlink_is_not_copied(tmp_path, monkeypatch):
    source = (tmp_path / "masstree-src")
    source.mkdir()
    target = tmp_path / "outside.hh"
    target.write_text("outside\n", encoding="utf-8")
    (source / "tracked.hh").symlink_to(target)
    (source / "config.h").write_text("config\n", encoding="utf-8")
    _install_source_probe(monkeypatch, source.resolve(), ("tracked.hh",))

    with pytest.raises(
            material.CanonicalDependencyMaterialError) as caught:
        material.materialize_canonical_dependency(
            source.resolve(), lease_parent=tmp_path,
            expected_head=_PINNED_HEAD,
        )
    assert caught.value.detail_code == "canonical-copy-failed"
    assert list(tmp_path.glob(".sort-swo-dependency-*")) == []


def test_two_root_verifier_rejects_live_tracked_byte_drift(
        tmp_path, monkeypatch):
    source, tracked = _synthetic_source(tmp_path)
    _install_source_probe(monkeypatch, source, tracked)
    created = material.materialize_canonical_dependency(
        source, lease_parent=tmp_path, expected_head=_PINNED_HEAD,
    )
    try:
        changed = source / tracked[0]
        changed.write_bytes(changed.read_bytes() + b"\nchanged after oracle\n")
        with pytest.raises(
                material.CanonicalDependencyMaterialError) as caught:
            material.assert_source_matches_canonical(
                source, created.root, expected_head=_PINNED_HEAD,
                expected_manifest_sha256=created.manifest_sha256,
            )
        assert caught.value.detail_code == "canonical-source-drift"
    finally:
        material.cleanup_canonical_dependency(created)


def test_two_root_verifier_rechecks_all_file_identities_after_final_probe(
        tmp_path, monkeypatch):
    source = tmp_path / "masstree-src"
    source.mkdir()
    (source / "tracked.hh").write_text("// pinned\n", encoding="utf-8")
    (source / "config.h").write_text("#pragma once\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(
        ["git", "-C", str(source), "add", "--", "tracked.hh"], check=True,
    )
    subprocess.run(
        [
            "git", "-C", str(source), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid",
            "commit", "-qm", "identity recheck source",
        ],
        check=True,
    )
    head = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--verify", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    payloads = {
        "PIN": f"{head}\n".encode("ascii"),
        "config.h": (source / "config.h").read_bytes(),
        "tracked.hh": (source / "tracked.hh").read_bytes(),
    }
    for relative, payload in payloads.items():
        (canonical / relative).write_bytes(payload)
    manifest = b"".join(
        hashlib.sha256(payloads[relative]).hexdigest().encode("ascii")
        + b"  " + relative.encode("utf-8") + b"\n"
        for relative in sorted(payloads)
    )
    (canonical / "SHA256SUMS").write_bytes(manifest)
    first_relative = sorted(set(payloads) - {"PIN"})[0]
    original_reader = material._read_source_file_with_identity
    changed = False

    def read_then_change_first(observed_root: Path, relative: str):
        nonlocal changed
        payload, identity = original_reader(observed_root, relative)
        if relative == first_relative and not changed:
            observed_root.joinpath(*relative.split("/")).write_bytes(
                payload + b"\nchanged after the first stable read\n"
            )
            changed = True
        return payload, identity

    monkeypatch.setattr(
        material, "_read_source_file_with_identity",
        read_then_change_first,
    )
    with pytest.raises(
            material.CanonicalDependencyMaterialError) as caught:
        material.assert_source_matches_canonical(
            source.resolve(), canonical, expected_head=head,
            expected_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        )
    assert changed is True
    assert caught.value.detail_code == "canonical-source-drift"
    assert caught.value.path == source.resolve() / first_relative


def test_manifest_line_builder_matches_pinned_fixture_exactly(
        tmp_path, monkeypatch):
    source, tracked = _synthetic_source(tmp_path)
    _install_source_probe(monkeypatch, source, tracked)
    created = material.materialize_canonical_dependency(
        source, lease_parent=tmp_path, expected_head=_PINNED_HEAD,
    )
    try:
        generated = (created.root / "SHA256SUMS").read_bytes()
        assert generated == (_FIXTURE / "SHA256SUMS").read_bytes()
        assert hashlib.sha256(generated).hexdigest() == (
            sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
        )
    finally:
        material.cleanup_canonical_dependency(created)


@pytest.mark.parametrize(
    ("mutation", "material_detail", "verifier_detail"),
    [
        (
            "drop-pin-declaration", "canonical-manifest-mismatch",
            "dependency-manifest-not-canonical",
        ),
        (
            "single-space", "canonical-verification-failed",
            "dependency-manifest-invalid",
        ),
        (
            "reverse-order", "canonical-verification-failed",
            "dependency-manifest-invalid",
        ),
    ],
)
def test_manifest_mutations_have_one_exact_verifier_reason(
        tmp_path, monkeypatch, mutation, material_detail, verifier_detail):
    source, tracked = _synthetic_source(tmp_path)
    _install_source_probe(monkeypatch, source, tracked)
    if mutation == "drop-pin-declaration":
        original_payloads = material._canonical_payloads

        def without_pin(source_payloads: dict[str, bytes], head: str):
            payloads = original_payloads(source_payloads, head)
            del payloads["PIN"]
            return payloads

        monkeypatch.setattr(material, "_canonical_payloads", without_pin)
    elif mutation == "single-space":
        monkeypatch.setattr(material, "_MANIFEST_SEPARATOR", b" ")
    else:
        monkeypatch.setattr(
            material, "_manifest_paths",
            lambda payloads: tuple(reversed(sorted(payloads))),
        )

    with pytest.raises(
            material.CanonicalDependencyMaterialError) as caught:
        material.materialize_canonical_dependency(
            source, lease_parent=tmp_path, expected_head=_PINNED_HEAD,
        )
    assert caught.value.detail_code == material_detail
    assert isinstance(
        caught.value.__cause__, sort_swo_oracle._DependencyVerificationError,
    )
    assert caught.value.__cause__.detail_code == verifier_detail
    assert list(tmp_path.glob(".sort-swo-dependency-*")) == []


def test_real_prebuilt_masstree_material_is_pinned_when_explicitly_configured(
        tmp_path, monkeypatch):
    configured = os.environ.get("IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT")
    if not configured:
        pytest.skip("IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT is not configured")
    configured_source = Path(configured).resolve(strict=True)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    source = base / "masstree-src"
    shutil.copytree(configured_source, source)
    created = material.materialize_canonical_dependency(
        source.resolve(), lease_parent=base, expected_head=_PINNED_HEAD,
    )
    try:
        assert created.head == _PINNED_HEAD
        assert len(created.files) == 101
        assert created.config_sha256 == (
            "e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a"
        )
        assert created.manifest_sha256 == (
            sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
        )
        assert (created.root / "SHA256SUMS").read_bytes() == (
            _FIXTURE / "SHA256SUMS"
        ).read_bytes()

        compiler = shutil.which("g++")
        if compiler is None:
            pytest.skip("real-root oracle series requires g++")
        environment = sort_swo_oracle.resolve_oracle_environment(
            _ORCH.parent / "external" / "ccbench",
            compiler=compiler,
            dependency_root=created.root,
        )
        statement = sort_swo_oracle.render_sort_ir(
            sort_swo_oracle.SortComparatorIr((
                (sort_swo_oracle.SortIrField.KEY,
                 sort_swo_oracle.SortIrDirection.ASC),
            ))
        )
        materialized_source = (
            "// EVOLVE-BLOCK-BEGIN silo-writeset-sort\n"
            "#if SORT_VARIANT\n"
            f"{statement}\n"
            "#else\n"
            "sort(write_set_.begin(), write_set_.end());\n"
            "#endif\n"
            "// EVOLVE-BLOCK-END silo-writeset-sort\n"
        )
        oracle_result = sort_swo_oracle.check_materialized_sort_swo(
            materialized_source,
            marker_id="silo-writeset-sort",
            proposal_source=statement,
            environment=environment,
        )
        assert oracle_result.status is sort_swo_oracle.OracleStatus.PASS
        assert oracle_result.finding is None

        from orchestrator.tests import test_buildcache_v2 as build_support

        archive = source / "libkohler_masstree_json.a"
        assert archive.is_file()
        build_support._install_toolchain(tmp_path, monkeypatch)
        build_support._fake_build_environment(monkeypatch, tmp_path)
        binding = {
            "fetchcontent_base_dir": str(base.resolve()),
            "oracle_dependency_root": str(created.root),
            "dependency_manifest_sha256": created.manifest_sha256,
            "masstree_head": created.head,
            "config_sha256": created.config_sha256,
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        }
        first = build_support._build(
            tmp_path, build_support._contract(1798),
            ccbench_dir=str(_ORCH.parent / "external" / "ccbench"),
            post_oracle_dependency_binding=binding,
        )
        second = build_support._build(
            tmp_path, build_support._contract(1798),
            ccbench_dir=str(_ORCH.parent / "external" / "ccbench"),
            post_oracle_dependency_binding=binding,
        )
        assert first.cached is False
        assert second.cached is True
        assert first.build_dir == second.build_dir
    finally:
        material.cleanup_canonical_dependency(created)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
