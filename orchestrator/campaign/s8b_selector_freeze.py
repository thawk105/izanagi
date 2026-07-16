# -*- coding: utf-8 -*-
"""段 8b selector の予測計画と oracle 非依存 prediction freeze。

このモジュールは selector を実行しない。``plan`` は固定 job の表示だけを行い、
``verify`` は既存 prediction freeze を信頼済み holdout freeze に再束縛する。
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    _ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
    if str(_ROOT_FOR_IMPORT) not in sys.path:
        sys.path.insert(0, str(_ROOT_FOR_IMPORT))
    from orchestrator.campaign.s8b_descriptor import descriptor_for_holdout
    from orchestrator.campaign.s8b_selector_input import (
        CHOICE_TO_BINDING,
        STATIC_DEFAULT_CHOICE_ID,
        build_selector_payload,
        selector_payload_sha256,
    )
    from orchestrator.campaign.s8b_selector_output import (
        SelectorOutputError,
        parse_selector_output,
    )
else:
    from .s8b_descriptor import descriptor_for_holdout
    from .s8b_selector_input import (
        CHOICE_TO_BINDING,
        STATIC_DEFAULT_CHOICE_ID,
        build_selector_payload,
        selector_payload_sha256,
    )
    from .s8b_selector_output import SelectorOutputError, parse_selector_output


ROOT = Path(__file__).resolve().parents[2]
HOLDOUT_FREEZE_PATH = ROOT / "output/s8b-freeze/holdout_freeze.json"
PREDICTION_FREEZE_PATH = ROOT / "output/s8b-freeze/selector_predictions.json"

SCHEMA_VERSION = "8b-selector-prediction-freeze/v1"
ARMS = ("on", "off", "swapped")
AGENT_DECISION_METHOD = "selector_agent"
STATIC_DECISION_METHOD = "static_default"
STATIC_DEFAULT_RULE_VERSION = "stock-common-v1"

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_SHA_RE = re.compile(r"[0-9a-f]{40}")
_SOURCE_KEYS = {
    "holdout_freeze", "builder", "role", "input_schema", "output_schema",
}
_EXECUTION_POLICY = {
    "attempts_per_agent_cell": 1,
    "retry": False,
    "reuse_equal_payload_output": False,
    "fresh_context": True,
    "declared_tools": [],
}
_DOCUMENT_KEYS = {
    "schema_version", "generated_at", "pre_oracle_head", "sources",
    "selector_basis_sha256", "execution_policy", "static_default",
    "derangement", "rows", "swapped_follow_expectations", "body_sha256",
}
_ROW_KEYS = {
    "target_holdout", "arm", "descriptor_source_holdout", "decision_method",
    "status", "choice_id", "binding_key", "binding_entry_sha256", "rationale",
    "input_payload_sha256", "raw_response_path", "raw_sha256",
    "parser_error_code", "agent_provenance",
}
_ROW_REQUIRED_INPUT_KEYS = {
    "target_holdout", "arm", "descriptor_source_holdout", "decision_method",
    "status", "choice_id", "input_payload_sha256",
}
_AGENT_PROVENANCE_KEYS = {
    "child_id", "role_file_sha256", "model", "started_at", "finished_at",
    "fresh_context", "declared_tools", "observed_tool_events",
}


class SelectorFreezeError(RuntimeError):
    """prediction freeze の構築・照合契約に対する fail-closed 拒否。"""


def _canonical_bytes(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise SelectorFreezeError("canonical JSON に変換できない") from exc
    return rendered.encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_string(value: Any, *, field: str, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise SelectorFreezeError(f"{field} は64桁 lowercase SHA-256でなければならない")
    return value


def _nonempty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelectorFreezeError(f"{field} は空でない文字列でなければならない")
    return value


def _file_sha256(path: Path, *, field: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise SelectorFreezeError(f"{field} の実ファイルを読めない: {path}: {exc}") from exc


def _root_file(path_text: str, *, root: Path, field: str) -> Path:
    root = Path(root)
    try:
        trusted_root = root.resolve(strict=True)
        recorded = Path(path_text)
        candidate = recorded if recorded.is_absolute() else trusted_root / recorded
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise SelectorFreezeError(f"{field} が存在する root 配下ファイルでない: {exc}") from exc
    if not resolved.is_relative_to(trusted_root) or not resolved.is_file():
        raise SelectorFreezeError(f"{field} が root 配下の通常ファイルでない: {resolved}")
    return resolved


def _verify_file_record(record: Mapping, *, root: Path, field: str) -> None:
    path = _root_file(record["path"], root=root, field=f"{field}.path")
    actual = _file_sha256(path, field=field)
    if actual != record["sha256"]:
        raise SelectorFreezeError(f"{field}.sha256 が実ファイルと不一致")


def _timestamp(value: Any, *, field: str) -> tuple[str, dt.datetime]:
    rendered = _nonempty_string(value, field=field)
    try:
        parsed = dt.datetime.fromisoformat(rendered.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SelectorFreezeError(f"{field} が ISO-8601 時刻でない") from exc
    if parsed.tzinfo is None:
        raise SelectorFreezeError(f"{field} に timezone がない")
    return rendered, parsed


def _validate_agent_provenance(
    provenance: Any, *, field: str, role_file_sha256: str,
) -> dict:
    if not isinstance(provenance, Mapping) or set(provenance) != _AGENT_PROVENANCE_KEYS:
        raise SelectorFreezeError(
            f"{field} schema が不一致: expected={sorted(_AGENT_PROVENANCE_KEYS)}"
        )
    projected = dict(provenance)
    for key in ("child_id", "model"):
        projected[key] = _nonempty_string(projected[key], field=f"{field}.{key}")
    projected["role_file_sha256"] = _sha256_string(
        projected["role_file_sha256"], field=f"{field}.role_file_sha256",
    )
    if projected["role_file_sha256"] != role_file_sha256:
        raise SelectorFreezeError(f"{field}.role_file_sha256 が sources.role.sha256 と不一致")
    projected["started_at"], started = _timestamp(
        projected["started_at"], field=f"{field}.started_at",
    )
    projected["finished_at"], finished = _timestamp(
        projected["finished_at"], field=f"{field}.finished_at",
    )
    if finished < started:
        raise SelectorFreezeError(f"{field} の開始・終了時刻順が逆")
    if projected["fresh_context"] is not True:
        raise SelectorFreezeError(f"{field}.fresh_context は true 固定")
    if projected["declared_tools"] != []:
        raise SelectorFreezeError(f"{field}.declared_tools は [] 固定")
    if projected["observed_tool_events"] != []:
        raise SelectorFreezeError(f"{field}.observed_tool_events は [] 固定")
    return copy.deepcopy(projected)


def _freeze_axes(freeze: Mapping) -> tuple[Mapping, Mapping, tuple[str, ...]]:
    if not isinstance(freeze, Mapping):
        raise SelectorFreezeError("holdout freeze は object でなければならない")
    holdouts = freeze.get("holdouts")
    derangement = freeze.get("derangement")
    if not isinstance(holdouts, Mapping) or len(holdouts) != 2:
        raise SelectorFreezeError("holdout freeze はちょうど2 holdout を持たなければならない")
    if not all(isinstance(target, str) and target for target in holdouts):
        raise SelectorFreezeError("holdout ID は空でない文字列でなければならない")
    targets = tuple(sorted(holdouts))
    if not all(isinstance(holdouts[target], Mapping) for target in targets):
        raise SelectorFreezeError("各 holdout entry は object でなければならない")
    if not isinstance(derangement, Mapping) or set(derangement) != set(targets):
        raise SelectorFreezeError("derangement の target 集合が holdout と一致しない")
    if not all(isinstance(source, str) for source in derangement.values()):
        raise SelectorFreezeError("derangement の source は holdout ID 文字列でなければならない")
    if set(derangement.values()) != set(targets):
        raise SelectorFreezeError("derangement の source 集合が holdout と一致しない")
    if any(derangement[target] == target for target in targets):
        raise SelectorFreezeError("derangement に固定点がある")
    return holdouts, derangement, targets


def build_prediction_jobs(freeze: Mapping) -> list[dict]:
    """検証済み freeze から2 holdout × 3 armを決定論的に列挙する。"""
    holdouts, derangement, targets = _freeze_axes(freeze)
    jobs: list[dict] = []
    for target in targets:
        for arm in ARMS:
            if arm == "off":
                jobs.append({
                    "target_holdout": target,
                    "arm": arm,
                    "descriptor_source_holdout": None,
                    "decision_method": STATIC_DECISION_METHOD,
                    "input_payload_sha256": None,
                    "choice_id": STATIC_DEFAULT_CHOICE_ID,
                })
                continue
            source = target if arm == "on" else derangement[target]
            descriptor = descriptor_for_holdout(holdouts[source])
            payload = build_selector_payload(descriptor)
            jobs.append({
                "target_holdout": target,
                "arm": arm,
                "descriptor_source_holdout": source,
                "decision_method": AGENT_DECISION_METHOD,
                "input_payload_sha256": selector_payload_sha256(payload),
                "choice_id": None,
            })
    return jobs


def selector_basis_sha256(freeze: Mapping) -> str:
    """floor/budget と独立な workload・binding・catalog 対応の部分 hash。"""
    holdouts, derangement, targets = _freeze_axes(freeze)
    basis_holdouts = {}
    for target in targets:
        entry = holdouts[target]
        missing = {"ycsb", "records", "threads", "variant_binding"} - set(entry)
        if missing:
            raise SelectorFreezeError(
                f"holdouts.{target} の selector basis field が不足: {sorted(missing)}"
            )
        basis_holdouts[target] = {
            "workload": {
                "ycsb": copy.deepcopy(entry["ycsb"]),
                "records": copy.deepcopy(entry["records"]),
                "threads": copy.deepcopy(entry["threads"]),
            },
            "variant_binding": copy.deepcopy(entry["variant_binding"]),
        }
    basis = {
        "holdouts": basis_holdouts,
        "derangement": copy.deepcopy(dict(derangement)),
        "choice_to_binding": copy.deepcopy(CHOICE_TO_BINDING),
    }
    return _canonical_sha256(basis)


def binding_entry_for_choice(
    freeze: Mapping, target_holdout: str, choice_id: str,
) -> dict:
    """opaque choice ID を target 側の trusted variant binding へ解決する。"""
    holdouts, _, _ = _freeze_axes(freeze)
    if not isinstance(choice_id, str) or choice_id not in CHOICE_TO_BINDING:
        raise SelectorFreezeError(f"unknown selector choice_id: {choice_id!r}")
    if target_holdout not in holdouts:
        raise SelectorFreezeError(f"unknown target_holdout: {target_holdout!r}")
    binding = holdouts[target_holdout].get("variant_binding")
    entries = binding.get("entries") if isinstance(binding, Mapping) else None
    binding_key = CHOICE_TO_BINDING[choice_id]
    entry = entries.get(binding_key) if isinstance(entries, Mapping) else None
    if not isinstance(entry, Mapping):
        raise SelectorFreezeError(
            f"target binding entry がない: target={target_holdout!r} key={binding_key!r}"
        )
    return copy.deepcopy(dict(entry))


def record_agent_attempt(*, job: Mapping, raw_output: str) -> dict:
    """agent の単一 raw 出力を記録し、不正出力へ fallback しない。"""
    if not isinstance(job, Mapping) or job.get("decision_method") != AGENT_DECISION_METHOD:
        raise SelectorFreezeError("record_agent_attempt は selector_agent job 専用")
    if job.get("arm") not in {"on", "swapped"}:
        raise SelectorFreezeError("record_agent_attempt の arm が agent cell でない")
    if not isinstance(raw_output, str):
        raise SelectorFreezeError("raw_output は str でなければならない")
    raw_sha256 = hashlib.sha256(raw_output.encode("utf-8")).hexdigest()
    try:
        decision = parse_selector_output(raw_output)
    except SelectorOutputError as exc:
        return {
            "status": "invalid",
            "choice_id": None,
            "parser_error_code": exc.code,
            "raw_sha256": raw_sha256,
        }
    if decision.raw_sha256 != raw_sha256:
        raise SelectorFreezeError("selector parser の raw_sha256 が collector と不一致")
    return {
        "status": "valid",
        "choice_id": decision.choice_id,
        "rationale": decision.rationale,
        "raw_sha256": raw_sha256,
    }


def _validate_sources(sources: Any) -> dict:
    if not isinstance(sources, Mapping) or set(sources) != _SOURCE_KEYS:
        raise SelectorFreezeError(
            f"sources schema が不一致: expected={sorted(_SOURCE_KEYS)}"
        )
    projected = {}
    for name in sorted(_SOURCE_KEYS):
        record = sources[name]
        if not isinstance(record, Mapping) or set(record) != {"path", "sha256"}:
            raise SelectorFreezeError(f"sources.{name} は path/sha256 object でなければならない")
        projected[name] = {
            "path": _nonempty_string(record["path"], field=f"sources.{name}.path"),
            "sha256": _sha256_string(record["sha256"], field=f"sources.{name}.sha256"),
        }
    return projected


def _validate_execution_policy(execution_policy: Any) -> dict:
    if not isinstance(execution_policy, Mapping) or dict(execution_policy) != _EXECUTION_POLICY:
        raise SelectorFreezeError(
            "execution_policy は1回・再試行なし・出力再利用なし・fresh・toolsなし固定"
        )
    return copy.deepcopy(_EXECUTION_POLICY)


def _normalise_rows(
    freeze: Mapping, rows: Any, *, role_file_sha256: str,
) -> list[dict]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise SelectorFreezeError("rows は配列でなければならない")
    jobs = build_prediction_jobs(freeze)
    expected = {(job["target_holdout"], job["arm"]): job for job in jobs}
    if len(rows) != len(expected):
        raise SelectorFreezeError(f"prediction row はちょうど{len(expected)}行必要")

    observed: dict[tuple[str, str], dict] = {}
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise SelectorFreezeError(f"rows[{index}] は object でなければならない")
        unknown = set(raw) - _ROW_KEYS
        missing = _ROW_REQUIRED_INPUT_KEYS - set(raw)
        if unknown or missing:
            raise SelectorFreezeError(
                f"rows[{index}] schema 不一致: missing={sorted(missing)} unknown={sorted(unknown)}"
            )
        target = raw["target_holdout"]
        arm = raw["arm"]
        if not isinstance(target, str) or not isinstance(arm, str):
            raise SelectorFreezeError(f"rows[{index}] の target/arm は文字列でなければならない")
        cell = (target, arm)
        if cell not in expected:
            raise SelectorFreezeError(f"未知 prediction cell: {cell!r}")
        if cell in observed:
            raise SelectorFreezeError(f"prediction cell 重複: {cell!r}")
        job = expected[cell]
        for field in (
            "descriptor_source_holdout", "decision_method", "input_payload_sha256",
        ):
            if raw[field] != job[field]:
                raise SelectorFreezeError(f"rows[{index}].{field} が固定 job と不一致")

        row = {key: copy.deepcopy(raw.get(key)) for key in _ROW_KEYS}
        row["target_holdout"] = target
        row["arm"] = arm
        status = row["status"]
        if status not in {"valid", "invalid", "missing"}:
            raise SelectorFreezeError(f"rows[{index}].status が不正")

        if arm == "off":
            if row["decision_method"] != STATIC_DECISION_METHOD:
                raise SelectorFreezeError("off row は static_default 固定")
            if status != "valid" or row["choice_id"] != STATIC_DEFAULT_CHOICE_ID:
                raise SelectorFreezeError("off row は valid + static default choice 固定")
            agent_fields = (
                "rationale", "raw_response_path", "raw_sha256",
                "parser_error_code", "agent_provenance",
            )
            if any(row[field] is not None for field in agent_fields):
                raise SelectorFreezeError("off row に agent provenance/output を記録してはならない")
        else:
            if row["decision_method"] == STATIC_DECISION_METHOD:
                raise SelectorFreezeError("agent row に static_default を指定してはならない")
            if row["decision_method"] != AGENT_DECISION_METHOD:
                raise SelectorFreezeError("agent row の decision_method が不正")
            row["agent_provenance"] = _validate_agent_provenance(
                row["agent_provenance"], field=f"rows[{index}].agent_provenance",
                role_file_sha256=role_file_sha256,
            )
            if status in {"valid", "invalid"}:
                _nonempty_string(
                    row["raw_response_path"], field=f"rows[{index}].raw_response_path"
                )
                _sha256_string(row["raw_sha256"], field=f"rows[{index}].raw_sha256")
            elif row["raw_response_path"] is not None or row["raw_sha256"] is not None:
                raise SelectorFreezeError("missing row に raw response を記録してはならない")

            if status == "valid":
                if row["choice_id"] not in CHOICE_TO_BINDING:
                    raise SelectorFreezeError("valid agent row の choice_id が不正")
                _nonempty_string(row["rationale"], field=f"rows[{index}].rationale")
                if row["parser_error_code"] is not None:
                    raise SelectorFreezeError("valid agent row に parser error がある")
            elif status == "invalid":
                if row["choice_id"] is not None or row["rationale"] is not None:
                    raise SelectorFreezeError("invalid agent row は choice/rationale null 固定")
                _nonempty_string(
                    row["parser_error_code"], field=f"rows[{index}].parser_error_code"
                )
            else:
                if any(row[field] is not None for field in (
                    "choice_id", "rationale", "parser_error_code",
                )):
                    raise SelectorFreezeError("missing agent row の result field は null 固定")

        choice_id = row["choice_id"]
        if choice_id is None:
            expected_binding_key = None
            expected_binding_sha = None
        else:
            expected_binding_key = CHOICE_TO_BINDING.get(choice_id)
            if expected_binding_key is None:
                raise SelectorFreezeError(f"unknown choice_id: {choice_id!r}")
            expected_binding_sha = _canonical_sha256(
                binding_entry_for_choice(freeze, target, choice_id)
            )
        supplied_binding = raw.get("binding_key")
        supplied_binding_sha = raw.get("binding_entry_sha256")
        if supplied_binding is not None and supplied_binding != expected_binding_key:
            raise SelectorFreezeError("binding_key が trusted 解決結果と不一致")
        if supplied_binding_sha is not None and supplied_binding_sha != expected_binding_sha:
            raise SelectorFreezeError("binding_entry_sha256 が trusted 解決結果と不一致")
        row["binding_key"] = expected_binding_key
        row["binding_entry_sha256"] = expected_binding_sha
        observed[cell] = row

    if set(observed) != set(expected):
        raise SelectorFreezeError("prediction cell に欠落がある")
    return [observed[(job["target_holdout"], job["arm"])] for job in jobs]


def _derive_swapped_expectations(freeze: Mapping, rows: Sequence[Mapping]) -> list[dict]:
    _, derangement, targets = _freeze_axes(freeze)
    on_choice = {
        row["target_holdout"]: row["choice_id"]
        for row in rows if row["arm"] == "on"
    }
    return [
        {
            "target_holdout": target,
            "source_on_holdout": derangement[target],
            "expected_choice_id": on_choice[derangement[target]],
        }
        for target in targets
    ]


def build_prediction_freeze(
    *,
    freeze: Mapping,
    rows,
    generated_at,
    pre_oracle_head,
    sources,
    execution_policy,
) -> dict:
    """6セルの結果を oracle 非参照で immutable prediction 文書へ構成する。"""
    generated_at = _nonempty_string(generated_at, field="generated_at")
    if not isinstance(pre_oracle_head, str) or _GIT_SHA_RE.fullmatch(pre_oracle_head) is None:
        raise SelectorFreezeError("pre_oracle_head は40桁 lowercase Git SHAでなければならない")
    validated_sources = _validate_sources(sources)
    normalised_rows = _normalise_rows(
        freeze, rows, role_file_sha256=validated_sources["role"]["sha256"],
    )
    document = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "pre_oracle_head": pre_oracle_head,
        "sources": validated_sources,
        "selector_basis_sha256": selector_basis_sha256(freeze),
        "execution_policy": _validate_execution_policy(execution_policy),
        "static_default": {
            "rule_version": STATIC_DEFAULT_RULE_VERSION,
            "choice_id": STATIC_DEFAULT_CHOICE_ID,
        },
        "derangement": copy.deepcopy(dict(freeze["derangement"])),
        "rows": normalised_rows,
        "swapped_follow_expectations": _derive_swapped_expectations(
            freeze, normalised_rows
        ),
    }
    document["body_sha256"] = _canonical_sha256(document)
    return document


def verify_prediction_freeze(document, *, freeze: Mapping, root=ROOT) -> None:
    """prediction 文書の hash chain、basis、全セル、期待値を再導出照合する。"""
    if not isinstance(document, Mapping) or set(document) != _DOCUMENT_KEYS:
        raise SelectorFreezeError("prediction freeze top-level schema が不一致")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise SelectorFreezeError("prediction freeze schema_version が不一致")
    recorded_body_sha = _sha256_string(document.get("body_sha256"), field="body_sha256")
    body = {key: copy.deepcopy(value) for key, value in document.items()
            if key != "body_sha256"}
    if _canonical_sha256(body) != recorded_body_sha:
        raise SelectorFreezeError("prediction freeze body_sha256 が不一致")
    if document.get("selector_basis_sha256") != selector_basis_sha256(freeze):
        raise SelectorFreezeError("selector_basis_sha256 が holdout freeze と不一致")
    _, derangement, _ = _freeze_axes(freeze)
    if document.get("derangement") != dict(derangement):
        raise SelectorFreezeError("prediction derangement が holdout freeze と不一致")
    if document.get("static_default") != {
        "rule_version": STATIC_DEFAULT_RULE_VERSION,
        "choice_id": STATIC_DEFAULT_CHOICE_ID,
    }:
        raise SelectorFreezeError("static_default 契約が不一致")
    _nonempty_string(document.get("generated_at"), field="generated_at")
    if (not isinstance(document.get("pre_oracle_head"), str)
            or _GIT_SHA_RE.fullmatch(document["pre_oracle_head"]) is None):
        raise SelectorFreezeError("pre_oracle_head が不正")
    sources = _validate_sources(document.get("sources"))
    for name, record in sources.items():
        _verify_file_record(record, root=Path(root), field=f"sources.{name}")
    _validate_execution_policy(document.get("execution_policy"))
    normalised_rows = _normalise_rows(
        freeze, document.get("rows"), role_file_sha256=sources["role"]["sha256"],
    )
    if normalised_rows != document.get("rows"):
        raise SelectorFreezeError("prediction rows が canonical trusted 解決結果でない")
    for index, row in enumerate(normalised_rows):
        if row["status"] not in {"valid", "invalid"} or row["arm"] == "off":
            continue
        _verify_file_record(
            {"path": row["raw_response_path"], "sha256": row["raw_sha256"]},
            root=Path(root), field=f"rows[{index}].raw_response",
        )
    expected = _derive_swapped_expectations(freeze, normalised_rows)
    if document.get("swapped_follow_expectations") != expected:
        raise SelectorFreezeError("swapped_follow_expectations の再導出結果が不一致")


def write_prediction_freeze(path, document) -> None:
    """同一 directory の一時ファイルを atomic link し、既存 path を拒否する。"""
    if not isinstance(document, Mapping):
        raise SelectorFreezeError("prediction document は object でなければならない")
    recorded = document.get("body_sha256")
    body = {key: value for key, value in document.items() if key != "body_sha256"}
    if recorded != _canonical_sha256(body):
        raise SelectorFreezeError("書き込み前 body_sha256 検査に失敗")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError as exc:
            raise SelectorFreezeError(
                f"prediction freeze が既に存在する: {destination}"
            ) from exc
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        if isinstance(exc, FileExistsError):  # pragma: no cover - translated above
            raise SelectorFreezeError(f"prediction freeze が既に存在する: {destination}") from exc
        raise SelectorFreezeError(f"prediction freeze を書けない: {destination}: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _load_json_object(path: Path) -> dict:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant: {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SelectorFreezeError(f"JSON object を読めない: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SelectorFreezeError(f"JSON top-level が object でない: {path}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8b selector prediction freeze の計画・照合")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="6セルの job 計画だけを表示する")
    plan.add_argument("--freeze", type=Path, default=HOLDOUT_FREEZE_PATH)
    verify = subparsers.add_parser("verify", help="prediction freeze を再照合する")
    verify.add_argument("--path", type=Path, required=True)
    verify.add_argument("--freeze", type=Path, default=HOLDOUT_FREEZE_PATH)
    verify.add_argument("--root", type=Path, default=ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        freeze = _load_json_object(args.freeze)
        if args.command == "plan":
            print(json.dumps(build_prediction_jobs(freeze), ensure_ascii=False, indent=2))
        else:
            document = _load_json_object(args.path)
            verify_prediction_freeze(document, freeze=freeze, root=args.root)
            print(f"verified: {args.path}")
    except SelectorFreezeError as exc:
        print(f"fails-closed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
