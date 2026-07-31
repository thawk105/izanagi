#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""段 8a D 段偵察の必須前提 (a): 要因別 abort 頻度の事前実測 (D48 前提 1、D49 申し送り c)。

silo-backoff-trigger-gating 軸の偵察 (機械 sweep) の列挙空間を設計するため、p2_2 確定
動作点 (t48 / 1M records / skew0.9) の 3 workload (rr95/rr50/rr5) で abort 要因の分布を
実測し、**不感ビット (実測カウント 0 の要因)** を確定する。C 段 coverage
(`s8a_trigger_coverage.py`、t4/tuple200 の検証動作点) の要因分布は偵察設計に流用できない
(D49 申し送り c) — 本 driver がその宿題を消化する。

**これは characterization であって性能計測ではない (規律 1/4):**
  - patch 構成は C 段 coverage と同一 — 骨格 (TEMPLATE_PATCH、hole 初期値 true = 恒等
    gate = stock 挙動) + 計装 (INSTR_PATCH、per-abort A 行) を TRACE=1 ビルドに重ねる。
  - trace I/O は実行を遅くし絶対頻度・abort 率を歪めるが、**不感ビット判定 (要因の
    構造ゼロ) は構造的性質で trace I/O に不変** (発生不能な要因は I/O があっても発生
    しない)。相対分布は参考値。
  - **性能数値 (tps 等) は一切出力しない。** stdout から読むのは abort_counts_ (保存則
    検査の分母) のみ。
  - genome は E 段 driver と同じ `_BASE` (BACK_OFF=1) + ADD_ANALYSIS=1 — E 段ループが
    走る側の動作点で分布を取る。
  - extime=1 / reps=1: 頻度の「≈0 か否か」に計測グレードの反復は不要。abort イベントは
    1 run で 10^5 規模になり、非構造要因が偶然 0 になる確率は無視できる。

**不感ビット判定規則 (事前凍結、設計ドラフト §1(a) + レビュー STAT-1/MS-3 裁定):**
実測カウント 0 の要因のみ列挙から除外する (閾値判定はしない — 微小でも非ゼロなら実効
ビット、fails-closed)。3 workload の**いずれか**で非ゼロなら実効 (workload ごとに列挙
空間を変えない)。予想 (update-absent ≈0 は YCSB delete なしの構造論拠、node-vali ≈0 は
t4 coverage 由来の**経験的**予想 — 「構造的発生不能」と言えるのは前者のみ) が外れて
非ゼロならそのまま実効ビットに入れる。reps=1 で「たまたま 0」を守るのは構造論ではなく
**traced run の実測 abort 総数 N が検出下限 (~1/N) を要因発火率で上回ること** — JSON に
N (abort_counts) を記録し、偵察 insight は不感判定の分母として N を報告する。

**保存則 (fails-closed):** 各 run で A 行総数 == stdout `abort_counts_` を検査。破れたら
数え漏れのある分布で不感判定することになるため即失敗させる。awk による手組み tally が
verifier の A 行集計経路 (C 段 coverage) と別実装であることの数え漏れリスクは、この
保存則が機械的に検査する (総数が合わない限り通らない。未知タグも raise、レビュー MS-4)。

実行 (計測機で直列、実行前に single-tenant を確認):
  python3 campaign/s8a_trigger_freq.py            # 3 workload
  python3 campaign/s8a_trigger_freq.py balanced   # 1 workload だけ
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign.axis_trigger_gating import (                             # noqa: E402
    GATEABLE_REASONS, INSTR_PATCH, PIN, REASON_NAMES, TEMPLATE_PATCH, _BASE)
from campaign.layout import repo_output_root                           # noqa: E402
from campaign.model import Genome                                      # noqa: E402
from campaign.p2_2 import (CLK, RECORDS, THREADS, WORKLOADS,           # noqa: E402
                           _assert_single_tenant)
from campaign.patchharness import applied, apply_patch, assert_pinned_clean  # noqa: E402
from campaign.s8a_trigger_coverage import (                            # noqa: E402
    _build, _parse_abort_counts, _require_direct_build_site,
)

ENV_TAG = "linux-baremetal"
RUN_TIMEOUT_S = 600.0     # 1M records のロード + extime 1s + trace I/O 減速の余裕

# E 段が走る側 (BACK_OFF=1) の動作点。ADD_ANALYSIS は abort_counts_ の出力用
# (result.cc は ADD_ANALYSIS 無しでも abort_counts_ を出すが、coverage と構成を揃える)。
GENOME = Genome("silo", dict(_BASE, ADD_ANALYSIS=1))

