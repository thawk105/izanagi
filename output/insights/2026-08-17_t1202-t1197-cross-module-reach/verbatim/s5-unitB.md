実装は完了しましたが、実行基盤不足のため「実装済み・未実走」です。`closed` やテスト緑とは申告しません。

## 総括

- 実装したもの:
  - [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration.py:50) の `DECIDER_VERSION` を `s8c-decider/v2` へ更新。
  - [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:2017) に v2 の exact assert を追加。M12 の `v2 -> v1` で失敗する形。
  - 既存の不一致 fixture 4 件を current と異なる版へ変更。
  - hostile `str` subclass を `HostileRuntimeDecider(M.DECIDER_VERSION)` へ変更。
  - v1 固定 assertion 2 件を record 保存版からの比較へ変更。
  - malformed な `v0`、`v01`、`v1/extra` は維持。
  - `git diff --check` 成功。docs 編集、commit と凍結記録変更はなし。

- 実走した nodeid:
  - なし。
  - `python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_core.py` を起動したが、pytest 到達前に Pegasus dispatch が `qstat -Q rc=1`、runner rc=16 で停止。
  - local headroom は再確認時も 0 bytesで、安全な実走条件を満たさなかった。

- 未実走のもの:
  - core ファイル全体と exact assert。
  - M12 変異実走。
  - `test_trial_registry.py`、`test_reflux_origin_binding.py`。
  - `test_p3_autonomous_workload_trial.py::test_projected_provider_rejects_server_tool_use`。
  - 新設テストに対する横断 meta-testと親の受入全走。

- 期待赤と回帰の区別:
  - 期待赤は、単位 A 未統合時に cross-module の新しい C12 reason/evidence を要求する predicate suiteだけ。
  - core、版一致、trial registry、reflux、p3 consumer の赤はすべて回帰扱い。
  - 今回はテスト本体が未実行のため、観測された期待赤・回帰ともにゼロ。

- 波及:
  - `trial_registry`、`reflux_origin_binding`、p3 test は版 literal ではなく定数または capability/digest を参照しており、静的には追従。
  - digest の間接 consumer は `s8c_acceptance_receipt`、`autonomous_trial_completeness`、trial lifecycle。
  - 共有 fixture は core の `_record_raw` / `_install_g1`、trial registry と reflux の effective report fixture。
  - 現 g3 は legacy schemaで `decider_version` を持たず、引き続き `decider-version-unbound`。
  - 所有外の `s8c_preregistration_evidence.py` と predicate test に並行する単位 A の差分が存在するが、変更していない。