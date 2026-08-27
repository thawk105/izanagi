## 総括

変更前は、承認なしの floor pilot を driver が拒否し、承認 option/env を submitter から job まで伝播していました。変更後は承認経路を撤去し、pilot は既存の正しさゲートへ進みます。official 拒否と D1161 予算承認は不変です。

編集は指定された 6 file のみです。pytest は infrastructure failure で未実走です。

## 実装した内容

- [s8b_floor_campaign.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-b/orchestrator/campaign/s8b_floor_campaign.py:6945)
  - public/core API の承認引数、exact-bool 検査、pilot 拒否を撤去。
  - 予約 call から `irreversible_pilot_approved` を削除。
  - CLI option と `main()` の伝播を撤去。
  - reservation は引き続き opaque に finalize へ渡すため、A が追加する `measurement_generation_digest` と整合します。

- [submit_floor.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-b/tools/pegasus/submit_floor.sh:621)
  - usage、case、既定値、`qsub -v` の承認 env を撤去。
  - export は submission nonce と既存 evidence root のみに限定。

- [floor_campaign.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-b/tools/pegasus/floor_campaign.sh:1223)
  - 承認 env/nonce 一致検査と driver flag 追加を撤去。
  - `--mode pilot` は固定のままです。

## 現行挙動と変更後挙動

- 変更前:
  - driver/submitter は旧承認 option を受理。
  - 承認なし pilot は拒否。
  - submitter は nonce-bound 承認 env を輸送し、job が照合して flag を追加。

- 変更後:
  - driver と submitter は旧 option を argparse/case default で exit 2 拒否。
  - pilot は承認値なしで既存の protocol、freeze、environment、perf、build、admission 各 gate へ進む。
  - job は承認 env を参照せず、driver argv は mode/protocol/fetchcontent の固定集合。
  - official は従来どおり拒否。

## 追加・改訂したテスト

必須 nodeid を実在させました。

- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-b/orchestrator/tests/test_s8b_floor_campaign.py:6927)  
  `test_floor_driver_rejects_removed_confirmation_option`

- [test_pegasus_floor_tools.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/impl-b/orchestrator/tests/test_pegasus_floor_tools.py:2482)  
  `test_submit_floor_export_spec_has_no_confirmation_env`

加えて、public/core signature、予約 call keyword、job source/argv、submit option 拒否を active 面に限定して更新しました。全 source identifier ゼロ検査にはしていません。

file 集合メタテストとして以下を確認しました。

- `test_plain_runner_coverage.py` の全 `test_*.py` 列挙
- `test_pytest_collection_config.py` の `test_*.py` glob

test file の新設・改名はないため追随不要です。旧 nodeid は所有外の `acceptance_duration_ledger.json` に残っています。

## 実走したもの / 実走できなかったもの

実走済み:

- `bash -n tools/pegasus/submit_floor.sh tools/pegasus/floor_campaign.sh`: 成功
- Python 4 file の AST parse: 成功
- `git diff --check`: 成功
- actual CLI smoke:
  - driver の旧 option: exit 2、`unrecognized arguments`
  - submitter の旧 option: exit 2、`unknown argument`

pytest は未実走です。`tools/run_tests.py` で必須 2 nodeidおよび関連 nodeidを試行しましたが、すべて `qstat -Q preflight rc=1`、`child_started=false`、rc=16 で終了し、pytest child は一件も起動していません。したがってテスト緑は主張しません。

## 所有外への波及可能性

- 実装子 A の `s8b_holdout_admission.py` が新署名と `measurement_generation_digest` を land するまで、core 到達テストは旧必須 kw 欠落になります。
- A 所有の `test_s8b_holdout_admission.py`、`s8b_floor_evidence_fixture.py`、`test_s8b_oracle_driver.py` は新 schema/API への追随が必要です。
- R33 pin 対象の oracle/n-pilot driver・shell・test は意図的に未変更で、旧 identifier が残ります。
- `acceptance_duration_ledger.json` の削除・改名済み nodeid は親の統合後処理候補です。

## 親が処理すべき docs の残存箇所

- `tools/pegasus/README.md:226`
- `tools/pegasus/README.md:241-243`
- `docs/phase3-8b-restart-runbook.md:235`

## 期待赤 (実装子 A 未 land 由来)

事前指定した期待赤は次だけです。

- floor reservation 到達時の旧 callee必須 kw `irreversible_pilot_approved` 欠落
- A 未実装の `measurement_generation_digest` 契約に直接由来する failure

pytest child 自体が起動しなかったため、実際に観測した期待赤はありません。それ以外の failure は回帰扱いです。

## 未完・親の判断が要る点

- 実装子 A land 後の必須 nodeid・所有 3 test file の実走
- full integration test と acceptance duration ledger の扱い
- 上記 docs の更新
- test runner が自動生成した ignored `output/pegasus-dispatch/*/receipt.json` は編集・削除していません
- git commit/add等は行っていません。