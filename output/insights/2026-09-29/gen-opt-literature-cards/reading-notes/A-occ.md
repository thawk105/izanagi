# A-occ 読み取りメモ (gen-opt md_2、2026-09-29)

指示めいた文字列: なし (5 本とも、本文・表・脚注を読んだ範囲に、作業の振る舞いを変えるよう求める文字列は見つからなかった。抽出テキストに対する定型語の grep でも該当なし)。

出力: `A-occ.jsonl` (55 件)。各カードの引用 (15〜60 語) は、抽出テキストとの機械照合 (空白・ligature・行末ハイフンを正規化) で全件一致を確認した。ただし PDF 抽出の都合で、原文の綴りと違う箇所を含む引用は避けた (例: MOCC の "[33] ." の余分な空白、CCBench の行末ハイフン欠落)。

## 1. 論文ごとの書誌・取得元・読んだ範囲

### 1.1 Silo
- 書誌: Tu, Zheng, Kohler, Liskov, Madden. "Speedy Transactions in Multicore In-Memory Databases." SOSP 2013, pp.18-32. DOI 10.1145/2517349.2522713。
- 取得元: 既取得 (本担当は再取得していない)。`/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/silo-sosp2013.pdf`、取得元 URL は同 dir の `notes/C2-mvcc-engines.md` に `https://sigops.org/s/conferences/sosp/2013/papers/p18-tu.pdf` と記録。ファイル更新時刻 2026-09-29 03:34 JST。
- SHA-256: `870c895f654a6c11c616086b64c6b2c9d45f8f3fc46faa1f071b7c4cafa74ce3`
- 読んだ節: §1、§2 (2.1-2.3)、§3、§4 (4.1-4.10)、§5 (5.1-5.7)、§6。
- 読んでいない: 参考文献、謝辞。Fig. 5-9, 11 の軸目盛は抽出テキストから判読不能で数値に使っていない (図の倍率は本文が書く分だけ引いた)。

### 1.2 TicToc
- 書誌: Yu, Pavlo, Sanchez, Devadas. "TicToc: Time Traveling Optimistic Concurrency Control." SIGMOD 2016. DOI 10.1145/2882903.2882935。
- 取得元: 既取得。`.../vhash-related-work-2026-09-29/src/tictoc-sigmod2016.pdf`。同 dir の `notes/B-cicada-tictoc.md` によれば、`dspace.mit.edu` 経由は CAPTCHA HTML で失敗、成功したのは `https://people.csail.mit.edu/sanchez/papers/2016.tictoc.sigmod.pdf`。更新時刻 2026-09-29 03:30 JST。
- SHA-256: `d19fc1e7140a6b4f5f2f120d4ef68ce1c94c092bf673a81fa796f22443b547ff`
- 読んだ節: Abstract、§1、§2、§3 (3.1-3.7)、§4 (4.1-4.2)、§5 (5.1-5.4)、§6 (6.1-6.6)、§7。
- 読んでいない: 参考文献。Fig. 4-10 の軸目盛は判読不能で、本文と表 (Table 1, 2) の数値だけ使った。
- 頁の書き方: 引用位置の "p.N" は PDF の頁 (1 始まり)。

### 1.3 MOCC
- 書誌: Wang, Kimura. "Mostly-Optimistic Concurrency Control for Highly Contended Dynamic Workloads on a Thousand Cores." PVLDB 10(2): 49-59, 2016。
- 取得元: `https://www.vldb.org/pvldb/vol10/p49-wang.pdf` (curl -sSL -A "izanagi-literature-survey")、取得時刻 2026-09-29T10:02:09+09:00。保存先 `src/mocc-pvldb10.pdf` (894,635 bytes)、`src/mocc.txt` は `pdftotext` (段組を解かない形) の出力。
- SHA-256: `e3acc3bc0a5c3ca5129e10c3411547e4724f31caf946c8eb4b38282233df137a`
- 読んだ節: Abstract、§1、§2、§3 (3.1-3.4)、§4 (4.1-4.3)、§5 (5.1-5.6)、§6、§7。
- 読んでいない: MQL の完全な algorithm (本文は extended version [44] に委ねる。未取得)、Fig. 1, 2, 6, 7, 8 の軸目盛 (判読不能)、参考文献。
- 印刷頁 (49-59) を引用位置に使った。

