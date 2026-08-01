# T-180 段 1 前提実測 probe package

段 1 で「codex worker job に資源封筒を掛ける seam が実在するか」を確かめた実走の記録。
段 3 敵対相談 A / B の指摘 (probe が監査不能・過大一般化) を受けて再構成した。

## 射程 (意図的に狭く述べる)

ここで示せるのは **codex-cli 0.146.0 の本機 1 実走で観測できた seam** だけである。
「唯一の live seam」という段 1 brief の書き方は過大であり、
**「本 probe で観測できた live seam は rollout tail だけだった」**へ縮小する。
buffering・負荷・CLI 版差・filesystem 差での一般性は**証明していない**。
この不確実性は実装側で fail-closed に吸収する (plan v2 の R1 / R2)。

## 実行環境

- `codex --version` = `codex-cli 0.146.0`
- executable = `/home/SFC/tanab/.local/bin/codex`
- `CODEX_HOME` 未設定 → rollout root = `~/.codex/sessions`
- 実行 cwd = 本 wave の worktree (`.claude/worktrees/dev-wave-t180-resource-envelope`)
- probe1 / probe2 とも `-m gpt-5.6-sol -c model_reasoning_effort="low" -s read-only --json`

## probe1 — session 束縛の実在

`prompt.txt` を 1 turn で返させただけの最小実行。

| 観測点 | 値 |
|---|---|
| stdout `thread.started.thread_id` | `019fadcd-a610-76e2-ab1e-57440d35d795` |
| rollout `session_meta.payload.session_id` | 同上 (一致) |
| rollout filename | `rollout-2026-07-29T21-16-03-019fadcd-a610-76e2-ab1e-57440d35d795.jsonl` (一致) |
| stdout `turn.completed.usage` | input 16,586 / cached 0 / output 11 |
| rollout 最終 `total_token_usage` | 同上 (一致) |

→ 起動した job と rollout を **session_id で決定的に束縛できる**。
cwd 部分一致 (T-179 の限界) に依存しない受理集合が作れる。

## probe2 — live 可読性

4 step の shell 実行を挟ませ、複数 model call を発生させた実行 (`prompt2.txt`)。
`poll_probe2.sh` 相当の poller で 2 秒間隔に stdout 行数・rollout 行数・
`token_count` event 数を観測した (`liveness.tsv`)。

| elapsed_s | stdout_lines | rollout_lines | token_count_events |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 2 | 2 | 2 | 0 |
| 6 | 2 | 2 | 0 |
| 8 | 2 | 10 | 0 |
| 12 | 5 | 15 | 1 |
| 20 | 7 | 18 | 2 |
| 29 | 9 | 21 | 3 |
| 37 | 11 | 24 | 4 |
| 39 | 13 | 28 | 5 |

- rollout の `token_count` は **実行中に逐次増えた** (12/20/29/37/39 秒)。
  → 実行中に model call 数と累積 usage を読める。
- stdout 側の usage は **`turn.completed` の 1 回だけ**で、実行中には来ない。
  → 実行中の停止判断には使えない。終了時の判定には使える。

| 観測点 | 値 |
|---|---|
| thread_id | `019fadce-d927-7681-88fa-3cd329a66a90` |
| stdout `turn.completed.usage` | input 84,667 / cached 64,512 / output 299 |
| rollout 最終 `total_token_usage` | 同上 (一致) |
| T-179 定義の `cli_reported` (`input - cached + output`) | 20,454 |

## 既知の欠落 (段 3 の指摘、是正済み / 未是正)

- **是正済み**: `liveness.tsv` に混入していた単独 `0` 行 (`grep -c` の fallback `echo 0` に由来) と
  末尾の 1 列行 `TID=...` を除去し、4 列契約に揃えた。生の初回観測は
  `liveness-raw.tsv` として残す (一次資料を書き換えない、F1)。
- **未是正 (意図的)**: poll 粒度は 2 秒であり、「thread_id が起動直後に出る」ことは測っていない。
  言えるのは「2 秒後の最初の観測時点で既に出ていた」だけである。
  実装は ID 未到来・遅延・変化を fail-closed で扱う (R5 / R13)。
- **未是正 (scope 外)**: buffering や CLI 版差での再現性は 1 実走では示せない。
  実装は metering evidence 欠落を非採用にすることで吸収する (R2)。

## ファイル

| file | 内容 |
|---|---|
| `prompt.txt` / `prompt2.txt` | 投入した prompt (逐語) |
| `events.jsonl` / `events2.jsonl` | stdout `--json` event 列 (逐語) |
| `out.md` / `out2.md` | `-o` の最終 message |
| `err.log` / `err2.log` | stderr |
| `liveness.tsv` | 4 列に整形した観測列 |
| `liveness-raw.tsv` | 初回観測の生ファイル (整形前) |
| `rollout-digest.json` | 両 session の rollout 参照・sha256・token_count 時系列 |
| `reproduce.sh` | 再現手順 |
