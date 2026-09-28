# -*- coding: utf-8 -*-
"""mini trace verifier の単体テスト。

pytest でも、素の `python orchestrator/tests/test_verifier.py` でも走る
(pytest 非依存の runner を末尾に持つ)。フィクスチャは tests/fixtures/。
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import replace

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from skiputil import Skip                                     # noqa: E402
from orchestrator.verifier import (render_text,                         # noqa: E402
                                   verify_trace_dir as _verify_trace_dir,
                                   result_to_dict)
from orchestrator.verifier.dsg import DSG                                  # noqa: E402
from orchestrator.verifier.model import (                              # noqa: E402
    CycleEdge, EdgeReason, Integrity, ProofSurfaceAssessment, RW,
    VerifyResult, WR, WW, assess_protocol_proof_surfaces,
    compiled_protocol_source_texts,
)
from orchestrator.verifier.parse import ParseError, parse_trace_dir        # noqa: E402

FIX = os.path.join(_HERE, "fixtures")
REAL_SILO_FIXTURE = os.path.join(FIX, "g5_silo_real_prefix")
SILO_SERIAL_1THREAD_FIXTURE = os.path.join(FIX, "g6_silo_serial_1thread")
BROKEN_SILO_NORW_FIXTURE = os.path.join(FIX, "r8_silo_broken_norw")
# repo ルート相対で実 Silo トレース (生成済みなら)
_REPO = os.path.dirname(_ORCH)
SILO_SAMPLE = os.path.join(_REPO, "output", "runs", "silo-sample")
REAL_CCBENCH_ROOT = os.path.join(_REPO, "external", "ccbench")
_PROOF_SOURCE_TMP = tempfile.TemporaryDirectory(
    prefix="izanagi-verifier-proof-source-",
)
CCBENCH_ROOT = _PROOF_SOURCE_TMP.name
_SILO_SOURCE = os.path.join(CCBENCH_ROOT, "cc", "silo")
os.makedirs(_SILO_SOURCE)
with open(os.path.join(_SILO_SOURCE, "CMakeLists.txt"), "w", encoding="utf-8") as _f:
    _f.write("ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n")
with open(os.path.join(_SILO_SOURCE, "transaction.cc"), "w", encoding="utf-8") as _f:
    _f.write(
        "#if TRACE\n"
        "izanagi_trace::emit_lock_violation(0, 0, {}, {});\n"
        "izanagi_trace::stream(0) << \"P \";\n"
        "#endif\n"
    )


def verify_trace_dir(trace_dir, *args, **kwargs):
    """Legacy trace fixtures を complete な synthetic Silo source へ束縛する。"""
    kwargs.setdefault("protocol", "silo")
    kwargs.setdefault("ccbench_root", CCBENCH_ROOT)
    return _verify_trace_dir(trace_dir, *args, **kwargs)


def _verify(name):
    return verify_trace_dir(os.path.join(FIX, name))


# ---- 緑 (serializable) ----

def test_green_fixtures():
    for name in ("g1_serial", "g2_rmw_chain", "g3_readonly", "g4_rw_no_cycle"):
        res = _verify(name)
        assert res.serializable, f"{name} should be serializable: {res.anomalies}"
        assert not res.anomalies, f"{name} unexpected anomalies"
        assert res.integrity.framing_violations == 0


def test_g4_has_rw_edge_but_no_cycle():
    # rw 辺が 1 本でも cycle でなければ serializable (「rw=即異常」誤検出ガード)
    res = _verify("g4_rw_no_cycle")
    assert res.n_edges == 1
    assert res.serializable


def test_current_pin_proof_surfaces_accept_silo_and_reject_mocc_same_trace():
    """名前は mocc に X/P 計装が無かった T-2304 期に由来し、C 以後の拒否側被験は tictoc。"""
    from orchestrator.campaign.pin import CURRENT_PIN

    trace_dir = os.path.join(FIX, "g1_serial")
    head, pinned = subprocess.run(
        [
            "git", "-C", REAL_CCBENCH_ROOT, "rev-parse",
            "HEAD", f"{CURRENT_PIN}^{{commit}}",
        ],
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert len(head) == 40 and len(pinned) == 40
    assert head == pinned
    silo = _verify_trace_dir(
        trace_dir, protocol="silo", ccbench_root=REAL_CCBENCH_ROOT,
    )
    mocc = _verify_trace_dir(
        trace_dir, protocol="mocc", ccbench_root=REAL_CCBENCH_ROOT,
    )
    tictoc = _verify_trace_dir(
        trace_dir, protocol="tictoc", ccbench_root=REAL_CCBENCH_ROOT,
    )
    assert silo.integrity.proof_surfaces.as_record() == {
        "protocol": "silo",
        "X": "evidence-present",
        "P": "evidence-present",
        "I": "evidence-absent",
    }
    assert silo.integrity.clean()
    assert silo.certified
    assert mocc.integrity.proof_surfaces.as_record() == {
        "protocol": "mocc",
        "X": "evidence-present",
        "P": "evidence-present",
        "I": "evidence-absent",
    }
    assert mocc.integrity.clean()
    assert mocc.verdict == "serializable"
    assert mocc.certified
    tictoc_sources = compiled_protocol_source_texts("tictoc", REAL_CCBENCH_ROOT)
    assert tictoc_sources is not None
    assert all("#if TRACE" not in source for source in tictoc_sources)
    assert tictoc.integrity.proof_surfaces.as_record() == {
        "protocol": "tictoc",
        "X": "unavailable",
        "P": "unavailable",
        "I": "unavailable",
    }
    assert not tictoc.integrity.clean()
    assert tictoc.verdict == "indeterminate"
    assert not tictoc.certified
    assert assess_protocol_proof_surfaces(
        "si", REAL_CCBENCH_ROOT,
    ).as_record() == {
        "protocol": "si",
        "X": "evidence-absent",
        "P": "evidence-absent",
        "I": "evidence-absent",
    }


def test_proof_surfaces_unavailable_source_fails_closed():
    """読めない source を positive evidence に変換せず認証不能にする。"""
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        protocol_dir = os.path.join(root, "cc", "silo")
        os.makedirs(protocol_dir)
        with open(os.path.join(protocol_dir, "CMakeLists.txt"), "wb") as stream:
            stream.write(b"\xff")
        result = _verify_trace_dir(
            os.path.join(FIX, "g1_serial"),
            protocol="silo",
            ccbench_root=root,
        )
    assert result.integrity.proof_surfaces.as_record() == {
        "protocol": "silo",
        "X": "unavailable",
        "P": "unavailable",
        "I": "unavailable",
    }
    assert result.verdict == "indeterminate"
    assert not result.certified


def test_proof_surfaces_unspecified_fail_closed():
    result = _verify_trace_dir(os.path.join(FIX, "g1_serial"))
    assert result.integrity.proof_surfaces == ProofSurfaceAssessment()
    assert result.verdict == "indeterminate"
    assert not result.certified


def test_proof_surface_emitters_inside_if_zero_are_not_evidence():
    """M03: literal inactive block の死んだ emitter token では認証しない。"""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        protocol_dir = root / "cc/mocc"
        protocol_dir.mkdir(parents=True)
        (protocol_dir / "CMakeLists.txt").write_text(
            "ccbench_add_protocol(mocc SOURCES transaction.cc WORKLOADS ycsb)\n",
            encoding="utf-8",
        )
        (protocol_dir / "transaction.cc").write_text(
            "#if TRACE\n"
            "#if 0\n"
            "izanagi_trace::emit_lock_violation(0, 0, {}, {});\n"
            "izanagi_trace::stream(0) << \"P \";\n"
            "izanagi_trace::stream(0) << \"I \";\n"
            "#endif\n"
            "#endif\n",
            encoding="utf-8",
        )
        result = _verify_trace_dir(
            os.path.join(FIX, "g1_serial"),
            protocol="mocc",
            ccbench_root=root,
        )
    assert result.integrity.proof_surfaces.as_record() == {
        "protocol": "mocc",
        "X": "evidence-absent",
        "P": "evidence-absent",
        "I": "evidence-absent",
    }
    assert not result.certified


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


def test_dense_cycle4_clean_g2():
    res = _verify("r9_dense_cycle4")
    assert res.integrity.clean(), res.integrity.notes
    assert res.abort_reasons == {}
    assert res.certified is False
    assert not res.serializable
    assert res.verdict == "non-serializable"
    assert (
        res.n_txns, res.n_reads, res.n_writes, res.n_keys, res.n_edges,
    ) == (4, 4, 4, 4, 4)
    assert res.total_cycles == 1
    assert len(res.anomalies) == 1

    txns, _issues = parse_trace_dir(os.path.join(FIX, "r9_dense_cycle4"))
    assert [
        (txn.txid, txn.thid, txn.commit) for txn in txns
    ] == [
        (0, 0, (1, 1)),
        (1, 0, (1, 2)),
        (2, 0, (1, 3)),
        (3, 1, (1, 4)),
    ]

    a = res.anomalies[0]
    assert a.phenomenon == "G2"
    assert set(a.cycle) == {0, 1, 2, 3}
    assert a.length == 4
    edge_types = {
        (edge.src, edge.dst): set(edge.types)
        for edge in a.edges
    }
    assert edge_types == {
        (0, 1): {WR},
        (1, 2): {WR},
        (2, 3): {WR},
        (3, 0): {RW},
    }


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
    assert issues.framing_violations == []
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


def _tmp_trace_files(files: dict[str, str]) -> str:
    """一時 trace dir を作る。filename は canonical/non-canonical を保持する。"""
    import tempfile
    d = tempfile.mkdtemp(prefix="izanagi_trace_")
    for filename, content in files.items():
        with open(os.path.join(d, filename), "w") as f:
            f.write(content)
    return d


_V2_FIXTURE_FILES = (
    "cicada_g1_genesis_readonly/trace_0.log",
    "cicada_g1_genesis_readonly/trace_1.log",
    "cicada_g2_write_skew/trace_0.log",
    "cicada_g2_write_skew/trace_1.log",
    "g1_serial/trace_0.log",
    "g2_rmw_chain/trace_0.log",
    "g3_readonly/trace_0.log",
    "g3_readonly/trace_1.log",
    "g4_rw_no_cycle/trace_0.log",
    "g5_silo_real_prefix/trace_0.log",
    "g5_silo_real_prefix/trace_1.log",
    "g5_silo_real_prefix/trace_2.log",
    "g5_silo_real_prefix/trace_3.log",
    "g6_silo_serial_1thread/trace_0.log",
    "g7_mocc_minimal_2thread/trace_0.log",
    "g7_mocc_minimal_2thread/trace_1.log",
    "integrity_orphan/trace_0.log",
    "m1_commit_at_genesis/trace_0.log",
    "m2_version_dup/trace_0.log",
    "m3_mocc_lock_coverage/trace_0.log",
    "m3_mocc_lock_coverage/trace_1.log",
    "m4_mocc_permutation/trace_0.log",
    "m4_mocc_permutation/trace_1.log",
    "p1_phantom_skew/trace_0.log",
    "p1_phantom_skew/trace_1.log",
    "r1_write_skew/trace_0.log",
    "r2_lost_update/trace_0.log",
    "r2_lost_update/trace_1.log",
    "r3_cycle3/trace_0.log",
    "r4_mixed_cycle/trace_0.log",
    "r5_nonlatest_transitive/trace_0.log",
    "r6_epoch_version_order/trace_0.log",
    "r7_epoch_rw_successor/trace_0.log",
    "r8_silo_broken_norw/trace_0.log",
    "r8_silo_broken_norw/trace_1.log",
    "r8_silo_broken_norw/trace_2.log",
    "r8_silo_broken_norw/trace_3.log",
    "r9_dense_cycle4/trace_0.log",
    "r9_dense_cycle4/trace_1.log",
)


def test_all_v2_fixture_files_have_clean_framing():
    actual = []
    for root, _dirs, files in os.walk(FIX):
        for filename in files:
            if filename.startswith("trace_") and filename.endswith(".log"):
                actual.append(os.path.relpath(os.path.join(root, filename), FIX))
    assert tuple(sorted(actual)) == _V2_FIXTURE_FILES
    for dirname in sorted({os.path.dirname(path) for path in _V2_FIXTURE_FILES}):
        res = _verify(dirname)
        assert res.integrity.framing_violations == 0, (
            dirname, res.integrity.notes)


def test_v1_c_record_is_rejected():
    """5-field C は意図的に残す唯一の v1 literal。専用 ParseError にする。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1\n")
    try:
        try:
            parse_trace_dir(d)
            assert False, "trace v1 C record must be rejected"
        except ParseError as exc:
            assert "trace v1 C record is not supported" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_c_record_requires_exactly_seven_fields():
    import shutil
    d = _tmp_trace("C 0 0 1 1 0 0 extra\n")
    try:
        try:
            parse_trace_dir(d)
            assert False, "C with extra fields must be rejected"
        except ParseError as exc:
            assert "expected exactly 7 fields" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_negative_txid_is_rejected_before_gap_math_can_cancel_it():
    """{-1, 1} は旧 max(txid)+1-len(txns) だと欠番を相殺できた。構文で拒否する。"""
    import shutil
    d = _tmp_trace(
        "C -1 0 1 1 0 0\nE -1\n"
        "C 1 0 1 2 0 0\nE 1\n")
    try:
        try:
            verify_trace_dir(d)
            assert False, "negative txid must be rejected"
        except ParseError as exc:
            assert "txid must be a non-negative integer" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_negative_declared_counts_are_rejected():
    import shutil
    d = _tmp_trace("C 0 0 1 1 -1 0\nE 0\n")
    try:
        try:
            parse_trace_dir(d)
            assert False, "negative declared count must be rejected"
        except ParseError as exc:
            assert "declared read/write counts must be non-negative" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_declared_read_and_write_counts_must_match():
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 1 0\nE 0\n",   # read だけ不足
        "C 1 1 1 2 0 1\nE 1\n",   # write だけ不足
    )
    try:
        _txns, issues = parse_trace_dir(d)
        assert [v.kind for v in issues.framing_violations] == [
            "count-mismatch", "count-mismatch",
        ]
        first, second = issues.framing_violations
        assert (first.expected_reads, first.observed_reads) == (1, 0)
        assert (first.expected_writes, first.observed_writes) == (0, 0)
        assert (second.expected_reads, second.observed_reads) == (0, 0)
        assert (second.expected_writes, second.observed_writes) == (1, 0)
        res = verify_trace_dir(d)
        assert res.integrity.framing_violations == 2
        assert res.serializable is True
        assert res.verdict == "indeterminate"
        assert res.certified is False
        assert result_to_dict(res)["integrity"]["framing_violations"] == 2
        assert result_to_dict(res)["integrity"]["framing_violation_details"] == [
            {
                "kind": "count-mismatch",
                "txid": 0,
                "expected_reads": 1,
                "observed_reads": 0,
                "expected_writes": 0,
                "observed_writes": 0,
            },
            {
                "kind": "count-mismatch",
                "txid": 1,
                "expected_reads": 0,
                "observed_reads": 0,
                "expected_writes": 1,
                "observed_writes": 0,
            },
        ]
        assert "framing_violations=2" in render_text(res)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_end_is_indeterminate():
    import shutil
    d = _tmp_trace("C 0 0 1 1 0 0\n")
    try:
        _txns, issues = parse_trace_dir(d)
        assert [v.kind for v in issues.framing_violations] == ["missing-end"]
        res = verify_trace_dir(d)
        assert res.integrity.framing_violations == 1
        assert res.serializable is True
        assert res.verdict == "indeterminate"
        assert res.certified is False
        assert result_to_dict(res)["integrity"]["framing_violation_details"] == [
            {
                "kind": "missing-end",
                "txid": 0,
                "expected_reads": 0,
                "observed_reads": 0,
                "expected_writes": 0,
                "observed_writes": 0,
            },
        ]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_duplicate_end_is_indeterminate():
    import shutil
    d = _tmp_trace("C 0 0 1 1 0 0\nE 0\nE 0\n")
    try:
        _txns, issues = parse_trace_dir(d)
        assert [v.kind for v in issues.framing_violations] == ["duplicate-end"]
        res = verify_trace_dir(d)
        assert res.n_txns == 1
        assert res.integrity.framing_violations == 1
        assert res.verdict == "indeterminate"
        assert res.certified is False
        assert result_to_dict(res)["integrity"]["framing_violation_details"] == [
            {
                "kind": "duplicate-end",
                "txid": 0,
                "expected_reads": None,
                "observed_reads": None,
                "expected_writes": None,
                "observed_writes": None,
            },
        ]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_end_txid_mismatch_is_parse_error():
    import shutil
    d = _tmp_trace("C 0 0 1 1 0 0\nE 1\n")
    try:
        try:
            parse_trace_dir(d)
            assert False, "mismatched E txid must be rejected"
        except ParseError as exc:
            assert "E txid 1 does not match open txn 0" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_end_record_requires_exactly_two_fields():
    import shutil
    d = _tmp_trace("C 0 0 1 1 0 0\nE 0 extra\n")
    try:
        try:
            parse_trace_dir(d)
            assert False, "E with extra fields must be rejected"
        except ParseError as exc:
            assert "expected exactly 2 fields" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_new_commit_before_end_records_missing_end():
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 0 0\n"
        "C 1 0 1 2 0 0\nE 1\n")
    try:
        _txns, issues = parse_trace_dir(d)
        assert [(v.kind, v.txid) for v in issues.framing_violations] == [
            ("missing-end", 0),
        ]
        res = verify_trace_dir(d)
        assert res.n_txns == 2
        assert res.integrity.framing_violations == 1
        assert res.verdict == "indeterminate"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_non_immediate_duplicate_end_remains_parse_error():
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 0 0\nE 0\n"
        "C 1 0 1 2 0 0\nE 1\n"
        "E 0\n")
    try:
        try:
            parse_trace_dir(d)
            assert False, "non-immediate duplicate E must remain ParseError"
        except ParseError as exc:
            assert "E for txid 0 has no matching open txn" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_zero_read_zero_write_frame_is_valid():
    import shutil
    d = _tmp_trace("C 0 0 1 1 0 0\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.framing_violations == 0
        assert res.integrity.clean()
        assert res.verdict == "serializable"
        assert res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_x_and_i_records_do_not_count_as_reads_or_writes():
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 0 0\n"
        "X 0 aa not-locked-at-entry\n"
        "I 0 aa write-set-entry-without-intent\n"
        "E 0\n")
    try:
        txns, issues = parse_trace_dir(d)
        assert len(txns) == 1
        assert txns[0].reads == [] and txns[0].writes == []
        assert issues.framing_violations == []
        res = verify_trace_dir(d)
        assert res.integrity.framing_violations == 0
        assert res.n_reads == 0 and res.n_writes == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cycle_verdict_takes_priority_over_framing_violation():
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 1 1\nR 0 aa 1 0\nW 0 bb U 1 1\nE 0\n"
        "C 1 0 1 2 1 1\nR 1 bb 1 0\nW 1 aa U 1 2\n")
    try:
        res = verify_trace_dir(d)
        assert res.serializable is False
        assert res.integrity.framing_violations == 1
        assert res.verdict == "non-serializable"
        assert res.certified is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_txid_gap_indeterminate():
    """txid 欠番 = trx 丸ごと欠落 (thread の trace ファイル欠落等) は認証しない。

    write-skew の片側 trace ファイルを丸ごと除去すると cycle が消えて serializable に
    見える (実証済み偽陰性)。txid 密連番保証の破れとして indeterminate に倒す。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1 0 1\nW 0 aa U 1 1\nE 0\n",
                   "C 2 1 1 2 0 1\nW 2 bb U 1 2\nE 2\n")  # txid 1 が欠番
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
    d = _tmp_trace("C 0 0 1 1 0 1\nW 0 aa U 999 888\nE 0\n")
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
    d = _tmp_trace("C 0 0 1 1 0 1\nW 0 AA U 1 1\nE 0\n")
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
    d = _tmp_trace("C 0 0 0 5 0 1\nW 0 aa U 0 5\nE 0\n")
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
    倒す。既存 integrity 条件のうち唯一 verdict 級 positive control が無かった穴を閉じる
    (S4 consumer 段の敵対検証 fixture-1)。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 0 1\nW 0 aa U 1 1\nE 0\n"
        "C 0 0 1 2 0 1\nW 0 aa U 1 2\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.dup_txids == 1
        assert res.verdict == "indeterminate"
        assert not res.certified
        assert result_to_dict(res)["integrity"]["dup_txids"] == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- lock 被覆違反 (X 行) の positive control (後続段 3, D38) ----
#
# writePhase の #if TRACE 被覆 assert が emit する X 行を、verifier が
# Integrity.lock_coverage_violations に配線し verdict を indeterminate に倒すことを
# 固定する。実ビルド実走の positive control (lockskip/early-unlock) は
# orchestrator/campaign/s3_lock_coverage.py の driver が担う (fixture はその
# verdict 級テストの相方 = 段 2 の dup_txids / J8-B と同型)。

def test_lock_coverage_violation_indeterminate():
    """X 行 (lock 被覆違反) は verdict を indeterminate に倒す。cycle は生まないので
    non-serializable にはならない (torn read で版 stamp が信用不能 → 辺が落ちる恐れ =
    他 integrity カウンタと同じ indeterminate、絶対規律2)。GATE-1/CODE-1 の裁定:
    'integrity 同型かつ non-serializable' は機構的に両立不能なので indeterminate に確定。"""
    import shutil
    # 1 txn が lock を持たずに key aa を書いた (それ自体は cycle を生まない serializable)。
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\n"
        "X 0 aa not-locked-at-entry\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.lock_coverage_violations == 1
        assert res.total_cycles == 0                    # cycle は無い
        assert res.serializable                          # 純グラフ事実 = 非巡回
        assert res.verdict == "indeterminate"            # だが認証できない (X が汚す)
        assert res.verdict != "non-serializable"         # cycle を捏造しない (GATE-1)
        assert not res.certified
        assert result_to_dict(res)["integrity"]["lock_coverage_violations"] == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_lock_coverage_control_serializable():
    """X 行の無い同じ形は serializable/certified (非恒真の基底 = assert は正しいコード
    で沈黙する)。lockskip fixture との唯一の差が X 行であることを示す negative control。"""
    import shutil
    d = _tmp_trace("C 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.lock_coverage_violations == 0
        assert res.verdict == "serializable"
        assert res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_lock_coverage_reasons_parsed():
    """2 reason (獲得欠落 not-locked-at-entry / 保持破れ lock-lost-before-write) が
    parse され、件数と (txid,key,reason) 見本が issues に載る (critic の読み分け素材)。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\n"
        "X 0 aa not-locked-at-entry\n"
        "X 0 aa lock-lost-before-write\nE 0\n")
    try:
        _txns, issues = parse_trace_dir(d)
        assert len(issues.lock_coverage_violations) == 2
        reasons = {r for _t, _k, r in issues.lock_coverage_violations}
        assert reasons == {"not-locked-at-entry", "lock-lost-before-write"}
        res = verify_trace_dir(d)
        assert res.integrity.lock_coverage_violations == 2
        # notes に reason 別内訳と見本が載る (render/critic が読む)
        note = " ".join(res.integrity.notes)
        assert "not-locked-at-entry" in note and "lock-lost-before-write" in note
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_lock_coverage_malformed_key_flagged():
    """X 行の key も hex 形式検査を通す (表現揺れは帰属を汚すため、規律3)。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\n"
        "X 0 AA not-locked-at-entry\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.lock_coverage_violations == 1
        assert res.integrity.malformed_keys == 1        # AA は大文字 = 形式違反
        assert res.verdict == "indeterminate"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- write intent 被覆違反 (I 行) の positive control (T-152) ----
#
# writePhase の write_set_ と API write intent の相互被覆 assert が emit する I 行を、
# verifier が Integrity.write_intent_violations に配線する。I は X と同じ txid 相関型。

def test_write_intent_violation_indeterminate_and_reports_json_text():
    """I 行は cycle を捏造せず、write 完全性の認証不能として indeterminate に倒す。
    JSON と text の両 report surface に同じ固定件数が出ることも一緒に固定する。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\n"
        "I 0 aa write-set-entry-without-intent\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.write_intent_violations == 1
        assert res.total_cycles == 0
        assert res.serializable
        assert res.verdict == "indeterminate"
        assert res.verdict != "non-serializable"
        assert not res.certified
        assert result_to_dict(res)["integrity"]["write_intent_violations"] == 1
        assert "write_intent_violations=1" in render_text(res)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_write_intent_control_serializable():
    """I 行の無い同じ形は clean/serializable/certified のまま (過剰拒否の正対照)。"""
    import shutil
    d = _tmp_trace("C 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.write_intent_violations == 0
        assert res.integrity.clean()
        assert res.verdict == "serializable"
        assert res.certified
        assert result_to_dict(res)["integrity"]["write_intent_violations"] == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_write_intent_reasons_parsed_and_summarized():
    """契約上の 2 reason を (txid,key,reason) で保持し、件数内訳と見本を notes に出す。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\n"
        "I 0 aa write-set-entry-without-intent\n"
        "I 0 bb intent-missing-from-write-set\nE 0\n")
    try:
        _txns, issues = parse_trace_dir(d)
        assert issues.write_intent_violations == [
            (0, "aa", "write-set-entry-without-intent"),
            (0, "bb", "intent-missing-from-write-set"),
        ]
        res = verify_trace_dir(d)
        assert res.integrity.write_intent_violations == 2
        note = " ".join(res.integrity.notes)
        assert "write-set-entry-without-intent×1" in note
        assert "intent-missing-from-write-set×1" in note
        assert "txn0 key=aa" in note and "txn0 key=bb" in note
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_write_intent_malformed_key_flagged():
    """I 行の key も X と同じ小文字偶数長 hex 検査を通す。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\n"
        "I 0 AA write-set-entry-without-intent\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.write_intent_violations == 1
        assert res.integrity.malformed_keys == 1
        assert res.verdict == "indeterminate"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_write_intent_txid_must_match_open_txn():
    """I は P と違って txid 相関型であり、別 txn への誤帰属を _expect が拒否する。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\n"
        "I 1 aa write-set-entry-without-intent\nE 0\n")
    try:
        try:
            parse_trace_dir(d)
            assert False, "mismatched I txid は ParseError でなければならない"
        except ParseError as exc:
            assert "txid 1 does not match open txn 0" in str(exc)
            assert "C/R/W/X/I must be inside one contiguous C/E frame" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_write_intent_unknown_reason_counted_and_indeterminate():
    """未知の非空 reason も I 違反として保持し、分類シグナルを失わない。"""
    import shutil
    d = _tmp_trace("C 0 0 5 10 0 0\nI 0 aa invented-reason\nE 0\n")
    try:
        _txns, issues = parse_trace_dir(d)
        assert issues.write_intent_violations == [
            (0, "aa", "invented-reason"),
        ]
        res = verify_trace_dir(d)
        assert res.integrity.write_intent_violations == 1
        assert res.total_cycles == 0
        assert res.serializable
        assert res.verdict == "indeterminate"
        assert not res.certified
        payload = result_to_dict(res)
        assert payload["integrity"]["write_intent_violations"] == 1
        note = " ".join(payload["integrity"]["notes"])
        assert "invented-reason×1" in note
        assert "write-intent coverage violation" in note
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- permutation 保存違反 (P 行) の positive control (段 5, D41) ----
#
# validationPhase の #if TRACE assert が emit する P 行を、verifier が
# Integrity.permutation_violations に配線し verdict を indeterminate に倒すことを
# 固定する。P 行は X と異なり txid を持たない (validationPhase は commit 前に走り、
# abort する trx でも起こりうるため)。実ビルド実走の positive control (要素 erase の
# broken comparator) は s3_lock_coverage.py 様式の別 driver が担う (X 行と同じ役割分担)。

def test_permutation_violation_indeterminate():
    """P 行 (permutation 保存違反) は verdict を indeterminate に倒す。txid を持たない
    ので txn ブロックの外 (C 行の前) に単独で出現しても正しくパースされる。"""
    import shutil
    d = _tmp_trace("P size-changed\nC 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.permutation_violations == 1
        assert res.total_cycles == 0                    # cycle は無い
        assert res.serializable                          # 純グラフ事実 = 非巡回
        assert res.verdict == "indeterminate"            # だが認証できない (P が汚す)
        assert res.verdict != "non-serializable"         # cycle を捏造しない (GATE-1 と同型)
        assert not res.certified
        assert result_to_dict(res)["integrity"]["permutation_violations"] == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_permutation_violation_control_serializable():
    """P 行の無い同じ形は serializable/certified (非恒真の基底 = assert は正しい sort
    で沈黙する)。"""
    import shutil
    d = _tmp_trace("C 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.permutation_violations == 0
        assert res.verdict == "serializable"
        assert res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_permutation_violation_reasons_parsed():
    """2 reason (size-changed / rcdptr-set-changed) が parse され件数が issues に載る。"""
    import shutil
    d = _tmp_trace(
        "P size-changed\nP rcdptr-set-changed\n"
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n")
    try:
        _txns, issues = parse_trace_dir(d)
        assert len(issues.permutation_violations) == 2
        assert set(issues.permutation_violations) == {"size-changed", "rcdptr-set-changed"}
        res = verify_trace_dir(d)
        assert res.integrity.permutation_violations == 2
        note = " ".join(res.integrity.notes)
        assert "size-changed" in note and "rcdptr-set-changed" in note
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_permutation_violation_between_txn_blocks():
    """P 行は txn ブロックの間 (前の txn の commit 後、次の txn の C 行の前) にも
    独立して出現しうる (validationPhase は txn 単位でなくワーカーのタイムライン上の
    任意の点で走るため)。txid 相関検査 (_expect) を通らないことの確認。"""
    import shutil
    d = _tmp_trace(
        "C 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n"
        "P rcdptr-set-changed\n"
        "C 1 0 5 11 0 1\nW 1 bb U 5 11\nE 1\n")
    try:
        res = verify_trace_dir(d)
        assert res.integrity.permutation_violations == 1
        assert res.n_txns == 2                           # 両 txn とも正常に parse される
        assert res.verdict == "indeterminate"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_permutation_violation_details_follow_parse_verify_report_path():
    """P-only の複数 trace file、重複 reason、未知 token、非 canonical 名を
    parse -> verify -> result_to_dict の実経路で突き合わせる。"""
    import shutil
    d = _tmp_trace_files({
        "trace_0.log": "P size-changed\nP size-changed\n",
        "trace_worker.log": "P rcdptr-set-changed\nP not-a-known-code\n",
    })
    try:
        raw_tokens = [
            "size-changed", "size-changed",
            "rcdptr-set-changed", "not-a-known-code",
        ]
        _txns, issues = parse_trace_dir(d)
        assert _txns == []
        assert [v.raw_reason for v in issues.permutation_violation_details] == raw_tokens
        assert [
            (v.source_thread_hint, v.source_thread_hint_basis)
            for v in issues.permutation_violation_details
        ] == [
            (0, "canonical-filename"),
            (0, "canonical-filename"),
            (None, None),
            (None, None),
        ]

        res = verify_trace_dir(d)
        payload = result_to_dict(res)
        details = payload["integrity"]["permutation_violation_details"]
        expected_counts = Counter(
            token if token in {"size-changed", "rcdptr-set-changed"}
            else "unknown"
            for token in raw_tokens
        )
        assert details["counts"] == {
            "size-changed": expected_counts["size-changed"],
            "rcdptr-set-changed": expected_counts["rcdptr-set-changed"],
            "unknown": expected_counts["unknown"],
        }
        assert sum(details["counts"].values()) == res.integrity.permutation_violations
        assert details["unknown_reason_sample"] == [
            json.dumps("not-a-known-code", ensure_ascii=True),
        ]
        assert len(details["sample"]) <= 5
        assert all(
            set(item) == {
                "observation", "source_thread_hint", "source_thread_hint_basis",
            }
            for item in details["sample"]
        )
        assert details["sample"][0]["observation"] == {
            "kind": "size-changed",
            "size_preserved": False,
            "rcdptr_multiset_preserved": "NOT_EVALUATED",
            "recognized": True,
        }
        assert "raw_reason" not in details["sample"][0]
        assert "raw_reason_escaped" not in details["sample"][0]
        assert details["sample"][2]["observation"] == {
            "kind": "rcdptr-set-changed",
            "size_preserved": True,
            "rcdptr_multiset_preserved": False,
            "recognized": True,
        }
        assert details["sample"][2]["source_thread_hint"] is None
        assert details["sample"][2]["source_thread_hint_basis"] is None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_permutation_violation_details_bound_large_known_sample():
    """既知 reason の大量 P 行は件数を保ち、外部 sample だけを bounded にする。"""
    import shutil
    count = 32
    d = _tmp_trace_files({
        "trace_7.log": "\n".join(["P size-changed"] * count) + "\n",
    })
    try:
        _txns, issues = parse_trace_dir(d)
        assert len(issues.permutation_violations) == count
        assert len(issues.permutation_violation_details) == count
        res = verify_trace_dir(d)
        payload = result_to_dict(res)
        details = payload["integrity"]["permutation_violation_details"]
        assert details["counts"] == {
            "size-changed": count,
            "rcdptr-set-changed": 0,
            "unknown": 0,
        }
        assert sum(details["counts"].values()) == res.integrity.permutation_violations
        assert len(details["sample"]) <= 5
        assert details["unknown_reason_sample"] == []
        assert all(
            item["source_thread_hint"] == 7
            and item["source_thread_hint_basis"] == "canonical-filename"
            for item in details["sample"]
        )
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- A 行 (abort 要因の記録、段 8a/D48 positive control 計装) ----

def test_abort_reason_tally_parsed_not_verdict():
    """A 行は**集計データ**であり integrity/verdict に不関与 (certified のまま)。
    P と同じく txid 非相関 (abort する trx は txid 未採番) — txn ブロック外でも
    受理される。要因別カウントが VerifyResult.abort_reasons と JSON stats に載る
    (coverage driver の整合検査入力、D48 必須条件 3)。"""
    import shutil
    d = _tmp_trace(
        "A lock-conflict\nC 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n"
        "A lock-conflict\nA readvali-tid\n")
    try:
        res = verify_trace_dir(d)
        assert res.abort_reasons == {"lock-conflict": 2, "readvali-tid": 1}
        assert res.verdict == "serializable"     # A 行は認証を汚さない
        assert res.certified
        assert res.integrity.clean()
        assert result_to_dict(res)["stats"]["abort_reasons"] == {
            "lock-conflict": 2, "readvali-tid": 1}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_abort_reason_absent_is_empty():
    """A 行の無い通常 trace では abort_reasons は空 dict (通常 verify の出力不変性)。"""
    import shutil
    d = _tmp_trace("C 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n")
    try:
        res = verify_trace_dir(d)
        assert res.abort_reasons == {}
        assert result_to_dict(res)["stats"]["abort_reasons"] == {}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_unknown_tag_still_parse_error_after_a():
    """A タグを足しても未知タグの fails-closed (ParseError) は不変 (規律2)。"""
    import shutil
    d = _tmp_trace("Z bogus\nC 0 0 5 10 0 1\nW 0 aa U 5 10\nE 0\n")
    try:
        try:
            verify_trace_dir(d)
            assert False, "unknown tag must raise ParseError"
        except ParseError as e:
            assert "unknown record tag" in str(e)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_known_tag_prefixes_are_not_accepted_as_record_tags():
    """既知 tag と同じ先頭文字でも、record tag の完全一致以外は拒否する。"""
    import shutil
    traces = (
        "C 0 0 5 10 0 0\nEnd 0\n",
        "Commit 0 0 5 10 0 0\nE 0\n",
    )
    for trace in traces:
        d = _tmp_trace(trace)
        try:
            try:
                verify_trace_dir(d)
                assert False, "prefixed known tag must raise ParseError"
            except ParseError as e:
                assert "unknown record tag" in str(e)
        finally:
            shutil.rmtree(d, ignore_errors=True)


# ---- 既知偽陰性の characterization ----
#
# witness を渡す live 経路では FN-1 を分離する。一方、witness を省略できる optional
# API には末尾 txid 全体が消える FN-1 だけが残る。FN-2 (C 行は残るが trx 尾部の
# R/W/E が消える) は v2 の件数・終端 framing で分離する。

def test_characterization_tail_txid_gap_is_false_green():
    """witness を渡さない optional API では FN-1 が残る (意図した後方互換)。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1 1 1\nR 0 0000000000000001 1 0\n"
                   "W 0 0000000000000002 U 1 1\nE 0\n")  # txid 1 を丸ごと切る
    try:
        res = verify_trace_dir(d)
        assert res.integrity.missing_txids == 0      # 末尾欠番は欠番に数えられない
        assert res.certified, "witness 無し optional API の互換挙動が変わった"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_characterization_tail_txid_gap_is_indeterminate_with_commit_witness():
    """末尾欠番 (max txid 以降の trx 欠落) を trace 外 witness で拒否する。

    欠番検査は expected = max(txid)+1 で数えるため、write-skew (r1) の txid 1 側を
    丸ごと落としても missing_txids は 0 のまま。commit witness だけが FN-1 を分離する。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1 1 1\nR 0 0000000000000001 1 0\n"
                   "W 0 0000000000000002 U 1 1\nE 0\n")  # txid 1 を丸ごと切る
    try:
        res = verify_trace_dir(d, expected_commits=2)
        assert res.integrity.missing_txids == 0      # 末尾欠番は欠番に数えられない
        assert res.serializable
        assert res.verdict == "indeterminate"
        assert not res.certified
        assert res.integrity.expected_commits == 2
        assert res.integrity.observed_commits == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_characterization_txn_tail_loss_is_indeterminate():
    """v2 framing は C が残る trx 尾部欠落 (FN-2) を認証しない。

    write-skew (r1) の txid 1 の R/W/E を落とすと DSG の cycle 自体は消えるが、
    count-mismatch と missing-end が欠落を構造化して indeterminate に倒す。"""
    import shutil
    d = _tmp_trace("C 0 0 1 1 1 1\nR 0 0000000000000001 1 0\n"
                   "W 0 0000000000000002 U 1 1\nE 0\n"
                   "C 1 0 1 2 1 1\n")              # txid 1 の R/W/E が消失
    try:
        res = verify_trace_dir(d)
        assert res.integrity.missing_txids == 0      # 欠番はない (txid は連続)
        assert res.serializable is True
        assert res.integrity.framing_violations == 2
        assert res.verdict == "indeterminate"
        assert res.certified is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _complete_two_file_trace() -> str:
    return _tmp_trace(
        "C 0 0 1 1 0 1\nW 0 aa U 1 1\nE 0\n",
        "C 1 1 1 2 0 1\nW 1 bb U 1 2\nE 1\n",
    )


def test_commit_count_witness_detects_removed_trace_file():
    import shutil
    d = _complete_two_file_trace()
    try:
        os.unlink(os.path.join(d, "trace_1.log"))
        res = verify_trace_dir(d, expected_commits=2)
        assert res.integrity.missing_txids == 0
        assert res.serializable
        assert not res.integrity.clean()
        assert not res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_commit_count_witness_accepts_complete_trace():
    import shutil
    d = _complete_two_file_trace()
    try:
        res = verify_trace_dir(d, expected_commits=2)
        assert res.integrity.clean()
        assert res.certified
        assert res.verdict == "serializable"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_commit_count_witness_result_is_structured():
    import shutil
    d = _complete_two_file_trace()
    try:
        os.unlink(os.path.join(d, "trace_1.log"))
        res = verify_trace_dir(d, expected_commits=2)
        payload = result_to_dict(res)
        expected_note = (
            "commit witness mismatch: expected=2 observed=1 delta=-1"
        )
        assert [
            note for note in payload["integrity"]["notes"]
            if "expected=2 observed=1 delta=-1" in note
        ] == [expected_note]
        assert payload["integrity"]["clean"] is False
        assert payload["certified"] is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_commit_witness_partial_state_is_unclean_without_report_schema_change():
    from orchestrator.verifier.model import Integrity, VerifyResult
    res = VerifyResult(
        trace_dir="partial", serializable=True, n_txns=1,
        integrity=Integrity(expected_commits=1),
    )
    payload = result_to_dict(res)
    assert "commit_witness" not in payload["integrity"]
    assert payload["integrity"]["clean"] is False
    assert payload["certified"] is False
    assert "integrity UNCLEAN" in render_text(res)


def test_result_to_dict_commit_witness_changes_notes_without_new_keys():
    trace_dir = os.path.join(FIX, "g1_serial")
    baseline = result_to_dict(verify_trace_dir(trace_dir))
    witnessed = result_to_dict(verify_trace_dir(trace_dir, expected_commits=3))

    assert witnessed.keys() == baseline.keys()
    assert witnessed["stats"].keys() == baseline["stats"].keys()
    assert witnessed["integrity"].keys() == baseline["integrity"].keys()
    assert "commit_witness" not in witnessed["integrity"]

    expected_note = "commit witness mismatch: expected=3 observed=2 delta=-1"
    assert baseline["integrity"]["notes"] == []
    assert witnessed["integrity"]["notes"] == [expected_note]
    assert witnessed["integrity"]["clean"] is False
    assert witnessed["certified"] is False

    # witness 生値以外に変わるのは、notes から導かれるゲート出力だけ。
    assert {
        key: value for key, value in witnessed.items()
        if key not in {"verdict", "certified", "integrity"}
    } == {
        key: value for key, value in baseline.items()
        if key not in {"verdict", "certified", "integrity"}
    }
    assert {
        key: value for key, value in witnessed["integrity"].items()
        if key not in {"clean", "notes"}
    } == {
        key: value for key, value in baseline["integrity"].items()
        if key not in {"clean", "notes"}
    }


def test_result_to_dict_without_commit_witness_matches_frozen_json_bytes():
    result = replace(
        verify_trace_dir(os.path.join(FIX, "g1_serial")),
        trace_dir="/fixture/g1_serial",
    )
    actual = json.dumps(
        result_to_dict(result), indent=2, ensure_ascii=False,
    ).encode("utf-8")
    expected = """{
  "trace_dir": "/fixture/g1_serial",
  "verdict": "serializable",
  "certified": true,
  "serializable": true,
  "stats": {
    "txns": 2,
    "reads": 1,
    "writes": 1,
    "keys": 1,
    "edges": 1,
    "abort_reasons": {}
  },
  "integrity": {
    "clean": true,
    "orphan_reads": 0,
    "version_dups": 0,
    "dup_txids": 0,
    "genesis_commits": 0,
    "missing_txids": 0,
    "write_version_mismatch": 0,
    "malformed_keys": 0,
    "framing_violations": 0,
    "framing_violation_details": [],
    "lock_coverage_violations": 0,
    "write_intent_violations": 0,
    "permutation_violations": 0,
    "permutation_violation_details": {
      "counts": {
        "size-changed": 0,
        "rcdptr-set-changed": 0,
        "unknown": 0
      },
      "sample": [],
      "unknown_reason_sample": []
    },
    "notes": []
  },
  "anomaly_count": 0,
  "total_cycles": 0,
  "anomalies": []
}""".encode("utf-8")
    assert actual == expected


def test_matching_commit_witness_does_not_mask_existing_integrity_failure():
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 0 1\nW 0 aa U 1 1\nE 0\n",
        "C 2 1 1 2 0 1\nW 2 bb U 1 2\nE 2\n",
    )
    try:
        res = verify_trace_dir(d, expected_commits=2)
        assert res.integrity.observed_commits == 2
        assert res.integrity.missing_txids == 1
        assert not res.integrity.clean()
        assert not res.certified
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_expected_commits_accepts_single_trace_dir():
    import contextlib
    import io
    from orchestrator.verifier import cli
    with contextlib.redirect_stdout(io.StringIO()):
        assert cli.main([
            os.path.join(FIX, "g1_serial"), "--expected-commits", "2", "--quiet",
            "--protocol", "silo", "--ccbench-root", CCBENCH_ROOT,
        ]) == 0


def test_cli_expected_commits_mismatch_is_indeterminate_json():
    import contextlib
    import io
    from orchestrator.verifier import cli
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        rc = cli.main([
            os.path.join(FIX, "g1_serial"),
            "--expected-commits", "3", "--json",
            "--protocol", "silo", "--ccbench-root", CCBENCH_ROOT,
        ])
    payload = json.loads(stdout.getvalue())
    result = payload["results"][0]
    assert rc == 3
    assert result["certified"] is False
    assert result["verdict"] == "indeterminate"
    assert result["integrity"]["notes"] == [
        "commit witness mismatch: expected=3 observed=2 delta=-1"
    ]


def test_cli_expected_commits_rejects_multiple_trace_dirs():
    import contextlib
    import io
    from orchestrator.verifier import cli
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            cli.main([
                os.path.join(FIX, "g1_serial"), os.path.join(FIX, "g2_rmw_chain"),
                "--expected-commits", "2",
            ])
        assert False, "複数 trace_dir と witness の併用を拒否すべき"
    except SystemExit as exc:
        assert exc.code != 0


def test_cli_expected_commits_rejects_negative_integer():
    import contextlib
    import io
    from orchestrator.verifier import cli
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            cli.main([os.path.join(FIX, "g1_serial"), "--expected-commits", "-1"])
        assert False, "負数 witness を拒否すべき"
    except SystemExit as exc:
        assert exc.code != 0


def test_cli_expected_commits_rejects_non_integer():
    import contextlib
    import io
    from orchestrator.verifier import cli
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            cli.main([os.path.join(FIX, "g1_serial"), "--expected-commits", "two"])
        assert False, "非整数 witness を拒否すべき"
    except SystemExit as exc:
        assert exc.code != 0


def test_nonascii_wrapped_as_parse_error():
    """バイナリごみ (非 ASCII) は生 UnicodeDecodeError でなく ParseError で返す
    (pipeline の variant 単位 abort 隔離・exit code 2 の意味を保つ)。"""
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="izanagi_trace_")
    with open(os.path.join(d, "trace_0.log"), "wb") as f:
        f.write(b"C 0 0 1 1 0 0\nE 0\n\xff\xfe garbage\n")
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


def test_multi_ww_reason_report_is_hash_seed_deterministic():
    import shutil

    keys = [f"{value:016x}" for value in range(1, 7)]
    rows = []
    for txid, tid in ((0, 1), (1, 2)):
        rows.append(f"C {txid} {txid} 1 {tid} 6 6")
        rows.extend(f"R {txid} {key} 1 0" for key in keys)
        rows.extend(f"W {txid} {key} U 1 {tid}" for key in keys)
        rows.append(f"E {txid}")
    trace_dir = _tmp_trace("\n".join(rows) + "\n")

    script = (
        "import json,sys;"
        "from orchestrator.verifier import result_to_dict,verify_trace_dir;"
        "report=result_to_dict(verify_trace_dir(sys.argv[1],workers=1));"
        "sys.stdout.write(json.dumps("
        "report,sort_keys=True,separators=(',',':')))"
    )

    try:
        reports = []
        output_tail_bytes = 4096

        def _output_tail(output):
            return (output or b"")[-output_tail_bytes:]

        for seed in ("1", "777"):
            environment = dict(os.environ)
            environment["PYTHONHASHSEED"] = seed
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                completed = subprocess.run(
                    [sys.executable, "-c", script, trace_dir],
                    cwd=_REPO,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=120,
                )
            except subprocess.TimeoutExpired as exc:
                assert False, (
                    f"seed={seed} subprocess timed out after {exc.timeout}s; "
                    f"stdout_tail={_output_tail(exc.stdout)!r}; "
                    f"stderr_tail={_output_tail(exc.stderr)!r}"
                )
            assert completed.returncode == 0, (
                f"seed={seed}; returncode={completed.returncode}; "
                f"stdout_tail={_output_tail(completed.stdout)!r}; "
                f"stderr_tail={_output_tail(completed.stderr)!r}"
            )
            reports.append(completed.stdout)

        assert reports[0] == reports[1]
        for raw in reports:
            payload = json.loads(raw)
            edge = next(
                edge for edge in payload["anomalies"][0]["edges"]
                if (edge["from"], edge["to"]) == (0, 1)
            )
            assert [
                (reason["type"], reason["key"])
                for reason in edge["reasons"]
            ] == [("ww", key) for key in keys]
            assert payload["verdict"] == "non-serializable"
            assert payload["serializable"] is False
            assert payload["anomaly_count"] == 1
            assert payload["total_cycles"] == 1
            assert payload["anomalies"][0]["phenomenon"] == "G2"
            # certified は cycle と proof-surface metadata 欠落で過剰決定になるため assert しない。
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)


# ---- 実 Silo トレース (tracked prefix は常時、大規模 sample は存在時だけ) ----

_REAL_SILO_FIXTURE_BYTES = {
    "trace_0.log": (43140, "dd29e43ecba185dc898436f677ed85a703151171cb925fa730f8fd9948947e99"),
    "trace_1.log": (110139, "ae31f582340e6cfa0615e435145716524ba8d5f4af79a8b78688e5a025c027a2"),
    "trace_2.log": (111402, "66a4f265ce8d66163d9db63a4a7f4b2e726cee72cb49b63d3b0d67d2482c1c25"),
    "trace_3.log": (51209, "240d03187bc75fe5cd5fd01c2cea67d3d27033b2e91f37444a19a83e678c7f03"),
}
_SILO_SERIAL_1THREAD_FIXTURE_BYTES = {
    "trace_0.log": (
        43543,
        "1dbb84734cd360e785f25ae241ab2d61ef51a4b2c55e77ea8af2a641ee511a2a",
    ),
}
_BROKEN_SILO_NORW_FIXTURE_BYTES = {
    "trace_0.log": (
        17919,
        "c2ceedba73a0602d22cc08b05bcb5abb41c044f9b6e6f9ed22ef5a86450ee2e0",
    ),
    "trace_1.log": (
        24452,
        "fda8b5769f090291cf65ec8e1c22dba37fd8caa3a0938cb1f0601d9deaf85c4b",
    ),
    "trace_2.log": (
        14148,
        "bb310698a5b86cfcde44a10ff64e0b3b43d7c6f85b7d2c101ddae3fb265bd8fa",
    ),
    "trace_3.log": (
        8311,
        "2847b9501f3dbec71b7d7e8dcaf06a9bf9b3bcb174c47a446998025819a1b17f",
    ),
}


def test_silo_serial_1thread_fixture_contract():
    """g6 の独立根拠、派生受理結果、verifier golden を分離して固定する。"""
    res = verify_trace_dir(SILO_SERIAL_1THREAD_FIXTURE, expected_commits=200)

    # 独立根拠: 1 thread の逐次実行から verifier の外で決まるのは
    # serializable というラベルだけである。先にその構造前提を検査する。
    txns, _issues = parse_trace_dir(SILO_SERIAL_1THREAD_FIXTURE)
    assert len({txn.thid for txn in txns}) == 1
    by_id = {txn.txid: txn for txn in txns}
    assert set(by_id) == set(range(len(txns)))
    ordered = [by_id[txid] for txid in range(len(txns))]
    assert all(
        left.commit < right.commit
        for left, right in zip(ordered, ordered[1:])
    )
    dsg = DSG(txns)
    assert all(
        by_id[src].commit < by_id[dst].commit
        for src, destinations in dsg.adj.items()
        for dst in destinations
    )
    assert res.serializable

    # verifier 由来の golden: integrity、統計、巡回診断は独立証明ではない。
    assert res.integrity.clean(), res.integrity.notes
    assert res.anomalies == []
    assert res.total_cycles == 0
    assert (
        res.n_txns, res.n_reads, res.n_writes, res.n_keys, res.n_edges,
    ) == (200, 924, 460, 131, 931)

    # 派生する受理結果: verdict はラベルの言い換えである。certified は定義上
    # n_txns > 0 and serializable and integrity.clean() なので、先行 assert から決まる。
    assert res.verdict == "serializable"
    assert res.certified


def test_broken_silo_norw_fixture_contract():
    """r8 の独立根拠、派生受理結果、verifier golden を分離して固定する。"""
    res = verify_trace_dir(BROKEN_SILO_NORW_FIXTURE, expected_commits=288)

    # 独立根拠: read-set 再検証を抜いた build の raw witness 監査により、
    # verifier を使わず G2 が少なくとも 1 本実在すると確認済みである。
    assert not res.serializable

    # 派生する受理結果: verdict はラベルの言い換えであり、not certified は
    # certified の定義に serializable が必要なことから先行 assert だけで決まる。
    assert res.verdict == "non-serializable"
    assert not res.certified

    # verifier 由来の golden: integrity、統計、巡回集合、辺と理由は
    # raw witness 監査による独立証明ではない。
    assert res.integrity.clean(), res.integrity.notes
    assert res.anomalies
    assert all(anomaly.phenomenon == "G2" for anomaly in res.anomalies)

    assert (
        res.n_txns, res.n_reads, res.n_writes, res.n_keys, res.n_edges,
    ) == (288, 1352, 693, 149, 1509)
    assert len(res.anomalies) == 4
    assert res.total_cycles == 4
    assert all(
        edge.reasons
        for anomaly in res.anomalies
        for edge in anomaly.edges
    )
    actual = {
        frozenset(anomaly.cycle): {
            (edge.src, edge.dst): (edge.types, edge.reasons)
            for edge in anomaly.edges
        }
        for anomaly in res.anomalies
    }
    assert len(actual) == len(res.anomalies)
    assert all(
        len({(edge.src, edge.dst) for edge in anomaly.edges})
        == len(anomaly.edges)
        for anomaly in res.anomalies
    )
    expected = {
        frozenset({191, 192, 195}): {
            (191, 192): (
                [WW, WR],
                [
                    EdgeReason(WW, "0000000000000000", (1, 135), (1, 136)),
                    EdgeReason(WR, "0000000000000001", (1, 135), None),
                    EdgeReason(WR, "0000000000000000", (1, 135), None),
                ],
            ),
            (192, 195): (
                [WW],
                [EdgeReason(WW, "0000000000000000", (1, 136), (1, 137))],
            ),
            (195, 191): (
                [RW],
                [EdgeReason(RW, "0000000000000000", (1, 133), (1, 135))],
            ),
        },
        frozenset({137, 139, 140}): {
            (137, 139): (
                [WR],
                [EdgeReason(WR, "0000000000000000", (1, 101), None)],
            ),
            (139, 140): (
                [RW],
                [EdgeReason(RW, "0000000000000003", (1, 94), (1, 103))],
            ),
            (140, 137): (
                [RW],
                [EdgeReason(RW, "0000000000000001", (1, 95), (1, 101))],
            ),
        },
        frozenset({200, 206}): {
            (200, 206): (
                [WW],
                [EdgeReason(WW, "0000000000000008", (1, 139), (1, 142))],
            ),
            (206, 200): (
                [RW],
                [EdgeReason(RW, "0000000000000008", (1, 112), (1, 139))],
            ),
        },
        frozenset({3, 7}): {
            (3, 7): (
                [WR],
                [EdgeReason(WR, "0000000000000009", (1, 2), None)],
            ),
            (7, 3): (
                [RW],
                [EdgeReason(RW, "0000000000000005", (1, 0), (1, 2))],
            ),
        },
    }
    assert actual == expected


def test_broken_silo_norw_structured_report_is_exact():
    """verifier 由来の外部 report 射影を独立証明でない golden として固定する。"""
    res = verify_trace_dir(BROKEN_SILO_NORW_FIXTURE, expected_commits=288)
    anomalies = result_to_dict(res)["anomalies"]
    actual = {frozenset(anomaly["cycle"]): anomaly for anomaly in anomalies}
    assert len(actual) == len(anomalies)
    expected = {
        frozenset({191, 192, 195}): {
            "phenomenon": "G2",
            "length": 3,
            "cycle": [191, 192, 195],
            "edges": [
                {
                    "from": 191,
                    "to": 192,
                    "types": ["ww", "wr"],
                    "reasons": [
                        {
                            "type": "ww",
                            "key": "0000000000000000",
                            "u_ver": [1, 135],
                            "v_ver": [1, 136],
                        },
                        {
                            "type": "wr",
                            "key": "0000000000000001",
                            "u_ver": [1, 135],
                        },
                        {
                            "type": "wr",
                            "key": "0000000000000000",
                            "u_ver": [1, 135],
                        },
                    ],
                },
                {
                    "from": 192,
                    "to": 195,
                    "types": ["ww"],
                    "reasons": [
                        {
                            "type": "ww",
                            "key": "0000000000000000",
                            "u_ver": [1, 136],
                            "v_ver": [1, 137],
                        },
                    ],
                },
                {
                    "from": 195,
                    "to": 191,
                    "types": ["rw"],
                    "reasons": [
                        {
                            "type": "rw",
                            "key": "0000000000000000",
                            "u_ver": [1, 133],
                            "v_ver": [1, 135],
                        },
                    ],
                },
            ],
        },
        frozenset({137, 139, 140}): {
            "phenomenon": "G2",
            "length": 3,
            "cycle": [137, 139, 140],
            "edges": [
                {
                    "from": 137,
                    "to": 139,
                    "types": ["wr"],
                    "reasons": [
                        {
                            "type": "wr",
                            "key": "0000000000000000",
                            "u_ver": [1, 101],
                        },
                    ],
                },
                {
                    "from": 139,
                    "to": 140,
                    "types": ["rw"],
                    "reasons": [
                        {
                            "type": "rw",
                            "key": "0000000000000003",
                            "u_ver": [1, 94],
                            "v_ver": [1, 103],
                        },
                    ],
                },
                {
                    "from": 140,
                    "to": 137,
                    "types": ["rw"],
                    "reasons": [
                        {
                            "type": "rw",
                            "key": "0000000000000001",
                            "u_ver": [1, 95],
                            "v_ver": [1, 101],
                        },
                    ],
                },
            ],
        },
        frozenset({200, 206}): {
            "phenomenon": "G2",
            "length": 2,
            "cycle": [200, 206],
            "edges": [
                {
                    "from": 200,
                    "to": 206,
                    "types": ["ww"],
                    "reasons": [
                        {
                            "type": "ww",
                            "key": "0000000000000008",
                            "u_ver": [1, 139],
                            "v_ver": [1, 142],
                        },
                    ],
                },
                {
                    "from": 206,
                    "to": 200,
                    "types": ["rw"],
                    "reasons": [
                        {
                            "type": "rw",
                            "key": "0000000000000008",
                            "u_ver": [1, 112],
                            "v_ver": [1, 139],
                        },
                    ],
                },
            ],
        },
        frozenset({3, 7}): {
            "phenomenon": "G2",
            "length": 2,
            "cycle": [3, 7],
            "edges": [
                {
                    "from": 3,
                    "to": 7,
                    "types": ["wr"],
                    "reasons": [
                        {
                            "type": "wr",
                            "key": "0000000000000009",
                            "u_ver": [1, 2],
                        },
                    ],
                },
                {
                    "from": 7,
                    "to": 3,
                    "types": ["rw"],
                    "reasons": [
                        {
                            "type": "rw",
                            "key": "0000000000000005",
                            "u_ver": [1, 0],
                            "v_ver": [1, 2],
                        },
                    ],
                },
            ],
        },
    }
    assert actual == expected


def test_new_real_fixture_bytes_are_exact():
    """raw bytes を独立性の証明ではない fixture golden として固定する。"""
    actual_bytes = {}
    for fixture_name, trace_dir, expected_bytes in (
        (
            "g6_silo_serial_1thread",
            SILO_SERIAL_1THREAD_FIXTURE,
            _SILO_SERIAL_1THREAD_FIXTURE_BYTES,
        ),
        (
            "r8_silo_broken_norw",
            BROKEN_SILO_NORW_FIXTURE,
            _BROKEN_SILO_NORW_FIXTURE_BYTES,
        ),
    ):
        fixture_bytes = {}
        for filename in sorted(expected_bytes):
            with open(os.path.join(trace_dir, filename), "rb") as fh:
                data = fh.read()
            fixture_bytes[filename] = (
                len(data), hashlib.sha256(data).hexdigest(),
            )
        actual_bytes[fixture_name] = fixture_bytes
    assert actual_bytes == {
        "g6_silo_serial_1thread": _SILO_SERIAL_1THREAD_FIXTURE_BYTES,
        "r8_silo_broken_norw": _BROKEN_SILO_NORW_FIXTURE_BYTES,
    }


def _assert_certified_serializable(trace_dir, *, expected_commits=None):
    res = verify_trace_dir(trace_dir, expected_commits=expected_commits)
    assert res.serializable, (
        f"trace MUST be serializable but got {len(res.anomalies)} anomalies: "
        f"{[a.phenomenon for a in res.anomalies[:3]]}")
    assert res.integrity.clean(), f"integrity not clean: {res.integrity.notes}"
    assert res.certified, "serializable clean trace MUST be certified"
    return res


def test_real_silo_fixture_bytes_are_exact():
    actual = {}
    for filename in sorted(_REAL_SILO_FIXTURE_BYTES):
        with open(os.path.join(REAL_SILO_FIXTURE, filename), "rb") as fh:
            data = fh.read()
        actual[filename] = (len(data), hashlib.sha256(data).hexdigest())
    assert actual == _REAL_SILO_FIXTURE_BYTES


def test_epoch_version_order_g2():
    res = _verify("r6_epoch_version_order")
    assert not res.serializable
    assert res.verdict == "non-serializable"
    assert res.integrity.clean(), res.integrity.notes
    assert not res.certified
    assert len(res.anomalies) == 1
    assert res.anomalies[0].phenomenon == "G2"
    assert set(res.anomalies[0].cycle) == {0, 1}


def test_epoch_rw_successor_order_g2():
    res = _verify("r7_epoch_rw_successor")
    assert not res.serializable
    assert res.verdict == "non-serializable"
    assert res.integrity.clean(), res.integrity.notes
    assert not res.certified
    assert len(res.anomalies) == 1
    anomaly = res.anomalies[0]
    assert anomaly.phenomenon == "G2"
    assert set(anomaly.cycle) == {1, 2}
    cross_epoch_rw = [
        reason
        for edge in anomaly.edges
        if (edge.src, edge.dst) == (2, 1)
        for reason in edge.reasons
        if reason.etype == RW
    ]
    assert cross_epoch_rw == [
        EdgeReason(RW, "0000000000000001", (1, 100), (2, 1)),
    ]


def test_cicada_g1_genesis_readonly_versions():
    trace_dir = os.path.join(FIX, "cicada_g1_genesis_readonly")
    res = verify_trace_dir(
        trace_dir, protocol="cicada", ccbench_root=REAL_CCBENCH_ROOT,
    )
    assert res.serializable and res.total_cycles == 0 and not res.anomalies
    assert (res.n_txns, res.n_reads, res.n_writes) == (6, 6, 3)
    for name in (
        "orphan_reads", "version_dups", "dup_txids", "genesis_commits",
        "missing_txids", "write_version_mismatch", "malformed_keys",
        "framing_violations", "lock_coverage_violations",
        "write_intent_violations", "permutation_violations",
        "existence_violations",
    ):
        assert getattr(res.integrity, name) == 0, name
    assert res.integrity.proof_surfaces.as_record() == {
        "protocol": "cicada", "X": "unavailable", "P": "unavailable",
        "I": "unavailable",
    }
    assert res.verdict == "indeterminate" and not res.certified

    txns, _issues = parse_trace_dir(trace_dir)
    by_txid = {txn.txid: txn for txn in txns}
    key = "0000000000000001"
    assert by_txid[1].writes == []
    assert by_txid[1].reads[0].ver == (1, 0)
    assert by_txid[4].reads[0].ver == (1, 4294967295)
    assert by_txid[5].reads[0].ver == (2, 0)
    from orchestrator.verifier.parse import _parse_trace_dir_compact
    dsg = DSG.from_compact(_parse_trace_dir_compact(trace_dir))
    assert dsg.versions[key] == [
        (1, 2147483648), (1, 4294967295), (2, 0),
    ]


def test_cicada_g2_write_skew_versions_and_reasons():
    res = verify_trace_dir(
        os.path.join(FIX, "cicada_g2_write_skew"),
        protocol="cicada", ccbench_root=REAL_CCBENCH_ROOT,
    )
    assert not res.serializable and res.verdict == "non-serializable"
    assert res.total_cycles >= 1 and not res.certified
    assert res.integrity.orphan_reads == 0
    assert res.integrity.version_dups == 0
    assert res.integrity.framing_violations == 0
    g2 = [a for a in res.anomalies if a.phenomenon == "G2"]
    assert g2
    reasons = {
        (edge.src, edge.dst, reason.etype, reason.key,
         reason.u_ver, reason.v_ver)
        for anomaly in g2 for edge in anomaly.edges for reason in edge.reasons
        if reason.etype == RW
    }
    assert reasons == {
        (0, 1, RW, "0000000000000001", (1, 0), (2, 0)),
        (1, 0, RW, "0000000000000002", (1, 0), (1, 2147483648)),
    }


def test_real_silo_edge_type_combinations_are_exact():
    txns, _issues = parse_trace_dir(REAL_SILO_FIXTURE)
    dsg = DSG(txns)
    combinations = Counter(
        tuple(sorted({reason.etype for reason in dsg._reasons(src, dst)}))
        for src, destinations in dsg.adj.items()
        for dst in destinations
    )
    assert combinations == Counter({
        (WR,): 2677,
        (RW,): 2724,
        (WR, WW): 2934,
        (RW, WR, WW): 62,
        (RW, WR): 69,
    })

    extended = Counter()
    for edge_types, count in combinations.items():
        for edge_type in edge_types:
            extended[edge_type] += count
    assert extended == Counter({WR: 5742, RW: 2855, WW: 2996})
    assert sum(combinations.values()) == 8466


def test_real_silo_serializable():
    res = _assert_certified_serializable(
        REAL_SILO_FIXTURE, expected_commits=1345,
    )
    assert (
        res.n_txns, res.n_reads, res.n_writes, res.n_keys, res.n_edges,
    ) == (1345, 6311, 3244, 199, 8466)

    if os.path.isdir(SILO_SAMPLE):
        _assert_certified_serializable(SILO_SAMPLE)


def test_real_silo_node_behaviorally_calls_verifier_and_propagates_failure():
    global verify_trace_dir

    original = verify_trace_dir
    tracked_fixture = os.path.normcase(os.path.realpath(os.path.join(
        _HERE, "fixtures", "g5_silo_real_prefix",
    )))
    clean = Integrity(
        expected_commits=1345,
        observed_commits=1345,
        proof_surfaces=ProofSurfaceAssessment(
            protocol="silo",
            lock_coverage="evidence-present",
            permutation="evidence-present",
            write_intent="evidence-absent",
        ),
    )
    good = VerifyResult(
        trace_dir=tracked_fixture,
        serializable=True,
        integrity=clean,
        n_txns=1345,
        n_reads=6311,
        n_writes=3244,
        n_keys=199,
        n_edges=8466,
    )

    def invoke(spy):
        global verify_trace_dir
        verify_trace_dir = spy
        try:
            try:
                test_real_silo_serializable()
            except BaseException as exc:
                is_pytest_skip = (
                    type(exc).__module__ == "_pytest.outcomes"
                    and type(exc).__name__ == "Skipped"
                )
                if isinstance(exc, Skip) or is_pytest_skip:
                    raise AssertionError(
                        "tracked 実 Silo node が verifier 実走を skip した"
                    ) from exc
                raise
        finally:
            verify_trace_dir = original

    calls = []

    def good_spy(trace_dir, max_report=20, *, expected_commits=None):
        calls.append((
            os.path.normcase(os.path.realpath(os.fspath(trace_dir))),
            expected_commits,
        ))
        return good

    invoke(good_spy)
    mandatory_calls = [call for call in calls if call[0] == tracked_fixture]
    assert mandatory_calls == [(tracked_fixture, 1345)]
    assert verify_trace_dir is original

    broken = replace(good, serializable=False)
    try:
        invoke(lambda *args, **kwargs: broken)
        assert False, "壊れた verifier 結果を node が assertion error にしなかった"
    except AssertionError as exc:
        assert "trace MUST be serializable" in str(exc)
    assert verify_trace_dir is original

    def skip_spy(*args, **kwargs):
        raise Skip("behavioral meta-test sentinel")

    try:
        invoke(skip_spy)
        assert False, "verifier の Skip を meta-test が赤にしなかった"
    except AssertionError as exc:
        assert isinstance(exc.__cause__, Skip)
    assert verify_trace_dir is original


def test_parallel_production_path_matches_certified_result_and_runs_workers():
    """The certified result adopts real parse and DSG child-process outcomes."""
    import importlib
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    dsg_module = importlib.import_module("orchestrator.verifier.dsg")
    sequential = verify_trace_dir(
        os.path.join(FIX, "g3_readonly"), workers=1,
    )
    parallel = verify_trace_dir(
        os.path.join(FIX, "g3_readonly"), workers=2,
    )
    assert result_to_dict(parallel) == result_to_dict(sequential)
    assert parallel.certified
    adopted_parse_pids = parse_module._LAST_PARSE_WORKER_PIDS
    adopted_dsg_pids = dsg_module._LAST_DSG_WORKER_PIDS
    assert adopted_parse_pids
    assert adopted_dsg_pids
    # These diagnostics are built from adopted outcomes only.  A sequential
    # fallback records the parent PID and therefore cannot satisfy this check.
    assert os.getpid() not in adopted_parse_pids
    assert os.getpid() not in adopted_dsg_pids


def test_default_worker_cap_is_16_but_explicit_workers_remain_available():
    import importlib
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    original_getaffinity = parse_module.os.sched_getaffinity
    parse_module.os.sched_getaffinity = lambda _pid: set(range(64))
    try:
        assert parse_module._effective_worker_count(64, None) == 16
        assert parse_module._effective_worker_count(64, 48) == 48
    finally:
        parse_module.os.sched_getaffinity = original_getaffinity


def test_concurrent_verifications_keep_edge_worker_inputs_isolated():
    """Two threads cannot replace one another's cyclic/acyclic edge input."""
    import concurrent.futures
    import shutil
    import threading

    common = (
        "C 0 0 1 1 1 1\n"
        "R 0 aa 1 0\n"
        "W 0 bb U 1 1\n"
        "E 0\n"
    )
    cyclic = _tmp_trace(
        common,
        "C 1 1 1 2 1 1\n"
        "R 1 bb 1 0\n"
        "W 1 aa U 1 2\n"
        "E 1\n",
    )
    acyclic = _tmp_trace(
        common,
        "C 1 1 1 2 1 1\n"
        "R 1 bb 1 1\n"
        "W 1 aa U 1 2\n"
        "E 1\n",
    )
    real_process_pool = concurrent.futures.ProcessPoolExecutor
    thread_state = threading.local()
    both_edge_pools_ready = threading.Barrier(2)
    both_edge_pools_forked = threading.Barrier(2)
    forked_edge_pools = []
    forked_edge_pools_lock = threading.Lock()

    class SynchronizedProcessPool(real_process_pool):
        """Synchronize real edge-pool forks after both verifier calls arrive."""

        def __init__(self, *args, **kwargs):
            pool_number = getattr(thread_state, "pool_number", 0) + 1
            thread_state.pool_number = pool_number
            self._synchronize_first_submit = pool_number == 2
            super().__init__(*args, **kwargs)

        def submit(self, *args, **kwargs):
            if self._synchronize_first_submit:
                self._synchronize_first_submit = False
                both_edge_pools_ready.wait(timeout=15)
                future = super().submit(*args, **kwargs)
                # ProcessPoolExecutor forks all workers during the first submit.
                with forked_edge_pools_lock:
                    forked_edge_pools.append(id(self))
                both_edge_pools_forked.wait(timeout=15)
                return future
            return super().submit(*args, **kwargs)

    try:
        cyclic_baseline = verify_trace_dir(
            cyclic, expected_commits=2, workers=1,
        )
        acyclic_baseline = verify_trace_dir(
            acyclic, expected_commits=2, workers=1,
        )
        assert cyclic_baseline.verdict == "non-serializable"
        assert acyclic_baseline.verdict == "serializable"

        concurrent.futures.ProcessPoolExecutor = SynchronizedProcessPool
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            cyclic_future = executor.submit(
                verify_trace_dir, cyclic, expected_commits=2, workers=2,
            )
            acyclic_future = executor.submit(
                verify_trace_dir, acyclic, expected_commits=2, workers=2,
            )
            cyclic_result = cyclic_future.result(timeout=30)
            acyclic_result = acyclic_future.result(timeout=30)
        assert len(forked_edge_pools) == 2
        assert result_to_dict(cyclic_result) == result_to_dict(cyclic_baseline)
        assert result_to_dict(acyclic_result) == result_to_dict(acyclic_baseline)
    finally:
        concurrent.futures.ProcessPoolExecutor = real_process_pool
        shutil.rmtree(cyclic, ignore_errors=True)
        shutil.rmtree(acyclic, ignore_errors=True)


