---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1574-t1529-sort-swo-oracle
seq: 2
---

## 新規

### {{F:same-process-oracle-protocol-capability}}. process外へ出たbytesをtrustedと誤認し、untrusted producerのfd capabilityを見落とした [恒真ゲート]

- 事象: sort SWO oracle のpre-sort snapshotを専用pipeへ書けばcandidateが基準を取り消せないため、親側pre/post比較をmutation防壁として再有効化できると判断した。敵対検査で、candidateが同じprocessのpost pipe fdを所有し、mutation前snapshotと合法relationを偽frameとして書けることが判明した。別TUでsymbolを隠してもfd capabilityは残った。
- 根本原因: 「既に送ったpre bytesを削除できない」と「後続のpost bytesがtrusted producer由来である」を混同し、byte境界だけをauthority境界として扱った。
- 恒久対応: CLAUDE.md規律2と{{D:sort-swo-strong-isolation-before-reactivation}}により、candidateがprotocol fdを所有せずsnapshot対象memoryへの書込みも強制拒否・観測できる境界を実証するまで防壁を再有効化しない。
- 再発検知: 将来設計のnegative controlでcandidateからprotocol fd列挙・writer surface・snapshot対象writeの各到達が不可能または構造化rejectになることを実測し、一つでも到達すれば再有効化を止める。

## 再発

### F1

- **再発: 2026-08-24 (near-miss)** — handoffの最終更新を`date`で実測せず「13:50 JST」と記入した。commit前に実測して「14:13 JST」へ訂正したためcanonicalへの誤記は回避した。恒久対応は既存どおり、時刻を書く1回ごとに`date`を実行する。
