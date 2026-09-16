# certification attempt 0:478.nqsv

quality: accepted

```
== calibration [pegasus] threads=48 ==
clocks_per_us (TSC 実測): 2100 MHz
workload: ycsb_zipf_skew=0.9, ycsb_rratio=5, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 2,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000      0.340%                  517MB
     2,000,000      1.567%    +1.227pp     1023MB
     4,000,000      4.707%    +3.140pp     1958MB
  working set / L3 = 9.7×
  · cache_floor 下限 0.50% を満たす最小 N を同じ下限基準候補から選択: N=1,000,000 (LLC miss 0.340%) → N=2,000,000 (LLC miss 1.567%)。
  · 測定範囲内で飽和点なし。下限基準を適用: working set (maxrss 1023 MB) が L3 (105 MB) の 9.7 倍 (≥4×) かつ LLC miss 率 ≥ 0.50% を満たす最小 N=2,000,000 を採用。

-- noise floor (N=10 run) --
  median 2,761,684 tps  mean 2,767,079  CV 0.971%
```
