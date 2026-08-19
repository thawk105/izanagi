---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1198-c12-stale-closure
seq: 2
---

## 再発

### F35

- **再発: 2026-08-19** — [T-1198] (2026-08-16 entry 585 起票、
  `docs/archive/worklog-phase3-0816-585.md`) が (586) から (684) まで stale のまま carry され
  続けた。従来の F35 型 (完了節への明示漏れ) とは異なる新しい発生角度: 同じ症状 (C12 の
  `machine_checkable` 反転で `UNSATISFIED`/`environment-contract-consumer-absent` を誤って返す)
  を指す**別の task ID ([T-1197]・[T-1202])** が 2026-08-17 の commit
  (`ccb9ee65`/`0862ac11`/`9aee98f3`/`47146d74`) で先に fix・完了節記入されたが、fix した側は
  [T-1197]・[T-1202] だけを名指しし [T-1198] を知らないまま閉じたため、carry 台帳の
  [T-1198] 側との突合せをする者がいなかった。恒久対応 1 (`DW-S01`: 人間手番待ちの前提を
  brief 前に git・実成果物へ照合する) は本件にも有効に働いた (今回の検出経路そのもの) が、
  「同一症状の兄弟 finding が別 ID で fix された」場合の横断照合は `DW-S01` の射程外であり、
  機械防壁は無いまま。
