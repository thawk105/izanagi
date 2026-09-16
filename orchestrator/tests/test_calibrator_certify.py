# -*- coding: utf-8 -*-
"""calibrator certification mode の production entry と quality gate 負例。"""
from __future__ import annotations

import copy
import errno
import hashlib
import json
import math
import os
import shutil
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.calibrator import cli  # noqa: E402
from orchestrator.calibrator import runner, sweep  # noqa: E402
from orchestrator.calibrator.model import (CalibrationResult, CertificationEvidence,  # noqa: E402
                              CertificationMeasurement, NoiseFloor,
                              PerfCounters, SaturationResult, ScalePoint)
from orchestrator.calibrator.report import certification_quality_reasons  # noqa: E402
from orchestrator.calibrator.schema_v2 import validate_calibration_v2  # noqa: E402
from orchestrator.calibrator.tsc import TscMeasurement  # noqa: E402
from orchestrator.campaign import env_attestation as ea  # noqa: E402
from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator.campaign import execution_guard as eg  # noqa: E402


_EARLY_CLOCK_NOT_EVALUATED = [
    "dynamic-pre-competing-process-probe",
    "benchmark-calibration",
    "post-attestation-comparison",
    "post-isolation",
    "certification-quality",
    "late-effective-clock-self-comparison",
    "final-artifact-assembly-and-schema-validation",
    "publish-policy-identity",
    "publish",
    "published-artifact-bytes-self-comparison",
]


