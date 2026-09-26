# certification attempt 0:29394.nqsv

quality: accepted

```
== calibration [pegasus] threads=48 ==
clocks_per_us (TSC 実測): 2100 MHz
workload: ycsb_zipf_skew=0.9, ycsb_rratio=50, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 1,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000     14.349%                  640MB
     2,000,000     18.566%    +4.217pp     1268MB
     4,000,000     25.159%    +6.593pp     2447MB
  working set / L3 = 6.1×
  · 測定範囲内で飽和点なし。下限基準を適用: working set (maxrss 640 MB) が L3 (105 MB) の 6.1 倍 (≥4×) かつ LLC miss 率 ≥ 0.50% を満たす最小 N=1,000,000 を採用。

-- noise floor (N=10 run) --
  median 817,246 tps  mean 817,446  CV 0.989%
```
