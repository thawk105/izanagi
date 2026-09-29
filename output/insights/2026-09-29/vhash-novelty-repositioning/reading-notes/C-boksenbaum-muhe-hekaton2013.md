# 読み取りノート C: Boksenbaum 1984 / Mühe 2013 / Hekaton 2013

記法は /work/1/SFC/tanab/tmp/vhash-novelty-2026-09-29/notation.md の 7 項目に従う。
引用は原典テキスト (pdftotext 出力) の逐語。Boksenbaum は OCR 版で崩れが多く、引用も OCR のまま (句読点・記号の崩れを含む)。
原典に指示めいた文は見当たらなかった (Mühe・Hekaton・Boksenbaum とも)。

---------------------------------------------------------------------

## 1. Boksenbaum, Cart, Ferrié, Pons (VLDB 1984)

### 7 項目の表

| 項目 | 内容 |
|---|---|
| 位置 π(T) | 各キー x について tx が持つ timestamp の区間 I(T,x)。tx 全体では I(T) = 各 x の I(T,x) の共通部分 (分散では site ごとの I(T,Si) の共通部分)。区間は tx が動いている間だけ持つ。certification で I(T) が空なら reject、空でなければ I(T) 内から 1 点 t_T を選んで確定する。確定するまで点は決まらない。 |
| 契機 | (a) tx 自身の read / prewrite: 操作ごとに、検証済み tx との依存に応じて区間を更新する (区間 Ic(T) が各 read/prewrite のたびに site へ送られ、site が区間を絞って返す)。(b) 別の tx T が certify されて t_T を選んだとき: T と競合していた living tx T' の区間を、その t_T で切り詰める (adjust)。 |
| 向き | 区間は両端が内側へ縮む方向にだけ変わる (共通部分と切り詰めのみ。区間を広げる記述は読んだ節に無い)。競合の型で切り詰める側が違う: 検証された T が先に書いた側の tx は下限が上がる (後ろへ)、T が読んだだけの側の tx は上限が下がる (前へ)。最終的に 1 点 t_T に潰れる。何かを狙って点を後ろへ動かす機構ではなく、他 tx の確定点による切り詰めの結果。 |
| 読む版の選択 | 記述なし (読んだ節: 全文)。単版として書かれているように読めるが、明言は無い。版の選択規則は書かれていない。書かれているのは、各オブジェクトに、検証済み tx の読み・書きの最高 timestamp R(x), W(x) を持つこと (OCR 崩れで式は不完全)、certification 時に prewrite した新しい値を base へ写すこと (swap) 、多版 TO (Reed) は「版と timestamp を余計に持つ」として対比されていること。旧版を新たに読む機構の記述なし。 |
| 既読維持の判定 | read のたびに区間に制約を織り込む (性質 P2: I(T,x) は x を使った検証済み tx の timestamp すべてと矛盾しない)。commit 時 (certification) に I(T) が空でないことを確認し、空なら reject。読み直しや待ちは記述なし。 |
| GC への反映 | 記述なし (読んだ節: 全文。版・表の回収 (garbage / purge / delete) に触れる語は無い)。 |
| 長い tx / 読み取り後に止まっている tx | 記述なし。関連する記述は、starvation 回避として、tx が開始時に prioritary-certify を全 site へ流し、他の tx の certification をすべて遅らせる保護段階に入ること (T が長く動く間、他 tx の確定を止める向き)。 |

### 根拠の逐語

