---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1376-receipt-ledger-scope
seq: 1
title: [T-1376] COMMIT receipt の一回限り保証を ledger 単位へ限定した (docs のみ、branch worktree-dev-wave-t1376-receipt-ledger-scope)
---

## 本文

- D729 を再起票せず、既存裁定を authority として D525、2026-08-17 の T-1286 裁定文、
  entry 660 の見出し・T-1286 実績を近接訂正した。保証は同じ ledger の消費済み集合内での
  single-use に限り、別 layout の ledger を横断する一意性は主張しない。
- 同一 lock bytes を持つ 2 layout に、同じ verifier 発行 live receipt object と同じ
  operation・variant・workload・payload・sink・lock context を渡した逐次 probe では、各 WAL の
  初回が同じ receipt ID で受理され、同一 WAL の 2 回目だけ `already consumed by this WAL` で
  拒否された。これは cross-layout 一意性の反例と当該逐次ケースの二重消費拒否であり、一般的な
  exactly-once 配送の実証とは扱わない。
- 実装、schema、外部 registry、正しさ gate、receipt の受理条件、テストは変更していない。
  `python3 tools/run_tests.py orchestrator/tests/test_t1286_commit_receipt.py -q` は 18 passed。
- 段2 plan は land 済み D729 の重複起票を提案したため採用せず、段3の2レンズで差し戻した。
  段6レビュー2本は訂正文を受理し、実測の全束縛同一性、repo 全体検索、T-1520 非重複の証跡を
  handoff へ補った。焦点再レビューは全所見 `closed`、`partial` / `regressed` 0、blocker なし。

## 次の一手差分

### 完了

- [T-1376] D729 の ledger 単位裁定を既存の裁定文・台帳記述へ反映し、cross-layout 一意性の
  過大主張を除いた。外部状態、実装、gate、受理条件の変更はない。
  remaining: none
  base: 86a4931e2c30d7ff6a563441ac8909c0e8dd9c1ce2194c349ee6befb9d770dec
