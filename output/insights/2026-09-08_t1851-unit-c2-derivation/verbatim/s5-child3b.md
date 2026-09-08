## 変更前の受理・拒否挙動

- runner は exact 7-key observation を生成し、exact consumer は旧 6-key observation を拒否する状態でした。
- 所有 file の fixture 10 箇所だけが旧 6-key のまま残っていました。
- `pipeline._run_balanced_schedule()` は key 集合を検査せず、`throughput` だけを読む subset consumer でした。
- 受理・拒否条件そのものは変更していません。

## 追随した literal (file:line)

すべて正常 rep のため、exact `bool` の `execution_failure=False` を追加しました。rep 単位の実行例外を模す literal はありませんでした。

- `s8b_v2_freeze_fixture.py:155`
- `test_s8b_attempt_registry.py:347`
- `test_s8b_floor_attempt_launcher.py:238`
- `test_s8b_floor_attempt_launcher.py:865`
- `test_s8b_floor_attempt_launcher.py:870`
- `test_s8b_floor_attempt_launcher.py:875`
- `test_s8b_floor_attempt_launcher.py:948`
- `test_s8b_floor_attempt_launcher.py:1415`
- `test_s8b_ratified_freeze.py:530`
- `test_s8b_ratified_verify.py:377`

AST 検査で全件が exact 7 key、`execution_failure` が exact `False` であることを確認しました。

## B5 の固定

`test_backoff_extended_sweep.py:205` に `test_b5_pipeline_balanced_schedule_is_a_seven_key_subset_consumer` を追加しました。

実体 `campaign_pipeline._run_balanced_schedule` の AST を検査し、`observation` の全 read が3箇所の `get("throughput")` だけであることを固定しています。exact 7-key observation を入力例に使用し、依存先の stub 置換は行っていません。

## 実走した nodeid と結果

- `test_s8b_attempt_registry.py::*`: 147 passed
- `test_s8b_floor_attempt_launcher.py::*`: 61 passed
- `test_backoff_extended_sweep.py::*`: 40 passed
  - 新設 B5 node を含めて PASS

次は指定起動を実行しましたが、自己実行 harness がなく node は実走されていません。

- `test_s8b_ratified_freeze.py`: rc=0、node 0
- `test_s8b_ratified_verify.py`: rc=0、node 0
- `test_s8b_oracle_manifest.py`: rc=0、node 0
- `test_s8b_oracle_report.py`: rc=0、node 0

次は成長 hold で拒否されました。解除や迂回はしていません。

- `test_s8b_holdout_freeze.py::*`: `GrowthTestHoldBypassRefused`
- `test_s8b_oracle_driver.py::*`: `GrowthTestHoldBypassRefused`

## 64hex literal を書き換えずに済んだか

済みました。既存の 64hex literal は一件も変更していません。`docs/` と `output/` も変更していません。

## 残った赤とその帰属

実走された node に assertion failure はありません。

ただし fixture consumer のうち、成長 hold の 2 file と自己実行 harness がない 4 file は未実走です。このため全 consumer を closed とは申告しません。

## 所有外への波及可能性 (静的列挙)

- `s8b_v2_freeze_fixture.py` の consumer は holdout freeze と oracle driver、manifest、report です。
- campaign、stats、terminal evidence、resume の exact 7-key gate と fixture が整合しました。
- 旧 6-key journal は引き続き fail-closed です。
- `pipeline._run_balanced_schedule` は `throughput` だけを読む subset consumer として固定しました。
- `FORMULA_ID`、凍結成果物 bytes、固定 digest には波及していません。

## 総括

所有 6 file 内の追随と B5 固定は実装済みです。実走できた 249 node は全緑でした。成長 hold または harness 不在の consumer が残るため、総状態は「実装済み・一部未実走」です。commit は作成していません。