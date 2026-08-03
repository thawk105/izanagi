# -*- coding: utf-8 -*-
"""P2-5 基盤: P2-2 WAL の replay-evaluate (新規直列計測なしで探索戦略を比較する土台)。

P2-5 (LLM 誘導探索 vs 全探索) は「最適到達までの評価本数」の比較であり、各 genome の
fitness は P2-2 (silo 全探索) で既に実測・WAL 永続化済み。よって誘導/ランダム/貪欲/全探索の
どの順序で genome を引いても、記録済み値を「評価結果」として配れば**新規の直列計測は不要**
(絶対規律4 のコストをゼロにし、between-run ドリフトが到達順位を揺らす交絡も消す)。

この module は P2-2 の 3 workload campaign WAL を読み、{canonical genome → 記録済み結果}
の lookup (= landscape) を構築し、`replay_evaluate` で配る。探索戦略 (guided/random/greedy)
はこの landscape の上を走る。

**C1 (campaign-id drift, phase2.md):** P2-2 dir 名 (5ffcabad 等) は古い ccbench_commit
'6656e93' を pre-image にして決まっており、現 pin (どの値であれ、以降前進済み) で campaign-id
を再計算すると別ハッシュになり dir を引けない。WAL の中身は commit 非依存なので、ここでは **dir 名の
prefix (slug-tag) で discover** する (id 再計算に依存しない)。re-run で同 tag に複数 dir が
できたら曖昧として明示エラー (黙って誤った方を拾わない)。
"""
from __future__ import annotations

import glob
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import wal                                          # noqa: E402
from campaign.artifact_admission import (AdmittedCampaign,        # noqa: E402
                                         require_admitted_campaign)
from campaign.genome import SILO_SPACE                            # noqa: E402
from campaign.layout import CampaignLayout, repo_output_root      # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_START,  # noqa: E402
                            STAGE_COMMIT, STAGE_VERIFY_DONE, Genome)
from campaign.p2_2 import BETWEEN_RUN_CV, WORKLOADS               # noqa: E402
from calibrator.stability import compare                         # noqa: E402

P2_2_SLUG = "p2-2-silo"
P2_2_SEARCH_TAG = "enumerate"


@dataclass(frozen=True)
class GenomeResult:
    """P2-2 が記録した 1 genome の評価結果 (replay で配る単位)。"""
    genome: str                          # canonical (silo|BACK_OFF=0,...)
    flags: Dict[str, int]
    fitness_tps: Optional[float]         # median_tps
    tps: List[float]                     # reps 反復の生 tps (compare 用)
    leading_indicators: Dict[str, float]
    certified: bool


def parse_flags(canonical: str) -> Dict[str, int]:
    body = canonical.split("|", 1)[1]
    return {k: int(v) for k, v in (kv.split("=") for kv in body.split(","))}


def genome_label(flags: Dict[str, int]) -> str:
    """短ラベル B{0,1}-{L,T}-W{0,1} (no-wait は L=locking / T=tictoc に畳む)。"""
    b = "B" + str(flags["BACK_OFF"])
    nw = "L" if flags.get("NO_WAIT_LOCKING_IN_VALIDATION") == 1 else "T"
    w = "W" + str(flags["WAL"])
    return f"{b}-{nw}-{w}"


def genome_from_label(label: str) -> Genome:
    """短ラベル B{0,1}-{L,T}-W{0,1} → Genome (genome_label の逆写像)。

    critic が候補ラベルで次手を返すので、それを SILO_SPACE 内の Genome に戻す。
    XOR 制約を満たさない/未知のラベルは ValueError (空間外を黙って評価しない、規律6)。"""
    parts = label.strip().split("-")
    if len(parts) != 3 or parts[0] not in ("B0", "B1") \
            or parts[1] not in ("L", "T") or parts[2] not in ("W0", "W1"):
        raise ValueError(f"不正な genome ラベル: {label!r} (期待 B{{0,1}}-{{L,T}}-W{{0,1}})")
    flags = {
        "BACK_OFF": int(parts[0][1]),
        "NO_WAIT_LOCKING_IN_VALIDATION": 1 if parts[1] == "L" else 0,
        "NO_WAIT_OF_TICTOC": 1 if parts[1] == "T" else 0,
        "WAL": int(parts[2][1]),
    }
    g = Genome("silo", flags)
    valid = {x.canonical() for x in SILO_SPACE.enumerate()}
    if g.canonical() not in valid:
        raise ValueError(f"ラベル {label!r} は SILO_SPACE の有効空間外 (XOR 制約違反)")
    return g


