# -*- coding: utf-8 -*-
"""source_digest — variant の identity を「コードの差」まで覆う preprocess 後ハッシュ (D23)。

Phase 3 では coder (LLM) が CCBench の EVOLVE-BLOCK 領域を書き換える。フラグだけで
決まっていた identity (cache_key / variant_id) を**ソース内容**まで覆わないと、
同じ genome で別コードの variant が同一キーを共有し偽 cache hit になる (規律2 への
直接攻撃)。本モジュールはその identity 核を計算する。

設計 (decisions D23、3 レンズ敵対レビューで確定):
- **方式 E:** 対象ソースから #include を除去し `g++ -E -P -nostdinc -Werror=undef
  -D...` で preprocess (= #if/#else 解決 + コメント除去) した出力を sha256。include を
  展開しないので小さい。defines = Options.cmake の `set(CCBENCH_<NAME> <v>
  CACHE ...)` デフォルト (CCBENCH_ 剥がし・クォート剥がし・空値 unset) を base に
  genome.flags で上書き。
- **道Y (digest==実枝の構造保証、D34 で -undef 廃止後):** 組込 builtin (__x86_64__ 等) を
  **実ビルドと同じく定義済みのまま** preprocess する (-undef を外した = D34/案A)。これで
  EVOLVE-BLOCK 内の生 `#ifdef __x86_64__`/`defined()` は digest 環境でも実枝を取り identity に
  正直に反映される (別挙動なら digest が動く = 偽 cache hit しない)。旧設計は -undef で
  builtin を消し「digest と実ビルドの乖離を hook が生 #ifdef 禁止で埋める」前提だったが、
  方針 A で hook payload 検査を削除した後この前提が崩れ builtin definedness の偽 cache hit が
  critical になった (2026-07-04 敵対検証) ため、identity 核側で実環境と揃えて根本封鎖した。
  本モジュールの -Werror=undef は #if/#elif が未定義マクロ (骨格 BACKOFF_FIXED 等の供給漏れ)
  を参照したら rc≠0 で捕える防壁として維持。非決定 builtin (__DATE__ 等) は churn するが
  偽 hit しない (毎回 cache-miss、正しさ不変)。
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
  computed include (`#if __has_include(...)`) は #include 行に現れない別死角だったが、
  T-148 の文脈ガード (下記) が出現を一律 fails-closed で止める (骨格・stock は不使用ゆえ
  skeleton 抽出不要。D34 known-limitation の解消)。
- **マクロ文脈死角の閉塞 (T-148):** TU 注入マクロ (`cc/silo/*_silo.cc:3` の
  `#define GLOBAL_VALUE_DEFINE`) に条件づけられた枝は、単体 preprocess の素文脈では dead に
  なり枝内編集が digest に不可視 = stock 偽 alias だった (`-Werror=undef` は `#ifdef`/
  `defined()` を捕えない)。対策は二層: (1) CONTEXT_MACROS に登録済みのマクロは「素 + define」
  の**両文脈**で preprocess し両枝を identity に織り込む (compute/baseline/_trace_pair_diff。
  builtin definedness の D34/案A と対で、既知の乖離源は digest 側で実枝被覆)。(2) 条件指令が
  参照するマクロが defines ∪ ファイル内 #define ∪ CONTEXT_MACROS ∪ builtin (-dM) に閉じるか
  検査し、未知マクロと __has_include は resolve で fails-closed abort
  (assert_conditional_macros_covered。次の GLOBAL_VALUE_DEFINE 型を沈黙させない)。
  **正直に:** ガードの駆動点は resolve() (単一窓口)。resolve を経ない compute() 直呼びは
  ガード外だが、identity の確定窓口は resolve に一本化済み (D23/D24) で、loop も
  pipeline.evaluate も resolve を通る。
- **後方互換:** working-tree の preprocess が HEAD baseline と一致する (= stock/inert) なら
  src トークンを "stock" に正規化し pre-image から省く → silo 8 genome の旧 id を温存。
- **fails-closed:** identity を決める計算は best-effort skip しない (buildcache の commit/nm
  照合と違う)。g++ 不在・rc≠0・git show 失敗・allowlist 外改変は全て RuntimeError で停止。
"""
from __future__ import annotations

