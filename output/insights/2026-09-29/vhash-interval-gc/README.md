# Cicada に区間 GC (最小形・一般形) を試作した (VHash 論文 md_18、2026-09-29〜30)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-interval-gc`、起点 local main `5f23b9e45` (開始 gate rc 0、2026-09-29 17:5x JST)、CCBench submodule = pin `68106660` (動かしていない)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-interval-gc/` (段 1 brief・段 2 plan・段 3 相談・段 4 / 6 裁定 `s4-ruling.md`・`s6-ruling.md`・Codex の prompt と報告・文献抽出 `lit-extract.md`)。
依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_18.txt`。計測の原本は `/work/SFC/tanab/tmp/vhash-interval-gc-2026-09-29/` (`bundle1/`・`parts3/` の 40 part・`aggregate4/`)。

**この文書の性能値・計数はすべて「未検証の診断値」である。** 区間 GC を入れた Cicada が serializable だとは書かない (§5)。

## 1. 依頼と結論

依頼 (md_18): Steam §4.3 と SAP HANA の区間 GC の原典と、ユーザー案 (最古と 2 番目の境界の間を掃除する) を照合する。Cicada に最小形 (最初の隙間だけ) と
一般形 (全ての隙間) を inert な切替式 patch で試作する。md_3 の検査器と「見える版まで消す」壊し patch で正しさを確かめる。長い tx 1 本 + online の負荷で、
md_11 の最良設定 (B0 O1 P0 R1 W0、GC 10/100 µs) の stock と同時刻に比べる。区間 GC の後に残る費用と VHash (forwarding・U0) の余地を、実測と見積りに分けて書く。

結論:

1. **案そのものは既知である。** 最小形は vDriver の Fig 6(c)・定義 3.4・定理 3.5 に、一般形は Steam §4.3・HANA 定義 1・vDriver 定理 3.5 に書かれている (§2)。
   3 本とも「reader が辿っている途中版を物理的に解放しない条件」は、読んだ範囲では独立に述べていない。
2. **試作は動くが、安全な物理再利用までは作れなかった。** 外した版を再利用する mode 0 は、4 回の修正 (補正 3〜5、A13) の後も SIGSEGV・停止した。
   計測した変種は「版を鎖から外すが、走行中は再利用しない」(mode 1、補正 6) である。外した版の bytes は走行中に返らない (§3.4)。
3. **正常 3 腕の検査は全て巡回 0。ただし事前登録した壊し patch の正例は不成立。** stock・最小形・一般形 × 5 cell × 2 thread 数の 30 走行が、全て巡回 0・integrity 0・
   indeterminate だった。事前登録の正例 cell (長い read-only tx の ronly_wait) では、試作が一度も剪定しないので壊し patch も発火 0 だった。
   K・R・wait_after_reads の巡回検出 6 件は、事前登録外の補助として別に数える (§5)。
4. **この試作の費用は、剪定よりも install の経路が支配する。** 補正 5 で「書き込みを tuple lock の下で挿入する」にしたため、install の lock 待ちが thread 時間の
   8〜72% を占めた。throughput は stock 比で最小形 0.062〜0.692・一般形 0.025〜0.684 である。剪定が 0 回の長い read-only の cell でも最小形は 0.062 (rr50) まで落ちた (§6.3)。
5. **鎖・hop の腕間差は、書き込み量の差と交絡している。** 区間 GC の腕は install 数が stock の 1/1.3〜1/34 なので、hop 総数・鎖上の版数の減少を剪定の効果と読めない。
   剪定 0 の read-only cell でも online read-only の hop は stock の 1/138 になった (rr50)。剪定の効果を切り分けるには、同じ install 経路で剪定しない mode 3 の同時刻対照が要る (§9)。
6. **区間 GC が最も効くはずの「長い read-only tx」で、試作は何もしなかった。** read-only の commit が GC の flag を立てないので MinRts が公開されず
   (4 cell 全腕で公開 0 回)、条件 (e) の足場が無く剪定 0 だった。stock はこの型で鎖 2.2 GB・RSS 6.0 GB (rr50) に達する。
   同じ原因は `vhash-readonly-gc-publish` が別に見つけて直している (§7)。
7. **VHash への含意 (見積り):** 区間 GC は鎖を短くできても、外した版の bytes は長い tx の終了まで安全には返せない (§3.4)。bytes と再利用の側は、境界を前へ動かす U0 の担当として残る。
   ただし U0 の試作も zipf 0.9 では前進の成功が 0.05〜0.27% で効果が消えている (§7)。

## 2. 先行研究との対応 (原典の読んだ範囲つき)

抽出: Claude sonnet の読取専用の子 (job dir `lit-extract.md`、原文の短い逐語と節・ページつき)。原典は md_1 が取得した `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/` の PDF とテキスト (Steam は `steam-boettcher-pvldb13-2019.*` と `bottcher-pvldb2019.*` が byte 一致の同一論文)。検索記録の成熟度は RW0〜RW1 相当 (`docs/related-work/README.md` 7.7.3) で、「新しい」「先行なし」とは書けない。「記述なし」は読んだ節に限った不在である。

| 観点 | ユーザー案 (最小形 / 一般形) | Steam (Böttcher ほか, PVLDB 13(2) 2019) | SAP HANA HybridGC (Lee ほか, SIGMOD 2016) | vDriver (Kim ほか, 技術報告) |
|---|---|---|---|---|
| 判定に使う timestamp | 最小形: 最古と 2 番目の境界。一般形: 実行中 timestamp の集合 | 全 active tx の start timestamp のソート済み集合 (§4.3、p.133)。最古だけの方式と対比 (§2.1、p.129) | 全 active snapshot timestamp の順序集合 (global STS tracker、§4.1、pp.1311–1312) | 全 live tx の begin timestamp から作る dead zone の列 (定義 3.4、PDF p.4)。最古と 2 番目の間の zone を描く図もある (Fig 6(c)、PDF p.7) |
| 回収する版の定義 | 最小形: 最古の境界で見える版と 2 番目で見える版の間。一般形: どの点からも見えない版 | 各 active timestamp で見える版と最新版の間の版を除く (§4.3、Fig 6) | 可視区間 [t, 次の版の timestamp) に集合の要素が 1 つも無い版 (定義 1、pp.1310–1311) | 可視区間が dead zone に完全に含まれる版 (定理 3.5、PDF p.4) |
| 判定の単位 | キー (版の列) ごと | 版の列ごと (§4.3)。tx 単位の回収と併用 (§4.1) | 区間判定は単一版の列ごと。group 単位は timestamp 判定だけ (§4.2、p.1312) | 版ごと (移動時) と segment ごと (§3.4、PDF p.8) |
| 契機 | (本 wave の実装: 書き込み時) | 版の列が伸びる更新・挿入の時に、その worker が即時に (§3、p.130、§4.3.2、p.134) | 背景 thread の周期起動、区間 GC は 10 秒 (§5.1、p.1314) | 版の移動時 (更新 tx) と背景の segment 回収 (§3.3・§3.4) |
| 物理回収の安全条件 | (本 wave の実装: §3.4) | unlink と解放を分け、解放は所有 tx の解放まで遅らせる (§3、p.131)。reader が辿っている版への安全の論拠は記述なし (読んだ範囲: §3、§4.1–§4.4、§5.7) | 記述なし (読んだ範囲: §2.2、§3、§4.1–§4.4)。§6.2 の hazard pointer 等は言語 runtime の説明で HANA の機構ではない | 回収側と挿入側の競合を atomic TAS で解決 (§3.4、PDF pp.9–10)。reader が辿っている版への安全は記述なし (読んだ範囲: §3.4、§3.5 冒頭、§4.3 相当と語の検索) |
| 長い tx が複数 | 一般形が扱う | 版の列の長さは active tx 数まで (§3)。OLAP thread を増やす評価 (Fig 9、§5.3) | 手法は複数要素の集合で動く (§3.1)。複数の長い tx を並べた実験は記述なし (読んだ範囲: §5.2–§5.6) | 複数の長い tx で wide dead zone が複数でき、非連続の segment 切除が起こる (§3.4) |
| 効果 (原典の値) | 本 wave §6 | 版の列の平均長 287.43 → 1.07、最大 30,287 → 2、Transactions/s 6,554 → 30,580 (Table 5、p.139) | 長い cursor の下で版数がほぼ一定 (Fig 10)、区間 GC が 118M 版を回収 (Fig 11、p.1315) | 版の列の最大長 100 未満 (§5.2.1)、移動時に 92% 超を剪定 (Fig 15) |

読んだ範囲で言えること:

- **最小形** (最古と 2 番目の境界の間を掃除する) の判定は、vDriver の Fig 6(c) と定義 3.4・定理 3.5 が述べている (最古と 2 番目に古い begin timestamp の間の dead zone に含まれる版を回収する)。
- **一般形** (実行中の全 timestamp で、どこからも見えない途中版を回収する) の判定は、Steam §4.3・HANA の定義 1・vDriver の定理 3.5 の 3 本がそれぞれ述べている。HANA と Steam は互いを interval 方式の先行として位置づけている (Steam Table 2、vDriver §2)。
- 3 本の違いは、契機 (Steam は更新時の即時、HANA は背景の周期、vDriver は版の移動時 + 背景)、単位、対象システム (Steam・HANA は主記憶、vDriver は disk-based) にある。
- **reader が辿っている途中版を物理的に解放しないための安全条件**は、読んだ範囲では 3 本とも独立に述べていない。Cicada に載せるときに固有に決める必要があった。本 wave は安全な再利用を実装しきれず、計測は「走行中は再利用しない」変種で行った (§3.4)。
- ユーザー案が既知であることは、この wave の価値を消さない: (a) VHash 論文の比較相手として「区間 GC を入れた Cicada」は審査で必ず問われる、(b) 区間 GC が長い tx の GC 問題をどこまで解くかで、VHash の GC 側の主張 (U0) の残りの価値が決まる (依頼 md_18)。

## 3. 設計 (正本は job dir `s4-ruling.md` の S1〜S10 と補正 1〜6)

### 3.1 切替と既定

| macro (全て 0/1) | 意味 | 既定 |
|---|---|---|
| `CICADA_INTERVAL_GC` | 区間 GC の機構 (最小形) | 0 = stock と同じ前処理結果 (4 target の全 owner TU で pin と一致) |
| `CICADA_INTERVAL_GC_GENERAL` | 一般形 (companion `CICADA_INTERVAL_GC=1`) | 0 |
| `CICADA_INTERVAL_COUNT` | 診断計数 (stock でも数える、perf build には渡さない) | 0 |
| `CICADA_INTERVAL_LONGTX` | 長い tx 負荷 (`ycsb_cicada.cc`) | 0 |

条件 gate (`condition_meaning_gate`) は「要求値 1 / 既定値 0」の真偽 macro と、owner TU 内の完全一致の `#if MACRO` 行しか観測できない (F139)。そのため分岐は全て単独の `#if` 行にした。
登録 site 数は GC 27・GC_GENERAL 1・COUNT 13・LONGTX 2 である (補正 2、B2)。対象は YCSB の point read / update だけで、scan・insert・delete の経路に入ったら異常終了する。

