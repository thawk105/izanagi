# P2-4 利得値の正典化 — 論文 §8 A-3 の決着 (read-heavy と図の誤記を含む)

authority: none

default_effect: no-state-change

## 結論

P2-4 (silo 静的 backoff 合成) の旧環境における論文採用値は、**同一 sweep 内の no-backoff control**
(`BACK_OFF=0`, `BACKOFF_FIXED=-1`) を分母として、次の 3 件に固定する。

| workload | rratio | 最良の静的 backoff | 論文値 |
|---|---:|---|---:|
| write-heavy | 5 | fixed 10us | **+38.3%** |
| balanced | 50 | fixed 5us | **+11.3%** |
| read-heavy | 95 | fixed 2us | **-6.6%** |

`backoff_profile_t48_skew0p9_rr5.json` から得る **+38.5%** は、別 CCBench commit・
`BACKOFF_NOINLINE=1`・`perf record`・3 反復の**機序診断 cell** である。D20 が
「perf 下 tps は headline 非使用」と定めているため headline に採らない。
**採らない理由は D20 の利用方針であって、値の大きさが違うと実証したからではない** (下記)。

本 report は既存 tracked 成果物の再計算と条件照合だけであり、新規性能計測も
correctness / certification の更新も行っていない。

## 本 report と 2026-08-24 report の関係

`output/insights/2026-08-24_paper-story-a3-evidence-integration/README.md`
(sha256 `12e93572a2aa4f5943f4923d13ba43c89b59a956740a0edba9039bbc71961ac9`) が
write-heavy と balanced について同じ結論を既に出している。本 report との関係は次のとおり。

- **重なるセル (write-heavy / balanced / profile / repro) は独立再導出で一致した。**
  08-24 report を読む前に一次資料 (JSON / WAL / campaign.lock / driver source) から
  条件と値を導出し、結果が一致することを確認した。source ledger の SHA-256 も
  5 件すべて byte 一致を確認した。**「全項目一致」ではない** — 08-24 report の結論は
  write-heavy と balanced の 2 件だけを固定しており、条件表にも read-heavy row が無い。
- **本 report は 08-24 report の successor (addendum) であって、欠落の修理ではない。**
  08-24 report は A-3 が名指ししていた 2 値衝突 (+38.5% 対 +38.3%/+11.3%) へ意図的に scope を
  絞っており、同 report の「欠損と後続測定」節は「必要な新規測定 cell はなし」と結論している。
  read-heavy を含む 3 workload 版は、その結論を保ったまま範囲を広げたものである。
- **本 report が足したもの** は (1) read-heavy セル、(2) read-heavy の正典 campaign の一意性、
  (3) 論文図 `fig2_backoff_mechanism.png` の baseline 誤記、(4) +38.5% を採らない理由の精密化、
  (5) P2-2 stock 最良分母の read-heavy counterpart (-7.1%)。

08-24 report は編集していない。凍結済みの着地物として参照する。

## 論文図 `fig2_backoff_mechanism.png` の baseline 誤記

`docs/paper-story/figures/fig2_backoff_mechanism.png` の左パネルは、**図の中で**
横破線に `stock adaptive backoff (Cicada-type hill-climb)` というラベルを持ち、
パネル見出しは `Synthesized static backoff beats stock adaptive`、注記は `+38% at 10 us` である。

- この破線の値は profile JSON の `is_none: true` 行、すなわち **無 backoff** の 1,867,747 tps である。
- **図の中の決定的な自己矛盾:** 赤い曲線の x=0 の点 (`BACK_OFF=0` = 無 backoff) と、
  「stock adaptive」と書かれた破線が**同じ高さにある**。同一の値に 2 つの異なるラベルが付いている。
- write-heavy の stock 適応 backoff の実測は **1,052,528 tps** であり
  (`backoff-sweep-write-heavy_report.md` の参照節、WAL の variant `602b4ce9c788`、
  `output/s1-freeze/measurement_freeze.json` の `reference_fitness_tps` とも一致)、
  この図の縦軸下限 (約 1.78M) に入らない。適応を分母にすれば利得は +147.4% であって +38% ではない。
