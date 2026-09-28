# C1-mvcc-gc: MVCC の GC と長い transaction の系統 — 文献照合結果

担当: C1-mvcc-gc (MVCC GC・長い transaction 系統)。対象は VHash + 選択的 timestamp forwarding 案の
関連研究節向け。指示された 5 候補すべてが原典で実在確認でき、うち 4 本 (HANA を除く) は camera-ready
または著者公開技術報告の PDF を取得して本文を読んだ。HANA も camera-ready PDF (CMU 講義資料経由の
公式ミラー) を取得できた。加えて vDriver の後続論文 Diva の実在をもう一つの原典 (LeanStore 論文の
参考文献) から確認したが、本文は入手できていない。

**指示めいた文字列:** 取得した PDF・Web ページの中に、エージェントの振る舞いを変えようとする指示め
いた文字列は見つからなかった。

---

## 0. 取得記録一覧

保存先はすべて `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/` (repo 外)。

| ファイル | 取得元 URL | SHA-256 |
|---|---|---|
| steam-boettcher-pvldb13-2019.pdf | http://www.vldb.org/pvldb/vol13/p128-bottcher.pdf | ceae3ff7928379a76d52ec4dc5e3b71ab5d8e26f8fe69dcf27d075a8d22b40e5 |
| hana-hybridgc-sigmod2016.pdf | https://15721.courses.cs.cmu.edu/spring2019/papers/05-mvcc3/p1307-lee.pdf (camera-ready と同一内容、SIGMOD 2016 pp.1307-1318 の講義用ミラー) | e81d952698e8ad1c147073877f2b2df2c3b8ea19676dcde3f7f0d8bf95ea3db0 |
| vdriver-techreport.pdf | https://github.com/hyu-scslab/vDriver/raw/master/vdriver_techreport.pdf (著者リポジトリの Technical Report 版。表題・著者・abstract は SIGMOD 2020 版 (pp.495-510) と一致するが、本文が camera-ready と bit-identical である保証はない) | 5d24648fc9f79636b9e424dc5702df12088469d69fb8fa284feea6e07cbab3f1 |
| wu-empirical-mvcc-pvldb10-2017.pdf | https://www.vldb.org/pvldb/vol10/p781-Wu.pdf | e0f3d3be03734d2afd5de7681a268a7aead0572e9f254e49ff4b4852ba787bd1 |
| alhomssi-leanstore-si-pvldb16-2023.pdf | https://www.vldb.org/pvldb/vol16/p1426-alhomssi.pdf | c334ca5dcfdbe713bd69430c6a8236a818f1f83436f7ca643d7d8b830837f487 |

各 PDF は同じ場所に `pdftotext -layout` で `.txt` を作成して読んだ。

---

## 1. Steam — Böttcher, Leis, Neumann, Kemper, "Scalable Garbage Collection for In-Memory MVCC Systems"

- **書誌:** Jan Böttcher, Viktor Leis, Thomas Neumann, Alfons Kemper. *Scalable Garbage Collection
  for In-Memory MVCC Systems.* PVLDB 13(2): 128–141, 2019. DOI: 10.14778/3364324.3364328
- **取得元:** 上表。VLDB 公式 camera-ready PDF (14 頁、p.128–141)。
- **読んだ範囲:** §1 Introduction, §2 Versioning in MVCC (§2.1, §2.2), §3 GC Survey 冒頭,
  §4.2 (概要), §4.3 Eager Pruning of Obsolete Versions (EPO) (§4.3.1, §4.3.2), §4.4 Layout of
  Version Records, §5.6–5.7 実験 (Table 4, Table 5), §6 Related Work, §7 Conclusion。§5 の他の
  実験細部・§4.1 (thread-local active transaction 管理の詳細実装) は読んでいない。

### 機構の比較 6 列
1. **入力:** 現在アクティブな transaction の開始 timestamp の集合 (sorted, duplicate-free list)。
   「版チェーンを辿る/伸ばす」タイミング (update/insert 時) をトリガに使う。
   > "EPO is designed for mixed workloads... creating a set of active transactions will hardly
   > pay off, as the number of reducible version chains is small." (§4.3.1, p.133)
2. **変える状態:** 版チェーンそのもの (中間版を物理的に削除)。長い tx 自身の timestamp や snapshot
   は変えない。
   > "Steam prunes every version chain eagerly whenever it traverses one. It removes all versions
   > that are not required by any active transaction" (§1, p.128)
3. **保つ不変条件:** snapshot isolation の可視性 (active transaction に見えるべき版は必ず残す)。
   > "a version must be preserved as long as an active transaction requires it to observe a
   > consistent snapshot of the database." (§2.1, p.129)
4. **減らすコスト:** 版チェーン長 (traversal コスト)、GC 自体の処理時間。abort は減らさない/対象外。
   > 実測: "the engines with vDriver..." ではなく Steam 自身の実験、Table 5: "Traversed Versions
   > 1,197m → 4.2m" (Standard watermark vs EPO)。
