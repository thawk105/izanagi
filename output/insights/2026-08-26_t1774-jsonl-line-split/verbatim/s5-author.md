## 変更前の受理・拒否挙動

- 正常な LF JSONL は受理。
- `str.splitlines()` が JSON string 内の U+2028/U+2029 を行境界として誤分割し、正当な event を拒否。
- byte 側の `splitlines()` は CR/CRLF を除去するため、本来 CR を拒否する parser に不正入力を黙って通していた。
- byte 上限、object 要求、重複 key、非 JSON、CR、BOM、NUL、非 NFC の拒否と空行 skip は維持。

## 実装 scope

- [events.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1774-jsonl-line-split/orchestrator/codex_roles/events.py:316) の 1 式を `split("\n")` へ変更。
- [codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1774-jsonl-line-split/tools/codex_worker_launch.py:1273) の指定 5 式を `split(b"\n")` へ変更。
- [新規テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1774-jsonl-line-split/orchestrator/tests/test_codex_jsonl_line_split.py:1) に指定 8 test と自走 harness を実装。
- 禁止された `completed.stdout.splitlines()` は未変更。拒否分岐、CR 正規化、厳格性緩和もありません。
- U+2028/U+2029 は escape 表記のみ。対象リテラル文字と U+0300–U+036F の静的走査は 0 件でした。
- `git status` 上の変更は許可された 3 file のみ。stage/commit はしていません。

## 変異 KILL 点検

| 変異 | 赤になる nodeid |
|---|---|
| #1 `events.py` | `test_parse_jsonl_accepts_unicode_line_separators[u2028/u2029]`、`test_drain_stdout_accepts_unicode_line_separators[u2028/u2029]` |
| #2 `_drain_stdout` | `test_drain_stdout_rejects_crlf_terminated_event` |
| #3 `_tail_rollout` | `test_tail_rollout_rejects_crlf_terminated_event` |
| #4 `_recorded_summary` | `test_recorded_summary_skips_crlf_terminated_event` |
| #5 stdout recompute | `test_recompute_metering_stdout_rejects_crlf_terminated_event` |
| #6 rollout recompute | `test_recompute_metering_rollout_rejects_crlf_terminated_event` |

指定 killer に恒真な test はありません。`test_parse_jsonl_still_rejects_malformed_and_oversized_lines` は6変異の killer ではなく、厳格性維持と上限ちょうどの正例を固定する意図的な対照です。

## 実走結果

pytest は未実走です。次の2範囲を `tools/run_tests.py` 経由で試しましたが、いずれも `qstat -Q` の dispatch preflight で rc=16となり、pytest child は起動しませんでした。

- 新規 test＋`test_plain_runner_coverage.py`＋`test_dev_waves_isolation_contract.py`
- 新規 test file 単独

queue state は観測不能でした。`git diff --check` と変更面・禁止文字の静的検査は成功しています。

## 波及可能性

- `parse_jsonl` の consumer である `validate_event_stream`、live stdout、resume stdout 経路に U+2028/U+2029 受理の影響があります。
- rollout tail、記録済み summary、resume metering では CR/CRLF の過受理が拒否へ変わります。
- `AttemptState`／`RolloutState` の定義や共有 fixture は変更していません。
- `test_codex_role_runtime.py`、`test_codex_worker_launch.py`、`test_codex_hooks.py` と2本の meta-test は infra failure により未実走です。
- 裁定どおり、scope 外の `tools/check_codex_hooks.py::_parse_events` にある同型の U+2028/U+2029 問題は残ります。

## 総括

- 指定された6式を LF 専用分割へ置換しました。
- 指定8 test、自走 harness、厳格性の正例・負例を新設しました。
- 6変異すべてに静的 killer があり、#1 の fanout も確認しました。
- 変更は許可された3 fileだけで、commit/stageはありません。
- pytest は dispatch infrastructure failure のため未実走です。
- 残る主なリスクは既存 consumer test 未実走と scope 外の同型欠陥です。