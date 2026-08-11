#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 hook: Edit/Write の書き込み時点防壁 — 方針 A の最小第二防壁 (規律2, phase3.md タスク3)。

PreToolUse (Write|Edit|MultiEdit|NotebookEdit) で発火し、対象パスが管轄内なら
書き込み**前**に検査して exit 2 (拒否, stderr が Claude に返る) / exit 0 (許可)。

管轄 = **明白な直接書き込みの拒否、この 2 本だけ** (方針 A, D30/D33。これ以外のパスは
即許可 — 通常の開発作業を妨げない):
1. **成果物の proof chain (規律2):** official / exploration campaign の `runs/`
   (WAL)・`campaign.lock` と `build-variants/` への Edit/Write を拒否する。また、
   exploration namespace marker への直接書き込みも拒否する。COMMIT/fitness を書く
   唯一の経路は pipeline.evaluate() (phase3.md)。verifier を迂回した成果物更新を塞ぐ。
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


def _protected_artifact(rp: str, camp_roots: tuple[str, ...]) -> str:
    """proof-chain 成果物なら理由ラベル、そうでなければ空文字。

    camp_roots は official / exploration の閉じた二要素集合。rp と各 root は同じ
    resolution mode に揃えるため、realpath 判定でも lexical entry 判定でも片側だけが
    symlink 解決されて照合を外すことがない。"""
    for camp_root in camp_roots:
        camp = camp_root + os.sep
        if rp.startswith(camp):
            parts = rp[len(camp):].split(os.sep)
            if len(parts) >= 2 and parts[1] == "runs":
                return "WAL (campaigns/*/runs/)"
            if len(parts) == 2 and parts[1] == "campaign.lock":
                return "campaign.lock (identity の正準 pre-image)"
    # campaign root に依存しない leaf 条件は root loop の外に一度だけ置く。
    if os.sep + "build-variants" + os.sep in rp or rp.endswith(os.sep + "build-variants"):
        return "build-variants (ビルドキャッシュ)"
    return ""


_APPLY_PATCH_DIRECTIVES = (
    ("add", "*** Add File: "),
    ("update", "*** Update File: "),
    ("delete", "*** Delete File: "),
    ("move_to", "*** Move to: "),
)


def parse_apply_patch(command: str) -> list[tuple[str, str]]:
    """Codex apply_patch の exact directive を最後まで抽出する。

    block の妥当性は許可根拠にしない。壊れた block や orphan Move to があっても
    後続を含む全行を走査し、見つかった候補は拒否を増やすためだけに使う。
    """
    operations = []
    for line in command.splitlines():
        for kind, prefix in _APPLY_PATCH_DIRECTIVES:
            if line.startswith(prefix):
                operations.append((kind, line[len(prefix):]))
                break
    return operations


def classify_path(
    abs_path: str,
    root: str,
    *,
    resolve_final: bool = True,
) -> tuple[bool, str]:
    """絶対 path を既存の artifact / namespace / freeze / ccbench 核で判定する。

    ``resolve_final=False`` は Delete / Move 元の lexical directory entry 用。
    判定条件は共通のまま、対象と比較基盤の双方を lexical に揃える。
    """
    root = os.path.realpath(root)
    lexical_path = os.path.abspath(abs_path)
    if resolve_final:
        rp = os.path.realpath(lexical_path)
        camp_roots = (
            os.path.realpath(os.path.join(root, "output", "campaigns")),
            os.path.realpath(os.path.join(root, "output", "exploration", "campaigns")),
        )
    else:
        rp = lexical_path
        camp_roots = (
            os.path.abspath(os.path.join(root, "output", "campaigns")),
            os.path.abspath(os.path.join(root, "output", "exploration", "campaigns")),
        )
    label = _protected_artifact(rp, camp_roots)
    if label:
        return False, (
            f"{label} への直接書き込みは拒否 (規律2)。COMMIT/fitness を書く唯一の"
            "経路は pipeline.evaluate()。verifier を迂回した成果物の更新は不可")

    if resolve_final:
        exploration_root = os.path.realpath(
            os.path.join(root, "output", "exploration"))
    else:
        exploration_root = os.path.abspath(
            os.path.join(root, "output", "exploration"))
    lexical_exploration_root = os.path.abspath(
        os.path.join(root, "output", "exploration"))
    if (os.path.basename(lexical_path) == "namespace.json"
            and (lexical_path.startswith(lexical_exploration_root + os.sep)
                 or rp.startswith(exploration_root + os.sep))):
        return False, (
            "output/exploration/ 配下の namespace.json への直接書き込みは"
            "拒否。exploration 成果物を official と誤受理させないための "
            "namespace marker は変更不可")

    # s8b-freeze namespace (承認 record / active pointer / revocation / 世代 file) への
    # 直接 Write/Edit を拒否する (F6a、C1-11)。これは **誤操作抑止であって認証防壁では
    # ない** — approval/active/revocation の真正性は s8b_ratified_freeze の Git 内容による
    # 規約 attestation (AI-Agent: none 逐語 + 導入 commit topology) が担い、hook を層に
    # 数えない。AI が `none` commit を作れる以上ここは人間性の機械証明にならない。
    if resolve_final:
        freeze_root = os.path.realpath(os.path.join(root, "output", "s8b-freeze"))
    else:
        freeze_root = os.path.abspath(os.path.join(root, "output", "s8b-freeze"))
    if rp == freeze_root or rp.startswith(freeze_root + os.sep):
        return False, (
            "output/s8b-freeze/ 配下への直接書き込みは拒否 (F6a 誤操作抑止)。approval/"
            "active pointer/revocation/世代 file の発効は人間 commit + s8b_ratified_freeze "
            "検証を経る (これは認証防壁ではなく誤操作抑止)")

    if resolve_final:
        sub = os.path.realpath(os.path.join(root, "external", "ccbench"))
    else:
        sub = os.path.abspath(os.path.join(root, "external", "ccbench"))
    if rp == sub or rp.startswith(sub + os.sep):
        rel = os.path.relpath(rp, sub)
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


