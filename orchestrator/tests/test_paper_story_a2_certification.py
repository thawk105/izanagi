import base64
import copy
import hashlib
import inspect
import json
import socket
import subprocess
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
QSTAT_VISIBILITY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "paper_story_a2"
    / "qstat-visibility-945411.stdout"
)
QSTAT_FANOUT_VISIBILITY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "paper_story_a2"
)
QSTAT_FANOUT_VISIBILITY_FIXTURES = {
    "rr5": QSTAT_FANOUT_VISIBILITY_FIXTURE
    / "qstat-visibility-fanout-945411.stdout",
    "rr50": QSTAT_FANOUT_VISIBILITY_FIXTURE
    / "qstat-visibility-fanout-945412.stdout",
}
NON_ACCEPTED_VISIBILITY_VOCABULARY = (
    ("Held", "outside the submission acceptance set"),
    ("Suspended", "state vocabulary is unknown"),
)


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
        job_root = attempt_root / "jobs" / workload_id
        for child in (job_root, job_root / "campaigns", job_root / "cache",
                      job_root / "scheduler"):
            child.mkdir(parents=True, exist_ok=True)
        campaign_id = str(ident.campaign_id(cfg))
        layout_root = job_root / "campaigns" / campaign_id
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
        claim_path = A2.raw_result_claim_path(
            policy, workload_id, attempt_root, campaign_id)
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(json.dumps({
            "campaign_identity": campaign_id,
            "protocol_digest": hashlib.sha256(
                ident.canonical_preimage(cfg).encode("utf-8")
            ).hexdigest(),
            "job_id": (
                "945411.nqsv" if workload_id == "rr5" else "945412.nqsv"),
            "host": "bnode001",
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(
                encoding="ascii").strip(),
            "pid": 123,
            "proc_starttime": 456,
            "created_utc": "2026-08-27T00:00:00+00:00",
        }, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
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
        terminal_reason="scheduler-end-state", record_completion=True):
    results = _positive_results(policy, attempt_root)
    for workload_id in A2.workload_ids(policy):
        raw_root = A2.workload_job_root(policy, attempt_root, workload_id) / "raw"
        if not raw_root.exists():
            raw_root.mkdir()
            for result in results:
                if policy.cell(result["cell_id"]).workload_id == workload_id:
                    A2.write_json_x(
                        raw_root / f"{result['cell_id']}.json", result)
    log_record = lambda path: {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    repo_root = A2.POLICY_PATH.parents[2]
    job_body = repo_root / policy.document["scheduler"]["job_body"]
    started = int(time.time()) - 1
    request_ids = {"rr5": "945411.nqsv", "rr50": "945412.nqsv"}
    submission_jobs = []
    completion_jobs = []
    driver_rcs = {
        "rr5": driver_rc,
        "rr50": 0,
    }
    for workload_id in A2.workload_ids(policy):
        request_id = request_ids[workload_id]
        job_root = A2.workload_job_root(policy, attempt_root, workload_id)
        stdout_path = job_root / "scheduler" / "job.stdout"
        stderr_path = job_root / "scheduler" / "job.stderr"
        stdout_path.write_text("job output\n", encoding="utf-8")
        stderr_path.write_text(
            f"Request ID: {request_id}\nGroup Name: SFC\n"
            "Started Request Time: now\nEnded Request Time: later\nElapse: 1\n",
            encoding="utf-8",
        )
        qsub_environment = {
            "IZANAGI_A2_ATTEMPT_ROOT": str(attempt_root),
            "IZANAGI_A2_WORKLOAD": workload_id,
            "IZANAGI_A2_EXPECTED_HEAD": SOURCE_COMMIT,
            "IZANAGI_A2_CURRENT_PIN": CURRENT_PIN,
            "IZANAGI_A2_CCBENCH_ROOT": "/pinned/ccbench",
            "IZANAGI_A2_REPO_ROOT": str(repo_root),
            "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE": "/pinned/deps",
        }
        variable_arg = ",".join(
            f"{key}={value}" for key, value in qsub_environment.items())
        submission_jobs.append({
            "workload": workload_id,
            "qsub_argv": [
                "qsub", "-A", "SFC", "-q", "gen_S", "-b", "1",
                "-l", "elapstim_req=06:00:00", "-N", "paper-a2-cert",
                "-v", variable_arg,
                "-o", str(stdout_path), "-e", str(stderr_path),
                str(job_body),
            ],
            "qsub_stdout": f"Request {request_id} submitted\n",
            "qsub_stderr": "",
            "qsub_returncode": 0,
            "request_id": request_id,
            "qstat_visibility": {
                "observed": True,
                "observed_at_utc": "2026-08-25T00:00:00Z",
                "request_id": request_id,
                "argv": ["qstat", "-f", request_id],
                "returncode": 0,
                "state": "QUE",
                "stdout": QSTAT_FANOUT_VISIBILITY_FIXTURES[workload_id].read_text(
                    encoding="utf-8"),
                "stderr": "",
            },
            "qsub_environment": qsub_environment,
        })
        allocation_stdout = job_root / "scheduler" / "allocation-qstat.stdout"
        allocation_stderr = job_root / "scheduler" / "allocation-qstat.stderr"
        allocation_stdout.write_text(
            f"Request ID: {request_id}\nStarted Request Time = now\n"
            "(Per-Req) Elapse Time Limit = Max: 21600S\n",
            encoding="utf-8",
        )
        allocation_stderr.write_text("", encoding="utf-8")
        reservation_environment = {
            "IZANAGI_RESERVATION_JOB_ID": request_id,
            "IZANAGI_RESERVATION_REQUESTED_S": "21600",
            "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
            "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + 21600),
            "IZANAGI_RESERVATION_HOST": "bnode001",
            "IZANAGI_RESERVATION_BOOT_ID": Path(
                "/proc/sys/kernel/random/boot_id").read_text(
                    encoding="ascii").strip(),
            "IZANAGI_RESERVATION_SCRIPT_SHA256": hashlib.sha256(
                job_body.read_bytes()).hexdigest(),
            "IZANAGI_RESERVATION_NONCE": request_id,
        }
        reservation_result = job_root / "reservation.json"
        A2.write_json_x(reservation_result, {
            "schema_version": A2.RESERVATION_RESULT_SCHEMA,
            "environment": reservation_environment,
            "allocation_qstat_stdout": log_record(allocation_stdout),
            "allocation_qstat_stderr": log_record(allocation_stderr),
        })
        compute_result = job_root / "compute-result.json"
        A2.write_json_x(compute_result, {
            "schema_version": A2.COMPUTE_RESULT_SCHEMA,
            "workload": workload_id,
            "driver_rc": driver_rcs[workload_id],
            "pbs_jobid": request_id,
            "current_pin": CURRENT_PIN,
        })
        terminal_stdout = (
            f"Request ID: {request_id}\nRequest State = EXT\n"
            if terminal_reason == "scheduler-end-state"
            else f"Batch Request: {request_id} does not exist on nqsv.\n"
        )
        completion_jobs.append({
            "workload": workload_id,
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
            "driver_rc": driver_rcs[workload_id],
            "compute_result": str(compute_result),
            "compute_result_sha256": hashlib.sha256(
                compute_result.read_bytes()).hexdigest(),
            "reservation_result": str(reservation_result),
            "reservation_result_sha256": hashlib.sha256(
                reservation_result.read_bytes()).hexdigest(),
            "scheduler_stdout": log_record(stdout_path),
            "scheduler_stderr": log_record(stderr_path),
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
        "submission_cwd": str(repo_root),
        "job_body_sha256": hashlib.sha256(job_body.read_bytes()).hexdigest(),
        "jobs": submission_jobs,
    }
    A2.record_submission_receipt(
        policy, attempt_root, CURRENT_PIN, submission)
    if not record_completion:
        return None, submission
    manifest_path = None
    if all(value == 0 for value in driver_rcs.values()) and claim_manifest:
        manifest_path = A2.finalize_raw_manifest(
            policy, attempt_root, CURRENT_PIN)
    completion = {
        "schema_version": A2.COMPLETION_SCHEMA,
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_root.name,
        "attempt_root": str(attempt_root),
        "source_commit": SOURCE_COMMIT,
        "current_pin": CURRENT_PIN,
        "jobs": completion_jobs,
        "raw_result_manifest": (
            str(manifest_path) if manifest_path is not None else None),
        "raw_result_manifest_sha256": (
            hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            if manifest_path is not None else None),
    }
    A2.record_completion_receipt(
        policy, attempt_root, CURRENT_PIN, completion)
    acquisition_path = A2.record_acquisition_receipt(
        policy, attempt_root, CURRENT_PIN)
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
    assert policy.document["certification_composition"] == {
        "campaign_unit": (
            "one independently environment-contracted campaign per workload"),
        "outer_certification": "logical conjunction in policy workload order",
    }
    original = json.loads(A2.POLICY_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(original)
    changed["certification_composition"]["outer_certification"] += " changed"
    original_sha = hashlib.sha256(
        A2._canonical_json(A2._protocol_preimage(original))).hexdigest()
    changed_sha = hashlib.sha256(
        A2._canonical_json(A2._protocol_preimage(changed))).hexdigest()
    assert original_sha != changed_sha
    decorative_original = dict(A2._protocol_preimage(original))
    decorative_changed = dict(A2._protocol_preimage(changed))
    decorative_original.pop("certification_composition")
    decorative_changed.pop("certification_composition")
    assert hashlib.sha256(A2._canonical_json(decorative_original)).hexdigest() == \
        hashlib.sha256(A2._canonical_json(decorative_changed)).hexdigest()


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
        request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
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
            request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"})


def test_m6_positive_report_never_claims_global_minimality(tmp_path):
    policy = _policy(tmp_path)
    root = A2.create_attempt_root(policy, "attempt-m6")
    report = A2.collect_results(
        policy, _positive_results(policy, root), attempt_id=root.name,
        current_pin=CURRENT_PIN,
        request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"})
    assert report["status"] == "observed-positive"
    assert report["global_minimality_established"] is False
    assert report["smallest_observed_sufficient_in_this_two_point_protocol"] is None


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
        request_ids={"rr5": "123.nqsv", "rr50": "124.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
    assert report["status"] == "reject"
    assert A2.driver_rc(report) == 0

    root2 = A2.create_attempt_root(policy, "attempt-perf-incomplete")
    results2 = _positive_results(policy, root2)
    results2[0]["performance"]["samples_tps"].pop()
    report2 = A2.collect_results(
        policy, results2, attempt_id=root2.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "124.nqsv", "rr50": "125.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
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
    canonical_binary = evidence["run_argv"][binary_index]
    expected_workload_flags = A2._run_workload_flags(
        evidence["run_argv"][binary_index:])
    evidence["run_argv"][binary_index] = str(decoy)
    evidence["run_argv"].insert(binary_index + 1, canonical_binary)
    assert evidence["run_argv"][binary_index] == str(decoy)
    assert canonical_binary in evidence["run_argv"][binary_index + 1:]
    assert A2._run_workload_flags(
        evidence["run_argv"][binary_index + 1:]) == expected_workload_flags
    with pytest.raises(A2.CertificationError, match=r"argv\[0\]"):
        A2._require_run_binary_at_position(
            evidence["run_argv"], binary_index, Path(canonical_binary))
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
    assert evidence["request_ids"] == {
        "rr5": "945411.nqsv", "rr50": "945412.nqsv"}
    assert "scheduler_stdout" not in submission
    assert "scheduler_stderr" not in submission
    assert "scheduler_stdout" in evidence["completion"]["jobs"][0]
    assert "scheduler_stderr" in evidence["completion"]["jobs"][0]
    binding = reservation.read_binding(
        evidence["reservation_results"]["rr5"]["environment"])
    assert binding.job_id == "945411.nqsv"
    assert binding.deadline_epoch == binding.scheduler_started_epoch + 21600
    with pytest.raises(FileExistsError):
        A2.record_submission_receipt(
            policy, root, CURRENT_PIN, submission)
    subset = {key: submission[key] for key in (
        "route", "study", "current_pin", "attempt_root", "jobs")}
    with pytest.raises(A2.CertificationError, match="missing required"):
        A2._validate_submission_receipt(
            policy, subset, root.name, root, CURRENT_PIN)

    coordinates = [
        {
            "workload": "rr5", "request_id": "101.nqsv",
            "scheduler_stdout_path": tmp_path / "rr5.stdout",
            "scheduler_stderr_path": tmp_path / "rr5.stderr",
        },
        {
            "workload": "rr50", "request_id": "102.nqsv",
            "scheduler_stdout_path": tmp_path / "rr50.stdout",
            "scheduler_stderr_path": tmp_path / "rr50.stderr",
        },
    ]
    A2._validate_group_coordinates(policy, coordinates)
    duplicate_request = copy.deepcopy(coordinates)
    duplicate_request[1]["request_id"] = duplicate_request[0]["request_id"]
    with pytest.raises(A2.CertificationError, match="request IDs must be distinct"):
        A2._validate_group_coordinates(policy, duplicate_request)
    with pytest.raises(A2.CertificationError, match="workload order"):
        A2._validate_group_coordinates(policy, list(reversed(coordinates)))

    qsub_calls = []
    original_precheck = A2.submission_ratification_precheck
    try:
        A2.submission_ratification_precheck = lambda: "ratified-fixture-digest"

        def runner(argv, **kwargs):
            qsub_calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0, "101.nqsv\n", "")

        assert A2.ratified_qsub(
            ["qsub", "job.sh"], runner=runner).returncode == 0

        def unratified():
            raise A2.CertificationError(
                "enforcement-source-closure-unratified")

        A2.submission_ratification_precheck = unratified
        with pytest.raises(A2.CertificationError, match="unratified"):
            A2.ratified_qsub(["qsub", "job.sh"], runner=runner)
        assert len(qsub_calls) == 1
    finally:
        A2.submission_ratification_precheck = original_precheck

    finish_root = A2.preregister_attempt(
        policy, "attempt-finish-group", CURRENT_PIN)
    _write_receipt_bundle(
        policy, finish_root, record_completion=False)
    try:
        A2.submission_ratification_precheck = lambda: "ratified-fixture-digest"

        def qstat(command, **kwargs):
            request_id = command[-1]
            return subprocess.CompletedProcess(
                command, 0,
                f"Request ID: {request_id}\nRequest State = EXT\n", "")

        completion_path, finish_acquisition = A2.finish_group(
            policy, finish_root, CURRENT_PIN, qstat_runner=qstat)
    finally:
        A2.submission_ratification_precheck = original_precheck
    assert completion_path == finish_root / "receipts" / "completion.json"
    finish_evidence = A2.validate_acquisition_bundle(
        policy, finish_acquisition, current_pin=CURRENT_PIN)
    assert finish_evidence["driver_rcs"] == {"rr5": 0, "rr50": 0}
    assert finish_evidence["raw_manifest_valid"] is True


@pytest.mark.parametrize("missing", ("qsub_argv", "qstat_visibility"))
def test_m10_each_canonical_qsub_and_submit_observation_field_is_required(
        tmp_path, missing):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-m10-" + missing.replace("_", "-"), CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0].pop(missing)
    with pytest.raises(A2.CertificationError, match="not exact"):
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
        mutant["jobs"][0]["qsub_environment"]["PYTHONPATH"] = "/tmp/decoy"
        mutant["jobs"][0]["qsub_argv"][12] += ",PYTHONPATH=/tmp/decoy"
    elif mutation == "nodes":
        mutant["jobs"][0]["qsub_argv"][6] = "2"
    else:
        decoy = root / "decoy" / "paper_story_a2_certification.sh"
        decoy.parent.mkdir()
        decoy.write_bytes(
            (A2.POLICY_PATH.parents[2]
             / policy.document["scheduler"]["job_body"]).read_bytes())
        mutant["jobs"][0]["qsub_argv"][-1] = str(decoy)
        mutant["job_body_sha256"] = hashlib.sha256(decoy.read_bytes()).hexdigest()
    with pytest.raises(A2.CertificationError):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def _assert_real_submission_visibility_is_accepted(policy, root, submission):
    binding = A2._validate_submission_receipt(
        policy, submission, root.name, root, CURRENT_PIN)
    assert binding["request_ids"] == {
        "rr5": "945411.nqsv", "rr50": "945412.nqsv"}
    assert submission["jobs"][0]["qstat_visibility"]["state"] == "QUE"


def test_submission_visibility_uses_the_full_real_qstat_fixture(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-real-qstat", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    fixture_bytes = QSTAT_VISIBILITY_FIXTURE.read_bytes()
    assert hashlib.sha256(fixture_bytes).hexdigest() == (
        "55bc7a633cd903bfa592ab71c4f347b6a50cce7ca295acb068de50b390ef830d"
    )
    fixture = fixture_bytes.decode("utf-8")
    assert len(fixture.splitlines()) == 94
    assert "Current State           = Staging" in fixture
    assert "Request State = RUN" not in fixture
    historical_stdout = (
        "/work/1/SFC/tanab/izanagi-measurements/"
        "dev-wave-paper-story-a2-cert-20260824/t1647-20260825/"
        "scheduler/job.stdout")
    historical_stderr = historical_stdout.removesuffix("job.stdout") + "job.stderr"
    for workload_id, request_id in (
            ("rr5", "945411.nqsv"), ("rr50", "945412.nqsv")):
        expected = fixture.replace("945411.nqsv", request_id)
        expected = expected.replace(
            historical_stdout,
            f"/synthetic/attempt/jobs/{workload_id}/scheduler/job.stdout")
        expected = expected.replace(
            historical_stderr,
            f"/synthetic/attempt/jobs/{workload_id}/scheduler/job.stderr")
        fanout_fixture = QSTAT_FANOUT_VISIBILITY_FIXTURES[
            workload_id].read_text(encoding="utf-8")
        assert fanout_fixture == expected
        assert len(fanout_fixture.splitlines()) == 94
        assert submission["jobs"][
            0 if workload_id == "rr5" else 1]["qstat_visibility"]["stdout"] \
            == fanout_fixture
    assert A2.SUBMISSION_SCHEMA == "paper-story-a2-submission-receipt/v4"
    assert A2._SUBMISSION_VISIBLE_STATES == frozenset({"QUE", "RUN"})
    _assert_real_submission_visibility_is_accepted(
        policy, root, submission)


def test_submission_visibility_rejects_another_request_block(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-another-block", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = (
        "Request ID: 999999.nqsv\n"
        + mutant["jobs"][0]["qstat_visibility"]["stdout"])
    with pytest.raises(A2.CertificationError, match="request ID count is not one"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_conflicting_state_fields(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-state-conflict", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] += "Request State = RUN\n"
    with pytest.raises(A2.CertificationError, match="state fields conflict"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_state_before_target_id(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-state-before-id", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = (
        "Request State = QUE\n"
        + mutant["jobs"][0]["qstat_visibility"]["stdout"])
    with pytest.raises(
        A2.CertificationError, match="state before the target request ID"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_non_none_ended_time(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-ended-time", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = mutant[
        "jobs"][0]["qstat_visibility"]["stdout"].replace(
            "Ended Request Time   = (none)",
            "Ended Request Time   = Tue Aug 25 09:00:00 2026",
            1,
        )
    with pytest.raises(A2.CertificationError, match=r"not \(none\)"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


@pytest.mark.parametrize(
    ("mutation", "signature"),
    (
        ("missing", "ended request time is missing"),
        ("duplicated", "ended request time is duplicated"),
        ("before-request-id", "ended request time precedes request ID"),
    ),
)
def test_submission_visibility_requires_one_ended_time_after_request_id(
        tmp_path, mutation, signature):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-ended-time-" + mutation, CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    ended_line = "    Ended Request Time   = (none)\n"
    stdout = mutant["jobs"][0]["qstat_visibility"]["stdout"]
    assert stdout.count(ended_line) == 1
    if mutation == "missing":
        stdout = stdout.replace(ended_line, "", 1)
    elif mutation == "duplicated":
        stdout = stdout.replace(ended_line, ended_line * 2, 1)
    else:
        stdout = ended_line + stdout.replace(ended_line, "", 1)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = stdout
    with pytest.raises(A2.CertificationError, match=signature):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_disappearance_with_visible_block(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-visible-and-disappeared", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] += (
        "Batch Request: 945411.nqsv does not exist on nqsv.\n")
    with pytest.raises(
            A2.CertificationError,
            match="contains a disappeared request signature"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_receipt_state_mismatch(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-receipt-state-mismatch", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["state"] = "RUN"
    with pytest.raises(
            A2.CertificationError,
            match="receipt state differs from canonical stdout state"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_rejects_finished_request_stdout(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-finished-request", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = mutant[
        "jobs"][0]["qstat_visibility"]["stdout"].replace(
            "Current State           = Staging",
            "Current State           = Completed",
            1,
        )
    with pytest.raises(A2.CertificationError, match="contains a terminal state"):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


@pytest.mark.parametrize(
    ("raw_state", "signature"),
    NON_ACCEPTED_VISIBILITY_VOCABULARY,
)
def test_submission_visibility_rejects_nonaccepted_vocabulary(
        tmp_path, raw_state, signature):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-vocab-" + raw_state.casefold(), CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)
    mutant = copy.deepcopy(submission)
    mutant["jobs"][0]["qstat_visibility"]["stdout"] = mutant[
        "jobs"][0]["qstat_visibility"]["stdout"].replace(
            "Current State           = Staging",
            "Current State           = " + raw_state,
            1,
        )
    with pytest.raises(A2.CertificationError, match=signature):
        A2._validate_submission_receipt(
            policy, mutant, root.name, root, CURRENT_PIN)


def test_submission_visibility_vocabulary_sets_are_nonvacuous_and_exact():
    assert NON_ACCEPTED_VISIBILITY_VOCABULARY
    assert {item[0] for item in NON_ACCEPTED_VISIBILITY_VOCABULARY} == {
        "Held", "Suspended"}
    assert A2._SUBMISSION_VISIBLE_STATES == frozenset({"QUE", "RUN"})


def test_submission_visibility_requires_timestamped_nonterminal_state(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-submit-missing-timestamp", CURRENT_PIN)
    _, submission = _write_receipt_bundle(policy, root)
    _assert_real_submission_visibility_is_accepted(policy, root, submission)

    missing_time = copy.deepcopy(submission)
    missing_time["jobs"][0]["qstat_visibility"].pop("observed_at_utc")
    with pytest.raises(A2.CertificationError, match="qstat visibility"):
        A2._validate_submission_receipt(
            policy, missing_time, root.name, root, CURRENT_PIN)


def test_m11_materializer_stages_marker_before_single_noreplace_rename(
        tmp_path, monkeypatch):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-m11", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2.collect_results(
        policy, evidence["raw_results"], attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"],
        frozen_files=evidence["raw_files"], attempt_root=root)
    report["source_commit"] = evidence["source_commit"]
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

    v2_report = copy.deepcopy(report)
    v2_report["schema_version"] = "paper-story-a2-certification-result/v2"
    v2_repo = tmp_path / "v2-repo"
    v2_repo.mkdir()
    with pytest.raises(A2.CertificationError, match="identity differ"):
        A2.materialize(policy, v2_report, evidence, repo_root=v2_repo)
    assert not (v2_repo / policy.tracked_destination).exists()


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
        request_ids={"rr5": "reps-a.nqsv", "rr50": "reps-b.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
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
        request_ids={"rr5": "finite-a.nqsv", "rr50": "finite-b.nqsv"},
        _test_token=A2._COLLECT_TEST_TOKEN)
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
    compute = root / "jobs" / "rr5" / "compute-result.json"
    compute.write_text(
        json.dumps({
            "schema_version": A2.COMPUTE_RESULT_SCHEMA,
            "workload": "rr5",
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
    if terminal_reason == "request-disappeared-after-visibility":
        assert evidence["completion"]["jobs"][0]["terminal_observation"]["stdout"] == (
            "Batch Request: 945411.nqsv does not exist on nqsv.\n")


@pytest.mark.parametrize(
    "mutation", ("empty-output", "visible-output", "nonzero-rc", "stderr"),
)
def test_disappeared_terminal_rejects_noncanonical_observations(
        tmp_path, mutation):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(
        policy, "attempt-disappeared-negative-" + mutation, CURRENT_PIN)
    _, submission = _write_receipt_bundle(
        policy, root, terminal_reason="request-disappeared-after-visibility")
    completion, _ = A2._read_json(root / "receipts" / "completion.json")
    terminal = completion["jobs"][0]["terminal_observation"]
    if mutation == "empty-output":
        terminal["stdout"] = ""
    elif mutation == "visible-output":
        terminal["stdout"] = "Request ID: 945411.nqsv\nRequest State = RUN\n"
    elif mutation == "nonzero-rc":
        terminal["returncode"] = 1
    else:
        terminal["stderr"] = "qstat failed\n"
    submission_binding = A2._validate_submission_receipt(
        policy, submission, root.name, root, CURRENT_PIN)
    with pytest.raises(A2.CertificationError):
        A2._validate_completion_receipt(
            policy, completion, root.name, root, CURRENT_PIN,
            submission_binding,
        )


def test_raw_manifest_binds_campaign_lock_and_wal_and_freezes_raw_bytes(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-frozen", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    assert len(evidence["raw_files"]) == 10
    raw_path = root / "jobs" / "rr5" / "raw" / "rr5-stock.json"
    raw_path.write_text('{"tampered":true}\n', encoding="utf-8")
    report = A2.collect_results(
        policy, evidence["raw_results"], attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"],
        frozen_files=evidence["raw_files"], attempt_root=root)
    assert report["status"] == "observed-positive"
    assert report["independent_observation_limits"]["correctness_run_argv"] \
        == "not-recorded-by-existing-pipeline"

    direct_root = A2.preregister_attempt(
        policy, "attempt-finalizer-direct", CURRENT_PIN)
    _write_receipt_bundle(policy, direct_root, claim_manifest=False)
    noise = direct_root / "jobs" / "not-a-policy-workload" / "raw"
    noise.mkdir(parents=True)
    (noise / "decoy.json").write_text("{}\n", encoding="utf-8")
    assert A2.finalize_raw_manifest(
        policy, direct_root, CURRENT_PIN).is_file()

    polluted_root = A2.preregister_attempt(
        policy, "attempt-job-local-raw-extra", CURRENT_PIN)
    _write_receipt_bundle(policy, polluted_root, claim_manifest=False)
    (polluted_root / "jobs" / "rr5" / "raw" / "decoy.json").write_text(
        "{}\n", encoding="utf-8")
    with pytest.raises(A2.CertificationError, match="inventory is not closed"):
        A2.finalize_raw_manifest(policy, polluted_root, CURRENT_PIN)

    consumer_root = A2.preregister_attempt(
        policy, "attempt-consumer-raw-extra", CURRENT_PIN)
    consumer_acquisition, _ = _write_receipt_bundle(policy, consumer_root)
    (consumer_root / "jobs" / "rr50" / "raw" / "decoy.json").write_text(
        "{}\n", encoding="utf-8")
    consumer_evidence = A2.validate_acquisition_bundle(
        policy, consumer_acquisition, current_pin=CURRENT_PIN)
    assert consumer_evidence["raw_manifest_valid"] is False
    assert "inventory is not closed" in consumer_evidence["raw_manifest_reason"]

    manifest_root = A2.preregister_attempt(
        policy, "attempt-manifest-inventory", CURRENT_PIN)
    _, manifest_submission = _write_receipt_bundle(policy, manifest_root)
    completion, _ = A2._read_json(
        manifest_root / "receipts" / "completion.json")
    submission_binding = A2._validate_submission_receipt(
        policy, manifest_submission, manifest_root.name, manifest_root,
        CURRENT_PIN)
    completion_binding = A2._validate_completion_receipt(
        policy, completion, manifest_root.name, manifest_root, CURRENT_PIN,
        submission_binding)
    manifest_path = Path(completion["raw_result_manifest"])
    manifest, _ = A2._read_json(manifest_path)
    manifest["files"]["jobs/rr5/raw/extra.json"] = "0" * 64
    mutant_path = manifest_root / "raw-manifest-mutant.json"
    A2.write_json_x(mutant_path, manifest)
    with pytest.raises(A2.CertificationError, match="inventory"):
        A2._load_raw_manifest_bundle(
            policy, mutant_path,
            hashlib.sha256(mutant_path.read_bytes()).hexdigest(),
            attempt_id=manifest_root.name, attempt_root=manifest_root,
            current_pin=CURRENT_PIN,
            job_bindings=completion_binding["jobs"],
        )

    raw = evidence["raw_results"][0]
    claim_path = Path(raw["campaign_evidence"]["claim_path"])
    claim = A2._decode_campaign_claim(claim_path.read_bytes(), "fixture claim")
    binding = reservation.read_binding(
        evidence["reservation_results"]["rr5"]["environment"])
    A2._validate_claim_reservation_binding(
        claim, campaign_id=raw["campaign_evidence"]["campaign_id"],
        request_id="945411.nqsv", reservation_binding=binding,
        expected_protocol_digest=claim["protocol_digest"])
    mutant_claim = dict(claim)
    mutant_claim["protocol_digest"] = "0" * 64
    with pytest.raises(A2.CertificationError, match="protocol digest"):
        A2._campaign_observation(
            policy, policy.cell(raw["cell_id"]),
            str(Path(raw["campaign_evidence"]["lock_path"]).parent),
            root.name, CURRENT_PIN,
            claim_bytes=A2._canonical_json(mutant_claim))
    with pytest.raises(A2.CertificationError, match="protocol digest"):
        A2._validate_claim_reservation_binding(
            mutant_claim,
            campaign_id=raw["campaign_evidence"]["campaign_id"],
            request_id="945411.nqsv", reservation_binding=binding,
            expected_protocol_digest=claim["protocol_digest"])

    mutant_claim = dict(claim)
    mutant_claim["job_id"] = "another-request.nqsv"
    with pytest.raises(A2.CertificationError, match="submission or reservation"):
        A2._validate_claim_reservation_binding(
            mutant_claim,
            campaign_id=raw["campaign_evidence"]["campaign_id"],
            request_id="945411.nqsv", reservation_binding=binding,
            expected_protocol_digest=claim["protocol_digest"])

    failed_root = A2.preregister_attempt(
        policy, "attempt-one-driver-failed", CURRENT_PIN)
    failed_acquisition, failed_submission = _write_receipt_bundle(
        policy, failed_root, driver_rc=7, claim_manifest=False)
    failed_evidence = A2.validate_acquisition_bundle(
        policy, failed_acquisition, current_pin=CURRENT_PIN)
    assert failed_evidence["driver_rcs"] == {"rr5": 7, "rr50": 0}
    failed_completion, _ = A2._read_json(
        failed_root / "receipts" / "completion.json")
    decoy = failed_root / "decoy-manifest.json"
    A2.write_json_x(decoy, {"decoy": True})
    failed_completion["raw_result_manifest"] = str(decoy)
    failed_completion["raw_result_manifest_sha256"] = hashlib.sha256(
        decoy.read_bytes()).hexdigest()
    failed_submission_binding = A2._validate_submission_receipt(
        policy, failed_submission, failed_root.name, failed_root, CURRENT_PIN)
    with pytest.raises(A2.CertificationError, match="failed group"):
        A2._validate_completion_receipt(
            policy, failed_completion, failed_root.name, failed_root,
            CURRENT_PIN, failed_submission_binding)


def test_changed_campaign_wal_invalidates_the_manifest_bundle(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "attempt-wal-change", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    raw, _ = A2._read_json(
        root / "jobs" / "rr5" / "raw" / "rr5-stock.json")
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


def test_official_run_observes_and_passes_current_toolchain_manifest(
        tmp_path, monkeypatch):
    source = inspect.getsource(A2.run_workload)
    observed = "buildcache.observed_toolchain_manifest("
    passed = "expected_toolchain_manifest=expected_toolchain_manifest"
    assert observed in source and passed in source
    assert source.index(observed) < source.index("summary = run_campaign(")

    policy = _policy(tmp_path)
    attempt = A2.preregister_attempt(
        policy, "actual-run-workload-producer", CURRENT_PIN)
    job_root = A2.workload_job_root(policy, attempt, "rr5")
    raw_root = job_root / "raw"
    raw_root.mkdir()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    ccbench = tmp_path / "ccbench"
    ccbench.mkdir()
    calls = {}

    def git_run(command, **kwargs):
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, CURRENT_PIN + "\n", "")
        if command[:3] == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(command)

    def producer(cfg, genomes, *args, output_root, **kwargs):
        cfg = ident.bind_admission_policy(
            cfg, kwargs["build_context"].policy)
        layout = loop.campaign_layout(
            str(ident.campaign_id(cfg)), output_root).ensure()
        calls["output_root"] = Path(output_root)
        calls["layout_root"] = Path(layout.root)
        return A2.SimpleNamespace(
            results=[A2.SimpleNamespace() for _ in genomes],
            skipped=0, layout_root=layout.root)

    def raw_producer(_policy, cell, *, layout_root, **kwargs):
        assert Path(layout_root) == calls["layout_root"]
        return {"cell_id": cell.cell_id, "terminal": "commit"}

    monkeypatch.setattr(A2.subprocess, "run", git_run)
    monkeypatch.setattr(loop, "run_campaign", producer)
    monkeypatch.setattr(A2, "_raw_cell_from_wal", raw_producer)
    monkeypatch.setattr(
        buildcache, "compilers_for_current_site", lambda: ("gcc", "g++"))
    monkeypatch.setattr(
        buildcache, "observed_toolchain_manifest",
        lambda *_args, **_kwargs: {"fixture": "toolchain"})
    monkeypatch.setattr(env_contract, "authorize", lambda _tag: object())

    A2.run_workload(
        policy, workload_id="rr5", attempt_root=attempt, raw_root=raw_root,
        current_pin=CURRENT_PIN, dependency_prefix=dependency,
        ccbench_dir=ccbench, log=lambda *_args: None)
    assert calls["output_root"] == job_root
    assert calls["layout_root"].parent == job_root / "campaigns"
    assert not (job_root / "campaigns" / "campaigns").exists()
    assert {path.name for path in raw_root.iterdir()} == {
        "rr5-stock.json", "rr5-fixed10.json"}


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


def test_wal_configure_locator_comes_from_versioned_grammar():
    source = inspect.getsource(A2._raw_cell_from_wal)
    assert '_cmake_directory(configure, "-B")' not in source
    assert '["build_directory_option"]' in source


def test_synthetic_pbs_free_preregister_through_analyze_positive(tmp_path):
    policy = _policy(tmp_path)
    root = A2.preregister_attempt(policy, "synthetic-positive", CURRENT_PIN)
    acquisition, _ = _write_receipt_bundle(policy, root)
    evidence = A2.validate_acquisition_bundle(
        policy, acquisition, current_pin=CURRENT_PIN)
    report = A2.collect_results(
        policy, A2.load_raw_results(policy, root), attempt_id=root.name,
        current_pin=CURRENT_PIN, request_ids=evidence["request_ids"])
    report["source_commit"] = evidence["source_commit"]
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
        request_ids={"rr5": "125.nqsv", "rr50": "126.nqsv"})
    report_b = A2.collect_results(
        policy, second, attempt_id=root.name, current_pin=CURRENT_PIN,
        request_ids={"rr5": "125.nqsv", "rr50": "126.nqsv"})
    assert report_a == report_b


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
