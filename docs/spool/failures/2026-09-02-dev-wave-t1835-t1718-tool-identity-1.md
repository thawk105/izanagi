---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t1835-t1718-tool-identity
seq: 1
---

## 再発

### F106

- **再発: 2026-09-02** — 受入全走の走行中に、親が段 7 の記録 (worklog / decisions fragment と
  insight 一式) を worktree へ新規作成した。受入は preflight の `prerun-clean` で `rc=70` 停止し、
  テストを 1 件も走らせずに 1 回分を失った。commit ではなく untracked file の作成でも同じ結果になる。
  親は「待ち時間を記録の起草で埋める」つもりでいたが、起草先が repo 内だったことに気づいていなかった。
  **待ち時間に進めてよい独立作業は repo 外に置くものだけである。**
  今回の記録は最終的に受入より前へ commit し直した。
