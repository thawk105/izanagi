# S-1 検証相 extime 校正結果

- env: linux-baremetal / ccbench pin: `d706650`
- 構成: read-heavy (rr95) × `g_rl` / genome: `silo|BACKOFF_TRIGGER_GATING=1,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`
- 採用 extime: **3s** / 上限: 600s

## 保守側の校正対象

D50 では系側 gate が stock より +61〜99% 高 throughput であり、trace transaction 数も 増えるため、stock 校正は extime を過大選択しうる。絶対 throughput 最大と見込む read-heavy (rr95) × g_rl を最重条件として校正した。

他 workload/構成で個別 verify が 600s を超える見込みが出た場合は extime を下げる。事前登録済みの N_verify は削らない (phase3-main-experiment.md 層 1 (iv 付属) の安全弁)。

## 候補

| extime | trace run | trace | verifier | maxrss | txns | edges | verdict |
|---:|---:|---:|---:|---:|---:|---:|---|
| 3s | 3.51s | 48 files / 1.75GiB / 57660545 lines | 433.33s | 25.68GiB | 5283740 | 80726086 | serializable |
| 6s | 6.84s | 48 files / 3.53GiB / 114012094 lines | 974.73s | 51.43GiB | 10447714 | 172771102 | serializable |

## 選定規則

extime 3,6,10 を昇順に各 1 回実測し、verifier walltime <= 600s の最大値を採る。walltime > 600s で残候補を打ち切り、extime=3 も超過なら候補なしとして失敗する。verdict != serializable または certified != true は校正全体を失敗させる。

詳細な構成 provenance と全候補の生値は同名 JSON に記録した。
