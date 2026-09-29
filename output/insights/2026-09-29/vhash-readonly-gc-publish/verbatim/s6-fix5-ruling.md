# 段 6 fix5 裁定 — md_22 [T-2911] (2026-09-30 01:3x JST)

verify1 (commit 5c781ae7c、wave 木、36633.nqsv、bnode085、job Elapse 428 s、raw `raw/verify1.json`、trace `raw/verify1-traces/`): driver rc=1。
24 走 (default・最良 genome × ro 50/95 × 長い ro 有無 × seed 3) の実測: 判定器 rc=3 (verdict indeterminate) 24/24、巡回 0、`READ_WTS_MISMATCH` 0、integrity の数値項目 11 種 (orphan_reads・version_dups・dup_txids・genesis_commits・missing_txids・write_version_mismatch・malformed_keys・framing_violations・lock_coverage_violations・write_intent_violations・permutation_violations) すべて 0、trace の txn 数 = workload の commit 数 (24/24)、variant の flag 立て > 0 (最小 2、最大 221,890)。検査した commit 済み txn 計 11,954,950。
それでも driver が rc=1 になった原因: `verify_acceptance` が `integrity.clean is True` を要求している。`orchestrator/verifier/model.py` の `Integrity.clean()` は数値項目・commit 照合に加えて `proof_surfaces.certification_gate_satisfied()` を要求し、Cicada には X/P/I の証拠面が無いので常に false (= 上限 indeterminate の理由そのもの)。受理条件が Cicada では到達不能だった (DW-O13 の「要求する値が到達可能か」の見落とし、本 wave の段 4 の B-3 の書き方と子の実装の両方)。
先例: md_14 の repo 外起動器 `/work/SFC/tanab/tmp/vhash-gc-connection-prototype-2026-09-29/launch_cicada_run_gc.py` の `stock_pass` は `clean` を使わず、INTEGRITY_NUMERIC がすべて 0・trace の commit 行 = expected_commits・total_cycles 0・verdict indeterminate で受理した。

- **FB-11:** `verify_acceptance` の `integrity.clean is True` を、integrity の数値項目 (上の 11 種と `existence_violations`) がすべて 0、かつ判定器の stats の txn 数 = `--expected-commits` に渡した commit 数、に置き換える。rc ∈ {0, 3}・巡回 0・`non_serializable` 0・`READ_WTS_MISMATCH` 0・COUNT の ro commit と flag 立て > 0 はそのまま。どの数値項目が 1 でも、txn 数が 1 でもずれたら拒否する (受理集合を広げるのは「証拠面が無いこと」だけ)。
- test: 数値項目それぞれ 1 件で拒否、txn 数の不一致で拒否、証拠面なし (`clean=false`・数値項目 0・txn 一致) で受理、の 3 型を実体の関数で固定する。
- 判定器 (`orchestrator/verifier/`) は編集しない。
- 親は fix5 統合後に verify を取り直す (verify1 の raw は事実として残し、一次資料に「受理判定の不具合で rc=1、中身は上の実測」と書く)。
