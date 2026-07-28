# -*- coding: utf-8 -*-
"""後続段 4 coder 自律ループ harness (p3_s4_loop) + diff-quarantine 還流の単体テスト。

build/verify/bench を伴わない **機械部分** を固める (LLM proposal は fixture で与える):
挿入 (render_hole) → diff 検疫 (quarantine) → WAL 記録 (record_diff_reject) →
消費 (load_diff_rejections / render_rejections) → whiteboard 射影 → 停止判定 →
mutation-red gate。実 build/verify/bench の E2E は p3_s4_loop.main() が別途行う。

pytest でも 素の `python3 orchestrator/tests/test_p3_s4_loop.py` でも走る。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest.mock

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import ident, p3_s4_loop as L                        # noqa: E402
from campaign import p3_s4_loop_sort as SORT_LOOP                  # noqa: E402
from campaign import p3_s4_loop_trigger_gating as TRIGGER_LOOP     # noqa: E402
from campaign import source_digest, wal                            # noqa: E402
from campaign.loop import CampaignSummary                          # noqa: E402
from campaign.pipeline import variant_id                           # noqa: E402
from campaign.diff_quarantine import DiffRejectSubtype            # noqa: E402
from campaign.layout import CampaignLayout                        # noqa: E402
from campaign.model import Genome, STAGE_ABORT                    # noqa: E402
from critic.digest import (DIFF_QUARANTINE_REASON,                 # noqa: E402
                           load_diff_rejections,
                           load_liveness_rejections, render_rejections)

# 実 backoff.hh の EVOLVE-BLOCK 骨格を写した fixture (test_diff_quarantine と同型)。
_TEMPLATE = """#pragma once
#include "atomic_tool.hh"

class Backoff {
 public:
  static void backoff(size_t clocks_per_us) {
    uint64_t start(rdtscp()), stop;
    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
    // izanagi Phase 3: この骨格だけが coder の編集面 (合成枝の中身のみ)。
#if BACKOFF_FIXED >= 0
    double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
    // EVOLVE-BLOCK-END silo-backoff-magnitude
    while (stop - start < clocks_per_us * now_backoff) stop = rdtscp();
  }
};
"""
_SRC_REL = "backoff.hh"
_G = Genome("silo", {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0,
                     "WAL": 0, "BACK_OFF": 1, "BACKOFF_FIXED": 20})


def _mk_template_dir():
    d = tempfile.mkdtemp(prefix="izanagi_s4loop_")
    with open(os.path.join(d, _SRC_REL), "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


# ==== render_hole / quarantine (挿入 + 検疫) ==================================

def test_render_hole_preserves_indent_and_replaces_only_hole():
    """hole 行だけがインデント保持で置換され、フレーム (#if/#else/stock 枝) は不変。"""
    from campaign.diff_quarantine import parse_template_file
    d = _mk_template_dir()
    m = parse_template_file(os.path.join(d, _SRC_REL), "silo-backoff-magnitude")
    edited = L.render_hole(_TEMPLATE, m, "double now_backoff = 20.0;")
    assert "    double now_backoff = 20.0;" in edited          # インデント保持
    assert "double now_backoff = Backoff_.load" in edited      # stock 枝 (不可触) 残存
    assert "#if BACKOFF_FIXED >= 0" in edited                  # #if フレーム不変
    assert "static_cast<double>(BACKOFF_FIXED)" not in edited  # 旧 hole 消失


def test_quarantine_passes_clean_backoff_value():
    """正常な straight-line 提案 (hole 内・生指令なし) は passed=True。"""
    d = _mk_template_dir()
    res, base, edited, diff = L.quarantine(d, "double now_backoff = 20.0;",
                                           source_rel=_SRC_REL, write=False)
    assert res.passed, f"clean 提案が reject された: {res.reason}"
    assert "20.0" in edited and diff  # 実際に diff が生じている


def test_quarantine_rejects_directive_in_hole():
    """hole 内の行頭前処理指令 (#define 等) は HOLE_ESCAPE reject (二次検査)。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, "#define EVIL 1\ndouble now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.HOLE_ESCAPE
    assert "branch=content-directive" in res.digest["evidence"]


def test_quarantine_rejects_marker_forgery_in_hole():
    """hole 内の EVOLVE-BLOCK-BEGIN/END 指令はフレーム偽装 → HOLE_ESCAPE reject。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d,
                           'const char* marker = "EVOLVE-BLOCK-END demo";\n'
                           "double now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.HOLE_ESCAPE
    assert "branch=content-marker" in res.digest["evidence"]


def test_quarantine_fails_closed_on_broken_template():
    """骨格が壊れて parse_template_file が None を返す → MALFORMED 相当で fails-closed。"""
    d = tempfile.mkdtemp(prefix="izanagi_s4loop_bad_")
    with open(os.path.join(d, _SRC_REL), "w", encoding="utf-8") as f:
        f.write("no evolve block here\n")
    res, *_ = L.quarantine(d, "double now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    assert not res.passed
    assert res.digest and res.digest["subtype"] == "malformed"


# ==== WAL 往復 (record_diff_reject → load_diff_rejections、片肺の両端) =========

def test_diffq_reason_matches_diff_quarantine_rejection_type():
    """DIFF_QUARANTINE_REASON が diff_quarantine の rejection_type と 1:1 (暗黙 API 固定)。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, "#define X 1\ndouble now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    assert res.digest["rejection_type"] == DIFF_QUARANTINE_REASON


def test_record_and_load_diff_rejection_roundtrip():
    """diff 検疫 reject が WAL に焼かれ、load_diff_rejections が構造を保って復元する。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, "#define X 1\ndouble now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    lay = CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s4loop_wal_"))
    lay.ensure()
    v = L.record_diff_reject(lay, _G, "#define X 1\ndouble now_backoff = 20.0;", res)
    dqs = load_diff_rejections(lay)
    assert len(dqs) == 1
    dq = dqs[0]
    assert dq.variant == v
    assert dq.subtype == "hole-escape"
    assert dq.genome == _G.canonical()
    assert dq.reason and dq.evidence            # 構造 (理由・証拠) が保たれている


