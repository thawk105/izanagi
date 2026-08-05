# -*- coding: utf-8 -*-
"""段 5 sort-strategy 自律ループ harness (p3_s4_loop_sort) の単体テスト。

`p3_s4_loop.py` (backoff 軸) の既存テストが検証済みの共有機構 (quarantine の構造的
封じ込め・check_stop・LoopState 永続化) は再検証しない — `p3_s4_loop_sort` がそれらを
正しい引数 (marker_id/source_rel) で呼び出しているかと、**sort 軸固有の新規機構**
(auditor gate の digest 突合・verdict 分岐・schema 検証) を固める。

build/verify/bench を伴わない機械部分のみ。実 LLM proposal は fixture で与える。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import ident, p3_s4_loop as L                         # noqa: E402
from campaign import p3_s4_loop_sort as S                           # noqa: E402
from campaign import wal                                            # noqa: E402
from campaign.artifact_admission import require_admitted_campaign   # noqa: E402
from campaign.diff_quarantine import DiffRejectSubtype              # noqa: E402
from campaign.layout import CampaignLayout                          # noqa: E402
from campaign.model import Genome                                   # noqa: E402
from campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY               # noqa: E402
from campaign.pipeline import VERIFY_LEGACY_PLUS_S2                  # noqa: E402
from critic.digest import load_diff_rejections                      # noqa: E402

# 実 transaction.cc の EVOLVE-BLOCK 骨格 (sort marker) を写した fixture。silo-sort-variant.patch
# と同型 (hole = #if 枝全体、実テンプレ原文の `// coder 編集面` も回帰保存)。
_TEMPLATE = """#pragma once
#include "storage.hh"

