---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1582-mocc-trace0-pilot
seq: 1
title: [T-1582] MoCC TRACE=0 pilotでreceiptとthroughputを取得した
---

## 本文

- ccbench `058d0c4e`をsourceとするTRACE=0 MoCC pilotをPegasus gen_Sで実施した。一次資料は`output/insights/2026-08-24_t1582-mocc-trace0-pilot.md`。
- 成功request `942177.nqsv`は1,060,263 transactions / 3.078599114秒、throughput 344,397.877326226 txns/s。checker pass、workload rc=0、source/job/receipt/binary/terminal binding一致を確認した。
- 先行2attemptはPython 3.10未満と共有hydrate staging汚染でfail-closedし、throughputを生成しなかった。Python resolver修正commitは`eea2ac59`、変異はbaseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0、実装受入はchild-green。
- 3attemptのrepo内生成物はrepo外へ完全copy・hash照合してから限定削除し、成功attemptのmanifest SHAは`e11fd9ea66b4fc22babd5333da5d61e2d48341e2d5f6f88f3a97d5987a8e9b33`。各投入でuntracked 0、終端までHEAD固定、退避後tree cleanを実測した。
- 結果はpilot-only、official certification false、eligible for refreeze false。別sourceのTRACE=1 evidenceとのsame-source比較は行わず、certified選択を変更していない。

## 次の一手差分

### 完了

- [T-1582] `058d0c4e` sourceのTRACE=0 MoCC pilotを完走し、receiptとthroughputを記録した。
  remaining: none
  base: 8cb2e07e1f7754b69847bc26f92c1676200f5f0f9b6d0a13b8a4ee9dcf390e99
