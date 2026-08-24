import copy
import hashlib
import inspect
import json
import socket
from pathlib import Path

import pytest

from orchestrator.campaign import loop
from orchestrator.campaign import paper_story_a2_certification as A2
from orchestrator.campaign.model import CampaignConfig
from orchestrator.campaign.pipeline import (
    LEGACY_TAG,
    PERFORMANCE_TAG,
    PerfConfig,
    VERIFY_LEGACY_PLUS_PERFORMANCE,
    VERIFY_LEGACY_PLUS_S2,
    performance_correctness_workload,
    s2_correctness_workload,
)


CURRENT_PIN = "1" * 40
SOURCE_COMMIT = "2" * 40


def _policy(tmp_path):
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(tmp_path / "durable-a2")
    document["tracked_destination"] = (
        "output/insights/2026-08-24_paper-story-a2-certification")
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return A2.load_policy(path)


def _campaign_cfg(mode):
    search = {} if mode is None else {"verify": mode}
    return CampaignConfig(
        spec_slug="a2-test", search_tag="a2-test", spec_content="a2",
        ccbench_commit=CURRENT_PIN, search_config=search,
    )


def _pass_verify(policy, cell, tag, build_attempt_id, trace_sha):
    return {
        "tag": tag,
        "status": "pass",
        "trace_enabled": True,
        "build_attempt_id": build_attempt_id,
        "workload_flags": A2._expected_verify_flags(policy, cell, tag),
        "trace_binary_sha256": trace_sha,
        "certified": True,
        "integrity": "ok",
        "verdict": "serializable",
        "commit_witness": {
            "commit_counts": 11,
            "batch_commit_counts": 0,
        },
    }


def _raw_cell(policy, cell, root, *, adopted_gain=1.1):
    build_dir = root / "build" / cell.cell_id
    build_dir.mkdir(parents=True)
    binary = build_dir / "ycsb_SILO.exe"
    binary.write_bytes(("binary:" + cell.cell_id).encode("ascii"))
    perf_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    trace_sha = hashlib.sha256(("trace:" + cell.cell_id).encode("ascii")).hexdigest()
    defines = A2.expected_controlled_defines(policy, cell.cell_id)
    configure = ["cmake", "-S", "/source", "-B", str(build_dir)] + [
        f"-D{key}={value}" for key, value in defines.items()
    ]
    build = ["cmake", "--build", str(build_dir)]
    run = [str(binary)] + [
        f"-{key}={value}" for key, value in
        A2._expected_verify_flags(policy, cell, PERFORMANCE_TAG).items()
    ]
    attempt_id = root.name
    build_attempt_id = "build-" + cell.cell_id
    stock = 100.0
    value = stock * (adopted_gain if cell.role == "adopted" else 1.0)
    samples = [value - 2, value - 1, value, value + 1, value + 2]
    return {
        "schema_version": A2.RAW_RESULT_SCHEMA,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "current_pin": CURRENT_PIN,
        "cell_id": cell.cell_id,
        "genome": dict(cell.genome),
        "campaign_preimage": A2.campaign_preimage(
            policy, cell.workload_id, attempt_id, CURRENT_PIN),
        "build_attempt_id": build_attempt_id,
        "build_evidence": {
            "source_commit": CURRENT_PIN,
            "trace_enabled_build": True,
            "performance_trace_disabled_build": True,
            "trace_bin_sha256": trace_sha,
            "perf_bin_sha256": perf_sha,
            "compile_out_evidence_scope": A2.COMPILE_OUT_SCOPE,
        },
        "correctness": {
            LEGACY_TAG: _pass_verify(
                policy, cell, LEGACY_TAG, build_attempt_id, trace_sha),
            PERFORMANCE_TAG: _pass_verify(
                policy, cell, PERFORMANCE_TAG, build_attempt_id, trace_sha),
        },
        "performance": {
            "status": "complete",
            "trace_enabled": False,
            "build_attempt_id": build_attempt_id,
            "workload": dict(cell.perf),
            "perf_bin_sha256": perf_sha,
            "samples_tps": samples,
            "unstable": False,
            "rep_notes": [],
        },
        "trace0_evidence": {
            "schema_version": A2.TRACE0_SCHEMA,
            "cell_id": cell.cell_id,
            "attempt_id": attempt_id,
            "current_pin": CURRENT_PIN,
            "source_commit": CURRENT_PIN,
            "controlled_defines": defines,
            "configure_argv": configure,
            "build_argv": build,
            "build_dir": str(build_dir),
            "run_argv": run,
            "perf_binary": str(binary),
            "perf_bin_sha256": perf_sha,
            "build_done": {
                "source_commit": CURRENT_PIN,
                "trace_bin_sha256": trace_sha,
                "perf_bin_sha256": perf_sha,
            },
            "compile_out_evidence_scope": A2.COMPILE_OUT_SCOPE,
        },
        "terminal": "commit",
        "abort": None,
    }


