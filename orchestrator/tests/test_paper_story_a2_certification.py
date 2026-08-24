import base64
import copy
import hashlib
import inspect
import json
import socket
import time
from pathlib import Path

import pytest

from orchestrator.campaign import buildcache, loop
from orchestrator.campaign import campaign_lock, env_contract, ident, reservation, wal
from orchestrator.campaign import paper_story_a2_certification as A2
from orchestrator.campaign.model import (
    CampaignConfig,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
    WalRecord,
)
from orchestrator.calibrator.runner import PERF_EVENTS
from orchestrator.campaign.pipeline import (
    LEGACY_TAG,
    PERFORMANCE_TAG,
    PerfConfig,
    VERIFY_LEGACY_PLUS_PERFORMANCE,
    VERIFY_LEGACY_PLUS_S2,
    performance_correctness_workload,
    s2_correctness_workload,
    variant_id,
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


def _verify_wal_payload(tag, build_attempt_id):
    return {
        "build_attempt_id": build_attempt_id,
        "verdict": "serializable",
        "certified": True,
        "commit_witness": {
            "commit_counts": 11,
            "batch_commit_counts": 0,
        },
        "anomalies": 0,
        "workload": {"tag": tag},
    }


def _campaign_lock_text(policy, workload_id, attempt_id):
    expected = A2.campaign_preimage(
        policy, workload_id, attempt_id, CURRENT_PIN)
    observed = {
        **expected,
        ident.ADMISSION_POLICY_SEARCH_KEY: {"fixture": "producer-shaped"},
    }
    identity = {
        "spec_content": A2._canonical_json(expected).decode("ascii"),
        "ccbench_commit": CURRENT_PIN,
        "search_tag": policy.study + "-" + workload_id,
        "search_config": observed,
        "trial": attempt_id,
    }
    identity_preimage = json.dumps(
        identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    authority = {
        "environment_contract_sha256": "a" * 64,
        "activation_serial": 1,
        "activation_state_sha256": "b" * 64,
        "contract_loader_commit": "c" * 40,
        "contract_loader_blob_sha256s": {
            path: "d" * 64
            for path in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        },
    }
    return campaign_lock.encode_campaign_lock_v2(identity_preimage, authority)


def _positive_results(policy, attempt_root, *, adopted_gain=1.1):
    results = []
    contract = env_contract.lookup("pegasus")
    toolchain = {
        "cc": {
            "requested": "gcc", "realpath": "/usr/bin/gcc",
            "version_first_line": "gcc fixture",
        },
        "cxx": {
            "requested": "g++", "realpath": "/usr/bin/g++",
            "version_first_line": "g++ fixture",
        },
        "cmake": {
            "requested": "cmake", "realpath": "/usr/bin/cmake",
            "version_first_line": "cmake fixture",
        },
    }
    for workload_id in ("rr5", "rr50"):
        lock_text = _campaign_lock_text(
            policy, workload_id, attempt_root.name)
        identity = campaign_lock.decode_campaign_lock(lock_text).identity
        cfg = CampaignConfig(
            spec_slug="paper-story-a2-" + workload_id,
            search_tag=policy.study + "-" + workload_id,
            spec_content=identity["spec_content"],
            ccbench_commit=CURRENT_PIN,
            search_config=identity["search_config"],
            trial=attempt_root.name,
        )
        layout_root = attempt_root / "campaigns" / str(ident.campaign_id(cfg))
        runs = layout_root / "runs"
        runs.mkdir(parents=True)
        (layout_root / "campaign.lock").write_text(
            lock_text,
            encoding="utf-8",
        )
        records = []
        cells = [cell for cell in policy.cells if cell.workload_id == workload_id]
        for cell_index, cell in enumerate(cells):
            build_dir = attempt_root / "build" / cell.cell_id
            binary = (
                build_dir / "cc" / "SILO" / "ycsb_SILO.exe")
            binary.parent.mkdir(parents=True)
            binary.write_bytes(("binary:" + cell.cell_id).encode("ascii"))
            perf_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
            trace_sha = hashlib.sha256(
                ("trace:" + cell.cell_id).encode("ascii")).hexdigest()
            configure, build = buildcache._v2_commands(
                A2._genome_for_cell(policy, cell), False, "/source",
                str(build_dir), toolchain, jobs=48,
                dependency_prefix="/pinned/dependencies",
            )
            run_flags = [
                f"-thread_num={cell.perf['threads']}",
                f"-ycsb_tuple_num={cell.perf['records']}",
                f"-extime={cell.perf['extime']}",
                f"-clocks_per_us={contract.clocks_per_us}",
            ] + [
                f"-{key}={value}" for key, value in cell.perf["workload"].items()
            ]
            run = (
                list(contract.numactl)
                + ["perf", "stat", "-e", ",".join(PERF_EVENTS), "--", str(binary)]
                + run_flags
            )
            build_attempt_id = "build-" + cell.cell_id
            genome = A2._genome_for_cell(policy, cell)
            variant = variant_id(genome)
            value = 100.0 * (
                adopted_gain if cell.role == "adopted" else 1.0)
            samples = [value - 2, value - 1, value, value + 1, value + 2]
            payloads = [
                (STAGE_BUILD_START, {
                    "build_attempt_id": build_attempt_id,
                    "genome": genome.canonical(),
                }),
                (STAGE_BUILD_DONE, {
                    "build_attempt_id": build_attempt_id,
                    "trace_bin_sha256": trace_sha,
                    "perf_bin_sha256": perf_sha,
                    "perf_configure_cmd": " ".join(configure),
                    "perf_build_cmd": " ".join(build),
                    "toolchain": toolchain,
                }),
                (STAGE_VERIFY_DONE, _verify_wal_payload(
                    LEGACY_TAG, build_attempt_id)),
            ]
            payloads.extend(
                (STAGE_VERIFY_DONE, _verify_wal_payload(
                    PERFORMANCE_TAG, build_attempt_id))
                for _ in range(cell.perf["reps"])
            )
            payloads.extend([
                (STAGE_BENCH_DONE, {
                    "build_attempt_id": build_attempt_id,
                    "run_cmd": " ".join(run),
                    "tps": samples,
                    "unstable": False,
                    "rep_notes": [],
                }),
                (STAGE_COMMIT, {"build_attempt_id": build_attempt_id}),
            ])
            records.extend(
                WalRecord(
                    variant=variant, stage=stage, env_tag="pegasus",
                    ts=float(cell_index + offset + 1), payload=payload,
                )
                for offset, (stage, payload) in enumerate(payloads)
            )
        wal_path = runs / "wal.jsonl"
        wal_path.write_text(
            "".join(wal._record_to_line(record) + "\n" for record in records),
            encoding="utf-8",
        )
        for cell in cells:
            results.append(A2._raw_cell_from_wal(
                policy, cell,
                result=type("Result", (), {
                    "variant": variant_id(A2._genome_for_cell(policy, cell))})(),
                layout_root=str(layout_root), attempt_id=attempt_root.name,
                current_pin=CURRENT_PIN,
            ))
    return [
        next(raw for raw in results if raw["cell_id"] == cell.cell_id)
        for cell in policy.cells
    ]


def _raw_cell(policy, cell, root, *, adopted_gain=1.1):
    return next(
        raw for raw in _positive_results(
            policy, root, adopted_gain=adopted_gain)
        if raw["cell_id"] == cell.cell_id
    )


def _write_receipt_bundle(
        policy, attempt_root, *, driver_rc=0, claim_manifest=True,
        terminal_reason="scheduler-end-state"):
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
    repo_root = A2.POLICY_PATH.parents[2]
    job_body = repo_root / policy.document["scheduler"]["job_body"]
    qsub_environment = {
        "IZANAGI_A2_ATTEMPT_ROOT": str(attempt_root),
        "IZANAGI_A2_EXPECTED_HEAD": SOURCE_COMMIT,
        "IZANAGI_A2_CURRENT_PIN": CURRENT_PIN,
        "IZANAGI_A2_CCBENCH_ROOT": "/pinned/ccbench",
        "IZANAGI_A2_REPO_ROOT": str(repo_root),
        "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE": "/pinned/deps",
    }
    variable_arg = ",".join(
        f"{key}={value}" for key, value in qsub_environment.items())
    allocation_stdout = attempt_root / "scheduler" / "allocation-qstat.stdout"
    allocation_stderr = attempt_root / "scheduler" / "allocation-qstat.stderr"
    allocation_stdout.write_text(
        "Request ID: 12345.nqsv\nStarted Request Time = now\n"
        "(Per-Req) Elapse Time Limit = Max: 21600S\n",
        encoding="utf-8",
    )
    allocation_stderr.write_text("", encoding="utf-8")
    started = int(time.time()) - 1
    reservation_environment = {
        "IZANAGI_RESERVATION_JOB_ID": request_id,
        "IZANAGI_RESERVATION_REQUESTED_S": "21600",
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + 21600),
        "IZANAGI_RESERVATION_HOST": "bnode001",
        "IZANAGI_RESERVATION_BOOT_ID": Path(
            "/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
        "IZANAGI_RESERVATION_SCRIPT_SHA256": hashlib.sha256(
            job_body.read_bytes()).hexdigest(),
        "IZANAGI_RESERVATION_NONCE": request_id,
    }
    reservation_result = attempt_root / "reservation.json"
    A2.write_json_x(reservation_result, {
        "schema_version": A2.RESERVATION_RESULT_SCHEMA,
        "environment": reservation_environment,
        "allocation_qstat_stdout": log_record(allocation_stdout),
        "allocation_qstat_stderr": log_record(allocation_stderr),
    })
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
            "-l", "elapstim_req=06:00:00", "-N", "paper-a2-cert",
            "-v", variable_arg,
            "-o", str(stdout_path), "-e", str(stderr_path),
            str(job_body),
        ],
        "submission_cwd": str(repo_root),
        "qsub_environment": qsub_environment,
        "job_body_sha256": hashlib.sha256(job_body.read_bytes()).hexdigest(),
        "qsub_stdout": "Request 12345.nqsv submitted\n",
        "qsub_stderr": "",
        "qsub_returncode": 0,
        "request_id": request_id,
        "qstat_visibility": {
            "observed": True,
            "request_id": request_id,
            "argv": ["qstat", "-f", request_id],
            "returncode": 0,
            "stdout": "Request ID: 12345.nqsv\nRequest State = RUN\n",
            "stderr": "",
        },
    }
    submission_path = A2.record_submission_receipt(
        policy, attempt_root, CURRENT_PIN, submission)
    compute_result = attempt_root / "compute-result.json"
    A2.write_json_x(compute_result, {
        "schema_version": A2.COMPUTE_RESULT_SCHEMA,
        "driver_rc": driver_rc,
        "pbs_jobid": request_id,
        "current_pin": CURRENT_PIN,
    })
    terminal_stdout = (
        "Request ID: 12345.nqsv\nRequest State = EXT\n"
        if terminal_reason == "scheduler-end-state" else ""
    )
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
            "stdout": terminal_stdout,
            "stderr": "",
            "reason": terminal_reason,
        },
        "driver_rc": driver_rc,
        "compute_result": str(compute_result),
        "compute_result_sha256": hashlib.sha256(
            compute_result.read_bytes()).hexdigest(),
        "reservation_result": str(reservation_result),
        "reservation_result_sha256": hashlib.sha256(
            reservation_result.read_bytes()).hexdigest(),
        "raw_result_manifest": (
            str(manifest_path) if driver_rc == 0 and claim_manifest else None),
        "raw_result_manifest_sha256": (
            hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            if driver_rc == 0 and claim_manifest else None),
        "scheduler_stdout": log_record(stdout_path),
        "scheduler_stderr": log_record(stderr_path),
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
    assert policy.document["trace0_cmake_argv"] == {
        "configure": {
            "source_option": "-S",
            "build_directory_option": "-B",
            "fixed_arguments": [
                "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
            ],
            "toolchain_arguments": [
                {"role": "cc", "prefix": "-DCMAKE_C_COMPILER="},
                {"role": "cxx", "prefix": "-DCMAKE_CXX_COMPILER="},
            ],
            "dependency_prefix_argument": "-DCMAKE_PREFIX_PATH=",
            "controlled_define_argument": "-D",
        },
        "build": {
            "subcommand": "--build",
            "target_option": "--target",
            "target_prefix": "ycsb_",
            "target_suffix": ".exe",
            "jobs_option": "-j",
        },
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
    assert performance_correctness_workload(perf).reps == 5
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
    changed_perf = copy.deepcopy(perf)
    changed_perf.records = 200
    with pytest.raises(A2.CertificationError, match="PerfConfig"):
        A2.validate_campaign_binding(
            policy, "rr5", "attempt-1", CURRENT_PIN, expected, changed_perf)


def test_m4_full_scale_verify_is_required_for_cell_completion(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m4")
    results = _positive_results(policy, root)
    results[0]["correctness"].pop(PERFORMANCE_TAG)
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="123.nqsv", _test_token=A2._COLLECT_TEST_TOKEN)
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
        results[-1]["cell_id"] = "rr95-extra"
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
    anomaly["correctness"][PERFORMANCE_TAG][0] = {
        **anomaly["correctness"][PERFORMANCE_TAG][0],
        "status": "anomaly",
        "certified": False,
        "verdict": "non-serializable",
        "anomalies": [{"cycle": ["t1", "t2"]}],
    }
    anomaly["correctness"][PERFORMANCE_TAG] = [
        anomaly["correctness"][PERFORMANCE_TAG][0]]
    anomaly["trace0_evidence"] = None
    anomaly["performance"] = {
        "status": "indeterminate", "reason": "verify-reject"}
    results[1]["correctness"].pop(PERFORMANCE_TAG)
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="123.nqsv", _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["status"] == "reject"
    assert A2.driver_rc(report) == 0

    root2 = A2.create_attempt_root(policy, "attempt-perf-incomplete")
    results2 = _positive_results(policy, root2)
    results2[0]["performance"]["samples_tps"].pop()
    report2 = A2.collect_results(
        policy, results2, attempt_id=root2.name, current_pin=CURRENT_PIN,
        request_id="124.nqsv", _test_token=A2._COLLECT_TEST_TOKEN)
    assert report2["status"] == "performance-indeterminate"
    assert A2.driver_rc(report2) != 0


@pytest.mark.parametrize("mutation", ("map", "argv"))
def test_m8_controlled_define_map_and_argv_are_independent_gates(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m8")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    if mutation == "map":
        evidence["controlled_defines"]["CCBENCH_UNEXPECTED"] = "1"
    else:
        evidence["configure_argv"].append("-DCCBENCH_UNEXPECTED=1")
    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


def test_m9_run_argv_zero_must_be_the_canonical_binary(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m9")
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    decoy = root / "decoy"
    decoy.write_bytes(b"decoy")
    binary_index = evidence["run_argv"].index("--") + 1
    evidence["run_argv"][binary_index] = str(decoy)
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
    assert "scheduler_stdout" not in submission
    assert "scheduler_stderr" not in submission
    assert "scheduler_stdout" in evidence["completion"]
    assert "scheduler_stderr" in evidence["completion"]
    binding = reservation.read_binding(evidence["reservation_result"]["environment"])
    assert binding.job_id == "12345.nqsv"
    assert binding.deadline_epoch == binding.scheduler_started_epoch + 21600
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


@pytest.mark.parametrize("mutation", ("extra-env", "nodes", "job-body"))
def test_submission_argv_environment_nodes_and_job_body_are_exact(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-" + mutation, CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    mutant = copy.deepcopy(submission)
    if mutation == "extra-env":
        mutant["qsub_environment"]["PYTHONPATH"] = "/tmp/decoy"
        mutant["qsub_argv"][12] += ",PYTHONPATH=/tmp/decoy"
    elif mutation == "nodes":
        mutant["qsub_argv"][6] = "2"
    else:
        decoy = root / "decoy" / "paper_story_a2_certification.sh"
        decoy.parent.mkdir()
        decoy.write_bytes(
            (A2.POLICY_PATH.parents[2]
             / policy.document["scheduler"]["job_body"]).read_bytes())
        mutant["qsub_argv"][-1] = str(decoy)
        mutant["job_body_sha256"] = hashlib.sha256(decoy.read_bytes()).hexdigest()
    with pytest.raises(A2.CertificationError):
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
    materialized = json.loads(
        (destination / "certification.json").read_text(encoding="utf-8"))
    assert base64.b64decode(materialized["policy_bytes_base64"]) == policy.raw_bytes


def test_m12_attempt_root_must_be_direct_child_of_pinned_durable_base(tmp_path):
    policy = _policy(tmp_path)
    outside = tmp_path / "arbitrary-repo-external" / "attempt"
    outside.mkdir(parents=True)
    with pytest.raises(A2.CertificationError, match="pinned durable base"):
        A2.validate_attempt_root(policy, outside)


def test_m12_durable_base_rejects_symlinked_ancestor(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    document = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    document["durable_measurement_base"] = str(alias / "a2")
    path = tmp_path / "symlink-policy.json"
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    policy = A2.load_policy(path)
    with pytest.raises(A2.CertificationError, match="symlink"):
        A2.create_attempt_root(policy, "attempt-symlink")


def test_correctness_requires_every_ratified_repetition(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-repetitions")
    results = _positive_results(policy, root)
    assert len(results[0]["correctness"][PERFORMANCE_TAG]) == 5
    results[0]["correctness"][PERFORMANCE_TAG].pop()
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="reps.nqsv", _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["cells"][0]["correctness"]["status"] == "indeterminate"
    assert report["status"] == "indeterminate"


def test_nonfinite_json_and_samples_are_fail_closed(tmp_path):
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"sample":NaN}\n', encoding="utf-8")
    with pytest.raises(A2.CertificationError, match="non-finite"):
        A2._read_json(nonfinite)

    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-infinity")
    results = _positive_results(policy, root)
    results[0]["performance"]["samples_tps"][0] = float("inf")
    report = A2.collect_results(
        policy, results, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_id="finite.nqsv", _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["status"] == "performance-indeterminate"
    assert report["effects"] == {"rr50": pytest.approx(0.1)}


@pytest.mark.parametrize("driver_rc,claim_manifest", ((7, False), (0, False)))
def test_collector_never_calls_positive_path_for_failed_or_manifestless_compute(
        tmp_path, monkeypatch, driver_rc, claim_manifest):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, f"attempt-collector-{driver_rc}-{int(claim_manifest)}", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(
        policy, root, driver_rc=driver_rc, claim_manifest=claim_manifest)
    monkeypatch.setattr(A2, "load_policy", lambda: policy)
    positive_calls = []
    monkeypatch.setattr(
        A2, "collect_results",
        lambda *args, **kwargs: positive_calls.append((args, kwargs)),
    )
    captured = {}

    def materialize(_policy, report, _evidence, *, repo_root):
        captured.update(report)
        return Path(repo_root) / "captured"

    monkeypatch.setattr(A2, "materialize", materialize)
    args = type("Args", (), {
        "acquisition_receipt": str(acquisition),
        "current_pin": CURRENT_PIN,
        "attempt_root": str(root),
        "repo_root": str(tmp_path),
    })()
    assert A2._collect_command(args) == 2
    assert positive_calls == []
    assert captured["status"] == "indeterminate"


def test_completion_driver_rc_request_and_pin_are_bound_to_compute_result(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-compute-binding", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    compute = root / "compute-result.json"
    compute.write_text(
        json.dumps({
            "schema_version": A2.COMPUTE_RESULT_SCHEMA,
            "driver_rc": 0,
            "pbs_jobid": "different.nqsv",
            "current_pin": CURRENT_PIN,
        }) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(A2.CertificationError, match="compute result"):
        A2.validate_acquisition_bundle(
            policy, acquisition, current_pin=CURRENT_PIN)


@pytest.mark.parametrize(
    "terminal_reason",
    ("scheduler-end-state", "request-disappeared-after-visibility"),
)
def test_completion_accepts_both_canonical_terminal_observations(
        tmp_path, terminal_reason):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-terminal-" + terminal_reason, CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(
        policy, root, terminal_reason=terminal_reason)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["raw_manifest_valid"] is True


def test_raw_manifest_binds_campaign_lock_and_wal_and_freezes_raw_bytes(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-frozen", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert len(evidence["raw_files"]) == 8
    raw_path = root / "raw" / "rr5-stock.json"
    raw_path.write_text('{"tampered":true}\n', encoding="utf-8")
    report = A2.collect_results(
        policy, evidence["raw_results"], attempt_id=root.name,
        current_pin=CURRENT_PIN, request_id=evidence["request_id"],
        frozen_files=evidence["raw_files"], attempt_root=root)
    assert report["status"] == "observed-positive"
    assert report["independent_observation_limits"]["correctness_run_argv"] \
        == "not-recorded-by-existing-pipeline"


def test_changed_campaign_wal_invalidates_the_manifest_bundle(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-wal-change", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    raw, _ = A2._read_json(root / "raw" / "rr5-stock.json")
    wal_path = Path(raw["campaign_evidence"]["wal_path"])
    with wal_path.open("ab") as stream:
        stream.write(b"{}\n")
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert evidence["raw_manifest_valid"] is False
    assert "hash mismatch" in evidence["raw_manifest_reason"]


def test_cli_has_no_policy_injection_surface():
    with pytest.raises(SystemExit):
        A2._parser().parse_args(["--policy", "/tmp/alternate.json", "preregister"])


def test_official_run_observes_and_passes_current_toolchain_manifest():
    source = inspect.getsource(A2.run_workload)
    observed = "buildcache.observed_toolchain_manifest("
    passed = "expected_toolchain_manifest=expected_toolchain_manifest"
    assert observed in source and passed in source
    assert source.index(observed) < source.index("summary = run_campaign(")


def test_pipeline_runs_correctness_workload_repetitions_without_new_wal_fields():
    source = inspect.getsource(
        __import__(
            "orchestrator.campaign.pipeline", fromlist=["evaluate"]).evaluate)
    assert "for _repetition in range(workload.reps)" in source
    assert "verification_receipt_tags.extend([tag] * workload.reps)" in source


@pytest.mark.parametrize("mutation", (
    "separated-define", "duplicate-configure-token", "unknown-configure-token",
    "build-subcommand", "unknown-build-token", "unknown-run-flag",
    "clocks-per-us",
))
def test_trace0_argv_closed_grammar_rejects_unconsumed_tokens(tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-argv-" + mutation)
    raw = _raw_cell(policy, policy.cells[0], root)
    evidence = raw["trace0_evidence"]
    if mutation == "separated-define":
        evidence["configure_argv"].extend(["-D", "CCBENCH_TRACE=0"])
    elif mutation == "duplicate-configure-token":
        evidence["configure_argv"].append("-DENABLE_SANITIZER=OFF")
    elif mutation == "unknown-configure-token":
        evidence["configure_argv"].append("-DUNKNOWN=1")
    elif mutation == "build-subcommand":
        evidence["build_argv"][1] = "--install"
    elif mutation == "unknown-build-token":
        evidence["build_argv"].append("--verbose")
    elif mutation == "unknown-run-flag":
        evidence["run_argv"].append("-unknown_flag=1")
    else:
        clock_index = next(
            index for index, token in enumerate(evidence["run_argv"])
            if token.startswith("-clocks_per_us="))
        evidence["run_argv"][clock_index] = "-clocks_per_us=1"
    with pytest.raises(A2.CertificationError):
        A2.validate_trace0_evidence(
            policy, raw["cell_id"], root.name, CURRENT_PIN, evidence)


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


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
