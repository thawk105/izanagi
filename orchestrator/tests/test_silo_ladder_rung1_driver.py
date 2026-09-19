# -*- coding: utf-8 -*-
"""Rung1 driver/PBS の fixture 契約。cmake/qsub/実 build は起動しない。"""
from __future__ import annotations

import copy
import dataclasses
import inspect
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures/silo_ladder_rung1_driver"
TOOLS = ROOT / "tools/pegasus"
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import silo_ladder_rung1 as driver  # noqa: E402


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_condition_family_dominates_stock_build_and_includes_companion_macro():
    job = inspect.getsource(driver._gap_job_command)
    correctness = inspect.getsource(driver._correctness_command)
    gate = inspect.getsource(driver._require_condition_gates)
    first_build = job.index("variant=\"stock\"")
    assert job.count("_require_condition_gates(") == 2
    assert job.index("configure_argv=perf_gate_configure") < first_build
    assert job.index("configure_argv=liveness_gate_configure") < first_build
    assert "for gate_variant, gate_macros in" not in job
    assert correctness.index("_require_condition_gates") < correctness.index(
        "configured = _run("
    )
    assert "configure_argv=configure" in correctness
    assert '("BACKOFF_FIXED", -1, None, True)' in gate
    assert "(REPORT_MACRO, 1, 0, False)" in gate
    assert "declare_define_runtime_meaning(request)" in gate
    assert "declaration=None" not in gate
    configure = inspect.getsource(driver._configure_argv)
    assert '"-DCCBENCH_BACKOFF_FIXED=-1"' in configure
    assert '"-DBACKOFF_FIXED=-1"' not in configure


def test_condition_gates_pass_real_factory_declarations_to_evaluator(monkeypatch, tmp_path):
    gate = driver.condition_meaning_gate
    patched_source = tmp_path / "patched"
    stock_source = tmp_path / "stock"
    for source in (patched_source, stock_source):
        source.mkdir()
        (source / "CMakeLists.txt").write_text("# fixture\n", encoding="utf-8")
    tools = {"cmake": "/fixture/cmake", "g++": "/fixture/g++"}
    captured = object()
    observed = []
    record = SimpleNamespace(canonical_json=lambda: "{}")

    def capture(source, *, stock_root, configure_args):
        assert source == patched_source
        assert stock_root == stock_source
        return captured

    def observe_meaning(inputs, *, request, declaration, cxx):
        assert inputs is captured
        assert cxx == tools["g++"]
        observed.append((request, declaration))
        return record

    monkeypatch.setattr(gate, "capture_define_inputs", capture)
    monkeypatch.setattr(
        gate, "evaluate_define_supply_effectuation", lambda *args, **kwargs: record,
    )
    monkeypatch.setattr(gate, "evaluate_define_runtime_meaning", observe_meaning)
    monkeypatch.setattr(
        gate, "require_condition_gate_family",
        lambda *args, **kwargs: SimpleNamespace(admitted=True, canonical_json=lambda: "{}"),
    )

    driver._require_condition_gates(
        patched_source=patched_source,
        stock_source=stock_source,
        tools=tools,
        configure_argv=[
            tools["cmake"], "-S", str(patched_source), "-B", str(tmp_path / "build"),
            "-DCCBENCH_BACKOFF_FIXED=-1",
            "-DCMAKE_CXX_FLAGS=-DIZANAGI_SILO_LADDER_RUNG1=1 "
            "-DIZANAGI_SILO_LADDER_RUNG1_REPORT=1",
        ],
    )

    assert [request.macro for request, _ in observed] == [
        "BACKOFF_FIXED", driver.RUNG_MACRO, driver.REPORT_MACRO,
    ]
    (backoff, backoff_declaration), (_, rung_declaration), (report, declaration) = observed
    assert backoff.requested_value == -1
    assert backoff.stock_comparison is True
    assert backoff_declaration is None
    assert rung_declaration is None
    assert type(declaration) is gate.ConditionalBranchMeaningDeclaration
    assert declaration.macro == report.macro == "IZANAGI_SILO_LADDER_RUNG1_REPORT"
    assert declaration.source_rel == "cc/silo/ycsb_silo.cc"


def _text_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _target_object_path(relative: str) -> str:
    return (
        "/fixture/build/cc/silo/CMakeFiles/ycsb_silo.exe.dir/"
        f"{Path(relative).name}.o"
    )


def _balanced_or_stock_first(mode: str) -> dict:
    schedule = driver.generate_schedule("01" * 32)
    if mode == "balanced":
        return schedule
    assert mode in {"all-stock-first", "cross-workload-imbalance"}
    rebuilt = []
    for rep in range(1, 7):
        rep_rows = [row for row in schedule["runs"] if row["rep"] == rep]
        workload_order = list(dict.fromkeys(row["workload"] for row in rep_rows))
        for workload in workload_order:
            pair = [
                row for row in schedule["runs"]
                if row["rep"] == rep and row["workload"] == workload
            ]
            by_variant = {row["variant"]: row for row in pair}
            stock_first = (
                mode == "all-stock-first"
                or (
                    mode == "cross-workload-imbalance"
                    and workload == "W-cal"
                )
            )
            variants = (
                ("stock", "rung-perf")
                if stock_first else ("rung-perf", "stock")
            )
            rebuilt.extend(by_variant[variant] for variant in variants)
    schedule["runs"] = [
        {**row, "ordinal": ordinal} for ordinal, row in enumerate(rebuilt)
    ]
    return schedule


def _integrity() -> dict:
    return {
        "clean": True,
        "orphan_reads": 0,
        "version_dups": 0,
        "dup_txids": 0,
        "genesis_commits": 0,
        "missing_txids": 0,
        "write_version_mismatch": 0,
        "malformed_keys": 0,
        "framing_violations": 0,
        "framing_violation_details": [],
        "lock_coverage_violations": 0,
        "write_intent_violations": 0,
        "permutation_violations": 0,
        "permutation_violation_details": {
            "counts": {
                "size-changed": 0,
                "rcdptr-set-changed": 0,
                "unknown": 0,
            },
            "sample": [],
            "unknown_reason_sample": [],
        },
        "notes": [],
    }


def _liveness_runs(zero_worker: int | None) -> list[dict]:
    runs = []
    for workload in driver.WORKLOADS:
        for rep in (1, 2):
            values = [worker + rep for worker in range(48)]
            if zero_worker is not None and not runs:
                values[zero_worker] = 0
            workers = [
                {"worker": worker, "commits": value}
                for worker, value in enumerate(values)
            ]
            batches = [
                {"worker": worker, "commits": 0} for worker in range(48)
            ]
            runs.append({
                "ordinal": len(runs) + 24,
                "workload": workload,
                "rep": rep,
                "variant": "rung-liveness",
                "binary_id": "rung-liveness",
                "workload_argv": list(driver.WORKLOADS[workload]["argv"]),
                "argv": [
                    "/fixture/rung-liveness",
                    *driver.WORKLOADS[workload]["argv"],
                ],
                "started_at_utc": "2026-07-29T00:00:00Z",
                "completed_at_utc": "2026-07-29T00:00:04Z",
                "returncode": 0,
                "bounded_completion": True,
                "stdout_sha256": "a" * 64,
                "stderr_sha256": "b" * 64,
                "raw_path": f"runs/liveness-{len(runs) + 24:02d}-{workload}-r{rep}",
                "commit_count": sum(values),
                "batch_commit_count": 0,
                "per_worker_commits": workers,
                "per_worker_batch_commits": batches,
            })
    return runs


def _performance_runs(schedule: dict) -> list[dict]:
    result = []
    workload_index = {name: index for index, name in enumerate(driver.WORKLOADS)}
    for row in schedule["runs"]:
        workload = row["workload"]
        rep = row["rep"]
        variant = row["variant"]
        base = 2_000_000 + workload_index[workload] * 100_000
        result.append({
            "ordinal": row["ordinal"],
            "workload": workload, "rep": rep, "variant": variant,
            "binary_id": variant,
            "workload_argv": list(driver.WORKLOADS[workload]["argv"]),
            "argv": [f"/fixture/{variant}", *driver.WORKLOADS[workload]["argv"]],
            "started_at_utc": "2026-07-29T00:00:00Z",
            "completed_at_utc": "2026-07-29T00:00:04Z",
            "returncode": 0,
            "throughput_tps": base + rep if variant == "stock" else base // 4 + rep,
            "commit_count": 100,
            "batch_commit_count": 0,
            "stdout_sha256": "a" * 64,
            "stderr_sha256": "b" * 64,
            "raw_path": (
                f"runs/perf-{row['ordinal']:02d}-{workload}-{variant}-r{rep}"
            ),
        })
    return result