def test_base_sort_trigger_reject_writers_fail_closed_on_unframed_tail():
    d = _mk_template_dir()
    implementation = "#define X 1\ndouble now_backoff = 20.0;"
    res, *_ = L.quarantine(d, implementation, source_rel=_SRC_REL, write=False)
    assert not res.passed

    for caller, env_tag in (
            ("p3-base", L.ENV_TAG),
            ("p3-sort", SORT_LOOP.ENV_TAG),
            ("p3-trigger", TRIGGER_LOOP.ENV_TAG)):
        lay = CampaignLayout(root=tempfile.mkdtemp(prefix=f"izanagi_{caller}_")).ensure()
        with open(lay.wal_file, "wb") as stream:
            stream.write(b'{"unframed":')
        before = open(lay.wal_file, "rb").read()

        try:
            L.record_diff_reject(lay, _G, implementation, res, env_tag=env_tag)
            raise AssertionError(f"{caller}: unframed tail への reject append が通った")
        except wal.WalAppendError as exc:
            assert exc.phase == "tail-gate"
            assert isinstance(exc.cause, wal.WalFramingError)

        assert open(lay.wal_file, "rb").read() == before
        assert not any(name.startswith("wal-tail-repair-")
                       for name in os.listdir(lay.runs_dir))


def test_diff_reject_not_double_counted_in_liveness_other():
    """load_liveness_rejections が diff-quarantine を other に混ぜない (二重計上防止)。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, "#define X 1\ndouble now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    lay = CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s4loop_wal2_"))
    lay.ensure()
    L.record_diff_reject(lay, _G, "#define X 1\ndouble now_backoff = 20.0;", res)
    livs, other = load_liveness_rejections(lay)
    assert livs == []                            # liveness ではない
    assert DIFF_QUARANTINE_REASON not in other   # other にも混ざらない


def test_render_rejections_diff_section_has_no_perf_tokens():
    """render_rejections の diff-quarantine 節に性能数値 (fitness/throughput) が無い (規律2)。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, "#define X 1\ndouble now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    lay = CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s4loop_wal3_"))
    lay.ensure()
    L.record_diff_reject(lay, _G, "#define X 1\ndouble now_backoff = 20.0;", res)
    out = render_rejections([], [], {}, None, diff_rejections=load_diff_rejections(lay))
    assert "diff-quarantine:hole-escape" in out
    for tok in ("throughput", "fitness", "ops/sec", "tps"):
        assert tok not in out.lower()


def test_comment_reject_wal_to_critic_digest_does_not_repeat_payload():
    """コメント payload は reject 後の WAL→critic 描画にも逐語で再掲しない。"""
    sentinel = "QPROBE_7f3a4"
    implementation = f"double now_backoff = 20.0; // {sentinel}"
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, implementation, source_rel=_SRC_REL, write=False)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.HOLE_ESCAPE
    assert "branch=content-comment-line" in res.digest["evidence"]

    lay = CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s4loop_comment_redact_"))
    lay.ensure()
    L.record_diff_reject(lay, _G, implementation, res)
    raw_records = wal.read_records(lay)
    raw_payloads = json.dumps([r.payload for r in raw_records], ensure_ascii=False)
    assert sentinel not in raw_payloads
    reject_records = [
        r for r in raw_records
        if r.stage == STAGE_ABORT
        and r.payload.get("reason") == DIFF_QUARANTINE_REASON
    ]
    assert len(reject_records) == 1
    assert set(reject_records[0].payload) == {
        "reason", "genome", "diff_quarantine",
    }

    loaded = load_diff_rejections(lay)
    assert len(loaded) == 1
    out = render_rejections([], [], {}, None, diff_rejections=loaded)
    assert "diff-quarantine:hole-escape" in out
    assert sentinel not in out


