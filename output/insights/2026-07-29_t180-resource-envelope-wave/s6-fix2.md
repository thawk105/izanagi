修正完了です。編集は指定された 2 ファイルのみで、commit は作成していません。

- [tools/codex_worker_launch.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-a/tools/codex_worker_launch.py)
- [test_codex_worker_launch.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-a/orchestrator/tests/test_codex_worker_launch.py)

| ID | 判定 | 対応 |
|---|---|---|
| N-1 | closed | 新規 receipt を v2 化。v1 旧 field set と本 wave の拡張 v1 を厳格に識別し、旧 v1 で未定義だった4検査は診断付き skip。 |
| N-2 | closed | `_seal_attempt`・audit・publication 失敗を launcher-error receipt に変換。run 自身が公開した output は除去。wall-clock scope を `launcher_start_to_receipt_fields_finalized` に限定。 |
| N-3 | closed | receipt slot を output 公開前に確保。競合敗者の output は残らない。manifest は費消済み session 台帳なので保持する理由を docstring に明記。 |
| N-4 | closed | M17 は fake worker PID 生存中の manifest 追記を直接検査。M19 は peak latch・terminal mismatch・limit gate に mask されない rollback 単独負例へ再照準。 |

N-1 実 receipt の最終実証:

- `review-a.receipt.json`: `rc=0`、schema v1、新規4検査の skip 診断あり
- `review-b.receipt.json`: `rc=0`、schema v1、新規4検査の skip 診断あり
- `focus.receipt.json`: `rc=0`、既知拡張 v1、skip なし

実走 nodeid:

- `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[True/False]`
- `test_seal_failure_still_writes_launcher_error_receipt`
- `test_post_attempt_audit_failure_still_writes_launcher_error_receipt`
- `test_receipt_publication_failure_removes_output_and_writes_error_receipt`
- `test_complete_receipt_publication_is_atomic_create_only_at_run_callsite`
- `test_manifest_is_appended_while_correlated_session_is_running`
- `test_usage_rollback_alone_is_rejected_without_peak_or_terminal_mask`

焦点実走は `8 passed`。指定全走は最終的に `58 passed in 22.20s`、直接起動 harness も `58 passed`、F42 meta-test は `1 passed` です。最初の全走では既存の fake PID 作成競合が一度だけ発生し `57 passed / 1 failed` でしたが、単独再走 `1 passed`、以降の全走2回はともに `58 passed` でした。

所有外への静的波及可能性:

- receipt JSON を checker 外で直接読む consumer は、schema v2 と新しい `wall_clock_scope` 値への追随が必要です。
- `tools/codex_worker_ledger.py` 側の manifest schema は不変更です。競合敗者の費消 session も manifest に残るため、ledger の session/job 集合には意図どおり現れます。
- T-184 の将来 dispatcher 結線では、新規 receipt が v2 であることを前提にする必要があります。
- `check_codex_output`、events parser、manifest parser、worker termination primitive の interface は変更していません。

`git diff --check`、`py_compile`、`check_codex_agents.py`、`check_docs.py` はすべて成功。所有外ファイルの変更はありません。

## 総括

closed 4 / partial 0 / regressed 0。  
指定全 nodeid: `orchestrator/tests/test_codex_worker_launch.py` — 58 passed。  
焦点 nodeid 8件 — 8 passed。  
実 v1 receipt 3件 — review-a rc=0 / review-b rc=0 / focus rc=0。  
F42 meta-test — 1 passed。  
未了実装なし。実 mutation matrix の本走と統合 commit は親担当です。