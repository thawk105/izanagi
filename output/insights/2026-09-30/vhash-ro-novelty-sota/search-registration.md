# VHash の read-only 前進の新規性と SOTA — 事前記述 (追加検索の前に固定する)

- 目的: VHash 論文の主張を「条件 C で、手法 M が、C での SOTA より大きく速い」の形にするため、新しさがどこに残るかと公正な比較相手を、
  性能結果 (並行 wave md_42) と追加検索の結果を見る前に固定する。依頼は並行 VHash wave の md_43。
- 起草: 2026-09-30 (JST)。入力 commit: `908741c6fe1db954c824857ccc2086fe16856d45` (local main)。
- この文書は追加検索 (§4 の R01〜R09) の前の commit に置く。凍結後の変更は末尾の「追記」節にだけ書き、時刻と理由を残す。
- 規則の正本は `docs/related-work/README.md` 7.7 (RW 段階、判定語彙、要裁定を不在側へ倒さない、停止条件を結果前に固定)。
- 既存の検索 N01〜N10 (`output/insights/2026-09-29/vhash-novelty-repositioning/`、以下「md_9」) は取り直さず、その結果を引用して再利用する。
  本 wave の追加分は ID を R で始め、N と混ぜて数えない。
- 本 wave は md_42 (性能結果) の出力を開かない。主張・比較相手を性能結果に合わせて後から変えない。

## 1. 主張

### 1.1 本命 (A) — 逐語

> **読み続ける read-only tx が、既読を保ったまま snapshot を進め、commit 前に版データの保護義務を縮める。**

限定語 (判定で落とさない):

| 記号 | 限定語 | 意味 |
|---|---|---|
| A1 | 読み続ける | 前進の時点で tx はまだ read を発行している (読み取り後に待つだけの tx は含めない。md_9 §3.3) |
| A2 | read-only tx | 書き込みを持たない tx (書き込みを持つ tx の前進は md_9 の U0 が扱った) |
| A3 | 既読を保ったまま | abort・再実行・読み直しをせず、既に読んだ全版が進めた先の時刻でも見える (可視区間に入る) ことを確かめて続ける |
| A4 | snapshot を進め | tx の読み取り時刻 (snapshot) を実行中に後の時刻へ動かす |
| A5 | commit 前に版データの保護義務を縮める | 進めた時刻を tx の終了前に回収側 (GC の保護集合・watermark・保護下限) へ反映し、旧い snapshot でだけ見える版を論理的に回収可能にする |

### 1.2 既知の部分

根拠の階層を分ける: 「本 wave で原典を直接読んだ」/「md_9・md_18 の照合済み記録に依拠 (本 wave で再照合していない)」/「本案に関する論証 (原典の確認ではない)」。

| 部分 | 既知の根拠 (原典の節) | 根拠の階層 |
|---|---|---|
| A3 + A4 の骨格 (実行中に読み取り時刻・有効区間を後へ動かし、既読との整合を確かめて続ける) | CockroachDB SIGMOD 2020 §3.3–3.4 (read refresh。契機は衝突・時計の不確かさ)。SI-STM TRANSACT 2006 §3.1–3.2 / LSA DISC 2006 §3.2 (有効区間の上端の延長。SI-STM の契機は区間が空になったとき) | md_9 §3.1・K15・K16 に依拠。本 wave の読み取り役の抽出 (extract-R2) で延長の逐語を再確認 |
| A5 の目的 (位置を新しい側へ寄せれば古い版を早く捨てられる) | SI-STM TRANSACT 2006 §3.1 | md_9 K20 に依拠 |
| 既知の GC 境界規則 (回収境界 = 実行中 tx の時刻の最小)。**前進した tx の保護時刻を commit 前に公開すること (A5) は、この根拠では未確認** | Hekaton SIGMOD 2013 §8.1、Cicada SIGMOD 2017 §3.8 | md_9 K17 に依拠 |
| 長い読み手がいても、どの snapshot からも見えない途中の版を回収する (読み手を動かさずに保護義務を縮める) | Steam PVLDB 2019 §4.3、SAP HANA HybridGC SIGMOD 2016 定義 1、vDriver (Long-lived Transactions Made Less Harmful) 定理 3.5 | md_18 (`output/insights/2026-09-29/vhash-interval-gc/README.md` §2) に依拠 |
| 読み手の開始時刻を揃えれば chain に 1 版だけ残せばよい。人工的に query を遅らせて開始時刻を共有させる案の評価は「数 % の向上、query 待ち時間の増加と引き換え」 | Steam PVLDB 2019 §5.3 (逐語は §6) | 本 wave で親が原典を直接読んだ |
| 長い tx を走らせる worker は回収用の epoch を定期的に更新すべき (直列化位置は動かさない) | Silo SOSP 2013 §4 | md_9 K18 に依拠 |
| (論証) 読み取り後に待つ tx の保持は、アクセス駆動の前進では縮まない | — | 本案に関する論証 (md_9 §3.3)。原典の確認ではない |

