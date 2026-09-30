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

## erratum 1 (2026-10-01 00:5x JST、計測の投入前・結果は未取得)

§2 の「1.2〜1.5 倍は、大きく伸ばせる残存費用が実測された場合だけ追加試作を 1 度認める」は、「大きく」の基準を数値で書いていなかった (段 6 焦点再レビュー FR-4)。
結果を見る前に次のとおり固定する。元の文は残す。

- **残存費用が大きい** ⇔ 代表点で、読み手除去の対照の比 R−LR / R (予備、選んだ GC 間隔、同じ job・node・round の対) の中央値が **1.5 以上**。
  意味: 長い読み手が R に課している費用が、目標 (1.5 倍) に届きうる大きさである。R−LR は上限ではない (§3) ので、これは追加試作を 1 度だけ認める材料であり、届くことの証明ではない。
- 中央値が 1.5 未満なら「残存費用は小さい」とし、1.2〜1.5 倍帯でも追加試作は推奨しない。代表点が P4 (長い読み手が無い) なら R−LR が無いので「材料不足」とする。
- R の診断値 (公開回数・境界年齢・論理生存版数) は並べて示すが、この判定には使わない。

---

以下は計測の後に書いた (§1〜§4 と erratum 1 は計測の投入前に固定した)。

## 5. 結論 — 今の VHash を主論文の候補から外すことを推奨する

**推奨 (基準との照合):** 事前記述 §2 の「有望点でも 1.2 倍未満、かつ機構は発火した」に当たるので、**今の VHash (hot 配置 v2・前進 C の最小前進) を主論文の候補から外す**ことを推奨する。
規則が選んだ代表は P3 (skew 0.97・長い読み手 1 本) の前進 C で、30 秒比較 (新しい 6 round) の比 (腕 / R) の中央値は **0.981**、隣接点 P2 でも **0.993**。
基準 (代表点 1.5・隣接点 1.3) に遠く届かず、1.2 も下回った。前進 C は trace 走行で成功 970 回、診断で P3 の契機 273,245 回のうち成功 6,353 回 (2.3%) と、機構は発火している。

1. **予備で見えた小さな勝ちは 30 秒比較で消えた。** 予備 (3 round × 10 秒) で最大だった P3 の前進 C 1.096・hot v2 K=1 1.082 は、30 秒比較で 0.981・0.935 になった。
   P2 の前進 C 0.993・hot v2 K=1 0.967。どの M の腕も R を越えていない (§6.2)。
2. **長い読み手が修正済みの最良 Cicada に課す費用そのものは大きい。** 読み手除去の対照 R−LR / R (予備、3 round そろい) は P3 **1.98**・P2 **1.56**・P1 **1.08**。
   長い読み手が居るだけで、P3 では通常 worker の throughput が約半分になる。**今の M の腕はこの費用を取り戻していない。** 長い読み手は read-only なので前進 C の対象外 (§3)、hot v2 は通常 worker の読みの第 1 段を置き換えるだけで、長い読み手の snapshot が境界を押さえることには触れない。
   R の診断では、境界年齢の p50 は P1・P2 で 8,192 µs、P3 で 16,384 µs の bucket (長い tx の無い P4 は 128 µs)。
3. **区間 GC の試作は剪定が働くが、遅い。** P3 で剪定が 74.7 万版 (P2 142 万版) 起きたが、R 比は mode 1 で P1 0.75・P2 0.40・P3 0.33、剪定しない mode 3 でも 0.98・0.90・0.63 だった。
   mode 1 / mode 3 (剪定の効果の目安) は P1 0.77・P2 0.44・P3 0.52 で、この試作では剪定がむしろ遅くしている (外した版を走行中に再利用しない mode 1 で、書き込み時の剪定自体の費用が載る)。**この試作は Steam・HANA の費用を代表しない** (§1) ので、区間 GC の SOTA についてはこれ以上言わない。
