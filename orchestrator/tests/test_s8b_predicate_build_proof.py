# -*- coding: utf-8 -*-
from __future__ import annotations

import contextlib
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import s8b_binary_admission as admission_receipt
from orchestrator.campaign import s8b_expected_materialization as snapshot
from orchestrator.tests.s8b_v2_freeze_fixture import sealed_source_protection_fixture
from orchestrator.campaign import s8b_floor_campaign as floor
from orchestrator.campaign import s8b_materialization as materialization
from orchestrator.campaign.build_admission import (
    resolve_current_build_admission_policy,
)
from orchestrator.campaign.model import Genome
from orchestrator.campaign.s1_direct_comparison import PreparedCell
from orchestrator.campaign.source_digest import (
    SOURCE_EVIDENCE_SCHEMA,
    SourceEvidence,
)


_PIN = "1" * 40
_CONTRACT_SHA256 = hashlib.sha256(b"predicate-build-proof-contract").hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _producer_fixture(
        tmp_path: Path, monkeypatch, *, missing_snapshot: bool = False,
        missing_manifest: bool = False):
    source_root = tmp_path / "source-snapshot"
    compiler_input = source_root / "include" / "predicate.hh"
    compiler_input.parent.mkdir(parents=True)
    compiler_input.write_bytes(b"bool declared_predicate = true;\n")
    genome = Genome("silo", {"BACKOFF_FIXED": 0})
    src_token = hashlib.sha256(b"predicate-build-proof-source").hexdigest()
    prepared = PreparedCell(
        genome=genome, src_token=src_token,
        ccbench_dir=str(source_root), cache_root=str(tmp_path / "cache"),
    )
    entry = {
        "configuration": "stock_common",
        "flags": {"BACKOFF_FIXED": 0},
    }
    freeze = {"holdouts": {"H1": {"variant_binding": {"entries": {
        "stock_common": entry,
    }}}}}
    cell = {
        "cell_id": "H1::stock_common", "holdout_id": "H1",
        "configuration_id": "stock_common",
    }
    expected_materialization_sha256 = snapshot.snapshot_tree_digest(source_root)
    identity = materialization.binding_from_prepared(entry, prepared)
    evidence = SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=str(source_root.resolve()), ccbench_commit=_PIN,
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
        src_token=src_token,
        source_bytes_sha256=hashlib.sha256(b"source bytes").hexdigest(),
        tracked_clean=False,
        tracked_diff_sha256=hashlib.sha256(b"tracked diff").hexdigest(),
        tracked_paths=("include/predicate.hh",),
    )
    manifest = {
        "schema_version": "s8b-compiler-input/v1",
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": "ycsb_silo.exe",
        "depfile_count": 1,
        "inputs": [{
            "path": "include/predicate.hh",
            "sha256": hashlib.sha256(compiler_input.read_bytes()).hexdigest(),
        }],
    }
    manifest_sha256 = _canonical_sha256(manifest)
    observed_build_kwargs: list[dict] = []

    @contextlib.contextmanager
    def prepared_binding(**_kwargs):
        yield dict(identity), prepared

    def build_fn(_genome, **kwargs):
        observed_build_kwargs.append(dict(kwargs))
        binary = tmp_path / "built" / "ycsb_silo.exe"
        binary.parent.mkdir()
        binary.write_bytes(b"predicate proof binary")
        binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
        source_protection = sealed_source_protection_fixture(
            source=evidence, binary_sha256=binary_sha256,
            compiler_input_manifest_sha256=manifest_sha256,
        )
        return SimpleNamespace(
            source_protection=source_protection,
            binary=str(binary), bin_sha256=binary_sha256,
            bin_hash=binary_sha256[:16], cached=False,
            configure_argv=("cmake", "-S", str(source_root)),
            build_argv=("cmake", "--build", str(tmp_path / "built")),
            ccbench_root=str(source_root), contract_sha256=_CONTRACT_SHA256,
            compiler_input_manifest=(None if missing_manifest else manifest),
            compiler_input_manifest_sha256=(
                None if missing_manifest else manifest_sha256
            ),
            source_snapshot_sha256=(
                None if missing_snapshot else expected_materialization_sha256
            ),
            expected_materialization_sha256=(
                None if missing_snapshot else expected_materialization_sha256
            ),
        )

    monkeypatch.setattr(floor, "prepared_binding", prepared_binding)
    monkeypatch.setattr(
        floor.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: evidence,
    )
    monkeypatch.setattr(
        floor.buildcache, "compilers_for_current_site",
        lambda: ("fixture-cc", "fixture-cxx"),
    )
    monkeypatch.setattr(
        floor, "_bind_current_toolchain",
        lambda *_args, **_kwargs: {"fixture": {"version": "1"}},
    )
    contract = SimpleNamespace(contract_sha256=_CONTRACT_SHA256)
    return {
        "built": lambda: floor.build_cells(
            freeze, [cell], ccbench_pin=_PIN,
            out_root=tmp_path / "out", prepare_fn=lambda: None,
            contract=contract, verified_calibration=object(),
            build_fn=build_fn,
        ),
        "cell": cell,
        "expected_materialization_sha256": expected_materialization_sha256,
        "observed_build_kwargs": observed_build_kwargs,
    }


