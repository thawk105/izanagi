### A1 α の v3 帰属で表を照合していない

**重大度:** must-fix
**根拠:** 既存の [skip-read-recheck patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/patches/broken-cicada-skip-read-recheck.patch:24) の事象には `table` がない。[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:567) は `event["table"] is None` なら表照合を省く。原本 `runs/j1-a/result-J1-TPCC.json` の `runs.SKIP_READ_RECHECK_TPCC-M-t4.attribution.examples[0].matches[0]` でも、`event.table=null`、辺の `table=0` である。
**影響:** 異なる表の同じ key・版でも α を「期待した経路で検出」と分類でき、[一次資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:117) の「表付き v3 witness で帰属」という主張の証明が欠ける。今回の誤帰属そのものを示す所見ではない。
**推奨対処:** 保存済み raw trace の事象 txn・key・`a_wts` に一致する R から表を一意に復元し、辺の表と照合する。欠落・複数候補は帰属不能にして、20 witness の分類を再計算する。段 4 裁定 R4 の「表を記録」も「表を照合」へ明確化する。

## 総括

現状の α の帰属分類を根拠にした採用は保留する。
表照合を追加し、保存済み J1 原本で α が再び条件を満たせば、この所見は解消できる。
L0・GC・J1 の要約値は原本 JSON と照合した。F t4 の異常終了は pin C・TRACE=0 でも再現し、親が記した機序は仮説として区別されている。
β の単一の意味変更、raw orphan の数え直しと事象照合、stock 合否条件には追加所見はない。
TRACE=0 比較は指定された 12 TU で compile command、命令列、trace 語の結果を確認した。
delete の並行履歴、phantom、campaign 接続は一次資料でも未対応と明記されている。