### 3.2 保護点と閾値

leader (thid 0) が `gc_inter_us` ごとに、GC flag の全員待ちとは独立に保護点を集める。集めるのは各 thread の wts と wts−1、各 rts、MinWts−1、MinRts である。
閾値は H = (T<<8)−1 とする (T は採取時の rdtscp)。begin の途中の thread が 1 本でもあれば、その回は採取を見送る。以後に始まる tx の timestamp が
{snapshot の点} ∪ [H, ∞) に入ることの論拠は S2 (単一 socket の同期 TSC を仮定)。

### 3.3 剪定の条件 (書き込み時、Steam §4.3 と同じ契機)

writePhase の後、書いた tuple の `gc_lock_` を try-lock で取って剪定する。版 v を外す条件は次の全部である (S3)。

- (a) v は committed。
- (b) どの保護点も v の可視区間 [wts(v), wts(次の committed 版)) に入らない。
- (c) wts(次) ≤ H。
- (d′) 各保護点 p について「wts ≤ p の最初の鎖上の節点」の直上ではない (補正 3)。
- (e) v は MinRts の可視版より新しい。

最小形は最初の隙間だけを、一般形は全ての隙間を剪定する。

### 3.4 物理再利用 — 未解決 (補正 3〜6 の経緯)

| 段 | 変更 | 実測 |
|---|---|---|
| S5 (当初) | 外した版を stock の pop (wts < MinRts) で再利用 | 一般形 SIGSEGV (smoke3) |
| 補正 3 | 条件 (d) を (d′) へ (blind write の足場が外れる反例) | なお mode 0 で落ちる |
| 補正 4 | 退役列 + epoch (外した時点で走っていた全 tx の終了まで待つ)。**当初の S5 は親の裁定の誤りで、段 2 plan と段 3 相談の推奨が正しかった** | smoke6 の二分: mode 0 だけ落ち、mode 1・2・3 は正常 |
| 補正 5 | blind write の install を tuple lock の下で latest から探し直す (lock を使わない削除と挿入の競合を閉じる) | mode 0 の計数診断と一般形がなお SIGSEGV |
| A13 | epoch の clear 順序 (R2) と、stock の末尾切離しが凍った next を辿る経路 (R4) を直す | smoke9 / 9b: mode 0 は SIGSEGV・停止、mode 1 は全て正常 |
| 補正 6 | **計測する変種は mode 1 (外すが走行中は再利用しない)** を既定にし、mode 0 は「安全でないことが実測で分かっている実験用」と明記 | smoke10 以降の全走行が完走 |

