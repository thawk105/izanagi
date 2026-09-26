# Izanagi 本体論文：結果・考察草稿 (2026-09-26 版)

本稿は 2026-09-26 の執筆依頼 (論文ストーリー 2026-09-26 版を入力に日本語草稿 5 節へ反映する) に基づく日本語草稿である。
前稿 (2026-09-21b 版、`output/insights/2026-09-21/paper-results-ja-b/results-discussion.md`、worklog entry 1801) を置き換える (supersede)。
前稿は 1 byte も変えずに残す。前稿の骨格 (12 節) と節番号はそのまま継承し、前稿の採用時点 (`d99c556df`) より後に main へ着地した結果のうち
結果・考察に属するものを、論文ストーリー 2026-09-26 版 (`docs/paper-story/2026-09-26.md`) の状態まで足した — K2 の同 job pair と 4 巡目 (§8.1、表 11 の 4 巡化と表 11b)、
verifier の検出期待表と容量の実測 (§6.3 と表 8c を新設)、TPC-C 段 1 の trace の判定 (§6.4 を新設)、関数単位の軸 `silo-function-policy` の段階 C・D と既知最良との小比較
(§7 の末尾と表 10b)、B-5 本走の中断と判定不能・探索の独立反復の試走の中断・ccbench pin の C への前進・MOCC の差し込み・転移の実行器・図の描き直し (§10〜§12)。
§1〜§5・§6.1・§6.2・§9 の数値と判定は前稿から変えていない (いずれも前稿の採用時点までに取得され、その後に動いた記録は無い)。

資料の採用時点は local main `6d198ca8a` (2026-09-26 17:17 JST。worklog entry 1867 までの fold を含む)。稼働中の wave の成果は数えない。
**数値は結果稿の表・insight・provenance の逐語であり、丸めは各資料の表示桁に従う。** 各節の「言えること / 言えないこと」は、その資料の限定と
論文ストーリー 2026-09-26 版 §6・§7・§8 に揃えた。前稿から継承した文の時点表記 (「本稿の採用時点」) は、継承部分では前稿の照合時点 `d99c556df` を指す
場合があり、その箇所は括弧で明示した。
**個々の実験の留保は本稿が持ち、論文全体の限界 (対象の空白、LLM の因果的必要性、保証範囲の一般論) は序論・限界稿が持つ。** 本文中の資料番号は末尾の出所を指す。

書き方の規律 (各稿と共通): `observed-positive` / `reject` / `accepted` / `not-observed` / `different` / `resolved-above-floor` は
protocol または consumer の出力であって研究の成否のラベルではない (D12)。性能の判定と別走行の正しさの証拠は別の段で書き、
性能の `reject` は正しさ証拠の欠落ではなく、正しさの `certified` は性能の認証ではない (D1993 項 2)。旧い判定は取り消さず (規律 7)、
別 protocol の走行をプールしない (D1993 項 6)。

## 1. 有限フラグ空間では LLM 誘導の優越を示さなかった

まず、既存の設定を選ぶ操作に LLM を用いる価値を調べた。P2-5 では、Silo の 8 構成からなる有限フラグ空間を対象に、
LLM 誘導と、LLM を使わない貪欲探索を比較した。評価には既存の測定値を再生する方式を用いており、ここでの試行数は
新しい性能測定の反復数ではない。指標は最良群に到達するまでの評価回数で、少ないほどよい。未到達は予算上限の 8 回として数えた。
誘導側には評価済み構成の指標だけを提示し、最適解の明示的な事前知識を除いた専用 critic を用いた。
この実験はコード生成の比較ではない。[1]

**表 1　既存 8 構成の探索コスト。** 平均は評価回数。A は同数を半分に数えた「誘導のコストが貪欲より小さい」確率優越で、
0.5 が同水準に当たる。

| 負荷 | 誘導の試行数 | 誘導の平均 | 貪欲の平均 (500 試行) | 誘導の未到達 | A | 読み取れる結果 |
|---|---:|---:|---:|---:|---:|---|
| balanced | 12 | 3.750 | 4.234 | 0/12 | 0.5813 | 有意差を示さない (p≈0.16) |
| write-heavy | 12 | 6.333 | 4.362 | 8/12 | 0.2304 | 誘導側のコストが高い (片側 exact permutation p=0.0002521) |
| read-heavy | 6 | 1.667 | 1.756 | 0/6 | — | 最良群が 8 構成中 4 構成を占め、識別力のある比較として扱わない |

write-heavy の判定は、2 負荷 × 3 比較の Holm 補正後も維持された。記録された未到達 8 試行は、最良群へ到達しないまま停止した
試行である。したがって、少なくともこの有限空間では、指標を言語的に解釈することが貪欲探索を超える探索効率をもたらしたとは
いえない。balanced で有意差が出なかったことは、両者の等価性を証明するものではない。また、この結果から LLM によるコード生成
一般が無益だとは推論できない。[1]

**言えること / 言えないこと。** 言えるのは「評価器の自信ある早期停止は、deceptive な信号の下では負債になる」という、
事前に立てた仮説を独立に反証した結果である (write-heavy の誤収束 8/12)。これは第 2 幕の実証であり、本稿の他の節の結果によって
動いていない。言えないのは、この負の結果を LLM 一般や、後述する操作を拡張する合成 (§2 以降) へ一般化することである。[1, 12]

## 2. 静的 backoff の追加は旧環境の sweep で 2 負荷を改善し 1 負荷で退行した

既存フラグの選択とは別に、abort 後の待機量を静的に指定する操作を Silo へ追加した。これは既存フラグ空間の外へ操作の集合を
広げた事例である。追加後の数値探索は機械的な sweep で行った。P2-4 の旧環境の測定では、write-heavy と balanced の静的候補は
無 backoff 対照を上回り、read-heavy では測った静的候補の最良点でも退行した。この 3 値は 2026-09-20 に一次資料 (3 campaign の
`campaign.lock`・WAL・材料レポート・fig2b の provenance) から単独稿へ再抽出された。[2]

**表 2　旧環境の静的 backoff sweep (記述的結果)。** 各側 5 反復のスループット中央値 (WAL `bench_done.payload.median_tps`) を用い、
利得は `100 × (静的候補の中央値 / 無 backoff 対照の中央値 − 1)` で計算した。分母は同じ sweep 内の `BACK_OFF=0, BACKOFF_FIXED=-1`
であり、CCBench 既定の適応 backoff ではない。

| 負荷 (read 比率) | sweep が選んだ静的点 | 無 backoff (tps) | 静的候補 (tps) | 未丸め値 | 論文値 |
|---|---:|---:|---:|---:|---:|
| write-heavy (5%) | 10 µs | 1,882,125 | 2,603,521 | 38.32880387859468% | +38.3% |
| balanced (50%) | 5 µs | 2,791,760 | 3,106,342 | 11.268232226265873% | +11.3% |
| read-heavy (95%) | 2 µs | 8,450,806 | 7,889,420 | −6.642987662951915% | −6.6% |

「sweep が選んだ静的点」は静的 6 点 (2 / 5 / 10 / 25 / 50 / 100 µs) のうち median が最大の点である。read-heavy は 6 点すべてが
対照を下回り、最大の fixed 2 µs でも対照に届かない。条件は旧 `linux-baremetal` 環境 (較正記録の `host.node` は cygnus)、
CCBench `6656e93`、gcc-13、48 threads、1,000,000 records、Zipf 0.9、RMW 無効、各実行 3 秒、`clocks_per_us` 1800 である。
性能は trace 無効の build (`-DCCBENCH_TRACE=0`) で取得し、24 走はすべて `perf stat` によるカウンタ集計の下にある。
別 CCBench revision・`BACKOFF_NOINLINE=1`・`perf record` 下・3 反復の機序診断 profile が与える +38.5% (未丸め 38.46157964649388%)
は、D20 の利用方針により headline に使わない (この 4 点が利得の大きさを変えたという実証も無い)。
測定日は write-heavy と balanced が 2026-06-22、read-heavy が 2026-06-28 で同一ではない。[2]

図 2b (`fig2b_backoff_sweep_3workload`) は同じ 3 campaign を描くが、図の点推定は標本平均であり、平均から同じ式で計算すると
+38.1% / +11.4% / −6.9% になる。論文値は median 比、図は標本平均で、両者は同じ生値の別の要約であって丸め違いではない。[2]

正しさは性能とは別の走行で検査され、WAL の `verify_done` は 24 件すべて `serializable` / `certified: true` / `anomalies: 0`
である。ただしこれは 2026 年 6 月の判定器による当時の判定であり (provenance の verifier epoch は `E0`、`v1-authority-absent`)、
verify の workload・argv・trace は WAL に無い。**論文の 3 値の正しさは今も「backoff は正しさに影響しない」という機序論証による
外挿であり、§3 の現行 certification はこの 3 値へ遡らない** (D1993 項 4)。[2]

**言えること / 言えないこと。** 言えるのは、同一 sweep 内の無 backoff 対照に対する記述的な median 比として、2 負荷で正、1 負荷で
負だった、までである (稿の限定 1: D496 以前の記述的結果で、A-1 が定める配置と推定対象の下で測り直したものではない。ただし
「同一 campaign 内の対測定が 1 件も無い」とは書かない — その形は §3 の 3 走行が満たす)。言えないのは、別 boot での再取得
(限定 2、D1100 / D1525 により A-5 は未充足のまま)、有意差や区間推定 (限定 10)、3 workload の採用点 (10 / 5 / 2 µs) を単一
treatment の一般効果として平均すること (限定 9)、adaptive を分母にした +147.4% を論文値として扱うこと (限定 7)、
そして現行環境の値 (§3〜§5) との前後比較・プール (限定 4、規律 7) である。[2]

## 3. 現行環境の 3 走行 — 正しい identity で測った採用静的 backoff

測定当時の現行環境 (Pegasus・CCBench pin `511c953`) で、採用静的 backoff を測った正式な走行が 3 つある。**3 つは独立した protocol であり、
1 つの横断実験ではない** (D1993 項 6)。それぞれ単独稿を持つ。[3, 4, 5]

### 3.1 A-2 (write-heavy / balanced) — `observed-positive`

2026-09-07 の A-2 attempt `t2364-20260907b` は、pin + patch に束縛した `src_token` で cell の identity を計算する driver で走り、
4 cell すべてが `source_binding_status=bound`、stock cell は `src_token=stock`、adopted cell は非 `stock` と記録されている。
write-heavy と balanced をそれぞれ独立の campaign (request `981476.nqsv` / `bnode077`、`981477.nqsv` / `bnode085`) として取得した。[3]

**表 3　A-2 attempt `t2364-20260907b` の 4 cell。** 各 cell は trace 無効の 5 反復。効果は median 比 (`effects`)。
abort 率は cell 単位の集約値であり、信頼区間や因果効果を表さない。

| 負荷 | cell | 構成 | median (tps) | mean (tps) | 95% CI 半幅 | 変動係数 | abort 率 | 効果 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| write-heavy (rr5) | `rr5-stock` | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 2,438,295 | 2,462,838.6 | 99,765.6 | 0.0326 | 0.7845 | 基準 |
| write-heavy (rr5) | `rr5-fixed10` | `BACK_OFF=1`, `BACKOFF_FIXED=10` | 3,987,794 | 4,004,505.0 | 45,583.8 | 0.0092 | 0.3833 | +63.5485% |
| balanced (rr50) | `rr50-stock` | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 3,756,230 | 3,808,422.0 | 138,475.2 | 0.0293 | 0.6850 | 基準 |
| balanced (rr50) | `rr50-fixed5` | `BACK_OFF=1`, `BACKOFF_FIXED=5` | 4,297,929 | 4,302,525.0 | 58,456.7 | 0.0109 | 0.4615 | +14.4213% |

outer status は 2 workload の論理積で `observed-positive` である。権威値は `effects.rr5 = 0.6354846316791036`、
`effects.rr50 = 0.14421348000521794`。平均の 95% CI は標本を記述するものであって、効果・判定・median の信頼区間ではなく、
成果物は有意性の判定を行わない (`a4_noise_floor_status = open`)。図は fig6。[3]

### 3.2 A-6 (read-heavy) — `reject`

2026-09-08 の A-6 attempt `a6-20260908b` (request `982234.nqsv`) は read-heavy の 2 cell を測った。protocol は workload が rr95 の
1 つなので、outer status はその 1 問の答えそのものである。[4]

**表 4　A-6 attempt `a6-20260908b` の 2 cell。** median と abort 率は権威 bytes と WAL の値。mean・変動係数・95% CI 半幅は
稿の執筆者が生の 5 標本から計算した派生値で、権威 bytes には無い (A-6 には図の provenance が無かったため)。

| cell | 構成 | median (tps) | mean (tps) | 変動係数 | 95% CI 半幅 (tps) | abort 率 | 効果 |
|---|---|---:|---:|---:|---:|---:|---:|
| `rr95-stock` | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 10,088,796 | 10,132,250.6 | 0.0132 | 165,646.2 | 0.1547 | 基準 |
| `rr95-fixed2` | `BACK_OFF=1`, `BACKOFF_FIXED=2` | 9,505,248 | 9,565,649.4 | 0.0117 | 139,341.9 | 0.145 | −5.7841% |

outer status は `reject` (権威値 `effects.rr95 = -0.057841193339621455`)。図は fig11 (2026-09-20 着地)。
B-10 read-heavy 正式系列の 3 block (同じ 2 genome、1 job 内 3 block × 5 標本) の block 別効果は −6.609% / −5.377% / −5.317% で
A-6 の値はこの帯に入るが、これは近接条件の別実行による履歴的照合であって独立再現ではない。反復 attempt は行わない ([T-2430])。
実行基盤の測定に付随して得た −4.876% は attempt に数えない (D1870)。[4]

### 3.3 [T-1998] (balanced) — 事前登録の下で `accepted`

balanced については、別の事前登録 (`docs/t1998-balanced-stock-inline-preregistration.md` v1) に基づく prospective な対比較が
2026-09-13 に 1 job (`995755.nqsv`、`bnode024`) で測られ、2026-09-14 に consumer が `accepted` と判定した。事前登録は結果を見る前に
2 点 (無 backoff 対 静的 5 µs) と判定規則 (median 比) を固定し、旧 headline の +11.3% を期待値として固定していない。[5]

**表 5　[T-1998] の登録 2 arm。** 5 標本は `bench_done.tps` の記載順。

| arm | 構成 | 5 標本 (tps) | median (tps) | 変動係数 | abort 率 |
|---|---|---|---:|---:|---:|
| baseline | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 4079966 / 3891020 / 3978513 / 3859794 / 3893509 | 3,893,509 | 0.0227 | 0.6795 |
| target | `BACK_OFF=1`, `BACKOFF_FIXED=5` | 4437166 / 4326276 / 4361949 / 4330570 / 4289164 | 4,330,570 | 0.0128 | 0.4613 |

