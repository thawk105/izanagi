## 総括

裁定2の G1・G2・G3 を所有 path 内で修正しました。通常 preview の拒否文言を基点に戻し、G2 のテストでは実体の build context を使うようにしました。静的 10 µs は既存の `run_stock_control` 経路に載せ、driver の `run_campaign` 呼出し箇所は AST 上で2箇所に戻っています。

## 変更 file と行数

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/campaign/p3_s4_loop_policy.py): 34行追加、36行削除
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_p3_s4_loop_policy.py): 1行削除
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_campaign.py): 段5で変更した期待値2箇所を基点の `2` に復元

## 実装した interface

`load_proposal_file(..., preview_auditor=False)` は通常 preview で従来の `{coder}` と拒否文言を維持し、対照 preview で `{coder, auditor}` を受けます。`run_stock_control(..., fixed10=False)` に静的 10 µs の経路を加え、`measure_slot` の `ref-fixed10` から呼びます。CLI と event 名の変更はありません。

## テスト

`py_compile` と `git diff --check` は通過しました。AST で `run_campaign` 呼出し2箇所を確認しました。`python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop_policy.py` は `qstat -Q` の事前確認失敗（rc=16）で止まり、テスト本体は**未実走**です。

## 所有外への波及

`test_p3_exploration_namespace.py::test_driver_ast_supplements_runtime_namespace_gate[p3_s4_loop_policy]` と、`test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` の閉じた inventory に関係します。所有外 file は編集していません。

## 変異の位置

- M4: [p3_s4_loop_policy.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/campaign/p3_s4_loop_policy.py:254) — `test_p3_s4_loop_policy.py::test_machine_origin_can_write_only_after_shared_gate`
- M5: [p3_s4_loop_policy.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/campaign/p3_s4_loop_policy.py:766) — `test_p3_s4_loop_policy.py::test_contrast_unit_rejects_changed_proposal_before_slot_start`

## 未解決・報告して止めたこと

Pegasus dispatch の事前確認が失敗したため、関連テストの成否は未確認です。