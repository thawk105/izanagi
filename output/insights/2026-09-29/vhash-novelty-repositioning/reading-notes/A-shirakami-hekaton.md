# A: Shirakami (S-LTX) と Hekaton (MV/O) の 7 項目

注: 原典の 2 段組抽出が混ざるため、逐語は `pdftotext <pdf>` (段組なし) で確認したもの。本文中に指示めいた文は見つからなかった。

---
# 1. Shirakami (arXiv 2303.18142 v3) — 対象は S-LTX

## 7 項目

| 項目 | 内容 |
|---|---|
| 位置 π(T) | serialization epoch (整数 epoch) + 同 epoch 内の位置 (priority と order forwarding で決まる)。開始時に startable epoch = 現 epoch N + 1 を初期値として持つ (= commit_epoch)。commit 時 (order forwarding の段) に new_epoch へ置き換わり確定。S-OCC は epoch 内で S-LTX より後ろ。 |
| 契機 | 開始時 (staging) に N+1 に設定。動くのは commit 時の read validation で、自分の read_set に対し「より高優先の S-LTX が新しい版を書いた / WP を置いた」ことを検出したとき (order forwarding)。 |
| 向き | 前へ (earlier)。低優先 tx が高優先 tx の epoch へ寄り、その高優先 tx の「前」に置かれる (new_epoch = min(commit_epoch, その ltx の commit epoch))。開始 epoch より前に置かれうる。後ろへは動かさない (記述なし)。 |
| 読む版の選択 | 開始 epoch (commit_epoch) 時点の epoch 単位 snapshot の版を読む (read_snapshot(key, commit_epoch))。旧版 (最新でない版) は epoch snapshot として読める。ただし現実装は unsafe snapshot (epoch 末の最新 committed 版) を読み、後から order forwarding された S-LTX で変わりうる。S-OCC は最新版 (Silo 系。版選択の記述は §3.3 で単一版と読めるが明示なし)。 |
| 既読維持の判定 | commit 時。(a) read validation: 高優先 S-LTX が読んだキーを書いていれば order forwarding し、max_read_epoch ≥ new_epoch なら ABORT。前方移動の下限 (lower limit) は、read set を上書き/WP 予約する tx の最小値。(b) 移動した場合のみ write validation: commit_epoch ≤ max_reader_epoch(key) なら ABORT (committed S-OCC の read を壊さないため)。unsafe snapshot で不整合を読んだ場合も abort。 |
| GC への反映 | 版データの GC 境界が何で決まるかは記述なし (読んだ節: §3.1.2, §3.3, §3.4.1, §3.4.3, §3.5, §3.7)。epoch 長が「garbage collection のコスト」に効くと述べるのみ。S-OCC の read epoch metadata は in-place 更新で GC 不要、と別記。 |
| 長い tx / 停止 tx | 長い S-LTX を通すための設計 (WP、order forwarding、開始時 epoch 固定 snapshot)。「読み取り後に待つ tx が境界を止めるか」は記述なし。短 epoch 化で S-LTX が epoch 完了待ちになる旨のみ (§3.4.1)。 |

