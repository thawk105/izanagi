---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t1396-c04-reject-started
seq: 1
---

## 再発

### F42

- **再発: 2026-09-08** — [T-1396] wave で発生。**新規 file ではなく既存 file へ足した 1 テスト**が
  同型を起こした。実 repo を読む負例へ `@pytest.mark.xdist_group("s8c-predicate-snapshot")` を付けた
  ところ、`orchestrator/tests/test_real_repo_serialization.py` の group golden に未登録のまま
  受入全走まで露出せず、`test_real_repo_group_collection_exactly_matches_canonical_nodes` と
  `test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`
  の 2 件が赤になった (21568 collected / 2 failed)。親の焦点走は変更した production module 名で
  consumer を引く形 (`DW-O26`) だったため、**mark の名前で引かねば当たらない登録簿**を落とした。
  過去の再発が新設 file と自走 harness / duration ledger を対象にしていたのに対し、今回の入口は
  **mark の付与**である。
  さらに単純な登録追加では閉じなかった。group の golden
  (`_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN`) と、その group の共有 fixture の consumer 集合
  (`_REAL_REPO_FIXTURE_ACCESS_GOLDEN` の `current_commit_snapshot[module]`) は**同一の
  frozenset を共有**しており、group にだけ足すと fixture consumer 側の実測一致検査が破れる。
  fixture を消費しない group 所属 node は、集合を分離しない限り登録できない。今回は負例を
  共有 fixture の consumer へ変える形で両集合を一致させて閉じた (受入 21598 collected /
  21530 passed / 赤 0)。
