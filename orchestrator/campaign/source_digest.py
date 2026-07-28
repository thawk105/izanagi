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
  参照するマクロが defines ∪ 先行する #define ∪ CONTEXT_MACROS ∪ builtin (-dM) に閉じるか
  検査し、未知マクロと __has_include は resolve で fails-closed abort
  (assert_conditional_macros_covered。次の GLOBAL_VALUE_DEFINE 型を沈黙させない)。(3) digest の
  -D 集合自体を**実 TU 供給集合**へ揃える (parse_supplied_macros + PLATFORM_MACROS +
  BUILD_FLAGS) — cmake CACHE 全体を一律 -D すると他 protocol 専用マクロ (DEBUG_MSG 等) が
  digest だけ定義済みになり、`#ifdef` で枝が逆転する (段 6 レビュー B、2026-07-28)。
  **正直に (駆動点):** ガードを駆動するのは resolve() であって compute()/baseline()/src_token()
  単体ではない。legacy `buildcache.build(src_token=None)` は src_token() を直接呼ぶため、その
  経路のガードは build 出口の `_recheck_src_token` (resolve を通る) まで遅れる。現行 driver
  (S1/S6/S8a・loop・p3_s4_loop) は patch 適用中に resolve() した token を評価へ渡す。
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

# 実 TU に無条件で入るがマクロ供給表に現れないもの (ProtocolHelpers.cmake が
# `CMAKE_SYSTEM_NAME STREQUAL "Linux"` で `target_compile_definitions(... Linux)` する)。
# 計測層は Linux 専有 (D13/環境契約) なので digest 側も定義済みで揃える。値なしの純 definedness。
PLATFORM_MACROS = {"Linux": "1"}
# 実ビルドのコンパイル環境フラグ。digest がこれを外したまま preprocess/照会すると条件枝が
# 実ビルドと逆転する (段 6 レビュー、いずれも g++-12 実測):
# - `-std=c++20`: cmake/CompileOptions.cmake の `CMAKE_CXX_STANDARD 20` + `CXX_EXTENSIONS OFF`。
#   外すと `#if __cplusplus >= 202002L` が逆転し、認識される指令 (`#elifdef` 等) も変わる。
# - `-O3 -DNDEBUG`: buildcache が `-DCMAKE_BUILD_TYPE=Release` で configure し、CompileOptions.cmake
#   は RELEASE フラグを上書きしないため GNU 既定のこの 2 つが実 TU に必ず入る。外すと
#   `__NO_INLINE__` / `__OPTIMIZE__` / `NDEBUG` の definedness が反転する。
BUILD_FLAGS = ("-std=c++20", "-O3", "-DNDEBUG")
# digest と実ビルドで同一に評価される組込演算子 (同一 cxx・同一 std なので乖離しない) =
# 受理してよい。`__has_include` 系だけは header 探索パスに依存し digest が -nostdinc で
# 常に 0 に倒れるため別扱い (fails-closed、下記ガード)。
KNOWN_HAS_OPERATORS = frozenset({
    "__has_builtin", "__has_attribute", "__has_cpp_attribute", "__has_c_attribute",
    "__has_feature", "__has_extension"})
INCLUDE_PROBE_OPERATORS = ("__has_include_next", "__has_include")

_SET_RE = re.compile(
    r"set\(\s*CCBENCH_(\w+)\s+(.*?)\s+CACHE\s+STRING", re.IGNORECASE)
_INCLUDE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*include\b.*$")
_COND_DIRECTIVE_RE = re.compile(
    r"(?m)^[ \t]*#[ \t]*(?:if|ifdef|ifndef|elif|elifdef|elifndef)\b(.*)$")
_DEFINE_RE = re.compile(r"(?m)^[ \t]*#[ \t]*define[ \t]+(\w+)[^\n]*")
_IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_RAW_STRING_RE = re.compile(r'(?:u8|u|U|L)?R"')
# `__has_builtin(__builtin_expect)` の引数は builtin 名や属性名でマクロ参照ではない。
# 演算子ごと式から落としてから識別子を拾う (落とさないと引数を未知マクロと誤判定する)。
_HAS_OP_CALL_RE = re.compile(r"\b__has_\w+\s*\([^()]*\)")
# CMake が TU へ渡すマクロ供給表の行 (`NAME=${CCBENCH_NAME}`)。universal は Options.cmake の
# ccbench_universal_definitions()、protocol 固有は cc/<protocol>/CMakeLists.txt の OPTIONS。
_UNIVERSAL_FN_RE = re.compile(
    r"function\(\s*ccbench_universal_definitions.*?endfunction\(\)", re.DOTALL)
