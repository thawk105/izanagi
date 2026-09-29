# 読み取りメモ: D-contention (gen-opt md_2、2026-09-29)

指示めいた文字列: なし (6 件の本文・README・source のいずれにも、作業の振る舞いを変えるよう求める文字列は見つからなかった)。

読み取りと記録のみ。repo の file は編集していない。取得時刻は UTC (JST は +9 時間)。抽出テキストの頁番号は PDF 内の頁順 (論文の印字頁ではない)。

## 0. 取得の要約

| 論文 | 取得元 | 取得時刻 (UTC) | SHA-256 | 状態 |
|---|---|---|---|---|
| Bamboo (SIGMOD 2021、extended version) | https://arxiv.org/pdf/2103.09906 | 2026-09-29T01:02:11Z | `4381c05f05812689864b396dad987b69a02ac0e690cf3e3df1d33270d0c23f07` (`src/bamboo.pdf`、14 頁) | 本文取得 |
| Rebirth-Retire (PVLDB 18(9), 2025) | 既取得 `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/rebirth-retire.pdf` (2026-09-29 03:34 JST に取得済み) | 既取得 | `005e2d84fdfaac45ab3ec24837f22a83a3d75c7c3131c50175760ae3cfa03655` | 本文 (`src/rr.txt` は段組を解く形の再抽出) |
| Polaris (SIGMOD 2023) | 本文 PDF は取得できず。README と source を github.com/ssya23/polaris (master) から `raw.githubusercontent.com` 経由で取得 | 2026-09-29T01:02:56Z (README)、2026-09-29T01:03:38Z (source) | README `6a44a8cdc8acfeae032007cbca979acc701b81a436816daa52bc91fe01aeeec2`、`row_silo_prio.h` `4713597f5db5f2b123ba9b60a6cdbf7e87eaa425cf1660b33250bea5cb48abe7`、`row_silo_prio.cpp` `e44d2ab0763f92e4b7db8ab49ed09b5bb61a6972935cf45173b0fcb32b751c61` | **論文本文でなく source から取った** |
| Plor (SIGMOD 2022) | https://storage.cs.tsinghua.edu.cn/papers/sigmod22plor.pdf | 2026-09-29T01:02:14Z | `336c2c92cfe262b76cb02e37d6e9805b79bdccd405717a5f2064ea4c1a1f5810` (`src/plor.pdf`、15 頁) | 本文取得 |
| STOv2 (PVLDB 13(5), 2020) | https://www.vldb.org/pvldb/vol13/p629-huang.pdf | 2026-09-29T01:02:16Z | `0ba782941384e1c0c5dd18eef6f450f90d2d5563e9d40e2fbc75b37d37eb279a` (`src/stov2.pdf`、14 頁) | 本文取得 |
| Shirakami (arXiv:2303.18142、v3 = 2 Jul 2026 の版) | 既取得 `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/shirakami.pdf` | 既取得 | `e9cf8b914e00130e2b9a0260047eaaeb20a0df30ad60bedde9c534b6cd078b03` | 本文 (`src/shir.txt` は段組を解く形の再抽出) |

Polaris の取得試行の記録:
- `https://dl.acm.org/doi/pdf/10.1145/3588724` は PDF でなく HTML を返した (ACM 403 系。本文にならず破棄)。
- `https://pages.cs.wisc.edu/~chenhaoy/publication/polaris/polaris.pdf` (検索結果が示した path) は HTTP 404 (HTML)。`www.cs.wisc.edu` 側の同 path も 404。
- arXiv: `arxiv.org/pdf/2302.06136` を試したが別論文 (blockchain) で破棄。arXiv に Polaris 論文は見つからなかった (検索結果は「ACM 掲載のみ」との趣旨)。
- github.com/chenhao-ye/polaris は検索結果に現れたが、README と source は `ssya23/polaris` から取れた (README 冒頭に artifact 用 `ARTIFACT.md` への参照あり、未取得)。
- Polaris の記録 3 件は、README の build parameter 記述と `row_silo_prio.{h,cpp}` の実装から作った。数値の効果は本文を読めていないため書いていない。検索ツールが返した要約 (abstract 相当の文) が述べる主張 (高優先度 transaction の p999 latency の低減、abort-aware 方策での改善) は、原典で確認していない二次情報である。

