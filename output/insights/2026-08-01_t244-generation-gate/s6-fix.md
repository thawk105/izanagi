## 総括

受理集合は、generation 予算について exact built-in `int` の `1` のみ受理します。`2..10` は未承認、範囲外・`bool`・非 `int`・`int` サブクラスは契約違反として拒否します。freshness は `loop_state.json` 不在を受理し、正常な既存 state と壊れた checkpoint を拒否します。lock・WAL のみの残骸や並行 start race は今回も対象外です。

### (a) 実装した fix

- FIX-1: 型検査・範囲検査・承認上限検査を3段に分離し、exact `int` に限定。`__add__` を改変したサブクラス負例を追加。
- FIX-2: production と同じ campaign layout に正規保存した state の拒否、空 layout の受理を monkeypatch なしで追加。既存2本は provider 順序 poison test と明記。
- FIX-3: checkpoint loader の例外を cause 付き `AutonomousTrialError` に正規化。壊れた JSON と `delta_pct` leak を固定。
- FIX-4: CLI 予算テストを `claude-headless` build 経路へ変更。
- FIX-5: invalid planner の直接呼出回数を計測し、1回を assert。production の `break` は不変。

### (b) 編集した file:line

- [p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:184): generation validator と freshness 例外正規化（184–206行）。
- [test_p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:71): 実 layout helper、型・layout・checkpoint・planner回数・CLI経路テスト（71–425、486–508行）。

境界値 `1` / `2` は引き続き literal です。編集は指定2ファイルのみで、docs・role・adapter・commitには触れていません。

### (c) 新設・更新したテスト nodeid

- `test_generation_budget_rejects_int_subclass_with_overridden_add`
- `test_invalid_role_is_single_attempt_and_stops_cell`
- `test_run_workload_rejects_existing_campaign_state`
- `test_run_workload_accepts_fresh_campaign_state`
- `test_run_workload_rejects_actual_existing_campaign_state`
- `test_run_workload_accepts_actual_fresh_campaign_layout`
- `test_freshness_wraps_malformed_json_with_cause`
- `test_freshness_wraps_delta_pct_leak_with_cause`
- `test_main_rejects_unapproved_budget_before_build_preparation`

### (d) 検査結果

- 対象ファイル全走を指定コマンドで試行:
  `python3 tools/run_tests.py orchestrator/tests/test_p3_autonomous_workload_trial.py -rf`
  - `rc=16`
  - `qstat -Q preflight rc=1`
  - dispatch 前に失敗したため、実行済み nodeid はありません。テスト緑は主張しません。
- `git diff --check`: rc=0
- 対象2ファイルの `python3 -m py_compile`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 親 docs 未 land による事前予想赤は対象テスト単体にはありませんでした。docs の意味追随は段7の親作業です。

### (e) fix-brief との食い違い

なし。A-02 の lock・reservation・原子的排他は実装していません。

### (f) 所有外への波及可能性

- 静的検索では、対象 module/test 外の Python caller、共有 fixture、consumer test は見つかりませんでした。
- 外部 programmatic callerが `int` サブクラスを渡していた場合は新たに拒否されます。CLI の値は argparse が built-in `int` を生成するため影響しません。
- 壊れた checkpoint に対する terminal report の `fatal_error.type` は、素の decode/schema例外から `AutonomousTrialError` へ安定化します。
- 親の変異 harness は V9/V10a/V12/V13/P4 の新しい anchor・期待 nodeへ更新が必要です。