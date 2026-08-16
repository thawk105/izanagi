# 対象条件での between-run 分布 — 実測結果 [T-1142]

事前登録は同ディレクトリの `preregistration.md`。**本文書は実測値だけを載せる。**

## 0. これが何か

[T-987] が `n` を導出不能とした 3 番目の理由は「対象条件 (Pegasus / rr20・rr80 /
extime=5) の between-run 実測が存在しない」ことだった。登録済み較正は within-run・rr50、
between-run の既存実測は linux-baremetal の rr5/rr50/rr95・extime=3 しかなかった。
**本文書はその欠落を埋める最初の実測である。**

## 1. 走行の同一性

- 観測 round 数: **11** (12 cell x round、計 132 session)
- `use_perf`: `False` (計算ノードに perf が無く、preflight が unavailable と判定)
- `freeze_verification_status`: `held`
- holdout 観測承認: `True` (ユーザーが不可逆・一度きりで付与)
- `n_analysis`: 出していない (`per-allocation-result-does-not-derive-n`)

## 2. cell ごとの between-run 分布

outer trial = reps=5 の median。下表の統計は round 間 (= between-run) のもの。

| holdout | configuration | median (tps) | 標本 sd | CV |
|---|---|---:|---:|---:|
| rr20 | `backoff_fixed_best` | 3,574,720 | 9,773.5 | 0.0027 |
| rr20 | `ident_all` | 1,188,889 | 12,010.0 | 0.0101 |
| rr20 | `p2_2_flag_opt` | 2,526,710 | 13,582.2 | 0.0054 |
| rr20 | `sort_best` | 1,204,168 | 15,144.7 | 0.0126 |
| rr20 | `stock_common` | 1,188,753 | 10,177.0 | 0.0086 |
| rr20 | `system_gate` | 1,260,757 | 7,981.2 | 0.0063 |
| rr80 | `backoff_fixed_best` | 6,833,166 | 15,230.5 | 0.0022 |
| rr80 | `ident_all` | 1,519,297 | 14,216.7 | 0.0093 |
| rr80 | `p2_2_flag_opt` | 7,186,316 | 25,724.5 | 0.0036 |
| rr80 | `sort_best` | 1,515,617 | 17,045.2 | 0.0112 |
| rr80 | `stock_common` | 1,521,064 | 13,416.0 | 0.0088 |
| rr80 | `system_gate` | 3,152,090 | 10,783.3 | 0.0034 |

**CV の範囲: 0.0022 〜 0.0126** (12 cell)。

## 3. 対比 (stock_common との差)

**これは診断であって検定比較対ではない** — 既存凍結が stock_common を
「併記用の文脈セル」として比較対から除いているため。oracle の判定は 6 構成の argmax である。

| holdout | configuration | 相対差 median | 散布比 (sd/\|mean\|) |
|---|---|---:|---:|
| rr20 | `backoff_fixed_best` | +2.01122 | 0.01474 |
| rr20 | `ident_all` | -0.00294 | 7.92797 |
| rr20 | `p2_2_flag_opt` | +1.13138 | 0.01381 |
| rr20 | `sort_best` | +0.01974 | 1.07008 |
| rr20 | `system_gate` | +0.06085 | 0.16067 |
| rr80 | `backoff_fixed_best` | +3.48981 | 0.01279 |
| rr80 | `ident_all` | +0.00330 | 3.45239 |
| rr80 | `p2_2_flag_opt` | +3.73550 | 0.01159 |
| rr80 | `sort_best` | -0.00180 | 4.62810 |
| rr80 | `system_gate` | +1.07583 | 0.02113 |

## 4. 6 構成の同時分布

**[T-987] が「差の分散に共分散が要る」と指摘した量が、ここで初めて観測可能になった。**
完全な共分散行列・相関行列は `result.json` の `statistics.joint_covariance` /
`statistics.joint_correlation` に全 round の raw 値とともに入っている。
cell 独立でなく **同一 round の 6 構成 vector を一単位として**保存してある。

## 5. ドリフト診断 (事前登録した閾値での判定)

- `valid_for_n_analysis`: **True**
- 無効化理由: なし
- 閾値: {"max_abs_position_correlation": 0.5, "max_abs_relative_time_slope_per_second": 5e-06}

**全 12 cell が事前登録した閾値を通過した。** 巡内の実行位置と性能の順位相関も、
単調時刻に対する相対傾きも、閾値を超えたものは無い。

## 6. 規模の未達 (正直に書く)

事前登録は R >= 32 (分散の相対標準誤差 <= 25%) を要求したが、**実測は R = 11** である。

原因は親の設計判断の誤りである。holdout admission の cell claim は排他作成で
**1 cell につき 1 走行**しか claim できず、33 round は 1 本の job で取るべきだった。
3 allocation へ分割した裁定が、本 wave 中に main が着地させた admission の計上モデルと
衝突し、allocation 1 が 12 cell すべてを 11 round 分の allowance で claim した時点で
allocation 2 / 3 は `n pilot holdout cell key was already consumed` で拒否された。

R=11 の分散相対標準誤差は `sqrt(2/10) = 44.7%` で、事前登録の 25% 以下を満たさない
(R=8 の 53.5% よりは改善)。**したがって本値から `n` を確定してはならない。**

それでも本値を残すのは、対象条件の between-run 実測が 0 件だったからである。
0 件と 11 round では、後続が置ける仮定の幅が違う。
**次の取得は 33 round を 1 job で行う。**

## 7. 条件付け

- `all-rows-eligible`: pilot は throughput しか集めない。実 judge の verify/eligibility 状態は
  含まない。**certified error rate と呼んではならない。**
- 単一 allocation: 割当内の連続 round であり、cold-boot・温度ドリフトを含まない**下限**。
- `perf-off`: 本走が perf ありで走るなら条件が異なりうる。
- pin と binary SHA は `result.json` に記録した。**これは provenance であって再利用条件ではない** —
  再利用の可否は「その変更が測った量に効きうるか」で判断する。
