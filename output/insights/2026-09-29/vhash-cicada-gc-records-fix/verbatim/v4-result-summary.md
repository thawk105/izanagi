# 確認走行 V4 の結果 (最終 patch での取り直し。構成は V3 と同じ、scan-key patch だけ予備付きの最終版)

V4a: request 36425.nqsv、bnode020、2026-09-30 00:17:12〜00:19:15 JST、Elapse 129 秒、起動器 rc=1 (ASAN_FIX2_WA_F の期待外、下記)。
V4b: request 36426.nqsv、bnode138、00:17:13〜00:19:58 JST、Elapse 171 秒、起動器 rc=0。
原本 runs/v4a・runs/v4b の result-CUSTOM.json。起動器 stage7/launch_gcfix_run.py (= stage6、sha256 056fca8c…)、spec-v4a.json・spec-v4b.json (spec-v3a/b の stage6 → stage7 置換)。
fix2 = stage7/fix-cicada-gc-records.patch (2c9cb880…、wave commit 278daafee と同一) → stage7/fix-cicada-gc-records-scan-key.patch (9e397f39…、wave commit bf24ae053 と同一)。計数 patch は stage5/count-gcfix-skips.patch (ea0d4a49…)。

**V4a (TRACE=0・ASan、38 run):**
| build | run | 結果 | 期待 | 判定 |
|---|---|---|---|---|
| F_T0 (無修理、同時刻対照) | F×t4×5、F×t8×5 | t4 5/5・t8 4/5 が gc_records の ERR (t8 の 1 回は完走) | thread ごとに ERR ≥ 1 | 満たす |
| FIX2_F_T0 | F×t4×10、F×t8×10 | 20/20 rc=0 | 全 rc=0 | 満たす |
| C_FIX2_T0 (pin C) | F×t4×3 | 3/3 rc=0 | 全 rc=0 | 満たす |
| ASAN_F_M (F 無 patch、削除なし) | M×t4×2 | 2/2 heap-use-after-free (writeSetClean ← abort、U) | record-only | U は stock の既存欠陥 |
| ASAN_FIX2_WA_F (F + fix2 + U 回避) | F×t4×3 | 3/3 とも実行中の `ERROR: AddressSanitizer` 0 件・gc_records の ERR 0 件で完走 (commit_counts 6,684 / 9,019 / 9,140)。終了時 LeakSanitizer (解放しない領域) で rc=1 | rc=0 かつ ASan 報告 0 | 文言は満たさない (終了時の leak 報告)、実行中のメモリ誤用 0 は満たす |

**V4b (TRACE=1):**
| run | 判定 | 巡回 | integrity 数値 (存在履歴違反を含む) | C 行 = commit 数 | READ_WTS_MISMATCH | W op D (thread 数) | 読み飛ばし回収 |
|---|---|---|---|---|---|---|---|
| FIX2_F_TRACE F t4 r1 | indeterminate | 0 | 全 0 | 34,829 = 34,829 | 0 | 3,020 (4) | 555 |
| 同 r2 | indeterminate | 0 | 全 0 | 33,447 = 33,447 | 0 | 3,570 (4) | 607 |
| 同 r3 | indeterminate | 0 | 全 0 | 18,608 = 18,608 | 0 | 890 (4) | 179 |
| FIX2_F_TRACE M t4 ×2 | indeterminate ×2 | 0 | 全 0 | 41,633 / 43,378 一致 | 0 | 0 | 0 |
| FIX2_F_TRACE R2 t4 ×2 | indeterminate ×2 | 0 | 全 0 | 31,049 / 30,522 一致 | 0 | 0 | 0 |
| SKIPRC_FIX2_F_TRACE F t4 (M3) | **non-serializable** | 386 | 全 0 | 13,447 一致 | 0 | 5,190 (4) | 0 |
identity: (F + fix2) 対 (F + instr + instr-tpcc + fix2)、TRACE=0、tpcc の 3 TU で compile command・命令列一致、nm・strings 一致。
