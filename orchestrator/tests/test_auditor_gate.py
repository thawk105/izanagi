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
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign.auditor_gate import (AuditorGateFailure, AuditorVerdict,  # noqa: E402
                                   apply_mandatory_deny_only_veto,
                                   assert_digest_matches, auditor_reject_result,
                                   compute_diff_digest, parse_auditor_dict)
from orchestrator.campaign.diff_quarantine import DiffQuarantineResult              # noqa: E402
from orchestrator.critic.digest import DIFF_QUARANTINE_REASON                        # noqa: E402


def test_violation_type_ceiling_is_per_call_and_default_stays_21():
    verdict = {'verdict': 'reject', 'diff_digest': 'a' * 64,
               'violations': [{'type': 22}]}
    try:
        parse_auditor_dict(verdict)
        raise AssertionError('default ceiling accepted type 22')
    except AuditorGateFailure:
        pass
    for kind in range(22, 27):
        verdict['violations'] = [{'type': kind}]
        assert parse_auditor_dict(verdict, max_violation_type=26).violations[0]['type'] == kind
    verdict['violations'] = [{'type': 27}]
    try:
        parse_auditor_dict(verdict, max_violation_type=26)
        raise AssertionError('policy ceiling accepted type 27')
    except AuditorGateFailure:
        pass


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


def test_mandatory_deny_only_veto_acceptance_set_never_exceeds_machine_gate():
    working_diff = "actual working diff\n"
    digest = compute_diff_digest(working_diff)
    auditors = (
        AuditorVerdict(verdict="pass", diff_digest=digest),
        AuditorVerdict(
            verdict="reject", diff_digest=digest,
            violations=[{"type": 1}],
        ),
        AuditorVerdict(
            verdict="uncertain", diff_digest=digest,
            uncertainty="closed inputs are insufficient",
        ),
    )
    machine_results = (
        DiffQuarantineResult(passed=True),
        DiffQuarantineResult(passed=False, reason="machine reject"),
    )

    for machine_result in machine_results:
        for auditor in auditors:
            combined = apply_mandatory_deny_only_veto(
                machine_result,
                auditor,
                working_diff,
                diff_region="r",
                template_diff_id="m",
            )
            assert not combined.passed or machine_result.passed
            if not machine_result.passed:
                assert combined is machine_result
            elif auditor.verdict == "pass":
                assert combined is machine_result
            else:
                assert not combined.passed


def test_mandatory_veto_revalidates_mutated_auditor_scalars_and_entries_at_sink():
    working_diff = "actual working diff\n"
    digest = compute_diff_digest(working_diff)
    machine_pass = DiffQuarantineResult(passed=True)
    mutated = []

    contradictory = AuditorVerdict(
        verdict="reject", diff_digest=digest, violations=[{"type": 1}],
    )
    contradictory.verdict = "pass"
    mutated.append(contradictory)

    invalid_entry = AuditorVerdict(verdict="pass", diff_digest=digest)
    invalid_entry.nits.append({"type": "not-a-nit"})
    mutated.append(invalid_entry)

    for auditor in mutated:
        try:
            apply_mandatory_deny_only_veto(
                machine_pass,
                auditor,
                working_diff,
                diff_region="r",
                template_diff_id="m",
            )
            raise AssertionError("事後変異した auditor verdict を素通しした")
        except AuditorGateFailure:
            pass


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
    a = parse_auditor_dict({"verdict": "reject", "diff_digest": "a" * 64,
                            "violations": [{"type": 1}], "uncertainty": "x"})
    assert a.verdict == "reject" and a.diff_digest == "a" * 64
    assert a.violations == [{"type": 1}] and a.uncertainty == "x"


def test_parse_auditor_dict_accepts_sort_closed_region_violation_codes_17_through_21():
    for code in range(17, 22):
        parsed = parse_auditor_dict({
            "verdict": "reject",
            "diff_digest": "a" * 64,
            "violations": [{"type": code}],
        })
        assert parsed.violations == [{"type": code}]


def test_parse_auditor_dict_rejects_violation_code_22():
    try:
        parse_auditor_dict({
            "verdict": "reject",
            "diff_digest": "a" * 64,
            "violations": [{"type": 22}],
        })
        raise AssertionError("gallery code 22 を素通しした")
    except AuditorGateFailure:
        pass


def test_parse_auditor_dict_accepts_consistent_pass_and_uncertain():
    passed = parse_auditor_dict({"verdict": "pass", "diff_digest": "a" * 64})
    uncertain = parse_auditor_dict({"verdict": "uncertain", "diff_digest": "b" * 64,
                                    "uncertainty": "designated source が不足"})
    assert passed.violations == []
    assert uncertain.violations == [] and uncertain.uncertainty


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


def test_parse_auditor_dict_rejects_non_list_dict_structured_fields():
    bad_values = (None, {}, "text", ["not-a-dict"], [{"ok": True}, 1])
    for key in ("violations", "nits", "proposed_tests"):
        for bad in bad_values:
            try:
                parse_auditor_dict({"verdict": "pass", "diff_digest": "a" * 64,
                                    key: bad})
                raise AssertionError(f"{key}={bad!r} を素通しした")
            except AuditorGateFailure:
                pass


def test_parse_auditor_dict_rejects_nonstring_uncertainty():
    for bad in (None, 1, [], {}):
        try:
            parse_auditor_dict({"verdict": "pass", "diff_digest": "a" * 64,
                                "uncertainty": bad})
            raise AssertionError(f"uncertainty={bad!r} を素通しした")
        except AuditorGateFailure:
            pass


def test_parse_auditor_dict_rejects_verdict_violation_contradictions():
    bad_objects = (
        {"verdict": "pass", "violations": [{"type": 1}]},
        {"verdict": "reject", "violations": []},
        {"verdict": "uncertain", "violations": [{"type": 1}], "uncertainty": "x"},
        {"verdict": "uncertain", "violations": []},
        {"verdict": "uncertain", "violations": [], "uncertainty": ""},
        {"verdict": "uncertain", "violations": [], "uncertainty": "  \t"},
    )
    for bad in bad_objects:
        try:
            parse_auditor_dict({"diff_digest": "a" * 64, **bad})
            raise AssertionError(f"矛盾した auditor verdict を素通しした: {bad!r}")
        except AuditorGateFailure:
            pass


def test_parse_auditor_dict_missing_keys_fail_closed():
    for obj in ({}, {"verdict": "pass"}, {"diff_digest": "a" * 64}):
        try:
            parse_auditor_dict(obj)
            raise AssertionError(f"欠落 {obj!r} を素通しした")
        except (KeyError, AuditorGateFailure):
            pass
