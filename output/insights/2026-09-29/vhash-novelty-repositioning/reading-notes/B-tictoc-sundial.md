# B: TicToc / Sundial (7 項目、原典の逐語つき)

記法は /work/1/SFC/tanab/tmp/vhash-novelty-2026-09-29/notation.md の 7 項目。逐語は原典テキストからの英語引用。要約は日本語で別掲。
原典本文中に指示めいた文は見つからなかった。Sundial は 2 段組混在を避けるため sundial.pdf を pdftotext (段組なし) で読み直した。

---------------------------------------------------------------
## 1. TicToc (Yu ほか SIGMOD 2016)

読んだ節: §2 (Timestamp Allocation)、§3.1、§3.2 (Algorithm 1〜3)、§3.3、§5.2 (approximate commit timestamp)、§5.3、§6.4、§3.6 冒頭 (TS_word の delta overflow)。

### 7 項目の表

| 項目 | 内容 |
|---|---|
| 位置 π(T) | 実行中に tx の位置を表す変数は無い。commit_ts は commit 時 (validation の Step 2) に、read/write set の各エントリの wts / rts から 1 回だけ導出される点 timestamp。read set には各 tuple の {wts, rts} のコピーがあるが、これは tuple の版の有効範囲であって tx の位置ではない。 |
| 契機 | commit 操作の呼び出し後の validation phase (write set を lock した後の Step 2)。read 時や衝突検出では動かない。 |
| 向き | 変数として動くのではなく導出。read set の tuple については commit_ts >= wts、write set の tuple については commit_ts >= rts + 1 (Algorithm 2 は max を取る)。すなわち「読んだ版の wts より後、書く前版の rts より後」。 |
| 読む版の選択 | 最新版だけ。旧版を新たに読む経路は無い。timestamp history も旧版の値は持たず wts のみ。 |
| 既読維持の判定 | validation Step 3。r.rts >= commit_ts なら何もしない。r.rts < commit_ts なら atomic に「local wts == tuple の現 wts かつ (tuple.rts > commit_ts または lock されていない、または自 tx の write set)」を確認し、満たせば tuple.rts を max(commit_ts, rts) に延長。満たさなければ abort。§5.3 の timestamp history は、wts が一致しないが、その wts が tuple の history buffer にあり、commit_ts が「local wts から history の次の wts まで」に入るとき validation を通す (abort を救う)。 |
| GC への反映 | single-version (上書き) のため版データの GC は該当なし。timestamp history は「固定個数の直近 wts を持つ per-tuple 配列」で、保持期間 (tx の開始 timestamp 等) に結ぶ記述は無い。「GC 不要」と明記。 |
| 長い tx / 停止 tx | 記述なし (読んだ節: §3, §5, §6.4)。 |

### 根拠の逐語

位置 / 契機:
- §3: "a transaction’s timestamp is calculated lazily at its commit time in a distributed manner based on the tuples it accesses."
- §3.2.2: "TicToc uses the timestamps stored in the transaction’s read and write sets to compute its commit timestamp."
- §3.2.1: "TicToc does not allocate timestamps statically, so it does not restrict the set of potential orderings."
- Algorithm 2 Step 2: "commit_ts = max(commit_ts, e.tuple.rts +1)" (write set)、"commit_ts = max(commit_ts, e.wts)" (read set)。
- §3.1 式 (1): "(∀v ∈ {versions read by T}, v.wts ≤ commit_ts ≤ v.rts)" と "(∀v ∈ {versions written by T}, v.rts < commit_ts)"。

読む版:
- §5.3: "transactions in TicToc always read the latest data version."
- §3.1: "A read always returns the version valid at that timestamp" (これは不変式の説明であり、実際に旧版を読むわけではない。read 時の Algorithm 1 は tuple の現値と現 wts/rts を atomic に copy するだけ)。
- §6.3.2 (YCSB): "multiple versions allows more read operations to succeed (since they can access older versions)" は Hekaton についての記述で、TicToc ではない。