def _evidence(spec: dict) -> dict:
    schedule = _balanced_or_stock_first(spec["schedule_mode"])
    hexes = {
        name: char * 64 for name, char in zip(
            ("patch", "ledger", "driver", "pbs_job", "submitter",
             "verifier_module", "calibration", "contract"),
            "12345678",
        )
    }
    file_ref = lambda name: {"path": f"fixture/{name}", "sha256": hexes[name]}
    transaction_sha = "9" * 64
    tools = [
        {
            "name": name,
            "realpath": f"/fixture/{name}",
            "version": f"{name} fixture version",
            "sha256": f"{index:x}" * 64,
        }
        for index, name in enumerate(
            ("git", "nm", "readelf", "cmake", "gcc", "g++", "python"), 1
        )
    ]
    dependencies = [
        {
            "name": name,
            "resolved_path": f"/fixture/{name}-install",
            "pin": pin,
            "git_head_raw": pin + "\n",
            "git_status_porcelain_raw": "",
        }
        for name, pin in (
            ("gflags", "e171aa2d15ed9eb17054558e0b3a6a413bb01067"),
            ("glog", "8f9ccfe770add9e4c64e9b25c102658e3c763b73"),
        )
    ]
    dependency_pin_argv = [
        f"-DIZANAGI_GFLAGS_SRC_HEAD={dependencies[0]['pin']}",
        f"-DIZANAGI_GLOG_SRC_HEAD={dependencies[1]['pin']}",
    ]
    third_party_policy = driver.third_party_policy(ROOT)
    def third_party_records(root: str) -> list[dict]:
        return [
            {
                **item,
                "resolved_path": f"{root}/{item['source_name']}",
                "git_head_raw": item["pin"] + "\n",
                "git_status_porcelain_raw": "",
                "clean": True,
            }
            for item in third_party_policy
        ]
    correctness_third_party = third_party_records(
        "/fixture/thirdparty-staging"
    )
    gap_third_party = third_party_records("/fixture/thirdparty-scratch")
    correctness_third_party_argv = driver._third_party_configure_flags(
        correctness_third_party
    )
    gap_third_party_argv = driver._third_party_configure_flags(
        gap_third_party
    )
    return {
        "schema_version": driver.SCHEMA_VERSION,
        "artifact_id": driver.ARTIFACT_ID,
        "generated_at_utc": "2026-07-29T00:00:00Z",
        "classification": {
            "evaluation_role": "ability_probe",
            "research_goal_eligible": False,
            "recovery_measurement_eligibility": False,
        },
        "activation_contract": {
            "macro": driver.RUNG_MACRO,
            "symbols": [driver.IDENTITY_SYMBOL],
        },
        "binding": {
            "patch": file_ref("patch"),
            "ledger": file_ref("ledger"),
            "driver": file_ref("driver"),
            "pbs_job": file_ref("pbs_job"),
            "submitter": file_ref("submitter"),
            "verifier_module": file_ref("verifier_module"),
            "policy": {"path": "fixture/policy", "sha256": "9" * 64},
            "runtime_modules": [
                {"path": "fixture/runtime.py", "sha256": "a" * 64},
            ],
            "ccbench_pin_full": driver.PIN,
            "calibration": {
                "path": "fixture/calibration.json",
                "sha256": hexes["calibration"],
                "contract_sha256": hexes["contract"],
                "quality_status": "accepted",
                "records": 1_000_000,
                "threads": 48,
                "transfer_scope": ["build_contract", "records", "threads"],
            },
        },
        "provenance": {
            "environment_scrubbed": True,
            "tools": copy.deepcopy(tools),
            "third_party_sources": copy.deepcopy(gap_third_party),
            "source_witness": {
                "submit_whole_tree_clean": True,
                "job_source_surface_clean": True,
                "job_source_exclusions": ["output"],
                "job_prologue_manifest_sha256": "b" * 64,
                "expected_patched_source_sha256": {
                    path: "f" * 64 for path in driver.SOURCE_FILES
                },
                "observed_patched_source_sha256": {
                    path: "f" * 64 for path in driver.SOURCE_FILES
                },
            },
        },
        "correctness_leg": {
            "workload": {"argv": driver.CORRECTNESS_WORKLOAD, "threads": 4},
            "build": {
                "id": "correctness",
                "trace": True,
                "macros": [driver.RUNG_MACRO],
                "identity_defined_count": 1,
                "transaction_object_sha256": transaction_sha,
                "activation_ok": True,
                "configure_argv": [
                    "cmake", "-DCCBENCH_TRACE=1",
                    f"-D{driver.RUNG_MACRO}=1",
                    "-DCMAKE_PREFIX_PATH=/fixture/gflags-install;/fixture/glog-install",
                    "-DIZANAGI_GFLAGS_SRC_HEAD=e171aa2d15ed9eb17054558e0b3a6a413bb01067",
                    "-DIZANAGI_GLOG_SRC_HEAD=8f9ccfe770add9e4c64e9b25c102658e3c763b73",
                    *correctness_third_party_argv,
                ],
                "build_argv": ["cmake", "--build", "fixture"],
                "binary_sha256": "c" * 64,
                "compile_invocations": [
                    {
                        "source_rel": path, "argv": ["g++", "-c", path],
                        "object_path": _target_object_path(path),
                        "object_sha256": transaction_sha,
                        "replay_object_sha256": transaction_sha,
                        "replay_match": True,
                    }
                    for path in driver.SOURCE_FILES
                ],
                "cmake_cache_sha256": "e" * 64,
                "source_sha256": {
                    path: "f" * 64 for path in driver.SOURCE_FILES
                },
                "dependencies": copy.deepcopy(dependencies),
                "raw_paths": ["compile_commands.json", "verifier.json"],
            },
            "provenance": {
                "environment_scrubbed": True,
                "tools": copy.deepcopy(tools),
                "ccbench_pin_full": driver.PIN,
                "expected_patched_source_sha256": {
                    path: "f" * 64 for path in driver.SOURCE_FILES
                },
                "observed_patched_source_sha256": {
                    path: "f" * 64 for path in driver.SOURCE_FILES
                },
                "dependencies": copy.deepcopy(dependencies),
                "third_party_sources": copy.deepcopy(correctness_third_party),
            },
            "verifier_rc": 0,
            "verifier": {
                "runs": 1,
                "certified_serializable": 1,
                "non_serializable": 0,
                "indeterminate": 0,
                "results": [{
                    "trace_dir": "fixture/trace",
                    "verdict": "serializable",
                    "certified": spec["certified"],
                    "serializable": True,
                    "stats": {
                        "txns": 4, "reads": 0, "writes": 4, "keys": 4,
                        "edges": 0, "abort_reasons": {},
                    },
                    "integrity": _integrity(),
                    "anomaly_count": 0,
                    "total_cycles": 0,
                    "anomalies": [],
                }],
            },
            "trace_files": [
                {
                    "path": f"trace_{worker}.log",
                    "commits": 1,
                    "non_insert_write_witness": True,
                }
                for worker in range(4)
            ],
            "raw_paths": ["correctness/verifier.json"],
        },
        "gap_leg": {
            "status": spec.get("gap_status", "complete"),
            "workloads": [
                {"id": name, **copy.deepcopy(value)}
                for name, value in driver.WORKLOADS.items()
            ],
            "schedule_receipt": schedule,
            "builds": [
                {
                    "id": "stock", "trace": False, "macros": [],
                    "identity_defined_count": 0,
                    "transaction_object_sha256": "a" * 64,
                    "activation_ok": True,
                    "configure_argv": [
                        "cmake", "-DCCBENCH_TRACE=0", *dependency_pin_argv,
                        *gap_third_party_argv,
                    ],
                    "build_argv": ["cmake", "--build", "fixture"],
                    "binary_sha256": "c" * 64,
                    "compile_invocations": [
                        {
                            "source_rel": path, "argv": ["g++", "-c", path],
                            "object_path": _target_object_path(path),
                            "object_sha256": "d" * 64,
                            "replay_object_sha256": "d" * 64,
                            "replay_match": True,
                        }
                        for path in driver.SOURCE_FILES
                    ],
                    "cmake_cache_sha256": "e" * 64,
                    "source_sha256": {
                        path: "f" * 64 for path in driver.SOURCE_FILES
                    },
                    "dependencies": copy.deepcopy(dependencies),
                    "raw_paths": ["build-stock/compile_commands.json"],
                },
                {
                    "id": "rung-perf", "trace": False,
                    "macros": [driver.RUNG_MACRO],
                    "identity_defined_count": 1,
                    "transaction_object_sha256": transaction_sha,
                    "activation_ok": True,
                    "configure_argv": [
                        "cmake", f"-D{driver.RUNG_MACRO}=1",
                        *dependency_pin_argv,
                        *gap_third_party_argv,
                    ],
                    "build_argv": ["cmake", "--build", "fixture"],
                    "binary_sha256": "c" * 64,
                    "compile_invocations": [
                        {
                            "source_rel": path, "argv": ["g++", "-c", path],
                            "object_path": _target_object_path(path),
                            "object_sha256": transaction_sha,
                            "replay_object_sha256": transaction_sha,
                            "replay_match": True,
                        }
                        for path in driver.SOURCE_FILES
                    ],
                    "cmake_cache_sha256": "e" * 64,
                    "source_sha256": {
                        path: "f" * 64 for path in driver.SOURCE_FILES
                    },
                    "dependencies": copy.deepcopy(dependencies),
                    "raw_paths": ["build-rung-perf/nm.txt"],
                },
                {
                    "id": "rung-liveness", "trace": False,
                    "macros": [driver.RUNG_MACRO, driver.REPORT_MACRO],
                    "identity_defined_count": 1,
                    "transaction_object_sha256": transaction_sha,
                    "activation_ok": True,
                    "configure_argv": [
                        "cmake", f"-D{driver.RUNG_MACRO}=1",
                        f"-D{driver.REPORT_MACRO}=1",
                        *dependency_pin_argv,
                        *gap_third_party_argv,
                    ],
                    "build_argv": ["cmake", "--build", "fixture"],
                    "binary_sha256": "c" * 64,
                    "compile_invocations": [
                        {
                            "source_rel": path, "argv": ["g++", "-c", path],
                            "object_path": _target_object_path(path),
                            "object_sha256": transaction_sha,
                            "replay_object_sha256": transaction_sha,
                            "replay_match": True,
                        }
                        for path in driver.SOURCE_FILES
                    ],
                    "cmake_cache_sha256": "e" * 64,
                    "source_sha256": {
                        path: "f" * 64 for path in driver.SOURCE_FILES
                    },
                    "dependencies": copy.deepcopy(dependencies),
                    "raw_paths": ["build-rung-liveness/readelf.txt"],
                },
            ],
            "performance_runs": _performance_runs(schedule),
            "liveness_runs": _liveness_runs(spec["zero_worker"]),
            "attestation": {
                "contract_sha256": hexes["contract"],
                "calibration_sha256": hexes["calibration"],
                "cpu_model_match": True,
                "effective_clock_match": True,
                "cpuset_match": True,
                "ht_match": True,
                "numa_match": True,
                "per_sample_solo_checks": [
                    {
                        "ordinal": ordinal,
                        "pgrep_returncode": 1,
                        "competing_processes": [],
                        "load1": 0.1,
                        "load_threshold": 48.0,
                        "passed": True,
                    }
                    for ordinal in range(28)
                ],
                "all_pass": True,
            },
            "attempts": [{
                "attempt": 1,
                "failure_class": spec.get("terminal_failure_class"),
                "reason_code": spec.get("terminal_reason_code"),
                "raw_root": "attempts/1",
                "attempt_receipt_sha256": "d" * 64,
                "job_id": "fixture-job",
                "nonce": "e" * 32,
                "submit_receipt_sha256": "f" * 64,
                "campaign_attempt_root_receipt": {
                    "path": "fixture/campaign/attempt-1/attempt-root-receipt.json",
                    "sha256": "1" * 64,
                },
            }],
        },
        "retry_policy": {
            "max_attempts": 2,
            "infra_reason_codes": sorted(driver.INFRA_REASON_CODES),
            "substantive_negative_retried": False,
        },
        "limitations": {
            "raw_object_binary_bytes_retained": False,
            "nqsv_scheduler_exit_status": "unavailable",
            "third_party_rederivation": "sha256-chain-consistency-only",
        },
        "raw_bundle": {
            "root": "fixture/raw",
            "paths": sorted([
                "correctness/verifier.json",
                "gap/schedule-receipt.json",
                "gap/build-stock/compile_commands.json",
                "gap/pbs-accounting.txt",
            ]),
        },
        "checks": {
            "correctness": True,
            "schedule": True,
            "per_worker_ever_committed": True,
            "bounded_completion": True,
            "performance_direction": True,
            "activation": True,
            "attestation": True,
            "raw_recomputed": True,
        },
        "all_pass": True,
    }


def _reason_codes(spec_name: str) -> list[str]:
    return [
        failure.reason_code
        for failure in driver.validate_evidence(_evidence(_fixture(spec_name)))
    ]


def test_p_plus_2_normal_evidence_bundle_is_all_green():
    assert _reason_codes("p_plus_2.json") == []


def test_n4_certified_false_kills_only_correctness_gate():
    positive = _evidence(_fixture("p_plus_2.json"))
    negative = _evidence(_fixture("n4_certified_false.json"))
    positive["correctness_leg"]["verifier"]["results"][0]["certified"] = False
    assert negative == positive
    assert _reason_codes("n4_certified_false.json") == ["correctness_certified"]


def test_write_intent_violation_kills_correctness_gate():
    document = _evidence(_fixture("p_plus_2.json"))
    document["correctness_leg"]["verifier"]["results"][0][
        "integrity"
    ]["write_intent_violations"] = 1
    assert [
        failure.reason_code for failure in driver.validate_evidence(document)
    ] == ["correctness_certified"]


def test_n5_one_zero_worker_kills_only_ever_committed_gate():
    document = _evidence(_fixture("n5_one_worker_zero.json"))
    mutated = document["gap_leg"]["liveness_runs"][0]
    assert sum(
        item["commits"] for item in mutated["per_worker_commits"]
    ) == mutated["commit_count"]
    assert sum(
        item["commits"] == 0 for item in mutated["per_worker_commits"]
    ) == 1
    assert _reason_codes("n5_one_worker_zero.json") == [
        "per_worker_ever_committed"
    ]


def test_n6_all_stock_first_kills_only_schedule_balance_gate():
    runs = _evidence(
        _fixture("n6_all_stock_first.json")
    )["gap_leg"]["schedule_receipt"]["runs"]
    first_variants = [
        next(row for row in runs if row["rep"] == rep)["variant"]
        for rep in range(1, 7)
    ]
    first_workloads = [
        next(row for row in runs if row["rep"] == rep)["workload"]
        for rep in range(1, 7)
    ]
    assert first_variants == ["stock"] * 6
    assert first_workloads.count("W-cal") == 3
    assert _reason_codes("n6_all_stock_first.json") == ["schedule_balance"]


def test_cross_workload_imbalance_kills_only_schedule_balance_gate():
    document = _evidence(_fixture("n6_cross_workload_imbalance.json"))
    rows = document["gap_leg"]["schedule_receipt"]["runs"]
    assert all(
        next(
            row for row in rows
            if row["workload"] == "W-cal" and row["rep"] == rep
        )["variant"] == "stock"
        for rep in range(1, 7)
    )
    assert all(
        next(
            row for row in rows
            if row["workload"] == "W-hw" and row["rep"] == rep
        )["variant"] == "rung-perf"
        for rep in range(1, 7)
    )
    assert _reason_codes("n6_cross_workload_imbalance.json") == [
        "schedule_balance"
    ]


def test_closed_schema_rejects_unknown_key_at_each_material_layer():
    valid = _evidence(_fixture("p_plus_2.json"))
    locations = [
        valid,
        valid["classification"],
        valid["binding"],
        valid["binding"]["runtime_modules"][0],
        valid["binding"]["calibration"],
        valid["binding"]["patch"],
        valid["provenance"],
        valid["provenance"]["tools"][0],
        valid["provenance"]["third_party_sources"][0],
        valid["provenance"]["source_witness"],
        valid["correctness_leg"],
        valid["correctness_leg"]["workload"],
        valid["correctness_leg"]["build"],
        valid["correctness_leg"]["build"]["compile_invocations"][0],
        valid["correctness_leg"]["provenance"],
        valid["correctness_leg"]["provenance"]["tools"][0],
        valid["correctness_leg"]["provenance"]["third_party_sources"][0],
        valid["correctness_leg"]["verifier"],
        valid["correctness_leg"]["verifier"]["results"][0],
        valid["correctness_leg"]["verifier"]["results"][0]["stats"],
        valid["correctness_leg"]["verifier"]["results"][0]["integrity"],
        valid["correctness_leg"]["trace_files"][0],
        valid["gap_leg"],
        valid["gap_leg"]["workloads"][0],
        valid["gap_leg"]["builds"][0],
        valid["gap_leg"]["builds"][0]["compile_invocations"][0],
        valid["gap_leg"]["performance_runs"][0],
        valid["gap_leg"]["liveness_runs"][0],
        valid["gap_leg"]["liveness_runs"][0]["per_worker_commits"][0],
        valid["gap_leg"]["attestation"],
        valid["gap_leg"]["attestation"]["per_sample_solo_checks"][0],
        valid["gap_leg"]["attempts"][0],
        valid["gap_leg"]["attempts"][0]["campaign_attempt_root_receipt"],
        valid["retry_policy"],
        valid["limitations"],
        valid["raw_bundle"],
        valid["checks"],
    ]
    for index in range(len(locations)):
        mutated = copy.deepcopy(valid)
        cursor = [
            mutated,
            mutated["classification"],
            mutated["binding"],
            mutated["binding"]["runtime_modules"][0],
            mutated["binding"]["calibration"],
            mutated["binding"]["patch"],
            mutated["provenance"],
            mutated["provenance"]["tools"][0],
            mutated["provenance"]["third_party_sources"][0],
            mutated["provenance"]["source_witness"],
            mutated["correctness_leg"],
            mutated["correctness_leg"]["workload"],
            mutated["correctness_leg"]["build"],
            mutated["correctness_leg"]["build"]["compile_invocations"][0],
            mutated["correctness_leg"]["provenance"],
            mutated["correctness_leg"]["provenance"]["tools"][0],
            mutated["correctness_leg"]["provenance"]["third_party_sources"][0],
            mutated["correctness_leg"]["verifier"],
            mutated["correctness_leg"]["verifier"]["results"][0],
            mutated["correctness_leg"]["verifier"]["results"][0]["stats"],
            mutated["correctness_leg"]["verifier"]["results"][0]["integrity"],
            mutated["correctness_leg"]["trace_files"][0],
            mutated["gap_leg"],
            mutated["gap_leg"]["workloads"][0],
            mutated["gap_leg"]["builds"][0],
            mutated["gap_leg"]["builds"][0]["compile_invocations"][0],
            mutated["gap_leg"]["performance_runs"][0],
            mutated["gap_leg"]["liveness_runs"][0],
            mutated["gap_leg"]["liveness_runs"][0]["per_worker_commits"][0],
            mutated["gap_leg"]["attestation"],
            mutated["gap_leg"]["attestation"]["per_sample_solo_checks"][0],
            mutated["gap_leg"]["attempts"][0],
            mutated["gap_leg"]["attempts"][0]["campaign_attempt_root_receipt"],
            mutated["retry_policy"],
            mutated["limitations"],
            mutated["raw_bundle"],
            mutated["checks"],
        ][index]
        cursor["unknown"] = "rejected"
        assert [f.reason_code for f in driver.validate_evidence(mutated)] == ["schema"]