- 図が描いている系列は profile (perf record 下、1.87→2.59M) であり、headline 適格な
  sweep 系列 (1.88→2.60M) ではない。2026-07-10 版のキャプションが
  `backoff_profile_t48_skew0p9_rr5.json` を出所と自己申告している。
- 誤記は 2026-07-10 版 (図の初回収録 `ff3268f8`、監査修正 `3940bbe4`) から入り、
  2026-08-23 版が引き継いでいる。**図の生成器は tracked に存在しない**
  (repo 全件検索で fig2 への参照は paper-story の 2 つの md だけ)。

**「stock」という語そのものは誤記と断じない。** D18 は `BACK_OFF=0` を指して
「stock の `BACK_OFF=0` が既に最適だった」と書いており、repo の語彙では `BACK_OFF=0` を
stock 最良と呼ぶ用法が実在する。曖昧なだけである。**誤りなのは `adaptive` / `適応` と
明記した箇所**、すなわち図中ラベル・パネル見出し・2026-08-23 版のキャプション
「stock の適応 backoff を +38% 上回る」である。本文では
「no-backoff control (`BACK_OFF=0`)」と書けば曖昧さが消える。

**本 wave では図を変更しない。** 同 PNG は複数の凍結スナップショット (2026-07-10 / 2026-08-23) が
同じ path で共有する着地物であり、上書きは過去版の遡及改変になる。tracked な生成器も無いため、
今この場で描き直すと再現不能な図をもう 1 枚増やすだけになる。本 report を erratum とし、
再作成 (sweep 系列で描き直すか、profile 系列のまま `no-backoff control` と正しく label するかの
選択を含む) を新規 T 項目として起票する。論文執筆では、この図を使う限り
**キャプションで baseline を明示的に訂正する**か、図を使わない。

## read-heavy の正典 campaign — 3 つのうち 1 つだけが sweep 曲線を持つ

`output/campaigns/` には read-heavy の backoff sweep campaign が 3 つある。

| campaign | CCBench commit (宣言) | screening | 終端 | reports/ | 判定 |
|---|---|---|---|---|---|
| `…read-heavy-sweep-610004b9` | `6656e93` | 無 | 8 variant すべてが `build_done`→`verify_done`→`bench_done`→`commit` | 有 | **正典** |
| `…read-heavy-sweep-6f169f90` | `d706650` | 有 | `abort` / `reason: screen-slower-than-floor` (fixed100 で打ち切り) | 無 | screening の positive control |
| `…read-heavy-sweep-8ff95955` | `dff0f1e` | 有 | `abort` / `reason: build-error` | 無 | build 失敗 |

610004b9 だけが write-heavy / balanced の sweep と同じ CCBench commit (`6656e93`) を宣言し、
`campaign.lock#search_config` に `screening` field を持たず、6 点の静的 backoff 曲線と
材料レポートを持つ。他の 2 件は**そもそも headline 候補ではない** —
6f169f90 は bench-first screening 機構の positive control として
`orchestrator/tests/test_bench_first_real_wal.py` が実 WAL として参照しており、
8ff95955 は build error で終わっている (宣言 `dff0f1e` に対し WAL 記録の submodule HEAD は `d706650`)。
よって -6.6% の一次資料は 610004b9 に一意に定まる。

この選択は `output/reports/layer3_paper_evidence_dossier.md` の 3.2 節が独立に行っており
(「`campaign.lock#search_config` に `screening` field が無いことで screening 無効と確認できる」)、
同節は 3 workload の値を**正しい baseline ラベル (「無 backoff」)** で持っている。
誤記は paper-story 側に局在している。

## 条件表 — workload と treatment

