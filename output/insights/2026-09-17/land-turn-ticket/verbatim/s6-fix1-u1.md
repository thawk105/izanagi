## 所見対応表 (closed / partial / regressed)

**pytest 未実走のため、closed は申告しません。** 表の nodeid はすべて `orchestrator/tests/test_dev_wave_land.py::` 配下です。

| 所見・test | 判定 | 対応 |
|---|---|---|
| A `test_land_runner_entry_shape_is_permanent_rejection[main-blob-tip-missing]` | partial | runner 照合を lock 内へ戻した。未実走 |
| A 同 `[main-blob-tip-tree]` | partial | 同上 |
| A 同 `[main-tree-tip-blob]` | partial | 同上 |
| A `test_land_runner_path_absence_is_permanent_rejection` | partial | 既存の permanent rejection 経路へ戻した。未実走 |
| A `test_land_child_green_runner_path_absence_is_permanent_rejection` | partial | 同上 |
| A `test_land_rejects_tip_runner_digest_instead_of_tested_main_digest` | partial | main digest 照合を lock 内へ移動。未実走 |
| A `test_land_accepts_child_green_tip_runner_change_with_main_digest` | partial | 登録前の runner lookup 重複を除去。未実走 |
| A `test_provenance_checker_missing_and_symlink_components_are_rejected_clean` | partial | **未修正。登録前検証と fixture の不整合が残る** |
| A `test_d987_rejects_final_runner_change_before_provenance_rc16` | partial | 余分な runner lookup 2 回を除去。未実走 |
| B `test_cumulative_wait_budget_arithmetic_uses_production_timeouts` | partial | 二層予算と turn deadline による切詰めの確認を追加。未実走 |
| B/C `test_merge_child_inherits_lock_fd_if_helper_is_killed` | partial | 3600 秒期待へ変更し、子の完了待ちを finally に移動。未実走 |
| C `test_successful_fold_rollback_remains_held_fail_closed` | partial | 実登録・grant・common flock を持つ setup を追加。未実走 |
| C `test_fold_rollback_failure_reason_reports_preserved_state` | partial | 同上 |
| C `test_fold_rollback_failure_reason_omits_non_regular_state_directory` | partial | 同上 |
| C `test_fold_rollback_failure_reason_omits_non_regular_state_symlink` | partial | 同上 |
| D `test_provenance_checker_infrastructure_rc_is_retryable_and_retains` | partial | 既存 rc 分類を早期終端と共用。未実走 |
| D `test_provenance_checker_signal_returncode_is_retryable_and_retains` | partial | 同上 |

ログから確認できた原因は、依頼文の推測と次の点で異なります。

- SHA 列は **reflog ではなく `_runner_tree_entry` の lookup 履歴**でした。
- rollback 3 本は、票なし拒否により `update-ref` の failure injection へ到達していません。
- `Directory not empty: 'refs'` は merge 子のテストで、180 秒期待の assertion 失敗後に発生しています。
- 3600 対 180 の失敗は、確認したログでは同じ merge 子の node が通常表示と抜粋に重複しています。

## 変更の要約 (関数・行)

[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/tools/dev_wave_land.py)

| 行・関数 | 変更 |
|---|---|
| 970 `_verify_acceptance_static` | runner の lookup・shape・digest 照合を移動。固定 waiter の検証は維持 |
| 1178 `_verify_acceptance_locked_authority` | runner 照合を lock 内で実施 |
| 1207 `_verify_acceptance_receipt` | 同じ receipt bytes を static／locked の両検証へ渡す |
| 3605 `_reject_provenance_returncode` | violation rc のみ非 retryable、それ以外の非ゼロは retryable とする共通分類 |
| 3622 `_verify_provenance_receipt` | 上記分類を使用 |
| 4641 `_run_outside_land_lock` | 再取得を待たない即終端を維持し、上記分類を使用 |
| 5587 `land` | 登録前の permanent receipt 拒否に `release_safe=True` を付与 |