### 1.3 新しいと考える部分 (仮説。本 wave で検査する)

- **N-A:** A1〜A5 を同時に満たす機構 — 読み続ける read-only tx が、abort せず既読を保ったまま snapshot を進め、その前進を commit 前に回収側へ公開する — と、
  その前進の確定と公開の順序 (md_9 の小モデル R6→R7、D2290 の SP)。
- **N-A の SOTA 差 (仮説):** 区間 GC (Steam / HANA / vDriver 型) は読み手の snapshot を動かさないので、固定 snapshot の読み手がその後に読みうる
  各キーの可視な値を再構成できる情報は残る (原典は「各キー最大 1 版」とは書かない。複数の読み手が同じ版を共有でき、Steam の属性別 before-image も
  単純な 1 版ではない)。N-A は前進に成功した範囲で、その旧 snapshot だけのために必要だった情報の**論理的な**保持義務を減らしうる。
  **物理的な解放** (bytes・RSS・再利用) は、読み手が既読版への参照を持つ限り N-A にも区間 GC にも同じ制約がかかる (Steam は unlink と解放を分けて解放を
  所有 tx の解放まで遅らせる、D2323 の Cicada 試作でも安全な解放は長い tx 自身が塞いだ)。
  Steam 自身は開始時刻を揃える案 (実行中ではなく開始時) を評価し「数 %」と報告しているが、これは TPC-C / CH 系の OLAP 読み手を人工的に遅らせる案の性能差であり、
  N-A の保持削減の上限でも見込み値でもない (§5.2 K3)。

### 1.4 別の主張 U1′ (従) — cold 進入を前進の契機にする

> 版探索の費用 (版の列の深さ・置き場所・cache miss) を、tx の timestamp を調整する判断の入力に使う。

md_9 の U1 と同じ主張を「timestamp の調整」と「版探索の費用」の対応として式を分けて検索する (R06)。md_9 の N06〜N08 の結果は再利用する。

## 2. 検出条件 (判定規則)

md_9 の判定語彙と理由コードを使う (検出 / 近傍 / 除外 X1〜X4 / 要裁定)。

- **A の検出:** read-only tx (または、read-only tx にも同じ規則が適用されると原典で確認できる全 tx 向けの機構) が、既読を持つ状態で、
  abort・再実行・読み直しをせず既読の全版が進めた先でも見えることを保ったまま snapshot を後の時刻へ進め、**その後も同じ tx で read を続け** (A1)、
  進めた時刻を tx の終了前に回収側 (GC の保護集合・watermark・保護下限) へ反映する (A5)。A5 は旧版が直ちに物理的に削除されることまでは要求しない。
- **要裁定 (A 固有):** 前進の契機が read であることは分かるが前進後の read の継続が確かめられない候補。要旨で A3・A4 を満たすが A5 の有無を要旨で決められない候補
  (本文で「回収へ反映しない」と確認できたものだけを近傍に移す)。全 tx 向けの機構で read-only tx への適用が要旨で決められない候補。
- **A の近傍:** A3〜A5 の一部だけで、欠ける部分が要旨または本文で確認できるもの (例: 前進するが回収へ反映しないと本文で確認 = read refresh・LSA 型、
  回収するが読み手を動かさない = 区間 GC 型、snapshot を文 (statement) ごとに取り直すが既読を保たない = read committed 型、開始時刻を揃える = Steam §5.3 型、
  読み手を abort・失効させる)。
