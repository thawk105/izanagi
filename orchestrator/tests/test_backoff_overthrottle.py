from __future__ import annotations

import inspect
from contextlib import nullcontext

import pytest

from orchestrator.campaign import backoff_extended_sweep as S
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
