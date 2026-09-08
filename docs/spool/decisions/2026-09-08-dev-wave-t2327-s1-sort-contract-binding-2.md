---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2327-s1-sort-contract-binding
seq: 2
---

## {{D:s1-sort-contract-consumers-forward}}. s1 materializer の sort 契約束縛は、同じ materializer を使う consumer が値を転送するだけで閉じ、stock 同一 bytes の短絡は D1630 の規約のまま据え置く

**決定:** D1548 の sort 軸局所適用を s1 driver へ通すとき、(1) `prepare_cell` は sort_best だけ oracle が attest した
`contract_id` で `source_digest.resolve_evidence(..., sort_oracle_contract_id=).src_token` を確定し、`PreparedCell` に
その ID を持たせる。(2) `run_role`、`s8b_oracle_driver` の evaluate、`s8b_floor_campaign` の evidence 解決と build は、
`PreparedCell.sort_oracle_contract_id` が非 None のときだけ同じ値を既存 keyword へ転送する。(3) 束縛値の出所は
oracle 結果であり、campaign 宣言 (`_search_identity` の同じ定数) との exact 一致は既存の oracle 検査が担う。
新しい gate・定数・producer は足さない。(4) comparator が stock と同一 bytes に materialize される sort_best で
契約を改版しても token が `STOCK` のままになる挙動は、D1630 の binder 規約どおり変えない。

**理由:**
- s1 の束縛だけを入れると、同じ `prepare_cell` を使う s8b oracle driver と floor campaign が契約 ID 無しで
  `pipeline.evaluate` / `build_v2` へ進み、src_token 照合で sort_best が全件 abort する。consumer の転送は
  「gate の新設」ではなく、束縛値を落とさないための整合であり、D1548 が禁じた任意軸への一般化ではない。
- `_require_sort_oracle_contract(cfg)` を s1 から呼ぶ案は、`prepare_cell` に cfg が無く `prepare_cell_fn` seam を
  広げる。oracle 検査 (`oracle.contract_id != ORACLE_CONTRACT_ID` → DriverError) が同じ exact 一致を既に要求している。
- stock 同一 bytes では build 結果も stock binary であり、契約 ID の改版が binary を変えない以上、cache の再利用は
  stale build ではない。分離が要るなら `source_digest._resolved_src_token` (D1630) 側の設計変更であり、
  本 wave の編集面ではない。

**却下した選択肢:**
- s8b 側を旧経路 (契約 ID 無し) のまま残す — s1 の束縛が consumer を壊す。
- `prepare_cell` に束縛の opt-in 引数を足して s8b だけ束縛しない — identity 分断を s8b に残し、seam も広がる。
- stock 短絡より先に契約 ID を束縛する — D1630 の規約変更で、loop 側 producer との不整合を生む。
