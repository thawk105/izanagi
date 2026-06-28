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

from .model import Genome


def _ccbench_dir() -> str:
    # buildcache.py = <repo>/orchestrator/campaign/buildcache.py → repo は dirname×2
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    repo = os.path.dirname(os.path.dirname(here))         # <repo>
    return os.path.join(repo, "external", "ccbench")


def cache_key(genome: Genome, ccbench_commit: str, trace: bool) -> str:
    raw = f"{genome.canonical()}|{ccbench_commit}|trace={int(trace)}"
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
          cache_root: str = "", cc: str = "gcc-13", cxx: str = "g++-13",
          jobs: int = 16, ccbench_dir: str = "") -> BuildResult:
    """genome を (trace 有無で) ビルドし BuildResult を返す。キャッシュヒットなら skip。"""
    sub = ccbench_dir or _ccbench_dir()
    _verify_ccbench_commit(sub, ccbench_commit)        # 偽キャッシュヒット防止 (honest)
    root = cache_root or os.path.join(sub, "build-variants")
    key = cache_key(genome, ccbench_commit, trace)
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
    機械検出する (worklog の一度きり手動 nm を継続執行に格上げ)。nm が無い環境は best-effort skip。"""
    try:
        r = subprocess.run(["nm", "-C", binary], capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return
    if r.returncode != 0:
        return
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
    未 init なら照合不能なので best-effort で skip (実ビルドは cmake 側で失敗する)。"""
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
