# -*- coding: utf-8 -*-
"""source_digest — variant の identity を「コードの差」まで覆う preprocess 後ハッシュ (D23)。

Phase 3 では coder (LLM) が CCBench の EVOLVE-BLOCK 領域を書き換える。フラグだけで
決まっていた identity (cache_key / variant_id) を**ソース内容**まで覆わないと、
同じ genome で別コードの variant が同一キーを共有し偽 cache hit になる (規律2 への
直接攻撃)。本モジュールはその identity 核を計算する。

設計 (decisions D23、3 レンズ敵対レビューで確定):
- **方式 E:** 対象ソースから #include を除去し `g++ -E -P -undef -nostdinc -Werror=undef
  -D...` で preprocess (= #if/#else 解決 + コメント除去) した出力を sha256。include を
  展開しないので環境非依存・小さい。defines = Options.cmake の `set(CCBENCH_<NAME> <v>
  CACHE ...)` デフォルト (CCBENCH_ 剥がし・クォート剥がし・空値 unset) を base に
  genome.flags で上書き。
- **道Y (digest==実枝の構造保証):** -undef cpp 環境は実ビルドのマクロ環境
  (-DLinux/-DNDEBUG/builtin/TU の GLOBAL_VALUE_DEFINE) と乖離するので、EVOLVE-BLOCK 内の
  生 #if/#ifdef や非決定 builtin (__DATE__ 等) を **hook (Phase3 タスク3) で禁止**し、
  領域内で枝を決めるのは骨格 #if の既知マクロだけにする。本モジュールの -Werror=undef は
  その #if/#elif 側の供給漏れを fails-closed で捕える防壁。
- **#include 死角の閉塞 (phase3.md blocking, 最小案):** preprocess 前に #include 行を
  除去する (環境非依存化) ため、正規化出力だけでは coder の #include 追加/差し替え
  (別ファイルを取り込む = バイナリが変わる) が identity 不変 = stock と alias になり、
  既存バイナリの偽 cache hit で**変更が一度もコンパイルされないまま certified 記録**
  される。対策 = **EVOLVE_BLOCK_SOURCES の #include 行集合が HEAD baseline と異なれば
  resolve で fails-closed abort** (`assert_includes_match_head`)。coder は EVOLVE-BLOCK の
  #if 枝しか触れず #include 追加は禁止 (phase3.md 閉じた領域制約) なので、include 行が
  HEAD と 1 行でも違えば逸脱 = 停止する。「行を identity に織り込んで許す」恒久案は却下:
  include **先ファイルの中身**は identity に乗らず、中身違いの新規 header で variant 間
  alias が残る (2026-07-03 敵対検証 high)。行集合を丸ごと HEAD 固定にすれば include 追加
  そのものを止めるのでこの穴ごと消える。template patch は #include を足さない
  (silo-backoff-fixed.patch) ので inert = 完了条件 1 (inert=stock cache-hit) を壊さない。
  **残る穴 (正直に):** `#if __has_include(...)` や #define 経由の computed include は
  #include 行に現れないので本 assert では捕えない = 道Y の一般問題 (payload 内の生指令)。
  identity 核だけでは完了条件 1 (骨格指令は inert) と両立して塞げない (骨格 #if と payload
  #if の区別に skeleton 抽出が要る) → guard_write の payload 検査 (方針 A の第二防壁) +
  auditor の領域。phase3.md 残存リスクに記録。
- **後方互換:** working-tree の preprocess が HEAD baseline と一致する (= stock/inert) なら
  src トークンを "stock" に正規化し pre-image から省く → silo 8 genome の旧 id を温存。
- **fails-closed:** identity を決める計算は best-effort skip しない (buildcache の commit/nm
  照合と違う)。g++ 不在・rc≠0・git show 失敗・allowlist 外改変は全て RuntimeError で停止。
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from typing import Dict, Iterable

from .model import Genome

# ---- 対象集合 (kickoff の固定集合。動的なマーカー走査はマーカー導入後に格上げ) ----
OPTIONS_CMAKE = "cmake/Options.cmake"
EVOLVE_BLOCK_SOURCES = ("include/backoff.hh",)
# template patch (silo-backoff-fixed.patch) が touch するファイル。working-tree の
# tracked 改変がこれを超えたら coder の編集面が EVOLVE-BLOCK を逸脱した印 → 停止。
ALLOWLIST = frozenset({"cmake/Options.cmake", "include/backoff.hh"})

STOCK = "stock"        # 後方互換: working-tree==HEAD baseline のときの src トークン

_SET_RE = re.compile(
    r"set\(\s*CCBENCH_(\w+)\s+(.*?)\s+CACHE\s+STRING", re.IGNORECASE)
_INCLUDE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*include\b.*$")


def _ccbench_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    repo = os.path.dirname(os.path.dirname(here))         # <repo>
    return os.path.join(repo, "external", "ccbench")


def parse_options_defaults(options_text: str) -> Dict[str, str]:
    """Options.cmake の `set(CCBENCH_<NAME> <v> CACHE STRING ...)` から既定値辞書を作る。

    CCBENCH_ 接頭辞を剥がす (ソース内マクロ名と一致)。値のクォートを剥がし、剥がして
    空 ("") は cmake の remove_definitions=未定義 意味論に合わせ **除外** する
    (`-DINSERT_READ_DELAY_MS=""` の罠を回避、D23)。
    """
    out: Dict[str, str] = {}
    for m in _SET_RE.finditer(options_text):
        name = m.group(1)
        val = m.group(2).strip()
        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
            val = val[1:-1]
        if val == "":
            continue
        out[name] = val
    return out


def _merge_defines(defaults: Dict[str, str], flags: Dict[str, int]) -> Dict[str, str]:
    """Options 既定を base に genome.flags で上書き (未定義マクロ 0 扱い穴を base で塞ぐ)。"""
    merged: Dict[str, str] = dict(defaults)
    for k, v in flags.items():
        merged[k] = str(v)
    return merged


def _cpp_normalize(source_text: str, defines: Dict[str, str], cxx: str) -> str:
    """#include を除去し preprocess (#if/#else 解決 + コメント除去) した正規化出力を返す。

    -undef -nostdinc で組込/系マクロを消し環境非依存に。-Werror=undef で #if/#elif の
    未定義マクロ参照 (= defines 供給漏れ) を rc≠0 にして fails-closed (D23 / 規律6)。
    g++ 不在・preprocess 失敗は RuntimeError (identity 核に best-effort skip を持ち込まない)。
    """
    stripped = _INCLUDE_RE.sub("", source_text)
    args = [cxx, "-E", "-P", "-undef", "-nostdinc", "-Werror=undef"]
    for k in sorted(defines):
        args.append(f"-D{k}={defines[k]}")
    args += ["-x", "c++", "-"]
    try:
        r = subprocess.run(args, input=stripped, capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: preprocess を起動できない ({cxx}: {e}) — identity を確定"
            "できないため fails-closed で停止 (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: preprocess 失敗 (rc={r.returncode})。#if が参照する "
            "マクロが defines に揃っていない (供給漏れ) 疑い → fails-closed。\n"
            f"  {r.stderr.strip()[-500:]}")
    return r.stdout


def _include_lines(source_text: str) -> str:
    """#include 行の列 (順序込み・生バイト)。HEAD 一致検査の比較素材。

    preprocess (_cpp_normalize) は #include を除去してから走るので、include の追加/削除/
    差し替えは正規化出力に現れない (identity 不変の死角)。この列を HEAD baseline と比較して
    1 行でも違えば abort する (assert_includes_match_head)。条件コンパイルで死んでいる枝の
    #include も含む = 安全側 (dead 枝の include 差し替えも止める)。順序込みで比較する
    (include 順序も取り込むヘッダを変えうる)。"""
    return "\n".join(m.group(0) for m in _INCLUDE_RE.finditer(source_text))


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _git_show(ccbench_dir: str, commit: str, rel: str) -> str:
    """submodule の特定 commit のファイル内容 (baseline = patch 前 stock)。"""
    try:
        r = subprocess.run(["git", "-C", ccbench_dir, "show", f"{commit}:{rel}"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: git show 起動失敗 ({e}) — baseline を確定できず "
            "fails-closed (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: git show {commit}:{rel} 失敗 (rc={r.returncode})。"
            f"submodule 未 init / commit 不一致を疑え → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    return r.stdout


def _digest(parts: Iterable[str]) -> str:
    h = hashlib.sha256()
    h.update("\x00".join(parts).encode("utf-8"))
    return h.hexdigest()


def compute(genome: Genome, ccbench_dir: str = "", cxx: str = "g++-13") -> str:
    """working-tree の EVOLVE-BLOCK ソースを genome の defines で正規化した digest。"""
    sub = ccbench_dir or _ccbench_dir()
    defaults = parse_options_defaults(_read(os.path.join(sub, OPTIONS_CMAKE)))
    defines = _merge_defines(defaults, genome.flags)
    parts = [_cpp_normalize(_read(os.path.join(sub, rel)), defines, cxx)
             for rel in EVOLVE_BLOCK_SOURCES]
    return _digest(parts)


def assert_includes_match_head(genome: Genome, ccbench_commit: str,
                               ccbench_dir: str = "", cxx: str = "g++-13") -> None:
    """EVOLVE_BLOCK_SOURCES の #include 行集合が HEAD baseline と一致するか (fails-closed)。

    preprocess は #include を除去してから走る (環境非依存化) ので、include の追加/削除/
    差し替えは digest に現れない = 「別ファイルを取り込みバイナリが変わるのに identity 不変」
    の死角になる (2026-07-03 敵対検証 high)。coder は #if 枝しか触れず #include 追加は
    phase3.md の閉じた領域制約で禁止なので、include 行が HEAD と 1 行でも違えば逸脱として
    停止する。順序込みで比較 (include 順序も取り込むヘッダを変えうる)。git show 失敗は
    identity 核ゆえ RuntimeError (best-effort skip を持ち込まない)。"""
    sub = ccbench_dir or _ccbench_dir()
    for rel in EVOLVE_BLOCK_SOURCES:
        cur = _include_lines(_read(os.path.join(sub, rel)))
        base = _include_lines(_git_show(sub, ccbench_commit, rel))
        if cur != base:
            raise RuntimeError(
                f"source_digest: {rel} の #include 行集合が HEAD baseline と不一致 — "
                "coder の #include 追加/差し替えは preprocess 後 digest に現れず偽 cache hit "
                "の死角になるため停止 (phase3.md 閉じた領域制約 / 2026-07-03 敵対検証 high)。\n"
                f"  HEAD: {base!r}\n  現在: {cur!r}")


def baseline(genome: Genome, ccbench_commit: str, ccbench_dir: str = "",
             cxx: str = "g++-13") -> str:
    """HEAD (commit) の stock ソース (patch 前) を同じ defines で正規化した digest。

    defaults も Options.cmake の HEAD 版から取る (patch が足した CCBENCH_BACKOFF_FIXED が
    無くても HEAD backoff.hh はそれを #if 参照しないので preprocess は変わらない)。
    """
    sub = ccbench_dir or _ccbench_dir()
    defaults = parse_options_defaults(_git_show(sub, ccbench_commit, OPTIONS_CMAKE))
    defines = _merge_defines(defaults, genome.flags)
    parts = [_cpp_normalize(_git_show(sub, ccbench_commit, rel), defines, cxx)
             for rel in EVOLVE_BLOCK_SOURCES]
    return _digest(parts)


def src_token(genome: Genome, ccbench_commit: str, ccbench_dir: str = "",
              cxx: str = "g++-13") -> str:
    """identity に織り込む src トークン。

    working-tree が stock/inert (HEAD baseline と同一 digest) なら "stock" (後方互換:
    pre-image から省かれ旧 id を温存)、coder が枝を変えていれば実 digest を返す。
    """
    cur = compute(genome, ccbench_dir, cxx)
    base = baseline(genome, ccbench_commit, ccbench_dir, cxx)
    return STOCK if cur == base else cur


def assert_worktree_within_allowlist(ccbench_dir: str = "") -> None:
    """submodule working-tree の tracked 改変が ALLOWLIST 内か検査する (fails-closed)。

    coder の編集面は EVOLVE-BLOCK (= template patch が touch するファイル) に閉じている
    べき。それを超えた tracked 改変 (例 transaction.cc の M) は source_digest が覆わない
    偽 hit 源 (D23 finding F-allowlist) なので停止する。untracked (??、build 生成物等) は
    無視する。git が無い/失敗は identity 核なので fails-closed。
    """
    sub = ccbench_dir or _ccbench_dir()
    try:
        r = subprocess.run(["git", "-C", sub, "status", "--porcelain"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: git status 起動失敗 ({e}) — working-tree の健全性を "
            "確認できず fails-closed (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: git status 失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    extra = set()
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        xy, path = line[:2], line[3:]
        if xy == "??":                       # untracked = build 生成物等、ソース改変でない
            continue
        if " -> " in path:                   # rename: "old -> new"
            path = path.split(" -> ")[-1]
        path = path.strip()
        if path not in ALLOWLIST:
            extra.add(path)
    if extra:
        raise RuntimeError(
            "source_digest: ALLOWLIST 外の tracked 改変を検知 → 偽 cache hit を防ぐため "
            f"停止 (coder の編集面が EVOLVE-BLOCK を逸脱)。allowlist={sorted(ALLOWLIST)} "
            f"外={sorted(extra)} (D23)")


def resolve(genome: Genome, ccbench_commit: str, ccbench_dir: str = "",
            cxx: str = "g++-13") -> str:
    """variant の identity (src_token) を確定する単一窓口 = allowlist 検査 + src_token。

    **WAL は書かない** (呼び手が skip 判定・abort 記録を担う) ので、loop (評価前に skip キーを
    決める) と pipeline.evaluate (直接 caller の自己計算) の両方が同じ計算を共有でき、id 確定点が
    二重化しない (D23/D24: identity を消費側まで一致させる)。**fails-closed**: allowlist 逸脱・
    #include 行の HEAD 不一致・preprocess 失敗・git show 失敗は RuntimeError (best-effort skip を
    identity 核に持ち込まない)。"""
    assert_worktree_within_allowlist(ccbench_dir)
    assert_includes_match_head(genome, ccbench_commit, ccbench_dir, cxx)  # #include 死角 (最小案)
    return src_token(genome, ccbench_commit, ccbench_dir, cxx)
