# -*- coding: utf-8 -*-
"""Tests for the dedicated B-4 floor pair driver.

All measurement tests stop immediately below ``runner.measure_point``.  They do
not spawn a real subprocess, build a binary, run a benchmark, or dispatch work.
"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.calibrator.model import ScalePoint
from orchestrator.campaign import floor_pair_driver as F


NOW = datetime(2030, 1, 1, 0, 30, tzinfo=timezone.utc)
HEAD = "b" * 40
SOURCE_COMMIT = HEAD
REAL_SUBPROCESS_RUN = F.subprocess.run


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _map_sha256(value: object, *, ensure_ascii: bool) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=ensure_ascii,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _portable_build_record(
    binary_relpath: str,
    binary_sha256: str,
    *,
    tag: str,
) -> dict[str, object]:
    """実 s8b-binary-admission/v2 reader を通る最小 portable record。"""
    admission_module = F.s8b_binary_admission
    genome = json.dumps(
        {"fixture": tag}, sort_keys=True, separators=(",", ":")
    )
    src_token = hashlib.sha256(f"source:{tag}".encode()).hexdigest()
    entry_sha256 = hashlib.sha256(f"entry:{tag}".encode()).hexdigest()
    binding = {
        "genome_canonical": genome,
        "src_token": src_token,
        "variant_id": hashlib.sha256(
            f"{genome}|src={src_token}".encode()
        ).hexdigest()[:12],
        "entry_sha256": entry_sha256,
    }
    binding["binding_sha256"] = _map_sha256(binding, ensure_ascii=False)
    compiler_input = {
        "schema_version": admission_module.s8b_compiler_input.MANIFEST_SCHEMA,
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": "ycsb_fixture.exe",
        "depfile_count": 1,
        "inputs": [
            {
                "root": "snapshot",
                "path": "fixture.cc",
                "sha256": hashlib.sha256(f"input:{tag}".encode()).hexdigest(),
            }
        ],
    }
    compiler_input_sha256 = admission_module.s8b_compiler_input.manifest_sha256(
        compiler_input
    )
    source = {
        "schema": admission_module.SOURCE_EVIDENCE_SCHEMA,
        "ccbench_commit": "c" * 40,
        "genome_sha256": hashlib.sha256(genome.encode()).hexdigest(),
        "src_token": src_token,
        "source_bytes_sha256": hashlib.sha256(
            f"source-bytes:{tag}".encode()
        ).hexdigest(),
        "tracked_clean": False,
        "tracked_diff_sha256": hashlib.sha256(
            f"tracked-diff:{tag}".encode()
        ).hexdigest(),
        "tracked_paths": ["include/backoff.hh"],
    }
    materialization_sha256 = hashlib.sha256(
        f"materialization:{tag}".encode()
    ).hexdigest()
    receipt = {
        "schema": admission_module.RECEIPT_SCHEMA,
        "admission": {
            "schema": admission_module.ADMISSION_SCHEMA,
            "class": admission_module.BuildProvenance.HUMAN_REVIEWED.value,
            "policy_sha256": hashlib.sha256(b"policy").hexdigest(),
            "review_id": admission_module.ReviewId.S8B_FLOOR.value,
            "input_sha256": entry_sha256,
            "source": source,
        },
        "subject": {
            "cell_id": f"cell-{tag}",
            "holdout_id": f"holdout-{tag}",
            "configuration_id": f"configuration-{tag}",
            "entry_sha256": entry_sha256,
            "binding_sha256": binding["binding_sha256"],
            "binary_sha256": binary_sha256,
            "contract_sha256": hashlib.sha256(b"contract").hexdigest(),
            "trace": False,
            "source_snapshot_sha256": materialization_sha256,
            "compiler_input_manifest_sha256": compiler_input_sha256,
            "expected_materialization_sha256": materialization_sha256,
        },
        "proof": {
            "compiler_input_manifest": compiler_input,
            "materialization_binding": binding,
        },
    }
    receipt["receipt_sha256"] = _map_sha256(receipt, ensure_ascii=True)
    return {
        "cell_id": f"cell-{tag}",
        "holdout_id": f"holdout-{tag}",
        "configuration_id": f"configuration-{tag}",
        "binary": binary_relpath,
        "binary_sha256": binary_sha256,
        "bin_hash_short": binary_sha256[:16],
        "binding": binding,
        "configure_argv": ["cmake", "fixture"],
        "build_argv": ["cmake", "--build", "fixture"],
        "cached": False,
        "store_path": f"fixture-store/{binary_sha256}",
        "admission_receipt": receipt,
    }


def _write_inputs(root: Path) -> dict[str, str]:
    (root / "refs").mkdir(parents=True)
    (root / "bin").mkdir()
    (root / "out").mkdir()
    payloads = {
        "refs/calibration.json": b"{}\n",
        "bin/candidate.exe": b"candidate fixture binary\n",
        "bin/reference.exe": b"reference fixture binary\n",
    }
    result: dict[str, str] = {}
    for relpath, raw in payloads.items():
        (root / relpath).write_bytes(raw)
        result[relpath] = hashlib.sha256(raw).hexdigest()
    receipt_payloads = {
        "refs/candidate-receipt.json": _canonical(
            _portable_build_record(
                "bin/candidate.exe", result["bin/candidate.exe"], tag="candidate"
            )
        )
        + b"\n",
        "refs/reference-receipt.json": _canonical(
            _portable_build_record(
                "bin/reference.exe", result["bin/reference.exe"], tag="reference"
            )
        )
        + b"\n",
    }
    for relpath, raw in receipt_payloads.items():
        (root / relpath).write_bytes(raw)
        result[relpath] = hashlib.sha256(raw).hexdigest()
    return result


def _valid_document(hashes: dict[str, str]) -> dict[str, object]:
    return {
        "schema": F.SPEC_SCHEMA,
        "provenance": {
            "calibration": {
                "path": "refs/calibration.json",
                "sha256": hashes["refs/calibration.json"],
                "attestation_mode": "required",
            },
            "source_commit": SOURCE_COMMIT,
        },
        "environment": {
            "site": F.site_policy.OTHER,
            "env_tag": "test-env",
            "clocks_per_us": 2100,
            "numactl_argv": ["numactl", "--interleave=all"],
            "use_perf": False,
            "timeout_s": 12,
            "extra_env": {"FIXTURE_ENV": "1"},
            "probe_timeout_s": 2,
        },
        "artifacts": [
            {
                "artifact_id": "candidate-a",
                "binary_relpath": "bin/candidate.exe",
                "binary_sha256": hashes["bin/candidate.exe"],
                "build_receipt": {
                    "path": "refs/candidate-receipt.json",
                    "sha256": hashes["refs/candidate-receipt.json"],
                },
                "trace": False,
            },
            {
                "artifact_id": "reference-a",
                "binary_relpath": "bin/reference.exe",
                "binary_sha256": hashes["bin/reference.exe"],
                "build_receipt": {
                    "path": "refs/reference-receipt.json",
                    "sha256": hashes["refs/reference-receipt.json"],
                },
                "trace": False,
            },
        ],
        "cells": [
            {
                "cell_id": "cell-a",
                "perf_config": {
                    "records": 1000,
                    "threads": 1,
                    "workload": {
                        "ycsb_zipf_skew": "0.9",
                        "ycsb_rratio": "50",
                        "ycsb_rmw": "0",
                    },
                    "extime": 1,
                    "reps": 2,
                    "ycsb_max_ope": 10,
                },
            }
        ],
        "pairs": [
            {
                "pair_id": "pair-a",
                "cell_id": "cell-a",
                "reference_artifact_id": "reference-a",
                "sides": [
                    {
                        "side_id": "candidate_1",
                        "candidate_artifact_id": "candidate-a",
                    },
                    {
                        "side_id": "candidate_2",
                        "candidate_artifact_id": "candidate-a",
                    },
                ],
            }
        ],
        "windows": [
            {
                "window_id": "window-a",
                "campaign_id": "campaign-a",
                "not_before": "2030-01-01T00:00:00Z",
                "not_after": "2030-01-01T01:00:00Z",
                "sample_count": 1,
                "pair_ids": ["pair-a"],
                "artifact_relpath": "out/window-a.jsonl",
            }
        ],
        "randomization": {
            "algorithm": F.RANDOMIZATION_ID,
            "seed_hex": "01" * 32,
        },
        "statistics": {
            "session_reducer": F.SESSION_REDUCER_ID,
            "stratum_upper": F.STRATUM_UPPER_ID,
            "closed_strata": [{"window_id": "window-a", "pair_id": "pair-a"}],
            "final_combiner": F.FINAL_COMBINER_ID,
        },
        "failure_policy": {
            "policy": F.FAILURE_POLICY_ID,
            "retry_count": 0,
            "require_all_reps": True,
        },
        "outputs": {
            "window_format": F.WINDOW_FORMAT_ID,
            "summary_format": F.SUMMARY_FORMAT_ID,
            "summary_relpath": "out/summary.json",
        },
    }


def _fake_completed(returncode: int, stdout: bytes, stderr: bytes = b""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _install_git(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    *,
    head_overrides: dict[str, bytes] | None = None,
) -> None:
    overrides = {} if head_overrides is None else dict(head_overrides)

    def fake_run(cmd, **kwargs):
        if cmd[0] != "git":
            return REAL_SUBPROCESS_RUN(cmd, **kwargs)
        assert kwargs == {
            "capture_output": True,
            "check": False,
            "timeout": F._GIT_TIMEOUT_S,
        }
        assert cmd[:3] == ["git", "-C", str(root)]
        if cmd[3] == "rev-parse":
            assert cmd[4] == "HEAD"
            return _fake_completed(0, (HEAD + "\n").encode("ascii"))
        assert cmd[3] == "show"
        assert cmd[4].startswith("HEAD:")
        relpath = cmd[4][len("HEAD:") :]
        raw = overrides[relpath] if relpath in overrides else (root / relpath).read_bytes()
        return _fake_completed(0, raw)

    monkeypatch.setattr(F.subprocess, "run", fake_run)


def _verified_calibration(
    *,
    env_tag: str = "test-env",
    threads: int = 1,
    clocks_per_us: int = 2100,
    workload: dict[str, str] | None = None,
    records: int = 1000,
    quality_status: str = "accepted",
    saturation: bool = True,
):
    effective_workload = (
        {
            "ycsb_zipf_skew": "0.9",
            "ycsb_rratio": "50",
            "ycsb_rmw": "0",
        }
        if workload is None
        else workload
    )
    return SimpleNamespace(
        calibration=SimpleNamespace(
            env_tag=env_tag,
            threads=threads,
            clocks_per_us=clocks_per_us,
            workload=effective_workload,
            quality=SimpleNamespace(status=quality_status),
            saturation={"records": records} if saturation else None,
        )
    )


def _prepare_spec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    document: dict[str, object] | None = None,
    raw: bytes | None = None,
    expected_sha256: str | None = None,
    head_overrides: dict[str, bytes] | None = None,
    verified=None,
) -> tuple[F.FloorPairSpec, dict[str, object], bytes]:
    hashes = _write_inputs(tmp_path)
    effective_document = _valid_document(hashes) if document is None else document
    effective_raw = _canonical(effective_document) if raw is None else raw
    (tmp_path / "spec.json").write_bytes(effective_raw)
    _install_git(monkeypatch, tmp_path, head_overrides=head_overrides)
    verified_value = _verified_calibration() if verified is None else verified
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: verified_value,
    )
    expected = hashlib.sha256(effective_raw).hexdigest()
    if expected_sha256 is not None:
        expected = expected_sha256
    spec = F.load_frozen_spec(
        Path("spec.json"),
        expected,
        repo_root=tmp_path,
    )
    return spec, effective_document, effective_raw


def _document_only(tmp_path: Path) -> tuple[dict[str, object], dict[str, str]]:
    hashes = _write_inputs(tmp_path)
    return _valid_document(hashes), hashes


PUBLIC_DATACLASSES = (
    F.BoundReference,
    F.CalibrationReference,
    F.ProvenanceConfig,
    F.EnvironmentConfig,
    F.ArtifactConfig,
    F.FrozenPerfConfig,
    F.CellConfig,
    F.PairSide,
    F.PairConfig,
    F.WindowConfig,
    F.RandomizationConfig,
    F.StatisticsConfig,
    F.FailurePolicy,
    F.OutputsConfig,
    F.FloorPairSpec,
    F.PlannedSession,
    F.MeasurementPlan,
    F.MeasurementRequest,
    F.MeasurementResult,
    F.GainDifference,
    F.WindowRunResult,
    F.FinalFloorResult,
)


def test_all_floor_pair_dataclass_fields_have_no_defaults():
    for cls in PUBLIC_DATACLASSES:
        assert dataclasses.is_dataclass(cls)
        for field in dataclasses.fields(cls):
            assert field.default is dataclasses.MISSING, (cls.__name__, field.name)
            assert field.default_factory is dataclasses.MISSING, (cls.__name__, field.name)


def test_module_docstring_names_limits_and_unrecorded_env_failure_is_not_a_status():
    assert F.__doc__ is not None
    for limitation in F.NOT_PROVEN:
        assert limitation in F.__doc__
    assert "environment_mismatch" not in F.SESSION_STATUSES


REQUIRED_FIELD_PATHS = (
    ("schema",),
    ("provenance",),
    ("environment",),
    ("artifacts",),
    ("cells",),
    ("pairs",),
    ("windows",),
    ("randomization",),
    ("statistics",),
    ("failure_policy",),
    ("outputs",),
    ("provenance", "calibration"),
    ("provenance", "source_commit"),
    ("provenance", "calibration", "path"),
    ("provenance", "calibration", "sha256"),
    ("provenance", "calibration", "attestation_mode"),
    *(('environment', key) for key in (
        "site", "env_tag", "clocks_per_us", "numactl_argv", "use_perf",
        "timeout_s", "extra_env", "probe_timeout_s",
    )),
    *(("artifacts", 0, key) for key in (
        "artifact_id", "binary_relpath", "binary_sha256", "build_receipt", "trace",
    )),
    ("artifacts", 0, "build_receipt", "path"),
    ("artifacts", 0, "build_receipt", "sha256"),
    ("cells", 0, "cell_id"),
    ("cells", 0, "perf_config"),
    *(("cells", 0, "perf_config", key) for key in (
        "records", "threads", "workload", "extime", "reps", "ycsb_max_ope",
    )),
    *(("cells", 0, "perf_config", "workload", key) for key in (
        "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw",
    )),
    *(("pairs", 0, key) for key in (
        "pair_id", "cell_id", "reference_artifact_id", "sides",
    )),
    ("pairs", 0, "sides", 0, "side_id"),
    ("pairs", 0, "sides", 0, "candidate_artifact_id"),
    *(("windows", 0, key) for key in (
        "window_id", "campaign_id", "not_before", "not_after", "sample_count",
        "pair_ids", "artifact_relpath",
    )),
    ("randomization", "algorithm"),
    ("randomization", "seed_hex"),
    *(("statistics", key) for key in (
        "session_reducer", "stratum_upper", "closed_strata", "final_combiner",
    )),
    ("statistics", "closed_strata", 0, "window_id"),
    ("statistics", "closed_strata", 0, "pair_id"),
    ("failure_policy", "policy"),
    ("failure_policy", "retry_count"),
    ("failure_policy", "require_all_reps"),
    ("outputs", "window_format"),
    ("outputs", "summary_format"),
    ("outputs", "summary_relpath"),
)


def _delete_path(document: object, path: tuple[object, ...]) -> None:
    cursor = document
    for component in path[:-1]:
        cursor = cursor[component]
    del cursor[path[-1]]


@pytest.mark.parametrize("field_path", REQUIRED_FIELD_PATHS, ids=lambda value: ".".join(map(str, value)))
def test_every_schema_field_is_required(tmp_path, monkeypatch, field_path):
    document, _hashes = _document_only(tmp_path)
    _delete_path(document, field_path)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    with pytest.raises(F.FloorPairSpecError):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_mutation_01_unknown_key_is_rejected_only_by_exact_loader(tmp_path, monkeypatch):
    document, _hashes = _document_only(tmp_path)
    document["unknown_mutation_key"] = "must fail"
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: pytest.fail("unknown key must fail before calibration"),
    )
    with pytest.raises(F.FloorPairSpecError, match="unknown"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


@pytest.mark.parametrize("removed_field", ("execution_contract", "protocol"))
def test_removed_claim_only_schema_fields_are_rejected_as_unknown(
    tmp_path, monkeypatch, removed_field
):
    document, _hashes = _document_only(tmp_path)
    if removed_field == "execution_contract":
        document["provenance"][removed_field] = {
            "path": "refs/calibration.json",
            "sha256": document["provenance"]["calibration"]["sha256"],
        }
    else:
        document["cells"][0][removed_field] = "silo"
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairSpecError, match=removed_field):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_mutation_02_valid_spec_with_wrong_expected_sha256_is_rejected(
    tmp_path, monkeypatch
):
    document, _hashes = _document_only(tmp_path)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairBindingError, match="sha256"):
        F.load_frozen_spec(Path("spec.json"), "0" * 64, repo_root=tmp_path)


def test_mutation_03_head_blob_byte_mismatch_is_rejected(tmp_path, monkeypatch):
    document, _hashes = _document_only(tmp_path)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path, head_overrides={"spec.json": raw + b"\n"})
    with pytest.raises(F.FloorPairBindingError, match="HEAD tracked blob"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


@pytest.mark.parametrize("operation", ("head", "show"))
def test_git_startup_failure_is_normalized_to_driver_binding_error(
    tmp_path, monkeypatch, operation
):
    def missing_git(*args, **kwargs):
        raise FileNotFoundError("git fixture missing")

    monkeypatch.setattr(F.subprocess, "run", missing_git)
    with pytest.raises(F.FloorPairBindingError, match="git"):
        if operation == "head":
            F._git_head(tmp_path)
        else:
            F._git_show_head(tmp_path, "spec.json")


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b'{"schema":NaN}', "非有限"),
        (b'{"schema":"a","schema":"b"}', "duplicate"),
    ],
)
def test_nonfinite_and_duplicate_json_are_rejected(tmp_path, monkeypatch, raw, message):
    _write_inputs(tmp_path)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairSpecError, match=message):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("environment", "clocks_per_us"), True),
        (("cells", 0, "perf_config", "reps"), False),
        (("windows", 0, "sample_count"), 0),
        (("cells", 0, "perf_config", "extime"), "1"),
        (("environment", "use_perf"), 0),
        (("cells", 0, "perf_config", "workload", "extra"), "x"),
    ],
)
def test_type_bool_range_and_nested_unknown_keys_fail_closed(
    tmp_path, monkeypatch, path, value
):
    document, _hashes = _document_only(tmp_path)
    cursor = document
    for component in path[:-1]:
        cursor = cursor[component]
    cursor[path[-1]] = value
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    with pytest.raises(F.FloorPairSpecError):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_loader_rejects_symlink_and_checkout_escape(tmp_path, monkeypatch):
    hashes = _write_inputs(tmp_path)
    document = _valid_document(hashes)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.json"
    outside.write_bytes(raw)
    with pytest.raises(F.FloorPairBindingError, match="repo_root 外"):
        F.load_frozen_spec(outside, hashlib.sha256(raw).hexdigest(), repo_root=tmp_path)
    (tmp_path / "spec-link.json").symlink_to(tmp_path / "spec.json")
    with pytest.raises(F.FloorPairBindingError, match="symlink"):
        F.load_frozen_spec(
            Path("spec-link.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


@pytest.mark.parametrize(
    ("verified", "message"),
    [
        (_verified_calibration(threads=2), "calibration threads"),
        (
            _verified_calibration(
                workload={
                    "ycsb_zipf_skew": "0.8",
                    "ycsb_rratio": "50",
                    "ycsb_rmw": "0",
                }
            ),
            "calibration workload",
        ),
        (_verified_calibration(records=2000), "calibration records"),
    ],
    ids=("threads", "workload", "records"),
)
def test_mutation_04_calibration_projection_gates_have_single_reason_inputs(
    tmp_path, monkeypatch, verified, message
):
    document, _hashes = _document_only(tmp_path)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    calls = []

    def load_verified_calibration(**kwargs):
        calls.append(kwargs)
        return verified

    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        load_verified_calibration,
    )
    with pytest.raises(F.FloorPairBindingError, match=message):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )
    assert calls == [
        {
            "env_tag": "test-env",
            "clocks_per_us": 2100,
            "attestation_mode": "required",
            "calibration_path": "refs/calibration.json",
            "calibration_sha256": document["provenance"]["calibration"]["sha256"],
            "repo_root": tmp_path.resolve(),
        }
    ]


def test_mutation_14_rejected_calibration_is_rejected_for_quality_only(
    tmp_path, monkeypatch
):
    document, _hashes = _document_only(tmp_path)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(quality_status="rejected"),
    )
    with pytest.raises(F.FloorPairBindingError, match="quality.status"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_mutation_15_calibration_records_mismatch_is_rejected_for_records_only(
    tmp_path, monkeypatch
):
    document, _hashes = _document_only(tmp_path)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(records=2000),
    )
    with pytest.raises(F.FloorPairBindingError, match="calibration records"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_calibration_none_mode_rejection_is_explicit_and_intentional(
    tmp_path, monkeypatch
):
    document, _hashes = _document_only(tmp_path)
    document["provenance"]["calibration"]["attestation_mode"] = "none"
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: SimpleNamespace(calibration=None),
    )
    with pytest.raises(F.FloorPairBindingError, match="意図的に受理しない"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_build_receipt_uses_real_binary_admission_validator_and_binds_sha(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    assert spec.artifacts[0].binary_sha256 == hashlib.sha256(
        (tmp_path / "bin/candidate.exe").read_bytes()
    ).hexdigest()
    record = json.loads(
        (tmp_path / "refs/candidate-receipt.json").read_text(encoding="utf-8")
    )
    receipt = F.s8b_binary_admission.validate_portable_binary_record(
        record, expected_policy=None
    )
    assert receipt["schema"] == F.s8b_binary_admission.RECEIPT_SCHEMA
    assert receipt["subject"]["binary_sha256"] == spec.artifacts[0].binary_sha256
    assert receipt["subject"]["trace"] is False


@pytest.mark.parametrize(
    "mutation",
    ("record-binary-sha", "receipt-trace"),
)
def test_build_receipt_binary_sha_and_trace_mutations_fail_closed(
    tmp_path, monkeypatch, mutation
):
    document, hashes = _document_only(tmp_path)
    receipt_path = tmp_path / "refs/candidate-receipt.json"
    record = json.loads(receipt_path.read_text(encoding="utf-8"))
    if mutation == "record-binary-sha":
        record["binary_sha256"] = "0" * 64
    else:
        record["admission_receipt"]["subject"]["trace"] = True
        unsigned = dict(record["admission_receipt"])
        unsigned.pop("receipt_sha256")
        record["admission_receipt"]["receipt_sha256"] = _map_sha256(
            unsigned, ensure_ascii=True
        )
    raw_receipt = _canonical(record) + b"\n"
    receipt_path.write_bytes(raw_receipt)
    hashes["refs/candidate-receipt.json"] = hashlib.sha256(raw_receipt).hexdigest()
    document["artifacts"][0]["build_receipt"]["sha256"] = hashes[
        "refs/candidate-receipt.json"
    ]
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    with pytest.raises(F.FloorPairBindingError, match="build receipt"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_mutation_16_probe_command_is_not_a_spec_field(tmp_path, monkeypatch):
    document, _hashes = _document_only(tmp_path)
    document["environment"]["probe_argv"] = ["/bin/false"]
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairSpecError, match="probe_argv"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )
    assert F.COMPETING_PROBE_ARGV == ("pgrep", "-af", r"ycsb_.*\.exe")


def test_mutation_19_source_commit_must_equal_loaded_head(tmp_path, monkeypatch):
    document, _hashes = _document_only(tmp_path)
    document["provenance"]["source_commit"] = "a" * 40
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    with pytest.raises(F.FloorPairBindingError, match="source_commit"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


@pytest.mark.parametrize("name", ("PATH", "LD_PRELOAD", "LD_LIBRARY_PATH"))
def test_mutation_20_extra_env_cannot_control_path_resolution(
    tmp_path, monkeypatch, name
):
    document, _hashes = _document_only(tmp_path)
    document["environment"]["extra_env"][name] = "/tmp/forged"
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairSpecError, match="PATH / LD_"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_pair_owns_artifact_references_and_requires_same_candidate(tmp_path, monkeypatch):
    document, _hashes = _document_only(tmp_path)
    document["pairs"][0]["sides"][1]["candidate_artifact_id"] = "reference-a"
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    with pytest.raises(F.FloorPairSpecError, match="同一 candidate"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_trace_self_declaration_must_be_false_but_is_not_binary_inspection(
    tmp_path, monkeypatch
):
    document, _hashes = _document_only(tmp_path)
    document["artifacts"][0]["trace"] = True
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairSpecError, match="trace"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def _multiple_pair_sample_document(hashes: dict[str, str]) -> dict[str, object]:
    document = _valid_document(hashes)
    second_pair = copy.deepcopy(document["pairs"][0])
    second_pair["pair_id"] = "pair-b"
    document["pairs"].append(second_pair)
    document["windows"][0]["sample_count"] = 2
    document["windows"][0]["pair_ids"] = ["pair-a", "pair-b"]
    document["statistics"]["closed_strata"].append(
        {"window_id": "window-a", "pair_id": "pair-b"}
    )
    return document


def test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order(
    tmp_path, monkeypatch
):
    hashes = _write_inputs(tmp_path)
    document = _multiple_pair_sample_document(hashes)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    spec = F.load_frozen_spec(
        Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
    )
    plan = F.make_measurement_plan(spec)
    assert [item.session_id for item in plan.sessions] == [
        "window-a.pair-b.s000001.reference",
        "window-a.pair-b.s000001.candidate_2",
        "window-a.pair-b.s000001.candidate_1",
        "window-a.pair-a.s000001.candidate_1",
        "window-a.pair-a.s000001.reference",
        "window-a.pair-a.s000001.candidate_2",
        "window-a.pair-b.s000000.candidate_2",
        "window-a.pair-b.s000000.candidate_1",
        "window-a.pair-b.s000000.reference",
        "window-a.pair-a.s000000.candidate_2",
        "window-a.pair-a.s000000.candidate_1",
        "window-a.pair-a.s000000.reference",
    ]
    assert [item.schedule_index for item in plan.sessions] == list(range(12))
    assert len({item.session_id for item in plan.sessions}) == 12
    assert F.make_measurement_plan(spec) == plan
    changed = dataclasses.replace(
        spec,
        randomization=dataclasses.replace(spec.randomization, seed_hex="02" * 32),
    )
    assert [item.session_id for item in F.make_measurement_plan(changed).sessions] != [
        item.session_id for item in plan.sessions
    ]


def test_gain_difference_uses_one_common_reference_and_registry_is_closed():
    result = F.compute_gain_difference(120.0, 90.0, 100.0)
    assert result.gain_1 == pytest.approx(0.2)
    assert result.gain_2 == pytest.approx(-0.1)
    assert result.difference == pytest.approx(0.3)
    assert F.apply_upper_statistic(F.STRATUM_UPPER_ID, [0.1, 0.3, 0.2]) == 0.3
    assert F.apply_upper_statistic(F.FINAL_COMBINER_ID, [0.4, 0.2]) == 0.4
    with pytest.raises(ValueError, match="未登録"):
        F.apply_upper_statistic("quantile/v1", [0.1])
    with pytest.raises(ValueError):
        F.compute_gain_difference(True, 1.0, 1.0)
    with pytest.raises(ValueError):
        F.apply_upper_statistic(F.STRATUM_UPPER_ID, [float("nan")])


def _request(spec: F.FloorPairSpec, session_id: str = "session-a") -> F.MeasurementRequest:
    return F.MeasurementRequest(
        session_id=session_id,
        binary_path=str(spec.repo_root / "bin/candidate.exe"),
        perf_config=spec.cells[0].perf_config,
        clocks_per_us=spec.environment.clocks_per_us,
        numactl_argv=spec.environment.numactl_argv,
        use_perf=spec.environment.use_perf,
        timeout_s=spec.environment.timeout_s,
        extra_env=spec.environment.extra_env,
    )


def test_mutation_12_production_adapter_passes_all_runner_arguments_and_sinks(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    captured = []

    def fake_measure_point(*args, **kwargs):
        captured.append((args, kwargs.copy()))
        kwargs["rep_returncodes"].extend([0, 0])
        kwargs["rep_observations"].extend(
            [
                {"rep_index": 0, "returncode": 0, "throughput": 101.0},
                {"rep_index": 1, "returncode": 0, "throughput": 103.0},
            ]
        )
        kwargs["rep_timestamps"].extend(
            [
                {"rep_index": 0, "started_at_ns": 1, "finished_at_ns": 2},
                {"rep_index": 1, "started_at_ns": 3, "finished_at_ns": 4},
            ]
        )
        return ScalePoint(
            records=args[1], threads=args[2], throughputs=[101.0, 103.0]
        )

    monkeypatch.setattr(F.runner, "measure_point", fake_measure_point)
    request = _request(spec)
    result = F._measure_with_runner(request)
    assert len(captured) == 1
    args, kwargs = captured[0]
    assert args == (
        request.binary_path,
        1000,
        1,
        2100,
    )
    assert set(kwargs) == {
        "extime", "reps", "workload", "numactl", "settle_first", "extra_env",
        "timeout_s", "require_all_reps", "require_complete_metrics",
        "rep_returncodes", "rep_observations", "rep_timestamps", "use_perf",
    }
    assert kwargs["extime"] == 1
    assert kwargs["reps"] == 2
    assert kwargs["workload"] == {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "50",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    }
    assert kwargs["numactl"] == ["numactl", "--interleave=all"]
    assert kwargs["settle_first"] is False
    assert kwargs["extra_env"] == {"FIXTURE_ENV": "1"}
    assert kwargs["timeout_s"] == 12
    assert kwargs["require_all_reps"] is True
    assert kwargs["require_complete_metrics"] is False
    assert kwargs["use_perf"] is False
    assert result.throughputs == (101.0, 103.0)
    assert result.rep_returncodes == (0, 0)
    assert len(result.rep_observations) == 2
    assert len(result.rep_timestamps) == 2


def _install_live_environment(
    monkeypatch: pytest.MonkeyPatch, *, env_tag: str = "test-env"
) -> None:
    def current_site(*, require_evidence=False):
        assert require_evidence is True
        return F.site_policy.OTHER

    monkeypatch.setattr(F.site_policy, "current_site", current_site)
    monkeypatch.setattr(
        F.env_contract,
        "REGISTRY",
        {"fixture": SimpleNamespace(attestation_mode="none", env_tag=env_tag)},
    )


def _install_live_and_trace(monkeypatch: pytest.MonkeyPatch, *, env_tag: str = "test-env"):
    _install_live_environment(monkeypatch, env_tag=env_tag)
    git_run = F.subprocess.run

    def subprocess_run(cmd, **kwargs):
        if cmd[0] == "nm":
            assert kwargs == {"capture_output": True, "text": True}
            return SimpleNamespace(returncode=0, stdout="0000 T ordinary_symbol\n", stderr="")
        return git_run(cmd, **kwargs)

    monkeypatch.setattr(F.buildcache.subprocess, "run", subprocess_run)


def _clear_probe(argv, timeout_s):
    assert tuple(argv) == F.COMPETING_PROBE_ARGV
    assert timeout_s == 2
    return 1, "", ""


def test_machine_env_tag_derivation_uses_real_production_helper_for_compute_and_other(
    monkeypatch,
):
    monkeypatch.setattr(
        F.env_contract,
        "lookup_required_attestation_contract",
        lambda: SimpleNamespace(env_tag="compute-env"),
    )
    assert F._machine_env_tag_for_site(F.site_policy.PEGASUS_COMPUTE) == "compute-env"
    monkeypatch.setattr(
        F.env_contract,
        "REGISTRY",
        {
            "required": SimpleNamespace(
                attestation_mode="required", env_tag="compute-env"
            ),
            "none": SimpleNamespace(attestation_mode="none", env_tag="other-env"),
        },
    )
    assert F._machine_env_tag_for_site(F.site_policy.OTHER) == "other-env"


@pytest.mark.parametrize(
    "site",
    (F.site_policy.PEGASUS_LOGIN, F.site_policy.PEGASUS_SUSPECT, "UNKNOWN"),
)
def test_machine_env_tag_derivation_rejects_login_suspect_and_unknown(site):
    with pytest.raises(F.FloorPairRunError) as excinfo:
        F._machine_env_tag_for_site(site)
    assert excinfo.value.status == "environment_mismatch"


def test_machine_env_tag_derivation_rejects_ambiguous_registry(monkeypatch):
    monkeypatch.setattr(
        F.env_contract,
        "REGISTRY",
        {
            "none-a": SimpleNamespace(attestation_mode="none", env_tag="env-a"),
            "none-b": SimpleNamespace(attestation_mode="none", env_tag="env-b"),
        },
    )
    with pytest.raises(F.FloorPairRunError, match="一意"):
        F._machine_env_tag_for_site(F.site_policy.OTHER)


@pytest.mark.parametrize(
    "site", (F.site_policy.PEGASUS_LOGIN, F.site_policy.PEGASUS_SUSPECT)
)
def test_login_and_suspect_are_rejected_before_output_reservation(
    tmp_path, monkeypatch, site
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    monkeypatch.setattr(
        F.site_policy,
        "current_site",
        lambda *, require_evidence=False: site,
    )
    with pytest.raises(F.FloorPairRunError) as excinfo:
        F.run_window(
            spec, plan, "window-a", probe_fn=_clear_probe, now_fn=lambda: NOW
        )
    assert excinfo.value.status == "environment_mismatch"
    assert not (tmp_path / "out/window-a.jsonl").exists()


def test_mutation_17_site_detection_requires_fail_closed_evidence(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    evidence_arguments = []

    def evidence_sensitive_site(*, require_evidence=False):
        evidence_arguments.append(require_evidence)
        return (
            F.site_policy.PEGASUS_SUSPECT
            if require_evidence
            else F.site_policy.OTHER
        )

    monkeypatch.setattr(F.site_policy, "current_site", evidence_sensitive_site)
    _install_complete_measurement(monkeypatch)
    with pytest.raises(F.FloorPairRunError) as excinfo:
        F.run_window(
            spec, plan, "window-a", probe_fn=_clear_probe, now_fn=lambda: NOW
        )
    assert excinfo.value.status == "environment_mismatch"
    assert evidence_arguments == [True]
    assert not (tmp_path / "out/window-a.jsonl").exists()


def test_live_site_must_equal_spec_site_before_output_reservation(
    tmp_path, monkeypatch
):
    hashes = _write_inputs(tmp_path)
    document = _valid_document(hashes)
    document["environment"]["site"] = F.site_policy.PEGASUS_COMPUTE
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    spec = F.load_frozen_spec(
        Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    with pytest.raises(F.FloorPairRunError, match="live site"):
        F.run_window(
            spec, plan, "window-a", probe_fn=_clear_probe, now_fn=lambda: NOW
        )
    assert not (tmp_path / "out/window-a.jsonl").exists()


def _complete_scale_point(
    args: tuple[object, ...],
    kwargs: dict[str, object],
    *,
    throughputs: tuple[float, ...] = (100.0, 102.0),
) -> ScalePoint:
    kwargs["rep_returncodes"].extend(0 for _value in throughputs)
    kwargs["rep_observations"].extend(
        {"rep_index": index, "returncode": 0, "throughput": value}
        for index, value in enumerate(throughputs)
    )
    kwargs["rep_timestamps"].extend(
        {
            "rep_index": index,
            "started_at_ns": index * 2 + 1,
            "finished_at_ns": index * 2 + 2,
        }
        for index in range(len(throughputs))
    )
    return ScalePoint(
        records=args[1],
        threads=args[2],
        throughputs=list(throughputs),
    )


def _install_complete_measurement(
    monkeypatch: pytest.MonkeyPatch,
    *,
    throughputs: tuple[float, ...] = (100.0, 102.0),
) -> None:
    def measure_point(*args, **kwargs):
        return _complete_scale_point(args, kwargs, throughputs=throughputs)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _rewrite_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def test_run_window_orders_pre_measure_post_and_records_all_sessions(tmp_path, monkeypatch):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    events = []

    def probe(argv, timeout_s):
        events.append("probe")
        return 1, "", ""

    def measure_point(*args, **kwargs):
        events.append("measure")
        return _complete_scale_point(args, kwargs)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)

    result = F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=probe,
        now_fn=lambda: NOW,
    )
    assert result.status == "complete"
    assert len(events) == 9
    for offset in range(0, 9, 3):
        assert events[offset] == "probe"
        assert events[offset + 1] == "measure"
        assert events[offset + 2] == "probe"
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    assert [record["event"] for record in records] == [
        "header", "session", "session", "session", "terminal"
    ]
    assert records[-1]["status"] == "complete"


def test_measure_exception_still_runs_post_probe_and_closes_remaining_plan(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    probes = []

    def probe(argv, timeout_s):
        probes.append(len(probes))
        return 1, "", ""

    def failed_measure_point(*args, **kwargs):
        raise RuntimeError("fixture failure")

    monkeypatch.setattr(F.runner, "measure_point", failed_measure_point)

    result = F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=probe,
        now_fn=lambda: NOW,
    )
    assert result.status == "incomplete"
    assert probes == [0, 1]
    sessions = _load_jsonl(tmp_path / "out/window-a.jsonl")[1:-1]
    assert sessions[0]["status"] == "measure_failed"
    assert [record["status"] for record in sessions[1:]] == [
        "not_run_after_fail_closed", "not_run_after_fail_closed"
    ]


def test_mutation_05_real_trace_inspection_call_rejects_before_probe_and_measure(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_environment(monkeypatch)
    inspected = []
    git_run = F.subprocess.run

    def subprocess_run(cmd, **kwargs):
        if cmd[0] == "nm":
            inspected.append(cmd)
            assert kwargs == {"capture_output": True, "text": True}
            return SimpleNamespace(
                returncode=0,
                stdout="0000 T izanagi_trace_fixture\n",
                stderr="",
            )
        return git_run(cmd, **kwargs)

    monkeypatch.setattr(F.buildcache.subprocess, "run", subprocess_run)
    measure_calls = []
    probe_calls = []

    def measure_point(*args, **kwargs):
        measure_calls.append(args)
        return _complete_scale_point(args, kwargs)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)

    def probe(argv, timeout_s):
        probe_calls.append((argv, timeout_s))
        return 1, "", ""

    F.run_window(spec, plan, "window-a", probe_fn=probe, now_fn=lambda: NOW)
    sessions = _load_jsonl(tmp_path / "out/window-a.jsonl")[1:-1]
    first_session = plan.sessions[0]
    first_artifact = next(
        artifact
        for artifact in spec.artifacts
        if artifact.artifact_id == first_session.artifact_id
    )
    assert inspected == [
        ["nm", "-C", str(tmp_path / first_artifact.binary_relpath)]
    ]
    assert sessions[0]["status"] == "binary_binding_failed"
    assert measure_calls == []
    assert probe_calls == []


def test_mutation_06_live_env_mismatch_rejects_before_output_reservation(
    tmp_path, monkeypatch
):
    system_elf = next(
        path for path in (Path("/usr/bin/true"), Path("/bin/true")) if path.is_file()
    )
    hashes = _write_inputs(tmp_path)
    elf_raw = system_elf.read_bytes()
    for tag in ("candidate", "reference"):
        binary_relpath = f"bin/{tag}.exe"
        receipt_relpath = f"refs/{tag}-receipt.json"
        (tmp_path / binary_relpath).write_bytes(elf_raw)
        hashes[binary_relpath] = hashlib.sha256(elf_raw).hexdigest()
        record = _portable_build_record(
            binary_relpath, hashes[binary_relpath], tag=tag
        )
        receipt_raw = _canonical(record) + b"\n"
        (tmp_path / receipt_relpath).write_bytes(receipt_raw)
        hashes[receipt_relpath] = hashlib.sha256(receipt_raw).hexdigest()
    document = _valid_document(hashes)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    spec = F.load_frozen_spec(
        Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
    )
    plan = F.make_measurement_plan(spec)
    seen_evidence = []

    def current_site(*, require_evidence=False):
        seen_evidence.append(require_evidence)
        return F.site_policy.OTHER

    monkeypatch.setattr(F.site_policy, "current_site", current_site)
    monkeypatch.setattr(
        F.env_contract,
        "REGISTRY",
        {"foreign": SimpleNamespace(attestation_mode="none", env_tag="foreign-env")},
    )
    measure_calls = []

    def measure_point(*args, **kwargs):
        measure_calls.append(args)
        return _complete_scale_point(args, kwargs)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)

    with pytest.raises(F.FloorPairRunError) as excinfo:
        F.run_window(
            spec,
            plan,
            "window-a",
            probe_fn=_clear_probe,
            now_fn=lambda: NOW,
        )
    assert excinfo.value.status == "environment_mismatch"
    assert seen_evidence == [True]
    assert not (tmp_path / "out/window-a.jsonl").exists()
    assert measure_calls == []


def test_mutation_10_exclusive_create_rejects_existing_path_before_measurement(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    output = tmp_path / "out/window-a.jsonl"
    output.write_bytes(b"existing artifact\n")
    calls = []

    def measure_point(*args, **kwargs):
        calls.append(args)
        return _complete_scale_point(args, kwargs)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)

    with pytest.raises(FileExistsError):
        F.run_window(
            spec,
            plan,
            "window-a",
            probe_fn=_clear_probe,
            now_fn=lambda: NOW,
        )
    assert output.read_bytes() == b"existing artifact\n"
    assert calls == []


def test_runtime_head_must_complete_source_commit_three_way_binding(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    monkeypatch.setattr(F, "_git_head", lambda root: "a" * 40)
    with pytest.raises(F.FloorPairRunError, match="runtime HEAD") as excinfo:
        F.run_window(
            spec, plan, "window-a", probe_fn=_clear_probe, now_fn=lambda: NOW
        )
    assert excinfo.value.status == "source_commit_mismatch"
    assert not (tmp_path / "out/window-a.jsonl").exists()


def test_output_open_uses_all_five_required_flags(tmp_path, monkeypatch):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    observed = []
    real_open = os.open

    def recording_open(path, flags, mode=0o777):
        observed.append(flags)
        return real_open(path, flags, mode)

    monkeypatch.setattr(F.os, "open", recording_open)
    _install_complete_measurement(monkeypatch)
    F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=_clear_probe,
        now_fn=lambda: NOW,
    )
    required = os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW
    assert observed == [required]


def _run_production(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    values_by_role: dict[str, tuple[float, float]],
) -> tuple[F.FloorPairSpec, F.MeasurementPlan]:
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    roles = [session.role for session in plan.sessions]
    calls = []

    def fake_measure_point(*args, **kwargs):
        role = roles[len(calls)]
        calls.append(role)
        values = values_by_role[role]
        kwargs["rep_returncodes"].extend([0, 0])
        kwargs["rep_observations"].extend(
            [
                {"rep_index": 0, "returncode": 0, "throughput": values[0]},
                {"rep_index": 1, "returncode": 0, "throughput": values[1]},
            ]
        )
        kwargs["rep_timestamps"].extend(
            [
                {"rep_index": 0, "started_at_ns": 1, "finished_at_ns": 2},
                {"rep_index": 1, "started_at_ns": 3, "finished_at_ns": 4},
            ]
        )
        return ScalePoint(
            records=args[1], threads=args[2], throughputs=list(values)
        )

    monkeypatch.setattr(F.runner, "measure_point", fake_measure_point)
    result = F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=_clear_probe,
        now_fn=lambda: NOW,
    )
    assert result.status == "complete"
    assert calls == roles
    return spec, plan


def _run_multi_pair_sample_production(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[F.FloorPairSpec, F.MeasurementPlan]:
    hashes = _write_inputs(tmp_path)
    document = _multiple_pair_sample_document(hashes)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )
    spec = F.load_frozen_spec(
        Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    calls = []

    def measure_point(*args, **kwargs):
        calls.append(args)
        return _complete_scale_point(args, kwargs)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)
    result = F.run_window(
        spec, plan, "window-a", probe_fn=_clear_probe, now_fn=lambda: NOW
    )
    assert result.status == "complete"
    assert len(calls) == 12
    return spec, plan


def test_production_adapter_artifact_finalizes_from_raw_medians(tmp_path, monkeypatch):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        {
            "candidate_1": (120.0, 120.0),
            "candidate_2": (110.0, 110.0),
            "reference": (100.0, 100.0),
        },
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "generated"
    assert result.upper == pytest.approx(0.1)
    assert result.candidate_floor == pytest.approx(0.1)
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    assert summary["proof_limitations"] == {
        "section": "証明していないこと",
        "items": list(F.NOT_PROVEN),
    }
    sample = summary["derivation"][0]["samples"][0]
    assert sample["session_medians"] == {
        "candidate_1": 120.0,
        "candidate_2": 110.0,
        "reference": 100.0,
    }


@pytest.mark.parametrize(
    ("target", "field", "value"),
    [
        ("header", "format", "forged-format/v1"),
        ("header", "loaded_head", "a" * 40),
        ("header", "runtime_head", "a" * 40),
        ("header", "randomization_algorithm", "fixed-order/v1"),
        ("header", "seed_hex", "02" * 32),
        ("terminal", "status", "incomplete"),
    ],
)
def test_finalizer_revalidates_complete_header_and_terminal_contract(
    tmp_path, monkeypatch, target, field, value
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        {
            "candidate_1": (120.0, 120.0),
            "candidate_2": (110.0, 110.0),
            "reference": (100.0, 100.0),
        },
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    record = records[0] if target == "header" else records[-1]
    record[field] = value
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match=target):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


def test_mutation_18_recorded_multiple_pair_sample_order_must_match_plan(
    tmp_path, monkeypatch
):
    spec, plan = _run_multi_pair_sample_production(tmp_path, monkeypatch)
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    assert [record["session_id"] for record in records[1:-1]] == [
        session.session_id for session in plan.sessions
    ]
    records[1], records[2] = records[2], records[1]
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match="session 順"):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


def test_mutation_07_one_noncomplete_session_makes_whole_floor_missing(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        {
            "candidate_1": (120.0, 120.0),
            "candidate_2": (110.0, 110.0),
            "reference": (100.0, 100.0),
        },
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    records[1]["status"] = "measure_incomplete"
    _rewrite_jsonl(artifact, records)
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "not_generated_missing_samples"
    assert result.upper is None
    assert result.candidate_floor is None


def test_nonfinite_measurement_is_recorded_incomplete_not_serialized_as_nan(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)

    def nonfinite(*args, **kwargs):
        return _complete_scale_point(
            args, kwargs, throughputs=(100.0, float("nan"))
        )

    monkeypatch.setattr(F.runner, "measure_point", nonfinite)

    F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=_clear_probe,
        now_fn=lambda: NOW,
    )
    raw = (tmp_path / "out/window-a.jsonl").read_text(encoding="utf-8")
    assert "NaN" not in raw
    sessions = _load_jsonl(tmp_path / "out/window-a.jsonl")[1:-1]
    assert sessions[0]["status"] == "measure_incomplete"
    assert sessions[0]["throughputs"] == [100.0, None]


def test_mutation_08_upper_at_or_above_one_is_preserved_and_not_clamped(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        {
            "candidate_1": (300.0, 300.0),
            "candidate_2": (100.0, 100.0),
            "reference": (100.0, 100.0),
        },
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "not_generated_upper_out_of_domain"
    assert result.upper == 2.0
    assert result.candidate_floor is None
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    assert summary["upper"] == 2.0
    assert summary["candidate_floor"] is None


def test_mutations_09_and_13_forged_production_named_high_measure_is_rejected(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)

    def forged_measure(request):
        raise AssertionError("高位 forged measure は呼ばれてはならない")

    forged_measure.__module__ = F._measure_with_runner.__module__
    forged_measure.__qualname__ = F._measure_with_runner.__qualname__
    with pytest.raises(TypeError, match="measure_fn"):
        F.run_window(
            spec,
            plan,
            "window-a",
            measure_fn=forged_measure,
            probe_fn=_clear_probe,
            now_fn=lambda: NOW,
        )
    assert not (tmp_path / "out/window-a.jsonl").exists()


def test_finalizer_rejects_duplicate_session_id_even_when_set_matches(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        {
            "candidate_1": (120.0, 120.0),
            "candidate_2": (110.0, 110.0),
            "reference": (100.0, 100.0),
        },
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    records.insert(2, copy.deepcopy(records[1]))
    records[-1]["recorded_session_count"] = 4
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match="session ID/count"):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


def test_summary_is_exclusive_create(tmp_path, monkeypatch):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        {
            "candidate_1": (120.0, 120.0),
            "candidate_2": (110.0, 110.0),
            "reference": (100.0, 100.0),
        },
    )
    summary = tmp_path / "out/summary.json"
    summary.write_bytes(b"existing summary\n")
    with pytest.raises(FileExistsError):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert summary.read_bytes() == b"existing summary\n"


def test_cli_execute_window_selects_the_named_production_adapter(
    tmp_path, monkeypatch, capfd
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    observed = []
    monkeypatch.setattr(F, "load_frozen_spec", lambda *args, **kwargs: spec)
    monkeypatch.setattr(F, "make_measurement_plan", lambda value: plan)

    def run_window(spec_arg, plan_arg, window_id, **kwargs):
        observed.append((spec_arg, plan_arg, window_id, kwargs))
        return F.WindowRunResult(
            status="complete",
            window_id=window_id,
            artifact_relpath="out/window-a.jsonl",
            artifact_sha256="0" * 64,
            session_count=3,
        )

    monkeypatch.setattr(F, "run_window", run_window)
    rc = F.main(
        [
            "--repo-root", str(tmp_path),
            "--spec", "spec.json",
            "--expected-sha256", "0" * 64,
            "--execute-window", "window-a",
        ]
    )
    assert rc == 0
    assert len(observed) == 1
    assert observed[0][0] is spec
    assert observed[0][1] is plan
    assert observed[0][2] == "window-a"
    assert "measure_fn" not in observed[0][3]
    assert observed[0][3]["probe_fn"] is F._run_probe
    assert observed[0][3]["now_fn"] is F._utc_now
    assert json.loads(capfd.readouterr().out)["status"] == "complete"


def test_validate_only_prints_plan_without_reserving_output(tmp_path, monkeypatch, capfd):
    spec, _document, raw = _prepare_spec(tmp_path, monkeypatch)
    expected = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(F, "load_frozen_spec", lambda *args, **kwargs: spec)
    rc = F.main(
        [
            "--repo-root", str(tmp_path),
            "--spec", "spec.json",
            "--expected-sha256", expected,
            "--validate-only",
        ]
    )
    assert rc == 0
    output = json.loads(capfd.readouterr().out)
    assert output["schema"] == F.PLAN_SCHEMA
    assert output["plan_sha256"] == F.make_measurement_plan(spec).plan_sha256
    assert not (tmp_path / "out/window-a.jsonl").exists()
    assert not (tmp_path / "out/summary.json").exists()


def test_module_source_has_no_frozen_fallback_or_publish_bypass():
    source = Path(F.__file__).read_text(encoding="utf-8")
    assert ".get(" not in source
    assert "setdefault(" not in source
    assert "from .p2_2" not in source
    assert "between_run_floor" not in source
    assert "p3_s4_loop" not in source
    forbidden_publish_names = ("un" + "link(", "re" + "name(")
    for name in forbidden_publish_names:
        assert name not in source


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
