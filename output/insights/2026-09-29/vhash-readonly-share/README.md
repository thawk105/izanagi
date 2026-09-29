# VHash md_15: read-only tx は深い版探索と GC の遅れの主因か (2026-09-29)

VHash 論文 (`docs/paper-story-vhash/` 2026-09-29 版の H1・U0、出典メモ §17) の伸びしろがどこにあるかを決めるための診断計測。
md_2 (`output/insights/2026-09-29/vhash-cicada-version-measure/`) の計器 patch を拡張し、read-only (ro) tx の比率を独立の軸にして、
Pegasus 計算ノードで 86 条件 × 3 反復を測った。**計器入り build の値であり、throughput は性能値ではない。正しさ (serializability) の主張はしない。**

## 0. 結論 (図から)

![ro の深い探索](figures/depth_share.png)

1. **深い版探索の大半は ro tx から来る。** ro 指定率 25% 以上の全条件 (既定 Cicada・skew 0・調整済み Cicada) で、最新版より奥 (位置 ≥ 1) へ行った read の
   87〜100% が ro の read だった。位置 ≥ 4 の read が観測された条件では、その 99.4〜100% が ro だった (位置 ≥ 4 の read が 0 件の S95-none-gc10 は除く、§5.1)。
   ro read のうち位置 ≥ 1 へ行く割合は、既定 Cicada (skew 0.9、ro 指定率 25〜95%) で gc_inter_us = 10 µs なら 25〜30%、100 ms なら 44〜56%、
   長い ro tx があると 59〜76%。版を tuple 内に置く最適化 (INLINE_VERSION_OPT=1) を入れた調整済み Cicada の測った格子 (skew 0.9) でも 18〜55% だった (図 1 下段)。
   skew 0 (長い tx なし) では gc 10 µs で 0.1〜1% と小さく、gc 100 ms で 9〜40%。update tx の read が位置 ≥ 1 へ行くのは全 R/S/T 条件で 0.00003〜5.8% (最大は調整済み・ro 0%)。
   → **H1 (hot 配置) の伸びしろは ro の read にあり、その大きさは競合 (skew) と snapshot の古さで決まる。**
2. **ただし回収境界の遅れの主因は、競合の強い設定では短い ro tx ではない。** 既定 Cicada・skew 0.9 では、ro 指定率を 0% → 95% に変えても
   境界年齢の平均は 1.5〜1.9 ms (gc 10 µs)、2.3〜2.7 ms (gc 1 ms)、122 ms (gc 100 ms) のまま動かない (ro の総差 −0.3〜+0.2 ms、符号も揃わない、§6.1)。
   これに対し 10 ms の長い update tx は、ro 0% のとき境界年齢を +14〜24 ms (既定)、+6〜21 ms (skew 0)、+3〜13 ms (調整済み) 押し上げた。
   **md_2 §0.6 の読み (ro の多い B で境界年齢 p50 が 2 ms) との関係:** 今回の読み比 50%・ro 0% の対照では、skew を 0 → 0.9 に変えるだけで p50 が 32 µs → 2,048 µs の bucket に動いた。
   md_2 の A/B は skew・読み比・ro 比率を同時に変えた比較で、その差のうち ro の寄与がどれだけかは本計測では特定していないが、「ro が主因」とする根拠にはならない (§6.1)。
3. **長い ro tx が 1 本あると、観測した 3 秒間 MinRts の公開が止まった。** 10 ms 待つ ro tx を 1 worker が続ける条件 (wait10msR) では、ro 比率・gc 間隔によらず
   45 走すべてで 3 秒間に MinRts の公開が 0 回、ro snapshot の年齢は 1.5〜1.9 s (走行の大半) になった。Cicada の実装では ro commit が GC flag を上げない (`mainte()` を通らない) ので、
   その worker の flag が立たず、全 worker の flag を待つ leader は公開できない、という経路と整合する (§6.3)。
4. **ro commit が flag を上げないことに伴う公開の待ち (見積り b、観測走の時刻分割による機会量) は、更新 tx が速い設定で大きい。** 公開間隔のうち「最後の flag 上げを
   ro commit ならもっと早くできた分」の割合は、既定 Cicada・skew 0.9 で 0.2〜8.7%、skew 0 で 21〜76%、調整済み Cicada で 12〜77% (いずれも gc 10 µs、
   ro 50〜95%)。skew 0・調整済みでは ro 95% で境界年齢の平均も 2〜2.5 倍になった (375 → 792 µs、201 → 512 µs)。gc 100 ms では 1% 未満 (§6.2)。
   これは介入後の公開の短縮量ではない。
