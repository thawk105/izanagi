# -*- coding: utf-8 -*-
"""P3 後続段 2 driver — S4 consumer の赤 2 本 (実走) + WAL 機械判定。

**赤 1 (coder 発 liveness-red、完全 E2E):** coder が合成枝に書いた過大 backoff
(1e9 µs = 1000 秒 ≫ trace timeout 120 秒) の patch を適用して評価する。backoff の
spin は quit フラグを見ない (backoff.hh の for(;;) — worker loop の quit 検査は
workload 外側のみ) ため worker join が返らず trace-timeout abort が決定的に発火する。
値 1e9 の含意: timeout の 8 倍で決定的、かつ driver 異常死で子プロセスが孤児化しても
約 17 分で spin を抜けて自然終了する (無限に CPU を焼かない)。値は orchestrator が
与えた (coder は発明しない — kickoff と同じリーク制御。「赤を出すための値」であり
性能勝ち筋のリークではない)。

**赤 2 (fixture 発 verify-red、半実):** verify-red を実 run で出す変異は validation
経路 (broken-silo patch) だが、それは buildcache の allowlist (EVOLVE_BLOCK_SOURCES
限定) に**正しく拒否され** pipeline を通れない — 規律2 の防壁が機能している構造的
事実で、正規経路での verify-red 初発火は編集面が validation に開く段 3 以降になる。
防壁を緩めずに焼き込み経路 (pipeline → abort payload → WAL → load_rejections) を
実証するため、既存の G2 赤 fixture trace (tests/fixtures/r1_write_skew) を
_run_trace 差し替えで注入する — verifier / result_to_dict / WAL 焼き込み /
load_rejections / render はすべて実物で、モック点は trace 供給の 1 点のみ。
この variant の WAL 上の genome は stock だが trace は fixture 由来 (帰属は偽) —
本 campaign は fixture 用 (search_tag=s4-red-consumer) で正系列とは WAL/digest が
物理分離される (fixture red を正系列 WAL に書かない規約の実体)。

判定は WAL 機械確認 (宣言でなくレコードを gate にする — kickoff/D30 の様式踏襲)。
digest (rejections 節込み) を campaign dir に書き出し、critic (fresh) の読みに渡す。

  python3 orchestrator/campaign/p3_s4_red.py --allow-coder-derived-build
      # 赤1 → 赤2 → 判定 → digest 書き出し
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import env_contract, ident, pipeline, wal            # noqa: E402
from .artifact_admission import require_admitted_campaign # noqa: E402
from .build_admission import (BuildAdmissionError, GeneratorId,  # noqa: E402
                                      add_coder_build_authority_argument,
                                      build_run_context)
from .layout import exploration_campaign_layout            # noqa: E402
from .loop import run_campaign                             # noqa: E402
from .model import CampaignConfig, Genome                  # noqa: E402
from .p2_2 import _assert_single_tenant                    # noqa: E402
from .patchharness import applied, assert_pinned_clean     # noqa: E402
from .pipeline import PerfConfig                           # noqa: E402
from .p3_s4_loop import make_critic_identity_projection    # noqa: E402
from ..critic.digest import (Rejection, load_liveness_rejections,    # noqa: E402
                           load_rejections, load_verify_abort_signals,
                           render_rejections)


PIN = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
STOCK_G = Genome("silo", {**_BASE, "BACK_OFF": 1})

# 合成枝 literal (1000000000.0) と genome 値を揃える (static50 前例の整合規約:
# genome 値は枝選択 + identity、コードの中身は patch。両者が食い違うと還流信号が
# 自己矛盾する)。
RED_BACKOFF_US = 1_000_000_000
RED_G = Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": RED_BACKOFF_US})

RED_PATCH = "patches/variant-backoff-red-1e9.patch"
FIXTURE_TRACE_DIR = "orchestrator/tests/fixtures/r1_write_skew"


def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def _cfg() -> CampaignConfig:
    return CampaignConfig(
        spec_slug="p3-s4-red", search_tag="s4-red-consumer",
        spec_content=("P3 後続段 2: S4 consumer の赤 2 本 — coder 発 liveness-red "
                      "(過大 backoff 1e9µs → trace-timeout、完全 E2E) + fixture 発 "
                      "verify-red (r1_write_skew trace 注入の半実 — stock genome への"
                      "帰属は偽で fixture 用 campaign に隔離)。正系列に混ぜない"),
        ccbench_commit=PIN,
        search_config={"scale": "silo", "variants": "red-timeout+fixture-norw-trace",
                       "records": 100_000, "threads": 4},
        trial="p3-s4-red")


def _perf() -> PerfConfig:
    # 赤は verify 段で死ぬため bench には到達しない (wiring 規模の指定のみ)。
    return PerfConfig(records=100_000, threads=4,
                      workload={"ycsb_rratio": "50", "ycsb_zipf_skew": "0.9",
                                "ycsb_rmw": "false"}, extime=1, reps=2)


def _fixture_run_trace(binary, trace_dir, flags, clocks_per_us, timeout_s=None,
                       numactl=None):
    """_run_trace の fixture 差し替え (赤 2 専用)。バイナリは実行せず r1_write_skew
    (G2 赤、C 行 2) を trace_dir へコピーする。rc=0・aborts=1・C 行数と一致する
    commit witness・batch=0 を返し、手前 reject を踏まずに実 verifier へ渡す。"""
    src = os.path.join(_repo_root(), FIXTURE_TRACE_DIR)
    n = 0
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".log"):
            continue
        dst = os.path.join(trace_dir, fn)
        shutil.copy(os.path.join(src, fn), dst)
        with open(dst) as f:
            n += sum(1 for line in f if line.startswith("C "))
    return pipeline._TraceRunResult(
        trace_c_lines=n,
        returncode=0,
        abort_counts=1,
        commit_count_witness=n,
        batch_commit_count_witness=0,
    )


def _synthetic_integrity_rejection() -> Rejection:
    """integrity 型 (indeterminate) の合成 fixture (J8-B と同形)。実 run 由来ではない
    ことは閉じた origin_kind で heading に明示する。"""
    return Rejection(
        genome="silo|BACK_OFF=1,BACKOFF_FIXED=999,NO_WAIT_LOCKING_IN_VALIDATION=1,"
               "NO_WAIT_OF_TICTOC=0,WAL=0",
        flags={"BACK_OFF": 1}, verdict="indeterminate", anomalies=[],
        integrity={"clean": False, "orphan_reads": 0, "version_dups": 0,
                   "dup_txids": 0, "genesis_commits": 0, "missing_txids": 3,
                   "write_version_mismatch": 0, "malformed_keys": 0,
                   "notes": ["missing txids sample: [7, 8, 9]"]},
        stats={"txns": 97, "reads": 280, "writes": 95, "keys": 50, "edges": 110},
        total_cycles=0, variant="", src_token="", workload={},
        origin_kind="synthetic-fixture")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="P3 coder-derived red-path fixture")
    add_coder_build_authority_argument(parser)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.coder_build_authority is None:
        raise BuildAdmissionError("--allow-coder-derived-build の明示 opt-in が必要")
    build_context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=args.coder_build_authority,
    )
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    _assert_single_tenant()
    assert_pinned_clean(sub, PIN)
    cfg, perf = ident.bind_admission_policy(_cfg(), build_context.policy), _perf()
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))

    print("=== 赤 1: coder 発 liveness-red (過大 backoff → trace-timeout、完全 E2E) ===")
    print(f"  期待: build → trace run が {pipeline.TRACE_TIMEOUT_S:.0f}s timeout → abort")
    with applied(os.path.join(root, RED_PATCH), PIN, sub):
        s1 = run_campaign(cfg, [RED_G], perf, ENV_TAG, CLK, numactl=NUMA,
                          authorization_contract=env_contract.authorize(ENV_TAG),
                          build_context=build_context,
                          campaign_namespace="exploration")
    v1 = next((r.variant for r in s1.results), None)

    print("\n=== 赤 2: fixture 発 verify-red (r1_write_skew trace 注入の半実) ===")
    saved = pipeline._run_trace
    pipeline._run_trace = _fixture_run_trace
    try:
        s2 = run_campaign(cfg, [STOCK_G], perf, ENV_TAG, CLK, numactl=NUMA,
                          authorization_contract=env_contract.authorize(ENV_TAG),
                          build_context=build_context,
                          campaign_namespace="exploration")
    finally:
        pipeline._run_trace = saved
    v2 = next((r.variant for r in s2.results), None)

    # --- WAL 機械判定 (完了判定 (b): レコードと復元を gate にする) ---
    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    r1 = wal.records_by_stage(layout, v1) if v1 else {}
    r2 = wal.records_by_stage(layout, v2) if v2 else {}
    critic_view = require_admitted_campaign(layout.root)
    livs, other = load_liveness_rejections(critic_view)
    rejs = load_rejections(critic_view)

    checks = {
        "赤1. trace-timeout abort (coder 発 liveness-red)":
            r1.get("abort", {}).get("reason") == "trace-timeout",
        "赤1. timeout_s が payload に記録":
            r1.get("abort", {}).get("timeout_s") == pipeline.TRACE_TIMEOUT_S,
        "赤1. 非 stock src_token (coder のコード差が identity に映る)":
            r1.get("build_start", {}).get("src_token") not in (None, "", "stock"),
        "赤1. load_liveness_rejections が復元 (variant/src_token 込み)":
            any(l.reason == "trace-timeout" and l.variant == v1 and l.src_token
                for l in livs),
        "赤2. abort payload に verify 構造 (焼き込み経路の初発火)":
            r2.get("abort", {}).get("verify") is not None,
        "赤2. verdict=non-serializable & total_cycles>=1":
            r2.get("abort", {}).get("verify", {}).get("verdict") == "non-serializable"
            and (r2.get("abort", {}).get("verify", {}).get("total_cycles") or 0) >= 1,
        "赤2. load_rejections が復元 (edges/reasons まで)":
            any(rj.verdict == "non-serializable" and rj.anomalies
                and rj.anomalies[0].get("edges") for rj in rejs),
    }
    print("\n=== 判定 (WAL 機械確認) ===")
    ok = all(checks.values())
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")

    # --- digest 書き出し (critic の読みに渡す。integrity 型は合成 fixture を併記) ---
    digest_txt = render_rejections(
        rejs + [_synthetic_integrity_rejection()], livs, other,
        load_verify_abort_signals(critic_view),
        identity_projection=make_critic_identity_projection(critic_view),
    )
    out_path = os.path.join(layout.root, "s4_rejections_digest.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(digest_txt)
    print(f"\ndigest (rejections 節) 書き出し: {out_path}")
    print(f"campaign dir: {layout.root}")
    print(f"\n後続段 2 実走判定: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