def test_render_rejections_diff_only_not_all_green():
    """diff-quarantine reject だけあるとき「全 variant 緑」と誤表示しない。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, "#define X 1\ndouble now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    lay = CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s4loop_wal4_"))
    lay.ensure()
    L.record_diff_reject(lay, _G, "#define X 1\ndouble now_backoff = 20.0;", res)
    out = render_rejections([], [], {}, None, diff_rejections=load_diff_rejections(lay))
    assert "全 variant 緑" not in out


# ==== whiteboard 射影 (機序を落とす) =========================================

def test_whiteboard_entry_has_no_attribution_field():
    """WhiteboardEntry は機序 (critic attribution) フィールドを持たない
    (structural inference リスク対策の物理的表現、design v1 §4)。"""
    e = L.WhiteboardEntry(iteration=1, direction="increase", magnitude="small",
                          result="fail", delta_pct=-1.2)
    assert not hasattr(e, "attribution")
    assert not hasattr(e, "justification")
    # 記録されるのは方向・magnitude・result・delta_pct のみ。
    assert set(vars(e)) == {"iteration", "direction", "magnitude", "result", "delta_pct"}


def test_project_whiteboard_appends_direction_only():
    st = L.LoopState(iteration=2, start_ts=time.monotonic())
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="decrease", magnitude="medium",
                           justification="機序 (漏らしてはいけない)")
    e = L.project_whiteboard(st, pl, "success", delta_pct=3.1)
    assert e.direction == "decrease" and e.magnitude == "medium"
    assert e.result == "success" and e.delta_pct == 3.1
    assert len(st.whiteboard) == 1
    # planner の justification (機序) は whiteboard に転写されない。
    assert "機序" not in str(vars(e))


# ==== 停止判定 (design v1 §4) ================================================

def test_check_stop_continue():
    st = L.LoopState(iteration=1, start_ts=time.monotonic())
    assert L.check_stop(st) == L.StopDecision(False, "continue")


def test_check_stop_budget_iterations():
    st = L.LoopState(iteration=L.MAX_ITER, start_ts=time.monotonic())
    assert L.check_stop(st).reason == "budget-iterations"


def test_check_stop_converged_same_direction_small():
    st = L.LoopState(iteration=4, start_ts=time.monotonic())
    for i in range(1, 4):
        st.whiteboard.append(L.WhiteboardEntry(i, "increase", "small", "fail", -0.5))
    assert L.check_stop(st).reason == "converged"


def test_check_stop_not_converged_when_magnitude_changes():
    """small→medium→large の段階的変化は「異なる提案」= 収束と扱わない。"""
    st = L.LoopState(iteration=4, start_ts=time.monotonic())
    for i, mag in enumerate(["small", "medium", "large"], 1):
        st.whiteboard.append(L.WhiteboardEntry(i, "increase", mag, "fail", -0.5))
    assert L.check_stop(st).reason == "continue"


def test_check_stop_reverse_exhausted():
    st = L.LoopState(iteration=5, start_ts=time.monotonic())
    st.reverse_recommendations = L.REVERSE_STREAK
    st.whiteboard.append(L.WhiteboardEntry(4, "increase", "small", "fail", -1.0))
    assert L.check_stop(st).reason == "reverse-exhausted"


def test_check_stop_reject_streak_not_converged():
    """diff 検疫 reject (result=rejected) が同方向・small で 3 連続しても収束扱いしない
    — 評価未成立を最適収束と取り違えない (規律3、D39 決定2a)。"""
    st = L.LoopState(iteration=4, start_ts=time.monotonic())
    for i in range(1, 4):
        st.whiteboard.append(L.WhiteboardEntry(i, "increase", "small", "rejected"))
    assert L.check_stop(st).reason == "continue"


def test_check_stop_converged_ignores_interleaved_reject():
    """収束は評価済み提案で測る — 間に挟まる reject は数えず、評価済み 3 連続で収束する。"""
    st = L.LoopState(iteration=5, start_ts=time.monotonic())
    st.whiteboard.append(L.WhiteboardEntry(1, "increase", "small", "fail", -0.5))
    st.whiteboard.append(L.WhiteboardEntry(2, "increase", "small", "rejected"))
    st.whiteboard.append(L.WhiteboardEntry(3, "increase", "small", "fail", -0.4))
    st.whiteboard.append(L.WhiteboardEntry(4, "increase", "small", "success", 0.1))
    assert L.check_stop(st).reason == "converged"


def test_check_stop_reverse_exhausted_none_delta_still_fires():
    """段 4 は delta_pct 未算出 (None) — 「改善なら止めない」escape は明示的に無効で
    reverse-exhausted は reverse_recommendations 単独で発火する (D39 決定2b の段 4 挙動)。"""
    st = L.LoopState(iteration=5, start_ts=time.monotonic())
    st.reverse_recommendations = L.REVERSE_STREAK
    st.whiteboard.append(L.WhiteboardEntry(4, "increase", "small", "success", None))
    assert L.check_stop(st).reason == "reverse-exhausted"


def test_check_stop_reverse_escape_lives_when_delta_positive():
    """段 6 で delta_pct が算出されると「直近改善 (delta>0) なら止めない」escape が live 化する
    — 恒真ガードでないことの対照 (正の delta を与えると reverse-exhausted しない)。"""
    st = L.LoopState(iteration=5, start_ts=time.monotonic())
    st.reverse_recommendations = L.REVERSE_STREAK
    st.whiteboard.append(L.WhiteboardEntry(4, "increase", "small", "success", 5.0))
    assert L.check_stop(st).reason == "continue"


# ==== mutation-red 汎用ゲート (D38 残、design v1 §4(d)) =======================

def test_mutation_red_gate_rejects_tautology():
    ok, why = L.mutation_red_gate("x == x", "some_invariant")
    assert not ok and "恒真" in why


def test_mutation_red_gate_rejects_condition_equals_invariant():
    ok, _ = L.mutation_red_gate("aborts >= 0", "aborts >= 0")
    assert not ok


def test_mutation_red_gate_rejects_empty_and_true():
    assert not L.mutation_red_gate("", "inv")[0]
    assert not L.mutation_red_gate("true", "inv")[0]


def test_mutation_red_gate_passes_non_tautology():
    ok, _ = L.mutation_red_gate("lock_coverage_violations == 0", "trace_is_complete")
    assert ok


def test_mutation_red_gate_rejects_constant_tautology():
    """両辺が定数の常真比較 (5>=3, 1==1) は恒真として reject (fail-open の穴を 1 つ塞ぐ)。"""
    assert not L.mutation_red_gate("5 >= 3", "different_invariant")[0]
    assert not L.mutation_red_gate("1 == 1", "different_invariant")[0]
    assert L.mutation_red_gate("3 >= 5", "different_invariant")[0]   # 常偽は tautology でない


def test_mutation_red_gate_semantic_tautology_fails_open_by_design():
    """文脈依存の意味的恒真 (unsigned の aborts>=0 等) は構文篩を fail-open で通す —
    構文検査の原理的限界 (D33)。load-bearing な担保は positive control 実走 (段 5)。
    この既知の穴を change-detector で固定する (4a の conservative-by-design と同型)。"""
    ok, _ = L.mutation_red_gate("aborts >= 0", "trace_is_complete")
    assert ok


# ==== 帰属整合 (value ↔ hole literal、D39 決定7 の機械強制) ===================

def test_value_literal_consistency_accepts_match():
    """value と now_backoff literal が数値一致すれば通る (20==20、20.0==20)。"""
    L.assert_value_literal_consistent(
        L.CoderProposal(axis=L.MARKER_ID, value=20,
                        implementation="double now_backoff = 20;"))
    L.assert_value_literal_consistent(
        L.CoderProposal(axis=L.MARKER_ID, value=20.0,
                        implementation="double now_backoff = 20.0;"))


def test_value_literal_consistency_rejects_mismatch():
    """value=20 だが literal=999 → 帰属汚染で AttributionMismatch (規律6/D39 決定7)。"""
    try:
        L.assert_value_literal_consistent(
            L.CoderProposal(axis=L.MARKER_ID, value=20,
                            implementation="double now_backoff = 999;"))
        raise AssertionError("value↔literal 不一致が AttributionMismatch を送出しなかった")
    except L.AttributionMismatch:
        pass


def test_value_literal_consistency_fails_closed_when_value_absent():
    """now_backoff literal を抽出できず value が数値として現れない自由式は fails-closed。"""
    try:
        L.assert_value_literal_consistent(
            L.CoderProposal(axis=L.MARKER_ID, value=20,
                            implementation="double now_backoff = compute_it();"))
        raise AssertionError("value 不在の自由式が AttributionMismatch を送出しなかった")
    except L.AttributionMismatch:
        pass


# ==== variant id / critic digest =============================================

def test_diffq_variant_id_deterministic_and_proposal_sensitive():
    a1 = L.diffq_variant_id(_G, "double now_backoff = 20.0;")
    a2 = L.diffq_variant_id(_G, "double now_backoff = 20.0;")
    b = L.diffq_variant_id(_G, "double now_backoff = 30.0;")
    assert a1 == a2 and a1 != b
    assert a1.startswith("diffq-")


def test_make_critic_digest_reflux_off_drops_red_section():
    """reflux=off (還流 off ablation) では赤節を落とす (LLM ablation の対照)。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d, "#define X 1\ndouble now_backoff = 20.0;",
                           source_rel=_SRC_REL, write=False)
    lay = CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s4loop_reflux_"))
    lay.ensure()
    L.record_diff_reject(lay, _G, "#define X 1\ndouble now_backoff = 20.0;", res)
    on = L.make_critic_digest(lay, reflux=True)
    off = L.make_critic_digest(lay, reflux=False)
    assert "diff-quarantine" in on            # on アームは赤を還流
    assert "diff-quarantine" not in off       # off アームは落とす