| cell | 再計算値 | baseline | variant | workload | records | threads | skew | rratio | rmw |
|---|---:|---|---|---|---:|---:|---:|---:|---:|
| sweep-write | +38.3% | BO=0, FIXED=-1, NI=0 | BO=1, FIXED=10, NI=0 | write-heavy | 1,000,000 | 48 | 0.9 | 5 | 0 |
| sweep-balanced | +11.3% | BO=0, FIXED=-1, NI=0 | BO=1, FIXED=5, NI=0 | balanced | 1,000,000 | 48 | 0.9 | 50 | 0 |
| sweep-read | -6.6% | BO=0, FIXED=-1, NI=0 | BO=1, FIXED=2, NI=0 | read-heavy | 1,000,000 | 48 | 0.9 | 95 | 0 |
| profile-write | +38.5% | BO=0, FIXED=-1, NI=1 | BO=1, FIXED=10, NI=1 | write-heavy | 1,000,000 | 48 | 0.9 | 5 | 0 |

略号は BO=`BACK_OFF`、FIXED=`BACKOFF_FIXED`、NI=`BACKOFF_NOINLINE`。NI=0 は configure command に
明示されない既定 inline build であり、profile の NI=1 と区別する。全 cell で
`-extime=3`、`-clocks_per_us=1800`、`numactl --interleave=all`、env tag `linux-baremetal`、
`CCBENCH_TRACE=0` は共通。

## 条件表 — build、計装、反復、時期

| cell | CCBench commit | build / instrumentation | reps | aggregate | execution order | measurement time (JST) |
|---|---|---|---:|---|---|---|
| sweep-write | `6656e931…` | Release; gcc/g++-13; TRACE=0; `perf stat` | 5 | 各側 TPS median の比 | no-backoff→適応→2→5→10→25→50→100us | 2026-06-22 22:58:59–23:09:04 |
| sweep-balanced | `6656e931…` | Release; gcc/g++-13; TRACE=0; `perf stat` | 5 | 各側 TPS median の比 | no-backoff→適応→2→5→10→25→50→100us | 2026-06-22 23:09:04–23:14:19 |
| sweep-read | `6656e931…` | Release; gcc/g++-13; TRACE=0; `perf stat` | 5 | 各側 TPS median の比 | no-backoff→適応→2→5→10→25→50→100us | 2026-06-28 14:34:11–14:39:04 |
| profile-write | `dff0f1ef…` | TRACE=0; NI=1; `perf record -e cycles,instructions` | 3 | 各側 TPS median の比 | none→2→5→10→25→50→100us | absent |

**日付の扱い。** `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md` は表題と本文で
`日付: 2026-06-22` を名乗り、read-heavy の C5 (`最小 2us で -6.6%`) を含む。しかし同 file の
初回 tracked commit は `71530e18` = 2026-06-28 14:55:35 JST であり、その初回版に既に C5 がある。
read-heavy の測定そのものは WAL の epoch で 2026-06-28 14:34:11–14:39:04、材料レポートの初回収録は
`2c59dc3d` = 同日 14:39:38 である。**insight の表題日を測定日として使わない。**

profile JSON は measurement timestamp、compiler、binary digest を持たない。
profile の CCBench commit は artifact 自身の field ではなく、同 artifact を収録した repo commit
`b97ee915…` の木で `orchestrator/campaign/p2_2.py` の `CCBENCH_COMMIT` を読み、その tree の
pin と gitlink がともに `dff0f1e` であることから束縛した。これは history から導いた強い推論であって
artifact の自己申告ではない。sweep 側は `campaign.lock` が `ccbench_commit` を直接持つ。

## 再計算

全 cell で式は `100 * (variant_median / baseline_median - 1)`、表示は小数 1 桁への四捨五入である。

| cell | baseline median TPS | variant median TPS | 未丸め値 | 表示 |
|---|---:|---:|---:|---:|
| sweep-write | 1,882,125 | 2,603,521 | 38.328803879% | +38.3% |
| sweep-balanced | 2,791,760 | 3,106,342 | 11.268232226% | +11.3% |
| sweep-read | 8,450,806 | 7,889,420 | -6.642987663% | -6.6% |
| profile-write | 1,867,747 | 2,586,112 | 38.461579646% | +38.5% |

