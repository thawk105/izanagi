実装は完了し、指定された2ファイル以外は変更していません。pytest は Pegasus の認証障害により未実走です。

## 総括

(a) 実装内容

- 現行の `1..10` 契約を維持しつつ、承認上限 `1` を3入口で強制しました。
- bool・非 int・絶対範囲外を先に拒否し、続いて未承認の `2..10` を拒否します。
- campaign state の freshness gate を最初の provider 呼び出し前に追加しました。
- CLI 既定値を literal `1` に変更し、AST テストで固定しました。
- V1〜V12・P1〜P3を狙う負例・正例を追加しました。

(b) 編集した file:line

- [p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:90)
  - 定数: 90–91
  - validator/freshness helper: 184–202
  - `_run_workload()`: 643、658
  - `run_trial()`: 883
  - CLI default/main gate: 1040、1051
- [test_p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:71)
  - generation/AST テスト: 71–112
  - role-invalid 更新: 176–201
  - programmatic/freshness テスト: 204–292
  - CLI テスト: 353–390

(c) 新設・更新した nodeid

新設:

- `test_generation_budget_boundary_at_ratified_launch`
- `test_generation_budget_rejects_bool`
- `test_generation_budget_rejects_zero_and_non_int[0]`
- `test_generation_budget_rejects_zero_and_non_int[1.0]`
- `test_cli_default_is_literal_one_by_ast`
- `test_run_trial_rejects_unapproved_budget_before_artifact_creation`
- `test_run_workload_direct_call_rejects_unapproved_budget`
- `test_run_workload_rejects_existing_campaign_state`
- `test_run_workload_accepts_fresh_campaign_state`
- `test_main_rejects_unapproved_budget_before_build_preparation`

更新:

- `test_invalid_role_is_single_attempt_and_stops_cell`
- `test_main_default_generation_budget_is_one`（旧 fixture no-build accept test を改名・強化）

新規テストファイルはなく、nodeid を制約する meta-test は grep 上ありませんでした。

(d) 検査結果

- `py_compile`: 2ファイル成功、失敗0
- `git diff --check`: 成功
- 対象 pytest: 実行 nodeid 0、pass 0、fail 0
- `python3 tools/run_tests.py orchestrator/tests/test_p3_autonomous_workload_trial.py -rf` で計算ノード dispatch を試みましたが、`qstat -Q preflight rc=1`／`Unknown user-id (uid: 31609)` で pytest 起動前に停止しました。
- `pegasus02` 上での直接 pytest はリポジトリ規律により禁止されているため実行していません。親による計算ノード実走が必要です。
- 親 docs 未 land に起因する想定赤は、この対象テスト範囲ではありません。

(e) 裁定文書との食い違い

あり。裁定 §3.6 の「新規8本＋既存2本更新」と、§4で要求される個別 nodeid をすべて満たす場合の本数が一致しません。詳細な V1〜V12・P1〜P3 を優先し、新規9関数（parametrize 後10ケース）＋既存2本更新としました。それ以外の食い違いはありません。

(f) 所有外への波及可能性

- Python 全体を grep した範囲では、所有外ファイルから `run_trial`、`_run_workload`、当該 `main` を直接呼ぶ consumer test はありません。
- CLI を外部運用から呼ぶ場合、flag 省略は `1`、明示 `2..10` は build準備前拒否へ変わります。
- 外部の programmatic callerや直接 `_run_workload()` callerも `2..10` を利用できなくなります。
- 既存 campaign checkpoint がある build運転は、run-root が別でも provider 呼び出し前に拒否されます。
- 共有 fixtureでは既存3本のCLI正例が既定値 `1` を間接固定し、role-invalid fixtureは上限を3へ monkeypatchして従来の停止検出力を維持します。