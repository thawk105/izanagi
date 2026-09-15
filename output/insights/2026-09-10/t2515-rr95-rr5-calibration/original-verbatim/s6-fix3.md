対応は [test_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-author/orchestrator/tests/test_pegasus_tools.py:255) のみに限定しました。commit はしていません。

### 対応表

| 対応事項 | 状態 | 結果 |
|---|---|---|
| 選定ブロックだけを抽出 | closed | 条件関門・gflags・glog を除外 |
| PATH shim の実行検証 | closed | 独立した shim 行を連結し、既存 harness で実行 |
| 既存 assert の維持 | closed | 削除・緩和・skip・xfail なし |
| 無関係な行の混入検査 | closed | `GFLAGS_SOURCE_PATH`、`GLOG_SOURCE_PATH`、`run_condition_gate`、`PERF_EVENTS` を検査 |
| 公式 runner による nodeid 実走 | partial | `qstat -Q` preflight rc=1、child 未起動 |
| 既知の退行 | regressed | 0件 |

抽出境界は実 source から次の逐語 anchor を使用しています。

- 選定範囲先頭: `CALIBRATE_PYTHON=""`
- 選定範囲末尾: `fi`
- 直後の除外 anchor: `run_condition_gate() {`
- 連結する shim 範囲: `CALIBRATE_PATH="$TMPDIR/bin:$(dirname "$CALIBRATE_PYTHON"):$PATH"` の1行だけ

検査結果:

- 構文 compile: PASS
- `git diff --check`: PASS
- 同じ2テスト関数の harness 補助実走: PASS
- 以下の nodeid は実装済み・未実走:
  - `orchestrator/tests/test_pegasus_tools.py::test_certify_calibrator_resolves_and_shims_versioned_interpreter`
  - `orchestrator/tests/test_pegasus_tools.py::test_certify_calibrator_interpreter_resolution_fails_closed`

所有外への静的な波及可能性は、helper を共有する上記2テストのみです。production script、submit script、workload test、docs は本段では変更していません。

## 総括

選定ブロックと後段 PATH shim を別々に抽出し、連結して実行検証するよう修正しました。  
gflags・glog・条件関門・perf 行の混入を fragment 自身で検出します。  
既存の候補順・smoke・fail-closed・calibrator argv の assert はすべて維持しています。  
親は scheduler 復旧後に上記2 nodeid、続いて実機 certification job を再実走してください。