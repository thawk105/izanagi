# 段 5 author 子の停止の証拠 (逐語の抜粋)

原本は wave 専用 dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/codex/` 配下 (repo 外)。

## 1. launcher と待ち手

- launcher `codex/launch-s5-author.sh` (job-id `t2826-s5-author`、`--stage author --sandbox workspace-write`、`--repo-root` = 子 worktree `author-t2826-probe`、`--max-model-calls 400`)。
- `codex/s5-author.done` の内容: `1`
- `codex/s5-author.log` の全文 (逐語):

```
worktree-commit: committed 31894443efd6c662f9e257d1055a0da0d15ca375
```

- `codex/s5-author.wait.log` の全文 (逐語、`tools/dev_wave_wait.py producer ... --commit-worktree <子 worktree>`):

```
worktree-commit: clean
error: stage=producer-files rc=70
```

## 2. receipt (`artifacts/dev-wave-t2826-shard-plugin-modify-timing/t2826-s5-author/receipt.json`、sha256 `ecf03dbfd9ad8f87ff53f82d6fc46516f378c5b44cc70f139749d04f94e61d0e`、mtime 2026-09-21 14:33:16 JST) の attempt 1 の field (抜粋)

| field | 値 |
|---|---|
| `codex_exit_code` | 1 |
| `failure_class` | `f45_missing_output` |
| `model_calls` | 9 (観測値。同 receipt の `model_calls_semantics=observed_token_count_events`、`possible_unobserved_overshoot=true`、`metering_status=missing`) |
| `output_bytes` | 0 |
| `wall_clock_s` | 513.954562833 |
| `input_tokens` | 425575 |
| `output_tokens` | 16254 |
| `accepted` | false |

## 3. events の末尾 2 行 (`attempt-0001.events.jsonl`、sha256 `f1118f284e8a391070ad02a315baef6a466df93f5167faff91fe2542155f650d`、逐語)

```
{"type":"error","message":"You’ve hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 26th, 2026 7:35 PM."}
{"type":"turn.failed","error":{"message":"You’ve hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 26th, 2026 7:35 PM."}}
```

同 file で `"type":"error"` を含む行は全部で 3 行。残り 2 行は top-level の error ではなく `item.completed` の中の `item.type:"error"` で、起動器 (`tools/codex_worker_launch.py`) が付ける `--dangerously-bypass-hook-trust` に対して Codex CLI が出した警告。本文は逐語で
``"`--dangerously-bypass-hook-trust` is enabled. Enabled hooks may run without review for this invocation."`` (2 行とも同文)。

## 4. 子 worktree に残った書きかけ file (起動器の終端 commit `31894443e`、branch `author-t2826-probe`)

子は検査も報告もしていない (出力 0 byte)。repo には入れず、wave 専用 dir `partial-author/` へ退避した (sha256 は元と一致)。

| file | 行数 | bytes | sha256 |
|---|---|---|---|
| `tools/t2826_modify_timing_probe.sh` | 178 | 7683 | `535257684f545e57becee27f6b2da8b205f329c5f706dcdfa6c2d353405fbb0a` |
| `tools/t2826_probe_plugin.py` | 530 | 20837 | `27348cb3b61bf5105ba6232066794b32ecd5845cd9d2a3b4d01b05b190bbc669` |
| `tools/t2826_modify_timing_aggregate.py` | 584 | 29446 | `a57b43ef1c2eb5e337a3cdeb776b641317241150f00d7722b7d35b42b7774c3e` |
