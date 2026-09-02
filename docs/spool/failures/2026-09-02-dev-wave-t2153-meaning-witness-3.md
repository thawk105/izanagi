---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2153-meaning-witness
seq: 3
---

## 新規

### {{F:mutation-dispatch-orphan-hold-two-kinds}}. 投入の保留ファイルは 2 種類あり、片方だけ片付けると同じ理由で無限に弾かれる [手順漏れ]

- 事象: 変異走行が 6 回続けて起動前に中断した。中断のたびに親が規約の復旧順序 (対象 request が
  qstat から消えたことを確認 → dirty を復元 → clean/HEAD 確認 → 保留削除) を実行して再投入したが、
  同じ理由で 45 秒後に弾かれ続けた。投入自体が一度も成立しなかった。
- 根本原因: 保留ファイルは 2 系統ある。`output/pegasus-dispatch/orphan-hold.json` (harness 側) と
  `output/pegasus-dispatch/orphan-holds/<request_id>.json` (投入 request 単位)。親は前者だけを
  消していた。後者に終端済み request の保留が残り、harness はそれを見て起動を拒否していた。
  中断メッセージが名指しする `hold path` は前者だけなので、メッセージに従うと後者へ到達しない。
- 恒久対応: 復旧では両系統を列挙し、それぞれの request が qstat から消えたことを確認してから
  削除する。片方の不在を全体の不在の根拠にしない。手動 `qdel` は使わない (F47 のラッチを武装させ、
  解除がユーザー手番になる)。本 wave はこの手順を `verify_mutation_diff.py` と復旧ループへ実装し、
  想定外の dirty・HEAD 不一致では何も消さずに停止する fails-closed 検査を置いた。
- 再発検知: 中断後に `orphan-holds/` の残件数を数え、0 でなければ再投入しない。
- 併発: 最初の中断は、親が provenance 監査と変異 harness を同じ worktree から並行投入したことが
  原因だった。`DW-O26` が「同一 worktree からの dispatch は全種を直列にする。並行投入は
  orphan hold で rc=16 になる」と既に書いており、規約の欠落ではなく遵守の失敗である。
- 被害: 実装・成果物への影響なし。1 回だけ変異が適用されたまま止まったが、残差分が登録済み変異
  そのものであることを照合してから復元した。
