---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t189-reasoning-allowlist
seq: 3
---

## 新規

### {{F:positive-mutation-node-enumeration}}. 過剰拒否変異の期待 node を新テストだけから導き、正当な追加赤を MISMATCH で受け取った [テスト代表性] [手順漏れ]

- 事象: [T-189] wave の変異本走で、受理集合から `low` を消す過剰拒否変異 (V9) が `MISMATCH` に
  なった。親が事前登録した期待 node は本 wave が追加した正例 2 本と exact-vocabulary meta-test の
  3 件だけだったが、実際には
  `test_dev_waves_cli.py::test_export_is_create_only_and_contains_only_sanitized_wal_view` も
  赤になった。同テストは profile の `effort="low"` で実 supervisor wave を走らせるため、
  worker spec / child argv 層に到達して**正当に**赤くなる。変異は期待方向へ効いており、
  誤っていたのは登録側である
- 根本原因: 過剰拒否 (positive) 変異の期待 node を「この wave が追加したテスト」から導いた。
  受理集合から値を消す変異は、**runner scope 内でその値を消費する既存テスト全部**を赤にする。
  新設テストの列挙は必要条件でしかない
- 見落としの経路: 段 6 の焦点再レビューはこの型を認識しており、
  「`test_dev_waves_integration.py` 全体を runner に含めてはならない」と警告した。しかし同じ理由で
  赤くなる `test_dev_waves_cli.py` の wave 実走テストは挙げなかった。**敵対レビューによる列挙も
  完全ではない**
- 恒久対応: (a) 機械防壁は既存で有効 — `tools/mutation_harness.py` の
  `_validate_registrations` と期待 node 突き合わせが `MISMATCH` を rc≠0 で返し、本件を実際に捕えた。
  黙って KILLED にはならない。(b) 手順側は `DW-M01` の事前登録契約へ「受理集合を縮小する変異は、
  削除する値のリテラルを runner scope 全体へ機械検索してから期待 node を確定する」を足す。
  `docs/dev-wave/` は本 wave の no-touch 対象のため、条文追加は
  {{T:devwave-m01-shrink-mutation-enumeration}} が所有する
- 再発検知: 変異台帳の `MISMATCH` で actual ⊋ expected かつ追加 node が当該値を消費する既存テスト
  なら、この型である。一次資料は
  `output/insights/2026-08-03_t189-reasoning-effort-allowlist/mutation-ledger.json` (初回、V9 MISMATCH) と
  同 `mutation-ledger-v9-erratum.json` (補正後、KILLED)
- 近縁: F60 (期待 node が対象 gate を実行していない)、F33 (期待 node と記録 node の形式不一致)
