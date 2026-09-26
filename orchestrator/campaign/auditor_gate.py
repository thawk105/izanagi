# -*- coding: utf-8 -*-
"""auditor 機械 gate の軸非依存部品 (コード片軸の標準装備。D43 で新設 → 2 軸目で共有昇格)。

D41 条件 4 の機械化 (D43): auditor の verdict を「宣言止まり」(照合なしの verdict 参照 =
fail-open) にせず、auditor が審査した working_diff の sha256 (`diff_digest`) を proposal
JSON の必須フィールドにして、driver が `quarantine()` の実際に生成する working_diff の
digest と機械照合する。不一致は `AuditorGateFailure` で即停止 (fails-closed)。この digest は
attribution/provenance 専用であり、auditor は **mandatory deny-only veto; affirmative
security credit なし**である。

本モジュールは sort 軸 driver (`p3_s4_loop_sort.py`, D43) で新設された機構から**軸非依存の
部品だけ**を抽出したもの (段 8a E 段設計レビュー 2026-07-12 must-fix: `_quarantine_and_audit`
/`_auditor_reject_result` は MARKER_ID/SOURCE_REL/ENV_TAG 等の軸定数に閉じるため移動せず、
各 driver に wrapper として残す — 「純粋移動」は成立しない)。軸固有の文脈 (marker/source)
は引数で受ける。兄弟 driver 間 import (trigger → sort) はレイヤ違反のため不可
(axis-onboarding §1 脚注の「偵察器が E 段 driver を import する歴史的経緯を踏襲しない」と
同型)。
"""
from __future__ import annotations

import hashlib
from dataclasses import InitVar, dataclass, field
from typing import Dict, List

from .diff_quarantine import DiffQuarantineResult
from ..critic.digest import DIFF_QUARANTINE_REASON

_AUDITOR_VERDICTS = {"pass", "reject", "uncertain"}
_VIOLATION_FIELDS = frozenset({
    "type", "location", "correctness_impact", "verifier_blind_spot",
    # Legacy fixtures used these two fixed fields before the closed projection.
    "note", "reason",
})
_NIT_KEYSETS = (
    frozenset({"type"}),
    frozenset({"finding"}),
    frozenset({"note"}),
)
_PROPOSED_TEST_FIELDS = frozenset({
    "mutation", "expected_gate", "machine_judgment",
})


def _reject_schema(field: str) -> None:
    # Raw entry values are deliberately absent from this message.  Auditor input
    # is untrusted and may contain a candidate wire/mask which must not escape in
    # exception text.
    raise AuditorGateFailure(
        f"auditor.{field} が閉じた構造化 schema に一致しない (規律2/6)"
    )


def _validate_auditor_entries(
    violations: object, nits: object, proposed_tests: object,
    *, max_violation_type: int = 21,
) -> None:
    if type(max_violation_type) is not int or max_violation_type < 1:
        _reject_schema('max_violation_type')
    if type(violations) is not list:
        _reject_schema("violations")
    for entry in violations:
        if (
            type(entry) is not dict
            or "type" not in entry
            or not set(entry) <= _VIOLATION_FIELDS
            or type(entry["type"]) is not int
            or not 1 <= entry["type"] <= max_violation_type
            or any(type(value) is not str for key, value in entry.items()
                   if key != "type")
        ):
            _reject_schema("violations")

    if type(nits) is not list:
        _reject_schema("nits")
    for entry in nits:
        if type(entry) is not dict or frozenset(entry) not in _NIT_KEYSETS:
            _reject_schema("nits")
        key = next(iter(entry))
        if key == "type":
            if entry[key] != "nit":
                _reject_schema("nits")
        elif type(entry[key]) is not str:
            _reject_schema("nits")

    if type(proposed_tests) is not list:
        _reject_schema("proposed_tests")
    for entry in proposed_tests:
        if (
            type(entry) is not dict
            or frozenset(entry) != _PROPOSED_TEST_FIELDS
            or any(type(value) is not str for value in entry.values())
        ):
            _reject_schema("proposed_tests")


def _validate_auditor_scalars(
    verdict: object, diff_digest: object, uncertainty: object,
) -> None:
    if type(verdict) is not str or verdict not in _AUDITOR_VERDICTS:
        raise AuditorGateFailure(
            f"auditor.verdict は {sorted(_AUDITOR_VERDICTS)} のいずれか — "
            "未知の値は fails-closed で拒否 (規律2)"
        )
    if type(diff_digest) is not str or not diff_digest:
        raise AuditorGateFailure(
            "auditor.diff_digest が空/非文字列 — working_diff と機械照合できない"
        )
    if type(uncertainty) is not str:
        raise AuditorGateFailure(
            "auditor.uncertainty は string のみ — 構造化監査結果を拒否"
        )


