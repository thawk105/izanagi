---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-23
wave: worktree-dev-wave-t2849-comparison-harness
seq: 3
---

## 再発

### F42

- **再発: 2026-09-23** — [T-2849] で U-A の実装子が足した新規 test 2 本 (`orchestrator/tests/test_t2849_loop_entry.py`・`test_t2853_trace_preservation.py`) に自走 harness も allowlist 記載も無く、最終の受入全走 1 回目が `orchestrator/tests/test_plain_runner_coverage.py` の 1 件だけで赤になった (同じ wave の他の新規 5 本は自走 harness を持っていた)。子の sandbox は試験を実走できず、親は焦点走の file 集合に DW-O26 の「新規 test file を足す走は file 集合列挙のメタテストも含める」を適用しなかった。U-A の fix 子が 2 本へ同形の自走 harness を足して受入を取り直した。

### F1041

- **再発: 2026-09-23** — [T-2849] の段 4 で親は、開発の検査の見積りを「≤ 0.99 node 時間」と置いたが、変異 dispatch の job (新しい種類) の単価を実測しておらず、walltime × job 数の上限も取らないまま変異 probe 29 job を投入した (本項の恒久対応の不適用)。probe の後、`tools/mutation_worktree.py` が使い捨て作業木ごと dispatch の受領証を消していて Elapse を実測できないと分かり、同じ runner argv の 1 job を dispatch して単価 (job Elapse 13 秒) を実測してから本走を投じた。本走 28 job の実測は計 435 秒で、wave の合計は ≈ 0.31 node 時間 (線の内側、測定値・判定への影響なし)。是正: 変異のように job 数が多い新種 job は、投入前に同じ argv の 1 job を dispatch して単価を実測し、変異の台帳に Elapse が残らない点を見込んで受領証を走行中に写す (insight `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md` §7)。
