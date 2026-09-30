---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-vhash-ro-continuing
seq: 1
title: VHash md_44: 読み続ける read-only tx を前進させる成立条件を紙とコード照合で論じ、前進先を安定境界 (Cicada では MinWts − 1) に限り全既読の可視を確かめれば RA なしで一貫性と論理的な GC 安全が保たれると示した。効き目は細く、試作の前に実装なしの診断を推す (docs のみ、branch worktree-dev-wave-vhash-ro-continuing)
---

## 本文

- 依頼: 並行 VHash wave の md_44 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_44.txt`)。一次資料 `output/insights/2026-09-30/vhash-ro-continuing-feasibility/README.md`、設計の判断は {{D:vhash-ro-continuing-stable-advance}}。計算 0 (計測・探索・実装なし)。
- 段構成: 既定の軽量版。段 2・3 を省き (正しさの防壁・受理集合を変えない docs だけ)、段 1 前に関連資料の抽出を read-only の Explore 子 (sonnet) 1 本に任せた。実装面なしのため段 5 の Codex 実装子と変異 matrix は無し。段 6 は read-only codex review 2 本 (A: 論証の反例探し、B: 事実照合と過剰) を並列で回し、所見 11 件 (must-fix 2・should-fix 8・nit 1) をすべて real として親が直した。焦点再レビューは省いた (直しは主張を狭める向きだけで、論証の骨格は変えていない)。
- 棄却・訂正: レビュー A は抽象仕様 RO-A の定理 S-RO・G-RO の反例を作れなかった。代わりに、Cicada の初期 MinWts (`initial_wts + 2`) が core 間の時計の順しだいで安定境界にならない起動直後の列をコード上で作った。この穴は stock の read-only の begin にも同じく当たる (実機での発生は未確認)。レビュー B は、区間 GC に対する上積みを「未読の更新キーごとに高々 1 版」とした初稿の上限を撤回させた (区間 GC の条件 (d′)(e) と stock の切り離しに左右されるため)。
- 素材: 長い read-only tx は Cicada で前進先を 3 通りに止める。(1) 自分の ThreadWtsArray が MinWts の上限になる。(2) 自分の GCFlag が立たず leader の集計が止まる。(3) thread 0 なら leader の仕事そのものが止まる。`rts_ = MinWts − 1` の再実行だけでは前進しない。前進できる幅は既読のどれかに次の確定版が来るまでで、md_29 の batchR (skew 0.99) の熱いキーの鎖長からの粗い目安は約 2.7 µs。
- 異常: 待ち手を producer 2 本に加えて生の until ループで 1 本重ねて張り、気づいて止めた (1 条件 1 本の規律違反、実害なし)。

## 次の一手差分

### 新規

- {{T:vhash-ro-advance-diagnostic}} **P2・新規**: VHash の読み続ける read-only tx の前進 (md_44、{{D:vhash-ro-continuing-stable-advance}}) を試作へ進めるかを決める、実装なしの診断。md_42 ([T-2962] の天井の直接比較) の結果の後に、一次資料 `output/insights/2026-09-30/vhash-ro-continuing-feasibility/README.md` §9 の D1〜D3 を測る (D2: 既読の次の確定版と活動中の書き手の最小時刻から前進できた幅を後から数え、tx の後半まで残るか。D3: その幅で区間 GC の条件と stock の切り離しを当てたとき追加で外せる版)。判定の閾値は結果を見る前にその wave で登録する。幅が残る負荷があるときだけ試作 (D4) へ進み、試作では K4 (初期 MinWts)・昇格の禁止・ST-1 の後からの照合を必須にする。
