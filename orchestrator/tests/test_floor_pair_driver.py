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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.calibrator.model import ScalePoint
from orchestrator.campaign import floor_pair_driver as F


NOW = datetime(2030, 1, 1, 0, 30, tzinfo=timezone.utc)
PARENT = "b" * 40
HEAD = "d" * 40
SOURCE_COMMIT = PARENT
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
    genome_canonical: str | None = None,
) -> dict[str, object]:
    """実 s8b-binary-admission/v3 reader を通る最小 portable record。"""
    admission_module = F.s8b_binary_admission
    genome = (
        json.dumps({"fixture": tag}, sort_keys=True, separators=(",", ":"))
        if genome_canonical is None
        else genome_canonical
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
            "source_protection": {
                "kind": "sealed-build",
                "source_snapshot_sha256": materialization_sha256,
                "expected_materialization_sha256": materialization_sha256,
                "binary_sha256": binary_sha256,
                "compiler_input_manifest_sha256": compiler_input_sha256,
            },
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


def _write_inputs(
    root: Path,
    *,
    genome_canonicals: dict[str, str] | None = None,
) -> dict[str, str]:
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
                "bin/candidate.exe",
                result["bin/candidate.exe"],
                tag="candidate",
                genome_canonical=(
                    None
                    if genome_canonicals is None
                    else genome_canonicals["candidate"]
                ),
            )
        )
        + b"\n",
        "refs/reference-receipt.json": _canonical(
            _portable_build_record(
                "bin/reference.exe",
                result["bin/reference.exe"],
                tag="reference",
                genome_canonical=(
                    None
                    if genome_canonicals is None
                    else genome_canonicals["reference"]
                ),
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
            "reference_measurements_per_pair_sample": (
                F.REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE
            ),
            "difference_formula": F.DIFFERENCE_FORMULA,
        },
        "failure_policy": {
            "policy": F.FAILURE_POLICY_ID,
            "retry_count": 0,
            "require_all_reps": True,
            "max_dropped_fraction": "1/20",
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
    blob_overrides: dict[str, bytes] | None = None,
    ancestor_returncode: int = 0,
) -> list[tuple[str, ...]]:
    overrides = {} if blob_overrides is None else dict(blob_overrides)
    calls: list[tuple[str, ...]] = []

    def fake_run(cmd, **kwargs):
        if cmd[0] != "git":
            return REAL_SUBPROCESS_RUN(cmd, **kwargs)
        calls.append(tuple(cmd))
        assert kwargs == {
            "capture_output": True,
            "check": False,
            "timeout": F._GIT_TIMEOUT_S,
        }
        assert cmd[:3] == ["git", "-C", str(root)]
        if cmd[3] == "rev-parse":
            assert cmd[3:] == ["rev-parse", "HEAD"]
            return _fake_completed(0, (HEAD + "\n").encode("ascii"))
        if cmd[3] == "show":
            assert len(cmd) == 5
            revision, separator, relpath = cmd[4].partition(":")
            assert separator == ":"
            assert revision in {"HEAD", HEAD}
            raw = overrides[cmd[4]] if cmd[4] in overrides else (root / relpath).read_bytes()
            return _fake_completed(0, raw)
        assert cmd[3:5] == ["merge-base", "--is-ancestor"]
        assert len(cmd) == 7
        assert cmd[6] == HEAD
        return _fake_completed(ancestor_returncode, b"")

    monkeypatch.setattr(F.subprocess, "run", fake_run)
    return calls


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


def _real_git(root: Path, *args: str) -> bytes:
    completed = REAL_SUBPROCESS_RUN(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, bytes(completed.stderr).decode(
        "utf-8", errors="replace"
    )
    return bytes(completed.stdout)


def _init_real_git_repo(tmp_path: Path) -> tuple[Path, dict[str, str], str, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _real_git(root, "init")
    _real_git(root, "config", "user.name", "Floor Pair Test")
    _real_git(root, "config", "user.email", "floor-pair@example.invalid")
    hashes = _write_inputs(root)
    (root / "out/.gitkeep").write_bytes(b"")
    _real_git(root, "add", "--", "refs", "bin", "out/.gitkeep")
    _real_git(root, "-c", "commit.gpgsign=false", "commit", "-m", "fixed inputs")
    parent = _real_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    primary_branch = (
        _real_git(root, "branch", "--show-current").decode("ascii").strip()
    )
    return root, hashes, parent, primary_branch


def _write_real_spec(root: Path, hashes: dict[str, str], parent: str) -> bytes:
    document = _valid_document(hashes)
    document["provenance"]["source_commit"] = parent
    raw = _canonical(document)
    (root / "spec.json").write_bytes(raw)
    return raw


def _install_calibration_verifier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )


def _prepare_spec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    document: dict[str, object] | None = None,
    raw: bytes | None = None,
    expected_sha256: str | None = None,
    blob_overrides: dict[str, bytes] | None = None,
    verified=None,
) -> tuple[F.FloorPairSpec, dict[str, object], bytes]:
    hashes = _write_inputs(tmp_path)
    effective_document = _valid_document(hashes) if document is None else document
    effective_raw = _canonical(effective_document) if raw is None else raw
    (tmp_path / "spec.json").write_bytes(effective_raw)
    _install_git(monkeypatch, tmp_path, blob_overrides=blob_overrides)
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


def _prepare_configured_spec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    configure,
) -> tuple[F.FloorPairSpec, dict[str, object], bytes]:
    hashes = _write_inputs(tmp_path)
    document = _valid_document(hashes)
    configure(document)
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
    return spec, document, raw


def test_real_git_strict_ancestor_loads_after_later_unrelated_commit(
    tmp_path, monkeypatch
):
    root, hashes, parent, _primary_branch = _init_real_git_repo(tmp_path)
    raw = _write_real_spec(root, hashes, parent)
    _real_git(root, "add", "--", "spec.json")
    _real_git(root, "-c", "commit.gpgsign=false", "commit", "-m", "freeze spec")
    freeze_head = _real_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    (root / "later.txt").write_bytes(b"unrelated change after freeze\n")
    _real_git(root, "add", "--", "later.txt")
    _real_git(root, "-c", "commit.gpgsign=false", "commit", "-m", "later change")
    loaded_head = _real_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    checkout = tmp_path / "checkout"
    _real_git(root, "worktree", "add", "--detach", str(checkout), loaded_head)
    _install_calibration_verifier(monkeypatch)

    spec = F.load_frozen_spec(
        Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=checkout
    )

    assert (checkout / "out/.gitkeep").is_file()
    assert spec.provenance.source_commit == parent
    assert spec.loaded_head == loaded_head
    assert parent != freeze_head != loaded_head


def test_real_git_nonancestor_source_commit_is_rejected(
    tmp_path, monkeypatch
):
    root, hashes, _parent, primary_branch = _init_real_git_repo(tmp_path)
    _real_git(root, "checkout", "-b", "unrelated-lineage")
    (root / "unrelated.txt").write_bytes(b"separate lineage\n")
    _real_git(root, "add", "--", "unrelated.txt")
    _real_git(root, "-c", "commit.gpgsign=false", "commit", "-m", "unrelated")
    unrelated_commit = _real_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    _real_git(root, "checkout", primary_branch)
    raw = _write_real_spec(root, hashes, unrelated_commit)
    _real_git(root, "add", "--", "spec.json")
    _real_git(root, "-c", "commit.gpgsign=false", "commit", "-m", "freeze spec")
    _install_calibration_verifier(monkeypatch)

    with pytest.raises(F.FloorPairBindingError, match="祖先でない"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=root
        )


