## 変更の要約

**A1 を実装し、差分を working tree に残しました。commit は作成していません。変更は指定範囲内の 4 ファイルです。**

| ファイル | 変更 |
|---|---|
| [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py) | CLI 3 引数・排他、slot identity、machine resolver、durable sidecar、B-5 skip 拒否、rounds=3。追加引数を既定 None/False で接続 |
| [b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/b5_generator_contrast.py) | 新設 864 行。生成器、台帳、分類、系列／block-stock driver、handshake、継承検査、endpoint／score、計時、CLI |
| [test_b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_generator_contrast.py) | 新設 701 行・85 ケース |
| [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_p3_s4_loop.py) | seam テスト 152 行追加。既存期待値は変更なし |

`test_official_perf_closure.py` は変更していません。実際の `_python_has_perf_predicate` が新 module に対して False を返し、inventory 全 7 件も通過しました。

変更前の受理・拒否は以下のとおり確認しました。

- `--b5-slot`：未知 option、rc 2。
- 通常 build の `--run-iteration` without opt-in：`BuildAdmissionError`。既存 `--no-build` は例外。
- `--stock-control` with `--run-iteration`：排他違反、rc 2。

## 既定挙動不変の確認

- 固定 `_DEFAULT_PREIMAGE_BEFORE_PAIR` を変更せず、既定 preimage テストが通過。
- `default_cfg`／`default_perf`／`calibrated_perf`／`check_stop`／`_resolve_duplicate`／`_stock_capability_resolver` は変更前との AST 一致を確認。
- 既定経路では新 search_config key や `run_campaign` kwargs を追加しません。
- `exploration_campaign_layout` は **11 呼出し**、`run_campaign` は **2 呼出し**を維持。
- import 閉包 **49** と既存 guard の焦点テストが通過。
- 新 module の禁止 authority import／呼出し、直接 `run_campaign` 呼出しは **0**。subprocess 実行は `default_runner` の **1 箇所**です。
- hole 文法・検疫・verify→bench の既存実装は変更していません。

## 台帳 schema と handshake の確定形

正本は `header.json` と `events/NNNNNN-<kind>.json`。`series.json` は再生成可能な `{schema, header, events}` view です。header／event は fsync 後に上書き禁止で公開します。

header は cohort、purpose、arm、workload、series、block、mode、repo_head、pin、perf_config、verify_mode、bench_max_rounds、A/B/N_eval、job、allocation deadline、tier0_status、limits を保持します。

以下はイベント形の例です。placeholder は実測値ではありません。

```json
{
  "event_seq": 5,
  "kind": "evaluation-result",
  "ts_utc": "<UTC>",
  "a": 1,
  "b": 1,
  "logical_slot": "search-1",
  "attempt": 0,
  "slot_key": "b5-generator-contrast-v1|t2797-beta-v1|random|write-heavy|1|search|1|attempt-0",
  "proposal_path": "<ledger>/proposals/accepted-1.json",
  "proposal_sha256": "<sha256>",
  "provenance": {
    "arm": "random",
    "preimage": "b5-generator-contrast-v1|random|write-heavy|1|1|0",
    "counter": 0
  },
  "campaign_id": "<campaign-id>",
  "campaign_root": "<campaign-root>",
  "variant": "<variant>",
  "build_attempt_id": "<attempt-id>",
  "wal_sha256": "<sha256>",
  "outcome": "build-failed",
  "failure_class": "candidate",
  "quality": null,
  "fitness_tps": null,
  "anomalies": 0,
  "whiteboard_entry": {
    "iteration": 1,
    "direction": "explore_both",
    "magnitude": "small",
    "result": "fail",
    "delta_pct": null
  },
  "timing": {
    "subprocess_wall_s": 12.0,
    "verify_interval_label": "trace+verifier+周辺処理 区間",
    "build_wall_s": null,
    "verify_intervals": [],
    "verify_total_wall_s": null,
    "verify_missing_reps": 5,
    "verify_truncated": true,
    "bench_wall_s": null,
    "bench_surrounding_wall_s": null
  },
  "note": "",
  "value": 20,
  "submitted": true,
  "returncode": 1,
  "abort_reason": "build-error",
  "bench_payload": null,
  "src_token": "<source-token>",
  "argv": ["<slot argv>"]
}
```

handshake は以下です。

- job：`request-<a>.json` を公開。`a`、`next_evaluation`、`expected_whiteboard`、`current_perf`、`baseline`、`current_perf_source`、`deadline_utc`。
- 親：`inputs-<a>.json = {planner_input, coder_input}` と `proposal-<a>.json`、または `proposal-<a>.rejected.json = {reason}`。
- job：順序・全 field・baseline・診断一致を検査。評価後に `slot-<b>.json` を公開。
- 2700 秒 timeout は `proposal-wait-timeout` で終了し、retry しません。

