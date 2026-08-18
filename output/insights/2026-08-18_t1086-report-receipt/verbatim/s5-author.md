段 4 裁定の 1〜5 をすべて実装しました。commit、docs、remote 操作は行っていません。状態は「実装済み・pytest 未実走」です。

### 編集ファイル

- `orchestrator/campaign/s8b_oracle_report.py`
  - `ReverifiedFreeze` の exact type と manifest freeze SHA 束縛を追加。
  - store を component ごとに `O_NOFOLLOW` で開き、leaf の `fstat`、regular-file 検査、1 MiB chunk hash を実装。
  - `store_reverification` receipt を WAL 評価後に生成。
  - official `main()` だけが再検証 token を渡す配線を追加。
- `orchestrator/campaign/s8b_oracle_judge.py`
  - report から独立した exact schema 定数と validator を追加。
  - 欠落、空、重複、被覆不足、SHA・state 矛盾、mismatch、missing を `top_reasons` と configuration `unknown` へ伝播。
  - `judge_oracle` の位置引数 1 + keyword 3 を維持。judge CLI も変更なし。
- `orchestrator/tests/test_s8b_oracle_report.py`
  - authority、path、symlink、exact type、freeze 束縛、fstat、chunk hash、production caller の対照を追加。
  - official CLI baseline を実 store rootへ接続し、receipt 全文と token identity を検査。
- `orchestrator/tests/test_s8b_oracle_judge.py`
  - 正常 receipt を共有 fixture に追加。
  - 恒真性、exact keys、coverage、非 canonical path、receipt 欠落の負例を追加。
- `orchestrator/tests/test_s8b_oracle_driver.py`
  - 実 v2 正対照を receipt と determinate judge まで拡張。
  - post-run の置換・削除 A/B を追加。
- `orchestrator/tests/test_s8b_verdict.py`
  - verifier fixture に正常 receipt を追加。
  - receipt 欠落・mismatch が combined verdict まで indeterminate に伝播する E2E を追加。
- `orchestrator/tests/test_s8b_oracle_manifest.py`
  - 手書き canonical golden の report/judge SHA と raw SHA literal だけを更新。

### 追加テスト nodeid

改名はありません。追加 nodeid は以下です。すべて実装済み・未実走です。

- `orchestrator/tests/test_s8b_oracle_driver.py::test_v2_post_run_store_change_is_reported_and_refused[replaced]`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_v2_post_run_store_change_is_reported_and_refused[removed]`
- `orchestrator/tests/test_s8b_oracle_judge.py::test_official_store_reverification_absence_is_indeterminate`
- `orchestrator/tests/test_s8b_oracle_judge.py::test_store_reverification_rejects_non_tautological_receipts[empty-mapping-store-reverification-schema]`
- 同テストの `[empty-cells-store-reverification-cells]`
- 同テストの `[missing-cell-store-reverification-cell-coverage]`
- 同テストの `[duplicate-cell-store-reverification-duplicate]`
- 同テストの `[verified-with-mismatch-store-reverification-state]`
- 同テストの `[unverified-with-all-match-store-reverification-state]`
- 同テストの `[mismatch-with-equal-sha-store-reverification-cell-state]`
- 同テストの `[missing-with-actual-sha-store-reverification-cell-state]`
- `orchestrator/tests/test_s8b_oracle_judge.py::test_store_reverification_requires_exact_keys[outer-extra]`
- 同テストの `[cell-extra]`
- `orchestrator/tests/test_s8b_oracle_judge.py::test_store_reverification_rejects_receipt_cell_outside_schedule`
- `orchestrator/tests/test_s8b_oracle_judge.py::test_store_reverification_rejects_noncanonical_path[absolute]`
- 同テストの `[parent]`、`[control]`、`[backslash]`
- `orchestrator/tests/test_s8b_oracle_report.py::test_official_direct_api_without_reverified_freeze_is_non_certifying`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_rejects_empty_binary_authority`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_rejects_binary_cell_coverage[missing]`
- 同テストの `[extra]`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_rejects_out_of_root_store_path[absolute]`
- 同テストの `[parent]`、`[control]`、`[backslash]`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_rejects_out_of_root_symlink[parent]`
- 同テストの `[leaf]`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_requires_exact_token_and_manifest_freeze_binding`
- `orchestrator/tests/test_s8b_oracle_report.py::test_legacy_manifest_rejects_reverified_freeze`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_expected_sha_comes_from_reverified_freeze`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_requires_regular_leaf_fstat`
- `orchestrator/tests/test_s8b_oracle_report.py::test_store_reverification_hashes_store_in_bounded_chunks`
- `orchestrator/tests/test_s8b_oracle_report.py::test_build_observations_production_caller_is_main_only`
- `orchestrator/tests/test_s8b_verdict.py::test_store_reverification_failure_propagates_to_combined_verdict`

