#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 hook: Bash 経由の成果物書き込み防壁 (規律2 第二防壁, phase3.md タスク3)。

guard_write.py (Edit/Write hook) は Bash の `echo >> wal.jsonl` を見ない — その穴を
塞ぐ。PreToolUse (Bash) で発火し、コマンドが防護対象を**書く/消す/動かす**兆候を
示したら exit 2 で拒否する。

【設計 = allowlist 反転 (敵対レビュー 2026-07-02 の教訓)】
初版は「書き込みコマンドを列挙して拒否」する blocklist だったが、シェルの書き込み
経路は事実上無限 (find -delete / awk -i inplace / ex/ed / git mv / サブシェルで head
を隠す / >& リダイレクト …) で列挙しきれず多数の迂回が実証された。読み取り専用
コマンドの集合は小さく安定しているので反転する: **防護対象トークンに触れる
セグメントは、その head が既知の読み取り専用でなければ拒否 (未知コマンド = fails-
closed で拒否)。** これで新種の writer は列挙せずとも自動的に落ちる。

判定 (shlex でクォートを解決してからトークン単位で見る):
1. 防護対象 (末端 = WAL/campaign.lock/runs/build-variants、祖先 = campaign dir /
   ccbench root) がコマンドに現れない → 即許可 (fast path、通常作業を妨げない)。
2. 不透明構文 ($()/バッククォート/プロセス置換/eval/xargs) が防護対象と同居 →
   分類不能 = fails-closed で拒否。
3. shlex (punctuation_chars) でクォート aware にトークン化し演算子でセグメント分割。
   - リダイレクト (>, >>, >&, &>) の先が末端防護対象なら head 不問で拒否。
   - **末端**に触れるセグメント: head が read-only allowlist に無ければ拒否。
   - **祖先**にのみ触れるセグメント: head が破壊系 (rm/mv/find -delete/git clean 等)
     なら拒否 (祖先 dir 丸ごとの削除・移動で proof chain が消える = 規律2)。read や
     reports/insights への書き込みは通す。

限界 (正直に): テキスト検査の第二防壁であり sandbox ではない。変数展開でパスを
組み立てる・スクリプトファイル越し・python スクリプト内での書き込みは見えない
(スクリプトファイルは監査可能な作業物として許可する)。`git commit -m "$(...)"` の
heredoc はメッセージに防護トークンが入ると opaque 判定で拒否される — 単一行 -m か
`git commit -F <file>` で回避する。一次防壁は pipeline.evaluate の fails-closed 設計と
WAL の proof chain、事後は規律6 の監査。
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

# ---- 防護対象 (トークン単位で判定) ----
# 末端: 中身の改変も削除も規律2 違反 (WAL 偽造 / proof chain 破壊)。
_LEAF_RE = re.compile(
    r"(?:^|/)wal\.jsonl(?:$|[/?])"
    r"|(?:^|/)campaign\.lock(?:$|[/?])"
    r"|output/campaigns/[^\s]*?/runs(?:/|$)"
    r"|build-variants")
# fast path トリガ (広い): これが現れなければ即許可。祖先の祖先 (rm -rf output)
# まで精査に載せるため、防護ツリーの構成語を広く含める。精査自体はトークン単位の
# 厳密パターン (_LEAF_RE / _overlaps_protected_tree) が担うので、広い分は read で落ちる。
_MENTION_RE = re.compile(
    r"wal\.jsonl|campaign\.lock|build-variants"
    r"|output/campaigns|external/ccbench"
    r"|\boutput\b|\bexternal\b|\bccbench\b|\bcampaigns\b")
# proof chain を配下に持つツリー root (削除・移動・展開で丸ごと消える対象)。
_PROTECTED_TREES = ("output/campaigns", "external/ccbench")

# 不透明構文: 中で何が起きるかテキストから追えない。防護対象と同居したら拒否。
_OPAQUE_RE = re.compile(r"\$\(|`|<\(|>\(|\beval\b|\bxargs\b")

# リダイレクト演算子トークン (shlex punctuation_chars 後)。>& は fd 複製 (2>&1) と
# file 版 (>&file) 両用なので、次トークンが数値でなければ file とみなす。
_REDIR_OPS = frozenset({">", ">>", ">&", "&>", "&>>"})

# セグメント境界となる演算子・シェル構文語 (制御構文で head を隠す攻撃対策)。
_SEG_OPS = frozenset({";", "&", "&&", "|", "||", "(", ")", "{", "}", "\n"})
_SHELL_WORDS = frozenset({
    "if", "then", "elif", "else", "fi", "for", "while", "until", "do", "done",
    "case", "esac", "select", "function", "!", "[[", "]]", "time", "coproc"})
_WRAPPERS = frozenset({"sudo", "env", "nohup", "time", "nice", "ionice", "stdbuf",
                       "timeout", "numactl", "taskset", "setsid", "command", "exec"})

