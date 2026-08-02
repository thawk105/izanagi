# -*- coding: utf-8 -*-
"""A2: between-run noise floor を実機で確定する独立ドライバ (直列・単一テナント, 絶対規律4)。

calibrator が確定済みの **within-run** noise floor (1 measure_point の reps の CV = その 1 測定の
品質, 2.28%) は、variant と baseline が**別 run/別ビルド**で測られる現実を過小評価する。compare の
採否丸め閾値は『差が信用できるかの下限』= **between-run** であるべき (roadmap §3.6(4), A2)。

ここでは silo の baseline genome (B0-L-W0 = p2_2 が比較に使う stock 構成) を確定動作点で、
**8 個の独立セッション** (各 = reps=5 の measure_point = 実 campaign 1 測定と同形) 回し、
session-median の CV (= between-run noise floor) を `stability.between_run_noise_floor` で出す。
同じ点で within-run floor (reps=10 の 1 measure_point) も測り、両者を併記する (用途が違うので
『between > within』とは主張しない — between=差の floor / within=測定の品質)。

high-abort 域こそ run 間ドリフトが大きい (worklog: no-backoff abort 82% が最大の分散源) ので、
write-heavy(rr5, high-abort) と balanced(rr50, 既存 within 2.28% の点) の 2 点で測る。fresh な
back-to-back セッションは cold-boot/温度ドリフトを含まない**下限**なので、wired する floor は本値と
cross-campaign の genuine な between データ (sweep vs repro, 別時間窓) を突き合わせ保守側に採る。
read-heavy(rr95) は段 8a D 偵察の必須前提 (D48 前提 (b)、シート F4 — trigger-gating 軸の
最良ケース側 workload) で追加 (2026-07-11)。既存 2 点と同形 (同 genome/同動作点) で測る。

**pin の注記 (2026-07-11):** 既存 2 点 (write-heavy/balanced) は dff0f1e (p2_2 歴史 pin) で
実測済み。本 driver は以後 `pin.CURRENT_PIN` でビルドする — floor の用途は現行 pin で走る
campaign (D 偵察等) の採否参照線であり、pin 側に合わせるのが用途に正しい。perf ビルド
(trace=False) では izanagi-trace ブランチの差分は #if TRACE で全て消えるため物理量としての
floor は pin 間で同等 (buildcache の nm ガードが trace シンボル混入を fails-closed に検査)。

  python orchestrator/campaign/between_run_floor.py            # 両動作点
  python orchestrator/campaign/between_run_floor.py write-heavy # 1 点だけ
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calibrator.analyze import noise_floor                       # noqa: E402
from calibrator.runner import measure_point                      # noqa: E402
from calibrator.stability import between_run_noise_floor        # noqa: E402
from campaign import buildcache, pin                             # noqa: E402
from campaign.build_admission import BuildAdmission, BuildProvenance  # noqa: E402
from campaign.layout import env_scope_dir                    # noqa: E402
from campaign.model import Genome                                # noqa: E402
from campaign.p2_2 import (CLK, ENV_TAG, EXTIME,                 # noqa: E402
                           NUMA, RECORDS, THREADS, _assert_single_tenant)

CCBENCH_COMMIT = pin.CURRENT_PIN   # docstring「pin の注記」参照 (2026-07-11)

# p2_2 が比較に使う stock 構成 = baseline。BACK_OFF=0 なので write-heavy では high-abort。
BASELINE = Genome("silo", {"BACK_OFF": 0, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                           "NO_WAIT_OF_TICTOC": 0, "WAL": 0})

WITHIN_REPS = 10        # within-run floor: 既存 calibration と同じ reps=10 (2.28% と同形)
SESSION_REPS = 5        # between: 各セッションは実 campaign と同形 (p2_2 REPS=5)
SESSIONS = 8            # 独立セッション数 (CV 推定の相対 SE ~27%, 保守側に丸めて使う)

POINTS = [
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
    ("read-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"}),
]


def _wl_tag(wl: dict) -> str:
    return (f"skew{str(wl['ycsb_zipf_skew']).replace('.', 'p')}"
            f"_rr{wl['ycsb_rratio']}_rmw{wl['ycsb_rmw']}")


def measure_point_floor(binary: str, workload: dict, log=print) -> dict:
    """1 動作点で within-run と between-run の noise floor を測る。"""
    def measure_session():
        pt = measure_point(binary, RECORDS, THREADS, CLK, extime=EXTIME,
                           reps=SESSION_REPS, workload=workload, numactl=NUMA)
        return pt.throughput            # session 代表値 = reps の median

    # within-run floor (reps=10 の 1 セッション = その測定の品質)。
    log(f"  [within] {WITHIN_REPS} reps を 1 セッションで ...")
    w_pt = measure_point(binary, RECORDS, THREADS, CLK, extime=EXTIME,
                         reps=WITHIN_REPS, workload=workload, numactl=NUMA)
    within = noise_floor(w_pt.throughputs)
    log(f"  [within] CV={'n/a' if within.cv is None else f'{within.cv*100:.2f}%'} "
        f"(median {'n/a' if within.median is None else f'{within.median:,.0f}'}, "
        f"abort {(w_pt.abort_rate or 0)*100:.0f}%)")

    # between-run floor (独立 8 セッションの session-median の CV)。セッション間の admission は
    # **lag-free な競合検知** (_assert_single_tenant = competing_bench_pids, A1 と同型) を使う。
    # settle (load EMA) は連続 run 間では残像でほぼ即 return し独立性も足さない (runner.settle
    # docstring) ので per-session ゲートには使わない。競合が現れたら fails-closed で中断 (規律4)。
    log(f"  [between] {SESSIONS} 独立セッション (各 reps={SESSION_REPS}) ...")
    between = between_run_noise_floor(measure_session, settle_fn=_assert_single_tenant,
                                      sessions=SESSIONS)
    log(f"  [between] CV={'n/a' if between.cv is None else f'{between.cv*100:.2f}%'} "
        f"(sessions={between.sessions}, median "
        f"{'n/a' if between.median is None else f'{between.median:,.0f}'})")
    return {
        "workload": workload, "genome": BASELINE.canonical(),
        "records": RECORDS, "threads": THREADS, "clocks_per_us": CLK,
        "abort_rate": w_pt.abort_rate, "run_cmd": w_pt.run_cmd,
        "within_run": {"reps": WITHIN_REPS, "cv": within.cv, "median": within.median,
                       "mean": within.mean, "stdev": within.stdev,
                       "throughputs": within.throughputs,
                       "high_variance": within.high_variance},
        "between_run": {"sessions": between.sessions, "reps_per_session": SESSION_REPS,
                        "cv": between.cv, "median": between.median, "mean": between.mean,
                        "stdev": between.stdev,
                        "session_throughputs": between.session_throughputs,
                        "high_variance": between.high_variance, "notes": between.notes},
    }


def _write_out(tag: str, workload: dict, res: dict, log=print) -> str:
    out_dir = os.path.join(env_scope_dir(ENV_TAG), "calibration")
    os.makedirs(out_dir, exist_ok=True)
    stem = f"between_run_noise_t{THREADS}_{_wl_tag(workload)}"
    json_path = os.path.join(out_dir, stem + ".json")
    # 既存の確定 calibration JSON は不可侵 (byte-identical provenance)。別ファイルに書く。
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    md_path = os.path.join(out_dir, stem + ".md")
    wr = res["between_run"]
    wi = res["within_run"]
    wi_cv = "n/a" if wi["cv"] is None else f"{wi['cv']*100:.2f}%"
    wr_cv = "n/a" if wr["cv"] is None else f"{wr['cv']*100:.2f}%"
    wi_med = "n/a" if wi["median"] is None else f"{wi['median']:,.0f}"
    wr_med = "n/a" if wr["median"] is None else f"{wr['median']:,.0f}"
    L = [f"# between-run noise floor — {ENV_TAG} / {tag} ({_wl_tag(workload)})", "",
         "> A2 (orchestrator/campaign/between_run_floor)。計測は trace-disabled build (規律1)・"
         "単一テナント直列 (規律4)。既存 calibration JSON は不可侵で本ファイルは別出力。", "",
         f"- genome (baseline): `{res['genome']}`",
         f"- 動作点: records={res['records']:,} / threads={res['threads']} / "
         f"clocks_per_us={res['clocks_per_us']} / {_wl_tag(workload)}",
         f"- abort_rate: {(res['abort_rate'] or 0)*100:.0f}%", "",
         "## noise floor (用途が違う 2 値を併記)", "",
         "| 種別 | 構成 | CV | median tps | 用途 |",
         "|---|---|---:|---:|---|",
         f"| within-run | {wi['reps']} reps × 1 session | {wi_cv} | "
         f"{wi_med} | その 1 測定の品質 (remeasure 品質ゲート) |",
         f"| between-run | {wr['sessions']} sessions × {wr['reps_per_session']} reps | "
         f"{wr_cv} | {wr_med} | 差が信用できるかの下限 (compare の丸め閾値) |", "",
         "between-run は session-median の散らばり。settle は admission (独立性でない) ため "
         "cold-boot/温度ドリフト未含 = **下限**。wired する floor は cross-campaign の genuine な "
         "between データと突き合わせ保守側に採る (worklog 2026-06-28)。", "",
         "**再現:**", "", "```bash", res["run_cmd"], "```", ""]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    log(f"  wrote {json_path}\n  wrote {md_path}")
    return json_path


def main(argv) -> int:
    sel = argv[1] if len(argv) > 1 else None
    pts = [p for p in POINTS if sel is None or p[0] == sel]
    if not pts:
        print(f"unknown point: {sel} (選択肢: {[p[0] for p in POINTS]})")
        return 2

    _assert_single_tenant()             # campaign 冒頭の単一テナント確認 (規律4)
    print("[build] baseline (B0-L-W0, perf=trace-disabled) ...")
    br = buildcache.build(
        BASELINE, ccbench_commit=CCBENCH_COMMIT, trace=False,
        admission=BuildAdmission(BuildProvenance.STOCK_OR_PINNED),
    )
    print(f"[build] {'cache hit' if br.cached else 'built'}: {br.binary}")

    results = []
    for tag, workload in pts:
        print(f"\n=== between-run floor  workload={tag}  ({workload}) ===")
        res = measure_point_floor(br.binary, workload)
        _write_out(tag, workload, res)
        results.append((tag, res))

    print("\n=== between-run noise floor サマリ ===")
    print(f"  {'workload':12s} {'within(10rep)':>14s} {'between(8sess)':>15s} {'abort':>6s}")
    for tag, res in results:
        wi = res["within_run"]["cv"]
        wr = res["between_run"]["cv"]
        ab = res["abort_rate"] or 0
        print(f"  {tag:12s} "
              f"{('n/a' if wi is None else f'{wi*100:.2f}%'):>14s} "
              f"{('n/a' if wr is None else f'{wr*100:.2f}%'):>15s} "
              f"{ab*100:>5.0f}%")
    print("\n→ wired する BETWEEN_RUN_CV は上記 fresh 値と cross-campaign genuine データ "
          "(sweep vs repro) の保守側 (最大) を人間が確定する。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
