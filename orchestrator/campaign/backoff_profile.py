# -*- coding: utf-8 -*-
"""P2-4: backoff ケーススタディの [P0] 機序純度 — spin 命令を分離し「有用 IPC」を実測する。

backoff ケーススタディの敵対的検証が残した最大の穴 [P0]: 看板 write-heavy で
「throughput = (1-abort)×ipc の積」が peak 位置を外す (積 25us vs throughput 10us)。残差
K=tps/((1-abort)·ipc) が backoff 増で 15-31% 低下 = 第三因子 = backoff() の `_mm_pause`+`rdtscp`
busy-wait スピンが perf instructions/cycles を希釈する。total ipc は「有用な stall」と
「スピン希釈」の混交になっている (insight 2026-06-22_p2-case-study-backoff-synthesis)。

ここでは BACKOFF_NOINLINE=1 (診断専用 inert patch) で backoff() を独立シンボル化し、
`perf record -e cycles,instructions` で **Backoff::backoff の cycle%/instruction%** を分離 →
**有用 IPC = (全命令 − spin 命令) / (全 cycle − spin cycle)** を実測する。backoff 量を振って
有用 IPC が一定/単調なら、total ipc の低下は純粋に spin 希釈であり、機序は
「backoff は abort を減らす (有用 txn 増) が spin は純 latency。**有用仕事の per-instruction 効率は
不変**」と確定する (= [P0] 解消)。

絶対規律1: perf は trace-disabled build に当てる。BACKOFF_NOINLINE は trace と直交 (診断専用、
default 0=inert で stock 不変)。絶対規律4: 単一テナント直列・pgrep gate。

  python orchestrator/campaign/backoff_profile.py            # write-heavy + balanced
  python orchestrator/campaign/backoff_profile.py write-heavy
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator.benchparse import (abort_rate as parse_abort,    # noqa: E402
                                   parse_bench_stdout, throughput_tps)
from ..holdout_observation import (                         # noqa: E402
    assert_holdout_observation_admitted,
)
from . import buildcache, source_digest                   # noqa: E402
from .build_admission import (GeneratorId, attest_generator_output,  # noqa: E402
                                      build_run_context, derive_build_admission)
from .layout import env_scope_dir                    # noqa: E402
from .model import Genome                                # noqa: E402
from .p2_2 import (CCBENCH_COMMIT, CLK, ENV_TAG, EXTIME,  # noqa: E402
                           RECORDS, THREADS, _assert_single_tenant)


_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
NUMA = ["numactl", "--interleave=all"]
REPS = 3                       # spin%/ipc は run 間安定。tps は median を採る
BACKOFF_US = [2, 5, 10, 25, 50, 100]   # 静的 backoff 量 (sweep と同じ grid)
PERF_EVENTS = "cycles,instructions"

POINTS = [
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
]


def _genome(backoff_us):
    """backoff_us=None → 無 backoff (BACK_OFF=0)。それ以外 → 静的固定 + noinline 診断。"""
    if backoff_us is None:
        return Genome("silo", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1,
                               "BACKOFF_NOINLINE": 1})
    return Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": backoff_us,
                           "BACKOFF_NOINLINE": 1})


def _flags(workload):
    f = [f"-thread_num={THREADS}", f"-ycsb_tuple_num={RECORDS}",
         f"-extime={EXTIME}", f"-clocks_per_us={CLK}"]
    for k, v in workload.items():
        f.append(f"-{k}={v}")
    return f


def _parse_perf_report(report_text):
    """perf report --stdio から (event→total_count) と Backoff::backoff の event 別 % を取る。

    出力はイベント区切り (`# Samples: ... of event 'cycles'` … `# Event count (approx.): N`) ごとに
    シンボル行 (`   65.44%  ... [.] Backoff::backoff`) が並ぶ。event ごとに total と spin% を拾う。"""
    totals = {}      # event -> total count
    spin_pct = {}    # event -> Backoff::backoff の overhead %
    cur = None
    for ln in report_text.splitlines():
        m = re.search(r"of event '([^']+)'", ln)
        if m:
            cur = m.group(1)
            spin_pct.setdefault(cur, 0.0)   # シンボルが出なければ 0 (= 呼ばれない/閾値下)
            continue
        m = re.search(r"Event count \(approx\.\):\s*(\d+)", ln)
        if m and cur:
            totals[cur] = int(m.group(1))
            continue
        if cur and "Backoff::backoff" in ln:
            m = re.match(r"\s*([\d.]+)%", ln)
            if m:
                spin_pct[cur] = float(m.group(1))
    return totals, spin_pct


def _profile_run(binary, workload, tmp):
    """1 run perf record → (tps, abort, total_cycles, total_instr, spin_cyc%, spin_instr%)。"""
    data = os.path.join(tmp, "perf.data")
    cmd = list(NUMA) + ["perf", "record", "-o", data, "-e", PERF_EVENTS,
                        "--", binary] + _flags(workload)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp, timeout=180)
    if proc.returncode != 0 or not os.path.exists(data):
        raise RuntimeError(f"perf record failed (rc={proc.returncode}, "
                           f"perf.data={'有' if os.path.exists(data) else '無'}): "
                           f"{proc.stderr[-400:]}")
    metrics = parse_bench_stdout(proc.stdout)
    if not metrics:
        raise RuntimeError(f"ccbench produced no metrics. stderr={proc.stderr[-300:]}")
    tps = throughput_tps(metrics)
    abort = parse_abort(metrics)
    rep = subprocess.run(["perf", "report", "-i", data, "--stdio",
                          "--percent-limit", "0"], capture_output=True, text=True)
    if rep.returncode != 0:
        raise RuntimeError(f"perf report failed (rc={rep.returncode}): {rep.stderr[-300:]}")
    totals, spin = _parse_perf_report(rep.stdout)
    return {
        "tps": tps, "abort": abort,
        "cycles": totals.get("cycles"), "instructions": totals.get("instructions"),
        "spin_cyc_pct": spin.get("cycles", 0.0),
        "spin_instr_pct": spin.get("instructions", 0.0),
    }


def _median(xs):
    s = sorted(x for x in xs if x is not None)
    return s[len(s) // 2] if s else None


def profile_point(backoff_us, workload, log=print):
    """1 backoff 量を REPS 回 profile し、有用 IPC を含む集計を返す。"""
    workload_snapshot = dict(workload)
    assert_holdout_observation_admitted(
        gflags=tuple(_flags(workload_snapshot)), admission=None,
    )
    g = _genome(backoff_us)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_PROFILE)
    evidence = source_digest.resolve_evidence(g, CCBENCH_COMMIT)
    capability = attest_generator_output(
        build_context, evidence,
        generator_input_sha256=hashlib.sha256(
            f"backoff-profile/v1|{g.canonical()}".encode("utf-8")
        ).hexdigest(),
    )
    br = buildcache.build(
        g, ccbench_commit=CCBENCH_COMMIT, trace=False,
        admission=derive_build_admission(
            build_context, evidence, generator_receipt=capability,
        ),
        build_context=build_context, source_evidence=evidence,
    )
    _assert_single_tenant()        # 各点の頭で再確認 (長い perf ループでも fail-closed, 規律4)
    runs = []
    for _ in range(REPS):
        tmp = tempfile.mkdtemp(prefix="izanagi_prof_")
        try:
            runs.append(_profile_run(br.binary, workload_snapshot, tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    # 代表 = tps 中央値の run (spin%/ipc は安定なのでその run の値を採る)
    tmed = _median([r["tps"] for r in runs])
    rep = min((r for r in runs if r["tps"] is not None),
              key=lambda r: abs(r["tps"] - tmed), default=runs[-1])
    cyc, instr = rep["cycles"], rep["instructions"]
    spin_c, spin_i = rep["spin_cyc_pct"] / 100.0, rep["spin_instr_pct"] / 100.0
    total_ipc = (instr / cyc) if (cyc and instr) else None
    useful_cyc = cyc * (1 - spin_c) if cyc else None
    useful_instr = instr * (1 - spin_i) if instr else None
    useful_ipc = (useful_instr / useful_cyc) if (useful_cyc and useful_instr) else None
    abort = rep["abort"]
    # 残差 K = tps / ((1-abort)·ipc)。total と useful の両方で出し、useful が一定かを見る。
    k_total = (tmed / ((1 - abort) * total_ipc)) if (tmed and abort is not None
                                                     and total_ipc) else None
    k_useful = (tmed / ((1 - abort) * useful_ipc)) if (tmed and abort is not None
                                                       and useful_ipc) else None
    row = {
        "backoff_us": backoff_us if backoff_us is not None else 0,
        "is_none": backoff_us is None,
        "genome": g.canonical(), "tps_median": tmed, "abort": abort,
        "total_ipc": total_ipc, "useful_ipc": useful_ipc,
        "spin_cyc_pct": rep["spin_cyc_pct"], "spin_instr_pct": rep["spin_instr_pct"],
        "k_total": k_total, "k_useful": k_useful,
        "tps_all": [r["tps"] for r in runs],
    }
    log(f"  backoff={row['backoff_us']:>4}us  tps={tmed:>12,.0f}  abort={abort*100:5.1f}%  "
        f"spin_cyc={row['spin_cyc_pct']:5.1f}%  total_ipc={total_ipc:.3f}  "
        f"useful_ipc={useful_ipc:.3f}  K_useful={k_useful:,.0f}")
    return row


def profile_workload(tag, workload, log=print):
    log(f"\n=== backoff profile  workload={tag}  ({workload}) ===")
    log(f"  {'pt':>6} {'tps':>14} {'abort':>7} {'spin_cyc':>9} {'tot_ipc':>8} "
        f"{'use_ipc':>8} {'K_useful':>12}")
    rows = [profile_point(None, workload, log)]
    for us in BACKOFF_US:
        rows.append(profile_point(us, workload, log))
    return rows


def _write_out(tag, workload, rows, log=print):
    out_dir = os.path.join(env_scope_dir(ENV_TAG), "profile")
    os.makedirs(out_dir, exist_ok=True)
    wl = f"skew{workload['ycsb_zipf_skew'].replace('.', 'p')}_rr{workload['ycsb_rratio']}"
    stem = os.path.join(out_dir, f"backoff_profile_t{THREADS}_{wl}")
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump({"workload": workload, "tag": tag, "threads": THREADS,
                   "records": RECORDS, "rows": rows}, f, indent=2, ensure_ascii=False)
    # useful_ipc の一定性 = [P0] 解消の核
    uipc = [r["useful_ipc"] for r in rows if r["useful_ipc"]]
    tipc = [r["total_ipc"] for r in rows if r["total_ipc"]]
    # sweet-spot (0-10us, throughput ピーク帯) と over-throttle を含む全域を分けて出す。
    # 核命題「有用 IPC は一定」は sweet-spot 限定 (全域は over-throttle の二次低下を含むので大きく出る)。
    uipc_sweet = [r["useful_ipc"] for r in rows if r["useful_ipc"] and r["backoff_us"] <= 10]
    def spread(xs):
        return (max(xs) - min(xs)) / (sum(xs) / len(xs)) if xs else None
    L = [f"# backoff profile — {ENV_TAG} / {tag} ({wl})", "",
         "> P2-4 (orchestrator/campaign/backoff_profile)。BACKOFF_NOINLINE 診断 build で perf record "
         "(cycles,instructions) し backoff() spin を分離。trace-disabled (規律1)・単一テナント直列 (規律4)。", "",
         "## 有用 IPC (spin 除外) は backoff 量で一定か = [P0] の核", "",
         f"- total_ipc の散布 (max-min)/mean = **{spread(tipc)*100:.1f}%** (全域。backoff 量で大きく動く = 積モデル破綻の原因)",
         f"- **useful_ipc の散布 (sweet-spot 0-10us) = {spread(uipc_sweet)*100:.1f}%** "
         "(throughput ピーク帯。ここで一定 = total_ipc 低下は純 spin 希釈 = [P0] の核命題)",
         f"- useful_ipc の散布 (全域 0-100us) = {spread(uipc)*100:.1f}% "
         "(over-throttle 域 25-100us の有用 IPC 二次低下を含むので大きく出る。一定主張は sweet-spot 限定)",
         "",
         "| backoff us | tps (median) | abort% | spin cyc% | spin instr% | total IPC | useful IPC | K_total | K_useful |",
         "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        L.append(f"| {r['backoff_us']}{'(none)' if r['is_none'] else ''} | "
                 f"{r['tps_median']:,.0f} | {r['abort']*100:.1f} | {r['spin_cyc_pct']:.1f} | "
                 f"{r['spin_instr_pct']:.1f} | {r['total_ipc']:.3f} | {r['useful_ipc']:.3f} | "
                 f"{(r['k_total'] or 0):,.0f} | {(r['k_useful'] or 0):,.0f} |")
    L += ["", "注: tps は **perf record 下** の値 (sampling overhead 込み)。headline throughput は",
          "stock inline build の値 (P2-2/backoff_sweep)。ここは spin%/IPC 比の機序分析専用。", ""]
    with open(stem + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    log(f"  wrote {stem}.json / .md  (useful_ipc 散布 {spread(uipc)*100:.1f}% vs total_ipc {spread(tipc)*100:.1f}%)")
    return stem + ".json"


def main(argv):
    # 既定は [P0] の看板 write-heavy 単独 (balanced は積モデルが元々合致するので [P0] の核でない、
    # D20 で繰り延べ)。`all` で全 POINTS、`<tag>` で個別。
    sel = argv[1] if len(argv) > 1 else "write-heavy"
    pts = POINTS if sel == "all" else [p for p in POINTS if p[0] == sel]
    if not pts:
        print(f"unknown point: {sel} (選択肢: {[p[0] for p in POINTS]} / all)")
        return 2
    _assert_single_tenant()
    for tag, workload in pts:
        rows = profile_workload(tag, workload)
        _write_out(tag, workload, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