consumer の出力は `status = accepted`、`ratio = 1.1122537536191646`、`improvement_percent = 11.225375361916456` である。
1 回目 (2026-09-13) の解析は consumer 側の 2 系統の述語 (測定側ではない) が拒否し、是正 (受理集合を広げる変更を 1 件含む) の後に同じ
保全成果物を通して `accepted` を得た。事前登録の bytes と判定規則は動いていない。着地後の main (2026-09-15) の consumer でも全桁再現した。図は無い。[5]

### 3.4 別走行の正しさ — 性能の判定ではない

正しさは trace 有効の別 build・別 run から来る (規律 1)。A-2 の 4 cell と A-6 の 2 cell は、`source_binding_status=bound` の下で
legacy 1 回 + performance 条件 5 回の検査がすべて `certified` である (A-6 の `verify_done` 12 件は `serializable` / `certified` /
anomaly 0)。[T-1998] の 2 arm は campaign WAL の `verify_done` で `serializable` / `certified` / anomaly 0 だが、`workload.tag`
は `legacy` (1 件ずつ) であり、A-2 / A-6 の「legacy 1 回 + performance 5 回」と同じ形式ではない (稿はこの違いを強さの比較としてで
なく形式の違いとして書く)。[3, 4, 5]

この certification には 5 つの限定が付く (D1993 項 3 の (i)〜(iv) と identity 層の (v))。(i) verifier の射程は YCSB の point read /
write に限った観測 trace 上の直列化可能性である (L01)。(ii) correctness 側の argv は既存 pipeline では独立に記録されておらず、
workload の束縛は campaign lock と pipeline constructor による (D1257)。(iii) 成果物自身が「source-routed evidence であって、
artifact hash 単独では compile-out の証明にならない」と宣言している。(iv) 条件関門について成果物が保存しているのは admission
record と `record_ids` までで、元の record の本体は残らない。(v) `src_token` の一致だけでは実翻訳単位全体の意味の一致を保証しない
([T-2630] が実測した `#define` / `#undef` の範囲は [T-2731] (D2108) が塞ぎ、指令と include の相対位置と `push_macro` / `pop_macro` が
限界として残る。A-2 / A-6 の attempt で変異が起きた証拠は無く、修正は判定を遡って強くしない)。[3, 4, 12]

### 3.5 旧 attempt の訂正 — 測っていたのは内蔵 backoff の有効/無効

旧 A-2 attempt `t2022-20260828c` (2026-08-28) は、静的量を要求しながら patch なしの stock 木を build していた。WAL の
`build_start` 4 record は `src_token = stock`、`tracked_clean = true`、`tracked_paths = []` を記録し、実際に効いた条件差は
CCBench 内蔵の適応 backoff の有効/無効 (`BACK_OFF` の 0/1) だけだった (D1645、F707)。その値 (rr5 2,527,542 → 1,355,011 で
−46.3902%、rr50 3,662,448 → 1,248,603 で −65.9080%、outer `reject`) は当時の事実として残るが、支持する命題は「内蔵 backoff の
有効/無効」であり、静的候補の失敗として用いない。内蔵機構はスループット勾配に応じて待機量を固定幅で増減する適応制御であり、
「指数 backoff」という呼び方も採用しない。新旧の status は異なる実条件に対する出力であり、「同じ構成の判定が `reject` から
成功へ反転した」とは書けない。条件記述を訂正した図は fig7 で、旧 fig5 は採用静的 backoff の結論・図としては期限なしで使わない
(D1936 項 21)。[6]

### 3.6 言えること / 言えないこと

- **言えること。** 正しい identity で測った採用静的 backoff は、A-2 protocol (write-heavy と balanced の連言) で `observed-positive`、
  A-6 protocol (read-heavy) で `reject`、[T-1998] の事前登録 (balanced) で `accepted` だった。3 走行の符号 (+ / + / −) は旧
  `linux-baremetal` の 3 値と 3 workload とも一致した。**これは記述的な照合であって、再現判定ではない。** D496 が求める「同じ
  campaign の中で比べる」形は 3 走行がいずれも満たしている。A-2 の 4 cell と A-6 の 2 cell は、性能条件に対応する別 build・別 run の検査
  (legacy 1 回 + performance 5 回) でも certified であり、採用静的 backoff は性能を測った workload そのもので certified と言える。[T-1998] の
  正しさ記録は legacy 条件で各 arm 1 回に限る (§3.4)。いずれも性能の認証ではない。
- **言えないこと。** 「採用した静的 backoff は現行環境でも効くことを再現した」— 環境も CCBench の版も測定契約も違い、A-2 も
  A-6 も 2 点 protocol で信頼区間を持たず、[T-1998] も点推定である。旧値と新値を pool しない。「A-2 の結果を read-heavy へ転移
  できる」「read-heavy で stock が最良である」— A-6 の `reject` は 1 attempt・5 標本の中央値比較であり、他の read 比率・機体・pin へ
  外挿しない。「関門を実施し通過したことを独立に確認した」— 成果物にあるのは受領証の記録までである。A-2 / A-6 の abort 率は
  代表 rep 1 点の記述的な先行指標で、機序の説明には使わない。[3, 4, 5, 12]

## 4. 同一候補 fixed 5 µs の 3 workload 同時期測定 — read-heavy だけが床値超の退行

§3 の 3 走行は workload ごとに採用値が違い (10 / 5 / 2 µs)、同一 variant の横断比較にならなかった。2026-09-19 の attempt
`b7f5-20260919a` (study `paper-story-b7-fixed5-regression`、request `10807` / `10808` / `10809`、各 5 node、source `c18a80967`) は、
A-2 / A-6 と同じ certification 経路を descriptive に使った別 study instance として、同一候補 fixed 5 µs ([T-1998] 事前登録の採用 arm と
同じ genome・同じ source bytes digest `678b7203…`) を 3 workload で同時期 (33 分 38 秒の窓、各 workload で stock の直後に adopted) に
測った。判定規則 (対差 < −床値 で退行、床値 = D1639 の between-run CV) は結果を見る前に固定した (D2162)。[7]

**表 6　attempt `b7f5-20260919a` の 3 workload の対差と床値判定 (退行込み、符号を問わず同じ表)。** `effect_w` は権威 bytes の
`effects` の全桁。

| 負荷 | stock median (tps) | fixed5 median (tps) | `effect_w` | 百分率 | −床値 | 判定 | abort 率 (stock → fixed5) |
|---|---:|---:|---|---:|---:|---|---|
| write-heavy (rr5) | 2,354,846 | 3,953,710 | `0.6789675418265144` | +67.8968% | −0.9536% | 退行なし | 0.7881 → 0.4997 |
| balanced (rr50) | 3,832,768 | 4,318,443 | `0.12671651401806727` | +12.6717% | −0.7250% | 退行なし | 0.681 → 0.4599 |
| read-heavy (rr95) | 10,334,945 | 9,158,963 | `-0.11378696258180376` | −11.3787% | −0.2228% | 退行 (床値超) | 0.1543 → 0.1345 |

機構の outer status は 3 workload の論理積で `reject` だが、これは read-heavy の対差が負であることの帰結であり、「3 workload とも退行」
ではない。`a4_noise_floor_status` は `open`。別の trace 有効走行では 6 cell とも `correctness.status = certified`・anomaly 0
(legacy 1 + performance 5、計 36 記録) で、**退行した `rr95-fixed5` も certified である**。「退行なし」の 2 行は優越の判定ではない。
図は fig10 (2026-09-20 着地)。[7]

既存材料 (§3、workload 別の採用値 10 / 5 / 2 µs) とは表を分けて併記し、プールしない。同じ workload の左右の値 (例: rr95 の −5.78% と
−11.38%) は採用値・attempt・日付・node が違うので、床値と比べる対差ではない。[7]

**B-7 (全 workload の退行込み報告) の扱い。** 稿 (D2162) 自身は「B-7 の要件充足は判定しない」と書き、論文ストーリー 2026-09-20 版も
「要件充足へは昇格させない (D2044 項 3)」と書いていた。その後のユーザー裁定 D2174 項 3 (2026-09-20) が、この稿と図 10 を根拠に、
B-7 を **単一 attempt・descriptive・非認証・反復間安定性は未判定** という限定付きで満たしたと扱い、D2044 項 3 をこの限定付き充足で
supersede した。反復 attempt は認可されず、certified 昇格・有意差判定・新規測定は含まない。「充足」は報告要件 (失敗条件 (e) の退行込み
全 workload 報告) についてであり、候補の採用・認証・性能主張ではない。稿と図 10 の本文は凍結のままである。[7, 8]

**言えること / 言えないこと。** 言えるのは、結果を見る前に固定した規則で、同一候補 fixed 5 µs が read-heavy でだけ床値超の退行を示し、
write-heavy と balanced では退行なしだった、までである。床値判定は記述的で (床は 1 arm の between-run CV であり 2 arm の比の分散では
ない)、有意差判定ではなく、「退行なし」は差が無いことの証明ではない。1 attempt・各 5 標本であり反復間の安定性へ一般化しない。
「同一候補」は source bytes・define・toolchain・pin までで、binary は workload ごとに別 build である。機序 (read-heavy で 5 µs が退行する
理由) は述べない。[7]

## 5. A-1 sized 本走 attempt-0001 と attempt-0002 — 非認証 lane の descriptive 出力 (2 attempt の並記、プールしない)

P2-4 の headline estimand と一致する対測定 (A-1、但し書き 1 に対応) は、事前登録・sizing 証明書 (3 workload とも n = 30)・本走 policy v3
(非認証 lane、`formal=false` / `promotion_prohibited=true`) の下で、2026-09-18 に attempt-0001 が 1 attempt 認可 (D2120 項 3) で投入され、
3 workload とも `valid=true` / `errors=[]` で完走した (job `4939` / `4940` / `4941`、bnode107〜109、各 30 対 × 2 arm、均衡 5-rep ブロック
交互配置)。[9]

**表 7　attempt-0001 の登録済み解析の出力 (`result.json` の `workloads[].statistics` から逐語、descriptive のみ)。** 対差平均は
variant − baseline。`h = k·s/√n` (k = 2.8315526875186725、df 29)、`B` は baseline 平均の 3%。

| 負荷 | contrast | 対差平均 (tps) | h (tps) | B (tps) | baseline 平均 (tps) | 分類 | `variance_plan_breach` |
|---|---|---:|---:|---:|---:|---|---|
| write-heavy | `fixed10` − `no-backoff` | +1,591,948.5 | 23,911.50 | 68,795.22 | 2,293,173.97 | `resolved-above-floor` | false |
| balanced | `fixed5` − `no-backoff` | +448,830.17 | 28,351.60 | 115,876.90 | 3,862,563.20 | `resolved-above-floor` | false |
| read-heavy | `fixed2` − `no-backoff` | −576,749.77 | 32,963.70 | 310,204.40 | 10,340,146.73 | `resolved-above-floor` | false |

分類は 3 workload とも「区間 (平均 ± h) が床 ±B の外」を言うだけで向きを持たず、向きは平均の符号で読む。3 行は並記であって集計ではない。
別の trace 有効走行では 6 arm とも `verify_done` が `certified=true` / `anomalies=0` / `verdict=serializable` (`legacy` 条件 1 件ずつ)。
図は fig9。[9]

attempt-0002 は、2026-09-19 に独立再現として 1 attempt 認可された後、既存 submit 経路の gate (`_assert_no_prior_v3_bench_start`、
規律 2 由来) に qsub の前で拒否され (D2156)、投入経路がユーザー裁定 D2172 項 2 (択 1 = exact な認可 record を gate の入力に取る、
1 attempt 限定) で決まり、その実装 (D2178) が main に着地した (entry 1736) のち、**2026-09-20 18:11 JST に認可 record 経由で 1 回投入され
(job `13220` / `13221` / `13222`、bnode035 / 039 / 040)、3 workload とも `valid=true` / `errors=[]` で完走した** (entry 1755)。研究目的は
「同一配置 (同 seed・同物理順) の反復」であり、attempt-0001 の失敗後の再走ではない。schedule receipt の `root_seed` / `effective_root_seed` /
`seed_counter` / `group_bits` / `blocks[].arm` は attempt-0001 と 3 workload とも一致し、束縛 9 file のうち driver 1 本だけが認可 record の
生成・照合と submit / materialize への接続の 143 行で異なる (推定量・分類・測定経路の関数に変更行が無いことは静的確認のみ)。登録済み解析の
出力は 3 workload とも `resolved-above-floor` で、対差平均 (variant − baseline) は write-heavy +1,538,451.47 tps、balanced +548,138.23 tps、
read-heavy −560,565.60 tps。write-heavy と read-heavy では 30 対の差の標本標準偏差が事前登録の計画 sigma を超え (`variance_plan_breach = true`、
標本 sd 80,148.44 > 計画 sigma 66,403.45、80,752.99 > 74,668.49)、balanced では超えていない (49,427.36 < 56,697.44)。分類は
`abs(mean) − h > B` で決まり、超過した workload でも `resolved-above-floor` のままである。超過の原因 (node・時刻帯・bench 相の順序・
baseline arm の変動) は稿も本稿も帰属しない。別の trace 有効走行では 6 arm とも `verify_done` が `certified=true` / `anomalies=0` /
`verdict=serializable` (`legacy` 条件 1 件ずつ)。attempt-0002 の図は本稿の採用時点で無く、fig9 は attempt-0001 の図である。[26]

**表 7b　2 attempt の登録済み解析の出力の並記 (attempt-0002 稿 §2.7 から逐語。値は各公開 leaf の `result.json` の
`workloads[].statistics`、全桁)。** 2 行は独立した 2 つの観測であり、本稿は 2 行から何も計算しない。

