段 5 author 実装は完了しました。ただし計算ノード dispatch が基盤エラーで停止したため、状態は「実装済み・未実走」であり `closed` ではありません。

## 変更

- [env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:36)
  - K=5、interval=50ms、選択規則から method を構築。
  - affinity・走行 CPU・cpuinfo・時刻・待機だけを注入する runtime seam を追加。
  - `/proc/thread-self/stat` の processor field を使用。
  - sysfs CPU ∩ 元 affinity から決定的に K target を選択。
  - `pin → mask exact → deadline → pre CPU → read → post CPU` を独立検査。
  - `finally` で元 affinity を復元し、再取得した集合との exact 一致を確認。
  - K snapshot の CPU 集合・identity drift を拒否し、CPU ごとの最小 MHz を算出。
  - TSC 測定を復元完了後へ固定。
  - fallback、read skip、K 切り下げ、正しさ用 `assert` はなし。

- [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:36)
  - 既存 fixture を exact な5 CPU fixtureへ更新し、OS monkeypatchをruntime seamへ置換。
  - method/target規則、thread-self stat、静穏受理、reader外れ値吸収、持続外れ値拒否を追加。
  - 4高値+1帯内の受理／4帯内+1低値の拒否を固定。
  - mask不変、pre/post CPU不一致、K未満、read中断、CPU集合・identity drift、復元失敗を追加。
  - set失敗時のruntime readと直接parser fallbackを二重spyで禁止。
  - read開始間隔、遅延受理、TSC復元後順序、純関数reducerを検査。
  - outward clock keyを `samples_mhz` / `method` / `governor` のexact集合で固定。

テストファイルの新設・改名はないため、test-file inventory用meta-testの追加対象ではありません。docs、commit、no-touch面は変更していません。

## 検査

成功:

- `python3 -m py_compile orchestrator/campaign/env_attestation.py orchestrator/tests/test_env_attestation.py`
- `git diff --check`

未実走:

```text
python3 tools/run_tests.py orchestrator/tests/test_env_attestation.py -q
```

結果は runner rc=16:

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
NQSconnect: [API ESYSCAL] Can't create socket. (errno: 1)
```

したがって `test_env_attestation.py` の全nodeid、関連consumer test、既存330件は未実走です。意図的に赤くなるテスト集合はありません。

## 静的な波及

所有外の直接caller:

- `qualification/t126_driver.py`
- `campaign/execution_guard.py`
- `campaign/s8b_floor_campaign.py`
- `calibrator/cli.py`
- `tools/pegasus/run_probe.py`

transitive caller:

- `campaign/loop.py`
- `campaign/s8b_oracle_driver.py`
- `campaign/silo_ladder_rung1.py`
- calibration certification / smoke probe scripts

関連consumer testとして再走が必要な面:

- `test_execution_guard.py`
- `test_calibrator_certify.py`
- `test_env_contract.py`
- `test_t126_qualification_driver.py`
- `test_s8b_floor_campaign.py`
- `test_s8b_oracle_driver.py`
- `test_silo_ladder_rung1_driver.py`
- `test_silo_ladder_rung1_evidence.py`
- no-touch保存物consumerの `test_s8b_ratified_freeze.py` / `test_s8b_oracle_report.py`
- probe wrapperの `test_pegasus_tools.py`

共有fixtureは同一ファイル内の `_probe_tree` と `_patch_runtime_probe` のみで、外部参照は静的検索上ありません。

## 総括

方式αの本番経路と要求された純増検出力をコード・テストへ実装しました。変更は2ファイルだけで、docs・commit・no-touch面への変更はありません。計算ノード接続失敗のためテストは未実走であり、親によるdispatch再実行が必要です。