---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: dev-wave-t2866-tpcc-campaign
seq: 2
---

## 再発

### F242

- **再発: 2026-09-27** ([T-2866] の wave) — 統合 commit が `pipeline._BENCH_DONE_CONDITIONAL_PAYLOAD_KEYS` (private symbol) に `workload` を足した。
  段 6 の敵対レビュー 2 本と焦点再レビュー 1 本は「固定 key 検査と衝突しない」と判定し、親の焦点走 2 回 (2,765 passed) も通ったが、
  受入全走で `orchestrator/tests/test_layer3_report.py::test_run_bench_ast_assignments_exactly_match_declared_payload_keys` (条件付き key 数の pin) が赤になった。
  `DW-O26` は「private symbol は consumer 表に出ないので symbol 名で production を grep する」と既に書いており、親がこの symbol で consumer test を grep しなかった
  (手順は在ったが適用しなかった)。焦点走 1 回目では同じ型の `_PreparedEvaluation` の直接構築 fixture 11 件を捕えていたので、同じ差分の別 private symbol へ grep を広げていれば受入前に出た。
  帰属判定と対処は `output/insights/2026-09-27/t2866-tpcc-campaign-wiring/README.md` §1 (payload への追加を取り下げて閉じた)。