def test_schedule_generation_is_seeded_balanced_and_interleaved():
    first = driver.generate_schedule("ab" * 32)
    second = driver.generate_schedule("ab" * 32)
    assert first == second
    assert driver.validate_schedule(first) is None
    assert len(first["runs"]) == 24
    assert {
        row["variant"] for row in first["runs"]
    } == {"stock", "rung-perf"}


def test_environment_scrub_is_allowlist_and_removes_injection_channels(monkeypatch):
    source = {
        "PATH": "/bin",
        "HOME": "/fixture",
        "PBS_JOBID": "0:1.nqsv",
        "GIT_CONFIG_COUNT": "1",
        "PYTHONPATH": "/attack",
        "LD_LIBRARY_PATH": "/attack",
        "MAKEFLAGS": "-j999",
        "CXXFLAGS": "-DATTACK=1",
        "CCACHE_DIR": "/attack",
        "UNRELATED_SECRET": "drop",
    }
    assert driver.scrub_environment(source) == {
        "PATH": "/bin", "HOME": "/fixture", "PBS_JOBID": "0:1.nqsv",
    }


def test_solo_load_threshold_comes_from_bound_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(
        driver, "_run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", ""),
    )
    monkeypatch.setattr(driver.os, "getloadavg", lambda: (47.5, 1.0, 1.0))
    result = driver._solo_check(tmp_path, 0)
    policy = json.loads((TOOLS / "policy.json").read_text(encoding="utf-8"))
    assert result["load_threshold"] == policy["silo_ladder_rung1"][
        "solo_load1_threshold"
    ]
    assert result["passed"] is True


def test_attestation_json_parse_failure_is_retryable_infra(monkeypatch, tmp_path):
    def fake_run(argv, **kwargs):
        output = Path(argv[argv.index("--output") + 1])
        output.write_text("{", encoding="utf-8")
        Path(kwargs["stdout_path"]).write_text("", encoding="utf-8")
        Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(driver, "_run", fake_run)
    with pytest.raises(driver.InfraFailure) as captured:
        driver._attest_environment(tmp_path)
    assert captured.value.reason_code == "parse_failure"


def _all_pass_live_probe_payload(
    *,
    duplicate_schema_key: bool = False,
    schema_version: str = driver.env_attestation.PEGASUS_PROBE_OUTPUT_V2,
    forged_cpu_pair: bool = False,
) -> str:
    contract = driver.env_contract.lookup("pegasus")
    verified = driver.env_attestation.load_verified_calibration(contract, ROOT)
    profile = driver.env_attestation.profile_to_dict(
        verified.attestation_profile,
    )
    if schema_version == driver.env_attestation.PEGASUS_PROBE_OUTPUT_V1:
        profile["effective_clock"]["tolerance_pct"] = 100.0
    else:
        del profile["effective_clock"]["tolerance_pct"]
    if forged_cpu_pair:
        profile["cpu"].update({
            "model_name_raw": "Intel Xeon Platinum 8468H",
            "model_name_normalized": "Intel Xeon Platinum 8468",
        })
    expected_samples = profile["effective_clock"]["samples_mhz"]
    ordered = sorted(expected_samples)
    middle = len(ordered) // 2
    median = (ordered[middle - 1] + ordered[middle]) / 2.0
    profile["effective_clock"]["samples_mhz"] = [
        median for _ in expected_samples
    ]
    payload = json.dumps({
        "schema_version": schema_version,
        "ok": True,
        "observed_epoch": 1,
        "profile": profile,
    }, separators=(",", ":"))
    if duplicate_schema_key:
        schema_prefix = (
            '{"schema_version":' + json.dumps(schema_version) + ","
        )
        payload = payload.replace(
            schema_prefix,
            schema_prefix + '"schema_version":' + json.dumps(schema_version) + ",",
            1,
        )
    return payload


@pytest.mark.parametrize("schema_version", [
    driver.env_attestation.PEGASUS_PROBE_OUTPUT_V1,
    driver.env_attestation.PEGASUS_PROBE_OUTPUT_V2,
])
def test_live_attestation_rejects_forged_cpu_name_pair(
        monkeypatch, tmp_path, schema_version):
    payload = _all_pass_live_probe_payload(
        schema_version=schema_version,
        forged_cpu_pair=True,
    )

    def fake_run(argv, **kwargs):
        Path(argv[argv.index("--output") + 1]).write_text(
            payload, encoding="utf-8",
        )
        Path(kwargs["stdout_path"]).write_text(payload, encoding="utf-8")
        Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, payload, "")

    monkeypatch.setattr(driver, "_run", fake_run)

    with pytest.raises(driver.InfraFailure) as captured:
        driver._attest_environment(tmp_path)

    assert captured.value.reason_code == "parse_failure"


@pytest.mark.parametrize(
    "case,reason_code",
    [
        ("duplicate-key", "parse_failure"),
        ("typed-failure", "attestation"),
    ],
    ids=["duplicate-key", "typed-failure"],
)
def test_live_attestation_parser_failures_preserve_infra_reason(
        monkeypatch, tmp_path, case, reason_code):
    if case == "duplicate-key":
        payload = _all_pass_live_probe_payload(duplicate_schema_key=True)
    else:
        payload = json.dumps({
            "schema_version": "pegasus-probe-output/v2",
            "ok": False,
            "observed_epoch": 1,
            "error": {"stage": "probe", "type": "RuntimeError", "message": "x"},
        })

    def fake_run(argv, **kwargs):
        Path(argv[argv.index("--output") + 1]).write_text(
            payload, encoding="utf-8",
        )
        Path(kwargs["stdout_path"]).write_text(payload, encoding="utf-8")
        Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, payload, "")

    monkeypatch.setattr(driver, "_run", fake_run)
    with pytest.raises(driver.InfraFailure) as captured:
        driver._attest_environment(tmp_path)
    assert captured.value.reason_code == reason_code


@pytest.mark.parametrize("authority,want", [(2.0, False), (3.0, True)])
def test_silo_live_clock_wiring_moves_with_policy_and_uses_exact_keys(
        monkeypatch, tmp_path, authority, want):
    contract = driver.env_contract.lookup("pegasus")
    verified = driver.env_attestation.load_verified_calibration(contract, ROOT)
    assert verified.calibration is not None
    expected_raw = driver.env_attestation.profile_to_dict(
        verified.attestation_profile,
    )
    expected_raw["effective_clock"]["samples_mhz"] = [2101.0] * 48
    expected_raw["effective_clock"]["tolerance_pct"] = authority
    expected = driver.env_attestation.normalize_profile(expected_raw)
    calibration = dataclasses.replace(
        verified.calibration, attestation_profile=expected,
    )
    synthetic_verified = dataclasses.replace(
        verified,
        calibration=calibration,
        attestation_profile_sha256=(
            driver.env_attestation.profile_sha256(expected)
        ),
    )
    monkeypatch.setattr(
        driver.env_attestation, "load_verified_calibration",
        lambda _contract, _root: synthetic_verified,
    )
    monkeypatch.setattr(
        driver.execution_guard.effective_clock_policy,
        "EFFECTIVE_CLOCK_TOLERANCE_PCT", authority,
    )
    observed_raw = copy.deepcopy(expected_raw)
    del observed_raw["effective_clock"]["tolerance_pct"]
    observed_raw["effective_clock"]["samples_mhz"] = (
        [2101.0] * 47 + [2164.03]
    )
    payload = json.dumps({
        "schema_version": "pegasus-probe-output/v2",
        "ok": True,
        "observed_epoch": 1,
        "profile": observed_raw,
    })

    def fake_run(argv, **kwargs):
        Path(argv[argv.index("--output") + 1]).write_text(
            payload, encoding="utf-8",
        )
        Path(kwargs["stdout_path"]).write_text(payload, encoding="utf-8")
        Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, payload, "")

    calls = []
    real_predicate = driver.execution_guard.effective_clock_comparison_passes

    def predicate_spy(expected_clock, observed_clock):
        assert set(expected_clock) == {"samples_mhz", "tolerance_pct"}
        assert set(observed_clock) == {"samples_mhz"}
        calls.append((copy.deepcopy(expected_clock), copy.deepcopy(observed_clock)))
        return real_predicate(expected_clock, observed_clock)

    monkeypatch.setattr(driver, "_run", fake_run)
    monkeypatch.setattr(
        driver.execution_guard, "effective_clock_comparison_passes", predicate_spy,
    )
    if want:
        result = driver._attest_environment(tmp_path)
        assert result["effective_clock_match"] is True
        assert result["all_pass"] is True
    else:
        with pytest.raises(driver.InfraFailure) as captured:
            driver._attest_environment(tmp_path)
        assert captured.value.reason_code == "attestation"
    assert len(calls) == 1


def test_runtime_binding_covers_all_execution_semantics_modules():
    paths = {
        item["path"] for item in driver.runtime_modules_binding(ROOT)
    }
    expected = {
        "orchestrator/campaign/__init__.py",
        "orchestrator/campaign/silo_ladder_rung1_contract.py",
        "orchestrator/campaign/toolchain_binding.py",
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/env_contract_activation.py",
        *{
            path.relative_to(ROOT).as_posix()
            for path in (
                ROOT / "orchestrator/campaign/env_contract_activations"
            ).glob("*.json")
        },
        "orchestrator/campaign/env_attestation.py",
        "orchestrator/campaign/calibration_verify.py",
        "orchestrator/campaign/execution_guard.py",
        "orchestrator/calibrator/__init__.py",
        "orchestrator/calibrator/effective_clock_policy.py",
        "orchestrator/calibrator/schema_v2.py",
        "orchestrator/calibrator/tsc.py",
        "orchestrator/campaign/patchharness.py",
        "tools/pegasus/run_probe.py",
        *{
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "orchestrator/verifier").rglob("*.py")
        },
    }
    assert paths == expected


def test_tool_identity_set_includes_symbol_witness_tools(monkeypatch):
    monkeypatch.setattr(
        driver, "_tool_identity",
        lambda name, executable=None: {"name": name, "executable": executable},
    )
    identities = driver.capture_tool_identities()
    assert [item["name"] for item in identities] == [
        "git", "nm", "readelf", "cmake", "gcc", "g++", "python",
    ]
    assert identities[-1]["executable"] == sys.executable


def test_tool_version_body_ignores_only_argv0_and_rejects_body_mismatch():
    registered = "gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0"
    same_binary = (
        "x86_64-linux-gnu-gcc-11 "
        "(Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0"
    )
    different_binary = (
        "x86_64-linux-gnu-gcc-11 "
        "(Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.1"
    )

    assert driver.tool_version_body(same_binary) == (
        driver.tool_version_body(registered)
    )
    assert driver.tool_version_body(different_binary) != (
        driver.tool_version_body(registered)
    )


def test_dependency_pins_are_policy_bound_and_match_registered_calibration():
    policy = json.loads((TOOLS / "policy.json").read_text(encoding="utf-8"))
    pins = policy["silo_ladder_rung1"]["dependency_pins"]
    assert pins == driver._dependency_pins(ROOT)
    calibration = json.loads(
        (ROOT / driver.env_contract.lookup("pegasus").calibration_ref.path)
        .read_text(encoding="utf-8")
    )
    build_argv = calibration["acquisition_receipt"]["ccbench"]["build_argv"]
    assert {
        name: next(
            token.split("=", 1)[1] for token in build_argv
            if token.startswith(f"-DIZANAGI_{name.upper()}_SRC_HEAD=")
        )
        for name in ("gflags", "glog")
    } == pins


