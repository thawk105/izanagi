# A-ccbench-cidr: CCBench §7 照合 + CIDR 2021 "Everything is a Transaction" 照合

指示めいた文字列: 取得した2本のPDF本文中に、作業の振る舞いを変えるよう指示する文字列は見当たらなかった。

---

## 担当1: CCBench 論文 §7 の照合

### 書誌
Takayuki Tanabe, Takashi Hoshino, Hideyuki Kawashima, Osamu Tatebe.
"An Analysis of Concurrency Control Protocols for In-Memory Databases with CCBench."
PVLDB, 13(13): 3531–3544, 2020 (VLDB 2020)。
DOI: https://doi.org/10.14778/3424573.3424575

### 取得元
- URL: https://www.vldb.org/pvldb/vol13/p3531-tanabe.pdf
- 保存先: `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/ccbench-pvldb13-13-tanabe.pdf`
- SHA-256: `fee3789bbe81ae308650bc3f3b3fdb2e797ad1bc61ef530d4e76b8a9e5844c93`
- 14 ページ、camera-ready (PVLDB vol.13 収録版)。印刷頁は 3531–3544 (= PDF 1〜14 ページ目に対応、3531+n-1 = 印刷頁)。

### 読んだ範囲
Abstract、§1 (Introduction, 1.1〜1.3)、§2.1 (Concurrency Control Protocols の説明中の Cicada 節)、§3.2 (CCBench: A Platform for Fair Analysis の最適化手法定義部)、§3.3 (Optimization Method Implementations の Cicada 実装差分部)、§4.3 (Cicada reproduction)、**§7 全体 (7.1, 7.2, 7.3) を精読**、§8 冒頭 (Related Work 先頭数行)、§9 (Conclusion)。§5 (Cache)・§6 (Delay) は §7 の記述が参照する箇所のみ確認 (§5.1 への参照)。§2.2 以降の細部、§8 の全文、実験セットアップの詳細 (Table 1/2 本文以外) は読んでいない。

### (a) §7 は version lifetime と性能の関係を分析しているか
**一致。** §7 の見出しは "ANALYSIS OF VERSION LIFETIME" そのもの (p.3540)。
> "7. ANALYSIS OF VERSION LIFETIME" (見出し, §7, p.3540)

§1.3 Organization にも明示: "§7 investigates the eﬀect of version lifetime management." (§1.3, p.3531)

### (b) 図12〜13 に関する版探索コストの分析 (Cicada の追加コストが read/write に現れ、version chain traversal との関係が分析されている)
**一致。** §7.1 (p.3540〜3541) で次のように書かれている。
> "In Figs. 12a and 12b, we can see that the major overhead of Cicada lies in the read and write operations rather than validation or GC." (§7.1, p.3540)

続けて、Cicada の inline 版を上書きする SVCC 版 (Cicada-SV) を作って図13 で対照実験し、
> "The latencies of Cicada-SV and Silo were almost the same. We attribute the overhead shown by Cicada in Figs. 12a and 12b to the cost of version chain traversals." (§7.1, p.3540)

と結論している。図12 (Cicada vs Silo の latency breakdown、skew 0、YCSB-A/B) と図13 (Cicada-SV vs Silo の同条件比較) の対比によって、Cicada の read/write オーバーヘッドが version chain traversal に起因すると特定する、という構成であり、メモの記述と完全に一致する。

### (c) 図14 が RapidGC の限界を示す (長い tx が古い履歴を必要とすると GC 間隔を短くしても性能改善が頭打ちになる)
**一致。** §7.2 "Limit of Current Approach" (p.3541) にて、read phase 末尾に人工遅延を挿入した長い tx を 1 スレッドだけに実行させ、RapidGC の interval と遅延幅を振って測定している。
> "Even state-of-the-art GC does not suﬃciently reduce the number of visible versions if there is only a single long transaction." (§7.2, p.3541)
> "As shown in Fig. 14, performance saturated when a delay was inserted. Saturation occurred when the GC interval was the same as the added delay. ... This is because current GC methods do not collect visible versions that may be read by active long transactions. The current GC scheme does not collect the versions until the transaction ﬁnishes." (§7.2, p.3541〜3542)

