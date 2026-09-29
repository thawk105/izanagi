## 所見

原文ファイルの基点は `/work/1/SFC/tanab/tmp/vhash-motivation-evidence-2026-09-29/src/`。README・reading-notes と照合し、保存原文の `.txt` で20点以上を確認した。

- **A1 / must-fix / §5.1 M1** — 「長い tx が1本あると、それより新しい版もまとめて回収が止まる」は、README 自身が挙げる途中版の剪定と矛盾する。根拠: `src/R3/bottcher-pvldb2019.txt` §5.7 は “EPO removes all versions as soon as they are not required by any active transaction anymore.” と述べる。**直し方:** 回収できないのは「長い tx から見えうる版」であり、不要な途中版は回収できる、と書く。
- **A2 / must-fix / §5.2 C4** — 「prepared tx は結果が確定済み」は誤り。根拠: `src/R1/pg-vacuum.txt` §24.1.5 は “Such transactions should be committed or rolled back.” と記す。**直し方:** commit／rollback が未決のまま待機し、アクセス駆動の前進が発火しない主体、と説明する。
- **A3 / should-fix / §5.2 C2** — 「read-write tx を扱う」は試作の適用範囲より広い。根拠: `docs/paper-story-vhash/2026-09-29b.md` §6.1 は scan・insert・delete を含む tx を「試作では前進しない」と明記する。**直し方:** C2 のうち前進を許す操作・条件に限定し、特殊操作は別行にする。
- **A4 / should-fix / §3 timeout の行** — 3種類の PostgreSQL 設定をまとめて「上限を超えた tx・session を終わらせる」とするのは不正確。根拠: `src/R1/pg-runtime-client.txt` §19.11 の `statement_timeout` は “Abort any statement that takes more than the specified amount of time.”、`transaction_timeout` は “Terminate any session…” と区別する。**直し方:** 文の中止、tx／session の終了、idle session の終了を設定ごとに書き分ける。
- **A5 / should-fix / §4.2 C3** — PostgreSQL の idle in transaction と MongoDB の「放置された tx」を、**読み取り後に待つ** C3 の直接の根拠とするのは分類を絞りすぎる。根拠: `src/R1/pg-runtime-client.txt` は “an open transaction prevents vacuuming away recently-dead tuples…”、`src/R2/mongo-prod.txt` は “When you abandon a transaction, abort the transaction.” と述べ、直前に読み取りをしたかは指定しない。**直し方:** 両文書は「idle／放置された tx」一般の根拠とし、C3 の具体的な操作列は md_2 の条件として示す。
- **A6 / should-fix / §2.1 冒頭・§3 末尾** — 「時間型は回収が止まらない」「時間型は長い読み取りを失敗させる」は例外を落としている。根拠: `src/R2/spanner-tsbounds.txt` は “The only exception is Partition Read/Query with partition tokens, which will prevent garbage collection of expired data while the session remains active.” と明記する。**直し方:** 通常の読み取りについての説明とし、Spanner の partition token、CockroachDB の protected timestamp を併記する。
- **A7 / should-fix / §3 末尾** — 「tx 型の製品は、既定では長い tx を生かして回収を止め」は TiDB の既定上限と両立しない。根拠: `src/R2/tidb-sv.txt` の `tidb_gc_max_wait_time` は “Default value: 86400”、`src/R2/tidb-gcconf.txt` は超過後に “the GC safe point is forwarded forcefully.” とする。**直し方:** 期限なしで待つ設定と、既定の待機上限がある設定を分ける。
- **B1 / should-fix / §4.1** — 「本文・図表の説明文にある数値」の表に、数値がない Wu と HyPer、版・GC が原因ではない Sirin を置くと動機づけに使える実測と混同しやすい。根拠: `src/R3/hyper-mvcc-sigmod2015.txt` の該当文は条件を述べる定性文で、R3 reading-notes §R3-8 は Sirin の原因を LLC・メモリ帯域と記す。**直し方:** 数値表は Steam・vDriver・HANA・LeanStore に絞り、残りは短い「使わない／反対側の材料」注に移す。
- **B2 / nit / §0・§4.2・§5.2・§8** — 「研究の数値は C1 で、C2 の痛みとして使えない」という重要な制限が繰り返される。根拠: `src/R3/bottcher-pvldb2019.txt` Table 5 と `src/R3/hana-hybridgc-sigmod2016.txt` §5 の条件は読み手側の実験。**直し方:** §0 と主張対応表には残し、§8 は参照だけにする。
- **B3 / should-fix / 成果物** — 指定資料からは、依頼 `md_27.txt` の成果物「spool fragment」の所在を確認できない。**直し方:** fragment の保存先を README に記す。射影外のファイルは点検していないため、欠落の断定ではない。

