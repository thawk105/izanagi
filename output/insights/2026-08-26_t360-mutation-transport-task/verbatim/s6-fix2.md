## 対応表

| DW-O16 所見 | 状態 | 結果 |
|---|---|---|
| `unconfirmed` の赤 | closed | 欠落した `request.json` を読まないよう修正 |
| `confirmed` の赤 | closed | 同上 |
| 同型 fixture の全探索 | closed | 6 関数、parameter 展開後 8 cases |
| request hash 検査 | closed | request がある経路の実 bytes hash を維持 |
| pytest 実証 | partial | 指示どおり未実走 |
| 新たな回帰 | closed | 静的検査では認めず |

## 直した内容

[orchestrator/tests/test_pegasus_dispatch_compute.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:121)

- `_Scheduler._finish()` は `request.json` が実在する場合だけ bytes を読み、SHA-256 を計算する。
- request が無い場合は `request_sha256` field を省き、段 5 以前と同じ result payload にする。
- 既存 assertion は変更していない。

## 同型の赤の探索結果

`_Scheduler` を使い、submission dir に `request.json` を作らないものは、6 test 関数、8 cases だった。

- `test_parent_recovers_unconfirmed_intent_without_expanding_run_qdel` — 2 cases
- `test_intent_recovery_absent_only_keeps_hold_and_never_marks_handled` — 2 cases
- `test_confirmed_intent_recovery_release_failure_is_durable_and_unhandled`
- `test_release_fsync_failure_restores_blocking_hold_and_keeps_intent_unhandled`
- `test_release_rollback_ledger_only_blocks_all_consumers_and_preserves_peer`
- `test_intent_recovery_visible_end_releases_owned_hold_then_marks_handled`

このうち欠落 request のまま `_finish()` の `DONE` 経路へ入るのは、今回赤だった 2 cases だけだった。他の test は `QUE`、`RUN`、`EXT` 経路であり、同じ例外には到達しない。

repo 全体の `orchestrator/tests/test_*.py` も検索した。別 test file に同じ `_Scheduler`、または request bytes を読んで dispatch result の `request_sha256` を合成する相当経路はなかった。

## 検査を弱めていないことの説明

request がある通常経路では、[同 file:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:123) から実際の `request.json` bytes を読み、従来どおり SHA-256 を result に格納する。

既存の正常系 hash 一致 assertion は [同 file:4504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:4504)、不一致拒否 assertion は [同 file:4527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:4527) に残っている。固定 hash や代替値は導入していない。

## 未実走

pytest は指示どおり実行していない。実施したのは AST 構文解析、静的な経路探索、`git diff --check` のみで、いずれも問題なし。commit、`git add`、Web 検索は行っていない。

## 総括

欠落 `request.json` の無条件読み込みを helper 内で閉じ、対象 2 cases の原因を除去した。動的な緑確認は親の実走待ち。