# -*- coding: utf-8 -*-
"""mini trace verifier の単体テスト。

pytest でも、素の `python orchestrator/tests/test_verifier.py` でも走る
(pytest 非依存の runner を末尾に持つ)。フィクスチャは tests/fixtures/。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from verifier import verify_trace_dir, result_to_dict        # noqa: E402
from verifier.dsg import DSG                                  # noqa: E402
from verifier.model import (CycleEdge, EdgeReason, RW, WR, WW)  # noqa: E402
from verifier.parse import parse_trace_dir                    # noqa: E402

FIX = os.path.join(_HERE, "fixtures")
# repo ルート相対で実 Silo トレース (生成済みなら)
_REPO = os.path.dirname(_ORCH)
SILO_SAMPLE = os.path.join(_REPO, "output", "runs", "silo-sample")


def _verify(name):
    return verify_trace_dir(os.path.join(FIX, name))


# ---- 緑 (serializable) ----

def test_green_fixtures():
    for name in ("g1_serial", "g2_rmw_chain", "g3_readonly", "g4_rw_no_cycle"):
        res = _verify(name)
        assert res.serializable, f"{name} should be serializable: {res.anomalies}"
        assert not res.anomalies, f"{name} unexpected anomalies"


def test_g4_has_rw_edge_but_no_cycle():
    # rw 辺が 1 本でも cycle でなければ serializable (「rw=即異常」誤検出ガード)
    res = _verify("g4_rw_no_cycle")
    assert res.n_edges == 1
    assert res.serializable


# ---- 赤 (non-serializable, すべて G2) ----

def test_write_skew_g2():
    res = _verify("r1_write_skew")
    assert not res.serializable
    assert len(res.anomalies) == 1
    a = res.anomalies[0]
    assert a.phenomenon == "G2"
    assert set(a.cycle) == {0, 1}
    # 2 本とも rw
    types = {t for e in a.edges for t in e.types}
    assert types == {RW}


def test_lost_update_g2():
    res = _verify("r2_lost_update")
    assert not res.serializable
    a = res.anomalies[0]
    assert a.phenomenon == "G2"
    assert set(a.cycle) == {0, 1}
    types = {t for e in a.edges for t in e.types}
    assert RW in types and WW in types       # rw + ww の混在 cycle


def test_cycle3_g2():
    res = _verify("r3_cycle3")
    assert not res.serializable
    a = res.anomalies[0]
    assert a.phenomenon == "G2"
    assert set(a.cycle) == {0, 1, 2}
    assert a.length == 3


def test_mixed_cycle_g2_all_three_edge_types():
    # 1 本の cycle に ww・wr・rw が全部乗る (定理「全 cycle は >=1 rw を含む」の実例)
    res = _verify("r4_mixed_cycle")
    assert not res.serializable
    a = res.anomalies[0]
    assert a.phenomenon == "G2"
    assert a.length == 3
    types = {t for e in a.edges for t in e.types}
    assert {WW, WR, RW} <= types


def test_nonlatest_read_caught_via_ww_transitivity():
    # 古い版を読んだ trx の anti-dependency が、immediate-successor + ww 連鎖で
    # 遠い overwriter まで届くか (immediate-successor 規則の健全性の要)
    res = _verify("r5_nonlatest_transitive")
    assert not res.serializable
    assert res.anomalies[0].phenomenon == "G2"


# ---- integrity 軸 (絶対規律2: integrity 不良なら certified しない) ----

def test_orphan_read_indeterminate():
    res = _verify("integrity_orphan")
    assert res.serializable                  # グラフは非巡回 (cycle 無し)
    assert not res.integrity.clean()
    assert res.integrity.orphan_reads == 1
    assert res.verdict == "indeterminate"    # でも認証できない
    assert not res.certified


def test_commit_at_genesis_indeterminate_and_wr_edge_kept():
    # FIX2: (1,0) commit を genesis と誤認して wr 辺を落とさない。かつ非物理として弾く
    res = _verify("m1_commit_at_genesis")
    assert res.integrity.genesis_commits == 1
    assert res.verdict == "indeterminate"
    assert not res.certified
    assert res.n_edges == 1                   # wr 辺が落ちていない (旧コードは 0 だった)


def test_version_dup_indeterminate():
    # FIX1: 同一 (key,版) を 2 trx が産む = malformed → 認証拒否
    res = _verify("m2_version_dup")
    assert res.integrity.version_dups >= 1
    assert res.verdict == "indeterminate"
    assert not res.certified


def test_empty_trace_indeterminate_not_certified():
    """規律2: 空トレース (検証すべき実行が無い) を serializable と認証しない。

    空 DSG は無条件 acyclic だが certified にすると false-green。安全側不変条件を
    最下層 (VerifyResult) に置いたので CLI 直叩き経路でも pipeline 経路でも一律
    indeterminate。"""
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="izanagi_emptytrace_")
    try:
        open(os.path.join(d, "trace_0.log"), "w").close()   # 空ファイル = 0 txn
        res = verify_trace_dir(d)
        assert res.n_txns == 0
        assert res.serializable                  # 空 DSG は acyclic (純グラフ事実)
        assert res.verdict == "indeterminate"    # だが認証しない
        assert not res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_phantom_skew_invisible_documented_limitation():
    # スコープ限界 (output/insights/ に記録): 述語(範囲)読みはトレース形式に出ない
    # ので phantom write-skew は key 粒度では見えず serializable に見える。これは
    # trace-hook の限界であり dsg.py のバグではない。ここで限界を固定 (回帰検出)。
    res = _verify("p1_phantom_skew")
    assert res.certified                      # verifier は (見える範囲では) 正しく serializable
    assert res.n_edges == 0


# ---- パーサ ----

def test_parser_groups_by_txid_across_files():
    txns, dups = parse_trace_dir(os.path.join(FIX, "g3_readonly"))
    assert dups == []
    assert len(txns) == 2
    by = {t.txid: t for t in txns}
    assert by[0].commit == (1, 1) and len(by[0].writes) == 1
    assert by[1].commit == (1, 2) and len(by[1].reads) == 2 and by[1].thid == 1


# ---- 分類器の枝 (G0/G1c は well-formed trace では出ないので合成辺で直接) ----

def test_classify_branches():
    g2 = [CycleEdge(0, 1, [EdgeReason(RW, "k")]),
          CycleEdge(1, 0, [EdgeReason(WW, "k")])]
    g1c = [CycleEdge(0, 1, [EdgeReason(WR, "k")]),
           CycleEdge(1, 0, [EdgeReason(WW, "k")])]
    g0 = [CycleEdge(0, 1, [EdgeReason(WW, "k")]),
          CycleEdge(1, 0, [EdgeReason(WW, "k")])]
    assert DSG._classify(g2) == "G2"
    assert DSG._classify(g1c) == "G1c"
    assert DSG._classify(g0) == "G0"


# ---- 構造化出力 (絶対規律3: pass/fail に潰さない) ----

def test_structured_report_has_edge_detail():
    res = _verify("r1_write_skew")
    d = result_to_dict(res)
    assert d["verdict"] == "non-serializable"
    a = d["anomalies"][0]
    assert a["phenomenon"] == "G2"
    # 各辺に type と key/版の witness が載っていること
    for e in a["edges"]:
        assert e["types"]
        assert e["reasons"]
        for r in e["reasons"]:
            assert "key" in r and "type" in r


# ---- 実 Silo トレース (生成済みのときだけ。緑のはず) ----

def test_real_silo_serializable():
    if not os.path.isdir(SILO_SAMPLE):
        print(f"  (skip) no real Silo sample at {SILO_SAMPLE}")
        return
    res = verify_trace_dir(SILO_SAMPLE)
    assert res.serializable, (
        f"real Silo trace MUST be serializable but got "
        f"{len(res.anomalies)} anomalies: "
        f"{[a.phenomenon for a in res.anomalies[:3]]}")
    assert res.integrity.clean(), f"integrity not clean: {res.integrity.notes}"


# ---- 素の runner (pytest 無しでも) ----

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
