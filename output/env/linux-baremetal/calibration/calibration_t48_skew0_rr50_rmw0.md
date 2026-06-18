# calibration: linux-baremetal / threads=48

```
== calibration [linux-baremetal] threads=48 ==
clocks_per_us (TSC 実測): 1800 MHz
workload: ycsb_zipf_skew=0, ycsb_rratio=50, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 1,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000     14.895%                  597MB
     2,000,000     22.725%    +7.830pp     1025MB
     4,000,000     34.077%   +11.353pp     2038MB
  working set / L3 = 6.6×
  · miss 率が単調上昇で飽和点なし (masstree 系の木深化, D15)。下限基準を適用: working set (maxrss 597 MB) が L3 (90 MB) の 6.6 倍 (≥4×) になる最小 N=1,000,000 を採用。many-core cache 競合は再現され、かつ run コスト最小

-- noise floor (N=10 run) --
  median 6,440,280 tps  mean 6,431,544  CV 0.473%

-- scale sensitivity (small vs medium) --
  small  : 4t/1,000,000rec  per-thread 134,926 tps
  medium : 48t/1,000,000rec  per-thread 134,589 tps
  efficiency ratio (medium/small) 1.00
```