_SUPPLY_RE = re.compile(r"(\w+)=\$\{CCBENCH_(\w+)\}")
_PROTOCOL_CMAKE = "cc/{protocol}/CMakeLists.txt"
_BUILTIN_MACRO_CACHE: Dict[tuple, frozenset] = {}


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


def parse_supplied_macros(options_text: str, protocol_cmake_text: str) -> frozenset:
    """実 TU へ実際に `-D` される マクロ名の集合を CMake ソースから静的に取る (fails-closed)。

    Options.cmake の全 `set(CCBENCH_<NAME> ...)` は cmake CACHE 変数にすぎず、TU に届くのは
    `ccbench_universal_definitions()` の供給表 + protocol の `ccbench_add_protocol(... OPTIONS ...)`
    に列挙されたものだけである (残りは他 protocol 専用。例 `DEBUG_MSG` は oze 用)。digest が
    Options 既定を一律 `-D` すると「digest では定義済み・実 silo TU では未定義」の乖離が生まれ、
    `#ifdef DEBUG_MSG` で枝が逆転して偽 cache hit になる (レビュー B must-fix 1、T-148 fix round)。
    variant patch は protocol CMakeLists (ALLOWLIST 外) でなく Options.cmake の供給表へ追記する
    規約 (silo-backoff-fixed.patch / silo-sort-variant.patch) なので、patch 適用後もここが追随する。
    configure 出力 (compile_commands.json) でなく CMake ソースを読むため D23 の鶏卵は起きない。
    パース結果が空なら CMake 構造の変化とみなし停止する (恒真化防止)。"""
    fn = _UNIVERSAL_FN_RE.search(options_text)
    if not fn:
        raise RuntimeError(
            "source_digest: Options.cmake に ccbench_universal_definitions() が見つからない — "
            "実 TU のマクロ供給集合を確定できないため fails-closed (T-148)")
    names = {m.group(1) for m in _SUPPLY_RE.finditer(fn.group(0))}
    names |= {m.group(1) for m in _SUPPLY_RE.finditer(protocol_cmake_text)}
    if not names:
        raise RuntimeError(
            "source_digest: マクロ供給表が空 — CMake 構造が変わった疑い → fails-closed (T-148)")
    return frozenset(names)


def _merge_defines(defaults: Dict[str, str], flags: Dict[str, int],
                   supplied: Iterable[str] = ()) -> Dict[str, str]:
    """Options 既定を base に genome.flags で上書き (未定義マクロ 0 扱い穴を base で塞ぐ)。

    T-148 fix round: `supplied` (実 TU へ届くマクロ名集合、parse_supplied_macros) を渡すと、
    それに含まれないマクロを落とし PLATFORM_MACROS を足して**実ビルドの -D 集合と揃える**。
    genome.flags も同じフィルタに掛ける — 供給表に無いフラグは cmake CACHE に入るだけで TU に
    届かず、digest だけが定義済みになる乖離を生むため。"""
    merged: Dict[str, str] = dict(defaults)
    for k, v in flags.items():
        merged[k] = str(v)
    if len(CONTEXT_MACROS) > 1:
        # 単発文脈列は結合枝 (#if defined(A) && defined(B)) を覆えない。増やすなら
        # 組合せ文脈への再設計が要るので、増えた時点で機械的に止める (段 6 レビュー A nit 3)。
        raise RuntimeError(
            "source_digest: CONTEXT_MACROS が 2 個以上 — 単発文脈列では結合枝を覆えないため停止 "
            "(組合せ文脈への再設計が要る、T-148)")
    if supplied:
        keep = set(supplied)
        clash = keep & set(CONTEXT_MACROS)
        if clash:
            # 文脈マクロが実 TU 供給集合にも居ると素文脈が define 文脈へ縮退し、
            # 反対枝 (#ifndef 側) が両文脈とも dead = 再び identity 死角になる。
            raise RuntimeError(
                f"source_digest: CONTEXT_MACROS {sorted(clash)} が実 TU 供給集合にも存在 — "
                "素文脈が縮退して反対枝が digest から落ちるため停止 (T-148)。供給されるように"
                "なったマクロは CONTEXT_MACROS から外し、両枝の被覆方法を再設計する。")
        merged = {k: v for k, v in merged.items() if k in keep}
        merged.update(PLATFORM_MACROS)
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
    args = [cxx, "-E", "-P", "-nostdinc", "-Werror=undef", *BUILD_FLAGS]
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