# ---- 読み取り専用 allowlist (末端に触れてよい head) ----
_PURE_READERS = frozenset({
    "cat", "tac", "grep", "egrep", "fgrep", "rg", "ag", "zgrep", "jq", "yq",
    "head", "tail", "less", "more", "most", "wc", "nl", "cut", "tr", "od", "xxd",
    "hexdump", "strings", "stat", "file", "ls", "dir", "vdir", "diff", "cmp",
    "comm", "column", "fold", "fmt", "rev", "paste", "join", "expand", "unexpand",
    "md5sum", "sha1sum", "sha256sum", "sha512sum", "cksum", "b2sum",
    "basename", "dirname", "realpath", "readlink", "echo", "printf", "true",
    "false", "test", "pwd", "date", "seq", "cd", "pushd", "popd", "which", "type"})
# git の読み取り/proof-chain 非破壊サブコマンド (checkout/restore/clean/rm/reset/
# stash/mv は含めない → それらは head=git でも read-only 判定 False = 拒否)。
_GIT_READ_SUBS = frozenset({
    "log", "diff", "show", "status", "ls-files", "ls-tree", "blame", "cat-file",
    "rev-parse", "rev-list", "describe", "shortlog", "reflog", "grep", "add",
    "commit", "config", "remote", "branch", "tag", "fetch", "whatchanged"})
# inline コードを取るインタプリタ (スクリプトファイル実行のみ許可、-c/-e/-i は拒否)。
_INTERP = frozenset({"python", "python2", "python3", "perl", "ruby", "node",
                     "bash", "sh", "zsh", "dash", "ksh"})
# 防護ツリーを丸ごと削除/移動/展開する head (祖先層)。ファイル単位で書く
# cp/tee/sed/dd 等はここに含めない — それらが末端に触れれば末端層 (read-only 判定)
# が捕える。祖先層は「dir ごと消す/動かす」= 末端まとめて破壊する head に絞る。
_TREE_MUTATORS = frozenset({"rm", "rmdir", "shred", "unlink", "mv", "tar", "rsync",
                            "install", "mkfs"})
_GIT_DESTROY_SUBS = frozenset({"clean", "rm", "checkout", "restore", "reset",
                               "stash", "mv"})


def _normalize_redirs(command: str) -> str:
    """`&>>`/`&>`/`>|` を `>>`/`>`/`>` に正規化 (shlex が綺麗に割れる形へ)。"""
    command = command.replace("&>>", " >> ").replace("&>", " > ")
    return command.replace(">|", " > ")


def _tokenize(command: str):
    """shlex (punctuation_chars) でクォート aware にトークン化。ValueError は None。"""
    lx = shlex.shlex(_normalize_redirs(command), posix=True,
                     punctuation_chars=";()<>|&")
    lx.whitespace_split = True
    try:
        return list(lx)
    except ValueError:
        return None


def _segments(tokens):
    """トークン列を演算子・シェル構文語でセグメントに割る (演算子トークンは落とす)。"""
    segs, cur = [], []
    for t in tokens:
        if t in _SEG_OPS:
            if cur:
                segs.append(cur)
                cur = []
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs


def _head_and_args(seg):
    """env 代入・wrapper・シェル構文語を剥いで実 head (basename) と残り引数を返す。"""
    i = 0
    while i < len(seg):
        t = seg[i]
        if re.match(r"^\w+=", t):                 # FOO=bar 前置
            i += 1
            continue
        base = os.path.basename(t)
        if base in _SHELL_WORDS or t in ("in",):  # for X in ...; do の in
            i += 1
            continue
        if base in _WRAPPERS:
            i += 1
            # timeout の期間引数・wrapper 自身のフラグを飛ばす
            while i < len(seg) and (seg[i].startswith("-")
                                    or re.fullmatch(r"\d+[smhd]?", seg[i])
                                    or seg[i] in ("-c",)):
                i += 1
            continue
        return base, seg[i + 1:]
    return "", []


def _is_read_only(head: str, args) -> bool:
    """head が末端防護対象に触れてよい (中身を変えない) 読み取り専用操作か。"""
    if head in _PURE_READERS:
        return True
    if head == "dd":
        # dd if=WAL of=/tmp (読み) は許可、of= が末端 (書き) なら拒否
        return not any(a.startswith("of=") and _LEAF_RE.search(a) for a in args)
    if head == "find":
        return not any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir")
                       or a.startswith("-fprint") for a in args)
    if head == "sed":
        return not any(a == "-i" or a.startswith("-i") or a.startswith("--in-place")
                       for a in args)
    if head in ("awk", "gawk", "mawk"):
        return "-i" not in args and not any(a.startswith("--include") for a in args)
    if head == "sort":
        return not any(a in ("-o", "--output") or a.startswith("-o")
                       or a.startswith("--output=") for a in args)
    if head == "git":
        sub = next((a for a in args if not a.startswith("-")), "")
        return sub in _GIT_READ_SUBS
    if head in _INTERP:
        # inline コード (-c/-e) や in-place (-i/-pe/-ne 等 perl/ruby) は拒否。
        # 素の `python3 script.py wal.jsonl` (レポート生成) だけ許可。
        for a in args:
            if a in ("-c", "-e"):
                return False
            if a.startswith("-") and ("e" in a[1:] or "i" in a[1:]):
                return False   # perl -pe / -i / -ne / ruby -i 等
        return True
    return False                                  # 未知 head = fails-closed