| workload | attempt | 投入 (JST) | source commit | node | mean (variant − baseline) tps | h tps | descriptive interval tps | B tps | baseline mean tps | sample sd / planned sigma | classification | variance_plan_breach |
|---|---|---|---|---|---:|---:|---|---:|---:|---|---|---|
| write-heavy | attempt-0001 | 2026-09-18 06:30 | `d2ebef7a4` | bnode107 | `1591948.5` | `23911.502943472762` | `[1568036.9970565273, 1615860.0029434727]` | `68795.219` | `2293173.966666667` | `46253.31396347129` / `66403.45210801972` | `resolved-above-floor` | `false` |
| write-heavy | attempt-0002 | 2026-09-20 18:11 | `fec4a8187` | bnode035 | `1538451.4666666666` | `41434.211082207854` | `[1497017.2555844588, 1579885.6777488743]` | `72952.12299999999` | `2431737.433333333` | `80148.43644687126` / `66403.45210801972` | `resolved-above-floor` | `true` |
| balanced | attempt-0001 | 2026-09-18 06:30 | `d2ebef7a4` | bnode108 | `448830.1666666667` | `28351.599461068836` | `[420478.5672055979, 477181.7661277355]` | `115876.89600000001` | `3862563.2` | `54842.032905228465` / `56697.43571357468` | `resolved-above-floor` | `false` |
| balanced | attempt-0002 | 2026-09-20 18:11 | `fec4a8187` | bnode039 | `548138.2333333333` | `25552.384438113106` | `[522585.8488952202, 573690.6177714464]` | `110832.746` | `3694424.8666666667` | `49427.359824489315` / `56697.43571357468` | `resolved-above-floor` | `false` |
| read-heavy | attempt-0001 | 2026-09-18 06:30 | `d2ebef7a4` | bnode109 | `-576749.7666666667` | `32963.69867738655` | `[-609713.4653440532, -543786.0679892802]` | `310204.40199999994` | `10340146.733333332` | `63763.46597396226` / `74668.48956627495` | `resolved-above-floor` | `false` |
| read-heavy | attempt-0002 | 2026-09-20 18:11 | `fec4a8187` | bnode040 | `-560565.6` | `41746.744315864176` | `[-602312.3443158641, -518818.8556841358]` | `305064.861` | `10168828.7` | `80752.98639149407` / `74668.48956627495` | `resolved-above-floor` | `true` |

並記から書けるのは次の事実命題までである — (a) 登録済み解析の分類は 2 attempt × 3 workload の 6 cell すべてが `resolved-above-floor`、
(b) 対差平均の符号は 3 workload とも 2 attempt で同じ (+ / + / −)、(c) `variance_plan_breach` は attempt-0001 が 3 本とも false、attempt-0002 が
write-heavy / read-heavy で true。2 attempt は同じ policy・同じ root seed・同じ物理順だが、node・時刻帯・bench 相の順序 (attempt-0001 は
read-heavy → write-heavy → balanced、attempt-0002 は balanced → read-heavy → write-heavy、いずれも bench lock の獲得順)・source commit
(driver の gate 部分) が異なり、どの差がどの値の差に効いたかは帰属しない。**2 attempt をプールした推定量・差・比・合成区間は作らず、区間の
重なりも計算しない** (D1993 項 6。attempt 間の比較のための事前登録は存在せず、事前登録 §5 は 1 attempt 内の 30 対に対する規則である)。
表 7 の丸めた値と表 7b の全桁の値は同じ `statistics` の 2 表記である。[9, 26]

**言えること / 言えないこと。** 言えるのは「A-1 の attempt-0001 と attempt-0002 が非認証 lane で完走し、いずれも 3 workload とも
`resolved-above-floor` の descriptive 出力を出した」「対差平均の符号 (+ / + / −) は 2 attempt で同じであり、3 走行および旧環境の 3 値とも
同じ向きである (観察であって再現判定ではない。推定対象・環境・分母が異なる)」までである。言えないのは「A-1 の値がある」「P2-4 の利得を
A-1 の登録済み対測定で確認した」「再現した」「反復間で安定している」— A-1 の充足・formal 化・昇格、attempt-0001 稿の限定 L-A1S-4
(単一 attempt を反復間の安定性へ一般化しない) の解除可否、3 本目の attempt の認可は判定されておらず (認可はユーザー手番、D2044 項 8)、
事前登録 §7.2 と policy は lane の反転を文書編集で行うことを禁じている。認可は attempt-0002 の 1 attempt 限りで、attempt-0003 には改めて
裁定と record が要り、本 attempt の性能値・`variance_plan_breach` は再投入・3 本目の理由にならない。認可 record は電子署名ではなく、
認可者が attempt-0001 の性能値を見た後に再現を選んだかどうかを識別しない (attempt-0002 は attempt-0001 の結果が公開された後に裁定・認可・
投入された)。分類は「有意差」「p 値」「検出力」の言葉へ翻訳しない。abort 率・latency・cache・IPC は測っていない。[T-1998] とは推定対象
(対差の算術平均 対 median 比) と配置が違い、A-2 / A-6 / [T-1998] とプールしない。[9, 12, 26]

## 6. 正しさ側の追加検証 — 採用候補 2 genome の検証相と、S-1 最終候補の B-8 検証

本節の 2 つの検証はいずれも trace 有効 build の正しさ専用走であり、性能値を含まない。対象が違うので (6.1 = 採用静的 backoff 2 genome、
6.2 = S-1 の最終候補である系側 gate 構成)、両者を比較せず、プールもしない。

### 6.1 採用候補 2 genome の検証相 (D2160)

採用候補 fixed 5 µs と fixed 10 µs について、現行 source (patch 改訂 `91a5bfca3` 後) の trace 有効 build で、独立 8 反復 × 3 workload
(計 24 verify / 候補、extime 3 s) の検証相を 2026-09-19〜20 に Pegasus gen_S で走らせた (D2160、S-1 (iv 付属) の規則を準用)。
校正 (段 A) は extime {3, 6, 10} s を各 1 回走らせ、verifier wall ≤ 600 s を適格とする規則で extime = 3 s に確定した。[10]

**表 8　検証相の判定 (`summarize` の出力)。**

| 候補 | 判定 | 判定集合 | anomaly | 未完走 (校正、開示) | extime | 本走の実消費 |
|---|---|---|---:|---:|---:|---:|
| fixed-5 | pass | 30 verify (本走 24 + 校正完走 6) | 0 | 2 件 | 3 s | 6316 S (1.75 h) |
| fixed-10 | pass | 30 verify (本走 24 + 校正完走 6) | 0 | 2 件 | 3 s | 6134 S (1.70 h) |

本走 48 枠は全件 `serializable`・certified・anomaly 0、bench 失敗・verifier 未完走・再検証は 0 件。校正の extime 10 s の走 2 件 / 候補
(balanced、write-heavy) は verifier が完走せず verdict を持たない (trace は保全済み)。検証相の記録時点では原因は未確定だった。後続の調査
(worklog entry 1744。保全済みの fixed-5 の 10 s trace 2 本を計算ノードで profile) は、balanced 10 s は fork した edge worker の
copy-on-write による OOM kill、write-heavy 10 s は worker が殺された後の pool の停滞 (SIGTERM 無視環境) と同定し、省メモリ化した verifier で
両 trace を完走させた (判定は旧版と bytes まで同一)。**当時の未完走記録・判定集合 30 件・extime 3 s は変えない** (規律 7)。fixed-5 の source bytes は
[T-1998] v1 の target と一致し、fixed-10 は A-2 当時の `src_token` と `91a5bfca3` の改訂分だけ異なる (A-2 当時のバイナリの再検証ではない)。[10]

**言えること / 言えないこと。** 言えるのは「両候補とも判定集合 30 verify で anomaly 0 (操作的事実)」までである。「全走 anomaly ゼロ」
「serializable であることが示された」「信頼度 1−εⁿ」とは書かない (数値 seed・乱数列の独立性は記録できない)。性能値を含まない
(trace 有効 build の commit 数は診断生値)。B-8 (種を変えた長時間実行による最終候補の検証) には数えない — 対象が S-1 の最終候補で
なく採用静的 backoff 2 genome であり、長さは校正規則で 3 s である。B-8 の事前登録の発効で「種を変えた」の仕分けは独立 process の
自己シードへ改まったが (§6.2)、それは検証相の対象と長さの違いを変えない。S-1 の充足でもなく、
A-2 / A-6 / [T-1998] の certified 記録を昇格も降格もしない (規律 7)。[10, 12, 27]

### 6.2 S-1 の最終候補 (案 A) の B-8 検証 — 発効した事前登録 v1 の下で 3 値判定 `pass`

B-8 は、最終候補の正しさを種を変えた長時間実行で検証する要件である。その別登録 (事前登録 v1、
`docs/b8-final-candidate-longrun-verify-preregistration.md`) は対象の 2 案のうち**案 A** = S-1 の最終候補である系側 gate 構成 (§7 の合成軸。
`g_rl` = balanced / read-heavy、`g_rt` = write-heavy) を推奨し、D2186 項 1 がこれを認可して発効束で固定した (D2194 項 1)。本走は
**独立 8 反復 × 3 workload (計 24 verify)** を trace 有効 build で走らせる。事前登録は 2026-09-21 に発効し (発効 commit `624c84986`、D2194 項 1 の承認)、発効前に校正・本走は走らせていない。校正 (段 A、3 job) は
各 workload で extime {6, 10} s を各 1 回走らせ、6 行すべてが適格 (bench 完走・trace 保全・verifier 完走・`serializable`・certified・
anomaly 0・identity 一致・verifier wall ≤ 1800 s) だったので、適格集合の共通部分の最大値として規則が機械的に **extime = 10 s** を決めた。
本走 (段 B、6 job) は同日 09:17〜10:13 JST に Pegasus gen_S で走った。identity は当時の現行 pin `e9e477ca` と現行 patch に束縛され
(`g_rl` `b0f95b21…` / `g_rt` `a0219ce0…`、24 枠すべてで build 前後とも期待値と一致)、S-1 campaign 当時 (旧 pin `d706650c`) の
source bytes とは異なる。[27, 28]

**表 8b　B-8 の判定。** 判定の各行は runner v5 の `summarize` の出力 (事前登録 §6.1 の順序付き 3 値を 1 度だけ評価)、費用の行は
dispatch Elapse の和 (結果稿 §3.4。runner 内部の集計値とは別)。

| 量 | 値 |
|---|---:|
| 判定 | `pass` |
| 判定集合 | 30 枠 (本走 24 + 校正の完走 verdict 6) |
| anomaly を検出した verify | 0 |
| `serializable` でない verdict | 0 |
| 未完走 (校正) / bench 失敗 / 規約不適合 (record 段 / job 段) | 0 / 0 / 0 / 0 |
| 再検証 (`reverify`) / 再開 (`--resume`) | 0 / 0 |
| extime | 10 s (初期選択も 10、段下げ無し) |
| 反復数 | 8 / workload (削っていない)、3 workload で 24 verify |
| 本走の実消費 (dispatch Elapse の和) | 9,280 S (予算 ≤ 14,400 s / 対象) |

本走 24 枠はすべて bench 完走・trace 保全済み・verifier 完走・`serializable`・certified・anomaly 0・identity 一致だった。これで B-8 の
3 要件 — 対象 = S-1 の最終候補 (案 A)、種 = 独立 process の自己シード (事前登録 §3.2。各反復を独立な bench process として起動し、各 worker
thread が `std::random_device` から自己シードする。seed 値は記録しない)、長時間 = extime 10 s (開発相と D2160 の検証相が用いた 3 s より長い)
— が揃った検証で、3 値判定は `pass` だった。[27, 28]

**言えること / 言えないこと。** 言えるのは「S-1 の最終候補 (案 A) は、発効した事前登録 v1 の規則の下、独立 8 反復 × 3 workload・
extime 10 s の本走 24 枠と、校正で完走した 6 枠 (3 workload × extime 6 s / 10 s、各 1 回) を合わせた判定集合 30 枠のすべてで anomaly 0 で
あり、runner の 3 値判定は `pass` だった (操作的事実)」までである。
`pass` は規則の機械適用の出力であって研究の成功宣告ではない (D12)。certified の保証範囲 (観測した trace の依存グラフ上の判定であり、
predicate・phantom・公平性・未観測の実行は対象外) を超えず、「serializable であることが示された」「証明した」「保証」「信頼度」とは
書かない。「種を変えた」は独立 process の自己シードという操作的定義で、独立性は操作的仮定であり `std::random_device` の実装は
測っておらず、同じ 32 bit 値の再出現も検査できない。「異なる乱数列であることを検証した」とは書かない。「長時間」は extime 10 s という操作的定義で、長さ・反復数の検出力は
主張しない。性能値を含まない (規律 1)。S-1 当時のソース・バイナリの再検証ではなく、binary は node ごとの別 build なので「同一 binary で
24 反復」とも書かない。S-1 事前登録 (iv 付属) の充足ではなく、S-1a の不成立と S-1b の性格 (結果既知の追試) を変えない (§7)。§6.1 の
検証相 (案 B) の判定を変えず、両者を比較しない。D2160 の校正で 10 s が未完走だったこととも比較しない — 対象も verifier の版も違い、
本走で 10 s が完走したことは「verifier が改善した」ことの測定ではない。扱う失敗条件は事前登録の (a) (合成が certified を破るか) だけで、
(b)〜(e) については何も言えない。1 回の cohort の結果であり、別の日・別の node 集合での再現は取っていない。[27, 28]

### 6.3 verifier の検出期待表と容量 — 壊した実装を捕まえるか (検出力の網羅的な証明ではない)

正しさゲートの価値は、壊れた実装を実際に捕まえるかに依存する。設計 (2026-09-22、計算なし) は、現行の判定が abort・取引内の中間版・値・範囲読みの述語・
liveness を判定の外に置くことを整理し、CC 変異 34 と無改変 si 1 の検出期待表を置いた。その後、期待表の行を計算ノードで実走した。各行は投入前に期待と分類の規則を
事前登録し、verdict が serializable の行は、変異の枝に発火診断 (枝に入った回数・元コードと違う挙動を生んだ回数・その取引が commit した回数) を置いて
「盲点として certified」(変異が挙動を変え、その取引が commit した履歴が certified になった) と「未発生」(変異がそもそも起きなかった) を分けた (D2239)。[29, 30, 31]

**表 8c　検出期待表の実走 (各 cell 1 回の有限の走)。** silo は pin `e9e477ca`、mocc は pin C (`68106660`)。

| 対象 | 母集合 | 期待した層で検出 | 別の層で検出 | 盲点として certified | 未発生 | 五分類の外の状態 | 対照 |
|---|---|---:|---:|---:|---:|---|---|
| silo 既存壊し patch (2026-09-23) | 10 本・13 run | 12 run | 1 run | — | — | — | — |
| silo 新規変異 + trigger-misattr (2026-09-23) | 15 行 (新規 14 本 = 変異 11・対照 3、misattr 1) | 3 | 1 | 6 | 2 | — | 対照の誤検出 0 |
| silo sort-nonswo V07 (2026-09-23) | 4 run (壊し 17 要素・16 要素、stock 2) | 0 | 1 (17 要素で process の異常終了) | — | — | 16 要素は S (verifier は V07 を捕まえない) | stock 2 本は S |
| mocc 既存 4 本 + 新規 V25 + 対照 V34 (2026-09-26) | 34 cell | 20 | 0 | 1 | 2 | 発火未確認の S 2・停止 3 | 対照正常 6 (誤検出 0) |

mocc の同 job の stock 対照 28 run はすべて certified で、別の層・誤検出・帰属不能は 0 である。4 thread の既存 2 本では、期待した X に加えて巡回と version dup が
併発した (主分類は期待した層)。V07 の 17 要素の壊し build は hang の主予測に反して SIGSEGV で止まり、原因は検証していない。[30, 31, 32]

