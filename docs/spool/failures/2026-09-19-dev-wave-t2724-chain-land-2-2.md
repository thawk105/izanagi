---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-19
wave: dev-wave-t2724-chain-land-2
seq: 2
---

## 再発

### F30

- **再発: 2026-09-19** — [T-2724] 凍結 v2 g1 の chain + G を main へ取り込む wave の段 1 で、pin 閉包を持ち込む成果物の **file 名** (`holdout_freeze.v2.g1`、`s8b-freeze-budget-inputs/g1`、run dir 名) の `git grep` だけで作り、**directory 名 `"output/s8b-freeze"` を丸ごと列挙して bytes digest を固定する pin** (`orchestrator/tests/test_backoff_extended_sweep.py::test_b10_freeze_tree_bytes_match_the_wave_local_gate` と `tools/pegasus/b10_backoff_grid.sh` の `EXPECTED_FREEZE_TREES_SHA256`、B-10 の起動契約) を数え落とした。焦点走 8 file (前回 wave の集合の流用) にもこの test file は無く、受入全走 (30 分) で初めて赤 1 node (1 failed / 25311 passed) が出て、chain を land できずに終端した。`DW-O09` の「path 検索は path key の pin しか出さない。role 名や xdist group 名など key 側でも検索し、hit 0 件を pin なしとしない」を、**directory 名と算法名 (`rglob`、`freeze_digest`、`EXPECTED_*SHA256`、`FROZEN_MANIFEST`) の key 側検索**として適用していなかった。追加だけで凍結 gate が赤になる型は memory `grid-constants-and-new-artifact-names-hit-freeze-gates` (2026-08-26) が既に記録していた。一次資料 `output/insights/2026-09-19/t2724-chain-land-2/README.md` §5。
