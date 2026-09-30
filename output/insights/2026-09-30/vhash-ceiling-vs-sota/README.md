# VHash md_42: 利得の天井を、修正済みの最良 Cicada と区間 GC を相手に測る (勝てる負荷の第 2 段、T-2962)

wave `dev-wave-vhash-ceiling-vs-sota` (branch `worktree-dev-wave-vhash-ceiling-vs-sota`)。起点 local main `d79fd3524` (開始 gate fresh rc 0、2026-09-30 19:5x JST)、段 4 の前に `908741c6f` (md_37 hot v2 の着地を含む) へ ff-only で進めた。
CCBench submodule = pin `68106660` (動かしていない)。依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_42.txt` と同 dir の `common.txt`。段 1〜4 の逐語は `verbatim/`。

**§1〜§4 は計測の投入前に commit する事前記述である。結果を見てから変えない。** 変える必要が出たら、元の文を残して erratum を追記する。
この wave は VHash を論文の題材として続けるかを決める**探索**であり、評価計画の確認段ではない。

## 1. 条件 C・手法 M・C での SOTA

**条件 C (長い読み手で版が溜まる負荷):** 1 worker が 1,000 read の read-only tx を途切れなく続け (batchR)、他の 47 worker が短い更新 tx (10 操作、読み比率 5%) を回す YCSB。
record 100 万・値 4 B。md_29 (`output/insights/2026-09-30/vhash-workload-space/README.md` §0・§4) が、stock Cicada で MinRts の公開が止まり版が record の 5〜15 倍に溜まることを示した領域 (候補 (a)(c)(d)) である。
対照の条件として、長い tx の無い read-only 指定率 95%・12 thread (候補 (b)) を置く。

**手法 M (VHash):** 版を抱える期間を縮める保持の側 (U0) を芯にし、cold への進入を前進の契機にする U1 (前進 C) と、直近の少数版を手元に置く hot 配置を加えた機構の組 (D2322 項 1)。
この wave で実物として比べられる M の腕は **hot v2 (B-post、md_37・D2331) の K=1・K=8** と **前進 C の最小前進 (C-min、K=1)** の 3 本である。
U0 の実物 (構成 E) は修理版 (md_39) が起点の main に無いので欠測とし、旧 E で代用しない。

**C での SOTA:** (i) ro-gcflag 修正入りの md_11 の観測最良設定 Cicada (`B0 O1 P0 R1 W0` + `IZANAGI_CICADA_RO_GCFLAG=1`)。以下「md_11 の観測最良設定 + 修正」= **R** と呼ぶ (D2322 項 2)。
修正なしの stock (**S**) は修正の効果を分ける対照として同じ round に置く。
(ii) 長い tx 向けの GC として、途中版を剪定する区間 GC (Steam §4.3・SAP HANA HybridGC 定義 1・vDriver 定理 3.5。`output/insights/2026-09-29/vhash-interval-gc/README.md` §2 の対照表)。

**SOTA (ii) の穴:** この repo の区間 GC 試作 (md_18、`patches/cicada-interval-gc-variant.patch`) は install を tuple lock の下で行い、その lock 待ちが thread 時間の 8〜72% を占めた (md_18 §1 項 4)。
Steam・HANA の実装費用を代表しないので、**この試作に勝っても「SOTA に勝った」とは書かない。** 論文で (ii) を埋める案と穴の大きさ:

- 案 A — 原典の数値を引用する: Steam は CH-benCHmark (OLAP 1 + OLTP 1) で途中版の剪定により 6,554 → 30,580 txn/s (Table 5、約 4.7 倍)、HANA は長い cursor の下で版数をほぼ一定に保った (Fig 10・11)。
  系・負荷・実装が違うので、Cicada 上の比と並べて比べられない。位置づけにだけ使える。
- 案 B — より公正な試作: install の lock を外す (剪定と挿入の競合を CAS 前の印で閉じる、md_18 §9 項 3)。未設計・未実装で、安全な物理再利用も未解決 (md_18 §3.4)。
- 案 C — この wave で囲める分: 同じ install 経路で剪定しない mode 3 と剪定する mode 1 を並べ、剪定の効果 (mode 1 / mode 3) を install 費用から切り離す。
  これは「lock の無い区間 GC が R に上乗せできる量」の目安にはなるが、剪定の実装費用を含むので上限ではない。
- **穴の大きさ:** lock なしの区間 GC の R 比は未測定であり、この wave の値では埋まらない。この wave の推奨は **R に対する研究継続の判断**に限り、区間 GC の SOTA との比較は独立の残課題として残す。

## 2. 継続・撤退の基準 (研究投資の基準。評価計画の統計判定は置き換えない)

- 目標は R に対して 2 倍級。**代表点の 30 秒比較で、同じ M の腕の比 (腕 / R、同じ round・同じ node の対) の中央値が 1.5 倍以上、かつ隣接点でも同じ腕が 1.3 倍以上なら継続の材料。**
- **有望点でも 1.2 倍未満で、縮むのが境界年齢・版数だけなら、今の VHash を主論文の候補から外すことを推奨する。**
  M の腕の版数は計器が当たらないので測れない (§4.3)。この条件は「比 <1.2 かつ、その腕の機構が発火した (§3 の witness が非空)」で判定し、発火しなければ「未判定 (機構が働かない負荷)」と書く。
- 1.2〜1.5 倍は、大きく伸ばせる残存費用が実測された場合だけ追加試作を 1 度認める。残存費用の材料は、R の診断値 (公開回数・境界年齢・論理生存版数) と、読み手除去の対照 R−LR の比である。
- **数えない勝ち:**
  - stock (S) だけに勝つ勝ち。
  - GC 間隔を悪くした相手だけに勝つ勝ち (§4.2 の固定規則の外の間隔での比)。
  - 長い読み手が完了しなくなる勝ち。対ごとに batch 完了数の比 (腕 / R) を取り、点 × 腕の中央値が **0.8 未満**なら数えない。P1〜P3 で batch 完了数 0 の走行は失格。
  - 正しさの欠陥がある勝ち。判定器の巡回、integrity の数値項目 ≠ 0、全 commit 数 ≠ 全 C 行数、batch 完了数 ≠ batch worker の C 行数、既読 WTS の食い違いのいずれか。
  - 機構が trace 走行で発火しなかった腕の勝ち (§4.4)。
- 区間 GC の腕 (試作) と R−LR の比は M の勝ちとして数えない。
- 隣接点を削った場合、継続基準は「判定不能」とする。

## 3. 腕ごとの発火条件 (この負荷で機構が実際に働くか)

| 腕 | P1〜P3 (長い読み手 1 本) | P4 (ro 95%・長い tx なし) |
|---|---|---|
| S (修正なし stock) | 長い読み手の read-only commit は `mainte()` を通らず GC flag を立てない (md_22)。leader は全 worker の flag を待つので MinRts の公開が止まり、版が溜まる (md_29 の batchR 84 行すべてで公開 0 回) | ro commit が flag を立てないので公開が遅れる (md_22 の ro 95% で公開 4,978〜7,314 回 / 3 秒) |
| R (修正入り、主な相手) | ro commit ごとに `mainte()` が flag を立て (`patches/cicada-ro-gcflag-variant.patch`)、公開が戻る。ただし長い読み手の tx の間はその rts が境界を押さえるので、tx 1 本の長さ分の版は残る (md_22 §0 項 6) | 公開が大きく増える (md_22: 約 14 万回 / 3 秒) |
| R−LR (読み手除去の対照、予備のみ) | R と同じ binary で batch_th_num=0 (通常 worker 47 本はそのまま)。長い読み手の費用の目安であり、上限ではない (worker の組・競合・GC の状態も変わる) | 置かない |
| R + hot v2 K=1・K=8 (M) | 通常 worker の read は hot (版の列の手がかり) を先に見て、隣接確認が通れば列を辿らない。書き込みは B-post の短い書き区間で hot に書き足す (D2331)。**長い読み手の snapshot は古く、熱いキーでは hot の K 件より古い版を読むので cold (hot の外れ) になり、stock の走査へ落ちる**見込み。通常 worker の read は読み比率 5% で tx あたり約 0.5 回 | read-only の read が多い。md_37 は thread 48・ro 95% で stock 比 0.94〜1.02 (差なし) だった。thread 12 は未測定 |
| R + C-min K=1 (M、P2・P3) | 前進は `!this->is_ronly_` の tx の read だけ (`patches/cicada-forwarding-variant.patch` の read_internal の条件)。**長い読み手 (read-only) は前進しない。** 通常 tx の read で版の列の K=1 より奥へ入りそうなときだけ発火し、md_29 の h2 (前進候補の割合) は最大 0.046 | 置かない |
| R + 区間 GC mode 1 (対照) | R で MinRts が公開されるので剪定の条件 (e) の足場ができる。書き込み時に、長い読み手の snapshot から見える版と最新版の間の途中版を鎖から外す (再利用はしない) | 置かない |
| R + 区間 GC mode 3 (対照) | mode 1 と同じ install 経路 (tuple lock の下) で剪定を呼ばない。mode 1 / mode 3 が剪定の効果、mode 3 / R が install 経路の費用 | 置かない |
| GC 接続 E (参考、走らせない) | read-only tx は対象外 (`patches/cicada-forwarding-gc.patch` の `if (tx.is_ronly_ ...) return;`)。長い読み手の snapshot は前進しない。RA の外で読み続ける tx を前進させる試作は依頼でしない | — |

**先に言えること:** 長い読み手の版保持そのものに効く可能性がある腕は、M の中には無い (hot v2 と C-min はどちらも長い読み手の読みを速くせず、境界も動かさない)。
M の腕が勝つとすれば、通常 worker の読み書きが速くなる経路だけである。区間 GC は長い読み手の snapshot の下の途中版を外すが、試作の install 費用が大きい。

## 4. 手順 (段 4 裁定の plan v2、`verbatim/s4-ruling.md`)

### 4.1 点と腕

| 点 | 条件 | 予備の腕 |
|---|---|---|
| P1 | rr 5・ro 指定 0%・通常 47 + batchR 1・skew 0.6 | S、R、R−LR、R+hot K=1、R+hot K=8、R+区間 GC mode 1、mode 3 |
| P2 | P1 の skew 0.9 | P1 の腕 + R+C-min K=1 |
| P3 | P1 の skew 0.97 | P2 と同じ |
| P4 | rr 50・ro 指定 95%・通常 12・skew 0.9・長い tx なし | S、R、R+hot K=1、R+hot K=8 |

共通: record 100 万・値 4 B・通常 tx 10 操作・batchR は 1,000 read の read-only tx・clocks_per_us 2100・genome `B0 O1 P0 R1 W0` (全腕共通、S だけ ro-gcflag なし)。
長い読み手と ro 指定率の生成は、新しい最小の workload patch `patches/cicada-ceiling-workload.patch` (macro `IZANAGI_CICADA_CEILING_WORKLOAD`、既定 0 で inert) が全腕共通に行う。
batch 完了数は、batch worker の既存の per-thread commit 数を計測窓の後に 1 行出すだけで、hot path に計数を足さない。

### 4.2 GC 間隔の固定規則

予備で全腕を gc_inter_us 10・100 µs の両方で走らせる。点ごとに **R の throughput の中央値 (3 round) が高い方**を選ぶ (同値は 10 µs)。以後、その点の全腕をその間隔の値で読む。M の腕の値は選択に使わない。

### 4.3 性能値・診断値・正しさを分ける (規律 1・2)

- **性能値:** TRACE・COUNT・VLIFE を外した build だけ。compile command の -D 集合が腕ごとの期待集合と完全一致することを driver が検査する。throughput は通常 worker の commit 数 / 秒 (batch worker の commit を除く)。
- **診断値 (別 build・各 1 走):** S・R は VLIFE 計器 (公開回数・境界年齢・論理生存版数、当たる木だけ)、hot は hot の計数 (hit・cold・fallback)、C-min は前進の計数 (試行・成功)、区間 GC は自前の計数 (公開・剪定・鎖)。M の腕の版数は計器が当たらず欠測。診断 build の throughput は性能値に使わない。
- **正しさ (trace build):** 各腕と新 workload の組を `instr-cicada-trace.patch` の木で走らせ、判定器 (`python -m orchestrator.verify --protocol cicada`) に掛ける。巡回 0・integrity の数値項目 0・全 commit 数 = 全 C 行数・batch 完了数 = batch worker の C 行数・既読 WTS の食い違い 0 を要求する。判定の上限は indeterminate で、certified とは書かない。

### 4.4 trace 走行の機構 witness と壊し正例

腕ごとに trace 走行で次が非空であることを要求する: 全腕 = batch worker の C 行 ≥1 (P1〜P3 型)、R = ro-gcflag の flag 立て ≥1、hot = hot の hit ≥1、C-min = 前進成功 ≥1、区間 GC mode 1 = 剪定 ≥1。
0 なら走行時間を 1 → 3 秒に 1 回だけ延ばし、なお 0 なら「未検証 (機構未行使)」とし、その腕の値は継続判定に使わない。
壊し正例は 1 本: `patches/broken-cicada-interval-gc-overprune.patch` を R + 区間 GC の木に重ね、長い読み手ありで走らせ、判定器が巡回を出すことを確かめる。出なければ「正例不成立」と書き、別の cell や patch へ付け替えない。

### 4.5 有望点・代表の腕・隣接点・30 秒比較

- P1〜P3 の各点で、M の各腕の予備の比 (選んだ GC 間隔、同じ round・node の対) の中央値を出す。完了比の中央値 ≥0.8 かつ §4.4 の witness が非空の腕だけを候補にし、最大の (点, 腕) を代表とする (同値は点 P2→P3→P1、腕 hot K=1→hot K=8→C-min)。
- 隣接点は P2→P3、P1→P2、P3→P2。全敗でも P2 と最大の M 腕を代表として残す。
- P4 は別の条件として報告する。P4 の M の腕の予備の比の中央値が 1.3 以上なら、30 秒比較に P4 と隣接の P4′ (skew 0.97) を加える。
- 代表点の予備で M の腕の比の中央値が 1.5 以上なら、30 秒比較の前に R を GC 間隔 {1, 10, 100, 1000} µs で 3 round ずつ走らせ、最良の間隔を 30 秒比較に使う (相手側の追加調整)。
- 30 秒比較は代表点と隣接点で、S・R・代表 M 腕・次点 M 腕の 4 腕 × 新しい 6 round × 30 秒。予備の run は再利用しない。

### 4.6 計算の組み方

1 job は 5 分程度を目安にし、多数を同時に投げる (ユーザー方針 2026-09-30)。同じ点の比較腕は同じ job・同じ node に入れ、round ごとに腕の順序を回転・逆順にして位置を均衡させる。1 node 1 job、node local の $TMPDIR を使い、共有の repo 状態に書かない。
build は木ごとの build job で作り、binary ごとの manifest (pin・patch と順序・macro・compile command・compiler・binary の sha256) と一緒に共有の一時領域へ置く。計測 job は node local へ写して manifest と照合してから走らせる。
各 job の直列条件数と見積り秒、合計の node 時間は smoke の実測の後に §5 に書く。合計が 2 node 時間を超える見込みなら、削り順 (S の非選択間隔 → 区間 GC mode 3 の P1 → R−LR → C-min の P3) か、land 調整役への相談で決める。隣接点・R・正しさ検査・代表の M 腕は削らない。
