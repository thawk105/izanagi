```text
# fix Unit D 報告

## 1. 赤ごとの対応表

| 項目 | 状態 | 対応 |
|---|---|---|
| F-D1 | partial | token 発行時の保護 signature と実行時の実効 ratio を、同じ identity state 内で照合するよう修正。直接診断は成功したが、正式 pytest は未実走。 |
| F-D2 | partial | 既定 durable policy を callable seam や計測より前へ移動。private helper の暗黙 policy 補完も除去。直接診断は成功したが、正式 pytest は未実走。 |

regressed と判定した項目はない。ただし正式 pytest が collection 前停止したため closed は主張しない。

## 2. 根本原因

F-D1:
- 一次資料 `/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/focus2.log:28-325` では、既定 measure_point の全 4 parametrization が rep 0 件だった。
- `/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/fix_c.md:89` の申告どおり、campaign は合成 rr79／rr23 の表から token を発行する一方、`orchestrator/calibrator/runner.py:417-421` から呼ぶ gate は production 固定表だけで分類していた。
- token が正規発行済みでも rr79／rr23 が「非保護」と分類され、各 rep が spawn 前に例外となっていた。

F-D2:
- 一次資料 `/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/focus2.log:328-365` では、durable root 拒否前に `_forbid_measure` へ到達していた。
- Unit C の `orchestrator/tests/test_s8b_floor_campaign.py:426-436` にあった暗黙 policy 補完が、未指定 policy の負例を明示承認済み経路へ変えていた。
- durable preflight 自体も core の後段にあり、順序保証が局所化されていなかった。

## 3. 変更した file と要点

- `orchestrator/holdout_observation.py`
  - 発行 state が保持する signature の ratio と、正規化済み実行 ratio を identity 検査と同じ lock 内で照合。
  - token 無し経路だけが production 固定中立表を使用する構造に変更。
- `orchestrator/campaign/s8b_floor_campaign.py`
  - durable output root preflight を core 冒頭の非計測 preflightへ移動。
  - cell claim は従来どおり manifest と全非計測 preflight 後、`runner.run()` 直前に維持。
- `orchestrator/tests/test_holdout_observation.py`
  - rr79 向け token が rr23 を認可できず、拒否後も本来の rr79 だけを認可できる回帰を追加。
- `orchestrator/tests/test_s8b_floor_campaign.py`
  - private helper の暗黙 durable policy 補完を除去。
  - durable policy が必要な他の private fixture は明示注入へ変更。既存期待値は変更していない。

docs と所有外 file は編集していない。commit も作成していない。

## 4. token と分類の整合をどう保証したか

- token 発行時の `_IssuedAdmissionState.signature` が有効表の解決結果を保持する。
- `run_once` は正規化済み gflags の実効 `ycsb_rratio` を、その発行 state と直接照合する。
- identity、signature、残回数の検査と減算は `orchestrator/holdout_observation.py:315-338` の同じ lock 内で行う。
- token 無しの分類は `orchestrator/holdout_observation.py:364-373` の production 固定表のまま。
- private signature source は `_run_campaign_core` にだけ存在し、公開 wrapper、CLI、公開 admission API から到達不能。構造固定は `orchestrator/tests/test_s8b_floor_campaign.py:3148-3161`。
- 別 signature の拒否テストは `orchestrator/tests/test_holdout_observation.py:374`。

F-D2 の順序は durable preflight が `s8b_floor_campaign.py:4267-4273`、cell claim が同 `4730-4747`、計測開始が同 `4777-4778`。F-B4 の「claim は非計測 preflight 成功後」を維持している。

## 5. 実走したテスト / 実走できなかったもの

正式 pytest として次の 6 nodeid を投入した。

- `test_rep_integrity_positive_control_default_measure_point[clean]`
- `test_rep_integrity_positive_control_default_measure_point[no_perf]`
- `test_rep_integrity_positive_control_default_measure_point[nonzero_rc]`
- `test_rep_integrity_positive_control_default_measure_point[missing_cycles]`
- `test_floor_default_durable_policy_rejects_external_output_without_side_effects`
- `test_private_signature_token_cannot_authorize_another_private_signature`

結果:
- `--force-dispatch` 2 回: `qstat -Q preflight rc=1`
- 通常判定 1 回: 同じ dispatch infrastructure failure
- pytest collection／実行 nodeid: 0 件

したがって正式には「実装済み・未実走」。

補助確認:
- token 取り違えと durable 拒否順序の限定直接診断: `DIRECT_DIAGNOSTIC_OK`
- `git diff --check`: 成功
- 所有 7 file の AST／NFC／結合文字検査: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし

関連 3 test file 全体は、焦点走行が infrastructure で停止したため未実走。

## 6. 事前登録変異の位置

- M1: 不変
- M2: 不変
- M3: 不変
- M4: 不変
- M5: 不変
- M6: 不変
- M7: 移動
  - 新位置: `orchestrator/holdout_observation.py:374`
  - old 逐語:
    `_consume_holdout_observation_run_once(
        admission,
        effective_ycsb_rratio=ratio,
    )`
- P1: 不変

## 7. 所有外への波及可能性

- `runner.run_once`／`measure_point` の token 無し caller:
  `s1_verify_extime_calibration.py`、`s2_verify_calibration.py`、
  `s3_lock_coverage.py`、`backoff_profile.py`。production 固定表の受理集合は不変。
- consumer test:
  `test_calibrator.py`、`test_plain_runner_coverage.py`、
  `test_ccbench_spawn_sites.py`、`test_s8b_freeze_io.py`、
  `test_s8b_ratified_freeze.py`、`test_trial_registry.py`、
  `test_between_run_floor.py`、`test_campaign.py`。
- `_run_campaign_core` の invalid out_root は、env attestation や injected callable より早く durable error になる。valid policy の経路は不変。
- private helper を共有する floor tests は、durable policy の明示漏れがあれば早期拒否になる。静的確認では既定 policy 負例以外の全 private caller が明示 policy を持つ。

## 8. 閉じられなかった項目と理由

F-D1／F-D2 とも実装と限定直接診断は完了したが、正式 pytest が 3 回とも `qstat -Q preflight rc=1` で collection 前停止したため partial。

`git submodule update --init` は共有 `.git` が read-only で config lock を作れず失敗した。ただし `external/ccbench` は `511c9538e4e8efa54b45cda62e72389ed3b706ec` に展開済みで、本修正の焦点 Python nodeidは submodule build を必要としない。

第 3 巡上限のため追加 fix は行わない。残る作業は infrastructure 回復後の焦点 6 nodeidと関連 3 file 全走による親の最終確認。
```

## 総括

F-D1 と F-D2 の実装修正は完了し、既存期待値は変更していません。  
token は発行時 signature と実行 ratio を同じ identity state で照合します。  
durable 拒否は計測前へ戻し、cell claim の F-B4 順序も維持しました。  
限定直接診断と静的検査は成功しています。  
正式 pytest は dispatch infrastructure failure のため未実走で、両項目を partial と報告します。