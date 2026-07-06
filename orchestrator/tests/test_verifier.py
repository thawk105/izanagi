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

from skiputil import Skip, skip                               # noqa: E402
from verifier import verify_trace_dir, result_to_dict        # noqa: E402
from verifier.dsg import DSG                                  # noqa: E402
from verifier.model import (CycleEdge, EdgeReason, RW, WR, WW)  # noqa: E402
from verifier.parse import ParseError, parse_trace_dir        # noqa: E402

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


def test_total_cycles_survives_witness_cap():
    # gate の機械判定は witness 数でなく total_cycles を使う (witness 上限での偽判定防止)。
    # max_report=0 で witness を全部切っても total_cycles は全数を保持し、
    # serializable 判定も total 基準のまま赤である。
    res = verify_trace_dir(os.path.join(FIX, "r1_write_skew"), max_report=0)
    assert not res.serializable
    assert len(res.anomalies) == 0            # witness は切られている
    assert res.total_cycles == 1              # が、全数は構造化されて残る
    assert result_to_dict(res)["total_cycles"] == 1

    green = _verify("g1_serial")
    assert green.total_cycles == 0


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
    # 規律3: 構造化 payload (Phase 3 で planner が原因軸を読む唯一の機械可読経路) にも
    # genesis_commits が出る。integrity カウンタ (Integrity dataclass の全フィールド) の
    # 1 つだけ欠けると原因軸が機械可読に落ちる
    assert result_to_dict(res)["integrity"]["genesis_commits"] == 1


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
    txns, issues = parse_trace_dir(os.path.join(FIX, "g3_readonly"))
    assert issues.dup_txids == []
    assert issues.missing_txids == 0
    assert issues.write_version_mismatches == []
    assert issues.malformed_keys == 0
    assert len(txns) == 2
    by = {t.txid: t for t in txns}
    assert by[0].commit == (1, 1) and len(by[0].writes) == 1
    assert by[1].commit == (1, 2) and len(by[1].reads) == 2 and by[1].thid == 1


# ---- 部分 trace / 整合破れの偽陰性ガード (audit 2026-07-02 洗練検査で追加) ----
#
# trace-hook が構造的に保証する不変条件 (txid 密連番・W 版 ≡ C commit・小文字 hex key)
# の破れは「trx や辺が黙って落ちて cycle を隠す」経路。落ちた結果のグラフは非巡回に
# なりがちなので、certified でなく indeterminate に倒すことが規律2 の要。

def _tmp_trace(*files: str) -> str:
    """一時 trace dir を作る。files[i] が trace_<i>.log の中身になる。"""
    import tempfile
    d = tempfile.mkdtemp(prefix="izanagi_trace_")
    for i, content in enumerate(files):
        with open(os.path.join(d, f"trace_{i}.log"), "w") as f:
            f.write(content)
    return d


def test_missing_txid_gap_indeterminate():
    """txid 欠番 = trx 丸ごと欠落 (thread の trace ファイル欠落等) は認証しない。

    write-skew の片側 trace ファイルを丸ごと除去すると cycle が消えて serializable に
    見える (実証済み偽陰性)。txid 密連番保証の破れとして indeterminate に倒す。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1\nW 0 aa U 1 1\n",
                   "C 2 1 1 2\nW 2 bb U 1 2\n")     # txid 1 が欠番
    try:
        res = verify_trace_dir(d)
        assert res.integrity.missing_txids == 1
        assert not res.integrity.clean()
        assert res.verdict == "indeterminate"
        assert not res.certified
        assert result_to_dict(res)["integrity"]["missing_txids"] == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_write_version_mismatch_indeterminate():
    """W 行の版 != C 行 commit は trace 口の整合破れとして認証しない。

    blind write の ww 順序ずれは orphan_reads に乗らないため、この照合が無いと
    cycle を見逃しうる (Phase 3 の合成 CC の trace 口への防壁)。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1\nW 0 aa U 999 888\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.write_version_mismatch == 1
        assert res.verdict == "indeterminate"
        assert not res.certified
        assert result_to_dict(res)["integrity"]["write_version_mismatch"] == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_malformed_key_indeterminate():
    """key の表現揺れ (大文字 hex 等) は同一キーを別キーに見せ競合辺を黙って消すため
    認証しない (片側 key を AA にすると辺 0 本で緑になる実証済み偽陰性)。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1\nW 0 AA U 1 1\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.malformed_keys == 1
        assert res.verdict == "indeterminate"
        assert not res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_commit_below_genesis_indeterminate():
    """genesis 番兵 (1,0) 未満の commit (epoch=0 等) も非物理として認証しない
    (ちょうど (1,0) だけでなく辞書順で下も弾く)。"""
    import shutil
    d = _tmp_trace("C 0 0 0 5\nW 0 aa U 0 5\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.genesis_commits == 1
        assert res.verdict == "indeterminate"
        assert not res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dup_txid_indeterminate():
    """同一 txid の C 行 2 回 (txid 発番の破れ) は認証しない。last-wins で最初の trx の
    R/W が失われ、落ちた辺が cycle を隠して false-green になるため indeterminate に
    倒す。integrity 7 条件のうち唯一 verdict 級 positive control が無かった穴を閉じる
    (S4 consumer 段の敵対検証 fixture-1)。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1\nW 0 aa U 1 1\nC 0 0 1 2\nW 0 aa U 1 2\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.dup_txids == 1
        assert res.verdict == "indeterminate"
        assert not res.certified
        assert result_to_dict(res)["integrity"]["dup_txids"] == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- 既知偽陰性の characterization (現状の挙動を明示ロックする) ----