- **U1′ の検出:** tx の timestamp (snapshot・直列化位置) を、abort せずに調整する判断に、版探索の費用 (版の列の位置・深さ・置き場所・cache miss・記憶階層) を入力として使う。
- **U1′ の近傍:** 逆向き (時刻 → 置き場所: 版の配置を時刻・可視区間で決める)、版探索の費用を下げる工夫で timestamp を動かさないもの。
- **要裁定:** 要旨が無く題名と掲載先で決められない、または要旨で決められない。**要裁定を不在側へ倒さない。**
- 判定は要旨 (OpenAlex の要旨、無ければ Semantic Scholar の要旨・自動要約・出版社頁) の範囲。本文を読むのは §5 の比較表の対象と、検出・要裁定の候補だけ。

## 3. 索引・母集合・打ち切り

- **索引:** OpenAlex (`title_and_abstract.search`、題名 + 要旨)、arXiv (`all:`)、DBLP (md_9 と同じ全件書き出し `dblp.xml.gz`、
  SHA-256 `4ed8c4614244b755e9c1ef45f97b1d9166703aa32acf19442f532d69539caf01`、Last-Modified 2026-09-28 20:23:37 GMT、題名の手元照合)。
- **実行器:** md_9 の repo 外スクリプト (`/work/1/SFC/tanab/tmp/vhash-novelty-2026-09-29/tools/`、`SHA256SUMS` 記録済み) を変更せず、
  新しい `queries.json` (本 §4 の式を機械展開したもの) を渡して使う。新しい検索の道具は作らない。
- **打ち切り (結果の前に固定):**
  - OpenAlex: 1 走の request 予算 80、要求間隔 6 秒、429 は retryAfter + 5 秒で最大 5 試行、取れなければその式は未完走。
    未完走の式は、10 分以上空けて同じ式のまま 1 式ずつ 1 回だけ再走する (再走は元の証拠を上書きしない別 dir)。再走でも取れなければ未完走で確定。
  - arXiv: 要求間隔 3.5 秒、非 200・空本文・`totalResults` 欠落はその式を未完走。再走規則は OpenAlex と同じ。
  - DBLP: 書き出しの全 record を走査。
  - 宣言総数が 800 を超える式は `incomplete-oversize` = 未完走とし、結果を見て式を絞り直さない (絞るなら別 ID で理由と時刻を残す)。
  - 件数の事前確認 (live preflight): 凍結前に OpenAlex・arXiv の宣言総数だけを取り (題名・要旨は見ない)、800 超の式は凍結前に直す予定だった。
    **実際には取れなかった:** 2026-09-30 22:30〜22:40 JST、OpenAlex の匿名検索は HTTP 503 (`"Anonymous search is paused while the search cluster recovers from heavy load."`)、
    arXiv API は自明な式 (`all:mvcc`) でも HTTP 500 を返した。OpenAlex の単体取得 (`/works/<id>`) は 200。したがって本登録は件数を見ずに凍結する。
    800 超の式は上の規則どおり未完走とし、絞った式を足すなら別 ID で理由と時刻を残す。無料 API key はメール登録が要るので作らない。
  - **索引の停止時の扱い:** 503・500 など索引側の停止が続く間は本走を始めない。30 分以内に 1 回、主題と無関係な 1 request で再開を確かめ、
    両索引が応答したら本走を始める。**2026-10-01 03:00 JST までに再開しない索引の枝は未完走で確定**し、その索引についての不在の文は書かない
    (DBLP は手元の書き出しなので停止の影響を受けない)。
- **索引ごとの式の意味の差:** 同じ式 ID でも 3 索引の集合条件は同じではない。OpenAlex には展開後の文字列をそのまま `title_and_abstract.search` に渡す
  (句は語幹化される。md_9 の構文確認で AND / OR / 括弧 / 句が効くことを確かめた。実行器は解釈の同一性を検証しない)。arXiv は各語・句を `all:` に変換する
  (題名・要旨以外のフィールドにも当たりうる)。DBLP は題名の語の前方一致と、句の語ごとの前方一致である。凍結時に全式の完全展開文字列と実際の request URL
  (実行器の `--dry-run` 出力) を `queries.json` と `dry-run-urls.txt` に保存する。「同じ意味の検索を 3 索引で行った」とは書かない。
  保存先は repo 外 `/work/1/SFC/tanab/tmp/vhash-ro-novelty-sota-2026-09-30/search/` (実行器の入力なので repo に置かない)。凍結時の SHA-256:
  `queries.json` `5121345695e0ec64f86393c81aefa6b47ae1d4f815e25a512bdad89793b71a6d`、`dry-run-urls.txt` `a986958e2ea4578493c3a1c3ab66c4a250d2eb0e0a00957c700e1364f40d5320`
  (展開元の `spec.json` `998602ce2cdcbcc2c58fe3c58a08c0a7065ee86232679d752719948db46094c5`。展開は §4.1 のブロック名を括弧つきの中身へ置き換えるだけで、
  全式が実行器の `qlang.parse` を通ることを確かめた)。