数値としては本文に「GC interval が 100 us 以下なら高い throughput」「1 ms の遅延を入れた場合、GC interval が 1 ms で性能が飽和した」「1 s の遅延は OOM killer に殺されるため計測不能だった」という記述がある (図から読み取った数値ではなく本文記載)。

### (d) §7.3 が AggressiveGC 構想 (必要とされ得る版も回収し、必要になった tx を新しい timestamp で再実行する方向) を提起しているか
**一致。節番号もメモ通り §7.3。** 見出しは "7.3 Aggressive Garbage Collection" (p.3542)。
> "From the limitation of the current GC scheme described above, we suggest a novel GC scheme, AggressiveGC, that aggressively collects versions beyond the current ones to deal with long transactions. For example, the multi-version timestamp ordering (MVTO) protocol could be integrated with a GC method that aggressively collects visible versions. It could make some versions non-visible even though active or future transactions need to read them. Such a protocol might incur read operation failures unlike conventional MVTO, which could be handled by aborting the transaction and retrying it with a new timestamp." (§7.3, p.3542)

「必要とされ得る版も回収し、必要になった tx は新しい timestamp で abort/retry する」という記述は、メモの整理 (研究メモ §2 の figure) と正確に対応する。
補足: kVSR・2V2PL という既存の「版数制限」手法と比較し、「visible な版は連続でなくてよい・版数は文脈依存で柔軟でよい」という点で優位性を主張している (§7.3, p.3542)。また starvation リスクと wait-die 的な優先度管理の必要性にも触れている。

### (e) 図14 では長い tx を作るため read phase 末尾に人工遅延を入れている (§16.1)
**一致。** §7.2 (p.3541) に明記。
> "To generate a long transaction, we added an artiﬁcial delay at the end of the read phase. Both long and short transactions used the same number of operations with the same read-write ratio. One worker thread executed the long transaction, and the remaining worker threads executed the short transactions." (§7.2, p.3541)

図14 のキャプションにも "Inserted delays for long transactions: 0 to 10 ms." とある (図14キャプション、p.3541)。

### §7 の小節構成 (メモとのずれなし)
- 7. ANALYSIS OF VERSION LIFETIME (p.3540)
  - 7.1 Determining Version Overhead (p.3540〜3541、図11・図12・図13、Insight 5)
  - 7.2 Limit of Current Approach (p.3541〜3542、図14)
  - 7.3 Aggressive Garbage Collection (p.3542、Insight 6)
- 直後は §8 RELATED WORK (p.3542)。
節番号・図番号ともメモの記述とずれはなかった。

### §7 で使われている用語の定義 (逐語)
- **version lifetime (版の生死区間の考え方)**: "The life of a version begins when a corresponding write operation creates it. The version state is called visible during the period when other transactions can read it. Otherwise, the version state is called non-visible." (§7.1, p.3540)
- **RapidGC**: 2箇所に定義あり。
  - §2.1 (Cicada の最適化手法列挙内): "RapidGC is a quick and parallel GC optimization method." (p.3532)
  - §3.2 (CCBench の最適化手法一覧、Table 1 の説明): "(7) RapidGC: frequent updating of timestamp watermark for GC in MVCC protocols." (p.3534)
- **AggressiveGC**: "we suggest a novel GC scheme, AggressiveGC, that aggressively collects versions beyond the current ones to deal with long transactions." (§7.3, p.3542)。Contribution 節 (§1.2, p.3532) でも先出しされている: "To overcome this problem, we deﬁned a new optimization method, AggressiveGC. It requires an unprecedented protocol that weaves GC into MVCC, thus going beyond the current assumption that versions can not be collected if they might be read by transactions (§7.3)."
- **BestEffortInlining** (Cicada の最適化。VHash の hot/cold 配置と関連しうる既存手法): "BestEﬀortInlining embeds an inline version in the record header at the top of the version list to reduce indirect reference cost." (§2.1, p.3532)
- **AssertiveVersionReuse** (CCBench 独自の最適化。GC で回収した版のメモリを再利用しメモリマネージャ負荷を下げる): "This method enables each worker thread to maintain a container for future version reuse. When GC begins, the versions collected are stored in this container. A new version is taken from this container except if it is empty." (§3.2, p.3534〜3535)

