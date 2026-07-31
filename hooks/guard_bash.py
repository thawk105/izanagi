#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 hook: Bash 経由の成果物書き込み防壁 (規律2 第二防壁, phase3.md タスク3 / 方針 A)。

guard_write.py (Edit/Write hook) は Bash の `echo >> wal.jsonl` を見ない — その穴を
塞ぐ。PreToolUse (Bash) で発火し、コマンドが防護対象を**書く/消す/動かす**兆候を
示したら exit 2 で拒否する。

別系統の運用防壁として、canonical ``pegasus_policy`` が Pegasus login と分類した
場合は、既知の直接 pytest / build command 形だけを拒否する。site 観測が成立しない
場合も、その既知 heavy 候補だけを安全側へ止める。この判定は既存の wrapper /
compound parser と一段の shell ``-c`` 再解析に限定した best-effort 防壁である。

【設計 = allowlist 反転 (敵対レビュー 2026-07-02 の教訓)】
初版は「書き込みコマンドを列挙して拒否」する blocklist だったが、シェルの書き込み
経路は事実上無限 (find -delete / awk -i inplace / ex/ed / git mv / サブシェルで head
を隠す / >& リダイレクト …) で列挙しきれず多数の迂回が実証された。読み取り専用
コマンドの集合は小さく安定しているので反転する: **防護対象トークンに触れる
セグメントは、その head が既知の読み取り専用でなければ拒否 (未知コマンド = fails-
closed で拒否)。** これで新種の writer は列挙せずとも自動的に落ちる。

判定 (shlex でクォートを解決してからトークン単位で見る):
1. 防護対象 (末端 = WAL/campaign.lock/runs/build-variants、ツリー = output/campaigns /
   external/ccbench) がコマンドに現れない → 即許可 (fast path、通常作業を妨げない)。
2. 末端/防護ツリーの**パス字面**と不透明構文 ($()/バッククォート/プロセス置換/<<<
   /eval/xargs) が同居 → 分類不能 = fails-closed で拒否 (パス字面が無ければ通す —
   `--output=/tmp/x $(nproc)` のような無関係コマンドを巻き込まない, F-FP-4)。
3. shlex (punctuation_chars) でクォート aware にトークン化し演算子でセグメント分割。
   - リダイレクト (>, >>, >&, &>) の先が末端防護対象なら head 不問で拒否。
   - **末端**に引数で触れるセグメント: head が read-only allowlist に無ければ拒否。
     例外 (F-FP-1): head 自身が build-variants 配下のバイナリ = **実行** (計測の正道)
     は書き込みでないので通す。cmake/make/ninja (ビルドシステム) の build-variants
     生成も正当経路 (`cmake -E` の任意コピーは除く)。perf は `perf <sub> [opts] --
     <cmd>` の明示形なら子コマンドを実 head として検査する。
   - **防護ツリー破壊**: external/ccbench は全域 (祖先/自身/子孫)、output/campaigns は
     祖先・自身・campaign dir 単位の削除/移動を拒否。campaign dir 配下の reports/ 等
     proof-chain でない子孫の mv/rm は通す (F-FP-2、末端はどの深さでも拒否)。glob
     (`output/*`) はメタ文字前の prefix で重なり判定 (リテラル prefix のみ, GB2-1)。
   - **bare/stdin インタプリタ** (`... | python3` / `python3 -`) が防護対象パス字面と
     同居 → コードの中身を追えないので fails-closed (GB2-3)。

限界 (正直に): テキスト検査の第二防壁であり sandbox ではない。変数展開でパスを
組み立てる・スクリプトファイル越し・`rm -rf out*` のような部分 glob は見えない
(スクリプトファイルは監査可能な作業物として許可する)。実効保証は一次防壁 =
pipeline.evaluate の fails-closed 設計と WAL の proof chain、事後は規律6 の監査。
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS_DIR = os.path.join(_REPO_ROOT, "tools")
if _TOOLS_DIR in sys.path:
    sys.path.remove(_TOOLS_DIR)
sys.path.insert(0, _TOOLS_DIR)

import pegasus_policy  # noqa: E402 — direct hook execution needs <repo>/tools bootstrap