def test_file_failures_keep_sorted_path_priority_over_later_io_error():
    """A later dangling symlink cannot replace the first file's ParseError."""
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 1 0\nR 0 aa not-an-int 0\nE 0\n",
        "C 1 1 1 2 0 0\nE 1\n",
    )
    later_path = os.path.join(d, "trace_1.log")
    os.unlink(later_path)
    os.symlink(os.path.join(d, "missing-target.log"), later_path)
    try:
        for workers in (1, 2):
            try:
                verify_trace_dir(d, workers=workers)
                assert False, "the first path's ParseError must win"
            except ParseError as exc:
                assert "trace_0.log:2" in str(exc)
                assert type(exc.__cause__) is ValueError
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_worker_parse_error_survives_file_disappearing_before_parent_reread():
    """The worker's ParseError remains primary if parent reread hits I/O."""
    import importlib
    import shutil
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    d = _tmp_trace(
        "C 0 0 1 1 1 0\nR 0 aa not-an-int 0\nE 0\n",
        "C 1 1 1 2 0 0\nE 1\n",
    )
    original = parse_module._parse_file_to_columns
    parent_pid = os.getpid()

    def remove_failed_file(task):
        outcome = original(task)
        if (task[0] == 0 and os.getpid() != parent_pid
                and isinstance(outcome, parse_module._ParsedFileFailure)):
            os.unlink(task[1])
        return outcome

    parse_module._parse_file_to_columns = remove_failed_file
    try:
        try:
            verify_trace_dir(d, workers=2)
            assert False, "the worker's original ParseError must be restored"
        except ParseError as exc:
            assert "trace_0.log:2" in str(exc)
            assert type(exc.__cause__) is ValueError
            assert "not-an-int" in str(exc.__cause__)
    finally:
        parse_module._parse_file_to_columns = original
        shutil.rmtree(d, ignore_errors=True)


