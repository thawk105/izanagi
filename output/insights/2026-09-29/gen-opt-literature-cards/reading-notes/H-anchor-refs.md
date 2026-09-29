# H-anchor-refs 読みメモ (2026-09-29)

指示めいた文字列: なし (5 本の本文を読み、作業の振る舞いを変えるよう求める文字列は見つからなかった。`grep` でも該当なし)

JSONL は 26 件。引用は各 PDF の頁ごとの抽出テキスト (段組を左右に切った版と切らない版) に対し、空白・ハイフン・文献番号 `[n]`・小文字大文字の組版崩れ (`O RTHRUS`) を無視して一致を確かめた (`src/build_h_anchor_refs.py`)。引用の語数は 15〜60 語。loc の頁は PDF の頁番号。

## 取得した 5 本

すべて 2026-09-29 (JST) に `curl -sSL -A "izanagi-literature-survey"` で取得。置き場は `src/`。

| 略称 | 書誌 | 取得元 | 取得時刻 | SHA-256 | 読んだ節 | 読んでいない節 |
|---|---|---|---|---|---|---|
| No False Negatives | Durner, Neumann, ICDE 2019, doi:10.1109/ICDE.2019.00071 (12 頁) | https://db.in.tum.de/~durner/papers/no-false-negatives-icde19.pdf (`nofalseneg.pdf`) | 10:08:40 | eac326a6bd6356f00f64711685de1c979b531f0b73b4e807969f0afe7b8a5a73 | Abstract、§I、§II 全部、§III、§IV-A〜E と Fig. 4-9 | §V、§VI、Table I/II の数値表 |
| Strife (前身稿) | Prasaad, Cheung, Suciu, arXiv:1810.01997v1 (2018-10-03、15 頁) | https://arxiv.org/pdf/1810.01997 (`strife-arxiv.pdf`) | 10:08:50 | 7c6dbf15e46187bd262fe5329a3bb58fe7e615059bb9551248bc225a48a967f0 | 全体 (§1〜§5、§4.1〜4.8) | §6 関連研究、参考文献 |
| ACC | Tang, Jiang, Elmore, CIDR 2017 (8 頁) | https://www.cidrdb.org/cidr2017/papers/p63-tang-cidr17.pdf (`acc.pdf`) | 10:08:41 | 14610aff227f98e65cb9119bcb4b43dd339ef0f2d9e450443dace17819576276 | 全節 | 参考文献 |
| Orthrus | Ren, Faleiro, Abadi, arXiv:1512.06168v3 (2016-01-05、16 頁。脚注に "draft of work that is accepted to appear at SIGMOD 2016") | https://arxiv.org/pdf/1512.06168 (`orthrus-arxiv1512.06168.pdf`) | 10:10:07 | e2ad72f46a46077ec9f41fd93ef94308805d9b35208caf7e14f231cc79d24eea | §1〜§4 (4.1〜4.4)、§5 の前半 | §5 後半以降、付録 A、参考文献 |
| Deuteronomy range CC | Levandoski, Lomet, Sengupta, Stutsman, Wang, PVLDB 8(13):2146-2157, 2015, doi:10.14778/2831360.2831368 (12 頁) | https://vldb.org/pvldb/vol8/p2146-levandoski.pdf (`deuteronomy.pdf`) | 10:09:39 | d0ce5a1a193e43594b2f6429d30d0025359b9d23f1f02633a98de36b67e14e10 | Abstract、§1〜§7 | §8 結論、参考文献 |

### 取得にまつわる注意 (事実)

- **Strife は SIGMOD 2020 掲載版を取得していない。** arXiv で該当題名 (Handling Highly Contended OLTP Workloads Using Fast Dynamic Partitioning) は見つからず、題名検索で当たったのは 2018 年のプレプリント v1 (題名 "Improving High Contention OLTP Performance via Transaction Scheduling") だった。同じ著者の同じ機構 (Strife) の前身稿で、掲載版の追加・変更 (例えば掲載版で加わりうる改良や追加実験) は未確認。カードの paper 欄にこの旨を書いた。
- **Orthrus は SIGMOD 2016 掲載版そのものでなく arXiv 草稿 v3。** 最初に取った arXiv:1412.2324 は別の論文 (Faleiro, Abadi "Rethinking serializable multiversion concurrency control" = BOHM) だったので破棄し、題名検索で arXiv:1512.06168 を取り直した (BOHM の側は既取得の `bohm-pvldb2015.pdf` があるので使っていない)。
- **Deuteronomy の巻号・頁。** 依頼文の候補 URL `p1228-levandoski.pdf` は誤り (vldb.org の登録簿にない)。vldb.org の巻 8 目次から `p2146-levandoski.pdf` を得た。PDF 本文の版権表記は "Proceedings of the VLDB Endowment, Vol. 8, No. 13"、目次と OpenAlex は 8(13)、頁 2146-2157 で一致。ただし本文の版権行には "42nd International Conference on Very Large Data Bases, September 5th-9th 2016, New Delhi" とあり、年は 2015 (掲載年、Copyright 2015)。
- Deuteronomy の PDF 内で、§1.4 が評価の節を「5.3.1」「5.5.1」「5.5.2」と参照するのに対し、実際の見出しは 5.4.1、5.6.1、5.6.2 で食い違う。カードでは実際の見出し番号を使った。
- Strife の arXiv v1 内で、§1 の箇条書きは高競合 YCSB で「最大 4 倍」、§4.8 の本文は「5 倍」と書き、食い違う。カードは両方を書いた。

## 論文ごとの最適化一覧

