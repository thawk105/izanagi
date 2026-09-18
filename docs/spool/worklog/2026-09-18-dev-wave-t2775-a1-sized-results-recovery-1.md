---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2775-a1-sized-results-recovery
seq: 1
title: A-1 sized results稿と図9の中断を回収し、着地bundle全欠落の検査漏れとREADMEの個別扱いを処置した (台帳ID未起票、entry1653の系譜、branch dev-wave-t2775-a1-sized-results-recovery)
---

## 本文

- ユーザーは旧未commit差分とimpl tip `1c991c0cc`の回収、F-MF1/A-S1処置、図生成・変異・独立レビュー・main landを指定した。
  formal化・A-1要件充足へ昇格せず、追加のgate・一般化・改善実装・次waveは行わない。清掃は成果保全と非稼働確認後に許可済み。
- 旧親PID1544193の生存を検出し、ユーザーの明示許可後に停止した。SIGTERM後に同一sessionが再出現したため、
  正規stopでsessionを終端した。旧差分はpatch/archiveで保全し、着手時main `b2037abfa`基点へ回収した。
- `de28c4853` — 旧author履歴3commitの回収。`fd7506c74` — F-MF1・最終図・実値hash・phase記録の統合anchor。
- 旧焦点レビューのclosed10/partial1＋F-MF1から、隔離authorの局所修正と親のA-S1説明を経て、
  最終独立レビューはclosed13/partial0/regressed0・GO。最重要点は全欠落skipの除去と、稿からの検証記録参照の完結である。
  数値・図・caption・hashは独立に照合され、既存leaf・policy・事前登録・既存図のbytesは変更していない。
- 単独28 passed/skip0、関連4file 111 passed。変異はM0 SURVIVED、M1〜M13 KILLED、期待node完全集合14/14一致。
  初回投入はwalltime形式で実行前拒否。次走はharness完走後の共有tree照合でwrapper rc125となり、原因は断定しなかった。
  同anchor/specの独立clone再走6435.nqsvはwrapper rc0、共有照合・撤去とも成功した。検査を除外・緩和していない。
- 一次資料・裁定・逐語・変異ledgerは `output/insights/2026-09-18/t2775-a1-sized-results-draft/README.md`。
  旧worklog下書きの完了先書きは採用せず、F1再発の元記録と近接事象を保持した。workerは旧6＋回収3の9本。
- 受入はこの記録を含む最終tipに正規waiterで投入し、結果の正本を外部receiptとland応答に置く。
  自己改善は専用handoffの「dev-wave 改善候補」への記録だけとし、実装・次waveを追加しない。

## 次の一手差分
