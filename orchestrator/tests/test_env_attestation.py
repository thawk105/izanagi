# -*- coding: utf-8 -*-
"""Strict env attestation probe, comparator, and calibration admission tests."""
from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
if str(_ORCH) not in sys.path:
    sys.path.insert(0, str(_ORCH))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from calibrator import schema_v2 as sv2  # noqa: E402
from campaign import env_attestation as ea  # noqa: E402
from campaign import env_contract as ec  # noqa: E402
from campaign import execution_guard as eg  # noqa: E402
from test_schema_v2 import _valid_document  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _probe_tree(tmp_path: Path) -> ea.ProbeRoots:
    proc = tmp_path / "proc"
    sys_cpu = tmp_path / "sys/devices/system/cpu"
    sys_node = tmp_path / "sys/devices/system/node"
    proc.mkdir()
    cpuinfo_blocks = []
    for cpu, mhz in ((0, "2390.000"), (1, "2410.000")):
        cpuinfo_blocks.append(
            f"processor : {cpu}\n"
            "vendor_id : GenuineIntel\n"
            "cpu family : 6\n"
            "model : 143\n"
            "model name : Intel(R)  Xeon(TM) Test CPU @ 2.40GHz\n"
            f"cpu MHz : {mhz}\n"
        )
        cpu_root = sys_cpu / f"cpu{cpu}"
        _write(cpu_root / "topology/core_id", f"{cpu}\n")
        _write(cpu_root / "cpufreq/scaling_governor", "performance\n")
        cache = cpu_root / "cache/index0"
        _write(cache / "level", "1\n")
        _write(cache / "type", "Data\n")
        _write(cache / "size", "32K\n")
        _write(cache / "coherency_line_size", "64\n")
        _write(cache / "shared_cpu_list", f"{cpu}\n")
    _write(proc / "cpuinfo", "\n".join(cpuinfo_blocks))
    _write(proc / "mounts", "proc /proc proc rw,nosuid,nodev,noexec 0 0\n")
    _write(proc / "2/comm", "kthreadd\n")
    _write(sys_node / "node0/cpulist", "1,0\n")
    return ea.ProbeRoots(proc=proc, sys_cpu=sys_cpu, sys_node=sys_node)


def _patch_runtime_probe(monkeypatch) -> None:
    monkeypatch.setattr(ea.os, "sched_getaffinity", lambda _pid: {0, 1})
    monkeypatch.setattr(
        ea, "_measure_tsc_profile",
        lambda: sv2.TscProfile(
            raw_samples_mhz=[1800.0, 1800.1, 1799.9, 1800.0, 1800.0],
            median_mhz=1800.0,
            clocks_per_us_int=1800,
            source="clock_gettime-monotonic/rdtscp",
        ),
    )


