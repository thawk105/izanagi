## 総括

4ファイルを独立監査し、既存ハンクを採用したうえで追加修正しました。**実装済み・未実走**です。stage・commit・資料移動はしていません。

- 採用：全既存blob/mode照合、移動前の全計画再照合、宛先衝突拒否、保持条件、raw2846件への6ページ索引、旧検査対象を保存した日付直下Markdown検査。
- 修正：資料内部の分割された固定参照も保留対象に追加。
- 修正：案内を日本語化し、一覧の保留理由を短く集約。詳細パスはplan JSONに保持。
- 追加：全操作の`--output`。既存ファイル・入力JSONへの上書きを移動前に拒否し、stdoutにはsummaryだけを出力。証拠配下へのJSON保存も拒否。

静的確認では4ファイルの構文と`git diff --check`が正常でした。HEADに存在する既存checkerテスト定義はAST比較で全件不変です。変更規模は新規helper340行、新規テスト252行、checker追加20行、checkerテスト追加40行です。

親が実走する主要nodeは次のとおりです。

`orchestrator/tests/test_insights_date_layout.py`：

- `test_moves_preserve_bytes_modes_and_retained_entries`
- `test_destination_collision_preflights_before_any_move`
- `test_pins_and_existing_links_are_retained_but_broken_links_are_not`
- `test_raw_pages_cover_all_git_leaves_including_partial_page`
- `test_navigation_keeps_hold_details_in_plan_only`
- `test_internal_split_pin_keeps_original_directory`
- `test_cli_output_plan_apply_verify_roundtrip`
- `test_cli_output_collision_refuses_before_mutation`
- `test_cli_output_cannot_write_into_evidence`
- `test_cli_failed_apply_removes_only_new_output`

`orchestrator/tests/test_check_docs.py`：

- `test_placeholder_guard_date_layout_preserves_old_targets_and_shallow_scope`
- `test_placeholder_guard_date_directory_rejects_symlink_and_non_directory`

関連meta-testは`test_pytest_collection_config.py`と`test_growth_test_holds_contract.py`です。これらを含めテスト・変異検査・実データplan/apply/verifyは未実走です。

所有外ファイルは変更していません。共有fixture、凍結manifest/hash、旧pin、実行記録検査器も変更していません。親の文書差分による既報のL1予算超過と未生成README参照は、本作業では再検査していません。

親が計算ノードで使用するCLIです。各保存先は新規ファイルにしてください。

```bash
python3 tools/insights_date_layout.py --output /tmp/insights-date-plan.json
python3 tools/insights_date_layout.py --apply /tmp/insights-date-plan.json --output /tmp/insights-date-applied.json
python3 tools/insights_date_layout.py --verify /tmp/insights-date-plan.json --output /tmp/insights-date-verified.json
```

apply前に、実データplanの保留集合と移動後件数の確認が必要です。