def discover_campaign_dir(slug: str, search_tag: str,
                          output_root: str = "") -> AdmittedCampaign:
    """campaign dir を `<slug>-<search_tag>-*` の名前 prefix で discover する。

    C1 回避 (phase2.md 選択肢a): campaign-id の再計算 (`ident.campaign_id(config_for(...))`)
    は宣言 ccbench_commit が submodule pin の前進でドリフトすると on-disk id と一致しなく
    なり、歴史的 campaign の WAL が沈黙して引けなくなる。dir 名 prefix なら id の
    pre-image に依存しない。WAL を持つ dir がちょうど 1 つでなければ明示エラー
    (re-run 重複を黙って選ばない)。"""
    root = output_root or repo_output_root()
    pat = os.path.join(root, "campaigns", f"{slug}-{search_tag}-*")
    hits = [d for d in sorted(glob.glob(pat))
            if os.path.exists(os.path.join(d, "runs", "wal.jsonl"))]
    if len(hits) != 1:
        raise FileNotFoundError(
            f"campaign dir ({slug}-{search_tag}): WAL を持つ dir がちょうど 1 つ要るが "
            f"{len(hits)} 個: {[os.path.basename(h) for h in hits]}。"
            "C1 回避で dir 名 prefix discover している。re-run で重複したら明示解決せよ。")
    return require_admitted_campaign(CampaignLayout(root=hits[0]))


def discover_p2_2_dir(tag: str, output_root: str = "") -> AdmittedCampaign:
    """P2-2 campaign dir を slug-tag prefix で discover (discover_campaign_dir の特化形)。"""
    return discover_campaign_dir(f"{P2_2_SLUG}-{tag}", P2_2_SEARCH_TAG, output_root)


def load_landscape(tag: str, output_root: str = "") -> Dict[str, GenomeResult]:
    """P2-2 の 1 workload WAL を読み {canonical genome → GenomeResult} を作る。

    digest.load_workload と同じく **committed (= 全段通過) genome のみ**採る
    (half-evaluated を混ぜない、A: atomicity)。"""
    view = discover_p2_2_dir(tag, output_root)
    genome_of: Dict[str, str] = {}
    bench_of: Dict[str, dict] = {}
    certified_of: Dict[str, bool] = {}
    committed: set = set()
    # [T-082] prefix 容認 (crash tail は黙って捨てる) — 公式判定に使わない。
    for r in view.records:
        if r.stage == STAGE_BUILD_START:
            genome_of[r.variant] = r.payload.get("genome", genome_of.get(r.variant, ""))
        elif r.stage == STAGE_BENCH_DONE:
            bench_of[r.variant] = r.payload
        elif r.stage == STAGE_VERIFY_DONE:
            certified_of[r.variant] = bool(r.payload.get("certified"))
        elif r.stage == STAGE_COMMIT:
            committed.add(r.variant)
    out: Dict[str, GenomeResult] = {}
    for v in committed:
        g = genome_of.get(v)
        p = bench_of.get(v)
        if not g or p is None:
            continue
        out[g] = GenomeResult(
            genome=g, flags=parse_flags(g),
            fitness_tps=p.get("median_tps"),
            tps=list(p.get("tps") or []),
            leading_indicators=dict(p.get("leading_indicators") or {}),
            certified=certified_of.get(v, False))
    return out