def _dump_macros(source_text: str, defines: Dict[str, str], cxx: str) -> frozenset:
    """`-dM` で「この環境・このソースで実際に定義されるマクロ」名の集合を取る (fails-closed)。

    実ビルドと同じ `BUILD_FLAGS` で照会する。`-Werror=undef` は付けない (未知マクロを含む
    ソースでも定義状態は取れる必要があるため — 未知の判定はガード本体の仕事)。"""
    args = [cxx, "-dM", "-E", "-nostdinc", *BUILD_FLAGS]
    for k in sorted(defines):
        args.append(f"-D{k}={defines[k]}")
    args += ["-x", "c++", "-"]
    try:
        r = subprocess.run(args, input=_INCLUDE_RE.sub("", source_text),
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"source_digest: マクロ定義状態の照会を起動できない ({cxx}: {e}) — 文脈ガードを"
            "確定できないため fails-closed で停止 (D23)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"source_digest: マクロ定義状態の照会に失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    names = frozenset(m.group(1) for m in _DEFINE_RE.finditer(r.stdout))
    if not names:
        raise RuntimeError(
            "source_digest: マクロ定義状態の照会が空 — 文脈ガードが恒真化するため停止")
    return names


def _environment_macros(defines: Dict[str, str], cxx: str) -> frozenset:
    """ソース非依存の定義済みマクロ (builtin + BUILD_FLAGS + -D)。プロセス内 cache。

    D34 案A で builtin は digest 環境でも定義済み = `#ifdef __GNUC__` 等は受理して別 identity に
    する仕様 (test_source_digest_builtin_ifdef_not_aliased_to_stock)。照会フラグは実ビルドに
    揃える — `-O3 -DNDEBUG` を外すと `__NO_INLINE__` 等が「digest では定義済み・実ビルドでは
    未定義」になり、その否定形の枝を digest だけが dead 扱いする (段 6 レビュー A must-fix 4)。"""
    key = (cxx, tuple(sorted(defines.items())))
    got = _BUILTIN_MACRO_CACHE.get(key)
    if got is None:
        got = _dump_macros("", defines, cxx)
        _BUILTIN_MACRO_CACHE[key] = got
    return got


def _lex_normalize(source_text: str, rel: str = "") -> str:
    """翻訳フェーズ 2-3 の近似: 行継続とコメントを畳み、リテラル中身を消す (fails-closed)。

    条件指令の静的走査を素の正規表現でやると C++ の字句と食い違い、ガードが素通りする
    (段 6 レビュー、いずれも g++ 実測で偽 STOCK alias を構築):
    - `#/**/ifdef FOO` は正規の条件指令。`#` 直後に空白しか許さない走査は見落とす (B must-fix 2)。
    - 複数行コメントは**空白 1 個**であって改行ではない。`#if 1 /*<改行>*/ && defined(X)` は
      1 論理行の指令なので、改行を保存すると続きの被演算子が走査から落ちる (A must-fix 1)。
      したがってここではブロックコメント内の改行を残さない (行数は保存しない — 診断は行番号でなく
      指令の逐語を出す)。行コメント `//` の改行は規格どおり残す。
    - `#if 'A' == 65` の文字定数は識別子でない。拾うと受理集合を不当に狭める (B must-fix 4)。
      一方 `1'000` の桁区切りはリテラル開始ではない — リテラル扱いすると閉じ引用符を探して
      以降のソースを飲み込み、その先の指令すべてがガードから消える (A must-fix 3)。
    - 未終端のコメント/リテラルと raw string は「解釈不能」であり、静かに全消しして受理すると
      ガードが恒真化する。identity 核の契約どおり停止する (A should 3)。"""
    src = source_text.replace("\\\n", "")
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            if j < 0:
                raise RuntimeError(
                    f"source_digest: {rel} に未終端のブロックコメント — 条件指令を字句として"
                    "解釈できないため fails-closed (T-148)")
            out.append(" ")
            i = j + 2
        elif c == "/" and nxt == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" ")
            i = j
        elif c in "Ru8UL" and _RAW_STRING_RE.match(src, i):
            raise RuntimeError(
                f"source_digest: {rel} に raw string literal — 字句正規化が未対応のため "
                "fails-closed (骨格・stock は不使用、T-148)")
        elif c == "'" and i and (src[i - 1].isalnum() or src[i - 1] == "_"):
            out.append("'")          # 数値の桁区切り (1'000)。リテラル開始ではない
            i += 1
        elif c in "\"'":
            j, quote = i + 1, c
            while j < n and src[j] not in (quote, "\n"):
                j += 2 if src[j] == "\\" else 1
            if j >= n or src[j] == "\n":
                raise RuntimeError(
                    f"source_digest: {rel} に未終端の文字列/文字リテラル — 条件指令を字句として"
                    "解釈できないため fails-closed (T-148)")
            out.append(quote + quote)
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _assert_conditional_macros_covered(source_text: str, defines: Dict[str, str],
                                       cxx: str, rel: str) -> None:
    """条件指令が参照するマクロが既知集合に閉じるか検査する (fails-closed、T-148 ガード)。

    -Werror=undef は `#if MACRO` の未定義参照しか捕えず、`#ifdef`/`#ifndef`/`defined()` は
    静かに偽枝を取る (g++ 実測 rc=0)。既知集合 = defines (実 TU 供給集合まで絞った Options 既定 +
    genome.flags + PLATFORM_MACROS) ∪ **その指令より前の** ファイル内 #define ∪ CONTEXT_MACROS
    (両文脈で被覆済み) ∪ 組込 builtin (-dM、D34 案A で受理仕様)。ここに無いマクロの条件枝は
    digest がどの文脈でも覆えない未知枝 (次の GLOBAL_VALUE_DEFINE 型) なので停止する。

    T-148 fix round (段 6 レビュー A/B):
    - 走査対象は `_lex_normalize` を通した字句で、`#/**/ifdef` 形の指令も、コメントで分断された
      論理行の続きも検出する。リテラル中身は識別子にしない。不整形は停止する。
    - `#define` の既知化は「**その指令より前**に静的に現れ、**かつ実際に定義される**」ものに限る。
      後ろの `#define` はその時点で未定義であり、`#if 0` 等の dead 枝にある `#define` は
      そもそも定義されない — どちらも既知に数えると未知マクロを洗浄してしまう (A must-fix 2)。
      実定義は `-dM` の実照会で取る (`#undef` も自動的に反映される)。
    - `__has_include` / `__has_include_next` は条件式の literal 出現だけでなく、そこへ
      **展開されうる `#define` 本体**も止める (`#define IZ_HAS __has_include(...)` → `#if IZ_HAS`
      の迂回、B must-fix 3)。#include 行検査にも preprocess 後 digest にも現れず (digest 環境は
      -nostdinc で header 未発見 = dead 枝)、実ビルドだけ別バイナリになる identity 死角
      (D34 known-limitation の fails-closed 化)。header 探索に依存しない他の `__has_*` 演算子は
      digest と実ビルドで同一に評価されるので受理する — 引数 (builtin 名・属性名) はマクロ参照
      ではないので演算子ごと式から落としてから識別子を拾う (A should 2)。
    - 予約識別子 (`__NO_INLINE__` 等) でも、この環境照会に現れないものは受理しない。`BUILD_FLAGS`
      で実ビルドに揃えた範囲の外に未知のフラグ差が残りうる以上、「定義されていない予約名の
      definedness テスト」は乖離候補として停止側に倒す (A must-fix 4 の残余。骨格・stock は
      いずれも使用しないので実害はない)。"""
    scan = _lex_normalize(source_text, rel)
    for probe in INCLUDE_PROBE_OPERATORS:
        if probe not in scan:
            continue
        for m in _DEFINE_RE.finditer(scan):
            if probe in m.group(0):
                raise RuntimeError(
                    f"source_digest: {rel} の #define 本体に {probe} — 条件式へ展開されると "
                    "computed include が digest を迂回する (literal 検査の裏をかく経路) ため停止 "
                    f"(T-148)。\n  定義: {m.group(0).strip()!r}")
    defs_at: List[tuple] = [(m.start(), m.group(1)) for m in _DEFINE_RE.finditer(scan)]
    live = _dump_macros(source_text, defines, cxx) if defs_at else frozenset()
    base_known = set(defines) | set(CONTEXT_MACROS) | _environment_macros(defines, cxx)
    unknown = set()
    for m in _COND_DIRECTIVE_RE.finditer(scan):
        expr = m.group(1)
        for probe in INCLUDE_PROBE_OPERATORS:
            if probe in expr:
                raise RuntimeError(
                    f"source_digest: {rel} の条件指令に {probe} — computed include は "
                    "#include 行検査にも preprocess 後 digest にも現れず (digest 環境は -nostdinc "
                    "で header 未発見 = dead 枝)、実ビルドだけ別バイナリになる identity 死角の"
                    "ため停止 (D34 known-limitation の fails-closed 化、T-148)。\n"
                    f"  指令: {m.group(0).strip()!r}")
        known = base_known | {name for pos, name in defs_at if pos < m.start() and name in live}
        for ident in _IDENT_RE.findall(_HAS_OP_CALL_RE.sub(" ", expr)):
            if ident in ("defined", "true", "false") or ident in KNOWN_HAS_OPERATORS:
                continue
            if ident not in known:
                unknown.add(ident)
    if unknown:
        raise RuntimeError(
            f"source_digest: {rel} の条件指令が未知マクロ {sorted(unknown)} を参照 — 実 TU 供給"
            "マクロ・先行する #define・CONTEXT_MACROS・builtin のいずれでもなく、digest はこの"
            "条件枝をどの文脈でも覆えない (TU 注入マクロ GLOBAL_VALUE_DEFINE 型の identity 死角、"
            "偽 cache hit の運び屋) ため fails-closed で停止 (T-148)。既知の文脈マクロなら "
            "CONTEXT_MACROS への登録 (= 両文脈 digest 化) が正しい封鎖で、この検査の緩和ではない "
            "(規律2)。")


