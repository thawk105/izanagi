# R2 読書メモ: Oracle・SQL Server・MongoDB・分散 DB

取得はすべて 2026-09-29 (JST) に curl で実施。原文は /work/1/SFC/tanab/tmp/vhash-motivation-evidence-2026-09-29/src/R2/ (`*.html` が原本、`*.txt` は本文化)。HTTP status は特記なければ 200。SHA-256 は先頭 16 桁。
本文化は単純なタグ除去のため、Cockroach / TiDB の一部でリンク付き語句 (inline 部品) が欠落している。引用は欠落のない文だけを使った。

---
### R2-1 Oracle Database 19c Database Administrator's Guide, ch.16 "Managing Undo"
- URL: https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-undo.html / 版: 19c / 取得 2026-09-29T22:40:32 / SHA b50b0c7c1dc7a8d2 / src/R2/oracle-undo19.html
- 併読: 同 23 版 (oracle-database/23/admin/managing-undo.html, SHA 302c57d49af315d7, 22:40:34): 保持保証の記述は同じ (該当節で確認)。
- 併読: Database Reference 19c "UNDO_RETENTION" (https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/UNDO_RETENTION.html, 22:41:17, SHA 9e85bc50738ae38b)。
- 併読: ORA-30036 (https://docs.oracle.com/en/error-help/db/ora-30036/, 22:41:17, SHA f3cae3257523d2bd)。
- 読んだ節: 16.2.2 The Undo Retention Period / 16.2.2.1 (About the Undo Retention Period) / 16.2.2.2 Automatic Tuning of Undo Retention / 16.2.2.3 Retention Guarantee / 16.2.2.5 Tracking the Tuned Undo Retention Period / undo 領域アラートの節。
- (a) 症状:
  - 「Long-running queries could fail with a snapshot too old error, which means that there was insufficient undo data for read consistency.」(16.2.2.2)
  - 「DML could fail because there is not enough space to accommodate undo for new transactions.」(16.2.2.2、固定サイズ undo 表領域が小さすぎる場合)
  - UNDO_RETENTION ページ: 「If an active transaction requires undo space and the undo tablespace does not have available space, then the system starts reusing unexpired undo space. This action can potentially cause some queries to fail with a "snapshot too old" message.」
  - ORA-30036 の Cause: 「the specified undo tablespace has no more space available.」 Action: 「Add more space to the undo tablespace before retrying the operation. An alternative is to wait until active transactions to commit.」
- (b) 機構: 古い committed undo は「consistent read purposes, long-running queries may require this old undo information」(16.2.2.1) のために保持される。「unexpired」= 保持期間より新しい undo。回収境界は時間ベース (retention 期間) で、tx の生存 (最古の読み手) そのものではない。auto-tuning は「somewhat longer than the longest-running active query」に保持期間を伸ばす (AUTOEXTEND 時、16.2.2.2)。
- (c) 対処:
  - AUTOEXTEND 表領域: UNDO_RETENTION 分は保持し、領域不足時は「instead of overwriting unexpired undo information, the tablespace auto-extends」、MAXSIZE 到達で「the database may begin to overwrite unexpired undo information」(16.2.2.1)。
  - RETENTION GUARANTEE: 「the database never overwrites unexpired undo data even if it means that transactions fail due to lack of space in the undo tablespace」。さらに「Enabling retention guarantee can cause multiple DML operations to fail. Use with caution.」(16.2.2.3) = 長い読みを守る代償として書き込み tx を失敗させる方向の設定が公式に存在する。
  - 監視: V$UNDOSTAT の TUNED_UNDORETENTION (16.2.2.5)。長い query 由来の SNAPSHOT TOO OLD アラートは「at most once every 24 hours」(アラート節)。
- (d) 数値: UNDO_RETENTION 既定値 900 (秒) (Reference "Default value 900")、範囲 0 〜 2^31-1。「The warning alert threshold defaults to 70%」(16.2.2.4 近傍) 。それ以外の容量倍率は書かれていない。
- (e) 区別: 原因は「long-running queries」(読み) と Flashback / Active Data Guard のスタンバイ読み (UNDO_RETENTION ページ: 「In Oracle Active Data Guard environments, you may want to increase the value of UNDO_RETENTION on the primary instance in order to accommodate undo retention requirements on the standby instances.」)。read-write tx の長さによる undo 回収停止の記述は、読んだ範囲では別事項 (ORA-30036 の Action に active transactions を待てとある程度)。
- 怪しい記述: なし。ORA-30036 の文書は同一項が 3 回重複表示 (ページ構造)。
- 補足: 「ORA-30036」は Managing Undo の本文には現れない (grep 0 件)。error-help ページのみ。

---
### R2-2 SQL Server (Microsoft Learn) の row versioning と ADR
- 版: いずれも `view=sql-server-ver17` (SQL Server 2025 系列の文書表示)。
  - Transaction locking and row versioning guide: https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver17 / 22:40:34 / SHA fdd80a84700cc1f2 / src/R2/mssql-rowver.html
  - Accelerated database recovery (ADR): .../accelerated-database-recovery-concepts?view=sql-server-ver17 / 22:40:35 / SHA 8944a078872eb801
  - Monitor and troubleshoot ADR: .../accelerated-database-recovery-troubleshoot?view=sql-server-ver17 / 22:41:58 / SHA 36ac482d72fe4f50
  - sys.dm_tran_persistent_version_store_stats: .../sys-dm-tran-persistent-version-store-stats?view=sql-server-ver17 / 22:40:35 / SHA 90ee3cd8d6f937b4
  - ADR management: .../accelerated-database-recovery-management?view=sql-server-ver17 / 22:40:35 / SHA 0dbfe38ea15f420d
- 読んだ節: rowver guide の "Space used in tempdb"、"Row versioning resource usage"、"Monitor row versioning and the version store"、"Manage long-running transactions"。ADR の Persistent version store (PVS)・Design goals。troubleshoot の "Examine the size of the PVS" 以下。
- (a) 症状:
  - tempdb 満杯時: 「update operations stop generating versions but continue to succeed, but read operations might fail because a particular row version that is needed doesn't exist.」(rowver guide、version store 節)
  - ADR で version store 満杯時: 「read operations continue to succeed but write operations that generate versions, such as UPDATE and DELETE fail.」(同)
  - 強制 shrink: 「the longest running transactions that haven't yet generated row versions are marked as victims. A message 3967 is generated in the error log for each victim transaction.」victim が版を読もうとすると「message 3966 is generated and the transaction is rolled back」、また版が作られなかった箇所へのアクセスは error 3958 (Space used in tempdb)。
  - PVS: 「Long-running transactions ... can delay version cleanup and increase PVS size.」(ADR 文書の推奨節)。「If the database doesn't have enough room for PVS to grow, ADR might fail to generate versions, causing DML statements to fail.」
  - ログ: 「it holds up log truncation indefinitely, causing the transaction log to grow and possibly fill up. If the transaction log fills up, the database can't perform any more writes.」(Manage long-running transactions。版ではなくログの話だが同型の症状)
- (b) 機構: 「A long-running transaction prevents space in the version store from being released if it meets any of the following conditions: It uses row versioning-based isolation. It uses triggers, MARS, or online index build operations. It generates row versions.」(Space used in tempdb)。また「when the SNAPSHOT isolation level is enabled, although a new transaction won't hold locks, a long-running transaction will prevent the old versions from being removed from the version store.」(Manage long-running transactions)。troubleshoot 文書は PVS 肥大の原因を 4 つ列挙: 「Long-running active transactions / Long-running active snapshot scans / Long-running queries on secondary replicas / Aborted transactions」。snapshot scan の詳細: 「Snapshot scans can, therefore, prevent PVS cleanup in any database on the same database engine instance.」(instance 単位の timestamp のため)。secondary は「a long-running query on a secondary replica can also hold up ghost cleanup」。
- (c) 対処:
  - 監視: sys.dm_tran_version_store_space_usage (安価)、sys.dm_tran_top_version_generators / sys.dm_tran_version_store は「can be expensive, since both scan the entire version store」。性能カウンタ Version Generation rate (KB/s)・Version Cleanup rate (KB/s)・Version Store Size (KB)。PVS は sys.dm_tran_persistent_version_store_stats (oldest_active_transaction_id, min_transaction_timestamp, persistent_version_store_size_kb など)。
  - 判定: 「PVS is considered large if it's significantly larger than the baseline or if it's close to 50% of the database size.」
  - 操作: 「consider killing the session, if allowed」、「Consider a different isolation level, such as READ COMMITTED, instead of SNAPSHOT or RCSI for long-running queries that are delaying PVS cleanup.」、elastic pool では DB を pool 外へ。診断クエリの既定閾値例 `@LongTxThreshold int = 900` (秒) と `@LongTransactionLogBytes bigint = 1073741824`。sys.sp_persistent_version_cleanup で同期的に強制清掃、SQL Server 2022 以降 multi-threaded PVS cleanup。
  - 自動の強制 abort: tempdb 満杯時の victim 化 (上記) のみ。時間上限で自動 kill する設定は、読んだ範囲では記述なし。
- (d) 数値: 「[size of common version store] = 2 * [version store data generated per minute] * [longest running time (minutes) of the transaction]」(Monitor row versioning... 節、性能カウンタ説明)。PVS の 50%、上記 900 秒 / 1073741824 バイトの診断閾値例。ほかに実測倍率なし。
- (e) 区別: 原因は「long-running transaction」全般 (snapshot 分離を使う tx、版を生成する tx、trigger/MARS/オンラインインデックス)。read-only の snapshot scan と secondary replica の読み取りは別項として明記される。普通の read-write tx (版を生成する tx) も明示的に原因。
- 怪しい記述: なし。ページ内に「Summarize this article for me」等の UI 文言があるがページ機能の残骸で、指示ではない。

---
### R2-3 MongoDB Manual: Production Considerations (Transactions) / Parameters / Read Concern "snapshot"
- URL: https://www.mongodb.com/docs/manual/core/transactions-production-consideration/ / 22:40:37 / SHA d5dee471e38d3a8f
- URL: https://www.mongodb.com/docs/manual/reference/parameters/ / 22:41:21 / SHA 39a9d74a8c53ca60
- URL: https://www.mongodb.com/docs/manual/reference/read-concern-snapshot/ / 22:42:01 / SHA 6b309ae6fbc24e34
- 版: 「manual」(unversioned = 取得時の current)。ページに "MongoDB 9.0" の宣伝表示があるが、どの版の manual かは断定できていない。
- 読んだ節: Production Considerations の "Runtime Limit"・"WiredTiger Cache"。Parameters の transactionLifetimeLimitSeconds・minSnapshotHistoryWindowInSeconds。Read Concern "snapshot" の Important 注記。
- (a) 症状: 「If you have an uncommitted transaction that causes excessive pressure on the WiredTiger cache, the transaction aborts and returns a write conflict error.」「If a transaction is too large to ever fit in the WiredTiger cache, the transaction aborts and returns a TransactionTooLargeForCache error.」(WiredTiger Cache)。snapshot 読み: 「A read operation that lasts longer than minSnapshotHistoryWindowInSeconds may terminate.」。過去読み: 古い atClusterTime は SnapshotTooOld error。
- (b) 機構: 「To prevent storage cache pressure from negatively impacting the performance: When you abandon a transaction, abort the transaction.」 = 放置された tx が cache 圧力の原因。記述はここまでで、版の蓄積の内部機構までは書かれていない。
- (c) 対処: 「By default, a transaction must have a runtime of less than one minute. You can modify this limit using transactionLifetimeLimitSeconds ... Transactions that exceeds this limit are considered expired and will be aborted by a periodic cleanup process.」(Runtime Limit)。「The transactionLifetimeLimitSeconds also ensures that expired transactions are aborted periodically to relieve storage cache pressure.」 Parameters: 「Default: 60」「The cleanup process runs every transactionLifetimeLimitSeconds/2 seconds or at least once every 60 seconds.」「The minimum value ... is 1 second.」
  - スナップショット履歴: minSnapshotHistoryWindowInSeconds 「Default: 300」、「Increasing the value of minSnapshotHistoryWindowInSeconds increases disk usage.」
- (d) 数値: transactionLifetimeLimitSeconds 既定 60、掃除間隔は上限 60 秒、minSnapshotHistoryWindowInSeconds 既定 300、最小 1 秒 (上記逐語)。それ以外なし。
- (e) 区別: 対象は multi-document transaction (read-write / read 両方を含む tx) の寿命上限。長い read-only 分析専用の扱いは別に "Perform Long-Running Snapshot Queries" 節があるが、その本文までは読んでいない (見出しの存在のみ確認)。
- 怪しい記述: ページ冒頭に「For AI agents: a documentation index is available at https://www.mongodb.com/docs/llms.txt」という AI 向け誘導文がある。従わず、記録のみ。

---
### R2-4 CockroachDB: Storage Layer / Configure Replication Zones
- URL: https://www.cockroachlabs.com/docs/stable/architecture/storage-layer / 22:40:37 / SHA 88f0e9e56f93c9f9
- URL: https://www.cockroachlabs.com/docs/stable/configure-replication-zones / 22:40:37 / SHA c688ea6dec5e0902
- 版: stable。HTML 内の版表記は v26.3 が最多 (v26.2 も出現) だが、どの版か文書自体の明示は未確認。
- 読んだ節: Storage layer の "Garbage collection"・"Protected timestamps"、Replication zones の gc.ttlseconds。
- (a) 症状: gc.ttlseconds を大きくしすぎる場合: 「Setting the GC TTL too high can cause problems if the retained versions of a single row approach the maximum range size.」。版が溜まる側の性能: 「A shorter GC TTL means that fewer previous MVCC values are kept around. This can help lower query execution costs for workloads which update rows frequently throughout the day」。
- (b) 機構: 「Garbage collection can only run on MVCC values which are not covered by a protected timestamp.」「When a long-running job such as a backup wants to protect data at a certain timestamp from being garbage collected, it creates a protection record」(How protected timestamps work)。つまり GC を止めるのは長い job (backup 等) の保護 record であり、通常の SQL tx ではない。読んだ範囲では、長い SQL tx が GC を止める記述は Storage layer / Replication zones には無い。むしろ GC は TTL で切れ、「Larger values increase the interval allowed for queries」(gc.ttlseconds) = TTL より長い読みは許されない設計。
- (c) 対処: gc.ttlseconds は cluster / database / table 単位で設定。「Default: 14400 (4 hours)」。「The smallest value we regularly test is 600 (10 minutes)」「The largest value we regularly test is 90000 (25 hours)」。「Increasing the GC TTL is not meant to be a solution for long-term retention of history」。job 終了時は protection record を削除。
- (d) 数値: 上記 (14400 / 600 / 90000)。
- (e) 区別: 止めるのは backup 等の長い job の保護 record (固定 snapshot 型)。普通の read-write tx についての記述なし。
- 怪しい記述: 本文化で inline 語句が欠落する箇所があり (「configuring the .」など)、引用は欠落のない文に限った。

---
### R2-5 TiDB: Garbage Collection Overview / Configuration / System Variables
- URL: https://docs.pingcap.com/tidb/stable/garbage-collection-overview/ (22:40:40, SHA 5e1d2f7088c9e14a)、.../garbage-collection-configuration/ (22:40:40, SHA 321ab00126651baa)、.../system-variables/ (22:40:41, SHA 1035499b65044ba4)
- 版: stable。system-variables の HTML に v8.5.3 の言及が最多だが、取得時の stable が何版かは文書に明記なし (未確認)。
- 読んだ節: Overview (GC 機構)、Configuration の "Changes in TiDB 6.1.0"、System variables の tidb_gc_life_time・tidb_gc_max_wait_time。
- (a) 症状: 「If the transaction is too long, the safe point will be blocked for a long time, which affects the application performance.」(Configuration、Changes in TiDB 6.1.0)。tidb_gc_life_time の注: 「a large value (days or even months) ... may cause potential issues, such as: Larger storage use」、「A large amount of history data may affect performance to a certain degree, especially for range queries such as select count(*) from t」。
- (b) 機構: 「Before TiDB v6.1.0, the transaction in TiDB does not affect the GC safe point. Starting from v6.1.0, TiDB considers the startTS of the transaction when calculating the GC safe point, to resolve the problem that the data to be accessed has been cleared.」(Configuration)。Overview: 「the safe point does not exceed the start time (start_ts) of the ongoing transactions.」tidb_gc_life_time: 「If there is any transaction that has been running longer than tidb_gc_life_time, during GC, the data since start_ts is retained for this transaction to continue execution.」
- (c) 対処: tidb_gc_max_wait_time: 「the maximum time that active transactions block the GC safe point. After the value is exceeded, the GC safe point is forwarded forcefully.」(Configuration) / 「If the runtime of active transactions does not exceed this variable value, the GC safe point will be blocked until the runtime exceeds this value.」(System variables)。tidb_gc_life_time は「Default value: 10m0s」、範囲 [10m0s, 8760h0m0s] (Self-Managed / Dedicated)。GC 実装側: Compaction Filter GC で「avoids extra disk read caused by GC」「avoids a large number of left tombstone marks which degrade the sequential scan performance」。
- (d) 数値: tidb_gc_max_wait_time 「Default value: 86400」(秒 = 24 時間、単位は原文 "Unit: Seconds")、範囲 [600, 31536000]。tidb_gc_life_time 既定 10m0s。GC 起動間隔「GC is triggered every 10 minutes」(Overview)。
- (e) 区別: tx 種別の区別は書かれていない (「active transactions」一般)。強制的に safe point を進めた場合にその tx が読む版が失われる点は、読んだ範囲では明記されていない (「forwarded forcefully」とのみ)。
- 怪しい記述: なし。

---
### R2-6 Google Cloud Spanner: PITR / Timestamp bounds
- URL: https://cloud.google.com/spanner/docs/pitr (22:40:42, SHA 7ae7b0ed632e5520)、https://cloud.google.com/spanner/docs/timestamp-bounds (22:43:21, SHA dbf48ac8661c0c1e, 「Last updated 2026-09-24 UTC」)
- 読んだ節: PITR の Performance considerations、Timestamp bounds の "Maximum timestamp staleness"。
- (a) 症状: 保持期間を伸ばした場合: 「Increased storage utilization」「Increased CPU usage and latency. Spanner uses additional computing resources to compact and maintain earlier versions of data.」「Increased time to perform schema updates.」。読み側: 「Reads and SQL queries with too-old read timestamps fail with the error FAILED_PRECONDITION.」
- (b) 機構: 版の回収は時間基準。「Version garbage collection reclaims versions after they expire past a database's version_retention_period」(Maximum timestamp staleness)。長い tx が回収を止めるのではなく、「This restriction also applies to in-progress reads or SQL queries with timestamps that become too old while executing.」= 実行中でも保持期間を超えれば失敗する。例外: 「Partition Read/Query with partition tokens, which will prevent garbage collection of expired data while the session remains active.」(固定 snapshot が回収を止める唯一の記述)。
- (c) 対処: 「By default, your database retains all versions of its data and schema for one hour. You can increase this time limit to as long as seven days through the version_retention_period option.」(PITR)。timestamp-bounds 側は「defaults to 1 hour, but can be configured up to 1 week」と書いており、PITR 文書 (7 日) と表現が異なる。
- (d) 数値: 既定 1 時間、上限 7 日 (PITR) / 1 週 (timestamp-bounds)。
- (e) 区別: 通常の tx が GC を止めるとは書かれていない (読んだ範囲)。止めるのは partition token を使う分析読みのみ。
- 怪しい記述: なし。

---
### R2-7 YugabyteDB: yb-tserver reference
- URL: https://docs.yugabyte.com/preview/reference/configuration/yb-tserver/ / 22:40:45 / SHA e94b1db7127af410 (preview 版。版番号は未確認)。併読: .../architecture/transactions/transactional-io-path/ (22:43:25, SHA a77c29b4bd265fc2)。
- 読んだ節: flag `--timestamp_history_retention_interval_sec` (同名 flag が 2 箇所)、transactional-io-path の MVCC 説明。
- (a)(b) 症状・機構: 「Point-in-time reads at a hybrid time prior to this interval might not be allowed after a compaction and return a Snapshot too old error.」 = Spanner と同型の時間基準。長い tx が回収を止める記述は、読んだ範囲では無い。
- (c) 対処: 「Set this to be greater than the expected maximum duration of any single transaction in your application.」
- (d) 数値: 「Default: 900 (15 minutes)」。
- (e) 区別: 書かれていない。「A long-running read operation ... can proceed concurrently with write operations modifying the same key.」(transactional-io-path) と、長い読みが書きを止めない点のみ。
- 怪しい記述: 同 flag の説明が 1 ページ内に 2 箇所あり、片方は説明が短い (版差の混在の可能性、未確認)。

---
### R2-8 SAP HANA (help.sap.com)
- 失敗。検索で "Version Garbage Collection Issues" (https://help.sap.com/docs/SAP_HANA_PLATFORM/bed8c14f9f024763b0777aa72b5436f6/bfa4b65c2bd441c58f46b8f4b9e44bb4.html) の存在は分かったが、本文は取得できていない。
- 試行: curl で同 URL は HTTP 200 だが 1160 バイトの SPA 殻 (「SAP Help Portal | SAP Online Help」のみ、SHA f1fc6e13c197e64f、src/R2/hana-vgc2.html)。pagecontent API は HTTP 500。WebFetch も殻だけで内容なし。別ミラーは 2 回試して諦めた。
- WebSearch の要約は事実として使わない契約のため、症状・数値は書かない。

---
## 取得失敗の一覧
- SAP HANA: help.sap.com の本文 (SPA 殻のみ)。
- YugabyteDB: .../architecture/transactions/read-restart/ は HTTP 404 (使っていない)。.../explore/backup-restore/point-in-time-recovery-ysql/ は 459 バイトの殻で内容なし。
- Oracle: .../19/errmg/ORA-29950.html は 404 (URL 推測の誤り、使っていない)。ORA-30036 は error-help ページで取得。
- 内容が別 URL と同一 (fragment のみの違い): mongo-txn-prod2 / mongo-txn-limit / crdb-pts / crdb-mvcc / crdb-gcttl / yb-tserver2 / yb-ysql-timeout (SHA 同一で確認済み、追加情報なし)。

## 確かめたこと / 確かめていないこと
確かめた:
- Oracle の retention guarantee の副作用 (DML 失敗)、UNDO_RETENTION 既定 900、ORA-30036 の Cause/Action を原文で確認。
- SQL Server の版 store 満杯時の症状、長い tx が解放を止める条件、PVS 肥大の 4 原因、診断 DMV と閾値例を原文で確認。
- MongoDB の transactionLifetimeLimitSeconds 既定 60・強制 abort・cache 圧力の関係、minSnapshotHistoryWindowInSeconds 既定 300。
- TiDB の safe point が tx の start_ts で止まること、tidb_gc_max_wait_time 既定 86400 秒で強制前進すること。
- Spanner / YugabyteDB / CockroachDB の gc は時間基準の TTL が中心。tx 由来の停止は CockroachDB の protected timestamp (長い job) と Spanner の partition token だけ。

確かめていない:
- MongoDB "Perform Long-Running Snapshot Queries" の本文、WiredTiger 内部で古い snapshot が版を保持する機構の記述。
- Oracle: ORA-01555 (md_1 既読)、Oracle の長い tx が undo を回収不能にする記述は本文で確認できていない。
- TiDB / Cockroach / Yugabyte の実際の版番号 (stable / preview 表示のみ)。
- SAP HANA の全内容。
- 各社の設定既定値が過去版でも同じかどうか (取得時点の版のみ)。
