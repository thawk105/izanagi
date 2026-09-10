## 総括

FA-15 は **closed（実機再受入は親担当）** です。

- [`dispatch_compute.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fa/tools/pegasus/dispatch_compute.py:241)
  - `_job_name()` を単一導出元にし、PBS script、qsub、receipt、ログ候補で共有。
  - `<job-name>.o/e<ID>` を第一候補に追加。
  - `dispatch.sh.o/e<ID>` は後方互換として維持。
  - ID非束縛の汎用候補を除外し、別 request のログを拾わない構造に変更。
- [`test_pegasus_dispatch_compute.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fa/orchestrator/tests/test_pegasus_dispatch_compute.py:302)
  - job-name 形のみで収集成功。
  - script名形のみでも収集成功。
  - 別 request ID は不採用。

現行実装での期待赤確認:

- `...::test_fa15_job_name_logs_match_job_script_and_are_collected`
- `result/log/accounting-grace-expired` により `rc=16`
- 結果: `1 failed, 2 passed`

実装後の実行範囲:

- 上記FA-15の3 node: `3 passed`
- `orchestrator/tests/test_pegasus_dispatch_compute.py` 全 node: `41 passed`
- 所有2ファイルの `py_compile`: rc=0
- `git diff --check`: rc=0
- 実 qsub、全suite、build、commit、docs編集は未実施。

追加変異:

- **M15:** `_log_candidates()` から PBS job-name 形候補を削除。
- 期待赤 node:
  `orchestrator/tests/test_pegasus_dispatch_compute.py::test_fa15_job_name_logs_match_job_script_and_are_collected`

所有外への波及可能性:

- caller: `tools/run_tests.py`
- 実環境: NQSVが生成するjob-name形ログと親dispatcher receipt
- receipt schemaおよび公開関数の引数変更はなし。
- ID非束縛だった `scheduler.o/e`・`stdout.log`・`stderr.log` の受理は要件どおり廃止。リポジトリ内に本dispatcherの当該候補を直接利用するconsumerは見つかりませんでした。