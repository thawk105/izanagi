---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t472-canonical-predicate-consumers
seq: 3
---

## 新規

### {{F:mutation-preregistration-false-kill}}. 変異事前登録に「赤くはなるが受理集合は変わらない」偽 kill を登録しかけた [恒真ゲート]

- 事象: 段 4 で登録した共有層変異 (M5) の期待 node が
  `test_p3_s4_loop.py::test_trigger_quarantine_rejects_noncanonical_text_before_structure_inspection`
  だけだった。このテストは存在しない path を渡すため、membership を消すと後続の
  ファイル読み込みが `FileNotFoundError` になって赤くなる。**node は赤くなるが、
  非正準入力は依然 fail-closed のままで受理集合は変わっていない。**
  同じ登録には他に 3 件の誤りがあった — 期待 node の不足 (2 件)、
  「検査を省く」形の変異では正例テストが赤にならないこと (1 件)。
- 根本原因: 親が事前登録を「gate を消せばそれを検査するテストが赤くなる」という
  推論だけで書き、**赤の理由が受理集合の変化かどうかをテスト本体まで読んで確認しなかった**。
  `DW-M01` が要求する「無効化時の赤理由が一つに絞れること」の確認を、
  node 名の対応づけで代用していた。
- 恒久対応: `DW-M01` / `DW-M03` の既存契約 (事前登録時に単一理由性をコードで確認する、
  診断文字列だけの赤を kill にしない) を、段 6 の敵対レビュー 1 本のレンズへ明示的に入れる。
  本 wave では段 6 レンズ B が走らせる前に 4 件すべてを検出し、是正後は
  `tools/mutation_harness.py` の node 集合完全一致検査が 7/7 で通った。
  是正しなければ harness は全て `MISMATCH` として fail-closed していた
  (機械防壁は最終的に効くが、無駄な 1 巡を生む)。
- 再発検知: `tools/mutation_harness.py` の期待 node 集合完全一致検査 (`MISMATCH` で停止)。
  受理集合が変わらない変異は、事前登録の段階で診断感度 pin として別枠に分類する。
