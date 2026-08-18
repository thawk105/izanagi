## 総括

- [T-762] の current／historical-prefix 二重 wrapper 化を実装し、`ident.py` の直接 activation leaf 経路を除去した。
- serial-1 calibration 破損の runtime 負対照 2 本と、過剰拒否を検出する正例 3 本、AST 補助検査を追加した。
- pytest は dispatch preflight の rc=16 で開始されておらず、実装済み・未実走。残る赤は実行基盤エラーと未実測範囲である。

## 変更点 (file:line)

- [env_contract.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/env_contract.py:634)
  - active row の generation/hash 再照合、calibration 検証、verified hash 更新を共通化。
  - [env_contract.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/env_contract.py:690) に historical-prefix loader を追加。
  - [env_contract.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/env_contract.py:721) で historical cache も fork 後に破棄。
  - [env_contract.py:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/env_contract.py:805) に current／historical の公開 wrapper を追加。既存 `current_activation_state()` は同じ current snapshot を返す。
- [ident.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:210) と [ident.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:264)
  - current head と recorded prefix を別 wrapper へ接続。
  - `env_contract_activation` import と三関数への直接参照を除去。
- [test_env_contract_activation.py:1952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_env_contract_activation.py:1952)
  - 既存 serial-2 artifact-admission テストの意図を維持し、wrapper の `EnvContractError` 境界へ追随。
- [test_t762_ident_wrapper.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t762_ident_wrapper.py:108)
  - 新規 runtime／正例／AST テスト群を追加。

## 負の対照

実コードでは successor callback は serial-2 以降だけで、serial-1 では呼ばれないことを確認した。この差を使い、record・catalog・contract hash は変更せず calibration bytes だけを破損している。

- [test_t762_ident_wrapper.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t762_ident_wrapper.py:108): current serial-1。旧 direct `load_activation_state` は受理し、新 current wrapper は拒否する。
- [test_t762_ident_wrapper.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t762_ident_wrapper.py:154): current serial-2／recorded prefix serial-1。旧 direct prefix validation は受理し、新 historical wrapper は拒否する。
- 正例:
  - current serial-2: [line 193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t762_ident_wrapper.py:193)
  - recorded serial-1: [line 215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t762_ident_wrapper.py:215)
  - 旧 v2 lock の prefix: [line 246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t762_ident_wrapper.py:246)
- AST 補助検査: [line 268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t762_ident_wrapper.py:268)

## 現行挙動と変更後の受理集合

変更前は、serial-1 の record/catalog/hash が整合していれば、active calibration が壊れていても `ident.py` の current および prefix 直接経路は受理した。serial-2 の変更 row は successor callback が既に検査するため、既存 serial-2 fixture はこの差を検出できなかった。

変更後は、同じ入力を current／historical の双方で calibration・registry 再照合して拒否する。一方、正常な current serial-2、recorded serial-1、旧 v2 prefix は維持する。受理集合は未検証 calibration を持つ activation tuple の分だけ狭まり、指示外の受理拡大はない。

## 波及可能性

所有外 production import caller の grep 結果:

- `ident`: `artifact_admission.py`, `backoff_repro.py`, `backoff_sweep.py`, `guided.py`, `loop.py`, `pipeline.py`, `reflux_origin_binding.py`, `screening_driver.py`, `source_digest.py`, `qualification/series.py`, `p3_*`, `s1_*`, `s6_sort_sweep.py`, `s8a_trigger_sweep.py`。
- `env_contract`: `buildcache.py`, `certified_writer_admission.py`, `env_attestation.py`, `execution_guard.py`, `wal.py`, `pipeline.py`, `loop.py`, `model.py`, `reservation.py`, `reflux_source_closure.py`, `qualification/t126_driver.py`, `p2_2.py`, `p3_*`, `s1_*`, `s6_*`, `s8a_*`, `s8b_*`, `screening_driver.py`, `silo_ladder_rung1.py`, `sanity_silo.py`, `demo.py`, `pegasus_floor_scoping.py`。

所有外 test/support の grep hit は `test_env_contract.py`, `test_campaign.py`, `test_artifact_admission.py`, `test_campaign_lock_codec.py`, `test_campaign_lock_wal_consumers.py`, `campaign_lock_test_support.py`, `test_execution_guard.py`, `test_guided.py`, `test_screening_driver.py`, `test_t671_source_binding.py`, `test_t126_qualification_*`, 各 `test_p3_*`, `test_s6_*`, `test_s8a_*`, `test_s8b_*` など。特に `env_contract.py`／`ident.py` の bytes 変更は単位 C の loader-binding closure pin と `test_t671_source_binding.py` に波及し得る。

## 未実走・未解決

- 試行範囲: `python3 tools/run_tests.py orchestrator/tests/test_t762_ident_wrapper.py`
- 結果: `qstat -Q` preflight 失敗、rc=16。pytest child は未開始で、全 nodeid 未実走。
- `test_env_contract_activation.py` の焦点 nodeid、`test_plain_runner_coverage.py`、closure consumer test、全受入は親での実測が必要。
- 静的確認は `AST OK` 4 file、import/API probe、禁止直接参照の grep 0 件、`git diff --check` 成功。
- docs 編集・commit は行っていない。