def test_real_git_worktree_spec_bytes_changed_after_commit_are_rejected(
    tmp_path, monkeypatch
):
    root, hashes, parent, _primary_branch = _init_real_git_repo(tmp_path)
    raw = _write_real_spec(root, hashes, parent)
    _real_git(root, "add", "--", "spec.json")
    _real_git(root, "-c", "commit.gpgsign=false", "commit", "-m", "freeze spec")
    changed_raw = raw + b"\n"
    (root / "spec.json").write_bytes(changed_raw)
    _install_calibration_verifier(monkeypatch)

    with pytest.raises(F.FloorPairBindingError, match="HEAD tracked blob"):
        F.load_frozen_spec(
            Path("spec.json"),
            hashlib.sha256(changed_raw).hexdigest(),
            repo_root=root,
        )


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
    F.PlannedMeasurement,
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
    assert (
        "落ちた標本による残存標本数の減少を許容限界の被覆確率へ補正せず、"
        "残存標本で 95% 被覆を保つことを証明しない。"
    ) in F.NOT_PROVEN
    assert (
        "campaign 合算の 5% は pair 間の欠測の偏りを制限しない "
        "(stratum ごとの件数は報告する)。"
    ) in F.NOT_PROVEN
    assert (
        "spec bytes と loaded HEAD の tracked blob の byte 一致、および"
        " source_commit が loaded HEAD の真の祖先であることだけを保証する。"
        "その間の変更内容は制限しない。commit OID の同値と、実行中 module bytes が"
        "記録 commit に対応することは保証しない。定数が D1699 の裁定値であることを"
        "証明する独立な pin も freeze receipt も無い。"
    ) in F.NOT_PROVEN
    assert (
        "測定実体は module 属性であり、同一 process 内でこれを差し替える経路は防がない。"
    ) in F.NOT_PROVEN
    assert len(F.NOT_PROVEN) == 10
    assert "environment_mismatch" not in F.SESSION_STATUSES


def test_all_four_semantic_schema_identifiers_are_bumped():
    assert F.SPEC_SCHEMA == "floor-pair-spec/v3"
    assert F.PLAN_SCHEMA == "floor-pair-plan/v2"
    assert F.WINDOW_SCHEMA == "floor-pair-window/v3"
    assert F.SUMMARY_SCHEMA == "floor-pair-summary/v3"


def test_loader_rejects_v2_schema_on_v3_shaped_spec(tmp_path, monkeypatch):
    document, _hashes = _document_only(tmp_path)
    document["schema"] = "floor-pair-spec/v2"
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: pytest.fail("v2 schema must fail before calibration"),
    )

    with pytest.raises(F.FloorPairSpecError, match="schema"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_plan_v1_schema_is_rejected_with_current_plan_shape(tmp_path, monkeypatch):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    stale_plan = dataclasses.replace(plan, schema="floor-pair-plan/v1")

    with pytest.raises(F.FloorPairBindingError, match="canonical plan"):
        F._assert_plan_exact(spec, stale_plan, error_type=F.FloorPairBindingError)


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
        "reference_measurements_per_pair_sample", "difference_formula",
    )),
    ("statistics", "closed_strata", 0, "window_id"),
    ("statistics", "closed_strata", 0, "pair_id"),
    ("failure_policy", "policy"),
    ("failure_policy", "retry_count"),
    ("failure_policy", "require_all_reps"),
    ("failure_policy", "max_dropped_fraction"),
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


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("policy", "all_planned_samples_required/v1"),
        ("max_dropped_fraction", "1/19"),
    ],
)
def test_d1641_failure_policy_is_the_only_accepted_wire_policy(
    tmp_path, monkeypatch, field, value
):
    document, _hashes = _document_only(tmp_path)
    document["failure_policy"][field] = value
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairSpecError, match=field):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reference_measurements_per_pair_sample", 1),
        ("difference_formula", "D=forged"),
    ],
)
def test_frozen_pair_statistics_require_exact_module_constants(
    tmp_path, monkeypatch, field, value
):
    document, _hashes = _document_only(tmp_path)
    document["statistics"][field] = value
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(monkeypatch, tmp_path)
    with pytest.raises(F.FloorPairSpecError, match=field):
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
    _install_git(
        monkeypatch,
        tmp_path,
        blob_overrides={f"{HEAD}:spec.json": raw + b"\n"},
    )
    with pytest.raises(F.FloorPairBindingError, match="HEAD tracked blob"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


def test_blob_queries_use_the_once_resolved_loaded_head(tmp_path, monkeypatch):
    document, _hashes = _document_only(tmp_path)
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    git_calls = _install_git(
        monkeypatch,
        tmp_path,
        blob_overrides={
            "HEAD:spec.json": raw + b"symbolic HEAD must not be queried",
            f"{HEAD}:spec.json": raw,
        },
    )
    _install_calibration_verifier(monkeypatch)

    spec = F.load_frozen_spec(
        Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
    )

    assert spec.loaded_head == HEAD
    assert sum(call[3:] == ("rev-parse", "HEAD") for call in git_calls) == 1
    blob_queries = [
        call[4]
        for call in git_calls
        if len(call) == 5 and call[3] == "show" and ":" in call[4]
    ]
    unique_receipt_paths = {
        artifact["build_receipt"]["path"] for artifact in document["artifacts"]
    }
    expected_blob_queries = Counter(
        [
            f"{HEAD}:spec.json",
            f"{HEAD}:{document['provenance']['calibration']['path']}",
            *(f"{HEAD}:{path}" for path in unique_receipt_paths),
        ]
    )
    assert Counter(blob_queries) == expected_blob_queries


def test_tracked_calibration_declared_sha_mismatch_is_rejected_for_sha_only(
    tmp_path, monkeypatch
):
    document, hashes = _document_only(tmp_path)
    calibration_path = tmp_path / "refs/calibration.json"
    calibration_raw = calibration_path.read_bytes()
    assert hashlib.sha256(calibration_raw).hexdigest() == hashes[
        "refs/calibration.json"
    ]
    assert hashes["refs/calibration.json"] != "0" * 64
    document["provenance"]["calibration"]["sha256"] = "0" * 64
    raw = _canonical(document)
    (tmp_path / "spec.json").write_bytes(raw)
    _install_git(
        monkeypatch,
        tmp_path,
        blob_overrides={f"{HEAD}:refs/calibration.json": calibration_raw},
    )
    monkeypatch.setattr(
        F.calibration_verify,
        "load_verified_calibration",
        lambda **kwargs: _verified_calibration(),
    )

    with pytest.raises(
        F.FloorPairBindingError, match="calibration artifact sha256 不一致"
    ):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=tmp_path
        )


@pytest.mark.parametrize("operation", ("head", "show", "ancestor"))
@pytest.mark.parametrize("failure", ("startup", "timeout"))
def test_git_startup_and_timeout_failures_are_normalized_to_driver_binding_error(
    tmp_path, monkeypatch, operation, failure
):
    def missing_git(*args, **kwargs):
        if failure == "startup":
            raise FileNotFoundError("git fixture missing")
        raise F.subprocess.TimeoutExpired(args[0], F._GIT_TIMEOUT_S)

    monkeypatch.setattr(F.subprocess, "run", missing_git)
    with pytest.raises(F.FloorPairBindingError, match="git"):
        if operation == "head":
            F._git_head(tmp_path)
        elif operation == "show":
            F._git_show_head(tmp_path, HEAD, "spec.json")
        else:
            F._git_is_ancestor(tmp_path, SOURCE_COMMIT, HEAD)