### CCBench 論文の他の節で、版探索・GC・長い tx・Cicada の inlining に関わる記述
- **Abstract**: "(I6) Even a state-of-the-art garbage collection method cannot improve the performance of multi-version protocols if there is a single long transaction mixed into the workload. ... we deﬁned the aggressive garbage collection optimization in which even visible versions are collected." (Abstract, p.3531)
- **§1.2 (Contribution)**: I5/I6 の先出し要約があり、AggressiveGC を "§7.3" と明示して参照している (p.3532、上記引用)。
- **§2.1** (Cicada の説明): BestEffortInlining・RapidGC・EarlyAbort・PrecheckValidation・AdaptiveBackoff・SortWriteSetByContention という Cicada の6つの最適化手法の定義がある (p.3532)。
- **§3.2** (CCBench の最適化手法一覧, Table 1 相当の説明文): RapidGC の定義に加え、AssertiveVersionReuse の紹介と、AggressiveGC を "§7.3 で述べる" と先出し参照 (p.3534〜3535)。
- **§3.3** (Cicada 実装の詳細): "We implemented all six optimization methods: SortWriteSetByContention, PrecheckVersionConsistency, AdaptiveBackoﬀ, EarlyAborts, RapidGC, and BestEﬀortInlining. Moreover, we ﬁxed a logical bug, i.e., the incomplete version consistency check in the validation phase." (p.3534、原論文 [Cicada 原論文] の validation の不備を指摘し修正した旨の記述)。
- **§4.3** (Cicada 再現実験): "We discuss this inconsistency in Insight 5 (§7.1)." と、read-intensive workload での Cicada の性能低下の議論を §7.1 に接続している (p.3533〜3534 付近)。
- **§6.1** (Analysis of Delay, NoWait/Wait の議論): 長い tx における abort コストへの言及があるが、これは version lifetime ではなく lock 待ち/abort-retry コストの文脈: "The cost of aborts should be smaller for short transactions and larger for long ones." (§6.1, p.3538 付近)。§7 の「長い tx が古い履歴を必要とする」問題とは別の論点であり、混同しないよう分けて報告する。

### CCBench 実装 (external/ccbench) での RapidGC / AggressiveGC の実在確認 (任意, grep のみ)
worktree 内 `external/ccbench` を対象に grep した (書き込みはしていない)。
- 文字列 `"RapidGC"` `"AggressiveGC"` はソースコード中 (`.h`/`.cc`/`.cpp`) に**存在しない** (スクリプト名に `xgci` = 恐らく "x GC interval" というパラメータ振りスクリプトはあるが、識別子としての `RapidGC` 文字列はコードになし)。
- `cc/cicada/transaction.cc` に `gc_versions()` / `gcpv()` / `gc_records()` という GC 関数があり、`gcq_.front().wts_ >= MinRts.load(...)` のように `MinRts` という timestamp watermark と比較して版を回収する実装がある。これは論文の RapidGC 定義 ("frequent updating of timestamp watermark for GC") に対応する実装と考えられるが、コード中に `RapidGC` という名前そのものは付いていない (`FLAGS_gc_inter_us` という GC 間隔フラグが対応すると見られる)。
- `AggressiveGC` に対応する実装は grep で見つからなかった。§7.3 の記述通り、AggressiveGC は論文内で「提起した (suggest)」構想であり、実装されたと書かれてはいない。実装が存在しないことと整合している。
(この項目は任意確認であり、grep 結果の報告に留める。実装の完全性は監査していない。)

---

## 担当2: CIDR 2021 "Everything is a Transaction"

