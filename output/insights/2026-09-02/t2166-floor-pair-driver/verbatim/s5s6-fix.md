## 総括

FIX-RULING の M1〜M10 を二つの許可ファイルだけに実装しました。全項目 `closed`、`partial` / `regressed` はありません。

pytest は login node の headroom 判定が計算ノード dispatch を要求したため、禁止事項に従い child を起動せず停止しました。したがって状態は「実装済み・未実走」です。変更は working tree に残し、git 操作は行っていません。

## M1〜M10 対応表

|項目|状態|実装位置と内容|
|---|---|---|
|M1|closed|[floor_pair_driver.py:1712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1712)、[同:1777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1777)。`measure_fn` seam を削除し、常に `_measure_with_runner` を直接呼ぶ。自己申告 identity field・比較も不要になったため削除。偽装名関数の負例は [test_floor_pair_driver.py:1724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:1724)。|
|M2|closed|[floor_pair_driver.py:1031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1031)。`quality.status=accepted`、非 null saturation、全 cell の records 一致を要求。none mode の意図的拒否を docstring と例外へ明記。env/clocks の冗長 gate はコメント付きで維持。|
|M3|closed|[floor_pair_driver.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:59)、[同:1506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1506)。probe argv を spec から削除し、runner と同じ exact pgrep argv に固定。|
|M4|closed|[floor_pair_driver.py:1437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1437)。`current_site(require_evidence=True)` を使用し、login / suspect / spec site 不一致を出力確保前に拒否。|
|M5|closed|[floor_pair_driver.py:1899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1899)。header 全体、terminal complete、loaded/runtime HEAD、randomization、session plan 順を exact 再検証。|
|M6|closed|[floor_pair_driver.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:963)、[同:1147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1147)、[同:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1803)。source commit 三者一致、live site 一致を実効化。protocol と execution contract は削除。build receipt は実 validator で strict 検証し、receipt・spec・実 binary の SHA-256 と trace=false を束縛。|
|M7|closed|[floor_pair_driver.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1404)、[test_floor_pair_driver.py:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:1084)。production helper 自体を通し、直下の registry / contract のみ fixture 化。compute、OTHER、login、suspect、unknown、曖昧 registry を網羅。|
|M8|closed|[floor_pair_driver.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:487)、[同:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:622)。git timeout と例外正規化、extra_env の PATH / `LD_` 拒否を追加。nm の PATH 未束縛は module docstring と `NOT_PROVEN` に明記。|
|M9|closed|[floor_pair_driver.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:78)、[同:1957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1957)。恒真な count 再検査を削除し、`environment_mismatch` を session status 集合から削除。Counter 比較は exact count 検査として維持。|
|M10|closed|[test_floor_pair_driver.py:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:522) 以降。#1〜#12 を再照準し、#13〜#20 を追加。#6 は strip 済み `/usr/bin/true`、#11/#18 は複数 pair × 複数 sample を使用。|

## Build receipt の根拠

field は削除せず実効化しました。実 schema は `s8b-binary-admission/v2` です。

- schema と exact receipt key: `orchestrator/campaign/s8b_binary_admission.py:39,48-50`
- subject の `binary_sha256` と `trace`: 同 `:61-65`
- exact validator と outer hash: 同 `:317-325`
- subject SHA-256 と trace=false 検証: 同 `:340-352`

driver はこの production validator を実際に呼び、返された subject SHA-256、portable record SHA-256、spec SHA-256を一致させます。別途 `buildcache.assert_binary_sha256` が実 binary bytes を検査します。

## 変異 #1〜#20

以下は各変異を単一理由で赤にするよう再照準した nodeid です。ただし pytest 未実走のため、現時点ではテスト設計と静的配線の対応表です。