def _validate_auditor_consistency(
    verdict: str, violations: List[Dict], uncertainty: str,
) -> None:
    if verdict == "pass" and violations:
        raise AuditorGateFailure(
            "auditor.verdict='pass' なのに correctness violations が非空 — 正しさ違反を "
            "pass にできない (規律2)"
        )
    if verdict == "reject" and not violations:
        raise AuditorGateFailure(
            "auditor.verdict='reject' なのに correctness violations が空 — reject の根拠を "
            "構造化して返す必要がある (規律3)"
        )
    if verdict == "uncertain" and (violations or not uncertainty.strip()):
        raise AuditorGateFailure(
            "auditor.verdict='uncertain' は violations が空かつ uncertainty が非空であることが "
            "必須 — correctness 違反は reject、根拠なし uncertain は fails-closed (規律2/3)"
        )


@dataclass
class AuditorVerdict:
    """auditor (subagent_type='auditor') の構造化出力 (D41 条件4 の機械 gate)。

    **mandatory deny-only veto; affirmative security credit なし**。`diff_digest` は
    attribution/provenance 専用であり、auditor が審査した working_diff
    (`--preview-diff` が生成したもの) の sha256 hexdigest。driver はこれを実際に
    `quarantine()` が生成する working_diff の digest と突合する — 「この iteration の
    この diff を実際に見た判定か」を機械確認する (敵対レビュー 2026-07-10、backoff の
    `assert_value_literal_consistent` と同型の自己矛盾検出)。"""
    verdict: str                      # pass | reject | uncertain
    diff_digest: str
    violations: List[Dict] = field(default_factory=list)
    nits: List[Dict] = field(default_factory=list)
    proposed_tests: List[Dict] = field(default_factory=list)
    uncertainty: str = ""
    max_violation_type: InitVar[int] = 21

    def __post_init__(self, max_violation_type: int) -> None:
        _validate_auditor_scalars(
            self.verdict, self.diff_digest, self.uncertainty,
        )
        _validate_auditor_entries(
            self.violations, self.nits, self.proposed_tests,
            max_violation_type=max_violation_type,
        )


class AuditorGateFailure(ValueError):
    """auditor gate の機械的整合性が破れた (規律6、敵対レビュー 2026-07-10)。

    - diff_digest 不一致: auditor が審査した diff と実際に build/検疫される diff が
      食い違う (メインセッションの伝達ミス・古い verdict の使い回し・入れ替えのいずれか
      を示す — 悪意の有無を問わず「整合が機械確認できない」時点で fails-closed に倒す)。
    - proposal JSON の `auditor` フィールド欠落・verdict が未知の値: schema 違反。

    backoff 軸の `AttributionMismatch` と同型の設計 — 「整合規約」を harness が機械照合し、
    破れたら reject (WAL 記録して次提案へ) でなく即例外で止める (メインセッションが catch
    し、必要なら diff を作り直して auditor に再審査させる想定)。"""


def compute_diff_digest(working_diff: str) -> str:
    """working_diff (unified diff テキスト) の sha256 hexdigest。auditor gate の機械照合対象。"""
    return hashlib.sha256(working_diff.encode("utf-8")).hexdigest()


def assert_digest_matches(auditor: AuditorVerdict, working_diff: str) -> str:
    """照合コア: 実 working_diff の digest と auditor.diff_digest を突合する。

    不一致は `AuditorGateFailure` (帰属汚染 — 宣言でなく機械照合)。一致すれば実 digest を
    返す。"""
    actual = compute_diff_digest(working_diff)
    if actual != auditor.diff_digest:
        raise AuditorGateFailure(
            "帰属汚染: auditor.diff_digest と実際の working_diff の digest が不一致 — "
            "auditor が審査した diff と実際に build/検疫される diff が "
            f"食い違う (規律6、宣言でなく機械照合、敵対レビュー 2026-07-10)")
    return actual