容量の側では、既存の実測の最大は巡回 0 で 3,275 万取引・辺 5.95 億・verify 896 s・node の増分 81.2 GiB (fixed 5 µs の read-heavy 6 s) で、読み集合の再検証を外した
壊し patch の 3 本 (巡回 472〜3,052 本) と参照 genome の 3 s trace 4 本もすべて完走した。取得した記録では、別機構を要する資源の超過は観測されなかった。[33]

**言えること / 言えないこと。** 言えるのは「事前登録した期待と分類の下で、壊した silo・mocc の実装の多くを期待した層で捕まえ、捕まえなかった行を
盲点として記録した」までである。言えないのは検出力の網羅的な証明である。各 cell は 1 回の有限の走で、停止 (mocc の V25 の 4 thread、120 秒の run timeout。同 job の
stock は約 1 秒で完走) は deadlock の実証ではない。「盲点として certified」は verifier の欠陥の主張ではない — 盲点の行には、trace にも verifier にも現れない値・
取引内の読み・TID 規則の変更や、直列化可能性の条件ではない lock 順の違反 (V25 の 1 thread) が含まれる。V34 の対照が示すのは評価された 2 site の等価性までである。
mocc の検証は証人なし verifier で、commit trace の完全性までは主張しない。容量の最大値は観測した規模であって、安全を保証する境界ではない。性能値は含まない。[30, 31, 32, 33]

### 6.4 TPC-C 段 1 の trace の判定 — 合成候補の評価ではない

VLDB 向けの方針 (D2212 項 2、D2219 項 2) は TPC-C を段 1 (NewOrder / Payment、点読み・点書き・insert のみ) → 段 2 (範囲読みを含む全 5 取引) の順で必須にした。
段 1 では、verifier が trace v3 を (表, key) で読み (D2224)、段 1 の存在契約 (その object の最初の committed write が insert でなければ genesis から存在する、ほか) を
silo の版付けに裏付けて検査するようになった (D2232)。CCBench 側の silo の v3 emitter が出した実 TPC-C trace (silo、36,156 取引) について、verifier は
直列化可能 (存在違反 0) と判定し、存在違反 1 行を注入した写しは認定しなかった (2026-09-23、公開 API)。続いて pipeline の trace 検査段が、binary 名が `tpcc_` で
取引比の 4 flag が段 1 の 57:43 (Payment 43、OrderStatus / Delivery / StockLevel 0) に文字列で一致するときだけ trace を走らせ、verifier の後に v3 を要求するように
なり、同じ実 trace と実 stdout は pipeline の executor でも受理され、存在違反と末尾 frame 欠落の写しは reject された (D2238)。57:43 は CCBench の既存 flag で
3 取引を 0% にした比で、既定の 45 : 43 の正規化は整数 % で表せない。さらに、silo と mocc の emitter を現 pin C の上に 1 系列で並べた結合候補
(未 push の local branch) を計算ノード 1 走で確かめ、TPC-C の silo・mocc とも v3 の構造・witness・内容、YCSB の silo・mocc とも v2 の certified、TRACE=0 の
前処理と逆アセンブルの一致、結合固有の変異 4 件の検出を得た (D2244)。**本稿は certified を §3.4 の限定 (i) のとおり YCSB の観測 trace 上の判定として使ってきたので、
TPC-C の trace にはこの語を使わず「verifier が直列化可能と判定した」と書く。** [34, 35, 36]

**言えること / 言えないこと。** 言えるのは「段 1 の silo の実 trace 1 本を、verifier が段 1 の存在契約の下で直列化可能と判定し、pipeline の trace 検査段も
同じ trace を受理した」までである。言えないのは、TPC-C で合成候補を認定・評価したこと、TPC-C の性能、段 2 の保証である。production の build は YCSB の binary だけを
作り、campaign で TPC-C の候補を評価する配線は無い。現 pin の tpcc binary は v2 を出すので v3 要求で reject される (v3 emitter は pin に入っていない)。現行の D297 検査器は
結合候補を header 差分で拒否し、その受理方式はユーザー裁定待ち (4 択) である。trace の取引種別を pipeline で検査することはしていない。[34, 35, 36]

## 7. 合成軸と既知軸最良 — S-1a は不成立、S-1b は成立、適格率次元は未実証

trigger-gating は abort の要因に応じて backoff を発火させる軸である。S-1 (2026-07-16、旧環境 `linux-baremetal`・CCBench `d706650`・
`perf stat` 下) は、この軸の系側 gate 構成 (`g_rl` / `g_rt`) を、2026-07-12 に凍結した既知軸最良 3 種 (`p2_2_flag_opt`、
`backoff_fixed_best`、`sort_best`) と 3 workload で直接比較した登録追試である。各 cell は 8 標本 (block1 4 + block2 4、各標本は
session 内 5 反復の中央値)、判定境界は相対中央値差 +3% (gate (1)) と 2 ブロックの方向一致 (gate (2))、family 判定は 9 対の連言である。
2026-09-20 に凍結 report・fig4 provenance・4 campaign の WAL から単独稿へ再抽出された。[11]

**表 9　S-1a の 9 対 (左 = 合成軸、右 = 既知軸)。** 中央値は各 cell の 8 標本の中央値。相対中央値差は report の
`relative_median_difference` を百分率にして小数第 1 位に丸めた値。

| 負荷 | 右 cell | 左 median (tps) | 右 median (tps) | 相対中央値差 | gate (1) | gate (2) | 判定 |
|---|---|---:|---:|---:|---|---|---|
| write-heavy | `p2_2_flag_opt` | 1,689,666.5 | 1,863,839.5 | −9.3% | 不通過 | 通過 | 不成立 |
| write-heavy | `backoff_fixed_best` (fixed 10 µs) | 1,689,666.5 | 2,639,678.5 | −36.0% | 不通過 | 通過 | 不成立 |
| write-heavy | `sort_best` | 1,689,666.5 | 1,086,580.5 | +55.5% | 通過 | 通過 | 成立 |
| balanced | `p2_2_flag_opt` | 1,705,405.0 | 2,723,265.0 | −37.4% | 不通過 | 通過 | 不成立 |
| balanced | `backoff_fixed_best` (fixed 5 µs) | 1,705,405.0 | 3,078,552.0 | −44.6% | 不通過 | 通過 | 不成立 |
| balanced | `sort_best` | 1,705,405.0 | 929,335.0 | +83.5% | 通過 | 通過 | 成立 |
| read-heavy | `p2_2_flag_opt` | 3,803,639.0 | 8,474,516.5 | −55.1% | 不通過 | 通過 | 不成立 |
| read-heavy | `backoff_fixed_best` (fixed 2 µs) | 3,803,639.0 | 7,906,185.5 | −51.9% | 不通過 | 通過 | 不成立 |
| read-heavy | `sort_best` | 3,803,639.0 | 1,916,834.0 | +98.4% | 通過 | 通過 | 成立 |

成立した 3 対の `p_perm` は 1/4,900 (完全分離) だが、family は 9 対の max を取るので family p = 1.0 のままで、**S-1a は不成立**である。
落ちた 6 対はすべて gate (1) 不通過で gate (2) は通過しており、負けは 2 ブロック間で方向が一致した負けである (cross-run 再現の
観測であって機序の説明ではない)。負けた 6 対は左の 8 標本すべてが右の 8 標本すべてより低い (確率優越 0.0)。正しさは別 build の検査で、
正典 4 campaign の `verify_done` 324 件 (develop は cell ごとに `legacy` と `s2` の 2 件 = 36 件、floor 144 件・block1 72 件・block2 72 件は
session ごとに `legacy` 1 件 — `legacy` 306 件 + `s2` 18 件) がすべて `serializable` / `certified` / anomaly 0 である。性能の認証ではない。
図は fig4 (失敗報告図)。[11]

同じ report の別 family である S-1b (gate 述語を恒真にした対照との 3 対比較) は成立し (`p_family` 0.00020408163265306123、相対中央値差
balanced 0.874244 / write-heavy 0.60638 / read-heavy 0.999298)、Holm 族 4 の第 1 段 (α 0.0125) を通過した。これは軸を有効にする効果を
支持するが、既知軸最良への優越を支持するものではない。効果は先行する機械 sweep で既知だったため、結果既知の事前登録付き追試として
位置づけ、未見データでの新発見とは数えない。[11, 13]

**表 10　Holm 族 4 の判定 (2026-07-16、人間承認)。** 族 α = 0.05、段階 α は p 昇順に 0.05/4、0.05/3、0.05/2、0.05/1。

| 検定 | 名目 p (family) | Holm 段階 α | 調整済み判定 |
|---|---:|---|---|
| S-1b | 0.000204 | 0.0125 (第 1 段) | 有意 — 成立 |
| S-2 | 0.115 | 0.0167 (第 2 段) | 非有意 (ここで手順打ち切り) — 不成立 |
| S-1a | 1.0 | (打ち切り後) | 非有意 — 不成立 |
| S-3 | 1.0 | (打ち切り後) | 非有意 — 棄却 (退化を示せない) |

軸提案の適格率を比較した S-2 では、本アーム 20/20 に対して選定のみを無作為化した C4 は 17/20 で、差は有意ではなかった
(名目 p = 0.1154)。C4 は生成過程全体を非 LLM へ置き換えた対照ではない。旧 S-3 の診断数値を除いた C5 では適格率が 20/20 で本アームと
同率だった (名目 p = 1.0)。登録した「帰属遮断による適格率の退化」は示されなかった。ただし採点基準は診断への言及を加点しないよう
設計されており、この非有意結果を診断の寄与が存在しない証明とも読めない。これは性能診断の入力と提案の適格率についての比較であり、
直列性の反例を次の合成へ渡す効果の比較ではない。P2-5 の貪欲探索、S-1 の機械探索済み候補、S-2 の無作為選定は、異なる問いに対する
対照であり、まとめて「同じ編集面・同じ予算で LLM 生成が非 LLM 生成を上回った」と扱うことはできない。[1, 11, 13]

**言えること / 言えないこと。** 言えるのは「合成した軸は既知軸の一部 (sort) には 3 workload とも +55.5%〜+98.4% で明確に勝つ」
「登録した追試として S-1b は成立した (新発見ではない)」「登録した 9 対の family 判定 (S-1a) は不成立で、縮小主張 S' の headline
(既知軸最良の超越) は成立しなかった」までである。言えないのは「合成が無価値である」(既知軸集合は単軸最良の凍結有限集合 = 合成
未探索の下界であり、超えなかったことは無価値の否定ではない)、「新しい否定的発見」(結果既知の追試の失敗報告である)、
「適格率次元の発見再現性」(S-2 不成立・S-3 棄却により未実証のままで、S-1b の成立はこの限界を解消しない — 確定文言の必須併記)、
そして現行環境 (§3〜§6.1) との比較 (環境・pin・genome・identity が違い、`backoff_fixed_best` の値が A-2 / A-6 の採用値と同じでも
同じ測定ではない。§6.2 は同じ最終候補を扱うが、正しさ専用走で性能値を持たず、identity も S-1 当時と違う)。S-1 の凍結資料に記録された本走は 1 回であり、本走間の再現性は判定しない。[11, 12, 13]

この最終候補 (系側 gate 構成 `g_rl` / `g_rt`) の正しさを種を変えた長時間実行で検証した B-8 の結果は §6.2 に置き、性能の判定とは別の段で
書く。B-8 の `pass` は当時の現行 pin (`e9e477ca`)・現行 patch の trace 有効 build についての正しさ側の結果であり、S-1a の不成立も S-1b の性格も変えない。[27, 28]

**関数単位の軸 `silo-function-policy` の偵察と既知最良との小比較 (探索的)。** VLDB 向けの方針 (D2212 項 3) は、フラグや定数でなく関数単位の方策を
合成空間に開いた (正しさゲートは不変、D2214)。段階 C は骨格 patch・型付き構文検査 (契約 fixture 85 本)・機構変異・手書き方策の生死確認で出口を満たした
(診断 build で、certified 候補とは称さない、D2226)。段階 D は型付き有限 IR の固定 16 点 (未調整、定数は段階 C の手書き方策から結果を見る前に固定) を write-heavy の
8 job で偵察し、二値 = true を返した — 16 点すべてが legacy と性能構成の両 verify で certified、同 job の abort0 (骨格内の退化点) 比 1.34〜1.78、ID 順の先頭 4 点が
別 job で 1.53〜1.62 を再現した (D2234)。ただし基準 abort0 は abort 率 0.78 の thrashing 点で、待機を入れる方策ならほぼ何でも 3% 線を越える。そこで段階 E の前に、
同じ 16 点・8 job の構成に既知最良の参照 3 本を同じ job に置いた小比較を 1 回走らせた (D2235 項 7、D2240)。[37, 38, 39]

**表 10b　既知最良との小比較 (write-heavy、8 job、各方策 5 rep の中央値、千 txn/s)。** 参照は stock (`BACK_OFF=1`)・`B0-L-W0` (`BACK_OFF=0`)・静的 10 µs
(stock 木へ `patches/silo-backoff-fixed.patch` を当てる元の適用方法、実効 define を検査)。比は IR 点の中央値 ÷ 同 job の参照 3 本の中央値の最大 (最良参照比)。

| 項目 | 値 |
|---|---|
| 参照 3 本のうち最良 | 全 8 job で静的 10 µs |
| 同 job の中央値 (静的 10 µs / `B0-L-W0` / stock) | 3,944〜4,011 / 2,374〜2,533 / 1,343〜1,378 |
| IR 16 点の最良参照比 | 0.836〜1.069 (16 点すべて比較に適格) |
| 3% 線を越えた点 | 3 点 (1.062〜1.069)。いずれも 5 rep の最小が同 job の静的 10 µs の最大を上回った |
| 残り 13 点 | 1.005 以下 |
| 段階 D (別 job) との関係 | 同じ 3 点が段階 D でも上位 3 点で、throughput は 1% 以内で一致 |

越えた 3 点は、lock 競合への応答を「試行 4 回まで再試行」にする水準を持つ (D2240)。計算は計測 8 job の Elapse 6,180 秒 (1.72 node 時間) である。
第 35 回の裁定 (D2243 項 1) は、この結果を材料に軸を段階 E (driver・role・firewall の機械化) へ進め、3 点の別 job 再測は段階 E の条件にしない一方、
**論文でこの 3 点を既知最良を超えた点として書く前に再測する**と定めた。段階 E は本稿の採用時点で実装されておらず、LLM が関数方策を生成した記録は無い。[38, 39, 40]

