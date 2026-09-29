# C-mvcc-engines-gc: MVCC エンジンと GC の最適化カード (7 論文、40 件)

作成: 2026-09-29 JST。読み取りのみ (izanagi repo 無編集・git 操作なし)。JSONL は同名 `.jsonl`。
JSONL の quotes は、抽出テキストとの逐語一致と語数 (15〜60 語) を `src/build_C_cards.py` で機械検査した (curly quote と en dash は
直線記号へ正規化して照合)。

指示めいた文字列: なし (7 本の抽出テキスト全体を「ignore」「you must」「LLM」「assistant」等で grep し、該当は参考文献の人名 Kallman のみ)。

## 共通の取得元と束縛

7 本とも既取得の PDF を読んだ (今回は新規取得なし)。PDF と抽出物は `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/`。
取得は同 wave の別担当 (C1/C2 メモ) が 2026-09-29 03:30〜03:35 JST に行ったもので、取得元 URL は同 wave の
`notes/C1-mvcc-gc.md`・`notes/C2-mvcc-engines.md` の記録による (今回の読み手は再取得していない)。段組を解いた本文抽出
(`pdftotext` 既定) を `src/C-*.nl.txt` に置いた。

| 論文 | 取得元 (先行メモの記録) | SHA-256 (今回 `sha256sum` で再計算) |
|---|---|---|
| Hekaton (hekaton-pvldb2011.pdf) | https://www.microsoft.com/en-us/research/wp-content/uploads/2011/12/MVCC-published-revised.pdf | 0abcc1ff2eb15d2100f9bdca749ed8237a126e756e5c66c13e6f7717af470bdd |
| HyPer MVCC (hyper-mvcc-sigmod2015.pdf) | https://db.in.tum.de/people/sites/muehlbau/papers/mvcc.pdf | af94b3c882ac62189d1fd77ddede4d34b8d8d228a2d59df25ce09db6fa6c3bd2 |
| Steam (steam-boettcher-pvldb13-2019.pdf) | http://www.vldb.org/pvldb/vol13/p128-bottcher.pdf | ceae3ff7928379a76d52ec4dc5e3b71ab5d8e26f8fe69dcf27d075a8d22b40e5 |
| SAP HANA HybridGC (hana-hybridgc-sigmod2016.pdf) | https://15721.courses.cs.cmu.edu/spring2019/papers/05-mvcc3/p1307-lee.pdf (CMU 講義用ミラー。camera-ready と同一内容と先行メモは記す) | e81d952698e8ad1c147073877f2b2df2c3b8ea19676dcde3f7f0d8bf95ea3db0 |
| vDriver (vdriver-techreport.pdf) | https://github.com/hyu-scslab/vDriver/raw/master/vdriver_techreport.pdf (著者リポジトリの **技術報告版**。SIGMOD 2020 camera-ready と本文が同一である保証はない) | 5d24648fc9f79636b9e424dc5702df12088469d69fb8fa284feea6e07cbab3f1 |
| LeanStore SI (alhomssi-leanstore-si-pvldb16-2023.pdf) | https://www.vldb.org/pvldb/vol16/p1426-alhomssi.pdf | c334ca5dcfdbe713bd69430c6a8236a818f1f83436f7ca643d7d8b830837f487 |
| Freitag 2022 (freitag-pvldb2022.pdf) | https://www.vldb.org/pvldb/vol15/p2797-freitag.pdf | dc933deb8243e29ce66da9e3a10a5eb08f194330483cc7336e2c6578d4b90e29 |

## 読んだ節と読まなかった節

- Hekaton: 読んだ = §1、§2.1–2.7、§3.1–3.4、§4.1–4.5、§5.1–5.3、§6。未読 = 正しさ証明 (本文は online addendum を参照し PDF に無い)、§7、参考文献。
- HyPer: 読んだ = 要旨、§1、§2.1–2.7、§3.1–3.2、§4.1–4.4。未読 = §5 関連研究、§6、参考文献。
- Steam: 読んだ = 要旨、§1–§4 (Table 1〜3)、§5.1–5.7。未読 = §6、§7、参考文献。
- HANA: 読んだ = 要旨、§1–§5.6、§6。未読 = 参考文献。
- vDriver: 読んだ = 要旨、§1–§4、§5.1、§5.2.1–5.2.2。未読 = §5.2.3 以降 (分類誤りの影響などの評価)、関連研究の後半。
- LeanStore: 読んだ = 要旨、§1–§3.5、§4 のうち評価設定と Fig. 9–11・out-of-memory breakdown 表・Bulk Loading 冒頭。未読 = §4 の残りと関連研究、結論。
- Freitag: 読んだ = 要旨、§1–§3.3、§4.1–4.2、§4.3.1、§4.3.2 の冒頭。未読 = §4.3.2 の後半以降、§5、§6。
- 全論文共通の限界: 図は画像で軸の値を読めない。カードに書いた数値は本文・表に活字で書かれたものだけで、図由来の数値は書かない。頁番号は PDF 抽出の頁末番号から数えたもので、HyPer と vDriver は頁番号が抽出に無いので節番号のみ。