## 1. 読んだ節・読んでいない節 (論文ごと)

| 論文 | 読んだ節 | 読んでいない節 |
|---|---|---|
| Bamboo | §3 (3.1-3.6)、§4.1-4.2、§5.1-5.4 (5.4 は YCSB 部分)、§5.5 の冒頭部 | §1-2 (背景)、§5.5-5.6 の詳細、§6 以降、付録 |
| Rebirth-Retire | §1、§2.1-2.3、§3、§4、§5.1-5.5 (Table 1-4 と Fig. 2-9 の本文記述)、§6-7 | 図の実測値そのもの (本文の記述のみ)、付録 |
| Polaris | README、`row_silo_prio.h`、`row_silo_prio.cpp` | 論文本文の全節、`system/txn.cpp` 等の呼び出し側 |
| Plor | §1 (Limitations 含む)、§2.3 の要点、§3、§4.1-4.2、§4.3 冒頭、§6.2.1-6.2.2、§6.4 | §2 の詳細、§4.3 の証明本文、§5、§6.1、§6.3、§6.5 以降 (図の値は本文に出るもののみ) |
| STOv2 | Abstract、§1-9 (Fig. 4、Fig. 7、Fig. 12 の表 12g を含む) | 各図の曲線そのもの、Fig. 8-9 の個別の点 |
| Shirakami | Abstract、§1-2 の要点、§3 全体、§5 (結果本文)、§6.1 | §4 (Tsurugi・各 benchmark の図と表)、§7 以降、付録。S-OCC と Silo だけを比べる実測は読んだ範囲に無い |

## 2. 論文ごとの最適化の一覧 (JSONL 41 件)

### Bamboo (7 件)
- `bamboo-lock-retire` (protocol-core): Lock retire (early lock release, violating 2PL)
- `bamboo-commit-semaphore-cascading-abort` (protocol-core): commit_semaphore による commit 順序保証と cascading abort
- `bamboo-retire-point-synthesis` (optimization): 最後の write の後で retire する点を program analysis で合成する (retire 条件の合成、loop fission)
- `bamboo-opt1-no-latch-read-retire` (optimization): Optimization 1: No extra latches for read operations
- `bamboo-opt2-skip-retire-tail-writes` (optimization): Optimization 2: No retire when there is no benefit (最後の delta 割合の write を retire しない)
- `bamboo-opt3-no-raw-abort` (optimization): Optimization 3: Eliminate aborts due to read-after-write conflicts
- `bamboo-opt4-dynamic-timestamp` (optimization): Optimization 4: Assign timestamps to a transaction on its first conflict

Bamboo の 4 最適化 (§3.5) のうち ablation 図があるのは Opt2 (BAMBOO-base との対比、Fig. 4-5) のみ。他の 3 件は本文の記述だけで、単体の効果を示す表・図は読んだ範囲に無い。

### Rebirth-Retire (7 件)
- `rr-passive-retire` (protocol-core): Passive Retire (retire を待ち側の要求で起動する)
- `rr-rebirth` (protocol-core): Rebirth (older が younger を abort せず自分に大きい timestamp を振り直す)
- `rr-parents-children-dependency-lists` (optimization): commit_semaphore を parents / children の依存リストに置き換える
- `rr-o1-latch-free-dependency-tracking` (optimization): O1: Latch-free Dependency Tracking (children を 8 byte atomic word の bit で持つ)
- `rr-o2-optimistic-read-descendant` (optimization): O2: Optimistic Read Descendant (子孫 txn object を lock せず Version で楽観読みする)
- `rr-o3-assign-larger-timestamps` (optimization): O3: Assign Larger Timestamps (Largest でなく Larger 戦略、hybrid timestamp)
- `rr-o4-version-prefetching` (optimization): O4: Version Prefetching (version chain に jump pointer を持たせ software prefetch)

