## 合成監査結果

両親の変更はすべて生存しており、消失・取り違え・意図しない二重化はありません。

| 変更項目 | 現在版 | 判定 |
|---|---:|---|
| main: `paper_story_a1_paired.py` sink 定義 | `7103` | 生存 |
| main: 上記 sink の golden | `7103` | 生存 |
| wave: certify deferred entry | owner・reason・`2486` | 生存 |
| wave: performance/diagnostic deferred entry | owner・reason・`2831` | 生存 |
| wave: deferred ledger golden | 2 entry とも一致 | 生存 |
| wave: reason literal 検査 | 2 reason とも一致 | 生存 |
| wave: s1 sink 数 golden | `proven-unreachable: 28` | 生存 |
| wave: s8b sink 数 golden | `covered: 32` | 生存 |

## 両親接触ファイル

指定された両 diff を確認しました。tip 間 diff の単純交差には wave 固有差分も現れるため、merge-base `61bc6ac694679e511c03b3b51058426e435efae0` から各親への変更集合も交差しました。

結果は以下の 2 files です。

- `docs/README.md`
- [orchestrator/tests/test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_ccbench_spawn_sites.py)

docs を除く実装面の両親接触は、指定された 1 file だけです。

## 変更

変更不要でした。ファイル編集および `git add` は行っていません。

対象ファイルの index と作業ツリーは同一 hash `a24df855e…` で、unstaged 差分はありません。HEAD は `8bfa6d110`、main は `8c07ded74` のままです。

## 実走テスト

- Nodeid selection: `orchestrator/tests/test_ccbench_spawn_sites.py`
  - 結果: `44 passed in 82.13s`
  - scheduler: `serial`
  - 関連 nodeid:
    - `::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`
    - `::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`

- Nodeid selection: `orchestrator/tests/test_paper_story_a1_paired.py`
  - 結果: `179 passed in 71.61s`
  - scheduler: `serial`

## 総括

main の `7103` 更新と wave の deferred gate ledger・golden は正しく合成されています。欠陥はなく、修正不要です。