# ==== LoopState checkpoint/resume (段 4b の cross-process 永続化) ==============

def _tmp_layout(tag: str) -> CampaignLayout:
    return CampaignLayout(root=tempfile.mkdtemp(prefix=f"izanagi_s4loop_{tag}_")).ensure()


def test_loop_state_roundtrip():
    """save → load で whiteboard/iteration/reverse/start_wall が完全復元する (段 4 は
    delta_pct≡None ゆえ entry の delta_pct は None)。"""
    lay = _tmp_layout("ckpt")
    st = L.LoopState(iteration=3, start_wall=1000.5, reverse_recommendations=1)
    st.whiteboard.append(L.WhiteboardEntry(1, "increase", "small", "fail", None))
    st.whiteboard.append(L.WhiteboardEntry(2, "decrease", "medium", "rejected", None))
    p = L.save_loop_state(lay, st)
    assert os.path.exists(p)
    st2 = L.load_loop_state(lay)
    assert L.state_to_dict(st) == L.state_to_dict(st2)
    assert st2.iteration == 3 and st2.reverse_recommendations == 1
    assert st2.start_wall == 1000.5
    assert [e.direction for e in st2.whiteboard] == ["increase", "decrease"]
    assert all(e.delta_pct is None for e in st2.whiteboard)


