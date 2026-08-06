| Fix | 判定 | 対応 |
|---|---|---|
| F1 | **partial** | manifest 単位で resolver/calibration を1回だけ解決し、同一結果/error を各 campaign へ伝播。2 campaign test 追加。未実走 |
| F2 | **partial** | 既存 cross-env dishonest 負例を維持し、same-env/wrong-hash 負例を独立追加。未実走 |
| F3 | **partial** | C4 正例・拒否 matrix で rows 件数を status/reason より先に固定。未実走 |
| F4 | **partial** | calibration mock error を temp repo の実ファイル削除・bytes 改変へ置換。未実走 |
| F5 | **partial** | 揮発 hash を正規化後、reason 集合の完全一致を復元。未実走 |
| F6 | **partial** | live gate core に `LaunchValidatedFreeze` exact-type gate と historical token 拒否 test を追加。未実走 |
| F7 | **partial** | shared core と公式 CLI の docstring を現行経路へ訂正。未実走 |
| F8 | **partial** | ambiguous/dishonest が patch-only 構造防御で production artifact から到達不能と明記。未実走 |

## 変更 hunk

- [s8b_oracle_report.py:1264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1264)、[同:1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1381)、[同:1626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1626)
  - `build_observations` で解決を1回だけ行い、結果/error を `_assess_campaign` へ渡す。
  - error 適用位置は従来どおり terminal 正常・campaign-start 一意の枝内。early return の status/reason は変更していない。

- [s8b_oracle_driver.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:344)
  - `_gate_check_core` 入口に exact-type 拒否を追加。この1点以外は未編集。

- [s8b_ratified_freeze.py:2845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2845)
  - shared core の説明を中立な full validation core へ変更。

- [s8b_oracle_manifest.py:819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_manifest.py:819)
  - 公式 CLI の経路を `reverify_published_freeze` と historical contract 再検証へ訂正。

- [test_s8b_oracle_report.py:1951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1951)、[同:1961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1961)、[同:2085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:2085)、[同:2113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:2113)
  - rows 件数、2 campaign call-count、F8 docstring、F5 reason 完全一致を追加。

- [test_s8b_ratified_verify.py:760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_ratified_verify.py:760)、[同:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_ratified_verify.py:804)、[同:855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_ratified_verify.py:855)
  - F8 docstring、same-env/wrong-hash resolver、実 calibration 削除・改変を追加。

- [test_s8b_oracle_driver.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_driver.py:1430)
  - `ReverifiedFreeze` を live core に渡す拒否 test を追加。

## Test nodeid

すべて実装済み・pytest 未実走です。

- `orchestrator/tests/test_s8b_oracle_report.py::test_build_observations_accepts_recorded_g1_under_g2_current`
- `...::test_build_observations_resolves_contract_once_across_two_campaigns`
- `...::test_build_observations_historical_resolver_fails_closed_without_current_fallback`
- `...::test_manifest_contract_sha256_mismatch_with_registry_is_protocol_violation`
- `orchestrator/tests/test_s8b_ratified_verify.py::test_public_reverify_resolver_refusals_do_not_fallback_to_current`
- `...::test_public_reverify_rejects_dishonest_same_env_wrong_hash_resolver`
- `...::test_public_reverify_calibration_refusals_do_not_fallback_to_current`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_gate_check_core_rejects_reverified_freeze_token`

新設 test 用 meta-test:

- `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `...::test_every_test_file_is_self_runnable_or_allowlisted`
- `...::test_this_metatest_is_itself_self_runnable`

`tools/run_tests.py` から計算ノード dispatch を2回試みましたが、いずれも pytest 開始前の `qstat -Q preflight rc=1`、dispatch rc=16 で停止しました。

静的検査は以下が成功しています。

- 対象7ファイルの `python3 -m py_compile`
- `git diff --check`
- 禁止語0件
- docs、output、`env_contract.py`、`s8b_floor_campaign.py` の差分0件
- commit / `git add` 未実行

## 所有外への波及可能性

- `build_observations` の全 consumer と `test_s8b_oracle_report.py` 全体は、解決タイミング変更の回帰対象。
- `_gate_check_core` の caller は `gate_check` と `_gate_check_validated`。live `run_block` の正当 token は不変だが driver consumer test 全体が確認対象。
- 共有 fixture `_two_campaign_manifest`、`_build_launch_repo`、`_fake_launch_validated` を利用。production fixture 自体は変更していない。
- floor campaign、loop、pipeline、trigger gating、fuse、registry は未変更。
- R7 の不正 `run_contract` legacy 迂回には触れていない。

## 総括

残る赤は未判定で、全行 `partial（実装済み・未実走）`。  
親は計算ノードで上記 nodeid、meta-test、関連3 test file、および M3a/M3b/M3c を必ず確認する。  
特に F1 の terminal 異常時 status/reason と F6 の正当な live token 不変を確認すること。  
commit・add・docs/output 編集は行っていない。