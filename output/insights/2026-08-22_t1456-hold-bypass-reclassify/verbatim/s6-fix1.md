変更完了。対象は指定の2ファイルのみで、4 entry の `reason` を更新しました。

検証結果:

- `python3 tools/run_tests.py orchestrator/tests/test_hold_inventory.py`
  - rc=16
  - Pegasus `qstat -Q preflight` infrastructure failure
  - child 未起動、実走 nodeid なし
  - 実装済み・未実走
- `hold_inventory.py --format json`
  - 4 entryすべてに `T-930 closed this bypass` を確認
  - D360、`__wrapped__`、guard再束縛の記述も保持
- source/golden-copy の reason 完全一致: `true`
- `git diff --check`: 成功
- commit: なし

## 総括

`reason` のみを source とテスト期待値へ同期しました。テストは dispatch infrastructure failure により未実走です。