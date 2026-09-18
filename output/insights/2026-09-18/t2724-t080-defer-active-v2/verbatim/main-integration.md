## 総括

所有2ファイルへの合成完了。未commitです。実走検証は未完了です。

## 変更

- `conftest.py`：receipt consumer 8関数/8node、invalid seamの両resource reader登録を反映。
- `test_real_repo_serialization.py`：独立golden、T080接続20node検査、receipt関連検査を反映。
- T1259の30関数登録・独立golden・全件suffix検査を保持。

## 静的照合

- 差分は指定パッチと行番号・blob ID以外で完全一致。
- process-memo集合34関数（T1259 30＋既存4）とreceipt集合8関数を個別に照合。
- 親木のreceipt consumerは8関数/8nodeで一致。T080対象14関数の存在を確認。
- `git diff --check`、`check_codex_agents.py`、`check_docs.py`成功。

## 未実走/期待赤

関連meta-testを`tools/run_tests.py`経由で投入しましたが、`qstat -Q` preflight失敗でrc=16、`child_started=false`。実走nodeはありません。

この木ではT2724未導入によるinventory・20node接続・invalid seam収集の期待赤があり得ます。親で合成後、T1259全51caseとT080新旧ケース、関連meta-testの実走が必要です。

## 波及

所有外の確認対象：

- consumer：`test_t1259_qsub_env_delivery_probe.py`、`test_s8b_oracle_driver.py`、`test_s8b_binding_driftguards.py`
- 共有fixture：`_clean_detached_source_snapshot_template`、`_clean_detached_source_snapshot`、ratified memo、`real_repo_receipt_memo`
- caller/meta-test：`test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`、`test_run_tests_task_run.py`のreceipt prewarm検査

production・docs・timeout・skip・holdは変更していません。