from __future__ import annotations

import ast
import copy
import errno
import hashlib
import json
import math
import os
import shlex
import statistics
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest


pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")

from orchestrator.calibrator import runner as calibrator_runner
from orchestrator.campaign import campaign_lock, ident, loop as campaign_loop, wal
from orchestrator.campaign import paper_story_a1_paired as paired
from orchestrator.campaign.build_admission import (
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import exploration_campaign_layout
from orchestrator.campaign.model import COMMIT_CONTRACT_SHA256_KEY, WalRecord
from orchestrator.campaign.pipeline import BalancedScheduleConfig
from orchestrator.campaign.source_digest import SourceEvidence
from orchestrator.tests import commit_receipt_support as receipt_support


_TEST_BUILD_DIR: Path | None = None
_MISSING = object()


@pytest.fixture(autouse=True)
def _readable_perf_binary(tmp_path: Path):
    global _TEST_BUILD_DIR
    build_root = (tmp_path / "trace0-build").resolve()
    for name in ("adaptive", "static10"):
        for flavor in (name, f"{name}-trace"):
            binary = build_root / flavor / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(
                f"paper-story-a1-{flavor}-test-binary\n".encode()
            )
    _TEST_BUILD_DIR = build_root
    try:
        yield
    finally:
        _TEST_BUILD_DIR = None


def _source_binding() -> dict:
    return {
        "measurement_source_commit": "a" * 40,
        "files": {
            relative: {
                "git_blob_oid": "b" * 40,
                "working_sha256": "c" * 64,
            }
            for relative in paired.SOURCE_RELATIVE_PATHS
        },
        "evidence_level": "source-routed-trace0",
        "artifact_standalone_proof": False,
    }


def _dependency_prefix_fixture() -> str:
    assert _TEST_BUILD_DIR is not None
    root = (_TEST_BUILD_DIR.parent / "dependency-scratch").resolve()
    return f"{root / 'gflags-install'};{root / 'glog-install'}"


def _reservation_binding() -> dict:
    return {
        "job_id": "0:12345.nqsv",
        "requested_s": 21600,
        "scheduler_started_epoch": 1_700_000_000.0,
        "deadline_epoch": 1_700_021_600.0,
        "host": "compute01",
        "boot_id": "test-boot-id",
        "script_sha256": "c" * 64,
        "nonce": "attempt",
    }


def _attempt_id_fixture(name: str, ordinal: int = 1) -> str:
    assert _TEST_BUILD_DIR is not None
    return hashlib.sha256(
        f"{_TEST_BUILD_DIR}|{name}|{ordinal}".encode("utf-8")
    ).hexdigest()[:32]


def _frame(stage: str, variant: str, attempt_id: str, payload: dict) -> dict:
    return {
        "line_number": 1,
        "byte_start": 0,
        "byte_end": 1,
        "raw_sha256": "1" * 64,
        "variant": variant,
        "stage": stage,
        "env_tag": "pegasus",
        "payload": {"build_attempt_id": attempt_id, **payload},
    }


def _arm(
    policy: dict,
    name: str,
    tps: list[object] | None = None,
    *,
    workload_name: str = "write-heavy",
) -> dict:
    assert _TEST_BUILD_DIR is not None
    build_dir = _TEST_BUILD_DIR / name
    binary = build_dir / "cc" / "silo" / "ycsb_silo.exe"
    trace_binary = (
        _TEST_BUILD_DIR / f"{name}-trace" / "cc" / "silo" / "ycsb_silo.exe"
    )
    arm = next(item for item in policy["arms"] if item["name"] == name)
    workload = next(
        item for item in policy["workloads"] if item["name"] == workload_name
    )
    attempt_id = _attempt_id_fixture(name)
    variant = f"variant-{name}"
    reps = paired._expected_reps(policy, workload_name)
    values = list(tps if tps is not None else (
        [1_000_000.0 + 10.0 * index for index in range(reps)]
        if name == "adaptive"
        else [990_000.0 + 20.0 * index for index in range(reps)]
    ))
    numeric = all(
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        for value in values
    )
    median = statistics.median(values) if numeric and values else 1.0
    cv = (
        statistics.stdev(values) / statistics.fmean(values)
        if numeric and len(values) >= 2 and statistics.fmean(values) != 0 else 0.0
    )
    receipt_sha = "e" * 64
    genome = paired.Genome(arm["protocol"], dict(arm["flags"]))
    toolchain = {
        "cmake": {"realpath": "/toolchain/cmake"},
        "cc": {"realpath": "/toolchain/cc"},
        "cxx": {"realpath": "/toolchain/cxx"},
    }
    toolchain_record_sha256 = hashlib.sha256(
        json.dumps(
            toolchain,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    configure_argv, build_argv = paired.buildcache._v2_commands(
        genome,
        False,
        "/source",
        os.fspath(build_dir),
        toolchain,
        jobs=48,
        dependency_prefix=_dependency_prefix_fixture(),
    )
    contract = paired.p2_2.env_contract.lookup("pegasus")
    run_flags = [
        "-thread_num=48",
        "-ycsb_tuple_num=1000000",
        "-extime=3",
        f"-clocks_per_us={contract.clocks_per_us}",
        "-ycsb_zipf_skew=0.9",
        f"-ycsb_rratio={workload['ycsb_rratio']}",
        "-ycsb_rmw=0",
        "-ycsb_max_ope=10",
    ]
    configure = " ".join(configure_argv)
    frames = [
        _frame(paired.STAGE_BUILD_START, variant, attempt_id, {
            "genome": paired.Genome(
                arm["protocol"], dict(arm["flags"])
            ).canonical(),
            "src_token": "source-token",
            "build_admission_receipt_sha256": receipt_sha,
        }),
        _frame(paired.STAGE_BUILD_DONE, variant, attempt_id, {
            "build_admission_receipt_sha256": receipt_sha,
            "perf_bin": os.fspath(binary),
            "perf_bin_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "perf_build_cmd": " ".join(build_argv),
            "perf_cached": False,
            "perf_configure_cmd": configure,
            "toolchain": toolchain,
            "toolchain_record_sha256": toolchain_record_sha256,
            "trace_bin": os.fspath(trace_binary),
            "trace_bin_sha256": hashlib.sha256(
                trace_binary.read_bytes()
            ).hexdigest(),
            "trace_cached": False,
        }),
        _frame(paired.STAGE_VERIFY_DONE, variant, attempt_id, {
            "certified": True,
            "verdict": "serializable",
            "workload": {"tag": "legacy"},
        }),
        _frame(paired.STAGE_BENCH_DONE, variant, attempt_id, {
            "median_tps": median,
            "cv": cv,
            "high_variance": False,
            "unstable": False,
            "rounds": 1,
            "tps": values,
            "rep_notes": [],
            "perf_observation": {"use_perf": False},
            "run_cmd": calibrator_runner.repro_command(
                os.fspath(binary), run_flags, contract.numactl, use_perf=False
            ),
        }),
        _frame(paired.STAGE_COMMIT, variant, attempt_id, {
            "fitness_tps": median,
            "cv": cv,
            "high_variance": False,
            "unstable": False,
            "verify_configs": ["legacy"],
            "build_admission_receipt_sha256": receipt_sha,
            COMMIT_CONTRACT_SHA256_KEY: contract.contract_sha256,
        }),
    ]
    frames[1]["raw_sha256"] = "2" * 64
    frames[3]["raw_sha256"] = "3" * 64
    evidence = {
        "name": name,
        "variant": variant,
        "attempt_count": 1,
        "attempts": [{"build_attempt_id": attempt_id, "frames": frames}],
        "last_terminal_stage": paired.STAGE_COMMIT,
        "last_stage": paired.STAGE_COMMIT,
    }
    evidence["all_evaluation_frames"] = frames
    return evidence


def _policy() -> dict:
    return paired.load_policy()[0]


def _v3_pilot_policy() -> dict:
    return paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]


def _balanced_receipt_fixture(
    policy: dict, workload_name: str,
) -> tuple[dict, dict[str, dict[str, object]]]:
    plan = paired._balanced_schedule_plan(policy, workload_name)
    variant = paired._workload_arm_by_role(
        policy, workload_name, "variant",
    )["name"]
    baseline = paired._workload_arm_by_role(
        policy, workload_name, "baseline",
    )["name"]
    role_to_name = {"variant": variant, "baseline": baseline}
    rows = []
    blocks = []
    arm_values = {variant: [], baseline: []}
    clock = 1_000_000
    for block in plan["blocks"]:
        arm_name = role_to_name[block["role"]]
        values = []
        for position, pair_index in enumerate(block["pair_indices"]):
            tps = (
                1_010_000.0 + pair_index * 3.0
                if block["role"] == "variant"
                else 1_000_000.0 + pair_index * 2.0
            )
            values.append(tps)
            rows.append({
                "arm": arm_name,
                "block": block["pair_block_number"],
                "block_position": position,
                "ended_at_ns": clock + 5,
                "group": block["group"],
                "pair_index": pair_index,
                "started_at_ns": clock,
                "tps": tps,
            })
            clock += 10
        arm_values[arm_name].extend(values)
        blocks.append({
            "arm": arm_name,
            "block": block["block_number"],
            "block_in_group": block["block_number"] % 4,
            "cv": statistics.stdev(values) / statistics.fmean(values),
            "group": block["group"],
            "tps": values,
        })
    arms = {}
    arm_results = {}
    for _role, name in role_to_name.items():
        values = arm_values[name]
        variant_id = f"variant-{name}"
        arms[name] = {
            "block_cvs": [
                item["cv"] for item in blocks if item["arm"] == name
            ],
            "cv": statistics.stdev(values) / statistics.fmean(values),
            "median_tps": statistics.median(values),
            "rounds": 1,
            "tps": values,
            "unstable": False,
            "variant": variant_id,
        }
        arm_results[name] = {"raw_tps": values, "variant": variant_id}
    derivation = plan["derivation"]
    return {
        "arms": arms,
        "bench_max_rounds": 1,
        "blocks": blocks,
        "effective_root_seed": derivation["effective_root_seed"],
        "group_bits": derivation["order_bits"],
        "pairing_design": paired.V3_PAIRING_DESIGN,
        "reps": rows,
        "root_seed": paired._workload_plan(
            policy, workload_name,
        )["schedule_root_seed"],
        "rounds": 1,
        "schedule_wall_s": 1.0,
        "schema_version": "paper-story-a1-balanced-schedule-receipt/v1",
        "seed_counter": derivation["counter"],
        "settled": {"settled": True},
        "workload": workload_name,
    }, arm_results


def _validated_workload(name: str = "write-heavy", campaign_id: str = "campaign-a"):
    policy = _policy()
    result = paired.validate_workload_evidence(
        policy,
        workload_name=name,
        campaign_id=campaign_id,
        env_tag="pegasus",
        arms=[
            _arm(policy, "adaptive", workload_name=name),
            _arm(policy, "static10", workload_name=name),
        ],
        wal_evidence={"path": "/raw/wal.jsonl", "size": 1, "sha256": "4" * 64},
        source_binding=_source_binding(),
        campaign_binding={"wal_path": f"/raw/{name}/runs/wal.jsonl"},
    )
    return result


def _raw_documents(*, invalid_workload: bool = False) -> tuple[dict, dict, dict, dict]:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    if invalid_workload:
        workloads[1]["valid"] = False
        workloads[1]["errors"] = ["fixture-invalid"]
        workloads[1]["statistics"] = None
        workloads[1]["terminal_result"] = {
            "status": "invalid",
            "reasons": ["fixture-invalid"],
        }
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        reservation_binding=_reservation_binding(),
        workloads=workloads,
    )
    attempt_identity = {"st_dev": 1, "st_ino": 2}
    completion_receipt = "/durable/attempt.completion.json"
    submission_sha = "d" * 64
    receipt = {
        "schema_version": paired.RECEIPT_SCHEMA,
        "study_id": paired.STUDY_ID,
        "formal": False,
        "promotion_prohibited": True,
        "pbs_jobid": "0:12345.nqsv",
        "policy": {
            "path": paired.POLICY_RELATIVE_PATH,
            "sha256": paired.POLICY_SHA256,
        },
        "source_binding": _source_binding(),
        "roots": {
            "attempt_root": "/durable/attempt",
            "completion_receipt": completion_receipt,
            "attempt_identity": attempt_identity,
        },
        "submission_receipt": {"sha256": submission_sha},
    }
    terminal = {
        "schema_version": paired.JOB_TERMINAL_SCHEMA,
        "study_id": paired.STUDY_ID,
        "pbs_jobid": "0:12345.nqsv",
        "pbs_observation": {
            "pbs_jobid": "0:12345.nqsv",
            "pbs_o_host": "pegasus01",
            "pbs_o_workdir": "/repo",
        },
        "expected_head": "a" * 40,
        "observed_head": "a" * 40,
        "porcelain": "",
        "driver_rc": 0,
        "shell_rc": 0,
        "status": "finished",
        "terminal_source_binding": _source_binding(),
        "reservation_binding": _reservation_binding(),
        "completion_receipt_path": completion_receipt,
        "attempt_identity": attempt_identity,
        "submission_receipt_sha256": submission_sha,
    }
    return result, receipt, terminal, policy


def _production_wal_workload(
    tmp_path: Path,
    name: str = "write-heavy",
    *,
    mutate_frames=None,
    raw_suffix: str = "",
    expected_preimage_transform=None,
) -> dict:
    policy = _policy()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    contract = paired.p2_2.env_contract.lookup("pegasus")
    cfg = paired.campaign_config(policy, name, contract=contract)
    cfg = paired.p2_2._campaign_cfg_for_site(
        cfg, paired.site_policy.PEGASUS_COMPUTE, contract
    )
    cfg = ident.bind_admission_policy(
        cfg, context.policy
    )
    lock_identity_preimage = ident.canonical_preimage(cfg)
    expected_preimage = (
        expected_preimage_transform(lock_identity_preimage)
        if expected_preimage_transform is not None else lock_identity_preimage
    )
    campaign_id = paired._campaign_id_from_preimage(name, expected_preimage)
    layout = exploration_campaign_layout(campaign_id, tmp_path / "campaign-output")
    Path(layout.runs_dir).mkdir(parents=True)
    ident.ensure_campaign_identity(
        cfg,
        layout,
        admission_policy=context.policy,
    )
    frames = []
    for arm_name in paired.ARM_ORDER:
        policy_arm = next(
            item for item in policy["arms"] if item["name"] == arm_name
        )
        genome = paired.Genome(
            policy_arm["protocol"], dict(policy_arm["flags"])
        )
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=str(tmp_path.resolve()),
            ccbench_commit=paired.pin.CURRENT_PIN,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token="stock",
            source_bytes_sha256=hashlib.sha256(b"stock").hexdigest(),
            tracked_clean=True,
            tracked_diff_sha256=hashlib.sha256(b"").hexdigest(),
            tracked_paths=(),
        )
        receipt = derive_build_admission(context, evidence).as_wal_receipt()
        arm = _arm(policy, arm_name, workload_name=name)
        arm_frames = arm["attempts"][0]["frames"]
        for frame in arm_frames:
            if frame["stage"] == paired.STAGE_BUILD_START:
                frame["payload"].update({
                    "src_token": receipt["source"]["src_token"],
                    "build_admission": receipt,
                    "build_admission_receipt_sha256": receipt["receipt_sha256"],
                })
            elif frame["stage"] in {
                paired.STAGE_BUILD_DONE,
                paired.STAGE_COMMIT,
            }:
                frame["payload"]["build_admission_receipt_sha256"] = (
                    receipt["receipt_sha256"]
                )
        frames.extend(arm_frames)
    if mutate_frames is not None:
        mutate_frames(frames)
    lines = []
    for index, frame in enumerate(frames, 1):
        record = WalRecord(
            variant=frame["variant"],
            stage=frame["stage"],
            env_tag=frame["env_tag"],
            ts=float(index),
            payload=frame["payload"],
        )
        lines.append(wal._record_to_line(record))
    Path(layout.wal_file).write_text(
        "\n".join(lines) + "\n" + raw_suffix, encoding="utf-8"
    )
    return paired.collect_workload(
        policy,
        workload_name=name,
        campaign_id=campaign_id,
        layout=layout,
        admission_policy=context.policy,
        env_tag="pegasus",
        source_binding=_source_binding(),
        expected_campaign_preimage=expected_preimage,
        expected_layout_root=layout.root,
    )


