#!/usr/bin/env python3
"""docs の一貫性 lint — 2026-07-05 の文書恒久対応で導入。

背景: 2026-07-04 の文書一貫性監査で確定矛盾 39 件。根本原因の大半は
「可変状態 (完了状況・現在 Phase・次の一手) の再掲」と「行番号参照の腐敗」。
このスクリプトは禁止パターン、肥大、command から規範節への構造到達性を機械的に
検出する決定的な lint であり、規律の防壁 (hooks/) ではない。義務本文の文言保存や
意味的なずれ (チェックボックス反映漏れ等) は検出できない — それは D27 の敵対監査と
人間レビューの領分。dispatch 表から leaf reference への直接到達性は閉じるが、leaf から
別 living doc への間接委譲は検査しない既知限界がある。

使い方: python3 tools/check_docs.py   (セッション締めの手順で実行。違反あり = exit 1)
"""
from __future__ import annotations

import ast
import argparse
import hashlib
import importlib.util
import re
import stat
import sys
import time
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

from dev_waves.launch_authority import (
    AuthorityError,
    visible_top_level_matches,
    visible_top_level_lines,
)

REPO = Path(__file__).resolve().parent.parent

# spool_fold の allocator と同じ canonical decision heading。番号直後の `.` は必須。
DECISION_ID_RE = re.compile(r"^## D(?P<number>[1-9][0-9]*)\.", re.MULTILINE)
DECISION_HEADING_CANDIDATE_RE = re.compile(
    r"^## D(?P<number>[0-9]+)(?P<suffix>[^\n]*)$",
    re.MULTILINE,
)

R33_DECISION_SLUG = "t1142-n-pilot-r33-admission-authority"

R33_EXPECTED = {
    "role": "n_pilot_r33",
    "generation": "n-pilot-r33",
    "pilot_rounds": 33,
    "allocation_count": 3,
    "cell_count": 12,
    "schedule_row_count": 396,
    "decision_pin": R33_DECISION_SLUG,
}

R33_ROLE_RE = re.compile(
    r'(?m)^[ \t]*OBSERVATION_ROLE_N_PILOT_R33[ \t]*=[ \t]*'
    r'["\'](?P<role>[^"\']+)["\'][ \t]*$'
)

R33_SOURCE_ENTRY_RE = re.compile(
    r'(?ms)^[ \t]*["\']n_pilot_r33["\'][ \t]*:[ \t]*\{'
    r'(?P<body>.*?)'
    r'^[ \t]*\}[ \t]*,?[ \t]*$'
)

R33_OBSERVATION_ROLES_DECL_RE = re.compile(
    r"(?m)^[ \t]*_OBSERVATION_ROLES[ \t]*=[ \t]*\{"
)

R33_SOURCE_FIELD_RE = {
    "generation": re.compile(
        r'(?m)^[ \t]*["\']generation_id["\'][ \t]*:[ \t]*'
        r'["\'](?P<value>[^"\']+)["\'][ \t]*,?[ \t]*$'
    ),
    "pilot_rounds": re.compile(
        r'(?m)^[ \t]*["\']pilot_rounds["\'][ \t]*:[ \t]*'
        r'(?P<value>[0-9]+)[ \t]*,?[ \t]*$'
    ),
    "allocation_count": re.compile(
        r'(?m)^[ \t]*["\']allocation_count["\'][ \t]*:[ \t]*'
        r'(?P<value>[0-9]+)[ \t]*,?[ \t]*$'
    ),
    "cell_count": re.compile(
        r'(?m)^[ \t]*["\']cell_count["\'][ \t]*:[ \t]*'
        r'(?P<value>[0-9]+)[ \t]*,?[ \t]*$'
    ),
    "schedule_row_count": re.compile(
        r'(?m)^[ \t]*["\']schedule_row_count["\'][ \t]*:[ \t]*'
        r'(?P<value>[0-9]+)[ \t]*,?[ \t]*$'
    ),
    "decision_pin": re.compile(
        r'(?m)^[ \t]*["\']decision_pin["\'][ \t]*:[ \t]*'
        r'["\'](?P<value>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)["\']'
        r'[ \t]*,?[ \t]*$'
    ),
}

# _h2_section_slices() が返す heading は `## ` を除いた title。canonical
# decision は period の後にタイトルが続くため、period の直後で終端を要求しない。
R33_DECISION_HEADING_RE = re.compile(
    r"^D[1-9][0-9]*\.(?:\s|$)"
)

R33_PENDING_HEADING_RE = re.compile(
    r"^\{\{D:" + re.escape(R33_DECISION_SLUG) + r"\}\}\."
)

R33_DECISION_SLUG_RE = re.compile(
    r"(?m)^[ \t]*- authority slug:[ \t]*"
    r"`(?P<slug>t1142-n-pilot-r33-admission-authority)`[ \t]*$"
)

R33_DECISION_CONTRACT_RE = re.compile(
    r"(?m)^[ \t]*- R33 admission contract:[ \t]*"
    r"role=`(?P<role>[^`]+)`;[ \t]*"
    r"generation=`(?P<generation>[^`]+)`;[ \t]*"
    r"pilot_rounds=(?P<pilot_rounds>[0-9]+);[ \t]*"
    r"allocation_count=(?P<allocation_count>[0-9]+);[ \t]*"
    r"cell_count=(?P<cell_count>[0-9]+);[ \t]*"
    r"schedule_row_count=(?P<schedule_row_count>[0-9]+)\.[ \t]*$"
)

# living docs = 現在の状態・設計を主張する文書。ここに可変状態の再掲と行番号参照を禁止する。
# 対象外 = 追記型の日誌・記録 (書いた時点で凍結): worklog / decisions / insights / paper-story /
# docs/archive/ 配下 (監査台帳・worklog アーカイブ等の凍結族。規約は同 README — ファイル名不変で移動)、
# および完了 Phase の phase1/phase2 (2026-07-05 に冒頭へ凍結宣言済み)。
LIVING_DOCS = [
    REPO / "README.md",                         # リポジトリ入口 (現況主張・パス参照を持つ生きた文書)
    REPO / "AGENTS.md",                         # Codex 用の共有規律入口
    REPO / "CLAUDE.md",
    REPO / "tools" / "README.md",              # tools 実行場所分類の生きた入口
    REPO / ".codex" / "agents" / "README.md", # Codex runtime adapter の生きた運用文書
    REPO / "output" / "README.md",              # 成果物 namespace の生きた地図
    REPO / "output" / "task-runs" / "README.md",  # 開発観測台帳の生きた運用正本
    REPO / "docs" / "README.md",                  # docs の地図 (2026-07-11 fc-05 で CLAUDE.md から委譲)
    REPO / "docs" / "ai-provenance.md",           # commit provenance の共有規約
    REPO / "docs" / "provenance" / "correction.md",
    REPO / "docs" / "provenance" / "audit.md",
    REPO / "docs" / "roadmap.md",
    REPO / "docs" / "related-work" / "README.md",  # 旧 related-work.md はディレクトリ化 (2026-07-11 監査 lint-04 で修正 — 旧パスは黙って skip されていた)
    REPO / "docs" / "phase3.md",                  # 現行 phase doc。Phase 移行時にここを差し替え、旧 doc は凍結宣言
    REPO / "docs" / "phase3-main-experiment.md",  # 事前登録 (サンプル設計数値の確定追記が残るため living)
    REPO / "docs" / "phase3-8b-descriptor-design.md",  # 段 8b の実走前凍結設計 (draft の間は living)
    REPO / "docs" / "phase3-8c-preregistration.md",  # 段 8c の実走前事前登録 (発効前は living)
    REPO / "docs" / "phase3-b4-reflux-ablation-preregistration.md",  # B-4 還流 ablation の実走前事前登録 (発効前は living)
    REPO / "docs" / "glossary.md",
    REPO / "docs" / "agent-architecture.md",
    REPO / "docs" / "orchestrator-design.md",
    REPO / "docs" / "ccbench-anatomy.md",
    REPO / "docs" / "axis-onboarding.md",              # 2026-07-11 監査 dup-05 で追加
    REPO / "docs" / "isolation-phenomena.md",          # 2026-07-12 監査: 現在形の生きた参照文書なのに lint 網の外だった
    REPO / "docs" / "ruleops.md",                       # RuleOps v1 の生きた運用・schema 正本
    REPO / "docs" / "dev-wave" / "core.md",
    REPO / "docs" / "dev-wave" / "workers.md",
    REPO / "docs" / "dev-wave" / "mutation.md",
    REPO / "docs" / "dev-wave" / "operations.md",
    REPO / "docs" / "skill-self-improvement.md",
    # token-management-strategy.md は 2026-07-11 に docs/archive/ へ凍結移動 → 2026-07-15 に git-history-only 化 (F8 捏造文書、墓標 = docs/archive/README.md)
]
# 手書き列挙分 (glob 由来ではない) を凍結してスナップショットする。列挙対象の不在は
# 「黙って skip」ではなく違反にする — 改名/削除で検査が黙って蒸発するのを防ぐ (F9 恒真ゲート
# の再発防止。_current_pin 経路と同じ原則)。glob 由来の動的分は実在物だけを拾うので対象外。
_ENUMERATED_DOCS = frozenset(LIVING_DOCS)

# 段 runbook (現在の実走手順を主張する生きた運用文書) は glob で自動編入する —
# 手書き列挙だと段の追加で取りこぼす (2026-07-12 監査: s8a runbook が網の外で pin literal が腐る構造だった)。
# design 系 (phase3-s*-design-*.md) は段完了で凍結する族なので編入しない。
LIVING_DOCS += sorted((REPO / "docs").glob("phase3-s*-runbook.md"))

# docs 間の行番号参照 (追記で必ずずれる)。節名参照に直すこと。
# 対象は自リポジトリの docs のみ (pin 固定の submodule 内文書への参照は腐らないので許容)。
# 「.md:数字」形の確実なものと「N 行」「line N 参照」形だけを違反とする (過検出を避ける)
_OWN = r"(?:CLAUDE|README|roadmap|phase\d[\w-]*|decisions|worklog[\w-]*|agent-architecture|orchestrator-design|ccbench-anatomy|paper-story[\w-]*|audit[\w-]*|isolation-phenomena|glossary|related-work|ruleops)"
LINE_REF_STRICT = [
    re.compile(_OWN + r"\.md:\d+"),
    re.compile(_OWN + r"\.md\s*の?\s*\d+\s*行"),
    re.compile(r"line\s*\d+\s*参照", re.IGNORECASE),
]

HANDOFF_DIR = REPO / "docs" / "handoff"
HANDOFF_STALE_SECONDS = 48 * 3600

# handoff schema (段 4 裁定 B4): land (`tools/dev_wave_land.py`) はもう handoff の書式を
# 検査しない (書式を執行していた `_validate_handoff_at` は削除済み)。ここに残る 3 点の
# 検査が書式を可視化する唯一の経路であり、阻害力は持たない非阻害 warning としてのみ
# 機能する (自己完結。dev_wave_land からは import しない)。所有者判定がないので、
# finding 化すると本 wave が消した「他人巻き込み」を再導入してしまう。
_HANDOFF_HEADER_PREFIXES = ("- 目的: ", "- 状態: ", "- 最終更新: ", "- 基準コミット: ")
_HANDOFF_STATES = frozenset({"作業中", "計測中", "中断"})
_HANDOFF_SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")

ARCHIVE_DIR = REPO / "docs" / "archive"
ARCHIVE_README = ARCHIVE_DIR / "README.md"

# --- worklog 肥大 (2026-07-15 追加、トークン節約メンテ) ---
# ブート時「末尾エントリのみ読む」運用でも、肥大は grep 誤爆・事故全読・コンテキスト
# 圧迫の温床になる (2026-07-05 のローテ後、Phase 3 分だけで 224KB まで再肥大した実績)。
# 閾値超過 = ローテーションの合図 (手順の正本は worklog.md 冒頭)。
WORKLOG = REPO / "docs" / "worklog.md"
WORKLOG_ROTATE_BYTES = 100_000
INSIGHTS_DIR = REPO / "output" / "insights"

# F36 恒久対応 2。正規表現への一般化は裁定で却下済み
# (日本語メタ変数と欠陥説明の引用を誤検出するため)。
LITERAL_PLACEHOLDERS = (
    "<反映>",
    "<受入結果を反映>",
    "<受入全走結果を反映>",
)

# F36 が retroactive な埋め戻しを禁じる、埋め戻し失敗の歴史的債務。
# key は scope -> 行 digest。worklog 族は H2 エントリ見出しに束縛するため、
# エントリごと archive へ移す正規のローテーションでは台帳を変更しなくてよい。
# 行だけを別エントリへ移す replay は赤になる。insights を移動・改名する場合は、
# 同じ種別・digest・count の key を移す (追加・増数ではない)。
KNOWN_PLACEHOLDER_DEBTS = {
    "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2": {
        "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0": 1,
    },
    "worklog-entry:0885598e3ddffd2a6a5c0424c3e6a65ba24f67048374cf3eefc064247e746eb7": {
        "3beb84d709104086993083d461c6b511b63ffd595f2037c28f5c5ae91e046327": 1,
    },
    "worklog-entry:be893df535111cf91c64c141d38afa482dbca6f0a8a829a55b36ac72d8dc79bc": {
        "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0": 1,
    },
    "insights-path:output/insights/2026-07-24_e2e-real-seal.md": {
        "c022f2e9ee8cfaf2237eafa5c30e0c772a368c953e5ccf03a29233028bbe52fd": 1,
    },
}

# placeholder そのものを説明する既存行。歴史的債務とは意味を混ぜない。
KNOWN_PLACEHOLDER_MENTIONS = {
    "worklog-entry:1241aea6de50f3519f1cb497ff8b0fc07d4b4c2b76f35047d091bfb893aa685a": {
        "abdbb38938a76268b5cf63c13309339f58f0cc996deaa13db39c3786e2f3b866": 1,
    },
    "worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511": {
        "80101b39632c395324f424bc9929db7a5c5b76c66b21d61e30afd52434f097ce": 1,
        "9162d9fc17d08b52b54c4f4b1adb96a3b614ed4d944ac955de27bb0ea5b539e5": 1,
    },
    "insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md": {
        "90d8e1f6a7f7229085d78f91ddc7bc91155bbe1ec39b44aaae2b2809daaaf5d9": 1,
        "c66c4f6e14de10c369167108971c74fd0d1462b6a4489792efae907c5d02875c": 1,
    },
}

# 新規 hit に例外を認めない。台帳への追加はユーザーの明示裁定のみ。
EXPECTED_KNOWN_PLACEHOLDER_DEBTS = 4
EXPECTED_KNOWN_PLACEHOLDER_MENTIONS = 5

# D837 (c) で認められた歴史的な carry ID 不一致だけを固定する。
# 外側 key は source entry の H2 raw 行、内側 key は list marker と継続行を
# 含む carry 論理項目の raw slice の sha256。追加はユーザーの明示裁定に限る。
# この境界はレビュー契約であり、
# 台帳と期待総数を同じ patch で変えること自体を機械的に禁止するものではない。
KNOWN_CARRY_ID_MISMATCHES = {
    "6bc0dfb4679d3be38c2a97c7c81c595b62a2b033800e5b27d7f9a63b75c3814b": {
        "34209a9f738fe90a9f3cd57531c3ef900085884b79fc6c1dd833fdf3c46ee45c": 1,
        "f46fe17fc7831678f44471bf5c7c460be6bd65bac6a7e5a47cd0535c150a54a6": 1,
        "f5e03b5bb559682274a1731a73e6d4dca0208c7846fabe312cad1834bc74c14e": 1,
        "5e4a6cb7d118a27df5b710ca20351ea9e5e45ef764ed559b597dc9931140b666": 1,
    },
}
EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 4
# candidate == parsed が parser の完全性を担う。これは母集合全体が消える型だけを
# 捉える粗い補助下限であり、完全性の保証ではない。
MIN_EXPECTED_CARRY_REFERENCE_COUNT = 404_326
_CARRY_FINDING_SAMPLE_LIMIT = 20
PHASE3 = REPO / "docs" / "phase3.md"

# --- command / reference anti-bloat ---


@dataclass(frozen=True)
class TextLimit:
    max_bytes: int
    max_line_chars: int | None = None


# 段2 DW-S07縮約案は、この節だけの「再走値は amend」「insights の逐語・変異台帳」義務を
# byte予算のため落としていた。安全義務を削らせる手段目的の逆転を止めるため、ユーザー裁定
# (2026-08-02) により小幅に引き上げる。
COMMAND_LIMITS = {
    ".claude/commands/dev-wave.md": TextLimit(9_520, 140),
    ".claude/commands/cleanup-branches.md": TextLimit(6_204, 110),
    ".claude/commands/rulings.md": TextLimit(5_623, 180),
    ".claude/commands/next-tasks.md": TextLimit(27_100, 100),
}
SELF_LIMITS = {
    "docs/skill-self-improvement.md": TextLimit(6_000, 100),
}
TOOLS_README_LIMITS = {
    "tools/README.md": TextLimit(3_000),
}
PROVENANCE_ENTRY = "docs/ai-provenance.md"
PROVENANCE_REFERENCE_ROOT = "docs/provenance"
PROVENANCE_LIMITS = {
    PROVENANCE_ENTRY: TextLimit(6_300),
}
PROVENANCE_REFERENCE_LIMITS = {
    "docs/provenance/correction.md": TextLimit(1_600),
    "docs/provenance/audit.md": TextLimit(1_600),
}
PROVENANCE_FAMILY_LIMITS = {
    **PROVENANCE_LIMITS,
    **PROVENANCE_REFERENCE_LIMITS,
}
PROVENANCE_FAMILY_FILES = frozenset(PROVENANCE_FAMILY_LIMITS)
PROVENANCE_FAMILY_BYTES = 9_000
PROVENANCE_DISPATCH_HEADER = "| key | 発火条件 | 読む節 |"

REQUIRED_PROVENANCE_REFERENCE_SECTIONS = {
    "docs/provenance/correction.md": {
        "PR-C01", "PR-C02", "PR-C03",
    },
    "docs/provenance/audit.md": {
        "PR-A01", "PR-A02", "PR-A03",
    },
}
PROVENANCE_DISPATCH_CONTRACT = {
    "correction": (
        "固定 target の forward correction を扱う",
        frozenset({
            ("docs/provenance/correction.md", "PR-C01"),
            ("docs/provenance/correction.md", "PR-C02"),
            ("docs/provenance/correction.md", "PR-C03"),
        }),
    ),
    "message-file": (
        "commit 前に message を検査する",
        frozenset({
            ("docs/provenance/audit.md", "PR-A01"),
        }),
    ),
    "history": (
        "commit 後・別 range の履歴を監査する",
        frozenset({
            ("docs/provenance/audit.md", "PR-A02"),
            ("docs/provenance/correction.md", "PR-C03"),
        }),
    ),
    "analysis": (
        "provenance を比較や改善判断に使う",
        frozenset({
            ("docs/provenance/audit.md", "PR-A03"),
        }),
    ),
}
PROVENANCE_SHARED_DISPATCH_PAIRS = {
    ("docs/provenance/correction.md", "PR-C03"): frozenset({
        "correction", "history",
    }),
}
CODEX_DEV_WAVE_SKILL_LIMITS = {
    ".agents/skills/dev-wave/SKILL.md": TextLimit(5_500, 400),
    ".agents/skills/dev-wave/agents/openai.yaml": TextLimit(500, 160),
}
DEV_WAVE_L1_BYTES_MAX = 10_625
DEV_WAVE_L1_5_BYTES_MAX = 9_696
DEV_WAVE_L2_SECTION_BYTES_MAX = 1_000
CODEX_DEV_WAVE_SKILL_FILES = frozenset(CODEX_DEV_WAVE_SKILL_LIMITS)
CODEX_DEV_WAVE_STAGE9_LAND_LITERAL = (
    "段 9 は dispatcher が指定する共通 land 契約だけに従い、"
    "Codex 固有の取り込み手順を重ねない。"
)
DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL = (
    "`<model>`: 全段 `gpt-6-astra` (段 3 の 2 本も同じ)。"
)
DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING = (
    "docs/dev-wave/operations.md: DW-O01 の可視本文に model 権威行が "
    "exact 1 件でない、または権威行外に `gpt-` model slug がある — "
    "model の単一権威を保持する"
)
DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING = (
    "docs/dev-wave/workers.md: ファイル全体の可視テキストに `gpt-` model slug がある — "
    "model の権威は DW-O01 の model 権威行だけ"
)
DEV_WAVE_OPERATIONS_OUTSIDE_DW_O01_MODEL_SLUG_ABSENCE_FINDING = (
    "docs/dev-wave/operations.md: DW-O01 外の可視テキストに `gpt-` model slug がある — "
    "model の権威は DW-O01 の model 権威行だけ"
)
DEV_WAVE_COMMAND_MODEL_SLUG_ABSENCE_FINDING = (
    ".claude/commands/dev-wave.md: ファイル全体の可視テキストに `gpt-` model slug がある — "
    "model の権威は DW-O01 の model 権威行だけ"
)
DEV_WAVE_OPERATIONS_NON_ATTRIBUTABLE_ONLY_ABSENCE_FINDING = (
    "docs/dev-wave/operations.md: 可視本文に `non-attributable-only` がある — "
    "受入の受理は `child-green` だけ"
)
DEV_WAVE_OPERATIONS_ACCEPTANCE_REDS_TOOL_ABSENCE_FINDING = (
    "docs/dev-wave/operations.md: 可視本文に `tools/check_acceptance_reds.py` がある — "
    "廃止済みの代替受理経路を正本へ戻さない"
)
DEV_WAVE_DW_O01_SECTION_CARDINALITY_FINDING = (
    "docs/dev-wave/operations.md: DW-O01 節が一意でない — "
    "codex subprocess 起動契約を検査できない"
)
DEV_WAVE_DW_O01_MODEL_PLACEHOLDER_FINDING = (
    "docs/dev-wave/operations.md: DW-O01 の可視 top-level に dispatcher route 行が "
    "exact 1 件でない — dispatcher が定める model の束縛位置を保持する"
)
DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL = (
    "`tools/dev_wave_codex.py --stage <stage> [--lane <lane>] -o <出力>.md` "
    "で起動（他の引数は `--help`）。model は全段、effort は段 5 / 6 "
    "が docs 権威から導出。caller 指定は不可。"
)
DEV_WAVE_SINGLE_DISPATCH_STAGE_CHOICES = (
    "plan",
    "consult",
    "author",
    "review",
    "fix",
    "focus",
)
DEV_WAVE_SINGLE_DISPATCH_DECLARATION_LITERAL = (
    "単独段 dispatch: stage=<plan|consult|author|review|fix|focus>; "
    "sandbox=<read-only|workspace-write>; parent=<絶対パス>"
)
DEV_WAVE_SINGLE_DISPATCH_PROJECTION_HEADING = "必読事項の射影:"
DEV_WAVE_SINGLE_DISPATCH_PROJECTION_PATH_RE = re.compile(
    r"/[^\s`<>]+"
)
DEV_WAVE_SINGLE_DISPATCH_PROJECTION_STOP_LITERAL = "読めなければ即停止"
DEV_WAVE_SINGLE_DISPATCH_AGENTS_HEADING = "単独段 dispatch の例外"
DEV_WAVE_SINGLE_DISPATCH_OPERATIONS_REFERENCE_LITERAL = (
    "prompt 先頭は AGENTS.md の単独段例外と同形式。"
)
DEV_WAVE_SINGLE_DISPATCH_AGENTS_SECTION_FINDING = (
    "AGENTS.md: 単独段 dispatch の例外節が可視 H2 で一意でない — "
    "単独段 prompt の適用範囲を検査できない"
)
DEV_WAVE_SINGLE_DISPATCH_DECLARATION_FINDING = (
    "AGENTS.md: 単独段 dispatch の宣言テンプレートが可視本文に "
    "exact 1 件ない — launcher の stage/sandbox/parent 契約を検査できない"
)
DEV_WAVE_SINGLE_DISPATCH_PROJECTION_FINDING = (
    "AGENTS.md: 宣言テンプレート直後の「必読事項の射影:」見出し行が "
    "可視本文にない — 必読資料の射影契約を検査できない"
)
DEV_WAVE_SINGLE_DISPATCH_PROJECTION_CONTENT_FINDING = (
    "AGENTS.md: 宣言テンプレート直後の射影節本文に絶対パスらしき記述と"
    "「読めなければ即停止」の両方がない — 必読資料の射影契約を検査できない"
)
DEV_WAVE_SINGLE_DISPATCH_LAUNCHER_FINDING = (
    "AGENTS.md: tools/dev_wave_codex.py の STAGES を解析できない — "
    "単独段 dispatch の stage 検査を実行できない"
)
DEV_WAVE_SINGLE_DISPATCH_STAGE_FINDING = (
    "AGENTS.md: 単独段 dispatch の stage 語彙が "
    "tools/dev_wave_codex.py の --stage choices と不一致"
)
DEV_WAVE_SINGLE_DISPATCH_OPERATIONS_SECTION_FINDING = (
    "docs/dev-wave/operations.md: DW-O02 節が可視本文で一意でない — "
    "単独段 dispatch の到達契約を検査できない"
)
DEV_WAVE_SINGLE_DISPATCH_OPERATIONS_REFERENCE_FINDING = (
    "docs/dev-wave/operations.md: DW-O02 に AGENTS.md の単独段例外を"
    "参照する可視文言が exact 1 件ない"
)
DEV_WAVE_STAGE6_WAITER_CONSUMER_LINES = (
    "6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。",
    "   受入投入は `tools/dev_wave_wait.py acceptance --lease-optional` を使う。",
)
DEV_WAVE_STAGE9_WAITER_CONSUMER_LINES = (
    "9. **終端・local main (親):** 共通 land operation で監査済み成果だけを取り込み、結果を確定して終了する。",
    "   受入・land の終端で必ず `tools/dev_wave_wait.py acceptance` で `release` し、",
    "   land 成功時だけ `message` を照合済み peer へ 1 度送る。",
)
DEV_WAVE_DW_C00_WAITER_CONSUMER_LITERAL = (
    "待ち手は 1 条件 1 本とし、通知ごとに作り直さず `tools/dev_wave_wait.py` を使う。"
)
DEV_WAVE_DW_O01_WAITER_CONSUMER_LITERAL = (
    "待機は `tools/dev_wave_wait.py producer` を使い、`--pid-file` は producer script 自身が "
    "`echo $$` で書く。"
)
DEV_WAVE_WAITER_DISCLAIMER_RE = re.compile(
    r"参考例|任意|手動投入|してよい|使わない|実行しない|"
    r"必須(?:では|で)ない|省略(?:可|してよい)"
)
DEV_WAVE_WAITER_TARGET = "tools/dev_wave_wait.py"
DEV_WAVE_STAGE6_WAITER_CONSUMER_FINDING = (
    ".claude/commands/dev-wave.md: 9 段状態機械の項 6 に waiter consumer "
    "normative line が可視 top-level exact 1 件でない"
)
DEV_WAVE_STAGE9_WAITER_CONSUMER_FINDING = (
    ".claude/commands/dev-wave.md: 9 段状態機械の項 9 に waiter consumer "
    "normative line が可視 top-level exact 1 件でない"
)
DEV_WAVE_DW_C00_WAITER_CONSUMER_FINDING = (
    "docs/dev-wave/core.md: DW-C00 に waiter consumer normative line が "
    "可視 top-level exact 1 件でない"
)
DEV_WAVE_DW_O01_WAITER_CONSUMER_FINDING = (
    "docs/dev-wave/operations.md: DW-O01 に waiter consumer normative line が "
    "可視 top-level exact 1 件でない"
)
DEV_WAVE_WAITER_DISCLAIMER_FINDING = (
    "dev-wave waiter consumer: normative line と同じ節に義務を打ち消す語がある"
)
DEV_WAVE_WAITER_TARGET_FINDING = (
    "tools/dev_wave_wait.py: waiter consumer の canonical target が symlink でない "
    "regular file として実在しない"
)
DEV_WAVE_MODEL_SLUG_RE = re.compile(
    r"(?<![A-Za-z0-9._-])gpt-[0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
    r"(?![A-Za-z0-9._-])"
)
DEV_WAVE_DW_S02_REASONING_XHIGH_LITERAL = "`reasoning=medium`"
DEV_WAVE_DW_S03_REASONING_XHIGH_LITERAL = "`reasoning=medium`"
DEV_WAVE_DW_S06_A_REASONING_XHIGH_LITERAL = "`reasoning=medium`"
DEV_WAVE_DW_S06_C_REASONING_XHIGH_LITERAL = "`reasoning=medium`"
DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE = (
    "実装 wave は異なるレンズの敵対レビューを `reasoning=medium` で必ず 2 本並列で行う。"
)
DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE = (
    "並列 fix の統合後、焦点再レビューは全体へ `reasoning=medium` で 1 本でよい。"
)
DEV_WAVE_DW_S05_A_REASONING_XHIGH_SENTENCE = (
    "codex は `reasoning=medium`、`sandbox=workspace-write` とする。"
)
DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING = (
    "docs/dev-wave/workers.md: DW-S02 の `reasoning=medium` は"
    "現行 adoption pin と不一致 — "
    "変更には採用裁定 (A/B 証拠またはユーザー裁定) と pin の同時更新が必要"
)
DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING = (
    "docs/dev-wave/workers.md: DW-S03 の `reasoning=medium` は"
    "現行 adoption pin と不一致 — "
    "変更には採用裁定 (A/B 証拠またはユーザー裁定) と pin の同時更新が必要"
)
DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING = (
    "docs/dev-wave/workers.md: DW-S06-A の `reasoning=medium` は段 6 敵対レビューの"
    "現行 adoption pin と不一致 — 変更には採用裁定と pin の同時更新が必要"
)
DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING = (
    "docs/dev-wave/workers.md: DW-S06-C の `reasoning=medium` は段 6 焦点再レビューの"
    "現行 adoption pin と不一致 — 変更には採用裁定と pin の同時更新が必要"
)
DEV_WAVE_DW_S05_A_REASONING_XHIGH_FINDING = (
    "docs/dev-wave/workers.md: DW-S05-A の `reasoning=medium` は段 5 実装子の"
    "現行 adoption pin と不一致 — 変更には採用裁定と pin の同時更新が必要"
)
DEV_WAVE_DW_O16_REASONING_EFFORT_FINDING = (
    "docs/dev-wave/operations.md: DW-O16 に reasoning effort 値がある — "
    "焦点再レビューの effort は DW-S06-C だけを正本とする"
)
DEV_WAVE_REASONING_EFFORT_RE = re.compile(
    r"(?<![A-Za-z0-9_./?-])"
    r"(?:reasoning|reasoning_effort|model_reasoning_effort)="
    r"(?P<quote>[\"']?)"
    r"(?P<value>[^ \t\r\n`。、，,;；!?！？()（）\[\]{}「」『』]+?)"
    r"(?P=quote)"
    r"(?=$|[ \t\r\n`。、，,;；!?！？()（）\[\]{}「」『』])"
)
DEV_WAVE_COMMAND_START_SECTION_LITERAL = """## 入力と開始

- 第一声から進捗、裁定、最終報告、`result:` まで、ユーザー向け出力はすべて日本語にする。
- `CLAUDE.md` のクラス 3 起動手順を実行し、引数があれば対象にする: $ARGUMENTS
- wave 開始時に `docs/skill-self-improvement.md` の発火 gate・routing・dev-wave を読み、
  専用 handoff に「dev-wave 改善候補」節を作る。
- 無人継続の外部 supervisor は、最初の `claude -p` spawn 前に
  `docs/dev-wave/core.md` の `DW-CTX` を読む。

"""
CODEX_DEV_WAVE_STARTUP_ROUTING_ITEM_LITERAL = """4. `docs/skill-self-improvement.md` の発火 gate・routing・dev-wave 終端を読み、専用 handoff に
   `dev-wave 改善候補` 節を作る。"""
