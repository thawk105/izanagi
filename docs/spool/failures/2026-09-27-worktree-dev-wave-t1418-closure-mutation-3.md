---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: worktree-dev-wave-t1418-closure-mutation
seq: 3
---

## supersede 追記

- F424 **supersede: 2026-09-27** — 根本原因の記述は古い: `ratified_enforcement_source` fixture は b4ff38f6b (2026-08-27) で no-op になり、現行の drift 源は `orchestrator/campaign/ident.py` → `contract_loader_binding.capture_contract_loader_binding` (現 HEAD の閉包 96 path の blob と disk bytes の一致) である。file-swap の変異は停止せず全件 drift で赤になり、値の層が見えない形に変わっていた。恒久対応は {{D:mutation-commit-injection}} の `tools/mutation_harness.py --inject commit` (検査: `orchestrator/tests/test_mutation_harness.py` の commit 注入 test 群、実 dispatch の dogfood は `output/insights/2026-09-27/t1418-commit-injection/README.md`)。