`--cicada_igc_debug_mode` は 0 = 再利用 (安全でない)、1 = 外すが再利用しない (既定)、2 = 外さない、3 = 剪定を呼ばない。
**帰結:** 外した版の bytes は走行中に返らない。安全な解放の条件 (外した時点で走っていた全 tx の終了) は、長い tx の間は満たされない。
したがって正しく実装できても、bytes は長い tx の終了まで返らない (Steam も解放を所有 tx の解放まで遅らせる)。
測った throughput には、mode の分岐と、mode 0 用の退役列の走査 (全 thread の開始 epoch の読み) の費用も含まれる (レビュー B-02)。

## 4. 負荷

`patches/cicada-interval-gc-longtx.patch` (`CICADA_INTERVAL_LONGTX`、`ycsb_cicada.cc` だけ) は、leader を除く末尾 L 本 (既定 1) の thread に長い tx を回させる。
型は wait_after_reads (10 read + 1 write の後に W µs 待って commit)、many_ops (1,000 操作・read 90%)、ronly_wait (10 read の後に W µs 待つ read-only tx) の 3 つ。
md_6 の `CICADA_LONGTX` (T-2904 のビルド不具合) とは独立に作ったので、「読み取り後に待つ型」は欠測にならなかった。長い tx の試行・commit・abort・滞在時間は終了時に 1 行 JSON で出す。