def test_daemon_process_falls_back_to_sequential_verification():
    """A daemon that cannot fork still verifies a valid multi-file trace."""
    import multiprocessing
    context = multiprocessing.get_context("fork")
    parent_conn, child_conn = context.Pipe(duplex=False)

    def run_in_daemon():
        try:
            result = verify_trace_dir(
                os.path.join(FIX, "g3_readonly"), workers=2,
            )
            child_conn.send(("ok", result.certified, result.verdict))
        except BaseException as exc:
            child_conn.send(("error", type(exc).__name__, str(exc)))
        finally:
            child_conn.close()

    process = context.Process(target=run_in_daemon)
    process.daemon = True
    process.start()
    child_conn.close()
    try:
        process.join(20)
        assert not process.is_alive(), "daemon verifier did not terminate"
        assert parent_conn.poll(), "daemon verifier returned no result"
        assert parent_conn.recv() == ("ok", True, "serializable")
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
            process.join(5)
        parent_conn.close()


def test_parallel_worker_exit_discards_partial_results_and_rereads_all_files():
    """M1: losing the tail outcome cannot certify the surviving half."""
    import importlib
    import shutil
    import time
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    d = _tmp_trace(
        "C 0 0 1 1 1 1\nR 0 aa 1 0\nW 0 bb U 1 1\nE 0\n",
        "C 1 1 1 2 1 1\nR 1 bb 1 0\nW 1 aa U 1 2\nE 1\n",
    )
    marker = os.path.join(d, "worker-exit.pid")
    parent_pid = os.getpid()
    original = parse_module._parse_file_to_columns

    def force_tail_worker_exit(task):
        if task[0] == 1 and os.getpid() != parent_pid:
            # Let path 0 become a received partial outcome before this worker dies.
            time.sleep(0.2)
            with open(marker, "w") as fh:
                fh.write(str(os.getpid()))
            os._exit(71)
        return original(task)

    parse_module._parse_file_to_columns = force_tail_worker_exit
    try:
        result = verify_trace_dir(d, workers=2)
        assert not result.serializable
        assert result.verdict == "non-serializable"
        with open(marker) as fh:
            worker_pid = int(fh.read())
        assert worker_pid != parent_pid
    finally:
        parse_module._parse_file_to_columns = original
        shutil.rmtree(d, ignore_errors=True)


