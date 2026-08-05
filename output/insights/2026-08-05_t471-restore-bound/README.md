# [T-471] `_restore_targets` 所要時間の実測 — 成果物の地図

| ファイル | 内容 |
|---|---|
| `preregistration.md` | **実測前に凍結**した判定規則。測る case (C2/C1) の literal 凍結、arm 5 本、観測者効果の遮断、代入規則、環境タグ、[T-399] 凍結式への当てはめ方 |
| `erratum-1.md` | 同事前登録の erratum。§6 spec manifest の射程確定と、計測器に意図的に残した限界とその裁定理由 |
| `RESULT.md` | **実測結果と判定**。復元は数十ミリ秒 (max 71.79 ms)、支配項は pycache purge。凍結式は R 非依存で偽 = [T-360] 条件 3 は R では閉じない |
| `warn-margin.md` | `elapstim_req` の warn 値の設計メモ (候補・未 certify)。律速は R ではなく未計測の `H_head` と `D_delivery` |
| `driver/measure_restore_bound.py` | 使い捨て計測 driver (293 行)。本物の `_restore_targets` を 1 trial 1 回だけ呼ぶ |
| `driver/restore_bound_analysis.py` | 解析純関数 (集計・profile 検査・fail-closed 判定) |
| `driver/restore_bound.pbs` | 計算ノード wrapper (環境変数インタフェース、fail-closed gate) |
| `evidence/rbound-a1/restore-bound.json` | 実測の生証拠。全 500 trial の生値、arm profile、layout、環境タグ |
| `evidence/rbound-a1/compute-node.marker` | 計算ノード側が書いた marker (投入の有効性検査用) |
| `mutation-spec.json` / `mutation-ledger.json` | 変異事前登録と本走結果 (6/6 KILLED、SURVIVED 0) |

## 一言でいうと

mutation_harness の復元処理は**数十ミリ秒**で、scheduler の kill 予告後に確保すべき時間の
支配項ではない (支配項は `_stop_process` の 2 段 wait 最大 10 秒)。一方、この実測をもってしても
[T-360] の条件 3 は閉じない — 判定式が復元時間に依存しない形になっており、
必要なのは「production の cleanup が grace 内で実際に完走した attempt」だからである。
