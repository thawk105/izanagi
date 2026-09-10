実装済み・未実走です。指定検査は dispatch preflight で停止し、pytest は起動されませんでした。

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

## 総括

- 変更 field:
  - `inside_process_state` / `outside_process_state`: `normal-exit`、`timed-out`、`signal-exit`、`unexpected-exit` 等の終了状況
  - `inside_process_detail` / `outside_process_detail`: return code
  - `inside_payload_state` / `outside_payload_state`: sentinel の有無・内容だけを表し、不在・解析不能は `missing`
- 編集ファイル:
  - `tools/pegasus/probes/t316_sandbox_backend_probe.py`
  - `orchestrator/tests/test_t316_sandbox_probe.py`
- 対象 nodeid:
  - `orchestrator/tests/test_t316_sandbox_probe.py::test_runner_seam_distinguishes_bwrap_setup_failure_from_payload_denial`
  - 指定ファイル全体は pytest 未起動のため passed 0 / failed 0、dispatch infrastructure failure `rc=16`
- 静的検査:
  - 両編集ファイルの AST parse: passed
  - `git diff --check`: passed
- G1/G2:
  - `inside_blocked` は denied sentinel と正常終了の両方が成立した場合だけ真になる
  - timeout・signal・想定外 rc は明示的に `inconclusive` へ落ちる
  - sentinel 不在も `inconclusive`
  - `go` の受理条件は広げておらず、G1/G2 の封じ込め判定契約に回帰はありません
- docs 編集・commit・直接の `qsub` / `qstat` / `qdel` 実行は行っていません。