CODEX_DEV_WAVE_START_SECTION_LITERAL = """## 開始する

0. prompt 本文の最初の非空行が `AGENTS.md`「単独段 dispatch の例外」節と同一形式の宣言・射影を
   満たす場合は、以下 1〜5 を適用せず、宣言と射影が指示する資料だけを読む。宣言が欠落・形式不正・
   重複、または射影対象を読めない場合はこの例外を使わず、以下の手順に従う。
1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読み、依頼をクラス 3 として起動する。
2. ユーザーが指定した対象を優先する。対象がなければ worklog 末尾の「次の一手」から 1 件選ぶ。
3. `.claude/commands/dev-wave.md` を全文読む。同ファイルを 9 段状態機械、段 dispatch、条件 dispatch、
   巻き戻し、停止条件の共通 dispatcher として扱う。
4. `docs/skill-self-improvement.md` の発火 gate・routing・dev-wave 終端を読み、専用 handoff に
   `dev-wave 改善候補` 節を作る。
5. main では編集しない。既存の専用 Codex worktree があれば状態と対象を照合して再利用し、
   なければ local main の HEAD から `.codex/worktrees/` 配下に専用 branch/worktree を作る。

参照先の節は、dispatcher が指定する段または条件の直前に読み直す。記憶や本 Skill の要約で代用しない。
参照先が不在、読取不能、非一意、または期限後に条件成立が判明した場合は dispatcher どおり
fail-closed に停止または巻き戻す。

"""
DEV_WAVE_SELF_ROUTING_SECTION_LITERAL = """## routing

1. 新しい失敗型・near miss・既存防壁の破れは `docs/failures.md` へ送る。
   同型再発なら新しい F を作らず、既存 F に「再発: 日付」を追記する。
2. 長期の設計、権限、正本、interface を変える採用済み判断は `docs/decisions.md` へ送る。
   未裁定または大きい変更を既成事実にせず、裁定パッケージとしてユーザーへ返す。
3. dev-wave 固有の手順は発火段に対応する `docs/dev-wave/` の既存 leaf 節へ統合し、意味を保って
   統合できない場合だけ新しい節・ファイルを候補にする。新規 L2 節の登録は鏡像の
   「発火実績あり × 義務が現に機械代替されていない × 同じ意味検索で反証も同一発火点の
   既存正本もなし」を満たす場合だけとする (D271)。L2 (条件成立時だけ読む節) の削除を裁定
   パッケージへ送れるのは「発火実績なし × テスト/機械検査で義務代替済み」の両条件を満たす
   節だけで、実施はユーザー裁定に限る。「発火実績なし」は ID 件数でなく repo 全体
   (insights・memo 含む) の意味検索で反証されないことを確認する。
4. cleanup-branches / rulings の短い手順は各 command の既存節を是正する。
   長い事故説明は F ポインタにし、裁定待ち・branch 状態・可変データを command へ書かない。
5. 同じ内容を複数の行き先へ全文複製しない。入口は命令と dispatch、reference は実行手順、
   failures は事象・原因・恒久対応、decisions は採用理由を担う。

"""
DEV_WAVE_DW_O18_SECTION_LITERAL = """## DW-O18 — テスト cwd と非帰属赤の着地

cwd=repo root。nested subprocess import path偽赤は回帰外。file選択走は`from tests import`確立後に限り未確立赤も偽赤。

受入赤返却時が判定主体の境界。待ち手は赤返却だけ。人・AIが判定し根拠をworklogへ残す。assertion本文・差分実体で判定、署名一致禁止。非帰属赤の着地5分超禁止、悩まない(D690)。自分起因は直す。N走完全一致はflakeでも非帰属の証拠でもない。差分到達不能は単独再走、非再現なら受入再走。同一tipで各1回だけ。再赤/決定的赤はmain既存Fを証拠にCodex`role=author`が`orchestrator/tests/flaky_test_holds.py`へ登録(field正本=同file)。F不在は登録せず裁定送り、判定不能・原因未理解は除外せず共に停止。停止条件外は治すかhold登録後だけ投げ直しwaveを止めない。受理は`child-green`だけ、赤の受領証禁止。

"""
DEV_WAVE_DW_O25_SECTION_LITERAL = """## DW-O25 — ff-only land の全史 provenance 関門

D254 に従い、land は `locked_main != 着地tip` のときだけ lock を解放して全史 provenance 監査を自ら走らせ、480 秒以内の rc=0 を必須とする。赤は `RC_PROVENANCE = 29` で main を 1 bit も変えず拒否し、CLI flag・環境変数・警告化の逃がし道を作らない。
lock 再取得後に全検査をやり直し、`tip_sha` / `checker_blob_sha` / `executed_bytes_sha` / `returncode` を束縛した receipt を lock 内で再照合する。`already-landed` の no-op と active fold transaction の recovery では監査を起動しない。
"""
DEV_WAVE_DW_O26_SECTION_LITERAL = """## DW-O26 — 焦点走の consumer test 拡張

`DW-O18` の焦点走対象 file 集合は、変更した test file だけでなく、変更した production file を
参照する consumer test も含める。名前の推測でなく参照関係で引く。private symbol の変更は
公開 API の consumer 表に出ない。symbol 名で production 全体を grep する。この拡張を欠く
焦点走は、静的レビューが見落とした破れを初回実測でも取り逃す（F242）。
同一 worktree からの dispatch は全種を直列にする。並行投入は orphan hold で rc=16 になる。
変更した test file は受入全走前に単独走で確認する（全走緑は file 単独緑を含意しない）。新規
test file を足す走は file 集合列挙のメタテストも焦点走に含める。並行 wave が自分の編集 file を
所有するなら main 取込み済みの木で既存走行に相乗りし受入後に足さない。
"""
DEV_WAVE_DW_O28_SECTION_LITERAL = """## DW-O28 — land 後の自己撤去

親は `landed` / `already-landed` を確認後、同じ段 9 で先に対象 worktree 外の main worktree へ移り、投入した計算ノード job の終端後に次を実行する（`<MAIN>` / `<WAVE>` は絶対 path）。
`python3 tools/dev_wave_cleanup.py --main-worktree <MAIN> --wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>`
tool は unoccupied、clean、tested tip が `refs/heads/main` の祖先、fold state 不在、wave が非 primary、cwd が対象外を全て要求し、どれかが不成立または判定不能なら fail-closed で停止する。
同一 wave の worktree と branch を撤去し、次 wave・ユーザー・`/cleanup-branches` へ引き渡さない。
F26 に従い `git worktree remove` と `git submodule deinit` は使わない。branch は `git branch -d` だけで消し `-D` を使わない。撤去できない理由は報告し、次 wave の worklog へ記録する。
"""
DEV_WAVE_DW_C01_SECTION_LITERAL = """## DW-C01 — 実測で是正した作法

`DW-O01/O08/O17/O20`より優先。
- `--lane`はconsult、`--reasoning`はplan/consultで必須。他段指定/必須段無指定はrc=2。
- 待ち手はpid file実在後に張る。先行は子の生存中も即戻る。
- 隔離worktreeのdetachは`.sh`2枚(launcher/detach)へ。直に叩くとguard拒否。
- 複数起点は全隣接区間の異なる正値で判別。
- 変異harnessはbaseline緑必須。既存赤は根拠を台帳へ書き`--deselect`。
- 全新規worktreeを`python3 tools/dev_wave_submodule_init.py --worktree <ABSOLUTE>`で再帰初期化する。
- 呼出し規約変更取込は、両親の変更行が非競合でも全呼出しを数える。
- 段6fixも受理・拒否の含意を2文に分け、通る正例を添える。
- merge/`add`/commitは親、子は競合解決だけ。
- 子の成果物はrepo内に書かせ、親が実行後repo外へ退避。
- Web検索は必要な段だけ明示して使う。
"""
DEV_WAVE_EXACT_VISIBLE_SECTIONS = {
    (".claude/commands/dev-wave.md", "入力と開始"):
        DEV_WAVE_COMMAND_START_SECTION_LITERAL,
    ("docs/skill-self-improvement.md", "routing"):
        DEV_WAVE_SELF_ROUTING_SECTION_LITERAL,
    ("docs/dev-wave/operations.md", "DW-O18 — テスト cwd と非帰属赤の着地"):
        DEV_WAVE_DW_O18_SECTION_LITERAL,
    ("docs/dev-wave/operations.md", "DW-O25 — ff-only land の全史 provenance 関門"):
        DEV_WAVE_DW_O25_SECTION_LITERAL,
    ("docs/dev-wave/operations.md", "DW-O26 — 焦点走の consumer test 拡張"):
        DEV_WAVE_DW_O26_SECTION_LITERAL,
    ("docs/dev-wave/operations.md", "DW-O28 — land 後の自己撤去"):
        DEV_WAVE_DW_O28_SECTION_LITERAL,
    ("docs/dev-wave/core.md", "DW-C01 — 実測で是正した作法"):
        DEV_WAVE_DW_C01_SECTION_LITERAL + "\n",
}

CODEX_DEV_WAVE_NATURAL_LANGUAGE_STOP_LITERAL = (
    "本 Skill は明示起動専用であり、自然文の依頼を一般タスクとして\n"
    "  処理せず、`$dev-wave <対象>` の明示起動を案内して止まる。"
)
CODEX_DEV_WAVE_PROTECTED_PATH_AUTHORING_LITERAL = (
    "防護パス文字列を含む prompt・commit message は、Bash heredoc や不透明な command substitution で\n"
    "  作らない。Codex では Bash の中からではなく `apply_patch` tool を直接呼び、新規 file は\n"
    "  `*** Add File:` patch で作る。commit message はその file を `git commit -F <file>` へ渡す。"
)
CODEX_DEV_WAVE_SKILL_LITERALS = (
    ".claude/commands/dev-wave.md",
    CODEX_DEV_WAVE_STARTUP_ROUTING_ITEM_LITERAL,
    "docs/dev-wave/workers.md",
    "docs/dev-wave/operations.md",
    CODEX_DEV_WAVE_NATURAL_LANGUAGE_STOP_LITERAL,
    CODEX_DEV_WAVE_PROTECTED_PATH_AUTHORING_LITERAL,
    "manager は実装面を直接編集しない",
    "codex exec",
    "collaboration child",
    ".codex/role-adapters/*.json",
    "hooks/README.md",
    "supervised manifest",
    "段 1〜9",
    "local main",
)
CODEX_DEV_WAVE_DESCRIPTION = (
    "Run one Izanagi development wave through its brief, Codex planning and "
    "adversarial review, implementation, mutation and acceptance checks, "
    "recording, and bounded termination workflow. Use only for an explicit "
    "$dev-wave invocation; implicit invocation is disabled. Do not use it for "
    "a CC synthesis campaign."
)
CODEX_DEV_WAVE_OPENAI_YAML = """interface:
  display_name: "Dev Wave"
  short_description: "Izanagi の開発 wave を共通契約に従って実行"
  default_prompt: "Use $dev-wave to run one Izanagi development wave for the specified task."

policy:
  allow_implicit_invocation: false
"""
CODEX_RULINGS_SKILL_LIMITS = {
    ".agents/skills/rulings/SKILL.md": TextLimit(3_000, 400),
    ".agents/skills/rulings/agents/openai.yaml": TextLimit(500, 160),
}
CODEX_RULINGS_SKILL_FILES = frozenset(CODEX_RULINGS_SKILL_LIMITS)
CODEX_RULINGS_SKILL_LITERALS = (
    "AGENTS.md",
    "CLAUDE.md",
    ".claude/commands/rulings.md",
    "$ARGUMENTS",
    "$rulings",
    "docs/worklog.md",
    "docs/skill-self-improvement.md",
    "hooks/README.md",
    "クラス 1",
    "クラス 2",
    "それ以外ではファイルを編集しない",
    "push と remote branch 操作は人間に残す",
)
CODEX_RULINGS_OPENAI_YAML = """interface:
  display_name: "Rulings"
  short_description: "Izanagi の裁定待ちを索引・詳説して判断を補佐"
  default_prompt: "Use $rulings to list and explain the Izanagi decisions awaiting my ruling."
"""
# next-tasks の repo-scoped Skill 契約を登録する。
CODEX_NEXT_TASKS_SKILL_LIMITS = {
    ".agents/skills/next-tasks/SKILL.md": TextLimit(5_460, 400),
    ".agents/skills/next-tasks/agents/openai.yaml": TextLimit(300, 160),
}
CODEX_NEXT_TASKS_SKILL_FILES = frozenset(CODEX_NEXT_TASKS_SKILL_LIMITS)
CODEX_NEXT_TASKS_SKILL_LITERALS = (
    "AGENTS.md",
    "CLAUDE.md",
    ".claude/commands/next-tasks.md",
    "$1",
    "$next-tasks",
    "$dev-wave",
    "docs/pegasus-runbook.md",
    "docs/skill-self-improvement.md",
    "hooks/README.md",
    "クラス 1",
    "クラス 2",
    "D2051",
    "next_tasks_consult.sh claude",
    "実測せずに外さない",
    "CONSULT-MODE",
    "3 巡目へ進めず",
    "件数合わせで除外候補を復活させない",
    "自己改善の終端条件を含める",
    "丸付き数字は使わない",
    "それ以外ではファイルを編集しない",
    "push と remote branch 操作は人間に残す",
    "環境に API キーを置かない",
    "API key や代替 provider を新設して呼び出す経路は作らない",
)
CODEX_NEXT_TASKS_OPENAI_YAML = """interface:
  display_name: "Next Tasks"
  short_description: "今すぐ投げられる dev-wave タスク候補を提案"
  default_prompt: "Use $next-tasks to propose two dev-wave tasks that can start now."
"""
CODEX_CLEANUP_BRANCHES_SKILL_LIMITS = {
    ".agents/skills/cleanup-branches/SKILL.md": TextLimit(3_100, 210),
    ".agents/skills/cleanup-branches/agents/openai.yaml": TextLimit(300, 110),
}
CODEX_CLEANUP_BRANCHES_SKILL_FILES = frozenset(
    CODEX_CLEANUP_BRANCHES_SKILL_LIMITS
)
CODEX_CLEANUP_BRANCHES_DESCRIPTION = (
    "Safely inventory and clean up merged local Izanagi branches and worktrees "
    "through the shared dispatcher. Use for merged-branch or worktree cleanup; "
    "deletion needs explicit $cleanup-branches."
)
CODEX_CLEANUP_BRANCHES_SKILL_SHA256 = (
    "268a32aeb2fb4a361e2a99cc7c90ff09e905c74465c64e8b4e2227d8b2d85dea"
)
CODEX_CLEANUP_BRANCHES_OPENAI_YAML = """interface:
  display_name: "Cleanup Branches"
  short_description: "Izanagi のマージ済み branch と worktree を安全に整理"
  default_prompt: "Use $cleanup-branches to safely clean up merged local branches and worktrees."
"""
CLEANUP_COMMAND_SHA256 = (
    "75939b07e112fd2977ecaa0efbb77f4119a7050d052f9fdf668c35acdddb8730"
)
CLEANUP_OCCUPANCY_SECTION = "3. worktree の削除手順 (F26)"
CLEANUP_OCCUPANCY_CONTRACT = (
    "削除の直前に対象ごと `python3 tools/check_worktree_occupancy.py "
    "<worktree>`。rc0 のみ進み、\n"
    "rc1=占有/rc2=判定不能は停止。submodule は `git worktree remove` 禁止、"
    "F26 の手順にする:"
)

COMMAND_INTERFACES = {
    ".claude/commands/dev-wave.md": {
        "frontmatter_keys": {
            "description", "argument-hint", "disable-model-invocation",
        },
        "disable-model-invocation": "true",
        "arguments_count": 1,
    },
    ".claude/commands/cleanup-branches.md": {
        "frontmatter_keys": {"description", "argument-hint"},
        "arguments_count": 1,
    },
    ".claude/commands/rulings.md": {
        "frontmatter_keys": {"description", "argument-hint"},
        "arguments_count": 1,
    },
    ".claude/commands/next-tasks.md": {
        "frontmatter_keys": {"description", "argument-hint"},
        "arguments_count": 0,
    },
}

# DW-O07 は T-154(1) 裁定 (2026-07-28) で削除済み — 復活時は裁定を新規に起こす。
# DW-O15 も T-450 裁定で削除済み — 復活時は裁定を新規に起こす。
# DW-O21/O22 は core の external continuation 条件が使用済みなので、land は DW-O23/O25。
_OPERATION_NUMBERS = (*range(1, 7), *range(8, 15), *range(16, 21), 23, 25)
DEV_WAVE_LAND_HELPER = "tools/dev_wave_land.py"
DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL = (
    "`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路"
)
DEV_WAVE_S09_ACCEPTANCE_ORDER_LITERAL = (
    "全 commit・受入結果を固定し、tested main/tip と監査 commit 列を実測して "
    "`DW-O23` を行う。"
)
ALTERNATE_LAND_HELPER_COMMAND = re.compile(
    r"(?m)^[ \t]*(?:\$\s*)?python3?"
    r"(?:[ \t]+[^\s`]+)*?[ \t]+(?:\./)?tools/"
    r"(?!dev_wave_land\.py(?:[ \t]|$))"
    r"[^\s`]*land[^\s`]*\.py(?:\s|$)"
)
DIRECT_MAIN_FF_COMMAND = re.compile(
    r"(?m)^[ \t]*(?:\$\s*)?git"
    r"(?:[ \t]+[^\s`]+)*?[ \t]+merge(?=[ \t])"
    r"(?=[^\n]*[ \t]--ff-only(?:[ \t]|$))[^\n]*$"
)

REQUIRED_REFERENCE_SECTIONS = {
    "docs/dev-wave/core.md": {
        "DW-C00", "DW-C01", "DW-STOP", "DW-S01", "DW-G01", "DW-G02",
        "DW-G03", "DW-G04", "DW-G05", "DW-S04", "DW-S07",
        "DW-S08", "DW-S09", "DW-CTX",
    },
    "docs/dev-wave/workers.md": {
        "DW-S02", "DW-S03",
        "DW-S05-A", "DW-S05-B", "DW-S05-C",
        "DW-S06-A", "DW-S06-B", "DW-S06-C",
    },
    "docs/dev-wave/mutation.md": {
        "DW-M01", "DW-M02", "DW-M03", "DW-M04",
        "DW-M05", "DW-M06", "DW-M07", "DW-M08",
    },
    "docs/dev-wave/operations.md": (
        # O26/O27/O28 は既存の削除済み ID を含む番号列から独立した新規節。
        {f"DW-O{i:02d}" for i in _OPERATION_NUMBERS} | {"DW-O26", "DW-O27", "DW-O28"}
    ),
}
DEV_WAVE_REFERENCE_FILES = frozenset(REQUIRED_REFERENCE_SECTIONS)
NORMATIVE_DISPATCH_ALLOWLIST = (
    DEV_WAVE_REFERENCE_FILES | frozenset(SELF_LIMITS)
)
REQUIRED_SELF_HEADINGS = {
    2: {
        "発火 gate", "routing", "command 入口の編集条件",
        "command 別の終端", "検査と commit 境界",
    },
    3: {"dev-wave", "cleanup-branches", "rulings", "next-tasks"},
}
_SELF_PATH = "docs/skill-self-improvement.md"
_SELF_SECTIONS = frozenset(
    (_SELF_PATH, heading)
    for headings in REQUIRED_SELF_HEADINGS.values()
    for heading in headings
)


def _pairs(path: str, *sections: str) -> frozenset[tuple[str, str]]:
    return frozenset((path, section) for section in sections)


_CORE = "docs/dev-wave/core.md"
_WORKERS = "docs/dev-wave/workers.md"
_MUTATION = "docs/dev-wave/mutation.md"
_OPERATIONS = "docs/dev-wave/operations.md"
_ALL_OPERATIONS = _pairs(
    _OPERATIONS, *(f"DW-O{i:02d}" for i in _OPERATION_NUMBERS)
)

DEV_WAVE_STAGE_DISPATCH_LEGEND = "種別は U=無条件、C=条件 dispatch 成立時。"
DEV_WAVE_STAGE_DISPATCH_HEADER = "| 入る直前 | 種別 | 必ず読む節 |"
DEV_WAVE_CONDITION_DISPATCH_HEADER = "| # | 発火条件 | 読む節 |"
DEV_WAVE_L1_STAGE_KEYS = frozenset({
    "wave 開始", "段 1", "段 4", "段 7", "段 8 preflight", "段 9",
})
DEV_WAVE_L1_5_STAGE_KEYS = frozenset({
    "段 2 preflight", "段 3 preflight", "段 5", "段 6",
})

STAGE_UNCONDITIONAL_DISPATCH_CONTRACT = {
    "wave 開始": _pairs(_CORE, "DW-C00", "DW-STOP"),
    "段 1": _pairs(
        _CORE, "DW-S01", "DW-G01", "DW-G02", "DW-G03", "DW-G04", "DW-G05"
    ),
    "段 2 preflight": (
        _pairs(_WORKERS, "DW-S02")
        | _pairs(_OPERATIONS, "DW-O01", "DW-O02", "DW-O05")
    ),
    "段 3 preflight": (
        _pairs(_WORKERS, "DW-S03")
        | _pairs(_OPERATIONS, "DW-O01", "DW-O02", "DW-O05")
    ),
    "段 4": (
        _pairs(
            _CORE, "DW-S04", "DW-G01", "DW-G02", "DW-G03", "DW-G04", "DW-G05"
        )
        | _pairs(_MUTATION, "DW-M01")
    ),
    "段 5": _pairs(_WORKERS, "DW-S05-A", "DW-S05-B", "DW-S05-C"),
    "段 6": (
        _pairs(
            _WORKERS,
            "DW-S05-A", "DW-S05-B", "DW-S05-C",
            "DW-S06-A", "DW-S06-B", "DW-S06-C",
        )
        | _pairs(_CORE, "DW-G05")
        | _pairs(
            _MUTATION,
            "DW-M02", "DW-M03", "DW-M04", "DW-M05",
            "DW-M06", "DW-M08",
        )
    ),
    "段 7": _pairs(_CORE, "DW-S07"),
    "段 8 preflight": (
        _pairs(_CORE, "DW-S08")
        | _SELF_SECTIONS
    ),
    "段 9": (
        _pairs(_CORE, "DW-S09", "DW-CTX", "DW-STOP")
        | _pairs(_OPERATIONS, "DW-O23")
    ),
}

STAGE_CONDITIONAL_DISPATCH_CONTRACT = {
    "段 5": _ALL_OPERATIONS,
    "段 6": _ALL_OPERATIONS,
    "段 7": _pairs(_OPERATIONS, "DW-O12", "DW-O17", "DW-O18", "DW-O19"),
    "段 8 preflight": _pairs(_OPERATIONS, "DW-O17"),
}

STAGE_DISPATCH_CONTRACT = {
    key: (
        STAGE_UNCONDITIONAL_DISPATCH_CONTRACT.get(key, frozenset())
        | STAGE_CONDITIONAL_DISPATCH_CONTRACT.get(key, frozenset())
    )
    for key in (
        set(STAGE_UNCONDITIONAL_DISPATCH_CONTRACT)
        | set(STAGE_CONDITIONAL_DISPATCH_CONTRACT)
    )
}
CONDITION_DISPATCH_CONTRACT = {
    f"{i:02d}": _pairs(_OPERATIONS, f"DW-O{i:02d}")
    for i in _OPERATION_NUMBERS
}
CONDITION_DISPATCH_CONTRACT["15"] = _pairs(_MUTATION, "DW-M07")
CONDITION_DISPATCH_CONTRACT["18"] = _pairs(
    _OPERATIONS, "DW-O18", "DW-O26", "DW-O27"
)
CONDITION_DISPATCH_CONTRACT.update({
    "21": _pairs(_CORE, "DW-CTX"),
    "22": _pairs(_CORE, "DW-CTX"),
    "24": _pairs(_CORE, "DW-C00"),
    "26": _pairs(_CORE, "DW-C01"),
    "27": _pairs(_OPERATIONS, "DW-O28"),
})
CONDITION_18_RUN_POINT_LITERAL = "テスト・受入前"
CONDITION_18_RED_POINT_LITERAL = "赤処理前"
CONDITION_TRIGGER_CONTRACT = {
    "01": "codex subprocess を起動する直前",
    "02": "prompt・log・patch を作る直前",
    "03": "prompt に防護パス文字列を含めて作る直前",
    "04": "commit message に防護パス文字列を含めて作る直前",
    "05": "read-only codex に相談・レビューさせる直前",
    "06": "workspace-write 子で submodule 系テストを扱う直前",
    "08": "freeze / oracle gate / proof chain に触る可能性が判明",
    "09": "凍結成果物の bytes を変えうる可能性が判明",
    "10": "09 が成立し producer の出力 bytes が変わりうる",
    "11": "ファイル削除を伴うと判明",
    "12": "裁定手順と実行手順が食い違った時点",
    "13": "gate・検証を新設する可能性が生じた時点",
    "14": "no-touch 対象へ monkeypatch を検討する直前",
    "15": "変異を走らせる直前",
    "16": "fix 後の焦点再レビューを行う直前",
    "17": "commit を作る直前",
    "18": "親のテスト・受入前と赤処理前",
    "19": "tracked file を一時変異する直前",
    "20": "背景 job + worktree 隔離の wave 開始時（最遅: clean-tree gate を worktree で走らせる直前）",
    "21": "無人継続を構成し最初の process を起動する前",
    "22": "supervisor を使用する前",
    "23": "local main を取り込む直前",
    "24": "背景 producer・待ち手の生成 / 再利用 / 停止、通知処理、待ち条件作成の直前",
    "25": "main を進める land を起動する直前",
    "26": "起動/待機/検査/submodule/取込/fix前",
    "27": "land 成功後の自己撤去直前",
}

D2_ROLLBACK_STRUCTURE = re.compile(
    r"条件には最遅読了段がある。"
    r".*?`DW-O08`.*?`DW-O09`.*?`DW-O10`.*?段 1 brief 前"
    r".*?`DW-O13`.*?段 2 プラン前"
    r".*?期限後.*?invalidate"
    r".*?前者は段 1 brief.*?後者は段 2.*?再実行"
    r".*?巻き戻し後.*?再評価.*?流用してはならない",
    re.DOTALL,
)
D4_FIX_INHERITANCE_STRUCTURE = re.compile(
    r"段 6 で fix を codex へ再投する子は"
    r".*?`DW-S05-A`.*?`DW-S05-B`.*?`DW-S05-C`.*?全文継承"
    r".*?段 6 時点で成立している全条件の `DW-Oxx`"
    r".*?fix 操作の直前に読む",
    re.DOTALL,
)
CODEX_AUTHORING_STRUCTURE = re.compile(
    r"コード・テスト.*?以下「実装面」.*?軽量版でも"
    r".*?Codex `role=author`.*?親は実装面を直接編集せず",
    re.DOTALL,
)
CODEX_FIRST_REFERENCE_LITERALS = {
    _CORE: (
        "実装面があれば段 5 の Codex 実装子と fix 子は",
        "親は直接編集しない",
    ),
    _WORKERS: (
        "実装面に Codex `role=author` のないハンク",
        "親が直接直さない",
    ),
}

# --- 「次の一手」ID 保存則 (D70) ---
# 1〜999 は 3 桁固定、1000 以上は冗長な先頭ゼロなしを正規形とする。
TASK_ID_PATTERN = r"\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\]"
TASK_ID_AT_HEAD_RE = re.compile(rf"^(?P<id>{TASK_ID_PATTERN})(?=$|[ \t])")
TASK_ID_LIKE_AT_HEAD_RE = re.compile(r"^\[T-[^\]\n]*\]")
TASK_ID_LIKE_RE = re.compile(r"\[T-[^\]\n]*\]")
TOP_LEVEL_ITEM_RE = re.compile(
    r"^(?:[1-9][0-9]*\.|-)[ \t]+(?P<text>[^\n]*)$", re.MULTILINE
)
FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,}).*$")
WORKLOG_H2_RE = re.compile(r"^##[ \t]+(?P<title>[^\n]+?)[ \t]*$", re.MULTILINE)
ROTATION_RE = re.compile(r"^## ローテーション[^\n]*$", re.MULTILINE)
WORKLOG_ENTRY_TITLE_RE = re.compile(
    r"\d{4}-\d{2}-\d{2} \((?P<order>[1-9][0-9]*)\) — .+"
)
ARCHIVE_WORKLOG_ENTRY_TITLE_RE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?: \((?P<order>[1-9][0-9]*|続き[0-9]*)\))? — .+"
)
NEXT_ACTION_RE = re.compile(
    r"^### 次の一手(?:[ \t][^\n]*)?$\n?(?P<body>.*?)(?=^###[ \t]|^##[ \t]|\Z)",
    re.MULTILINE | re.DOTALL,
)
CARRY_REFERENCE_RE = re.compile(
    rf"^(?P<id>{TASK_ID_PATTERN}) \((?P<target>[1-9][0-9]*)\)$"
)
LEGACY_CARRY_REFERENCE_RE = re.compile(
    rf"^(?P<id>{TASK_ID_PATTERN})(?=$|[ \t]).*?"
    r"変わらず \(\((?P<target>[1-9][0-9]*)\) 参照\)"
)
ARCHIVE_PHASE_TOKEN_RE = re.compile(r"phase[0-9]+")
ARCHIVE_MMDD_TOKEN_RE = re.compile(
    r"(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])"
)
ARCHIVE_ENTRY_TOKEN_RE = re.compile(r"[1-9][0-9]*")
ARCHIVE_README_CLAIM_RE = re.compile(
    r"`(?P<name>worklog-[^`/]+\.md)`\s*—\s*worklog の\s*"
    r"(?P<date1>[0-9]{4}-[0-9]{2}-[0-9]{2})\s*"
    r"\((?P<lo>[1-9][0-9]*)\)"
    r"(?:\s*〜\s*(?:(?P<date2>(?:[0-9]{4}-)?[0-9]{2}-[0-9]{2})\s*)?"
    r"\((?P<hi>[1-9][0-9]*)\))?\s*分"
)
ARCHIVE_README_NAME_RE = re.compile(r"`(?P<name>worklog-[^`/]+\.md)`")
DEFERRED_LEDGER_HEADING_RE = re.compile(
    r"^## 見送り台帳(?:[ \t][^\n]*)?$", re.MULTILINE
)
COMPLETION_RECORD_HEADING_RE = re.compile(
    r"^### 裁定・完了記録(?:[ \t][^\n]*)?$", re.MULTILINE
)


@dataclass
class _ArchiveWorklog:
    path: Path
    text: str
    entries: list[tuple[str, str, int]]
    next_actions: list[tuple[str, int] | None]
    sources: list[set[str]]


@dataclass(frozen=True)
class _CarryReference:
    path: str
    line: int
    task_id: str
    source_entry: int
    target_entry: int
    source_h2_digest: str
    item_digest: str


@dataclass(frozen=True)
class _CarrySource:
    path: str
    whole_text: str
    source_entry: int
    h2_raw_line: str
    section_body: str
    section_offset: int


@dataclass
class _CarryScanStats:
    candidate_count: int = 0
    parsed_count: int = 0
    invalid_count: int = 0
    invalid_samples: list[str] | None = None

    def __post_init__(self) -> None:
        if self.invalid_samples is None:
            self.invalid_samples = []


@dataclass(frozen=True)
class _ArchiveFilenameClaim:
    classification: str
    entry_range: tuple[int, int] | None = None


@dataclass
class _BacklogCheckResult:
    numbered_archive_entries: dict[str, frozenset[int] | None]
    archive_scan_complete: bool