5. **見積り (a): 観測鎖・先頭 K 版・既読区間に限定した楽観的適格率。** 位置 ≥ 1 の ro read のうち、先頭 1 版に「既読と矛盾しない確定版」があったのは
   既定 Cicada で 31〜40% (gc 10 µs〜1 ms)、18〜24% (gc 100 ms)、長い ro tx で 11〜18%、調整済み Cicada で 19〜50%。
   固定 snapshot が要る ro の割合 f を仮定すると、避けうる深い探索の割合の目安は (1 − f) × この率 × (深い read に占める ro) (独立を仮定した感度曲線上の値で、上限ではない、§7)。

**この図から読み取ってはならないこと。** 値は計器入り build・48 worker・1M 件・3 秒の YCSB の観測で、Cicada や VHash の性能は言っていない。
D-F の差は条件間の総差で「ro のせい」の因果的な内訳ではない。見積り (a)(b) は機会量で、実装したときの効果・上限ではない。

## 1. 何を確かめ、何を確かめていないか

**確かめたこと (実測):**
- 計器 patch の既定 build (両 macro 未定義) は stock と正規化 `objdump -d`・`.rodata` が一致し、`nm` に izanagi 記号が無い (smoke1、§4)。
- 86 条件 × 3 反復 = 258 走がすべて rc=0 で、計器行 (schema 2) を driver の fail-closed 検査で parse できた。
- 1M 件は D15 第二基準 (maxrss ≥ 4 × L3) を満たす (smoke1: 1,087,144 KB ≥ 4 × 105 MiB)。
- 計器の D-C 記録の除外 (世代不一致 `dc_generation`・欠損 `dc_missing`・時刻逆転 `dc_negative`) は各走で公開間隔の 3.5% 以下 (最大 1/29、S95-none-gc100000)、`dc_epoch_mismatch` は全 258 走で 0 (§9)。
- md_2 と同じ flag の anchor 2 条件は md_2 の値とほぼ一致 (§4、計器増分の目安)。
- 本計測 4 job は別々のノードで走った (bnode051・bnode148・bnode037・bnode074)。md_14 と同じノードを使った自分の job は 3 本 (md_14 側の job との組は 4 組) で、いずれも時刻は重ならない (順番使用):
  m1 (35818.nqsv、bnode148、18:30:46〜18:35:27) の直前に md_14 の 35808.nqsv (18:23:36〜18:30:29)、smoke1 (35800.nqsv、bnode011、18:24:19〜18:26:05) の直後に md_14 の 35810.nqsv (18:26:22〜)、
  smoke0 (35602.nqsv、bnode035、17:25:27〜17:27:13) と md_14 の 35597・35811.nqsv (16:57〜16:58、18:29〜18:36)。照合は `verbatim/node-overlap.txt` (dispatch log の開始・終了時刻と receipt の hostname)。
  md_11 の計測は 15:2x に着地済みで時間が重ならない。
  各走は driver の競合ベンチ検査 (自ノードの ccbench プロセス) を通過した。

**確かめていないこと:**
- **正しさ:** Cicada は 2026-09-29 時点で izanagi の正しさ検査器を通せない。計器と種別制御は既定 inert だが、有効 build での serializability は確かめていない。
- **forwarding の実現可能性・費用:** 見積り (a) は観測時点の鎖の上で 1 read ずつ独立に判定した楽観値。後から入る writer、pending 版の後日確定、
  read set の検証 (stock の ro は検証しない)、連続した前進、timestamp の一意性、前進した ro が GC 境界に与える影響を含まない。
- **ro commit に flag を上げさせた場合の実際の公開・境界:** 見積り (b) は観測走の時刻の分割で、介入後の実行 (早い公開 → 新しい snapshot → 版の生成・abort の変化) を再現しない。
- **性能:** 計器入り build の throughput は性能値に使わない (絶対規律 1)。update commit/s・install/s は各セルの状態の記述にだけ使う。
- **他の workload・thread 数・長時間走:** YCSB (10 ops、update tx の op は読み 50%)、48 worker・1 ソケット・1M 件・3 秒だけ。
- **固定 snapshot が要る ro の実際の割合 f:** YCSB の ro は区別しない。

## 2. 定義 (結果を見る前に固定、段 4 裁定と段 6 の裁定)

### 2.1 read-only tx の 2 種類 (出典メモ §17.1〜§17.2)