## +38.5% と +38.3% はなぜ別の値なのか — 出自の差と、大きさの差を分けて書く

**出自 (provenance) は 4 点で食い違う。** profile-write と sweep-write は workload 署名
(records / threads / skew / rratio / rmw / extime / clocks_per_us) が完全に一致するが、

1. **CCBench source revision** — sweep `6656e9319566e602113edf46588de9a612d166a1`、
   profile `dff0f1ef2a4b84746f6463839e85b24301f4b16d`。差分は 1 commit
   (`Fix ODR violation: build ccbench_common with the universal definitions`)。
2. **診断計装** — profile は baseline 側を含む全 genome に `BACKOFF_NOINLINE=1` を付ける。
3. **計測 harness** — sweep は `perf stat` (カウンタ集計)、profile は `perf record` (サンプリング)。
4. **反復数** — sweep 5 反復、profile 3 反復。

**しかし、この 4 点が利得の大きさを変えたという実証は無い。** 正直に分けて書く。

- ODR fix が直しているのは `#if ADD_ANALYSIS` 下で `Result` の layout が変わる件であり、
  sweep も profile も `CCBENCH_ADD_ANALYSIS` を設定していない (どちらの configure command にも
  現れない)。上流 commit `dff0f1ef` の message 自身が
  **「default (ADD_ANALYSIS=0) and Release -Werror builds are unaffected」**と明記している。
  よって source revision の差は**同一性の差**として real だが、この cell (AA=0) の throughput を
  変えたという一次証拠は無く、むしろ上流が不変と宣言している。
- noinline 計装単体の観測者効果は D20 が実測済みで、
  `noinline fix10 = 2,623,221 vs stock 2,603,521 = +0.76%`、between-run floor 3.0% の内側である。
- profile は sweep に対し baseline -0.764%、fix10 -0.669% と**同方向に**動いており、
  利得の差は 0.133 パーセントポイントに留まる。これは測定分解能の内側である。

したがって次のように書く。**両者は同じ公称 contrast の別 realization であり、
効果量は実測分解能の内側で整合する。それでも profile の TPS を headline に採らないのは、
D20 が「perf 下 tps は sampling overhead 込みで headline 非使用、絶対値は stock build の
committed fitness」と定めているからである。** 0.133 パーセントポイントの近さを
「同じ測定の丸め違い」の根拠にもしないし、逆に「別 regime だから値が違う」の根拠にもしない。

D20 の同じ規則を一次資料 2 箇所が繰り返している。

- `backoff_profile_t48_skew0p9_rr5.md` 末尾: 「tps は **perf record 下** の値 (sampling overhead 込み)。
  headline throughput は stock inline build の値 (P2-2/backoff_sweep)。ここは spin%/IPC 比の
  機序分析専用。」
- `2026-06-22_p2-case-study-backoff-synthesis.md` の 2026-06-28 追記:
  「perf 下 tps は sampling overhead 込みで **headline 非使用** (絶対値は stock build の
  committed fitness)。」

## 参考 — 同じケーススタディに登場する他の分母 (論文値ではない)

読者が混同しやすいので、論文値でないものを明示的に列挙する。**分母をまたいで混ぜない。**

| 分母 | write-heavy | balanced | read-heavy | 出典 | 役割 |
|---|---:|---:|---:|---|---|
| P2-2 全探索の stock 最良 | +39.0% | +12.9% | **-7.1%** | `output/s1-freeze/known_axes_freeze.json` の `p2_2_flag_opt.reference_fitness_tps` (1,872,376 / 2,752,621 / 8,487,844) | headline が cherry-pick でないことの補強 |
| 別時刻・逆順の repro campaign の no-backoff | +42.2% | +11.7% | 未実施 | `backoff-repro-*` の WAL | 定性的 corroboration。元 sweep と平均しない |
| stock 適応 backoff | +147.4% | — | — | write-heavy 1,052,528 tps | over-throttling の大きさ。論文の headline 利得ではない |

