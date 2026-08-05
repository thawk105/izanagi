---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t244-p4-batch-freeze
seq: 3
---

## 再発

### F106

- **再発: 2026-08-05** — [T-244] P4 batch freeze wave。今度は受入全走ではなく**変異 matrix の走行中**に、
  親が段 7 の spool fragment を作って untracked file を増やした。`tools/mutation_harness.py` は
  runner 実行前の preflight で untracked file を検出して `rc=2` で停止し、**偽の赤ではなく
  fail-closed で止まった**。防壁が機能したので実害は再走の一手間だけである。
  根本原因は F106 と同一で、長い走行を待ち時間とみなし、その間に別の段の作業を worktree 内で進めたこと。
  「計算ノードへ dispatch するから自分の worktree を触っても影響しない」という誤認も同じである。
  本 wave の親は同じ注意を自分の handoff に書いたうえで踏んだ。恒久対応は F106 のまま
  (`DW-O19` の「本走は統合 commit 後に限る」と harness preflight) で、
  **受入全走だけでなく変異本走にも同じ「投入から結果取得までは worktree を触らない」を適用する**
  という読み方を本再発で顕在化する。段を跨ぐ待ち時間には repo 外の作業だけを置く。
