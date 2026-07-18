# -*- coding: utf-8 -*-
"""calibration/v2 と W0 leaf dataclass の production validation 負例。"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR))

from calibrator import schema_v2 as sv2  # noqa: E402
from calibrator.model import (CalibrationResult, NoiseFloor, PerfCounters,  # noqa: E402
                              SaturationResult, ScalePoint)
from calibrator.report import result_to_dict  # noqa: E402
from campaign.campaign_claim import ClaimError, ClaimRecord  # noqa: E402
from campaign.durable_root import DurableRootError, DurableRootPolicy  # noqa: E402
from campaign.reservation import ReservationBinding, ReservationError  # noqa: E402


def _point() -> ScalePoint:
    return ScalePoint(
        records=1000, threads=2,
        counters=PerfCounters(llc_load_misses=20, llc_loads=100),
        throughputs=[100.0, 101.0, 99.0], walltime_s=1.5,
    )


def _valid_document() -> dict:
    """v1 field は hand-made dict でなく production result_to_dict から作る。"""
    result = CalibrationResult(
        env_tag="test-env", threads=2, clocks_per_us=1800,
        saturation=SaturationResult(
            records=1000, saturated=True, threshold=0.01, miss_rate_at=0.2,
            series=[{"records": 1000.0, "miss_rate": 0.2, "maxrss_kb": 2048.0}],
        ),
        noise_floor=NoiseFloor(
            throughputs=[100.0, 101.0, 99.0], mean=100.0, median=100.0,
            stdev=1.0, cv=0.01,
        ),
        sweep=[_point()], workload={"ycsb_zipf_skew": "0.9"},
        host={"node": "provenance-only"},
    )
    doc = result_to_dict(result)
    doc["schema_version"] = sv2.SCHEMA_VERSION
    doc["noise_floor"]["kind"] = "within-run"
    doc["scale_sensitivity"] = "not-measured"
    doc["attestation_profile"] = {
        "cpu": {
            "vendor": "GenuineIntel", "family": 6, "model": 143,
            "model_name_raw": "Intel(R) Test CPU",
            "model_name_normalized": "Intel Test CPU",
        },
        "cores": {
            "physical": 2, "logical": 2, "smt_active": False,
            "affinity_visible": 2,
        },
        "cache_topology": [
            {"level": 1, "type": "Data", "bytes": 32768, "line": 64,
             "shared_cpus": [0]},
            {"level": 1, "type": "Data", "bytes": 32768, "line": 64,
             "shared_cpus": [1]},
        ],
        "numa": [{"node_id": 0, "cpulist": [0, 1]}],
        "tsc": {
            "raw_samples_mhz": [1800.0, 1800.1, 1799.9, 1800.0, 1800.0],
            "median_mhz": 1800.0, "clocks_per_us_int": 1800,
            "source": "clock_gettime-monotonic-raw/rdtsc",
        },
        "effective_clock": {
            "samples_mhz": [2400.0, 2410.0, 2390.0],
            "method": "sysfs-sampling", "governor": "performance",
            "tolerance_pct": 5.0,
        },
        "visibility": {
            "hidepid": "0", "pid_ns_shared_with_host": True,
            "pid_ns_method": "proc2-kthreadd",
        },
    }
    doc["acquisition_receipt"] = {
        "qsub": {
            "request_id": "123.server", "submit_epoch": 1784332800,
            "queue": "batch", "project": "project", "nodes": 1,
            "elapstim_req_s": 600,
        },
        "allocation": {
            "pbs_jobid": "123.server", "assigned_host_qstat": "node-a",
            "hostname_observed": "node-a", "cpuset_size": 2, "ht_off": True,
        },
        "toolchain": {
            "module_list": ["gcc/13"], "compiler_path": "/opt/compiler/bin/g++",
            "compiler_version": "g++ 13.2", "cmake_version": "cmake 3.28",
        },
        "ccbench": {
            "head_sha": "a" * 40, "pinned_clean": True,
            "build_argv": ["cmake", "--build", "build"],
            "binary_sha256": "b" * 64,
        },
        "job_script_sha256": "c" * 64,
        "walltime": {
            "formula": "points*reps+reserve", "required_s": 600, "reserve_s": 60,
        },
        "known_values_check": {
            "expected_cpu_model": "Intel Test CPU", "expected_cores": 2,
            "source": "pegasus-runbook §1", "passed": True,
        },
    }
    doc["quality"] = {"status": "accepted", "reasons": []}
    return doc


def _validated_document_for_mutation() -> dict:
    """production writer 由来の原形が valid であることを確認して返す。"""
    doc = _valid_document()
    sv2.validate_calibration_v2(doc)
    return doc


def _set_path(doc: dict, path: str, value) -> None:
    parts = path.split(".")
    target = doc
    for part in parts[:-1]:
        target = target[int(part)] if part.isdigit() else target[part]
    last = parts[-1]
    if last.isdigit():
        target[int(last)] = value
    else:
        target[last] = value


def test_validate_calibration_v2_positive_and_frozen_dataclasses():
    validated = sv2.validate_calibration_v2(_valid_document())
    assert validated.schema_version == "calibration/v2"
    assert validated.attestation_profile.cpu.vendor == "GenuineIntel"
    assert validated.acquisition_receipt.allocation.hostname_observed == "node-a"
    assert validated.quality == sv2.QualityVerdict(status="accepted", reasons=[])
    with pytest.raises(dataclasses.FrozenInstanceError):
        validated.clocks_per_us = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        validated.attestation_profile.cpu.vendor = "x"  # type: ignore[misc]


@pytest.mark.parametrize("field,bad", [
    ("schema_version", "calibration/v1"), ("env_tag", True),
    ("threads", 2.0), ("clocks_per_us", True), ("sweep", {}),
    ("workload", []), ("host", {"node": 1}), ("notes", "none"),
])
def test_v2_rejects_top_level_type_or_value(field, bad):
    doc = _valid_document()
    doc[field] = bad
    with pytest.raises(sv2.CalibrationSchemaError):
        sv2.validate_calibration_v2(doc)


def test_v2_rejects_missing_and_unknown_top_level_fields():
    missing = _valid_document()
    missing.pop("quality")
    with pytest.raises(sv2.CalibrationSchemaError, match="欠落"):
        sv2.validate_calibration_v2(missing)
    unknown = _valid_document()
    unknown["future"] = 1
    with pytest.raises(sv2.CalibrationSchemaError, match="未知"):
        sv2.validate_calibration_v2(unknown)


@pytest.mark.parametrize("path,bad", [
    ("attestation_profile.cpu.vendor", 1),
    ("attestation_profile.cpu.family", True),
    ("attestation_profile.cpu.model", -1),
    ("attestation_profile.cpu.model_name_raw", ""),
    ("attestation_profile.cpu.model_name_normalized", "Intel  Test"),
    ("attestation_profile.cores.physical", 0),
    ("attestation_profile.cores.logical", "2"),
    ("attestation_profile.cores.smt_active", 0),
    ("attestation_profile.cores.affinity_visible", 3),
    ("attestation_profile.cache_topology.0.level", 0),
    ("attestation_profile.cache_topology.0.type", None),
    ("attestation_profile.cache_topology.0.bytes", 0),
    ("attestation_profile.cache_topology.0.line", 0),
    ("attestation_profile.cache_topology.0.shared_cpus", [1, 0]),
    ("attestation_profile.numa.0.node_id", -1),
    ("attestation_profile.numa.0.cpulist", [1, 0]),
    ("attestation_profile.tsc.raw_samples_mhz", [1800.0]),
    ("attestation_profile.tsc.median_mhz", 1700.0),
    ("attestation_profile.tsc.clocks_per_us_int", 1799),
    ("attestation_profile.tsc.source", ""),
    ("attestation_profile.effective_clock.samples_mhz", []),
    ("attestation_profile.effective_clock.method", ""),
    ("attestation_profile.effective_clock.governor", None),
    ("attestation_profile.effective_clock.tolerance_pct", 0.0),
    ("attestation_profile.visibility.hidepid", ""),
    ("attestation_profile.visibility.pid_ns_shared_with_host", 1),
    ("attestation_profile.visibility.pid_ns_method", "proc1-readlink"),
])
def test_attestation_profile_rejects_each_bad_field(path, bad):
    doc = _valid_document()
    _set_path(doc, path, bad)
    with pytest.raises(sv2.CalibrationSchemaError):
        sv2.validate_calibration_v2(doc)


def test_attestation_profile_rejects_unknown_missing_and_noncanonical_lists():
    for mutate in ("unknown", "missing"):
        doc = _valid_document()
        cpu = doc["attestation_profile"]["cpu"]
        if mutate == "unknown":
            cpu["stepping"] = 8
        else:
            cpu.pop("model")
        with pytest.raises(sv2.CalibrationSchemaError):
            sv2.validate_calibration_v2(doc)
    doc = _valid_document()
    doc["attestation_profile"]["cache_topology"].reverse()
    with pytest.raises(sv2.CalibrationSchemaError, match="canonical"):
        sv2.validate_calibration_v2(doc)


@pytest.mark.parametrize("path,bad", [
    ("acquisition_receipt.qsub.request_id", ""),
    ("acquisition_receipt.qsub.submit_epoch", 1.0),
    ("acquisition_receipt.qsub.queue", None),
    ("acquisition_receipt.qsub.project", ""),
    ("acquisition_receipt.qsub.nodes", 0),
    ("acquisition_receipt.qsub.elapstim_req_s", True),
    ("acquisition_receipt.allocation.pbs_jobid", "different"),
    ("acquisition_receipt.allocation.assigned_host_qstat", ""),
    ("acquisition_receipt.allocation.hostname_observed", 1),
    ("acquisition_receipt.allocation.cpuset_size", 0),
    ("acquisition_receipt.allocation.ht_off", "true"),
    ("acquisition_receipt.toolchain.module_list", []),
    ("acquisition_receipt.toolchain.compiler_path", ""),
    ("acquisition_receipt.toolchain.compiler_version", None),
    ("acquisition_receipt.toolchain.cmake_version", ""),
    ("acquisition_receipt.ccbench.head_sha", "a" * 39),
    ("acquisition_receipt.ccbench.pinned_clean", 1),
    ("acquisition_receipt.ccbench.build_argv", "cmake"),
    ("acquisition_receipt.ccbench.binary_sha256", "g" * 64),
    ("acquisition_receipt.job_script_sha256", "c" * 63),
    ("acquisition_receipt.walltime.formula", ""),
    ("acquisition_receipt.walltime.required_s", 0),
    ("acquisition_receipt.walltime.reserve_s", 600),
    ("acquisition_receipt.known_values_check.expected_cpu_model", ""),
    ("acquisition_receipt.known_values_check.expected_cores", True),
    ("acquisition_receipt.known_values_check.source", "runbook"),
    ("acquisition_receipt.known_values_check.passed", 1),
])
def test_acquisition_receipt_rejects_each_bad_field(path, bad):
    doc = _valid_document()
    _set_path(doc, path, bad)
    with pytest.raises(sv2.CalibrationSchemaError):
        sv2.validate_calibration_v2(doc)


def test_acquisition_receipt_rejects_unknown_and_missing_nested_fields():
    doc = _valid_document()
    doc["acquisition_receipt"]["qsub"]["unknown"] = 1
    with pytest.raises(sv2.CalibrationSchemaError, match="未知"):
        sv2.validate_calibration_v2(doc)
    doc = _valid_document()
    doc["acquisition_receipt"]["ccbench"].pop("build_argv")
    with pytest.raises(sv2.CalibrationSchemaError, match="欠落"):
        sv2.validate_calibration_v2(doc)


@pytest.mark.parametrize("mutator", [
    lambda d: d["noise_floor"].__setitem__("kind", "between-run"),
    lambda d: d.__setitem__("scale_sensitivity", None),
    lambda d: d["noise_floor"].__setitem__("extra", 1),
    lambda d: d["sweep"][0].pop("notes"),
    lambda d: d["quality"].__setitem__("status", "maybe"),
    lambda d: d["quality"].__setitem__("reasons", [1]),
])
def test_v1_compatible_fields_and_quality_fail_closed(mutator):
    doc = _valid_document()
    mutator(doc)
    with pytest.raises(sv2.CalibrationSchemaError):
        sv2.validate_calibration_v2(doc)


def test_quality_rejected_requires_reason_and_accepted_requires_clean_receipt():
    rejected = _valid_document()
    rejected["quality"] = {"status": "rejected", "reasons": []}
    with pytest.raises(sv2.CalibrationSchemaError):
        sv2.validate_calibration_v2(rejected)
    dirty = _valid_document()
    dirty["acquisition_receipt"]["ccbench"]["pinned_clean"] = False
    with pytest.raises(sv2.CalibrationSchemaError, match="pinned_clean"):
        sv2.validate_calibration_v2(dirty)


def test_accepted_rejects_failed_known_values_check_alone():
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["known_values_check"]["passed"] = False
    with pytest.raises(sv2.CalibrationSchemaError, match="known_values_check.passed"):
        sv2.validate_calibration_v2(doc)


def test_accepted_rejects_ht_enabled_allocation_alone():
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["allocation"]["ht_off"] = False
    with pytest.raises(sv2.CalibrationSchemaError, match="allocation.ht_off"):
        sv2.validate_calibration_v2(doc)


def test_accepted_rejects_missing_saturation_alone():
    doc = _validated_document_for_mutation()
    doc["saturation"] = None
    with pytest.raises(sv2.CalibrationSchemaError, match="saturation が null"):
        sv2.validate_calibration_v2(doc)


def test_accepted_rejects_empty_sweep_alone():
    doc = _validated_document_for_mutation()
    doc["sweep"] = []
    with pytest.raises(sv2.CalibrationSchemaError, match="sweep/noise_floor が空"):
        sv2.validate_calibration_v2(doc)


def test_accepted_rejects_walltime_required_above_qsub_request():
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["qsub"]["elapstim_req_s"] = 599
    with pytest.raises(sv2.CalibrationSchemaError, match="必要 walltime が qsub 要求を超過"):
        sv2.validate_calibration_v2(doc)


@pytest.mark.parametrize("qsub_requested_s", [600, 601], ids=["equal", "contained"])
def test_accepted_allows_walltime_required_within_qsub_request(qsub_requested_s):
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["qsub"]["elapstim_req_s"] = qsub_requested_s
    assert sv2.validate_calibration_v2(doc).quality.status == "accepted"


@pytest.mark.parametrize("qsub_id,pbs_jobid", [
    ("123.server", "0:123.server"),
    ("0:123.server", "123.server"),
])
def test_accepted_normalizes_only_zero_subrequest_prefix(qsub_id, pbs_jobid):
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["qsub"]["request_id"] = qsub_id
    doc["acquisition_receipt"]["allocation"]["pbs_jobid"] = pbs_jobid
    validated = sv2.validate_calibration_v2(doc)
    assert validated.quality.status == "accepted"
    assert validated.acquisition_receipt.qsub.request_id == qsub_id
    assert validated.acquisition_receipt.allocation.pbs_jobid == pbs_jobid


@pytest.mark.parametrize("qsub_id,pbs_jobid", [
    ("123.server", "1:123.server"),
    ("123.server", "124.server"),
])
def test_accepted_rejects_other_prefix_and_raw_id_mismatch(qsub_id, pbs_jobid):
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["qsub"]["request_id"] = qsub_id
    doc["acquisition_receipt"]["allocation"]["pbs_jobid"] = pbs_jobid
    with pytest.raises(sv2.CalibrationSchemaError, match="qsub ID と PBS_JOBID"):
        sv2.validate_calibration_v2(doc)


def test_accepted_rejects_cpuset_affinity_mismatch_alone():
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["allocation"]["cpuset_size"] = 1
    with pytest.raises(sv2.CalibrationSchemaError, match="cpuset_size と affinity_visible"):
        sv2.validate_calibration_v2(doc)


def test_accepted_rejects_expected_physical_cores_mismatch_alone():
    doc = _validated_document_for_mutation()
    doc["acquisition_receipt"]["known_values_check"]["expected_cores"] = 1
    with pytest.raises(sv2.CalibrationSchemaError, match="expected_cores と physical cores"):
        sv2.validate_calibration_v2(doc)


def test_v2_rejects_clocks_per_us_tsc_mismatch_alone():
    doc = _validated_document_for_mutation()
    doc["clocks_per_us"] = 1801
    with pytest.raises(sv2.CalibrationSchemaError, match="clocks_per_us と attestation_profile.tsc"):
        sv2.validate_calibration_v2(doc)


def test_v2_rejects_threads_affinity_mismatch_alone():
    doc = _validated_document_for_mutation()
    doc["threads"] = 1
    with pytest.raises(sv2.CalibrationSchemaError, match="threads と attestation_profile.cores"):
        sv2.validate_calibration_v2(doc)


def test_tsc_rejects_inexact_median_even_when_rounded_clock_matches():
    doc = _validated_document_for_mutation()
    tsc = doc["attestation_profile"]["tsc"]
    tsc["raw_samples_mhz"] = [1799.0, 1799.5, 1800.0, 1800.5, 1801.0]
    tsc["median_mhz"] = 1800.4
    with pytest.raises(sv2.CalibrationSchemaError, match="median と不一致"):
        sv2.validate_calibration_v2(doc)


def test_rejected_quality_preserves_failed_acquisition_values():
    doc = _valid_document()
    doc["quality"] = {"status": "rejected", "reasons": ["allocation mismatch"]}
    doc["saturation"] = None
    doc["sweep"] = []
    doc["noise_floor"]["throughputs"] = []
    doc["acquisition_receipt"]["allocation"]["pbs_jobid"] = "different"
    doc["acquisition_receipt"]["allocation"]["ht_off"] = False
    doc["acquisition_receipt"]["ccbench"]["pinned_clean"] = False
    doc["acquisition_receipt"]["known_values_check"]["passed"] = False
    validated = sv2.validate_calibration_v2(doc)
    assert validated.quality.status == "rejected"


def test_duplicate_key_is_rejected_during_real_json_parse():
    raw = json.dumps(_valid_document(), ensure_ascii=False, separators=(",", ":"))
    duplicate = '{"schema_version":"calibration/v2",' + raw[1:]
    with pytest.raises(sv2.CalibrationSchemaError, match="duplicate key"):
        sv2.validate_calibration_v2(duplicate)  # type: ignore[arg-type]


def test_nested_duplicate_key_is_rejected_during_real_json_parse():
    raw = json.dumps(_valid_document(), ensure_ascii=False, separators=(",", ":"))
    needle = '"cpu":{"vendor":"GenuineIntel",'
    duplicate = raw.replace(
        needle, '"cpu":{"vendor":"GenuineIntel","vendor":"GenuineIntel",', 1,
    )
    with pytest.raises(sv2.CalibrationSchemaError, match="duplicate key"):
        sv2.validate_calibration_v2(duplicate)  # type: ignore[arg-type]


def test_reservation_binding_positive_and_field_negatives():
    valid = dict(
        job_id="123.server", requested_s=600, scheduler_started_epoch=1000.5,
        deadline_epoch=1600.5, host="node-a", boot_id="boot",
        script_sha256="a" * 64, nonce="nonce",
    )
    assert ReservationBinding(**valid).requested_s == 600
    bad_values = {
        "job_id": "", "scheduler_started_epoch": "1000",
        "deadline_epoch": 1601.5, "host": None, "boot_id": "",
        "script_sha256": "A" * 64, "nonce": 0,
    }
    for field, bad in bad_values.items():
        candidate = dict(valid)
        candidate[field] = bad
        with pytest.raises(ReservationError):
            ReservationBinding(**candidate)


def test_reservation_binding_rejects_bool_requested_s_without_deadline_shielding():
    valid = dict(
        job_id="123.server", requested_s=600, scheduler_started_epoch=1000.5,
        deadline_epoch=1600.5, host="node-a", boot_id="boot",
        script_sha256="a" * 64, nonce="nonce",
    )
    assert ReservationBinding(**valid).requested_s == 600
    candidate = dict(valid, requested_s=True, deadline_epoch=1001.5)
    with pytest.raises(ReservationError, match="requested_s は正整数"):
        ReservationBinding(**candidate)


def test_durable_root_policy_positive_and_field_negatives(tmp_path):
    approved = tmp_path / "approved"
    forbidden = tmp_path / "forbidden"
    policy = DurableRootPolicy(approved_roots=(approved,), forbidden_roots=(forbidden,))
    assert policy.approved_roots == (approved,)
    with pytest.raises(DurableRootError):
        DurableRootPolicy(approved_roots=[], forbidden_roots=())  # type: ignore[arg-type]
    with pytest.raises(DurableRootError):
        DurableRootPolicy(approved_roots=(), forbidden_roots=())
    with pytest.raises(DurableRootError):
        DurableRootPolicy(approved_roots=(Path("relative"),), forbidden_roots=())
    with pytest.raises(DurableRootError):
        DurableRootPolicy(approved_roots=(approved, approved), forbidden_roots=())
    with pytest.raises(DurableRootError):
        DurableRootPolicy(approved_roots=(approved,), forbidden_roots=[forbidden])  # type: ignore[arg-type]


def test_claim_record_positive_and_field_negatives():
    valid = dict(
        campaign_identity="campaign", job_id="123.server", host="node-a", boot_id="boot",
        pid=123, proc_starttime=456, created_utc="2026-07-18T00:00:00+00:00",
    )
    assert ClaimRecord(**valid).pid == 123
    bad_values = {
        "campaign_identity": "", "job_id": None, "host": 1, "boot_id": "",
        "pid": True, "proc_starttime": 0, "created_utc": "2026-07-18T00:00:00",
    }
    for field, bad in bad_values.items():
        candidate = dict(valid)
        candidate[field] = bad
        with pytest.raises(ClaimError):
            ClaimRecord(**candidate)


def test_leaf_dataclass_missing_and_unknown_fields_raise_type_error(tmp_path):
    with pytest.raises(TypeError):
        ReservationBinding(job_id="x")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        DurableRootPolicy(approved_roots=(tmp_path,), forbidden_roots=(), extra=1)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        ClaimRecord(campaign_identity="x")  # type: ignore[call-arg]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