5. **旧版を新たに読めるか:** 不可。EPO で prune された中間版は物理削除され、以後は読めない (読める
   のは active transaction の可視範囲に必要な版だけ)。
6. **長い tx への効き方:** 回収境界 (global minimum timestamp) 自体は長い tx がいる限り進まない
   (bound to oldest active transaction のまま)。EPO はその境界の中で「どの版が本当に必要か」を厳密化
   し、境界内の不要な中間版を都度削ることで chain 長を「アクティブ transaction 数」に上限を付ける。
   長い tx の timestamp・snapshot 自体は一切変更しない。abort もしない。
   > "In Steam, the pruning happens during every update of a tuple... a chain will never grow to
   > more versions than the current number of active transactions and will never contain obsolete
   > versions." (§4.3.2, p.134)
   > 関連研究 (Lee et al. = HANA 論文) からの引用として: "Lee et al. [20] describe practical
   > solutions to this problem such as: (1) flushing old versions to disk if main memory is
   > exceeded, (2) aborting long-running transactions (user gets an error), and (3) closing
   > transactions as soon as possible" (§6, p.139) — Steam 自身はこの 3 つのいずれも採用せず、
   > eager pruning のみで対処する立場を取る。

### 本案 4 点との対応
1. **物理配置を timestamp 制御の入力にする:** 言っていない (読んだ範囲、特に §4.3, §4.4)。Steam に
   は版の物理配置 (hot/cold 領域の区別) という概念自体が存在しない。version record は単一の版
   ストレージに置かれ、Table 3 (§4.4) のレイアウトも配置の区別を持たない。
2. **版選択と timestamp 選択を同時に扱う:** 言っていない。EPO は「どの版を残すか」だけを決め、reader
   (長い tx) 側の timestamp を動かす発想は読んだ範囲に見当たらない。
3. **前進を GC (保持義務の縮小) へ接続する:** 該当なし —前進という概念自体がない。ただし独立した
   近い軸として: EPO は「境界を進める」のではなく「境界内の中間版を削る」ことで保持義務を実質的に
   縮小しており、本案の(3)とは異なる経路で同じゴール (保持期間の短縮) に迫っている。
4. **複数版メタデータを共通の物理構造にまとめ、判断を安くする:** 言っていない。Table 3 のレコード
   レイアウトは通常の GC・rollback 用メタデータであり、forwarding 可否判断は存在しないため、それを
   安くする仕掛けもない。

### 関連研究からの近い先行研究
- §6 で "virtual memory snapshots (forks) for read-only queries" (Mühe, Kemper, Neumann,
  *Executing long-running transactions in synchronization-free main memory database systems*,
  CIDR 2013, [26]) が長い tx 対策として言及されているが、これは MVCC の timestamp 前進ではなく
  OS レベルのフォークによる読み取り専用スナップショット複製であり、本案とは機構が異なる。原典未取得
  (Steam 論文中の要約のみを確認)。

---

## 2. HANA HybridGC — Lee, Shin, Park, Ko, Noh, Chuh, Stephan, Han, "Hybrid Garbage Collection for Multi-Version Concurrency Control in SAP HANA"

- **書誌:** Juchang Lee, Hyungyu Shin, Chang Gyoo Park, Seongyun Ko, Jaeyun Noh, Yongjae Chuh,
  Wolfgang Stephan, Wook-Shin Han. *Hybrid Garbage Collection for Multi-Version Concurrency
  Control in SAP HANA.* SIGMOD 2016, pp.1307–1318. DOI: 10.1145/2882903.2903734
- **取得元:** 上表。camera-ready と同一内容の PDF (CMU 15-721 講義資料のミラー、12 頁、
  p.1307–1318、ACM の頁範囲と一致)。ACM DL 本体は 403 (認証不可) のため直接確認はできていないが、
  題名・著者・頁範囲・DOI・図番号が web 上の複数の独立記述 (dblp, ACM abstract ページ) と一致してお
  り、camera-ready と同一と判断した。
- **読んだ範囲:** §1 Introduction, §2 Preliminaries (§2.1–2.2), §3 Variants of Garbage Collector
  (§3.1–3.2)、§4 Implementation (§4.1 Global Group GC, §4.2 Interval GC, §4.3 Table GC, §4.4
  HybridGC), §5 Experiments (§5.2, §5.5, §5.6 の記述部分。図の数値そのものの精読は省略)、§6 Related
  Work。§7 Conclusion は未読。

### 機構の比較 6 列
1. **入力:** アクティブな snapshot timestamp の集合 (global STS tracker)。Table GC はさらに
   「どの snapshot がどの table にアクセスするか」(Stmt-SI ではクエリプランから静的に分かる) を追加
   入力にする。
   > "under Stmt-SI... the complete set of the accessed tables within that snapshot can be
   > retrieved by just accessing its compiled query plan." (§4.3, p.1312)
