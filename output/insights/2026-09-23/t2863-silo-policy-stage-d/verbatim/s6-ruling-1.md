# 段 6 裁定 1 巡目 — [T-2863] (2026-09-23、親 = Claude manager)

入力: s6-review-A.md (NO-GO、must-fix RA1〜RA3)、s6-review-B.md (NO-GO、must-fix RB1)、焦点走 focus-b1 (13 file、1 failed / 937 passed / 5 skipped、赤 = test_silo_policy_recon.py::test_submit_dry_run_lists_eight_jobs)。
前提: 初走 8 job (20182〜20189.nqsv) は commit `ce4985ab2` の `run` で走行中。`run` の挙動を変える fix は計測と実装の対応を崩すので本巡では行わない。`aggregate` は login で後から走るので fix してよい。

| ID | 判定 | 裁定 |
|---|---|---|
| RA1 | real | fix。`aggregate` は全入力の workload が `run` の固定値 (`{"legacy": C.LEGACY, "performance": FLAGS, "bench_reps": 5, "numa": True}`) と一致することを照合し、不一致は error (binary null) |
| RA2 | real | fix。`aggregate` は初走・再測の abort0 行の本文 sha256 = `render_policy(degenerate_policy())` の sha256、stock 行の genome flags = BACK_OFF 1 の `locks._BASE`、B0-L-W0 行 = BACK_OFF 0 を照合し、不一致は error |
| RA3 / RB1 | real | fix。投入 script は不採用 (台帳未登録、dispatch_compute --task generic を使う) なので、script を実行する test を削除する (本 wave で新設した test で、既存 test の期待値の変更ではない)。script の再実装はしない |
| RB2 | real (効率) | 不採用。`run` を変える。二値・受理集合は変わらず、job 0 の所要が build 1 回分増えるだけ |
| RB3 | real (効率) | 不採用。同上 (legacy 非 certified の点で性能 verify 1 回分の時間) |
| RB4 | nit | 不採用。記録 field 1 つで結果は変わらない |

変異の追加登録 (fix 前、DW-M01): M-AGG-WORKLOAD (workload の固定値照合を除去 → 別 workload の入力で null にならない)、M-AGG-CONTROL (abort0 本文 sha256 照合を除去 → 基準の本文違いで null にならない)。
