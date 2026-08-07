# -*- coding: utf-8 -*-
"""P3 kickoff driver — coder 全配線 1 周の機械判定 (phase3.md 完了条件 2 項)。

完了条件 1 (dirty no-op admission): coder の no-op variant (#if 枝 = #else 枝の逐語複写)
も tracked tree は dirty なので stock/cache-hit とみなさず、CLI token を要求して coder
namespace の **cache-miss** で certified commit する。
完了条件 2 (合成枝の 1 周): 純 timing variant (静的 backoff 値 1 つ。値は人間が与える
= kickoff のリーク制御、coder は値を発明しない) が stock と**別の** variant_id /
cache_key に解決され **cache-miss で新規ビルド**され、verify (abort>0 = 合成枝が
verify 中に実行された証拠) → bench → WAL certified commit まで 1 周する。
どちらも WAL で機械確認する (宣言でなくレコードを gate にする、D30 の教訓)。

旧 seed stock cache は使わない。dirty no-op は source bytes が stock と同値でも tracked
evidence が dirty のため coder receipt を要求し、新しい admission namespaceへ入る。

variant patch は coder (サブエージェント) の編集から orchestrator が patch 化したもの
(patches/variant-*.patch)。駆動順序 = applied() (apply → resolve → build → revert) に
run_campaign を包む。fitness は配線テストであり baseline ではない (wiring 規模、規律4)。

  python3 orchestrator/campaign/p3_kickoff.py --allow-coder-derived-build
      # 条件1 → 条件2 → 判定
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import env_contract, ident, wal                     # noqa: E402
from campaign.build_admission import (BuildAdmissionError, GeneratorId,  # noqa: E402
                                      add_coder_build_authority_argument,
                                      build_run_context)
from campaign.layout import exploration_campaign_layout           # noqa: E402
from campaign.loop import run_campaign                            # noqa: E402
from campaign.model import CampaignConfig, Genome                 # noqa: E402
from campaign.p2_2 import _assert_single_tenant                   # noqa: E402
from campaign.patchharness import applied, assert_pinned_clean    # noqa: E402
from campaign.pipeline import PerfConfig, variant_id              # noqa: E402

PIN = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
STOCK_G = Genome("silo", {**_BASE, "BACK_OFF": 1})
# BACKOFF_FIXED=50 は #if 枝 (合成枝) を選ぶ genome 値。coder が書いた合成枝の実体は
# patch 側の literal (patches/variant-backoff-static50.patch) — genome 値は枝選択、
# コードの中身は patch、と役割が分かれる (identity は両方を覆う: flags は canonical、
# コードは src_token)。50us は sweep 済み**非勝者**点 (over-throttle 帯。sweet-spot
# 5〜10us 帯の外) — 配線実証用に人間が与えた値で、勝ち筋の先取りではない (敵対検証
# 2026-07-05 の指摘採用: 当初案 10us は write-heavy 勝者値でリーク台帳が偽になる)。
STATIC_G = Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 50})

NOOP_PATCH = "patches/variant-noop-else-copy.patch"
STATIC_PATCH = "patches/variant-backoff-static50.patch"


def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    return os.path.dirname(os.path.dirname(here))


def _cfg() -> CampaignConfig:
    return CampaignConfig(
        spec_slug="p3-kickoff", search_tag="coder-wiring",
        spec_content=("P3 kickoff: coder 全配線 1 周 — no-op (identity 後方互換) + "
                      "純 timing static50 (合成枝 cache-miss 1 周)。phase3.md 完了条件 2 項"),
        ccbench_commit=PIN,
        search_config={"scale": "silo", "variants": "noop+static50",
                       "records": 100_000, "threads": 4},
        trial="p3-kickoff")


def _perf() -> PerfConfig:
    # wiring 規模 (demo.py 相当)。fitness は配線テストで baseline ではない (規律4:
    # 配線実証に大スケールは不要)。verify の CorrectnessWorkload は pipeline の既定。
    return PerfConfig(records=100_000, threads=4,
                      workload={"ycsb_rratio": "50", "ycsb_zipf_skew": "0.9",
                                "ycsb_rmw": "false"}, extime=1, reps=2)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="P3 coder wiring kickoff")
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

    cfg, perf = ident.bind_admission_policy(_cfg(), build_context.policy), _perf()
    assert_pinned_clean(sub, PIN)
    print("=== 完了条件 1: dirty no-op → coder namespace の cache-miss commit ===")
    with applied(os.path.join(root, NOOP_PATCH), PIN, sub):
        s1 = run_campaign(cfg, [STOCK_G], perf, ENV_TAG, CLK, numactl=NUMA,
                          authorization_contract=env_contract.lookup(ENV_TAG),
                          build_context=build_context,
                          campaign_namespace="exploration")

    print("\n=== 完了条件 2: 純 timing static50 → cache-miss 新規ビルド 1 周 ===")
    with applied(os.path.join(root, STATIC_PATCH), PIN, sub):
        s2 = run_campaign(cfg, [STATIC_G], perf, ENV_TAG, CLK, numactl=NUMA,
                          authorization_contract=env_contract.lookup(ENV_TAG),
                          build_context=build_context,
                          campaign_namespace="exploration")

    # --- WAL 機械判定 (完了条件の文言どおり。宣言でなくレコードを gate にする) ---
    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    v1 = next((r.variant for r in s1.results), variant_id(STOCK_G))
    r1 = wal.records_by_stage(layout, v1)
    v2 = next((r.variant for r in s2.results), None)
    r2 = wal.records_by_stage(layout, v2) if v2 else {}

    checks = {
        # 条件 1: dirty no-op は coder authority/new namespace が必須
        "1. no-op が dirty coder admission":
            v1 is not None
            and (r1.get("build_start", {}).get("build_admission") or {}).get("class")
            == "coder-authored",
        "1. dirty no-op が cache-miss (trace)":
            r1.get("build_done", {}).get("trace_cached") is False,
        "1. dirty no-op が cache-miss (perf)":
            r1.get("build_done", {}).get("perf_cached") is False,
        "1. certified commit":
            "commit" in r1,
        # 条件 2: 別 id / cache-miss 新規ビルド / verify abort>0 / certified commit
        "2. static50 が stock と別 variant_id":
            v2 is not None and v2 != v1,
        "2. 非 stock src_token":
            v2 is not None
            and r2.get("build_start", {}).get("src_token") not in (None, "stock"),
        "2. cache-miss 新規ビルド (trace)":
            r2.get("build_done", {}).get("trace_cached") is False,
        "2. cache-miss 新規ビルド (perf)":
            r2.get("build_done", {}).get("perf_cached") is False,
        "2. verify abort>0 (合成枝が verify 中に実行された証拠)":
            (r2.get("verify_done", {}).get("aborts") or 0) > 0,
        "2. certified commit (fitness 込み 1 周)":
            "commit" in r2 and r2["commit"].get("fitness_tps") is not None,
    }
    print("\n=== 判定 (WAL 機械確認) ===")
    ok = True
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    if not checks["2. verify abort>0 (合成枝が verify 中に実行された証拠)"]:
        print("  ⚠ abort≈0 なら空振り認証 → S2-lite (競合度を上げた縮小 verify) を"
              "前倒す (phase3.md 完了条件 2 の分岐)")
    print(f"\nkickoff 完了条件: {'PASS (1 と 2 の AND)' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