class TxExecutor {
 public:
  bool validationPhase() {
#ifndef SORT_VARIANT
#error "SORT_VARIANT must be defined"
#endif
    // EVOLVE-BLOCK-BEGIN silo-writeset-sort
    // izanagi Phase 3 (D41/phase3.md): coder の編集面はこの #if 枝のみ。
#if SORT_VARIANT
    sort(write_set_.begin(), write_set_.end());  // coder 編集面
#else
    sort(write_set_.begin(), write_set_.end());
#endif
    // EVOLVE-BLOCK-END silo-writeset-sort
    return true;
  }
};
"""
# `S.SOURCE_REL` ("cc/silo/transaction.cc") とそのまま一致させる — `_quarantine_and_audit`
# は marker_id/source_rel を引数化せず module 定数を使うため (実 driver と同じ経路を
# テストする)、fixture 側をネスト構造に合わせる。
_SRC_REL = S.SOURCE_REL
_G = Genome("silo", {**S._BASE, "SORT_VARIANT": 1})
_CLEAN_IMPL = ("    sort(write_set_.begin(), write_set_.end(),\n"
              "         [](const auto& a, const auto& b) { return a.key_ < b.key_; });")
_NON_SWO_IMPL = ("    sort(write_set_.begin(), write_set_.end(),\n"
                 "         [](const auto& a, const auto& b) { return &a != &b; });")


def _mk_template_dir() -> str:
    d = tempfile.mkdtemp(prefix="izanagi_s5sortloop_")
    full = os.path.join(d, _SRC_REL)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


def _tmp_layout(tag: str) -> CampaignLayout:
    return CampaignLayout(root=tempfile.mkdtemp(prefix=f"izanagi_s5sortloop_{tag}_")).ensure()


def _critic_view(layout: CampaignLayout):
    wal.write_lock(layout, ident.canonical_preimage(S.default_cfg()))
    return require_admitted_campaign(layout)


def _planner() -> "L.PlannerProposal":
    return L.PlannerProposal(axis=S.MARKER_ID, direction="explore_both", magnitude="small")


def _digest_for(d: str, impl: str = _CLEAN_IMPL) -> str:
    _res, _b, _e, working_diff = L.quarantine(d, impl, marker_id=S.MARKER_ID,
                                              source_rel=_SRC_REL, write=False)
    return S.compute_diff_digest(working_diff)


# ==== compute_diff_digest ======================================================

def test_compute_diff_digest_deterministic_and_sensitive():
    """同じ diff テキストは同じ digest、異なる diff は異なる digest (hash 衝突を前提にしない範囲)。"""
    a = S.compute_diff_digest("diff line 1\ndiff line 2\n")
    b = S.compute_diff_digest("diff line 1\ndiff line 2\n")
    c = S.compute_diff_digest("diff line 1\ndiff line 3\n")
    assert a == b
    assert a != c
    assert len(a) == 64  # sha256 hexdigest


# ==== _quarantine_and_audit / run_one_iteration (do_build=False) ==============

def test_run_one_iteration_dry_pass_when_auditor_pass_and_digest_matches():
    """diff 検疫 pass + auditor verdict=pass + digest 一致 → dry-pass (build に進まず)。

    `_quarantine_and_audit` を直接叩く (`applied()` = 実 submodule への git 操作を要する
    ため、その前提込みの E2E は `test_drive_iteration_checkpoint_survives_across_calls` 側
    でカバーする)。"""
    d = _mk_template_dir()
    digest = _digest_for(d)
    auditor = S.AuditorVerdict(verdict="pass", diff_digest=digest)
    coder = S.CoderProposalSort(axis=S.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    gate = S._quarantine_and_audit(d, coder, auditor, _G, _tmp_layout("pass"), state,
                                   _planner(), write=False)
    assert gate is None


def test_quarantine_and_audit_rejects_hole_escape_before_auditor_gate():
    """diff 検疫 (フレーム/hole 逸脱) で reject された場合、auditor gate に到達せず
    diff-quarantine 型の reject を返す (structural check が auditor より先)。"""
    d = _mk_template_dir()
    bad_impl = "#define EVIL 1\n" + _CLEAN_IMPL
    # digest は auditor が「pass」と言おうと関係なく hole-escape で reject されるはず。
    auditor = S.AuditorVerdict(verdict="pass", diff_digest="irrelevant")
    coder = S.CoderProposalSort(axis=S.MARKER_ID, implementation=bad_impl)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("holeescape")
    gate = S._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
    assert gate is not None
    assert gate["outcome"] == "rejected"
    assert gate["digest"]["rejection_type"] == "diff-quarantine"
    assert gate["digest"]["subtype"] == DiffRejectSubtype.HOLE_ESCAPE.value


def test_quarantine_and_audit_raises_on_digest_mismatch():
    """auditor.diff_digest が実際の working_diff と食い違うと AuditorGateFailure (fails-closed、
    宣言でなく機械照合。敵対レビュー 2026-07-10 の必須修正)。"""
    d = _mk_template_dir()
    auditor = S.AuditorVerdict(verdict="pass", diff_digest="0" * 64)  # 明らかに不一致
    coder = S.CoderProposalSort(axis=S.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("mismatch")
    try:
        S._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
        raise AssertionError("digest 不一致を素通しした")
    except S.AuditorGateFailure as e:
        assert "digest" in str(e)


def test_quarantine_and_audit_rejects_auditor_verdict_reject():
    """コメントなしの実 non-SWO comparator は検疫を通り、auditor 型14で reject。

    コメント byte 拒否が non-SWO の意味検査を吸収して意図の branch を死なせない。
    auditor.verdict='reject' (digest 一致) は auditor-violation subtype で既存の
    diff-quarantine consumer に相乗りする (auditor.md 型5 対策)。
    """
    d = _mk_template_dir()
    digest = _digest_for(d, _NON_SWO_IMPL)
    auditor = S.AuditorVerdict(verdict="reject", diff_digest=digest,
                               violations=[{"type": 14, "note": "非SWO疑い"}])
    coder = S.CoderProposalSort(axis=S.MARKER_ID, implementation=_NON_SWO_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("auditreject")
    gate = S._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
    assert gate is not None
    assert gate["outcome"] == "rejected"
    assert gate["digest"]["subtype"] == "auditor-violation"
    assert gate["digest"]["rejection_type"] == "diff-quarantine"
    # whiteboard には粗い "rejected" のみ (violations 本文は転写しない、規律2/6)
    assert state.whiteboard[-1].result == "rejected"
    # 既存 consumer (load_diff_rejections) がそのまま拾える (新規 loader 不要)
    dqs = load_diff_rejections(_critic_view(lay))
    assert len(dqs) == 1 and dqs[0].subtype == "auditor-violation"


def test_quarantine_and_audit_rejects_auditor_verdict_uncertain_with_distinct_subtype():
    """auditor.verdict='uncertain' は reject と同じ bucket (build に進まない) だが、
    WAL/digest 上の subtype は 'auditor-uncertain' で区別する (規律3、敵対レビュー 2026-07-10)。"""
    d = _mk_template_dir()
    digest = _digest_for(d)
    auditor = S.AuditorVerdict(verdict="uncertain", diff_digest=digest,
                               uncertainty="write_set_ サイズが小さく SWO 違反が顕在化しない可能性")
    coder = S.CoderProposalSort(axis=S.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("auditunc")
    gate = S._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
    assert gate["digest"]["subtype"] == "auditor-uncertain"
    dqs = load_diff_rejections(_critic_view(lay))
    assert dqs[0].subtype == "auditor-uncertain"
    assert dqs[0].subtype != "auditor-violation"


def test_render_rejections_uses_auditor_hint_for_auditor_subtypes():
    """render_rejections が auditor-* subtype には diff-quarantine 用の読み方でなく
    auditor 専用の読み方ヒントを出す (critic.digest の微修正、敵対レビュー 2026-07-10)。"""
    from critic.digest import render_rejections
    d = _mk_template_dir()
    digest = _digest_for(d)
    auditor = S.AuditorVerdict(verdict="reject", diff_digest=digest, violations=[{"type": 15}])
    coder = S.CoderProposalSort(axis=S.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("renderhint")
    S._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
    out = render_rejections(
        [], [], {}, None,
        diff_rejections=load_diff_rejections(_critic_view(lay)),
    )
    assert "auditor" in out
    assert "フレーム/hole 逸脱" not in out.split("auditor-violation")[-1][:400]


# ==== load_proposal_file (schema 検証) ==========================================

def _base_proposal() -> dict:
    return {"planner": {"axis": S.MARKER_ID, "direction": "increase", "magnitude": "small"},
           "coder": {"axis": S.MARKER_ID, "implementation": _CLEAN_IMPL}}


def _write_json(obj: dict, name: str) -> str:
    p = os.path.join(tempfile.mkdtemp(prefix="izanagi_s5sortprop_"), name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def test_load_proposal_file_requires_auditor_key():
    """auditor トップレベルキーが欠落 → KeyError (`.get()` に頼らない fails-closed)。"""
    p = _write_json(_base_proposal(), "no_auditor.json")
    try:
        S.load_proposal_file(p)
        raise AssertionError("auditor 欠落を素通しした")
    except KeyError:
        pass


def test_load_proposal_file_rejects_unknown_verdict():
    obj = {**_base_proposal(), "auditor": {"verdict": "maybe", "diff_digest": "a" * 64}}
    p = _write_json(obj, "bad_verdict.json")
    try:
        S.load_proposal_file(p)
        raise AssertionError("未知の verdict を素通しした")
    except S.AuditorGateFailure as e:
        assert "verdict" in str(e)


def test_load_proposal_file_rejects_empty_diff_digest():
    obj = {**_base_proposal(), "auditor": {"verdict": "pass", "diff_digest": ""}}
    p = _write_json(obj, "empty_digest.json")
    try:
        S.load_proposal_file(p)
        raise AssertionError("空 diff_digest を素通しした")
    except S.AuditorGateFailure as e:
        assert "diff_digest" in str(e)


def test_load_proposal_file_rejects_nonstring_diff_digest():
    obj = {**_base_proposal(), "auditor": {"verdict": "pass", "diff_digest": 12345}}
    p = _write_json(obj, "nonstr_digest.json")
    try:
        S.load_proposal_file(p)
        raise AssertionError("非文字列 diff_digest を素通しした")
    except S.AuditorGateFailure:
        pass


def test_load_proposal_file_rejects_pass_with_correctness_violations():
    """現役 sort driver も共有 parser 境界で矛盾した pass を閉じる。"""
    obj = {**_base_proposal(),
          "auditor": {"verdict": "pass", "diff_digest": "a" * 64,
                      "violations": [{"type": 14}]}}
    p = _write_json(obj, "pass_with_violations.json")
    try:
        S.load_proposal_file(p)
        raise AssertionError("correctness violations 付き pass を素通しした")
    except S.AuditorGateFailure:
        pass


def test_load_proposal_file_roundtrip():
    obj = {**_base_proposal(),
          "auditor": {"verdict": "pass", "diff_digest": "a" * 64,
                      "violations": [], "nits": [{"note": "n1"}],
                      "proposed_tests": [], "uncertainty": "u"},
          "prior_critic_reverse": True}
    p = _write_json(obj, "ok.json")
    planner, coder, auditor, prior = S.load_proposal_file(p)
    assert planner.axis == S.MARKER_ID and planner.direction == "increase"
    assert coder.implementation == _CLEAN_IMPL
    assert not hasattr(coder, "value")  # sort 軸に value フィールドは存在しない
    assert auditor.verdict == "pass" and auditor.diff_digest == "a" * 64
    assert auditor.nits == [{"note": "n1"}]
    assert prior is True


def test_load_proposal_file_rejects_nonbool_prior_reverse():
    obj = {**_base_proposal(),
          "auditor": {"verdict": "pass", "diff_digest": "a" * 64},
          "prior_critic_reverse": "true"}
    p = _write_json(obj, "badprior.json")
    try:
        S.load_proposal_file(p)
        raise AssertionError("非 bool prior_critic_reverse を素通しした")
    except ValueError as e:
        assert "prior_critic_reverse" in str(e)


# ==== default_cfg (S2 verify 配線、敵対レビュー 2026-07-10 必須修正) =============

def test_default_cfg_wires_s2_verify():
    """D41 の採用根拠 (S2 が hot key 競合を実際に踏む) をこの driver 自身でも満たすため、
    search_config に legacy+s2 が明記されていること (敵対レビュー 2026-07-10)。"""
    cfg = S.default_cfg()
    assert cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2


def test_default_cfg_axis_is_sort_marker():
    cfg = S.default_cfg()
    assert cfg.search_config.get("axis") == S.MARKER_ID
    assert cfg.ccbench_commit == S.PIN == "d706650"


# ==== drive_iteration (checkpoint 継続、backoff 版と同型) ======================

def test_drive_iteration_stops_before_running_when_reverse_exhausted():
    """入口停止: reverse-exhausted なら run_one_iteration を呼ばず (ran=False)。
    sub に不在パスを渡しても到達しないことが実行前停止の証拠。"""
    lay = _tmp_layout("stopbefore")
    seed = L.LoopState(iteration=0, start_wall=time.time(),
                       reverse_recommendations=L.REVERSE_STREAK - 1)
    L.save_loop_state(lay, seed)
    cfg, perf = S.default_cfg(), S.default_perf()
    pl = _planner()
    cd = S.CoderProposalSort(axis=S.MARKER_ID, implementation=_CLEAN_IMPL)
    au = S.AuditorVerdict(verdict="pass", diff_digest="a" * 64)
    out = S.drive_iteration(cfg, perf, pl, cd, au, prior_critic_reverse=True,
                            sub="/nonexistent/should/not/be/touched",
                            do_build=False, layout=lay)
    assert out["ran"] is False
    assert out["stop_reason"] == "reverse-exhausted"
    st = L.load_loop_state(lay)
    assert st.reverse_recommendations == L.REVERSE_STREAK


def test_drive_iteration_recovers_real_wal_start_before_entry_stop():
    lay = _tmp_layout("recover-before-stop")
    cfg, perf = S.default_cfg(), S.default_perf()
    wal.write_lock(lay, ident.canonical_preimage(cfg))
    wal.log(lay, "crashed-v", "build_start", "test-env", {
        "build_attempt_id": "crashed-attempt",
    })
    seed = L.LoopState(
        iteration=0, start_wall=time.time(),
        reverse_recommendations=L.REVERSE_STREAK - 1,
    )
    L.save_loop_state(lay, seed)
    planner = _planner()
    coder = S.CoderProposalSort(
        axis=S.MARKER_ID, implementation=_CLEAN_IMPL,
    )
    auditor = S.AuditorVerdict(verdict="pass", diff_digest="a" * 64)

    out = S.drive_iteration(
        cfg, perf, planner, coder, auditor, prior_critic_reverse=True,
        sub="/must/not/run", do_build=False, layout=lay,
    )
    assert out["ran"] is False
    records = wal.read_records(lay)
    assert [record.stage for record in records] == ["build_start", "abort"]
    assert records[-1].payload == {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": "crashed-attempt",
    }


def test_inner_run_recovers_reject_start_before_writing_retry_start():
    import contextlib
    from unittest import mock
    from campaign import patchharness

    lay = _tmp_layout("inner-reject-recovery")
    cfg, perf = S.default_cfg(), S.default_perf()
    wal.write_lock(lay, ident.canonical_preimage(cfg))
    implementation = "#define EVIL 1\n" + _CLEAN_IMPL
    variant = L.diffq_variant_id(_G, implementation)
    wal.log(lay, variant, "build_start", "test-env", {
        "genome": _G.canonical(), "src_token": "",
        "build_attempt_id": "crashed-reject-attempt",
    })
    coder = S.CoderProposalSort(
        axis=S.MARKER_ID, implementation=implementation,
    )
    auditor = S.AuditorVerdict(
        verdict="pass", diff_digest="not-reached-before-quarantine-reject",
    )
    state = L.LoopState(start_wall=time.time())

    with mock.patch.object(
            patchharness, "applied",
            side_effect=lambda *_args, **_kwargs: contextlib.nullcontext()):
        out = S.run_one_iteration(
            cfg, perf, _planner(), coder, auditor, state, _mk_template_dir(),
            do_build=False, layout=lay, log=lambda *_args: None,
        )

    assert out["outcome"] == "rejected"
    records = wal.read_records(lay)
    assert [record.stage for record in records] == [
        "build_start", "abort", "build_start", "abort",
    ]
    assert records[1].payload == {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": "crashed-reject-attempt",
    }
    assert records[2].payload["build_attempt_id"] != "crashed-reject-attempt"


def test_drive_iteration_checkpoint_survives_across_calls():
    """fresh reject が identity を確立し、次候補の public drive が resume できる。"""
    import contextlib
    from unittest import mock
    from campaign import patchharness

    sub = _mk_template_dir()
    lay = _tmp_layout("drivereject")
    cfg, perf = S.default_cfg(), S.default_perf()
    pl = _planner()
    bad_impl = "#define EVIL 1\n" + _CLEAN_IMPL
    cd = S.CoderProposalSort(axis=S.MARKER_ID, implementation=bad_impl)
    au = S.AuditorVerdict(verdict="pass", diff_digest="irrelevant-hole-escape-precedes-gate")
    with mock.patch.object(
            patchharness, "applied",
            side_effect=lambda *_a, **_k: contextlib.nullcontext()):
        out1 = S.drive_iteration(
            cfg, perf, pl, cd, au, None, sub, do_build=False, layout=lay,
        )
    assert out1["ran"] is True and out1["outcome"] == "rejected" and out1["iteration"] == 1
    assert wal.read_lock(lay) == ident.canonical_preimage(cfg)
    st = L.load_loop_state(lay)
    assert len(st.whiteboard) == 1 and st.whiteboard[0].result == "rejected"
    next_cd = S.CoderProposalSort(
        axis=S.MARKER_ID, implementation="#define EVIL_NEXT 1\n" + _CLEAN_IMPL,
    )
    with mock.patch.object(
            patchharness, "applied",
            side_effect=lambda *_a, **_k: contextlib.nullcontext()):
        out2 = S.drive_iteration(
            cfg, perf, pl, next_cd, au, None, sub, do_build=False, layout=lay,
        )
    assert out2["iteration"] == 2 and out2["outcome"] == "rejected"
    st = L.load_loop_state(lay)
    assert len(st.whiteboard) == 2 and st.iteration == 2


if __name__ == "__main__":
    import pytest as _pytest
    raise SystemExit(_pytest.main([__file__, "-v"]))
