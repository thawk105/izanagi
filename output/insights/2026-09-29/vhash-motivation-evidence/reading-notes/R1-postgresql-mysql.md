# R1 読書メモ: PostgreSQL / MySQL InnoDB / AWS Aurora の公式文書

原文置き場: /work/1/SFC/tanab/tmp/vhash-motivation-evidence-2026-09-29/src/R1/ (`<名>.html` が原文、`<名>.txt` が本文化、fetch*.sh・fetch*.log が取得記録)。
取得日は全て 2026-09-29 (JST)。PostgreSQL の「current」は取得時点で **18** (各ページ題に "Documentation: 18")。

## 出典一覧 (取得記録)

| ID | URL | HTTP | 取得時刻 (JST) | SHA-256 先頭16桁 | 保存 |
|---|---|---|---|---|---|
| R1-PG-VAC | postgresql.org/docs/current/routine-vacuuming.html (PG18 §24.1) | 200 | 22:40:39 | 568c632ab04dc2eb | pg-vacuum.html |
| R1-PG-CLIENT | .../current/runtime-config-client.html (PG18 §19.11) | 200 | 22:40:41 | c898282005582247 | pg-runtime-client.html |
| R1-PG-HS | .../current/hot-standby.html (PG18 §26.4) | 200 | 22:40:42 | a1a44a5c462467b5 | pg-hot-standby.html |
| R1-PG-REPL | .../current/runtime-config-replication.html (PG18 §19.6) | 200 | 22:40:44 | 9a633320c7c0a63f | pg-runtime-replication.html |
| R1-PG-SLOTS | .../current/view-pg-replication-slots.html | 200 | 22:40:45 | ab73173d7120fe3b | pg-view-slots.html |
| R1-PG-STAT | .../current/monitoring-stats.html | 200 | 22:40:47 | 16f5d160ed15a512 | pg-monitoring-stats.html |
| R1-PG15-RES | .../docs/15/runtime-config-resource.html (PG15 §20.4) | 200 | 22:40:50 | dfd36ce7f7245e72 | pg15-runtime-resource.html |
| R1-PG15-REPL | .../docs/15/runtime-config-replication.html (PG15 §20.6) | 200 | 22:42:41 | b9b23a77d51b44ee | pg15-runtime-replication.html |
| R1-PG-REL17 | .../docs/release/17.0/ (題は Documentation: 18 の Release 17) | 200 | 22:40:53 | 931375c44a64eda4 | pg-rel-17.html |
| R1-PG-REL16 | .../docs/release/16.0/ | 200 | 22:40:55 | da7eb17079c92e9f | pg-rel-16.html |
| R1-MY-MVCC | dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html (§17.3) を Wayback 経由 (snapshot 20260917121333) | 200 (直接は403) | 22:41:09 | af371c2c8606bca0 | my-innodb-multi-versioning.html |
| R1-MY-PURGE | .../innodb-purge-configuration.html (§17.8.9)、Wayback 20260927185402 | 200 | 22:41:11 | e2799baad634080b | my-innodb-purge-configuration.html |
| R1-MY-UNDO | .../innodb-undo-tablespaces.html (§17.6.3.4)、Wayback 20260523112629 | 200 | 22:41:12 | de8299f18030e317 | my-innodb-undo-tablespaces.html |
| R1-MY-STATUS | .../innodb-standard-monitor.html、Wayback 20260812074923 | 200 | 22:41:21 | c491c4c8e807f18b | my-innodb-standard-monitor.html |
| R1-MY-METRICS | .../innodb-information-schema-metrics-table.html、Wayback 20260513195831 | 200 | 22:41:23 | f46e0435ca65245a | my-innodb-information-schema-metrics-table.html |
| R1-AWS-HLL | docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/proactive-insights.history-list.html (Aurora MySQL「InnoDB history list length が大きく増えた」) | 200 | 22:40:58 | 5930a351dcdb38b2 | aws-aurora-rbs.html |
| R1-AWS-PARAM | .../AuroraMySQL.Reference.ParameterGroups.html (Aurora MySQL parameters) | 200 | 22:43:00 | 6b1282a69bc8a0ba | aws-aurora-txtimeout.html |
| R1-AWS-PGBLK | .../Appendix.PostgreSQL.CommonDBATasks.Autovacuum_Monitoring.Resolving_Identifiableblockers.html (Aurora PostgreSQL) | 200 | 22:43:37 | 19b827be993ae207 | aws-aurorapg-blockers.html |