def _canonical_json_sha256(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _point(reps: int = 2) -> ScalePoint:
    return ScalePoint(
        records=1000, threads=2,
        counters=PerfCounters(
            llc_load_misses=20, llc_loads=100,
            instructions=300, cycles=200,
        ),
        throughputs=[100.0 + i for i in range(reps)],
        walltime_s=1.0, maxrss_kb=4096,
    )


def _result(*, cv: float | None = 0.01) -> CalibrationResult:
    return CalibrationResult(
        env_tag="test-env", threads=2, clocks_per_us=1800,
        saturation=SaturationResult(
            records=1000, saturated=True, threshold=0.01,
            miss_rate_at=0.2, l3_bytes=1024, l3_multiple=4.0,
            working_set_ratio=4.0,
            series=[{"records": 1000.0, "miss_rate": 0.2,
                     "maxrss_kb": 4096.0}],
        ),
        noise_floor=NoiseFloor(
            throughputs=[100.0, 101.0, 99.0], mean=100.0,
            median=100.0, stdev=1.0, cv=cv,
        ),
        sweep=[_point()], workload={"ycsb_zipf_skew": "0.9"},
        host={"node": "fixture", "l3_total_bytes": "1024"},
    )


def _evidence() -> CertificationEvidence:
    return CertificationEvidence(
        tsc_measured=True, cooldown_settled=True,
        measurements=[CertificationMeasurement("sweep", 2, _point())],
        all_subprocesses_succeeded=True,
        all_windows_isolated=True, post_static_matches=True,
    )


@pytest.mark.parametrize("mutate,reason", [
    (lambda r, e: setattr(e, "tsc_measured", False), "tsc-not-measured"),
    (lambda r, e: setattr(e, "cooldown_settled", False), "cooldown-not-settled"),
    (lambda r, e: setattr(e, "all_subprocesses_succeeded", False), "reps-incomplete"),
    (lambda r, e: setattr(e.measurements[0].point, "maxrss_kb", None),
     "required-metrics-missing"),
    (lambda r, e: setattr(r.saturation, "cache_floor_warning", True),
     "selection-invalid"),
    (lambda r, e: setattr(r.noise_floor, "cv", None), "within-run-cv-invalid"),
    (lambda r, e: setattr(e, "all_windows_isolated", False),
     "isolation-window-failed"),
    (lambda r, e: setattr(e, "post_static_matches", False),
     "post-attestation-mismatch"),
])
def test_quality_eight_conditions_each_fail_alone(mutate, reason):
    result = _result()
    evidence = _evidence()
    mutate(result, evidence)
    assert certification_quality_reasons(result, evidence) == [reason]


@pytest.mark.parametrize("mutate,reason", [
    (lambda r, e: e.measurements.clear(), "reps-incomplete"),
    (lambda r, e: e.measurements[0].point.throughputs.pop(), "reps-incomplete"),
    (lambda r, e: setattr(e.measurements[0].point.counters, "cycles", None),
     "required-metrics-missing"),
    (lambda r, e: setattr(r.saturation, "l3_bytes", None), "required-metrics-missing"),
    (lambda r, e: setattr(r.saturation, "records", 0), "selection-invalid"),
    (lambda r, e: setattr(r.saturation, "saturated", False), "selection-invalid"),
], ids=["measurements-empty", "throughput-count", "counter-none", "l3-none",
        "records-nonpositive", "not-saturated"])
def test_quality_compound_or_each_branch_is_load_bearing(mutate, reason):
    result = _result()
    evidence = _evidence()
    mutate(result, evidence)
    assert reason in certification_quality_reasons(result, evidence)


def test_certify_sweep_brackets_every_measurement_group(monkeypatch):
    events = []
    sink = []

    def fake_measure(binary, records, threads, clocks_per_us, **kwargs):
        events.append(("measure", records, threads, kwargs["reps"]))
        return ScalePoint(
            records=records, threads=threads,
            counters=PerfCounters(
                llc_load_misses=20, llc_loads=100,
                instructions=300, cycles=200,
            ),
            throughputs=[100.0 + i for i in range(kwargs["reps"])],
            walltime_s=1.0, maxrss_kb=4096,
        )

    monkeypatch.setattr(sweep, "measure_point", fake_measure)
    monkeypatch.setattr(sweep, "detect_l3_bytes", lambda: 1024)
    monkeypatch.setattr(
        sweep, "_apply_clocks_fallback",
        lambda *_args: (_ for _ in ()).throw(AssertionError("fallback must not run")),
    )

    def probe(label):
        events.append(("probe", label))

    result = sweep.calibrate(
        binary="fixture", env_tag="test-env", threads=2,
        start_records=1000, max_records=1000, extime=1,
        sweep_reps=2, noise_reps=3, clocks_per_us=1800,
        certify=True, skip_settle=True, window_probe=probe,
        measurement_sink=sink, log=lambda *args: None,
    )
    assert result.noise_floor is not None
    assert [item.kind for item in sink] == ["sweep", "noise"]
    assert result.scale is None
    for index, kind in enumerate(["sweep", "noise"]):
        triple = events[index * 3:(index + 1) * 3]
        assert triple[0][0] == "probe" and triple[0][1].startswith(kind + ":pre:")
        assert triple[1][0] == "measure"
        assert triple[2][0] == "probe" and triple[2][1].startswith(kind + ":post:")


def test_strict_measurement_rejects_one_failed_rep(monkeypatch):
    calls = {"n": 0}

    def fake_run_once(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("injected rep failure")
        return ({"throughput[tps]": "100", "maxrss": "100 kB"},
                PerfCounters(llc_load_misses=1, llc_loads=2,
                             instructions=3, cycles=4), 1.0)

    monkeypatch.setattr(runner, "run_once", fake_run_once)
    with pytest.raises(RuntimeError, match="rep1/3 fatal"):
        runner.measure_point(
            "fixture", 1000, 2, 1800, reps=3,
            require_all_reps=True, require_complete_metrics=True,
        )


def test_certify_sweep_rejects_missing_tsc_without_fallback(monkeypatch):
    monkeypatch.setattr(
        sweep, "measure_clocks_per_us",
        lambda: (_ for _ in ()).throw(AssertionError("measurement fallback must not run")),
    )
    with pytest.raises(RuntimeError, match="fallback is forbidden"):
        sweep.calibrate(
            binary="fixture", env_tag="test-env", threads=2,
            start_records=1000, max_records=1000, extime=1,
            sweep_reps=2, noise_reps=3, clocks_per_us=None,
            certify=True, skip_settle=True, window_probe=lambda _label: None,
            log=lambda *_args: None,
        )


def test_composite_probe_rc1_is_visibility_failure_and_cleans_child():
    with pytest.raises(runner.CompositeProbeViolation, match="visibility") as caught:
        runner.composite_competing_probe(
            nonce="abcdef1234567890",
            subprocess_runner=lambda *args, **kwargs: _Completed(
                returncode=1, stdout="", stderr=""),
        )
    assert caught.value.kind == "visibility"


def _profile() -> dict:
    return {
        "cpu": {
            "vendor": "GenuineIntel", "family": 6, "model": 143,
            "model_name_raw": "Intel Test CPU",
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
            "raw_samples_mhz": [1800.0] * 5, "median_mhz": 1800.0,
            "clocks_per_us_int": 1800, "source": "fixture",
        },
        "effective_clock": {
            "samples_mhz": [2390.0, 2410.0],
            "method": "fixture", "governor": "performance",
        },
        "visibility": {
            "hidepid": "0", "pid_ns_shared_with_host": True,
            "pid_ns_method": "proc2-kthreadd",
        },
    }


def _pegasus_shaped_probe(sample_rows: list[list[float]]):
    """Return the three probe profiles used by certify, with real-shaped clocks."""
    assert len(sample_rows) == 3
    profiles = []
    for samples in sample_rows:
        assert len(samples) == 48
        profile = _profile()
        profile["cores"] = {
            "physical": 48, "logical": 48, "smt_active": False,
            "affinity_visible": 2,
        }
        profile["cache_topology"] = [
            {"level": 1, "type": "Data", "bytes": 32768, "line": 64,
             "shared_cpus": [cpu]}
            for cpu in range(48)
        ]
        profile["numa"] = [{"node_id": 0, "cpulist": list(range(48))}]
        profile["effective_clock"] = {
            "samples_mhz": list(samples),
            "method": "proc-cpuinfo", "governor": "performance",
        }
        profiles.append(profile)

    calls = []

    def probe():
        index = len(calls)
        calls.append(index)
        return ea.normalize_observed_profile(copy.deepcopy(profiles[index]))

    return probe, profiles, calls


def _expect_48_physical_cores(receipt: dict) -> None:
    receipt["known_values_check"]["expected_cores"] = 48


def _published_bytes_self_comparison_passes(path: Path) -> bool:
    """Read published bytes only and apply the canonical clock predicate."""
    document = json.loads(path.read_bytes())
    clock = document["attestation_profile"]["effective_clock"]
    return eg.effective_clock_comparison_passes(
        {
            "samples_mhz": clock["samples_mhz"],
            "tolerance_pct": clock["tolerance_pct"],
        },
        {"samples_mhz": clock["samples_mhz"]},
    )


def _receipt(binary_sha: str, *, job_id: str = "123.server") -> dict:
    budget = cli.reservation_budget(1000, 1000, 2, 3)
    frozen_required_s = budget["required_s"] + cli.FINALIZE_RESERVE_S
    return {
        "qsub": {
            "request_id": job_id, "submit_epoch": 1784332800,
            "queue": "batch", "project": "project", "nodes": 1,
            "elapstim_req_s": frozen_required_s,
        },
        "allocation": {
            "pbs_jobid": job_id, "assigned_host_qstat": "node-a",
            "hostname_observed": "node-a", "cpuset_size": 2,
            "ht_off": True,
        },
        "toolchain": {
            "module_list": ["gcc/13"], "compiler_path": "/opt/g++",
            "compiler_version": "g++ 13", "cmake_version": "cmake 3",
        },
        "ccbench": {
            "head_sha": "a" * 40, "pinned_clean": True,
            "build_argv": [
                "cmake", "-S", "ccbench", "-B", "build",
                "-DCCBENCH_BACK_OFF=0",
                "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
                "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
                "-DCCBENCH_WAL=0",
                "-DCCBENCH_BACKOFF_FIXED=-1",
                "-DCCBENCH_TRACE=0",
                "&&", "cmake", "--build", "build",
                "--target", "ycsb_silo.exe",
            ],
            "binary_sha256": binary_sha,
        },
        "job_script_sha256": "c" * 64,
        "walltime": {
            "formula": "job-level frozen minimum fixture",
            "required_s": frozen_required_s,
            "reserve_s": cli.FINALIZE_RESERVE_S,
        },
        "known_values_check": {
            "expected_cpu_model": "Intel Test CPU", "expected_cores": 2,
            "source": "pegasus-runbook §1", "passed": True,
        },
    }


class _Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _FakeTime:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _fake_calibrate(*, bad_cv: bool = False):
    def run(**kwargs):
        result = _result(cv=0.10 if bad_cv else 0.01)
        result.env_tag = kwargs["env_tag"]
        result.clocks_per_us = kwargs["clocks_per_us"]
        sink = kwargs["measurement_sink"]
        for kind, reps in (("sweep", 2), ("noise", 3)):
            sink.append(CertificationMeasurement(kind, reps, _point(reps)))
        return result
    return run


def _invoke(tmp_path: Path, monkeypatch, *, load1=None, bad_cv=False,
            composite=None, extra_args=None, receipt_mutator=None,
            profile_fn=None, clock_fn=None,
            calibrate_fn=None, bench_runner=None) -> tuple[int, Path, Path]:
    binary = tmp_path / "ycsb_silo.exe"
    binary.write_bytes(b"trace-disabled fixture")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    receipt_path = tmp_path / "receipt.json"
    receipt = _receipt(digest)
    if receipt_mutator is not None:
        receipt_mutator(receipt)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    out = tmp_path / "output"
    monkeypatch.setattr(cli, "_output_root", lambda explicit: str(out))
    if composite is None:
        composite = lambda **kw: {  # noqa: E731
            "status": "passed", "canary_pid": 1,
            "canary_nonce": kw["nonce"], "canary_starttime": "1",
            "argv": ["pgrep"],
        }
    monkeypatch.setattr(cli, "composite_competing_probe", composite)

    def subprocess_runner(argv, **kwargs):
        if argv[0] == "nm":
            return _Completed(stdout="0000 T stock_symbol\n")
        if argv[0] == "sha256sum":
            return _Completed(stdout=f"{digest}  {binary}\n")
        if bench_runner is not None:
            return bench_runner(argv, **kwargs)
        raise AssertionError(argv)

    fake_time = _FakeTime()
    values = iter(load1 or [0.5, 0.5, 0.5])
    args = [
        "--binary", str(binary), "--env-tag", "test-env", "--threads", "2",
        "--start-records", "1000", "--max-records", "1000", "--extime", "1",
        "--sweep-reps", "2", "--noise-reps", "3", "--certify",
        "--receipt-json", str(receipt_path), "--binary-sha256", digest,
    ] + list(extra_args or [])
    rc = cli.main(
        args, probe_fn=profile_fn or (
            lambda: ea.normalize_observed_profile(copy.deepcopy(_profile()))
        ),
        load1_fn=lambda: next(values),
        clock_fn=clock_fn or (lambda: TscMeasurement([1800.0] * 5, 1800.0, 1800)),
        subprocess_runner=subprocess_runner, nonce_fn=lambda: "abcdef1234567890",
        monotonic_fn=fake_time.monotonic, sleep_fn=fake_time.sleep,
        calibrate_fn=calibrate_fn or _fake_calibrate(bad_cv=bad_cv),
    )
    attempt = out / "env/test-env/calibration/attempts/123.server"
    registered = out / "env/test-env/calibration/registered"
    return rc, attempt, registered


def test_receipt_genome_derivation_names_mocc_and_preserves_non_axis_define():
    receipt = _receipt("a" * 64)
    receipt["ccbench"]["build_argv"] = [
        "cmake", "-S", "ccbench", "-B", "build",
        "-DCCBENCH_BACK_OFF=0",
        "-DCCBENCH_TEMPERATURE_RESET_OPT=1",
        "-DCCBENCH_KEY_SORT=0",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
        "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
        "-DCCBENCH_WAL=0",
        "-DCCBENCH_BACKOFF_FIXED=-1",
        "-DCCBENCH_TRACE=0",
        "&&", "cmake", "--build", "build", "--target", "ycsb_mocc.exe",
    ]

    assert cli._canonical_genome_from_receipt(
        receipt, "/fixture/ycsb_mocc.exe",
    ) == (
        "mocc|BACKOFF_FIXED=-1,BACK_OFF=0,KEY_SORT=0,"
        "NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,"
        "TEMPERATURE_RESET_OPT=1,WAL=0"
    )


def _remove_receipt_define(receipt: dict, flag: str) -> None:
    prefix = f"-DCCBENCH_{flag}="
    receipt["ccbench"]["build_argv"] = [
        token for token in receipt["ccbench"]["build_argv"]
        if not token.startswith(prefix)
    ]


def _replace_receipt_token(receipt: dict, old: str, new: str) -> None:
    argv = receipt["ccbench"]["build_argv"]
    argv[argv.index(old)] = new


@pytest.mark.parametrize("mutate", [
    pytest.param(
        lambda receipt: _remove_receipt_define(receipt, "WAL"),
        id="missing-protocol-axis",
    ),
    pytest.param(
        lambda receipt: _replace_receipt_token(
            receipt, "-DCCBENCH_TRACE=0", "-DCCBENCH_TRACE=1",
        ),
        id="receipt-trace-enabled",
    ),
])
def test_receipt_genome_invalid_is_rejected_before_benchmark(
        tmp_path, monkeypatch, mutate):
    calibrate_calls = []
    rc, attempt, registered = _invoke(
        tmp_path,
        monkeypatch,
        receipt_mutator=mutate,
        calibrate_fn=lambda **kwargs: calibrate_calls.append(kwargs),
    )

    assert rc != 0
    assert calibrate_calls == []
    rejection = json.loads((attempt / "rejection.json").read_text(encoding="utf-8"))
    assert any(
        reason.startswith("receipt-genome-invalid")
        for reason in rejection["quality"]["reasons"]
    )
    assert not registered.exists()


@pytest.mark.parametrize("mutate", [
    pytest.param(
        lambda receipt: receipt["ccbench"]["build_argv"].insert(
            receipt["ccbench"]["build_argv"].index("&&"),
            "-DCCBENCH_BACK_OFF=1",
        ),
        id="duplicate-flag",
    ),
    pytest.param(
        lambda receipt: receipt["ccbench"]["build_argv"].remove("--target"),
        id="missing-target",
    ),
    pytest.param(
        lambda receipt: receipt["ccbench"]["build_argv"].append(
            "-DCCBENCH_WAL=1",
        ),
        id="define-on-build-side",
    ),
    pytest.param(
        lambda receipt: _replace_receipt_token(
            receipt, "-DCCBENCH_WAL=0", "-DCCBENCH_WAL=not-an-int",
        ),
        id="non-integer-define",
    ),
    pytest.param(
        lambda receipt: _replace_receipt_token(
            receipt, "-DCCBENCH_WAL=0", "-DCCBENCH_WAL=",
        ),
        id="missing-define-value",
    ),
    pytest.param(
        lambda receipt: _remove_receipt_define(receipt, "TRACE"),
        id="missing-trace-define",
    ),
    pytest.param(
        lambda receipt: _replace_receipt_token(
            receipt, "ycsb_silo.exe", "ycsb_mocc.exe",
        ),
        id="binary-target-mismatch",
    ),
    pytest.param(
        lambda receipt: receipt["ccbench"]["build_argv"].insert(1, "&&"),
        id="duplicate-separator",
    ),
])
def test_receipt_genome_malformed_argv_is_rejected_before_benchmark(
        tmp_path, monkeypatch, mutate):
    calibrate_calls = []
    rc, attempt, _ = _invoke(
        tmp_path,
        monkeypatch,
        receipt_mutator=mutate,
        calibrate_fn=lambda **kwargs: calibrate_calls.append(kwargs),
    )
    assert rc != 0
    assert calibrate_calls == []
    rejection = json.loads((attempt / "rejection.json").read_text(encoding="utf-8"))
    assert any(
        reason.startswith("receipt-genome-invalid")
        for reason in rejection["quality"]["reasons"]
    )


def test_cli_rejects_certify_clock_override_before_attempt(tmp_path, monkeypatch):
    rc, attempt, _ = _invoke(
        tmp_path, monkeypatch, extra_args=["--clocks-per-us", "1800"])
    assert rc == 2
    assert not attempt.exists()


def test_cli_rr50_certify_keeps_capability_none_and_writes_no_marker(
        tmp_path, monkeypatch):
    calls = []

    def capture(**kwargs):
        calls.append(kwargs)
        return _fake_calibrate()(**kwargs)

    rc, _, _ = _invoke(
        tmp_path, monkeypatch,
        extra_args=["--workload", "ycsb_rratio=50"],
        calibrate_fn=capture,
    )
    assert rc == 0
    assert calls[0]["calibration_observation_capability"] is None
    assert not (tmp_path / "output/calibration-capability-markers").exists()


def test_cli_rr80_certify_issues_once_and_marker_blocks_staging_replay(
        tmp_path, monkeypatch):
    calls = []

    def capture(**kwargs):
        calls.append(kwargs)
        return _fake_calibrate()(**kwargs)

    workload = ["--workload", "ycsb_rratio=80"]
    rc, attempt, _ = _invoke(
        tmp_path, monkeypatch, extra_args=workload, calibrate_fn=capture,
    )
    assert rc == 0
    assert calls[0]["calibration_observation_capability"] is not None
    marker = tmp_path / "output/calibration-capability-markers/123.server.json"
    marker_document = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_document["job_id"] == "123.server"
    assert marker_document["env_tag"] == "test-env"
    assert len(marker_document["receipt_sha256"]) == 64
    assert len(marker_document["plan_sha256"]) == 64

    shutil.rmtree(attempt)
    rc_replay, replay_attempt, _ = _invoke(
        tmp_path, monkeypatch, extra_args=workload,
    )
    assert rc_replay != 0
    assert "attempt-replay" in (replay_attempt / "rejection.json").read_text()


def test_cli_rejects_certify_out_root_before_attempt(tmp_path, monkeypatch):
    rc, attempt, _ = _invoke(
        tmp_path, monkeypatch, extra_args=["--out-root", str(tmp_path / "forbidden")])
    assert rc == 2
    assert not attempt.exists()


def test_noncertify_output_remains_genome_absent(tmp_path):
    binary = tmp_path / "ycsb_mocc.exe"
    binary.write_bytes(b"trace-disabled fixture")

    def subprocess_runner(argv, **_kwargs):
        assert argv[0] == "nm"
        return _Completed(stdout="0000 T stock_symbol\n")

    rc = cli.main(
        [
            "--binary", str(binary),
            "--env-tag", "test-env",
            "--threads", "2",
            "--clocks-per-us", "1800",
            "--out-root", str(tmp_path / "output"),
        ],
        subprocess_runner=subprocess_runner,
        calibrate_fn=lambda **_kwargs: _result(),
    )

    assert rc == 0
    document = json.loads(
        (tmp_path / "output/env/test-env/calibration/"
         "calibration_t2_default.json").read_text(encoding="utf-8")
    )
    assert "genome" not in document


def test_cli_rejects_binary_sha256_mismatch_before_calibration(tmp_path, monkeypatch):
    called = []
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, extra_args=["--binary-sha256", "0" * 64],
        calibrate_fn=lambda **_kwargs: called.append(True),
    )
    assert rc != 0
    assert called == []
    assert (attempt / "rejection.json").exists()
    assert not registered.exists()


@pytest.mark.parametrize("clock_fn", [
    lambda: None,
    lambda: TscMeasurement([1800.0] * 5, 1799.0, 1800),
], ids=["none", "inconsistent-median"])
def test_cli_rejects_invalid_measured_tsc_before_calibration(
        tmp_path, monkeypatch, clock_fn):
    called = []
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, clock_fn=clock_fn,
        calibrate_fn=lambda **_kwargs: called.append(True),
    )
    assert rc != 0
    assert called == []
    assert (attempt / "rejection.json").exists()
    assert not registered.exists()


