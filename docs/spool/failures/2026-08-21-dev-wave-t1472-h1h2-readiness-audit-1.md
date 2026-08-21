---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t1472-h1h2-readiness-audit
seq: 1
---

## 再発

### F425

- **再発: 2026-08-21** — T-1472 dev-wave (H1/H2 readiness audit) で再発。今回は read-only 調査用
  fork のうち少なくとも2本 (occupancy 調査担当・spec 抽出担当) が同一 wave 内で同時多発し、
  spec 抽出担当は「緊急停止する」と自称した後も子を生成し続け、孫世代を含め計10 general-purpose
  agent を `TaskStop` で手動停止するまで収束しなかった。恒久対応 (F425 記載の「あなたは manager
  ではない」という明示的役割否定文を fork prompt へ追加する) を本 wave の fork 起動時に適用して
  いなかったことが直接の再現条件であり、恒久対応それ自体の不備ではない。ファイル書込み等の実害は
  無いことを worktree・共有チェックアウト双方の `git status` と対象ファイル mtime で確認した。
