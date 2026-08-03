#!/usr/bin/env python3
"""Leg 1/2 の mutation ledger を fail-closed に比較する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LEDGER_SCHEMA = "izanagi-dev-wave-mutation/v4"
SPEC_SCHEMA = "izanagi-dev-wave-mutation-spec/v1"
DEFAULT_ANCHOR = "ea6ca433eb83d666ec64f3629cc35c769a2b5c19"
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

TOP_KEYS = {
    "schema",
    "date",
    "updated_at",
    "repo_head",
    "spec_sha256",
    "runner_sha256",
    "runner_identity",
    "tool_sha256",
    "tool_identity",
    "procedure",
    "baseline",
    "summary",
    "mutations",
    "nonterminal_history",
}
RUNNER_IDENTITY_KEYS = {
    "runner_mode",
    "command",
    "entrypoint_kind",
    "executable_path",
    "executable_sha256",
    "entrypoint_path",
    "entrypoint_sha256",
    "pytest_distribution_sha256",
    "dispatch_entrypoint_path",
    "dispatch_entrypoint_sha256",
    "dispatch_head_blob_sha256",
    "repo_path",
    "head_blob_sha256",
    "repo_tree",
}
TOOL_IDENTITY_KEYS = {"path", "sha256", "repo_path", "head_blob_sha256"}
COMMAND_EXECUTABLE_PATHS = {
    ("procedure", "test_command", 0),
    ("runner_identity", "command", 0),
}
RUNNER_EXECUTABLE_SHA256_PATH = ("runner_identity", "executable_sha256")
PROCEDURE_KEYS = {
    "runner_mode",
    "test_command",
    "timeout_seconds",
    "hang_timeout_seconds",
    "source_policy",
    "restore_policy",
    "node_policy",
    "registration_preflight",
    "registration_sha256",
    "collection",
}
ARTIFACT_KEYS = {
    "runner_mode",
    "receipt_path",
    "job_stdout_path",
    "stdout",
    "stdout_sha256",
}
COLLECTION_KEYS = {
    "status",
    "rc",
    "collected_nodes",
    "duration_s",
    "artifact",
    "repo_head",
    "spec_sha256",
    "runner_sha256",
    "tool_sha256",
}
BASELINE_KEYS = {
    "status",
    "rc",
    "failed_nodes",
    "timed_out",
    "duration_s",
    "artifact_error",
    "artifact",
    "test_output_sha256",
    "test_output_tail",
    "repo_head",
    "spec_sha256",
    "registration_sha256",
    "runner_sha256",
    "tool_sha256",
    "collection_sha256",
}
MUTATION_KEYS = {
    "id",
    "category",
    "replacements",
    "expected_nodes",
    "expected_status",
    "hang_risk",
    "status",
    "matches_expectation",
    "rc",
    "failed_nodes",
    "timed_out",
    "duration_s",
    "artifact_error",
    "artifact",
    "anchor_counts",
    "injection_diff_sha256",
    "test_output_sha256",
    "test_output_tail",
    "repo_head",
    "spec_sha256",
    "registration_sha256",
    "runner_sha256",
    "tool_sha256",
    "collection_sha256",
}
SPEC_KEYS = {
    "schema",
    "estimated_run_seconds",
    "timeout_seconds",
    "hang_timeout_seconds",
    "mutations",
}
SPEC_MUTATION_KEYS = {
    "id",
    "category",
    "replacements",
    "expected_nodes",
    "expected_status",
    "hang_risk",
}
REGISTRATION_KEYS = {
    "anchor_counts",
    "expected_nodes",
    "expected_status",
    "injection_diff_sha256",
    "replacements",
}
REPLACEMENT_KEYS = {"file", "old", "new"}


@dataclass(frozen=True)
class Exclusion:
    pattern: tuple[str, ...]
    reason: str


# この表を再帰比較そのものが参照する。表示専用の除外一覧ではない。
EXCLUSIONS = (
    Exclusion(("date",), "run ごとの記録時刻"),
    Exclusion(("updated_at",), "run ごとの更新時刻"),
    Exclusion(("runner_sha256",), "経路固有 field を含む runner_identity 全体の派生 hash"),
    Exclusion(("runner_identity", "runner_mode"), "比較対象である transport の差"),
    Exclusion(("runner_identity", "dispatch_entrypoint_path"), "dispatch 経路にだけ存在する path"),
    Exclusion(("runner_identity", "dispatch_entrypoint_sha256"), "dispatch 経路にだけ存在する entrypoint identity"),
    Exclusion(("runner_identity", "dispatch_head_blob_sha256"), "dispatch 経路にだけ存在する HEAD blob identity"),
    Exclusion(("runner_identity", "executable_sha256"), "実行 host 上の outer Python bytes"),
    Exclusion(("runner_identity", "entrypoint_path"), "worktree の絶対 path"),
    Exclusion(("tool_identity", "path"), "worktree の絶対 path"),
    Exclusion(("procedure", "runner_mode"), "比較対象である transport の差"),
    Exclusion(("procedure", "collection", "duration_s"), "collection の経路別所要時間"),
    Exclusion(("procedure", "collection", "runner_sha256"), "経路固有 runner identity の派生 hash"),
    Exclusion(("procedure", "collection", "artifact", "runner_mode"), "比較対象である transport の差"),
    Exclusion(("procedure", "collection", "artifact", "receipt_path"), "dispatch 経路にだけ存在する receipt path"),
    Exclusion(("procedure", "collection", "artifact", "job_stdout_path"), "dispatch 経路にだけ存在する stdout path"),
    Exclusion(("procedure", "collection", "artifact", "stdout"), "full bytes は時刻を含むため除外し、raw nodeid 順序列を別 gate で比較"),
    Exclusion(("procedure", "collection", "artifact", "stdout_sha256"), "時刻を含む collection stdout の派生 hash"),
    Exclusion(("baseline", "duration_s"), "test run の経路別所要時間"),
    Exclusion(("baseline", "runner_sha256"), "経路固有 runner identity の派生 hash"),
    Exclusion(("baseline", "collection_sha256"), "時刻を含む collection stdout の派生 hash"),
    Exclusion(("baseline", "test_output_sha256"), "時刻を含む test stdout の派生 hash"),
    Exclusion(("baseline", "artifact", "runner_mode"), "比較対象である transport の差"),
    Exclusion(("baseline", "artifact", "receipt_path"), "dispatch 経路にだけ存在する receipt path"),
    Exclusion(("baseline", "artifact", "job_stdout_path"), "dispatch 経路にだけ存在する stdout path"),
    Exclusion(("baseline", "artifact", "stdout"), "pytest の所要時間等を含む経路別 stdout"),
    Exclusion(("baseline", "artifact", "stdout_sha256"), "経路別 test stdout の派生 hash"),
    Exclusion(("mutations", "*", "duration_s"), "test run の経路別所要時間"),
    Exclusion(("mutations", "*", "runner_sha256"), "経路固有 runner identity の派生 hash"),
    Exclusion(("mutations", "*", "collection_sha256"), "時刻を含む collection stdout の派生 hash"),
    Exclusion(("mutations", "*", "test_output_sha256"), "時刻を含む test stdout の派生 hash"),
    Exclusion(("mutations", "*", "artifact", "runner_mode"), "比較対象である transport の差"),
    Exclusion(("mutations", "*", "artifact", "receipt_path"), "dispatch 経路にだけ存在する receipt path"),
    Exclusion(("mutations", "*", "artifact", "job_stdout_path"), "dispatch 経路にだけ存在する stdout path"),
    Exclusion(("mutations", "*", "artifact", "stdout"), "pytest の所要時間等を含む経路別 stdout"),
    Exclusion(("mutations", "*", "artifact", "stdout_sha256"), "経路別 test stdout の派生 hash"),
)


@dataclass
class Gate:
    conditions: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def require(self, condition: str, accepted: bool, failure: str) -> None:
        self.conditions.append(condition)
        if not accepted:
            self.failures.append(failure)


@dataclass(frozen=True)
class Difference:
    path: tuple[str | int, ...]
    leg1: Any
    leg2: Any
    exclusion: Exclusion | None


def _load_json(path: Path, label: str, gate: Gate) -> tuple[dict[str, Any] | None, bytes | None]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        gate.require(f"{label} が UTF-8 JSON object として読める", False, f"{label}: JSON を読めない: {exc}")
        return None, None
    gate.require(
        f"{label} が UTF-8 JSON object として読める",
        isinstance(value, dict),
        f"{label}: root が object でない",
    )
    return (value if isinstance(value, dict) else None), raw


def _json_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _exact_keys(value: Any, expected: set[str], label: str, gate: Gate) -> bool:
    accepted = isinstance(value, dict) and set(value) == expected
    actual = sorted(value) if isinstance(value, dict) else type(value).__name__
    gate.require(
        f"{label} の field 集合が schema 定義と完全一致",
        accepted,
        f"{label}: field 集合が不正: expected={sorted(expected)}, actual={actual}",
    )
    return accepted


def _validate_replacements(value: Any, label: str, gate: Gate) -> None:
    ok = isinstance(value, list) and len(value) > 0
    gate.require(f"{label} が非空 replacement list", ok, f"{label}: 非空 list でない")
    if not isinstance(value, list):
        return
    for index, replacement in enumerate(value):
        item_label = f"{label}[{index}]"
        if not _exact_keys(replacement, REPLACEMENT_KEYS, item_label, gate):
            continue
        gate.require(
            f"{item_label} の file/old/new が文字列",
            all(isinstance(replacement[key], str) for key in REPLACEMENT_KEYS),
            f"{item_label}: file/old/new に非文字列がある",
        )


def _validate_artifact(value: Any, label: str, mode: str, gate: Gate) -> str | None:
    if not _exact_keys(value, ARTIFACT_KEYS, label, gate):
        return None
    assert isinstance(value, dict)
    stdout = value["stdout"]
    gate.require(f"{label}.runner_mode == {mode!r}", value["runner_mode"] == mode, f"{label}.runner_mode={value['runner_mode']!r}")
    gate.require(f"{label}.stdout が文字列", isinstance(stdout, str), f"{label}.stdout が文字列でない")
    if isinstance(stdout, str):
        actual = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
        gate.require(f"{label}.stdout_sha256 が実 stdout bytes と一致", value["stdout_sha256"] == actual, f"{label}.stdout_sha256 が実 stdout bytes と不一致")
    else:
        gate.require(f"{label}.stdout_sha256 が SHA-256", _is_sha256(value["stdout_sha256"]), f"{label}.stdout_sha256 が SHA-256 でない")
    if mode == "dispatch":
        for key in ("receipt_path", "job_stdout_path"):
            gate.require(f"{label}.{key} が dispatch path 文字列", isinstance(value[key], str) and bool(value[key]), f"{label}.{key} が dispatch path 文字列でない")
    else:
        for key in ("receipt_path", "job_stdout_path"):
            gate.require(f"{label}.{key} が local 経路では null", value[key] is None, f"{label}.{key} が local 経路で null でない")
    return stdout if isinstance(stdout, str) else None


def _strip_relay_prefix(line: str) -> str:
    line = ANSI_RE.sub("", line).lstrip()
    while line.startswith("|"):
        line = line[1:].lstrip()
    return line


def _raw_collection_nodes(stdout: str) -> list[str]:
    nodes: list[str] = []
    for raw_line in stdout.splitlines():
        line = _strip_relay_prefix(raw_line).strip()
        if "::" in line and not line.startswith("FAILED "):
            nodes.append(line)
    return nodes


def _normalize_raw_node(node: str, repo: Path | None) -> str | None:
    value = node.strip().replace("\\", "/")
    if repo is not None:
        prefix = repo.as_posix().rstrip("/") + "/"
        if value.startswith(prefix):
            value = value[len(prefix):]
    while value.startswith("./"):
        value = value[2:]
    path_part, separator, test_part = value.partition("::")
    if not separator or not path_part or not test_part:
        return None
    return f"{path_part}::{test_part.strip()}"


def _collection_projection(stdout: str, repo: Path | None) -> tuple[list[str], list[str], dict[str, list[str]]]:
    raw_nodes = _raw_collection_nodes(stdout)
    normalized: list[str] = []
    sources: dict[str, list[str]] = {}
    for node in raw_nodes:
        key = _normalize_raw_node(node, repo)
        if key is None:
            continue
        sources.setdefault(key, []).append(node)
        if key not in normalized:
            normalized.append(key)
    collisions = {
        key: values
        for key, values in sources.items()
        if len(set(values)) > 1
    }
    return raw_nodes, normalized, collisions


def _repo_root_from_identity(ledger: dict[str, Any]) -> Path | None:
    identity = ledger.get("runner_identity")
    path = identity.get("entrypoint_path") if isinstance(identity, dict) else None
    if not isinstance(path, str):
        return None
    candidate = Path(path)
    return candidate.parent.parent if candidate.parent.name == "tools" else None


def _validate_collection(
    value: Any,
    label: str,
    mode: str,
    repo: Path | None,
    gate: Gate,
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    if not _exact_keys(value, COLLECTION_KEYS, label, gate):
        return [], [], {}
    assert isinstance(value, dict)
    gate.require(f"{label}.status == 'PASSED'", value["status"] == "PASSED", f"{label}.status={value['status']!r}")
    gate.require(f"{label}.rc は bool でない int 0", type(value["rc"]) is int and value["rc"] == 0, f"{label}.rc={value['rc']!r}")
    nodes = value["collected_nodes"]
    gate.require(f"{label}.collected_nodes が非空文字列 list", _string_list(nodes) and bool(nodes), f"{label}.collected_nodes が非空文字列 list でない")
    gate.require(f"{label}.duration_s が非負数", _is_number(value["duration_s"]) and value["duration_s"] >= 0, f"{label}.duration_s が非負数でない")
    stdout = _validate_artifact(value["artifact"], f"{label}.artifact", mode, gate)
    if stdout is None:
        return [], [], {}
    raw, normalized, collisions = _collection_projection(stdout, repo)
    gate.require(f"{label} の raw collection stdout に nodeid がある", bool(raw), f"{label}: raw collection stdout に nodeid がない")
    gate.require(f"{label}.collected_nodes が raw stdout の _normalize_node 後順序列と一致", nodes == normalized, f"{label}.collected_nodes が raw stdout の正規化後順序列と不一致")
    return raw, normalized, collisions


def _validate_run_record(value: Any, label: str, expected_keys: set[str], mode: str, gate: Gate) -> None:
    if not _exact_keys(value, expected_keys, label, gate):
        return
    assert isinstance(value, dict)
    gate.require(f"{label}.rc が bool でない int/null", value["rc"] is None or type(value["rc"]) is int, f"{label}.rc の型が不正")
    gate.require(f"{label}.failed_nodes が文字列 list", _string_list(value["failed_nodes"]), f"{label}.failed_nodes が文字列 list でない")
    gate.require(f"{label}.timed_out が bool", isinstance(value["timed_out"], bool), f"{label}.timed_out が bool でない")
    gate.require(f"{label}.duration_s が非負数", _is_number(value["duration_s"]) and value["duration_s"] >= 0, f"{label}.duration_s が非負数でない")
    gate.require(f"{label}.artifact_error が string/null", value["artifact_error"] is None or isinstance(value["artifact_error"], str), f"{label}.artifact_error の型が不正")
    gate.require(f"{label}.test_output_tail が文字列 list", _string_list(value["test_output_tail"]), f"{label}.test_output_tail が文字列 list でない")
    stdout = _validate_artifact(value["artifact"], f"{label}.artifact", mode, gate)
    if stdout is not None:
        digest = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
        gate.require(f"{label}.test_output_sha256 が実 stdout bytes と一致", value["test_output_sha256"] == digest, f"{label}.test_output_sha256 が実 stdout bytes と不一致")


def _validate_ledger(
    ledger: dict[str, Any],
    label: str,
    expected_mode: str,
    expected_head: str,
    actual_spec_sha256: str | None,
    gate: Gate,
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    if not _exact_keys(ledger, TOP_KEYS, label, gate):
        return [], [], {}
    gate.require(f"{label}.schema == LEDGER_SCHEMA ({LEDGER_SCHEMA})", ledger["schema"] == LEDGER_SCHEMA, f"{label}.schema={ledger['schema']!r}")
    gate.require(f"{label}.repo_head == expected anchor {expected_head}", ledger["repo_head"] == expected_head, f"{label}.repo_head={ledger['repo_head']!r}")
    if actual_spec_sha256 is not None:
        gate.require(f"{label}.spec_sha256 == 実 spec file SHA-256", ledger["spec_sha256"] == actual_spec_sha256, f"{label}.spec_sha256={ledger['spec_sha256']!r}, actual={actual_spec_sha256}")

    runner = ledger["runner_identity"]
    if _exact_keys(runner, RUNNER_IDENTITY_KEYS, f"{label}.runner_identity", gate):
        assert isinstance(runner, dict)
        gate.require(f"{label}.runner_sha256 が runner_identity の実 hash", ledger["runner_sha256"] == _json_sha256(runner), f"{label}.runner_sha256 が runner_identity の実 hash と不一致")
        gate.require(f"{label}.runner_identity.runner_mode == {expected_mode!r}", runner["runner_mode"] == expected_mode, f"{label}.runner_identity.runner_mode={runner['runner_mode']!r}")
        gate.require(f"{label}.runner_identity.command が非空文字列 list", _string_list(runner["command"]) and bool(runner["command"]), f"{label}.runner_identity.command が非空文字列 list でない")
        for key in ("entrypoint_sha256", "pytest_distribution_sha256", "repo_tree"):
            validator = _is_sha256 if key != "repo_tree" else lambda value: isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None
            gate.require(f"{label}.runner_identity.{key} が正規 hash", validator(runner[key]), f"{label}.runner_identity.{key} が正規 hash でない")
        gate.require(f"{label}.runner_identity.entrypoint_kind が文字列", isinstance(runner["entrypoint_kind"], str), f"{label}.runner_identity.entrypoint_kind が文字列でない")
        if expected_mode == "dispatch":
            for key in ("dispatch_entrypoint_path", "dispatch_entrypoint_sha256", "dispatch_head_blob_sha256"):
                accepted = isinstance(runner[key], str) and bool(runner[key]) if key.endswith("path") else _is_sha256(runner[key])
                gate.require(f"{label}.runner_identity.{key} が dispatch identity", accepted, f"{label}.runner_identity.{key} が dispatch identity でない")
        else:
            for key in ("dispatch_entrypoint_path", "dispatch_entrypoint_sha256", "dispatch_head_blob_sha256"):
                gate.require(f"{label}.runner_identity.{key} が local 経路では null", runner[key] is None, f"{label}.runner_identity.{key} が local 経路で null でない")

    tool = ledger["tool_identity"]
    if _exact_keys(tool, TOOL_IDENTITY_KEYS, f"{label}.tool_identity", gate):
        assert isinstance(tool, dict)
        gate.require(f"{label}.tool_sha256 が tool_identity の実 hash", ledger["tool_sha256"] == _json_sha256(tool), f"{label}.tool_sha256 が tool_identity の実 hash と不一致")
        gate.require(f"{label}.tool_identity.sha256 が SHA-256", _is_sha256(tool["sha256"]), f"{label}.tool_identity.sha256 が SHA-256 でない")
        gate.require(f"{label}.tool_identity.head_blob_sha256 == tool_identity.sha256", tool["head_blob_sha256"] == tool["sha256"], f"{label}.tool HEAD blob/hash が不一致")

    procedure = ledger["procedure"]
    if not _exact_keys(procedure, PROCEDURE_KEYS, f"{label}.procedure", gate):
        return [], [], {}
    assert isinstance(procedure, dict)
    gate.require(f"{label}.procedure.runner_mode == {expected_mode!r}", procedure["runner_mode"] == expected_mode, f"{label}.procedure.runner_mode={procedure['runner_mode']!r}")
    gate.require(f"{label}.procedure.test_command == runner_identity.command", isinstance(runner, dict) and procedure["test_command"] == runner.get("command"), f"{label}.procedure.test_command と runner_identity.command が不一致")
    for key in ("timeout_seconds", "hang_timeout_seconds"):
        gate.require(f"{label}.procedure.{key} が正数", _is_number(procedure[key]) and procedure[key] > 0, f"{label}.procedure.{key} が正数でない")
    registration = procedure["registration_preflight"]
    gate.require(f"{label}.procedure.registration_preflight が object", isinstance(registration, dict), f"{label}.procedure.registration_preflight が object でない")
    if isinstance(registration, dict):
        gate.require(f"{label}.procedure.registration_sha256 が registration_preflight の実 hash", procedure["registration_sha256"] == _json_sha256(registration), f"{label}.procedure.registration_sha256 が実 hash と不一致")
    raw, normalized, collisions = _validate_collection(procedure["collection"], f"{label}.procedure.collection", expected_mode, _repo_root_from_identity(ledger), gate)
    collection = procedure["collection"]
    if isinstance(collection, dict):
        for key, expected in (
            ("repo_head", ledger["repo_head"]),
            ("spec_sha256", ledger["spec_sha256"]),
            ("runner_sha256", ledger["runner_sha256"]),
            ("tool_sha256", ledger["tool_sha256"]),
        ):
            gate.require(f"{label}.procedure.collection.{key} == top-level {key}", collection.get(key) == expected, f"{label}.procedure.collection.{key} が top-level と不一致")
    collection_sha256 = _json_sha256(collection) if isinstance(collection, dict) else None

    baseline = ledger["baseline"]
    _validate_run_record(baseline, f"{label}.baseline", BASELINE_KEYS, expected_mode, gate)
    if isinstance(baseline, dict):
        gate.require(f"{label}.baseline.status == 'PASSED'", baseline.get("status") == "PASSED", f"{label}.baseline.status={baseline.get('status')!r}")
        gate.require(f"{label}.baseline.rc は bool でない int 0", type(baseline.get("rc")) is int and baseline["rc"] == 0, f"{label}.baseline.rc={baseline.get('rc')!r}")
        gate.require(f"{label}.baseline.failed_nodes == []", baseline.get("failed_nodes") == [], f"{label}.baseline.failed_nodes={baseline.get('failed_nodes')!r}")
        gate.require(f"{label}.baseline.timed_out is false", baseline.get("timed_out") is False, f"{label}.baseline.timed_out={baseline.get('timed_out')!r}")
        gate.require(f"{label}.baseline.artifact_error is null", baseline.get("artifact_error") is None, f"{label}.baseline.artifact_error={baseline.get('artifact_error')!r}")
        for key, expected in (
            ("repo_head", ledger["repo_head"]),
            ("spec_sha256", ledger["spec_sha256"]),
            ("runner_sha256", ledger["runner_sha256"]),
            ("tool_sha256", ledger["tool_sha256"]),
            ("collection_sha256", collection_sha256),
        ):
            gate.require(f"{label}.baseline.{key} が同じ ledger の evidence binding と一致", baseline.get(key) == expected, f"{label}.baseline.{key} が同じ ledger の evidence binding と不一致")

    mutations = ledger["mutations"]
    gate.require(f"{label}.mutations が非空 list", isinstance(mutations, list) and bool(mutations), f"{label}.mutations が非空 list でない")
    if isinstance(mutations, list):
        for index, record in enumerate(mutations):
            record_label = f"{label}.mutations[{index}]"
            _validate_run_record(record, record_label, MUTATION_KEYS, expected_mode, gate)
            if not isinstance(record, dict):
                continue
            gate.require(f"{record_label}.id が非空文字列", isinstance(record.get("id"), str) and bool(record["id"]), f"{record_label}.id が非空文字列でない")
            gate.require(f"{record_label}.matches_expectation is true", record.get("matches_expectation") is True, f"{record_label}.matches_expectation={record.get('matches_expectation')!r}")
            gate.require(f"{record_label}.expected_status == status", record.get("expected_status") == record.get("status"), f"{record_label}: expected_status/status が不一致")
            gate.require(f"{record_label}.expected_nodes/failed_nodes が文字列 list", _string_list(record.get("expected_nodes")) and _string_list(record.get("failed_nodes")), f"{record_label}: node field の型が不正")
            gate.require(f"{record_label}.category が文字列", isinstance(record.get("category"), str), f"{record_label}.category が文字列でない")
            gate.require(f"{record_label}.hang_risk が bool", isinstance(record.get("hang_risk"), bool), f"{record_label}.hang_risk が bool でない")
            gate.require(f"{record_label}.anchor_counts が object", isinstance(record.get("anchor_counts"), dict), f"{record_label}.anchor_counts が object でない")
            gate.require(f"{record_label}.injection_diff_sha256 が SHA-256", _is_sha256(record.get("injection_diff_sha256")), f"{record_label}.injection_diff_sha256 が SHA-256 でない")
            _validate_replacements(record.get("replacements"), f"{record_label}.replacements", gate)
            for key, expected in (
                ("repo_head", ledger["repo_head"]),
                ("spec_sha256", ledger["spec_sha256"]),
                ("runner_sha256", ledger["runner_sha256"]),
                ("tool_sha256", ledger["tool_sha256"]),
                ("collection_sha256", collection_sha256),
            ):
                gate.require(f"{record_label}.{key} が同じ ledger の evidence binding と一致", record.get(key) == expected, f"{record_label}.{key} が同じ ledger の evidence binding と不一致")

    gate.require(f"{label}.summary が object", isinstance(ledger["summary"], dict), f"{label}.summary が object でない")
    gate.require(f"{label}.nonterminal_history == []", ledger["nonterminal_history"] == [], f"{label}.nonterminal_history={ledger['nonterminal_history']!r}")
    return raw, normalized, collisions


def _validate_spec(spec: dict[str, Any], gate: Gate) -> list[dict[str, Any]]:
    if not _exact_keys(spec, SPEC_KEYS, "spec", gate):
        return []
    gate.require(f"spec.schema == SPEC_SCHEMA ({SPEC_SCHEMA})", spec["schema"] == SPEC_SCHEMA, f"spec.schema={spec['schema']!r}")
    for key in ("estimated_run_seconds", "timeout_seconds", "hang_timeout_seconds"):
        gate.require(f"spec.{key} が正数", _is_number(spec[key]) and spec[key] > 0, f"spec.{key} が正数でない")
    mutations = spec["mutations"]
    gate.require("spec.mutations が非空 list", isinstance(mutations, list) and bool(mutations), "spec.mutations が空または list でない")
    records: list[dict[str, Any]] = []
    if not isinstance(mutations, list):
        return records
    for index, mutation in enumerate(mutations):
        label = f"spec.mutations[{index}]"
        if not _exact_keys(mutation, SPEC_MUTATION_KEYS, label, gate):
            continue
        assert isinstance(mutation, dict)
        gate.require(f"{label}.id が非空文字列", isinstance(mutation["id"], str) and bool(mutation["id"]), f"{label}.id が非空文字列でない")
        gate.require(f"{label}.expected_nodes が非空文字列 list", _string_list(mutation["expected_nodes"]) and bool(mutation["expected_nodes"]), f"{label}.expected_nodes が非空文字列 list でない")
        gate.require(f"{label}.category/expected_status が文字列", isinstance(mutation["category"], str) and isinstance(mutation["expected_status"], str), f"{label}.category/expected_status の型が不正")
        gate.require(f"{label}.hang_risk が bool", isinstance(mutation["hang_risk"], bool), f"{label}.hang_risk が bool でない")
        _validate_replacements(mutation["replacements"], f"{label}.replacements", gate)
        records.append(mutation)
    ids = [item["id"] for item in records if isinstance(item.get("id"), str)]
    gate.require("spec mutation ID 列に重複がない", len(ids) == len(set(ids)), f"spec mutation ID 列が重複: {ids}")
    return records


def _validate_spec_projection(
    ledger: dict[str, Any],
    label: str,
    spec_mutations: list[dict[str, Any]],
    spec: dict[str, Any],
    gate: Gate,
) -> None:
    raw_records = ledger.get("mutations")
    records = raw_records if isinstance(raw_records, list) else []
    spec_ids = [item["id"] for item in spec_mutations]
    ledger_ids = [item.get("id") if isinstance(item, dict) else None for item in records]
    gate.require(f"{label} mutation ID 順序列 == spec ID 順序列", ledger_ids == spec_ids, f"{label}: mutation ID 順序列が spec と不一致: ledger={ledger_ids}, spec={spec_ids}")
    gate.require(f"{label} record 数 == spec 件数", len(records) == len(spec_mutations), f"{label}: record 数={len(records)}, spec={len(spec_mutations)}")
    procedure = ledger.get("procedure")
    if isinstance(procedure, dict):
        gate.require(f"{label}.procedure.timeout_seconds == spec.timeout_seconds", procedure.get("timeout_seconds") == spec.get("timeout_seconds"), f"{label}: timeout_seconds が spec と不一致")
        gate.require(f"{label}.procedure.hang_timeout_seconds == spec.hang_timeout_seconds", procedure.get("hang_timeout_seconds") == spec.get("hang_timeout_seconds"), f"{label}: hang_timeout_seconds が spec と不一致")
    registration = procedure.get("registration_preflight") if isinstance(procedure, dict) else None
    for index, expected in enumerate(spec_mutations):
        if index >= len(records) or not isinstance(records[index], dict):
            continue
        record = records[index]
        mutation_id = expected["id"]
        for key in ("id", "expected_status", "expected_nodes", "category", "hang_risk", "replacements"):
            gate.require(f"{label}.mutations[{index}].{key} == spec.{mutation_id}.{key}", record.get(key) == expected.get(key), f"{label}.mutations[{index}].{key} が spec と不一致")
        preflight = registration.get(mutation_id) if isinstance(registration, dict) else None
        if not _exact_keys(preflight, REGISTRATION_KEYS, f"{label}.registration_preflight.{mutation_id}", gate):
            continue
        assert isinstance(preflight, dict)
        for key in ("expected_status", "expected_nodes", "replacements"):
            gate.require(f"{label}.registration_preflight.{mutation_id}.{key} == spec", preflight[key] == expected[key], f"{label}.registration_preflight.{mutation_id}.{key} が spec と不一致")
        for key in ("anchor_counts", "injection_diff_sha256"):
            gate.require(f"{label}.mutations[{index}].{key} == registration_preflight.{mutation_id}.{key}", record.get(key) == preflight[key], f"{label}.mutations[{index}].{key} が registration preflight と不一致")
        gate.require(f"{label}.mutations[{index}].registration_sha256 が mutation preflight の実 hash", record.get("registration_sha256") == _json_sha256(preflight), f"{label}.mutations[{index}].registration_sha256 が実 hash と不一致")
    baseline = ledger.get("baseline")
    if isinstance(baseline, dict) and isinstance(registration, dict):
        gate.require(f"{label}.baseline.registration_sha256 が全 registration_preflight の実 hash", baseline.get("registration_sha256") == _json_sha256(registration), f"{label}.baseline.registration_sha256 が実 hash と不一致")


def _matching_exclusion(path: tuple[str | int, ...]) -> Exclusion | None:
    for exclusion in EXCLUSIONS:
        if len(path) != len(exclusion.pattern):
            continue
        if all(expected == "*" or expected == str(actual) for actual, expected in zip(path, exclusion.pattern)):
            return exclusion
    return None


def _walk_differences(left: Any, right: Any, path: tuple[str | int, ...] = ()) -> list[Difference]:
    exclusion = _matching_exclusion(path)
    if exclusion is not None:
        return [] if left == right else [Difference(path, left, right, exclusion)]
    if type(left) is not type(right):
        return [Difference(path, left, right, None)]
    if isinstance(left, dict):
        differences: list[Difference] = []
        for key in sorted(set(left) | set(right)):
            if key not in left:
                differences.append(Difference((*path, key), "<missing>", right[key], _matching_exclusion((*path, key))))
            elif key not in right:
                differences.append(Difference((*path, key), left[key], "<missing>", _matching_exclusion((*path, key))))
            else:
                differences.extend(_walk_differences(left[key], right[key], (*path, key)))
        return differences
    if isinstance(left, list):
        differences = []
        if len(left) != len(right):
            differences.append(Difference((*path, "length"), len(left), len(right), None))
        for index, (item1, item2) in enumerate(zip(left, right)):
            differences.extend(_walk_differences(item1, item2, (*path, index)))
        return differences
    return [] if left == right else [Difference(path, left, right, None)]


def _path_text(path: tuple[str | int, ...] | tuple[str, ...]) -> str:
    text = "$"
    for part in path:
        if isinstance(part, int) or part == "*":
            text += f"[{part}]"
        else:
            text += f".{part}"
    return text


def _short(value: Any) -> str:
    if isinstance(value, str) and len(value) > 120:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return f"<string bytes={len(value.encode('utf-8'))} sha256={digest}>"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _print_collision_report(label: str, raw: list[str], normalized: list[str], collisions: dict[str, list[str]]) -> None:
    print(f"- {label}: raw_nodeids={len(raw)}, normalized_deduplicated_keys={len(normalized)}, loss={len(raw) - len(normalized)}")
    if not collisions:
        print("  collision: なし")
        return
    for key, values in sorted(collisions.items()):
        print(f"  collision key={_short(key)} <- {_short(values)}")


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=here / "spec.json")
    parser.add_argument("--leg1", type=Path, default=here / "leg1-ledger.json")
    parser.add_argument("--leg2", type=Path, default=here / "leg2-ledger.json")
    parser.add_argument("--expected-repo-head", default=DEFAULT_ANCHOR)
    parser.add_argument("--leg1-runner-mode", choices=("dispatch", "local"), default="dispatch")
    parser.add_argument("--leg2-runner-mode", choices=("dispatch", "local"), default="local")
    args = parser.parse_args(argv)

    gate = Gate()
    spec, spec_bytes = _load_json(args.spec, "spec", gate)
    leg1, _ = _load_json(args.leg1, "leg1", gate)
    leg2, _ = _load_json(args.leg2, "leg2", gate)
    actual_spec_sha256 = hashlib.sha256(spec_bytes).hexdigest() if spec_bytes is not None else None

    spec_mutations = _validate_spec(spec, gate) if spec is not None else []
    raw1: list[str] = []
    normalized1: list[str] = []
    collisions1: dict[str, list[str]] = {}
    raw2: list[str] = []
    normalized2: list[str] = []
    collisions2: dict[str, list[str]] = {}
    if leg1 is not None:
        raw1, normalized1, collisions1 = _validate_ledger(leg1, "leg1", args.leg1_runner_mode, args.expected_repo_head, actual_spec_sha256, gate)
        if spec is not None:
            _validate_spec_projection(leg1, "leg1", spec_mutations, spec, gate)
    if leg2 is not None:
        raw2, normalized2, collisions2 = _validate_ledger(leg2, "leg2", args.leg2_runner_mode, args.expected_repo_head, actual_spec_sha256, gate)
        if spec is not None:
            _validate_spec_projection(leg2, "leg2", spec_mutations, spec, gate)

    differences: list[Difference] = []
    same_executable_path = False
    if leg1 is not None and leg2 is not None:
        differences = _walk_differences(leg1, leg2)
        runner1 = leg1.get("runner_identity")
        runner2 = leg2.get("runner_identity")
        executable_path1 = runner1.get("executable_path") if isinstance(runner1, dict) else None
        executable_path2 = runner2.get("executable_path") if isinstance(runner2, dict) else None
        same_executable_path = (
            isinstance(executable_path1, str)
            and isinstance(executable_path2, str)
            and executable_path1 == executable_path2
        )
        gate.require(
            "両 ledger の runner_identity.executable_path（解決済み Python path）が完全一致",
            same_executable_path,
            f"runner_identity.executable_path が不一致: leg1={executable_path1!r}, leg2={executable_path2!r}",
        )
        command1 = runner1.get("command") if isinstance(runner1, dict) else None
        command2 = runner2.get("command") if isinstance(runner2, dict) else None
        gate.require(
            "両 ledger の runner_identity.command[1:]（pytest 引数列）が完全一致",
            _string_list(command1) and _string_list(command2) and command1[1:] == command2[1:],
            "runner_identity.command[1:]（pytest 引数列）が不一致",
        )
        procedure1 = leg1.get("procedure")
        procedure2 = leg2.get("procedure")
        test_command1 = procedure1.get("test_command") if isinstance(procedure1, dict) else None
        test_command2 = procedure2.get("test_command") if isinstance(procedure2, dict) else None
        gate.require(
            "両 ledger の procedure.test_command[1:]（pytest 引数列）が完全一致",
            _string_list(test_command1) and _string_list(test_command2) and test_command1[1:] == test_command2[1:],
            "procedure.test_command[1:]（pytest 引数列）が不一致",
        )
        semantic = [
            difference
            for difference in differences
            if difference.exclusion is None
            and not (
                same_executable_path
                and difference.path in COMMAND_EXECUTABLE_PATHS
            )
        ]
        gate.require("両 ledger の非除外 field が全て再帰的に完全一致", not semantic, f"非除外 field に {len(semantic)} 件の非等価差分")
        gate.require("collection.collected_nodes の件数・内容・重複度・順序が完全一致", normalized1 == normalized2, f"collection.collected_nodes が順序付きで不一致: leg1={len(normalized1)}, leg2={len(normalized2)}")
        gate.require("collection raw stdout の nodeid 件数・内容・重複度・順序が完全一致", raw1 == raw2, f"collection raw stdout nodeid 列が不一致: leg1={len(raw1)}, leg2={len(raw2)}")

    print("判定に使った条件（実際に評価した gate から導出）:")
    for condition in gate.conditions:
        print(f"- {condition}")
    print("cross-ledger 完全一致から除外した field（再帰比較が参照する policy から導出）:")
    for exclusion in EXCLUSIONS:
        print(f"- {_path_text(exclusion.pattern)}: {exclusion.reason}")
    print("注: 除外 field も型・実 hash・leg 固有 route 契約の対象になり、実データで差があれば下に全件表示する。")

    print("_normalize_node 衝突監査:")
    print("- ledger.collected_nodes は _normalize_node 後に順序を保って重複除去された key であり、生 nodeid 件数とは限らない。")
    print("- _normalize_node は nodeid 全体の backslash を slash に変えるため、parameter id も衝突しうる。")
    _print_collision_report("leg1", raw1, normalized1, collisions1)
    _print_collision_report("leg2", raw2, normalized2, collisions2)

    print("実データで一致しなかった field（完全一覧）:")
    if not differences:
        print("- なし")
    for difference in differences:
        if difference.path in COMMAND_EXECUTABLE_PATHS and same_executable_path:
            classification = "同一実体の別綴り"
            reason = "raw command[0] は異なるが runner_identity.executable_path が一致するため verdict に効かない"
        elif difference.exclusion is None:
            classification = "非等価性"
            reason = "意味論的一致を要求する非除外 field。合否は NO-GO"
        else:
            classification = "経路差"
            reason = difference.exclusion.reason
        print(f"- {_path_text(difference.path)}: {classification}; {reason}; leg1={_short(difference.leg1)}, leg2={_short(difference.leg2)}")

    command_differences = [difference for difference in differences if difference.path in COMMAND_EXECUTABLE_PATHS]
    print("Python command path の判断:")
    if command_differences and same_executable_path:
        print("- raw command[0] の差は同一実体の別綴り。根拠は両 ledger の解決済み runner_identity.executable_path が一致すること。")
        print("- raw command[0] の差は上の完全一覧に残し、command[1:]（pytest 引数列）は従来どおり厳密一致を要求する。")
    elif command_differences:
        print("- raw command[0] が異なり、runner_identity.executable_path も一致しないため非等価性として NO-GO。")
    else:
        print("- command[0] の差は観測されなかった。")
        print("- runner_identity.executable_path は raw command[0] と独立に完全一致を要求する。")

    executable_sha256_difference = next(
        (difference for difference in differences if difference.path == RUNNER_EXECUTABLE_SHA256_PATH),
        None,
    )
    print("Python interpreter bytes の名前付き観測（verdict 非関与）:")
    if executable_sha256_difference is None:
        print("- runner_identity.executable_sha256 の非等価差は観測されなかった。")
    else:
        print(
            "- 非等価だが verdict に効かない: runner_identity.executable_sha256; "
            f"leg1={_short(executable_sha256_difference.leg1)}, "
            f"leg2={_short(executable_sha256_difference.leg2)}"
        )
    print("- 含意: leg1 (dispatch) の runner_identity は login node の interpreter を記録している。実際に pytest を走らせたのは計算ノードである。leg2 (束ね) は実際の runner を記録している。")

    if gate.failures:
        print("NO-GO")
        print("合否差分:")
        for failure in gate.failures:
            print(f"- {failure}")
        return 1
    print("GO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
