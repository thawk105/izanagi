# -*- coding: utf-8 -*-
"""auditor 機械 gate の軸非依存部品 (コード片軸の標準装備。D43 で新設 → 2 軸目で共有昇格)。

D41 条件 4 の機械化 (D43): auditor の verdict を「宣言止まり」(照合なしの verdict 参照 =
fail-open) にせず、auditor が審査した working_diff の sha256 (`diff_digest`) を proposal
JSON の必須フィールドにして、driver が `quarantine()` の実際に生成する working_diff の
digest と機械照合する。不一致は `AuditorGateFailure` で即停止 (fails-closed)。

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
from dataclasses import dataclass, field
from typing import Dict, List

from campaign.diff_quarantine import DiffQuarantineResult
from critic.digest import DIFF_QUARANTINE_REASON

_AUDITOR_VERDICTS = {"pass", "reject", "uncertain"}


@dataclass
class AuditorVerdict:
    """auditor (subagent_type='auditor') の構造化出力 (D41 条件4 の機械 gate)。

    `diff_digest`: auditor が審査した working_diff (`--preview-diff` が生成したもの) の
    sha256 hexdigest。driver はこれを実際に `quarantine()` が生成する working_diff の
    digest と突合する — 「この iteration のこの diff を実際に見た判定か」を機械確認する
    (敵対レビュー 2026-07-10、backoff の `assert_value_literal_consistent` と同型の
    自己矛盾検出)。"""
    verdict: str                      # pass | reject | uncertain
    diff_digest: str
    violations: List[Dict] = field(default_factory=list)
    nits: List[Dict] = field(default_factory=list)
    proposed_tests: List[Dict] = field(default_factory=list)
    uncertainty: str = ""


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
            f"帰属汚染: auditor.diff_digest={auditor.diff_digest!r} だが実際の working_diff の "
            f"digest={actual!r} — auditor が審査した diff と実際に build/検疫される diff が "
            f"食い違う (規律6、宣言でなく機械照合、敵対レビュー 2026-07-10)")
    return actual


def auditor_reject_result(subtype: str, auditor: AuditorVerdict, *,
                          diff_region: str, template_diff_id: str) -> DiffQuarantineResult:
    """auditor gate reject を diff-quarantine 経路 (`record_diff_reject` /
    `load_diff_rejections` / `render_rejections`) に相乗りさせる合成結果。

    新規 loader/renderer を作らず既存 consumer をそのまま再利用する (auditor.md 型5
    「consumer 取り残し」を自ら再演しない、敵対レビュー 2026-07-10)。WAL 上の `reason` は
    既存の `DIFF_QUARANTINE_REASON` と揃え (`load_diff_rejections` がこれでフィルタする)、
    `digest["subtype"]` だけ `auditor-violation`/`auditor-uncertain` で区別する (規律3:
    reject と uncertain を同一 bucket にしない)。軸固有の識別 (diff_region/
    template_diff_id) は呼び手 (各 driver の wrapper) が自軸定数を注入する。"""
    evidence_parts = []
    if auditor.violations:
        evidence_parts.append(f"violations={auditor.violations}")
    if auditor.nits:
        evidence_parts.append(f"nits={auditor.nits}")
    if auditor.uncertainty:
        evidence_parts.append(f"uncertainty={auditor.uncertainty}")
    reason = f"auditor verdict={auditor.verdict} ({len(auditor.violations)} violations)"
    return DiffQuarantineResult(
        passed=False, reason=reason,
        digest={"rejection_type": DIFF_QUARANTINE_REASON, "subtype": subtype,
                "reason": reason, "diff_region": diff_region,
                "template_diff_id": template_diff_id,
                "evidence": "; ".join(evidence_parts) or "(詳細なし)"})


def parse_auditor_dict(a: Dict) -> AuditorVerdict:
    """proposal JSON の `auditor` オブジェクトを fails-closed に検証して読む。

    verdict が未知の値・diff_digest が空/非文字列は `AuditorGateFailure` (規律2、
    敵対レビュー 2026-07-10)。呼び手はトップレベルの `auditor` キー自体を `d["auditor"]`
    で取り出すこと (`.get()` に頼らない — 欠落は KeyError で fails-closed)。"""
    verdict = a["verdict"]
    if verdict not in _AUDITOR_VERDICTS:
        raise AuditorGateFailure(
            f"auditor.verdict は {sorted(_AUDITOR_VERDICTS)} のいずれか (got {verdict!r}) — "
            f"未知の値は fails-closed で拒否 (規律2、敵対レビュー 2026-07-10)")
    digest = a["diff_digest"]
    if not isinstance(digest, str) or not digest:
        raise AuditorGateFailure(
            "auditor.diff_digest が空/非文字列 — quarantine() の working_diff と機械照合できない "
            "(fails-closed、敵対レビュー 2026-07-10)")
    return AuditorVerdict(
        verdict=verdict, diff_digest=digest,
        violations=a.get("violations", []), nits=a.get("nits", []),
        proposed_tests=a.get("proposed_tests", []), uncertainty=a.get("uncertainty", ""))
