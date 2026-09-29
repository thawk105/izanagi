# F-occ-abort-reduction 読みメモ (2026-09-29 JST 10:06-10:30 に取得・読了)

指示めいた文字列: なし (5 本の本文抽出テキストを読み、作業の振る舞いを変えるよう求める文字列は見つからなかった。「ignore」「disregard」等の語の grep も 0 件)

## 書誌・取得元・SHA-256

取得は `curl -sSL -A "izanagi-literature-survey"`。vldb.org は https では接続失敗 (SSL eof / reset) で、http で取れた。ACM DL は Cloudflare の確認頁 (HTML) が返り取れなかった。

| 略称 | 書誌 | 取得元 | 取得時刻 (JST) | SHA-256 |
|---|---|---|---|---|
| BCC | Yuan ほか, PVLDB 9(6) 2016, DOI 10.14778/2904121.2904126 | http://www.vldb.org/pvldb/vol9/p504-yuan.pdf | 2026-09-29 10:07 | d7337b670d5906dd3a8a071d288313333d577bc913c8da1cd6ab66641fb51246 |
| AOCC | Guo ほか, PVLDB 12(5) 2019, DOI 10.14778/3303753.3303763 | http://www.vldb.org/pvldb/vol12/p584-guo.pdf | 2026-09-29 10:07 | 7ed94e6abe929898126971019a616855f464b6a8aa2fff28729b51ee1d155888 |
| Ding | Ding, Kot, Gehrke, PVLDB 12(2) 2018, DOI 10.14778/3282495.3282502 | http://www.vldb.org/pvldb/vol12/p169-ding.pdf | 2026-09-29 10:07 | 41416f64c794c06e129c9781b9d014e925031eeffcf1f6a117ef1c866d7e00c0 |
| TSkd | Cao, Fan, Ou, Xie, Zhao, PACMMOD 1(1) art.26 (SIGMOD 2023) | https://www.pure.ed.ac.uk/ws/portalfiles/portal/360117816/Transaction_Scheduling_CAO_DOA16082022_AFV.pdf (Edinburgh の承認版 (peer reviewed version)) | 2026-09-29 10:08 | 302daeb54d09b69f29fd3bbab6990648980f53946176421d389361d07fcc59a0 |
| HDCC | Hong, Zhao, Lu, Du, Chen, Pan, Zheng, PVLDB 18(5) 2025, pp.1376-1389, DOI 10.14778/3718057.3718066 | http://www.vldb.org/pvldb/vol18/p1376-lu.pdf | 2026-09-29 10:08 | 32834f06f7d82b096ee77984637f497b7f04d6c24b814b0fc3f5b0cbf09f0120 |

置き場は `src/` (PDF、`.txt` は pdftotext 出力、`.layout.txt` は -layout 出力)。カード生成と引用照合は `src/mk_cards_F.py`。

### 依頼文との食い違い
- TSkd の著者は依頼文の「Cheng ほか」ではなく、Cao, Fan, Ou, Xie, Zhao (Edinburgh / Shenzhen Institute of Computing Sciences / Beihang)。Audrey Cheng の "Towards Optimal Transaction Scheduling" (PVLDB 17, 2024) は別の論文で、今回は読んでいない。
- TSkd の DOI は、ACM DL の URL は `10.1145/3588706`、Edinburgh の承認版の表紙は `10.1145/3603164` と印字している。どちらが正しいかは確認していない。カードの locator に両方を記した。
- 取得した TSkd は承認版 (出版版でない) のため頁番号がない。引用の loc は節番号のみ。
- 本文抽出で TSkd と HDCC の数式の文字 (T_i^c など) は数学用イタリック体の Unicode で出る。引用は NFKC 正規化して空白を除いた形で原文と照合し、一致を確認した (カードの引用は ASCII 化した表記)。

### 読んだ節・読んでいない節
- BCC: §1-§6.2 (本文 pp.504-512、Algorithm 1-3、Fig.4-8、Table 1)。未読: §6.3 (latency・memory)、§7 以降。
- AOCC: 要旨、§1-§6 の実験本文 (Fig.1-10 の説明)、§5.3 の正しさ。未読: §6.5 以降、関連研究の詳細。gList の詳細は本文が技術報告に委ねている。
- Ding: 要旨、§1-§5 (Fig.1-28 のうち本文が引く図)、§5.7 の要約。未読: 関連研究。図の数値は本文の文章から取り、図自体は見ていない。
- TSkd: 要旨、§1-§6.4 (Fig.1-6、Table 2 は本文の記述のみ)。未読: 証明の詳細、TsPar の ckRCF (本文で省略)。
- HDCC: 要旨、§1-§4、§5 の要点、§7.2.1-§7.3 の本文。未読: technical report [10] (証明・実装詳細)、§7.4 以降。図は見ず本文の記述から数値を採った。

## 論文ごとの最適化 (JSONL に入れたもの: 計 26 件)

### BCC (5 件)
土台は Silo に BCC と 2PL を実装した自前の拡張 (§5)。Silo に足したメタデータは次のとおり。
- 全 txn に TID を付ける (Silo は書き込み txn のみ) と、thread ごとの最新 TID を並べた global TID vector (実装では socket ごとの sub-vector を cache line に整列)。
- txn ごとの read set hash table (tuple pointer と TID) と thread ごとの history list <TID, Address, Release>。
- read 段には tuple TID と Start の比較 (wr 依存の検出) を追加し、validation 段には write set の tuple TID の比較 (ww)、他 thread の hash table との交差 (rw)、read set 変化 (anti-dependency) の検査を追加。
- カード: bcc-essential-pattern-validation (protocol-core)、bcc-global-tid-vector-clock、bcc-readset-history-hashtable、bcc-readonly-snapshot-sync-point、bcc-multilevel-circular-buffers (cpu-cache)。
- 事前宣言・batch: 不要。ただし snapshot txn の開始時に全 active txn の完了を待つ同期点がある。

