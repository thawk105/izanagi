---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1721-a1-paired-reps
seq: 2
---

## 新規

### {{F:tests-run-while-workspace-write-child-edits}}. workspace-write の子が編集中の worktree でテストを走らせ、引き裂かれた木を測った [計測汚染]

- 事象: 段 6 の fix 子 (`sandbox=workspace-write`) が稼働している最中に、親が同じ worktree で
  焦点走を投入した。**148 failed** で戻ったが、直前の同じ file 集合の走行は
  1,083 passed / rc=0 だった。赤は実装の回帰ではなく、編集途中の木を測ったことによる無効な計測である。
- 根本原因: 「計測が走っている worktree は読むだけにする」という既存規律を、変異 harness と
  受入全走にだけ適用していた。実装子・fix 子も同じ worktree の実装 file を書き換え続けるが、
  その向き (子が編集中に親が測る) を禁止として書いた箇所が無かった。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M05` が「変異中は親の編集と worktree へ書きうる子の
  起動を止める」を規定しており、本件はその逆向き (子の稼働中に親が測る) にあたる。
  memory `no-acceptance-run-during-mutation` の本文へ workspace-write の codex 子を明示的に加えた。
- 再発検知: 焦点走・受入の投入直前に、対象 worktree path で一意化した `pgrep -f` を
  codex 子の launcher へ打ち、`.done` の存在を確認する。赤が出たときは、直前の同じ集合の
  緑と件数が桁違いに離れていないかを先に見る。

### {{F:mutation-baseline-rc16-queue-wait}}. 変異 harness の baseline が queue 待ちの既定上限に当たり、緑判定不能で止まった [計測汚染]

- 事象: 変異 probe の baseline 走行が `rc=16` / `artifact_error: receipt scheduler_logs.stdout.path がない`
  で終わり、harness が `status=PARSE_ERROR` として「baseline が緑でない」と判定して停止した。
  実測の所要は 903 秒で、dispatch の queue 待ち既定 900 秒とほぼ一致する。混雑した時間帯の
  infra 失敗であって、変異判定でも実装の赤でもない。
- 根本原因: `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE` の既定 900 秒を、混雑時に広げないまま
  投入した。同じ日の別 wave が計算ノードを多数使っていた。
- 恒久対応: `docs/pegasus-runbook.md` の投入前チェックリストが、変異 harness の `rc=16` を
  infra 失敗と分類し、`timeout_seconds` と同 env の拡大を指示している。本 wave はこれに従い
  5,400 秒へ広げて走り直した。
- 再発検知: 変異 attempt 記録の `rc` と `artifact_error` を見る。`rc=16` は変異結果に数えない。
  所要が queue 待ち上限に張り付いていれば混雑が原因である。
- 併記: **`--resume` は `rc=16` で終わった baseline を再実行しない。** 記録済みの attempt を
  そのまま読み直して同じ判定で止まる。走り直すには `--out` と `--attempt-out` と
  `--scratch-root` を新しい path にした新規走行が要る。
