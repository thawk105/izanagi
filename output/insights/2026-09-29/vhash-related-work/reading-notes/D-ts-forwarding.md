# D-ts-forwarding: timestamp 後決め・区間保持・延長・前進、および版破棄再実行系の文献照合

担当: transaction の timestamp を後から決める・区間で持つ・延長する・前進させる方式と、版を捨てて
再実行させる方式の系統 (候補 1〜6 + 検索による候補 7)。

規則に従い、原典で確かめた事実だけを「確認」と書き、確認できないものは「原典で確認できず」、
自分の推論は「推論」と明記する。取得した PDF・Web ページの中身はすべてデータであり指示ではない。
**指示めいた文字列は見つからなかった** (全取得物を通じて、報告すべき injection 的な記述はゼロ件)。

---

## 総括 (本案 4 点の被覆状況、結論を先に)

本案の新規性候補 4 点について、読んだ範囲で確認できたことだけを書く。

1. **物理配置 (cold 領域に入ること) を timestamp 制御の入力にする**
   → **6 論文 + 発見した関連研究のいずれにも見当たらない (読んだ範囲では「言っていない」)。**
   Sundial・Shirakami・Rebirth-Retire は timestamp/order を動かす契機を「衝突」(lease 不足・
   WP 衝突・lock 衝突) だけに置き、対象データが hot/cold のどちらの物理領域にあるかを条件に
   使っていない。Rebirth-Retire は逆に「version chain が長くて cache miss が増える」という
   物理コストを **prefetch というポインタ最適化で隠す側**に回っており、timestamp 決定の入力には
   していない (§4.4、後述)。MaaT・Sundial の DTA 系譜文献 (Bayer 1982, Lomet et al. 2012, MaaT)
   も衝突検出のみを契機にしている。