def _noncertifying_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    anomalies: object = 0,
):
    policy, policy_sha = paired.load_policy()
    monkeypatch.setattr(
        paired, "_durable_measurement_base", lambda _policy: tmp_path.resolve(),
    )
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    contract = paired.p2_2.env_contract.lookup("pegasus")
    repo_root = paired._repo_root().resolve(strict=True)
    source_commit = paired._run_git(repo_root, "rev-parse", "HEAD")
    legacy_source_binding = _source_binding()
    legacy_source_binding["measurement_source_commit"] = source_commit
    non_certifying_source_binding = paired._non_certifying_source_binding(
        repo_root, source_commit,
    )
    configs = [
        ident.bind_admission_policy(
            paired.p2_2._campaign_cfg_for_site(
                paired.campaign_config(
                    policy, name, contract=contract, non_certifying=True,
                ),
                paired.site_policy.PEGASUS_COMPUTE,
                contract,
            ),
            context.policy,
        )
        for name in paired.WORKLOAD_ORDER
    ]
    campaign_ids = [str(ident.campaign_id(cfg)) for cfg in configs]
    attempt = (tmp_path / "noncertifying-attempt").resolve()
    attempt.mkdir()
    (attempt / "raw" / "tmp").mkdir(parents=True)
    (attempt / "cache").mkdir()
    argv, options = paired._canonical_qsub_contract(
        repo_root=repo_root,
        study_id=paired.STUDY_ID,
        source_commit=source_commit,
        attempt=attempt,
    )
    intent = {
        "schema_version": paired.SUBMISSION_INTENT_SCHEMA,
        "study_id": paired.STUDY_ID,
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "qsub_argv": argv,
        "qsub_options": options,
        "source_binding": non_certifying_source_binding,
    }
    intent["intent_sha256"] = paired._submission_intent_digest(intent)
    paired._exclusive_write(paired._attempt_intent_path(attempt), intent)
    projection = paired.trial_registry.issue_a1_registered_noncertifying_projection(
        study_id=paired.STUDY_ID,
        policy_sha256=policy_sha,
        preregistration_sha256=paired.PREREGISTRATION_SHA256,
        source_commit=source_commit,
        workloads=paired.WORKLOAD_ORDER,
        campaign_ids=campaign_ids,
    )
    common = paired._a1_common_record(
        projection,
        source_binding=non_certifying_source_binding,
        environment_contract_sha256=contract.contract_sha256,
        intent_sha256=intent["intent_sha256"],
    )
    layouts = [
        exploration_campaign_layout(cid, attempt / "raw" / "campaign-output")
        for cid in campaign_ids
    ]
    paired._preseed_a1_non_certifying_locks(
        configs=configs,
        layouts=layouts,
        workloads=paired.WORKLOAD_ORDER,
        common_record=common,
    )
    rewritten = []
    for name, cfg, campaign_id, layout in zip(
        paired.WORKLOAD_ORDER, configs, campaign_ids, layouts,
    ):
        with wal.a1_non_certifying_io(layout):
            for arm_name in paired.ARM_ORDER:
                arm_policy = next(
                    item for item in policy["arms"] if item["name"] == arm_name
                )
                genome = paired.Genome(
                    arm_policy["protocol"], dict(arm_policy["flags"])
                )
                source = SourceEvidence(
                    schema_version="source-evidence/v1",
                    source_root=str(tmp_path.resolve()),
                    ccbench_commit=paired.pin.CURRENT_PIN,
                    genome_sha256=hashlib.sha256(
                        genome.canonical().encode("utf-8")
                    ).hexdigest(),
                    src_token="stock",
                    source_bytes_sha256=hashlib.sha256(b"stock").hexdigest(),
                    tracked_clean=True,
                    tracked_diff_sha256=hashlib.sha256(b"").hexdigest(),
                    tracked_paths=(),
                )
                admission = derive_build_admission(
                    context, source
                ).as_wal_receipt()
                frames = _arm(policy, arm_name, workload_name=name)[
                    "attempts"
                ][0]["frames"]
                for index, frame in enumerate(frames):
                    payload = copy.deepcopy(frame["payload"])
                    if (
                        name == paired.WORKLOAD_ORDER[0]
                        and arm_name == paired.ARM_ORDER[0]
                        and frame["stage"] == paired.STAGE_VERIFY_DONE
                    ):
                        if anomalies is not _MISSING:
                            payload["anomalies"] = anomalies
                    elif frame["stage"] == paired.STAGE_VERIFY_DONE:
                        payload["anomalies"] = 0
                    if frame["stage"] == paired.STAGE_BUILD_START:
                        payload.update({
                            "src_token": admission["source"]["src_token"],
                            "build_admission": admission,
                            "build_admission_receipt_sha256": admission[
                                "receipt_sha256"
                            ],
                        })
                    elif frame["stage"] in {
                        paired.STAGE_BUILD_DONE, paired.STAGE_COMMIT,
                    }:
                        payload["build_admission_receipt_sha256"] = admission[
                            "receipt_sha256"
                        ]
                    record = WalRecord(
                        variant=frame["variant"],
                        stage=frame["stage"],
                        env_tag=frame["env_tag"],
                        ts=float(index + 1),
                        payload=payload,
                    )
                    if record.stage == paired.STAGE_COMMIT:
                        receipt_support.log_receipted_commit(
                            layout,
                            record.variant,
                            record.env_tag,
                            record.payload,
                            operation_identity=record.payload[
                                "build_attempt_id"
                            ],
                        )
                    else:
                        wal.append(layout, record)
        rewritten.append(paired.collect_workload(
            policy,
            workload_name=name,
            campaign_id=campaign_id,
            layout=layout,
            admission_policy=context.policy,
            env_tag="pegasus",
            source_binding=legacy_source_binding,
            expected_campaign_preimage=ident.canonical_preimage(cfg),
            expected_layout_root=layout.root,
        ))
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=legacy_source_binding,
        reservation_binding={
            **_reservation_binding(),
            "job_id": "12345.nqsv",
            "nonce": attempt.name,
        },
        workloads=rewritten,
    )
    evidence = paired._attempt_evidence_paths(attempt)
    request_id = "12345.nqsv"
    qsub_stdout = f"{request_id}\n"
    submission = {
        "schema_version": paired.SUBMISSION_SCHEMA,
        "route": "direct-qsub",
        "study_id": paired.STUDY_ID,
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "request_id": request_id,
        "submission_receipt_path": evidence["submission_receipt"],
        "completion_receipt_path": evidence["completion_receipt"],
        "qsub_argv": argv,
        "qsub_options": options,
        "submit_observation": {
            "submit_host": "fixture-host",
            "qsub_stdout": qsub_stdout,
            "qsub_stdout_sha256": hashlib.sha256(qsub_stdout.encode()).hexdigest(),
            "qsub_stderr": "",
            "qsub_stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "qstat_visibility": {
                "request_id": request_id,
                "visible": True,
                "state": "QUE",
                "queue": "gen_S",
                "observed_epoch": 1,
            },
        },
    }
    paired._exclusive_write(Path(evidence["submission_receipt"]), submission)
    result_root = attempt / "raw" / "results"
    result_root.mkdir()
    result_path = result_root / "result.json"
    receipt_path = result_root / "receipt.json"
    paired._exclusive_write(result_path, result)
    roots = {
        "attempt_root": os.fspath(attempt),
        "attempt_identity": paired._attempt_root_identity(attempt),
        "raw_root": os.fspath(attempt / "raw"),
        "output_root": os.fspath(attempt / "raw" / "campaign-output"),
        "cache_root": os.fspath(attempt / "cache"),
        "result_root": os.fspath(result_root),
        "tmp_root": os.fspath(attempt / "raw" / "tmp"),
        **evidence,
    }
    receipt = {
        "schema_version": paired.RECEIPT_SCHEMA,
        "study_id": paired.STUDY_ID,
        "formal": False,
        "promotion_prohibited": True,
        "route": "direct-qsub",
        "pbs_jobid": request_id,
        "host": "fixture-host",
        "recorded_epoch": 1,
        "policy": {
            "path": paired.POLICY_RELATIVE_PATH,
            "sha256": policy_sha,
        },
        "source_binding": legacy_source_binding,
        "submission_receipt": {
            "path": evidence["submission_receipt"],
            "sha256": hashlib.sha256(
                Path(evidence["submission_receipt"]).read_bytes()
            ).hexdigest(),
        },
        "scheduler_completion_receipt": {
            "path": evidence["completion_receipt"],
        },
        "roots": roots,
        "result": {
            "path": os.fspath(result_path),
            "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "complete": result["complete"],
            "all_workloads_terminal": result["all_workloads_terminal"],
        },
        "calibration_sha256": None,
    }
    paired._exclusive_write(receipt_path, receipt)
    sidecar = paired._issue_non_certifying_observation(
        common_record=common,
        source_binding=non_certifying_source_binding,
        workloads=rewritten,
        result_path=result_path,
        receipt_path=receipt_path,
    )
    Path(evidence["stdout_path"]).write_bytes(b"fixture stdout\n")
    Path(evidence["stderr_path"]).write_bytes(b"")
    terminal_path = attempt / "raw" / "job-terminal.json"
    terminal = {
        "schema_version": paired.JOB_TERMINAL_SCHEMA,
        "study_id": paired.STUDY_ID,
        "pbs_jobid": request_id,
        "expected_head": source_commit,
        "observed_head": source_commit,
        "porcelain": "",
        "driver_rc": 0,
        "shell_rc": 0,
        "status": "finished",
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "submission_receipt_sha256": receipt["submission_receipt"]["sha256"],
        "completion_receipt_path": evidence["completion_receipt"],
        "pbs_observation": {
            "pbs_jobid": request_id,
            "pbs_o_host": "fixture-host",
            "pbs_o_workdir": os.fspath(repo_root),
        },
        "reservation_binding": result["reservation_binding"],
        "attempt_identity": roots["attempt_identity"],
        "terminal_source_binding": legacy_source_binding,
        "recorded_epoch": 2,
    }
    paired._exclusive_write(terminal_path, terminal)

    def binding(candidate: Path) -> dict:
        return {
            "path": os.fspath(candidate),
            "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        }

    qstat_stdout = (
        f"Request ID: {request_id}\nState: EXT\nExit Status: 0\n"
    )
    completion = {
        "schema_version": paired.COMPLETION_SCHEMA,
        "study_id": paired.STUDY_ID,
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "request_id": request_id,
        "submission_receipt": binding(Path(evidence["submission_receipt"])),
        "scheduler_terminal": {
            "terminal_reason": "scheduler-end-state",
            "qstat_visible": True,
            "qstat_rc": 0,
            "state": {"observed": True, "value": "EXT"},
            "exit_status": {"observed": True, "value": 0},
            "observed_epoch": 2,
            "qstat_stdout": qstat_stdout,
            "qstat_stdout_sha256": hashlib.sha256(
                qstat_stdout.encode()
            ).hexdigest(),
        },
        "stdout": binding(Path(evidence["stdout_path"])),
        "stderr": binding(Path(evidence["stderr_path"])),
        "job_terminal": binding(terminal_path),
    }
    paired._exclusive_write(Path(evidence["completion_receipt"]), completion)
    return sidecar, rewritten, common


def _frame_for(arm: dict, stage: str) -> dict:
    return next(
        frame for frame in arm["attempts"][0]["frames"]
        if frame["stage"] == stage
    )


def test_policy_file_is_the_exact_preregistered_contract() -> None:
    policy, digest = paired.load_policy()
    assert policy["schema_version"] == "paper-story-a1-paired-policy/v2"
    assert policy["study_id"] == paired.STUDY_ID
    assert policy["arm_order"] == ["adaptive", "static10"]
    assert [item["name"] for item in policy["workloads"]] == list(
        paired.WORKLOAD_ORDER
    )
    assert policy["pairing"]["design"] == "arm-grouped-positional-v1"
    assert policy["authority"] == {
        "formal": False,
        "promotion_prohibited": True,
        "result_authority": "exploratory",
        "statistics_authority": "T-1721 stage-4 sized preregistration",
        "d510_role": "analogy-only",
    }
    assert policy["execution"]["durable_measurement_base"] == (
        "/work/1/SFC/tanab/dev-wave-jobs/"
        "dev-wave-paper-story-a1-paired-20260826-sized/measurement"
    )
    assert policy["execution"]["materialization_relative_path"] == (
        "output/insights/2026-08-26_paper-story-a1-sized"
    )
    assert policy["execution"]["bench_max_rounds"] == 3
    assert {
        item["name"]: (
            item["reps"], item["df"], item["k"], item["planned_sigma_tps"]
        )
        for item in policy["workloads"]
    } == {
        "write-heavy": (72, 71, 1.993943, 103551.0849),
        "balanced": (205, 204, 1.971661, 156906.1857),
        "read-heavy": (28, 27, 2.051831, 60384.6868),
    }
    assert policy["statistics"]["floor"]["floor_fraction"] == 0.030
    assert policy["statistics"]["classification_rules"] == paired.CLASSIFICATION_RULES
    assert policy["statistics"]["variance_plan_breach"][
        "overrides_classification"
    ] is False
    assert policy["rerun"]["allowed_reasons"] == paired.RERUN_REASONS
    assert policy["preregistration"] == {
        "path": paired.PREREGISTRATION_RELATIVE_PATH,
        "sha256": paired.PREREGISTRATION_SHA256,
    }
    assert hashlib.sha256(paired.POLICY_PATH.read_bytes()).hexdigest() == digest


def test_legacy_frozen_bytes_have_independent_literal_goldens() -> None:
    repo_root = Path(paired.__file__).resolve().parents[2]
    literal_goldens = {
        "orchestrator/campaign/paper_story_a1_paired.v2.json": "83b9c1a1ca4cce1e6394ce3338b491b14663427259eb3e129560fe5b50b99b5b",
        "output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md": "c85279e997c7483060f3282836aa4800f473b95fe5f0fc1807431f06a0817fea",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/MUTATION.md": "40e297edfb1b377445667e1e8ff7364c05de4b683983ffedc1a3edccfefaa93a",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/README.md": "6133e2143f73c47d8b69909755f5953f926a755df9c62fce4e7bb1a0f29aae03",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/mutation-attempts.final.json": "0d7e844c74228d26a3db3440b3de9f3e8f17eebbd79653dc29be39fbf7a60f6a",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/mutation-ledger.final.json": "13e5e27695aede3ea8ef40f5ce11f23e3ca41f33d8faffdfa25d43453dea4148",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/mutation-ledger.m06-correction.json": "ec507c8f5e72e62c7271664fd1ccd68743ea35dd6a45a920f064108a9e95daa2",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/mutation-spec.final.json": "6d10323b30644074b7f306fbf2094d7576cba12edb3514de1ea5a0a705becc77",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/mutation-spec.m06-correction.json": "d48c7cb2fb4e551f67da131053d73131be0a242471ce020d42c965618f2a0fd2",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/sizing-certificate.failed-v1.json": "da511809ba1ef855c39f78aacee3feba5524c222b80d77f2884b61223aa10efd",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/sizing-certificate.v2.json": "4f4735cf43f227f421b0bfcc2c9f17328736a105def15071838e0ba5d5a3e18a",
        "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/sizing-replay-receipt.v2.json": "269f070b4603e93b42ebc6433d0f8deb370a021be6afcd452320a63e9a9f0ff3",
        "orchestrator/campaign/paper_story_a1_headline.py": "08ee08ad505d5a1a1c9186bd2838545f5f830d6a9f9ff0a0376069cc466f0edf",
        "orchestrator/campaign/paper_story_a1_headline.v1.json": "b38a728fc73ab01834355b809c3565e3f71bafb0786b5c9bcb26bc38968eb746",
        "tools/size_paper_story_a1_headline.py": "9755faec6f5f3731f2c1eea25c6ce5568c58f6bb344ac30a66f941841e180596",
        "tools/verify_paper_story_a1_headline_sizing.py": "248835d4d7f295a3caa928efe0aa823ff7cc6cdbb895161ca8a33d00ab46ad94",
    }
    for relative, expected_sha in literal_goldens.items():
        assert hashlib.sha256((repo_root / relative).read_bytes()).hexdigest() == expected_sha
    preregistration_root = (
        repo_root
        / "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration"
    )
    assert {
        path.relative_to(repo_root).as_posix()
        for path in preregistration_root.rglob("*")
        if path.is_file()
    } == {
        relative for relative in literal_goldens
        if relative.startswith(
            "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/"
        )
    }


def test_policy_schema_dispatch_preserves_v2_and_rejects_unknown() -> None:
    legacy, legacy_sha = paired.load_policy()
    assert legacy["schema_version"] == "paper-story-a1-paired-policy/v2"
    assert legacy_sha == (
        "83b9c1a1ca4cce1e6394ce3338b491b14663427259eb3e129560fe5b50b99b5b"
    )
    unknown = copy.deepcopy(legacy)
    unknown["schema_version"] = "paper-story-a1-paired-policy/v999"
    with pytest.raises(paired.PaperStoryError, match="unknown"):
        paired._validate_policy_semantics(unknown)


def test_v3_loader_rejects_duplicate_json_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = paired.V3_PILOT_POLICY_PATH.read_text(encoding="utf-8")
    duplicate = raw.replace(
        "{\n",
        '{\n  "schema_version": "paper-story-a1-paired-policy/v3",\n',
        1,
    )
    path = tmp_path / "duplicate-v3.json"
    path.write_text(duplicate, encoding="utf-8")
    monkeypatch.setattr(paired, "V3_PILOT_POLICY_PATH", path)
    with pytest.raises(paired.PaperStoryError, match="duplicate JSON key"):
        paired.load_policy(paired.V3_PILOT_STUDY_ID)


def test_v3_pilot_has_workload_local_exact_role_and_contrast_arms() -> None:
    policy = _v3_pilot_policy()
    assert policy["schema_version"] == "paper-story-a1-paired-policy/v3"
    assert policy["study_id"] == "paper-story-a1-20260901-balanced5-pilot-v1"
    assert policy["campaign_schema"] == "paper-story-a1-paired-campaign/v2"
    assert policy["final_estimate_eligible"] is False
    assert "arms" not in policy
    assert "arm_order" not in policy
    expected = {
        "write-heavy": ("fixed10", 10, "5"),
        "balanced": ("fixed5", 5, "50"),
        "read-heavy": ("fixed2", 2, "95"),
    }
    for workload in policy["workloads"]:
        variant_name, fixed, rratio = expected[workload["name"]]
        assert workload["reps"] == 60
        assert workload["df"] == 59
        assert workload["ycsb_rratio"] == rratio
        assert [
            (arm["name"], arm["role"], arm["contrast"])
            for arm in workload["arms"]
        ] == [
            (variant_name, "variant", "minuend"),
            ("no-backoff", "baseline", "subtrahend"),
        ]
        assert workload["arms"][0]["flags"]["BACKOFF_FIXED"] == fixed
        assert workload["arms"][1]["flags"] == {
            "BACKOFF_FIXED": -1,
            "BACK_OFF": 0,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0,
        }


@pytest.mark.parametrize("forbidden", ("arms", "arm_order"))
def test_v3_rejects_legacy_top_level_arm_fields(forbidden: str) -> None:
    policy = copy.deepcopy(_v3_pilot_policy())
    policy[forbidden] = []
    with pytest.raises(paired.PaperStoryError, match="prohibits top-level"):
        paired._validate_policy_semantics(policy)


def test_v3_loader_accepts_future_sized_policy_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance: certificate-selected n/k/sigma are accepted exactly.
    Rejection: policy drift or an unavailable certificate is rejected.
    """
    prereg_raw = b"synthetic sized preregistration\n"
    prereg_sha = hashlib.sha256(prereg_raw).hexdigest()
    monkeypatch.setattr(paired, "V3_SIZED_PREREGISTRATION_RELATIVE_PATH", "README.md")
    monkeypatch.setattr(paired, "V3_SIZED_PREREGISTRATION_SHA256", prereg_sha)
    sized = copy.deepcopy(_v3_pilot_policy())
    sized["preregistration"] = {"path": paired.V3_SIZED_PREREGISTRATION_RELATIVE_PATH, "sha256": paired.V3_SIZED_PREREGISTRATION_SHA256}
    sized["study_id"] = paired.V3_SIZED_STUDY_ID
    sized["final_estimate_eligible"] = True
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_bytes(prereg_raw)
    pilot_relative = "pilot.json"
    certificate_relative = "sizing-certificate.json"
    pilot = {
        "final_estimate_eligible": False,
        "schema_version": paired.BALANCED_SIZING_PILOT_SCHEMA,
        "study_id": paired.V3_PILOT_STUDY_ID,
        "workloads": [],
    }
    pilot_path = repo / pilot_relative
    pilot_path.write_text(json.dumps(pilot, sort_keys=True) + "\n", encoding="utf-8")
    pilot_sha = hashlib.sha256(pilot_path.read_bytes()).hexdigest()
    certificate = {
        "policy": {
            "search": {"trials": 20000},
            "certification": {"trials": 100000},
            "candidate_grid": {"registered_minimum": 28, "maximum": 4096},
            "root_seed": {
                "digest": "e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3",
            },
        },
        "inputs": {"pilot": {"path": pilot_relative, "sha256": pilot_sha}},
        "schema_version": paired.BALANCED_SIZING_CERTIFICATE_SCHEMA,
        "status": "selected",
        "workloads": [
            {
                "planned_sigma_tps": "100000.0",
                "selected": {"df": 29, "n": 30, "t_critical": "2.0"},
                "status": "selected",
                "workload": name,
            }
            for name in paired.WORKLOAD_ORDER
        ],
    }
    certificate_path = repo / certificate_relative
    certificate_path.write_text(
        json.dumps(certificate, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    certificate_sha = hashlib.sha256(certificate_path.read_bytes()).hexdigest()
    sized["sizing_inputs"] = {
        "pilot_result": {"path": pilot_relative, "sha256": pilot_sha},
        "sizing_certificate": {
            "path": certificate_relative,
            "sha256": certificate_sha,
        },
    }
    for workload in sized["workloads"]:
        workload["reps"] = 30
        workload["df"] = 29
        workload["pair_indices"]["stop_exclusive"] = 30
        workload["k"] = 2.0
        workload["planned_sigma_tps"] = 100_000.0
    path = tmp_path / "paper_story_a1_paired.v3-sized.json"
    path.write_text(
        json.dumps(sized, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(paired, "_repo_root", lambda: repo)
    monkeypatch.setattr(paired, "V3_SIZED_POLICY_PATH", path)
    monkeypatch.setattr(
        paired, "V3_SIZED_POLICY_SHA256",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    loaded, digest = paired.load_policy(paired.V3_SIZED_STUDY_ID)
    assert loaded == sized
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert paired.genomes(loaded, "balanced")[0].flags["BACKOFF_FIXED"] == 5
    for field, value in (("reps", 40), ("k", 2.1), ("planned_sigma_tps", 99999.0)):
        drifted = copy.deepcopy(sized)
        drifted["workloads"][0][field] = value
        if field == "reps":
            drifted["workloads"][0]["df"] = 39
            drifted["workloads"][0]["pair_indices"]["stop_exclusive"] = 40
        with pytest.raises(paired.PaperStoryError, match="certificate"):
            paired._validate_policy_semantics(drifted)
    unavailable = copy.deepcopy(sized)
    unavailable["sizing_inputs"]["sizing_certificate"] = {
        "path": "missing-certificate.json",
        "sha256": "0" * 64,
    }
    with pytest.raises(paired.PaperStoryError, match="unavailable"):
        paired._validate_policy_semantics(unavailable)


@pytest.fixture
def sized_certificate_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Copy frozen inputs; mutations never touch the registered artifacts."""
    policy, _ = paired.load_policy(paired.V3_SIZED_STUDY_ID)
    repo = paired._repo_root()
    for binding in (*policy["sizing_inputs"].values(), policy["preregistration"]):
        destination = tmp_path / binding["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((repo / binding["path"]).read_bytes())
    certificate_path = tmp_path / policy["sizing_inputs"]["sizing_certificate"]["path"]
    certificate = json.loads(certificate_path.read_bytes())
    monkeypatch.setattr(paired, "_repo_root", lambda: tmp_path)
    return policy, certificate, certificate_path


def _rewrite_sized_certificate(policy: dict, certificate: dict, path: Path) -> None:
    raw = (json.dumps(
        certificate, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ) + "\n").encode("utf-8")
    path.write_bytes(raw)
    policy["sizing_inputs"]["sizing_certificate"]["sha256"] = hashlib.sha256(raw).hexdigest()


def test_v3_sized_frozen_policy_loads_with_registered_certificate() -> None:
    policy, digest = paired.load_policy(paired.V3_SIZED_STUDY_ID)
    assert digest == hashlib.sha256(paired.V3_SIZED_POLICY_PATH.read_bytes()).hexdigest()
    assert policy["study_id"] == "paper-story-a1-20260901-balanced5-sized-v1"
    assert policy["authority"] == {
        "formal": False, "promotion_prohibited": True,
        "result_authority": "sized-preregistered-descriptive-only",
    }
    assert policy["final_estimate_eligible"] is True
    assert policy["sizing_inputs"] == {
        "pilot_result": {
            "path": "output/insights/2026-09-01_paper-story-a1-balanced5-pilot/sizing-pilot.json",
            "sha256": "b4201083cc02434b6b300eb24b6916304bfcadc17c7259257e5cf2ee5a7451ed",
        },
        "sizing_certificate": {
            "path": "output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/sizing-certificate.json",
            "sha256": "41d041963c8f3a175b5501810f52ab2619d9285f6f1eeb176790698131fc8299",
        },
    }
    assert [
        (w["name"], w["reps"], w["df"], w["k"], w["planned_sigma_tps"])
        for w in policy["workloads"]
    ] == [
        ("write-heavy", 30, 29, "2.8315526875186725", "66403.452108019716"),
        ("balanced", 30, 29, "2.8315526875186725", "56697.435713574683"),
        ("read-heavy", 30, 29, "2.8315526875186725", "74668.489566274948"),
    ]
    for workload in policy["workloads"]:
        assert workload["pair_indices"] == {"start_inclusive": 0, "stop_exclusive": 30}
    assert policy["execution"]["durable_measurement_base"] == (
        "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement"
    )
    assert policy["execution"]["materialization_relative_path"] == (
        "output/insights/2026-09-13/paper-story-a1-balanced5-sized"
    )
    pilot = _v3_pilot_policy()
    for field in ("durable_measurement_base", "materialization_relative_path"):
        assert policy["execution"][field] != pilot["execution"][field]
    assert policy["sizing"] == pilot["sizing"]


@pytest.mark.parametrize(("section", "field", "value"), [
    pytest.param("search", "trials", 19999, id="search-trials"),
    pytest.param("certification", "trials", 99999, id="certification-trials"),
    pytest.param("candidate_grid", "registered_minimum", 29, id="registered-minimum"),
    pytest.param("candidate_grid", "maximum", 4095, id="maximum"),
    pytest.param("root_seed", "digest", "0" * 64, id="root-seed"),
])
def test_v3_sized_certificate_requires_registered_parameters(
    sized_certificate_copy, section: str, field: str, value: object,
) -> None:
    policy, certificate, path = sized_certificate_copy
    paired._validate_policy_semantics(policy)
    certificate["policy"][section][field] = value
    _rewrite_sized_certificate(policy, certificate, path)
    with pytest.raises(
        paired.PaperStoryError,
        match=rf"registered policy differs: {section}\.{field}$",
    ):
        paired._validate_policy_semantics(policy)


@pytest.mark.parametrize(("section", "field", "expected"), [
    ("search", "trials", 20000),
    ("certification", "trials", 100000),
    ("candidate_grid", "registered_minimum", 28),
    ("candidate_grid", "maximum", 4096),
    ("root_seed", "digest", "e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3"),
])
@pytest.mark.parametrize("mutation", [
    "missing-policy", "missing-section", "non-object-section", "missing-field",
    "bool", "float-or-uppercase", "string-or-int",
])
def test_v3_sized_certificate_rejects_missing_or_mistyped_registered_parameters(
    sized_certificate_copy, section: str, field: str, expected: object, mutation: str,
) -> None:
    policy, certificate, path = sized_certificate_copy
    registered = certificate["policy"]
    if mutation == "missing-policy":
        del certificate["policy"]
    elif mutation == "missing-section":
        del registered[section]
    elif mutation == "non-object-section":
        registered[section] = []
    elif mutation == "missing-field":
        del registered[section][field]
    else:
        registered[section][field] = {
            "bool": True,
            "float-or-uppercase": float(expected) if type(expected) is int else expected.upper(),
            "string-or-int": str(expected) if type(expected) is int else 123,
        }[mutation]
    _rewrite_sized_certificate(policy, certificate, path)
    with pytest.raises(paired.PaperStoryError, match="registered policy differs"):
        paired._validate_policy_semantics(policy)


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("mutation", ["shortest-float", "last-digit"])
def test_v3_sized_certificate_preserves_decimal_statistics(
    sized_certificate_copy, index: int, mutation: str,
) -> None:
    policy, certificate, path = sized_certificate_copy
    sigma = certificate["workloads"][index]["planned_sigma_tps"]
    changed = str(float(sigma)) if mutation == "shortest-float" else sigma + "1"
    assert changed != sigma
    assert float(changed) == float(sigma)
    policy["workloads"][index]["planned_sigma_tps"] = changed
    with pytest.raises(paired.PaperStoryError, match="planned sigma differs from certificate"):
        paired._validate_policy_semantics(policy)
    policy["workloads"][index]["planned_sigma_tps"] = sigma
    certificate["workloads"][index]["planned_sigma_tps"] = changed
    _rewrite_sized_certificate(policy, certificate, path)
    with pytest.raises(paired.PaperStoryError, match="planned sigma differs from certificate"):
        paired._validate_policy_semantics(policy)


@pytest.mark.parametrize("field", ["k", "planned_sigma_tps"])
@pytest.mark.parametrize("value", [
    True, False, None, "not-a-number", "NaN", "Infinity", 0, -1, "0", "-1",
    "1e-999", "1e999", "2_.8315526875186725",
])
def test_v3_sized_statistics_reject_invalid_decimal_values(
    sized_certificate_copy, field: str, value: object,
) -> None:
    policy, certificate, path = sized_certificate_copy
    policy["workloads"][0][field] = value
    # Match the certificate too: underflow must fail before exact-value comparison.
    if field == "k":
        certificate["workloads"][0]["selected"]["t_critical"] = value
    else:
        certificate["workloads"][0][field] = value
    _rewrite_sized_certificate(policy, certificate, path)
    with pytest.raises(paired.PaperStoryError, match=f"v3 sized workload {field}: write-heavy"):
        paired._validate_policy_semantics(policy)


@pytest.mark.parametrize("entry", ["load", "validate"])
def test_v3_sized_policy_bytes_are_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str,
) -> None:
    policy, digest = paired.load_policy(paired.V3_SIZED_STUDY_ID)
    assert paired.V3_SIZED_POLICY_SHA256 == digest
    assert digest == hashlib.sha256(paired.V3_SIZED_POLICY_PATH.read_bytes()).hexdigest()
    policy["workloads"][0]["schedule_root_seed"] = "0" * 64
    path = tmp_path / "drifted-sized.json"
    path.write_text(json.dumps(policy) + "\n", encoding="utf-8")
    monkeypatch.setattr(paired, "V3_SIZED_POLICY_PATH", path)
    with pytest.raises(paired.PaperStoryError, match="tracked policy bytes differ"):
        if entry == "load":
            paired.load_policy(paired.V3_SIZED_STUDY_ID)
        else:
            paired.validate_policy(policy)


def test_v3_sized_preregistration_binding_has_no_policy_self_reference(
    sized_certificate_copy,
) -> None:
    policy, _, _ = sized_certificate_copy
    raw_path = paired._repo_root() / policy["preregistration"]["path"]
    raw = raw_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        policy["preregistration"]["sha256"]
    ) == paired.V3_SIZED_PREREGISTRATION_SHA256 == (
        "6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2"
    )
    assert policy["preregistration"]["path"] == paired.V3_SIZED_PREREGISTRATION_RELATIVE_PATH
    assert hashlib.sha256(paired.V3_SIZED_POLICY_PATH.read_bytes()).hexdigest().encode() not in raw
    raw_path.write_bytes(raw + b"\n")
    with pytest.raises(paired.PaperStoryError, match="human-readable preregistration bytes differ"):
        paired.load_policy(paired.V3_SIZED_STUDY_ID)