4. **比較相手に修正を入れることの効果は非常に大きい。** 修正なしの stock S の R 比は P1 0.13・P2 0.23・P3 0.39、長い読み手の完了は R の 2〜17% に落ちる。長い tx の無い P4 では S も R も同じ (0.999)。stock を相手にした勝ちを数えない規則 (§2) は、この差の大きさから見ても必要だった。
5. **残存費用の基準 (erratum 1) は「大きい」側** (P3 の R−LR / R 1.98 ≥ 1.5)。ただし代表点の M の比が 1.2 未満なので、§2 の規則では追加試作の条件 (1.2〜1.5 倍帯) に入らない。
   **次の依頼の候補として書く (依頼の「修正後も長い読み手の費用が大きく残ると分かった場合」に当たる):** 長い読み手そのものの版保持を攻める別の機構 — 長い読み手の snapshot を RA の中で安全に進める仕組み、または lock の無い区間 GC — の天井は、この wave では測っていない。R−LR / R が 1.5〜2.0 あることは、そうした機構の目標の大きさの目安にはなるが、上限でも到達の証明でもない (§3)。

**この結論から読み取ってはならないこと。**
- 評価計画の確認段の判定ではない (探索、予備 3 round・30 秒比較 6 round)。判定の上限は indeterminate で、serializable とは書かない。
- 区間 GC の SOTA (lock の無い実装) には比べていない。「区間 GC に勝った / 負けた」とは書かない。
- 「長い読み手の費用を攻める機構は届かない」とは書かない。示したのは、今の VHash の腕 (hot v2・C-min) の天井が R を越えないことである。U0 の実物 (構成 E) は修理版が無く欠測。

## 6. 結果

### 6.1 予備 (3 round × 10 秒、点 × round を 1 job、同じ job に両 GC 間隔と全腕、round ごとに腕順を回転・逆順)

GC 間隔は §4.2 どおり R の中央値だけで選んだ: P1 100 µs・P2 100 µs・P3 10 µs・P4 100 µs。比は選んだ間隔の対 (同じ job・node・round) の中央値。完了比は長い読み手の commit 数の比 (腕 / R)。

| 点 | GC µs | 腕 | 比の中央値 | 範囲 (3 対) | 完了比 | 適格 |
|---|---:|---|---:|---|---:|---|
| P1 | 100 | S | 0.127 | 0.127〜0.129 | 0.17 | 不適格 |
| P1 | 100 | R−LR | 1.077 | 1.073〜1.082 | 0.00 | 不適格 (対照) |
| P1 | 100 | hot1 | 0.979 | 0.965〜0.987 | 0.93 | 適格 |
| P1 | 100 | hot8 | 0.960 | 0.948〜0.964 | 1.01 | 適格 |
| P1 | 100 | igc1 | 0.752 | 0.739〜0.754 | 1.02 | 適格 (対照) |
| P1 | 100 | igc3 | 0.978 | 0.970〜0.980 | 1.00 | 適格 (対照) |
| P2 | 100 | S | 0.229 | 0.221〜0.234 | 0.03 | 不適格 |
| P2 | 100 | R−LR | 1.562 | 1.535〜1.659 | 0.00 | 不適格 (対照) |
| P2 | 100 | hot1 | 0.940 | 0.899〜0.956 | 0.95 | 適格 |
| P2 | 100 | hot8 | 0.982 | 0.947〜1.018 | 1.18 | 適格 |
| P2 | 100 | fwd | 0.992 | 0.903〜1.050 | 0.93 | 適格 |
| P2 | 100 | igc1 | 0.397 | 0.392〜0.417 | 1.85 | 適格 (対照) |
| P2 | 100 | igc3 | 0.901 | 0.837〜0.912 | 1.20 | 適格 (対照) |
| P3 | 10 | S | 0.388 | 0.352〜0.451 | 0.02 | 不適格 |
| P3 | 10 | R−LR | 1.984 | 1.726〜2.336 | 0.00 | 不適格 (対照) |
| P3 | 10 | hot1 | 1.082 | 0.973〜1.123 | 1.08 | 適格 |
| P3 | 10 | hot8 | 0.962 | 0.884〜1.092 | 1.75 | 適格 |
| P3 | 10 | fwd | 1.096 | 0.901〜1.278 | 1.05 | 適格 |
| P3 | 10 | igc1 | 0.326 | 0.301〜0.378 | 3.03 | 適格 (対照) |
| P3 | 10 | igc3 | 0.633 | 0.588〜0.759 | 2.27 | 適格 (対照) |
| P4 | 100 | S | 0.999 | 0.998〜1.000 | — | — |
| P4 | 100 | hot1 | 0.978 | 0.977〜0.979 | — | 適格 |
| P4 | 100 | hot8 | 0.970 | 0.969〜0.970 | — | 適格 |