def test_state_from_dict_rejects_nonnull_delta_pct():
    """段 4 の delta_pct≡None 不変を load 側が値契約として強制する — 非 None (勝ち筋チャネル) の
    checkpoint 経由混入を WhiteboardLeakError で弾く (型で名前を whitelist するだけでは防げない、
    規律2/6、監査 2026-07-08)。"""
    bad = {"iteration": 3, "start_wall": 0.0, "reverse_recommendations": 0,
           "whiteboard": [{"iteration": 1, "direction": "increase", "magnitude": "small",
                           "result": "success", "delta_pct": 4.7}]}
    try:
        L.state_from_dict(bad)
        raise AssertionError("非 None delta_pct を素通しした (勝ち筋チャネル混入)")
    except L.WhiteboardLeakError as e:
        assert "delta_pct" in str(e)


def test_state_from_dict_fails_closed_on_missing_top_level_field():
    """top-level 予算フィールド欠落 (drift/改竄) を fail-closed で弾く — 無音デフォルトすると
    iteration/reverse カウンタが暗黙リセットされ予算ゲートが fail-open する (規律2/4/6、監査 2026-07-08)。"""
    for drop in ("iteration", "reverse_recommendations", "start_wall", "whiteboard"):
        d = {"iteration": 9, "start_wall": 1.0, "reverse_recommendations": 5, "whiteboard": []}
        del d[drop]
        try:
            L.state_from_dict(d)
            raise AssertionError(f"必須フィールド {drop} 欠落を素通しした (予算ゲート fail-open)")
        except ValueError as e:
            assert drop in str(e) or "必須" in str(e)


def test_state_from_dict_rejects_unknown_top_level_field():
    """top-level の未知キー (schema drift/改竄) を fail-closed で弾く (whiteboard entry 層と対称)。"""
    d = {"iteration": 1, "start_wall": 0.0, "reverse_recommendations": 0, "whiteboard": [],
         "sweet_spot": 25.0}   # 未知 top-level フィールド混入
    try:
        L.state_from_dict(d)
        raise AssertionError("未知 top-level フィールドを素通しした")
    except ValueError as e:
        assert "sweet_spot" in str(e)


def test_whiteboard_for_planner_rejects_nonnull_delta_pct():
    """planner 射影の関所でも段 4 は delta_pct≡None を強制する (in-memory 経路の二重防壁、規律2/6)。"""
    st = L.LoopState(iteration=2)
    st.whiteboard.append(L.WhiteboardEntry(1, "increase", "small", "success", 3.3))
    try:
        L.whiteboard_for_planner(st)
        raise AssertionError("planner 射影が非 None delta_pct を素通しした")
    except L.WhiteboardLeakError:
        pass


def test_load_loop_state_missing_returns_none():
    """checkpoint 未作成の layout は None (呼び出し元が初期化する)。"""
    assert L.load_loop_state(_tmp_layout("empty")) is None


def test_state_to_dict_has_only_abstract_whiteboard_fields():
    """checkpoint の whiteboard entry は決定3 の 5 フィールドのみ — 機序 (attribution/
    justification) を永続化層に持ち込まない (structural inference 経路を型で塞ぐ、規律2/6)。"""
    st = L.LoopState(iteration=1)
    st.whiteboard.append(L.WhiteboardEntry(1, "increase", "small", "fail", -1.0))
    d = L.state_to_dict(st)
    assert set(d["whiteboard"][0]) == {"iteration", "direction", "magnitude",
                                       "result", "delta_pct"}
    assert set(d) == {"iteration", "start_wall", "reverse_recommendations", "whiteboard"}
    assert "start_ts" not in d          # monotonic は永続化しない (跨ぐと無意味)