### 書誌
Ling Zhang, Matthew Butrovich, Tianyu Li, Yash Nannapanei, Andrew Pavlo, John Rollinson,
Huanchen Zhang, Ambarish Balakumar, Daniel Biales, Ziqi Dong, Emmanuel Eppinger, Jordi Gonzalez,
Wan Shen Lim, Jianqiao Liu, Lin Ma, Prashanth Menon, Soumil Mukherjee, Tanuj Nayak, Amadou Ngom,
Jeff Niu, Deepayan Patra, Poojita Raj, Stephanie Wang, Wuwen Wang, Yao Yu, William Zhang.
"Everything is a Transaction: Unifying Logical Concurrency Control and Physical Data Structure
Maintenance in Database Management Systems." CIDR 2021 (11th Conference on Innovative Data
Systems Research)。Carnegie Mellon University (NoisePage プロジェクト)。
公式 URL (cidrdb.org 系): https://www.vldb.org/cidrdb/2021/ (proceedings index)。
本文取得元 URL は CMU DB グループのミラー (下記)。

### 取得元
- URL: https://db.cs.cmu.edu/papers/2021/cidr2021_paper06.pdf
- 保存先: `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/cidr2021-everything-is-a-transaction.pdf`
- SHA-256: `5ec8f8fa57707f49286386857113c326ec8a7b2644b3c166e1089e47075da6db`
- 9 ページ。CIDR 2021 の camera-ready (著者版ミラー。cidrdb.org 本体の proceedings ページは index のみで、個別 PDF は著者/CMU ミラー経由で取得した)。

### 読んだ範囲
Abstract、§1 Introduction、§2 Background (2.1 The NoisePage System, 2.2 Data Structure Maintenance
in MVCC)、§3 Framework Overview (3.1 System Characteristics, 3.2 Implementation, 3.3 Ordering
Actions) を精読。§4 (Optimizations) は見出しと冒頭のみ確認 (4.1 Multi-Threaded Action Processing,
4.2 Timestamp Caching & Batching Actions の内容は精読していない)。§5 (Other uses of DAF) は見出し
(5.2 Non-Blocking Schema Change) のみ確認、本文未読。§6 (評価実験) は未読。**§7 Related Work は全文
読んだ。** §8 (Future Work) は未読。§9 Conclusion は簡単に確認。参考文献リストの該当箇所は確認した。

### §23.4 の主張の照合: 「transactional semantics と物理データ構造の maintenance の分断を問題にしている」
**一致 (逐語で確認)。** Abstract と §1 Introduction の両方に、ほぼ同内容の文が独立に現れる。
- Abstract: "As a result, there is a disconnect between the logical semantics of transactions and the DBMS's underlying implementation." (Abstract, p.1)
- §1: "This difficulty partly arises from a disconnect between the concurrency control semantics of the logical layer of the system (e.g., transactions, tuples) and the synchronization techniques of the underlying physical data structures (e.g., arrays, hash tables, trees)." (§1, p.1)

メモの要約はこの2文の言い換えとして正確であり、「分断」を問題として設定している点は一致と判定する。

### 機構の比較6列

1. **何を入力に判断するか**: DAF が deferred action を実行してよいかどうかの判断入力は、**その action に付いたタグ timestamp と、現在系の「最古の実行中 transaction の開始 timestamp (=oldest running transaction)」との比較のみ**である。物理配置 (hot/cold) やアクセスパターンは入力にしていない。
   > "DAF guarantees to invoke the given action only after there are no transactions in the system with a start timestamp smaller than the tagged timestamp." (§3, p.2)

2. **どの状態を変えるか**: 変えるのは物理データ構造側 (version chain の unlink・版の delete・index key の削除・テーブル削除などの「deferred action」の実行) であり、**個々の transaction の timestamp そのものは一切変更しない**。global timestamp counter は transaction の begin/commit で自然に進むだけで、DAF が能動的に進める対象ではない。
   > Figure 1 の説明: "a transaction worker first increments the global timestamp counter... When the transaction begins... it increments the global timestamp counter again. The action thread then processes the queue in order." (§3.2, p.2)

