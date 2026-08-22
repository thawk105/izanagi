---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-tictoc-cicada-catalog-card-i5-fix
seq: 1
title: entry (814) の I5 誤引用を訂正する (docsのみ、branch worktree-dev-wave-tictoc-cicada-catalog-card-i5-fix)
---

## 本文

- entry (814) (`output/insights/2026-08-21_cicada-selective-precheck-catalog-card.md` §8) が、
  Cicada/Silo 間のデータ構造非互換性を CCBench 著者の I5「異なる実装の混合は深い分析には
  不適切」の具体例として引用していたが、ユーザーが誤りを指摘した。
- I5 の正しい意味: 実装者間 (例: A氏実装のプロトコルBとC氏実装のプロトコルD) の実装技術・
  ワークロードハックの差が、プロトコル間の性能比較を不公平にするという比較妥当性の問題である。
- 本カードの発見 (Cicada の技法が要求する per-tuple counter・MVCC version chain を Silo の
  単一版 `Tidword` が持たない) は、実装者間の技術力差ではなく単純なデータ構造の前提不一致であり、
  I5 が指す論点とは無関係。カード §8 から誤った I5 引用を削除し、訂正注記を付けた。
  結論 (No-Go 判定・技術的根拠) 自体は変わらない。

## 次の一手差分