def _third_party_verifier_function(path: Path, next_marker: str) -> str:
    source = path.read_text(encoding="utf-8")
    start = source.index("verify_third_party_pinned_clean() {")
    end = source.index(next_marker, start)
    return source[start:end]


@pytest.mark.parametrize(
    ("script", "next_marker"),
    [
        (TOOLS / "submit_silo_ladder_rung1.sh", "\nusage() {"),
        (TOOLS / "silo_ladder_rung1.sh", "\nif [[ -z"),
    ],
    ids=("submitter", "job"),
)
def test_submitter_and_job_reject_third_party_head_mismatch(
    tmp_path, script, next_marker,
):
    spec = _fixture("third_party_head_mismatch.json")
    source = tmp_path / script.stem
    source.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(
        ["git", "-C", str(source), "config", "user.email",
         "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(source), "config", "user.name", "Fixture"],
        check=True,
    )
    (source / "README").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "README"], check=True)
    subprocess.run(
        ["git", "-C", str(source), "commit", "-qm", "fixture"],
        check=True,
    )
    fragment = _third_party_verifier_function(script, next_marker)
    checked = subprocess.run(
        [
            "bash", "-c",
            fragment + '\nverify_third_party_pinned_clean "$1" "$2" "$3"',
            "fixture", str(source), spec["expected_pin"], spec["name"],
        ],
        capture_output=True, text=True,
    )
    assert checked.returncode != 0
    assert spec["reason"] in checked.stderr


def test_driver_rejects_absent_third_party_staging(tmp_path):
    with pytest.raises(
        driver.ContractFailure, match="third-party source root is absent",
    ):
        driver.third_party_source_contract(ROOT, source_root=tmp_path / "absent")


def test_compile_invocation_summary_requires_exact_unique_source_set():
    document = _evidence(_fixture("p_plus_2.json"))
    invocations = document["correctness_leg"]["build"]["compile_invocations"]
    invocations[1] = copy.deepcopy(invocations[0])
    assert [item.reason_code for item in driver.validate_evidence(document)] == [
        "schema"
    ]


def test_terminal_attempt_must_be_successful_even_with_complete_gap_status():
    document = _evidence(_fixture("p_plus_2.json"))
    document["gap_leg"]["attempts"][-1].update({
        "failure_class": "contract",
        "reason_code": "contract_failure",
    })
    assert [item.reason_code for item in driver.validate_evidence(document)] == [
        "retry_policy"
    ]


def test_terminal_contract_failure_fixture_bundle_is_rejected(tmp_path):
    document = _evidence(_fixture("terminal_contract_failure.json"))
    raw = tmp_path / "terminal-contract-bundle"
    _materialize_raw_bundle(raw, document)
    failures = (
        driver.validate_evidence(document)
        + driver.validate_raw_bundle(document, raw)
    )
    assert "schema" in {item.reason_code for item in failures}


@pytest.mark.parametrize(
    ("stage", "returncode", "expected"),
    [
        ("interpreter_resolution", 2, ("infra", "nonzero_returncode")),
        ("qstat_initial", 2, ("infra", "nonzero_returncode")),
        ("qstat_driver", 124, ("infra", "timeout")),
        ("dependency_acquire", 2, ("infra", "nonzero_returncode")),
        ("dependency_extract", 2, ("infra", "nonzero_returncode")),
        ("attestation_acquisition", 2, ("infra", "nonzero_returncode")),
        ("post_driver_finalize", 2, ("infra", "nonzero_returncode")),
        ("dependency_build", 124, ("infra", "timeout")),
        ("dependency_build", 2, ("contract", "contract_failure")),
        ("policy_contract", 2, ("contract", "contract_failure")),
        ("schema_contract", 2, ("contract", "contract_failure")),
        ("json_contract", 2, ("contract", "contract_failure")),
    ],
)
def test_wrapper_failure_retry_set_is_closed(stage, returncode, expected):
    assert driver.classify_wrapper_failure(stage, returncode) == expected


@pytest.mark.parametrize(
    "bad",
    ["-UFOO", "-include", "-imacrosx", "@args.rsp", "-B/tmp/x",
     "-specs=/tmp/x", "-flto=auto"],
)
def test_compile_argv_gate_rejects_bypass_channels(bad):
    with pytest.raises(driver.DriverError, match="forbidden"):
        driver.validate_compile_argv(
            ["g++", bad, f"-D{driver.RUNG_MACRO}=1", "-c", "x.cc"],
            expected_macro=driver.RUNG_MACRO,
        )


def test_compile_argv_gate_requires_exactly_one_macro_and_clean_stock():
    good = ["g++", f"-D{driver.RUNG_MACRO}=1", "-c", "x.cc"]
    assert driver.validate_compile_argv(
        good, expected_macro=driver.RUNG_MACRO,
    ) == (driver.RUNG_MACRO,)
    with pytest.raises(driver.DriverError, match="exactly one"):
        driver.validate_compile_argv(
            good + [f"-D{driver.RUNG_MACRO}=1"],
            expected_macro=driver.RUNG_MACRO,
        )
    with pytest.raises(driver.DriverError, match="stock"):
        driver.validate_compile_argv(good, expected_macro=None)
    with pytest.raises(driver.DriverError, match="forbidden"):
        driver.validate_compile_argv(
            ["g++", "-D", f"{driver.RUNG_MACRO}=1", "-c", "x.cc"],
            expected_macro=None,
        )
    assert driver.validate_compile_argv(
        ["g++", f"-Wp,-D{driver.RUNG_MACRO}=1", "-c", "x.cc"],
        expected_macro=driver.RUNG_MACRO,
    ) == (driver.RUNG_MACRO,)
    for forwarded in (
        "-Wp,-include,/tmp/attack.h",
        "-Wp,-imacros,/tmp/attack.h",
        "-Wp,@args.rsp",
    ):
        with pytest.raises(driver.DriverError, match="forbidden"):
            driver.validate_compile_argv(
                ["g++", forwarded, f"-D{driver.RUNG_MACRO}=1", "-c", "x.cc"],
                expected_macro=driver.RUNG_MACRO,
            )
    with pytest.raises(driver.DriverError, match="exactly zero"):
        driver.validate_compile_argv(
            good + [f"-D{driver.REPORT_MACRO}=1"],
            expected_macro=driver.RUNG_MACRO,
        )


def test_multi_target_compile_commands_selects_one_ycsb_entry_per_tu():
    selected = driver.compile_commands_for_sources(
        _fixture("compile_commands_multi_target.json"),
        None,
    )

    assert [item["source_rel"] for item in selected] == list(
        driver.SOURCE_FILES
    )
    assert all(
        "/CMakeFiles/ycsb_silo.exe.dir/" in item["output"]
        for item in selected
    )


def test_compile_commands_extract_two_tus_and_replay_same_argv_object_sha(tmp_path):
    source = tmp_path / "source"
    transaction = source / "cc/silo/transaction.cc"
    ycsb = source / "cc/silo/ycsb_silo.cc"
    transaction.parent.mkdir(parents=True)
    transaction.write_text("fixture\n", encoding="utf-8")
    ycsb.write_text("fixture\n", encoding="utf-8")
    build = tmp_path / "build/cc/silo"
    build.mkdir(parents=True)
    compiler = tmp_path / "fixture-cxx"
    compiler.write_text(
        """#!/bin/sh
out=
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-o" ]; then out=$2; shift 2; continue; fi
  shift
done
printf 'deterministic fixture object\\n' >"$out"
""",
        encoding="utf-8",
    )
    compiler.chmod(0o755)
    target_object_dir = build / "CMakeFiles/ycsb_silo.exe.dir"
    target_object_dir.mkdir(parents=True)
    transaction_object = target_object_dir / "transaction.cc.o"
    ycsb_object = target_object_dir / "ycsb_silo.cc.o"
    for target in (transaction_object, ycsb_object):
        target.write_text("deterministic fixture object\n", encoding="utf-8")
    macro = f"-D{driver.RUNG_MACRO}=1"
    document = [
        {
            "directory": str(build),
            "file": str(transaction),
            "arguments": [
                str(compiler), macro, "-c", str(transaction),
                "-o", "CMakeFiles/tpcc_silo.exe.dir/transaction.cc.o",
            ],
            "output": "CMakeFiles/tpcc_silo.exe.dir/transaction.cc.o",
        },
        {
            "directory": str(build),
            "file": str(transaction),
            "arguments": [
                str(compiler), macro, "-c", str(transaction),
                "-o", str(transaction_object),
            ],
            "output": str(transaction_object),
        },
        {
            "directory": str(build),
            "file": str(ycsb),
            "command": " ".join([
                str(compiler), macro, "-c", str(ycsb),
                "-o", str(ycsb_object),
            ]),
            "output": str(ycsb_object),
        },
        {
            "directory": str(build),
            "file": str(transaction),
            "command": " ".join([
                str(compiler), macro, "-c", str(transaction),
                "-o", "CMakeFiles/bomb_silo.exe.dir/transaction.cc.o",
            ]),
        },
        {
            "directory": str(build),
            "file": str(transaction),
            "command": " ".join([
                str(compiler), macro, "-c", str(transaction),
                "-o", "CMakeFiles/sbomb_silo.exe.dir/transaction.cc.o",
            ]),
        },
    ]
    extracted = driver.compile_commands_for_sources(document, source)
    assert [item["source_rel"] for item in extracted] == list(driver.SOURCE_FILES)
    assert all(
        "/CMakeFiles/ycsb_silo.exe.dir/" in item["output"]
        for item in extracted
    )
    driver.validate_compile_argv(
        extracted[0]["argv"], expected_macro=driver.RUNG_MACRO,
    )
    replay = driver.reexecute_compile_and_compare(extracted[0])
    assert replay["replay_match"] is True
    assert replay["object_sha256"] == replay["replay_object_sha256"]


def test_duplicate_ycsb_target_compile_command_is_rejected():
    with pytest.raises(
        driver.DriverError,
        match="target TU compile command count mismatch",
    ):
        driver.compile_commands_for_sources(
            _fixture("compile_commands_duplicate_ycsb_target.json"),
            None,
        )


def test_publish_is_staging_hardlink_create_only_and_fsyncs(tmp_path):
    target = tmp_path / "final.json"
    driver.publish_create_only_json(target, {"fixture": True}, staging_dir=tmp_path)
    assert json.loads(target.read_text(encoding="utf-8")) == {"fixture": True}
    before = target.read_bytes()
    with pytest.raises(driver.DriverError, match="already exists"):
        driver.publish_create_only_json(target, {"fixture": False}, staging_dir=tmp_path)
    assert target.read_bytes() == before
    assert not list(tmp_path.glob("*.staging"))


def test_subprocess_command_receipt_is_create_only_and_binds_stream_hashes(
    tmp_path,
):
    receipt = tmp_path / "command.json"
    result = driver._run(
        [sys.executable, "-c", "print('receipt fixture')"],
        receipt_path=receipt,
    )
    assert result.returncode == 0
    document = json.loads(receipt.read_text(encoding="utf-8"))
    assert document["schema_version"] == driver.COMMAND_RECEIPT_SCHEMA
    assert document["argv"][0] == sys.executable
    assert document["returncode"] == 0
    assert document["timed_out"] is False
    assert document["stdout_sha256"] == driver.sha256_bytes(
        b"receipt fixture\n"
    )
    assert document["argv0_sha256"] == driver.sha256_file(Path(sys.executable))
    assert document["target_sha256"] is None
    with pytest.raises(driver.DriverError, match="already exists"):
        driver._run(
            [sys.executable, "-c", "pass"],
            receipt_path=receipt,
        )


def test_schema_rejects_empty_attestation_and_duplicate_build_ids():
    empty = _evidence(_fixture("p_plus_2.json"))
    empty["gap_leg"]["attestation"]["per_sample_solo_checks"] = []
    assert [item.reason_code for item in driver.validate_evidence(empty)] == [
        "schema"
    ]

    duplicate = _evidence(_fixture("p_plus_2.json"))
    duplicate["gap_leg"]["builds"][2]["id"] = "rung-perf"
    assert [item.reason_code for item in driver.validate_evidence(duplicate)] == [
        "activation"
    ]


def test_bounded_completion_is_separate_from_ever_committed_predicate():
    document = _evidence(_fixture("p_plus_2.json"))
    document["gap_leg"]["liveness_runs"][0]["bounded_completion"] = False
    assert [item.reason_code for item in driver.validate_evidence(document)] == [
        "bounded_completion"
    ]


