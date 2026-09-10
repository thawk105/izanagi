## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| must-fix 1 | partial（実装済み・未実走） | 正例・負例とも、`index()` より前に `-o` / `-e` の明示 assert を追加 |
| must-fix 2 | partial（実装済み・未実走） | 正例に `assert expected_root.is_dir()` を追加 |

変更箇所は [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t583-author/orchestrator/tests/test_pegasus_calibration_workload.py:237) のみです。既存期待値は変更せず、`submit_certify.sh` はこの fix 段では編集していません。

## テスト実走

次の2 nodeidを `tools/run_tests.py` 経由で焦点走行しました。

- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submit_dry_run_passes_scheduler_file_paths_to_qsub`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submit_dry_run_keeps_scheduler_output_outside_the_repository`

実行範囲は上記2件ですが、dispatch の `qstat -Q` preflight が rc=1、ランナーが rc=16となり、`child_started=false` のため実際に走った nodeid は0件です。直接 pytest には迂回していません。静的検査では Python AST parse と `git diff --check` が成功しました。

## 受理・拒否の含意

受理: `-o` / `-e` が存在し、導出された repo 外 directory が作成されている場合に契約を満たし、通る正例は `test_submit_dry_run_passes_scheduler_file_paths_to_qsub` の fixture 配置です。  
拒否: option を削除すれば値抽出前の assert が失敗し、`mkdir -p` を削除すれば `expected_root.is_dir()` が失敗します。

## 静的波及

- 所有外 caller: production APIや呼出し側の変更はありません。
- 共有 fixture: 2テストが共有する `_run_submit_dry_run_in_clean_fixture` は未変更です。
- consumer test: 波及対象は上記の正例・負例2件だけです。
- script、docs、CLI、gate、既存期待値、Git staging/commitには変更ありません。

## 総括

指定テストファイルだけに5個の assertを追加しました。  
must-fix 1、2とも実装済みですが、dispatch障害により未実走なので状態はpartialです。  
焦点2 nodeidは子テスト開始前にrc=16で停止しました。  
AST parseと差分検査は成功しています。