EXTIME = 1                # 頻度分布に p2_2 の extime=3 は不要 (trace 量の最小化)


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_freq(binary: str, workload: dict) -> tuple:
    """trace-enabled binary を p2_2 動作点で 1 run し (A 行 tally, abort_counts_) を返す。

    trace は TMPDIR 配下 (数百 MB〜GB 級 — C/R/W 行が支配的) に書き、tally 後すぐ消す。
    A 行の集計は awk (GB 級ファイルの Python 行読みを避ける)。"""
    tdir = tempfile.mkdtemp(prefix="izanagi_s8a_freq_")
    os.makedirs(os.path.join(tdir, "log"), exist_ok=True)
    flags = {"ycsb_tuple_num": str(RECORDS), "thread_num": str(THREADS),
             "extime": str(EXTIME), **workload}
    args = [binary] + [f"-{k}={v}" for k, v in flags.items()] \
        + [f"-clocks_per_us={CLK}"]
    env = dict(os.environ, IZANAGI_TRACE_DIR=tdir)
    try:
        proc = subprocess.run(args, env=env, capture_output=True, text=True,
                              timeout=RUN_TIMEOUT_S, cwd=tdir)
        if proc.returncode != 0:
            raise RuntimeError(f"run rc={proc.returncode}: "
                               f"{proc.stderr.strip()[-300:]}")
        traces = sorted(os.path.join(tdir, f)
                        for f in os.listdir(tdir) if f.startswith("trace_"))
        if not traces:
            raise RuntimeError("trace ファイルが 1 つも無い — TRACE=1 ビルドでない"
                               "か trace 出力先の取り違え (fails-closed。空 glob の"
                               " awk は stdin 待ちでハングする — レビュー F3)")
        tally_out = subprocess.run(
            ["awk", '/^A /{c[$2]++} END{for(k in c) print k, c[k]}'] + traces,
            capture_output=True, text=True, check=True,
            stdin=subprocess.DEVNULL).stdout
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
    tally = {name: 0 for name in REASON_NAMES}
    for line in tally_out.splitlines():
        name, cnt = line.rsplit(None, 1)
        if name not in tally:
            raise RuntimeError(f"未知の A 行要因タグ: {name!r} (計装と REASON_NAMES の"
                               "不整合 — fails-closed)")
        tally[name] = int(cnt)
    return tally, _parse_abort_counts(proc.stdout)


def main(argv, *, site_observer=None) -> int:
    site_observation = _require_direct_build_site(site_observer)
    sel = argv[1] if len(argv) > 1 else None
    wls = [w for w in WORKLOADS if sel is None or w[0] == sel]
    if not wls:
        print(f"unknown workload: {sel} (選択肢: {[w[0] for w in WORKLOADS]})")
        return 2

    _assert_single_tenant()
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    assert_pinned_clean(sub, PIN)
    patches = os.path.join(root, "patches")

    result = {"purpose": ("段 8a D 偵察の必須前提 (a): 要因別 abort 頻度の事前実測。"
                          "characterization であり性能計測ではない — 性能数値なし。"
                          "trace I/O 下の分布につき相対分布は参考値、不感判定 (=0) のみ"
                          "設計入力 (構造的性質で trace I/O に不変)。"),
              "env_tag": ENV_TAG, "ccbench_commit": PIN,
              "genome": GENOME.canonical(), "clocks_per_us": CLK,
              "records": RECORDS, "threads": THREADS, "extime": EXTIME,
              "reason_names": list(REASON_NAMES),
              "gateable_reasons": list(GATEABLE_REASONS),
              "workloads": {}}

    bdir = tempfile.mkdtemp(prefix="izanagi_s8a_freq_build_")
    try:
        with applied(os.path.join(patches, TEMPLATE_PATCH), PIN, sub):
            apply_patch(os.path.join(patches, INSTR_PATCH), sub)
            print("== build skeleton+instr (TRACE=1) ==")
            binary = _build(
                bdir, genome=GENOME, site_observation=site_observation,
            )  # 自前 GENOME を明示 (レビュー F1)
            for tag, workload in wls:
                print(f"== freq run  workload={tag}  ({workload}) ==")
                tally, aborts = _run_freq(binary, workload)
                conservation_ok = sum(tally.values()) == aborts
                result["workloads"][tag] = {
                    "ycsb": workload, "reason_tally": tally,
                    "abort_counts": aborts,
                    "conservation_ok": conservation_ok,
                }
                print(f"  aborts={aborts} tally={tally} "
                      f"conservation={'OK' if conservation_ok else 'BROKEN'}")
                if not conservation_ok:
                    raise RuntimeError(
                        f"保存則が破れた (workload={tag}): A 行総数 "
                        f"{sum(tally.values())} != abort_counts_ {aborts}。"
                        "数え漏れのある分布で不感判定はできない (fails-closed)")
    finally:
        shutil.rmtree(bdir, ignore_errors=True)
    assert_pinned_clean(sub, PIN)

    # 不感ビット判定 (事前凍結規則): gate 可能 5 要因のうち、全 workload で実測 0 の
    # もののみ不感。1 workload でも非ゼロなら実効。
    if len(result["workloads"]) == len(WORKLOADS):
        effective = [r for r in GATEABLE_REASONS
                     if any(w["reason_tally"][r] > 0
                            for w in result["workloads"].values())]
        insensitive = [r for r in GATEABLE_REASONS if r not in effective]
        result["effective_reasons"] = effective
        result["insensitive_reasons"] = insensitive
        print(f"\n実効ビット ({len(effective)}): {effective}")
        print(f"不感ビット ({len(insensitive)}): {insensitive}"
              f"  → 偵察の列挙空間 = 2^{len(effective)}")
    else:
        print("\n(部分実行のため不感ビット判定はスキップ — 全 workload で回すこと)")

    outdir = os.path.join(repo_output_root(), "env", ENV_TAG, "calibration")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"s8a_trigger_freq_t{THREADS}.json")
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(f"-> {outpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