既存の CLI baseline、実 v2 正対照、official exact-key 対照も新 receipt 契約へ拡張しました。

### 所有外への波及可能性

- production caller:
  - `build_observations` は `s8b_oracle_report.main()` のちょうど 1 呼び出しだけ。
  - `judge_oracle` は judge CLI と `s8b_verdict.verify_oracle_verdict` が consumer。
- shared fixture:
  - `_ratified_cli_manifest`
  - `s8b_v2_freeze_fixture`
  - judge の `_observations` / `_asymmetric_observations`
  - verdict の `_oracle_verifier_case`
- consumer test:
  - `test_s8b_oracle_artifacts.py` は optional key を逐語保持するため production 変更不要。
  - `test_s8b_oracle_manifest_contract.py` と `test_official_perf_closure.py` は caller/source 検査の波及候補。
  - `test_s8b_oracle_manifest.py` の source-byte pin 2 件は golden 更新対象。
- `s8b_oracle_artifacts.py`、schema version、n-pilot、certified-selection consumer、台帳は変更していません。

### 受理・拒否挙動

変更前は official report が再検証 token を捨て、post-run の store 置換・削除や forged receipt が oracle 判定へ影響しませんでした。

変更後は次のとおりです。

- 全 store が freeze SHA と一致: receipt=`verified`、従来どおり determinate。
- store 置換・削除・読取不能: report は `mismatch` / `missing` を記録し、judge と combined verdict は indeterminate。
- receipt 欠落、空、部分集合、重複、outer/cell 矛盾、SHA/state 矛盾: judge が拒否。
- absolute、`..`、制御文字、backslash、symlink、非 regular leaf: report が fail-closed。
- authority の空・schedule 不一致、token 型不一致、manifest freeze SHA 不一致: report が失敗し出力しない。
- official direct API の token 省略は非 certifying report のままだが、judge は receipt 欠落で拒否。
- legacy は token なしの従来 report を維持し、judge では既存 `manifest-kind` 理由で拒否。

### PIN_GATE_SPEC

更新済みです。

- `report`: `05011cdb0af5c06c9d3e8303a8c262ae4883558349de7f4b42f93269218764cf`
- `judge`: `0e6276ddcb6cde6e38f781bdbb8df1289520cfcce9653330d2c83a1db20784d3`
- `PIN_GATE_SPEC_SHA256`: `a2228d3179c876201c355d5f5e0531b55e8e0d98519121ea75a7ed5a9fbdf633`

artifacts は未編集です。production serializer は使用せず、AST literal から raw bytes を取り出して再計算しました。

### 未実走・制約

Python AST 構文、judge 署名、CLI 引数不変、production caller 数、golden 自己整合、`git diff --check` は静的確認済みです。pytest は指示どおり実走していません。submodule 初期化は共有 Git 管理領域が read-only で `core.worktree` を更新できず失敗しましたが、対象 Python 実装と静的検査は完了しています。未実装項目はありません。

## 総括

- 段 4 裁定の report receipt、judge gate、resolver、authority 束縛を実装した。
- post-run の置換と削除は oracle・combined verdict の拒否へ伝播する。
- 恒真性、symlink、CLI、caller、combined verdict の対照を追加した。
- judge API と judge CLI は変更していない。
- expected SHA は `ReverifiedFreeze.binaries_by_cell` だけから取得する。
- PIN_GATE_SPEC の 3 literal は最終 source bytes に同期済み。
- docs、worklog、insight、commit、remote は変更していない。
- 全変更は実装済み・pytest 未実走であり、親の受入実測が必要。