2. **変える状態:** (a) interval GC: 版チェーン中の中間版を削除。(b) table GC: グローバル STS
   tracker から per-table STS tracker へ snapshot timestamp を「移す」ことで、GC 境界の**適用範囲
   (スコープ)** を table 単位に分割する。reader (長時間 snapshot) 自身の timestamp は変えない。
   > "the snapshot timestamp of the classified snapshot is copied to one or more relevant
   > per-table snapshot timestamp trackers... snapshot timestamp of such snapshot is removed from
   > the global STS tracker." (§4.3, p.1312)
3. **保つ不変条件:** snapshot isolation (Trans-SI / Stmt-SI) の可視性。
4. **減らすコスト:** 版チェーン traversal コスト (RID hash table の hash collision 率低下)、長時間
   OLAP クエリのレイテンシ。
   > "HG performs the best, showing the shortest query latency among the three." (§5.5, p.1316)
5. **旧版を新たに読めるか:** GC された版は不可。Table GC でスコープ外になった table の版は通常通り
   回収されるため、以後読めない (対象 snapshot がその table にアクセスしないという前提が前段で
   保証されている)。
6. **長い tx への効き方:** 回収境界は長時間 snapshot が生きている限り「その snapshot が関係する
   table については」進まない。しかし Table GC により、長時間 snapshot が **関係しない table** の
   GC は妨げない (スコープの限定によって保持義務を局所化)。それでも解決しない場合の運用対処として、
   HANA は次を明示的に持つ (Steam 論文が要約していた 3 手段の原典に相当):
   > "Conventional workarounds for this version space overflow problem are as follows. 1) The
   > system flushes old versions out to disk. 2) The system closes problematic cursors or
   > Trans-SI transactions by force and returns errors to clients... 3) The system implicitly
   > closes cursors earlier than the explicit cursor close request." (§1, p.1307–1308)
   これらはいずれも「長い tx の timestamp を前進させる」のではなく、**abort/強制クローズ**または
   **ディスクへの退避**である。timestamp 前進の記述は読んだ範囲に見当たらない。

### 本案 4 点との対応
1. **物理配置を timestamp 制御の入力にする:** 一部だけ言っている、ただし方向が異なる。Table GC は
   「どの table にアクセスするか」という **意味論的スコープ** を GC 境界 (実質的に一種の物理的区画
   分け: per-table STS tracker) の入力にする。しかし、これは個々の版の物理配置 (hot/cold) の話では
   なく、また timestamp 制御 (reader 側の前進) には接続していない。§4.3 の範囲では言っていない。
2. **版選択と timestamp 選択の同時扱い:** 言っていない。読んだ範囲 (§1–§6) に reader 側 timestamp
   を動かす発想はなく、対処は abort/強制クローズである。
3. **前進を GC へ接続する:** 該当なし (前進の概念がない)。近い軸として、Table GC は「境界を進める」
   のではなく「境界の適用範囲を分割する」ことで保持義務を局所的に縮小している。
4. **共通の物理構造にまとめ判断を安くする:** 言っていない。TransContext / GroupCommitContext は
   commit 処理と GC 判定の共有のためのメタデータだが、forwarding 判断という概念がそもそも無い。

### 関連研究からの近い先行研究
- §6 で Silo (Tu et al.) の epoch ベース GC が "a variant of GT where each group corresponds to a
  set of transactions within an epoch" として言及され、また Loesing et al. の shared-data
  architecture ([12], load-link/store-conditional による MVCC) が "also uses the minimum snapshot
  timestamp... belongs to ST" と評されている。いずれも global/watermark ベースの GC 分類の一種として
  引用されており、本案の (1)〜(4) に新規に近いものではない。

---

## 3. vDriver — Kim, Cho, Kim, Yu, Kang, Jung, "Long-lived Transactions Made Less Harmful"

- **書誌:** Jongbin Kim, Hyunsoo Cho, Kihwang Kim, Jaeseon Yu, Sooyong Kang, Hyungsoo Jung.
  *Long-lived Transactions Made Less Harmful.* SIGMOD 2020, pp.495–510 (dblp: KimCKYKJ20;
  Hanyang University リポジトリでも確認)。DOI (SIGMOD版): 10.1145/3318464.3389714
- **取得元:** 上表。著者リポジトリ (github.com/hyu-scslab/vDriver) 公開の **Technical Report 版**
  PDF (17 頁、表題・全著者名・abstract は SIGMOD 版と一致)。表紙に明示的に
  "[Technical Report]" と記載されており、camera-ready (SIGMOD Proceedings 版、pp.495–510) との
  bit-identity は確認できていない。ACM DL は 403 で直接照合不可。
- **読んだ範囲:** Abstract, §1 Introduction (1.1–1.3), §2 Motivation and Related Work (2.1 の
  一部), §3 Design (§3.1 Theoretical Foundations — Theorem 3.5 含む, §3.2 Design Overview, §3.3
  vSorter — SIRO-versioning・version classification・dead zone-based version pruning, §3.4
  vCutter 冒頭)。§4 実装詳細・§5 評価の数値部分は精読していない。

