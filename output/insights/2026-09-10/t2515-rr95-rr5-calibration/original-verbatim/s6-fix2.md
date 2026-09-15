修正は完了し、commit は作成していません。

- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-author/tools/pegasus/certify_calibration.sh:395): 既存の interpreter 選定ブロックを内容不変で前倒しし、条件関門を `"$CALIBRATE_PYTHON"` で起動するよう修正。
- [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-author/orchestrator/tests/test_pegasus_calibration_workload.py:427): smoke check、選定順序、fail-closed、argv 先頭を静的に固定。M8 は argv の完全一致検査で KILLED になります。
- 定義順は `TMPDIR` → `ATTEMPT_DIR` → `write_failure` → interpreter 選定 → 条件関門呼び出しです。移動ブロックの参照は自己定義変数と定義済み `write_failure` のみです。
- `CALIBRATE_PATH` の代入位置と最終式は不変です。条件関門の timeout、macro、use-class、呼び出し位置も変更していません。
- 所有外への静的波及は、全 protocol で interpreter 不在時の失敗が build 前へ早まることだけです。`submit_certify.sh` の既存変更には触れていません。

検査結果:

- 変更前・変更後 `bash -n`: PASS
- `git diff --check`: PASS
- nodeid 実走: runner が `qstat -Q` preflight で rc=16、`child_started=false` のため、以下は**実装済み・未実走**です。
  - `test_condition_gate_uses_smoke_checked_interpreter_selected_before_call`
  - `test_calibration_shell_scripts_parse`
  - `test_job_rechecks_the_submission_workload_and_records_it`

## 総括

- smoke 済み Python 3.10 を条件関門にも使用し、関門自体の意味論は維持しました。
- 静的検査で選定順序・fail-closed・M8 の検出力を固定しました。
- `bash -n` は前後とも成功しましたが、nodeid は dispatch 基盤障害により未実走です。
- 親では M8 と、rr95／rr5 が実機条件関門を通過して accepted calibration を生成することを確認してください。