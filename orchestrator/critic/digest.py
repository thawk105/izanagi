# -*- coding: utf-8 -*-
"""WAL の leading indicators → critic 用 digest (genome 別表 + フラグ軸の限界効果)。

critic は「生のカウンタでなく組み合わせて読み、特定の設計選択に帰属させる」
(agent-architecture §critic)。そのために必要な構造化を機械側で先に行う:

1. **genome 別の leading indicators** — throughput / abort_rate / latency / llc_miss /
   ipc を 1 行ずつ。
2. **フラグ軸ごとの限界効果** — 各設計選択 (BACK_OFF / no-wait 政策 / WAL) を
   フリップしたとき各指標がどう動くか (他フラグで周辺化した平均)。これが
   「fitness を設計選択に帰属させる」核心。例: BACK_OFF 0→1 で throughput が
   半減し latency が 3 倍だが abort_rate はほぼ不変 → backoff のコストは
   contention 低減でなく latency と読める。

純データ整形 (machine 非依存)。実走・書き込みはしない。
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import wal                                          # noqa: E402
from campaign.layout import CampaignLayout                        # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_START,  # noqa: E402
                            STAGE_COMMIT)

# critic が見る指標と「大きいほど良いか」(throughput/ipc は大、他は小が良い)。
INDICATORS = ["throughput_tps", "abort_rate", "latency_ns", "llc_miss_rate", "ipc"]
HIGHER_IS_BETTER = {"throughput_tps": True, "ipc": True,
                    "abort_rate": False, "latency_ns": False, "llc_miss_rate": False}


@dataclass
class GenomeLI:
    """1 genome の leading indicators (committed なもの)。"""
    genome: str                       # canonical
    flags: Dict[str, int]
    li: Dict[str, Optional[float]]    # INDICATORS → 値

    def axis_value(self, axis: str) -> Optional[str]:
        """フラグ軸の値 (no-wait は L/T の categorical に畳む)。"""
        if axis == "BACK_OFF":
            return str(self.flags.get("BACK_OFF"))
        if axis == "WAL":
            return str(self.flags.get("WAL"))
        if axis == "no_wait":
            if self.flags.get("NO_WAIT_LOCKING_IN_VALIDATION") == 1:
                return "L"            # no-wait-locking = 競合で即 abort
            if self.flags.get("NO_WAIT_OF_TICTOC") == 1:
                return "T"            # tictoc-no-wait = 解放して retry
            return None
        return None


@dataclass
class AxisEffect:
    """1 フラグ軸の限界効果 = 各水準での指標平均 + 差。"""
    axis: str
    levels: List[str]
    # indicator → {level: 平均値}
    means: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # indicator → throughput の相対差 (level[1] / level[0] - 1) 等の代表差
    rel_throughput: Optional[float] = None    # 主軸 = throughput の相対変化


@dataclass
class WorkloadDigest:
    tag: str
    workload: Dict[str, str]
    genomes: List[GenomeLI]
    axes: List[AxisEffect]
    fastest: Optional[GenomeLI] = None


_AXES = ["BACK_OFF", "no_wait", "WAL"]


def _parse_flags(canonical: str) -> Dict[str, int]:
    body = canonical.split("|", 1)[1]
    return {k: int(v) for k, v in (kv.split("=") for kv in body.split(","))}


def load_workload(layout: CampaignLayout) -> List[GenomeLI]:
    """campaign WAL から **committed** genome の leading indicators を読む。

    bench_done だけで拾うと、bench は走ったが COMMIT 前にクラッシュした half-evaluated
    な点 (A: atomicity の漏れ窓) を採用しうる。STAGE_COMMIT がある variant だけに絞る
    (採用済み = 全段通過した genome のみを critic に渡す)。"""
    genome_of: Dict[str, str] = {}
    li_of: Dict[str, Dict] = {}
    committed: set = set()
    for r in wal.read_records(layout):
        if r.stage == STAGE_BUILD_START:
            genome_of[r.variant] = r.payload.get("genome", genome_of.get(r.variant, ""))
        elif r.stage == STAGE_BENCH_DONE:
            li = r.payload.get("leading_indicators")
            if li is not None:
                li_of[r.variant] = li
        elif r.stage == STAGE_COMMIT:
            committed.add(r.variant)
    out = []
    for v, li in li_of.items():
        g = genome_of.get(v, "")
        if not g or v not in committed:      # 採用済み (commit あり) のみ
            continue
        out.append(GenomeLI(genome=g, flags=_parse_flags(g),
                            li={k: li.get(k) for k in INDICATORS}))
    out.sort(key=lambda x: (x.li.get("throughput_tps") or 0), reverse=True)
    return out


def _mean(xs: List[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def axis_effects(genomes: List[GenomeLI], axis: str) -> AxisEffect:
    """軸を水準でグループ化し、各指標の水準別平均を出す (他フラグで周辺化)。"""
    buckets: Dict[str, List[GenomeLI]] = {}
    for g in genomes:
        lv = g.axis_value(axis)
        if lv is not None:
            buckets.setdefault(lv, []).append(g)
    levels = sorted(buckets)
    eff = AxisEffect(axis=axis, levels=levels)
    for ind in INDICATORS:
        eff.means[ind] = {}
        for lv in levels:
            m = _mean([g.li.get(ind) for g in buckets[lv]])
            if m is not None:
                eff.means[ind][lv] = m
    # 主軸 throughput の相対差 (2 水準のときのみ意味を持つ)。
    tp = eff.means.get("throughput_tps", {})
    if len(levels) == 2 and tp.get(levels[0]):
        eff.rel_throughput = tp[levels[1]] / tp[levels[0]] - 1.0
    return eff


def build_digest(tag: str, workload: Dict[str, str],
                 layout: CampaignLayout) -> WorkloadDigest:
    genomes = load_workload(layout)
    axes = [axis_effects(genomes, a) for a in _AXES]
    fastest = genomes[0] if genomes else None
    return WorkloadDigest(tag=tag, workload=workload, genomes=genomes,
                          axes=axes, fastest=fastest)


def _fmt(ind: str, v: Optional[float]) -> str:
    if v is None:
        return "—"
    if ind == "throughput_tps":
        return f"{v:,.0f}"
    if ind == "latency_ns":
        return f"{v:,.0f}ns"
    if ind in ("abort_rate", "llc_miss_rate"):
        return f"{v * 100:.2f}%"
    return f"{v:.2f}"            # ipc


def load_p2_2_digests() -> List[WorkloadDigest]:
    """P2-2 の 3 workload campaign を campaign-id 再計算で引き digest を作る。"""
    from campaign import ident
    from campaign.layout import campaign_layout
    from campaign.p2_2 import WORKLOADS, config_for
    out = []
    for tag, wl in WORKLOADS:
        lay = campaign_layout(str(ident.campaign_id(config_for(tag, wl))))
        if os.path.exists(lay.wal_file):
            out.append(build_digest(tag, wl, lay))
    return out


def render_text(digests: List[WorkloadDigest]) -> str:
    """critic に渡す人間/LLM 可読 digest。genome 別表 + 軸の限界効果。"""
    L: List[str] = ["# critic digest — silo leading indicators (P2-3)", ""]
    for d in digests:
        wl = ", ".join(f"{k}={v}" for k, v in sorted(d.workload.items()))
        L.append(f"## workload: {d.tag} ({wl})")
        L.append("")
        L.append("genome | " + " | ".join(INDICATORS))
        L.append("---|" + "|".join("---" for _ in INDICATORS))
        for g in d.genomes:
            cells = [_fmt(i, g.li.get(i)) for i in INDICATORS]
            L.append(f"{g.genome.split('|',1)[1]} | " + " | ".join(cells))
        L.append("")
        L.append("### フラグ軸の限界効果 (他フラグで周辺化した水準別平均)")
        for eff in d.axes:
            L.append(f"- **{eff.axis}** ({'/'.join(eff.levels)}):")
            for ind in INDICATORS:
                parts = [f"{lv}={_fmt(ind, eff.means[ind].get(lv))}"
                         for lv in eff.levels if lv in eff.means.get(ind, {})]
                if parts:
                    extra = ""
                    if ind == "throughput_tps" and eff.rel_throughput is not None:
                        extra = f"  (rel {eff.rel_throughput * 100:+.1f}%)"
                    L.append(f"    - {ind}: " + ", ".join(parts) + extra)
        L.append("")
    return "\n".join(L)


def main(argv) -> int:
    digests = load_p2_2_digests()
    if not digests:
        print("P2-2 campaign が無い (orchestrator/campaign/p2_2.py を先に実行)。")
        return 1
    print(render_text(digests))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
