# S2 縮小 verify 構成の校正結果 (phase3.md 後続段 1、D36)

- env: linux-baremetal / ccbench pin: dff0f1e / genome: `silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`
- S2 構成: {'ycsb_tuple_num': '1000000', 'ycsb_zipf_skew': '0.9', 'ycsb_rratio': '50', 'ycsb_rmw': 'false', 'ycsb_max_ope': '10', 'thread_num': '48'} + extime=3 (perf 代表 workload と同一フラグ)
- 判定: **all_pass = True**

## 候補別 gate 1/2

### extime=3
- gate1 (contention 再現): PASS — abort率 対照 0.204 / trace時 0.2631 (比 1.29, 帯 (0.5, 2.0)), aborts 中央値 556483
- gate2 (trace 規模): PASS — run 最大 3.54s, verifier 140.66s / RSS 7.68GB / txns 1548952, stock certified = True

## gate 3 (赤検出力 + ablation)

- norw @ S2: 赤 PASS (total_cycles=4053)
- highkey @ S2: 赤 PASS (total_cycles=5)
- highkey @ legacy (tuple200/t4): 緑 PASS — S2 だけが検出する違反の機械実証 (ablation 点)

## 生データ

同名 .json (全 rep・全 run・閾値・環境)。
