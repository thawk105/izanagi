# R3 読書メモ: 研究側 (HTAP・長い tx と OLTP の同居で版の保持・GC が律速になる報告)

- 作成: 2026-09-29 (JST)、調査子 R3。契約: common-research.txt。原文: `/work/1/SFC/tanab/tmp/vhash-motivation-evidence-2026-09-29/src/R3/`
- 方針: 症状の大きさ (throughput・版の数・版の列の長さ・容量) を、本文・caption に書かれた数値だけで抜く。図から値を目測で読まない。
  図しか数値を持たないものは「数値は図中のみ (使えない)」と書く。機構の比較は md_1 (vhash-related-work README §6.3, §11.1) で済みなので再調査しない。
- 記号: (a) 症状 / (b) 原因の機構 / (c) 既存の対処 / (d) 数値 / (e) 固定 snapshot か普通の read-write か / (f) 長い側が read-only (固定 snapshot) か read-write か / (g) 実験条件。
- 取得元の版: md_1 が取得済みの 6 本は `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/` から src/R3 へ複製し、SHA-256 が md_1 の §11.1 の値と一致することを確認した (再取得はしていない)。本メモの逐語は複製した PDF の `pdftotext` (レイアウト無し) から採った。

## 早見表 (症状の大きさ、本文・caption の数値のみ)

| ID | 出典 | 症状の指標 | 数値 (原文にある物のみ) | 長い側 |
|---|---|---|---|---|
| R3-1 | Steam (PVLDB 2019) | 版の列の長さ・throughput | 標準 watermark GC で平均 287.43 (最大 30287)、EPO で 1.07 (最大 2)。OLTP 6554 txn/s 対 30,580 txn/s (Table 5) | read-only の OLAP query (CH-benCHmark) |
| R3-2 | LeanStore MVCC (PVLDB 2023) | TPC-C throughput の崩壊 | Fig.1 は正規化値で数値は本文に無い。「開いて sleep するだけ」の snapshot で崩壊 | 固定 snapshot (何もしない) |
| R3-3 | vDriver (SIGMOD 2020 技術報告版) | throughput 崩壊・版の列の長さ | vanilla の最大版列長が「104」(10^4 と読める) に達し、LLT が生きる間伸び続ける (§5.2.1) | read-only の点 query (LLT) |
| R3-4 | SAP HANA hybrid GC (SIGMOD 2016) | 版の数・容量・throughput | 実 ERP で 408,664 query 中 6 cursor が 1 時間超。1000 秒で TG 3.79 億版、SI 1.18 億版を回収 (§1, §5.2) | read-only の cursor / Trans-SI tx |
| R3-5 | Wu ほか (PVLDB 2017) | 性能低下 (定性) | 数値なし | 記述なし (「long-running transactions」) |
| R3-6 | HyPer MVCC (SIGMOD 2015) | scan 性能 (GC 無効時) | 数値は図中のみ | scan (read-only) |
| R3-7 | HTAP survey (arXiv 2404.15670) | 版の列が長い (定性) | 数値なし | 記述なし |
| R3-8 | Sirin ほか CIDR 2021 abstract | OLTP throughput (ハード干渉) | Table 1: 0.58 など。版・GC とは無関係 | OLAP scan/join (2 コピー構成) |
| R3-9 | CH-benCHmark (資料版) | benchmark の定義 | 数値なし | 分析 session |
| R3-10 | OLxPBench (arXiv 2203.16095) | latency 干渉 | 版・GC の記述なし | — |

---

### R3-1 Böttcher, Leis, Neumann, Kemper, "Scalable Garbage Collection for In-Memory MVCC Systems" (Steam), PVLDB 13(2), 2019

- 書誌 / URL: PVLDB 13(2), DOI 10.14778/3364324.3364328。取得元 = md_1 の §11.1 (vldb.org/pvldb/vol13/p128-bottcher.pdf、公式版)。src/R3/bottcher-pvldb2019.pdf (md_1 の src から複製)。
- SHA-256 先頭 16 桁: ceae3ff7928379a7 (md_1 §11.1 と一致)。取得時刻: 本 wave では再取得せず複製 (2026-09-29 22:42 JST)。HTTP status: 再取得なし。
- 読んだ節: 要旨、§1 (Figure 1・Figure 2)、§2.2「Practical Impacts of GC」、§5.1 (Figure 7)、§5.4 (Figure 9)、§5.7 (Table 5)、§6 関連研究。
- (a) 症状: 版の数が増え、版の列が長くなり、読みも書きも遅くなる。悪循環として図示される。
  - 要旨: "in HTAP workloads, this reclamation of old versions, i.e., garbage collection, often becomes the performance bottleneck." / "in the presence of long-running queries, state-of-the-art garbage collectors are too coarse-grained. As a consequence, the number of versions grows quickly slowing down the entire system."
  - §1: "During the lifetime of a transaction, newly-added versions cannot be garbage collected. The number of active versions accumulates and leads to long version chains."
  - §2.2 の Figure 2 説明: "We see that the read performance collapses within seconds, while the writes are slowed down by long periods of GC." / "At some point, the entire system would run out of memory."
  - §2.2: "The query throughput drops significantly after some seconds and queries start to last seconds (instead of milliseconds as before)." / "the read and write performance drops to almost 0."
