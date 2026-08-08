段 4「プラン v2」を指定テスト 1 枚だけに実装しました。pytest は基盤障害で起動できなかったため、結果は「実装済み・未実走」です。

### 現行の受理・拒否挙動

変更前後とも、production の受理集合は不変です。

- 受理: 全受理 conjunct が成立した attempt の launcher rc=0。
- 通常の非受理: sealed attempt が不成立なら rc=1。
- preflight・integrity・launcher error: rc=2。
- receipt 同一 path の競争テスト: 2 process の rc multiset が厳密に `[0, 2]`。
- checker rc と receipt 内部の `launcher_rc` は独立した検査として維持。

`tools/codex_worker_launch.py`、`conftest.py`、docs、他テストは変更していません。

### 変更箇所

- [test_codex_worker_launch.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:41)
  - `LauncherReturncodeMismatch(AssertionError)`。
  - byte 上限付き head+tail、SHA-256、総 byte 数、切詰め byte 数、path。
  - receipt と attempt 真理値行、`failed_predicates`、末尾要約。
  - UTF-8 は `errors="backslashreplace"`、総メッセージは16 KiB以下。
- [test_codex_worker_launch.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:340)
  - `CompletedProcess`、`Popen`、in-process、`TimeoutExpired` の共通診断 adapter。
  - unordered `[0,2]` はラベル付き専用経路。
- [test_codex_worker_launch.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:729)
  - 既存 mode を変えず、非0 child rc 注入用 `child_error` を追加。
- [test_codex_worker_launch.py:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:864)
  - `_run_case` に必須の `expected_returncode` を追加し、strict receipt load より前で判定。
- [test_codex_worker_launch.py:927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:927)
  - 指定名の meta-test 7 本を追加。
- [test_codex_worker_launch.py:1129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1129)
  - 既存 launcher rc call site を同じ期待値の helper へ結線。
- [test_codex_worker_launch.py:1765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1765)
  - unordered 2-process 経路。
- [test_codex_worker_launch.py:2205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:2205)
  - F57 既往の direct `Popen` node を共通診断へ結線。

時間予算は `max_wall="3"`、evidence `1.0`、termination `0.05`、poll `0.01`、外側 timeout `10` のままです。

### 期待 rc call site

テスト関数から期待 rc を渡す静的 call site は合計60箕所です。unordered 1 箇所が2値を持つため、process 期待値は61個です。

| 区分 | 構文上の箇所 | process期待値 | rc=0 | rc=1 | rc=2 |
|---|---:|---:|---:|---:|---:|
| 既存 `_run_case` | 33 | 33 | 19 | 11 | 3 |
| 既存 direct / in-process | 15 | 15 | 4 | 3 | 8 |
| 既存 unordered | 1 | 2 | 1 | 0 | 1 |
| 新規 meta-test | 11 | 11 | 11 | 0 | 0 |
| 合計 | 60 | 61 | 35 | 14 | 12 |

既存判定だけでは49 assert 文・50 process期待値、内訳は rc=0:24 / rc=1:14 / rc=2:12 です。

### 削除した assert

削除したのは launcher 実行結果の rc equality だけです。

- `_run_case` rc=0、19件:
  `test_positive_p1_normal_job_is_accepted`、`test_all_repo_policy_reasoning_values_are_accepted`、`test_token_cap_uses_cli_reported_definition`、`test_positive_p3_exact_limit_natural_exit_is_accepted`、6本の `test_check_receipt_*` 準備実行、`test_manifest_refuses_foreign_wave_id` の初回、`test_delayed_thread_and_rollout_are_read_from_byte_zero`、`test_fake_stdout_matches_observed_cli_event_shape`、`test_late_rollout_writer_does_not_change_sealed_receipt`、`test_setsid_escape_is_not_claimed_as_contained`、`test_check_receipt_rejects_unknown_and_duplicate_fields`、`test_check_receipt_rejects_impossible_truth_table`、`test_check_receipt_detects_executable_identity_change`。
- `_run_case` rc=1、11件:
  limit stop、missing metering、token limit、inconsistent、rollback 2件、null token、final drain、missing rollout、missing thread、cached/input malformed。
- `_run_case` rc=2、3件:
  workspace-write retry、manifest append failure、thread ID change。
- direct rc=0、4件:
  parallel jobs の2 process、correlated-session `Popen`、partial receipt replacement。
- direct rc=1、3件:
  SIGTERM ignoring、cumulative limits、max attempts。
- direct/in-process rc=2、8件:
  unknown reasoning、version preflight、in-process error 3件、foreign manifest、outside cwd、unknown base。
- unordered assert 1件:
  atomic receipt publication の2 process `[0,2]`。

安全な理由は、各 equality を同じ期待値で `_assert_launcher_returncode` へ移し、値が一致しなければ専用の `AssertionError` 派生例外を必ず送出するためです。unordered も従来どおり厳密な multiset `[0,2]` を比較します。

削除していないもの:

- checker の `returncode` assert: 9件のまま。
- `receipt["launcher_rc"]` assert: 5件のまま。
- help、receipt field、stop reason、limit、evidence、metering 等の既存 assert。

### 波及可能性

- `_run_case`、`_base_command`、`_write_fake_codex` の他 Python ファイルからの caller は静的検索で0件。
- 共有 fixture の変更なし。新規テストは builtin `tmp_path` / `monkeypatch` のみ使用。
- `REAL_REPO_SERIAL_NODES` への追加不要。実 repo、socket、submoduleを使わない。
- 他 test file の consumer はありません。
- 成功時は rc 比較後すぐ return するため、receipt・stream の診断再読は失敗時だけです。
- direct launcher capture に `errors="backslashreplace"` を付けたため、非UTF-8でも一次 rc 判定を失いません。

### 検査

静的検査は成功しました。

- `python3 -m py_compile orchestrator/tests/test_codex_worker_launch.py`
- 外側 test module と埋込み fake Codex source の `ast.parse`
- 必須7テスト名、全 `_run_case` の期待 rc 指定、時間予算逐語の静的検査
- `git diff --check`
- 変更ファイルが指定1枚だけであることを確認

焦点実走として以下を投入しましたが、pytest 起動前に失敗しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_codex_worker_launch.py -k launcher_failure_diagnostic -q
rc=16
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

したがって、走った nodeid は0件で、緑は主張しません。

### 実装できなかった項目

コード上の未実装項目はありません。未完了なのは実走検証だけです。`conftest.py` の変更は不要でした。段4でscope外とされた dispatch relay E2E、production早期receipt、時間予算変更、48-worker反復は実装していません。

## 総括

- 段4 R1〜R5を指定テスト1枚へ実装した。
- production・受理集合・時間予算は不変。
- 既存50 process判定を同じrc期待値の診断経路へ移した。
- 専用例外、真理値行、failed predicates、16 KiB上限、末尾要約を追加した。
- CompletedProcess・Popen・in-process・TimeoutExpiredを扱う。
- checker rc・receipt内部assertは削除していない。
- 静的検査は成功。
- pytestはdispatch基盤rc=16のため未実走。