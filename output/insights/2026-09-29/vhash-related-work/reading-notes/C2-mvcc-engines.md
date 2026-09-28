# C2-mvcc-engines: in-memory MVCC エンジンの版管理・可視性判定・版探索の系統

担当: Hekaton / HyPer MVCC / ERMIA / BOHM / Silo の 5 本 (原典指定)。加えて関連研究から本案 (VHash +
選択的 timestamp forwarding、出典メモ §0・§23) の 4 点に近い先行研究を 3 本追加。

指示めいた文字列: 取得した PDF・二次情報のいずれにも指示めいた文字列は見つからなかった。

---

## 1. Hekaton (Larson, Blanas, Diaconu, Freedman, Patel, Zwilling, PVLDB 5(4), 2011)

- 書誌: Per-Åke Larson, Spyros Blanas, Cristian Diaconu, Craig Freedman, Jignesh M. Patel, Mike
  Zwilling. "High-Performance Concurrency Control Mechanisms for Main-Memory Databases." PVLDB
  5(4):298–309, 2011. DOI 10.14778/2095686.2095689.
- 取得元: https://www.microsoft.com/en-us/research/wp-content/uploads/2011/12/MVCC-published-revised.pdf
  (Microsoft Research 版、PVLDB revised と明記)。保存先
  `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/hekaton-pvldb2011.pdf`
  (SHA-256 `0abcc1ff2eb15d2100f9bdca749ed8237a126e756e5c66c13e6f7717af470bdd`, 12 頁、PVLDB
  頁番号 298–309 と一致)。`.txt` は同ディレクトリの `hekaton-pvldb2011.txt` (pdftotext -layout)。
- 読んだ範囲: §1 Introduction (要旨部分)、§2.1–§2.7 (Storage/Indexing, Updates, Transaction
  Phases, Version Visibility, Updating a Version, Commit Dependencies) 全文、§3.1–§3.4
  (Optimistic: Normal Processing, Preparation, Postprocessing, Lower Isolation Levels) 全文、
  §4.1 (Pessimistic: Lock Types) の冒頭のみ、§5.1–§5.3 (評価: Homogeneous/Heterogeneous/TATP)
  全文、§6 Related Work、§7 Concluding Remarks。未読: §4.2–§4.4 (pessimistic の詳細処理)、
  §8 謝辞、§9 参考文献の逐語 (書誌のみ確認)。

### 機構比較 6 列
1. **入力**: 版の Begin/End フィールドの中身 (timestamp か、進行中トランザクションの ID か) と、
   読み手の logical read time RT。"To determine whether a version V is visible to T, we check V's
   Begin and End fields. If both fields contain timestamps, we simply check whether RT falls
   between the two timestamps." (§2.5, p.300)
2. **変える状態**: 版の Begin/End (Active 時は tx ID、確定後は timestamp)、GC 対象マーク。
   "A transaction ID stored in the End field serves as a write lock... A transaction Id stored in
   the Begin field informs readers that the version may not yet be committed" (§2.2, p.299)
3. **不変条件**: optimistic は backward validation によるシリアライザビリティ (read の再可視性 +
   phantom)。"Instead of validating a read set against the write sets of all other transactions,
   we simply check whether a version that was read is still visible as of the end of the
   transaction." (§3.1, p.301)。phantom は ScanSet の再走査で検出 (§3.2, p.302)。
4. **減らすコスト**: バルク挿入・更新の write-write 検出コストと read の block を減らす設計だが、
   GC アルゴリズム自体の詳細は明示的に scope 外: "Details of our garbage collection algorithm are
   beyond the scope of this paper." (§2.1, p.299)。版探索コストを減らす特別な配置 (最新版を head
   に置く等) は明記されておらず、ハッシュバケット内の全版を線形に舐める: "a scan of bucket J that
   checks every version in the bucket but returns only the one whose valid time overlaps the read
   time." (§2.2, p.299)
5. **旧版を新たに読めるか**: 可能。RT が Begin/End 区間に入る版であれば、GC されるまでいつでも読める
   (multi-version、single-version ではない)。
6. **長い tx への効き方**: 実験で直接評価。「1 本の long read-only tx が加わるだけで 1V (single
   version locking) の update throughput は 75% 落ちるが、MV 方式は 5% しか落ちない」("At x=1,
   update throughput drops 75% for the single version engine. In contrast, update throughput drops
   only 5% for the MV schemes, making MV twice as fast as 1V." §5.2.2, p.307)。ただし GC 側で
   長い tx が版保持義務を伸ばす具体的な対処は書かれていない (GC 詳細が scope 外のため)。read-only
   比率が増えるほど update 活動が減るため GC 負荷も下がる、という副次的言及のみ: "This is primarily
   because the update activity is reduced, reducing the overhead of garbage collection." (§5.2.1,
   p.306)

### 本案 4 点との一致度
1. **配置を timestamp 制御の入力にする**: 言っていない (読んだ範囲では)。版はハッシュバケットの
   連結リストに置かれるだけで、位置 (hot/cold) に応じて tx の timestamp を変える機構は記述されて
   いない。探索は「バケット内の全版を検査」(§2.2, p.299) であり、位置情報を read timestamp
   決定に使う記述はない。