def _materialize_raw_bundle(root: Path, document: dict) -> None:
    root.mkdir()
    active = root / "attempts/1"
    active.mkdir(parents=True)
    contract = driver.env_contract.lookup("pegasus")
    calibration_path = ROOT / contract.calibration_ref.path
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    document["binding"]["calibration"].update({
        "path": contract.calibration_ref.path,
        "sha256": driver.sha256_file(calibration_path),
        "contract_sha256": contract.contract_sha256,
    })
    document["gap_leg"]["attestation"]["calibration_sha256"] = (
        document["binding"]["calibration"]["sha256"]
    )
    document["gap_leg"]["attestation"]["contract_sha256"] = (
        contract.contract_sha256
    )
    observed_profile = copy.deepcopy(calibration["attestation_profile"])
    del observed_profile["effective_clock"]["tolerance_pct"]
    expected_samples = calibration["attestation_profile"]["effective_clock"][
        "samples_mhz"
    ]
    ordered_samples = sorted(expected_samples)
    middle = len(ordered_samples) // 2
    median = (ordered_samples[middle - 1] + ordered_samples[middle]) / 2.0
    # U-2/T-453 に適合する all-green fixture。旧 median-only outlier は別負例で保持する。
    observed_profile["effective_clock"]["samples_mhz"] = [
        median for _ in expected_samples
    ]
    (active / "attestation-job.json").write_text(json.dumps({
        "schema_version": "pegasus-probe-output/v2",
        "ok": True,
        "observed_epoch": 1,
        "profile": observed_profile,
    }), encoding="utf-8")
    (active / "schedule-receipt.json").write_text(
        json.dumps(document["gap_leg"]["schedule_receipt"]),
        encoding="utf-8",
    )
    prologue = active / "job-prologue"
    prologue.mkdir()
    for name, pin in driver._dependency_pins(ROOT).items():
        (prologue / f"{name}-source-head.txt").write_text(
            pin + "\n", encoding="utf-8",
        )
        (prologue / f"{name}-source-status.txt").write_text(
            "", encoding="utf-8",
        )
    correctness = root / "correctness"
    correctness.mkdir()
    (correctness / "verifier.json").write_text(
        json.dumps(document["correctness_leg"]["verifier"]),
        encoding="utf-8",
    )
    (correctness / "compile-replay.json").write_text(
        json.dumps({
            "invocations": document["correctness_leg"]["build"][
                "compile_invocations"
            ],
        }),
        encoding="utf-8",
    )
    correctness_object = b"fixture-rung-transaction-object\n"
    correctness_binary = b"fixture-correctness-binary\n"
    correctness_build = document["correctness_leg"]["build"]
    correctness_build["transaction_object_sha256"] = driver.sha256_bytes(
        correctness_object
    )
    correctness_build["binary_sha256"] = driver.sha256_bytes(correctness_binary)
    correctness_build["compile_invocations"][0].update({
        "object_sha256": correctness_build["transaction_object_sha256"],
        "replay_object_sha256": correctness_build["transaction_object_sha256"],
    })
    (correctness / "compile-replay.json").write_text(
        json.dumps({
            "invocations": correctness_build["compile_invocations"],
        }),
        encoding="utf-8",
    )
    gxx = next(
        item["realpath"] for item in document["provenance"]["tools"]
        if item["name"] == "g++"
    )
    gcc = next(
        item["realpath"] for item in document["provenance"]["tools"]
        if item["name"] == "gcc"
    )

    def compile_commands(macros):
        directory = "/fixture/build/cc/silo"

        def entry(relative, target):
            argv = [
                gxx, *(f"-D{macro}=1" for macro in macros),
                "-c", f"/fixture/source/{relative}",
                "-o", f"CMakeFiles/{target}.dir/{Path(relative).name}.o",
            ]
            return {
                "directory": directory,
                "file": f"/fixture/source/{relative}",
                "command": shlex.join(argv),
            }

        commands = [
            entry(relative, "ycsb_silo.exe")
            for relative in driver.SOURCE_FILES
        ]
        commands.extend(
            entry(driver.SOURCE_FILES[0], target)
            for target in ("tpcc_silo.exe", "bomb_silo.exe", "sbomb_silo.exe")
        )
        return commands

    def cmake_cache(macros, trace):
        flags = " ".join(f"-D{macro}=1" for macro in macros)
        return (
            "CCBENCH_CCACHE:STRING=OFF\n"
            f"CCBENCH_TRACE:STRING={trace}\n"
            f"CMAKE_C_COMPILER:FILEPATH={gcc}\n"
            f"CMAKE_CXX_COMPILER:FILEPATH={gxx}\n"
            f"CMAKE_CXX_FLAGS:STRING={flags}\n"
        )

    correctness_commands = compile_commands([driver.RUNG_MACRO])
    (correctness / "compile_commands.json").write_text(
        json.dumps(correctness_commands), encoding="utf-8",
    )
    command_by_source = {
        item["source_rel"]: item["argv"]
        for item in driver.compile_commands_for_sources(
            correctness_commands, None,
        )
    }
    for invocation in correctness_build["compile_invocations"]:
        invocation["argv"] = command_by_source[invocation["source_rel"]]
    (correctness / "compile-replay.json").write_text(
        json.dumps({
            "invocations": correctness_build["compile_invocations"],
        }),
        encoding="utf-8",
    )
    (correctness / "CMakeCache.txt").write_text(
        cmake_cache([driver.RUNG_MACRO], 1), encoding="utf-8",
    )
    symbol_line = f"00000000 T {driver.IDENTITY_SYMBOL}\n"
    (correctness / "binary.nm.txt").write_text(symbol_line, encoding="utf-8")
    (correctness / "binary.nm.stderr").write_text("", encoding="utf-8")
    (correctness / "transaction.nm.txt").write_text(
        symbol_line, encoding="utf-8",
    )
    (correctness / "transaction.nm.stderr").write_text("", encoding="utf-8")
    (correctness / "binary.readelf.txt").write_text(
        symbol_line, encoding="utf-8",
    )
    (correctness / "binary.readelf.stderr").write_text("", encoding="utf-8")
    traces = correctness / "traces"
    traces.mkdir()
    for worker in range(4):
        key = f"{worker + 1:02x}"
        (traces / f"trace_{worker}.log").write_text(
            f"C {worker} {worker} 1 {worker + 1} 0 1\n"
            f"W {worker} {key} U 1 {worker + 1}\n"
            f"E {worker}\n",
            encoding="utf-8",
        )
    runs = active / "runs"
    runs.mkdir()
    perf = {
        (item["workload"], item["rep"], item["variant"]): item
        for item in document["gap_leg"]["performance_runs"]
    }
    for row in document["gap_leg"]["schedule_receipt"]["runs"]:
        run = runs / (
            f"perf-{row['ordinal']:02d}-{row['workload']}-"
            f"{row['variant']}-r{row['rep']}"
        )
        run.mkdir()
        value = perf[(row["workload"], row["rep"], row["variant"])]
        (run / "stdout.txt").write_text(
            "commit_counts_:\t100\nbatch_commit_counts_:\t0\n"
            f"throughput[tps]:\t{value['throughput_tps']}\n",
            encoding="utf-8",
        )
        (run / "stderr.txt").write_text("", encoding="utf-8")
        value["stdout_sha256"] = driver.sha256_file(run / "stdout.txt")
        value["stderr_sha256"] = driver.sha256_file(run / "stderr.txt")
    live = {
        (item["workload"], item["rep"]): item
        for item in document["gap_leg"]["liveness_runs"]
    }
    ordinal = 24
    for workload in driver.WORKLOADS:
        for rep in (1, 2):
            run = runs / f"liveness-{ordinal:02d}-{workload}-r{rep}"
            run.mkdir()
            value = live[(workload, rep)]
            lines = [
                f"commit_counts_:\t{value['commit_count']}",
                "batch_commit_counts_:\t0",
                "throughput[tps]:\t1",
            ]
            lines.extend(
                f"silo_ladder_rung1.worker_commit[{item['worker']}]={item['commits']}"
                for item in value["per_worker_commits"]
            )
            lines.extend(
                f"silo_ladder_rung1.worker_batch_commit[{item['worker']}]=0"
                for item in value["per_worker_batch_commits"]
            )
            (run / "stdout.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            (run / "stderr.txt").write_text("", encoding="utf-8")
            value["stdout_sha256"] = driver.sha256_file(run / "stdout.txt")
            value["stderr_sha256"] = driver.sha256_file(run / "stderr.txt")
            ordinal += 1
    for build in document["gap_leg"]["builds"]:
        target = active / f"build-{build['id']}"
        target.mkdir()
        macros = build["macros"]
        object_bytes = (
            b"fixture-stock-transaction-object\n"
            if build["id"] == "stock" else correctness_object
        )
        binary_bytes = f"fixture-{build['id']}-binary\n".encode()
        build["transaction_object_sha256"] = driver.sha256_bytes(object_bytes)
        build["binary_sha256"] = driver.sha256_bytes(binary_bytes)
        build["compile_invocations"][0].update({
            "object_sha256": build["transaction_object_sha256"],
            "replay_object_sha256": build["transaction_object_sha256"],
        })
        replay = {"invocations": copy.deepcopy(build["compile_invocations"])}
        build_commands = compile_commands(macros)
        command_by_source = {
            item["source_rel"]: item["argv"]
            for item in driver.compile_commands_for_sources(
                build_commands, None,
            )
        }
        for invocation in build["compile_invocations"]:
            invocation["argv"] = command_by_source[invocation["source_rel"]]
        replay = {"invocations": copy.deepcopy(build["compile_invocations"])}
        (target / "compile-replay.json").write_text(
            json.dumps(replay), encoding="utf-8",
        )
        (target / "compile_commands.json").write_text(
            json.dumps(build_commands), encoding="utf-8",
        )
        (target / "CMakeCache.txt").write_text(
            cmake_cache(macros, 0), encoding="utf-8",
        )
        expected_count = 0 if build["id"] == "stock" else 1
        symbols = symbol_line if expected_count else ""
        (target / "binary.nm.txt").write_text(symbols, encoding="utf-8")
        (target / "binary.nm.stderr").write_text("", encoding="utf-8")
        (target / "transaction.nm.txt").write_text(
            symbols, encoding="utf-8",
        )
        (target / "transaction.nm.stderr").write_text("", encoding="utf-8")
        (target / "binary.readelf.txt").write_text(
            symbols, encoding="utf-8",
        )
        (target / "binary.readelf.stderr").write_text("", encoding="utf-8")
    for solo in document["gap_leg"]["attestation"]["per_sample_solo_checks"]:
        ordinal = solo["ordinal"]
        (active / f"solo-{ordinal:02d}.pgrep.stdout").write_text(
            "", encoding="utf-8",
        )
        (active / f"solo-{ordinal:02d}.pgrep.stderr").write_text(
            "", encoding="utf-8",
        )
        (active / f"solo-{ordinal:02d}.load.json").write_text(
            json.dumps({"load1": solo["load1"], "load5": 0.1, "load15": 0.1}),
            encoding="utf-8",
        )
    command = {
        "schema_version": driver.COMMAND_RECEIPT_SCHEMA,
        "argv": ["fixture-command"],
        "cwd": "/fixture",
        "started_at_utc": "2026-07-29T00:00:00Z",
        "completed_at_utc": "2026-07-29T00:00:01Z",
        "elapsed_monotonic_s": 1.0,
        "timeout_s": 60.0,
        "timed_out": False,
        "returncode": 0,
        "stdout_sha256": driver.sha256_bytes(b""),
        "stderr_sha256": driver.sha256_bytes(b""),
        "argv0_sha256": None,
        "target_sha256": None,
    }

    def write_command(
        path: Path, argv: list[str], stdout_path: Path, stderr_path: Path,
        *, argv0_sha256: str | None = None, target_sha256: str | None = None,
    ) -> None:
        receipt = {
            **command,
            "argv": argv,
            "stdout_sha256": driver.sha256_file(stdout_path),
            "stderr_sha256": driver.sha256_file(stderr_path),
            "argv0_sha256": argv0_sha256,
            "target_sha256": target_sha256,
        }
        path.write_text(json.dumps(receipt), encoding="utf-8")

    correctness_tools = {
        item["name"]: item for item in document["correctness_leg"]["provenance"]["tools"]
    }
    gap_tools = {
        item["name"]: item for item in document["provenance"]["tools"]
    }
    write_command(
        correctness / "binary.nm.command.json",
        [
            correctness_tools["nm"]["realpath"],
            "-g", "--defined-only", "/fixture/correctness",
        ],
        correctness / "binary.nm.txt", correctness / "binary.nm.stderr",
        argv0_sha256=correctness_tools["nm"]["sha256"],
        target_sha256=correctness_build["binary_sha256"],
    )
    write_command(
        correctness / "transaction.nm.command.json",
        [
            correctness_tools["nm"]["realpath"], "-g", "--defined-only",
            next(
                item["object_path"]
                for item in correctness_build["compile_invocations"]
                if item["source_rel"] == driver.SOURCE_FILES[0]
            ),
        ],
        correctness / "transaction.nm.txt", correctness / "transaction.nm.stderr",
        argv0_sha256=correctness_tools["nm"]["sha256"],
        target_sha256=correctness_build["transaction_object_sha256"],
    )
    write_command(
        correctness / "binary.readelf.command.json",
        [
            correctness_tools["readelf"]["realpath"],
            "-Ws", "/fixture/correctness",
        ],
        correctness / "binary.readelf.txt", correctness / "binary.readelf.stderr",
        argv0_sha256=correctness_tools["readelf"]["sha256"],
        target_sha256=correctness_build["binary_sha256"],
    )
    (correctness / "run.stdout").write_text(
        "commit_counts_:\t4\nbatch_commit_counts_:\t0\n"
        "throughput[tps]:\t4\n",
        encoding="utf-8",
    )
    (correctness / "run.stderr").write_text("", encoding="utf-8")
    write_command(
        correctness / "run.command.json",
        ["/fixture/correctness", *driver.CORRECTNESS_WORKLOAD],
        correctness / "run.stdout", correctness / "run.stderr",
        argv0_sha256=correctness_build["binary_sha256"],
        target_sha256=correctness_build["binary_sha256"],
    )
    for build in document["gap_leg"]["builds"]:
        target = active / f"build-{build['id']}"
        write_command(
            target / "binary.nm.command.json",
            [
                gap_tools["nm"]["realpath"],
                "-g", "--defined-only", f"/fixture/{build['id']}",
            ],
            target / "binary.nm.txt", target / "binary.nm.stderr",
            argv0_sha256=gap_tools["nm"]["sha256"],
            target_sha256=build["binary_sha256"],
        )
        write_command(
            target / "transaction.nm.command.json",
            [
                gap_tools["nm"]["realpath"], "-g", "--defined-only",
                next(
                    item["object_path"]
                    for item in build["compile_invocations"]
                    if item["source_rel"] == driver.SOURCE_FILES[0]
                ),
            ],
            target / "transaction.nm.txt", target / "transaction.nm.stderr",
            argv0_sha256=gap_tools["nm"]["sha256"],
            target_sha256=build["transaction_object_sha256"],
        )
        write_command(
            target / "binary.readelf.command.json",
            [
                gap_tools["readelf"]["realpath"],
                "-Ws", f"/fixture/{build['id']}",
            ],
            target / "binary.readelf.txt", target / "binary.readelf.stderr",
            argv0_sha256=gap_tools["readelf"]["sha256"],
            target_sha256=build["binary_sha256"],
        )
    for run in [
        *document["gap_leg"]["performance_runs"],
        *document["gap_leg"]["liveness_runs"],
    ]:
        run_dir = active / run["raw_path"]
        build = next(
            item for item in document["gap_leg"]["builds"]
            if item["id"] == run["binary_id"]
        )
        write_command(
            run_dir / "run.command.json", run["argv"],
            run_dir / "stdout.txt", run_dir / "stderr.txt",
            argv0_sha256=build["binary_sha256"],
            target_sha256=build["binary_sha256"],
        )
    (active / "fixture.command.json").write_text(
        json.dumps(command), encoding="utf-8",
    )
    commands = active / "commands"
    commands.mkdir()
    for ordinal in range(28):
        receipt = {
            **command,
            "argv": ["pgrep", "-a", "-f", r"ycsb_.*\.exe"],
            "returncode": 1,
        }
        (commands / f"{ordinal:04d}-pgrep.command.json").write_text(
            json.dumps(receipt), encoding="utf-8",
        )
    (active / "pbs-accounting.txt").write_text(
        _text_fixture("nqsv_accounting_epilogue.txt").replace(
            "873909.nqsv", "fixture-job",
        ),
        encoding="utf-8",
    )
    attempt = document["gap_leg"]["attempts"][0]
    (active / "submit-receipt.json").write_text(
        json.dumps({
            "nonce": attempt["nonce"],
            "campaign_id": "c" * 64,
            "qsub": {"request_id": attempt["job_id"]},
        }),
        encoding="utf-8",
    )
    attempt["submit_receipt_sha256"] = driver.sha256_file(
        active / "submit-receipt.json"
    )
    attempt_receipt = driver.write_attempt_receipt(active, 1)
    attempt["attempt_receipt_sha256"] = driver.sha256_file(attempt_receipt)
    driver.write_raw_manifest(active)
    seals = root / "campaign-attempt-root-receipts"
    seals.mkdir()
    seal = {
        "schema_version": "silo_ladder_rung1-campaign-attempt-root/v1",
        "campaign_id": "c" * 64,
        "attempt": 1,
        "job_id": attempt["job_id"],
        "nonce": attempt["nonce"],
        "submit_receipt_sha256": attempt["submit_receipt_sha256"],
        "attempt_receipt_sha256": attempt["attempt_receipt_sha256"],
        "failure_class": None,
        "reason_code": None,
    }
    (seals / "1.json").write_text(json.dumps(seal), encoding="utf-8")
    attempt["campaign_attempt_root_receipt"]["sha256"] = driver.sha256_file(
        seals / "1.json"
    )
    (root / "campaign-root-receipt.json").write_text(
        json.dumps({
            "schema_version": "silo_ladder_rung1-campaign-root-final/v1",
            "campaign_id": "c" * 64,
            "schedule_receipt": document["gap_leg"]["schedule_receipt"],
            "bindings": {},
            "attempts": [seal],
        }),
        encoding="utf-8",
    )
    (root / "gap-result-receipt.json").write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-gap-receipt/v1",
        "gap_leg": document["gap_leg"],
    }), encoding="utf-8")
    (root / "provenance-receipt.json").write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-provenance-receipt/v1",
        "provenance": document["provenance"],
    }), encoding="utf-8")
    driver.write_raw_manifest(root)
    document["raw_bundle"]["paths"] = driver.validate_raw_manifest(root)


