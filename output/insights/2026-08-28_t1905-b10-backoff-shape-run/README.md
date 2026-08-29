# T-1905 B-10 待ち方 grid probe — 物理残差 gate で停止

## 結論

修理後の計算ノード probe は18 cellを生成して正常終了したが、事前登録済みの
`maximum_absolute_deviation_pct_exclusive = 1.0` を4 cellが超えた。規律2に従い上限を緩めず、
`docs/b10-backoff-shape-preregistration.md` §5はplaceholderのまま維持した。
したがって発効版、formal build、workload別verify/perf、最終formal reportは生成していない。

## 実行 identity

- source commit: `8df4fa25da01311e887336b6f454f6d33ec28a2c`
- placeholder prereg commit: `1549bd92794d72e05aeafe5903568f7d9023614d`
- request: `953543.nqsv`
- host: `bnode142`
- nonce: `6f8cea40fcf2193f4e4157e9c89adde1`
- probe result SHA-256: `6e7d8ed7d27be091ce94de4b85ac61a50e99d97167e75c4328e8a54982224bc3`
- submission receipt SHA-256: `782b25fc0aecf78d0aa9dfa36ef2d036c777eb171b3ebe654405b7364dc7eb54`
- `clocks_per_us`: 2100、calls/cell: 100000

raw full precisionは同directoryの `probe-result.json` が正本である。`submit-receipt.json` と
`job-result.json` もrepo外durable rootのbytesをそのまま保全した。

## gateを超えたcell

| shape | mean_us | realized_mean_cycles | commanded_mean_cycles | deviation_pct |
|---|---:|---:|---:|---:|
| binary | 2 | 4382.71288 | 4200 | 4.350306666666667 |
| binary | 5 | 10742.28884 | 10500 | 2.307512761904755 |
| binary | 10 | 21313.97052 | 21000 | 1.4950977142857091 |
| binary | 50 | 106971.61978 | 105000 | 1.8777331238095178 |

最大偏差は binary / 2 us の 4.350306666666667%。1.0% はexclusive上限なので、exactに1.0%でも拒否する。

## 修理と検証

- compute jobのmodule起動からisolated modeだけを外し、repo root cwdの `-B -m` に揃えた。
- 関連test: target node 1 passed、B-10 file 55 passed。
- 変異matrix: baseline PASSED、`-I`復帰 1/1 KILLED、SURVIVED 0、MISMATCH 0。
- `check_codex_agents`、`check_docs`、implementation commit後の全履歴provenanceは緑。

## 残る範囲

このprobeは待機ループの物理残差だけを測った。throughput、正しさcertification、shape効果、
過抑制域、ピーク位置、balanced profile、要求待ち量分布は未取得である。
formal performanceの既存認可を実経路で確認する段にも到達していない。
