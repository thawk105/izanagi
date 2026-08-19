---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1379-c05-activation
seq: 3
---

## 再発

### F408

- **再発: 2026-08-19** — `dev-wave-t1379-c05-activation` (T-1379, C05 activation) の
  変異 spec 組成で、`@CANDIDATE_XDIST_GROUP` 付きテスト2件
  (`test_candidate_freeze_matches_contract_and_generation_chain`,
  `test_repository_tip_binds_current_decider_version_without_activation`) の
  `expected_nodes` がどちらの表記でも一致しなかった (T-1355 と同一の2 test、同一の
  collection/実行の representation gap)。同じ `--deselect` workaround で回避した。
  2つの独立 wave での再現により DW-G03 の族一般化条件 (異なる producer/consumer で
  2件) を満たしたため、`_normalize_node` への xdist group suffix 除去の恒久対応を
  次の一手として提案する。
