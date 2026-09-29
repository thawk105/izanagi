# 確認走行 V3 の結果 (scan-key 修理の初版 174135c7… を含む)

V3a: request (runs/v3a.log)、bnode125、2026-09-29 23:59:37〜00:01:39 JST (UTC 14:59:37〜15:01:39)、起動器 rc=1 (ASAN_FIX2_WA_F の期待外、下記)。
V3b: bnode125、00:02:07〜00:04:39 JST、起動器 rc=0。原本 runs/v3a・runs/v3b の result-CUSTOM.json。起動器 stage6/launch_gcfix_run.py (sha256 056fca8c…)、spec-v3a.json・spec-v3b.json。
fix2 = stage6/fix-cicada-gc-records.patch (2c9cb880…) → stage6/fix-cicada-gc-records-scan-key.patch (174135c7…)。

**V3a (TRACE=0・ASan、38 run。追補裁定の見積り 48 は誤り):**
| build | run | 結果 | 期待 | 判定 |
|---|---|---|---|---|
| F_T0 (無修理、同時刻対照) | F×t4×5、F×t8×5 | 10/10 rc=1、gc_records の ERR | thread ごとに ERR ≥ 1 | 満たす |
| FIX2_F_T0 | F×t4×10、F×t8×10 | 20/20 rc=0 | 全 rc=0 | 満たす |
| C_FIX2_T0 (pin C) | F×t4×3 | 3/3 rc=0 | 全 rc=0 | 満たす |
| ASAN_F_M (F 無 patch、M cell = 削除なし) | M×t4×2 | 2/2 AddressSanitizer heap-use-after-free (writeSetClean ← abort、freed by abort の INSERT tuple delete) | record-only | 新事実 U が修理・削除と無関係に stock で起きることの帰属 |
| ASAN_FIX2_WA_F (F + fix2 + U 回避) | F×t4×3 | 3/3 とも実行中の `ERROR: AddressSanitizer` 0 件・gc_records の ERR 0 件で完走 (commit_counts 9,381 / 8,695 / 8,003)。終了時に LeakSanitizer の「detected memory leaks」(TxExecutor・初期 load の Tuple・insert の版など、終了時に解放しない領域) が出て rc=1 | rc=0 かつ ASan 報告 0 | **事前登録の文言は満たさない** (rc≠0 は終了時の leak 報告による)。実行中のメモリ誤用の報告 0 という実質は満たす。修理分岐がこの build で発火した回数は測っていない (計数 patch を入れていない) |

**V3b (TRACE=1):**
| run | 判定 | 巡回 | integrity 数値 12 項目 (存在履歴違反を含む) | C 行 = commit 数 | READ_WTS_MISMATCH | W op D (thread 数) | 読み飛ばし回収 |
|---|---|---|---|---|---|---|---|
| FIX2_F_TRACE F t4 r1 | indeterminate | 0 | 全 0 | 34,554 = 34,554 | 0 | 2,980 (4) | 561 |
| 同 r2 | indeterminate | 0 | 全 0 | 33,693 = 33,693 | 0 | 3,520 (4) | 499 |
| 同 r3 | indeterminate | 0 | 全 0 | 34,240 = 34,240 | 0 | 3,270 (4) | 533 |
| FIX2_F_TRACE M t4 ×2 | indeterminate ×2 | 0 | 全 0 | 41,859 / 44,096 一致 | 0 | 0 | 0 |
| FIX2_F_TRACE R2 t4 ×2 | indeterminate ×2 | 0 | 全 0 | 30,336 / 31,079 一致 | 0 | 0 | 0 |
| SKIPRC_FIX2_F_TRACE F t4 (M3) | **non-serializable** | 586 | 全 0 | 15,361 一致 | 0 | 6,550 (4) | 0 |
identity (FIX2_F_TRACE の前): (F + fix2) 対 (F + instr + instr-tpcc + fix2)、TRACE=0、tpcc の 3 TU で compile command 一致・命令列一致、nm・strings 一致。
起動器の期待: FIX2_F_TRACE = trace-pass 満たす、SKIPRC = trace-cycles 満たす。
