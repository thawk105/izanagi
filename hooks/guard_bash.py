#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 hook: Bash 経由の成果物書き込み防壁 (規律2 第二防壁, phase3.md タスク3 / 方針 A)。

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
1. 防護対象 (末端 = WAL/campaign.lock/runs/build-variants/exploration namespace
   marker、ツリー = official / exploration campaigns と external/ccbench) がコマンドに
   現れない → 即許可 (fast path、通常作業を妨げない)。
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
   - **防護ツリー破壊**: external/ccbench は全域 (祖先/自身/子孫)、official / exploration
     campaign tree は祖先・自身・campaign dir 単位の削除/移動/直接書込みを拒否。
     campaign dir 配下の reports/ 等 proof-chain でない子孫の mv/rm/書込みは通す
     (F-FP-2、末端はどの深さでも拒否)。glob (`output/*`) はメタ文字前の prefix で
     重なり判定 (リテラル prefix のみ, GB2-1)。
   - **bare/stdin インタプリタ** (`... | python3` / `python3 -`) が防護対象パス字面と
     同居 → コードの中身を追えないので fails-closed (GB2-3)。

限界 (正直に): テキスト検査の第二防壁であり sandbox ではない。変数展開でパスを
組み立てる・スクリプトファイル越し・`eval`・`python3 -c`・`rm -rf out*` のような
部分 glob は見えない (スクリプトファイルは監査可能な作業物として許可する)。
また Codex subprocess には hook が未配線であり、ユーザー端末・IDE・cron もこの
PreToolUse の外にある。sanctioned 経路の一次防壁と組み合わせる第二防壁であって、
全経路を機械保証するものではない。実効保証は一次防壁 = pipeline.evaluate の
fails-closed 設計と WAL の proof chain、事後は規律6 の監査。
"""
from __future__ import annotations

import json
import fnmatch
import os
import re
import shlex
import socket
import sys
import unicodedata


def _repo_root() -> str:
    # hooks/guard_bash.py = <repo>/hooks/guard_bash.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# settings.json はこのファイルを直接実行するため、通常の package import と違って
# sys.path[0] は hooks/ になる。U1 の site policy を production main から使えるよう、
# repo root を明示的に bootstrap する。import/current_site の障害時は後段の hostname
# fallback が Pegasus login だけを安全側に分類する。
_BOOTSTRAP_ROOT = _repo_root()
if _BOOTSTRAP_ROOT not in sys.path:
    sys.path.insert(0, _BOOTSTRAP_ROOT)
try:
    from orchestrator.campaign import site_policy
except BaseException:  # SystemExit も module 初期化から漏らさず hostname fallback へ
    site_policy = None


# ---- 防護対象 (トークン単位で判定) ----
# 末端: 中身の改変も削除も規律2 違反 (WAL 偽造 / proof chain 破壊)。
_LEAF_RE = re.compile(
    r"(?:^|/)wal\.jsonl(?:$|[/?])"
    r"|(?:^|/)campaign\.lock(?:$|[/?])"
    r"|output/(?:exploration/)?campaigns/[^\s]*?/runs(?:/|$)"
    r"|build-variants")
# 防護ツリーのパス字面 (opaque 同居・bare interpreter 判定の精密トリガ)。
_TREE_LITERAL_RE = re.compile(
    r"output/(?:exploration/)?campaigns|output/exploration/namespace\.json"
    r"|external/ccbench")
# fast path トリガ (広い): これが現れなければ即許可。祖先の祖先 (rm -rf output)
# まで精査に載せるため、防護ツリーの構成語を広く含める。精査自体はトークン単位の
# 厳密パターン (_LEAF_RE / _tree_violation) が担うので、広い分は read で落ちる。
# 裸単語は直前が `-`/単語構成字なら除外 (`--output=` フラグ等の誤爆防止, F-FP-4)。
_MENTION_RE = re.compile(
    r"wal\.jsonl|campaign\.lock|build-variants"
    r"|output/(?:exploration/)?campaigns|output/exploration/namespace\.json"
    r"|external/ccbench"
    r"|(?<![-\w])(?:output|external|ccbench|campaigns|exploration|namespace)\b")
# proof chain を配下に持つツリー root。
_CCBENCH_TREE = "external/ccbench"     # 全域防護 (submodule working-tree = identity の実体)
_CAMPAIGN_TREE = (                      # 閉じた二要素集合 (子孫は末端のみ)
    "output/campaigns",
    "output/exploration/campaigns",
)
_EXPLORATION_TREE = "output/exploration"

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
# tree path 自体を file のように直接上書きする writer。一般の copy/archive までここへ
# 含めると campaign tree を backup 元にする既存の read 受理を狭めるため、対象を限定する。
_TREE_DIRECT_WRITERS = frozenset({"tee", "truncate"})
_GIT_DESTROY_SUBS = frozenset({"clean", "rm", "checkout", "restore", "reset",
                               "stash", "mv"})

# ---- Pegasus login/suspect の重い処理を止める第二防壁 ----
# U1 import が壊れたときにも login node を fail-open しないための最小 fallback。
# site_policy.LOGIN_FALLBACK_RE との一致は test_hooks.py の meta-test が固定する。
_LOGIN_FALLBACK_RE = re.compile(r"^pegasus0[1-9]$")
_FALLBACK_OTHER = "OTHER"
_FALLBACK_LOGIN = "PEGASUS_LOGIN"
_FALLBACK_SUSPECT = "PEGASUS_SUSPECT"
_POLICY_UNSET = object()

_PEGASUS_LOCAL_OK = "local-ok"
_PEGASUS_DISPATCH_REQUIRED = "dispatch-required"
_PEGASUS_UNKNOWN = "unknown"
_PEGASUS_UNREGISTERED = object()
_PEGASUS_ENTRY_FIELDS = frozenset({
    "class", "reason", "primary_gate", "evidence",
})
_PEGASUS_CLASSES = frozenset({
    _PEGASUS_LOCAL_OK, _PEGASUS_DISPATCH_REQUIRED, _PEGASUS_UNKNOWN,
})
_PEGASUS_RAW_MENTION_RE = re.compile(r"tools(?:/|\.)pegasus(?:/|\b)")

# Pegasus admission の正本は JSON。loader 自身と返値の障害を hook module 初期化で
# 漏らすと rc=1 の fail-open になるため、ここで BaseException まで吸収する。
_NON_PEGASUS_SANCTIONED_PATHS = frozenset({
    "tools/run_tests.py",
    # checker 自身が site gate を持ち、login node では計算ノードへ dispatch し
    # SUSPECT では rc=16 で止まる = 「自分で fail-closed する entry point」。
    "tools/check_ai_provenance.py",
})
# JSON 正本が読めないときにも既知の非 Pegasus admission path を
# fail-open させないための静的投影。正本ではない。
_NON_PEGASUS_ADMISSION_FALLBACK_PATHS = frozenset({
    "tools/claude_session_ledger.py",
})


def _non_pegasus_admission_raw_spellings(path: str):
    spellings = {path, f"./{path}"}
    if "/" in path:
        directory, name = path.rsplit("/", 1)
        spellings.update({f"{directory}//{name}", f"{directory}/./{name}"})
    if path.endswith(".py"):
        spellings.add(path[:-3].replace("/", "."))
    return spellings


_NON_PEGASUS_ADMISSION_RAW_MENTION_RE = re.compile(
    "|".join(
        re.escape(spelling)
        for path in sorted(_NON_PEGASUS_ADMISSION_FALLBACK_PATHS)
        for spelling in sorted(_non_pegasus_admission_raw_spellings(path))
    )
)


def _is_canonical_admission_path(path) -> bool:
    return (type(path) is str
            and bool(path)
            and not os.path.isabs(path)
            and ".." not in path.split("/")
            and not path.endswith("/")
            and "\\" not in path
            and not any(unicodedata.category(char) == "Cc" for char in path)
            and os.path.normpath(path) == path)


def _load_pegasus_admission_registry():
    source = os.path.join(
        _BOOTSTRAP_ROOT, "tools", "pegasus_admission_registry.py")
    module_name = "_izanagi_pegasus_admission_registry_for_guard"
    previous_modules = sys.modules
    previous_dont_write_bytecode = sys.dont_write_bytecode
    try:
        # import machinery は stale/unchecked pyc を読み得る。review 対象である exact
        # source bytes を直接 compile/exec し、pyc の読込み・生成経路を持たない。
        with open(source, "rb") as stream:
            source_bytes = stream.read()
        namespace = {
            "__file__": source,
            "__name__": module_name,
            "__package__": "",
        }
        exec(compile(source_bytes, source, "exec", dont_inherit=True), namespace)
        loader = namespace.get("load_admission_registry")
        if not callable(loader):
            raise TypeError("load_admission_registry が callable でない")

        loaded = loader(_BOOTSTRAP_ROOT)
        if type(loaded) is not dict:
            raise TypeError("loader return が plain dict でない")
        if not loaded:
            raise ValueError("loader return が空")
        registry = {}
        for path, entry in loaded.items():
            if not _is_canonical_admission_path(path):
                raise TypeError("loader return path が canonical admission path でない")
            if type(entry) is not dict or set(entry) != _PEGASUS_ENTRY_FIELDS:
                raise TypeError("loader return entry の 4 field が不正")
            copied = dict(entry)
            if any(type(copied[field]) is not str or not copied[field]
                   for field in _PEGASUS_ENTRY_FIELDS):
                raise TypeError("loader return entry value が非空 plain str でない")
            if copied["class"] not in _PEGASUS_CLASSES:
                raise TypeError("loader return entry class が閉集合外")
            if (not path.startswith("tools/pegasus/")
                    and copied["class"] == _PEGASUS_LOCAL_OK):
                raise TypeError("loader return の非 Pegasus local-ok は禁止")
            registry[path] = copied

        local_ok_paths = {
            path for path, entry in registry.items()
            if (path.startswith("tools/pegasus/")
                and entry["class"] == _PEGASUS_LOCAL_OK)
        }
        non_local_paths = {
            path for path, entry in registry.items()
            if entry["class"] != _PEGASUS_LOCAL_OK
        }
        sanctioned_paths = frozenset(
            (_NON_PEGASUS_SANCTIONED_PATHS
             - non_local_paths
             - _NON_PEGASUS_ADMISSION_FALLBACK_PATHS)
            | local_ok_paths)
        return registry, sanctioned_paths, ""
    except BaseException as exc:  # SystemExit を含め module 初期化から絶対に漏らさない。
        diagnostic = (
            "Pegasus admission registry load failed: "
            f"{type(exc).__name__}"
        )
        return {}, frozenset(
            _NON_PEGASUS_SANCTIONED_PATHS
            - _NON_PEGASUS_ADMISSION_FALLBACK_PATHS), diagnostic
    finally:
        # loader 自身が sys の可変属性を壊しても cleanup 例外を hook 外へ漏らさない。
        try:
            sys.dont_write_bytecode = previous_dont_write_bytecode
        except BaseException:
            pass
        try:
            sys.modules = previous_modules
        except BaseException:
            pass


(
    _PEGASUS_ADMISSION_REGISTRY,
    _SANCTIONED_PATHS,
    _PEGASUS_ADMISSION_DIAGNOSTIC,
) = _load_pegasus_admission_registry()
_SANCTIONED_HEADS = frozenset({"qsub", "qdel", "qstat"})
_PYTHON_HEAD_RE = re.compile(r"^python(?:\d+(?:\.\d+)*)?$")
_PYTHON_MODULE_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_PYTEST_MODULES = frozenset({"pytest", "pytest.__main__", "_pytest.main"})
_SCRIPT_EXECUTOR_MODULE_OPTIONS = {
    "cProfile": frozenset({"-o", "--outfile", "-s", "--sort", "-m"}),
    "profile": frozenset({"-o", "--outfile", "-s", "--sort", "-m"}),
    "pdb": frozenset({"-c", "--command", "-m"}),
    "trace": frozenset({
        "-f", "--file", "-C", "--coverdir", "--ignore-module",
        "--ignore-dir", "--module",
    }),
    "runpy": frozenset(),
    "pydoc": frozenset({"-k", "-n", "-p"}),
    "doctest": frozenset({"-o", "--option"}),
    "unittest": frozenset({"-k", "-s", "--start-directory", "-p", "--pattern",
                            "-t", "--top-level-directory"}),
}
_SCRIPT_EXECUTOR_OUTPUT_OPTIONS = {
    "cProfile": frozenset({"-o", "--outfile"}),
    "profile": frozenset({"-o", "--outfile"}),
}
_MULTI_TARGET_EXECUTOR_MODULES = frozenset({"pydoc", "doctest", "unittest"})
_MODULE_HELP_OPTIONS = frozenset({"-h", "--help"})
_PYDOC_NONEXECUTING_MODES = frozenset({"-n", "-p", "-b", "-w"})
_YCSB_EXE_RE = re.compile(r"^ycsb_.*\.exe$")
_BUILD_VARIANTS_HEAD_RE = re.compile(r"(?:^|/)build-variants(?:/|$)")
_NINJA_READ_ONLY_TOOLS = frozenset({
    "commands", "compdb", "deps", "graph", "inputs", "list", "missingdeps",
    "multi-inputs", "query", "rules", "targets", "wincodepage",
})

# provenance 履歴監査 (git subprocess を数千本使う重い処理) の exact path / module 綴り。
# 一次強制は checker 自身の site gate であり、hook が閉じるのは「同じ処理を sanctioned
# 以外の綴りで起動する形」だけである (綴り差のみ。script file 越し・変数展開・eval・
# python3 -c・Codex subprocess は原理的に見えない)。checker を **実行しない**
# `python3 -m py_compile <checker>` のような別 module 起動は閉じない — 閉じると
# AGENTS.md が明示許可する静的検査まで機械拒否になる (段 6 レビュー A の MF-1)。
_PROVENANCE_SCRIPT_PATH = "tools/check_ai_provenance.py"
_PROVENANCE_SCRIPT_BASENAME = "check_ai_provenance.py"
_PROVENANCE_MODULE = "tools.check_ai_provenance"
# 直接実行形のうち重くない呼び方は綴りを問わず通す。--message-file は checker の
# site gate 自身の免除、--help/-h は argparse が即 SystemExit する形。--collect-only /
# --version も argparse が履歴監査へ入る前に終える形なので受理集合を狭めない。
_PROVENANCE_EXEMPT_FLAGS = frozenset({
    "--message-file", "--help", "-h", "--collect-only", "--version",
})

# wrapper option のうち「次 token が値」のもの。未知 option は flag として 1 token
# だけ飛ばし、非 option を闇雲に捨てない。これで sudo -u tanab の tanab を head と
# 誤認せず、同時に実 command まで過剰に skip しない。
_WRAPPER_VALUE_OPTIONS = {
    "sudo": frozenset({
        "-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt",
        "-C", "--close-from", "-R", "--chroot", "-D", "--chdir",
        "-T", "--command-timeout", "-r", "--role", "-t", "--type",
    }),
    "env": frozenset({
        "-u", "--unset", "-C", "--chdir", "-S", "--split-string",
        "--block-signal", "--default-signal", "--ignore-signal",
    }),
    "nice": frozenset({"-n", "--adjustment"}),
    "ionice": frozenset({
        "-c", "--class", "-n", "--classdata", "-p", "--pid",
        "-P", "--pgid", "-u", "--uid",
    }),
    "stdbuf": frozenset({"-i", "--input", "-o", "--output", "-e", "--error"}),
    "timeout": frozenset({"-k", "--kill-after", "-s", "--signal"}),
    "numactl": frozenset({
        "-m", "--membind", "-p", "--preferred", "-P", "--preferred-many",
        "-i", "--interleave", "-w", "--weighted-interleave", "-N", "--cpunodebind",
        "-C", "--physcpubind",
    }),
    "taskset": frozenset({"-c", "--cpu-list"}),
    "time": frozenset({"-f", "--format", "-o", "--output"}),
    "exec": frozenset({"-a"}),
}


def _fallback_label(hostname):
    if not isinstance(hostname, str):
        return ""
    normalized = hostname.lower().rstrip(".")
    return normalized.split(".", 1)[0] if normalized else ""


def _runtime_site(*, policy=_POLICY_UNSET, hostname=None):
    """production site を返す。policy 障害時は login hostname だけ安全側へ倒す。"""
    active_policy = site_policy if policy is _POLICY_UNSET else policy
    if active_policy is not None:
        try:
            return active_policy.current_site()
        except Exception:  # noqa: BLE001 — 壊れた policy でも login を allow に倒さない
            pass
    if hostname is None:
        try:
            hostname = socket.gethostname()
        except Exception:  # noqa: BLE001 — hostname 不明なら OTHER。全 Bash は止めない
            hostname = None
    if _LOGIN_FALLBACK_RE.fullmatch(_fallback_label(hostname)):
        return _FALLBACK_LOGIN
    return _FALLBACK_OTHER


def _refuses_heavy_work(site) -> bool:
    if site is None:
        return False
    if site_policy is not None:
        try:
            return site_policy.refuses_heavy_work(site)
        except Exception:  # noqa: BLE001 — policy API 障害時も既知の拒否値は維持
            pass
    return site in {_FALLBACK_LOGIN, _FALLBACK_SUSPECT}


def _heavy_refusal(site, what: str) -> str:
    if site_policy is not None:
        try:
            return site_policy.heavy_work_refusal(site, what)
        except Exception:  # noqa: BLE001 — reason 作成失敗で判定を allow に反転しない
            pass
    return (f"{what} を拒否します: Pegasus ログイン/疑義ノードでは重い処理を"
            "実行できません。qsub または qlogin で計算ノードを使用してください。")


def _option_takes_attached_value(token: str, options) -> bool:
    for opt in options:
        if opt.startswith("--"):
            if token.startswith(opt + "="):
                return True
        elif token.startswith(opt) and token != opt:
            return True
    return False


def _skip_wrapper_options(wrapper: str, seg, i: int) -> int:
    value_options = _WRAPPER_VALUE_OPTIONS.get(wrapper, frozenset())
    while i < len(seg):
        token = seg[i]
        if token == "--":
            return i + 1
        if wrapper == "env" and re.match(r"^\w+=", token):
            i += 1
            continue
        if token in value_options:
            i += 2
            continue
        if _option_takes_attached_value(token, value_options):
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        break
    # timeout は option 群の後に duration、taskset は -c 無しなら mask を取る。
    if wrapper == "timeout" and i < len(seg):
        i += 1
    elif wrapper == "taskset" and i < len(seg) and _WRAPPER_VAL_RE.fullmatch(seg[i]):
        i += 1
    return i


def _has_terminal_command_reader(seg) -> bool:
    """wrapper 列に実行しない ``command -v/-V`` があれば True を返す。

    ``command`` の valid な短 option は ``-pVv`` なので bundle と分離形を扱う。
    ``-p`` 単独と ``--`` 後は実 command の探索を続け、未知 option は問い合わせと
    みなさない。呼び手は A#12 で追加された raw systemd-run 拒否だけを除外し、
    wave 前からの他の拒否 bit は変えない。
    """
    i = 0
    while i < len(seg):
        token = seg[i]
        if re.match(r"^\w+=", token):
            i += 1
            continue
        base = os.path.basename(token)
        if base in _SHELL_WORDS or token == "in":
            i += 1
            continue
        if base not in _WRAPPERS:
            return False
        if base == "command":
            j = i + 1
            while j < len(seg):
                option = seg[j]
                if option == "--" or not option.startswith("-"):
                    break
                if re.fullmatch(r"-[pVv]*[Vv][pVv]*", option):
                    return True
                j += 1
        i = _skip_wrapper_options(base, seg, i + 1)
    return False


def _expand_env_split_strings(seg):
    """wrapper prefix の ``env -S`` 値を argv token へ展開する。

    shell の outer tokenize 後は quote 済み split-string が 1 token になるため、その
    まま option 値として捨てると実 command head を失う。GNU env が command 起動前に
    行う split を局所的に再現し、制御演算子としては扱わず argv の一部として保つ。
    解析不能時は None を返し、呼び手が login/suspect で安全側に拒否する。
    """
    out = list(seg)
    i = 0
    while i < len(out):
        token = out[i]
        if re.match(r"^\w+=", token):
            i += 1
            continue
        base = os.path.basename(token)
        if base in _SHELL_WORDS or token == "in":
            i += 1
            continue
        if base not in _WRAPPERS:
            break
        if base == "env":
            j = i + 1
            while j < len(out):
                option = out[j]
                split_value = None
                consumed = 1
                if option in {"-S", "--split-string"}:
                    if j + 1 >= len(out):
                        return None
                    split_value = out[j + 1]
                    consumed = 2
                elif option.startswith("--split-string="):
                    split_value = option.split("=", 1)[1]
                elif option.startswith("-S") and option != "-S":
                    split_value = option[2:]
                if split_value is not None:
                    try:
                        split_tokens = shlex.split(split_value, posix=True)
                    except ValueError:
                        return None
                    if not split_tokens:
                        return None
                    out[j:j + consumed] = split_tokens
                    break
                if option == "--":
                    break
                if re.match(r"^\w+=", option):
                    j += 1
                    continue
                value_options = _WRAPPER_VALUE_OPTIONS["env"]
                if option in value_options:
                    j += 2
                    continue
                if (_option_takes_attached_value(option, value_options)
                        or option.startswith("-")):
                    j += 1
                    continue
                break
        i = _skip_wrapper_options(base, out, i + 1)
    return out


def _heavy_head_and_args(seg):
    """wrapper の値を含めて剥がし、(raw head, basename, args) を返す。"""
    i = 0
    while i < len(seg):
        token = seg[i]
        if re.match(r"^\w+=", token):
            i += 1
            continue
        base = os.path.basename(token)
        if base in _WRAPPERS:
            i = _skip_wrapper_options(base, seg, i + 1)
            continue
        if base in _SHELL_WORDS or token == "in":
            i += 1
            continue
        return token, base, seg[i + 1:]
    return "", "", []


def _invocation_path(token: str, repo_root: str) -> str:
    expanded = os.path.expanduser(token)
    if os.path.isabs(expanded):
        normalized = os.path.normpath(expanded)
        root = os.path.normpath(repo_root)
        if normalized == root or normalized.startswith(root + os.sep):
            return os.path.relpath(normalized, root)
        return normalized
    return os.path.normpath(expanded)


def _pegasus_admission_entry(path: str):
    """exact entry、Pegasus 配下の未登録 sentinel、管轄外 None を返す。"""
    entry = _PEGASUS_ADMISSION_REGISTRY.get(path)
    if entry is not None:
        if (path.startswith("tools/pegasus/")
                or entry["class"] != _PEGASUS_LOCAL_OK):
            return entry
        # wrapper と sanctioned 導出が同時に壊れても allow に反転させない。
        return _PEGASUS_UNREGISTERED
    # loader 障害時の静的投影は exact path だけを deny 側へ倒す。
    if path in _NON_PEGASUS_ADMISSION_FALLBACK_PATHS:
        return _PEGASUS_UNREGISTERED
    # prefix は allow に使わず、Pegasus 配下の未登録を deny に倒すためだけに使う。
    if path == "tools/pegasus" or path.startswith("tools/pegasus/"):
        return _PEGASUS_UNREGISTERED
    return None


def _python_prefix_invocation(head: str, args):
    """Python prefix を解釈し ``(kind, value, remaining_args)`` を返す。"""
    if not _PYTHON_HEAD_RE.fullmatch(head):
        return None
    no_value_options = frozenset("bBdEhiIOPqRsSuvVx")
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            if i + 1 < len(args):
                return "script", args[i + 1], args[i + 2:]
            return "none", "", []
        if token == "-":
            return "stdin", "", args[i + 1:]
        if not token.startswith("-"):
            return "script", token, args[i + 1:]
        if token.startswith("--"):
            if token == "--check-hash-based-pycs":
                if i + 1 >= len(args):
                    return "invalid", "", []
                i += 2
                continue
            if token.startswith("--check-hash-based-pycs="):
                i += 1
                continue
            # help/version 等は interpreter 内で終了する。未知 long option も
            # Python が拒否するが、残余は baseline 互換の fail-closed 検査へ渡す。
            return "interpreter", token, args[i + 1:]

        bundle = token[1:]
        consumed_value = False
        for j, option in enumerate(bundle):
            if option in {"c", "m", "W", "X"}:
                attached = bundle[j + 1:]
                if attached:
                    value = attached
                    remaining = args[i + 1:]
                    next_i = i + 1
                elif i + 1 < len(args):
                    value = args[i + 1]
                    remaining = args[i + 2:]
                    next_i = i + 2
                else:
                    return "invalid", "", []
                if option == "c":
                    return "command", value, remaining
                if option == "m":
                    return "module", value, remaining
                # -W/-X は値を取るが prefix parsing は続く。
                i = next_i
                consumed_value = True
                break
            if option not in no_value_options:
                return "invalid", "", args[i + 1:]
        if not consumed_value:
            i += 1
    return "none", "", []


def _python_module_invocation(head: str, args):
    """Python CLI の ``-m`` 形を ``(module, module_args)`` として返す。

    分離形に加え ``-mname`` と、値を取らない短 option に ``m`` を結合した
    ``-qm name`` / ``-Om name`` / ``-qmpytest`` を扱う。``-c`` / ``-W`` /
    ``-X`` の残部は各 option の値なので、その中の ``m`` は module option とみなさない。
    """
    parsed = _python_prefix_invocation(head, args)
    if parsed is None or parsed[0] != "module":
        return None
    return parsed[1], parsed[2]


def _python_module_path(module: str, repo_root: str) -> str:
    """module 名の repo 内実体を exact path として返す。"""
    if not _PYTHON_MODULE_RE.fullmatch(module):
        return ""
    stem = module.replace(".", "/")
    for relative in (stem + ".py", stem + "/__main__.py"):
        if os.path.isfile(os.path.join(repo_root, relative)):
            return os.path.normpath(relative)
    return ""


def _python_module_target(head: str, args, repo_root: str) -> str:
    """Python ``-m name`` の repo 内実体を exact path として返す。"""
    invocation = _python_module_invocation(head, args)
    if invocation is None:
        return ""
    module, _ = invocation
    return _python_module_path(module, repo_root)


def _module_option_value(token: str, options):
    """module CLI option の attached value、非該当 None を返す。"""
    for option in options:
        if option.startswith("--"):
            if token.startswith(option + "="):
                return token.split("=", 1)[1]
        elif token.startswith(option) and token != option:
            return token[len(option):]
    return None


def _executor_module_target(value: str, repo_root: str) -> str:
    """module 名なら repo 内実体へ写像し、それ以外は空文字列を返す。"""
    return _python_module_path(value, repo_root)


def _script_executor_output_targets(module: str, args, repo_root: str) -> tuple:
    """program 決定前に指定された executor の出力先を返す。"""
    output_options = _SCRIPT_EXECUTOR_OUTPUT_OPTIONS.get(module)
    if output_options is None:
        return ()
    value_options = _SCRIPT_EXECUTOR_MODULE_OPTIONS[module]
    targets = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in _MODULE_HELP_OPTIONS:
            return ()
        if token == "--":
            break
        if token in output_options:
            if i + 1 >= len(args):
                break
            targets.append(_invocation_path(args[i + 1], repo_root))
            i += 2
            continue
        attached = _module_option_value(token, output_options)
        if attached is not None:
            targets.append(_invocation_path(attached, repo_root))
            i += 1
            continue
        if token in value_options:
            i += 2
            continue
        if _module_option_value(token, value_options) is not None:
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        break
    return tuple(targets)


def _script_executor_targets(module: str, args, repo_root: str) -> tuple:
    """後続 script/module を実行する module の全実行対象を返す。"""
    if module in {"coverage", "coverage.__main__"}:
        if not args or args[0] != "run":
            return ()
        args = args[1:]
        value_options = frozenset({
            "--concurrency", "--context", "--data-file", "--include",
            "--omit", "--rcfile", "--source", "-m", "--module",
        })
    else:
        value_options = _SCRIPT_EXECUTOR_MODULE_OPTIONS.get(module)
        if value_options is None:
            return ()

    targets = []
    nonexecuting_mode = False
    parsing_options = True
    i = 0
    while i < len(args):
        token = args[i]
        if parsing_options and token in _MODULE_HELP_OPTIONS:
            return ()
        if parsing_options and module == "trace" and token == "--report":
            return ()
        if (parsing_options and module == "pydoc"
                and token in _PYDOC_NONEXECUTING_MODES):
            nonexecuting_mode = True
            i += 2 if token in {"-n", "-p"} else 1
            continue
        if parsing_options and module == "pydoc":
            attached_mode = _module_option_value(
                token, frozenset({"-n", "-p"}))
            if attached_mode is not None:
                nonexecuting_mode = True
                i += 1
                continue
        if parsing_options and token == "--":
            positional = args[i + 1:]
            if nonexecuting_mode:
                return ()
            if module not in _MULTI_TARGET_EXECUTOR_MODULES:
                positional = positional[:1]
            for value in positional:
                mapped = _executor_module_target(value, repo_root)
                targets.append(mapped or value)
            return tuple(targets)
        if parsing_options and token in value_options:
            if i + 1 >= len(args):
                return tuple(targets)
            value = args[i + 1]
            if token in {"-m", "--module"}:
                mapped = _executor_module_target(value, repo_root)
                return (mapped,) if mapped else ()
            i += 2
            continue
        attached = (_module_option_value(token, value_options)
                    if parsing_options else None)
        if attached is not None:
            if any(token.startswith(opt) for opt in {"-m", "--module"}):
                mapped = _executor_module_target(attached, repo_root)
                return (mapped,) if mapped else ()
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        if nonexecuting_mode:
            return ()
        if module == "runpy":
            mapped = _executor_module_target(token, repo_root)
            return (mapped,) if mapped else ()
        mapped = _executor_module_target(token, repo_root)
        targets.append(mapped or token)
        if module not in _MULTI_TARGET_EXECUTOR_MODULES:
            return tuple(targets)
        parsing_options = False
        i += 1
    return tuple(targets)


_SHELL_VALUE_OPTIONS = frozenset({
    "-O", "+O", "-o", "+o", "--init-file", "--rcfile",
})
_SHELL_STARTUP_FILE_OPTIONS = frozenset({"--init-file", "--rcfile"})


def _shell_startup_targets(args) -> tuple:
    """shell prefix に指定された startup file をすべて実行対象として返す。"""
    kind, _, _ = _shell_prefix_invocation(args)
    if kind == "command" and not _shell_prefix_is_interactive(args):
        return ()
    targets = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in _SHELL_STARTUP_FILE_OPTIONS:
            if i + 1 < len(args):
                targets.append(args[i + 1])
            i += 2
            continue
        attached = _module_option_value(token, _SHELL_STARTUP_FILE_OPTIONS)
        if attached is not None:
            targets.append(attached)
            i += 1
            continue
        if token == "--" or token == "-" or not token.startswith(("-", "+")):
            break
        if token in _SHELL_VALUE_OPTIONS:
            i += 2
            continue
        if _option_takes_attached_value(token, _SHELL_VALUE_OPTIONS):
            i += 1
            continue
        if token.startswith("--"):
            i += 1
            continue
        if "c" in token[1:] or "s" in token[1:]:
            break
        i += 1
    return tuple(targets)


def _shell_prefix_is_interactive(args) -> bool:
    """command/script 決定前の shell option に ``-i`` があるか。"""
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--" or token == "-" or not token.startswith(("-", "+")):
            return False
        if token in _SHELL_VALUE_OPTIONS:
            i += 2
            continue
        if _option_takes_attached_value(token, _SHELL_VALUE_OPTIONS):
            i += 1
            continue
        if token.startswith("--"):
            i += 1
            continue
        bundle = token[1:]
        if "i" in bundle:
            return True
        if "c" in bundle or "s" in bundle:
            return False
        i += 1
    return False


def _shell_prefix_invocation(args):
    """shell prefix を解釈し ``(kind, index, remaining_args)`` を返す。"""
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            if i + 1 < len(args):
                return "script", i + 1, args[i + 2:]
            return "interpreter", None, []
        if token == "-":
            return "stdin", None, args[i + 1:]
        if not token.startswith(("-", "+")):
            return "script", i, args[i + 1:]
        if token in _SHELL_VALUE_OPTIONS:
            if i + 1 >= len(args):
                return "invalid", None, []
            i += 2
            continue
        if _option_takes_attached_value(token, _SHELL_VALUE_OPTIONS):
            i += 1
            continue
        if token.startswith("--"):
            i += 1
            continue
        bundle = token[1:]
        if "c" in bundle:
            if i + 1 < len(args):
                return "command", i + 1, args[i + 2:]
            return "invalid", None, []
        if "s" in bundle:
            return "stdin", None, args[i + 1:]
        i += 1
    return "interpreter", None, []


def _shell_command_index(args):
    """shell の短 option 群に ``c`` があれば command-string の index を返す。"""
    kind, index, _ = _shell_prefix_invocation(args)
    return index if kind == "command" else None


def _script_targets(raw_head: str, head: str, args, repo_root: str) -> tuple:
    """registry/sanction 判定対象となる全 execution target を返す。"""
    candidates = [raw_head]
    python_invocation = _python_prefix_invocation(head, args)
    if python_invocation is not None:
        kind, value, remaining = python_invocation
        if kind == "module":
            module_target = _python_module_path(value, repo_root)
            if module_target:
                candidates.append(module_target)
            candidates.extend(_script_executor_targets(value, remaining, repo_root))
        elif kind == "script":
            candidates.append(value)
    elif head in {"bash", "sh", "zsh"}:
        candidates.extend(_shell_startup_targets(args))
        kind, index, _ = _shell_prefix_invocation(args)
        if kind == "script" and index is not None:
            candidates.append(args[index])
    targets = []
    for candidate in candidates:
        path = _invocation_path(candidate, repo_root)
        if (path in _SANCTIONED_PATHS
                or _pegasus_admission_entry(path) is not None):
            if path not in targets:
                targets.append(path)
    return tuple(targets)


def _script_target(raw_head: str, head: str, args, repo_root: str) -> str:
    """互換用の単数 target。判定核は `_script_targets` で全件を検査する。"""
    targets = _script_targets(raw_head, head, args, repo_root)
    return targets[0] if targets else _invocation_path(raw_head, repo_root)


def _is_sanctioned(raw_head: str, head: str, args, repo_root: str) -> bool:
    if head in _SANCTIONED_HEADS:
        return True
    targets = _script_targets(raw_head, head, args, repo_root)
    return bool(targets) and all(target in _SANCTIONED_PATHS for target in targets)


def _pytest_nonexecuting(args) -> bool:
    return any(a in {"--collect-only", "--help", "--version"} for a in args)


def _python_pytest_args(head: str, args):
    invocation = _python_module_invocation(head, args)
    if invocation is None:
        return None
    module, module_args = invocation
    return module_args if module in _PYTEST_MODULES else None


def _make_parallel(args) -> bool:
    return any(a in {"-j", "--jobs"} or a.startswith("-j")
               or a.startswith("--jobs=") for a in args)


def _first_non_option(args) -> str:
    return next((a for a in args if not a.startswith("-") and a != "--"), "")


def _ninja_tool(args) -> str:
    for i, arg in enumerate(args):
        if arg in {"-t", "--tool"}:
            return args[i + 1] if i + 1 < len(args) else ""
        if arg.startswith("--tool="):
            return arg.split("=", 1)[1]
    return ""


def _provenance_entry(raw_head: str, head: str, args, repo_root: str):
    """checker を **実行する** 綴りを ``(path, sanctioned)`` で返す。

    実行しない綴りは None。``python3 -m <他 module> … <checker>`` は checker を
    実行しない別プログラム (py_compile / json.tool 等の静的読み取り) なので、ここでは
    名指しとみなさない — 違反にすると AGENTS.md が明示許可する
    ``python3 -m py_compile tools/check_ai_provenance.py`` まで機械拒否される。
    sanctioned の借用抑止は `_provenance_script_borrow` が別に担う。
    判定対象は head が python 系か checker 自身の場合だけに絞る
    (`cat`/`git show`/`rg` 等が引数で名指しする読み取りを巻き込まない)。
    """
    invocation = _python_module_invocation(head, args)
    if invocation is not None:
        if invocation[0] != _PROVENANCE_MODULE:
            return None
        target = _python_module_target(head, args, repo_root)
        return target, target == _PROVENANCE_SCRIPT_PATH
    if os.path.basename(raw_head) == _PROVENANCE_SCRIPT_BASENAME:
        path = _invocation_path(raw_head, repo_root)
        return path, path == _PROVENANCE_SCRIPT_PATH
    if _PYTHON_HEAD_RE.fullmatch(head):
        script = _first_non_option(args)
        if script and os.path.basename(script) == _PROVENANCE_SCRIPT_BASENAME:
            path = _invocation_path(script, repo_root)
            return path, path == _PROVENANCE_SCRIPT_PATH
    return None


def _provenance_script_borrow(head: str, args) -> bool:
    """``python3 -m <他 module> … <checker>`` の形で checker を渡しているか。

    違反ではない (module 側が実体で checker は data)。ただし **sanctioned 判定を
    script 引数から借りさせない** — 借りると ``-m pytest tools/check_ai_provenance.py``
    が `_is_sanctioned` の早期許可を取って pytest 判定へ到達しなくなる
    (execution target の sanctioned 判定より先にこの分岐を評価する)。
    引数順に依存させない: ``-m py_compile a.py <checker>`` も借用と見なす。
    """
    invocation = _python_module_invocation(head, args)
    if invocation is None or invocation[0] == _PROVENANCE_MODULE:
        return False
    return any(
        not a.startswith("-") and a != "--"
        and os.path.basename(a) == _PROVENANCE_SCRIPT_BASENAME
        for a in invocation[1])


def _provenance_violation(raw_head: str, head: str, args, repo_root: str):
    """非 sanctioned な綴りでの provenance 履歴監査起動を拒否理由にする。"""
    entry = _provenance_entry(raw_head, head, args, repo_root)
    if entry is None:
        return None
    path, sanctioned = entry
    if sanctioned:
        return None
    if any(a in _PROVENANCE_EXEMPT_FLAGS or a.startswith("--message-file=")
           for a in args):
        return None
    return f"非 sanctioned provenance 履歴監査実行体 ({path or raw_head})"


def _executor_output_violation(head: str, args, repo_root: str):
    """executor の出力先が admission 対象を上書きする形を拒否する。"""
    invocation = _python_module_invocation(head, args)
    if invocation is None:
        return None
    module, module_args = invocation
    for path in _script_executor_output_targets(module, module_args, repo_root):
        if (_pegasus_admission_entry(path) is not None
                or path in _SANCTIONED_PATHS):
            return f"executor の出力先が admission 登録 path ({path})"
    return None


def _python_module_invocation_anywhere(args):
    """baseline 互換: argv 全体から最初の ``-m`` 綴りを探す。"""
    no_value_options = frozenset("bBdEhiIOPqRsSuvVx")
    value_options = frozenset("cWX")
    for i, token in enumerate(args):
        if token == "-m":
            if i + 1 < len(args):
                return args[i + 1], args[i + 2:]
            return None
        if not token.startswith("-") or token.startswith("--") or token == "-":
            continue
        bundle = token[1:]
        for j, option in enumerate(bundle):
            if option == "m":
                attached = bundle[j + 1:]
                if attached:
                    return attached, args[i + 1:]
                if i + 1 < len(args):
                    return args[i + 1], args[i + 2:]
                return None
            if option in value_options or option not in no_value_options:
                break
    return None


def _baseline_first_token_violation(args, repo_root: str, pytest_args=None):
    """baseline が実行体扱いした最初の非 option token だけを検査する。"""
    token_index = next((i for i, arg in enumerate(args)
                        if not arg.startswith("-") and arg != "--"), None)
    if token_index is None:
        return None
    token = args[token_index]
    path = _invocation_path(token, repo_root)
    admission = _pegasus_admission_entry(path)
    if (admission is _PEGASUS_UNREGISTERED
            or (admission is not None
                and admission["class"] != _PEGASUS_LOCAL_OK)):
        return f"interpreter の baseline 実行体 ({path})"
    base = os.path.basename(token)
    if (base in {"pytest", "py.test"} and pytest_args is not None
            and _pytest_nonexecuting(pytest_args)):
        return None
    if (base in {"pytest", "py.test", "cmake", "make", "ninja", "ctest", "perf"}
            or _YCSB_EXE_RE.fullmatch(base)
            or _BUILD_VARIANTS_HEAD_RE.search(token)):
        return f"interpreter の baseline 重量対象 ({token})"
    return None


def _interpreter_residual_violation(head: str, args, repo_root: str):
    """baseline の先頭 token と args 全体の pytest 検出を維持する。"""
    python_invocation = _python_prefix_invocation(head, args)
    if python_invocation is not None:
        kind, _, _ = python_invocation
        invocation = _python_module_invocation_anywhere(args)
        pytest_args = (invocation[1] if invocation is not None
                       and invocation[0] in _PYTEST_MODULES else None)
        if kind != "command":
            violation = _baseline_first_token_violation(
                args, repo_root, pytest_args=pytest_args)
            if violation:
                return violation
        if invocation is not None:
            module, module_args = invocation
            if module in _PYTEST_MODULES and not _pytest_nonexecuting(module_args):
                return "interpreter argv の python3 -m pytest"
    elif head in {"bash", "sh", "zsh"}:
        kind, _, _ = _shell_prefix_invocation(args)
        if kind != "command":
            return _baseline_first_token_violation(args, repo_root)
    return None


def _heavy_segment_violation(seg, repo_root: str, depth: int):
    seg = _expand_env_split_strings(seg)
    if seg is None:
        return "env -S split-string を解析不能"
    raw_head, head, args = _heavy_head_and_args(seg)
    if not head:
        return None
    if head == "systemd-run":
        if _has_terminal_command_reader(seg):
            return None
        return "systemd-run"
    # sanctioned 早期許可より前に評価する。後ろに置くと、script 引数から借りた
    # sanctioned 判定がこの分岐に到達させない。
    provenance = _provenance_violation(raw_head, head, args, repo_root)
    if provenance:
        return provenance

    output = _executor_output_violation(head, args, repo_root)
    if output:
        return output

    targets = _script_targets(raw_head, head, args, repo_root)
    for target in targets:
        admission = _pegasus_admission_entry(target)
        if admission is _PEGASUS_UNREGISTERED:
            if target == "tools/pegasus" or target.startswith("tools/pegasus/"):
                return f"未登録 Pegasus 実行体 ({target})"
            return f"未登録 admission 実行体 ({target})"
        if admission is not None and admission["class"] != _PEGASUS_LOCAL_OK:
            if target.startswith("tools/pegasus/"):
                return (f"Pegasus {admission['class']} 実行体 ({target})")
            return (f"admission {admission['class']} 実行体 ({target})")

    residual = _interpreter_residual_violation(head, args, repo_root)
    if residual:
        return residual

    # shell command-string は startup file の sanctioned 判定より先に検査する。
    # 先に許可すると local-ok rcfile が内側の pytest を隠せてしまう。
    if head in {"bash", "sh", "zsh"} and depth < 2:
        command_index = _shell_command_index(args)
        if command_index is not None:
            nested = _heavy_command_violation(
                args[command_index], repo_root, depth + 1)
            if nested:
                return nested

    # `-m <他 module> … <checker>` は checker を実行しないので通すが、sanctioned だけは
    # 借りさせず以降の既存判定 (pytest 等) へ落とす。
    if (not _provenance_script_borrow(head, args)
            and _is_sanctioned(raw_head, head, args, repo_root)):
        return None

    if head in {"pytest", "py.test"}:
        if not _pytest_nonexecuting(args):
            return f"{head} による test 実行"
        return None

    pytest_args = _python_pytest_args(head, args)
    if pytest_args is not None:
        if not _pytest_nonexecuting(pytest_args):
            return f"{head} -m pytest による test 実行"
        return None

    if head == "cmake" and "--build" in args:
        return "cmake --build"
    if head == "make" and _make_parallel(args):
        if not any(a in {"-n", "--dry-run"} for a in args):
            return "make の並列 build"
        return None
    if head == "ninja":
        if any(a in {"--help", "--version"} for a in args):
            return None
        tool = _ninja_tool(args)
        if tool in _NINJA_READ_ONLY_TOOLS:
            return None
        if tool:
            return f"ninja の非読み取り専用 tool ({tool})"
        return "ninja build"
    if head == "ctest":
        if any(a in {"-N", "--show-only", "--help", "--version"}
               or a.startswith("--show-only=") for a in args):
            return None
        return "ctest 実行"
    if head == "perf" and _first_non_option(args) in {"stat", "record"}:
        return f"perf {_first_non_option(args)}"
    if _BUILD_VARIANTS_HEAD_RE.search(raw_head):
        return "build-variants 配下の実行体"
    if _YCSB_EXE_RE.fullmatch(head):
        return f"{head} benchmark 実行"

    return None


def _heavy_command_violation(command: str, repo_root: str, depth: int = 0):
    tokens = _tokenize(command)
    if tokens is None:
        return None
    for seg in _segments(tokens):
        violation = _heavy_segment_violation(seg, repo_root, depth)
        if violation:
            return violation
    return None


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
            # wrapper 自身のフラグ・オプション値 (期間 / CPU リスト / 16 進マスク) を飛ばす
            while i < len(seg) and (seg[i].startswith("-")
                                    or _WRAPPER_VAL_RE.fullmatch(seg[i])):
                i += 1
            continue
        return base, seg[i + 1:]
    return "", []


def _stdin_script(head: str, args) -> bool:
    """interpreter がスクリプトファイル無しで stdin/pipe のコードを実行する形か。"""
    if head not in _INTERP:
        return False
    if "-" in args:
        return True                               # 明示 stdin 実行
    return not any(not a.startswith("-") for a in args)   # 非フラグ引数ゼロ = bare


def _is_read_only(head: str, args, repo_root: str = "", cwd: str = "") -> bool:
    """head が末端防護対象に触れてよい (中身を変えない) 読み取り専用操作か。"""
    if head in _PURE_READERS:
        return True
    if head == "dd":
        # dd if=WAL of=/tmp (読み) は許可、of= が末端 (書き) なら拒否
        return not any(a.startswith("of=") and (
            _LEAF_RE.search(a) or _namespace_marker_violation(a, repo_root, cwd)
        ) for a in args)
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


def _repo_relative_path(token: str, repo_root: str, cwd: str = "") -> str:
    """path 字面 (~ 展開済) を repo_root 相対に正規化して返す。"""
    raw = os.path.expanduser(token)
    if not os.path.isabs(raw) and cwd:
        raw = os.path.join(cwd, raw)
    if os.path.isabs(raw):
        ap = os.path.normpath(raw)
        root = os.path.normpath(repo_root) if repo_root else ""
        if root and (ap == root or ap.startswith(root + os.sep)):
            return os.path.relpath(ap, root)
        return ap.strip("/")
    return os.path.normpath(raw).strip("/")


def _repo_relative(token: str, repo_root: str, cwd: str = "") -> str:
    """glob prefix (~ 展開済) を repo_root 相対に正規化して返す。

    2026-07-04 敵対検証: 絶対パス (`/home/.../output/campaigns/c`)・`~/…` は、strip 後
    `home/…` 前置ゆえ相対リテラル `output/campaigns` を prefix に持たず、防護ツリー破壊
    (`rm -rf <abs>/output/campaigns/c`) が素通りしていた。repo_root で相対化してから既存の
    厳密照合に載せる。repo 外絶対 (`/tmp/output/campaigns`) は相対化せず素通り = 防護外
    (正しい)。`$VAR` 展開はシェルの実行時展開ゆえ hook からは追えない (docstring の限界)。"""
    return _repo_relative_path(_glob_prefix(token), repo_root, cwd)


def _brace_patterns(pattern: str):
    """shell brace のカンマ列挙を marker 照合用に展開する。"""
    match = re.search(r"\{([^{}]*)\}", pattern)
    if match is None or "," not in match.group(1):
        return (pattern,)
    expanded = []
    for choice in match.group(1).split(","):
        replaced = pattern[:match.start()] + choice + pattern[match.end():]
        expanded.extend(_brace_patterns(replaced))
    return tuple(expanded)


def _namespace_marker_violation(
        token: str, repo_root: str = "", cwd: str = "") -> bool:
    """repo 内 exploration tree の namespace.json に pattern が一致し得るか。"""
    candidate = token
    if token.startswith("of=") or token.startswith("--output="):
        candidate = token.split("=", 1)[1]
    for pattern in _brace_patterns(candidate):
        relative = _repo_relative_path(pattern, repo_root, cwd)
        parts = relative.split("/")
        if (len(parts) >= 3
                and parts[:2] == ["output", "exploration"]
                and fnmatch.fnmatchcase("namespace.json", parts[-1])):
            return True
    return False


def _campaign_tree_violation(token: str, repo_root: str = "") -> bool:
    """campaign tree の祖先・自身・campaign dir 単位に重なるなら True。"""
    p = _repo_relative(token, repo_root)
    if not p or p == ".":
        return False
    for tree in _CAMPAIGN_TREE:
        if p == tree or tree.startswith(p + "/"):
            return True                           # 祖先 or 自身
        if p.startswith(tree + "/"):
            rel = p[len(tree) + 1:]
            if "/" not in rel:
                return True                       # campaign dir 丸ごと (runs を内包)
    return False


def _tree_violation(token: str, repo_root: str = "", cwd: str = "") -> bool:
    """token の削除/移動/展開が proof chain を壊すか。

    - 末端 (_LEAF_RE) はどの深さでも壊す。
    - external/ccbench は全域 (祖先/自身/子孫) — submodule working-tree は identity の
      実体で、部分破壊も評価を汚す。
    - official / exploration campaign tree は祖先・自身・campaign dir 単位
      (`<campaign-tree>/<id>`) まで。それより深い proof-chain でない子孫
      (reports/ 等) は末端に触れない限り通す (F-FP-2: 散文・プロットの
      mv/rm を巻き込まない)。
    絶対パス・`~` は repo_root で相対化してから照合する (2026-07-04 敵対検証)。glob は
    メタ文字前のリテラル prefix で判定 (`output/*` → `output/` は祖先 = 拒否。`out*` の
    ような部分 glob は判定不能 = 素通り、限界として docstring に記録)。"""
    if _LEAF_RE.search(token) or _namespace_marker_violation(token, repo_root, cwd):
        return True
    p = _repo_relative(token, repo_root)
    if not p or p == ".":
        return False
    t = _CCBENCH_TREE
    if p == t or t.startswith(p + "/") or p.startswith(t + "/"):
        return True
    return _campaign_tree_violation(token, repo_root)


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


def _destroys_protected_tree(
        head: str, args, repo_root: str = "", cwd: str = "") -> bool:
    """head が防護ツリーを丸ごと削除/移動/展開する操作か。"""
    if head == "git":
        if "clean" in args:                       # cwd 再帰で untracked WAL を消す
            return True
        if any(a in _GIT_DESTROY_SUBS for a in args):
            return any(_tree_violation(t, repo_root, cwd) for t in _path_args(args))
        return False
    if head == "find":
        if any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir") for a in args):
            return any(_tree_violation(t, repo_root, cwd) for t in _path_args(args))
        return False
    if head == "tar":
        if _tar_creates(args):                    # backup (読み) は通す
            return False
        return any(_tree_violation(t, repo_root, cwd) for t in _path_args(args))
    if head == "rsync":
        # DEST (最後の path 引数) が防護ツリーなら mirror INTO (書き) = 拒否。
        # SRC だけが防護対象 (backup 元) の読みは通す。
        paths = _path_args(args)
        return bool(paths) and _tree_violation(paths[-1], repo_root, cwd)
    if head in _TREE_MUTATORS:
        return any(_tree_violation(t, repo_root, cwd) for t in _path_args(args))
    return False


def _redirect_hits_protected(seg, repo_root: str = "", cwd: str = "") -> bool:
    """セグメント内でリダイレクト先が末端または防護 tree 自体なら True。"""
    for i, t in enumerate(seg):
        if t in _REDIR_OPS and i + 1 < len(seg):
            tgt = seg[i + 1]
            if t == ">&" and tgt.isdigit():       # 2>&1 等の fd 複製は無視
                continue
            if (_LEAF_RE.search(tgt)
                    or _namespace_marker_violation(tgt, repo_root, cwd)
                    or _campaign_tree_violation(tgt, repo_root)
                    and _repo_relative(tgt, repo_root).startswith(
                        _EXPLORATION_TREE + "/")):
                return True
    return False


def decide(command: str, repo_root: str = "", *, site=None) -> tuple:
    """(allow: bool, reason: str)。reason は拒否時のみ。"""
    # 絶対パス・`~` を repo 相対化するため root を realpath で確定 (2026-07-04 敵対検証)。
    root = os.path.realpath(repo_root or _repo_root())
    # site=None は明示的に OTHER と同義。既存の防護パス判定へ入る前に、production
    # main が注入した LOGIN/SUSPECT だけを追加検査する。
    if _refuses_heavy_work(site):
        violation = _heavy_command_violation(command, root)
        if violation:
            return False, _heavy_refusal(site, violation)
    if not _MENTION_RE.search(command):
        return True, ""                            # fast path

    # 「防護対象パスの字面が実在するか」— opaque 同居と bare interpreter の発火条件。
    # 裸単語 mention (散文の 'output' 等) では発火させない (F-FP-4 の虚偽拒否防止)。
    hot = bool(_LEAF_RE.search(command) or _TREE_LITERAL_RE.search(command))

    if hot and _OPAQUE_RE.search(command):
        return False, ("末端/防護ツリーのパス (WAL/campaign.lock/build-variants/"
                       "namespace marker/official・exploration campaigns/external/ccbench) "
                       "と不透明構文 ($()/` `/"
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

    marker_cwd = ""
    for seg in _segments(tokens):
        if _redirect_hits_protected(seg, root, marker_cwd):
            return False, ("リダイレクト先が末端防護対象または campaign tree。WAL/"
                           "campaign.lock/build-cache を書く唯一の経路は "
                           "pipeline.evaluate() (規律2)")
        head, args = _head_and_args(seg)
        if head == "cd":
            paths = _path_args(args)
            if len(paths) == 1:
                marker_cwd = _repo_relative_path(paths[0], root, marker_cwd)
            continue
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
        if _destroys_protected_tree(head, args, root, marker_cwd):
            return False, (f"campaign dir / ccbench root を破壊する操作 ({head})。"
                           "proof chain を配下ごと削除/移動/展開するのは不可 (規律2)")
        if (head in _TREE_DIRECT_WRITERS
                and any(_campaign_tree_violation(t, root)
                        and _repo_relative(t, root).startswith(
                            _EXPLORATION_TREE + "/") for t in args)):
            return False, (f"campaign tree 自体を上書きする操作 ({head})。proof chain を"
                           "配下ごと破壊しうるため不可 (規律2)")
        if hot and _stdin_script(head, args):
            return False, ("防護対象パスを含むコマンドでの bare/stdin インタプリタ実行 "
                           "(pipe や here-string でコードを流し込む形) は中身を追えない "
                           "= fails-closed (GB2-3)。スクリプトはファイルに置いて実行する")
        leaf_hits = [t for t in args if (
            _LEAF_RE.search(t) or _namespace_marker_violation(t, root, marker_cwd)
        )]
        if leaf_hits and not _is_read_only(head, args, root, marker_cwd):
            # ビルドシステムによる build-variants の生成/更新は正当経路
            # (cmake -E の任意ファイル操作は除く)。head 自身が build-variants 配下の
            # バイナリである「実行」は leaf_hits (args のみ) に乗らず素通り (F-FP-1)。
            if (head in _BUILDERS and not (head == "cmake" and "-E" in args)
                    and all("build-variants" in t for t in leaf_hits)):
                continue
            return False, (f"末端防護対象に触れる非読み取りコマンド ({head or '?'})。"
                           "WAL/campaign.lock/build-cache/namespace marker の書き換え・"
                           "削除・移動は不可 (規律2)。読み取りは cat/grep/jq/head/tail 等で")
    return True, ""


def main() -> int:
    raw = sys.stdin.read()                 # 例外時の fails-closed 判定に使うため一度で読む
    try:
        payload = json.loads(raw)
        command = (payload.get("tool_input") or {}).get("command", "")
        # production entry point だけが live site を注入する。decide() の既定 None は
        # 既存単体テストと非 Pegasus の受理集合を変えない。
        allow, reason = decide(command, site=_runtime_site())
    except BaseException as exc:  # SystemExit/KeyboardInterrupt も hook 外へ漏らさない。
        # ただし生入力に防護対象が見えるときだけ fails-closed。
        if (_MENTION_RE.search(raw)
                or _PEGASUS_RAW_MENTION_RE.search(raw)
                or _NON_PEGASUS_ADMISSION_RAW_MENTION_RE.search(raw)):
            print(f"guard_bash hook 内部エラー ({type(exc).__name__}) — 防護対象を"
                  "含むため fails-closed で拒否", file=sys.stderr)
            return 2
        return 0
    if not allow:
        print(f"[guard_bash] 拒否: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
