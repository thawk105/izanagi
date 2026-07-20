#!/usr/bin/env python3
"""docs の一貫性 lint — 2026-07-05 の文書恒久対応で導入。

背景: 2026-07-04 の文書一貫性監査で確定矛盾 39 件。根本原因の大半は
「可変状態 (完了状況・現在 Phase・次の一手) の再掲」と「行番号参照の腐敗」。
このスクリプトは禁止パターンを機械的に検出する決定的な lint であり、
規律の防壁 (hooks/) ではない。意味的なずれ (チェックボックス反映漏れ等) は
検出できない — それは D27 の敵対監査の領分。

使い方: python3 tools/check_docs.py   (セッション締めの手順で実行。違反あり = exit 1)
"""
from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# living docs = 現在の状態・設計を主張する文書。ここに可変状態の再掲と行番号参照を禁止する。
# 対象外 = 追記型の日誌・記録 (書いた時点で凍結): worklog / decisions / insights / paper-story /
# docs/archive/ 配下 (監査台帳・worklog アーカイブ等の凍結族。規約は同 README — ファイル名不変で移動)、
# および完了 Phase の phase1/phase2 (2026-07-05 に冒頭へ凍結宣言済み)。
LIVING_DOCS = [
    REPO / "README.md",                         # リポジトリ入口 (現況主張・パス参照を持つ生きた文書)
    REPO / "AGENTS.md",                         # Codex 用の共有規律入口
    REPO / "CLAUDE.md",
    REPO / ".codex" / "agents" / "README.md", # Codex runtime adapter の生きた運用文書
    REPO / "output" / "README.md",              # 成果物 namespace の生きた地図
    REPO / "output" / "task-runs" / "README.md",  # 開発観測台帳の生きた運用正本
    REPO / "docs" / "README.md",                  # docs の地図 (2026-07-11 fc-05 で CLAUDE.md から委譲)
    REPO / "docs" / "ai-provenance.md",           # commit provenance の共有規約
    REPO / "docs" / "roadmap.md",
    REPO / "docs" / "related-work" / "README.md",  # 旧 related-work.md はディレクトリ化 (2026-07-11 監査 lint-04 で修正 — 旧パスは黙って skip されていた)
    REPO / "docs" / "phase3.md",                  # 現行 phase doc。Phase 移行時にここを差し替え、旧 doc は凍結宣言
    REPO / "docs" / "phase3-main-experiment.md",  # 事前登録 (サンプル設計数値の確定追記が残るため living)
    REPO / "docs" / "phase3-8b-descriptor-design.md",  # 段 8b の実走前凍結設計 (draft の間は living)
    REPO / "docs" / "glossary.md",
    REPO / "docs" / "agent-architecture.md",
    REPO / "docs" / "orchestrator-design.md",
    REPO / "docs" / "ccbench-anatomy.md",
    REPO / "docs" / "axis-onboarding.md",              # 2026-07-11 監査 dup-05 で追加
    REPO / "docs" / "isolation-phenomena.md",          # 2026-07-12 監査: 現在形の生きた参照文書なのに lint 網の外だった
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
_OWN = r"(?:CLAUDE|README|roadmap|phase\d[\w-]*|decisions|worklog[\w-]*|agent-architecture|orchestrator-design|ccbench-anatomy|paper-story[\w-]*|audit[\w-]*|isolation-phenomena|glossary|related-work)"
LINE_REF_STRICT = [
    re.compile(_OWN + r"\.md:\d+"),
    re.compile(_OWN + r"\.md\s*の?\s*\d+\s*行"),
    re.compile(r"line\s*\d+\s*参照", re.IGNORECASE),
]

HANDOFF_DIR = REPO / "docs" / "handoff"
HANDOFF_STALE_SECONDS = 48 * 3600

ARCHIVE_DIR = REPO / "docs" / "archive"
ARCHIVE_README = ARCHIVE_DIR / "README.md"

# --- worklog 肥大 (2026-07-15 追加、トークン節約メンテ) ---
# ブート時「末尾エントリのみ読む」運用でも、肥大は grep 誤爆・事故全読・コンテキスト
# 圧迫の温床になる (2026-07-05 のローテ後、Phase 3 分だけで 224KB まで再肥大した実績)。
# 閾値超過 = ローテーションの合図 (手順の正本は worklog.md 冒頭)。
WORKLOG = REPO / "docs" / "worklog.md"
WORKLOG_ROTATE_BYTES = 100_000
PHASE3 = REPO / "docs" / "phase3.md"

# --- 「次の一手」ID 保存則 (D69) ---
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
    r"\d{4}-\d{2}-\d{2} \([1-9][0-9]*\) — .+"
)
ARCHIVE_WORKLOG_ENTRY_TITLE_RE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?: \((?P<order>[1-9][0-9]*|続き[0-9]*)\))? — .+"
)
NEXT_ACTION_RE = re.compile(
    r"^### 次の一手(?:[ \t][^\n]*)?$\n?(?P<body>.*?)(?=^###[ \t]|^##[ \t]|\Z)",
    re.MULTILINE | re.DOTALL,
)
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

