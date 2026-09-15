## 実装

plan v2 を実装しました。変更は許可された 2 ファイルのみ、追加 265 行です。docs 編集・commit はしていません。

- [writer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2470-impl/orchestrator/campaign/trial_registry.py:2433)：総書込量と inode の両条件を満たす場合だけ撤去し、元例外を再送出。
- [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2470-impl/orchestrator/tests/test_trial_registry.py:8441)：指定の新規 14 nodeid と既存 genesis 負例の強化を追加。既存期待値の変更なし。

現行の「未存在名への作成を受理、既存名を拒否」は維持しました。変更点は、条件を満たす書込失敗の残骸を撤去して再試行可能にすることです。照合と unlink の間の競合窓は裁定どおり残ります。

## 実走結果

すべて自走 harness で確認しました。

| 実走 nodeid 範囲 | 結果 |
|---|---|
| `orchestrator/tests/test_trial_registry.py::*` | **262 passed**、1297.20 秒 |
| `orchestrator/tests/test_plain_runner_coverage.py::*` | 3 passed |
| `orchestrator/tests/test_update_acceptance_duration_ledger.py::*` | 24 passed |
| `orchestrator/tests/test_acceptance_schedule_order.py::*` | 79 passed、警告 1 件 |

指定の新規・強化 nodeid はすべて上記に含まれます。さらに、次の 17 件を焦点走し、一時パス・fixture commit hash が異なる再走でも通過しました。

- `test_attempt_create_only_failure_removes_residue_and_allows_retry[{genesis,classification}-{write,write_no_progress,file_fsync,directory_fsync}]`：8 件
- `test_attempt_create_only_keeps_file_extended_by_another_writer`
- `test_attempt_create_only_keeps_replaced_inode_at_same_name`
- `test_create_only_unlink_failure_preserves_original_error`
- `test_create_only_interrupt_removes_residue_and_allows_retry`
- `test_create_only_success_preserves_bytes_and_fsync_order`
- `test_attempt_registry_classification_rejection_preserves_receipt_bytes`
- `test_attempt_registry_genesis_is_closed_before_first_performance_observation`
- `test_attempt_registry_classification_receipt_is_create_only`
- `test_genesis_cli_rejects_second_creation_without_changing_bytes`

`write_no_progress` は 0 返却で writer が生成する `OSError` の型・本文を確認し、例外注入ケースは cause の同一性を確認しています。

実走範囲の赤は **0 件**。docs 由来として事前除外した finding も 0 件です。通常 runner は `qstat -Q` 失敗により起動前 rc=16 でしたが、上記自走で検証を完了しました。`git diff --check` も通過しています。

## 波及範囲と未実走

直接 caller は `create_attempt_registry_genesis` と `classify_attempt`。所有外の入口は genesis CLI、`p3_autonomous_workload_trial.py:4876`、分類の別名 `classify_attempt_failure` です。

共有 fixture の `_genesis_cli_fixture`・`_attempt_fixture`・`_reserve_attempt` は既存実装を使用し、変更していません。他 module の同名 writer も未変更です。

裁定の consumer 集合で未実走なのは、`orchestrator/tests/` 配下の次の 13 ファイルです。

`test_attempt_registry_core_equivalence.py`、`test_p3_autonomous_workload_trial.py`、`test_reflux_origin_binding.py`、`test_reflux_originless_compatibility.py`、`test_autonomous_trial_completeness.py`、`test_attempt_registry_core_s8b_profile.py`、`test_s8c_preregistration_predicates.py`、`test_s8c_preregistration_core.py`、`test_s8c_preregistration_invariant.py`、`test_holdout_observation.py`、`test_campaign.py`、`test_paper_story_a1_paired.py`、`test_paper_story_a1_job_contract.py`。

## 総括

段 5 の実装・指定テスト・関連メタテストは完了しました。変異走、残りの consumer 走、親の受入全走は未実走であり、今回の結果で代替していません。