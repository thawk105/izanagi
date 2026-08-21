---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-tictoc-cicada-catalog-card
seq: 1
title: Stage 7-(i) TicToc/Cicada 最適化カタログカード試作 — Cicada selective precheck は Silo EVOLVE-BLOCK へ No-Go (docsのみ、branch worktree-dev-wave-tictoc-cicada-catalog-card)
---

## 本文

- Stage 7-(i) (T番号未発行、`docs/phase3.md` item7 Group D (i) の一歩目、D32 が定める「カタログ化
  試作 1 枚」) の研究-only wave として、Cicada の commit-streak gated selective precheck
  (`precheckInValidation()`) を Silo の EVOLVE-BLOCK 実編集面 (write_set_ ロック順序 comparator +
  `backoff.hh`) へ着想移植できるかを判定した。判定 = No-Go (per-tuple counter・MVCC version chain
  という前提が Silo の単一 `Tidword` に無い)。コード変更・ベンチ・性能値の実測はなし。
- 段2 codex plan (1本、reasoning=max、read-only) が tictoc/cicada 双方から候補 3 件
  (Cicada selective precheck、TicToc timestamp history、TicToc validation loop fusion) を
  file:line 付きで起草し候補1を推薦。段3 敵対相談 2 レンズ (A=技術正確性/sol、
  B=D32・I5・規律6・scope 遵守/luna、いずれも reasoning=max・read-only) を並列実施した。
  A は所見4件 (refuted 2件 = No-Go 判定を支持、real 2件 = 用語精緻化と TicToc 側の見落とし)、
  B は所見7件全て refuted (問題なし)。No-Go 結論自体は親の一次ソース直接確認 (Silo Tidword、
  read validation、backoff.hh、Cicada precheck/tuple/comparator) を含む三重確認を通じて一貫した。
- レンズAが CCBench 本体のコメント (「両ステップを adaptively omit する」) と実装
  (`partial_sort` は常時実行、閾値判定は内側の version check のみ) の乖離を発見し、親が直接ソースで
  支持した。カタログカード §4 に記録した。
- レンズAが射影外の一次ソース走査から見落とし候補 2 件 (Cicada Early Abort Check、TicToc
  `NO_WAIT_OF_TICTOC` の lock-conflict 最適化) を報告したが、いずれも本カードの No-Go 判定を覆さず、
  scope (1技法限定) の外として次カードの出発点にのみ記録した。
- 素材: Cicada の per-tuple 前提 (連続 commit カウンタ + MVCC version chain) と Silo の単一版
  `Tidword` bitfield は根本的に非互換であり、コード片の直接移植が成立しない具体例になった
  (CCBench 著者の I5 警告「異なる実装の混合は深い分析には不適切」の実例)。
- 一次資料: `output/insights/2026-08-21_cicada-selective-precheck-catalog-card.md`、
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-tictoc-cicada-catalog-card/`
  (stage2-plan-output.md、stage3-lensA-output.md、stage3-lensB-output.md)。

## 次の一手差分