def test_parallel_parse_issues_keep_sorted_path_order():
    """M2: completion order never becomes ParseIssues/report order."""
    import importlib
    import shutil
    import time
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    d = _tmp_trace(
        "C 0 0 1 1 1 0\nE 0\n",
        "C 1 1 1 2 0 1\nE 1\n",
    )
    sequential = verify_trace_dir(d, workers=1)
    original = parse_module._parse_file_to_columns
    parent_pid = os.getpid()

    def delay_first_path(task):
        if task[0] == 0 and os.getpid() != parent_pid:
            time.sleep(0.2)
        return original(task)

    parse_module._parse_file_to_columns = delay_first_path
    try:
        parallel = verify_trace_dir(d, workers=2)
        assert result_to_dict(parallel) == result_to_dict(sequential)
        details = parallel.integrity.framing_violation_details
        assert [detail.txid for detail in details] == [0, 1]
    finally:
        parse_module._parse_file_to_columns = original
        shutil.rmtree(d, ignore_errors=True)


def _ordinal_witness_trace() -> str:
    """Three-file trace whose source 1 edges arrive from distinct read shards."""
    files = [[], [], []]
    for txid in range(17):
        target = 0 if txid < 8 else (1 if txid < 16 else 2)
        if txid == 1:
            files[target].append(
                "C 1 0 1 2 2 2\n"
                "R 1 cc 1 9\nR 1 dd 1 17\n"
                "W 1 aa U 1 2\nW 1 bb U 1 2\nE 1\n")
        elif txid == 8:
            files[target].append(
                "C 8 1 1 9 1 1\nR 8 aa 1 2\nW 8 cc U 1 9\nE 8\n")
        elif txid == 16:
            files[target].append(
                "C 16 2 1 17 1 1\nR 16 bb 1 2\nW 16 dd U 1 17\nE 16\n")
        else:
            files[target].append(
                f"C {txid} {target} 2 {txid + 1} 0 0\nE {txid}\n")
    return _tmp_trace(*["".join(rows) for rows in files])