### 機構の比較 6 列
1. **入力:** (a) pruning 判定: 「dead zone」— 連続する 2 つの live transaction の begin timestamp
   区間。(b) 版配置の分類 (version classification) 判定: 版の可視区間の長さ (update interval) と、
   その版が長寿命 transaction (LLT) の snapshot に含まれるか否か。
   > "vSorter considers three factors: start and end timestamps of a version, and a clear sign of
   > indicating that a version belongs to any snapshots of LLTs." (§3.3)
2. **変える状態:** 版の物理配置。SIRO-versioning により「直近版のみ in-row (データページ内)、残りは
   off-row (別領域)」に固定配置しつつ、off-row 側をさらに 3 クラス (VChot / VCcold / VCLLT) に
   物理的に分けて格納する。reader (LLT) 自身の timestamp は変えない。
   > "we classify versions as three classes: (i) hot versions (VChot), (ii) cold versions
   > (VCcold), and (iii) versions belonging to the snapshots of LLTs (VCLLT)." (§3.3)
3. **保つ不変条件:** 「non-reclaimable な版は生きている transaction が必要とする限り reachable で
   なければならない」という representation invariant、および Theorem 3.5 (Complete Version Pruning
   Theorem) による必要十分条件。
4. **減らすコスト:** 版空間 (メモリ/ストレージ) 使用量、および GC (pruning/segment cleaning) が
   「live だが無関係な版」によって止まるのを防ぐことで GC 処理そのものの停滞コストを減らす。index
   modification コスト (in-row 側は 1 版のみなので page split を抑制)。
5. **旧版を新たに読めるか:** 可能 (multi-version)。Theorem 3.5 で dead と判定され prune/cut される
   まではオフロー領域に保持され、生きている transaction は任意の必要な版を辿れる。
6. **長い tx への効き方:** LLT が必要とする版は VCLLT クラスに**隔離**され、VChot / VCcold クラスの
   pruning・segment cleaning を妨げない設計。LLT 自身の begin timestamp や read-view は変更しない。
   LLT を abort させる記述も読んだ範囲にはない。
   > "versions born around the same time are classed separately through version classification if
   > they differ considerably as to their visibility. By doing this, live versions in one class
   > would never impinge on the removal of dead versions in other classes." (§3.3)
   LLT の定義自体も明示されている: "we define a long-lived transaction as the one whose tb is
   older than a certain threshold δLLT, which is a multiple of an average transaction length."
   (§3.3)

### 本案 4 点との対応
1. **物理配置を timestamp 制御の入力にする:** 一部だけ言っている、ただし**逆方向**。vDriver は
   「timestamp (update interval・LLT 関与) を版の物理配置の入力にする」— 本案が意図する「物理配置を
   timestamp 制御の入力にする」の逆写像である。版を置いた後に reader 側の timestamp を動かす発想は
   読んだ範囲 (§3.1–3.4) に見当たらない。
2. **版選択と timestamp 選択の同時扱い:** 言っていない。version classification は「どの版をどの
   物理クラスタに置き、いつ pruning/cleaning するか」だけを決め、reader の timestamp 選択とは独立。
3. **前進を GC へ接続する:** 該当なし (前進の概念がない)。近い軸として、LLT が必要とする版を
   VCLLT に隔離することで、他クラスの保持義務 (=GC の停滞) を実質的に縮小している。これは Steam の
   EPO・HANA の Table GC と同じ「隔離による縮小」系であり、本案の「前進による縮小」とは異なる経路。
4. **共通の物理構造にまとめ、判断を安くする:** 一部だけ言っている。VS descriptor
   (seg_id, vmin, vmax) は segment 単位で pruning 可否を高速判定するための共通メタデータだが、これ
   は forwarding 可否判断のためではなく、pruning (削除可否) 判断のみを安くするものである。
   > "Each VS descriptor includes three fields—seg_id, vmin and vmax—used for deciding whether we
   > can reclaim the current segment" (§3.3)

### 関連研究からの近い先行研究
- 後続論文 **Diva** の実在を、本論文自身からではなく LeanStore 論文 (Alhomssi & Leis 2023) の参考
  文献 [30] から確認した (下記 §5 参照)。vDriver 本文の Related Work (§2.1 の一部のみ読了) からは
  Diva への言及を確認できていない (未読部分に含まれる可能性がある)。

---

## 4. Wu, Arulraj, Lin, Xian, Pavlo, "An Empirical Evaluation of In-Memory Multi-Version Concurrency Control"

- **書誌:** Yingjun Wu, Joy Arulraj, Jiexi Lin, Ran Xian, Andrew Pavlo. *An Empirical Evaluation of
  In-Memory Multi-Version Concurrency Control.* PVLDB 10(7): 781–792, 2017.
  DOI: 10.14778/3067421.3067427