def _repo_root() -> str:
    # hooks/guard_bash.py = <repo>/hooks/guard_bash.py
    return _REPO_ROOT


# ---- 防護対象 (トークン単位で判定) ----
# 末端: 中身の改変も削除も規律2 違反 (WAL 偽造 / proof chain 破壊)。
_LEAF_RE = re.compile(
    r"(?:^|/)wal\.jsonl(?:$|[/?])"
    r"|(?:^|/)campaign\.lock(?:$|[/?])"
    r"|output/campaigns/[^\s]*?/runs(?:/|$)"
    r"|build-variants")
# 防護ツリーのパス字面 (opaque 同居・bare interpreter 判定の精密トリガ)。
_TREE_LITERAL_RE = re.compile(r"output/campaigns|external/ccbench")
# fast path トリガ (広い): これが現れなければ即許可。祖先の祖先 (rm -rf output)
# まで精査に載せるため、防護ツリーの構成語を広く含める。精査自体はトークン単位の
# 厳密パターン (_LEAF_RE / _tree_violation) が担うので、広い分は read で落ちる。
# 裸単語は直前が `-`/単語構成字なら除外 (`--output=` フラグ等の誤爆防止, F-FP-4)。
_MENTION_RE = re.compile(
    r"wal\.jsonl|campaign\.lock|build-variants"
    r"|output/campaigns|external/ccbench"
    r"|(?<![-\w])(?:output|external|ccbench|campaigns)\b")
# proof chain を配下に持つツリー root。
_CCBENCH_TREE = "external/ccbench"     # 全域防護 (submodule working-tree = identity の実体)
_CAMPAIGN_TREE = "output/campaigns"    # 祖先/自身/campaign dir 単位で防護 (子孫は末端のみ)

# 不透明構文: 中で何が起きるかテキストから追えない。防護対象パス字面と同居したら拒否。
# `<<` は here-doc (本文コードが追えない) と here-string `<<<` を両方捕える
# (2026-07-04 敵対検証: GB2-2 の `<<<` fix が `<<` 綴りを取り残し heredoc 経由の bare
# interpreter で防護対象を書けた)。
_OPAQUE_RE = re.compile(r"\$\(|`|<<|<\(|>\(|\beval\b|\bxargs\b")

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
# wrapper のオプション値として読み飛ばす形: timeout の期間・taskset/numactl の
# CPU リスト (0-47 / 0,2,4-6) と 16 進マスク (0xff) (F-FP-3)。
_WRAPPER_VAL_RE = re.compile(r"\d+[smhd]?|\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*"
                             r"|0[xX][0-9a-fA-F]+")

# ---- 読み取り専用 allowlist (末端に触れてよい head) ----
_PURE_READERS = frozenset({
    "cat", "tac", "grep", "egrep", "fgrep", "rg", "ag", "zgrep", "jq", "yq",
    "head", "tail", "less", "more", "most", "wc", "nl", "cut", "tr", "od", "xxd",
    "hexdump", "strings", "stat", "file", "ls", "dir", "vdir", "diff", "cmp",
    "comm", "column", "fold", "fmt", "rev", "paste", "join", "expand", "unexpand",
    "md5sum", "sha1sum", "sha256sum", "sha512sum", "cksum", "b2sum",
    "basename", "dirname", "realpath", "readlink", "echo", "printf", "true",
    "false", "test", "pwd", "date", "seq", "cd", "pushd", "popd", "which", "type",
    # バイナリ/シンボル検査 (規律1 の nm 観測者効果検証を手でも回せるように。書き込み
    # 不能ツールなので規律2 を弱めない, 2026-07-04 敵対検証 false-positive):
    "nm", "objdump", "readelf", "ldd", "size", "addr2line", "c++filt",
    # ディスク使用量・圧縮読み (純読み取り, 同上):
    "du", "zcat", "zless", "zmore", "zdiff"})
