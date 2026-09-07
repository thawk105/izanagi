from __future__ import annotations

import inspect
import os
import sys
from contextlib import nullcontext

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import backoff_extended_sweep as S
from orchestrator.campaign import backoff_extended_sweep_report as R
from orchestrator.campaign import backoff_overthrottle as M


def _metrics(**extra):
    return {
        "throughput[tps]": "1000",
        "abort_rate": "0.2",
        "latency[ns]": "500",
        **extra,
    }


def test_mu5_run_once_is_spied_as_strict_and_perf_disabled(monkeypatch):
    observed = {}

    def run_once(binary, flags, **kwargs):
        observed.update({"binary": binary, "flags": flags, **kwargs})
        return _metrics(backoff_latency_rate="0.1"), {}, 3.0

    monkeypatch.setattr(M, "run_once", run_once)
    monkeypatch.setattr(M, "bench_lock", nullcontext)
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    M._run_rep("binary", ["-extime=3"], [])
    assert observed["use_perf"] is False
    assert observed["strict_returncode"] is True


def test_mu6_aa_binding_is_fail_closed_before_measurement():
    expected = S.genomes("balanced")
    bindings = {genome.canonical(): f"v{index}" for index, genome in enumerate(expected)}
    M.require_complete_bindings(expected, bindings)
    bindings.pop(expected[-1].canonical())
    with pytest.raises(RuntimeError, match="certified AA reference set mismatch"):
        M.require_complete_bindings(expected, bindings)
    source = inspect.getsource(M.measure)
    assert source.index("require_complete_bindings") < source.index("buildcache.build_v2")


def test_condition_gate_uses_backoff_flags_from_imported_genomes(monkeypatch):
    captured = {}

    def require(*_args, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(M, "_require_backoff_condition_gate", require)
    references = S.genomes("balanced")
    M._require_condition_gate_before_measurement(
        "/patched", stock_root="/stock", references=references, cxx="c++",
    )

    assert captured["driver_id"] == "orchestrator/campaign/backoff_overthrottle.py"
    assert captured["macro_values"] == {
        "BACKOFF_FIXED": tuple(
            M._aa_genome(reference).flags["BACKOFF_FIXED"]
            for reference in references
        ),
    }


def test_static_1000_generator_to_diagnostic_report_uses_physical_label():
    reference = next(
        genome for genome in S.genomes("balanced")
        if genome.flags["BACKOFF_FIXED"] == 3000
    )
    assert M.JSONL_SCHEMA == "b10-backoff-overthrottle-rep/v2"
    assert M.MANIFEST_SCHEMA == "b10-backoff-overthrottle-manifest/v2"
    assert M._point_label(reference) == "fixed-1000us"
    assert M._point_backoff_us(reference) == 1000

    rows = []
    for rep in range(M.REPS):
        rows.append({
            "workload": "balanced",
            "workload_coordinates": dict(S.WORKLOAD_BY_TAG["balanced"]),
            "campaign_id": "campaign",
            "reference_variant_id": "static-1000",
            "reference_genome": reference.canonical(),
            "aa_genome": M._aa_genome(reference).canonical(),
            "label": M._point_label(reference),
            "point_index": 30,
            "rep": rep,
            "back_off": 1,
            "backoff_us": M._point_backoff_us(reference),
            "values": {
                field: M._value(float(rep + 1))
                for field in (
                    "backoff_latency_rate", "abort_rate", "latency_ns",
                    "tps_aa", "eff_tps",
                )
            },
        })
    summary = M._summaries(rows)[0]
    assert (summary["label"], summary["backoff_us"]) == ("fixed-1000us", 1000)

    normal_point = {
        "workload": "balanced",
        "workload_coordinates": dict(S.WORKLOAD_BY_TAG["balanced"]),
        "campaign_id": "campaign",
        "variant_id": "static-1000",
        "reference_genome": reference.canonical(),
        "kind": "static",
        "backoff_us": 1000,
        "point_index": 30,
    }
    expected = R._expected_aa_binding(normal_point)
    assert expected["reference_genome"] == reference.canonical()
    assert (expected["label"], expected["backoff_us"]) == ("fixed-1000us", 1000)


def test_mu9_only_back_off_zero_accepts_structural_missing_spin():
    none = next(genome for genome in S.genomes("balanced") if genome.flags["BACK_OFF"] == 0)
    adaptive = next(
        genome for genome in S.genomes("balanced")
        if genome.flags["BACK_OFF"] == 1 and genome.flags["BACKOFF_FIXED"] == -1
    )
    assert M.extract_rep_values(_metrics(), none)["backoff_latency_rate"] == 0.0
    with pytest.raises(RuntimeError, match="BACK_OFF=1 is missing"):
        M.extract_rep_values(_metrics(), adaptive)


def test_mu12_rep_records_survive_before_terminal_manifest(tmp_path):
    path = tmp_path / "aa.jsonl"

    def row(rep):
        return {
            "schema_version": M.JSONL_SCHEMA,
            "workload": "balanced",
            "campaign_id": "campaign",
            "reference_variant_id": "variant",
            "rep": rep,
            "certified": False,
            "diagnostic_only": True,
        }

    M._append_jsonl(path, row(0))
    assert [item["rep"] for item in M._load_existing(
        path, workload="balanced", campaign_id="campaign",
    )] == [0]
    M._append_jsonl(path, row(1))
    assert [item["rep"] for item in M._load_existing(
        path, workload="balanced", campaign_id="campaign",
    )] == [0, 1]
    source = inspect.getsource(M.measure)
    assert "_append_jsonl(jsonl_path, row)" in source
    assert source.index("_append_jsonl(jsonl_path, row)") < source.index("_write_create_only")


def test_aa_build_uses_the_job_supplied_cache_root():
    source = inspect.getsource(M.measure)
    assert "cache_root=cache_root" in source
    assert 'os.path.join(buildcache._ccbench_dir(), "build-variants")' not in source


def test_aa_applies_patch_and_checks_all_binary_hashes_before_first_rep():
    source = inspect.getsource(M.measure)
    checkout = source.index("with patchharness.checkout")
    patch = source.index("with patchharness.applied")
    condition_gate = source.index("_require_condition_gate_before_measurement")
    build = source.index("buildcache.build_v2")
    identity = source.index("_require_distinct_static_binary_hashes")
    measure = source.index("_run_rep")
    assert checkout < patch < condition_gate < build < identity < measure


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