# --- 参照実在性 (2026-07-11 追加、docs 整備) ---
# living docs 中の「実在しない D 番号」「実在しないファイルパス」への参照 = 腐敗。
# 凍結族 (worklog/decisions/insights/archive) は対象外 — 書いた時点で正しければよい。
D_REF = re.compile(r"\bD(\d{1,3})\b")
# パスは既知のトップディレクトリ始まりに限定 (submodule 内 cc/ 等は pin 固定で腐らないので対象外)。
# プレースホルダ (<日付> 等)・glob (*) は文字クラス外なのでマッチが切れ、拡張子必須で自然に除外される。
# 負の後読み: external/ccbench/docs/... のような長いパスの途中を docs/... と誤マッチしない
PATH_REF = re.compile(r"(?<![\w/])(?:docs|tools|orchestrator|hooks|patches|output|src|\.claude|\.codex)/[\w.\-/]+\.[A-Za-z0-9]+")


@dataclass(frozen=True)
class _ReadTextCacheEntry:
    outcome: str
    payload: str
    identity: tuple[int, int, int, int, int, int]


_READ_TEXT_CACHE: ContextVar[
    dict[tuple[Path, str | None], _ReadTextCacheEntry] | None
] = ContextVar("check_docs_read_text_cache", default=None)


def _safe_read_text(
    path: Path,
    findings: list[str],
    failure_prefix: str,
    *,
    newline: str | None = None,
    unsafe_path_prefix: str | None = None,
    invalid_utf8_prefix: str | None = None,
) -> str | None:
    """読取不能を集約 finding に変換し、symlink / 非 regular は開かない。"""

    try:
        # final component だけでなく repo 内の親 component も検査する。
        # 例えば docs/archive が symlink のとき README.md 自体は symlink ではないため、
        # path.is_symlink() だけでは外部 target を開いてしまう。
        candidate = path
        while True:
            if candidate.is_symlink():
                findings.append(
                    f"{unsafe_path_prefix or failure_prefix} "
                    f"(symlink を含む path は読まない: {candidate})"
                )
                return None
            if candidate == REPO or candidate.parent == candidate:
                break
            candidate = candidate.parent

        path_stat = path.lstat()
        if not stat.S_ISREG(path_stat.st_mode):
            findings.append(
                f"{unsafe_path_prefix or failure_prefix} "
                f"(regular file でないため読まない: {path})"
            )
            return None
    except OSError as exc:
        findings.append(
            f"{failure_prefix} ({type(exc).__name__}: {exc})"
        )
        return None

    # path と newline が同じ呼出しだけ本文を共有する。cache hit でも上の
    # symlink / lstat 判定は毎回行い、呼出し時点の安全判定を飛ばさない。
    cache = _READ_TEXT_CACHE.get()
    cache_key = (path, newline)
    identity = (
        path_stat.st_mode,
        path_stat.st_mtime_ns,
        path_stat.st_ctime_ns,
        path_stat.st_size,
        path_stat.st_ino,
        path_stat.st_dev,
    )
    # 既存 lstat で観測できる identity が変わった場合だけ stale と判定する。
    # 6 値を保ったまま本文だけが変わる差し替えは既知の残差として残る。
    cached = cache.get(cache_key) if cache is not None else None
    if cached is not None and cached.identity != identity:
        cache.pop(cache_key, None)
        cached = None
    if cached is None and cache is not None and newline is None:
        # newline="" の本文は改行を変換しない基底表現として共有できる。
        # newline=None の返り値は別 key に CR/LF 変換後の本文を保存する。
        raw = cache.get((path, ""))
        if raw is not None and raw.identity != identity:
            cache.pop((path, ""), None)
            raw = None
        if raw is not None:
            cached = (
                _ReadTextCacheEntry(
                    "text",
                    raw.payload.replace("\r\n", "\n").replace("\r", "\n"),
                    identity,
                )
                if raw.outcome == "text"
                else raw
            )
            cache[cache_key] = cached
    if cached is not None:
        if cached.outcome == "text":
            return cached.payload
        prefix = (
            invalid_utf8_prefix or failure_prefix
            if cached.outcome == "invalid-utf8"
            else failure_prefix
        )
        findings.append(f"{prefix} ({cached.payload})")
        return None

    # main 内の newline=None は raw text を一度だけ取得して変換する。これにより
    # newline="" と返り値を混同せず、同じ file の物理読取だけを共有できる。
    open_newline = "" if cache is not None and newline is None else newline
    try:
        with path.open("r", encoding="utf-8", newline=open_newline) as stream:
            text = stream.read()
    except UnicodeDecodeError as exc:
        detail = f"{type(exc).__name__}: {exc}"
        if cache is not None:
            entry = _ReadTextCacheEntry("invalid-utf8", detail, identity)
            cache[cache_key] = entry
            if newline is None:
                cache[(path, "")] = entry
        findings.append(
            f"{invalid_utf8_prefix or failure_prefix} "
            f"({detail})"
        )
        return None
    except OSError as exc:
        detail = f"{type(exc).__name__}: {exc}"
        if cache is not None:
            entry = _ReadTextCacheEntry("os-error", detail, identity)
            cache[cache_key] = entry
            if newline is None:
                cache[(path, "")] = entry
        findings.append(
            f"{failure_prefix} ({detail})"
        )
        return None
    if cache is not None:
        if newline is None:
            cache[(path, "")] = _ReadTextCacheEntry("text", text, identity)
            text = text.replace("\r\n", "\n").replace("\r", "\n")
        cache[cache_key] = _ReadTextCacheEntry("text", text, identity)
    return text


def _check_spool_guard(
    findings: list[str],
    *,
    expected_transaction_id: str | None = None,
) -> None:
    """spool schema/参照検査を fail-closed で finding 化する。"""

    source = REPO / "tools" / "spool_fold.py"
    module_name = "_izanagi_spool_fold_guard"
    previous_module = sys.modules.get(module_name)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    try:
        spec = importlib.util.spec_from_file_location(module_name, source)
        if spec is None or spec.loader is None:
            raise ImportError("import spec/loader を作成できない")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
        validate_spool_tree = getattr(module, "validate_spool_tree")
        if not callable(validate_spool_tree):
            raise TypeError("validate_spool_tree が callable でない")
    except (Exception, SystemExit) as exc:  # SystemExit(0) でも検査を蒸発させない。
        findings.append(
            "tools/spool_fold.py: spool schema guard の import 失敗 — "
            f"{type(exc).__name__}: {exc}"
        )
        return
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module

    try:
        validator_kwargs = (
            {"expected_transaction_id": expected_transaction_id}
            if expected_transaction_id is not None
            else {}
        )
        issues = sorted(
            validate_spool_tree(REPO, **validator_kwargs),
            key=lambda issue: (
                issue.path,
                issue.line,
                issue.code,
                issue.message,
            ),
        )
        rendered = [
            f"{issue.path}:{issue.line}: spool {issue.code}: {issue.message}"
            for issue in issues
        ]
    except (Exception, SystemExit) as exc:  # validator の SystemExit(0) も緑にしない。
        findings.append(
            "tools/spool_fold.py: spool schema guard の実行失敗 — "
            f"{type(exc).__name__}: {exc}"
        )
        return
    findings.extend(rendered)


def _current_pin(findings: list[str]) -> str | None:
    """pin.CURRENT_PIN の現在値を pin.py から抽出する (import せず正規表現 — 単体スクリプトのため)。

    living docs にこの値の literal が書かれると pin 前進で黙って腐る (2026-07-12 監査:
    runbook のゲート行が該当)。値の正本は pin.py であり、docs は `pin.CURRENT_PIN` への
    記号参照で書く。抽出に失敗したら None を返し、main が違反として可視化する
    (黙って skip すると検査自体が蒸発する — tests/README.md の疑似スキップ禁止と同系)。
    """
    pin_py = REPO / "orchestrator" / "campaign" / "pin.py"
    if not pin_py.exists():
        return None
    text = _safe_read_text(
        pin_py,
        findings,
        "orchestrator/campaign/pin.py: pin literal 検査の読取失敗",
    )
    if text is None:
        return None
    m = re.search(r'^CURRENT_PIN\s*=\s*"([0-9a-f]{7,40})"', text, re.MULTILINE)
    return m.group(1) if m else None


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _extract_current_entries(
    text: str, findings: list[str]
) -> list[tuple[str, str, int]] | None:
    """現行 worklog の entry を構造検証して抽出する。失敗は空集合にしない。"""

    rotations = list(ROTATION_RE.finditer(text))
    if len(rotations) != 1:
        findings.append(
            f"docs/worklog.md: `## ローテーション` が {len(rotations)} 件 — "
            "一意に entry 範囲を抽出できない"
        )
        return None

    rotation = rotations[0]
    h2s = [m for m in WORKLOG_H2_RE.finditer(text) if m.start() > rotation.start()]
    invalid = [m for m in h2s if WORKLOG_ENTRY_TITLE_RE.fullmatch(m.group("title")) is None]
    for m in invalid:
        findings.append(
            f"docs/worklog.md:{_line_number(text, m.start())}: ローテーション以後の H2 "
            f"{m.group('title')!r} が worklog entry title に full-match しない"
        )
    if invalid:
        return None
    if not h2s:
        findings.append(
            "docs/worklog.md: ローテーション以後の worklog エントリが 0 件 — "
            "保存則検査が蒸発している"
        )
        return None

    entries: list[tuple[str, str, int]] = []
    for i, h2 in enumerate(h2s):
        body_end = h2s[i + 1].start() if i + 1 < len(h2s) else len(text)
        entries.append((h2.group("title"), text[h2.end():body_end], h2.end()))
    return entries


def _extract_archive_entries(
    path: Path, text: str, findings: list[str]
) -> list[tuple[str, str, int]] | None:
    """ローテーション済み worklog の entry を抽出する。archive 自体に marker はない。"""

    rel = path.relative_to(REPO)
    h2s = list(WORKLOG_H2_RE.finditer(text))
    if not h2s:
        findings.append(
            f"{rel}: 日付付き worklog entry が 0 件 — archive の遷移を検査できない"
        )
        return None

    invalid = [
        m for m in h2s
        if ARCHIVE_WORKLOG_ENTRY_TITLE_RE.fullmatch(m.group("title")) is None
    ]
    for m in invalid:
        findings.append(
            f"{rel}:{_line_number(text, m.start())}: H2 {m.group('title')!r} が "
            "archive worklog entry title に full-match しない"
        )
    if invalid:
        return None

    entries: list[tuple[str, str, int]] = []
    for i, h2 in enumerate(h2s):
        body_end = h2s[i + 1].start() if i + 1 < len(h2s) else len(text)
        entries.append((h2.group("title"), text[h2.end():body_end], h2.end()))
    return entries


def _extract_next_action(
    rel: str,
    whole_text: str,
    entry: tuple[str, str, int],
    findings: list[str],
) -> tuple[str, int] | None:
    """entry の「次の一手」を一意抽出する。0/複数を必ず finding にする。"""

    title, body, body_offset = entry
    sections = list(NEXT_ACTION_RE.finditer(body))
    if len(sections) != 1:
        findings.append(
            f"{rel}: エントリ {title!r} の `### 次の一手` が {len(sections)} 件 — "
            "source を一意に抽出できない"
        )
        return None
    section = sections[0]
    return section.group("body"), body_offset + section.start("body")


def _mask_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """HTML comment を同じ長さの空白へ置換し、行をまたぐ状態を返す。"""

    visible: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                visible.append(" " * (len(line) - cursor))
                cursor = len(line)
            else:
                end += len("-->")
                visible.append(" " * (end - cursor))
                cursor = end
                in_comment = False
            continue

        start = line.find("<!--", cursor)
        if start < 0:
            visible.append(line[cursor:])
            cursor = len(line)
        else:
            visible.append(line[cursor:start])
            cursor = start
            in_comment = True
    return "".join(visible), in_comment


def _dispatch_visible_markdown_lines(text: str) -> list[tuple[str, int, str]]:
    """reference 契約用に raw HTML block も除いた可視行を返す。"""

    return visible_top_level_lines(text, reject_unicode_separators=False)


def _visible_markdown_lines(text: str) -> list[tuple[str, int, str]]:
    """code fence / HTML comment 外の可視行と offset・改行を返す。"""

    lines: list[tuple[str, int, str]] = []
    in_comment = False
    fence: tuple[str, int] | None = None
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        newline = raw_line[len(line):]
        if fence is not None:
            marker_char, marker_len = fence
            stripped = line.lstrip(" \t")
            indent = len(line) - len(stripped)
            if indent <= 3 and re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*", stripped
            ):
                fence = None
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue

        # fence opener の info string 内にある `<!--` は comment 開始ではない。
        # comment 継続中でない行は opener を先に判定する。
        if not in_comment:
            fence_match = FENCE_OPEN_RE.fullmatch(line)
            if fence_match is not None:
                marker = fence_match.group("marker")
                fence = (marker[0], len(marker))
                lines.append(("", offset, newline))
                offset += len(raw_line)
                continue

        visible, in_comment = _mask_html_comments(line, in_comment)
        fence_match = FENCE_OPEN_RE.fullmatch(visible)
        if fence_match is not None:
            marker = fence_match.group("marker")
            fence = (marker[0], len(marker))
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue

        lines.append((visible, offset, newline))
        offset += len(raw_line)
    return lines


def _visible_markdown_text(text: str) -> str:
    """Markdown の不可視部分を除き、元の行境界を保った文字列を返す。"""

    return "".join(
        visible + newline
        for visible, _, newline in _visible_markdown_lines(text)
    )


def _visible_dispatch_inventory_text(text: str) -> str:
    """reference 契約抽出用に raw HTML block も不可視化する。"""

    return "".join(
        visible + newline
        for visible, _, newline in _dispatch_visible_markdown_lines(text)
    )


def _h2_section_slices(text: str) -> tuple[list[str], dict[str, list[str]]]:
    """与えられた Markdown の H2 順序と節全体 slice を返す。"""

    headings = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    order: list[str] = []
    sections: dict[str, list[str]] = {}
    for index, heading in enumerate(headings):
        title = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        order.append(title)
        sections.setdefault(title, []).append(text[heading.start():end])
    return order, sections


def _visible_h2_section_slices(text: str) -> tuple[list[str], dict[str, list[str]]]:
    """dispatch 可視化後の H2 順序と節全体 slice を返す。"""

    return _h2_section_slices(_visible_dispatch_inventory_text(text))


def _r33_python_code_mask(source: str) -> str:
    """Python の文字列と comment を空白化し、改行と code を残す。"""

    chars = list(source)
    quote: str | None = None
    triple = False
    escaped = False
    comment = False
    index = 0
    while index < len(source):
        char = source[index]
        if comment:
            if char in "\r\n":
                comment = False
            else:
                chars[index] = " "
            index += 1
            continue

        if quote is not None:
            if escaped:
                if char not in "\r\n":
                    chars[index] = " "
                escaped = False
                index += 1
                continue
            if char == "\\":
                chars[index] = " "
                escaped = True
                index += 1
                continue
            if triple and source.startswith(quote * 3, index):
                chars[index:index + 3] = [" "] * 3
                quote = None
                triple = False
                index += 3
                continue
            if not triple and char == quote:
                chars[index] = " "
                quote = None
                index += 1
                continue
            if char not in "\r\n":
                chars[index] = " "
            index += 1
            continue

        if char == "#":
            chars[index] = " "
            comment = True
        elif char in {"'", '"'}:
            if source.startswith(char * 3, index):
                chars[index:index + 3] = [" "] * 3
                quote = char
                triple = True
                index += 3
                continue
            chars[index] = " "
            quote = char
            triple = False
        index += 1

    return "".join(chars)