import difflib
import hashlib
import os
import re
import subprocess
from typing import Dict, Iterable, List

from .model import Genome

# ---- 対象集合 (kickoff の固定集合。動的なマーカー走査はマーカー導入後に格上げ) ----
OPTIONS_CMAKE = "cmake/Options.cmake"
# cc/silo/transaction.cc = 後続段 3 (D38) の lock 経路。編集面への追加は段 5 (D38 決定5) で
# auditor live 機械 4 点 (test_lock_path_edit_surface_requires_auditor_live) の gate 下に解禁。
# 段 4 の coder loop (p3_s4_loop.SOURCE_REL) はまだ backoff.hh 単一マーカーのみを駆動する —
# ここでの追加は identity/allowlist 層の地ならしで、実マーケット化 (template patch) は別タスク。
EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")
# template patch (silo-backoff-fixed.patch) が touch するファイル。working-tree の
# tracked 改変がこれを超えたら coder の編集面が EVOLVE-BLOCK を逸脱した印 → 停止。
ALLOWLIST = frozenset({"cmake/Options.cmake", "include/backoff.hh", "cc/silo/transaction.cc"})

STOCK = "stock"        # 後方互換: working-tree==HEAD baseline のときの src トークン

# TU 注入マクロ (T-148): -D でなく取り込み側 TU の #define で供給されるマクロ。単体 preprocess の
# 素文脈では常に未定義 = 条件枝が dead になり、枝内編集が digest に不可視 (stock 偽 alias) になる。
# ここに登録したマクロは compute/baseline/_trace_pair_diff が「素 + define」の両文脈で preprocess し
# 両枝を identity に織り込む。未登録の同型マクロは assert_conditional_macros_covered が fails-closed
# で止める (登録漏れが沈黙しない)。現状 GLOBAL_VALUE_DEFINE のみ (cc/silo/*_silo.cc:3 が #define し
# include/backoff.hh:123 が #ifdef 参照)。2 個以上に増やすときは結合枝 (#if defined(A)&&defined(B))
# の被覆に組合せ文脈が要るか再設計する (現状は単一マクロずつの文脈で十分)。
CONTEXT_MACROS = ("GLOBAL_VALUE_DEFINE",)

_SET_RE = re.compile(
    r"set\(\s*CCBENCH_(\w+)\s+(.*?)\s+CACHE\s+STRING", re.IGNORECASE)