### No False Negatives (7 件)
1. `nofalseneg-sgt-txlocal-graph` — protocol-core。transaction 局所 lock の conflict graph による SGT。事前宣言なし、batch・partition 不要 (worker は 1 core 固定・interactive でない試作だが、事前宣言や batch は本文に要求がない)。
2. `nofalseneg-tuple-access-history` — optimization。tuple ごとの局所 sequence 番号と順序付きアクセス履歴。
3. `nofalseneg-node-address-txid` — optimization。node のアドレスを transaction ID にして大域カウンタを避ける。
4. `nofalseneg-delayed-node-deletion` — optimization。commit は許すが入辺が消えるまで node の削除を遅らせ、epoch GC。
5. `nofalseneg-reduced-dfs-cycle-check` — optimization。検査対象部分だけの DFS、共有 lock、最終検査だけ排他。
6. `nofalseneg-online-topological-order` — design-dimension。位相順序維持の O-SGT。評価した全設定で DFS 版に勝てなかったという否定的結果。
7. `nofalseneg-msgt-epoch-readonly-versions` — optimization。epoch 付き snapshot による長い読み専用 transaction 向けの多版拡張 (M-SGT)。

### Strife 前身稿 (5 件、すべて batch と read/write set の事前取得が前提)
1. `strife-batch-clustering-scheduling` — protocol-core。
2. `strife-spot-stage` — optimization。
3. `strife-allocate-stage` — optimization。
4. `strife-merge-stage-alpha` — optimization。
5. `strife-readonly-item-pruning` — optimization。

JSONL に入れなかった候補: analysis と次 batch の重ね合わせ (§4.1 に「実装しなかった」とあり、評価対象の技法でないため)、residual を単一 core で逐次実行する案 (脚注 1 に「複数 core + CC の方が良かった」とだけあり、独立の技法として説明されていないため)。

### ACC (4 件。8 頁のビジョン論文で、評価は予備結果)
1. `acc-domcc-mixed-cc` — protocol-core。cluster ごとに 1 つの protocol を割り当てる混在 CC。事前に触る cluster が分かることを要求 (PartCC の partition lock を Preprocess 段で取るため)。試作は one-shot stored procedure。
2. `acc-protocol-selection-model` — optimization。特徴量と決定木による protocol 選択。
3. `acc-contention-mark-detect-counters` — optimization。記録ごとの counter による競合度推定。
4. `acc-partition-merge-clustering` — optimization。Partition-Merge によるデータ clustering と core 割当て。

JSONL に入れなかった候補: 再 clustering のための階層 (tiered) index (§3 で 1 文触れるだけで、増分の再 clustering は将来課題と明記されているため独立の技法として扱えない)。混在ログ・回復 (§5、「未解決の問い」と明記され技法ではない)。

### Orthrus (5 件)
1. `orthrus-partitioned-functionality` — protocol-core。CC thread と実行 thread の機能分離とメッセージ通信。
2. `orthrus-planned-deadlock-free-locking` — optimization。lock 集合の事前計画による deadlock 回避と OLLP。事前宣言を要する。
3. `orthrus-cc-thread-request-forwarding` — optimization。CC thread による要求の転送 (message 数 2Ncc → Ncc+1)。
4. `orthrus-async-lock-requests` — optimization。実行 thread の非同期 lock 要求。
5. `orthrus-split-partitioned-index` — design-dimension。index を物理分割した Split ORTHRUS の比較。

`requires_predeclared_sets` の付け方: 機能分離そのもの (1) と index 分割 (5) は false。事前計画 (2) と、その順序取得を前提にする転送 (3)・非同期要求 (4) は true (試作の Orthrus は全 lock 集合が分かってから要求する、§3.2)。

### Deuteronomy (5 件。in-memory 多コア専用ではなく、TC/DC 分離と I/O を含む構成)
1. `deut-range-mvcc-ix-lastread` — protocol-core。range の IX 投稿と last-read time による phantom 防止。
2. `deut-logical-range-partitions` — optimization。logical partition による range 資源の粒度選択。
3. `deut-six-scan-and-update` — optimization。SIX access。
4. `deut-tc-dc-scan-merge` — optimization。TC の版と DC の scan の merge による range 生成と増分配送。
5. `deut-timestamp-late-insert-filter` — optimization。DC record の timestamp による late insert の判別。

JSONL に入れなかった候補: range 読みの last-read 時刻による短絡検査 (§3.3.2 の 1 段落の最適化。カード 1 の implementation_gist に含めた)、page 単位の「箱」割当て (§4.4 の実装上の最適化。カード 4 の gist に含めた)。

## 効果分類の分布
cpu-cache 3 件 (Orthrus の機能分離、index 分割、NFN の node アドレス ID)、delay-on-conflict 3 件 (NFN の SGT、Orthrus の deadlock-free 計画と転送)、version-lifetime 2 件 (NFN の M-SGT、Deuteronomy の scan merge)、none 18 件 (Strife、ACC、Deuteronomy の大半、NFN の内部機構)。none の理由は各カードの `effect_category_note` に書いた。

## 数値の出所に関する注意
- 数値はすべて本文の記述から引き、括弧内の図表番号を添えた。図の軸そのものの値は読んでいない。
- ACC の数値 (最大 3.0 倍、4.5 倍など) は合成 workload の予備結果で、8 頁論文の本文にある値。
- Orthrus の比較対象 (2PL・deadlock-free locking) は Orthrus 自身の同一コードベース上の自前実装で、Silo・TicToc など他の公開実装との比較はない。
