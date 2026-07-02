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
from campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,        # noqa: E402
                            STAGE_BUILD_START, STAGE_COMMIT)

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


@dataclass
class Rejection:
    """verify-red で reject された variant の構造化 anomaly (規律3 の次手入力)。

    「なぜ壊れたか」= どの trx 間の・どの依存 (ww/wr/rw) で・どの版で cycle ができたか。
    fitness は無い (正しさゲートで失格 = 採用しない、規律2)。次手生成はこれを読んで
    「その依存を断つ方向」の variant を作る。Phase 3 (LLM が RED variant を出す) で
    load-bearing になる (Phase 2 は全緑で空)。"""
    genome: str                       # canonical
    flags: Dict[str, int]
    verdict: str                      # non-serializable | indeterminate
    anomalies: List[dict] = field(default_factory=list)   # 構造化 (cycle/edges/reasons)
    integrity: Dict = field(default_factory=dict)
    # コード軸の識別 (D23): Phase 3 では同一 genome.flags で #if 枝の中身だけ違う複数
    # variant が生まれる。これらが両方 RED になったとき、genome/flags だけでは
    # 「どのコード diff がどの anomaly を生んだか」を次手生成が帰属できない (alias)。
    variant: str = ""                 # WAL キー (src_token 込みの variant id)
    src_token: str = ""               # BUILD_START payload の src_token


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


def load_rejections(layout: CampaignLayout) -> List[Rejection]:
    """campaign WAL から verify-red で reject された variant の構造化 anomaly を読む。

    規律3 (正しさシグナルを後付けにしない) の次手入力経路: verifier の構造化 anomaly が
    pipeline で abort payload (`{"verify": result_to_dict(vr)}`) に載っているのを拾い、
    「なぜ壊れたか」を次手生成 (critic/planner) が読める形で返す。build-error 等の verify を
    伴わない abort は除外 (verify payload を持つ = 正しさゲート不通過のみ)。

    Phase 2 (フラグ列挙 = 全 variant 緑) では空。Phase 3 (LLM が RED variant を合成) で
    load-bearing。`load_workload` が committed (緑) を読むのと対をなす (red を読む)。"""
    genome_of: Dict[str, str] = {}
    srctok_of: Dict[str, str] = {}
    out: List[Rejection] = []
    for r in wal.read_records(layout):
        if r.stage == STAGE_BUILD_START:
            genome_of[r.variant] = r.payload.get("genome", genome_of.get(r.variant, ""))
            srctok_of[r.variant] = r.payload.get("src_token", srctok_of.get(r.variant, ""))
        elif r.stage == STAGE_ABORT:
            v = r.payload.get("verify")
            if v is None:                  # build-error/trace 異常等は verify を持たない
                continue
            g = genome_of.get(r.variant, "")
            out.append(Rejection(
                genome=g, flags=_parse_flags(g) if "|" in g else {},
                verdict=v.get("verdict", r.payload.get("reason", "")),
                anomalies=v.get("anomalies", []),
                integrity=v.get("integrity", {}),
                variant=r.variant, src_token=srctok_of.get(r.variant, "")))
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
    """P2-2 の 3 workload campaign を dir 名 prefix discover で引き digest を作る。

    C1 回避: 旧実装の campaign-id 再計算 (宣言 ccbench_commit 依存) は submodule pin
    前進で on-disk id と食い違い、count=0 を沈黙して返していた。discover できなければ
    raise (critic の入力が空のまま進む方が有害、規律3)。"""
    from campaign.p2_2 import WORKLOADS
    from campaign.replay import discover_p2_2_dir
    return [build_digest(tag, wl, discover_p2_2_dir(tag)) for tag, wl in WORKLOADS]


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