@pytest.mark.parametrize("mutate,reason", [
    (lambda r: r["allocation"].__setitem__("hostname_observed", "node-b"),
     "acquisition-host-mismatch"),
    (lambda r: r["qsub"].__setitem__("request_id", "other.server"),
     "acquisition-job-id-mismatch"),
    (lambda r: r["qsub"].__setitem__("nodes", 2),
     "acquisition-node-count-invalid"),
    (lambda r: r["ccbench"].__setitem__("binary_sha256", "0" * 64),
     "acquisition-binary-hash-mismatch"),
    (lambda r: r["walltime"].__setitem__(
        "required_s", cli.reservation_budget(1000, 1000, 2, 3)["required_s"]),
     "reservation-mismatch"),
    (lambda r: r["known_values_check"].__setitem__("passed", False),
     "known-values-check-failed"),
    (lambda r: r["qsub"].__setitem__(
        "elapstim_req_s", r["walltime"]["required_s"] - 1),
     "reservation-qsub-mismatch"),
], ids=["host", "request-id", "nodes", "receipt-binary", "internal-budget",
        "known-values", "qsub-containment"])
def test_cli_acquisition_gate_rejects_before_benchmark_without_outputs(
        tmp_path, monkeypatch, mutate, reason):
    called = []
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, receipt_mutator=mutate,
        calibrate_fn=lambda **_kwargs: called.append(True),
    )
    assert rc != 0
    assert called == []
    rejection = json.loads((attempt / "rejection.json").read_text(encoding="utf-8"))
    assert any(reason in item for item in rejection["quality"]["reasons"])
    assert not (attempt / "candidate.json").exists()
    assert not (attempt / "calibration.json").exists()
    assert not (attempt / "calibration.md").exists()
    assert not (attempt / "window-probes.json").exists()
    assert not registered.exists()


