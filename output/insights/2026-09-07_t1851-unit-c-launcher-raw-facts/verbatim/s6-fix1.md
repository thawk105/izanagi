在庫検査へ launcher を登録しました。

- perf file 登録を理由コメント付きで追加
- `use_perf_from_receipt` の AST 実測 count `1` を surface `A` へ登録
- AST 正規化で実測した 2 guard をそのまま登録
- commit、docs 編集なし
- `git diff --check` 成功

## 総括

- 変更: [test_official_perf_closure.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix1/orchestrator/tests/test_official_perf_closure.py:60) `+15/-0`
- 実走: 同ファイルの自走 harness、全 `test_*` 7 node
- 結果: `7 passed, 0 failed`
- 変異検査: `test_outer_perf_file_mutations_are_not_tautologies`、`test_closure_inventory_mutations_are_not_tautologies` ともに passed
- 所有外への波及: なし。launcher、launcher test、production、docs は未変更
- commit: なし