def test_raw_bundle_major_predicates_are_recomputed_from_files(tmp_path):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    manifest = json.loads(
        (raw / "raw-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == driver.RAW_MANIFEST_SCHEMA
    assert {item["path"] for item in manifest["files"]} == (
        set(document["raw_bundle"]["paths"]) - {"raw-manifest.json"}
    )
    assert "attempts/1/raw-manifest.json" in document["raw_bundle"]["paths"]
    assert document["raw_bundle"]["paths"].count("raw-manifest.json") == 1
    assert not any(
        path.endswith(("transaction.o", "ycsb_silo.exe"))
        for path in document["raw_bundle"]["paths"]
    )
    assert driver.validate_raw_bundle(document, raw) == ()
    first = raw / "attempts/1/runs/perf-00-W-cal-stock-r1/stdout.txt"
    if not first.exists():
        first = next((raw / "attempts/1/runs").glob("perf-00-*/stdout.txt"))
    first.write_text(
        first.read_text(encoding="utf-8").replace(
            "throughput[tps]:", "throughput[tps]:\t999999999\nignored:"
        ),
        encoding="utf-8",
    )
    failures = driver.validate_raw_bundle(document, raw)
    assert [item.reason_code for item in failures] == ["raw_bundle"]


def test_raw_bundle_correctness_commit_witness_mismatch_rejects(tmp_path):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    stdout_path = raw / "correctness/run.stdout"
    stdout_path.write_text(
        stdout_path.read_text(encoding="utf-8").replace(
            "commit_counts_:\t4", "commit_counts_:\t5",
        ),
        encoding="utf-8",
    )
    command_path = raw / "correctness/run.command.json"
    command = json.loads(command_path.read_text(encoding="utf-8"))
    command["stdout_sha256"] = driver.sha256_file(stdout_path)
    command_path.write_text(json.dumps(command), encoding="utf-8")
    (raw / "raw-manifest.json").unlink()
    driver.write_raw_manifest(raw)
    document["raw_bundle"]["paths"] = driver.validate_raw_manifest(raw)

    failures = driver.validate_raw_bundle(document, raw)
    assert [item.reason_code for item in failures] == ["raw_bundle"]
    assert "commit witness differs from verifier txns" in failures[0].detail


def test_raw_bundle_recomputes_write_intent_violations(tmp_path):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    verifier_path = raw / "correctness/verifier.json"
    verifier = json.loads(verifier_path.read_text(encoding="utf-8"))
    verifier["results"][0]["integrity"]["write_intent_violations"] = 1
    verifier_path.write_text(json.dumps(verifier), encoding="utf-8")
    document["correctness_leg"]["verifier"] = verifier
    (raw / "raw-manifest.json").unlink()
    driver.write_raw_manifest(raw)
    document["raw_bundle"]["paths"] = driver.validate_raw_manifest(raw)
    assert [item.reason_code for item in driver.validate_raw_bundle(
        document, raw,
    )] == ["raw_bundle"]


def _reseal_materialized_raw(root: Path, document: dict) -> None:
    active = root / "attempts/1"
    (root / "raw-manifest.json").unlink()
    (active / "raw-manifest.json").unlink()
    (active / "attempt-receipt.json").unlink()
    receipt = driver.write_attempt_receipt(active, 1)
    attempt = document["gap_leg"]["attempts"][0]
    attempt["attempt_receipt_sha256"] = driver.sha256_file(receipt)
    driver.write_raw_manifest(active)
    seal_path = root / "campaign-attempt-root-receipts/1.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["attempt_receipt_sha256"] = attempt["attempt_receipt_sha256"]
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    attempt["campaign_attempt_root_receipt"]["sha256"] = driver.sha256_file(
        seal_path
    )
    campaign = json.loads(
        (root / "campaign-root-receipt.json").read_text(encoding="utf-8")
    )
    campaign["attempts"] = [seal]
    (root / "campaign-root-receipt.json").write_text(
        json.dumps(campaign), encoding="utf-8",
    )
    (root / "gap-result-receipt.json").write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-gap-receipt/v1",
        "gap_leg": document["gap_leg"],
    }), encoding="utf-8")
    driver.write_raw_manifest(root)
    document["raw_bundle"]["paths"] = driver.validate_raw_manifest(root)


@pytest.mark.parametrize(
    "case",
    [
        "malformed",
        "duplicate-key",
        "typed-failure",
    ],
    ids=["malformed", "duplicate-key", "typed-failure"],
)
def test_raw_attestation_parser_failures_remain_raw_bundle_evidence(
        tmp_path, case):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    probe_path = raw / "attempts/1/attestation-job.json"
    if case == "malformed":
        payload = "{"
    elif case == "duplicate-key":
        payload = probe_path.read_text(encoding="utf-8").replace(
            '{"schema_version": "pegasus-probe-output/v2",',
            ('{"schema_version": "pegasus-probe-output/v2", '
             '"schema_version": "pegasus-probe-output/v2",'),
            1,
        )
    else:
        payload = json.dumps({
            "schema_version": "pegasus-probe-output/v2",
            "ok": False,
            "observed_epoch": 1,
            "error": {"stage": "probe", "type": "RuntimeError", "message": "x"},
        })
    probe_path.write_text(payload, encoding="utf-8")
    _reseal_materialized_raw(raw, document)

    failures = driver.validate_raw_bundle(document, raw)

    assert [item.reason_code for item in failures] == ["raw_bundle"]


@pytest.mark.parametrize("schema_version", [
    driver.env_attestation.PEGASUS_PROBE_OUTPUT_V1,
    driver.env_attestation.PEGASUS_PROBE_OUTPUT_V2,
])
def test_raw_attestation_rejects_forged_cpu_name_pair(
        tmp_path, schema_version):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    probe_path = raw / "attempts/1/attestation-job.json"
    payload = json.loads(probe_path.read_text(encoding="utf-8"))
    payload["schema_version"] = schema_version
    if schema_version == driver.env_attestation.PEGASUS_PROBE_OUTPUT_V1:
        payload["profile"]["effective_clock"]["tolerance_pct"] = 100.0
    payload["profile"]["cpu"].update({
        "model_name_raw": "Intel Xeon Platinum 8468H",
        "model_name_normalized": "Intel Xeon Platinum 8468",
    })
    probe_path.write_text(json.dumps(payload), encoding="utf-8")
    _reseal_materialized_raw(raw, document)

    failures = driver.validate_raw_bundle(document, raw)

    assert [item.reason_code for item in failures] == ["raw_bundle"]


def test_silo_raw_clock_wiring_moves_with_policy_and_uses_exact_keys(
        tmp_path, monkeypatch):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    probe_path = raw / "attempts/1/attestation-job.json"
    payload = json.loads(probe_path.read_text(encoding="utf-8"))
    payload["profile"]["effective_clock"]["samples_mhz"] = (
        [2101.0] * 47 + [2164.03]
    )
    probe_path.write_text(json.dumps(payload), encoding="utf-8")
    _reseal_materialized_raw(raw, document)

    # 2% authority では +3% vector を current raw replay が拒否する。
    failures = driver.validate_raw_bundle(document, raw)
    assert [item.reason_code for item in failures] == ["raw_bundle"]

    real_load_json = driver._load_json
    calibration_path = (
        ROOT / document["binding"]["calibration"]["path"]
    ).resolve()

    def policy_three_calibration(path):
        loaded = real_load_json(path)
        if Path(path).resolve() == calibration_path:
            loaded = copy.deepcopy(loaded)
            loaded["attestation_profile"]["effective_clock"][
                "tolerance_pct"
            ] = 3.0
        return loaded

    monkeypatch.setattr(driver, "_load_json", policy_three_calibration)
    monkeypatch.setattr(
        driver.execution_guard.effective_clock_policy,
        "EFFECTIVE_CLOCK_TOLERANCE_PCT", 3.0,
    )
    calls = []
    real_predicate = driver.execution_guard.effective_clock_comparison_passes

    def predicate_spy(expected_clock, observed_clock):
        assert set(expected_clock) == {"samples_mhz", "tolerance_pct"}
        assert set(observed_clock) == {"samples_mhz"}
        calls.append((copy.deepcopy(expected_clock), copy.deepcopy(observed_clock)))
        return real_predicate(expected_clock, observed_clock)

    monkeypatch.setattr(
        driver.execution_guard, "effective_clock_comparison_passes", predicate_spy,
    )

    assert driver.validate_raw_bundle(document, raw) == ()
    assert len(calls) == 1