## 根拠の逐語
- §3.1.3: "t2 ’s serialization epoch is adjusted to match t1 ’s serialization epoch. We refer to this as order forwarding."
- §3.1.3 (図1): "their serialization order becomes t3 → t2 → t1 via order forwarding" (図 1 キャプション。commit 時刻順と直列化順が逆転)。
- §3.1.2: "The S-LTX transactions to be executed at that time share the snapshot to read, which is the result of the previous epoch. Shirakami uses a multiversion data structure to provide snapshots per epoch."
- §3.2.1: "It obtains the current epoch N and sets its own startable epoch (initial value of the serialization epoch, valid epoch) to N + 1."
- §3.2 冒頭: "If order forwarding succeeds, its serialization epoch is set to the highpriority transaction’s epoch, and the two transactions are ordered by reverse priority within that epoch."
- §3.2.2: "In read validation, if another transaction has already written a new version or placed a WP, the transaction attempts to orderforward. If the transaction exceeds its lower limit for order forwarding, it aborts."
- §3.2.2: "The lower limit of order forwarding is the minimum value among all transactions that overwrite or place WPs on the current transaction’s read set."
- Algorithm 1 行 8, 15-17: read_snapshot(opr.key, commit_epoch); new_epoch ← min(commit_epoch, commit_epoch_of(ltx_id)); if max_read_epoch ≥ new_epoch then return ABORT (抽出テキストの語順は微妙に崩れるので逐語ではなく要約)。
- Algorithm 1 行 19-22 と §3.2.2: "write validation is executed only when the transaction has performed order forwarding"
- §3.2.2 前後 (Algorithm 2 の説明): "an S-LTX transaction may be placed earlier than its opening epoch by order forwarding."
- §3.4.3: "An S-LTX transaction is assigned to a specific epoch at the start and reads the specific version of each record for that epoch."
- §3.4.3: "The created snapshot may be inconsistent because S-LTX transactions that run later and are moved to the epoch via order forwarding may change it. If a transaction reads a record in an inconsistent snapshot, the transaction is aborted."
- §3.4.3: "S-LTX transactions currently read unsafe snapshots, taking the abort risk but preferring newer snapshots."
- §3.4.3: "If no S-LTX transactions execute order forwarding at the end of an epoch, a snapshot consisting of the latest committed versions is referred to as a safe snapshot."
- §3.5 (on-demand version order): "The version ordering of S-LTX transactions within the same epoch is dynamically determined, enabling aggressive order forwarding."
- §3.5: "When a later transaction in the serialization order has already written a version, the corresponding writes and logging of earlier transactions can be omitted by exploiting the non-visible write rule [23]."
- §3.5: "it is guaranteed that no transaction will ever read w2 (d)" / "S-LTX transactions read from a snapshot constructed on an epoch basis. Therefore, w2 (d) satisfies the conditions of the non-visible write rule"
  (要約: 同 epoch で後ろに置かれた tx が既に書いた版があるとき、前に置かれる tx の write は誰にも読まれないので、ログもメモリ表への書きも省略できる。)
- §3.5 (lower bound): "Theoretically, the lower bound of the serialization order is the transaction’s begin timestamp at the start of the chain of anti-dependency" と "the implementation uses epoch information as the lower bound for serialization order."
- §3.4.1: "Setting a longer epoch reduces epoch carryover and the cost of garbage collection in multi-version environments."
- §3.3.1: "Since this metadata is updated in place, garbage collection is not required." (S-OCC の read epoch metadata)
- §3.7: "When no consistent placement exists, the lower-priority S-LTX aborts."
- §3.7: "Within an epoch, all S-LTX transactions are ordered before all S-OCC transactions."
- §3.4.1: "subsequent S-LTX executions will be in a waiting state until the current epoch is complete."

## 読んだ節
§3 冒頭〜§3.1.6、§3.2 (Alg.1)、§3.3 (Alg.2)、§3.4 全体、§3.5、§3.6、§3.7。GC・長い tx・oldest 等を全文 grep。

---
# 2. Hekaton (Larson ほか, PVLDB 5(4) 2011) — 対象は optimistic (MV/O), serializable

## 7 項目

| 項目 | 内容 |
|---|---|
| 位置 π(T) | 2 点: logical read time (serializable では begin time) と end timestamp (precommit で取得)。commit 順序は end timestamp で決まる。 |
| 契機 | 通常処理中は read time = begin time で固定。end timestamp は commit 要求時の precommit で取得 (Active → Preparing)。 |
| 向き | 「読みの位置 (begin) → 直列化位置 (end) へ後ろへ」と読める。read は begin 時刻、validation は end 時刻で行う。ただし論文はこれを「直列化位置が移る」とは書いていない (逐語なし)。以上は原典の 2 つの時刻の記述からの読み取り。 |
| 読む版の選択 | 論理 read time RT に valid time が重なる版 (版ごとに valid time は重ならず、高々 1 つ)。旧版を読める (serializable 楽観は RT = begin time)。read time は begin〜現在の任意値でよく、分離水準と CC 方式で決まる。 |
| 既読維持の判定 | commit 時 (Preparing の validation): ReadSet の各版が end 時刻でも可視か検査 + ScanSet を再実行して phantom 検査。失敗なら abort。commit dependency は待つ。 |
| GC への反映 | 「no longer visible to any transaction」になった版を捨てる。境界の具体 (最古 active tx の begin など) は記述なし ("Details of our garbage collection algorithm are beyond the scope of this paper")。validation 中・precommit 後の tx の寄与も記述なし。WriteSet の旧版ポインタが GC 用に残る旨のみ。 |
| 長い tx / 停止 tx | 長い read-only tx を混ぜた実験はある (§5.2.2 相当)。境界が進むかの記述なし。 |