`endpoint-fixed.endpoint` は選択元 evaluation event。`series-end` に reason、score、score_sessions、必要時 `fallback="pending-block-stock"` を記録します。品質／機械欠測を fallback で埋めません。

## 新 test 一覧

以下の変異は**それぞれ記載の単位テストを実走して kill**しました。M0 は等価対照として生存しました。

| 変異 | テスト名 | 独立した根拠 |
|---|---|---|
| M0 | `test_random_value_independent_known_vector` | コメント追加で結果不変 |
| M1 | `test_integer_log_weights_independent_floor_and_table_hash` | ln2 の固定 40 桁・m₁ 定数。表 hash は独立 atanh 級数で算出 |
| M2 | `test_random_value_independent_known_vector` | 逐語 preimage、実 hashlib、小さい重み表の固定 residue |
| M3 | `test_random_value_rejects_exact_L_without_hash_stub` | 実 digest から M=U₀ を構成し U=L を実現 |
| M4 | `test_sweep_order_independent_hashes` | テスト内の固定 28 点と独立 hash 順 |
| M5 | `test_quality_each_single_condition_is_missing` | rep 欠落・unstable・settled None の単独負例 |
| M6 | `test_submitted_abort_consumes_B_and_history_does_not_stop_next_slot` | submitted＋build abort を 10 評価として計上 |
| M7 | `test_endpoint_tie_is_lower_value_then_earlier_slot` | 同値で値昇順、次に評価順 |
| M8 | `test_series_scores_fresh_sessions_after_endpoint_fix` | 探索 1000 に対して fresh score の中央値 30 |
| M9 | `test_inheritance_order_and_all_fields_checked` | 履歴順序交換・field 改変を拒否 |
| M10 | `test_b5_slot_changes_identity_and_default_kwargs_stay_exact` | 実 main／ident、slot のみ違う 2 identity、固定既定 preimage |
| M11 | `test_machine_no_authority_guard_and_sidecar_before_campaign` | 実 context の観測 wrapper、authority=None、opt-in 無しで到達 |
| M12 | 同上 | `run_campaign` 境界で例外を投げる前に marker 実在確認 |
| M15 | `test_handshake_timeout_ends_without_retry` | 仮想時計で 2700 秒経過、retry 0 |
| M19 | `test_duplicate_skip_ends_series_without_B_or_retry` | fake runner の duplicate-skip で B=0、系列失敗 |

その他の新規テスト名と対象です。

- proposal：`test_machine_proposal_real_schema_and_loader`、`test_machine_proposal_rejects_outside_grammar`。
- slot／品質：`test_slot_keys_separate_physical_attempt_and_logical_kind`、`test_quality_rejects_invalid_numeric_evidence`。
- WAL 分類：`test_classify_slot_actual_wal_and_submission`、`test_classify_pre_start_and_duplicate_are_not_success`、`test_classify_rejects_mixed_or_incomplete_evidence`。
- 計時：`test_timing_uses_adjacent_verify_differences`。
- 予算／retry：`test_preprocess_reject_advances_candidates_to_registered_cap`、`test_retry_same_logical_slot_fresh_attempt_without_AB_increment`、`test_machine_retry_exhaustion_is_missing_without_fallback`、`test_submitted_unresolved_consumes_B_without_retry`、`test_sweep_rejections_continue_after_tenth_candidate`、`test_subprocess_timeout_is_never_machine_retry`。
- 品質／score：`test_quality_missing_keeps_budget_without_retry`、`test_all_quality_missing_has_no_stock_fallback`、`test_score_quality_missing_is_not_fallback_or_retry`、`test_score_anomaly_has_no_reselection`。
- stock／allocation：`test_stock_unestablished_prevents_proposal`、`test_block_stock_five_independent_sessions`、`test_allocation_exhausted_starts_no_new_session`、`test_allocation_is_checked_between_sessions`。
- handshake：`test_handshake_rejection_consumes_A_then_next_request`、`test_handshake_mismatched_inputs_end_before_evaluation`、`test_llm_handshake_valid_inputs_drive_ten_fresh_evaluations`。
- 台帳／CLI：`test_ledger_events_are_immutable_and_view_rebuildable`、`test_slot_argv_literal_contract`、`test_cli_rejects_cross_arm_knowledge_options`、`test_cli_weights_real_subprocess`、`test_expected_inputs_cli_uses_ledger_not_series_view`、`test_default_runner_uses_repo_cwd_and_no_bytecode`、`test_registered_budgets_and_no_cli_overrides`、`test_new_cli_static_bootstrap_and_import_contract`。
- p3 seam：`test_b5_cli_invalid_combinations_rejected`、`test_machine_cli_exclusions_before_external_work`、`test_b5_duplicate_skip_returns_failure_without_restore`、`test_b5_stock_submission_precedes_campaign_exception`、`test_b5_sidecar_no_overwrite`。