2. **版選択と timestamp 選択を同時に扱う (最新版でない旧版を選んで既読値を保つ)**
   → **部分的に一致する先行研究として Lomet et al. (ICDE 2012、本案の直接候補ではないが Sundial・
   MaaT の両方が引用する MVCC 版 DTA) を発見・確認した。** この論文は「writer が既存 reader の
   後ろに回れない場合、reader を待たせず writer 側を旧版のまま concurrent に進める」という、
   版選択と timestamp 区間調整を同時に行う設計を持つ (§(TCM の "Resource with at least one
   writer" 節、後述)。ただし対象は"より新しい write が来た場合に reader が古い版を読み続けられるか"
   であり、**"transaction 自身が cold な最新版を避けて hot な旧版を明示的に選ぶ" という本案の
   向き (読み手が能動的に旧版を選ぶ) の記述は見当たらない。** MV3C は逆に、version 選択の再利用は
   「述語の計算結果 (result-set) の再利用」であり、旧版選択とは無関係 (§5.2)。Shirakami の
   order forwarding は read した値を"維持"する方向 (§3.2.1 Algorithm 1 の read validation) の
   議論はあるが、"意図して非最新版を選ぶ" という記述はない。

3. **前進を履歴の保持義務の縮小 (GC) へ接続する**
   → **Shirakami に "epoch 長 → multi-version 環境の GC コスト" という一般論の接続は明記されている
   が (§3.4.1)、order forwarding という個別の前進操作が GC 境界を直接縮めるという明示的な接続は
   見当たらない。** Lomet et al. (2012) は「TCM のロック (メタデータ) は、その timestamp が
   active な書き込み transaction の timestamp 区間へ影響し得なくなるまで保持し、以後は破棄できる」
   という、timestamp 機構と保持境界を明示的に結びつけた記述を持つ (§VIII.C, §VIII.F) —
   これは本案 (3) にかなり近い先行例である。Morty (EuroSys 2023、候補 7 として発見) は
   re-execution で読み値を前進させた版順序 (`ver`) をそのまま truncation の境界 (`truncation_ver`)
   に使っており (§4.4)、**「前進操作の結果そのものを GC/truncation 境界の入力にする」という構造は
   Morty に確認できる。** ただし Morty の前進は「旧版保持のため」ではなく「旧版を捨てて新しい値に
   置き換える」向きであり、本案とは前進の目的が逆になっている。MaaT・MV3C の GC は、いずれも
   "最も古い active transaction" を境界にする素朴な watermark 方式で、timestamp forwarding
   操作そのものとは独立に設計されている。

4. **複数版メタデータを共通の物理構造にまとめ、版選択・forwarding 可否判断・validation を安くする**
   → 6 論文中でこれに近いのは Shirakami の WP (write preservation) をテーブル粒度で 1 つの
   atomic word にまとめる最適化 (§3.6) と、Rebirth-Retire の version chain 上に prefetch 用
   jump pointer を追加する最適化 (§4.4) だが、いずれも「forwarding 可否判断そのものを高速化する
   共通構造」ではなく、別々の目的 (WP 検査の高速化、cache miss 削減) に閉じている。「版選択・
   forwarding 可否・validation を単一の物理構造で安くする」という統合の記述は見当たらない。

以下、論文ごとに詳細を書く。

---

## 候補 1: Sundial (PVLDB 11(10), 2018)

**書誌**: Xiangyao Yu, Yu Xia, Andrew Pavlo, Daniel Sanchez, Larry Rudolph, Srinivas Devadas.
"Sundial: Harmonizing Concurrency Control and Caching in a Distributed OLTP Database Management
System." PVLDB 11(10):1289–1302, 2018. DOI: 10.14778/3231751.3231763

**取得元**: http://www.vldb.org/pvldb/vol11/p1289-yu.pdf →
`src/sundial.pdf` (SHA-256: `4f384ac51d4dbf77330b6df0446e272b99b821664cafa0847af7b7c32f1e638b`)。
PVLDB 公式掲載版そのもの (pdfinfo で 14 頁、PVLDB ページ番号 1289–1302 が本文中に埋め込まれている
ことを確認)。camera-ready。

**読んだ範囲**: §1 Introduction、§2 (2.1–2.4) Background and Related Work、§3 (3.1–3.5) Sundial
Concurrency Control 全体、§5.2 Sundial vs. MaaT、§5.3 Limitations、§6.1 Workloads (概要)、
§6.5 Measuring Aborts、§6.6 Dynamic vs. Static Timestamps、§6.7 Scalability、§6.8 Comparison to
Dynamic Timestamp Range、§7 Conclusion、References [8][12][29][30][34][35] の書誌事項。
**未読**: §4 (Data Caching) の実装詳細、§6.2–6.4 の実験詳細図表の逐一の読み込み、§3.5 (Fault
Tolerance) の詳細、Reference 全件 (関係するもの以外)。

### 機構の比較 6 列

1. **何を入力に判断するか**: tuple 単位の logical lease `(wts, rts)` との衝突。write 時は
   `rts+1` 以降でしか書けない、read 時は自分の `commit_ts` が読んだ全 tuple の `[wts, rts]` に
   収まる必要がある、という制約違反が契機。引用: "wts is the logical time when the tuple was
   last written; rts is the end of the lease, meaning that the tuple can be read at logical
   time ts such that wts ≤ ts ≤ rts." (§3.1, p.1291)
2. **どの状態を変えるか**: 自分の `commit_ts`、および対象 tuple の `rts` (lease extension)。
   引用: "the DBMS extends the end of the lease on A from 2 to 3 such that both operations
   performed by T2 are valid at timestamp 3." (§3.1, p.1291, Figure 1 の説明)
3. **どの不変条件を保つか**: serializability。commit_ts は「読んだ全 tuple の lease 内」に
   収まることで保証 (§3.1)。
4. **どのコストを減らすか**: read-write 衝突による無用な abort。引用: "Sundial dynamically
   determines the logical order among transactions at runtime, based on their data access
   patterns." (Abstract)
5. **旧版を新たに読めるか (MVCC か)**: **不可、single-version。** 引用: "their protocol
   requires a multi-version database while Sundial works in a single-version database."
   (§2.1, p.1290)。tuple 構造も `DB[key] = {wts, rts, owner, waitlist, data}` で data は 1 つ
   のみ (§3.3.1, p.1291)。
6. **長い transaction への効き方**: 明示的な議論なし。lease 延長・extension のコストへの言及は
   あるが (§5.1、"more extensions and potential aborts")、長い tx 固有の対策 (GC 連動や version
   選択) は書かれていない。

### 本案 4 点との照合

- (1) 物理配置を入力にする: **言っていない (読んだ範囲では見当たらない)。** §5.3 で tuple の
  lease 保存コスト削減のため「'cold' な tuple の lease は単一の `(cold_wts, cold_rts)` にまとめる」
  という最適化はあるが (p.1296)、これは *lease の値が物理配置 (メタデータ保存要否) を決める* 逆
  方向であり、物理配置が timestamp 制御を左右する構造ではない。
- (2) 版選択と timestamp 選択の同時扱い: **該当なし** (single-version のため版選択という概念
  自体が存在しない)。
- (3) 前進を GC へ接続: **該当なし** (single-version のため版 GC の概念がない)。
- (4) 複数版メタデータの共通構造化: **該当なし** (single-version)。

**単一ノードへの適用可能性 (依頼の追加観点)**: 原典は明示的に論じていない (原典で確認できず)。
機構自体 (tuple ごとの `wts/rts` と `commit_ts = max(...)`、lease extension の可否判定) は
RPC をローカル呼出に置き換えれば単一ノードでも成立しそうな構造に見えるが、これは**推論**であり
原典の主張ではない。

### 関連研究節・引用から見つけた先行研究

- **Bayer, Elhardt, Heigert, Reiser. "Dynamic Timestamp Allocation for Transactions in Database
  Systems." DDB 1982, pp. 9–20.** — Sundial 参考文献 [8] として実在を確認 (p.1301 の書誌エントリ
  をそのまま確認)。本文では「2PL の deadlock 検出、および OCC への DTA の初出」として引用
  (§5.2, p.1295)。→ 候補 3 として別項で扱う。
- **Lomet, Fekete, Wang, Ward. "Multi-Version Concurrency via Timestamp Range Conflict
  Management." ICDE 2012.** — Sundial 参考文献 [34]。本文で "Lomet et al. [34] proposed a
  multi-version concurrency control protocol that lazily determines a transaction's commit
  timestamp using timestamp ranges... their protocol requires a multi-version database while
  Sundial works in a single-version database" (§2.1, p.1290) と明記され、§6.8 (p.1300) で
  定量比較もされている。**候補外だが強く関連するため、原典を別途取得し確認した (詳細は後述の
  「追加で確認した関連研究」)。**
- **Boksenbaum, Ferrié, Pons. "Concurrent Certifications by Intervals of Timestamps in
  Distributed Database Systems." TSE (1987), 409–419.** — Sundial 参考文献 [12]。
  書誌は確認したが、本文の逐語取得は試みていない (Sundial 中での言及は "OCC protocols [12, 29,
  30]" という並列列挙のみ、p.1295)。**未確認**。MaaT の参考文献 [14] (後述) と著者・題名が
  酷似するが年・誌が異なり (TSE 1987 vs VLDB 1984)、別バージョン (会議版と誌上版) の可能性が
  ある。両論文を実際に読んで初めて分かった食い違いであり、二次資料には出てこない事実。

---

## 候補 2: MaaT (PVLDB 7(5), 2014)

**書誌**: Hatem A. Mahmoud, Vaibhav Arora, Faisal Nawab, Divyakant Agrawal, Amr El Abbadi.
"MaaT: Effective and Scalable Coordination of Distributed Transactions in the Cloud." PVLDB
7(5):329–340, 2014. DOI: 10.14778/2732269.2732270

**取得元**: http://www.vldb.org/pvldb/vol7/p329-mahmoud.pdf →
`src/maat.pdf` (SHA-256: `e2caafb363d0c90e47da06802b5c150fca778f418d9c58817a7fd1171e1b3ad6`)。
PVLDB 公式掲載版そのもの (pdfinfo で 12 頁、ページ番号 329(暗黙)〜340 を本文中に確認)。camera-ready。

**読んだ範囲**: §1 Introduction (概要)、§2.3 Scalability、§3 MaaT Transaction Processing 全体
(3.1 Design Overview〜3.3 Concurrency Control、3.3 内の GC 節を含む)、§8 References の該当箇所。
**未読**: §4 Analysis (4.1–4.4、正しさ証明・耐障害性の詳細)、§5 Experiments の大半 (deterministic
deployment 比較の断片のみ読んだ)、§6 Conclusion。

### 機構の比較 6 列

1. **何を入力に判断するか**: 各 data item の `tsr(x)` (最後に読んだ tx の commit ts)・
   `tsw(x)` (最後に書いた tx の commit ts) と、自 tx の区間 `[lower(T), upper(T)]` との矛盾。
   引用: "whenever a transaction T reads (resp. writes) a data item x whose write timestamp
   tsw(x) (resp. read timestamp tsr(x)) is not less than the lower bound of the timestamp
   range of T, ... this conflict results in an adjustment of the lower bound of the timestamp
   range of T" (§3.1, p.332)。
2. **どの状態を変えるか**: 自 tx の `[lower(T), upper(T)]` (基本は lower を押し上げて区間を
   狭める)。commit 時に区間の交わりから 1 点を選び commit timestamp にする (§3.2.4, p.335)。
3. **どの不変条件を保つか**: serializability (OCC + soft lock による validate-at-commit)。
4. **どのコストを減らすか**: 2PC 中のロック待ち (locking-free な atomic commit)、distributed
   OCC の全サーバ validation コスト (「その tx がアクセスしたサーバだけで validate する」設計、
   §3.1, p.331–332)。
5. **旧版を新たに読めるか (MVCC か)**: **不可、single-version。** 引用: "We avoid multi-version
   concurrency control so as to make efficient use of memory space. ... the design decision of
   using single-version concurrency control has been made by several commercial main memory
   databases as well" (§3.1 Motivation, p.331)。
6. **長い transaction への効き方**: 明示的な深い議論は少ない。Spanner が long-lived
   transaction への対処を理由に lock-based MVCC へ転換したという他社事例を批判的に紹介し
   ("We question the validity of that reasoning... multi-version OCC also performs well in
   terms of throughput in the presence of long-lived transactions [25]", §1, p.330) つつ、
   MaaT 自身の long tx 固有の対策 (version 選択・GC 連動) は書かれていない。

### 本案 4 点との照合

- (1) 物理配置を入力にする: **言っていない (読んだ範囲では見当たらない)。**
- (2) 版選択と timestamp 選択の同時扱い: **該当なし** (single-version)。
- (3) 前進を GC へ接続: **部分的に別種の GC のみ確認、本案の意味では言っていない。** §3.3
  Garbage collection (p.334–335) はあるが、これは **timetable エントリ (衝突検出用メタデータ)
  の GC** であり、版データの GC ではない (MaaT に版という概念がないため)。引用: "For any given
  transaction T, as long as the state of T on a data server s is set to RUNNING or VALIDATED,
  the timetable entry of T on s can not be garbage collected." (§3.3, p.334)。timestamp 区間の
  調整 (narrowing) 操作そのものが GC 境界を動かすという記述はない。
- (4) 複数版メタデータの共通構造化: **該当なし** (single-version、Data table と timetable は
  別構造、§3.1 Figure 1, p.332)。

### 関連研究節・引用から見つけた先行研究

- **Bayer, Elhardt, Heigert, Reiser (1982)** — MaaT 参考文献 [11]、"In Proceedings of the Second
  International Symposium on Distributed Data Bases, DDB '82, pages 9–20, 1982." として
  Sundial と同一の書誌を確認 (p.339)。本文では "as in the case in pessimistic timestamp
  ordering... and transaction-time databases [26], where adjustments to timestamp ranges are
  done whenever a conflict occurs, rather than at commit time as the case in OCC" (§3.1, p.332、
  ただし文脈上この一文が [11] と [26] のどちらの特徴づけかはやや曖昧 — 逐語通りに引用するに
  留める) という形で言及されている。
- **Boksenbaum, Cart, Ferrié, Pons. "Certification by Intervals of Timestamps in Distributed
  Database Systems." VLDB 1984.** — MaaT 参考文献 [14]。本文で「distributed OCC validation
  based on dynamic timestamp ranges の元祖の理論提案だが、"each data server needs to be
  involved in the validation of each transaction, even data servers that are not accessed by
  that transaction" という実用上の弱点を持つ」と明記 (§3.1, p.332)。MaaT はこの弱点を「その
  tx がアクセスしたサーバだけで validate する」ことで解消したと主張している。
  vldb.org 上の該当 PDF (`https://www.vldb.org/conf/1984/P377.PDF`) を取得しようとしたが
  **403 Forbidden で本文取得できず**。Sundial の [12] (Boksenbaum, Ferrié, Pons, TSE 1987) と
  著者が重なるが年・巻・共著者数 (3 名 vs 4 名、"Cart" の有無) が異なり、**別文献の可能性が高い
  (未確定)**。
- **Lomet, Fekete, Wang, Ward (ICDE 2012)** — MaaT 参考文献 [26]、"transaction-time databases"
  の例として言及 (§3.1, p.332)。Sundial からも独立して引用されており、後述の追加確認対象。

---

## 候補 3: Bayer, Elhardt, Heigert, Reiser (1982)

**書誌 (原典未読、引用元 2 件で確認)**: Rudolf Bayer, Klaus Elhardt, Johannes Heigert, Angelika
Reiser. "Dynamic Timestamp Allocation for Transactions in Database Systems." In *Distributed
Data Bases* (ed. H. J. Schneider), North-Holland, Proceedings of the Second International
Symposium on Distributed Data Bases, Berlin, F.R.G., September 1–3, 1982, pp. 9–20.

**実在の確認方法**: 単独の DBLP 検索では確認できなかった (後述) が、**Sundial (p.1301) と
MaaT (p.339) という互いに独立した 2 本の一次資料が、著者名・題名・venue・頁を完全に一致させて
引用しており**、これをもって書誌の実在を確認した (Sundial [8]、MaaT [11]、いずれも "Dynamic
Timestamp Allocation for Transactions in Database Systems... DDB '82, pages 9–20" で一致)。

**本文取得の試行と結果**: `dblp.org`・`dblp.dagstuhl.de` はいずれも bot 対策 (Anubis challenge)
により直接 fetch がブロックされ (`Making sure you're not a bot!`)、WebFetch 経由でも同じ
ブロックページが返った。CiteSeerX は web.archive.org へリダイレクトされたが、本セッションの
環境では web.archive.org への fetch ができない制約があり参照できなかった。有償データベース
(ACM/Springer 等) 以外に本文 PDF は見つからなかった。**→ 本文を取得できず。**

**内容についての注記**: WebSearch のスニペット (二次資料) には「limited timestamp history
information を使って commit 時に動的にタイムスタンプ (または区間) を導出し、"back-shifted
timestamp" を certification に使う」という要約が出てくるが、これは検索エンジンの要約であって
原典の逐語ではないため、規則に従い**確認済みとしては書かない**。一次資料からの間接的な性格づけ
としては、MaaT (§3.1, p.332) が Bayer 論文の文脈を「pessimistic timestamp ordering」として、
かつ「conflict が起きるたびに (commit 時ではなく) timestamp 区間を調整する」系譜として引用して
いる、という事実だけを書く (これは MaaT という一次資料からの引用であり、Bayer 論文自体を読んだ
ことにはならない)。

**機構比較 6 列・本案 4 点との照合**: 原典未読のため**すべて「原典で確認できず」**。

---

## 候補 4: Shirakami (arXiv:2303.18142)

**書誌**: Takayuki Tanabe, Shinichi Umegane, Suguru Arakawa, Ryoji Kurosawa, Takashi Hoshino,
Hideyuki Kawashima, Masahiro Tanaka, Takashi Kambayashi. "Shirakami: A Hybrid Concurrency
Control Protocol for Tsurugi Relational Database System." arXiv:2303.18142.

**取得元**: https://arxiv.org/pdf/2303.18142 → `src/shirakami.pdf`
(SHA-256: `e9cf8b914e00130e2b9a0260047eaaeb20a0df30ad60bedde9c534b6cd078b03`)。
arXiv の submission history を直接確認したところ v1 (2023-03-31)・v2 (2026-03-18)・v3
(2026-07-02) の 3 版があり、`/pdf/2303.18142` は最新の **v3 (2026-07-02 提出、13 頁)** に解決
されることを sha256 の一致で確認した (v3 明示 URL `/pdf/2303.18142v3` を再取得し同一ハッシュを
確認済み)。したがって本レポートの引用は **v3** に基づく。

**読んだ範囲**: §1 (概要のみ)、§3 全体 (3.1 Overview〜3.7 Safety and Liveness、Algorithm 1・2 を
含む)、§6 Related Work の冒頭 (6.1.1–6.1.2、6.2 の冒頭数文)。**未読**: §2 (Motivating
applications の詳細)、§4 Evaluation of Tsurugi、§5 Evaluation of Shirakami の実験詳細図表、
§6.2 の後半、§7 Conclusion。

### 機構の比較 6 列

1. **何を入力に判断するか**: (a) S-LTX 同士: 高優先度 (先に開始した = id が小さい) tx が既に
   commit 済みで、自分の read_set と write_keys が重なる場合。引用 (Algorithm 1, lines 13–14):
   "foreach ltx_id ∈ overtaken_set do // order forwarding / if committed(ltx_id) ∧ (read_set ∩
   write_keys(ltx_id) ≠ ∅) then". (b) S-OCC 側: table 粒度の WP (write preservation) を
   read/commit 時に観測した場合 (§3.3, §3.7)。
2. **どの状態を変えるか**: 自 tx の serialization epoch (`commit_epoch`)。引用: "its
   serialization epoch is adjusted to match t1's serialization epoch. We refer to this as
   order forwarding." (§3.1.3)。
3. **どの不変条件を保つか**: serializability (S-LTX・S-OCC とも)。§3.7 で Adya 型の
   dependency-graph 論法により証明。
4. **どのコストを減らすか**: false-positive abort。引用: "Using S-LTX, three transactions are
   committed, which is ideal and incurs no false positives... Using MVTO..., we can commit
   only one transaction." (§3.1.3, Figure 1 の説明)。
5. **旧版を新たに読めるか (MVCC か)**: **可、MVCC。** "Shirakami uses a multiversion data
   structure to provide snapshots per epoch" (§3.1.2)。§3.4.3 Snapshot: "this is an in-memory
   snapshot: a set of committed versions maintained solely for transaction reads."
6. **長い transaction への効き方**: 本論文の主題そのもの。S-LTX が高優先度、staging により
   次 epoch から開始、order forwarding で false-positive abort を回避 (§3.1.1–3.1.3)。評価
   (§5、未詳読) でも long-tx の commit 率・スループットを主指標にしている。

**order forwarding の既読値維持条件 (詳細)**: Algorithm 1 line 15–17 で "new_epoch ←
min(commit_epoch, commit_epoch_of(ltx_id))" のあと "if max_read_epoch ≥ new_epoch then return
ABORT // read validation" と明記されている。つまり、forwarding 先の epoch (`new_epoch`) が
自分が既に読んだ版の epoch (`max_read_epoch`) 以下になってしまう場合は abort する、という
既読値保護の条件が明示的に存在する。ただし forwarding の方向 (epoch を上げるのか下げるのか) に
ついては、§3.3 の "an S-LTX transaction may be placed earlier than its opening epoch by order
forwarding" という記述と、Algorithm の `min(...)` 演算とが素直に符合しており、**「epoch 値としては
早まる (小さくなる) 方向に動くことがある」**というのが原典の記述であり、必ずしも「時間的に前進
(未来へ) する」という直感的な意味の forward ではないことに注意 (逐語のまま報告し、深読みしない)。

**GC との接続**: "Setting a longer epoch reduces epoch carryover and the cost of garbage
collection in multi-version environments." (§3.4.1)。ただしこれは epoch 長という**設計パラメタ**
の効果の記述であり、order forwarding という**個別の前進操作**が GC 境界を直接動かす、という
記述ではない。S-OCC 側の read epoch metadata については「in-place 更新のため GC 不要」という
逆方向の記述もある: "Since this metadata is updated in place, garbage collection is not
required." (§3.3)。

### 本案 4 点との照合

- (1) 物理配置を入力にする: **言っていない (読んだ範囲では見当たらない)。** hot/cold・物理配置・
  メモリ階層への言及は全文検索した範囲でゼロ件 (grep で `hot`/`cold`/`placement`/`NVM` 等を
  検索したが該当なし)。
- (2) 版選択と timestamp 選択の同時扱い: **言っていない (読んだ範囲では見当たらない)。**
  order forwarding は「自分の epoch を動かす」操作であり、「意図的に非最新版を選ぶ」記述はない
  (§3.4.3 の snapshot は epoch 単位の committed version 集合であり、tx はその中の可視版を読む
  という通常の MVCC 可視性であって、能動的な旧版選択ではない)。
- (3) 前進を GC へ接続: **一般論としては言っている (epoch 長と GC コストの接続) が、forwarding
  操作個別との接続は言っていない (読んだ範囲では見当たらない)。**
- (4) 複数版メタデータの共通構造化: **一部言っている。** WP を「table 粒度・1 つの 64-bit atomic
  word」にまとめて version 情報と lock bit を同居させる最適化がある (§3.6)。ただしこれは
  「forwarding 可否判断」の高速化ではなく「WP 観測の高速化」に閉じている。

### 関連研究節・引用から見つけた先行研究

§6.1.2 (Protocols for Long Transactions) で以下が見つかった。いずれも**未確認 (原典未取得)**。
- Oze [25] — "explores the MVSR, which offers a broader scheduling space than traditional CSR"
- TuskFlow [28] — グラフデータ向け長時間 read-write transaction、deterministic CC ベース
- DDI [12] — "selectively utilizing multiple weak isolation levels (e.g., Read Committed and
  Snapshot Isolation)"