O1-O4 の単体効果は Table 3 (YCSB の低/中/高 contention)。Bamboo の 4 最適化 (read の直接 retire、末尾 write の retire 省略、古い版を読ませて abort を避ける、first conflict で timestamp を付与) は Rebirth-Retire でも適用すると §4 冒頭が述べる (別カードにしていない)。

### Polaris (3 件、source のみ)
- `polaris-priority-reservation` (protocol-core): Priority reservation in the tuple TID word (SILO_PRIO)
- `polaris-no-reserve-lowest-prio` (optimization): Lowest-priority optimization (SILO_PRIO_NO_RESERVE_LOWEST_PRIO)
- `polaris-abort-aware-priority-increment` (optimization): Abort-aware priority assignment (abort 回数に応じた priority の引き上げ)

### Plor (6 件)
- `plor-optimistic-reading` (protocol-core): Pessimistic locking and optimistic reading (read-write conflict を read 段で無視し private buffer に書く)
- `plor-delayed-conflict-detection` (protocol-core): Delayed conflict detection with Wound-Wait timestamps (commit 段で timestamp 順に commit させる)
- `plor-latch-free-locker` (optimization): Latch-free locker (reader リストを 8 byte word の bit で持つ)
- `plor-delayed-write-lock-acquisition` (optimization): Delayed write-lock acquisition (DWA: write lock を commit 段まで遅らせる)
- `plor-read-only-dynamic-validation` (optimization): Read-only transaction: 最初は validation、3 回 abort したら read lock を使う
- `plor-atomic-ctx-word` (optimization): status と ts を同じ 64 bit 語に置き、kill を語全体の CAS で行う

### STOv2 (9 件: 技法 3 件 + 実装上の要因 = basis factor 6 件)
- `stov2-commit-time-updates` (optimization): Commit-time updates (CU: read-modify-write を updater 付きの blind write にする)
- `stov2-timestamp-splitting` (optimization): Timestamp splitting (TS: record の列を部分集合に分け、部分集合ごとに timestamp を持つ)
- `stov2-contention-aware-index` (optimization): Contention-aware indexes (key の成分ごとに 8 byte を割り当て、別の B-tree 層へ写す)
- `stov2-basis-memory-allocation` (design-dimension): Basis factor: Memory allocation (スケーラブルな汎用 allocator を基準にする)
- `stov2-basis-contention-regulation` (design-dimension): Basis factor: Contention regulation (retry の前の randomized exponential backoff)
- `stov2-basis-abort-mechanism` (design-dimension): Basis factor: Abort mechanism (C++ 例外でなく戻り値の明示検査で abort する)
- `stov2-basis-index-types` (design-dimension): Basis factor: Index types (hash table を使える所で使う)
- `stov2-basis-deadlock-avoidance` (design-dimension): Basis factor: Deadlock avoidance (write set の sort でなく bounded spinning)
- `stov2-basis-transaction-internals` (design-dimension): Basis factor: Transaction internals (read / write set を hash table で管理する)

STOv2 は、commit-time updates、timestamp splitting、contention-aware index を 1 件ずつ、basis factor (memory allocation、contention regulation、abort mechanism、index types、deadlock avoidance、transaction internals) を 1 件ずつ記録した。basis factor は「設計次元」として `kind: "design-dimension"` にした。論文が Fig. 7 に載せる basis factor の列見出しは 7 つ (下の逐語表。contention-aware index はその 1 つで、技法としても 1 件にした)。

