# D: LSA (Riegel-Felber-Fetzer 2006) の 7 項目

書誌 (Crossref で確認済み):
- DISC 論文: Torvald Riegel, Pascal Felber, Christof Fetzer, "A Lazy Snapshot Algorithm with Eager Validation", DISC 2006, LNCS 4167, DOI 10.1007/11864219_20。題名・年とも依頼どおり。読んだ版は著者 (Felber) の公開ページの PDF (pdfinfo で 15 ページ、`retrieval/pdf/lsa-disc06.pdf`)。
- TRANSACT 論文: Riegel, Fetzer, Felber, "Snapshot Isolation for Software Transactional Memory", TRANSACT 2006 (Crossref に DOI なし)。読んだ版は同じく著者の公開ページの PDF (`retrieval/pdf/lsa-transact06.pdf`)。著者順は原典では Riegel, Fetzer, Felber (依頼どおり)。
- 記法: 原典の R_T' = [min, max] (DISC) / V_T = [min_T, max_T] (TRANSACT)。以下では区間 [min, max] と書く。
- 引用は pdftotext の出力と空白を正規化して照合済み。用語の対応: 原典の "most recent" = 最新版。

## 1. 論文 1: DISC 2006 (LSA 本体、ほぼ単一版 + 「残っていれば旧版」)

読んだ節: 1, 2, 3.1 から 3.5, Algorithm 1 (疑似コード)、4 の冒頭。