## 論文ごとの一覧

### 1. Hekaton (Larson ほか、PVLDB 2011): 6 件
- hekaton-mvo-backward-validation (protocol-core, none): 読んだ版が終了時点でも可視かの再確認 + scan 再走査。Table 3 で serializable は RC 比 19.2% 低下。
- hekaton-mvl-pessimistic-locking (protocol-core, delay-on-conflict): 版の read lock と bucket lock。serializable の落ち 10.0%。ただし MV/O より 30% 低い (Fig. 4 の本文)。
- hekaton-speculative-read-commit-dependency (optimization, delay-on-conflict): Preparing 中の tx の版を推測で読み・無視し、待ちを commit 直前へ。単独の ablation は無い。
- hekaton-eager-update-wait-for-dependency (optimization, delay-on-conflict): read lock 済みの版も先に更新し precommit で待つ。単独の ablation は無い。
- hekaton-lock-embedded-in-end-field (optimization, cpu-cache): lock を End の 64 bit に埋め込む。
- hekaton-isolation-level-pay-as-you-go (optimization, none): 分離水準ごとに validation と記録を省く。

JSONL に入れなかった候補: 版の GC (本文が「beyond the scope」と明言。§2.1)。Hekaton の cooperative GC は Steam・HANA の記述から間接的にしか分からず原典に無いので出さない。deadlock 検出 (§4.4、標準的な wait-for graph + Tarjan) は独立の最適化として説明されず、MV/L の一部として card に含めた。

### 2. HyPer MVCC (Neumann ほか、SIGMOD 2015): 6 件
- hyper-inplace-update-undo-buffer-versions (protocol-core, cpu-cache): in-place + undo buffer の before-image delta。
- hyper-precision-locking-validation (protocol-core, none): recentlyCommitted の undo buffer を read predicate と照合。TPC-C の predicate logging は record-level 5%、attribute-level 7%。
- hyper-attribute-level-predicate-log (optimization, none): 属性粒度で偽の abort を減らす。
- hyper-predicate-tree-validation (optimization, none): predicate tree による validation の漸近的高速化。
- hyper-versioned-positions-synopsis (optimization, cpu-cache): 1024 record ごとの synopsis。使わない場合より scan が 5.5 倍超 (§4.1、Fig. 8)。
- hyper-undo-buffer-gc (optimization, version-lifetime): commit ごとの tx 単位 GC。

JSONL に入れなかった候補: write-write 即 abort (§2.3、協議の核の一部なので precision locking card に含む)。index の扱い (indexed 属性の更新を delete+insert とする、§2.5) は版管理の付随事項で独立の名前付き最適化ではない。同期 (§2.7) は短い latch と commit の短い排他区間の記述のみ。

### 3. Steam (Böttcher ほか、PVLDB 2019): 6 件
- steam-eager-pruning-of-obsolete-versions (optimization, version-lifetime): EPO。CH benchmark で 5 倍速く処理し、最大 chain 長が 30287 から 2 へ (Table 5)。
- steam-thread-local-txn-lists (optimization, cpu-cache): thread 局所の tx list と局所最小値の atomic 公開。
- steam-foreground-on-creation-pruning (optimization, version-lifetime): commit 後の foreground GC と、版を作る側が片付ける on-creation pruning。
- steam-version-record-layout (optimization, version-lifetime): Attribute Mask による delta と被覆判定、bulk insert の共有版 record。分類は「保持費用・GC の被覆判定費用」で version-lifetime に厳密には収まらない (推測込み)。
- steam-active-timestamp-set-reuse (optimization, none): EPO の取得費用を 5 ms 周期で償却。
- steam-gc-design-dimensions (design-dimension, version-lifetime): 追跡粒度・頻度/精度・版の置き場・識別・回収の各次元と 8 GC の比較。

JSONL に入れなかった候補: 「読み手の開始を batch して同じ start timestamp を共有させる」案 (§5.3)。著者が「数 % の利得、query latency と引き換え」と述べる試行のみで、名前付き技法でなく、アルゴリズムも示されない。

### 4. SAP HANA HybridGC (Lee ほか、SIGMOD 2016): 7 件
- hana-interval-gc (optimization, version-lifetime): Algorithm 1 の merge 交差。
- hana-group-gc (optimization, version-lifetime): GroupCommitContext 単位の一括回収。
- hana-table-gc (optimization, version-lifetime, requires_predeclared_sets=true): snapshot が触れる table を事前に確定できることが前提。
- hana-hybridgc-combination (optimization, version-lifetime): GT・TG・SI を別周期で起動 (実験は 1 s・3 s・10 s)。
- hana-global-sts-tracker (optimization, version-lifetime): 参照カウント付き順序 list。global mutex による劣位は Steam の主張 (HANA 自身の記述ではないと card に明記)。
- hana-indirect-cid-assignment (optimization, cpu-cache): GroupCommitContext を介した間接 CID 付与。
- hana-is-versioned-flag (optimization, cpu-cache): 版が無い record の hash 参照を省く。

