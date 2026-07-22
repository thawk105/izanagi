# -*- coding: utf-8 -*-
"""段 8b selector prediction の at-most-once 実走・journal・seal CLI。"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

_ORCHESTRATOR_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(_ORCHESTRATOR_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_ORCHESTRATOR_FOR_IMPORT))

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    _ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
    if str(_ROOT_FOR_IMPORT) not in sys.path:
        sys.path.insert(0, str(_ROOT_FOR_IMPORT))
    from orchestrator.campaign.s8b_descriptor import descriptor_for_holdout
    from orchestrator.campaign.s8b_selector_freeze import (
        AGENT_DECISION_METHOD,
        STATIC_DECISION_METHOD,
        V1_FREEZE_SHA256,
        build_prediction_freeze,
        build_prediction_jobs,
        record_agent_attempt,
        verify_prediction_freeze,
        write_prediction_freeze,
    )
    from orchestrator.campaign.s8b_selector_input import (
        STATIC_DEFAULT_CHOICE_ID,
        build_selector_payload,
        selector_payload_sha256,
    )
else:
    from .s8b_descriptor import descriptor_for_holdout
    from .s8b_selector_freeze import (
        AGENT_DECISION_METHOD,
        STATIC_DECISION_METHOD,
        V1_FREEZE_SHA256,
        build_prediction_freeze,
        build_prediction_jobs,
        record_agent_attempt,
        verify_prediction_freeze,
        write_prediction_freeze,
    )
    from .s8b_selector_input import (
        STATIC_DEFAULT_CHOICE_ID,
        build_selector_payload,
        selector_payload_sha256,
    )


ROOT = Path(__file__).resolve().parents[2]
JOURNAL_SCHEMA_VERSION = "8b-prediction-journal/v1"
AGENT_ARMS = ("on", "swapped")
OFF_ARM = "off"
PROVIDER_KIND_CLAUDE_HEADLESS = "claude-headless"
CLAUDE_ENV_ALLOWLIST = frozenset({"PATH", "HOME", "LANG", "LC_ALL", "TERM"})
CLAUDE_TIMEOUT_S = 1200

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_SHA_RE = re.compile(r"[0-9a-f]{40}")
_CELL_RECORD_TYPES = {"claim", "invocation", "static_terminal"}
_HEADER_KEYS = {
    "record_type", "seq", "schema", "pre_oracle_head", "protocol_sha256",
    "freeze_sha256", "provider_kind", "role_file_sha256", "parser_module_sha256",
    "claude_executable_path", "claude_executable_sha256", "created_at",
}
_CLAIM_KEYS = {
    "record_type", "seq", "target_holdout", "arm", "decision_method",
    "input_payload_sha256", "payload_path", "claimed_at",
}
_INVOCATION_KEYS = {
    "record_type", "seq", "target_holdout", "arm", "status", "choice_id",
    "rationale", "parser_error_code", "raw_response_path", "raw_sha256", "receipt",
}
_STATIC_KEYS = {
    "record_type", "seq", "target_holdout", "arm", "decision_method", "choice_id",
}

_PROTOCOL_PATH = Path("output/s8b-freeze/floor_protocol.json")
_FREEZE_PATH = Path("output/s8b-freeze/holdout_freeze.json")
_JOURNAL_PATH = Path("output/s8b-freeze/selector-runs/journal.jsonl")
_PREDICTIONS_PATH = Path("output/s8b-freeze/selector_predictions.json")
_ROLE_PATH = Path(".claude/agents/selector-8b.md")
_PARSER_MODULE_PATH = Path("orchestrator/campaign/s8b_selector_output.py")
_SOURCE_PATHS = {
    "holdout_freeze": _FREEZE_PATH,
    "builder": Path("orchestrator/campaign/s8b_selector_input.py"),
    "role": _ROLE_PATH,
    "input_schema": Path("orchestrator/campaign/s8b_selector_catalog.json"),
    "output_schema": Path("orchestrator/campaign/s8b_selector_output_schema.json"),
}
_EXECUTION_POLICY = {
    "attempts_per_agent_cell": 1,
    "retry": False,
    "reuse_equal_payload_output": False,
    "fresh_context": True,
    "declared_tools": [],
}


class PredictionRunnerError(RuntimeError):
    """prediction runner の証拠鎖・at-most-once 契約に対する fail-closed 拒否。"""


@dataclass(frozen=True)
class ProviderResponse:
    raw_response: str
    provenance: Mapping[str, Any]


Provider = Callable[..., ProviderResponse]


def unwired_provider(*, target_holdout: str, arm: str, payload: Mapping) -> ProviderResponse:
    raise PredictionRunnerError(
        "selector の production 実走は未配線: --provider claude-headless の明示 opt-in が必要"
    )


PRODUCTION_PROVIDER: Provider = unwired_provider


@dataclass(frozen=True)
class JournalBinding:
    """run_header が束縛する read-once 入力と実走構成。"""

    pre_oracle_head: str
    protocol_sha256: str
    freeze_sha256: str
    provider_kind: str
    role_file_sha256: str
    parser_module_sha256: str
    claude_executable_path: str
    claude_executable_sha256: str
    known_cells: frozenset[tuple[str, str]]

    def __post_init__(self) -> None:
        if not isinstance(self.pre_oracle_head, str) or _GIT_SHA_RE.fullmatch(
            self.pre_oracle_head
        ) is None:
            raise PredictionRunnerError("pre_oracle_head は40桁 lowercase hex 必須")
        for field in (
            "protocol_sha256", "freeze_sha256", "role_file_sha256",
            "parser_module_sha256", "claude_executable_sha256",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise PredictionRunnerError(f"{field} は64桁 lowercase hex 必須")
        if not isinstance(self.provider_kind, str) or not self.provider_kind.strip():
            raise PredictionRunnerError("provider_kind は空でない文字列必須")
        if (not isinstance(self.claude_executable_path, str)
                or not Path(self.claude_executable_path).is_absolute()):
            raise PredictionRunnerError("claude_executable_path は絶対 path 必須")
        if (not isinstance(self.known_cells, frozenset) or len(self.known_cells) != 6
                or any(
                    not isinstance(cell, tuple) or len(cell) != 2
                    or not all(isinstance(value, str) and value for value in cell)
                    for cell in self.known_cells
                )):
            raise PredictionRunnerError("known_cells は固定6セルの frozenset 必須")

    def header_values(self) -> dict[str, str]:
        return {
            "schema": JOURNAL_SCHEMA_VERSION,
            "pre_oracle_head": self.pre_oracle_head,
            "protocol_sha256": self.protocol_sha256,
            "freeze_sha256": self.freeze_sha256,
            "provider_kind": self.provider_kind,
            "role_file_sha256": self.role_file_sha256,
            "parser_module_sha256": self.parser_module_sha256,
            "claude_executable_path": self.claude_executable_path,
            "claude_executable_sha256": self.claude_executable_sha256,
        }


@dataclass(frozen=True)
class CellStatus:
    target_holdout: str
    arm: str
    kind: str
    claim: Mapping[str, Any] | None = None
    invocation: Mapping[str, Any] | None = None
    static: Mapping[str, Any] | None = None


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise PredictionRunnerError("canonical JSON bytes を構成できない") from exc


def _reject_duplicate_keys(pairs):
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise PredictionRunnerError(f"JSON に duplicate key: {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str):
    raise PredictionRunnerError(f"JSON に非有限数: {token}")


def _parse_json_object(raw: bytes, *, source: object) -> dict:
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, PredictionRunnerError) as exc:
        raise PredictionRunnerError(f"JSON object を読めない: {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise PredictionRunnerError(f"JSON top-level が object でない: {source}")
    return value


def _validate_timestamp(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise PredictionRunnerError(f"{field} は空でない時刻文字列必須")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PredictionRunnerError(f"{field} が ISO-8601 時刻でない") from exc
    if parsed.tzinfo is None:
        raise PredictionRunnerError(f"{field} に timezone がない")


class PredictionJournal:
    """O_APPEND + fsync の append-only JSONL journal。"""

    def __init__(self, path) -> None:
        self.path = Path(path)
        self._next_seq: int | None = None

    def read_records(self) -> list[dict]:
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            return []
        except OSError as exc:
            raise PredictionRunnerError(f"journal を読めない: {self.path}: {exc}") from exc
        try:
            text = raw.decode("utf-8")
        except UnicodeError as exc:
            raise PredictionRunnerError(f"journal が UTF-8 でない: {self.path}") from exc
        records: list[dict] = []
        for index, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(
                    line, object_pairs_hook=_reject_duplicate_keys,
                    parse_constant=_reject_constant,
                )
            except (json.JSONDecodeError, PredictionRunnerError) as exc:
                raise PredictionRunnerError(f"journal 行 {index} を parse できない: {exc}") from exc
            if not isinstance(value, dict):
                raise PredictionRunnerError(f"journal 行 {index} が object でない")
            records.append(value)
        return records

    def _reserve_seq(self) -> int:
        if self._next_seq is None:
            self._next_seq = len(self.read_records()) + 1
        seq = self._next_seq
        self._next_seq += 1
        return seq

    def append(self, record: Mapping[str, Any]) -> dict:
        if not isinstance(record, Mapping):
            raise PredictionRunnerError("journal record は object 必須")
        stored = dict(record)
        stored["seq"] = self._reserve_seq()
        payload = _canonical_json_bytes(stored) + b"\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self.path, flags, 0o644)
            try:
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("journal write が前進しない")
                    view = view[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
            _fsync_directory(self.path.parent)
        except OSError as exc:
            self._next_seq -= 1  # type: ignore[operator]
            raise PredictionRunnerError(f"journal へ追記できない: {self.path}: {exc}") from exc
        return stored


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _validate_header(record: Mapping, *, binding: JournalBinding) -> None:
    if set(record) != _HEADER_KEYS:
        raise PredictionRunnerError(
            "run_header schema 不一致: "
            f"missing={sorted(_HEADER_KEYS - set(record))} "
            f"unknown={sorted(set(record) - _HEADER_KEYS)}"
        )
    if record.get("record_type") != "run_header" or record.get("seq") != 1:
        raise PredictionRunnerError("journal 最初の record は seq=1 の run_header 必須")
    _validate_timestamp(record.get("created_at"), field="run_header.created_at")
    for field, expected in binding.header_values().items():
        if record.get(field) != expected:
            raise PredictionRunnerError(
                f"run_header.{field} が呼び出し束縛と不一致: "
                f"recorded={record.get(field)!r} expected={expected!r}"
            )


def ensure_run_header(
    journal: PredictionJournal, *, binding: JournalBinding, created_at: str | None = None,
) -> dict:
    """新規 journal を run_header 1 行だけで atomic create、既存なら完全一致を要求。"""
    records = journal.read_records()
    if records:
        _validate_header(records[0], binding=binding)
        resolve_journal(records, binding=binding)
        return records[0]
    if journal.path.exists():
        raise PredictionRunnerError("既存の空 journal は run_header 欠落として拒否")
    header = {
        "record_type": "run_header",
        "seq": 1,
        **binding.header_values(),
        "created_at": created_at or _now_iso(),
    }
    _validate_header(header, binding=binding)
    payload = _canonical_json_bytes(header) + b"\n"
    journal.path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(journal.path, flags, 0o644)
    except FileExistsError:
        records = journal.read_records()
        if not records:
            raise PredictionRunnerError("並行作成された journal に run_header がない")
        _validate_header(records[0], binding=binding)
        resolve_journal(records, binding=binding)
        return records[0]
    except OSError as exc:
        raise PredictionRunnerError(f"run_header journal を作れない: {exc}") from exc
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("run_header write が前進しない")
            view = view[written:]
        os.fsync(fd)
    except OSError as exc:
        raise PredictionRunnerError(f"run_header を durable 化できない: {exc}") from exc
    finally:
        os.close(fd)
    _fsync_directory(journal.path.parent)
    journal._next_seq = 2
    return header


def _validate_record_shape(record: Mapping, *, index: int) -> str:
    rt = record.get("record_type")
    if rt not in _CELL_RECORD_TYPES:
        raise PredictionRunnerError(f"journal[{index}] の record_type が不正: {rt!r}")
    expected = {
        "claim": _CLAIM_KEYS,
        "invocation": _INVOCATION_KEYS,
        "static_terminal": _STATIC_KEYS,
    }[rt]
    if set(record) != expected:
        raise PredictionRunnerError(
            f"journal[{index}] ({rt}) schema 不一致: "
            f"missing={sorted(expected - set(record))} unknown={sorted(set(record) - expected)}"
        )
    target = record.get("target_holdout")
    arm = record.get("arm")
    if not isinstance(target, str) or not target or not isinstance(arm, str) or not arm:
        raise PredictionRunnerError(f"journal[{index}] の target_holdout/arm が不正")
    return rt


def resolve_journal(
    records: Sequence[Mapping], *, binding: JournalBinding,
) -> dict[tuple[str, str], CellStatus]:
    """header を束縛照合し、後続 record をセル別終端状態へ畳み込む。"""
    if not records:
        raise PredictionRunnerError("journal に必須 run_header がない")
    _validate_header(records[0], binding=binding)
    for index, record in enumerate(records, start=1):
        seq = record.get("seq")
        if isinstance(seq, bool) or seq != index:
            raise PredictionRunnerError(
                f"journal[{index - 1}].seq が append 順と不一致: {seq!r} != {index}"
            )

    claims: dict[tuple[str, str], Mapping] = {}
    invocations: dict[tuple[str, str], Mapping] = {}
    statics: dict[tuple[str, str], Mapping] = {}
    for index, record in enumerate(records[1:], start=1):
        rt = _validate_record_shape(record, index=index)
        cell = (record["target_holdout"], record["arm"])
        if cell not in binding.known_cells:
            raise PredictionRunnerError(
                f"protocol violation: 固定6セル外の journal record: {cell!r}"
            )
        arm = record["arm"]
        if rt == "claim":
            if arm not in AGENT_ARMS:
                raise PredictionRunnerError(f"journal[{index}]: agent 以外を claim: {cell!r}")
            if cell in claims:
                raise PredictionRunnerError(f"protocol violation: 二重 claim: {cell!r}")
            if record.get("decision_method") != AGENT_DECISION_METHOD:
                raise PredictionRunnerError(f"journal[{index}]: claim decision_method 不正")
            claims[cell] = record
        elif rt == "invocation":
            if cell not in claims:
                raise PredictionRunnerError(f"protocol violation: claim なき invocation: {cell!r}")
            if cell in invocations:
                raise PredictionRunnerError(f"protocol violation: 二重 invocation: {cell!r}")
            invocations[cell] = record
        else:
            if arm != OFF_ARM:
                raise PredictionRunnerError(
                    f"journal[{index}]: static_terminal は off arm 専用: {cell!r}"
                )
            if record.get("decision_method") != STATIC_DECISION_METHOD:
                raise PredictionRunnerError(f"journal[{index}]: static decision_method 不正")
            if record.get("choice_id") != STATIC_DEFAULT_CHOICE_ID:
                raise PredictionRunnerError(f"journal[{index}]: static choice_id 不正")
            if cell in claims or cell in statics:
                raise PredictionRunnerError(
                    f"protocol violation: static terminal の重複/claim 混在: {cell!r}"
                )
            statics[cell] = record

    statuses: dict[tuple[str, str], CellStatus] = {}
    for cell, static in statics.items():
        statuses[cell] = CellStatus(cell[0], cell[1], "static", static=static)
    for cell, claim in claims.items():
        invocation = invocations.get(cell)
        if invocation is None:
            statuses[cell] = CellStatus(cell[0], cell[1], "claimed_missing", claim=claim)
        else:
            statuses[cell] = CellStatus(
                cell[0], cell[1], "resolved", claim=claim, invocation=invocation,
            )
    return statuses


def _payload_for_job(freeze: Mapping, job: Mapping) -> dict:
    holdouts = freeze.get("holdouts")
    source = job["descriptor_source_holdout"]
    if not isinstance(holdouts, Mapping) or source not in holdouts:
        raise PredictionRunnerError(f"holdout source が freeze にない: {source!r}")
    payload = build_selector_payload(descriptor_for_holdout(holdouts[source]))
    if selector_payload_sha256(payload) != job["input_payload_sha256"]:
        raise PredictionRunnerError(
            f"再構成 payload sha が job と不一致: {job['target_holdout']}/{job['arm']}"
        )
    return payload


def _write_bytes_bound(
    path: Path, data: bytes, *, _read_back: Callable[[Path], bytes] | None = None,
) -> str:
    """O_EXCL|O_NOFOLLOW で create-only 書込みし、read-back 完全一致後に hash を返す。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o644)
    except OSError as exc:
        raise PredictionRunnerError(f"artifact を create-only で作れない: {path}: {exc}") from exc
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("artifact write が前進しない")
            view = view[written:]
        os.fsync(fd)
    except OSError as exc:
        raise PredictionRunnerError(f"artifact を書けない: {path}: {exc}") from exc
    finally:
        os.close(fd)
    _fsync_directory(path.parent)
    reader = _read_back or (lambda candidate: candidate.read_bytes())
    try:
        observed = reader(path)
    except OSError as exc:
        raise PredictionRunnerError(f"artifact read-back 失敗: {path}: {exc}") from exc
    if observed != data:
        raise PredictionRunnerError(f"artifact read-back bytes 不一致: {path}")
    return _sha256(data)


