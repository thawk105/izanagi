# -*- coding: utf-8 -*-
"""8b binding identity / 実体化の共有 producer モジュール。

oracle driver と floor campaign が共有する binding identity 生成と使い捨て worktree の
実体化契約を単一正本として持つ。binding_sha256 の canonical 化 helper もここが producer 側の
唯一の定義である。

依存方向: このモジュールは ``s1_direct_comparison`` (PreparedCell / prepare_cell)・``pipeline``
(variant_id)・標準ライブラリだけに依存する。``s8b_oracle_driver`` / ``s8b_floor_campaign`` を
import してはいけない (逆 import 禁止 — ``materialization → s1 → pipeline`` の acyclic を保つ)。
consumer 側の例外契約 (OracleDriverError / FloorCampaignError) への変換は各 consumer が境界で行い、
本モジュールは ``MaterializationError`` だけを送出する。
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
from campaign.s1_direct_comparison import PreparedCell, prepare_cell  # noqa: E402


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
    identity["binding_sha256"] = _canonical_sha256(identity)
    return identity


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