def _r33_observation_roles_span(
    source: str,
    findings: list[str],
) -> tuple[int, int] | None:
    """`_OBSERVATION_ROLES` の実体辞書リテラルの source span を返す。"""

    code = _r33_python_code_mask(source)
    declarations = list(R33_OBSERVATION_ROLES_DECL_RE.finditer(code))
    if len(declarations) != 1:
        findings.append(
            "R33 _OBSERVATION_ROLES 宣言は exact 1 件が必要"
        )
        return None

    opening = declarations[0].end() - 1
    depth = 0
    for index in range(opening, len(code)):
        char = code[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return opening, index + 1
            if depth < 0:
                break

    findings.append(
        "R33 _OBSERVATION_ROLES の対応する閉じ括弧を特定できない"
    )
    return None


def _r33_source_contract(
    source: str,
    findings: list[str],
) -> dict[str, object] | None:
    roles_span = _r33_observation_roles_span(source, findings)
    if roles_span is None:
        return None

    code = _r33_python_code_mask(source)
    role_name = "OBSERVATION_ROLE_N_PILOT_R33"
    role_matches = []
    for match in R33_ROLE_RE.finditer(source):
        name_start = source.find(role_name, match.start(), match.end())
        if (
            name_start >= 0
            and code[name_start:name_start + len(role_name)] == role_name
        ):
            role_matches.append(match)
    entries = []
    for match in R33_SOURCE_ENTRY_RE.finditer(source):
        opening_offset = match.group().find("{")
        if (
            opening_offset >= 0
            and roles_span[0] <= match.start()
            and match.end() <= roles_span[1]
            and code[match.start() + opening_offset] == "{"
        ):
            entries.append(match)

    if len(role_matches) != 1:
        findings.append(
            "R33 role literal は OBSERVATION_ROLE_N_PILOT_R33 "
            "の exact 1 件が必要"
        )
        return None

    if len(entries) != 1:
        findings.append(
            "R33 role contract entry は exact 1 件が必要"
        )
        return None

    values: dict[str, object] = {
        "role": role_matches[0].group("role"),
    }
    body = entries[0].group("body")

    for name, pattern in R33_SOURCE_FIELD_RE.items():
        matches = list(pattern.finditer(body))
        if len(matches) != 1:
            findings.append(
                f"R33 role contract field {name!r} は exact 1 件が必要"
            )
            return None
        value = matches[0].group("value")
        values[name] = (
            int(value)
            if name in {
                "pilot_rounds",
                "allocation_count",
                "cell_count",
                "schedule_row_count",
            }
            else value
        )

    return values


def _r33_decision_contract_in_text(
    text: str,
    findings: list[str],
    *,
    pending: bool,
) -> bool:
    _, raw_sections = _h2_section_slices(text)
    _, visible_sections = _visible_h2_section_slices(text)

    heading_re = (
        R33_PENDING_HEADING_RE
        if pending
        else R33_DECISION_HEADING_RE
    )

    candidates: list[tuple[str, int, str, list[str]]] = []
    for heading, sections in visible_sections.items():
        if heading_re.match(heading) is None:
            continue

        # `R33_DECISION_HEADING_RE` は canonical D 節全体に一致するため、
        # R33 固有の marker を持つ heading group だけを候補として数える。
        # その group の全 section を残すことで、同じ heading の valid/invalid
        # 重複を先頭の成功だけで通さない。
        if not any(
            R33_DECISION_SLUG_RE.search(section) is not None
            or R33_DECISION_CONTRACT_RE.search(section) is not None
            for section in sections
        ):
            continue
        raw_candidates = raw_sections.get(heading, [])
        candidates.extend(
            (heading, index, section, raw_candidates)
            for index, section in enumerate(sections)
        )

    if len(candidates) > 1:
        findings.append(
            "R33 decision section が曖昧 — 条件に合致する section は "
            f"exact 1 件が必要 (observed={len(candidates)})"
        )
        return False
    if not candidates:
        return False

    _, index, section, raw_candidates = candidates[0]
    slug_match = R33_DECISION_SLUG_RE.search(section)
    contract_match = R33_DECISION_CONTRACT_RE.search(section)
    if slug_match is None or contract_match is None:
        return False

    if (
        index >= len(raw_candidates)
        or raw_candidates[index] != section
    ):
        findings.append(
            "R33 decision section の raw/visible slice が不一致"
        )
        return False

    decision = contract_match.groupdict()
    observed = {
        "role": decision["role"],
        "generation": decision["generation"],
        "pilot_rounds": int(decision["pilot_rounds"]),
        "allocation_count": int(decision["allocation_count"]),
        "cell_count": int(decision["cell_count"]),
        "schedule_row_count": int(decision["schedule_row_count"]),
    }
    if (
        slug_match.group("slug") == R33_DECISION_SLUG
        and observed == {
            key: R33_EXPECTED[key]
            for key in (
                "role",
                "generation",
                "pilot_rounds",
                "allocation_count",
                "cell_count",
                "schedule_row_count",
            )
        }
    ):
        return True

    return False


def _pending_r33_decision_fragments(
    findings: list[str],
) -> list[str]:
    directory = REPO / "docs" / "spool" / "decisions"
    if not directory.exists() or directory.is_symlink() or not directory.is_dir():
        return []

    texts: list[str] = []
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        text = _safe_read_text(
            path,
            findings,
            f"{path.relative_to(REPO)}: R33 decision fragment の読取失敗",
            newline="",
        )
        if (
            text is not None
            and f"{{{{D:{R33_DECISION_SLUG}}}}}" in text
        ):
            texts.append(text)
    return texts


def _check_n_pilot_role_decision_pin(
    findings: list[str],
    *,
    decisions_text: str | None,
) -> None:
    source = _safe_read_text(
        REPO / "orchestrator" / "campaign" / "s8b_holdout_admission.py",
        findings,
        "R33 role authority source の読取失敗",
    )
    if source is None or decisions_text is None:
        findings.append(
            "R33 role authority は source/decision の読取失敗で検査不能"
        )
        return

    source_values = _r33_source_contract(source, findings)
    if source_values is None:
        return

    if source_values != R33_EXPECTED:
        findings.append(
            "R33 role contract の role/generation/round/allocation/pin が "
            f"expected と不一致 — observed={source_values!r}"
        )
        return

    if _r33_decision_contract_in_text(
        decisions_text,
        findings,
        pending=False,
    ):
        return

    # wave tree では canonical decision はまだ fold 前である。
    # 同じ wave の exact fragment がある場合だけ pre-fold lint を通す。
    for fragment in _pending_r33_decision_fragments(findings):
        if _r33_decision_contract_in_text(
            fragment,
            findings,
            pending=True,
        ):
            return

    findings.append(
        "R33 role contract に対応する decision section がない — "
        "canonical docs/decisions.md または exact pending fragment が必要"
    )


def _check_exact_visible_h2_section(
    findings: list[str],
    *,
    rel: str,
    text: str,
    heading: str,
    expected: str,
) -> None:
    """H2 節の raw/可視一致と可視内容を exact pin する。"""

    _, raw_sections = _h2_section_slices(text)
    _, visible_sections = _visible_h2_section_slices(text)
    raw_actual = raw_sections.get(heading, [])
    visible_actual = visible_sections.get(heading, [])
    if raw_actual != visible_actual:
        findings.append(
            f"{rel}: H2 節 {heading!r} の raw slice と可視 slice が不一致 — "
            f"raw_sections={len(raw_actual)}, "
            f"visible_sections={len(visible_actual)}"
        )
    if visible_actual != [expected]:
        findings.append(
            f"{rel}: 可視 H2 節 {heading!r} の節全体が exact 契約と不一致 — "
            f"sections={len(visible_actual)}"
        )


def _top_level_items(body: str) -> Iterator[tuple[str, int]]:
    """code fence / HTML comment 外にあるトップレベル項目を逐次返す。"""

    for visible, offset, _ in _visible_markdown_lines(body):
        item = TOP_LEVEL_ITEM_RE.fullmatch(visible)
        if item is not None:
            yield item.group("text"), offset


def _top_level_ids(body: str) -> list[str]:
    """トップレベル list item の先頭にある有効 ID だけを返す。"""

    ids: list[str] = []
    for item_text, _ in _top_level_items(body):
        match = TASK_ID_AT_HEAD_RE.match(item_text)
        if match:
            ids.append(match.group("id"))
    return ids


def _entry_h2_raw_line(
    whole_text: str,
    entry: tuple[str, str, int],
) -> str:
    """entry tuple の body offset 直前にある H2 raw 物理行を返す。"""

    h2_end = entry[2]
    h2_start = whole_text.rfind("\n", 0, h2_end) + 1
    return whole_text[h2_start:h2_end]


def _top_level_item_raw_slice(body: str, item_offset: int) -> str:
    """list marker から継続物理行の終端までの raw slice を返す。"""

    assert 0 <= item_offset < len(body)
    line_end = item_offset
    while line_end < len(body) and body[line_end] not in "\r\n":
        line_end += 1
    raw_end = line_end
    cursor = line_end
    while cursor < len(body):
        if body[cursor] == "\r":
            cursor += 1
            if cursor < len(body) and body[cursor] == "\n":
                cursor += 1
        elif body[cursor] == "\n":
            cursor += 1
        continuation_end = cursor
        while (
            continuation_end < len(body)
            and body[continuation_end] not in "\r\n"
        ):
            continuation_end += 1
        continuation = body[cursor:continuation_end]
        if not continuation.startswith((" ", "\t")):
            break
        raw_end = continuation_end
        cursor = continuation_end
    return body[item_offset:raw_end]


def _is_carry_candidate(item_text: str) -> bool:
    """厳密 parser の取りこぼしを拾う、意図的に広い carry 候補述語。"""

    task = TASK_ID_AT_HEAD_RE.match(item_text)
    if task is None:
        return False
    unchanged_at = item_text.find("変わらず", task.end())
    reference_at = item_text.find("参照", unchanged_at + len("変わらず"))
    if (
        unchanged_at >= 0
        and reference_at > unchanged_at
        and re.search(
            r"[0-9]", item_text[unchanged_at:reference_at]
        ) is not None
    ):
        return True
    return re.fullmatch(
        r"[ \t]*\((?=[ \t0-9]*[0-9])[ \t0-9]*\)",
        item_text[task.end():],
    ) is not None


def _iter_carry_references(
    sources: Iterable[_CarrySource],
    stats: _CarryScanStats | None = None,
) -> Iterator[_CarryReference]:
    """carry occurrence を entry source 群から逐次 yield する。"""

    scan = stats if stats is not None else _CarryScanStats()
    for source in sources:
        source_h2_digest = _placeholder_line_digest(source.h2_raw_line)
        for item_text, item_offset in _top_level_items(source.section_body):
            candidate = _is_carry_candidate(item_text)
            carry = CARRY_REFERENCE_RE.fullmatch(item_text)
            if carry is None:
                carry = LEGACY_CARRY_REFERENCE_RE.search(item_text)
            if candidate:
                scan.candidate_count += 1
            if carry is None:
                if candidate:
                    scan.invalid_count += 1
                    assert scan.invalid_samples is not None
                    if len(scan.invalid_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
                        lineno = _line_number(
                            source.whole_text,
                            source.section_offset + item_offset,
                        )
                        scan.invalid_samples.append(
                            f"{source.path}:{lineno}: carry 風 candidate {item_text!r} が"
                            "厳密 carry 文法に一致しない — 正例: `- [T-1219] (953)`"
                        )
                continue
            # 厳密 parser の受理集合は広い candidate 集合の部分集合でなければならない。
            # 将来この前提を壊す parser 変更も candidate == parsed で赤にする。
            scan.parsed_count += 1
            yield _CarryReference(
                source.path,
                _line_number(
                    source.whole_text,
                    source.section_offset + item_offset,
                ),
                carry.group("id"),
                source.source_entry,
                int(carry.group("target")),
                source_h2_digest,
                _placeholder_line_digest(
                    _top_level_item_raw_slice(
                        source.section_body,
                        item_offset,
                    )
                ),
            )


def _validate_next_action_items(
    rel: str,
    whole_text: str,
    entry: tuple[str, str, int],
    section: tuple[str, int],
    findings: list[str],
    *,
    latest: bool = False,
) -> None:
    """ID 導入済み entry の次の一手について ID 完備性と重複を検査する。"""

    title, _, _ = entry
    section_body, section_offset = section
    label = "末尾エントリ" if latest else f"エントリ {title!r}"
    seen: set[str] = set()
    for item_text, item_offset in _top_level_items(section_body):
        valid = TASK_ID_AT_HEAD_RE.match(item_text)
        lineno = _line_number(whole_text, section_offset + item_offset)
        if valid is None:
            invalid = TASK_ID_LIKE_AT_HEAD_RE.match(item_text)
            if invalid is not None:
                findings.append(
                    f"{rel}:{lineno}: {label} の `### 次の一手` のトップレベル"
                    f"項目先頭 ID {invalid.group(0)!r} が不正形式"
                )
            else:
                findings.append(
                    f"{rel}:{lineno}: {label} の `### 次の一手` の "
                    "トップレベル項目先頭に有効な [T-NNN] ID がない"
                )
            continue

        task_id = valid.group("id")
        if task_id in seen:
            findings.append(
                f"{rel}:{lineno}: {label} の `### 次の一手` 内で ID {task_id} が重複"
            )
        seen.add(task_id)


def _archive_filename_entry_range(path: Path) -> _ArchiveFilenameClaim:
    """archive 名を正規文法で非採番・採番・malformed に分類する。"""

    name = path.name
    if not name.startswith("worklog-"):
        return _ArchiveFilenameClaim("unnumbered")
    remainder = name[len("worklog-"):]
    if re.match(r"phase[0-9]+-", remainder) is None:
        if name.endswith(".md"):
            tokens = remainder[:-len(".md")].split("-")
            if any(
                ARCHIVE_ENTRY_TOKEN_RE.fullmatch(token) is not None
                for token in tokens
            ):
                return _ArchiveFilenameClaim("malformed")
        return _ArchiveFilenameClaim("unnumbered")
    if not name.endswith(".md"):
        return _ArchiveFilenameClaim("malformed")
    tokens = name[len("worklog-"):-len(".md")].split("-")
    phase_token, tail = tokens[0], tokens[1:]
    if ARCHIVE_PHASE_TOKEN_RE.fullmatch(phase_token) is None:
        return _ArchiveFilenameClaim("unnumbered")

    phase_number = phase_token[len("phase"):]
    if (
        re.fullmatch(r"[1-9][0-9]?", phase_number) is not None
        and len(tail) == 1
        and re.fullmatch(r"[1-9][0-9]?", tail[0]) is not None
    ):
        # Phase 1〜2 のような phase 範囲名。
        return _ArchiveFilenameClaim("unnumbered")

    is_mmdd = lambda token: ARCHIVE_MMDD_TOKEN_RE.fullmatch(token) is not None
    is_entry = lambda token: ARCHIVE_ENTRY_TOKEN_RE.fullmatch(token) is not None
    if len(tail) == 2 and is_mmdd(tail[0]) and is_entry(tail[1]):
        entry_tokens = (tail[1], tail[1])
    elif len(tail) in {1, 2} and all(is_mmdd(token) for token in tail):
        return _ArchiveFilenameClaim("unnumbered")
    elif (
        len(tail) == 3
        and is_mmdd(tail[0])
        and is_entry(tail[1])
        and is_entry(tail[2])
    ):
        entry_tokens = (tail[1], tail[2])
    elif (
        len(tail) == 4
        and is_mmdd(tail[0])
        and is_entry(tail[1])
        and is_mmdd(tail[2])
        and is_entry(tail[3])
    ):
        entry_tokens = (tail[1], tail[3])
    else:
        return _ArchiveFilenameClaim("malformed")
    return _ArchiveFilenameClaim("numbered", tuple(map(int, entry_tokens)))


def _entry_number_from_title(title: str) -> int | None:
    match = ARCHIVE_WORKLOG_ENTRY_TITLE_RE.fullmatch(title)
    if match is None:
        raise ValueError(f"invalid archive entry title: {title!r}")
    order = match.group("order")
    return int(order) if order is not None and order.isdigit() else None


def _compact_number_ranges(numbers: list[int]) -> str:
    if not numbers:
        return "なし"
    chunks: list[str] = []
    start = previous = numbers[0]
    for number in numbers[1:]:
        if number == previous + 1:
            previous = number
            continue
        chunks.append(str(start) if start == previous else f"{start}〜{previous}")
        start = previous = number
    chunks.append(str(start) if start == previous else f"{start}〜{previous}")
    return ",".join(chunks)


def _missing_entry_ranges(actual: list[int], lo: int, hi: int) -> str:
    if lo > hi:
        return "範囲逆転"
    chunks: list[str] = []
    expected = lo
    for number in actual:
        if number < lo or number > hi:
            continue
        if number > expected:
            end = number - 1
            chunks.append(str(expected) if expected == end else f"{expected}〜{end}")
        expected = number + 1
    if expected <= hi:
        chunks.append(str(expected) if expected == hi else f"{expected}〜{hi}")
    return ",".join(chunks) if chunks else "なし"


def _validate_claimed_entry_range(
    label: str,
    claim: tuple[int, int],
    actual_entries: frozenset[int],
    findings: list[str],
) -> None:
    lo, hi = claim
    actual = sorted(actual_entries)
    outside = [number for number in actual if number < lo or number > hi]
    missing = _missing_entry_ranges(actual, lo, hi)
    if lo <= hi and not outside and missing == "なし":
        return
    findings.append(
        f"{label} が名乗る entry 範囲 ({lo})〜({hi}) と実体 entry 集合が不一致 — "
        f"欠番={missing}, 範囲外={_compact_number_ranges(outside)}"
    )


def _append_sampled_findings(
    findings: list[str],
    category: str,
    samples: Sequence[str],
    total: int,
    *,
    unit: str = "carry occurrence",
) -> None:
    """分類別 finding を上限付きで出し、抑止件数を必ず明示する。"""

    if total == 0:
        return
    findings.extend(samples)
    suppressed = max(0, total - len(samples))
    findings.append(
        f"carry {category}: 他 {suppressed} 件を抑止"
    )
    if unit == "carry occurrence":
        findings.append(
            f"carry {category}: 上記の {suppressed} 件は target 数でなく "
            "carry occurrence 数"
        )
    else:
        findings.append(
            f"carry {category}: 上記の {suppressed} 件の単位は {unit}"
        )


def _validate_entry_universe(
    locations: Mapping[int, list[str]],
    next_action_ids_by_entry: Mapping[int, set[str] | None],
    carry_sources: Sequence[_CarrySource],
    findings: list[str],
    *,
    numbered_archive_input_complete: bool,
) -> None:
    duplicated = {
        number for number, number_locations in locations.items()
        if len(number_locations) > 1
    }
    for number in sorted(duplicated):
        findings.append(
            f"docs/worklog.md / docs/archive: 全域 entry 番号 ({number}) が複数箇所に実在 — "
            + ", ".join(locations[number])
        )
    if not numbered_archive_input_complete:
        findings.append(
            "docs/archive: 番号付き archive 入力が不完全 — "
            "carry 参照先の実在検査を停止"
        )
        return

    registered_total = sum(
        expected
        for entries in KNOWN_CARRY_ID_MISMATCHES.values()
        for expected in entries.values()
    )
    if registered_total != EXPECTED_KNOWN_CARRY_ID_MISMATCHES:
        findings.append(
            "KNOWN_CARRY_ID_MISMATCHES の登録 occurrence 総数が不一致 — "
            f"expected={EXPECTED_KNOWN_CARRY_ID_MISMATCHES}, actual={registered_total}"
        )

    universe = set(locations)
    index = set(next_action_ids_by_entry)
    index_samples: list[str] = []
    index_total = 0
    for number in sorted(universe - index):
        index_total += 1
        if len(index_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
            index_samples.append(
                f"entry ({number}) は全域 universe にあるが次の一手索引 key が不在"
            )
    for number in sorted(index - universe):
        index_total += 1
        if len(index_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
            index_samples.append(
                f"entry ({number}) は次の一手索引にあるが全域 universe に不在"
            )
    _append_sampled_findings(
        findings,
        "universe / index 集合不一致",
        index_samples,
        index_total,
        unit="entry key",
    )

    scan = _CarryScanStats()
    missing_samples: list[_CarryReference] = []
    missing_total = 0
    index_key_missing_samples: list[_CarryReference] = []
    index_key_missing_total = 0
    index_none_samples: list[_CarryReference] = []
    index_none_total = 0
    index_empty_samples: list[_CarryReference] = []
    index_empty_total = 0
    mismatch_samples: list[str] = []
    mismatch_total = 0
    observed_known: dict[tuple[str, str], int] = {}

    for carry in _iter_carry_references(carry_sources, scan):
        target = carry.target_entry
        if target not in locations:
            missing_total += 1
            if len(missing_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
                missing_samples.append(carry)
            continue
        if target in duplicated:
            continue
        if target not in next_action_ids_by_entry:
            index_key_missing_total += 1
            if len(index_key_missing_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
                index_key_missing_samples.append(carry)
            continue
        target_ids = next_action_ids_by_entry[target]
        if target_ids is None:
            index_none_total += 1
            if len(index_none_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
                index_none_samples.append(carry)
            continue
        if not target_ids:
            index_empty_total += 1
            if len(index_empty_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
                index_empty_samples.append(carry)
            continue
        if carry.task_id in target_ids:
            continue

        known_key = (carry.source_h2_digest, carry.item_digest)
        expected = KNOWN_CARRY_ID_MISMATCHES.get(
            carry.source_h2_digest, {}
        ).get(carry.item_digest)
        if expected is not None:
            observed_known[known_key] = observed_known.get(known_key, 0) + 1
            continue

        mismatch_total += 1
        if len(mismatch_samples) < _CARRY_FINDING_SAMPLE_LIMIT:
            target_location = locations[target][0]
            mismatch_samples.append(
                f"{carry.path}:{carry.line}: {carry.task_id} の carry 参照先 entry "
                f"({target}) の次の一手に同じ ID がない — 参照先 H2 "
                f"{target_location}; 参照先の次の一手に同じ ID を置くか、"
                "carry を正しい参照先へ直す"
            )

    if scan.candidate_count != scan.parsed_count:
        assert scan.invalid_samples is not None
        detail = " | ".join(scan.invalid_samples)
        suppressed = max(0, scan.invalid_count - len(scan.invalid_samples))
        findings.append(
            "carry 風 candidate 数と厳密 parse 成功数が不一致 — "
            f"candidate={scan.candidate_count}, parsed={scan.parsed_count}; "
            f"厳密 carry 文法に一致しない sample={detail}; "
            f"他 {suppressed} carry occurrence を抑止"
        )

    missing_sample_text = [
        f"{carry.path}:{carry.line}: {carry.task_id} の carry 参照先 entry "
        f"({carry.target_entry}) が全域番号 universe に実在しない — 宙吊り参照"
        for carry in missing_samples
    ]
    _append_sampled_findings(
        findings,
        "参照先不在",
        missing_sample_text,
        missing_total,
    )

    def target_index_samples(
        references: Sequence[_CarryReference],
        detail: str,
    ) -> list[str]:
        return [
            f"{carry.path}:{carry.line}: {carry.task_id} の carry 参照先 entry "
            f"({carry.target_entry}) の次の一手索引が {detail} — 参照先 H2 "
            f"{locations[carry.target_entry][0]}"
            for carry in references
        ]

    for category, references, total, detail in (
        (
            "索引 key 不在",
            index_key_missing_samples,
            index_key_missing_total,
            "key 不在",
        ),
        (
            "索引値 None",
            index_none_samples,
            index_none_total,
            "値 None (section 抽出対象外)",
        ),
        (
            "索引値空集合",
            index_empty_samples,
            index_empty_total,
            "空集合 (次の一手が空)",
        ),
    ):
        _append_sampled_findings(
            findings,
            category,
            target_index_samples(references, detail),
            total,
        )

    _append_sampled_findings(
        findings,
        "同一 ID 不一致",
        mismatch_samples,
        mismatch_total,
    )

    for source_digest, entries in KNOWN_CARRY_ID_MISMATCHES.items():
        for item_digest, expected in entries.items():
            actual = observed_known.get((source_digest, item_digest), 0)
            if actual == expected:
                continue
            remediation = (
                "凍結 archive を編集せず、復元するか裁定へ返す"
                if actual == 0
                else "凍結 archive を編集せず、重複を裁定へ返す"
            )
            findings.append(
                "KNOWN_CARRY_ID_MISMATCHES の登録 digest が観測数不一致 — "
                f"source_h2={source_digest}, item={item_digest}, "
                f"expected={expected}, actual={actual}; {remediation}"
            )

    if scan.parsed_count < MIN_EXPECTED_CARRY_REFERENCE_COUNT:
        findings.append(
            "carry 参照母数が粗い下限を下回る — "
            f"minimum={MIN_EXPECTED_CARRY_REFERENCE_COUNT}, actual={scan.parsed_count}"
        )


def _archive_readme_items(
    body: str,
    body_offset: int,
) -> Iterator[tuple[str, int]]:
    """「現在の収容物」の物理行を継続行込みの論理項目へ畳む。"""

    current: list[str] | None = None
    current_offset = 0
    offset = 0
    while offset < len(body):
        line_end = offset
        while line_end < len(body) and body[line_end] not in "\r\n":
            line_end += 1
        next_offset = line_end
        if next_offset < len(body):
            next_offset += 1
            if body[line_end] == "\r" and next_offset < len(body) and body[next_offset] == "\n":
                next_offset += 1
        visible = body[offset:line_end]
        if visible.startswith("- "):
            if current is not None:
                yield " ".join(current), body_offset + current_offset
            current = [visible]
            current_offset = offset
        elif current is not None and visible[:1] in {" ", "\t"}:
            current.append(visible.strip())
        offset = next_offset
    if current is not None:
        yield " ".join(current), body_offset + current_offset


def _validate_archive_readme_claims(
    readme_text: str,
    section_body: str,
    section_offset: int,
    backlog: _BacklogCheckResult,
    findings: list[str],
) -> None:
    """README の採番 archive 主張を既読本文の実体集合と照合する。"""

    if not backlog.archive_scan_complete:
        return
    valid_counts = {
        name: 0 for name, entries in backlog.numbered_archive_entries.items()
        if entries is not None
    }
    for item, offset in _archive_readme_items(section_body, section_offset):
        item_names = [match.group("name") for match in ARCHIVE_README_NAME_RE.finditer(item)]
        numbered_names = [
            name for name in item_names
            if name in backlog.numbered_archive_entries
            and backlog.numbered_archive_entries[name] is not None
        ]
        if not numbered_names:
            continue
        lineno = _line_number(readme_text, offset)
        claims = list(ARCHIVE_README_CLAIM_RE.finditer(item))
        for name in numbered_names:
            matching = [claim for claim in claims if claim.group("name") == name]
            if len(matching) != 1:
                findings.append(
                    f"docs/archive/README.md:{lineno}: 番号付き archive {name} の"
                    "「現在の収容物」行から entry 範囲を抽出できない"
                )
                continue
            claim = matching[0]
            valid_counts[name] += 1
            lo = int(claim.group("lo"))
            hi = int(claim.group("hi") or claim.group("lo"))
            actual = backlog.numbered_archive_entries[name]
            assert actual is not None
            _validate_claimed_entry_range(
                f"docs/archive/README.md:{lineno}: {name}",
                (lo, hi),
                actual,
                findings,
            )

    for name, count in sorted(valid_counts.items()):
        if count != 1:
            findings.append(
                "docs/archive/README.md: 実在する番号付き archive "
                f"{name} の正規な「現在の収容物」行が {count} 件 — ちょうど 1 件必要"
            )


def _archive_entry_point(title: str) -> tuple[str, int | None]:
    """archive entry title から、ファイル間順序に使える日付・明示連番を返す。"""

    match = ARCHIVE_WORKLOG_ENTRY_TITLE_RE.fullmatch(title)
    if match is None:  # _extract_archive_entries が先に full-match を保証する。
        raise ValueError(f"invalid archive entry title: {title!r}")
    order = match.group("order")
    return match.group("date"), int(order) if order and order.isdigit() else None


def _entry_point_is_before(left_title: str, right_title: str) -> bool:
    """日付または同日の明示連番から left < right を証明できるときだけ True。"""

    left_date, left_order = _archive_entry_point(left_title)
    right_date, right_order = _archive_entry_point(right_title)
    if left_date != right_date:
        return left_date < right_date
    return (
        left_order is not None
        and right_order is not None
        and left_order < right_order
    )


def _archive_is_before(left: _ArchiveWorklog, right: _ArchiveWorklog) -> bool:
    return _entry_point_is_before(left.entries[-1][0], right.entries[0][0])


def _extract_deferred_ledger(
    text: str, findings: list[str]
) -> tuple[str, int] | None:
    """見送り台帳を完了記録の手前まで抽出する (完了済み ID を sink にしない)。"""

    ledgers = list(DEFERRED_LEDGER_HEADING_RE.finditer(text))
    completions = list(COMPLETION_RECORD_HEADING_RE.finditer(text))
    if len(ledgers) != 1:
        findings.append(
            f"docs/phase3.md: `## 見送り台帳` が {len(ledgers)} 件 — sink を一意に抽出できない"
        )
    if len(completions) != 1:
        findings.append(
            "docs/phase3.md: `### 裁定・完了記録` が "
            f"{len(completions)} 件 — 見送り台帳 sink の終端を一意に抽出できない"
        )
    if len(ledgers) != 1 or len(completions) != 1:
        return None

    ledger = ledgers[0]
    completion = completions[0]
    if completion.start() <= ledger.end():
        findings.append(
            "docs/phase3.md: `### 裁定・完了記録` が `## 見送り台帳` より後にない — "
            "見送り台帳 sink の範囲を抽出できない"
        )
        return None
    # 見出し行を [^\n]* で止めてから範囲を切る。DOTALL 下の `.` に見出し以後を
    # 飲ませると body が空になるため、見出し suffix に `.*` は使わない。
    body_start = ledger.end()
    if body_start < len(text) and text[body_start] == "\n":
        body_start += 1
    return text[body_start:completion.start()], body_start


def _literal_placeholder_targets(
    findings: list[str],
) -> tuple[list[Path], set[Path], bool, bool]:
    """リテラル placeholder の対象 3 族を fail-closed で列挙する。"""

    targets: list[Path] = []
    blocked: set[Path] = set()
    worklog_complete = True
    insights_complete = True
    if not WORKLOG.exists():
        findings.append(
            "docs/worklog.md: placeholder 検査の列挙対象が不在 — "
            "台帳照合と worklog H2 一意性検査を停止"
        )
        worklog_complete = False
    elif WORKLOG.is_symlink() or not WORKLOG.is_file():
        findings.append(
            "docs/worklog.md: placeholder 検査の列挙対象が regular file でない — "
            "台帳照合と worklog H2 一意性検査を停止"
        )
        blocked.add(WORKLOG)
        worklog_complete = False
    else:
        targets.append(WORKLOG)

    families = (
        (ARCHIVE_DIR, "docs/archive", "worklog-*.md"),
        (INSIGHTS_DIR, "output/insights", "*.md"),
    )
    for directory, rel, pattern in families:
        if directory.is_symlink():
            findings.append(
                f"{rel}: placeholder 検査の対象 directory が symlink — "
                "対象族に依存する後続検査を停止"
            )
            blocked.add(directory)
            if directory == ARCHIVE_DIR:
                worklog_complete = False
            else:
                insights_complete = False
            continue
        if not directory.exists():
            findings.append(
                f"{rel}: placeholder 検査の対象 directory が不在 — "
                "対象族に依存する後続検査を停止"
            )
            blocked.add(directory)
            if directory == ARCHIVE_DIR:
                worklog_complete = False
            else:
                insights_complete = False
            continue
        if not directory.is_dir():
            findings.append(
                f"{rel}: placeholder 検査の対象が directory でない — "
                "対象族に依存する後続検査を停止"
            )
            blocked.add(directory)
            if directory == ARCHIVE_DIR:
                worklog_complete = False
            else:
                insights_complete = False
            continue
        members = sorted(directory.glob(pattern))
        if directory == INSIGHTS_DIR:
            # Keep the old direct members; only the new date level is added.
            try:
                date_dirs = sorted(
                    p for p in directory.iterdir()
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)
                )
                for date_dir in date_dirs:
                    if date_dir.is_symlink() or not date_dir.is_dir():
                        raise OSError(f"{date_dir.relative_to(REPO)}: directory でない / symlink")
                    if not date_dir.stat().st_mode & 0o444:
                        raise OSError(f"{date_dir.relative_to(REPO)}: directory が読取不能")
                    # iterdir propagates read errors (glob may suppress them).
                    members.extend(sorted(
                        p for p in date_dir.iterdir() if p.name.endswith(".md")
                    ))
            except OSError as exc:
                findings.append(f"{rel}: placeholder 日付 directory の列挙失敗: {exc}")
                blocked.add(directory)
                insights_complete = False
        if not members:
            findings.append(
                f"{rel}/{pattern}: placeholder 検査の対象族に実体がない — "
                "対象族に依存する後続検査を停止"
            )
            blocked.add(directory)
            if directory == ARCHIVE_DIR:
                worklog_complete = False
            else:
                insights_complete = False
            continue
        regular_members = []
        for member in members:
            member_rel = member.relative_to(REPO)
            if member.is_symlink() or not member.is_file():
                findings.append(
                    f"{member_rel}: placeholder 検査の対象 member が regular file でない — "
                    "対象族に依存する後続検査を停止"
                )
                blocked.add(member)
                if directory == ARCHIVE_DIR:
                    worklog_complete = False
                else:
                    insights_complete = False
                continue
            regular_members.append(member)
        if not regular_members:
            findings.append(
                f"{rel}/{pattern}: placeholder 検査の対象族に regular file がない — "
                "対象族に依存する後続検査を停止"
            )
            blocked.add(directory)
            if directory == ARCHIVE_DIR:
                worklog_complete = False
            else:
                insights_complete = False
            continue
        targets.extend(regular_members)
    return targets, blocked, worklog_complete, insights_complete


def _placeholder_logical_lines(text: str) -> list[str]:
    """CRLF / LF / CR だけを改行とし、終端だけを除いた論理行を返す。"""

    return re.split(r"\r\n|\n|\r", text)


def _placeholder_line_digest(line: str) -> str:
    """strip・Unicode 正規化なしの論理行 UTF-8 bytes を digest 化する。"""

    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def _placeholder_scope(rel: str, h2_line: str | None) -> str:
    if rel == "docs/worklog.md" or re.fullmatch(
        r"docs/archive/worklog-[^/]+\.md", rel
    ):
        if h2_line is None:
            return "worklog-entry:<none>"
        return f"worklog-entry:{_placeholder_line_digest(h2_line)}"
    return f"insights-path:{rel}"


def _check_literal_placeholder_guard(findings: list[str]) -> set[Path]:
    """F36 の exact 3 文字列を Markdown 解釈なしの raw text で検査する。"""

    ledgers = (
        ("KNOWN_PLACEHOLDER_DEBTS", KNOWN_PLACEHOLDER_DEBTS),
        ("KNOWN_PLACEHOLDER_MENTIONS", KNOWN_PLACEHOLDER_MENTIONS),
    )
    observed: dict[str, dict[tuple[str, str], int]] = {
        name: {} for name, _ in ledgers
    }
    targets, blocked, worklog_complete, insights_complete = _literal_placeholder_targets(
        findings
    )
    h2_locations: dict[str, list[tuple[str, int]]] = {}

    for path in targets:
        rel = str(path.relative_to(REPO))
        text = _safe_read_text(
            path,
            findings,
            f"{rel}: placeholder 検査の読取失敗 — "
            "当該対象に依存する後続検査を停止",
            newline="",
        )
        if text is None:
            blocked.add(path)
            if rel == "docs/worklog.md" or rel.startswith("docs/archive/worklog-"):
                worklog_complete = False
            else:
                insights_complete = False
            continue

        preceding_h2: str | None = None
        is_worklog = (
            rel == "docs/worklog.md"
            or re.fullmatch(r"docs/archive/worklog-[^/]+\.md", rel) is not None
        )
        for lineno, line in enumerate(_placeholder_logical_lines(text), 1):
            h2_match = WORKLOG_H2_RE.match(line) if is_worklog else None
            if h2_match is not None:
                h2_locations.setdefault(line, []).append((rel, lineno))
            counts = {
                token: line.count(token)
                for token in LITERAL_PLACEHOLDERS
                if token in line
            }
            if counts:
                digest = _placeholder_line_digest(line)
                scope = _placeholder_scope(rel, preceding_h2)
                registered = False
                for ledger_name, ledger in ledgers:
                    if digest not in ledger.get(scope, {}):
                        continue
                    key = (scope, digest)
                    ledger_observed = observed[ledger_name]
                    ledger_observed[key] = ledger_observed.get(key, 0) + 1
                    registered = True
                if not registered:
                    detail = ", ".join(
                        f"{token!r}={count}" for token, count in counts.items()
                    )
                    findings.append(
                        f"{rel}:{lineno}: 未許可のリテラル placeholder ({detail})"
                    )
            if h2_match is not None:
                preceding_h2 = line

    if not worklog_complete:
        findings.append(
            "placeholder guard: worklog 族の入力が不明 — "
            "worklog scope の台帳照合と worklog H2 一意性検査を停止"
        )
    if not insights_complete:
        findings.append(
            "placeholder guard: insights 族の入力が不明 — "
            "insights-path scope の台帳照合を停止"
        )

    if worklog_complete:
        for h2_line, locations in h2_locations.items():
            if len(locations) < 2:
                continue
            rendered = ", ".join(
                f"{rel}:{lineno}" for rel, lineno in locations
            )
            findings.append(
                "worklog 族の H2 raw bytes が重複 — "
                f"{h2_line!r}: {rendered}"
            )

    expected_totals = (
        ("KNOWN_PLACEHOLDER_DEBTS", KNOWN_PLACEHOLDER_DEBTS,
         EXPECTED_KNOWN_PLACEHOLDER_DEBTS),
        ("KNOWN_PLACEHOLDER_MENTIONS", KNOWN_PLACEHOLDER_MENTIONS,
         EXPECTED_KNOWN_PLACEHOLDER_MENTIONS),
    )
    for ledger_name, ledger, pinned_total in expected_totals:
        registered_total = sum(
            count for entries in ledger.values() for count in entries.values()
        )
        if registered_total != pinned_total:
            findings.append(
                f"{ledger_name}: 台帳 occurrence 総数が固定値と不一致 — "
                f"expected={pinned_total}, actual={registered_total}"
            )
        for scope, entries in ledger.items():
            if scope.startswith("worklog-entry:") and not worklog_complete:
                continue
            if scope.startswith("insights-path:") and not insights_complete:
                continue
            for digest, expected in entries.items():
                actual = observed[ledger_name].get((scope, digest), 0)
                if actual != expected:
                    findings.append(
                        f"{scope}: {ledger_name} の登録 digest {digest} が観測数不一致 — "
                        f"expected={expected}, actual={actual}"
                    )
    return blocked


_UNREAD = object()


def _check_backlog_guard(
    findings: list[str],
    *,
    previously_unreadable: frozenset[Path] | set[Path] = frozenset(),
    phase3_text: str | None | object = _UNREAD,
) -> _BacklogCheckResult:
    """worklog の次アクション保存則と見送り台帳の ID 構造を検査する。"""

    worklog_text: str | None = None
    if WORKLOG in previously_unreadable:
        findings.append(
            "docs/worklog.md: placeholder 検査で読取不能と判定済み — "
            "次の一手の保存則を停止"
        )
        worklog_text = None
    elif not WORKLOG.exists():
        findings.append("docs/worklog.md: ファイルが不在 — 次の一手の保存則を検査できない")
    else:
        worklog_text = _safe_read_text(
            WORKLOG,
            findings,
            "docs/worklog.md: 次の一手の保存則を検査するための読取失敗",
        )
    if phase3_text is _UNREAD:
        if not PHASE3.exists():
            findings.append("docs/phase3.md: ファイルが不在 — 見送り台帳 sink を検査できない")
            phase3_text = None
        else:
            phase3_text = _safe_read_text(
                PHASE3,
                findings,
                "docs/phase3.md: 見送り台帳 sink を検査するための読取失敗 — "
                "見送り台帳に依存する遷移検査を停止",
            )

    ledger_ids: set[str] | None = None
    if phase3_text is not None:
        ledger = _extract_deferred_ledger(phase3_text, findings)
        if ledger is None:
            findings.append(
                "docs/phase3.md: 見送り台帳 sink の構造抽出失敗 — "
                "見送り台帳に依存する worklog 遷移検査を停止"
            )
        else:
            ledger_ids = set()
            ledger_body, ledger_offset = ledger
            seen: set[str] = set()
            for item_text, item_offset in _top_level_items(ledger_body):
                lineno = _line_number(phase3_text, ledger_offset + item_offset)
                if item_text.startswith("~~"):
                    terminal_id = TASK_ID_LIKE_RE.search(item_text)
                    if terminal_id is not None:
                        findings.append(
                            f"docs/phase3.md:{lineno}: 見送り台帳の取り消し線項目に "
                            f"ID {terminal_id.group(0)!r} がある"
                        )
                    continue

                valid = TASK_ID_AT_HEAD_RE.match(item_text)
                if valid:
                    task_id = valid.group("id")
                    if task_id in seen:
                        findings.append(
                            f"docs/phase3.md:{lineno}: "
                            f"見送り台帳の ID {task_id} が重複"
                        )
                    seen.add(task_id)
                    ledger_ids.add(task_id)
                else:
                    invalid = TASK_ID_LIKE_AT_HEAD_RE.match(item_text)
                    if invalid is None:
                        findings.append(
                            f"docs/phase3.md:{lineno}: 見送り台帳の生存項目先頭に"
                            "有効な [T-NNN] ID がない"
                        )
                        continue
                    token = invalid.group(0)
                    findings.append(
                        f"docs/phase3.md:{lineno}: "
                        f"見送り台帳の項目先頭 ID {token!r} が不正形式"
                    )

    if worklog_text is None:
        return _BacklogCheckResult({}, False)
    entries = _extract_current_entries(worklog_text, findings)
    if entries is None:
        return _BacklogCheckResult({}, False)

    entry_locations: dict[int, list[str]] = {}
    next_action_ids_by_entry: dict[int, set[str] | None] = {}
    carry_sources: list[_CarrySource] = []
    for entry in entries:
        match = WORKLOG_ENTRY_TITLE_RE.fullmatch(entry[0])
        assert match is not None
        number = int(match.group("order"))
        lineno = _line_number(worklog_text, entry[2])
        entry_locations.setdefault(number, []).append(f"docs/worklog.md:{lineno}")

    next_actions: list[tuple[str, int] | None] = [
        _extract_next_action("docs/worklog.md", worklog_text, entry, findings)
        for entry in entries
    ]
    sources = [set(_top_level_ids(section[0])) if section is not None else set()
               for section in next_actions]
    for entry, section, source_ids in zip(entries, next_actions, sources):
        match = WORKLOG_ENTRY_TITLE_RE.fullmatch(entry[0])
        assert match is not None
        number = int(match.group("order"))
        next_action_ids_by_entry[number] = (
            source_ids if section is not None else None
        )
    if not any(sources):
        findings.append(
            "docs/worklog.md: 現行 worklog に有効 ID を持つエントリが 1 件もない — "
            "保存則検査が蒸発している"
        )

    for i, (entry, section) in enumerate(zip(entries, next_actions)):
        if section is None:
            continue
        if _top_level_ids(entry[1]) or i == len(entries) - 1:
            _validate_next_action_items(
                "docs/worklog.md",
                worklog_text,
                entry,
                section,
                findings,
                latest=i == len(entries) - 1,
            )
            match = WORKLOG_ENTRY_TITLE_RE.fullmatch(entry[0])
            assert match is not None
            carry_sources.append(
                _CarrySource(
                    "docs/worklog.md",
                    worklog_text,
                    int(match.group("order")),
                    _entry_h2_raw_line(worklog_text, entry),
                    section[0],
                    section[1],
                )
            )

    def check_transition(
        source_entry: tuple[str, str, int],
        source_ids: set[str],
        sink_entry: tuple[str, str, int],
        source_rel: str,
    ) -> None:
        if not source_ids or ledger_ids is None:
            return
        sink_ids = set(_top_level_ids(sink_entry[1])) | ledger_ids
        for task_id in sorted(source_ids):
            if task_id not in sink_ids:
                findings.append(
                    f"{source_rel}: エントリ {source_entry[0]!r} の次の一手 ID {task_id} が "
                    f"後続エントリ {sink_entry[0]!r} のトップレベル項目にも "
                    "docs/phase3.md の見送り台帳にもない"
                )

    for i in range(len(entries) - 1):
        if next_actions[i] is not None:
            check_transition(entries[i], sources[i], entries[i + 1], "docs/worklog.md")

    archive_worklogs: list[_ArchiveWorklog] = []
    numbered_archive_entries: dict[str, frozenset[int] | None] = {}
    archive_blocked = any(
        path == ARCHIVE_DIR or ARCHIVE_DIR in path.parents
        for path in previously_unreadable
    )
    archive_input_complete = not archive_blocked
    numbered_archive_input_complete = not archive_blocked
    if archive_blocked:
        findings.append(
            "docs/archive: placeholder 検査で archive worklog 族の入力が読取不能 — "
            "archive 族全体に依存する順序・境界遷移検査を停止"
        )
    archive_paths = (
        []
        if ARCHIVE_DIR.is_symlink() or not ARCHIVE_DIR.is_dir()
        else sorted(ARCHIVE_DIR.glob("worklog-*.md"), key=lambda path: path.name)
    )
    for archive_path in archive_paths:
        filename_claim = _archive_filename_entry_range(archive_path)
        if filename_claim.classification == "malformed":
            findings.append(
                f"docs/archive/{archive_path.name}: MMDD で始まる worklog archive 名が"
                "位置文法に合わない — malformed filename"
            )
        elif filename_claim.classification == "numbered":
            numbered_archive_entries[archive_path.name] = None
        if archive_path in previously_unreadable:
            archive_input_complete = False
            if filename_claim.classification == "numbered":
                numbered_archive_input_complete = False
            continue
        if archive_path.is_symlink() or not archive_path.is_file():
            archive_input_complete = False
            if filename_claim.classification == "numbered":
                numbered_archive_input_complete = False
            continue
        archive_rel = str(archive_path.relative_to(REPO))
        archive_text = _safe_read_text(
            archive_path,
            findings,
            f"{archive_rel}: archive worklog 遷移検査の読取失敗 — "
            "archive 族全体に依存する順序・境界遷移検査を停止",
        )
        if archive_text is None:
            archive_input_complete = False
            if filename_claim.classification == "numbered":
                numbered_archive_input_complete = False
            continue
        archive_entries = _extract_archive_entries(archive_path, archive_text, findings)
        if archive_entries is None:
            archive_input_complete = False
            if filename_claim.classification == "numbered":
                numbered_archive_input_complete = False
            findings.append(
                f"{archive_rel}: archive entry の構造抽出失敗 — "
                "archive 族全体に依存する順序・境界遷移検査を停止"
            )
            continue

        actual_entry_numbers = frozenset(
            number for title, _, _ in archive_entries
            if (number := _entry_number_from_title(title)) is not None
        )
        if filename_claim.classification == "numbered":
            numbered_archive_entries[archive_path.name] = actual_entry_numbers
            assert filename_claim.entry_range is not None
            _validate_claimed_entry_range(
                f"{archive_rel}: filename",
                filename_claim.entry_range,
                actual_entry_numbers,
                findings,
            )
            for title, _, title_offset in archive_entries:
                number = _entry_number_from_title(title)
                if number is None:
                    findings.append(
                        f"{archive_rel}:{_line_number(archive_text, title_offset)}: "
                        f"番号付き archive 内の H2 {title!r} に全域 entry 番号がない"
                    )
                    continue
                entry_locations.setdefault(number, []).append(
                    f"{archive_rel}:{_line_number(archive_text, title_offset)}"
                )

        archive_next_actions: list[tuple[str, int] | None] = []
        archive_sources: list[set[str]] = []
        for i, entry in enumerate(archive_entries):
            raw_sections = list(NEXT_ACTION_RE.finditer(entry[1]))
            entry_has_id = bool(_top_level_ids(entry[1]))
            # ID 導入前の古い archive には inline の「次の一手」しかない entry がある。
            # source が存在しない非末尾 entry だけは空遷移として扱い、ID を持つ entry、
            # archive 境界を担う末尾 entry、複数節は構造を必ず検査する。
            must_extract = entry_has_id or i == len(archive_entries) - 1 or len(raw_sections) > 1
            if len(raw_sections) == 1 or must_extract:
                section = _extract_next_action(
                    archive_rel, archive_text, entry, findings
                )
            else:
                section = None
            archive_next_actions.append(section)
            source_ids = set(_top_level_ids(section[0])) if section is not None else set()
            archive_sources.append(source_ids)
            if filename_claim.classification == "numbered":
                number = _entry_number_from_title(entry[0])
                if number is not None:
                    next_action_ids_by_entry[number] = (
                        source_ids if section is not None else None
                    )
            if entry_has_id and section is not None:
                _validate_next_action_items(
                    archive_rel,
                    archive_text,
                    entry,
                    section,
                    findings,
                )
                if filename_claim.classification == "numbered":
                    number = _entry_number_from_title(entry[0])
                    assert number is not None
                    carry_sources.append(
                        _CarrySource(
                            archive_rel,
                            archive_text,
                            number,
                            _entry_h2_raw_line(archive_text, entry),
                            section[0],
                            section[1],
                        )
                    )

        archive = _ArchiveWorklog(
            archive_path,
            archive_text,
            archive_entries,
            archive_next_actions,
            archive_sources,
        )
        archive_worklogs.append(archive)
        for i in range(len(archive_entries) - 1):
            if archive_next_actions[i] is not None:
                check_transition(
                    archive_entries[i],
                    archive_sources[i],
                    archive_entries[i + 1],
                    archive_rel,
                )

    archive_worklogs.sort(
        key=lambda archive: (
            _archive_entry_point(archive.entries[0][0])[0],
            _archive_entry_point(archive.entries[0][0])[1] is None,
            _archive_entry_point(archive.entries[0][0])[1] or 0,
            archive.path.name,
        )
    )
    ambiguous_order = False
    if archive_input_complete:
        for i, left in enumerate(archive_worklogs):
            for right in archive_worklogs[i + 1:]:
                if _archive_is_before(left, right):
                    continue
                ambiguous_order = True
                findings.append(
                    "docs/archive: archive worklog の順序を一意に決定できない — "
                    f"{left.path.name} の末尾 {left.entries[-1][0]!r} と "
                    f"{right.path.name} の先頭 {right.entries[0][0]!r} が同日または範囲重複"
                )

    if archive_input_complete and archive_worklogs and not ambiguous_order:
        for left, right in zip(archive_worklogs, archive_worklogs[1:]):
            check_transition(
                left.entries[-1],
                left.sources[-1],
                right.entries[0],
                str(left.path.relative_to(REPO)),
            )

        latest_archive = archive_worklogs[-1]
        if not _entry_point_is_before(latest_archive.entries[-1][0], entries[0][0]):
            findings.append(
                "docs/archive: 最終 archive と現行 worklog 先頭の順序を一意に決定できない — "
                f"{latest_archive.path.name} の末尾 {latest_archive.entries[-1][0]!r} / "
                f"docs/worklog.md の先頭 {entries[0][0]!r}"
            )
        else:
            check_transition(
                latest_archive.entries[-1],
                latest_archive.sources[-1],
                entries[0],
                str(latest_archive.path.relative_to(REPO)),
            )

    _validate_entry_universe(
        entry_locations,
        next_action_ids_by_entry,
        carry_sources,
        findings,
        numbered_archive_input_complete=numbered_archive_input_complete,
    )
    return _BacklogCheckResult(
        numbered_archive_entries,
        not archive_blocked,
    )


@dataclass
class _DispatchTables:
    edges: set[tuple[str, str, str, str]]
    condition_triggers: dict[str, set[str]]
    condition_leaked_tokens: dict[str, set[str]]
    condition_row_counts: dict[str, int]
    paths: set[str]
    structure_errors: tuple[str, ...]

    @property
    def stage_unconditional(self) -> dict[str, set[tuple[str, str]]]:
        return _stage_dispatch_from_edges(self.edges, "U")

    @property
    def stage_conditional(self) -> dict[str, set[tuple[str, str]]]:
        return _stage_dispatch_from_edges(self.edges, "C")

    @property
    def stages(self) -> dict[str, set[tuple[str, str]]]:
        keys = set(self.stage_unconditional) | set(self.stage_conditional)
        return {
            key: (
                self.stage_unconditional.get(key, set())
                | self.stage_conditional.get(key, set())
            )
            for key in keys
        }

    @property
    def conditions(self) -> dict[str, set[tuple[str, str]]]:
        result: dict[str, set[tuple[str, str]]] = {}
        for owner, mode, path, section in self.edges:
            if owner.startswith("条件 ") and mode == "C":
                result.setdefault(owner.removeprefix("条件 "), set()).add(
                    (path, section)
                )
        return result


def _stage_dispatch_from_edges(
    edges: set[tuple[str, str, str, str]],
    mode: str,
) -> dict[str, set[tuple[str, str]]]:
    result: dict[str, set[tuple[str, str]]] = {}
    for owner, edge_mode, path, section in edges:
        if not owner.startswith("条件 ") and edge_mode == mode:
            result.setdefault(owner, set()).add((path, section))
    return result


_DISPATCH_PATH_RE = re.compile(r"`((?:docs|\.claude)/[^`]+\.md)`")
_DISPATCH_RAW_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"(?:docs|\.claude)/[^\s`|;:]+\.md"
    r"(?![A-Za-z0-9_.-])"
)
_DISPATCH_SECTION_ID = (
    r"(?:DW-(?:[A-Z][0-9]{2}(?:-[A-C])?|CTX|STOP)|PR-[AC][0-9]{2})"
)
_DISPATCH_TOKEN_RE = re.compile(
    r"`(?P<path>(?:docs|\.claude)/[^`]+\.md)`"
    rf"|`(?P<section>{_DISPATCH_SECTION_ID})`"
)
_BASE = r"DW-[A-Z][0-9]{2}"
_DISPATCH_PATH_TOKEN = r"`(?:docs|\.claude)/[^`\r\n]+\.md`"
_DISPATCH_SECTION_TOKEN = rf"`{_DISPATCH_SECTION_ID}`"
_DISPATCH_ANNOTATION = r"(?:（[^（）\r\n`]*）)?"
_DISPATCH_SECTION_ITEM = (
    rf"(?:`{_BASE}`〜`{_BASE}`|{_DISPATCH_SECTION_TOKEN})"
    rf"{_DISPATCH_ANNOTATION}"
)
_DISPATCH_SECTION_LIST = (
    rf"{_DISPATCH_SECTION_ITEM}(?:, {_DISPATCH_SECTION_ITEM})*"
)
_DISPATCH_REFERENCE_GROUP = (
    rf"{_DISPATCH_PATH_TOKEN}: {_DISPATCH_SECTION_LIST}"
)
_DISPATCH_SELF_GROUP = rf"`{re.escape(_SELF_PATH)}` の全節"
_DISPATCH_REFERENCE_CELL_RE = re.compile(
    rf"(?:{_DISPATCH_REFERENCE_GROUP}|{_DISPATCH_SELF_GROUP})"
    rf"(?:; (?:{_DISPATCH_REFERENCE_GROUP}|{_DISPATCH_SELF_GROUP}))*"
)
_SELF_ALL_SECTIONS_RE = re.compile(
    rf"(?:^|;[ \t]*)`{re.escape(_SELF_PATH)}` の全節(?=;|$)"
)


def _dispatch_reference_cell_errors(cell: str) -> tuple[str, ...]:
    """dev-wave の参照 cell で grammar 外の path・全節指定を拒否する。"""

    quoted_matches = list(_DISPATCH_PATH_RE.finditer(cell))
    quoted_paths = {match.group(1) for match in quoted_matches}
    quoted_spans = {
        (match.start(1), match.end(1)) for match in quoted_matches
    }
    raw_matches = list(_DISPATCH_RAW_PATH_RE.finditer(cell))
    raw_paths = {match.group(0) for match in raw_matches}
    unquoted_paths = sorted(
        {
            match.group(0)
            for match in raw_matches
            if (match.start(), match.end()) not in quoted_spans
        }
    )

    errors: list[str] = []
    if raw_paths != quoted_paths or unquoted_paths:
        errors.append(
            "raw .md path と backtick path が一致しない — "
            f"raw={sorted(raw_paths)}, quoted={sorted(quoted_paths)}, "
            f"unquoted={unquoted_paths}"
        )

    all_sections_count = cell.count("の全節")
    exact_self_count = len(_SELF_ALL_SECTIONS_RE.findall(cell))
    if all_sections_count != exact_self_count:
        errors.append(
            "`docs/skill-self-improvement.md` の exact fragment 以外に "
            f"の全節がある — all={all_sections_count}, exact={exact_self_count}"
        )
    if _DISPATCH_REFERENCE_CELL_RE.fullmatch(cell) is None:
        errors.append(
            "cell 全文が参照 grammar に fullmatch しない — "
            f"cell={cell!r}"
        )
    return tuple(errors)


def _markdown_sections(text: str, heading: str) -> list[str]:
    return [
        match.group("body")
        for match in re.finditer(
            rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
    ]


def _reference_id_sections(text: str, section_id: str) -> list[str]:
    """``## DW-XNN — title`` 形式の leaf 本文を ID で一意に抽出する。"""
    return [
        match.group("body")
        for match in re.finditer(
            rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n"
            r"(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
    ]


def _expand_dispatch_range(start: str, end: str) -> set[str]:
    left = re.fullmatch(r"DW-([A-Z])(\d{2})", start)
    right = re.fullmatch(r"DW-([A-Z])(\d{2})", end)
    if left is None or right is None or left.group(1) != right.group(1):
        return set()
    first, last = int(left.group(2)), int(right.group(2))
    if first > last:
        return set()
    return {f"DW-{left.group(1)}{i:02d}" for i in range(first, last + 1)}


def _dispatch_pairs_from_line(
    line: str,
) -> tuple[set[tuple[str, str]], set[str]]:
    pairs: set[tuple[str, str]] = set()
    paths = set(_DISPATCH_PATH_RE.findall(line))
    current_path: str | None = None
    previous: tuple[str, str, int] | None = None
    for token in _DISPATCH_TOKEN_RE.finditer(line):
        path = token.group("path")
        section = token.group("section")
        if path is not None:
            current_path = path
            previous = None
            continue
        if section is None:
            continue
        if current_path is None:
            pairs.add(("<unbound>", section))
            previous = None
            continue
        pairs.add((current_path, section))
        if previous is not None:
            previous_section, previous_path, previous_end = previous
            between = line[previous_end:token.start()]
            if (
                previous_path == current_path
                and re.fullmatch(r"[ \t]*〜[ \t]*", between)
            ):
                pairs.update(
                    (current_path, expanded)
                    for expanded in _expand_dispatch_range(
                        previous_section, section
                    )
                )
        previous = (section, current_path, token.end())
    if _SELF_PATH in paths and len(_SELF_ALL_SECTIONS_RE.findall(line)) == 1:
        pairs.update(_SELF_SECTIONS)
    return pairs, paths


@dataclass
class _ConditionDispatch:
    rows: dict[str, set[tuple[str, str]]]
    conditions: dict[str, set[str]]
    row_counts: dict[str, int]
    column_counts: dict[str, set[int]]
    leaked_tokens: dict[str, set[str]]
    paths: dict[str, set[str]]
    structure_errors: tuple[str, ...]


def _markdown_table_cells(line: str) -> tuple[list[str], int, int]:
    """外周 delimiter を高々1個だけ外し、Markdown table の cell を返す。"""

    stripped = line.strip()
    leading = len(stripped) - len(stripped.lstrip("|"))
    trailing = len(stripped) - len(stripped.rstrip("|"))
    body = stripped[1:] if leading else stripped
    if trailing:
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")], leading, trailing


def _is_three_cell_separator(line: str) -> bool:
    cells, leading, trailing = _markdown_table_cells(line)
    return (
        leading <= 1
        and trailing <= 1
        and len(cells) == 3
        and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)
    )


def _condition_dispatch_table(
    text: str,
    heading: str,
) -> _ConditionDispatch | None:
    visible_text = _visible_markdown_text(text)
    sections = _markdown_sections(visible_text, heading)
    if len(sections) != 1:
        return None

    rows: dict[str, set[tuple[str, str]]] = {}
    conditions: dict[str, set[str]] = {}
    row_counts: dict[str, int] = {}
    column_counts: dict[str, set[int]] = {}
    leaked_tokens: dict[str, set[str]] = {}
    paths: dict[str, set[str]] = {}
    structure_errors: list[str] = []
    section_lines = sections[0].splitlines()
    header_indices = [
        index
        for index, line in enumerate(section_lines)
        if line == PROVENANCE_DISPATCH_HEADER
    ]
    if len(header_indices) != 1:
        structure_errors.append(
            f"header {PROVENANCE_DISPATCH_HEADER!r} が {len(header_indices)} 件"
        )
    separator_indices = [
        index
        for index, line in enumerate(section_lines)
        if _is_three_cell_separator(line)
    ]
    if len(separator_indices) != 1:
        structure_errors.append(
            f"3列 separator が {len(separator_indices)} 件"
        )
    if (
        len(header_indices) == 1
        and len(separator_indices) == 1
        and separator_indices[0] != header_indices[0] + 1
    ):
        structure_errors.append("separator が header 直後にない")

    for line in section_lines:
        if "|" not in line:
            continue
        if line == PROVENANCE_DISPATCH_HEADER or _is_three_cell_separator(line):
            continue
        cells, leading, trailing = _markdown_table_cells(line)
        if leading > 1 or trailing > 1 or len(cells) != 3:
            structure_errors.append(
                "data row が3列・外周 delimiter 高々1個でない — "
                f"leading={leading}, trailing={trailing}, cells={len(cells)}"
            )
            continue

        key = cells[0]
        condition = cells[1]
        reference_cell = cells[2]
        pairs, row_paths = _dispatch_pairs_from_line(reference_cell)
        leaks = {match.group(0) for match in _DISPATCH_TOKEN_RE.finditer(condition)}

        rows.setdefault(key, set()).update(pairs)
        conditions.setdefault(key, set()).add(condition)
        row_counts[key] = row_counts.get(key, 0) + 1
        column_counts.setdefault(key, set()).add(len(cells))
        leaked_tokens.setdefault(key, set()).update(leaks)
        paths.setdefault(key, set()).update(row_paths)

    return _ConditionDispatch(
        rows,
        conditions,
        row_counts,
        column_counts,
        leaked_tokens,
        paths,
        tuple(structure_errors),
    )


_DISPATCH_RUNBOOK = "docs/pegasus-runbook.md"
_DISPATCH_SOURCE = "tools/pegasus/dispatch_compute.py"
_DISPATCH_SECTION_RE = re.compile(
    r"^[ \t]{0,3}###(?!#)[ \t]+7\.0(?:[ \t\u3000]+[^\n]+)?[ \t]*$",
    re.MULTILINE,
)
_DISPATCH_PARENT_HEADING_RE = re.compile(
    r"^[ \t]{0,3}(?P<marker>#{1,2})(?!#)[ \t]+(?P<title>[^\n]+?)[ \t]*$",
    re.MULTILINE,
)
_DISPATCH_PARENT_TITLE_RE = re.compile(r"^7(?:\.)?(?:[ \t\u3000]+|$)")
_TASKS_MUTATING_METHODS = frozenset({
    "__delitem__",
    "__init__",
    "__ior__",
    "__setitem__",
    "clear",
    "pop",
    "popitem",
    "setdefault",
    "update",
})


def _dispatch_inventory_finding(findings: list[str], detail: str) -> None:
    findings.append(f"tools/check_docs.py: dispatch inventory drift — {detail}")


def _dispatch_inventory_from_runbook(
    text: str, findings: list[str]
) -> dict[str, str] | None:
    """runbook §7.0 の exact task 表だけを ``{task: child_script}`` にする。"""

    visible_text = _visible_dispatch_inventory_text(text)
    sections = list(_DISPATCH_SECTION_RE.finditer(visible_text))
    if len(sections) != 1:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} の `### 7.0` 節が {len(sections)} 件",
        )
        return None

    section = sections[0]
    parent_headings = list(_DISPATCH_PARENT_HEADING_RE.finditer(visible_text))
    parents = [
        heading
        for heading in parent_headings
        if (
            heading.group("marker") == "##"
            and _DISPATCH_PARENT_TITLE_RE.match(heading.group("title"))
        )
    ]
    if len(parents) != 1:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} の親 `## 7` 節が {len(parents)} 件",
        )
        return None
    preceding_parents = [
        heading for heading in parent_headings if heading.start() < section.start()
    ]
    if not preceding_parents or preceding_parents[-1] is not parents[0]:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} の `### 7.0` が親 `## 7` の直下でない",
        )
        return None

    tail = visible_text[section.end():]
    next_heading = re.search(
        r"^[ \t]{0,3}#{1,3}(?!#)[ \t]+", tail, re.MULTILINE
    )
    body = tail[:next_heading.start()] if next_heading is not None else tail
    lines = body.splitlines()
    header_indices: list[int] = []
    for index, line in enumerate(lines):
        cells, leading, trailing = _markdown_table_cells(line)
        if (
            leading <= 1
            and trailing <= 1
            and cells == ["task", "子 script"]
        ):
            header_indices.append(index)
    if len(header_indices) != 1:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} §7.0 の exact task 表 header が "
            f"{len(header_indices)} 件",
        )
        return None

    header_index = header_indices[0]
    separator_index = header_index + 1
    if separator_index >= len(lines):
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} §7.0 の exact task 表 separator が不在",
        )
        return None
    separator_cells, leading, trailing = _markdown_table_cells(
        lines[separator_index]
    )
    if not (
        leading <= 1
        and trailing <= 1
        and len(separator_cells) == 2
        and all(
            re.fullmatch(r":?-{3,}:?", cell)
            for cell in separator_cells
        )
    ):
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} §7.0 の exact task 表 separator が2列でない",
        )
        return None

    inventory: dict[str, str] = {}
    duplicates: set[str] = set()
    structure_errors: list[str] = []
    for line in lines[separator_index + 1:]:
        if not line.strip() or "|" not in line:
            break
        cells, leading, trailing = _markdown_table_cells(line)
        if leading > 1 or trailing > 1 or len(cells) != 2:
            structure_errors.append(line.strip())
            continue
        task_match = re.fullmatch(r"`([^`\s]+)`", cells[0])
        script_match = re.fullmatch(r"`([^`\s]+)`", cells[1])
        if task_match is None or script_match is None:
            structure_errors.append(line.strip())
            continue
        task = task_match.group(1)
        if task in inventory:
            duplicates.add(task)
        else:
            inventory[task] = script_match.group(1)

    if structure_errors:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} §7.0 の exact task 表に不正な行がある — "
            f"{structure_errors}",
        )
        return None
    if duplicates:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} §7.0 の exact task 表で task 行が重複 — "
            f"{sorted(duplicates)}",
        )
        return None
    if not inventory:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} §7.0 の exact task 表が 0 行",
        )
        return None
    return inventory