def test_parallel_edge_replay_uses_global_logical_ordinal():
    """M3: arrival reversal preserves the exact anomaly witness and ordering."""
    import importlib
    import shutil
    import time
    dsg_module = importlib.import_module("orchestrator.verifier.dsg")
    d = _ordinal_witness_trace()
    sequential = verify_trace_dir(d, workers=1)
    original = dsg_module._edge_candidates_for_task
    parent_pid = os.getpid()

    def delay_edge_fragment(task):
        if (task.kind == "read" and task.start <= 8 < task.end
                and os.getpid() != parent_pid):
            time.sleep(0.2)
        return original(task)

    dsg_module._edge_candidates_for_task = delay_edge_fragment
    try:
        parallel = verify_trace_dir(d, workers=3)
        assert result_to_dict(parallel) == result_to_dict(sequential)
        assert parallel.anomalies[0].cycle == [1, 8]
    finally:
        dsg_module._edge_candidates_for_task = original
        shutil.rmtree(d, ignore_errors=True)


def _serial_parent_optimization_trace() -> str:
    """Four-file trace with two ordered SCCs and colliding destinations."""
    files = [[], [], [], []]
    for txid in range(33):
        file_index = min(txid // 8, 3)
        if txid == 0:
            files[file_index].append(
                "C 0 0 2 1 1 5\n"
                "R 0 aa 1 0\n"
                "W 0 10 U 2 1\nW 0 12 U 2 1\n"
                "W 0 14 U 2 1\nW 0 16 U 2 1\n"
                "W 0 18 U 2 1\nE 0\n")
        elif txid == 8:
            files[file_index].append(
                "C 8 1 2 9 4 0\n"
                "R 8 b0 1 0\nR 8 aa 1 0\n"
                "R 8 10 2 1\nR 8 12 1 0\nE 8\n")
        elif txid == 16:
            files[file_index].append(
                "C 16 2 2 17 5 0\n"
                "R 16 b2 1 0\nR 16 b4 1 0\nR 16 aa 1 0\n"
                "R 16 14 2 1\nR 16 16 1 0\nE 16\n")
        elif txid == 17:
            files[file_index].append(
                "C 17 2 2 18 1 4\n"
                "R 17 18 2 1\n"
                "W 17 20 U 2 18\nW 17 22 U 2 18\n"
                "W 17 24 U 2 18\nW 17 26 U 2 18\nE 17\n")
        elif txid == 24:
            files[file_index].append(
                "C 24 3 2 25 6 0\n"
                "R 24 b6 1 0\nR 24 b8 1 0\nR 24 ba 1 0\n"
                "R 24 aa 1 0\nR 24 20 2 18\nR 24 22 1 0\nE 24\n")
        elif txid == 32:
            files[file_index].append(
                "C 32 3 2 33 2 0\n"
                "R 32 24 2 18\nR 32 26 1 0\nE 32\n")
        else:
            files[file_index].append(
                f"C {txid} {file_index} 3 {txid + 1} 0 0\nE {txid}\n")
    return _tmp_trace(*["".join(rows) for rows in files])


def test_serial_parent_optimizations_match_workers_and_pin_witness_order():
    import importlib
    import shutil
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    dsg_module = importlib.import_module("orchestrator.verifier.dsg")
    d = _serial_parent_optimization_trace()
    try:
        compact = parse_module._parse_trace_dir_compact(d, workers=1)
        local_shared_key_ids = []
        for columns in compact.files:
            tokens = [
                columns.token_blob[columns.token_offsets[index]:
                                   columns.token_offsets[index + 1]].decode("ascii")
                for index in range(len(columns.token_offsets) - 1)
            ]
            local_shared_key_ids.append(tokens.index("aa"))
        assert local_shared_key_ids == [0, 1, 2, 3]
        compact_graph = DSG.from_compact(compact)
        assert compact_graph.adj[0] == (8, 16, 17)
        assert 0 not in compact_graph.adj[17]
        assert [set(component) for component in compact_graph._sccs()] == [
            {17, 24, 32}, {0, 8, 16},
        ]

        # The workers=4 split puts ranks 8 and 16 in different tasks, so pin
        # M2's structural premise with one fixed read task spanning both ranks
        # while excluding rank 17 (which contributes the later 0->17 edge).
        from array import array
        edge_state = dsg_module._EdgeWorkerState(
            trace=compact,
            producer=compact_graph.producer,
            versions=compact_graph.versions,
            keys=tuple(compact_graph.versions),
        )
        edge_outcome = dsg_module._edge_candidates_for_task(
            dsg_module._EdgeTask(0, "read", 0, 17), edge_state,
        )
        source_run = edge_outcome.run_src.index(0)
        run_start = edge_outcome.run_offsets[source_run]
        run_end = edge_outcome.run_offsets[source_run + 1]
        assert edge_outcome.run_dst[run_start:run_end] == array("q", [8, 16])

        source_order_dir = _ordinal_witness_trace()
        try:
            source_order_compact = parse_module._parse_trace_dir_compact(
                source_order_dir, workers=1,
            )
            source_order_graph = DSG.from_compact(source_order_compact)
            source_order_state = dsg_module._EdgeWorkerState(
                trace=source_order_compact,
                producer=source_order_graph.producer,
                versions=source_order_graph.versions,
                keys=tuple(source_order_graph.versions),
            )
            source_order_outcome = dsg_module._edge_candidates_for_task(
                dsg_module._EdgeTask(0, "read", 0, 17), source_order_state,
            )
            assert source_order_outcome.run_src == array("q", [8, 16, 1])
        finally:
            shutil.rmtree(source_order_dir, ignore_errors=True)

        sequential = verify_trace_dir(d, workers=1)
        default = verify_trace_dir(d)
        parallel = verify_trace_dir(d, workers=4)
        assert result_to_dict(default) == result_to_dict(sequential)
        assert result_to_dict(parallel) == result_to_dict(sequential)
        assert parse_module._LAST_PARSE_WORKER_PIDS
        assert dsg_module._LAST_DSG_WORKER_PIDS
        assert os.getpid() not in parse_module._LAST_PARSE_WORKER_PIDS
        assert os.getpid() not in dsg_module._LAST_DSG_WORKER_PIDS

        assert parallel.total_cycles == 2
        assert len(parallel.anomalies) == 2
        assert [anomaly.cycle for anomaly in parallel.anomalies] == [
            [17, 24], [0, 8],
        ]
        assert parallel.n_edges == 9
        assert [
            [str(reason) for edge in anomaly.edges for reason in edge.reasons]
            for anomaly in parallel.anomalies
        ] == [
            [
                "EdgeReason(etype='wr', key='20', u_ver=(2, 18), v_ver=None)",
                "EdgeReason(etype='rw', key='22', u_ver=(1, 0), v_ver=(2, 18))",
            ],
            [
                "EdgeReason(etype='wr', key='10', u_ver=(2, 1), v_ver=None)",
                "EdgeReason(etype='rw', key='12', u_ver=(1, 0), v_ver=(2, 1))",
            ],
        ]

        capped = verify_trace_dir(d, workers=1, max_report=1)
        assert capped.total_cycles == 2
        assert capped.anomalies == parallel.anomalies[:1]

        txns, _issues = parse_trace_dir(d)
        legacy_anomalies, legacy_total = DSG(txns).anomalies()
        assert legacy_total == parallel.total_cycles
        assert legacy_anomalies == parallel.anomalies
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_scc_dense_arrays_keep_root_emission_order_for_both_adjacency_types():
    from collections import defaultdict

    legacy_adjacency = defaultdict(set)
    legacy_adjacency[2].add(1)  # destination-only node 1 must be dense-mapped.
    legacy_adjacency[9].add(10)
    legacy_adjacency[10].add(9)
    legacy_adjacency[4].add(5)
    legacy_adjacency[5].add(4)
    compact_adjacency = {
        source: tuple(destinations)
        for source, destinations in legacy_adjacency.items()
    }

    actual = []
    for adjacency in (legacy_adjacency, compact_adjacency):
        graph = DSG.__new__(DSG)
        graph.adj = adjacency
        actual.append(graph._sccs())
    assert actual == [
        [[10, 9], [5, 4]],
        [[10, 9], [5, 4]],
    ]


def test_version_dup_keeps_first_writer_note_and_edge():
    import importlib
    import shutil
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    d = _tmp_trace(
        "C 0 0 2 1 0 2\n"
        "W 0 aa U 2 1\nW 0 aa U 2 1\nE 0\n",
        "C 1 1 2 1 0 1\nW 1 aa U 2 1\nE 1\n"
        "C 2 1 2 2 1 0\nR 2 aa 2 1\nE 2\n",
    )
    try:
        sequential = verify_trace_dir(d, workers=1)
        parallel = verify_trace_dir(d, workers=2)
        assert result_to_dict(parallel) == result_to_dict(sequential)
        assert sequential.integrity.version_dups == 1
        assert sequential.integrity.notes == [
            "version dup: key=aa ver=(2, 1) by txid 0 and 1",
        ]

        compact = parse_module._parse_trace_dir_compact(d, workers=1)
        graph = DSG.from_compact(compact)
        assert graph.producer[("aa", (2, 1))] == 0
        assert graph.adj == {0: (2,)}
        assert graph._reasons(0, 2) == [
            EdgeReason(WR, "aa", (2, 1), None),
        ]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_edge_worker_failure_discards_partial_tasks_and_recomputes_all():
    import importlib
    import shutil
    dsg_module = importlib.import_module("orchestrator.verifier.dsg")
    d = _ordinal_witness_trace()
    baseline = verify_trace_dir(d, workers=1)
    original = dsg_module._edge_candidates_for_task
    parent_pid = os.getpid()

    def fail_cycle_closing_task(task, state=None):
        if (task.kind == "read" and task.start <= 8 < task.end
                and os.getpid() != parent_pid):
            raise RuntimeError("edge-task failure sentinel")
        return original(task, state)

    dsg_module._edge_candidates_for_task = fail_cycle_closing_task
    try:
        recovered = verify_trace_dir(d, workers=3)
        assert result_to_dict(recovered) == result_to_dict(baseline)
        assert recovered.anomalies[0].cycle == [1, 8]
        assert dsg_module._LAST_DSG_WORKER_PIDS == frozenset({parent_pid})
    finally:
        dsg_module._edge_candidates_for_task = original
        shutil.rmtree(d, ignore_errors=True)


def test_parallel_parse_error_is_raised_by_parent_scanner_with_cause():
    """M4: worker syntax failure is reparsed, not rebuilt from exception args."""
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 1 0\nR 0 aa not-an-int 0\nE 0\n",
        "C 1 1 1 2 0 0\nE 1\n",
    )

    def capture(workers):
        try:
            verify_trace_dir(d, workers=workers)
            assert False, "ParseError expected"
        except ParseError as exc:
            frames = []
            tb = exc.__traceback__
            while tb is not None:
                frames.append(tb.tb_frame.f_code.co_name)
                tb = tb.tb_next
            return (
                type(exc), exc.args, type(exc.__cause__), str(exc.__cause__), frames,
            )

    try:
        sequential = capture(1)
        parallel = capture(2)
        assert parallel[:4] == sequential[:4]
        assert parallel[2] is ValueError
        assert "_parse_file" in parallel[4]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_compact_dsg_keeps_rw_edge_and_detects_g2_cycle():
    """M5: the production compact path must retain read anti-dependencies."""
    result = verify_trace_dir(os.path.join(FIX, "r1_write_skew"), workers=1)
    assert result.verdict == "non-serializable"
    assert result.anomalies[0].phenomenon == "G2"
    assert RW in {
        edge_type
        for edge in result.anomalies[0].edges
        for edge_type in edge.types
    }


def test_parallel_cross_file_duplicate_txid_is_parent_replayed():
    """M6: neither worker sees this duplicate locally; the parent must."""
    import shutil
    d = _tmp_trace(
        "C 0 0 1 1 0 1\nW 0 aa U 1 1\nE 0\n",
        "C 0 1 1 2 0 1\nW 0 aa U 1 2\nE 0\n",
    )
    try:
        sequential = verify_trace_dir(d, workers=1)
        parallel = verify_trace_dir(d, workers=2)
        assert result_to_dict(parallel) == result_to_dict(sequential)
        assert parallel.integrity.dup_txids == 1
        assert parallel.verdict == "indeterminate"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_sparse_huge_txid_returns_bounded_indeterminate_result():
    """Accepted A4 difference: bounded gap scan replaces legacy MemoryError."""
    import shutil
    d = _tmp_trace("C 1000000000000 0 2 1 0 0\nE 1000000000000\n")
    try:
        txns, issues = parse_trace_dir(d, workers=1)
        assert [txn.txid for txn in txns] == [1000000000000]
        assert issues.missing_txids == 1000000000000
        assert issues.missing_sample == [0, 1, 2, 3, 4]
        result = verify_trace_dir(d, workers=1)
        assert result.n_txns == 1
        assert result.integrity.missing_txids == 1000000000000
        assert result.verdict == "indeterminate"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_parallel_capability_remains_bound_to_parent_pid():
    import commit_receipt_support as receipt_support
    from orchestrator.verifier.core import verify_trace_dir_with_capability
    genome, source_evidence, build_admission = (
        receipt_support._proof_build_binding("baseline")
    )
    result, capability = verify_trace_dir_with_capability(
        os.path.join(FIX, "g3_readonly"),
        workers=2,
        genome=genome,
        source_evidence=source_evidence,
        build_admission=build_admission,
        receipt_sink_kind="test",
        receipt_lock_identity_sha256="0" * 64,
        receipt_variant="baseline",
        receipt_operation_identity="parallel-parent-pid",
        receipt_workload_tag="unit",
    )
    assert result.certified
    assert capability._pid == os.getpid()
    capability._assert_matches(
        sink_kind="test",
        lock_identity_sha256="0" * 64,
        variant="baseline",
        operation_identity="parallel-parent-pid",
        workload_tag="unit",
    )


def _capacity_tuple_result(trace_dir, workers=1):
    """Run the preserved pre-capacity builder through the full result consumer."""
    original = DSG._build_compact
    DSG._build_compact = DSG._build_compact_tuple
    try:
        return verify_trace_dir(trace_dir, workers=workers)
    finally:
        DSG._build_compact = original


def _capacity_compare_tuple_graph(compact):
    packed = DSG.from_compact(compact)
    original = DSG._build_compact
    DSG._build_compact = DSG._build_compact_tuple
    try:
        old = DSG.from_compact(compact)
    finally:
        DSG._build_compact = original
    assert packed.adj == old.adj
    assert list(packed.adj) == list(old.adj)
    assert packed._sccs() == old._sccs()
    assert packed.integrity == old.integrity
    assert packed.anomalies() == old.anomalies()
    return packed


