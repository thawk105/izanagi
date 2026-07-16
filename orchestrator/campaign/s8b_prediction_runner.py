# -*- coding: utf-8 -*-
"""段 8b R3 層 — trusted prediction runner (append-only journal 上の at-most-once 駆動)。

契約 (`output/insights/2026-07-16_s8b-freeze-v2-design-material.md` の「R3 層」節):

- **at-most-once + 結果不明 crash は当該セル missing で恒久確定 (再呼出なし)。**
  exactly-once はローカル台帳では実現不能なので採らない (F14 型の宣言のみ遮断を避ける,
  `docs/failures.md:125`)。claim を call の前に durable 化し、call 後に invocation receipt を
  書く。claim と invocation の間の crash は当該セルを missing のまま恒久確定させ、**再呼出も
  fallback もしない** (§9 項 4/5、`docs/phase3-8b-descriptor-design.md:292-300`)。
- append-only journal に durable claim を先行させ、canonical payload (byte 固定)・実 invocation
  receipt・raw 応答 bytes を束縛する。claim なき応答・二重 claim はどちらも protocol violation。
- off arm (2 セル) は invocation record を持たない ``static_default`` の static terminal record
  で、agent 呼出と journal 上で構造的に区別する (§9 項 1)。
- selector の実応答受理は strict parser (``s8b_selector_output``) を唯一経路とする (§9 項 5)。
  parser を通らないセルは invalid として記録し、既定構成へ fallback しない。
- selector の実呼び出しは ``provider`` (callable) として注入する。production 呼び出しは未配線で
  あり (実走はまだ解禁されない)、既定 provider ``PRODUCTION_PROVIDER`` は claim を書く前に
  fail-closed で拒否する (claim を書いてから拒否すると journal を missing で汚染するため)。
- ``selector_predictions.json`` の封印は既存 ``s8b_selector_freeze`` API
  (``build_prediction_freeze`` + ``write_prediction_freeze``) に委譲し、exclusive-create +
  selector_basis 束縛をそのまま得る。

**selector_basis preimage の拡張は現行のまま。** 設計素材 R3 層は versioned preimage
(実送信 payload bytes・catalog bytes・descriptor projection・role・model 等) への拡張を挙げるが、
これは §8 再凍結事項 (`docs/phase3-8b-descriptor-design.md:255-267`) であり裁定・再凍結まで
発効しない。本 runner は現行 ``selector_basis_sha256`` を変更せずそのまま束縛に用いる。
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    import sys

    _ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
    if str(_ROOT_FOR_IMPORT) not in sys.path:
        sys.path.insert(0, str(_ROOT_FOR_IMPORT))
    from orchestrator.campaign.s8b_descriptor import descriptor_for_holdout
    from orchestrator.campaign.s8b_selector_freeze import (
        AGENT_DECISION_METHOD,
        STATIC_DECISION_METHOD,
        build_prediction_freeze,
        build_prediction_jobs,
        record_agent_attempt,
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
        build_prediction_freeze,
        build_prediction_jobs,
        record_agent_attempt,
        write_prediction_freeze,
    )
    from .s8b_selector_input import (
        STATIC_DEFAULT_CHOICE_ID,
        build_selector_payload,
        selector_payload_sha256,
    )


JOURNAL_SCHEMA_VERSION = "8b-prediction-journal/v1"
AGENT_ARMS = ("on", "swapped")
OFF_ARM = "off"
_RECORD_TYPES = {"claim", "invocation", "static_terminal"}
_CLAIM_KEYS = {
    "record_type", "seq", "target_holdout", "arm", "decision_method",
    "input_payload_sha256", "payload_path", "claimed_at",
}
_INVOCATION_KEYS = {
    "record_type", "seq", "target_holdout", "arm", "status", "choice_id",
    "rationale", "parser_error_code", "raw_response_path", "raw_sha256",
    "receipt",
}
_STATIC_KEYS = {
    "record_type", "seq", "target_holdout", "arm", "decision_method", "choice_id",
}


class PredictionRunnerError(RuntimeError):
    """R3 trusted prediction runner の at-most-once・journal 契約に対する fail-closed 拒否。"""


@dataclass(frozen=True)
class ProviderResponse:
    """注入 provider が返す単一 selector 実呼び出しの結果。

    ``raw_response`` は strict parser へそのまま渡す raw 文字列、``provenance`` は
    ``s8b_selector_freeze`` の agent_provenance schema (8 field) に一致させる。
    """

    raw_response: str
    provenance: Mapping[str, Any]


# provider の型: キーワード target_holdout/arm/payload を受け ProviderResponse を返す callable。
Provider = Callable[..., ProviderResponse]


def unwired_provider(*, target_holdout: str, arm: str, payload: Mapping) -> ProviderResponse:
    """production selector 実走は未配線 (実走は未解禁)。呼ばれたら fail-closed で拒否する。"""
    raise PredictionRunnerError(
        "selector の production 実走は未配線であり実走は未解禁: "
        "テスト/実装は provider を注入せよ"
    )


# production の既定 provider。drive は claim を書く前にこの sentinel を検出して拒否する。
PRODUCTION_PROVIDER: Provider = unwired_provider


@dataclass(frozen=True)
class CellStatus:
    """journal から解決した 1 セルの終端状態。

    kind: "unstarted" / "claimed_missing" (claim 後未解決 = 恒久 missing) /
    "resolved" (invocation 済み) / "static" (off arm の static terminal)。
    """

    target_holdout: str
    arm: str
    kind: str
    claim: Mapping[str, Any] | None = None
    invocation: Mapping[str, Any] | None = None
    static: Mapping[str, Any] | None = None


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _reject_duplicate_keys(pairs):
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise PredictionRunnerError(f"journal record に duplicate key: {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str):
    raise PredictionRunnerError(f"journal record に非有限数: {token}")


class PredictionJournal:
    """selector 予測の append-only JSONL journal。

    append は O_APPEND + fsync で durable 化し、read は 1 行 1 record を strict parse する
    (duplicate key・非有限数・非 object を拒否)。claim を call の前に durable 化する契約
    (at-most-once) を成立させる下位機構。
    """

    def __init__(self, path) -> None:
        self.path = Path(path)
        self._next_seq: int | None = None

    def read_records(self) -> list[dict]:
        """journal 全 record を append 順に strict parse して返す (欠損は空リスト)。"""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError) as exc:
            raise PredictionRunnerError(f"journal を読めない: {self.path}: {exc}") from exc
        records: list[dict] = []
        for index, line in enumerate(text.splitlines()):
            if not line.strip():
                continue
            try:
                value = json.loads(
                    line,
                    object_pairs_hook=_reject_duplicate_keys,
                    parse_constant=_reject_constant,
                )
            except (json.JSONDecodeError, PredictionRunnerError) as exc:
                raise PredictionRunnerError(
                    f"journal 行 {index} を parse できない: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise PredictionRunnerError(f"journal 行 {index} が object でない")
            records.append(value)
        return records

    def _reserve_seq(self) -> int:
        if self._next_seq is None:
            self._next_seq = len(self.read_records())
        seq = self._next_seq
        self._next_seq += 1
        return seq

    def append(self, record: Mapping[str, Any]) -> dict:
        """1 record を canonical 化し O_APPEND + fsync で durable に追記する。"""
        if not isinstance(record, Mapping):
            raise PredictionRunnerError("journal record は object でなければならない")
        stored = dict(record)
        stored["seq"] = self._reserve_seq()
        try:
            line = json.dumps(stored, ensure_ascii=False, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError) as exc:
            self._next_seq -= 1  # type: ignore[operator]
            raise PredictionRunnerError("journal record を JSON 化できない") from exc
        payload = (line + "\n").encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644,
        )
        try:
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        directory_fd = os.open(self.path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return stored


def _validate_record_shape(record: Mapping, *, index: int) -> str:
    rt = record.get("record_type")
    if rt not in _RECORD_TYPES:
        raise PredictionRunnerError(f"journal[{index}] の record_type が不正: {rt!r}")
    expected = {
        "claim": _CLAIM_KEYS,
        "invocation": _INVOCATION_KEYS,
        "static_terminal": _STATIC_KEYS,
    }[rt]
    if set(record) != expected:
        raise PredictionRunnerError(
            f"journal[{index}] ({rt}) schema 不一致: "
            f"missing={sorted(expected - set(record))} "
            f"unknown={sorted(set(record) - expected)}"
        )
    target = record.get("target_holdout")
    arm = record.get("arm")
    if not isinstance(target, str) or not target:
        raise PredictionRunnerError(f"journal[{index}] の target_holdout が不正")
    if not isinstance(arm, str) or not arm:
        raise PredictionRunnerError(f"journal[{index}] の arm が不正")
    return rt


def resolve_journal(records: Sequence[Mapping]) -> dict[tuple[str, str], CellStatus]:
    """journal record 列を append 順に走査し、セル別終端状態へ畳み込む。

    protocol violation (claim なき invocation・二重 claim・二重 invocation・off セルの claim・
    static の重複) は即 fail-closed。crash 後の claim (invocation なし) は missing を残す。
    """
    claims: dict[tuple[str, str], Mapping] = {}
    invocations: dict[tuple[str, str], Mapping] = {}
    statics: dict[tuple[str, str], Mapping] = {}
    for index, record in enumerate(records):
        rt = _validate_record_shape(record, index=index)
        cell = (record["target_holdout"], record["arm"])
        arm = record["arm"]
        if rt == "claim":
            if arm not in AGENT_ARMS:
                raise PredictionRunnerError(
                    f"journal[{index}]: agent 以外の arm を claim できない: {cell!r}"
                )
            if cell in claims:
                raise PredictionRunnerError(
                    f"protocol violation: 二重 claim: {cell!r}"
                )
            if record.get("decision_method") != AGENT_DECISION_METHOD:
                raise PredictionRunnerError(
                    f"journal[{index}]: claim の decision_method が不正: {cell!r}"
                )
            claims[cell] = record
        elif rt == "invocation":
            if cell not in claims:
                raise PredictionRunnerError(
                    f"protocol violation: claim なき invocation: {cell!r}"
                )
            if cell in invocations:
                raise PredictionRunnerError(
                    f"protocol violation: 二重 invocation: {cell!r}"
                )
            invocations[cell] = record
        else:  # static_terminal
            if arm != OFF_ARM:
                raise PredictionRunnerError(
                    f"journal[{index}]: static_terminal は off arm 専用: {cell!r}"
                )
            if record.get("decision_method") != STATIC_DECISION_METHOD:
                raise PredictionRunnerError(
                    f"journal[{index}]: static_terminal の decision_method が不正: {cell!r}"
                )
            if record.get("choice_id") != STATIC_DEFAULT_CHOICE_ID:
                raise PredictionRunnerError(
                    f"journal[{index}]: static_terminal の choice_id が既定値でない: {cell!r}"
                )
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
            f"再構成 payload の sha256 が job と不一致: {job['target_holdout']}/{job['arm']}"
        )
    return payload


def _write_bytes_bound(path: Path, data: bytes) -> str:
    """byte 列を fsync 付きで書き、その sha256 を返す (byte 固定束縛の下位)。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    return hashlib.sha256(data).hexdigest()