- **構文の生死確認 (本走の直前、索引の再開後):** 主題と無関係な語で `a OR b AND c` と `(a OR b) AND c` の宣言総数が OpenAlex で異なること、
  ハイフン句 `"read-only"` と空白句 `"read only"` の宣言総数を記録する (解釈の差の記録であって、式の変更には使わない)。
- **使い方:** A について「見当たらなかった」と書けるのは、A を支える式 (§4) が 3 索引すべてで完走し、A の検出 0 かつ要裁定 0 のときだけ。
  その文には索引名・式 ID・cutoff を同じ文に置く (RW2)。U1′ も同じ。
- **成熟度の予定:** 索引別の RW2。RW3 は名乗らない (registration preflight で実行器の bytes を登録に束縛していない、DBLP は題名だけ、判定は要旨の範囲)。

## 4. 検索式と主張の対応

### 4.1 概念ブロック

- **SA** (snapshot を進める): `(snapshot AND (advance OR advancing OR advancement OR refresh OR refreshing OR renew OR renewal OR extend OR extending OR extension OR "move forward")) OR ("read timestamp" AND (advance OR advancing OR forward OR refresh OR bump OR push)) OR "read refresh" OR "lazy snapshot" OR "validity interval" OR "timestamp extension"`
- **RO** (読み続ける読み手): `"read-only" OR "read only" OR "long-running" OR "long-lived" OR "long running" OR "long lived" OR OLAP OR HTAP OR analytical OR "long transaction" OR "long transactions" OR "long query" OR "long queries" OR scan`
- **GC2** (回収): `"garbage collection" OR "garbage collector" OR reclamation OR "version retention" OR "version pruning" OR "version cleanup" OR watermark OR vacuum OR purge`
- **MV** (md_9 と同じ): `multiversion OR "multi-version" OR MVCC OR "version chain" OR "old version" OR "older version"`
- **CX** (md_9 と同じ): `concurrency OR serializability OR serializable OR transaction OR transactions OR database`
- **TS** (md_9 と同じ): `(timestamp AND (forward OR forwarding OR advance OR adjust OR adjustment OR reassign OR reassignment OR shift)) OR "serialization order" OR "timestamp range" OR "timestamp interval" OR "dynamic timestamp" OR "order forwarding" OR "commit timestamp"`
- **VC** (版探索の費用): `"version chain" OR "version chains" OR "version traversal" OR "version search" OR "version lookup" OR "chain length" OR "cache miss" OR "cache misses" OR "pointer chasing"`

### 4.2 式

| ID | 式 | GC の語 | 支える主張 |
|---|---|---|---|
| R01 | (SA) AND (GC2) AND (CX) | 必須 | A |
| R02 | (RO) AND (GC2) AND (MV) | 必須 | A |
| R03 | (SA) AND (RO) AND (CX) | なし | A |
| R04 | (SA) AND ((MV) OR "snapshot isolation" OR "transactional memory" OR serializability OR serializable) | なし | A |
| R05 | ("read-only transaction" OR "read-only transactions" OR "read only transaction" OR "read only transactions") AND ("snapshot isolation" OR (MV)) AND (serializable OR serializability OR "safe snapshot" OR freshness OR staleness OR stale) | なし | A |
| R06 | ((TS) OR (SA)) AND (VC) | — | U1′ |
| R07 | ("read view" OR "serialization interval" OR "serialization point" OR "validity window" OR "read time" OR "start timestamp") AND ("oldest active" OR "safe point" OR "low watermark" OR "obsolete version" OR "obsolete versions" OR (GC2)) AND (MV) | 必須 (別語を含む) | A |
| R08 | ("validity interval" OR "snapshot of the future" OR "snapshot extension" OR (snapshot AND (extend OR extension))) AND ("old version" OR "old versions" OR discard OR reclaim OR reclamation OR "garbage collection") AND ("transactional memory" OR STM) | 必須 (STM の語) | A |
| R09 | ("long-running reader" OR "long-running readers" OR "long-lived reader" OR "long-lived readers" OR "read transaction" OR "read transactions" OR "analytical query" OR "analytical queries") AND (SA) AND ((MV) OR "transactional memory") | なし | A |