| 項目 | 内容 |
|---|---|
| 位置 π(T) | 区間 [T.min, T.max] (暫定の validity range R_T')。開始時に [CT, ∞] とし、版を読むたびに、読んだ版の validity range と交差を取って縮める。最新版を読んだときの上端は「今の CT」で暫定。update tx は commit 時に一意の commit 時刻 CT_T を取り、区間が CT_T - 1 を含むことを確かめる。 |
| 契機 | (a) read/write (Open) 時: 最新版の作成時刻 > T.max のとき、update かつ open なら Extend を試みる。(b) commit 時: update tx が T.max < CT_T - 1 なら Extend を試みる。原典は「延長は正しさに必須でなく、適した版が見つかる確率を上げるだけ」と述べる。 |
| 向き | 下端 min は単調に増える (読んだ版の作成時刻へ)。上端 max は Extend で「今の CT」へ後ろへ伸びる。読んだ版の交差なので区間が縮む側にも動く (交差)。区間が空になると保てない。 |
| 読む版の選択 | 原則は「まだ存在し、かつ snapshot を一貫に保つ最新の版」。最新版が T.max より新しく延長もできないとき、read-only tx は T.max で有効だった旧版を読み、tx を "closed" (以後延長不可) にする。update tx は最新版しか読めず、それが無理なら abort。旧版が無ければ abort。 |
| 既読維持の判定 | 既読の版を毎回検査し直さず、区間の不変条件で保つ。Extend は、既読の各オブジェクトの「暫定上端」を再計算して max を取り直す (その版が今も最新かの確認)。update tx は commit 時に区間が CT_T - 1 を含むこと (Theorem 2)。write は visible な印 (write marker) で競合を検出。保証できないとき abort。 |
| GC への反映 | 「読んだ節には無い」。原典は「システムは最新版を常に保持する。加えて、まだ GC されていない旧版を使えることがある」と書くのみで、何個保持するか・何を境界に回収するかの規則は記述なし (読んだ節: 3.2、4 の冒頭)。 |
| 長い tx / 読み取り後に止まっている tx | 明示の記述なし。関連するのは 3.5 の議論: 同時 update が増えても、tx が触るオブジェクトに更新がなければ最新版は不変で延長は要らず、延長は最大でオブジェクトごとに 1 回。 |
| 版の置き場所・アクセスコストを選択の契機にしているか | していない (読んだ節: 3.2, 3.5)。版の選択は validity range の重なりだけで決まる。コスト議論は「CT 参照回数が少ない」(3.5) と「全既読の再検証を避ける」ことに向いている。 |

根拠の逐語 (節番号つき):

> "When a transaction T is started, we set RT0 to [CT, ∞]"  (3.2)

> "Note that this is not required for correctness—it only increases the chance that a suitable object version is available."  (3.2)

> "LSA assumes that a system always keeps the most recent version of an object."  (3.2)

> "LSA tries to select the newest object version from Hi that still exists and that keeps the snapshot consistent"  (3.2)

> "we might still read some older version whose validity range overlaps RT0"  (3.2)

> "If no such version exists anymore, the transaction needs to be aborted."  (3.2)

> "which have not yet been garbage collected"  (3.2)

> "Update transactions can only commit if their validity range and their unique commit time"  (3.3)

> "Update transaction must access most recent versions"  (Algorithm 1, Extend の行 35 のコメント)

> "the validity of snapshots is fixed to the start time of a transaction and is not extended on demand"  (2、Dice らの TL2 系との対比)

日本語要約: LSA は「tx の snapshot が有効な区間」を持ち、区間の上端を必要になったとき (最新版が上端より新しい read、または commit) にだけ延長する。延長は既読オブジェクトの上端を取り直すだけで、全既読の値の再読みはしない。read-only tx は延長しても足りないとき、旧版が残っていればそれを読める (以後その tx は延長不可)。update tx は最新版だけを読む。旧版の保持数と回収規則は本論文にはない。

## 2. 論文 2: TRANSACT 2006 (多版・snapshot isolation 版 SI-STM)

読んだ節: 1 (冒頭)、2.2、3 (3.1 から 3.3)、4.1 から 4.4、6 (評価)、7。

| 項目 | 内容 |
|---|---|
| 位置 π(T) | 区間 V_T = [min_T, max_T]。tx が読む各版の validity 区間の交差。最初のアクセス時刻 first_T に対し max_T >= first_T を保証し、min_T > first_T もありうる (「未来の snapshot」)。実効開始時刻 = max(first_T, min_T)。update tx は commit 時に一意の commit_T を取る。 |
| 契機 | 読む版が既存の区間と重ならず、区間が空になるとき Extend を試みる (abort 頻度を下げる目的)。加えて、線形化 (linearizability) を求める場合は commit 前に区間の延長を試みる。先行的な延長 (proactive extension) は将来課題と明記。 |
| 向き | min は増える方向、max は暫定上端の再計算で後ろへ延びる。区間は交差で縮む。 |
| 読む版の選択 | 「最新版から順に探し、tx の区間と重なる最初の版を選ぶ」。旧版を新たに読める (多版)。区間が空のまま延長もできなければ abort。write は現行 (最新) 版が tx の区間に重なることを要求し、重ならなければ (延長後も) 失敗する。 |
| 既読維持の判定 | 区間の不変条件 (各版は min_T 以前に commit され、区間内に別版の commit が無い)。read 時に locator の変更も既読の再検証も要らない、と明言。延長では未確定の上端を再計算。SI では write/write 競合を contention manager が first-committer-wins で解決。 |
| GC への反映 | 版の個数上限で保持を決める: 測定では各オブジェクトに小さな数 k の旧版を保持、実装では locator に n 個の旧版 (n は典型的に 1 から 8)。将来は固定個数の weak reference にして、JVM の GC に回収を任せる予定。境界は tx の開始時刻や π(T) には結ばれていない (個数と JVM のメモリで決まる)。最新性を求める動機の一つに「旧版を早く捨てられる」がある。 |
| 長い tx / 読み取り後に止まっている tx | 結論部で長い tx の負荷で良い性能と述べる。旧版が個数上限で捨てられた後に古い区間の tx が戻ると、交差が空になり abort しうる (原典は「十分長い履歴があれば区間は空にならない」と条件つきで述べる)。止まっている tx への特別な扱いは記述なし。 |
| 版の置き場所・アクセスコストを選択の契機にしているか | していない (読んだ節: 3.2, 4.4, 6)。選択は区間の重なりだけ。コストの議論は検証コスト (二乗になる再検証の回避) とタイムスタンプ用の中央カウンタの競合に向いている。 |

根拠の逐語:

> "we can actually take a snapshot of the future"  (3.1)

> "we look for the most recent version ovi with a validity interval V that overlaps VT"  (3.2, Read access)

> "Our system tries to extend the validity interval VT if VT becomes empty."  (3.2, Extension)

> "The goal of this extension is to decrease the abort frequency."  (3.2)

> "Additional proactive extensions could be useful in some cases."  (3.2)

> "If we keep a sufficiently long history of objects, the validity interval will never become empty."  (3.2, Commit)

> "To minimize aborts, a transaction T will try to extend its validity interval before committing."  (3.3)

> "In our measurements we keep a small number k of old variants for each object."  (3.2, Memory Overhead)

> "we will change this and will use a fixed number of weak references"  (3.2, Memory Overhead)

> "the Java garbage collector will be able to automatically reclaim old"  (3.2, Memory Overhead)

> "n is a small value that is typically between 1 and 8."  (4.4)

> "searches through the committed versions of the object starting by the most recent and selects the first that intersects with its validity range"  (4.4)

> "If the intersection remains empty after the extend, the transaction needs to abort."  (4.4)

> "no modification to the locator nor validation of previously read objects is necessary when accessing a transactional object in read mode"  (4.4)

> "the maximum number of versions kept per object was 8"  (6)

> "Keeping one or two versions was sufficient to achieve similar and sometimes even better results than with 8 versions."  (6)

日本語要約: 多版版 LSA。版ごとの validity 区間と tx ごとの区間の交差で snapshot の一貫性を保ち、最新版から探して区間が重なる最初の版を読む (旧版を読める)。区間が空になれば延長を試み、それでも空なら abort。旧版の保持は「オブジェクトあたり小さな個数 n (1 から 8)」で、tx の位置には結ばれていない。1 から 2 版でも 8 版と同程度という測定を報告。

## 3. 二論文の差 (比較用の一言)

DISC 版は主に「最新版 + 残っていれば旧版」の線形化 STM で、read-only tx が延長できないとき旧版を読み tx を closed にする。TRANSACT 版は多版が前提の snapshot isolation で、旧版の個数上限を持つ。どちらも版の置き場所・アクセスコストを選択の契機にしていない。

## 確かめられなかったこと

- DISC 論文の 4 (評価) の後半と 5 (結論) は、旧版の保持・回収の記述を探して grep しただけで通読していない。GC の記述は 3.2 の一文と 4 の Java GC 設定のみだった。
- 出版社版 (Springer の PDF) との差は確認していない。読んだのは著者の公開ページの PDF で、ページ組みが LNCS 版と一致するかは不明。
- 旧版が個数上限で捨てられた結果、read-only tx が実際に abort する割合は原典に無い (測定は throughput 中心)。
- 節番号は TRANSACT 論文の 3.1 から 3.3 と 4.x はレイアウト付き抽出で確認した。2 段組みのため、逐語の位置 (Extension / Read access などの小見出し) は小見出し名で補った。
