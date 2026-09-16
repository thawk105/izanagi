---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t304-throughput-rename
seq: 3
---

## 新規

### {{F:mutation-collect-error-yields-no-node}}. import を壊す変異は collect error になり、node 抽出が 0 件で PARSE_ERROR になる [手順漏れ]

- 事象: 2026-09-16、[T-304] wave の変異 probe。`orchestrator/codex_roles/review_ledger.py` の
  `SOURCE_FILE_SHA256["planner-v4"]` を旧値へ戻す変異が、2 度続けて `PARSE_ERROR` (観測 node 0 件) で
  終わった。1 度目は kill 集合 153 / 214 node の中継上限が疑われたが、対象を designated gate 4 本へ
  絞って kill 集合を 1〜3 node にしても同じだった。**2 走ぶん (約 20 分) を誤った原因仮説に使った。**
- 根本原因: この変異は `orchestrator/codex_roles/spec.py` の `load_role_specs()` を **module import 時**に
  `RoleSpecError` で落とす。`orchestrator/tests/test_codex_agents.py` は
  `tools/check_codex_agents.py` を module 級で exec するため、pytest の collect 段階で 48 件の
  `when=collect` error になる。`DW-M08` の node 抽出は `FAILED` 行から `<file>::<test>` を取る規約なので、
  **nodeid が file 級しかない collect error からは 1 件も取れない。**
- 誤った結果は出ていない: `DW-M08` の「rc≠0 で 0 件は fail-closed 停止」が働き、harness は
  `PARSE_ERROR` を返して後続を止めた。**防壁は破れておらず、破れたのは原因の読みである。**
- 恒久対応: `docs/dev-wave/mutation.md` `DW-M07` の fail-closed 規約 (`KILLED`期待で node 空の spec は
  起動前に中止、probe は全件 `SURVIVED` 登録) が誤った kill の記録を機械的に塞ぐ。本エントリが足すのは
  **再照準の型**である — 同型に当たったら、同じ pin 閉包を import を壊さない別 file
  (生成 adapter が埋め込む source sha256 等) で突く形へ変える。本 wave はこの形で 5/5 KILLED に
  到達した (`output/insights/2026-09-16/t304-throughput-rename/README.md` の erratum 節)。
  **この型を `DW-M07` の本文へ収容できなかった理由も記録する** — 同節は単節予算 1000 bytes に
  飽和しており、`--out`/`--attempt-out` に `--spec` を足す 9 bytes の事実訂正を入れるだけで
  超過したため、意味を変えない縮約で余白を作って事実訂正だけを収容した。
- 再発検知: 変異 probe が `PARSE_ERROR` を返したら中継上限と即断せず、job stdout の
  `when=collect` 行数を数える。0 件でなければ本型である。
