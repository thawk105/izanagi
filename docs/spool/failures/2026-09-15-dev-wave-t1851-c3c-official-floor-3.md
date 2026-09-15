---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-t1851-c3c-official-floor
seq: 3
---

## 新規

### {{F:argv-budget-reused-for-diagnostics}}. argv 用の切り詰め予算を診断本文へ流用し、実機で原因の半分を落とした [誤前提] [防壁の射程誤認]

- 事象: official 床値 campaign の condition gate が `preprocess-failed` で止まる原因を取るため、
  拒否本文へ red record の `evidence.detail` を添える実装を入れた。段 5 の初稿は
  `condition_meaning_gate` の argv 用 helper を流用したため、切り詰めが**先頭 500 bytes だけ**を
  残した。実機の走行 (request `999039.nqsv`) で保存された本文は
  `In file included from` の連鎖だけで、**fatal error 行が落ちていた** (original 1057 bytes の
  後半 557 bytes)。原因は判らず、投入を 1 回余分に使った。
- 根本原因: **予算の「意味」が違うものを 1 つの helper で共有した。** argv は先頭に command が
  来るので先頭優先の切り詰めが正しい。コンパイラ診断は末尾に結論 (error 行) が来る。
  byte 上限という形が同じなので流用できると誤前提した。「detail を失わせない」という目的に対して、
  どちらの端を残すかを検討しなかった。
- 恒久対応: {{D:condition-detail-both-ends}} — 診断専用の byte 予算を消費側 module の定数として
  分離し、先頭と末尾の両方を残して中央を省略する。省略 bytes 数と全文 sha256 の印を必須にする。
  予算は観測された診断長への倍率で決め、根拠を comment に書く。
- 再発検知: 登録変異 M5 (末尾を落とす) / M6 (先頭を落とす) / M7 (省略 bytes 数または全文 sha256 の
  印を落とす) を殺す `orchestrator/tests/test_s1_direct_comparison.py` のテスト。実 `ConditionArmRecord`
  を使い依存先を stub しない。予算内に収まる短い本文で切り詰めが起きず全文が残ることを正例にした。
- 実害: 投入 1 回ぶんの計算資源と wall time。台帳消費はゼロ (走行は registry reservation 前に停止)。
  誤った結論を記録に残す前に実機で露出した。

## 再発

### F39

- **再発: 2026-09-15** — official 床値 campaign を 3 回投入したところ、発行された起動証明書の
  `clean_scan_digest` が 3 走行ですべて異なった (`b09b3e0d…` / `0ec84656…` / `41ccc100…`)。
  走行間で repo へ commit を足したためである。**「凍結 bytes を触らなければ安全」ではなく、
  file 集合そのものが digest の preimage に入る**という F39 の性質が、初めて official 走行の
  実測で確認された。本 wave はこの性質を段 1 brief の不変条件に据え、記録では holdout の値を
  逐語で並べず凍結 file への参照で示す運用にした。段 3 の 2 レンズはこの不変条件が
  **十分条件ではない**ことも指摘した — 実装は holdout 値を escape せず regex へ置換するので
  親の逐語 3 表記の検索より受理形が広く、列挙集合も `external/ccbench` の tracked を含む。
  「この書き方だけで clean scan 通過を保証する」とは書かない。