def test_raw_bundle_rejects_duplicate_ycsb_target_compile_entry(tmp_path):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    commands_path = raw / "correctness/compile_commands.json"
    commands = json.loads(commands_path.read_text(encoding="utf-8"))
    transaction = next(
        entry for entry in commands
        if entry["file"].endswith(driver.SOURCE_FILES[0])
        and "CMakeFiles/ycsb_silo.exe.dir/" in entry["command"]
    )
    duplicate = copy.deepcopy(transaction)
    duplicate["command"] = duplicate["command"].replace(
        "CMakeFiles/ycsb_silo.exe.dir/transaction.cc.o",
        "CMakeFiles/ycsb_silo.exe.dir/transaction-duplicate.cc.o",
    )
    commands.append(duplicate)
    commands_path.write_text(json.dumps(commands), encoding="utf-8")
    _reseal_materialized_raw(raw, document)

    failures = driver.validate_raw_bundle(document, raw)

    assert [item.reason_code for item in failures] == ["raw_bundle"]
    assert "target TU compile command count mismatch" in failures[0].detail


@pytest.mark.parametrize(
    "broken_link",
    [
        "compile-replay", "nm-target", "run-binary",
        "nm-argv0", "nm-argv0-path", "readelf-argv0",
        "correctness-run-argv", "correctness-run-rc",
        "correctness-run-target", "correctness-run-stdout",
        "correctness-run-stderr", "correctness-nm-argv",
        "correctness-nm-rc", "correctness-nm-stderr",
        "correctness-nm-argv0", "correctness-readelf-argv0",
        "dependency-head",
    ],
)
def test_raw_hash_chain_rejects_exactly_one_broken_link(tmp_path, broken_link):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    active = raw / "attempts/1"
    if broken_link == "compile-replay":
        path = active / "build-stock/compile-replay.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["invocations"][0]["object_sha256"] = "0" * 64
        value["invocations"][0]["replay_object_sha256"] = "0" * 64
    elif broken_link == "nm-target":
        path = active / "build-stock/transaction.nm.command.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["target_sha256"] = "0" * 64
    elif broken_link in {"nm-argv0", "readelf-argv0"}:
        receipt_name = (
            "transaction.nm.command.json"
            if broken_link == "nm-argv0"
            else "binary.readelf.command.json"
        )
        path = active / "build-stock" / receipt_name
        value = json.loads(path.read_text(encoding="utf-8"))
        value["argv0_sha256"] = None
    elif broken_link == "nm-argv0-path":
        path = active / "build-stock/transaction.nm.command.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        assert Path(value["argv"][0]).name == "nm"
        value["argv"][0] = "/different-provenance-tool/nm"
    elif broken_link == "run-binary":
        run = document["gap_leg"]["performance_runs"][0]
        path = active / run["raw_path"] / "run.command.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["argv0_sha256"] = "0" * 64
    elif broken_link == "dependency-head":
        path = active / "job-prologue/gflags-source-head.txt"
        path.write_text("0" * 40 + "\n", encoding="utf-8")
        value = None
    else:
        correctness = raw / "correctness"
        if broken_link.startswith("correctness-readelf-"):
            receipt_name = "binary.readelf.command.json"
        elif broken_link.startswith("correctness-nm-"):
            receipt_name = "binary.nm.command.json"
        else:
            receipt_name = "run.command.json"
        path = correctness / receipt_name
        value = json.loads(path.read_text(encoding="utf-8"))
        field = broken_link.rsplit("-", 1)[1]
        if field == "argv":
            value["argv"] = [*value["argv"], "--unexpected"]
        elif field == "rc":
            value["returncode"] = 1
        elif field == "target":
            value["target_sha256"] = "0" * 64
        elif field == "stdout":
            value["stdout_sha256"] = "0" * 64
        elif field == "argv0":
            value["argv0_sha256"] = "0" * 64
        else:
            assert field == "stderr"
            value["stderr_sha256"] = "0" * 64
    if value is not None:
        path.write_text(json.dumps(value), encoding="utf-8")
    _reseal_materialized_raw(raw, document)
    failures = driver.validate_raw_bundle(document, raw)
    assert [item.reason_code for item in failures] == ["raw_bundle"]


def test_attempt_two_bundle_isolated_and_each_subtree_sealed(tmp_path):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    (raw / "raw-manifest.json").unlink()
    first_root = raw / "attempts/1"
    second_root = raw / "attempts/2"
    shutil.copytree(first_root, second_root)
    epilogue = _text_fixture("nqsv_accounting_epilogue.txt")
    (first_root / "pbs-accounting.txt").write_text(
        epilogue.replace("873909.nqsv", "fixture-job-1"),
        encoding="utf-8",
    )
    (second_root / "pbs-accounting.txt").write_text(
        epilogue.replace("873909.nqsv", "fixture-job-2"),
        encoding="utf-8",
    )
    for root in (first_root, second_root):
        (root / "raw-manifest.json").unlink()
        (root / "attempt-receipt.json").unlink()
    wrapper = {
        "schema_version": "silo_ladder_rung1-failure/v1",
        "pbs_jobid": "fixture-job-1",
        "rc": 2,
        "stage": "shell",
        "message": "fixture infra",
        "recorded_epoch": 1,
        "failure_class": "infra",
        "reason_code": "nonzero_returncode",
        "attempt_number": 1,
    }
    (first_root / "wrapper-failure.json").write_text(
        json.dumps(wrapper), encoding="utf-8",
    )
    (first_root / "submit-receipt.json").write_text(
        json.dumps({
            "nonce": "e" * 32,
            "campaign_id": "c" * 64,
            "qsub": {"request_id": "fixture-job-1"},
        }),
        encoding="utf-8",
    )
    (second_root / "submit-receipt.json").write_text(
        json.dumps({
            "nonce": "2" * 32,
            "campaign_id": "c" * 64,
            "qsub": {"request_id": "fixture-job-2"},
        }),
        encoding="utf-8",
    )
    first_receipt = driver.write_attempt_receipt(first_root, 1)
    driver.write_raw_manifest(first_root)
    second_receipt = driver.write_attempt_receipt(second_root, 2)
    driver.write_raw_manifest(second_root)
    first = {
        **copy.deepcopy(document["gap_leg"]["attempts"][0]),
        "failure_class": "infra",
        "reason_code": "nonzero_returncode",
        "job_id": "fixture-job-1",
        "submit_receipt_sha256": driver.sha256_file(
            first_root / "submit-receipt.json"
        ),
        "attempt_receipt_sha256": driver.sha256_file(first_receipt),
    }
    second = {
        **copy.deepcopy(document["gap_leg"]["attempts"][0]),
        "attempt": 2,
        "raw_root": "attempts/2",
        "job_id": "fixture-job-2",
        "nonce": "2" * 32,
        "submit_receipt_sha256": "2" * 64,
        "attempt_receipt_sha256": driver.sha256_file(second_receipt),
        "campaign_attempt_root_receipt": {
            "path": "fixture/campaign/attempt-2/attempt-root-receipt.json",
            "sha256": "",
        },
    }
    second["submit_receipt_sha256"] = driver.sha256_file(
        second_root / "submit-receipt.json"
    )
    document["gap_leg"]["attempts"] = [first, second]
    seals = raw / "campaign-attempt-root-receipts"
    seal_docs = []
    for attempt in (first, second):
        seal = {
            "schema_version": "silo_ladder_rung1-campaign-attempt-root/v1",
            "campaign_id": "c" * 64,
            "attempt": attempt["attempt"],
            "job_id": attempt["job_id"],
            "nonce": attempt["nonce"],
            "submit_receipt_sha256": attempt["submit_receipt_sha256"],
            "attempt_receipt_sha256": attempt["attempt_receipt_sha256"],
            "failure_class": attempt["failure_class"],
            "reason_code": attempt["reason_code"],
        }
        path = seals / f"{attempt['attempt']}.json"
        path.write_text(json.dumps(seal), encoding="utf-8")
        attempt["campaign_attempt_root_receipt"]["sha256"] = driver.sha256_file(path)
        seal_docs.append(seal)
    campaign = json.loads(
        (raw / "campaign-root-receipt.json").read_text(encoding="utf-8")
    )
    campaign["attempts"] = seal_docs
    (raw / "campaign-root-receipt.json").write_text(
        json.dumps(campaign), encoding="utf-8",
    )
    (raw / "gap-result-receipt.json").write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-gap-receipt/v1",
        "gap_leg": document["gap_leg"],
    }), encoding="utf-8")
    driver.write_raw_manifest(raw)
    document["raw_bundle"]["paths"] = driver.validate_raw_manifest(raw)
    assert driver.validate_raw_bundle(document, raw) == ()
    assert document["raw_bundle"]["paths"].count("raw-manifest.json") == 1
    assert {
        "attempts/1/raw-manifest.json",
        "attempts/2/raw-manifest.json",
    } <= set(document["raw_bundle"]["paths"])
    # top-level manifest だけを mutation 後に再封印しても、prior self-manifest
    # と attempt receipt の内部集合が stale なので受理しない。
    (raw / "raw-manifest.json").unlink()
    (first_root / "post-submit-mutation.log").write_text(
        "mutated after attempt-2 submit\n", encoding="utf-8",
    )
    driver.write_raw_manifest(raw)
    document["raw_bundle"]["paths"] = driver.validate_raw_manifest(raw)
    assert [item.reason_code for item in driver.validate_raw_bundle(
        document, raw,
    )] == ["raw_bundle"]


def test_nqsv_accounting_epilogue_accepts_real_terminal_fields():
    epilogue = _text_fixture("nqsv_accounting_epilogue.txt")
    accounting = driver.validate_nqsv_accounting_epilogue(
        epilogue, "873909.nqsv",
    )
    assert "Request ID:             873909.nqsv" in accounting
    assert any("Started Request Time:" in line for line in accounting)
    assert any("Ended Request Time:" in line for line in accounting)
    assert any("Elapse:" in line for line in accounting)
    assert "exit_status" not in epilogue.lower()


def test_nqsv_accounting_epilogue_rejects_request_id_mismatch():
    epilogue = _text_fixture("nqsv_accounting_epilogue.txt")
    with pytest.raises(driver.ContractFailure, match="Request ID mismatch"):
        driver.validate_nqsv_accounting_epilogue(
            epilogue, "873910.nqsv",
        )


def test_nqsv_accounting_epilogue_rejects_missing_started_time():
    epilogue = _text_fixture("nqsv_accounting_epilogue.txt")
    epilogue = "\n".join(
        line for line in epilogue.splitlines()
        if "Started Request Time:" not in line
    )
    with pytest.raises(
        driver.ContractFailure, match="Started Request Time",
    ):
        driver.validate_nqsv_accounting_epilogue(
            epilogue, "873909.nqsv",
        )


def test_collect_classifies_complete_gap_without_success_sentinel_as_infra(tmp_path):
    correctness = tmp_path / "correctness.json"
    correctness.write_text("{}\n", encoding="utf-8")
    staging = tmp_path / "job"
    staging.mkdir()
    (staging / "gap-result.json").write_text(
        json.dumps({"status": "complete", "attempt_number": 1}),
        encoding="utf-8",
    )
    with pytest.raises(driver.InfraFailure) as captured:
        driver._collect_command(
            correctness, staging,
            tmp_path / "scheduler.o1", tmp_path / "scheduler.e1",
            tmp_path / "output.json",
        )
    assert captured.value.reason_code == "nonzero_returncode"


def test_collect_uses_post_driver_wrapper_failure_receipt_as_infra(tmp_path):
    correctness = tmp_path / "correctness.json"
    correctness.write_text("{}\n", encoding="utf-8")
    staging = tmp_path / "job"
    staging.mkdir()
    (staging / "gap-result.json").write_text(
        json.dumps({"status": "complete", "attempt_number": 1}),
        encoding="utf-8",
    )
    (staging / "failure.json").write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-failure/v1",
        "pbs_jobid": "fixture-job",
        "rc": 1,
        "stage": "post_driver_finalize",
        "message": "sentinel write failed",
        "recorded_epoch": 1,
        "failure_class": "infra",
        "reason_code": "nonzero_returncode",
        "attempt_number": 1,
    }), encoding="utf-8")
    with pytest.raises(driver.InfraFailure) as captured:
        driver._collect_command(
            correctness, staging,
            tmp_path / "scheduler.o1", tmp_path / "scheduler.e1",
            tmp_path / "output.json",
        )
    assert captured.value.reason_code == "nonzero_returncode"