2. **版選択と timestamp 選択を同時に扱う**: 言っていない。RT はトランザクションの begin time
   (serializable/repeatable read) か「現在時刻」(read committed) のどちらかで固定的に決まり、
   個々の版の物理配置とは独立 (§2.5, p.299–300)。
3. **前進を GC (保持義務の縮小) へ接続する**: 言っていない。GC アルゴリズムの詳細が明示的に scope
   外とされているため (§2.1, p.299)、前進のような手当ての記述はない。
4. **複数版メタデータを共通構造にまとめて版選択・forwarding 可否判断・validation を安くする**:
   言っていない (読んだ範囲では)。各版は自分の Begin/End/HashPtr を個別に持つのみで、複数版を
   横断する共有メタデータ構造は記述されていない。

### 関連研究からの追加候補
- §6 で MVSV (Carey)、MVPV (Agrawal et al.)、SSI (Cahill et al. 2008/2009) を引用しているが、
  いずれも古典的な optimistic multi-version 方式で、本案の 4 点に近い記述は見当たらない
  (読んだ範囲、§6 全文)。

---

## 2. HyPer MVCC (Neumann, Mühlbauer, Kemper, SIGMOD 2015)

- 書誌: Thomas Neumann, Tobias Mühlbauer, Alfons Kemper. "Fast Serializable Multi-Version
  Concurrency Control for Main-Memory Database Systems." SIGMOD 2015, pp.677–689. DOI
  10.1145/2723372.2749436。
- 取得元: https://db.in.tum.de/people/sites/muehlbau/papers/mvcc.pdf (著者本人サイト、TUM)。
  保存先 `src/hyper-mvcc-sigmod2015.pdf` (SHA-256
  `af94b3c882ac62189d1fd77ddede4d34b8d8d228a2d59df25ce09db6fa6c3bd2`, 13 頁、677–689 の頁数と一致)。
  `.txt` は `hyper-mvcc-sigmod2015.txt`。
- 読んだ範囲: Abstract/§1 の冒頭、§2.1 Version Maintenance、§2.2 Version Access、§2.3
  Serializability Validation (§2.3.1 Predicate Logging、§2.3.2 Implementation Details)、§2.4
  Garbage Collection、§2.5 Handling of Index Structures、§2.6 Efficient Scanning、§2.7
  Synchronization of Data Structures を全文、§4.2 Insert/Update/Delete Benchmarks の該当箇所、
  §5.1 Multi-Version Concurrency Control (Related Work)、§5.2 冒頭、§6 Conclusion を読んだ。
  未読: §3 Theory (形式化・証明) の詳細、§4.1 Setup、§4 の残り (TPC-H 個別数値など)。

### 機構比較 6 列
1. **入力**: 読み手の startTime と、undo buffer チェーン中の各版の validity timestamp。
   "Any read access of a transaction with startTime below T5 applies this version delta and any
   read access with a startTime above or equal to T5 ignores it" (§2.1)。書き込み側の validation
   は「直近コミットされた write が今コミットしようとしている tx の read predicate 空間と交差するか」
   を検査する precision locking 系。
2. **変える状態**: 最新版は in-place 更新、旧版は undo buffer 内の before-image delta として
   newest-to-oldest にチェーン化。"we refrain from creating new versions in newly allocated areas
   as in Hekaton [8, 23]; instead we update in-place and maintain the backward delta between the
   updated (yet uncommitted) and the replaced version in the undo buffer" (§2.1) — Hekaton との
   対比を著者自身が明記。
3. **不変条件**: full serializability (SI ではない)。precision locking の適応で「直近コミット分の
   write が committing tx の read predicate と交差しないこと」を検証 (§2.3)。
4. **減らすコスト**: (a) 版の再構成コストを before-image delta で安くする: "version
   'reconstruction' is actually cheap, as we store the physical before-image deltas" (§2.2)。
   (b) スキャン性能を VersionedPositions synopsis (1024 レコード単位の範囲要約) で維持:
   "Maintenance of VersionedPositions is very cheap... Using the VersionedPositions synopses,
   adjacent unversioned records are accumulated to one range where version checking is not
   necessary." (§2.6)。実測: "scan performance is improved by more than 5.5×" (§4.2)。
   (c) 更新コストはチェーンの長さと無関係: "As the newest version is stored in-place and the
   version record of the previous version is inserted at the beginning of the version chain,
   performance of updates is also independent of the total number of versions." (§4.2)
5. **旧版を新たに読めるか**: GC されるまで可能。ただし GC は継続的で「ごく一部だけが versioned
   のまま残る」設計 (§2.1, §2.4)。
6. **長い tx への効き方**: GC の watermark は「いずれかのアクティブ tx から可視な更新を持つ、
   最も古い committed tx の timestamp」("the now oldest visible transactionID, i.e., the oldest
   timestamp of a transaction that has updates that are visible by at least one active
   transaction", §2.4) で、長い読み取り tx がいれば当然 watermark は進まない。ただし本当に
   極端に長い tx への対処は「打ち切って snapshot からやり直す」方向: "the long-running
   transaction can be aborted and restarted on a snapshot [29]" (§4.2, ref [29] = 別稿の virtual
   memory snapshot 手法)。related work でも同様に述べる: "we previously proposed using virtual
   memory snapshots for long-running transactions [29], where updates are merged back into the
   database at commit-time." (§5.1)