_INCLUDE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*include\b.*$")
_COND_DIRECTIVE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*(?:if|ifdef|ifndef|elif)\b(.*)$")
_DEFINE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*define[ \t]+(\w+)")
_IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_BUILTIN_MACRO_CACHE: Dict[str, frozenset] = {}


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

    -nostdinc で系ヘッダは辿らないが、**組込 builtin (__x86_64__ 等) は実ビルドと同じく
    定義済みのままにする** (D34 / 案A)。旧 -undef は builtin を全消しして環境非依存に
    していたが、digest 環境と実ビルドが乖離し、EVOLVE-BLOCK 内の生 `#ifdef __x86_64__` が
    digest では stock 枝・実ビルドでは別枝を取る**偽 cache hit** を生んだ (方針 A で hook の
    payload 検査を削除し道Y の「生 #ifdef を hook で禁止」前提が消えた後は一次防壁がこれを
    塞げず critical、2026-07-04 敵対検証)。builtin を実環境と揃えれば `#ifdef`/`defined()` が
    digest に正直に反映され偽 hit しない。-Werror=undef は #if/#elif の未定義マクロ参照
    (= 骨格 BACKOFF_FIXED 等の defines 供給漏れ) を rc≠0 にして fails-closed (D23 / 規律6)。
    代償 = digest 値が cxx/環境に依存する (別環境で別値) が、cache は env/<tag> 軸で環境別
    (D13) ゆえ実害なし。非決定 builtin (__DATE__ 等) は churn するが偽 hit しない
    (毎回 cache-miss = 新規ビルド+verify、正しさ不変)。g++ 不在・preprocess 失敗は
    RuntimeError (identity 核に best-effort skip を持ち込まない)。
    """
    stripped = _INCLUDE_RE.sub("", source_text)
    args = [cxx, "-E", "-P", "-nostdinc", "-Werror=undef"]
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


def _context_overlays() -> List[Dict[str, str]]:
    """digest が織り込むマクロ文脈の列: 素文脈 + CONTEXT_MACROS 各 1 個の define 文脈。"""
    return [{}] + [{m: "1"} for m in CONTEXT_MACROS]


def _normalize_contexts(source_text: str, defines: Dict[str, str], cxx: str) -> str:
    """全文脈の正規化出力を文脈タグ付きで連結する (T-148: TU 注入マクロの両枝を identity に乗せる)。

    素文脈だけの preprocess では `#ifdef GLOBAL_VALUE_DEFINE` 枝 (backoff.hh:123、TU の
    #define で供給) が dead になり、枝内編集が digest に不可視 = src_token が 'stock' に化けて
    stock の certified 結果・cache バイナリを継承する (規律2 直撃、実測 2026-07-28)。define 文脈を
    足して両枝を pre-image に織り込めば、どちらの枝の編集も digest を動かす。タグと \\x02 区切りは
    文脈間の出力境界の衝突 (別文脈の連結が偶然同一 bytes になる) を防ぐ。"""
    parts = []
    for overlay in _context_overlays():
        tag = ",".join(f"{k}={v}" for k, v in sorted(overlay.items())) or "base"
        parts.append(f"[ctx:{tag}]\n" + _cpp_normalize(
            source_text, dict(defines, **overlay), cxx))
    return "\x02".join(parts)


def _builtin_macros(cxx: str) -> frozenset:
    """cxx の組込 builtin マクロ名集合 (-dM 照会、プロセス内 cache)。fails-closed。

    D34 案A で builtin は digest 環境でも定義済み = `#ifdef __GNUC__` 等は受理して別 identity に
    する仕様 (test_source_digest_builtin_ifdef_not_aliased_to_stock)。文脈ガードが builtin を
    未知マクロと誤検知しないための既知集合。空集合は照会失敗とみなし停止する (恒真ガード化防止)。"""
    got = _BUILTIN_MACRO_CACHE.get(cxx)
    if got is not None:
        return got
    try:
        r = subprocess.run([cxx, "-dM", "-E", "-x", "c++", "-"],
                           input="", capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: builtin マクロ照会を起動できない ({cxx}: {e}) — 文脈ガードを"
            "確定できないため fails-closed で停止 (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: builtin マクロ照会失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    names = frozenset(m.group(1) for m in _DEFINE_RE.finditer(r.stdout))
    if not names:
        raise RuntimeError(
            "source_digest: builtin マクロ照会が空 — 文脈ガードが恒真化するため停止")
    _BUILTIN_MACRO_CACHE[cxx] = names
    return names


def _assert_conditional_macros_covered(source_text: str, defines: Dict[str, str],
                                       cxx: str, rel: str) -> None:
    """条件指令が参照するマクロが既知集合に閉じるか検査する (fails-closed、T-148 ガード)。

    -Werror=undef は `#if MACRO` の未定義参照しか捕えず、`#ifdef`/`#ifndef`/`defined()` は
    静かに偽枝を取る (g++ 実測 rc=0)。既知集合 = defines (Options 既定 + genome.flags) ∪
    ファイル内 #define ∪ CONTEXT_MACROS (両文脈で被覆済み) ∪ 組込 builtin (-dM、D34 案A で
    受理仕様)。ここに無いマクロの条件枝は digest がどの文脈でも覆えない未知枝 (次の
    GLOBAL_VALUE_DEFINE 型) なので停止する。`__has_include` は #include 行に現れず -nostdinc の
    digest 環境で dead 化して stock に alias する documented hole (D34 known-limitation) だったが、
    骨格・stock ソースは不使用のため出現 = 逸脱として一律停止で塞ぐ (skeleton 抽出は不要)。"""
    scan = source_text.replace("\\\n", " ")          # 行継続を畳んで指令 1 行に正規化
    local_defs = set(_DEFINE_RE.findall(scan))
    known = set(defines) | local_defs | set(CONTEXT_MACROS) | _builtin_macros(cxx)
    unknown = set()
    for m in _COND_DIRECTIVE_RE.finditer(scan):
        expr = re.sub(r"//.*|/\*.*?\*/", " ", m.group(1))     # 指令内コメントは識別子でない
        if "__has_include" in expr:
            raise RuntimeError(
                f"source_digest: {rel} の条件指令に __has_include — computed include は "
                "#include 行検査にも preprocess 後 digest にも現れず (digest 環境は -nostdinc で "
                "header 未発見 = dead 枝)、実ビルドだけ別バイナリになる identity 死角のため停止 "
                "(D34 known-limitation の fails-closed 化、T-148)。\n"
                f"  指令: {m.group(0).strip()!r}")
        for ident in _IDENT_RE.findall(expr):
            if ident == "defined" or ident in ("true", "false"):
                continue
            if ident not in known:
                unknown.add(ident)
    if unknown:
        raise RuntimeError(
            f"source_digest: {rel} の条件指令が未知マクロ {sorted(unknown)} を参照 — defines・"
            "ファイル内 #define・CONTEXT_MACROS・builtin のいずれでもなく、digest はこの条件枝を "
            "どの文脈でも覆えない (TU 注入マクロ GLOBAL_VALUE_DEFINE 型の identity 死角、偽 cache "
            "hit の運び屋) ため fails-closed で停止 (T-148)。既知の文脈マクロなら CONTEXT_MACROS "
            "への登録 (= 両文脈 digest 化) が正しい封鎖で、この検査の緩和ではない (規律2)。")


def assert_conditional_macros_covered(genome: Genome, ccbench_dir: str = "",
                                      cxx: str = "g++-13") -> None:
    """working-tree の EVOLVE_BLOCK_SOURCES 全体に文脈ガードを適用する (resolve が駆動)。"""
    sub = ccbench_dir or _ccbench_dir()
    defaults = parse_options_defaults(_read(os.path.join(sub, OPTIONS_CMAKE)))
    defines = _merge_defines(defaults, genome.flags)
    for rel in EVOLVE_BLOCK_SOURCES:
        _assert_conditional_macros_covered(_read(os.path.join(sub, rel)), defines, cxx, rel)


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
    """working-tree の EVOLVE-BLOCK ソースを genome の defines で正規化した digest。

    T-148: 正規化は全マクロ文脈 (_context_overlays) で取り、TU 注入マクロの条件枝も
    identity に乗せる。baseline と同一の文脈列を使うため stock (working-tree==HEAD) の
    src_token 正規化 = silo 8 golden id は不変。"""
    sub = ccbench_dir or _ccbench_dir()
    defaults = parse_options_defaults(_read(os.path.join(sub, OPTIONS_CMAKE)))
    defines = _merge_defines(defaults, genome.flags)
    parts = [_normalize_contexts(_read(os.path.join(sub, rel)), defines, cxx)
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


def _trace_pair_diff(source_text: str, defines: Dict[str, str], cxx: str) -> List[str]:
    """TRACE=1 と TRACE=0 の正規化出力の差分**内容** (unified diff の +/- 行のみ)。

    ハンクヘッダ (@@ 行番号) は比較素材から除外する — variant の正当な payload 編集
    (TRACE 非依存) でも行数が動けばハンク位置はずれるため、位置を比較に入れると
    偽陽性になる。差分の中身 (どの行が TRACE で増減するか) だけを見る。
    TRACE は最後に明示上書きする (Options.cmake の CCBENCH_TRACE 既定 0 に依存しない。
    genome.flags への TRACE 混入は model.Genome が禁止済み)。
    T-148: 差分も全マクロ文脈で取る — 素文脈だけだと `#ifdef GLOBAL_VALUE_DEFINE` の内側に
    `#if TRACE` を隠す攻撃が両 TRACE 値とも dead で D_variant==D_stock になり素通りする
    (規律1 の穴)。文脈タグを行に前置し、別文脈間の差分相殺も防ぐ。"""
    out: List[str] = []
    for overlay in _context_overlays():
        tag = ",".join(f"{k}={v}" for k, v in sorted(overlay.items())) or "base"
        base = dict(defines, **overlay)
        p1 = _cpp_normalize(source_text, dict(base, TRACE="1"), cxx)
        p0 = _cpp_normalize(source_text, dict(base, TRACE="0"), cxx)
        diff = difflib.unified_diff(p0.splitlines(), p1.splitlines(), n=0, lineterm="")
        out.extend(f"[ctx:{tag}]{ln}" for ln in diff
                   if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
    return out


def assert_trace_diff_matches_head(genome: Genome, ccbench_commit: str,
                                   ccbench_dir: str = "", cxx: str = "g++-13") -> None:
    """観測者効果の二重検査 — diff-of-diffs (phase3.md blocking / D30 一次防壁)。

    述語: working-tree の preprocess(TRACE=1) − preprocess(TRACE=0) の差分 D_variant が、
    pinned HEAD から同様に取った D_stock と**一致**する。つまり「variant が TRACE 条件付き
    コードを追加/改変していない = trace/perf ビルドの差は stock の trace-hook 由来のみ」を
    機械保証する (規律1: 観測者効果の分離)。nm の name-based 検査 (_assert_no_trace_symbols)
    が見逃す data-structure 観測者効果・`#ifdef TRACE` の内側に挙動差を隠す攻撃も、
    D_variant≠D_stock として捕える。対象 = EVOLVE_BLOCK_SOURCES (coder の編集面全体。
    それ以外の worktree 改変は assert_worktree_within_allowlist が既に遮断)。

    fails-closed: diff 不一致・preprocess 取得不能 (RuntimeError 伝播) とも abort
    (警告に格下げしない)。**保証しないこと (正直に):** 検証専用メタデータが #if TRACE の
    **外** (両ビルド共通) に常駐するケースはこの述語では判定不能 — その場合コストは perf
    ビルドにも乗り fitness が自己ペナルティを受けるため false-green にはならず、意味判定は
    auditor / 人間レビュー領域 (phase3.md タスク定義)。"""
    sub = ccbench_dir or _ccbench_dir()
    cur_defaults = parse_options_defaults(_read(os.path.join(sub, OPTIONS_CMAKE)))
    head_defaults = parse_options_defaults(_git_show(sub, ccbench_commit, OPTIONS_CMAKE))
    for rel in EVOLVE_BLOCK_SOURCES:
        d_var = _trace_pair_diff(_read(os.path.join(sub, rel)),
                                 _merge_defines(cur_defaults, genome.flags), cxx)
        d_stock = _trace_pair_diff(_git_show(sub, ccbench_commit, rel),
                                   _merge_defines(head_defaults, genome.flags), cxx)
        if d_var != d_stock:
            raise RuntimeError(
                f"source_digest: 観測者効果の二重検査 (diff-of-diffs) 不一致 — {rel} の "
                "TRACE=1/TRACE=0 preprocess 差分が pinned HEAD の同差分と食い違う。variant が "
                "TRACE 条件付きコードを追加/改変した疑い (規律1: 検証コードの perf ビルド混入、"
                "または #ifdef TRACE 内側への挙動差の隠蔽) → fails-closed で停止 "
                "(phase3.md blocking / D30)。\n"
                f"  D_stock ({len(d_stock)} 行): {d_stock[:8]!r}\n"
                f"  D_variant ({len(d_var)} 行): {d_var[:8]!r}")


def baseline(genome: Genome, ccbench_commit: str, ccbench_dir: str = "",
             cxx: str = "g++-13") -> str:
    """HEAD (commit) の stock ソース (patch 前) を同じ defines で正規化した digest。

    defaults も Options.cmake の HEAD 版から取る (patch が足した CCBENCH_BACKOFF_FIXED が
    無くても HEAD backoff.hh はそれを #if 参照しないので preprocess は変わらない)。
    """
    sub = ccbench_dir or _ccbench_dir()
    defaults = parse_options_defaults(_git_show(sub, ccbench_commit, OPTIONS_CMAKE))
    defines = _merge_defines(defaults, genome.flags)
    parts = [_normalize_contexts(_git_show(sub, ccbench_commit, rel), defines, cxx)
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
    #include 行の HEAD 不一致・条件指令の未知マクロ / __has_include・preprocess 失敗・git show
    失敗は RuntimeError (best-effort skip を identity 核に持ち込まない)。"""
    assert_worktree_within_allowlist(ccbench_dir)
    assert_includes_match_head(genome, ccbench_commit, ccbench_dir, cxx)  # #include 死角 (最小案)
    assert_conditional_macros_covered(genome, ccbench_dir, cxx)           # マクロ文脈死角 (T-148)
    return src_token(genome, ccbench_commit, ccbench_dir, cxx)
