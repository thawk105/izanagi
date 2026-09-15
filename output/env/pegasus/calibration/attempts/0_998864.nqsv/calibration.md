# certification attempt 0:998864.nqsv

quality: accepted

```
== calibration [pegasus] threads=48 ==
clocks_per_us (TSC 実測): 2100 MHz
workload: ycsb_zipf_skew=0.9, ycsb_rratio=95, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 1,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000     17.008%                  640MB
     2,000,000     23.826%    +6.817pp     1268MB
     4,000,000     29.139%    +5.313pp     2446MB
  working set / L3 = 6.1×
  · miss 率が単調上昇で飽和点なし (masstree 系の木深化, D15)。下限基準を適用: working set (maxrss 640 MB) が L3 (105 MB) の 6.1 倍 (≥4×) になる最小 N=1,000,000 を採用。many-core cache 競合は再現され、かつ run コスト最小

-- noise floor (N=10 run) --
  median 2,377,091 tps  mean 2,382,336  CV 1.720%
```
