---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2464-b4-start-time
seq: 3
---

## 再発

### F818

- **再発: 2026-09-16** — 段 3 のレンズ B が 8 model call・220 秒で
  `Selected model is at capacity. Please try a different model.` を受け、F818 と**同じ署名**
  (出力 0 byte・`f45_missing_output`・`codex_exit_code=1`) で終了した。**原因は枠切れではなく
  一過性の容量不足で、復帰は 5 日後ではなく即時である。** `--job-id` を変えて再投入したら
  同じ prompt で 1 回目に成功した。F818 の恒久対応 (docs-only へ落として実装候補を裁定へ返す) を
  この型へ適用すると、30 秒で直る事象のために wave を 5 日止める。署名だけで分岐せず、
  `attempt-0001.events.jsonl` 末尾の `turn.failed` の**本文**を読んで枠切れと容量不足を区別する。