def test_state_from_dict_rejects_unknown_whiteboard_field():
    """未知フィールド (機序漏れ) を持つ checkpoint を load 側で拒否する — 決定3 の型不変を
    復元経路でも守る (汚染 checkpoint を素通しして planner に機序を渡さない、規律6)。"""
    bad = {"iteration": 1, "start_wall": 0.0, "reverse_recommendations": 0,
           "whiteboard": [{"iteration": 1, "direction": "increase", "magnitude": "small",
                           "result": "fail", "delta_pct": -1.0,
                           "attribution": "MLP 低下が効いた"}]}   # 機序フィールド混入
    try:
        L.state_from_dict(bad)
        raise AssertionError("機序フィールド混入 checkpoint を素通しした")
    except ValueError as e:
        assert "attribution" in str(e)


def test_cross_process_whiteboard_accumulates():
    """別 iteration = 別プロセスを模し、checkpoint 経由で whiteboard が累積することを確認。
    これが無いと planner が前 iteration の result を見れず feedback loop が死ぬ (段 4b の core)。"""
    lay = _tmp_layout("xproc")
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="increase", magnitude="small")
    # iteration 1 (プロセス A): 復元 (無 → 初期化) → 射影 → 保存
    st = L.load_loop_state(lay) or L.LoopState(start_wall=time.time())
    st.iteration += 1
    L.project_whiteboard(st, pl, "fail")
    L.save_loop_state(lay, st)
    # iteration 2 (プロセス B): 復元 (iteration 1 の状態を拾う) → 射影 → 保存
    st = L.load_loop_state(lay)
    assert st is not None and len(st.whiteboard) == 1 and st.iteration == 1
    st.iteration += 1
    L.project_whiteboard(st, pl, "rejected")
    L.save_loop_state(lay, st)
    # 復元して 2 件累積・順序保持を確認
    st = L.load_loop_state(lay)
    assert st.iteration == 2 and len(st.whiteboard) == 2
    assert [e.result for e in st.whiteboard] == ["fail", "rejected"]


def test_fold_critic_reverse():
    """critic feedback の畳込み: True→+1 (逆方向推奨の連続)、False→0 リセット、None→変更なし。"""
    st = L.LoopState()
    L._fold_critic_reverse(st, True)
    L._fold_critic_reverse(st, True)
    assert st.reverse_recommendations == 2
    L._fold_critic_reverse(st, None)          # 変更なし
    assert st.reverse_recommendations == 2
    L._fold_critic_reverse(st, False)         # 順方向路線 → リセット
    assert st.reverse_recommendations == 0


def test_wall_budget_via_start_wall():
    """checkpoint 経由 (start_wall 設定) では wall-clock で予算判定する (cross-process)。
    start_wall を過去に置くと budget-walltime、直近なら継続 — monotonic に依存しない。"""
    st = L.LoopState(iteration=1, start_wall=time.time() - L.MAX_WALLTIME_S - 1)
    assert L.check_stop(st).reason == "budget-walltime"
    st2 = L.LoopState(iteration=1, start_wall=time.time())
    assert L.check_stop(st2).reason == "continue"


def test_drive_iteration_stops_before_running_when_reverse_exhausted():
    """入口停止: 前 critic の逆方向推奨で reverse_recommendations が閾値に達すると、
    drive_iteration は run_one_iteration を呼ばず (ran=False) build/verify/bench に進まない。
    sub に不在パスを渡しても到達しない = 実行前に停止する証拠 (submodule に触れない)。"""
    lay = _tmp_layout("stopbefore")
    seed = L.LoopState(iteration=0, start_wall=time.time(),
                       reverse_recommendations=L.REVERSE_STREAK - 1)
    L.save_loop_state(lay, seed)
    cfg, perf = L.default_cfg(), L.default_perf()
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="increase", magnitude="small")
    cd = L.CoderProposal(axis=L.MARKER_ID, value=20.0,
                         implementation="double now_backoff = 20.0;")
    out = L.drive_iteration(cfg, perf, pl, cd, prior_critic_reverse=True,
                            sub="/nonexistent/should/not/be/touched",
                            do_build=False, layout=lay)
    assert out["ran"] is False
    assert out["stop_reason"] == "reverse-exhausted"
    # checkpoint に畳込み後の reverse=REVERSE_STREAK が焼かれている
    st = L.load_loop_state(lay)
    assert st.reverse_recommendations == L.REVERSE_STREAK