- (b) 機構: 高水位 (high watermark) が最古の実行中 tx に縛られる。
  - §1 Figure 1 caption: "Old versions cannot be garbage collected as long as there are long-running transactions that have to retrieve them"
  - §2.2: "As long as the query is running, the number of version records stack up. ... Only when the reader is completed, the writer starts to clean up the version records."
  - §1: "even low-volume workloads can run into this problem as soon as GC is blocked by a very long-running transaction (e.g., by an interactive user transaction)."
- (c) 既存の対処 (Steam 自身の提案と、§6 が挙げる従来策):
  - Steam: "Steam prunes every version chain eagerly whenever it traverses one." (§1)
  - §6 の従来策: "Lee et al. [20] describe practical solutions to this problem such as: (1) flushing old versions to disk if main memory is exceeded, (2) aborting long-running transactions (user gets an error), and (3) closing transactions as soon as possible ... However, these solutions are not applicable to high volume workloads."
  - fork による snapshot: "One proposal for such workloads is to create virtual memory snapshots (forks) for read-only queries [26, 39]. However, this strongly affects the overall scalability of the system as it requires a shared mutex per column."
- (d) 数値:
  - Table 5 (caption: "Effect of using EPO – CH benchmark, 1 read thread, 1 write thread, 300k transactions in total"): 版の除去 (GC) で辿った版 "1,197m" 対 "4.2m"、平均版列長 "287.43 (30287)" 対 "1.07 (2)"。表 scan の辿った版 "120m" 対 "37m"、平均版列長 "1.00 (141)" 対 "1.00 (2)"。"Queries/s" "4.8" 対 "5.1"、"Transactions/s" "6554" 対 "30,580" (左が Standard Watermark、右が EPO Exact)。
  - §5.7: "The version chains grow quickly hitting a maximum length of 30287. When the optimization is enabled, the maximum length goes down to two versions." / "Steam processes the given set of transactions 5× faster using EPO."
  - §2.2: "Having only one warehouse, the isolated query execution times are reasonably fast (5-500 ms). However, compared to the duration of a write (0.02 ms), some of the queries are already long-running enough to run into the “vicious cycle”." (単一 warehouse・OLAP 1 thread・OLTP 1 thread で既に発生)
  - §5.1: 標準 GC に対し EPO で "the main improvements can be seen in the write throughput (roughly 3× compared to the second-best solution)"。"the average number of active version records only goes up by 42%, whereas the number of writes ... increases significantly by 354%."
  - §5.4 (Figure 9): OLAP thread 数を増やすと "the throughput of the single OLTP thread is highly affected by concurrent OLAP threads." (数値は図中のみ)
  - Figure 7 (10 分の時系列、read / write / version records / memory) は数値が図中のみで、本メモでは使わない。
- (e)/(f) 長い側: read-only の分析 query (CH-benCHmark の TPC-H 由来 query、OLAP thread)。§5.1 は "the main consumer of long version chains are not long-running queries but GC." (§5.1) とも書き、長い版の列を最も消費するのは読み手でなく GC の走査だと述べる。read-write の長い tx は実験に無い。
- (g) 実験条件: CH-benCHmark (TPC-C + TPC-H)、1 OLAP thread + 1 OLTP thread (Fig.2, Fig.7, Table 5)、Table 5 は 300k tx。1 warehouse。Fig.9 は OLAP thread 数を変える。実験機は §5 冒頭にあるが本メモでは未確認。
- 怪しい記述 / 確かめていないこと: Table 5 の列の割当て (左 = Standard Watermark) は pdftotext のレイアウト版で確認 (右 = EPO)。CH-benCHmark は data set が txn ごとに増えるため (§5.1)、時系列の悪化には data 増加も混ざる。指示めいた文は無し。

