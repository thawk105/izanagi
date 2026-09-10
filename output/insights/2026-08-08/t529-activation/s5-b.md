実装は完了しました。docs・commit・所有外ファイルには触れていません。pytest は Pegasus dispatch 障害により未実走です。

## 総括

1. 実装ファイルと行数

- [execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:47): 728 行、`+143/-6`
  - PID・opaque process seal・serial/state hash・state/receipt object identity を持つ process-local receipt。
  - fork child で lock/seal/receipt を再初期化。
  - guard は `env_contract.lookup()` を呼ばず、receipt の検証済み state と `GENERATIONS` から契約を解決。
- [contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/contract.py:38): 603 行、`+10`
  - activation leaf、calibration verifier、execution guard と静的 import 閉包を追加。
  - activation record JSON は identity path 集合へ追加していない。
- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:254): 4,864 行、`+5`
  - runtime binding に activation leaf と record directory 内 JSON を追加。
- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/pegasus/probes/t419_probe_causality.py:3469): 4,524 行、`+2`
  - dirty scope に activation leaf と record directory を追加。
- 対応テスト:
  - [test_execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_execution_guard.py:40): 857 行、`+89`
  - [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_campaign.py:2246): 7,531 行、`+60`
  - [test_silo_ladder_rung1_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_silo_ladder_rung1_driver.py:926): 2,614 行、`+7`
  - [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_t419_probe_causality.py:1567): 1,657 行、`+45`
  - [test_t126_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_t126_pegasus_tools.py:1428): 5,924 行、`+40`
  - [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py:303): 542 行。指定された `first` の `NameError` を 1 行で修理。
  - [test_s8b_ratified_verify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_s8b_ratified_verify.py:702): 2,336 行、`+2/-2`。構造検査、activation current、historical/live lane の三点を検査する意味へ更新。

受理集合は、変更前には exact current contract を `lookup()` で照合し、receipt の stale・forged・fork 継承は受理結果へ影響しませんでした。変更後は従来の exact current contract だけを引き続き受理し、不正 receipt を型検査直後に拒否します。既存 5 条件の意味・順序、成果物 bytes、scope 外入口の受理集合は変えていません。

2. 走らせた検査と結果

- `git diff --check`: OK
- 変更対象 11 Python ファイルの `ast.parse`: OK
- 静的 import 閉包検査: OK
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- docs 差分: なし
- commit: なし

最終形の新設・修理 nodeid 12 件と `test_plain_runner_coverage.py`、さらに `test_execution_guard.py` 全体を `tools/run_tests.py -n 1` へ渡しましたが、すべて実行開始前に `rc=16`、`qstat -Q preflight rc=1` で停止しました。実行 nodeid は 0 件で、pytest の緑は主張しません。

3. 未実走・未達

- 上記焦点 nodeid、meta-test、関連ファイル全体、受入全走は未実走。
- mutation matrix、provenance 監査は親担当かつ未実施。
- floor・oracle driver・selector・T126 の最初の書込み境界・PBS wrapper への receipt 配線は裁定どおり scope 外。

4. 期待される赤

- commit 前は activation leaf が untracked のため、T126 の `test_every_required_identity_path_is_tracked_in_this_repo[...]` は赤になる見込み。親 commit 後に解消すべき赤です。
- 所有外の `_patch_current_contract_to_synthetic_successor` は先行単位の g2 登録後も `GENERATIONS[ENV_TAG][-1]` を g1 と扱うため、次の 4 テストは既知の赤候補です。
  - `test_public_validate_protocol_resolves_recorded_historical_generation_once`
  - `test_main_validates_recorded_g1_with_historical_lane_when_current_is_g2`
  - `test_fresh_run_rejects_recorded_g1_when_current_contract_is_g2_before_io`
  - `test_resume_rejects_recorded_g1_when_current_contract_is_g2_before_calibration`
- 今回の変更はこの fixture や floor lane に触れておらず、既知の問題を悪化させていません。
- ratified verify の陳腐化 assert と activation test の `NameError` は修理済みですが未実走です。

5. 親への申し送り

- pytest はキュー復旧後、上記焦点 nodeid、変更した test file 全体、meta-test、受入全走の順で再実行してください。
- commit 後に T126 tracked-path test と provenance 監査が必要です。
- 所有外 caller は `loop.py`、`pipeline.py`、`s1_direct_comparison.py`、`screening_driver.py`。共有 consumer は T126 identity producer/verifier、silo runtime binding producer/verifier、T419 submission/final binding、ratified freeze の historical/live lane です。
- certified sink の guard では receipt が load-bearing になりましたが、「全入口 receipt 済み」とは扱わないでください。