# git の読み取り/proof-chain 非破壊サブコマンド (checkout/restore/clean/rm/reset/
# stash/mv は含めない → それらは head=git でも read-only 判定 False = 拒否)。
# config も含めない: `git config -f <protected>` は書き込み invocation (GB2-4)。
_GIT_READ_SUBS = frozenset({
    "log", "diff", "show", "status", "ls-files", "ls-tree", "blame", "cat-file",
    "rev-parse", "rev-list", "describe", "shortlog", "reflog", "grep", "add",
    "commit", "remote", "branch", "tag", "fetch", "whatchanged"})
# inline コードを取るインタプリタ (スクリプトファイル実行のみ許可、-c/-e/-i/
# bare stdin 実行は拒否)。
_INTERP = frozenset({"python", "python2", "python3", "perl", "ruby", "node",
                     "bash", "sh", "zsh", "dash", "ksh"})
# ビルドシステム (build-variants を生成/更新する正当経路。cmake -E の任意コピーは除外)。
_BUILDERS = frozenset({"cmake", "make", "ninja"})
# 防護ツリーを丸ごと削除/移動/展開する head (祖先層)。ファイル単位で書く
# cp/tee/sed/dd 等はここに含めない — それらが末端に触れれば末端層 (read-only 判定)
# が捕える。祖先層は「dir ごと消す/動かす」= 末端まとめて破壊する head に絞る。
# tar/rsync は _destroys_protected_tree で read/write を個別判別する (backup=読みは通す、
# 展開/mirror INTO=書きは拒否, 2026-07-04 敵対検証 F-FP)。ここには「常に破壊」の head だけ。
_TREE_MUTATORS = frozenset({"rm", "rmdir", "shred", "unlink", "mv", "install", "mkfs"})
_GIT_DESTROY_SUBS = frozenset({"clean", "rm", "checkout", "restore", "reset",
                               "stash", "mv"})


def _normalize_redirs(command: str) -> str:
    """`&>>`/`&>`/`>|` を `>>`/`>`/`>` に正規化 (shlex が綺麗に割れる形へ)。"""
    command = command.replace("&>>", " >> ").replace("&>", " > ")
    return command.replace(">|", " > ")


def _tokenize(command: str):
    """shlex (punctuation_chars) でクォート aware にトークン化。ValueError は None。

    改行はセグメント境界にする (2026-07-04 敵対検証: shlex(whitespace_split) は改行を
    whitespace として食うため改行トークンが出ず、複数行コマンドが 1 セグメントに潰れて
    先頭行の read-only head が後続行の writer を隠蔽していた)。行継続 (バックスラッシュ+
    改行) は先に splice し、残る (クォート外の) 改行を `;` に正規化する。クォート内の改行は
    shlex がトークン内文字として保持するので `;` はセグメント境界にならない (影響しない)。"""
    command = re.sub(r"\\\n", "", command)          # 行継続 splice (翻訳フェーズ2 相当)
    command = command.replace("\n", " ; ")          # 残る改行 = セグメント境界
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
    _, head, args = _head_token_and_args(seg)
    return head, args


class _EnvSplitError(ValueError):
    """heavy classifier が env split-string payload を安全に展開できない。"""


_ENV_SPLIT_MAX_DEPTH = 16
_ENV_SPLIT_INVALID_LABEL = "env split-string (invalid payload)"
_ENV_SPLIT_SPECIAL_ESCAPE_RE = re.compile(r"\\(?:[cfnrtv]|_)")


def _split_env_payload(payload: str) -> list[str]:
    """GNU env の split-string payload を command argv 相当に分割する。

    shell 演算子を実行構文として扱わないため ``_tokenize`` ではなく
    ``shlex.split`` を使う。split-string 自身の quote 不整合は、外側 shell command
    が構文上 valid でも起き得るため heavy classifier では曖昧扱いにする。GNU env
    固有の空白/control escape (``\\_`` / ``\\c`` 等) も shlex と意味が異なるため、
    head を過少分類せず曖昧扱いにする。
    """
    if _ENV_SPLIT_SPECIAL_ESCAPE_RE.search(payload):
        raise _EnvSplitError(
            "coreutils-specific split-string escape is unsupported")
    try:
        return shlex.split(payload, comments=False, posix=True)
    except ValueError as exc:
        raise _EnvSplitError(str(exc)) from exc


