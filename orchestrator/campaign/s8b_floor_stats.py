# -*- coding: utf-8 -*-
"""s8b floor 統計の純関数モジュール (formula v1 の実装正本)。

段 8b oracle の **採否丸め閾値 (floor)** を、holdout×構成のセル計測から算出する記述的
統計を、I/O・環境参照を一切持たない純関数として実装する。実機ドライバ・レポータは本モジュール
を通してのみ floor を得る (自前で式を持たない)。生成側と検証側が同一関数を通るので、
`verify_floor_artifact` は自己申告値を厳密 (==) 比較で照合できる。

**この floor は記述的な効果量 (block 対比 delta) + noise gate (session-median の散らばり) で
あり、α・検定力を保証する検定ではない。** 「有意」とは呼ばない。u_noise は 2 群の session-median
標準偏差の RSS、delta は block 間の対比差の絶対値で、いずれも「差がその大きさ未満なら run 間
ノイズと区別できない」という下限を与える。

算出式 (formula_id = FORMULA_ID) はセルの有効性契約・floor 合成・scalar 代替・診断まで含めて
本モジュールが正本である。**式を変えるときは FORMULA_ID を改版し、凍結案パッケージ
(output/insights/2026-07-16_s8b-floor-protocol-package.md) の formula v1 と §8 再凍結事項を
同時に更新する。** コードとパッケージ本文で式が一字一句一致していること。

fail-closed 契約 (絶対規律): 縮退・欠測・不正入力はすべて null/判定不能へ倒す。
- 無効 session は median を作らない (fallback 値を代入しない)。
- stock セルが無効なら当該 holdout の floor は未確定 = 全 pair null (holdout ごと丸ごと落とす)。
- stock 以外のセル c が無効なら floor_pair(c) のみ null。他 pair に veto しない。
- scalar 代替はいずれかの pair が null なら null (max を欠測で盛らない)。
- protocol config (n_sessions / blocks / replicates_per_block / stock / wired_min_rel_floor) は
  すべて呼び出し側からの入力必須。本モジュールは未凍結数値のデフォルトを内蔵しない (F14 対策)。
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

FORMULA_ID = "s8b-floor-stats/v1"


# ---------------------------------------------------------------------------
# 入力レコード
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SessionRecord:
    """1 セッション (= 実 campaign の 1 measure_point と同形) の生計測。

    throughputs は「成功した rep の tps」列であり、reps_expected 本揃って初めて有効。
    exec_failures / excluded_reason / 非有限・非正値はいずれも session を無効にする。
    """
    cell_id: str
    holdout_id: str
    configuration_id: str
    block: int                       # 1-origin の block 番号
    seq: int                         # holdout×構成内のセッション連番 (順序の決定性用)
    throughputs: tuple                # tuple[float, ...] — 成功 rep の tps
    reps_expected: int
    exec_failures: int
    excluded_reason: Optional[str]
    retry: bool


def session_median(rec: SessionRecord) -> Optional[float]:
    """有効 session の session_median = statistics.median(throughputs)。無効なら None。

    有効性 ⇔ excluded_reason が None ∧ exec_failures == 0 ∧
    len(throughputs) == reps_expected ∧ 全値が math.isfinite かつ > 0。
    無効 session は median を作らない (fallback を返さない)。
    """
    if rec.excluded_reason is not None:
        return None
    if rec.exec_failures != 0:
        return None
    tps = rec.throughputs
    if len(tps) != rec.reps_expected:
        return None
    if rec.reps_expected <= 0:
        # 期待 rep が 0 以下なら medians の母集団が定義できない = 判定不能。
        return None
    for v in tps:
        if not isinstance(v, (int, float)):
            return None
        if not math.isfinite(v) or v <= 0:
            return None
    return statistics.median(tps)


# ---------------------------------------------------------------------------
# セル統計
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CellStats:
    """セル c (holdout×構成) の記述統計。

    valid=False のとき m/s/cv/block_medians が None でも部分診断値は保持しうるが、
    holdout_floors は valid=True のセルしか floor 合成に使わない (無効は null へ倒す)。
    """
    cell_id: str
    n_valid: int
    medians: tuple                        # 有効 session medians (block,seq 昇順)
    m: Optional[float]                    # statistics.median(medians)
    s: Optional[float]                    # statistics.stdev(medians) — n-1、要 2 点以上
    block_medians: Optional[dict]        # {block: median(その block の有効 medians)}、無効時 None
    valid: bool
    cv: Optional[float]                  # s / statistics.fmean(medians) — 診断
    notes: tuple = ()                     # 無効理由等 (人間可読)


def cell_stats(records: Sequence[SessionRecord], *, n_sessions: int, blocks: int,
               replicates_per_block: int) -> CellStats:
    """1 セルの有効 session medians から CellStats を組む。

    セル有効 ⇔ 有効 session 数 == n_sessions ∧ 各 block (1..blocks) が
    replicates_per_block 本ずつ揃う ∧ 全レコードの cell_id が一致 ∧ 有効レコードの
    block が 1..blocks の範囲内。s は statistics.stdev (n-1、要 2 点以上)。
    block_medians は有効時のみ dict、無効時 None。
    """
    notes: list = []
    cell_id = records[0].cell_id if records else ""
    if not records:
        notes.append("レコードが空")

    # cell_id の一貫性 (混入検知、fail-closed)。
    mixed = sorted({r.cell_id for r in records})
    if len(mixed) > 1:
        notes.append(f"cell_id 不一致: {mixed}")

    expected_blocks = tuple(range(1, blocks + 1))

    # 有効 session を (block, seq) 昇順に。順序の決定性は verify の == 照合に効く。
    valid_recs = [r for r in records if session_median(r) is not None]
    valid_recs.sort(key=lambda r: (r.block, r.seq))
    medians = tuple(session_median(r) for r in valid_recs)  # 全て非 None
    n_valid = len(medians)

    # block 外れ値の検知。
    out_of_range = sorted({r.block for r in valid_recs if r.block not in expected_blocks})
    if out_of_range:
        notes.append(f"expected 範囲外の block: {out_of_range} (期待 1..{blocks})")

    # block ごとの有効本数。
    per_block: dict = {}
    for r in valid_recs:
        per_block.setdefault(r.block, []).append(session_median(r))

    m = statistics.median(medians) if n_valid >= 1 else None
    s = statistics.stdev(medians) if n_valid >= 2 else None
    cv: Optional[float] = None
    if s is not None:
        mean = statistics.fmean(medians)
        cv = s / mean if mean > 0 else None

    # セル有効性。
    valid = (len(mixed) <= 1 and not out_of_range and n_valid == n_sessions)
    if n_valid != n_sessions:
        notes.append(f"有効 session 数 {n_valid} != n_sessions {n_sessions}")
    for b in expected_blocks:
        cnt = len(per_block.get(b, ()))
        if cnt != replicates_per_block:
            valid = False
            notes.append(f"block {b}: 有効 {cnt} 本 != replicates_per_block {replicates_per_block}")

    block_medians: Optional[dict] = None
    if valid:
        block_medians = {b: statistics.median(per_block[b]) for b in expected_blocks}

    return CellStats(cell_id=cell_id, n_valid=n_valid, medians=medians, m=m, s=s,
                     block_medians=block_medians, valid=valid, cv=cv, notes=tuple(notes))


# ---------------------------------------------------------------------------
# holdout の floor 合成
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HoldoutFloors:
    """1 holdout の pair 別 floor と scalar 代替。

    stock 無効 → 全 pair None + scale_ref None (holdout 未確定)。
    c 無効 → 当該 pair のみ None (他 pair に veto しない)。
    scalar_alt: 全 pair floor の max。いずれかが None なら None。
    scale_ref: m_stock (oracle 実走時の scale-adequacy gate 用)。
    """
    pairs: dict                          # {cell_id: floor_pair (float) | None}
    scalar_alt: Optional[float]
    scale_ref: Optional[float]
    diagnostics: dict


def holdout_floors(cells: Mapping[str, CellStats], *, stock_id: str,
                   wired_min_rel_floor: float) -> HoldoutFloors:
    """FORMULA v1 逐語:

        u_noise(c)   = sqrt(s_c^2 + s_stock^2)
        d_{c,b}      = m_{c,b} - m_{stock,b}   (b = 1, 2)
        delta_c      = |d_{c,1} - d_{c,2}|
        floor_pair(c)= max(u_noise(c), delta_c, wired_min_rel_floor × m_stock)

    stock (= stock_common セル) が無効/不在なら当該 holdout の全 pair は null、
    scale_ref も null (holdout 未確定)。c 無効 → その pair のみ null。
    """
    diagnostics: dict = {"stock_id": stock_id, "wired_min_rel_floor": wired_min_rel_floor,
                         "cells": {}}
    stock = cells.get(stock_id)
    stock_valid = stock is not None and stock.valid
    diagnostics["stock_valid"] = bool(stock_valid)

    pairs: dict = {}
    # 非 stock セル全てを列挙 (無効も null として明示的に載せる)。
    for cid in cells:
        if cid == stock_id:
            continue
        pairs[cid] = None  # 既定は判定不能。以下で確定できたときだけ上書き。

    if not stock_valid:
        # holdout 未確定。全 pair null、scale_ref null。
        diagnostics["reason"] = "stock セル無効/不在"
        return HoldoutFloors(pairs=pairs, scalar_alt=None, scale_ref=None,
                             diagnostics=diagnostics)

    m_stock = stock.m
    s_stock = stock.s
    bm_stock = stock.block_medians
    scale_ref = m_stock
    rel_floor = wired_min_rel_floor * m_stock

    # formula v1 は d_{c,b} を b=1,2 に固定した 2-block 専用式であり block_medians[1]/[2] を
    # 直接添字参照する。stock の block_medians がちょうど {1, 2} でなければ式の前提が破れて
    # いるので、ここで確実に落とす (validate_protocol の blocks==2 検査と対になる fail-closed
    # 二重防御。レビュー所見 F1-blocks-not-pinned-to-2)。
    if set(bm_stock) != {1, 2}:
        raise ValueError(
            f"holdout_floors: stock の block_medians が {{1, 2}} でない "
            f"(formula v1 は 2-block 固定): {sorted(bm_stock)}"
        )

    for cid, c in cells.items():
        if cid == stock_id:
            continue
        if not c.valid:
            diagnostics["cells"][cid] = {"floor": None, "reason": "セル無効"}
            continue
        if set(c.block_medians) != {1, 2}:
            raise ValueError(
                f"holdout_floors: セル {cid} の block_medians が {{1, 2}} でない "
                f"(formula v1 は 2-block 固定): {sorted(c.block_medians)}"
            )
        u_noise = math.sqrt(c.s ** 2 + s_stock ** 2)
        d1 = c.block_medians[1] - bm_stock[1]
        d2 = c.block_medians[2] - bm_stock[2]
        delta = abs(d1 - d2)
        floor_pair = max(u_noise, delta, rel_floor)
        pairs[cid] = floor_pair
        diagnostics["cells"][cid] = {
            "u_noise": u_noise, "delta": delta, "rel_floor": rel_floor,
            "d1": d1, "d2": d2, "floor": floor_pair, "cv": c.cv,
        }

    # scalar 代替: 全 pair の max。空 or いずれか null → null (欠測で盛らない)。
    vals = list(pairs.values())
    if not vals or any(v is None for v in vals):
        scalar_alt: Optional[float] = None
    else:
        scalar_alt = max(vals)

    return HoldoutFloors(pairs=pairs, scalar_alt=scalar_alt, scale_ref=scale_ref,
                         diagnostics=diagnostics)


# ---------------------------------------------------------------------------
# 自己申告値の検証 (生データからの再計算と厳密照合)
# ---------------------------------------------------------------------------
_REQUIRED_CONFIG = ("n_sessions", "blocks", "replicates_per_block",
                    "stock_configuration_id", "wired_min_rel_floor")
_REQUIRED_SESSION = ("cell_id", "holdout_id", "configuration_id", "block", "seq",
                     "throughputs", "reps_expected", "exec_failures",
                     "excluded_reason", "retry")


def _record_from_mapping(d: Mapping) -> SessionRecord:
    """session 生データ dict を SessionRecord に厳密変換 (欠損キーは KeyError)。"""
    return SessionRecord(
        cell_id=d["cell_id"],
        holdout_id=d["holdout_id"],
        configuration_id=d["configuration_id"],
        block=int(d["block"]),
        seq=int(d["seq"]),
        throughputs=tuple(d["throughputs"]),
        reps_expected=int(d["reps_expected"]),
        exec_failures=int(d["exec_failures"]),
        excluded_reason=d["excluded_reason"],
        retry=bool(d["retry"]),
    )


def _cmp(ctx: str, name: str, reported, computed, out: list) -> None:
    if reported != computed:
        out.append(f"{ctx}: {name} 齟齬 (申告 {reported!r} != 再計算 {computed!r})")


def verify_floor_artifact(artifact: Mapping) -> list:
    """artifact の生 session データから cells/floors を再計算し、自己申告値と厳密比較する。

    artifact の想定形:
        {
          "config": {n_sessions, blocks, replicates_per_block,
                     stock_configuration_id, wired_min_rel_floor},
          "sessions": [ {SessionRecord と同じ key の dict}, ... ],
          "cells":  { cell_id: {n_valid, medians, m, s, block_medians, valid, cv} },
          "floors": { holdout_id: {pairs, scalar_alt, scale_ref} },
        }

    返り値は人間可読の齟齬文字列のリスト。**空リスト = 完全一致。** 生成側と同じ関数を
    通すので float は == で比較する (再現不能な誤差は入らない)。欠損・不正形は fail-closed
    で齟齬として列挙する (黙認しない)。
    """
    errors: list = []

    # --- config ---
    config = artifact.get("config")
    if not isinstance(config, Mapping):
        return ["artifact に config が無い (protocol 値は入力必須、既定値は持たない)"]
    for k in _REQUIRED_CONFIG:
        if k not in config:
            errors.append(f"config: 必須キー {k} が欠損")
    if errors:
        return errors
    n_sessions = int(config["n_sessions"])
    blocks = int(config["blocks"])
    replicates_per_block = int(config["replicates_per_block"])
    stock_cfg = config["stock_configuration_id"]
    wired = config["wired_min_rel_floor"]

    # --- sessions のパース ---
    raw_sessions = artifact.get("sessions")
    if not isinstance(raw_sessions, Sequence):
        return ["artifact に sessions 列が無い"]
    records: list = []
    for i, d in enumerate(raw_sessions):
        if not isinstance(d, Mapping):
            errors.append(f"sessions[{i}]: dict でない")
            continue
        missing = [k for k in _REQUIRED_SESSION if k not in d]
        if missing:
            errors.append(f"sessions[{i}]: 必須キー欠損 {missing}")
            continue
        records.append(_record_from_mapping(d))
    if errors:
        return errors

    # --- holdout → cell への grouping ---
    by_holdout: dict = {}
    for r in records:
        by_holdout.setdefault(r.holdout_id, {}).setdefault(r.cell_id, []).append(r)

    # --- cells の再計算と照合 ---
    reported_cells = artifact.get("cells", {})
    if not isinstance(reported_cells, Mapping):
        return ["artifact.cells が Mapping でない"]

    recomputed_cells: dict = {}
    for holdout_id, cell_map in by_holdout.items():
        for cid, recs in cell_map.items():
            cs = cell_stats(recs, n_sessions=n_sessions, blocks=blocks,
                            replicates_per_block=replicates_per_block)
            recomputed_cells[cid] = cs

    calc_ids = set(recomputed_cells)
    rep_ids = set(reported_cells)
    for extra in sorted(rep_ids - calc_ids):
        errors.append(f"cells: 申告に余分な cell_id {extra} (生データに対応セッション無し)")
    for missing in sorted(calc_ids - rep_ids):
        errors.append(f"cells: 申告に cell_id {missing} が欠損")

    for cid in sorted(calc_ids & rep_ids):
        cs = recomputed_cells[cid]
        rep = reported_cells[cid]
        ctx = f"cell {cid}"
        if not isinstance(rep, Mapping):
            errors.append(f"{ctx}: 申告が Mapping でない")
            continue
        _cmp(ctx, "n_valid", rep.get("n_valid"), cs.n_valid, errors)
        _cmp(ctx, "medians", _as_tuple(rep.get("medians")), cs.medians, errors)
        _cmp(ctx, "m", rep.get("m"), cs.m, errors)
        _cmp(ctx, "s", rep.get("s"), cs.s, errors)
        _cmp(ctx, "block_medians", _norm_block_medians(rep.get("block_medians")),
             cs.block_medians, errors)
        _cmp(ctx, "valid", rep.get("valid"), cs.valid, errors)
        _cmp(ctx, "cv", rep.get("cv"), cs.cv, errors)

    # --- floors の再計算と照合 ---
    reported_floors = artifact.get("floors", {})
    if not isinstance(reported_floors, Mapping):
        return errors + ["artifact.floors が Mapping でない"]

    for holdout_id, cell_map in by_holdout.items():
        cells = {cid: recomputed_cells[cid] for cid in cell_map}
        # stock セル = configuration_id が stock_configuration_id のセル。
        stock_ids = sorted({cid for cid, recs in cell_map.items()
                            if recs[0].configuration_id == stock_cfg})
        ctx = f"holdout {holdout_id}"
        if len(stock_ids) != 1:
            errors.append(f"{ctx}: stock 構成 {stock_cfg!r} のセルが {len(stock_ids)} 個 "
                          f"(1 個であるべき)")
            continue
        hf = holdout_floors(cells, stock_id=stock_ids[0], wired_min_rel_floor=wired)
        rep = reported_floors.get(holdout_id)
        if not isinstance(rep, Mapping):
            errors.append(f"{ctx}: floors 申告が無い/Mapping でない")
            continue
        _cmp(ctx, "pairs", _as_plain_dict(rep.get("pairs")), hf.pairs, errors)
        _cmp(ctx, "scalar_alt", rep.get("scalar_alt"), hf.scalar_alt, errors)
        _cmp(ctx, "scale_ref", rep.get("scale_ref"), hf.scale_ref, errors)

    return errors


def _as_tuple(v):
    """medians 申告 (list/tuple/None) を tuple/None に正規化して == 照合可能にする。"""
    if v is None:
        return None
    return tuple(v)


def _as_plain_dict(v):
    if v is None:
        return None
    return dict(v)


def _norm_block_medians(v):
    """block_medians 申告のキーを int に正規化 (JSON 由来の str キーを吸収)。None は None。"""
    if v is None:
        return None
    return {int(k): val for k, val in v.items()}
