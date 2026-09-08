## 変更

- [s8c_budget.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2234-budget-vacuity/orchestrator/campaign/s8c_budget.py:113)
  - arm・holdout 上限の正値検査、arm 間の厳密対称検査、holdout 合計と総上限の厳密一致検査を追加。
  - [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2234-budget-vacuity/orchestrator/campaign/s8c_budget.py:530) で全 cell の予約値が正の場合だけ `held` になる判定を追加。
- [test_s8c_budget.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2234-budget-vacuity/orchestrator/tests/test_s8c_budget.py:27)
  - `_limits`、`_reserve` と指定 fixture を更新。
  - [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2234-budget-vacuity/orchestrator/tests/test_s8c_budget.py:259) にゼロ予約、非正上限、厳密一致、正常系、旧 ledger 読み戻しの計 10 test case を追加。
- [test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2234-budget-vacuity/orchestrator/tests/test_p3_autonomous_workload_trial.py:9100)
  - 指定 fixture の holdout 上限を `H1=1.0, H2=1.0` に変更。
- `git status --short` は上記 3 ファイルだけ。docs、契約 JSON、ledger、git 状態は変更していない。

## 実走

- `PYTHONPATH=. python3 orchestrator/tests/test_s8c_budget.py`
  - ファイル内全 20 node: `20 passed in 1.79s`
- `PYTHONPATH=. python3 orchestrator/tests/test_p3_autonomous_workload_trial.py`
  - ファイル内全 266 node: `266 passed in 216.04s`
- `PYTEST_ADDOPTS='-k "test_prepare_s8c_budget_inputs_accepts_matching_ratified_holdout_ids or test_prepare_s8c_budget_inputs_rejects_mismatched_holdout_id_set"' PYTHONPATH=. python3 orchestrator/tests/test_p3_autonomous_workload_trial.py`
  - 指定 2 node: `2 passed, 264 deselected`
- `git diff --check -- <変更3ファイル>`
  - rc=0
- 最終状態の実走に failed/error はなく、報告対象となる非意図的な赤はない。

## 変異の単一理由性

各変異を実際に適用し、次の selector を `PYTEST_ADDOPTS=-k` へ渡して自走 harness を実行後、直ちに復元した。各回とも指定した 1 nodeだけが `failed`、残り 19 node は `deselected` だった。

|変異|指定 node|観測した単一の赤理由|
|---|---|---|
|M1|`test_all_zero_cell_reservations_are_insufficient`|`state` が `held`|
|M2|`test_one_zero_cell_reservation_makes_whole_matrix_insufficient`|3 層確認後、`state` が `held`|
|M3|`test_all_zero_cell_reservations_are_insufficient`|`state` が `held`|
|M4|`test_budget_limits_reject_nonpositive_caps[arm]`|`BudgetError` が発生しない|
|M5|`test_budget_limits_reject_nonpositive_caps[holdout]`|`BudgetError` が発生しない|
|M6|`test_budget_limits_reject_asymmetric_arm_caps[gross]`|`BudgetError` が発生しない|
|M7|`test_budget_limits_reject_asymmetric_arm_caps[ulp]`|`BudgetError` が発生しない|
|M8|`test_budget_limits_reject_holdout_caps_not_summing_to_total[gross]`|`BudgetError` が発生しない|
|M9|`test_budget_limits_reject_holdout_caps_not_summing_to_total[ulp]`|`BudgetError` が発生しない|
|M10|`test_each_budget_layer_has_a_numeric_insufficient_witness[total]`|`state` が `held`|
|M11|`test_each_budget_layer_has_a_numeric_insufficient_witness[arm]`|`state` が `held`|
|M12|`test_each_budget_layer_has_a_numeric_insufficient_witness[holdout]`|`state` が `held`|

M1-M12 の入力を前後または内側で別検査が拒否する事象はなかった。過剰拒否の正例、coverage 例、指定された p3 正負例も最終 harness で緑になっている。

## 波及の静的列挙

- `s8c_budget.py` 内:
  - 新規予約は `reserve_all_cells -> _check_limit_state`。
  - ledger 読み戻しは `_ledger_from_raw -> BudgetLimits` と `_check_limit_state` を通るため、旧来の「ゼロ予約かつ held」ledger は `BudgetError("reservation の limit state が不一致")` になる。
  - `settle` と既存 ledger の冪等予約も同じ読み戻し経路の影響を受ける。
- 所有外の実 caller は [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2234-budget-vacuity/orchestrator/campaign/p3_autonomous_workload_trial.py:2082) のみ。
  - `_prepare_s8c_budget_inputs` が `BudgetLimits` を受け、`run_trial` が予約後の `insufficient` を全 cell の対称停止へ投影する。
  - 現在の `_load_s8c_schedule_authority` は無条件停止のため、production schedule は未結線のまま。
- `s8c_preregistration_evidence.py` は `BudgetLimits` の field と `_check_limit_state` の実在・呼び出し辺を AST 検査する consumer。名称、field、`reserve_all_cells` からの辺は維持した。
- `test_s8c_preregistration_invariant.py` は C06 path・entrypoint pin、`test_s8c_preregistration_predicates.py` は real-module AST consumerと独立した decoy source、`test_real_repo_serialization.py` はその fixture の間接 consumer。いずれも編集していない。
- repo-wide の Python 検索では、以上の外に実 `BudgetLimits` constructor または実 `_check_limit_state` caller はなかった。

## 総括

- 段 4 裁定 §3 のプラン v2 を許可された 3 ファイルだけへ実装した。
- 最終実走は budget 20/20、workload trial 266/266、指定 p3 node 2/2 passed。
- M1-M12 は全件、登録された単一理由で指定テストに殺された。
- プラン v2 の未実装指示はない。
- §2 で明示的に scope 外とされた極小正値 regime と `ReservationCell` field 正規化は変更していない。