### 1.4 CCBench
- 書誌: Tanabe, Hoshino, Kawashima, Tatebe. "An Analysis of Concurrency Control Protocols for In-Memory Databases with CCBench." PVLDB 13(13): 3531-3544, 2020. DOI 10.14778/3424573.3424575。
- 取得元: 既取得。`.../vhash-related-work-2026-09-29/src/ccbench-pvldb13-13-tanabe.pdf`。同 dir の `notes/A-ccbench-cidr.md` に `https://www.vldb.org/pvldb/vol13/p3531-tanabe.pdf` と記録。更新時刻 2026-09-29 03:29 JST。
- SHA-256: `fee3789bbe81ae308650bc3f3b3fdb2e797ad1bc61ef530d4e76b8a9e5844c93`
- 読んだ節: Abstract、§1、§2、§3 (3.1-3.4、Table 1 は PDF 4 頁をレイアウト付きで確認)、§4 (4.1-4.3)、§5、§6、§7 (7.1-7.3)、§8、§9。
- 読んでいない: 参考文献、拡張版 [49] (TPC-C の結果、未取得)。図の軸目盛は判読不能。
- 印刷頁 (3531-3544) を引用位置に使った。

### 1.5 "Staring into the Abyss"
- 書誌: Yu, Bezerra, Pavlo, Devadas, Stonebraker. PVLDB 8(3): 209-220, 2014。DOI は本担当では未確認 (URL のみ記録)。
- 取得元: `https://www.vldb.org/pvldb/vol8/p209-yu.pdf` (curl -sSL -A "izanagi-literature-survey")、取得時刻 2026-09-29T10:02:10+09:00。保存先 `src/abyss-pvldb8.pdf` (911,157 bytes)、`src/abyss.txt` は `pdftotext` の出力。
- SHA-256: `77d32efbf102db75d7bb3b29fa538edbf3b59d233a08061106bc8d9b735b3746`
- 読んだ節: Abstract、§1、§2 (2.1, 2.2)、§3 (3.1-3.4)、§4 (4.1-4.3)、§5 (5.1-5.6)、§6 (6.1, 6.2)、§7、§8、§10。
- 読んでいない: 参考文献。図の軸目盛は判読不能 (傾向は本文から)。
- 印刷頁 (209-220) を引用位置に使った (PDF 頁 p に 208 を足した値。節見出しを PDF 頁ごとに確認)。
- 注: `src/` には、他担当のものと思われる `bamboo.pdf`・`plor.pdf`・`ssn-arxiv1605.04292.pdf`・`ssn.txt` も置かれている。本担当は読んでいない。

## 2. CCBench の 3 分類の定義 (原文の逐語)

論文は 3 分類を 1 か所で形式的に定義しない。分類名と各要因の説明は次に分かれる。

- 分類名 (Abstract): "We classified the optimization methods on the basis of three performance factors: CPU cache, delay on conflict, and version lifetime."
- 分類名 (§8 Related Work、§9): "We classified a variety of methods on the basis of three performance factors: cache, delay, and version lifetime." 本文中は 'cache' / 'delay' / 'version lifetime' の短い名を使い、'delay on conflict' の呼称は Abstract だけ。
- Table 1 (p.3534) の見出しは "Performance Factor: Cache / Delay / Version Lifetime"。配下の最適化方法 (Table 1 と §3.2 の (1)-(7)) は次のとおり。
  - Cache: DecentralizedOrdering、InvisibleReads
  - Delay: NoWait or Wait、AdaptiveBackoff、ReadPhaseExtension
  - Version Lifetime: AssertiveVersionReuse、RapidGC
  (Table 1 の Cache / Delay / Version Lifetime の見出し位置は、PDF 4 頁をレイアウト付きで抽出して確認した。)
