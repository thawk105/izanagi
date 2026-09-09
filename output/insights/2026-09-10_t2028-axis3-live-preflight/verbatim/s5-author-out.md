## 変更前の受理・拒否挙動

- host pacing は未実装で、連続送信間隔を制限していなかった。
- WAL は一般的な inline retry を拒否する一方、初回 plan 完了後の最新失敗 stream は回数無制限で再試行を受理していた。
- transport 例外時は pending intent が materialize されず、再開用 bundle が不完全になった。
- 予算・30日締切の拒否は `begin_attempt` 後だったため、未送信 intent が残り得た。
- report v1 は `pacing_observations` を持たず、追加すると schema が拒否した。
- 非 200 → `unavailable`、未解決 factory → `blocked` の分類は変更していない。

## 実装した内容 (file:line)

- [related_work_search.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:73): report v2 と7項目の `pacing_observations` を追加。
- [related_work_search.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:269): host別固定間隔、retry、DBLP cooldown 定数を source literal 化。
- [related_work_search.py:5575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5575): bundle永続化、flock、0600、fake clock/sleeper seam を持つ `HostLimiter` を追加。送信直前の実時刻を記録。
- [related_work_search.py:5801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5801): 状態を変えない予算・締切検査を追加。
- [related_work_search.py:5842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5842): wait → budget check → `begin_attempt` → consume → 発行時刻取得 → transport の順序を固定。transport 例外は pending intent を materialize 後に再送出。
- [related_work_search.py:6183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6183): WAL intent から非関門の pacing 観測を再導出。
- [related_work_search.py:6262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6262): inline retry を受理し、同一 stream の4回目を `bundle_preflight_sequence` で拒否。
- [related_work_search.py:6513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6513): retryable 429/503 の最大3 attempt、固定 backoff、DBLP 2700秒 cooldown を実装。初回 availability 429 の exact-one stop は維持。
- [related_work_search.py:6803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6803): pacing 件数と evidence 順だけを検査し、`observed_interval_seconds` の値では拒否しない。
- [test_related_work_search.py:789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:789): pacing、発行時刻、永続化、wait-before-intent を固定。
- [test_related_work_search.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:881): 予算・締切拒否で intent が残らないことを固定。
- [test_related_work_search.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:940): transport 例外時の materialization を固定。
- [test_related_work_search.py:1321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:1321): DBLP の `44.87` 秒を受理する正例。
- [test_related_work_search.py:1667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:1667): DBLP retry と2700秒 cooldown。
- [test_related_work_search.py:2926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:2926): 3 attempt 正例と4回目拒否。
- [acceptance_duration_ledger.json:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/acceptance_duration_ledger.json:3): 正本 producer で6 node の実測値を追加。すべて正数で、node数は22163。

## 実走したテスト (nodeid と結果)

- `orchestrator/tests/test_related_work_search.py` 全114 node: `114 passed in 69.65s`。
- 新設6 nodeを `-k` で個別範囲実走: 全件成功。
  - `::test_host_pacing_uses_actual_pre_send_time_and_persists_across_limiters`
  - `::test_wire_budget_rejection_precedes_attempt_intent`
  - `::test_transport_exception_materializes_pending_attempt_before_reraise`
  - `::test_preflight_report_observed_interval_is_nonblocking_n3`
  - `::test_preflight_retries_retryable_dblp_three_attempts_then_cools_down`
  - `::test_preflight_wal_accepts_three_inline_attempts_and_rejects_fourth`
- 既存期待値を含む以下も全体実走内で成功。
  - `::test_preflight_200_separates_availability_from_lookup_resolution`
  - `::test_full_catalog_preflight_report_round_trips_without_wal`
  - `::test_preflight_200_can_be_available_but_unresolved_and_continues`
  - `::test_mutation_m6_openalex_429_sends_exactly_one_request_and_checkpoints`
- Meta-test:
  - `test_update_acceptance_duration_ledger.py::test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations`: 1 passed。
  - `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`: 1 passed。
- 台帳 producer `--add-only --check`: `added=0`, `skipped_existing=114`。
- Catalog は `HEAD` producer と byte exact 一致。SHA-256 `7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58`、2,818,599 bytes。
- `git diff --check` 成功。

## 波及可能性の静的列挙

- 所有外 caller は `tools/run_axis3_search.py` の preflight、run-ready、resume。追加した `sleeper` は既定値付きなので呼出し変更不要。
- report は v2 になり source digest も変わるため、親による commit 後の seal 再発行が必要。
- bundle validator、preflight loader、run-ready consumer は source 内の v2 validator を経由する。
- `_run_stream` の直接 caller は対象 test 内だけで、全箇所を更新済み。
- acceptance scheduler は追加された6件の所要時間を利用する。
- CLI、外部 schema 4本、凍結文書4本は `HEAD` から無変更。

## 未実装・未実走として残したもの

- scope外の pending intent 回復強度、body/wall-clock ceiling、resolver、control評価器、DBLP題名lookupは未実装。
- live external request、register、seal再発行、docs、commit、pushは未実施。親の担当として残した。
- 必須の対象コード・テストに未実走項目はない。

## 総括

§3.1〜3.7を指定3ファイルだけに実装しました。既存期待値、catalog bytes、非200分類、初回OpenAlex 429 exact-one境界を維持し、全114 testと関連meta-testは緑です。commitは作成していません。