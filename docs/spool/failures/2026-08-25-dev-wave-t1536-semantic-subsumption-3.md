---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1536-semantic-subsumption
seq: 3
---

## 再発

### F95

- **再発: 2026-08-25** — `s8c-predicate-snapshot` group の 3 node で同型が再発した。
  収集は `-n 0` で bare node、実走は loadgroup で `@s8c-predicate-snapshot` 付きになり、
  どちらの表記で登録しても一致しない。同じ形は F408 が別 group で先に記録している。
  本 wave は harness を直さずに済ませた — 正規化の設計は別 ID が所有しているためである。
  代わりに**実行形を 2 通り測った**。受入と同じ loadgroup 走で node 集合を取り、
  runner の正規経路である `-n 0` を渡した直列走で機械照合を通す。3 版すべてで、
  2 走の失敗 node 集合は接尾辞を除いて完全一致した。loadgroup 走の label は
  MISMATCH のまま残し、KILLED と読み替えていない。手順の正本は
  {{D:semantic-subsumption-retirement}}。