**言えること / 言えないこと。** 言えるのは「固定テンプレートの部分空間 16 点に、同 job の静的 10 µs (現 pin 相当で再評価した既知最良) を 6〜7% 上回る点が 3 つ観測された」
という探索的な観察までである。報告カテゴリは偵察 (preliminary) で事前登録の構成ではなく、1 回・再測なし・16 点から最大を選ぶ多重選択の補正なし・3% 線は Pegasus で
未較正の暫定値であり、段階 D との一致は事前に定めた再現判定ではない。**B-1 (既知軸最良の超越) は S-1a で不成立のままで、この小比較はその判定を変えない。**
全 IR・LLM が書く C++ 方策の空間・別 workload (balanced・read-heavy・TPC-C)・静的 10 µs 以外の静的値 (現 pin で掃いていない) との比較については何も言わない。
診断 build は certified 候補と称さない。計測は pin `e9e477ca` の branch で行った (silo の source は pin C と同じ)。[38, 39, 40]

## 8. 正しさゲートを毎反復回す loop の到達と、還流の効果の未取得

### 8.1 K2 手動 loop の 4 巡 — 実測の還流 3 回、診断の還流 2 回、4 巡目で初めて同 job の stock 対照

取得済み記録には、測定記録を知識入力 (K2) とした候補を当時の新しい pin (`511c9538`) で評価し、検証から性能測定、終端記録まで到達した事例がある。
2026-09-10 の再評価 (campaign `p3-s4-loop-s4-autonomous-409e13f8`、既存の値 20 の proposal を無変更で再利用) では、現行 verifier v2 が
466,113 commits、81,919 aborts、anomaly 0 の履歴を serializable と判定し、候補 1 件が committed となった。ここでいう abort 数は
トランザクションの abort 数であり、合成候補の失格数ではない。[14]

その後、K2 手動 loop を 4 巡実施した。まず 3 巡 (2026-09-16 / 09-18 / 09-19) を述べる。1 巡 = (i) planner-v4 と coder-v4-autonomous-k2 が K2 知識源を含む型付き入力から提案値を 1 つ
作る → (ii) 既存の段 4 loop 経路がその 1 値を build (trace / perf 別 build) → verify (trace 有効) → bench (trace 無効) の順で 1 回評価し
WAL に terminal record を書く → (iii) critic が digest と WAL を読んで帰属を試み、次の提案の方向を書く。「還流」は (ii) の実測または
(iii) の診断が次の (i) の型付き入力に入ったことを言い、**実測の還流は 2 回 (巡 1 → 2、巡 2 → 3)、診断の還流は 1 回 (critic-2 → 巡 3)
成立した** (3 巡の時点。4 巡目は下の段落)。3 巡は独立の 3 wave (2026-09-16 / 09-18 / 09-19) で、campaign ID は同一だが別 tree・
別 WAL である (ID の同一は走行の同一ではない)。図は fig12 (データフローの説明図、値なし)。[15]

**表 11　3 巡の評価 3 本の terminal record (campaign WAL)。** commits / aborts / anomalies は trace 有効 build の verify 走、
`median_tps` 以下は trace 無効 build の bench 走 (2 反復) の値。

| 巡 | 日付 | job / host | 提案値 | verdict (legacy) | commits / aborts / anomalies | `median_tps` | run 内 cv | 提案の性質 |
|---|---|---|---:|---|---|---:|---:|---|
| 1 | 2026-09-16 | `1216.nqsv` / bnode058 | 20 | serializable / certified | 469,618 / 83,034 / 0 | 719,324.5 | 0.01703 | run-card の既知値の再提案 |
| 2 | 2026-09-18 | `4954.nqsv` / bnode110 | 25 | serializable / certified | 445,394 / 71,877 / 0 | 687,508.5 | 0.01007 | 未評価だった値 (巡 1 が保存した proposal-2) |
| 3 | 2026-09-19 | `10761.nqsv` / bnode020 | 10 | serializable / certified | 523,120 / 122,211 / 0 | 815,983.0 | 0.00159 | critic-2 の診断の候補値と同じ (既知値集合の外) |

巡 2 では critic の診断が型付き入力に無く、coder は critic の候補 10 に対し既知値 20 を再提案した (両者の因果は未検証)。巡 3 では
[T-2783] (D2155) が実装した型付き入力 `k2_critic_diagnosis` (critic-2 逐語の exact 6 field) が planner-4 / coder-4 の両入力に届き、
coder-4 が 10 を出した。診断が「届いた」こと (入力 JSON に key が実在し、逐語から作った bytes と一致する) と「参照したと申告した」
ことは書けるが、「効いた」(提案値を変えた因果) は書けない — planner-3 と planner-4 の入力は診断 key 以外同一、coder-3 と coder-4 の
入力は診断と `planner_direction` の差だけだが、各条件 1 回の別起動であり、無作為化も反復も無い。critic-3 の avoid は「候補 10 の
評価をもって『診断が効いた』と数える」ことを明示的に禁じる。規律 6 の検査は coder の 4 出力 (coder-1〜4) が `instruction_like_content_detected=false`、
planner / critic は散文で「指示めいた文字列なし」と自己申告した。巡 2 の投入は 2 本 (1 本目は job body の preflight が拒否、評価に
到達せず。D2148 項 2 が今回限定で事後承認)。[15]

3 巡では同 job の stock 対照がどの巡にも無かった。その経路はユーザー裁定 D2172 項 3 で決まり、pair launcher の初投入 (2026-09-20、`13339.nqsv`) は
stock 側が one-shot claim leaf の `ClaimError` で build に到達せず不成立だった (D2187、entry 1754。候補 10 の再評価 811,956 tps は当時の判定として保持し、
pair・改善の証拠に昇格させない)。1 process の認可 session で claim を共有し候補 → stock の順に評価する driver への修復 (D2205、entry 1795) の後、
ユーザー裁定 D2211 項 1 が pair の再投入 1 job と、pair が成立したときだけ 4 巡目 1 job を認可した。[15, 16]

**pair の再投入と 4 巡目 (2026-09-22〜23)。** pair の再投入 (`16269.nqsv`、巡ではない。候補 = 巡 3 の値 10 の再評価) と 4 巡目 (`16312.nqsv`) は、
どちらも候補と同じ job・同じ campaign・同じ WAL で stock (CCBench 既定の `BACK_OFF=1` の適応 backoff。`BACK_OFF=0` の無 backoff ではない) を評価し、
候補・stock とも `serializable` / certified / anomaly 0、stock の `src_token` は `stock` だった。4 巡目の入力は巡 3 の repo 内の派生物だけから組み
(巡 3 の campaign 原本が消失した後の択 A、D2194 項 2)、pair の結果は入れていない。planner-5 は decrease / large を出し、coder-5 は値 5 を出した。
4 巡目の後に critic-4 を 1 回走らせ、planner-5 / coder-5 / critic-4 の出力を材料レポート (機序仮説層 v3、`mechanism_hypotheses` 1 件、`source_refs` 14、
`certifying_input=false`) へ取り込んだ。これで **実測の還流は 3 回 (巡 1 → 2、巡 2 → 3、巡 3 → 4)、診断の還流は 2 回 (critic-2 → 巡 3、critic-3 → 巡 4)**
になった。critic-4 の診断を次の提案へ戻す巡 5 は無い。[41]

**表 11b　同じ job の候補と stock (trace 無効 build の bench、2 反復の `median_tps`)。** 比は同じ job の 2 点の記述値。

| job | 位置づけ | 候補 | 候補 `median_tps` | stock `median_tps` | 候補 / stock | perf の abort 率 (候補 / stock) |
|---|---|---:|---:|---:|---:|---|
| `16269.nqsv` (bnode001) | pair の再投入 (巡ではない) | 10 | 825,490 | 348,883 | 2.366 | 9.01% / 1.815% |
| `16312.nqsv` (bnode052) | 巡 4 | 5 | 884,922.5 | 354,948 | 2.493 | 10.105% / 1.835% |

2 job の stock どうしにも +1.74% の差がある (別 job・別 node で同じ stock を 2 回測った 1 対)。**候補 5 と候補 10 の差 (+7.20%) と比の差 (2.366 → 2.493) は
job・node の差と分離できず、設定の効果に帰属しない。** 比はこの配線 (4 threads / 100,000 records / rr50 / skew 0.9 / rmw=false / extime 1 秒 / reps 2) の 1 点の記述値で、
固定 backoff が適応 backoff より良いという一般命題ではない。critic-4 の「適応は待ちすぎ」は LLM の帰属記録であって本稿の判定ではない。[41]

**言えること / 言えないこと。** 言えるのは「限定スコープで、設定した正しさゲートを一度も緩めずに、コード粒度の合成を certified まで
回せる safe variant loop が成立し、当時の新しい pin (`511c9538`) の下で certified の terminal verdict へ到達した (2026-09-10 の再評価、3 巡、pair の再投入、4 巡目)」
「実測の還流 3 回と診断の還流 2 回が既存経路で成立した」「4 巡目で初めて同じ job の stock 対照を伴って評価した」までである。言えないのは、性能の改善・退行
(巡どうしの値 20 / 25 / 10 / 5 は別日・別 node・別 tree の非同時刻の点で、2 巡目比 +18.7% のような比を書いても性能主張にならない。同 job の比も 1 点の記述値)、
候補 5 が候補 10 より良いこと (別 job)、知識 (K2) や診断の因果効果 (統制が無い)、新しい CC 構造の合成 (動かしたのは固定 backoff の値の literal 1 つ)、
B-4 の材料としての適格性・B-6 (リーク制御を完備した実走) の充足 (critic は 4 巡とも Bash を持つ legacy role)、そして規律 3 が求める「なぜ壊れたか」の還流 —
4 巡の評価とも anomaly 0 で、正しさ側の赤の還流は 1 度も発火していない。K2 は論文の必須経路の外にある (D2211 項 1)。
`abort_rate` の集約規則が巡 1 (速い側 rep) と巡 2 以降 (中央 2 件の中央値) で違うので、巡の abort 率を同じ規則の値として並べない。[15, 41]

### 8.2 反例フィードバックの効果 — B-4 は未実走

反例フィードバックによる改善は、これらの到達実績からは結論できない。詳細な反例の効果を扱う B-4 は、両アームに粗い成功・失敗・
拒否の結果と緑候補の指標を共通に渡し、構造化 rejection の詳細の有無だけを変える設計である。D1936 項 8 で有意性を主張せず適格な
少数の赤を用いる記述統計への限定が採用され、適格確認済みの赤 precursor は本稿の採用時点でも 0 件で、必要数に満たない間は実施不可
のまま走らせない (D1986 項 4)。B-4 床値 (floor-pair) の w1 は凍結 spec 3 本 (rr95 / rr50 / rr5) で実投入され、3 job とも terminal
`complete` (124 / 124 session、62 / 62 標本、drop 0) で完走したが、値の比較・集約・採用は行っておらず、w2 と finalize は後続である。
成功した K2 候補を赤 precursor の代わりに数えない。配線・登録・裁定の存在を、反例還流による性能や探索効率の改善の実証へ置き換える
ことはできない。[17, 12]

## 9. backoff の機序の帯域外 — 待ち方 grid と静的右 tail

これらは 2 本目の論文 (`docs/paper-story-backoff/`) の主題と重なるが、本体論文では **静的 backoff 軸の性能地形が headline の
2 点 (§2〜§4) の外でどう振る舞うかの記述的な材料**としてだけ引く。機序は書かない (D1678、D1724、D1857)。いずれも性能は未認証
(`official_certification: false` / `performance_certified: false`) で、ここにある性能値を根拠に variant を採用してはならない (規律 2)。
数値は 2 本目の論文と共用しない (D1637)。[18, 19, 20]

### 9.1 待ち方 grid — 登録した 1 contrast は 3 族とも `different`

事前登録 (`docs/b10-backoff-shape-preregistration.md`、発効版 commit `77b33e37d`) に対して report phase (request `978195.nqsv`、
2026-09-05) が、3 campaign × 45 cell = 135 cell (性能 cell 135/135、検証 slot 270/270、135 cell とも correctness certified) を集約し、
登録した `constant` 対 `symmetric-modulo` (μ = 2〜100 µs の 6 点 × 3 block、48 スレッド) の 1 contrast について 3 族 Holm を出した。[18]

**表 12　3 族 Holm (α 0.05)。** raw p は全 2^18 通りの符号反転を列挙した exact 値。

| 族 (負荷) | outcome | 対の数 | raw p | Holm p | 方向 |
|---|---|---:|---:|---:|---|
| write-heavy | `different` | 18 | 0.025566101 | 0.025566101 | `symmetric-modulo` が高い側 |
| balanced | `different` | 18 | 0.00026702881 | 0.00053405762 | 同 |
| read-heavy | `different` | 18 | 7.6293945e-06 | 2.2888184e-05 | 同 |

36 cell (`symmetric-modulo` 18 + `constant` 18。後者は自分自身との対なので効果 0・区間 [0, 0] で `inside-equivalence-range`) の効果量は
すべて `estimable` で、95% paired-block 区間と等価域 ±3.0% の関係は**内側 32、境界を跨ぐ 4** (write-heavy μ 2・μ 25、balanced μ 2・μ 25)、
**外側 0**、判定不能 0 である。`symmetric-modulo` 18 cell のうち点推定が負なのは write-heavy μ 5 の 1 cell (−0.97%、区間は 0 を含む) だけで、
残り 17 cell は正。54 個の対差のうち負は write-heavy 5 / 18、balanced 2 / 18、read-heavy 0 / 18 (最小 −1.49%、最大 +2.66%)。
図は fig13 (`figures/fig13_b10_waiting_grid_forest.*`、2026-09-20 着地) — 3 族の Holm 判定と 36 cell の効果量・95% paired-block 区間・
等価域 ±3.0% を 1 行 × 3 panel の forest 図に描いた結果図で、判定は report の provenance から読み、生成器は同じ式で再計算して一致を要求する
だけで判定を作らない。区間が帯の内側にあることは等価性の成立ではなく (等価性検定はしていない)、cell ごとの有意差は判定せず、静的右 tail の
2 cohort (fig8 / fig8b) と合成・比較しない。稿 (D1678) の限定「論文図は無い」は起草時点の事実である。[18]

**言えること / 言えないこと。** 判定が及ぶのは、登録した `constant` 対 `symmetric-modulo`、μ = 2〜100 µs、48 スレッドの Silo / YCSB
3 workload という 1 つの対比だけである。方向は 3 族とも `symmetric-modulo` が高い側 (事前登録 §3 が認めた範囲の記述)。`binary`・
3 水準の ladder・用量反応・待ち方の効果一般・機序 (「差の機序が脱同期だけである」とは書けない — 総待ち量 = 呼び出し回数 × μ も
同時に動く) は判定していない。μ は指示値 (構成上の平均) で、実走行の待ち量の分布は測っていない (D1097)。判定下限 (床値) による
退行判定は行っておらず、参考幅は外部 floor 由来で検出力の保証ではない。3 workload の実行は別 job・別日・別 driver 版で、
write-heavy の実行 host は成果物に無い。事前登録 §9 の 9 項目はいずれも閉じない (うち 5 項目は D1678 が見送り、再訪条件は査読での
要求)。「B-10 を閉じた」とは書かない。[18]