MySQL は 8.4 Reference Manual (各ページ題 "MySQL 8.4 Reference Manual")。Wayback は archive.org 上の保存物で、dev.mysql.com 原本の逐語コピーと想定するが、原本との一致は確かめていない (下記)。

---

### R1-PG-VAC PostgreSQL 18 §24.1 Routine Vacuuming
- 読んだ節: 24.1 冒頭、24.1.1 Vacuuming Basics 〜 24.1.5 Preventing Transaction ID Wraparound Failures (XID wraparound、multixact)
- (a) 症状:
  - 容量: 「the row version must not be deleted while it is still potentially visible to other transactions. But eventually, an outdated or deleted row version is no longer of interest to any transaction. The space it occupies must then be reclaimed for reuse by new rows, to avoid unbounded growth of disk space requirements. This is done by running VACUUM.」(§24.1)。bloat の語: 「it may get bloated to the point that VACUUM FULL is really necessary to reclaim space」(§24.1.2 相当の autovacuum 段落)。
  - 可用性 (wraparound): 「the system will refuse to assign new XIDs once there are fewer than three million transactions left until wraparound」、エラー「database is not accepting commands that assign new transaction IDs to avoid wraparound data loss」。「In this condition any transactions already in progress can continue, but only read-only transactions can be started. Operations that modify database records or truncate relations will fail.」(§24.1.5)。警告は wraparound の 4000 万 tx 手前から (「reach forty million transactions from the wraparound point」)。
- (b) 原因の機構: §24.1.5 の復旧手順 3 項が、境界 (oldest XID) を止める主体を列挙している。
  - 「Resolve old prepared transactions. You can find these by checking pg_prepared_xacts ... Such transactions should be committed or rolled back.」
  - 「End long-running open transactions. You can find these by checking pg_stat_activity for rows where age(backend_xid) or age(backend_xmin) is large. Such transactions should be committed or rolled back, or the session can be terminated using pg_terminate_backend.」
  - 「Drop any old replication slots. Use pg_replication_slots to find slots where age(xmin) or age(catalog_xmin) is large.」
  - 「Running transactions and prepared transactions can be ignored if there is no chance that they might appear in a multixact.」「Unlike transaction ID wraparound, replication slots do not directly hold back multixact cleanup.」
- (c) 既存の対処: 上記の commit / rollback / pg_terminate_backend / slot の drop / VACUUM。自動失効の機構はこの節に無い (timeout は R1-PG-CLIENT)。
- (d) 数値: 「autovacuum_freeze_max_age ... The default, 200 million transactions」「pg_xact ... about 50MB」「pg_commit_ts about 2GB」(§24.1.5; 既定値 200M 時)、最大 20 億で「pg_xact ... about half a gigabyte and pg_commit_ts to about 20GB」。警告開始 40,000,000 tx、拒否開始 3,000,000 tx。multixact: 「if the storage occupied by multixacts members exceeds about 10GB, aggressive vacuum scans will occur more often」「can grow up to about 20GB before reaching wraparound」。
- (e) 区別: §24.1.5 は「long-running open transactions」(read-write / read-only の別なし)、prepared tx、replication slot を並べる。固定 snapshot を要求する read-only 分析を特に名指しする記述は、この節を読んだ範囲では無い。
- 怪しい記述: なし。
- 補足: §24.1 (Recovering Disk Space) には「xmin horizon が止める」という用語は本文中に無かった (grep で "horizon" は freeze の文脈のみ)。horizon の語は backend_xmin の説明 (R1-PG-STAT) にある。「dead but not yet removable」「removable cutoff」の説明は、取得した PG18 の routine-vacuuming / sql-vacuum / progress-reporting の本文化物には見つからなかった (VACUUM VERBOSE 出力の説明は本文化物内の grep "removable" で 0 件)。

