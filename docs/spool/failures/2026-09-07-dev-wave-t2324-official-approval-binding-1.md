---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2324-official-approval-binding
seq: 1
---

## 再発

### F102

- **再発: 2026-09-07** — 同じ署名 (rc=1・出力 0 bytes) を **author 子**で観測した。原因は flag では
  なく model call 上限で、`stop_reason=max_model_calls` / `codex_exit_code=-15` /
  `failure_class=f45_missing_output` (100 call・1587 秒)。**この型が既存 3 件と決定的に違うのは、
  報告が 0 bytes でも所有 9 file の編集が完全に残っていたことである** — 親が blob hash 照合で
  確認した。既存の再発検知 (「events 末尾の `turn.failed` で flag か上限かを切り分ける」) は
  consult / review 子だけを名指ししていたため、author / fix 子に適用する動機が弱かった。
  恒久対応の追加: 対象を author / fix 子へ広げ、**上限による中断と分かった場合は再投入の前に
  所有 file を base commit の blob hash と照合する** (`sha1("blob <len>\0" + bytes)` を自 worktree で
  計算して `ls-tree` の値と比べる)。完成していれば再投入せず回収し、完成度の確定を段 6 の
  レビューへ渡す (`DW-O01` の「中断子は未完了と記して保全し、次の子に監査させる」の実行形)。
  重い巡では `--max-model-calls` を先に上げる。
