# -*- coding: utf-8 -*-
"""s6_proposal_rounds (D52 提案ラウンド束の実走 driver) の単体テスト。

API を呼ばない機械部分のみ: proposer 出力の三分法 (classify_proposer_output、v2 §3.3)・
採点出力の機械照合 (validate_score、採点器敵対チェック must 1)・seed 導出の決定性・
freeze→verify の配線と改変検出。freeze のテストは**モック母集団** (ダミー領域名) で回す —
実 edit_surface_map での抽出列をテストが生成・表示すると「seed の試算」(v2 §3.2 で禁止)
になるため。抽出列の中身は assert しない (件数と母集団所属のみ)。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import s6_proposal_rounds as M  # noqa: E402


def _proposal(**over):
    p = {"axis_name": "a", "mutation_type": "code_fragment",
         "hole_location": {"region": "r", "source_rel": "s", "position": "p",
                           "skeleton": "k"},
         "mechanism_hypothesis": "m", "safety_argument_hypothesis": "s",
         "unknowns": []}
    p.update(over)
    return p


def _bundle(n=1):
    return {"proposals": [_proposal() for _ in range(n)], "global_unknowns": []}


# ==== classify_proposer_output (v2 §3.3 三分法) =================================


def test_classify_parse_failure_is_supplement():
    cls, d = M.classify_proposer_output("not json {")
    assert cls == "supplement" and d["reason"] == "json-parse-failure"


def test_classify_fenced_json_is_scored():
    """amendment 2026-07-13 (ユーザー裁定 A): フェンス付き完全 JSON は整形欠陥で
    落とさない。実走 1 巡目で 5/7 attempt がこの形で supplement 化した実出力分布の反映。"""
    raw = "```json\n" + json.dumps(_bundle()) + "\n```"
    cls, _ = M.classify_proposer_output(raw)
    assert cls == "score"


def test_classify_fence_without_lang_tag_is_scored():
    raw = "```\n" + json.dumps(_bundle()) + "\n```"
    cls, _ = M.classify_proposer_output(raw)
    assert cls == "score"


def test_classify_fenced_broken_json_still_supplement():
    """フェンスを剥がしても壊れている JSON は従来どおり supplement (判定規則は不変)。"""
    cls, d = M.classify_proposer_output("```json\nnot json {\n```")
    assert cls == "supplement" and d["reason"] == "json-parse-failure"


def test_classify_unclosed_fence_unchanged():
    """フェンスが閉じていない場合は剥がさない (機械規則の閉じた定義)。"""
    cls, d = M.classify_proposer_output("```json\n" + json.dumps(_bundle()))
    assert cls == "supplement" and d["reason"] == "json-parse-failure"


def test_strip_code_fence_leaves_plain_json_untouched():
    plain = json.dumps(_bundle())
    assert M.strip_code_fence(plain) == plain


def test_classify_missing_toplevel_field_is_supplement():
    cls, _ = M.classify_proposer_output(json.dumps({"proposals": []}))
    assert cls == "supplement"  # global_unknowns の物理欠落


def test_classify_zero_proposals_goes_to_score_zero_not_supplement():
    """0 提案 = 内容的帰結 → ラウンド不適格直行。補充に流すと outcome-dependent
    exclusion (v1 レビュー must 1、2/3 レンズ収束) の再発。"""
    cls, d = M.classify_proposer_output(
        json.dumps({"proposals": [], "global_unknowns": []}))
    assert cls == "score_zero" and d["reason"] == "zero-proposals"


def test_classify_proposals_not_array_is_score_zero():
    cls, _ = M.classify_proposer_output(
        json.dumps({"proposals": "x", "global_unknowns": []}))
    assert cls == "score_zero"


def test_classify_non_dict_elements_dropped_and_recorded():
    b = {"proposals": [_proposal(), "garbage"], "global_unknowns": []}
    cls, d = M.classify_proposer_output(json.dumps(b))
    assert cls == "score"
    assert d["dropped_non_dict_indices"] == [1]
    assert len(d["bundle"]["proposals"]) == 1


def test_classify_all_non_dict_is_score_zero():
    b = {"proposals": ["g1", "g2"], "global_unknowns": []}
    cls, _ = M.classify_proposer_output(json.dumps(b))
    assert cls == "score_zero"


def test_classify_missing_proposal_field_is_supplement():
    p = _proposal()
    del p["unknowns"]
    cls, _ = M.classify_proposer_output(
        json.dumps({"proposals": [p], "global_unknowns": []}))
    assert cls == "supplement"


def test_classify_truncates_over_3_to_head_3_deterministically():
    b = _bundle(5)
    b["proposals"][3]["axis_name"] = "fourth"
    b["proposals"][4]["axis_name"] = "fifth"
    cls, d = M.classify_proposer_output(json.dumps(b))
    assert cls == "score"
    assert d["truncated"]
    assert len(d["bundle"]["proposals"]) == 3
    names = [p["axis_name"] for p in d["bundle"]["proposals"]]
    assert "fourth" not in names and "fifth" not in names  # JSON 配列順の先頭 3


# ==== validate_score (採点器敵対チェック must 1 の機械照合) =======================


def _score(eligibles, round_el=None, dea=None):
    ps = []
    for i, e in enumerate(eligibles):
        ps.append({"index": i, "c1_novel_vs_projection": e, "c1_reason": "r",
                   "c2_mechanism_substantive": e, "c2_reason": "r",
                   "c3_axis_eligible": e, "c3_reason": "r", "eligible": e})
    n_el = sum(1 for e in eligibles if e)
    return {"proposals_scored": ps,
            "round_eligible": any(eligibles) if round_el is None else round_el,
            "distinct_eligible_axes": (1 if n_el else 0) if dea is None else dea,
            "dedup_notes": "", "overall_notes": ""}


def test_validate_score_accepts_consistent():
    b = _bundle(2)
    assert M.validate_score(_score((True, False)), b) is None


def test_validate_score_rejects_count_mismatch():
    b = _bundle(2)
    assert M.validate_score(_score((True,)), b) is not None


def test_validate_score_rejects_string_round_eligible():
    """"false" (文字列) は Python truthy — 素通しすると一次エンドポイントが 1 に化ける。"""
    b = _bundle(1)
    assert M.validate_score(_score((False,), round_el="false"), b) is not None


def test_validate_score_rejects_eligible_not_and_of_criteria():
    b = _bundle(1)
    s = _score((False,))
    s["proposals_scored"][0]["eligible"] = True
    s["round_eligible"] = True
    s["distinct_eligible_axes"] = 1
    assert M.validate_score(s, b) is not None


def test_validate_score_rejects_round_eligible_not_or():
    b = _bundle(1)
    assert M.validate_score(_score((True,), round_el=False), b) is not None


def test_validate_score_rejects_dea_out_of_range():
    b = _bundle(1)
    assert M.validate_score(_score((True,), dea=5), b) is not None
    assert M.validate_score(_score((True,), dea=0), b) is not None  # 適格ありなのに 0


# ==== seed 導出 (v2 §3.2) ======================================================


def test_derive_seed_deterministic_and_purpose_separated():
    a = M.derive_seed(42, "c4-draw")
    assert a == M.derive_seed(42, "c4-draw")
    assert a != M.derive_seed(42, "exec-order")
    assert a != M.derive_seed(43, "c4-draw")


# ==== freeze → verify の配線 (モック母集団) =====================================


_TEST_SEED = 1  # モック母集団専用。実走の master seed は人間確定 (v2 §3.2)


def _mock_pi():
    regions = [f"mock/region_{i:02d}.cc" for i in range(17)]
    return {
        "diagnostics": {"mock-axis": {"status": "alive", "attribution": []}},
        "stock_excerpts": [{"region": r, "source_rel": r, "excerpt": "int x;\n"}
                           for r in regions],
        "edit_surface_map": [{"region": r, "role": "mock", "opened": False}
                             for r in regions],
    }


def _patch_paths(monkeypatch, tmp_path):
    out = tmp_path / "s6-rounds"
    monkeypatch.setattr(M, "OUT", out)
    monkeypatch.setattr(M, "FROZEN", out / "frozen")
    monkeypatch.setattr(M, "RUNS", out / "runs")
    monkeypatch.setattr(M, "ANON", out / "anon")
    monkeypatch.setattr(M, "SCORES", out / "scores")
    monkeypatch.setattr(M, "load_projected_input", _mock_pi)
    monkeypatch.setattr(M, "freshness_check", lambda: [])
    return out


def test_freeze_then_verify_roundtrip_and_tamper_detection(monkeypatch, tmp_path):
    out = _patch_paths(monkeypatch, tmp_path)
    M.cmd_freeze(argparse.Namespace(master_seed=_TEST_SEED))

    ledger = json.loads((out / "frozen/hash_ledger.json").read_text())
    regions = sorted(e["region"] for e in _mock_pi()["edit_surface_map"])
    assert len(ledger["c4_drawn_regions"]) == M.N_ROUNDS
    assert all(r in regions for r in ledger["c4_drawn_regions"])
    assert len(ledger["exec_order"]) == 60 and len(set(ledger["exec_order"])) == 60
    assert len(ledger["payload_sha256"]) == 60
    # 採点定型部が射影を埋め込み、可変部プレースホルダ 1 箇所だけ残す (v2 §5.2)
    prefix = (out / "frozen/scoring_user_prefix.txt").read_text()
    assert prefix.count("{PROPOSAL_BUNDLE_JSON}") == 1
    assert "{PROJECTED_INPUT_JSON}" not in prefix

    M.cmd_verify(argparse.Namespace())  # 無改変なら通る

    # 凍結物の改変を verify が検出する (恒真ゲートでないことの positive control、F9 型)
    p = out / "frozen/payloads/c5-00.json"
    d = json.loads(p.read_text())
    d["diagnostics"] = {"x": 1}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    with pytest.raises(SystemExit):
        M.cmd_verify(argparse.Namespace())


def test_freeze_refuses_second_run(monkeypatch, tmp_path):
    """凍結のやり直し (引き直し) は fails-closed で拒否される。"""
    _patch_paths(monkeypatch, tmp_path)
    M.cmd_freeze(argparse.Namespace(master_seed=_TEST_SEED))
    with pytest.raises(SystemExit):
        M.cmd_freeze(argparse.Namespace(master_seed=_TEST_SEED))


def test_freeze_arm_payload_single_difference(monkeypatch, tmp_path):
    """アーム差分 = 構成フィールドのみ (v2 §4) を凍結物で直接確認。"""
    out = _patch_paths(monkeypatch, tmp_path)
    M.cmd_freeze(argparse.Namespace(master_seed=_TEST_SEED))
    main0 = json.loads((out / "frozen/payloads/main-00.json").read_text())
    c4_0 = json.loads((out / "frozen/payloads/c4-00.json").read_text())
    c5_0 = json.loads((out / "frozen/payloads/c5-00.json").read_text())
    assert set(main0) == {"diagnostics", "stock_excerpts", "edit_surface_map"}
    assert set(c4_0) == set(main0) | {"hole_region_directive"}
    assert set(c5_0) == set(main0)
    assert c5_0["diagnostics"] == {}
    assert main0["diagnostics"] == c4_0["diagnostics"] != {}
    assert main0["stock_excerpts"] == c4_0["stock_excerpts"] == c5_0["stock_excerpts"]