(R−LR の完了比 0 は、長い読み手を除いた走行なので定義どおり。区間 GC の完了比が 1 を大きく超えるのは、通常 worker が遅くなって長い読み手が相対的に進むためである。)

規則 (§4.5) の結果: 代表 = P3 の前進 C (適格な M 腕の最大 1.096)、次点 = P3 の hot v2 K=1、隣接点 = P2。相手側の追加調整 (代表の予備の比 ≥1.5) と P4・P4′ の追加 (P4 の M 腕 ≥1.3) はどちらも発火しなかった。

### 6.2 30 秒比較 (新しい 6 round、代表点 P3 は GC 10 µs、隣接点 P2 は GC 100 µs、腕 S・R・前進 C・hot v2 K=1)

| 点 | 腕 | 比の中央値 | 範囲 (6 対) | 完了比 | 適格 |
|---|---|---:|---|---:|---|
| P3 | fwd (代表) | **0.981** | 0.701〜0.998 | 0.84 | 適格 |
| P3 | hot1 (次点) | 0.935 | 0.817〜1.316 | 1.01 | 適格 |
| P3 | S | 0.365 | 0.348〜0.510 | 0.01 | 不適格 |
| P2 | fwd | **0.993** | 0.804〜1.153 | 0.93 | 適格 |
| P2 | hot1 | 0.967 | 0.925〜1.117 | 0.94 | 適格 |
| P2 | S | 0.241 | 0.234〜0.271 | 0.01 | 不適格 |

判定 (§2 と erratum 1 の規則を driver の判定関数で機械的に当てた。集計の逐語は `verbatim/analysis-final_decision.md`、出力は `analysis/final-decision.json`): 代表点 0.981 < 1.2 かつ機構が発火 → **「今の VHash を主論文候補から外す推奨」**。継続の判定 (1.5 / 1.3) は「基準未達」。

### 6.3 正しさ (trace build、判定器 `python -m orchestrator.verify --protocol cicada`)

計測の規模 (48 thread・100 万 record) ではなく、4 thread・record 200・長い読み手ありの小規模走行 (1 秒)。全 commit 数 = 全 C 行数と、長い読み手の完了数 = batch worker の C 行数を別々に照合した。

| 腕 | 判定 | 巡回 | batch worker の C 行 | 機構 witness |
|---|---|---:|---:|---|
| S | 巡回 0、上限 indeterminate (rc 3) | 0 | 44 | — |
| R | 同上 | 0 | 3,316 | ro-gcflag の flag 立て 3,315 |
| hot v2 K=1 | 同上 | 0 | 3,390 | hot の hit 743,778 |
| hot v2 K=8 | 同上 | 0 | 3,811 | hot の hit 800,612 |
| 前進 C (K=1) | 同上 | 0 | 3,283 | 前進成功 970 |
| 区間 GC mode 1 | 同上 | 0 | 3,850 | 剪定 844,429 |
| 壊し正例 (区間 GC + 見える版まで外す) | **巡回 43** (正例成立) | 43 | 3,929 | 剪定 818,434 |

**失格の腕は無い。** 壊し正例は事前登録どおり区間 GC の木・長い読み手ありで判定器に検出された (md_18 では長い読み手の cell で剪定 0 のため正例が不成立だった)。

