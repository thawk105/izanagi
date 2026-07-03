#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 hook: Edit/Write の書き込み時点防壁 (規律1・2 の第二防壁, phase3.md タスク3)。

PreToolUse (Write|Edit|MultiEdit|NotebookEdit) で発火し、対象パスが管轄内なら
書き込み**前**に検査して exit 2 (拒否, stderr が Claude に返る) / exit 0 (許可)。

管轄 (これ以外のパスは即許可 — 通常の開発作業を妨げない):
1. **成果物の proof chain (規律2):** `output/campaigns/*/runs/` (WAL)・`campaign.lock`・
   `build-variants/` への Edit/Write を拒否。COMMIT/fitness を書く唯一の経路は
   pipeline.evaluate() (phase3.md)。verifier を迂回した性能数値の直接更新を塞ぐ。
2. **coder の編集面 (規律1/2, D23/D24):** `external/ccbench/` 内は EVOLVE-BLOCK ソース
   (source_digest.EVOLVE_BLOCK_SOURCES) だけ書き込み可。`Options.cmake` は digest 非被覆
   (敵対レビュー F1 = 偽 cache hit 源) なので人間 template 専有 — template 改訂は patches/
   + git apply (Bash) 経由で行う。許可ソース内も**変更が EVOLVE-BLOCK 領域の #if 枝
   (payload) に閉じる**ことを検査し、payload 内の生プリプロセッサ指令・予約識別子/
   非決定 builtin・TRACE トークンを拒否 (F2 / D23 道Y / 規律1)。