### 9.2 静的右 tail — 「登録した述語では、表現可能域 9999 µs までに飽和を観測しなかった」が独立な 2 cohort で成り立つ

事前登録 (`docs/b10-backoff-static-tail-preregistration.md`) の格子 (境界参照 1000 µs + 右 tail 7 点 1250 / 1768 / 2500 / 3535 / 5000 /
7070 / 9999 µs、3 workload × 8 点 = 24 cell、各 5 反復) の本走が、cohort 1 (group `b10-backoff-grid-20260915T061814Z-545445`、
2026-09-15) と、事前登録の 2026-09-19 追記 (D2157) で独立再現と地位を固定した cohort 2 (group `b10-backoff-grid-20260919T131526Z-2235286`、
2026-09-19) の 2 度完走した。両 cohort とも集団 verdict は `not-observed-in-any-workload`、3 workload とも `not-observed`、
`saturation_location` は `null`、18 区間すべて `declining` (`saturated` も `indeterminate` も 0)、`failures` は空、
`performance_certified` は `false`、正しさは trace 有効の別走行で 120 記録とも certified・anomaly 0 (検査条件は `legacy` mode の
小設定 — 4 スレッド・200 tuple・rratio 50・rmw 有効・1 秒・max ope 5 — であり、性能を測った条件そのものではない)。図は fig8
(cohort 1) と fig8b (主結果 cohort 1 と独立再現 cohort 2 を上下 2 block で区別して併記した後継図)。[19, 20]

**表 13　同じ格子上の throughput (過抑制の費用、5 反復の算術平均、単位 tps) と abort 率 (5 反復平均)。** 事前登録 §3 が併記を要求する。
中央値ではない。

| backoff (µs) | write-heavy tps (c1 / c2) | balanced tps (c1 / c2) | read-heavy tps (c1 / c2) | abort 率 write / balanced / read (c1) |
|---:|---|---|---|---|
| 1000 (境界参照) | 993,106.4 / 992,686.2 | 718,264.8 / 719,938.2 | 1,703,577.8 / 1,704,680.0 | 0.042344 / 0.058753 / 0.023749 |
| 1250 | 905,601.2 / 905,498.2 | 659,017.0 / 657,520.8 | 1,545,212.0 / 1,544,381.8 | 0.037662 / 0.051936 / 0.021324 |
| 2500 | 684,422.6 / 683,409.0 | 496,833.6 / 498,175.2 | 1,133,420.6 / 1,134,612.0 | 0.025764 / 0.035602 / 0.015179 |
| 5000 | 520,175.6 / 519,930.4 | 387,841.6 / 386,980.0 | 834,521.0 / 832,181.8 | 0.017357 / 0.023357 / 0.010631 |
| 9999 | 401,697.6 / 403,188.2 | 317,246.2 / 318,499.4 | 618,689.8 / 615,347.8 | 0.011435 / 0.014523 / 0.007335 |

(1768 / 3535 / 7070 µs の行と cohort 2 の abort 率は各稿 §2.3 にある。) 同じ格子で throughput は 1000 → 9999 µs で 3 workload とも
半分以下へ下がり、abort 率は下がり続ける。**abort 率が下がり続けることと、その帯で性能が大きく失われることは同時に成り立っている。**
倍増あたりの低下率の同時下限 `L` は 18 区間すべてで 0.27 以上 (述語の閾値 0.05 を大きく超える) で、両 cohort でそうである。[19, 20]

**言えること / 言えないこと。** 言えるのは、事前登録 §4.5 の固定表現「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに
飽和を観測しなかった」が、独立な 2 つの cohort のそれぞれについて成り立つ、までである。これは事前登録 §3 が反証可能な主張として
置いた「全 workload で登録述語を満たす飽和位置が存在する」の反証結果である。言えないのは「飽和しない」「飽和点が存在しない」
「再現されたので飽和しない」「2 cohort で有意」— cohort 1 の verdict を主として保持し、cohort 2 は再現欄に併記して合成せず、
統合 verdict・プール推定・またぐ有意水準は存在しない。2 cohort の数値の近さを再現精度として評価しない。9999 µs は符号化の上限で
あって物理的な限界ではなく、右側は測れない。901〜998 µs の帯は未測 (D2027 / D2044 項 14)、旧 consumer へ schema v2 を入力した
場合の判定も未測定である。機序 (なぜ abort 率がこの形で下がるか) は書かない。事前登録 §0 が開示するとおり、格子の位置と刻み幅・等価幅 5%・
変動係数の品質 gate・「表現域内で飽和しない」を正当な結末に含める選択は、いずれも探索走 (`t2418-explore`) の結果を見た後に選ばれたもので、
前向きに固定したのは本格 cohort に対する測定規則と判定規則である (cohort 2 では地位 (独立再現) と併記法も結果前に固定した)。
`[qL, qU]` は Bonferroni を適用した同時区間であり区間ごとの 95% 信頼区間ではなく、表 13 の平均は算術平均であって median ではない。[19, 20]

## 10. stock mocc の G2 signal — 非 certifying の観測 2 件

Silo 固定スコープの解除 (D2114) 後、mocc は第 2 例の準備段階にある。stock mocc (RWLOCK 版、hook branch 先端 `e9e477ca`。観測当時の
CCBench pin は `511c9538` で、pin はその後 `e9e477ca` ([T-2304]、2026-09-20 着地) を経て、本稿の採用時点では mocc の X/P 計装を含む C (`68106660`、
[T-2858]、2026-09-23 着地、D2236) へ前進している) の TRACE=1 観測専用 build で、verifier が G2 signal を出す条件を分けた観測が 2 件ある。**いずれも
非 certifying の観測記録であり、headline・certified 選択・floor・oracle・fitness の根拠にしない。性能値を含まない。**
「mocc は第 2 成功例」とは書かない。[21, 22]

**表 14　観測条件の分離 ([T-2779]、2026-09-18、4 block × 30 round × 3 arm = 360 走、全走 witness off)。** CP = Clopper–Pearson 両側 95%。

| arm | k/m | 検出率 | CP 95% 区間 | 主比較 (片側 Fisher、未調整) |
|---|---:|---:|---|---|
| 通常 (`e9-instr-nowit`) | 5/120 | 4.1667% | [1.3665%, 9.4559%] | — |
| 診断 patch (`e9-diag-nowit`) | 0/120 | 0% | [0%, 3.0273%] | 対 通常 p = 0.0299507441 |
| `BACK_OFF=1` (`e9-instr-nowit-bo1`) | 2/120 | 1.6667% | [0.2025%, 5.8909%] | 対 通常 p = 0.2230864755 |

**表 15　軽量 witness の 4 arm (2026-09-19、4 block × 15 round × 4 arm = 240 走)。**

| arm | k/m | 検出率 | CP 95% 区間 | 比較 (片側 Fisher、on < off、未調整) |
|---|---:|---:|---|---|
| 軽量 witness on、`BACK_OFF=0` | 0/60 | 0% | [0%, 5.963%] | 対 off p = 0.500 |
| off、`BACK_OFF=0` | 1/60 | 1.667% | [0.042%, 8.940%] | — |
| on、`BACK_OFF=1` | 0/60 | 0% | [0%, 5.963%] | 対 off p = 0.500 |
| off、`BACK_OFF=1` | 1/60 | 1.667% | [0.042%, 8.940%] | — |

G2 signal の走はいずれも `verdict: non-serializable`、`certified: false`、`total_cycles: 1`、anomaly は `G2`、長さ 2、2 辺とも `rw`、
`integrity.clean: true` で、規律 2 の即 reject 契約はそのまま働いている。表 14・15 の CP 区間と Fisher の p は独立・同率 Bernoulli を仮定した
参考値で、node 内相関・回転順・時間変動をモデル化していない。検出率は固定時間 (3 秒) の走あたりの率であり、同じ commit 数への曝露比較ではない
(on の曝露量は少ない)。表 14 の 4 block は別 node・別 binary・別時刻であり「同一条件の 120 反復」とは書けず (稿 §5 項 18)、表 15 の 4 block は
4 node で同時刻に走り block 内で 4 arm が順次実行された (稿 §3 項 8) — いずれも node 内相関・回転順・時間変動はモデル化していない。[21, 22]

**言えること / 言えないこと。** 言えるのは「stock mocc の G2 signal は witness を切った producer で再現し、診断 patch (2 変更を束ねた介入)
の arm では 0/120 で、固定条件で介入と検出率低下が整合する」「軽量 witness on では 0/60・0/60、off では 1/60・1/60 で、この標本・条件
では on/off の率差を検出しなかった (設計仮定下の検出力 0.105)」までである。言えないのは、根因の同定 (実装 / hook / verifier 仮定の
三分岐は識別できない)、`BACK_OFF=1` の抑制効果 (p = 0.2230864755、「低下を検出できない」まで)、witness の観測者効果の実証・除去、
そして「G2 が無い」— **0 件は不在証明ではなく、非有意は同等性証明ではない**。主比較 2 本の family 全体で有意とは判定しない。
mocc の certified 昇格・探索の解禁は本観測から導かれない (pin 前進は D2150 項 1 の承認の下で 2026-09-20 に main へ着地した ([T-2304]) が、
それは本観測の帰結ではなく、探索・軸採用は未解禁のままである — D2159)。上流向けには観測事実と限界の報告までで修正 PR は見送る
(D2148 項 13)。[21, 22, 24]

**pin C の後 (本稿の採用時点)。** pin C では mocc の X/P が証拠として存在し、同じ trace を mocc として検証すると clean・serializable・certified になるように
verifier の正負対が追随した (D2236)。検出期待表の mocc の行 (§6.3) の同 job の stock 対照 28 run はすべて certified だった。比較 harness には MOCC が
protocol 引数で差し込まれ、pin C で取った MOCC の認定較正 3 件 (records 1,000,000、silo と同値) の動作点で、系列 1 本の 5 slot (開始 stock・初期点 5 / 10 µs・
探索 1・endpoint) と block 対照 1 slot がすべて certified・品質 normal・anomaly 0 で通った (MOCC の slot だけ campaign pin を C にした、D2248)。**これは疎通の
生死確認であって比較ではなく、MOCC の性能比較は 0 件である。** pin 前進は探索・軸採用の解禁でも mocc の certified 系列の成立でもない。比較 harness の
silo の campaign pin は `511c9538` のまま動いていない。表 14・15 の観測は当時の pin の事実として残る (規律 7)。[24, 42, 43]

## 11. 考察：操作の拡張は支持されたが、生成器の優越は未実証である

結果が支持するのは、既存の設定空間を探索することと、実装が選べる操作を増やすことを分ける Izanagi の構成である。有限フラグ空間では
LLM 誘導が貪欲探索を上回らず、一部では探索コストが増えた (§1)。一方、静的 backoff という操作を追加した後の機械 sweep は、無 backoff
より高いスループットを持つ点を旧環境の 2 負荷で見つけ (§2)、正しい identity で測った現行環境の走行 (§3) と同一候補の 3 workload 測定
(§4)、A-1 の descriptive 出力 (§5) は、いずれも同じ向きの符号を示した。従って P2-4 は、対象実装の操作を拡張することの実現可能性を
支持する一事例になる。**ただし、符号の一致は記述的な照合であって再現判定ではなく、それらの走行は互いにプールできない。** その軸を
LLM だけが発見できたことや、生成器として LLM が必要だったことまでは示していない — 「LLM でなければできない」という形の必要性は
対照を取っても言えないと裁定されており (D1067)、条件付き優越を示す対照 (B-5) も未取得である。[1, 2, 3, 7, 9, 12]

性能の改善は負荷と対照に依存した。read-heavy の退行は旧環境 (−6.6%)、A-6 (−5.7841%)、同一候補 5 µs (−11.3787%)、A-1 attempt-0001
(対差平均 −576,749.77 tps) と attempt-0002 (同 −560,565.60 tps) のいずれでも負の向きであり、「待機を増やせば一律に速くなる」という解釈に反する。S-1a の不成立は「軸に効果が
ある」(S-1b、sort に対する +55.5〜+98.4%) と「最良の既知軸を超える」の隔たりを示す。このため、システムが返す stock や tie は、証拠が
改善を支持しない場合の有効な出力として扱う必要がある。ただし、比較値が未取得の場合や protocol が成立していない場合は、tie を判定した
ことにもならない。また、負荷ごとに異なる最良点 (10 / 5 / 2 µs) が観測された事実だけでは、workload descriptor を条件とする生成の因果的な
効果 (B-2) を示したことにならない。[2, 4, 7, 9, 11, 12, 26]

abort 率と throughput の同時変化は、競合の抑制と待機コストの釣合いという解釈に整合する。しかし abort 率の集約方法は実験ごとに異なり
(A-2 / A-6 と同一候補の測定は WAL の `leading_indicators` の cell あたり 1 点 — A-6 稿は代表 rep 1 点と記す、右 tail の表 13 は rep ごとの率の
5 反復算術平均、K2 は巡によって集約規則が違う)、
いずれも信頼区間を持たない記述的な先行指標であって、これだけから性能差を特定の機序へ帰属できない。待ち方 grid (§9.1) と右 tail (§9.2) が与えるのは記述的な会計と分類であり、
「abort 率が下がり続けても性能は失われる」という同時成立の観測までで、機序の同定ではない。既定の適応 backoff に関する観測は
CCBench の当該定数設定の範囲に限られ、適応制御一般の欠点には一般化できない (D1505 / D1506)。[2, 18, 19, 20]

本研究の結果を提示する中心は、トランザクション CC を対象に、対象実装の action vocabulary そのものを拡張し、各反復に正しさの判定を
入れることである (核 3 点、D1598)。正しさと性能を別 build・別 run に分ける規律 (規律 1) と、判定を性能値から独立に保つ規律 (規律 2)
は、実際に働いた例を持つ。旧 A-2 の走行 (§3.5) は、correctness の合格だけでは要求した構成が build されたことを保証しない例である —
要求した define が黙って無視されたまま正式 protocol が完走し (F707)、その訂正は WAL の `src_token` と追跡木の変更記録 (`tracked_clean` /
空 diff / 空 paths) の連言の照合に基づく (token 単独では木が HEAD どおりとは言えない)。新 attempt は pin + patch に束縛した identity を
cell ごとに要求した。性能と正しさの独立 (規律 1・2) は、同一候補の測定で退行した cell も certified であること (§4) と、性能値を一切含まない
検証相 (§6.1) と B-8 検証 (§6.2) に示される — S-1 の最終候補は旧環境・旧 pin の性能で既知軸最良を超えなかったが (§7)、同じ gate 構成を
当時の現行 pin (`e9e477ca`)・現行 patch の trace 有効 build で検証した B-8 (案 A、本走 = 独立 8 反復 × 3 workload・extime 10 s の 24 枠、判定集合 30 枠 = 本走 24 +
校正の完走 6) の 3 値判定は `pass` であり (規則の機械適用の出力であって研究の成功宣告ではない、D12)、両者は source bytes の違う別の段の
結果として並べるだけで互いを補わない。記録の追跡可能性はこれらの区別を確認する補助であるが、記録の整合性や説明文の
生成から、説明の忠実性、因果機序の同定、合成能力の高さを導くことはできない。provenance そのものを研究上の優越に数えない。[3, 6, 7, 10, 28]

