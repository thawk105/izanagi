実装は完了しましたが、pytest は dispatch 基盤障害により未実走です。変更は [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py) 1 枚だけで、production・docs・他テスト・時間予算は変更していません。commit も作成していません。

### F0〜F8 対応表

未実走のため、実装済み項目も契約に従い `closed` ではなく `partial` としています。

| Finding | 状態 | 根拠 |
|---|---|---|
| F0 | partial | `_paths` を束縛済みの `paths` に修正。[test_codex_worker_launch.py:2922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:2922) |
| F1 | partial | 固定名 wiring test が `_run_case`、`_communicate_launcher`、in-process wrapper の実経路を通り、各専用例外の具体的 `str(exc)` を検査。[test_codex_worker_launch.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1432) |
| F2 | partial | production と同じ strict loader と `_validate_receipt` を通過した receipt だけを真理値表示。欠落 field、duplicate key、型違い、非有限値を追加。[test_codex_worker_launch.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:309)、[test_codex_worker_launch.py:1543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1543) |
| F3 | partial | `lstat`/`fstat`、inode 照合、`O_NOFOLLOW`/`O_NONBLOCK`、256 KiB read 上限を実装。FIFO と上限超 stream の meta-test を追加。[test_codex_worker_launch.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:79)、[test_codex_worker_launch.py:1581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1581) |
| F4 | partial | receipt 上限を production の16 MiBへ統一。全 attempt を予算内で要約し、末尾の決定的 attempt を予約。10 attempt・600 KiB超の valid receipt を追加。[test_codex_worker_launch.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:44)、[test_codex_worker_launch.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:222)、[test_codex_worker_launch.py:1635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1635) |
| F5 | partial | manifest 待機中に `poll()` を確認し、終了済みなら manifest assert より先に診断付き rc 判定。早期 rc=2 の meta-test も追加。[test_codex_worker_launch.py:1282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1282)、[test_codex_worker_launch.py:2827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:2827) |
| F6 | partial | 可視 conjunct が全成立した非受理を `unrecorded_acceptance_guard=true` と表示。複数 conjunct の全件列挙を固定。[test_codex_worker_launch.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:157)、[test_codex_worker_launch.py:1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1666) |
| F7 | partial | hostname、xdist/PBS環境、test PID、load average、receipt limits/actuals、wall/evidence/termination/poll/外側 timeout を出力。[test_codex_worker_launch.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:384)、[test_codex_worker_launch.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:493) |
| F8 | partial | 未検証 receipt は `observability_status=insufficient` と bounded raw のみ。`failed_predicates` と断定表現が無いことを meta-test で固定。[test_codex_worker_launch.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:248)、[test_codex_worker_launch.py:1543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1543) |

### 変更した主な関数

- stream・receipt 診断: `_stream_diagnostic_from_path`、`_load_receipt_strict_regular`、`_receipt_diagnostic`
- 真理値要約: `_failed_predicates`、`_has_unrecorded_acceptance_guard`、`_truth_summary`
- 実行状況: `_runtime_diagnostic`、`_launcher_failure_message`
- rc adapter: `_bounded_failure_message`、`_assert_launcher_returncode`、`_run_launcher_subprocess`、`_communicate_launcher`
- 実 call site: `_run_launcher_in_process`
- fixture/helper: `_repeat_valid_receipt_attempt`、`_wait_for_correlated_manifest`

受理・拒否集合は不変です。wall `3`、evidence `1.0`、termination `0.05`、poll `0.01`、外側 timeout `10` も据え置きです。

### 追加した meta-test

- `test_launcher_failure_diagnostic_rejects_invalid_receipt_shapes`
- `test_launcher_failure_diagnostic_rejects_fifo_stream_without_hiding_rc`
- `test_launcher_failure_diagnostic_bounds_large_stream_reads`
- `test_launcher_failure_diagnostic_preserves_large_final_attempt_summary`
- `test_launcher_failure_diagnostic_reports_all_failed_predicates`
- `test_launcher_failure_diagnostic_marks_unrecorded_acceptance_guard`
- `test_launcher_failure_diagnostic_reports_runtime_context_and_budgets`
- `test_manifest_wait_reports_early_launcher_failure_before_manifest_assert`

段5の固定7テスト名はすべて維持しています。

### assert の削除・置換

既存の動作期待 assert、receipt/checker assert の削除はありません。

F1 の wiring meta-test 内だけ、単一 helper 呼出しを検査していた `assert calls == [completed]` と単一 message assert を、3実経路の型・呼出順・具体的メッセージ検査へ置換しました。これは期待値の緩和ではなく、実 call site への検出力強化です。段5で削除済みの launcher rc equality 群には追加変更していません。

### 検査結果

成功:

- `python3 -m py_compile orchestrator/tests/test_codex_worker_launch.py`
- AST parse、固定7テスト名の存在確認
- `git diff --check`
- 変更ファイルが指定1枚だけであること
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

pytest 焦点走行:

```text
python3 tools/run_tests.py orchestrator/tests/test_codex_worker_launch.py -k launcher_failure_diagnostic -q
rc=16
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

pytest node は0件です。したがって「実装済み・未実走」であり、緑は主張しません。

## 総括

- F0〜F8を指定テスト1枚へ実装した。
- production・docs・他テストは無編集。
- 受理集合と全時間予算は不変。
- strict validation前の真理値断定を廃止した。
- FIFO・symlink・非regular・巨大streamをboundedに扱う。
- 最後の決定的attemptを16 KiB内へ保持する。
- 静的検査と必須checkerは成功した。
- pytestは基盤rc=16のため未実走で、全項目partial。