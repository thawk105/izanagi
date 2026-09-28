# 生死確認 L0 の実測結果 (親の要約、2026-09-29 04:3x JST)

原本: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/runs/l0-b/result-L0.json (起動器 sha256 fcd86dd2d4903d4fe974bb3ee7be340971f41acf20dfd3d6278d594030360c8d、checkout 2eb59beca、request 33776.nqsv、Elapse 101 s)。
1 回目 l0-a (33768.nqsv、Elapse 30 s) は起動器の compile command 選択 (workload 別 target が 4 件) で停止し、fix-l0-1 で直した。

## run (build = pin + instr-cicada-trace.patch、TRACE=1、CMake 値は s4-ruling R1 C5 どおりと cache で確認)

| run | 判定 | 巡回 | integrity 数値項目 | C 行 = commit_counts_ | READ_WTS_MISMATCH | 全 W > initial_wts |
|---|---|---|---|---|---|---|
| K-t1 | indeterminate (verifier rc 3) | 0 | 全 0 | 191730 = 191730 | 0 | 真 (893230 W) |
| K-t4 | indeterminate | 0 | 全 0 | 178445 = 178445 | 0 | 真 (832386 W) |
| W-t1 | indeterminate | 0 | 全 0 | 213879 = 213879 | 0 | 真 (1003345 W) |
| W-t4 | indeterminate | 0 | 全 0 | 193316 = 193316 | 0 | 真 (906677 W) |

proof surfaces は X/P/I とも unavailable (cicada は対象外) なので `integrity.clean` は構造上つねに false。

## TRACE=0 同一性 (pin と instr patch、同じ compile command modulo root)

- 命令列 (objdump 正規化): transaction.cc・ycsb_cicada.cc・util.cc の 3 TU とも差分 0 byte。
- nm / strings: 全文一致、trace 残存 (`izanagi_trace`・`CICADA_TRACE`) 0。
- 前処理出力: 行 marker を除いても一致しないが、差分は空行の増減だけ (空行以外の差分行 0)。

## 起動器の欠陥 (単位 B で直す)

`launch_cicada_run.py:590-596` の合否集計が `integrity.clean is True` を要求するため、cicada では常に failed (rc=1) になる。事前登録の L0 期待は「integrity の数値項目 0」であり clean ではない。前処理比較も「空行だけの差」を不一致として扱う。
