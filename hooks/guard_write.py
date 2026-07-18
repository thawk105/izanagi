#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 hook: Edit/Write の書き込み時点防壁 — 方針 A の最小第二防壁 (規律2, phase3.md タスク3)。

PreToolUse (Write|Edit|MultiEdit|NotebookEdit) で発火し、対象パスが管轄内なら
書き込み**前**に検査して exit 2 (拒否, stderr が Claude に返る) / exit 0 (許可)。

管轄 = **明白な直接書き込みの拒否、この 2 本だけ** (方針 A, D30/D33。これ以外のパスは
即許可 — 通常の開発作業を妨げない):
1. **成果物の proof chain (規律2):** `output/campaigns/*/runs/` (WAL)・`campaign.lock`・
   `build-variants/` への Edit/Write を拒否。COMMIT/fitness を書く唯一の経路は
   pipeline.evaluate() (phase3.md)。verifier を迂回した性能数値の直接更新を塞ぐ。
2. **designated ソース外への Write (D23/D24):** `external/ccbench/` 内は EVOLVE-BLOCK
   ソース (source_digest.EVOLVE_BLOCK_SOURCES) だけ書き込み可。`Options.cmake` 等は
   人間 template 専有 — template 改訂は patches/ + git apply (Bash) 経由で行う。

**旧設計 (payload/skeleton のテキスト検査) は方針 A で削除した (D33):** #ifdef・build 時
マクロ・TRACE 混入の保証は、テキスト検査の完全性 (GW2R-1 の backslash-newline splice が
原理的限界を実証) ではなく一次防壁が担う — identity は source_digest の preprocess 後
ハッシュ + #include 行 HEAD 固定 + build 出口の TOCTOU 再照合、観測者効果 (規律1) は
diff-of-diffs (source_digest.assert_trace_diff_matches_head、build 出口で発火)。
designated ソース内の書き込み内容はここでは検査しない — 何を書いても identity が正直に
変わり (偽 cache hit しない)、TRACE 条件付き挙動差は build 出口で fails-closed になる。
意味的な逸脱 (骨格破壊・領域外編集) の判定は auditor / 人間レビュー領域。

