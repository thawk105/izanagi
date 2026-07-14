#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""コンテキスト衛生 hook: 大きい記録ファイルの offset/limit 無し Read を止める (D35)。

PreToolUse (Read) で発火し、repo 内 `docs/` / `output/` 配下の閾値超テキストを
offset/limit 無しで Read しようとしたら exit 2 (拒否, stderr が Claude に返る)。

**位置づけ: guard_write / guard_bash (正しさ規律 1・2 の第二防壁) とは別系統の
コンテキスト衛生層。** D35 (大きい参照文書は grep index → 部分読み) は prompt 規律
だったが、事故 1 回の全読 (decisions.md 235KB ≈ 70K token) の被害が大きく、
機械執行に格上げした (2026-07-15、失敗台帳 [コンテキスト浪費] 型の恒久対応)。

設計:
- 管轄 = repo 内 `docs/` と `output/` 配下のみ (ソースコード等の通常開発は妨げない)
- 閾値 = 80KB。規約上の全読があり得る文書 (roadmap 52KB の Phase 初回全読、
  phase3.md 54KB、glossary 43KB) は通し、事故の主犯級 (decisions 235KB /
  worklog アーカイブ / 監査 JSON / WAL・trace) だけ捕まえる
- offset / limit / pages のいずれかが明示されていれば許可 — 止めるのは「事故の
  無指定全読」だけで、意図的な分割読みや部分読みは 1 回の再試行で通る
- 画像等のバイナリは除外 (offset の概念がない)
- **fail-open**: hook 自身の不具合では読み取りを止めない (guard_write の
  fails-closed と逆。読み取り事故の被害はトークンであって正しさではないため、
  可用性を優先する)
"""
from __future__ import annotations

import json
import os
import sys

# 管轄 top ディレクトリ (repo 相対)。docs = 参照文書・記録、output = insights/WAL/trace。
GUARDED_TOPDIRS = ("docs", "output")
# 閾値。根拠は docstring 参照。UTF-8 日本語混在で 80KB ≈ 25K token 前後。
THRESHOLD_BYTES = 80_000
# offset/limit が意味を持たないバイナリ族は管轄外 (Read は画像も表示できる)。
BINARY_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".pdf", ".svg")


def _repo_root() -> str:
    # hooks/guard_read.py = <repo>/hooks/guard_read.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def decide(tool_name: str, tool_input: dict, repo_root: str = "") -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    if tool_name != "Read":
        return True, ""                     # 管轄外ツール
    path = tool_input.get("file_path") or ""
    if not path:
        return True, ""                     # パス無し = ツール側が失敗する。管轄外
    # 部分読みの意思 (キー存在で判定 — offset=0 等の falsy 値も明示指定として尊重)
    if any(k in tool_input for k in ("offset", "limit", "pages")):
        return True, ""

    # 両端 realpath で照合 (guard_write の symlink fail-open 対策と同系)
    root = os.path.realpath(repo_root or _repo_root())
    rp = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
    for top in GUARDED_TOPDIRS:
        base = os.path.realpath(os.path.join(root, top))
        if rp == base or rp.startswith(base + os.sep):
            break
    else:
        return True, ""                     # 管轄外 (repo 外・docs/output 外)

    if rp.lower().endswith(BINARY_SUFFIXES):
        return True, ""
    try:
        size = os.path.getsize(rp)
    except OSError:
        return True, ""                     # 実在しない等はツール側が報告する
    if size <= THRESHOLD_BYTES:
        return True, ""

    rel = os.path.relpath(rp, root)
    return False, (
        f"{rel} ({size // 1000}KB) の offset/limit 無し Read は拒否 (コンテキスト衛生、"
        "D35)。まず grep -n で見出し index を取り (例: decisions は grep -n '^## D'、"
        "worklog 系は grep -n '^## ')、必要な節だけ offset/limit 指定で部分読みする。"
        "全文が本当に必要な場合も offset/limit を明示して分割で読む (大きい全読の要約は"
        "サブエージェントに委ね、構造化された結論だけ受け取るのが規約)")


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        allow, reason = decide(payload.get("tool_name", ""),
                               payload.get("tool_input") or {})
    except Exception:  # noqa: BLE001 — 衛生層は fail-open (docstring 参照)
        return 0
    if not allow:
        print(f"[guard_read] 拒否: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