@pytest.mark.parametrize("spread", [10.0, 100000.0])
def test_v3_sized_consumer_uses_registered_decimal_statistics(spread: float) -> None:
    policy, _ = paired.load_policy(paired.V3_SIZED_STUDY_ID)
    baseline = [1000000.0] * 30
    variant = [1000100.0 - spread, 1000100.0 + spread] * 15
    result = paired._consumer_positional_statistics(
        policy, "write-heavy", {"no-backoff": baseline, "fixed10": variant},
    )
    expected_sd = spread * math.sqrt(30 / 29)
    expected_half_width = 2.8315526875186725 * expected_sd / math.sqrt(30)
    assert result["n"] == 30
    assert result["df"] == 29
    assert result["mean_signed_positional_difference_tps"] == 100.0
    assert result["sample_sd_positional_difference_tps"] == pytest.approx(expected_sd)
    assert result["k"] == 2.8315526875186725
    assert result["planned_sigma_tps"] == float("66403.452108019716")
    assert result["descriptive_half_width_tps"] == pytest.approx(expected_half_width)
    assert result["descriptive_interval_tps"] == pytest.approx(
        [100.0 - expected_half_width, 100.0 + expected_half_width]
    )
    assert result["floor_boundary_tps"] == 30000.0
    assert result["variance_plan_breach"] is (spread == 100000.0)


def test_v3_sized_schedule_roots_follow_frozen_derivation() -> None:
    policy, _ = paired.load_policy(paired.V3_SIZED_STUDY_ID)
    pilot = _v3_pilot_policy()
    for workload, pilot_workload in zip(policy["workloads"], pilot["workloads"]):
        preimage = (
            "paper-story-a1-balanced5-sized-schedule-root/v1|workload=" + workload["name"]
        ).encode("ascii")
        assert workload["schedule_root_seed"] == hashlib.sha256(preimage).hexdigest()
        assert workload["schedule_root_seed"] != pilot_workload["schedule_root_seed"]
    assert policy["pairing"] == pilot["pairing"]


def test_v3_seed_preimage_is_literal_and_excludes_study_and_date_M4() -> None:
    seed = _v3_pilot_policy()["pairing"]["seed"]
    assert seed["group_preimage"] == (
        "a1-balanced5/v1|workload=<name>|group=<zero-based decimal>"
    )
    assert seed["group_preimage_prohibits"] == ["study ID", "date"]
    schedule = paired._schedule_group_bits(_v3_pilot_policy(), "balanced")
    assert schedule["group_preimages"] == [
        f"a1-balanced5/v1|workload=balanced|group={index}"
        for index in range(6)
    ]
    assert all("20260901" not in item for item in schedule["group_preimages"])
    assert all(
        paired.V3_PILOT_STUDY_ID not in item
        for item in schedule["group_preimages"]
    )


def test_v3_all_identical_seed_bits_are_redrawn_before_schedule_M5() -> None:
    policy = copy.deepcopy(_v3_pilot_policy())
    assert policy["pairing"]["seed"]["all_identical_redraw"][
        "effective_root_seed_preimage"
    ] == "<64-lowercase-hex>|counter=<zero-based decimal>"
    write = next(
        item for item in policy["workloads"] if item["name"] == "write-heavy"
    )
    write["schedule_root_seed"] = (
        "3323f8a3985857bf76df1b28f115cdf70caf2f71a35e3cea0e5583ca6b756962"
    )
    schedule = paired._schedule_group_bits(policy, "write-heavy")
    assert schedule["counter"] == 1
    assert schedule["effective_root_seed"] == (
        "98d1957c592d4ce0d057b1cf2441c1e24ac202326c860f8b7d904857e6fe6efc"
    )
    assert schedule["order_bits"] == [0, 0, 0, 0, 1, 0]
    assert len(set(schedule["order_bits"])) == 2


def test_v3_production_options_use_real_balanced_schedule_and_fail_closed() -> None:
    """Acceptance: v3 selects the real BalancedScheduleConfig and one round.
    Rejection: deleting either registered option is rejected before run_campaign.
    """
    policy = _v3_pilot_policy()
    options = paired._campaign_execution_options(policy, "balanced")
    assert options["bench_max_rounds"] == 1
    assert type(options["balanced_schedule"]) is BalancedScheduleConfig
    assert options["balanced_schedule"] == BalancedScheduleConfig(
        workload="balanced",
        root_seed=paired._workload_plan(
            policy, "balanced",
        )["schedule_root_seed"],
        arm_names=paired._workload_arm_order(policy, "balanced"),
        receipt_name=paired.BALANCED_SCHEDULE_RECEIPT_NAME,
    )
    for missing in ("bench_max_rounds", "balanced_schedule"):
        broken = {key: value for key, value in options.items() if key != missing}
        with pytest.raises(
            paired.PaperStoryError,
            match="must use the registered balanced schedule",
        ):
            paired._require_registered_execution_options(
                policy, "balanced", broken,
            )
    wrong_order = dict(options)
    wrong_order["balanced_schedule"] = replace(
        options["balanced_schedule"],
        arm_names=tuple(reversed(options["balanced_schedule"].arm_names)),
    )
    with pytest.raises(
        paired.PaperStoryError,
        match="must use the registered balanced schedule",
    ):
        paired._require_registered_execution_options(
            policy, "balanced", wrong_order,
        )
    assert paired._campaign_execution_options(_policy(), "balanced") == {}
    assert paired.campaign_config(
        policy, "balanced",
    ).ccbench_commit == paired.CANONICAL_CCBENCH_OID
    assert paired.campaign_config(
        _policy(), "balanced",
    ).ccbench_commit == paired.pin.CURRENT_PIN
    tree = ast.parse(Path(paired.__file__).read_text(encoding="utf-8"))
    measurement = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_measurement"
    )
    collectors = [
        node for node in ast.walk(measurement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "collect_workload"
    ]
    assert len(collectors) == 1
    receipt_keyword = next(
        keyword for keyword in collectors[0].keywords
        if keyword.arg == "expected_schedule_receipt"
    )
    assert any(
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "summary"
        and node.attr == "balanced_schedule_receipt"
        for node in ast.walk(receipt_keyword.value)
    )
    forwarded = {"schema_version": "non-empty-v3-receipt"}
    expression = ast.Expression(body=receipt_keyword.value)
    ast.fix_missing_locations(expression)
    assert eval(  # noqa: S307 - evaluates a reviewed production AST expression
        compile(expression, paired.__file__, "eval"),
        {},
        {"summary": SimpleNamespace(balanced_schedule_receipt=forwarded)},
    ) is forwarded
    assert eval(  # noqa: S307 - same expression, legacy summary contract
        compile(expression, paired.__file__, "eval"),
        {},
        {"summary": SimpleNamespace(balanced_schedule_receipt=None)},
    ) is None


@pytest.mark.parametrize("workload_name", paired.WORKLOAD_ORDER)
def test_v3_schedule_receipt_consumer_binds_placement_and_arm_tps(
    workload_name: str,
) -> None:
    """Acceptance: the frozen receipt and WAL-arm projections agree exactly.
    Rejection: one physical placement mutation makes the receipt invalid.
    """
    policy = _v3_pilot_policy()
    receipt, arm_results = _balanced_receipt_fixture(policy, workload_name)
    assert paired._balanced_schedule_receipt_errors(
        policy, workload_name, receipt, arm_results,
    ) == []
    mutated = copy.deepcopy(receipt)
    expected_arms = paired._workload_arm_order(policy, workload_name)
    mutated["reps"][0]["arm"] = next(
        name for name in expected_arms
        if name != mutated["reps"][0]["arm"]
    )
    assert "schedule-receipt-placement-mismatch" in (
        paired._balanced_schedule_receipt_errors(
            policy, workload_name, mutated, arm_results,
        )
    )
    coerced = copy.deepcopy(receipt)
    coerced["reps"][0]["pair_index"] = False
    assert "schedule-receipt-placement-mismatch" in (
        paired._balanced_schedule_receipt_errors(
            policy, workload_name, coerced, arm_results,
        )
    )


def test_v3_collector_requires_schedule_receipt_and_sizing_projection_is_exact() -> None:
    """Acceptance: a valid receipt projects to the exact sizing pilot schema.
    Rejection: a missing receipt is an explicit collector error.
    """
    policy = _v3_pilot_policy()
    assert paired._balanced_schedule_receipt_errors(
        policy, "write-heavy", None, {},
    ) == ["schedule-receipt-missing"]
    tree = ast.parse(Path(paired.__file__).read_text(encoding="utf-8"))
    collector = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "validate_workload_evidence"
    )
    receipt_calls = [
        node for node in ast.walk(collector)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_balanced_schedule_receipt_errors"
    ]
    assert len(receipt_calls) == 1
    assert [argument.id for argument in receipt_calls[0].args[:2]] == [
        "policy", "workload_name",
    ]

    workloads = []
    receipts = []
    for index, name in enumerate(paired.WORKLOAD_ORDER):
        receipt, arm_results = _balanced_receipt_fixture(policy, name)
        receipts.append(receipt)
        workloads.append({
            "arms": arm_results,
            "campaign_id": f"campaign-{index}",
            "errors": [],
            "schedule_receipt": {"document": receipt},
            "valid": True,
            "workload": name,
        })
    pilot = paired._balanced_sizing_pilot_document(
        policy,
        {"complete": True, "workloads": workloads},
    )
    assert pilot["schema_version"] == paired.BALANCED_SIZING_PILOT_SCHEMA
    assert pilot["final_estimate_eligible"] is False
    assert [item["workload"] for item in pilot["workloads"]] == list(
        paired.WORKLOAD_ORDER
    )
    assert all(
        item["observations"] is receipt["reps"]
        for item, receipt in zip(pilot["workloads"], receipts)
    )
    first = pilot["workloads"][0]["observations"][0]
    assert set(first) == {
        "arm", "block", "block_position", "ended_at_ns", "group",
        "pair_index", "started_at_ns", "tps",
    }
    assert first["arm"] in {"fixed10", "no-backoff"}
    assert first["block"] == first["pair_index"] // 5
    assert first["block_position"] == first["pair_index"] % 5
    publisher = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_publish_materialization_bundle"
    )
    sizing_calls = [
        node for node in ast.walk(publisher)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_balanced_sizing_pilot_document"
    ]
    assert len(sizing_calls) == 1
    assert [argument.id for argument in sizing_calls[0].args] == [
        "policy", "result",
    ]


@pytest.mark.parametrize("workload_name", paired.WORKLOAD_ORDER)
def test_v3_schedule_has_exact_balanced_five_rep_blocks_M8(
    workload_name: str,
) -> None:
    policy = _v3_pilot_policy()
    schedule = paired._balanced_schedule_plan(policy, workload_name)
    variant = paired._workload_arm_by_role(
        policy, workload_name, "variant"
    )["name"]
    baseline = paired._workload_arm_by_role(
        policy, workload_name, "baseline"
    )["name"]
    blocks = schedule["blocks"]
    assert len(blocks) == 24
    assert [block["block_number"] for block in blocks] == list(range(24))
    assert all(block["reps"] == 5 for block in blocks)
    first_roles = [blocks[index]["role"] for index in range(0, 24, 2)]
    assert first_roles.count("variant") == 6
    assert first_roles.count("baseline") == 6
    for group, bit in enumerate(schedule["derivation"]["order_bits"]):
        observed = [block["arm"] for block in blocks[group * 4:group * 4 + 4]]
        assert observed == (
            [variant, baseline, baseline, variant]
            if bit == 0 else
            [baseline, variant, variant, baseline]
        )


def test_v3_sizing_and_ccbench_contract_are_exact_literals() -> None:
    policy = _v3_pilot_policy()
    sizing = policy["sizing"]
    assert sizing["sigma_pair"] == (
        "c(one-sided, alpha_c, df = 59) * sd(60 paired differences)"
    )
    assert sizing["sigma_block"] == (
        "sqrt(5) * c(one-sided, alpha_c, df = 11) * "
        "sd(12 five-pair block means)"
    )
    assert sizing["planned_sigma"] == "max(sigma_pair, sigma_block)"
    assert sizing["alpha_c"] == {"denominator": 20, "numerator": 1}
    assert sizing["n_grid"] == {
        "effective_minimum": 30,
        "maximum": 4096,
        "maximum_candidate": 4090,
        "nominal_minimum": 28,
        "rule": "evaluate operating characteristics only at the actual candidate n",
        "step": 10,
    }
    assert sizing["pilot_pairs_per_workload"] == 60
    assert sizing["pilot_pair_blocks"] == {
        "baseline_first": 6,
        "pairs_per_block": 5,
        "total": 12,
        "variant_first": 6,
    }
    assert policy["ccbench_acceptance"] == {
        "boundaries": paired.V3_CCBENCH_BOUNDARIES,
        "build_preflight_required": True,
        "canonical_pin": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
        "parent_submodule_ignore_independent": True,
        "tracked_clean_required": True,
        "untracked_files_ignored": True,
    }
    assert policy["preregistration"] == {
        "path": paired.V3_PILOT_PREREGISTRATION_RELATIVE_PATH,
        "sha256": paired.V3_PILOT_PREREGISTRATION_SHA256,
    }
    assert paired.V3_PILOT_PREREGISTRATION_RELATIVE_PATH == (
        "output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md"
    )
    assert paired.V3_PILOT_PREREGISTRATION_SHA256 == (
        "8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc"
    )
    paired._require_policy_ready_for_execution(policy)