def test_probe_fixture_tree_returns_frozen_schema_profile(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    _patch_runtime_probe(monkeypatch)
    profile = ea.probe(roots)
    assert isinstance(profile, sv2.ObservedAttestationProfile)
    assert profile.cpu == sv2.CpuProfile(
        vendor="GenuineIntel", family=6, model=143,
        model_name_raw="Intel(R)  Xeon(TM) Test CPU @ 2.40GHz",
        model_name_normalized="Intel Xeon Test CPU",
    )
    assert profile.cores == sv2.CoreProfile(
        physical=2, logical=2, smt_active=False, affinity_visible=2,
    )
    assert [item.shared_cpus for item in profile.cache_topology] == [[0], [1]]
    assert profile.numa == [sv2.NumaNode(node_id=0, cpulist=[0, 1])]
    assert profile.tsc.clocks_per_us_int == 1800
    assert profile.effective_clock.samples_mhz == [2390.0, 2410.0]
    assert profile.effective_clock.governor == "performance"
    assert not hasattr(profile.effective_clock, "tolerance_pct")
    assert profile.visibility == sv2.VisibilityProfile(
        hidepid="0", pid_ns_shared_with_host=True,
        pid_ns_method="proc2-kthreadd",
    )
    assert ea.normalize_observed_profile(ea.observed_profile_to_dict(profile)) == profile


def test_probe_rejects_mixed_governors_across_visible_cpus(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    _patch_runtime_probe(monkeypatch)
    _write(roots.sys_cpu / "cpu1/cpufreq/scaling_governor", "powersave\n")
    with pytest.raises(ea.AttestationError, match="governor"):
        ea.probe(roots)


@pytest.mark.parametrize("failure", [
    "cache-field", "cache-index", "cpuinfo", "hidepid",
])
def test_probe_rejects_partial_or_hidden_observation(tmp_path, monkeypatch, failure):
    roots = _probe_tree(tmp_path)
    _patch_runtime_probe(monkeypatch)
    if failure == "cache-field":
        (roots.sys_cpu / "cpu1/cache/index0/size").unlink()
    elif failure == "cache-index":
        cache = roots.sys_cpu / "cpu0/cache/index1"
        _write(cache / "level", "2\n")
        _write(cache / "type", "Unified\n")
        _write(cache / "size", "1M\n")
        _write(cache / "coherency_line_size", "64\n")
        _write(cache / "shared_cpu_list", "0\n")
    elif failure == "cpuinfo":
        text = (roots.proc / "cpuinfo").read_text(encoding="utf-8")
        (roots.proc / "cpuinfo").write_text(
            text.replace("model name :", "missing name :", 1), encoding="utf-8",
        )
    elif failure == "hidepid":
        (roots.proc / "mounts").write_text(
            "proc /proc proc rw,hidepid=2 0 0\n", encoding="utf-8",
        )
    with pytest.raises(ea.AttestationError):
        ea.probe(roots)


@pytest.mark.parametrize("proc2_state", ["missing", "mismatch"])
def test_probe_records_non_host_pid_namespace_without_probe_error(
        tmp_path, monkeypatch, proc2_state):
    roots = _probe_tree(tmp_path)
    _patch_runtime_probe(monkeypatch)
    proc2_comm = roots.proc / "2/comm"
    if proc2_state == "missing":
        proc2_comm.unlink()
    else:
        proc2_comm.write_text("not-kthreadd\n", encoding="utf-8")
    visibility = ea.probe(roots).visibility
    assert visibility.pid_ns_shared_with_host is False
    assert visibility.pid_ns_method == "proc2-kthreadd"


def test_probe_rejects_unexpected_proc2_comm_oserror(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    _patch_runtime_probe(monkeypatch)
    (roots.proc / "2/comm").unlink()
    (roots.proc / "2/comm").mkdir()
    with pytest.raises(ea.AttestationError, match="/proc/2/comm"):
        ea.probe(roots)


def test_required_tsc_probe_has_no_fallback(monkeypatch):
    monkeypatch.setattr(ea._tsc, "measure_tsc", lambda **_kwargs: None)
    with pytest.raises(ea.AttestationError, match="fallback 禁止"):
        ea._measure_tsc_profile()


def _profile() -> sv2.AttestationProfile:
    document = _valid_document()
    # U-2 の current issuer accepted set は policy 2.0 に縮小した。
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    return sv2.validate_calibration_v2(document).attestation_profile


def _observed(profile: sv2.AttestationProfile) -> sv2.ObservedAttestationProfile:
    raw = ea.profile_to_dict(profile)
    del raw["effective_clock"]["tolerance_pct"]
    return ea.normalize_observed_profile(raw)


def _observed_comparison_fixture(
    profile: sv2.AttestationProfile,
) -> sv2.ObservedAttestationProfile:
    """Build comparator input without applying raw parser invariants."""
    return sv2.ObservedAttestationProfile(
        cpu=profile.cpu,
        cores=profile.cores,
        cache_topology=profile.cache_topology,
        numa=profile.numa,
        tsc=profile.tsc,
        effective_clock=sv2.ObservedEffectiveClockProfile(
            samples_mhz=profile.effective_clock.samples_mhz,
            method=profile.effective_clock.method,
            governor=profile.effective_clock.governor,
        ),
        visibility=profile.visibility,
    )


def _replace_cpu(profile, **values):
    return dataclasses.replace(profile, cpu=dataclasses.replace(profile.cpu, **values))


def _replace_clock(profile, **values):
    return dataclasses.replace(
        profile,
        effective_clock=dataclasses.replace(profile.effective_clock, **values),
    )


@pytest.mark.parametrize("field,mutate", [
    ("cpu.vendor", lambda p: _replace_cpu(p, vendor="OtherVendor")),
    ("cpu.family", lambda p: _replace_cpu(p, family=7)),
    ("cpu.model", lambda p: _replace_cpu(p, model=144)),
    ("cpu.model_name_raw", lambda p: _replace_cpu(p, model_name_raw="Different CPU")),
    ("cpu.model_name_normalized", lambda p: _replace_cpu(p, model_name_normalized="Different CPU")),
    ("cores.physical", lambda p: dataclasses.replace(
        p, cores=sv2.CoreProfile(physical=1, logical=2, smt_active=True, affinity_visible=2),
    )),
    ("cores.logical", lambda p: dataclasses.replace(
        p, cores=sv2.CoreProfile(physical=1, logical=1, smt_active=False, affinity_visible=1),
    )),
    ("cores.smt_active", lambda p: dataclasses.replace(
        p, cores=sv2.CoreProfile(physical=1, logical=2, smt_active=True, affinity_visible=2),
    )),
    ("cores.affinity_visible", lambda p: dataclasses.replace(
        p, cores=dataclasses.replace(p.cores, affinity_visible=1),
    )),
    ("cache_topology", lambda p: dataclasses.replace(
        p, cache_topology=[
            p.cache_topology[0], dataclasses.replace(p.cache_topology[1], bytes=65536),
        ],
    )),
    ("numa", lambda p: dataclasses.replace(
        p, numa=[sv2.NumaNode(node_id=0, cpulist=[0])],
    )),
    ("tsc.clocks_per_us_int", lambda p: dataclasses.replace(
        p, tsc=sv2.TscProfile(
            raw_samples_mhz=[1900.0] * 5, median_mhz=1900.0,
            clocks_per_us_int=1900, source=p.tsc.source,
        ),
    )),
    ("tsc.raw_samples_mhz", lambda p: dataclasses.replace(
        p, tsc=sv2.TscProfile(
            raw_samples_mhz=[1900.0] * 5, median_mhz=1900.0,
            clocks_per_us_int=1900, source=p.tsc.source,
        ),
    )),
    ("tsc.median_mhz", lambda p: dataclasses.replace(
        p, tsc=sv2.TscProfile(
            raw_samples_mhz=[1900.0] * 5, median_mhz=1900.0,
            clocks_per_us_int=1900, source=p.tsc.source,
        ),
    )),
    ("tsc.source", lambda p: dataclasses.replace(
        p, tsc=dataclasses.replace(p.tsc, source="different-source"),
    )),
    ("effective_clock.samples_mhz", lambda p: _replace_clock(
        p, samples_mhz=[3000.0, 3010.0, 2990.0],
    )),
    ("effective_clock.method", lambda p: _replace_clock(p, method="different-method")),
    ("effective_clock.governor", lambda p: _replace_clock(p, governor="powersave")),
    ("visibility.hidepid", lambda p: dataclasses.replace(
        p, visibility=dataclasses.replace(p.visibility, hidepid="2"),
    )),
    ("visibility.pid_ns_shared_with_host", lambda p: dataclasses.replace(
        p, visibility=dataclasses.replace(p.visibility, pid_ns_shared_with_host=False),
    )),
])
def test_compare_profiles_reports_each_field_mismatch(field, mutate):
    expected = _profile()
    comparisons = ea.compare_profiles(
        expected,
        _observed_comparison_fixture(mutate(expected)),
        now_fn=lambda: "now",
    )
    failures = {item["field"] for item in comparisons if item["verdict"] == "fail"}
    assert field in failures


def test_compare_profiles_normalizes_raw_name_and_applies_expected_clock_tolerance():
    expected = _profile()
    observed_raw_name = "Intel Test CPU @ 2.10GHz"
    observed_expected_shape = _replace_cpu(
        expected,
        model_name_raw=observed_raw_name,
        model_name_normalized=ea.normalize_cpu_model_name(observed_raw_name),
    )
    observed_expected_shape = _replace_clock(
        observed_expected_shape, samples_mhz=[2440.0, 2448.0, 2430.0],
    )
    observed = _observed(observed_expected_shape)
    comparisons = ea.compare_profiles(expected, observed, now_fn=lambda: "now")
    by_field = {item["field"]: item["verdict"] for item in comparisons}
    assert by_field["cpu.model_name_raw"] == "pass"
    assert by_field["effective_clock.samples_mhz"] == "pass"

    outlier = _observed(_replace_clock(
        expected, samples_mhz=[2400.0, 2400.0, 3000.0],
    ))
    outlier_comparisons = ea.compare_profiles(expected, outlier, now_fn=lambda: "now")
    assert next(item for item in outlier_comparisons
                if item["field"] == "effective_clock.samples_mhz")["verdict"] == "fail"


def _probe_document(version: str) -> dict:
    profile = copy.deepcopy(_valid_document()["attestation_profile"])
    if version == ea.PEGASUS_PROBE_OUTPUT_V1:
        profile["effective_clock"]["tolerance_pct"] = 100.0
    else:
        del profile["effective_clock"]["tolerance_pct"]
    return {
        "schema_version": version,
        "ok": True,
        "observed_epoch": 1,
        "profile": profile,
    }


@pytest.mark.parametrize("sentinel", [100, 2.0, 99.0])
def test_probe_output_v1_accepts_only_exact_float_sentinel(sentinel):
    document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V1)
    document["profile"]["effective_clock"]["tolerance_pct"] = sentinel
    with pytest.raises(ea.AttestationError, match="sentinel"):
        ea.parse_probe_output(json.dumps(document))


@pytest.mark.parametrize("tolerance", [2.0, 100.0])
def test_probe_output_v2_rejects_tolerance_field(tolerance):
    document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V2)
    document["profile"]["effective_clock"]["tolerance_pct"] = tolerance
    with pytest.raises(ea.AttestationError, match="effective_clock"):
        ea.parse_probe_output(json.dumps(document))


@pytest.mark.parametrize("version", [
    ea.PEGASUS_PROBE_OUTPUT_V1,
    ea.PEGASUS_PROBE_OUTPUT_V2,
])
def test_probe_output_rejects_forged_cpu_name_pair(version):
    document = _probe_document(version)
    document["profile"]["cpu"].update({
        "model_name_raw": "Intel Xeon Platinum 8468H",
        "model_name_normalized": "Intel Xeon Platinum 8468",
    })

    with pytest.raises(ea.AttestationError, match="normalized name"):
        ea.parse_probe_output(json.dumps(document))


@pytest.mark.parametrize("version", [
    ea.PEGASUS_PROBE_OUTPUT_V1,
    ea.PEGASUS_PROBE_OUTPUT_V2,
])
@pytest.mark.parametrize("level", ["top", "profile", "effective_clock"])
def test_probe_output_rejects_duplicate_keys_at_every_raw_level(version, level):
    document = _probe_document(version)
    profile_text = json.dumps(document["profile"], separators=(",", ":"))
    if level == "profile":
        profile_text = profile_text.replace('"cpu":{', '"cpu":{},"cpu":{', 1)
    elif level == "effective_clock":
        profile_text = profile_text.replace(
            '"samples_mhz":[', '"samples_mhz":[1.0],"samples_mhz":[', 1,
        )
    raw = (
        '{"schema_version":' + json.dumps(version)
        + ',"ok":true,"observed_epoch":1,"profile":' + profile_text
        + (',"profile":' + profile_text if level == "top" else "")
        + "}"
    )
    with pytest.raises(ea.AttestationError, match="duplicate key"):
        ea.parse_probe_output(raw)


def test_observed_hash_projection_preserves_source_schema_preimage():
    v1_document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V1)
    v2_document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V2)
    parsed_v1 = ea.parse_probe_output(json.dumps(v1_document))
    parsed_v2 = ea.parse_probe_output(json.dumps(v2_document))

    def digest(profile):
        return hashlib.sha256(json.dumps(
            profile, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")).hexdigest()

    assert ea.observed_profile_sha256(parsed_v1) == digest(v1_document["profile"])
    assert ea.observed_profile_sha256(parsed_v2) == digest(v2_document["profile"])
    assert "tolerance_pct" in ea.observed_profile_projection(parsed_v1)["effective_clock"]
    assert "tolerance_pct" not in ea.observed_profile_projection(parsed_v2)["effective_clock"]


_V1_CORPUS_PAIRS = (
    ("calibration/job-staging/0:867865.nqsv/attestation-static.json", "calibration/job-staging/0:867865.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867866.nqsv/attestation-static.json", "calibration/job-staging/0:867866.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867867.nqsv/attestation-static.json", "calibration/job-staging/0:867867.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867868.nqsv/attestation-static.json", "calibration/job-staging/0:867868.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867869.nqsv/attestation-pre.json", "calibration/job-staging/0:867869.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867869.nqsv/attestation-static.json", "calibration/job-staging/0:867869.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867870.nqsv/attestation-pre.json", "calibration/job-staging/0:867870.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867870.nqsv/attestation-static.json", "calibration/job-staging/0:867870.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867872.nqsv/attestation-pre.json", "calibration/job-staging/0:867872.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867872.nqsv/attestation-static.json", "calibration/job-staging/0:867872.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867874.nqsv/attestation-pre.json", "calibration/job-staging/0:867874.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867874.nqsv/attestation-static.json", "calibration/job-staging/0:867874.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867876.nqsv/attestation-post.json", "calibration/job-staging/0:867876.nqsv/attestation-post.stdout"),
    ("calibration/job-staging/0:867876.nqsv/attestation-pre.json", "calibration/job-staging/0:867876.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867876.nqsv/attestation-static.json", "calibration/job-staging/0:867876.nqsv/attestation-static.stdout"),
    ("smoke/0:867857.nqsv/observation.json", "smoke/0:867857.nqsv/run_probe.stdout"),
    ("smoke/0:867858.nqsv/observation.json", "smoke/0:867858.nqsv/run_probe.stdout"),
    ("smoke/0:867859.nqsv/observation.json", "smoke/0:867859.nqsv/run_probe.stdout"),
    ("smoke/0:867860.nqsv/observation.json", "smoke/0:867860.nqsv/run_probe.stdout"),
    ("smoke/0:867861.nqsv/observation.json", "smoke/0:867861.nqsv/run_probe.stdout"),
    ("smoke/0:867862.nqsv/observation.json", "smoke/0:867862.nqsv/run_probe.stdout"),
    ("silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/attestation-job.json", "silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/attestation-job.stdout"),
)
_V1_CORPUS_DOCS = {
    "calibration/attempts/0_867874.nqsv/calibration.md",
    "calibration/attempts/0_867876.nqsv/calibration.md",
    "silo_ladder_rung1/README.md",
}
_V1_SUCCESS_JSONS = {
    "calibration/job-staging/0:867865.nqsv/attestation-static.json",
    "calibration/job-staging/0:867866.nqsv/attestation-static.json",
    "calibration/job-staging/0:867867.nqsv/attestation-static.json",
    "calibration/job-staging/0:867868.nqsv/attestation-static.json",
    "calibration/job-staging/0:867869.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867869.nqsv/attestation-static.json",
    "calibration/job-staging/0:867870.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867870.nqsv/attestation-static.json",
    "calibration/job-staging/0:867872.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867872.nqsv/attestation-static.json",
    "calibration/job-staging/0:867874.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867874.nqsv/attestation-static.json",
    "calibration/job-staging/0:867876.nqsv/attestation-post.json",
    "calibration/job-staging/0:867876.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867876.nqsv/attestation-static.json",
    "smoke/0:867860.nqsv/observation.json",
    "smoke/0:867861.nqsv/observation.json",
    "smoke/0:867862.nqsv/observation.json",
    ("silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/"
     "attempts/1/attestation-job.json"),
}
_V1_FAILURE_JSONS = {
    "smoke/0:867857.nqsv/observation.json",
    "smoke/0:867858.nqsv/observation.json",
    "smoke/0:867859.nqsv/observation.json",
}


def test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies():
    root = _ORCH.parent / "output/env/pegasus"
    discovered_payloads = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.suffix in {".json", ".stdout"}
        and ea.PEGASUS_PROBE_OUTPUT_V1 in path.read_text(encoding="utf-8")
    }
    golden_payloads = {item for pair in _V1_CORPUS_PAIRS for item in pair}
    discovered_docs = {
        str(path.relative_to(root))
        for path in (
            *root.glob("calibration/attempts/*/calibration.md"),
            root / "silo_ladder_rung1/README.md",
        )
        if path.is_file()
    }
    assert discovered_payloads == golden_payloads
    assert discovered_docs == _V1_CORPUS_DOCS
    assert all((root / path).is_file() for path in _V1_CORPUS_DOCS)
    assert len(golden_payloads | discovered_docs) == 47
    assert _V1_SUCCESS_JSONS.isdisjoint(_V1_FAILURE_JSONS)
    assert _V1_SUCCESS_JSONS | _V1_FAILURE_JSONS == {
        pair[0] for pair in _V1_CORPUS_PAIRS
    }

    registered = json.loads(next(
        (root / "calibration/registered").glob("calibration-*.json")
    ).read_text(encoding="utf-8"))
    expected_clock = {
        "samples_mhz": registered["attestation_profile"]["effective_clock"]["samples_mhz"],
        "tolerance_pct": 2.0,
    }
    observed_success = set()
    observed_failure = set()
    for json_rel, stdout_rel in _V1_CORPUS_PAIRS:
        json_raw = (root / json_rel).read_bytes()
        stdout_raw = (root / stdout_rel).read_bytes()
        assert json.loads(json_raw) == json.loads(stdout_raw)
        parsed = ea.parse_probe_output(json_raw)
        if not parsed.ok:
            observed_failure.add(json_rel)
            continue
        observed_success.add(json_rel)
        assert parsed.profile is not None
        observed_samples = parsed.profile.effective_clock.samples_mhz
        expected_median = statistics.median(expected_clock["samples_mhz"])
        observed_median = statistics.median(observed_samples)
        assert abs(observed_median - expected_median) <= expected_median * 0.02
        assert not eg.effective_clock_comparison_passes(
            expected_clock, {"samples_mhz": observed_samples},
        )
    assert observed_success == _V1_SUCCESS_JSONS
    assert observed_failure == _V1_FAILURE_JSONS


def _required_artifact(tmp_path: Path, doc: dict | None = None, *, raw: bytes | None = None):
    document = copy.deepcopy(doc if doc is not None else _valid_document())
    if doc is None:
        # U-2 の required-loader accepted set は policy 2.0 に縮小した。
        document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    artifact_raw = raw if raw is not None else json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    artifact = tmp_path / "calibration.json"
    artifact.write_bytes(artifact_raw)
    contract = ec.ExecutionEnvironmentContract(
        env_tag=document["env_tag"], clocks_per_us=document["clocks_per_us"],
        numactl=(), attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path="calibration.json", sha256=hashlib.sha256(artifact_raw).hexdigest(),
        ),
    )
    return artifact, contract


