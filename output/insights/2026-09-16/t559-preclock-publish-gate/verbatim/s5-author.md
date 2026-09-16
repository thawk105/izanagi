## 変更内容

- [cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/calibrator/cli.py:1018)：82行、1018–1046行。canonicalの戻り値によるpre→post gate、失敗時sidecar、early未評価名を追加。
- [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t559-impl/orchestrator/tests/test_calibrator_certify.py:1656)：41行、1656–1798行。必須6種、bad_cv複合、実入力spyを追加。

変更は上記2ファイルのみ。既存fixture・期待値は指定の定数以外変更なし。commitなし。`git diff --check`成功。

## 実走結果

最終版で **88 passed / 0 failed**。範囲は`orchestrator/tests/test_calibrator_certify.py`の全nodeidです。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider -v' PYTHONPATH=. python3 orchestrator/tests/test_calibrator_certify.py
```

追加nodeidは同ファイルの以下9件です。

- `test_cli_pre_post_clock_rejects_high_outlier[0]`、`[24]`、`[47]`
- `test_cli_pre_post_clock_accepts_using_dynamic_pre[2095.0]`、`[2300.0]`
- `test_cli_pre_post_clock_rejection_mechanisms[low-outlier]`、`[post-self-pass]`、`[bad-cv]`、`[policy-change]`

指定された既存early完全一致assertionの4箇所もpassedです。

集合制約meta-testは **3 passed / 0 failed**。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py
```

実走nodeは以下です。

- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_this_metatest_is_itself_self_runnable`

## 挙動差と波及

以前はpre自己照合が通れば、post clockが帯外でも他条件次第でpublishできました。変更後はcanonicalのpre→post比較失敗を末尾reasonへ追加し、publish前に拒否します。benchmark中のpolicy変更では既存self reasonと新reasonの両方が残ります。

合格時のartifact入力・serialization・publish処理は変更していません。同じ既存入力に対するpublished bytes不変は差分上確認しました。変更前後のbytes比較実走はしていません。

参照関係から確認した波及先：

- `orchestrator/calibrate.py`が`cli.main`をimportするため、`--certify`取得経路に新拒否条件が届きます。
- 指定共有fixtureの参照は対象テスト内のみです。
- `test_effective_clock_policy.py`はCLIを、`test_pegasus_calibration_workload.py`はCLIの例外・genome helperをimportします。
- `test_execution_guard.py`、`test_env_attestation.py`、`test_env_contract.py`は共有canonical述語を参照します。述語自体は未変更です。これら所有外テストは未実走です。

## 射程と未実走

> 本 gate は、CLI が benchmark 直後に取得した post clock と凍結 pre profile の canonical 照合を
> publish 前に課す。benchmark **中**に帯外へ振れて post 観測までに戻った変動は検出しない。
> CLI 終了後に外側 wrapper が撮る `attestation-post.json` は本 gate の検査対象外であり、
> その窓は残る。probe の観測者効果 (F108) は是正しない。

plan v2の実装項目に未達はありません。M01–M09の変異実走・台帳登録は未実施です。成功時sidecar・別process verifier等は裁定どおりscope外です。

## 総括

- publish前に凍結pre→postのcanonical照合を追加し、失敗時だけ再計算用sidecarを保存。
- 上記逐語コマンドでcertify全88件、meta-test全3件passed、failedなし。
- 変異試験・所有外consumer test・変更前後bytes比較は未実走。