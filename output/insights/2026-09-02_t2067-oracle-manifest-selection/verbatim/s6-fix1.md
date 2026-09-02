## 変更

`assert isinstance(captured.value.__cause__, oracle_spec.ReviewedSpecError)` を追加しました。これにより、gate 由来の同一 reason ではなく、spec loader まで到達したことを識別できます。

## 検査

指定 nodeid は dispatch 基盤の `qstat -Q` 認証エラーで子 test が起動せず、実装済み・未実走です。生成された一時物は除去済みです。

## 総括

- 変更した file と行: [test_s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067-fix1/orchestrator/tests/test_s8b_oracle_manifest.py:1483)
- 足した assert: `isinstance(captured.value.__cause__, oracle_spec.ReviewedSpecError)`
- 実走の有無と結果: 実装済み・未実走。nodeid `orchestrator/tests/test_s8b_oracle_manifest.py::test_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate`、dispatch `rc=16`、`child_started=false`