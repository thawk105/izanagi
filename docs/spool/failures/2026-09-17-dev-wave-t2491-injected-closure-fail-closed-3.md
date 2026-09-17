---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2491-injected-closure-fail-closed
seq: 3
---

## supersede 追記

- F918 **supersede: 2026-09-17** — 恒久対応の「検査本体の強化はユーザー裁定へ返した」は D1882 の裁定と {{D:injected-closure-unswallowed-rule}} の実装 (commit 125ab5fd1 + 79dd07742、`orchestrator/tests/test_ccbench_spawn_sites.py`) で実施済み。同一置換の変異で閉包検査が旧版 PASSED / 新版 FAILED を実測 (`output/insights/2026-09-17/t2491-injected-closure-fail-closed/`)。再発検知の「負例だけが赤で閉包検査が緑なら何も保証していない」は引き続き有効。