def test_v3_artifact_consumer_recomputes_contrast_without_producer_helper_M9(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _v3_pilot_policy()
    baseline = [1_000_000.0 + index for index in range(60)]
    variant = [value + 25.0 for value in baseline]
    monkeypatch.setattr(
        paired,
        "positional_statistics",
        lambda *_args, **_kwargs: {"mean_signed_positional_difference_tps": -25.0},
    )
    observed = paired._consumer_positional_statistics(
        policy,
        "write-heavy",
        {"fixed10": variant, "no-backoff": baseline},
    )
    assert observed["mean_signed_positional_difference_tps"] == 25.0
    assert observed["contrast"] == "variant-minus-baseline"
    consumer = next(
        node for node in ast.parse(Path(paired.__file__).read_text()).body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_consumer_positional_statistics"
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "positional_statistics"
        for node in ast.walk(consumer)
    )


def test_historical_v1_is_unchanged_and_inactive() -> None:
    historical = paired.POLICY_PATH.with_name("paper_story_a1_paired.v1.json")
    assert paired.POLICY_PATH != historical
    assert paired.POLICY_PATH.name == "paper_story_a1_paired.v2.json"
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == (
        "0112d4b351096aeca3bbc036735ba244045f512d9f2fb9566ed6b5bbb2648d44"
    )


def test_human_preregistration_binding_has_no_policy_self_reference() -> None:
    preregistration = (
        Path(paired.__file__).resolve().parents[2]
        / paired.PREREGISTRATION_RELATIVE_PATH
    )
    raw = preregistration.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == paired.PREREGISTRATION_SHA256
    assert paired.POLICY_SHA256.encode("ascii") not in raw


@pytest.mark.parametrize(
    "mutation",
    [
        "reps-too-small",
        "df-mismatch",
        "k-mismatch",
        "reps-k-mismatch",
        "pair-range-mismatch",
        "missing-workload",
    ],
)
def test_policy_semantics_reject_incoherent_workload_design(
    mutation: str,
) -> None:
    policy = copy.deepcopy(_policy())
    write = next(
        item for item in policy["workloads"] if item["name"] == "write-heavy"
    )
    if mutation == "reps-too-small":
        write["reps"] = 1
        write["df"] = 0
        write["pair_indices"]["stop_exclusive"] = 1
    elif mutation == "df-mismatch":
        write["df"] = write["reps"]
    elif mutation == "k-mismatch":
        write["k"] = 1.0
    elif mutation == "reps-k-mismatch":
        write["reps"] = 73
        write["df"] = 72
        write["pair_indices"]["stop_exclusive"] = 73
    elif mutation == "pair-range-mismatch":
        write["pair_indices"]["stop_exclusive"] = 71
    else:
        policy["workloads"] = [
            item for item in policy["workloads"]
            if item["name"] != "read-heavy"
        ]
    with pytest.raises(paired.PaperStoryError):
        paired._validate_policy_semantics(policy)


def test_policy_pair_ranges_are_exact_workload_reps() -> None:
    policy = _policy()
    for workload_name, expected_reps in {
        "write-heavy": 72,
        "balanced": 205,
        "read-heavy": 28,
    }.items():
        indices = paired._pair_indices(policy, workload_name)
        assert indices.start == 0
        assert indices.stop == expected_reps
        assert len(indices) == expected_reps


def test_workload_rratio_is_exactly_bound_from_policy_through_campaign_M24() -> None:
    policy = _policy()
    policy_workloads = {
        item["name"]: item for item in policy["workloads"]
    }
    expected_rratios = {
        "write-heavy": "5",
        "balanced": "50",
        "read-heavy": "95",
    }
    assert {
        name: policy_workloads[name]["ycsb_rratio"]
        for name in paired.WORKLOAD_ORDER
    } == expected_rratios

    for name in paired.WORKLOAD_ORDER:
        flags = paired.workload_flags(policy, name)
        configured_workload = paired.campaign_config(
            policy, name
        ).search_config["workload"]
        assert flags["ycsb_rratio"] == expected_rratios[name]
        assert flags["ycsb_rratio"] == policy_workloads[name]["ycsb_rratio"]
        assert configured_workload == {"name": name, **flags}
        assert configured_workload["ycsb_rratio"] == expected_rratios[name]


def test_durable_base_append_preserves_campaign_preimage_and_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _policy()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    current = {
        workload: ident.bind_admission_policy(
            paired.campaign_config(policy, workload), context.policy
        )
        for workload in paired.WORKLOAD_ORDER
    }
    legacy = copy.deepcopy(policy)
    legacy["execution"].pop("durable_measurement_base")
    monkeypatch.setattr(paired, "validate_policy", lambda candidate: candidate)
    baseline = {
        workload: ident.bind_admission_policy(
            paired.campaign_config(legacy, workload), context.policy
        )
        for workload in paired.WORKLOAD_ORDER
    }
    for workload in paired.WORKLOAD_ORDER:
        current_preimage = ident.canonical_preimage(current[workload])
        baseline_preimage = ident.canonical_preimage(baseline[workload])
        assert current_preimage == baseline_preimage
        assert ident.campaign_id(current[workload]) == ident.campaign_id(
            baseline[workload]
        )


@pytest.mark.parametrize(
    ("arm_name", "field", "replacement"),
    [
        ("adaptive", "BACKOFF_FIXED", 0),
        ("static10", "BACKOFF_FIXED", 5),
    ],
    ids=["M1-adaptive-not-minus-one", "M2-static-not-ten"],
)
def test_paired_genomes_are_exact_and_ordered(
    arm_name: str, field: str, replacement: int
) -> None:
    policy = _policy()
    assert [genome.flags["BACKOFF_FIXED"] for genome in paired.genomes(policy)] == [-1, 10]
    mutated = copy.deepcopy(policy)
    arm = next(item for item in mutated["arms"] if item["name"] == arm_name)
    arm["flags"][field] = replacement
    with pytest.raises(paired.PaperStoryError, match="arms"):
        paired.validate_policy(mutated)


def test_campaign_identity_binds_study_and_arms_M3() -> None:
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(
        paired.campaign_config(_policy(), "write-heavy"), context.policy
    )
    preimage = ident.canonical_preimage(cfg)
    assert paired.STUDY_ID in preimage
    for genome in paired.genomes(_policy()):
        assert genome.canonical() in preimage
    without_study = replace(
        cfg,
        search_config={key: value for key, value in cfg.search_config.items() if key != "study_id"},
    )
    without_arms = replace(
        cfg,
        search_config={key: value for key, value in cfg.search_config.items() if key != "arms"},
    )
    assert ident.campaign_id(cfg) != ident.campaign_id(without_study)
    assert ident.campaign_id(cfg) != ident.campaign_id(without_arms)


@pytest.mark.parametrize(
    ("workload_name", "count"),
    [
        ("write-heavy", 71),
        ("write-heavy", 73),
        ("balanced", 204),
        ("balanced", 206),
        ("read-heavy", 27),
        ("read-heavy", 29),
        ("write-heavy", 5),
        ("balanced", 5),
        ("read-heavy", 5),
    ],
)
def test_collector_requires_exact_workload_policy_reps_M4(
    workload_name: str, count: int,
) -> None:
    policy = _policy()
    adaptive = _arm(
        policy, "adaptive", [1_000_000.0] * count,
        workload_name=workload_name,
    )
    result = paired.validate_workload_evidence(
        policy,
        workload_name=workload_name,
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[
            adaptive,
            _arm(policy, "static10", workload_name=workload_name),
        ],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert any(
        "tps-length-or-value-disagrees-with-workload-policy" in error
        for error in result["errors"]
    )


def test_validate_arm_has_an_independent_exact_length_gate_F8() -> None:
    policy = _policy()
    workload_name = "write-heavy"
    reps = paired._expected_reps(policy, workload_name)
    evidence = _arm(
        policy,
        "adaptive",
        [1_000_000.0 + index for index in range(reps + 1)],
        workload_name=workload_name,
    )
    arm_policy = next(
        item for item in policy["arms"] if item["name"] == "adaptive"
    )
    result = paired._validate_arm(
        arm_policy,
        evidence,
        policy=policy,
        workload_name=workload_name,
        env_tag="pegasus",
        source_binding=_source_binding(),
    )
    assert result["errors"] == [
        "tps-length-or-value-disagrees-with-workload-policy"
    ]


def test_positional_statistics_has_an_independent_exact_length_gate_F8() -> None:
    policy = _policy()
    workload_name = "write-heavy"
    reps = paired._expected_reps(policy, workload_name)
    with pytest.raises(
        paired.PaperStoryError,
        match="adaptive length differs from workload policy reps",
    ):
        paired.positional_statistics(
            policy,
            workload_name,
            [1_000_000.0 + index for index in range(reps + 1)],
            [990_000.0 + index for index in range(reps)],
        )


@pytest.mark.parametrize(
    "bad",
    [True, float("nan"), float("inf"), 0.0, -1.0, 10 ** 10000],
    ids=["bool", "nan", "infinity", "zero", "negative", "huge-integer"],
)
def test_collector_rejects_bool_nonfinite_and_nonpositive_M5(bad: object) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    bench = _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"]
    bench["tps"][2] = bad
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert any(
        "tps-length-or-value-disagrees-with-workload-policy" in error
        for error in result["errors"]
    )


@pytest.mark.parametrize("mutation", ["second-attempt", "stage-order"])
def test_collector_rejects_mixed_or_duplicate_attempts_M6(
    tmp_path: Path, mutation: str
) -> None:
    if mutation == "second-attempt":
        def add_second_attempt(frames: list[dict]) -> None:
            first = [
                frame for frame in frames
                if frame["variant"] == "variant-adaptive"
            ]
            second = copy.deepcopy(first)
            second_attempt_id = _attempt_id_fixture("adaptive", ordinal=2)
            for frame in second:
                frame["payload"]["build_attempt_id"] = second_attempt_id
            frames[len(first):len(first)] = second

        result = _production_wal_workload(
            tmp_path, mutate_frames=add_second_attempt
        )
        assert result["valid"] is False
        assert result["errors"] == ["adaptive:attempt-count-not-one"]
        assert result["arms"]["adaptive"]["errors"] == ["attempt-count-not-one"]
        return

    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    frames = adaptive["attempts"][0]["frames"]
    frames[2], frames[3] = frames[3], frames[2]
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert any(
        marker in error
        for error in result["errors"]
        for marker in ("attempt-count-not-one", "stage-sequence-mismatch")
    )


@pytest.mark.parametrize("mutation", ["round-two", "unstable"])
def test_collector_rejects_remeasured_or_unstable_arm_M7(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    bench = _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"]
    commit = _frame_for(adaptive, paired.STAGE_COMMIT)["payload"]
    if mutation == "round-two":
        bench["rounds"] = 2
    else:
        bench["unstable"] = True
        commit["unstable"] = True
    raw = list(bench["tps"])
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert result["arms"]["adaptive"]["raw_tps"] == raw
    assert any(
        marker in error
        for error in result["errors"]
        for marker in ("rounds-not-one", "unstable-not-false")
    )


def test_statistics_keep_static_minus_adaptive_positional_sign_M8() -> None:
    policy = _policy()
    reps = paired._expected_reps(policy, "write-heavy")
    adaptive = [1_000_000.0 + 3.0 * index for index in range(reps)]
    static10 = [999_990.0 + 5.0 * index for index in range(reps)]
    expected_differences = [
        -10.0 + 2.0 * index for index in range(reps)
    ]
    stats = paired.positional_statistics(
        policy,
        "write-heavy",
        adaptive,
        static10,
    )
    assert [pair["signed_difference_tps"] for pair in stats["pairs"]] == (
        expected_differences
    )
    assert stats["mean_signed_positional_difference_tps"] == statistics.fmean(
        expected_differences
    )
    assert "direction" not in stats


@pytest.mark.parametrize("workload_name", paired.WORKLOAD_ORDER)
def test_statistics_use_workload_n_minus_one_and_emit_exact_variance_M9(
    workload_name: str,
) -> None:
    policy = _policy()
    reps = paired._expected_reps(policy, workload_name)
    differences = [float(index) for index in range(1, reps + 1)]
    stats = paired.positional_statistics(
        policy,
        workload_name,
        [1_000_000.0] * reps,
        [1_000_000.0 + value for value in differences],
    )
    assert stats["n"] == reps
    assert stats["df"] == reps - 1
    assert stats["mean_signed_positional_difference_tps"] == statistics.fmean(
        differences
    )
    assert stats["sample_variance_positional_difference_tps2"] == (
        statistics.variance(differences)
    )
    assert stats["sample_sd_positional_difference_tps"] == statistics.stdev(
        differences
    )


@pytest.mark.parametrize(
    ("workload_name", "expected"),
    [
        (
            "write-heavy",
            {
                "adaptive_mean_tps": 1_000_355.0,
                "floor_boundary_tps": 30_010.649999999998,
                "descriptive_half_width_tps": 49.179436265677225,
                "descriptive_interval_tps": [
                    -9_694.179436265676,
                    -9_595.820563734324,
                ],
                "classification": "bounded-below-floor",
            },
        ),
        (
            "balanced",
            {
                "adaptive_mean_tps": 1_001_020.0,
                "floor_boundary_tps": 30_030.6,
                "descriptive_half_width_tps": 81.69119201693485,
                "descriptive_interval_tps": [
                    -9_061.691192016935,
                    -8_898.308807983065,
                ],
                "classification": "bounded-below-floor",
            },
        ),
        (
            "read-heavy",
            {
                "adaptive_mean_tps": 1_000_135.0,
                "floor_boundary_tps": 30_004.05,
                "descriptive_half_width_tps": 31.897009149797125,
                "descriptive_interval_tps": [
                    -9_896.897009149798,
                    -9_833.102990850202,
                ],
                "classification": "bounded-below-floor",
            },
        ),
    ],
)
def test_production_statistics_derive_exact_B_h_interval_and_classification_F4(
    workload_name: str,
    expected: dict[str, object],
) -> None:
    result = _validated_workload(
        workload_name, f"campaign-statistics-{workload_name}"
    )
    assert result["valid"] is True
    statistics_result = result["statistics"]
    assert statistics_result["adaptive_mean_tps"] == expected["adaptive_mean_tps"]
    assert statistics_result["floor_boundary_tps"] == expected[
        "floor_boundary_tps"
    ]
    assert statistics_result["descriptive_half_width_tps"] == expected[
        "descriptive_half_width_tps"
    ]
    assert statistics_result["descriptive_interval_tps"] == expected[
        "descriptive_interval_tps"
    ]
    assert statistics_result["classification"] == expected["classification"]


@pytest.mark.parametrize("sign", [-1.0, 1.0])
def test_classification_boundaries_are_exact_and_prioritized(sign: float) -> None:
    boundary = 30.0
    half_width = 10.0
    above_edge = sign * (boundary + half_width)
    below_edge = sign * (boundary - half_width)
    assert paired._classify_difference(
        above_edge, half_width, boundary
    ) == "unresolved"
    assert paired._classify_difference(
        math.nextafter(above_edge, math.copysign(math.inf, sign)),
        half_width,
        boundary,
    ) == "resolved-above-floor"
    assert paired._classify_difference(
        below_edge, half_width, boundary
    ) == "bounded-below-floor"
    assert paired._classify_difference(
        math.nextafter(below_edge, math.copysign(math.inf, sign)),
        half_width,
        boundary,
    ) == "unresolved"


def test_variance_plan_breach_does_not_override_classification() -> None:
    policy = _policy()
    workload_name = "write-heavy"
    reps = paired._expected_reps(policy, workload_name)
    differences = [
        300_000.0 if index % 2 == 0 else 700_000.0
        for index in range(reps)
    ]
    stats = paired.positional_statistics(
        policy,
        workload_name,
        [1_000_000.0] * reps,
        [1_000_000.0 + value for value in differences],
    )
    assert stats["variance_plan_breach"] is True
    assert stats["classification"] == "resolved-above-floor"


def test_variance_plan_breach_uses_strict_greater_than_boundary_F7() -> None:
    policy = copy.deepcopy(_policy())
    workload = next(
        item for item in policy["workloads"]
        if item["name"] == "write-heavy"
    )
    workload["reps"] = 2
    workload["df"] = 1
    workload["pair_indices"]["stop_exclusive"] = 2
    differences = [2.0, 6.0]
    realized_sd = statistics.stdev(differences)
    workload["planned_sigma_tps"] = realized_sd
    equal = paired.positional_statistics(
        policy,
        "write-heavy",
        [1_000.0, 1_000.0],
        [1_002.0, 1_006.0],
    )
    assert equal["sample_sd_positional_difference_tps"] == realized_sd
    assert equal["planned_sigma_tps"] == realized_sd
    assert equal["variance_plan_breach"] is False

    just_above_policy = copy.deepcopy(policy)
    just_above_workload = next(
        item for item in just_above_policy["workloads"]
        if item["name"] == "write-heavy"
    )
    just_above_workload["planned_sigma_tps"] = math.nextafter(
        realized_sd, -math.inf
    )
    just_above = paired.positional_statistics(
        just_above_policy,
        "write-heavy",
        [1_000.0, 1_000.0],
        [1_002.0, 1_006.0],
    )
    assert just_above["sample_sd_positional_difference_tps"] == realized_sd
    assert just_above["planned_sigma_tps"] == math.nextafter(
        realized_sd, -math.inf
    )
    assert just_above["variance_plan_breach"] is True


@pytest.mark.parametrize("workload_name", paired.WORKLOAD_ORDER)
def test_exact_registered_workload_reps_are_accepted_and_classified(
    workload_name: str,
) -> None:
    result = _validated_workload(workload_name, f"campaign-{workload_name}")
    expected = {"write-heavy": 72, "balanced": 205, "read-heavy": 28}
    assert result["valid"] is True
    assert result["statistics"]["n"] == expected[workload_name]
    adaptive_tps = result["arms"]["adaptive"]["raw_tps"]
    static10_tps = result["arms"]["static10"]["raw_tps"]
    assert len(set(adaptive_tps)) == expected[workload_name]
    assert len(set(static10_tps)) == expected[workload_name]
    assert [
        pair["signed_difference_tps"]
        for pair in result["statistics"]["pairs"]
    ] == [
        -10_000.0 + 10.0 * index
        for index in range(expected[workload_name])
    ]
    assert result["statistics"]["classification"] in {
        "resolved-above-floor",
        "bounded-below-floor",
        "unresolved",
    }
    assert result["terminal_result"] == {
        "status": "valid",
        "classification": result["statistics"]["classification"],
    }


def test_active_statistics_path_has_no_fixed_count_pin() -> None:
    tree = ast.parse(Path(paired.__file__).read_text(encoding="utf-8"))
    targets = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "positional_statistics"
    ]
    assert len(targets) == 1
    constants = [
        node.value for node in ast.walk(targets[0])
        if isinstance(node, ast.Constant)
    ]
    assert 5 not in constants
    assert all(
        "five" not in value.lower()
        for value in constants if type(value) is str
    )
    assert not any(
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Div)
        and isinstance(node.right, ast.Constant)
        and node.right.value == 4
        for node in ast.walk(targets[0])
    )
    arm_validators = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_validate_arm"
    ]
    assert len(arm_validators) == 1
    assert all(
        not (
            isinstance(node, ast.Constant)
            and (
                node.value == 5
                or (type(node.value) is str and "five" in node.value.lower())
            )
        )
        for node in ast.walk(arm_validators[0])
    )


def test_invalid_workload_keeps_independent_terminal_results_M10() -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    workloads[1]["valid"] = False
    workloads[1]["errors"] = ["fixture-invalid"]
    workloads[1]["statistics"] = None
    workloads[1]["terminal_result"] = {
        "status": "invalid",
        "reasons": ["fixture-invalid"],
    }
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        reservation_binding=_reservation_binding(),
        workloads=workloads,
    )
    assert result["complete"] is False
    assert result["all_workloads_terminal"] is True
    assert "cross_workload_conclusion" not in result
    assert workloads[0]["statistics"] is not None
    assert workloads[2]["statistics"] is not None
    assert "invalid: fixture-invalid" in paired._readme(result)


def test_validate_raw_documents_accepts_matching_complete_positive() -> None:
    result, receipt, terminal, policy = _raw_documents()
    assert result["complete"] is True
    assert paired.validate_raw_documents(
        result, receipt, terminal, policy
    ) == (result, receipt, terminal)


def test_validate_raw_documents_accepts_invalid_reason_as_terminal_outcome() -> None:
    result, receipt, terminal, policy = _raw_documents(invalid_workload=True)
    assert result["all_workloads_terminal"] is True
    assert result["complete"] is False
    assert paired.validate_raw_documents(
        result, receipt, terminal, policy
    ) == (result, receipt, terminal)


def test_materializer_rejects_tampered_result_policy_sha() -> None:
    result, receipt, terminal, policy = _raw_documents()
    result["policy_sha256"] = "0" * 64
    with pytest.raises(paired.PaperStoryError, match="result policy hash"):
        paired.validate_raw_documents(result, receipt, terminal, policy)


@pytest.mark.parametrize("field", ["path", "sha256"])
def test_materializer_rejects_tampered_receipt_policy_binding(
    field: str,
) -> None:
    result, receipt, terminal, policy = _raw_documents()
    receipt["policy"][field] = "wrong" if field == "path" else "0" * 64
    with pytest.raises(paired.PaperStoryError, match="receipt policy binding"):
        paired.validate_raw_documents(result, receipt, terminal, policy)


def test_materializer_rejects_tampered_v2_policy_source_binding() -> None:
    result, receipt, terminal, policy = _raw_documents()
    assert paired.POLICY_RELATIVE_PATH.endswith(".v2.json")
    assert paired.POLICY_RELATIVE_PATH in result["source_binding"]["files"]
    result["source_binding"]["files"][paired.POLICY_RELATIVE_PATH][
        "working_sha256"
    ] = "0" * 64
    with pytest.raises(paired.PaperStoryError, match="source bindings differ"):
        paired.validate_raw_documents(result, receipt, terminal, policy)


def test_validate_raw_documents_rejects_reservation_terminal_mismatch() -> None:
    result, receipt, terminal, policy = _raw_documents()
    terminal["reservation_binding"]["nonce"] = "different-attempt"
    with pytest.raises(
        paired.PaperStoryError,
        match="job terminal reservation binding differs from result",
    ):
        paired.validate_raw_documents(result, receipt, terminal, policy)


def test_validate_raw_documents_rejects_claimed_complete_with_invalid_workload_M25(
) -> None:
    result, receipt, terminal, policy = _raw_documents(invalid_workload=True)
    assert result["complete"] is False
    result["complete"] = True
    with pytest.raises(
        paired.PaperStoryError,
        match="top-level complete does not match workload validity",
    ):
        paired.validate_raw_documents(result, receipt, terminal, policy)


def test_validate_raw_documents_rejects_claimed_incomplete_with_all_valid_workloads_M25(
) -> None:
    result, receipt, terminal, policy = _raw_documents()
    assert result["complete"] is True
    result["complete"] = False
    with pytest.raises(
        paired.PaperStoryError,
        match="top-level complete does not match workload validity",
    ):
        paired.validate_raw_documents(result, receipt, terminal, policy)


def test_materialize_refuses_existing_destination_M11(tmp_path: Path) -> None:
    destination = paired.create_materialization_destination(tmp_path / "insight")
    assert destination.is_dir()
    with pytest.raises(paired.PaperStoryError, match="already exists"):
        paired.create_materialization_destination(destination)

    target = tmp_path / "create-only.json"
    paired._exclusive_write(target, {"first": True})
    with pytest.raises(paired.PaperStoryError, match="create-only write refused"):
        paired._exclusive_write(target, {"second": True})