| 種類 | 意味 | 本資料での扱い |
|---|---|---|
| 固定 snapshot 必須の ro | 指定時点・同じ snapshot の読み取りを要求する (例: 分析 query、snapshot ID の共有) | 読む時点を動かしてはいけない。見積り (a) の対象外 |
| serializable でよい ro | 実行全体を直列順序のどこかに置ければよい | 読む時点を前へ動かす余地がある。ただし stock Cicada の ro は read set を記録・検証しないので、前へ動かすには read set の検証など未実装の費用がかかる |
| 区別不能の割合 f | YCSB の ro はどちらかを区別しない | 見積り (a) を f の関数 (感度曲線) で示す |

Cicada の ro は `begin()` で `rts_ = MinWts − 1` を読み (transaction.cc 42)、commit で read set を検証しない (934〜937)。
この snapshot は「すでに確定し、後から版が差し込まれない境界」の直下なので安定している。前へ動かすと安定境界の外に出る。

### 2.2 回収境界の遅れ

- 境界年齢: MinRts の公開ごとの (公開を検出した時刻 − MinRts の時刻部)。µs。厳密和 ÷ 公開回数を平均、2 倍刻みヒストグラムの p50 を別に示す。
- ro snapshot 年齢: ro tx の `begin()` での (現在時刻 − rts_ の時刻部)。境界年齢とは元の配列が違い (MinWts 由来 / MinRts 由来)、同じ条件でも乖離しうる別の量。

### 2.3 分解 D-F (条件間の総差と交互作用)

gc_inter_us と workload を揃えた条件の平均境界年齢 Lag(r, L) (r = ro 指定率、L = 長い tx の型) について:
- ro の総差 (r) = Lag(r, none) − Lag(0, none)
- 長い update の総差 (L) = Lag(0, L) − Lag(0, none)
- 交互作用 = Lag(r, L) − Lag(r, none) − Lag(0, L) + Lag(0, none)

**これは「ro のせい」の因果的な内訳ではない。** ro 指定率を上げると update tx の数・版の生成量・abort 数も変わる。各セルに実現 ro 試行率・commit 率、update commit/s、install/s、abort 率を併記する。不確かさは非対応の条件平均差として計算する (反復同士を対にしない)。

### 2.4 分解 D-C (観測走における flag 機会の時刻分割)

各公開 k について、前回公開 t_{k−1}、公開検出 t_k、各 thread i の実際の GC flag 上げ時刻 raise_i と、「ro commit も mainte と同じ timer 条件で flag を上げたとしたら」の最初の時刻 cf_i (実際に上げた方が早ければその時刻) を記録し、

t_k − t_{k−1} = [max cf − t_{k−1}] + [max raise − max cf] + [t_k − max raise]

の 3 項に分ける。第 2 項 (Δ_ro) を「ro commit が flag を上げないことに伴う待ち」、第 1 項を max cf の thread がそのとき commit・abort した tx の種別 (通常 update・長い update・abort・ro・長い ro) で分け、第 3 項は「最後の flag 上げから公開検出まで」。
**これは観測走の中の時刻の分割であって、ro commit に flag を上げさせたときの公開時刻や MinRts の前進量ではない** (早く公開すれば後続の timer・snapshot・版の生成が変わる)。除外 (初回公開・世代不一致・欠損・時刻逆転) は条件ごとに件数を出す。

### 2.5 境界保持 tx の種別

公開ごとに、公開された MinRts と同じ rts を持つ thread (公開直前に採取) の現在の tx 種別を 1/n ずつ数える (n = 一致した thread 数)。一致なしは unresolved として別に数える。

### 2.6 見積り (a): 観測鎖・先頭 K 版・既読区間に限定した楽観的適格率

ro read のうち位置 ≥ K (観測した鎖で最新から K 番目以降の版を選んだ) ものの中で、その鎖の先頭 K 版内に確定済みの版 v があって
max(wts(v), L, rts + 1) < min(e(v), U) を満たすものの割合 (md_2 の update 側と同じ式)。L = 同じ tx の既読版 wts の最大、U = 既読版それぞれの「読んだ時点で直上にあった確定版の wts」の最小、e(v) = v の直上の確定版の wts。
外した制約: 後から入る writer、pending 版の後日確定、read set の検証、連続した前進、一意性。外した制約には候補を減らすものも増やすものもあるので、**一般の上限ではない**。
固定 snapshot 必須の割合 f に対し、避けられる深い探索の割合 ≒ (1 − f) × 適格率 は、固定の要否と適格性が独立という仮定の感度曲線である。

### 2.7 見積り (b): 公開間隔に対する局所的な機会量

Σ Δ_ro ÷ Σ 公開間隔 (有効な公開間隔だけ)。「ro commit も flag を上げていたら、観測した各公開間隔のうちどれだけが待ちでなかったか」の局所的な量で、境界の前進量・上下限ではない。

