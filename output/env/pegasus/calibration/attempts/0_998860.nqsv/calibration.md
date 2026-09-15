# certification attempt 0:998860.nqsv

quality: accepted

```
== calibration [pegasus] threads=48 ==
clocks_per_us (TSC 実測): 2100 MHz
workload: ycsb_zipf_skew=0.9, ycsb_rratio=50, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 1,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000      7.969%                  518MB
     2,000,000     12.840%    +4.872pp     1023MB
     4,000,000     17.099%    +4.258pp     1958MB
  working set / L3 = 4.9×
  · miss 率が単調上昇で飽和点なし (masstree 系の木深化, D15)。下限基準を適用: working set (maxrss 518 MB) が L3 (105 MB) の 4.9 倍 (≥4×) になる最小 N=1,000,000 を採用。many-core cache 競合は再現され、かつ run コスト最小

-- noise floor (N=10 run) --
  median 1,367,300 tps  mean 1,360,228  CV 2.216%
```
