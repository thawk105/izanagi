# P2-2 サマリ — silo 全探索 (workload 別の最速構成)

> 自動生成。各 workload campaign の最速 genome を横断比較 (genome 列挙=no-wait XOR で 8、空間訂正は insight 2026-06-22_silo-both-no-wait-zero-livelock.md)。

- calibration: records=1,000,000 / threads=48 / clocks_per_us=1800 / skew0.9 / noise floor CV 2.28%

| workload | 最速 genome | median tps | CV | 2位との差 |
|---|---|---:|---:|---|
| read-heavy | `B0-T-W0` (BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0) | 8,466,239 | 0.22% | 差 +0.3% は信用できる差でない (noise内/非有意) |
| balanced | `B0-L-W0` (BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0) | 2,722,529 | 1.49% | 最速が **+6.1%** 速い (有意, p=0.012) |
| write-heavy | `B0-L-W0` (BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0) | 1,883,017 | 1.03% | 最速が **+13.2%** 速い (有意, p=0.012) |

## 各 workload の詳細レポート

- **read-heavy**: [p2-2-silo-read-heavy-enumerate-5ffcabad/reports/p2-2-fitness-read-heavy_report.md](p2-2-silo-read-heavy-enumerate-5ffcabad/reports/p2-2-fitness-read-heavy_report.md)
- **balanced**: [p2-2-silo-balanced-enumerate-f1588056/reports/p2-2-fitness-balanced_report.md](p2-2-silo-balanced-enumerate-f1588056/reports/p2-2-fitness-balanced_report.md)
- **write-heavy**: [p2-2-silo-write-heavy-enumerate-8967bed6/reports/p2-2-fitness-write-heavy_report.md](p2-2-silo-write-heavy-enumerate-8967bed6/reports/p2-2-fitness-write-heavy_report.md)