def _dispatch_inventory_from_source(
    text: str, findings: list[str]
) -> dict[str, str] | None:
    """dispatcher source を実行せず TASKS[*].child_script を抽出する。"""

    try:
        tree = ast.parse(text, filename=_DISPATCH_SOURCE)
    except SyntaxError as exc:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_SOURCE} の TASKS を解析できない — SyntaxError: {exc}",
        )
        return None

    assignments: list[ast.Assign | ast.AnnAssign] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TASKS"
            for target in node.targets
        ):
            assignments.append(node)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "TASKS"
            and node.value is not None
        ):
            assignments.append(node)
    definition = assignments[0] if assignments else None
    task_value = definition.value if definition is not None else None
    direct_definition = (
        definition is not None
        and isinstance(task_value, ast.Dict)
        and (
            isinstance(definition, ast.AnnAssign)
            or (
                isinstance(definition, ast.Assign)
                and len(definition.targets) == 1
                and isinstance(definition.targets[0], ast.Name)
                and definition.targets[0].id == "TASKS"
            )
        )
    )
    if not direct_definition:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_SOURCE} の最初の TASKS 定義が不在または非 literal",
        )
        return None

    assert definition is not None
    definition_end = getattr(definition, "end_lineno", definition.lineno)
    definition_end_col = getattr(definition, "end_col_offset", 0)

    def preserves_tasks_alias(node: ast.AST | None) -> bool:
        """式の値が TASKS 本体を保持し得る場合だけ True にする。"""

        if node is None:
            return False
        if isinstance(node, ast.Name):
            return node.id == "TASKS" and isinstance(node.ctx, ast.Load)
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return any(preserves_tasks_alias(element) for element in node.elts)
        if isinstance(node, ast.Dict):
            return any(
                preserves_tasks_alias(element)
                for element in (*node.keys, *node.values)
            )
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return (
                preserves_tasks_alias(node.elt)
                or any(
                    preserves_tasks_alias(generator.iter)
                    or any(
                        preserves_tasks_alias(condition)
                        for condition in generator.ifs
                    )
                    for generator in node.generators
                )
            )
        if isinstance(node, ast.DictComp):
            return (
                preserves_tasks_alias(node.key)
                or preserves_tasks_alias(node.value)
                or any(
                    preserves_tasks_alias(generator.iter)
                    or any(
                        preserves_tasks_alias(condition)
                        for condition in generator.ifs
                    )
                    for generator in node.generators
                )
            )
        if isinstance(node, ast.Starred):
            return preserves_tasks_alias(node.value)
        if isinstance(node, ast.NamedExpr):
            return preserves_tasks_alias(node.value)
        if isinstance(node, ast.BoolOp):
            return any(preserves_tasks_alias(value) for value in node.values)
        if isinstance(node, ast.IfExp):
            return (
                preserves_tasks_alias(node.body)
                or preserves_tasks_alias(node.orelse)
            )
        if isinstance(node, ast.Subscript):
            # TASKS[key] は task spec の読み取りであって mapping alias ではない。
            # container[TASKS を含む位置] は本体を再び取り出し得るので拒否する。
            return (
                not isinstance(node.value, ast.Name)
                and preserves_tasks_alias(node.value)
            )
        if isinstance(node, ast.Lambda):
            return preserves_tasks_alias(node.body)
        if isinstance(node, ast.Call):
            # tuple(TASKS) は既存の task 名 snapshot。TASKS 本体を保持しない。
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "tuple"
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "TASKS"
                and not node.keywords
            ):
                return False
            return any(
                preserves_tasks_alias(argument)
                for argument in (
                    *node.args,
                    *(keyword.value for keyword in node.keywords),
                )
            ) or (
                isinstance(node.func, ast.Attribute)
                and preserves_tasks_alias(node.func.value)
            )
        return False

    writes: list[str] = []
    for node in ast.walk(tree):
        node_start = (
            getattr(node, "lineno", 0),
            getattr(node, "col_offset", 0),
        )
        if node_start <= (definition_end, definition_end_col):
            continue
        if (
            isinstance(node, ast.Name)
            and node.id == "TASKS"
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ):
            writes.append(f"line {node.lineno}: TASKS への束縛/削除")
        elif (
            isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
            and preserves_tasks_alias(node.value)
        ):
            writes.append(f"line {node.lineno}: TASKS の alias 束縛")
        elif (
            isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
            )
            and any(
                preserves_tasks_alias(default)
                for default in (
                    *node.args.defaults,
                    *(default for default in node.args.kw_defaults
                      if default is not None),
                )
            )
        ):
            writes.append(f"line {node.lineno}: TASKS の function default capture")
        elif (
            isinstance(node, ast.Call)
            and not (
                isinstance(node.func, ast.Name)
                and node.func.id == "tuple"
            )
            and any(
                preserves_tasks_alias(argument)
                for argument in (
                    *node.args,
                    *(keyword.value for keyword in node.keywords),
                )
            )
        ):
            writes.append(
                f"line {node.lineno}: TASKS の実引数渡しを静的確定できない"
            )
        elif (
            isinstance(node, (ast.Subscript, ast.Attribute))
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and any(
                isinstance(child, ast.Name) and child.id == "TASKS"
                for child in ast.walk(node)
            )
        ):
            writes.append(f"line {node.lineno}: TASKS の要素/属性への書込み")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "TASKS"
            and node.func.attr in _TASKS_MUTATING_METHODS
        ):
            writes.append(
                f"line {node.lineno}: TASKS.{node.func.attr}() による変更"
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or (
                    alias.name.split(".", 1)[0]
                    if isinstance(node, ast.Import) else alias.name
                )
                if bound == "TASKS":
                    writes.append(f"line {node.lineno}: import による TASKS 再束縛")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == "TASKS":
                writes.append(f"line {node.lineno}: 定義による TASKS 再束縛")
        elif isinstance(node, ast.arg) and node.arg == "TASKS":
            writes.append(f"line {node.lineno}: 引数による TASKS 束縛")
        elif isinstance(node, ast.ExceptHandler) and node.name == "TASKS":
            writes.append(f"line {node.lineno}: except による TASKS 束縛")
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)):
            if node.name == "TASKS":
                writes.append(f"line {node.lineno}: match による TASKS 束縛")
        elif (
            isinstance(node, (ast.Subscript, ast.Attribute))
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id in {"globals", "locals", "vars"}
                for child in ast.walk(node)
            )
        ):
            writes.append(
                f"line {node.lineno}: 動的 namespace 経由の書込みを静的確定できない"
            )
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id in {"globals", "locals", "vars"}
            and node.func.attr in _TASKS_MUTATING_METHODS
        ):
            writes.append(
                f"line {node.lineno}: 動的 namespace の変更を静的確定できない"
            )
    if writes:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_SOURCE} の TASKS 写像を静的に確定できない — "
            f"{sorted(set(writes))}",
        )
        return None

    inventory: dict[str, str] = {}
    duplicates: set[str] = set()
    errors: list[str] = []
    task_dict = task_value
    assert isinstance(task_dict, ast.Dict)
    for key_node, value_node in zip(task_dict.keys, task_dict.values):
        if not (
            isinstance(key_node, ast.Constant)
            and isinstance(key_node.value, str)
            and isinstance(value_node, ast.Call)
            and isinstance(value_node.func, ast.Name)
            and value_node.func.id == "_TaskSpec"
        ):
            errors.append("TASKS の key/value が string/_TaskSpec call でない")
            continue
        child_keywords = [
            keyword.value
            for keyword in value_node.keywords
            if keyword.arg == "child_script"
        ]
        if len(child_keywords) != 1 or not isinstance(
            child_keywords[0], (ast.Tuple, ast.List)
        ):
            errors.append(f"{key_node.value!r} の child_script tuple を抽出できない")
            continue
        parts = []
        for element in child_keywords[0].elts:
            if not (
                isinstance(element, ast.Constant)
                and isinstance(element.value, str)
            ):
                parts = []
                break
            parts.append(element.value)
        if not parts:
            errors.append(f"{key_node.value!r} の child_script が空または非 literal")
            continue
        task = key_node.value
        if task in inventory:
            duplicates.add(task)
        else:
            inventory[task] = "/".join(parts)

    if errors:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_SOURCE} の TASKS 構造が不一致 — {errors}",
        )
        return None
    if duplicates:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_SOURCE} の TASKS key が重複 — {sorted(duplicates)}",
        )
        return None
    if not inventory:
        _dispatch_inventory_finding(
            findings,
            f"{_DISPATCH_SOURCE} の TASKS が 0 件",
        )
        return None
    return inventory


def _check_dispatch_inventory(findings: list[str]) -> None:
    runbook_text = _safe_read_text(
        REPO / _DISPATCH_RUNBOOK,
        findings,
        "tools/check_docs.py: dispatch inventory drift — "
        f"{_DISPATCH_RUNBOOK} の読取失敗",
    )
    source_text = _safe_read_text(
        REPO / _DISPATCH_SOURCE,
        findings,
        "tools/check_docs.py: dispatch inventory drift — "
        f"{_DISPATCH_SOURCE} の読取失敗",
    )
    documented = (
        _dispatch_inventory_from_runbook(runbook_text, findings)
        if runbook_text is not None else None
    )
    implemented = (
        _dispatch_inventory_from_source(source_text, findings)
        if source_text is not None else None
    )
    if documented is None or implemented is None:
        return

    documented_tasks = set(documented)
    implemented_tasks = set(implemented)
    changed_scripts = {
        task: {"runbook": documented[task], "TASKS": implemented[task]}
        for task in sorted(documented_tasks & implemented_tasks)
        if documented[task] != implemented[task]
    }
    if documented != implemented:
        _dispatch_inventory_finding(
            findings,
            "{task: child_script} が不一致 — "
            f"TASKS_only={sorted(implemented_tasks - documented_tasks)}, "
            f"runbook_only={sorted(documented_tasks - implemented_tasks)}, "
            f"child_script={changed_scripts}",
        )


_ADMISSION_PREFIX = "tools/check_docs.py: Pegasus admission drift — "
_ADMISSION_LOADER = "tools/pegasus_admission_registry.py"
_ADMISSION_README = "tools/pegasus/README.md"
_ADMISSION_PROJECTION_HEADER = ("path", "class", "evidence")
_ADMISSION_UNKNOWN_HEADER = ("経路", "なぜ `unknown` か")
_ADMISSION_MEASURED_HEADER = ("経路", "観測ピーク", "certified peak", "分類")
_ADMISSION_DECLARATION_HEADER = (
    "path",
    "手順上の実行 site",
    "registry class",
)
_ADMISSION_SITES = frozenset({"login-direct", "qsub-job-body", "compute-only"})
_ADMISSION_CLASSES = frozenset({"local-ok", "dispatch-required", "unknown"})
_ADMISSION_LITERAL_RE = re.compile(r"`([^`\r\n]+)`\Z")
_ADMISSION_SITE_TAG_RE = re.compile(r"^[ \t]*# admission-site:[ \t]*(?P<site>\S.*?)[ \t]*$")
_ADMISSION_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])tools(?:[/／]+)pegasus"
    r"(?:[/／]+[A-Za-z0-9_.-]+)+(?:[/／]+)?",
    re.IGNORECASE,
)

# This is an independent golden for the one grandfather warning whose presence is
# normative even though the surrounding unknown inventory is intentionally open.
_ADMISSION_REQUIRED_GRANDFATHER_WARNINGS = {
    "tools/pegasus/submit_silo_ladder_rung1.sh": (
        "local-ok",
        "legacy-admitted (未実測)",
    ),
}


@dataclass(frozen=True)
class _AdmissionTable:
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class _AdmissionFence:
    info: str
    first_lineno: int
    lines: tuple[str, ...]


def _admission_finding(findings: list[str], detail: str) -> None:
    findings.append(f"{_ADMISSION_PREFIX}{detail}")


def _admission_exception(exc: BaseException) -> str:
    """例外 payload を再評価せず、安全な型名だけを診断へ写す。"""

    try:
        name = type(exc).__name__
        return name if isinstance(name, str) and name else "BaseException"
    except BaseException:
        return "BaseException"