### 6.4 診断 (計数入り build、各点 1 走 × 1 秒、性能値には使わない)

- **公開と境界 (VLIFE、S・R):** S は P1〜P3 で公開 0 回 (境界は定義されない)。R は公開が戻るが、境界年齢の p50 は P1・P2 8,192 µs、P3 16,384 µs の bucket (P4 は 128 µs)。R の ro-gcflag の flag 立ては ro commit とほぼ同数 (P3 88 / 88)。
- **前進 C:** P2 で契機 135,942・試行 7,455・成功 6,096、P3 で契機 273,245・試行 9,544・成功 6,353。契機の 94〜97% が前進先なし (`no_target`)。
- **hot v2:** P3 の K=1 は hot の hit 1,754,077・cold 141,502・隣接確認の外れ 159,810。K=8 は hit 1,512,959・外れ 342,393。
- **区間 GC:** mode 1 の剪定 (外して保留した版) は P1 36.6 万・P2 142 万・P3 74.7 万版。mode 3 は 0。鎖上の版数はどちらも約 100 万版 (record 数と同程度) で、mode 1 は外した版を走行中に再利用しないので bytes は返らない。
- 集計の逐語は `verbatim/analysis-diag_extract.md`。

## 7. 実行の記録と計算量

- **smoke:** 1 回目 (40040.nqsv、55 s) は perf の -D 完全一致検査が CMake 由来の Boost の定義 2 つで停止 (期待集合の誤り、fix 2)。2 回目 (40111.nqsv、185 s) は区間 GC の木で KeyError (fix 4・6 の FR-5)。3 回目は perf・診断 8 木 (40210.nqsv、bnode017) と trace 5 木 (40212.nqsv、bnode024) を別 checkout から並行し、子は rc 0 で全 19 binary と inert の前処理一致を出した。dispatch の親は login の qstat / qsub の 30 秒 timeout で rc 16 (login の load 41〜75) を返し、job の Elapse を記録できなかった (各 約 400 s・約 260 s と見積る)。runbook §7.6 どおり終端を確かめて orphan hold を外した。
- **本計測:** binary は smoke の出力 (manifest と sha256 で束縛) をそのまま使い、build job は投げていない。予備 12 job (各 90〜184 s、計 1,841 s)、30 秒比較 12 job と診断 4 job (計 1,648 s)、正しさ検査 2 job (35 s・63 s)。計測用 checkout 3 本と wave 木から lane ごとに直列に dispatch し、同時に 3〜4 node を使った。1 job の直列条件数は予備 8〜16 走、30 秒比較 4 走。
- **合計:** smoke 約 900 s + 本計測 3,587 s + 焦点走・変異の計算ノード分 ≈ **1.5 node 時間** (2 node 時間未満)。
- 全 raw は `raw/` (gzip -9): `perf-all.jsonl.gz` (予備 162 走 + 30 秒比較 48 走)、`diag-all.jsonl.gz` (診断 24 走)、`verify-all.json.gz` (正しさ検査 7 腕)。

## 8. 何を確かめ、何を確かめていないか

**確かめたこと (実測):** 本計測の全 234 走 rc 0。同じ点の腕は同じ job・同じ node で、round ごとに順序を回転・逆順。30 秒比較の run ID は予備と重複なし (driver が拒否する)。perf build の -D 集合が腕ごとの期待集合と完全一致 (build 時に検査)。新 workload patch の macro 0 で owner TU の前処理が pin と一致 (smoke)。7 腕の正しさ検査と壊し正例 (§6.3)。

