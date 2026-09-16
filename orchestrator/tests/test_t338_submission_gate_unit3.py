"""T-338 unit 3: raw-evidence semantic validation and reject-only checks.

Every negative fixture documents the single semantic condition it breaks.  The
shape gate is exercised separately where a small mapping is enough; the full
receipt control is built once with the same ``tmp_path``/Git fixture pattern as
unit 1, so a semantic failure is not accidentally a schema failure.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

from orchestrator.preregistration.blobref import BlobRef
from orchestrator.submission_gate import _binding, _git, _manifest
from orchestrator.submission_gate import _semantic_validator as semantic
from orchestrator.submission_gate._receipt_io import ReceiptDocument, ReceiptParseError
from orchestrator.submission_gate._receipt_schema import ReceiptSchema, validate_receipt_shape
from orchestrator.submission_gate._safe_io import SafeIOError


_GIT = "/usr/bin/git"
_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "output"
    / "insights"
    / "2026-08-11_t139-manifest-land1"
    / "receipt-schema-v1.json"
)


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "T-338 unit3",
            "GIT_AUTHOR_EMAIL": "t338-unit3@example.invalid",
            "GIT_COMMITTER_NAME": "T-338 unit3",
            "GIT_COMMITTER_EMAIL": "t338-unit3@example.invalid",
        }
    )
    return env


def _run(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        [_GIT, *arguments],
        cwd=root,
        env=_git_env(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _commit(root: Path, message: str, *paths: str) -> str:
    _run(root, "add", *paths)
    _run(root, "commit", "-m", message)
    return _run(root, "rev-parse", "HEAD")


def _file_record(root: Path, relative_path: str, data: bytes) -> dict[str, object]:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        "path": relative_path,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _blob_ref(path: str, commit: str, data: bytes) -> BlobRef:
    return BlobRef(path, commit, hashlib.sha256(data).hexdigest())


def _forge_legacy_d282_authority_for_consumer_compatibility(
    record: _manifest.PreregistrationRecord,
) -> _manifest.ApprovedManifest:
    """Forge only the pre-D574 semantic-consumer fixture; writer rejects it."""

    approved = object.__new__(_manifest.ApprovedManifest)
    errata = {item.erratum_id: BlobRef(item.path, item.commit, item.sha256) for item in record.errata}
    values = {
        "approval_ref": record.approval_manifest,
        "target_core": record.core,
        "approved_blobs": {
            "addendum_a": record.addendum_a,
            "derivation_map": record.addendum_a,
            "erratum_t139_core_s15_exactkey_v1": errata["t139-core-s15-exactkey-v1"],
            "erratum_t139_core_s7_stresscheck_v1": errata["t139-core-s7-stresscheck-v1"],
            "record_items": record.addendum_a,
            "receipt_schema": record.receipt_schema,
        },
        "erratum_application_order": tuple(item.erratum_id for item in record.errata),
        "composed_sha256": record.composed_core_sha256,
        "prereg_commit": record.prereg_commit,
        "_seal": _manifest._MANIFEST_CAPABILITY_TOKEN,
    }
    for name, value in values.items():
        object.__setattr__(approved, name, value)
    return approved


def _preregistration_value(record: _manifest.PreregistrationRecord) -> dict[str, object]:
    def blob(ref: BlobRef) -> dict[str, str]:
        return {"path": ref.path, "commit": ref.commit, "sha256": ref.sha256}

    return {
        "core": blob(record.core),
        "addendum_a": blob(record.addendum_a),
        "addendum_b": None if record.addendum_b is None else blob(record.addendum_b),
        "fold_commit": record.fold_commit,
        "errata": [
            {
                "erratum_id": item.erratum_id,
                "path": item.path,
                "commit": item.commit,
                "sha256": item.sha256,
                "approval_fold_commit": item.approval_fold_commit,
            }
            for item in record.errata
        ],
        "approval_manifest": blob(record.approval_manifest),
        "receipt_schema": blob(record.receipt_schema),
        "composed_core_sha256": record.composed_core_sha256,
    }


def _phase_data(role: str, offset: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    caps = (
        semantic._PERFORMANCE_PHASE_CAPS
        if role == "performance_cluster"
        else semantic._VERIFICATION_PHASE_CAPS
    )
    phase_caps = [
        {"phase": phase, "cap_s": cap, "sub_cap_s_or_null": sub}
        for phase, (cap, sub) in caps.items()
    ]
    phase_events: list[dict[str, object]] = []
    timestamp = offset
    for phase in caps:
        phase_events.append({"phase": phase, "event": "enter", "monotonic_ns": timestamp})
        timestamp += 1
        phase_events.append({"phase": phase, "event": "leave", "monotonic_ns": timestamp})
        timestamp += 1
    return phase_caps, phase_events


def _ccbench_log(workload: str) -> bytes:
    flags = semantic._EXPECTED_FLAGS[workload]
    lines = [
        f"#FLAGS_clocks_per_us:\t{flags['clocks_per_us']}",
        f"#FLAGS_epoch_time:\t{flags['epoch_time']}",
        f"#FLAGS_extime:\t{flags['extime']}",
        f"#FLAGS_thread_num:\t{flags['thread_num']}",
        f"#FLAGS_ycsb_max_ope:\t{flags['ycsb_max_ope']}",
        f"#FLAGS_ycsb_rmw:\t{flags['ycsb_rmw']}",
        f"#FLAGS_ycsb_rratio:\t{flags['ycsb_rratio']}",
        f"#FLAGS_ycsb_tuple_num:\t{flags['ycsb_tuple_num']}",
        f"#FLAGS_ycsb_zipf_skew:\t{flags['ycsb_zipf_skew']}",
        "#ShowOptParameters(): ADD_ANALYSIS 0 : BACK_OFF 0 : KEY_SIZE 8 : "
        "MASSTREE_USE 1 : NO_WAIT_LOCKING_IN_VALIDATION 1 : PARTITION_TABLE 0 : "
        "PROCEDURE_SORT 0 : SLEEP_READ_PHASE 0 : VAL_SIZE 4 : WAL 0",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _make_git_fixture(tmp_path: Path) -> SimpleNamespace:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run([_GIT, "init", "-q"], cwd=root, env=_git_env(), check=True)
    (root / "root.txt").write_bytes(b"root\n")
    (root / "prereg").mkdir()
    (root / "prereg/approval.json").write_bytes(b"approval\n")
    root_commit = _commit(root, "root", "root.txt", "prereg/approval.json")

    content_files = {
        "prereg/core.md": b"core\n",
        "prereg/addendum-a.md": b"addendum-a\n",
        "prereg/erratum-one.md": b"erratum-one\n",
        "prereg/erratum-two.md": b"erratum-two\n",
        "prereg/receipt-schema.json": _SCHEMA_PATH.read_bytes(),
    }
    for path, data in content_files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(data)
    content_commit = _commit(root, "content", *content_files)
    (root / "effective.txt").write_bytes(b"effective\n")
    effective_commit = _commit(root, "effective", "effective.txt")

    # All raw artifacts are in the measurement commit so source/tree identity
    # and every pointer have one stable checkout anchor.
    tree_files: dict[str, bytes] = {
        "transaction.cc": b"int transaction_fixture() { return 0; }\n",
        "build/compile_commands.json": json.dumps(
            [
                {
                    "directory": ".",
                    "file": "transaction.cc",
                    "arguments": [
                        "g++",
                        "-DTRACE=0",
                        "-DADD_ANALYSIS=0",
                        "-c",
                        "transaction.cc",
                    ],
                }
            ],
            separators=(",", ":"),
        ).encode(),
        "build/CMakeCache.txt": b"CCBENCH_TRACE:STRING=0\nCCBENCH_ADD_ANALYSIS:STRING=0\n",
        "correctness/compile_commands.json": json.dumps(
            [
                {
                    "directory": ".",
                    "file": "transaction.cc",
                    "arguments": [
                        "g++",
                        "-DTRACE=1",
                        "-DADD_ANALYSIS=1",
                        "-c",
                        "transaction.cc",
                    ],
                }
            ],
            separators=(",", ":"),
        ).encode(),
        "correctness/CMakeCache.txt": b"CCBENCH_TRACE:STRING=1\nCCBENCH_ADD_ANALYSIS:STRING=1\n",
        "build/argv-w1.json": json.dumps(list(semantic._EXPECTED_DRIVER_ARGV["W1"]), separators=(",", ":")).encode(),
        "build/argv-w2.json": json.dumps(list(semantic._EXPECTED_DRIVER_ARGV["W2"]), separators=(",", ":")).encode(),
        "build/run-w1.log": _ccbench_log("W1"),
        "build/run-w2.log": _ccbench_log("W2"),
        "build/marker": b"started\n",
        "build/intent-performance": b"intent-performance\n",
        "build/intent-verification": b"intent-verification\n",
        "build/qsub-performance": b"qsub-performance\n",
        "build/qsub-verification": b"qsub-verification\n",
        "build/failure-verification": b"failure-verification\n",
        "build/attestation-expected": b"expected profile\n",
        "build/attestation-observed": b"observed profile\n",
        "build/accounting-performance": b"accounting-performance\n",
        "build/accounting-verification": b"accounting-verification\n",
        "build/exclusivity-performance": b"exclusivity-performance\n",
        "build/exclusivity-verification": b"exclusivity-verification\n",
        "build/path-choice-performance": b"path-choice-performance\n",
        "build/path-choice-verification": b"path-choice-verification\n",
        "build/telemetry-alpha": b"alpha\n",
        "build/telemetry-stress": b"stress\n",
        "build/stat-before": b"cpu 0 0 0 0 0 0 0 0\n",
        "build/stat-after": b"cpu 1 0 0 99 0 0 0 0\n",
        "correctness/stock.bin": b"correctness-stock\n",
        "correctness/mode1.bin": b"correctness-mode1\n",
        "correctness/modeX.bin": b"correctness-modeX\n",
        "correctness/stock-w1.json": b'{"expected":{"value":1},"actual":{"value":1}}\n',
        "correctness/stock-w2.json": b'{"expected":{"value":1},"actual":{"value":1}}\n',
        "correctness/mode1-w1.json": b'{"expected":{"value":1},"actual":{"value":1}}\n',
        "correctness/mode1-w2.json": b'{"expected":{"value":1},"actual":{"value":1}}\n',
        "correctness/modeX-w1.json": b'{"expected":{"value":1},"actual":{"value":1}}\n',
        "correctness/modeX-w2.json": b'{"expected":{"value":1},"actual":{"value":1}}\n',
        "liveness/stock-w1.log": b"liveness stock W1 ok\n",
        "liveness/stock-w2.log": b"liveness stock W2 ok\n",
        "liveness/mode1-w1.log": b"liveness mode1 W1 ok\n",
        "liveness/mode1-w2.log": b"liveness mode1 W2 ok\n",
        "liveness/modeX-w1.log": b"liveness modeX W1 ok\n",
        "liveness/modeX-w2.log": b"liveness modeX W2 ok\n",
    }
    for index, arm in enumerate(semantic._ARMS):
        tree_files[f"build/{arm}.bin"] = f"performance-{arm}\n".encode()
        tree_files[f"build/{arm}.artifact"] = f"artifact-{arm}\n".encode()
    for path, data in tree_files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(data)
    head_commit = _commit(root, "measurement artifacts", *tree_files)
    tree_sha = _run(root, "rev-parse", f"{head_commit}^{{tree}}")

    refs = {
        path: _blob_ref(path, content_commit, data)
        for path, data in content_files.items()
    }
    record = _manifest.PreregistrationRecord(
        core=refs["prereg/core.md"],
        addendum_a=refs["prereg/addendum-a.md"],
        addendum_b=None,
        fold_commit=root_commit,
        errata=(
            _manifest.ErratumRef(
                erratum_id="t139-core-s15-exactkey-v1",
                path=refs["prereg/erratum-one.md"].path,
                commit=content_commit,
                sha256=refs["prereg/erratum-one.md"].sha256,
                approval_fold_commit=root_commit,
            ),
            _manifest.ErratumRef(
                erratum_id="t139-core-s7-stresscheck-v1",
                path=refs["prereg/erratum-two.md"].path,
                commit=content_commit,
                sha256=refs["prereg/erratum-two.md"].sha256,
                approval_fold_commit=root_commit,
            ),
        ),
        approval_manifest=_blob_ref("prereg/approval.json", root_commit, b"approval\n"),
        receipt_schema=refs["prereg/receipt-schema.json"],
        composed_core_sha256=hashlib.sha256(b"composed core\n").hexdigest(),
        prereg_commit=root_commit,
    )
    binding = _binding._PreregBinding._issue(
        record=record,
        approved_manifest=_forge_legacy_d282_authority_for_consumer_compatibility(record),
        repository_root=root,
        measurement_head=head_commit,
        prereg_commit=root_commit,
        prereg_content_commit=content_commit,
        prereg_effective_commit=effective_commit,
        root_identity=(root.stat().st_dev, root.stat().st_ino),
        token=_binding._CAPABILITY_TOKEN,
    )
    return SimpleNamespace(
        root=root,
        root_commit=root_commit,
        content_commit=content_commit,
        effective_commit=effective_commit,
        head_commit=head_commit,
        tree_sha=tree_sha,
        record=record,
        binding=binding,
        tree_files=tree_files,
    )


def _full_receipt(fixture: SimpleNamespace) -> tuple[dict[str, Any], ReceiptSchema]:
    root = fixture.root
    record = fixture.record
    def pointer(path: str) -> dict[str, object]:
        data = fixture.tree_files.get(path, (root / path).read_bytes())
        return _file_record(root, path, data)

    schedule = semantic._canonical_schedule_bytes(semantic._A09_SEED)
    (root / "build/schedule.tsv").write_bytes(schedule)
    schedule_record = pointer("build/schedule.tsv")
    run_rows: list[dict[str, object]] = []
    schedule_rows = semantic._derive_schedule_rows(semantic._A09_SEED)
    ordinal = 1
    for slot in range(1, 9):
        for row in semantic._expected_planned_runs_for_slot(schedule_rows, slot):
            run_rows.append({"run_id": f"run-{ordinal}", **row})
            ordinal += 1
    allocations: list[dict[str, object]] = []
    perf_caps, perf_events = _phase_data("performance_cluster", 0)
    ver_caps, ver_events = _phase_data("verification", 100)
    allocations.append(
        {
            "allocation_id": "alloc-perf-1",
            "allocation_role": "performance_cluster",
            "cluster_slot_or_null": 1,
            "scheduler_request_id": "req-perf-1",
            "path_choice": "primary_build_outside",
            "path_choice_intent": pointer("build/path-choice-performance"),
            "node": "node-1",
            "requested_walltime_s": 3600,
            "internal_deadline_s": 3300,
            "started_at_monotonic_ns": 0,
            "ended_at_monotonic_ns": 2_000_000_000_000,
            "accounting_trace": pointer("build/accounting-performance"),
            "exclusivity": {"method": "scheduler_accounting", "raw": pointer("build/exclusivity-performance")},
            "phase_caps": perf_caps,
            "phase_events": perf_events,
            "binary_rehash": [],
        }
    )
    allocations.append(
        {
            "allocation_id": "alloc-verification",
            "allocation_role": "verification",
            "cluster_slot_or_null": None,
            "scheduler_request_id": "req-verification",
            "path_choice": "primary_build_outside",
            "path_choice_intent": pointer("build/path-choice-verification"),
            "node": "node-2",
            "requested_walltime_s": 3600,
            "internal_deadline_s": 3300,
            "started_at_monotonic_ns": 100,
            "ended_at_monotonic_ns": 120,
            "accounting_trace": pointer("build/accounting-verification"),
            "exclusivity": {"method": "scheduler_accounting", "raw": pointer("build/exclusivity-verification")},
            "phase_caps": ver_caps,
            "phase_events": ver_events,
            "binary_rehash": [],
        }
    )
    arms: dict[str, object] = {}
    for arm_index, arm in enumerate(semantic._ARMS):
        binary = pointer(f"build/{arm}.bin")
        artifact = pointer(f"build/{arm}.artifact")
        if arm == "stock":
            mode_macro = None
            patch_path = None
            patch_sha256 = None
        elif arm == "mode1":
            mode_macro = semantic._EXPECTED_MODE_MACROS[arm]
            patch_path = semantic._EXPECTED_PATCH_PATH
            patch_sha256 = semantic._EXPECTED_PATCH_SHA256
        else:
            mode_macro = semantic._EXPECTED_MODE_MACROS[arm]
            patch_path = semantic._EXPECTED_PATCH_PATH
            patch_sha256 = semantic._EXPECTED_PATCH_SHA256
        compile_record = {
            "source": {
                "repo_commit": fixture.head_commit,
                "ccbench_pin": semantic._CCBENCH_PIN,
                "base_tree_sha": fixture.tree_sha,
                "patch_path": patch_path,
                "patch_sha256": patch_sha256,
            },
            "mode_macro": mode_macro,
            "configure_argv": ["-DCCBENCH_TRACE=0", "-DCCBENCH_ADD_ANALYSIS=0"],
            "translation_units": {
                "transaction.cc": {
                    "normalized_argv": [
                        "g++",
                        "-DTRACE=0",
                        "-DADD_ANALYSIS=0",
                        "-c",
                        "transaction.cc",
                    ],
                    "sha256": hashlib.sha256(fixture.tree_files["transaction.cc"]).hexdigest(),
                }
            },
            "identity_sha256": "a" * 64,
            "trace_enabled": False,
            "analysis_enabled": False,
            "cmake_cache": {"trace": 0, "add_analysis": 0},
            "compile_commands": pointer("build/compile_commands.json"),
        }
        arms[arm] = {
            "compile": compile_record,
            "binary": binary,
            "built_outside_allocation": {
                "artifact_path": artifact["path"],
                "size": artifact["size"],
                "sha256": artifact["sha256"],
            },
            "toolchain": {
                "compiler_path": "/bin/g++",
                "compiler_version": "GNU 11.4.0",
                "compiler_sha256": "b" * 64,
                "link_argv": [],
                "dynamic_deps": [],
                "elf_interpreter": "/lib64/ld-linux-x86-64.so.2",
            },
        }
    actual_runs: list[dict[str, object]] = []
    timeline_ns = 0
    for index, run in enumerate(run_rows[:36]):
        workload = run["workload"]
        argv_path = "build/argv-w1.json" if workload == "W1" else "build/argv-w2.json"
        log_path = "build/run-w1.log" if workload == "W1" else "build/run-w2.log"
        wait = dict(run["preceding_wait"])
        wait_seconds = int(wait["required_s"])
        wait["monotonic_start_ns"] = timeline_ns
        wait["monotonic_end_ns"] = wait["monotonic_start_ns"] + wait_seconds * 1_000_000_000
        argv_pointer = pointer(argv_path)
        run_start = wait["monotonic_end_ns"] + 10_000_000_000
        run_end = run_start + 1
        actual_runs.append(
            {
                **{
                    field: run[field]
                    for field in (
                        "run_id",
                        "cluster_slot",
                        "workload",
                        "block_index",
                        "permutation",
                        "position",
                        "predecessor_arm",
                        "arm",
                    )
                },
                "attempt_id": "attempt-performance",
                "allocation_id": "alloc-perf-1",
                "actual_ordinal": index + 1,
                "preceding_wait": wait,
                "started_at_monotonic_ns": run_start,
                "ended_at_monotonic_ns": run_end,
                "binary_sha256": arms[run["arm"]]["binary"]["sha256"],  # type: ignore[index]
                "exec_witness": {"path": arms[run["arm"]]["binary"]["path"], "inode": 1, "size": arms[run["arm"]]["binary"]["size"], "sha256": arms[run["arm"]]["binary"]["sha256"], "monotonic_ns": run_start},  # type: ignore[index]
                "argv_sha256": argv_pointer["sha256"],
                "argv_raw": argv_pointer,
                "run_log": pointer(log_path),
            }
        )
        timeline_ns = run_end
    allocations[0]["binary_rehash"] = [
        {
            "point": point,
            "arm": arm,
            "sha256": arms[arm]["binary"]["sha256"],  # type: ignore[index]
            "monotonic_ns": timestamp,
        }
        for point, timestamp in (
            ("after_staging", 0),
            ("before_first_run", 10),
            ("after_last_run", 20),
        )
        for arm in semantic._ARMS
    ]
    marker = pointer("build/marker")
    observation_common = {
        "stat_before_raw": pointer("build/stat-before"),
        "stat_after_raw": pointer("build/stat-after"),
        "stat_before": [0] * 8,
        "stat_after": [1, 0, 0, 99, 0, 0, 0, 0],
        "load1_diagnostic": 0.0,
        "malformed_reason": None,
    }
    first_run_start = actual_runs[0]["started_at_monotonic_ns"]
    observations = [
        {
            "ordinal": 1,
            "scope": "preflight",
            "run_id_or_null": None,
            "monotonic_start_ns": first_run_start - 10_000_000_000,
            "monotonic_end_ns": first_run_start,
            **observation_common,
        }
    ]
    for observation_index, run in enumerate(actual_runs[1:], 2):
        run_start = run["started_at_monotonic_ns"]
        observations.append(
            {
                "ordinal": observation_index,
                "scope": "pre_run",
                "run_id_or_null": run["run_id"],
                "monotonic_start_ns": run_start - 10_000_000_000,
                "monotonic_end_ns": run_start,
                **observation_common,
            }
        )
    attempts = [
        {
            "attempt_id": "attempt-performance",
            "cluster_slot_or_null": 1,
            "reason_code": "completed",
            "replaces_attempt_id": None,
            "parent_attempt_id": None,
            "allocation_id": "alloc-perf-1",
            "submitted_at_monotonic_ns": 0,
            "intent_ref": pointer("build/intent-performance"),
            "qsub_result": {"returncode": 0, "raw": pointer("build/qsub-performance")},
            "performance_started_marker": {
                "path": marker["path"],
                "size": marker["size"],
                "sha256": marker["sha256"],
                "created_at_monotonic_ns": 1,
            },
            "environment_observations": observations,
            "failure_evidence": None,
        },
        {
            "attempt_id": "attempt-verification",
            "cluster_slot_or_null": None,
            "reason_code": "pre_performance_infra_failure",
            "replaces_attempt_id": None,
            "parent_attempt_id": None,
            "allocation_id": "alloc-verification",
            "submitted_at_monotonic_ns": 100,
            "intent_ref": pointer("build/intent-verification"),
            "qsub_result": {"returncode": 1, "raw": pointer("build/qsub-verification")},
            "performance_started_marker": None,
            "environment_observations": [],
            "failure_evidence": {"kind": "scheduler", "pointer": pointer("build/failure-verification")},
        },
    ]
    telemetry = [
        {"ordinal": 1, "kind": "alpha_reservation", "receipt": pointer("build/telemetry-alpha"), "fixed_inputs": {"input_sha256": "c" * 64, "B_or_null": None, "seed_or_null": None}, "ledger_evidence": {"ledger_path": "output/registry/t139-alpha-reservations.jsonl", "family_root": "a" * 40, "ordinal": 1, "reservation_entry_sha256": "b" * 64, "reservation_commit": "c" * 40}},
        {"ordinal": 2, "kind": "stress_check_simulation", "receipt": pointer("build/telemetry-stress"), "fixed_inputs": {"input_sha256": "d" * 64, "B_or_null": 1, "seed_or_null": "e" * 64}, "ledger_evidence": None},
    ]
    correctness_source = dict(arms["stock"]["compile"]["source"])  # type: ignore[index]
    correctness_evidence = [
        {
            "ordinal": 1,
            "arm": "stock",
            "workload": "W1",
            "build": {
                "source": correctness_source,
                "compile": {
                    "identity_sha256": "d" * 64,
                    "argv": ["-DCCBENCH_TRACE=1", "-DCCBENCH_ADD_ANALYSIS=1"],
                    "trace_enabled": True,
                    "analysis_enabled": True,
                    "cmake_cache": {"trace": 1, "add_analysis": 1},
                    "compile_commands": pointer("correctness/compile_commands.json"),
                },
                "binary": pointer("correctness/stock.bin"),
            },
            "run_scope": {"allocation_id": "alloc-verification", "run_ordinal": 1},
            "outputs": [pointer("correctness/stock-w1.json")],
        }
    ]
    value: dict[str, Any] = {
        "schema_version": "t139-receipt/v1",
        "study_id": "unit3-study",
        "declared_use_class": "official",
        "study_stage": "pilot",
        "series_id": "f" * 64,
        "parent_series_id": None,
        "preregistration": _preregistration_value(record),
        "environment": {"env_tag": "unit3", "attestation_mode": "required", "attestations": [
            {"ordinal": 1, "profile_kind": "expected", "schema_version": "env/v1", "raw": pointer("build/attestation-expected")},
            {"ordinal": 2, "profile_kind": "observed", "schema_version": "env/v1", "raw": pointer("build/attestation-observed")},
        ]},
        "measurement_checkout": {"repository_head": fixture.head_commit, "ccbench_head": semantic._CCBENCH_PIN},
        "dependency_pins": [{"name": name, "commit": semantic._EXPECTED_DEPENDENCY_PINS[name]} for name in sorted(semantic._DEPENDENCIES)],
        "arms": arms,
        "allocations": allocations,
        "planned_execution": {
            "workloads": {
                workload: {
                    "driver_argv": list(semantic._EXPECTED_DRIVER_ARGV[workload]),
                    "effective_flags": dict(semantic._EXPECTED_FLAGS[workload]),
                    "opt_parameters": dict(semantic._EXPECTED_OPT_PARAMETERS),
                }
                for workload in semantic._WORKLOADS
            },
            "schedule_seed": semantic._A09_SEED,
            "schedule_algorithm": semantic._A09_ALGORITHM,
            "schedule_table": schedule_record,
            "schedule_sha256": hashlib.sha256(schedule).hexdigest(),
            "consumed_cluster_slots": list(range(1, 9)),
            "cluster_slots": [dict(row) for row in schedule_rows],
            "runs": run_rows,
        },
        "actual_runs": actual_runs,
        "correctness_evidence": correctness_evidence,
        "liveness": [],
        "admission_telemetry": telemetry,
        "attempts": attempts,
    }
    schema_ref = record.receipt_schema
    schema_document = json.loads((root / "prereg/receipt-schema.json").read_bytes())
    schema = ReceiptSchema(ref=schema_ref, sha256=schema_ref.sha256, document=schema_document)
    return value, schema


def _certified_receipt(fixture: SimpleNamespace) -> tuple[dict[str, Any], ReceiptSchema]:
    original, schema = _full_receipt(fixture)
    value = copy.deepcopy(original)
    root = fixture.root

    def pointer(path: str) -> dict[str, object]:
        data = fixture.tree_files.get(path, (root / path).read_bytes())
        return _file_record(root, path, data)

    for attempt in value["attempts"]:
        if attempt["attempt_id"] == "attempt-verification":
            attempt.update(
                reason_code="completed",
                qsub_result={"returncode": 0, "raw": pointer("build/qsub-verification")},
                failure_evidence=None,
                performance_started_marker=None,
            )
    template = value["correctness_evidence"][0]
    value["correctness_evidence"] = []
    value["liveness"] = []
    pairs = [(arm, workload) for arm in ("stock", "mode1", "modeX") for workload in ("W1", "W2")]
    for ordinal, (arm, workload) in enumerate(pairs, 1):
        entry = copy.deepcopy(template)
        entry.update(ordinal=ordinal, arm=arm, workload=workload)
        entry["build"]["source"] = copy.deepcopy(value["arms"][arm]["compile"]["source"])
        entry["build"]["binary"] = pointer(f"correctness/{arm}.bin")
        entry["outputs"] = [pointer(f"correctness/{arm}-{workload.lower()}.json")]
        entry["run_scope"] = {"allocation_id": "alloc-verification", "run_ordinal": ordinal}
        value["correctness_evidence"].append(entry)
        value["liveness"].append({
            "ordinal": ordinal,
            "allocation_id": "alloc-verification",
            "probe": "liveness_run",
            "arm_or_null": arm,
            "workload_or_null": workload,
            "monotonic_ns": 105 + ordinal,
            "raw": pointer(f"liveness/{arm}-{workload.lower()}.log"),
        })
    return value, schema


def _without_verification_attempt(value: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(value)
    value["attempts"] = [
        attempt for attempt in value["attempts"]
        if attempt["cluster_slot_or_null"] is not None
    ]
    return value


def _completed_performance_reason_payload() -> dict[str, Any]:
    return {
        "planned_execution": {
            "consumed_cluster_slots": [1],
            "runs": [{"run_id": f"run-{i}", "cluster_slot": 1} for i in range(36)],
        },
        "attempts": [{
            "attempt_id": "p",
            "cluster_slot_or_null": 1,
            "reason_code": "completed",
            "allocation_id": "alloc-performance",
            "performance_started_marker": {"path": "marker"},
            "failure_evidence": None,
            "replaces_attempt_id": None,
        }],
        "actual_runs": [{"run_id": f"run-{i}", "attempt_id": "p"} for i in range(36)],
        "correctness_evidence": [
            {"arm": arm, "workload": workload, "run_scope": {"allocation_id": "alloc-verification"}}
            for arm in ("stock", "mode1", "modeX") for workload in ("W1", "W2")
        ],
    }


def _assert_semantic(code: str, callable_object, *args, **kwargs) -> None:
    with pytest.raises(semantic.SemanticValidationError) as info:
        callable_object(*args, **kwargs)
    assert info.value.reason_code == code


def _receipt_document(value: dict[str, Any]) -> ReceiptDocument:
    raw_bytes = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    return ReceiptDocument(
        raw_bytes=raw_bytes,
        value=value,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
    )


def test_semantic_validator_accepts_complete_performance_receipt(tmp_path: Path) -> None:
    """この入力は shape を通過し、全 raw pointer と slot1 の36-run facts が整合する。"""
    fixture = _make_git_fixture(tmp_path)
    value, schema = _full_receipt(fixture)
    document = _receipt_document(value)
    semantic._validate_receipt_semantics(
        fixture.root, document, schema=schema, binding=fixture.binding
    )


def test_certified_receipt_accepts_six_pairs(tmp_path: Path) -> None:
    fixture = _make_git_fixture(tmp_path)
    value, schema = _certified_receipt(fixture)
    semantic._validate_receipt_semantics(
        fixture.root, _receipt_document(value), schema=schema, binding=fixture.binding
    )


@pytest.mark.parametrize("count", [0, 1], ids=["0", "1"])
def test_completed_performance_requires_correctness_top_level(tmp_path: Path, count: int) -> None:
    fixture = _make_git_fixture(tmp_path)
    value, schema = _full_receipt(fixture)
    value = _without_verification_attempt(value)
    value["correctness_evidence"] = value["correctness_evidence"][:count]
    _assert_semantic(
        "correctness", semantic._validate_receipt_semantics,
        fixture.root, _receipt_document(value), schema=schema, binding=fixture.binding,
    )


@pytest.mark.parametrize("count", [0, 1, 5], ids=["0", "1", "5"])
def test_completed_performance_requires_correctness_reason_branches(count: int) -> None:
    value = _completed_performance_reason_payload()
    value["correctness_evidence"] = value["correctness_evidence"][:count]
    _assert_semantic("correctness", semantic._validate_reason_branches, value, {}, anomaly=False)


def test_completed_performance_rejects_duplicate_correctness_pair(tmp_path: Path) -> None:
    fixture = _make_git_fixture(tmp_path)
    value, schema = _certified_receipt(fixture)
    value = _without_verification_attempt(value)
    value["correctness_evidence"][5] = copy.deepcopy(value["correctness_evidence"][0])
    value["correctness_evidence"][5]["ordinal"] = 6
    value["correctness_evidence"][5]["run_scope"]["run_ordinal"] = 6
    _assert_semantic(
        "correctness", semantic._validate_receipt_semantics,
        fixture.root, _receipt_document(value), schema=schema, binding=fixture.binding,
    )


def test_completed_performance_rejects_seven_correctness_entries() -> None:
    value = _completed_performance_reason_payload()
    value["correctness_evidence"].append(copy.deepcopy(value["correctness_evidence"][0]))
    _assert_semantic("correctness", semantic._validate_reason_branches, value, {}, anomaly=False)


@pytest.mark.parametrize("count", [0, 5], ids=["0", "5"])
def test_failed_performance_accepts_partial_correctness(count: int) -> None:
    value = _completed_performance_reason_payload()
    value["attempts"][0].update(
        reason_code="pre_performance_infra_failure",
        performance_started_marker=None,
        failure_evidence={"kind": "scheduler", "pointer": {"path": "failure"}},
    )
    value["actual_runs"] = []
    value["correctness_evidence"] = value["correctness_evidence"][:count]
    semantic._validate_reason_branches(value, {}, anomaly=False)


def test_recorded_verification_failure_accepts_empty_correctness() -> None:
    value = _completed_performance_reason_payload()
    value["attempts"].append({
        "attempt_id": "v",
        "cluster_slot_or_null": None,
        "reason_code": "pre_performance_infra_failure",
        "allocation_id": "alloc-verification",
        "performance_started_marker": None,
        "failure_evidence": {"kind": "scheduler", "pointer": {"path": "failure"}},
    })
    value["correctness_evidence"] = []
    semantic._validate_reason_branches(value, {}, anomaly=False)


def test_completed_performance_requires_full_bijection(tmp_path: Path) -> None:
    """shapeは通過するが、completed attemptのplanned↔actual 36件だけを壊す。"""
    fixture = _make_git_fixture(tmp_path)
    value, _ = _full_receipt(fixture)
    value["actual_runs"] = value["actual_runs"][:-1]
    _assert_semantic(
        "planned_actual",
        semantic._validate_planned_actual_relationship,
        value,
        {row["run_id"]: row for row in value["planned_execution"]["runs"]},
    )


def test_completed_verification_requires_six_pairs() -> None:
    """shape検査を通過し、verification completedのpair cardinalityだけで拒否する。"""
    value = {
        "planned_execution": {"consumed_cluster_slots": [1], "runs": []},
        "attempts": [{"attempt_id": "v", "cluster_slot_or_null": None, "reason_code": "completed", "allocation_id": "a", "performance_started_marker": None, "failure_evidence": None}],
        "actual_runs": [],
        "correctness_evidence": [],
        "liveness": [],
    }
    _assert_semantic("reason", semantic._validate_reason_branches, value, {}, anomaly=False)


def test_pre_performance_failure_rejects_marker_or_actual_run() -> None:
    """shape検査を通過し、開始前申告へmarkerを足すsemantic一点だけで拒否する。"""
    value = {
        "planned_execution": {"consumed_cluster_slots": [1]},
        "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "pre_performance_infra_failure", "performance_started_marker": {}, "failure_evidence": {"kind": "scheduler"}}],
        "actual_runs": [],
    }
    _assert_semantic("reason", semantic._validate_reason_branches, value, {}, anomaly=False)


def test_post_failure_accepts_marker_route() -> None:
    value = {"planned_execution": {"consumed_cluster_slots": [1]}, "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "post_performance_failure", "performance_started_marker": {}, "failure_evidence": {"kind": "driver"}}], "actual_runs": []}
    semantic._validate_reason_branches(value, {}, anomaly=False)


def test_post_failure_accepts_actual_run_route() -> None:
    value = {"planned_execution": {"consumed_cluster_slots": [1]}, "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "post_performance_failure", "performance_started_marker": None, "failure_evidence": {"kind": "collector"}}], "actual_runs": [{"attempt_id": "a", "run_id": "r"}]}
    semantic._validate_reason_branches(value, {}, anomaly=False)


def test_post_failure_recomputes_a03_route() -> None:
    value = {"planned_execution": {"consumed_cluster_slots": [1]}, "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "post_performance_failure", "performance_started_marker": None, "failure_evidence": {"kind": "a03_environment"}}], "actual_runs": []}
    results = {"attempt:a:0": semantic.A03Result("short_columns", None, True, (), ())}
    semantic._validate_reason_branches(value, results, anomaly=False)


def test_a03_malformed_reason_uses_first_failure(tmp_path: Path) -> None:
    """shape検査を通過し、malformed_reasonの評価順序の一点だけで拒否する。"""
    before = b"cpu 10 10 10\n"
    after = b"cpu 9 10 10\n"
    result = semantic._derive_a03_failure(before, after, monotonic_start_ns=0, monotonic_end_ns=1_000_000_000)
    assert result.malformed_reason == "short_columns"


def test_replacement_only_targets_infra_failure_and_reuses_slot() -> None:
    """対象外条件を正例に保ち、post-performance attemptのreplacementだけを破る。"""
    value = {"planned_execution": {"consumed_cluster_slots": [1]}, "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "post_performance_failure", "replaces_attempt_id": "old", "performance_started_marker": {}, "failure_evidence": {"kind": "driver"}}], "actual_runs": []}
    _assert_semantic("reason", semantic._validate_reason_branches, value, {}, anomaly=False)


def test_replacement_chain_rejects_cycles() -> None:
    value = {
        "attempts": [
            {"attempt_id": "a", "replaces_attempt_id": "b", "parent_attempt_id": None, "allocation_id": None},
            {"attempt_id": "b", "replaces_attempt_id": "a", "parent_attempt_id": None, "allocation_id": None},
        ],
        "allocations": [],
        "actual_runs": [],
        "liveness": [],
        "correctness_evidence": [],
        "planned_execution": {"runs": []},
    }
    _assert_semantic("reference", semantic._validate_reference_graph, value, {})


def test_top_level_replacement_cycle_is_rejected(tmp_path: Path) -> None:
    fixture = _make_git_fixture(tmp_path)
    value, schema = _full_receipt(fixture)
    value["attempts"][0]["replaces_attempt_id"] = "attempt-verification"
    value["attempts"][1]["replaces_attempt_id"] = "attempt-performance"
    _assert_semantic(
        "reference",
        semantic._validate_receipt_semantics,
        fixture.root,
        _receipt_document(value),
        schema=schema,
        binding=fixture.binding,
    )


def test_a03_failure_is_assigned_to_an_exact_attempt_id() -> None:
    own = semantic.A03Result("short_columns", None, True, (), ())
    child = semantic.A03Result(None, 0.0, False, (0,) * 8, (0,) * 8)
    observations = {"attempt:a:0": own, "attempt:a:child:0": child}
    assert semantic._attempt_observation_failures(observations, "a") == (own,)
    assert semantic._attempt_observation_failures(observations, "a:child") == (child,)


def test_reference_graph_rejects_dangling_and_duplicate_ids() -> None:
    """shape検査を通過し、dangling allocation refのsemantic一点だけで拒否する。"""
    value = {"attempts": [{"attempt_id": "a", "replaces_attempt_id": None, "parent_attempt_id": None, "allocation_id": "alloc"}], "allocations": [{"allocation_id": "alloc", "allocation_role": "verification", "cluster_slot_or_null": None}], "actual_runs": [{"run_id": "r", "attempt_id": "a", "allocation_id": "missing"}], "liveness": [], "correctness_evidence": [], "planned_execution": {"runs": [{"run_id": "r"}]}}
    _assert_semantic("reference", semantic._validate_reference_graph, value, {"r": value["planned_execution"]["runs"][0]})


def test_planned_actual_rejects_gap_and_late_completion() -> None:
    """shape検査を通過し、actual prefixの先頭を飛ばすsemantic一点だけで拒否する。"""
    value = {"planned_execution": {"runs": [{"run_id": "p1", "cluster_slot": 1}, {"run_id": "p2", "cluster_slot": 1}]}, "actual_runs": [{"run_id": "p2", "attempt_id": "a", "actual_ordinal": 1}], "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "post_performance_failure"}]}
    _assert_semantic("planned_actual", semantic._validate_planned_actual_relationship, value, {"p1": value["planned_execution"]["runs"][0], "p2": value["planned_execution"]["runs"][1]})


def test_compile_flags_require_three_legs(tmp_path: Path) -> None:
    """shape検査を通過し、三者一致のcompile実体だけを壊して拒否する。"""
    record = _file_record(tmp_path, "build/compile_commands.json", b"[]")
    _file_record(tmp_path, "build/CMakeCache.txt", b"CCBENCH_TRACE:STRING=0\nCCBENCH_ADD_ANALYSIS:STRING=0\n")
    record_data = {"configure_argv": ["-DCCBENCH_TRACE=0", "-DCCBENCH_ADD_ANALYSIS=0"], "compile_commands": record, "cmake_cache": {"trace": 0, "add_analysis": 0}, "trace_enabled": False, "analysis_enabled": False}
    # The compile_commands empty-list rejection is the sole broken leg here.
    _assert_semantic("compile", semantic._validate_compile_legs, tmp_path, record_data, expected_trace=0, expected_analysis=0)


def test_compile_commands_reject_nonfinite_json_with_parse_cause(tmp_path: Path) -> None:
    """shapeを通過するcompile_commands pointerで、JSON数値の非有限値だけを破る。"""
    commands = (
        b'[{"arguments":["g++","-DTRACE=0",'
        b'"-DADD_ANALYSIS=0"],"diagnostic":1e999999}]'
    )
    record = _file_record(tmp_path, "build/compile_commands.json", commands)
    _file_record(
        tmp_path,
        "build/CMakeCache.txt",
        b"CCBENCH_TRACE:STRING=0\nCCBENCH_ADD_ANALYSIS:STRING=0\n",
    )
    data = {
        "configure_argv": ["-DCCBENCH_TRACE=0", "-DCCBENCH_ADD_ANALYSIS=0"],
        "compile_commands": record,
        "cmake_cache": {"trace": 0, "add_analysis": 0},
        "trace_enabled": False,
        "analysis_enabled": False,
    }
    with pytest.raises(semantic.SemanticValidationError) as info:
        semantic._validate_compile_legs(
            tmp_path,
            data,
            expected_trace=0,
            expected_analysis=0,
        )
    assert isinstance(info.value.__cause__, ReceiptParseError)


def test_cmake_cache_is_reject_only(tmp_path: Path) -> None:
    """shape検査を通過し、raw CMakeCacheの不一致だけで拒否する。"""
    commands = json.dumps([{"arguments": ["g++", "-DTRACE=0", "-DADD_ANALYSIS=0"]}], separators=(",", ":")).encode()
    record = _file_record(tmp_path, "build/compile_commands.json", commands)
    _file_record(tmp_path, "build/CMakeCache.txt", b"CCBENCH_TRACE:STRING=1\nCCBENCH_ADD_ANALYSIS:STRING=0\n")
    data = {"configure_argv": ["-DCCBENCH_TRACE=0", "-DCCBENCH_ADD_ANALYSIS=0"], "compile_commands": record, "cmake_cache": {"trace": 0, "add_analysis": 0}, "trace_enabled": False, "analysis_enabled": False}
    _assert_semantic("compile", semantic._validate_compile_legs, tmp_path, data, expected_trace=0, expected_analysis=0)


def test_argv_raw_and_run_log_are_exact(tmp_path: Path) -> None:
    """a07のtab行とShowOptParametersのmapだけを検査し、余剰source flagは無視する。"""
    raw = _ccbench_log("W1")
    flags, options = semantic._parse_ccbench_run_log(raw)
    assert flags == semantic._EXPECTED_FLAGS["W1"]
    assert {key: options[key] for key in semantic._OPT_PARAMETER_KEYS} == semantic._EXPECTED_OPT_PARAMETERS
    bad = raw.replace(b"#FLAGS_thread_num:\t48", b"#FLAGS_thread_num 48")
    _assert_semantic("run_log", semantic._validate_ccbench_run_log, bad, workload="W1")


def test_ccbench_rejects_unrepresentable_integer_token() -> None:
    raw = _ccbench_log("W1").replace(
        b"#FLAGS_thread_num:\t48",
        b"#FLAGS_thread_num:\t" + b"9" * 5000,
    )
    _assert_semantic("run_log", semantic._validate_ccbench_run_log, raw, workload="W1")


def test_observation_window_cardinality_and_cpu_formula(tmp_path: Path) -> None:
    """正例の36窓を通過させ、raw counterだけから busy core を再計算する。"""
    fixture = _make_git_fixture(tmp_path)
    value, _ = _full_receipt(fixture)
    results = semantic._validate_observations(fixture.root, value)
    assert len(value["attempts"][0]["environment_observations"]) == 36
    assert sum(result.failure for result in results.values()) == 0
    before = _file_record(tmp_path, "before", b"cpu 0 0 0 0 0 0 0 0\n")
    after = _file_record(tmp_path, "after", b"cpu 1 0 0 0 0 0 0 0\n")
    obs = {"stat_before_raw": before, "stat_after_raw": after, "stat_before": [0] * 8, "stat_after": [1, 0, 0, 0, 0, 0, 0, 0], "monotonic_start_ns": 0, "monotonic_end_ns": 10_000_000_000, "malformed_reason": None}
    result = semantic._observation_failure(tmp_path, obs)
    assert result.busy_core_equivalents == 48.0
    assert result.failure is True


def test_schedule_is_redriven_not_taken_from_declared_digest(tmp_path: Path) -> None:
    """shape検査を通過し、canonical raw tableの1 byteだけでsemantic拒否する。"""
    expected = semantic._canonical_schedule_bytes(semantic._A09_SEED)
    tampered = expected.replace(b"W1", b"W2", 1)
    _file_record(tmp_path, "schedule.tsv", tampered)
    planned = {"workloads": {workload: {"driver_argv": list(semantic._EXPECTED_DRIVER_ARGV[workload]), "effective_flags": dict(semantic._EXPECTED_FLAGS[workload]), "opt_parameters": dict(semantic._EXPECTED_OPT_PARAMETERS)} for workload in semantic._WORKLOADS}, "schedule_seed": semantic._A09_SEED, "schedule_algorithm": semantic._A09_ALGORITHM, "schedule_table": _file_record(tmp_path, "schedule.tsv", tampered), "schedule_sha256": hashlib.sha256(tampered).hexdigest(), "consumed_cluster_slots": [1, 2, 3, 4, 5, 6, 7, 8], "cluster_slots": [dict(row) for row in semantic._derive_schedule_rows(semantic._A09_SEED)], "runs": []}
    _assert_semantic("schedule", semantic._validate_schedule, tmp_path, planned, study_stage="pilot")


def test_pilot_slots_are_exact_first_eight() -> None:
    """shape検査を通過し、pilot slot identityの一点だけを9へ変えて拒否する。"""
    planned = {"consumed_cluster_slots": [1, 2, 3, 4, 5, 6, 7, 9]}
    _assert_semantic("schedule", semantic._validate_schedule, Path("/unused"), {"workloads": {"W1": {"driver_argv": list(semantic._EXPECTED_DRIVER_ARGV["W1"]), "effective_flags": dict(semantic._EXPECTED_FLAGS["W1"]), "opt_parameters": dict(semantic._EXPECTED_OPT_PARAMETERS)}, "W2": {"driver_argv": list(semantic._EXPECTED_DRIVER_ARGV["W2"]), "effective_flags": dict(semantic._EXPECTED_FLAGS["W2"]), "opt_parameters": dict(semantic._EXPECTED_OPT_PARAMETERS)}}, "schedule_seed": semantic._A09_SEED, "schedule_algorithm": semantic._A09_ALGORITHM, "schedule_table": {}, "schedule_sha256": "0" * 64, "consumed_cluster_slots": planned["consumed_cluster_slots"], "cluster_slots": [], "runs": []}, study_stage="pilot")


def test_phase_caps_and_monotonic_order_are_recomputed() -> None:
    """shape検査を通過し、phase event順の一点だけを逆転させて拒否する。"""
    caps, events = _phase_data("performance_cluster", 0)
    allocation = {"allocation_role": "performance_cluster", "phase_caps": caps, "phase_events": list(reversed(events)), "started_at_monotonic_ns": 0, "ended_at_monotonic_ns": 20, "internal_deadline_s": 3300, "requested_walltime_s": 3600, "path_choice": "primary_build_outside"}
    _assert_semantic("phase", semantic._validate_phase_budget, {"allocations": [allocation]})


def test_translation_unit_key_and_base_tree_are_redriven(tmp_path: Path) -> None:
    """shape検査を通過し、POSIX正規化不能なTU keyだけを置いて拒否する。"""
    value = {"measurement_checkout": {"repository_head": "a" * 40, "ccbench_head": semantic._CCBENCH_PIN}, "arms": {arm: {"compile": {"source": {"repo_commit": "a" * 40, "ccbench_pin": semantic._CCBENCH_PIN, "base_tree_sha": "b" * 40, "patch_path": None if arm == "stock" else semantic._EXPECTED_PATCH_PATH, "patch_sha256": None if arm == "stock" else semantic._EXPECTED_PATCH_SHA256}, "mode_macro": semantic._EXPECTED_MODE_MACROS[arm], "translation_units": {"src/../bad.cc": {"sha256": "c" * 64}}}} for arm in semantic._ARMS}}
    _assert_semantic("source", semantic._validate_source_identity, tmp_path, value)


def test_translation_units_are_nonempty_and_match_source_digest(tmp_path: Path) -> None:
    fixture = _make_git_fixture(tmp_path)
    value, schema = _full_receipt(fixture)
    value["arms"]["stock"]["compile"]["translation_units"] = {}
    _assert_semantic(
        "source",
        semantic._validate_receipt_semantics,
        fixture.root,
        _receipt_document(value),
        schema=schema,
        binding=fixture.binding,
    )

    value, schema = _full_receipt(fixture)
    value["arms"]["stock"]["compile"]["translation_units"]["transaction.cc"][
        "sha256"
    ] = "0" * 64
    _assert_semantic(
        "source",
        semantic._validate_receipt_semantics,
        fixture.root,
        _receipt_document(value),
        schema=schema,
        binding=fixture.binding,
    )


def test_nonexistent_translation_unit_rejects_synthetic_compile_digest(
    tmp_path: Path,
) -> None:
    """実在しないTUをcompile_commands由来の合成digestで偽装できない。"""
    fixture = _make_git_fixture(tmp_path)
    value, schema = _full_receipt(fixture)
    (fixture.root / "transaction.cc").unlink()

    command_argv = value["arms"]["stock"]["compile"]["translation_units"][
        "transaction.cc"
    ]["normalized_argv"]
    synthetic = json.dumps(
        {"file": "transaction.cc", "arguments": command_argv},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    for arm in semantic._ARMS:
        value["arms"][arm]["compile"]["translation_units"]["transaction.cc"][
            "sha256"
        ] = hashlib.sha256(synthetic).hexdigest()

    _assert_semantic(
        "source",
        semantic._validate_receipt_semantics,
        fixture.root,
        _receipt_document(value),
        schema=schema,
        binding=fixture.binding,
    )


def test_pointer_reader_checks_size_digest_and_symlink(tmp_path: Path) -> None:
    """各独立 fixture は shape を通過し、digestまたはsymlink traversalの1点だけを破る。"""
    record = _file_record(tmp_path, "safe.txt", b"safe")
    bad = dict(record, sha256="0" * 64)
    _assert_semantic("pointer", semantic._read_file_record, tmp_path, bad, label="bad")
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    (tmp_path / "link").symlink_to(outside)
    link = {"path": "link", "size": 7, "sha256": hashlib.sha256(b"outside").hexdigest()}
    with pytest.raises(semantic.SemanticValidationError) as info:
        semantic._read_file_record(tmp_path, link, label="link")
    assert info.value.reason_code == "pointer"
    assert isinstance(info.value.__cause__, SafeIOError)


def test_declared_use_class_cannot_bypass_missing_attempt_facts() -> None:
    """shape検査を通過し、dry宣言でもcompleted raw facts欠落の一点で拒否する。"""
    value = {"declared_use_class": "dry", "planned_execution": {"consumed_cluster_slots": [1]}, "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "completed", "performance_started_marker": None, "failure_evidence": None}], "actual_runs": []}
    _assert_semantic("reason", semantic._validate_reason_branches, value, {}, anomaly=False)


def test_reason_code_completed_is_not_positive_authority() -> None:
    """shape検査を通過し、completed申告以外のraw facts欠落だけで拒否する。"""
    value = {"planned_execution": {"consumed_cluster_slots": [1]}, "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "completed", "performance_started_marker": None, "failure_evidence": None}], "actual_runs": []}
    _assert_semantic("reason", semantic._validate_reason_branches, value, {}, anomaly=False)


def test_qsub_returncode_is_not_positive_authority() -> None:
    """shape検査を通過し、returncode=0申告だけではcompletedにできない一点を拒否する。"""
    value = {"planned_execution": {"consumed_cluster_slots": [1]}, "attempts": [{"attempt_id": "a", "cluster_slot_or_null": 1, "reason_code": "completed", "performance_started_marker": None, "failure_evidence": None, "qsub_result": {"returncode": 0}}], "actual_runs": []}
    _assert_semantic("reason", semantic._validate_reason_branches, value, {}, anomaly=False)


def test_exclusivity_raw_is_not_a_verdict() -> None:
    """shape検査を通過し、exclusivity rawを合否へ昇格しないままphase算術だけを検査する。"""
    caps, events = _phase_data("verification", 0)
    allocation = {"allocation_role": "verification", "cluster_slot_or_null": None, "phase_caps": caps, "phase_events": events, "started_at_monotonic_ns": 0, "ended_at_monotonic_ns": 20, "internal_deadline_s": 3300, "requested_walltime_s": 3600, "path_choice": "primary_build_outside", "exclusivity": {"method": "scheduler_accounting", "raw": {"path": "raw", "size": 0, "sha256": "0" * 64}}}
    semantic._validate_phase_budget({"allocations": [allocation]})


def test_fixed_inputs_and_declared_digest_are_reject_only(tmp_path: Path) -> None:
    """shape検査を通過し、自己申告digestをpositive authorityへ昇格させず拒否する。"""
    expected = semantic._canonical_schedule_bytes(semantic._A09_SEED)
    assert hashlib.sha256(expected).hexdigest() != "0" * 64
    raw = json.dumps({"B": 2, "seed": "e" * 64}, separators=(",", ":")).encode()
    receipt = _file_record(tmp_path, "stress.json", raw)
    value = {
        "declared_use_class": "official",
        "admission_telemetry": [{
            "kind": "stress_check_simulation",
            "fixed_inputs": {"input_sha256": "a" * 64, "B_or_null": 1, "seed_or_null": "e" * 64},
            "receipt": receipt,
        }],
    }
    _assert_semantic("reject_only", semantic._validate_reject_only, tmp_path, value)


def test_anomaly_clean_declaration_is_killed_by_raw_evidence(tmp_path: Path) -> None:
    """top-level入口で、clean申告ではraw不一致を覆せないことを確認する。"""
    fixture = _make_git_fixture(tmp_path)
    value, schema = _full_receipt(fixture)
    bad_raw = json.dumps(
        {"expected": {"value": 10}, "actual": {"value": 11}, "clean": True},
        separators=(",", ":"),
    ).encode()
    value["correctness_evidence"][0]["outputs"] = [
        _file_record(fixture.root, "correctness/stock-w1.json", bad_raw)
    ]
    _assert_semantic(
        "correctness",
        semantic._validate_receipt_semantics,
        fixture.root,
        _receipt_document(value),
        schema=schema,
        binding=fixture.binding,
    )


@pytest.mark.parametrize(
    "raw",
    [b"[]", b"not correctness evidence\n", b"\xff\xfe"],
    ids=["json-array", "unrecognized-text", "invalid-utf8"],
)
def test_correctness_raw_without_comparable_pair_is_rejected_top_level(
    tmp_path: Path, raw: bytes
) -> None:
    fixture = _make_git_fixture(tmp_path)
    value, schema = _full_receipt(fixture)
    value["correctness_evidence"][0]["outputs"] = [
        _file_record(fixture.root, "correctness/stock-w1.json", raw)
    ]
    _assert_semantic(
        "correctness",
        semantic._validate_receipt_semantics,
        fixture.root,
        _receipt_document(value),
        schema=schema,
        binding=fixture.binding,
    )


def test_preregistration_eight_key_adapter_compares_all_nine_fields(tmp_path: Path) -> None:
    """shape検査を通過する8-key objectで、binding対応fieldの1つだけを改変して拒否する。"""
    fixture = _make_git_fixture(tmp_path)
    value = _preregistration_value(fixture.record)
    adapted = semantic._validate_preregistration(fixture.root, value, binding=fixture.binding)
    assert adapted == fixture.record
    value["composed_core_sha256"] = "0" * 64
    _assert_semantic("preregistration", semantic._parse_preregistration_8key, value, binding=fixture.binding)


def test_study_receipts_require_order_coverage_and_verification_digest_identity(
    tmp_path: Path,
) -> None:
    fixture = _make_git_fixture(tmp_path)
    pilot, schema = _full_receipt(fixture)
    main = copy.deepcopy(pilot)
    main["study_stage"] = "main_run"
    pilot_document = _receipt_document(pilot)
    main_document = _receipt_document(main)
    semantic._validate_study_receipts(
        fixture.root,
        [pilot_document, main_document],
        schema=schema,
        binding=fixture.binding,
    )

    _assert_semantic(
        "study",
        semantic._validate_study_receipts,
        fixture.root,
        [pilot_document],
        schema=schema,
        binding=fixture.binding,
    )
    duplicate_main = copy.deepcopy(main)
    duplicate_main["study_stage"] = "pilot"
    _assert_semantic(
        "study",
        semantic._validate_study_receipts,
        fixture.root,
        [pilot_document, _receipt_document(duplicate_main)],
        schema=schema,
        binding=fixture.binding,
    )

    changed_trace = copy.deepcopy(main)
    changed_trace["allocations"][1]["accounting_trace"] = _file_record(
        fixture.root,
        "build/accounting-verification-changed",
        b"changed-accounting\n",
    )
    _assert_semantic(
        "study",
        semantic._validate_study_receipts,
        fixture.root,
        [pilot_document, _receipt_document(changed_trace)],
        schema=schema,
        binding=fixture.binding,
    )


def test_forged_binding_like_object_is_rejected(tmp_path: Path) -> None:
    """shape検査を通過し、正しいtokenを得ていないbinding-like objectだけを拒否する。"""
    fixture = _make_git_fixture(tmp_path)
    forged = SimpleNamespace(record=fixture.record, prereg_commit=fixture.binding.prereg_commit)
    _assert_semantic("authority", semantic._parse_preregistration_8key, _preregistration_value(fixture.record), binding=forged)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