def _overlaps_protected_tree(token: str) -> bool:
    """token が防護ツリー (campaign dir / ccbench root) と祖先-子孫いずれかで重なるか。

    - `output` は `output/campaigns` の祖先 → 削除で防護対象が消える。
    - `output/campaigns/c` は子孫 → 配下に runs (末端) を持つ。
    セパレータ境界で判定 (`output/campaignsX` の誤爆を避ける)。末端も直接拾う。"""
    if _LEAF_RE.search(token):
        return True
    p = os.path.normpath(token).strip("/")
    for tree in _PROTECTED_TREES:
        if p == tree or tree.startswith(p + "/") or p.startswith(tree + "/"):
            return True
    return False


def _path_args(args):
    """フラグ・`--` を除いたパス様引数 (削除/移動対象の候補)。"""
    return [a for a in args if not a.startswith("-") and a != "--"]


def _destroys_protected_tree(head: str, args) -> bool:
    """head が防護ツリーを丸ごと削除/移動/展開する操作か。"""
    if head == "git":
        if "clean" in args:                       # cwd 再帰で untracked WAL を消す
            return True
        if any(a in _GIT_DESTROY_SUBS for a in args):
            return any(_overlaps_protected_tree(t) for t in _path_args(args))
        return False
    if head == "find":
        if any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir") for a in args):
            return any(_overlaps_protected_tree(t) for t in _path_args(args))
        return False
    if head in _TREE_MUTATORS:
        return any(_overlaps_protected_tree(t) for t in _path_args(args))
    return False


def _redirect_hits_leaf(seg) -> bool:
    """セグメント内でリダイレクト先が末端防護対象なら True。"""
    for i, t in enumerate(seg):
        if t in _REDIR_OPS and i + 1 < len(seg):
            tgt = seg[i + 1]
            if t == ">&" and tgt.isdigit():       # 2>&1 等の fd 複製は無視
                continue
            if _LEAF_RE.search(tgt):
                return True
    return False


def decide(command: str) -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    if not _MENTION_RE.search(command):
        return True, ""                            # fast path

    if _OPAQUE_RE.search(command):
        return False, ("防護対象 (WAL/campaign.lock/build-variants/campaign dir) と"
                       "不透明構文 ($()/` `/プロセス置換/eval/xargs) の同居は分類不能 "
                       "= fails-closed。読むだけなら cat/grep/jq で、正規の書き込みは "
                       "pipeline.evaluate() で、コミットは単一行 -m か -F <file> で")

    tokens = _tokenize(command)
    if tokens is None:
        if _LEAF_RE.search(command) or any(
                _overlaps_protected_tree(w) for w in command.split()):
            return False, ("防護対象を含むコマンドを解析できない (クォート不整合等) — "
                           "fails-closed で拒否")
        return True, ""                            # 防護対象に触れない解析不能は素通し

    for seg in _segments(tokens):
        head, args = _head_and_args(seg)
        if _redirect_hits_leaf(seg):
            return False, ("リダイレクト先が末端防護対象。WAL/campaign.lock/build-cache "
                           "を書く唯一の経路は pipeline.evaluate() (規律2)")
        if _destroys_protected_tree(head, args):
            return False, (f"campaign dir / ccbench root を破壊する操作 ({head})。"
                           "proof chain を配下ごと削除/移動/展開するのは不可 (規律2)")
        if any(_LEAF_RE.search(t) for t in seg) and not _is_read_only(head, args):
            return False, (f"末端防護対象に触れる非読み取りコマンド ({head or '?'})。"
                           "WAL/campaign.lock/build-cache の書き換え・削除・移動は不可 "
                           "(規律2)。読み取りは cat/grep/jq/head/tail 等で")
    return True, ""


def main() -> int:
    raw = sys.stdin.read()                 # 例外時の fails-closed 判定に使うため一度で読む
    try:
        payload = json.loads(raw)
        command = (payload.get("tool_input") or {}).get("command", "")
        allow, reason = decide(command)
    except Exception as e:  # noqa: BLE001 — hook 自身の不具合で全 Bash を止めない。
        # ただし生入力に防護対象が見えるときだけ fails-closed。
        if _MENTION_RE.search(raw):
            print(f"guard_bash hook 内部エラー ({type(e).__name__}: {e}) — 防護対象を"
                  "含むため fails-closed で拒否", file=sys.stderr)
            return 2
        return 0
    if not allow:
        print(f"[guard_bash] 拒否: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