def test_materialization_rejects_bundle_before_all_workloads_are_terminal(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "insight"
    with pytest.raises(
        paired.PaperStoryError,
        match="terminal outcomes for every workload",
    ):
        paired._publish_materialization_bundle(
            destination,
            {"receipt": True},
            {
                "complete": False,
                "all_workloads_terminal": False,
                "workloads": [],
            },
        )
    assert not destination.exists()
    assert list(tmp_path.glob(".insight.staging-*")) == []


def test_materialization_second_publish_to_same_destination_is_rejected(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "insight"
    result = {
        "complete": False,
        "all_workloads_terminal": True,
        "workloads": [],
        "workload_reps": {},
        "limitations": [],
    }
    paired._publish_materialization_bundle(destination, {"receipt": True}, result)
    with pytest.raises(
        paired.PaperStoryError,
        match="no-replace|destination already exists",
    ):
        paired._publish_materialization_bundle(
            destination, {"receipt": True}, result
        )


def test_exclusive_write_bytes_refuses_existing_path_M26(tmp_path: Path) -> None:
    target = tmp_path / "raw-snapshot"
    target.write_bytes(b"original\n")
    with pytest.raises(paired.PaperStoryError, match="create-only write refused"):
        paired._exclusive_write_bytes(target, b"replacement\n")
    assert target.read_bytes() == b"original\n"


def test_exclusive_write_bytes_refuses_final_symlink(tmp_path: Path) -> None:
    target = tmp_path / "raw-snapshot-target"
    target.write_bytes(b"original\n")
    alias = tmp_path / "raw-snapshot-alias"
    alias.symlink_to(target)
    with pytest.raises(paired.PaperStoryError, match="create-only write refused"):
        paired._exclusive_write_bytes(alias, b"replacement\n")
    assert alias.is_symlink()
    assert target.read_bytes() == b"original\n"


def test_materialization_is_exact_leaf_and_noreplace_publish(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    destination = repo / paired.MATERIALIZATION_RELATIVE_PATH
    destination.parent.mkdir(parents=True)
    assert paired._exact_materialization_destination(repo, destination) == destination
    with pytest.raises(paired.PaperStoryError, match="exact A-1 insight leaf"):
        paired._exact_materialization_destination(repo, destination.parent / "other")

    staging = destination.parent / ".a1-staging"
    staging.mkdir()
    paired._exclusive_write(staging / "result.json", {"complete": True})
    paired._exclusive_write(staging / "receipt.json", {"complete": True})
    paired._exclusive_write_text(staging / "README.md", "complete\n")
    paired._publish_complete_staging(staging, destination, {"complete": True})
    assert {path.name for path in destination.iterdir()} == {
        "README.md", "receipt.json", "result.json", paired.COMPLETION_MARKER,
    }

    second = destination.parent / ".a1-staging-second"
    second.mkdir()
    with pytest.raises(paired.PaperStoryError, match="no-replace"):
        paired._publish_staging_noreplace(second, destination)


def test_einval_fallback_publishes_absent_destination_and_records_limits_M37(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "insight"
    calls: list[int] = []

    def einval_then_default(source: Path, target: Path, flags: int) -> None:
        calls.append(flags)
        if flags == paired._RENAME_NOREPLACE:
            raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))
        assert flags == paired._RENAME_DEFAULT
        source.rename(target)

    monkeypatch.setattr(paired, "_renameat2_directory", einval_then_default)
    paired._publish_materialization_bundle(
        destination,
        {"receipt": True},
        {
            "complete": False,
            "all_workloads_terminal": True,
            "limitations": [],
        },
    )

    assert calls == [paired._RENAME_NOREPLACE, paired._RENAME_DEFAULT]
    assert destination.is_dir()
    result = json.loads((destination / "result.json").read_text(encoding="utf-8"))
    publish = result["materialization_evidence"]["publish"]
    assert publish["selected_mechanism"] == paired.PUBLISH_EINVAL_FALLBACK
    assert publish["selection_observation"] == {
        "rename_noreplace_attempted": True,
        "errno": "EINVAL",
    }
    assert any(
        "not atomic no-replace against a non-cooperating writer" in limitation
        for limitation in publish["limitations"]
    )
    assert any(
        "not atomic no-replace against a non-cooperating destination writer"
        in limitation
        for limitation in result["limitations"]
    )
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "RENAME_NOREPLACE was attempted" in readme
    assert "returned EINVAL" in readme
    assert "may be replaced" in readme
    completion = json.loads(
        (destination / paired.COMPLETION_MARKER).read_text(encoding="utf-8")
    )
    assert completion["publish"] == publish


def test_einval_fallback_refuses_existing_destination_M36(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "insight"
    destination.mkdir()
    original_identity = destination.stat().st_ino
    calls: list[int] = []

    def einval_then_overwriting_default(
        source: Path, target: Path, flags: int
    ) -> None:
        calls.append(flags)
        if flags == paired._RENAME_NOREPLACE:
            raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))
        assert flags == paired._RENAME_DEFAULT
        source.rename(target)

    monkeypatch.setattr(
        paired, "_renameat2_directory", einval_then_overwriting_default
    )
    with pytest.raises(
        paired.PaperStoryError,
        match="fallback materialization publish refused: destination already exists",
    ):
        paired._publish_materialization_bundle(
            destination,
            {"receipt": True},
            {
                "complete": False,
                "all_workloads_terminal": True,
                "limitations": [],
            },
        )

    assert calls == [paired._RENAME_NOREPLACE]
    assert destination.is_dir()
    assert destination.stat().st_ino == original_identity
    assert list(destination.iterdir()) == []


def test_unpublished_materialization_staging_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "insight"
    staging = tmp_path / f".insight.staging-{os.getpid()}"

    def refuse_publish(source: Path, target: Path) -> None:
        assert source == staging
        assert target == destination
        raise paired.PaperStoryError("injected publish refusal")

    monkeypatch.setattr(paired, "_publish_staging_noreplace", refuse_publish)
    monkeypatch.setattr(
        paired,
        "_observe_materialization_publish",
        lambda target: paired._materialization_publish_evidence(
            paired.PUBLISH_RENAME_NOREPLACE
        ),
    )
    with pytest.raises(paired.PaperStoryError, match="injected publish refusal"):
        paired._publish_materialization_bundle(
            destination,
            {"receipt": True},
            {"complete": False, "all_workloads_terminal": True},
        )
    assert not staging.exists()
    assert not destination.exists()


def test_publish_error_after_rename_does_not_remove_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "insight"

    def rename_then_report_error(source: Path, target: Path) -> None:
        source.rename(target)
        raise paired.PaperStoryError("injected post-rename error")

    monkeypatch.setattr(
        paired, "_publish_staging_noreplace", rename_then_report_error
    )
    monkeypatch.setattr(
        paired,
        "_observe_materialization_publish",
        lambda target: paired._materialization_publish_evidence(
            paired.PUBLISH_RENAME_NOREPLACE
        ),
    )
    with pytest.raises(paired.PaperStoryError, match="injected post-rename error"):
        paired._publish_materialization_bundle(
            destination,
            {"receipt": True},
            {"complete": False, "all_workloads_terminal": True},
        )
    assert destination.is_dir()
    assert paired.COMPLETION_MARKER in {
        path.name for path in destination.iterdir()
    }


def test_revalidate_raw_wals_accepts_exact_producer_layout_for_all_workloads_B11(
    tmp_path: Path,
) -> None:
    output_root = (tmp_path / "campaign-output").resolve()
    workloads = [
        _production_wal_workload(tmp_path, name)
        for name in paired.WORKLOAD_ORDER
    ]
    for workload in workloads:
        relative = Path(workload["wal_evidence"]["path"]).resolve().relative_to(
            output_root
        )
        assert relative.parts == (
            "exploration",
            "campaigns",
            workload["campaign_id"],
            "runs",
            "wal.jsonl",
        )

    paired._revalidate_raw_wals(
        {"workloads": workloads, "source_binding": _source_binding()},
        {"roots": {"output_root": os.fspath(output_root)}},
    )


def test_raw_wal_rederivation_rejects_self_consistent_stored_reclassification(
    tmp_path: Path,
) -> None:
    output_root = (tmp_path / "campaign-output").resolve()
    workload = _production_wal_workload(tmp_path, "write-heavy")
    original = workload["statistics"]["classification"]
    replacement = (
        "unresolved" if original != "unresolved" else "bounded-below-floor"
    )
    workload["statistics"]["classification"] = replacement
    workload["terminal_result"]["classification"] = replacement
    assert paired._workload_has_terminal_result(workload)
    with pytest.raises(
        paired.PaperStoryError,
        match="raw WAL snapshot",
    ):
        paired._revalidate_raw_wals(
            {"workloads": [workload], "source_binding": _source_binding()},
            {"roots": {"output_root": os.fspath(output_root)}},
        )


def test_raw_wal_rederivation_does_not_preserve_stored_campaign_errors_F1(
    tmp_path: Path,
) -> None:
    output_root = (tmp_path / "campaign-output").resolve()
    workload = _production_wal_workload(tmp_path, "write-heavy")
    workload["valid"] = False
    workload["errors"] = ["campaign-error:forged"]
    workload["statistics"] = None
    workload["terminal_result"] = {
        "status": "invalid",
        "reasons": ["campaign-error:forged"],
    }
    assert paired._workload_has_terminal_result(workload)
    with pytest.raises(
        paired.PaperStoryError,
        match="raw WAL snapshot",
    ):
        paired._revalidate_raw_wals(
            {"workloads": [workload], "source_binding": _source_binding()},
            {"roots": {"output_root": os.fspath(output_root)}},
        )


def test_raw_wal_rederivation_rejects_stored_raw_tps_statistics_and_terminal_F2(
    tmp_path: Path,
) -> None:
    output_root = (tmp_path / "campaign-output").resolve()
    workload = _production_wal_workload(tmp_path, "write-heavy")
    policy = _policy()
    reps = paired._expected_reps(policy, "write-heavy")
    stored_adaptive = [
        1_200_000.0 + 3.0 * index for index in range(reps)
    ]
    stored_static10 = [
        1_190_000.0 + 8.0 * index for index in range(reps)
    ]
    workload["arms"]["adaptive"]["raw_tps"] = stored_adaptive
    workload["arms"]["static10"]["raw_tps"] = stored_static10
    workload["statistics"] = paired.positional_statistics(
        policy,
        "write-heavy",
        stored_adaptive,
        stored_static10,
    )
    workload["terminal_result"] = {
        "status": "valid",
        "classification": workload["statistics"]["classification"],
    }
    assert paired._workload_has_terminal_result(workload)

    result, receipt, terminal, raw_policy = _raw_documents()
    result["workloads"][0] = workload
    assert paired.validate_raw_documents(
        result, receipt, terminal, raw_policy
    ) == (result, receipt, terminal)
    with pytest.raises(
        paired.PaperStoryError,
        match="raw WAL snapshot",
    ):
        paired._revalidate_raw_wals(
            {"workloads": [workload], "source_binding": _source_binding()},
            {"roots": {"output_root": os.fspath(output_root)}},
        )


def test_production_materialize_route_calls_raw_wal_rederivation_F2() -> None:
    tree = ast.parse(Path(paired.__file__).read_text(encoding="utf-8"))
    materializer = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_materialize"
    )
    rederivations = [
        node
        for node in ast.walk(materializer)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_revalidate_raw_wals"
        )
    ]
    assert len(rederivations) == 1
    assert [argument.id for argument in rederivations[0].args] == [
        "result",
        "receipt",
        "policy",
    ]
    publishes = [
        node
        for node in ast.walk(materializer)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_publish_materialization_bundle"
        )
    ]
    assert len(publishes) == 1
    assert rederivations[0].lineno < publishes[0].lineno


def test_v3_non_certifying_completion_rederives_with_tracked_policy() -> None:
    tree = ast.parse(Path(paired.__file__).read_text(encoding="utf-8"))
    consumer = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_validate_non_certifying_observation_contents"
    )
    calls = [
        node for node in ast.walk(consumer)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_revalidate_raw_wals"
    ]
    assert len(calls) == 1
    assert [argument.id for argument in calls[0].args] == [
        "result", "receipt", "policy",
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong-exploration",
        "wrong-campaigns",
        "wrong-runs",
        "extra-depth",
    ],
)
def test_raw_wal_layout_rejects_noncanonical_descendant_M34(
    tmp_path: Path, mutation: str,
) -> None:
    output_root = (tmp_path / "campaign-output").resolve()
    output_root.mkdir()
    campaign_id = "paper-story-a1-write-heavy-paired-fixture"
    relative = {
        "wrong-exploration": Path(
            "archive", "campaigns", campaign_id, "runs", "wal.jsonl"
        ),
        "wrong-campaigns": Path(
            "exploration", "archive", campaign_id, "runs", "wal.jsonl"
        ),
        "wrong-runs": Path(
            "exploration", "campaigns", campaign_id, "archive", "wal.jsonl"
        ),
        "extra-depth": Path(
            "exploration", "campaigns", campaign_id, "extra", "runs", "wal.jsonl"
        ),
    }[mutation]

    with pytest.raises(
        paired.PaperStoryError,
        match="WAL evidence is not in the canonical campaign layout",
    ):
        paired._canonical_workload_wal_layout(
            resolved_wal_path=output_root / relative,
            output_root=output_root,
            campaign_id=campaign_id,
        )


def test_raw_wal_layout_rejects_other_workload_campaign_id_M35(
    tmp_path: Path,
) -> None:
    output_root = (tmp_path / "campaign-output").resolve()
    write_heavy = _production_wal_workload(tmp_path, "write-heavy")
    balanced = _production_wal_workload(tmp_path, "balanced")
    assert write_heavy["campaign_id"] != balanced["campaign_id"]

    with pytest.raises(
        paired.PaperStoryError,
        match="WAL evidence campaign ID differs from workload",
    ):
        paired._canonical_workload_wal_layout(
            resolved_wal_path=Path(balanced["wal_evidence"]["path"]).resolve(),
            output_root=output_root,
            campaign_id=write_heavy["campaign_id"],
        )


def test_completion_marker_is_present_at_single_publish_boundary_M17(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / "staging"
    destination = tmp_path / "published"
    staging.mkdir()
    for name in ("README.md", "receipt.json", "result.json"):
        (staging / name).write_text(name, encoding="utf-8")
    observed: dict[str, set[str]] = {}

    def inspect_publish(source: Path, target: Path) -> None:
        assert source == staging
        assert target == destination
        observed["files"] = {path.name for path in source.iterdir()}
        source.rename(target)

    monkeypatch.setattr(paired, "_publish_staging_noreplace", inspect_publish)
    paired._publish_complete_staging(
        staging,
        destination,
        {"complete": True},
        paired._materialization_publish_evidence(
            paired.PUBLISH_RENAME_NOREPLACE
        ),
    )
    assert observed["files"] == {
        "README.md", "receipt.json", "result.json", paired.COMPLETION_MARKER,
    }
    assert {path.name for path in destination.iterdir()} == observed["files"]


def test_production_wal_bytes_positive_fixture(tmp_path: Path) -> None:
    result = _production_wal_workload(tmp_path)
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["campaign_binding"]["canonical_preimage"]
    assert result["wal_evidence"]["line_issues"] == []
    assert result["wal_evidence"]["truncated_tail"] is False


def test_trace0_accepts_actual_pegasus_no_perf_nine_token_run_argv_positive(
    tmp_path: Path,
) -> None:
    result = _production_wal_workload(tmp_path)
    evidence = result["arms"]["adaptive"]["performance_trace0_evidence"]
    configure_argv = shlex.split(evidence["perf_configure_cmd"])
    assert configure_argv[0:2] == [
        "/toolchain/cmake", "-S",
    ]
    assert len(configure_argv) == 16
    assert configure_argv[9].startswith("-DCMAKE_PREFIX_PATH=")
    prefix_paths = configure_argv[9].split("=", 1)[1].split(";")
    assert [Path(item).name for item in prefix_paths] == [
        "gflags-install", "glog-install",
    ]
    assert Path(prefix_paths[0]).parent == Path(prefix_paths[1]).parent
    run_argv = shlex.split(evidence["bench_run_cmd"])
    contract = paired.p2_2.env_contract.lookup("pegasus")
    assert len(run_argv) == 9
    assert Path(run_argv[0]).name == "ycsb_silo.exe"
    assert run_argv[1:] == [
        "-thread_num=48",
        "-ycsb_tuple_num=1000000",
        "-extime=3",
        f"-clocks_per_us={contract.clocks_per_us}",
        "-ycsb_zipf_skew=0.9",
        "-ycsb_rratio=5",
        "-ycsb_rmw=0",
        "-ycsb_max_ope=10",
    ]
    assert result["valid"] is True


def test_trace0_accepts_exact_perf_run_when_observation_requires_perf(
    tmp_path: Path,
) -> None:
    def mutate(frames: list[dict]) -> None:
        bench = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BENCH_DONE
        )["payload"]
        bench["perf_observation"]["use_perf"] = True
        bench["run_cmd"] = " ".join([
            "perf", "stat", "-e", ",".join(calibrator_runner.PERF_EVENTS), "--",
            bench["run_cmd"],
        ])

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["valid"] is True


def test_trace0_run_argv_requires_exact_token_count_and_positions_M30(
    tmp_path: Path,
) -> None:
    def mutate(frames: list[dict]) -> None:
        bench = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BENCH_DONE
        )["payload"]
        bench["run_cmd"] = f"/bin/echo {bench['run_cmd']}"

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


def test_campaign_lock_identity_preimage_is_compared_exactly_M31(
    tmp_path: Path,
) -> None:
    result = _production_wal_workload(
        tmp_path,
        expected_preimage_transform=lambda preimage: preimage + " ",
    )
    assert result["errors"] == ["campaign-lock-preimage-mismatch"]
    assert all(arm["valid"] is True for arm in result["arms"].values())


def test_trace0_rejects_dependency_prefix_token_outside_index_nine_M29(
    tmp_path: Path,
) -> None:
    def mutate(frames: list[dict]) -> None:
        build = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BUILD_DONE
        )["payload"]
        configure_argv = shlex.split(build["perf_configure_cmd"])
        prefix_token = configure_argv.pop(9)
        configure_argv.append(prefix_token)
        build["perf_configure_cmd"] = shlex.join(configure_argv)

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


@pytest.mark.parametrize(
    "mutation",
    [
        "separated-define",
        "typed-define",
        "joined-undefine",
        "separated-undefine",
        "extra-source",
        "unknown-configure-option",
        "unknown-build-option",
        "unknown-run-option",
    ],
)
def test_trace0_token_allowlist_rejects_every_unregistered_token_M18(
    tmp_path: Path, mutation: str
) -> None:
    def mutate(frames: list[dict]) -> None:
        adaptive = [
            frame for frame in frames if frame["variant"] == "variant-adaptive"
        ]
        build = next(
            frame for frame in adaptive if frame["stage"] == paired.STAGE_BUILD_DONE
        )["payload"]
        bench = next(
            frame for frame in adaptive if frame["stage"] == paired.STAGE_BENCH_DONE
        )["payload"]
        if mutation == "separated-define":
            build["perf_configure_cmd"] = build["perf_configure_cmd"].replace(
                "-DCCBENCH_TRACE=0", "-D CCBENCH_TRACE=0"
            )
        elif mutation == "typed-define":
            build["perf_configure_cmd"] = build["perf_configure_cmd"].replace(
                "-DCCBENCH_TRACE=0", "-DCCBENCH_TRACE:BOOL=0"
            )
        elif mutation == "joined-undefine":
            build["perf_configure_cmd"] += " -UCCBENCH_TRACE"
        elif mutation == "separated-undefine":
            build["perf_configure_cmd"] += " -U CCBENCH_TRACE"
        elif mutation == "extra-source":
            build["perf_configure_cmd"] += " -S /other-source"
        elif mutation == "unknown-configure-option":
            build["perf_configure_cmd"] += " --future-configure-option"
        elif mutation == "unknown-build-option":
            build["perf_build_cmd"] += " --future-build-option"
        else:
            bench["run_cmd"] += " -future_workload_knob=1"

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


def test_trace0_rejects_unregistered_ccbench_define_M13(tmp_path: Path) -> None:
    def mutate(frames: list[dict]) -> None:
        build = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BUILD_DONE
        )
        build["payload"]["perf_configure_cmd"] += " -DCCBENCH_UNREGISTERED=1"

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


def test_trace0_requires_canonical_argv0_M14(tmp_path: Path) -> None:
    def mutate(frames: list[dict]) -> None:
        bench = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BENCH_DONE
        )
        bench["payload"]["run_cmd"] = (
            f"/bin/echo {bench['payload']['run_cmd']}"
        )

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]
    assert result["arms"]["static10"]["valid"] is True