還流について言えるのは、正しさゲートを毎反復回す loop が certified まで到達し (2026-09-10 の再評価、4 巡、pair の再投入)、実測の還流 3 回と
critic 診断の型付き還流 2 回が既存経路で成立し、4 巡目で初めて同じ job の stock 対照を伴って評価した、までである (§8.1)。診断が「届いた」ことと
「効いた」ことは別であり、統制の無い 1 回ずつの起動から因果は言えない。同 job の比 (2.366 / 2.493) は 1 配線の記述値である。
規律 3 が求める「なぜ壊れたか」の還流は、4 巡の評価とも anomaly 0 だったため 1 度も発火しておらず、B-4 の ablation は適格な赤 precursor
0 件のまま実施不可である (§8.2)。[15, 17, 41]

操作の拡張の方向では、関数単位の軸の小比較 (§7 末尾) が、固定テンプレートの 16 点のうち 3 点で同 job の静的 10 µs を 6〜7% 上回った。これは値の軸
(静的・適応 backoff の値空間) には無い次元 (lock 競合への応答) を持つ点の探索的な観察で、操作の拡張が値の最良点の先へ届きうることと整合する。
しかし 1 回・再測なし・多重選択の補正なしであり、16 点は人が固定したテンプレートの点で LLM が生成したものではない。**B-1 は不成立のままで、
この観察を既知最良の超越とも、LLM による合成の成果とも書かない** (再測は論文に書く前、D2243 項 1)。[38, 39, 40]

正しさゲートの費用も、実測で輪郭が見えた。B-5 本走の中断までの 12 job では非 LLM の計算の 95.0% が検証 (trace 取得 + verifier + 周辺処理) で、探索の
独立反復の試走でも評価 1 回の約 91% が検証だった。検証の trace 5 本を同じ node で同時に検査すると、判定を全件一致させたまま検査の wall が 0.24〜0.26 倍に
なった (同時検査の直後は load が上がるので、bench 前の静定待ちの延長と組でしか使えない)。検証の回数と規模は正しさゲートと評価の定義なので、費用の削減は
検査を弱めない形 (同時化・LLM 待ちを計算 node の外へ) に限って議論されている (規律 2)。**これは費用の観測であって性能の結果ではない。** [44, 45]

## 12. 未取得の比較と進行中の成果

本稿の採用時点 (local main `6d198ca8a`) で、次は取得されていない。

- **A-1 の充足 (但し書き 1)。** attempt-0001 と attempt-0002 はいずれも非認証 lane の descriptive 出力であり、「A-1 の値がある」とは
  書けない。attempt-0002 は 1 attempt 認可 (D2172 項 2) の下で exact な認可 record (D2178) 経由で投入され完走したが (entry 1755)、A-1 の充足・
  formal 化・attempt 間の再現性 (attempt-0001 稿の限定 L-A1S-4 の解除)・3 本目の認可は判定されていない。formal 化はユーザー手番である
  (D2044 項 8)。前稿の採用時点より後に A-1 に触れる着地は無い。[9, 12, 26]
- **別 boot での再取得 (A-5、但し書き 3)。** D1100 が要求する別 boot 成果物は無く、Pegasus で取っても充足にならない (D1525)。2 度の投入は
  測定前に止まった。[2, 12]
- **合成軸が既知軸最良を超える証拠 (B-1)。** S-1a で不成立。§3〜§6 の走行はこの比較ではない。関数単位の軸の小比較 (§7 末尾) は探索的・1 回・再測なし・
  多重選択の補正なしの観察で、B-1 の判定を変えない。[11, 12, 38, 40]
- **descriptor を条件にした合成の因果証拠 (B-2)。** 未実走・未取得。[12]
- **生成器の対照 (B-5 = 固定予算・同一編集面で、事前登録した非 LLM 生成器に対する条件付き優越を問う対照。D1067 により「必要性」の形では対照を取っても言えない)。**
  未取得。上限付き試走 (3 arm と block stock の 4 job、計 53 論理 session) は完走したが n = 1・主標本外で優劣は言わない (entry 1779)。本走は第 32 回 D2227 項 2 が
  総 wall 上限約 680.7 node 時間で認可し、block 1 stage 1 の 12 job が 2026-09-23 21:53 JST に投入された (Elapse 計 35.1 node 時間) が、その後で止まっている。
  LLM 親 4 本が同日 23:50 JST に週上限 (429) で同時に止まり、series job が提案待ちの時間切れで系列を閉じたため、report の規則のままでは **現行 cohort
  `b5-registered-v1` の 6 比較 (3 workload × 2 baseline) すべてが判定不能 (欠測)** であり、write-heavy の random 2 系列は系列開始 stock の品質欠測で、その比較は
  再開しても判定不能である (F1050)。ユーザーは規模に異議を示し、続行形は **ユーザー裁定待ちの 4 択** (v1 を stage 1 で閉じて開示し、LLM 待ちを計算 node の外へ出す実装と
  取得済み trace の同時検査を入れた新 cohort として登録し直す前提で、n = 12・3 workload / n = 9 / read-heavy を外す / 見送り) である。B-5 の発効 commit は main の祖先でない
  branch にあり、本走の候補値・throughput は本稿に無い。**判定不能は report の規則の出力で、性能の結果ではない。** [12, 44]
- **探索の独立反復の試走 (P3)。** 事前登録 v1 (D2231) を write-heavy だけで発効させ (D2245、18 job、見積り 42.4〜60.6 node 時間)、block 1 の 6 job (7.28 node 時間) で
  random・sweep・llm の 3 系列が欠測した (系列開始 stock の静定待ちの時間切れ、LLM 親の週上限)。2026-09-26 にユーザー指示で block 2・3 の投入を止め、費用を削る案を
  実測で比べた。正典の台帳は案 (a) LLM 待ちを node の外へ・(b) 検証の同時化・(c) 系列数などの縮小を「ユーザーの確認」を要する択として残しており、案 (b) の採用は
  ユーザーの委任を受けた親裁定として repo 外の記録にあるだけで、正典への記録と実装は本稿の採用時点で着地していない。**試走の結果 (手法間の比較・系列の分散) は無い。** [45]
- **8c 正式系列 (B-3)、リーク制御を完備した実走 (B-6)。** 未完走・未達。K2 の 4 巡と同 job の対照は B-6 の材料であって充足ではない (§8.1)。[12, 15, 41]
- **反例還流の on/off ablation (B-4)。** 適格な赤 precursor 0 件で実施不可。床値 w1 は完走したが集約・採用は未 (§8.2)。[17]
- **現行環境の判定下限の較正。** 取れているのは走行間ばらつきの下限 (between-run CV: rr5 0.9536% / rr50 0.7250% / rr95 0.2228%、
  cold-boot と温度ドリフトを含まない) と、配線下限 0.03 × stock 中央値で決まった official の floor 案 (rr20 35,817.945 / rr80 46,065.78 tps)
  である。この floor 案を候補充填した凍結 v2 g1 は、承認 A と active pointer X (AI 手番、D2180) により 2026-09-20 に批准され、批准 loader は
  成功した (worklog entry 1742)。ただし P3 の full launch validation は未達で、live の起動検査は段階 4 の binary admission policy の不一致で拒否されたまま
  (entry 1776 / 1787 / 1790、前稿の照合時点の記録) であり、旧系列の再開 (g1 の live launch を含む) は VLDB 向けの方針で論文の必須経路から外れた (D2212)。
  「判定下限を較正した」「科学的に十分な床」とは書かない (D2120 項 2)。official の rr20 / rr80 の値を A-2 / A-6 の 3 workload や B-4 の床値へ転用しない。[7, 23, 25]
- **クロスプロトコル (C-1)。** Silo 固定スコープは解除されたが、非 Silo の性能比較は 0 件である。pin C で mocc の X/P が証拠として存在するようになり (D2236)、
  比較 harness に MOCC が差し込まれて疎通の生死確認が通った (D2248) が、比較・探索・軸採用は行っていない (§10)。[21, 22, 24, 42, 43]
- **TPC-C。** 段 1 の silo の実 trace 1 本を verifier が直列化可能と判定し、pipeline の trace 検査段も受理した (§6.4) が、合成候補の TPC-C での認定・評価、TPC-C の
  性能測定、段 2 は無い。結合候補の受理方式 (D297 の header 差分) はユーザー裁定待ちである。[34, 35, 36]
- **未知条件への転移 (P4)。** 事前登録 (YCSB 版 D2223・TPC-C 版 D2228) と実行器・解析器 (D2241) は着地したが、測定は発効しておらず、留保 cell は 1 走もしていない。
  実行器の錨の生死確認では、検証に CCBench の source root を渡さないと証明面が unavailable になり certified に届かない欠陥が見つかり、直した後に certified に届いた
  (F649 の再発)。[46]
- **再現パッケージと図。** 生成器のある 17 図を計測機の外で描き直し、17 図とも値の差 0・PNG は bytes まで一致した (node 時間 0、D2247) が、これは生成器と保存入力からの
  再生成であって測定の再実行 (R2) ではない。主要 20 図の再実行計画 (R2 を推奨する 9 図、図 1 本で投入前の確認が要る fig10 の 3.40 node 時間ほか) は置かれたが、R2 は
  走っていない。[47, 48]
- **pin 前進と既存の測定の関係。** 本稿の現行環境の測定のうち §3〜§5、§6.1、§9 はいずれも pin `511c9538` の下の値、§6.2 の B-8 検証と §6.3 の silo の行、§7 末尾の
  小比較は pin `e9e477ca` の下、§6.3 の mocc の行と §10 の MOCC の疎通は pin C の下の記録である (K2 の 4 巡と pair は driver の campaign pin `511c9538` を checkout)。
  pin は本稿の採用時点で C へ前進しているが、それは記録を無効にしない (規律 7)。旧系列を新 pin の main へ移すには系列ごとの整合が要り、本稿はその移行を扱わない。[24, 28, 42]

同じ編集面・固定予算で非 LLM 生成器と比べる新しい比較は、P2-5 や S-2 で代替しない。これらの空欄を推定値や成功例で埋めず、得られた
条件付きの観測と、未実証の生成・還流効果を分けて報告する。B-7 の限定付き充足 (§4) は報告要件についてのものであり、これらの空欄を
埋めるものではない。種を変えた長時間実行による最終候補の検証 (B-8) は §6.2 のとおりこの一覧に含めない — 発効した事前登録 v1 の下、
案 A に対する本走 (独立 8 反復 × 3 workload・extime 10 s の 24 枠) と校正の完走 6 枠からなる判定集合 30 枠のすべてで anomaly 0、3 値判定は
`pass` だった (規則の機械適用の出力であって研究の成功宣告ではない、D12)。ただしそれは最終候補の正しさ側の検証であり、上の空欄
(性能・生成・還流の比較) を埋めない。検出期待表 (§6.3) と TPC-C 段 1 の判定 (§6.4) も正しさ側の記録で、上の空欄を埋めない。
本稿の完成は、これらの実験や Phase 3 全体の完了を意味しない。

## 出所 (執筆者向け)

数値の権威は各 results 稿の表とその §「一次資料」が指す権威 bytes にあり、本稿はそれを転記した。以下の path は原則 repo root 相対。
ただし `results/…` は `docs/paper-story/results/…`、`figures/…` は `docs/paper-story/figures/…` の短縮である。

1. **P2-5:** `output/campaigns/p2-5-summary.json` の `rows`、`recalibration_2026_07_02`、`correction_2026_07_03` (2026-09-20 に
   再確認、前稿から変化なし)。元の誘導試行 WAL は削除済みで、凍結した試行コスト・軌跡と再生側の記録が残る。
   専用 critic は `.claude/agents/critic-experiment.md`。
2. **P2-4 (旧環境 sweep):** `docs/paper-story/results/2026-09-20-p24-static-backoff-sweep-linux-baremetal.md` (§2.1 の 3 値と未丸め値、
   §2.2 の 8 genome、§2.3 の fig2b provenance、§2.4 の `verify_done`、§3 限定 15 件)。campaign は write-heavy `493813a7`、
   balanced `484c663e`、read-heavy `610004b9`。profile と参考値は同稿が引く A-3 insight `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`。
   図は `docs/paper-story/figures/fig2b_backoff_sweep_3workload.*`。
3. **A-2 新 attempt:** `docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md` (§1 の `src_token`、§2.1 の表、§2.3 の条件、
   §3 の限定)。権威 bytes は `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`。図は
   `figures/fig6_a2_certification_observed_positive.*`。
4. **A-6:** `docs/paper-story/results/2026-09-18-a6-certification-reject.md` (§2.1 の表と派生値の注記、§2.2 の正しさ、§3.1 の B-10 との照合、
   §4 の限定 12 件)。権威 bytes は `output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json`。図は
   `figures/fig11_a6_certification_reject.*` (`figures/README.md` の fig11 節)。
5. **[T-1998]:** `docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md` (§2.1 の consumer 判定、§2.2 の生標本、
   §2.3 の正しさ、§3 の限定 20 件)。事前登録は `docs/t1998-balanced-stock-inline-preregistration.md` v1。
6. **旧 A-2 の訂正:** `docs/paper-story/results/2026-09-07-a2-certification-reject.md` (§1 の WAL field、§3 の表 1、§4 の限定、§5 の図 5 の扱い)。
   図 7 は `figures/fig7_a2_builtin_backoff_onoff_reject.*`。
7. **同一候補 fixed 5 µs:** `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` (§0.4 主判定文、§2.1 の主表、
   §2.3 の abort 率、§2.4 の正しさ、§3 の併記、§4 の限定 14 件)。権威 bytes は同稿 §5.1。床値は D1639 の between-run CV。図は
   `figures/fig10_b7_fixed5_three_workload_regression.*`。3 走行の併記は `results/2026-09-16-b7-three-run-materials.md`
   (4 対比較・8 arm、限定 20 件) と `results/2026-09-14-b7-all-workload-regression.md` (2 attempt・6 cell)。
8. **B-7 の限定付き充足:** D2174 項 3、論文ストーリー 2026-09-20 第 2 版 (`docs/paper-story/2026-09-20b.md`) §6 (前版の stale 注記を本文に
   吸収)、`figures/README.md` の fig10 節の追補、`output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md`。