## 照合した点の一覧

| README の節・点 | 原文 file | 判定 |
|---|---|---|
| §0・§2.2 PostgreSQL の容量増加 | `src/R1/pg-vacuum.txt` §24.1 | 一致 |
| §0・§2.2 PostgreSQL の残り300万 tx で XID 割当拒否 | `src/R1/pg-vacuum.txt` §24.1.5 | 一致 |
| §2.2 PostgreSQL の警告開始4000万 tx | `src/R1/pg-vacuum.txt` §24.1.5 | 一致 |
| §2.2 idle in transaction と bloat | `src/R1/pg-runtime-client.txt` §19.11 | 一致 |
| §3 PostgreSQL の3設定の既定値0 | `src/R1/pg-runtime-client.txt` §19.11 | 一致 |
| §3 `statement_timeout` が tx／session を終わらせるとの一括説明 | `src/R1/pg-runtime-client.txt` §19.11 | **不一致** |
| §2.1・§2.2 MySQL の undo 保持と領域増加 | `src/R1/my-innodb-multi-versioning.txt` §17.3 | 一致 |
| §3 `innodb_max_purge_lag` 既定0・DML 遅延 | `src/R1/my-innodb-purge-configuration.txt` §17.8.9 | 一致 |
| §2.1 Aurora MySQL の “either read or write” | `src/R1/aws-aurora-rbs.txt` | 一致 |
| §2.2 SQL Server の tempdb／ADR 満杯時の失敗操作 | `src/R2/mssql-rowver.txt` | 一致 |
| §2.2 PVS の「50%近く」 | `src/R2/mssql-adr-troubleshoot.txt` | 一致。ただし診断上の目安 |
| §3 MongoDB の既定60秒と定期的 abort | `src/R2/mongo-prod.txt`、`mongo-txn-limit.txt` | 一致 |
| §3 Oracle の保持保証による DML 失敗 | `src/R2/oracle-undo19.txt` §16.2.2.3 | 一致 |
| §3 TiDB の既定86,400秒と強制前進 | `src/R2/tidb-sv.txt`、`tidb-gcconf.txt` | 一致 |
| §3 Spanner の既定1時間・古い読取の失敗 | `src/R2/spanner-tsbounds.txt` | 一致。ただし partition token は例外 |
| §4.1 Steam の平均287.43／1.07、最大30,287／2 | `src/R3/bottcher-pvldb2019.txt` Table 5 | 一致 |
| §4.1 Steam の6,554／30,580 txn/s | `src/R3/bottcher-pvldb2019.txt` Table 5 | 一致 |
| §4.1 HANA の408,664 query 中6 cursor・1時間超 | `src/R3/hana-hybridgc-sigmod2016.txt` §1 | 一致 |
| §4.1 HANA の3.79億／1.18億版 | `src/R3/hana-hybridgc-sigmod2016.txt` §5.2 | 一致 |
| §0・§4.1 LeanStore の「sleep する snapshot」と性能崩壊 | `src/R3/alhomssi-leanstore-si-pvldb16-2023.txt` §1・§2 | 一致 |
| §4.1 vDriver の「10⁴」 | `src/R3/vdriver-techreport.txt` §5.2.1 | **未照合**。抽出テキストは `104`。README §1.1 の PDF 文字配置による判断は、このレビューでは再検証していない |
| §4.2 md_2 の32／2048／32768 µs、1.03e6→1.41e6、約3000試行 | `output/insights/2026-09-29/vhash-cicada-version-measure/README.md` §0 | 一致 |

## 総括

must-fix **2件**、should-fix **7件**。主要な実測値と製品設定値は概ね一致する。
**判定: A1・A2 を修正し、適用範囲と例外を明記してから動機づけの根拠として使用。**