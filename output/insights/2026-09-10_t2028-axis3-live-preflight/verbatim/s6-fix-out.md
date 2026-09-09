## 所見の対応表 (closed / partial / regressed)

| 所見 | 状態 | 根拠 |
|---|---|---|
| A-1 transport 例外 retry 不在 | closed | `live_transport` だけを捕捉し、初回 + retry 3 回まで処理。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6890) [test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:1733) |
| A-2 429/503 後の 200 による洗濯 | closed | HTTP response は retry せず、その row を確定。HTTP failure 後の inline success も validator が拒否。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6964) [test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:3125) |
| A-3 production 発行時刻が send 直前でない | closed | `LiveSearchSession` の型・identity 検査後、transport `.send()` の直前に limiter を issue。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:2829) [related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6126) [test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:881) |
| A-4 resume observation の捏造 | closed | WAL intent から再導出する全 interval を `null` に固定。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6413) [test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:3154) |
| A-5 cooldown・limiter state の fail-open | closed | cooldown を既存 `last_issued_at` へ永続化し、欠落 state は WAL 最終 intent から復元。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5884) [related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5980) [test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:3173) |
| A-6 final bundle の retryability 回帰 | closed | retryable tail の非 finalize 判定を `kind == "final"` へ復元。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:3848) [test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:3143) |
| B-1 transport 例外 retry 不在 | closed | WAL に `transport_failed` を commit し、report を落とさず retry・次 row へ継続。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:4178) [related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5345) |
| B-2 materialized pending の resume 不可 | partial | in-process transport failure は WAL commit 後に pending を解消した。一方、intent 後・commit 前の process death は裁定どおり scope 外で、`unconfirmed_attempt_intent` のまま。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5303) [related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:9521) |
| B-3 cooldown 非永続 | closed | DBLP の HTTP 429/503 と transport retry 枯渇の双方で cooldown state を先に永続化。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:7085) [test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:1814) |
| B-4 同一 bundle の 2 process 起動 | partial | fix-ruling §2 の scope 外として未変更。limiter lock と WAL writer 排他は依然別である。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:4929) [related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:5765) |

## 実装した内容 (file:line)

- retry 上限を合計 4 attempt に訂正し、3、6、12 秒／15、30、60 秒をすべて到達可能にした。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:279)
- transport failure は HTTP status を捏造せず、専用 WAL event として commit。4 回まで受理し、5 回目を `bundle_preflight_sequence` で拒否する方式を採用した。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:4178) [related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6501)
- transport 枯渇 row は `unavailable / live_transport_retry_exhausted` として report へ残す。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6452)
- report・bundle validator を「wire attempt 数と HTTP response evidence 数が異なり得る」構造へ対応させた。429/503 の inline retry は拒否する。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:7132)
- production timestamp、resume observation、cooldown 永続化、state 欠落復元、final retryability を修正した。
- F1〜F6 の正負例を追加・訂正した。[test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:881)
- harness の実測 duration を反映し、新設・改名 10 node を正数で収載。台帳件数は 22,170。[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/acceptance_duration_ledger.json:5)

## 実走したテスト (nodeid と結果)

指定 harness の全範囲を最終実走:

```text
orchestrator/tests/test_related_work_search.py
121 passed in 139.60s
```

新設・訂正した主要 nodeid はすべて PASS:

```text
::test_live_session_records_issue_time_immediately_before_transport_send
::test_preflight_retries_live_transport_and_never_retries_http_status
::test_preflight_exhausts_four_dblp_transport_attempts_then_cools_down
::test_preflight_does_not_swallow_non_transport_contract_errors
::test_preflight_wal_accepts_four_transport_attempts_and_rejects_fifth
::test_http_failure_cannot_be_followed_by_inline_success
::test_final_retryable_tail_remains_nonfinalizable
::test_resume_pacing_intervals_are_unmeasured_null
::test_cooldown_and_missing_limiter_state_survive_new_instance
::test_packed_wal_commits_transport_failure_without_pending_intent
```

既存固定期待値も全 file 実走内で維持:

- `wire_attempt_count == 1929`
- `blocked == 193`
- `rows == 2122`
- `len(transport.calls) == 1929`

追加検査:

- AST parse: PASS
- `git diff --check`: PASS
- 変更 file: 許可された 3 file のみ
- catalog: `2,818,599 bytes`
- catalog SHA-256: `7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58`
- ledger: 10 対象 node 全て正数、`nodeid_count == key count == 22170`
- 実時間 sleep: なし

## 波及可能性の静的列挙

- caller: `run_preflight`、preflight resume、`resume_bundle`、`BundleWriter.finalize_preflight`。
- final consumer: `BundleWriter.finalize_run` と final resume の retryable-tail 判定。
- report consumer: `validate_preflight_report`、bundle material 照合、`load_preflight_bundle`、`run_ready`。
- WAL consumer: replay、bundle validation、resume。新しい `transport_failed` event を認識する。
- shared fixture: `catalog`、`catalog_data`、`seal`、`green_preflight_report`、`_FakeTime`、`_packed_preflight_attempt`。
- CLI caller `tools/run_axis3_search.py` は既存 producer／loader へ委譲するため静的な波及先だが、bytes は変更していない。
- `LiveSearchSession._send_with_receipt` は optional callback 追加、`HostLimiter` は optional fallback 追加のため既存 caller 互換を維持している。

## 未実装・未実走として残したもの

- intent 後・commit 前に process が死んだ bundle の回復強化: scope 外。
- 同一 bundle の 2 process 同時起動対策: scope 外。
- transport body ceiling／attempt 全体の wall-clock ceiling: scope 外。
- 実ネットワークへの live preflight: 未発火。production 経路テストは `LiveSearchSession` を通し、送信先だけを test double にした。
- 投影外の repo-wide test、docs 検査、provenance 検査は未実走。
- docs 編集、commit、push は実施していない。

## 総括

F1〜F6 と指定テストを実装し、指定 harness 全 121 node は緑です。レビュー A の 6 件とレビュー B の B-1・B-3 は closed、fix-ruling §2 で明示的に scope 外となった B-2・B-4 は partial のままです。regressed はありません。