9. **A-1 attempt-0001:** `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` (§0.4 主判定文、§2.1 の
   `statistics`、§2.4 の正しさ、§3 の限定 L-A1S-1〜20)。権威 bytes は公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/result.json`。
   図は `figures/fig9_a1_balanced5_sized_attempt1.*`。attempt-0002 の gate 拒否は `output/insights/2026-09-19/a1-sized-attempt2/README.md` と D2156、
   投入経路の裁定と実装は D2172 項 2 / D2178 と worklog entry 1736 (`docs/archive/worklog-phase3-0920-1736.md`)。attempt-0002 の完走と値は出所 26。
10. **検証相:** `docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md` (§1.1 の identity、§2 の規則、§3.1〜§3.3 の校正・本走・判定、
    §4 の限定 9 件)。記録は `output/insights/2026-09-20/verify-phase-adopted-backoff/README.md`。裁定は D2160。
11. **S-1a:** `docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md` (§0 主判定文、§2.1 の 9 対、§2.2 の 12 cell、§2.5 の正しさ、
    §2.6 の Holm 族 4、§3.1 の S-1b、§4 の限定 19 件)。凍結 report は `output/reports/s1_direct_comparison/report.json`、族 4 の最終報告は
    `output/reports/s_prime_final_report.md`。図は `figures/fig4_s1a_9pair_direct_comparison.*`。
12. **位置づけと裁定:** 本稿 (2026-09-26 版) の照合先は `docs/paper-story/2026-09-26.md` §6 / §7 / §8。以下は前稿から継承した照合先:
    `docs/paper-story/2026-09-20b.md` (2026-09-20 第 2 版) §3 / §6 / §8、`docs/paper-story/README.md` の stale 注記
    (2026-09-21 版の稿が見た 5 件。B-8 の記述は前稿の採用時点で同 README が積んでいた stale 注記 3 に揃えた)、
    `docs/decisions.md` の D12 / D20 / D1067 / D1100 / D1409 / D1525 / D1598 / D1993 / D2044 / D2120 / D2148 / D2156 / D2157 / D2160 / D2162 /
    D2172 / D2174 / D2175 / D2178 / D2186 / D2187 / D2190 / D2194 / D2196 / D2200 / D2201 / D2202 / D2205。裁定を実装・実走済みの証拠にはしない。
    B-5 の試走の完走は worklog entry 1779 (`docs/archive/` の該当 file) が実施記録。
13. **S-2 / S-3:** `output/s6-rounds/tally.json` (`eligible_counts` main 20 / c4 17 / c5 20、`nominal_p_s2_main_vs_c4` 0.11538461538461539、
    `nominal_p_s3_main_vs_c5` 1.0。2026-09-20 に再確認)、確定文言 `output/insights/2026-07-13_s6-report-language.md`。
14. **K2 再評価 (2026-09-10):** `output/insights/2026-09-10_t2581-k2-pin/README.md` と、その参照先の campaign WAL
    (`verify_done` と `commit`。source commit `55d0f2399…`、request `990027.nqsv`)。前稿から変化なし。
15. **K2 手動 loop 3 巡:** `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` (§0.1 の巡と還流の定義、§2.1 の表、§2.2 の巡ごとの
    記録、§2.3 の「届いた / 効いた」、§2.4 の規律 6、§3 の限定 21 件)。図は `figures/fig12_k2_manual_loop_dataflow.*`。
    **provenance の注記 (執筆者向け):** 3 巡の campaign 原本 (submit-tree の worktree 4 本) は 2026-09-20 19:25 JST の撤去事故 (F1034) で失われた。
    3 巡の原本の sha256 と bytes 数は消失前に 3 巡稿 §5.1 が記録している。現在確認できる範囲 ([T-2815]、worklog entry 1764、
    `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` §0〜§1): round 3 の `loop_state.json` と round 2 / 3 の
    `agent_outputs.jsonl` は、repo 派生物 (`materials/run-summary.json`、`layer3_report.json`) から記録 sha256 と byte 一致する形で再構成できる。
    round 2 の WAL は byte 一致する写し (t2746 job dir の scratch) が残り、round 3 の WAL は材料レポートの record と canonical 内容の同一まで確認できる
    (bytes は戻らない)。round 1 の WAL は原本 bytes を再検算できず、転記値と job 出力による。材料レポート自体は repo に残存する (再構成の入力側であって
    対象ではない)。本稿は表 11 の値を稿からの転記として保ち、既存の値・判定を変えず、再構成の範囲を超える主張はしない。
16. **同 job stock 対照:** D2172 項 3、D2183、worklog entry 1746 ([T-2795] の実装記録)、初投入の不成立は D2187 と worklog entry 1754
    (`output/insights/2026-09-20/t2795-k2-pair-attempt/README.md`、job `13339.nqsv`、候補 10 の再評価 811,956 tps は当時の判定として保持し pair・
    改善の証拠に昇格させない)。driver の修復は D2205 と worklog entry 1795 (`output/insights/2026-09-21/t2795-pair-repair/README.md` §0 の
    「主張しない」= 実機で pair が成立したとは言わない、pair 再投入と 4 巡目は未投入 — 同 insight の時点の記述。その後の再投入と 4 巡目の成立は出所 41)。
17. **B-4:** `docs/phase3-b4-reflux-ablation-preregistration.md` §2、D1936 項 8〜10、D1986 項 4、D2016。床値 w1 は
    `output/insights/2026-09-19/t2288-floor-pair-w1/README.md`。登録は未取得効果の定義に用い、観測結果として引用していない。
18. **B-10 待ち方 grid:** `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` (§0.2 の判定しないこと、§2.1 の完全性、§2.2 の
    3 族 Holm、§2.3 の対差、§2.4 の 36 cell、§2.5 の参考幅、§3 の限定 19 件)。裁定は D1678。図は `figures/fig13_b10_waiting_grid_forest.*`
    (`figures/README.md` の fig13 節、worklog entry 1763。稿を `caption_source` として束縛する結果図)。
19. **B-10 右 tail cohort 1:** `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` (§2.1 の verdict、§2.2 の 18 区間、
    §2.3 の費用、§3 の限定 15 件)。図は `figures/fig8_b10_static_tail_not_observed.*`。
20. **B-10 右 tail cohort 2:** `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md` (§2.1、§2.3、§2.6 の再現欄、§3 の限定)。
    裁定は D2157。図は `figures/fig8b_b10_static_tail_cohort2.*`。
21. **mocc G2 の観測条件:** `docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md` (§0.1 の限定 10 項、§3.1〜§3.4 の結果、
    §5 の限定 11〜18)。
22. **mocc 軽量 witness 4 arm:** `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md` (§2.1〜§2.4 の結果、§3 の限定 11 件)。
23. **床値・official floor 案:** between-run CV は D1639 と `output/insights/2026-09-19/t2288-floor-pair-w1/README.md` §「床値」の全桁
    (rr5 `0.009536033056996148`、rr50 `0.00725042525457718`、rr95 `0.0022283754708938273`)、official floor 案は
    `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` (rr20 35,817.945 / rr80 46,065.78) と D2120 項 2。
24. **ccbench pin 前進:** `output/insights/2026-09-20/t2304-pin-advance/README.md` ([T-2304]、gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を
    同一 commit で `511c9538` → `e9e477ca` へ、main `482f19b88` に着地)、worklog entry 1747、D2184 (pin 前進の波及の射程)。
25. **凍結 v2 g1 の批准と launch validation の未達:** worklog entry 1742 ([T-2724]、`docs/worklog.md`)、
    `output/insights/2026-09-20/t2724-ax-delegated/README.md`、D2180。不整合 2 件の整合は D2196 と entry 1776 ([T-2810]、
    `output/insights/2026-09-20/t2810-g1-launch-validation/README.md`)、live の段階 4 の拒否は entry 1776 / 1787 ([T-2824]、
    `output/insights/2026-09-21/t2824-g1-candidate-removal/README.md` §3) / 1790 ([T-2812]、`output/insights/2026-09-21/t2812-old-series-realignment/README.md`)、
    設計択一は D2201。worklog entry は `docs/archive/` の該当 file。検証相の未完走原因の同定は worklog entry 1744 と
    `output/insights/2026-09-20/verifier-capacity/README.md` §2・§4 (D2181)。
26. **A-1 attempt-0002:** `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` (§0.4 主判定文、§1.4 の認可 record・
    投入・受領証、§1.5 の比較可能条件、§2.1 の `statistics`、§2.3 の arm ごとの記述、§2.4 の正しさ、§2.5 の時系列、§2.7 の並記表、§3 の限定
    L-A1S2-1〜13)。権威 bytes は公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/result.json`。記録は
    `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md` と worklog entry 1755 ([T-2792])。裁定は D2172 項 2、gate は D2178。
    表 7b は同稿 §2.7 の逐語で、attempt-0001 側の値は公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/result.json` (同稿が転記) による。
27. **B-8 の試走認可・発効前試走・発効と実施:** D2186 (第 26 回 /rulings、対象・定義・上限付き試走の認可、発効と本走は試走後に再提示。
    項 1 (2) = 仕分け (2) を「独立 process の自己シード」へ改める限定)、D2190 (runner v5、案 A の identity `g_rl` `b0f95b21…` / `g_rt` `a0219ce0…`)、
    worklog entry 1766 ([T-2807])、`output/insights/2026-09-20/t2807-b8-prerun/README.md`。事前登録 v1 は D2175。発効と本走の承認は D2194 項 1
    (認可の出所)、発効・校正・本走・判定の実施記録は worklog entry 1791 と `output/insights/2026-09-21/t2807-b8-effective/README.md`
    (§1 発効、§2 仕分け (2) の限定、§3〜§5 校正・本走・判定、§6 限定)、実施の形は D2202。
28. **B-8 の結果:** `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md` (§1.1 の対象と identity、§1.2 の固定条件、§2 の規則、
    §3.1 の校正、§3.2 の本走、§3.3 の判定、§3.4 の費用、§4 の限定 11 件)。規則の正本は事前登録 v1
    `docs/b8-final-candidate-longrun-verify-preregistration.md` (sha256 `6ccb18c7…`、発効 commit `624c84986`)、発効束 JSON は
    `output/insights/2026-09-21/t2807-b8-effective/verbatim/b8-effective-bundle.json` (sha256 `059536a7…`)。機械集計 `summary-final.json`
    (sha256 `ee94bdf2…`) と保全 trace は repo 外の job dir にある (同稿 §5)。

以下は本稿 (2026-09-26 版) で足した出所である。位置づけと状態語の照合先は論文ストーリー 2026-09-26 版 (`docs/paper-story/2026-09-26.md`) §0・§6・§7・§8。
worklog entry 1847〜1862 は `docs/archive/` の該当 file、1863〜1867 は `docs/worklog.md` にある。

29. **検出期待表の設計と既存 patch・コーパス:** `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` (§2 判定の範囲、§4 期待表)、
    `output/insights/2026-09-23/t2847-patch-verify/README.md` (既存 silo 壊し patch 10 本・13 run)、`output/insights/2026-09-23/t2847-corpus-gaps/README.md`。
30. **silo の新規変異と trigger-misattr:** `output/insights/2026-09-23/t2847-mutation-run/README.md`、D2239 (発火診断と五分類)、worklog entry 1854。
31. **sort-nonswo (V07):** `output/insights/2026-09-23/t2847-sort-nonswo/README.md`、worklog entry 1855。
32. **mocc の 34 cell:** `output/insights/2026-09-26/t2847-mocc-run/README.md` (§1 結論、§3 検出表、§9 限界)、D2246 (五分類の外の状態)、worklog entry 1864。
33. **verifier の容量:** `output/insights/2026-09-23/t2847-verifier-capacity/README.md` §1。
34. **TPC-C 段 1 の verifier と存在契約:** 設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md`、trace v3 の読み D2224
    (`output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md`)、silo の emitter D2225 (`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md`)、
    存在履歴の検査 D2232 (`output/insights/2026-09-23/t2854-v3-existence/README.md`、worklog entry 1843)。段の分割は D2219 項 2。
35. **pipeline の TPC-C 段 1 受理:** D2238、`output/insights/2026-09-23/t2854-unit5-v3-wiring/README.md`、worklog entry 1852。
36. **結合候補 (単位 11):** D2244、`output/insights/2026-09-26/t2854-unit11-combined/README.md` (§5 の 4 択)、worklog entry 1862。
37. **関数単位の軸と段階 C:** D2212 項 3、D2214、D2226、`output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md`。
38. **段階 D:** D2234、`output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md`、worklog entry 1846。
39. **既知最良との小比較:** D2235 項 7 (択 (b))、D2240 (決定 1〜5 と限定)、`output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md`
    (§0 要約、§3.2 参照、§3.3 IR 16 点、§4 限定。点 ID・比の一覧は同 insight にだけ置く — 手順書 §3-D の firewall)、worklog entry 1856。
40. **段階 E への裁定:** D2243 項 1 (worklog entry 1860)。
41. **K2 の pair の再投入と 4 巡目:** `docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md` (冒頭の成立範囲と限定 1〜7、§2.1 の 4 巡の表、§2.3 の同 job の表、
    §2.6 の材料レポート、§3 の限定)、D2211 項 1、worklog entry 1823・1832、`output/insights/2026-09-23/t2860-k2-round4-reflux/README.md`。
42. **ccbench pin の C への前進:** `output/insights/2026-09-23/t2858-mocc-xp-pin-advance/README.md`、D2236、worklog entry 1850。
43. **比較 harness への MOCC の差し込み:** D2248、`output/insights/2026-09-26/t2849-mocc-insertion/README.md` (§0 要約)、worklog entry 1867、F1051。
44. **B-5 本走の中断と判定不能、費用:** D2227 項 2 (認可)、worklog entry 1866、`output/insights/2026-09-26/t2797-b5-cost-options/README.md` (§1 要約、§2 実測、§3 判定不能、§7 の 4 択)、
    F1050、D2243 の索引外。候補値と throughput は同 insight に載っていない (事前登録 §8)。
45. **探索の独立反復の試走:** 事前登録 `docs/search-repetition-trial-preregistration.md` (D2231)、発効 D2245、worklog entry 1863 (次の一手の [T-2850] を含む)、
    `output/insights/2026-09-26/t2850-trial-pause-cost-options/README.md` (§1 欠測の原因、§2 評価 1 回の内訳、§3 同時検査、§4 案、§5 限定)。
46. **未知条件への転移:** `docs/unseen-condition-transfer-preregistration.md` (D2223)、`docs/tpcc-unseen-condition-transfer-preregistration.md` (D2228)、実行器と解析器 D2241、
    `output/insights/2026-09-26/t2851-transfer-runner/README.md`、worklog entry 1857。
47. **17 図の描き直しと保全口の inventory:** D2247、`output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md` (§2)、worklog entry 1865。
48. **主要図の再実行計画:** `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md`、worklog entry 1848。
