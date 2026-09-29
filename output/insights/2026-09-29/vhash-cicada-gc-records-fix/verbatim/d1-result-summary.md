# 診断走行 D1 の結果 (job d1、request 36143.nqsv、bnode023、2026-09-29 22:27:31〜22:28:27 JST、dispatch rc=0、起動器 rc=0)

原本: runs/d1/result-CUSTOM.json (sha256 82317192dc84397a7cc521327e0947052a37bf978e32524a0138fcb1256a3ec7)、raw stderr = runs/d1/raw/CUSTOM/*.stderr。
起動器 launch_gcfix_run.py sha256 40b82f60…f660、診断 patch diag/diag-cicada-gc-records.patch sha256 568ce542…996b (Codex author-d-1)。
計測木 gcfix-m1 (main 8fe87f852、detached)。F cell (43/4/4/4、warehouse 1、extime 1、group_commit 0)、base F 25898d00、TRACE=0、CMake 値は md_17 と同じ。

| build | thread | 5 回の結果 |
|---|---|---|
| DIAG_F_T0 (F + 診断 patch) | 4 | 5 回とも rc=1、gc_records の ERR (診断 dump あり) |
| DIAG_F_T0 | 8 | 5 回とも rc=1、同上 |
| F_T0 (F 無 patch、同じ job) | 4 | 5 回とも rc=1、`transaction.cc 853 gc_records` |
| F_T0 | 8 | 5 回中 4 回 rc=1 (同上)、r2 だけ rc=0 で完走 |

ERR dump 10 件の機械照合 (起動器の parse_gcdiag、版ポインタで ABORTED_INSTALL と DELETE_COMMIT を引く) — **10 件すべて `aborted-delete-over-deleted`**:
- 表はすべて 5 = NewOrder (include/tpcc/tpcc_tables.hh の列挙順)。
- 版鎖は「aborted の削除版 (他 thread の wts) → deleted の版」が 9 件、「aborted → aborted → deleted」が 1 件 (t4-r2、2 本の後発削除が重なった)。
- aborted 版はすべて op=DELETE、abort の段は validation の read set 再検査 (a) (`read_recheck`)、その下の版は deleted。
- 最初の非 aborted 版 (deleted) は、ERR した thread 自身が commit した削除版 (DELETE_COMMIT の thid = ERR の thid が 10/10)。

run ごと (err_thid・key・版鎖・abort 段):
- t4-r1 thid 3 key 000100010000001c aborted@t2>deleted@t3 read_recheck
- t4-r2 thid 0 key 000100010000000b aborted@t1>aborted@t2>deleted@t0 read_recheck×2
- t4-r3 thid 0 key 0001000100000006 aborted@t2>deleted@t0
- t4-r4 thid 3 key 0001000100000004 aborted@t0>deleted@t3
- t4-r5 thid 0 key 0001000100000004 aborted@t3>deleted@t0
- t8-r1 thid 2 key 0001000100000012 aborted@t7>deleted@t2
- t8-r2 thid 3 key 0001000100000009 aborted@t7>deleted@t3
- t8-r3 thid 5 key 0001000100000007 aborted@t6>deleted@t5
- t8-r4 thid 5 key 0001000100000013 aborted@t4>deleted@t5
- t8-r5 thid 1 key 0001000100000012 aborted@t6>deleted@t1

副次の観測 (ABORTED_INSTALL の (op, 段, 下の版) 別件数、全 run): `DELETE|node_set|committed` が最多 (1 run 23〜276 件、scan の node 版検査で abort した削除版が committed の版の上に aborted で残る。gc_records には入らない)、`DELETE|read_recheck|deleted` 2〜6 件、`DELETE|write_rts|committed` 0〜10 件、`DELETE|install_wts|pending` 1 run で 10 件、`DELETE|read_recheck|committed` 0〜1 件。

判定: md_17 の仮説 (P1) を支持する。機序 = 2 本の Delivery が同じ NewOrder 行を削除し合い、後発 (wts 大) が先発の削除版 D1 の上に自分の削除版 D2 を install した後、read set 再検査 (D2 の tx は D1 以前の committed 版を読んでいた) で abort し、writeSetClean が D2 を aborted にして版鎖に残す。D1 を commit した thread の gc_records が最新版 = aborted の D2 を見て ERR。仮説のうち「(b) の deleted 検査で abort」の経路は今回の 10 件では観測されず、全件 (a)。
限界: 診断出力は stderr への書き込みで時間を変えうる (無 patch の対照も t4 5/5、t8 4/5 で落ちたので、到達の有無は変わっていない)。1 job・1 ノードの 20 走行。