def test_cli_acquisition_gate_accepts_zero_subrequest_prefix_via_production_entry(
        tmp_path, monkeypatch):
    rc, _, registered = _invoke(
        tmp_path, monkeypatch,
        receipt_mutator=lambda r: r["allocation"].__setitem__(
            "pbs_jobid", "0:123.server"),
    )
    assert rc == 0
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    validated = validate_calibration_v2(published[0].read_bytes())
    assert validated.acquisition_receipt.qsub.request_id == "123.server"
    assert validated.acquisition_receipt.allocation.pbs_jobid == "0:123.server"


@pytest.mark.parametrize("field,value", [
    ("hidepid", "2"),
    ("pid_ns_shared_with_host", False),
], ids=["hidepid", "pid-namespace"])
def test_cli_visibility_gate_rejects_non_host_visibility_before_benchmark(
        tmp_path, monkeypatch, field, value):
    profile = _profile()
    profile["visibility"][field] = value
    called = []
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch,
        profile_fn=lambda: ea.normalize_observed_profile(copy.deepcopy(profile)),
        calibrate_fn=lambda **_kwargs: called.append(True),
    )
    assert rc != 0
    assert called == []
    rejection = json.loads((attempt / "rejection.json").read_text(encoding="utf-8"))
    assert any("visibility-not-host" in item for item in rejection["quality"]["reasons"])
    assert not registered.exists()


def test_cli_cooldown_failure_is_fatal_and_staged(tmp_path, monkeypatch):
    # 41 observations: 0,30,...,1200 reaches the frozen 20 minute timeout.
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, load1=[2.0] * 41)
    assert rc != 0
    rejection = json.loads((attempt / "rejection.json").read_text())
    assert rejection["quality"]["status"] == "rejected"
    assert any("cooldown-timeout" in r for r in rejection["quality"]["reasons"])
    assert not registered.exists()


def test_cli_probe_violation_kills_attempt_and_never_publishes(tmp_path, monkeypatch):
    def violation(**kwargs):
        raise cli.CompositeProbeViolation("competition", "fixture competitor")

    rc, attempt, registered = _invoke(tmp_path, monkeypatch, composite=violation)
    assert rc != 0
    assert (attempt / "rejection.json").exists()
    assert not registered.exists()


def test_cli_quality_rejection_is_v2_staged_and_nonzero(tmp_path, monkeypatch):
    rc, attempt, registered = _invoke(tmp_path, monkeypatch, bad_cv=True)
    assert rc != 0
    raw = (attempt / "calibration.json").read_bytes()
    validated = validate_calibration_v2(raw)
    assert validated.quality.status == "rejected"
    assert "within-run-cv-invalid" in validated.quality.reasons
    assert not registered.exists()


def test_self_gate_rejects_outlier_at_every_index():
    for index in range(48):
        samples = [2101.0] * 48
        samples[index] = 3080.0
        assert not cli._effective_clock_self_comparison_passes({
            "effective_clock": {
                "samples_mhz": samples,
                "method": "proc-cpuinfo",
                "governor": "performance",
                "tolerance_pct": 2.0,
            },
        })


def test_self_gate_rejects_all_nonpolicy_equality_edges():
    for tolerance in (
        math.nextafter(2.0, math.inf),
        math.nextafter(2.0, -math.inf),
        2.5,
        2.9,
    ):
        assert not cli._effective_clock_self_comparison_passes({
            "effective_clock": {
                "samples_mhz": [100.0],
                "method": "proc-cpuinfo",
                "governor": "performance",
                "tolerance_pct": tolerance,
            },
        })


@pytest.mark.parametrize("outlier_index", [0, 24, 47])
def test_cli_effective_clock_self_failure_is_acquisition_rejected_before_benchmark(
        tmp_path, monkeypatch, outlier_index):
    failing_samples = [2101.0] * 48
    failing_samples[outlier_index] = 3079.456
    probe, profiles, calls = _pegasus_shaped_probe([
        [2101.0] * 48,
        failing_samples,
        [2101.0] * 48,
    ])
    calibrate_calls = []
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
        calibrate_fn=lambda **kwargs: calibrate_calls.append(kwargs),
    )

    assert rc != 0
    assert calls == [0, 1]
    assert calibrate_calls == []
    rejection = json.loads((attempt / "rejection.json").read_bytes())
    assert rejection["quality"] == {
        "status": "rejected",
        "reasons": ["effective-clock-self-comparison-failed"],
    }
    assert rejection["not_evaluated"] == _EARLY_CLOCK_NOT_EVALUATED
    effective_clock_input = rejection["diagnostics"]["effective_clock_input"]
    assert effective_clock_input == {
        "samples_mhz": failing_samples,
        "tolerance_pct": 2.0,
        "method": "proc-cpuinfo",
        "governor": "performance",
    }
    assert not eg.effective_clock_comparison_passes(
        {
            "samples_mhz": effective_clock_input["samples_mhz"],
            "tolerance_pct": effective_clock_input["tolerance_pct"],
        },
        {"samples_mhz": effective_clock_input["samples_mhz"]},
    )
    expected_profile = copy.deepcopy(profiles[1])
    expected_profile["effective_clock"]["tolerance_pct"] = 2.0
    expected_profile["tsc"] = {
        "raw_samples_mhz": [1800.0] * 5,
        "median_mhz": 1800.0,
        "clocks_per_us_int": 1800,
        "source": "clock_gettime-monotonic/rdtscp",
    }
    assert rejection["diagnostics"]["attestation_profile_sha256"] == (
        _canonical_json_sha256(expected_profile)
    )
    diagnostic = rejection["diagnostics"]["effective_clock_self_comparison"]
    assert diagnostic["input_valid"] is True
    assert diagnostic["policy_matches"] is True
    assert diagnostic["band_pass"] is False
    assert diagnostic["median_mhz"] == 2101.0
    assert diagnostic["lower_mhz"] == pytest.approx(2058.98)
    assert diagnostic["upper_mhz"] == pytest.approx(2143.02)
    assert diagnostic["out_of_band_count"] == 1
    assert diagnostic["evaluation_error"] is None
    assert diagnostic["violations"] == [{
        "sample_index": outlier_index,
        "sample_mhz": 3079.456,
        "direction": "above",
        "deviation_from_median_mhz": pytest.approx(978.456),
        "outside_by_mhz": pytest.approx(936.436),
    }]
    assert not (attempt / "calibration.json").exists()
    assert not (attempt / "calibration.md").exists()
    assert not (attempt / "window-probes.json").exists()
    assert not (attempt / "candidate.json").exists()
    assert not (attempt / "publish.json").exists()
    assert not (attempt / "published-self-comparison.json").exists()
    assert not registered.exists()


def test_cli_rejection_profile_hash_recomputes_from_artifact_only(
        tmp_path, monkeypatch):
    failing_samples = [2101.0] * 48
    failing_samples[24] = 3079.456
    probe, _, _ = _pegasus_shaped_probe([
        [2101.0] * 48,
        failing_samples,
        [2101.0] * 48,
    ])
    rc, attempt, _ = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
        calibrate_fn=lambda **_kwargs: None,
    )
    assert rc != 0
    rejection = json.loads((attempt / "rejection.json").read_bytes())
    diagnostics = rejection["diagnostics"]
    assert diagnostics["attestation_profile_canonicalization"] == (
        "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True)/utf-8"
    )
    artifact_profile = diagnostics["attestation_profile"]
    artifact_preimage = json.dumps(
        artifact_profile,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    assert diagnostics["attestation_profile_sha256"] == hashlib.sha256(
        artifact_preimage
    ).hexdigest()


def test_cli_early_admission_uses_canonical_predicate_not_diagnostic_count(
        tmp_path, monkeypatch):
    failing_samples = [2101.0] * 47 + [3079.456]
    probe, _, _ = _pegasus_shaped_probe([
        [2101.0] * 48,
        failing_samples,
        [2101.0] * 48,
    ])
    monkeypatch.setattr(
        cli, "effective_clock_comparison_diagnostics",
        lambda _expected, _observed: {
            "input_valid": True,
            "policy_matches": True,
            "band_pass": True,
            "median_mhz": 2101.0,
            "lower_mhz": 2058.98,
            "upper_mhz": 2143.02,
            "out_of_band_count": 0,
            "violations": [],
            "evaluation_error": None,
        },
    )
    calibrate_calls = []
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
        calibrate_fn=lambda **kwargs: calibrate_calls.append(kwargs),
    )
    assert rc != 0
    assert calibrate_calls == []
    rejection = json.loads((attempt / "rejection.json").read_bytes())
    assert rejection["quality"] == {
        "status": "rejected",
        "reasons": ["effective-clock-self-comparison-failed"],
    }
    assert rejection["not_evaluated"] == _EARLY_CLOCK_NOT_EVALUATED
    assert rejection["diagnostics"]["effective_clock_input"][
        "tolerance_pct"
    ] == 2.0
    assert rejection["diagnostics"]["effective_clock_self_comparison"][
        "out_of_band_count"
    ] == 0
    assert not (attempt / "candidate.json").exists()
    assert not (attempt / "publish.json").exists()
    assert not (attempt / "published-self-comparison.json").exists()
    assert not registered.exists()