def _head_token_and_args(
        seg, *, expand_env_split: bool = False, env_split_depth: int = 0):
    """wrapper 等を剥いだ実 head の元token、basename、残り引数を返す。"""
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
            if base == "env":
                while i < len(seg):
                    option = seg[i]
                    if option == "--":
                        i += 1
                        break
                    if option in ("-S", "--split-string"):
                        if i + 1 >= len(seg):
                            if expand_env_split:
                                raise _EnvSplitError(
                                    f"{option} requires a payload")
                            i += 2
                            continue
                        if expand_env_split:
                            if env_split_depth >= _ENV_SPLIT_MAX_DEPTH:
                                raise _EnvSplitError(
                                    "split-string nesting is too deep")
                            expanded = _split_env_payload(seg[i + 1])
                            return _head_token_and_args(
                                ["env", *expanded, *seg[i + 2:]],
                                expand_env_split=True,
                                env_split_depth=env_split_depth + 1,
                            )
                        i += 2
                        continue
                    payload = None
                    if option.startswith("--split-string="):
                        payload = option.partition("=")[2]
                    elif option.startswith("-S") and option != "-S":
                        payload = option[2:]
                    if payload is not None:
                        if expand_env_split:
                            if env_split_depth >= _ENV_SPLIT_MAX_DEPTH:
                                raise _EnvSplitError(
                                    "split-string nesting is too deep")
                            expanded = _split_env_payload(payload)
                            return _head_token_and_args(
                                ["env", *expanded, *seg[i + 1:]],
                                expand_env_split=True,
                                env_split_depth=env_split_depth + 1,
                            )
                        i += 1
                        continue
                    if option in ("-u", "--unset", "-C", "--chdir"):
                        i += 2
                        continue
                    if option.startswith("-") or re.match(r"^\w+=", option):
                        i += 1
                        continue
                    break
                continue
            if base == "timeout":
                while i < len(seg) and seg[i].startswith("-"):
                    option = seg[i]
                    i += 1
                    if option in ("-s", "--signal", "-k", "--kill-after"):
                        i += 1
                if i < len(seg):                  # duration
                    i += 1
                continue
            if base == "taskset":
                while i < len(seg) and seg[i].startswith("-"):
                    i += 1
                if i < len(seg):                  # mask / cpu-list
                    i += 1
                continue
            # wrapper 自身のフラグ・オプション値 (期間 / CPU リスト / 16 進マスク) を飛ばす
            while i < len(seg) and (seg[i].startswith("-")
                                    or _WRAPPER_VAL_RE.fullmatch(seg[i])):
                i += 1
            continue
        return t, base, seg[i + 1:]
    return "", "", []


_PYTHON_HEAD_RE = re.compile(r"python(?:[23](?:\.\d+)?)?\Z", re.ASCII)
_SHELL_C_HEADS = frozenset({"bash", "sh", "zsh", "dash", "ksh"})


def _shell_c_command(args):
    """shell の `-c` / `-lc` 形から command string を一つ返す。"""
    for i, arg in enumerate(args):
        if arg == "--command" or (
                arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]):
            if i + 1 < len(args):
                return args[i + 1]
            return None
    return None


def _is_python_m_pytest(args) -> bool:
    """interpreter option列の `-m pytest` だけを認識し、script引数は見ない。"""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-m":
            return i + 1 < len(args) and args[i + 1] == "pytest"
        if arg == "--" or not arg.startswith("-"):
            return False
        if arg == "-c" or arg.startswith("-c"):
            return False
        if arg in ("-W", "-X", "--check-hash-based-pycs"):
            i += 2
        else:
            i += 1
    return False