既読維持:
- §3.2.2: "If the entry’s rts is less than commit_ts, however, it is not clear whether the local value is still valid at commit_ts."
- §3.2.2: "If they are different, the tuple has already been modified by another transaction and thus it is not possible to extend the rts of the local version."
- §3.2.2: "If wts matches, but the tuple is already locked by a different transaction ... it is not possible to extend the rts either."
- Algorithm 2 line 14〜17: "abort()" / "r.tuple.rts = max(commit_ts, r.tuple.rts)"。
- §5.3: "TicToc always aborts a transaction if its local rts of a tuple is less than commit_ts and the local wts does not match the latest wts."
- §5.3: "To prevent these unnecessary aborts, we can extend TicToc to maintain a history of each tuple’s wts rather than just one scalar value."
- §5.3: "If so, the valid range of that version is from the local wts to the next wts in the history buffer. If commit_ts falls within that range, the tuple can still be validated."
- §6.4: "A key finding is that the timestamp history optimization does not provide any measurable performance gain in either workload."
- §6.4: "TICTOC without this optimization already stores multiple versions of a tuple in each transaction’s private workspace."
- §6.4: "in practice there is no clear performance benefit for the workloads we evaluated."

GC:
- §5.3: "The value of the old version does not need to be stored since transactions in TicToc always read the latest data version."
- §5.3: "the history buffer is a per-tuple array that keeps a fixed number of the most recent wts’s, and thus the DBMS does not have to perform garbage collection."
- §3.2.3 Write phase: "the DBMS sets their wts and rts to commit_ts, indicating that it is a new version" (Algorithm 3 は write(w.tuple.value, w.value) で上書き)。

### 補足 (要約)
- TicToc の commit_ts は「後から決まる」ので、途中で位置が動くという表現自体が当てはまらない。§5.2 の preemptive abort は「local wts/rts から近似 commit timestamp を計算して早期 abort」する (§5.2: "the actual commit timestamp is no less than our approximation")。これは位置の保持ではなく事前検査。
- §3.6 の TS_word: delta が 15 bit を溢れたときは "we also increase wts to keep delta within 15 bits" (dummy write と同等)。これは rts 延長の実装上の副作用で、GC ではない。

---------------------------------------------------------------
## 2. Sundial (Yu ほか PVLDB 11(10) 2018)

読んだ節: §1〜§2.1 (single-version の明記)、§3.1、§3.2、§3.3.1〜3.3.3 (Algorithm 1〜3)、§4 (4.1〜4.3)、§5.1、§5.2 (single-version 言及)、§5.3。
(sundial.txt は 2 段組混在があるため /tmp に pdftotext 段組なしで再抽出して読んだ)

### 7 項目の表

| 項目 | 内容 |
|---|---|
| 位置 π(T) | T.commit_ts。実行中に持つ変数がある: "T.commit_ts is initialized to 0 when T begins" で、read のたびに max(commit_ts, wts)、write の lock 取得のたびに max(commit_ts, rts + 1) と更新される (実行中は下限として単調に増える)。prepare phase でこの値がそのまま commit timestamp として使われ、全 lease の内側に入るかを検査する。 |
| 契機 | execution phase の read (RS の wts を取り込む、line 14) と write の lock 取得 (rts + 1、line 24)。prepare phase の lease 延長。 |
| 向き | 後へだけ (later): 読んだ版の wts 以上、書く前版の rts + 1 以上へ。tuple の wts と rts も "can only increase but never decrease"。 |
| 読む版の選択 | 最新版だけ (single-version)。lock されていても、その tuple の現データと lease を読む (書き込み中の値は commit 後まで見えない)。cache は「過去に読んだ版のコピー」を再利用できるが、旧版を DB の版履歴から選ぶ仕組みではない。 |
| 既読維持の判定 | prepare phase の validate_read_set。read set の tuple (write set 以外) について commit_ts <= rts ならそのまま。commit_ts > rts なら renew_lease を home server に送る。wts が read 時と違う、または (commit_ts > 現 rts かつ他 tx が lock 中) なら ABORT。そうでなければ rts を max(rts, commit_ts) に延長。延長失敗時は cache から該当 key を除去して abort。§5.1 が abort の 3 場合 (a: DB の wts >= commit_ts、b: 別 tx が commit_ts より前に最新版を書いた、c: 他 tx が lock 中) を列挙し、(a) は "maintaining a history of recent wts’s in each tuple [53]" で解消しうると述べる (Sundial 自体は実装しない)。 |
| GC への反映 | single-version のため版データの GC は該当なし (原典は GC に言及しない)。Sundial の保持に関する記述は 2 つ: (1) cache は LRU 置換 (期間ではなく容量)、(2) §5.3 の lease table は cold tuple の lease を (cold_wts, cold_rts) の 1 組に潰し、削除時に max を取る。いずれも tx の開始 timestamp や commit_ts に結ぶ記述は無い。 |
| 長い tx / 停止 tx | 記述なし (読んだ節: §3, §4, §5)。§4.2 に「古い lease のキャッシュを使うと lease 延長に失敗して abort する」記述はあるが、tx の長さではなく cache の古さの話。 |