seq 処理は既存 `_finish_land_turn` の retryable 判定へ連動します。mutation 前の所有確認は省略していません。

未修正の checker テストは、全ケースで `make_acceptance_receipt=False`、ancestor-symlink ケースでは `tools` 全体を削除しています。現 fixture のままでは、登録前の receipt／waiter 検証より先に provenance の rc=29 を期待しています。**検証を迂回する変更や期待値変更は行わず、この不整合を残して報告します。**

所有外の `acceptance_shards.py`、`check_docs.py` の helper path 契約、`dev_wave_wait.py`、`test_run_tests_shards.py` は未変更です。共有 `_Repo` fixture も今回変更していません。consumer tests の実走確認は残っています。

## 変更した test と理由

[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/orchestrator/tests/test_dev_wave_land.py)

- **3527 `_granted_land_turn`**：実票の登録・grant・common flock 取得を行う helper を追加。
- **4311 `test_cumulative_wait_budget_arithmetic_uses_production_timeouts`**：既存 assertion を維持し、180 秒消費後の3600 秒期限、および残り60秒で取得枠を切る確認と docstring を追加。
- **7976 `test_merge_child_inherits_lock_fd_if_helper_is_killed`**：B の許可に従い、時間期待を `_LAND_TURN_WAIT_SECONDS` に変更。fixture cleanup 前の子の完了待ちを finally に移動。
- **6979 `_fold_main_locked_with_failed_ref_rollback`**：上表の rollback failure 3 node に granted ticket setup を追加。
- **9484 `test_successful_fold_rollback_remains_held_fail_closed`**：同じ setup を追加。

**今回、既存期待値を変更したのは B の時間期待だけです。** C の結果 assertion は維持しました。

## 変異 anchor 表 (更新)

行番号は `tools/dev_wave_land.py`。変異実走・KILLED 判定は未実施です。

| ID | anchor |
|---|---|
| M0 | 2627 `_land_lock_now` |
| M1 | 5615 `land` の `_wait_land_turn` |
| M2 | 2916 `_register_land_turn` の既存 seq 継承 |
| M3 | 2790 `_turn_live` |
| M4a | 6218 ff 前 `_land_turn_mutating` |
| M4b | 5145 apply 前 `_land_turn_mutating` |
| M4c | 5316 shape B の `before_mutation` 内所有確認。mark／finalize 前から呼出し |
| M5 | 2854 `_turn_select`、3011 `_observe_dead_land_turn` |
| M6a/b | 4641 `_run_outside_land_lock`、3128 `_acquire_land_lock_until_turn` |
| M7a/b | 5720／6004 fingerprint 比較 |
| M8 | 1734 protected 外 child の `continue` |
| M9 | 3200 `_verify_land_lock_binding` の自 wave inode 比較 |
| M10 | U2 所有。位置未確認 |
| M11 | 5587 登録前 `_verify_acceptance_static` |
| M12 | 3007 `_finish_land_turn` の同一 registry 更新内引渡し |
| M13 | 4651–4652 非ゼロ provenance の即終端・rc 分類 |

## 実走結果

`tools/run_tests.py` 経由で次を試行しました。

1. `orchestrator/tests/test_dev_wave_land.py -q`
2. 同ファイルと `test_plain_runner_coverage.py`、`test_pytest_collection_config.py`、`test_flaky_test_holds_contract.py`

**両方とも `qstat -Q preflight rc=1`、runner rc=16、`child_started=false`。pytest は開始されていません。**

成功した検査：

- 両編集ファイルの構文検査
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- `git diff --check`

変更対象は指定の2ファイルだけです。commit は作成していません。

## 総括

runner 検証分割、provenance 分類、直接 fold 呼出しの setup、二層予算の修正を実装しました。**実装済み・未実走です。**

checker 欠落テストの fixture と登録前検証の不整合が1件残っています。全件 closed・受入可能とは申告しません。