- Wait-Hit protocol [35] — "circumventing complex cycle detection in favor of lightweight
  verification based on compressed conflict information"

---

## 候補 5: Rebirth-Retire (PVLDB 18(9), 2025)

**書誌**: Qian Zhang, Yiwen Xiang, Jianhao Wei, Yang Yang, Yifan Li, Xueqing Gong, Wanggen Liu.
"Rebirth-Retire: A Concurrency Control Protocol Adaptable to Different Levels of Contention."
PVLDB 18(9):3162–3174, 2025.

**取得元**: https://www.vldb.org/pvldb/vol18/p3162-zhang.pdf (依頼文に記載の URL と一致) →
`src/rebirth-retire.pdf` (SHA-256: `005e2d84fdfaac45ab3ec24837f22a83a3d75c7c3131c50175760ae3cfa03655`)。
PVLDB 公式掲載版 (pdfinfo で 13 頁、ページ番号 3162–3174 を本文中に確認)、PDF/A-2b。

**読んだ範囲**: §1 Introduction (概要)、§2.2–2.3 (System Time Proportion, Unnecessary Abort)、
§3.1.2 Rebirth、§3.2 Protocol Description 全体 (Algorithm 1–3 を含む)、§3.3 Proof of
Correctness、§4.2–4.4 (Optimistic Read Descendant, Assign Larger Timestamps, Version
Prefetching)、§6 Related Work、§7 Conclusion、References の該当箇所。**未読**: §2.1、§5 全体
(実験詳細)、§4.1。