def assert_conditional_macros_covered(genome: Genome, ccbench_dir: str = "",
                                      cxx: str = "g++-13") -> None:
    """working-tree の EVOLVE_BLOCK_SOURCES 全体に文脈ガードを適用する (resolve が駆動)。"""
    sub = ccbench_dir or _ccbench_dir()
    defines = _worktree_defines(sub, genome)
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
    """identity 経路のファイル読取。失敗は RuntimeError に正規化する。

    呼び手 (`loop`・`pipeline.evaluate`・`buildcache._recheck_src_token`) は identity 確定の
    失敗を `except RuntimeError` で受けて variant 単位の abort に隔離する。`OSError` を
    そのまま投げると campaign 全体が落ち、build dir の破棄 (`_discard_build_dir`) も走らない
    (段 6 レビュー A should 4)。HEAD 側 (`_git_show`) は既に RuntimeError 化してあり、
    working-tree 側だけ非対称だった。"""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise RuntimeError(
            f"source_digest: {path} を読めない ({e}) — identity を確定できないため "
            "fails-closed で停止 (D23)") from e


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


def _protocol_cmake_rel(genome: Genome) -> str:
    return _PROTOCOL_CMAKE.format(protocol=genome.protocol)


def _worktree_defines(sub: str, genome: Genome) -> Dict[str, str]:
    """working-tree 版の実効 defines (実 TU 供給集合に揃えたもの、T-148 fix round)。"""
    options_text = _read(os.path.join(sub, OPTIONS_CMAKE))
    proto_text = _read(os.path.join(sub, _protocol_cmake_rel(genome)))
    supplied = parse_supplied_macros(options_text, proto_text)
    return _merge_defines(parse_options_defaults(options_text), genome.flags, supplied)