|#|対応テスト|
|---:|---|
|1|`test_mutation_01_unknown_key_is_rejected_only_by_exact_loader`|
|2|`test_mutation_02_valid_spec_with_wrong_expected_sha256_is_rejected`|
|3|`test_mutation_03_head_blob_byte_mismatch_is_rejected`|
|4|`test_mutation_04_calibration_projection_gates_have_single_reason_inputs[threads]`、`[workload]`、`[records]`|
|5|`test_mutation_05_real_trace_inspection_call_rejects_before_probe_and_measure`|
|6|`test_mutation_06_live_env_mismatch_rejects_before_output_reservation`|
|7|`test_mutation_07_one_noncomplete_session_makes_whole_floor_missing`|
|8|`test_mutation_08_upper_at_or_above_one_is_preserved_and_not_clamped`|
|9|`test_mutations_09_and_13_forged_production_named_high_measure_is_rejected`。identity 文字列ではなく、高位 seam を再導入する変異へ再照準。|
|10|`test_mutation_10_exclusive_create_rejects_existing_path_before_measurement`|
|11|`test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order`|
|12|`test_mutation_12_production_adapter_passes_all_runner_arguments_and_sinks`|
|13|`test_mutations_09_and_13_forged_production_named_high_measure_is_rejected`|
|14|`test_mutation_14_rejected_calibration_is_rejected_for_quality_only`|
|15|`test_mutation_15_calibration_records_mismatch_is_rejected_for_records_only`|
|16|`test_mutation_16_probe_command_is_not_a_spec_field`|
|17|`test_mutation_17_site_detection_requires_fail_closed_evidence`|
|18|`test_mutation_18_recorded_multiple_pair_sample_order_must_match_plan`|
|19|`test_mutation_19_source_commit_must_equal_loaded_head`。runtime 側は `test_runtime_head_must_complete_source_commit_three_way_binding`。|
|20|`test_mutation_20_extra_env_cannot_control_path_resolution[PATH]`。`LD_PRELOAD` / `LD_LIBRARY_PATH` も同じ gate を検査。|

## テストと検証

pytest nodeid の実行件数は 0 件です。

- 試行範囲: `orchestrator/tests/test_floor_pair_driver.py`
- `tools/run_tests.py` は Pegasus login の headroom 判定後に dispatch を要求。
- 明示した dispatch 拒否 seam により rc=16、pytest child 未起動。
- collection-only も dispatch preflight で rc=16、child 未起動。
- wrapper が作った `output/pegasus-dispatch/d10fd171072b1dabb9ed07b2f31ad0ba` の4ファイルは、今回生成した exact path を確認して削除済み。生成制御ファイルであり復元不可です。

実施済みの非 pytest 検証:

- module import: 成功
- 実 `validate_portable_binary_record`: 成功
- `run_window` signature と削除 dataclass field の投影検査: 成功
- in-memory canonical spec の12 session golden order照合: 成功
- `nm -C /usr/bin/true`: rc=0、no symbols
- `git diff --check`: 成功
- `git status --short`: 許可された二ファイルだけ変更

## Spec schema の縮小

削除した入力 field:

- `provenance.execution_contract`
- `cells[*].protocol`
- `environment.probe_argv`

これらを含む spec は strict loader の unknown key として拒否されます。受理集合は、無照合の execution contract・自己申告 protocol・任意 probe command を含む集合から、それらを持たない閉じた schema へ狭まりました。

さらに以下でも受理集合を縮小しています。

- calibration は accepted、非 null saturation、records 一致のみ。
- source commit は loaded HEAD と runtime HEAD の三者一致のみ。
- site と env_tag は evidence-required live 導出との一致のみ。
- build receipt は genuine `s8b-binary-admission/v2` portable recordのみ。
- extra_env は PATH と `LD_` keyを持てない。
- window artifact は canonical plan 順、complete terminal、完全な headerのみ。

入力 spec 外では `MeasurementResult.measurement_callable` と session record の同 field、生成不能だった `environment_mismatch` session status も削除しました。

## 所有外への波及可能性

静的検索では repository 内に `floor_pair_driver`、`FloorPairSpec`、`floor-pair-spec/v1` の所有外 caller・共有 fixture・専用 consumer test は見つかりませんでした。

潜在的な repository 外 caller には次の変更が必要です。

- `run_window(..., measure_fn=...)` を削除する。
- spec から上記3 fieldを削除する。
- build receipt fixtureを実 `s8b-binary-admission/v2` portable recordへ置換する。
- `current_site` の test doubleは `require_evidence=True` keywordを受け取れるようにする。

自動 consumer への波及候補は、`pytest.ini` の `orchestrator/tests` 自動収集、`test_plain_runner_coverage.py` の全 `test_*.py` 列挙、`test_pytest_collection_config.py` の glob 収集です。専用 test file は引き続き `__main__` harness を保持しています。