## 変更前の挙動

- current v5 は report / journal の digest、arm execution、stored leaf 群からの aggregate、attempt registry を検査していた。
- 個別 cross-binding leaf は現物から再導出されず、leaf と aggregate を整合させて差し替えた tracked receipt を受理できた。
- legacy v3/v4 も aggregate-only。下流 capability は `require_current_verified_receipt` が v5 のみ受理するため到達不能。

## 実装

- [s8c_acceptance_receipt.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/campaign/s8c_acceptance_receipt.py:4)
  - import 時は completeness verifier をロードしないことを明記。
  - leaf 再導出は current v5 のみ、legacy v3/v4 は aggregate-only、legacy が下流へ到達しない理由を明記。
- [s8c_acceptance_receipt.py:1366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/campaign/s8c_acceptance_receipt.py:1366)
  - report / journal を decode し、journal 親から `run_root` を復元する helper を追加。
  - build 時だけ `output_root=run_root.parent.parent`。
  - completeness verifier は関数内 import。
  - `AutonomousTrialCompletenessError` を cause 付き `AcceptanceReceiptError` へ変換。
  - receipt 内の leaf は再導出入力に使用していない。
- [s8c_acceptance_receipt.py:2026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/campaign/s8c_acceptance_receipt.py:2026)
  - current v5 の全 trial leaf を再導出して照合。
  - mismatch 文言に `trial_id` を追加。
  - legacy 分岐と既存 aggregate gate は変更なし。
- [test_s8c_acceptance_receipt_v2.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:232)
  - fixture report に `"do_build": False` を追加。
- [test_s8c_acceptance_receipt_v2.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:492)
  - 合成 leaf を廃止し、実 report / journal と `verify_s8c_cross_binding` から生成。
- [test_s8c_acceptance_receipt_v2.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1064)
  - 最後の trial leaf と aggregate だけを再構成する負の対照を追加。
- [test_trial_registry.py:1904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/tests/test_trial_registry.py:1904)
  - materialized-build receipt を track し、standalone verifier まで通す正例を追加。

## 実走

全 command が `qstat -Q preflight rc=1`、`child_started=false`、rc=16 で停止した。実行 node は各 0 件で、テスト結果は未判定。

- `python3 tools/run_tests.py orchestrator/tests/test_s8c_acceptance_receipt_v2.py -q`
- 新設 node 単独
- `test_s8c_acceptance_receipt.py -q`
- `test_trial_registry.py -q`
- `test_ccbench_spawn_sites.py -q`
- `test_update_acceptance_duration_ledger.py -q`
- `test_plain_runner_coverage.py -q`
- ledger schema node 単独
- trial-registry node-name 重複検査単独

`queue_state` は観測不能、login-node headroom は最終確認時 0 bytes だったため、直接 pytest は起動していない。

非 pytest 検査結果:

- 変更 3 ファイルの AST parse 成功。
- `git diff --check` 成功。
- U+0300〜U+036F は 0 件。
- cold import 時に completeness module が未ロードであることを確認。
- `subprocess.run` は従来の `<module>._git` 1 箇所のみ。

## 巻き添え 12 node

以下はすべて実装済み・未実走。各 node の結果は同じ dispatch infrastructure failure により未判定。

- `test_v3_requires_cross_binding_receipt_sha256`
- `test_v5_attempt_binding_accepts_all_predeclared_observed_units`
- `test_v5_rejects_attempt_registry_bound_to_another_manifest`
- `test_v5_rejects_attempt_registry_bound_to_another_content_commit`
- `test_v5_rejects_attempt_registry_bound_to_another_effective_commit`
- `test_v5_rejects_registry_first_tracked_after_prereg_commit`
- `test_v5_rejects_second_registry_root_on_another_ref`
- `test_m3_v5_rejects_predeclared_unit_without_final_terminal`
- `test_m3b_v5_rejects_receipt_projection_divergent_from_registry`
- `test_p1_v5_accepts_observed_and_terminal_failure_mix`
- `test_p2_v5_accepts_retryable_failure_followed_by_next_attempt`
- `test_v3_aggregate_is_recomputed_from_trial_leaves`

## 波及可能性

静的に確認した所有外の面:

- production caller:
  - `require_current_verified_receipt`
  - `layer3_report.build_accepted_report`
  - `layer3_report.render_accepted`
- producer:
  - `trial_registry.py` の receipt 発行経路。発行式自体は未変更。
- 共有 fixture:
  - v2 の `_fixture`、`_upgrade_to_current`
  - registry の `_registered_repo`、`_prepare_registered_build_report`、`_accept`
- consumer test:
  - `test_s8c_acceptance_receipt.py`
  - `test_s8c_acceptance_receipt_v2.py`
  - `test_trial_registry.py`
  - `test_layer3_report.py`
- `tools/dev_wave_land.py` の同名関数は別 receipt 用で、本 API の caller ではない。

## meta-test

- test-file 集合: `test_plain_runner_coverage.py` を特定。既存ファイルへの node 追加なので allowlist 更新不要。実走は rc=16。
- node-ID 台帳: `acceptance_duration_ledger.json` と `test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations` を確認。
  - `nodeid_count == len(durations)`、全 duration 有限・非負を静的確認。
  - 新 node は未登録。現行 fail-soft 契約と裁定どおり ledger は編集していない。
  - 実走は rc=16。
- top-level node 名: v2 は 35 関数、trial registry は 193 関数、重複 0 を AST で確認。対応 meta-test の実走は rc=16。
- growth/flaky hold 台帳を検索し、対象 v2 test file の既存 pin は見つからなかった。

## 総括

T-1748 は指定の 3 ファイルに実装済みだが、全 pytest は infrastructure failure により未実走であり、`closed` とは申告しない。親では `qstat` 復旧後に指定 5 file、巻き添え 12 node、新設負例、meta-test を再実走する必要がある。

docs、worklog、commit、index は変更していない。既存の未追跡 `output/insights/2026-09-07_t1748-receipt-leaf-binding/` にも触れていない。