- cache の説明 (§5 冒頭、p.3537): "Cache-line conflict occurs when many worker threads access to the same cache-line with some writes (e.g., accessing a single shared counter). The cache-line becomes occupied by a single thread, and the other threads are internally blocked. Cache-line replacement occurs when transactions access a large amount of data (e.g., high cardinality, low skew, or large payload). The data accesses tend to replace the contents of the L1/L2/L3 cache."
- delay の説明 (§6.1、p.3539): "A method for mitigating performance degradation caused by conflicts is to place an additional artificial delay before a retry, such as with NoWaitTT [64] and AdaptiveBackoff [35]."
- version lifetime の説明 (§7.1、p.3540): "The life of a version begins when a corresponding write operation creates it. The version state is called visible during the period when other transactions can read it. Otherwise, the version state is called non-visible."
- 各方法の 1 行定義 (§3.2、p.3535): (1) DecentralizedOrdering: "prevents contended accesses to a single shared counter." (2) InvisibleReads: "read operations that do not update memory and cache-line conflicts do not occur." (3) NoWait or Wait: "immediate abort upon detecting a conflict followed by retry, or waiting for lock release." (4) ReadPhaseExtension: "an artificial delay added to the read phase, inspired by the extra read process that retries the read operation." (5) AdaptiveBackoff: "an artificial delay before restarting an aborted transaction." (6) AssertiveVersionReuse: "allocates thread-local space, denoted as version cache in Fig. 1, to retain versions so that memory manager access is not needed." (7) RapidGC: "frequent updating of timestamp watermark for GC in MVCC protocols."
- カード側の `effect_category` は、CCBench 論文の当該最適化には論文の Table 1 の群に従い、他 4 本の論文の最適化には CCBench の 3 要因へ本担当が当てはめた (各カードの `effect_category_note` に「推測」と注記)。当てはまらないものは `none`。

## 3. 論文ごとの最適化の一覧 (JSONL に入れたもの、計 55 件)

### Silo (11 件)
- silo-commit-protocol (protocol-core)、silo-decentralized-tid (protocol-core)、silo-epoch-serialization (protocol-core)
- silo-version-validated-reads、silo-inplace-overwrite、silo-inline-record-data、silo-snapshot-transactions、silo-epoch-gc、silo-node-set-phantom-protection、silo-epoch-group-durability、silo-numa-aware-allocator

### TicToc (6 件)
- tictoc-data-driven-timestamp (protocol-core)
- tictoc-ts-word-packing、tictoc-nowait-validation、tictoc-preemptive-abort、tictoc-timestamp-history、tictoc-lower-isolation-levels

### MOCC (5 件)
- mocc-temperature-selective-read-locks (protocol-core)、mocc-canonical-mode-lock-release-reacquire (protocol-core)
- mocc-approximate-counter-page-temperature、mocc-retrospective-lock-list、mocc-queuing-lock-mql

### CCBench (15 件)
- 論文が Table 1 で名指す 7 方法: ccbench-decentralized-ordering、ccbench-invisible-reads、ccbench-nowait-or-wait、ccbench-adaptive-backoff、ccbench-read-phase-extension (新規)、ccbench-assertive-version-reuse (新規)、ccbench-rapid-gc
- §7.3 の提案 (評価なし): ccbench-aggressive-gc (新規)、ccbench-version-overwriting、ccbench-non-visible-write
- §3.3 の実装上の改良 (各 protocol の CCBench 実装差分): ccbench-silo-epoch-cacheline-padding、ccbench-fused-commit-tid-calculation、ccbench-tictoc-skip-redundant-rts-update、ccbench-mocc-temperature-reset-epoch、ccbench-ermia-onedim-mapping-table

### Abyss (18 件、すべて design-dimension か optimization)
- 設計次元 (kind: design-dimension): abyss-dl-detect、abyss-no-wait、abyss-wait-die、abyss-basic-to、abyss-mvcc、abyss-occ、abyss-hstore、および timestamp 割当て 5 方式 (abyss-ts-alloc-mutex、-atomic-add、-batched-atomic、-clock、-hardware-counter)
- 最適化 (kind: optimization): abyss-per-tuple-lock-table、abyss-custom-malloc、abyss-lockfree-partitioned-deadlock-detector、abyss-lock-wait-timeout、abyss-distributed-validation、abyss-hstore-local-partitions

論文が挙げる bottleneck (Abyss §6.1、p.219): "In particular, we identified several bottlenecks to scalability: (1) lock thrashing, (2) preemptive aborts, (3) deadlocks, (4) timestamp allocation, and (5) memory-to-memory copying." 各方式の要約は Table 2 (p.219)。対策として本文が示すのは、非待機の deadlock 防止 (NO_WAIT)、timeout による abort (§4.2)、hardware 支援の timestamp 割当て (§4.3、§6.1)、および方式の切替の示唆 (§6.1、評価なし)。

## 4. JSONL に入れなかった候補 (理由つき)

