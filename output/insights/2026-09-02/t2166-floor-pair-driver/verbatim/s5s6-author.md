## 総括

段 4 裁定を、指定された 2 ファイルだけへ実装しました。

- [floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py)
- [test_floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py)

git 操作、既存 file、docs、output 成果物は変更していません。working tree の新規 file は上記 2 本だけです。

実装済み・未実走です。Pegasus のメモリ余裕が local 下限 1 GiB 未満で、計算ノード dispatch も `qstat -Q` 失敗となり、pytest child は一度も開始されませんでした。緑とは報告しません。

## 実装内容

- HEAD tracked blob、期待 SHA-256、作業木 bytes の一致を要求する strict spec loader
- duplicate key、未知・欠落 key、型違い、bool-as-int、非有限、値域外、参照不整合の拒否
- calibration verifier の返却値と env、threads、clock、3-key workload の exact equality
- HMAC-SHA256 rank による決定的な 3-session 計画
- live env 検査後、測定前の最初の変更として exclusive-create JSONL を確保
- candidate/reference の各 session 直前の binary hash と trace symbol 検査
- `measure_point` への固定引数と全 raw sink の production adapter
- pre probe、測定、post probe、追記、fail-closed な残計画記録
- exact 1 回の session ID、raw reps、sink、metadata の finalizer 再検査
- `sample_max/v1` と `max_over_closed_strata/v1` だけの閉じた統計登録簿
- 欠測、非 complete、非有限、非 production、`upper >= 1` の各未生成状態
- module docstring と summary の「証明していないこと」5 項目

## プラン v2 の実装位置

|項目|実装位置|
|---|---|
|1. calibration 意味束縛|[floor_pair_driver.py:944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:944)、既存 verifier 呼出しは同 :969|
|2. trace-disabled 実体検査|[floor_pair_driver.py:1608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1608)|
|3. live env 一致を出力確保前に検査|[floor_pair_driver.py:1369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1369)、呼出順は :1735、確保は :1763|
|4. measurement callable identity|[floor_pair_driver.py:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:268)、production 判定は :1971|
|5. runner 固定引数と理由|[floor_pair_driver.py:1274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1274)、実引数は :1301-1305|
|6. artifact 参照を pairs が所有|[floor_pair_driver.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:709)|
|7. session ID exact 1 回|[floor_pair_driver.py:1827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1827)、count 判定は :1868-1877|
|8. 閉じた統計登録簿|[floor_pair_driver.py:1240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1240)|
|9. 証明していないこと|[floor_pair_driver.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1)、summary は :2103|
|10. anchor 修正|runtime の新機構ではないため既存 file は未編集。runner の実 anchor は adapter docstring :1277-1283、create-only 実装は :1383|

## テスト状況

実走を試みた範囲:

- `orchestrator/tests/test_floor_pair_driver.py` の全 nodeid
- `orchestrator/tests/test_plain_runner_coverage.py` の全 nodeid
- `orchestrator/tests/test_pytest_collection_config.py` の全 nodeid

いずれも runner が child を開始する前に `rc=16` となったため、実行済み nodeid は 0 件です。

静的に確認済み:

- 両 file の `compile()` と AST parse
- `git diff --check`
- 結合文字 U+0300〜U+036F が 0 件
- 禁止 fallback/import/publish API が module にない
- `test_plain_runner_coverage` の実 predicateで、新規 test が `self_runnable=True`、allowlist 不要、file 集合内であること
- working tree が指定 2 file だけであること

## 変異 12 件の単一理由テスト

|変異|赤にするテスト|
|---|---|
|1. 未知 key 素通し|`test_mutation_01_unknown_key_is_rejected_only_by_exact_loader`|
|2. expected SHA 比較除去|`test_mutation_02_expected_sha256_mismatch_precedes_json_parse`|
|3. HEAD blob 一致検査除去|`test_mutation_03_head_blob_byte_mismatch_is_rejected`|
|4. calibration equality 除去|`test_mutation_04_calibration_projection_equality_is_the_rejecting_mechanism`|
|5. trace 検査呼出し除去|`test_mutation_05_real_trace_inspection_call_rejects_before_probe_and_measure`|
|6. live env equality 除去|`test_mutation_06_live_env_mismatch_rejects_before_output_reservation`|
|7. 非 complete の無視|`test_mutation_07_one_noncomplete_session_makes_whole_floor_missing`|
|8. upper の 0.999 clamp|`test_mutation_08_upper_at_or_above_one_is_preserved_and_not_clamped`|
|9. production identity 判定除去|`test_mutation_09_fake_measurement_identity_never_generates_candidate_floor`|
|10. `O_EXCL` 除去|`test_mutation_10_exclusive_create_rejects_existing_path_before_measurement`|
|11. HMAC rank 無視|`test_mutation_11_hmac_rank_has_a_golden_order`|
|12. `require_all_reps=False`|`test_mutation_12_production_adapter_passes_all_runner_arguments_and_sinks`|

## 受理・拒否挙動の変化

実装前は module、loader、CLI、finalizer が存在せず、floor-pair spec を受理する sanctioned surface 自体がありませんでした。

実装後は新規 surface に限り、凍結 bytes、schema、calibration、artifact、live env、全 session、raw reps、production identity の全条件を満たす入力だけを受理します。既存 caller はなく、既存 file も変更していないため、既存機構の受理集合は変えていません。

## 所有外への波及可能性

静的検索では、現時点の caller、共有 fixture、consumer test は 0 件でした。

将来影響を受けうる依存面は次です。

- `calibration_verify.load_verified_calibration` の返却 schema
- `buildcache.assert_binary_sha256` と `_assert_no_trace_symbols`
- `runner.measure_point`、`ScalePoint`、`classify_competing_probe`
- `site_policy.current_site` と `env_contract` registry
- 全 `test_*.py` を列挙する `test_plain_runner_coverage.py`
- 将来 summary を読む floor consumer

材料レポート consumer、既存 floor driver、pipeline、校正 producerへの接続は行っていません。