- Abstract: "allows a chronological validation order which differs from the serialization one" (検証の時間順と直列化順が違ってよい、の主張)
- §1: "use of intervals of timestamps allows us to surmatize dependencies in C* without washing out those of type" (§5 結論。OCR 崩れあり。区間で依存を要約する、の意味)
- §2 (性質 P2): "Property P2. For each living transaction T and for each object x it has used, I(T,x) is compatible with timestamps of all the validated transactions which have also used x."
- §2: "The bounds of this interval express the strongest constraints between T and validated transactions"
- §2: "allow keeping track of T--LTi* dependencies" (OCR。区間が「T が検証済み Ti より前」という依存を追える、の意味。前後の語順も崩れている)
- §3 (認証の骨格): "if I(T)=0 then T is rejected, otherwise a timestamp value t T is chosen in I(T) to be associated to T" (原文では空集合の記号が 0 と崩れている)
- §3 (他 tx の区間の調整): "adjustment of intervals of living transactions T’ in conflict with T"
- §4 (区間の伝搬): "is transmitted during each read or prewrite made by T to the various sites accessed by T"
- §4 (確定点の選び方): "Choice of tT=UI(T) fulfils this condition"
- §4 (選択の効果): "Choosing tT=UI(T) would have the reverse effect."
- §4 (切り詰め): "will truncate the intervals of the value tT on the" (OCR。左右どちらを切るかの文は崩れており、上の表の「向き」は §4 のこの箇所と §3 の "left truncation point" / "right truncation point" 相当の崩れた文から読んだ。左右の割り当ては OCR の崩れで確信が弱い。)
- §1 (多版 TO との対比): "muLtiple timestamped versions of the aaae" (OCR 崩れ。多版 TO は同じ物の複数の timestamp 付き版を持つ、の意味)
- §4 (validation の実体): "corresponds to the copy of the new values of objects"
- §4 (starvation): "must broadcast to all sites a prioritary-certify message"

### 読んだ節
全文 (§1 導入、§2 依存グラフと区間、§3 区間による certification、§4 分散実装、§5 結論)。ただし OCR の崩れで、手続きの擬似コード (read / prewrite / adjust) は式が読めない箇所が多く、逐語では引けていない。

---------------------------------------------------------------------

## 2. Mühe, Kemper, Neumann (CIDR 2013) "tentative execution"

### 7 項目の表

| 項目 | 内容 |
|---|---|
| 位置 π(T) | 明示の点 timestamp / 区間は無い。長い tx (ill-natured tx) は、ある snapshot 時点で直列に実行されたものとして扱う。validation 通過後、短い apply transaction を主 DB の直列実行キューに入れ、apply が commit した位置が直列化位置になる。view-serializability の場合は、apply 時に読みが「主 DB の現在値」と一致することを要求する。snapshot は定期的に refresh され、tx は「自分が到着した後に作られる次の snapshot」で実行を始める。 |
| 契機 | 長い tx を選ぶ契機は、時間・件数の上限超過 (ロールバックして snapshot 側で再実行)、静的解析、ユーザーの明示ラベル、過去の統計。位置が動く契機は記述なし (tx の位置を動かす機構は無い)。validation の失敗は abort。 |
| 向き | 動かない。tx の snapshot 時点は固定で、apply が先送りされても位置を後ろへ進める記述は無い。abort されたあと再実行するかの記述も読んだ節に無い。 |
| 読む版の選択 | snapshot (tx 一貫) の上で読む。snapshot isolation では「t が始まる前に commit した最後の版」を読む。view-serializability では snapshot の値を読み、その値が主 DB の現在値と同じかを apply で検証する。HyPer では fork による page shadowing で、複数の snapshot が同時に存在できる。 |
| 既読維持の判定 | commit 時 (apply transaction) の validation。読みの記録 L = {(tid, snapshotVersion(tid))} を取り、「∀(tid, ver) ∈ L : currentVersion(tid) = ver」を確認する。版は「値そのもの」または版カウンタ (関係・列・索引の葉・メモリページの粒度) で表す。保証できなければ abort。 |
| GC への反映 | 版データの回収境界の記述なし (読んだ節: 全文。garbage / reclaim は出ない)。関連する記述は、HyPer の snapshot が page を共有し、書き込みで page を複製する (copy-on-write) こと、および refresh 時に主 DB を静止する (quiesce) こと。古い snapshot は、待ちの tx が終わるまで生き、その間は新しい snapshot の作成を遅らせない。 |
| 長い tx / 読み取り後に止まっている tx | 中心の主題。長い tx は snapshot 上で走り、主 DB の短い tx を止めない。ただし snapshot が古いほど abort が増える (refresh 間隔が長いと commit 率が 0 に向かう)。ホットな行を読む長い tx は view-serializability で高い abort 率になる。 |

### 根拠の逐語