## 5. 正しさ (md_3 の検査器、TRACE=1 build、上限 indeterminate)

cell は md_3 の K / W / R と、長い tx の wait_after_reads・ronly_wait (各 thread 4・8)。3 腕 + 壊し patch (`patches/broken-cicada-interval-gc-overprune.patch`、条件 (b) から最小点 p1 を除く) を走らせた。
集計は `data/aggregate.json` の `verification` (status `normal_arms_passed_s8_positive_unmet`)。

| 腕 | 結果 |
|---|---|
| stock・最小形・一般形 (30 走行) | 全て巡回 0・integrity 数値項目 0・C 行 = commit 数・verdict indeterminate・read-WTS 不一致 0。失格 0 |
| 壊し: ronly_wait (事前登録の正例 cell) t4 / t8 | **発火 0 / 0 → S8 正例は不成立** (試作が read-only 長 tx の下で剪定しないため。§6.4) |
| 壊し: K t4 / t8 | 巡回 15 / 16、発火 21,015 / 21,095 — 補助の検出 (長い tx の無い cell で末尾 worker を長い tx の代役にした事前登録外の帰属) |
| 壊し: R t4 / t8 | 巡回 1,405 / 8,523、発火 8,298 / 35,666 — 同上 |
| 壊し: wait_after_reads t4 / t8 | 巡回 4 / 3、発火 1,592 / 1,902、帰属 0 — 補助の検出 (事前登録の帰属規則は「長い read-only tx を含む辺」で、この cell の長い tx は更新型) |
| 壊し: W t4 / t8 | 発火 22,966 / 24,728、巡回 0 (未検出) |

読み方: 壊し patch が発火した 8 走行のうち 6 走行で巡回が出ている。正常腕は同じ cell で巡回 0 なので、検査器は「見える版まで外す」誤りを捉えうる。
ただし事前登録した cell と帰属規則では示せていない。段 6 の敵対レビュー (R1・B-01) が、K・R だけで `passed` としていた集計を指摘した。
原因は、親が B1-11 の指示で S8 を「どこか 1 cell で検出すれば成立」と言い換えたことである。集計は S8 の literal に戻した (`s6-ruling.md`)。