def _heavy_candidates(command: str, *, shell_depth: int = 0) -> tuple[str, ...]:
    """既知の直接 build/test head を返す。一段の shell `-c` だけ再解析する。"""
    tokens = _tokenize(command)
    if tokens is None:
        return ()

    found = []
    for seg in _segments(tokens):
        try:
            _, head, args = _head_token_and_args(
                seg, expand_env_split=True)
        except _EnvSplitError:
            found.append(_ENV_SPLIT_INVALID_LABEL)
            continue
        if not head:
            continue
        if head in ("pytest", "py.test"):
            found.append("pytest")
            continue
        if _PYTHON_HEAD_RE.fullmatch(head) and _is_python_m_pytest(args):
            found.append("python -m pytest")
            continue
        if head == "cmake" and any(
                arg == "--build" or arg.startswith("--build=") for arg in args):
            found.append("cmake --build")
            continue
        if head in ("make", "ninja", "ctest"):
            found.append(head)
            continue
        if shell_depth == 0 and head in _SHELL_C_HEADS:
            nested = _shell_c_command(args)
            if nested is not None:
                found.extend(_heavy_candidates(nested, shell_depth=1))
    return tuple(found)


def _heavy_gate(command: str, site_observer) -> tuple[bool, str]:
    """heavy候補だけsite policyを観測し、login/観測不成立をfail-closedにする。"""
    candidates = _heavy_candidates(command)
    if not candidates:
        return True, ""

    label = ", ".join(dict.fromkeys(candidates))
    try:
        observed = site_observer()
        if not isinstance(observed, pegasus_policy.SiteObservation):
            raise pegasus_policy.SitePolicyError(
                "site observer returned an invalid observation")
        validated = pegasus_policy.classify_site(
            observed.hostname_raw,
            observed.pbs_job_id_raw,
            observed.affinity_cpus,
        )
        if validated != observed:
            raise pegasus_policy.SitePolicyError(
                "site observation is inconsistent with canonical policy")
    except Exception as exc:  # noqa: BLE001 — heavy候補だけ安全側へ停止する
        return False, (
            f"高負荷候補 ({label}) のsite観測が不成立 "
            f"({type(exc).__name__}: {exc}) — fails-closed。"
            "repository正規runner/submitterを使用する")

    if observed.site_kind is pegasus_policy.PEGASUS_LOGIN:
        return False, (
            f"Pegasus login node での直接高負荷command ({label}) は拒否。"
            "テストは tools/run_tests.py、投入は "
            "tools/pegasus/submit_tests.py を使用する")
    if observed.site_kind in (
            pegasus_policy.PEGASUS_COMPUTE, pegasus_policy.OTHER):
        return True, ""
    return False, (
        f"高負荷候補 ({label}) のsite分類が不明 — fails-closed。"
        "repository正規runner/submitterを使用する")


def _stdin_script(head: str, args) -> bool:
    """interpreter がスクリプトファイル無しで stdin/pipe のコードを実行する形か。"""
    if head not in _INTERP:
        return False
    if "-" in args:
        return True                               # 明示 stdin 実行
    return not any(not a.startswith("-") for a in args)   # 非フラグ引数ゼロ = bare


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
        # inline コード (-c/-e)・in-place (-i/-pe/-ne 等)・bare/stdin 実行は拒否。
        # 素の `python3 script.py wal.jsonl` (レポート生成) だけ許可。
        for a in args:
            if a in ("-c", "-e"):
                return False
            if a.startswith("-") and a != "-" and ("e" in a[1:] or "i" in a[1:]):
                return False   # perl -pe / -i / -ne / ruby -i 等
        return not _stdin_script(head, args)
    return False                                  # 未知 head = fails-closed


def _glob_prefix(token: str) -> str:
    """glob メタ文字 (*?[) より前のリテラル prefix (GB2-1: `output/*` の重なり判定用)。"""
    return re.split(r"[*?\[]", token, maxsplit=1)[0]


def _repo_relative(token: str, repo_root: str) -> str:
    """glob prefix (~ 展開済) を repo_root 相対に正規化して返す。

    2026-07-04 敵対検証: 絶対パス (`/home/.../output/campaigns/c`)・`~/…` は、strip 後
    `home/…` 前置ゆえ相対リテラル `output/campaigns` を prefix に持たず、防護ツリー破壊
    (`rm -rf <abs>/output/campaigns/c`) が素通りしていた。repo_root で相対化してから既存の
    厳密照合に載せる。repo 外絶対 (`/tmp/output/campaigns`) は相対化せず素通り = 防護外
    (正しい)。`$VAR` 展開はシェルの実行時展開ゆえ hook からは追えない (docstring の限界)。"""
    raw = os.path.expanduser(_glob_prefix(token))
    if os.path.isabs(raw):
        ap = os.path.normpath(raw)
        root = os.path.normpath(repo_root) if repo_root else ""
        if root and (ap == root or ap.startswith(root + os.sep)):
            return os.path.relpath(ap, root)      # repo 内絶対 → 相対
        return ap.strip("/")                       # repo 外絶対 → 照合で外れる
    return os.path.normpath(raw).strip("/")        # 相対 → そのまま


