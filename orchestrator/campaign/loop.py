# -*- coding: utf-8 -*-
"""campaign ループ — 同一性確定 → リカバリ → 未評価 genome を評価 (orchestrator-design.md)。

1 campaign = (spec, 探索 config) 固定 (D13)。起動時に:
  1. campaign-id を入力から再計算 (状態を保存せず再現)
  2. campaign.lock を確定 (初回) or 照合 (再開、IdentityMismatch で関所)
  3. WAL をリプレイし terminal (commit/abort) な variant をスキップ (D, A リカバリ)
  4. 残りの genome を評価パイプラインに通す

Phase 1 は探索 = 列挙 (全 genome)。Phase 2 で LLM 誘導の選択/変異が loop の上に乗る。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from . import ident, source_digest, wal
from .layout import campaign_layout
from .model import CampaignConfig, Genome, STAGE_ABORT, STAGE_BUILD_START
from .pipeline import (EvalResult, PerfConfig, S2_TAG, SEARCH_CONFIG_VERIFY_KEY,
                       VERIFY_LEGACY_PLUS_S2, evaluate, s2_correctness_workload,
                       variant_id)


@dataclass
class CampaignSummary:
    campaign_id: str
    layout_root: str
    total: int = 0
    skipped: int = 0           # リカバリでスキップ (既に terminal)
    identity_skipped: int = 0  # identity 確定不能かつ stock id が terminal 済みで今 run 未評価
    evaluated: int = 0
    committed: int = 0
    aborted: int = 0
    results: List[EvalResult] = field(default_factory=list)


def run_campaign(cfg: CampaignConfig, genomes: Sequence[Genome],
                 perf: PerfConfig, env_tag: str, clocks_per_us: int,
                 numactl: Optional[Sequence[str]] = None,
                 do_bench: bool = True, output_root: str = "",
                 log=print, ccbench_dir: str = "", cache_root: str = "") -> CampaignSummary:
    """`ccbench_dir`/`cache_root` (段5 git worktree 隔離): pipeline.evaluate と同じ実行時
    引数の素通し。省略時は共有固定パス既定 (既存動作と完全互換)。campaign-id には含めない
    (numactl/do_bench と同じ扱い、pipeline.evaluate の docstring 参照)。"""
    cid = ident.campaign_id(cfg)
    layout = campaign_layout(str(cid), output_root).ensure()

    # D36 決定4-1: search_config[SEARCH_CONFIG_VERIFY_KEY]=="legacy+s2" で S2 構成
    # (t48 フルロード規模、データパス被覆担当) を legacy (検出力担当) に追加する。
    # search_config はここで既に campaign_id のハッシュ対象 (D13) なので、S2 on/off
    # の切り替えは自動的に別 campaign になり WAL terminal skip の汚染を構造的に防ぐ。
    extra_correctness = None
    if cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2:
        extra_correctness = [(S2_TAG, s2_correctness_workload())]

    # 同一性: 初回は lock を書く、再開は照合 (黙ってマージしない関所, D13)
    pre = ident.canonical_preimage(cfg)
    existing = wal.read_lock(layout)
    if existing is not None:
        ident.verify_against_lock(cfg, existing)     # 不一致なら IdentityMismatch
    else:
        wal.write_lock(layout, pre)
    log(f"[campaign] {cid}  ({layout.root})")

    # リカバリ: terminal な variant はスキップ
    states = wal.replay(layout)
    terminal = wal.terminal_variants(states)
    # identity-error abort は transient infra 失敗 (g++ 一時不在 / git 一時失敗等) でも起きうる。
    # genome-intrinsic な失敗 (verifier-red / build-error / eval-exception) と違い環境修復で解消し
    # うるので permanent skip にせず再評価する (D25: terminal-abort が transient を誤分類して
    # stock baseline を silently drop する穴を塞ぐ)。永続エラーなら再 resolve で同じ identity-error
    # に倒れ abort 記録するのでクラッシュループにはならない (commit 済みは除外して再評価しない)。
    # 判定は last_terminal (最後の commit/abort) 基準 — last (最終レコード全般) 基準だと
    # 「identity-error abort → 修復後の再評価が BUILD_START を書いた直後にクラッシュ」で
    # 判定から漏れ、aborted の粘着により permanent skip が復活する (洗練検査 2026-07-02 HIGH)。
    retryable = {v for v, st in states.items()
                 if st.aborted and not st.committed and st.last_terminal is not None
                 and st.last_terminal.payload.get("reason") == "identity-error"}
    terminal = terminal - retryable
    if terminal:
        log(f"[campaign] リカバリ: {len(terminal)} variant は評価済み → スキップ")
    if retryable:
        log(f"[campaign] リカバリ: {len(retryable)} variant は identity-error (transient) → 再評価")

    s = CampaignSummary(campaign_id=str(cid), layout_root=layout.root,
                        total=len(genomes))
    done = set(terminal)        # terminal を seed して 1 run 内の二重評価も防ぐ (U1)
    first_bench = True          # settle は最初の実 bench の前に 1 回だけ (calibrator 契約)
    for g in genomes:
        # identity (D23/D24): skip/abort キーを src_token id に揃える (coder variant の
        # リカバリ冪等性 D・例外 abort の整合 A)。pipeline.evaluate と同じ確定窓口
        # (source_digest.resolve) を使い、確定済み src_token を渡して id 確定点を単一化する。
        # 確定不能は stock id で fails-closed abort (best-effort skip を持ち込まない, 規律2)。
        try:
            src_tok = source_digest.resolve(g, cfg.ccbench_commit, ccbench_dir)
        except RuntimeError as e:
            v0 = variant_id(g)              # identity 不明ゆえ canonical のみの stock id
            if v0 in done:
                # stock id が terminal 済み → この run では評価も abort 記録もできない。
                # 沈黙させず可視化する (規律3): 永久 drop ではない (次 run で resolve が
                # 直れば正しい src_token id で評価される) が、summary 上「リカバリ skip」
                # と区別が付かないと成果物からの欠落が読めない。
                s.skipped += 1
                s.identity_skipped += 1
                log(f"[campaign] {g.canonical()} identity 確定不能かつ stock id は "
                    f"terminal 済み → この run はスキップ (環境修復後の次 run で再評価): {e}")
                continue
            done.add(v0)
            wal.log(layout, v0, STAGE_BUILD_START, env_tag, {"genome": g.canonical()})
            wal.log(layout, v0, STAGE_ABORT, env_tag,
                    {"reason": "identity-error", "error": str(e)})
            log(f"[campaign] {v0} identity 確定不能 → abort 隔離して継続: {e}")
            s.results.append(EvalResult(genome=g, variant=v0, certified=False,
                                        aborted=True,
                                        notes=[f"source_digest 確定不能 → reject ({e})"]))
            s.evaluated += 1
            s.aborted += 1
            continue
        v = variant_id(g, src_tok)
        if v in done:
            s.skipped += 1
            continue
        done.add(v)
        log(f"[campaign] evaluate {g.canonical()}")
        try:
            r = evaluate(g, layout, env_tag, cfg.ccbench_commit, perf,
                         clocks_per_us, numactl=numactl, do_bench=do_bench,
                         do_settle=(do_bench and first_bench),
                         src_token=src_tok, extra_correctness=extra_correctness,
                         log=log, ccbench_dir=ccbench_dir, cache_root=cache_root)
        except Exception as e:   # noqa: BLE001  この variant 固有の失敗を隔離する
            # 想定外の例外も abort として terminal 化し、再起動で同地点の再クラッシュを
            # 防ぐ (overnight 耐性 / A)。KeyboardInterrupt 等は Exception 外なので通す。
            wal.log(layout, v, STAGE_ABORT, env_tag,
                    {"reason": f"eval-exception: {type(e).__name__}: {e}"})
            log(f"[campaign] {v} 評価中に例外 → abort 隔離して継続: {e}")
            r = EvalResult(genome=g, variant=v, certified=False, aborted=True,
                           notes=[f"評価中の例外 → reject ({e})"])
        s.results.append(r)
        s.evaluated += 1
        if r.aborted:
            s.aborted += 1
        elif r.certified:
            s.committed += 1
            if do_bench and r.fitness_tps is not None:
                first_bench = False     # 実 bench が 1 回成功 → 以降 settle 不要
    log(f"[campaign] done: {s.committed} committed / {s.aborted} aborted / "
        f"{s.skipped} skipped (of {s.total})")
    return s