### 本案 4 点との一致度
1. **配置を timestamp 制御の入力にする**: 一部だけ言っている、ただし主旨が異なる。「最新版は
   hot な in-place 領域、旧版は undo buffer (別領域)」という物理的な hot/cold 分離は明確に採用
   している (§2.1 の Hekaton との対比の引用)。しかし、この配置情報を使って「transaction の
   timestamp を前進させる」という記述はない。物理配置は再構成コストを決めるだけで、
   timestamp/tx の可視区間を制御する入力にはなっていない (読んだ範囲では)。
2. **版選択と timestamp 選択を同時に扱う**: 言っていない。startTime はトランザクション開始時に
   固定され (§2.1、"reads are performed in the state that existed at the start of the
   transaction" §2.2)、実行中に版を選び直すために timestamp を動かす記述はない。
3. **前進を GC へ接続する**: 言っていない。GC の watermark は標準的な「最古のアクティブ tx の
   開始時刻」方式 (§2.4) であり、前進によって保護境界を動かす仕組みはない。長い tx への対処は
   「打ち切って別の snapshot 機構に切り替える」であって timestamp 前進ではない。
4. **共通の物理構造で版選択・forwarding 可否判断・validation を安くする**: 一部だけ言っている。
   VersionedPositions は「レコード範囲ごとに版の有無をまとめた synopsis」であり、複数レコードに
   ついて版検索を一括して安くする共通構造ではある。ただし対象は「同じレコードの複数版」ではなく
   「多数レコードのうちどれが versioned か」であり、単一キーの版選択・validation を安くする
   構造ではない。precision locking の undo buffer 一括検証 (§2.3) は、単一 tx の validation を
   read-set 全体でなく write-set 側の undo buffer 数に依存させる点で、多少 (4) に近い発想だが、
   「版選択」を安くする話ではなく「validation」だけの話である。

### 関連研究からの追加候補
- §5.1 で Lomet et al. の「main-memory DB 向けに transaction の timestamp 範囲を使う MVCC」への
  言及があるが、書誌が本文中で番号引用のみ ([27]) で、参考文献一覧の該当エントリを直接は確認
  できていない (原典で確認できず、参照番号のみ)。
- 同節で Hyder (Bernstein et al.) を「log-structured multi-version DB」として紹介しているが、
  timestamp forwarding や配置ベースの制御の言及はない (読んだ範囲)。

---

## 3. ERMIA (Kim, Wang, Johnson, Pandis, SIGMOD 2016)

- 書誌: Kangnyeon Kim, Tianzheng Wang, Ryan Johnson, Ippokratis Pandis. "ERMIA: Fast
  Memory-Optimized Database System for Heterogeneous Workloads." SIGMOD 2016, pp.1675–1687. DOI
  10.1145/2882903.2882905。
- 取得元: https://www.cs.sfu.ca/~tzwang/ermia.pdf (共著者 T. Wang の個人ページ)。保存先
  `src/ermia-sigmod2016.pdf` (SHA-256
  `0c9f8151e25da64241ad36f40c32fa7298f9b5bfa469644945d3fbe1b204b22a`, 13 頁、1675–1687 の頁数と
  一致)。`.txt` は `ermia-sigmod2016.txt`。
- 読んだ範囲: §1 Introduction 冒頭 (heterogeneous workload の動機部分)、§3.2 Indirection
  arrays、§3.4 Epoch-based resource management、§3.5 Transaction management、§3.6 Concurrency
  control (§3.6.1 Snapshot Isolation、§3.6.2 Serializability/SSN) を全文、§5 Related Work と §6
  Conclusion を全文。未読: §3.1 Overview、§3.3 Logging の大半 (LSN 管理の詳細は見出しのみ確認)、
  §3.7 Recovery、§4 Evaluation (図表のキャプションのみ見た程度で本文は未読)。

### 機構比較 6 列
1. **入力**: 読み手の begin timestamp と、version chain を辿って見つけた各版の creation
   timestamp (または owner tx の commit 状態)。"the reader transaction needs to perform
   visibility check directly on LSN-stamped versions by comparing its begin timestamp and the
   version's creation timestamp." (§3.6.1)
2. **変える状態**: indirection array のスロット (OID→物理ポインタ)、TID テーブルの
   begin/end timestamp と status、SSN の π(T)/η(T) スタンプ。"Each entry in the TID table records
   the transaction's full TID..., begin timestamp (an LSN), end timestamp (if one exists), and
   current status." (§3.5)
3. **不変条件**: SI (既定) + SSN によるシリアライザビリティ検証。"ERMIA adopts a recent proposal,
   the Serial Safety Net (SSN) [48], which provides both serializability and balanced
   reader/writer performance" (§3.6.2)
4. **減らすコスト**: indirection array による「ほぼタダの多版対応」。"indirection arrays allow
   cheap (almost free) multi-versioning at an extremely low overhead" (§3.6)。GC は indirection
   array を周期的に走査: "The garbage collector periodically scans the indirection arrays and
   removes any versions that are not needed" (§3.2)。3 段階 epoch (very-short/medium/multi-tx
   scale) で「straggler と busy thread の誤検出」を避け、epoch 更新コストを下げる (§3.4)。