def _tree_violation(token: str, repo_root: str = "") -> bool:
    """token の削除/移動/展開が proof chain を壊すか。

    - 末端 (_LEAF_RE) はどの深さでも壊す。
    - external/ccbench は全域 (祖先/自身/子孫) — submodule working-tree は identity の
      実体で、部分破壊も評価を汚す。
    - output/campaigns は祖先・自身・campaign dir 単位 (`output/campaigns/<id>`) まで。
      それより深い proof-chain でない子孫 (reports/ 等) は末端に触れない限り通す
      (F-FP-2: 散文・プロットの mv/rm を巻き込まない)。
    絶対パス・`~` は repo_root で相対化してから照合する (2026-07-04 敵対検証)。glob は
    メタ文字前のリテラル prefix で判定 (`output/*` → `output/` は祖先 = 拒否。`out*` の
    ような部分 glob は判定不能 = 素通り、限界として docstring に記録)。"""
    if _LEAF_RE.search(token):
        return True
    p = _repo_relative(token, repo_root)
    if not p or p == ".":
        return False
    t = _CCBENCH_TREE
    if p == t or t.startswith(p + "/") or p.startswith(t + "/"):
        return True
    t = _CAMPAIGN_TREE
    if p == t or t.startswith(p + "/"):
        return True                               # 祖先 or 自身
    if p.startswith(t + "/"):
        rel = p[len(t) + 1:]
        if "/" not in rel:
            return True                           # campaign dir 丸ごと (runs を内包)
    return False


def _path_args(args):
    """フラグ・`--` を除いたパス様引数 (削除/移動対象の候補)。"""
    return [a for a in args if not a.startswith("-") and a != "--"]


def _tar_creates(args) -> bool:
    """tar が作成モード (-c / --create、backup = 防護ツリーを**読む**方向) か。

    展開 (-x / --extract、防護ツリー内に**書く**方向) は False。判別不能も False = 安全側
    (書き扱いで tree_violation 検査に載せる)。`tar czf b.tgz output/campaigns/c` の backup は
    通し、`tar xzf b.tgz -C output/campaigns` の展開は拒否する (2026-07-04 敵対検証 F-FP)。"""
    for a in args:
        if a.startswith("--"):
            if a == "--create":
                return True
            if a in ("--extract", "--get"):
                return False
            continue
        # tar のモード文字列はハイフン有無両様 (`tar czf` / `tar -czf`)。パス様は除外。
        flags = a.lstrip("-")
        if not flags or "/" in a or a.startswith("."):
            continue
        if "x" in flags:
            return False
        if "c" in flags:
            return True
    return False


def _destroys_protected_tree(head: str, args, repo_root: str = "") -> bool:
    """head が防護ツリーを丸ごと削除/移動/展開する操作か。"""
    if head == "git":
        if "clean" in args:                       # cwd 再帰で untracked WAL を消す
            return True
        if any(a in _GIT_DESTROY_SUBS for a in args):
            return any(_tree_violation(t, repo_root) for t in _path_args(args))
        return False
    if head == "find":
        if any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir") for a in args):
            return any(_tree_violation(t, repo_root) for t in _path_args(args))
        return False
    if head == "tar":
        if _tar_creates(args):                    # backup (読み) は通す
            return False
        return any(_tree_violation(t, repo_root) for t in _path_args(args))
    if head == "rsync":
        # DEST (最後の path 引数) が防護ツリーなら mirror INTO (書き) = 拒否。
        # SRC だけが防護対象 (backup 元) の読みは通す。
        paths = _path_args(args)
        return bool(paths) and _tree_violation(paths[-1], repo_root)
    if head in _TREE_MUTATORS:
        return any(_tree_violation(t, repo_root) for t in _path_args(args))
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


