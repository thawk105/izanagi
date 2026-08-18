---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1348-c09-c10-consumer
seq: 3
---

## 新規

### {{F:masked-dedicated-negative-control}}. ある gate のために書いた専用の負例が、隣接 gate と正例に先取りされて発火しない [テスト代表性]

- 事象: 事前登録した 11 変異のうち 2 件で、その gate のために新設した負例テストが
  変異注入後も緑のままだった。M09 (WAL 被覆検査の削除) では
  `..._rejects_an_unclassified_wal_record` が発火せず `[build_records]` の別負例が捕え、
  M10 (`artifact_refs` の全件再読を 1 件目へ縮小) では `[artifact_refs]` の負例が発火せず
  **正例 4 本が赤になって**検出した。いずれも SURVIVED ではないため、
  検出力そのものは失われていない。
- 根本原因: 負例 fixture が、狙った gate より手前で発火する隣接 gate の入力も同時に壊していた。
  M09 は layer3 側の射影も動かしてしまい、被覆検査の手前で別の完全一致検査が落ちた。
  M10 は再読を縮小すると下流が使う検証済み bytes が欠け、負例より先に正例が壊れた。
  段 6 の敵対レビューが「別ゲートに隠れる」と事前に指摘していたが、
  fix はその 2 件について単一理由化を達成できていなかった。
- 恒久対応: 変異の期待 node は書き手の意図ではなく**実測 node を権威**とする。
  probe 走で実測してから再登録する運用を守る (`DW-M08`)。
  専用負例が発火しなかった変異は、KILLED であっても
  「その負例は当該 gate の単独証拠にならない」と台帳へ明記する。
- 再発検知: probe 走の期待 node と実測 node の差分。
  期待した node が実測集合に**含まれない**変異は、KILLED でも検出力の注記対象とする。