#
# 以下 2 テストは「現状 certified になってしまう」ことを assert する。**これは仕様の
# 保証ではなく既知の限界の可視化** (規律3: 偽陰性の存在を台帳と機械テストの両方に残す)。
# 恒久対応は trace 形式拡張 (C 行に R/W 件数・終端マーカー) = izanagi-trace ブランチ
# 変更が必要で S1 移植と同時に行う (worklog 2026-07-02 [MED] 台帳)。
# **このテストが FAIL したら**: 検出力が向上した合図。assert を反転して赤 (indeterminate)
# を期待する形に書き換え、S1 送り台帳の該当項を閉じること (自動では反転しない)。

def test_characterization_tail_txid_gap_is_false_green():
    """末尾欠番 (max txid 以降の trx 欠落、例: 全ファイル尾部切り) は検出されない。
    欠番検査は expected = max(txid)+1 で数えるため、write-skew (r1) の txid 1 側を
    丸ごと落とすと欠番ゼロ扱い → cycle 相手が消えて certified serializable。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1\nR 0 0000000000000001 1 0\n"
                   "W 0 0000000000000002 U 1 1\n")   # r1 から txid 1 を尾部切り
    try:
        res = verify_trace_dir(d)
        assert res.integrity.missing_txids == 0      # 末尾欠番は欠番に数えられない
        assert res.certified, "偽陰性が塞がれた? → 本テストを反転し S1 台帳を閉じよ"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_characterization_txn_tail_loss_is_false_green():
    """trx 尾部欠落 (C 行だけ残り R/W 行が消失) は検出されない。現 trace 形式は C 行に
    R/W 件数を持たないため、R/W ゼロの trx と切り詰められた trx を区別できない —
    write-skew (r1) の txid 1 の R/W を落とすと辺が消えて certified serializable。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1\nR 0 0000000000000001 1 0\n"
                   "W 0 0000000000000002 U 1 1\n"
                   "C 1 0 1 2\n")                    # txid 1 は C 行のみ (R/W 消失)
    try:
        res = verify_trace_dir(d)
        assert res.integrity.missing_txids == 0      # 欠番はない (txid は連続)
        assert res.certified, "偽陰性が塞がれた? → 本テストを反転し S1 台帳を閉じよ"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_nonascii_wrapped_as_parse_error():
    """バイナリごみ (非 ASCII) は生 UnicodeDecodeError でなく ParseError で返す
    (pipeline の variant 単位 abort 隔離・exit code 2 の意味を保つ)。"""
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="izanagi_trace_")
    with open(os.path.join(d, "trace_0.log"), "wb") as f:
        f.write(b"C 0 0 1 1\n\xff\xfe garbage\n")
    try:
        try:
            verify_trace_dir(d)
            assert False, "ParseError を期待"
        except ParseError as e:
            assert "non-ASCII" in str(e)
    finally:
        shutil.rmtree(d, ignore_errors=True)


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
        skip(f"no real Silo sample at {SILO_SAMPLE} — 再生成手順は tests/README.md")
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
    passed = failed = skipped = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
