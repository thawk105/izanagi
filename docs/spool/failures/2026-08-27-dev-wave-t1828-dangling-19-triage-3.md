---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1828-dangling-19-triage
seq: 3
---

## supersede 追記

- F118 **supersede: 2026-08-27** — 未了節の盲点一覧は検出側だけを挙げている。抑止側にも射程があり、runbook §7.2 のとおり抑止には basename 一致が要るため、別名同内容の控えは抑止されない。2026-08-27 の 19 commit の分類では、監査が控え無しとした 9 path の**全件**が「同じ探索根に別名で同一 bytes が在る」型で、名前違いだけを理由に要確認へ残っていた。安全側の過大報告なので防壁は破れないが、効き方は例外的ではない。抑止条件を緩められるかの検討は {{T:audit-offrepo-name-independent}}。