### 根拠の逐語

位置 / 契機 / 向き:
- §3.1: "the DBMS computes a single commit timestamp for a transaction T , which is a logical time that falls within the leases of all tuples the transaction accesses."
- §3.1: "A transaction writes to a tuple only after the current lease expires, namely, at a timestamp no less than rts + 1."
- Algorithm 1 冒頭: "T.commit_ts is initialized to 0 when T begins."
- Algorithm 1 line 14: "T.commit_ts = Max(T.commit_ts, T.RS[key].wts)"; line 24: "T.commit_ts = Max(T.commit_ts, rts + 1)"。
- §3.3.1: "The coordinator then updates T.commit_ts to be at least the wts of the tuple (line 14), reflecting that T’s logical commit time must be no earlier than the logical time when the tuple was last written."
- §3.3: "Both the wts and rts of a tuple can only increase but never decrease."
- §3.1: "Sundial serializes transactions in logical rather than physical time order."

読む版:
- §2.1: "their protocol requires a multi-version database while Sundial works in a single-version database."
- §3.3.1: "If a tuple is locked, a reading transaction still reads the data of the tuple, with its associated logical lease."
- §3.3.1: "other transactions cannot read tuples in T’s write set—they become visible only after T commits"。
- §4.1: "a transaction can read a cached tuple as long as its commit_ts falls within the lease of the tuple, even if the tuple has been changed at the home server"。

既読維持:
- §3.3.2: "The transaction aborts if the lease renewal fails (line 9)."
- §3.3.2: "If the current wts of the tuple is different from the wts observed by the transaction during the execution phase, or if the extension is required but the tuple is locked by a different transaction, then the DBMS cannot extend the lease and ABORT is returned"
- §3.3.2: "In Sundial, lease extension is the only way to change a tuple’s rts."
- Algorithm 2 renew_lease: "DB[key].rts = Max(DB[key].rts, commit_ts)"。
- §4.1: "if a lease extension fails, the tuple is removed from the cache to prevent repeated failures in the future"
- §5.1 Case (a): "The DBMS must abort T because it is unknown whether or not the version read by T is still valid at T’s commit_ts."
- §5.1 Case (a): "This uncertainty could be resolved by maintaining a history of recent wts’s in each tuple [53]."
- §5.1: "Sundial can potentially avoid the aborts if the DBMS extends the tuple’s lease during the execution phase" (execution 中の延長は "future work" と明記: "We defer the exploration of these optimizations in Sundial to future work.")
- §4.3: 読み取り専用 table では table 単位の tab_rts 延長と rts を commit_ts + δ まで投機延長する。

GC / 保持:
- §4: "Figure 5: Caching Architecture – The cache is at the network side, containing multiple banks with LRU replacement."
- §4: "When the bank is full, tuples are replaced following a least-recently-used (LRU) policy."
- §5.3: "The leases of all ‘cold’ tuples are represented using a single (cold_wts, cold_rts)."
- §5.3: "the DBMS updates cold_wts and cold_rts to Max(cold_wts, wts) and Max(cold_rts, rts), respectively."
- 版の GC を Sundial 自身について述べる箇所は、読んだ節に無い。§6 で garbage collection に触れるのは MaaT の実装 ("improving its garbage collection") と MVCC 比較の "overhead (e.g., garbage collection)" だけで、Sundial の版回収の話ではない。

---------------------------------------------------------------
## 確かめられなかったこと

- TicToc §3.6 (lock-free な TS_word 実装、Algorithm 4) の詳細と §4 (証明)、§5.1 (no-wait)、§5.4 以降の隔離水準の節は、本件の 7 項目に影響しないと見て詳読していない。
- TicToc の「read set に持つ値のコピー = 各 tx の private workspace の複数版」(§6.4) は著者の説明であり、GC や長い tx の記述ではない。長い tx / 停止 tx の記述は、TicToc・Sundial とも読んだ節に見つからなかった (grep: "long-running" は両文書で 0 件)。文書全体の全文精読まではしていない。
- Sundial §6 (評価) の 6.8 (Lomet et al. との比較) と MVCC 比較の節は、7 項目のうち読む版・GC に直接関係する記述が見つからず、精読していない。
- Sundial の [53] (recent wts の history) の中身は参照先の別論文であり、取得済みテキストの範囲外。