def assert_complete(landscape: Dict[str, GenomeResult], tag: str = "") -> None:
    """landscape が SILO_SPACE 全 8 genome を被覆し、全て certified かを検証。

    replay の前提 (記録済みを配る) が崩れていないかの関所。欠落/未 certify は明示エラー。"""
    expected = {g.canonical() for g in SILO_SPACE.enumerate()}
    got = set(landscape)
    if got != expected:
        raise AssertionError(
            f"landscape ({tag}) が SILO_SPACE と不一致。"
            f"欠落={sorted(expected - got)} 余剰={sorted(got - expected)}")
    uncert = [g for g, r in landscape.items() if not r.certified]
    if uncert:
        raise AssertionError(f"landscape ({tag}) に未 certified genome: {sorted(uncert)} "
                             "(replay は certified 済みのみ配る前提)")


def replay_evaluate(landscape: Dict[str, GenomeResult], genome) -> GenomeResult:
    """記録済み landscape から 1 genome の評価結果を配る (新規 bench を走らせない)。

    genome は Genome (canonical() を持つ) でも canonical 文字列でもよい。landscape に
    無い genome を引いたら明示エラー (replay は記録済みしか配れない = 空間外を黙って評価しない)。"""
    key = genome.canonical() if hasattr(genome, "canonical") else str(genome)
    if key not in landscape:
        raise KeyError(f"genome {key!r} は P2-2 WAL に無い "
                       "(replay は記録済み genome のみ配れる。空間外を評価しようとした)")
    return landscape[key]


def winner_tied_set(landscape: Dict[str, GenomeResult],
                    between_run_cv: float = BETWEEN_RUN_CV) -> set:
    """winner と between-run noise floor 内で区別できない equivalence class (= 連結成分)。

    「最適到達」を単一 genome 一致でなくこの tied set への到達で定義する (reps5 ノイズで
    argmax が揺れる read-heavy の循環を避ける、D14)。winner (median 最大) から出発し、
    既存メンバのいずれかと compare が no-difference な genome を吸収する連結成分。
    tied set が大きいほど到達は容易 = 全戦略に等しく有利 (誘導優位を過大評価しない保守側)。"""
    items = sorted(landscape.values(),
                   key=lambda r: (r.fitness_tps or 0.0), reverse=True)
    if not items:
        return set()
    tied = {items[0].genome}
    changed = True
    while changed:
        changed = False
        for r in items:
            if r.genome in tied:
                continue
            for m in list(tied):
                c = compare(landscape[m].tps, r.tps, noise_cv=between_run_cv)
                if c.verdict == "no-difference":
                    tied.add(r.genome)
                    changed = True
                    break
    return tied


def main(argv) -> int:
    """自己テスト: 3 workload の landscape を読み、ランキング + winner-tied set を表示。

    P2-2 WAL の直接再計算 (手動検証) と一致するかの sanity。新規計測は走らせない。"""
    for tag, _wl in WORKLOADS:
        lscape = load_landscape(tag)
        try:
            assert_complete(lscape, tag)
            complete = "✓ 8 genome / 全 certified"
        except AssertionError as e:
            complete = f"⚠ {e}"
        tied = winner_tied_set(lscape)
        items = sorted(lscape.values(), key=lambda r: (r.fitness_tps or 0), reverse=True)
        win = items[0].fitness_tps or 1.0
        print(f"\n==== {tag}  ({complete}) ====")
        print(f"  winner={genome_label(items[0].flags)}  tied-set(k={len(tied)}, "
              f"floor {BETWEEN_RUN_CV*100:.1f}%)={sorted(genome_label(lscape[g].flags) for g in tied)}")
        for r in items:
            gap = (win - (r.fitness_tps or 0)) / win * 100
            mark = " ★tied" if r.genome in tied else ""
            print(f"    {genome_label(r.flags):9s} {r.fitness_tps:12,.0f}  gap {gap:5.2f}%"
                  f"  cert={r.certified}{mark}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
