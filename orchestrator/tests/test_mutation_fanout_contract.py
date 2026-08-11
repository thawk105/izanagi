"""Mutation fan-out の分割・併合 proof chain を純関数 fixture で検査する。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOL = _REPO / "tools" / "mutation_fanout_contract.py"
_SPEC = importlib.util.spec_from_file_location("mutation_fanout_contract_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
MF = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MF
_SPEC.loader.exec_module(MF)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _artifact(
    original_root: Path,
    relocated_root: Path,
    *,
    request_id: str,
    rc: int,
    output: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    submission = original_root / f"request-{request_id}"
    receipt = submission / "receipt.json"
    stdout = submission / f"izdw-fixture.o{request_id}"
    relocated_receipt = relocated_root / receipt.relative_to(original_root)
    relocated_stdout = relocated_root / stdout.relative_to(original_root)
    relocated_receipt.parent.mkdir(parents=True, exist_ok=True)
    relocated_receipt.write_text(
        json.dumps({"request_id": request_id, "outcome": {"rc": rc}}) + "\n",
        encoding="utf-8",
    )
    relocated_stdout.write_text(output, encoding="utf-8")
    artifact = {
        "runner_mode": "dispatch",
        "receipt_path": str(receipt),
        "job_stdout_path": str(stdout),
        "stdout": output,
        "stdout_sha256": _sha(output.encode()),
    }
    request = {
        "request_id": request_id,
        "submission_dir": str(submission),
        "receipt_path": str(receipt),
        "job_stdout_path": str(stdout),
        "outcome_rc": rc,
    }
    return artifact, request


def _mutation(mutation_id: str, *, hang_risk: bool = False) -> dict[str, Any]:
    return {
        "id": mutation_id,
        "category": "negative",
        "replacements": [
            {"file": "target.py", "old": f"{mutation_id} = 0", "new": f"{mutation_id} = 1"}
        ],
        "expected_nodes": [f"tests/test_gate.py::test_{mutation_id.lower()}"],
        "expected_status": "KILLED",
        "hang_risk": hang_risk,
    }


def _parent_bytes() -> bytes:
    return json.dumps(
        {
            "schema": MF.SPEC_SCHEMA,
            "estimated_run_seconds": 12.5,
            "timeout_seconds": 120,
            "hang_timeout_seconds": 360,
            "mutations": [
                _mutation("M1", hang_risk=True),
                _mutation("M2"),
                _mutation("M3", hang_risk=True),
                _mutation("M4"),
            ],
        },
        ensure_ascii=False,
        indent=1,
    ).encode() + b"\n"


def _registration(mutation: dict[str, Any]) -> dict[str, Any]:
    return {
        "anchor_counts": {"0": 1},
        "injection_diff_sha256": "a" * 64,
        "expected_nodes": mutation["expected_nodes"],
        "expected_status": mutation["expected_status"],
        "replacements": mutation["replacements"],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_group(tmp_path: Path) -> dict[str, Any]:
    parent_path = tmp_path / "parent.json"
    parent = _parent_bytes()
    parent_path.write_bytes(parent)
    parent_sha = _sha(parent)
    assignment, shard_payloads = MF.derive_split(
        parent, expected_parent_sha256=parent_sha, shard_count=2
    )
    assignment_path = tmp_path / "assignment.json"
    assignment_path.write_bytes(MF.canonical_json_bytes(assignment))
    assignment_sha = _sha(assignment_path.read_bytes())
    group_shards: list[dict[str, Any]] = []
    ledgers: list[Path] = []
    wrappers: list[Path] = []
    attempts_paths: list[Path] = []
    shared_checkout = tmp_path / "reused-scratch" / ".izanagi-mutation-worktree" / "repo"
    shared_scratch = shared_checkout.parents[1]
    shared_lock = tmp_path / "shared.lock"
    repo_head = "b" * 40
    wrapper_sha = "c" * 64
    all_collected = [f"tests/test_gate.py::test_m{index}" for index in range(1, 5)]

    for index, (assignment_shard, shard_payload) in enumerate(
        zip(assignment["shards"], shard_payloads, strict=True)
    ):
        shard_id = assignment_shard["shard_id"]
        spec_path = tmp_path / assignment_shard["relative_spec_path"]
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_bytes(shard_payload)
        spec = json.loads(shard_payload)
        ledger_path = tmp_path / f"{shard_id}.ledger.json"
        wrapper_path = Path(f"{ledger_path}.wrapper-receipt.json")
        attempt_path = tmp_path / f"{shard_id}.attempts.json"
        original_root = shared_checkout / "output" / "pegasus-dispatch"
        relocated_root = Path(f"{ledger_path}.dispatch-evidence")
        runner_identity = {
            "runner_mode": "dispatch",
            "command": ["python3", "tools/run_tests.py", "tests", "-rf"],
            "entrypoint_kind": "izanagi-run-tests",
            "executable_path": "/usr/bin/python3",
            "executable_sha256": "d" * 64,
            "entrypoint_path": str(shared_checkout / "tools" / "run_tests.py"),
            "entrypoint_sha256": "e" * 64,
            "pytest_distribution_sha256": "f" * 64,
            "dispatch_entrypoint_path": str(
                shared_checkout / "tools" / "pegasus" / "dispatch_compute.py"
            ),
            "dispatch_entrypoint_sha256": "1" * 64,
            "dispatch_head_blob_sha256": "1" * 64,
            "repo_path": "tools/run_tests.py",
            "head_blob_sha256": "e" * 64,
            "repo_tree": "2" * 40,
        }
        tool_identity = {
            "path": str(shared_checkout / "tools" / "mutation_harness.py"),
            "sha256": "3" * 64,
            "repo_path": "tools/mutation_harness.py",
            "head_blob_sha256": "3" * 64,
        }
        runner_sha = MF._compact_sha256(runner_identity)
        tool_sha = MF._compact_sha256(tool_identity)
        registration = {
            mutation["id"]: _registration(mutation) for mutation in spec["mutations"]
        }
        collection_artifact, collection_request = _artifact(
            original_root,
            relocated_root,
            request_id=f"{index}01.server",
            rc=0,
            output="\n".join(all_collected) + "\n",
        )
        collection = {
            "status": "PASSED",
            "rc": 0,
            "collected_nodes": all_collected,
            "duration_s": 1.0 + index,
            "artifact": collection_artifact,
            "repo_head": repo_head,
            "spec_sha256": _sha(shard_payload),
            "runner_sha256": runner_sha,
            "tool_sha256": tool_sha,
        }
        baseline_artifact, baseline_request = _artifact(
            original_root,
            relocated_root,
            request_id=f"{index}02.server",
            rc=0,
            output="1 passed\n",
        )
        baseline = {
            "status": "PASSED",
            "rc": 0,
            "failed_nodes": [],
            "timed_out": False,
            "duration_s": 2.0,
            "artifact_error": None,
            "artifact": baseline_artifact,
            "test_output_sha256": _sha(b"1 passed\n"),
            "test_output_tail": [],
            "repo_head": repo_head,
            "spec_sha256": _sha(shard_payload),
            "registration_sha256": MF._compact_sha256(registration),
            "runner_sha256": runner_sha,
            "tool_sha256": tool_sha,
            "collection_sha256": MF._compact_sha256(collection),
        }
        records: list[dict[str, Any]] = []
        requests = [("collection", None, 0, collection_request), ("baseline", None, 0, baseline_request)]
        for mutation_index, mutation in enumerate(spec["mutations"]):
            output = f"FAILED {mutation['expected_nodes'][0]} - AssertionError\n"
            artifact, request = _artifact(
                original_root,
                relocated_root,
                request_id=f"{index}{mutation_index + 3:02d}.server",
                rc=1,
                output=output,
            )
            mutation_registration = registration[mutation["id"]]
            records.append(
                {
                    **mutation,
                    "status": "KILLED",
                    "matches_expectation": True,
                    "rc": 1,
                    "failed_nodes": mutation["expected_nodes"],
                    "timed_out": False,
                    "duration_s": 3.0,
                    "artifact_error": None,
                    "artifact": artifact,
                    "anchor_counts": {"0": 1},
                    "injection_diff_sha256": "a" * 64,
                    "test_output_sha256": _sha(output.encode()),
                    "test_output_tail": [],
                    "repo_head": repo_head,
                    "spec_sha256": _sha(shard_payload),
                    "registration_sha256": MF._compact_sha256(mutation_registration),
                    "runner_sha256": runner_sha,
                    "tool_sha256": tool_sha,
                    "collection_sha256": MF._compact_sha256(collection),
                }
            )
            requests.append(("mutation", mutation["id"], 1, request))
        summary = {
            "registered": len(records),
            "recorded": len(records),
            "completed": len(records),
            "matching": len(records),
            "KILLED": len(records),
            "SURVIVED": 0,
            "MISMATCH": 0,
            "TIMEOUT": 0,
            "PARSE_ERROR": 0,
        }
        ledger = {
            "schema": MF.LEDGER_SCHEMA,
            "date": "2026-08-11T00:00:00+00:00",
            "updated_at": "2026-08-11T00:00:01+00:00",
            "repo_head": repo_head,
            "spec_sha256": _sha(shard_payload),
            "runner_sha256": runner_sha,
            "runner_identity": runner_identity,
            "tool_sha256": tool_sha,
            "tool_identity": tool_identity,
            "procedure": {
                "runner_mode": "dispatch",
                "test_command": runner_identity["command"],
                "timeout_seconds": spec["timeout_seconds"],
                "hang_timeout_seconds": spec["hang_timeout_seconds"],
                "source_policy": "fixed repo_head blob plus startup/read-back equality",
                "restore_policy": "write fixed repo_head text then exact read_text equality",
                "node_policy": "trusted pytest collection plus parameter-exact failed-node set",
                "registration_preflight": registration,
                "registration_sha256": MF._compact_sha256(registration),
                "collection": collection,
            },
            "baseline": baseline,
            "summary": summary,
            "mutations": records,
            "nonterminal_history": [],
        }
        _write_json(ledger_path, ledger)
        wrapper = {
            "schema": MF.WRAPPER_SCHEMA,
            "wrapper_sha256": wrapper_sha,
            "resolved_commit": repo_head,
            "container_path": str(shared_checkout.parent),
            "scratch_root": str(shared_scratch),
            "lock_path": str(shared_lock),
            "child_rc": 0,
            "dispatch_evidence": {
                "original_path": str(original_root),
                "relocated_path": str(relocated_root),
                "rehydrated": False,
                "relocated": True,
            },
            "shared_snapshot_matches": True,
            "terminal_ledger": True,
            "teardown_attempted": True,
            "teardown_completed": True,
            "container_preserved": False,
            "failure": None,
        }
        _write_json(wrapper_path, wrapper)
        attempt_entries = []
        for ordinal, (phase, mutation_id, rc, request) in enumerate(requests, start=1):
            attempt_entries.append(
                {
                    "run_attempt_ordinal": ordinal,
                    "wrapper_attempt_ordinal": 1,
                    "phase": phase,
                    "mutation_id": mutation_id,
                    "state": "finished",
                    "started_at": f"2026-08-11T00:00:{ordinal:02d}+00:00",
                    "finished_at": f"2026-08-11T00:01:{ordinal:02d}+00:00",
                    "rc": rc,
                    "timed_out": False,
                    "artifact_error": None,
                    "console_sha256": "4" * 64,
                    "request": request,
                }
            )
        _write_json(
            attempt_path,
            {
                "schema": MF.ATTEMPT_SCHEMA,
                "repo_head": repo_head,
                "spec_sha256": _sha(shard_payload),
                "runner_sha256": runner_sha,
                "tool_sha256": tool_sha,
                "expected_initial_requests": len(records) + 2,
                "attempts": attempt_entries,
            },
        )
        group_shards.append(
            {
                "index": index,
                "shard_id": shard_id,
                "spec_path": str(spec_path),
                "ledger_path": str(ledger_path),
                "wrapper_receipt_path": str(wrapper_path),
                "attempt_path": str(attempt_path),
                "wrapper_attempt_ordinal": 1,
                "wrapper_rc": 0,
                "expected_paths": {
                    "scratch_root": str(shared_scratch),
                    "container_path": str(shared_checkout.parent),
                    "lock_path": str(shared_lock),
                    "runner_entrypoint_path": runner_identity["entrypoint_path"],
                    "dispatch_entrypoint_path": runner_identity["dispatch_entrypoint_path"],
                    "tool_path": tool_identity["path"],
                },
            }
        )
        ledgers.append(ledger_path)
        wrappers.append(wrapper_path)
        attempts_paths.append(attempt_path)

    group_path = tmp_path / "group.json"
    _write_json(
        group_path,
        {
            "schema": MF.GROUP_SCHEMA,
            "parent_spec_sha256": parent_sha,
            "assignment_sha256": assignment_sha,
            "shards": group_shards,
        },
    )
    return {
        "parent": parent_path,
        "parent_sha": parent_sha,
        "assignment": assignment_path,
        "group": group_path,
        "ledgers": ledgers,
        "wrappers": wrappers,
        "attempts": attempts_paths,
        "out": tmp_path / "merge-index.json",
    }


def _merge(paths: dict[str, Any]) -> dict[str, Any]:
    return MF.merge_group(
        paths["parent"],
        expected_parent_sha256=paths["parent_sha"],
        assignment_path=paths["assignment"],
        group_manifest_path=paths["group"],
        output_path=paths["out"],
    )


def _mutate_json(path: Path, update: Callable[[dict[str, Any]], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    update(value)
    _write_json(path, value)


def test_serializer_and_split_are_deterministic_and_preserve_parent_values() -> None:
    parent = _parent_bytes()
    parent_sha = _sha(parent)

    first_assignment, first_shards = MF.derive_split(
        parent, expected_parent_sha256=parent_sha, shard_count=2
    )
    second_assignment, second_shards = MF.derive_split(
        parent, expected_parent_sha256=parent_sha, shard_count=2
    )

    pinned = MF.canonical_json_bytes({"z": "雪", "a": 1})
    assert pinned == (
        b'{\n  "a": 1,\n  "z": "\xe9\x9b\xaa"\n}\n'
    )
    assert _sha(pinned) == "82d8e64acb41647ab5cae14c985971cd8d223c818cb8e2f073621f0699339095"
    assert first_assignment == second_assignment
    assert first_shards == second_shards
    assert [entry["mutation_ids"] for entry in first_assignment["shards"]] == [
        ["M1", "M2"],
        ["M3", "M4"],
    ]
    for payload in first_shards:
        shard = json.loads(payload)
        assert shard["estimated_run_seconds"] == 12.5
        assert shard["timeout_seconds"] == 120
        assert shard["hang_timeout_seconds"] == 360
    parent_document = json.loads(parent)
    derived_mutations = {
        mutation["id"]: mutation
        for payload in first_shards
        for mutation in json.loads(payload)["mutations"]
    }
    assert derived_mutations == {
        mutation["id"]: mutation for mutation in parent_document["mutations"]
    }
    assert first_assignment["serializer"] == MF.SERIALIZER


def test_split_requires_explicit_valid_n_and_rejects_existing_outputs(tmp_path: Path) -> None:
    parent = tmp_path / "parent.json"
    parent.write_bytes(_parent_bytes())
    parent_sha = _sha(parent.read_bytes())
    with pytest.raises(SystemExit):
        MF._parser().parse_args(
            [
                "split",
                "--parent-spec",
                str(parent),
                "--expected-parent-sha256",
                parent_sha,
                "--group-root",
                str(tmp_path / "missing-n"),
            ]
        )
    with pytest.raises(MF.FanoutContractError, match="mutation 数を超える"):
        MF.derive_split(parent.read_bytes(), expected_parent_sha256=parent_sha, shard_count=5)

    assignment = MF.write_split(
        parent, expected_parent_sha256=parent_sha, shard_count=2, group_root=tmp_path / "group"
    )
    assert assignment["shard_count"] == 2
    with pytest.raises(MF.FanoutContractError, match="既に存在"):
        MF.write_split(
            parent, expected_parent_sha256=parent_sha, shard_count=2, group_root=tmp_path / "group"
        )


def test_merge_accepts_manifest_exact_paths_even_when_shards_reuse_same_paths(
    tmp_path: Path,
) -> None:
    paths = _build_group(tmp_path)

    index = _merge(paths)

    assert index["registered"] == index["recorded"] == 4
    assert index["matches_expectation"] is True
    assert index["result_rc"] == 0
    assert len(index["requests"]) == 8
    assert all("ledger" not in shard for shard in index["shards"])
    saved = json.loads(paths["out"].read_text(encoding="utf-8"))
    assert saved == index
    with pytest.raises(MF.FanoutContractError, match="既に存在"):
        _merge(paths)


@pytest.mark.parametrize(
    ("target", "update", "message"),
    [
        (
            "ledgers",
            lambda value: value.__setitem__("spec_sha256", "0" * 64),
            "spec hash",
        ),
        (
            "ledgers",
            lambda value: value["summary"].__setitem__("recorded", 1),
            "registered != recorded",
        ),
        (
            "ledgers",
            lambda value: value["procedure"]["collection"]["collected_nodes"].append("extra::node"),
            "collected_nodes",
        ),
        (
            "wrappers",
            lambda value: value.__setitem__("terminal_ledger", False),
            "terminal_ledger",
        ),
        (
            "ledgers",
            lambda value: (
                value["mutations"][0].__setitem__("status", "TIMEOUT"),
                value["mutations"][0].__setitem__("matches_expectation", False),
                value["summary"].__setitem__("KILLED", value["summary"]["KILLED"] - 1),
                value["summary"].__setitem__("TIMEOUT", 1),
                value["summary"].__setitem__("matching", value["summary"]["matching"] - 1),
            ),
            "TIMEOUT record",
        ),
        (
            "ledgers",
            lambda value: value["runner_identity"].__setitem__("new_identity", "unknown"),
            "unknown=.*new_identity",
        ),
        (
            "ledgers",
            lambda value: value["procedure"].__setitem__("source_policy", "drift"),
            "内容 identity",
        ),
        (
            "attempts",
            lambda value: value["attempts"].pop(),
            "attempt 数",
        ),
    ],
)
def test_merge_rejects_each_fail_closed_condition(
    tmp_path: Path,
    target: str,
    update: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    paths = _build_group(tmp_path)
    path = paths[target][1]
    _mutate_json(path, update)

    with pytest.raises(MF.FanoutContractError, match=message):
        _merge(paths)
    assert not paths["out"].exists()


def test_merge_compares_paths_to_manifest_not_pairwise_difference(tmp_path: Path) -> None:
    paths = _build_group(tmp_path)
    group = json.loads(paths["group"].read_text(encoding="utf-8"))
    group["shards"][1]["expected_paths"]["tool_path"] += ".wrong"
    _write_json(paths["group"], group)

    with pytest.raises(MF.FanoutContractError, match="manifest path"):
        _merge(paths)


def test_merge_derives_global_result_from_records_and_cross_checks_rc(tmp_path: Path) -> None:
    paths = _build_group(tmp_path)
    ledger_path = paths["ledgers"][0]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["mutations"][0]["status"] = "SURVIVED"
    ledger["mutations"][0]["matches_expectation"] = False
    ledger["summary"]["KILLED"] -= 1
    ledger["summary"]["SURVIVED"] += 1
    ledger["summary"]["matching"] -= 1
    _write_json(ledger_path, ledger)

    with pytest.raises(MF.FanoutContractError, match="rc と ledger matches_expectation"):
        _merge(paths)


@pytest.mark.parametrize(
    "shard_ids",
    [["M1", "M2", "M3"], ["M1", "M2", "M3", "M3"], ["M1", "M2", "M3", "UNKNOWN"]],
)
def test_parent_id_bijection_rejects_missing_duplicate_and_unknown(shard_ids: list[str]) -> None:
    with pytest.raises(MF.FanoutContractError, match="直和"):
        MF._require_id_bijection(["M1", "M2", "M3", "M4"], shard_ids)