def test_drive_iteration_checkpoint_survives_across_calls():
    """fresh reject が identity を確立し、次候補の public drive が resume できる。"""
    import contextlib
    from campaign import patchharness

    sub = tempfile.mkdtemp(prefix="izanagi_s4loop_public_")
    os.makedirs(os.path.join(sub, "include"))
    with open(os.path.join(sub, L.SOURCE_REL), "w", encoding="utf-8") as stream:
        stream.write(_TEMPLATE)
    lay = _tmp_layout("drivereject")
    cfg, perf = L.default_cfg(), L.default_perf()
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="increase", magnitude="small")
    # hole-escape (行頭 #define) → diff 検疫 reject。value と literal は整合させる。
    cd = L.CoderProposal(axis=L.MARKER_ID, value=20.0,
                         implementation="#define EVIL 1\ndouble now_backoff = 20.0;")
    with unittest.mock.patch.object(
            patchharness, "applied",
            side_effect=lambda *_a, **_k: contextlib.nullcontext()):
        out1 = L.drive_iteration(
            cfg, perf, pl, cd, None, sub, do_build=False, layout=lay,
        )
    assert out1["ran"] is True and out1["outcome"] == "rejected" and out1["iteration"] == 1
    assert wal.read_lock(lay) == ident.canonical_preimage(cfg)
    st = L.load_loop_state(lay)
    assert len(st.whiteboard) == 1 and st.whiteboard[0].result == "rejected"
    next_cd = L.CoderProposal(
        axis=L.MARKER_ID, value=30.0,
        implementation="#define EVIL_NEXT 1\ndouble now_backoff = 30.0;",
    )
    with unittest.mock.patch.object(
            patchharness, "applied",
            side_effect=lambda *_a, **_k: contextlib.nullcontext()):
        out2 = L.drive_iteration(
            cfg, perf, pl, next_cd, None, sub, do_build=False, layout=lay,
        )
    assert out2["iteration"] == 2 and out2["outcome"] == "rejected"
    st = L.load_loop_state(lay)
    assert len(st.whiteboard) == 2 and st.iteration == 2


def test_load_proposal_file_rejects_nonbool_prior_reverse():
    """prior_critic_reverse が非 bool (文字列 "true" 等) だと _fold_critic_reverse で黙って no-op し
    停止フィードバックが fail-open する → load 側で fail-closed に弾く (規律2、監査 2026-07-08)。"""
    d = os.path.join(tempfile.mkdtemp(prefix="izanagi_s4loop_prop_"), "prop.json")
    with open(d, "w", encoding="utf-8") as f:
        json.dump({"planner": {"axis": "silo-backoff-magnitude", "direction": "increase",
                               "magnitude": "small"},
                   "coder": {"axis": "silo-backoff-magnitude", "value": 20.0,
                             "implementation": "double now_backoff = 20.0;"},
                   "prior_critic_reverse": "true"}, f)   # 非 bool (文字列)
    try:
        L.load_proposal_file(d)
        raise AssertionError("非 bool prior_critic_reverse を素通しした (停止フィードバック fail-open)")
    except ValueError as e:
        assert "prior_critic_reverse" in str(e)


def test_load_proposal_file_accepts_null_and_bool_prior_reverse():
    """null と bool は正常に読める (fail-closed が正当値を巻き込まない)。"""
    base = {"planner": {"axis": "silo-backoff-magnitude", "direction": "increase",
                        "magnitude": "small"},
            "coder": {"axis": "silo-backoff-magnitude", "value": 20.0,
                      "implementation": "double now_backoff = 20.0;"}}
    dd = tempfile.mkdtemp(prefix="izanagi_s4loop_prop2_")
    for val, expect in [(None, None), (True, True), (False, False)]:
        p = os.path.join(dd, f"prop_{val}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({**base, "prior_critic_reverse": val}, f)
        _pl, _cd, prior = L.load_proposal_file(p)
        assert prior is expect


# ==== _resolve_duplicate (重複 genome 提案 = coder が既評価値を独立に再提案) ==========

def _dup_summary(v) -> CampaignSummary:
    """run_campaign がリカバリ skip した summary の写し (skip id は applied 内で確定済み)。"""
    return CampaignSummary(campaign_id="test", layout_root="unused", total=1,
                           skipped=1, skipped_variants=[v] if v else [])


def test_resolve_duplicate_recovers_certified_from_wal():
    """run_campaign が重複 (既存 terminal variant) としてスキップし summary.results が
    空になっても、_resolve_duplicate は summary.skipped_variants の確定済み id で既存 WAL の
    commit/verify_done から証拠を復元して outcome=duplicate・whiteboard result=success を
    返す (fail と誤記録しない、規律3。段 4b iteration 2 の実走で coder が独立に同一値を
    再提案した実例で発見した回帰)。"""
    lay = _tmp_layout("dupok")
    genome = L.Genome("silo", {**L._BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 40})
    fake_src_tok = "deadbeef"
    v = variant_id(genome, fake_src_tok)
    L.wal.log(lay, v, L.STAGE_BUILD_START, L.ENV_TAG,
              {"genome": genome.canonical(), "src_token": fake_src_tok})
    L.wal.log(lay, v, L.STAGE_VERIFY_DONE, L.ENV_TAG,
              {"verdict": "serializable", "certified": True, "commits": 1, "aborts": 1})
    L.wal.log(lay, v, L.STAGE_COMMIT, L.ENV_TAG, {"fitness_tps": 491796.0, "cv": 0.009})
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="decrease", magnitude="medium")
    state = L.LoopState(iteration=2, start_wall=time.time())
    out = L._resolve_duplicate(lay, pl, state, _dup_summary(v))
    assert out["outcome"] == "duplicate"
    assert out["variant"] == v
    assert out["fitness_tps"] == 491796.0
    assert len(state.whiteboard) == 1
    assert state.whiteboard[0].result == "success"


