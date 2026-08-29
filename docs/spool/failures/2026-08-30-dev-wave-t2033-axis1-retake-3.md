---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-30
wave: dev-wave-t2033-axis1-retake
seq: 3
---

## 新規

### {{F:waiter-reports-completion-while-child-lives}}. 待ち手が生存中の子に対して完了を返した [恒真ゲート]

- 事象: 1 wave の中で 8 回以上、背景の待ちが「完了」を返したのに、待っていた `.done` が
  存在せず子は生きていた。`tools/dev_wave_wait.py producer` は
  `/proc/<pid>/stat を読めないため pid-only へ縮退します` を出して戻り、素の
  `until [ -f <done> ]; do sleep N; done` を背景投入した場合も同じく数十秒で「完了」になった。
  子の生存は `ps -eo args` で確認しており、その後 `.done` は正しく現れた。
- 根本原因: 未特定。**待ち手ツール固有ではない** — ツールを使わない素の bash ループでも同じ
  現れ方をしたので、背景タスクの生存判定そのものが疑わしい。本 wave は原因の切り分けまでは
  行っていない (観測の記録である)。
- 影響: 待ち手の「完了」を根拠に次段へ進むと、**未完成の成果物を統合する。** 実際に本 wave では
  子の途中出力を読みかけた場面が 1 度あり、`.done` 不在で気づいた。
- 恒久対応: `docs/dev-wave/core.md` の `DW-C00`「完了は `.done` 非空で決める」と
  `docs/dev-wave/operations.md` の `DW-O01`「完了は `.done` と exit code だけで判定し、
  grep も通知も判定にしない」が既に防壁である。**本 wave はこの規律だけで 8 回すべてを弾いた。**
  規律を足すのではなく、既存規律が実際に効いた実測として残す。
- 再発検知: 待ちが戻った直後に `.done` の実在を確かめる手順を守る限り、同じ形で顕在化する。
  「待ちが完了を返した」だけを進行の根拠にした瞬間に破れる。