- **取得元:** 上表。VLDB 公式 camera-ready PDF (12 頁、p.781–792)。
- **読んだ範囲:** §1 Introduction 冒頭, §4 Version Storage (4.1 Append-only [O2N/N2O],
  4.2 Time-Travel, 4.3 Delta, 4.4 Discussion), §5 Garbage Collection (5.1 Tuple-level [VAC/COOP],
  5.2 Transaction-level, 5.3 Discussion), §6 Index Management (6.1 Logical Pointers [PKey/TupleId],
  6.2 Physical Pointers, 6.3 Discussion)。§2 Background の MVCC 分類表 (Table 1)、§3 concurrency
  control protocol の詳細、§7 実験は未読 (見出しと表 1 のみ確認)。

### 機構の比較 6 列
本論文は特定機構を提案する論文ではなく、既存 in-memory MVCC 実装の設計選択肢を横断的に分類・実測
する empirical survey である。「機構」として書けるのは分類軸そのもの。
1. **入力:** (分類対象であり、単一の「入力」は無い) 各設計は version の begin-ts/end-ts、または
   transaction の write-set を入力に GC・可視性判定を行う。
2. **変える状態:** 版の物理配置 (append-only O2N/N2O、time-travel table、delta/rollback segment)、
   index のポインタ種別 (logical: PKey/TupleId、physical)。
3. **保つ不変条件:** MVCC の可視性規則一般 (個別プロトコルの正しさはこの論文の主題ではない)。
4. **減らすコスト:** 版探索コスト (index traversal, chain traversal)、GC スキャンコスト、書き込み時
   の index 更新コスト — 各設計選択のトレードオフとして提示。
5. **旧版を新たに読めるか:** 各方式共通で、GC されるまでは multi-version として保持され読める
   (append-only, time-travel, delta いずれも)。方式によって「読み取りコスト」が異なるのみ。
6. **長い tx への効き方:** 一般論としての記述のみで、対策の提案はない。
   > "The DBMS's performance drops in the presence of long-running transactions. This is because
   > all the versions generated during the lifetime of such a transaction cannot be removed until
   > it completes." (§6.1 直前の discussion 文脈, p.786)

### 本案 4 点との対応
本論文はサーベイであり新規機構を提案しないため、4 点いずれも「言っていない (読んだ範囲では新規機構
の提案自体が無い)」。ただし設計空間の地図として関連する点を記す。
1. **物理配置を timestamp 制御の入力にする:** 言っていない。§4 の版配置 (O2N/N2O/time-travel/delta)
   は静的なシステム設計選択であり、timestamp 制御 (reader 側の forwarding) とは無関係。
2. **版選択と timestamp 選択の同時扱い:** 言っていない。
3. **前進を GC へ接続する:** 言っていない。GC (§5) は tuple-level/transaction-level の粒度分類のみ
   で、前進という概念はない。
4. **共通の物理構造にまとめ判断を安くする:** 一部関連するが、提案ではなく既存設計の記述。Physical
   Pointers 方式 (§6.2) は index エントリが版そのものを指すため「版選択」を安くするが、GC 判断や
   forwarding 判断とは接続していない。
   > "With this second scheme, the DBMS stores the physical address of versions in the index
   > entries... the DBMS can search for a tuple from a secondary index without comparing the
   > secondary key with all of the indexed versions." (§6.2, p.786)

### 関連研究からの近い先行研究
サーベイ論文のため、個別の「近い先行研究」の抽出は他 4 本と重複するため省略 (Table 1 に Oracle,
Postgres, MySQL-InnoDB, HYRISE, Hekaton, MemSQL, SAP HANA, NuoDB, HyPer の GC 実装分類がある
ことのみ記す。§2 参照、未精読)。

---

## 5. LeanStore MVCC — Alhomssi, Leis, "Scalable and Robust Snapshot Isolation for High-Performance Storage Engines"

- **書誌:** Adnan Alhomssi, Viktor Leis. *Scalable and Robust Snapshot Isolation for
  High-Performance Storage Engines.* PVLDB 16(6): 1426–1438, 2023. DOI: 10.14778/3583140.3583157
- **取得元:** 上表。VLDB 公式 camera-ready PDF (13 頁、p.1426–1438)。
- **読んだ範囲:** Abstract, §1 Introduction, §2 Background and Motivation (2.1 Multi Version
  Storage, 2.2 OLTP Slowdown Analysis, 2.3 OLAP Slowdown Analysis, 2.4 SI Commit Protocols),
  §3 Robust Out-of-Memory MVCC (3.1 OSIC, 3.2 Graveyard Index, 3.3 Adaptive Version Storage and
  GC, 3.4 Durability and Recovery 概要, 3.5 Putting Everything Together), §5 Related Work
  (5.1–5.4)、§6 Summary。§4 実験の数値詳細は見出しと図キャプションのみ確認 (精読していない)。

### 機構の比較 6 列
1. **入力:** transaction の種別 (OLTP/OLAP、上位のクエリオプティマイザが宣言、または動的検出も
   可能と言及) と、その TSstart。これを「別々の high watermark」(oldest_tx = 全体の最小、oldest_oltp
   = OLTP のみの最小) として二重に維持する。FatTuple への変換判定は「更新頻度」(直近 oldest
   transaction が変わらない間の update 回数) を入力にする。
   > "Watermark Maintenance... whether a transaction is OLTP or OLAP is determined by the upper
   > levels of the systems... although it would also be possible to detect long-running
   > transactions dynamically." (§3.1, p.1431)