def _load_admission_registry(
    findings: list[str],
) -> dict[str, dict[str, str]] | None:
    """canonical loader の exact source bytes を実行し、異常を単一 finding に畳む。"""

    source = REPO / _ADMISSION_LOADER
    module_name = "_izanagi_check_docs_pegasus_admission_registry"
    previous_modules = sys.modules
    previous_dont_write_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        with source.open("rb") as stream:
            source_bytes = stream.read()
        namespace = {
            "__file__": str(source),
            "__name__": module_name,
            "__package__": "",
        }
        exec(
            compile(source_bytes, str(source), "exec", dont_inherit=True),
            namespace,
        )
        loader = namespace.get("load_admission_registry")
        if not callable(loader):
            raise TypeError("load_admission_registry が callable でない")
        loaded = loader(REPO)
        if not isinstance(loaded, Mapping) or not loaded:
            raise TypeError("loader 返値が非空 Mapping でない")

        registry: dict[str, dict[str, str]] = {}
        for path, entry in loaded.items():
            if not isinstance(path, str) or not isinstance(entry, Mapping):
                raise TypeError("loader 返値の entry が path→Mapping でない")
            entry_class = entry.get("class")
            evidence = entry.get("evidence")
            if (
                entry_class not in _ADMISSION_CLASSES
                or not isinstance(evidence, str)
                or not evidence
            ):
                raise TypeError("loader 返値の class/evidence が不正")
            registry[path] = {"class": entry_class, "evidence": evidence}
        return registry
    except BaseException as exc:
        try:
            detail = _admission_exception(exc)
        except BaseException:
            detail = "BaseException"
        _admission_finding(findings, f"canonical registry を確定できない — {detail}")
        return None
    finally:
        try:
            sys.dont_write_bytecode = previous_dont_write_bytecode
        except BaseException:
            pass
        try:
            sys.modules = previous_modules
        except BaseException:
            pass


def _admission_single_literal(cell: str) -> str | None:
    match = _ADMISSION_LITERAL_RE.fullmatch(cell)
    return match.group(1) if match is not None else None


def _admission_path_mentions(
    text: str,
    registry: Mapping[str, object],
) -> tuple[set[str], list[str]]:
    """Pegasus-like path を正規化し、既知 path と非 canonical 綴りを返す。"""

    by_folded = {path.casefold(): path for path in registry}
    mentioned: set[str] = set()
    noncanonical: list[str] = []
    for match in _ADMISSION_PATH_RE.finditer(text):
        raw = match.group(0)
        normalized = raw.replace("／", "/")
        normalized = re.sub(r"/+", "/", normalized).rstrip("/")
        parts = normalized.split("/")
        canonical_spelling = "/".join(("tools", "pegasus", *parts[2:]))
        if raw != canonical_spelling:
            noncanonical.append(raw)
        canonical = by_folded.get(normalized.casefold())
        if canonical is None:
            continue
        mentioned.add(canonical)
        if raw != canonical and raw not in noncanonical:
            noncanonical.append(raw)
    return mentioned, noncanonical


def _admission_fences(text: str) -> tuple[_AdmissionFence, ...]:
    opener = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
    active: tuple[str, int, str, int, list[str]] | None = None
    fences: list[_AdmissionFence] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if active is not None:
            marker_char, marker_len, info, first_lineno, lines = active
            stripped = line.lstrip(" \t")
            if re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*",
                stripped,
            ):
                fences.append(_AdmissionFence(info, first_lineno, tuple(lines)))
                active = None
            else:
                lines.append(line)
            continue
        match = opener.fullmatch(line)
        if match is not None:
            marker = match.group("marker")
            info = match.group("info").strip().split(maxsplit=1)[0].casefold()
            active = (marker[0], len(marker), info, lineno + 1, [])
    return tuple(fences)


def _admission_command_paths(
    fence: _AdmissionFence,
    registry: Mapping[str, object],
) -> list[tuple[str, bool]]:
    """規範 command と判定できる行だけから (path, qsub 引数か) を抽出する。"""

    if fence.info in {"diff", "patch", "text", "markdown", "md"}:
        return []
    commands: list[tuple[str, bool]] = []
    negative = re.compile(
        r"実行してはなら|実行しない|直接実行を禁止|拒否され|"
        r"\b(?:do not|must not|never)\b",
        re.IGNORECASE,
    )
    by_folded = {path.casefold(): path for path in registry}
    for line in fence.lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "+", "-")) or negative.search(line):
            continue
        for match in _ADMISSION_PATH_RE.finditer(line):
            raw = match.group(0)
            normalized = re.sub(r"/+", "/", raw.replace("／", "/")).rstrip("/")
            canonical = by_folded.get(normalized.casefold())
            if canonical is None:
                continue
            before = line[:match.start()]
            token_prefix = before.rsplit(maxsplit=1)[-1] if before.split() else before
            if "://" in token_prefix or before.count("`") % 2:
                continue
            if "#" in before and before.index("#") < len(before):
                continue
            words = before.strip().split()
            qsub_argument = bool(words and words[0] == "qsub")
            interpreter_argument = bool(
                words and words[0] in {"python", "python3", "bash", "sh"}
            )
            direct = not before.strip() or (
                len(words) == 1
                and (words[0].endswith("/") or words[0] in {"./"})
            )
            if qsub_argument or interpreter_argument or direct:
                commands.append((canonical, qsub_argument))
    return commands


def _admission_code_spans_are_balanced(line: str) -> bool:
    runs = [len(match.group(0)) for match in re.finditer(r"`+", line)]
    return len(runs) % 2 == 0 and all(
        runs[index] == runs[index + 1]
        for index in range(0, len(runs), 2)
    )


def _admission_tables(
    text: str,
    *,
    label: str,
    findings: list[str],
) -> list[_AdmissionTable] | None:
    """可視な pipe table を構文検査し、orphan row も fail-closed にする。"""

    lines = text.splitlines()
    tables: list[_AdmissionTable] = []
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        block: list[str] = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            block.append(lines[index])
            index += 1
        if (
            len(block) < 2
            or any("\\|" in line for line in block)
            or any(not _admission_code_spans_are_balanced(line) for line in block)
        ):
            _admission_finding(
                findings,
                f"{label} に orphan row・escaped pipe・code span 崩れがある",
            )
            return None

        header, header_leading, header_trailing = _markdown_table_cells(block[0])
        separator, sep_leading, sep_trailing = _markdown_table_cells(block[1])
        valid_separator = (
            header_leading == header_trailing == 1
            and sep_leading == sep_trailing == 1
            and len(header) == len(separator)
            and bool(header)
            and all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator)
        )
        rows: list[tuple[str, ...]] = []
        malformed = not valid_separator
        for line in block[2:]:
            cells, leading, trailing = _markdown_table_cells(line)
            if leading != 1 or trailing != 1 or len(cells) != len(header):
                malformed = True
                continue
            rows.append(tuple(cells))
        if malformed:
            _admission_finding(
                findings,
                f"{label} に header/separator/row の malformed がある",
            )
            return None
        if len(rows) != len(set(rows)):
            _admission_finding(findings, f"{label} に duplicate row がある")
            return None
        tables.append(_AdmissionTable(tuple(header), tuple(rows)))
    return tables


def _admission_exact_table(
    tables: list[_AdmissionTable],
    header: tuple[str, ...],
    *,
    label: str,
    findings: list[str],
) -> _AdmissionTable | None:
    matches = [table for table in tables if table.header == header]
    if len(matches) != 1:
        _admission_finding(
            findings,
            f"{label} の exact header が {len(matches)} 件",
        )
        return None
    return matches[0]


def _admission_runbook_section(
    text: str, findings: list[str]
) -> tuple[str, str] | None:
    visible = _visible_dispatch_inventory_text(text)
    sections = list(_DISPATCH_SECTION_RE.finditer(visible))
    if len(sections) != 1:
        _admission_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} の可視な `### 7.0` 節が {len(sections)} 件",
        )
        return None
    section = sections[0]
    parent_headings = list(_DISPATCH_PARENT_HEADING_RE.finditer(visible))
    parents = [
        heading
        for heading in parent_headings
        if (
            heading.group("marker") == "##"
            and _DISPATCH_PARENT_TITLE_RE.match(heading.group("title"))
        )
    ]
    preceding = [heading for heading in parent_headings if heading.start() < section.start()]
    if len(parents) != 1 or not preceding or preceding[-1] is not parents[0]:
        _admission_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} の `### 7.0` が一意な親 `## 7` の直下でない",
        )
        return None
    tail = visible[section.end():]
    next_heading = re.search(r"^[ \t]{0,3}#{1,3}(?!#)[ \t]+", tail, re.MULTILINE)
    visible_body = tail[:next_heading.start()] if next_heading is not None else tail

    raw_sections = list(_DISPATCH_SECTION_RE.finditer(text))
    if len(raw_sections) != 1:
        _admission_finding(
            findings,
            f"{_DISPATCH_RUNBOOK} の raw `### 7.0` 節が {len(raw_sections)} 件",
        )
        return None
    raw_section = raw_sections[0]
    raw_tail = text[raw_section.end():]
    raw_next = re.search(r"^[ \t]{0,3}#{1,3}(?!#)[ \t]+", raw_tail, re.MULTILINE)
    raw_body = raw_tail[:raw_next.start()] if raw_next is not None else raw_tail
    return visible_body, raw_body


def _admission_hidden_header(
    raw: str,
    visible: str,
    header: tuple[str, ...],
) -> bool:
    rendered = "| " + " | ".join(header) + " |"
    raw_count = sum(line.strip() == rendered for line in raw.splitlines())
    visible_count = sum(line.strip() == rendered for line in visible.splitlines())
    return raw_count != visible_count


def _check_admission_projection(
    table: _AdmissionTable,
    registry: dict[str, dict[str, str]],
    findings: list[str],
) -> None:
    projected: set[tuple[str, str, str]] = set()
    duplicates: set[tuple[str, str, str]] = set()
    for row in table.rows:
        values = tuple(_admission_single_literal(cell) for cell in row)
        if any(value is None for value in values):
            _admission_finding(
                findings,
                "runbook §7.0 投影表の cell が単一 backtick literal でない",
            )
            return
        item = (values[0], values[1], values[2])
        assert all(value is not None for value in item)
        normalized = (str(item[0]), str(item[1]), str(item[2]))
        if normalized in projected:
            duplicates.add(normalized)
        projected.add(normalized)
    if duplicates:
        _admission_finding(findings, "runbook §7.0 投影表に duplicate row がある")
        return
    canonical = {
        (path, entry["class"], entry["evidence"])
        for path, entry in registry.items()
    }
    if projected != canonical:
        _admission_finding(
            findings,
            "runbook §7.0 投影表が registry と集合完全一致しない — "
            f"registry_only={sorted(canonical - projected)}, "
            f"runbook_only={sorted(projected - canonical)}",
        )


def _check_admission_unknown_table(
    table: _AdmissionTable,
    registry: dict[str, dict[str, str]],
    findings: list[str],
) -> None:
    seen: set[str] = set()
    for path_cell, explanation in table.rows:
        path = _admission_single_literal(path_cell)
        mentions, noncanonical = _admission_path_mentions(path_cell, registry)
        if noncanonical:
            _admission_finding(
                findings,
                f"unknown 表に非 canonical Pegasus path がある — {noncanonical}",
            )
            return
        if path is None and mentions:
            _admission_finding(findings, "unknown 表の path cell が単一 backtick literal でない")
            return
        if path is None or not path.startswith("tools/pegasus/"):
            continue
        if path in seen:
            _admission_finding(findings, f"unknown 表に duplicate path がある — {path}")
            return
        seen.add(path)
        entry = registry.get(path)
        if entry is None:
            _admission_finding(findings, f"unknown 表に未登録 path がある — {path}")
            return
        if entry["class"] == "unknown":
            continue
        legacy = (
            entry["class"] == "local-ok"
            and entry["evidence"].startswith("legacy-admitted")
            and "`local-ok`" in explanation
            and f"`{entry['evidence']}`" in explanation
        )
        if not legacy:
            _admission_finding(
                findings,
                f"unknown 表の admission 説明が registry と不整合 — {path}",
            )
            return

    expected = set(_ADMISSION_REQUIRED_GRANDFATHER_WARNINGS)
    if not expected <= seen:
        _admission_finding(
            findings,
            "unknown 表に必須 grandfather 警告がない — "
            f"missing={sorted(expected - seen)}",
        )
        return
    for path, (expected_class, expected_evidence) in (
        _ADMISSION_REQUIRED_GRANDFATHER_WARNINGS.items()
    ):
        entry = registry.get(path)
        if entry != {"class": expected_class, "evidence": expected_evidence}:
            _admission_finding(
                findings,
                f"必須 grandfather golden が registry と不一致 — {path}",
            )
            return


def _check_admission_measured_table(
    table: _AdmissionTable,
    registry: dict[str, dict[str, str]],
    findings: list[str],
) -> None:
    paths: set[str] = set()
    previous_path: str | None = None
    for row in table.rows:
        classification = _admission_single_literal(row[3]) or row[3]
        if classification != "local-ok":
            _admission_finding(findings, "runbook §7.0 実測表に非 local-ok 行がある")
            return
        explicit = re.search(r"`(tools/pegasus/[^`\s]+)(?:\s[^`]*)?`", row[0])
        if explicit is not None:
            previous_path = explicit.group(1)
        elif row[0].startswith("同 "):
            if previous_path is None:
                _admission_finding(findings, "runbook §7.0 実測表の `同` 行に継承元がない")
                return
        else:
            _admission_finding(findings, "runbook §7.0 実測表の path を解析できない")
            return
        assert previous_path is not None
        paths.add(previous_path)
    expected = {
        path
        for path, entry in registry.items()
        if entry["evidence"] == "runbook §7.0 実測"
    }
    if paths != expected:
        _admission_finding(
            findings,
            "runbook §7.0 実測表の path 集合が registry と不一致 — "
            f"registry={sorted(expected)}, runbook={sorted(paths)}",
        )


def _check_admission_runbook(
    text: str,
    registry: dict[str, dict[str, str]],
    findings: list[str],
) -> None:
    section = _admission_runbook_section(text, findings)
    if section is None:
        return
    visible, raw = section
    headers = (
        _ADMISSION_PROJECTION_HEADER,
        _ADMISSION_UNKNOWN_HEADER,
        _ADMISSION_MEASURED_HEADER,
    )
    if any(_admission_hidden_header(raw, visible, header) for header in headers):
        _admission_finding(findings, "runbook §7.0 に fence/comment へ隠した admission 表がある")
        return
    tables = _admission_tables(
        visible,
        label=f"{_DISPATCH_RUNBOOK} §7.0",
        findings=findings,
    )
    if tables is None:
        return
    projection = _admission_exact_table(
        tables,
        _ADMISSION_PROJECTION_HEADER,
        label="runbook §7.0 投影表",
        findings=findings,
    )
    unknown = _admission_exact_table(
        tables,
        _ADMISSION_UNKNOWN_HEADER,
        label="runbook §7.0 unknown 表",
        findings=findings,
    )
    measured = _admission_exact_table(
        tables,
        _ADMISSION_MEASURED_HEADER,
        label="runbook §7.0 実測表",
        findings=findings,
    )
    if projection is None or unknown is None or measured is None:
        return
    _check_admission_projection(projection, registry, findings)
    _check_admission_unknown_table(unknown, registry, findings)
    _check_admission_measured_table(measured, registry, findings)


def _check_admission_tagged_fences(
    text: str,
    registry: dict[str, dict[str, str]],
    declared_sites: Mapping[str, str],
    findings: list[str],
) -> None:
    """site tag を command target と exact 結合し、3 値を潰さず検査する。"""

    placeholder = "<login-direct | qsub-job-body | compute-only>"
    qsub_arguments: set[str] = set()
    for fence in _admission_fences(text):
        tag_rows = [
            (index, match.group("site"))
            for index, line in enumerate(fence.lines)
            if (match := _ADMISSION_SITE_TAG_RE.fullmatch(line)) is not None
            and match.group("site") != placeholder
        ]
        if len(tag_rows) > 1:
            _admission_finding(
                findings,
                f"Pegasus README の fenced block に admission-site tag が重複 — line={fence.first_lineno}",
            )
            return
        if tag_rows and tag_rows[0][1] not in _ADMISSION_SITES:
            _admission_finding(
                findings,
                "Pegasus README の admission-site tag が閉集合外 — "
                f"{tag_rows[0][1]}",
            )
            return

        commands = _admission_command_paths(fence, registry)
        if fence.info not in {"diff", "patch", "text", "markdown", "md"}:
            for offset, line in enumerate(fence.lines):
                stripped = line.strip()
                if (
                    "pegasus/" in line
                    and "tools/pegasus/" not in line
                    and not stripped.startswith(("#", "+", "-"))
                    and "://" not in line
                    and re.match(r"^(?:qsub|python\d*|bash|sh)\b", stripped)
                ):
                    _admission_finding(
                        findings,
                        "Pegasus README の fenced command が tools/pegasus/ literal を失っている — "
                        f"lines={[fence.first_lineno + offset]}",
                    )
                    return
        if not commands:
            continue
        if not tag_rows:
            _admission_finding(
                findings,
                f"Pegasus README の registry 実行体を含む fenced command に admission-site tag がない — line={fence.first_lineno}",
            )
            return
        tag_index, site = tag_rows[0]
        if tag_index != 0:
            _admission_finding(
                findings,
                f"Pegasus README の admission-site tag が fenced block の先頭行でない — line={fence.first_lineno}",
            )
            return
        for path, qsub_argument in commands:
            declared_site = declared_sites.get(path)
            if declared_site != site:
                _admission_finding(
                    findings,
                    "Pegasus README の fenced command site が宣言表と不一致 — "
                    f"path={path}, tag={site}, declaration={declared_site}",
                )
                return
            if site == "qsub-job-body" and not qsub_argument:
                _admission_finding(
                    findings,
                    f"Pegasus README の qsub-job-body 実行体が qsub 引数でない — {path}",
                )
                return
            if qsub_argument:
                qsub_arguments.add(path)

    required_qsub = {
        path for path, site in declared_sites.items() if site == "qsub-job-body"
    }
    if qsub_arguments != required_qsub:
        _admission_finding(
            findings,
            "Pegasus README の qsub-job-body 宣言集合が qsub 引数集合と不一致 — "
            f"declaration={sorted(required_qsub)}, qsub={sorted(qsub_arguments)}",
        )


def _check_admission_readme(
    text: str,
    registry: dict[str, dict[str, str]],
    findings: list[str],
) -> None:
    visible = _visible_dispatch_inventory_text(text)
    section_matches = list(re.finditer(
        r"^[ \t]{0,3}##(?!#)[ \t]+0\.(?:[ \t\u3000]+[^\n]+)?[ \t]*$",
        visible,
        re.MULTILINE,
    ))
    if len(section_matches) != 1:
        _admission_finding(
            findings,
            f"{_ADMISSION_README} の可視な `## 0.` 節が {len(section_matches)} 件",
        )
        return
    section_tail = visible[section_matches[0].end():]
    next_section = re.search(r"^[ \t]{0,3}#{1,2}(?!#)[ \t]+", section_tail, re.MULTILINE)
    visible_section = (
        section_tail[:next_section.start()]
        if next_section is not None
        else section_tail
    )
    raw_section_matches = list(re.finditer(
        r"^[ \t]{0,3}##(?!#)[ \t]+0\.(?:[ \t\u3000]+[^\n]+)?[ \t]*$",
        text,
        re.MULTILINE,
    ))
    if len(raw_section_matches) != 1:
        _admission_finding(
            findings,
            f"{_ADMISSION_README} の raw `## 0.` 節が {len(raw_section_matches)} 件",
        )
        return
    raw_section_tail = text[raw_section_matches[0].end():]
    raw_next_section = re.search(
        r"^[ \t]{0,3}#{1,2}(?!#)[ \t]+",
        raw_section_tail,
        re.MULTILINE,
    )
    raw_section = (
        raw_section_tail[:raw_next_section.start()]
        if raw_next_section is not None
        else raw_section_tail
    )
    if _admission_hidden_header(
        raw_section,
        visible_section,
        _ADMISSION_DECLARATION_HEADER,
    ):
        _admission_finding(findings, "Pegasus README の宣言表が fence/comment に隠れている")
        return
    tables = _admission_tables(
        visible_section,
        label=f"{_ADMISSION_README} 宣言表",
        findings=findings,
    )
    if tables is None:
        return
    declaration = _admission_exact_table(
        tables,
        _ADMISSION_DECLARATION_HEADER,
        label="Pegasus README 宣言表",
        findings=findings,
    )
    if declaration is None:
        return
    if not declaration.rows:
        _admission_finding(findings, "Pegasus README 宣言表が空である")
        return

    declared: set[str] = set()
    declared_sites: dict[str, str] = {}
    for row in declaration.rows:
        values = tuple(_admission_single_literal(cell) for cell in row)
        if any(value is None for value in values):
            _admission_finding(findings, "Pegasus README 宣言表の cell が単一 backtick literal でない")
            return
        path, site, documented_class = (str(value) for value in values)
        _, noncanonical = _admission_path_mentions(path, registry)
        if noncanonical:
            _admission_finding(
                findings,
                f"Pegasus README 宣言表に非 canonical Pegasus path がある — {noncanonical}",
            )
            return
        if path in declared:
            _admission_finding(findings, f"Pegasus README 宣言表に duplicate path がある — {path}")
            return
        declared.add(path)
        declared_sites[path] = site
        entry = registry.get(path)
        if entry is None:
            _admission_finding(findings, f"Pegasus README 宣言表に未登録 path がある — {path}")
            return
        if site not in _ADMISSION_SITES:
            _admission_finding(findings, f"Pegasus README 宣言表の site が閉集合外 — {site}")
            return
        if documented_class != entry["class"]:
            _admission_finding(findings, f"Pegasus README 宣言表の class が registry と不一致 — {path}")
            return
        if (site == "login-direct") != (entry["class"] == "local-ok"):
            _admission_finding(findings, f"Pegasus README 宣言表の site/class が不整合 — {path}")
            return

    mentioned, noncanonical = _admission_path_mentions(text, registry)
    if noncanonical:
        _admission_finding(
            findings,
            f"Pegasus README に非 canonical Pegasus path がある — {noncanonical}",
        )
        return
    if not mentioned <= declared:
        _admission_finding(
            findings,
            "Pegasus README 本文の既知 path が宣言表に未掲載 — "
            f"{sorted(mentioned - declared)}",
        )
        return
    _check_admission_tagged_fences(text, registry, declared_sites, findings)


def _check_pegasus_admission_docs_impl(findings: list[str]) -> None:
    """registry の class/evidence と公表 inventory の同期だけを検査する。"""

    registry = _load_admission_registry(findings)
    if registry is None:
        return
    runbook = _safe_read_text(
        REPO / _DISPATCH_RUNBOOK,
        findings,
        f"{_ADMISSION_PREFIX}{_DISPATCH_RUNBOOK} の読取失敗",
    )
    readme = _safe_read_text(
        REPO / _ADMISSION_README,
        findings,
        f"{_ADMISSION_PREFIX}{_ADMISSION_README} の読取失敗",
    )
    if runbook is not None:
        _check_admission_runbook(runbook, registry, findings)
    if readme is not None:
        _check_admission_readme(readme, registry, findings)


def _check_pegasus_admission_docs(findings: list[str]) -> None:
    """Admission 検査全体から BaseException を漏らさず fail-closed にする。"""

    try:
        _check_pegasus_admission_docs_impl(findings)
    except BaseException as exc:
        try:
            detail = _admission_exception(exc)
        except BaseException:
            detail = "BaseException"
        try:
            _admission_finding(
                findings,
                f"admission checker 内部失敗を fail-closed 化 — {detail}",
            )
        except BaseException:
            findings.append(
                f"{_ADMISSION_PREFIX}admission checker 内部失敗を fail-closed 化 — BaseException"
            )


def _provenance_markdown_ambiguities(text: str) -> tuple[str, ...]:
    """共有 scanner が過剰 mask しうる provenance 固有の曖昧性を列挙する。"""

    issues: list[str] = []
    in_comment = False
    fence: tuple[str, int, int] | None = None
    inline_code = re.compile(r"(?P<ticks>`+)(?P<body>.*?)(?P=ticks)")
    fence_candidate = re.compile(
        r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})(?P<info>.*)$"
    )

    for lineno, line in enumerate(text.splitlines(), 1):
        if fence is not None:
            marker_char, marker_len, _ = fence
            stripped = line.lstrip(" \t")
            indent = len(line) - len(stripped)
            if indent <= 3 and re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*", stripped
            ):
                fence = None
                continue
            candidate = fence_candidate.fullmatch(line)
            if candidate is not None and candidate.group("marker")[0] != marker_char:
                issues.append(f"line {lineno}: 異種 fence closer")
            continue

        if not in_comment:
            for match in inline_code.finditer(line):
                if "<!--" in match.group("body") or "-->" in match.group("body"):
                    issues.append(
                        f"line {lineno}: inline code 内の HTML comment delimiter"
                    )

        visible, next_in_comment = _mask_html_comments(line, in_comment)
        if not in_comment:
            candidate = fence_candidate.fullmatch(visible)
            if candidate is not None:
                marker = candidate.group("marker")
                info = candidate.group("info")
                if marker[0] == "`" and "`" in info:
                    issues.append(f"line {lineno}: 無効な backtick fence info string")
                else:
                    fence = (marker[0], len(marker), lineno)
        in_comment = next_in_comment

    if fence is not None:
        issues.append(f"line {fence[2]}: 未閉じ code fence")
    if in_comment:
        issues.append("未閉じ HTML comment")
    return tuple(dict.fromkeys(issues))


def _dispatch_tables(text: str) -> _DispatchTables | None:
    """段/条件表を一意に取り出し、typed edge へ展開する。

    表の直接参照だけを閉じる。leaf reference 本文から別 living doc への間接委譲は、
    義務本文の意味判定を要するため本 lint の既知限界として検査しない。
    """

    visible_text = _visible_dispatch_inventory_text(text)
    sections = {
        heading: _markdown_sections(visible_text, heading)
        for heading in ("段 dispatch", "条件 dispatch")
    }
    if any(len(matches) != 1 for matches in sections.values()):
        return None

    edges: set[tuple[str, str, str, str]] = set()
    condition_triggers: dict[str, set[str]] = {}
    condition_leaked_tokens: dict[str, set[str]] = {}
    condition_row_counts: dict[str, int] = {}
    paths: set[str] = set()
    structure_errors: list[str] = []

    stage_lines = sections["段 dispatch"][0].splitlines()
    legend_count = stage_lines.count(DEV_WAVE_STAGE_DISPATCH_LEGEND)
    header_count = stage_lines.count(DEV_WAVE_STAGE_DISPATCH_HEADER)
    if legend_count != 1:
        structure_errors.append(
            f"段 dispatch 凡例が exact 1 件でない — rows={legend_count}"
        )
    if header_count != 1:
        structure_errors.append(
            f"段 dispatch header が exact 1 件でない — rows={header_count}"
        )

    for line in stage_lines:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line == DEV_WAVE_STAGE_DISPATCH_HEADER or all(
            re.fullmatch(r":?-+:?", cell) for cell in cells
        ):
            continue
        if len(cells) != 3:
            structure_errors.append(
                f"段 dispatch data row が3列でない — cells={len(cells)}"
            )
            continue
        key, mode, reference_cell = cells
        if mode not in {"U", "C"}:
            structure_errors.append(
                f"段 dispatch {key!r} の種別が U/C exact 1文字でない — {mode!r}"
            )
            continue
        reference_errors = _dispatch_reference_cell_errors(reference_cell)
        if reference_errors:
            structure_errors.extend(
                f"段 dispatch {key!r} の参照 cell grammar が不一致 — {error}"
                for error in reference_errors
            )
        pairs, line_paths = _dispatch_pairs_from_line(reference_cell)
        pair_paths = {path for path, _ in pairs}
        if line_paths != pair_paths:
            structure_errors.append(
                f"段 dispatch {key!r} に節へ束縛されない path がある — "
                f"paths={sorted(line_paths)}, pair_paths={sorted(pair_paths)}"
            )
        edges.update((key, mode, path, section) for path, section in pairs)
        paths.update(line_paths)

    condition_lines = sections["条件 dispatch"][0].splitlines()
    condition_header_count = condition_lines.count(
        DEV_WAVE_CONDITION_DISPATCH_HEADER
    )
    first_condition_table_row = next(
        (index for index, line in enumerate(condition_lines) if line.startswith("|")),
        None,
    )
    if (
        condition_header_count != 1
        or first_condition_table_row is None
        or condition_lines[first_condition_table_row]
        != DEV_WAVE_CONDITION_DISPATCH_HEADER
    ):
        structure_errors.append(
            "条件 dispatch header が exact 1 件でない、または先頭表行でない — "
            f"rows={condition_header_count}"
        )

    for index, line in enumerate(condition_lines):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if (
            index == first_condition_table_row
            or line == DEV_WAVE_CONDITION_DISPATCH_HEADER
            or all(
                re.fullmatch(r":?-+:?", cell) for cell in cells
            )
        ):
            continue
        if len(cells) != 3:
            structure_errors.append(
                f"条件 dispatch data row が3列でない — cells={len(cells)}"
            )
            continue
        key, trigger, reference_cell = cells
        reference_errors = _dispatch_reference_cell_errors(reference_cell)
        if reference_errors:
            structure_errors.extend(
                f"条件 dispatch {key!r} の参照 cell grammar が不一致 — {error}"
                for error in reference_errors
            )
        pairs, line_paths = _dispatch_pairs_from_line(reference_cell)
        pair_paths = {path for path, _ in pairs}
        if line_paths != pair_paths:
            structure_errors.append(
                f"条件 dispatch {key!r} に節へ束縛されない path がある — "
                f"paths={sorted(line_paths)}, pair_paths={sorted(pair_paths)}"
            )
        edges.update(
            (f"条件 {key}", "C", path, section)
            for path, section in pairs
        )
        condition_triggers.setdefault(key, set()).add(trigger)
        leaks = {
            match.group(0) for match in _DISPATCH_TOKEN_RE.finditer(trigger)
        }
        condition_leaked_tokens.setdefault(key, set()).update(leaks)
        condition_row_counts[key] = condition_row_counts.get(key, 0) + 1
        paths.update(line_paths)

    return _DispatchTables(
        edges,
        condition_triggers,
        condition_leaked_tokens,
        condition_row_counts,
        paths,
        tuple(structure_errors),
    )


def resolve_condition_sections(
    dev_wave_text: str,
    situation: str,
) -> dict[str, tuple[str, ...]]:
    """入口の条件表だけから、状況に一致する条件番号と参照節を解決する。"""

    dispatch = _dispatch_tables(dev_wave_text)
    if dispatch is None:
        return {}
    return {
        key: tuple(sorted(
            section for _, section in dispatch.conditions.get(key, set())
        ))
        for key, triggers in dispatch.condition_triggers.items()
        if any(situation in trigger for trigger in triggers)
    }


def _parse_frontmatter(text: str) -> tuple[dict[str, str], set[str]] | None:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    values: dict[str, str] = {}
    duplicates: set[str] = set()
    for line in lines[1:end]:
        if ":" not in line:
            return None
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            return None
        if key in values:
            duplicates.add(key)
        else:
            values[key] = value.strip()
    return values, duplicates


