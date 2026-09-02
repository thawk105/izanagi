## 変更

[tools/pegasus/b10_backoff_shape_campaign.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-signal-trap-author/tools/pegasus/b10_backoff_shape_campaign.sh:107) は `local` を分割し、signal status の算出前に `number` を代入するよう修正しました。
[orchestrator/tests/test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-signal-trap-author/orchestrator/tests/test_b10_backoff_shape_sweep.py:1762) は production file から handler を一意抽出し、記録引数と status を検証するテストを追加しました。

変更はこの 2 ファイルのみで、commit はしていません。`git diff --check` は rc=0 です。

## テスト実走

対象 nodeid:

`orchestrator/tests/test_b10_backoff_shape_sweep.py::test_pegasus_job_signal_handler_records_failure_and_exits_with_signal_status`

`python3 tools/run_tests.py <nodeid>` は runner rc=16、`child_started=false` でした。`qstat -Q` preflight が失敗し、user cgroup 使用量も最終的に約15.3 GiBで14 GiB ceilingを超えていたため、pytest 自体は起動していません。したがって状態は「実装済み・未実走」です。

修正後にテストと同一の抽出・shell bodyを直接実行した結果は、実行 harness rc=0、shell status=143、記録引数は `["143", "signal", "received TERM"]` でした。

`bash -n` は Pegasus hook が job script を `dispatch-required` として実行前に拒否したため、構文検査も未実走です。

## 壊れた handler の赤確認

production 修正前、新テスト追加後に同一の production 抽出・shell bodyを直接実行しました。

- harness rc=1、内部 shell rc=1
- stderr: `number: unbound variable`
- `failure_args_exists=False`
- 失敗箇所: [assert completed.returncode == 143](/work/1/SFC/tanab/izanagi/.codex/worktrees/b10-signal-trap-author/orchestrator/tests/test_b10_backoff_shape_sweep.py:1790)

ただし、上記の runner infra failure により、pytest nodeidとしての赤は確認できていません。

## 静的波及

grep で確認した参照先は次のとおりです。

- `test_b10_backoff_shape_sweep.py`: output-root helper、binary path policy、official-root env、PBS契約、verify-perf walltime、dry-run staging、新 signal test。
- `test_hooks.py`: `_PEGASUS_EXPECTED_CLASSES` と `_PEGASUS_EXPECTED_ENTRIES` の `dispatch-required` 分類。
- `test_official_perf_closure.py`: performance-bearing file allowlist。
- 共有 fixture、caller、`failure.json` consumerの変更はありません。新テストは既存の `tmp_path` のみを利用します。

## 受理・拒否挙動

phase・workload・PBS environment・`bootstrap_fail` の受理／拒否条件は変更前後で変わりません。`write_failure` の create-only と `failure_written` の一度きり性も変更していません。

signal 時だけ、変更前は TERM 15 が未割り当て変数で rc=1・記録なしでしたが、変更後は `write_failure 143 signal "received TERM"` を1回実行して status 143 で終了します。未変更の trap 引数から、INT/HUPもそれぞれ130/129になります。

## 総括

- 指定された2ファイルだけを変更し、signal handler修正とproduction実体を使う挙動テストを追加しました。
- 壊れた handler は直接実測で rc=1・assertion失敗、修正後は status 143・期待引数を確認しました。
- pytest nodeidはrunner rc=16で子が起動せず、「実装済み・未実走」です。
- 所有外の参照先は上記3 test fileの静的契約に限られ、job scriptの受理・拒否集合は変わりません。