read-heavy の **-7.1%** (8,487,844 → 7,889,420 = -7.050365205%) は、write-heavy / balanced の
+39.0% / +12.9% と同じ分母規則を read-heavy へ適用した値である。旧文書がこの counterpart を
書いていなかったため、本 report で明示する。**論文採用値は -6.6% (同一 sweep 内の no-backoff 分母)
のままである** — 分母が違う 2 つの値を取り違えないために両方を載せる。

## 論文で使う表現

> 旧 linux-baremetal 環境の trace-disabled inline sweep では、同一 sweep 内の
> no-backoff control (`BACK_OFF=0`) に対し、sweep が選んだ静的 backoff の median throughput は
> write-heavy (fixed 10us) で 38.3% 高く、balanced (fixed 5us) で 11.3% 高く、
> read-heavy (fixed 2us) では 6.6% 低かった。これらは現在の paired campaign 契約 (D496) より前の
> 記述的結果である。

機序説明で profile を使う場合は次の限定を付ける。

> 別 CCBench revision の noinline perf-sampling 診断では、同じ公称 write-heavy contrast が
> 38.5% だった。この TPS は sampling overhead 込みであり、D20 により headline 値ではない。

## 言わないこと

- +38.5% と +38.3% を同じ測定の丸め違いとは言わない。
- 逆に、+38.5% と +38.3% の差を「別 regime が効果量を変えた実証」とも言わない。
  4 点の出自差は real だが、効果量への寄与は分解できていない。
- baseline を stock adaptive と呼ばない。適応の TPS は sweep レポートにあるが利得分母ではない。
  図・キャプション・見出しのいずれにも `adaptive` を残さない。
- 分母の違う値 (+39.0 / +12.9 / -7.1、+42.2 / +11.7、+147.4) を headline 3 値と混ぜない。
- write-heavy fixed 10us / balanced fixed 5us / read-heavy fixed 2us を単一 treatment の
  一般効果として平均しない。
- repro 値を元 sweep と pool せず、「頑健性を定量証明した」とも言わない。
- 性能成果物から correctness / certification / safe を推論しない。
- read-heavy の -6.6% を「backoff は常に有害」と一般化しない。これは abort baseline が低い
  領域の対照であり、機序主張は「利得は abort baseline が高いほど大きい」に限る。
- insight の表題日 (2026-06-22) を read-heavy の測定日として使わない。

## 未解決として残すもの (規律 3 — 何が足りないかを構造で返す)

A-3 (旧値の一本化) の範囲では**新規測定は不要**であり、本 report で閉じた。
以下は A-3 の外にある別項目であり、本 report では埋めない。

| 残件 | 何が足りないか | 所有 |
|---|---|---|
| `fig2_backoff_mechanism.png` の再作図 | 図中ラベルが誤っており、生成器が tracked に存在しない。sweep 系列で描き直すか、profile 系列のまま「no-backoff control」と正しく label するかの選択も要る | 本 wave が新規 T として起票 |
| profile の exact measurement timestamp / compiler / binary digest | artifact 自身が記録していない。worklog 日付や収録 commit 時刻を代用しない | 埋めない (推測禁止) |
| 4 点の出自差それぞれの throughput 寄与 | perf record 単独の overhead、profile の実行時刻、binary digest が無いため分解できない | 埋めない (A-3 の判定には不要) |
| D496 契約下の fresh paired 値 | 同一 campaign 内対測定 | A-1 (別 wave、[T-1721] 系) |
| 性能 workload そのものでの certification | 検証 workload と性能 workload が異なる | A-2 (別 wave) |

## source ledger

raw TPS と run 条件は JSON / WAL / campaign.lock / driver source を一次とし、
decisions・phase2・archive worklog は解釈と時系列の資料とする。