def _accept_or_create_payload(path: Path, data: bytes) -> str:
    """再開時は同一 bytes の既存 payload だけを受理し、それ以外は拒否する。"""
    path = Path(path)
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise PredictionRunnerError(f"既存 payload artifact が実 file でない: {path}")
        try:
            observed = path.read_bytes()
        except OSError as exc:
            raise PredictionRunnerError(f"既存 payload artifact を読めない: {path}: {exc}") from exc
        if observed != data:
            raise PredictionRunnerError(f"既存 payload artifact bytes が期待値と不一致: {path}")
        return _sha256(data)
    return _write_bytes_bound(path, data)


def _relative_artifact(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (OSError, ValueError) as exc:
        raise PredictionRunnerError(f"artifact が root 配下でない: {path}") from exc


def _acquire_drive_lock(journal: PredictionJournal) -> int:
    lock_path = journal.path.parent / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(lock_path, flags, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(fd)
            raise
    except BlockingIOError as exc:
        raise PredictionRunnerError(f"prediction journal lock を取得できない: {lock_path}") from exc
    except OSError as exc:
        raise PredictionRunnerError(f"prediction journal lock を開けない: {lock_path}: {exc}") from exc
    return fd


def drive_journal(
    *,
    freeze: Mapping,
    journal: PredictionJournal,
    artifact_root: Path,
    root: Path,
    binding: JournalBinding,
    provider: Provider = PRODUCTION_PROVIDER,
) -> dict[tuple[str, str], CellStatus]:
    """flock 下で 6 セルを claim-first・再試行なしで駆動する。"""
    lock_fd = _acquire_drive_lock(journal)
    try:
        artifact_root = Path(artifact_root)
        root = Path(root)
        jobs = build_prediction_jobs(freeze)
        known_cells = frozenset(
            (job["target_holdout"], job["arm"]) for job in jobs
        )
        if known_cells != binding.known_cells:
            raise PredictionRunnerError("freeze の固定6セルが run_header 束縛と不一致")
        statuses = resolve_journal(journal.read_records(), binding=binding)
        observed_child_ids: set[str] = set()
        for status in statuses.values():
            if status.kind != "resolved":
                continue
            invocation = status.invocation
            assert invocation is not None
            receipt = invocation.get("receipt")
            child_id = receipt.get("child_id") if isinstance(receipt, Mapping) else None
            if not isinstance(child_id, str) or not child_id:
                raise PredictionRunnerError(
                    "既存 invocation receipt の child_id は空でない str 必須"
                )
            if child_id in observed_child_ids:
                raise PredictionRunnerError(
                    "既存 invocation receipt に session_id 重複を観測"
                )
            observed_child_ids.add(child_id)
        provider_kind = getattr(provider, "provider_kind", None)
        role_sha = getattr(provider, "role_file_sha256", None)
        if provider_kind is not None and provider_kind != binding.provider_kind:
            raise PredictionRunnerError("provider kind が run_header と不一致")
        if role_sha is not None and role_sha != binding.role_file_sha256:
            raise PredictionRunnerError("provider role sha が run_header と不一致")
        seed_session_ids = getattr(provider, "seed_observed_session_ids", None)
        if seed_session_ids is not None:
            if not callable(seed_session_ids):
                raise PredictionRunnerError("provider session_id 復元 seam が callable でない")
            seed_session_ids(observed_child_ids)

        for job in jobs:
            cell = (job["target_holdout"], job["arm"])
            arm = job["arm"]
            status = statuses.get(cell)
            if arm == OFF_ARM:
                if status is not None and status.kind == "static":
                    continue
                if status is not None:
                    raise PredictionRunnerError(f"off セルに非 static record: {cell!r}")
                journal.append({
                    "record_type": "static_terminal",
                    "target_holdout": job["target_holdout"],
                    "arm": arm,
                    "decision_method": STATIC_DECISION_METHOD,
                    "choice_id": STATIC_DEFAULT_CHOICE_ID,
                })
                continue
            if status is not None:
                continue  # resolved と claimed_missing の双方を再呼出ししない。
            if provider is PRODUCTION_PROVIDER:
                raise PredictionRunnerError(
                    f"selector 実走は未解禁 (provider 未配線): {cell!r}"
                )

            payload = _payload_for_job(freeze, job)
            payload_bytes = _canonical_json_bytes(payload)
            if _sha256(payload_bytes) != selector_payload_sha256(payload):
                raise PredictionRunnerError("送信 payload bytes sha と selector payload sha が不一致")
            payload_path = artifact_root / f"payload_{job['target_holdout']}_{arm}.json"
            _accept_or_create_payload(payload_path, payload_bytes)
            journal.append({
                "record_type": "claim",
                "target_holdout": job["target_holdout"],
                "arm": arm,
                "decision_method": AGENT_DECISION_METHOD,
                "input_payload_sha256": job["input_payload_sha256"],
                "payload_path": _relative_artifact(payload_path, root=root),
                "claimed_at": _now_iso(),
            })

            response = provider(
                target_holdout=job["target_holdout"], arm=arm,
                payload=copy.deepcopy(payload),
            )
            if not isinstance(response, ProviderResponse):
                raise PredictionRunnerError("provider は ProviderResponse を返さねばならない")
            if not isinstance(response.raw_response, str):
                raise PredictionRunnerError("provider raw_response は str 必須")
            if not isinstance(response.provenance, Mapping):
                raise PredictionRunnerError("provider provenance は Mapping 必須")
            response_child_id = response.provenance.get("child_id")
            if not isinstance(response_child_id, str) or not response_child_id:
                raise PredictionRunnerError("provider provenance.child_id は空でない str 必須")
            if response_child_id in observed_child_ids:
                raise PredictionRunnerError(
                    "fresh context に反する session_id 重複を観測"
                )
            observed_child_ids.add(response_child_id)
            raw_bytes = response.raw_response.encode("utf-8")
            raw_path = artifact_root / f"raw_{job['target_holdout']}_{arm}.txt"
            raw_sha256 = _write_bytes_bound(raw_path, raw_bytes)
            attempt = record_agent_attempt(job=job, raw_output=response.raw_response)
            if attempt["raw_sha256"] != raw_sha256:
                raise PredictionRunnerError("raw 応答 bytes と strict parser の sha が不一致")
            journal.append({
                "record_type": "invocation",
                "target_holdout": job["target_holdout"],
                "arm": arm,
                "status": attempt["status"],
                "choice_id": attempt.get("choice_id"),
                "rationale": attempt.get("rationale"),
                "parser_error_code": attempt.get("parser_error_code"),
                "raw_response_path": _relative_artifact(raw_path, root=root),
                "raw_sha256": raw_sha256,
                "receipt": copy.deepcopy(dict(response.provenance)),
            })
        return resolve_journal(journal.read_records(), binding=binding)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def build_rows_from_journal(
    freeze: Mapping, journal: PredictionJournal, *, binding: JournalBinding,
) -> list[dict]:
    """journal を、claim-crash missing を含む canonical 6 行へ射影する。"""
    jobs = build_prediction_jobs(freeze)
    statuses = resolve_journal(journal.read_records(), binding=binding)
    rows: list[dict] = []
    for job in jobs:
        cell = (job["target_holdout"], job["arm"])
        arm = job["arm"]
        status = statuses.get(cell)
        if arm == OFF_ARM:
            if status is None or status.kind != "static":
                raise PredictionRunnerError(f"off セルの static terminal がない: {cell!r}")
            rows.append({
                "target_holdout": job["target_holdout"], "arm": arm,
                "descriptor_source_holdout": None,
                "decision_method": STATIC_DECISION_METHOD, "status": "valid",
                "choice_id": STATIC_DEFAULT_CHOICE_ID, "input_payload_sha256": None,
                "rationale": None, "raw_response_path": None, "raw_sha256": None,
                "parser_error_code": None, "agent_provenance": None,
            })
            continue
        if status is None:
            raise PredictionRunnerError(f"agent セルが未着手: {cell!r}")
        claim = status.claim
        assert claim is not None
        if claim["input_payload_sha256"] != job["input_payload_sha256"]:
            raise PredictionRunnerError(
                "claim payload sha が job と不一致 (freeze/journal 束縛違反): "
                f"{cell!r} claim={claim['input_payload_sha256']!r} "
                f"job={job['input_payload_sha256']!r}"
            )
        if status.kind == "claimed_missing":
            rows.append({
                "target_holdout": job["target_holdout"], "arm": arm,
                "descriptor_source_holdout": job["descriptor_source_holdout"],
                "decision_method": AGENT_DECISION_METHOD, "status": "missing",
                "choice_id": None, "input_payload_sha256": job["input_payload_sha256"],
                "rationale": None, "raw_response_path": None, "raw_sha256": None,
                "parser_error_code": None, "agent_provenance": None,
            })
            continue
        invocation = status.invocation
        assert invocation is not None
        rows.append({
            "target_holdout": job["target_holdout"], "arm": arm,
            "descriptor_source_holdout": job["descriptor_source_holdout"],
            "decision_method": AGENT_DECISION_METHOD, "status": invocation["status"],
            "choice_id": invocation["choice_id"],
            "input_payload_sha256": job["input_payload_sha256"],
            "rationale": invocation["rationale"],
            "raw_response_path": invocation["raw_response_path"],
            "raw_sha256": invocation["raw_sha256"],
            "parser_error_code": invocation["parser_error_code"],
            "agent_provenance": copy.deepcopy(dict(invocation["receipt"])),
        })
    return rows


def materialize_predictions(
    *, freeze: Mapping, journal: PredictionJournal, predictions_path,
    generated_at: str, pre_oracle_head: str, sources: Mapping,
    execution_policy: Mapping, binding: JournalBinding,
) -> dict:
    """header 束縛済み journal から missing 込み prediction 文書を exclusive-create する。"""
    if pre_oracle_head != binding.pre_oracle_head:
        raise PredictionRunnerError("materialize pre_oracle_head が run_header と不一致")
    role = sources.get("role") if isinstance(sources, Mapping) else None
    if not isinstance(role, Mapping) or role.get("sha256") != binding.role_file_sha256:
        raise PredictionRunnerError("materialize sources.role.sha256 が run_header と不一致")
    rows = build_rows_from_journal(freeze, journal, binding=binding)
    document = build_prediction_freeze(
        freeze=freeze, rows=rows, generated_at=generated_at,
        pre_oracle_head=pre_oracle_head, sources=sources,
        execution_policy=execution_policy,
    )
    write_prediction_freeze(predictions_path, document)
    return document


def _parse_role_frontmatter(role_bytes: bytes) -> tuple[dict[str, Any], str]:
    try:
        text = role_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise PredictionRunnerError("selector role が UTF-8 でない") from exc
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise PredictionRunnerError("selector role frontmatter がない")
    frontmatter_text, body = text[4:].split("\n---\n", 1)
    values: dict[str, Any] = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            raise PredictionRunnerError("selector role frontmatter 行が不正")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if key in values:
            raise PredictionRunnerError(f"selector role frontmatter duplicate: {key}")
        if key == "tools":
            if raw_value != "[]":
                raise PredictionRunnerError("selector role tools は [] 固定")
            values[key] = []
        elif raw_value.startswith('"'):
            try:
                values[key] = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise PredictionRunnerError("selector role frontmatter string 不正") from exc
        else:
            values[key] = raw_value
    required = {"name", "description", "tools", "model", "effort"}
    if not required <= set(values):
        raise PredictionRunnerError(
            f"selector role frontmatter 必須 field 欠落: {sorted(required - set(values))}"
        )
    if values["name"] != "selector-8b" or values["model"] != "opus":
        raise PredictionRunnerError("selector role name/model が承認値でない")
    if values["effort"] != "high" or values["tools"] != []:
        raise PredictionRunnerError("selector role effort/tools が high/[] でない")
    if not isinstance(values["description"], str) or not values["description"]:
        raise PredictionRunnerError("selector role description が不正")
    if not body.strip():
        raise PredictionRunnerError("selector role 本文が空")
    return values, body


class ClaudeHeadlessProvider:
    """claude CLI を neutral cwd・tools/MCP 無し・fresh context で 1 回だけ呼ぶ provider。"""

    provider_kind = PROVIDER_KIND_CLAUDE_HEADLESS

    def __init__(
        self, *, artifact_root: Path, role_file: Path = ROOT / _ROLE_PATH,
        role_bytes: bytes | None = None, repository_root: Path = ROOT,
        executable: str | os.PathLike[str] = "claude",
        runner: Callable[..., Any] = subprocess.run,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.artifact_root = Path(artifact_root)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.artifact_root = self.artifact_root.resolve(strict=True)
        resolved = shutil.which(os.fspath(executable))
        if resolved is None:
            raise PredictionRunnerError(f"claude executable を解決できない: {executable}")
        self.executable = str(Path(resolved).resolve(strict=True))
        try:
            self.executable_sha256 = _sha256(Path(self.executable).read_bytes())
        except OSError as exc:
            raise PredictionRunnerError(f"claude executable bytes を読めない: {self.executable}") from exc
        if role_bytes is None:
            try:
                role_bytes = Path(role_file).read_bytes()
            except OSError as exc:
                raise PredictionRunnerError(f"selector role を read-once できない: {role_file}") from exc
        elif not isinstance(role_bytes, bytes):
            raise PredictionRunnerError("selector role read-once 値は bytes 必須")
        frontmatter, body = _parse_role_frontmatter(role_bytes)
        self.role_file_sha256 = _sha256(role_bytes)
        self.inline_agents_json = _canonical_json_bytes({
            "selector-8b-inline": {
                "description": frontmatter["description"],
                "prompt": body,
                "tools": [],
                "model": frontmatter["model"],
            }
        }).decode("utf-8")
        self.neutral_root = Path(tempfile.mkdtemp(prefix="s8b-selector-")).resolve(strict=True)
        repository_root = Path(repository_root).resolve()
        try:
            self.neutral_root.relative_to(repository_root)
        except ValueError:
            pass
        else:
            raise PredictionRunnerError("neutral root は repository 外でなければならない")
        self.mcp_config_path = self.neutral_root / "empty-mcp-config.json"
        mcp_bytes = b'{"mcpServers":{}}'
        if self.mcp_config_path.is_symlink():
            raise PredictionRunnerError("empty MCP config に symlink を許可しない")
        if self.mcp_config_path.exists():
            if not self.mcp_config_path.is_file() or self.mcp_config_path.read_bytes() != mcp_bytes:
                raise PredictionRunnerError("既存 empty MCP config が固定 bytes と不一致")
        else:
            _write_bytes_bound(self.mcp_config_path, mcp_bytes)
        self.neutral_cwd: Path | None = None
        self._observed_session_ids: set[str] = set()
        source_env = os.environ if environ is None else environ
        self.env = {key: source_env[key] for key in CLAUDE_ENV_ALLOWLIST if key in source_env}
        if "HOME" not in self.env:
            raise PredictionRunnerError("claude 認証に必要な HOME が allowlist env にない")
        self._runner = runner
        self.argv = [
            self.executable,
            "-p",
            "--agent", "selector-8b-inline",
            "--agents", self.inline_agents_json,
            "--output-format", "json",
            "--input-format", "text",
            "--effort", "high",
            "--setting-sources", "",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--mcp-config", str(self.mcp_config_path),
            "--no-session-persistence",
        ]

    def seed_observed_session_ids(self, session_ids: set[str]) -> None:
        """resume 前の journal に durable 記録済みの session_id を観測集合へ復元する。"""
        if not isinstance(session_ids, set) or any(
            not isinstance(session_id, str) or not session_id
            for session_id in session_ids
        ):
            raise PredictionRunnerError("復元 session_id 集合が不正")
        self._observed_session_ids.update(session_ids)

    def __call__(self, *, target_holdout: str, arm: str, payload: Mapping) -> ProviderResponse:
        payload_bytes = _canonical_json_bytes(payload)
        expected_sha = selector_payload_sha256(payload)
        if _sha256(payload_bytes) != expected_sha:
            raise PredictionRunnerError("provider 送信 bytes と selector_payload_sha256 が不一致")
        payload_path = self.artifact_root / f"payload_{target_holdout}_{arm}.json"
        try:
            artifact_bytes = payload_path.read_bytes()
        except OSError as exc:
            raise PredictionRunnerError("provider payload artifact がない") from exc
        if artifact_bytes != payload_bytes:
            raise PredictionRunnerError("payload artifact と stdin bytes が不一致")

        neutral_cwd = Path(tempfile.mkdtemp(prefix="cwd-", dir=self.neutral_root))
        if neutral_cwd.is_symlink() or not neutral_cwd.is_dir():
            raise PredictionRunnerError("neutral cwd が実 directory でない")
        if any(neutral_cwd.iterdir()):
            raise PredictionRunnerError("neutral cwd は invocation ごとに空でなければならない")
        self.neutral_cwd = neutral_cwd

        started_at = _now_iso()
        try:
            completed = self._runner(
                list(self.argv), input=payload_bytes, cwd=str(neutral_cwd),
                env=dict(self.env), timeout=CLAUDE_TIMEOUT_S, check=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except subprocess.TimeoutExpired as exc:
            raise PredictionRunnerError("claude headless invocation timeout") from exc
        except OSError as exc:
            raise PredictionRunnerError(f"claude headless invocation 起動失敗: {exc}") from exc
        finished_at = _now_iso()
        stdout = getattr(completed, "stdout", None)
        if not isinstance(stdout, bytes):
            raise PredictionRunnerError("claude envelope stdout は bytes 必須")
        envelope_path = self.artifact_root / f"envelope_{target_holdout}_{arm}.json"
        _write_bytes_bound(envelope_path, stdout)
        if getattr(completed, "returncode", None) != 0:
            raise PredictionRunnerError(
                f"claude headless invocation nonzero rc: {getattr(completed, 'returncode', None)!r}"
            )
        envelope = _parse_json_object(stdout, source=envelope_path)
        if envelope.get("type") != "result" or envelope.get("subtype") != "success":
            raise PredictionRunnerError("claude envelope type/subtype が result/success でない")
        if envelope.get("is_error") is not False:
            raise PredictionRunnerError("claude envelope is_error は false 固定")
        num_turns = envelope.get("num_turns")
        if type(num_turns) is not int or num_turns != 1:
            raise PredictionRunnerError("claude envelope num_turns は 1 固定")
        if envelope.get("permission_denials") != []:
            raise PredictionRunnerError("claude envelope permission_denials は [] 固定")
        result = envelope.get("result")
        session_id = envelope.get("session_id")
        if not isinstance(result, str):
            raise PredictionRunnerError("claude envelope result は str 必須")
        if not isinstance(session_id, str) or not session_id:
            raise PredictionRunnerError("claude envelope session_id は空でない str 必須")
        model_usage = envelope.get("modelUsage")
        if not isinstance(model_usage, Mapping):
            raise PredictionRunnerError("claude envelope modelUsage は object 必須")
        if any(not isinstance(record, Mapping) for record in model_usage.values()):
            raise PredictionRunnerError("claude envelope modelUsage の各 record は object 必須")
        opus_slugs = [
            key for key in model_usage
            if isinstance(key, str) and key.startswith("claude-opus-")
        ]
        if len(opus_slugs) != 1:
            raise PredictionRunnerError("modelUsage の主 claude-opus- slug が一意でない")
        opus_usage = model_usage[opus_slugs[0]]
        for token_key in ("inputTokens", "outputTokens"):
            token_count = opus_usage.get(token_key)
            if type(token_count) is not int or token_count <= 0:
                raise PredictionRunnerError(
                    f"modelUsage の主 claude-opus- record は正の {token_key} 必須"
                )
        usage = envelope.get("usage")
        server_tool_use = usage.get("server_tool_use") if isinstance(usage, Mapping) else None
        if not isinstance(server_tool_use, Mapping):
            raise PredictionRunnerError("usage.server_tool_use は object 必須")
        for key, count in server_tool_use.items():
            if not isinstance(key, str) or isinstance(count, bool) or not isinstance(count, int):
                raise PredictionRunnerError("usage.server_tool_use count schema が不正")
            if count != 0:
                raise PredictionRunnerError("server tool use を観測したため拒否")
        if session_id in self._observed_session_ids:
            raise PredictionRunnerError("fresh context に反する session_id 重複を観測")
        self._observed_session_ids.add(session_id)
        return ProviderResponse(
            raw_response=result,
            provenance={
                "child_id": session_id,
                "role_file_sha256": self.role_file_sha256,
                "model": opus_slugs[0],
                "started_at": started_at,
                "finished_at": finished_at,
                "fresh_context": True,
                "declared_tools": [],
                "observed_tool_events": [],
            },
        )


def _git_bytes(root: Path, args: Sequence[str]) -> bytes:
    git = shutil.which("git")
    if git is None:
        raise PredictionRunnerError("git executable を解決できない")
    try:
        completed = subprocess.run(
            [str(Path(git).resolve()), *args], cwd=root, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise PredictionRunnerError(f"git 起動失敗: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise PredictionRunnerError(f"git {' '.join(args)} が失敗: {detail}")
    return completed.stdout


def _read_source_bytes(root: Path) -> dict[str, bytes]:
    result = {}
    for name, relative in _SOURCE_PATHS.items():
        try:
            result[name] = (root / relative).read_bytes()
        except OSError as exc:
            raise PredictionRunnerError(f"source を read-once できない: {relative}: {exc}") from exc
    return result


def _source_records(*, frozen_bytes: Mapping[str, bytes]) -> dict:
    result = {}
    for name, relative in _SOURCE_PATHS.items():
        if name not in frozen_bytes or not isinstance(frozen_bytes[name], bytes):
            raise PredictionRunnerError(f"source read-once bytes がない: {name}")
        raw = frozen_bytes[name]
        result[name] = {"path": str(relative), "sha256": _sha256(raw)}
    return result


def _assert_seal_worktree_clean(root: Path) -> None:
    raw = _git_bytes(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    allowed_prefix = _JOURNAL_PATH.parent.as_posix() + "/"
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        if not entry.startswith(b"?? "):
            raise PredictionRunnerError("seal は selector-runs 外の clean worktree 必須")
        try:
            path = entry[3:].decode("utf-8")
        except UnicodeError as exc:
            raise PredictionRunnerError("git status path が UTF-8 でない") from exc
        if not path.startswith(allowed_prefix):
            raise PredictionRunnerError("seal は selector-runs 外の clean worktree 必須")


def _derive_protocol_bytes(root: Path) -> bytes:
    try:
        if __package__ in {None, ""}:  # pragma: no cover
            from orchestrator.campaign import s8b_approved, s8b_floor_campaign
        else:
            from . import s8b_approved, s8b_floor_campaign
        built = s8b_floor_campaign.build_protocol_document(
            s8b_approved.APPROVED_MASTER_SEED,
            s8b_approved.APPROVED_ENV_TAG,
            stock_configuration=s8b_approved.APPROVED_STOCK_CONFIGURATION,
            extime_s=s8b_approved.APPROVED_EXTIME_S,
            wired_min_rel_floor=s8b_approved.APPROVED_WIRED_MIN_REL_FLOOR,
            root=root,
        )
    except Exception as exc:
        raise PredictionRunnerError(f"承認定数から protocol を再導出できない: {exc}") from exc
    return built.canonical_bytes


def seal(
    *, pre_oracle_head: str, provider_kind: str = "unwired", root: Path = ROOT,
    provider_runner: Callable[..., Any] = subprocess.run,
    claude_executable: str | os.PathLike[str] = "claude",
) -> dict:
    """正規 path だけを使い protocol pin → 実走 → disk reload verify まで封印する。"""
    root = Path(root).resolve()
    if not isinstance(pre_oracle_head, str) or _GIT_SHA_RE.fullmatch(pre_oracle_head) is None:
        raise PredictionRunnerError("--pre-oracle-head は40桁 lowercase hex 必須")
    actual_head = _git_bytes(root, ["rev-parse", "HEAD"]).decode("ascii").strip()
    if actual_head != pre_oracle_head:
        raise PredictionRunnerError(
            f"--pre-oracle-head が現在 HEAD と不一致: {pre_oracle_head} != {actual_head}"
        )
    _assert_seal_worktree_clean(root)
    predictions_path = root / _PREDICTIONS_PATH
    if predictions_path.exists() or predictions_path.is_symlink():
        raise PredictionRunnerError("selector_predictions.json が既に存在する")
    source_bytes = _read_source_bytes(root)
    if provider_kind == "unwired":
        raise PredictionRunnerError(
            "実走には --provider claude-headless の明示 opt-in が必要"
        )
    if provider_kind != PROVIDER_KIND_CLAUDE_HEADLESS:
        raise PredictionRunnerError(f"未知 provider: {provider_kind!r}")

    committed_protocol = _git_bytes(
        root, ["cat-file", "blob", f"{pre_oracle_head}:{_PROTOCOL_PATH.as_posix()}"],
    )
    derived_protocol = _derive_protocol_bytes(root)
    if committed_protocol != derived_protocol:
        raise PredictionRunnerError(
            "HEAD floor_protocol.json blob bytes が承認定数からの canonical 再導出と不一致"
        )
    try:
        freeze_bytes = source_bytes["holdout_freeze"]
        role_bytes = source_bytes["role"]
        parser_bytes = (root / _PARSER_MODULE_PATH).read_bytes()
    except OSError as exc:
        raise PredictionRunnerError(f"seal source を read-once できない: {exc}") from exc
    # selector prediction は v1 freeze に対して封印される (C2-7)。read-once した bytes を
    # v1 trust root と照合し、差し替え freeze からの封印を fail-closed で拒否する。
    if _sha256(freeze_bytes) != V1_FREEZE_SHA256:
        raise PredictionRunnerError(
            "holdout freeze bytes が v1 trust root と不一致 (C2-7): "
            f"実 {_sha256(freeze_bytes)} != v1 {V1_FREEZE_SHA256}"
        )
    freeze = _parse_json_object(freeze_bytes, source=root / _FREEZE_PATH)
    artifact_root = root / _JOURNAL_PATH.parent
    provider = ClaudeHeadlessProvider(
        artifact_root=artifact_root, role_file=root / _ROLE_PATH,
        role_bytes=role_bytes, repository_root=root,
        executable=claude_executable, runner=provider_runner,
    )
    if provider.role_file_sha256 != _sha256(role_bytes):
        raise PredictionRunnerError("role read-once bytes と provider preflight sha が不一致")
    binding = JournalBinding(
        pre_oracle_head=pre_oracle_head,
        protocol_sha256=_sha256(committed_protocol),
        freeze_sha256=_sha256(freeze_bytes),
        provider_kind=provider.provider_kind,
        role_file_sha256=provider.role_file_sha256,
        parser_module_sha256=_sha256(parser_bytes),
        claude_executable_path=provider.executable,
        claude_executable_sha256=provider.executable_sha256,
        known_cells=frozenset(
            (job["target_holdout"], job["arm"])
            for job in build_prediction_jobs(freeze)
        ),
    )
    journal = PredictionJournal(root / _JOURNAL_PATH)
    ensure_run_header(journal, binding=binding)
    drive_journal(
        freeze=freeze, journal=journal, artifact_root=artifact_root,
        root=root, binding=binding, provider=provider,
    )
    sources = _source_records(frozen_bytes=source_bytes)
    document = materialize_predictions(
        freeze=freeze, journal=journal, predictions_path=predictions_path,
        generated_at=_now_iso(), pre_oracle_head=pre_oracle_head,
        sources=sources, execution_policy=_EXECUTION_POLICY, binding=binding,
    )
    try:
        destination_bytes = predictions_path.read_bytes()
    except OSError as exc:
        raise PredictionRunnerError(f"書込済み prediction を reload できない: {exc}") from exc
    reloaded = _parse_json_object(destination_bytes, source=predictions_path)
    try:
        verify_prediction_freeze(reloaded, freeze=freeze, root=root)
    except Exception as exc:
        raise PredictionRunnerError(f"disk reload prediction verify 失敗: {exc}") from exc
    if reloaded != document:
        raise PredictionRunnerError("disk reload 文書が in-memory 文書と不一致")
    return reloaded


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8b selector prediction 実走・封印")
    subparsers = parser.add_subparsers(dest="command", required=True)
    seal_parser = subparsers.add_parser("seal", help="正規 path へ prediction を封印する")
    seal_parser.add_argument(
        "--provider", choices=("unwired", PROVIDER_KIND_CLAUDE_HEADLESS),
        default="unwired",
    )
    seal_parser.add_argument("--pre-oracle-head", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None, *, root: Path = ROOT,
    provider_runner: Callable[..., Any] = subprocess.run,
    claude_executable: str | os.PathLike[str] = "claude",
    stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr,
) -> int:
    args = _parser().parse_args(argv)
    try:
        document = seal(
            pre_oracle_head=args.pre_oracle_head, provider_kind=args.provider,
            root=root, provider_runner=provider_runner,
            claude_executable=claude_executable,
        )
    except PredictionRunnerError as exc:
        print(f"fails-closed: {exc}", file=stderr)
        return 1
    print(json.dumps({
        "status": "sealed",
        "path": str(_PREDICTIONS_PATH),
        "body_sha256": document["body_sha256"],
    }, ensure_ascii=False, sort_keys=True), file=stdout)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