## 3. 条件表

| 軸 | 値 |
|---|---|
| 主格子 R (60) | 既定 genome (CMake 既定: BACK_OFF=1, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=1, REUSE_VERSION=1, WRITE_LATEST_ONLY=0)、skew 0.9、ro 指定率 r ∈ {0, 25, 50, 75, 95}% × 長い tx {none, wait1msU, wait10msU, wait10msR} × gc_inter_us {10, 1000, 100000} |
| skew 0 対照 S (12) | 既定 genome、skew 0、r ∈ {0, 50, 95} × {none, wait10msU} × gc {10, 100000} |
| 調整済み T (12) | md_11 の最良設定 (BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0)、skew 0.9、r ∈ {0, 50, 95} × {none, wait10msU} × gc {10, 100000} |
| anchor (2) | md_2 の B-none-gc10・B-wait10ms-gc10 と同じ flag (YCSB の生成のまま: 読み 95%、skew 0.9、ro は約 59%) |
| 共通 | YCSB 10 ops、update tx の op は読み 50% (`ycsb_rratio=50`、ro 以外の手続きは少なくとも 1 op を write にする)、payload 4 B、48 worker、N = 1,000,000、extime 3 s、clocks_per_us 2100、各 3 反復 |
| 長い tx | worker 1 が `commit()` 冒頭で 1 ms / 10 ms 待つ (md_2 と同じ)。U = その worker の手続きを update に固定、R = read-only に固定 |
| ro 指定率 | 新しい手続きの初回 `begin()` で確率 r% で全 op を READ に (`izanagi_ronly_pct`)。retry では変えない。実現した試行率は §5 の表 |

job の割り方: gc 間隔ごとにまとめ、D-F の比較が同じノード内で完結するようにした (m0 = R・gc 10、m1 = R・gc 1000、m2 = R・gc 100000、m3 = S + T + anchor)。

## 4. smoke と anchor

- smoke1 (35800.nqsv、patch sha256 `fafdd862…`、commit 1ec90f6d3): 既定 build の inert witness (正規化 objdump・rodata 一致、nm・strings)、1M の maxrss、4 build (stock・既定・計器・調整済み計器)、
  短い走 2 本 (既定・調整済み) の schema 2 parse、所要見積り 1,308 node 秒。
- smoke0 (35602.nqsv、fix3 前の patch) の短い走では、D-C の公開間隔の 60% (既定) と 84% (調整済み) が「世代不一致」で除外されていた。
  段 6 の fix3・fix4 (§9) 後の smoke1 では 1.0〜1.7% に下がった。smoke0 の値は結果に使っていない。
- anchor と md_2 の比較 (計器増分の目安。同時刻の対照ではない):

| 条件 | 指標 | md_2 | 本計測 |
|---|---|---|---|
| B-none-gc10 | ro read の位置 ≥ 1 / ≥ 8 | 0.24 / 0.10 | 0.238 / 0.0995 |
| B-none-gc10 | 公開回数 / s | 1,320 (3,960 / 3 s) | 1,340 |
| B-none-gc10 | 境界年齢 p50 bucket | 2,048 µs | 2,048 µs |
| B-wait10ms-gc10 | 公開回数 / s | 83 (248 / 3 s) | 83.9 |

## 5. 結果: 深い探索

![境界年齢・公開・snapshot 年齢](figures/boundary_age.png)

全 86 条件の 3 反復平均は `analysis/summary.md`、反復ごとの値と最小・最大は `analysis/summary.json` (生成 script は `verbatim/summarize-source.md`、repo 外で実行)。

### 5.1 ro read の深さと、深い read に占める ro (抜粋、3 反復平均)

| 条件 | 実現 ro 試行率 | ro read の位置 ≥ 1 / ≥ 4 / ≥ 8 | 深い read に占める ro (≥ 1 / ≥ 4 / ≥ 8) | update read の位置 ≥ 1 |
|---|---|---|---|---|
| R50-none-gc10 | 0.47 | 0.296 / 0.184 / 0.143 | 0.958 / 1.000 / 1.000 | 0.023 |
| R95-none-gc10 | 0.95 | 0.245 / 0.141 / 0.104 | 0.999 / 1.000 / 1.000 | 0.012 |
| R50-none-gc100000 | 0.48 | 0.534 / 0.380 / 0.323 | 0.985 / 1.000 / 1.000 | 0.015 |
| R50-wait10msU-gc10 | 0.47 | 0.471 / 0.328 / 0.275 | 0.978 / 1.000 / 1.000 | 0.019 |
| R50-wait10msR-gc10 | 0.49 | 0.710 / 0.528 / 0.460 | 0.997 / 1.000 / 1.000 | 0.005 |
| S50-none-gc10 | 0.50 | 0.010 / 4e-7 / 0 | 1.000 / 1.000 / — | 6e-6 |
| S50-none-gc100000 | 0.50 | 0.398 / 0.007 / 4e-6 | 1.000 / 1.000 / 1.000 | 5e-6 |
| T50-none-gc10 | 0.41 | 0.280 / 0.179 / 0.139 | 0.922 / 0.994 / 0.999 | 0.033 |
| T50-none-gc100000 | 0.47 | 0.549 / 0.397 / 0.339 | 0.991 / 1.000 / 1.000 | 0.009 |

