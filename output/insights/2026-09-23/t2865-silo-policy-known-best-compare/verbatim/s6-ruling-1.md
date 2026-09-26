# [T-2865] 段 6 裁定 1 巡目 (親)

入力: codex/s6-review-A.md (NO-GO、must-fix 2・should 1・nit 1)。対象 commit 7779e44b9。

| 所見 | 判定 | 採否 | 成果物影響 |
|---|---|---|---|
| R1 job 7 (と 6) の巡回漏れ: `result[job:] + result[:job]` は job ≥ 6 で基本列 | real (6 要素に slice 7 → 基本列) | fix: `offset = job % 6`。test の期待 8 列を独立に列挙 | 放置時、job 7 の参照位置が裁定 P2 と違う (値は変わらないが設計の記録と食い違う) |
| R2 BACK_OFF の重複 define (`-DBACK_OFF=1 -DBACK_OFF=0`) を有効と判定 | real | fix: BACK_OFF 系 define の列がちょうど `["-DBACK_OFF=1"]`、BACKOFF_FIXED 系がちょうど `["-DBACKOFF_FIXED=10"]` | 放置時、後勝ちの BACK_OFF=0 で build された値が fixed10 の分母になりうる |
| R3 fixed10 test が `_build_variant` を stub し configure argv を見ない | real | fix: `_build_variant` を実際に呼び、外側の既存 seam (configure の `compute._run_checked` と build) を観測 wrapper で捕捉して `-DCCBENCH_BACKOFF_FIXED=10` と `-DCCBENCH_BACK_OFF=1` を確認する test を足す (既存 test_silo_policy_coverage.py の `_build_variant` test の組み方を写す) | 放置時、build 配線の欠落を投入前に検出できない |
| R4 `case_order` を照合しない | real (nit) | fix: `case_order` も予定列と照合 | 記録の食い違いが残る |

## 変異の追加登録 (DW-M01、fix 前)

| ID | 位置 | 壊し方 | 期待 |
|---|---|---|---|
| m-rotation-mod | `_cases("compare")` | `job % 6` → `job` | 8 列を独立に列挙した test (job 6・7) |
| m-backoff-dup | `_backoff_fixed_defines_effective` | BACK_OFF の一意性検査を外す (`count == 1` だけに戻す) | 重複 BACK_OFF の負例 test |
| m-fx-argv | `_build_variant` | stock_flags へ BACKOFF_FIXED を足さない | 実 configure argv の test |
| m-case-order | `_compare_detail` | case_order 照合を外す | case_order 食い違いの test |

既登録 9 本はそのまま (m-rotation の kill 点 test は独立列挙へ更新)。計 13 本。
