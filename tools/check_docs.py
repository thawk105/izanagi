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
    REPO / "CLAUDE.md",
    REPO / "docs" / "README.md",                  # docs の地図 (2026-07-11 fc-05 で CLAUDE.md から委譲)
    REPO / "docs" / "roadmap.md",
    REPO / "docs" / "related-work" / "README.md",  # 旧 related-work.md はディレクトリ化 (2026-07-11 監査 lint-04 で修正 — 旧パスは黙って skip されていた)
    REPO / "docs" / "phase3.md",                  # 現行 phase doc。Phase 移行時にここを差し替え、旧 doc は凍結宣言
    REPO / "docs" / "phase3-main-experiment.md",  # 事前登録 (サンプル設計数値の確定追記が残るため living)
    REPO / "docs" / "glossary.md",
    REPO / "docs" / "agent-architecture.md",
    REPO / "docs" / "orchestrator-design.md",
    REPO / "docs" / "ccbench-anatomy.md",
    REPO / "docs" / "axis-onboarding.md",              # 2026-07-11 監査 dup-05 で追加
    # token-management-strategy.md は 2026-07-11 に docs/archive/ へ凍結移動 (対象外の凍結族へ)
]

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
HANDOFF_MAX_LINES = 60          # 定型 40 行 + 余白
HANDOFF_STALE_SECONDS = 48 * 3600

# --- 参照実在性 (2026-07-11 追加、docs 整備) ---
# living docs 中の「実在しない D 番号」「実在しないファイルパス」への参照 = 腐敗。
# 凍結族 (worklog/decisions/insights/archive) は対象外 — 書いた時点で正しければよい。
D_REF = re.compile(r"\bD(\d{1,3})\b")
# パスは既知のトップディレクトリ始まりに限定 (submodule 内 cc/ 等は pin 固定で腐らないので対象外)。
# プレースホルダ (<日付> 等)・glob (*) は文字クラス外なのでマッチが切れ、拡張子必須で自然に除外される。
# 負の後読み: external/ccbench/docs/... のような長いパスの途中を docs/... と誤マッチしない
PATH_REF = re.compile(r"(?<![\w/])(?:docs|tools|orchestrator|hooks|patches|output|src|\.claude)/[\w.\-/]+\.[A-Za-z0-9]+")


def main() -> int:
    findings: list[str] = []

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

    if HANDOFF_DIR.exists():
        now = time.time()
        for f in sorted(HANDOFF_DIR.glob("*.md")):
            if f.name == "README.md":
                continue
            rel = f.relative_to(REPO)
            text = f.read_text()
            nlines = len(text.splitlines())
            if nlines > HANDOFF_MAX_LINES:
                findings.append(
                    f"{rel}: {nlines} 行 (> {HANDOFF_MAX_LINES})。handoff は上書き運用・40 行上限"
                )
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
