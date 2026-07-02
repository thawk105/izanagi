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
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from . import source_digest
from .model import Genome


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


@dataclass
class BuildResult:
    genome: Genome
    trace: bool
    binary: str             # ycsb_<protocol>.exe の絶対パス
    bin_hash: str           # バイナリ内容の sha256[:16] (provenance / WAL)
    build_dir: str
    cached: bool            # キャッシュヒットで再ビルドを省いたか
    configure_cmd: str = ""  # このバイナリを作る cmake configure (実験再現用)
    build_cmd: str = ""      # cmake --build (実験再現用)


def _bin_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


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
        if not trace:
            _assert_no_trace_symbols(binary)     # 規律1: 既存 perf binary も継続検査
        return BuildResult(genome, trace, binary, _bin_hash(binary), bdir, cached=True,
                           configure_cmd=cfg_str, build_cmd=build_str)

    _run(cfg, "configure")
    _run(build_cmd, "build")
    if not os.path.exists(binary):
        raise RuntimeError(f"build succeeded but binary missing: {binary}")
    if not trace:
        _assert_no_trace_symbols(binary)         # 規律1: 新規 perf binary に trace 漏れが無いか
    return BuildResult(genome, trace, binary, _bin_hash(binary), bdir, cached=False,
                       configure_cmd=cfg_str, build_cmd=build_str)


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