### Shirakami (9 件)
- `shirakami-write-preservation` (optimization): Write preservation (WP: S-LTX が書込み領域を table 単位で予告し、S-OCC が read 時と commit 時に検査する)
- `shirakami-reader-epoch-metadata` (optimization): Reader-epoch metadata (record ごとに最新の read epoch だけを atomic に持つ)
- `shirakami-wp-optimistic-lock-fixed-array` (optimization): WP の管理: 楽観 lock (LSB を lock bit、残りを version) と固定長 array
- `shirakami-order-forwarding` (protocol-core): Order forwarding (S-LTX の直列化 epoch の動的変更)
- `shirakami-read-area-declaration` (optimization): S-LTX: Read area declaration
- `shirakami-on-demand-version-order` (optimization): S-LTX: On-demand version order determination (non-visible write rule による write と log の省略)
- `shirakami-epoch-lower-bound` (optimization): S-LTX: Lower bound of serialization order (begin timestamp の代わりに epoch を下限にする)
- `shirakami-safe-snapshot` (optimization): In-memory snapshot: unsafe snapshot と safe snapshot (read-only は safe snapshot で validation を省く)
- `shirakami-reuse-deleted-records` (optimization): S-OCC: Reuse of deleted records

Shirakami の S-OCC (Silo からの変更) は次の 2 つが中心で、それぞれ 1 件にした。(1) write preservation の検査 (`shirakami-write-preservation`)。(2) reader-epoch metadata (`shirakami-reader-epoch-metadata`)。WP の管理方式 (楽観 lock と固定長 array、§3.6) を 3 件目にした。文面上の食い違いとして、WP を S-OCC が検査する時点は、§3.1.2 が「read の前に WP を検知して abort できる」と述べる一方、Algorithm 2 は commit 段の `wp_conflict` のみを示す。カードには両方を併記した。

## 3. JSONL に入れなかった候補 (理由つき)

- Bamboo §3.4 の weak isolation 対応、opacity が要る場合の Wound-Wait への退避、Wait-Die への適用の議論: 独立した名前付き技法ではなく議論の節。
- Bamboo の interactive mode 評価 (§5.1、Fig. 8b・9b・10b): 最適化でなく評価条件。
- Rebirth-Retire が Bamboo から継承する 4 最適化: 上記のとおり別カードにしていない (原典は継承と述べるのみ)。
- Plor の insert の扱い (Silo 方式の事前 insert)、range query: Silo の手法の流用と本文が述べる。§4.1.3。
- Plor の 3 つ目以降の節 (§5 以降): 未読。
- STOv2: MSTO の inlined version (Cicada の最適化の継承、§2.2)、Silo の fast order-ID optimization (workload 側の実装)、delivery transaction の queue (TPC-C 仕様)、TicToc の delta-rts 符号化を使わず 64 bit の wts / rts を別々に持つ変更 (§2.3、「性能低下は無かった」と本文が述べる)、RCU 型の epoch GC (§2.1)、MVCC の read-only を rtsg の過去時刻で実行する扱い (§2.2): いずれも STOv2 の基盤の説明であり、論文が名前を付けて独立に評価した技法ではないため除外。ただし version-lifetime 系の関連事実として上の RCU / gcts の記述 (§2.1) は参照価値がある。
- Shirakami: epoch の長さ (3 ms、§3.4.1)、logging と non-visible write rule (§3.4.2、`shirakami-on-demand-version-order` に統合)、S-OCC の phantom 回避 (§3.3.3、Silo の node-set 検査に依拠)、S-LTX の staging (§3.1.2)、transaction mode の選択 (§3.1.6): 独立の最適化として評価されていない、または他カードに含めた。
- Polaris: 論文本文が名付ける他の技法は不明 (本文未読)。source に現れる `writer_release_*` 系の priority 再設定、`unlock()` による validation 中の backoff (`row_silo_prio.h` の comment「temporarily release the lock ... only happen as a backoff in validation」) は、論文上の名前と評価を確認できないためカード化しなかった。

## 4. 注意 (数値の扱い)

