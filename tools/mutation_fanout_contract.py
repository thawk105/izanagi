#!/usr/bin/env python3
"""Mutation fan-out の決定的分割と fail-closed 併合契約。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any


SPEC_SCHEMA = "izanagi-dev-wave-mutation-spec/v1"
LEDGER_SCHEMA = "izanagi-dev-wave-mutation/v4"
WRAPPER_SCHEMA = "izanagi-mutation-worktree-wrapper/v1"
ASSIGNMENT_SCHEMA = "izanagi-dev-wave-mutation-fanout-assignment/v1"
GROUP_SCHEMA = "izanagi-dev-wave-mutation-fanout-group/v1"
ATTEMPT_SCHEMA = "izanagi-dev-wave-mutation-attempts/v1"
MERGE_SCHEMA = "izanagi-dev-wave-mutation-fanout-index/v1"
ALLOCATION_RULE = "hang-spread-count-balance-v1"
SERIALIZER = "json.dumps(ensure_ascii=False,sort_keys=True,indent=2)+LF"

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_MERGEABLE_STATUSES = frozenset({"KILLED", "SURVIVED", "MISMATCH"})

_SPEC_FIELDS = {
    "schema", "estimated_run_seconds", "timeout_seconds",
    "hang_timeout_seconds", "mutations",
}
_MUTATION_SPEC_FIELDS = {
    "id", "category", "replacements", "expected_nodes", "expected_status",
    "hang_risk",
}
_REPLACEMENT_FIELDS = {"file", "old", "new"}
_ASSIGNMENT_FIELDS = {
    "schema", "parent_spec_sha256", "parent_spec_size", "parent_mutation_ids",
    "shard_count", "allocation_rule", "serializer", "shards",
}
_ASSIGNMENT_SHARD_FIELDS = {
    "index", "shard_id", "mutation_ids", "hang_risk_ids",
    "relative_spec_path", "shard_spec_sha256", "shard_spec_size",
}
_GROUP_FIELDS = {"schema", "parent_spec_sha256", "assignment_sha256", "shards"}
_GROUP_SHARD_FIELDS = {
    "index", "shard_id", "spec_path", "ledger_path", "wrapper_receipt_path",
    "attempt_path", "wrapper_attempt_ordinal", "wrapper_rc", "expected_paths",
}
_EXPECTED_PATH_FIELDS = {
    "scratch_root", "container_path", "lock_path", "runner_entrypoint_path",
    "dispatch_entrypoint_path", "tool_path",
}
_WRAPPER_FIELDS = {
    "schema", "wrapper_sha256", "resolved_commit", "container_path",
    "scratch_root", "lock_path", "child_rc", "dispatch_evidence",
    "shared_snapshot_matches", "terminal_ledger", "teardown_attempted",
    "teardown_completed", "container_preserved", "failure",
}
_EVIDENCE_FIELDS = {"original_path", "relocated_path", "rehydrated", "relocated"}
_LEDGER_FIELDS = {
    "schema", "date", "updated_at", "repo_head", "spec_sha256",
    "runner_sha256", "runner_identity", "tool_sha256", "tool_identity",
    "procedure", "baseline", "summary", "mutations", "nonterminal_history",
}
_RUNNER_FIELDS = {
    "runner_mode", "command", "entrypoint_kind", "executable_path",
    "executable_sha256", "entrypoint_path", "entrypoint_sha256",
    "pytest_distribution_sha256", "dispatch_entrypoint_path",
    "dispatch_entrypoint_sha256", "dispatch_head_blob_sha256", "repo_path",
    "head_blob_sha256", "repo_tree",
}
_TOOL_FIELDS = {"path", "sha256", "repo_path", "head_blob_sha256"}
_PROCEDURE_FIELDS = {
    "runner_mode", "test_command", "timeout_seconds", "hang_timeout_seconds",
    "source_policy", "restore_policy", "node_policy", "registration_preflight",
    "registration_sha256", "collection",
}
_REGISTRATION_FIELDS = {
    "anchor_counts", "injection_diff_sha256", "expected_nodes",
    "expected_status", "replacements",
}
_COLLECTION_FIELDS = {
    "status", "rc", "collected_nodes", "duration_s", "artifact", "repo_head",
    "spec_sha256", "runner_sha256", "tool_sha256",
}
_BASELINE_FIELDS = {
    "status", "rc", "failed_nodes", "timed_out", "duration_s",
    "artifact_error", "artifact", "test_output_sha256", "test_output_tail",
    "repo_head", "spec_sha256", "registration_sha256", "runner_sha256",
    "tool_sha256", "collection_sha256",
}
_MUTATION_RECORD_FIELDS = {
    "id", "category", "replacements", "expected_nodes", "expected_status",
    "hang_risk", "status", "matches_expectation", "rc", "failed_nodes",
    "timed_out", "duration_s", "artifact_error", "artifact", "anchor_counts",
    "injection_diff_sha256", "test_output_sha256", "test_output_tail",
    "repo_head", "spec_sha256", "registration_sha256", "runner_sha256",
    "tool_sha256", "collection_sha256",
}
_ARTIFACT_FIELDS = {
    "runner_mode", "receipt_path", "job_stdout_path", "stdout", "stdout_sha256",
}
_SUMMARY_FIELDS = {
    "registered", "recorded", "completed", "matching", "KILLED", "SURVIVED",
    "MISMATCH", "TIMEOUT", "PARSE_ERROR",
}
_ATTEMPT_FIELDS = {
    "run_attempt_ordinal", "wrapper_attempt_ordinal", "phase", "mutation_id",
    "state", "started_at", "finished_at", "rc", "timed_out", "artifact_error",
    "console_sha256", "request",
}
_REQUEST_FIELDS = {
    "request_id", "submission_dir", "receipt_path", "job_stdout_path", "outcome_rc",
}
_ATTEMPT_ROOT_FIELDS = {
    "schema", "repo_head", "spec_sha256", "runner_sha256", "tool_sha256",
    "expected_initial_requests", "attempts",
}


class FanoutContractError(RuntimeError):
    """fan-out の証拠を一意に検証できないときの fail-closed 停止。"""


def canonical_json_bytes(value: Any) -> bytes:
    """shard/assignment/index で pin した唯一の JSON 直列化。"""

    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _compact_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _exact(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FanoutContractError(f"{label} が object でない")
    actual = set(value)
    if actual != fields:
        raise FanoutContractError(
            f"{label} の field 集合が不正: "
            f"missing={sorted(fields - actual)}, unknown={sorted(actual - fields)}"
        )
    return value


def _strict_int(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise FanoutContractError(f"{label} が {minimum} 以上の int でない")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise FanoutContractError(f"{label} が lowercase SHA-256 でない")
    return value


def _path_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise FanoutContractError(f"{label} が非空 path 文字列でない")
    return value


def _safe_relative_path(value: Any, label: str) -> str:
    text = _path_string(value, label)
    if "\\" in text:
        raise FanoutContractError(f"{label} が POSIX 相対 path でない")
    path = PurePosixPath(text)
    if path.is_absolute() or path.as_posix() != text or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise FanoutContractError(f"{label} が安全な正規相対 path でない")
    return text


def _read_file(path: Path, label: str) -> bytes:
    try:
        if path.is_symlink() or not path.is_file():
            raise FanoutContractError(f"{label} が symlink でない通常 file でない")
        return path.read_bytes()
    except FanoutContractError:
        raise
    except OSError as exc:
        raise FanoutContractError(f"{label} を読めない: {exc}") from exc


def _relocated_evidence_path(recorded: str, evidence: dict[str, Any], label: str) -> Path:
    recorded_path = Path(recorded)
    original = Path(_path_string(evidence["original_path"], f"{label}.original_path"))
    relocated = Path(_path_string(evidence["relocated_path"], f"{label}.relocated_path"))
    try:
        relative = recorded_path.relative_to(original)
    except ValueError as exc:
        raise FanoutContractError(f"{label} が dispatch evidence original path 外") from exc
    return relocated / relative


def _json_document(payload: bytes, label: str) -> Any:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FanoutContractError(f"{label} JSON を読めない: {exc}") from exc


def _validate_spec_document(value: Any, label: str) -> dict[str, Any]:
    document = _exact(value, _SPEC_FIELDS, label)
    if document["schema"] != SPEC_SCHEMA:
        raise FanoutContractError(f"{label}.schema が未知")
    for key in ("estimated_run_seconds", "timeout_seconds", "hang_timeout_seconds"):
        number = document[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or number <= 0:
            raise FanoutContractError(f"{label}.{key} が正の数でない")
    mutations = document["mutations"]
    if not isinstance(mutations, list) or not mutations:
        raise FanoutContractError(f"{label}.mutations が非空 list でない")
    seen: set[str] = set()
    for index, raw_mutation in enumerate(mutations):
        mutation_label = f"{label}.mutations[{index}]"
        mutation = _exact(raw_mutation, _MUTATION_SPEC_FIELDS, mutation_label)
        mutation_id = mutation["id"]
        if not isinstance(mutation_id, str) or _ID_RE.fullmatch(mutation_id) is None:
            raise FanoutContractError(f"{mutation_label}.id が安全な ID でない")
        if mutation_id in seen:
            raise FanoutContractError(f"{label} の mutation ID が重複: {mutation_id}")
        seen.add(mutation_id)
        if mutation["category"] not in {"negative", "positive", "both-layers"}:
            raise FanoutContractError(f"{mutation_label}.category が未知")
        expected_status = mutation["expected_status"]
        if expected_status not in {"KILLED", "SURVIVED", "TIMEOUT"}:
            raise FanoutContractError(f"{mutation_label}.expected_status が未知")
        if not isinstance(mutation["hang_risk"], bool):
            raise FanoutContractError(f"{mutation_label}.hang_risk が bool でない")
        if expected_status == "TIMEOUT" and mutation["hang_risk"] is not True:
            raise FanoutContractError(f"{mutation_label} TIMEOUT 期待に hang_risk がない")
        nodes = mutation["expected_nodes"]
        if not isinstance(nodes, list) or any(
            not isinstance(item, str) or not item.strip() for item in nodes
        ):
            raise FanoutContractError(f"{mutation_label}.expected_nodes が文字列 list でない")
        if len(nodes) != len(set(nodes)):
            raise FanoutContractError(f"{mutation_label}.expected_nodes が重複")
        if (expected_status == "KILLED") is not bool(nodes):
            raise FanoutContractError(f"{mutation_label}.expected_nodes と status が不整合")
        replacements = mutation["replacements"]
        if not isinstance(replacements, list) or not replacements:
            raise FanoutContractError(f"{mutation_label}.replacements が非空 list でない")
        for replacement_index, raw_replacement in enumerate(replacements):
            replacement = _exact(
                raw_replacement, _REPLACEMENT_FIELDS,
                f"{mutation_label}.replacements[{replacement_index}]",
            )
            _safe_relative_path(replacement["file"], f"{mutation_label}.replacement.file")
            if not isinstance(replacement["old"], str) or not replacement["old"]:
                raise FanoutContractError(f"{mutation_label}.replacement.old が不正")
            if not isinstance(replacement["new"], str) or replacement["new"] == replacement["old"]:
                raise FanoutContractError(f"{mutation_label}.replacement.new が不正")
    return document


def derive_split(
    parent_spec_bytes: bytes, *, expected_parent_sha256: str, shard_count: int
) -> tuple[dict[str, Any], tuple[bytes, ...]]:
    """親 raw bytes と明示 N だけから assignment と shard bytes を再導出する。"""

    expected = _sha256(expected_parent_sha256, "expected_parent_sha256")
    actual = _bytes_sha256(parent_spec_bytes)
    if actual != expected:
        raise FanoutContractError(
            f"親 spec hash が不一致: expected={expected}, actual={actual}"
        )
    parent = _validate_spec_document(_json_document(parent_spec_bytes, "parent spec"), "parent spec")
    mutation_count = len(parent["mutations"])
    _strict_int(shard_count, "shard_count", minimum=2)
    if shard_count > mutation_count:
        raise FanoutContractError("shard_count が mutation 数を超える")

    allocated: list[list[int]] = [[] for _ in range(shard_count)]
    hang_counts = [0] * shard_count
    total_counts = [0] * shard_count
    hang_indices = [
        index for index, mutation in enumerate(parent["mutations"])
        if mutation["hang_risk"] is True
    ]
    normal_indices = [
        index for index, mutation in enumerate(parent["mutations"])
        if mutation["hang_risk"] is False
    ]
    for mutation_index in hang_indices:
        shard_index = min(
            range(shard_count),
            key=lambda item: (hang_counts[item], total_counts[item], item),
        )
        allocated[shard_index].append(mutation_index)
        hang_counts[shard_index] += 1
        total_counts[shard_index] += 1
    for mutation_index in normal_indices:
        shard_index = min(
            range(shard_count),
            key=lambda item: (total_counts[item], hang_counts[item], item),
        )
        allocated[shard_index].append(mutation_index)
        total_counts[shard_index] += 1
    if any(not indices for indices in allocated):
        raise FanoutContractError("空 shard が導出された")

    shard_bytes: list[bytes] = []
    shard_entries: list[dict[str, Any]] = []
    parent_ids = [mutation["id"] for mutation in parent["mutations"]]
    for shard_index, indices in enumerate(allocated):
        ordered = sorted(indices)
        mutations = [parent["mutations"][index] for index in ordered]
        shard_document = {
            "schema": parent["schema"],
            "estimated_run_seconds": parent["estimated_run_seconds"],
            "timeout_seconds": parent["timeout_seconds"],
            "hang_timeout_seconds": parent["hang_timeout_seconds"],
            "mutations": mutations,
        }
        payload = canonical_json_bytes(shard_document)
        shard_id = f"shard-{shard_index:03d}"
        shard_bytes.append(payload)
        shard_entries.append(
            {
                "index": shard_index,
                "shard_id": shard_id,
                "mutation_ids": [mutation["id"] for mutation in mutations],
                "hang_risk_ids": [
                    mutation["id"] for mutation in mutations if mutation["hang_risk"]
                ],
                "relative_spec_path": f"shards/{shard_id}.spec.json",
                "shard_spec_sha256": _bytes_sha256(payload),
                "shard_spec_size": len(payload),
            }
        )
    assignment = {
        "schema": ASSIGNMENT_SCHEMA,
        "parent_spec_sha256": expected,
        "parent_spec_size": len(parent_spec_bytes),
        "parent_mutation_ids": parent_ids,
        "shard_count": shard_count,
        "allocation_rule": ALLOCATION_RULE,
        "serializer": SERIALIZER,
        "shards": shard_entries,
    }
    return assignment, tuple(shard_bytes)


def _create_only(path: Path, payload: bytes, label: str) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError as exc:
        raise FanoutContractError(f"{label} を create-only で作れない: {exc}") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def write_split(
    parent_spec_path: Path,
    *,
    expected_parent_sha256: str,
    shard_count: int,
    group_root: Path,
) -> dict[str, Any]:
    """決定的 split 成果物を fresh group root へ create-only で保存する。"""

    parent_bytes = _read_file(parent_spec_path, "parent spec")
    assignment, shard_payloads = derive_split(
        parent_bytes,
        expected_parent_sha256=expected_parent_sha256,
        shard_count=shard_count,
    )
    root = group_root.resolve()
    targets = [root / entry["relative_spec_path"] for entry in assignment["shards"]]
    targets.append(root / "assignment.json")
    if any(path.exists() or path.is_symlink() for path in targets):
        raise FanoutContractError("split 成果物の出力先が既に存在する")
    for entry, payload in zip(assignment["shards"], shard_payloads, strict=True):
        _create_only(root / entry["relative_spec_path"], payload, entry["shard_id"])
    _create_only(root / "assignment.json", canonical_json_bytes(assignment), "assignment")
    return assignment


def _validate_assignment(
    value: Any,
    *,
    derived: dict[str, Any],
    assignment_bytes: bytes,
) -> dict[str, Any]:
    assignment = _exact(value, _ASSIGNMENT_FIELDS, "assignment")
    shards = assignment["shards"]
    if not isinstance(shards, list):
        raise FanoutContractError("assignment.shards が list でない")
    for index, raw in enumerate(shards):
        _exact(raw, _ASSIGNMENT_SHARD_FIELDS, f"assignment.shards[{index}]")
    if assignment != derived or assignment_bytes != canonical_json_bytes(derived):
        raise FanoutContractError("assignment が親 spec からの再導出結果と不一致")
    return assignment


def _validate_artifact(
    value: Any, label: str, *, allow_incomplete_dispatch: bool = False
) -> dict[str, Any]:
    artifact = _exact(value, _ARTIFACT_FIELDS, label)
    if artifact["runner_mode"] != "dispatch":
        raise FanoutContractError(f"{label}.runner_mode が dispatch でない")
    stdout = artifact["stdout"]
    if not isinstance(stdout, str):
        raise FanoutContractError(f"{label}.stdout が文字列でない")
    if artifact["stdout_sha256"] != _bytes_sha256(stdout.encode("utf-8")):
        raise FanoutContractError(f"{label}.stdout_sha256 が不一致")
    if (
        allow_incomplete_dispatch
        and artifact["receipt_path"] is None
        and artifact["job_stdout_path"] is None
    ):
        return artifact
    for key in ("receipt_path", "job_stdout_path"):
        _path_string(artifact[key], f"{label}.{key}")
    return artifact


def _validate_run_record_types(value: dict[str, Any], label: str) -> None:
    if not isinstance(value["timed_out"], bool):
        raise FanoutContractError(f"{label}.timed_out が bool でない")
    rc = value["rc"]
    if rc is not None and (isinstance(rc, bool) or not isinstance(rc, int)):
        raise FanoutContractError(f"{label}.rc が int/null でない")
    duration = value["duration_s"]
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 0:
        raise FanoutContractError(f"{label}.duration_s が非負数でない")
    error = value["artifact_error"]
    if error is not None and not isinstance(error, str):
        raise FanoutContractError(f"{label}.artifact_error が string/null でない")
    for key in ("failed_nodes", "test_output_tail"):
        field = value[key]
        if not isinstance(field, list) or any(not isinstance(item, str) for item in field):
            raise FanoutContractError(f"{label}.{key} が文字列 list でない")
    for key in (
        "test_output_sha256", "repo_head", "spec_sha256", "registration_sha256",
        "runner_sha256", "tool_sha256", "collection_sha256",
    ):
        if key == "repo_head":
            if not isinstance(value[key], str) or re.fullmatch(
                r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value[key]
            ) is None:
                raise FanoutContractError(f"{label}.repo_head が full object ID でない")
        else:
            _sha256(value[key], f"{label}.{key}")


def _validate_attempts(
    value: Any,
    *,
    shard_id: str,
    ledger: dict[str, Any],
    mutation_ids: list[str],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str | None], dict[str, Any]]]:
    sidecar = _exact(value, _ATTEMPT_ROOT_FIELDS, f"{shard_id} attempt sidecar")
    expected_header = {
        "schema": ATTEMPT_SCHEMA,
        "repo_head": ledger["repo_head"],
        "spec_sha256": ledger["spec_sha256"],
        "runner_sha256": ledger["runner_sha256"],
        "tool_sha256": ledger["tool_sha256"],
        "expected_initial_requests": len(mutation_ids) + 2,
    }
    for key, expected in expected_header.items():
        if sidecar[key] != expected:
            raise FanoutContractError(f"{shard_id} attempt sidecar.{key} が不一致")
    attempts = sidecar["attempts"]
    history = ledger["nonterminal_history"]
    expected_attempt_count = len(mutation_ids) + 2 + len(history)
    if not isinstance(attempts, list) or len(attempts) != expected_attempt_count:
        raise FanoutContractError(f"{shard_id} attempt 数が期待 invocation 数と不一致")
    latest: dict[tuple[str, str | None], dict[str, Any]] = {}
    key_counts: Counter[tuple[str, str | None]] = Counter()
    ordinals: list[int] = []
    for index, raw in enumerate(attempts):
        attempt = _exact(raw, _ATTEMPT_FIELDS, f"{shard_id}.attempts[{index}]")
        ordinal = _strict_int(attempt["run_attempt_ordinal"], "run_attempt_ordinal", minimum=1)
        ordinals.append(ordinal)
        _strict_int(attempt["wrapper_attempt_ordinal"], "wrapper_attempt_ordinal", minimum=1)
        phase = attempt["phase"]
        mutation_id = attempt["mutation_id"]
        if phase not in {"collection", "baseline", "mutation"}:
            raise FanoutContractError(f"{shard_id} attempt phase が未知")
        if phase == "mutation":
            if mutation_id not in mutation_ids:
                raise FanoutContractError(f"{shard_id} attempt mutation ID が未知")
        elif mutation_id is not None:
            raise FanoutContractError(f"{shard_id} 非 mutation attempt に ID がある")
        if attempt["state"] != "finished":
            raise FanoutContractError(f"{shard_id} に finished でない attempt が残る")
        if not isinstance(attempt["started_at"], str) or not isinstance(attempt["finished_at"], str):
            raise FanoutContractError(f"{shard_id} attempt timestamp が不正")
        if not isinstance(attempt["timed_out"], bool):
            raise FanoutContractError(f"{shard_id} attempt timed_out が bool でない")
        rc = attempt["rc"]
        if rc is not None and (isinstance(rc, bool) or not isinstance(rc, int)):
            raise FanoutContractError(f"{shard_id} attempt rc が int/null でない")
        error = attempt["artifact_error"]
        if error is not None and not isinstance(error, str):
            raise FanoutContractError(f"{shard_id} attempt artifact_error が不正")
        _sha256(attempt["console_sha256"], f"{shard_id} attempt console_sha256")
        request = _exact(attempt["request"], _REQUEST_FIELDS, f"{shard_id} attempt request")
        if not isinstance(request["request_id"], str) or not request["request_id"]:
            raise FanoutContractError(f"{shard_id} attempt request_id が不正")
        for key in ("submission_dir", "receipt_path", "job_stdout_path"):
            _path_string(request[key], f"{shard_id} attempt request.{key}")
        outcome_rc = request["outcome_rc"]
        if isinstance(outcome_rc, bool) or not isinstance(outcome_rc, int):
            raise FanoutContractError(f"{shard_id} attempt outcome_rc が int でない")
        if outcome_rc != rc:
            raise FanoutContractError(f"{shard_id} attempt request rc が invocation rc と不一致")
        key = (phase, mutation_id)
        latest[key] = attempt
        key_counts[key] += 1
    if ordinals != list(range(1, len(attempts) + 1)):
        raise FanoutContractError(f"{shard_id} run_attempt_ordinal が連続でない")
    expected_keys = {("collection", None), ("baseline", None)} | {
        ("mutation", mutation_id) for mutation_id in mutation_ids
    }
    if set(latest) != expected_keys:
        raise FanoutContractError(f"{shard_id} invocation 対応が完全でない")
    expected_key_counts: Counter[tuple[str, str | None]] = Counter(expected_keys)
    for record in history:
        if not isinstance(record, dict) or record.get("id") not in mutation_ids:
            raise FanoutContractError(f"{shard_id} history の attempt 対応 ID が不正")
        expected_key_counts[("mutation", record["id"])] += 1
    if key_counts != expected_key_counts:
        raise FanoutContractError(f"{shard_id} attempt と ledger/history の対応数が不一致")
    return attempts, latest


def _require_id_bijection(parent_ids: Sequence[str], shard_ids: Sequence[str]) -> None:
    if Counter(shard_ids) != Counter(parent_ids) or len(shard_ids) != len(parent_ids):
        raise FanoutContractError("shard mutation ID の直和が親 ID 集合と一致しない")


def _validate_ledger(
    value: Any,
    *,
    shard_id: str,
    shard_spec: dict[str, Any],
    shard_spec_sha256: str,
    expected_paths: dict[str, Any],
) -> tuple[dict[str, Any], list[str], bool]:
    ledger = _exact(value, _LEDGER_FIELDS, f"{shard_id} ledger")
    if ledger["schema"] != LEDGER_SCHEMA or ledger["spec_sha256"] != shard_spec_sha256:
        raise FanoutContractError(f"{shard_id} ledger schema/spec hash が不一致")
    runner = _exact(ledger["runner_identity"], _RUNNER_FIELDS, f"{shard_id} runner_identity")
    tool = _exact(ledger["tool_identity"], _TOOL_FIELDS, f"{shard_id} tool_identity")
    if runner["runner_mode"] != "dispatch":
        raise FanoutContractError(f"{shard_id} runner_mode が dispatch でない")
    path_expectations = {
        "entrypoint_path": expected_paths["runner_entrypoint_path"],
        "dispatch_entrypoint_path": expected_paths["dispatch_entrypoint_path"],
    }
    for key, expected in path_expectations.items():
        if runner[key] != expected:
            raise FanoutContractError(f"{shard_id} runner_identity.{key} が manifest path と不一致")
    if tool["path"] != expected_paths["tool_path"]:
        raise FanoutContractError(f"{shard_id} tool_identity.path が manifest path と不一致")
    if ledger["runner_sha256"] != _compact_sha256(runner):
        raise FanoutContractError(f"{shard_id} runner_sha256 が identity と不一致")
    if ledger["tool_sha256"] != _compact_sha256(tool):
        raise FanoutContractError(f"{shard_id} tool_sha256 が identity と不一致")

    procedure = _exact(ledger["procedure"], _PROCEDURE_FIELDS, f"{shard_id} procedure")
    if procedure["runner_mode"] != "dispatch" or procedure["test_command"] != runner["command"]:
        raise FanoutContractError(f"{shard_id} procedure runner/command が不一致")
    if procedure["timeout_seconds"] != shard_spec["timeout_seconds"]:
        raise FanoutContractError(f"{shard_id} timeout_seconds が親由来値と不一致")
    if procedure["hang_timeout_seconds"] != shard_spec["hang_timeout_seconds"]:
        raise FanoutContractError(f"{shard_id} hang_timeout_seconds が親由来値と不一致")

    mutation_ids = [mutation["id"] for mutation in shard_spec["mutations"]]
    expected_mutations = {mutation["id"]: mutation for mutation in shard_spec["mutations"]}
    registration = procedure["registration_preflight"]
    if not isinstance(registration, dict) or set(registration) != set(mutation_ids):
        raise FanoutContractError(f"{shard_id} registration_preflight の ID 集合が不一致")
    for mutation_id in mutation_ids:
        item = _exact(
            registration[mutation_id],
            _REGISTRATION_FIELDS,
            f"{shard_id} registration {mutation_id}",
        )
        expected_mutation = expected_mutations[mutation_id]
        if (
            item["expected_nodes"] != expected_mutation["expected_nodes"]
            or item["expected_status"] != expected_mutation["expected_status"]
            or item["replacements"] != expected_mutation["replacements"]
        ):
            raise FanoutContractError(f"{shard_id} registration {mutation_id} が spec と不一致")
        counts = item["anchor_counts"]
        expected_count_keys = {
            str(index) for index in range(len(expected_mutation["replacements"]))
        }
        if not isinstance(counts, dict) or set(counts) != expected_count_keys or any(
            _strict_int(value, f"{shard_id} anchor count", minimum=1) != 1
            for value in counts.values()
        ):
            raise FanoutContractError(f"{shard_id} registration anchor_counts が不正")
        _sha256(item["injection_diff_sha256"], f"{shard_id} injection diff")
    if procedure["registration_sha256"] != _compact_sha256(registration):
        raise FanoutContractError(f"{shard_id} registration_sha256 が不一致")

    collection = _exact(procedure["collection"], _COLLECTION_FIELDS, f"{shard_id} collection")
    if collection["status"] != "PASSED" or collection["rc"] != 0:
        raise FanoutContractError(f"{shard_id} collection が PASSED/0 でない")
    if collection["repo_head"] != ledger["repo_head"]:
        raise FanoutContractError(f"{shard_id} collection.repo_head が不一致")
    expected_collection = {
        "spec_sha256": ledger["spec_sha256"],
        "runner_sha256": ledger["runner_sha256"],
        "tool_sha256": ledger["tool_sha256"],
    }
    for key, expected in expected_collection.items():
        if collection[key] != expected:
            raise FanoutContractError(f"{shard_id} collection.{key} が不一致")
    if not isinstance(collection["collected_nodes"], list) or any(
        not isinstance(item, str) for item in collection["collected_nodes"]
    ):
        raise FanoutContractError(f"{shard_id} collected_nodes が文字列 list でない")
    expected_nodes = {
        node for mutation in shard_spec["mutations"] for node in mutation["expected_nodes"]
    }
    if not expected_nodes <= set(collection["collected_nodes"]):
        raise FanoutContractError(f"{shard_id} collection に expected node がない")
    _validate_artifact(collection["artifact"], f"{shard_id} collection artifact")

    baseline = _exact(ledger["baseline"], _BASELINE_FIELDS, f"{shard_id} baseline")
    _validate_run_record_types(baseline, f"{shard_id} baseline")
    _validate_artifact(baseline["artifact"], f"{shard_id} baseline artifact")
    if baseline["status"] != "PASSED" or baseline["rc"] != 0 or baseline["failed_nodes"] != []:
        raise FanoutContractError(f"{shard_id} baseline が PASSED/0/[] でない")
    collection_sha256 = _compact_sha256(collection)
    baseline_links = {
        "repo_head": ledger["repo_head"],
        "spec_sha256": ledger["spec_sha256"],
        "registration_sha256": procedure["registration_sha256"],
        "runner_sha256": ledger["runner_sha256"],
        "tool_sha256": ledger["tool_sha256"],
        "collection_sha256": collection_sha256,
    }
    if any(baseline[key] != expected for key, expected in baseline_links.items()):
        raise FanoutContractError(f"{shard_id} baseline proof link が不一致")
    if baseline["test_output_sha256"] != _bytes_sha256(
        baseline["artifact"]["stdout"].encode("utf-8")
    ):
        raise FanoutContractError(f"{shard_id} baseline stdout hash が不一致")

    summary = _exact(ledger["summary"], _SUMMARY_FIELDS, f"{shard_id} summary")
    for key in _SUMMARY_FIELDS:
        _strict_int(summary[key], f"{shard_id} summary.{key}")
    records = ledger["mutations"]
    history = ledger["nonterminal_history"]
    if not isinstance(records, list) or not isinstance(history, list):
        raise FanoutContractError(f"{shard_id} mutations/history が list でない")
    if summary["registered"] != summary["recorded"] or summary["registered"] != len(mutation_ids):
        raise FanoutContractError(f"{shard_id} registered != recorded")
    if len(records) != len(mutation_ids) or summary["completed"] != len(mutation_ids):
        raise FanoutContractError(f"{shard_id} record/completed 数が不一致")
    if summary["PARSE_ERROR"] != 0:
        raise FanoutContractError(f"{shard_id} PARSE_ERROR を含む")

    record_ids: list[str] = []
    status_counts = Counter()
    matching = 0
    all_matching = True
    for index, raw_record in enumerate(records):
        record = _exact(raw_record, _MUTATION_RECORD_FIELDS, f"{shard_id} mutations[{index}]")
        _validate_run_record_types(record, f"{shard_id} mutations[{index}]")
        mutation_id = record["id"]
        if mutation_id not in expected_mutations:
            raise FanoutContractError(f"{shard_id} mutation record に未知 ID がある")
        expected_mutation = expected_mutations[mutation_id]
        mutation_registration = registration[mutation_id]
        for key in ("id", "category", "replacements", "expected_nodes", "expected_status", "hang_risk"):
            if record[key] != expected_mutation[key]:
                raise FanoutContractError(f"{shard_id} {mutation_id}.{key} が shard spec と不一致")
        status = record["status"]
        if status == "TIMEOUT":
            raise FanoutContractError(f"{shard_id} に TIMEOUT record がある")
        if status not in _MERGEABLE_STATUSES:
            raise FanoutContractError(f"{shard_id} mutation status が merge terminal でない")
        _validate_artifact(record["artifact"], f"{shard_id} mutations[{index}].artifact")
        record_links = {
            "anchor_counts": mutation_registration["anchor_counts"],
            "injection_diff_sha256": mutation_registration["injection_diff_sha256"],
            "repo_head": ledger["repo_head"],
            "spec_sha256": ledger["spec_sha256"],
            "registration_sha256": _compact_sha256(mutation_registration),
            "runner_sha256": ledger["runner_sha256"],
            "tool_sha256": ledger["tool_sha256"],
            "collection_sha256": collection_sha256,
        }
        if any(record[key] != expected for key, expected in record_links.items()):
            raise FanoutContractError(f"{shard_id} {mutation_id} proof link が不一致")
        if record["test_output_sha256"] != _bytes_sha256(
            record["artifact"]["stdout"].encode("utf-8")
        ):
            raise FanoutContractError(f"{shard_id} {mutation_id} stdout hash が不一致")
        matches = record["matches_expectation"]
        if not isinstance(matches, bool) or matches is not (status == record["expected_status"]):
            raise FanoutContractError(f"{shard_id} {mutation_id}.matches_expectation が不一致")
        record_ids.append(mutation_id)
        status_counts[status] += 1
        matching += int(matches)
        all_matching = all_matching and matches
    if record_ids != mutation_ids:
        raise FanoutContractError(f"{shard_id} ledger mutation ID/順序が shard spec と不一致")
    for raw_history in history:
        history_record = _exact(raw_history, _MUTATION_RECORD_FIELDS, f"{shard_id} history")
        _validate_run_record_types(history_record, f"{shard_id} history")
        if history_record["status"] == "TIMEOUT":
            raise FanoutContractError(f"{shard_id} history に TIMEOUT record がある")
        if history_record["status"] != "PARSE_ERROR":
            raise FanoutContractError(f"{shard_id} history に PARSE_ERROR 以外がある")
        _validate_artifact(
            history_record["artifact"],
            f"{shard_id} history artifact",
            allow_incomplete_dispatch=True,
        )
    recomputed = {
        "registered": len(mutation_ids),
        "recorded": len(records),
        "completed": len(records),
        "matching": matching,
        "KILLED": status_counts["KILLED"],
        "SURVIVED": status_counts["SURVIVED"],
        "MISMATCH": status_counts["MISMATCH"],
        "TIMEOUT": 0,
        "PARSE_ERROR": 0,
    }
    if summary != recomputed:
        raise FanoutContractError(f"{shard_id} summary が record 再集計と不一致")
    return ledger, mutation_ids, all_matching


def merge_group(
    parent_spec_path: Path,
    *,
    expected_parent_sha256: str,
    assignment_path: Path,
    group_manifest_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """親 spec を権威として全 shard を検査し create-only hash index を作る。"""

    output = output_path.resolve()
    if output.exists() or output.is_symlink():
        raise FanoutContractError("merge index が既に存在する")
    parent_bytes = _read_file(parent_spec_path, "parent spec")
    assignment_bytes = _read_file(assignment_path, "assignment")
    assignment_value = _json_document(assignment_bytes, "assignment")
    if not isinstance(assignment_value, dict):
        raise FanoutContractError("assignment root が object でない")
    shard_count = _strict_int(assignment_value.get("shard_count"), "assignment.shard_count", minimum=2)
    derived, shard_payloads = derive_split(
        parent_bytes,
        expected_parent_sha256=expected_parent_sha256,
        shard_count=shard_count,
    )
    assignment = _validate_assignment(
        assignment_value, derived=derived, assignment_bytes=assignment_bytes
    )
    assignment_sha256 = _bytes_sha256(assignment_bytes)

    group_bytes = _read_file(group_manifest_path, "group manifest")
    group = _exact(_json_document(group_bytes, "group manifest"), _GROUP_FIELDS, "group manifest")
    if group["schema"] != GROUP_SCHEMA:
        raise FanoutContractError("group manifest schema が未知")
    if group["parent_spec_sha256"] != expected_parent_sha256:
        raise FanoutContractError("group manifest parent spec hash が不一致")
    if group["assignment_sha256"] != assignment_sha256:
        raise FanoutContractError("group manifest assignment hash が不一致")
    group_shards = group["shards"]
    if not isinstance(group_shards, list) or len(group_shards) != shard_count:
        raise FanoutContractError("group manifest shard 数が assignment と不一致")

    parent = _validate_spec_document(_json_document(parent_bytes, "parent spec"), "parent spec")
    parent_ids = [mutation["id"] for mutation in parent["mutations"]]
    seen_ids: list[str] = []
    collected_nodes: list[str] | None = None
    common_runner_content: dict[str, Any] | None = None
    common_tool_content: dict[str, Any] | None = None
    common_procedure_content: dict[str, Any] | None = None
    common_repo_head: str | None = None
    common_wrapper_sha256: str | None = None
    request_ids: set[str] = set()
    shard_index_entries: list[dict[str, Any]] = []
    mutation_index: list[dict[str, Any]] = []
    request_index: list[dict[str, Any]] = []
    total_recorded = 0
    total_history = 0
    global_matching = True

    for index, (raw_group_shard, assignment_shard, expected_spec_bytes) in enumerate(
        zip(group_shards, assignment["shards"], shard_payloads, strict=True)
    ):
        shard = _exact(raw_group_shard, _GROUP_SHARD_FIELDS, f"group.shards[{index}]")
        if (
            _strict_int(shard["index"], "group shard index") != index
            or shard["shard_id"] != assignment_shard["shard_id"]
        ):
            raise FanoutContractError("group shard index/ID が assignment と不一致")
        expected_paths = _exact(
            shard["expected_paths"], _EXPECTED_PATH_FIELDS,
            f"group.shards[{index}].expected_paths",
        )
        for key in _EXPECTED_PATH_FIELDS:
            _path_string(expected_paths[key], f"group shard expected_paths.{key}")
        spec_path = Path(_path_string(shard["spec_path"], "group shard spec_path"))
        spec_bytes = _read_file(spec_path, f"{shard['shard_id']} spec")
        if spec_bytes != expected_spec_bytes:
            raise FanoutContractError(f"{shard['shard_id']} spec bytes が再導出結果と不一致")
        spec_sha256 = _bytes_sha256(expected_spec_bytes)
        if spec_sha256 != assignment_shard["shard_spec_sha256"]:
            raise FanoutContractError(f"{shard['shard_id']} assignment spec hash が不一致")
        shard_spec = _validate_spec_document(
            _json_document(spec_bytes, f"{shard['shard_id']} spec"),
            f"{shard['shard_id']} spec",
        )

        ledger_path = Path(_path_string(shard["ledger_path"], "group shard ledger_path"))
        ledger_bytes = _read_file(ledger_path, f"{shard['shard_id']} ledger")
        ledger, mutation_ids, shard_matching = _validate_ledger(
            _json_document(ledger_bytes, f"{shard['shard_id']} ledger"),
            shard_id=shard["shard_id"],
            shard_spec=shard_spec,
            shard_spec_sha256=spec_sha256,
            expected_paths=expected_paths,
        )

        wrapper_path = Path(_path_string(
            shard["wrapper_receipt_path"], "group shard wrapper_receipt_path"
        ))
        wrapper_bytes = _read_file(wrapper_path, f"{shard['shard_id']} wrapper receipt")
        wrapper = _exact(
            _json_document(wrapper_bytes, f"{shard['shard_id']} wrapper receipt"),
            _WRAPPER_FIELDS,
            f"{shard['shard_id']} wrapper receipt",
        )
        evidence = _exact(
            wrapper["dispatch_evidence"], _EVIDENCE_FIELDS,
            f"{shard['shard_id']} dispatch_evidence",
        )
        if wrapper["schema"] != WRAPPER_SCHEMA:
            raise FanoutContractError(f"{shard['shard_id']} wrapper schema が未知")
        _sha256(wrapper["wrapper_sha256"], f"{shard['shard_id']} wrapper_sha256")
        for key in ("scratch_root", "container_path", "lock_path"):
            if wrapper[key] != expected_paths[key]:
                raise FanoutContractError(f"{shard['shard_id']} wrapper {key} が manifest path と不一致")
        if wrapper["resolved_commit"] != ledger["repo_head"]:
            raise FanoutContractError(f"{shard['shard_id']} wrapper commit が ledger と不一致")
        wrapper_rc = shard["wrapper_rc"]
        if isinstance(wrapper_rc, bool) or wrapper_rc not in {0, 1}:
            raise FanoutContractError(f"{shard['shard_id']} wrapper_rc が terminal rc でない")
        expected_rc = 0 if shard_matching else 1
        child_rc = wrapper["child_rc"]
        if isinstance(child_rc, bool) or child_rc not in {0, 1}:
            raise FanoutContractError(f"{shard['shard_id']} wrapper child_rc が terminal rc でない")
        if child_rc != wrapper_rc or wrapper_rc != expected_rc:
            raise FanoutContractError(f"{shard['shard_id']} rc と ledger matches_expectation が不一致")
        if wrapper["terminal_ledger"] is not True:
            raise FanoutContractError(f"{shard['shard_id']} terminal_ledger が true でない")
        if (
            wrapper["shared_snapshot_matches"] is not True
            or wrapper["teardown_attempted"] is not True
            or wrapper["teardown_completed"] is not True
            or wrapper["container_preserved"] is not False
            or wrapper["failure"] is not None
            or evidence["relocated"] is not True
        ):
            raise FanoutContractError(f"{shard['shard_id']} wrapper terminal state が不完全")

        attempt_path = Path(_path_string(shard["attempt_path"], "group shard attempt_path"))
        attempt_bytes = _read_file(attempt_path, f"{shard['shard_id']} attempt sidecar")
        attempts, latest = _validate_attempts(
            _json_document(attempt_bytes, f"{shard['shard_id']} attempt sidecar"),
            shard_id=shard["shard_id"],
            ledger=ledger,
            mutation_ids=mutation_ids,
        )
        wrapper_attempt_ordinal = _strict_int(
            shard["wrapper_attempt_ordinal"],
            f"{shard['shard_id']} wrapper_attempt_ordinal",
            minimum=1,
        )
        if max(entry["wrapper_attempt_ordinal"] for entry in attempts) != wrapper_attempt_ordinal:
            raise FanoutContractError(
                f"{shard['shard_id']} wrapper attempt と run attempt が不一致"
            )
        ledger_rows = {
            ("collection", None): ledger["procedure"]["collection"],
            ("baseline", None): ledger["baseline"],
        }
        ledger_rows.update({("mutation", row["id"]): row for row in ledger["mutations"]})
        for key, row in ledger_rows.items():
            attempt = latest[key]
            artifact = row["artifact"]
            request = attempt["request"]
            if attempt["rc"] != row["rc"]:
                raise FanoutContractError(f"{shard['shard_id']} attempt rc と ledger 行が不一致")
            if request["receipt_path"] != artifact["receipt_path"]:
                raise FanoutContractError(f"{shard['shard_id']} request receipt と ledger 行が不一致")
            if request["job_stdout_path"] != artifact["job_stdout_path"]:
                raise FanoutContractError(f"{shard['shard_id']} request stdout と ledger 行が不一致")
            relocated_stdout = _read_file(
                _relocated_evidence_path(
                    request["job_stdout_path"], evidence,
                    f"{shard['shard_id']} request stdout",
                ),
                f"{shard['shard_id']} relocated request stdout",
            ).decode("utf-8", "replace")
            if relocated_stdout != artifact["stdout"]:
                raise FanoutContractError(
                    f"{shard['shard_id']} relocated stdout bytes が ledger 行と不一致"
                )
        for attempt in attempts:
            request = attempt["request"]
            request_id = request["request_id"]
            if request_id in request_ids:
                raise FanoutContractError("request ID が shard 間または attempt 間で重複")
            request_ids.add(request_id)
            request_index.append(
                {
                    "request_id": request_id,
                    "shard_id": shard["shard_id"],
                    "run_attempt_ordinal": attempt["run_attempt_ordinal"],
                    "phase": attempt["phase"],
                    "mutation_id": attempt["mutation_id"],
                    "receipt_path": request["receipt_path"],
                    "receipt_sha256": _bytes_sha256(_read_file(
                        _relocated_evidence_path(
                            request["receipt_path"], evidence, f"request {request_id} receipt"
                        ),
                        f"request {request_id} receipt",
                    )),
                }
            )

        runner_content = {
            key: value for key, value in ledger["runner_identity"].items()
            if key not in {"entrypoint_path", "dispatch_entrypoint_path"}
        }
        tool_content = {
            key: value for key, value in ledger["tool_identity"].items() if key != "path"
        }
        procedure_content = {
            key: ledger["procedure"][key]
            for key in (
                "runner_mode", "test_command", "timeout_seconds", "hang_timeout_seconds",
                "source_policy", "restore_policy", "node_policy",
            )
        }
        if common_runner_content is None:
            common_runner_content = runner_content
            common_tool_content = tool_content
            common_procedure_content = procedure_content
            common_repo_head = ledger["repo_head"]
            common_wrapper_sha256 = wrapper["wrapper_sha256"]
            collected_nodes = ledger["procedure"]["collection"]["collected_nodes"]
        elif (
            runner_content != common_runner_content
            or tool_content != common_tool_content
            or procedure_content != common_procedure_content
            or ledger["repo_head"] != common_repo_head
            or wrapper["wrapper_sha256"] != common_wrapper_sha256
        ):
            raise FanoutContractError(f"{shard['shard_id']} の内容 identity が shard 間で不一致")
        if ledger["procedure"]["collection"]["collected_nodes"] != collected_nodes:
            raise FanoutContractError("procedure.collection.collected_nodes が順序込みで不一致")

        seen_ids.extend(mutation_ids)
        total_recorded += ledger["summary"]["recorded"]
        total_history += len(ledger["nonterminal_history"])
        global_matching = global_matching and shard_matching
        for row_index, mutation_id in enumerate(mutation_ids):
            mutation_index.append(
                {
                    "mutation_id": mutation_id,
                    "shard_id": shard["shard_id"],
                    "ledger_pointer": f"/mutations/{row_index}",
                }
            )
        shard_index_entries.append(
            {
                "index": index,
                "shard_id": shard["shard_id"],
                "spec_path": str(spec_path),
                "spec_sha256": spec_sha256,
                "ledger_path": str(ledger_path),
                "ledger_sha256": _bytes_sha256(ledger_bytes),
                "ledger_size": len(ledger_bytes),
                "wrapper_receipt_path": str(wrapper_path),
                "wrapper_receipt_sha256": _bytes_sha256(wrapper_bytes),
                "attempt_path": str(attempt_path),
                "attempt_sha256": _bytes_sha256(attempt_bytes),
                "runner_sha256": ledger["runner_sha256"],
                "tool_sha256": ledger["tool_sha256"],
                "recorded": ledger["summary"]["recorded"],
            }
        )

    _require_id_bijection(parent_ids, seen_ids)
    if total_recorded != len(parent_ids):
        raise FanoutContractError("Σrecorded が親 registered と一致しない")
    if len(request_ids) != len(parent_ids) + 2 * shard_count + total_history:
        raise FanoutContractError("request 総数が変異数 + 2N (+ resume history) と不一致")

    index_document = {
        "schema": MERGE_SCHEMA,
        "parent_spec_path": str(parent_spec_path.resolve()),
        "parent_spec_sha256": expected_parent_sha256,
        "parent_spec_size": len(parent_bytes),
        "assignment_path": str(assignment_path.resolve()),
        "assignment_sha256": assignment_sha256,
        "group_manifest_path": str(group_manifest_path.resolve()),
        "group_manifest_sha256": _bytes_sha256(group_bytes),
        "shard_count": shard_count,
        "registered": len(parent_ids),
        "recorded": total_recorded,
        "matches_expectation": global_matching,
        "result_rc": 0 if global_matching else 1,
        "shards": shard_index_entries,
        "mutations": mutation_index,
        "requests": request_index,
    }
    _create_only(output, canonical_json_bytes(index_document), "merge index")
    return index_document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    split = subparsers.add_parser("split")
    split.add_argument("--parent-spec", required=True, type=Path)
    split.add_argument("--expected-parent-sha256", required=True)
    split.add_argument("--shard-count", required=True, type=int)
    split.add_argument("--group-root", required=True, type=Path)
    merge = subparsers.add_parser("merge")
    merge.add_argument("--parent-spec", required=True, type=Path)
    merge.add_argument("--expected-parent-sha256", required=True)
    merge.add_argument("--assignment", required=True, type=Path)
    merge.add_argument("--group-manifest", required=True, type=Path)
    merge.add_argument("--out", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.operation == "split":
        write_split(
            args.parent_spec,
            expected_parent_sha256=args.expected_parent_sha256,
            shard_count=args.shard_count,
            group_root=args.group_root,
        )
    else:
        merge_group(
            args.parent_spec,
            expected_parent_sha256=args.expected_parent_sha256,
            assignment_path=args.assignment,
            group_manifest_path=args.group_manifest,
            output_path=args.out,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FanoutContractError as exc:
        print(f"mutation fan-out contract aborted: {exc}", file=os.sys.stderr)
        raise SystemExit(2)
