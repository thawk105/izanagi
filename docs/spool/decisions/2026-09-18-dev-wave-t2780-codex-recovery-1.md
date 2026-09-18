---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2780-codex-recovery
seq: 1
---

## {{D:mocc-pilot-patch-binding}}. T1943 pilot receipt を計装 source の束縛を持つ v2 へ置換する

**決定:** T1943 専用 receipt を `mocc-trace-pilot-receipt/t1943-g2-v2` に置換し、旧v1を
job-result の受理集合から外す。patch path/hash・touch set・適用後source hashとbuild配線の記録を持つ。
general v4 と verifier の判定規則・rc許可集合は維持する。

**理由:** X/P patch の適用有無で source の命題が異なる。receipt writer が実 bytes と
sidecar を照合し、job-result writer が binding の field・型・値を確認する。
`trace0_built_from_patched_source` は配線に基づく記録で、コンパイラの読取りbytesの独立証明ではない。

**却下:** v1 のまま束縛を増やすこと、verifier rc=3 の許可、異常の certified 昇格。
今回の job5905 の no-g2 は discriminator の完走正例であり正式認証ではない。
