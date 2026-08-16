# Unit I 報告

## 1. observation role の設計

- key を `(freeze_sha256, freeze_holdout_key, configuration_id, ccbench_pin, env_tag, observation_role)` に拡張した。
- 許可値は `floor_campaign` と `oracle_driver` の閉じた 2 値だけ。未知値は fail-closed で拒否する。
- floor は従来どおり 12 cell、各 10 ticket の導出を維持し、claim／admission／attempt 台帳には role field だけを追加した。
- 同じ cell を両 producer が各 1 回観測でき、同一 role での再確保は `O_EXCL` で拒否される。
- 実装位置: `orchestrator/campaign/s8b_holdout_admission.py:64`, `:406`, `:781`

## 2. oracle driver の authority

- exact `VerifiedManifest` と exact `LaunchValidatedFreeze` の組だけを受理する。
- manifest 自身の digest と、manifest が参照する freeze SHA を再照合する。
- cell、holdout、configuration、schedule index は `config_for_block()` が返す manifest 列挙から取得する。
- `ccbench_pin`、`env_tag`、許可 reps は manifest の `run_contract` から導出する。caller に cells や reps の指定口はない。
- claim は共有 durable root へ `O_EXCL` で作成し、その成功後だけ capability を発行する。
- 実装位置: `orchestrator/campaign/s8b_holdout_admission.py:973-1256`、原子的作成は `:1150-1162`

## 3. oracle driver の結線位置

- cell 一括確保: `orchestrator/campaign/s8b_oracle_driver.py:1353-1365`
  - campaign-start、budget、実測ループより前。
- schedule ticket 消費: `orchestrator/campaign/s8b_oracle_driver.py:1494-1513`
  - binding 一致後、`evaluate_fn` 呼び出しより前。
- token の測定伝搬: `orchestrator/campaign/s8b_oracle_driver.py:1526-1566`
- pipeline 転送: `orchestrator/campaign/pipeline.py:404-461`, `:580-602`, `:1123-1128`, `:1225-1241`
  - token がない既存 caller では `measure_point` の呼び出し shape を増やさない。

## 4. 現行の受理・拒否挙動 → 変更後

- 変更前: floor が同じ effect key を確保すると oracle は永久に競合した。
- 変更後: floor と oracle は role ごとに 1 回ずつ受理される。同一 role の再確保は拒否される。
- 変更前: oracle の holdout 実測は tokenless のため subprocess gateway で拒否された。
- 変更後: manifest schedule ticket を実測前に耐久消費し、manifest reps に束縛した token を渡す。
- 未知 role、偽 VerifiedManifest、偽 LaunchValidatedFreeze、manifest／freeze SHA 不一致、ticket 再利用は拒否する。
- 非 holdout 測定と、admission を指定しない既存 `pipeline.evaluate` caller の受理規約は変更していない。

## 5. 実走したテスト / 実走できなかったもの

状態は **実装済み・未実走**。

実走を試みた nodeid:

- `test_observation_role_is_closed_and_separates_two_authorized_producers`
- `test_oracle_admission_uses_verified_manifest_schedule_and_reps`
- `test_official_driver_records_returncodes_through_real_producer_flow`

指定全範囲も投入した:

- `orchestrator/tests/test_s8b_oracle_driver.py`
- `orchestrator/tests/test_s8b_holdout_admission.py`
- `orchestrator/tests/test_s8b_floor_campaign.py`

いずれも `tools/run_tests.py --force-dispatch` が `qstat -Q preflight rc=1`、wrapper rc=16 で停止し、pytest 自体は起動していない。緑は主張しない。

静的検査:

- 変更 5 ファイルの AST parse: 成功
- module import、role key 分離、authority／pipeline signature smoke: 成功
- pyflakes は今回の変更外とみられる既存診断を 3 件報告したため、緑判定には使っていない。

## 6. 所有外への波及可能性

- `pipeline.evaluate` の共有 caller:
  - `s1_direct_comparison.py`
  - campaign loop 系 caller
  - `test_campaign.py`、qualification 系 consumer tests
  - 新引数は keyword-only、既定 `None` なので呼び出し形は維持される。
- floor producer:
  - `s8b_floor_campaign.py`
  - floor claim／ledger の exact-key test と attempt-ledger consumer
- 共有 leaf／gateway:
  - `holdout_observation.py`
  - `calibrator/runner.py`
  - `test_holdout_observation.py`、calibrator tests
- oracle の共有 fixture:
  - real repository の read-only `.git` を汚さないよう、legacy oracle unit helper だけ admission root を隔離した。
  - v2 temporary Git fixture は実共有-root 解決を通す。
- role field を持たない旧 ledger row は fail-closed になる。既存 floor 実走が 0 件という親裁定と整合する。

## 7. [T-524] へ踏み込まずに成立させた根拠

`prereg_generation`、arm、`replicate_slot` は追加・再定義していない。oracle ticket は既存の immutable manifest schedule indexをそのまま使用し、1 ticket の `run_once` 許可数も既存 `run_contract.reps` を読むだけである。新しい実験単位や retry 意味論は導入していない。

docs、逐語、凍結材料は編集していない。commit と git サブコマンドも実行していない。

## 総括

第三 producer である 8b oracle driver を admission 経路へ結線した。  
一回性 key は閉じた observation role ごとに分離され、未知 role は拒否される。  
oracle authority は検証済み manifest と launch-validated freeze に限定した。  
ticket は manifest schedule と実 reps から導出され、測定前に原子的に消費される。  
dispatch 基盤 rc=16 のため、実装済みだが指定テストは未実走である。