def test_cli_late_gate_rechecks_policy_after_benchmark(tmp_path, monkeypatch):
    probe, _, calls = _pegasus_shaped_probe([[2101.0] * 48] * 3)
    real_calibrate = _fake_calibrate()

    def rebind_policy_then_return(**kwargs):
        monkeypatch.setattr(
            cli.effective_clock_policy, "EFFECTIVE_CLOCK_TOLERANCE_PCT", 3.0,
        )
        return real_calibrate(**kwargs)

    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
        calibrate_fn=rebind_policy_then_return,
    )
    assert calls == [0, 1, 2]
    assert rc != 0
    rejected = validate_calibration_v2((attempt / "calibration.json").read_bytes())
    assert "effective-clock-self-comparison-failed" in rejected.quality.reasons
    assert not registered.exists()


def test_cli_publish_gate_rejects_policy_change_after_late_gate(
        tmp_path, monkeypatch):
    def rebind_before_publish(_size):
        monkeypatch.setattr(
            cli.effective_clock_policy,
            "EFFECTIVE_CLOCK_TOLERANCE_PCT",
            3.0,
        )
        return "policy-change"

    monkeypatch.setattr(cli.secrets, "token_hex", rebind_before_publish)
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)
    assert rc != 0
    rejected = validate_calibration_v2((attempt / "calibration.json").read_bytes())
    assert any(
        reason.startswith("effective-clock-policy-changed:")
        for reason in rejected.quality.reasons
    )
    assert not (attempt / "candidate.json").exists()
    assert not (attempt / "publish.json").exists()
    assert not list(registered.glob("calibration-*.json"))
    assert not list(registered.glob(".publish-*.tmp"))


def test_cli_publish_temp_write_failure_removes_partial_file(
        tmp_path, monkeypatch):
    real_fsync = cli.os.fsync

    def fail_publish_fsync(fd):
        if "/.publish-" in os.readlink(f"/proc/self/fd/{fd}"):
            raise OSError("injected publish write failure")
        return real_fsync(fd)

    monkeypatch.setattr(cli.os, "fsync", fail_publish_fsync)
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)
    assert rc != 0
    orphans = list(registered.glob(".publish-*.tmp"))
    assert len(orphans) == 1
    rejected = validate_calibration_v2((attempt / "calibration.json").read_bytes())
    assert len(rejected.quality.reasons) == 1
    assert rejected.quality.reasons[0].startswith(
        "publish-temporary-write-failed: temporary-path="
    )
    assert str(orphans[0]) in rejected.quality.reasons[0]
    assert rejected.quality.reasons[0].endswith(
        "OSError: injected publish write failure"
    )


def test_cli_publish_temp_cleanup_failure_is_structured(
        tmp_path, monkeypatch):
    real_unlink = cli.os.unlink

    def fail_publish_rename(_source, _target):
        raise cli.CertificationError("publish-failed", "injected rename failure")

    def deny_publish_temp_cleanup(path):
        if "/.publish-" in os.fspath(path):
            raise PermissionError(errno.EACCES, "injected cleanup denial")
        return real_unlink(path)

    monkeypatch.setattr(cli, "_rename_noreplace", fail_publish_rename)
    monkeypatch.setattr(cli.os, "unlink", deny_publish_temp_cleanup)
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)
    assert rc != 0
    assert len(list(registered.glob(".publish-*.tmp"))) == 1
    rejected = validate_calibration_v2((attempt / "calibration.json").read_bytes())
    assert len(rejected.quality.reasons) == 1
    assert rejected.quality.reasons[0].startswith(
        "publish-temporary-cleanup-failed: PermissionError:"
    )


def test_cli_publish_rename_failure_cleans_completed_temp(
        tmp_path, monkeypatch):
    def fail_publish_rename(source, _target):
        assert Path(source).is_file()
        raise cli.CertificationError("publish-failed", "injected rename failure")

    monkeypatch.setattr(cli, "_rename_noreplace", fail_publish_rename)
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)

    assert rc != 0
    assert not list(registered.glob(".publish-*.tmp"))
    rejected = validate_calibration_v2((attempt / "calibration.json").read_bytes())
    assert rejected.quality.reasons == [
        "publish-failed: injected rename failure",
    ]


def test_write_rejection_preserves_legacy_exclusive_write_failure_behavior(
        tmp_path, monkeypatch):
    staging = tmp_path / "attempt"
    staging.mkdir()
    real_fsync = cli.os.fsync

    def fail_rejection_fsync(fd):
        if os.readlink(f"/proc/self/fd/{fd}").endswith("/rejection.json"):
            raise OSError("injected rejection write failure")
        return real_fsync(fd)

    monkeypatch.setattr(cli.os, "fsync", fail_rejection_fsync)
    with pytest.raises(OSError, match="injected rejection write failure"):
        cli._write_rejection(str(staging), ["fixture-rejection"], {})

    assert (staging / "rejection.json").is_file()


@pytest.mark.parametrize("existing_kind", ["file", "symlink"])
def test_cli_publish_temp_collision_preserves_existing_path(
        tmp_path, monkeypatch, existing_kind):
    registered = tmp_path / "output/env/test-env/calibration/registered"
    registered.mkdir(parents=True)
    existing = registered / ".publish-123.server-collision.tmp"
    expected_bytes = b"other-owner"
    if existing_kind == "file":
        existing.write_bytes(expected_bytes)
    else:
        referent = tmp_path / "other-owner-target"
        referent.write_bytes(expected_bytes)
        existing.symlink_to(referent)

    monkeypatch.setattr(cli.secrets, "token_hex", lambda _size: "collision")
    rc, _, returned_registered = _invoke(tmp_path, monkeypatch)

    assert rc != 0
    assert returned_registered == registered
    if existing_kind == "symlink":
        assert existing.is_symlink()
    assert existing.read_bytes() == expected_bytes


def test_cli_exact_2101_profile_passes_both_gates_and_publishes(
        tmp_path, monkeypatch):
    probe, _, calls = _pegasus_shaped_probe([[2101.0] * 48] * 3)
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
    )
    assert calls == [0, 1, 2]
    assert rc == 0
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    assert _published_bytes_self_comparison_passes(published[0])
    self_comparison = json.loads(
        (attempt / "published-self-comparison.json").read_bytes()
    )
    assert self_comparison == {
        "schema": "izanagi/published-effective-clock-self-comparison/v1",
        "passed": True,
        "input_sha256": hashlib.sha256(published[0].read_bytes()).hexdigest(),
        "policy_identity": {
            "authority": (
                "calibrator.effective_clock_policy."
                "EFFECTIVE_CLOCK_TOLERANCE_PCT"
            ),
            "tolerance_pct": 2.0,
        },
    }