def decide(command: str, repo_root: str = "", *, site_observer=None) -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    observer = pegasus_policy.observe_site if site_observer is None else site_observer
    allow, reason = _heavy_gate(command, observer)
    if not allow:
        return allow, reason

    # 絶対パス・`~` を repo 相対化するため root を realpath で確定 (2026-07-04 敵対検証)。
    root = os.path.realpath(repo_root or _repo_root())
    if not _MENTION_RE.search(command):
        return True, ""                            # fast path

    # 「防護対象パスの字面が実在するか」— opaque 同居と bare interpreter の発火条件。
    # 裸単語 mention (散文の 'output' 等) では発火させない (F-FP-4 の虚偽拒否防止)。
    hot = bool(_LEAF_RE.search(command) or _TREE_LITERAL_RE.search(command))

    if hot and _OPAQUE_RE.search(command):
        return False, ("末端/防護ツリーのパス (WAL/campaign.lock/build-variants/"
                       "output/campaigns/external/ccbench) と不透明構文 ($()/` `/"
                       "プロセス置換/<<</eval/xargs) の同居は分類不能 = fails-closed。"
                       "読むだけなら cat/grep/jq で、正規の書き込みは pipeline.evaluate() "
                       "で、コミットは単一行 -m か -F <file> で")

    tokens = _tokenize(command)
    if tokens is None:
        if _LEAF_RE.search(command) or any(
                _tree_violation(w, root) for w in command.split()):
            return False, ("防護対象を含むコマンドを解析できない (クォート不整合等) — "
                           "fails-closed で拒否")
        return True, ""                            # 防護対象に触れない解析不能は素通し

    for seg in _segments(tokens):
        if _redirect_hits_leaf(seg):
            return False, ("リダイレクト先が末端防護対象。WAL/campaign.lock/build-cache "
                           "を書く唯一の経路は pipeline.evaluate() (規律2)")
        head, args = _head_and_args(seg)
        if head == "perf":
            # perf の自前出力先 (-o/--output) が防護対象なら拒否
            for i, a in enumerate(args):
                if ((a in ("-o", "--output") and i + 1 < len(args)
                     and _LEAF_RE.search(args[i + 1]))
                        or (a.startswith("--output=") and _LEAF_RE.search(a))):
                    return False, "perf の出力先 (-o/--output) が末端防護対象 (規律2)"
            if "--" in args:
                # 明示形 `perf <sub> [opts] -- <cmd>`: 子コマンドを実 head として続検査
                # (build-variants バイナリの計測 = 正道を通しつつ、子が writer なら落とす)
                head, args = _head_and_args(args[args.index("--") + 1:])
            elif any(_LEAF_RE.search(t) or _tree_violation(t, root) for t in args):
                return False, ("perf と防護対象の同居は `perf <サブコマンド> [opts] -- "
                               "<コマンド>` の明示形のみ許可 (子コマンドを検査するため)。"
                               "防護対象に触れない計測は自由 (F-FP-1)")
            else:
                continue
        if _destroys_protected_tree(head, args, root):
            return False, (f"campaign dir / ccbench root を破壊する操作 ({head})。"
                           "proof chain を配下ごと削除/移動/展開するのは不可 (規律2)")
        if hot and _stdin_script(head, args):
            return False, ("防護対象パスを含むコマンドでの bare/stdin インタプリタ実行 "
                           "(pipe や here-string でコードを流し込む形) は中身を追えない "
                           "= fails-closed (GB2-3)。スクリプトはファイルに置いて実行する")
        leaf_hits = [t for t in args if _LEAF_RE.search(t)]
        if leaf_hits and not _is_read_only(head, args):
            # ビルドシステムによる build-variants の生成/更新は正当経路
            # (cmake -E の任意ファイル操作は除く)。head 自身が build-variants 配下の
            # バイナリである「実行」は leaf_hits (args のみ) に乗らず素通り (F-FP-1)。
            if (head in _BUILDERS and not (head == "cmake" and "-E" in args)
                    and all("build-variants" in t for t in leaf_hits)):
                continue
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