3. **どの不変条件を保つか**: 「まだ visible な版・オブジェクトを、実行中または将来の transaction から見えなくしない」というメモリ安全性/意味論的正しさ (safety requirement)。NoisePage は snapshot isolation の MVCC (newest-to-oldest version chain, tstart/tend) をベースにしており、DAF はその上で GC・index cleanup 等の non-transactional maintenance のタイミングだけを保証する。CC プロトコル自体 (serializability/SI の保証方式) を変更する提案ではない。
   > "the system can remove the older version only after that version is no longer visible to any current or future transactions in the system." (§3, p.2)

4. **どのコストを減らすか**: 版探索コストや read/write のレイテンシではなく、**「transactional access と non-transactional maintenance task を安全に協調させる実装の複雑さ」**を減らすことが主目的。性能面では「手で最適化した既存実装と同等程度 (competitive)」を目標としており、性能改善そのものは主張の中心ではない。
   > "We found that DAF reduces these tasks' implementation complexity while offering competitive performance compared to hand-optimized alternatives." (§1, p.1)

5. **旧版を新たに読めるか**: DAF 自体は read path (version 選択・探索) に一切関与しない。まだ読んでいない旧版を取得できるかどうかは、NoisePage の既存 MVCC 実装 (newest-to-oldest version chain) に依存しており、DAF が変更・提供する能力ではない。この論文は「版の探索コストや版選択方式」を主題にしていない。
6. **長い transaction への効き方**: **DAF 自身が §7 Related Work で自らの限界として明記している。** 「最古の実行中 tx が終わらない限り action 処理が全部止まる」という、まさに CCBench の Insight 6 (RapidGC の限界) と同型の弱点を持つ。
   > "Long-Running Transactions: The most onerous shortcoming of our current implementation of DAF is that it assumes user transactions are short-lived. Action processing will halt if the oldest running transaction in the system does not finish. It will result in a similar impact of long-running transactions in [21] [Neumann et al., HyPer MVCC, SIGMOD 2015], or the effect of a thread does not refresh its epoch in [9] [FASTER]." (§7, p.8)

   この節では、緩和策として HANA ([16]) や Böttcher et al. のスケーラブル GC ([8]) の技法を将来使える可能性に触れるのみで、DAF 自身に長い tx への対策は実装されていない、と明記している。

### 本案の4点との照合

- **(1) 物理配置 (cold 領域に入ること) を timestamp 制御の入力にする**: **言っていない (読んだ範囲では見当たらない)**。DAF の入力は global timestamp counter / oldest-running-txn の watermark のみであり、hot/cold のような物理配置やアクセス局所性を判断入力にする記述は §1〜§3, §7 のどこにもない。
- **(2) 版選択と timestamp 選択を同時に扱う**: **言っていない**。DAF は個々の transaction の read 経路 (どの版を読むか、どの timestamp を採用するか) には一切触れない。DAF が扱うのは非transactional な maintenance action の実行タイミングのみであり、transaction 自身の version 選択ロジックとは独立している (§3.1: "DAF requires the DBMS concurrency control algorithm to satisfy specific properties" と述べるのみで、CC 側の版選択方式には介入しない)。
- **(3) 前進を履歴の保持義務の縮小へ接続する**: **一部だけ言っている、ただし方向が異なる**。DAF も「transaction の timestamp 状態」と「GC/maintenance が安全に実行できる境界」を接続する点では同型の発想を持つ (oldest-running-txn の watermark で GC の実行可否を決める)。しかしこれは §7 で述べる Hekaton の "high watermark" や SAP HANA と同じ**既存の受動的な GC 手法**であり (§7, p.7 で両者を先行研究として引用)、VHash 案のように「transaction 側を能動的に前進 (forwarding) させて古い履歴への依存そのものを減らす」機構ではない。DAF は transaction が自然に終了するのを待つだけで、能動的な forwarding や retention 短縮の手段は持たない。この違いは §7 の Long-Running Transactions の節 (上記引用) でDAF自身の限界として認めている。
- **(4) 共通の物理構造で版選択・forwarding 可否判断・validation を安くする**: **言っていない**。DAF は既存の version chain・index 構造の外側に被せる汎用キュー/API であり (defer(action) 一関数のみが公開 API)、版のメタデータを局所化・共通化して探索や validation を安くするようなデータ構造上の工夫は提案していない。むしろ "Because DAF decouples action processing from action generation" (§1, p.1) とあるように、**意図的に処理を分離する**設計であり、共通の物理構造で複数の判断を一括して安くする方向とは逆である。