- A を支える式は R01〜R05 と R07〜R09 (GC の語を必須にする R01・R02・R07・R08 と、しない R03〜R05・R09)。U1′ を支える式は R06 と、再利用する md_9 の N06〜N08。
- R07〜R09 は、前進を `snapshot` と呼ばない文献 (read view・区間・read time)、回収を `garbage collection` と呼ばない文献 (oldest active・low watermark・obsolete)、
  STM の用語、`read-only` と呼ばない読み手を拾う狭い枝である (段 3 相当の相談 A の指摘)。`reader`・`query` 単独は件数が爆発しうるので足さない。
- md_9 の N01〜N05 (U0) は A の上位の主張 (書き込みを含む全 tx) についての結果であり、A の判定にも近傍として引用するが、A を支える式の完走条件には数えない。

### 4.3 陽性対照 (期待する式と索引。結果の前に固定)

期待は、凍結前に各対照の OpenAlex レコードを DOI で単体取得し (検索結果ではない)、要旨の語が各ブロックを満たすことを確かめて置いた
(取得物は repo 外 `controls/`)。

| 対照 | 期待する式 | 各ブロックを満たす要旨・題名の語 (OpenAlex) | OpenAlex | arXiv | DBLP (題名) |
|---|---|---|---|---|---|
| Böttcher ほか 2019 Steam "Scalable Garbage Collection for In-Memory MVCC Systems" (10.14778/3364324.3364328、W2982402713) | R02 | RO: "long-running"・HTAP / GC2: "garbage collection" / MV: MVCC | 出現を期待 | 期待せず | 期待せず (題名に RO の語が無い) |
| Lee ほか 2016 SAP HANA "Hybrid Garbage Collection for Multi-Version Concurrency Control in SAP HANA" (10.1145/2882903.2903734、W2441046553) | R02 | RO: "long-lived"・OLAP / GC2: "garbage collection" / MV: MVCC・"multi-version" | 出現を期待 | 期待せず | 期待せず (題名に RO の語が無い) |
| Kim ほか 2020 vDriver "Long-lived Transactions Made Less Harmful" (10.1145/3318464.3389714、W3032843849) | R02 | RO: "long-lived" / GC2: "garbage collection" / MV: MVCC | 出現を期待 | 期待せず | 期待せず (題名に GC・MV の語が無い) |
| Ports・Grittner 2012 "Serializable Snapshot Isolation in PostgreSQL" (10.14778/2367502.2367523、W2139285682) | R05 | "read-only transactions" / "snapshot isolation" / serializable | 出現を期待 | 期待せず | 期待せず (題名に read-only の語が無い) |

- **取りこぼし対照 (出ないことを期待):** CockroachDB SIGMOD 2020 (W3031917602) は要旨に read refresh・snapshot の前進の語が無いので、どの式にも出ない見込み。
  LSA DISC 2006 (W1523021320) は OpenAlex に要旨が無く、題名 "A Lazy Snapshot Algorithm with Eager Validation" だけでは R04・R08 の第 2 ブロックを満たさない。
  この 2 本は A3 + A4 の骨格を持つ既知の近傍であり、登録検索で拾えない型の実例として記録する (§5 の比較表では原典を直接読む)。
- 判定は md_9 と同じく題名の正規化文字列の包含で機械判定し、親が目で確かめる。**陽性対照の通過は網羅の証明にならない** (A を満たす既知の文献は存在しないので、
  検出に近い陽性対照は置けない。置けるのは近傍の対照だけである)。

## 5. 比較表と推奨の判定基準 (結果の前に固定)

### 5.1 比較表の対象と列