### R3-2 Alhomssi, Leis, "Scalable and Robust Snapshot Isolation for High-Performance Storage Engines" (LeanStore MVCC), PVLDB 16(6), 2023

- 書誌 / URL: PVLDB 16(6) 2023。取得元 = md_1 §11.1 (vldb.org/pvldb/vol16/p1426-alhomssi.pdf、公式版)。src/R3/alhomssi-leanstore-si-pvldb16-2023.pdf (md_1 src から複製)。
- SHA-256 先頭 16 桁: c334ca5dcfdbe713 (md_1 と一致)。取得: 複製 (2026-09-29 22:42 JST)。
- 読んだ節: §1 (Figure 1)、§2 冒頭 (Performance Collapse)、§5 Evaluation (Figure 9・10・11)、§7 関連研究 (deterministic 系の一文)。
- (a) 症状: TPC-C throughput の崩壊と、時間とともの劣化。
  - Figure 1 caption: "TPC-C performance collapses as long-running OLAP query occurs after 10 seconds (1 OLTP, 1 OLAP thread)"
  - §1: "Performance stays stable for 10s – until a long-running OLAP query enters. Although the query in this experiment does nothing and just sleeps – keeping the snapshot open – it causes OLTP performance to collapse."
  - §2: "Once a long-running transaction enters the system, the TPC-C throughput quickly drops and degrades over time. OLAP performance, as measured by the number of logically-visible tuples scanned per second, also deteriorates."
- (b) 機構: 最古の snapshot が回収境界 (高水位) を止める。TPC-C の queue 型 index で論理削除済みの tombstone (neworder) が積もる点が固有の原因として挙がる。
  - §1: "This happens due to the accumulation of logically-deleted tuples in the queue index; these tuples are visible to the long-running query and therefore cannot be garbage collected."
  - §2: "Systems that only garbage collect versions using a global minimum timestamp (high watermark) such as PostgreSQL, MySQL, and WiredTiger deteriorate faster than systems with interval-based GC such as SAP HANA [33], Steam [13], and vDriver [29]."
  - §2: "even with fine-grained and aggressive GC, challenging OLTP workloads such as TPC-C still suffer from performance collapse when a long-running transaction enters the system."
- (c) 既存の対処: 本論文の提案 (Graveyard Index で tombstone を退避、FatTuple で版の列を短く)。§5: "Only by using the Graveyard Index, we manage to retain a stable OLTP throughput." / "FatTuple limits the version chain length and thereby stabilizes OLAP performance but not OLTP." §7 関連研究: "a single long-running OLAP query may effectively halt OLTP processing for a long time." (これは deterministic 系 (バッチ実行) についての一文で、MVCC 一般の実測ではない)。
- (d) 数値:
  - Figure 1 は「normalized TPC-C performance」で、本文・caption に低下率の数値は無い。図から値は読まない。
  - 提案手法の側の数値のみ本文にある: "LeanStore achieves ≈2 million TPC-C transactions per second despite a concurrent long-running OLAP scan." (64 コア)。§5: "even at the start of the experiment its throughput is 2×/30× faster than WiredTiger/PostgreSQL."
  - Figure 10 (scan 開始遅延と scan throughput、10 TPC-C threads + 1 scan thread): 本文は「longer delay means that many versions accumulate」と定性のみ。
  - Figure 11 の caption: "TPC-C in-memory (OLTP only vs. HTAP)"。本文 "the TPC-C performance would drop quickly as tombstones accumulate in the neworder table" (数値なし)。
- (e)/(f) 長い側: 固定 snapshot を開いたまま何もしない (sleep) tx が最小再現。実験では「1 OLAP thread が long-running scan」(Figure 9, 11) または sleep (Figure 1)。read-write の長い tx は扱わない。
- (g) 条件: 1 OLTP thread (TPC-C) + 1 OLAP thread (Figure 1, 9)。PostgreSQL 12.9 と WiredTiger 10.0.0 と比較。Figure 1 の 3 系統は LeanStore (Basic)・PostgreSQL・WiredTiger と読める (本文 §2 は "three MVCC implementations" と書き、系統名は本メモでは Figure 1 の凡例まで確認していない)。実験機: AMD EPYC 7713 64 コア・512 GB (§5)。snapshot isolation。
- 怪しい記述 / 確かめていないこと: Figure 1 の系統名の確認は未了。TPC-C の queue 型 (neworder) に固有の現象で、更新が一様な workload の一般値ではない。