### 機構の比較 6 列

1. **何を入力に判断するか**: lock 要求時、要求者 (Older, timestamp が小さい) が保持者 (Younger)
   と衝突するという lock 衝突。引用: "When a transaction A acquires a lock, it discovers that a
   younger transaction B holds the lock and conflicts with it." (§3.1.2, p.3166)
2. **どの状態を変えるか**: 要求者 (と、それに依存する descendant 群) の timestamp。「現在の
   系全体で最大の timestamp を順に割り当てる ("Largest" 戦略)」か「衝突相手の最大 timestamp+1
   から順に割り当てる ("Larger" 戦略)」のいずれか (§4.3, p.3168)。
3. **どの不変条件を保つか**: serializability。ただし証明 (§3.3, Theorem 1) は **timestamp の
   値そのものではなく、`Parents`/`Children` 依存グラフと commit point の順序**に基づく
   (Lemma 1)。引用: "Every schedule in Rebirth-Retire is serializable... no cycle may exist
   since a transaction cannot reach the commit point after it has already reached the commit
   point" (§3.3, p.3167)。
4. **どのコストを減らすか**: Wound (younger の強制 abort) による無用な abort。引用: "The basic
   idea of Rebirth is to assign a new, larger timestamp to the older transaction, thereby
   avoiding aborting the younger transaction holding the lock." (§3.1.2, p.3166)