def _head_defines(sub: str, genome: Genome, ccbench_commit: str) -> Dict[str, str]:
    """HEAD (pin) 版の実効 defines。baseline と working-tree で同じ絞り方を使う。"""
    options_text = _git_show(sub, ccbench_commit, OPTIONS_CMAKE)
    proto_text = _git_show(sub, ccbench_commit, _protocol_cmake_rel(genome))
    supplied = parse_supplied_macros(options_text, proto_text)
    return _merge_defines(parse_options_defaults(options_text), genome.flags, supplied)


def compute(genome: Genome, ccbench_dir: str = "", cxx: str = "g++-13") -> str:
    """working-tree の EVOLVE-BLOCK ソースを genome の defines で正規化した digest。

    T-148: 正規化は全マクロ文脈 (_context_overlays) で取り、TU 注入マクロの条件枝も
    identity に乗せる。defines は実 TU 供給集合まで絞る (_worktree_defines)。baseline と
    同一の文脈列・同一の絞り方を使うため stock (working-tree==HEAD) の src_token 正規化 =
    silo 8 golden id は不変。"""
    sub = ccbench_dir or _ccbench_dir()
    defines = _worktree_defines(sub, genome)
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
    cur_defines = _worktree_defines(sub, genome)
    head_defines = _head_defines(sub, genome, ccbench_commit)
    for rel in EVOLVE_BLOCK_SOURCES:
        d_var = _trace_pair_diff(_read(os.path.join(sub, rel)), cur_defines, cxx)
        d_stock = _trace_pair_diff(_git_show(sub, ccbench_commit, rel), head_defines, cxx)
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
    供給集合の絞り込み (T-148 fix round) も HEAD 版 CMake から取り、working-tree 側と
    同じ規則で行う。
    """
    sub = ccbench_dir or _ccbench_dir()
    defines = _head_defines(sub, genome, ccbench_commit)
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
