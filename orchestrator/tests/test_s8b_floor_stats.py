# -*- coding: utf-8 -*-
"""s8b_floor_stats (formula v1) の mutation-killing golden テスト。

値はすべてテスト内の手計算根拠コメント付き。median/mean 取り違え・stdev の n-1 vs n・
block 対比 delta の符号と絶対値・wired 下限と u_noise の支配関係・fail-closed の null 伝播
(stock 無効 → 全 null / c 無効 → 当該 pair のみ null / scalar_alt の veto)・session 有効性
契約 (rep 本数・非有限・0 以下・exec_failures・excluded_reason)・verify_floor_artifact の
改竄検出を固定する。
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import asdict

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign.s8b_floor_stats import (  # noqa: E402
    FORMULA_ID,
    CellStats,
    SessionRecord,
    cell_stats,
    holdout_floors,
    session_median,
    verify_floor_artifact,
)


# ---------------------------------------------------------------------------
# ヘルパ
# ---------------------------------------------------------------------------
def _sess(cell_id, block, seq, throughputs, *, reps_expected=None,
          holdout_id="H", configuration_id="cfg", exec_failures=0,
          excluded_reason=None, retry=False):
    if reps_expected is None:
        reps_expected = len(throughputs)
    return SessionRecord(
        cell_id=cell_id, holdout_id=holdout_id, configuration_id=configuration_id,
        block=block, seq=seq, throughputs=tuple(throughputs),
        reps_expected=reps_expected, exec_failures=exec_failures,
        excluded_reason=excluded_reason, retry=retry)


def _cell(cell_id, *, m, s, block_medians, valid=True, n_valid=4, medians=(),
          cv=None):
    return CellStats(cell_id=cell_id, n_valid=n_valid, medians=tuple(medians),
                     m=m, s=s, block_medians=block_medians, valid=valid, cv=cv,
                     notes=())


# ---------------------------------------------------------------------------
# FORMULA_ID
# ---------------------------------------------------------------------------
def test_formula_id_is_v1():
    # 式の版は凍結パッケージ formula v1 と一致していること。
    assert FORMULA_ID == "s8b-floor-stats/v1"


# ---------------------------------------------------------------------------
# session_median — 有効性契約
# ---------------------------------------------------------------------------
def test_session_median_uses_median_not_mean():
    # throughputs [10,10,100]: median=10, mean=40。median を返すこと (取り違え検出)。
    rec = _sess("c", 1, 0, [10, 10, 100])
    assert session_median(rec) == 10


def test_session_median_rejects_short_reps():
    # 4/5 reps: len(throughputs)=4 != reps_expected=5 → 無効 (None)。
    rec = _sess("c", 1, 0, [1, 2, 3, 4], reps_expected=5)
    assert session_median(rec) is None


def test_session_median_rejects_nonfinite():
    # 非有限 (inf/nan) を含めば無効。
    assert session_median(_sess("c", 1, 0, [1.0, math.inf])) is None
    assert session_median(_sess("c", 1, 0, [1.0, math.nan])) is None


def test_session_median_rejects_nonpositive():
    # 0 以下 (0 / 負) を含めば無効。
    assert session_median(_sess("c", 1, 0, [1.0, 0.0])) is None
    assert session_median(_sess("c", 1, 0, [1.0, -5.0])) is None


def test_session_median_rejects_exec_failures():
    # exec_failures>0 は throughputs が揃っていても無効。
    assert session_median(_sess("c", 1, 0, [10, 10, 10], exec_failures=1)) is None


def test_session_median_rejects_excluded_reason():
    # excluded_reason が付けば無効。
    assert session_median(_sess("c", 1, 0, [10, 10, 10],
                                excluded_reason="orphan-detected")) is None


# ---------------------------------------------------------------------------
# cell_stats — median/mean・stdev n-1・block_medians・有効性
# ---------------------------------------------------------------------------
def test_cell_stats_golden():
    # 有効 session medians = [100,100,100,200] (block1: 100,100 / block2: 100,200)。
    #   m   = median([100,100,100,200]) = 100  (mean=125 なので median/mean 取り違えを殺す)
    #   s   = stdev(n-1): mean=125, dev=[-25,-25,-25,75], Σsq=7500, /3=2500, sqrt=50.0
    #         (pstdev(n) なら sqrt(7500/4)=43.30… なので n-1 vs n を殺す)
    #   block_medians = {1: median(100,100)=100, 2: median(100,200)=150}
    #   cv  = s/mean = 50/125 = 0.4
    recs = [
        _sess("c", 1, 0, [100]), _sess("c", 1, 1, [100]),
        _sess("c", 2, 2, [100]), _sess("c", 2, 3, [200]),
    ]
    cs = cell_stats(recs, n_sessions=4, blocks=2, replicates_per_block=2)
    assert cs.valid is True
    assert cs.n_valid == 4
    assert cs.m == 100          # median、mean=125 ではない
    assert math.isclose(cs.s, 50.0)   # n-1
    assert cs.block_medians == {1: 100, 2: 150}
    assert math.isclose(cs.cv, 0.4)
    assert cs.medians == (100, 100, 100, 200)


def test_cell_stats_invalid_when_block_short():
    # block2 に有効 session が 1 本しか無い → replicates_per_block=2 に満たず無効。
    recs = [
        _sess("c", 1, 0, [100]), _sess("c", 1, 1, [110]),
        _sess("c", 2, 2, [120]),
    ]
    cs = cell_stats(recs, n_sessions=4, blocks=2, replicates_per_block=2)
    assert cs.valid is False
    assert cs.block_medians is None


def test_cell_stats_invalid_when_n_valid_mismatch():
    # 全 block 揃っても n_valid(4) != n_sessions(6) なら無効。
    recs = [
        _sess("c", 1, 0, [100]), _sess("c", 1, 1, [110]),
        _sess("c", 2, 2, [120]), _sess("c", 2, 3, [130]),
    ]
    cs = cell_stats(recs, n_sessions=6, blocks=2, replicates_per_block=2)
    assert cs.valid is False


def test_cell_stats_excludes_invalid_sessions_from_medians():
    # 無効 session (excluded_reason) は median 母集団に入れない (fallback しない)。
    recs = [
        _sess("c", 1, 0, [100]), _sess("c", 1, 1, [110]),
        _sess("c", 2, 2, [120]), _sess("c", 2, 3, [130]),
        _sess("c", 2, 4, [999], excluded_reason="drift"),
    ]
    cs = cell_stats(recs, n_sessions=4, blocks=2, replicates_per_block=2)
    # 有効は 4 本、block2 は 2 本 (999 は除外) → 有効。999 は medians に入らない。
    assert cs.valid is True
    assert 999 not in cs.medians
    assert cs.n_valid == 4


# ---------------------------------------------------------------------------
# holdout_floors — floor 合成の支配関係
# ---------------------------------------------------------------------------
def test_floor_u_noise_dominates():
    # stock: s=3, bm={1:100,2:100}; c: s=4, bm={1:105,2:108}。
    #   u_noise = sqrt(4^2+3^2) = sqrt(25) = 5.0
    #   d1=105-100=5, d2=108-100=8, delta=|5-8|=3
    #   rel = 0.01*100 = 1.0
    #   floor = max(5.0, 3, 1.0) = 5.0  → u_noise 支配
    stock = _cell("stock", m=100, s=3.0, block_medians={1: 100, 2: 100})
    c = _cell("c", m=104, s=4.0, block_medians={1: 105, 2: 108})
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01)
    assert math.isclose(hf.pairs["c"], 5.0)
    assert math.isclose(hf.scalar_alt, 5.0)
    assert hf.scale_ref == 100


def test_floor_delta_dominates_and_is_absolute():
    # stock: s=3, bm={1:100,2:100}; c: s=4。u_noise=5.0, rel=1.0。
    #   bm={1:105,2:120}: d1=5, d2=20, delta=|5-20|=15 → floor=max(5,15,1)=15
    stock = _cell("stock", m=100, s=3.0, block_medians={1: 100, 2: 100})
    c = _cell("c", m=112, s=4.0, block_medians={1: 105, 2: 120})
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01)
    assert math.isclose(hf.pairs["c"], 15.0)

    # 符号を逆に (bm={1:120,2:105}): d1=20, d2=5, delta=|20-5|=15。abs なので同値。
    c2 = _cell("c", m=112, s=4.0, block_medians={1: 120, 2: 105})
    hf2 = holdout_floors({"stock": stock, "c": c2}, stock_id="stock",
                         wired_min_rel_floor=0.01)
    assert math.isclose(hf2.pairs["c"], 15.0)


def test_floor_wired_min_dominates():
    # stock: s=1, m=100, bm={1:100,2:100}; c: s=1, bm={1:100,2:100}。
    #   u_noise=sqrt(1+1)=1.414…, delta=|0-0|=0, rel=0.05*100=5.0
    #   floor=max(1.414,0,5.0)=5.0 → wired 下限が支配
    stock = _cell("stock", m=100, s=1.0, block_medians={1: 100, 2: 100})
    c = _cell("c", m=100, s=1.0, block_medians={1: 100, 2: 100})
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.05)
    assert math.isclose(hf.pairs["c"], 5.0)


def test_floor_stock_invalid_nulls_whole_holdout():
    # stock 無効 → 全 pair null、scalar_alt null、scale_ref null (holdout 未確定)。
    stock = _cell("stock", m=None, s=None, block_medians=None, valid=False)
    c = _cell("c", m=104, s=4.0, block_medians={1: 105, 2: 108})
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01)
    assert hf.pairs["c"] is None
    assert hf.scalar_alt is None
    assert hf.scale_ref is None


def test_floor_cell_invalid_nulls_only_its_pair():
    # c1 有効・c2 無効 → c2 の pair のみ null。c1 は floor が出る (veto しない)。
    stock = _cell("stock", m=100, s=3.0, block_medians={1: 100, 2: 100})
    c1 = _cell("c1", m=104, s=4.0, block_medians={1: 105, 2: 120})   # floor=15
    c2 = _cell("c2", m=None, s=None, block_medians=None, valid=False)
    hf = holdout_floors({"stock": stock, "c1": c1, "c2": c2}, stock_id="stock",
                        wired_min_rel_floor=0.01)
    assert math.isclose(hf.pairs["c1"], 15.0)
    assert hf.pairs["c2"] is None
    # scalar_alt は c2 の null によって veto される (max を欠測で盛らない)。
    assert hf.scalar_alt is None
    assert hf.scale_ref == 100


def test_floor_scalar_alt_is_max_when_all_valid():
    # 2 pair 有効: c1 floor=15, c2 floor=5 → scalar_alt=max=15。
    stock = _cell("stock", m=100, s=3.0, block_medians={1: 100, 2: 100})
    c1 = _cell("c1", m=104, s=4.0, block_medians={1: 105, 2: 120})   # delta 15
    c2 = _cell("c2", m=104, s=4.0, block_medians={1: 105, 2: 108})   # u_noise 5
    hf = holdout_floors({"stock": stock, "c1": c1, "c2": c2}, stock_id="stock",
                        wired_min_rel_floor=0.01)
    assert math.isclose(hf.pairs["c1"], 15.0)
    assert math.isclose(hf.pairs["c2"], 5.0)
    assert math.isclose(hf.scalar_alt, 15.0)


def test_floor_rejects_stock_block_medians_not_exactly_one_two():
    # formula v1 は d_{c,b} を b=1,2 に固定した 2-block 専用式。stock の block_medians が
    # {1,2} でなければ (呼び手の calling 契約が破れている) 直接添字参照ではなく確実に落ちる
    # べき (レビュー所見 F1-blocks-not-pinned-to-2 の防御的二重チェック)。
    stock = _cell("stock", m=100, s=3.0, block_medians={1: 100, 2: 100, 3: 100})
    c = _cell("c", m=104, s=4.0, block_medians={1: 105, 2: 108})
    with pytest.raises(ValueError, match=r"\{1, 2\}"):
        holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                       wired_min_rel_floor=0.01)


def test_floor_rejects_cell_block_medians_not_exactly_one_two():
    stock = _cell("stock", m=100, s=3.0, block_medians={1: 100, 2: 100})
    c = _cell("c", m=104, s=4.0, block_medians={1: 105})
    with pytest.raises(ValueError, match=r"\{1, 2\}"):
        holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                       wired_min_rel_floor=0.01)


# ---------------------------------------------------------------------------
# verify_floor_artifact — 自己申告値の照合と改竄検出
# ---------------------------------------------------------------------------
def _build_artifact():
    """honest な生成器を模して、生データ・cells・floors が整合した artifact を組む。"""
    holdout = "H1"
    stock_cfg = "stock_common"
    var_cfg = "variant_A"
    stock_cell = f"{holdout}::{stock_cfg}"
    var_cell = f"{holdout}::{var_cfg}"
    config = {
        "n_sessions": 4, "blocks": 2, "replicates_per_block": 2,
        "stock_configuration_id": stock_cfg, "wired_min_rel_floor": 0.01,
    }

    def mk(cell, cfg, block, seq, tp):
        return _sess(cell, block, seq, [tp], holdout_id=holdout, configuration_id=cfg)

    records = [
        # stock medians [100,110,120,130]
        mk(stock_cell, stock_cfg, 1, 0, 100), mk(stock_cell, stock_cfg, 1, 1, 110),
        mk(stock_cell, stock_cfg, 2, 2, 120), mk(stock_cell, stock_cfg, 2, 3, 130),
        # variant medians [140,150,200,210]
        mk(var_cell, var_cfg, 1, 0, 140), mk(var_cell, var_cfg, 1, 1, 150),
        mk(var_cell, var_cfg, 2, 2, 200), mk(var_cell, var_cfg, 2, 3, 210),
    ]

    cells = {}
    by_cell = {}
    for r in records:
        by_cell.setdefault(r.cell_id, []).append(r)
    for cid, recs in by_cell.items():
        cs = cell_stats(recs, n_sessions=4, blocks=2, replicates_per_block=2)
        cells[cid] = asdict(cs)

    cell_objs = {cid: cell_stats(recs, n_sessions=4, blocks=2, replicates_per_block=2)
                 for cid, recs in by_cell.items()}
    hf = holdout_floors(cell_objs, stock_id=stock_cell, wired_min_rel_floor=0.01)
    floors = {holdout: asdict(hf)}

    artifact = {
        "config": config,
        "sessions": [asdict(r) for r in records],
        "cells": cells,
        "floors": floors,
    }
    return artifact, holdout, var_cell


def test_verify_accepts_consistent_artifact():
    artifact, _, _ = _build_artifact()
    assert verify_floor_artifact(artifact) == []


def test_verify_detects_tampered_floor():
    # floor 値を +1 改竄 → 再計算と不一致で pairs の齟齬が挙がる。
    artifact, holdout, var_cell = _build_artifact()
    artifact["floors"][holdout]["pairs"][var_cell] += 1
    errs = verify_floor_artifact(artifact)
    assert errs
    assert any("pairs" in e for e in errs)


def test_verify_detects_swapped_session():
    # 生 session の throughput を差し替え → 再計算が申告 cells/floors と食い違う。
    artifact, _, _ = _build_artifact()
    artifact["sessions"][0]["throughputs"] = [999999.0]
    errs = verify_floor_artifact(artifact)
    assert errs


def test_verify_fails_closed_on_missing_config():
    # protocol config が無ければ fail-closed (既定値で通さない)。
    artifact, _, _ = _build_artifact()
    del artifact["config"]
    errs = verify_floor_artifact(artifact)
    assert errs
    assert any("config" in e for e in errs)