def test_load_verified_calibration_accepts_result_to_dict_derived_v2(tmp_path):
    _, contract = _required_artifact(tmp_path)
    verified = ea.load_verified_calibration(contract, tmp_path)
    assert verified.schema_version == sv2.SCHEMA_VERSION
    assert verified.calibration is not None
    assert verified.calibration.env_tag == contract.env_tag
    assert verified.attestation_profile_sha256 == ea.profile_sha256(_profile())


@pytest.mark.parametrize("tolerance", [
    math.nextafter(2.0, math.inf),
    math.nextafter(2.0, -math.inf),
    2.5,
    2.9,
])
def test_loader_rejects_well_formed_nonpolicy_tolerance(tmp_path, tolerance):
    document = _valid_document()
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = tolerance
    _, contract = _required_artifact(tmp_path, document)
    with pytest.raises(ea.AttestationError, match="current policy"):
        ea.load_verified_calibration(contract, tmp_path)


@pytest.mark.parametrize("tolerance", [
    math.nextafter(2.0, math.inf),
    math.nextafter(2.0, -math.inf),
    2.5,
    2.9,
])
def test_issuer_rejects_every_nonpolicy_equality_edge(tolerance):
    expected = dataclasses.replace(
        _profile(),
        effective_clock=dataclasses.replace(
            _profile().effective_clock,
            samples_mhz=[100.0],
            tolerance_pct=tolerance,
        ),
    )
    observed = _observed(dataclasses.replace(
        _profile(),
        effective_clock=dataclasses.replace(
            _profile().effective_clock, samples_mhz=[100.0],
        ),
    ))
    comparisons = ea.compare_profiles(expected, observed, now_fn=lambda: "now")
    clock = next(row for row in comparisons
                 if row["field"] == "effective_clock.samples_mhz")
    assert clock["verdict"] == "fail"