対象の最低限 (依頼の指定): Steam (開始時刻を揃える案を含む)、SAP HANA の区間 GC、vDriver (= Long-lived Transactions Made Less Harmful)、DIVA、OneShotGC、
LSA / SI-STM、CockroachDB の read refresh、Hekaton、TicToc、SSI の safe snapshot (Ports・Grittner 2012)。
加えて比較の基準として **本案 M 自身、ro-gcflag 修正入りの最良設定 Cicada、stock Cicada** の行を置く (D2322 項 2)。
知識による補助探索で足す候補 (7.7.6 の補助探索): Silo の snapshot epoch、Cicada、ERMIA、read committed の文ごとの snapshot、
PostgreSQL / Oracle の長い snapshot の扱い (md_27 の製品文書)、Mühe ほか CIDR 2013、YugabyteDB の read restart、JVSTM / SMV (多版 STM の GC)。
依頼の最低限の対象と、K2 の対抗候補になりうるもの (DIVA・OneShotGC・製品方式) は、本文を読めなくても「未確認」の行として残す。

列 (依頼の 6 列): **読み続けてよいか** / **既読を保つか** / **将来の書き込みへの対処** / **論理的な回収** / **物理的な回収** / **費用**。
各セルは原典の節 (と短い逐語) を持つ。本文を読めていないものは「未確認」のまま残す。
「費用」は別表で分ける: read / write / GC の CPU・同期、abort・再実行の有無、開始の待ちと尾部遅延、論理版数・鎖長、退役待ちの bytes・RSS。
原典が数値を書く場合は負荷・方式・測定量を併記し、方式間で数値を並べて比べない。

### 5.2 推奨の判定基準

- **条件 C の書き方 (結果の前に固定):** 主条件 C は「更新と並行して読み取りを続け、前進の候補となる read を発行する長い read-only tx」とする。
  読み取り後に待つ tx (閉じない cursor・対話的な待機) は、read 契機の M が効かない**境界条件**として別に示し、C から黙って外さない。
  GC の要求で待機中に前進する安全点 (SP、ストーリー §5.1) は別の機構・別の主張として扱う。C の用途・read の間隔・待機時間・既読量の値は評価計画 (md_40 の所有) が決め、本 wave は決めない。
- **K1 (新しさの残存):** 同一方式の同一構成で A1〜A5 がすべて成立するもの (§2 の検出) が 1 つでもあれば、A は既知として「採用しない」。
- **K2 (SOTA の選び方):** C と同じ読み取り保証 (直列化可能、読み手は abort されず既読を保つ) を満たす公表済み方式を候補に挙げ、
  論理版数・鎖長 (読み手の探索 hop)・更新側の費用・追加メモリ・物理解放の遅れを原典の範囲で比べて、C で最も強い候補を SOTA とする。
  保証を変える方式 (読み手の失効・abort・文ごとの snapshot の取り直し・snapshot を待たせる方式) は、その変更と費用を明示した別の対抗候補とする。
  直接実装する相手は「候補の強さ」と「CCBench への移植の忠実度」を別々に記録して選び、移しやすさで SOTA の名を別の方式に移さない。
  区間 GC はこの時点では有力候補であって SOTA の確定ではない。ro-gcflag 修正入りの最良設定 Cicada (D2302・D2322 項 2) は直接比較の基準腕として残す。
- **K3 (勝ち筋の存在):** 原典の記述だけから (本案の性能値を見ずに)、M が同じ保証の最強候補より減らせる対象を「どの版を・どの時点で・どの操作で」の形で特定する。
  **論理** (論理生存版数・鎖長・探索 hop・将来の割当量) と **物理** (bytes・RSS・再利用) を分け、物理の改善は参照の退役条件を満たすことを直接確かめた場合だけ主張する
  (区間 GC と M に同じ退役規則を当てる)。原典の数値 (Steam §5.3 の「数 %」など) は負荷・方式・測定量を併記して引くだけで、M の効果の閾値には使わない。
  特定できれば推奨し、構造上の余地しか示せない部分は「仮説」と書く。特定できなければ「残る差が弱く採用しない」とする。
  数値の成功閾値 (「大きく速い」の大きさ) は本 wave では置かず、評価計画 (md_40) の事前登録に委ねる。