### R1-PG-CLIENT PostgreSQL 18 §19.11 Client Connection Defaults (timeouts)
- 読んだ節: statement_timeout / transaction_timeout / idle_in_transaction_session_timeout / idle_session_timeout
- (a) 症状: 「an open transaction prevents vacuuming away recently-dead tuples that may be visible only to this transaction; so remaining idle for a long time can contribute to table bloat. See Section 24.1 for more details.」(idle_in_transaction_session_timeout)
- (b) 機構: idle in transaction の open tx が recently-dead tuple の回収を止める (上記引用)。「an idle session without a transaction imposes no large costs on the server」(idle_session_timeout)。
- (c) 対処と既定値:
  - idle_in_transaction_session_timeout: 「Terminate any session that has been idle ... within an open transaction for longer than the specified amount of time. ... A value of zero (the default) disables the timeout.」
  - transaction_timeout: 「Terminate any session that spans longer than the specified amount of time in a transaction. ... A value of zero (the default) disables the timeout.」「Prepared transactions are not subject to this timeout.」
  - statement_timeout: 「A value of zero (the default) disables the timeout.」「Setting statement_timeout in postgresql.conf is not recommended because it would affect all sessions.」(transaction_timeout も同型の警告)
  - transaction_timeout の導入版: PG17 release notes に「Add server variable transaction_timeout to restrict the duration of transactions」(R1-PG-REL17)。
- (d) 数値: 3 種とも既定 0 (無効)。
- (e) 区別: idle in transaction (何もしていない tx) を特に問題視。read-only か否かの区別は書かれていない。
- 怪しい記述: なし。

### R1-PG-HS PostgreSQL 18 §26.4 Hot Standby (§26.4.2 Handling Query Conflicts)
- (a) 症状: 主 (primary) 側: 「this will delay cleanup of dead rows on the primary, which may result in undesirable table bloat」。standby 側: 「tables that are regularly and heavily updated on the primary server will quickly cause cancellation of longer running queries on the standby」。
- (b) 機構: 「The most common reason for conflict between standby queries and WAL replay is “early cleanup”. Normally, PostgreSQL allows cleanup of old row versions when there are no transactions that need to see them ... However, this rule can only be applied for transactions executing on the primary.」また「Application of a vacuum cleanup record from WAL conflicts with standby transactions whose snapshots can still “see” any of the rows to be removed.」
- (c) 対処: 「The first option is to set the parameter hot_standby_feedback, which prevents VACUUM from removing recently-dead rows and so cleanup conflicts do not occur. ... the cleanup situation will be no worse than if the standby queries were running directly on the primary server」。または max_standby_archive_delay / max_standby_streaming_delay (「a finite value ... can be considered similar to setting statement_timeout」、「-1 which means wait forever」)。
- (d) 数値: 数値は R1-PG-REPL 側 (既定 30 秒、feedback 既定 off)。
- (e) 区別: standby で走る「longer running queries」(読取専用) が標的。read-only の長い問合せが primary の GC を止める構造が明示されている (hot_standby_feedback 経由)。
- 怪しい記述: なし。

