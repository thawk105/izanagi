# [T-1582] MoCC TRACE=0 性能 pilot — `058d0c4e` source の単一観測

- 日付: 2026-08-24
- environment: Pegasus `gen_S`、`bnode033`、Intel Xeon Platinum 8468、48 physical cores、HT off
- outer source: `d8ea4111aa03cf34722baaa2f40458347e4f75df`
- ccbench source: `058d0c4e5f237d88ec1c2ebe0739113d82906e47`
- request: `942177.nqsv`、submission nonce `3511e3b90a74ba4ff28e6472e4a07505`
- receipt SHA-256: `1a62ba3abb4d4253ec8fe0af6f8ce2938f5af2e7d59505c9e5dae7596ba60bee`
- binary SHA-256: `3f5b48c2942e90e4d484376db87a974df5fecf9f17f5081878cac4ebdcc6c8c3`

## 結果

TRACE=0 の MoCC YCSB pilot は次の単一観測を得た。

| 項目 | 値 |
|---|---:|
| completed transactions | 1,060,263 |
| workload elapsed | 3.078599114 s |
| throughput | **344,397.877326226 txns/s** |
| average latency | 2.9036183607274797 us |

workload は records=10,000、threads=48、zipf skew=0.9、read ratio=50、RMW=0、max operations=10、extime=3秒である。値はstdoutの一意な`commit_counts_` witnessとmonotonic elapsedから再計算し、`throughput.json`、pilot receipt、job resultの値と一致した。

## correctness と source binding

- build は `CCBENCH_TRACE=0`、target `ycsb_mocc.exe`。TRACE=0 preprocess identity checkerはrc=0、`result=pass`で、8 genome × 2 overlay = 16 context/fileを実行した。
- workload rc=0。TRACE=0 runなのでverifierは`not-run`であり、trace artifactを性能値の正しさ証明へ読み替えない。
- submit receipt、job-side copy、pilot receipt、job result、scheduler accountingのrequest IDは正規化後`942177.nqsv`で一致した。
- outer HEADは投入前からterminal・証拠退避まで`d8ea4111…`で固定した。ccbenchのbase `511c9538…`と計測source `058d0c4e…`の束縛も一致した。
- receiptは`pilot=true`、`official_certification=false`、`eligible_for_refreeze=false`。throughputの`measurement_role`は`pilot-only; not official calibration`である。

## fail-closedした先行attemptと修正

1. `941866.nqsv`: 計算ノード既定`python3`が3.10未満でchecker importが失敗した。checker rc=1、workloadはskip、throughputは未生成。D95 Codex authorがPython 3.10+ resolverを`eea2ac59133e5193b32ade382a25ea90be096373`で実装した。焦点テスト9 passed、変異matrixはbaseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0、実装受入はchild-green。
2. `941979.nqsv`: 初回jobが共有hydrate destinationへ残したMasstree ignored build artifactを次jobが検出し、build前にfail-closedした。汚染された`thirdparty-src`だけを証拠保全後に除去し、cache pinを再検証した。
3. `942177.nqsv`: cleanなhydrate destinationから完走し、上記throughputを得た。

いずれの失敗でもchecker・verifier・correctness gateを緩めていない。無効なattemptのthroughputを後付け生成していない。

## 射程と留保

- これは1回のpilot raw observationであり、official calibration、certified選択、refreezeの入力ではない。
- 既存TRACE=1 evidenceは別source `ef9328a3`である。**same-source pairing、TRACE=1/0 speedup、回帰・優劣の比較は行わない。**
- job内`qstat -x`はPegasusで非対応のため`qstat_accounting_rc=1`だが、親側はrequest消失とPBS stderrの同一ID `Ended Request Time`をterminal receiptへ束縛した。job成功判定はpilot receipt/job-result/外側terminalの積で行った。
- 共有hydrate destinationをjob buildがin-placeで汚染する再attempt間の問題は、本pilot値を変えないscope外所見として専用handoffへ残した。本waveではper-attempt staging化を実装しない。

## repo外一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1582-mocc-trace0-pilot/evidence/`に3attemptを保全した。

- attempt 1: 78 files / 58,295 bytes、manifest SHA-256 `4fdb19d7719710e4c7d7b6344fee2166a136310cd65d86defc2281f695351728`
- attempt 2: 912 files / 76,214,963 bytes、manifest SHA-256 `fe261db4afac02e4f41a0c40a2da3ffbf23bccff7495c7333cdc0becfca81539`
- attempt 3: 945 files / 76,268,348 bytes、manifest SHA-256 `e11fd9ea66b4fc22babd5333da5d61e2d48341e2d5f6f88f3a97d5987a8e9b33`
- attempt 3 validation: `validation.json` (`status=verified`)

各attemptはrepo内sourceとrepo外copyのpath/type/size/SHA-256完全一致を確認してから、`output/env/pegasus/mocc-trace/{attempts,job-staging}`と当該PBS stdout/stderrを限定削除した。成功attemptでは共有hydrate stagingも同じmanifestへ含めてから除去した。
