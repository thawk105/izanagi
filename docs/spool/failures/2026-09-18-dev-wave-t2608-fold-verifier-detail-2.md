---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2608-fold-verifier-detail
seq: 2
---

## 再発

### F266

- **再発: 2026-09-18** — T-2608の回収で、main基点へ旧waveをmergeした後に同内容のauthor tipを履歴保全目的でmergeした。
  後者ceb258ff7はtrusted親0で、第二親から見ると `M docs/spool/FOLDED.md` があり、landはrc26で拒否した。
  累積tree差分ゼロとspool dry-run、受入25134 passed / 69 skippedを履歴適格性と取り違えた。mainは不動。
  既存対処どおりmain第一親の一括mergeへ組み直す。DW-O23から本Fの一括merge・各親差分確認へ接続し、gateは変更しない。

### F946

- **再発: 2026-09-18** — 上記の修復可能なland拒否に対し、親が次wave禁止を理由に終了し、新contextでの再開をユーザーへ要求した。
  `retryable_same_request=false` は同じ入力の再投入を拒む値で、監査済み成果からの局所修復まで禁じる根拠ではなかった。
  ユーザーの「main landまでやれよ。自己改善よろ」で同じ依頼を継続。DW-STOPへ同一目的の修復と次waveの区別を明記した。
  正式停止の条件、postcondition failureの停止、規律2、rebase/force禁止は維持する。