JSONL に入れなかった候補: immediate successor subgroup (§3.2、著者が「beyond the scope」「future topic」と明記した未実装の案)。RID hash table の chained hash 実装 (§2.2) は版管理の付随実装。

### 5. vDriver (Kim ほか、技術報告版): 5 件 (ディスク主体。SIGMOD 2020 版との同一性は未確認)
- vdriver-dead-zone-version-pruning (optimization, version-lifetime): Theorem 3.5 と dead zone による刈り込み。ZT の周期更新を含む。
- vdriver-siro-versioning (optimization, cpu-cache): 最初の旧版だけ in-row。disk 前提のため in-memory への移転は推測と明記。
- vdriver-version-classification (optimization, version-lifetime): hot・cold・LLT の 3 cluster。
- vdriver-segment-cleaning-vcutter (optimization, version-lifetime): segment の v_min/v_max が dead zone に収まる場合に丸ごと削除。
- vdriver-collaborative-cleaning-tas (optimization, delay-on-conflict): TAS の勝者が cleaner と挿入の両方を実行。

JSONL に入れなかった候補: version buffer と Location Lookaside Buffer (vBuffer・LLB、§3.2) は SIRO の探索を速くする実装部品で、独立した ablation が無い。recovery の undo (§3.5) は toggle bit を戻すだけの設計で SIRO card に含む。PostgreSQL・MySQL 個別の実装 (§4.3) は統合作業の記述。

### 6. LeanStore SI (Alhomssi・Leis、PVLDB 2023): 6 件 (out-of-memory 向け)
- leanstore-osic-commit-protocol (protocol-core, cpu-cache): Commit Log と LCB。in-memory 型 (write set への commit timestamp 刻み込み) 比で NoSteal は index 走査が 1.6 倍 (Fig. 11 の本文)。
- leanstore-graveyard-index (optimization, version-lifetime): tombstone を OLTP 経路から外す。
- leanstore-adaptive-version-storage-fattuple (optimization, version-lifetime): Delta Index と FatTuple の切替と OPGC。
- leanstore-separate-oltp-olap-watermarks (optimization, version-lifetime): OLTP 用と全 tx 用の 2 watermark。OLTP/OLAP の区別を上位層が与える前提。
- leanstore-cooperative-gc-worker-lcb (optimization, version-lifetime): worker が自分の版を回収。
- leanstore-early-lock-release (optimization, delay-on-conflict): 既知技法 [15, 28] を実装したもので新規ではない、と card に明記。

JSONL に入れなかった候補: 「先行技法 PGC (Steam の EPO に相当する精密 GC) を LeanStore へ移植した比較対象」(OSIC+PGC、out-of-memory 表) は Steam の card と重複する。durability と recovery の章 (§3.4) は WAL を唯一の真実とする設計で、CC の最適化としては扱わなかった (Early Lock Release のみ card 化)。

### 7. Freitag ほか (PVLDB 2022): 4 件 (ディスク主体。インメモリへ持ち込める技法だけを拾った)
- freitag-local-mapping-tables (optimization, cpu-cache): page ごとの mapping table。移転可能な部分は「版付き page かどうかを page 粒度の 1 か所で判定し、版なし page は分岐なし scan」(HyPer の VersionedPositions と同型、推測)。
- freitag-mapping-table-pruning-on-page-access (optimization, version-lifetime): latch 済みの page access で表を刈る。空 chain の割合が閾値 (例 5%) 超で実行。
- freitag-bulk-op-virtual-versions (optimization, version-lifetime): 物理版なしの bulk 用 virtual version。disk 主体の大 write 向けで in-memory への移転は限定的と card に明記。
- freitag-inplace-vs-append-only-versions (design-dimension, version-lifetime): Table 1 で in-place を止めると TPC-C が 5.13・5.24 倍低下 (Umbra 上の実測)。

JSONL に入れなかった候補: thread ごとの local tx list (Steam の技法の流用、§3.1.4)、Steam の eager pruning の採用 (§3.1.2)、in-place + before-image の基本設計 (HyPer の card と重複)、回復方式 (§3.1.3、WAL のみ)、bulk の検出 (§3.2.3、運用上の判定であり CC の機構ではない)。

## 分類と数値の扱いに関する注意

- effect_category は、GC の技法を version-lifetime とし、commit protocol や lock の置き場のように版の寿命でなく通信・cache に効くものを cpu-cache、待ちの置き場を変えるものを delay-on-conflict、validation の方式や粒度を変えるものを none とした。Steam の version record layout と Freitag の in-place 比較は version-lifetime に厳密には収まらず、card の effect_category_note に理由を書いた。
- 「他論文の主張」として書いた数値 (HANA の global STS tracker が Steam で劣る、など) は、その原典の表・図番号 (Steam Fig. 8) を添えて card 内に出所を区別した。
- vDriver は技術報告版で、camera-ready と同一でない可能性を paper.venue と本メモの取得元表に残した。
- 論文が図だけで示す値 (スループットの絶対値や曲線の形) は図の軸が読めないため、card に書かなかった。書いた数値はすべて本文・表の活字に基づく。
