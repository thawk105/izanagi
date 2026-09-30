---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-vhash-ro-continuing
seq: 2
---

## {{D:vhash-ro-continuing-stable-advance}}. VHash で読み続ける read-only tx を前進させるなら、前進先を安定境界 (それ以下の時刻に新しい版がもう置かれない値) に限り、全既読がそこで見えることを確かめて snapshot を先に移し、その後に floor を上げる。試作へ進む前に実装なしの診断で前進の幅を確かめる

**決定:**
1. 読み続ける read-only tx (固定キーの point read だけ、昇格しない) の前進は、抽象仕様 RO-A とする。安全点で安定境界 σ を得る。各既読 v について (v.wts, σ] の最初の非 ABORTED 版を観測し、s = min(σ, その版の wts − 1) を求める。s が今の snapshot より大きければ、snapshot を s へ移してから floor を s 以下で公開する。確認は rts を書かない。失敗しても snapshot と floor は変えない。一次資料 `output/insights/2026-09-30/vhash-ro-continuing-feasibility/README.md`。
2. 論証は紙の上の抽象仕様についてで、直列化 (最後の snapshot の位置に置く) と論理的な GC 安全を示した。D2319 の条件 RA は使わない。安定境界の条件 ST は、X1・X2 の書き手 (前進先より小さい時刻で、前進の時点でまだ活動中の書き手) をまさに除く。
3. Cicada では `MinWts − 1` を安定境界とする。そのための条件 K1〜K5 (thread ごとの時刻と slot の単調性、集計の下限性、`group_commit = 0`、初期 MinWts、0 からの減算) はコード読解で、未確認を含む。前進の実装には「将来書かない」と「読んだ版を守る下限」を分ける。前者は ThreadWtsArray を自 thread の時計へ持ち上げること (localClock_ も進める)、後者は ThreadRtsArray である。GCFlag は tx の途中で立て、thread 0 なら leaderWork を呼ぶ。昇格は禁止する。
4. 試作は今は作らない。md_42 の後に、実装なしの診断 (一次資料 §9 の D1〜D3) で前進できる幅が tx の後半まで残る負荷があるかを確かめてから決める。

**理由:**
- 安定な snapshot で読んだ版は、他 tx の後続の確定版が snapshot より上にしか来ない。これが読みの時期によらず成り立つので、md_26 の (I2) を確認に頼らず得られ、RA が要らなくなる。段 6 レビュー A は RO-A の定理の反例を作れなかった。
- 各条件を外した紙の上の列がある。確認を外すと読みの skew の巡回 (C1)、前進先が安定でないと 3 tx の巡回と X1 型の回収 (C2)、floor を先に上げると D2317 が却下した形 (C3)、時計を進めずに持ち上げると他の read-only tx の安定境界の下に版が置かれる (C4)。したがって、floor だけで守り rts を書かない設計の類では、どの条件も外せない。
- 効き目は細い見込み。前進の幅は既読のどれかに次の確定版が来るまでで頭打ちになる。md_29 の batchR (skew 0.99) の熱いキーからの粗い目安は約 2.7 µs。区間 GC に対する上積みは条件 (d′)(e) に左右され、上限を出せない。安全でない前進の速さを天井にしないためにも、先に幅を後から数える。

**却下した選択肢:**
- `rts_ = MinWts − 1` の再実行だけで前進する。長い read-only tx 自身の ThreadWtsArray・止まった GCFlag・thread 0 の leader が前進先を止めるので前進しない。確認なしなら C1 の巡回になる。
- 前進先を自分の時計 (書き手型の E-max) にして既読の rts を上げる。読み続ける tx には RA を課せず、rts を書く読みは Cicada の read-only の設計 (共有の書き込みをしない) に反し、書き手を abort させる。
- 読みごとに別の snapshot を許す。一貫 snapshot を壊し、C1 と同じ巡回になる。
- ST の監視を確認の時点の PENDING の計数だけにする。確認の後に σ 以下へ遅れて置かれる版 (ST-1 の破れ) が見えない (段 6 レビュー A)。試作では設置の時刻と σ を後から照合する。
