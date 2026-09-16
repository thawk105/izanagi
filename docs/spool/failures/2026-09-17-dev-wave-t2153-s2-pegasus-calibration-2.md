---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2153-s2-pegasus-calibration
seq: 2
---

## 再発

### F273

- **再発: 2026-09-17** — [T-2153] S2 較正の Pegasus 実測 wave で、親が同一 wave worktree から計測用の
  generic dispatch 2 本 (gate CLI の NORW / HIGHKEY) を 5 秒差で投げ、2 本目が 1 本目の pending orphan hold
  (`phase: pending-qsub`、receipt 永続化まで残る) を検知して rc=16 (`child_started=false`、`reason=orphan-hold`)
  になった (親の操作ミス)。1 本目 (`2732.nqsv`) は走り切り rc=0、hold は終端で自然に解除、2 本目は再投入
  (`2733.nqsv`) で通った。qdel も hold の手動削除もしていない。別 checkout (detached submit-tree) からの
  同時投入 (`2731.nqsv`) は通った。直列化の義務は `DW-O26` にあるが、同節は受入・テスト前の条件 (18) からしか
  引かれず、計測用 generic dispatch の投入点には届かない。恒久対応として wave 開始時に必ず読む `DW-C00` へ
  「同一 worktree の dispatch は全種直列」を 1 文で足した (入口と重複していた読み込み契約の 1 文を削って予算内に収めた)。
