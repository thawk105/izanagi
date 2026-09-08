## 変更前の受理・拒否挙動

rep observation は常に 6 key で、実行例外の有無は `n_exec_fail` と診断用 notes にしか残りませんでした。正常、非 zero 戻り値、捕捉例外のいずれにも `execution_failure` はありませんでした。

## 実装した箇所 (file:line)

[runner.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s1/orchestrator/calibrator/runner.py:943)

- capture 面:
  - 初期値 `False`: 943
  - 捕捉時 `True`: 962、976
  - 最終 observation: 1002
- direct 面:
  - 初期値 `False`: 1116
  - 捕捉時 `True`: 1173、1188
  - 最終 observation: 1222
- 捕捉する例外型、`n_exec_fail`、診断 notes は変更していません。
- 集約 notes は 1036、1261 に残っています。
- 新 field には exact `bool` 以外を載せず、例外型名や message は載せていません。

## 足したテスト

- [test_calibrator.py:553](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s1/orchestrator/tests/test_calibrator.py:553)
  - `measure_point()` 専用。
- [test_calibrator_deferred_output.py:265](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s1/orchestrator/tests/test_calibrator_deferred_output.py:265)
  - `capture_measure_point()` 専用。

両 test とも正常、非 zero 戻り値、`RuntimeError`、`subprocess.TimeoutExpired`、基底 `Exception` を独立に確認し、全 observation を `type(value) is bool` で固定しています。

## 実走した nodeid と結果

- `orchestrator/tests/test_calibrator.py::*`: 60 passed
  - 新設 `::test_measure_point_execution_failure_is_exact_bool_for_all_outcomes`: PASS
- `orchestrator/tests/test_calibrator_deferred_output.py::*`: 10 passed
  - 新設 `::test_capture_measure_point_execution_failure_is_exact_bool_for_all_outcomes`: PASS
- `orchestrator/tests/test_pytest_collection_config.py::*`: 76 passed
- `orchestrator/tests/test_official_perf_closure.py::*`: 7 passed
- `orchestrator/tests/test_campaign_import_invariant.py::*`: 28 passed、2 failed
  - `::test_real_campaign_package_has_canonical_direct_bootstrap[...]`
    - 所有外の campaign 5 file が bootstrap ledger 未登録。
  - `::test_real_repository_legacy_namespace_matches_exception_ledger[...]`
    - 所有外の 2 file が legacy namespace ledger 未登録。
  - いずれも今回の 3 file や `execution_failure` とは無関係です。
- 所有 3 file の AST parse: 全件 OK
- U+0300〜U+036F: 全件 0

## 期待どおりの赤 (下流由来)

production gate の直接 probe では、正常な 5 rep の 7-key observation に対して次を実測しました。

- campaign exact 6-key gate: `throughputs=[]`、`rep_integrity_failures=5`
- stats exact 6-key gate: 5 件の `exact key 不一致`

静的に赤となる nodeid は次の 4 件です。

- `test_s8b_floor_campaign.py::test_rep_integrity_positive_control_default_measure_point[clean]`
- 同 `[nonzero_rc]`
- 同 `[missing_cycles]`
- 同 `[no_perf]`

`clean` / `no_perf` は期待する 5 qualified rep が 0 件となり、`nonzero_rc` / `missing_cycles` は期待する 4 qualified rep・1 failure が 0 qualified rep・5 failures になります。さらに stats verifier が全 rep の余分な `execution_failure` key を拒否します。

これらの node 本体は自己実行 harness がなく、所有外なので追加していません。ログインノードからの直接呼出しは target gate より前の machine-pin、続いて acquisition receipt gate で停止したため、上記 node を end-to-end 実走済みとは数えていません。

## 所有外への波及可能性 (静的列挙)

- `s8b_floor_campaign.py`: exact 6-key `complete` 述語。
- `s8b_floor_stats.py`: `_REP_OBSERVATION_KEYS` と exact 比較。
- `s8b_floor_attempt_launcher.py`: capture 面の private sink を後段へ渡す。
- `s8b_terminal_evidence.py`: observation bytes の digest と campaign record を束縛する。
- `s8b_ratified_freeze.py`: session 内の `rep_observations` を運ぶ。
- `pipeline.py`、`floor_pair_driver.py`、`backoff_extended_sweep.py`: subset key 読みなので静的には余分な key を許容。
- 子 2・子 3 所有の downstream test、fixture は 7-key 追随が必要です。

## 親の実測とのずれ

変更前の現物は親の位置と一致していました。変更後は挿入行により `measure_point()` が 1057 から 1064、集約 notes が 1029/1247 から 1036/1261 へ移動しています。

## 総括

S1 は両公開面で実装済み、所有テストは全緑です。S2、S3、B1〜B7、下流 gate、docs、output は変更していません。作業 rootへの add、commit、merge は行っていません。なお下流診断で呼んだ既存 test helper は一時 directory 内に fixture 用 git repository を作りましたが、作業 root の repository 状態は変更していません。