5. **旧版を新たに読めるか (MVCC か)**: **可、MVCC。** "in Rebirth-Retire, a tuple may have
   multiple versions, and transactions are allowed to read the corresponding version based on
   their timestamps." (§4.4, p.3168–3169)。version chain は heap 構造に格納され、長い chain の
   cache miss 対策として version ごとに prefetch 用 jump pointer を追加する最適化がある
   (同節)。
6. **長い transaction への効き方**: 明示的な議論は薄い。Rebirth により older tx が abort されにくく
   なる分、長時間ロックを保持し得る transaction への影響はあり得るが、原典中に「長い tx」を主題
   とした記述は見当たらない。

**既読値の維持条件について**: lock ベース (2PL 系統) であるため、Sundial/Shirakami のような
「commit 直前に読んだ値の epoch を検証する」明示的な read-validation ステップは見当たらない。
正しさは §3.3 の commit point 順序 (`Lemma 1`) にのみ依拠しており、**Rebirth によって timestamp
が変わった後、その tx が以前に読んだ版が新しい timestamp のもとでも妥当であり続けるかを
再検証する記述は、読んだ範囲では見当たらない**。これは原典が明示的に論じていない点として
「言っていない」と分類する (欠落の指摘であり、誤りだと主張するものではない)。

### 本案 4 点との照合