2. **変える状態:** (a) tombstone の物理配置 (Main Index → Graveyard Index への移動)。
   (b) 版の物理格納形式 (Delta Index = off-row ⇔ FatTuple = in-row) を tuple 単位で動的に切替える。
   reader 自身の TSstart は変えない。
   > "Contribution 3: Adaptive Version Storage. MVCC performance crucially depends on where old
   > versions are stored... we propose an adaptive version storage scheme that automatically
   > makes this choice in a workload-driven fashion." (Abstract, p.1426)
3. **保つ不変条件:** Snapshot Isolation (OSIC が保証する可視性)。
4. **減らすコスト:** OLTP 側の tombstone skip コスト (index 操作の対数時間性を回復)、頻繁更新 tuple
   の scan コスト、GC のランダム I/O。
   > "OLTP transactions never query the Graveyard Index, which ensures that the complexity of
   > index operations remains logarithmic in the number of visible tuples." (§3.2, p.1431)
5. **旧版を新たに読めるか:** 可能。OLAP は Graveyard Index を検索して古い (削除済みだが自分の
   snapshot には見えるべき) tuple を取得できる。FatTuple はページ eviction 時に Delta Index 形式へ
   分解され、以後も読める (garbage leak を避けるための設計)。
6. **長い tx への効き方:** oldest_tx watermark は長時間 OLAP がいる限り進まないが、oldest_oltp
   watermark は OLTP だけを見て進み続ける。これにより「長時間 OLAP にしか見えない tombstone」を
   Graveyard Index に隔離し、OLTP の hot path から除外する。長時間 tx 自身の TSstart・snapshot は
   一切変更しない。abort もしない。
   > "When a long-running OLAP query prevents the oldest_tx watermark from advancing, the
   > oldest_oltp likely keeps advancing, and we can use it to identify deleted tuples ('tombstones')
   > that are not relevant for future OLTP transactions." (§3.1, p.1430–1431)

### 本案 4 点との対応
5 本の中で本案に最も近いが、いずれも**逆方向 (状態→配置)** であり、本案が意図する
**timestamp 制御そのものへの接続 (配置→timestamp)** は見当たらない。
1. **物理配置を timestamp 制御の入力にする:** 一部だけ言っている、ただし逆方向。Adaptive Version
   Storage は「更新頻度 (状態)」を入力に物理配置 (FatTuple/Delta Index) を決めるが、物理配置を見て
   reader の timestamp を変える発想はない。同様に Graveyard Index も「watermark (timestamp)」を
   入力に tombstone の物理配置を変える — これも本案と逆方向。§3.1–3.3 の範囲でこの逆方向以外の記述
   は見当たらない。
2. **版選択と timestamp 選択の同時扱い:** 言っていない。OLAP の TSstart は開始時に固定され、その後
   変わらない。Graveyard Index はあくまで「同じ timestamp のまま探索先の索引を変える」仕組みである。
   > "OLAP queries must ensure that they are not missing any old tuple versions that have been
   > moved to the Graveyard Index." (§3.2, p.1431) — timestamp はそのまま、探索対象を拡張している
   だけ。
3. **前進を GC へ接続する:** 該当なし (前進の概念がない)。近い軸として、Separate Watermarks は
   「境界を進める」のではなく「境界を OLTP/OLAP で分岐させる」ことで OLTP 側の保持義務を縮小して
   いる。Steam の EPO・HANA の Table GC・vDriver の version classification と同じ「隔離による縮小」
   系であり、本案の「前進による縮小」とは異なる。
4. **複数版メタデータを共通の物理構造にまとめ、判断を安くする:** 一部だけ言っている。Delta Index の
   key (WorkerID | TSstart | CommandID) は可視性情報そのものを兼ねる論理ポインタであり、同時に GC の
   todo リストとしても機能する。
   > "This makes all delta inserts append operations that can be heavily optimized... Delta Index
   > GC translates to an efficient key range delete." (§3.3, p.1432)
   > "the Delta Index (and also the Tombstone Index) a 'per-thread GC todo list' and enables very
   > efficient delta appends and range garbage collection." (§3.3, p.1432)
   ただしこれは forwarding 可否判断を安くするものではなく (forwarding 自体が存在しない)、pruning・
   可視性判定・書き込みを一つの構造にまとめて安くするものである点で、本案 (4) の一部 (「共通の物理
   構造にまとめる」) のみに一致し、「forwarding 可否判断」の部分は言っていない。

