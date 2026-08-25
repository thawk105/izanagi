---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1135-prereg-blockers
seq: 1
---

## 再発

### F136

- **再発: 2026-08-26** — docs-only (spool fragment 3 file) の wave の受入 1 回目で
  12 failed / 16547 passed / 60 skipped になった。11 件は `test_s8b_floor_campaign.py` の
  `_real_output_snapshot()` 系で junit 差分は `first extra item: ('dir', 'task-runs/reports')`、
  12 件目は `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`
  で、いずれも同日 6 例目と逐語一致する。帰属は台帳の 3 点で否定した — (1) 差分は
  `docs/spool/` 配下の新規 3 file だけで実装面を 1 つも触らない、(2) 落ちた 2 file の単独走は
  571 passed / 8 skipped で緑、(3) junit 差分は実装ではなく `output/` の dir 増加を指す。
  **DW-O18 に従い受入を 1 回だけ再走したところ 1 failed / 16558 passed / 60 skipped となり、
  11 件は消えて t080 の 1 件だけが再赤になった。** 再赤の junit 差分は
  `runs/pytest-launcher-failures` の mtime 変化 (1787679360 → 1787680223) で、
  別 helper `_t080_output_snapshot()` が検出したものである。単独 node の再走は
  1 passed / 11.83 秒で緑。**新しいのは、同一 tree・同一操作で 11 件が消えて 1 件が残った点**で、
  この族の赤が決定的でなく shard の実行順序に依存することを示す。DW-O18 の規定どおり、
  F136 を証拠に当該 node を `orchestrator/tests/flaky_test_holds.py` へ登録した
  (Codex role=author)。恒久対応は受入基盤の所有 wave に委ね、解除条件は
  {{T:t080-output-snapshot-shard-race}} に置いた。

### F474

- **再発: 2026-08-26** — 向きが逆の同型。親は「`EVIDENCE_UNDEFINED` を区別する production
  consumer は存在しない」を、その literal を全 production file へ grep して 0 件と測り、
  段 2 の plan もこの前提の上に版 bump 不要を組み立てた。実際には gate レポートが
  `PredicateStatus` の enum を総なめして status count を出しており、literal を 1 度も書かない
  ため grep に掛からなかった。段 3 のレンズ B が参照関係から発見した。F474 が「値を複製する
  consumer」を探せと定めたのに対し、本件は「値を一度も綴らず enum ごと畳み込む consumer」で
  あり、単一の綴りによる grep はどちら向きにも閉包にならない。不在を主張するときは、
  値を綴る箇所と綴らない箇所 (enum 反復・総なめ・動的解決) の両方を型から引く。
