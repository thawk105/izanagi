実装は完了していますが、指示どおり pytest は未実走のため、全所見を `partial` としています。docs 編集・commit・既存期待値の変更はありません。

| 所見 | 状態 | 対応 |
|---|---|---|
| FIX-1 | partial（実装済み・未実走） | local violation は hold latch を作らず、rc=2 の停止 sidecar のみ作成。dispatch の latch 経路は維持 |
| FIX-2 | partial（実装済み・未実走） | 一意 token、`repo_root`、`task`、`args` で submission を走行へ束縛 |
| FIX-3 | partial（実装済み・未実走） | before/after inventory、request 読取、束縛の判定不能を非 terminal 停止へ変更 |
| FIX-4 | partial（実装済み・未実走） | local でも既存 hold を collection 前に検出して runner 起動を拒否 |

変更箇所:

- [tools/mutation_harness.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:133): latch の有無を停止情報へ保持。
- [tools/mutation_harness.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:269): local の既存 hold、matched、indeterminate を分離。local から latch producer を除去。
- [tools/mutation_harness.py:1516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1516): request の構造検証と走行束縛を追加。無関係と判定不能を区別。
- [tools/mutation_harness.py:1755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1755): local inventory 失敗を捕捉し、timeout 時の構造化 evidence に変換。一意 token は非空の `PYTHONDONTWRITEBYTECODE` 値として伝播し、bytecode 無効化の意味は維持。
- [tools/mutation_harness.py:2699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:2699): local sidecar に `hold_latched=false`、投入可能性、確認必須、判定状態を記録。
- [orchestrator/tests/test_mutation_harness.py:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:932): FIX-1、FIX-2 の matched 側。
- [orchestrator/tests/test_mutation_harness.py:982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:982): conclusively unrelated な submission の非 violation。
- [orchestrator/tests/test_mutation_harness.py:1018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1018): FIX-3 の inventory 失敗。
- [orchestrator/tests/test_mutation_harness.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1070): FIX-4 の local runner 起動拒否。
- [orchestrator/tests/test_mutation_harness.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1089): dispatch timeout の latch 非回帰。

受理・拒否挙動は次のとおりです。

- local timeout、新規 submission なし: 従来どおり terminal `TIMEOUT`。
- local timeout、明確に無関係な request: 従来どおり terminal `TIMEOUT`。
- local timeout、自走行に束縛済み: terminal record なし、sidecar、rc=2、変異保全、hold latch なし。
- local timeout、証拠取得または束縛が判定不能: terminal record なし、sidecar、rc=2、変異保全、hold latch なし。
- local、既存 hold あり: runner 起動前に停止。
- dispatch timeout: 従来どおり latch、sidecar、rc=2、変異保全。

非 timeout local、dispatch の既存 latch 判定、台帳 schema・status・summary・`LEDGER_SCHEMA` は変更していません。no-touch 2 ファイルも未変更です。既存テストの期待値変更・緩和・skip・削除はありません。

実施した静的検査は AST 解析と `git diff --check` のみで、双方成功しました。pytest は一切実走しておらず、緑は申告しません。親が走らせるべき 14 node は以下です。

- `orchestrator/tests/test_mutation_harness.py::test_hang_risk_uses_short_timeout_records_evidence_and_restores`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_after_dispatch_submission_stops_without_terminal_record`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_ignores_conclusively_unrelated_submission`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_inventory_failure_stops_without_terminal_record`
- `orchestrator/tests/test_mutation_harness.py::test_preexisting_dispatch_hold_blocks_local_runner_start`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_timeout_latches_hold_preserves_bytes_stops_next_and_writes_stop`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_non_timeout_parse_error_is_not_an_orphan_condition`
- `orchestrator/tests/test_mutation_harness.py::test_preexisting_hold_blocks_collection_and_baseline_runner_start[collection]`
- `orchestrator/tests/test_mutation_harness.py::test_preexisting_hold_blocks_collection_and_baseline_runner_start[baseline]`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[False-local]`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[False-dispatch]`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[True-local]`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[True-dispatch]`
- `orchestrator/tests/test_mutation_harness.py::test_timeout_request_recovery_uses_partial_receipt_as_correspondence_source`

作業ツリーは親の staged 差分に fix が unstaged で重なった `MM` 状態です。commit は作成していません。

## 総括

FIX-1〜4: すべて実装済み・未実走の `partial`、`regressed` 判定なし。  
親が走らせるべき nodeid: 14 件。  
残るリスク: 実走未確認、および FIX-4 の既存受理との衝突が親走行で判明した場合は指示どおり差し戻しが必要。