# --- 参照実在性 (2026-07-11 追加、docs 整備) ---
# living docs 中の「実在しない D 番号」「実在しないファイルパス」への参照 = 腐敗。
# 凍結族 (worklog/decisions/insights/archive) は対象外 — 書いた時点で正しければよい。
D_REF = re.compile(r"\bD(\d{1,3})\b")
# パスは既知のトップディレクトリ始まりに限定 (submodule 内 cc/ 等は pin 固定で腐らないので対象外)。
# プレースホルダ (<日付> 等)・glob (*) は文字クラス外なのでマッチが切れ、拡張子必須で自然に除外される。
# 負の後読み: external/ccbench/docs/... のような長いパスの途中を docs/... と誤マッチしない
PATH_REF = re.compile(r"(?<![\w/])(?:docs|tools|orchestrator|hooks|patches|output|src|\.claude|\.codex)/[\w.\-/]+\.[A-Za-z0-9]+")


def _current_pin() -> str | None:
    """pin.CURRENT_PIN の現在値を pin.py から抽出する (import せず正規表現 — 単体スクリプトのため)。

    living docs にこの値の literal が書かれると pin 前進で黙って腐る (2026-07-12 監査:
    runbook のゲート行が該当)。値の正本は pin.py であり、docs は `pin.CURRENT_PIN` への
    記号参照で書く。抽出に失敗したら None を返し、main が違反として可視化する
    (黙って skip すると検査自体が蒸発する — tests/README.md の疑似スキップ禁止と同系)。
    """
    pin_py = REPO / "orchestrator" / "campaign" / "pin.py"
    if not pin_py.exists():
        return None
    m = re.search(r'^CURRENT_PIN\s*=\s*"([0-9a-f]{7,40})"', pin_py.read_text(), re.MULTILINE)
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


def _top_level_items(body: str) -> list[tuple[str, int]]:
    """code fence / HTML comment 外にあるトップレベル項目と offset を返す。"""

    items: list[tuple[str, int]] = []
    in_comment = False
    fence: tuple[str, int] | None = None
    offset = 0
    for raw_line in body.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        if fence is not None:
            marker_char, marker_len = fence
            stripped = line.lstrip(" \t")
            indent = len(line) - len(stripped)
            if indent <= 3 and re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*", stripped
            ):
                fence = None
            offset += len(raw_line)
            continue

        # fence opener の info string 内にある `<!--` は comment 開始ではない。
        # comment 継続中でない行は opener を先に判定する。
        if not in_comment:
            fence_match = FENCE_OPEN_RE.fullmatch(line)
            if fence_match is not None:
                marker = fence_match.group("marker")
                fence = (marker[0], len(marker))
                offset += len(raw_line)
                continue

        visible, in_comment = _mask_html_comments(line, in_comment)
        fence_match = FENCE_OPEN_RE.fullmatch(visible)
        if fence_match is not None:
            marker = fence_match.group("marker")
            fence = (marker[0], len(marker))
            offset += len(raw_line)
            continue

        item = TOP_LEVEL_ITEM_RE.fullmatch(visible)
        if item is not None:
            items.append((item.group("text"), offset))
        offset += len(raw_line)
    return items


def _top_level_ids(body: str) -> list[str]:
    """トップレベル list item の先頭にある有効 ID だけを返す。"""

    ids: list[str] = []
    for item_text, _ in _top_level_items(body):
        match = TASK_ID_AT_HEAD_RE.match(item_text)
        if match:
            ids.append(match.group("id"))
    return ids


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