**確かめていないこと・限界:**
- **判定の上限は indeterminate。** 正しさ検査は小規模走行で、計測の規模ではない。
- **小標本。** 予備 3 round、30 秒比較 6 round。探索の判断材料であり、確認段の統計判定ではない。
- **U0 の実物 (構成 E) は欠測** (修理版 md_39 が起点の main に無い)。長い読み手を RA の中で前進させる仕組みは測っていない。
- **区間 GC は試作だけ。** lock の無い実装、安全な物理再利用は未実装 (md_18)。
- **batchR の長さは操作数 (1,000 read) で作った。** 実時間の長さは点ごとに違う。
- **driver の予算 gate は機械的に効いていない所がある** (段 6 の焦点再レビュー 2 巡目の所見 FR2-1〜FR2-5 と変異 M25 の正例。fix 子が 3 回とも test の期待値の許可の不足で止まり、land 調整役と合意して打ち切った)。この wave では次の 4 点を**親が運用で担保した**:
  1. 投入は点 × round で親が組んだ (driver の計画関数の job 分割は使っていない)。
  2. 条件付き job の発火と 2 node 時間の判定は親が追った (発火なし、合計 約 1.5 node 時間)。
  3. R−LR の揃いは段 7 で親が確かめた: 代表点 P3 の R−LR の対は round 1・2・3 の 3 対そろい (`analysis/final-decision.json` の `residual_cost.rounds`)。
  4. build job は投げていない (smoke の binary を manifest 照合で再利用)。
- **driver の aggregate は 30 秒比較の両点を代表点の GC 間隔で組むため、P2 (100 µs で走らせた) の対が作れず停止した。** 事前記述 §4.2 は「点ごとに選んだ間隔」なので、親が driver の関数をそのまま使い、両点を各点の間隔で組む集計を repo 外で行った。driver の `aggregate_diagnostics` も前進 C の parser が長い tx の行を要求して止まったので、診断値は親の要約 script で読んだ。作図器も同じ aggregate を呼ぶため 30 秒比較のパネルを描けず、予備の図にも表の見出しの重なりが残ったので、この版では図を載せていない。いずれも driver・作図器の修理は次の依頼の候補。

## 9. 実装と検証の記録

- **変更 file:** `patches/cicada-ceiling-workload.patch` (新設、macro `IZANAGI_CICADA_CEILING_WORKLOAD`、owner TU 2 site・header 2 site)、条件 gate の登録と閉包 (`condition_meaning_gate.py`・`screening_driver.py`・test 3 本、件数 pin を完成 patch の実 site から数え直し)、driver `orchestrator/campaign/vhash_ceiling_vs_sota.py` と test、作図器 `tools/plotting/plot_vhash_ceiling_vs_sota.py` と test、登録面 (`materializer_admission.py`・`test_ccbench_spawn_sites.py`・`test_p3_build_authority_cli.py`・`orchestrator/tests/README.md`)、`patches/README.md` と `tools/plotting/README.md` の節。
- **子の工数 (Codex):** plan 1・相談 2・author 3 (単位 A 1、単位 B 2 = 初回は docs の所有外で実装 0 のまま停止)・review 2・焦点再レビュー 2・fix 7 (fix 3 は報告が受理検査の byte 下限未満、fix 5・fix 7 は既存 test の期待値の許可不足で編集 0 のまま停止)。実装面の変更はすべて Codex `role=author`。
- **段 3 相談:** A (正しさ・整合) NO-GO、B (過剰・削除) 条件付き GO。must-fix は全採用 (`verbatim/s4-ruling.md`)。親の提案 P4 (R−LR を上限とする) は両相談が「上限ではない」と反証し、対照に格下げした。
- **段 6:** レビュー A・B とも NO-GO → fix 1〜3 → 焦点再レビュー 1 巡目 NO-GO → fix 4〜6 → 2 巡目 NO-GO → fix 7 は停止。DW-O16 の 3 巡上限で打ち切り、残所見 (予算 gate 周り) は §8 の運用担保として閉じた。正しさ・比の計算・判定の規則に関わる所見はすべて閉じた。
- **焦点走 (計算ノード):** 単位 A 30 file (3,743 passed・3 failed = 新 macro 1 個ぶんの件数 pin、許可して fix 1 で直した)、統合後 21 file (2,576 passed・3 failed = 同じ)、fix 1 後 10 file (700 passed・1 failed = 同型、fix 3)、fix 4・6 後 11 file (1,054 passed・0 failed)。main 取り込み後の結果は §10。
- **変異:** 登録 M1〜M25 (段 4 の M1〜M12、段 6 の M13〜M25)。M26〜M28 は fix 7 が停止して gate が実装されなかったので取り下げた (登録は `verbatim/s6-ruling-6.md` に残す)。
  期待 node は login の自走 probe (`verbatim/mutation-probe.md`。計測用 checkout の固定 commit 3dcdbbe4e へ注入 → 自走 → bytes を書き戻して sha256 照合) で集めた: 基準走緑、M0 (等価の対照) 生存、M1〜M24・M25b KILLED、M25 生存 (登録どおり: 条件付き job を常に足す変異は、未発火の条件付き job を持つ計画に予算 gate を呼ぶ正例が無いため検出されない。実効 gate へ再照準した M25b = committed の秒数を常に全体にする変異は KILLED)。
  本走は固定 commit 3dcdbbe4e に `tools/mutation_harness.py` を直接当てた (dispatch)。1 回目は M0〜M8 で、subTest を使う test の失敗が pytest の FAILED 行にならないため M1・M2 が node の不一致 (他の test は赤で KILLED)、M8 が抽出不能で harness が停止した。
  2 回目は M1・M2 の期待 node を dispatch の観測に改め、M8 は自走 probe の KILLED (期待 node と完全一致) を証拠に本走から外したが、親が同じ木から集計のために import して `__pycache__` を作ったため harness の復元検査が 8 本目の後で停止した (M1・M2・M9〜M14 は KILLED)。
  3 回目は残り 12 本 (M15〜M25b) で完走: KILLED 11・SURVIVED 1 (M25、登録どおり)。
  本走の合計: 26 本すべて登録どおり (M0・M3〜M7 は 1 回目、M1・M2・M9〜M14 は 2 回目、M15〜M25b は 3 回目)、M8 は自走 probe のみ。