### R1-PG-REPL PostgreSQL 18 §19.6 Replication (standby 設定) と PG15 版
- (c)(d): hot_standby_feedback: 「can cause database bloat on the primary for some workloads」「The default value is off.」。max_standby_streaming_delay / archive_delay: 「The default is 30 seconds. A value of -1 allows the standby to wait forever」。
- vacuum_defer_cleanup_age (PG15 §20.6 の本文): 「Specifies the number of transactions by which VACUUM and HOT updates will defer cleanup of dead row versions. The default is zero transactions, meaning that dead row versions can be removed as soon as possible, that is, as soon as they are no longer visible to any open transaction.」「You should also consider setting hot_standby_feedback on standby server(s) as an alternative to using this parameter.」
- 削除: PG16 release notes 「Remove the server variable vacuum_defer_cleanup_age (Andres Freund)」「This has been unnecessary since hot_standby_feedback and replication slots were added.」(R1-PG-REL16)。ページ直接取得の 16 版 runtime-config-replication.html (sha 55320d4f5f86f147) は、本文化物に vacuum_defer_cleanup_age の項が無いことは grep で確認していない (release notes を根拠とする)。

### R1-PG-SLOTS PostgreSQL 18 pg_replication_slots
- (b): xmin: 「The oldest transaction that this slot needs the database to retain. VACUUM cannot remove tuples deleted by any later transaction.」catalog_xmin: 「... VACUUM cannot remove catalog tuples deleted by any later transaction.」
- 他: 数値なし。(e) 区別なし。

### R1-PG-STAT PostgreSQL 18 pg_stat_activity
- 「backend_xmin xid — The current backend's xmin horizon.」(表の列説明。監視指標)。「backend_xid: Top-level transaction identifier of this backend, if any」。他は読んでいない (monitoring-stats は 29 万字、grep のみ)。

### R1-PG15-RES PostgreSQL 15 §20.4 old_snapshot_threshold
- (a)(c): 「Sets the minimum amount of time that a query snapshot can be used without risk of a “snapshot too old” error occurring when using the snapshot. Data that has been dead for longer than this threshold is allowed to be vacuumed away. This can help prevent bloat in the face of snapshots which remain in use for a long time.」「A value of -1 (the default) disables this feature, effectively setting the snapshot age limit to infinity.」「in many workloads extreme bloat or transaction ID wraparound may occur in much shorter time frames.」「When this feature is enabled, freed space at the end of a relation cannot be released to the operating system」。「Some tables cannot safely be vacuumed early, and so will not be affected by this setting, such as system catalogs.」
- (d): 既定 -1 (無効)、単位省略時は分、「Useful values for production work probably range from a small number of hours to a few days」、上限の例 60d。
- 削除: PG17 release notes 「Remove server variable old_snapshot_threshold (Thomas Munro)」「This variable allowed vacuum to remove rows that potentially could be still visible to running transactions, causing "snapshot too old" errors later if accessed. This feature might be re-added to PostgreSQL later if an improved implementation is found.」(R1-PG-REL17)。9.6 導入は md_1 既読のため本メモでは再確認していない。
- (e): 「snapshots which remain in use for a long time」(固定 snapshot 一般)。

### R1-PG-REL16 / R1-PG-REL17 release notes
- 上記の 3 引用 (vacuum_defer_cleanup_age 削除、old_snapshot_threshold 削除、transaction_timeout 追加) のみ利用。他の項は読んでいない。ページ題は "PostgreSQL: Documentation: 18" 系の release notes ページ。

### R1-MY-MVCC MySQL 8.4 §17.3 InnoDB Multi-Versioning
- (a) 症状 (容量): 「Otherwise, InnoDB cannot discard data from the update undo logs, and the rollback segment may grow too big, filling up the undo tablespace in which it resides.」
  - 性能 / 版の列: 「If you insert and delete rows in smallish batches at about the same rate in the table, the purge thread can start to lag behind and the table can grow bigger and bigger because of all the “dead” rows, making everything disk-bound and very slow.」
- (b) 機構: 「Update undo logs are used also in consistent reads, but they can be discarded only after there is no transaction present for which InnoDB has assigned a snapshot that in a consistent read could require the information in the update undo log to build an earlier version of a database row.」
- (c) 対処: 「It is recommend that you commit transactions regularly, including transactions that issue only consistent reads.」;「throttle new row operations, and allocate more resources to the purge thread by tuning the innodb_max_purge_lag system variable」。
- (d) 数値: この節に数値なし (読んだ範囲)。
- (e) 区別: 「including transactions that issue only consistent reads」と、read-only も対象と明記。
- 怪しい記述: 「It is recommend」は原文の誤記 (原文どおり)。

