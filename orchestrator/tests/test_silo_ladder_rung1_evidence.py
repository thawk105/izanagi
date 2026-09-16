# -*- coding: utf-8 -*-
"""Committed rung-1 evidence を raw bytes へ独立再束縛する commit-II gate。

この module は他 test module を import しない。現行ホストの compiler や
superproject HEAD も参照せず、repository に commit された bytes、hash receipt、
登録 calibration 契約だけを根拠にする。
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import statistics
import sys
import tempfile
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORCHESTRATOR = ROOT / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR.parent))

from pegasus_policy_expected_goldens import (  # noqa: E402
    EXPECTED_CURRENT_PEGASUS_POLICY_SHA256,
    EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256,
)
from orchestrator.campaign import env_attestation, env_contract, execution_guard  # noqa: E402
from orchestrator.campaign.silo_ladder_rung1 import (  # noqa: E402
    PIN,
    REPORT_MACRO,
    RUNG_MACRO,
    _configure_argv,
    _validate_correctness_commit_witness,
    compile_commands_for_sources,
    runtime_modules_binding,
    third_party_policy,
    tool_version_body,
    validate_compile_argv,
    validate_nqsv_accounting_epilogue,
)


EVIDENCE = (
    ROOT
    / "output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json"
)
LEDGER = ROOT / "patches/ledger.json"
RAW_MANIFEST_SCHEMA = "silo_ladder_rung1-raw-manifest/v1"
SCHEDULE_SCHEMA = "silo_ladder_rung1-schedule/v1"
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
EXPECTED_CHECK_KEYS = {
    "correctness",
    "schedule",
    "per_worker_ever_committed",
    "bounded_completion",
    "performance_direction",
    "activation",
    "attestation",
    "raw_recomputed",
}
SOURCE_FILES = (
    "cc/silo/transaction.cc",
    "cc/silo/ycsb_silo.cc",
)
HISTORICAL_SILO_EVIDENCE_IDENTITY = (
    "38f5de0e2c71ff820696c051c9382f7850e2e7914319b20b8dff5ec45a484b37",
    "e0e3779e67b3c67deacf7ea5bb2165aace4909d25e423f3e8df5c9a55fa5a3c2",
    "753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49",
    "92affaabf723d83c10731a9b506aceb346e3652a8aeedcba85d48f52a31355f8",
)
HISTORICAL_CCBENCH_PIN_FULL = "d706650cdb31e442bef45b9b4216951d4fb40969"
HISTORICAL_LEDGER_SHA256 = (
    "34d6bfe7d81fcdb3381532ac1d6aadb3b70a20d56be027dd2f584b610cddf603"
)
EXPECTED_HISTORICAL_VERIFIER_MODULE_SHA256 = (
    "e604cef0b06dc36dd8e236b8ade92eb452231a5f32b7926405b402f038e9d8a2"
)
EXPECTED_HISTORICAL_PBS_JOB_SHA256 = (
    "318c2b12fb3fa71b3587c81f201db640393d2adae2214fd6aca4a9222ab2f57c"
)
EXPECTED_CURRENT_PBS_JOB_SHA256 = (
    "99687368a1fdf10d8f699be3a32afd2814f51d98bcad5fbdf6a1862ca72b456f"
)
EXPECTED_HISTORICAL_SUBMITTER_SHA256 = (
    "e12ac6589f7587540b38d5c528b2561e446031b4ce0ee48443ee4be583d8e9b2"
)
EXPECTED_CURRENT_SUBMITTER_SHA256 = (
    "6990ad4470aba09b8c62224f33a453c330a0be4fbb913cf1e477bb882659412b"
)
# 2026-08-12 [T-816] base commit 前進により patched source hash が移動。凍結 bundle の記録値を歴史 golden として固定する。
EXPECTED_HISTORICAL_PATCHED_SOURCE_SHA256 = {
    "cc/silo/transaction.cc": (
        "847d27b07783fcb6bcd0c8f64514bf0292e407549039462f42870b9ac1d16d4b"
    ),
    "cc/silo/ycsb_silo.cc": (
        "716c4dd21c6c2c1098ab4c6f48f1b6f0c6df24dcdbeabed86472645397d68fa3"
    ),
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalize_job_id(value: str) -> str:
    return value[2:] if value.startswith("0:") else value


def _no_duplicate_object(pairs):
    value = {}
    for key, item in pairs:
        assert key not in value, f"duplicate JSON key: {key!r}"
        value[key] = item
    return value


def _load_json_bytes(path: Path) -> tuple[bytes, Any]:
    assert path.is_file(), f"required committed artifact is missing: {path}"
    raw = path.read_bytes()
    return raw, json.loads(raw, object_pairs_hook=_no_duplicate_object)


def _confined_file(root: Path, relative: str) -> Path:
    assert isinstance(relative, str) and relative
    path = Path(relative)
    assert not path.is_absolute() and ".." not in path.parts, (
        f"raw bundle path must be confined and relative: {relative!r}"
    )
    resolved_root = root.resolve()
    resolved = (root / path).resolve()
    assert resolved == resolved_root or resolved_root in resolved.parents, (
        f"raw bundle path escapes root: {relative!r}"
    )
    assert not (root / path).is_symlink(), f"raw bundle symlink is forbidden: {relative}"
    assert resolved.is_file(), f"raw bundle file is missing: {relative}"
    return resolved


def _raw_documents(evidence: Mapping[str, Any]) -> tuple[dict[str, bytes], list[Any]]:
    bundle = evidence["raw_bundle"]
    assert set(bundle) == {"root", "paths"}
    raw_root_text = bundle["root"]
    assert isinstance(raw_root_text, str) and raw_root_text
    assert not Path(raw_root_text).is_absolute(), (
        "raw_bundle.root must be repository-relative; acquisition host absolute "
        "paths are not committed-content bindings"
    )
    raw_root = (ROOT / raw_root_text).resolve()
    assert raw_root.is_dir(), f"raw bundle root is missing: {raw_root}"
    paths = bundle["paths"]
    assert isinstance(paths, list) and paths
    assert len(paths) == len(set(paths)), "raw_bundle.paths contains duplicates"

    # top-level manifest はちょうど 1 個。attempt subtree の self-manifest は
    # attempt seal の一部であり、この top-level count の対象外。
    manifest_names = [path for path in paths if path == "raw-manifest.json"]
    assert len(manifest_names) == 1, (
        "raw bundle needs exactly one raw-manifest.json hash receipt"
    )
    manifest_path = _confined_file(raw_root, manifest_names[0])
    _, manifest = _load_json_bytes(manifest_path)
    assert set(manifest) == {"schema_version", "files"}
    assert manifest["schema_version"] == RAW_MANIFEST_SCHEMA
    files = manifest["files"]
    assert isinstance(files, list) and files
    assert all(
        isinstance(item, dict) and set(item) == {"path", "sha256"}
        and isinstance(item["path"], str)
        and isinstance(item["sha256"], str)
        and HEX64.fullmatch(item["sha256"])
        for item in files
    )
    receipt_paths = [item["path"] for item in files]
    assert len(receipt_paths) == len(set(receipt_paths))
    assert set(receipt_paths) == set(paths) - {manifest_names[0]}, (
        "raw manifest must bind every raw path except itself, without extras"
    )

    raw_by_path: dict[str, bytes] = {}
    documents: list[Any] = []
    for receipt in files:
        path = _confined_file(raw_root, receipt["path"])
        raw = path.read_bytes()
        assert _sha256(raw) == receipt["sha256"], (
            f"raw receipt sha256 mismatch: {receipt['path']}"
        )
        raw_by_path[receipt["path"]] = raw
        if path.suffix == ".json":
            documents.append(
                json.loads(raw, object_pairs_hook=_no_duplicate_object)
            )
    assert any("verifier" in path for path in raw_by_path)
    assert any("schedule" in path or "submit-receipt" in path for path in raw_by_path)
    assert any("accounting" in path for path in raw_by_path)
    return raw_by_path, documents


def _assert_attempt_subtree_sealed(
    raw_by_path: Mapping[str, bytes], attempt: Mapping[str, Any],
) -> None:
    prefix = f"attempts/{attempt['attempt']}/"
    subtree = {
        path[len(prefix):]: raw
        for path, raw in raw_by_path.items()
        if path.startswith(prefix)
    }
    manifest_raw = subtree["raw-manifest.json"]
    manifest = json.loads(
        manifest_raw, object_pairs_hook=_no_duplicate_object,
    )
    assert set(manifest) == {"schema_version", "files"}
    assert manifest["schema_version"] == RAW_MANIFEST_SCHEMA
    manifest_paths = [item["path"] for item in manifest["files"]]
    assert len(manifest_paths) == len(set(manifest_paths))
    assert set(manifest_paths) == set(subtree) - {"raw-manifest.json"}
    for item in manifest["files"]:
        assert set(item) == {"path", "sha256"}
        assert _sha256(subtree[item["path"]]) == item["sha256"]

    receipt_raw = subtree["attempt-receipt.json"]
    assert _sha256(receipt_raw) == attempt["attempt_receipt_sha256"]
    receipt = json.loads(receipt_raw, object_pairs_hook=_no_duplicate_object)
    assert set(receipt) == {"schema_version", "attempt", "files"}
    assert receipt["schema_version"] == "silo_ladder_rung1-attempt-receipt/v1"
    assert receipt["attempt"] == attempt["attempt"]
    receipt_paths = [item["path"] for item in receipt["files"]]
    assert len(receipt_paths) == len(set(receipt_paths))
    expected = {
        path for path in subtree
        if path != "attempt-receipt.json"
        and Path(path).name != "raw-manifest.json"
    }
    assert set(receipt_paths) == expected
    for item in receipt["files"]:
        assert set(item) == {"path", "sha256"}
        assert _sha256(subtree[item["path"]]) == item["sha256"]


def _assert_command_link(
    receipt: Mapping[str, Any], *, expected_argv0: str, argv_tail: list[str],
    target_sha256: str, stdout_raw: bytes, stderr_raw: bytes,
    argv0_sha256: str,
) -> None:
    assert receipt["argv"][0] == expected_argv0
    assert receipt["argv"][1:] == argv_tail
    assert receipt["returncode"] == 0
    assert receipt["timed_out"] is False
    assert receipt["target_sha256"] == target_sha256
    assert receipt["stdout_sha256"] == _sha256(stdout_raw)
    assert receipt["stderr_sha256"] == _sha256(stderr_raw)
    assert receipt["argv0_sha256"] == argv0_sha256


def _unique_projected(documents: list[Any], projector, label: str):
    projected = []
    for document in documents:
        value = projector(document)
        if value is not None:
            projected.append(value)
    canonical = {
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        for value in projected
    }
    assert len(canonical) == 1, (
        f"raw bundle must contain one consistent {label}; "
        f"found {len(projected)} candidates/{len(canonical)} values"
    )
    return json.loads(next(iter(canonical)))


def _schedule_from(document):
    if not isinstance(document, dict):
        return None
    if document.get("schema_version") == SCHEDULE_SCHEMA:
        return document
    receipt = document.get("schedule_receipt")
    if isinstance(receipt, dict):
        return receipt
    gap = document.get("gap_leg")
    if isinstance(gap, dict) and isinstance(gap.get("schedule_receipt"), dict):
        return gap["schedule_receipt"]
    return None


def _gap_from(document):
    if isinstance(document, dict) and isinstance(document.get("gap_leg"), dict):
        gap = document["gap_leg"]
        if "performance_runs" in gap and "liveness_runs" in gap:
            return gap
    return None


def _verifier_from(document):
    if not isinstance(document, dict):
        return None
    required = {
        "runs", "certified_serializable", "non_serializable",
        "indeterminate", "results",
    }
    if required <= set(document):
        return {key: document[key] for key in required}
    verifier = document.get("verifier")
    if isinstance(verifier, dict) and required <= set(verifier):
        return {key: verifier[key] for key in required}
    correctness = document.get("correctness_leg")
    if isinstance(correctness, dict) and isinstance(correctness.get("verifier"), dict):
        verifier = correctness["verifier"]
        if required <= set(verifier):
            return {key: verifier[key] for key in required}
    return None


def _provenance_from(document):
    if isinstance(document, dict) and isinstance(document.get("provenance"), dict):
        return document["provenance"]
    return None


def _assert_balanced_schedule(schedule: Mapping[str, Any]) -> None:
    assert set(schedule) == {"schema_version", "algorithm", "seed", "runs"}
    assert schedule["schema_version"] == SCHEDULE_SCHEMA
    assert isinstance(schedule["seed"], str) and HEX64.fullmatch(schedule["seed"])
    rows = schedule["runs"]
    assert isinstance(rows, list) and len(rows) == 24
    assert [row["ordinal"] for row in rows] == list(range(24))
    assert all(
        isinstance(row, dict)
        and set(row) == {"ordinal", "workload", "rep", "variant"}
        for row in rows
    )
    for workload in ("W-cal", "W-hw"):
        first_variants = []
        for rep in range(1, 7):
            indexes = [
                index for index, row in enumerate(rows)
                if row["workload"] == workload and row["rep"] == rep
            ]
            pair = [rows[index] for index in indexes]
            assert len(pair) == 2
            assert indexes[1] == indexes[0] + 1
            assert {row["variant"] for row in pair} == {"stock", "rung-perf"}
            first_variants.append(pair[0]["variant"])
        assert Counter(first_variants) == {"stock": 3, "rung-perf": 3}
    first_variants = []
    first_workloads = []
    for rep in range(1, 7):
        rep_rows = [row for row in rows if row["rep"] == rep]
        assert len(rep_rows) == 4
        first_variants.append(rep_rows[0]["variant"])
        first_workloads.append(rep_rows[0]["workload"])
    assert Counter(first_variants) == {"stock": 3, "rung-perf": 3}
    assert Counter(first_workloads) == {"W-cal": 3, "W-hw": 3}


def _registered_workloads(calibration: Mapping[str, Any]) -> dict[str, list[str]]:
    workload = calibration["workload"]
    assert set(workload) == {"ycsb_rmw", "ycsb_rratio", "ycsb_zipf_skew"}
    assert workload == {
        "ycsb_rmw": "0",
        "ycsb_rratio": "50",
        "ycsb_zipf_skew": "0.9",
    }
    records = calibration["saturation"]["records"]
    threads = calibration["threads"]
    return {
        "W-cal": [
            "-ycsb_rmw=false",
            f"-ycsb_rratio={workload['ycsb_rratio']}",
            f"-ycsb_zipf_skew={workload['ycsb_zipf_skew']}",
            f"-ycsb_tuple_num={records}",
            "-ycsb_max_ope=10",
            f"-thread_num={threads}",
            "-extime=3",
        ],
        "W-hw": [
            "-ycsb_rmw=true",
            f"-ycsb_zipf_skew={workload['ycsb_zipf_skew']}",
            f"-ycsb_tuple_num={records}",
            "-ycsb_max_ope=10",
            f"-thread_num={threads}",
            "-extime=3",
        ],
    }


def _recompute_patched_source_hashes(
    entry: Mapping[str, Any],
) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="rung1-evidence-patch-") as temp:
        model = Path(temp)
        for relative in entry["source_files"]:
            target = model / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shown = subprocess.run(
                [
                    "git", "-C", str(ROOT / entry["base_repo"]), "show",
                    f"{entry['base_commit']}:{relative}",
                ],
                check=True, capture_output=True,
            )
            target.write_bytes(shown.stdout)
        subprocess.run(["git", "init", "-q"], cwd=model, check=True)
        subprocess.run(
            ["git", "apply", str(ROOT / entry["path"])],
            cwd=model, check=True,
        )
        return {
            relative: _sha256((model / relative).read_bytes())
            for relative in entry["source_files"]
        }


TPS_RE = re.compile(r"(?m)^throughput\[tps\]:\s*(\d+)\s*$")
COMMIT_RE = re.compile(r"(?m)^commit_counts_:\s*(\d+)\s*$")
BATCH_RE = re.compile(r"(?m)^batch_commit_counts_:\s*(\d+)\s*$")
WORKER_RE = re.compile(
    r"(?m)^silo_ladder_rung1\.worker_commit\[(\d+)\]=(\d+)\s*$"
)
WORKER_BATCH_RE = re.compile(
    r"(?m)^silo_ladder_rung1\.worker_batch_commit\[(\d+)\]=(\d+)\s*$"
)


def _raw_text(raw_by_path: Mapping[str, bytes], path: str) -> str:
    assert path in raw_by_path, f"raw path is absent from manifest: {path}"
    return raw_by_path[path].decode("utf-8")


def _parse_run_stdout(raw: str, *, workers: bool) -> dict[str, Any]:
    commits = COMMIT_RE.findall(raw)
    batches = BATCH_RE.findall(raw)
    assert len(commits) == len(batches) == 1
    result: dict[str, Any] = {
        "commit_count": int(commits[0]),
        "batch_commit_count": int(batches[0]),
    }
    if not workers:
        throughputs = TPS_RE.findall(raw)
        assert len(throughputs) == 1
        result["throughput_tps"] = int(throughputs[0])
        return result
    worker_pairs = sorted(
        (int(worker), int(value)) for worker, value in WORKER_RE.findall(raw)
    )
    batch_pairs = sorted(
        (int(worker), int(value))
        for worker, value in WORKER_BATCH_RE.findall(raw)
    )
    assert [worker for worker, _ in worker_pairs] == list(range(48))
    assert [worker for worker, _ in batch_pairs] == list(range(48))
    result["per_worker_commits"] = [
        {"worker": worker, "commits": value}
        for worker, value in worker_pairs
    ]
    result["per_worker_batch_commits"] = [
        {"worker": worker, "commits": value}
        for worker, value in batch_pairs
    ]
    return result


def _assert_command_receipts(
    raw_by_path: Mapping[str, bytes],
) -> None:
    paths = [
        path for path in raw_by_path if path.endswith(".command.json")
    ]
    assert paths, "all subprocess acquisition must emit command receipts"
    for path in paths:
        receipt = json.loads(
            raw_by_path[path], object_pairs_hook=_no_duplicate_object
        )
        assert set(receipt) == {
            "schema_version", "argv", "cwd", "started_at_utc",
            "completed_at_utc", "elapsed_monotonic_s", "timeout_s",
            "timed_out", "returncode", "stdout_sha256", "stderr_sha256",
            "argv0_sha256", "target_sha256",
        }
        assert receipt["schema_version"] == (
            "silo_ladder_rung1-command-receipt/v1"
        )
        assert isinstance(receipt["argv"], list) and receipt["argv"]
        assert Path(receipt["cwd"]).is_absolute()
        assert receipt["timed_out"] is False
        assert isinstance(receipt["returncode"], int)
        assert HEX64.fullmatch(receipt["stdout_sha256"])
        assert HEX64.fullmatch(receipt["stderr_sha256"])
        assert receipt["argv0_sha256"] is None or HEX64.fullmatch(
            receipt["argv0_sha256"]
        )
        if Path(str(receipt["argv"][0])).name in {"nm", "readelf"}:
            assert isinstance(receipt["argv0_sha256"], str)
            assert HEX64.fullmatch(receipt["argv0_sha256"])
        assert receipt["target_sha256"] is None or HEX64.fullmatch(
            receipt["target_sha256"]
        )


def _assert_workloads_and_runs(
    gap: Mapping[str, Any],
    schedule: Mapping[str, Any],
    expected_argv: Mapping[str, list[str]],
    raw_by_path: Mapping[str, bytes],
) -> None:
    declarations = gap["workloads"]
    assert declarations == [
        {
            "id": "W-cal",
            "calibration_status": "registered",
            "argv": expected_argv["W-cal"],
        },
        {
            "id": "W-hw",
            "calibration_status": "contract-transfer-only",
            "argv": expected_argv["W-hw"],
        },
    ]

    performance = gap["performance_runs"]
    builds = {item["id"]: item for item in gap["builds"]}
    assert isinstance(performance, list) and len(performance) == 24
    assert [run["ordinal"] for run in performance] == list(range(24))
    for row, run in zip(schedule["runs"], performance):
        assert {
            "ordinal": run["ordinal"],
            "workload": run["workload"],
            "rep": run["rep"],
            "variant": run["variant"],
        } == row
        assert run["binary_id"] == run["variant"]
        assert run["workload_argv"] == expected_argv[run["workload"]]
        assert run["argv"][1:] == run["workload_argv"]
        assert run["returncode"] == 0
        parsed = _parse_run_stdout(
            _raw_text(raw_by_path, run["raw_path"] + "/stdout.txt"),
            workers=False,
        )
        assert parsed == {
            "throughput_tps": run["throughput_tps"],
            "commit_count": run["commit_count"],
            "batch_commit_count": run["batch_commit_count"],
        }
        assert _sha256(
            raw_by_path[run["raw_path"] + "/stdout.txt"]
        ) == run["stdout_sha256"]
        assert _sha256(
            raw_by_path[run["raw_path"] + "/stderr.txt"]
        ) == run["stderr_sha256"]
        command = json.loads(
            raw_by_path[run["raw_path"] + "/run.command.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        _assert_command_link(
            command,
            expected_argv0=run["argv"][0],
            argv_tail=run["workload_argv"],
            target_sha256=builds[run["binary_id"]]["binary_sha256"],
            stdout_raw=raw_by_path[run["raw_path"] + "/stdout.txt"],
            stderr_raw=raw_by_path[run["raw_path"] + "/stderr.txt"],
            argv0_sha256=builds[run["binary_id"]]["binary_sha256"],
        )
        if run["variant"] == "stock":
            assert parsed["commit_count"] > 0
            assert parsed["batch_commit_count"] == 0

    for workload in expected_argv:
        stock = [
            run["throughput_tps"] for run in performance
            if run["workload"] == workload and run["variant"] == "stock"
        ]
        rung = [
            run["throughput_tps"] for run in performance
            if run["workload"] == workload and run["variant"] == "rung-perf"
        ]
        assert len(stock) == len(rung) == 6
        assert max(rung) < min(stock), (
            f"{workload}: max(rung) < min(stock) is false"
        )

    liveness = gap["liveness_runs"]
    assert isinstance(liveness, list) and len(liveness) == 4
    assert {
        (run["workload"], run["rep"]) for run in liveness
    } == {
        (workload, rep)
        for workload in expected_argv
        for rep in (1, 2)
    }
    for run in liveness:
        assert run["ordinal"] in range(24, 28)
        assert run["variant"] == "rung-liveness"
        assert run["binary_id"] == "rung-liveness"
        assert run["workload_argv"] == expected_argv[run["workload"]]
        assert run["argv"][1:] == run["workload_argv"]
        assert run["returncode"] == 0 and run["bounded_completion"] is True
        parsed = _parse_run_stdout(
            _raw_text(raw_by_path, run["raw_path"] + "/stdout.txt"),
            workers=True,
        )
        assert all(parsed[key] == run[key] for key in (
            "commit_count", "batch_commit_count", "per_worker_commits",
            "per_worker_batch_commits",
        ))
        workers = parsed["per_worker_commits"]
        batches = parsed["per_worker_batch_commits"]
        assert [item["worker"] for item in workers] == list(range(48))
        assert all(type(item["commits"]) is int and item["commits"] > 0 for item in workers)
        assert sum(item["commits"] for item in workers) == run["commit_count"]
        assert [item["worker"] for item in batches] == list(range(48))
        assert all(item["commits"] == 0 for item in batches)
        assert run["batch_commit_count"] == 0
        command = json.loads(
            raw_by_path[run["raw_path"] + "/run.command.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        _assert_command_link(
            command,
            expected_argv0=run["argv"][0],
            argv_tail=run["workload_argv"],
            target_sha256=builds["rung-liveness"]["binary_sha256"],
            stdout_raw=raw_by_path[run["raw_path"] + "/stdout.txt"],
            stderr_raw=raw_by_path[run["raw_path"] + "/stderr.txt"],
            argv0_sha256=builds["rung-liveness"]["binary_sha256"],
        )


def _tool_records(value: Any):
    if isinstance(value, dict):
        if (
            value.get("name") in {"gcc", "g++"}
            and isinstance(value.get("realpath"), str)
            and isinstance(value.get("version"), str)
        ):
            yield value
        for child in value.values():
            yield from _tool_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _tool_records(child)


def _assert_compiler_contract(
    provenance: Mapping[str, Any],
    raw_provenance: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> None:
    final_records = list(_tool_records(provenance))
    raw_records = list(_tool_records(raw_provenance))
    assert final_records and raw_records

    def identities(records):
        return {
            (
                item["name"],
                item["realpath"],
                item["version"],
                item.get("sha256"),
            )
            for item in records
        }

    assert identities(final_records) == identities(raw_records)
    by_name = {}
    for record in final_records:
        assert Path(record["realpath"]).is_absolute()
        assert record["version"].strip()
        assert isinstance(record.get("sha256"), str)
        assert HEX64.fullmatch(record["sha256"])
        by_name.setdefault(record["name"], set()).add(
            (record["realpath"], record["version"])
        )
    assert set(by_name) == {"gcc", "g++"}
    assert all(len(identities_) == 1 for identities_ in by_name.values())

    receipt = calibration["acquisition_receipt"]
    registered_argv = receipt["ccbench"]["build_argv"]
    registered_cxx = next(
        token.split("=", 1)[1]
        for token in registered_argv
        if token.startswith("-DCMAKE_CXX_COMPILER=")
    )
    registered_cc = next(
        token.split("=", 1)[1]
        for token in registered_argv
        if token.startswith("-DCMAKE_C_COMPILER=")
    )
    gcc_path, gcc_version = next(iter(by_name["gcc"]))
    gxx_path, _ = next(iter(by_name["g++"]))
    assert gcc_path == registered_cc
    assert gcc_path == receipt["toolchain"]["compiler_path"]
    assert tool_version_body(gcc_version) == tool_version_body(
        receipt["toolchain"]["compiler_version"]
    )
    assert gxx_path == registered_cxx


def _assert_third_party_provenance(
    provenance: Mapping[str, Any],
) -> None:
    policy = third_party_policy(ROOT)
    records = provenance["third_party_sources"]
    assert len(records) == len(policy) == 3
    assert [item["name"] for item in records] == [
        item["name"] for item in policy
    ] == ["masstree", "mimalloc", "googletest"]
    for expected, observed in zip(policy, records):
        assert all(
            observed[key] == expected[key]
            for key in ("name", "source_name", "url", "fetchcontent_ref", "pin")
        )
        assert observed["git_head_raw"] == expected["pin"] + "\n"
        assert observed["git_status_porcelain_raw"] == ""
        assert observed["clean"] is True


def _assert_expected_configure_argv(
    build: Mapping[str, Any],
    provenance: Mapping[str, Any],
    *,
    macros: list[str],
    trace: int,
) -> None:
    observed = build["configure_argv"]
    assert observed[1] == "-S"
    assert observed[3] == "-B"
    tools_by_name = {
        item["name"]: item["realpath"] for item in provenance["tools"]
    }
    dependencies = {
        item["name"]: item for item in build["dependencies"]
    }
    expected = _configure_argv(
        source=Path(observed[2]),
        build=Path(observed[4]),
        tools={
            name: tools_by_name[name] for name in ("cmake", "gcc", "g++")
        },
        prefix=";".join(
            dependencies[name]["resolved_path"] for name in ("gflags", "glog")
        ),
        macros=macros,
        trace=trace,
        third_party_sources=provenance["third_party_sources"],
    )
    assert observed == expected


def _assert_raw_builds(
    gap: Mapping[str, Any],
    raw_by_path: Mapping[str, bytes],
    entry: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> bool:
    builds = gap["builds"]
    assert len(builds) == 3
    assert len({item["id"] for item in builds}) == 3
    by_id = {item["id"]: item for item in builds}
    assert set(by_id) == {"stock", "rung-perf", "rung-liveness"}
    gxx = next(
        item["realpath"] for item in provenance["tools"]
        if item["name"] == "g++"
    )
    tools = {
        item["name"]: item for item in provenance["tools"]
    }
    expected_macros = {
        "stock": [],
        "rung-perf": [entry["macro"]],
        "rung-liveness": [entry["macro"], entry["report_macro"]],
    }
    expected_count = {"stock": 0, "rung-perf": 1, "rung-liveness": 1}
    binary_paths = {build_id: set() for build_id in by_id}
    for run in (*gap["performance_runs"], *gap["liveness_runs"]):
        binary_paths[run["binary_id"]].add(run["argv"][0])
    assert all(len(paths) == 1 for paths in binary_paths.values())
    _, policy = _load_json_bytes(ROOT / "tools/pegasus/policy.json")
    dependency_pins = policy["silo_ladder_rung1"]["dependency_pins"]
    assert dependency_pins == {
        "gflags": policy["gflags_expected_head"],
        "glog": policy["glog_expected_head"],
    }
    for name, pin in dependency_pins.items():
        assert _raw_text(
            raw_by_path, f"job-prologue/{name}-source-head.txt",
        ) == pin + "\n"
        assert _raw_text(
            raw_by_path, f"job-prologue/{name}-source-status.txt",
        ) == ""
    for build_id, build in by_id.items():
        prefix = f"build-{build_id}/"
        compile_commands = json.loads(
            raw_by_path[prefix + "compile_commands.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        target_argv = [
            (item["source_rel"], item["argv"])
            for item in compile_commands_for_sources(
                compile_commands,
                None,
            )
        ]
        expected_macro = None if build_id == "stock" else entry["macro"]
        active_sets = [
            validate_compile_argv(
                argv,
                expected_macro=expected_macro,
                require_report=build_id == "rung-liveness",
                expected_compiler_realpath=gxx,
            )
            for _, argv in target_argv
        ]
        active = [
            macro for macro in (entry["macro"], entry["report_macro"])
            if all(macro in active_set for active_set in active_sets)
        ]
        assert active == expected_macros[build_id] == build["macros"]
        replay = json.loads(
            raw_by_path[prefix + "compile-replay.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        assert replay == {"invocations": build["compile_invocations"]}
        assert (
            len(replay["invocations"]) == len(SOURCE_FILES)
            and {item["source_rel"] for item in replay["invocations"]}
            == set(SOURCE_FILES)
        )
        assert all(
            item["argv"] == dict(target_argv)[item["source_rel"]]
            for item in replay["invocations"]
        )
        transaction = next(
            item for item in replay["invocations"]
            if item["source_rel"] == "cc/silo/transaction.cc"
        )
        assert transaction["object_sha256"] == build["transaction_object_sha256"]
        nm_text = _raw_text(
            raw_by_path, prefix + "binary.nm.txt"
        )
        object_nm = _raw_text(
            raw_by_path, prefix + "transaction.nm.txt"
        )
        readelf = _raw_text(
            raw_by_path, prefix + "binary.readelf.txt"
        )
        symbol = entry["symbols"][0]["name"]
        for raw_text in (nm_text, object_nm, readelf):
            count = sum(
                line.split()[-1] == symbol
                for line in raw_text.splitlines() if line.split()
            )
            assert count == expected_count[build_id]
        assert build["identity_defined_count"] == expected_count[build_id]
        dependencies = {item["name"]: item for item in build["dependencies"]}
        assert set(dependencies) == set(dependency_pins)
        assert all(
            dependencies[name]["pin"] == pin
            and dependencies[name]["git_head_raw"] == pin + "\n"
            and dependencies[name]["git_status_porcelain_raw"] == ""
            for name, pin in dependency_pins.items()
        )
        assert all(
            f"-DIZANAGI_{name.upper()}_SRC_HEAD={pin}"
            in build["configure_argv"]
            for name, pin in dependency_pins.items()
        )
        _assert_expected_configure_argv(
            build,
            provenance,
            macros={
                "stock": [],
                "rung-perf": [RUNG_MACRO],
                "rung-liveness": [RUNG_MACRO, REPORT_MACRO],
            }[build_id],
            trace=0,
        )
        object_nm_receipt = json.loads(
            raw_by_path[prefix + "transaction.nm.command.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        binary_nm_receipt = json.loads(
            raw_by_path[prefix + "binary.nm.command.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        readelf_receipt = json.loads(
            raw_by_path[prefix + "binary.readelf.command.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        binary_path = next(iter(binary_paths[build_id]))
        _assert_command_link(
            object_nm_receipt,
            expected_argv0=tools["nm"]["realpath"],
            argv_tail=[
                "-g", "--defined-only", transaction["object_path"],
            ],
            target_sha256=build["transaction_object_sha256"],
            stdout_raw=raw_by_path[prefix + "transaction.nm.txt"],
            stderr_raw=raw_by_path[prefix + "transaction.nm.stderr"],
            argv0_sha256=tools["nm"]["sha256"],
        )
        _assert_command_link(
            binary_nm_receipt,
            expected_argv0=tools["nm"]["realpath"],
            argv_tail=["-g", "--defined-only", binary_path],
            target_sha256=build["binary_sha256"],
            stdout_raw=raw_by_path[prefix + "binary.nm.txt"],
            stderr_raw=raw_by_path[prefix + "binary.nm.stderr"],
            argv0_sha256=tools["nm"]["sha256"],
        )
        _assert_command_link(
            readelf_receipt,
            expected_argv0=tools["readelf"]["realpath"],
            argv_tail=["-Ws", binary_path],
            target_sha256=build["binary_sha256"],
            stdout_raw=raw_by_path[prefix + "binary.readelf.txt"],
            stderr_raw=raw_by_path[prefix + "binary.readelf.stderr"],
            argv0_sha256=tools["readelf"]["sha256"],
        )
        cache = _raw_text(raw_by_path, prefix + "CMakeCache.txt")
        assert f"CMAKE_CXX_COMPILER:STRING={gxx}" in cache
        assert "CCBENCH_TRACE:STRING=0" in cache
    return (
        by_id["rung-perf"]["transaction_object_sha256"]
        == by_id["rung-liveness"]["transaction_object_sha256"]
    )


def _assert_raw_attestation(
    attestation: Mapping[str, Any],
    raw_by_path: Mapping[str, bytes],
    calibration: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> bool:
    assert attestation["contract_sha256"] == binding["contract_sha256"]
    assert attestation["calibration_sha256"] == binding["sha256"]
    checks = attestation["per_sample_solo_checks"]
    assert len(checks) == 28
    assert [item["ordinal"] for item in checks] == list(range(28))
    _, policy = _load_json_bytes(ROOT / "tools/pegasus/policy.json")
    load_threshold = policy["silo_ladder_rung1"]["solo_load1_threshold"]
    pgrep_receipts = []
    for path in sorted(raw_by_path):
        if not path.endswith(".command.json"):
            continue
        receipt = json.loads(
            raw_by_path[path], object_pairs_hook=_no_duplicate_object
        )
        if Path(receipt["argv"][0]).name == "pgrep":
            pgrep_receipts.append(receipt)
    assert len(pgrep_receipts) == 28
    for item in checks:
        ordinal = item["ordinal"]
        pgrep_raw = raw_by_path[f"solo-{ordinal:02d}.pgrep.stdout"]
        competitors = [
            line for line in _raw_text(
                raw_by_path, f"solo-{ordinal:02d}.pgrep.stdout"
            ).splitlines() if line.strip()
        ]
        load = json.loads(
            raw_by_path[f"solo-{ordinal:02d}.load.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        assert item["competing_processes"] == competitors == []
        assert item["load1"] == load["load1"]
        assert item["pgrep_returncode"] == 1
        assert pgrep_receipts[ordinal]["returncode"] == 1
        assert pgrep_receipts[ordinal]["stdout_sha256"] == _sha256(pgrep_raw)
        assert item["load_threshold"] == load_threshold
        assert item["passed"] == (load["load1"] <= load_threshold)
    parsed_probe = env_attestation.parse_probe_output(
        raw_by_path["attestation-job.json"],
    )
    assert parsed_probe.ok and parsed_probe.profile is not None
    actual = env_attestation.observed_profile_to_dict(parsed_probe.profile)
    expected = calibration["attestation_profile"]
    expected_median = statistics.median(
        expected["effective_clock"]["samples_mhz"]
    )
    actual_median = statistics.median(
        actual["effective_clock"]["samples_mhz"]
    )
    tolerance = expected["effective_clock"]["tolerance_pct"]
    legacy_clock_match = (
        abs(actual_median - expected_median)
        <= expected_median * tolerance / 100
    )
    canonical_clock_match = execution_guard.effective_clock_comparison_passes(
        {
            "samples_mhz": expected["effective_clock"]["samples_mhz"],
            "tolerance_pct": 2.0,
        },
        {"samples_mhz": actual["effective_clock"]["samples_mhz"]},
    )
    assert legacy_clock_match is True
    assert canonical_clock_match is False
    historical_derived = {
        "cpu_model_match": (
            actual["cpu"]["model_name_normalized"]
            == expected["cpu"]["model_name_normalized"]
        ),
        "effective_clock_match": (
            legacy_clock_match
            and actual["effective_clock"]["method"]
            == expected["effective_clock"]["method"]
            and actual["effective_clock"]["governor"]
            == expected["effective_clock"]["governor"]
        ),
        "cpuset_match": (
            actual["cores"]["affinity_visible"] == 48
            and actual["cores"]["physical"] == 48
            and calibration["acquisition_receipt"]["allocation"][
                "cpuset_size"
            ] == 48
        ),
        "ht_match": (
            actual["cores"]["smt_active"] is False
            and calibration["acquisition_receipt"]["allocation"][
                "ht_off"
            ] is True
        ),
        "numa_match": actual["numa"] == expected["numa"],
    }
    assert all(attestation[key] is value
               for key, value in historical_derived.items())
    return all(historical_derived.values()) and all(item["passed"] for item in checks)


def _correctness_passes(correctness: Mapping[str, Any]) -> bool:
    verifier = correctness["verifier"]
    result = verifier["results"][0]
    return (
        correctness["verifier_rc"] == 0
        and verifier["runs"] == 1
        and verifier["certified_serializable"] == 1
        and verifier["non_serializable"] == 0
        and verifier["indeterminate"] == 0
        and result["verdict"] == "serializable"
        and result["certified"] is True
        and result["stats"]["txns"] > 0
        and result["stats"]["writes"] > 0
        and result["integrity"]["clean"] is True
        and result["anomaly_count"] == 0
        and result["total_cycles"] == 0
        and len(correctness["trace_files"]) == 4
        and all(
            item["commits"] > 0
            and item["non_insert_write_witness"] is True
            for item in correctness["trace_files"]
        )
    )


def _assert_raw_correctness(
    correctness: Mapping[str, Any],
    raw_by_path: Mapping[str, bytes],
    symbol: str,
    macro: str,
) -> bool:
    trace_paths = sorted(
        path for path in raw_by_path
        if path.startswith("correctness/traces/trace_")
        and path.endswith(".log")
    )
    assert len(trace_paths) == 4
    summaries = []
    for path in trace_paths:
        name = Path(path).name
        lines = raw_by_path[path].decode("utf-8").splitlines()
        summaries.append({
            "path": name,
            "commits": sum(line.startswith("C ") for line in lines),
            "non_insert_write_witness": any(
                len(parts := line.split()) == 6
                and parts[0] == "W"
                and parts[3] in {"U", "D"}
                for line in lines
            ),
        })
    # 2026-08-12 [T-816] trace v2 専用化により、この凍結 bundle (d706650 期・v1) の trace 再検証は退役。bytes と記録済み verifier 結果は不変。
    assert summaries == correctness["trace_files"]
    build = correctness["build"]
    for path in ("binary.nm.txt", "transaction.nm.txt", "binary.readelf.txt"):
        raw = _raw_text(raw_by_path, "correctness/" + path)
        assert sum(
            line.split()[-1] == symbol
            for line in raw.splitlines() if line.split()
        ) == 1
    compile_commands = json.loads(
        raw_by_path["correctness/compile_commands.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    targets = compile_commands_for_sources(
        compile_commands,
        None,
    )
    replay = json.loads(
        raw_by_path["correctness/compile-replay.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    assert replay == {"invocations": build["compile_invocations"]}
    assert (
        len(replay["invocations"]) == len(SOURCE_FILES)
        and {item["source_rel"] for item in replay["invocations"]}
        == set(SOURCE_FILES)
    )
    transaction = next(
        item for item in replay["invocations"]
        if item["source_rel"] == "cc/silo/transaction.cc"
    )
    assert transaction["object_sha256"] == build["transaction_object_sha256"]
    object_nm = json.loads(
        raw_by_path["correctness/transaction.nm.command.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    binary_nm = json.loads(
        raw_by_path["correctness/binary.nm.command.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    readelf = json.loads(
        raw_by_path["correctness/binary.readelf.command.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    run = json.loads(
        raw_by_path["correctness/run.command.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    tools = {
        item["name"]: item
        for item in correctness["provenance"]["tools"]
    }
    binary_path = run["argv"][0]
    _assert_command_link(
        object_nm,
        expected_argv0=tools["nm"]["realpath"],
        argv_tail=["-g", "--defined-only", transaction["object_path"]],
        target_sha256=build["transaction_object_sha256"],
        stdout_raw=raw_by_path["correctness/transaction.nm.txt"],
        stderr_raw=raw_by_path["correctness/transaction.nm.stderr"],
        argv0_sha256=tools["nm"]["sha256"],
    )
    _assert_command_link(
        binary_nm,
        expected_argv0=tools["nm"]["realpath"],
        argv_tail=["-g", "--defined-only", binary_path],
        target_sha256=build["binary_sha256"],
        stdout_raw=raw_by_path["correctness/binary.nm.txt"],
        stderr_raw=raw_by_path["correctness/binary.nm.stderr"],
        argv0_sha256=tools["nm"]["sha256"],
    )
    _assert_command_link(
        readelf,
        expected_argv0=tools["readelf"]["realpath"],
        argv_tail=["-Ws", binary_path],
        target_sha256=build["binary_sha256"],
        stdout_raw=raw_by_path["correctness/binary.readelf.txt"],
        stderr_raw=raw_by_path["correctness/binary.readelf.stderr"],
        argv0_sha256=tools["readelf"]["sha256"],
    )
    _assert_command_link(
        run,
        expected_argv0=binary_path,
        argv_tail=correctness["workload"]["argv"],
        target_sha256=build["binary_sha256"],
        stdout_raw=raw_by_path["correctness/run.stdout"],
        stderr_raw=raw_by_path["correctness/run.stderr"],
        argv0_sha256=build["binary_sha256"],
    )
    gxx = next(
        item["realpath"] for item in correctness["provenance"]["tools"]
        if item["name"] == "g++"
    )
    target_argv_by_source = {}
    for target in targets:
        argv = target["argv"]
        relative = target["source_rel"]
        target_argv_by_source[relative] = argv
        assert validate_compile_argv(
            argv,
            expected_macro=macro,
            expected_compiler_realpath=gxx,
        ) == (macro,)
    assert all(
        item["argv"] == target_argv_by_source[item["source_rel"]]
        for item in replay["invocations"]
    )
    cache = _raw_text(raw_by_path, "correctness/CMakeCache.txt")
    assert f"CMAKE_CXX_COMPILER:STRING={gxx}" in cache
    assert "CCBENCH_TRACE:STRING=1" in cache
    _, policy = _load_json_bytes(ROOT / "tools/pegasus/policy.json")
    pins = policy["silo_ladder_rung1"]["dependency_pins"]
    dependencies = {item["name"]: item for item in build["dependencies"]}
    assert set(dependencies) == set(pins)
    assert all(
        f"-DIZANAGI_{name.upper()}_SRC_HEAD={pin}"
        in build["configure_argv"]
        and dependencies[name]["pin"] == pin
        and dependencies[name]["git_head_raw"] == pin + "\n"
        and dependencies[name]["git_status_porcelain_raw"] == ""
        for name, pin in pins.items()
    )
    _assert_expected_configure_argv(
        build,
        correctness["provenance"],
        macros=[RUNG_MACRO],
        trace=1,
    )
    return _correctness_passes(correctness)


def test_silo_ladder_rung1_commit_witness_matches_committed_raw_data():
    _, evidence = _load_json_bytes(EVIDENCE)
    raw_root = ROOT / evidence["raw_bundle"]["root"] / "correctness"
    verifier = json.loads(
        (raw_root / "verifier.json").read_text(encoding="utf-8"),
        object_pairs_hook=_no_duplicate_object,
    )
    _validate_correctness_commit_witness(
        verifier,
        (raw_root / "run.stdout").read_text(encoding="utf-8"),
    )
    assert verifier["results"][0]["stats"]["txns"] == 480595


def test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head():
    """成果物欠落を含む全 binding drift を赤にし、all_pass を raw から再導出する。"""
    evidence_raw, evidence = _load_json_bytes(EVIDENCE)
    assert evidence_raw, "committed evidence must not be empty"
    _, ledger = _load_json_bytes(LEDGER)
    entry = next(
        item for item in ledger["entries"]
        if item["id"] == "silo_ladder_rung1"
    )
    binding = evidence["binding"]
    raw_probe = (
        ROOT
        / "output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/"
          "raw-bundle-attempt-1/attempts/1/attestation-job.json"
    )
    assert (
        _sha256(evidence_raw),
        _sha256(raw_probe.read_bytes()),
        binding["calibration"]["sha256"],
        binding["driver"]["sha256"],
    ) == HISTORICAL_SILO_EVIDENCE_IDENTITY
    assert evidence["limitations"] == {
        "raw_object_binary_bytes_retained": False,
        "nqsv_scheduler_exit_status": "unavailable",
        "third_party_rederivation": "sha256-chain-consistency-only",
    }

    patch_path = ROOT / entry["path"]
    patch_raw = patch_path.read_bytes()
    patch_sha = _sha256(patch_raw)
    assert binding["patch"]["path"] == entry["path"]
    assert patch_sha == binding["patch"]["sha256"] == entry["patch_sha256"]
    assert binding["ledger"]["path"] == "patches/ledger.json"
    assert binding["ledger"]["sha256"] == HISTORICAL_LEDGER_SHA256
    assert binding["ledger"]["sha256"] != _sha256(LEDGER.read_bytes())
    expected_bound_paths = {
        "driver": "orchestrator/campaign/silo_ladder_rung1.py",
        "pbs_job": "tools/pegasus/silo_ladder_rung1.sh",
        "submitter": "tools/pegasus/submit_silo_ladder_rung1.sh",
        "verifier_module": "orchestrator/verifier/report.py",
        "policy": "tools/pegasus/policy.json",
    }
    historical_sha256_by_key = {
        "driver": HISTORICAL_SILO_EVIDENCE_IDENTITY[3],
        "pbs_job": EXPECTED_HISTORICAL_PBS_JOB_SHA256,
        "submitter": EXPECTED_HISTORICAL_SUBMITTER_SHA256,
        "verifier_module": EXPECTED_HISTORICAL_VERIFIER_MODULE_SHA256,
        "policy": EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256,
    }
    for key, relative in expected_bound_paths.items():
        assert binding[key]["path"] == relative
        current_sha = _sha256((ROOT / relative).read_bytes())
        if key == "policy":
            assert current_sha == EXPECTED_CURRENT_PEGASUS_POLICY_SHA256, (
                "intentional policy update requires refreshing the single "
                "shared EXPECTED_CURRENT_PEGASUS_POLICY_SHA256 golden in "
                "orchestrator/tests/pegasus_policy_expected_goldens.py: "
                f"sha256({relative})={current_sha}"
            )
        if key == "pbs_job":
            assert current_sha == EXPECTED_CURRENT_PBS_JOB_SHA256, (
                "intentional pbs_job update requires refreshing the "
                "EXPECTED_CURRENT_PBS_JOB_SHA256 golden in "
                "orchestrator/tests/test_silo_ladder_rung1_evidence.py: "
                f"sha256({relative})={current_sha}"
            )
        if key == "submitter":
            assert current_sha == EXPECTED_CURRENT_SUBMITTER_SHA256, (
                "intentional submitter update requires refreshing the "
                "EXPECTED_CURRENT_SUBMITTER_SHA256 golden in "
                "orchestrator/tests/test_silo_ladder_rung1_evidence.py: "
                f"sha256({relative})={current_sha}"
            )
        if key in historical_sha256_by_key:
            assert binding[key]["sha256"] == historical_sha256_by_key[key]
            assert binding[key]["sha256"] != current_sha
        else:
            assert binding[key]["sha256"] == current_sha
    # 歴史 binding は保持し、現行 runtime binding とは一致させない。
    assert binding["runtime_modules"] != runtime_modules_binding(ROOT)

    pin = binding["ccbench_pin_full"]
    assert isinstance(pin, str) and HEX40.fullmatch(pin)
    assert pin == HISTORICAL_CCBENCH_PIN_FULL
    assert PIN == entry["base_commit"]
    assert pin != PIN
    # 意図的に `git rev-parse HEAD` は参照しない。content/pin receipt のみへ束縛する。

    activation = evidence["activation_contract"]
    assert set(activation) == {"macro", "symbols"}
    assert activation["macro"] == entry["macro"]
    assert activation["symbols"] == [item["name"] for item in entry["symbols"]]

    registered = env_contract.lookup("pegasus")
    calibration_binding = binding["calibration"]
    assert calibration_binding["path"] == registered.calibration_ref.path
    calibration_path = ROOT / calibration_binding["path"]
    calibration_raw, calibration = _load_json_bytes(calibration_path)
    assert (
        _sha256(calibration_raw)
        == calibration_binding["sha256"]
        == registered.calibration_ref.sha256
    )
    assert calibration_binding["contract_sha256"] == registered.contract_sha256
    assert calibration_binding["quality_status"] == calibration["quality"]["status"] == "accepted"
    assert calibration_binding["records"] == calibration["saturation"]["records"] == 1_000_000
    assert calibration_binding["threads"] == calibration["threads"] == 48
    _, policy = _load_json_bytes(ROOT / "tools/pegasus/policy.json")
    dependency_pins = policy["silo_ladder_rung1"]["dependency_pins"]
    registered_build = calibration["acquisition_receipt"]["ccbench"]["build_argv"]
    assert {
        name: next(
            token.split("=", 1)[1] for token in registered_build
            if token.startswith(f"-DIZANAGI_{name.upper()}_SRC_HEAD=")
        )
        for name in ("gflags", "glog")
    } == dependency_pins

    gap = evidence["gap_leg"]
    assert gap["status"] == "complete"
    current_attempt = gap["attempts"][-1]["attempt"]
    active_prefix = f"attempts/{current_attempt}/"
    raw_by_path, raw_documents = _raw_documents(evidence)
    active_raw = {
        path[len(active_prefix):]: raw
        for path, raw in raw_by_path.items()
        if path.startswith(active_prefix)
    }
    assert validate_nqsv_accounting_epilogue(
        active_raw["pbs-accounting.txt"].decode("utf-8", errors="replace"),
        gap["attempts"][-1]["job_id"],
    )
    validation_raw = {
        **{
            path: raw for path, raw in raw_by_path.items()
            if path.startswith("correctness/")
        },
        **active_raw,
    }
    _assert_command_receipts(validation_raw)
    raw_schedule = _unique_projected(
        raw_documents, _schedule_from, "schedule receipt"
    )
    raw_gap = _unique_projected(raw_documents, _gap_from, "gap summary")
    raw_verifier = _unique_projected(
        raw_documents, _verifier_from, "verifier result"
    )
    raw_provenance = _unique_projected(
        raw_documents, _provenance_from, "provenance receipt"
    )

    assert gap["schedule_receipt"] == raw_schedule
    assert gap["performance_runs"] == raw_gap["performance_runs"]
    assert gap["liveness_runs"] == raw_gap["liveness_runs"]
    assert gap["builds"] == raw_gap["builds"]
    assert gap["attestation"] == raw_gap["attestation"]
    verifier_projection = {
        key: evidence["correctness_leg"]["verifier"][key]
        for key in raw_verifier
    }
    assert verifier_projection == raw_verifier
    assert evidence["provenance"] == raw_provenance
    # third-party head の pin 照合は binding ではなく provenance 側へ一本化する。
    _assert_third_party_provenance(evidence["provenance"])
    _assert_third_party_provenance(
        evidence["correctness_leg"]["provenance"]
    )

    _assert_balanced_schedule(raw_schedule)
    expected_argv = _registered_workloads(calibration)
    _assert_workloads_and_runs(
        raw_gap, raw_schedule, expected_argv, validation_raw,
    )
    _assert_compiler_contract(evidence["provenance"], raw_provenance, calibration)
    _assert_compiler_contract(
        evidence["correctness_leg"]["provenance"],
        raw_provenance,
        calibration,
    )
    submit = json.loads(
        active_raw["submit-receipt.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    submit_bindings = dict(submit["bindings"])
    submit_bindings.pop("third_party_heads", None)
    assert submit_bindings == {
        "job_script_sha256": binding["pbs_job"]["sha256"],
        "driver_sha256": binding["driver"]["sha256"],
        "patch_sha256": binding["patch"]["sha256"],
        "ledger_sha256": binding["ledger"]["sha256"],
        "correctness_sha256": _sha256(
            json.dumps(
                evidence["correctness_leg"],
                ensure_ascii=False, sort_keys=True, indent=2,
            ).encode("utf-8") + b"\n"
        ),
        "schedule_sha256": _sha256(
            json.dumps(
                raw_schedule,
                ensure_ascii=False, sort_keys=True, indent=2,
            ).encode("utf-8") + b"\n"
        ),
        "submitter_sha256": binding["submitter"]["sha256"],
        "verifier_module_sha256": binding["verifier_module"]["sha256"],
        "policy_sha256": binding["policy"]["sha256"],
        "runtime_modules_sha256": _sha256(json.dumps(
            binding["runtime_modules"],
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")),
    }
    campaign_ref = submit["campaign_root_receipt"]
    assert _sha256(raw_by_path["campaign-identity-receipt.json"]) == (
        campaign_ref["sha256"]
    )
    campaign_identity = json.loads(
        raw_by_path["campaign-identity-receipt.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    campaign_root = json.loads(
        raw_by_path["campaign-root-receipt.json"],
        object_pairs_hook=_no_duplicate_object,
    )
    assert campaign_root["campaign_id"] == submit["campaign_id"]
    assert campaign_identity["campaign_id"] == submit["campaign_id"]
    assert campaign_root["schedule_receipt"] == raw_schedule
    assert campaign_root["bindings"]["runtime_modules_sha256"] == (
        submit_bindings["runtime_modules_sha256"]
    )
    assert campaign_root["bindings"]["expected_patched_source_sha256"] == (
        raw_provenance["source_witness"]["expected_patched_source_sha256"]
    )
    assert evidence["correctness_leg"]["provenance"][
        "expected_patched_source_sha256"
    ] == raw_provenance["source_witness"]["expected_patched_source_sha256"]
    assert evidence["correctness_leg"]["provenance"][
        "observed_patched_source_sha256"
    ] == raw_provenance["source_witness"]["expected_patched_source_sha256"]
    assert campaign_root["bindings"]["expected_patched_source_sha256"] == (
        EXPECTED_HISTORICAL_PATCHED_SOURCE_SHA256
    )
    assert EXPECTED_HISTORICAL_PATCHED_SOURCE_SHA256 != (
        _recompute_patched_source_hashes(entry)
    )

    activation_passes = _assert_raw_builds(
        raw_gap, validation_raw, entry, raw_provenance,
    )
    attestation = raw_gap["attestation"]
    attestation_passes = _assert_raw_attestation(
        attestation, validation_raw, calibration, calibration_binding,
    )
    assert len(raw_gap["attempts"]) in (1, 2)
    assert [item["attempt"] for item in raw_gap["attempts"]] in ([1], [1, 2])
    assert raw_gap["status"] == "complete"
    assert raw_gap["attempts"][-1]["failure_class"] is None
    assert raw_gap["attempts"][-1]["reason_code"] is None
    assert all(
        HEX64.fullmatch(item["attempt_receipt_sha256"])
        for item in raw_gap["attempts"]
    )
    assert campaign_root["attempts"] == [
        json.loads(
            raw_by_path[f"campaign-attempt-root-receipts/{item['attempt']}.json"],
            object_pairs_hook=_no_duplicate_object,
        )
        for item in raw_gap["attempts"]
    ]
    for item in raw_gap["attempts"]:
        assert item["raw_root"] == f"attempts/{item['attempt']}"
        assert f"attempts/{item['attempt']}/raw-manifest.json" in raw_by_path
        _assert_attempt_subtree_sealed(raw_by_path, item)
        attempt_submit_raw = raw_by_path[
            f"attempts/{item['attempt']}/submit-receipt.json"
        ]
        attempt_submit = json.loads(
            attempt_submit_raw, object_pairs_hook=_no_duplicate_object,
        )
        assert _sha256(attempt_submit_raw) == item["submit_receipt_sha256"]
        assert attempt_submit["nonce"] == item["nonce"]
        assert attempt_submit["campaign_id"] == campaign_root["campaign_id"]
        assert _normalize_job_id(
            attempt_submit["qsub"]["request_id"]
        ) == _normalize_job_id(item["job_id"])
        if item["failure_class"] == "infra":
            wrapper = json.loads(
                raw_by_path[
                    f"attempts/{item['attempt']}/wrapper-failure.json"
                ],
                object_pairs_hook=_no_duplicate_object,
            )
            assert wrapper["failure_class"] == "infra"
            assert wrapper["reason_code"] == item["reason_code"]
            assert wrapper["pbs_jobid"] == item["job_id"]
    derived = {
        "correctness": _assert_raw_correctness(
            evidence["correctness_leg"], raw_by_path,
            entry["symbols"][0]["name"],
            entry["macro"],
        ),
        "schedule": True,
        "per_worker_ever_committed": True,
        "bounded_completion": True,
        "performance_direction": True,
        "activation": activation_passes,
        "attestation": attestation_passes,
        "raw_recomputed": True,
    }
    assert set(evidence["checks"]) == EXPECTED_CHECK_KEYS
    assert evidence["checks"] == derived
    assert evidence["all_pass"] == all(derived.values())
    assert evidence["all_pass"] is True


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