def test_capacity_all_fixture_results_match_frozen_baseline():
    # Frozen by the parent using 947fd160a, never regenerated from this builder.
    frozen = {
        # Cicada entries computed with the 51f896352 verifier (production unchanged).
        'cicada_g1_genesis_readonly':
            '3561f40bc3d87782c41c2e4235952a6e27e9a069175712f81a91dab02d786ec9',
        'cicada_g2_write_skew':
            '2fbfe1f9c36624357bb50fb8b0bf6c22eb43c725e274676e6f36b0cc72adaf65',
        'g1_serial':
            '6ad7f8866e63185f8f9ee59a7f6fa3d181ba89a48804a46dbe461ab61787847a',
        'g2_rmw_chain':
            '992efbf4dce5edeace363ba442cf1daca8833ec70d06d280a83efd298df29831',
        'g3_readonly':
            '300c484d617666c8782f6abfb7fac30b32ac2f95d929e6ae11a26bd344ed8af9',
        'g4_rw_no_cycle':
            '1c548ac2f52f066f462e39447a18616f32f072e9db5d3aa98ec53f7e3a94235b',
        'g5_silo_real_prefix':
            '97d177435df8e15ce61f1b915f20fdd0af18702b4b15af530be7c47324d235c8',
        'g6_silo_serial_1thread':
            '1727ccdcc182df2aaefe656b0eed6f6d2f60a6812b4000a4361595a3cd88cc1a',
        'g7_mocc_minimal_2thread':
            'e42f5c0357452c141e732cb10a2c312075052e588566635e798854e5a1262703',
        'integrity_orphan':
            '43d3c1de1ca2dc8801a19edac8b796f2ee5ebf574ec0950e52cc20ddede383bb',
        'm1_commit_at_genesis':
            '3743cde434c76d687c93168f163d54162d51db24b1fa4537a256d2cd51c53b62',
        'm2_version_dup':
            'c35948493a15523a48353a52395f18ea64b92aa6e4ae588c642de01aa0e076d1',
        'm3_mocc_lock_coverage':
            'fd7fdd8c4752f51d3a7b1d9f796f3f1873a98da2cf52b9fca5e6723c28485149',
        'm4_mocc_permutation':
            'ec9206ae410a63a937ccf083ed987ec11122f444e343360f8716144a56595572',
        'p1_phantom_skew':
            'edc848576b586b0764b9e75d293c7451bb180c460e92984a4848c593d99f6a88',
        'r1_write_skew':
            '9ff85b22f8e09f611ddafd9e965713a36bc95153e673bab4795f99f41fa36135',
        'r2_lost_update':
            '56703559326954eb84a73c9c5d22f3c438b2de01bfae540a97f2a14162f9cd72',
        'r3_cycle3':
            '903278a3387fe59d12e57becd25115904c0e37b267d0fa550f49f11ed3614b2c',
        'r4_mixed_cycle':
            '37b07f44e83803b11791d52bca70f49de3ac20faf8aef55617880060bd615520',
        'r5_nonlatest_transitive':
            'a163e7037a18f82bd8771a3ddb0370ad22170901fd224200fb54e7c69ae802fa',
        'r6_epoch_version_order':
            '9db95da142e9a08f8b16a1ca1172d7f1ce8dc24745a73bb1e8691e32a69dc0bf',
        'r7_epoch_rw_successor':
            'd54af553d91e3abbbd94bf19777b51bda40ef85deb279a24aca84c16f3bce191',
        'r8_silo_broken_norw':
            'ef947c5498fb3abc313267e5c6fb5e8c33a927872bba17e39198b227b0019b88',
        'r9_dense_cycle4':
            'd4874d30526e3929ed73b1f9e936f0d8af4ef8d0c735038b9eea3824cfb925bd',
    }
    names = sorted(name for name in os.listdir(FIX)
                   if os.path.isdir(os.path.join(FIX, name))
                   and any(f.startswith("trace_") and f.endswith(".log")
                           for f in os.listdir(os.path.join(FIX, name))))
    assert names == sorted(frozen)
    for name in names:
        trace_dir = os.path.join(FIX, name)
        old = _capacity_tuple_result(trace_dir)
        for workers in (1, 2):
            result = verify_trace_dir(trace_dir, workers=workers)
            assert result == old, (name, workers, "all VerifyResult fields")
            doc = result_to_dict(result)
            doc["trace_dir"] = name
            blob = json.dumps(doc, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True).encode()
            assert hashlib.sha256(blob).hexdigest() == frozen[name], (name, workers)


def test_capacity_packed_versions_preserve_bounds_duplicates_and_notes():
    import shutil
    from orchestrator.verifier.parse import _parse_trace_dir_compact
    from orchestrator.verifier.dsg import _PackedVersions

    d = _tmp_trace(
        "C 0 0 1 0 0 2\nW 0 bb U 1 0\nW 0 aa U 1 0\nE 0\n"
        "C 1 0 1 0 0 3\nW 1 bb U 1 0\nW 1 bb U 1 0\nW 1 aa U 1 0\nE 1\n",
        "C 2 1 0 9 0 0\nE 2\n"
        "C 3 1 1 0 0 2\nW 3 aa U 1 0\nW 3 bb U 1 0\nE 3\n"
        "C 4 1 2 1 2 0\nR 4 bb 1 0\nR 4 aa 1 0\nE 4\n",
    )
    try:
        old = _capacity_tuple_result(d)
        for workers in (1, 2):
            result = verify_trace_dir(d, workers=workers)
            assert result == old
            assert result_to_dict(result) == result_to_dict(old)
            assert result.integrity.version_dups == 5
            assert result.integrity.genesis_commits == 4
            assert result.integrity.notes == [
                "txid 0 commits at or below genesis sentinel (1,0): (1, 0) (non-physical)",
                "txid 1 commits at or below genesis sentinel (1,0): (1, 0) (non-physical)",
                "version dup: key=bb ver=(1, 0) by txid 0 and 1",
                "version dup: key=bb ver=(1, 0) by txid 0 and 1",
                "version dup: key=aa ver=(1, 0) by txid 0 and 1",
                "txid 2 commits at or below genesis sentinel (1,0): (0, 9) (non-physical)",
                "txid 3 commits at or below genesis sentinel (1,0): (1, 0) (non-physical)",
                "version dup: key=aa ver=(1, 0) by txid 0 and 3",
                "version dup: key=bb ver=(1, 0) by txid 0 and 3",
            ]
        graph = _capacity_compare_tuple_graph(_parse_trace_dir_compact(d, workers=1))
        assert isinstance(graph.versions, _PackedVersions)
        assert tuple(graph.versions) == ("bb", "aa")
        assert graph.producer[("bb", (1, 0))] == 0
        assert graph.producer.get(("aa", (1, 0))) == 0
        assert ("aa", (1, 0)) in graph.producer
        assert ("aa", (1, -1)) not in graph.producer
        assert graph.versions.get("aa") == [(1, 0)]
        assert graph.versions.get("cc") is None
        assert graph.adj == {0: (4,)}
    finally:
        shutil.rmtree(d, ignore_errors=True)

    d = _tmp_trace("C 0 0 2 1 0 2\nW 0 aa U 2 1\nW 0 aa U 2 1\nE 0\n")
    try:
        result = verify_trace_dir(d, workers=1)
        assert result == _capacity_tuple_result(d)
        assert result.integrity.version_dups == 0
        assert result.integrity.notes == []
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # Each out-of-range writer triggers the untouched tuple builder before
    # genesis/dup diagnostics are emitted, even when valid writes precede it.
    for epoch, tid in ((2**32, 0), (0, -1), (-1, 0), (2, 2**32)):
        d = _tmp_trace(
            "C 0 0 1 0 0 1\nW 0 aa U 1 0\nE 0\n"
            f"C 1 0 {epoch} {tid} 1 1\nR 1 aa 1 0\n"
            f"W 1 aa U {epoch} {tid}\nE 1\n")
        try:
            old = _capacity_tuple_result(d)
            calls = []
            original = DSG._build_compact_tuple
            def record_tuple(graph):
                assert graph.integrity == Integrity()
                assert graph.producer == {} and graph.versions == {}
                calls.append(True)
                return original(graph)
            DSG._build_compact_tuple = record_tuple
            try:
                result = verify_trace_dir(d, workers=1)
            finally:
                DSG._build_compact_tuple = original
            assert calls == [True]
            assert result == old
            assert result_to_dict(result) == result_to_dict(old)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    # Signed-array boundary, epoch-first ordering, and out-of-range reads.
    # Too-large/negative tid reads still have a tuple-order rw successor.
    d = _tmp_trace(
        "C 0 0 2147483647 4294967295 0 1\nW 0 aa U 2147483647 4294967295\nE 0\n"
        "C 1 0 2147483648 0 0 1\nW 1 aa U 2147483648 0\nE 1\n"
        "C 2 0 4294967295 4294967295 0 1\nW 2 aa U 4294967295 4294967295\nE 2\n",
        "C 3 1 2 1 8 0\n"
        "R 3 aa 2147483647 4294967296\nR 3 aa 2147483648 -1\n"
        "R 3 aa -1 0\nR 3 aa 4294967296 0\n"
        "R 3 aa 4294967295 4294967295\nR 3 ff 1 0\n"
        "R 3 ff 0 0\nR 3 aa 0 9223372036854775807\nE 3\n")
    try:
        graph = _capacity_compare_tuple_graph(_parse_trace_dir_compact(d, workers=1))
        assert isinstance(graph.versions, _PackedVersions)
        assert graph.versions.versions_flat.typecode == "q"
        assert graph.versions.producers_flat.typecode == "q"
        assert graph.versions.key_offsets.typecode == "Q"
        assert all(a.typecode == "i" for a in graph.versions.token_to_key)
        assert graph.versions["aa"] == [
            (2147483647, 4294967295), (2147483648, 0),
            (4294967295, 4294967295),
        ]
        assert graph.integrity.orphan_reads == 6
        assert {u: set(vs) for u, vs in graph.adj.items()} == {
            3: {0, 1}, 2: {3}, 0: {1}, 1: {2},
        }
        old = _capacity_tuple_result(d)
        for workers in (1, 2):
            result = verify_trace_dir(d, workers=workers)
            assert result == old
            assert result_to_dict(result) == result_to_dict(old)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_capacity_last_wins_drops_old_writer_edges_and_orphans_reads():
    import shutil
    from orchestrator.verifier.parse import _parse_trace_dir_compact
    d = _tmp_trace(
        "C 0 0 2 1 0 1\nW 0 aa U 2 1\nE 0\n"
        "C 1 0 2 2 1 1\nR 1 aa 2 1\nW 1 aa U 2 2\nE 1\n",
        "C 0 1 3 1 0 1\nW 0 bb U 3 1\nE 0\n"
        "C 2 1 3 2 1 0\nR 2 bb 3 1\nE 2\n")
    try:
        old = _capacity_tuple_result(d)
        for workers in (1, 2):
            result = verify_trace_dir(d, workers=workers)
            assert result == old
            assert result_to_dict(result) == result_to_dict(old)
            assert (result.n_txns, result.n_reads, result.n_writes,
                    result.n_keys, result.n_edges, result.total_cycles) == (3, 2, 2, 2, 1, 0)
            assert result.integrity == Integrity(
                orphan_reads=1, dup_txids=1,
                notes=["duplicate txid C-lines: 0 ..."],
                proof_surfaces=ProofSurfaceAssessment(
                    protocol="silo", lock_coverage="evidence-present",
                    permutation="evidence-present", write_intent="evidence-absent"))
            assert result.verdict == "indeterminate"
        graph = _capacity_compare_tuple_graph(_parse_trace_dir_compact(d, workers=1))
        assert graph.adj == {0: (2,)}
        assert tuple(graph.versions) == ("bb", "aa")
        assert ("aa", (2, 1)) not in graph.producer
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_capacity_edge_worker_reads_only_arrays():
    import shutil
    from array import array
    from orchestrator.verifier.parse import _parse_trace_dir_compact
    from orchestrator.verifier.dsg import (
        _EdgeWorkerState, _EdgeTask, _edge_candidates_for_task,
        _PackedVersions, _PackedProducer,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("edge worker read a parent Mapping/key object")

    class ArrayVersions(_PackedVersions):
        __getitem__ = get = __contains__ = __iter__ = forbidden

    class ArrayProducer(_PackedProducer):
        __getitem__ = get = __contains__ = __iter__ = forbidden

    class NoKeys:
        __getitem__ = __iter__ = forbidden

    d = _ordinal_witness_trace()
    try:
        compact = _parse_trace_dir_compact(d, workers=1)
        graph = DSG.from_compact(compact)
        original = graph.versions
        guarded = ArrayVersions(
            NoKeys(), original.token_to_key, original.key_offsets,
            original.versions_flat, original.producers_flat)
        state = _EdgeWorkerState(compact, ArrayProducer(guarded), guarded, NoKeys())
        outcome = _edge_candidates_for_task(_EdgeTask(0, "read", 0, 17), state)
        assert outcome.run_src == array("q", [8, 16, 1])
        assert outcome.run_offsets == array("q", [0, 1, 2, 4])
        assert outcome.run_dst == array("q", [1, 1, 8, 16])
        assert outcome.orphan_reads == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)

    d = _tmp_trace(
        "C 0 0 2 1 0 2\nW 0 bb U 2 1\nW 0 aa U 2 1\nE 0\n"
        "C 1 0 3 1 0 1\nW 1 aa U 3 1\nE 1\n",
        "C 2 1 4 1 0 2\nW 2 bb U 4 1\nW 2 aa U 4 1\nE 2\n")
    try:
        compact = _parse_trace_dir_compact(d, workers=1)
        graph = DSG.from_compact(compact)
        original = graph.versions
        guarded = ArrayVersions(
            NoKeys(), original.token_to_key, original.key_offsets,
            original.versions_flat, original.producers_flat)
        state = _EdgeWorkerState(compact, ArrayProducer(guarded), guarded, NoKeys())
        outcome = _edge_candidates_for_task(_EdgeTask(1, "ww", 0, 2), state)
        assert outcome.run_src == array("q", [0, 1])
        assert outcome.run_offsets == array("q", [0, 2, 3])
        assert outcome.run_dst == array("q", [2, 1, 2])
        assert outcome.orphan_reads == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_capacity_workers_1_and_16_match():
    import shutil
    from orchestrator.verifier.parse import _parse_trace_dir_compact
    # Sixteen real files, with wr/rw/ww and the collision-sensitive two SCCs.
    source = _serial_parent_optimization_trace()
    try:
        files = ["" for _ in range(16)]
        rank = 0
        for name in sorted(os.listdir(source)):
            with open(os.path.join(source, name)) as stream:
                frame = []
                for line in stream:
                    frame.append(line)
                    if line.startswith("E "):
                        files[rank % 16] += "".join(frame)
                        rank += 1
                        frame = []
        d = _tmp_trace(*files)
        try:
            old = _capacity_tuple_result(d)
            _capacity_compare_tuple_graph(_parse_trace_dir_compact(d, workers=1))
            for workers in (1, 2, 16, None):
                result = verify_trace_dir(d, workers=workers)
                assert result == old
                assert result_to_dict(result) == result_to_dict(old)
                assert result.n_edges == 9
                assert [a.cycle for a in result.anomalies] == [[17, 24], [0, 8]]
        finally:
            shutil.rmtree(d, ignore_errors=True)
    finally:
        shutil.rmtree(source, ignore_errors=True)


def _capacity_broken_pool_child(kind):
    import importlib
    import shutil
    import signal
    import time

    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    dsg_module = importlib.import_module("orchestrator.verifier.dsg")
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    module = dsg_module if kind == "edge" else parse_module
    name = "_edge_candidates_for_task" if kind == "edge" else "_parse_file_worker"
    original = getattr(module, name)
    parent_pid = os.getpid()
    d = _ordinal_witness_trace()
    # Four files permit four parse workers as well as multiple edge tasks.
    with open(os.path.join(d, "trace_3.log"), "w"):
        pass
    # Results must exceed the result pipe capacity: after a worker exits the
    # manager stops draining that pipe. Tiny results can finish and consume
    # shutdown sentinels even without SIGKILL, hiding the production deadlock.
    for file_index in range(4):
        with open(os.path.join(d, f"trace_{file_index}.log"), "a") as fh:
            for txid in range(17 + file_index, 17 + 16384, 4):
                epoch, tid = (1, 0) if txid == 17 else (3, txid)
                fh.write(
                    f"C {txid} {file_index} 3 {txid + 1} 1 1\n"
                    f"R {txid} ee {epoch} {tid}\n"
                    f"W {txid} ee U 3 {txid + 1}\nE {txid}\n")
    marker = os.path.join(d, "exited-worker")

    def fail_worker(task, *args):
        if os.getpid() != parent_pid:
            assert signal.getsignal(signal.SIGTERM) == signal.SIG_IGN
            index = task.task_index if kind == "edge" else task[0]
            if index == 0:
                time.sleep(0.3)
                with open(marker, "w") as fh:
                    fh.write(str(os.getpid()))
                os._exit(3)
            time.sleep(5)
        return original(task, *args)

    # The parse function itself is submitted and must resolve by module name.
    fail_worker.__module__ = module.__name__
    fail_worker.__name__ = fail_worker.__qualname__ = name
    try:
        baseline = verify_trace_dir(d, workers=1)
        setattr(module, name, fail_worker)
        started = time.monotonic()
        recovered = verify_trace_dir(d, workers=4)
        assert time.monotonic() - started < 60
        assert os.path.exists(marker), "worker exit was not exercised"
        assert result_to_dict(recovered) == result_to_dict(baseline)
        pids = (dsg_module._LAST_DSG_WORKER_PIDS if kind == "edge"
                else parse_module._LAST_PARSE_WORKER_PIDS)
        assert pids == {parent_pid}, pids
        with open(f"/proc/{parent_pid}/task/{parent_pid}/children") as fh:
            assert not fh.read().strip(), "pool left live or unreaped children"
    finally:
        setattr(module, name, original)
        shutil.rmtree(d, ignore_errors=True)


def _capacity_run_broken_pool_child(kind):
    import signal
    # Kill the entire isolated group even when the pre-fix pool hangs.  Killing
    # only subprocess.run's child would leave its SIGTERM-ignoring workers.
    with tempfile.TemporaryDirectory(prefix="verifier-pool-child-") as d:
        pid_path = os.path.join(d, "pid")
        script = (
            "import os, runpy, sys\n"
            "with open(sys.argv[2], 'w') as f: f.write(str(os.getpid()))\n"
            "sys.path.insert(0, os.path.dirname(sys.argv[1]))\n"
            "tests = runpy.run_path(sys.argv[1])\n"
            "tests['_capacity_broken_pool_child'](sys.argv[3])\n"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-c", script, os.path.abspath(__file__),
                 pid_path, kind],
                timeout=120, start_new_session=True, capture_output=True,
                text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            )
            assert result.returncode == 0, result.stdout + result.stderr
        finally:
            if os.path.exists(pid_path):
                with open(pid_path) as fh:
                    pid = int(fh.read())
                try:
                    os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def test_capacity_broken_pool_terminates_workers_and_falls_back():
    _capacity_run_broken_pool_child("edge")


def test_capacity_parse_broken_pool_terminates_workers():
    _capacity_run_broken_pool_child("parse")


def test_capacity_partial_outcomes_are_released_before_full_fallback():
    """Partial arrays must die before the first sequential task, without GC."""
    import concurrent.futures
    import importlib
    import shutil
    import weakref
    from unittest.mock import patch

    dsg_module = importlib.import_module("orchestrator.verifier.dsg")
    parse_module = importlib.import_module("orchestrator.verifier.parse")
    d = _ordinal_witness_trace()
    try:
        for kind in ("edge", "parse"):
            for failure in ("worker", "incomplete", "submit"):
                refs = []
                sequential_tasks = []
                original = (dsg_module._edge_candidates_for_task if kind == "edge"
                            else parse_module._parse_file_worker)

                class PartialPool:
                    def __init__(self, **kwargs):
                        self.state = kwargs.get("initargs", (None,))[0]
                        self.count = 0

                    def submit(self, fn, task):
                        self.count += 1
                        if self.count > 1 and failure == "submit":
                            raise OSError("submit failure sentinel")
                        future = concurrent.futures.Future()
                        if self.count == 1 or failure == "incomplete":
                            outcome = (original(task, self.state) if kind == "edge"
                                       else original(task))
                            # Duplicate indices exercise completeness rejection.
                            if failure == "incomplete":
                                outcome = replace(outcome, **{
                                    "task_index" if kind == "edge" else "path_index": 0,
                                })
                            refs.append(weakref.ref(
                                outcome.run_dst if kind == "edge"
                                else outcome.txn_commit_epoch))
                            future.set_result(outcome)
                        else:
                            future.set_exception(RuntimeError("worker failure sentinel"))
                        return future

                    def shutdown(self, **kwargs):
                        pass

                def sequential(task, *args):
                    assert refs, "no partial outcome was injected"
                    assert all(ref() is None for ref in refs), (
                        kind, failure, "partial arrays still live at fallback")
                    sequential_tasks.append(task)
                    return original(task, *args)

                module = dsg_module if kind == "edge" else parse_module
                name = ("_edge_candidates_for_task" if kind == "edge"
                        else "_parse_file_worker")
                # Parse the edge test input first, outside the fake pool.
                compact = parse_module._parse_trace_dir_compact(d, workers=1)
                expected_graph = DSG.from_compact(compact)
                compact = replace(compact, worker_count=4)
                with patch.object(concurrent.futures, "ProcessPoolExecutor", PartialPool), \
                        patch.object(concurrent.futures, "as_completed", iter), \
                        patch.object(module, name, sequential):
                    if kind == "edge":
                        graph = DSG.from_compact(compact)
                        assert graph.adj == expected_graph.adj
                        assert graph.anomalies() == expected_graph.anomalies()
                    else:
                        parsed = parse_module._parse_trace_dir_compact(d, workers=4)
                        assert list(parsed.winner_txid) == list(compact.winner_txid)
                assert len(sequential_tasks) > 1, "full fallback was not exercised"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---- TPC-C v3: synthetic wire fixtures, no pytest-only dependencies ----