def test_collect_fixture_bundle_publishes_without_self_rejection(
    tmp_path, monkeypatch,
):
    repo = tmp_path / "repo"
    job_staging = repo / "job"
    correctness_dir = repo / "correctness"
    repo.mkdir()
    document = _evidence(_fixture("p_plus_2.json"))
    materialized = tmp_path / "materialized"
    _materialize_raw_bundle(materialized, document)

    correctness_dir.mkdir()
    shutil.copytree(materialized / "correctness", correctness_dir / "raw")
    correctness_json = correctness_dir / "correctness.json"
    correctness_json.write_text(
        json.dumps(document["correctness_leg"]), encoding="utf-8",
    )
    ccbench_fixture = repo / "external/ccbench"
    ccbench_fixture.parent.mkdir(parents=True)
    subprocess.run(
        [
            "git", "clone", "--quiet", "--shared",
            str(ROOT / "external/ccbench"), str(ccbench_fixture),
        ],
        check=True,
    )
    source_raw = job_staging / "attempt-1/raw"
    shutil.copytree(materialized / "attempts/1", source_raw)
    for relative in (
        "attempt-receipt.json", "raw-manifest.json", "pbs-accounting.txt",
    ):
        (source_raw / relative).unlink()

    copied_paths = (
        "tools/pegasus/policy.json",
        "tools/pegasus/silo_ladder_rung1.sh",
        "tools/pegasus/submit_silo_ladder_rung1.sh",
        "patches/silo_ladder_rung1.patch",
        "patches/ledger.json",
        "orchestrator/verifier/report.py",
        "external/ccbench/cmake/ThirdParty.cmake",
    )
    for relative in copied_paths:
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    calibration_relative = document["binding"]["calibration"]["path"]
    calibration_destination = repo / calibration_relative
    calibration_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / calibration_relative, calibration_destination)

    schedule_bytes = (
        json.dumps(
            document["gap_leg"]["schedule_receipt"],
            ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n"
    ).encode("utf-8")
    runtime_sha256 = "a" * 64
    expected_patched = {
        path: "f" * 64 for path in driver.SOURCE_FILES
    }
    frozen = {
        "job_script_sha256": driver.sha256_file(
            repo / "tools/pegasus/silo_ladder_rung1.sh"
        ),
        "driver_sha256": driver.sha256_file(Path(driver.__file__).resolve()),
        "patch_sha256": driver.sha256_file(
            repo / "patches/silo_ladder_rung1.patch"
        ),
        "ledger_sha256": driver.sha256_file(repo / "patches/ledger.json"),
        "submitter_sha256": driver.sha256_file(
            repo / "tools/pegasus/submit_silo_ladder_rung1.sh"
        ),
        "verifier_module_sha256": driver.sha256_file(
            repo / "orchestrator/verifier/report.py"
        ),
        "policy_sha256": driver.sha256_file(
            repo / "tools/pegasus/policy.json"
        ),
        "runtime_modules_sha256": runtime_sha256,
        "correctness_sha256": driver.sha256_file(correctness_json),
        "schedule_sha256": driver.sha256_bytes(schedule_bytes),
        "third_party_heads": {
            item["name"]: item["pin"]
            for item in driver.third_party_policy(ROOT)
        },
    }
    campaign_id = "c" * 64
    campaign_path = repo / "fixture/campaign/campaign-root.json"
    campaign_path.parent.mkdir(parents=True)
    campaign_path.write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-campaign-root/v1",
        "campaign_id": campaign_id,
        "first_attempt": 1,
        "attempt_chain": [1, 2],
        "schedule_receipt": document["gap_leg"]["schedule_receipt"],
        "bindings": {
            **frozen,
            "ccbench_pin_full": driver.PIN,
            "expected_patched_source_sha256": expected_patched,
        },
    }), encoding="utf-8")
    submit = {
        "nonce": "e" * 32,
        "campaign_id": campaign_id,
        "qsub": {"request_id": "fixture-job"},
        "bindings": frozen,
        "campaign_root_receipt": {
            "path": campaign_path.relative_to(repo).as_posix(),
            "sha256": driver.sha256_file(campaign_path),
        },
    }
    submit_path = job_staging / "submit-receipt.json"
    submit_path.parent.mkdir(parents=True, exist_ok=True)
    submit_path.write_text(json.dumps(submit), encoding="utf-8")
    (source_raw / "submit-receipt.json").write_text(
        json.dumps(submit), encoding="utf-8",
    )
    attempt = document["gap_leg"]["attempts"][0]
    attempt.update({
        "raw_root": "attempt-1/raw",
        "attempt_receipt_sha256": None,
        "submit_receipt_sha256": driver.sha256_file(submit_path),
        "campaign_attempt_root_receipt": None,
    })
    (job_staging / "gap-result.json").write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-gap-job/v1",
        "pbs_jobid": "fixture-job",
        "attempt_number": 1,
        "status": "complete",
        "failure_class": None,
        "reason_code": None,
        "provenance": document["provenance"],
        "gap_leg": document["gap_leg"],
        "checks": document["checks"],
        "raw_paths": [],
    }), encoding="utf-8")
    (job_staging / "success.json").write_text(json.dumps({
        "schema_version": "silo_ladder_rung1-success-sentinel/v1",
        "pbs_jobid": "fixture-job",
        "exit_status": 0,
        "completed_at_utc": "2026-07-29T00:00:00Z",
    }), encoding="utf-8")
    scheduler_stdout = repo / "scheduler.ofixture-job"
    scheduler_stderr = repo / "scheduler.efixture-job"
    scheduler_stdout.write_text("", encoding="utf-8")
    scheduler_stderr.write_text(
        _text_fixture("nqsv_accounting_epilogue.txt").replace(
            "873909.nqsv", "fixture-job",
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(driver, "_repo_root", lambda: repo)
    monkeypatch.setattr(
        driver, "runtime_modules_sha256", lambda _repo: runtime_sha256,
    )
    monkeypatch.setattr(
        driver, "_expected_patched_source_hashes",
        lambda *_args, **_kwargs: expected_patched,
    )
    monkeypatch.setattr(
        driver, "_binding", lambda _repo: copy.deepcopy(document["binding"]),
    )

    def validate_bindings_with_receipt(_document, _repo):
        result = driver._run([
            sys.executable, "-c", "print('fixture collect binding validation')",
        ])
        assert result.returncode == 0
        return ()

    monkeypatch.setattr(
        driver, "validate_current_bindings", validate_bindings_with_receipt,
    )
    output = repo / "published.json"
    published = driver._collect_command(
        correctness_json, job_staging,
        scheduler_stdout, scheduler_stderr, output,
    )

    assert published == output
    final = json.loads(output.read_text(encoding="utf-8"))
    raw_root = repo / final["raw_bundle"]["root"]
    active_root = raw_root / "attempts/1"
    assert driver.validate_attempt_subtree(active_root, 1)
    assert not (active_root / "commands-collect").exists()
    assert len(list((raw_root / "commands-collect").glob("*.command.json"))) == 1
    assert (
        f"commands-collect/0000-{Path(sys.executable).name}.command.json"
        in final["raw_bundle"]["paths"]
    )


def test_campaign_attempt_root_rejects_one_job_id_link_cut(tmp_path):
    document = _evidence(_fixture("p_plus_2.json"))
    raw = tmp_path / "raw"
    _materialize_raw_bundle(raw, document)
    (raw / "raw-manifest.json").unlink()
    seal_path = raw / "campaign-attempt-root-receipts/1.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["job_id"] = "other-job"
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    attempt = document["gap_leg"]["attempts"][0]
    attempt["campaign_attempt_root_receipt"]["sha256"] = driver.sha256_file(
        seal_path
    )
    campaign_path = raw / "campaign-root-receipt.json"
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    campaign["attempts"] = [seal]
    campaign_path.write_text(json.dumps(campaign), encoding="utf-8")
    driver.write_raw_manifest(raw)
    document["raw_bundle"]["paths"] = driver.validate_raw_manifest(raw)
    failures = driver.validate_raw_bundle(document, raw)
    assert [item.reason_code for item in failures] == ["raw_bundle"]


def _pbs_directives(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line.startswith("#PBS "):
            option, value = line[5:].split(maxsplit=1)
            result[option] = value
        elif line and not line.startswith("#"):
            break
    return result


def test_owned_pbs_assets_syntax_directives_policy_and_receipt_contract():
    policy = json.loads((TOOLS / "policy.json").read_text(encoding="utf-8"))
    rung = policy["silo_ladder_rung1"]
    job = TOOLS / "silo_ladder_rung1.sh"
    submit = TOOLS / "submit_silo_ladder_rung1.sh"
    for path in (job, submit):
        checked = subprocess.run(
            ["bash", "-n", str(path)], capture_output=True, text=True,
        )
        assert checked.returncode == 0, checked.stderr
    directives = _pbs_directives(job)
    assert directives == {
        "-A": rung["project"],
        "-q": rung["queue"],
        "-l": "elapstim_req=" + rung["walltime"],
        "-b": str(rung["nodes"]),
    }
    job_source = job.read_text(encoding="utf-8")
    submit_source = submit.read_text(encoding="utf-8")
    assert 'export TMPDIR="/scr/${PBS_JOBID//:/_}"' in job_source
    assert "sys.version_info[:2] >= (3, 10)" in job_source
    assert "qstat-after-qsub.stdout" in submit_source
    assert "--prepare-third-party-only" in submit_source
    assert "third-party sources prepared:" in submit_source
    assert "whole_tree_clean" in submit_source
    assert "attempt 2 is allowed only after attempt 1 infra failure" in submit_source
    assert rung["max_attempts"] == 2
    assert set(rung["infra_retry_reasons"]) == driver.INFRA_REASON_CODES
    assert "configure-build-replay(3 total)<=2700" in rung["walltime_formula"]
    assert "run-group(28)<=900" in rung["walltime_formula"]
    assert "collection<=300" in rung["walltime_formula"]
    assert rung["solo_load1_threshold"] == 48.0
    assert 'cd "$REPO_ROOT"' in submit_source
    assert "campaign-root/v1" in submit_source
    assert "publish_create_only_json" in submit_source
    assert "DEPENDENCY_DEADLINE=$((SECONDS + 180))" in job_source
    assert "qstat-driver.stdout" in job_source
    assert "--scheduler-deadline-epoch" in job_source
    assert 'timeout "$finalizer_timeout"' in job_source
    assert "FINALIZE_DEADLINE_EPOCH" in job_source
    assert "DRIVER_QSTAT_BASE_EPOCH=$(date +%s)" in job_source
    assert (
        job_source.index("DRIVER_QSTAT_BASE_EPOCH=$(date +%s)")
        < job_source.index('qstat -f "$QSTAT_JOBID" >"$JOB_STAGING/qstat-driver.stdout"')
    )
    assert (
        "DRIVER_QSTAT_BASE_EPOCH + DRIVER_REMAINING_S"
        in job_source
    )
    assert 'write_failure "$rc" "$CURRENT_STAGE"' in job_source
    assert "classify_wrapper_failure(stage,int(rc))" in job_source
    assert "CURRENT_STAGE=post_driver_finalize" in job_source
    assert "attempt-root-receipt.json" in job_source
    assert "validate_attempt_subtree(raw, 1)" in submit_source
    assert "runtime_modules_sha256" in submit_source
    assert "silo_ladder_rung1-success-sentinel/v1" in job_source
    assert job_source.index("silo_ladder_rung1-success-sentinel/v1") > (
        job_source.index('uptime >"$JOB_STAGING/load-after.txt"')
    )


def test_silo_build_dependencies_reach_scratch_before_dependency_stage():
    submit = (TOOLS / "submit_silo_ladder_rung1.sh").read_text()
    job = (TOOLS / "silo_ladder_rung1.sh").read_text()
    loop = 'for row in "${third_party_rows[@]}" "${build_dependency_rows[@]}"; do'
    for source, interpreter in ((submit, "python3"), (job, '"$PY"')):
        start = (
            f'readarray -t build_dependency_rows < <({interpreter} -I -B - "$POLICY"'
            " <<'PY_BUILD_DEPS'\n"
        )
        assert source.count(start) == 1
        body = source.split(start, 1)[1].split("\nPY_BUILD_DEPS", 1)[0]
        assert "orchestrator" not in body
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-", str(TOOLS / "policy.json")],
            input=body, text=True, capture_output=True, check=True,
        )
        policy = json.loads((TOOLS / "policy.json").read_text())
        expected = []
        for name in ("gflags", "glog"):
            fields = [name, name]
            if source == submit:
                fields.append(policy[f"{name}_source_url"])
            fields.append(policy[f"{name}_expected_head"])
            expected.append("\t".join(fields))
        assert result.stdout.splitlines() == expected
        assert '[[ ${#third_party_rows[@]} -eq 3 ]]' in source
        assert '[[ ${#build_dependency_rows[@]} -eq 2 ]]' in source
        assert source.count(loop) == 1
        assert source.index(start) < source.index(loop)
    submit_loop = submit.split(loop, 1)[1].split("\ndone", 1)[0]
    for required in (
        'destination="$THIRD_PARTY_ROOT/$third_source_name"',
        'git clone --no-checkout -- "$third_url" "$stage/repo"',
        'git -C "$stage/repo" checkout --detach "$third_pin"',
        'verify_third_party_pinned_clean',
        '"$destination" "$third_pin" "$third_name" || exit 2',
    ):
        assert required in submit_loop
    job_loop = job.split(loop, 1)[1].split("\ndone", 1)[0]
    ordered = (
        'persistent="$THIRD_PARTY_PERSISTENT/$third_source_name"',
        'scratch="$THIRD_PARTY_SCRATCH/$third_source_name"',
        'verify_third_party_pinned_clean',
        '"$persistent" "$third_pin" "$third_name"',
        'cp -a -- "$persistent" "$scratch"',
        'verify_third_party_pinned_clean "$scratch" "$third_pin" "$third_name"',
    )
    positions = [job_loop.index(fragment) for fragment in ordered]
    assert positions == sorted(positions)
    assert job_loop.count("verify_third_party_pinned_clean") == 2
    assert (job.index(loop)
            < job.index('export IZANAGI_THIRDPARTY_SOURCE_ROOT="$THIRD_PARTY_SCRATCH"')
            < job.index('GFLAGS_SOURCE="$THIRDPARTY_SOURCE_ROOT/gflags"')
            < job.index('git -C "$dep_source" rev-parse'))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