def apply_mandatory_deny_only_veto(
    machine_result: DiffQuarantineResult,
    auditor: AuditorVerdict,
    working_diff: str,
    *,
    diff_region: str,
    template_diff_id: str,
    max_violation_type: int = 21,
) -> DiffQuarantineResult:
    """Apply a mandatory deny-only veto; affirmative security credit なし.

    Machine reject is returned unchanged.  On machine pass, ``diff_digest`` is
    checked for attribution/provenance only and every mutable auditor field is
    revalidated at this sink.  Auditor pass returns the original machine-pass
    object; reject/uncertain can only narrow that result.
    """
    if not machine_result.passed:
        return machine_result

    _validate_auditor_scalars(
        auditor.verdict, auditor.diff_digest, auditor.uncertainty,
    )
    _validate_auditor_entries(
        auditor.violations, auditor.nits, auditor.proposed_tests,
        max_violation_type=max_violation_type,
    )
    assert_digest_matches(auditor, working_diff)
    _validate_auditor_consistency(
        auditor.verdict, auditor.violations, auditor.uncertainty,
    )

    if auditor.verdict == "pass":
        return machine_result
    subtype = (
        "auditor-uncertain"
        if auditor.verdict == "uncertain"
        else "auditor-violation"
    )
    return auditor_reject_result(
        subtype,
        auditor,
        diff_region=diff_region,
        template_diff_id=template_diff_id,
        max_violation_type=max_violation_type,
    )


def auditor_reject_result(subtype: str, auditor: AuditorVerdict, *,
                          diff_region: str, template_diff_id: str,
                          max_violation_type: int = 21) -> DiffQuarantineResult:
    """auditor gate reject を diff-quarantine 経路 (`record_diff_reject` /
    `load_diff_rejections` / `render_rejections`) に相乗りさせる合成結果。

    新規 loader/renderer を作らず既存 consumer をそのまま再利用する (auditor.md 型5
    「consumer 取り残し」を自ら再演しない、敵対レビュー 2026-07-10)。WAL 上の `reason` は
    既存の `DIFF_QUARANTINE_REASON` と揃え (`load_diff_rejections` がこれでフィルタする)、
    `digest["subtype"]` だけ `auditor-violation`/`auditor-uncertain` で区別する (規律3:
    reject と uncertain を同一 bucket にしない)。軸固有の識別 (diff_region/
    template_diff_id) は呼び手 (各 driver の wrapper) が自軸定数を注入する。"""
    # Lists remain mutable for compatibility with the existing dataclass API,
    # so the recipient sink revalidates immediately before projection.
    _validate_auditor_scalars(
        auditor.verdict, auditor.diff_digest, auditor.uncertainty,
    )
    _validate_auditor_entries(
        auditor.violations, auditor.nits, auditor.proposed_tests,
        max_violation_type=max_violation_type,
    )
    evidence_parts = []
    if auditor.violations:
        codes = ",".join(
            f"type-{entry['type']}" for entry in auditor.violations
        )
        evidence_parts.append(f"violations={codes}")
    if auditor.nits:
        evidence_parts.append(f"nits={len(auditor.nits)}")
    reason = f"auditor verdict={auditor.verdict} ({len(auditor.violations)} violations)"
    return DiffQuarantineResult(
        passed=False, reason=reason,
        digest={"rejection_type": DIFF_QUARANTINE_REASON, "subtype": subtype,
                "reason": reason, "diff_region": diff_region,
                "template_diff_id": template_diff_id,
                "evidence": "; ".join(evidence_parts) or "(詳細なし)"})


def parse_auditor_dict(a: Dict, *, max_violation_type: int = 21) -> AuditorVerdict:
    """proposal JSON の `auditor` オブジェクトを fails-closed に検証して読む。

    verdict が未知の値・diff_digest が空/非文字列・list[dict] / string の型契約違反・
    verdict と correctness violations の矛盾は `AuditorGateFailure` (規律2、敵対レビュー
    2026-07-10)。`pass` は violations なし、`reject` は violations あり、`uncertain` は
    violations なし + 非空 uncertainty に限定する。呼び手はトップレベルの `auditor`
    キー自体を `d["auditor"]` で取り出すこと (`.get()` に頼らない — 欠落は KeyError で
    fails-closed)。"""
    verdict = a["verdict"]
    digest = a["diff_digest"]
    uncertainty = a.get("uncertainty", "")
    _validate_auditor_scalars(verdict, digest, uncertainty)

    typed_lists = {}
    for key in ("violations", "nits", "proposed_tests"):
        value = a.get(key, [])
        typed_lists[key] = value
    _validate_auditor_entries(
        typed_lists["violations"], typed_lists["nits"],
        typed_lists["proposed_tests"],
        max_violation_type=max_violation_type,
    )

    violations = typed_lists["violations"]
    _validate_auditor_consistency(verdict, violations, uncertainty)

    return AuditorVerdict(
        verdict=verdict, diff_digest=digest,
        violations=violations, nits=typed_lists["nits"],
        proposed_tests=typed_lists["proposed_tests"], uncertainty=uncertainty,
        max_violation_type=max_violation_type)
