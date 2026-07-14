# -*- coding: utf-8 -*-
"""段 8a trigger-gating 自律ループ harness (p3_s4_loop_trigger_gating) の単体テスト。

`test_p3_s4_loop_sort.py` の型 (共有機構は再検証せず、正しい軸引数での呼び出しと
軸固有の新規機構だけを固める、axis-onboarding §7.4)。本軸固有 = 構文契約の禁止識別子
grep (subtype="syntax-contract") と provenance 情報源記録の受け皿 (E 段レビュー
2026-07-12 裁定の fails-closed 群)。build/verify/bench を伴わない機械部分のみ。
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

from campaign import p3_s4_loop as L                                # noqa: E402
from campaign import p3_s4_loop_sort as SORT                        # noqa: E402
from campaign import p3_s4_loop_trigger_gating as T                 # noqa: E402
from campaign.auditor_gate import AuditorGateFailure, AuditorVerdict  # noqa: E402
from campaign.layout import CampaignLayout                          # noqa: E402
from campaign.model import Genome                                   # noqa: E402
from campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY               # noqa: E402
from campaign.pipeline import VERIFY_LEGACY_PLUS_S2                  # noqa: E402
from critic.digest import load_diff_rejections                      # noqa: E402

# 実 transaction.cc の EVOLVE-BLOCK 骨格 (trigger-gating marker) を写した fixture。
# silo-backoff-trigger-gating-variant.patch と同型 — hole は #if 枝の述語代入 1 行、
# gate 変数宣言と gated call は marker 外 (coder 不可触)。
_TEMPLATE = """#pragma once
#include "backoff.hh"

