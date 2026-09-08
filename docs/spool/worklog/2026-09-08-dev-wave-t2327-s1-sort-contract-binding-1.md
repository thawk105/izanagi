---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2327-s1-sort-contract-binding
seq: 1
title: [T-2327] s1 の sort_best cell を SWO oracle 契約 ID へ束縛し、同じ materializer を使う s8b の consumer 2 本へ転送した (コード + テスト + insight、branch worktree-dev-wave-t2327-s1-sort-contract-binding、変異 baseline PASSED・KILLED 11・SURVIVED 1 (等価変異)・MISMATCH 0)
---

## 本文

- D1548 の sort 軸局所適用を s1 driver へ通した。`s1_direct_comparison.py` は campaign identity に契約 ID、
  sort_best comparator の materialize、SWO oracle 実行を既に持っていたが、src_token の確定 (`source_digest.resolve`) と
  `pipeline.evaluate` に契約 ID を渡していなかった。D1630 の binder (`resolve_evidence(..., sort_oracle_contract_id=)`)
  をそのまま使い、oracle が attest した `contract_id` (実行中 `ORACLE_CONTRACT_ID` との exact 一致を既存検査が要求) で
  sort_best だけ token を束縛し、`run_role` は非 None のときだけ `evaluate` へ同じ ID を渡す。`resolve()` / `src_token()`
  の public seam、`loop.py`、gate の新設はいずれも無し。
- **親の焦点走と静的閉包で consumer の取り残しを 2 件見つけた。** `s8b_oracle_driver.py` は s1 の `prepare_cell` で
  materialize した後 `PreparedCell` を作り直して契約 ID を落とし、`s8b_floor_campaign.py` は契約 ID 無しで
  `resolve_evidence` と `build_v2` へ進む。どちらも `pipeline.evaluate` / `build_v2` の src_token 照合で sort_best が
  全件 abort する形だった (s1 の束縛だけ入れると壊れる)。同じ sort 軸の値を転送するだけの consumer 整合として
  scope 内に入れた ({{D:s1-sort-contract-consumers-forward}})。
- **派生 pin を 1 段見落とした (F39 の再発として記録、実害なし)。** materializer 全体
  sha256 の literal は pin 閉包で拾って更新したが、その literal を含む golden bytes の sha256 は author prompt の
  「他の literal は触らない」で取り残され、親の焦点走 1 回目 (2 赤) で出た。
- 敵対レビュー 3 本 (A: identity/cache 意味論、B: テスト検出力、C: fix 後の焦点再レビュー) の must-fix は A の 1 件のみで、
  「stock 同一 bytes に materialize される sort_best は契約を改版しても token が `STOCK` のまま」という指摘。
  D1630 が binder に定めた規約そのもの (bytes が stock なら binary も stock で、cache の再利用は stale ではない) と
  裁定して実装しない。B は M5/M6 が既存テストでも落ちる冗長 gate であることを指摘し、事前登録の期待を訂正した。
- 変異は 12 件を事前登録し (負 11 + 等価 1)、probe 走で期待 node の完全集合を実測してから計算ノード dispatch で
  本走した。**baseline PASSED、KILLED 11 / SURVIVED 1 (等価変異) / MISMATCH 0 / PARSE_ERROR 0** で期待と完全一致
  (12/12)。本走 1 回目の等価変異 1 件は gen_S の queue 待ち 908 秒で `PARSE_ERROR` (F762、子は未起動) になり、
  DW-M07 の `--resume` で取り直した。逐語・台帳は
  `output/insights/2026-09-08_t2327-s1-sort-contract-binding/`。
- 焦点走 (13 file、計算ノード): 1 回目 3 赤 (派生 pin 2 + consumer test の double 1) → fix1 後 1 赤 (テスト側の
  key 名 `configuration` → `configuration_id`) → fix2 後 1197 緑 / 赤 0。
- **受入は 2 回とも wave の外側の事情と pin で止まった。** attempt 1 は `merge-history-provenance` rc=70 で、
  違反ではなく main が後から足した既知違反台帳の記録 file が wave HEAD に無いための実行不能 (F206 と同型、
  テストは 1 件も走らず)。main を先に取り込んで解いた。attempt 2 は 3 failed / 21,732 passed で、赤 3 件は
  すべて `test_ccbench_spawn_sites.py`。同 file が build sink を **行番号**で pin しており、転送を足して
  4 sink が下へずれたことによる (F39 の 3 例目、production の挙動は正しい)。台帳の位置だけを追随させた。

## 次の一手差分

### 完了

- [T-2327] s1 の sort_best cell を SWO oracle 契約 ID へ束縛し、s8b oracle driver / floor へ転送した。
  remaining: none
  base: e368a163be5b3e991e0ef15f08433d7078348d46ba27b2970b7a77af666fe629
