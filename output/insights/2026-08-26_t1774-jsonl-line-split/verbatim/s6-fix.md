## 修正内容

[test_codex_jsonl_line_split.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1774-jsonl-line-split/orchestrator/tests/test_codex_jsonl_line_split.py:12) だけを変更しました。

- repo root の `sys.path` bootstrap を repo import より前へ追加。
- 2 箇所の parametrize に `"\u0085"` / `u0085` を追加。
- `_recorded_summary` の負例を、`session_meta` は LF、`turn_context` だけ CRLF に変更。
- rollout metering の負例も、`session_meta` は LF、`turn_context` だけ CRLF に変更。
- U+0085 / U+2028 / U+2029 のリテラル文字は 0 件です。
- production、docs、共有 fixture、他テストは変更していません。commit もしていません。

## 実走結果

コマンド:

```text
python3 orchestrator/tests/test_codex_jsonl_line_split.py
```

結果:

```text
rc=0
collected 12 items
12 passed in 0.43s
```

0 件実行ではなく、12 test node が実行されています。

## 6 式の killer nodeid 完全集合

disk 上の production を変更せず、各式を process 内だけで `splitlines()` に戻して確認しました。

1. `events.py` の `text.split("\n")`

```text
orchestrator/tests/test_codex_jsonl_line_split.py::test_parse_jsonl_accepts_unicode_line_separators[u0085]
orchestrator/tests/test_codex_jsonl_line_split.py::test_parse_jsonl_accepts_unicode_line_separators[u2028]
orchestrator/tests/test_codex_jsonl_line_split.py::test_parse_jsonl_accepts_unicode_line_separators[u2029]
orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_accepts_unicode_line_separators[u0085]
orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_accepts_unicode_line_separators[u2028]
orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_accepts_unicode_line_separators[u2029]
```

2. `_drain_stdout` の `complete.split(b"\n")`

```text
orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_rejects_crlf_terminated_event
```

3. `_tail_rollout` の `complete.split(b"\n")`

```text
orchestrator/tests/test_codex_jsonl_line_split.py::test_tail_rollout_rejects_crlf_terminated_event
```

4. `_recorded_summary` の `raw.split(b"\n")`

```text
orchestrator/tests/test_codex_jsonl_line_split.py::test_recorded_summary_skips_crlf_terminated_event
```

5. `_recompute_attempt_metering` の `closed.split(b"\n")`

```text
orchestrator/tests/test_codex_jsonl_line_split.py::test_recompute_metering_stdout_rejects_crlf_terminated_event
```

6. `_recompute_attempt_metering` の `raw.split(b"\n")`

```text
orchestrator/tests/test_codex_jsonl_line_split.py::test_recompute_metering_rollout_rejects_crlf_terminated_event
```

式 1 は 6 failed / 6 passed、式 2 から 6 は各 1 failed / 11 passed でした。

## 恒真化と波及可能性

恒真になったテストはありません。`test_parse_jsonl_still_rejects_malformed_and_oversized_lines` は6変異の killer ではありませんが、既存の拒否契約を検査する裁定済みの冗長 gate のままです。

静的な波及可能性は次のとおりです。

- 所有外 caller: production symbolや呼出契約を変更していないため、新たな実行時波及はありません。対象テストは owner 側の private helper に直接依存するため、将来の signature 変更には追随が必要です。
- 共有 fixture: `conftest.py` や共有 pytest fixture は未変更です。使用した `_jsonl`、`_rollout_events`、`_sealed_attempt` は対象 module 内だけの helper です。
- consumer test: U+0085 の追加で parse と stdout の consumer node が各 1 件増えました。CRLF fixture の差し替えは対応する 2 node だけに閉じています。
- meta consumer: plain-runner 系の検査は bootstrap 成功を観測する可能性がありますが、本段では親の担当範囲として実走していません。
- scope 外の `tools/check_codex_hooks.py::_parse_events` に残る同型問題は未変更です。

## 総括

- 裁定済みの 3 修正を対象テスト 1 file だけへ反映しました。
- 直接実行は rc=0、12 件実行、12 件成功です。
- 6 式すべてを個別の in-memory 変異で kill し、恒真化はありません。
- production、docs、他テストは変更せず、commit もしていません。
- 残るリスクは scope 外の同型 reader と、親が行う横断テスト未実走です。