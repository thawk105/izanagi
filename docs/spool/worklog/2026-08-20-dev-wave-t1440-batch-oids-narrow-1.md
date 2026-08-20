---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1440-batch-oids-narrow
seq: 1
title: '[T-1440] D551と同じ原則を_batch_oidsの残る呼び出し経路へ適用する恒久対応を完了した (narrow漏れ経路は実測で不在と確定、既存テスト拡張で回帰テストを追加、コード+テスト、branch worktree-dev-wave-t1440-batch-oids-narrow、変異matrix = baseline PASSED・新HEAD 1/1 KILLED・旧HEAD 1/1 SURVIVED、MISMATCH 0)'
---

## 本文

- command 引数は「D551 と同じ設計原則を `orchestrator/campaign/s8c_preregistration.py`
  内の `_batch_oids` 残る呼び出し経路へ適用する」ことを求めていたが、段1 brief 実測
  (D551 親コミット時点のコードと T-1362 失敗 tip での再現実験、方法論の独立検証は
  段3 レンズA が実施) により、「narrow 漏れ経路が残っている」という前提自体が誤りと
  判明した。真因は T-1362 の branch が D551 land (2026-08-19 12:51:11) より前の main
  (11:08:54) から分岐していたことであり、単純な rebase 不足だった。
- 段3 の2レンズ (sol/luna) は主実装不要で独立一致したが、回帰テストの実装方針
  (新規関数 vs 既存テスト拡張) で分かれた。段4 裁定はレンズBの既存テスト拡張案を
  採用した (規律5「盛らない」)。
- 段6 敵対レビュー2本の所見 (計2件、うち1件は変異事前登録自体の単一理由性欠如) を
  fix 1本で解消し、焦点再レビューで全所見 closed を確認した。
- 変異 matrix (DW-M08 新旧比較): 新HEAD版で KILLED・旧HEAD版で SURVIVED を実測し、
  新設検査の純増検出力を確認した。旧HEAD版の走行では変異 harness の spec 制約
  (`expected_status: SURVIVED` は `expected_nodes` 空が必須) に1回抵触し、
  使い捨て worktree の `git worktree remove --force` での後片付けを要した。
- 段8 自己改善候補2件を発見した (variant spec の SURVIVED 制約が DW-M08 文面に
  明記されていない、旧HEAD版走行の `mutation_worktree.py --commit` 手順が
  DW-M08/DW-O19 いずれにも明記されていない)。

## 次の一手差分

### 完了

- [T-1440] D551 と同じ原則を `_batch_oids` の残る呼び出し経路へ適用する恒久対応を
  完了した。narrow 漏れ経路は実測で存在しないと確定し、`_assert_rulings_exist` 経路の
  専用回帰テストを既存テスト拡張で追加した (コード+テスト、
  branch worktree-dev-wave-t1440-batch-oids-narrow、変異matrix = baseline PASSED・
  新HEAD 1/1 KILLED・旧HEAD 1/1 SURVIVED (DW-M08新旧比較)・MISMATCH 0)
  remaining: none
  base: 9f8728df4b346b194a40bbcf38a0e2f997f18083e8f9f828ecdcb9328d85bd35