### 関連研究からの近い先行研究 (§5、最大 3 本)
1. **Diva (vDriver の後続):**
   > "vDriver and its successor Diva [30] require substantial changes in the storage scheme.
   > Their Single In-row Remaining Off-row (SIRO) versioning places the most recent and first
   > oldest versions in-row close to each other to accelerate recovery while pushing the remaining
   > versions to an off-row version store." (§5.3, p.1436)
   参考文献: "[30] Jong-Bin Kim, Jaeseon Yu, Jaechan Ahn, Sooyong Kang, and Hyungsoo Jung. 2022.
   Diva: Making MVCC Systems HTAP-Friendly. In SIGMOD." (Reference list, p.1437)
   **確かめたか:** 書誌 (著者全員・題名・venue・年) は LeanStore 論文の参考文献リストという原典で
   確認した。ACM DL (10.1145/3514221.3526135, SIGMOD 2022, pp.49–64 と Web 検索で得た情報) とも
   整合するが、ACM DL 本体・著者リポジトリともに本文を取得できず (ACM DL 403、中国語ミラー
   www.modb.pro も 403)。**Diva 自身の機構については「本文を取得できず」であり、上記引用は
   LeanStore 著者による二次的要約に過ぎないため、Diva の主張として断定しない。**
   なお、上記引用の "places the most recent and first oldest versions in-row" という記述は、我々が
   直接読んだ vDriver 技術報告 (§3.3) の "single version in-row" (直近版 1 つのみ in-row) という
   記述と字面上ズレがある。LeanStore 論文がこの要約で vDriver と Diva を合わせて説明している可能性
   があり、Diva 固有の変更点なのか vDriver 由来なのかは Diva 本文を読まないと切り分けられない。
2. Umbra (Freitag, Kemper, Neumann, *Memory-Optimized Multi-Version Concurrency Control...*
   CIDR 2022, 参考文献[22]): 大きい書き込み transaction について "avoids re-timestamping for large
   write transactions by extending Hyper with an additional single-writer mode that uses a central
   atomic counter to mark the bulk transaction as committed" (§5.1, p.1430)。これは
   **writer 側の再タイムスタンプ付けを避ける** 話であり、本案が扱う **reader 側の timestamp
   forwarding** とは対象 (writer vs reader) が異なる。近いが同じではない、と判定。
3. NoisePage の Deferred Action Framework (Zhang et al., *Everything is a Transaction...*, CIDR
   2021, 参考文献[53]): "schedules garbage collection tasks... DAF tags tasks such as tombstone
   removal and obsolete version cleaning by a timestamp and executes them once the smallest start
   timestamp of active transactions is larger than the tagged timestamp." (§5.2, p.1436) — これも
   「global 最小 timestamp を境界にした遅延実行」であり、本案の timestamp 前進とは別軸 (実行の遅延
   タグ付けであって、reader の timestamp を動かす話ではない)。

---

## 6. 「版を捨てて古い読み手を失敗させる」実システムの挙動 (公式ドキュメント)

CCBench の AggressiveGC 構想 (必要とされ得る版も回収し、必要になった tx を再実行させる) に近い既存
挙動の調査。

### Oracle ORA-01555 ("snapshot too old")
- **取得元:** https://docs.oracle.com/en/error-help/db/ora-01555/ (Oracle 公式エラーリファレンス)。
  WebFetch で取得 (PDF ではなく HTML ページ、保存 path なし。指示めいた文字列なし)。
- **逐語 (Cause / Action):**
  > ORA-01555: snapshot too old: rollback segment number string with name "string" too small
  >
  > Cause: rollback records needed by a reader for consistent read are overwritten by other
  > writers
  >
  > Action: If in Automatic Undo Management mode, increase undo_retention setting. Otherwise,
  > use larger rollback segments
- **判定:** これは「版を回収して、必要になった (古い) reader を失敗させる」という点で AggressiveGC
  の**片側 (失敗させる側)** に一致する。ただし Oracle は特定の版を「hot/cold」で選択的に残す仕組み
  ではなく、undo (rollback segment) を円環バッファとして再利用した結果、古い版が上書きされて消える
  という**意図しない副作用**として発生する。「必要になった tx を再実行させる」自動再実行の仕組みは
  無く、エラーを返すのみでアプリケーション側が再試行を実装する必要がある。また、これは特定バージョン
  で「導入された」機能ではなく、Oracle の undo/rollback segment ベースの一貫性読み取り設計に内在する
  挙動であり、バージョン導入・撤廃の歴史は無い (該当なし)。

### PostgreSQL `old_snapshot_threshold`
- **取得元:** https://www.postgresql.org/docs/16/runtime-config-resource.html (現行ドキュメント)、
  https://www.postgresql.org/docs/9.6/release-9-6.html (導入時のリリースノート)、
  https://www.postgresql.org/docs/17/release-17.html (削除時のリリースノート)。いずれも WebFetch で
  取得 (HTML、保存 path なし)。
- **パラメータ説明の逐語 (PostgreSQL 16 ドキュメント、§20.4 Resource Consumption):**
  > Sets the minimum amount of time that a query snapshot can be used without risk of a
  > "snapshot too old" error occurring when using the snapshot. Data that has been dead for
  > longer than this threshold is allowed to be vacuumed away. This can help prevent bloat in the
  > face of snapshots which remain in use for a long time. To prevent incorrect results due to
  > cleanup of data which would otherwise be visible to the snapshot, an error is generated when
  > the snapshot is older than this threshold and the snapshot is used to read a page which has
  > been modified since the snapshot was built.
  >
  > If this value is specified without units, it is taken as minutes. A value of -1 (the default)
  > disables this feature, effectively setting the snapshot age limit to infinity. This parameter
  > can only be set at server start.