@pytest.mark.parametrize(
    "mutation", ["build-directory", "binary-sha", "binary-unreadable"]
)
def test_trace0_binds_build_directory_and_binary_bytes(
    tmp_path: Path, mutation: str
) -> None:
    def mutate(frames: list[dict]) -> None:
        build = next(
            frame for frame in frames
            if frame["variant"] == "variant-adaptive"
            and frame["stage"] == paired.STAGE_BUILD_DONE
        )
        if mutation == "build-directory":
            assert _TEST_BUILD_DIR is not None
            other = (tmp_path / "other-build").resolve()
            build["payload"]["perf_build_cmd"] = build["payload"][
                "perf_build_cmd"
            ].replace(os.fspath(_TEST_BUILD_DIR), os.fspath(other))
        elif mutation == "binary-sha":
            build["payload"]["perf_bin_sha256"] = "f" * 64
        else:
            assert _TEST_BUILD_DIR is not None
            (
                _TEST_BUILD_DIR
                / "adaptive" / "cc" / "silo" / "ycsb_silo.exe"
            ).unlink()

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["errors"] == ["adaptive:trace0-source-route-incomplete"]


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("unbound-stage", "stage-sequence-mismatch"),
        ("duplicate-macro", "trace0-source-route-incomplete"),
        ("wrong-workload-argv", "trace0-source-route-incomplete"),
        ("huge-integer", "tps-length-or-value-disagrees-with-workload-policy"),
    ],
)
def test_production_wal_mutations_are_invalid(
    tmp_path: Path, mutation: str, expected: str
) -> None:
    def mutate(frames: list[dict]) -> None:
        adaptive = [frame for frame in frames if frame["variant"] == "variant-adaptive"]
        if mutation == "unbound-stage":
            extra = copy.deepcopy(next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_VERIFY_DONE
            ))
            extra["payload"].pop("build_attempt_id")
            frames.insert(frames.index(adaptive[-2]), extra)
        elif mutation == "duplicate-macro":
            build = next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_BUILD_DONE
            )
            build["payload"]["perf_configure_cmd"] += " -DCCBENCH_BACKOFF_FIXED=0"
        elif mutation == "wrong-workload-argv":
            bench = next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_BENCH_DONE
            )
            bench["payload"]["run_cmd"] = bench["payload"]["run_cmd"].replace(
                "-ycsb_rratio=5", "-ycsb_rratio=95"
            )
        else:
            bench = next(
                frame for frame in adaptive if frame["stage"] == paired.STAGE_BENCH_DONE
            )
            bench["payload"]["tps"][2] = 10 ** 400

    result = _production_wal_workload(tmp_path, mutate_frames=mutate)
    assert result["valid"] is False
    assert any(expected in error for error in result["errors"])


def test_invalid_wal_tail_preserves_snapshot_forensics(tmp_path: Path) -> None:
    result = _production_wal_workload(tmp_path, raw_suffix="{")
    assert result["valid"] is False
    assert result["wal_evidence"]["truncated_tail"] is True
    assert len(result["wal_evidence"]["records"]) == 10


def test_clean_exact_two_arm_three_workload_positive_case() -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    assert all(item["valid"] is True for item in workloads)
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        reservation_binding=_reservation_binding(),
        workloads=workloads,
    )
    assert result["complete"] is True
    assert result["all_workloads_terminal"] is True
    assert "cross_workload_conclusion" not in result
    readme = paired._readme(result)
    assert "No cross-workload conclusion is produced" in readme
    for workload_name, reps in {"write-heavy": 72, "balanced": 205, "read-heavy": 28}.items():
        assert f"| {workload_name} | valid | {reps} |" in readme
        workload = next(
            item for item in result["workloads"]
            if item["workload"] == workload_name
        )
        interval = workload["statistics"]["descriptive_interval_tps"]
        assert f"[{interval[0]:.6f}, {interval[1]:.6f}]" in readme
        assert workload["statistics"]["classification"] in readme
    assert paired.PREREGISTERED_LIMITATIONS in readme
    assert "five" not in readme.lower()


def test_result_and_readme_disclose_nqsv_observation_scope() -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        reservation_binding=_reservation_binding(),
        workloads=workloads,
    )
    assert result["pbs_evidence_scope"] == paired._json_safe(
        paired.PBS_EVIDENCE_SCOPE
    )
    scheduler_terminal = {
        "terminal_reason": "request-disappeared-after-visibility",
        "qstat_visible": False,
        "qstat_rc": 0,
        "state": {"observed": False},
        "exit_status": {"observed": False},
        "observed_epoch": 2,
        "qstat_stdout": (
            "Batch Request: 944956.nqsv does not exist on nqsv.\n"
        ),
        "qstat_stdout_sha256": "e" * 64,
    }
    materialized = paired._materialized_result(
        result,
        {"scheduler_terminal": scheduler_terminal},
        {"driver_rc": 0, "shell_rc": 0, "status": "finished"},
    )
    evidence = materialized["materialization_evidence"]
    assert evidence["derivation"] == {
        "authoritative_input": "raw WAL byte sequence",
        "workload_rederivation": "recollected from raw WAL before publish",
        "result_receipt_comparison": "self-consistency check only",
        "independent_evidence_claimed": False,
    }
    assert evidence["scheduler_terminal"] == scheduler_terminal
    terminal_forms = evidence["interpretation"]["terminal_forms"]
    assert set(terminal_forms) == {
        "scheduler-end-state",
        "request-disappeared-after-visibility",
    }
    assert "explicitly unobserved" in terminal_forms[
        "request-disappeared-after-visibility"
    ]
    assert evidence["job_terminal_outcome"] == {
        "driver_rc": 0,
        "shell_rc": 0,
        "status": "finished",
    }
    assert "driver_rc=0, shell_rc=0" in evidence["interpretation"]["job_outcome"]
    readme = paired._readme(result)
    assert "PBS_O_QUEUE is not exported" in readme
    assert "stdout/stderr FD targets are not the qsub -o/-e delivery files" in readme
    assert "scheduler completion receipt SHA-256" in readme
    assert "later absent from qstat" in readme
    assert "explicitly recorded as unobserved" in readme
    assert "driver_rc=0, shell_rc=0" in readme
    source = Path(paired.__file__).read_text(encoding="utf-8")
    materializer = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "run_materialize"
    )
    publish = next(
        node
        for node in ast.walk(materializer)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_publish_materialization_bundle"
        )
    )
    materialized_result = publish.args[2]
    assert isinstance(materialized_result, ast.Call)
    assert isinstance(materialized_result.func, ast.Name)
    assert materialized_result.func.id == "_materialized_result"
    assert [argument.id for argument in materialized_result.args] == [
        "result", "completion", "terminal",
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [("driver_rc", True), ("driver_rc", 1), ("shell_rc", 1)],
)
def test_materializer_requires_exact_zero_driver_and_shell_rc(
    field: str, value: object
) -> None:
    policy, policy_sha = paired.load_policy()
    workloads = [
        _validated_workload(name, f"campaign-{index}")
        for index, name in enumerate(paired.WORKLOAD_ORDER)
    ]
    result = paired.assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=_source_binding(),
        reservation_binding=_reservation_binding(),
        workloads=workloads,
    )
    receipt = {
        "schema_version": paired.RECEIPT_SCHEMA,
        "study_id": paired.STUDY_ID,
        "formal": False,
        "promotion_prohibited": True,
        "policy": {
            "path": paired.POLICY_RELATIVE_PATH,
            "sha256": paired.POLICY_SHA256,
        },
        "pbs_jobid": "12345.nqsv",
        "source_binding": _source_binding(),
        "roots": {"completion_receipt": "/durable/attempt.completion.json"},
        "submission_receipt": {"sha256": "d" * 64},
    }
    terminal = {
        "schema_version": paired.JOB_TERMINAL_SCHEMA,
        "study_id": paired.STUDY_ID,
        "pbs_jobid": "12345.nqsv",
        "expected_head": "a" * 40,
        "observed_head": "a" * 40,
        "porcelain": "",
        "driver_rc": 0,
        "shell_rc": 0,
        "status": "finished",
        "terminal_source_binding": _source_binding(),
        "completion_receipt_path": "/durable/attempt.completion.json",
        "submission_receipt_sha256": "d" * 64,
    }
    terminal[field] = value
    with pytest.raises(paired.PaperStoryError, match="finished raw bundle"):
        paired.validate_raw_documents(result, receipt, terminal, policy)


def test_positive_fixture_does_not_authorize_absent_settled_or_returncodes() -> None:
    result = _validated_workload()
    assert result["valid"] is True
    for arm in result["arms"].values():
        assert arm["rep_notes"] == []
        assert "settled" not in arm
        assert "rep_returncodes" not in arm


def test_collector_rejects_third_arm_and_missing_arm() -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    static10 = _arm(policy, "static10")
    third = copy.deepcopy(static10)
    third["name"] = "third"
    third["variant"] = "variant-third"
    for arms in ([adaptive], [adaptive, static10, third]):
        result = paired.validate_workload_evidence(
            policy,
            workload_name="write-heavy",
            campaign_id="campaign-a",
            env_tag="pegasus",
            arms=arms,
            wal_evidence={},
            source_binding=_source_binding(),
        )
        assert result["valid"] is False
        assert any("variant-set-cardinality" in error for error in result["errors"])


@pytest.mark.parametrize("mutation", ["uncertified", "abort"])
def test_collector_rejects_uncertified_or_abort(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    if mutation == "uncertified":
        _frame_for(adaptive, paired.STAGE_VERIFY_DONE)["payload"]["certified"] = False
    else:
        terminal = _frame_for(adaptive, paired.STAGE_COMMIT)
        terminal["stage"] = paired.STAGE_ABORT
        terminal["payload"] = {
            "build_attempt_id": adaptive["attempts"][0]["build_attempt_id"],
            "reason": "verifier-red",
        }
        adaptive["last_terminal_stage"] = paired.STAGE_ABORT
        adaptive["last_stage"] = paired.STAGE_ABORT
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False


@pytest.mark.parametrize("mutation", ["rep-notes", "commit-fitness", "verify-projection"])
def test_collector_rejects_diagnostic_or_commit_projection_drift(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    if mutation == "rep-notes":
        _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"]["rep_notes"] = [
            "rep failed"
        ]
    elif mutation == "commit-fitness":
        _frame_for(adaptive, paired.STAGE_COMMIT)["payload"]["fitness_tps"] += 1
    else:
        _frame_for(adaptive, paired.STAGE_COMMIT)["payload"]["verify_configs"] = []
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={"path": "/raw/wal", "size": 9, "sha256": "4" * 64},
        source_binding=_source_binding(),
    )
    assert result["valid"] is False
    assert result["wal_evidence"]["sha256"] == "4" * 64


@pytest.mark.parametrize("mutation", ["trace-one", "missing-run-cmd", "bad-source"])
def test_trace0_is_source_routed_and_never_standalone(mutation: str) -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    binding = _source_binding()
    if mutation == "trace-one":
        build = _frame_for(adaptive, paired.STAGE_BUILD_DONE)["payload"]
        build["perf_configure_cmd"] = build["perf_configure_cmd"].replace(
            "-DCCBENCH_TRACE=0", "-DCCBENCH_TRACE=1"
        )
    elif mutation == "missing-run-cmd":
        _frame_for(adaptive, paired.STAGE_BENCH_DONE)["payload"].pop("run_cmd")
    else:
        binding["artifact_standalone_proof"] = True
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=binding,
    )
    assert result["valid"] is False
    assert any("trace0-source-route-incomplete" in error for error in result["errors"])


@pytest.mark.parametrize("mutation", ["formal-missing", "promotion-flipped"])
def test_m_nc01_a1_marker_rejected_before_lock_preseed(
    tmp_path: Path, mutation: str,
) -> None:
    policy = _policy()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    configs = [
        ident.bind_admission_policy(
            paired.campaign_config(policy, name, non_certifying=True),
            context.policy,
        )
        for name in paired.WORKLOAD_ORDER
    ]
    search = dict(configs[0].search_config)
    if mutation == "formal-missing":
        search.pop("formal")
    else:
        search["promotion_prohibited"] = False
    configs[0] = replace(configs[0], search_config=search)
    layouts = [
        exploration_campaign_layout(f"campaign-{index}", tmp_path)
        for index in range(3)
    ]
    with pytest.raises(paired.PaperStoryError, match="marker differs"):
        paired._preseed_a1_non_certifying_locks(
            configs=configs,
            layouts=layouts,
            workloads=paired.WORKLOAD_ORDER,
            common_record={},
        )
    assert all(not Path(layout.lock_file).exists() for layout in layouts)


def test_a1_exact_marker_routes_loop_to_dedicated_replay_and_append(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _policy()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = paired.campaign_config(
        policy, paired.WORKLOAD_ORDER[0], non_certifying=True,
    )
    events = []

    def authorize(bound_cfg, *_args, **_kwargs):
        return campaign_loop._AuthorizationResult(
            authorized_contract=SimpleNamespace(),
            execution_receipt=None,
            bound_cfg=bound_cfg,
            campaign_identity=str(ident.campaign_id(bound_cfg)),
        )

    @contextmanager
    def unlocked(_path):
        yield

    @contextmanager
    def dedicated_io(layout):
        events.append("dedicated-io")
        token = wal._A1_IO_LAYOUT.set(os.fspath(layout.root))
        try:
            yield
        finally:
            wal._A1_IO_LAYOUT.reset(token)

    def dedicated_replay(*_args, **_kwargs):
        events.append("dedicated-replay")
        return {}

    def dedicated_append(_layout, record, *, commit_receipt=None):
        assert commit_receipt is None
        events.append(f"dedicated-append:{record.stage}")
        return record

    monkeypatch.setattr(campaign_loop, "_authorize_measurement", authorize)
    monkeypatch.setattr(campaign_loop, "campaign_lock", unlocked)
    monkeypatch.setattr(wal, "a1_non_certifying_io", dedicated_io)
    monkeypatch.setattr(wal, "replay_a1_non_certifying", dedicated_replay)
    monkeypatch.setattr(
        wal, "replay", lambda *_args, **_kwargs: pytest.fail("generic replay used"),
    )
    monkeypatch.setattr(wal, "append_a1_non_certifying", dedicated_append)
    monkeypatch.setattr(
        ident,
        "ensure_resumable_wal",
        lambda *_args, **_kwargs: SimpleNamespace(status="clean"),
    )
    monkeypatch.setattr(
        campaign_loop.source_digest,
        "resolve_evidence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("focused identity failure")
        ),
    )
    summary = campaign_loop.run_campaign(
        cfg,
        [paired.Genome("focused", {})],
        SimpleNamespace(),
        "pegasus",
        1,
        do_bench=False,
        output_root=os.fspath(tmp_path / "campaign-output"),
        authorization_contract=object(),
        build_context=context,
        declared_use_class="exploration",
        log=lambda *_args: None,
    )
    assert summary.aborted == 1
    assert events == [
        "dedicated-io",
        "dedicated-replay",
        f"dedicated-append:{paired.STAGE_BUILD_START}",
        f"dedicated-append:{paired.STAGE_ABORT}",
    ]


def test_noncertifying_sidecar_positive_and_exact_type_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, workloads, common = _noncertifying_bundle(tmp_path, monkeypatch)
    assert all(item["valid"] is True for item in workloads)
    view = paired.consume_non_certifying_observation(sidecar)
    assert type(view) is paired.NonCertifyingObservationView
    sidecar_document = json.loads(sidecar.read_bytes())
    assert set(sidecar_document["source_binding"]["files"]) == set(
        paired.NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    )
    assert view.common_record["mode"] == common["mode"]
    assert tuple(view.common_record["campaign_ids"]) == tuple(
        common["campaign_ids"]
    )
    with pytest.raises(TypeError):
        view.result["complete"] = False
    with pytest.raises(TypeError, match="専用consumer"):
        paired.NonCertifyingObservationView(
            sidecar_path=sidecar,
            common_record=common,
            campaigns=(),
            result={},
            receipt={},
            _token=object(),
        )
    from orchestrator.campaign import artifact_admission
    with pytest.raises(TypeError, match="exact CertifiedCampaignView"):
        artifact_admission.require_certified_campaign_view(view)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("completion-missing", "completion receipt is missing"),
        ("submission-sha", "submission receipt digest differs"),
        ("scheduler-exit", "visible scheduler terminal observation differs"),
        ("job-terminal-missing", "job terminal is missing"),
    ],
)
def test_final_noncertifying_view_requires_real_terminal_receipt_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    sidecar, _workloads, _common = _noncertifying_bundle(tmp_path, monkeypatch)
    value = json.loads(sidecar.read_bytes())
    receipt = json.loads(Path(value["receipt"]["path"]).read_bytes())
    roots = receipt["roots"]
    if mutation == "completion-missing":
        Path(roots["completion_receipt"]).unlink()
    elif mutation == "submission-sha":
        Path(roots["submission_receipt"]).write_bytes(b"tampered submission\n")
    elif mutation == "scheduler-exit":
        completion_path = Path(roots["completion_receipt"])
        completion = json.loads(completion_path.read_bytes())
        completion["scheduler_terminal"]["exit_status"]["value"] = 1
        completion_path.write_bytes(paired._canonical_json_bytes(completion))
    else:
        (Path(roots["raw_root"]) / "job-terminal.json").unlink()
    with pytest.raises(paired.PaperStoryError, match=message):
        paired.consume_non_certifying_observation(sidecar)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("request", "Request ID: 54321.nqsv"),
        ("state", "State: RUN"),
        ("exit", "Exit Status: 1"),
    ],
)
def test_final_noncertifying_view_reparses_scheduler_terminal_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    replacement: str,
) -> None:
    sidecar, _workloads, _common = _noncertifying_bundle(tmp_path, monkeypatch)
    value = json.loads(sidecar.read_bytes())
    receipt = json.loads(Path(value["receipt"]["path"]).read_bytes())
    completion_path = Path(receipt["roots"]["completion_receipt"])
    completion = json.loads(completion_path.read_bytes())
    terminal = completion["scheduler_terminal"]
    request_id = completion["request_id"]
    original = {
        "request": f"Request ID: {request_id}",
        "state": "State: EXT",
        "exit": "Exit Status: 0",
    }[field]
    terminal["qstat_stdout"] = terminal["qstat_stdout"].replace(
        original, replacement,
    )
    terminal["qstat_stdout_sha256"] = hashlib.sha256(
        terminal["qstat_stdout"].encode()
    ).hexdigest()
    completion_path.write_bytes(paired._canonical_json_bytes(completion))

    with pytest.raises(
        paired.PaperStoryError,
        match="visible scheduler terminal observation differs",
    ):
        paired.consume_non_certifying_observation(sidecar)


def test_run_complete_uses_raw_sidecar_gate_then_enables_final_view(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, _workloads, common = _noncertifying_bundle(tmp_path, monkeypatch)
    value = json.loads(sidecar.read_bytes())
    receipt = json.loads(Path(value["receipt"]["path"]).read_bytes())
    completion_path = Path(receipt["roots"]["completion_receipt"])
    completion_path.unlink()
    request_id = receipt["pbs_jobid"]
    stdout = (
        f"Request ID: {request_id}\nState: EXT\nExit Status: 0\n"
    )
    original_run = paired.subprocess.run

    def run_with_terminal_qstat(argv, *args, **kwargs):
        if list(argv) == ["qstat", "-f", request_id]:
            return SimpleNamespace(
                args=argv, returncode=0, stdout=stdout, stderr="",
            )
        return original_run(argv, *args, **kwargs)

    monkeypatch.setattr(
        paired.subprocess,
        "run",
        run_with_terminal_qstat,
    )
    assert paired.run_complete(SimpleNamespace(
        expected_head=common["source_commit"],
        attempt_root=receipt["roots"]["attempt_root"],
    )) == 0
    assert completion_path.is_file()
    assert type(
        paired.consume_non_certifying_observation(sidecar)
    ) is paired.NonCertifyingObservationView


def test_m_nc03_observation_tag_tamper_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, _workloads, _common = _noncertifying_bundle(tmp_path, monkeypatch)
    value = json.loads(sidecar.read_bytes())
    tag = value["observation_tag"]
    value["observation_tag"] = ("0" if tag[0] != "0" else "1") + tag[1:]
    sidecar.write_bytes(paired._canonical_json_bytes(value))
    with pytest.raises(paired.PaperStoryError, match="tag mismatch"):
        paired.consume_non_certifying_observation(sidecar)


def test_m_nc03_sidecar_decodes_lock_before_reading_bound_wal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, _workloads, _common = _noncertifying_bundle(tmp_path, monkeypatch)
    value = json.loads(sidecar.read_bytes())
    lock_path = Path(value["campaigns"][0]["campaign_lock"]["path"])
    lock = json.loads(lock_path.read_bytes())
    tag = lock["a1_non_certifying"]["identity_tag"]
    lock["a1_non_certifying"]["identity_tag"] = (
        ("0" if tag[0] != "0" else "1") + tag[1:]
    )
    lock_path.write_text(campaign_lock.canonical_json(lock), encoding="utf-8")
    value["campaigns"][0]["campaign_lock"]["sha256"] = hashlib.sha256(
        lock_path.read_bytes()
    ).hexdigest()
    value["observation_tag"] = paired._observation_identity_tag(value)
    sidecar.write_bytes(paired._canonical_json_bytes(value))
    original = paired._read_observation_binding

    def refuse_wal(binding, *, label):
        if label == "wal":
            pytest.fail("sidecar read WAL before dedicated lock rejection")
        return original(binding, label=label)

    monkeypatch.setattr(paired, "_read_observation_binding", refuse_wal)
    with pytest.raises(paired.PaperStoryError, match="campaign lock is invalid"):
        paired.consume_non_certifying_observation(sidecar)


def test_m_nc05_commit_receipt_rejects_retagged_lock_with_unchanged_wal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _sidecar, workloads, common = _noncertifying_bundle(tmp_path, monkeypatch)
    binding = workloads[0]["campaign_binding"]
    lock_path = Path(binding["campaign_lock_path"])
    decoded = campaign_lock.decode_non_certifying_campaign_lock(
        lock_path.read_text(encoding="utf-8")
    )
    changed = dict(common)
    changed["source_binding_sha256"] = "0" * 64
    lock_path.write_text(
        campaign_lock.encode_non_certifying_campaign_lock(
            decoded.identity_preimage,
            common_record=changed,
            workload_binding=decoded.workload_binding,
        ),
        encoding="utf-8",
    )
    with pytest.raises(wal.AttemptTopologyError, match="lock SHA"):
        wal.replay_a1_non_certifying(
            paired.CampaignLayout(binding["layout_root"]),
            admission_policy=build_run_context(
                generator_id=GeneratorId.BACKOFF_SWEEP
            ).policy,
        )


def test_m_nc06_sidecar_campaign_digest_replacement_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, _workloads, _common = _noncertifying_bundle(tmp_path, monkeypatch)
    value = json.loads(sidecar.read_bytes())
    value["campaigns"][1]["wal"]["sha256"] = "0" * 64
    value["observation_tag"] = paired._observation_identity_tag(value)
    sidecar.write_bytes(paired._canonical_json_bytes(value))
    with pytest.raises(paired.PaperStoryError, match="wal digest"):
        paired.consume_non_certifying_observation(sidecar)


def test_m_nc04_common_prereg_replacement_is_rederived_and_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, _workloads, _common = _noncertifying_bundle(tmp_path, monkeypatch)
    value = json.loads(sidecar.read_bytes())
    changed_common = dict(value["common_record"])
    changed_common["preregistration_sha256"] = "0" * 64
    result_path = Path(value["result"]["path"])
    result = json.loads(result_path.read_bytes())
    for ordinal, campaign in enumerate(value["campaigns"]):
        lock_path = Path(campaign["campaign_lock"]["path"])
        decoded = campaign_lock.decode_non_certifying_campaign_lock(
            lock_path.read_text(encoding="utf-8")
        )
        lock_path.write_text(
            campaign_lock.encode_non_certifying_campaign_lock(
                decoded.identity_preimage,
                common_record=changed_common,
                workload_binding=decoded.workload_binding,
            ),
            encoding="utf-8",
        )
        lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
        campaign["campaign_lock"]["sha256"] = lock_sha
        result["workloads"][ordinal]["campaign_binding"][
            "campaign_lock_sha256"
        ] = lock_sha
    paired._exclusive_write(result_path.with_suffix(".replacement"), result)
    replacement_path = result_path.with_suffix(".replacement")
    value["result"] = {
        "path": os.fspath(replacement_path),
        "sha256": hashlib.sha256(replacement_path.read_bytes()).hexdigest(),
    }
    receipt_path = Path(value["receipt"]["path"])
    receipt = json.loads(receipt_path.read_bytes())
    receipt["result"] = {
        "path": value["result"]["path"],
        "sha256": value["result"]["sha256"],
        "complete": result["complete"],
        "all_workloads_terminal": result["all_workloads_terminal"],
    }
    replacement_receipt = receipt_path.with_suffix(".replacement")
    paired._exclusive_write(replacement_receipt, receipt)
    value["receipt"] = {
        "path": os.fspath(replacement_receipt),
        "sha256": hashlib.sha256(replacement_receipt.read_bytes()).hexdigest(),
    }
    value["common_record"] = changed_common
    value["observation_tag"] = paired._observation_identity_tag(value)
    sidecar.write_bytes(paired._canonical_json_bytes(value))
    with pytest.raises(paired.PaperStoryError, match="common/source binding"):
        paired.consume_non_certifying_observation(sidecar)


def test_historical_v2_collector_accepts_verify_payload_without_anomalies() -> None:
    policy = _policy()
    adaptive = _arm(policy, "adaptive")
    assert "anomalies" not in _frame_for(
        adaptive, paired.STAGE_VERIFY_DONE,
    )["payload"]
    result = paired.validate_workload_evidence(
        policy,
        workload_name="write-heavy",
        campaign_id="campaign-a",
        env_tag="pegasus",
        arms=[adaptive, _arm(policy, "static10")],
        wal_evidence={},
        source_binding=_source_binding(),
    )
    assert result["valid"] is True


@pytest.mark.parametrize(
    ("anomalies", "accepted"),
    [
        pytest.param(0, True, id="exact-int-zero"),
        pytest.param(_MISSING, False, id="missing"),
        pytest.param(False, False, id="bool-false"),
        pytest.param(True, False, id="bool-true"),
        pytest.param(1, False, id="int-one"),
    ],
)
def test_m_nc07_decoded_noncertifying_lock_scopes_collector_anomaly_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    anomalies: object,
    accepted: bool,
) -> None:
    _sidecar, workloads, _common = _noncertifying_bundle(
        tmp_path, monkeypatch, anomalies=anomalies,
    )
    assert workloads[0]["valid"] is accepted
    anomaly_errors = [
        error for error in workloads[0]["errors"]
        if "verify-anomalies-not-zero" in error
    ]
    assert bool(anomaly_errors) is (not accepted)