5. **旧版を新たに読めるか**: 可能。version chain を辿って creation timestamp が begin timestamp
   より前の最初の版を返す (§3.6.1)。
6. **長い tx への効き方**: この論文の主題そのもの。lightweight OCC (Silo 等) は「read-mostly な
   長い tx がしばしば abort させられる」問題があるとし、SI ベースの ERMIA で解決を図る。
   "lightweight OCC usually aborts loser transactions at commit time, wasting precious CPU cycles
   on long transactions that are destined to abort... heavyweight read-mostly transactions often
   lead to significant overall performance degradation" (§1)。関連研究節でも Silo との対比:
   "In order to support large read-only transactions, a heavyweight copy-on-write snapshot
   mechanism must be invoked. These snapshots are too expensive to use with small transactions"
   (§5, Silo との比較)。

### 本案 4 点との一致度
1. **配置を timestamp 制御の入力にする**: 言っていない (読んだ範囲では)。indirection array は
   「更新の局所化」のための間接参照であり、版の物理的な新旧位置を timestamp 決定の入力にする
   記述はない。
2. **版選択と timestamp 選択を同時に扱う**: 言っていない。begin timestamp は tx 開始時に固定
   (TID table の begin timestamp フィールド、§3.5) されており、読む版はそこから chain を辿って
   都度決まるだけで、timestamp 側を動かす記述はない。
3. **前進を GC へ接続する**: 言っていない。GC は epoch-based resource management の標準的な
   RCU 型 (§3.4) で、「読者の timestamp を前進させることで保持義務を縮める」という記述はない。
4. **共通の物理構造で版選択・forwarding 可否判断・validation を安くする**: 一部だけ言っている。
   indirection array は「更新の局所化」による validation コスト削減 (index を汚さない、§3.2) に
   寄与するが、これは版選択そのものを安くする構造ではない。SSN の π(T)/η(T) は「版ごとに
   pstamp/sstamp を持たせて validation を軽くする」という点で共通メタデータ的だが、これは
   validation 専用のメタデータであり、版選択や forwarding 可否判断には使われていない
   ("record versions also maintain their π (sstamp) and η (pstamp) values", §3.6.2)。

### 関連研究からの追加候補
- §5 で Hekaton が "indirection map" に類する技術を使うと明記: "It is worth mentioning that
  Hekaton also uses a technique similar to the indirection map. ... In Hekaton, Bw-tree [30]
  exploits indirection map and delta records to achieve lock-free design." — Bw-Tree
  (Levandoski, Lomet, Sengupta, ICDE 2013) が候補になりうるが、これは index 構造の話で version
  chain の共通メタデータ構造とは主旨が異なる (読んだ範囲、書誌未追加照合)。

---

## 4. BOHM (Faleiro, Abadi, PVLDB 8(11), 2015)

- 書誌: Jose M. Faleiro, Daniel J. Abadi. "Rethinking Serializable Multiversion Concurrency
  Control." PVLDB 8(11):1190–1201, 2015. DOI 10.14778/2809974.2809981。
- 取得元: http://www.cs.umd.edu/~abadi/papers/rethink-mvcc.pdf (共著者 Abadi の個人ページ)。
  保存先 `src/bohm-pvldb2015.pdf` (SHA-256
  `ea7dff6561ff555fe5663924a3f2622fc93b8adad9cf875b9041738d5f5159cb`, 12 頁、1190–1201 の頁数と
  一致)。`.txt` は `bohm-pvldb2015.txt`。