def test_independent_published_bytes_self_comparison_detects_tampering(
        tmp_path, monkeypatch):
    probe, _, _ = _pegasus_shaped_probe([[2101.0] * 48] * 3)
    real_rename = cli._rename_noreplace

    def rename_then_tamper(source, target):
        method = real_rename(source, target)
        target_path = Path(target)
        tampered = json.loads(target_path.read_bytes())
        tampered["attestation_profile"]["effective_clock"][
            "samples_mhz"
        ][24] = 3079.456
        target_path.write_text(json.dumps(tampered), encoding="utf-8")
        return method

    monkeypatch.setattr(cli, "_rename_noreplace", rename_then_tamper)
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
    )
    assert rc != 0
    published = next(registered.glob("calibration-*.json"))
    assert not _published_bytes_self_comparison_passes(published)
    self_comparison = json.loads(
        (attempt / "published-self-comparison.json").read_bytes()
    )
    assert self_comparison["passed"] is False
    assert self_comparison["input_sha256"] == hashlib.sha256(
        published.read_bytes()
    ).hexdigest()
    assert self_comparison["policy_identity"]["tolerance_pct"] == 2.0
    rejected = validate_calibration_v2((attempt / "calibration.json").read_bytes())
    assert rejected.quality.status == "rejected"
    assert rejected.quality.reasons == [
        "published-effective-clock-self-comparison-failed",
    ]
    assert not (attempt / "candidate.json").exists()
    assert not (attempt / "publish.json").exists()
    assert published.exists()


@pytest.mark.parametrize("outlier_index", [0, 24, 47])
def test_cli_effective_clock_self_failure_is_quality_rejected_before_publish(
        tmp_path, monkeypatch, outlier_index):
    failing_samples = [2101.0] * 48
    failing_samples[outlier_index] = 3079.456
    sample_rows = [
        [2101.0] * 47 + [2095.0],
        failing_samples,
        [2101.0] * 47 + [2120.0],
    ]
    probe, profiles, calls = _pegasus_shaped_probe(sample_rows)
    assert len({tuple(row) for row in sample_rows}) == 3
    assert all(set(profile["effective_clock"]) == {
        "samples_mhz", "method", "governor",
    } for profile in profiles)
    policy_results = []
    for profile in profiles:
        expected = {
            "samples_mhz": list(profile["effective_clock"]["samples_mhz"]),
            "tolerance_pct": 2.0,
        }
        policy_results.append(eg.effective_clock_comparison_passes(
            expected, {"samples_mhz": list(expected["samples_mhz"])},
        ))
    assert policy_results == [True, False, True]

    calibrate_calls = []
    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
        calibrate_fn=lambda **kwargs: calibrate_calls.append(kwargs),
    )

    assert calls == [0, 1]
    assert calibrate_calls == []
    assert rc != 0
    rejection = json.loads((attempt / "rejection.json").read_bytes())
    assert rejection["quality"] == {
        "status": "rejected",
        "reasons": ["effective-clock-self-comparison-failed"],
    }
    assert rejection["not_evaluated"] == _EARLY_CLOCK_NOT_EVALUATED
    effective_clock_input = rejection["diagnostics"]["effective_clock_input"]
    assert effective_clock_input == {
        "samples_mhz": sample_rows[1],
        "tolerance_pct": 2.0,
        "method": "proc-cpuinfo",
        "governor": "performance",
    }
    assert len(effective_clock_input["samples_mhz"]) == 48
    assert effective_clock_input["samples_mhz"][outlier_index] == 3079.456
    assert not eg.effective_clock_comparison_passes(
        {
            "samples_mhz": effective_clock_input["samples_mhz"],
            "tolerance_pct": effective_clock_input["tolerance_pct"],
        },
        {"samples_mhz": effective_clock_input["samples_mhz"]},
    )
    expected_profile = copy.deepcopy(profiles[1])
    expected_profile["effective_clock"]["tolerance_pct"] = 2.0
    expected_profile["tsc"] = {
        "raw_samples_mhz": [1800.0] * 5,
        "median_mhz": 1800.0,
        "clocks_per_us_int": 1800,
        "source": "clock_gettime-monotonic/rdtscp",
    }
    assert rejection["diagnostics"]["attestation_profile_sha256"] == (
        _canonical_json_sha256(expected_profile)
    )
    diagnostic = rejection["diagnostics"]["effective_clock_self_comparison"]
    assert diagnostic["input_valid"] is True
    assert diagnostic["policy_matches"] is True
    assert diagnostic["band_pass"] is False
    assert diagnostic["out_of_band_count"] == 1
    assert diagnostic["evaluation_error"] is None
    assert diagnostic["violations"] == [{
        "sample_index": outlier_index,
        "sample_mhz": 3079.456,
        "direction": "above",
        "deviation_from_median_mhz": pytest.approx(978.456),
        "outside_by_mhz": pytest.approx(936.436),
    }]
    assert not (attempt / "calibration.json").exists()
    assert not (attempt / "calibration.md").exists()
    assert not (attempt / "window-probes.json").exists()
    assert not (attempt / "candidate.json").exists()
    assert not (attempt / "publish.json").exists()
    assert not (attempt / "published-self-comparison.json").exists()
    assert not registered.exists()


def test_cli_published_artifact_passes_runtime_effective_clock_self_comparison(
        tmp_path, monkeypatch):
    sample_rows = [
        [2101.0] * 47 + [2095.0],
        [2101.0] * 47 + [2110.0],
        [2101.0] * 47 + [2120.0],
    ]
    probe, profiles, calls = _pegasus_shaped_probe(sample_rows)
    assert len({tuple(row) for row in sample_rows}) == 3
    assert all(set(profile["effective_clock"]) == {
        "samples_mhz", "method", "governor",
    } for profile in profiles)
    rc, _, registered = _invoke(
        tmp_path, monkeypatch, profile_fn=probe,
        receipt_mutator=_expect_48_physical_cores,
    )
    assert calls == [0, 1, 2]
    assert rc == 0
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    validated = validate_calibration_v2(published[0].read_bytes())
    clock = validated.attestation_profile.effective_clock
    assert list(clock.samples_mhz) == sample_rows[1]
    # U-2/U-3 が producer の accepted set を policy 2.0 へ縮小したため。
    assert clock.tolerance_pct == 2.0
    expected = {
        "samples_mhz": list(clock.samples_mhz),
        "tolerance_pct": clock.tolerance_pct,
    }
    observed = {"samples_mhz": list(clock.samples_mhz)}
    assert eg._independent_comparison_passes(
        "effective_clock.samples_mhz", expected, observed,
    )


def test_cli_artifact_injects_effective_clock_policy(tmp_path, monkeypatch):
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)

    assert rc == 0
    attempt_artifact = validate_calibration_v2(
        (attempt / "calibration.json").read_bytes(),
    )
    attempt_clock = attempt_artifact.attestation_profile.effective_clock
    assert attempt_clock.tolerance_pct == 2.0
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    registered_artifact = validate_calibration_v2(published[0].read_bytes())
    registered_clock = registered_artifact.attestation_profile.effective_clock
    assert registered_clock.tolerance_pct == 2.0


def test_cli_certified_attempt_and_published_artifact_record_receipt_genome(
        tmp_path, monkeypatch):
    expected = (
        "silo|BACKOFF_FIXED=-1,BACK_OFF=0,"
        "NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
    )

    rc, attempt, registered = _invoke(tmp_path, monkeypatch)

    assert rc == 0
    attempt_artifact = validate_calibration_v2(
        (attempt / "calibration.json").read_bytes(),
    )
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    registered_artifact = validate_calibration_v2(published[0].read_bytes())
    assert attempt_artifact.genome == expected
    assert registered_artifact.genome == expected


