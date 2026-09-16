## 実装

[test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2117-legacy-bytes-removal/orchestrator/tests/test_codex_reasoning_ab.py:3569) だけを変更しました。

- 既存 m2 正例を残し、歴史 rollout・SHA 依存を合成入力へ置換。
- 専用 helper と mismatch 負例を追加。
- 実関数へ委譲する wrapper で経路・順序・比較入力を観測。消費した generator は実体化したリストを渡します。
- 負例は最初の path の追加側だけを変更し、rc・理由を完全一致で検査。
- SHA は row 追記後の全 bytes から計算し、`verify_source_sha=True` の既定を維持。

既存例は一時 repo 作成が 2417 行、定数差替えが 2461–2462 行でした。production・docs・登録簿は変更せず、commit も作成していません。

## 検査

`git diff --check` と AST 構文・定義比較は成功。既存定義の変更は正例だけ、追加は helper と負例、削除はありません。

以下を `tools/run_tests.py` 経由で試行しました。**両走行とも rc=16、pytest 未起動**です。

| 範囲（各項目は `file::node`） | 対象 node |
|---|---|
| `orchestrator/tests/test_codex_reasoning_ab.py` | `test_m2_production_golden_requires_both_routes`、`test_m2_production_golden_rejects_route_mismatch` |
| 同上 | `test_historical_rollout_guard_all_pins_present_does_not_skip`、`test_historical_rollout_guard_reports_missing_session`、`test_historical_rollout_guard_does_not_hide_sha_mismatch` |
| `orchestrator/tests/test_real_repo_serialization.py` | `test_real_repo_group_collection_exactly_matches_canonical_nodes` |
| `orchestrator/tests/test_acceptance_schedule_order.py` | `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` |
| `orchestrator/tests/test_update_acceptance_duration_ledger.py` | `test_add_only_preserves_existing_entry_bytes_and_excludes_frozen_nodes` |

原因は dispatch の `qstat -Q` が socket 作成制限で失敗したことです。全テスト走・変異実測は行っていません。

## 挙動と波及

変更前の m2 は歴史 rollout 不在時に skip し、存在時は比較到達と歴史 SHA を要求していました。変更後は合成二経路の一致を受理し、1 path の不一致を所定の例外で拒否する構成です。production 無変更により、その受理・拒否条件は変更していません。歴史 patch との統合保証を外す点は裁定済みの代償です。

静的な波及候補は次のとおりです。

- 所有外 caller：production の関数・定数は変更せず、差替えは function scope 内。
- 共有 fixture・consumer：両 node は `tmp_path` / `monkeypatch` のみ使用し、共有 fixture 閉包を増やしません。
- 登録簿・所要台帳：新 node の collection 追加は exact 集合検査と被覆率検査の確認対象。登録変更が必要な根拠は見つかりませんでした。
- guard 3 本、source-bound test、歴史記録は維持しています。

## 総括

実装済み・未実走です。対象 1 ファイルに合成正例・mismatch 負例・専用 helper を実装しました。  
実走した pytest nodeid はありません。上記 8 node の起動試行は環境エラー rc=16 で停止しました。  
静的検査は成功。テストの赤・緑および変異検出は未確認のまま残っています。