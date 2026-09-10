---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2528-role-input
seq: 1
title: [T-2528] role入力例を実射影の5fieldへ訂正した
---

## 本文

- D1936項23・25に従う限定訂正。起動時の対象role文書の所有重複は確認されず、受理集合・runtime blockedを維持した。
- 親がoriginless baselineのtrigger-gating側7箇所を落とし、単独走1FAILで検出。既存比較を維持した固定hash追随で解消（F433）。fix子の見出し欠落はF43として未受理にし、独立focus監査で現物を検収した。
- 工数はCodex author 1・fix 1・focus 1（gpt-6-astra/medium）。実装子のpytestはqstat preflightで未実走。親の修正後関連検査は941 passed/4 skipped、M1は1/1 KILLED・期待node完全一致。docs/codex_agents検査はrc0。全史provenanceは新規違反なし。
- 詳細と変異原記録は `output/insights/2026-09-11/t2528-role-input/README.md`。最終受入とlandは記録後の専用receiptへ束縛する。
- スキル改善候補は専用handoffへ記録し、改善実装・次wave・pushは行わない。

## 次の一手差分

### 完了

- [T-2528] D1936項23のrole入力例訂正と既存pin閉包の追随を完了。
  remaining: none
  base: d2d1128112eee6f46bf99723c6b74b2ab0d7de76d0ed119d2003b61d0da71fd0
