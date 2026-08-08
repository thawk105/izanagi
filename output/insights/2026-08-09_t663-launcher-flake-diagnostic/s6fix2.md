指定テスト 1 枚だけを修正しました。production・docs・他テストは未編集、commit もしていません。pytest は基盤障害により未実走です。

### F0〜F9 対応表

| Finding | 状態 | 根拠 |
|---|---|---|
| F0 | partial | `_paths` を `paths` へ名前だけ修正。[test_codex_worker_launch.py:2812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:2812) |
| F1 | partial | wiring test が `_run_case`、direct `Popen`、in-process の実 call site を通り、各専用例外の sentinel を検査。[test_codex_worker_launch.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1387) |
| F2 | partial | production と同じ strict loader と `_validate_receipt` を通過した receipt だけを真理値表示。欠落 field・duplicate key・型違い・非有限値を追加。[test_codex_worker_launch.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:222)、[同:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1291) |
| F3 | partial | `lstat`、byte 上限、`open`、`fstat` で regular file を確認。FIFO receipt・FIFO stream・上限超過 stream の一次 rc 保持を追加。[同:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:85)、[同:1554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1554) |
| F4 | partial | receipt 上限を production の16 MiBへ統一。全 attempt を予算内で収録しつつ最終 attempt を先に予約。10 attempt・600 KiB超 valid receipt を追加。[同:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:188)、[同:1600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1600) |
| F5 | partial | manifest 待機中に `poll()` を確認し、終了時は既存 manifest assert より先に診断付き rc 判定を実行。[同:2709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:2709) |
| F6 | partial | 可視 field が成立した非受理を `unrecorded_acceptance_guard` と表示。7 conjunct 同時失敗の全件列挙を固定。[同:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:169)、[同:1511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1511) |
| F7 | partial | hostname、xdist/PBS環境、PID、load average、limits/actuals全体、wall/evidence/termination/poll実値を追加。cgroup/pressureは未収集。[同:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:370)、[同:1219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1219) |
| F8 | partial | 未検証 receipt は `observability_status=insufficient` と raw抜粋だけに限定し、`failed_predicates` と断定表現を出さない。[同:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:222) |
| F9 | partial | 実 launcher を走らせる全7呼出を期待 rc=99へ統一し、実 rc literalへの依存を除去。AST検査では全件確認済みだがpytest未実走。[同:1219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1219) |

`partial` はすべて「実装済み・pytest未実走」の意味です。

### F9 対象一覧

| Meta-test／経路 | 期待 rc |
|---|---:|
| `reports_failed_predicates` `_run_case` | 99 |
| `reports_nonzero_codex_exit_code` `_run_case` | 99 |
| `reports_validator_rejection` `_run_case` | 99 |
| `reports_incomplete_evidence` `_run_case` | 99 |
| `is_wired...` `_run_case` | 99 |
| `is_wired...` direct `Popen` | 99 |
| `is_wired...` in-process | 99 |

残る診断 meta-test は synthetic result のみで、実 launcher は起動しません。

### 検査

- `py_compile`、外側/fake AST、`git diff --check`: 成功
- 7既存名の保持、実 launcher 7呼出すべて期待 rc=99のAST検査: 成功
- 軽量 smoke probe: strict valid/invalid、FIFO非ブロック、10 attempt末尾保持、16 KiB上限を確認
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功
- 焦点pytest: wrapper rc=16、`qstat -Q preflight rc=1`。起動 node 0件
- 差分: `orchestrator/tests/test_codex_worker_launch.py` 1枚のみ

## 総括

- F0〜F9を指定テスト1枚へ実装した。
- production・時間予算・既存の受理集合は変更していない。
- 既存7 meta-test名は維持した。
- commitは作成していない。
- pytestはdispatch基盤障害のため未実走であり、緑は主張しない。