- ro 指定率 25% 以上の全条件で、深い read に占める ro は位置 ≥ 1 で 0.874 (R25-none-gc10) 〜 1.000。位置 ≥ 4 の read が観測された条件では 0.994 (T50-none-gc10) 〜 1.000 (S95-none-gc10 は位置 ≥ 4 の read が 0 件で割合は未定義)。
- ro の深さは snapshot が古い条件ほど大きい (R、ro 指定率 25〜95%、位置 ≥ 1): gc 10 µs で 0.25〜0.30、長い update tx (gc 10 µs) で 0.39〜0.48、gc 100 ms で 0.44〜0.56、長い ro tx で 0.59〜0.76。ro 比率を上げると ro の深さはやや下がる (update tx が減り版の生成が遅くなる)。
- skew 0 (長い tx なし) では gc 10 µs の ro の深さが 0.1〜1% と小さく、gc 100 ms では 9〜40% (位置 ≥ 1)。位置 ≥ 4 は skew 0 の全条件で 0.8% 未満 (最大 S50-wait10msU-gc100000 の 0.0078)。
- 調整済み Cicada (T) の ro の深さは同じ条件の既定 (R) とほぼ同じか少し小さい (図 1 下段)。T を測ったのは skew 0.9 の 12 条件だけ。INLINE_VERSION_OPT=1 では版の 1 つが tuple 内にあるが、ここでの「位置」は鎖上の位置で、cache 上の近さではない。

## 6. 結果: 回収境界の遅れと、その分解

### 6.1 D-F: 条件間の総差と交互作用 (定義 §2.3)

![分解](figures/decompositions.png)

| 系列・gc | 基準 Lag(0, none) | ro の総差 (r = 25 / 50 / 75 / 95) | 長い update (10 ms) の総差 | 交互作用の範囲 (10 ms、r = 25〜95) |
|---|---|---|---|---|
| R・10 µs | 1.67 ms | +0.06 / +0.21 / +0.16 / −0.16 ms | +24.2 ms | −2.0〜−0.5 ms |
| R・1 ms | 2.51 ms | +0.08 / +0.11 / +0.14 / −0.25 ms | +23.1 ms | −2.2〜−0.4 ms |
| R・100 ms | 122.2 ms | −0.31 / −0.20 / −0.27 / −0.31 ms | +14.1 ms | −3.6〜−1.5 ms |
| S・10 µs | 0.375 ms | r = 50: −0.15、r = 95: +0.42 ms | +21.2 ms | −7.3〜−0.8 ms |
| T・10 µs | 0.201 ms | r = 50: +0.06、r = 95: +0.31 ms | +13.0 ms | −1.2〜−1.0 ms |

(値は 3 反復平均どうしの差。反復間の不確かさは図 3 の誤差棒 = 非対応の条件平均差の 95% t 区間。)

- 既定 Cicada・skew 0.9 では、ro の総差は ±0.3 ms の範囲で符号も揃わず、図 3 の誤差棒の内側。**この設定では短い ro tx は境界年齢を系統的に動かしていない。**
- 更新 tx が速い設定 (S・T、gc 10 µs) では、ro 95% で境界年齢が +0.3〜+0.4 ms (基準の 2〜2.5 倍)。p50 bucket も 32 µs → 1,024 µs (S)、32 → 512 µs (T)。
- 長い update tx の総差 (+13〜24 ms) は ro の総差より 2 桁大きい。交互作用は負 (ro があると長い tx の上乗せがやや小さい) だが、誤差棒が大きい。
- skew の差: ro 0% どうしで R (skew 0.9) 1.67 ms / p50 2,048 µs、S (skew 0) 0.375 ms / p50 32 µs。md_2 §0.6 の A と B の差 (32 µs と 2,048 µs) は skew・読み比・ro 比率を同時に変えた比較だった。今回の読み比 50%・ro 0% の対照では skew を変えるだけで同じ bucket 差が生じ、skew 0.9 では ro 比率を 0〜95% に動かしても p50 は 2,048〜4,096 µs の bucket から動かなかった。md_2 の差のうち ro の寄与は特定していないが、md_2 の比較は「ro が主因」の根拠にはならない。