- (1) 物理配置を入力にする: **言っていない (読んだ範囲では見当たらない)。** ただし興味深い
  近傍事実として、§4.4 は「長い version chain の走査で cache miss が増える」という物理コストを
  明示的に認識しているが (p.3168)、これを Rebirth の**発火条件**にはせず、prefetch という
  **隠蔽側の最適化**として処理している。引用: "Since tuple versions are typically stored in a
  heap structure, transactions may experience a significant number of cache misses while
  traversing these version chains. To address this, we leverage the software prefetching
  technique..." (§4.4, p.3168)。つまり原典は「物理配置コストをどう隠すか」は論じているが、
  「物理配置を timestamp 制御の入力にする」方向は取っていない。
- (2) 版選択と timestamp 選択の同時扱い: **言っていない (読んだ範囲では見当たらない)。**
  読み込み時の版選択は「自分の timestamp に対応する版」という通常の MVCC 可視性ルールのみで
  (§4.4)、Rebirth (timestamp 再割当) と version 選択を連動させる記述はない。
- (3) 前進を GC へ接続: **言っていない (読んだ範囲では見当たらない)。** version の GC・保持境界
  についての記述自体が §4.4 を含め見当たらない (prefetch の話のみで、version 削除・retention
  の議論はなし)。
- (4) 複数版メタデータの共通構造化: **部分的に近い。** `Children` list を 64 bit のうち 1 bit を
  各 worker thread に割り当てる atomic word として実装する最適化 (§4.2, "we propose an
  optimization that use an 8-byte word to implement the children list") はあるが、これは
  依存グラフ追跡の高速化であり、「版選択・forwarding 可否・validation を単一構造でまとめる」
  話ではない。

### 関連研究節・引用から見つけた先行研究 (Dynamic Timestamp Assignment 節、§6, p.3173)

- **Arora, Suresh Babu, Basil John, Agrawal, El Abbadi, Xun Xue, Zhiyanan, Zhujianfeng.
  "Dynamic Timestamp Allocation for Reducing Transaction Aborts." IEEE CLOUD 2018.** — 原文
  参照 [3]。**未確認** (書誌のみ)。DOI: 10.1109/CLOUD.2018.00041 と本文中に明記。
- **Matthew Burke, Florian Suri-Payer, Jeffrey Helt, Lorenzo Alvisi, Natacha Crooks. "Morty:
  Scaling Concurrency Control with Re-Execution." EuroSys 2023.** — 原文参照 [8]。
  **候補 7 として別途原典を取得・確認した (後述)。**
  引用: "Rebirth-Retire assigns timestamps when conflicts occur and can abort transactions at
  any point during execution" という対比の中で言及 (§6, p.3173)。
- **Zhiyuan Dong, Zhaoguo Wang, Xiaodong Zhang, Xian Xu, Changgeng Zhao, Haibo Chen, Aurojit
  Panda, Jinyang Li. "Fine-Grained Re-Execution for Efficient Batched Commit of Distributed
  Transactions." PVLDB 16(8):1930–1943, 2023.** — 参照 [17]。**未確認** (書誌のみ、本文中の
  直接引用は確認していない — Related Work の直後の版に現れる可能性があるが読んだ範囲外)。
- **Xingda Wei, Rong Chen, Haibo Chen, Zhaoguo Wang, Zhenhan Gong, Binyu Zang. "Unifying
  Timestamp with Transaction Ordering for MVCC with Decentralized Scalar Timestamp." NSDI
  2021.** — 参照 [39]。**未確認** (書誌のみ)。
- **"Timestamp as a Service, not an Oracle." PVLDB 17(5):994–1006, 2024.** — 参照 [31]。
  **未確認** (著者名は抽出テキストのレイアウト崩れで正確に取得できず、書誌の巻号のみ確認)。

---

## 候補 6: MV3C (Dashti, Basil John, Shaikhha, Koch)

**書誌 (出版版)**: Mohammad Dashti, Sachin Basil John, Amir Shaikhha, Christoph Koch.
"Transaction Repair for Multi-Version Concurrency Control." SIGMOD 2017, pp. 235–250.
DOI: 10.1145/3035918.3035919 (DATA Lab, EPFL, Switzerland)。