- 読んだ範囲: §3.2 Concurrency Control (§3.2.1 Timestamp Assignment、§3.2.2 Inserting
  Placeholders、§3.2.3 Processing a single transaction's read/write set、§3.2.4 Batching)、
  §3.3.2 Garbage Collection を全文、§4.2.2–4.2.3 (Hekaton/SI の timestamp counter ボトルネック、
  Impact of Long Read-only Transactions) を全文。未読: §1 Introduction、§2 Motivation、§3.1、
  §3.3.1、§4.1、§4.2.1、§4.3 SmallBank 以降、§5、§6 Conclusions。

### 機構比較 6 列
1. **入力**: 各 record の write-set 所属 (パーティション) と、concurrency control 層が事前に
   知る read-set/write-set の全体像。"An optimization to eliminate this cost is possible if the
   concurrency control phase has advanced knowledge of the read-sets of transactions" (§3.2.3)
2. **変える状態**: 版チェーンへの placeholder 挿入 (値は未確定のまま先に version を作る)、
   読み取り用の「正しい版への直接参照」を tx にあらかじめ書き込む。"concurrency control threads
   annotate the transaction with a reference to the correct version of the record to read...
   the correct version is simply the most recent version at the time the concurrency control
   thread is running." (§3.2.3)
3. **不変条件**: serializability を、書き込みが読み取りをブロックする形で保証 (reads never
   block writes, but writes can block reads)。timestamp はログ内の位置で単一に決まる
   ("B OHM assigns each transaction a single timestamp, ts ... ts 'squashes' tbegin and tend
   together", §3.2.1)。
4. **減らすコスト**: 版探索コストをゼロに近づける。"B OHM can obtain a reference to the version
   of a record required by a transaction without accessing any preceding or succeeding versions.
   In contrast, in Hekaton and SI, ... the system must traverse the list of succeeding versions
   ... Version traversal overhead is not specific to our implementations of Hekaton and SI – it
   is inherent in systems which determine the visibility of each transaction's writes after the
   transaction has finished executing." (§4.2.3, p.1199) — 「timestamp を実行後に決める設計だと
   版探索が避けられない」という診断を明言している。GC は batch 単位の low-watermark
   (min の実行中 batch 番号) で行う (§3.3.2)。
5. **旧版を新たに読めるか**: 可能 (GC されるまで Prev Pointer で遡れる、§3.2.3)。ただし通常の
   読み取りは CC 層が事前に annotate した「最新版への直接参照」を使うため、遡り自体は基本的に
   発生しない設計。
6. **長い tx への効き方**: 読み取り専用 tx の比率が増えるほど「1 本あたりの実行時間が長くなる」
   ため全体スループットは下がるが、multi-version 方式同士では B OHM が Hekaton/SI より速い
   ("we find that B OHM significantly outperforms Hekaton and SI. We attribute this difference
   to B OHM's read-set optimization", §4.2.3)。GC への影響は明記されておらず (原典で確認
   できず)、batch 単位の low-watermark が長い読み取り tx でどう遅延するかの直接記述は
   見当たらなかった (読んだ範囲)。

### 本案 4 点との一致度
1. **配置を timestamp 制御の入力にする**: 言っていない。読み取り版の決定は「CC 層が read-set/
   write-set を事前に知っている」ことに基づく事前計算であり、版の物理的な新旧位置 (hot/cold) を
   timestamp 制御の入力にする記述はない。
2. **版選択と timestamp 選択を同時に扱う**: 一部だけ言っている。ts が tbegin/tend を "squash"
   して単一化し (§3.2.1)、さらに読み取る版への参照を CC フェーズが timestamp 決定と同時に
   annotate する (§3.2.3) という点で、「版選択と timestamp を同時に扱う」設計思想は確かにある。
   ただし機構は本案と異なる: 事前の全体知識 (read-set/write-set の一括把握) による決定論的な
   事前計算であり、「既読値を保てる範囲で hot な旧版を選ぶ」ような、読み手ごとの forwarding
   判断ではない。
3. **前進を GC へ接続する**: 言っていない。GC は batch の low-watermark 方式で、timestamp の
   前進という概念自体が存在しない (単一 timestamp がログ位置で確定するのみ)。
4. **共通の物理構造で版選択・forwarding 可否判断・validation を安くする**: 一部だけ言っている。
   §4.2.3 の診断 ("determine the visibility of each transaction's writes after the transaction
   has finished executing" が版探索コストの根本原因) は、本案の問題意識と同じ方向を向いている。
   しかし解決手段は「共通メタデータ構造」ではなく「別レイヤ (CC phase) による事前決定的な
   参照配布」であり、版メタデータを共通構造にまとめる話ではない。

### 関連研究からの追加候補
- 読んだ範囲 (§3, §4.2 のみ) には related work 節が含まれておらず、追加候補は見つけられなかった
  (§5/§6 が未読のため、関連研究からの発見は今回は無し)。

---

## 5. Silo (Tu, Zheng, Kohler, Liskov, Madden, SOSP 2013)

- 書誌: Stephen Tu, Wenting Zheng, Eddie Kohler, Barbara Liskov, Samuel Madden. "Speedy
  Transactions in Multicore In-Memory Databases." SOSP 2013, pp.18–32. DOI
  10.1145/2517349.2522713。
- 取得元: https://sigops.org/s/conferences/sosp/2013/papers/p18-tu.pdf (公式 SIGOPS 会議 PDF)。
  保存先 `src/silo-sosp2013.pdf` (SHA-256
  `870c895f654a6c11c616086b64c6b2c9d45f8f3fc46faa1f071b7c4cafa74ce3`, 15 頁、18–32 の頁数と一致)。
  `.txt` は `silo-sosp2013.txt`。
- 読んだ範囲: §1 Introduction (epoch への言及部分)、§2 Related Work (Masstree/PALM/Bw-tree の
  段落)、§4.1 Epochs、§4.2 Transaction IDs、§4.4 Commit protocol、§4.5 Database operations、
  §4.6 Range queries and phantoms、§4.7 Secondary indexes、§4.8 Garbage collection、§4.9
  Snapshot transactions (前半、ロガー記述の手前まで) を全文。未読: §3 設計概要、§4.3 Data
  layout の詳細、§4.9 後半 (ロギング以降)、§5 Evaluation、§6 Conclusion。

### 機構比較 6 列
1. **入力**: 通常 tx は commit 時点の global epoch とレコードの TID (§4.4)。snapshot tx は
   自分が start 時に固定した local snapshot epoch `sew` とレコードの epoch(r.tid)。"Every worker
   w also maintains a local snapshot epoch sew; at the start of each transaction, it sets
   sew ← SE. Snapshot transactions use this value to find the right record versions. For record
   r, the relevant version is the most recent one with epoch ≤ sew." (§4.9)
2. **変える状態**: レコードの TID word (epoch+連番+status bit)、必要な場合のみ
   previous-version pointer で旧版を lazily に作る。"If the values differ, the old version must
   be preserved for current or future snapshot transactions, so the read/write transaction
   installs a new record whose previous-version pointer links to the old one." (§4.9)
3. **不変条件**: フルシリアライザビリティ (OCC + epoch 順序、S2PL への還元で証明、§4.4)。
4. **減らすコスト**: 通常運用は基本的に single-version (in-place 更新) にとどめ、"old version"
   を作るのは「今の版が、まだ有効な snapshot epoch にまたがって上書きされる場合」だけに限定する
   ことで、版保持そのものを最小化: "the transaction compares snap(epoch(r.tid)) and snap(E). If
   these values are the same, then it is safe to overwrite the record" (§4.9)。GC は per-core の
   epoch-based RCU で、tree ノードと record の両方を回収 (§4.8)。
5. **旧版を新たに読めるか**: 通常の read/write tx は不可 (常に最新版のみ、OCC の検証で
   リトライ/abort するだけ)。旧版を読めるのは、client が明示的に選ぶ snapshot transaction
   だけで、しかも読めるのは開始時に固定された 1 つの snapshot epoch に対応する版のみ (任意の
   過去の版を後から選んで読むことはできない)。
6. **長い tx への効き方**: 2 つの言及がある。(a) 通常の長い read/write tx はローカル epoch
   `ew` を更新し続ける必要があり、更新を怠ると GC 全体を遅延させる: "Silo requires that E and
   ew never diverge too far: E − ew ≤ 1 for all w. ... Workers running very long transactions
   should periodically refresh their ew values to ensure the system makes progress." (§4.1)。
   (b) 長い読み取り専用 tx は、abort を避けるために snapshot transaction として実行することが
   推奨される: "Epochs have other benefits as well; for example, we use them to provide database
   snapshots that long-lived read-only transactions can use to reduce aborts." (§1)。ただし
   snapshot epoch は現在から k=25 epoch (約 1 秒) 遅れた粒度でしか進まない: "The snapshot epoch
   snap(e) for epoch e equals k · be/kc; currently k = 25, so a new snapshot is taken about once
   a second." (§4.9)

### 本案 4 点との一致度
1. **配置を timestamp 制御の入力にする**: 言っていない。版を作るかどうかは snapshot epoch との
   比較で決まるが (§4.9)、これは「必要なら 1 個だけ old version を作る」ことの判断材料であって、
   物理配置 (hot/cold) が timestamp 側を動かす入力にはなっていない。
2. **版選択と timestamp 選択を同時に扱う**: 言っていない。通常 tx の TID は commit 時点で
   決まり (§4.2)、snapshot tx の sew は開始時に固定 (§4.9) — どちらも版の物理配置とは無関係に
   独立して決まる。
3. **前進を GC (保持義務の縮小) へ接続する**: 一部だけ言っている、ただし方向が違う。§4.1 は
   「長い tx が epoch を進めないと GC が止まる」という逆方向の警告であり、"前進させて保持義務を
   縮める" という能動的な仕組みではなく、"tx 側が自発的に epoch を更新しないと GC が遅れる" と
   いう受動的な注意書きである。
4. **共通の物理構造で版選択・forwarding 可否判断・validation を安くする**: 言っていない。
   TID word に lock/latest-version/absent の 3 bit を同居させて単一 atomic 操作で扱うという
   最適化はあるが (§4.2)、これは 1 版内のメタデータの詰め込みであり、複数版を横断する共通構造
   ではない。

### 関連研究からの追加候補
- §2 で Bw-tree (Levandoski, Lomet, Sengupta, ICDE 2013) を「RCU 型 epoch で GC する
  multi-version tree」として言及: "Like Silo, the Bw-tree uses RCU-style epochs for garbage
  collection; Silo's epochs also support scalable serializable logging and snapshots." — GC の
  epoch 方式という点で近いが、本案の 4 点そのもの (配置による timestamp 制御など) への直接の
  言及ではない (読んだ範囲)。

---

## 追加候補 (関連研究から発見、最大 3 本)

### A. Böttcher, Leis, Neumann, Kemper. "Scalable Garbage Collection for In-Memory MVCC
Systems." PVLDB 13(2):128–141, 2019. DOI 10.14778/3364324.3364328. (システム名 "Steam")

- 取得元: https://users.cs.utah.edu/~pandey/courses/cs6530/fall22/papers/mvcc/p128-bottcher.pdf
  (講義資料ミラー、著者版と同一と推定。ACM 公式頁 128–141 と PDF 頁数 14 が一致)。保存先
  `src/bottcher-pvldb2019.pdf` (SHA-256
  `ceae3ff7928379a76d52ec4dc5e3b71ab5d8e26f8fe69dcf27d075a8d22b40e5`)。`.txt` は
  `bottcher-pvldb2019.txt`。
- 読んだ範囲: Abstract、Figure 1 (vicious cycle 図)、§4.3 Eager Pruning of Obsolete Versions
  (§4.3.1 Short-Lived Transactions、§4.3.2 HANA's Interval-Based GC との比較)、§4.4 Layout of
  Version Records、Table 2 (HANA との比較表)、Table 4 (Hekaton/ERMIA/HANA/Steam の watermark
  設定比較表) を読んだ。未読: §1–§3 (導入・モデル・GC 全体設計)、§5 Evaluation、§6 Related
  Work。
- 見つけた理由: HyPer 論文の後続 (同じ TUM グループ、Neumann/Kemper 共著) で、「長い tx が MVCC の
  GC をボトルネックにする」問題そのものを主題とする。abstract で明言: "It turns out that in the
  presence of long-running queries, state-of-the-art garbage collectors are too coarse-grained.
  ... Old versions cannot be garbage collected as long as there are long-running transactions
  that have to retrieve them" (Figure 1 キャプション)。
- 機構要約: 版チェーンに触れるたび (更新時) に、現在アクティブな timestamp の集合と照合して
  不要な中間版を eager に刈り取る (EPO)。"In Steam, the pruning happens during every update of a
  tuple, i.e., whenever the version chain is extended by a new version. Thereby, a chain will
  never grow to more versions than the current number of active transactions and will never
  contain obsolete versions." (§4.3.2)
- 本案 4 点との一致度: 点 (3) 「前進を GC の保護条件へ接続し旧版の保持期間を縮める」に対して
  一部だけ言っている。目的 (長い tx がいても保持版数を最小化する) は共通するが、手段が違う:
  本案は「読み手の timestamp を前進させる (forwarding)」ことで GC の保護境界を動かすのに対し、
  Steam は「読み手のアクティブ timestamp 集合と照合して不要な版を能動的に刈り取る (pruning)」
  だけで、読み手の timestamp 自体は変えない。点 (1)(2)(4) への直接の言及は読んだ範囲では
  見当たらなかった。

### B. Freitag, Kemper, Neumann. "Memory-Optimized Multi-Version Concurrency Control for
Disk-Based Database Systems." PVLDB 15(11):2797–2810, 2022. DOI 10.14778/3551793.3551832.

- 取得元: https://www.vldb.org/pvldb/vol15/p2797-freitag.pdf (VLDB 公式)。保存先
  `src/freitag-pvldb2022.pdf` (SHA-256
  `dc933deb8243e29ce66da9e3a10a5eb08f194330483cc7336e2c6578d4b90e29`, 14 頁、2797–2810 の頁数と
  一致)。`.txt` は `freitag-pvldb2022.txt`。
- 読んだ範囲: Abstract、§3.1 In-Memory Version Maintenance、§3.1.1 Version Maintenance、§3.1.2
  Garbage Collection、Figure 2/3/4 のキャプションと周辺本文を全文。未読: §1–§2 (導入・関連
  システム)、§4 Evaluation、§5 以降。
- 見つけた理由: 同じ TUM グループの後続研究で、ディスクベースシステム (Umbra) 向けに
  「最新版だけをディスクのページに置き、旧版は全て in-memory に置く」という物理的な hot/cold
  分離を明示的に採用している。"Database pages that can be evicted to disk store only the most
  recent version of a data object. ... all additional versioning information resides
  exclusively in-memory." (§3.1、Figure 2 キャプション)
- 本案 4 点との一致度: 点 (1) 「物理配置 (cold 領域に入ること) を timestamp 制御の入力にする」に
  一部だけ言っている。最新版=ディスク行き得る (cold になりうる) 場所、旧版=常に in-memory
  (hot) という設計は本案と発想が近いが、本案とは逆方向 (本案は「旧版が cold 領域に落ちる前に
  timestamp を前進させて hot 版で済ませる」、Freitag et al. は「そもそも旧版は最初から
  hot=in-memory に固定し、ディスクに落ちるのは最新版だけ」) であり、配置を timestamp 制御の
  入力にする記述はない (transaction の timestamp は通常の MVCC の begin/commit timestamp の
  ままで、配置に応じて動かす機構はない)。GC は Böttcher らの Steam をそのまま採用
  ("Garbage collection is based on the highly scalable Steam algorithm devised for in-memory
  systems, albeit with some extensions to account for the local mapping tables", §3.1) — 点 (3)
  についても上記 Steam と同じく一部一致にとどまる。

### C. Tonta, Seeger, Soisalon-Soininen. "Multiversion Concurrency Control for Multiversion
B-Trees." arXiv:2606.09133v1 [cs.DB], 2026-06-08 投稿 (PVLDB 投稿形式だが巻号は未確定の
プレースホルダ表記、後述)。

- 取得元: https://arxiv.org/pdf/2606.09133 。保存先 `src/mvbt-arxiv2606.09133.pdf` (SHA-256
  `78d16075ee964d89aea4060c2c84ad5224058333776dd2075e56e8fe6a680bb0`, 13 頁)。`.txt` は
  `mvbt-arxiv2606.09133.txt`。
- 読んだ範囲: Abstract、§1 Introduction 全文 (version list 方式・CoW 方式それぞれの欠点、vWeaver
  への言及箇所を含む)、参考文献 [15]–[19] の書誌確認。未読: §2 以降の cMVBT 本体設計・評価。
- 書誌上の注記: 本文冒頭の "PVLDB Reference Format" に `PVLDB, 14(1): XXX-XXX, 2020` という
  記載があるが、arXiv 投稿日は 2026-06-08 であり、著者・巻号・年が矛盾するプレースホルダ
  (テンプレートの埋め忘れ) と判断される。実際の掲載先・巻号は本文からは確認できず「未確定」
  として扱う。
- 見つけた理由・vWeaver との関係: 本文が候補ヒントの "vWeaver" を直接引用しており、その出典は
  参考文献 [18] = Jongbin Kim, Kihwang Kim, Hyunsoo Cho, Jaeseon Yu, Sooyong Kang, Hyungsoo
  Jung. "Rethink the Scan in MVCC Databases." SIGMOD 2021, pp.938–950 (ACM SIGMOD 2021 Best
  Paper Honorable Mention、DOI 10.1145/3448016.3452783) であると確認した (書誌は実在確認済み:
  ACM DL の該当頁、著者本人ページ https://hyungsoo-jung.github.io/ の publication list の
  両方で確認)。**ただし vWeaver 論文自体の本文は ACM のペイウォールに阻まれ取得できなかった**
  (著者ページ・SNU/Hanyang 関連ページを検索したが公開 PDF は見つからず、ACM DL の PDF
  エンドポイントも HTML のログイン頁を返した)。そのため vWeaver 自身の機構は「本文を取得できず」
  とし、以下は cMVBT 論文 (Tonta et al.) 側からの二次的な説明であることを明記する: "clever
  garbage collection and more advanced list organization, such as frugal skiplists and
  vWeaver [18], mitigate the retrieval problem, they can incur substantial overhead for range
  scans for mixed workloads." (§1)
- cMVBT 自身の機構 (原典で確認): version list 方式 (B+-tree の各キーに版リストを付与) と
  CoW 方式の両方を批判し、multiversion B-tree (MVBT) の並行制御版を提案。"the concurrent MVBT
  (cMVBT), a redesign of the MVBT featuring a novel concurrency control protocol that uses
  optimistic latches for write operations and requires no latches for range scans" (Abstract)。
- 本案 4 点との一致度: 点 (4) 「複数版メタデータを共通の物理構造にまとめて版選択・validation を
  安くする」に一部だけ関連。cMVBT/vWeaver はいずれも「version chain を辿るコストを、索引寄りの
  構造 (MVBT のページ木、または frugal skip list) に置き換えて安くする」という問題意識は本案の
  版探索コスト削減と方向性が重なる。しかし対象が単一キーの読み取り・validation ではなく
  **range scan** (多数キーにまたがる版の一括走査) であり、本案が扱う「単一キーの版選択・
  forwarding 可否判断・validation を安くする」設計射程とは異なる。timestamp forwarding や
  hot/cold 配置による timestamp 制御への言及は cMVBT 本文 (§1、読んだ範囲) にはない。

---

## 検索・取得の記録まとめ

| 論文 | 取得元 | SHA-256 (先頭16桁) | 頁数 | 版 |
|---|---|---|---|---|
| Hekaton PVLDB 2011 | microsoft.com (MS Research revised) | 0abcc1ff2eb15d21 | 12 | PVLDB revised |
| HyPer MVCC SIGMOD 2015 | db.in.tum.de (著者) | af94b3c882ac6218 | 13 | 著者公開版 |
| ERMIA SIGMOD 2016 | cs.sfu.ca (共著者) | 0c9f8151e25da642 | 13 | 著者公開版 |
| BOHM PVLDB 2015 | cs.umd.edu (共著者) | ea7dff6561ff555f | 12 | 著者公開版 |
| Silo SOSP 2013 | sigops.org (公式) | 870c895f654a6c11 | 15 | 公式 camera-ready |
| Böttcher PVLDB 2019 (Steam) | users.cs.utah.edu (講義ミラー) | ceae3ff7928379a7 | 14 | 著者版と同一と推定 |
| Freitag PVLDB 2022 | vldb.org (公式) | dc933deb8243e29c | 14 | 公式 |
| Tonta et al. arXiv 2606.09133 (cMVBT) | arxiv.org | 78d16075ee964d89 | 13 | arXiv v1 (2026-06-08) |
| Kim et al. SIGMOD 2021 (vWeaver) | (未取得、ACM ペイウォール) | — | — | 本文未取得 |

全 PDF は `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/` に保存。repo
(`/work/1/SFC/tanab/izanagi`) には一切書き込んでいない。