def test_load_verified_calibration_rejects_sha_mismatch(tmp_path):
    _, contract = _required_artifact(tmp_path)
    bad = dataclasses.replace(
        contract,
        calibration_ref=dataclasses.replace(contract.calibration_ref, sha256="0" * 64),
    )
    with pytest.raises(ea.AttestationError, match="sha256 不一致"):
        ea.load_verified_calibration(bad, tmp_path)


def test_load_verified_calibration_hashes_and_parses_one_read(tmp_path, monkeypatch):
    artifact, contract = _required_artifact(tmp_path)
    original_read_bytes = Path.read_bytes
    reads = []

    def swapping_read(path):
        data = original_read_bytes(path)
        if path == artifact:
            reads.append(path)
            path.write_bytes(b'{"replaced":true}')
        return data

    monkeypatch.setattr(Path, "read_bytes", swapping_read)
    verified = ea.load_verified_calibration(contract, tmp_path)
    assert verified.calibration is not None
    assert reads == [artifact]
    assert artifact.read_text(encoding="utf-8") == '{"replaced":true}'


def test_load_verified_calibration_rejects_duplicate_key(tmp_path):
    raw = json.dumps(_valid_document(), ensure_ascii=False, separators=(",", ":"))
    duplicate = ('{"schema_version":"calibration/v2",' + raw[1:]).encode("utf-8")
    _, contract = _required_artifact(tmp_path, raw=duplicate)
    with pytest.raises(ea.AttestationError, match="duplicate key"):
        ea.load_verified_calibration(contract, tmp_path)


