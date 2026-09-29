# L0 (生死確認) の結果 — job l0-a (35456.nqsv、bnode017、2026-09-29 15:42〜15:46 JST)

原本: `runs/l0-a/result-L0-TPCC.json`、dispatch log `runs/l0-a.log` (rc=1)。wave commit `4878ab37c` (計測木 cicvext-m-l0)、起動器 sha256 `ceddfa39…a2`、g++ 11 (`/usr/bin/x86_64-linux-gnu-g++-11`)。

## stock TPC-C (C1' + instr + tpcc 重ね patch、TRACE=1)

| run | 判定器 rc | verdict | 巡回 | integrity 数値項目 | existence | C 行 = commit | READ_WTS_MISMATCH | 版順検査 4 項 | trace bytes / 行 |
|---|---|---|---|---|---|---|---|---|---|
| M t1 | 3 | indeterminate | 0 | 全 0 | 0 | 30,984 = 30,984 | 0 | 全 true | 41,242,137 / 978,380 |
| M t4 | 3 | indeterminate | 0 | 全 0 | 0 | 42,676 = 42,676 | 0 | 全 true | 55,413,144 / 1,308,200 |
| F t1 | 3 | indeterminate | 0 | 全 0 | 0 | 18,543 = 18,543 | 0 | 全 true | 42,337,348 / 1,009,650 |
| F t4 | — | — | — | — | — | — | — | — | — |

- **F t4: benchmark が rc=1 で異常終了。** stderr: `CICADA_TRACE_INITIAL_WTS=38694472998797056` / `ERROR: Success` / `… cc/cicada/transaction.cc  853  gc_records` / `CICADA_TRACE_READ_WTS_MISMATCH n=0`。853 行は `gc_records()` の `if (latest->ldAcqStatus() != VersionStatus::deleted) ERR;` (pin C でも 853 行。計装の追加はこれより後ろの行なので行番号はずれない)。
- 親の静的な読み (未実証): Delivery 2 本が同じ NewOrder 行を削除し合うと、wts の大きい側が先に commit された削除版 D1 の上に自分の削除版 D2 を install した後で validation に落ち、`writeSetClean()` が D2 を `aborted` にする。D2 は tuple の最新版に残るので、D1 側の `gc_records()` が最新版を deleted でないと見て `ERR` する。stock Cicada の delete 経路の欠陥と読めるが、trace を外した build で起きるかは未確認。

## TRACE=0 の命令列比較 (絶対規律 1)

同じ compile command (root だけ置換で一致を確認)、objdump の命令列を正規化して比較。

| 比較 | target | TU | 命令列 | 前処理の差 (空行以外) |
|---|---|---|---|---|
| (i) pin C 対 pin C + instr | tpcc / bomb / sbomb | 各 transaction.cc・util.cc・workload TU | 9 TU とも差分 0 byte | 0 行 (空行だけ 1〜6 行) |
| (ii) pin C 対 C1' + instr + tpcc 重ね patch | tpcc | transaction.cc・util.cc・tpcc_cicada.cc | 3 TU とも差分 0 byte | 0 行 (空行だけ 1〜6 行) |

nm・strings は 4 系列とも全文一致、trace 語の残存 0 (both_clean)。
