---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-fig13-b10-waiting-grid
seq: 2
---

## 再発

### F656

- **再発: 2026-09-20** — fig13 (B-10 待ち方 grid の forest 図) wave で、親が実装 commit 直後の provenance full 監査を同一 wave worktree から
  背景 dispatch し (request 13493.nqsv、queue 待ち 12 分)、その待ちの間に段 6 fix1 の実装 commit と docs commit を同じ worktree に作った。
  監査は起動時に HEAD (`680d6136d`) を固定し、終了時の HEAD (`225d0b311`) と不一致で `実行不能: HEAD が監査中に変化した` (rc=2、違反判定ではない) を返した。
  後発 dispatch の投入ではなく **HEAD の変更**が原因で、直列化の対象に「dispatch が終わるまで同一 worktree の commit / merge / checkout を作らない」も
  含めて読む必要がある。実害なし — 全 commit を固めた後に監査を再走して閉じた。qdel も hold の手動削除もしていない。