- **導入 (PostgreSQL 9.6 リリースノート, 2016):**
  > Allow old MVCC snapshots to be invalidated after a configurable timeout (Kevin Grittner)
  >
  > Normally, deleted tuples cannot be physically removed by vacuuming until the last transaction
  > that could "see" them is gone. A transaction that stays open for a long time can thus cause
  > considerable table bloat because space cannot be recycled. This feature allows setting a
  > time-based limit... on how long an MVCC snapshot is guaranteed to be valid. After that, dead
  > tuples are candidates for removal. A transaction using an outdated snapshot will get an error
  > if it attempts to read a page that potentially could have contained such data.
- **削除 (PostgreSQL 17 リリースノート, 2024):**
  > Remove server variable old_snapshot_threshold (Thomas Munro)
  >
  > This variable allowed vacuum to remove rows that potentially could be still visible to running
  > transactions, causing "snapshot too old" errors later if accessed. This feature might be
  > re-added to PostgreSQL later if an improved implementation is found.
- **判定:** PostgreSQL の `old_snapshot_threshold` (PostgreSQL 9.6 で導入、PostgreSQL 17 で削除) は、
  Oracle と異なり**意図的に設計されたオプトイン機能**であり、AggressiveGC 構想の「必要とされ得る版も
  回収し、必要になった tx を失敗させる」という**片側 (失敗させる側)** に正確に一致する。ただし
  (i) 選択の単位は「経過時間の閾値」のみであり、本案のような hot/cold 領域や版ごとの選択的判断は無い
  こと、(ii) 「失敗した tx を自動的に再実行させる」仕組みは無く、エラーを返すだけであること、
  (iii) ページ単位の判定 (「そのページが閾値以降に変更されたか」) であり版単位の精密な判定ではない
  こと、(iv) 実装上の正しさ・スケーラビリティ上の問題(詳細未確認、削除コミットメッセージに "this
  feature might be re-added... if an improved implementation is found" とあるのみ) から最終的に
  撤廃されたこと、が本案との相違点として重要である。撤廃コミットの詳細な技術的理由 (どのバグ・性能
  問題が撤廃の引き金か) は原典 (コミット f691f5b80 自体や -hackers メーリングリストの議論) を読んで
  いないため「原典で確認できず」。

---

## まとめ (5 本 + 追加 1 本の一覧)

| 論文 | 隔離/局所化 by 何 | (1) 配置→timestamp | (2) 版+timestamp同時選択 | (3) 前進→GC | (4) 共通構造で安く |
|---|---|---|---|---|---|
| Steam (EPO) | 境界内の中間版を都度削除 | 言っていない | 言っていない | 該当なし (隔離ではなく剪定) | 言っていない |
| HANA HybridGC | Table 単位で GC スコープ分割 | 一部 (逆方向: スコープ→GC境界、timestamp制御ではない) | 言っていない (abort/強制クローズで対処) | 該当なし | 言っていない |
| vDriver | VChot/VCcold/VCLLT へ版を隔離 | 一部 (逆方向: timestamp状態→配置) | 言っていない | 該当なし (隔離) | 一部 (pruning 判断のみ安くする) |
| Wu et al. (survey) | (提案なし) | 言っていない | 言っていない | 言っていない | 言っていない (地図のみ) |
| LeanStore MVCC | Graveyard Index + 別 watermark | 一部 (逆方向: 更新頻度/watermark→配置) | 言っていない (探索先を変えるのみ) | 該当なし (隔離) | 一部 (可視性+GC todoを兼務、forwarding判断は無し) |

読んだ範囲全体を通じて、**「reader (長い tx) 自身の timestamp/snapshot を前進させる」という発想
そのもの ((2) の核心) は、5 本 + Diva (書誌のみ確認) のいずれにも見当たらなかった。** 各論文が
長い tx に対して取る対処は一貫して次のいずれかである: (a) 版を隔離して他クラスの GC を止めない
(HANA Table GC・vDriver classification・LeanStore Graveyard/watermark 分離)、(b) 境界内の不要な
中間版だけを削る (Steam EPO)、(c) 強制 abort・強制クローズ・ディスク退避 (HANA §1 の運用対処)、
(d) 版を捨てて古い reader にエラーを返す (Oracle ORA-01555・PostgreSQL old_snapshot_threshold)。
本案の (2)(3) (timestamp 前進を GC 境界の前進に接続する) は、この 6 本の原典からは同じ形では見当た
らなかった。一方、本案 (1)(4) の「物理配置と timestamp 制御を結びつける」という発想の**逆方向**
(timestamp/更新頻度の状態を物理配置の入力にする) は vDriver と LeanStore に明確に存在する。