def test_m_nc07_anomaly_is_independently_rejected_by_sidecar_consumer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, workloads, _common = _noncertifying_bundle(
        tmp_path, monkeypatch, anomalies=1,
    )
    assert workloads[0]["valid"] is False
    with pytest.raises(paired.PaperStoryError, match="anomalies are nonzero"):
        paired.consume_non_certifying_observation(sidecar)


def _v3_accounting_fixture() -> dict:
    return {
        "method": "bash-times-delta-reaped-descendants/v1",
        "started_epoch_s": 100.0,
        "ended_epoch_s": 111.0,
        "started_monotonic_s": 20.0,
        "ended_monotonic_s": 31.0,
        "elapsed_s": 11.0,
        "shell_user_s": 1.0,
        "shell_system_s": 2.0,
        "reaped_descendants_user_s": 3.0,
        "reaped_descendants_system_s": 4.0,
        "cpu_total_s": 10.0,
        "times_baseline_raw": "0m1.000s 0m2.000s\n0m3.000s 0m4.000s",
        "times_final_raw": "0m2.000s 0m4.000s\n0m6.000s 0m8.000s",
        "unreaped_descendants": [],
    }


def _v3_job_executions_fixture(attempt: Path | None = None) -> list[dict]:
    attempt_name = attempt.name if attempt is not None else "attempt"
    return [
        {
            "workload": workload,
            "ordinal": ordinal,
            "request_id": f"{123 + ordinal}.server",
            "reservation_binding": {
                **_reservation_binding(),
                "job_id": f"{123 + ordinal}.server",
                "nonce": f"{attempt_name}.{workload}",
            },
            "accounting": _v3_accounting_fixture(),
        }
        for ordinal, workload in enumerate(paired.WORKLOAD_ORDER)
    ]


def test_mf1_request_ids_are_unique_only_after_nqsv_normalization_M1_M2() -> None:
    accepted = _v3_job_executions_fixture()
    assert paired._validate_v3_job_executions(accepted) == accepted

    aliased = copy.deepcopy(accepted)
    aliased[1]["request_id"] = "0:123.server"
    aliased[1]["reservation_binding"]["job_id"] = "0:123.server"
    with pytest.raises(paired.PaperStoryError, match="normalized request IDs"):
        paired._validate_v3_job_executions(aliased)


def test_mf3_accounting_recomputes_baseline_delta_and_rejects_unreaped_M5_M6() -> None:
    accounting = _v3_accounting_fixture()
    assert paired._validate_v3_accounting(accounting) == accounting

    absolute = copy.deepcopy(accounting)
    absolute["shell_user_s"] = 2.0
    absolute["cpu_total_s"] = 11.0
    with pytest.raises(paired.PaperStoryError, match="baseline times delta"):
        paired._validate_v3_accounting(absolute)

    unreaped = copy.deepcopy(accounting)
    unreaped["unreaped_descendants"] = [4321]
    with pytest.raises(paired.PaperStoryError, match="unreaped descendants"):
        paired._validate_v3_accounting(unreaped)


def test_v3_job_execution_ordinal_swap_is_rejected_M7() -> None:
    executions = _v3_job_executions_fixture()
    executions[0], executions[1] = executions[1], executions[0]
    with pytest.raises(paired.PaperStoryError, match="workload ordinal"):
        paired._validate_v3_job_executions(executions)


def test_v3_fan_in_result_replaces_single_reservation_and_readme_lists_accounting(
) -> None:
    policy = _v3_pilot_policy()
    workloads = [
        {
            "workload": workload,
            "campaign_id": f"campaign-{ordinal}",
            "campaign_binding": {"wal_path": f"/wal/{workload}"},
            "valid": True,
            "statistics": {
                "n": 20,
                "mean_signed_positional_difference_tps": 1.0,
                "descriptive_interval_tps": None,
                "floor_boundary_tps": 2.0,
                "classification": "pilot-sizing-input-only",
                "variance_plan_breach": False,
            },
            "errors": [],
            "terminal_result": {
                "status": "valid",
                "classification": "pilot-sizing-input-only",
            },
        }
        for ordinal, workload in enumerate(paired.WORKLOAD_ORDER)
    ]
    executions = _v3_job_executions_fixture()
    result = paired.assemble_result(
        policy,
        policy_sha256="a" * 64,
        source_binding=_source_binding(),
        job_executions=executions,
        workloads=workloads,
    )
    assert "reservation_binding" not in result
    assert result["job_executions"] == executions
    readme = paired._readme(result)
    assert "## Job accounting" in readme
    for ordinal, workload in enumerate(paired.WORKLOAD_ORDER):
        assert f"| {workload} | {123 + ordinal}.server |" in readme


def test_v3_fan_in_rejects_a_single_group_reservation() -> None:
    policy = _v3_pilot_policy()
    workloads = [
        {
            "workload": workload,
            "campaign_id": f"campaign-{ordinal}",
            "campaign_binding": {"wal_path": f"/wal/{workload}"},
            "valid": True,
            "statistics": {"classification": "pilot-sizing-input-only"},
            "errors": [],
            "terminal_result": {
                "status": "valid",
                "classification": "pilot-sizing-input-only",
            },
        }
        for ordinal, workload in enumerate(paired.WORKLOAD_ORDER)
    ]
    with pytest.raises(paired.PaperStoryError, match="must not claim one"):
        paired.assemble_result(
            policy,
            policy_sha256="a" * 64,
            source_binding=_source_binding(),
            reservation_binding=_reservation_binding(),
            job_executions=_v3_job_executions_fixture(),
            workloads=workloads,
        )


def test_v3_materializer_revalidates_group_sidecar_and_workload_wals() -> None:
    tree = ast.parse(
        Path(paired.__file__).read_text(encoding="utf-8")
    )
    materializer = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_run_materialize_v3"
    )
    called = {
        node.func.id
        for node in ast.walk(materializer)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "validate_raw_documents" in called
    assert "_validate_v3_group_completion" in called
    assert "consume_non_certifying_observation" in called
    assert "_revalidate_raw_wals" in called


def _barrier_ready_fixture(
    *, attempt: Path, workload: str, submission: dict, campaign_id: str,
) -> dict:
    ordinal = paired.WORKLOAD_ORDER.index(workload)
    return {
        "schema_version": paired.V3_READY_SCHEMA,
        "study_id": paired.V3_PILOT_STUDY_ID,
        "source_commit": "a" * 40,
        "attempt_root": os.fspath(attempt),
        "workload": workload,
        "ordinal": ordinal,
        "request_id": submission["jobs"][ordinal]["request_id"],
        "reservation_nonce": f"{attempt.name}.{workload}",
        "campaign_id": campaign_id,
        "prepared_arms": [
            {
                "variant": f"variant-{arm}",
                "build_attempt_id": f"attempt-{arm}",
                "build_admission_receipt_sha256": str(arm + 1) * 64,
                "verify_tags": list(paired.EXPECTED_VERIFY_CONFIGS),
            }
            for arm in range(2)
        ],
        "recorded_epoch": 1,
    }


def test_mf2_ready_exact_triple_precedes_bench_go_and_start_M3(tmp_path: Path) -> None:
    attempt = tmp_path / "attempt"
    (attempt / "barrier" / "ready").mkdir(parents=True)
    (attempt / "barrier" / "bench-start").mkdir()
    (attempt / "jobs").mkdir()
    for workload in paired.WORKLOAD_ORDER:
        (attempt / "jobs" / workload).mkdir()
    submission = {
        "jobs": [
            {"request_id": f"{123 + ordinal}.server"}
            for ordinal, _ in enumerate(paired.WORKLOAD_ORDER)
        ],
    }
    campaign_ids = [f"campaign-{ordinal}" for ordinal in range(3)]
    for workload in paired.WORKLOAD_ORDER[1:]:
        ready = _barrier_ready_fixture(
            attempt=attempt, workload=workload, submission=submission,
            campaign_id=campaign_ids[paired.WORKLOAD_ORDER.index(workload)],
        )
        paired._exclusive_write(
            Path(paired._v3_job_roots(attempt, workload)["ready"]), ready,
        )
    prepared = [
        SimpleNamespace(
            result=SimpleNamespace(variant=f"variant-{arm}"),
            build_attempt_id=f"attempt-{arm}",
            build_admission_receipt_sha256=str(arm + 1) * 64,
            verify_tags=list(paired.EXPECTED_VERIFY_CONFIGS),
        )
        for arm in range(2)
    ]
    reservation = {
        **_reservation_binding(),
        "job_id": "123.server",
        "nonce": f"{attempt.name}.write-heavy",
    }
    paired._v3_barrier_before_bench(
        prepared_arms=prepared, workload="write-heavy",
        campaign_id=campaign_ids[0], policy=_v3_pilot_policy(),
        source_commit="a" * 40, attempt=attempt, submission=submission,
        reservation=reservation, timeout_s=0.1,
    )
    assert (attempt / "barrier" / "bench-go.json").is_file()
    assert (attempt / "barrier" / "bench-start" / "write-heavy.json").is_file()


def test_mf2_one_ready_cannot_publish_bench_go_M3(tmp_path: Path) -> None:
    attempt = tmp_path / "attempt"
    (attempt / "barrier" / "ready").mkdir(parents=True)
    (attempt / "barrier" / "bench-start").mkdir()
    (attempt / "jobs").mkdir()
    for workload in paired.WORKLOAD_ORDER:
        (attempt / "jobs" / workload).mkdir()
    submission = {"jobs": [
        {"request_id": f"{123 + ordinal}.server"} for ordinal in range(3)
    ]}
    prepared = [
        SimpleNamespace(
            result=SimpleNamespace(variant=f"variant-{arm}"),
            build_attempt_id=f"attempt-{arm}",
            build_admission_receipt_sha256=str(arm + 1) * 64,
            verify_tags=list(paired.EXPECTED_VERIFY_CONFIGS),
        )
        for arm in range(2)
    ]
    with pytest.raises(paired.PaperStoryError, match="ready triple"):
        paired._v3_barrier_before_bench(
            prepared_arms=prepared, workload="write-heavy",
            campaign_id="campaign-0", policy=_v3_pilot_policy(),
            source_commit="a" * 40, attempt=attempt, submission=submission,
            reservation={
                **_reservation_binding(), "job_id": "123.server",
                "nonce": f"{attempt.name}.write-heavy",
            },
            timeout_s=0.0,
        )
    assert not (attempt / "barrier" / "bench-go.json").exists()


def test_mf2_prior_same_study_bench_start_blocks_new_attempt_M4(
    tmp_path: Path,
) -> None:
    base = tmp_path / "measurement"
    prior = base / "prior"
    bench_root = prior / "barrier" / "bench-start"
    bench_root.mkdir(parents=True)
    paired._exclusive_write(bench_root / "write-heavy.json", {
        "schema_version": paired.V3_BENCH_START_SCHEMA,
        "study_id": paired.V3_PILOT_STUDY_ID,
        "source_commit": "a" * 40,
        "attempt_root": os.fspath(prior),
        "workload": "write-heavy",
        "ordinal": 0,
        "request_id": "123.server",
        "bench_go_sha256": "1" * 64,
        "ready_sha256": "2" * 64,
        "recorded_epoch": 1,
    })
    with pytest.raises(paired.PaperStoryError, match="group rerun is prohibited"):
        paired._assert_no_prior_v3_bench_start(
            base, study_id=paired.V3_PILOT_STUDY_ID,
            current_attempt=base / "new-attempt",
        )


def test_f1_prior_bench_barrier_blocks_with_empty_or_missing_start_M8(
    tmp_path: Path,
) -> None:
    for reach_evidence in ("bench-go", "ready-triple"):
        base = tmp_path / reach_evidence / "measurement"
        prior = base / "prior"
        barrier = prior / "barrier"
        ready_root = barrier / "ready"
        ready_root.mkdir(parents=True)
        if reach_evidence == "bench-go":
            (barrier / "bench-start").mkdir()
            paired._exclusive_write(barrier / "bench-go.json", {
                "schema_version": paired.V3_BENCH_GO_SCHEMA,
                "study_id": paired.V3_PILOT_STUDY_ID,
                "source_commit": "a" * 40,
                "attempt_root": os.fspath(prior),
                "ready": [
                    {
                        "workload": workload,
                        "ordinal": ordinal,
                        "campaign_id": f"campaign-{workload}",
                        "path": os.fspath(ready_root / f"{workload}.json"),
                        "sha256": str(ordinal + 1) * 64,
                    }
                    for ordinal, workload in enumerate(paired.WORKLOAD_ORDER)
                ],
            })
        else:
            for ordinal, workload in enumerate(paired.WORKLOAD_ORDER):
                paired._exclusive_write(ready_root / f"{workload}.json", {
                    "schema_version": paired.V3_READY_SCHEMA,
                    "study_id": paired.V3_PILOT_STUDY_ID,
                    "source_commit": "a" * 40,
                    "attempt_root": os.fspath(prior),
                    "workload": workload,
                    "ordinal": ordinal,
                    "request_id": f"{100 + ordinal}.server",
                    "reservation_nonce": f"{prior.name}.{workload}",
                    "campaign_id": f"campaign-{workload}",
                    "prepared_arms": [
                        {
                            "variant": f"variant-{arm}",
                            "build_attempt_id": f"attempt-{arm}",
                            "build_admission_receipt_sha256": str(index + 1) * 64,
                            "verify_tags": list(paired.EXPECTED_VERIFY_CONFIGS),
                        }
                        for index, arm in enumerate(paired.ARM_ORDER)
                    ],
                    "recorded_epoch": 1,
                })
            assert not (barrier / "bench-start").exists()
        with pytest.raises(
            paired.PaperStoryError, match="group rerun is prohibited",
        ):
            paired._assert_no_prior_v3_bench_start(
                base, study_id=paired.V3_PILOT_STUDY_ID,
                current_attempt=base / "new-attempt",
            )


def test_f1_first_submit_has_no_prior_attempt_and_is_accepted_M8(
    tmp_path: Path,
) -> None:
    paired._assert_no_prior_v3_bench_start(
        tmp_path / "measurement",
        study_id=paired.V3_PILOT_STUDY_ID,
        current_attempt=tmp_path / "measurement" / "first-attempt",
    )


def test_submit_parser_rejects_missing_study_id_M1() -> None:
    """Acceptance: submit remains available when a study ID is explicit.
    Rejection: omitting --study-id fails argument parsing with exit code 2.
    """
    with pytest.raises(SystemExit) as exc_info:
        paired._parser().parse_args([
            "submit",
            "--expected-head", "a" * 40,
            "--attempt-root", "/x",
        ])
    assert exc_info.value.code == 2


def test_submit_parser_accepts_each_explicit_study_id() -> None:
    """Acceptance: every supported study ID can be selected explicitly.
    Rejection: the required option must not narrow its parse-time value set.
    """
    parser = paired._parser()
    for study_id in (
        paired.STUDY_ID,
        paired.V3_PILOT_STUDY_ID,
        paired.V3_SIZED_STUDY_ID,
    ):
        parsed = parser.parse_args([
            "submit",
            "--study-id", study_id,
            "--expected-head", "a" * 40,
            "--attempt-root", "/x",
        ])
        assert parsed.study_id == study_id


def test_run_submit_rejects_missing_study_id_attribute_M2() -> None:
    """Acceptance: run_submit consumes an explicitly supplied study_id attribute.
    Rejection: a missing attribute fails before policy loading without a fallback.
    """
    args = SimpleNamespace(expected_head="a" * 40, attempt_root="/x")
    with pytest.raises(AttributeError, match="study_id"):
        paired.run_submit(args)


def test_f3_v2_measure_rejects_explicit_workload_selector_M10() -> None:
    with pytest.raises(
        paired.PaperStoryError, match=r"v2 measure does not accept --workload",
    ):
        paired.run_measurement(SimpleNamespace(
            study_id=paired.STUDY_ID,
            workload="balanced",
        ))
    parsed = paired._parser().parse_args([
        "measure",
        "--study-id", paired.STUDY_ID,
        "--expected-head", "a" * 40,
        "--pbs-jobid", "123.server",
        "--acquisition-receipt", "/receipt",
        "--acquisition-receipt-sha256", "b" * 64,
        "--output-root", "/output",
        "--cache-root", "/cache",
        "--result-root", "/result",
        "--dependency-prefix", "/dependency",
    ])
    assert parsed.workload is None


@pytest.mark.parametrize("admitted", (True, False))
def test_f4_v3_backoff_gate_calls_real_family_before_measurement_M11(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    admitted: bool,
) -> None:
    repo = tmp_path / "repo"
    source = repo / "external" / "ccbench"
    stock = tmp_path / "stock"
    source.mkdir(parents=True)
    stock.mkdir()
    events = []

    @contextmanager
    def checkout(pin: str, *, base_dir: str):
        assert pin == paired.CANONICAL_CCBENCH_OID
        assert Path(base_dir) == source
        events.append("checkout")
        yield os.fspath(stock)

    def capture(source_root: Path, *, stock_root: str, configure_args):
        assert source_root == source
        assert Path(stock_root) == stock
        assert "-DCCBENCH_TRACE=0" in configure_args
        assert not any(arg.startswith("-DCCBENCH_BACKOFF_FIXED=") for arg in configure_args)
        events.append("capture")
        return object()

    def arm_record(request, arm: str):
        events.append((arm, request.macro, request.requested_value))
        return SimpleNamespace(
            arm=arm,
            reason_code="established",
            terminal_status="green",
        )

    def admit(supply_records, meaning_records, *, use_class: str):
        assert use_class == "paper"
        assert len(supply_records) == len(meaning_records) == 2
        events.append("admission")
        return SimpleNamespace(admitted=admitted)

    monkeypatch.setattr(paired.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        paired.condition_meaning_gate, "capture_define_inputs", capture,
    )
    monkeypatch.setattr(
        paired.condition_meaning_gate,
        "evaluate_define_supply_effectuation",
        lambda _captured, *, request, **_kwargs: arm_record(
            request, "supply-effectuation",
        ),
    )
    monkeypatch.setattr(
        paired.condition_meaning_gate,
        "evaluate_define_runtime_meaning",
        lambda _captured, *, request, **_kwargs: arm_record(
            request, "runtime-meaning",
        ),
    )
    monkeypatch.setattr(
        paired.condition_meaning_gate, "require_condition_gate_family", admit,
    )
    policy = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]

    if admitted:
        paired._require_v3_backoff_fixed_condition_gate(
            repo_root=repo, policy=policy, workload="balanced", cxx="g++",
        )
    else:
        with pytest.raises(paired.PaperStoryError, match="rejected measurement"):
            paired._require_v3_backoff_fixed_condition_gate(
                repo_root=repo, policy=policy, workload="balanced", cxx="g++",
            )
    assert events == [
        "checkout",
        "capture",
        ("supply-effectuation", "BACKOFF_FIXED", 5),
        ("runtime-meaning", "BACKOFF_FIXED", 5),
        "capture",
        ("supply-effectuation", "BACKOFF_FIXED", -1),
        ("runtime-meaning", "BACKOFF_FIXED", -1),
        "admission",
    ]


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())