## 6. 計測 (未検証の診断値)

### 6.1 条件と実行

48 thread (長い thread 1 本 + online 46 + leader)、N = 100 万、zipf 0.9、10 操作、GC 間隔 {10, 100} µs。
workload は rr50 / rr95 × 長い tx {wait1 (1 ms)、wait10 (10 ms)、many (1,000 操作)、ronly (10 ms)} と、長い thread 2 本の wait10 (rr50・GC 10) の計 17 cell。
各 cell で perf は 3 腕 × 3 rep × 3 s を同じ node・同じ job で順序を回転させ、count は各腕 1 rep × 3 s を走らせた。build は 1 回 (`bundle1/`) で、実行は 40 part の並列 job に分けた。
40 part の実行は 11:45:14〜11:51:15 JST (6 分 01 秒)・17 host で、driver の実時間は合計 1,259 s。親は part ごとの host が 1 つであること、(腕, build 種別) ごとの binary sha256 が 1 つであることを raw 244 記録で確かめた。

### 6.2 全 cell の表 (perf は 3 rep の中央値、他は count build の終了時)

| cell | stock tps (中央値) | min/stock | gen/stock | install lock 待ち min / gen | 外した版数 min / gen | 鎖上 MB s / m / g | 外したが未返却 MB m / g | perf RSS MB s / m / g | online read-only hop 総数 s / m / g |
|---|---|---|---|---|---|---|---|---|---|
| rr50-many-gc10 | 3.51M | 0.279 | 0.257 | 61% / 40% | 1,087,652 / 1,100,720 | 192 / 193 / 192 | 209 / 211 | 1207 / 1542 / 1527 | 911,354 / 164,444 / 92,515 |
| rr50-many-gc100 | 3.43M | 0.284 | 0.228 | 48% / 32% | 942,822 / 875,537 | 193 / 193 / 193 | 181 / 168 | 1224 / 1457 / 1412 | 1,147,743 / 130,110 / 76,259 |
| rr50-ronly-gc10 | 0.68M | 0.062 | 0.062 | 46% / 46% | 0 / 0 | 2174 / 314 / 314 | 0 / 0 | 6033 / 1282 / 1279 | 219,428,960 / 1,587,384 / 1,529,288 |
| rr50-ronly-gc100 | 0.68M | 0.062 | 0.062 | 47% / 46% | 0 / 0 | 2217 / 312 / 312 | 0 / 0 | 6030 / 1281 / 1278 | 222,525,725 / 1,434,406 / 1,981,060 |
| rr50-wait1-gc10 | 3.32M | 0.220 | 0.085 | 45% / 46% | 1,818,749 / 590,482 | 197 / 193 / 195 | 349 / 113 | 1188 / 1794 / 1297 | 2,155,034 / 245,075 / 43,877 |
| rr50-wait1-gc100 | 3.39M | 0.214 | 0.087 | 45% / 44% | 1,747,961 / 600,848 | 196 / 193 / 193 | 336 / 115 | 1202 / 1769 / 1303 | 2,015,542 / 249,519 / 44,471 |
| rr50-wait10-gc10 | 2.79M | 0.104 | 0.028 | 46% / 51% | 1,055,407 / 227,750 | 234 / 196 / 197 | 203 / 44 | 1393 / 1497 / 1126 | 11,508,480 / 268,725 / 30,666 |
| rr50-wait10-gc100 | 2.73M | 0.113 | 0.027 | 47% / 52% | 1,169,406 / 282,299 | 215 / 195 / 203 | 225 / 54 | 1397 / 1504 / 1103 | 11,933,347 / 293,930 / 34,558 |
| rr50-wait10-two-gc10 | 2.69M | 0.083 | 0.025 | 46% / 53% | 802,992 / 202,401 | 229 / 195 / 206 | 154 / 39 | 1448 / 1410 / 1137 | 17,806,897 / 216,939 / 26,849 |
| rr95-many-gc10 | 10.69M | 0.656 | 0.660 | 8% / 10% | 135,792 / 175,268 | 192 / 192 / 192 | 26 / 34 | 1094 / 1114 / 1142 | 334,321,684 / 220,499,894 / 158,989,077 |
| rr95-many-gc100 | 10.83M | 0.589 | 0.534 | 17% / 22% | 123,437 / 194,527 | 192 / 192 / 192 | 24 / 37 | 1098 / 1123 / 1169 | 410,093,688 / 253,147,211 / 218,481,135 |
| rr95-ronly-gc10 | 0.39M | 0.686 | 0.684 | 10% / 10% | 0 / 0 | 305 / 271 / 271 | 0 / 0 | 1114 / 1065 / 1063 | 4,243,047,290 / 3,620,083,134 / 3,635,568,534 |
| rr95-ronly-gc100 | 0.39M | 0.692 | 0.684 | 10% / 9% | 0 / 0 | 306 / 271 / 272 | 0 / 0 | 1113 / 1064 / 1062 | 4,237,542,590 / 3,620,984,503 / 3,650,822,401 |
| rr95-wait1-gc10 | 9.94M | 0.515 | 0.278 | 31% / 46% | 1,221,140 / 571,479 | 193 / 193 / 193 | 234 / 110 | 1089 / 1518 / 1290 | 908,425,846 / 802,541,727 / 288,212,084 |
| rr95-wait1-gc100 | 9.97M | 0.510 | 0.288 | 30% / 45% | 1,114,764 / 575,375 | 193 / 193 / 193 | 214 / 110 | 1088 / 1479 / 1274 | 879,479,214 / 801,231,137 / 307,701,242 |
| rr95-wait10-gc10 | 6.32M | 0.257 | 0.134 | 63% / 72% | 577,223 / 222,566 | 201 / 196 / 200 | 111 / 43 | 1102 / 1296 / 1147 | 2,967,589,175 / 927,032,238 / 206,410,414 |
| rr95-wait10-gc100 | 6.32M | 0.293 | 0.121 | 61% / 69% | 663,629 / 217,350 | 198 / 193 / 195 | 127 / 42 | 1104 / 1331 / 1130 | 3,010,934,433 / 1,094,200,877 / 187,959,877 |