これは第二防壁であり sandbox ではない。Bash 経由の書き込みは guard_bash.py が、
identity 整合は source_digest (fails-closed) が担う。
"""
from __future__ import annotations

import json
import os
import sys

# source_digest.EVOLVE_BLOCK_SOURCES の写し (hook は単体で動く必要があるため import
# しない)。ドリフトは orchestrator/tests/test_hooks.py が両者の一致を assert して防ぐ。
EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")


def _repo_root() -> str:
    # hooks/guard_write.py = <repo>/hooks/guard_write.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _protected_artifact(rp: str, camp_root: str) -> str:
    """proof-chain 成果物なら理由ラベル、そうでなければ空文字。

    camp_root = realpath(<root>/output/campaigns)。rp も realpath 済みなので、output/ が
    別ボリュームへの symlink でも両端が揃う (2026-07-04 敵対検証 write-bypass の fail-open)。"""
    camp = camp_root + os.sep
    if rp.startswith(camp):
        parts = rp[len(camp):].split(os.sep)
        if len(parts) >= 2 and parts[1] == "runs":
            return "WAL (campaigns/*/runs/)"
        if len(parts) == 2 and parts[1] == "campaign.lock":
            return "campaign.lock (identity の正準 pre-image)"
    if os.sep + "build-variants" + os.sep in rp or rp.endswith(os.sep + "build-variants"):
        return "build-variants (ビルドキャッシュ)"
    return ""


def decide(tool_name: str, tool_input: dict, repo_root: str = "") -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    # root も realpath で解決する: rp は realpath 済みなので、root が未解決 (output/ や
    # external/ccbench が別ボリュームへの symlink 等) だと startswith 照合が外れ fail-open に
    # なる (2026-07-04 敵対検証 write-bypass)。両端を realpath で揃える。
    root = os.path.realpath(repo_root or _repo_root())
    # NotebookEdit の実書込先は notebook_path。file_path を先に見ると、良性 file_path decoy で
    # 管轄外と誤判定し notebook_path 側 (ccbench/WAL) への書込を通す (2026-07-04 敵対検証)。
    if tool_name == "NotebookEdit":
        path = tool_input.get("notebook_path") or tool_input.get("file_path") or ""
    else:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not path:
        return True, ""                     # パス無し = ツール側が失敗する。管轄外
    rp = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))

    # 比較基盤も realpath で解決 (output/ や external/ccbench 自身が symlink でも rp と揃える)。
    camp_root = os.path.realpath(os.path.join(root, "output", "campaigns"))
    label = _protected_artifact(rp, camp_root)
    if label:
        return False, (
            f"{label} への直接書き込みは拒否 (規律2)。COMMIT/fitness を書く唯一の"
            "経路は pipeline.evaluate()。verifier を迂回した成果物の更新は不可")

    # s8b-freeze namespace (承認 record / active pointer / revocation / 世代 file) への
    # 直接 Write/Edit を拒否する (F6a、C1-11)。これは **誤操作抑止であって認証防壁では
    # ない** — approval/active/revocation の真正性は s8b_ratified_freeze の Git 内容による
    # 規約 attestation (AI-Agent: none 逐語 + 導入 commit topology) が担い、hook を層に
    # 数えない。AI が `none` commit を作れる以上ここは人間性の機械証明にならない。
    freeze_root = os.path.realpath(os.path.join(root, "output", "s8b-freeze"))
    if rp == freeze_root or rp.startswith(freeze_root + os.sep):
        return False, (
            "output/s8b-freeze/ 配下への直接書き込みは拒否 (F6a 誤操作抑止)。approval/"
            "active pointer/revocation/世代 file の発効は人間 commit + s8b_ratified_freeze "
            "検証を経る (これは認証防壁ではなく誤操作抑止)")

    sub = os.path.realpath(os.path.join(root, "external", "ccbench"))
    if rp == sub or rp.startswith(sub + os.sep):
        rel = os.path.relpath(rp, sub)
        if tool_name == "NotebookEdit":
            return False, "external/ccbench への NotebookEdit は編集面外 (D24)"
        if rel not in EVOLVE_BLOCK_SOURCES:
            return False, (
                f"external/ccbench の編集面は EVOLVE-BLOCK ソース {EVOLVE_BLOCK_SOURCES} "
                f"のみ ({rel} は不可)。Options.cmake 等は人間 template 専有 — template "
                "改訂は patches/ + git apply で (F1/D24)")
        # designated ソース内 — 内容は検査しない (方針 A, D33)。identity の正直さと
        # TRACE 混入は一次防壁 (preprocess 後ハッシュ / diff-of-diffs) が build/resolve
        # 出口で fails-closed に捕える。意味判定は auditor / 人間レビュー領域。
        return True, ""

    return True, ""                          # 管轄外 (通常の開発作業)


def main() -> int:
    raw = sys.stdin.read()                 # 例外時の fails-closed 判定に使うため一度で読む
    try:
        payload = json.loads(raw)
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input") or {}
        allow, reason = decide(tool_name, tool_input)
    except Exception as e:  # noqa: BLE001 — hook 自身の不具合で全書き込みを止めない。
        # ただし入力に管轄トークンが見えるときだけは fails-closed に倒す。
        if any(t in raw for t in ("external/ccbench", "wal.jsonl", "campaign.lock",
                                  "build-variants", "output/s8b-freeze")):
            print(f"guard_write hook 内部エラー ({type(e).__name__}: {e}) — 管轄パスを"
                  "含むため fails-closed で拒否", file=sys.stderr)
            return 2
        return 0
    if not allow:
        print(f"[guard_write] 拒否: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