def drive_journal(
    *,
    freeze: Mapping,
    journal: PredictionJournal,
    artifact_root: Path,
    root: Path,
    provider: Provider = PRODUCTION_PROVIDER,
) -> dict[tuple[str, str], CellStatus]:
    """6 セルを journal 上で at-most-once に駆動し、解決済み状態を返す。

    - off arm: invocation を持たない static terminal record を書く。
    - agent arm: 既 resolved は skip (再起動時 idempotent)、claim 済み未解決 (crash) は
      **再呼出せず** missing のまま skip、未着手のみ claim → provider 呼び出し → invocation。
    - claim は provider 呼び出しの前に durable 化する。provider が未配線 (production) の場合は
      claim を書く前に拒否し journal を汚染しない。

    payload/raw の bytes は ``artifact_root`` 配下に書き、journal には ``root`` からの相対 path を
    記録する (最終 freeze の raw_response_path が root 相対でなければならないため)。
    """
    artifact_root = Path(artifact_root)
    root = Path(root)
    jobs = build_prediction_jobs(freeze)
    statuses = resolve_journal(journal.read_records())

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
            # resolved は再呼出しない。claimed_missing (claim 後 crash) も再呼出せず
            # missing のまま恒久確定する (§9 項 4/5)。
            continue

        # 未着手セル: provider 未配線なら claim を書く前に拒否する (journal を汚染しない)。
        if provider is PRODUCTION_PROVIDER:
            raise PredictionRunnerError(
                f"selector 実走は未解禁 (provider 未配線): {cell!r}"
            )

        payload = _payload_for_job(freeze, job)
        payload_bytes = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
        )
        payload_path = artifact_root / f"payload_{job['target_holdout']}_{arm}.json"
        _write_bytes_bound(payload_path, payload_bytes)

        # --- durable claim を call の前に書く (at-most-once の要) ---
        journal.append({
            "record_type": "claim",
            "target_holdout": job["target_holdout"],
            "arm": arm,
            "decision_method": AGENT_DECISION_METHOD,
            "input_payload_sha256": job["input_payload_sha256"],
            "payload_path": str(payload_path.relative_to(root)),
            "claimed_at": _now_iso(),
        })

        # --- 実 invocation。ここで crash すると当該セルは missing 恒久確定 (再呼出なし) ---
        response = provider(
            target_holdout=job["target_holdout"], arm=arm, payload=copy.deepcopy(payload),
        )
        if not isinstance(response, ProviderResponse):
            raise PredictionRunnerError("provider は ProviderResponse を返さねばならない")
        if not isinstance(response.raw_response, str):
            raise PredictionRunnerError("provider raw_response は str でなければならない")

        raw_bytes = response.raw_response.encode("utf-8")
        raw_path = artifact_root / f"raw_{job['target_holdout']}_{arm}.txt"
        raw_sha256 = _write_bytes_bound(raw_path, raw_bytes)

        # strict parser を唯一の応答受理経路にする (record_agent_attempt は
        # parse_selector_output を用い、不正出力へ fallback しない)。
        attempt = record_agent_attempt(job=job, raw_output=response.raw_response)
        if attempt["raw_sha256"] != raw_sha256:
            raise PredictionRunnerError("raw 応答 bytes と parser の sha256 が不一致")

        journal.append({
            "record_type": "invocation",
            "target_holdout": job["target_holdout"],
            "arm": arm,
            "status": attempt["status"],
            "choice_id": attempt.get("choice_id"),
            "rationale": attempt.get("rationale"),
            "parser_error_code": attempt.get("parser_error_code"),
            "raw_response_path": str(raw_path.relative_to(root)),
            "raw_sha256": raw_sha256,
            "receipt": copy.deepcopy(dict(response.provenance)),
        })

    return resolve_journal(journal.read_records())