**取得できた版との相違に関する重要な注記**: SIGMOD 2017 版の PDF は ACM 有償ペイウォールの
ため取得できなかった。公開されている arXiv プレプリント **arXiv:1603.00542 ("Repairing
Conflicts among MVCC Transactions", 同一著者 4 名、2016-03-02 提出、v1 のみ)** を代わりに
取得・確認した。**このプレプリントの題名は SIGMOD 版の題名と異なる**
("Repairing Conflicts among MVCC Transactions" vs "Transaction Repair for Multi-Version
Concurrency Control")。abstract の内容は MV3C という名称・機構 (dependency graph による
partial re-execution) と一致することを確認したが、**本文の全文が SIGMOD camera-ready と
byte-for-byte 同一である保証はない** (プレプリントは 2016 年提出で SIGMOD 採択より前の版の
可能性が高い)。以下の逐語引用・節番号はすべてこのプレプリントに基づく。

**取得元**: https://arxiv.org/pdf/1603.00542 → `src/mv3c_arxiv.pdf`
(SHA-256: `0f7b7a2eeb3b987200c3fd6cae8b963e262e40b0d0ca30f86cb1db76aaec1fda`)。arXiv 提出履歴を
直接確認し、v1 (2016-03-02) のみが存在することを確認済み。

**読んだ範囲**: Abstract、§1 Introduction (概要)、§3 MV3C DESIGN 全体 (3.1 OMVCC overview〜3.5
MV3C repair、3.6 Serializability Proof の前半)、§5.2 Reusing Previously Read Versions、§6
Implementation (概要)。**未読**: §3.2 MV3C machinery の詳細、§3.3–3.4 の細部、§4 (存在すれば)、
§5.1、§7 Evaluation の実験詳細、References 全件 (抽出テキストのレイアウト崩れで機械的な
書誌抜き出しができなかった)。

### 機構の比較 6 列

1. **何を入力に判断するか**: 述語 (predicate) の validation 失敗。「別の並行 tx が commit した
   版が、自分の predicate の対象範囲と一致する」という検出 (§3.4, 詳細節は未読だが§3.5冒頭で
   要約されている)。
2. **どの状態を変えるか**: 新しい start timestamp `S'`、および無効になった predicate に対応する
   閉包 (closure) だけを pruning して再実行する。引用: "the first step for repairing the
   transaction is picking a new start timestamp S' for the transaction. Then, the Repair
   algorithm... is applied" (§3.5, PDF p.7)。
3. **どの不変条件を保つか**: serializability (commit order で証明、§3.6)。
4. **どのコストを減らすか**: 「conflict のたびに transaction 全体を abort & restart する」
   コスト。引用: "restarting from scratch creates a negative feedback loop in the system,
   because the system incurs additional overhead that may create even further conflicts."
   (Abstract)
5. **旧版を新たに読めるか (MVCC か)**: **可、MVCC (OMVCC ベース)。** version chain・
   committed version の定義あり (§3.1, PDF p.3, Definition 3.1–3.3)。
6. **長い transaction への効き方**: MV3C の主要な動機の 1 つ。引用: "having long running
   transactions, the lifespan of which intersects with that of many other transactions" を
   優先度の高い課題として挙げている (§1)。ただし対策は「衝突した述語だけを部分再実行する」ことで
   あり、本案の timestamp forwarding とは異なる (下記参照)。

**「既読値を保つ」かどうかの核心的な事実**: MV3C repair は本案とは逆の設計である。引用:
"All the read operations in a transaction that runs under a timestamp ordering algorithm...
return the same result-sets when re-executed, if the start timestamp does not change. In
other words, if a transaction reads obsolete data, even if it is re-executed, it would read
the same data, and fail validation again." (§3.5, PDF p.7)。つまり MV3C は「obsolete な
(stale な) 既読値をそのまま保って timestamp だけ動かす」ことを明示的に**しない** — 無効になった
predicate は timestamp を進めたうえで**再実行 (再読み込み) する**。有効なままの predicate
(L1 に分類されるもの) だけが、"read the same data" という理由で計算結果を再利用される
(§3.5, Case 1 の証明)。これは「壊れていない部分は再検証だけで済ませ、壊れた部分だけ新しい
timestamp で読み直す」という設計であり、child-common.md が指定する通り**「本案 (timestamp
forwarding で既読値を保つ) とは異なる、修復 (repair) 型」**であることを一次資料で確認した。

### 本案 4 点との照合

- (1) 物理配置を入力にする: **言っていない (読んだ範囲では見当たらない)。**
- (2) 版選択と timestamp 選択の同時扱い: **言っていない。** §5.2 "Reusing Previously Read
  Versions" は版選択の最適化に見えるが、実体は「述語の計算結果 (result-set) をキャッシュし、
  外挿的な差分修正で再利用する」ことであり (例: "the result-set can be fixed by accommodating
  the concurrently committed versions into the result-set", PDF p.9)、**「非最新の hot な版を
  意図的に選ぶ」話ではない**。
- (3) 前進を GC へ接続: **明示的な接続の記述はない。** GC は §6 Implementation にあるが、
  「最も古い active transaction の start timestamp」を境界とする標準的な watermark 方式
  (引用: "It is mainly used for tracking the active transaction with the oldest start
  timestamp, which is necessary for garbage collection. Like [14], the garbage collection of
  the versions created by a committed transaction is performed after ensuring that there is
  no older active transaction that could read the versions.", PDF p.8)。repair で `S'` に
  進むことで、その tx 自身が古い版を pin する期間が実質的に短縮されうるが、**この帰結を GC
  境界の観点から論じた記述は見当たらない** (これは推論であり、原典の主張ではないと明記する)。
- (4) 複数版メタデータの共通構造化: **言っていない。**

### 関連研究節・引用から見つけた先行研究

参考文献リストの抽出が PDF の 2 段組レイアウト崩れで機械的にできなかったため、本文中の言及
[14] (OMVCC の原論文、§3.1 で "Recent research proposes an optimistic MVCC algorithm as the
best fit for concurrency control in in-memory databases [14]" として言及) のみ確認できたが、
著者名・正確な書誌は特定できていない。**未確認**として報告する。

---

## 候補 7: 「版を捨てて古い tx を再実行させる・abort させる方式」の検索結果

検索クエリ: "long-running transaction abort garbage collection multiversion concurrency
control discard old timestamp reassign"、"kill/abort long transaction advance garbage
collection watermark"、および Rebirth-Retire の Related Work 節からの派生検索。

### 発見・確認した論文: Morty (EuroSys 2023)

**書誌**: Matthew Burke, Florian Suri-Payer, Jeffrey Helt, Lorenzo Alvisi, Natacha Crooks.
"Morty: Scaling Concurrency Control with Re-Execution." Eighteenth European Conference on
Computer Systems (EuroSys '23), May 9–12, 2023, Rome, Italy. DOI: 10.1145/3552326.3567500

**取得元**: https://www.cs.cornell.edu/~matthelb/papers/morty-eurosys23.pdf (著者本人の公開
ページ) → `src/morty.pdf` (SHA-256: `33599e6980bc1654bd0ef98272ce4e524acf16c8fbcf86b3f001386668896bd1`)。
16 頁、著者版 (author's copy、ACM フォーマット)。

**読んだ範囲**: Abstract、§1 Introduction (概要)、§3 Transaction Re-Execution 全体 (3.1
Existing Approaches, 3.2 Re-Execution)、§4.1 (冒頭のみ)、§4.3 Handling Failures、§4.4 Garbage
Collection & Truncation、§4.5 Correctness (Theorem 4.1 とその証明スケッチ)、§6 Related Work
の見出しのみ。**未読**: §2 (Sequential Execution ほかの背景節)、§4.1–4.2 の詳細、§5 Evaluation
の実験詳細。

**機構**: 2 つの transaction の serialization window が重なったとき、**古い方の transaction の
既読値を、衝突相手の書いた新しい値に置き換え、その値に依存する処理だけを部分的に再実行する**、
という「read unrolling」機構。引用: "Whenever the serialization windows of two transactions T
and T' overlap, transaction re-execution resolves the overlap by changing the read value of T
to T''s write, thereby shifting T's window forward." (§3.2, EuroSys '23 p.4 相当)。

**本案との違い (重要)**: これは本案の向きの**正反対**である。本案は「既読値を保てる範囲で
timestamp を前進させ、hot な旧版を読み続ける」設計だが、Morty は「timestamp (window) を前進
させるために、既読値を**捨てて**新しい版の値に置き換える」設計である。引用: "transaction
re-execution shifts reads forward in time by invalidating the current values read in a given
execution and replacing them with others, produced by newer writes." (§3.2)。

**GC との接続 (§4.4)**: Morty の version 順序識別子 `ver(T)` (re-execution により変わりうる
論理位置) が、そのまま truncation (GC) の境界 `truncation_ver` の入力になっている。引用:
"Morty safely truncates the erecord with a truncation protocol... which chooses an increasing
truncation_ver that summarizes all committed state from transactions with smaller versions...
state in the erecord and vstore associated with a transaction T whose version ver(T) is smaller
than truncated_ver may be deleted." (§4.4)。**「前進操作の結果 (version 順序) をそのまま GC/
truncation 境界に使う」という構造そのものは Morty に確認できる**が、対象は Morty 独自の
複製プロトコル用メタデータ (`erecord`/`vstore`) であり、本案が想定する「版データそのものの
保持義務」とは対象が異なる可能性がある (読んだ範囲では版データ本体と `vstore` の関係を完全には
確認できていない)。

**旧版を新たに読めるか**: 可 (再実行によって新しい版を読む、という設計そのものが version 管理
前提)。ただし「意図して古い版に留まる」ことはしない設計であり、本案 (2) の対極。

**物理配置の入力化**: **言っていない (読んだ範囲では見当たらない)。** 発火条件は純粋に
serialization window の重なり (論理的な衝突) であり、"hot key" への言及 (§5、"as the number
of transactions accessing... on hot keys increases") はあるが、これは contention (論理衝突) の
話であって物理メモリ配置の話ではない。

### 見つけたが未確認・未取得の関連候補 (item 7 の周辺)

- Dong et al. "Fine-Grained Re-Execution for Efficient Batched Commit of Distributed
  Transactions." PVLDB 16(8):1930–1943, 2023. (Rebirth-Retire 経由で発見、§6, p.3173)
- CCBench (Tanabe et al., arXiv:2009.11558, "An Analysis of Concurrency Control Protocols for
  In-Memory Databases with CCBench") — WebSearch の要約に "AggressiveGC" という、長い tx を
  abort して新しい timestamp で retry するスキームへの言及があったが、**これは本タスクの
  素材コーパスである CCBench 自体であり、本担当としては原典を deep-read していない
  (izanagi の他ドキュメントで既知の可能性が高いため対象外とした)**。

---

## 取得物一覧 (`src/` 配下、本担当が新規取得したもの)

| ファイル | SHA-256 | 取得元 |
|---|---|---|
| sundial.pdf | 4f384ac51d4dbf77330b6df0446e272b99b821664cafa0847af7b7c32f1e638b | vldb.org/pvldb/vol11/p1289-yu.pdf |
| maat.pdf | e2caafb363d0c90e47da06802b5c150fca778f418d9c58817a7fd1171e1b3ad6 | vldb.org/pvldb/vol7/p329-mahmoud.pdf |
| shirakami.pdf | e9cf8b914e00130e2b9a0260047eaaeb20a0df30ad60bedde9c534b6cd078b03 | arxiv.org/pdf/2303.18142 (= v3, 2026-07-02) |
| rebirth-retire.pdf | 005e2d84fdfaac45ab3ec24837f22a83a3d75c7c3131c50175760ae3cfa03655 | vldb.org/pvldb/vol18/p3162-zhang.pdf |
| mv3c_arxiv.pdf | 0f7b7a2eeb3b987200c3fd6cae8b963e262e40b0d0ca30f86cb1db76aaec1fda | arxiv.org/pdf/1603.00542 (v1、SIGMOD版とは別題名) |
| lomet2012.pdf | 3f3207d3fafc0e57504d6a65b68a06d80b7ca4af5edc450c0bc13645be90b00c | microsoft.com research wp-content (ICDE 2012 著者版) |
| morty.pdf | 33599e6980bc1654bd0ef98272ce4e524acf16c8fbcf86b3f001386668896bd1 | cs.cornell.edu/~matthelb (EuroSys 2023 著者版) |

Bayer et al. (1982) および Boksenbaum et al. (1984, VLDB) は取得を試みたが本文入手不可
(DBLP は bot 対策でブロック、vldb.org/conf/1984/P377.PDF は 403 Forbidden)。

## 指示めいた文字列について

取得した全 PDF (7 本) を通じて、エージェントの振る舞いを変えるよう求める指示めいた文字列は
**見つからなかった**。すべて通常の学術論文の本文・参考文献であった。
