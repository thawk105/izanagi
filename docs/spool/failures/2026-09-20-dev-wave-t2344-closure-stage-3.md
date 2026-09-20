---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2344-closure-stage
seq: 3
---

## 再発

### F474

- **再発: 2026-09-20** — 向きの違う同型 (識別子 grep が「値を別の形で持つ consumer」を落とす)。[T-2344] wave は
  収載 tuple を exact 63 → 85 に進め (certified の受理集合が変わる)、焦点走の file 集合を「変更 test 5 + 変更 production の symbol を参照する
  consumer test 15 + DW-O26 改訂版の inventory 4 群」で組んだ。しかし `orchestrator/tests/test_b10_backoff_static_tail_formal.py::test_formal_loader_rejects_real_exploration`
  は `campaign_lock` / `artifact_admission` の symbol を 1 つも参照せず、`b10_backoff_static_tail_formal` 経由で**実在の外部 campaign**
  (`/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/...`、記録 grammar exact-63) を certified 経路に渡して「not formal」で拒否されることを期待していた。
  tuple 前進後は decode 段 (exact key 集合不正) で拒否され message が変わるので赤になり、段 6 レビュー 2 本・焦点走 3 本を通って受入全走で初めて出た
  (受入 1 走 = 約 15 分の損失、fix 2 で test の主張を「実 exact-63 は decode 段拒否」と「not formal は現行 grammar の合成 campaign で検査」に分けて残した)。
  記録済み成果物は「変更した値を複製した consumer」の一種で、symbol 参照でも literal grep でも掛からない。受理集合 (lock grammar) を変える wave は、
  実 外部 root (`/work/1/SFC/tanab/` 配下) を読む test (2026-09-20 時点で 14 file) を参照関係に依らず焦点走へ加える (memory `mutation-discipline` /
  `codex-child-discipline` 系へ記録。DW-O26 は予算 998/1000 bytes で追記不能)。