- Silo: (a) insert 時に absent 状態の placeholder record を先に作る手法・delete を absent bit で表す手法 (§4.5)。commit protocol の一部の扱いで、独立した節・ablation がない。 (b) secondary index を table として commit protocol に載せる扱い (§4.7)。機構の追加が無い。 (c) LZ4 圧縮 ('+Compress'、Fig. 11、§5.7)。名前付きの因子だが、本文は「throughput の点で報われない」と述べる負の結果で、CC の最適化でなく logging の選択。 (d) Partitioned-Store と MemSilo+Split (§5.4)。比較対象であって最適化ではない。 (e) MemSilo+FastIds (§5.4)。workload 側の変更 (ID 生成を別 transaction にする) で protocol の最適化ではない。
- TicToc: (a) 並列 logging を batch ごとの最小 commit timestamp で実現する案 (§3.7)。実装も評価もなく、「範囲外」と本文が述べる。 (b) SI・RR は lower-isolation として 1 件にまとめた。 (c) DTA (dynamic timestamp allocation) は関連研究として説明されるだけ (§2.2)。
- MOCC: (a) FOEDUS 由来の「read に page latch を取らない」「apply-after-commit」(§3.1)。前提の recap で MOCC の独自最適化ではない。 (b) 全 read を、read lock で保護していても検証する選択 (§3.3.4)。canonical-mode カードと RLL カードの前提に含めた。 (c) try / asynchronous lock mode (§4.3、Table 1)。MQL カードに含めた。
- CCBench: (a) §2.1 が 1 文ずつ説明する Cicada の EarlyAbort、BestEffortInlining、PrecheckValidation、SortWriteSetByContention (§2.1 p.3532、Table 1 脚注 ζ)。Cicada の担当に委ねる。 (b) 「Silo・FOEDUS・MOCC・ERMIA が導入した read-only 最適化は CCBench が非対応」(§3.2、特定 case の 99% read-only・skew 0.99 でしか効かないため)。最適化ではなく非対応の宣言。 (c) mimalloc・numactl による interleave・事前確保 (§3.2)。公平性のための platform 設計。 (d) 2PL の自前 CAS reader/writer lock (§3.3)。 (e) ERMIA の pstamp/sstamp の統合 (§3.3、原典 ERMIA の §5.1 由来)。 (f) Cicada の version consistency check の不備の修正 (§3.3)。correctness の修正で最適化でない。
- Abyss: (a) §6.1 の将来案 (背景の memory コピー用 hardware accelerator、非集中の memory controller、workload に応じた scheme の切替、MySQL の DL_DETECT+MVCC 混成)。評価なし。 (b) 分割の hash 方針 (§5.5)。実験設定。

## 5. 気づいた点 (事実の記述)

- Abyss §4.3 は batched atomic addition を 'first proposed in the Silo DBMS [42]' と記す。本担当が読んだ Silo 原典 (§4.2) は、epoch と worker 単位の分散 TID を述べており、batched atomic add の記述を見つけていない。Abyss 側の帰属の主張で、本担当では Silo 原典の他の箇所までは確認していない (abyss-ts-alloc-batched-atomic カードに注記)。
- CCBench §4.1 は、TicToc 原論文の高 contention YCSB の曲線は AdaptiveBackoff を付けた TicToc (T+BO) に近く、NoWaitTT の固定 delay を持つ TicToc 原版 (Torg) は低い、と報告する。TicToc 原論文 (§5.1) は no-wait の sleep 長への感度を「大きすぎなければ問題ない」としか述べない。両者は tictoc-nowait-validation と ccbench-adaptive-backoff のカードに書き分けた。
- TicToc 原論文 §6.4 は timestamp history の測定可能な利得を示せなかった。CCBench の Table 1 は TicToc の PreemptiveAbort・TimestampHistory を「他 protocol に適用できない」(脚注) とする。
- MOCC の効果 (Abstract: OCC の 8×、悲観 lock の 23×) は、FOEDUS (OCC)・Orthrus・ERMIA など、別実装の混在で比べた結果である。CCBench §3.1 は、この混在を公平性の欠如として挙げる。MOCC の Fig. 7 の数値カードには、この前提を「FOEDUS 上」と記した。
- Silo 論文の epoch 更新周期 (40 ms) は、TicToc 論文 §2 が Silo の説明で再掲する (Silo 原典 §4.1 と一致)。CCBench §4.1 は再現実験で epoch 周期を 40 ms より長くして global epoch への cache-line 競合を避けたと記す。
- 全カードの数値は、本文・表・図番号を添えられるものだけ載せた。図の軸目盛から読んだ数値は使っていない。
