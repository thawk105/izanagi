実装は完了しましたが、実走は環境側で阻止され、未検証です。

変更は次の 2 ファイルです。

- [tools/check_branch_landed.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2706-landed-timeout/tools/check_branch_landed.py:38)：根拠コメント 2 行、定数を `30.0` に変更。他の製品コードは byte 比較で不変を確認。
- [orchestrator/tests/test_check_branch_landed.py:1009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2706-landed-timeout/orchestrator/tests/test_check_branch_landed.py:1009)：import と以下の 6 node を追加。既存関数・期待値の AST は不変。

追加 node（すべて同 test file 配下）：

- `test_command_timeout_default_is_bounded_and_bound`
- `test_git_run_real_command_timeout_is_truncated`
- `test_assess_real_log_timeout_is_indeterminate_not_a_verdict[True-proof-path-log]`
- `test_assess_real_log_timeout_is_indeterminate_not_a_verdict[True-any-path-find-object]`
- `test_assess_real_log_timeout_is_indeterminate_not_a_verdict[False-proof-path-log]`
- `test_assess_real_log_timeout_is_indeterminate_not_a_verdict[False-any-path-find-object]`

実走結果：

- 指定の直接 pytest：PreToolUse hook が拒否。
- runner 経由の対象全件・collection・関連 meta-test 3 ファイル：いずれも `qstat -Q preflight rc=1`、runner rc=16、`child_started=false`。
- **実走 node 0、緑 0、赤 0（未起動）**。4 node 合計 10 秒未満も未確認。
- 構文検査・既存コード不変検査・`git diff --check` は成功。

静的な波及確認：

- 所有外 caller は `tools/check_branch_rescue.py`。subprocess 起動した判定器に新定数が適用されますが、rescue 自身の予算設定は不変です。
- consumer は `orchestrator/tests/test_check_branch_rescue.py`。未変更・未実走です。
- `_history_fixture`、`_assert_exact_unit`、既存 repo 構築 helper を再利用。共有 fixture の追加・変更なし。
- 調査範囲では対象固有の test 名 allowlist・行番号 pin・file 数 pin は見つかりませんでした。`acceptance_duration_ledger.json` に既存 node の時間記録がありますが未変更です。
- runner が dispatch receipt を 3 件自動生成しました。docs 編集・commit・git add はしていません。

変異の検出見込み（静的判断）：

| 変異 | 赤になる見込みの node |
|---|---|
| M1 | 実 command timeout 単体、assess の delayed=True 2 node |
| M2 | 同上（outcome / proof phase） |
| M3 | default の bounded-and-bound |
| M4 | default の bounded-and-bound |
| M5 | assess の delayed=True 2 node、既存 global timeout |
| M6 | **新規 node では検出不可**。実 timeout は `_regular_decision` 到達前に最上位へ伝播するため、登録見直し対象 |
| M7 | 既存 `test_history_scan_limit_is_indeterminate_and_measured` |

## 総括

指定 2 ファイルの実装を完了しました。
製品の変更は定数とコメントのみ、既存テストは不変です。
新規 6 node を追加し、静的検査は成功しました。
テストは hook／dispatch 障害で未起動のため、実走検証が残っています。