def _check_backlog_guard(findings: list[str]) -> None:
    """worklog の次アクション保存則と見送り台帳の ID 構造を検査する。"""

    worklog_text: str | None = None
    phase3_text: str | None = None
    if not WORKLOG.exists():
        findings.append("docs/worklog.md: ファイルが不在 — 次の一手の保存則を検査できない")
    else:
        worklog_text = WORKLOG.read_text()
    if not PHASE3.exists():
        findings.append("docs/phase3.md: ファイルが不在 — 見送り台帳 sink を検査できない")
    else:
        phase3_text = PHASE3.read_text()

    ledger_ids: set[str] = set()
    if phase3_text is not None:
        ledger = _extract_deferred_ledger(phase3_text, findings)
        if ledger is not None:
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
        return
    entries = _extract_current_entries(worklog_text, findings)
    if entries is None:
        return

    next_actions: list[tuple[str, int] | None] = [
        _extract_next_action("docs/worklog.md", worklog_text, entry, findings)
        for entry in entries
    ]
    sources = [set(_top_level_ids(section[0])) if section is not None else set()
               for section in next_actions]
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

    def check_transition(
        source_entry: tuple[str, str, int],
        source_ids: set[str],
        sink_entry: tuple[str, str, int],
        source_rel: str,
    ) -> None:
        if not source_ids:
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
    for archive_path in sorted(ARCHIVE_DIR.glob("worklog-*.md"), key=lambda path: path.name):
        archive_text = archive_path.read_text()
        archive_entries = _extract_archive_entries(archive_path, archive_text, findings)
        if archive_entries is None:
            continue

        archive_rel = str(archive_path.relative_to(REPO))
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
            if entry_has_id and section is not None:
                _validate_next_action_items(
                    archive_rel, archive_text, entry, section, findings
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

    if archive_worklogs and not ambiguous_order:
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


def main() -> int:
    findings: list[str] = []

    current_pin = _current_pin()
    if current_pin is None:
        findings.append(
            "tools/check_docs.py: pin.CURRENT_PIN を抽出できない (pin.py 不在か形式変更) — "
            "pin literal 検査が蒸発している。_current_pin() を実体に追従させること"
        )

    # decisions.md の D 見出し重複 (grep index の壊れ)
    d_heads = re.findall(
        r"^## D(\d+)\b", (REPO / "docs" / "decisions.md").read_text(), re.MULTILINE
    )
    dups = {n for n in d_heads if d_heads.count(n) > 1}
    for n in sorted(dups, key=int):
        findings.append(f"docs/decisions.md: D{n} の見出しが重複 — grep index が壊れる")
    known_d = {int(n) for n in d_heads}

    for doc in LIVING_DOCS:
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
        for lineno, line in enumerate(doc.read_text().splitlines(), 1):
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
            for m in D_REF.finditer(line):
                if int(m.group(1)) not in known_d:
                    findings.append(
                        f"{rel}:{lineno}: 実在しない D 参照: {m.group(0)!r} (decisions.md に見出しなし)"
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

    _check_backlog_guard(findings)

    archive_readme_text = ARCHIVE_README.read_text()
    archive_section = re.search(
        r"^## 現在の収容物\s*$\n(?P<body>.*?)(?=^## |\Z)",
        archive_readme_text,
        re.MULTILINE | re.DOTALL,
    )
    if archive_section is None:
        findings.append("docs/archive/README.md: 「現在の収容物」節がない — archive の索引を検査できない")
    else:
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

    wl_size = WORKLOG.stat().st_size if WORKLOG.exists() else 0
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
            text = f.read_text()
            # 行数上限は撤廃 (2026-07-11 ユーザー指示: 手戻り防止が読み込みコストに優先。
            # 正本 = handoff/README.md 運用ルール)
            status_line = next((l for l in text.splitlines() if "状態:" in l), None)
            if status_line is None:
                findings.append(f"{rel}: ヘッダ定型 (状態:) がない — handoff/README.md の定型に従う")
            elif re.search(r"作業中|計測中", status_line) and now - f.stat().st_mtime > HANDOFF_STALE_SECONDS:
                findings.append(
                    f"{rel}: 状態が稼働中のまま 48h 以上未更新 — 死んだセッションの可能性。中断扱いで回収を"
                )

    if findings:
        print(f"check_docs: {len(findings)} 件の違反")
        for f in findings:
            print("  -", f)
        return 1
    print("check_docs: 違反なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