## 10. main 取り込み後の確認

記録の前に local main (46460068c、90 commit 先行) を取り込んだ (efc82271d)。文字の競合は 0 件。登録 2 file は main 側の版を採り、Codex の登録差分を当て直した (138c154f3)。
取り込み後の木 (138c154f3) の焦点走 (計算ノード、18 file: 本 wave の test 2 本、条件 gate・screening・spawn sites・build authority・p3_s4_loop の test、inventory 4 群、plain runner coverage、bytecode guard、VHash の既存 driver の test 3 本、artifact admission、buildcache): **2,621 passed・5 skipped・0 failed** (Elapse 175 s)。
計測と変異は取り込み前の commit 3dcdbbe4e で取った。取り込みは計測・判定に関わる code (driver・patch・条件 gate) を変えていない (main 側の変更は別機構の登録と patches/README.md の別節)。

## 11. 次の版 (paper-story-vhash) へ

- **結論の芯:** 長い読み手で版が溜まる負荷で、今の VHash の腕 (hot 配置 v2・前進 C の最小前進) は修正済みの最良 Cicada (R) を越えない (30 秒比較の比 0.93〜0.99)。VHash を今の形で論文の題材にしない推奨。
- **残る研究の芽:** 長い読み手が R に課す費用は大きい (R−LR / R が 1.5〜2.0)。これを取り戻すには長い読み手そのものの版保持を攻める機構が要り、今の VHash の構成 (read-write tx の前進、通常 worker の hot) はそれに触れない。
- **比較相手の修正の効果:** stock に比べ修正入りの R は 2.6〜7.9 倍 (長い読み手あり)。論文で修正の効果と本案の効果を分けて書く方針 (D2322 項 2) の裏付けになる。
- **限界:** 探索 (小標本)、判定の上限は indeterminate、U0 の実物 (構成 E) は欠測、区間 GC の SOTA は未比較、図はこの版では載せていない (§8)。
