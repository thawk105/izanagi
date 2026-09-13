# certification attempt 0:995805.nqsv

quality: accepted

```
== calibration [pegasus] threads=48 ==
clocks_per_us (TSC 実測): 2100 MHz
workload: ycsb_zipf_skew=0.9, ycsb_rratio=95, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 1,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000      6.023%                  518MB
     2,000,000     10.648%    +4.625pp     1023MB
     4,000,000     15.581%    +4.932pp     1958MB
  working set / L3 = 4.9×
  · miss 率が単調上昇で飽和点なし (masstree 系の木深化, D15)。下限基準を適用: working set (maxrss 518 MB) が L3 (105 MB) の 4.9 倍 (≥4×) になる最小 N=1,000,000 を採用。many-core cache 競合は再現され、かつ run コスト最小

-- noise floor (N=10 run) --
  median 10,225,118 tps  mean 10,227,291  CV 0.425%
```
