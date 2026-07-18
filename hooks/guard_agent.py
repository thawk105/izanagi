#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""モデル経済衛生 hook: model 未指定の ad-hoc Agent 呼び出し (親モデル暗黙継承) を止める。

PreToolUse (Agent) で発火し、model が明示されず、かつ frontmatter に model ピンの
ある named role でもない Agent 呼び出しを exit 2 (拒否, stderr が Claude に返る) する。

**位置づけ: guard_write / guard_bash (正しさ規律 1・2 の第二防壁) とも guard_read
(コンテキスト衛生) とも別系統の、モデル経済衛生層。** 子エージェントに model を
指定しないとセッション主モデル (fable) を暗黙継承する。fable のレート制限は他
モデルよりタイトで、subagent の大量並列がここを浪費すると親セッションの裁定・統合
が制限に当たる。「子の model/effort は難易度に整合させて明示する」は prompt 規律
(memory) だったが、暗黙継承は無指定という*不作為*で起きるため見落としやすく、
機械執行に格上げした (2026-07-18 ユーザー承認)。

設計:
- 管轄 = Agent tool のみ。止めるのは「model も frontmatter ピンも無い暗黙継承」だけ
- model が明示されていれば値は問わず通す (fable 明示も通す — 可視・意図的な選択の
  適否は規律領分。この hook は不作為のデフォルトだけを塞ぐ)
- subagent_type が named role で、その定義 (.claude/agents/<type>.md — project 側
  または user 側 ~/.claude/agents) の frontmatter に model ピンがあれば通す
  (ピンが機械適用されるため呼び出し側の明示は不要)
- subagent_type == "fork" は通す (fork は構造的に親モデル固定で override 無効 —
  明示しても意味がなく、fork と書くこと自体が可視・意図的な選択)
- **fail-open**: hook 自身の不具合では起動を止めない (guard_read と同方向。被害は
  トークンであって正しさではないため、可用性を優先する)
"""
from __future__ import annotations

import json
import os
import re
import sys

# role 名として許す形。path traversal (../ 等) で偽 role ファイルを参照させない。
_ROLE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
# fork は親モデル固定 (model override は無効) — 明示のしようがない特例。
_PARENT_PINNED_TYPES = {"fork"}


def _repo_root() -> str:
    # hooks/guard_agent.py = <repo>/hooks/guard_agent.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _agents_dirs(repo_root: str) -> list:
    # project 側が第一。user 側 (~/.claude/agents) の role も harness は解決する。
    return [os.path.join(repo_root, ".claude", "agents"),
            os.path.join(os.path.expanduser("~"), ".claude", "agents")]


def _frontmatter_has_model(md_path: str) -> bool:
    """agent 定義の YAML frontmatter (先頭の --- ... ---) に model ピンがあるか。

    敵対レビュー反映 (2026-07-18): BOM は utf-8-sig で除去、YAML doc-end `...` も
    終端扱い (本文の model: 行を誤検出しない)、`model :` (コロン前空白) も YAML
    としては正当なピンなので認める。
    """
    try:
        with open(md_path, encoding="utf-8-sig", errors="replace") as f:
            first = f.readline()
            if first.strip() != "---":
                return False
            for line in f:
                if line.strip() in ("---", "..."):
                    return False        # frontmatter 終端まで model なし
                if re.match(r"^model\s*:\s*\S", line):
                    return True
    except OSError:
        return False                    # 読めない定義はピンの証明にならない
    return False


def decide(tool_name: str, tool_input: dict, repo_root: str = "") -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    if tool_name != "Agent":
        return True, ""                 # 管轄外ツール
    model = tool_input.get("model")
    if isinstance(model, str) and model.strip():
        return True, ""                 # 明示があれば値は問わない (docstring 参照)

    stype = tool_input.get("subagent_type")
    stype = stype.strip() if isinstance(stype, str) else ""
    if stype in _PARENT_PINNED_TYPES:
        return True, ""
    if stype and _ROLE_NAME_RE.match(stype):
        root = os.path.realpath(repo_root or _repo_root())
        for d in _agents_dirs(root):
            p = os.path.join(d, stype + ".md")
            if os.path.exists(p):
                if _frontmatter_has_model(p):
                    return True, ""     # named role のピンが機械適用される
                # 最初に定義を見つけた dir で確定 (harness の同名解決と同じ優先
                # 順位)。後段 dir のピンでは上書きさせない — project 側 unpinned +
                # user 側 pinned の衝突で暗黙継承を素通しさせない (敵対レビュー反映)
                break

    label = stype or "(subagent_type 無し)"
    return False, (
        f"model 未指定の Agent 呼び出し ({label}) は拒否 (モデル経済衛生)。"
        "無指定はセッション主モデル (通常 fable) の暗黙継承になり、レート制限を"
        "浪費する。対処は次のどちらか: (1) model を明示して再試行 — 目安: 機械的"
        "検査・構造化収集・起草 = sonnet / 些末な確認 = haiku / 意味的レビュー・"
        "敵対検証・裁定 = opus。(2) model と effort を frontmatter にピンした "
        "named role (.claude/agents/) を subagent_type に指定する (effort を難易度に"
        "合わせる経路はこちら — Agent 呼び出し自体に effort パラメータは無い)。"
        "fable を使うべき例外 (真に最難の裁定) では model: fable と明示すれば通る")


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        tool_input = payload.get("tool_input")
        allow, reason = decide(payload.get("tool_name", ""),
                               tool_input if isinstance(tool_input, dict) else {})
    except Exception:  # noqa: BLE001 — 経済衛生層は fail-open (docstring 参照)
        return 0
    if not allow:
        print(f"[guard_agent] 拒否: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