### 6.2 D-C: 観測走における flag 機会の時刻分割 (定義 §2.4)、見積り (b)

| 条件 (gc 10 µs) | 公開間隔 平均 | 最後の flag 機会まで (第 1 項) | ro が flag を上げない分 Δ_ro | 最後の flag 上げ→公開検出 | (b) = ΣΔ_ro / Σ間隔 | 第 1 項の種別 (時間の割合) |
|---|---|---|---|---|---|---|
| R0-none | 762 µs | 570 | 0 | 192 | 0 | 通常 update 0.75、abort 0.25 |
| R50-none | 833 µs | 631 | 1.9 | 201 | 0.0023 | 通常 update 0.77、abort 0.23 |
| R95-none | 714 µs | 579 | 62 | 74 | 0.087 | 通常 update 0.83、abort 0.16、ro 0.01 |
| S50-none | 141 µs | 98 | 30 | 14 | 0.21 | 通常 update 0.96 |
| S95-none | 591 µs | 130 | 452 | 10 | 0.76 | 通常 update 0.96、ro 0.03 |
| T50-none | 168 µs | 139 | 21 | 9 | 0.12 | 通常 update 0.38、abort 0.61 |
| T95-none | 399 µs | 86 | 310 | 4 | 0.77 | 通常 update 0.46、abort 0.50 |
| R0-wait10msU | 10.5 ms | 10.25 ms | 0 | 0.28 ms | 0 | abort 0.91、長い update 0.08 |

- 既定 Cicada・skew 0.9 (R) の公開間隔は、ほぼ「timer 満了後に最後の worker が update tx を commit / abort するまで」の待ち (第 1 項) で決まる。ro の分 (b) は r = 95% でも 8.7%。
- 更新 tx が速い S・T では第 1 項が小さく、ro 95% のとき公開間隔の 76〜77% が「ro commit が flag を上げないための待ち」だった。
- gc 100 ms では公開間隔 ≈ 100 ms の timer がほぼすべてで、(b) は 1% 未満。
- 長い update tx (10 ms) では公開間隔 ≈ 10.5 ms で、第 1 項の終わりは主に abort (長い tx 自身の abort を含む。種別 abort は長短を区別しない)。
- **(b) は観測走の時刻の分割で、ro commit に flag を上げさせたときの境界の前進量ではない** (定義 §2.4、§2.7)。

### 6.3 長い ro tx の条件では、観測した 3 秒間に公開が 0 回

- wait10msR の 45 走 (15 条件 × 3) すべてで MinRts の公開は 0 回。ro snapshot の年齢の平均は 1.54〜1.87 s、ro read の位置 ≥ 1 は 59〜89%。
- 境界保持 tx の種別 (定義 §2.5) は公開が無いので記録されない。
- 同じ 10 ms の待機でも update に固定した wait10msU は 1 秒あたり約 95 回公開した (長い tx 1 本ごとに 1 回)。2 つの条件で違うのは長い worker の tx 種別で、Cicada の実装上その違いは「commit で `mainte()` を通り flag を上げるか」に現れる (ro tx の rts は update tx と同じく begin 時の MinWts − 1)。公開 0 回はこの経路と整合するが、flag だけを変えた介入走はしておらず、他の違い (read set・commit 経路) の寄与は切り分けていない。

### 6.4 境界保持 tx の種別

公開された MinRts と同じ rts を持っていた tx の種別 (1/n ずつ) は、ro 比率と gc 間隔に沿って ro に寄る: gc 10 µs の R では ro 25% で 0.03、95% で 0.61。gc 100 ms では ro 25% で 0.69、95% で 0.98。T の gc 100 ms では 0.96〜0.99。
「境界を保持していた」は rts が同じだったという意味で、その tx だけが公開を止めていたという意味ではない (全 tx の rts は begin 時の MinWts − 1 で、同じ値を持つ tx が多数ありうる)。

## 7. 見積り (a): 観測鎖・先頭 K 版・既読区間に限定した楽観的適格率 (定義 §2.6)

![見積り](figures/opportunities.png)

