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
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# living docs = 現在の状態・設計を主張する文書。ここに可変状態の再掲と行番号参照を禁止する。
# 対象外 = 追記型の日誌・記録 (書いた時点で凍結): worklog / decisions / insights / paper-story /
# docs/archive/ 配下 (監査台帳・worklog アーカイブ等の凍結族。規約は同 README — ファイル名不変で移動)、
# および完了 Phase の phase1/phase2 (2026-07-05 に冒頭へ凍結宣言済み)。
LIVING_DOCS = [
    REPO / "AGENTS.md",                         # Codex 用の共有規律入口
    REPO / "CLAUDE.md",
    REPO / ".codex" / "agents" / "README.md", # Codex runtime adapter の生きた運用文書
    REPO / "docs" / "README.md",                  # docs の地図 (2026-07-11 fc-05 で CLAUDE.md から委譲)
    REPO / "docs" / "ai-provenance.md",           # commit provenance の共有規約
    REPO / "docs" / "roadmap.md",
    REPO / "docs" / "related-work" / "README.md",  # 旧 related-work.md はディレクトリ化 (2026-07-11 監査 lint-04 で修正 — 旧パスは黙って skip されていた)
    REPO / "docs" / "phase3.md",                  # 現行 phase doc。Phase 移行時にここを差し替え、旧 doc は凍結宣言
    REPO / "docs" / "phase3-main-experiment.md",  # 事前登録 (サンプル設計数値の確定追記が残るため living)
    REPO / "docs" / "glossary.md",
    REPO / "docs" / "agent-architecture.md",
    REPO / "docs" / "orchestrator-design.md",
    REPO / "docs" / "ccbench-anatomy.md",
    REPO / "docs" / "axis-onboarding.md",              # 2026-07-11 監査 dup-05 で追加
    REPO / "docs" / "isolation-phenomena.md",          # 2026-07-12 監査: 現在形の生きた参照文書なのに lint 網の外だった
    # token-management-strategy.md は 2026-07-11 に docs/archive/ へ凍結移動 → 2026-07-15 に git-history-only 化 (F8 捏造文書、墓標 = docs/archive/README.md)
]
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