@pytest.fixture
def a1_detail_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Supply terminal records; compiler correctness belongs to the gate suite."""
    gate = paired.condition_meaning_gate
    repo = tmp_path / "repo"
    (repo / "external" / "ccbench").mkdir(parents=True)
    root = tmp_path / "raw"
    root.mkdir()
    records = []
    for arm in ("supply-effectuation", "runtime-meaning"):
        for index, value in enumerate((5, -1)):
            digest = hashlib.sha256(f"{arm}:{value}".encode("ascii")).hexdigest()
            records.append(gate.ConditionArmRecord(
                record_id=f"condition-gate/{arm}/{digest}",
                record_digest=digest, arm=arm,
                terminal_status="green" if arm == "runtime-meaning" and index else "red",
                reason_code="established" if arm == "runtime-meaning" and index else "preprocess-failed",
                driver_id="orchestrator.campaign.paper_story_a1_paired:v3-balanced",
                macro="BACKOFF_FIXED", request_digest=digest,
                evidence={"detail": f"{arm} value={value}: command stderr", "value": value},
            ))
    admission = gate.ConditionFamilyAdmission(
        admission_id="condition-gate/admission/fixture",
        admission_digest=hashlib.sha256(b"a1-detail-admission").hexdigest(),
        use_class="paper", admitted=False,
        record_ids=tuple(record.record_id for record in records),
        unestablished_meaning_macros=("BACKOFF_FIXED",),
    )
    state = SimpleNamespace(records=records, admission=admission, root=root)

    @contextmanager
    def checkout(*_args, **_kwargs):
        yield os.fspath(repo / "external" / "ccbench")

    monkeypatch.setattr(paired.patchharness, "checkout", checkout)
    monkeypatch.setattr(gate, "capture_define_inputs", lambda *_a, **_k: object())
    monkeypatch.setattr(
        gate, "evaluate_define_supply_effectuation",
        lambda _captured, *, request, **_kw: state.records[(5, -1).index(request.requested_value)],
    )
    monkeypatch.setattr(
        gate, "evaluate_define_runtime_meaning",
        lambda _captured, *, request, **_kw: state.records[2 + (5, -1).index(request.requested_value)],
    )

    def admit(supply, meaning, *, use_class):
        assert use_class == "paper"
        assert supply + meaning == state.records
        assert len(supply) == len(meaning) == 2
        return state.admission

    monkeypatch.setattr(gate, "require_condition_gate_family", admit)
    policy = paired.load_policy(paired.V3_PILOT_STUDY_ID)[0]

    def invoke(**kwargs):
        paired._require_v3_backoff_fixed_condition_gate(
            repo_root=repo, policy=policy, workload="balanced", cxx="g++", **kwargs,
        )

    state.invoke = invoke
    state.rejection = (
        "v3 BACKOFF_FIXED condition gate rejected measurement: "
        "supply-effectuation:preprocess-failed,supply-effectuation:preprocess-failed,"
        "runtime-meaning:preprocess-failed"
    )
    return state


def _a1_detail_expected(state):
    expected = {
        f"condition-gate-{record.arm}-{record.record_digest}.json":
        record.canonical_json().encode("ascii")
        for record in state.records
    }
    expected[f"condition-gate-admission-{state.admission.admission_digest}.json"] = (
        state.admission.canonical_json().encode("ascii")
    )
    return expected


def test_a1_detail_all_records_atomic_and_idempotent(a1_detail_gate, monkeypatch):
    state = a1_detail_gate
    expected = _a1_detail_expected(state)
    events, temporary_names = [], []
    real_fsync, real_replace = os.fsync, os.replace

    def fsync(fd):
        import stat
        events.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
        return real_fsync(fd)

    def publish(source, destination):
        assert source.parent == destination.parent == state.root
        assert source.name.startswith(f".{destination.name}.tmp-")
        assert source.read_bytes() == expected[destination.name]
        temporary_names.append(source.name)
        events.append("replace")
        return real_replace(source, destination)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "replace", publish)
    for _ in range(2):
        with pytest.raises(paired.PaperStoryError) as caught:
            state.invoke(evidence_root=state.root)
        assert str(caught.value) == state.rejection
        assert {p.name: p.read_bytes() for p in state.root.iterdir()} == expected
    assert len(expected) == 5
    assert events == ["file", "replace", "directory"] * 10
    assert len(set(temporary_names)) == 10
    for record in state.records:
        payload = json.loads(expected[f"condition-gate-{record.arm}-{record.record_digest}.json"])
        assert payload["evidence"]["detail"] == record.evidence["detail"]
    # A different detail/digest adds evidence without removing the earlier file.
    digest = hashlib.sha256(b"a1-detail-retry").hexdigest()
    state.records[0] = replace(
        state.records[0], record_digest=digest,
        record_id=f"condition-gate/supply-effectuation/{digest}",
        evidence={"detail": "retry command stderr", "value": 5},
    )
    state.admission = replace(
        state.admission,
        admission_digest=hashlib.sha256(b"a1-detail-retry-admission").hexdigest(),
        record_ids=tuple(record.record_id for record in state.records),
    )
    expected.update(_a1_detail_expected(state))
    with pytest.raises(paired.PaperStoryError) as caught:
        state.invoke(evidence_root=state.root)
    assert str(caught.value) == state.rejection
    assert len(expected) == 7
    assert {p.name: p.read_bytes() for p in state.root.iterdir()} == expected


@pytest.mark.parametrize("failure", ("serialize", "write", "replace", "file-fsync", "directory-fsync"))
def test_a1_detail_save_exception_preserves_rejection(a1_detail_gate, monkeypatch, failure):
    state = a1_detail_gate
    expected = _a1_detail_expected(state)
    first_name = next(iter(expected))

    class SaveFailure(ValueError):
        def __str__(self):
            raise AssertionError("exception text must not be inspected")

    real_open, real_replace, real_fsync = Path.open, os.replace, os.fsync
    triggered = False

    def fail_once():
        nonlocal triggered
        if not triggered:
            triggered = True
            raise SaveFailure()

    if failure == "serialize":
        original = type(state.records[0]).canonical_json

        def serialize(record):
            if record is state.records[0]:
                fail_once()
            return original(record)

        monkeypatch.setattr(type(state.records[0]), "canonical_json", serialize)
    elif failure == "write":
        @contextmanager
        def partial_open(path, mode="r", *args, **kwargs):
            with real_open(path, mode, *args, **kwargs) as output:
                if mode == "xb" and not triggered:
                    def write(data):
                        output.write(data[:7])
                        output.flush()
                        fail_once()
                    yield SimpleNamespace(write=write, flush=output.flush, fileno=output.fileno)
                else:
                    yield output

        monkeypatch.setattr(Path, "open", partial_open)
    elif failure == "replace":
        def publish(source, destination):
            fail_once()
            return real_replace(source, destination)

        monkeypatch.setattr(os, "replace", publish)
    else:
        def fsync(fd):
            import stat
            is_directory = stat.S_ISDIR(os.fstat(fd).st_mode)
            if is_directory == (failure == "directory-fsync"):
                fail_once()
            return real_fsync(fd)

        monkeypatch.setattr(os, "fsync", fsync)
    with pytest.raises(paired.PaperStoryError) as caught:
        state.invoke(evidence_root=state.root)
    assert triggered
    assert str(caught.value) == state.rejection + "; evidence_write_failures=supply[0]:SaveFailure"
    if failure != "directory-fsync":
        del expected[first_name]
    assert {p.name: p.read_bytes() for p in state.root.iterdir()} == expected


@pytest.mark.parametrize("target", ("arm-digest", "admission-digest", "admission-serialize", "path"))
def test_a1_detail_preparation_exception_is_local(a1_detail_gate, monkeypatch, target):
    state = a1_detail_gate
    expected = _a1_detail_expected(state)
    label = "admission" if target.startswith("admission") else "supply[0]"
    name = list(expected)[-1 if label == "admission" else 0]
    root = state.root
    if target == "path":
        class FailingPath(type(root)):
            calls = 0

            def __truediv__(self, other):
                type(self).calls += 1
                if type(self).calls == 1:
                    raise ValueError("path")
                return super().__truediv__(other)

        root = FailingPath(root)
    else:
        obj = state.admission if label == "admission" else state.records[0]
        attribute = "canonical_json" if target.endswith("serialize") else (
            "admission_digest" if label == "admission" else "record_digest"
        )
        original = getattr(type(obj), attribute)

        def fail_get(instance):
            if instance is obj:
                raise ValueError("preparation")
            return original.__get__(instance, type(instance))

        monkeypatch.setattr(type(obj), attribute, property(fail_get))
    with pytest.raises(paired.PaperStoryError) as caught:
        state.invoke(evidence_root=root)
    assert str(caught.value) == state.rejection + f"; evidence_write_failures={label}:ValueError"
    del expected[name]
    assert {p.name: p.read_bytes() for p in state.root.iterdir()} == expected


def test_a1_detail_success_and_omitted_root_have_no_side_effects(a1_detail_gate, monkeypatch):
    state = a1_detail_gate

    def forbidden(*_args, **_kwargs):
        raise AssertionError("successful or rootless gate must not serialize or persist")

    monkeypatch.setattr(paired, "_persist_v3_condition_gate_record", forbidden)
    monkeypatch.setattr(type(state.records[0]), "canonical_json", forbidden)
    monkeypatch.setattr(type(state.admission), "canonical_json", forbidden)
    with pytest.raises(paired.PaperStoryError) as caught:
        state.invoke()
    assert str(caught.value) == state.rejection
    state.admission = replace(state.admission, admitted=True)
    assert state.invoke(evidence_root=state.root / "not-created") is None
    assert list(state.root.iterdir()) == []


def test_a1_detail_fallback_and_could_not_run_unchanged(a1_detail_gate, monkeypatch):
    state = a1_detail_gate
    state.records[:] = [replace(record, terminal_status="green") for record in state.records]
    with pytest.raises(paired.PaperStoryError) as caught:
        state.invoke(evidence_root=state.root)
    assert str(caught.value) == (
        "v3 BACKOFF_FIXED condition gate rejected measurement: admission-not-granted"
    )
    assert len(list(state.root.iterdir())) == 5

    def unavailable(*_args, **_kwargs):
        raise OSError("fixture capture failure")

    monkeypatch.setattr(paired.condition_meaning_gate, "capture_define_inputs", unavailable)
    with pytest.raises(paired.PaperStoryError) as caught:
        state.invoke(evidence_root=state.root / "not-created")
    assert str(caught.value) == "v3 BACKOFF_FIXED condition gate could not run: fixture capture failure"
    assert isinstance(caught.value.__cause__, OSError)
    assert not (state.root / "not-created").exists()


def test_a1_detail_base_exception_propagates(a1_detail_gate, monkeypatch):
    state = a1_detail_gate

    def interrupted(_fd):
        raise KeyboardInterrupt()

    monkeypatch.setattr(os, "fsync", interrupted)
    with pytest.raises(KeyboardInterrupt):
        state.invoke(evidence_root=state.root)
    assert list(state.root.iterdir()) == []


def test_a1_detail_production_passes_raw_root():
    import inspect
    tree = ast.parse(inspect.getsource(paired._run_measurement_v3))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name)
             and node.func.id == "_require_v3_backoff_fixed_condition_gate"]
    assert len(calls) == 1
    roots = [kw.value for kw in calls[0].keywords if kw.arg == "evidence_root"]
    assert len(roots) == 1
    assert ast.dump(roots[0]) == ast.dump(ast.parse('Path(roots["raw_root"])', mode="eval").body)


@pytest.mark.parametrize("mutation", ("none", "root", "missing", "duplicate", "extra", "path"))
def test_a1_amended_exact_configure_consumer_M5_M6(mutation):
    """Use buildcache's actual grammar; mutate one root/token only."""
    policy = _policy()
    evidence = _arm(policy, "adaptive")
    frames = evidence["attempts"][0]["frames"]
    build = frames[1]["payload"]
    bench = frames[3]["payload"]
    arm = policy["arms"][0]
    base = _TEST_BUILD_DIR.parent / "fetchcontent"
    base.mkdir()
    options = {"fetchcontent_base_dir": str(base)}
    for name in ("masstree", "mimalloc", "googletest"):
        source = base / f"{name}-src"
        source.mkdir()
        options[f"{name}_source_dir"] = str(source)
    configure, build_argv = paired.buildcache._v2_commands(
        paired.Genome(arm["protocol"], dict(arm["flags"])), False, "/source",
        str(_TEST_BUILD_DIR / "adaptive"), build["toolchain"], jobs=48,
        dependency_prefix=_dependency_prefix_fixture(), **options,
    )
    root = "/source"
    if mutation == "root":
        root = "/other-source"
    elif mutation == "missing":
        del configure[10]
    elif mutation == "duplicate":
        configure.insert(10, configure[10])
    elif mutation == "extra":
        configure.append("-DUNREGISTERED=1")
    elif mutation == "path":
        configure[11] += "-other"
    assert paired._trace0_commands_match(
        arm, policy, "write-heavy", configure, build_argv,
        shlex.split(bench["run_cmd"]), False, build["perf_bin_sha256"],
        amended_source_root=root,
    ) is (mutation == "none")


def test_a1_amendment_binding_rejects_single_changed_input_M8():
    source = paired.a1_source
    contract = source.load_contract(Path(paired.__file__).resolve().parents[2])
    policy = _v3_pilot_policy()
    paths = paired._source_relative_paths(policy, non_certifying=False)
    files = {path: {"git_blob_oid": "b" * 40, "working_sha256": "c" * 64} for path in paths}
    fixed = {source.CONTRACT_PATH: source.CONTRACT_SHA256,
             contract["patch"]: contract["patch_sha256"],
             contract["amendment"]: contract["amendment_sha256"]}
    for path, digest in fixed.items():
        files[path]["working_sha256"] = digest
    binding = {**_source_binding(), "files": files}
    assert paired._validate_source_binding(binding, policy)
    for path in fixed:
        changed = copy.deepcopy(binding)
        changed["files"][path]["working_sha256"] = "0" * 64
        assert not paired._validate_source_binding(changed, policy)


def _sized_source_binding():
    source = paired.a1_source
    policy = paired.load_policy(source.SIZED_STUDY_ID)[0]
    contract = source.load_contract(Path(paired.__file__).resolve().parents[2], source.SIZED_STUDY_ID)
    files = {path: {"git_blob_oid": "b" * 40, "working_sha256": "c" * 64}
             for path in paired._source_relative_paths(policy, non_certifying=False)}
    for path, digest in (
        (source.SIZED_CONTRACT_PATH, source.SIZED_CONTRACT_SHA256),
        (contract["patch"], contract["patch_sha256"]),
        (contract["amendment"], contract["amendment_sha256"]),
    ):
        files[path]["working_sha256"] = digest
    return policy, {**_source_binding(), "files": files}


def test_sized_source_contract_pins_bytes_and_four_bindings(tmp_path):
    source = paired.a1_source
    repo = Path(paired.__file__).resolve().parents[2]
    contract = source.load_contract(repo, source.SIZED_STUDY_ID)
    assert set(contract) == {
        "schema_version", "study_id", "canonical_head", "patch", "patch_sha256",
        "policy", "policy_sha256", "preregistration", "preregistration_sha256",
        "amendment", "amendment_sha256",
    }
    assert contract["schema_version"] == "paper-story-a1-source/v2"
    assert contract["study_id"] == source.SIZED_STUDY_ID
    assert contract["canonical_head"] == paired.CANONICAL_CCBENCH_OID
    paths = [source.SIZED_CONTRACT_PATH, *(contract[k] for k in
             ("patch", "policy", "preregistration", "amendment"))]
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((repo / relative).read_bytes())
    assert source.load_contract(tmp_path, source.SIZED_STUDY_ID) == contract
    for relative in paths:
        target = tmp_path / relative
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n")
            with pytest.raises(RuntimeError, match="bytes differ"):
                source.load_contract(tmp_path, source.SIZED_STUDY_ID)
        finally:
            target.write_bytes(original)


def test_sized_amendment_binding_rejects_single_changed_input():
    policy, binding = _sized_source_binding()
    source = paired.a1_source
    assert paired._validate_source_binding(binding, policy)
    for path in (source.SIZED_CONTRACT_PATH, source.SIZED_SOURCE_PATHS[2],
                 source.SIZED_SOURCE_PATHS[3]):
        changed = copy.deepcopy(binding)
        changed["files"][path]["working_sha256"] = "0" * 64
        assert not paired._validate_source_binding(changed, policy)


def test_pilot_published_source_binding_remains_accepted():
    repo = Path(paired.__file__).resolve().parents[2]
    receipt = json.loads((repo / "output/insights/2026-09-01_paper-story-a1-balanced5-pilot/receipt.json").read_bytes())
    binding = receipt["source_binding"]
    assert paired._validate_source_binding(binding, _v3_pilot_policy())
    assert paired.a1_source.binding_matches(binding["files"])


def _sized_amended_arm():
    policy, binding = _sized_source_binding()
    arm = paired._workload_arm_by_role(policy, "write-heavy", "variant")
    fixture_policy = {**policy, "arms": [dict(arm, name="adaptive")]}
    evidence = _arm(fixture_policy, "adaptive")
    arm = fixture_policy["arms"][0]
    frames = evidence["attempts"][0]["frames"]
    start, build, bench = frames[0]["payload"], frames[1]["payload"], frames[3]["payload"]
    start["build_admission"] = {"source": {
        "source_root": "/source", "ccbench_commit": paired.CANONICAL_CCBENCH_OID,
        "tracked_clean": False, "src_token": start["src_token"],
        "genome_sha256": hashlib.sha256(start["genome"].encode()).hexdigest(),
    }}
    base = _TEST_BUILD_DIR.parent / "fetchcontent"
    base.mkdir()
    options = {"fetchcontent_base_dir": str(base)}
    for name in ("masstree", "mimalloc", "googletest"):
        target = base / (name + "-src")
        target.mkdir()
        options[name + "_source_dir"] = str(target)
    configure, build_argv = paired.buildcache._v2_commands(
        paired.Genome(arm["protocol"], dict(arm["flags"])), False, "/source",
        str(_TEST_BUILD_DIR / "adaptive"), build["toolchain"], jobs=48,
        dependency_prefix=_dependency_prefix_fixture(), **options,
    )
    build["perf_configure_cmd"] = shlex.join(configure)
    build["perf_build_cmd"] = shlex.join(build_argv)
    bench["settled"] = True
    scale = policy["scale"]
    argv = shlex.split(bench["run_cmd"])
    replacements = {"thread_num": scale["threads"], "ycsb_tuple_num": scale["records"],
                    "extime": scale["extime_s"], "ycsb_zipf_skew": scale["ycsb_zipf_skew"],
                    "ycsb_rmw": scale["ycsb_rmw"], "ycsb_max_ope": scale["ycsb_max_ope"]}
    bench["run_cmd"] = shlex.join([
        "-" + key + "=" + str(replacements[key]) if token.startswith("-") and
        (key := token[1:].split("=")[0]) in replacements else token for token in argv
    ])
    return policy, binding, arm, evidence


def _validate_sized_amended_arm(state):
    policy, binding, arm, evidence = state
    return paired._validate_arm(arm, evidence, policy=policy, workload_name="write-heavy",
                                env_tag="pegasus", source_binding=binding)


def test_sized_consumer_accepts_amended_configure():
    result = _validate_sized_amended_arm(_sized_amended_arm())
    assert result["valid"], result["errors"]


def test_sized_consumer_rejects_admission_mismatch():
    state = _sized_amended_arm()
    for key, value, error in (
        ("source_root", "relative", "amended-source-admission-mismatch"),
        ("tracked_clean", True, "amended-source-admission-mismatch"),
        ("ccbench_commit", "0" * 40, "amended-source-admission-mismatch"),
        ("source_root", "/other-source", "trace0-source-route-incomplete"),
    ):
        changed = copy.deepcopy(state)
        changed[3]["attempts"][0]["frames"][0]["payload"]["build_admission"]["source"][key] = value
        result = _validate_sized_amended_arm(changed)
        assert not result["valid"]
        assert error in result["errors"]
