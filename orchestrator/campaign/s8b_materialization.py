# -*- coding: utf-8 -*-
"""8b binding identity / 実体化の共有 producer モジュール。

oracle driver と floor campaign が共有する binding identity 生成と使い捨て worktree の
実体化契約、および ratified freeze entry と実体化 source を束縛する review capability を
単一正本として持つ。binding_sha256 の canonical 化 helper もここが producer 側の唯一の
定義である。

依存方向: このモジュールは ``s1_direct_comparison`` (PreparedCell / prepare_cell)・``pipeline``
(variant_id)・``build_admission`` / ``source_digest``・標準ライブラリだけに依存する。
``s8b_oracle_driver`` / ``s8b_floor_campaign`` を import してはいけない (逆 import 禁止 —
``materialization → s1 → pipeline`` の acyclic を保つ)。
consumer 側の例外契約 (OracleDriverError / FloorCampaignError) への変換は各 consumer が境界で行う。

review capability は canonical body と内部一貫性を証明するだけで、人間の真正な review 行為を
認証しない。同一 process の issuer、shell materializer、calibrator の任意 executable path、
S8b content-addressed store の resume loader は閉じておらず、security credit を与えない。
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import sys
from pathlib import Path
from typing import Mapping

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import pipeline  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    REVIEW_RECEIPT_SCHEMA,
    ReviewId,
    ReviewReceipt,
    verify_review_receipt,
)
from campaign.materializer_admission import (  # noqa: E402
    CLOSED_PYTHON_MATERIALIZER_SITES,
)
from campaign.s1_direct_comparison import PreparedCell, prepare_cell  # noqa: E402
from campaign.source_digest import SourceEvidence  # noqa: E402
from campaign.trigger_gate_language import TRIGGER_GATE_LANGUAGE  # noqa: E402


# Compatibility view for the repository-wide AST closure sentinel.  The sole
# registrations and their admitted/non-admissible dispositions live in
# materializer_admission; this module owns no second registry.
NON_ADMISSIBLE_MATERIALIZERS = CLOSED_PYTHON_MATERIALIZER_SITES

NON_TRIGGER_BINDING_KEYS = frozenset({
    "genome_canonical", "src_token", "variant_id", "entry_sha256",
    "binding_sha256",
})
TRIGGER_BINDING_KEYS = NON_TRIGGER_BINDING_KEYS | frozenset({
    "trigger_gate_language", "trigger_gate_implementation_sha256",
})


class MaterializationError(RuntimeError):
    """binding identity 生成・cell 実体化の入力・契約を検証できない場合の拒否。"""


def _canonical_bytes(value) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MaterializationError(f"canonical JSON に変換できない: {exc}") from exc


def _canonical_sha256(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _admission_receipt_sha256(value) -> str:
    """build_admission の canonical JSON (ensure_ascii=True) と exact 同型。"""
    rendered = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def reviewed_source_capability(
        *, review_id: ReviewId, source: SourceEvidence,
        input_sha256: str) -> ReviewReceipt:
    """Ratified freeze input と exact source evidence を canonical review body に束縛する。

    ``verify_review_receipt`` が構造と source equality を再検証する。これは署名付き human
    attestation の発行器ではなく、freeze ratification の process-local projection である。
    """
    if type(review_id) is not ReviewId:
        raise MaterializationError("review_id が registered ReviewId の exact member でない")
    if type(source) is not SourceEvidence:
        raise MaterializationError("source が resolve_evidence() 由来の exact value でない")
    body = {
        "schema": REVIEW_RECEIPT_SCHEMA,
        "review_id": review_id.value,
        "source": source.as_receipt(),
        "input_sha256": input_sha256,
    }
    body["receipt_sha256"] = _admission_receipt_sha256(body)
    try:
        return verify_review_receipt(review_id, source, receipt=body)
    except (TypeError, ValueError, RuntimeError) as exc:
        raise MaterializationError(f"review capability を束縛できない: {exc}") from exc


def binding_entry(freeze: Mapping, holdout_id: str, configuration_id: str) -> Mapping:
    try:
        holdout = freeze["holdouts"][holdout_id]
        binding = holdout["variant_binding"]
        entry = binding["entries"][configuration_id]
    except (KeyError, TypeError) as exc:
        raise MaterializationError(
            f"freeze binding がない: holdout={holdout_id} configuration={configuration_id}"
        ) from exc
    if not isinstance(entry, Mapping):
        raise MaterializationError("freeze binding entry が object でない")
    return entry


def binding_from_prepared(entry: Mapping, prepared: PreparedCell) -> dict:
    if not isinstance(prepared, PreparedCell):
        raise MaterializationError("prepare_fn の戻り値が PreparedCell でない")
    identity = {
        "genome_canonical": prepared.genome.canonical(),
        "src_token": prepared.src_token,
        "variant_id": pipeline.variant_id(prepared.genome, prepared.src_token),
        "entry_sha256": _canonical_sha256(entry),
    }
    evidence = prepared.source_evidence
    if evidence is not None:
        if type(evidence) is not SourceEvidence:
            raise MaterializationError("PreparedCell source_evidence の型が不正")
        if evidence.schema_version == "source-evidence/v2":
            if (evidence.trigger_gate_language != TRIGGER_GATE_LANGUAGE
                    or not isinstance(
                        evidence.trigger_gate_implementation_sha256, str,
                    )):
                raise MaterializationError("trigger source evidence binding が不正")
            identity.update({
                "trigger_gate_language": evidence.trigger_gate_language,
                "trigger_gate_implementation_sha256": (
                    evidence.trigger_gate_implementation_sha256
                ),
            })
        elif evidence.schema_version != "source-evidence/v1":
            raise MaterializationError("source evidence schema が binding 非対応")
    identity["binding_sha256"] = _canonical_sha256(identity)
    return identity


def binding_preimage(value: Mapping) -> dict:
    """Return an exact current binding preimage for either admitted shape."""
    if not isinstance(value, Mapping):
        raise MaterializationError("binding identity が object でない")
    keys = frozenset(value)
    if keys not in {NON_TRIGGER_BINDING_KEYS, TRIGGER_BINDING_KEYS}:
        raise MaterializationError("binding identity exact key 集合が不正")
    preimage = {
        key: value[key] for key in sorted(keys - {"binding_sha256"})
    }
    if value.get("binding_sha256") != _canonical_sha256(preimage):
        raise MaterializationError("binding identity sha256 が再計算不一致")
    if keys == TRIGGER_BINDING_KEYS:
        if value.get("trigger_gate_language") != TRIGGER_GATE_LANGUAGE:
            raise MaterializationError("binding trigger gate language が不正")
        digest = value.get("trigger_gate_implementation_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(ch not in "0123456789abcdef" for ch in digest)):
            raise MaterializationError("binding trigger implementation sha256 が不正")
    return preimage


def binding_matches_after_reinspection(
        expected: Mapping, actual: Mapping) -> bool:
    """Compare current bindings, or one legacy trigger subset, without mutation.

    ``actual`` must have been produced from a freshly materialized ``PreparedCell``.
    A trigger-shaped actual value therefore carries SourceEvidence v2 from the real
    source recognizer.  Dropping its two trigger fields is permitted only for this
    comparison; no caller may persist the projection as a current binding.
    """
    try:
        binding_preimage(actual)
    except MaterializationError:
        return False
    if _canonical_bytes(expected) == _canonical_bytes(actual):
        return True
    if frozenset(actual) != TRIGGER_BINDING_KEYS:
        return False
    legacy = {
        key: actual[key]
        for key in NON_TRIGGER_BINDING_KEYS - {"binding_sha256"}
    }
    legacy["binding_sha256"] = _canonical_sha256(legacy)
    return _canonical_bytes(expected) == _canonical_bytes(legacy)


@contextlib.contextmanager
def prepared_binding(
        *, freeze: Mapping, holdout_id: str, configuration_id: str,
        ccbench_pin: str, prepare_fn):
    entry = binding_entry(freeze, holdout_id, configuration_id)
    cell = {"configuration": configuration_id, "variant": entry}
    resource = prepare_fn(cell, ccbench_pin)
    manager = (resource if hasattr(resource, "__enter__") and hasattr(resource, "__exit__")
               else contextlib.nullcontext(resource))
    with manager as prepared:
        yield binding_from_prepared(entry, prepared), prepared


def prepare_binding(
        *, freeze, holdout_id, configuration_id, ccbench_pin,
        prepare_fn=prepare_cell) -> dict:
    """freeze entry を S-1 materializer で実体化し、完全 binding identity を返す。"""
    with prepared_binding(
            freeze=freeze, holdout_id=holdout_id,
            configuration_id=configuration_id, ccbench_pin=ccbench_pin,
            prepare_fn=prepare_fn) as (identity, _prepared):
        return identity