| 条件群 | 位置 ≥ 1 の ro read のうち適格 (K = 1) | K = 8 |
|---|---|---|
| R・gc 10 µs (none) | 0.33〜0.40 | 0.38〜0.46 |
| R・gc 1 ms (none) | 0.31〜0.38 | — |
| R・gc 100 ms (none) | 0.18〜0.24 | 0.19〜0.25 |
| R・長い ro tx (wait10msR) | 0.11〜0.18 | 0.12〜0.18 |
| T・gc 10 µs (none) | 0.33〜0.50 | 0.37〜0.55 |
| S・gc 10 µs (none) | 0.93〜0.99 (深い ro read 自体が少ない) | — |

- 古い snapshot ほど適格率は下がる (既読区間の上端 U が狭く、先頭の版がその外に出やすい)。
- 固定 snapshot の要否の割合 f との関係: 避けうる深い探索の割合 ≒ (1 − f) × 適格率 × (ro が深い read に占める割合 ≈ 0.9〜1.0)。
  例: 既定 Cicada・gc 10 µs (ro 指定率 25〜95%) で f = 0.5 なら 0.14〜0.20 程度 (R25 0.145、R50 0.159、R75 0.167、R95 0.200)。**独立を仮定した感度曲線で、上限でも実装の成功率でもない** (外した制約の一覧は §1)。

## 8. 生出力の所在

- raw (gzip、本 dir `raw/`): `measure-m0.json.gz` (R・gc 10 µs)、`measure-m1.json.gz` (R・gc 1 ms)、`measure-m2.json.gz` (R・gc 100 ms)、`measure-m3.json.gz` (S・T・anchor)、`smoke1.json.gz`。
  展開後と gzip の sha256 は `raw/SHA256SUMS`。展開後の JSON は各走の argv・stdout・計器行・parse 済み JSON を持つ。
- 計算ノード job: smoke1 35800.nqsv (bnode011、Elapse 110 s)、本計測 35820 (m0、bnode051)・35818 (m1、bnode148)・35819 (m2、bnode037)・35821 (m3、bnode074)、
  Elapse 288・285・287・377 s。checkout は detached worktree `vhash-ros-{s0,m0..m3}` @ 1ec90f6d3。
- 予備の smoke0 (35602.nqsv、fix3 前の patch) は結果に使っていない。repo 外 `/work/1/SFC/tanab/tmp/vhash-readonly-share-2026-09-29/raw/` に置いた (永続を保証しない)。
- 計算ノードの使用: smoke 2 本 (Elapse 各 110 s 前後)、本計測 4 本 (合計 1,237 s)、焦点走と変異 (§10)。合計は §10 に書く。

## 9. 限界

- **観測者効果:** 計器は read ごとの計数、tx ごとの rdtscp、公開ごとの全 worker の slot 採取を行う。anchor は md_2 と 2% 以内で一致したが、md_2 も計器入りで、stock との差は測っていない。
- **D-C の除外:** 各走で公開間隔の最大 3.5% (公開の少ない条件で 1 件)。原因は主に遅延公開 (leader の採取時に flag が揃っておらず、cicadaLeaderWork の中で揃って公開) の直後の短い隙間で、その事象は次の公開で「世代不一致」として除外され件数に出る。遅延公開では公開検出の時刻に数十 ns の計器処理が入る (µs の量に対して無視できる)。
- **D-F は総差:** ro 比率を上げると update tx 数・版の生成量・abort 率が同時に変わる (表 `analysis/summary.md` の update commit/s・abort 率)。「ro のせい」の因果的な内訳ではない。
- **(b) は介入の模擬ではない:** ro commit に flag を上げさせれば timer・snapshot・版の生成・abort が変わる。
- **(a) は一般の上限ではない:** 外した制約には候補を減らすもの (後から入る writer、検証) も増やすもの (観測後に生成される版) もある。
- **種別 abort は長短を区別しない。** 長い update tx の abort も「abort」に入る。
- **分位点は 2 倍刻みの bucket 上界**、時間は timestamp 空間 (clock boost を含む)。
- **YCSB だけ**、48 worker、1M 件、3 秒、各 3 反復。長い tx は worker 1 の全 tx が長い型 (md_2 と同じ)。

## 10. 実装と検証の記録

- patch `patches/instr-cicada-version-lifetime.patch` (md_2 の計器を拡張、既存 2 macro の下だけ)、driver `orchestrator/campaign/vhash_cicada_vlife.py` (条件 108 = 旧 24 + 新 84、schema 1/2)、
  test `orchestrator/tests/test_vhash_cicada_vlife.py`、作図 `tools/plotting/plot_vhash_readonly_share.py` (新規)、condition gate の VLIFE 件数 pin (33 → 37)。
  Codex `role=author` の実装子 1 本と fix 子 6 本 (fix1〜fix6)。
