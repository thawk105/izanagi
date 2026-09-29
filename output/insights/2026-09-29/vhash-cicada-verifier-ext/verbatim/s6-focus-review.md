## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| A1 α の表照合 | **closed** | [修正後の起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:550) は事象の `tx_wts` から C 行の txn を求め、その txn の R 行から key・`a_wts` に対応する表を復元し、[辺の表と比較する](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:623)。表は辺から取得しておらず、照合は恒真ではない。再計算 JSON の `runs.SKIP_READ_RECHECK_TPCC-M-t4.attribution` は `table_recovery.recovered_events=3604`、`unattributable_events=0`、`edge_table_mismatches=0`、`witness_count=20`。 |
| B1 GC 原因・範囲の限定 | **partial** | [一次資料 §5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:98) は再現条件を F cell × 4 thread に限定し、delete 競合の機序を未実証の仮説と明記した。原本の `runs/l0-a/result-L0-TPCC.json → runs.STOCK_TPCC-F-t4` と `runs/gc-a/result-GC-PROBE.json → runs.*.{rc,error}` は同じ `gc_records` 異常を計 11/11 回示す。ただし[結論の「trace の影響ではなく」](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:18)と[「delete 経路が並行下で」](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:124)は、確認できた「TRACE=0 でも F t4 で再現」より強い。 |
| B2 β の巡回帰属 | **closed** | [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:655) は stderr の事象と判定器の rw 理由を表・key・`a_wts`・`b_wts` で比較する。辺から事象を作っておらず恒真ではない。再計算 JSON の `runs.INSERT_PAST_TS_TPCC-R2-t4.cycle_attribution` は `witness_count=1`、`match_count=5`、`examples[0].cycle=[5,397]`。 |
| B3 未使用 job・cell の区別 | **closed** | [一次資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:151) は実測した 3 job、未使用の YCSB 系・J1-FOCUS・S、起動器の hash を明記した。J1 版の実際の SHA-256 は `12de8bd7…a15f3d`、修正後は `36ef9330…dd3ccd` で記載と一致する。 |

## 新しい所見

### N1 — should：B1 の限定表現が結論まで反映されていない

根拠：[一次資料の結論](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:18)は trace の影響を否定するが、原本が示すのは TRACE=0・TRACE=1 の双方で F t4 の異常が再現したこと。[§7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:124)の「delete 経路」も機序確定と読める。影響：B1 の範囲限定が要約で失われる。推奨：双方を「F cell × 4 thread で、trace の有無に依らず `gc_records()` 異常を観測」に揃える。

## 総括

修正前後の [`classify_break`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:750) を比較すると、α の巡回・witness 1 件以上、β の orphan read・件数一致・帰属 1 件以上という**合否条件は変更されていない**。β の巡回帰属は観測値として追加されている。原本・再計算 JSON は、stock 5 走行、GC 11/11 回、α の代表 20/20 件、β の orphan read 1,144,962 件全件、TRACE=0 の 12 TU という docs の件数を支持する。残る修正点は B1 の結論表現である。