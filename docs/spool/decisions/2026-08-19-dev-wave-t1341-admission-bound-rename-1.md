---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t1341-admission-bound-rename
seq: 1
---

## {{D:wall-clock-admission-bound-rename}}. max_wall_clock_s を wall_clock_admission_bound_s へ改名する

**決定:** receipt の `limits.max_wall_clock_s` を `limits.wall_clock_admission_bound_s` へ改名する
(CLI flag `--max-wall-clock-s` → `--wall-clock-admission-bound-s`、
`--expect-max-wall-clock-s` → `--expect-wall-clock-admission-bound-s`、定数
`DEFAULT_MAX_WALL_CLOCK_S` → `DEFAULT_WALL_CLOCK_ADMISSION_BOUND_S` を含む)。挙動は変えない。

**理由:**

- D498 と /rulings 全件 第 7 回裁定が「max_wall_clock_s は receipt の admission bound である」と
  明記して閉じ、「誤解を生んだのがこの名前自身であるため、受理上限であることが名前から分かる
  形にする」ことを条件とした。物理 hard cap・外部 watchdog は絶対規律 5 に触れるため不採用。
- `tools/codex_worker_launch.py` 自身が既に「admission」語彙を実装で使用済みだった
  (`site="retry_admission"`、コメント「late admission gate」「新しい admission を表さない」)。
  裁定の「admission bound」という語をこの既存語彙へ直結させ、新語を持ち込んでいない。
- sibling の `max_model_calls`・`max_cli_reported_tokens`・`max_attempts` は `max_` prefix を
  保つ。誤解が生じたのは時間ベースの wall-clock だけであり (カウント値は物理即時停止と誤読
  されにくい)、`max_` と `bound` は同義反復になるため wall-clock 側だけ `max_` を落として形を
  変え、他の 3 つと性質が違うことも名前で示した。

**却下した選択肢:**

- `max_` prefix を保ったまま `_admission_bound` 等を足す (例: `max_wall_clock_admission_bound_s`)
  — 「max」と「bound」が同義反復になり、かえって読みにくい。
- 物理 hard cap・外部 watchdog の新設 — 裁定で明示的に却下済み (新機構を要し絶対規律 5 に触れる)。