- 段 2 plan 1 本、段 3 相談 1 本 (条件付き GO)、段 6 レビュー 2 本 (2 本とも NO-GO → fix1)、焦点再レビュー 2 本 (NO-GO → fix3・fix4、2 巡目の残りは親が裁定で打ち切り)、
  実データの図を見た親の所見で fix5、変異 1 回目の生存 2 件で fix6。裁定と所見は `verbatim/`。
- 変異 (本 dir `mutation/`、事前登録は `verbatim/s4-ruling.md`・`s6-fix1〜5-ruling.md`、erratum は `verbatim/s6-mutation-ruling.md`):
  - 本走 1 回目 (35859.nqsv): spec の等価変異の category を harness の語彙外で書いた親の誤りで、変異前に rc=2。変異 0 件。
  - 本走 2 回目 (35877.nqsv、commit 1ec90f6d3、`spec-run2.json`・`ledger-run2.json`): baseline 28 passed、registered 19、matching 16。
    MUT-2・MUT-12 が生存 (fixture が別の検査でも拒否される過剰決定) → fix6 で単一理由の fixture を足した。MUT-16 は殺せたが MUT-18 の test も赤 (期待 node の登録漏れ) → erratum。
  - 本走 3 回目 (35911.nqsv、Elapse 653 s、最終 commit ec896c10a、`spec-run3.json`・`ledger-run3.json`): registered 20 = recorded 20、matching 19 (KILLED 18、EQ-1 SURVIVED)。
    MUT-4 は殺せたが fix5 で足した MUT-19 の test も赤 (期待 node の登録漏れ) → erratum で期待集合を直し、MUT-4 だけを再走 (35930.nqsv、`spec-run4-mut4.json`・`ledger-run4-mut4.json`): matching 1/1。
  - **最終: 20 変異すべて登録どおり** (本走 3 回目の 19 件 + MUT-4 の再走)。wrapper の rc=125 は走行中に別 wave が local main へ land し共有木の観測値が変わったためで (`ledger-run3.wrapper-receipt.json` の `shared_snapshot_matches=false`)、変異は固定 commit の使い捨て worktree で取れている。
  - 殺す test の多くは patch の文字列・構造を見る検査で、C++ の実行時挙動 (公開の世代・flag を上げない ro 経路) は計算ノードの smoke と計測で確かめた範囲に限る。
  - login の自走 probe は harness 内の worktree 作成が Lustre の EINTR で失敗したので行わず、本走 2 回目を初回の dispatch probe として扱った。
- 計算ノードの使用 (各 job の Elapse): smoke 2 本 110 s + 110 s、本計測 4 本 288 + 285 + 287 + 377 s、焦点走 4 本 (35493・35531・35680・35913) 21 + 193 + 236 + 218 s、
  変異 4 本 123 + 615 + 653 + 132 s。合計 3,648 s (約 1.0 node 時間、2 node 時間未満)。
- md_15 の指示との食い違い: 「`patches/ledger.json` の entry」は作らなかった。同台帳は D18 第 4 類 ability probe 専用で entry 数 1 を要求する (md_2 §9 と同じ理由)。`patches/README.md` の既存 entry を更新した。

## 11. 次の版 (paper-story-vhash 2 版目) へ

- **H1 (hot 配置):** 伸びしろは ro の read にある。update read が最新版より奥へ行くのは全条件で 0.00003〜5.8%。ro read の位置 ≥ 1 は既定 Cicada (skew 0.9、ro 25〜95%) で 25〜76%、
  調整済み Cicada の測った格子で 18〜55%、skew 0 では 0.1〜40% と競合と snapshot の古さで大きく変わる。
- **U0 (GC 接続):** 「短い ro tx が回収を遅らせる」は設定次第。競合の強い既定 Cicada では主因でなく (観測走の時刻分割で公開待ちの 9% 以下)、更新 tx が速い設定で ro が多いと 3/4 を占める。
  **最も強い事例は長い ro tx で、1 本で観測した 3 秒間 MinRts の公開を止めた。** Cicada の実装では ro commit が GC flag を上げないことと整合する。
  論文では、固定 snapshot の意味を保ったまま変えうる部分 (ro commit でも flag を上げる、など) と、snapshot を前へ動かさないと変わらない部分 (長い ro の rts が境界を押さえる) を分けて論じる必要がある。
  前者の変更が GC の安全性を保つか・どれだけ効くかは本計測では確かめていない (介入走なし、次の一手)。
- md_2 §0.6 の「ro の多い B で境界が遅い」という読みは、本計測の対照では skew の差で同じ bucket 差が出るので、ro の寄与の根拠としては使えない (§6.1)。