@pytest.mark.parametrize("operation", ("head", "show", "ancestor"))
def test_git_nonzero_exit_is_normalized_to_driver_binding_error(
    tmp_path, monkeypatch, operation
):
    monkeypatch.setattr(
        F.subprocess,
        "run",
        lambda *args, **kwargs: _fake_completed(2, b"", b"git fixture failure"),
    )
    with pytest.raises(F.FloorPairBindingError, match="git"):
        if operation == "head":
            F._git_head(tmp_path)
        elif operation == "show":
            F._git_show_head(tmp_path, HEAD, "spec.json")
        else:
            F._git_is_ancestor(tmp_path, SOURCE_COMMIT, HEAD)


@pytest.mark.parametrize(
    ("returncode", "expected"),
    [
        (0, True),
        (1, False),
    ],
)
def test_git_ancestor_uses_stdoutless_returncode_result(
    tmp_path, monkeypatch, returncode, expected
):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return _fake_completed(returncode, b"")

    monkeypatch.setattr(F.subprocess, "run", fake_run)

    assert F._git_is_ancestor(tmp_path, SOURCE_COMMIT, HEAD) is expected
    assert calls == [
        (
            [
                "git",
                "-C",
                str(tmp_path),
                "merge-base",
                "--is-ancestor",
                SOURCE_COMMIT,
                HEAD,
            ],
            {
                "capture_output": True,
                "check": False,
                "timeout": F._GIT_TIMEOUT_S,
            },
        )
    ]


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


