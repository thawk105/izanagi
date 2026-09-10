FIX-A の実装を所有範囲内で完了しました。docs・所有外ファイル・commit には触れていません。非 Pegasus (`OTHER`) の挙動変更もありません。

## 総括

| ID | 状態 | 対応 |
|---|---|---|
| FA-1 | closed | immediate で構造化 Request ID を確認後、`qstat rc=0` でも ID field が消えたら END。fake scheduler で 1 poll・10秒以内に子 rc を返すことを確認 |
| FA-2 | closed | `Staging`/`STG`→QUE、`Exiting`/`Post-running`/`EXT`→END。未知状態の overall timeout も固定 |
| FA-3 | closed | `site_policy.py` に future annotations を追加。変更 production 3 module を静的検査 |
| FA-4 | closed | compute job が submission dir へ ID・hostname 束縛 marker を書き、親が検証。release handshake なし |
| FA-5 | closed | Request ID 一致と Started/Ended/Elapse の連言へ変更。`MemoryError` 等の偽陽性を拒否 |
| FA-6 | closed | preferred/fallback receipt の双方が保存不能なら、子 rc=0 でも infra rc=16 |
| FA-7 | closed | queue wait 起点を qsub 復帰時刻へ変更。RUN 未観測時は終端時刻による上界と `observed=false` を記録 |
| FA-8 | closed | qsub rc=0 直後に active 化。parse 失敗時は一意な job name/submission dir から ID を探索して qdel |
| FA-9 | closed | immediate qstat 非ゼロは3回再試行し、失敗だけではラッチしない。poll 中の瞬断も継続 |
| FA-10 | closed | 投入、request ID、状態遷移、収集、receipt 保存を `flush=True` で出力 |
| FA-11 | closed | M5 を probe＋`_job_run()` 両層同時変異へ再照準。期待赤 node をdocstringに事前登録 |
| FA-12 | closed | 生成 job script を実行し、最終 child env を観測する M7 両層検査を追加。期待赤 nodeを事前登録 |
| FA-13 | closed | dispatch 免除集合をテスト側の literal 9要素と production 定数で照合 |
| FA-14 | closed | 恒真な `queue_wait_included_in_parent_duration` を削除し、実時刻関係のテストへ置換 |

主な変更先は [dispatch_compute.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fa/tools/pegasus/dispatch_compute.py:117)、[site_policy.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fa/orchestrator/campaign/site_policy.py:1) です。

実行した範囲:

- `test_site_policy.py` 全 node: 16 passed
- `test_pegasus_dispatch_compute.py` 全 node: 38 passed
- `test_run_tests_nproc.py` 全 node: 16 passed
- `test_run_tests_preflight.py` 全 node: 100 passed
- `test_run_tests_task_run.py` 全 node: 47 passed
- 合計: 217 passed
- 所有8ファイルの `py_compile`: rc=0
- `check_codex_agents.py`: rc=0
- `check_docs.py`: rc=0
- `git diff --check`: rc=0

両層変異の期待赤 node:

- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_m5_dual_layer_interpreter_rejection_changes_acceptance_only_together`
- `orchestrator/tests/test_run_tests_task_run.py::test_m7_dual_layer_job_script_and_child_environment_reject_task_run_state`

未達・親実施事項:

- 実 qsub、計算ノード全走、`-n16` 対照、実機 FA-1 再dogfoodは未実施
- mutation matrix 本走と `test_plain_runner_coverage.py` は未実施
- build・ベンチ・`tools/run_tests.py` は実行していない
- commit は作成していない

所有外への波及可能性:

- caller: `tools/run_tests.py`
- site policy consumer: `hooks/guard_bash.py`、`buildcache.py`、coverage 4 module
- consumer tests: `test_hooks.py`、`test_build_site_gate.py`
- meta-test: `test_plain_runner_coverage.py`
- receipt の恒真 field 削除と marker/timing field追加について、repository内に別 consumerは見つかりませんでした。親の実機 receipt 解析は再確認が必要です。