### R3-3 Kim ほか, "Long-lived Transactions Made Less Harmful" (vDriver), SIGMOD 2020 (技術報告版)

- 書誌 / URL: SIGMOD 2020。取得元 = md_1 §11.1 (github.com/hyu-scslab/vDriver の技術報告)。ACM 版とは同一の保証なし。ACM 版 (doi 10.1145/3318464.3389714) の再取得は今回試みず (Diva の ACM 取得が 403 だったため)。src/R3/vdriver-techreport.pdf (複製)。
- SHA-256 先頭 16 桁: 5d24648fc9f79636 (md_1 と一致)。
- 読んだ節: 要旨、§1、§2.1 Motivation (Figure 2・3)、§2.2、§5.1、§5.2.1 (Figure 13・14)。
- (a) 症状: throughput 崩壊、版の列の長さ、版空間 (容量)、CPU 時間。
  - §1: "Delaying version cleaning indeed causes version space to be bloated (rapidly in in-memory engines) ... In the worst case, the entire system would either halt due to a shortage of storage space or suffer severe performance degradation"
  - §2.1: "Common to both engines is the behavior that as a version chain gets long, transaction throughput is sharply collapsing."
  - §2.1 PostgreSQL: "PostgreSQL suffers throughput collapse as a long transaction remains alive." 主な CPU 時間は "version searching and index modifications" (in-row 版管理で index 更新が発生)。
  - §2.1 MySQL: "the long latch duration caused by a long-lived transaction surely prevents update transactions from accessing data pages, thus leading to throughput collapse."
- (b) 機構: 最古の生きている tx が回収境界。
  - §2.2: "in practice the oldest live transaction is often chosen as a reasonable proxy for establishing the death line ... but it is susceptible to LLTs due to the long suspension of version cleaning caused by the long-lived old transactions, leading versions to pile up rapidly."
  - 症状が版探索の順で分かれる: "searching a version from the oldest, like PostgreSQL, would severely affect short transactions, in contrast, searching a version from the newest while holding a page latch, like MySQL, would worsen latch contention."
- (c) 既存の対処: 現行の MySQL・PostgreSQL は粗い境界のまま。§2.2: "the concerned systems—MySQL and PostgreSQL—still use the age-old, coarse-grained criterion: using the oldest active transaction as a garbage-collection boundary." 提案 (vDriver) の効果は §5.2.1。
- (d) 数値:
  - §5.2.1 の図 13 の説明: "Even under highly-skewed workloads where a few hot records may lead to long version chains, vDriver can control the max chain length under 100 and retain the length until the end of LLTs. In contrast, the max chain length of the vanilla engines reaches 104 and keeps growing as long as LLTs remain alive." (原文の抽出テキストは "104" で、上付き指数の 10^4 が落ちたと思われる。10^4 と断定するには PDF の図 13 の縦軸を要確認。ここでは「抽出テキスト上 104」と書く)
  - Figure 3 (PostgreSQL・MySQL、90 秒の時系列で throughput と recent xid) と Figure 13 (throughput と DB size、600 秒) の縦軸値は図中のみで、本文・caption に数値なし。使わない。
- (e)/(f) 長い側: read-only。§5.2.1: "a group of long-lived transactions join around 50s in the first phase, and 350s in the second phase and perform a point query continuously against a table randomly chosen out of 48 tables, each of which contains 1000 records, the size of which is 256 bytes". §2.1 は「LLTs that read data items」。read-write の LLT は扱わない。
- (g) 条件: 96 コア (Xeon E7-8890 x4)・1 TiB・NVMe。sysbench 風 OLTP に uniform → skewed の 2 段階。PostgreSQL 12.0・MySQL 8.0 (InnoDB)、REPEATABLE READ。LLT 数は §5.2.1 の Fig.14 節に "four long-lived transactions" とある (本文の該当は Fig.14 の項目で確認、詳細な配置は未確認)。
- 怪しい記述 / 確かめていないこと: (1) 上記の 104。(2) 技術報告版で ACM 版と数値が一致する保証なし。(3) PostgreSQL 12・MySQL 8.0 の実測で、現行版 (PostgreSQL 17 等) での症状の大きさは示さない。

### R3-4 Lee ほか, "Hybrid Garbage Collection for Multi-Version Concurrency Control in SAP HANA", SIGMOD 2016