定義 (単位 C の生成器 `make_figures.py` と要約 `data/summary.json` の `conversions` が正本):

- 鎖上 MB は、鎖に残る版数 × sizeof(Version) (+ body)。キー 100 万件の各 1 版で約 192 MB になる。
- 外したが未返却 MB は、mode 1 で鎖から外し、走行中に返していない版の bytes。
- lock 待ちは rdtscp 合計 / clocks_per_us / 10^6 / (走行秒 × thread 数) で求めた。
- 3 rep の小差は優劣未確定として扱う。

図 (`figures/`、PNG・PDF・provenance JSON):

- (a) `interval-gc-a-throughput`: throughput と stock 比。ronly に `*` 印を付けた。
- (b) `interval-gc-b-retention`: 版の保持。鎖上と未返却を分け、install 1 版あたりに正規化した panel も付けた。
- (c) `interval-gc-c-hops`: site 別の hop 総数。1 読みあたりは分母の欠測で算出不能。
- (d) `interval-gc-d-gc-cost`: lock 待ちと剪定の試行・成功・失敗。

### 6.3 読み方 — 何が言えて何が言えないか

- **更新型の長い tx では、stock の鎖がそもそも長くない。** wait1・many の stock の鎖上は 192〜197 MB で、キーあたり 1 版の基準 (約 192 MB) とほぼ同じだった。
  wait10 でも 215〜234 MB にとどまる。長い tx が 1〜10 ms ごとに終わるので、stock の境界公開がその合間に進む (stock の count で 3 s あたり wait10 296〜299 回、wait1 2,946〜3,004 回、many 9,323〜34,756 回)。
  区間 GC はここで 12 万〜182 万版を鎖から外したが、mode 1 なので bytes は返らない。更新型の cell の perf RSS は、最小形が stock より −38〜+606 MB (wait10-two だけ減り、他は 20〜606 MB 増) だった。
- **throughput の低下は install 経路の費用が支配する。** 剪定 0 の ronly 4 cell で、最小形・一般形とも lock 待ち 9〜47%・stock 比 0.06 (rr50) / 0.69 (rr95) だった。
  これは補正 5 (tuple lock の下で latest から探し直す) の費用で、区間 GC 一般の費用ではない (レビュー R4)。一般形は隙間を全部見るぶん、wait 型でさらに遅い (0.025〜0.29)。
