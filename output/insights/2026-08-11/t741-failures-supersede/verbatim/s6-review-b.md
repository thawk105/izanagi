## 所見

### 1. 実 canonical の境界前提をテストが固定していない

- real / must-fix
- 根拠: `orchestrator/tests/test_spool_fold.py:1455` で F2 見出し位置だけを動的取得し、`orchestrator/tests/test_spool_fold.py:1458-1461` では空行なしを assert せず、その位置への splice を期待している。
- 成果物影響: `docs/failures.md` の将来変更で F1/F2 間に空行が追加されてもテストが通り、境界代表性を失う。
- 是正案: `boundary.start()` の直前が空行 1 行だけであることを assert し、空行あり・なしを別ケースとして明示する。

### 2. land 経路では issue code が結果理由から消える

- 疑い / nit
- 根拠: `tools/spool_fold.py:194-197` は `SpoolValidationError` の文字列表現に `Issue.message` しか含めず、`tools/dev_wave_land.py:2265-2269` は例外を汎用理由へ変換する。
- 成果物影響: land の失敗結果だけでは `failure-supersede-shape` 等の新 issue code を識別しにくい。
- 是正案: land の fold failure reason に `exc.issues` の code を含めるテストを追加する。ただし、既存 land エラー契約全体の見直しが必要かは未確認。

既知の `_insert_failure_supersedes` の空行配置問題は、指示どおり再報告しない。

変更対象は許可された4ファイルのみで、docs変更・commitは確認されない。

## 恒真テストの判定

追加テストは以下のとおりです。

- `test_failure_supersede_only_fragment_inserts_at_entry_end_byte_exact`: 性質を固定している
- `test_failure_recurrence_precedes_supersede_for_same_target_byte_exact`: 性質を固定している
- `test_failure_supersede_order_is_deterministic_by_fragment_key_and_item_index`: 性質を固定している
- `test_failure_supersede_body_resolves_cross_ledger_placeholder`: 性質を固定している
- `test_failure_supersede_target_placeholder_is_rejected`: 性質を固定している
- `test_failure_supersede_section_order_and_uniqueness_are_rejected`: 性質を固定している
- `test_empty_failure_supersede_section_is_rejected`: 性質を固定している
- `test_multiline_h3_and_base_failure_supersede_shapes_are_rejected`: 性質を固定している
- `test_failure_supersede_body_shape_and_calendar_date_are_rejected`: 性質を固定している
- `test_failure_supersede_missing_target_is_rejected`: 性質を固定している
- `test_failure_supersede_rejects_duplicate_canonical_target_ids`: 性質を固定している
- `test_failure_supersede_rejects_existing_identical_line`: 性質を固定している
- `test_failure_supersede_rejects_duplicate_line_within_same_fold`: 性質を固定している
- `test_failure_recurrence_and_supersede_identical_line_are_rejected`: 性質を固定している
- `test_failure_supersede_substring_of_existing_line_is_accepted`: 性質を固定している
- `test_failure_recurrence_supersede_misuse_is_rejected_but_prose_mention_is_accepted`: 性質を固定している
- `test_failure_topology_rejects_forged_heading_from_recurrence`: 性質を固定している
- `test_failure_list_marker_neutralizes_heading_if_shape_gate_regresses`: 性質を固定している
- `test_failure_topology_accepts_mixed_new_recurrence_and_supersede`: 性質を固定している
- `test_failure_supersede_replay_guards_exact_and_changed_fragments`: 性質を固定している
- `test_failure_new_and_recurrence_only_output_remains_byte_exact`: 性質を固定している
- `test_failure_supersede_real_f1_boundary_without_blank_line_is_byte_exact`: 恒真ではないが、境界前提の assert 不足
- `test_failure_supersede_real_f196_f197_boundary_is_byte_exact`: 性質を固定している。境界位置は動的
- `test_failure_supersede_real_final_entry_eof_is_byte_exact`: 性質を固定している
- `test_cli_dry_run_reports_failure_supersede_semantic_issue_without_writes`: 実CLI経路を通っており、性質を固定している
- `test_spool_guard_reports_failure_supersede_issue`: 実 `check_docs` subprocess 経路を通っており、性質を固定している
- `test_land_folds_failure_supersede_inside_lock`: 実 plan/apply と lock 内経路を通っており、性質を固定している

pytest は未実走のため、テストの実行結果は判定していない。

## 親が docs へ書くべきこと

- `docs/spool/failures/README.md` に H2 順序 `新規 → 再発 → supersede 追記` を追加する。
- fragment の形式を明記する。

  `- F196 **supersede: YYYY-MM-DD** — <本文>`

- target は literal `F<n>` のみで、`{{F:slug}}` は不可。
- 日付は実在する暦日、本文は空白以外を含む1物理行。
- H3、`base:`、継続行、空節は禁止。
- `再発` と `supersede 追記` の用途を分け、再発節の `- **supersede:` 誤用を禁止する。
- 同一 canonical 行、同一 fold 内の同一 `(target, 本文)` の重複を拒否する。
- `docs/spool/README.md` の fold 対象列挙に、既存 F エントリ末尾への supersede 行挿入を追加する。
- 同一 F に再発と supersede が同時にある場合は、再発を先、supersede を後にする。
- 本 wave の F196 fragment は、F197 で恒久対応済みであることを示す日付付き行にする。

## 総括

consumer 3経路と CLI はコード上正しく接続され、追加テストも大半は恒真ではありません。追加の must-fix は、実 canonical 境界テストが空行条件を固定していない点です。pytest未実走のため、実行上の緑は主張しません。