def _positive_results(policy, attempt_root):
    return [_raw_cell(policy, cell, attempt_root) for cell in policy.cells]


def _write_receipt_bundle(policy, attempt_root):
    raw_root = attempt_root / "raw"
    if not raw_root.exists():
        raw_root.mkdir()
        for result in _positive_results(policy, attempt_root):
            A2.write_json_x(raw_root / f"{result['cell_id']}.json", result)
    manifest_path = A2.finalize_raw_manifest(
        policy, attempt_root, CURRENT_PIN)
    request_id = "12345.nqsv"
    stdout_path = attempt_root / "scheduler" / "job.stdout"
    stderr_path = attempt_root / "scheduler" / "job.stderr"
    stdout_path.write_text("job output\n", encoding="utf-8")
    stderr_path.write_text(
        "Request ID: 12345.nqsv\nGroup Name: SFC\n"
        "Started Request Time: now\nEnded Request Time: later\nElapse: 1\n",
        encoding="utf-8",
    )
    log_record = lambda path: {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    submission = {
        "schema_version": A2.SUBMISSION_SCHEMA,
        "route": "direct-qsub",
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_root.name,
        "attempt_root": str(attempt_root),
        "source_commit": SOURCE_COMMIT,
        "current_pin": CURRENT_PIN,
        "submit_host": socket.gethostname(),
        "qsub_argv": [
            "qsub", "-A", "SFC", "-q", "gen_S", "-b", "1",
            "-l", "elapstim_req=06:00:00", "-N", "paper-a2",
            "-v", (
                f"IZANAGI_A2_ATTEMPT_ROOT={attempt_root},"
                f"IZANAGI_A2_EXPECTED_HEAD={SOURCE_COMMIT},"
                f"IZANAGI_A2_CURRENT_PIN={CURRENT_PIN},"
                "IZANAGI_A2_CCBENCH_ROOT=/pinned/ccbench,"
                "IZANAGI_A2_REPO_ROOT=/pinned/repo,"
                "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE=/pinned/deps,"
                "IZANAGI_RESERVATION_JOB_ID=12345.nqsv,"
                "IZANAGI_RESERVATION_HOST=bnode001,"
                "IZANAGI_RESERVATION_DEADLINE=999999"
            ),
            "-o", str(stdout_path), "-e", str(stderr_path),
            "tools/pegasus/paper_story_a2_certification.sh",
        ],
        "qsub_stdout": "Request 12345.nqsv submitted\n",
        "request_id": request_id,
        "qstat_visibility": {
            "observed": True,
            "request_id": request_id,
            "argv": ["qstat", "-f", request_id],
            "returncode": 0,
            "stdout": "Request ID: 12345.nqsv\nRequest State = RUN\n",
        },
        "scheduler_stdout": log_record(stdout_path),
        "scheduler_stderr": log_record(stderr_path),
    }
    submission_path = A2.record_submission_receipt(
        policy, attempt_root, CURRENT_PIN, submission)
    completion = {
        "schema_version": A2.COMPLETION_SCHEMA,
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_root.name,
        "attempt_root": str(attempt_root),
        "source_commit": SOURCE_COMMIT,
        "current_pin": CURRENT_PIN,
        "request_id": request_id,
        "terminal_observation": {
            "observed": True,
            "request_id": request_id,
            "argv": ["qstat", "-f", request_id],
            "returncode": 0,
            "state": "END",
            "stdout": "Request ID: 12345.nqsv\nRequest State = EXT\n",
        },
        "driver_rc": 0,
        "raw_result_manifest": str(manifest_path),
        "raw_result_manifest_sha256": hashlib.sha256(
            manifest_path.read_bytes()).hexdigest(),
        "scheduler_stdout_sha256": submission["scheduler_stdout"]["sha256"],
        "scheduler_stderr_sha256": submission["scheduler_stderr"]["sha256"],
    }
    A2.record_completion_receipt(
        policy, attempt_root, CURRENT_PIN, completion)
    acquisition_path = A2.record_acquisition_receipt(
        policy, attempt_root, CURRENT_PIN, request_id)
    return acquisition_path, submission


def test_policy_is_the_exact_literal_four_cell_protocol(tmp_path):
    policy = _policy(tmp_path)
    assert [(cell.cell_id, cell.workload_id, cell.role, dict(cell.genome))
            for cell in policy.cells] == [
        ("rr5-stock", "rr5", "stock", {"BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("rr5-fixed10", "rr5", "adopted", {"BACK_OFF": 1, "BACKOFF_FIXED": 10}),
        ("rr50-stock", "rr50", "stock", {"BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("rr50-fixed5", "rr50", "adopted", {"BACK_OFF": 1, "BACKOFF_FIXED": 5}),
    ]
    assert policy.cells[0].perf == {
        "records": 1_000_000,
        "threads": 48,
        "workload": {
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
        "extime": 3,
        "reps": 5,
    }
    assert policy.document["historical_reference"]["ccbench_commit"] == "6656e93"
    assert "never a current comparison value" in \
        policy.document["historical_reference"]["role"]
    assert policy.document["controlled_define_base"] == {
        "CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION": "1",
        "CCBENCH_NO_WAIT_OF_TICTOC": "0",
        "CCBENCH_WAL": "0",
        "CCBENCH_BACKOFF_NOINLINE": "0",
        "CCBENCH_TRACE": "0",
    }


def test_m1_closed_verify_mode_wires_performance_and_rejects_unknown():
    perf = PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    assert loop._closed_verify_workloads(_campaign_cfg(None), perf) is None
    assert loop._closed_verify_workloads(_campaign_cfg(LEGACY_TAG), perf) is None
    assert loop._closed_verify_workloads(
        _campaign_cfg(VERIFY_LEGACY_PLUS_S2), perf) == [
            ("s2", s2_correctness_workload())]
    matched = loop._closed_verify_workloads(
        _campaign_cfg(VERIFY_LEGACY_PLUS_PERFORMANCE), perf)
    assert matched == [(PERFORMANCE_TAG, performance_correctness_workload(perf))]
    with pytest.raises(ValueError, match="unsupported verify mode"):
        loop._closed_verify_workloads(_campaign_cfg("legacy+typo"), perf)
    source = inspect.getsource(loop.run_campaign)
    assert source.index("_closed_verify_workloads(cfg, perf)") \
        < source.index("_authorize_measurement(")


def test_m2_performance_constructor_is_exact_and_rejects_shrinkage():
    perf = PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    assert performance_correctness_workload(perf).flags == {
        "ycsb_tuple_num": "1000000", "thread_num": "48",
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
        "ycsb_rmw": "0", "ycsb_max_ope": "10", "extime": "3",
    }
    shrunk = copy.deepcopy(perf)
    shrunk.records = 200
    assert performance_correctness_workload(shrunk).flags["ycsb_tuple_num"] == "200"
    widened = copy.deepcopy(perf)
    widened.workload["ycsb_tuple_num"] = "200"
    with pytest.raises(ValueError, match="exact YCSB workload keys"):
        performance_correctness_workload(widened)


def test_m3_campaign_preimage_and_perfconfig_must_both_match(tmp_path):
    policy = _policy(tmp_path)
    cell = policy.cell("rr5-stock")
    expected = A2.campaign_preimage(policy, "rr5", "attempt-1", CURRENT_PIN)
    perf = A2.perf_config_for_cell(policy, cell.cell_id)
    A2.validate_campaign_binding(
        policy, "rr5", "attempt-1", CURRENT_PIN, expected, perf)
    changed = copy.deepcopy(expected)
    changed["workload"]["records"] = 200
    with pytest.raises(A2.CertificationError, match="preimage"):
        A2.validate_campaign_binding(
            policy, "rr5", "attempt-1", CURRENT_PIN, changed, perf)


def test_m4_full_scale_verify_is_required_for_cell_completion(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m4")
    results = _positive_results(policy, root)
    results[0]["correctness"].pop(PERFORMANCE_TAG)
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="123.nqsv")
    assert report["cells"][0]["correctness"]["status"] == "indeterminate"
    assert report["status"] == "indeterminate"


@pytest.mark.parametrize("mutation", ("missing", "extra", "duplicate", "cross-attempt"))
def test_m5_collector_rejects_non_exact_cell_sets(tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m5-" + mutation)
    results = _positive_results(policy, root)
    if mutation == "missing":
        results.pop()
    elif mutation == "extra":
        extra = copy.deepcopy(results[-1])
        extra["cell_id"] = "rr95-extra"
        results.append(extra)
    elif mutation == "duplicate":
        results[-1] = copy.deepcopy(results[0])
    else:
        results[-1]["attempt_id"] = "another-attempt"
    with pytest.raises(A2.CertificationError):
        A2.collect_results(
            policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
            request_id="123.nqsv")


def test_m6_positive_report_never_claims_global_minimality(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m6")
    report = A2.collect_results(
        policy, _positive_results(policy, root), attempt_id=root.name,
        current_pin=CURRENT_PIN, request_id="123.nqsv")
    assert report["status"] == "observed-positive"
    assert report["global_minimality_established"] is False
    assert report["smallest_observed_sufficient_in_this_two_point_protocol"] == "200/4"


def test_anomaly_is_determinate_reject_and_performance_incomplete_is_not_pass(
        tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-classification")
    results = _positive_results(policy, root)
    anomaly = results[0]
    anomaly["correctness"][PERFORMANCE_TAG] = {
        **anomaly["correctness"][PERFORMANCE_TAG],
        "status": "anomaly",
        "certified": False,
        "verdict": "non-serializable",
        "anomalies": [{"cycle": ["t1", "t2"]}],
    }
    anomaly["trace0_evidence"] = None
    anomaly["performance"] = {
        "status": "indeterminate", "reason": "verify-reject"}
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="123.nqsv")
    assert report["status"] == "reject"
    assert A2.driver_rc(report) == 0

    root2 = A2.create_attempt_root(policy, "attempt-perf-incomplete")
    results2 = _positive_results(policy, root2)
    results2[0]["performance"]["samples_tps"].pop()
    report2 = A2.collect_results(
        policy, results2, attempt_id=root2.name, current_pin=CURRENT_PIN,
        request_id="124.nqsv")
    assert report2["status"] == "performance-indeterminate"
    assert A2.driver_rc(report2) != 0


def test_m8_controlled_define_map_rejects_one_extra_ccbench_define(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m8")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    evidence["controlled_defines"]["CCBENCH_UNEXPECTED"] = "1"
    evidence["configure_argv"].append("-DCCBENCH_UNEXPECTED=1")
    with pytest.raises(A2.CertificationError, match="not exact"):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_m9_run_argv_zero_must_be_the_canonical_binary(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m9")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    decoy = root / "decoy"
    decoy.write_bytes(b"decoy")
    evidence["run_argv"] = [str(decoy), evidence["perf_binary"]]
    with pytest.raises(A2.CertificationError, match=r"argv\[0\]"):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_perf_sha_is_recomputed_from_binary_bytes(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-sha")
    raw = _raw_cell(policy, policy.cells[0], root)
    raw["trace0_evidence"]["perf_bin_sha256"] = "0" * 64
    with pytest.raises(A2.CertificationError, match="binary bytes"):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN,
            raw["trace0_evidence"])


def test_m10_full_submission_and_completion_receipts_are_cross_bound(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-m10", CURRENT_PIN)
    acquisition, submission = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["request_id"] == "12345.nqsv"
    with pytest.raises(FileExistsError):
        A2.record_submission_receipt(
            policy, root, CURRENT_PIN, submission)
    subset = {key: submission[key] for key in (
        "route", "study", "current_pin", "attempt_root", "request_id")}
    with pytest.raises(A2.CertificationError, match="missing required"):
        A2._validate_submission_receipt(
            policy, subset, root.name, root, CURRENT_PIN)


@pytest.mark.parametrize("missing", ("qsub_argv", "qstat_visibility"))
def test_m10_each_canonical_qsub_and_submit_observation_field_is_required(
        tmp_path, missing):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-m10-" + missing.replace("_", "-"), CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    mutant = copy.deepcopy(submission)
    mutant.pop(missing)
    with pytest.raises(A2.CertificationError, match="missing required"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_m11_materializer_stages_marker_before_single_noreplace_rename(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-m11", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = {
        "schema_version": A2.CERTIFICATION_SCHEMA,
        "attempt_id": root.name,
        "protocol_sha256": policy.protocol_sha256,
        "status": "reject",
    }
    repo = tmp_path / "repo"
    repo.mkdir()
    original = A2._rename_noreplace
    rename_calls = []

    def observed_rename(source, destination):
        rename_calls.append((source, destination))
        assert (source / "COMPLETE.json").is_file()
        assert (source / "certification.json").is_file()
        assert (source / "artifact-manifest.json").is_file()
        original(source, destination)

    monkeypatch.setattr(A2, "_rename_noreplace", observed_rename)
    destination = A2.materialize(policy, report, evidence, repo_root=repo)
    assert len(rename_calls) == 1
    assert (destination / "COMPLETE.json").is_file()
    assert sorted(path.name for path in destination.iterdir()) == [
        "COMPLETE.json", "acquisition-receipt.json", "artifact-manifest.json",
        "certification.json", "completion-receipt.json",
        "raw-manifest.json", "submission-receipt.json",
    ]


def test_m12_attempt_root_must_be_direct_child_of_pinned_durable_base(tmp_path):
    policy = _policy(tmp_path)
    outside = tmp_path / "arbitrary-repo-external" / "attempt"
    outside.mkdir(parents=True)
    with pytest.raises(A2.CertificationError, match="pinned durable base"):
        A2.validate_attempt_root(policy, outside)


def test_synthetic_pbs_free_preregister_through_analyze_positive(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "synthetic-positive", CURRENT_PIN)
    raw_root = root / "raw"
    raw_root.mkdir()
    results = _positive_results(policy, root)
    for result in results:
        A2.write_json_x(raw_root / f"{result['cell_id']}.json", result)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2.collect_results(
        policy, A2.load_raw_results(policy, root), attempt_id=root.name,
        current_pin=CURRENT_PIN, request_id=evidence["request_id"])
    repo = tmp_path / "repo"
    repo.mkdir()
    destination = A2.materialize(policy, report, evidence, repo_root=repo)
    assert A2.driver_rc(report) == 0
    assert report["status"] == "observed-positive"
    assert (destination / "COMPLETE.json").is_file()


def test_volatile_diagnostics_are_not_fixture_authority(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "volatile-diagnostics")
    first = _positive_results(policy, root)
    second = copy.deepcopy(first)
    for index, raw in enumerate(second):
        raw["diagnostics"] = {
            "working_tree_probe": "changed-" + str(index),
            "host_payload": {"free_bytes": index * 991},
        }
    report_a = A2.collect_results(
        policy, first, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="125.nqsv")
    report_b = A2.collect_results(
        policy, second, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="125.nqsv")
    assert report_a == report_b