- カードの数値は、原典の表・図・節に添えられるものだけを書いた。図の曲線から読み取った数値は書いていない。
- Bamboo の効果分類 (`effect_category`) の多くは `none` にした。3 分類のうち cpu-cache に当てたものは、論文自身が latch・cache・prefetch を理由に挙げる場合か、「推測:」と明記した場合に限る。
- Plor と Shirakami の一部の「効果」は、論文が別の目的 (tail latency、long transaction の commit 保証) の指標で示したもので、throughput の直接比較ではない。カードの `workloads_effective` に何の指標かを併記した。

## 5. STOv2 (Huang ほか) の逐語資料

以下は `src/stov2.txt` (pdftotext) から機械的に切り出した原文で、抽出の都合による改行と頁番号の混入がある。

### 5.1 §4 冒頭 (basis factor の定義と導入)

```
Main-memory transaction processing systems differ in concurrency control, but also often differ in implementation choices such
as memory allocation, index types, and backoff strategy. In years
of running experiments on such systems, we have developed a list
of basis factors where different choices can have significant impact
on performance. This section describes the basis factors we have
found most impactful. For instance, OCC’s contention collapse on
TPC-C can stem not from inherent limitations, but from particular basis factor choices. We describe the factors, suggest a specific
choice for each factor that performs well, and conduct experiments
using both high- and low-contention TPC-C to show their effects on
performance. We end the section by describing how other systems
implement the factors, calling out important divergences.
Figure 4 shows an overview of our results for OSTO, which is
our focus in this section. The heavy line represents the OSTO baseline in which all basis factors are implemented according to our
guidelines. In every other line, a single factor’s implementation is
replaced with a different choice taken from previous work. The impact of the factors varies, but on high-contention TPC-C, four factors have 20% or more impact on performance, and two factors can
cause collapse. In TSTO and MSTO, the basis factors have similar
impact, except that memory allocation in MSTO has even larger impact due to multi-version updates; we omit these results for brevity.
```

### 5.2 basis factor の列見出しと各 system の評価 (Fig. 7 の表、`pdftotext -layout`)

```
                                  Contention      Memory                                                               Transaction     Deadlock                               Contention-
           System                 regulation     allocation     Aborts             Index types                          internals      avoidance                              aware index
           Silo [49]                 −−              −−          −−                    −                                    −              +                                      +
           STO [21]                  −−              −−          −−                    +                                    +              +                                      +
           DBx1000 OCC [56]           +             N/A           +                    +                                    −             −−                                     −−
           DBx1000 TicToc [57]        +             N/A           +                    +                                    −              +                                     −−
           MOCC [50]                 N/A             +            +                    +                                    +              +                                     −−
           ERMIA [24]                 +               +          −−                    −                                    +              +                                      +
           Cicada [31]                +               +           +                    +                                    +             N/A                                    N/A
           STOv2 (this work)          +               +           +                    +                                    +              +                                      +
Figure 7: How comparison systems implement the basis factors described in §4. On high-contention TPC-C at 64 cores, “+” choices have
at least 0.9× STOv2’s performance, while “−” choices have 0.7–0.9× and “−−” choices have less than 0.7×.
```

basis factor の節構成 (見出しの逐語): 4.1 Memory allocation / 4.2 Contention regulation / 4.3 Abort mechanism / 4.4 Index types / 4.5 Contention-aware indexes / 4.6 Other factors (Transaction internals と Deadlock avoidance をここで述べる) / 4.7 Summary。

### 5.3 §9 Related work (9.1-9.4、逐語)