- **K4 (直接比較の可否):** SOTA の実装が公開されているか、CCBench へ移すときの差分と未実装の機能を列挙する。忠実な移植が無い場合、比較の主張は「我々の移植した X」に限る。
- **K5 (数値の引用):** 他論文の throughput の数値を引くだけでは SOTA に勝ったとは言えない (実装・負荷・機体が違う)。
  勝ちの主張は、同一負荷・同一機体・同一測定窓の同時刻の直接比較でだけ書く。

## 6. 起草時に読んだ逐語 (検索の前)

- Steam PVLDB 2019 §5.3: "Ideally, all transactions started at the same time and Steam only needs to keep one version per chain. This can be achieved by batching the start of readers in groups (similar to a group commit)."
- 同: "An evaluation of this idea showed gains of a few percents—at the cost of increased query latencies."

## 7. 凍結前の敵対相談と採否

草稿 v1 を別系統モデル (read-only、段 3 相当) 2 本に攻撃させ、凍結前に直した。出力は repo 外 (`/work/1/SFC/tanab/tmp/vhash-ro-novelty-sota-2026-09-30/codex/consult-a/out.md`・`consult-b2/out.md`)。

- 相談 A (検索の網羅と検出条件): 8 件すべて採用 — A1 の検出条件を「前進後も read を続ける」に揃えた (§2)、全 tx 方式は read-only への適用を確認できた場合だけ検出、
  要旨で A5 を決められない候補は要裁定 (§2)、別語の狭い枝 R07〜R09 (§4.2)、索引ごとの式の意味の差 (§3)、陽性対照の語の充足と取りこぼし対照 (§4.3)、
  §1.2 の根拠の階層、K2 を移しやすさで選ばない (§5.2)。
- 相談 B (判定基準と比較相手の公正さ): 6 件すべて採用 — K2 で区間 GC を SOTA と先決めしない、C と待機型の境界の書き方、「各キー最大 1 版」の読みを原典どおりに直す (§1.3)、
  論理の回収と物理の解放を分ける (K3)、Steam の「数 %」を閾値にしない (K3)、表に M・修正入り Cicada・stock を加え費用を分解し、K1・K4・K5 の判定単位を明記 (§5)。
  相談 B の 1 回目は相談役の出力に原典の非 NFC 文字が混ざって起動器に不受理 (event_invalid) になり、NFC の写しを渡して再投入した (内容の採否には影響しない)。

## 追記

(凍結後の追記はここにだけ、時刻と理由つきで書く)

- **2026-10-01 00:02 JST — arXiv の「停止」の観測の訂正 (式・対応・判定規則・打ち切りは変えない)。** §3 に書いた「arXiv API は自明な式 (`all:mvcc`) でも HTTP 500」は、
  件数だけを取るために `max_results=0` を付けた request の応答だった。同じ式で `max_results=1` は 200 を返す (00:01 JST に確かめた)。つまり arXiv は凍結時にも検索でき、
  500 は私の確認手順 (`max_results=0`) の欠陥だった。再開確認の script (repo 外 `probe-resume.sh`) も同じ欠陥を持っていたので止め、OpenAlex だけを確かめる版に替えた。
  arXiv の本走は、凍結時と同じ実行器・同じ `queries.json` (SHA-256 は §3) で 00:02 JST に始めた。本走の実行器は `max_results=200` を使うのでこの欠陥の影響を受けない。
  OpenAlex は 00:00 JST の確認で 503 から 429 に変わった。§3 の停止時の扱い (両索引の応答を待つ) は OpenAlex についてだけ残る。
  **逸脱:** §3 は「両索引が応答したら本走を始める」と書いたが、arXiv だけを先に始めた。索引ごとの取得は互いに独立で、取得した結果は OpenAlex の本走の開始と判定に使わないので、
  結果への影響は無いと判断した (判定は全索引の取得が終わってから行う)。
- **2026-10-01 00:15 JST — OpenAlex の本走。** 00:14 JST に主題と無関係な 1 request で 200 を確かめ、00:15〜00:19 JST に本走した (9 式すべて complete、request 14)。
  §3 の構文の生死確認は 1 件目の後が 429 で取れず、式の解釈の差は記録していない。§3 の期限 (03:00 JST) には達していない。
