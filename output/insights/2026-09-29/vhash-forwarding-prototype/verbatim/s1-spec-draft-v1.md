# Cicada 選択的 forwarding — プロトコル仕様 草案 v1 (親 provisional、段 3 の攻撃対象)

対象コード: external/ccbench (pin 51f896352 の gitlink) の cc/cicada/transaction.cc・include/transaction.hh・include/time_stamp.hh。

## 0. 記号
- T.ts = TxExecutor::wts_.ts_ (read-write tx の read/validation/install すべてに使う単一 timestamp)。ts = (clock << 8) | thid。
- 版リスト = tuple->latest_ から next_ で wts 降順。位置 p=1 が先頭。
- 「T.ts で見える版」= stock read_internal と同じ規則 (wts > T.ts を飛ばし、pending は待ち、aborted は飛ばす) で得る版。

## 1. 発火条件 (論理的な cold 境界)
- read-write tx (is_ronly_=false) の read() 経由の read_internal で、T.ts で見える版に到達するまでに
  先頭から K 版を超えて辿る必要がある (見える版の位置 p > K) とき。
- 位置は物理的なリスト位置 (pending / aborted を含む) で数える。hot 配置は作らない。
- scan() 経由の read_internal、read-only tx、write set に INSERT / DELETE を含む tx は「対象外」(試行せず計数だけ)。

## 2. 前進先の選び方 (最小前進)
- 先頭 K 版のうち最も古い committed 版 v_h を目標とする (無ければ「対象外: hot に committed 版なし」)。
- ts' = v_h.wts より大きい、この thread の形式 (下位 8 bit = thid) の最小の timestamp。
  clock(ts') = clock(v_h) + (thid <= thid(v_h) ? 1 : 0)。ts' > T.ts は v_h.wts > T.ts から従う。

## 3. 前進前の確認 (早期判定。最終保証ではない)
1. 既読: read set の各要素 r について、ts' で見える版 (先頭から辿る。later_ver_ は使わない) が r.ver_ と同一か。
   違えば「既読と合わない」。その途中で wts < ts' の pending 版に当たったら待たずに「競合」。
2. 書き込み側: write set の各要素 w について
   - RMW: 対応 read が 1. で確認済み。加えて latest.wts < ts' でなければ「書き込み側の制約」。
   - UPDATE (blind): ts' で見える版 v について v.rts > ts' なら「書き込み側の制約」(stock update() の早期 abort 条件を ts' で評価)。
3. rts は書かない (共有書き込みを増やさない)。rts を「見える区間の終わり」として使って確認を省かない (メモ §13.3)。

## 4. 前進の実行 (すべて tx ローカル、共有構造へは何も公開しない)
- T.ts := ts'。wts_.localClock_ := clock(ts') + 1 (次の begin() の ts が ts' と重複しないため。§6)。
- write set の各 new_ver_->wts_ := ts' (未設置 = 未公開なので書換えてよい。メモ §18.1)。
- read set と write set の later_ver_ をすべて nullptr にする (旧 ts で得た探索開始位置は ts' では誤り:
  later_ver_.wts < ts' のとき、検証がそれより新しい wts < ts' の版を見落とす)。
- ThreadWtsArray / ThreadRtsArray は更新しない (GC 保護は旧 ts のまま = 保守的に据え置き、メモ §29 段階 3)。
- その後、ts' で通常の read を行う (位置 p' を計数に記録)。

## 5. 失敗時
- 1〜3 のどれかで失敗したら T.ts は変えず、stock どおり元の ts で奥を辿る (メモ §18.2: 何も公開していないので戻れる)。

## 6. 正しさの根拠 (段 3 で攻撃すること)
- 最終保証は stock の validation (precheck → pending 設置 → rts 更新 → 既読の一致確認 → write set の rts 確認) を T.ts = ts' で
  そのまま走らせることに置く。validation は wts_.ts_ だけをパラメタにしており、既読版がすべて ts' で見える版と一致しなければ abort する。
  reader (rts を先に上げてから確認) と writer (pending を先に置いてから rts を確認) の双方参加の順序付けは stock のまま (メモ §13.2)。
- 前進は validation の開始前 (read 相) にだけ起こる。pending 版の設置後に T.ts は動かない (メモ §18.1)。
- 一意性: 他 thread とは下位 8 bit で区別。同一 thread 内は ts' > 旧 T.ts、localClock_ = clock(ts')+1 で次 tx も ts' より大。
  注: stock の generateTimeStamp は abort 後 clockBoost で localClock_ が rdtscp より進み、直後の commit で boost=0 に戻ると
  次の ts が前の ts と同じ値になりうる (コード読みの疑い、未実測)。本 variant はこれを直さない (stock と同条件)。
- GC: MinRts は min(ThreadRtsArray) ≤ MinWts-1 ≤ 旧 T.ts - 1 < ts'。旧 ts で読んだ版も ts' で読む版も保護される。
- MinWts 以上でしか commit しない不変条件 (read-only の rts = MinWts-1 の前提) は、ts が増えるだけなので保たれる。

## 7. F (比較構成)
- 発火条件 1. が立ったら、その場で status_=aborted にして read を打ち切る (runner が abort() → 次の begin() で新 ts)。
  計数: 「F abort」。長い tx が永遠に commit できない可能性は計数で見る (隠さない)。

## 8. knob
- IZANAGI_CICADA_FWD_MODE: 0 = stock (既定、patch を当てても stock と同じ前処理結果), 1 = C, 2 = F。compile 時。
- K: 実行時 flag (C/F build でだけ定義)。既定 3。
- IZANAGI_CICADA_FWD_COUNT: 計数 (既定 0)。計数入り build の throughput は性能値に使わない。
- 長い tx の生成: IZANAGI_CICADA_LONGTX (compile 時) + 実行時 flag (長い thread 数・長い tx の操作数・read 後の待ち us)。
  stock との比較のため FWD_MODE と独立 (stock CC + 長い tx の build を作れる)。
