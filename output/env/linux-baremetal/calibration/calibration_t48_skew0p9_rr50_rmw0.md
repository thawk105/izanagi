# calibration: linux-baremetal / threads=48

```
== calibration [linux-baremetal] threads=48 ==
clocks_per_us (TSC 実測): 1800 MHz
workload: ycsb_zipf_skew=0.9, ycsb_rratio=50, ycsb_rmw=0

-- saturation: LOWER-BOUND (膝なし→working set≥L3×4) → records = 1,000,000 (Δ閾値 1.000%) --
  records         miss_rate    Δ           maxrss
     1,000,000     20.443%                  597MB
     2,000,000     23.453%    +3.010pp     1025MB
     4,000,000     29.934%    +6.481pp     2038MB
  working set / L3 = 6.6×
  · miss 率が単調上昇で飽和点なし (masstree 系の木深化, D15)。下限基準を適用: working set (maxrss 597 MB) が L3 (90 MB) の 6.6 倍 (≥4×) になる最小 N=1,000,000 を採用。many-core cache 競合は再現され、かつ run コスト最小

-- noise floor (N=10 run) --
  median 914,883 tps  mean 908,623  CV 2.281%

-- scale sensitivity (small vs medium) --
  small  : 4t/1,000,000rec  per-thread 67,213 tps
  medium : 48t/1,000,000rec  per-thread 19,052 tps
  efficiency ratio (medium/small) 0.28  ⚠ scale-suspect
  · per-thread 効率が small→medium で 0.28 倍 (<0.7) に低下。スケール頭打ちの疑い
```