## 根拠の逐語
- §2.2: "Every read specifies a logical (as-of) read time and only versions whose valid time overlaps the read time are visible to the read"
- §2.2: "Different versions of a record have non-overlapping valid times so at most one version of a record is visible to a read."
- §2.5 (Visibility): "The read time can be any value between the transaction’s begin time and the current time."
- §3.1 (scan): "All reads specify T’s begin time as the logical read time."
- §2.4 / §2.5 前後 (validation 方式): "we simply check whether a version that was read is still visible as of the end of the transaction."
- §3.2: "Precommit simply consists of acquiring the transaction’s end timestamp and setting the transaction state to Preparing."
- §3.2: "To check visibility transaction T scans its ReadSet and for each version read, checks whether the version is still visible as of the end of the transaction."
- §3.2: "T walks its ScanSet and repeats each scan looking for versions that came into existence during T’s lifetime and are visible as of the end of the transaction."
- §3.2: "If T fails validation, it is not serializable and must abort."
- §3.2: "Commit ordering is determined by transaction end timestamps"
- §2.3 (更新): "A version can be discarded when it is no longer visible to any transaction."
- §2.3: "Details of our garbage collection algorithm are beyond the scope of this paper."
- §3.3 (Postprocessing): "the pointers to old versions in its WriteSet are needed for garbage collection."
- §3.4: "Snapshot isolation: Implementing snapshot isolation is straightforward in our case: always read as of the beginning of the transaction." / "Read committed: ... always using the current time as the logical read time."
- §2.7 前: "deadlocks cannot occur because an older transaction never waits on a younger transaction" (end timestamp で older/younger を定義)
- 論文中の validation 図の説明: "Version V4 was created during T’s lifetime and is visible at the end of T, so V4 is a phantom."
- §5.2.2 (長い read-only tx の実験。GC への言及なし): "Users often need to run operational reporting queries on the live system." / "The presence of a few long-running queries should not severely affect the throughput"

## 読んだ節
§2 (2.1-2.7)、§3 (3.1-3.4)、§4 冒頭、§5.2.2。GC / oldest / end timestamp / read time を全文 grep。

---
# 確かめられなかったこと
- Shirakami: 版データの GC 境界 (どの epoch より前を回収するか) は本文に記述なし。epoch 変更 (order forwarding) が GC 境界を動かすかも記述なし。read epoch metadata 以外の GC の仕組みも記述なし。
- Shirakami: S-LTX の epoch が「後ろ」へ動くことがあるか、明示の記述なし (前へ寄る記述のみ)。
- Shirakami: S-OCC の版選択 (単一版か) の明示なし。「Silo の修正」から推定できるが原典は明言せず。
- Hekaton: read time (begin) から end timestamp への移動を「直列化位置の後方移動」と述べた箇所はない。上の向きの欄は 2 つの時刻の記述からの読み取り。
- Hekaton: GC の境界 (最古の active tx の begin 時刻か) と、validation 中・precommit 後の tx の寄与は記述なし。「Details ... beyond the scope」とある。
- どちらも「読み取り後に待つ長い tx」で境界が進むかは記述なし。
- 抽出テキストの一部 (Shirakami の Alg.1 の行、Hekaton の一部節番号) は行から拾った。節番号は目安で、一部の逐語は節番号が正確でない可能性がある (特に Hekaton §2.4/§2.5 の validation 方式の文)。