def _decide_apply_patch(
    tool_input: dict,
    root: str,
    cwd: str,
) -> tuple[bool, str]:
    operations = parse_apply_patch(tool_input.get("command") or "")
    cwd_valid = bool(cwd) and os.path.isabs(cwd) and os.path.isdir(cwd)
    denials = []

    for index, (kind, raw_path) in enumerate(operations):
        if not os.path.isabs(raw_path) and not cwd_valid:
            denials.append(
                f"{raw_path!r}: 相対 path の基準となる payload cwd が空・非絶対・不在")
            continue

        lexical_path = os.path.abspath(
            raw_path if os.path.isabs(raw_path) else os.path.join(cwd, raw_path))
        reasons = []
        allow, reason = classify_path(lexical_path, root)
        if not allow:
            reasons.append(reason)

        is_move_source = (
            kind == "update"
            and index + 1 < len(operations)
            and operations[index + 1][0] == "move_to"
        )
        if kind == "delete" or is_move_source:
            lexical_allow, lexical_reason = classify_path(
                lexical_path, root, resolve_final=False)
            if not lexical_allow and lexical_reason not in reasons:
                reasons.append(lexical_reason)

        if reasons:
            denials.append(f"{raw_path!r}: {' / '.join(reasons)}")

    if denials:
        return False, "apply_patch の拒否対象: " + "; ".join(denials)
    # path を抽出できたこと自体は許可根拠ではない。候補から拒否が増えなかった場合にのみ、
    # wave 前と同じ管轄外扱いへ戻す。
    return True, ""


def decide(
    tool_name: str,
    tool_input: dict,
    repo_root: str = "",
    cwd: str = "",
) -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    # root も realpath で解決する: rp は realpath 済みなので、root が未解決 (output/ や
    # external/ccbench が別ボリュームへの symlink 等) だと startswith 照合が外れ fail-open に
    # なる (2026-07-04 敵対検証 write-bypass)。両端を realpath で揃える。
    root = os.path.realpath(repo_root or _repo_root())
    if tool_name == "apply_patch":
        return _decide_apply_patch(tool_input, root, cwd)

    # NotebookEdit の実書込先は notebook_path。file_path を先に見ると、良性 file_path decoy で
    # 管轄外と誤判定し notebook_path 側 (ccbench/WAL) への書込を通す (2026-07-04 敵対検証)。
    if tool_name == "NotebookEdit":
        path = tool_input.get("notebook_path") or tool_input.get("file_path") or ""
    else:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not path:
        return True, ""                     # パス無し = ツール側が失敗する。管轄外
    lexical_path = os.path.abspath(
        path if os.path.isabs(path) else os.path.join(root, path))
    allow, reason = classify_path(lexical_path, root)
    if tool_name == "NotebookEdit":
        rp = os.path.realpath(lexical_path)
        sub = os.path.realpath(os.path.join(root, "external", "ccbench"))
        if (rp == sub or rp.startswith(sub + os.sep)) and (
                allow or reason.startswith("external/ccbench の編集面")):
            return False, "external/ccbench への NotebookEdit は編集面外 (D24)"
    return allow, reason


def main() -> int:
    raw = sys.stdin.read()                 # 例外時の fails-closed 判定に使うため一度で読む
    tool_name = ""
    try:
        payload = json.loads(raw)
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input") or {}
        allow, reason = decide(tool_name, tool_input, cwd=payload.get("cwd") or "")
    except Exception as e:  # noqa: BLE001 — hook 自身の不具合で全書き込みを止めない。
        # ただし入力に管轄トークンが見えるときだけは fails-closed に倒す。
        protected_tokens = ("external/ccbench", "wal.jsonl", "campaign.lock",
                            "build-variants", "output/s8b-freeze",
                            "output/exploration/", "namespace.json")
        if tool_name == "apply_patch":
            protected_tokens += ("output/campaigns/", "/runs/", "runs/")
        if any(t in raw for t in protected_tokens):
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