### AOCC (5 件)
土台は DBx1000 (Silo でも自前 MVCC でもない)。LRV-OCC を Hekaton/Silo の代理、GWV-OCC を HyPer の代理として自前実装しているため、「Silo に実装した結果」ではない点に注意。
- カード: aocc-query-level-adaptive (protocol-core)、aocc-txn-level-adaptive、aocc-glist-lockfree-circular-array、aocc-threshold-T-fast-selection、aocc-defer-choice-nonpredictable-query。
- 効くのは abort の多さでなく validation 費用 (長い scan の validation)。effect_category は 1 件 cpu-cache (gList、推測を含む) を除き none。
- 事前宣言: query-level は不要。txn-level は実行ロジックが開始前に分かることが前提 (true)。

### Ding ほか (6 件)
土台は自前 Java prototype (storage/validator 分離型)。Cicada と商用 DBMS-X への統合も評価。
- カード: ding-storage-batching、ding-validator-batching-ibvr、ding-thread-aware-reordering、ding-prevalidation、ding-parallel-validator-pipeline、ding-tail-latency-policies。
- storage / validator の batching は batch を要する (batch size 既定 40) が、read/write set の事前宣言は要らない (validation 要求に含まれる)。thread-aware reordering は実行前に batch の access set を解析するため true とした (推測)。
- 数値の食い違い: rdeg による tail latency 削減は §5.3 本文で最大 86%、貢献欄・要旨相当では最大 82%。カードには両方を書いた。

### TSkd (3 件)
土台は DBx1000 (partitioner は Strife/Schism/Horticulture)。batch 内 scheduling と batch でない txn 向けを分けた。
- tskd-tspar-scheduling: batch 内の scheduling。事前の read/write set と実行時間の粗い推定が必要 (true)。
- tskd-tsdefer-proactive-deferment: batch でない txn 向けの proactive deferring。batch は不要だが、他 txn の予測 access set (定数・template からの推定でよい) が要るため true。
- tskd-tsdefer-lockfree-probing: TsDefer の lock-free 進捗追跡と乱択 probe (cpu-cache、推測を含む)。
- effect_category は TsPar と TsDefer を delay-on-conflict とした。TsPar は論文が「runtime conflict の削減」と呼ぶ scheduling であり、3 分類との対応は推測を含む。

### HDCC (7 件)
土台は Deneva 上で Calvin と Silo 型 OCC を統合。shared-nothing の分散が前提。
- カード: hdcc-calvin-occ-hybrid (protocol-core)、hdcc-lock-sharing、hdcc-global-validation、hdcc-two-log-interleaving、hdcc-rule-assignment-o1、hdcc-reschedule-aborted-occ-o2、hdcc-immediate-read-deferred-commit-o3。
- Calvin 側は read/write set の事前宣言と batch が必要 (true とした)。OCC 側は宣言不要で、宣言のない txn は OCC に回る (Rule 1)。lock-sharing / global validation / two-log は Calvin との混在のための機構で単独では意味を持たない。
- 効果の分解 (YCSB, Fig.9a): Half-O1 +0.1 倍、O1 +0.4 倍、O1+O2 3.0 倍、All (O1+O2+O3) 3.3 倍 (いずれも Snapper 型 Baseline 比)。
- 単一ノード・共有メモリ Silo 系の CC 合成に直接使える度合いは低い。O3 (Calvin の未 commit write を読んだ OCC を abort せず待たせる) と O2 (abort 後に read/write set を得て順序付き実行に回す) の発想だけが単ノードに写せる可能性がある (推測)。

## JSONL に入れなかった候補 (理由つき)
- BCC の phantom 対策 (§4.4): Silo の既存手法と同じと本文が述べるため独自の最適化ではない。
- BCC の 2PL 実装 (§5.2): 比較用の対照実装で最適化ではない。
- AOCC の secondary index の有無による Pno_readset 固定 (§5.4): 独立の節を持たない注記。
- Ding の hybrid FVS アルゴリズム、SCC-based greedy、sort-based greedy: ding-validator-batching-ibvr にまとめた (1 件に 3 アルゴリズムを記述)。
- Ding の DBMS-X 統合 (§5.6): 手法の応用例で新しい技法ではない。
- TSkd の TSgen の「partition なしで scheduling」(TSkd[0]): tskd-tspar-scheduling の別設定として扱った。
- HDCC の B+-tree phantom 対策: 本文は lock-sharing で葉 node に lock すると述べるのみ。
- HDCC の Zigzag 変種 checkpoint: Calvin 由来で HDCC 固有の最適化ではない。

## 全体で気づいた点
- 5 本とも、3 分類 (cpu-cache / delay-on-conflict / version-lifetime) のうち version-lifetime に当たる技法はない。none が多いのは、abort 判定の精度・validation の費用・順序付け・混在の正しさを扱う論文群のため。
- 単一ノード・事前宣言なしで Silo に載る候補は BCC の中核 (validation の判定緩和) と、AOCC の方式切替 (ただし DBx1000 上の結果)。Ding の storage batching は versioned datastore と分離構成が前提で Silo に直接は載らない。TSkd の TsDefer は CC を変えず thread-local buffer の順序を変えるだけで載せやすいが、予測 access set が要る。
