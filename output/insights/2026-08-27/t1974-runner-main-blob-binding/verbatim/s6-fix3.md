実装済み・未実走です。pytest は実走していません。

変更行:

- [test_dev_wave_land.py:2027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_dev_wave_land.py:2027) から 2057、[同:2093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_dev_wave_land.py:2093): 1 本目の canonical K=1 申告と環境設定。
- [test_dev_wave_land.py:2144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_dev_wave_land.py:2144) から 2174、[同:2217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_dev_wave_land.py:2217): 2 本目の同設定。

変更前後の検査差:

- `test_real_waiter_receipt_is_consumed_by_real_land_end_to_end`: 実 waiter の受領証を実 land が消費する検査を維持しつつ、runner の正規申告を成功条件に追加しました。
- `test_real_child_green_waiter_receipt_passes_real_land_end_to_end`: `child-green` 受領証が実 land を通る検査を維持しつつ、runner の正規申告を成功条件に追加しました。

同型 node はありません。`acceptance_launcher.py` の実コピーと `dev_wave_wait.py` の実起動 path を `rg` で照合し、該当各 2 箇所が上記 2 node のみであることを確認しました。

外側 test と生成 runner 2 本の構文、`git diff --check`、禁止結合文字なしを静的確認済みです。rc 0、受領証成功、land 成功の既存期待は変更していません。git add、commit も実行していません。

## 総括

対象 2 node に K=1 と canonical 申告を追加し、既存の成功検出力を維持しました。  
実装済み・未実走です。