def test_effective_clock_policy_metamorphic_wiring_producer_loader_issuer_consumer_self(
        tmp_path, monkeypatch):
    """Policy 変異が silo 以外の全 current admission layer へ同時に届く。"""
    monkeypatch.setattr(
        cli.effective_clock_policy, "EFFECTIVE_CLOCK_TOLERANCE_PCT", 3.0,
    )
    three_root = tmp_path / "policy-three"
    three_root.mkdir()
    vector_rows = [
        [2101.0] * 48,
        [2101.0] * 47 + [2164.03],
        [2101.0] * 48,
    ]
    probe_three, _, calls_three = _pegasus_shaped_probe(vector_rows)
    rc, _, registered = _invoke(
        three_root, monkeypatch, profile_fn=probe_three,
        receipt_mutator=_expect_48_physical_cores,
    )
    assert calls_three == [0, 1, 2]
    assert rc == 0
    published = next(registered.glob("calibration-*.json"))
    produced = validate_calibration_v2(published.read_bytes())
    assert produced.attestation_profile.effective_clock.tolerance_pct == 3.0

    relative = published.relative_to(three_root).as_posix()
    contract = ec.ExecutionEnvironmentContract(
        env_tag=produced.env_tag,
        clocks_per_us=produced.clocks_per_us,
        numactl=(),
        attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(
            single_process=True, allow_resume=False,
        ),
        calibration_ref=ec.CalibrationRef(
            path=relative,
            sha256=hashlib.sha256(published.read_bytes()).hexdigest(),
        ),
    )
    verified = ea.load_verified_calibration(contract, three_root)
    assert verified.calibration is not None

    expected_raw = ea.profile_to_dict(verified.attestation_profile)
    expected_raw["effective_clock"]["samples_mhz"] = [2101.0] * 48
    expected = ea.normalize_profile(expected_raw)
    observed_raw = copy.deepcopy(expected_raw)
    del observed_raw["effective_clock"]["tolerance_pct"]
    observed_raw["effective_clock"]["samples_mhz"] = (
        [2101.0] * 47 + [2164.03]
    )
    observed = ea.normalize_observed_profile(observed_raw)
    comparisons = ea.compare_profiles(expected, observed, now_fn=lambda: 0)
    clock_comparison = next(
        item for item in comparisons
        if item["field"] == "effective_clock.samples_mhz"
    )
    assert clock_comparison["verdict"] == "pass"
    assert eg.effective_clock_comparison_passes(
        clock_comparison["expected"], clock_comparison["observed"],
    )
    self_clock = copy.deepcopy(expected_raw["effective_clock"])
    self_clock["samples_mhz"] = [2101.0] * 47 + [2164.03]
    assert cli._effective_clock_self_comparison_passes({
        "effective_clock": self_clock,
    })
    receipt_three = eg.attest_and_build_receipt(
        contract, verified, probe_fn=lambda: observed,
        now_fn=lambda: "2026-08-05T00:00:00Z",
    )
    assert eg.receipt_matches_contract(
        receipt_three,
        env_tag=contract.env_tag,
        contract_sha256=contract.contract_sha256,
        attestation_mode="required",
        verified_calibration=verified,
    )

    monkeypatch.setattr(
        cli.effective_clock_policy, "EFFECTIVE_CLOCK_TOLERANCE_PCT", 2.0,
    )
    two_root = tmp_path / "policy-two"
    two_root.mkdir()
    probe_two, profiles_two, calls_two = _pegasus_shaped_probe(vector_rows)
    calibrate_two_calls = []
    rc_two, attempt_two, registered_two = _invoke(
        two_root, monkeypatch, profile_fn=probe_two,
        receipt_mutator=_expect_48_physical_cores,
        calibrate_fn=lambda **kwargs: calibrate_two_calls.append(kwargs),
    )
    assert calls_two == [0, 1]
    assert calibrate_two_calls == []
    assert rc_two != 0
    rejected_two = json.loads((attempt_two / "rejection.json").read_bytes())
    assert rejected_two["quality"] == {
        "status": "rejected",
        "reasons": ["effective-clock-self-comparison-failed"],
    }
    assert rejected_two["not_evaluated"] == _EARLY_CLOCK_NOT_EVALUATED
    clock_input_two = rejected_two["diagnostics"]["effective_clock_input"]
    assert clock_input_two == {
        "samples_mhz": vector_rows[1],
        "tolerance_pct": 2.0,
        "method": "proc-cpuinfo",
        "governor": "performance",
    }
    assert len(clock_input_two["samples_mhz"]) == 48
    assert clock_input_two["samples_mhz"][47] == 2164.03
    assert not eg.effective_clock_comparison_passes(
        {
            "samples_mhz": clock_input_two["samples_mhz"],
            "tolerance_pct": clock_input_two["tolerance_pct"],
        },
        {"samples_mhz": clock_input_two["samples_mhz"]},
    )
    expected_two_profile = copy.deepcopy(profiles_two[1])
    expected_two_profile["effective_clock"]["tolerance_pct"] = 2.0
    expected_two_profile["tsc"] = {
        "raw_samples_mhz": [1800.0] * 5,
        "median_mhz": 1800.0,
        "clocks_per_us_int": 1800,
        "source": "clock_gettime-monotonic/rdtscp",
    }
    assert rejected_two["diagnostics"]["attestation_profile_sha256"] == (
        _canonical_json_sha256(expected_two_profile)
    )
    diagnostic_two = rejected_two["diagnostics"][
        "effective_clock_self_comparison"
    ]
    assert diagnostic_two["out_of_band_count"] == 1
    assert diagnostic_two["violations"] == [{
        "sample_index": 47,
        "sample_mhz": 2164.03,
        "direction": "above",
        "deviation_from_median_mhz": pytest.approx(63.03),
        "outside_by_mhz": pytest.approx(21.01),
    }]
    assert not (attempt_two / "calibration.json").exists()
    assert not (attempt_two / "calibration.md").exists()
    assert not (attempt_two / "window-probes.json").exists()
    assert not (attempt_two / "candidate.json").exists()
    assert not (attempt_two / "publish.json").exists()
    assert not (attempt_two / "published-self-comparison.json").exists()
    assert not registered_two.exists()

    literal_two = copy.deepcopy(expected_raw)
    literal_two["effective_clock"]["tolerance_pct"] = 2.0
    literal_two["effective_clock"]["samples_mhz"] = (
        [2101.0] * 47 + [2164.03]
    )
    assert not cli._effective_clock_self_comparison_passes({
        "effective_clock": copy.deepcopy(literal_two["effective_clock"]),
    })
    literal_two_comparisons = ea.compare_profiles(
        ea.normalize_profile(literal_two), observed, now_fn=lambda: 0,
    )
    assert next(
        item for item in literal_two_comparisons
        if item["field"] == "effective_clock.samples_mhz"
    )["verdict"] == "fail"
    assert not eg.effective_clock_comparison_passes(
        {
            "samples_mhz": [2101.0] * 48,
            "tolerance_pct": 2.0,
        },
        {"samples_mhz": [2101.0] * 47 + [2164.03]},
    )

    literal_two_path = three_root / "literal-two.json"
    literal_two_document = json.loads(published.read_text(encoding="utf-8"))
    literal_two_document["attestation_profile"]["effective_clock"][
        "tolerance_pct"
    ] = 2.0
    literal_two_path.write_text(
        json.dumps(literal_two_document), encoding="utf-8",
    )
    literal_two_contract = ec.ExecutionEnvironmentContract(
        env_tag=contract.env_tag,
        clocks_per_us=contract.clocks_per_us,
        numactl=(),
        attestation_mode="required",
        isolation_policy=contract.isolation_policy,
        calibration_ref=ec.CalibrationRef(
            path=literal_two_path.relative_to(three_root).as_posix(),
            sha256=hashlib.sha256(literal_two_path.read_bytes()).hexdigest(),
        ),
    )
    verified_two = ea.load_verified_calibration(literal_two_contract, three_root)
    receipt_two = copy.deepcopy(receipt_three)
    receipt_two["contract_sha256"] = literal_two_contract.contract_sha256
    receipt_two["attestation_profile_sha256"] = (
        verified_two.attestation_profile_sha256
    )
    receipt_clock = next(
        item for item in receipt_two["comparisons"]
        if item["field"] == "effective_clock.samples_mhz"
    )
    receipt_clock["expected"]["tolerance_pct"] = 2.0
    assert not eg.receipt_matches_contract(
        receipt_two,
        env_tag=literal_two_contract.env_tag,
        contract_sha256=literal_two_contract.contract_sha256,
        attestation_mode="required",
        verified_calibration=verified_two,
    )

    # Loader equality の旧負例は帯幅 vector から独立に残す。
    monkeypatch.setattr(
        cli.effective_clock_policy, "EFFECTIVE_CLOCK_TOLERANCE_PCT", 3.0,
    )
    with pytest.raises(ea.AttestationError, match="current policy"):
        ea.load_verified_calibration(literal_two_contract, three_root)


@pytest.mark.parametrize("legacy_value", ["2.0", "100.0"])
def test_cli_rejects_legacy_tolerance_override_before_attempt(
        tmp_path, monkeypatch, legacy_value):
    with pytest.raises(SystemExit) as caught:
        _invoke(
            tmp_path, monkeypatch,
            extra_args=["--effective-clock-tolerance-pct", legacy_value],
        )
    assert caught.value.code == 2
    attempt = tmp_path / "output/env/test-env/calibration/attempts/123.server"
    registered = tmp_path / "output/env/test-env/calibration/registered"
    assert not attempt.exists()
    assert not registered.exists()


