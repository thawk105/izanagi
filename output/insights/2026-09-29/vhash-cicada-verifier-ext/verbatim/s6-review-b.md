### B1 GC 異常の原因を delete に確定しすぎている

重大度: **should**。根拠: [一次資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:16)、[R9 裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/s4-ruling.md:93)、原本 `runs/gc-a/result-GC-PROBE.json` の `runs.*.rc` と `runs.*.error`。F t4 は pin C・TRACE=0 でも 5/5 回 `gc_records` で止まるが、削除競合という機序は一次資料自身が未実証の仮説としている。

放置すると、一次資料と次の一手が「F t4 で再現した GC 異常」を「delete 経路の原因確定」「delete を含む並行 TPC-C はすべて完走不能」へ広げて伝える。推奨対処: 再現条件を F t4 に限定し、「計装なしでも再現する」と記す。delete 競合は仮説として維持し、修理 item も原因調査から始める。

### B2 insert 変異の「巡回として検出」は完了分類の条件に入っていない

重大度: **should**。根拠: [依頼](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/request-md_17.txt)、[R4 裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/s4-ruling.md:45)、[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:657)。β の分類は orphan read と事象の一致で成立し、巡回を要求しない。一方、原本 `runs/j1-a/result-J1-TPCC.json` の `runs.INSERT_PAST_TS_TPCC-R2-t4.summary.total_cycles` は **1** で、一次資料はその rw 辺を insert 事象に手動照合している。

放置すると、完了判定は「insert の壊しを巡回として検出」という依頼の字義を、実際には orphan read と別の変異 α の巡回で代替したままになる。推奨対処: β の巡回 witness と事象の照合を原本に機械可読で残し、**観測された β の巡回**を字義への直接の根拠として記す。事前登録した orphan read の合否は変更しない。新しい壊しや追加走行は要らない。

### B3 起動器に今回使わない旧 job・cell が残る

重大度: **nit**。根拠: [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:37) の旧 YCSB build・cell・job と `J1-FOCUS`・`S`。原本の job は `L0-TPCC`、`J1-TPCC`、`GC-PROBE` のみ。

放置すると、再利用者が今回の受入範囲と未実行の経路を取り違えやすい。推奨対処: 計測に使った起動器は hash とともに保存し、公開する再実行手順では今回の三つの job だけを列挙する。歴史的原本を書き換える必要はない。

## 総括

- **条件付き採用可。** 新 patch 2 本は、TPC-C の v3 出力と insert 変異に必要な範囲に収まる。
- L0・J1 の stock **5 走行**の巡回・integrity・存在履歴違反は原本と一致する。F t1 の raw trace には `D` 行が **7,700 件**ある。
- β の orphan read **1,144,962 件**と事象一致、α の代表 witness **20/20 件**は原本と一致する。
- TRACE=0 の **12 TU** は原本で命令列一致を確認できる。
- delete の正例を作らない裁定は、F t4 の異常終了を踏まえた本 wave の範囲指定として妥当。ただし並行 delete の判定が済んだとは扱えない。
- 一次資料の GC 原因・適用範囲を狭め、β の巡回帰属を依頼の字義に対応する根拠として明示してから採用する。
- 一次資料が明記する campaign 接続、phantom、certified の未対応は維持する。stock の GC 修理を本 wave に追加する必要はない。