def build_rows_from_journal(
    freeze: Mapping, journal: PredictionJournal,
) -> list[dict]:
    """解決済み journal を ``build_prediction_freeze`` 用の 6 行へ射影する。

    missing (claim 後 crash) セルが残る間は freeze を組めない (fail-closed)。missing セルを
    ``choice_id=null`` で凍結する経路 (§9 項 5) は現行 selector freeze schema が agent row に
    provenance を要求するため本 runner では成立せず、materialize は拒否する。
    """
    jobs = build_prediction_jobs(freeze)
    statuses = resolve_journal(journal.read_records())
    rows: list[dict] = []
    for job in jobs:
        cell = (job["target_holdout"], job["arm"])
        arm = job["arm"]
        status = statuses.get(cell)
        if arm == OFF_ARM:
            if status is None or status.kind != "static":
                raise PredictionRunnerError(f"off セルの static terminal がない: {cell!r}")
            rows.append({
                "target_holdout": job["target_holdout"],
                "arm": arm,
                "descriptor_source_holdout": None,
                "decision_method": STATIC_DECISION_METHOD,
                "status": "valid",
                "choice_id": STATIC_DEFAULT_CHOICE_ID,
                "input_payload_sha256": None,
                "rationale": None,
                "raw_response_path": None,
                "raw_sha256": None,
                "parser_error_code": None,
                "agent_provenance": None,
            })
            continue
        if status is None:
            raise PredictionRunnerError(f"agent セルが未着手: {cell!r}")
        if status.kind == "claimed_missing":
            raise PredictionRunnerError(
                f"agent セルが missing (claim 後未解決) のため freeze 不能: {cell!r}"
            )
        invocation = status.invocation
        claim = status.claim
        assert invocation is not None and claim is not None  # resolved 不変条件
        # claim が束縛した canonical payload (byte 固定) を job と fail-closed 照合する。
        # これがないと freeze A で駆動した invocation を別 descriptor の freeze B の job
        # (同一 holdout ID・derangement) へ付け替えても照合が恒真に通り、agent が実際に
        # 見た payload と異なる descriptor を消費したと誤って certified される (provenance
        # 汚染)。claim の sha は drive 時に _payload_for_job が job と一致確認済みなので、
        # ここで claim と job を照合すれば journal と freeze の束縛が発火する。
        if claim["input_payload_sha256"] != job["input_payload_sha256"]:
            raise PredictionRunnerError(
                "claim payload sha が job と不一致 (freeze/journal 束縛違反): "
                f"{cell!r} claim={claim['input_payload_sha256']!r} "
                f"job={job['input_payload_sha256']!r}"
            )
        rows.append({
            "target_holdout": job["target_holdout"],
            "arm": arm,
            "descriptor_source_holdout": job["descriptor_source_holdout"],
            "decision_method": AGENT_DECISION_METHOD,
            "status": invocation["status"],
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
    *,
    freeze: Mapping,
    journal: PredictionJournal,
    predictions_path,
    generated_at: str,
    pre_oracle_head: str,
    sources: Mapping,
    execution_policy: Mapping,
) -> dict:
    """解決済み journal から ``selector_predictions.json`` を封印する。

    封印は既存 ``s8b_selector_freeze`` API に委譲する: ``build_prediction_freeze`` が
    selector_basis を束縛し、``write_prediction_freeze`` が exclusive-create で書く。
    """
    rows = build_rows_from_journal(freeze, journal)
    document = build_prediction_freeze(
        freeze=freeze,
        rows=rows,
        generated_at=generated_at,
        pre_oracle_head=pre_oracle_head,
        sources=sources,
        execution_policy=execution_policy,
    )
    write_prediction_freeze(predictions_path, document)
    return document
