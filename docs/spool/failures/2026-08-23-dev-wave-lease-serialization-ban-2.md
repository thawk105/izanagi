---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-lease-serialization-ban
seq: 2
---

## supersede 追記

- F167 **supersede: 2026-08-23** — 恒久対応が挙げた「受入 lease (D239) が受入窓を 1 本へ直列化する」は現行契約ではない。D662 が待ち行列を廃止し、{{D:lease-wait-unreachable}} が待ち機構を実装から除去した。walltime 超過への対応は直列化に依存しない形へ読み替えること。
- F465 **supersede: 2026-08-23** — 恒久対応末尾の「`--lease-optional` が浸透すれば直列化待ちの発生頻度は下がるが、フラグを付け忘れた wave は引き続き同型の問題に当たりうる」という残余は解消した。{{D:lease-wait-unreachable}} が待ちループと待ち行列を到達不能にし、フラグは no-op になったため、付け忘れによる旧経路への falling back は起こらない。
