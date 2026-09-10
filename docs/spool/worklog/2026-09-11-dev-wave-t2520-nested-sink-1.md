---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2520-nested-sink
seq: 1
title: [T-2520] 入れ子buildの誤分類を修正し、既存検査が見逃した変異を直接回帰で検出した
---

## 本文

- D1936項18の限定修正。独立plan1・相談2・author1・レビュー2の計6走はaccepted。
  追加realなし、固定入力の一律過剰拒否と回帰の検出力不足はrefuted。
  14macroのruntime到達やclosure全般の完全性は主張しないと裁定した。
- 初回main焦点走はrunnerのメモリ上限で未完走、再投入は既存orphan holdで子未起動。
  他所有のholdを変更せず、専用worktreeの計算ノード走で44件成功を得た。
  修正後は47件成功、M1は既存44件でSURVIVED・新集合でexact2node KILLED。
- 起動時に同検査を触ったT-2417 recovery/T-1851 D2のmain統合を確認し、稼働T-2397の変更面も照合。
  外部裁定inboxに本件方針を覆す更新は無かった。実測と逐語は
  `output/insights/2026-09-11/t2520-nested-sink/README.md`。
- 実装anchorは `f5e3315b8` — Fix T-2520 nested build closure input classification。
  provenanceは新規違反なし、既知56件を分離表示した。改善実装・次wave・pushは行わない。
- 段8で自己改善契約を再読し、改善候補なしを専用handoffへ明記した。
- 統合版7544087a3の受入全走は23,071 passed / 68 skipped、child-green。
  受入中のmain更新後、完了項目の同位置挿入だけが競合したため両記録を保持した。
  T2520の完了項目は現行チェックポイントへ移し、同位置への追記競合を避けた。実装bytesは不変。
- 終端でlauncher正常rcにもかかわらずproducer未起動を1度観測し、未起動として再投入した。
  起動確認の明確化候補をhandoffへ追記（原因未確定）。改善実装は行っていない。

## 次の一手差分

### 完了

- [T-2520] D1936項18の局所修正と実sink・既存到達不能正例・変異の新旧比較を完了。
  remaining: none
  base: 781bb20023a3d7843699c6b2921819390e44dcfc3fa98d32ffbc5f60b5dca203
