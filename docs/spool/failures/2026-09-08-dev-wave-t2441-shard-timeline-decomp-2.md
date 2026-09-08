---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2441-shard-timeline-decomp
seq: 2
---

## supersede 追記

- F254 **supersede: 2026-09-08** — 「dry-run は directory を作らない」は現行挙動と違う。`tools/dev_wave_codex.py --dry-run` は artifact directory を実際に作る (2026-09-08 実測)。したがって親 directory 不在で止まる型は起きず、代わりに同じ job-id のまま本投入すると既存 directory に当たる。dry-run 後は当該 directory を rmdir するか job-id を変える。