- **鎖・hop の腕間差は交絡している。** 区間 GC の腕の install 数は stock の 1/1.3〜1/34 である (要約の `retention.installed`)。hop は鎖の長さ (= 長い tx の開始以後の書き込み量) で決まる。
  剪定 0 の rr50-ronly でも online read-only の hop は 219M → 1.6M (1/138) になった。したがって wait・many の cell の hop 減少 (rr50 で 1/5〜1/660) のうち、どれだけが剪定によるかは、このデータでは切り分けられない。
- **一般形の「追加の候補」は測れていない。** 一般形の外した版数が最小形より少ない cell が多いのは、一般形の書き込み量が更に少ないためで、同一履歴上の比較ではない (レビュー B-03)。
  smoke で使った `beyond_minimum_candidate` は腕間の観測差であり、同一履歴上の候補数ではない。

### 6.4 長い read-only tx — 試作が無作動だった型

ronly 4 cell では、全腕で境界 (MinRts) の公開が 0 回、剪定が 0 回だった。Cicada の read-only commit は `mainte()` を通らず GC flag を立てないので、
全 worker の flag を待つ leader が公開できない (`vhash-readonly-gc-publish` §0 と同じ機序)。試作は MinRts の可視版を足場にする条件 (e) を満たせず、剪定を見送った。
stock はこの型で、鎖上 2.17〜2.22 GB (キー 100 万件の 11 倍)・RSS 6.0 GB (rr50) に達した。区間 GC が原理上最も効くはずの場面を、この試作は扱えていない。

## 7. VHash との関係 — 実測と見積りを分ける

**実測 (この wave):**

- 更新型の長い tx (1〜10 ms) では、stock の鎖の伸びがそもそも小さく (基準 +0〜22%)、区間 GC で回収できる余地が小さかった。
- 長い read-only tx では stock の鎖と RSS が大きく伸びる (鎖 11 倍・RSS 6 GB) が、試作は何もしなかった。
- 長い tx 自身の読みの hop は、wait 型で小さい (長い thread の update site の hop は 3 s で 0〜4,515)。長い tx は待つ前に読むからである。
  many_ops の長い tx は 3 s あたり試行 1.7 万〜29 万回に対し commit 0〜1 回 (rr95-many-gc10 の最小形・一般形だけ 1 回) で、区間 GC の有無でほぼ変わらなかった。
- 古い tx が 2 本 (wait10-two) の cell は、最小形の外した版数が 1 本のとき (105 万) より少なく (80 万)、一般形は stock 比 0.025 だった。1 cell の観測である。

**他 wave の実測 (出典):**

- `vhash-gc-connection-prototype` §4.2〜4.5: U0 の前進 (構成 E) は、skew 0・10 ms で境界の遅れ −54%・保持時間 −47%・論理生存版数 −14.7 万。skew 0.9 では前進の成功が試行の 0.05〜0.27% で、効果はほぼ消える。throughput は stock 比 0.96〜1.06。
- `vhash-readonly-gc-publish`: read-only commit でも GC flag を立てる `cicada-ro-gcflag-variant.patch` (`IZANAGI_CICADA_RO_GCFLAG`、既定 0) で、公開は 289〜299 回 / 3 s に戻る。
  ただし公開後も境界年齢は 12.5〜14.3 ms で、長い read-only tx の rts が境界を押さえる。
- `vhash-forwarding-prototype` §5.1: forwarding の成功時、read の見える版の位置は平均 6.7 → 2.5 に縮んだ。throughput の差は検出できていない。
  `vhash-cicada-version-measure` §0 によれば、深い探索の大半は read-only (固定 snapshot、forwarding の対象外) である。

**見積り・論証 (測っていない):**

1. **bytes と再利用は、区間 GC では長い tx の終了まで返らない。** 安全な解放は「外した時点で走っていた全 tx の終了」を待つ必要があり (§3.4)、長い tx 自身がその条件を塞ぐ。
   鎖を短くして hop を減らすのが区間 GC、境界を動かして stock GC の再利用を早めるのが U0、という分担になる。U0 の「GC につなぐ」主張は、区間 GC の上でも bytes の側で残る。
   ただし U0 の前進は zipf 0.9 でほぼ成功しない (上記) ので、この条件表の上で U0 が稼げる量は小さい見込みである。