def _check_codex_skill_guard(
    findings: list[str],
    *,
    skill_name: str,
    limits: dict[str, TextLimit],
    expected_files: frozenset[str],
    literals: tuple[str, ...],
    openai_yaml: str,
    expected_description: str | None = None,
    expected_sha256: str | None = None,
    forbidden_literals: tuple[str, ...] = (),
    exact_literals: tuple[str, ...] = (),
    exact_visible_sections: Mapping[str, str] | None = None,
    forbidden_patterns: tuple[tuple[re.Pattern[str], str], ...] = (),
) -> None:
    """repo-scoped Codex Skill の閉包・interface・必須 adapter を検査する。"""

    skill_root = REPO / ".agents" / "skills" / skill_name
    label = f"Codex {skill_name} Skill"
    if skill_root.is_symlink():
        findings.append(
            f".agents/skills/{skill_name}: skill directory が symlink — "
            "外部 member を列挙・読取しない"
        )
        actual_skill_files: set[Path] = set()
    else:
        actual_skill_files = (
            {
                path for path in skill_root.rglob("*")
                if not path.is_dir() or path.is_symlink()
            }
            if skill_root.is_dir() else set()
        )
    expected_skill_files = {REPO / rel for rel in expected_files}
    for path in sorted(actual_skill_files - expected_skill_files):
        findings.append(
            f"{path.relative_to(REPO)}: {label} の予算未登録実体"
        )
    skill_decoded: dict[str, str] = {}
    for path in sorted(expected_skill_files - actual_skill_files):
        findings.append(
            f"{path.relative_to(REPO)}: {label} の必須 file が不在"
        )
    for rel, limit in limits.items():
        path = REPO / rel
        if path not in actual_skill_files:
            continue
        text = _safe_read_text(
            path,
            findings,
            f"{rel}: Skill 検査の読取失敗",
            newline="",
            unsafe_path_prefix=(
                f"{rel}: symlink または regular file 以外 — "
                "Skill interface と予算の検査対象として受理しない"
            ),
            invalid_utf8_prefix=f"{rel}: invalid UTF-8",
        )
        if text is None:
            continue
        skill_decoded[rel] = text
        size = len(text.encode("utf-8"))
        if size > limit.max_bytes:
            findings.append(
                f"{rel}: {size} bytes > 予算 {limit.max_bytes} bytes"
            )
        if limit.max_line_chars is not None:
            for lineno, line in enumerate(text.splitlines(), 1):
                if len(line) > limit.max_line_chars:
                    findings.append(
                        f"{rel}:{lineno}: {len(line)} chars > 最長行予算 "
                        f"{limit.max_line_chars}"
                    )

    skill_rel = f".agents/skills/{skill_name}/SKILL.md"
    skill_text = skill_decoded.get(skill_rel)
    if skill_text is not None:
        parsed = _parse_frontmatter(skill_text)
        if parsed is None:
            findings.append(f"{skill_rel}: frontmatter を一意に解析できない")
        else:
            values, duplicates = parsed
            if duplicates:
                findings.append(
                    f"{skill_rel}: frontmatter key 重複: "
                    f"{', '.join(sorted(duplicates))}"
                )
            if set(values) != {"name", "description"}:
                findings.append(
                    f"{skill_rel}: frontmatter key 集合が契約と不一致"
                )
            if values.get("name") != skill_name:
                findings.append(
                    f"{skill_rel}: name は {skill_name!r} 必須"
                )
            description = values.get("description", "")
            if not description.strip():
                findings.append(f"{skill_rel}: description が空")
            elif (
                expected_description is not None
                and description != expected_description
            ):
                findings.append(
                    f"{skill_rel}: description が explicit trigger 契約と不一致"
                )
        for literal in literals:
            if literal not in skill_text:
                findings.append(
                    f"{skill_rel}: Codex adapter 契約がない — {literal!r}"
                )
        if (
            expected_sha256 is not None
            and hashlib.sha256(skill_text.encode("utf-8")).hexdigest()
            != expected_sha256
        ):
            findings.append(
                f"{skill_rel}: whole-file SHA-256 が契約と不一致"
            )
        for literal in forbidden_literals:
            if literal in skill_text:
                findings.append(
                    f"{skill_rel}: 共通 dispatcher の leaf path を重複 pin している — "
                    f"{literal!r}"
                )
        for literal in exact_literals:
            count = skill_text.count(literal)
            if count != 1:
                findings.append(
                    f"{skill_rel}: exact adapter literal が {count} 件 — {literal!r}"
                )
        for heading, expected in (exact_visible_sections or {}).items():
            _check_exact_visible_h2_section(
                findings,
                rel=skill_rel,
                text=skill_text,
                heading=heading,
                expected=expected,
            )
        for pattern, label_text in forbidden_patterns:
            if pattern.search(skill_text):
                findings.append(
                    f"{skill_rel}: 共通 land 契約外の実行経路 — {label_text}"
                )

    openai_rel = f".agents/skills/{skill_name}/agents/openai.yaml"
    openai_text = skill_decoded.get(openai_rel)
    if openai_text is not None and openai_text != openai_yaml:
        findings.append(
            f"{openai_rel}: 生成済み Skill interface 契約と不一致"
        )


def _visible_reference_slices(
    text: str,
) -> tuple[str, dict[str, list[str]], str]:
    """可視 H2 の raw offset を境界に、原文 byte slice を返す。"""

    visible_lines = _dispatch_visible_markdown_lines(text)
    boundaries: list[tuple[int, str | None]] = []
    for visible, offset, _ in visible_lines:
        if not re.match(r"^##\s+", visible):
            continue
        match = re.match(r"^##\s+([^\s—]+)", visible)
        boundaries.append((offset, match.group(1) if match is not None else None))

    first = boundaries[0][0] if boundaries else len(text)
    slices: dict[str, list[str]] = {}
    for index, (start, section_id) in enumerate(boundaries):
        end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text)
        if section_id is not None:
            slices.setdefault(section_id, []).append(text[start:end])
    visible_text = "".join(
        visible + newline for visible, _, newline in visible_lines
    )
    return text[:first], slices, visible_text


def _check_dev_wave_layer_budget(
    findings: list[str],
    decoded: Mapping[str, str],
    edges: set[tuple[str, str, str, str]],
) -> None:
    """dispatch edge から leaf unique-footprint の三層予算を検査する。"""

    registered_pairs = {
        (path, section)
        for path, sections in REQUIRED_REFERENCE_SECTIONS.items()
        for section in sections
    }
    unconditional = _stage_dispatch_from_edges(edges, "U")
    l1_pairs = set().union(*(
        unconditional.get(key, set()) for key in DEV_WAVE_L1_STAGE_KEYS
    )) if DEV_WAVE_L1_STAGE_KEYS else set()
    l1_5_pairs = (
        set().union(*(
            unconditional.get(key, set()) for key in DEV_WAVE_L1_5_STAGE_KEYS
        )) if DEV_WAVE_L1_5_STAGE_KEYS else set()
    ) - l1_pairs
    l1_pairs &= registered_pairs
    l1_5_pairs &= registered_pairs
    l2_pairs = registered_pairs - l1_pairs - l1_5_pairs
    layer_pairs = {
        "L1": l1_pairs,
        "L1.5": l1_5_pairs,
        "L2": l2_pairs,
    }
    layer_bytes = {"L1": 0, "L1.5": 0, "L2": 0}
    classified_bytes = 0
    assigned_preamble_bytes = 0
    actual_bytes = 0

    for rel in sorted(DEV_WAVE_REFERENCE_FILES):
        text = decoded.get(rel)
        if text is None:
            continue
        actual_bytes += len(text.encode("utf-8"))
        preamble, slices, visible_text = _visible_reference_slices(text)
        present_layers = [
            layer
            for layer in ("L1", "L1.5", "L2")
            if any(path == rel for path, _ in layer_pairs[layer])
        ]
        if "L1" in present_layers:
            preamble_layer = "L1"
        elif "L1.5" in present_layers:
            preamble_layer = "L1.5"
        else:
            findings.append(
                f"{rel}: L2 節しかない reference — preamble の無上限化を拒否"
            )
            preamble_layer = None
        if preamble_layer is not None:
            preamble_bytes = len(preamble.encode("utf-8"))
            assigned_preamble_bytes += preamble_bytes
            layer_bytes[preamble_layer] += preamble_bytes

        for layer, pairs in layer_pairs.items():
            for path, section in sorted(pairs):
                if path != rel:
                    continue
                section_slices = slices.get(section, [])
                exact_count = len(_reference_id_sections(visible_text, section))
                if len(section_slices) != 1 or exact_count != 1:
                    findings.append(
                        f"{rel}: 可視 H2 {section} と byte slice が1:1でない — "
                        f"visible_exact={exact_count}, slices={len(section_slices)}"
                    )
                if len(section_slices) != 1:
                    continue
                section_bytes = len(section_slices[0].encode("utf-8"))
                classified_bytes += section_bytes
                layer_bytes[layer] += section_bytes
                if (
                    layer == "L2"
                    and section_bytes > DEV_WAVE_L2_SECTION_BYTES_MAX
                ):
                    findings.append(
                        f"{rel}: L2 節 {section} が {section_bytes} bytes > "
                        f"単節予算 {DEV_WAVE_L2_SECTION_BYTES_MAX} bytes"
                    )

    covered_bytes = classified_bytes + assigned_preamble_bytes
    if covered_bytes != actual_bytes:
        findings.append(
            "docs/dev-wave/**: 分類済み節 + preamble が実 bytes を被覆しない — "
            f"classified={classified_bytes}, preamble={assigned_preamble_bytes}, "
            f"actual={actual_bytes}"
        )
    if layer_bytes["L1"] > DEV_WAVE_L1_BYTES_MAX:
        findings.append(
            f"docs/dev-wave/**: L1 unique footprint {layer_bytes['L1']} bytes > "
            f"予算 {DEV_WAVE_L1_BYTES_MAX} bytes"
        )
    if layer_bytes["L1.5"] > DEV_WAVE_L1_5_BYTES_MAX:
        findings.append(
            f"docs/dev-wave/**: L1.5 unique footprint {layer_bytes['L1.5']} bytes > "
            f"予算 {DEV_WAVE_L1_5_BYTES_MAX} bytes"
        )


def _launcher_stage_choices() -> tuple[str, ...] | None:
    """dev-wave launcher の `STAGES` 定数を import せずに読む。"""

    path = REPO / "tools" / "dev_wave_codex.py"
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return None
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if value is None or not any(
            isinstance(target, ast.Name) and target.id == "STAGES"
            for target in targets
        ):
            continue
        try:
            choices = ast.literal_eval(value)
        except (ValueError, TypeError):
            return None
        if isinstance(choices, (tuple, list)) and all(
            isinstance(choice, str) for choice in choices
        ):
            return tuple(choices)
        return None
    return None


def _visible_single_dispatch_lines(
    text: str,
) -> list[tuple[str, int, str]]:
    """単独段 marker 用に Markdown の不可視行を除いた可視行を返す。"""

    try:
        lines = visible_top_level_lines(text, reject_unicode_separators=False)
    except AuthorityError:
        return []
    visible: list[tuple[str, int, str]] = []
    for line, offset, newline in lines:
        stripped = line.lstrip(" \t")
        leading = line[: len(line) - len(stripped)]
        indent = len(leading.replace("\t", "    "))
        if indent >= 4 or stripped.startswith(">"):
            continue
        visible.append((line, offset, newline))
    return visible


def _visible_marker_occurrences(text: str, marker: str) -> int:
    """不可視 Markdown・blockquote・indented code 内を除いた marker 数。"""

    return sum(
        line.count(marker)
        for line, _offset, _newline in _visible_single_dispatch_lines(text)
    )


def _check_dev_wave_single_dispatch_structure(
    agents_text: str | None,
    operations_text: str | None,
    findings: list[str],
) -> None:
    """単独段 dispatch の AGENTS marker と DW-O02 到達文を構造 pin する。"""

    if agents_text is not None:
        _, visible_sections = _visible_h2_section_slices(agents_text)
        agents_sections = visible_sections.get(
            DEV_WAVE_SINGLE_DISPATCH_AGENTS_HEADING,
            [],
        )
        if len(agents_sections) != 1:
            findings.append(DEV_WAVE_SINGLE_DISPATCH_AGENTS_SECTION_FINDING)
        else:
            visible_agents_lines = _visible_single_dispatch_lines(
                agents_sections[0]
            )
            declaration_positions = [
                index
                for index, (line, _offset, _newline) in enumerate(
                    visible_agents_lines
                )
                if DEV_WAVE_SINGLE_DISPATCH_DECLARATION_LITERAL in line
            ]
            declaration_count = len(declaration_positions)
            if declaration_count != 1:
                findings.append(DEV_WAVE_SINGLE_DISPATCH_DECLARATION_FINDING)
            else:
                projection_positions = [
                    index
                    for index, (line, _offset, _newline) in enumerate(
                        visible_agents_lines
                    )
                    if (
                        index > declaration_positions[0]
                        and DEV_WAVE_SINGLE_DISPATCH_PROJECTION_HEADING in line
                    )
                ]
                if len(projection_positions) != 1:
                    findings.append(DEV_WAVE_SINGLE_DISPATCH_PROJECTION_FINDING)
                else:
                    projection_body = "\n".join(
                        line
                        for line, _offset, _newline in visible_agents_lines[
                            projection_positions[0]:
                        ]
                    )
                    if (
                        DEV_WAVE_SINGLE_DISPATCH_PROJECTION_PATH_RE.search(
                            projection_body
                        ) is None
                        or DEV_WAVE_SINGLE_DISPATCH_PROJECTION_STOP_LITERAL
                        not in projection_body
                    ):
                        findings.append(
                            DEV_WAVE_SINGLE_DISPATCH_PROJECTION_CONTENT_FINDING
                        )
                stage_match = re.search(
                    r"stage=<([^>]+)>",
                    DEV_WAVE_SINGLE_DISPATCH_DECLARATION_LITERAL,
                )
                launcher_choices = _launcher_stage_choices()
                if launcher_choices is None:
                    findings.append(DEV_WAVE_SINGLE_DISPATCH_LAUNCHER_FINDING)
                elif (
                    stage_match is not None
                    and tuple(stage_match.group(1).split("|"))
                    != launcher_choices
                ):
                    findings.append(DEV_WAVE_SINGLE_DISPATCH_STAGE_FINDING)

    if operations_text is not None:
        visible_operations = _visible_dispatch_inventory_text(operations_text)
        operations_sections = _reference_id_sections(
            visible_operations,
            "DW-O02",
        )
        if len(operations_sections) != 1:
            findings.append(DEV_WAVE_SINGLE_DISPATCH_OPERATIONS_SECTION_FINDING)
        elif (
            _visible_marker_occurrences(
                operations_sections[0],
                DEV_WAVE_SINGLE_DISPATCH_OPERATIONS_REFERENCE_LITERAL,
            )
            != 1
        ):
            findings.append(
                DEV_WAVE_SINGLE_DISPATCH_OPERATIONS_REFERENCE_FINDING
            )


def _dev_wave_visible_inventory_is_exact(decoded: Mapping[str, str]) -> bool:
    """既存 inventory finding がある入力では層 finding を重ねない。"""

    for rel, expected in REQUIRED_REFERENCE_SECTIONS.items():
        text = decoded.get(rel)
        if text is None:
            return False
        visible_text = _visible_dispatch_inventory_text(text)
        actual = re.findall(r"^##\s+([^\s—]+)", visible_text, re.MULTILINE)
        if len(actual) != len(expected) or set(actual) != expected:
            return False
    return True


