# -*- coding: utf-8 -*-
"""auditor 機械 gate 共有部品 (campaign.auditor_gate) の単体テスト。

sort 軸 driver からの共有昇格 (段 8a E 段レビュー 2026-07-12) の semantics 不変検査。
driver 経由の結合挙動 (相乗り WAL 経路・render hint) は test_p3_s4_loop_sort.py /
test_p3_s4_loop_trigger_gating.py 側が既にカバーする — ここは引数化された共有部品
そのものの契約 (照合コア・builder・fails-closed パース) を固める。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign.auditor_gate import (AuditorGateFailure, AuditorVerdict,  # noqa: E402
                                   assert_digest_matches, auditor_reject_result,
                                   compute_diff_digest, parse_auditor_dict)
from critic.digest import DIFF_QUARANTINE_REASON                        # noqa: E402


def test_assert_digest_matches_returns_actual_on_match():
    diff = "diff line 1\ndiff line 2\n"
    a = AuditorVerdict(verdict="pass", diff_digest=compute_diff_digest(diff))
    assert assert_digest_matches(a, diff) == compute_diff_digest(diff)


def test_assert_digest_matches_raises_on_mismatch():
    a = AuditorVerdict(verdict="pass", diff_digest="0" * 64)
    try:
        assert_digest_matches(a, "some diff\n")
        raise AssertionError("digest 不一致を素通しした")
    except AuditorGateFailure as e:
        assert "digest" in str(e)


def test_auditor_reject_result_carries_axis_identity_from_arguments():
    """diff_region/template_diff_id は呼び手 (driver wrapper) の軸定数がそのまま載る —
    共有 builder が特定軸の定数を焼き込んでいない (レビュー must-fix の引数化)。"""
    a = AuditorVerdict(verdict="reject", diff_digest="d" * 64,
                       violations=[{"type": 16}])
    res = auditor_reject_result("auditor-violation", a,
                                diff_region="cc/some/other.cc",
                                template_diff_id="some-axis-marker")
    assert not res.passed
    assert res.digest["rejection_type"] == DIFF_QUARANTINE_REASON
    assert res.digest["subtype"] == "auditor-violation"
    assert res.digest["diff_region"] == "cc/some/other.cc"
    assert res.digest["template_diff_id"] == "some-axis-marker"
    assert "violations" in res.digest["evidence"]


def test_auditor_reject_result_uncertain_subtype_and_empty_evidence():
    a = AuditorVerdict(verdict="uncertain", diff_digest="d" * 64)
    res = auditor_reject_result("auditor-uncertain", a,
                                diff_region="r", template_diff_id="m")
    assert res.digest["subtype"] == "auditor-uncertain"
    assert res.digest["evidence"] == "(詳細なし)"


def test_parse_auditor_dict_roundtrip():
    a = parse_auditor_dict({"verdict": "pass", "diff_digest": "a" * 64,
                            "violations": [{"type": 1}], "uncertainty": "x"})
    assert a.verdict == "pass" and a.diff_digest == "a" * 64
    assert a.violations == [{"type": 1}] and a.uncertainty == "x"


def test_parse_auditor_dict_rejects_unknown_verdict():
    try:
        parse_auditor_dict({"verdict": "maybe", "diff_digest": "a" * 64})
        raise AssertionError("未知 verdict を素通しした")
    except AuditorGateFailure:
        pass


def test_parse_auditor_dict_rejects_empty_and_nonstring_digest():
    for bad in ("", 123, None):
        try:
            parse_auditor_dict({"verdict": "pass", "diff_digest": bad})
            raise AssertionError(f"diff_digest={bad!r} を素通しした")
        except AuditorGateFailure:
            pass


def test_parse_auditor_dict_missing_keys_fail_closed():
    for obj in ({}, {"verdict": "pass"}, {"diff_digest": "a" * 64}):
        try:
            parse_auditor_dict(obj)
            raise AssertionError(f"欠落 {obj!r} を素通しした")
        except (KeyError, AuditorGateFailure):
            pass