def test_cli_accepted_publish_is_content_addressed_and_duplicate_fatal(
        tmp_path, monkeypatch):
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)
    assert rc == 0
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    digest = hashlib.sha256(published[0].read_bytes()).hexdigest()
    assert published[0].name == f"calibration-{digest[:16]}.json"
    validate_calibration_v2(published[0].read_bytes())
    trace = json.loads((attempt / "publish.json").read_text(encoding="utf-8"))
    assert trace == {"method": "renameat2", "target": published[0].name}

    before = (attempt / "calibration.json").read_bytes()
    rc_existing, _, _ = _invoke(tmp_path, monkeypatch)
    assert rc_existing != 0
    assert (attempt / "calibration.json").read_bytes() == before

    # Same immutable attempt bytes, fresh staging: canonical name collision must reject.
    shutil.rmtree(attempt)
    rc2, attempt2, registered2 = _invoke(tmp_path, monkeypatch)
    assert rc2 != 0
    assert len(list(registered2.glob("calibration-*.json"))) == 1
    rejection = validate_calibration_v2((attempt2 / "calibration.json").read_bytes())
    assert rejection.quality.status == "rejected"
    assert any("publish-collision" in r for r in rejection.quality.reasons)
    assert not (attempt2 / "candidate.json").exists()


def test_cli_publish_falls_back_to_link_on_renameat2_einval(
        tmp_path, monkeypatch):
    def renameat2_einval(_source, _target):
        raise OSError(errno.EINVAL, "injected unsupported filesystem")

    monkeypatch.setattr(cli, "_renameat2_noreplace", renameat2_einval)
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)

    assert rc == 0
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    assert published[0].read_bytes() == (attempt / "calibration.json").read_bytes()
    trace = json.loads((attempt / "publish.json").read_text(encoding="utf-8"))
    assert trace == {"method": "link-unlink", "target": published[0].name}
    assert not list(registered.glob(".publish-*.tmp"))


def test_cli_link_fallback_rejects_existing_target(
        tmp_path, monkeypatch):
    def renameat2_einval(_source, _target):
        raise OSError(errno.EINVAL, "injected unsupported filesystem")

    monkeypatch.setattr(cli, "_renameat2_noreplace", renameat2_einval)
    rc, attempt, registered = _invoke(tmp_path, monkeypatch)
    assert rc == 0
    published = list(registered.glob("calibration-*.json"))
    assert len(published) == 1
    published_before = published[0].read_bytes()

    shutil.rmtree(attempt)
    rc2, attempt2, registered2 = _invoke(tmp_path, monkeypatch)

    assert rc2 != 0
    assert list(registered2.glob("calibration-*.json")) == published
    assert published[0].read_bytes() == published_before
    rejection = validate_calibration_v2((attempt2 / "calibration.json").read_bytes())
    assert rejection.quality.status == "rejected"
    assert any("publish-collision" in reason for reason in rejection.quality.reasons)
    assert not (attempt2 / "publish.json").exists()
    assert not list(registered2.glob(".publish-*.tmp"))


def _perf_receipt(tmp_path, *, probe_error=False):
    from orchestrator.calibrator.perf_preflight import probe_perf_availability

    receipt = probe_perf_availability(
        subprocess_runner=lambda *a, **kw: _Completed(
            returncode=-15 if probe_error else 2,
        ),
    )
    path = tmp_path / "perf-preflight-input.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return path, receipt


def _three_point_reservation(receipt):
    receipt["walltime"]["required_s"] = (
        cli.reservation_budget(1000, 4000, 2, 3)["required_s"]
        + receipt["walltime"]["reserve_s"]
    )
    receipt["qsub"]["elapstim_req_s"] = receipt["walltime"]["required_s"]


@pytest.mark.parametrize("ratio", [20, 50, 80])
def test_cli_no_perf_preserves_all_sweep_reps(tmp_path, monkeypatch, ratio):
    receipt_path, receipt = _perf_receipt(tmp_path)
    commands = []
    transitions = []
    results = []
    original = sweep._transition_calibration_observation_to_noise

    def observe(*args, **kwargs):
        transitions.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(sweep, "_transition_calibration_observation_to_noise", observe)

    def observe_calibrate(**kwargs):
        result = sweep.calibrate(**kwargs)
        results.append(result)
        return result

    def bench(argv, **kwargs):
        commands.append(argv)
        return _Completed(stdout="throughput[tps]:\t100\nmaxrss:\t4096 kB\n")

    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, calibrate_fn=observe_calibrate, bench_runner=bench,
        receipt_mutator=_three_point_reservation,
        extra_args=["--max-records", "4000", "--workload", f"ycsb_rratio={ratio}",
                    "--perf-preflight-json", str(receipt_path)],
    )
    # Observe before holdout_observation can reject a records=0 noise transition.
    assert transitions == []
    assert len(commands) == 6
    assert [next(a for a in cmd if a.startswith("-ycsb_tuple_num=")) for cmd in commands] == [
        "-ycsb_tuple_num=1000", "-ycsb_tuple_num=1000",
        "-ycsb_tuple_num=2000", "-ycsb_tuple_num=2000",
        "-ycsb_tuple_num=4000", "-ycsb_tuple_num=4000",
    ]
    assert all("perf" not in cmd for cmd in commands)
    assert len(results) == 1
    assert results[0].noise_floor is None
    for point in results[0].sweep:
        assert vars(point.counters) == {
            "llc_load_misses": None, "llc_loads": None,
            "instructions": None, "cycles": None, "raw": {},
        }
    assert rc == 1
    artifact = json.loads((attempt / "calibration.json").read_text())
    validate_calibration_v2(artifact)
    assert artifact["saturation"] is None
    assert artifact["noise_floor"]["throughputs"] == []
    assert artifact["quality"]["status"] == "rejected"
    assert artifact["host"]["perf"] == "unavailable"
    assert len(artifact["sweep"]) == 3
    for point in artifact["sweep"]:
        assert point["throughputs"] == [100.0, 100.0]
        assert point["throughput_median_tps"] == 100.0
        assert point["llc_load_misses"] is None
        assert point["llc_loads"] is None
        assert point["llc_miss_rate"] is None
    assert json.loads((attempt / "perf-preflight.json").read_text()) == receipt
    assert not registered.exists()


@pytest.mark.parametrize("failure,reason", [
    ("maxrss", "rep1/2 missing required metrics at records=1000: maxrss"),
    ("throughput", "rep1/2 missing required metrics at records=1000: throughput"),
    ("rc", "rep1/2 fatal at records=1000 threads=2: RuntimeError: ccbench failed. rc=7"),
], ids=["maxrss", "throughput", "rc"])
def test_cli_no_perf_fatal_stops_at_bad_rep(tmp_path, monkeypatch, failure, reason):
    receipt_path, _ = _perf_receipt(tmp_path)
    commands = []

    def bench(argv, **kwargs):
        commands.append(argv)
        bad = len(commands) == 2
        stdout = ""
        if not (bad and failure == "throughput"):
            stdout += "throughput[tps]:\t100\n"
        if not (bad and failure == "maxrss"):
            stdout += "maxrss:\t4096 kB\n"
        return _Completed(returncode=7 if bad and failure == "rc" else 0, stdout=stdout)

    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, calibrate_fn=sweep.calibrate, bench_runner=bench,
        receipt_mutator=_three_point_reservation,
        extra_args=["--max-records", "4000", "--workload", "ycsb_rratio=80",
                    "--perf-preflight-json", str(receipt_path)],
    )
    assert len(commands) == 2
    assert all("-ycsb_tuple_num=1000" in cmd for cmd in commands)
    assert rc == 1
    rejection = json.loads((attempt / "rejection.json").read_text())
    assert rejection["quality"]["status"] == "rejected"
    assert any(reason in item for item in rejection["quality"]["reasons"])
    assert not (attempt / "calibration.json").exists()
    assert not registered.exists()


def test_cli_perf_probe_error_stops_before_calibrate(tmp_path, monkeypatch):
    receipt_path, receipt = _perf_receipt(tmp_path, probe_error=True)
    calls = []
    original = sweep.calibrate

    def observe(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    rc, attempt, registered = _invoke(
        tmp_path, monkeypatch, calibrate_fn=observe,
        extra_args=["--perf-preflight-json", str(receipt_path)],
    )
    assert calls == []
    assert rc == 1
    assert json.loads((attempt / "perf-preflight.json").read_text()) == receipt
    rejection = json.loads((attempt / "rejection.json").read_text())
    assert any("PerfPreflightError" in item and "probe-signal" in item
               for item in rejection["quality"]["reasons"])
    assert not registered.exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