- Abstract: "we execute longrunning transactions on a consistent snapshot and integrate their effects into the main database using a deterministic and short apply transaction"
- §1: "Since the transaction-consistent snapshot is completely disconnected from the main database"
- §3: "The transaction is queued for the next snapshot being created after its arrival."
- §3.1: "it is rolled back using the undo log and re-executed using tentative execution" (時間・件数の上限を超えた tx の扱い)
- §3.2: "we monitor all reads on the snapshot and validate them against the main database"
- §3.3: "t reads the last version of x written by a transaction that committed before t started" (snapshot isolation の規則 1)
- §3.5: "A tentative transaction is successful if a) it commits on the snapshot and b) ∀(tid, ver) ∈ L : currentVersion(tid) = ver holds."
- §3.6: "checking that all version counters for written tuples are equal both during the execution on the snapshot and on the main database"
- §3.8: "the reads-from relation of a readonly transaction t is equal to the reads-from relation of the serial schedule in which t is executed serially right after the consistent snapshot of the database was taken"
- §3.9: "If validation is not successful, the transaction aborts just as if a lock could not be acquired"
- §5.1: "Until a modification occurs on a page, memory pages are shared between all snapshots."
- §5.1: "All transactions queued for execution on the old snapshot can still finish and be applied to the main database"
- §5.4: "the commit rate of the ‘paymentByCredit’ transaction decreases with less frequent refreshes and converges towards zero"
- §5.4: "requires the system to be quiesced when using hardware page shadowing"
- §5.5.2: "This can lead to long-running transactions suffering from high abort rates due to reading frequently-changing (hotspot) tuples."
- §6 (Larson らの紹介): "They find that optimistic multi-version storage performs favorable compared to locking, especially when long-running transactions are part of the workload."

### 読んだ節
全文 (要旨、§1〜§7 相当、付録の存在は確認、Table 1 は表として読み流し)。

---------------------------------------------------------------------

## 3. Diaconu ほか, Hekaton (SIGMOD 2013)

### 7 項目の表

| 項目 | 内容 |
|---|---|
| 位置 π(T) | 2 つの timestamp を持つ。論理 read time (RT) は tx の開始時刻に固定 (全分離水準)。commit / end timestamp は validation 開始時に取り、直列化履歴での位置を決める。version は valid time [begin, end) を持つ。 |
| 契機 | end timestamp は commit 処理に入り validation が始まるときに取得。read time が動く契機は記述なし。 |
| 向き | read time は開始時刻から動かない (規則として固定)。end timestamp は read time より後。read time を後ろへ進める記述は、読んだ節には「可能な範囲の説明」以外に無い (下の逐語を参照)。 |
| 読む版の選択 | 「valid time が read time と重なる版だけが見える」。read 操作は as-of の read time を指定する。read time より前の版 (旧版) は、read time が古い tx には見える。更新は旧版の end と新版の begin を設定する多版方式。 |
| 既読維持の判定 | serializable のとき commit 時に validation: read stability (読んだ版 V1 が end 時点でも見える版であること) と phantom 回避 (走査を再実行して新しい版が無いこと)。read set と scan set を保持する。snapshot isolation・read committed は validation 不要、repeatable read は read の validation のみ。失敗時は abort。commit 依存 (commit dependency) は連鎖 abort を生みうる。 |
| GC への反映 | 版は「どの active tx からも見えなくなったら」garbage。境界は、最古の active tx の begin timestamp (透かし、watermark) と、版の end timestamp の比較。GC 用の 1 つの処理が定期的に global transaction map を走査して最古の active tx の begin timestamp を求め、完了済み tx を分ける。 |
| 長い tx / 読み取り後に止まっている tx | 長い tx を主題にした記述なし (読んだ節: §4 版、§6 tx 管理、§8 GC)。原典から言えるのは、GC の境界が「最古の active tx の begin timestamp」であること、GC が active tx の処理を止めないこと、まで。長い tx で境界が古いまま残ることの明記は無い (これは推測で、原典には無い)。 |

### 根拠の逐語

