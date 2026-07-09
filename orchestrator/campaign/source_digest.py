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
  **残る穴 (正直に):** `#if __has_include(...)` や #define 経由の computed include は
  #include 行に現れず、かつ -nostdinc で header 未発見なら digest 環境で __has_include=0 に
  倒れる (実ビルドで include path 上に header があれば別バイナリ)。本 assert では捕えない =
  道Y の一般問題 (payload 内の生指令)。identity 核だけでは完了条件 1 (骨格指令は inert) と
  両立して塞げない (骨格 #if と payload #if の区別に skeleton 抽出が要る)。方針 A で hook の
  payload 検査は削除したので退避先は **auditor + 規律6 の独立監査**のみ (git status に
  `?? evil.hh` + `M backoff.hh` の __has_include として露出し、2026-07-04 敵対検証で捕捉可能
  と実証)。phase3.md 残存リスクに記録。builtin definedness (`#ifdef __x86_64__`) の方は
  D34/案A で digest に反映して封鎖済み — 残るのは header 存在に依存する computed include のみ。
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


def _trace_pair_diff(source_text: str, defines: Dict[str, str], cxx: str) -> List[str]:
    """TRACE=1 と TRACE=0 の正規化出力の差分**内容** (unified diff の +/- 行のみ)。

    ハンクヘッダ (@@ 行番号) は比較素材から除外する — variant の正当な payload 編集
    (TRACE 非依存) でも行数が動けばハンク位置はずれるため、位置を比較に入れると
    偽陽性になる。差分の中身 (どの行が TRACE で増減するか) だけを見る。
    TRACE は最後に明示上書きする (Options.cmake の CCBENCH_TRACE 既定 0 に依存しない。
    genome.flags への TRACE 混入は model.Genome が禁止済み)。"""
    d1 = dict(defines, TRACE="1")
    d0 = dict(defines, TRACE="0")
    p1 = _cpp_normalize(source_text, d1, cxx)
    p0 = _cpp_normalize(source_text, d0, cxx)
    diff = difflib.unified_diff(p0.splitlines(), p1.splitlines(), n=0, lineterm="")
    return [ln for ln in diff
            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]


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