@pytest.mark.parametrize("field,value", [("env_tag", "other-env"), ("clocks_per_us", 1801)])
def test_load_verified_calibration_rejects_contract_cross_field(tmp_path, field, value):
    _, contract = _required_artifact(tmp_path)
    bad = dataclasses.replace(contract, **{field: value})
    with pytest.raises(ea.AttestationError, match=field):
        ea.load_verified_calibration(bad, tmp_path)


def test_load_verified_calibration_rejects_repo_escape(tmp_path):
    outside = tmp_path.parent / "outside-calibration.json"
    outside.write_text("{}", encoding="utf-8")
    contract = ec.ExecutionEnvironmentContract(
        env_tag="test-env", clocks_per_us=1800, numactl=(),
        attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path="../outside-calibration.json",
            sha256=hashlib.sha256(b"{}").hexdigest(),
        ),
    )
    with pytest.raises(ea.AttestationError, match="repo_root 外"):
        ea.load_verified_calibration(contract, tmp_path)


def test_load_verified_calibration_accepts_exact_grandfathered_v1():
    repo_root = _ORCH.parent
    verified = ea.load_verified_calibration(ec.lookup("linux-baremetal"), repo_root)
    assert verified.schema_version == "calibration/v1"
    assert verified.sha256 == ea.GRANDFATHERED_V1_SHA256
    assert verified.calibration is None


def test_mode_none_rejects_hash_bound_but_non_grandfathered_v1(tmp_path):
    source = (_ORCH.parent / ec.lookup("linux-baremetal").calibration_ref.path).read_bytes()
    mutated = source + b"\n"
    artifact = tmp_path / "mutated-v1.json"
    artifact.write_bytes(mutated)
    base = ec.lookup("linux-baremetal")
    contract = dataclasses.replace(
        base,
        calibration_ref=ec.CalibrationRef(
            path=artifact.name,
            sha256=hashlib.sha256(mutated).hexdigest(),
        ),
    )
    with pytest.raises(ea.AttestationError, match="grandfathered"):
        ea.load_verified_calibration(contract, tmp_path)


def test_grandfathered_sha_is_module_constant_without_env_literal():
    source = Path(ea.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = [
        node for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name)
                and target.id == "GRANDFATHERED_V1_SHA256" for target in node.targets)
    ]
    assert len(assignments) == 1
    assert "linux-baremetal" not in source


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