- §4 (更新の例): "A version can be discarded when it is no longer visible to any active transaction."
- §4.1: "Every read operation specifies a logical (as-of) read time and only versions whose valid time overlaps the read time are visible to the read"
- §6: "A transaction is by definition serializable if its reads and writes logically occur as of the same time."
- §6: "a transaction is serializable if we can guarantee that it would see exactly the same data if all its reads were repeated at the end of the transaction"
- §6 (read stability): "If T reads some version V1 during its processing, we must ensure that V1 is still the version visible to T as of the end of the transaction."
- §6 (read stability): "This is implemented by validating that V1 has not been updated before T commits."
- §6.1: "Logical Read Time: the read time of a transaction can be any value between the transaction’s begin time and the current time."
- §6.1: "For all supported isolation levels, the logical read time of a transaction is set to the start time of the transaction."
- §6.1: "The commit time determines a transaction’s position in the serialization history."
- §6.2.1: "The validation phase begins with the transaction obtaining an end timestamp."
- §6.2.1: "To validate its reads, the transaction checks that the versions it read are visible as of the transaction’s end time."
- §8: "a version of a record is garbage if it is no longer visible to any active transaction"
- §8: "Since regular index scanners may encounter garbage versions as they scan indexes, index operations are empowered to unlink garbage versions when they encounter them."
- §8: "it ensures that old versions will not slow down future scanners by forcing them to skip over old versions encountered, for example, in hash index bucket chains"
- §8: "Garbage collection runs concurrently with the regular transaction workload, and never stalls processing of any active transaction."
- §8.1 (二段組で小節番号が混ざる。8.1.1〜8.1.3 のどこか): "Any version whose end timestamp is less than the current oldest active transaction in the system is not visible to any transaction and can be safely discarded."
- §8.1: "A GC thread periodically scans the global transaction map to determine the begin timestamp of the oldest active transaction in the sys"
- §8.1: "Any transaction T in the system whose end timestamp is older than the oldest transaction watermark is ready for collection."
- §8.1.3: "the garbage collection has been parallelized across all worker threads in the system"
- §8.1.3: "making sure that the system does not generate more garbage versions than the GC subsystem can retire"

### 読んだ節
§4 (版・索引・読み・更新の例)、§5 の冒頭 (コンパイル) は GC 参照箇所のみ、§6 tx 管理 (6.1 timestamp、6.2 commit 処理・validation・rollback)、§8 GC (8.1〜8.1.3)。§7 耐久性と §9 性能は GC 関連の語検索のみ。

---------------------------------------------------------------------

## 4. 「tx の timestamp を後の時刻へ進めて、読んだ値を保ったまま、古い版の保持を減らす」機構、または「版の置き場所・アクセスコストを契機に timestamp を動かす」機構

3 論文とも、読んだ節には無い。

近い記述と、それがなぜ該当しないか:

- Boksenbaum §3–§4: 他 tx の確定点で区間が切り詰められ、下限が上がる (後ろへ動く) ことはあるが、契機は他 tx の certification であり、読んだ値の保持と版の削減には結びつけられていない。版・回収の記述自体が無い。
- Hekaton §6.1: "the read time of a transaction can be any value between the transaction’s begin time and the current time." と書かれ、read time を後ろへ取れる余地は示されているが、直後に "the logical read time of a transaction is set to the start time of the transaction." と固定されている。読んだ値を保ったまま進める条件・機構・GC との結びつきは記述なし。
- Hekaton §8: 古い版が走査を遅くすること ("old versions will not slow down future scanners") は書かれているが、対処は GC による unlink であり、tx の timestamp を動かすことではない。
- Mühe §3.5, §5.4: snapshot の refresh は「新しい snapshot を作って新しく始める」ことであり、既存の tx の位置を進める機構ではない。

---------------------------------------------------------------------

## 確かめられなかったこと

- Boksenbaum の OCR 版では、read / prewrite / adjust の擬似コードと、切り詰めの左右割り当て (「T' が書いた側は左、読んだ側は右」) を式レベルで確認できなかった。表の「向き」は §3 の性質 P2 の意味づけ ("ti < LI" と "UI < ti") と §4 の切り詰めの文が崩れた形で示す内容から読んだもので、左右の割り当てには OCR 由来の不確かさがある。実 PDF の図版・式は画像として見ていない。
- Boksenbaum が単版か多版かは、明言する文が無い。多版 TO への言及と R(x) / W(x) の持ち方から単版らしく見えるが、原典の断言ではない。
- Hekaton の §8.1 の小節番号 (8.1.1 / 8.1.2 / 8.1.3) は、pdftotext の抽出順で二段組の文が混ざり、どの逐語がどの小節かを確定できなかった。逐語自体は原典に実在する。§4 の "A version can be discarded..." は §4.2 (更新の例) 付近と思われるが、見出しを直接確認できていない。
- Hekaton で長い tx が GC の境界に与える影響は、原典に明記が無いため書いていない。
- Mühe で abort された長い tx の再実行と、再実行時の snapshot の取り方は、読んだ節に記述が無かった。