### この論文の関連研究・引用から見つけた、本案に近い別の先行研究 (§7 Related Work より)
- **Microsoft Hekaton** (Diaconu et al., "Hekaton: SQL Server's Memory-Optimized OLTP Engine", SIGMOD 2013, 参考文献[10]): "a cooperative approach where actively running transactions are also responsible for version-chain pruning during query processing... Transactions refer to the 'high watermark' (i.e., the start timestamp of the oldest active transaction) to identify obsolete versions." (§7, p.7)。原典未確認、CIDR 論文の引用テキストから存在のみ確認。
- **SAP HANA** (Sikka et al., SIGMOD 2012, 参考文献[25] および GC の記述元として[16]と推定): "periodically triggers a GC background thread using the same watermarks... also uses an interval-based approach where the DBMS prunes unused versions in the middle of the chain." (§7, p.7)。原典未確認。
- **Böttcher, Leis, Neumann, Kemper, "Scalable garbage collection for in-memory MVCC systems", PVLDB 13(2), 2019** (参考文献[8]): 長い tx への対策の緩和策候補として §7 で名指しされている。原典未確認、題名・venue は CIDR 論文の参考文献リストから直接確認した (逐語ではなく書誌情報として確認)。
- **Chandramouli et al., "FASTER: A concurrent key-value store with in-place updates", SIGMOD 2018** (参考文献[9]): epoch を refresh しないスレッドの影響として長い tx 問題と並べて引用されている。原典未確認。
- **Neumann, Mühlbauer, Kemper, "Fast serializable multi-version concurrency control for main-memory database systems" (HyPer), SIGMOD 2015** (参考文献[21])。長い tx の影響が同種であるとして引用。原典未確認。
- いずれも「原典で確かめた」ものではなく、CIDR 2021 論文の関連研究節テキストの逐語引用から存在を確認したのみ。本系列でさらに深掘りする場合は、これらの原典を別途取得する必要がある。

---

## まとめ (担当1・担当2共通の結論)

- CCBench §7 に関するメモの (a)〜(e) はすべて **一致**。節番号・図番号のずれはなかった。§7.1/7.2/7.3 という小節構成もメモの想定通り。
- CIDR 2021 “Everything is a Transaction” は、メモ §23.4 が引用する「transactional semantics と物理データ構造 maintenance の分断」という問題意識を確かに持っている (逐語一致)。ただし、この論文が解決するのは「GC・index cleanup 等の非transactional maintenance タスクの実行タイミングを、transaction の epoch/timestamp 状態を使って安全に決める」という**汎用フレームワーク**の問題であり、VHash 案の中心である (1) 物理配置を timestamp 制御の入力にする、(2) 版選択と timestamp 選択を同時に扱う、(4) 共通物理構造で版選択・forwarding・validation を安くする、の3点は**読んだ範囲では見当たらない**。(3) 前進を GC 境界に接続する、という発想だけは epoch-watermark 方式として重なるが、これは DAF 自身が Hekaton/HANA 由来の**既存の受動的な**手法として引用しているものであり、VHash 案が言う「transaction 側を能動的に forward させて retention を縮める」方向とは異なる。さらに DAF 自身が「長い transaction には効かない」ことを §7 で明示的な限界として認めており、これは CCBench の Insight 6 / RapidGC の限界と同型の課題が、この論文でも未解決のまま残っていることを示している。
