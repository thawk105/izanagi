# -*- coding: utf-8 -*-
"""Runtime dependency-prefix roots bridge from floor build to real issuer."""
from __future__ import annotations

from orchestrator.tests.s8b_v2_freeze_fixture import (
    in_fresh_sealed_fixture_process, sealed_source_protection_fixture,
)

import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.campaign import env_attestation
from orchestrator.campaign import env_contract as ec
from orchestrator.campaign import s8b_floor_campaign as floor
from orchestrator.tests import test_s8b_floor_campaign as fixture


def _stock_cell() -> tuple[dict, list[dict]]:
    freeze = fixture._freeze_document()
    cells = [
        cell for cell in floor.enumerate_cells(
            freeze, stock_configuration=fixture._STOCK,
        )
        if cell["cell_id"] == "rr79::stock_common"
    ]
    assert len(cells) == 1
    return freeze, cells


def _install_floor_seams(monkeypatch) -> None:
    monkeypatch.setattr(
        floor.source_digest,
        "resolve_evidence",
        fixture._fixture_source_evidence,
    )
    monkeypatch.setattr(
        floor,
        "_bind_current_toolchain",
        fixture._fixture_toolchain_binding,
    )


def _dependency_build(
        tmp_path: Path, *, reported_roots: tuple[str, ...],
):
    dependency_root = tmp_path / "dependency-install"
    dependency_input = dependency_root / "include" / "dependency.hh"
    dependency_input.parent.mkdir(parents=True)
    dependency_input.write_bytes(b"floor dependency compiler input\n")
    fake_build = fixture._make_fake_build(tmp_path / "bin")

    def build(genome, **kwargs):
        result = fake_build(genome, **kwargs)
        manifest = {
            "schema_version": "s8b-compiler-input/v3",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": f"ycsb_{genome.protocol}.exe",
            "depfile_count": 1,
            "input_policy": "snapshot-and-external-hashes/v1",
            "inputs": [{
                "root": "dependency-prefix",
                "path": "include/dependency.hh",
                "sha256": hashlib.sha256(
                    dependency_input.read_bytes()
                ).hexdigest(),
            }],
        }
        result.compiler_input_manifest = manifest
        result.compiler_input_manifest_sha256 = hashlib.sha256(json.dumps(
            manifest, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        if reported_roots:
            result.source_protection = sealed_source_protection_fixture(
                source=kwargs["source_evidence"], binary_sha256=result.bin_sha256,
                compiler_input_manifest_sha256=result.compiler_input_manifest_sha256,
            )
            result.source_snapshot_sha256 = result.source_protection.source_snapshot_sha256
            result.expected_materialization_sha256 = (
                result.source_protection.expected_materialization_sha256
            )
        result.compiler_input_dependency_prefix_roots = reported_roots
        return result

    return build, dependency_root.resolve()


@in_fresh_sealed_fixture_process
def test_build_cells_passes_build_result_dependency_roots_to_real_receipt_issuer(
        tmp_path, monkeypatch):
    _install_floor_seams(monkeypatch)
    freeze, cells = _stock_cell()
    dependency_root = (tmp_path / "dependency-install").resolve()
    build, _ = _dependency_build(
        tmp_path, reported_roots=(str(dependency_root),),
    )
    original_issue = floor._binary_admission.issue_binary_admission_receipt
    observed = []

    def issue_spy(**kwargs):
        observed.append(
            kwargs["current_compiler_input_dependency_prefix_roots"]
        )
        return original_issue(**kwargs)

    monkeypatch.setattr(
        floor._binary_admission,
        "issue_binary_admission_receipt",
        issue_spy,
    )
    contract = ec.lookup(fixture.ENV_TAG)
    built = floor.build_cells(
        freeze, cells, ccbench_pin="0" * 40,
        out_root=tmp_path / "out", prepare_fn=fixture._fake_prepare,
        contract=contract,
        verified_calibration=env_attestation.load_verified_calibration(
            contract, fixture.ROOT,
        ),
        build_fn=build,
    )

    assert observed == [(str(dependency_root),)]
    receipt = built["rr79::stock_common"]["admission_receipt"]
    assert receipt["proof"]["compiler_input_manifest"]["inputs"][0][
        "root"
    ] == "dependency-prefix"
    assert str(dependency_root) not in json.dumps(receipt, sort_keys=True)


def test_build_cells_real_receipt_issuer_rejects_wrong_dependency_root_context(
        tmp_path, monkeypatch):
    _install_floor_seams(monkeypatch)
    freeze, cells = _stock_cell()
    build, _dependency_root = _dependency_build(
        tmp_path, reported_roots=(),
    )
    original_issue = floor._binary_admission.issue_binary_admission_receipt
    observed = []

    def issue_spy(**kwargs):
        observed.append(
            kwargs["current_compiler_input_dependency_prefix_roots"]
        )
        return original_issue(**kwargs)

    monkeypatch.setattr(
        floor._binary_admission,
        "issue_binary_admission_receipt",
        issue_spy,
    )
    contract = ec.lookup(fixture.ENV_TAG)
    with pytest.raises(floor.FloorCampaignError, match="receipt"):
        floor.build_cells(
            freeze, cells, ccbench_pin="0" * 40,
            out_root=tmp_path / "out", prepare_fn=fixture._fake_prepare,
            contract=contract,
            verified_calibration=env_attestation.load_verified_calibration(
                contract, fixture.ROOT,
            ),
            build_fn=build,
        )
    assert observed == [()]


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
