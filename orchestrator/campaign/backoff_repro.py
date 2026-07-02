# -*- coding: utf-8 -*-
"""backoff ケーススタディの cross-run 再現性チェック ([P0], 敵対的検証 measurement レンズ)。

敵対的検証は「+38.3%/+11.3% は単一 back-to-back 系列 (rounds=1, 同一 14 分窓) の産物で
別系列再現が未確認」を最致命の穴に挙げた。そこで**勝者と参照だけ**を、

  - **別 campaign** (別 spec → 別 campaign-id, recovery で skip されない)
  - **逆順** (fix10 → fix5 → none。元 sweep は none → … → fix10 の昇順)
  - 別の時間窓 (元 sweep の数時間後)

で再測し、winner-vs-no-backoff の相対差が元の値と between-run noise floor 内で一致するか見る。
別 boot ではないが「時間窓 + run 順序」の交絡は分離できる。各 genome は pipeline で
build(cache hit)→verify(正しさゲート)→bench。

  python orchestrator/campaign/backoff_repro.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import ident, source_digest, wal                   # noqa: E402
from campaign.backoff_sweep import _BASE                         # noqa: E402
from campaign.layout import campaign_layout                      # noqa: E402
from campaign.loop import run_campaign                           # noqa: E402
from campaign.model import CampaignConfig, Genome                # noqa: E402
from campaign.p2_2 import (BETWEEN_RUN_CV, CLK, ENV_TAG, EXTIME,  # noqa: E402
                           NUMA, RECORDS, REPS, THREADS, _assert_single_tenant)
from campaign.pipeline import PerfConfig, variant_id             # noqa: E402

CCBENCH_COMMIT = "dff0f1e"

# 元 sweep で確定した値 (committed)。再現の比較基準。
ORIG = {
    "write-heavy": {"workload": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"},
                    "best_us": 10, "none": 1882125.0, "best": 2603521.0, "rel": 0.383},
    "balanced":    {"workload": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
                    "best_us": 5, "none": 2791760.0, "best": 3106342.0, "rel": 0.113},
}
# 再現トレランス = between-run floor (A2)。再測 rel と元 rel は別 run の比なので between-run。
# なお rel_drift = rel(再測) - rel(元) は **2 つの between-run 比の差** なので、単一 floor を当てる
# のはむしろ厳しめ (保守的)。+38%/+11% の勝者再現はこの floor に鈍感 (worklog 2026-06-28)。
NOISE_CV = BETWEEN_RUN_CV


def _genomes_reversed(best_us: int):
    """勝者と参照だけ、逆順 (fix<best> → fix5 → none) で。"""
    others = {5, 10}
    gs = [Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": best_us})]
    for n in sorted(others - {best_us}):
        gs.append(Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": n}))
    gs.append(Genome("silo", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1}))   # none を最後に
    return gs


def _config(tag: str, workload: dict) -> CampaignConfig:
    return CampaignConfig(
        spec_slug=f"backoff-repro-silo-{tag}", search_tag="repro",
        spec_content=f"P0 cross-run 再現性: backoff winner 再測 (逆順) — workload={tag}",
        ccbench_commit=CCBENCH_COMMIT,
        search_config={"scale": "silo-backoff-repro", "base": "L-W0",
                       "order": "reversed", "workload": tag,
                       "records": RECORDS, "threads": THREADS, "ycsb": workload},
        trial="p2-backoff-repro")


def _bench_tps(layout, v: str) -> float:
    """campaign WAL から variant id v の median tps を引く。"""
    tps = None
    for r in wal.read_records(layout):
        if r.variant == v and r.stage == "bench_done":
            tps = r.payload.get("median_tps")
    return tps


def run_workload(tag: str, log=print) -> dict:
    _assert_single_tenant()
    o = ORIG[tag]
    gs = _genomes_reversed(o["best_us"])
    cfg = _config(tag, o["workload"])
    perf = PerfConfig(records=RECORDS, threads=THREADS, workload=o["workload"],
                      extime=EXTIME, reps=REPS)
    log(f"\n=== backoff repro  workload={tag}  逆順 {[g.flags['BACKOFF_FIXED'] for g in gs]} ===")
    s = run_campaign(cfg, gs, perf, ENV_TAG, CLK, numactl=NUMA, log=log)

    layout = campaign_layout(str(ident.campaign_id(cfg)))
    # WAL キーは run_campaign が src_token まで確定した variant id (D24)。identity を再計算せず
    # summary の EvalResult から引く (consumer が確定点を二重化しない — 旧実装は variant_id(genome)=
    # stock id で引き、BACKOFF_FIXED の非 stock src_token id を取りこぼし「判定不能」に倒れていた)。
    # ただし recovery skip された variant は s.results に載らない (中断→再開・完走後の再実行)。
    # その場合のみ loop と同一の確定窓口 (source_digest.resolve) で id を計算して WAL から引く
    # (resume 耐性 — WAL に bench_done が揃っているのに判定不能へ倒れない、洗練検査 MED)。
    vid = {r.genome.canonical(): r.variant for r in s.results}

    def _vid_of(g: Genome):
        v = vid.get(g.canonical())
        if v is not None:
            return v
        try:
            return variant_id(g, source_digest.resolve(g, CCBENCH_COMMIT))
        except RuntimeError:
            return None          # 確定不能 → 従来どおり判定不能に倒す (fails-closed)

    none_g = Genome("silo", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1})
    best_g = Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": o["best_us"]})
    none_v, best_v = _vid_of(none_g), _vid_of(best_g)
    none_tps = _bench_tps(layout, none_v) if none_v else None
    best_tps = _bench_tps(layout, best_v) if best_v else None
    if none_tps is None or best_tps is None:
        log(f"  [{tag}] 再測値が取れない → 判定不能")
        return {"tag": tag, "ok": False}
    rel = best_tps / none_tps - 1
    # 再現判定: 再測の rel が元 rel と noise floor 内で一致するか。
    rel_drift = rel - o["rel"]
    reproduced = abs(rel_drift) <= NOISE_CV
    log(f"  [{tag}] 再測: none={none_tps:,.0f} best({o['best_us']}us)={best_tps:,.0f} "
        f"rel={rel*100:+.1f}% (元 {o['rel']*100:+.1f}%, drift {rel_drift*100:+.1f}%) "
        f"→ {'✅再現' if reproduced else '⚠乖離'}")
    return {"tag": tag, "ok": reproduced, "rel": rel, "orig_rel": o["rel"],
            "none": none_tps, "best": best_tps, "aborted": s.aborted}


def main() -> int:
    results = [run_workload(t) for t in ORIG]
    print("\n=== cross-run 再現性サマリ ===")
    for r in results:
        if r.get("rel") is not None:
            print(f"  {r['tag']}: rel {r['rel']*100:+.1f}% vs 元 {r['orig_rel']*100:+.1f}% "
                  f"→ {'再現' if r['ok'] else '乖離'}")
    ok = all(r.get("ok") for r in results)
    print(f"\ncross-run 再現性: {'✅ +38%/+11% は別系列・逆順で再現' if ok else '⚠ 乖離あり (要精査)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
