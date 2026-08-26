---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1828-dangling-19-triage
seq: 3
---

## supersede 追記

- F118 **supersede: 2026-08-27** — 未了節が挙げる盲点一覧に**別名同内容**が抜けていた。外部控えの抑止は `_enumerate_offrepo_candidates` が basename・size・mode の一致で候補を絞ってから内容比較するため、同一 bytes でも file 名が違う控えは見えない。監査が控え無しとした 9 path の**全件**について、監査と同じ探索根の中に別名の同一 bytes 実体を実測した。方向は安全側 (過大報告) で正しさは破れないが、要確認件数と分類作業量を押し上げる。是正は {{T:audit-offrepo-name-independent}}。