2. **長い read-only tx の場面では、区間 GC と ro-gcflag を重ねるのが先である。** ro-gcflag で MinRts が公開されれば、条件 (e) の足場ができ、長い read-only tx の点と online の点の間の隙間を剪定できる。
   stock の 2.2 GB の鎖がどこまで縮むかは未測定。
3. **forwarding と区間 GC は狙う site が違う。** 区間 GC は、固定 snapshot の read-only reader が辿る途中版を減らす。forwarding は update read の timestamp を前進させる。
   重ねる余地は「長い update tx の読み」だが、wait 型では長い tx が待つ前に読むので、この site の hop はもともと小さかった (上記の実測)。many_ops 型は長い tx 自体がほぼ commit できない (区間 GC でも同じ) ので、forwarding の既読不一致の問題 (md_6) が先に効く。
4. **論文での位置づけ (提案):** 「区間 GC を入れた Cicada」は比較相手として必要である。ただしこの試作 (tuple lock の install、再利用なし) は、Steam・HANA の実装費用を代表しない。
   比較には、install の費用を切り分けた対照 (§9) を先に取る。

## 8. 限界

- 性能値は未検証の診断値で、3 rep の小差は優劣未確定。perf と正しさ検査は別 build (規律 1)。
- 安全な物理再利用は未実装 (mode 0 は落ちる)。計測は mode 1 で、外した版の bytes は走行中に返らない。
- install を tuple lock の下で行う (補正 5)。throughput の比較は、この install 費用と剪定の効果の和である。
- 長い read-only tx の型では、試作は剪定 0 (境界の公開 0)。
- 鎖・hop の腕間差は書き込み量の差と交絡し、剪定の効果として読めない。1 読みあたりの hop は、読み回数の計数が無く算出不能。
- 事前登録した壊し patch の正例 (ronly_wait) は不成立。検出の証拠は事前登録外の補助 6 件である。
- 保護点の論拠は単一 socket の同期 TSC を仮定する (S2)。
- 鎖上の版数は走行終了時の 1 標本である (時系列ではない)。

## 9. 次の一手

1. **剪定の効果と install 費用の切り分け:** 同じ build で `--cicada_igc_debug_mode=3` (剪定しない、install 経路は同じ) の腕を足し、stock・mode 3・最小形・一般形を同時刻に測る。driver に腕を 1 つ足すだけで、build は流用できる。
2. **長い read-only tx:** `cicada-ro-gcflag-variant.patch` と区間 GC を重ね、ronly cell で境界の公開と剪定が起きるかを確かめる。S8 の事前登録正例 (ronly_wait) もここで初めて発火しうる。
3. **install の lock を外す:** 剪定と挿入の競合を lock 無しで閉じる設計 (外した節点の印を CAS の前に付ける等) を段 2 から検討し、補正 5 の費用を除く。
4. **安全な再利用:** mode 0 の破損の根本原因は未特定。退役列の論拠 (補正 4) を小さなモデルで検査してから実装する。

## 10. 再現・計算量・出所

- patch: `patches/cicada-interval-gc-variant.patch`、`patches/cicada-interval-gc-longtx.patch`、`patches/broken-cicada-interval-gc-overprune.patch` (節は `patches/README.md`)。
- driver: `python3 -m orchestrator.campaign.vhash_interval_gc {smoke,build,plan-jobs,run-part,verify-part,aggregate}`。test は `orchestrator/tests/test_vhash_interval_gc.py` (自走 38 件)。
- 集計: `aggregate --raw <parts3 の 40 part の raw.jsonl> --output <repo 外>` → `data/aggregate.json` (sha256 `c03cf03dc1cb4eaaa2466f4c5df1e5cc67f60bbb3ae785a76f3f2d4e3bc11803`)。
- 図と要約: `make_figures.py --aggregate data/aggregate.json --raw <40 part> --output-prefix figures/... --summary data/summary.json`。生成器は raw から集計を再計算し、`data/aggregate.json` と一致しなければ止まる。
- 計算量 (計算ノード): smoke 群 5,712 s、build 1 回 178 s、本計測 40 part の driver 実時間 1,259 s (約 2 node 時間)。本計測は 40 job に分け、6 分 01 秒で完了した。