これは第二防壁であり sandbox ではない。Bash 経由の書き込みは guard_bash.py が、
identity 整合は source_digest (fails-closed) が、事後監査は auditor (Phase 3 後続) が担う。
判定不能 (Edit の old_string 不一致等) は管轄内なら fails-closed で拒否する。
"""
from __future__ import annotations

import json
import os
import re
import sys

# source_digest.EVOLVE_BLOCK_SOURCES の写し (hook は単体で動く必要があるため import
# しない)。ドリフトは orchestrator/tests/test_hooks.py が両者の一致を assert して防ぐ。
EVOLVE_BLOCK_SOURCES = ("include/backoff.hh",)

_BEGIN_RE = re.compile(r"^\s*//\s*EVOLVE-BLOCK-BEGIN\b")
_END_RE = re.compile(r"^\s*//\s*EVOLVE-BLOCK-END\b")
_IF_RE = re.compile(r"^\s*#\s*if\b")
_ELSE_RE = re.compile(r"^\s*#\s*else\b")
_ENDIF_RE = re.compile(r"^\s*#\s*endif\b")
_PLACEHOLDER = "\x00PAYLOAD\x00"

# コメント除去後の行頭指令検出。素の `#` に加え C++ digraph `%:` (g++ が # と解釈)
# も捕える (GW-1 敵対レビュー F1)。trigraph `??=` は g++ 既定 (-trigraphs 無し) で
# 無効なので対象外。
_DIRECTIVE_RE = re.compile(r"^\s*(#|%:)")

# payload (coder が書く #if 枝) で禁止するトークン。
# - ^\s*# 生指令: #include/#define/#if 系すべて (F2: -undef digest は active 枝の
#   build 時マクロ値を覆わない。行頭アンカー走査は F4 の方針どおり)
# - 予約識別子 (__* / _大文字*): __DATE__/__TIME__/__builtin_*/__OPTIMIZE__ 等の
#   非決定・digest 非被覆 builtin を包括的に塞ぐ
# - NDEBUG / GLOBAL_VALUE_DEFINE: 予約形式でないが build 時に値を持つ digest 非被覆マクロ (F2)
# - TRACE / izanagi_trace: 検証専用トークンが perf 経路 (EVOLVE payload は trace/perf
#   両ビルドに入る) に混入するのを拒否 (規律1)
_PAYLOAD_TOKEN_BANS = (
    (re.compile(r"\b__\w+"), "予約識別子 (__*) = 非決定/digest 非被覆 builtin の疑い"),
    (re.compile(r"\b_[A-Z]\w*"), "予約識別子 (_大文字*)"),
    (re.compile(r"\bNDEBUG\b"), "build 時マクロ NDEBUG (digest 非被覆, F2)"),
    (re.compile(r"\bGLOBAL_VALUE_DEFINE\b"),
     "build 時マクロ GLOBAL_VALUE_DEFINE (digest 非被覆, F2)"),
    (re.compile(r"\bTRACE\b"), "検証専用トークン TRACE (規律1: 観測者効果の分離)"),
    (re.compile(r"izanagi_trace"), "検証専用シンボル izanagi_trace (規律1)"),
)


def _repo_root() -> str:
    # hooks/guard_write.py = <repo>/hooks/guard_write.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _strip_comments(code: str) -> str:
    """C++ の字句規則に沿って左優先の単一パスで // と /* */ を除去する。

    素朴に「/* */ を先に消してから //」とすると、C++ レキサの左優先 (行内で先に
    現れた導入子が勝つ) が破れる: `// ... /*` の `/*` は行コメント内で本来無効
    (inert) なのに、ブロック除去を先にかけると本物のブロック開始と誤認して次の
    `*/` (別の // 行に隠せる) までの実コードを丸ごと消し、消えた行に置いた
    #include/__DATE__/TRACE が payload 検査から抜ける (GW-1 敵対レビュー critical)。
    左優先の状態機械にすれば行/ブロック導入子は先に現れた方が勝つ。文字列・文字
    リテラルは温存する (中の // が誤ってコメント開始扱いされないように)。
    行構造 (改行) は温存し ^ アンカー走査を保つ。"""
    out = []
    i, n = 0, len(code)
    LINE, BLOCK, STR, CHAR = range(4)
    state = None
    while i < n:
        c = code[i]
        two = code[i:i + 2]
        if state == LINE:
            if c == "\n":
                state = None
                out.append(c)
            i += 1
        elif state == BLOCK:
            if two == "*/":
                state = None
                i += 2
            else:
                if c == "\n":
                    out.append(c)
                i += 1
        elif state in (STR, CHAR):
            out.append(c)
            if c == "\\" and i + 1 < n:      # エスケープ: 次の1文字はリテラルの一部
                out.append(code[i + 1])
                i += 2
                continue
            if (state == STR and c == '"') or (state == CHAR and c == "'"):
                state = None
            i += 1
        else:                                # normal
            if two == "//":
                state = LINE
                i += 2
            elif two == "/*":
                state = BLOCK
                i += 2
            elif c == '"':
                state = STR
                out.append(c)
                i += 1
            elif c == "'":
                state = CHAR
                out.append(c)
                i += 1
            else:
                out.append(c)
                i += 1
    return "".join(out)


def _payload_violations(payload: str) -> list:
    """新しい payload の禁止トークン検査。違反理由のリストを返す (空 = 合格)。"""
    out = []
    if "EVOLVE-BLOCK" in payload:
        out.append("payload 内に EVOLVE-BLOCK マーカー文字列 (領域偽装)")
    code = _strip_comments(payload)
    for line in code.splitlines():
        if _DIRECTIVE_RE.match(line):
            out.append(f"生プリプロセッサ指令 (D23 道Y): {line.strip()[:60]}")
    for pat, why in _PAYLOAD_TOKEN_BANS:
        m = pat.search(code)
        if m:
            out.append(f"{why}: {m.group(0)}")
    return out


def _parse_regions(text: str):
    """text を EVOLVE-BLOCK 構造で分解 → (skeleton: str, payloads: list, err: str)。

    skeleton = payload を _PLACEHOLDER に置換した全文。payload = 各領域の #if 枝
    (BEGIN → head → #if 行 → **payload** → #else 行 → stock 枝 → #endif 行 → END)。
    構造が壊れていれば err (fails-closed)。マーカー無しのファイルは全文 skeleton
    (= どこも書き換え不可) として扱う。"""
    OUT, HEAD, PAYLOAD, TAIL, AFTER = range(5)
    state = OUT
    skeleton = []
    payloads = []
    cur = []
    for line in text.splitlines(keepends=True):
        if state == OUT:
            if _END_RE.match(line):
                return "", [], "BEGIN の無い EVOLVE-BLOCK-END"
            skeleton.append(line)
            if _BEGIN_RE.match(line):
                state = HEAD
        elif state == HEAD:
            if _BEGIN_RE.match(line) or _END_RE.match(line):
                return "", [], "EVOLVE-BLOCK 領域に #if 骨格が無い"
            skeleton.append(line)
            if _IF_RE.match(line):
                state, cur = PAYLOAD, []
        elif state == PAYLOAD:
            if _ELSE_RE.match(line):
                payloads.append("".join(cur))
                skeleton.append(_PLACEHOLDER)
                skeleton.append(line)
                state = TAIL
            elif _ENDIF_RE.match(line) or _BEGIN_RE.match(line) or _END_RE.match(line):
                return "", [], "#if 枝が #else で閉じていない (骨格の三枝が壊れている)"
            else:
                cur.append(line)
        elif state == TAIL:
            if _BEGIN_RE.match(line) or _END_RE.match(line):
                return "", [], "stock 枝 (#else) が #endif で閉じていない"
            skeleton.append(line)
            if _ENDIF_RE.match(line):
                state = AFTER
        elif state == AFTER:
            if _BEGIN_RE.match(line):
                return "", [], "END の無い EVOLVE-BLOCK-BEGIN (入れ子)"
            skeleton.append(line)
            if _END_RE.match(line):
                state = OUT
    if state != OUT:
        return "", [], "EVOLVE-BLOCK 領域が閉じていない (END 欠落等)"
    return "".join(skeleton), payloads, ""


def _check_evolve_edit(old: str, new: str) -> str:
    """許可ソースへの書き込み検査。空文字 = 許可、非空 = 拒否理由。"""
    sk_old, pl_old, err = _parse_regions(old)
    if err:
        return (f"現ファイルの EVOLVE-BLOCK 構造が壊れている ({err})。template patch "
                "(patches/silo-backoff-fixed.patch) 未適用なら Bash の git apply で適用する")
    sk_new, pl_new, err = _parse_regions(new)
    if err:
        return f"書き込み後の EVOLVE-BLOCK 構造が壊れる: {err}"
    if sk_old != sk_new:
        return ("変更が EVOLVE-BLOCK の #if 枝 (payload) の外に及ぶ。マーカー・#if/#else "
                "骨格・stock 枝・領域外は不可触 (人間 template 専有, phase3.md)")
    for old_p, new_p in zip(pl_old, pl_new):
        if old_p == new_p:
            continue
        vio = _payload_violations(new_p)
        if vio:
            return "payload 違反: " + "; ".join(vio)
    return ""


def _apply_edits(old: str, tool_name: str, tool_input: dict):
    """Edit/MultiEdit を再現して新内容を返す。判定不能は (None, 理由)。"""
    edits = (tool_input.get("edits") if tool_name == "MultiEdit"
             else [tool_input])
    text = old
    for e in edits or []:
        old_s = e.get("old_string", "")
        new_s = e.get("new_string", "")
        if not old_s:
            return None, "old_string が空"
        n = text.count(old_s)
        if n == 0:
            return None, "old_string が現ファイルに見つからない"
        if e.get("replace_all"):
            text = text.replace(old_s, new_s)
        elif n > 1:
            return None, "old_string が一意でない (replace_all 無し)"
        else:
            text = text.replace(old_s, new_s, 1)
    return text, ""


def _protected_artifact(rp: str, repo_root: str) -> str:
    """proof-chain 成果物なら理由ラベル、そうでなければ空文字。"""
    camp = os.path.join(repo_root, "output", "campaigns") + os.sep
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
    root = repo_root or _repo_root()
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not path:
        return True, ""                     # パス無し = ツール側が失敗する。管轄外
    rp = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))

    label = _protected_artifact(rp, root)
    if label:
        return False, (
            f"{label} への直接書き込みは拒否 (規律2)。COMMIT/fitness を書く唯一の"
            "経路は pipeline.evaluate()。verifier を迂回した成果物の更新は不可")

    sub = os.path.join(root, "external", "ccbench")
    if rp == sub or rp.startswith(sub + os.sep):
        rel = os.path.relpath(rp, sub)
        if tool_name == "NotebookEdit":
            return False, "external/ccbench への NotebookEdit は編集面外 (D24)"
        if rel not in EVOLVE_BLOCK_SOURCES:
            return False, (
                f"external/ccbench の編集面は EVOLVE-BLOCK ソース {EVOLVE_BLOCK_SOURCES} "
                f"のみ ({rel} は不可)。Options.cmake 等は digest 非被覆 = 偽 cache hit 源 "
                "(F1/D24) のため人間 template 専有 — template 改訂は patches/ + git apply で")
        try:
            with open(rp, encoding="utf-8") as f:
                old = f.read()
        except OSError as e:
            return False, f"対象を読めない ({e}) — 判定不能のため fails-closed で拒否"
        if tool_name == "Write":
            new = tool_input.get("content", "")
        else:
            new, why = _apply_edits(old, tool_name, tool_input)
            if new is None:
                return False, f"Edit を再現できない ({why}) — fails-closed で拒否"
        reason = _check_evolve_edit(old, new)
        if reason:
            return False, reason
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
                                  "build-variants")):
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