- 書誌 / URL: SIGMOD 2016, DOI 10.1145/2882903.2903734。取得元 = md_1 §11.1 (15721.courses.cs.cmu.edu の講義用ミラー、camera-ready 相当)。src/R3/hana-hybridgc-sigmod2016.pdf (複製)。
- SHA-256 先頭 16 桁: e81d952698e8ad1c (md_1 と一致)。
- 読んだ節: 要旨、§1 (Figure 2)、§5.1–§5.6 (Figure 10・11・12・13・16・17)。
- (a) 症状: 版空間の増加 (メモリ)、版の列の増加による走査コスト、throughput 低下、cursor の fetch の latency 増加。
  - 要旨: "long-lived queries or transactions in OLAP applications often block garbage collection ... Thus, these workloads typically cause the in-memory version space to grow. Additionally, the increasing version chains of records over time may also increase the traversal cost for them."
  - §1 (Figure 2 "A real example of version space overflow problem."): "The number of record versions, marked as “Active Versions” in blue color, keeps increasing over time. As a result, the system’s memory consumption, marked as “Used Memory” with green color, keeps growing."
  - §5.3: "The overall performance using GT alone dropped over time while the long-duration cursor is available for the table STOCK." (GT = 従来型の timestamp 方式。原因は行 store の chained hash (RID hash) の衝突増)
  - §5.4: "HG showed almost constant latency even though FETCH operations are repeated within a cursor while the latency increased over time in GT or GT+TG."
- (b) 機構: 最古の長寿命 snapshot (cursor / Trans-SI tx) が global minimum timestamp を止める。
  - §1: "we need to compare the version timestamp of each record version with the snapshot timestamp of the oldest, long-lived snapshot."
  - 実運用の原因: "Long-duration cursors or Trans-SI transactions due to either application logic or developers’ mistakes can easily block garbage collection."
- (c) 既存の対処 (従来策、§1): "1) The system flushes old versions out to disk. 2) The system closes problematic cursors or Trans-SI transactions by force and returns errors to clients. This is implemented in SAP HANA, especially to handle application developers’ mistakes. 3) The system implicitly closes cursors earlier than the explicit cursor close request". 監視: Figure 2 の "Active Commit ID Range" (最終 CID と最小 global snapshot timestamp の差) が伸びると長寿命 snapshot がある。提案 (HybridGC = GT+TG+SI) の対処は md_1 の §6.3 で済み。
- (d) 数値:
  - §1: "we collected statistics on cursor durations from a real ERP system. Out of 408,664 distinct queries executed in the system, the life times of six cursors were more than one hour!"
  - §5.2: "Due to the long-duration cursor, GT did not reclaim any record version but TG and SI respectively reclaimed 379 million versions and 118 million versions during the 1000 seconds of the TPC-C run time." (Figure 11、HG の実験で TG と SI が回収した累計)
  - §5.2 (Figure 10): "the number of record versions keeps growing for GT and GT+TG, the number of record versions in HG remained almost constant in spite of the long-duration cursor." (版数の絶対値は図中のみ)
  - §5.6: 長い cursor がある場合 "GT almost failed to reclaim" (Figure 19)。オーバーヘッドは "HG showed about 0.8% of performance overhead compared to GT" (長い snapshot が無い場合)。
  - §5.5: Trans-SI tx の実験は "(2) sleep 10 minutes"。Figure 16・17 の値は図中のみ。
- (e)/(f) 長い側: read-only。§5.1: "we added an emulated OLAP workload by using a long-duration cursor (under Stmt-SI) or long-duration transactions (under Trans-SI)." §5.2: "a simple scan query on the STOCK table without closing its cursor until the TPC-C benchmark finishes"。§5.4 は 500 万件を 1 万件ずつ 5 秒 sleep で fetch する incremental な cursor。read-write の長い tx は扱わない。
- (g) 条件: TPC-C 100 warehouses (SQLScript に埋め込み、warehouse ごとに専用 worker)。4 ソケット・1 TB メモリ・物理 60 コア。TPC-C は Stmt-SI (§5.5 のみ Trans-SI)。GC 起動周期は GT 1 秒・TG 3 秒・SI 10 秒。
- 怪しい記述 / 確かめていないこと: 408,664 query 中の 6 cursor は 1 システムの統計で、頻度の一般化は不可。SAP 自社の実装での結果で、外部再現は本文に無い。

### R3-5 Wu ほか, "An Empirical Evaluation of In-Memory Multi-Version Concurrency Control", PVLDB 10(7), 2017