### R1-MY-PURGE MySQL 8.4 §17.8.9 Purge Configuration
- (a) 症状: 「The History list length is typically a low value, usually less than a few thousand, but a write-heavy workload or long running transactions can cause it to increase, even for transactions that are read only.」purge の遅れは「slowed purge operations, increased purge lag, and increased tablespace file size if the DML operations involve large object values」(単一表への DML 集中時)。
- (b) 機構: 「under a consistent read transaction isolation level such as REPEATABLE READ, a transaction must return the same result as when the read view for that transaction was created. Consequently, the InnoDB multi-version concurrency control (MVCC) system must keep a copy of the data in the undo log until all transactions that depend on that data have completed.」例: 「A mysqldump operation that uses the --single-transaction option while there is a significant amount of concurrent DML.」「Running a SELECT query after disabling autocommit, and forgetting to issue an explicit COMMIT or ROLLBACK.」
- (c) 対処と既定値:
  - innodb_max_purge_lag: 「When the purge lag exceeds the innodb_max_purge_lag threshold, a delay is imposed on INSERT, UPDATE, and DELETE operations to allow time for purge operations to catch up. The default value is 0, which means there is no maximum purge lag and no delay.」遅延式: 「(purge_lag/innodb_max_purge_lag - 0.9995) * 10000」。
  - innodb_max_purge_lag_delay: 「specifies the maximum delay in microseconds ... an upper limit on the delay period」(既定値は本節に書かれていない)。
  - innodb_purge_threads: 「The default value is 1 if the number of available logical processors is <= 16, otherwise the default is 4.」「The maximum number of purge threads is 32.」
  - innodb_purge_batch_size: 「The default value is 300.」
  - 注意: purge スレッドを増やしても、長い tx が握る snapshot 自体は解けない (本節はこれを直接は書かない。筆者の解釈であり原文の主張ではない)。
- (d) 数値: 上記。「A typical innodb_max_purge_lag setting for a problematic workload might be 1000000 (1 million), assuming that transactions are small, only 100 bytes in size, and it is permissible to have 100MB of unpurged table rows.」
- (e) 区別: 「even for transactions that are read only」と明記。mysqldump --single-transaction (固定 snapshot の backup) を例示。read-write のみではない。
- History list length の定義: 「The purge lag is presented as the History list length value in the TRANSACTIONS section of SHOW ENGINE INNODB STATUS output.」
- 怪しい記述: なし。

### R1-MY-UNDO MySQL 8.4 §17.6.3.4 Undo Tablespaces
- (a) 症状 (容量): 「Because undo logs can become large during long-running transactions, creating additional undo tablespaces can help prevent individual undo tablespaces from becoming too large.」
- (b)(c): 自動 truncation は「innodb_undo_log_truncate」を有効にした場合、「undo tablespaces that exceed the size limit defined by the innodb_max_undo_log_size variable are subject to truncation」「default value of 1073741824 bytes (1024 MiB)」。手順: 「Existing transactions that are currently using rollback segments are permitted to finish. The purge system empties rollback segments by freeing undo logs that are no longer in use.」(truncation は purge が空にしてから走るので、purge が進まない = 長い tx があると truncate できない、は本節の手順文からの推論。「long-running tx があると truncate できない」という直接の逐語は、読んだ範囲では見つからなかった)。
  - truncation 自体の性能影響の要因に「Existing long running transactions」が挙がる (Performance Impact of Truncating Undo Tablespace Files)。
- (d) 数値: 初期サイズ 「normally 16MiB」、拡張は最小 16MB・最大 256MB (「maximum of 256MB」)、innodb_max_undo_log_size 既定 1 GiB。
- (e): 区別の記述なし (「long-running transactions」のみ)。
- 怪しい記述: なし。