```
RELATED WORK

9.1

Modern concurrency control research

Concurrency control is a central issue for databases and work
goes back many decades [18]. As with many database properties,
the best concurrency control algorithm can depend on workload,
and OCC has long been understood to work best for workloads
“where transaction conflict is highly unlikely” [27]. Since OCC
transactions cannot prevent other transactions from executing, OCC
workloads can experience starvation of whole classes of transactions. Locking approaches, such as two-phase locking (2PL), lack
this flaw, but write more frequently to shared memory. Performance
tradeoffs between OCC and locking depend on technology characteristics as well as workload characteristics, however, and on multicore main-memory systems, with their high penalty for memory

FUTURE WORK

In future work, we hope to investigate the remaining bottlenecks
in STOv2’s performance. We plan to focus on the MSTO implementation of both timestamp splitting and commit-time updates;
in addition MSTO might benefit from garbage collection improvements and additional Cicada optimizations. In OSTO the transaction processing machinery accounts for just 4.2% of the total runtime in low-contention TPC-C, leaving little room for further improvement.

638

contention, OCC can perform surprisingly well even for relatively
high-conflict workloads and long-running transactions. This work
was motivated by a desire to better understand the limitations of
OCC execution, especially on high-conflict workloads.
The main-memory Silo database [49,58] introduced an OCC protocol that, unlike other implementations [8, 27], lacked any pertransaction contention point, such as a shared timestamp counter.
Though Silo addressed some starvation issues by introducing snapshots for read-only transactions, and showed some reasonable results on a high-contention workload, subsequent work has reported
that Silo still experiences performance collapse on other high-contention workloads. These discrepancies are due to its basis factor
implementations, as discussed in §4.
Since Silo, many new concurrency control techniques have been
introduced. We concentrate on those that aim to preserve OCC’s
low-contention advantages and mitigate its high-contention flaws.
TicToc’s additional read timestamp allows it to commit some
apparently-conflicting transactions by reordering them [57]. Timestamp maintenance becomes more expensive than OCC, but reordering has benefits for high-contention workloads. We present
results for our implementation of TicToc.
Transaction batching and reordering [11] aims to discover more
reordering opportunities by globally analyzing dependencies within
small batches of transactions. It improves OLTP performance at
high contention, but requires more extensive changes to the commit protocol to accommodate batching and intra-batch dependency
analyses. We consider our workload-specific optimizations orthogonal to these techniques as our optimizations eliminate unnecessary
dependency edges altogether instead of working around them.
Hybrid concurrency control in MOCC [50] and ACC [46] uses
online conflict measurements and statistics to switch between OCClike and locking protocols dynamically. Locking can be expensive
(it handicaps MOCC in our evaluation), but prevents starvation.
MVCC [4, 41] systems, such as ERMIA [24] and Cicada [31],
keep multiple versions of each record. The multiple versions allow more transactions to commit through reordering, and read-only
transactions can always commit. ERMIA uses a novel commit-time
validation mechanism called the Serial Safety Net (SSN) to ensure strict transaction serializability. ERMIA transactions perform
a check at commit time that is intended to be cheaper and less conservative than OCC-style read set validations, and to allow more
transaction schedules to commit. The SSN mechanisms in ERMIA,
however, involve expensive global thread registration and deregistration operations that limited its scalability [50]. In our experiments, ERMIA’s locking overhead – a kind of basis factor – further
swamps any improvements from its commit protocol. Cicada contains optimizations that reduce overhead common to many MVCC
systems, and in its measurements, its MVCC outperforms singleversion alternatives in both low- and high- contention situations.
This disagrees with our results, which show OSTO outperforming
Cicada at low contention (Figure 9b). We believe the explanation
involves basis factor choices in Cicada’s OCC comparison systems.
Our MSTO MVCC system is based on Cicada, though we omit several of its optimizations.
Optimistic MVCC still suffers from many of the same problems
as single-version OCC. When executing read-write transactions
with serializability guarantees, read-write and write-write conflicts
still result in aborts. Optimizations such as commit-time updates
and timestamp splitting can alleviate these conflicts.
Static analysis can improve the performance of high-contention
workloads, since given an entire workload, a system can discover
equivalent alternative executions that generate many fewer conflicts. Transaction chopping [44] uses global static analysis of all

possible transactions to break up long-running transactions such
that subsequent pieces in the transaction can be executed conflictfree. More recent systems like IC3 [51] combine static analysis
with dynamic admission control to support more workloads. Static
analysis techniques are complementary to our work, and we hope
eventually to use static analysis to identify and address false sharing in secondary indexes and database records, and to automate the
application of commit-time updates and timestamp splitting.

9.2

Basis factors

Several prior studies have measured the effects of various basis
factors on database performance. A recent study found that a good
memory allocator alone can improve analytical query processing
performance by 2.7× [14]. A separate study presented a detailed
evaluation of implementation and design choices in main-memory
database systems, with a heavy focus on MVCC [55]. Similar to our
findings, the results acknowledge that CC is not the only contributing factor to performance, and lower-level factors like the memory
allocator and index design (physical vs. logical pointers) can play a
role in database performance. While we make similar claims in our
work, we also describe more factors and expand the scope of our
investigation beyond OLAP and MVCC.
Contention regulation [17] provides dynamic mechanisms, often orthogonal to concurrency control, that aim to avoid scheduling
conflicting transactions together. Cicada includes a contention regulator. Despite being acknowledged as an important factor in the
database research community, our work demonstrates instances in
prior performance studies where contention regulation is left uncontrolled, leading to potentially misleading results.
A review of database performance studies in the 1980s [2] acknowledged conflicting performance results and attributed much of
the discrepancy to the implicit assumptions made in different studies about how transactions behave in a system. These assumptions,
such as how a transaction restarts and system resource considerations, are analogous to basis factors we identified in that they do
not concern the core CC algorithm, but significantly affect performance results. Our study highlights the significance of basis factors
in the modern context, despite the evolution of database system architecture and hardware capabilities.

9.3

High-contention optimizations

Our commit-time update and timestamp splitting optimizations
have extensive precursors in other work. Timestamp splitting resembles row splitting, or vertical partitioning [38], which splits
records based on workload characteristics to optimize I/O. Taken
to an extreme, row splitting leads to column stores [28, 45] or
attribute-level locking [32]. Compared to these techniques, timestamp splitting has coarser granularity; this reduces fine-grained
locking overhead, and suffices to reduce conflicts, but does not facilitate column-store-like compressed data storage.
Commutativity has long been used to improve concurrency in
databases, file systems, and distributed systems [3,26,37,42,43,54],
with similar effects on concurrency control as commit-time updates. We know of no other work that applies commutativity or
commit-time updates to MVCC records, though many systems reason about the commutativity properties of modifications to MVCC
indexes. Upserts in BetrFS [22, §2.2] resemble how we encode
commit-time updates; they are used to avoid expensive key-value
lookups in lower-layer LSMs rather than for conflict reduction. Differential techniques used in column store databases [19] involve
techniques and data structures that resemble commit-time updates,
though their goal is to reduce I/O bandwidth usage in an readmostly OLAP system.

639

9.4

Transactional memory

CNS-1704376, CNS-1513416, CNS-1513447, and CNS-1513471.
We’re grateful to Stratos Idreos, Andy Pavlo, and Peter Alvaro for
thoughtful comments on earlier drafts. Thanks also to anonymous
reviewers of the work.

Extensive experience with transactional system implementation
is also found in the software transactional memory space [9,12,20];
there are even multiversion STMs [5, 16]. Efficient STMs can run
main-memory database workloads, and we base our platform on
one such system, STO [21]. Some of our baseline choices were
inspired by prior STM work, such as SwissTM’s contention regulation [12]. STO’s type-aware concurrency control included preliminary support for commit-time updates and timestamp splitting, but
only for OCC.
STO has also been used as a baseline for other systems that
address OCC’s problems on high-contention workloads, such as
DRP [36]. DRP effectively changes large portions of OCC transactions into commit-time updates by using lazy evaluation, automatically implemented by C++ operator overloading, to move most
computation into OCC’s commit phase. This works well at high
contention, but imposes additional runtime overhead that our simpler implementation avoids.
Several systems have achieved benefits by augmenting software
CC mechanisms with hardware transactional memory (HTM) [29,
52, 53]. HTM can also be used to implement efficient deadlock
avoidance as an alternative to bounded spinning [52].

```
