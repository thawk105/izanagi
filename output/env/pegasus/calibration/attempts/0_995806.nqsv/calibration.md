# certification attempt 0:995806.nqsv

quality: rejected

```
== calibration [pegasus] threads=48 ==
clocks_per_us (TSC 実測): 2100 MHz
workload: ycsb_zipf_skew=0.9, ycsb_rratio=5, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 1,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000      0.364%                  517MB
     2,000,000      1.392%    +1.027pp     1023MB
     4,000,000      4.762%    +3.370pp     1958MB
  working set / L3 = 4.9×
  ⚠ cache_floor 警告: working set が cache に乗る疑い (下限割れ)
  · miss 率が単調上昇で飽和点なし (masstree 系の木深化, D15)。下限基準を適用: working set (maxrss 517 MB) が L3 (105 MB) の 4.9 倍 (≥4×) になる最小 N=1,000,000 を採用。many-core cache 競合は再現され、かつ run コスト最小
  · 採用点の LLC miss 率 0.364% が下限 0.50% 未満。working set が cache に収まり、many-core の cache 競合が 再現されない恐れ (測定が楽観的に歪む)。レコード数の下げ過ぎを疑え

-- noise floor (N=10 run) --
  median 2,349,960 tps  mean 2,347,116  CV 1.353%
```
