# -*- coding: utf-8 -*-
"""genome → バイナリ。内容キーのビルドキャッシュ (orchestrator-design.md D の思想)。

同じ最適化組合せ (genome) を再ビルドしない。キャッシュキー = (protocol, genome 正準,
ccbench-commit, trace 有無)。**trace と perf は別ビルド** (絶対規律1): verify は
trace-enabled (`-DCCBENCH_TRACE=1`)、bench は trace-disabled (`=0`)。

ビルドキャッシュは campaign 非依存 (同じ genome は全 campaign で共有) なので、
ccbench submodule 下の固定キャッシュ root に置く。ccache が効くので warm rebuild は速い。
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from . import source_digest
from .model import Genome

# バイナリ digest の二系列契約 (敵対相談 A-6 裁定):
#   - 16 文字系列 = `sha256-prefix-16 / legacy-display-only`。WAL の `trace_bin`/`perf_bin`、
#     calibration の `binary_hash`、`BuildResult.bin_hash` が該当。provenance 表示専用で、
#     identity 照合には使わない。full 値の接頭辞であって identity ではない。
#   - 64 文字系列 = `exact 64 lowercase hex`。`BuildResult.bin_sha256`、WAL の
#     `*_bin_sha256`、`full_sha256()`/`assert_binary_sha256()` が該当。照合はこの系列だけで
#     行い、prefix 照合・prefix fallback・現在 disk からの遡及 backfill は禁止する。
_SHA256_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")


class BinaryDigestError(RuntimeError):
    """バイナリ digest の計算不能・期待値不正など (path/cause を保持, 規律3)。"""

    def __init__(self, path, *, cause=None, message: str = ""):
        self.path = str(path)
        self.cause = cause
        super().__init__(message or f"binary digest error: {self.path}")


class BinaryDigestMismatch(BinaryDigestError):
    """記録済み 64 文字 sha256 と実測が食い違った (path/expected/actual を保持)。"""

    def __init__(self, path, expected: str, actual: str, *, cause=None):
        self.expected = expected
        self.actual = actual
        super().__init__(
            path, cause=cause,
            message=(f"binary sha256 不一致: {path} "
                     f"(expected={expected} actual={actual})"))


def is_full_sha256(value) -> bool:
    """`value` が exact 64 lowercase hex (照合系列の正規形) かを判定する。

    prefix 照合・大文字許容・fallback はしない (A-6)。"""
    return isinstance(value, str) and bool(_SHA256_HEX64.match(value))


def full_sha256(path) -> str:
    """バイナリ内容の **full** sha256 hexdigest (64 文字, truncate しない)。

    1MB チャンク読み。読取不能は握りつぶさず `BinaryDigestError` (cause 保持) に倒す
    (規律3)。返り値は exact 64 lowercase hex 系列 (上記契約)。"""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    except OSError as exc:
        raise BinaryDigestError(
            path, cause=exc,
            message=f"バイナリ sha256 を計算できない: {path}: {exc}") from exc
    return h.hexdigest()


def assert_binary_sha256(path, expected: str) -> None:
    """`path` の full sha256 が `expected` (exact 64 lowercase hex) と一致することを assert。

    成功時のみ復帰する (bool を返さない, A-5)。`expected` が 64 桁 lowercase hex 以外
    (15/16/63/65 桁・非 hex・大文字を含む) は即 `BinaryDigestError` で拒否し、prefix 照合・
    prefix fallback は一切しない (A-6, fail-closed)。不一致は `BinaryDigestMismatch`。"""
    if not is_full_sha256(expected):
        raise BinaryDigestError(
            path,
            message=(f"expected が exact 64 lowercase hex でない: {expected!r} "
                     "(prefix 照合・fallback はしない, A-6)"))
    actual = full_sha256(path)
    if actual != expected:
        raise BinaryDigestMismatch(path, expected, actual)


def _ccbench_dir() -> str:
    # buildcache.py = <repo>/orchestrator/campaign/buildcache.py → repo は dirname×2
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    repo = os.path.dirname(os.path.dirname(here))         # <repo>
    return os.path.join(repo, "external", "ccbench")


DEFAULT_CC, DEFAULT_CXX = "gcc-13", "g++-13"


def cache_key(genome: Genome, ccbench_commit: str, trace: bool,
              src_token: str = source_digest.STOCK,
              cc: str = DEFAULT_CC, cxx: str = DEFAULT_CXX) -> str:
    """内容キー。Phase 3 で coder がコードを書き換えるので src_token (preprocess 後
    ハッシュ, D23) を pre-image に織り込み、同 genome 別ソースの偽 hit を防ぐ。
    stock (working-tree==HEAD) は src を省き旧キーを温存 (後方互換)。
    ツールチェーン (cc/cxx) も pre-image に織り込む — コンパイラを替えて再計測すると
    既評価 genome だけ旧コンパイラのバイナリで偽 hit し、同一 campaign 内で baseline と
    variant のビルド条件が食い違う (コンパイラ差はバックオフ級の差を容易に上回る)。
    既定ツールチェーンは省いて旧キーを温存 (src_token と同型の後方互換規則)。"""
    src = "" if src_token == source_digest.STOCK else f"|src={src_token}"
    tc = "" if (cc, cxx) == (DEFAULT_CC, DEFAULT_CXX) else f"|cc={cc}|cxx={cxx}"
    raw = f"{genome.canonical()}|{ccbench_commit}|trace={int(trace)}{src}{tc}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"{genome.protocol}_{h}_t{int(trace)}"


@dataclass(frozen=True)
class BuildResult:
    genome: Genome
    trace: bool
    binary: str             # ycsb_<protocol>.exe の絶対パス
    bin_sha256: str         # バイナリ内容の full sha256 (exact 64 lowercase hex, 単一ソース)
    build_dir: str
    cached: bool            # キャッシュヒットで再ビルドを省いたか
    configure_cmd: str = ""  # このバイナリを作る cmake configure (実験再現用)
    build_cmd: str = ""      # cmake --build (実験再現用)

    @property
    def bin_hash(self) -> str:
        """provenance / WAL 用の 16 文字表示 (= `bin_sha256[:16]`)。

        `bin_sha256` の read-only 派生であり、独立フィールドとして格納しない (A-3/D-7:
        「二つの真実」排除)。sha256-prefix-16 / legacy-display-only 系列 — 照合には使わない。"""
        return self.bin_sha256[:16]


def build(genome: Genome, ccbench_commit: str, trace: bool,
          cache_root: str = "", cc: str = DEFAULT_CC, cxx: str = DEFAULT_CXX,
          jobs: int = 16, ccbench_dir: str = "",
          src_token: Optional[str] = None) -> BuildResult:
    """genome を (trace 有無で) ビルドし BuildResult を返す。キャッシュヒットなら skip。

    src_token=None なら working-tree から計算する (D23: identity と materialization を
    結合し TOCTOU 偽 hit を防ぐ — working-tree が変われば cache_key が変わる)。呼び手
    (pipeline.evaluate) は trace/perf で同一値を共有するため事前計算して渡してよい。"""
    sub = ccbench_dir or _ccbench_dir()
    _verify_ccbench_commit(sub, ccbench_commit)        # 偽キャッシュヒット防止 (honest)
    source_digest.assert_worktree_within_allowlist(sub)  # coder の編集面が EVOLVE-BLOCK 内か (D23)
    if src_token is None:
        src_token = source_digest.src_token(genome, ccbench_commit, sub, cxx)
    root = cache_root or os.path.join(sub, "build-variants")
    key = cache_key(genome, ccbench_commit, trace, src_token, cc=cc, cxx=cxx)
    bdir = os.path.join(root, key)
    target = f"ycsb_{genome.protocol}.exe"
    binary = os.path.join(bdir, "cc", genome.protocol, target)

    # ビルドコマンドを先に組み立てる (cache hit でも実験再現用に BuildResult へ記録する)。
    defines = genome.cmake_defines() + [f"-DCCBENCH_TRACE={int(trace)}"]
    cfg = ["cmake", "-S", sub, "-B", bdir, "-DCMAKE_BUILD_TYPE=Release",
           "-DENABLE_SANITIZER=OFF", f"-DCMAKE_C_COMPILER={cc}",
           f"-DCMAKE_CXX_COMPILER={cxx}"] + defines
    build_cmd = ["cmake", "--build", bdir, "--target", target, "-j", str(jobs)]
    cfg_str, build_str = " ".join(cfg), " ".join(build_cmd)

    if os.path.exists(binary):
        # cache hit でも identity を再照合する: resolve→hit 判定の間に working-tree が
        # 動いていると「今の tree と食い違うバイナリ」を今の key で返してしまう。
        _recheck_src_token(genome, ccbench_commit, sub, cxx, src_token,
                           bdir, built_fresh=False)
        _assert_trace_diff(genome, ccbench_commit, sub, cxx, bdir, built_fresh=False)
        if not trace:
            _assert_no_trace_symbols(binary)     # 規律1: 既存 perf binary も継続検査
        return BuildResult(genome=genome, trace=trace, binary=binary,
                           bin_sha256=full_sha256(binary), build_dir=bdir, cached=True,
                           configure_cmd=cfg_str, build_cmd=build_str)

    _clear_stale_build_dir(bdir, binary)
    _run(cfg, "configure")
    _run(build_cmd, "build")
    if not os.path.exists(binary):
        raise RuntimeError(f"build succeeded but binary missing: {binary}")
    # TOCTOU 遮断 (phase3.md blocking / D30): resolve→build 間に working-tree が動くと
    # digest と実バイナリが食い違ったまま**共有ビルドキャッシュ (campaign 非依存) に永続**し、
    # 以後 cache hit で沈黙再利用される (偽 cache hit = 規律2 直撃)。build 完了直後に
    # src_token を再計算して照合し、不一致は build dir ごと破棄して fails-closed。
    _recheck_src_token(genome, ccbench_commit, sub, cxx, src_token,
                       bdir, built_fresh=True)
    _assert_trace_diff(genome, ccbench_commit, sub, cxx, bdir, built_fresh=True)
    if not trace:
        _assert_no_trace_symbols(binary)         # 規律1: 新規 perf binary に trace 漏れが無いか
    return BuildResult(genome=genome, trace=trace, binary=binary,
                       bin_sha256=full_sha256(binary), build_dir=bdir, cached=False,
                       configure_cmd=cfg_str, build_cmd=build_str)


def _recheck_src_token(genome: Genome, ccbench_commit: str, sub: str, cxx: str,
                       expected: str, bdir: str, built_fresh: bool) -> None:
    """build 出口の identity 再照合 (TOCTOU 遮断)。resolve 時の src_token と、いま現在の
    working-tree から再計算した src_token が一致することを assert する (fails-closed)。

    再計算は resolve と同じ単一窓口 (source_digest.resolve = allowlist 検査 + src_token) —
    tree が動いて allowlist 外改変が入ったケースも同時に捕える。数十 ms で規律4 に反しない
    (phase3.md タスク定義)。新規ビルドの不一致は汚染バイナリの永続を防ぐため build dir を
    破棄する。cache hit の不一致は既存 (過去の正当な) 成果物なので破棄せず停止のみ。"""
    try:
        actual = source_digest.resolve(genome, ccbench_commit, sub, cxx)
    except RuntimeError:
        # resolve 自体の失敗 (TOCTOU 汚染 / git・g++ の transient 障害を区別できない)。
        # identity 不明のバイナリは共有キャッシュに残さない (偽 hit 防止 > 再ビルドコスト) —
        # cache_key で次 run が再ビルドするので D25 の再評価可能性は保たれる (transient でも
        # 消すのは意図的な非対称)。破棄の成否まで確認する (下の _discard)。
        if built_fresh:
            _discard_build_dir(bdir)
        raise
    if actual != expected:
        if built_fresh:
            _discard_build_dir(bdir)
        raise RuntimeError(
            f"TOCTOU 検知: build {'後' if built_fresh else '(cache hit)'} の src_token "
            f"再計算 ({actual[:16]}) が resolve 時 ({expected[:16]}) と不一致 — "
            "resolve→build 間に working-tree が動いた。汚染バイナリを共有キャッシュに"
            f"永続させないため{'破棄して' if built_fresh else ''}停止する "
            "(fails-closed, phase3.md blocking / D30)")


def _assert_trace_diff(genome: Genome, ccbench_commit: str, sub: str, cxx: str,
                       bdir: str, built_fresh: bool) -> None:
    """build 出口の観測者効果二重検査 (diff-of-diffs、規律1 の一次防壁)。

    発火単位 = 毎 variant の trace/perf ビルド直後 (phase3.md タスク定義)。nm の
    name-based 検査 (_assert_no_trace_symbols) は data-structure 観測者効果と
    #ifdef TRACE 内側への挙動差隠蔽を見逃す — その補完で、述語の実体は
    source_digest.assert_trace_diff_matches_head。不一致・preprocess 失敗の variant
    バイナリは規律1 違反 (検証コードが perf ビルドに混入しうる) の疑いを晴らせないので、
    新規ビルドは build dir ごと破棄して共有キャッシュに残さない (_recheck_src_token と
    同じ非対称: cache hit 側は既存の正当な成果物なので破棄せず停止のみ)。"""
    try:
        source_digest.assert_trace_diff_matches_head(genome, ccbench_commit, sub, cxx)
    except RuntimeError:
        if built_fresh:
            _discard_build_dir(bdir)
        raise


def _clear_stale_build_dir(bdir: str, binary: str) -> None:
    """kill 等で中断された中途 build dir (binary 不在で dir だけ残る) を configure 前に破棄する。

    build 途中の kill では Python の例外経路 (_discard_build_dir) が走らず、
    「CMakeCache.txt あり・binary 無し」の残骸が共有キャッシュに永続する。残骸の
    CMakeCache には当時の一時 worktree パス (実行ごとランダム) が焼き付いているため、
    以後の同一 variant の configure が cmake のソースディレクトリ不一致で**毎回即死**する
    (2026-07-11 s8a sweep の stock 点が二重起動事故の kill 以降 build-error を再発し続けた
    実障害)。正当な完成品 (binary あり) は呼び手の cache hit 経路が先に扱う — ここに来る
    既存 dir は不完全と確定しているので、破棄してから新規 configure する (fails-closed 側の
    回復。破棄の成否検査は _discard_build_dir と共通)。"""
    if os.path.isdir(bdir) and not os.path.exists(binary):
        _discard_build_dir(bdir)


def _discard_build_dir(bdir: str) -> None:
    """汚染 build dir を破棄し、消し残しを検査する (fails-closed)。

    rmtree(ignore_errors=True) の沈黙 (権限・使用中で消せない) を放置すると、残った汚染
    バイナリが**次 run の cache hit で再照合されず再利用**される (再照合は『今の tree の
    resolve == expected』のみで残存バイナリの由来を見ない, 2026-07-03 敵対検証 low)。破棄
    失敗を明示例外にし、汚染の永続を沈黙させない。"""
    shutil.rmtree(bdir, ignore_errors=True)
    if os.path.exists(bdir):
        raise RuntimeError(
            f"汚染 build dir を破棄できなかった ({bdir}) — 権限/使用中を疑え。残存すると "
            "次 run の cache hit で汚染バイナリが再利用される。手動で削除してから再実行すること "
            "(fails-closed)")


def _has_trace_symbols(nm_output: str) -> bool:
    """nm 出力に izanagi_trace シンボルが含まれるか (perf build への trace 漏れ判定)。"""
    return any("izanagi_trace" in ln.lower() for ln in nm_output.splitlines())


def _assert_no_trace_symbols(binary: str) -> None:
    """perf (trace-disabled) build に trace シンボルが 1 つも無いことを assert (絶対規律1 の継続執行)。

    観測者効果分離は `#if TRACE` のソース層が一次防壁だが、誰かが `#ifdef TRACE` に書き戻す/
    CMake が常に `-DTRACE` を出す等で**サイレントに perf build へ漏れる**回帰を、ビルドごとに
    機械検出する (worklog の一度きり手動 nm を継続執行に格上げ)。nm が起動できない/失敗する
    環境では fails-closed で停止する — 「一次防壁の回帰」と「nm の欠如」が複合した瞬間だけ
    検査が沈黙するのは規律1/3 に反する (旧実装は silent pass だった、洗練検査 LOW)。
    限界: strip 済みバイナリはシンボル 0 で素通りする (ビルド直後の非 strip 前提)。"""
    try:
        r = subprocess.run(["nm", "-C", binary], capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"規律1 検査不能: nm を起動できない ({e})。trace シンボル漏れを検査できない"
            f"環境で perf build を採用しない (fails-closed)") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"規律1 検査不能: nm が失敗 (rc={r.returncode}): {r.stderr[-200:]} "
            f"(fails-closed で停止)")
    if _has_trace_symbols(r.stdout):
        raise RuntimeError(
            f"絶対規律1 違反: perf (trace-disabled) build に izanagi_trace シンボルが漏れている: "
            f"{binary}。#if TRACE でなく #ifdef TRACE に書き戻された / CMake が -DTRACE を常に "
            "出す等を疑え (decisions D14)。")


def _run(cmd: List[str], what: str) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{what} failed (rc={r.returncode}): "
                           f"{r.stderr[-800:]}")


def _verify_ccbench_commit(sub: str, declared: str) -> None:
    """宣言 ccbench_commit が submodule の実 HEAD と一致するか照合する。

    cache_key は宣言文字列だけで決まる (bin_hash は provenance 専用で照合に未使用)。
    宣言が実 HEAD とずれていると、別版でビルドしたバイナリを偽キャッシュヒットさせる。
    一致しなければ即停止 (ident.IdentityMismatch と同じ関所思想)。git が無い/submodule
    未 init なら照合不能なので best-effort で skip — ただし同経路では source_digest
    (source_digest.py) が git/g++ 不在時に fails-closed で先に停止するため、この skip
    単独で偽キャッシュヒットが通ることはない (実ビルドも cmake 側で失敗する)。"""
    if not declared:
        return
    try:
        r = subprocess.run(["git", "-C", sub, "rev-parse", "HEAD"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return
    head = r.stdout.strip()
    if r.returncode != 0 or not head:
        return
    if not head.startswith(declared):
        raise RuntimeError(
            f"ccbench_commit 不一致: 宣言={declared} だが submodule HEAD={head[:12]}。"
            "誤った版でのビルド/偽キャッシュヒットを防ぐため停止する "
            "(honest-by-construction)。")