def test_producer_proof_reaches_pre_measurement_consumer(tmp_path, monkeypatch):
    fixture = _producer_fixture(tmp_path, monkeypatch)
    built = fixture["built"]()
    record = built[fixture["cell"]["cell_id"]]
    build_kwargs = fixture["observed_build_kwargs"][0]
    assert "source_snapshot_sha256" not in build_kwargs
    descriptor = build_kwargs["expected_materialization_descriptor"]
    assert descriptor.configuration == fixture["cell"]["configuration_id"]
    assert descriptor.ccbench_commit == _PIN
    assert descriptor.declaration == {
        "configuration": "stock_common",
        "flags": {"BACKOFF_FIXED": 0},
    }
    assert descriptor.template_patch_path is None
    assert record["admission_receipt"]["subject"][
        "expected_materialization_sha256"
    ] == (
        fixture["expected_materialization_sha256"]
    )
    subject = record["admission_receipt"]["subject"]
    assert subject["source_snapshot_sha256"] == (
        subject["expected_materialization_sha256"]
    )
    assert subject["compiler_input_manifest_sha256"] == _canonical_sha256(
        record["admission_receipt"]["proof"]["compiler_input_manifest"]
    )
    materialization_binding = record["admission_receipt"]["proof"][
        "materialization_binding"
    ]
    assert materialization_binding == record["binding"]
    assert "expected_materialization_sha256" not in materialization_binding
    unsigned_binding = dict(materialization_binding)
    binding_sha256 = unsigned_binding.pop("binding_sha256")
    assert binding_sha256 == hashlib.sha256(json.dumps(
        unsigned_binding, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    checked, destination = floor._preflight_runtime_store_record(
        fixture["cell"]["cell_id"], record,
        store_root=tmp_path / "store",
        expected_policy=resolve_current_build_admission_policy(),
        expected_ccbench_pin=_PIN,
        expected_contract_sha256=_CONTRACT_SHA256,
    )
    assert checked is record
    assert destination.name == record["binary_sha256"]


@pytest.mark.parametrize("missing", ["snapshot", "manifest"])
def test_campaign_forwards_missing_proof_to_unconditional_issuer(
        tmp_path, monkeypatch, missing):
    fixture = _producer_fixture(
        tmp_path, monkeypatch,
        missing_snapshot=missing == "snapshot",
        missing_manifest=missing == "manifest",
    )
    issued = []

    real_issuer = floor._binary_admission.issue_binary_admission_receipt

    def issue(**kwargs):
        issued.append(kwargs)
        return real_issuer(**kwargs)

    monkeypatch.setattr(
        floor._binary_admission, "issue_binary_admission_receipt",
        issue,
    )
    with pytest.raises(
            floor.FloorCampaignError,
            match="binary admission receipt を発行できない"):
        fixture["built"]()
    assert len(issued) == 1
    if missing == "snapshot":
        assert issued[0]["source_snapshot_sha256"] is None
        assert issued[0]["expected_materialization_sha256"] is None
    else:
        assert issued[0]["compiler_input_manifest"] is None
        assert issued[0]["compiler_input_manifest_sha256"] is None


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("compiler_input_manifest_sha256", "proof 再計算値"),
        (
            "source_snapshot_sha256",
            "source snapshot SHA が expected materialization",
        ),
        (
            "expected_materialization_sha256",
            "source snapshot SHA が expected materialization",
        ),
    ],
)
def test_consumer_rejects_resealed_reverse_proof_mismatch(
        tmp_path, monkeypatch, field, message):
    fixture = _producer_fixture(tmp_path, monkeypatch)
    built = fixture["built"]()
    record = copy.deepcopy(built[fixture["cell"]["cell_id"]])
    receipt = record["admission_receipt"]
    receipt["subject"][field] = "0" * 64
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256")
    receipt["receipt_sha256"] = admission_receipt._sha256_map(unsigned)
    with pytest.raises(floor.FloorCampaignError, match=message):
        floor._preflight_runtime_store_record(
            fixture["cell"]["cell_id"], record,
            store_root=tmp_path / "store",
            expected_policy=resolve_current_build_admission_policy(),
            expected_ccbench_pin=_PIN,
            expected_contract_sha256=_CONTRACT_SHA256,
        )


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