### R1-MY-STATUS / R1-MY-METRICS
- STATUS (§17.17.3 相当の Standard Monitor 出力): 「History list length 19」が TRANSACTIONS 節の出力例に出るだけで、この項の説明文は読んだ範囲では無い (定義は R1-MY-PURGE と R1-AWS-HLL)。
- METRICS: 表の行に「trx_rseg_history_len | transaction | enabled」があるのみ。説明文 (comment 列) は取得ページに無かった。定義は R1-AWS-HLL の「trx_rseg_history_len ... same value as RollbackSegmentHistoryListLength」。

### R1-AWS-HLL Aurora MySQL 「The InnoDB history list length increased significantly」 (DevOps Guru proactive insight)
- 版: 「supported for all versions of Aurora MySQL」。
- (a) 症状: 「This increase affects query and database shutdown performance.」「If the InnoDB history list length grows too large, indicating a large number of old row versions, queries and database shutdowns become slower.」major version upgrade 等の shutdown を伴う作業の前に list を減らせと推奨。
- (b) 原因: 「Typical causes of a long history list include the following: Long-running transactions, either read or write / A heavy write load」。
- (c) 対処: 「You can find long-running transactions by querying information_schema.innodb_trx.」「Make sure also to look for long-running transactions on read replicas.」「End each long-running transaction with the stored procedure mysql.rds_kill.」「Use transaction timeout to prevent future occurrences: ... consider enabling the aurora_transaction_timeout parameter. This parameter automatically terminates transactions that exceed a specified duration.」
- 監視指標: 「RollbackSegmentHistoryListLength – This Amazon CloudWatch metric measures the undo logs that record committed transactions with delete-marked records.」「PurgeBoundary ... If this CloudWatch metric doesn't advance for extended periods of time, it's a good indication that InnoDB purging is blocked by long-running transactions.」(Aurora MySQL 2.11+ / 3.08+)。
- (d) 数値: 閾値の数値は本ページに無し (insight の発火条件は読んだ範囲で未記載)。クエリの例の 10 秒は診断クエリ内の値。
- (e) 区別: 「either read or write」と明記。read replica 上の長い tx にも注意 (Aurora MySQL では reader の tx も writer の purge を止める、という趣旨と読めるが、原文は「look for long-running transactions on read replicas」まで)。
- 怪しい記述: なし。

### R1-AWS-PARAM Aurora MySQL configuration parameters
- aurora_transaction_timeout: 「Sets the maximum duration, in seconds, for an InnoDB transaction. Transactions that exceed this duration are rolled back. A value of 0 (the default) disables the timeout. Available in Aurora MySQL version 8.4.8 and higher.」(取得時点のページ。以前の版でのこのパラメータの提供状況は、この 1 ページからは不明)

### R1-AWS-PGBLK Aurora PostgreSQL 「Resolving identifiable vacuum blockers」 (postgres_get_av_diag)
- (b) 機構: blocker の型として Active statement / Idle in transaction / Prepared transaction / Logical replication slot / Reader instances / Temporary tables を列挙。「When the hot_standby_feedback setting is enabled, it prevents autovacuum on the writer instance from removing dead rows that might still be needed by queries running on the reader instance」。「catalog_xmin ... can lead to catalog bloat and wraparound vacuum」。
- (c) 対処: 「terminate the session using the pg_terminate_backend() function」;slot は「After confirming that the replication slot is no longer needed, drop it」。検出には age 条件: 「postgres_get_av_diag() only checks for aggressive vacuum blockers when the age exceeds Amazon RDS' adaptive autovacuum threshold of 500 million transaction IDs」「the blocker must be at least 500 million transactions old」。「autovacuum_freeze_max_age (which has a default of 200 million transaction IDs)」。
- (d) 数値: 500 百万 (blocker 検出下限)、200 百万 (既定)。
- 取得に失敗した「long-running/idle in transaction insight」ページ (proactive-insights.idle-txn) は下記の通り stub だった。idle_in_transaction_session_timeout を parameter group で設定する推奨は、WebSearch の要約にあるが原文で確認していないため事実として使わない。
- (e) 区別: idle in transaction / active statement / reader (hot_standby_feedback) を別々に列挙。