def _check_dev_wave_model_pins(
    dev_wave_text: str | None,
    workers_text: str | None,
    operations_text: str | None,
    findings: list[str],
) -> None:
    """DW-O01 の model 権威と他 surface の slug 不在を pin する。"""

    if dev_wave_text is not None:
        visible_dev_wave = _visible_markdown_text(dev_wave_text)
        if DEV_WAVE_MODEL_SLUG_RE.search(visible_dev_wave) is not None:
            findings.append(DEV_WAVE_COMMAND_MODEL_SLUG_ABSENCE_FINDING)

    if workers_text is not None:
        visible_workers = _visible_markdown_text(workers_text)
        if DEV_WAVE_MODEL_SLUG_RE.search(visible_workers) is not None:
            findings.append(DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING)

    if operations_text is not None:
        dw_o01_pattern = re.compile(
            r"^## DW-O01(?:\s+—[^\n]*)?\s*$\n"
            r"(?P<body>.*?)(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        dw_o01_matches = list(dw_o01_pattern.finditer(operations_text))
        if len(dw_o01_matches) != 1:
            findings.append(DEV_WAVE_DW_O01_SECTION_CARDINALITY_FINDING)
        else:
            dw_o01_match = dw_o01_matches[0]
            body = dw_o01_match.group("body")
            try:
                authority_count = len(
                    visible_top_level_matches(
                        body,
                        re.compile(
                            re.escape(DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL)
                        ),
                        label="DW-O01 model authority",
                    )
                )
            except AuthorityError:
                authority_count = 0
            authority_residue = _visible_markdown_text(
                dw_o01_match.group(0)
            ).replace(
                DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL,
                "",
            )
            if (
                authority_count != 1
                or DEV_WAVE_MODEL_SLUG_RE.search(authority_residue) is not None
            ):
                findings.append(DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING)
            try:
                route_count = len(
                    visible_top_level_matches(
                        body,
                        re.compile(
                            re.escape(DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL)
                        ),
                        label="DW-O01 dispatcher route",
                    )
                )
            except AuthorityError:
                route_count = 0
            if route_count != 1:
                findings.append(DEV_WAVE_DW_O01_MODEL_PLACEHOLDER_FINDING)

        operations_outside_dw_o01 = dw_o01_pattern.sub("", operations_text)
        if DEV_WAVE_MODEL_SLUG_RE.search(
            _visible_markdown_text(operations_outside_dw_o01)
        ) is not None:
            findings.append(
                DEV_WAVE_OPERATIONS_OUTSIDE_DW_O01_MODEL_SLUG_ABSENCE_FINDING
            )


def _check_dev_wave_operations_forbidden_terms(
    operations_text: str | None,
    findings: list[str],
) -> None:
    """operations 全体の可視本文から廃止済み受理経路を排除する。"""

    if operations_text is None:
        return
    visible_operations = _visible_markdown_text(operations_text)
    for literal, finding in (
        (
            "non-attributable-only",
            DEV_WAVE_OPERATIONS_NON_ATTRIBUTABLE_ONLY_ABSENCE_FINDING,
        ),
        (
            "tools/check_acceptance_reds.py",
            DEV_WAVE_OPERATIONS_ACCEPTANCE_REDS_TOOL_ABSENCE_FINDING,
        ),
    ):
        if literal in visible_operations:
            findings.append(finding)


def _check_dev_wave_waiter_consumer_pins(
    dev_wave_text: str | None,
    core_text: str | None,
    operations_text: str | None,
    findings: list[str],
) -> None:
    """canonical waiter の docs consumer と実 target を可視正本へ束縛する。"""

    target = REPO / DEV_WAVE_WAITER_TARGET
    try:
        target_mode = target.lstat().st_mode
    except OSError:
        target_mode = None
    if target_mode is None or not stat.S_ISREG(target_mode):
        findings.append(DEV_WAVE_WAITER_TARGET_FINDING)

    def sequence_count(section: str, expected: tuple[str, ...]) -> int:
        lines = section.splitlines()
        width = len(expected)
        return sum(
            tuple(lines[index:index + width]) == expected
            for index in range(len(lines) - width + 1)
        )

    def one_reference_section(text: str, section_id: str) -> str | None:
        _, byte_slices, visible = _visible_reference_slices(text)
        sections = _reference_id_sections(visible, section_id)
        return (
            sections[0]
            if len(sections) == 1 and len(byte_slices.get(section_id, [])) == 1
            else None
        )

    def one_named_section(text: str, heading: str, slice_key: str) -> str | None:
        _, byte_slices, visible = _visible_reference_slices(text)
        sections = _markdown_sections(visible, heading)
        return (
            sections[0]
            if len(sections) == 1 and len(byte_slices.get(slice_key, [])) == 1
            else None
        )

    def normative_sentence_count(section: str, expected: str) -> int:
        count = 0
        try:
            lines = visible_top_level_lines(section)
        except AuthorityError:
            return 0
        for visible, _, _ in lines:
            count += sum(
                sentence + "。" == expected
                for sentence in visible.split("。")[:-1]
            )
        return count

    disclaimer_sections: list[str] = []
    if dev_wave_text is not None:
        state_machine = one_named_section(
            dev_wave_text, "9 段状態機械", "9"
        )
        if state_machine is not None:
            stage6_ok = (
                sequence_count(
                    state_machine, DEV_WAVE_STAGE6_WAITER_CONSUMER_LINES
                ) == 1
            )
            stage9_ok = (
                sequence_count(
                    state_machine, DEV_WAVE_STAGE9_WAITER_CONSUMER_LINES
                ) == 1
            )
            if not stage6_ok:
                findings.append(DEV_WAVE_STAGE6_WAITER_CONSUMER_FINDING)
            if not stage9_ok:
                findings.append(DEV_WAVE_STAGE9_WAITER_CONSUMER_FINDING)
            if stage6_ok and stage9_ok:
                disclaimer_sections.append(state_machine)

    if core_text is not None:
        dw_c00 = one_reference_section(core_text, "DW-C00")
        if dw_c00 is not None:
            dw_c00_count = normative_sentence_count(
                dw_c00, DEV_WAVE_DW_C00_WAITER_CONSUMER_LITERAL
            )
            if dw_c00_count != 1:
                findings.append(DEV_WAVE_DW_C00_WAITER_CONSUMER_FINDING)
            else:
                disclaimer_sections.append(dw_c00)

    if operations_text is not None:
        dw_o01 = one_reference_section(operations_text, "DW-O01")
        if dw_o01 is not None:
            dw_o01_count = 0
            try:
                dw_o01_count = len(
                    visible_top_level_matches(
                        dw_o01,
                        re.compile(
                            re.escape(DEV_WAVE_DW_O01_WAITER_CONSUMER_LITERAL)
                        ),
                        label="DW-O01 waiter consumer",
                    )
                )
            except AuthorityError:
                dw_o01_count = 0
            if dw_o01_count != 1:
                findings.append(DEV_WAVE_DW_O01_WAITER_CONSUMER_FINDING)
            else:
                disclaimer_sections.append(dw_o01)

    if any(
        DEV_WAVE_WAITER_DISCLAIMER_RE.search(section) is not None
        for section in disclaimer_sections
    ):
        findings.append(DEV_WAVE_WAITER_DISCLAIMER_FINDING)


def _check_dev_wave_reasoning_effort_pins(
    workers_text: str,
    findings: list[str],
    *,
    operations_text: str | None = None,
) -> None:
    """採用済み reasoning effort と O16 の非 override を可視節へ pin する。"""

    visible_workers_text = _visible_dispatch_inventory_text(workers_text)
    for section_id, expected, required_text, finding in (
        (
            "DW-S02",
            "medium",
            DEV_WAVE_DW_S02_REASONING_XHIGH_LITERAL,
            DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING,
        ),
        (
            "DW-S03",
            "medium",
            DEV_WAVE_DW_S03_REASONING_XHIGH_LITERAL,
            DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING,
        ),
        (
            "DW-S06-A",
            "medium",
            DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE,
            DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING,
        ),
        (
            "DW-S06-C",
            "medium",
            DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE,
            DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING,
        ),
        (
            "DW-S05-A",
            "medium",
            DEV_WAVE_DW_S05_A_REASONING_XHIGH_SENTENCE,
            DEV_WAVE_DW_S05_A_REASONING_XHIGH_FINDING,
        ),
    ):
        sections = _reference_id_sections(visible_workers_text, section_id)
        if len(sections) != 1:
            findings.append(finding)
            continue
        visible_section = sections[0]
        values = [
            match.group("value")
            for match in DEV_WAVE_REASONING_EFFORT_RE.finditer(visible_section)
        ]
        required_text_count = (
            visible_section.replace("\r\n", "\n").split("\n").count(required_text)
            if section_id in {"DW-S05-A", "DW-S06-A", "DW-S06-C"}
            else visible_section.count(required_text)
        )
        if values != [expected] or required_text_count != 1:
            findings.append(finding)

    if operations_text is None:
        return
    visible_operations_text = _visible_dispatch_inventory_text(operations_text)
    sections = _reference_id_sections(visible_operations_text, "DW-O16")
    if len(sections) != 1:
        findings.append(DEV_WAVE_DW_O16_REASONING_EFFORT_FINDING)
        return
    if DEV_WAVE_REASONING_EFFORT_RE.search(sections[0]) is not None:
        findings.append(DEV_WAVE_DW_O16_REASONING_EFFORT_FINDING)


def _check_command_docs_guard(findings: list[str]) -> set[Path]:
    """command/reference の閉包・予算・interface・dispatch を fail-closed 検査する。"""

    unreadable: set[Path] = set()
    command_dir = REPO / ".claude" / "commands"
    if command_dir.is_symlink():
        findings.append(
            ".claude/commands: command directory が symlink — "
            "外部 member を列挙・読取しない"
        )
        actual_commands: set[Path] = set()
    else:
        actual_commands = (
            {path for path in command_dir.glob("*.md")}
            if command_dir.is_dir() else set()
        )
    expected_commands = {REPO / rel for rel in COMMAND_LIMITS}
    extra_commands = sorted(actual_commands - expected_commands)
    missing_commands = sorted(expected_commands - actual_commands)
    for path in extra_commands:
        findings.append(
            f"{path.relative_to(REPO)}: command byte予算が未登録 — "
            "新規commandを黙ってlint対象外にしない"
        )
    for path in missing_commands:
        findings.append(
            f"{path.relative_to(REPO)}: 予算登録済み command が不在 — "
            "interface 検査が蒸発している"
        )
        unreadable.add(path)

    reference_root = REPO / "docs" / "dev-wave"
    actual_references = (
        {
            path for path in reference_root.rglob("*")
            if not path.is_dir() or path.is_symlink()
        }
        if reference_root.is_dir() else set()
    )
    expected_references = {REPO / rel for rel in DEV_WAVE_REFERENCE_FILES}
    extra_references = sorted(actual_references - expected_references)
    missing_references = sorted(expected_references - actual_references)
    for path in extra_references:
        findings.append(
            f"{path.relative_to(REPO)}: docs/dev-wave/** の層予算registry未登録実体 — "
            "規範 detail を4 referenceの閉包外へ逃がしてはならない"
        )
    for path in missing_references:
        findings.append(
            f"{path.relative_to(REPO)}: 登録済み dev-wave reference が不在 — "
            "dispatch が到達不能"
        )
        unreadable.add(path)

    provenance_root = REPO / PROVENANCE_REFERENCE_ROOT
    if provenance_root.is_symlink():
        findings.append(
            "docs/provenance: provenance reference directory が symlink — "
            "外部 member を列挙・読取しない"
        )
        actual_provenance_references: set[Path] = set()
    else:
        actual_provenance_references = (
            {
                path
                for path in provenance_root.rglob("*")
                if not path.is_dir() or path.is_symlink()
            }
            if provenance_root.is_dir()
            else set()
        )
    expected_provenance_references = {
        REPO / rel for rel in PROVENANCE_REFERENCE_LIMITS
    }
    extra_provenance_references = sorted(
        actual_provenance_references - expected_provenance_references
    )
    missing_provenance_references = sorted(
        expected_provenance_references - actual_provenance_references
    )
    for path in extra_provenance_references:
        findings.append(
            f"{path.relative_to(REPO)}: docs/provenance/** の予算未登録実体 — "
            "規範 detail を family 閉包外へ逃がしてはならない"
        )
    for path in missing_provenance_references:
        findings.append(
            f"{path.relative_to(REPO)}: 登録済み provenance reference が不在 — "
            "入口 dispatch が到達不能"
        )
        unreadable.add(path)

    bounded_limits = {
        **COMMAND_LIMITS,
        **SELF_LIMITS,
        **TOOLS_README_LIMITS,
        **PROVENANCE_LIMITS,
        **PROVENANCE_REFERENCE_LIMITS,
    }
    all_text_files: dict[str, TextLimit | None] = {"AGENTS.md": None}
    all_text_files.update(
        {rel: None for rel in DEV_WAVE_REFERENCE_FILES}
    )
    all_text_files.update(bounded_limits)
    decoded: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for rel, limit in all_text_files.items():
        path = REPO / rel
        if path in unreadable:
            continue
        # tools/README.md の不在は後段の _ENUMERATED_DOCS 検査に渡し、
        # living-doc lint が黙って蒸発しないことを同じ経路で可視化する。
        if rel in TOOLS_README_LIMITS and not path.exists():
            continue
        text = _safe_read_text(
            path,
            findings,
            f"{rel}: 文書検査の読取失敗",
            newline="",
            unsafe_path_prefix=(
                f"{rel}: symlink または regular file 以外 — "
                "予算・interface 検査対象として受理しない"
            ),
            invalid_utf8_prefix=(
                f"{rel}: invalid UTF-8 — 文書検査を継続できない"
            ),
        )
        if text is None:
            unreadable.add(path)
            continue
        size = len(text.encode("utf-8"))
        sizes[rel] = size
        if limit is not None and size > limit.max_bytes:
            findings.append(
                f"{rel}: {size} bytes > 予算 {limit.max_bytes} bytes — "
                "安全義務を削らず既存 reference へ統合する。予算増加は独立審査にする"
            )
        decoded[rel] = text
        if limit is not None and limit.max_line_chars is not None:
            for lineno, line in enumerate(text.splitlines(), 1):
                if len(line) > limit.max_line_chars:
                    findings.append(
                        f"{rel}:{lineno}: {len(line)} chars > 最長行予算 "
                        f"{limit.max_line_chars} — 規則を一行へ詰め込まない"
                    )

    if PROVENANCE_FAMILY_FILES.issubset(sizes):
        provenance_size = sum(
            sizes[rel] for rel in PROVENANCE_FAMILY_FILES
        )
        if provenance_size > PROVENANCE_FAMILY_BYTES:
            findings.append(
                "docs/ai-provenance.md + docs/provenance/**: "
                f"合計 {provenance_size} bytes > hard ceiling "
                f"{PROVENANCE_FAMILY_BYTES} bytes"
            )

    dev_wave_text = decoded.get(".claude/commands/dev-wave.md")
    agents_text = decoded.get("AGENTS.md")
    workers_text = decoded.get(_WORKERS)
    operations_text = decoded.get(_OPERATIONS)
    _check_dev_wave_single_dispatch_structure(
        agents_text,
        operations_text,
        findings,
    )
    _check_dev_wave_model_pins(
        dev_wave_text,
        workers_text,
        operations_text,
        findings,
    )
    _check_dev_wave_operations_forbidden_terms(
        operations_text,
        findings,
    )
    _check_dev_wave_waiter_consumer_pins(
        dev_wave_text,
        decoded.get(_CORE),
        operations_text,
        findings,
    )
    if workers_text is not None:
        _check_dev_wave_reasoning_effort_pins(
            workers_text,
            findings,
            operations_text=decoded.get(_OPERATIONS),
        )

    ambiguous_provenance: set[str] = set()
    for rel in sorted(PROVENANCE_FAMILY_FILES):
        text = decoded.get(rel)
        if text is None:
            continue
        ambiguity = _provenance_markdown_ambiguities(text)
        if ambiguity:
            ambiguous_provenance.add(rel)
            findings.append(
                f"{rel}: provenance Markdown の曖昧構文を受理しない — "
                f"{list(ambiguity)}"
            )

    for rel, contract in COMMAND_INTERFACES.items():
        text = decoded.get(rel)
        if text is None:
            continue
        if rel == ".claude/commands/cleanup-branches.md":
            command_body = text
            command_lines = text.splitlines()
            if command_lines and command_lines[0] == "---":
                try:
                    frontmatter_end = command_lines.index("---", 1)
                except ValueError:
                    pass
                else:
                    command_body = "\n".join(command_lines[frontmatter_end + 1:])
            visible_command_body = _visible_dispatch_inventory_text(command_body)
            if not any(
                re.search(r"(?<![0-9A-Za-z])F26(?![0-9A-Za-z])", line)
                and "`docs/failures.md`" in line
                for line in visible_command_body.splitlines()
            ):
                findings.append(
                    f"{rel}: F26 と `docs/failures.md` が同一可視行に共起しない — "
                    "他文書にしか無い義務への到達 edge を失っている"
                )
            _, visible_sections = _visible_h2_section_slices(command_body)
            occupancy_sections = visible_sections.get(
                CLEANUP_OCCUPANCY_SECTION,
                [],
            )
            if (
                len(occupancy_sections) != 1
                or CLEANUP_OCCUPANCY_CONTRACT not in occupancy_sections[0]
            ):
                findings.append(
                    f"{rel}: worktree 占有 checker の必須可視 literal が無い — "
                    f"可視 H2 節 {CLEANUP_OCCUPANCY_SECTION!r} 内の exact 2 行契約が必須"
                )
        parsed = _parse_frontmatter(text)
        if parsed is None:
            findings.append(f"{rel}: frontmatter を一意に解析できない")
            continue
        values, duplicates = parsed
        if duplicates:
            findings.append(
                f"{rel}: frontmatter key 重複: {', '.join(sorted(duplicates))}"
            )
        actual_keys = set(values)
        expected_keys = contract["frontmatter_keys"]
        if actual_keys != expected_keys:
            findings.append(
                f"{rel}: frontmatter key 集合が契約と不一致 — "
                f"actual={sorted(actual_keys)}, expected={sorted(expected_keys)}"
            )
        expected_disable = contract.get("disable-model-invocation")
        if expected_disable is not None and values.get("disable-model-invocation") != expected_disable:
            findings.append(
                f"{rel}: disable-model-invocation は {expected_disable!r} 必須"
            )
        count = text.count("$ARGUMENTS")
        if count != contract["arguments_count"]:
            findings.append(
                f"{rel}: $ARGUMENTS が {count} 件 — "
                f"interface 契約は {contract['arguments_count']} 件"
            )
        if (
            rel != ".claude/commands/dev-wave.md"
            and "docs/skill-self-improvement.md" not in text
        ):
            findings.append(f"{rel}: docs/skill-self-improvement.md への到達性がない")

    for (rel, heading), expected in DEV_WAVE_EXACT_VISIBLE_SECTIONS.items():
        text = decoded.get(rel)
        if text is None:
            continue
        _check_exact_visible_h2_section(
            findings,
            rel=rel,
            text=text,
            heading=heading,
            expected=expected,
        )

    if operations_text is not None:
        operation_order, _ = _visible_h2_section_slices(operations_text)
        operation_positions: dict[str, list[int]] = {
            "DW-O23": [],
            "DW-O25": [],
        }
        for index, title in enumerate(operation_order):
            section_match = re.match(r"[^\s—]+", title)
            if section_match is not None and section_match.group(0) in operation_positions:
                operation_positions[section_match.group(0)].append(index)
        if any(len(positions) != 1 for positions in operation_positions.values()):
            findings.append(
                "docs/dev-wave/operations.md: 可視 H2 の順序 pin 対象が一意でない — "
                f"DW-O23={len(operation_positions['DW-O23'])}, "
                f"DW-O25={len(operation_positions['DW-O25'])}"
            )
        elif operation_positions["DW-O25"][0] <= operation_positions["DW-O23"][0]:
            findings.append(
                "docs/dev-wave/operations.md: 可視 H2 の順序が契約と不一致 — "
                "DW-O25 は DW-O23 より後に置く"
            )

    for rel, sections in REQUIRED_REFERENCE_SECTIONS.items():
        text = decoded.get(rel)
        if text is None:
            continue
        visible_text = _visible_dispatch_inventory_text(text)
        actual_sections = re.findall(
            r"^##\s+([^\s—]+)", visible_text, re.MULTILINE
        )
        for section in sorted(sections):
            count = actual_sections.count(section)
            if count != 1:
                findings.append(
                    f"{rel}: H2 見出し {section} が {count} 件 — "
                    "dispatch先は一意でなければならない"
                )
        orphan_sections = sorted(set(actual_sections) - sections)
        if orphan_sections:
            findings.append(
                f"{rel}: dispatch 契約にない孤児 H2 — {orphan_sections}"
            )
        for literal in CODEX_FIRST_REFERENCE_LITERALS.get(rel, ()):
            if literal not in text:
                findings.append(
                    f"{rel}: Codex-first 実装契約がない — {literal!r}"
                )

    for rel, sections in REQUIRED_PROVENANCE_REFERENCE_SECTIONS.items():
        text = decoded.get(rel)
        if text is None or rel in ambiguous_provenance:
            continue
        visible_text = _visible_markdown_text(text)
        actual_sections = re.findall(
            r"^##\s+([^\s—]+)", visible_text, re.MULTILINE
        )
        for section in sorted(sections):
            count = len(_reference_id_sections(visible_text, section))
            if count != 1:
                findings.append(
                    f"{rel}: H2 見出し {section} が {count} 件 — "
                    "provenance dispatch 先は一意でなければならない"
                )
        orphan_sections = sorted(set(actual_sections) - sections)
        if orphan_sections:
            findings.append(
                f"{rel}: provenance dispatch 契約にない孤児 H2 — "
                f"{orphan_sections}"
            )

    budget_paths = set(PROVENANCE_REFERENCE_LIMITS)
    section_paths = set(REQUIRED_PROVENANCE_REFERENCE_SECTIONS)
    dispatch_paths = {
        path
        for _, pairs in PROVENANCE_DISPATCH_CONTRACT.values()
        for path, _ in pairs
    }
    if not (budget_paths == section_paths == dispatch_paths):
        findings.append(
            "tools/check_docs.py: provenance registry 三面の path 集合が不一致 — "
            f"budget={sorted(budget_paths)}, sections={sorted(section_paths)}, "
            f"dispatch={sorted(dispatch_paths)}"
        )

    registered_pairs = frozenset(
        (rel, section)
        for rel, sections in REQUIRED_PROVENANCE_REFERENCE_SECTIONS.items()
        for section in sections
    )
    pair_owners: dict[tuple[str, str], set[str]] = {}
    for key, (_, pairs) in PROVENANCE_DISPATCH_CONTRACT.items():
        for pair in pairs:
            pair_owners.setdefault(pair, set()).add(key)
    ownership_mismatches = {}
    for pair in set(pair_owners) | set(PROVENANCE_SHARED_DISPATCH_PAIRS):
        owners = frozenset(pair_owners.get(pair, set()))
        expected_owners = PROVENANCE_SHARED_DISPATCH_PAIRS.get(pair)
        if expected_owners is None:
            if len(owners) != 1:
                ownership_mismatches[pair] = {
                    "actual": sorted(owners),
                    "expected": "exactly one key",
                }
        elif owners != expected_owners:
            ownership_mismatches[pair] = {
                "actual": sorted(owners),
                "expected": sorted(expected_owners),
            }
    if ownership_mismatches:
        findings.append(
            "tools/check_docs.py: provenance dispatch pair の key 所有が不一致 — "
            f"{ownership_mismatches}"
        )
    contract_pairs = frozenset(pair_owners)
    if contract_pairs != registered_pairs:
        findings.append(
            "tools/check_docs.py: provenance section registry と "
            "dispatch contract の閉包が不一致 — "
            f"undispatched={sorted(registered_pairs - contract_pairs)}, "
            f"unregistered={sorted(contract_pairs - registered_pairs)}"
        )

    provenance_text = decoded.get(PROVENANCE_ENTRY)
    if (
        provenance_text is not None
        and PROVENANCE_ENTRY not in ambiguous_provenance
    ):
        dispatch = _condition_dispatch_table(
            provenance_text, "条件 dispatch"
        )
        if dispatch is None:
            findings.append(
                "docs/ai-provenance.md: 条件 dispatch 表を一意に抽出できない"
            )
        elif dispatch.structure_errors:
            findings.append(
                "docs/ai-provenance.md: provenance 条件 dispatch 表の構造が不一致 — "
                f"{list(dispatch.structure_errors)}"
            )
        else:
            for key in sorted(
                set(PROVENANCE_DISPATCH_CONTRACT) | set(dispatch.rows)
            ):
                expected_contract = PROVENANCE_DISPATCH_CONTRACT.get(key)
                expected_condition = (
                    expected_contract[0] if expected_contract is not None else None
                )
                expected_pairs = (
                    expected_contract[1] if expected_contract is not None else frozenset()
                )
                actual_pairs = dispatch.rows.get(key, set())
                actual_conditions = dispatch.conditions.get(key, set())
                row_count = dispatch.row_counts.get(key, 0)
                column_counts = dispatch.column_counts.get(key, set())
                leaked_tokens = dispatch.leaked_tokens.get(key, set())
                outside_paths = dispatch.paths.get(key, set()) - budget_paths
                if row_count != 1:
                    findings.append(
                        "docs/ai-provenance.md: provenance 条件 dispatch "
                        f"{key!r} の row count が不一致 — "
                        f"actual={row_count}, expected=1"
                    )
                    continue
                if column_counts != {3}:
                    findings.append(
                        "docs/ai-provenance.md: provenance 条件 dispatch "
                        f"{key!r} の列数が不一致 — "
                        f"actual={sorted(column_counts)}, expected=[3]"
                    )
                if actual_conditions != {expected_condition}:
                    findings.append(
                        "docs/ai-provenance.md: provenance 条件 dispatch "
                        f"{key!r} の発火条件が不一致 — "
                        f"actual={sorted(actual_conditions)!r}, "
                        f"expected={[expected_condition]!r}"
                    )
                if actual_pairs != expected_pairs:
                    findings.append(
                        "docs/ai-provenance.md: provenance 条件 dispatch "
                        f"{key!r} の参照集合が不一致 — "
                        f"missing={sorted(expected_pairs - actual_pairs)}, "
                        f"extra={sorted(actual_pairs - expected_pairs)}"
                    )
                if leaked_tokens:
                    findings.append(
                        "docs/ai-provenance.md: diagnostic sensitivity — "
                        f"provenance 条件 dispatch {key!r} の条件セルに "
                        f"reference token={sorted(leaked_tokens)}"
                    )
                if outside_paths:
                    findings.append(
                        "docs/ai-provenance.md: diagnostic sensitivity — "
                        f"provenance 条件 dispatch {key!r} の第3列に "
                        f"registry 外 path={sorted(outside_paths)}"
                    )

    core_text = decoded.get(_CORE)
    if core_text is not None:
        s09 = _reference_id_sections(core_text, "DW-S09")
        if len(s09) == 1:
            literal_count = s09[0].count(DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL)
            acceptance_order_count = s09[0].count(
                DEV_WAVE_S09_ACCEPTANCE_ORDER_LITERAL
            )
            section_path_count = s09[0].count(DEV_WAVE_LAND_HELPER)
            outside_path_count = (
                core_text.count(DEV_WAVE_LAND_HELPER) - section_path_count
            )
            if (
                literal_count != 1
                or section_path_count != 1
                or outside_path_count != 0
            ):
                findings.append(
                    "docs/dev-wave/core.md: DW-S09 の helper 唯一経路 literal "
                    f"が literal={literal_count}, path-section内={section_path_count}, "
                    f"path-section外={outside_path_count} 件"
                )
            if acceptance_order_count != 1:
                findings.append(
                    "docs/dev-wave/core.md: DW-S09 の acceptance/O23 順序 literal "
                    f"が {acceptance_order_count} 件"
                )

    if operations_text is not None:
        o23 = _reference_id_sections(operations_text, "DW-O23")
        o23_count = (
            o23[0].count(DEV_WAVE_LAND_HELPER)
            if len(o23) == 1 else 0
        )
        total_count = operations_text.count(DEV_WAVE_LAND_HELPER)
        if len(o23) == 1 and (o23_count != 1 or total_count != 1):
            findings.append(
                "docs/dev-wave/operations.md: land helper path は全体で exact 1 件かつ "
                f"DW-O23 内だけ — total={total_count}, O23={o23_count}"
            )
    for rel, text in decoded.items():
        if (
            rel not in {_CORE, _OPERATIONS}
            and DEV_WAVE_LAND_HELPER in text
        ):
            findings.append(
                f"{rel}: land helper path は DW-S09 / DW-O23 だけに置く"
            )

    self_text = decoded.get("docs/skill-self-improvement.md")
    if self_text is not None:
        for level, headings in REQUIRED_SELF_HEADINGS.items():
            actual_headings = re.findall(
                rf"^{'#' * level}\s+(.+?)\s*$",
                self_text,
                re.MULTILINE,
            )
            for heading in sorted(headings):
                count = actual_headings.count(heading)
                if count != 1:
                    findings.append(
                        f"docs/skill-self-improvement.md: H{level} 見出し "
                        f"{heading!r} が {count} 件"
                    )
            orphan_headings = sorted(set(actual_headings) - headings)
            if orphan_headings:
                findings.append(
                    "docs/skill-self-improvement.md: "
                    f"dispatch 契約にない孤児 H{level} — {orphan_headings}"
                )

    if dev_wave_text is not None:
        dispatch = _dispatch_tables(dev_wave_text)
        if dispatch is None:
            findings.append(
                ".claude/commands/dev-wave.md: 段/条件 dispatch 表を一意に抽出できない"
            )
        else:
            dispatch_findings_start = len(findings)
            if dispatch.structure_errors:
                findings.append(
                    ".claude/commands/dev-wave.md: 段/条件 dispatch 表の構造が不一致 — "
                    f"{list(dispatch.structure_errors)}"
                )
            for mode, expected_map, actual_map in (
                (
                    "U",
                    STAGE_UNCONDITIONAL_DISPATCH_CONTRACT,
                    dispatch.stage_unconditional,
                ),
                (
                    "C",
                    STAGE_CONDITIONAL_DISPATCH_CONTRACT,
                    dispatch.stage_conditional,
                ),
            ):
                for key in sorted(set(expected_map) | set(actual_map)):
                    expected = expected_map.get(key, frozenset())
                    actual = actual_map.get(key, set())
                    if actual == expected:
                        continue
                    findings.append(
                        ".claude/commands/dev-wave.md: "
                        f"段 dispatch {key!r} の {mode} edge が契約と不一致 — "
                        f"missing={sorted(expected - actual)}, "
                        f"extra={sorted(actual - expected)}"
                    )
            for key in sorted(
                set(CONDITION_DISPATCH_CONTRACT)
                | set(CONDITION_TRIGGER_CONTRACT)
                | set(dispatch.conditions)
                | set(dispatch.condition_triggers)
                | set(dispatch.condition_leaked_tokens)
            ):
                expected = CONDITION_DISPATCH_CONTRACT.get(key, frozenset())
                actual = dispatch.conditions.get(key, set())
                row_count = dispatch.condition_row_counts.get(key, 0)
                actual_triggers = dispatch.condition_triggers.get(key, set())
                expected_trigger = CONDITION_TRIGGER_CONTRACT.get(key)
                if (
                    actual != expected
                    or row_count != 1
                    or actual_triggers != {expected_trigger}
                ):
                    findings.append(
                        ".claude/commands/dev-wave.md: "
                        f"条件 dispatch {key!r} が契約と不一致 — "
                        f"rows={row_count}, "
                        f"triggers={sorted(actual_triggers)!r}, "
                        f"missing={sorted(expected - actual)}, "
                        f"extra={sorted(actual - expected)}"
                    )
                leaked = dispatch.condition_leaked_tokens.get(key, set())
                if leaked:
                    findings.append(
                        ".claude/commands/dev-wave.md: diagnostic sensitivity — "
                        f"条件 dispatch {key!r} の条件セルに "
                        f"reference token={sorted(leaked)}"
                    )
            condition_18_row_count = dispatch.condition_row_counts.get("18", 0)
            condition_18_triggers = dispatch.condition_triggers.get("18", set())
            if condition_18_row_count == 1:
                condition_18_trigger = next(iter(condition_18_triggers), "")
                if not (
                    CONDITION_18_RUN_POINT_LITERAL in condition_18_trigger
                    and CONDITION_18_RED_POINT_LITERAL in condition_18_trigger
                ):
                    findings.append(
                        ".claude/commands/dev-wave.md: 条件 dispatch '18' の trigger に "
                        "テスト・受入前と赤処理前が必要"
                    )
            disallowed = sorted(
                dispatch.paths - NORMATIVE_DISPATCH_ALLOWLIST
            )
            if disallowed:
                findings.append(
                    ".claude/commands/dev-wave.md: 規範 dispatch の参照先が allowlist 外 — "
                    f"{disallowed}"
                )
            registered_pairs = {
                (path, section)
                for path, sections in REQUIRED_REFERENCE_SECTIONS.items()
                for section in sections
            }
            dispatched_reference_pairs = {
                (path, section)
                for _, _, path, section in dispatch.edges
                if path in DEV_WAVE_REFERENCE_FILES
            }
            if dispatched_reference_pairs != registered_pairs:
                findings.append(
                    "tools/check_docs.py: dev-wave registry と typed edge の閉包が不一致 — "
                    f"undispatched={sorted(registered_pairs - dispatched_reference_pairs)}, "
                    f"unregistered={sorted(dispatched_reference_pairs - registered_pairs)}"
                )
            if (
                len(findings) == dispatch_findings_start
                and DEV_WAVE_REFERENCE_FILES <= set(decoded)
                and _dev_wave_visible_inventory_is_exact(decoded)
            ):
                _check_dev_wave_layer_budget(findings, decoded, dispatch.edges)
        if D2_ROLLBACK_STRUCTURE.search(dev_wave_text) is None:
            findings.append(
                ".claude/commands/dev-wave.md: D2 巻き戻し構造 "
                "(O08/O09/O10→段1、O13→段2、invalidate) がない"
            )
        if D4_FIX_INHERITANCE_STRUCTURE.search(dev_wave_text) is None:
            findings.append(
                ".claude/commands/dev-wave.md: D4 fix 子の段5全文継承・"
                "成立Oxx直前読了構造がない"
            )
        if CODEX_AUTHORING_STRUCTURE.search(dev_wave_text) is None:
            findings.append(
                ".claude/commands/dev-wave.md: Codex-first 実装境界 "
                "(実装面・軽量版・role=author・親直接編集禁止) がない"
            )
        for pattern, label_text in (
            (ALTERNATE_LAND_HELPER_COMMAND, "alternate land helper command"),
            (DIRECT_MAIN_FF_COMMAND, "direct git merge --ff-only main mutation"),
        ):
            if pattern.search(dev_wave_text):
                findings.append(
                    ".claude/commands/dev-wave.md: 共通 land 契約外の実行経路 — "
                    f"{label_text}"
                )

    _check_codex_skill_guard(
        findings,
        skill_name="dev-wave",
        limits=CODEX_DEV_WAVE_SKILL_LIMITS,
        expected_files=CODEX_DEV_WAVE_SKILL_FILES,
        literals=CODEX_DEV_WAVE_SKILL_LITERALS,
        openai_yaml=CODEX_DEV_WAVE_OPENAI_YAML,
        expected_description=CODEX_DEV_WAVE_DESCRIPTION,
        forbidden_literals=(DEV_WAVE_LAND_HELPER,),
        exact_literals=(CODEX_DEV_WAVE_STAGE9_LAND_LITERAL,),
        exact_visible_sections={
            "開始する": CODEX_DEV_WAVE_START_SECTION_LITERAL,
        },
        forbidden_patterns=(
            (ALTERNATE_LAND_HELPER_COMMAND, "alternate land helper command"),
            (DIRECT_MAIN_FF_COMMAND, "direct git merge --ff-only main mutation"),
        ),
    )
    _check_codex_skill_guard(
        findings,
        skill_name="rulings",
        limits=CODEX_RULINGS_SKILL_LIMITS,
        expected_files=CODEX_RULINGS_SKILL_FILES,
        literals=CODEX_RULINGS_SKILL_LITERALS,
        openai_yaml=CODEX_RULINGS_OPENAI_YAML,
    )
    _check_codex_skill_guard(
        findings,
        skill_name="next-tasks",
        limits=CODEX_NEXT_TASKS_SKILL_LIMITS,
        expected_files=CODEX_NEXT_TASKS_SKILL_FILES,
        literals=CODEX_NEXT_TASKS_SKILL_LITERALS,
        openai_yaml=CODEX_NEXT_TASKS_OPENAI_YAML,
    )
    _check_codex_skill_guard(
        findings,
        skill_name="cleanup-branches",
        limits=CODEX_CLEANUP_BRANCHES_SKILL_LIMITS,
        expected_files=CODEX_CLEANUP_BRANCHES_SKILL_FILES,
        literals=(),
        openai_yaml=CODEX_CLEANUP_BRANCHES_OPENAI_YAML,
        expected_description=CODEX_CLEANUP_BRANCHES_DESCRIPTION,
        expected_sha256=CODEX_CLEANUP_BRANCHES_SKILL_SHA256,
    )

    cleanup_text = decoded.get(".claude/commands/cleanup-branches.md")
    if (
        cleanup_text is not None
        and hashlib.sha256(cleanup_text.encode("utf-8")).hexdigest()
        != CLEANUP_COMMAND_SHA256
    ):
        findings.append(
            ".claude/commands/cleanup-branches.md: "
            "whole-file SHA-256 が契約と不一致"
        )

    return unreadable


def _handoff_schema_warnings(lines: list[str]) -> list[str]:
    """handoff の 4 行ヘッダ書式・状態語彙・基準コミット形を非阻害の warning として検査する。

    land はもう書式を検査しない (書式を執行していた `_validate_handoff_at` は削除済み)。
    書式検査はここが唯一の可視化経路であり、阻害力は持たない。ここでは最初の違反で
    打ち切らず「4 行ヘッダが書式通りか」を先に判定し、書式が崩れていれば個々の
    フィールドは信頼できないため以降の検査は行わない (誤検出の temptation を避ける)。
    書式が保たれていれば状態語彙・基準コミット形は独立に検査する。
    """
    msgs: list[str] = []
    header = lines[1:5]
    if len(header) < 4 or any(
        not line.startswith(prefix)
        for line, prefix in zip(header, _HANDOFF_HEADER_PREFIXES)
    ):
        msgs.append(
            "4 行ヘッダ (- 目的: / - 状態: / - 最終更新: / - 基準コミット:) の書式が "
            "handoff/README.md の定型と一致しない (警告のみ、rc には算入しない)"
        )
        return msgs

    state = header[1].removeprefix("- 状態: ").strip()
    if state not in _HANDOFF_STATES:
        msgs.append(
            f"状態の値 {state!r} が既知の 3 値 (作業中/計測中/中断) のいずれでもない "
            "(警告のみ、rc には算入しない)"
        )

    base_field = header[3].removeprefix("- 基準コミット: ").strip()
    base = base_field.split(maxsplit=1)[0] if base_field else ""
    if _HANDOFF_SHA_RE.fullmatch(base) is None:
        msgs.append(
            f"基準コミット {base!r} が 40 桁または 64 桁の hex ではない "
            "(警告のみ、rc には算入しない)"
        )

    return msgs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="docs の一貫性 lint")
    parser.add_argument(
        "--expect-active-transaction",
        metavar="ID",
        help="land 中に限り、complete な active fold transaction の exact ID を宣言する",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """1 回の検査内だけ読取結果を共有し、終了時に必ず破棄する。"""

    cache_token = _READ_TEXT_CACHE.set({})
    try:
        return _main(argv)
    finally:
        _READ_TEXT_CACHE.reset(cache_token)


def _main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(()) if argv is None else _parser().parse_args(argv)
    findings: list[str] = []
    warnings: list[str] = []

    guard_unreadable = _check_command_docs_guard(findings)
    _check_spool_guard(
        findings,
        expected_transaction_id=args.expect_active_transaction,
    )

    current_pin = _current_pin(findings)
    if current_pin is None:
        findings.append(
            "tools/check_docs.py: pin.CURRENT_PIN を抽出できない (pin.py 不在か形式変更) — "
            "pin literal 検査が蒸発している。_current_pin() を実体に追従させること"
        )

    _check_dispatch_inventory(findings)
    _check_pegasus_admission_docs(findings)

    # decisions.md の D 見出し重複 (grep index の壊れ)
    decisions_text = _safe_read_text(
        REPO / "docs" / "decisions.md",
        findings,
        "docs/decisions.md: D 見出し検査の読取失敗 — "
        "D 見出し重複検査と living docs の D 参照実在性検査を停止",
    )
    d_heads = (
        [match.group("number") for match in DECISION_ID_RE.finditer(decisions_text)]
        if decisions_text is not None
        else []
    )
    if decisions_text is not None:
        for match in DECISION_HEADING_CANDIDATE_RE.finditer(decisions_text):
            if DECISION_ID_RE.match(match.group(0)) is None:
                findings.append(
                    "docs/decisions.md: canonical D 見出しは "
                    f"`## D{match.group('number')}.` で始める"
                )
    dups = {n for n in d_heads if d_heads.count(n) > 1}
    for n in sorted(dups, key=int):
        findings.append(f"docs/decisions.md: D{n} の見出しが重複 — grep index が壊れる")
    known_d = {int(n) for n in d_heads} if decisions_text is not None else None
    _check_n_pilot_role_decision_pin(
        findings,
        decisions_text=decisions_text,
    )

    phase3_text: str | None | object = _UNREAD
    for doc in LIVING_DOCS:
        if doc in guard_unreadable:
            continue
        if not doc.exists():
            # 手書き列挙対象の不在 = 違反 (改名/削除で検査が黙って蒸発するのを封じる)。
            # glob 由来の動的分は実在物だけなので、不在があっても無視 (発生しえない)。
            if doc in _ENUMERATED_DOCS:
                findings.append(
                    f"{doc.relative_to(REPO)}: LIVING_DOCS の列挙対象が不在 — 改名/削除で "
                    "lint が黙って蒸発する。列挙を実体に追従させるか、凍結した族なら LIVING_DOCS から外す"
                )
            continue
        rel = doc.relative_to(REPO)
        failure_prefix = f"{rel}: living docs 検査の読取失敗"
        if doc == PHASE3:
            failure_prefix += (
                " — 見送り台帳に依存する worklog 遷移検査を停止"
            )
        doc_text = _safe_read_text(
            doc,
            findings,
            failure_prefix,
        )
        if doc == PHASE3:
            phase3_text = doc_text
        if doc_text is None:
            continue
        for lineno, line in enumerate(doc_text.splitlines(), 1):
            for pat in LINE_REF_STRICT:
                m = pat.search(line)
                if m:
                    findings.append(
                        f"{rel}:{lineno}: docs の行番号参照 (腐敗する): {m.group(0)!r} → 節名参照に直す"
                    )
            # 現況主張の正本は CLAUDE.md「現在地」のポインタのみ
            if doc.name != "CLAUDE.md" and re.search(r"現在は\s*Phase", line):
                findings.append(
                    f"{rel}:{lineno}: 現況主張の再掲 (正本は CLAUDE.md 現在地 → worklog 末尾)"
                )
            # 「次 = 」形式の次アクション主張は worklog 末尾 (次の一手) だけが持つ
            if doc.name in ("CLAUDE.md", "roadmap.md") and re.search(r"次\s*=", line):
                findings.append(
                    f"{rel}:{lineno}: 次アクションの再掲 (正本は worklog 末尾の「次の一手」)"
                )
            # pin.CURRENT_PIN の値 literal 再掲 (pin 前進で黙って腐る。2026-07-12 監査)
            if current_pin and current_pin in line:
                findings.append(
                    f"{rel}:{lineno}: pin.CURRENT_PIN の値 {current_pin!r} の literal 再掲 — "
                    "`pin.CURRENT_PIN` への記号参照に直す (値の正本は pin.py)"
                )
            # 実在しない D 番号への参照 (decisions.md の見出しが正)
            if known_d is not None:
                for m in D_REF.finditer(line):
                    if int(m.group(1)) not in known_d:
                        findings.append(
                            f"{rel}:{lineno}: 実在しない D 参照: {m.group(0)!r} "
                            "(decisions.md に見出しなし)"
                        )
            # 実在しないファイルパスへの参照 (改名・移動の腐敗検出)。
            # ccbench-anatomy.md は冒頭宣言どおり external/ccbench/ 相対パスも許容
            for m in PATH_REF.finditer(line):
                p = m.group(0)
                if (REPO / p).exists():
                    continue
                if doc.name == "ccbench-anatomy.md" and (REPO / "external" / "ccbench" / p).exists():
                    continue
                findings.append(f"{rel}:{lineno}: 実在しないパス参照: {p!r}")

    placeholder_unreadable = _check_literal_placeholder_guard(findings)
    backlog_result = _check_backlog_guard(
        findings,
        previously_unreadable=placeholder_unreadable,
        phase3_text=phase3_text,
    )

    archive_readme_text: str | None = None
    if not ARCHIVE_README.exists():
        findings.append(
            "docs/archive/README.md: ファイルが不在 — archive の索引を検査できない"
        )
    elif ARCHIVE_README.is_symlink() or not ARCHIVE_README.is_file():
        findings.append(
            "docs/archive/README.md: regular file でない — archive の索引を検査できない"
        )
    else:
        archive_readme_text = _safe_read_text(
            ARCHIVE_README,
            findings,
            "docs/archive/README.md: archive 索引の読取失敗",
        )

    if archive_readme_text is not None:
        archive_section = re.search(
            r"^## 現在の収容物\s*$\n(?P<body>.*?)(?=^## |\Z)",
            archive_readme_text,
            re.MULTILINE | re.DOTALL,
        )
        if archive_section is None:
            findings.append(
                "docs/archive/README.md: 「現在の収容物」節がない — "
                "archive の索引を検査できない"
            )
            archive_section = None
    else:
        archive_section = None

    if archive_readme_text is not None and archive_section is not None:
        _validate_archive_readme_claims(
            archive_readme_text,
            archive_section.group("body"),
            archive_section.start("body"),
            backlog_result,
            findings,
        )
        # 到達性 = archive の実在物を README の索引から辿れること。git-history-only の墓標は
        # working tree に実在しないことが契約なので、索引から実在物への逆方向検査を免除する。
        for archived in sorted(ARCHIVE_DIR.iterdir()):
            if archived.is_file() and archived.name != ARCHIVE_README.name:
                if archived.name not in archive_readme_text:
                    findings.append(
                        f"docs/archive/README.md: {archived.name} が索引 (現在の収容物) に未掲載 — "
                        "到達性がない (追記するか規約に従い墓標行を書く)"
                    )
        for line in archive_section.group("body").splitlines():
            if not line.startswith("- ") or "git-history-only" in line:
                continue
            for name in re.findall(r"`([^`/]+\.(?:md|json))`", line):
                if not (ARCHIVE_DIR / name).is_file():
                    findings.append(
                        f"docs/archive/README.md: {name} が索引 (現在の収容物) に掲載されているが "
                        "docs/archive/ に実在しない (削除済みなら git-history-only の墓標行にする)"
                    )

    wl_size = (
        WORKLOG.lstat().st_size
        if WORKLOG.exists() and not WORKLOG.is_symlink() and WORKLOG.is_file()
        else 0
    )
    if wl_size > WORKLOG_ROTATE_BYTES:
        findings.append(
            f"docs/worklog.md: {wl_size // 1000}KB > 閾値 {WORKLOG_ROTATE_BYTES // 1000}KB — "
            "肥大。過去分を docs/archive/worklog-<範囲>.md へローテーションする "
            "(手順の正本は worklog.md 冒頭のローテーション節)"
        )

    if HANDOFF_DIR.exists():
        now = time.time()
        for f in sorted(HANDOFF_DIR.glob("*.md")):
            if f.name == "README.md":
                continue
            rel = f.relative_to(REPO)
            text = _safe_read_text(
                f,
                findings,
                f"{rel}: handoff 検査の読取失敗",
            )
            if text is None:
                continue
            # 行数上限は撤廃 (2026-07-11 ユーザー指示: 手戻り防止が読み込みコストに優先。
            # 正本 = handoff/README.md 運用ルール)
            status_line = next((l for l in text.splitlines() if "状態:" in l), None)
            if status_line is None:
                findings.append(f"{rel}: ヘッダ定型 (状態:) がない — handoff/README.md の定型に従う")
            elif re.search(r"作業中|計測中", status_line) and now - f.stat().st_mtime > HANDOFF_STALE_SECONDS:
                warnings.append(
                    f"{rel}: 状態が稼働中のまま 48h 以上未更新 — 死んだセッションの可能性。中断扱いで回収を"
                )
            for msg in _handoff_schema_warnings(text.splitlines()):
                warnings.append(f"{rel}: {msg}")

    if warnings:
        print(f"check_docs: {len(warnings)} 件の警告 (rc には算入しない)")
        for w in warnings:
            print("  -", w)

    if findings:
        print(f"check_docs: {len(findings)} 件の違反")
        for f in findings:
            print("  -", f)
        return 1
    print("check_docs: 違反なし")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