- 取得元 = md_1 §11.1 (vldb.org/pvldb/vol10/p781-Wu.pdf)。src/R3/wu-empirical-mvcc-pvldb10-2017.pdf (複製)。SHA-256 先頭 16 桁: e0f3d3be03734d2a (md_1 と一致)。
- 読んだ節: §5 (GC) の該当段落、および Figure 10・12 周辺の見出し (Long Transactions のパネル)。
- (a)(b): §5.2 の記述 (節番号は本メモで未確認、GC の節内): "The DBMS’s performance drops in the presence of long-running transactions. This is because all the versions generated during the lifetime of such a transaction cannot be removed until it completes."
- (c) 対処: 該当段落に記載なし (GC 方式ごとの比較が主)。
- (d) 数値なし (本文の該当箇所)。
- (e)/(f) 区別の記述なし。実験の Long Transactions (#Ops=100) は tx 内の操作数 100 の短い/長いの比較で、長寿命 snapshot の実験ではない。
- 怪しい記述 / 確かめていないこと: 動機づけの症状の大きさとしては使えない (数値なしの一文)。

### R3-6 Neumann, Mühlbauer, Kemper, "Fast Serializable Multi-Version Concurrency Control for Main-Memory Database Systems" (HyPer), SIGMOD 2015

- 取得元 = md_1 §11.1 (db.in.tum.de の著者版)。src/R3/hyper-mvcc-sigmod2015.pdf (複製)。SHA-256 先頭 16 桁: af94b3c882ac6218 (md_1 と一致)。
- 読んだ節: §1、§5.1 の Figure 7・8・9 周辺、§6 (関連)、Figure 7 caption。
- (a) 症状: GC を無効にしたとき、古い版を巻き戻して読む scan が遅い。Figure 7 caption: "Scan performance with disabled garbage collection: the scan newest transaction only needs to verify the visibility of records while the scan oldest transaction needs to undo updates." Figure 9 caption: "Cycle breakdowns of scan-oldest transactions that need to undo 4 updates per dirty record"。
- (b) 機構: 長い read tx は更新の待ちを生む (ロック方式の説明、§1: "no update transaction is allowed to change a data object that has been read by a potentially long-running read transaction and thus has to wait until the read transaction finishes.")。
- (c) 対処: "the long-running transaction can be aborted and restarted on a snapshot [29]" (§5 の該当段)。§6: "we previously proposed using virtual memory snapshots for long-running transactions [29], where updates are merged back into the database at commit-time. Snapshotting and merging, however, can be very expensive depending on the size of the database." 前提: "the time that a transaction is active tends to be short (long-running transactions would be deferred to a “safe snapshot”)." (§5)
- (d) 数値: 本文・caption に scan 低下率の数値なし (図 7・8 の軸のみ)。
- (e)/(f) 長い側は scan (read-only)。
- 怪しい記述 / 確かめていないこと: HyPer 自身は「実運用で有意な低下に達するのは 10 万件級の hot item と長い open tx が要る」との見解 (§5 の Amazon の例)。動機づけの症状の大きさというより、「症状は限定条件で出る」との反論側の材料。逐語: "in order to measure a significant drop in scan performance there need to be hundreds of thousands of such bestselling items and a transaction that is open for a long period of time."

### R3-7 Zhang ほか, "HTAP Databases: A Survey", arXiv 2404.15670 v1 (2024-04-24)

- URL: https://arxiv.org/pdf/2404.15670。HTTP 200、2026-09-29 22:40 JST 取得、SHA-256 先頭 16 桁: 46246c3540aa2a1b。保存: src/R3/htap-survey.pdf。版: v1。
- 読んだ節: §4.1.1 (MVCC-based HTAP)、Table の Pros/Cons、§3.4 の HyPer 記述、MV-PBT の段。grep で「garbage」「long-running」「long-lived」「old version」「version chain」を検索した範囲。
- (a) 症状 (定性): §4.1.1 "HTAP workloads will lead to frequent version traversing and cleaning of stale data versions." / Pros and Cons: "However, when it comes to the long version chains, it will incur a significant overhead for version traversing and cleaning." 表の Cons 欄に "Long Version Chains"。MV-PBT の段: "there could be long version chains for an MVCC-based HTAP database".
- (b) 機構: 「長い分析 query が OLTP の GC を妨げる」という因果の記述は、上の grep の範囲では見当たらない。本文の "long-running queries" (§3 の row + column 型の説明) は列 store scan の話で、GC の話ではない。
- (c) 対処: Diva の要約 "Diva [54] separates the version searching and version cleaning by maintaining a provisional index and performing an interval-based version clearning separately" (原文の綴りのまま)。
- (d) 数値なし。(e) 区別の記述なし。
- 怪しい記述 / 確かめていないこと: 全文を通読していない (grep 範囲のみ)。survey の記述は他論文の要約で、一次の実測ではない。

### R3-8 Sirin, Dwarkadas, Ailamaki, "Workload Interference Analysis for HTAP" (CIDR 2021 abstract) と ICDE 2021 論文

- ICDE 2021 論文 ("Performance Characterization of HTAP Workloads") の本文 PDF は取得できなかった (取得失敗の一覧を参照)。読んだのは CIDR 2021 abstract のみ。
- 書誌 / URL: https://www.cidrdb.org/cidr2021/papers/cidr2021_abstract01.pdf、HTTP 200、2026-09-29 22:41 JST、SHA-256 先頭 16 桁: 5ca3693978a8976f、src/R3/cidr2021_abstract01.pdf。
- 読んだ節: 全文 (1 ページ)。
- (a) 症状: OLTP throughput の低下 (ハードウェア資源の共有)。Table 1 caption: "Normalized OLTP & OLAP throughput. 1T+12A: 1 OLTP and 12 OLAP threads."。集計 query では OLTP が 1T+12A で 0.58、7T+6A で 0.73、12T+1A で 0.80 (join では 0.78, 0.82, 0.89)。OLAP はほぼ 0.95 以上。
- (b) 機構: 版・GC ではない。"the sequential-scan-heavy aggregation query highly stresses the memory sub-system. As a result, the OLTP threads are blocked by the OLAP threads at the LLC and memory bandwidth." ソフトウェア側の干渉は「fresh tuple の伝播時間」: "Fresh tuple propagation time increases exponentially for 14 or more OLTP threads since the OLTP tuple generation throughput exceeds the fresh tuple propagation throughput of 1 propagation thread". 2 コピー構成 (OLTP 行 store + OLAP 列 store + delta) の話で、MVCC の版の保持は主題でない。
- (c) 対処: "HTAP systems should ensure that fresh tuple propagation throughput is greater than the throughput of the OLTP transactions that generate the fresh tuples."
- (d) 数値: 上記。他に "the database size is 30GB"、"fresh tuple propagation time is 2% and 23% of OLAP execution time with 1 and 7 OLTP threads"。
- (e)/(f) OLAP は分析 query (read-only)。長さは秒数の記載なし。
- 怪しい記述 / 確かめていないこと: 検索結果の要約にある「OLTP throughput drops by up to 42%」は WebSearch の要約文で、原文 (abstract) では確認していない (Table 1 の 0.58 が 42% 低下に相当するが、本メモでは計算値を数値として採らない)。ICDE 版は未読。本 wave の主題 (版・GC) には直接の根拠にならない。

### R3-9 CH-benCHmark (Cole ほか, DBTest 2011) — 論文本文は未取得、TUM の資料版のみ

- Cole ほか "The mixed workload CH-benCHmark" (DBTest 2011, DOI 10.1145/1988842.1988850) の本文は取得できず。semantic scholar の pdfs URL (https://pdfs.semanticscholar.org/835d/ad44179bf856c63b98cc1440b60cd6a3283a.pdf) は HTTP 200 で PDF を返したが、中身は "Mixed Workload CH-benCHmark" と題した TUM の Seibold・Funke・Kemper の発表資料 (スライド) で、論文本文ではない。SHA-256 先頭 16 桁: 794221f44337cacf、src/R3/chbench.pdf、2026-09-29 22:41 JST。
- 読んだ範囲: 資料の全文 (抽出テキスト)。
- 内容 (定義): "Process analytical queries directly on operational database"。"Fixed scale factor model (like TPC-H) ... Fixed number of warehouses, no wait times"。パラメータは「transactional/analytical sessions の数」(例 4/16、1/8、1/1、0/1、8/0)、isolation level (read committed・snapshot isolation・serializable)、warehouse 数 (12・120・500)。
- (a)–(e) 症状・機構・対処・数値: この資料には無い (benchmark の定義のみ)。「分析 query の長さ」の数値定義も、この資料の範囲では見当たらない。
- 本文 (Cole ほか) 由来の記述は使えない。前記の "The mixed workload CH-benCHmark" の要旨は WebSearch の要約文のみで、事実として使わない。
- Steam の §2.2 が CH-benCHmark の 1 warehouse で OLAP query が 5-500 ms と書く (R3-1) ので、CH-benCHmark の分析 query は「既定では長くない」ことが分かる。これは Steam 側の記述 (二次) で、Cole ほかの定義そのものではない。

### R3-10 OLxPBench (Kang ほか), arXiv 2203.16095 v2 (2022-04-05)

- URL: https://arxiv.org/pdf/2203.16095、HTTP 200、2026-09-29 22:40 JST、SHA-256 先頭 16 桁: 164194bd8049b333、src/R3/olxpbench.pdf。
- 読んだ範囲: 要旨、§1、§V の実験 (query 干渉の段落) を grep 検索した範囲。「garbage」「version」「long-running」「snapshot」で検索し、版の保持・GC に関する記述は見当たらなかった (該当語は TiDB の版番号・snapshot isolation の一文・参考文献のみ)。
- (a) 症状: OLTP の latency が分析 query の同居で悪化 (TiDB)。本文: "the standard deviation of average baseline latency increases from 2.21 to 9.16" (分析 query の干渉時)、"from 2.21 to 38.91" (real-time query の干渉時)。これは latency の標準偏差で、版の保持とは無関係。
- (b)–(e) 版・GC の記述なし。分析 query の長さ・鮮度の扱いは「real-time query を tx の途中に挟む」抽象 (hybrid transaction) で、長い snapshot を保持する設定ではない。
- 怪しい記述 / 確かめていないこと: 全文通読はしていない。

---

## 取得失敗の一覧

| 対象 | 試した取得元 | 結果 |
|---|---|---|
| Sirin ほか, ICDE 2021 (Performance Characterization of HTAP Workloads) | infoscience.epfl.ch の entities ページ (HTTP 405)、par.nsf.gov の servlets/purl (接続リセット、2 回) | 本文 PDF 未取得。WebSearch では infoscience と NSF PAR の 2 か所が所在として出たが、事実は使わない |
| Diva (Kim ほか, SIGMOD 2022) | dl.acm.org/doi/pdf/10.1145/3514221.3526135 → HTTP 403 (中身は HTML)。WebSearch で modb.pro (墨天轮の文書共有) が見つかったが、ミラーとして再取得はしていない (無認可の共有の可能性) | 未取得 |
| HTAPBench (Coelho ほか, ICPE 2017) | dl.acm.org/doi/pdf/10.1145/3030207.3030228 → HTTP 403。repositorio.inesctec.pt の推測 URL → HTTP 404 | 未取得 |
| Psaroudakis ほか, TPCTC 2014 | infoscience.epfl.ch/record/201827 → HTTP 405。researchgate.net → HTTP 403 | 未取得 |
| Cole ほか, DBTest 2011 | ACM は試さず。semantic scholar の URL は発表資料 (R3-9) を返した | 論文本文は未取得 |
| vDriver の ACM 版 | 試していない (md_1 の技術報告版を使用) | — |

## 確かめたこと / 確かめていないこと

確かめたこと:
- md_1 が取得した 6 本 (Steam・LeanStore・vDriver・HANA・Wu・HyPer) の src を複製し、SHA-256 が md_1 §11.1 と一致した。
- Steam の Table 5、HANA の実 ERP 統計と Figure 11 の回収数、vDriver の最大版列長の記述、LeanStore の Figure 1 caption と §2 の記述を、`pdftotext` の抽出テキストで逐語確認した。
- 「長い側が read-only (固定 snapshot)」であることを、Steam (OLAP query)、LeanStore (sleep する snapshot・scan)、vDriver (点 query)、HANA (cursor・Trans-SI tx) の実験条件の文で確認した。今回読んだ範囲で、長い側が read-write の tx の実験は 1 本も無かった。

確かめていないこと:
- 図 (Steam Fig.7・9、LeanStore Fig.1・10・11、vDriver Fig.3・13、HANA Fig.10・12・14・16・17) の値。目測しない方針のため、本文・caption に数値がある物だけを採った。LeanStore の Figure 1 は正規化値のため、低下率の数値は無い。
- vDriver の "104" が 10^4 か。
- ICDE 2021 (Sirin) の本文、Diva、HTAPBench、Psaroudakis の本文は未読 (取得失敗)。これらの記述は一切事実として使っていない。
- 現行の PostgreSQL / MySQL / SAP HANA 版での症状の大きさ (R3 の範囲外)。
- Wu の GC 段落の節番号。

怪しい記述 (プロンプトインジェクション): 読んだ PDF・HTML の中に、指示めいた文は見つからなかった。
