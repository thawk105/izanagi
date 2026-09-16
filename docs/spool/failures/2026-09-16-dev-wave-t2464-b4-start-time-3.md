---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2464-b4-start-time
seq: 3
---

## 再発

### F185

- **再発: 2026-09-16** — 変異 spec の `timeout_seconds` を 600 秒に置いたが、その時間帯の
  scheduler には他 session の job が 14 本あり、m5 の job が走り始める前に harness の per-run
  timeout が切れて orphan-hold を立て、変異を作業ツリーに残したまま中断した。baseline 1 走の
  実測は 262 秒で、往復の実測からは 600 秒は 2.3 倍の余裕に見えていた。**dispatch の既定
  envelope (queue-wait 900 秒 + overall grace 300 秒) を下回る値は、往復実測の何倍であっても
  混雑で割れる。** 取り直しは 2700 秒 (job walltime 3600 秒の内側) + D612 の queue-wait / grace
  上書きで完走した。同型 4 件目の再発なので、恒久対応として `DW-M07` へ
  「`timeout_seconds` は dispatch envelope 超」を発火段の節に明記した (従来は `DW-M06` の
  上限側だけが書かれ、下限側が操作直前の節に無かった)。

### F818

- **再発: 2026-09-16** — 段 3 のレンズ B が 8 model call・220 秒で
  `Selected model is at capacity. Please try a different model.` を受け、F818 と**同じ署名**
  (出力 0 byte・`f45_missing_output`・`codex_exit_code=1`) で終了した。**原因は枠切れではなく
  一過性の容量不足で、復帰は 5 日後ではなく即時である。** `--job-id` を変えて再投入したら
  同じ prompt で 1 回目に成功した。F818 の恒久対応 (docs-only へ落として実装候補を裁定へ返す) を
  この型へ適用すると、30 秒で直る事象のために wave を 5 日止める。署名だけで分岐せず、
  `attempt-0001.events.jsonl` 末尾の `turn.failed` の**本文**を読んで枠切れと容量不足を区別する。