def test_real_git_source_commit_equal_to_loaded_head_is_rejected_as_nonstrict(
    tmp_path, monkeypatch
):
    root, hashes, loaded_head, _primary_branch = _init_real_git_repo(tmp_path)
    raw = _write_real_spec(root, hashes, loaded_head)
    _real_git(root, "add", "--", "spec.json")
    _real_git(root, "-c", "commit.gpgsign=false", "commit", "-m", "replacement tree")
    replacement_commit = _real_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    _real_git(root, "replace", loaded_head, replacement_commit)
    _real_git(root, "checkout", "--detach", loaded_head)
    assert _real_git(root, "rev-parse", "HEAD").decode("ascii").strip() == loaded_head
    assert _real_git(root, "show", f"{loaded_head}:spec.json") == raw
    _install_calibration_verifier(monkeypatch)

    with pytest.raises(F.FloorPairBindingError, match="同一 commit"):
        F.load_frozen_spec(
            Path("spec.json"), hashlib.sha256(raw).hexdigest(), repo_root=root
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
    # Independently derived from the v3 receipt bytes: spec SHA-256
    # b1262edcd70aba9ac122ae31bba5f919aabc6616c2d9db4c7f728a2ed46dfa6a.
    # HMAC-SHA256 key = bytes.fromhex("01" * 32); fields are UTF-8 text
    # separated by NUL. Prefix = (schema, spec SHA, "window-a", pair, sample).
    # Ascending ranks with suffix "sample": a0=3a51f851, b1=52eec135,
    # b0=55f47d50, a1=6a93e4d9. Within each sample, rank sides with
    # ("side-session", side), then roles with
    # ("in-session-measurement", side, role). No production rank helper
    # was used to derive these session IDs or measurement-role goldens.
    assert [session.session_id for session in plan.sessions] == [
        "window-a.pair-a.s000000.candidate_1",
        "window-a.pair-a.s000000.candidate_2",
        "window-a.pair-b.s000001.candidate_2",
        "window-a.pair-b.s000001.candidate_1",
        "window-a.pair-b.s000000.candidate_2",
        "window-a.pair-b.s000000.candidate_1",
        "window-a.pair-a.s000001.candidate_1",
        "window-a.pair-a.s000001.candidate_2",
    ]
    expected_measurement_roles = [
        ("reference", "candidate"),
        ("reference", "candidate"),
        ("reference", "candidate"),
        ("candidate", "reference"),
        ("reference", "candidate"),
        ("reference", "candidate"),
        ("reference", "candidate"),
        ("reference", "candidate"),
    ]
    assert [
        tuple(measurement.role for measurement in session.measurements)
        for session in plan.sessions
    ] == expected_measurement_roles
    for offset in range(0, len(plan.sessions), 2):
        sample = plan.sessions[offset:offset + 2]
        assert len(sample) == 2
        assert len(
            {(item.window_id, item.pair_id, item.sample_index) for item in sample}
        ) == 1
        assert {item.side_id for item in sample} == set(F._SIDE_IDS)
        assert sum(
            measurement.role == "reference"
            for item in sample
            for measurement in item.measurements
        ) == F.REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE
    assert all(
        {measurement.role for measurement in session.measurements}
        == set(F._MEASUREMENT_ROLES)
        and [measurement.order_index for measurement in session.measurements] == [0, 1]
        and {
            measurement.role: measurement.artifact_id
            for measurement in session.measurements
        }
        == {"candidate": "candidate-a", "reference": "reference-a"}
        for session in plan.sessions
    )
    assert [item.schedule_index for item in plan.sessions] == list(range(8))
    assert len({item.session_id for item in plan.sessions}) == 8
    assert len(
        {
            measurement.measurement_id
            for session in plan.sessions
            for measurement in session.measurements
        }
    ) == 16
    assert F.make_measurement_plan(spec) == plan
    changed = dataclasses.replace(
        spec,
        randomization=dataclasses.replace(spec.randomization, seed_hex="02" * 32),
    )
    assert [item.session_id for item in F.make_measurement_plan(changed).sessions] != [
        item.session_id for item in plan.sessions
    ]


def test_gain_difference_uses_two_side_specific_references_and_registry_is_closed():
    result = F.compute_gain_difference(
        candidate_1_tps=120.0,
        reference_1_tps=100.0,
        candidate_2_tps=90.0,
        reference_2_tps=75.0,
    )
    assert result.gain_1 == pytest.approx(0.2)
    assert result.gain_2 == pytest.approx(0.2)
    assert result.difference == pytest.approx(0.0)
    assert F.apply_upper_statistic(F.STRATUM_UPPER_ID, [0.1, 0.3, 0.2]) == 0.3
    assert F.apply_upper_statistic(F.FINAL_COMBINER_ID, [0.4, 0.2]) == 0.4
    with pytest.raises(ValueError, match="未登録"):
        F.apply_upper_statistic("quantile/v1", [0.1])
    with pytest.raises(ValueError):
        F.compute_gain_difference(
            candidate_1_tps=True,
            reference_1_tps=1.0,
            candidate_2_tps=1.0,
            reference_2_tps=1.0,
        )
    with pytest.raises(ValueError):
        F.apply_upper_statistic(F.STRATUM_UPPER_ID, [float("nan")])


def _request(
    spec: F.FloorPairSpec, measurement_id: str = "measurement-a"
) -> F.MeasurementRequest:
    return F.MeasurementRequest(
        measurement_id=measurement_id,
        binary_path=str(spec.repo_root / "bin/candidate.exe"),
        perf_config=spec.cells[0].perf_config,
        clocks_per_us=spec.environment.clocks_per_us,
        numactl_argv=spec.environment.numactl_argv,
        use_perf=spec.environment.use_perf,
        timeout_s=spec.environment.timeout_s,
        extra_env=spec.environment.extra_env,
    )


def _complete_rep_observation(
    rep_index: int, throughput: float
) -> dict[str, object]:
    return {
        "rep_index": rep_index,
        "returncode": 0,
        "execution_failure": False,
        "counter_status": "not_required",
        "missing_perf_events": [],
        "perf_raw": {event: None for event in F.runner.PERF_EVENTS},
        "throughput": throughput,
    }


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
                _complete_rep_observation(0, 101.0),
                _complete_rep_observation(1, 103.0),
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
        _complete_rep_observation(index, value)
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


def _configure_campaign_shape(
    document: dict[str, object],
    *,
    sample_count: int,
    pair_count: int,
    window_count: int = 1,
) -> None:
    pair_template = document["pairs"][0]
    pairs = []
    pair_ids = []
    for index in range(pair_count):
        pair = copy.deepcopy(pair_template)
        pair_id = f"pair-{index:02d}"
        pair["pair_id"] = pair_id
        pairs.append(pair)
        pair_ids.append(pair_id)
    window_template = document["windows"][0]
    windows = []
    strata = []
    for index in range(window_count):
        window = copy.deepcopy(window_template)
        window_id = f"window-{index}"
        window["window_id"] = window_id
        window["campaign_id"] = f"campaign-{index}"
        window["not_before"] = f"2030-01-01T{index * 2:02d}:00:00Z"
        window["not_after"] = f"2030-01-01T{index * 2 + 1:02d}:00:00Z"
        window["sample_count"] = sample_count
        window["pair_ids"] = list(pair_ids)
        window["artifact_relpath"] = f"out/{window_id}.jsonl"
        windows.append(window)
        strata.extend(
            {"window_id": window_id, "pair_id": pair_id}
            for pair_id in pair_ids
        )
    document["pairs"] = pairs
    document["windows"] = windows
    document["statistics"]["closed_strata"] = strata


def _run_campaign_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    sample_count: int,
    pair_count: int,
    dropped_by_window: dict[str, int],
    window_count: int = 1,
    values_by_measurement: dict[tuple[str, str], tuple[float, float]] | None = None,
) -> tuple[F.FloorPairSpec, F.MeasurementPlan]:
    spec, _document, _raw = _prepare_configured_spec(
        tmp_path,
        monkeypatch,
        lambda document: _configure_campaign_shape(
            document,
            sample_count=sample_count,
            pair_count=pair_count,
            window_count=window_count,
        ),
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    measurement_values = (
        {
            ("candidate_1", "candidate"): (120.0, 120.0),
            ("candidate_1", "reference"): (100.0, 100.0),
            ("candidate_2", "candidate"): (110.0, 110.0),
            ("candidate_2", "reference"): (100.0, 100.0),
        }
        if values_by_measurement is None
        else values_by_measurement
    )
    for window in spec.windows:
        sessions = [
            session for session in plan.sessions if session.window_id == window.window_id
        ]
        planned_measurements = [
            (session, measurement)
            for session in sessions
            for measurement in session.measurements
        ]
        ordered_sample_keys = list(
            dict.fromkeys(
                (session.window_id, session.pair_id, session.sample_index)
                for session in sessions
            )
        )
        drop_keys = set(
            ordered_sample_keys[:dropped_by_window.get(window.window_id, 0)]
        )
        cursor = 0

        def measure_point(*args, **kwargs):
            nonlocal cursor
            session, measurement = planned_measurements[cursor]
            sample_key = (session.window_id, session.pair_id, session.sample_index)
            if sample_key in drop_keys:
                while cursor < len(planned_measurements):
                    current, _measurement = planned_measurements[cursor]
                    current_key = (
                        current.window_id,
                        current.pair_id,
                        current.sample_index,
                    )
                    if current_key != sample_key:
                        break
                    cursor += 1
                raise RuntimeError("fixture sample drop")
            cursor += 1
            return _complete_scale_point(
                args,
                kwargs,
                throughputs=measurement_values[(session.side_id, measurement.role)],
            )

        monkeypatch.setattr(F.runner, "measure_point", measure_point)
        result = F.run_window(
            spec,
            plan,
            window.window_id,
            probe_fn=_clear_probe,
            now_fn=lambda window=window: (
                window.not_before + (window.not_after - window.not_before) / 2
            ),
        )
        assert result.status == "complete"
    return spec, plan


def test_run_window_orders_three_probes_and_two_measurements_per_side_session(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    events = []
    measurement_paths = []

    def probe(argv, timeout_s):
        events.append("probe")
        return 1, "", ""

    def measure_point(*args, **kwargs):
        events.append("measure")
        measurement_paths.append(args[0])
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
    assert events == ["probe", "measure", "probe", "measure", "probe"] * 2
    artifacts = {artifact.artifact_id: artifact for artifact in spec.artifacts}
    assert measurement_paths == [
        str(tmp_path / artifacts[measurement.artifact_id].binary_relpath)
        for session in plan.sessions
        for measurement in session.measurements
    ]
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    assert [record["event"] for record in records] == [
        "header", "session", "session", "terminal"
    ]
    assert records[0]["planned_measurement_count"] == 4
    assert records[0]["measurements_per_session"] == 2
    assert records[0]["reference_measurements_per_pair_sample"] == 2
    assert records[0]["difference_formula"] == F.DIFFERENCE_FORMULA
    assert records[0]["reps_per_measurement"] == {"cell-a": 2}
    assert "reps_per_session" not in records[0]
    for session, record in zip(plan.sessions, records[1:-1], strict=True):
        assert record["side_id"] == session.side_id
        assert record["status"] == "complete"
        assert [item["measurement_id"] for item in record["measurements"]] == [
            measurement.measurement_id for measurement in session.measurements
        ]
        assert all(
            record[name]["status"] == "clear"
            for name in ("pre_probe", "mid_probe", "post_probe")
        )
    assert records[-1] == {
        "event": "terminal",
        "status": "complete",
        "window_id": "window-a",
        "planned_session_count": 2,
        "recorded_session_count": 2,
        "planned_measurement_count": 4,
        "recorded_measurement_count": 4,
        "planned_sample_count": 1,
        "dropped_sample_count": 0,
        "complete_sample_count": 1,
    }


def test_pre_probe_drop_closes_sample_and_continues_next_sample(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_configured_spec(
        tmp_path,
        monkeypatch,
        lambda document: document["windows"][0].update(sample_count=2),
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    probes = []

    def probe(argv, timeout_s):
        probes.append(len(probes))
        if len(probes) == 1:
            return 0, "999999 ycsb_fixture.exe\n", ""
        return 1, "", ""

    measure_calls = []

    def measure_point(*args, **kwargs):
        measure_calls.append(args)
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
    assert probes == list(range(9))
    assert len(measure_calls) == 4
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    sessions = records[1:-1]
    first_sample = sessions[:2]
    assert [record["status"] for record in first_sample] == [
        "pre_probe_competing",
        "not_run_sample_dropped",
    ]
    assert [record["error"] for record in first_sample[1:]] == ["sample_dropped"]
    assert [record["dropped_by_session_id"] for record in first_sample] == [
        None,
        first_sample[0]["session_id"],
    ]
    assert [record["status"] for record in sessions[2:]] == ["complete"] * 2
    assert records[-1]["planned_sample_count"] == 2
    assert records[-1]["dropped_sample_count"] == 1
    assert records[-1]["complete_sample_count"] == 1


def test_measure_exception_runs_post_probe_drops_remaining_side_session_and_continues(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_configured_spec(
        tmp_path,
        monkeypatch,
        lambda document: document["windows"][0].update(sample_count=2),
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    probes = []
    events = []

    def probe(argv, timeout_s):
        probes.append(len(probes))
        events.append("probe")
        return 1, "", ""

    measure_calls = []

    def measure_point(*args, **kwargs):
        measure_calls.append(args)
        events.append("measure")
        if len(measure_calls) == 1:
            raise RuntimeError("fixture measurement failure")
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
    assert events[:4] == ["probe", "measure", "probe", "probe"]
    assert probes == list(range(9))
    assert len(measure_calls) == 5
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    sessions = records[1:-1]
    first_sample = sessions[:2]
    assert [record["status"] for record in first_sample] == [
        "measure_failed",
        "not_run_sample_dropped",
    ]
    assert [record["error"] for record in first_sample[1:]] == ["sample_dropped"]
    assert [record["dropped_by_session_id"] for record in first_sample] == [
        None,
        first_sample[0]["session_id"],
    ]
    assert [record["status"] for record in sessions[2:]] == ["complete"] * 2
    assert records[-1]["planned_sample_count"] == 2
    assert records[-1]["dropped_sample_count"] == 1
    assert records[-1]["complete_sample_count"] == 1


@pytest.mark.parametrize(
    ("phase", "probe_status", "expected_status"),
    [
        ("pre", "competing", "pre_probe_competing"),
        ("pre", "indeterminate", "pre_probe_indeterminate"),
        ("mid", "competing", "mid_probe_competing"),
        ("mid", "indeterminate", "mid_probe_indeterminate"),
        ("post", "competing", "post_probe_competing"),
        ("post", "indeterminate", "post_probe_indeterminate"),
    ],
)
def test_droppable_probe_statuses_run_and_finalize(
    tmp_path, monkeypatch, phase, probe_status, expected_status
):
    spec, _document, _raw = _prepare_configured_spec(
        tmp_path,
        monkeypatch,
        lambda document: document["windows"][0].update(sample_count=21),
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    _install_complete_measurement(monkeypatch)
    probe_calls = []
    special_index = {"pre": 0, "mid": 1, "post": 2}[phase]

    def probe(argv, timeout_s):
        index = len(probe_calls)
        probe_calls.append(index)
        if index != special_index:
            return 1, "", ""
        if probe_status == "competing":
            return 0, "999999 ycsb_fixture.exe\n", ""
        raise RuntimeError("fixture probe failure")

    run_result = F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=probe,
        now_fn=lambda: NOW,
    )
    assert run_result.status == "complete"
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    sessions = records[1:-1]
    assert [record["status"] for record in sessions] == [
        expected_status,
        "not_run_sample_dropped",
        *(["complete"] * 40),
    ]
    assert records[-1]["dropped_sample_count"] == 1
    assert records[-1]["complete_sample_count"] == 20
    if phase == "mid":
        assert sessions[0]["pre_probe"]["status"] == "clear"
        assert sessions[0]["post_probe"]["status"] == "clear"
        assert sessions[0]["mid_probe"]["status"] == probe_status
        assert len(sessions[0]["measurements"][0]["throughputs"]) == 2
        assert sessions[0]["measurements"][1]["throughputs"] == []
        assert sessions[0]["measurements"][1]["error"] == "not_run_mid_probe"
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "generated"
    assert result.upper == 0.0
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    assert summary["dropped_sample_count"] == 1


@pytest.mark.parametrize("trace_artifact_id", ("candidate-a", "reference-a"))
def test_mutation_05_real_trace_inspection_call_rejects_each_binary_before_measure(
    tmp_path, monkeypatch, trace_artifact_id
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
            artifact = next(
                item
                for item in spec.artifacts
                if str(tmp_path / item.binary_relpath) == cmd[2]
            )
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "0000 T izanagi_trace_fixture\n"
                    if artifact.artifact_id == trace_artifact_id
                    else "0000 T ordinary_symbol\n"
                ),
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
    artifact_by_id = {artifact.artifact_id: artifact for artifact in spec.artifacts}
    target_index = next(
        index
        for index, measurement in enumerate(first_session.measurements)
        if measurement.artifact_id == trace_artifact_id
    )
    assert inspected == [
        [
            "nm",
            "-C",
            str(tmp_path / artifact_by_id[measurement.artifact_id].binary_relpath),
        ]
        for measurement in first_session.measurements[:target_index + 1]
    ]
    assert sessions[0]["status"] == "binary_binding_failed"
    assert [record["status"] for record in sessions[1:]] == [
        "not_run_after_fail_closed"
    ]
    terminal = _load_jsonl(tmp_path / "out/window-a.jsonl")[-1]
    assert terminal["status"] == "incomplete"
    assert terminal["dropped_sample_count"] == 0
    assert terminal["complete_sample_count"] == 0
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


def test_runtime_head_must_equal_loaded_head(tmp_path, monkeypatch):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    monkeypatch.setattr(F, "_git_head", lambda root: "a" * 40)
    with pytest.raises(F.FloorPairRunError, match="runtime HEAD") as excinfo:
        F.run_window(
            spec, plan, "window-a", probe_fn=_clear_probe, now_fn=lambda: NOW
        )
    assert excinfo.value.status == "loaded_head_mismatch"
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


def _pair_measurement_values(
    *,
    candidate_1: tuple[float, float],
    reference_1: tuple[float, float],
    candidate_2: tuple[float, float],
    reference_2: tuple[float, float],
) -> dict[tuple[str, str], tuple[float, float]]:
    return {
        ("candidate_1", "candidate"): candidate_1,
        ("candidate_1", "reference"): reference_1,
        ("candidate_2", "candidate"): candidate_2,
        ("candidate_2", "reference"): reference_2,
    }


def _run_production(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    values_by_measurement: dict[tuple[str, str], tuple[float, float]],
) -> tuple[F.FloorPairSpec, F.MeasurementPlan]:
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    planned = [
        (session, measurement)
        for session in plan.sessions
        for measurement in session.measurements
    ]
    artifacts = {artifact.artifact_id: artifact for artifact in spec.artifacts}
    calls = []

    def fake_measure_point(*args, **kwargs):
        session, measurement = planned[len(calls)]
        artifact = artifacts[measurement.artifact_id]
        assert args[0] == str(tmp_path / artifact.binary_relpath)
        calls.append(measurement.measurement_id)
        values = values_by_measurement[(session.side_id, measurement.role)]
        kwargs["rep_returncodes"].extend([0, 0])
        kwargs["rep_observations"].extend(
            [
                _complete_rep_observation(0, values[0]),
                _complete_rep_observation(1, values[1]),
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
    assert calls == [measurement.measurement_id for _session, measurement in planned]
    return spec, plan


def test_window_record_persists_exact_runner_observation_schema(
    tmp_path, monkeypatch
):
    _spec, _plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    assert records[0]["schema"] == "floor-pair-window/v3"
    observations = [
        observation
        for session in records[1:-1]
        for measurement in session["measurements"]
        for observation in measurement["rep_observations"]
    ]
    assert observations
    expected_keys = {
        "rep_index",
        "returncode",
        "counter_status",
        "missing_perf_events",
        "perf_raw",
        "throughput",
        "execution_failure",
    }
    for observation in observations:
        assert set(observation) == expected_keys
        assert type(observation["rep_index"]) is int
        assert type(observation["returncode"]) is int
        assert type(observation["counter_status"]) is str
        assert type(observation["missing_perf_events"]) is list
        assert type(observation["perf_raw"]) is dict
        assert type(observation["throughput"]) is float
        assert type(observation["execution_failure"]) is bool
        assert observation["returncode"] == 0
        assert observation["counter_status"] == "not_required"
        assert observation["missing_perf_events"] == []
        assert observation["perf_raw"] == {
            event: None for event in F.runner.PERF_EVENTS
        }
        assert observation["execution_failure"] is False


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
    assert len(calls) == 16
    return spec, plan


def test_production_adapter_artifact_finalizes_from_raw_medians(tmp_path, monkeypatch):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(110.0, 110.0),
        ),
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "generated"
    assert result.upper == pytest.approx(0.2)
    assert result.candidate_floor == pytest.approx(0.2)
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    assert summary["schema"] == "floor-pair-summary/v3"
    assert summary["statistics"] == {
        "reference_measurements_per_pair_sample": 2,
        "difference_formula": F.DIFFERENCE_FORMULA,
    }
    assert summary["dropped_sample_count"] == 0
    assert summary["dropped_record_count"] == 0
    assert summary["dropped"] == []
    assert summary["campaigns"] == [
        {
            "window_id": "window-a",
            "campaign_id": "campaign-a",
            "planned_sample_count": 1,
            "dropped_sample_count": 0,
            "dropped_fraction": {"numerator": 0, "denominator": 1},
            "threshold": "1/20",
            "admissible": True,
            "strata": [
                {
                    "window_id": "window-a",
                    "pair_id": "pair-a",
                    "planned_sample_count": 1,
                    "dropped_sample_count": 0,
                    "retained_sample_count": 1,
                }
            ],
        }
    ]
    assert summary["proof_limitations"] == {
        "section": "証明していないこと",
        "items": list(F.NOT_PROVEN),
    }
    sample = summary["derivation"][0]["samples"][0]
    assert sample["session_medians"] == {
        "candidate_1": {"candidate": 120.0, "reference": 100.0},
        "candidate_2": {"candidate": 110.0, "reference": 110.0},
    }


def test_mutation_21_max_finite_even_medians_generate_zero_upper(
    tmp_path, monkeypatch
):
    maximum = sys.float_info.max
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(maximum, maximum),
            reference_1=(maximum, maximum),
            candidate_2=(maximum, maximum),
            reference_2=(maximum, maximum),
        ),
    )
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    assert [record["status"] for record in records[1:-1]] == ["complete"] * 2
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "generated"
    assert result.upper == 0.0
    assert result.candidate_floor == 0.0


@pytest.mark.parametrize(
    ("value", "expected_status", "remaining_status", "terminal_status", "final_status"),
    [
        (
            10**400,
            "measure_incomplete",
            "not_run_sample_dropped",
            "complete",
            "not_generated_dropped_fraction_exceeded",
        ),
        (
            -(10**400),
            "protocol_violation",
            "not_run_after_fail_closed",
            "incomplete",
            "not_generated_missing_samples",
        ),
    ],
    ids=("positive-overflow", "negative-overflow"),
)
def test_mutation_22_large_exact_int_is_total_in_run_and_artifact_rederivation(
    tmp_path,
    monkeypatch,
    value,
    expected_status,
    remaining_status,
    terminal_status,
    final_status,
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)

    def measure_point(*args, **kwargs):
        return _complete_scale_point(args, kwargs, throughputs=(value, value))

    monkeypatch.setattr(F.runner, "measure_point", measure_point)
    run_result = F.run_window(
        spec, plan, "window-a", probe_fn=_clear_probe, now_fn=lambda: NOW
    )
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    assert [record["status"] for record in records[1:-1]] == [
        expected_status,
        remaining_status,
    ]
    assert run_result.status == terminal_status
    assert records[-1]["dropped_sample_count"] == (
        1 if expected_status == "measure_incomplete" else 0
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == final_status


@pytest.mark.parametrize(
    ("target", "field", "value"),
    [
        ("header", "format", "forged-format/v1"),
        ("header", "loaded_head", "a" * 40),
        ("header", "runtime_head", "a" * 40),
        ("header", "randomization_algorithm", "fixed-order/v1"),
        ("header", "seed_hex", "02" * 32),
        ("header", "planned_measurement_count", 3),
        ("header", "measurements_per_session", 1),
        ("header", "reference_measurements_per_pair_sample", 1),
        ("header", "difference_formula", "D=forged"),
        ("header", "reps_per_measurement", {"cell-a": 3}),
        ("terminal", "status", "incomplete"),
        ("terminal", "planned_measurement_count", 3),
        ("terminal", "recorded_measurement_count", 3),
        ("terminal", "planned_sample_count", 2),
        ("terminal", "dropped_sample_count", 1),
        ("terminal", "complete_sample_count", 0),
    ],
)
def test_finalizer_revalidates_complete_header_and_terminal_contract(
    tmp_path, monkeypatch, target, field, value
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    record = records[0] if target == "header" else records[-1]
    record[field] = value
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match=target):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


def test_finalizer_rejects_v2_schema_on_v3_shaped_window(tmp_path, monkeypatch):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    records[0]["schema"] = "floor-pair-window/v2"
    _rewrite_jsonl(artifact, records)

    with pytest.raises(F.FloorPairBindingError, match="header"):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


@pytest.mark.parametrize("mutation", ("session-order", "measurement-order"))
def test_mutation_18_recorded_multiple_pair_sample_order_must_match_plan(
    tmp_path, monkeypatch, mutation
):
    spec, plan = _run_multi_pair_sample_production(tmp_path, monkeypatch)
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    assert [record["session_id"] for record in records[1:-1]] == [
        session.session_id for session in plan.sessions
    ]
    if mutation == "session-order":
        records[1], records[2] = records[2], records[1]
        message = "session 順"
    else:
        records[1]["measurements"].reverse()
        message = "metadata"
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match=message):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


def test_mutation_07_status_only_rewrite_is_rejected_by_payload_derivation(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    records[1]["status"] = "measure_incomplete"
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match="再導出"):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


def test_complete_session_requires_exact_two_nested_measurements(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    records[1]["measurements"].pop()
    records[-1]["recorded_measurement_count"] = 3
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match="exact 2"):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)


def test_raw_candidate_reference_exchange_cannot_override_canonical_plan(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    first, second = records[1]["measurements"]
    for field in ("role", "artifact_id", "binary_sha256"):
        first[field], second[field] = second[field], first[field]
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match="metadata.role"):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)


_CAMPAIGN_BOUNDARY_CASES = (
    (59, 1, 2, "generated"),
    (59, 1, 3, "not_generated_dropped_fraction_exceeded"),
    (40, 1, 2, "generated"),
    (59, 3, 8, "generated"),
    (59, 3, 9, "not_generated_dropped_fraction_exceeded"),
)


@pytest.mark.parametrize(
    ("sample_count", "pair_count", "dropped_count", "expected_status"),
    _CAMPAIGN_BOUNDARY_CASES,
)
def test_campaign_drop_fraction_uses_exact_campaign_boundary_and_pair_sum(
    tmp_path,
    monkeypatch,
    sample_count,
    pair_count,
    dropped_count,
    expected_status,
):
    spec, plan = _run_campaign_shape(
        tmp_path,
        monkeypatch,
        sample_count=sample_count,
        pair_count=pair_count,
        dropped_by_window={"window-0": dropped_count},
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == expected_status
    assert (result.upper is not None) is (expected_status == "generated")


@pytest.mark.parametrize(
    ("sample_count", "pair_count", "dropped_count", "expected_status"),
    _CAMPAIGN_BOUNDARY_CASES,
)
def test_campaign_boundary_summary_causality_and_derivation_are_exact(
    tmp_path,
    monkeypatch,
    sample_count,
    pair_count,
    dropped_count,
    expected_status,
):
    spec, plan = _run_campaign_shape(
        tmp_path,
        monkeypatch,
        sample_count=sample_count,
        pair_count=pair_count,
        dropped_by_window={"window-0": dropped_count},
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    planned = sample_count * pair_count
    campaign = summary["campaigns"][0]
    assert campaign["planned_sample_count"] == planned
    assert campaign["dropped_sample_count"] == dropped_count
    fraction = F.Fraction(dropped_count, planned)
    assert campaign["dropped_fraction"] == {
        "numerator": fraction.numerator,
        "denominator": fraction.denominator,
    }
    assert campaign["admissible"] is (
        expected_status != "not_generated_dropped_fraction_exceeded"
    )
    assert summary["dropped_sample_count"] == dropped_count
    assert summary["dropped_record_count"] == dropped_count * 2
    assert len(summary["dropped"]) == dropped_count * 2
    dropped_groups = {}
    for record in summary["dropped"]:
        key = (record["window_id"], record["pair_id"], record["sample_index"])
        dropped_groups.setdefault(key, []).append(record)
    assert len(dropped_groups) == dropped_count
    for records in dropped_groups.values():
        failure = next(record for record in records if record["status"] == "measure_failed")
        cause_session_id = (
            f"{failure['window_id']}.{failure['pair_id']}."
            f"s{failure['sample_index']:06d}.{failure['side_id']}"
        )
        assert sum(record["status"] == "measure_failed" for record in records) == 1
        for record in records:
            if record is failure:
                assert record["dropped_by_session_id"] is None
            else:
                assert record["status"] == "not_run_sample_dropped"
                assert record["error"] == "sample_dropped"
                assert record["dropped_by_session_id"] == cause_session_id
    if expected_status == "generated":
        assert len(summary["derivation"][0]["samples"]) == planned - dropped_count
    else:
        assert result.candidate_floor is None
        assert summary["derivation"] == []


def test_campaign_threshold_is_local_to_each_window_not_global_sum(
    tmp_path, monkeypatch
):
    spec, plan = _run_campaign_shape(
        tmp_path,
        monkeypatch,
        sample_count=20,
        pair_count=1,
        window_count=2,
        dropped_by_window={"window-0": 2, "window-1": 0},
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "not_generated_dropped_fraction_exceeded"
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    assert [campaign["admissible"] for campaign in summary["campaigns"]] == [
        False,
        True,
    ]
    assert sum(campaign["planned_sample_count"] for campaign in summary["campaigns"]) == 40
    assert sum(campaign["dropped_sample_count"] for campaign in summary["campaigns"]) == 2


def test_dropped_summary_includes_complete_side_before_failure(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_configured_spec(
        tmp_path,
        monkeypatch,
        lambda document: document["windows"][0].update(sample_count=40),
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    planned = [
        (session, measurement)
        for session in plan.sessions
        for measurement in session.measurements
    ]
    cursor = 0

    def measure_point(*args, **kwargs):
        nonlocal cursor
        session, measurement = planned[cursor]
        if cursor == 2:
            cursor = 4
            raise RuntimeError("second side failure")
        cursor += 1
        values = _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        )[(session.side_id, measurement.role)]
        return _complete_scale_point(args, kwargs, throughputs=values)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)
    F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=_clear_probe,
        now_fn=lambda: NOW,
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "generated"
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    assert summary["dropped_sample_count"] == 1
    assert summary["dropped_record_count"] == 2
    assert [record["status"] for record in summary["dropped"]] == [
        "complete",
        "measure_failed",
    ]
    assert summary["dropped"][0]["error"] is None
    assert summary["dropped"][0]["dropped_by_session_id"] is None


def test_mutation_11_post_probe_drop_excludes_high_difference_sample(
    tmp_path, monkeypatch
):
    spec, _document, _raw = _prepare_configured_spec(
        tmp_path,
        monkeypatch,
        lambda document: document["windows"][0].update(sample_count=21),
    )
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    sessions = list(plan.sessions)
    planned = [
        (session, measurement)
        for session in sessions
        for measurement in session.measurements
    ]
    first_sample_key = (
        sessions[0].window_id,
        sessions[0].pair_id,
        sessions[0].sample_index,
    )
    cursor = 0

    def measure_point(*args, **kwargs):
        nonlocal cursor
        session, measurement = planned[cursor]
        cursor += 1
        sample_key = (session.window_id, session.pair_id, session.sample_index)
        values = (
            _pair_measurement_values(
                candidate_1=(175.0, 175.0),
                reference_1=(100.0, 100.0),
                candidate_2=(100.0, 100.0),
                reference_2=(100.0, 100.0),
            )
            if sample_key == first_sample_key
            else _pair_measurement_values(
                candidate_1=(125.0, 125.0),
                reference_1=(100.0, 100.0),
                candidate_2=(100.0, 100.0),
                reference_2=(100.0, 100.0),
            )
        )[(session.side_id, measurement.role)]
        return _complete_scale_point(args, kwargs, throughputs=values)

    monkeypatch.setattr(F.runner, "measure_point", measure_point)
    probe_calls = []

    def probe(argv, timeout_s):
        index = len(probe_calls)
        probe_calls.append(index)
        if index == 5:
            return 0, "999999 ycsb_fixture.exe\n", ""
        return 1, "", ""

    F.run_window(
        spec, plan, "window-a", probe_fn=probe, now_fn=lambda: NOW
    )
    artifact_records = _load_jsonl(tmp_path / "out/window-a.jsonl")[1:-1]
    first_sample = artifact_records[:2]
    assert [record["status"] for record in first_sample] == [
        "complete",
        "post_probe_competing",
    ]
    assert all(
        len(measurement["throughputs"]) == 2
        for record in first_sample
        for measurement in record["measurements"]
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    retained = summary["derivation"][0]["samples"]
    dropped_difference = F.compute_gain_difference(
        candidate_1_tps=175.0,
        reference_1_tps=100.0,
        candidate_2_tps=100.0,
        reference_2_tps=100.0,
    ).difference
    assert dropped_difference == 0.75
    assert len(retained) == 20
    assert {sample["difference"] for sample in retained} == {0.25}
    assert result.status == "generated"
    assert result.upper == 0.25
    assert dropped_difference > result.upper


def test_exact_five_percent_with_empty_stratum_is_not_generated(
    tmp_path, monkeypatch
):
    spec, plan = _run_campaign_shape(
        tmp_path,
        monkeypatch,
        sample_count=1,
        pair_count=20,
        dropped_by_window={"window-0": 1},
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "not_generated_empty_stratum"
    summary = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
    campaign = summary["campaigns"][0]
    assert campaign["admissible"] is True
    assert campaign["dropped_fraction"] == {"numerator": 1, "denominator": 20}
    assert sum(stratum["retained_sample_count"] == 0 for stratum in campaign["strata"]) == 1
    assert result.upper is None
    assert result.candidate_floor is None


def test_threshold_status_precedes_empty_stratum_status(tmp_path, monkeypatch):
    spec, plan = _run_campaign_shape(
        tmp_path,
        monkeypatch,
        sample_count=1,
        pair_count=2,
        dropped_by_window={"window-0": 1},
    )
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "not_generated_dropped_fraction_exceeded"
    assert result.upper is None
    assert result.candidate_floor is None


def test_not_run_sample_dropped_without_prior_failure_is_rejected(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    record = records[1]
    record.update(
        {
            "status": "not_run_sample_dropped",
            "measurements": [],
            "pre_probe": None,
            "mid_probe": None,
            "post_probe": None,
            "error": "sample_dropped",
            "dropped_by_session_id": "forged-cause",
        }
    )
    records[-1]["complete_sample_count"] = 0
    _rewrite_jsonl(artifact, records)
    with pytest.raises(
        F.FloorPairBindingError,
        match="先行失敗のない not_run_sample_dropped",
    ):
        F._validate_window_artifact(spec=spec, plan=plan, window=spec.windows[0])


def test_drop_selection_is_invariant_under_complete_throughput_changes(
    tmp_path, monkeypatch
):
    roots = [tmp_path / "first", tmp_path / "second"]
    for root in roots:
        root.mkdir()
    summaries = []
    for root, values in zip(
        roots,
        (
            _pair_measurement_values(
                candidate_1=(120.0, 120.0),
                reference_1=(100.0, 100.0),
                candidate_2=(110.0, 110.0),
                reference_2=(100.0, 100.0),
            ),
            _pair_measurement_values(
                candidate_1=(1.0, 1.0),
                reference_1=(250.0, 250.0),
                candidate_2=(500.0, 500.0),
                reference_2=(125.0, 125.0),
            ),
        ),
        strict=True,
    ):
        spec, plan = _run_campaign_shape(
            root,
            monkeypatch,
            sample_count=59,
            pair_count=1,
            dropped_by_window={"window-0": 2},
            values_by_measurement=values,
        )
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
        summaries.append(
            json.loads((root / "out/summary.json").read_text(encoding="utf-8"))
        )
    assert summaries[0]["dropped_sample_count"] == summaries[1]["dropped_sample_count"] == 2
    assert summaries[0]["dropped"] == summaries[1]["dropped"]


def test_candidate_zero_is_complete_and_contributes_gain_minus_one(
    tmp_path, monkeypatch
):
    spec, plan = _run_campaign_shape(
        tmp_path,
        monkeypatch,
        sample_count=1,
        pair_count=1,
        dropped_by_window={"window-0": 0},
        values_by_measurement=_pair_measurement_values(
            candidate_1=(0.0, 0.0),
            reference_1=(100.0, 100.0),
            candidate_2=(100.0, 100.0),
            reference_2=(100.0, 100.0),
        ),
    )
    sessions = _load_jsonl(tmp_path / "out/window-0.jsonl")[1:-1]
    assert [record["status"] for record in sessions] == ["complete"] * 2
    result = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert result.status == "not_generated_upper_out_of_domain"
    sample = json.loads(
        (tmp_path / "out/summary.json").read_text(encoding="utf-8")
    )["derivation"][0]["samples"][0]
    assert sample["session_medians"]["candidate_1"]["candidate"] == 0.0
    assert sample["gain_1"] == -1.0
    assert sample["difference"] == 1.0


@pytest.mark.parametrize(
    ("target", "invalid_values"),
    [
        (("candidate_1", "reference"), (0.0, 0.0)),
        (("candidate_1", "candidate"), (-1.0, -1.0)),
    ],
)
def test_reference_zero_and_negative_values_are_fatal_protocol_violations(
    tmp_path, monkeypatch, target, invalid_values
):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    planned = [
        (session, measurement)
        for session in plan.sessions
        for measurement in session.measurements
    ]
    values_by_measurement = _pair_measurement_values(
        candidate_1=(120.0, 120.0),
        reference_1=(100.0, 100.0),
        candidate_2=(110.0, 110.0),
        reference_2=(100.0, 100.0),
    )
    values_by_measurement[target] = invalid_values
    cursor = 0

    def measure_point(*args, **kwargs):
        nonlocal cursor
        session, measurement = planned[cursor]
        cursor += 1
        return _complete_scale_point(
            args,
            kwargs,
            throughputs=values_by_measurement[(session.side_id, measurement.role)],
        )

    monkeypatch.setattr(F.runner, "measure_point", measure_point)
    result = F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=_clear_probe,
        now_fn=lambda: NOW,
    )
    assert result.status == "incomplete"
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    statuses = [record["status"] for record in records[1:-1]]
    fatal_index = statuses.index("protocol_violation")
    assert statuses[fatal_index + 1:] == ["not_run_after_fail_closed"] * (
        len(statuses) - fatal_index - 1
    )
    assert records[-1]["dropped_sample_count"] == 0
    final = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert final.status == "not_generated_missing_samples"
    assert final.upper is None
    assert final.candidate_floor is None


def test_outside_window_is_fatal_and_not_counted_as_dropped(tmp_path, monkeypatch):
    spec, _document, _raw = _prepare_spec(tmp_path, monkeypatch)
    plan = F.make_measurement_plan(spec)
    _install_live_and_trace(monkeypatch)
    result = F.run_window(
        spec,
        plan,
        "window-a",
        probe_fn=_clear_probe,
        now_fn=lambda: datetime(2029, 12, 31, 23, 59, tzinfo=timezone.utc),
    )
    assert result.status == "incomplete"
    records = _load_jsonl(tmp_path / "out/window-a.jsonl")
    assert [record["status"] for record in records[1:-1]] == [
        "outside_window",
        "not_run_after_fail_closed",
    ]
    assert records[-1]["dropped_sample_count"] == 0
    final = F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert final.status == "not_generated_missing_samples"


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
    assert sessions[0]["measurements"][0]["throughputs"] == [100.0, None]
    assert sessions[0]["measurements"][1]["throughputs"] == []
    assert [record["status"] for record in sessions[1:]] == [
        "not_run_sample_dropped",
    ]


def test_mutation_08_upper_at_or_above_one_is_preserved_and_not_clamped(
    tmp_path, monkeypatch
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(300.0, 300.0),
            reference_1=(100.0, 100.0),
            candidate_2=(100.0, 100.0),
            reference_2=(100.0, 100.0),
        ),
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


@pytest.mark.parametrize("level", ("session", "measurement"))
def test_finalizer_rejects_duplicate_session_or_measurement_id(
    tmp_path, monkeypatch, level
):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
    )
    artifact = tmp_path / "out/window-a.jsonl"
    records = _load_jsonl(artifact)
    if level == "session":
        records.insert(2, copy.deepcopy(records[1]))
        records[-1]["recorded_session_count"] = 3
        records[-1]["recorded_measurement_count"] = 6
        message = "session ID/count"
    else:
        records[1]["measurements"].append(
            copy.deepcopy(records[1]["measurements"][0])
        )
        records[-1]["recorded_measurement_count"] = 5
        message = "exact 2"
    _rewrite_jsonl(artifact, records)
    with pytest.raises(F.FloorPairBindingError, match=message):
        F.finalize_floor(spec, plan, now_fn=lambda: NOW)
    assert not (tmp_path / "out/summary.json").exists()


def test_summary_is_exclusive_create(tmp_path, monkeypatch):
    spec, plan = _run_production(
        tmp_path,
        monkeypatch,
        _pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(100.0, 100.0),
        ),
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
            session_count=2,
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