## 実走結果

`::*` は当該ファイルの収集対象全 nodeid です。指定の Python harness／`pytest.main` 経由で実行しました。

| 対象 nodeid／選択 | 件数・結果 | rc |
|---|---:|---:|
| `test_b5_generator_contrast.py::*` 最終版 | **85 passed** | 0 |
| `test_p3_s4_loop.py::*` 最終再走 | **576 passed** | 0 |
| 同ファイル、指定 `-k 'b5 or machine or sidecar or preimage or stock_control or calibrated'` | **50 passed**, 526 deselected | 0 |
| `test_official_perf_closure.py` plain harness | **7 passed** | 0 |
| `test_p3_exploration_namespace.py::*`＋wiring-probe の `test_source_segment_helper_matches_stdlib_for_all_static_ifs`／`test_static_candidate_paths_and_driver_specific_guards` | **37 passed** | 0 |
| `test_campaign_import_invariant.py::*`＋`test_p3_build_authority_cli.py::*`＋`test_plain_runner_coverage.py::*`＋`test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` | **47 passed、6 skipped**（既存 growth hold） | 0 |
| hooks／plain-runner の `-k 'module or inventory or coverage'` | **16 passed、1 skipped**、470 deselected | 0 |
| 指定 pin 4 ファイル一括、`-x` | **99 passed、1 failed** | 1 |
| hooks／plain-runner 全走、`-x` | **65 passed、1 failed** | 1 |
| M0 | **SURVIVED、1 passed** | 0 |
| M1〜M12・M15・M19 | **14 変異 KILLED**。M5 は 3 負例、他は各 1 ケース | 各 1 |

残った失敗は以下の 2 件です。

- `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`：wiring-probe の 2 ファイル以外の変更を拒否する検査で、今回指定の未 commit 4 ファイルを検出。
- `test_hooks.py::test_t2146_authority_hardlink_alias_is_denied_in_both_guards`：sandbox 外 `/work/1/SFC/tanab/.izanagi-t2146-hardlink` への fixture 作成が read-only で失敗。

初回の新規テストの Path 型誤りと、既存 guard 式変更による pin 失敗は修正済みです。`git diff --check` も通過しています。

## 波及

- **sort／trigger**：各 module は独自の iteration driver を持ち、今回変更した base 関数への新引数追加は不要。共有する既存状態処理は不変です。
- **`p3_b4_launcher.py`**：`DRIVER_REGISTRY` 経由で既存 main を呼ぶため、既定 None/False 経路を継続します。
- **既存 test caller**：base の直接呼出しは既定値で互換。全 576 件を確認しました。
- **A2**：上記 header／events を正本として読んでください。`pipeline-submitted` は物理 attempt ごとに存在し得るため、イベント数をそのまま論理 B にしないでください。横断 anomaly の失格処理と block-stock fallback 結合は A2 の担当です。
- **A3**：job body から `run-series --arm --workload --series --block --ledger-root --fetchcontent-prebuild-receipt`、または `run-block-stock --workload --block --ledger-root --fetchcontent-prebuild-receipt`。K2 3 引数は llm のみ。単回評価の較正・verify・slot・machine argv は本 module が組みます。
- **親の README 差分案**：上記 CLI、handshake の公開順、A/B と attempt の区別、deadline 不明時の記録、53≤60 論理 session、Tier0 未実装、計時が純 verifier 秒ではないことを追記してください。

## 未了・懸念

- 一括回帰は上記 2 件のため全緑とは報告しません。作業ツリー検査は親の commit 後、hardlink 検査は書込み可能な実行面で再確認が必要です。
- import 制約の既存 growth hold 6 件は未実走です。新 CLI 自身の bootstrap 検査は別の新規テストで通過しています。
- 実機 build／bench、共有 FS での親との実 handshake、A2／A3 統合は未実施です。
- Tier0 は未実装。入力保存・照合は、親の介入不在や実送達を証明しません。

## 総括

**A1 の実装と単位内変異検証を完了しました。最終版は新 module 85 件、既存 loop 全 576 件通過。指定外ファイル・既存期待値は変更せず、差分は未 commit で残しています。**