---

## 取得失敗の一覧
- dev.mysql.com 8.4 と 8.0 の直接取得は全て HTTP 403 (bot 判定の「Technical Difficulties」HTML、sha 08d6afae16362939 ほか。curl の UA を Firefox 相当にしても 403)。Wayback (web.archive.org) 経由で 200 を得た (ミラー 1 回で成功)。
- 次の AWS URL は HTTP 200 だが本文化物は 2609 byte の同一 stub (sha 6944869410221ff5、内容は「Amazon Aurora」のみ) で、実質失敗: AuroraMySQL.Managing.Metrics.html、proactive-insights.long-running-transactions.html、AuroraPostgreSQL.wait-event.LWLockmultixact-member-slru.html、AuroraMySQL.Managing.TransactionTimeout.html、proactive-insights.idle-in-transaction.html、proactive-insights.idle-txn.html。URL は推測で当てたもので、実在は未確認。
- 「Transaction timeout in Amazon Aurora MySQL」の専用ページ (R1-AWS-HLL が参照) は取得できなかった。パラメータ表 (R1-AWS-PARAM) だけで代用。
- PostgreSQL 「VACUUM VERBOSE の removable cutoff / dead but not yet removable」の説明文は取得したどの PG18 ページの本文化物にも無かった (下記)。

## 確かめたこと / 確かめていないこと
確かめた (保存原文から逐語で確認):
- PG18 の §24.1.5 が wraparound の防止策として long-running open tx・prepared tx・replication slot の 3 種を挙げていること、拒否閾値 300 万・警告 4000 万。
- idle_in_transaction_session_timeout / transaction_timeout / statement_timeout の既定が 0 (無効) であること。transaction_timeout は PG17 で追加 (release notes)。
- hot_standby_feedback (既定 off) が primary の bloat を招くと明記されていること、standby の長い問合せが cleanup 衝突で cancel されること。
- vacuum_defer_cleanup_age は PG16 で削除、old_snapshot_threshold は PG17 で削除 (release notes の逐語。後者の本文設定説明は PG15 版)。
- MySQL 8.4 の purge / undo / MVCC 節が、read-only tx を含む長い tx による undo の肥大と history list の伸びを明記していること。既定: innodb_max_purge_lag=0、innodb_purge_batch_size=300、innodb_purge_threads=1 または 4、innodb_max_undo_log_size=1 GiB。
- Aurora MySQL の history list length insight が read と write の両方の長い tx を原因に挙げ、aurora_transaction_timeout (既定 0) を推奨していること。

確かめていない:
- MySQL の各ページは Wayback の保存物であり、dev.mysql.com の現行ページとの一致は未確認 (snapshot 日: 2026-05-13 〜 2026-09-27 と幅がある)。8.4 の文書であることはページ題で確認。
- MySQL の innodb_max_purge_lag_delay の既定値、innodb_undo_log_truncate の既定値 (本文化物の該当箇所で読んでいない)。
- 「長い tx があると undo tablespace の truncation ができない」旨の直接記述 (読んだ範囲では無し。手順文からの推論に留まる)。
- SHOW ENGINE INNODB STATUS の History list length の説明文と INNODB_METRICS の trx_rseg_history_len の comment (取得ページに説明文無し)。
- PostgreSQL の VACUUM VERBOSE 出力 (removable cutoff 等) の説明。
- PG16 版 runtime-config-replication ページ本文に vacuum_defer_cleanup_age が無いこと (release notes のみ根拠)。
- 数値の効果量 (どのくらいの bloat になるか等) は公式文書に無く、集めていない。
- 取得した原文に、指示めいた文 (プロンプトインジェクション) は見つからなかった。ただし全文精読ではなく grep と該当節の読みのみ。