class TxExecutor {
 public:
  void abort() {
#ifndef BACKOFF_TRIGGER_GATING
#error "BACKOFF_TRIGGER_GATING must be defined"
#endif
#if BACKOFF_TRIGGER_GATING
  bool izanagi_gate_pass = true;
#endif
  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
  // izanagi Phase 3 (D48/phase3.md): coder の編集面はこの #if 枝の代入 1 行のみ。
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
  // EVOLVE-BLOCK-END silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  if (izanagi_gate_pass) {
    Backoff::backoff(FLAGS_clocks_per_us);
  }
#endif
  }
};
"""
_SRC_REL = T.SOURCE_REL
_G = Genome("silo", dict(T._BASE))
_CLEAN_IMPL = ("  izanagi_gate_pass = "
               "(izanagi_abort_reason_ != IzanagiAbortReason::kNodeVali);")
_FORBIDDEN_IMPL = "  izanagi_gate_pass = (thid_ % 2 == 0);"


def _mk_template_dir() -> str:
    d = tempfile.mkdtemp(prefix="izanagi_s8atrigloop_")
    full = os.path.join(d, _SRC_REL)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


def _tmp_layout(tag: str) -> CampaignLayout:
    return CampaignLayout(
        root=tempfile.mkdtemp(prefix=f"izanagi_s8atrigloop_{tag}_")).ensure()


def _planner() -> "L.PlannerProposal":
    return L.PlannerProposal(axis=T.MARKER_ID, direction="explore_both", magnitude="small")


def _digest_for(d: str, impl: str = _CLEAN_IMPL) -> str:
    _res, _b, _e, working_diff = L.quarantine(d, impl, marker_id=T.MARKER_ID,
                                              source_rel=_SRC_REL, write=False)
    from campaign.auditor_gate import compute_diff_digest
    return compute_diff_digest(working_diff)


# ==== 構文契約の禁止識別子 grep =================================================

def test_check_syntax_contract_clean_and_forbidden():
    assert T.check_syntax_contract(_CLEAN_IMPL) == []
    assert T.check_syntax_contract(_FORBIDDEN_IMPL) == ["thid_"]
    multi = "  izanagi_gate_pass = (thid_ > 0) && write_set_.empty();"
    assert T.check_syntax_contract(multi) == ["thid_", "write_set_"]


def test_check_syntax_contract_requires_identifier_boundary():
    """前方境界 (\\b): 別識別子の内部 (例: xthid_) にはマッチしない。合成語の前方一致
    (write_set_foo) は過検出安全側で許容 (レビュー FC-N1 裁定)。"""
    assert T.check_syntax_contract("  izanagi_gate_pass = (xthid_ > 0);") == []
    assert T.check_syntax_contract("  izanagi_gate_pass = write_set_foo;") == ["write_set_"]


def test_quarantine_and_audit_rejects_forbidden_identifier():
    """禁止識別子は diff 検疫 pass 後でも subtype='syntax-contract' で機械 reject
    (hard gate、fails-closed — auditor verdict=pass でも通らない。レビュー FC-8 裁定)。"""
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest="irrelevant-syntax-precedes-gate")
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_FORBIDDEN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("syntax")
    gate = T._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
    assert gate is not None
    assert gate["outcome"] == "rejected"
    assert gate["digest"]["subtype"] == "syntax-contract"
    assert gate["digest"]["rejection_type"] == "diff-quarantine"
    # 既存 consumer がそのまま拾える (相乗り経路)
    dqs = load_diff_rejections(lay)
    assert len(dqs) == 1 and dqs[0].subtype == "syntax-contract"
    # evidence はマッチ識別子名のみ — coder の gate 式本文を critic へ運ばない (リーク裁定)
    assert "thid_" in gate["digest"]["evidence"]
    assert "% 2 == 0" not in gate["digest"]["evidence"]
    assert state.whiteboard[-1].result == "rejected"


def test_render_rejections_uses_syntax_contract_hint():
    from critic.digest import render_rejections
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest="irrelevant")
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_FORBIDDEN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("synthint")
    T._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
    out = render_rejections([], [], {}, None, diff_rejections=load_diff_rejections(lay))
    tail = out.split("syntax-contract")[-1]
    assert "構文契約違反" in tail
    assert "フレーム/hole 逸脱" not in tail[:400]


# ==== auditor gate (共有部品の軸引数配線のみ確認 — 本体は test_auditor_gate.py) ====

def test_quarantine_and_audit_dry_pass_when_clean_and_digest_matches():
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(d))
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    gate = T._quarantine_and_audit(d, coder, auditor, _G, _tmp_layout("pass"), state,
                                   _planner(), write=False)
    assert gate is None


def test_quarantine_and_audit_raises_on_digest_mismatch():
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest="0" * 64)
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    try:
        T._quarantine_and_audit(d, coder, auditor, _G, _tmp_layout("mm"), state,
                                _planner(), write=False)
        raise AssertionError("digest 不一致を素通しした")
    except AuditorGateFailure as e:
        assert "digest" in str(e)


def test_auditor_reject_carries_trigger_axis_identity():
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="reject", diff_digest=_digest_for(d),
                             violations=[{"type": 16}])
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("audrej")
    gate = T._quarantine_and_audit(d, coder, auditor, _G, lay, state, _planner(), write=False)
    assert gate["digest"]["subtype"] == "auditor-violation"
    assert gate["digest"]["template_diff_id"] == T.MARKER_ID
    assert gate["digest"]["diff_region"] == T.SOURCE_REL


# ==== load_proposal_file (schema 検証 — 共有 parse の配線) =======================

def _write_json(obj: dict, name: str) -> str:
    p = os.path.join(tempfile.mkdtemp(prefix="izanagi_s8atrigprop_"), name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def test_load_proposal_file_roundtrip_and_fails_closed():
    base = {"planner": {"axis": T.MARKER_ID, "direction": "increase", "magnitude": "small"},
            "coder": {"axis": T.MARKER_ID, "implementation": _CLEAN_IMPL}}
    # auditor キー欠落 → KeyError (fails-closed)
    try:
        T.load_proposal_file(_write_json(base, "no_auditor.json"))
        raise AssertionError("auditor 欠落を素通しした")
    except KeyError:
        pass
    # 正常 roundtrip (coder に value フィールドは無い)
    ok = {**base, "auditor": {"verdict": "pass", "diff_digest": "a" * 64},
          "prior_critic_reverse": True}
    planner, coder, auditor, prior = T.load_proposal_file(_write_json(ok, "ok.json"))
    assert coder.implementation == _CLEAN_IMPL and not hasattr(coder, "value")
    assert auditor.verdict == "pass" and prior is True

    # uncertain は violations なし + 非空 uncertainty が必須 (共有 parser 境界)。
    bad_uncertain = {**base,
                     "auditor": {"verdict": "uncertain", "diff_digest": "b" * 64}}
    try:
        T.load_proposal_file(_write_json(bad_uncertain, "uncertain_without_reason.json"))
        raise AssertionError("根拠なし uncertain を素通しした")
    except T.AuditorGateFailure:
        pass


# ==== campaign 設定 =============================================================

def test_default_cfg_wires_s2_verify_and_axis():
    cfg = T.default_cfg()
    assert cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2
    assert cfg.search_config.get("axis") == T.MARKER_ID
    assert cfg.ccbench_commit == T.PIN == "d706650"


def test_default_cfg_identity_distinct_from_sort():
    """spec_slug/search_tag/trial は sort から流用しない — campaign 出力の軸別分離
    (レビュー regression SF3 裁定)。"""
    cfg, scfg = T.default_cfg(), SORT.default_cfg()
    assert cfg.spec_slug != scfg.spec_slug
    assert cfg.search_tag != scfg.search_tag
    assert cfg.trial != scfg.trial


# ==== provenance 情報源記録 (E 段レビュー 2026-07-12 裁定の fails-closed 群) ======

def test_provenance_header_writes_sources_gate_record_and_firewall():
    lay = _tmp_layout("provhdr")
    T._write_provenance_header(lay)
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["axis"] == T.MARKER_ID and prov["pin"] == T.PIN
    assert len(prov["information_sources"]) >= len(T.INFORMATION_SOURCES)
    assert any("不読" in s["role"] for s in prov["information_sources"])
    assert set(prov["gate_record"]) == {"basis", "approval", "firewall_scope"}
    assert prov["liveness_binary"] == "alive"
    assert prov["entries"] == {}
    # 偵察診断キーの否定 assert (リークレンズ SF1 裁定)
    assert not ({"effective_reasons", "floor_cv", "freq_source"} & set(prov))


def test_provenance_header_fails_closed_on_empty_sources(monkeypatch):
    monkeypatch.setattr(T, "INFORMATION_SOURCES", ())
    lay = _tmp_layout("provempty")
    try:
        T._write_provenance_header(lay)
        raise AssertionError("INFORMATION_SOURCES 空を素通しした")
    except ValueError as e:
        assert "情報源" in str(e)
    assert not os.path.exists(T._provenance_path(lay))


def test_provenance_header_unions_extra_sources_across_rewrites():
    """--extra-source の追記分は、extra 再指定なしの header 焼き直し (次 iteration 相当)
    でも消えない。07-12 (5) real 裁定の恒久修正 (回避策「毎回再指定」の廃止) の回帰テスト。"""
    lay = _tmp_layout("provunion")
    extra = {"path": "output/insights/some-review.md", "role": "grep 部分読み"}
    T._write_provenance_header(lay, extra_sources=(extra,))
    T._write_provenance_header(lay)  # 再指定なしの焼き直し
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    paths = [s["path"] for s in prov["information_sources"]]
    assert extra["path"] in paths, "動的追加分が焼き直しで消えた (上書き置換への退行)"
    assert paths.count(extra["path"]) == 1, "union の重複排除が壊れた"
    for src in T.INFORMATION_SOURCES:
        assert src["path"] in paths, "固定定数分が union から欠落した"
    assert len(paths) == len(set(paths)), "information_sources に重複 path がある"


def test_provenance_write_rejects_recon_diagnostic_keys():
    lay = _tmp_layout("provforbid")
    try:
        T._write_provenance(lay, {"axis": T.MARKER_ID, "effective_reasons": ["lc"]})
        raise AssertionError("偵察診断キーを素通しした")
    except ValueError as e:
        assert "effective_reasons" in str(e)


def test_provenance_entry_merge_preserves_existing_and_is_idempotent():
    lay = _tmp_layout("provmerge")
    T._write_provenance_header(lay)
    T._append_provenance_entry(lay, 1, {"outcome": "rejected", "variant": None,
                                        "proposal_path": "p1.json",
                                        "auditor_diff_digest": "a" * 64})
    # ヘッダ再書き (次 iteration 入口) で entries が truncate されない
    T._write_provenance_header(lay)
    # 同 iteration キーの上書き = 冪等 (再実行、regression SF2 裁定)
    T._append_provenance_entry(lay, 1, {"outcome": "duplicate", "variant": "v1",
                                        "proposal_path": "p1.json",
                                        "auditor_diff_digest": "a" * 64})
    T._append_provenance_entry(lay, 2, {"outcome": "certified", "variant": "v2",
                                        "proposal_path": "p2.json",
                                        "auditor_diff_digest": "b" * 64})
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert set(prov["entries"]) == {"1", "2"}
    assert prov["entries"]["1"]["outcome"] == "duplicate"
    assert prov["information_sources"]     # ヘッダも健在


def test_provenance_preserves_unknown_keys_forward_compat():
    """スキーマ進化した既存ファイルの未知キーを merge で捨てない (レビュー FC-3 裁定)。"""
    lay = _tmp_layout("provfwd")
    os.makedirs(os.path.dirname(T._provenance_path(lay)), exist_ok=True)
    with open(T._provenance_path(lay), "w", encoding="utf-8") as f:
        json.dump({"future_key": "keep-me", "entries": {"9": {"outcome": "certified"}}}, f)
    T._write_provenance_header(lay)
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["future_key"] == "keep-me"
    assert prov["entries"]["9"]["outcome"] == "certified"


def test_provenance_corrupt_file_quarantined_and_raises():
    """decode 不能は .corrupt.* へ退避して例外停止 — silent reset (記録義務の黙殺) も
    そのまま brick も避ける (レビュー FC-3 × regression SF4 の折衷裁定)。"""
    lay = _tmp_layout("provcorrupt")
    path = T._provenance_path(lay)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"truncated": ')
    try:
        T._load_provenance(lay)
        raise AssertionError("破損 JSON を素通しした")
    except RuntimeError as e:
        assert "破損" in str(e)
    assert not os.path.exists(path)
    corrupts = [n for n in os.listdir(os.path.dirname(path)) if ".corrupt." in n]
    assert len(corrupts) == 1


def test_parse_extra_source():
    assert T.parse_extra_source("docs/x.md:読了 — 追加参照") == {
        "path": "docs/x.md", "role": "読了 — 追加参照"}
    # ROLE 内コロン許容 (最初のコロンのみで分割、レビュー FC-6 裁定)
    assert T.parse_extra_source("a.md:role: with colon")["role"] == "role: with colon"
    for bad in ("no-colon", ":role-only", "path-only:", "  :  "):
        try:
            T.parse_extra_source(bad)
            raise AssertionError(f"malformed {bad!r} を素通しした")
        except ValueError:
            pass


# ==== drive_iteration (checkpoint 継続 + provenance funnel) =====================

def test_drive_iteration_stops_before_running_but_writes_header():
    """入口停止でも provenance ヘッダは焼かれる (ヘッダは入口 = build 前、FC-1(a))。
    sub に不在パスを渡しても到達しないことが実行前停止の証拠。"""
    lay = _tmp_layout("stopbefore")
    seed = L.LoopState(iteration=0, start_wall=time.time(),
                       reverse_recommendations=L.REVERSE_STREAK - 1)
    L.save_loop_state(lay, seed)
    cfg, perf = T.default_cfg(), T.default_perf()
    cd = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    au = AuditorVerdict(verdict="pass", diff_digest="a" * 64)
    out = T.drive_iteration(cfg, perf, _planner(), cd, au, prior_critic_reverse=True,
                            sub="/nonexistent/should/not/be/touched",
                            do_build=False, layout=lay)
    assert out["ran"] is False
    assert out["stop_reason"] == "reverse-exhausted"
    assert os.path.exists(T._provenance_path(lay))


def _pinned_clean_sub_or_skip():
    import subprocess
    import pytest
    root = os.path.dirname(_ORCH)
    sub = os.path.join(root, "external", "ccbench")
    try:
        head = subprocess.check_output(["git", "-C", sub, "rev-parse", "--short", "HEAD"],
                                       text=True).strip()
        dirty = subprocess.check_output(["git", "-C", sub, "status", "--porcelain"],
                                        text=True).strip()
    except Exception:
        pytest.skip("submodule 未取得")
    if not head.startswith(T.PIN[:7]) or dirty:
        pytest.skip(f"submodule が pinned-clean でない (head={head} dirty={bool(dirty)}, "
                    f"要求 pin={T.PIN})")
    return sub


def test_drive_iteration_writes_entry_and_checkpoint(monkeypatch):
    """--run-iteration 実経路 (funnel) で entry が焼かれる。reject 経路 (do_build=False、
    実 submodule 要 — pinned-clean でなければ skip)。"""
    sub = _pinned_clean_sub_or_skip()
    lay = _tmp_layout("driveprov")
    cfg, perf = T.default_cfg(), T.default_perf()
    bad = T.CoderProposalTriggerGating(axis=T.MARKER_ID,
                                       implementation="#define EVIL 1\n" + _CLEAN_IMPL)
    au = AuditorVerdict(verdict="pass", diff_digest="irrelevant-hole-escape-precedes-gate")
    out = T.drive_iteration(cfg, perf, _planner(), bad, au, None, sub, do_build=False,
                            layout=lay, proposal_path="/scratch/prop1.json")
    assert out["ran"] is True and out["outcome"] == "rejected" and out["iteration"] == 1
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["entries"]["1"]["outcome"] == "rejected"
    assert prov["entries"]["1"]["proposal_path"] == "/scratch/prop1.json"
    st = L.load_loop_state(lay)
    assert st.iteration == 1 and st.whiteboard[0].result == "rejected"


def test_drive_iteration_entry_failure_blocks_checkpoint(monkeypatch):
    """provenance entry が書けない iteration は checkpoint を前進させない (FC-1(b) 裁定 —
    「WAL/checkpoint は進んだが記録なし」の中途半端を作らない)。"""
    sub = _pinned_clean_sub_or_skip()
    lay = _tmp_layout("provblock")
    cfg, perf = T.default_cfg(), T.default_perf()
    bad = T.CoderProposalTriggerGating(axis=T.MARKER_ID,
                                       implementation="#define EVIL 1\n" + _CLEAN_IMPL)
    au = AuditorVerdict(verdict="pass", diff_digest="irrelevant")

    def boom(layout, iteration, entry):
        raise OSError("simulated provenance write failure")
    monkeypatch.setattr(T, "_append_provenance_entry", boom)
    try:
        T.drive_iteration(cfg, perf, _planner(), bad, au, None, sub, do_build=False,
                          layout=lay)
        raise AssertionError("provenance 書き込み失敗を素通しした")
    except OSError:
        pass
    assert L.load_loop_state(lay) is None   # checkpoint は前進していない


if __name__ == "__main__":
    import pytest as _pytest
    raise SystemExit(_pytest.main([__file__, "-v"]))
