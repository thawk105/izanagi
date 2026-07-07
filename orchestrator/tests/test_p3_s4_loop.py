# -*- coding: utf-8 -*-
"""後続段 4 coder 自律ループ harness (p3_s4_loop) + diff-quarantine 還流の単体テスト。

build/verify/bench を伴わない **機械部分** を固める (LLM proposal は fixture で与える):
挿入 (render_hole) → diff 検疫 (quarantine) → WAL 記録 (record_diff_reject) →
消費 (load_diff_rejections / render_rejections) → whiteboard 射影 → 停止判定 →
mutation-red gate。実 build/verify/bench の E2E は p3_s4_loop.main() が別途行う。

pytest でも 素の `python3 orchestrator/tests/test_p3_s4_loop.py` でも走る。
"""
from __future__ import annotations

import os
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import p3_s4_loop as L                               # noqa: E402
from campaign.diff_quarantine import DiffRejectSubtype            # noqa: E402
from campaign.layout import CampaignLayout                        # noqa: E402
from campaign.model import Genome                                 # noqa: E402
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


def test_quarantine_rejects_marker_forgery_in_hole():
    """hole 内の EVOLVE-BLOCK-BEGIN/END 指令はフレーム偽装 → HOLE_ESCAPE reject。"""
    d = _mk_template_dir()
    res, *_ = L.quarantine(d,
                           "double now_backoff = 20.0; // EVOLVE-BLOCK-END x",
                           source_rel=_SRC_REL, write=False)
    assert not res.passed
    assert res.subtype is DiffRejectSubtype.HOLE_ESCAPE


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