def _v3_frame(txid, reads=(), writes=(), *, commit=None, tx_type=1, tail=""):
    epoch, tid = commit or (2, txid + 1)
    return (
        f"C {txid} 0 {epoch} {tid} {len(reads)} {len(writes)} 0 0 {tx_type}\n"
        + "".join(f"R {txid} {table} {key} {ve} {vt}\n"
                  for table, key, ve, vt in reads)
        + "".join(f"W {txid} {table} {key} {op} {epoch} {tid}\n"
                  for table, key, op in writes)
        + tail + f"E {txid}\n"
    )


def _v3_cycle_files(epoch=2):
    return (
        _v3_frame(0, [(0, "aa", 1, 0)], [(9, "aa", "U")],
                  commit=(epoch, 1), tx_type=1),
        _v3_frame(1, [(9, "aa", 1, 0)], [(0, "aa", "U")],
                  commit=(epoch, 2), tx_type=2),
    )


def _v3_paths(d, *, expect_compact=True, expect_packed=True, **kwargs):
    """Compare actual parsers/builders through existing outer seams, restoring all."""
    def edges(graph):
        return {(u, v) for u, destinations in graph.adj.items() for v in destinations}

    import orchestrator.verifier.core as core
    import orchestrator.verifier.parse as parser
    from orchestrator.verifier.dsg import _PackedVersions
    original_parse = core._parse_trace_dir_compact
    original_build = DSG._build_compact
    tuple_graphs = []

    def tuple_build(graph):
        tuple_graphs.append(graph)
        DSG._build_compact_tuple(graph)

    results = []
    try:
        for mode in ("legacy", "packed", "tuple"):
            for workers in ((1,) if mode == "legacy" else (1, 2)):
                core._parse_trace_dir_compact = (
                    (lambda path, **kw: parser._finish_legacy_parse(parser._trace_paths(path)))
                    if mode == "legacy" else original_parse)
                DSG._build_compact = tuple_build if mode == "tuple" else original_build
                parsed = core._parse_trace_dir_compact(d, workers=workers)
                if mode != "legacy" and expect_compact:
                    assert isinstance(parsed, parser._CompactTrace), (
                        f"{mode} workers={workers}: expected compact parser result")
                graph = (DSG(parsed.txns) if isinstance(parsed, parser._LegacyTrace)
                         else DSG.from_compact(parsed))
                if not isinstance(parsed, parser._LegacyTrace):
                    if mode == "packed" and expect_packed:
                        assert isinstance(graph.versions, _PackedVersions)
                    if mode == "tuple":
                        assert any(built is graph for built in tuple_graphs)
                        assert isinstance(graph.versions, dict)
                result = verify_trace_dir(d, workers=workers, **kwargs)
                results.append((graph, result))
        reference_graph, reference_result = results[0]
        for graph, result in results[1:]:
            assert graph.integrity == reference_graph.integrity
            assert edges(graph) == edges(reference_graph)
            assert list(graph.versions.items()) == list(reference_graph.versions.items())
            assert dict(graph.producer) == dict(reference_graph.producer)
            assert [graph._txn_for_id(txid) for txid in graph.adj] == [
                reference_graph._txn_for_id(txid) for txid in graph.adj]
            assert result == reference_result
            assert core.result_to_dict_v3(result) == core.result_to_dict_v3(reference_result)
        txns, _ = parse_trace_dir(d, workers=1)
        graph = DSG(txns)
        assert edges(graph) == edges(reference_graph)
        assert graph.integrity == reference_graph.integrity
        return results
    finally:
        core._parse_trace_dir_compact = original_parse
        DSG._build_compact = original_build


def _v3_rejected(*files, contains="", legacy=False, workers=1):
    import shutil
    import orchestrator.verifier.parse as parser
    d = _tmp_trace(*files)
    try:
        try:
            if legacy:
                parser._finish_legacy_parse(parser._trace_paths(d))
            else:
                parse_trace_dir(d, workers=workers)
        except ParseError as error:
            assert contains in str(error), str(error)
            return str(error).replace(d, "TRACE")
        raise AssertionError("malformed v3 trace was accepted")
    finally:
        shutil.rmtree(d)


def test_v3_table_identity_separates_edges():
    import shutil
    from orchestrator.verifier.parse import _parse_trace_dir_compact, _object_at
    for left, right in ((0, 9), (5, 6)):
        d = _tmp_trace(
            _v3_frame(0, [(left, "aa", 1, 0)], [(right, "aa", "I")], commit=(2, 2)),
            _v3_frame(1, writes=[(left, "aa", "D")], commit=(2, 1), tx_type=2))
        try:
            columns = _parse_trace_dir_compact(d, workers=1).files[0]
            assert columns.read_key_id[0] != columns.write_key_id[0]
            assert _object_at(columns, columns.read_key_id[0]) == (left, "aa")
            assert _object_at(columns, columns.write_key_id[0]) == (right, "aa")
            for graph, result in _v3_paths(d):
                assert {(u, v) for u, vs in graph.adj.items() for v in vs} == {(0, 1)}
                assert result.n_keys == 2
                assert result.integrity.version_dups == 0
                assert graph._txn_for_id(0).writes[0].op == "I"
                assert graph._txn_for_id(1).writes[0].op == "D"
        finally:
            shutil.rmtree(d)


def test_v3_serial_tables_types_and_ops():
    import shutil
    files = []
    for table in range(11):
        files.append(_v3_frame(table, writes=[(table, "aa", ("U", "I", "D")[table % 3])],
                               tx_type=table % 5 + 1))
    files.append(_v3_frame(11, [(table, "aa", 2, table + 1) for table in range(11)]))
    d = _tmp_trace(*files)
    try:
        for graph, result in _v3_paths(d):
            assert result.serializable and result.n_keys == 11 and result.n_edges == 11
            assert result.integrity.existence_violations == 3 and not result.certified
            for table in range(11):
                txn = graph._txn_for_id(table)
                assert txn.tx_type == table % 5 + 1 and txn.schema == 3
                assert txn.writes[0].table == table
    finally:
        shutil.rmtree(d)


def test_v3_cycle_reports_tables_and_tx_types():
    import shutil
    from orchestrator.verifier.core import result_to_dict_v3
    from orchestrator.verifier.model import AnomalyV3, EdgeReasonV3
    d = _tmp_trace(*_v3_cycle_files())
    try:
        for graph, result in _v3_paths(d):
            assert result.verdict == "non-serializable" and not result.certified
            anomaly = result.anomalies[0]
            assert isinstance(anomaly, AnomalyV3)
            assert dict(zip(anomaly.cycle, anomaly.cycle_tx_types)) == {0: 1, 1: 2}
            assert {(e.src, e.dst, r.etype, r.table, r.key)
                    for e in anomaly.edges for r in e.reasons} == {
                        (0, 1, "rw", 0, "aa"), (1, 0, "rw", 9, "aa")}
            assert all(isinstance(r, EdgeReasonV3) for e in anomaly.edges for r in e.reasons)
            old = json.dumps(result_to_dict(result), sort_keys=True)
            projected = result_to_dict_v3(result)["anomalies"][0]
            assert projected["cycle_nodes"] == [
                {"txid": txid, "tx_type": {0: 1, 1: 2}[txid]} for txid in anomaly.cycle]
            assert {(e["from"], r["table"], r["key"]) for e in projected["edges"]
                    for r in e["reasons"]} == {(0, 0, "aa"), (1, 9, "aa")}
            assert json.dumps(result_to_dict(result), sort_keys=True) == old
        limited = verify_trace_dir(d, max_report=0)
        assert limited.total_cycles == 1 and limited.verdict == "non-serializable"
        assert result_to_dict_v3(limited)["anomalies"] == []
        assert len(verify_trace_dir(d, max_report=1).anomalies) == 1
    finally:
        shutil.rmtree(d)


def test_v3_reasons_preserve_ww_wr_rw_identity():
    import shutil
    from orchestrator.verifier.model import EdgeReasonV3
    d = _tmp_trace(
        _v3_frame(0, [(9, "aa", 1, 0)], [(0, "aa", "U"), (9, "aa", "U")]),
        _v3_frame(1, [(0, "aa", 2, 1), (9, "aa", 1, 0)],
                  [(0, "aa", "U"), (9, "aa", "U")]))
    try:
        for graph, _ in _v3_paths(d):
            assert graph._reasons(0, 1) == [
                EdgeReasonV3(WW, "aa", (2, 1), (2, 2), table=0),
                EdgeReasonV3(WW, "aa", (2, 1), (2, 2), table=9),
                EdgeReasonV3(WR, "aa", (2, 1), None, table=0)]
            assert graph._reasons(1, 0) == [
                EdgeReasonV3(RW, "aa", (1, 0), (2, 1), table=9)]
    finally:
        shutil.rmtree(d)


def test_v3_packed_mapping_and_read_bounds():
    import shutil
    d = _tmp_trace(
        _v3_frame(0, writes=[(9, "aa", "U")]),
        _v3_frame(1, writes=[(0, "aa", "U")]),
        _v3_frame(2, [(0, "aa", 2, 2), (9, "aa", 2, 1), (0, "aa", 2, 1),
                      (0, "aa", 2, -1), (0, "aa", 2, 2**32)]))
    try:
        for graph, result in _v3_paths(d):
            assert list(graph.versions) == [(9, "aa"), (0, "aa")]
            assert graph.versions[(0, "aa")] == [(2, 2)]
            assert graph.producer[((9, "aa"), (2, 1))] == 0
            assert graph.producer.get(((0, "aa"), (2, 1))) is None
            assert result.integrity.orphan_reads == 3
            assert {(u, v) for u, vs in graph.adj.items() for v in vs} == {(0, 2), (1, 2), (2, 1)}
            for mapping, key in ((graph.versions, (5, "aa")),
                                 (graph.producer, ((5, "aa"), (2, 1)))):
                assert mapping.get(key) is None
                try:
                    mapping[key]
                except KeyError:
                    pass
                else:
                    raise AssertionError("missing object must raise KeyError")
    finally:
        shutil.rmtree(d)


def test_v3_same_version_table_duplicates_and_notes():
    import shutil
    for table in (0, 9):
        d = _tmp_trace(_v3_frame(0, writes=[(0, "aa", "U")]),
                       _v3_frame(1, writes=[(table, "aa", "U")], commit=(2, 1)))
        try:
            for graph, result in _v3_paths(d):
                assert result.integrity.version_dups == (1 if table == 0 else 0)
                assert graph.producer[((0, "aa"), (2, 1))] == 0
                if table == 0:
                    assert "version dup: table=0 key=aa ver=(2, 1) by txid 0 and 1" in result.integrity.notes
        finally:
            shutil.rmtree(d)


def test_v3_tuple_and_legacy_fallback_preserve_metadata():
    import shutil
    import orchestrator.verifier.parse as parser
    from orchestrator.verifier.dsg import _PackedVersions
    for epoch in (2**32, 2**63):
        files = _v3_cycle_files(epoch)
        d = _tmp_trace(files[0].replace("aa U", "aa I"), files[1])
        try:
            parsed = parser._parse_trace_dir_compact(d, workers=2)
            assert isinstance(parsed, parser._LegacyTrace) == (epoch == 2**63)
            for graph, result in _v3_paths(
                    d, expect_compact=(epoch != 2**63), expect_packed=False):
                assert not isinstance(graph.versions, _PackedVersions)
                assert result.verdict == "non-serializable"
                assert set(result.anomalies[0].cycle_tx_types) == {1, 2}
                assert set(graph.versions) == {(0, "aa"), (9, "aa")}
                assert result.integrity.existence_violations == 1
        finally:
            shutil.rmtree(d)


def test_v3_last_winner_tx_type_in_cycle():
    import shutil
    first, second = _v3_cycle_files()
    d = _tmp_trace(_v3_frame(0, tx_type=5), second, first)
    try:
        for _, result in _v3_paths(d):
            assert result.integrity.dup_txids == 1
            a = result.anomalies[0]
            assert dict(zip(a.cycle, a.cycle_tx_types)) == {0: 1, 1: 2}
    finally:
        shutil.rmtree(d)


def test_v3_rejects_mixed_schema_in_one_file():
    v2, v3 = "C 0 0 2 1 0 0\nE 0\n", _v3_frame(1)
    for a, b in ((v2, v3), (v3, v2)):
        for legacy in (True, False):
            assert "TRACE/trace_0.log:3: mixed trace schemas" == _v3_rejected(a + b, legacy=legacy)


def test_v3_rejects_mixed_schema_across_files():
    v2 = "C 0 0 2 1 0 0\nE 0\n"
    for v3 in (_v3_frame(0), _v3_frame(0, commit=(2**63, 1))):
        for a, b in ((v2, v3), (v3, v2)):
            for legacy in (False, True):
                for workers in ((1,) if legacy else (1, 2)):
                    message = _v3_rejected(a, "P unknown\nA abort\n", "", b,
                                           legacy=legacy, workers=workers, contains="mixed trace schemas")
                    assert "trace_0.log" in message and "trace_3.log" in message


def test_v3_schema_failure_precedes_cross_file_mixture():
    for legacy in (False, True):
        for workers in ((1,) if legacy else (1, 2)):
            message = _v3_rejected("C 0 0 2 1 0 0\nE 0\n", _v3_frame(1), "Z bad\n",
                                   legacy=legacy, workers=workers, contains="trace_2.log:1:")
            assert "unknown record tag" in message
            _v3_rejected(_v3_frame(0), "C 1 0 2 2 0 0\nE 1\nZ bad\n",
                         legacy=legacy, workers=workers, contains="trace_1.log:3:")


def test_v3_rejects_invalid_table_and_tx_type():
    for table in ("11", "-1", "01", "+1", "-0", "x", "1.0", "0x1", "1_0", "1 0"):
        for tag, suffix in (("R", "aa 1 0"), ("W", "aa U 2 1"),
                            ("X", "aa unknown"), ("I", "aa unknown")):
            frame = (_v3_frame(0, reads=[(table, "aa", 1, 0)]) if tag == "R" else
                     _v3_frame(0, writes=[(table, "aa", "U")]) if tag == "W" else
                     _v3_frame(0, tail=f"{tag} 0 {table} {suffix}\n"))
            _v3_rejected(frame,
                         contains="expected exactly" if table == "1 0" else "table")
    for tx_type in ("0", "6", "01", "+1", "-0", "x", "1.0", "1_0"):
        _v3_rejected(_v3_frame(0, tx_type=tx_type), contains="tx_type")


def test_v3_rejects_scan_counts_tags_ops_and_record_shapes():
    for offset in (7, 8):
        for value in ("1", "01", "+0", "-0", "x", "1_0"):
            fields = _v3_frame(0).splitlines()[0].split()
            fields[offset] = value
            _v3_rejected(" ".join(fields) + "\nE 0\n",
                         contains="段 2 未対応" if value == "1" else "canonical")
    for op in ("Z", "u", "INSERT", "DELETE", "UPDATE"):
        _v3_rejected(_v3_frame(0, writes=[(0, "aa", op)]), contains="invalid v3 W op")
    for tag in ("S", "Q"):
        _v3_rejected(_v3_frame(0, tail=f"{tag} 0 0 aa\n"), contains="unknown record tag")
    for line in ("R 0 aa 1 0", "W 0 aa U 2 1", "X 0 aa reason", "I 0 aa reason"):
        _v3_rejected(_v3_frame(0, tail=line + "\n"), contains="expected exactly")
        parts = line.split()
        parts.insert(2, "0")
        _v3_rejected("C 0 0 2 1 0 0\n" + " ".join(parts) + "\nE 0\n", contains="malformed line")
    for fields in ("C 0 0 2 1 0", "C 0 0 2 1 0 0 0 0", "C 0 0 2 1 0 0 0 0 1 0"):
        _v3_rejected(fields + "\n", contains="expected exactly 7 fields")


def test_v3_x_i_keep_table_and_make_indeterminate():
    import shutil
    for tag, attribute in (("X", "lock_coverage_violations"), ("I", "write_intent_violations")):
        d = _tmp_trace(_v3_frame(0, tail=f"{tag} 0 5 aa unknown-reason\n"))
        try:
            _, issues = parse_trace_dir(d, workers=1)
            assert getattr(issues, attribute) == [(0, (5, "aa"), "unknown-reason")]
            for _, result in _v3_paths(d, expected_commits=1):
                assert getattr(result.integrity, attribute) == 1
                assert result.verdict == "indeterminate" and result.serializable
                assert result.integrity.framing_violations == 0
                assert any("txn0 table=5 key=aa (unknown-reason)" in n for n in result.integrity.notes)
        finally:
            shutil.rmtree(d)


def test_v3_existence_violations_and_v2_control():
    import shutil
    from orchestrator.verifier.core import verify_trace_dir_with_capability
    import commit_receipt_support as receipt_support
    for op, read_version in (("U", (2, 1)), ("I", (1, 0)), ("D", (2, 1))):
        frames = (_v3_frame(0, writes=[(5, "aa", op)]),
                  _v3_frame(1, [(5, "aa", *read_version)], tx_type=2))
        d = _tmp_trace(*frames)
        try:
            for _, result in _v3_paths(d, expected_commits=2):
                ig = result.integrity
                assert result.certified == (op == "U")
                assert result.verdict == ("serializable" if op == "U" else "indeterminate")
                assert ig.existence_violations == (0 if op == "U" else 1)
                assert ig.proof_surfaces.certification_gate_satisfied()
                assert ig.expected_commits == ig.observed_commits == 2
                assert ig.orphan_reads == ig.framing_violations == 0
                assert len(ig.notes) == (0 if op == "U" else 1)
                if op != "U":
                    assert ig.existence_violation_details[0].kind == (
                        "read-unborn-genesis" if op == "I" else "read-deleted-version")
                assert replace(ig, existence_violations=0).clean()
            genome, evidence, admission = receipt_support._proof_build_binding("baseline")
            result, capability = verify_trace_dir_with_capability(
                d, expected_commits=2, workers=1, genome=genome, source_evidence=evidence,
                build_admission=admission, receipt_sink_kind="test",
                receipt_lock_identity_sha256="0" * 64, receipt_variant="baseline",
                receipt_operation_identity="v3-existence", receipt_workload_tag="unit")
            assert result.certified == capability._certified == (op == "U")
            assert capability._verdict == ("serializable" if op == "U" else "indeterminate")
        finally:
            shutil.rmtree(d)
        v2 = []
        for frame in frames:
            lines = []
            for line in frame.splitlines():
                f = line.split()
                if f[0] == "C":
                    f = f[:7]
                elif f[0] in ("R", "W"):
                    f = f[:2] + f[3:]
                lines.append(" ".join(f))
            v2.append("\n".join(lines) + "\n")
        d = _tmp_trace(*v2)
        try:
            result = verify_trace_dir(d, expected_commits=2)
            assert result.certified
            assert result.integrity.existence_violation_details is None
            assert result.integrity.notes == []
        finally:
            shutil.rmtree(d)