| artifact ID | tracked path | SHA-256 |
|---|---|---|
| profile-json | `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json` | `e99932213a571561c87f5ac253e19f59a81382718bb0cf08a9c64ea64281d184` |
| profile-md | `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.md` | `7d419391f9e9f8e205d87b5ca5b0b16eb57b5ebc73ce904adf47c8ee64e9e8c8` |
| sweep-write-lock | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/campaign.lock` | `493813a705e73908d8cbd99e55cba679f831b5cd3b8e1f40fc9f45d9dbee08ca` |
| sweep-write-wal | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl` | `9c179331a7171969ac6f4ed2b1d09e4afbf52378cfbac7bd133696a6589fe926` |
| sweep-write-report | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/reports/backoff-sweep-write-heavy_report.md` | `9590eaf5f4885ac12ab1350989076d02dbbdc607a908f156b722e53ac23ac283` |
| sweep-balanced-lock | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/campaign.lock` | `484c663ea167ec12ac1a44b30bf15353a3b66393ac6f528dacd4d97d3f67c857` |
| sweep-balanced-wal | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl` | `8ac3f47e55274fada20e6518eea9cbb0e822170eeda1b424df99e76e11fd789c` |
| sweep-balanced-report | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/reports/backoff-sweep-balanced_report.md` | `4860d2ee42dd5a703ed6c02f8d95f0a53508f57843d18e1c2c9067e429ad89a1` |
| sweep-read-lock | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/campaign.lock` | `610004b9e27e2f8d6961f919b720d757e05ec6169d66ef3d5b0108c79a930c56` |
| sweep-read-wal | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl` | `c74d5837a4facd071704a515f905d1d638463878850661cf217b96cd694774dc` |
| sweep-read-report | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/reports/backoff-sweep-read-heavy_report.md` | `8c9454316cc4aac607022a007a72187f1e20846c1c5a7c66c753885aa4d58379` |
| read-nc-1-lock | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/campaign.lock` | `6f169f9088b10ac5a8aa922a8766371f483e32d2979d51ae879529c693878c2c` |
| read-nc-1-wal | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/runs/wal.jsonl` | `9b5a3464ffc44dd0e27be06f2c8443348276270c190c6badd0621f29ad43aa17` |
| read-nc-2-lock | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-8ff95955/campaign.lock` | `8ff95955d76b3fc8c373563fa565444ff375af05a748f18a145397ca8332b346` |
| read-nc-2-wal | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-8ff95955/runs/wal.jsonl` | `7e3ea8f4724d1fcd9c4f3fde04304379b542354138c579f9fdad1d39b6c1cc4e` |
| dossier | `output/reports/layer3_paper_evidence_dossier.md` | `860697175d85cd645945465bccc66119f04d4e8297f8a54e310232151ee440a9` |
| prior-a3-report | `output/insights/2026-08-24_paper-story-a3-evidence-integration/README.md` | `12e93572a2aa4f5943f4923d13ba43c89b59a956740a0edba9039bbc71961ac9` |

`read-nc-1` / `read-nc-2` は正典でない read-heavy campaign であり、
「-6.6% の出所は 610004b9 に一意」を支える否定証拠として載せる。

## Canonical pointers

- `docs/paper-story/README.md` (日付なしの入口。本 report への writer-facing ポインタと
  最新スナップショットの stale 注記を置いた)
- `docs/paper-story/2026-08-23.md` の第 2 幕 P2-4 / 4 節 / 8 節 A-3 (凍結。誤記を含む)
- `output/insights/2026-08-24_paper-story-a3-evidence-integration/README.md`
- `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`
- `output/reports/layer3_paper_evidence_dossier.md` の 3.2 節
- `docs/decisions.md` D18 / D20 / D496
- `orchestrator/campaign/backoff_profile.py` / `orchestrator/campaign/p2_2.py`

既存 paper-story スナップショットと 08-24 report は凍結した入力・監査対象であり、
本 wave では上書きしていない。
