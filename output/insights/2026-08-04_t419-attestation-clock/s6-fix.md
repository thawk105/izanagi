F1・F2 ともテスト側のみで是正しました。production、docs、output、禁止ファイル、git index は変更していません。

## 総括

- 状態

  - F1: **closed（静的検査済み、pytest 実走は親待ち）**
  - F2: **closed（静的検査済み、pytest 実走は親待ち）**

- 変更ファイル／関数

  - [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:195)
    - `_profile`: probe tolerance を実値 `100.0` に変更し、通常 fixture の論理 CPU 数と標本数を整合。
    - `_pegasus_shaped_probe`: 48 標本×3 profile の fixture を追加。
    - `_expect_48_physical_cores`
    - `test_cli_effective_clock_self_failure_is_quality_rejected_before_publish`
    - `test_cli_published_artifact_passes_runtime_effective_clock_self_comparison`
  - [test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:436)
    - `test_registry_effective_clock_self_failures_are_exact_known_exception`
    - 恒真な集合比較を、独立した検査件数 `checked_entries == 2` に置換。

- 実データ確認

  - `job-staging` の `attestation-pre.json` 5 件すべてで `tolerance_pct=100`、標本数 48 を確認。
  - 負例には実データ由来の `3079.456 MHz` を使用。
  - 3 回の probe は異なる clock 列を返し、5% policy では `[static_pre=True, dynamic_pre=False, static_post=True]` と固定。

- 検査

  - pytest nodeid: **実走していない**。ホストが Pegasus ログインノード `pegasus02` のため、meta-test を含め親の計算ノード dispatch に委ねた。
  - `python3 -m py_compile orchestrator/tests/test_calibrator_certify.py orchestrator/tests/test_env_contract.py`: 成功。
  - `git diff --check`: 成功。
  - 親での焦点実走対象は上記 CLI 2 node、registry invariant node、および `test_plain_runner_coverage.py` の meta-test。既存成功系保護のため対象ファイル全体も必要。

- tolerance 上書き削除変異

  - dynamic-pre は probe tolerance 100% のままだと、差 `978.456` が許容差 `2101` 以下となり self-pass する。
  - その結果、負例が accepted になり [test_calibrator_certify.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:564) の `assert rc != 0` が落ちる。
  - 正例でも published artifact が `100.0` のままになり、[同ファイル:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:601) の `assert clock.tolerance_pct == 5.0` が落ちる。
  - gate を static-pre／static-post へ誤配線した場合も、両者は5%で passするため負例の `assert rc != 0` が落ちる。

- 波及可能性

  - `_profile` は同ファイル内の全 `_invoke` 利用テストで共有される。既存期待値は変更していないが、親のファイル全走が必要。
  - production caller は `cli._certify_main`、consumer は `execution_guard.effective_clock_comparison_passes`。両 production ファイルは本 fix では未変更。
  - registry 件数 pin により、将来の正当な entry 追加時も期待件数の明示更新が必要になる。
  - `test_execution_guard.py` の consumer golden vector、schema validation、実 calibration artifact 読込みが関連面。
  - U-1〜U-4、`silo_ladder_rung1`、`env_attestation.py`、`env_contract.py`、`output/` は非接触。commit／add／stash も未実施。