def test_resolve_duplicate_falls_back_to_fail_when_no_commit():
    """重複先が commit でなく abort のみ (証拠が commit でない) なら成功を捏造せず
    whiteboard は fail のまま (規律2: certified を安売りしない)。"""
    lay = _tmp_layout("dupfail")
    genome = L.Genome("silo", {**L._BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 999})
    fake_src_tok = "cafef00d"
    v = variant_id(genome, fake_src_tok)
    L.wal.log(lay, v, L.STAGE_BUILD_START, L.ENV_TAG,
              {"genome": genome.canonical(), "src_token": fake_src_tok})
    L.wal.log(lay, v, L.STAGE_ABORT, L.ENV_TAG, {"reason": "verify-red"})
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="decrease", magnitude="large")
    state = L.LoopState(iteration=2, start_wall=time.time())
    out = L._resolve_duplicate(lay, pl, state, _dup_summary(v))
    assert out["outcome"] == "aborted"
    assert len(state.whiteboard) == 1
    assert state.whiteboard[0].result == "fail"


def test_resolve_duplicate_never_reresolves_source():
    """_resolve_duplicate は source_digest.resolve を再実行しない ([T-157])。呼び手の
    with applied(...) は revert 済みで、revert 後の tree から resolve すると stock id
    (別 variant) を引き、成否を誤分類し (whiteboard/checkpoint)、trigger 系 provenance へ
    誤った variant id が永続化する。id の確定点は run_campaign (applied 内) の 1 箇所だけ
    (D23/D24)。動的束縛 = resolve を poison して非呼出を実測 (構造的束縛は別テスト
    test_resolve_duplicate_structurally_free_of_resolver — 本テストの直呼びは旧 signature 回帰で
    TypeError が先行するため、そこに構造 assert を同居させると評価されず F28 型の偽 KILL に戻る)。"""
    lay = _tmp_layout("dupnores")
    genome = L.Genome("silo", {**L._BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 41})
    v = variant_id(genome, "feedface")
    L.wal.log(lay, v, L.STAGE_BUILD_START, L.ENV_TAG,
              {"genome": genome.canonical(), "src_token": "feedface"})
    L.wal.log(lay, v, L.STAGE_COMMIT, L.ENV_TAG, {"fitness_tps": 1.0, "cv": 0.0})
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="increase", magnitude="small")
    state = L.LoopState(iteration=2, start_wall=time.time())
    with unittest.mock.patch.object(
            source_digest, "resolve",
            side_effect=AssertionError("revert 後の re-resolve は禁止 ([T-157])")) as m:
        out = L._resolve_duplicate(lay, pl, state, _dup_summary(v))
    assert out["outcome"] == "duplicate" and out["variant"] == v
    m.assert_not_called()


def test_resolve_duplicate_structurally_free_of_resolver():
    """構造的束縛: _resolve_duplicate の参照名に source_digest が現れない ([T-157]/F28)。
    独立テストであること自体が仕様 — 直呼びを含むテストに同居させると、旧 (cfg, genome)
    signature ごと戻す忠実な回帰で TypeError が先行し、性質でなく引数不一致で殺す偽 KILL に
    なる。本テストは呼び出さずに code object だけを検査するため、どんな signature 回帰でも
    「再 resolve の再導入」そのものを赤にする。"""
    assert "source_digest" not in L._resolve_duplicate.__code__.co_names


def test_resolve_duplicate_empty_skip_ids_does_not_fabricate_success():
    """skipped_variants が空 (identity_skipped = id 未確定の skip) なら duplicate の成功を
    捏造せず、variant=None の fail 側へ倒す (規律2)。"""
    lay = _tmp_layout("dupempty")
    pl = L.PlannerProposal(axis=L.MARKER_ID, direction="increase", magnitude="medium")
    state = L.LoopState(iteration=2, start_wall=time.time())
    out = L._resolve_duplicate(lay, pl, state, _dup_summary(None))
    assert out["outcome"] == "aborted" and out["variant"] is None
    assert len(state.whiteboard) == 1
    assert state.whiteboard[0].result == "fail"


def test_resolve_duplicate_single_implementation_across_axes():
    """sort/trigger driver は独自コピーでなく backoff 版と同一オブジェクトを使う ([T-157]:
    旧 sort/trigger 版は revert 後 re-resolve の同型欠陥を独立に抱えていた — 再分岐を塞ぐ)。"""
    assert SORT_LOOP._resolve_duplicate is L._resolve_duplicate
    assert TRIGGER_LOOP._resolve_duplicate is L._resolve_duplicate


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fail = 0
    for fn in fns:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except Exception:
            fail += 1
            print(f"[FAIL] {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - fail}/{len(fns)} passed")
    sys.exit(1 if fail else 0)
