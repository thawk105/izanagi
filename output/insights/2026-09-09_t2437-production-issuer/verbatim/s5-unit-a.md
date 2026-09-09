## 実装した内容

- [pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-a/orchestrator/campaign/pipeline.py:302)
  - `EvalResult` 末尾へ契約どおり `build_attempt_id`、`verify_result` を追加。
  - local verifier の戻り値を同一 object のまま repetition outcome へ保持。
  - `_abort` に keyword-only `verify_result` を追加し、`type(value) is VerifyResult` を強制。
  - `verify_result=None` の初期化は `_project_repetition_outcome` 入口の一箇所だけ。
  - accepted と remote fan-out は常に `None`。wire payload からの復元なし。
  - pre-build abort と通常経路へ生成済み `build_attempt_id` を設定。
- [test_pipeline_verify_result_retention.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-a/orchestrator/tests/test_pipeline_verify_result_retention.py:56)
  - 指定された正例・負例を5 nodeで追加。
  - self-run harness 付き。README allowlist への追加は不要。
- 所有外ファイル、docs、既存テスト期待値は変更していない。commit、push、ブランチ操作も未実施。

## 実走した検査 (nodeid と範囲を明記。未実走はそう書く)

全緑:

- 新規ファイル全5 node: `5 passed`
  - `test_local_rejected_repetition_retains_exact_verify_result_and_wal_binding`
  - `test_remote_fanout_abort_does_not_reconstruct_typed_verify_result`
  - `test_abort_rejects_non_exact_verify_result`
  - `test_accepted_evaluation_does_not_retain_one_pass_verify_result`
  - `test_prebuild_abort_retains_generated_build_attempt_id`
- `orchestrator/tests/test_verify_fanout.py` 全41 node: `41 passed`
- `orchestrator/tests/test_plain_runner_coverage.py` 全3 node: `3 passed`
- `orchestrator/tests/test_update_acceptance_duration_ledger.py` 全76 node: `76 passed`
- 両所有 pathの `git diff --check` と U+0300〜U+036F 検査: 合格

台帳 producer が最終 JUnit から生成した親登録用値:

- local rejected: `0.30s`
- remote fan-out abort: `0.34s`
- non-exact型拒否: `0.27s`
- accepted: `0.18s`
- pre-build abort: `0.12s`

`acceptance_duration_ledger.json` 自体は指示どおり未編集。

`test_campaign.py` 全範囲も self-runしたが、`333 passed, 67 failed, 3 skipped` で全緑ではない。失敗本文は次の既知分類だった。

- 未commitの `pipeline.py` による `contract-loader-drift`
- direct harnessで `tmp_path`、`monkeypatch`、parametrize引数が供給されない既存node
- sandbox内へ解決された official output root の拒否
- Pegasus login node上の計測拒否

新fieldやtyped保持の assertion failureは観測していないが、この全範囲は closed と申告しない。`tools/run_tests.py` 経由の受入全走も、指示記載のrc=16制約により未実走。

## 現行の受理・拒否挙動 (scope 前後)

変更前後とも、local verifier rejectはterminal abort、acceptedは全 repetition 成功後のcommit、remote abortは認証済みwire情報としてfail-closed、build/bench失敗はabortである。WALのframe、stage、payload key、`result_to_dict()` projectionは変更していない。

変更後に増えたのはin-memoryの帰属情報のみ。

- local rejected: verifierが返した同一 `VerifyResult` objectを保持
- accepted: `verify_result is None`
- remote fan-out: `detail.verify` が存在しても `verify_result is None`
- non-exact値: `_abort` 境界で明示拒否
- 一意なpipeline attempt: `EvalResult.build_attempt_id` とterminal WALが一致

したがってproduction入力の受理集合は不変。campaign lock digestの変化はsource closure設計どおり。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

production consumerは `loop.py`、`p2_2.py`、`backoff_sweep.py`、`sanity_silo.py`、`p3_kickoff.py`、`p3_s4_red.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`p3_s4_loop.py`、`p3_s4_loop_sort.py`、`p3_s4_loop_trigger_gating.py`、`paper_story_a2_certification.py`、`backoff_repro.py`、`demo.py`、`s1_direct_comparison.py`、`screening_driver.py`、`s8b_oracle_driver.py`。

直接constructorを持つ既存consumer testは `test_campaign.py`、`test_dev_wave_land.py`、`test_s1_direct_comparison.py`、`test_screening_driver.py`、`test_s8b_oracle_driver.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_paper_story_a2_certification.py`。末尾既定値のため変更不要で、`EvalResult` 全体を `asdict`、`vars`、`__dict__` 経由でserializeするproduction経路も見つからなかった。

新規テストは既存 `test_campaign`、`test_verify_fanout` の支援fixtureと、`g1_serial`、`r1_write_skew` trace fixtureを再利用するが、共有fixtureは未編集。

## 契約の問題

無し。

## 総括

単位Aは指定された2 pathだけで実装済み。焦点5 node、fan-out 41 node、self-run meta-test、台帳producer検査は全緑で、変更は未commitのまま保持している。