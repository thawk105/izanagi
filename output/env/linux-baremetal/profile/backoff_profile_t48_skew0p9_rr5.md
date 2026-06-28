# backoff profile — linux-baremetal / write-heavy (skew0p9_rr5)

> P2-4 (orchestrator/campaign/backoff_profile)。BACKOFF_NOINLINE 診断 build で perf record (cycles,instructions) し backoff() spin を分離。trace-disabled (規律1)・単一テナント直列 (規律4)。

## 有用 IPC (spin 除外) は backoff 量で一定か = [P0] の核

- total_ipc の散布 (max-min)/mean = **117.7%** (全域。backoff 量で大きく動く = 積モデル破綻の原因)
- **useful_ipc の散布 (sweet-spot 0-10us) = 4.4%** (throughput ピーク帯。ここで一定 = total_ipc 低下は純 spin 希釈 = [P0] の核命題)
- useful_ipc の散布 (全域 0-100us) = 29.9% (over-throttle 域 25-100us の有用 IPC 二次低下を含むので大きく出る。一定主張は sweet-spot 限定)

| backoff us | tps (median) | abort% | spin cyc% | spin instr% | total IPC | useful IPC | K_total | K_useful |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0(none) | 1,867,747 | 81.5 | 0.0 | 0.0 | 1.921 | 1.921 | 5,241,104 | 5,241,104 |
| 2 | 2,073,057 | 74.0 | 22.6 | 2.9 | 1.561 | 1.958 | 5,098,098 | 4,064,508 |
| 5 | 2,390,545 | 62.6 | 38.7 | 5.7 | 1.306 | 2.008 | 4,901,590 | 3,187,515 |
| 10 | 2,586,112 | 49.4 | 48.7 | 8.5 | 1.088 | 1.940 | 4,698,585 | 2,636,054 |
| 25 | 2,454,570 | 33.3 | 58.9 | 13.0 | 0.852 | 1.805 | 4,319,548 | 2,039,593 |
| 50 | 2,150,346 | 24.2 | 64.7 | 17.7 | 0.691 | 1.611 | 4,102,934 | 1,760,464 |
| 100 | 1,784,930 | 17.3 | 69.5 | 22.7 | 0.577 | 1.465 | 3,741,267 | 1,472,997 |

注: tps は **perf record 下** の値 (sampling overhead 込み)。headline throughput は
stock inline build の値 (P2-2/backoff_sweep)。ここは spin%/IPC 比の機序分析専用。