def test_v3_framing_and_neutral_files():
    import shutil
    frame = _v3_frame(0)
    cases = ((frame.replace(" 0 0 0 0 1", " 1 0 0 0 1"), ["count-mismatch"]),
             (frame.replace("E 0\n", ""), ["missing-end"]),
             (frame + "E 0\n", ["duplicate-end"]),
             (frame.replace("E 0\n", "") + _v3_frame(1), ["missing-end"]))
    for text, kinds in cases:
        d = _tmp_trace(text, "", "A abort\n")
        try:
            for _, result in _v3_paths(d):
                assert [v.kind for v in result.integrity.framing_violation_details] == kinds
                assert result.verdict == "indeterminate"
        finally:
            shutil.rmtree(d)
    d = _tmp_trace("", "P unknown\nA abort\n")
    try:
        assert verify_trace_dir(d).verdict == "indeterminate"
        assert verify_trace_dir(d).integrity.existence_violations == 0
    finally:
        shutil.rmtree(d)


def test_v3_parallel_processes_and_pool_failure_fallback():
    import shutil
    import orchestrator.verifier.parse as parser
    import orchestrator.verifier.dsg as dsg_module
    from orchestrator.verifier.core import result_to_dict_v3
    files = _v3_cycle_files()
    d = _tmp_trace(files[0].replace("aa U", "aa I"), files[1])
    parent_pid = os.getpid()
    original_build = DSG._build_compact
    try:
        expected = verify_trace_dir(d, workers=1)
        assert expected.integrity.existence_violations == 1
        assert verify_trace_dir(d, workers=2) == expected
        assert parser._LAST_PARSE_WORKER_PIDS and parent_pid not in parser._LAST_PARSE_WORKER_PIDS
        assert dsg_module._LAST_DSG_WORKER_PIDS and parent_pid not in dsg_module._LAST_DSG_WORKER_PIDS
        for kind in ("parse", "edge"):
            module = parser if kind == "parse" else dsg_module
            name = "_parse_file_worker" if kind == "parse" else "_edge_candidates_for_task"
            original = getattr(module, name)
            marker = os.path.join(d, "exited-worker")

            def fail_worker(task, *args):
                index = task[0] if kind == "parse" else task.task_index
                if os.getpid() != parent_pid and index == 0:
                    with open(marker, "w") as fh:
                        fh.write(str(os.getpid()))
                    os._exit(71)
                return original(task, *args)

            # The submitted parse worker must be resolvable by module/name.
            fail_worker.__module__ = module.__name__
            fail_worker.__name__ = fail_worker.__qualname__ = name
            setattr(module, name, fail_worker)
            try:
                for mode in ("packed", "tuple"):
                    DSG._build_compact = (original_build if mode == "packed"
                                          else DSG._build_compact_tuple)
                    if os.path.exists(marker):
                        os.unlink(marker)
                    recovered = verify_trace_dir(d, workers=2)
                    # Observe this call before any helper can overwrite the PID sets.
                    pids = (parser._LAST_PARSE_WORKER_PIDS if kind == "parse"
                            else dsg_module._LAST_DSG_WORKER_PIDS)
                    assert pids == frozenset({parent_pid}), pids
                    with open(marker) as fh:
                        assert int(fh.read()) != parent_pid, "worker exit was not exercised"
                    os.unlink(marker)
                    assert recovered == expected
                    assert result_to_dict_v3(recovered) == result_to_dict_v3(expected)
                DSG._build_compact = original_build
                for _, result in _v3_paths(d):
                    assert result == expected
            finally:
                setattr(module, name, original)
                DSG._build_compact = original_build
    finally:
        shutil.rmtree(d)


def test_v3_output_validation_and_v2_projection():
    import shutil
    from orchestrator.verifier.core import result_to_dict_v3
    for name in ("g1_serial", "r2_lost_update"):
        # v2 JSON/repr and full fixture hashes are additionally frozen above.
        d = os.path.join(FIX, name)
        result = verify_trace_dir(d)
        assert json.dumps(result_to_dict_v3(result)) == json.dumps(result_to_dict(result))
    d = _tmp_trace(*_v3_cycle_files())
    try:
        result = verify_trace_dir(d)
        anomaly = result.anomalies[0]
        invalid = [replace(anomaly, cycle_tx_types=()),
                   replace(anomaly, edges=[CycleEdge(0, 1, [EdgeReason(RW, "aa")])])]
        for a in invalid:
            try:
                result_to_dict_v3(replace(result, anomalies=[a]))
            except ValueError:
                pass
            else:
                raise AssertionError("malformed v3 witness projected silently")
    finally:
        shutil.rmtree(d)


# Existence tests exercise the stage-1 contract, not native emitter behavior.
def _existence_result(files, kinds=(), *, paths=False):
    import shutil
    d = _tmp_trace(*files)
    try:
        results = ([r for _, r in _v3_paths(d, expected_commits=len(files))]
                   if paths else [verify_trace_dir(d, expected_commits=len(files))])
        for result in results:
            ig = result.integrity
            assert result.serializable and result.total_cycles == 0
            assert ig.orphan_reads == ig.framing_violations == 0
            assert ig.expected_commits == ig.observed_commits == len(files)
            assert ig.proof_surfaces.certification_gate_satisfied()
            assert replace(ig, existence_violations=0).clean()
            assert ig.existence_violations == len(kinds)
            assert [v.kind for v in ig.existence_violation_details] == list(kinds)
            assert result.certified == (not kinds)
            assert result.verdict == ("indeterminate" if kinds else "serializable")
        return results[0]
    finally:
        shutil.rmtree(d)


def test_v3_existence_negative_pairs():
    from orchestrator.verifier.model import ExistenceViolation
    # Each repair changes exactly one R or W line; framing counts stay intact.
    cases = [
        ((_v3_frame(0, writes=[(5, "aa", "I")]),
          _v3_frame(1, [(5, "aa", 1, 0)])),
         1, "aa 1 0", "aa 2 1", "read-unborn-genesis", (1, 0), ()),
        ((_v3_frame(0, writes=[(5, "aa", "D")]),
          _v3_frame(1, [(5, "aa", 2, 1)])),
         0, "aa D", "aa U", "read-deleted-version", (2, 1), ()),
    ]
    for first, second, kind, repair in (
            ("U", "I", "insert-on-live", "U"),
            ("D", "U", "update-on-absent", "I"),
            ("D", "D", "delete-on-absent", "I")):
        cases.append(((_v3_frame(0, writes=[(5, "aa", first)]),
                       _v3_frame(1, writes=[(5, "aa", second)])),
                      1, f"aa {second}", f"aa {repair}", kind, (2, 2), (second,)))
    for files, index, old, new, kind, version, ops in cases:
        result = _existence_result(files, [kind], paths=True)
        assert result.integrity.existence_violation_details == [
            ExistenceViolation(1, 5, "aa", version, kind, ops)]
        repaired = list(files)
        repaired[index] = repaired[index].replace(old, new)
        _existence_result(repaired, paths=True)


def test_v3_existence_valid_histories_and_self_reads():
    cases = [
        (_v3_frame(0, [(5, "aa", 1, 0)]),),
        (_v3_frame(0, writes=[(5, "aa", "U")]), _v3_frame(1, [(5, "aa", 1, 0)])),
        (_v3_frame(0, writes=[(5, "aa", "I")]), _v3_frame(1, [(5, "aa", 2, 1)])),
        (_v3_frame(0, writes=[(5, "aa", "D")]),
         _v3_frame(1, writes=[(5, "aa", "I")]), _v3_frame(2, [(5, "aa", 2, 2)])),
        (_v3_frame(0, writes=[(5, "aa", "I")]),
         _v3_frame(1, writes=[(5, "aa", "D")]), _v3_frame(2, [(5, "aa", 2, 1)])),
    ]
    for files in cases:
        result = _existence_result(files)
        assert result.integrity.notes == []
    files = list(cases[-1])
    files[-1] = files[-1].replace("aa 2 1", "aa 2 2")
    _existence_result(files, ["read-deleted-version"])
    # Synthetic format semantics: no claim that the native emitter emits self R.
    for op in ("I", "U", "D"):
        _existence_result((_v3_frame(0, [(5, "aa", 2, 1)], [(5, "aa", op)]),),
                          ["read-deleted-version"] if op == "D" else [])


def test_v3_existence_version_order_and_table_isolation():
    _existence_result((_v3_frame(0, writes=[(5, "aa", "U")], commit=(3, 1)),
                       _v3_frame(1, writes=[(5, "aa", "I")], commit=(2, 9))), paths=True)
    files = (_v3_frame(0, writes=[(5, "aa", "I")]), _v3_frame(1, [(9, "aa", 1, 0)]))
    _existence_result(files, paths=True)
    _existence_result((files[0], files[1].replace("R 1 9", "R 1 5")),
                      ["read-unborn-genesis"], paths=True)


def test_v3_existence_write_duplicates():
    from orchestrator.verifier.model import ExistenceViolation
    files = (_v3_frame(0, writes=[(5, "aa", "I"), (5, "aa", "D")]),)
    result = _existence_result(files, ["ambiguous-write-version"], paths=True)
    assert result.integrity.existence_violation_details == [
        ExistenceViolation(0, 5, "aa", (2, 1), "ambiguous-write-version", ("D", "I"))]
    _existence_result((files[0].replace("aa D", "aa I"),), paths=True)
    # All P1/P2/P3 diagnostics on the ambiguous object are suppressed.
    _existence_result((files[0], _v3_frame(1, [(5, "aa", 1, 0)]),
                       _v3_frame(2, [(5, "aa", 2, 1)]),
                       _v3_frame(3, writes=[(5, "aa", "I")])),
                      ["ambiguous-write-version"])


def test_v3_existence_integrity_overlap_and_winners():
    import shutil
    cases = [
        ((_v3_frame(0, writes=[(5, "aa", "I")]),
          _v3_frame(1, writes=[(5, "aa", "D")], commit=(2, 1))), "version_dups", 0),
        ((_v3_frame(0, writes=[(5, "aa", "I")], commit=(1, 0)),), "genesis_commits", 0),
        ((_v3_frame(0, [(5, "aa", 7, 7)]),), "orphan_reads", 0),
        ((_v3_frame(0, writes=[(5, "aa", "I")]),
          _v3_frame(1, [(5, "aa", 1, 0), (5, "bb", 7, 7)])), "orphan_reads", 1),
        ((_v3_frame(0, writes=[(5, "aa", "I")]),
          _v3_frame(0, writes=[(5, "aa", "U")]),
          _v3_frame(1, [(5, "aa", 1, 0)])), "dup_txids", 0),
    ]
    for files, counter, count in cases:
        d = _tmp_trace(*files)
        try:
            for _, result in _v3_paths(d):
                assert getattr(result.integrity, counter) == 1
                assert result.integrity.existence_violations == count
                assert result.integrity.existence_violation_details is not None
                assert not result.certified
        finally:
            shutil.rmtree(d)
    # A neutral first file must not hide the later v3 schema.
    d = _tmp_trace("", _v3_frame(0, writes=[(5, "aa", "I")]),
                   _v3_frame(1, [(5, "aa", 1, 0)]))
    try:
        for _, result in _v3_paths(d, expected_commits=2):
            assert result.integrity.existence_violations == 1
            assert replace(result.integrity, existence_violations=0).clean()
    finally:
        shutil.rmtree(d)


def test_v3_existence_output_samples_and_cycle():
    import shutil
    from orchestrator.verifier.core import result_to_dict_v3
    files = tuple(_v3_frame(t, [(5, "aa", 2, 1)] * 2) for t in (3, 2, 1))
    files += (_v3_frame(0, writes=[(5, "aa", "D")]),)
    result = _existence_result(files, ["read-deleted-version"] * 6, paths=True)
    ig = result.integrity
    assert [v.txid for v in ig.existence_violation_details] == [1, 1, 2, 2, 3, 3]
    assert ig.notes == [
        "6 v3 existence violation(s) [read-deleted-version×6]: " + "; ".join(
            f"txn{t} table=5 key=aa ver=(2, 1) kind=read-deleted-version"
            for t in (1, 1, 2, 2, 3))]
    projected = result_to_dict_v3(result)["integrity"]
    assert projected["existence_violations"] == 6
    assert projected["existence_violation_details"] == [
        {"txid": t, "table": 5, "key": "aa", "version": [2, 1],
         "kind": "read-deleted-version", "ops": []} for t in (1, 1, 2, 2, 3, 3)]
    assert "existence_violations" not in result_to_dict(result)["integrity"]
    assert "existence_violation_details" not in result_to_dict(result)["integrity"]
    d = _tmp_trace(*_v3_cycle_files(), _v3_frame(
        2, [(5, "bb", 2, 3)], [(5, "bb", "D")]))
    try:
        for _, result in _v3_paths(d, expected_commits=3, max_report=0):
            assert result.verdict == "non-serializable" and not result.certified
            assert result.total_cycles > 0
            assert result.integrity.existence_violations == 1
            assert len(result_to_dict_v3(result)["integrity"]["existence_violation_details"]) == 1
    finally:
        shutil.rmtree(d)


def test_v3_cli_json_wiring_and_v2_bytes():
    import contextlib
    import io
    import shutil
    from orchestrator.verifier import cli
    from orchestrator.verifier.core import result_to_dict_v3

    cases = (
        (_v3_cycle_files(), 1),
        ((_v3_frame(0, writes=[(5, "aa", "I")]),
          _v3_frame(1, [(5, "aa", 1, 0)], tx_type=2)), 3),
        (("C 0 0 2 1 0 1\nW 0 aa U 2 1\nE 0\n",), 0),
    )
    for files, expected_rc in cases:
        d = _tmp_trace(*files)
        try:
            result = verify_trace_dir(d)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = cli.main([d, "--json", "--protocol", "silo",
                               "--ccbench-root", CCBENCH_ROOT])
            assert rc == expected_rc
            payload = json.loads(output.getvalue())["results"][0]
            assert payload == result_to_dict_v3(result)
            if expected_rc == 1:
                anomaly = payload["anomalies"][0]
                assert {n["tx_type"] for n in anomaly["cycle_nodes"]} == {1, 2}
                assert {reason["table"] for edge in anomaly["edges"]
                        for reason in edge["reasons"]} == {0, 9}
            elif expected_rc == 3:
                integrity = payload["integrity"]
                assert integrity["existence_violations"] == 1
                assert integrity["existence_violation_details"][0]["table"] == 5
            else:
                expected = {"runs": 1, "certified_serializable": 1,
                            "non_serializable": 0, "indeterminate": 0,
                            "results": [result_to_dict(result)]}
                assert output.getvalue().encode() == (
                    json.dumps(expected, indent=2, ensure_ascii=False) + "\n"
                ).encode()
        finally:
            shutil.rmtree(d)


def test_v3_capability_digest_binds_anomaly_and_existence():
    import shutil
    import commit_receipt_support as support
    from orchestrator.verifier.commit_receipt import _domain_digest
    from orchestrator.verifier.core import (result_to_dict_v3,
                                            verify_trace_dir_with_capability)

    genome, evidence, admission = support._proof_build_binding("baseline")
    cases = (
        _v3_cycle_files() + (_v3_frame(2, writes=[(5, "bb", "I")]),
                             _v3_frame(3, [(5, "bb", 1, 0)], tx_type=2)),
        ("C 0 0 2 1 0 1\nW 0 aa U 2 1\nE 0\n",),
    )
    for files in cases:
        d = _tmp_trace(*files)
        try:
            result, capability = verify_trace_dir_with_capability(
                d, expected_commits=len(files), workers=1, genome=genome,
                source_evidence=evidence, build_admission=admission,
                receipt_sink_kind="test", receipt_lock_identity_sha256="0" * 64,
                receipt_variant="baseline", receipt_operation_identity="v3-digest",
                receipt_workload_tag="unit")
            projection = result_to_dict_v3(result)
            projection.pop("trace_dir", None)
            projection["integrity"].pop("framing_violation_details", None)
            projection["integrity"].pop("permutation_violation_details", None)
            digest = lambda p: _domain_digest(b"izanagi-verifier-result-v1", p)
            assert capability._result_sha256 == digest(projection)
            if result.integrity.existence_violation_details is None:
                old = result_to_dict(result)
                old.pop("trace_dir", None)
                old["integrity"].pop("framing_violation_details", None)
                old["integrity"].pop("permutation_violation_details", None)
                assert capability._result_sha256 == digest(old)
            else:
                anomaly = projection["anomalies"][0]
                assert {n["tx_type"] for n in anomaly["cycle_nodes"]} == {1, 2}
                assert {r["table"] for e in anomaly["edges"]
                        for r in e["reasons"]} == {0, 9}
                assert projection["integrity"]["existence_violations"] == 1
                changed = json.loads(json.dumps(projection))
                changed["integrity"]["existence_violation_details"][0]["key"] = "other"
                assert digest(changed) != capability._result_sha256
                changed = json.loads(json.dumps(projection))
                changed["anomalies"][0]["cycle_nodes"][0]["tx_type"] = 5
                assert digest(changed) != capability._result_sha256
                changed = json.loads(json.dumps(projection))
                changed["anomalies"][0]["edges"][0]["reasons"][0]["table"] = 8
                assert digest(changed) != capability._result_sha256
        finally:
            shutil.rmtree(d)


def test_v3_district_lost_update_and_serial_control():
    import shutil
    lost = (
        _v3_frame(0, [(1, "aa", 1, 0)], [(1, "aa", "U")],
                  commit=(2, 1)),
        _v3_frame(1, [(1, "aa", 1, 0)], [(1, "aa", "U")],
                  commit=(2, 2), tx_type=2),
    )
    serial = (lost[0], _v3_frame(
        1, [(1, "aa", 2, 1)], [(1, "aa", "U")],
        commit=(2, 2), tx_type=2))
    for frames, expected in ((lost, "non-serializable"),
                             (serial, "serializable")):
        d = _tmp_trace(*frames)
        try:
            result = verify_trace_dir(d, expected_commits=2)
            assert result.integrity.proof_surfaces.certification_gate_satisfied()
            assert result.integrity.malformed_keys == 0
            assert result.integrity.framing_violations == 0
            assert result.verdict == expected
            assert result.certified == (expected == "serializable")
            if expected == "non-serializable":
                assert result.anomalies
                reasons = {(r.etype, r.table) for e in result.anomalies[0].edges
                           for r in e.reasons}
                assert ("ww", 1) in reasons and ("rw", 1) in reasons
        finally:
            shutil.rmtree(d)


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
