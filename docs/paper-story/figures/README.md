# docs/paper-story/figures/ — 図の凍結物と後継図

このディレクトリは論文ストーリー用の図を置く。

**この README 自身は「腐らない入口」であり、凍結物ではない。** 図が増えたり後継図が出たら更新する。
一方、**PNG / PDF / provenance JSON は凍結物**である。`docs/paper-story/README.md` の運用ルールに従い、
既存の図は上書きしない。誤りが見つかったら後継図を**別 filename**で、
**再現可能な生成器を伴うときだけ**作る。

## 図の一覧

| filename | 生成器 | 状態 |
|---|---|---|
| `fig1_phase2_negative.png` | tracked に無い | 凍結。2026-07-10 版で収録 |
| `fig2_backoff_mechanism.png` | tracked に無い | 凍結。**baseline を誤って label している** (下記) |
| `fig3_arc_status.png` | tracked に無い | 凍結。2026-07-10 版 (Phase 3 段 5 時点) の現況図 |
| `fig2b_backoff_sweep_3workload.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_backoff.py` | `fig2_` の**後継図**。本 README が再現手順を持つ |
| `fig2c_b10_extended_backoff.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_b10_extended_backoff.py` | B-10 拡張格子の**記述図**。1000 µs を F718 により除外した有効 28 点 |
| `fig4_s1a_9pair_direct_comparison.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_s1_9pair.py` | 縮小主張 S' の**失敗報告図**。既存図の後継ではなく独立した新図 |
| `fig5_a2_certification_reject.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_a2_certification.py` | A-2 正式 certification (outer `reject`) の**結果図**。既存図の後継ではなく独立した新図。判定は凍結 `certification.json` から読み、生成器は再計算しない。**測定条件の記述に erratum あり (同節の Erratum)。測ったのは採用静的 backoff ではなく `BACK_OFF` の有効/無効であり、取り直しまで論文の A-2 の結論にも図にも使わない (D1645)** |
| `fig6_a2_certification_observed_positive.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_a2_certification.py` | A-2 正式 certification (outer `observed-positive`) の**結果図**。D1644 の pin + patch 束縛 src_token で identity を計算する driver で取り直した attempt `t2364-20260907b` を描く。`fig5_` の後継ではなく、**別の条件を測った別の attempt** の独立した図である (絶対規律 7)。判定は `certification.json` から読み、生成器は再計算しない |
| `fig7_a2_builtin_backoff_onoff_reject.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_a2_certification.py` | `fig5_` と**同じ attempt `t2022-20260828c`・同じ値・同じ outer `reject`** を、**効いた条件の記述へ訂正**して描いた図。比較したのは CCBench 内蔵の適応 backoff の 有効/無効 (`BACK_OFF` の 0/1) である。`fig5_` の bytes は 1 byte も変えていない。**採用静的 backoff の結論・図としては使わない (D1936項21・D1993決定5、期限なし)** |
| `fig8_b10_static_tail_not_observed.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_b10_static_tail_formal.py` | B-10 静的 backoff 右 tail の **09-15 正式 cohort** (group `b10-backoff-grid-20260915T061814Z-545445`、集団判定 `not-observed-in-any-workload`) の**記述図**。事前登録 §4.1 の 8 点 × 3 workload × 5 反復。`fig2c_` とは別格子・別 cohort であり、その続きではない。言い方は事前登録 §4.5 の固定表現に限り、**性能は未認証 (`performance_certified: false`)**。2 本目の論文と共用しない (D1637)。**再現欄付きの後継図 `fig8b_` がある (下記)。本図の bytes は不変** |
| `fig8b_b10_static_tail_cohort2.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_b10_static_tail_formal.py` (`--reproduction-cohort 2`) | `fig8_` の**後継図 (再現欄付き)**。**主結果 cohort 1** (group `b10-backoff-grid-20260915T061814Z-545445`、上 block) と**独立再現 cohort 2** (group `b10-backoff-grid-20260919T131526Z-2235286`、事前登録追記込み commit `8737cacb4` に束縛、下 block) を縦 2 block で**区別して併記**する記述図。両 cohort とも集団判定 `not-observed-in-any-workload`、18/18 区間 `declining`。**合成しない** (プール推定・統合 verdict・cohort をまたぐ有意水準を作らず、近さを一致度として評価しない。事前登録 2026-09-19 追記 項 2〜3・項 7、D2157)。言い方は §4.5 の固定表現に限り、**性能は未認証 (`performance_certified: false`)**。2 本目の論文と共用しない (D1637) |
| `fig9_a1_balanced5_sized_attempt1.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_a1_sized_paired.py` | A-1 balanced5 sized 本走 **attempt-0001** (study `paper-story-a1-20260901-balanced5-sized-v1`、job `4939` / `4940` / `4941`) の**記述図**。3 workload の 30 対の差 (variant − baseline) と、その対差平均 ± 登録済み区間 h を床 ±B と並べる。**非認証 lane (`formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only`)** のdescriptive 出力であり、headline 値・workload 横断の結論・C1 の再現判定にせず、単一 attempt を反復間の安定性へ一般化しない。A-1 の充足・formal 化・再認可は判定しない。既存図の後継ではなく独立した新図。2 本目の論文と共用しない (D1637) |
| `fig3b_arc_status_2026-09-20.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_arc_status.py` | `fig3_` の**後継図**。ストーリー 2026-09-19 版の §0 の 3 幕と §8 の A 系列 5 項目 / B 群 11 項目の**状態** (取得済み / 非認証 / 裁定待ち・人間手番 / 未取得) だけを描いた模式図。**数値・新規判定を含まない** (生成器は JSON を描くだけで判定・値・認証を再計算しない)。入力は状態 JSON `tools/plotting/arc_status_story_2026-09-19.json` (人が同版本文から写した射影) と同版本文。旧 fig3 は凍結のまま。**2026-09-21c 版の状態を描いた後継図 `fig3c_` がある (下記)。本図の bytes は不変** |
| `fig3c_arc_status_2026-09-21.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_arc_status.py` | `fig3b_` の**後継図**。ストーリー 2026-09-21c 版 (同日の 3 版目) の §0 の 3 幕と §8 の A 系列 5 項目 / B 群 11 項目の**状態**だけを描いた模式図 (fig3b と同じ 4 状態・同じ生成器)。**数値・新規判定を含まない。** 入力は状態 JSON `docs/paper-story/figures/arc_status_story_2026-09-21c.json` (人が同版本文から写した射影) と同版本文。B-8 の obtained は観測した 30 枠の trace についての 3 値判定 `pass` の記録で、未観測の条件・性能・S-1 の充足へ広げない。副ラベルは本文【状態】の要約で限定を網羅しない (正本は同版 §8)。fig3 / fig3b は凍結のまま |
| `fig10_b7_fixed5_three_workload_regression.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_b7_fixed5_regression.py` | 採用候補 **fixed 5 µs** を 3 workload で同一 attempt `b7f5-20260919a` (study `paper-story-b7-fixed5-regression`、request `10807` / `10808` / `10809`) に測った 6 cell × 5 標本と、各 workload の median 効果を D1639 の between-run 床値と比べた**記述図** (B-7 の材料)。稿 `results/2026-09-19-b7-fixed5-three-workload-regression.md` の床値判定 (write-heavy / balanced 退行なし、**read-heavy は床値超の退行**) を写す (判定の出所は稿の転記で、生成器は述語 `effect < −floor` との整合だけを検査する)。**B-7 の要件充足・反復 attempt・certification 昇格・有意差は判定しない (D2044 項 3、D2162)。** 既存図の後継ではなく独立した新図。既存材料 (10 / 5 / 2 µs) とプール・比較しない (D1993 項 6)。2 本目の論文と共用しない (D1637)。**追補 (2026-09-20、D2174 項 3): B-7 は図の外で「単一 attempt・descriptive・非認証・反復間安定性は未判定」の限定付きで充足と裁定され、D2044 項 3 の「要件充足へ昇格させない」はこの限定付き充足で supersede された。図・caption・provenance の bytes は不変 (同節の追補)** |
| `fig11_a6_certification_reject.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_a2_certification.py` | A-6 read-heavy 正式 certification (attempt `a6-20260908b`、request `982234.nqsv`、outer `reject`) の**結果図**。rr95 の exact 2 cell (stock `BACK_OFF=0` 対 採用静的 backoff fixed 2 µs)、median 比 −5.7841%。fig6 (A-2) と同じ生成器・同じ描画契約で描き、`fig5_` / `fig6_` / `fig7_` の後継でも前身でもない別 policy・別 attempt・別 workload の独立した新図 (絶対規律 7)。判定は `certification.json` から読み、生成器は再計算しない。**性能の `reject` と別走行の正しさ `certified` (2/2) は別の段で、後者は性能の認証ではなく、前者は正しさ証拠を取り消さない (D1993 項 2)。** B-10 の近接条件 3 block ([T-2430]) は履歴的照合であって pool しない。稿 `results/2026-09-18-a6-certification-reject.md` を `caption_source` として SHA-256 束縛 (稿 bytes は不変)。2 本目の論文と共用しない (D1637) |
| `fig12_k2_manual_loop_dataflow.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_k2_loop_flow.py` | K2 手動 loop 3 巡 (稿 `results/2026-09-20-k2-manual-loop-three-rounds.md`、B-6 の材料) の**データフローの説明図** (fig2 系と同じ「説明図」、fig3b と同じ値なしの模式図)。役割 (planner-v4 / coder-v4-autonomous-k2 = role 定義が `tools: []` の構造遮断、critic = Bash を持つ legacy role)、親が射影する入力 key、評価経路 (Pegasus 計算ノード job → trace-enabled verify → trace-disabled bench → WAL)、実測の還流 2 回・診断の還流 1 回 (exact 6 field)、規律 6 の自己申告 marker を描く。**性能値を描かず、3 走を比較せず、知識・診断の因果効果を主張せず、B-6 の充足を判定しない。同 job stock 対照は未達 ([T-2795] 裁定待ち)。** 入力は稿から人が写した流れ JSON `tools/plotting/k2_loop_flow_2026-09-20.json` で、生成器は稿の見出し行の一意性と role frontmatter との一致だけを検査し判定・値を再計算しない。稿を `caption_source` として SHA-256 束縛する (稿は provenance の hash を持たない、F36)。既存図の後継ではなく独立した新図。2 本目の論文と共用しない (D1637) |
| `fig13_b10_waiting_grid_forest.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_b10_waiting_grid_forest.py` | B-10 待ち方 grid 正式走 (report phase、request `978195.nqsv`、事前登録 発効版 commit `77b33e37d`) の**結果図**。登録した `constant` 対 `symmetric-modulo` の 1 contrast についての 3 族 Holm 判定 (3 族とも `different`、方向は 3 族とも `symmetric-modulo` が高い側) と、36 cell の効果量・95% paired-block 区間 (df 2)・等価域 ±3.0% との関係 (内側 32 / 境界を跨ぐ 4 / 外側 0) を 1 行 × 3 panel の forest 図に描く。判定は report の provenance JSON から読み、生成器は 135 record から同じ式で再計算して一致を要求するだけで判定を作らない。**区間が帯の内側にあることは等価性の成立ではなく (等価性検定はしていない)、cell ごとの有意差は判定せず、静的右 tail の 2 cohort (fig8 / fig8b) と合成・比較しない。`official_certification` は `false` で、性能値を採用根拠にしない。機序は述べない。** 既存図の後継ではなく独立した新図。稿 `results/2026-09-20-b10-waiting-grid-formal.md` を `caption_source` として SHA-256 束縛 (稿 bytes は不変。稿の限定 11「論文図は無い」は起草時点の事実)。2 本目の論文と共用しない (D1637) |
| `fig14_a1_balanced5_sized_attempt2.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_a1_sized_paired.py` (`--attempt attempt-0002`) | A-1 balanced5 sized 本走 **attempt-0002** (job `13220` / `13221` / `13222`、D2172 項 2 が 1 attempt 限定で認可した独立の観測) の**記述図**。fig9 と同じ生成器・同じ形で、3 workload の 30 対の差と対差平均 ± 登録済み区間 h を床 ±B と並べ、各 panel 題に `variance_plan_breach` (write-heavy / read-heavy は true、balanced は false) と sd / planned sigma を描く。**非認証 lane** の descriptive 出力であり、headline 値・workload 横断の結論・C1 の再現判定にしない。**attempt-0001 (fig9) とプールせず、差・比・区間の重なり・再現判定を描かない (D1993 項 6、D2194 項 6)**。breach の原因を帰属しない。A-1 の充足・formal 化・L-A1S-4 の解除は判定しない。fig9 の兄弟であって後継ではない (fig9 の bytes は不変)。2 本目の論文と共用しない (D1637) |
| `fig15_mocc_witlight_four_arm.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_mocc_witlight_four_arm.py` | stock mocc の軽量 witness 4 arm × 60 走 (本走 4 block W1〜W4、smoke は含めない) の**記述図**。arm 別の G2 signal 検出率 (on 0/60・0/60、off 1/60・1/60) と Clopper–Pearson 両側 95% 区間を forest で、走あたり commit 数の平均 (TRACE=1 の曝露量) と on/off 比を数値列で示す。値は稿 `results/2026-09-20-mocc-witlight-four-arm.md` §2 の逐語。**非 certifying の観測**であり、片側 Fisher p = 0.500 (未調整) の非有意を同等性・効果なしとして、commit 数を性能として、G2 signal を根因の同定として描かない。repo 外の 5 file (W1〜W4 `result.json`・`summary.json`) を SHA-256 で束縛する。既存図の後継ではなく独立した新図。2 本目の論文と共用しない (D1637) |

**fig5 の用途制限の追補 (2026-09-11、D1936項21・T-2521):** 一覧の「取り直しまで」という期限は
当該旧図には適用しない。採用静的 backoff に関する A-2 の結論・図として使えない制限は期限なしである。
適用範囲は fig5 節の「追補 — 旧 fig5 の用途制限に期限を設けない」を参照する。

## 調整済み adaptive の実対照 (論文図へ未昇格)

D1506 は「backoff 機構の性能比較は、無 backoff と**調整済み adaptive** (刻み 1 µs /
更新間隔 2560 µs / 上限 1000 µs) の 2 本を基準線に置く」と定めた。
**その基準線を実際に同じ軸へ並べた図は、上の一覧には無い。** 現物は論文図の外にある。

- [`t2187_stage2_thread_axis.png`](../../../output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.png)
- [`t2187_stage2_thread_axis.pdf`](../../../output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.pdf)
- [`t2187_stage2_thread_axis.provenance.json`](../../../output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json)

生成器は `tools/plotting/plot_t2187_adaptive_consts.py` の `threads` モードである。同じ 6 パネル
(3 workload x throughput / abort 率) の同じスレッド軸へ、**無 backoff** (`none`)、
**CCBench 既定 3 定数の adaptive** (`s100-u10`)、**調整済み adaptive** (`s1-u2560`)、および
調整候補 2 本 (`s0.5-u2560` / `s1-u640`) を描く。スレッド 6〜48、7 反復、
t 分布の 95% 信頼区間つき。一次資料は
`output/insights/2026-09-02_cicada-adaptive-three-constants.md`。

**`fig2b` / `fig2c` をこの対照の代わりに引用してはならない。** 両図は適応側に既定 adaptive しか
持たず、調整済みのセルを含まない。旧 `linux-baremetal` の campaign にそのセルが無いためで、
足すには新規計測が要る。

**上の図と `fig2b` / `fig2c` を同じ図・同じ表・同じ時系列・同じ再現判定へ畳んではならない。**
違うのは環境だけではない — CCBench の版 (`6656e93` と `511c953` +
`patches/cicada-adaptive-params.patch`)、反復設計 (campaign 内 5 反復と 7 ノード x 1 rep)、
集約 (median 比と標本平均)、`clocks_per_us` (1800 と 2100) が違う。

**この図は認証されていない。** trace-disabled の性能測定のみで、直列性の検査を通していない
(provenance の `not_certified` field と、図中の `NOT CERTIFIED` 表示)。
**variant 採用の根拠にも、certified な性能結論にも使わない** (絶対規律 2)。
論文図への昇格には対応する correctness 検査の決着が要るが、**それは必要条件であって
十分条件ではない** — 現 provenance が束縛する出力 path は repo 外にあり、論文図の場所へ置いた
copy を検査する consumer も存在しない。昇格そのものは別途決着させる。

## `fig2_backoff_mechanism.png` の何が誤っていたか

旧図は横破線に `stock adaptive backoff (Cicada-type hill-climb)` という label を付けているが、
**その線が描いている値は無 backoff のもの**である。図の中で赤い曲線の x=0 の点 (無 backoff) と、
その破線が同じ高さにある — 同じ値に 2 つの異なる label が付いていた。

さらに旧図が描いていた系列は perf record 下の診断用 profile 系列であり、D20 が
「perf 下の tps は headline 非使用」と定めているため、論文の headline 値の出所にはできない。

詳細と一次資料は `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`。

後継図 `fig2b_backoff_sweep_3workload` はこれを次のように直している。

**本 README は「headline 適格」という分類語を使わない** (2026-08-26 に訂正した。理由は下記)。
後継図のデータは D496 より前の記述的結果であり、この図は論文の利得率の出所でもない
(下のキャプション正文を参照)。**現行の対測定契約 (D496) を満たすという意味でもない。**

**なぜ分類語をやめたか。** 以前この節は「表中の headline 適格 / 非適格 は D20 の一点、すなわち
perf record 下で採った tps かどうかだけを指す」と書き、後継図を「headline 適格」に分類していた。
しかし実測すると、後継図の入力 campaign 3 件の実行 command 24/24 件が
`numactl --interleave=all perf stat -e LLC-load-misses,LLC-loads,instructions,cycles -- ...` であり、
**後継図の系列も perf 下の測定である**。D20 の位置づけ節の字義は
「perf 下 tps は overhead 込みで headline 非使用」であって `perf record` に限定していない。
D497 は「perf が**無い**ことを性能主張の信頼性の条件にしない」という別方向の決定であり、
perf 下で採った tps を headline に使ってよいとは定めていない。
したがって「D20 の意味で headline 適格」という分類は D20 本文に支持されない。
**本 README の図はいずれも、絶対スループットを論文の headline 値の出所にしない。**
この訂正で変えたのは本 README の分類語だけであり、**図の PNG / PDF / provenance JSON の bytes、
各図のキャプション正文、凍結スナップショット (`2026-07-10.md` / `2026-08-23.md` / `2026-08-26.md`)
は一切変えていない。**

| 論点 | 旧図 | 後継図 |
|---|---|---|
| 系列 | profile (`perf record` 下の診断系列) | sweep (`perf stat` 下。絶対 tps は headline 値の出所にしない) |
| workload | write-heavy 1 件 | write-heavy / balanced / read-heavy の 3 件 |
| 基準線 | 無 backoff の値に「適応 backoff」の label | **無 backoff 対照 1 本だけ**を、そう名乗って描く |
| 基準線の不確かさ | 点推定のみ | 95% 信頼区間の帯を付ける |
| 下段の機序 | spin% を含む (profile 由来) | abort 率と IPC (sweep の集約値) |
| 生成器 | tracked に無い | `tools/plotting/plot_backoff.py` (tracked) |
| 入力の束縛 | 無し | provenance JSON が入力・生成器・出力の SHA-256 と、描いた線の label↔値 対応を記録 |

なお `fig2_backoff_mechanism.png` を参照する凍結スナップショット
(`docs/paper-story/2026-07-10.md` と `docs/paper-story/2026-08-23.md`) のキャプションも
同じ誤りを持つが、**両版は凍結物なので訂正しない**。訂正は日付なしの入口
`docs/paper-story/README.md` の erratum が担う。

## 後継図の再現

repo root から、**計測機の外**で次の 1 行を実行する (FIGURE_CONVENTIONS §7)。

```
python3 tools/plotting/plot_backoff.py --baselines no-backoff docs/paper-story/figures/fig2b_backoff_sweep_3workload output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7 output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9
```

`--baselines no-backoff` が、この図の基準線を無 backoff 対照 1 本に限定している。
**この図を撮った当時の生成器は、option を省くと無 backoff と `stock adaptive` の 2 本を描いた。**
2 本あると**どちらの線が利得の分母かが図から決まらなくなる** — それが旧図の事故の本質である。

**2026-09-02 に生成器の既定を無 backoff 1 本へ狭めた** (D1506)。ここでいう `stock adaptive` は
**CCBench 既定 3 定数** (刻み 100 µs / 上限 1000 µs / 更新間隔 10 µs) の適応 backoff であって、
調整済み adaptive ではない。D1506 は既定 adaptive を測ること自体を禁じないので、
`--baselines stock-adaptive` を明示すれば今も描ける。**禁じているのは、既定 adaptive を
単独の適応基準線に置いた比較から機構の優劣を言うことである。**
この旧 `linux-baremetal` campaign 3 件は調整済み adaptive のセルを含まないので、
**本図に調整済みの対照を足すことはできない** (足すには新規計測が要り、
Pegasus で測った値を旧環境の図へ混ぜてはならない)。上の再現コマンドは既定が変わった後も
そのまま有効で、生成される図は変わらない。

出力は次の 3 ファイル。

- `fig2b_backoff_sweep_3workload.png` — ラスタ
- `fig2b_backoff_sweep_3workload.pdf` — ベクター (論文投稿はこちら)
- `fig2b_backoff_sweep_3workload.provenance.json` — 入力・生成器・出力の SHA-256、
  描いた線の label↔値 対応、測定条件、図に出した主要数値

### 再現できるのは「値」であって「バイト列」ではない

同じコマンドを再実行すると同じ論理値・同じ図が得られるが、
**3 点セットの byte-for-byte 一致は保証しない。**

- provenance JSON は生成時刻 (`generated_utc`) を持つので**時刻依存**。
- PDF は matplotlib が生成日時を埋めるので**時刻依存**。
- PNG は matplotlib の版が metadata として入り、font 解決も環境に依存するので**環境依存**。

バイト一致を要求したいなら `SOURCE_DATE_EPOCH`・依存版・font を pin する別の仕組みが要る。
本図はそこまでしていない。**着地したバイト列の同一性は provenance JSON が記録した SHA-256 と
`orchestrator/tests/test_backoff_figure_provenance.py` が守る** — 再生成の決定性には依存しない。

## 入力

3 つとも `output/campaigns/` の tracked な既存 campaign であり、本図のために新規計測は行っていない。

| workload | campaign | read 比率 |
|---|---|---:|
| write-heavy | `backoff-sweep-silo-write-heavy-sweep-493813a7` | 5% |
| balanced | `backoff-sweep-silo-balanced-sweep-484c663e` | 50% |
| read-heavy | `backoff-sweep-silo-read-heavy-sweep-610004b9` | 95% |

各 campaign から読むのは反復ごとの生スループット値と genome を持つ WAL、abort 率と IPC の
集約値を持つ dat、CCBench commit を持つ lock file の 3 種である。
3 種の SHA-256 は provenance JSON にある。

read-heavy の campaign が 3 つあるうち `610004b9` が正典である理由 (他の 2 つは screening の
positive control と build 失敗) は、上記 insight の該当節にある。

## キャプション正文

> **図2b.** 旧 `linux-baremetal` 環境における Silo の静的 backoff sweep (3 workload)。
> 上段は各設定 5 反復の標本平均スループット (M tps = 毎秒 100 万トランザクション) と、
> t 分布による 95% 信頼区間。灰色の破線と帯は、**同じ sweep の中の無 backoff 対照**
> (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) の標本平均と 95% 信頼区間である。
> **この対照が利得の分母であり、図中の基準線はこれ 1 本だけである。**
> 上段の `peak` 注釈は、曲線の最大が両端でなく内側にある workload だけに付く。
> read-heavy は単調減少で最大が左端なので注釈は付かない。
> 下段は abort 率と IPC (instructions per cycle = 1 サイクルあたりの命令数)。
> 下段は集約 1 点なので信頼区間を付けない。
> 測定条件は 3 workload 共通で、レコード数 1,000,000、48 スレッド、Zipf skew 0.9、
> read-modify-write 無効、実行時間 3 秒、`clocks_per_us` = 1,800 TSC tick/µs、トレース無効、
> `numactl --interleave=all`、環境タグ `linux-baremetal`、CCBench commit `6656e93`。
> **記録された実行フラグの上では** read 比率だけが workload ごとに異なる
> (write-heavy 5%、balanced 50%、read-heavy 95%)。ただし測定日は同一ではない
> (write-heavy と balanced は 2026-06-22、read-heavy は 2026-06-28)。
> 縦軸は workload ごとに独立なので、パネル間で線の高さや傾きを直接比べてはならない。
> データは verifier epoch E0 (この campaign を撮った時点で verifier の同一性を束縛する権威が
> まだ無かったことを示す印) の `HISTORICAL_RAW` 読み出しであり、現行の paired campaign 契約
> (`docs/decisions.md` の D496) より前の記述的結果である。
> **本図は論文の利得率の出所ではない。** 論文値 (write-heavy +38.3%、balanced +11.3%、
> read-heavy -6.6%) は同じ WAL の各側 **median** の比であり、本図の点推定は**標本平均**である
> (平均から計算すると +38.1% / +11.4% / -6.9%)。両者は同じ生値の別の要約であって、
> 一方が他方の丸め違いではない。
> 旧図 `fig2_backoff_mechanism.png` が示していた spin 希釈の機序は**本図の射程外**である
> (spin% は perf record 下の診断系列にしかない)。

## proof chain

- 図に描いた線 → provenance JSON の `baselines[]` (label・値・95% CI 半幅・genome)
- 図の主要数値 → provenance JSON の `facts`
- provenance JSON → 入力 WAL / dat / lock file / 生成器 / 出力 PNG・PDF の SHA-256
- それらが着地後もずれないこと → `orchestrator/tests/test_backoff_figure_provenance.py`
- 図中の label と実際に描いた線の一致 → `orchestrator/tests/test_plot_backoff_ci.py`
- 利得率の一次資料と条件表 → `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

---

# `fig2c_b10_extended_backoff` — B-10 拡張格子

**CCBench 既定 3 定数** (刻み 100 µs / 上限 1000 µs / 更新間隔 10 µs) の adaptive backoff が
取りうる帯域を静的点で覆うために取得済みだった 3 workload の拡張格子を、
新規計測なしで論文図へ変換した。上段は WAL の各 5 反復から再計算した標本平均 throughput と
t 分布 95% 信頼区間、下段は dat の集約 abort rate である。

## 入力と除外

| job | workload | campaign id | identity SHA-256 |
|---:|---|---|---|
| 951689 | write-heavy | `b10-backoff-grid-silo-write-heavy-sweep-0a386b45` | `0a386b454829f7d3487ba016b81fe1360d6bf7c8a54666a9f33830dbfd196c7a` |
| 951690 | balanced | `b10-backoff-grid-silo-balanced-sweep-9ded73c4` | `9ded73c4e7d0ffc7ef77d0f909194b3aa83823d72414872c137b7b419ddc86c8` |
| 951691 | read-heavy | `b10-backoff-grid-silo-read-heavy-sweep-e2d75497` | `e2d75497facce68e80ee5468ac14070d51a96af7b0f9a297ac87bed8758e0c6a` |

各 campaign は raw 29 点を持つ。要求値 1000 µs は符号化衝突により mode 1・振幅 0 と解釈され、
実体は 0 µs の独立反復だった (F718)。その測定値は provenance に保持するが、格子点としては
3 workload とも除外し、図には 0〜900 µs の有効 28 点だけを描く。static 0 µs は
`BACK_OFF=1, BACKOFF_FIXED=0` であり、no backoff ではない (D1106)。

**被覆の目標が指しているのは「適応機構」一般ではなく、既定 3 定数の到達可能集合である**
(2026-09-02 追記)。D1106 が数えた 11 状態 `{0, 100, …, 1000}` µs は、刻み 100 µs と
上限 1000 µs という**既定値から導いた格子**であって、adaptive backoff という機構が
原理的に取りうる値の集合ではない。**調整済み adaptive** (刻み 1 µs / 更新間隔 2560 µs /
上限 1000 µs、D1506) の到達可能集合はこの 11 点と一致しない。
**変わるものと変わらないものを分けて書く。**

- **変わらない:** 本図が描いた 28 点の測定値、95% 信頼区間、F718 による 1000 µs の除外、
  および「静的 backoff 量に対する性能地形」としての読み。これらは 1 つも変わらない。
- **変わる:** この格子が**何を覆っているか**という主張である。「適応機構が到達しうる状態を
  覆った」から「**既定定数を入れた適応が**到達しうる状態を覆った」へ狭まる。
  **これは呼称の言い換えではなく、主張の射程の変更である。** 調整済み定数の下では
  同じ機構が別の状態集合を取るので、本図の被覆をもって「適応機構が取りうる範囲を
  静的点で覆った」とは言えない。

したがって本図を「適応機構が取りうる状態を静的点で覆った図」として引用してはならない。
正しくは「**既定定数の** adaptive が取りうる状態を覆うことを目標にした図」である。
一次資料は `output/insights/2026-09-02_cicada-adaptive-three-constants.md`、
洗い出しの全体は `output/insights/2026-09-02_default-adaptive-baseline-replacement.md`。

## 再現

repo root から、**計測機の外**で実行する。`MEASUREMENT_ROOT` は、provenance に記録された
root-relative 22 入力を保持するディレクトリである。

```
python3 tools/plotting/plot_b10_extended_backoff.py docs/paper-story/figures/fig2c_b10_extended_backoff MEASUREMENT_ROOT
```

出力は `.png`、`.pdf`、`.provenance.json` の 3 点。入力 root を別の場所へ移した場合も、
relative path と SHA-256 が一致すれば同じ入力として検証できる。外部 bytes が手元に無い場合でも、
provenance の 22 入力、receipt chain、測定条件、claim 境界、図と生成器の repo closure は検査される。

## キャプション正文

> Extended static backoff under trace-disabled committed measurements (48 threads, 1,000,000 records, Zipf skew 0.9, read ratios 5/50/95%, read-modify-write (RMW) disabled, Pegasus hosts bnode007/bnode009/bnode016). Throughput is reported in M tps = million transactions per second and is the mean of five WAL repetitions with t-distribution 95% confidence intervals; abort rate is the dat fraction and has no repetition-level confidence interval. Static 0 µs means BACK_OFF=1 and BACKOFF_FIXED=0, not no backoff. The requested 1000 µs row is retained in provenance but excluded under the canonical F718/D1106 ruling, which asserts mode 1 and amplitude 0 as a ruling interpretation rather than a value derived from measurement artifacts. Latency is retained for provenance but is not drawn or treated as independent mechanism evidence: in this 48-thread closed-loop benchmark it is the reciprocal-throughput quantity. Panel heights and slopes use workload-local y scales and must not be compared across panels.

旧 3% floor は現環境・workload 別に取り直す裁定 (D1094) の前なので、本図は noise band や
over-throttling onset の判定を描かない。ADD_ANALYSIS の診断値も D1092 に従い図へ使わない。

## proof chain

- 描画 84 点 → provenance `data[*].included_points` (各 workload 28 点)
- 除外 3 点 → `data[*].excluded_points` (1000 µs の値と F718 authority を保持)
- throughput と CI → WAL の 5 反復から独立再計算
- job / campaign / source 対応 → submit + completion + reservation + campaign lock
- 入力・生成器・依存・PNG/PDF → provenance の full SHA-256
- 着地 bytes → `orchestrator/tests/test_b10_extended_figure_provenance.py` の独立 PNG/PDF pin
- 図中の9系列・軸・label → `orchestrator/tests/test_plot_b10_extended_backoff.py`
- 作図規約 → `tools/plotting/FIGURE_CONVENTIONS.md`

---

# `fig4_s1a_9pair_direct_comparison` — S-1a の 9 対 (失敗報告図)

`docs/paper-story/2026-08-26.md` §4 は、縮小主張 S' の 9 対を「描ける (未作図)。失敗報告の図として
有用」と記していた。本図はそれを作図したものである。**同スナップショットの凍結後に、
新規計測をせず既存の tracked 成果物だけから描いた。**同スナップショット、S' の確定文言、
Holm 族 4 の判定表は変更していない。

## 何を示す図か

合成軸 (abort 要因別に backoff の発火可否を切り替える trigger gating 構成) を、既知軸の最良 3 種
— コンパイル時フラグ最適化・静的 backoff の最良値・書込ロック順の並べ替え — と 3 workload で
突き合わせた 9 対である。**S-1a の成立条件は 9 対すべてが判定境界 +3% を厳密に超えることであり、
6 対が超えないため S-1a は不成立である** (family p = 1.0)。

上段が 9 対の相対中央値差、下段が各セルの 8 標本の分布である。境界を超えた 3 対はいずれも
書込ロック順並べ替えとの比較だが、**この図は「1 軸に勝った」ことを主結果として描いていない** —
判定境界を超えない側を薄赤で塗り、9 点を同面積で置き、図の上端に不成立を明示している。

## 既存図との関係

| 論点 | 図2b (backoff sweep) | 図4 (本図) |
|---|---|---|
| 何の図か | 静的 backoff の sweep (記述) | 縮小主張 S' の登録 9 対 (失敗報告) |
| 関係 | `fig2_` の後継図 | **どの図の後継でもない独立の新図** |
| 入力 | backoff sweep campaign 3 件の WAL / dat | S-1 直接比較の凍結 report + campaign 4 件の WAL |
| 判定の出所 | 判定を持たない記述的な図 | 判定は凍結 report のみ。生成器は再計算しない |
| perf | `perf stat` 下 | `perf stat` 下 |
| 絶対 tps の扱い | headline 値の出所にしない | headline 値の出所にしない |

既存の `fig1` / `fig2` / `fig2b` / `fig3` の bytes は本図の追加で一切変わらない。

## 再現

repo root から、**計測機の外**で次の 1 行を実行する (FIGURE_CONVENTIONS §7)。

```
python3 tools/plotting/plot_s1_9pair.py docs/paper-story/figures/fig4_s1a_9pair_direct_comparison output/reports/s1_direct_comparison/report.json --develop output/campaigns/s1-direct-develop-direct-comparison-d0f495bf --floor output/campaigns/s1-direct-floor-direct-comparison-b82b9229 --block1 output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2 --block2 output/campaigns/s1-direct-block2-direct-comparison-9645b16a
```

出力は `.png` (ラスタ) / `.pdf` (ベクター、論文投稿はこちら) / `.provenance.json` の 3 つ。
同じ再現コマンドは provenance JSON の `reproduction.argv` にも記録されている。

### 再現できるのは「値」であって「バイト列」ではない

図2b と同じ制約である。provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、
PNG は matplotlib の版と font 解決に依存する。**着地したバイト列の同一性は provenance JSON が
記録した SHA-256 と `orchestrator/tests/test_s1_9pair_figure_provenance.py` が守る** —
再生成の決定性には依存しない。

## 入力

新規計測は行っていない。5 つとも tracked な既存成果物である。

| 役割 | path | 用途 |
|---|---|---|
| 凍結 report | `output/reports/s1_direct_comparison/report.json` | 判定・p 値・certified 標本集合 |
| develop | `output/campaigns/s1-direct-develop-direct-comparison-d0f495bf` | 認定標本の照合 (性能値なし) |
| floor | `output/campaigns/s1-direct-floor-direct-comparison-b82b9229` | 判定境界の算出・照合 |
| block1 | `output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2` | 効果量の標本 (各セル 4) |
| block2 | `output/campaigns/s1-direct-block2-direct-comparison-9645b16a` | 効果量の標本 (各セル 4) |

**効果量の標本母集合は block1 ∪ block2 (各セル 4+4=8) である。floor campaign の各セル 8 標本は
効果量には混ぜず、+3% 判定境界の算出と照合にだけ使う。**これは `orchestrator/campaign/s1_report.py`
の `bind_left_target` と `floor_cmp` が定める生成契約であり、生成器はそれを再計算して report と
照合する。

develop campaign は `s1-direct-develop-direct-comparison-d0f495bf` が正典である。もう一つの
`...-7bccdf1a` は 24 start / 15 commit で、report の accepted develop 18 件に対応しない。

### 凍結設計が記録している文脈 (図には描いていない)

`output/s1-freeze/measurement_freeze.json` は次を記録している。図の忠実性に関わるので、
事実としてここに引用する。

- 各比較定義の注記: `stock_common は併記用の文脈セルであり、検定比較対には含めない。`
  **本図は `stock_common` を描かない。** 基準線にすると、登録 9 対に含まれない第 10 の比較
  (合成軸と stock の差) を図が主張することになるためである。同セルの値と、
  `sort_best` および `system_gate` との比は provenance JSON の `facts.context_cells` に
  `registered_comparison: false` を付けて記録した。
- `sort_best` セルの選定履歴 (workload 別)。write-heavy は本走 argmax 規則で固定。
  balanced は本走 argmax で `sp_dd` を固定したが、再測定 campaign
  `p3-s6-sort-sweep-balanced-sweep-1b39095e` で floor 超を再現せず D46 の裁定は差なし。
  read-heavy は sweep 未実施で、D52 §2.1 の事前固定 `sk_ad` を採用し comparator は write-heavy
  本走 provenance から流用。

### report が参照する freeze と現行 bytes の差

凍結 report の `freeze_ref.sha256` は `5c719c07…` で、現行の
`output/s1-freeze/measurement_freeze.json` (`203de36b…`) と一致しない。前者は commit
`b4e5cb621e3f8f93de952e9400d4b8dcd34107e0` 時点の bytes である。差は次の 3 か所だけで、
**本図が使う意味内容 — 18 セル定義、12 比較定義とその注記、`operating_point`、`workload_flags` —
は両版で完全に同一である。**

- `/frozen_at_head`
- `/implementation_hashes/known_axes_freeze/sha256`
- `/cells/read-heavy:sort_best/variant/sources[0]/sha256`

この事実は provenance JSON の `facts.freeze_proof` に記録した。**旧 bytes の取得を検査の前提には
していない** — テストが確かめるのは、記録値が report の値および現行 file の hash と一致し、
両者が異なることまでである。上記 commit を `git show` すれば読者が差分を再導出できる。

## 作図規約への適合

provenance JSON の `facts.figure_conventions_compliance` は `"partial"` を記録している。
**標本と集約値は WAL からその場で再計算するので §1 を満たすが、判定と p 値は hash で束縛した
凍結 report を権威として読むので、§1 の「入力は WAL/dat のみ」の字義には合わない。**
これは意図した設計である — 作図側が判定を作り直すことは絶対規律 2 に触れるため、
凍結された裁定をそのまま描くことを優先した。規約側にこの限定例外を書き足すかは未裁定である。

## キャプション正文

キャプション正文は provenance JSON の `caption` にも同一文字列で記録されており、
`orchestrator/tests/test_s1_9pair_figure_provenance.py` が両者の一致と、必須要素が独立再計算した
値と対応することを検査する。

> 図4. 縮小主張 S' の性能次元 (S-1a) — 既知軸最良に対する直接比較 9 対 (失敗報告)。上段は、abort 要因別に backoff の発火可否を切り替える合成軸 (trigger gating) と、既知軸の最良 3 種 — コンパイル時フラグ最適化、静的 backoff の最良値、書込ロック順の並べ替え — との相対中央値差である。各点は 100 × (合成軸側の中央値 − 相手側の中央値) / 相手側の中央値 で、各セル 8 標本から再計算した。灰色の実線は差 0、赤の破線は厳密に超える必要がある判定境界 +3% (between-run floor = 走行間の再現ばらつきの下限) で、薄赤の領域は境界を超えない範囲である。S-1a の成立条件は 9 対すべてが境界を超えることである。コンパイル時フラグ最適化との 3 対は −9.3%〜−55.1%、静的 backoff 最良値との 3 対は −36.0%〜−51.9% で境界を超えず、書込ロック順並べ替えとの 3 対だけが +55.5%〜+98.4% で超えた。9 対中 6 対が満たされず、3 対が満たしたため、S-1a は不成立である (family p = 1.0)。下段は各セルの 8 標本を全数表示したもので、短い横線が中央値、菱形と誤差棒が標本平均と t 分布による 95% 信頼区間である。下段の平均の信頼区間は標本分布の記述用であり、上段の相対中央値差、判定境界、family 判定のいずれにも用いていない。下段の縦軸は workload ごとに独立なので、パネル間で点の高さや区間の幅を直接比べてはならない。各標本の値は同一セッション内 5 反復の中央値であり、M tps は毎秒 100 万トランザクションを表す。unstable と記録された標本は除外しない契約であり、本図の対象 12 セルには 1 件も無かった。測定条件は Silo、48 スレッド、レコード数 1,000,000、Zipf skew 0.9、read-modify-write 無効、実行時間 3 秒、`clocks_per_us` = 1,800 TSC tick/µs、トレース無効、`numactl --interleave=all`、環境タグ `linux-baremetal`、CCBench commit `d706650`。read 比率だけが workload ごとに異なる (write-heavy 5%、balanced 50%、read-heavy 95%)。測定は `perf stat` 下で最終レベルキャッシュの load misses / loads、instructions、cycles を収集しながら行われた記録であり、そのオーバーヘッドを含む。したがって本図の絶対スループットは論文の headline 値の出所ではなく、現行の同一 campaign 内対測定契約 (D496) を満たすとも主張しない。この限定は凍結済みの S-1a 判定を変更しない。生の追記専用ログ (write-ahead log; WAL) は admission を経た `HISTORICAL_RAW` として verifier epoch E0 で再読し、凍結報告が certified accepted evidence として受理した行と一致するものだけを描いた。判定と p 値は凍結報告から読んでおり、本図の生成器はそれを再計算していない。S-1b は既知軸最良との優劣を問う S-1a とは独立の主張であり、その成立は S-1a の不成立を救わない。

## proof chain

- 図に描いた点 → provenance JSON の `facts.comparisons` (9 対の左右セル・中央値・相対差・判定)
- 図に描いた標本分布 → provenance JSON の `facts.cells` (セルごとの 8 生値・中央値・平均・CI)
- 判定と p 値 → 凍結 report の `comparisons[*].judgment` と `families.s1a`。生成器は再計算しない
- 標本の由来 → admission を経た `HISTORICAL_RAW` view の WAL と、report の
  `hard_gates.certified.accepted_evidence` の全行一致
- 比較定義の由来 → `output/s1-freeze/measurement_freeze.json` (上記の版差つき)
- それらが着地後もずれないこと → `orchestrator/tests/test_s1_9pair_figure_provenance.py`
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

---

# `fig5_a2_certification_reject` — A-2 正式 certification の結果図 (outer `reject`)

## Erratum — この図が比較したのは静的 backoff ではない (2026-09-07 追記、D1645)

**この図を「採用静的 backoff が負けた」という論文の結論に使ってはならない。**
図・キャプション正文・provenance JSON の bytes、描かれた値、outer `reject` はいずれも変更していない
(凍結物であり、絶対規律 7 に従い訂正は追記でのみ行う)。誤っているのは条件の**記述**である。

attempt `t2022-20260828c` の 4 cell は patch が当たっていない stock の CCBench 木で build された。
adopted cell が要求した `BACKOFF_FIXED` (fixed 10 µs / 5 µs) は cmake の argv には渡っている。
届かなかったのではなく、pin `511c9538` の CCBench に `CCBENCH_BACKOFF_FIXED` の定義が木全体のどこにも無いため、
compile definition へ転送されず build の条件にならなかった (F707 の再発)。**この図が実際に比較したのは
`BACK_OFF=1` (CCBench 内蔵の適応 backoff 有効) と `BACK_OFF=0` (無効) である。** 一次資料は当時の WAL の
`build_start` record (`src_token`・`tracked_clean`・空の tracked diff・`tracked_paths`) と、
`build_done` に記録された実 cmake 引数である。

したがって**図中・provenance JSON・凍結キャプション正文に残る cell label (`fixed10` / `fixed5`) は、
要求された genome の名前**であって効いた条件ではない。これらは凍結物なので訂正しない。
下の「何を示す図か」以下の本文はこの erratum に合わせて既に直してある。
`BACK_OFF=1` が有効にする機構は CCBench の `include/backoff.hh` にある適応制御 (スループット勾配で
待機量を固定幅で増減する) であり、指数 backoff ではない。`cmake/Options.cmake` の option 説明文だけが
`exponential backoff on abort` と呼んでいる。

条件の正しい記述と現行の統制稿は `docs/paper-story/results/2026-09-07-a2-certification-reject.md` にある。
論文素材からは、正しい identity で取り直した attempt が出るまで A-2 の結論を外す (D1645)。

## 追補 — 旧 fig5 の用途制限に期限を設けない (2026-09-11、D1936項21・T-2521)

D1936項21に従い、上の Erratum と一覧に残る D1645 の「正しい identity で取り直した attempt が
出るまで」「取り直しまで」という期限を、当該旧 fig5 について外す。**採用静的 backoff に関する
A-2 の結論にも、その結果を示す図にも、この旧図を期限なしで使わない。** 新 attempt が得られても、
旧 attempt `t2022-20260828c` が比較したのは `BACK_OFF` の有効/無効という事実は変わらない。

旧図が示す範囲は、上の Erratum が訂正した当時の測定対象と判定に限る。要求 genome の名である
`fixed10` / `fixed5` を、実際に効いた静的 backoff の条件として引用してはならない。
旧画像・PDF・provenance JSON・統計・凍結稿・キャプション正文と outer `reject` は保持する。
本追補は用途制限の期限だけを当該旧図について改め、測定や判定を更新しない。

## 何を示す図か

A-2 が定義した exact 4 cell — write-heavy (rratio=5) と balanced (rratio=50) の 2 workload × 2 cell —
を、現行 Pegasus・CCBench pin `511c953` の正式 protocol で測った attempt `t2022-20260828c` の結果である。
**各 workload は独立に環境契約された campaign 1 本 (別 request・別 host・別時刻) であり、外側の certification status は
その論理積で決まる** (D1169)。

**cell 名 (`fixed10` / `fixed5`) は要求された genome に由来する名前であって、効いた条件ではない** (上の Erratum)。
実際に効いた条件差は `BACK_OFF` の有効/無効だけである。`BACK_OFF=1` (CCBench 内蔵の適応 backoff 有効) の
median throughput は同一 workload の `BACK_OFF=0` (無効) 対照に対して write-heavy で −46.3902%、
balanced で −65.9080% であり、**外側の status は `reject`** である。
**この図を採用静的 backoff についての結果として読んではならない。**

上段は各 cell の trace-disabled 性能 run 5 標本を全数表示し、短い横線が median、菱形と誤差棒が標本平均と t 分布 95% 信頼区間、
灰色の破線が同一 workload の無 backoff median (効果の分母) である。**平均の信頼区間は標本分布の記述用であり、効果・判定・median の
信頼区間ではない。成果物は有意差判定を持たない。** 下段は WAL に記録された abort 率の集約 1 点/cell で、descriptive な指標であり、
機序の同定には使わない。

**correctness の緑は性能の判定ではない。** 同じ 4 cell の correctness は別の trace-enabled run で 4 cell とも `certified` だったが、
図はそれを「not a performance certification」と一体で表示している。**この図は旧 `linux-baremetal` 系列の反証でも再現失敗でもない**
— 旧系列の値は comparator ではなく、符号差の原因は同定されていない。

**測定条件の関門族 (D1198) は本走行に適用されていない** (2026-09-01 に義務化。本走行は 08-28)。条件の同一性は genome 記録・
build admission receipt・source-routed evidence に依る。status `reject` は当時の protocol 出力として不変である (絶対規律 7)。

## 既存図との関係

| 論点 | 図4 (S-1a 9 対) | 図5 (本図) |
|---|---|---|
| 何の図か | 縮小主張 S' の登録 9 対 (失敗報告) | 正式 certification protocol の結果 (protocol status `reject`) |
| 負の結果の種類 | 既知結果の追試の失敗 | 現行環境での前向きな測定の protocol reject。**両者を畳まない** |
| 判定の出所 | 凍結 report。生成器は再計算しない | 凍結 `certification.json` (SHA-256 で束縛)。生成器は再計算しない |
| 入力 | 凍結 report + campaign 4 件の WAL | tracked `certification.json` / `raw-manifest.json` + repo 外の WAL 2 本 / raw cell JSON 4 本 (SHA-256 で束縛) |
| perf | `perf stat` 下 | **perf 無し**、trace-disabled |
| 絶対 tps の扱い | headline 値の出所にしない | headline 値の出所にしない |

既存の `fig1` / `fig2` / `fig2b` / `fig2c` / `fig3` / `fig4` の bytes は本図の追加で一切変わらない。

## 再現

repo root から、**計測機の外**で次を実行する (FIGURE_CONVENTIONS §7)。durable authority (repo 外) の場所は
環境変数 `IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT` か `--measurement-root` で与える (省略時の既定は同じ path)。

```
IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT=/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c python3 tools/plotting/plot_a2_certification.py docs/paper-story/figures/fig5_a2_certification_reject
```

出力は `.png` (ラスタ) / `.pdf` (ベクター、論文投稿はこちら) / `.provenance.json` の 3 つ。
再現コマンドは provenance JSON の `reproduction` にも記録されている。
図2b・図4 と同じく再現できるのは「値」であって「バイト列」ではない。**着地したバイト列の同一性は provenance JSON が記録した
SHA-256 と `orchestrator/tests/test_plot_a2_certification.py` が守る。** provenance の `generator.sha256` は生成時の bytes の
記録であり、現行 source を縛る pin ではない (`tools/plotting/README.md` の同旨)。

## 入力

- tracked: `output/insights/2026-08-24_paper-story-a2-certification/certification.json` (SHA-256 `f685b40d…bda40`、生成器が literal で照合。
  値は run README `output/insights/2026-08-28_t2022-a2-certification-run/README.md` の記録と一致) と同 dir `raw-manifest.json` (SHA-256 `12d8be7a…a7c35`)。
- repo 外 (durable authority、raw-manifest の `files` が SHA-256 を束縛): `jobs/<rr5|rr50>/campaigns/<campaign>/runs/wal.jsonl` 2 本
  (測定値として読むのは `stage == "bench_done"` の行だけ) と `jobs/<w>/raw/<cell>.json` 4 本。
- 生成器は WAL の 5 生値から median / 平均 / 標準偏差 / 95% CI / cv をその場で再計算し、WAL の `median_tps`・`cv`、raw JSON の
  `samples_tps`、certification の `median_tps`・`effects` と一致しなければ fail-closed で止まる。`outer_status` と `effects` は
  certification からコピーし、生成器は判定を作らない (絶対規律 2、D1074 の限定例外)。

## 作図規約への適合

§1 (WAL の生値からその場で再計算)、§2 (5 反復の t 分布 95% CI)、§3 (無 backoff median の基準線)、§4 (下段は機序を見せる目的でなく
descriptive と明記した別パネル)、§5 (図中用語は最小、展開は caption)、§6 (provenance)、§7 (login node で生成、計測機ではない)、
§8 (matplotlib / numpy のみ)、§9 (保存前・fail-closed の layout check)、§10 (実寸 fixture、本物の Figure を検査へ通す test) を満たす。
判定と効果は凍結 `certification.json` を権威として読む (§1 の限定例外、D1074)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、`orchestrator/tests/test_plot_a2_certification.py` が
本 README への収録と生成器の決定的な組み立てとの一致を検査する。英文で書く (論文の図キャプションとしてそのまま使う想定)。

> Figure 5. A-2 formal certification attempt t2022-20260828c (outer status: reject). The two independent workload campaigns were requests 954194.nqsv on bnode141 at 2026-08-27T20:51:15.094458+00:00 and 954195.nqsv on bnode064 at 2026-08-27T20:52:50.071485+00:00, at distinct recorded times; the outer status is their logical conjunction. The top row shows all five trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff median and the effect denominator. Median effects copied from certification are rr5 fixed 10 us -46.3902% and rr50 fixed 5 us -65.9080%. M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision. Reject is the protocol status based on the predefined median ratio. The bottom row is a descriptive leading indicator: one aggregate abort-rate point per cell, no confidence interval, and no causal mechanism claim. Correctness comes from separate trace-enabled runs: all four cells were certified, but this is not a performance certification. L01 limits that evidence to point-key traces; under D1257 the correctness argv was not independently recorded. The D1198 gate family was not applied to this run. Conditions: 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, five repetitions, CCBench pin 511c953, no perf, trace-disabled performance. Top-row y axes are scaled independently by workload; do not compare panel heights. The older series is not a comparator, and the cause of the sign difference has not been identified.

## proof chain

- 図に描いた標本・median・平均・CI・abort 率 → provenance JSON の `cells` (cell ごとの 5 生値と再計算値) と `artist_series` (描いた線の label↔値↔genome)
- 判定と効果 → 凍結 `certification.json` の `status` / `effects` (provenance の `outer_status` / `effects`)。生成器は再計算せず、`effect_crosschecks` に再計算値との一致を記録
- 標本の由来 → durable authority の WAL `bench_done` と raw cell JSON (provenance の `external_inputs` に root-relative path と SHA-256)
- 入力の束縛 → tracked `raw-manifest.json` の `files` (provenance の `tracked_inputs`)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_a2_certification.py`
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-07-a2-certification-reject.md`
  (2026-09-04 の稿は測定条件の記述を誤っており、append-only の履歴として残る。上の Erratum 節を参照)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

# `fig6_a2_certification_observed_positive` — 正しい identity で取り直した A-2 (outer `observed-positive`)

## 何を示す図か

attempt `t2364-20260907b` (2026-09-07) の 4 cell を描く。D1644 が定めた pin + patch 束縛の
`src_token` で cell の identity を計算する driver で走った、最初の A-2 正式 certification である。

上段は cell ごとの trace-disabled 性能標本 5 点、短い横棒が median、ひし形と誤差棒が標本平均と
t 分布 95% 信頼区間である。灰色の破線は同 workload の no-backoff median であり、効果の分母でもある。
下段は記述的な先行指標として cell あたり 1 点の集計 abort 率を置く。信頼区間は付けず、
因果の機序も主張しない。

## 既存図との関係

**`fig5_a2_certification_reject` の後継図ではない。** 両者は別の attempt であり、
測っている条件が違う。

- `fig5_` の attempt `t2022-20260828c` は patch が当たっていない stock の木で走っており、
  実際に効いた条件差は内蔵 backoff の有効/無効だけだった (D1645、F707 の再発)。
- 本図の attempt `t2364-20260907b` は patch を当てた木で走り、4 cell すべてが
  `source_binding_status=bound`、stock cell は `src_token=stock`、adopted cell は非 `stock` である。

**当時の測定と判定は事実として残る (絶対規律 7)。** 両者を前後比較として読んではならない。
`fig5_` とその provenance・results 稿は 1 byte も変更していない。

## 入力

- 権威 bytes: `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`
  (`paper-story-a2-certification-result/v4`) と同 dir の `raw-manifest.json`
  (`paper-story-a2-full-raw-manifest/v4`)。生成器は repo 所有の pin 表でこの 2 つの SHA-256 を
  照合する。**pin は CLI から渡せない。** 新しい attempt を図にするには pin 表へ entry を足す
  commit が要る。
- 外部入力: attempt `t2364-20260907b` の WAL 2 本、raw cell 4 本、campaign lock 2 本、
  campaign claim 2 本、条件関門の受領証 2 本の計 12 file。root 相対 path と SHA-256 を
  provenance の `external_inputs` に記録する。

## 再現

```bash
python3 tools/plotting/plot_a2_certification.py \
  --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b \
  --certification output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json \
  --raw-manifest output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json \
  docs/paper-story/figures/fig6_a2_certification_observed_positive
```

図番号は出力 prefix の `fig<N>_` から導く。`fig<N>_` の形でない prefix は出力前に拒否する。

## 条件関門についてこの図が言えること

raw manifest は `use_class="paper"` かつ `admitted=true` と記録する canonical な
admission record を 4 cell 分束縛している。**成果物が保存しているのはそこまでで、元の
supply / meaning records は残らない。** したがって caption は「関門を実施し通過した」ではなく
「そう記録された受領証が束縛されている」と書く。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、
`orchestrator/tests/test_plot_a2_certification.py` が本 README への収録と生成器の決定的な
組み立てとの一致を検査する。英文で書く。

> Figure 6. A-2 formal certification attempt t2364-20260907b (outer status: observed-positive). The independent workload campaigns were request 981476.nqsv on bnode077 at 2026-09-07T12:12:55.607184+00:00 and request 981477.nqsv on bnode085 at 2026-09-07T12:12:55.388302+00:00, at distinct recorded times; the outer status is their logical conjunction. The top row shows all five trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff median and the effect denominator. Median effects copied from certification are write-heavy (rr5) fixed 10 us 63.5485% and balanced (rr50) fixed 5 us 14.4213%. M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision. The displayed outer status is the protocol status based on the predefined median ratios. The bottom row is a descriptive leading indicator: one aggregate abort-rate point per cell, no confidence interval, and no causal mechanism claim. Correctness comes from separate trace-enabled runs: all 4 cells were certified, but this is not a performance certification. L01 limits that evidence to point-key traces; under D1257 the correctness argv was not independently recorded. The raw manifest binds canonical condition-admission records reporting use_class="paper" and admitted=true for all 4 policy cells; the original supply and meaning records are not retained in this artifact. Conditions: 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, CCBench pin 511c953, no perf, trace-disabled performance. Top-row y axes are scaled independently by workload; do not compare panel heights. The older series is not a comparator, and the cause of the sign difference has not been identified.

## proof chain

- 図に描いた標本・median・平均・CI・abort 率 → provenance JSON の `cells` と `artist_series`
- 判定と効果 → `certification.json` の `status` / `effects`。生成器は再計算せず、
  `effect_crosschecks` に再計算値との一致を記録する (rr5 / rr50 とも `authority_matches` が真)
- 標本の由来 → durable authority の WAL `bench_done` と raw cell JSON
  (provenance の `external_inputs` に root 相対 path と SHA-256)
- 入力の束縛 → tracked `raw-manifest.json` の `files` (provenance の `tracked_inputs`)
- source identity → 受領証 / raw / WAL / certification の 4 者で `src_token` が一致すること、
  stock cell は `stock`、adopted cell は非 `stock` であること
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_a2_certification.py`
- 結果節・表・限定の材料 →
  `docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md`
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

---

# `fig7_a2_builtin_backoff_onoff_reject` — 旧 A-2 attempt の条件記述を訂正した図 (outer `reject`)

## 何を示す図か

attempt `t2022-20260828c` (2026-08-28) の exact 4 cell を描く。**`fig5_a2_certification_reject` と
同じ測定・同じ値・同じ外側 status であり、違うのは条件の記述だけである。**

この attempt は patch が当たっていない stock の CCBench 木で走っており、adopted cell が要求した
`BACKOFF_FIXED` (fixed 10 µs / 5 µs) は cmake の argv には渡ったものの、pin `511c9538` の CCBench に
対応する option 定義が無いため compile definition にならなかった (F707 の再発)。**実際に効いた条件差は
`BACK_OFF` の 0/1 だけである。** `BACK_OFF=1` が有効にするのは `include/backoff.hh` の適応制御
(スループット勾配で待機量を固定幅で増減する) であって、指数 backoff ではない。

したがって本図は x 軸を `BACK_OFF=0` / `BACK_OFF=1`、軸名を
`CCBench built-in adaptive backoff` と表示し、caption も同じ条件対で書く。

上段は cell ごとの trace-disabled 性能標本 5 点、短い横棒が median、ひし形と誤差棒が標本平均と
t 分布 95% 信頼区間である。灰色の破線は同 workload の no-backoff median であり、効果の分母でもある。
下段は記述的な先行指標として cell あたり 1 点の集計 abort 率を置く。信頼区間は付けず、
因果の機序も主張しない。**backoff 有効側で abort 率が下がりながら throughput も下がっている、
という並びを機序の説明として読んではならない。**

## この図を使ってよい範囲・使ってはならない範囲

- **使ってよい:** 当時の測定が何を比較したかの記述、および「内蔵の適応 backoff を有効にすると
  この 2 workload では throughput が下がり、外側 protocol status は `reject` だった」という
  歴史記録の説明。
- **使ってはならない:** 採用静的 backoff についての結果・結論 (D1936 項21・D1993 決定 5 は
  期限なしでこれを禁じる)。本図は番号を変えた旧図の複製ではなく条件記述の訂正版だが、
  **禁じられている用途が復活するわけではない。**
- 論文の A-2 の結論そのものは、正しい identity で取り直した attempt `t2364-20260907b` を描く
  `fig6_a2_certification_observed_positive` が担う (D1993 決定 1)。

## 既存図との関係

- **`fig5_a2_certification_reject` の bytes は 1 byte も変えていない。** 訂正は追記でのみ行う
  (絶対規律 7)。旧図・旧 provenance・旧キャプション正文と、それらを記録した
  append-only の results 稿はそのまま残る。生成器は凍結 prefix の列挙
  (`FROZEN_LEGACY_CAPTION_PREFIXES`) に載る出力名のときだけ旧文言と旧目盛を返す。
  **legacy 権威 bytes から作る図の既定は訂正後の条件記述である。**
- **`fig6_a2_certification_observed_positive` の後継でも前身でもない。** fig6 は別の attempt
  (`t2364-20260907b`) で別の条件を測っている。両者を前後比較として読んではならない。
- 値・median・効果・outer status・cell identity は fig5 と同一である。生成器は判定を再計算しない。

## 入力

- 権威 bytes: `output/insights/2026-08-24_paper-story-a2-certification/certification.json`
  (`paper-story-a2-certification-result/v3`) と同 dir の `raw-manifest.json`
  (`paper-story-a2-raw-manifest/v3`)。fig5 と同じ bytes であり、生成器は repo 所有の pin 表で
  SHA-256 を照合する。**pin は CLI から渡せない。**
- 条件記述の出所: `docs/paper-story/results/2026-09-07-a2-certification-reject.md`。
  provenance の `tracked_inputs` に `kind: "caption_source"` として SHA-256 つきで記録する。
  `authority_scope` は `condition description only; not measurement values or protocol status`
  であり、**測定値と protocol status の権威ではない。** 同稿は自身を凍結物と宣言している。
- 外部入力: attempt `t2022-20260828c` の WAL 2 本と raw cell 4 本。root 相対 path と SHA-256 を
  provenance の `external_inputs` に記録する。

## 再現

repo root から、**計測機の外**で次を実行する (FIGURE_CONVENTIONS §7)。

```bash
python3 tools/plotting/plot_a2_certification.py \
  --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c \
  --certification output/insights/2026-08-24_paper-story-a2-certification/certification.json \
  --raw-manifest output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json \
  docs/paper-story/figures/fig7_a2_builtin_backoff_onoff_reject
```

図番号は出力 prefix の `fig<N>_` から導く。再現できるのは「値」であって「バイト列」ではない。

## 作図規約への適合

`FIGURE_CONVENTIONS.md` の §2 (反復があれば不確かさを描く)、§3 (ベースラインは基準線)、
§6 (provenance を刻む)、§7 (計測機の外)、§9 (保存前に重なりを機械検査し、重なれば出力せず落とす)
に従う。§9 の検査は `check_figure_layout` が担い、訂正後の目盛文言でも通ることを
`orchestrator/tests/test_plot_a2_certification.py` が検査する。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、
`orchestrator/tests/test_plot_a2_certification.py` が本 README への収録と生成器の決定的な
組み立てとの一致を検査する。英文で書く。

> Figure 7. A-2 formal certification attempt t2022-20260828c (outer status: reject). The two independent workload campaigns were requests 954194.nqsv on bnode141 at 2026-08-27T20:51:15.094458+00:00 and 954195.nqsv on bnode064 at 2026-08-27T20:52:50.071485+00:00, at distinct recorded times; the outer status is their logical conjunction. The top row shows all five trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff median and the effect denominator. Median effects copied from certification are rr5 CCBench built-in adaptive backoff enabled (BACK_OFF=1) versus disabled (BACK_OFF=0) -46.3902% and rr50 CCBench built-in adaptive backoff enabled (BACK_OFF=1) versus disabled (BACK_OFF=0) -65.9080%. The labels fixed 10 us / fixed 5 us and cell IDs rr5-fixed10 / rr50-fixed5 identify requested genomes, not effective conditions; BACKOFF_FIXED did not affect the build. BACK_OFF=1 enables CCBench built-in adaptive control, not exponential backoff. M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision. Reject is the protocol status based on the predefined median ratio. The bottom row is a descriptive leading indicator: one aggregate abort-rate point per cell, no confidence interval, and no causal mechanism claim. Correctness comes from separate trace-enabled runs: all four cells were certified, but this is not a performance certification. L01 limits that evidence to point-key traces; under D1257 the correctness argv was not independently recorded. The D1198 gate family was not applied to this run. Conditions: 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, five repetitions, CCBench pin 511c953, no perf, trace-disabled performance. Top-row y axes are scaled independently by workload; do not compare panel heights. The older series is not a comparator, and the cause of the sign difference has not been identified.

## proof chain

- 図に描いた標本・median・平均・CI・abort 率 → provenance JSON の `cells` と `artist_series`
- 判定と効果 → `certification.json` の `status` / `effects`。生成器は再計算せず、
  `effect_crosschecks` に再計算値との一致を記録する
- 標本の由来 → durable authority の WAL `bench_done` と raw cell JSON
  (provenance の `external_inputs` に root 相対 path と SHA-256)
- 入力の束縛 → tracked `raw-manifest.json` の `files` (provenance の `tracked_inputs`)
- 条件記述の出所 → `tracked_inputs` の `caption_source` 行 (SHA-256 で束縛)
- 効いた条件が `BACK_OFF` だけであることの根拠 → WAL `build_start` の `src_token` /
  `tracked_clean` / 空の tracked diff / `tracked_paths` と、`build_done` の実 cmake 引数、
  および pin `511c9538` の CCBench 全木検索 (`CCBENCH_BACKOFF_FIXED` は 0 件)。
  逐語は `docs/paper-story/results/2026-09-07-a2-certification-reject.md` §1
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_a2_certification.py`
- 用途制限 → D1936 項21、D1993 決定 5
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`
---

# `fig8_b10_static_tail_not_observed` — B-10 静的 backoff 右 tail の 09-15 正式 cohort (集団判定 `not-observed-in-any-workload`)

## 何を示す図か

事前登録 `docs/b10-backoff-static-tail-preregistration.md` §4.1 の格子 (右 tail 7 点 1250 / 1768 / 2500 /
3535 / 5000 / 7070 / 9999 マイクロ秒 + 境界参照 1000) × 3 workload の 09-15 正式 cohort
(group `b10-backoff-grid-20260915T061814Z-545445`) を描く**記述図**である。上段は throughput の 5 反復平均と
t 分布 95% 信頼区間、下段は整数カウンタから全精度で再計算した abort 率の 5 反復平均と同じ区間。下段で
隣接する tail 点を結ぶ線分は集団報告の区間分類 (`workloads[].intervals[].state`) で描き分け、3 workload
× 6 = 18 区間すべてが `declining` である。境界参照 1000 は同一 job 内で測るが区間集合に入らないので、
中抜き marker で区別し線で結ばない。

**言い方は事前登録 §4.5 の固定表現に限る。** 図と caption が言うのは「この事前登録の述語では、表現可能域で
ある 9999 マイクロ秒までに飽和を観測しなかった」までであり、「飽和しない」「飽和点が存在しない」とは
書かない。9999 は物理的な限界ではなく符号化の上限である。**性能は未認証 (`performance_certified: false`)**
で、この図を variant 採用の根拠にしない (絶対規律 2)。機序は言わない (D1678 / D1724)。図が支えるのは
B-10 の記述的な費用併記 (同じ格子上の throughput) と域内非飽和であって、主張ではない。

## 既存図との関係

- **`fig2c_b10_extended_backoff` の続きではない。** fig2c は別 cohort (group
  `b10-backoff-grid-20260826T234647Z-783837`、0〜1000 マイクロ秒の拡張格子、`perf stat` 下) であり、
  本図は別格子・別 cohort・別 report schema (`t2500-backoff-static-tail-formal-report/v1`、perf 無し) である。
  同じ軸へ畳まず、fig2c を右 tail の図として引かない。
- 探索走 `t2418-explore` (2000 / 4000 / 9999) と `t2266-tail` v2 系列 (150〜1000) の標本は入っていない。
  9999 も本 cohort で新規に測り直した値である。
- **2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637: 一次資料は共有し、数値と図は共有しない)。

## 入力

- 権威 bytes (repo 外、root `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/`):
  `group-report-20260915/t2500-backoff-static-tail-formal.json` (集団報告)、同 `.dat` (rep 単位の生値 120 行)、
  同 `-complete.json` (完了記録。上 2 件の SHA-256 を `artifacts` に束縛)。生成器は repo 所有の pin 表で
  3 件の SHA-256 を照合する。**pin は CLI から渡せない。** SHA-256 の値は
  `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` §4.1 と同じで、
  `orchestrator/tests/test_plot_b10_static_tail_formal.py` が両者の一致を検査する。
- group id は JSON の top-level に無く、`campaigns[].admission.campaign_path` (絶対 path) に
  `/<group>-<workload>/campaigns/` として含まれる。生成器はその包含を検査する。
- 判定 (`verdict`、workload の `state`、区間の `state` / `qhat` / `qL` / `qU` / `L` / `U`) は集団報告から
  コピーし、生成器は再計算しない (`L = 1 − 2^qU` と `U = 1 − 2^qL` の一致だけを検査する)。
  平均・t 分布 95% 信頼区間・abort 率・変動係数・端点比は reps の生値から再計算する。そのうち
  集団報告の `statistics` と fail-closed で照合するのは平均 2 種 (throughput / abort 率)・変動係数 2 種・
  abort 率の標本標準偏差であり、信頼区間と端点比は再計算だけで照合相手を持たない。

## 再現

```bash
python3 tools/plotting/plot_b10_static_tail_formal.py \
  --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal \
  docs/paper-story/figures/fig8_b10_static_tail_not_observed
```

図番号は出力 prefix の `fig<N>_` から導く。`fig<N>_` の形でない prefix は出力前に拒否する。
生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font
解決に依存する。着地したバイト列の同一性は provenance JSON が記録した `outputs[].sha256` と
`test_landed_fig8_repo_closure_and_caption_when_present` が守る。生成器の `generator.sha256` は生成時点の
記録であり、現行 source を縛る pin ではない。

## 作図規約への適合

- §1: 数値は `.dat` / JSON の reps からその場で再計算 (集団報告の `statistics` は相互検算にだけ使う)。
- §2: 5 反復の平均と t 分布 95% 信頼区間を上段・下段とも描く。
- §6: provenance に入力 3 file の root 相対 path と SHA-256、group id、campaign id・lock digest・WAL SHA-256・job id、
  測定条件、24 cell の生値と統計、区間分類のコピー、caption、展開済み再現 argv を記録する。
- §9: 保存前に renderer-backed layout check を走らせ、text の重なり・逸脱があれば 3 成果物を 1 つも出さない。
- §10: 単体テストの fixture は実寸 (3 workload × 8 点 × 5 反復、`.dat` 120 行、区間 6 × 3) で、本物の
  matplotlib Figure を layout check へ通す。実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、
`orchestrator/tests/test_plot_b10_static_tail_formal.py` が本 README への収録と生成器の決定的な組み立てとの
一致を検査する。英文で書く。

> Figure 8. B-10 static-backoff right tail, formal cohort of 2026-09-15 (group b10-backoff-grid-20260915T061814Z-545445; aggregate verdict not-observed-in-any-workload; performance_certified: false). Columns show write-heavy (rr5), balanced (rr50) and read-heavy (rr95), each an independent campaign (job IDs, respectively: 0:998865.nqsv, 0:998866.nqsv, 0:998867.nqsv). The x axis shows seven tail points (1250, 1768, 2500, 3535, 5000, 7070 and 9999 us; filled markers) and the 1000 us boundary reference (open marker), measured in the same job but excluded from the interval set. The top row shows means of five trace-disabled repetitions with t-distribution 95% confidence intervals (error bars). M tps means million transactions per second. The bottom row shows abort rates recomputed for each repetition from integer counters as aborts / (aborts + commits), averaged over five repetitions with the same confidence intervals. Segments between adjacent tail points are colored by the interval state copied from the group report: 18/18 intervals (6 per workload) are declining; simultaneous lower bounds L on the per-doubling decrease range from 0.2738 to 0.3704 (Bonferroni over 36 one-sided limits, familywise 0.05). Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of the current encoding. 9999 us is not a physical limit. From 1250 to 9999 us the mean throughput falls to 0.444, 0.481 and 0.400 of its 1250 us value (write-heavy, balanced, read-heavy) while the abort rate keeps decreasing. This figure is a descriptive accounting of that cost; it makes no mechanism claim and no adoption decision. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, silo, CCBench pin 511c953, no perf, trace-disabled performance. Correctness comes from separate trace-enabled runs under the recorded legacy check configuration, not the performance configuration: all 120 records were certified with 0 anomalies; certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification. Panel heights and slopes use workload-local y scales and must not be compared across panels. This cohort is a different grid and a different cohort from fig2c and is not a continuation of it. No samples from the exploratory run t2418-explore or the t2266-tail series are included; 9999 us was newly measured in this cohort.

## proof chain

- 図に描いた平均・信頼区間・abort 率 → provenance JSON の `workloads[].cells[]` と `artist_series`
- 区間分類と集団判定 → 集団報告 JSON の `workloads[].intervals[].state` / `verdict`。生成器は再計算せず、
  `L = 1 − 2^qU` と `U = 1 − 2^qL` の一致だけを検査する
- 標本の由来 → 集団報告 `.dat` の 120 行と JSON の `campaigns[].points[].reps[]` (provenance の `external_inputs` に
  root 相対 path と SHA-256)
- 入力の束縛 → `-complete.json` の `artifacts` (json / dat の SHA-256) と生成器の pin 表、results 稿 §4.1 の表
- 正しさの記録 → JSON の `campaigns[].points[].correctness[]` (120 記録 `certified`・anomaly 0。性能の認証ではない)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_b10_static_tail_formal.py`。着地後の closure 検査
  (`validate_repo_closure`) が見るのは、着地 PNG / PDF の SHA-256・pin 表・provenance に保存した cells からの
  artist / caption の再投影であって、reps からの再計算ではない。値の独立な再計算は同 test の実データ読込
  (`test_real_root_loads_and_matches_results_document_when_present`、root が読めるときだけ走る) と、
  results 稿 §2.3 の表との照合が担う
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`
- 事前登録 → `docs/b10-backoff-static-tail-preregistration.md` (§4.1 格子、§4.4 判定、§4.5 固定表現)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 追補 — 再現欄付きの後継図 fig8b (2026-09-20、[T-2793])

事前登録 2026-09-19 追記 項 2 (D2157) が求める「fig8 の再現欄」は、後継図 `fig8b_b10_static_tail_cohort2` (次節) が持つ。同図は本図と同じ cohort 1 を上 block に、独立再現 cohort 2 を下 block に区別して併記し、合成しない。**本節の既存本文と本図の凍結 3 成果物 (PNG / PDF / provenance JSON) は保持し、後継図への案内をここに追記するだけである** (bytes は 1 byte も変えていない)。cohort 1 だけを示すときは引き続き本図を使う。

# `fig8b_b10_static_tail_cohort2` — B-10 静的 backoff 右 tail: 主結果 cohort 1 と独立再現 cohort 2 の併記 (fig8 の後継図、再現欄付き)

## 何を示す図か

事前登録 `docs/b10-backoff-static-tail-preregistration.md` §4.1 の格子 (右 tail 7 点 + 境界参照 1000) × 3 workload を、
**主結果 cohort 1** (group `b10-backoff-grid-20260915T061814Z-545445`、2026-09-15 完走) と **独立再現 cohort 2** (group
`b10-backoff-grid-20260919T131526Z-2235286`、2026-09-19 完走) について**縦 2 block で区別して併記**する記述図である。上 block (2 行) が
cohort 1、下 block (2 行) が cohort 2 で、各 block の上段は throughput の 5 反復平均と t 分布 95% 信頼区間、下段は整数カウンタから全精度で
再計算した abort 率の 5 反復平均と同じ区間、区間線は各 cohort の集団報告の区間分類 (`workloads[].intervals[].state`) で描き分ける。
両 cohort とも 3 workload × 6 = 18 区間すべてが `declining`、集団 verdict は `not-observed-in-any-workload` である。y 軸は workload-local
かつ cohort-local で、panel 間でも block 間でも高さ・傾きを比べない。

**この図は fig8 に事前登録 2026-09-19 追記 項 2 (D2157) が求める「再現欄」を足した後継図である。** cohort 1 の判定・稿・図 (fig8) は
凍結物のまま改めず、cohort 2 の verdict を主結果と区別して併記する。**2 つの cohort を合成しない**: 標本・区間推定・verdict をまたいで
プール推定・統合 verdict・cohort をまたぐ有意水準を作らず、2 つの cohort の数値の近さを再現精度・一致度として評価しない (同追記 項 3、
cohort2 稿 §2.6)。

**言い方は事前登録 §4.5 の固定表現に限る。** 図と caption が言うのは「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに
飽和を観測しなかった」が、独立な 2 つの cohort のそれぞれについて成り立つ、までであり、「飽和しない」「飽和点が存在しない」
「再現されたので飽和しない」とは書かない (同追記 項 7)。**性能は未認証 (`performance_certified: false`)** で、この図を variant 採用の
根拠にしない (絶対規律 2)。機序は言わない (D1678 / D1724)。

## 再現欄 — 主結果と独立再現の束縛

| 欄 | 主結果: cohort 1 (上 block) | 独立再現: cohort 2 (下 block) |
|---|---|---|
| group id | `b10-backoff-grid-20260915T061814Z-545445` | `b10-backoff-grid-20260919T131526Z-2235286` |
| 完走 (JST) | 2026-09-15 | 2026-09-19 |
| job | `0:998865.nqsv` / `0:998866.nqsv` / `0:998867.nqsv` | `0:10752.nqsv` / `0:10753.nqsv` / `0:10754.nqsv` |
| 事前登録の束縛 | commit `cad6f46d86ae4dc31edadfbdfad39c65ed73d70a`、blob `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` | commit `8737cacb4bd286eb3e0784d16dba6eb85e5d6eab`、blob `8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e` |
| spec SHA-256 | `08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef` | `08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef` (同一) |
| 集団 verdict | `not-observed-in-any-workload` | `not-observed-in-any-workload` |
| 区間分類 | 18 区間すべて `declining` | 18 区間すべて `declining` |
| `performance_certified` | `false` | `false` |
| 正しさ | 120 記録 certified・anomaly 0 (trace 有効の別走行) | 120 記録 certified・anomaly 0 (trace 有効の別走行) |
| 集団報告 (repo 外、root `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/`) | `group-report-20260915/t2500-backoff-static-tail-formal.json` (`5f426ecbc16132048cf0c73eaf6960a395ec821a9f48cc04a83a787dceec8b28`)、同 `.dat` (`758b3121cebf7562315a8a70d1f305ced678f90b393fc3cd2a4af87ca0c71c44`)、同 `-complete.json` (`7192d1da0b4a032251a0e270ec60910a118a5f75844dc9276a6fba00a682d08c`) | `group-report-20260919-cohort2/t2500-backoff-static-tail-formal.json` (`932f6cccbf1a4be2ccbd4c11af31fe2a402b26fc352eb05e22b87b14cef504fd`)、同 `.dat` (`15b99944b8429c0c2bb0d36d4498c7ab2a57d3f90c97d2430f34838905881fd6`)、同 `-complete.json` (`934211874c779c7bfbffd9a596ef9b7094b7bfa2f7a660203065759abf59420c`) |
| 稿 | `results/2026-09-16-b10-static-tail-not-observed.md` | `results/2026-09-19-b10-static-tail-cohort2.md` (§2.6 が同じ表を持つ) |
| 単独の図 | `fig8_b10_static_tail_not_observed` (凍結、bytes 不変) | 無い (本図の下 block が cohort 2 の唯一の図) |

## 既存図との関係

- **`fig8_b10_static_tail_not_observed` の後継図。** 上 block は fig8 と同じ集団報告 (同じ pin) から同じ計算で描いた cohort 1 であり、
  fig8 の 3 file の bytes は 1 byte も変えていない。論文で再現欄付きの図を使うときは本図を使い、cohort 1 だけを示すときは fig8 を使う。
- **`fig2c_b10_extended_backoff` の続きではない** (別格子・別 cohort・別 report schema、fig8 節と同じ)。探索走 `t2418-explore` と
  `t2266-tail` 系列の標本は入っていない。
- **2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637)。

## 入力

- 権威 bytes (repo 外): 上の再現欄の表の 6 file。生成器は cohort ごとの repo 所有 pin 表 (`COHORTS[1]` / `COHORTS[2]` の `pinned_sha256`)
  で SHA-256 を照合する。**pin は CLI から渡せない。** cohort 2 の値は cohort2 稿 §4.1 と同じで、
  `orchestrator/tests/test_plot_b10_static_tail_formal.py` が両稿との一致を検査する。
- 役割 (cohort 1 = primary、cohort 2 = reproduction) と順序は生成器の定数で固定され、CLI (`--reproduction-cohort` は `2` だけを受理) からも
  provenance の改変からも入れ替えられない。
- 判定 (`verdict`、workload の `state`、区間の `state` / `qhat` / `qL` / `qU` / `L` / `U`) は各 cohort の集団報告からコピーし、生成器は
  再計算しない。平均・信頼区間・abort 率は各 cohort の reps から再計算し、集団報告の `statistics` と fail-closed で照合する (fig8 と同じ)。

## 再現

```bash
python3 tools/plotting/plot_b10_static_tail_formal.py \
  --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal \
  docs/paper-story/figures/fig8b_b10_static_tail_cohort2 \
  --reproduction-cohort 2
```

`--reproduction-cohort` を省くと現行どおり cohort 1 だけの図 (fig8 の形) を出す。図番号は出力 prefix の `fig<N>_` (英字 suffix は本経路だけが
受理) から導く。生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font 解決に依存する。着地したバイト列の
同一性は provenance JSON が記録した `outputs[].sha256` と `test_landed_fig8b_repo_closure_and_caption_when_present` が守る。生成器の
`generator.sha256` は生成時点の記録であり、現行 source を縛る pin ではない (規律 7)。

## 作図規約への適合

- §1: 数値は各 cohort の `.dat` / JSON の reps からその場で再計算 (集団報告の `statistics` は相互検算にだけ使う)。
- §2: 5 反復の平均と t 分布 95% 信頼区間を全 panel に描く。
- §4: 2 cohort を同一 panel に重ねない (縦 2 block)。
- §6: provenance (schema v2) に cohort ごとの入力 3 file の root 相対 path と SHA-256、group id、campaign id・lock digest・WAL SHA-256・job id、
  測定条件、24 cell の生値と統計、区間分類のコピー、`artist_series` (cohort 別)、caption、展開済み再現 argv を記録する。top-level に
  cohort をまたぐ統計 field は無い (`claim_boundary.cohorts_pooled: false`)。
- §9: 保存前に renderer-backed layout check (12 axes、block 見出しの panel 侵入検査を含む) を走らせ、違反があれば 3 成果物を 1 つも出さない。
- §10: 単体テストの fixture は実寸 (2 cohort × 3 workload × 8 点 × 5 反復) で、本物の matplotlib Figure を layout check へ通す。
  実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、`orchestrator/tests/test_plot_b10_static_tail_formal.py` が本 README への
収録と生成器の決定的な組み立てとの一致を検査する。英文で書く。

> Figure 8b. B-10 static-backoff right tail: primary result, formal cohort 1 of 2026-09-15 (group b10-backoff-grid-20260915T061814Z-545445; aggregate verdict not-observed-in-any-workload; preregistration commit cad6f46d8), and independent reproduction, cohort 2 of 2026-09-19 (group b10-backoff-grid-20260919T131526Z-2235286; aggregate verdict not-observed-in-any-workload; preregistration commit 8737cacb4); same spec SHA-256; performance_certified: false for both cohorts. The upper block (two rows) draws cohort 1 and the lower block draws cohort 2. Each cohort has separate samples and separate estimates; y scales are cohort-local. Columns show write-heavy (rr5), balanced (rr50) and read-heavy (rr95), each an independent campaign (job IDs cohort 1: 0:998865.nqsv, 0:998866.nqsv, 0:998867.nqsv; cohort 2: 0:10752.nqsv, 0:10753.nqsv, 0:10754.nqsv). Within each block, the upper row shows means of five trace-disabled repetitions with t-distribution 95% confidence intervals (error bars). M tps means million transactions per second. Within each block, the lower row shows abort rates recomputed for each repetition from integer counters as aborts / (aborts + commits), averaged over five repetitions with the same confidence intervals. The x axis shows seven tail points (1250, 1768, 2500, 3535, 5000, 7070 and 9999 us; filled markers) and the 1000 us boundary reference (open marker), measured in the same job but excluded from the interval set. In cohort 1, segments between adjacent tail points are colored by the interval state copied from its group report: 18/18 intervals (6 per workload) are declining; simultaneous lower bounds L on the per-doubling decrease range from 0.2738 to 0.3704 (Bonferroni over 36 one-sided limits, familywise 0.05 within this cohort). In cohort 2, segments between adjacent tail points are colored by the interval state copied from its group report: 18/18 intervals (6 per workload) are declining; simultaneous lower bounds L on the per-doubling decrease range from 0.2782 to 0.3732 (Bonferroni over 36 one-sided limits, familywise 0.05 within this cohort). The fixed wording applies to each cohort separately: Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of the current encoding. 9999 us is not a physical limit. The second cohort returning the same aggregate verdict is reported as such and is not read as anything beyond the fixed wording above. In cohort 1, from 1250 to 9999 us the mean throughput falls to 0.444, 0.481 and 0.400 of its 1250 us value (write-heavy, balanced, read-heavy) while the abort rate keeps decreasing. In cohort 2, from 1250 to 9999 us the mean throughput falls to 0.445, 0.484 and 0.398 of its 1250 us value (write-heavy, balanced, read-heavy) while the abort rate keeps decreasing. The two cohorts are not pooled: no combined estimate, no combined verdict and no cross-cohort significance level are formed, and the closeness of the two cohorts' values is not evaluated as reproduction accuracy or agreement. This figure is a descriptive accounting of that cost; it makes no mechanism claim and no adoption decision. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, silo, CCBench pin 511c953, no perf, trace-disabled performance. Correctness comes from separate trace-enabled runs under the recorded legacy check configuration, not the performance configuration (cohort 1: all 120 records were certified with 0 anomalies; cohort 2: all 120 records were certified with 0 anomalies); certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification. Panel heights and slopes use workload-local y scales and must not be compared across panels. The two cohort blocks also use cohort-local y scales and are not to be compared for shape or slope. These cohorts use a different grid and are different cohorts from fig2c and are not a continuation of it. No samples from the exploratory run t2418-explore or the t2266-tail series are included; 9999 us was newly measured in each cohort.

## proof chain

- 図に描いた平均・信頼区間・abort 率 → provenance JSON の `cohorts[].workloads[].cells[]` と `artist_series` (cohort 別)
- 区間分類と集団判定 → 各 cohort の集団報告 JSON の `workloads[].intervals[].state` / `verdict` (コピー)
- 標本の由来 → 各 cohort の集団報告 `.dat` の 120 行と JSON の `campaigns[].points[].reps[]` (provenance の `cohorts[].external_inputs`)
- 入力の束縛 → 各 `-complete.json` の `artifacts` と生成器の cohort 別 pin 表、両稿 §4.1 の表
- 主結果と独立再現の地位 → 事前登録 2026-09-19 追記 (項 1〜7)、D2157、cohort2 稿 §2.6
- 正しさの記録 → 各 JSON の `campaigns[].points[].correctness[]` (cohort ごとに 120 記録 `certified`・anomaly 0。性能の認証ではない)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_b10_static_tail_formal.py`。着地後の closure 検査 (`validate_repo_closure`、
  schema v2) が見るのは、着地 PNG / PDF の SHA-256・cohort 別 pin 表・役割と順序・provenance に保存した cells からの artist / caption の
  再投影であって、reps からの再計算ではない。値の独立な再計算は同 test の実データ読込 (root が読めるときだけ走る) と両稿 §2.3 の表との
  照合が担う
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md` (§2.6 再現欄、§3 限定) と
  `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`
- 事前登録 → `docs/b10-backoff-static-tail-preregistration.md` (§4.1 格子、§4.4 判定、§4.5 固定表現、2026-09-19 追記)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 言わないこと

- 「1 ページに入る」は主張しない。描画寸法は 7.2 × 10.6 in (4 行 × 3 列) で、掲載時の縮小と可読性は投稿テンプレートで確かめる。
- 2 つの cohort の値の近さを一致度・再現精度として評価しない。第 3 cohort の実施・地位は定めない。

# `fig9_a1_balanced5_sized_attempt1` — A-1 balanced5 sized 本走 attempt-0001 の対差平均 ± 登録済み区間 (非認証 lane の記述図)

## 何を示す図か

study `paper-story-a1-20260901-balanced5-sized-v1` の sized 本走 attempt-0001 (2026-09-18、job `4939.nqsv` / `4940.nqsv` /
`4941.nqsv`、各 30 対 × 2 arm) について、3 workload (write-heavy rr5: `fixed10` − `no-backoff`、balanced rr50: `fixed5` −
`no-backoff`、read-heavy rr95: `fixed2` − `no-backoff`) の**記述図**である。各 panel は x = pair index (0〜29)、y = 対差
(variant − baseline、M tps) で、30 対の差を open marker、対差の算術平均を実線、登録済み区間 (平均 ± h、`h = k·s/√n`、
`k = 2.8315526875186725`、df 29) を帯、0 を細い実線、登録済み床 ±B (B = baseline arm 平均の 3 %) を破線で描く。
y は workload ごとの尺度で、panel 間で高さを比べない。

**この lane は `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` である。**
登録済み解析の分類は 3 workload とも `resolved-above-floor` (対差平均の符号は write-heavy 正 / balanced 正 / read-heavy 負、
`variance_plan_breach` は 3 本とも false) だが、これは事前登録した分類規則の descriptive な出力であって、仮説検定でも
性能認証でもない。図と caption が言うのは「この attempt でこの値だった」までで、**headline 値・workload 横断の結論・C1 の
再現判定にせず、単一 attempt を反復間の安定性へ一般化しない。A-1 の充足・formal 化・再投入・再認可は判定しない**
(認可はユーザー手番、D2044 項 8 / D2120 項 3)。図を variant 採用の根拠にしない (絶対規律 2)。

## 既存図との関係

- 既存図 (fig1〜fig8) のいずれの後継でもない独立した新図。A-2 / A-6 の結果図 (fig5〜fig7) は median 比 (5 標本) の
  certification protocol、本図は 30 対の対差平均の descriptive lane で、推定量も protocol も違う。プールしない (D1993 項 6)。
- pilot (2026-09-01、60 対) の観測値は入っていない (反復数の決定にだけ使われた。事前登録 §7.2)。
- **2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637)。

## 入力

- 権威 bytes (repo 内、tracked): `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` の `result.json` (統計と 30 対の生値、
  arm の `correctness_evidence`)、`receipt.json` (job / host)、`.complete.json` (3 file の SHA-256 map) と、policy
  `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` (k / df / planned sigma / arm / `authority`)。生成器は repo 所有の
  pin 表で 4 件の SHA-256 を照合する。**pin は CLI から渡せない。** SHA-256 の値は
  `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` §5.1 と同じで、
  `orchestrator/tests/test_plot_a1_sized_paired.py` が両者の一致を検査する。
- 統計 (mean / variance / sd / h / baseline mean / B / 区間) は `statistics.pairs` の 30 対から生成器が再計算し、`statistics` の
  記録値と fail-closed で照合する。分類 (`classification`) は記録値をコピーし、述語 (`abs(mean) − h > B` → resolved-above-floor /
  `abs(mean) + h ≤ B` → bounded-below-floor / それ以外 unresolved) との一致だけを検査する。`variance_plan_breach` も検算する。
- 拒否条件: SHA-256 不一致、`formal` が false 以外、`promotion_prohibited` が true 以外、`valid` が true 以外、`errors` 非空、
  n ≠ 30、対の差が `variant − baseline` と不一致、`pairs[i]` と `raw_tps[i]` の不一致、genome 不一致、統計の不一致、分類の
  述語不一致、`variance_plan_breach` true、両 arm の `correctness_evidence.certified` が `[true]` 以外または `verify_configs`
  が `["legacy"]` 以外、policy SHA-256 と `policy_sha256` の不一致、caption_source (results 稿) の不在。いずれでも成果物を出さない。
- **caption_source:** provenance の `tracked_inputs` に `kind: "caption_source"` として results 稿
  `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` の path と SHA-256 を記録する
  (`authority_scope` = 限定と条件の言い方の出所であって、数値・分類の出所ではない)。稿は provenance の SHA-256 を持たない
  (F36 の自己参照回避)。稿は凍結物なので着地後に変わらない。

## 再現

```bash
python3 tools/plotting/plot_a1_sized_paired.py \
  docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1
```

`--repo-root` は省略時に生成器の位置から repo root を決める。入力は repo 相対で固定 (CLI から別の leaf を渡せない)。
図番号は出力 prefix の `fig<N>_` から導く。`fig<N>_` の形でない prefix は出力前に拒否する。
生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font 解決に依存する。
着地したバイト列の同一性は provenance JSON が記録した `outputs[].sha256` と
`test_landed_fig9_repo_closure_and_caption_when_present` が守る。生成器の `generator.sha256` は生成時点の記録であり、
現行 source を縛る pin ではない (規律 7)。

## 作図規約への適合

- §1: 数値は `result.json` の `pairs` (30 対の生値) からその場で再計算し、記録値 (`statistics`) とは fail-closed で照合する。
- §2: 30 対の生値と、登録済み区間 (平均 ± h) を描く。区間は事前登録が固定した k (`t(1 − (1/120)/2, 29)`) による幅で、
  caption に登録済みの k と分位点を明記する (95% CI とは書かない)。
- §3: 比較対象 (床 ±B と 0) を水平の破線・実線で描き、差の帯と目で比べられる。
- §5: 図中ラベルは `pairs` / `mean` / `mean ± h` / `±B floor` / `zero` と workload 名 + 対比だけ。内部識別子は出さない。
- §6: provenance に入力 4 file + caption_source の path と SHA-256、study / source commit / pin、測定条件、3 workload の
  cells (統計・30 対・request / host・正しさの記録)、`artist_series` (実際に描いた y 値)、`limitations` (result.json の逐語)、
  caption、展開済み再現 argv を記録する。
- §9: 保存前に renderer-backed layout check を走らせ、text の重なり・逸脱があれば 3 成果物を 1 つも出さない。
- §10: 単体テストの fixture は実寸 (3 workload × 30 対 × 2 arm) で、本物の matplotlib Figure を layout check へ通す。
  実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、
`orchestrator/tests/test_plot_a1_sized_paired.py` が本 README への収録と生成器の決定的な組み立てとの一致を検査する。
英文で書く。値 (mean / h / B / baseline mean / job / host / 分類 / 符号) は生成器が `result.json` / `receipt.json` から書式化する。

> Figure 9. A-1 balanced five-rep paired comparison, sized run attempt-0001 (study paper-story-a1-20260901-balanced5-sized-v1; formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only). Columns: write-heavy (rr5, fixed10 minus no-backoff), balanced (rr50, fixed5 minus no-backoff), read-heavy (rr95, fixed2 minus no-backoff), each an independent campaign in its own job (job IDs, respectively: 4939.nqsv, 4940.nqsv, 4941.nqsv; hosts bnode107, bnode108, bnode109). What is drawn: 30 paired differences (variant minus baseline, one per pair index under the balanced five-rep schedule, ten-pair groups in the order A^5 B^5 B^5 A^5 or B^5 A^5 A^5 B^5) as open markers; the arithmetic mean as a solid line with the registered interval mean ± h, h = k·s/√n, k = 2.8315526875186725 (t quantile at 1 − (1/120)/2 with df 29), s the sample standard deviation of the 30 differences; the zero line; and the registered floor boundary ±B, B = 3 % of the baseline-arm mean, as dashed lines. M tps means million transactions per second. Values: write-heavy mean +1.592 M tps (h 0.024 M, B 0.069 M, baseline mean 2.293 M); balanced mean +0.449 M tps (h 0.028 M, B 0.116 M, baseline mean 3.863 M); read-heavy mean -0.577 M tps (h 0.033 M, B 0.310 M, baseline mean 10.340 M). The registered classification is resolved-above-floor in all three workloads (sign positive, positive and negative, respectively); variance_plan_breach is false in all three. The interval and the classification are the descriptive outputs of the preregistered rule; they are not a hypothesis test and are not a performance certification. This figure reports a single attempt of a non-certified lane: it is not a headline value, no cross-workload conclusion is drawn (preregistration section 7.2), it is not a reproduction of C1, and one attempt does not speak to stability across repeated attempts. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s per repetition, 30 pairs per workload, silo, CCBench pin 511c953, measurement source commit d2ebef7a4, no perf, trace-disabled performance. Correctness comes from separate trace-enabled verify runs under the recorded legacy check configuration, not the performance configuration: all 6 arms are recorded as certified (result.json correctness_evidence, verify_done frames bound by SHA-256); certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification. Panel y scales are workload-local and must not be compared across panels. Pilot observations did not enter the estimate; the estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state effect.

## proof chain

- 図に描いた 30 点・平均・帯・±B・0 → provenance JSON の `artist_series` (panel ごとの y 値) と `workloads[]` (cells)
- cells の統計 → `result.json` の `workloads[].statistics` (生成器は `pairs` から再計算して照合。分類は記録値のコピー)
- 標本の由来 → `result.json` の `statistics.pairs` と `arms.<name>.raw_tps` (対応を検査)、その先は campaign WAL
  (`wal_evidence` の path と SHA-256、results 稿 §5.2)
- 入力の束縛 → `.complete.json` の `files` map、生成器の pin 表、results 稿 §5.1 の表
- 正しさの記録 → `result.json` の `arms.<name>.correctness_evidence` (6 arm とも `certified: [true]`、`legacy`。anomaly 数は
  `wal_evidence.records[]` と WAL にあり、6 本とも 0。性能の認証ではない)
- 限定と条件の言い方 → results 稿 (provenance の `caption_source`、SHA-256 束縛)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_a1_sized_paired.py`。着地後の closure 検査
  (`validate_repo_closure`) が見るのは、着地 PNG / PDF の SHA-256・pin 表・現行 leaf から作り直した cells / artist / caption
  との一致・caption_source の現 SHA-256 である
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`
- 事前登録 → `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` (§3 推定対象、§5.1 区間、
  §5.2 分類、§7.2 できないこと)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256

次の 3 行が着地 bytes の正本である。`orchestrator/tests/test_plot_a1_sized_paired.py` の着地 test が、この 3 行の値と
着地 file の現物 SHA-256 の一致を検査する (行の形は `- \`<basename>\` SHA-256: \`<64 hex>\`` で固定)。

- `fig9_a1_balanced5_sized_attempt1.png` SHA-256: `7bbf0b16c856e9534577b100dc783f9b97b337adb9c9675772eeb4cf7956ce95`
- `fig9_a1_balanced5_sized_attempt1.pdf` SHA-256: `a2db2577f1db830c8fd252dccde496e004738e779fcb8fbf5f8ddb8965a7ade7`
- `fig9_a1_balanced5_sized_attempt1.provenance.json` SHA-256: `6e386d42457b154c9c58910bc1905df0947e7988f980237381cb6116e5ebf5ac`

provenance が `caption_source` として束縛する results 稿の SHA-256 は `67e8c53cbfe27a33fa51d55744364050cadbd1e83e605c0f9c06477f882d8e2e`
(稿は凍結物で、着地後に変わらない)。

---

# `fig3b_arc_status_2026-09-20` — 3 幕構成と §8 A/B 群の現在地 (2026-09-19 版の状態だけを描いた模式図、`fig3_` の後継図)

## 何を示す図か

`docs/paper-story/2026-09-19.md` (凍結物) の **§0 の 3 幕の要約**と **§8 の証拠項目 (A 系列 5 項目 = A-1 / A-2 / A-3 / A-5 / A-6、
B 群 11 項目 = A-4 / B-1〜B-10) の【状態】**を、1 枚の模式図にしたものである。**数値は 1 つも描かない。** 各項目に描くのは
4 状態のどれか (色とマーカー形。白黒でも形で判別できる) と、項目 ID・短い名前・副ラベル (同版の【状態】が持つ判定語・限定語) だけである。

- **obtained (取得済み)** — 記録された判定または完了がある。**主張を支持するとは限らない** (B-1 は `not met`、A-6 は `reject`、
  A-3 は規則の決着であって証拠ではない)。
- **uncertified (非認証)** — 材料はあるが、項目として認証・昇格・閉鎖されていない (A-1 の descriptive 出力、B-7 の材料、B-9 の
  機序仮説 view、B-10 の記述的 cohort)。項目単位の分類であり、材料の中の個々の認証 (例: A-2 / A-6 の correctness certified) を
  取り消す意味ではない。
- **awaiting ruling / human action (裁定待ち・人間手番)** — 裁定または人間の手番が残っていて進めない (A-4: 床の採用は
  D2120 項 2 で裁定済みだが chain は main に無く、承認 A と active pointer X は人間 commit で未発効)。
- **not obtained (未取得)** — 当該要件の証拠が未取得 (構造的な閉塞を含む)。**部分的な実走や生値が無いという意味ではない**
  (A-5 は投入 2 度と balanced 生値 1 走があるが要件を満たさない、B-6 は K2 の 2 巡が閉じたがリーク制御は未完備)。

上段の 3 幕は §0 の要約で、第 1 幕・第 2 幕は `complete`、第 3 幕は `in progress`。第 3 幕の 5 行のうち、Silo 固定スコープの解除
(D2114) と機構の進展は「証拠の状態」ではないので中立の横線を付け、4 状態のマーカーを付けない。

**この図は判定を作らない。** 状態は人が同版 §8 の各項冒頭【状態】と §0 の実文から読んで JSON に写したもので、生成器は JSON を
描くだけであり、判定・値・認証を再計算しない (規律 2 は影響を受けない)。A-2 / A-6 の判定は当時の identity 層の下のものとして残り、
後の identity 修正で遡って強くならない (規律 7)。図を variant 採用や認可の根拠にしない。**「A-1 の値がある」「mocc は第 2 成功例」
「B-10 を閉じた」「床値が発効した」とは、この図からも読めない** (同版 §0 末尾の 4 つの否定と同じ)。

## 既存図との関係

- **`fig3_arc_status.png` (2026-07-10 版、Phase 3 段 5 時点) の後継図。** 旧図は凍結物で bytes は 1 byte も変えていない。旧図と
  2026-08-23 版以降の第 3 幕の記述が一致しないことは各版 §0 と入口 README が明記しており、その注記はこの図の追加後も真である
  (旧図自身は変わらないため)。旧図は値 (利得率・A 値) を含んでいたが、本図は値を持たない。
- fig1 / fig2 / fig2b / fig2c / fig4〜fig9 の bytes も変わらない。本図は、それらの図が描く測定・判定を要約せず、§8 の【状態】だけを写す。
- **2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637)。

## 入力

- **状態 JSON** `tools/plotting/arc_status_story_2026-09-19.json` (schema `izanagi-arc-status/v1`)。状態語の**意味の正本は
  同版本文**であり、JSON はその射影である。各項目の `source_anchor` は `§8 A-1` / `§0 item 3` / `§0 act 3` の形で本文の
  項目見出しを指し、生成器はその見出し行が同版本文の該当節に**ちょうど 1 行**あることを検査する (意味の一致は検査しない —
  それは本 wave の read-only レビューが担った。下の proof chain)。
- **本文** `docs/paper-story/2026-09-19.md`。`story_path` は `docs/paper-story/<story_version>.md` と一致しなければならない。
  JSON と本文の SHA-256 を provenance に記録する。
- **FIGURE_CONVENTIONS §1 (入力は WAL/dat のみ) との関係:** §1 は数値を描く図の規約である。本図は値を持たない模式図で、入力は
  「人が凍結本文から写した状態の一覧」に限る。この位置づけは本図に限った限定であり、数値図への一般的な免除ではない
  (fig4 節が凍結 report を権威として読む限定例外を書いたのと同型)。
- **拒否条件 (生成器は成果物を出さない):** schema / key 集合の不一致 (未知・不足・重複 key、NaN / Infinity)、4 状態以外の
  `state` (証拠項目)、ID 重複、anchor の不正・不在・非一意、`story_path` の不一致、自由文 (label / sublabel / 状態定義文) に
  数量が混じる (`=`、`%`、単位語、数詞、JSON で宣言した証拠項目 ID と `reference_ids` 以外の数字入り token)、prefix が
  `fig<N><letters>_` の形でない、既存の 3 出力のいずれかが存在する (上書きしない)、保存前の layout check (全 Text の figure 内包・
  所属領域内包・相互非交差・兄弟セル非交差・marker の非交差) の違反。
- **JSON は凍結物ではない** (凍結物は PNG / PDF / provenance JSON)。ただし本図の再現入力として残す方針を採り、状態が変わる次の版では
  上書きせず別 file (例 `arc_status_story_<次の版日付>.json`) を足す。

## 再現

repo root から、**計測機の外** (login node で生成した) で次を実行する。出力 prefix は着地済み file と衝突しないものにする
(既存の 3 出力があれば生成器が拒否する)。

```bash
python3 tools/plotting/plot_arc_status.py --states tools/plotting/arc_status_story_2026-09-19.json /path/to/reproduction/fig3b_arc_status_2026-09-20
```

作成時は `docs/paper-story/figures/fig3b_arc_status_2026-09-20` を prefix にした (provenance の `argv` に逐語)。図番号は prefix の
`fig<N><letters>_` から取る (`3b`)。`--states` 省略時の既定はこの JSON。

### 再現できるのは「状態と表示内容」であって「配置」や「バイト列」ではない

再現の対象は、記録された状態 (4 状態) と表示内容 (項目 ID・名前・副ラベル・凡例・脚注・caption) である。**配置は描画環境に
依存する** — 折返しと行位置は font の実測幅・高さから決まり、matplotlib の版と font 解決 (DejaVu Sans) が違えば改行や位置が
変わりうる (収まらなければ layout check が保存前に拒否する)。provenance JSON は生成時刻 (`generated_utc`) を持ち、PDF は
matplotlib が生成日時を埋めるので、byte 一致も保証しない。着地 bytes の SHA-256 は下に記録する (記録であり、着地後の一致を
検査する test は本図には無い — 下の proof chain)。

### 次の版 (2026-09-20 版以降) との整合

本図は **2026-09-19 版の snapshot** であり、稼働中の wave は数えない (同版 §8 冒頭の規則)。次の版が land したら、項目ごとに
`state` だけでなく副ラベルの事実・限定・未了理由・人間手番まで比較する。変わらなければ本図をそのまま使い、「2026-09-19 版由来」の
表示も維持する。変わった項目があれば、この JSON と 3 成果物は残したまま、新しい JSON (`arc_status_story_<版日付>.json`) と
別 filename の後継図 (例 `fig3c_arc_status_<作成日>`) を作る。同 filename への再生成は凍結規則 (本 README 冒頭) に反するので行わない。
図名の日付 (`2026-09-20`) は作成日、JSON 名と provenance の `story_version` (`2026-09-19`) は状態を読んだ版の日付である。

**追記 (2026-09-21):** 2026-09-21c 版の状態には 2026-09-19 版と異なる項目 (B-8・B-7 ほか) があるので、上の手順どおり後継図 `fig3c_arc_status_2026-09-21`
を別 filename で作った (本 README の fig3c 節)。本図の JSON と 3 成果物は残している。

## 作図規約への適合

- §1: 値を描かない模式図なので WAL/dat の再計算は無い (上の「入力」の限定)。数値の混入は生成器が自由文検査で拒否する。
- §2 / §3 / §4: 反復・基準線・二軸を持たない (数値図の項目は該当しない)。
- §5: 図中ラベルは、証拠項目が項目 ID + 短い名前 + 副ラベル、Act の行が短い名前 + 副ラベル (JSON 内部 ID は図に出さず provenance の `drawn_items.id` にだけ残す)、凡例は 4 状態の表示名と JSON の定義文。キャプションで一度だけ展開する。
- §6: provenance に入力 2 file (JSON・本文) と生成器・出力 2 file の SHA-256、描いた 27 項目 (`drawn_items`: ID・状態・実表示文字列)、
  状態定義、caption、展開済み argv、matplotlib / numpy の版を記録する。
- §7: login node で生成 (計測機の外)。
- §8: matplotlib / numpy のみ、自己完結 (既存生成器を import しない)。PNG (200 dpi) と PDF を出す。
- §9: 保存前に Agg renderer で layout check を走らせ、違反があれば 3 成果物を 1 つも出さない。
- §10: 単体テスト `orchestrator/tests/test_plot_arc_status.py` は**実 JSON そのもの**を実寸 fixture として本物の Figure を layout check へ
  通し、色・マーカーの独立表と provenance を照合する。実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列である (生成器の固定 template に図番号と版日付を差し込む)。英文で書く。

> Figure 3b. Status of the paper-story arc read from the frozen 2026-09-19 story: act summaries from section 0 and evidence-item states from section 8. Colors and marker shapes distinguish obtained, uncertified, awaiting ruling / human action, and not obtained. Obtained records that a judgment or completion exists, not that a claim is supported: B-1 remains not met and A-6 records reject. A-3 is a settled reporting rule, not new empirical evidence. A-1 remains descriptive and non-certifying; A-4 is adopted by ruling but inactive pending human action. B-7, B-9, and B-10 are neither promoted nor closed by this figure. This figure summarizes recorded statuses; it does not evaluate correctness, certify performance, or authorize further work. A-2 and A-6 retain the judgments made under the identity layer used at the time; later identity fixes do not strengthen them retrospectively. No measurement values are drawn and no judgments are recomputed. Successor to fig3; the original remains frozen.

## proof chain

- 図に描いた 27 項目 (Act 見出し 3・Act 行 8・証拠項目 16) → provenance JSON の `drawn_items` (ID・状態・実表示文字列。生成器は
  JSON から期待される集合と保存前に照合する)
- 各項目の状態と副ラベル → `tools/plotting/arc_status_story_2026-09-19.json` (provenance `inputs[kind=states]` の SHA-256)
- 状態の出所 → `docs/paper-story/2026-09-19.md` の §8 各項冒頭【状態】と §0 (provenance `inputs[kind=story]` の SHA-256、各項目の
  `source_anchor` が指す見出し行の一意な存在を生成器が検査)
- 状態の写しが本文の意味と一致すること → 本 wave の read-only 敵対レビュー (段 3 の逐語照合 16 項目 + Act 3 の 5 行、段 6 の独立
  レビュー)。一次資料は `output/insights/2026-09-20/fig3b-arc-status/README.md`
- 生成器 → `tools/plotting/plot_arc_status.py` (実装 commit `14529331c` (段 5 author)、段 6 fix `152c1d99d`、test だけの fix2 `5686eaa2a`、provenance `generator.sha256`)
- 実走 → login node、2026-09-20 08:25 JST (provenance `generated_utc` 2026-09-19T23:25:08Z)、rc=0、3 成果物。単体テスト `orchestrator/tests/test_plot_arc_status.py` は
  計算ノード job `11937.nqsv` で 30 passed / 9.03 秒 (段 6 fix 後。fix 前は job `11908.nqsv` で 29 passed / 9.06 秒)。変異 9 系列は独立 clone (commit `152c1d99d`) で probe → final の 2 段、final は 9/9 KILLED・期待 node 完全一致、test だけの fix2 の後の再走 final2 も 9/9 KILLED (一次資料 `output/insights/2026-09-20/fig3b-arc-status/` の `mutation-final-results.json`)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256 (記録)

次の 3 行は着地時点の bytes の記録である。fig9 と違い、着地後の一致を検査する test は**本図には作っていない** (gate の新設は
本 wave の scope 外)。着地後の同一性は git の履歴が担う。

- `fig3b_arc_status_2026-09-20.png` SHA-256: `831d2fcc0673c4ed1115af89d8e69f69e978bc60ac8583f3239e27426207a65b`
- `fig3b_arc_status_2026-09-20.pdf` SHA-256: `87018e0879a319a59b0eba426087b332950cc282e08bf12bb400ddf65f4269bd`
- `fig3b_arc_status_2026-09-20.provenance.json` SHA-256: `4772b3e41a7b4eef29904e7acc8a7583dc526ae5986bfb010665bd48cf99c597`

---

# `fig3c_arc_status_2026-09-21` — 3 幕構成と §8 A/B 群の現在地 (2026-09-21c 版の状態だけを描いた模式図、`fig3b_` の後継図)

## 何を示す図か

`docs/paper-story/2026-09-21c.md` (凍結物) の **§0 の 3 幕の要約**と **§8 の証拠項目 (A 系列 5 項目 = A-1 / A-2 / A-3 / A-5 / A-6、
B 群 11 項目 = A-4 / B-1〜B-10) の【状態】**を、1 枚の模式図にしたものである。**数値は 1 つも描かない。** 描くのは fig3b と同じ 4 状態
(色とマーカー形。白黒でも形で判別できる) と、項目 ID・短い名前・副ラベル (同版の【状態】が持つ判定語・限定語) だけである。4 状態の定義文は
fig3b と同じ文字列である (`state_definitions`)。

**状態語の意味 (2026-09-21c 版の例示)。** 定義文は fig3b と同じだが、fig3b 節の例示は 2026-09-19 版の状態の例である (たとえば同節の A-4 の
「人間 commit で未発効」は 2026-09-21c 版では偽)。2026-09-21c 版での例示は次のとおりである。

- **obtained (取得済み)** — 記録された判定または完了がある。**主張を支持するとは限らない** (A-2 は `observed-positive`、B-1 は `not met`、A-6 は `reject`、A-3 は規則の決着で
  証拠ではない、B-7 は単一 attempt・descriptive・非認証・反復間安定性は未判定の 4 語の限定付き充足、B-8 は単独稿 §4 の 11 項の限定付きの `pass`)。
- **uncertified (非認証)** — 材料はあるが項目として認証・昇格・閉鎖されていない (A-1 の 2 attempt の descriptive 出力、B-9 の機序仮説 view、
  B-10 の記述的な判定)。
- **awaiting ruling / human action (裁定待ち・人間手番)** — A-4 (凍結 v2 g1 は発効済みだが、live launch の択 S' / O' / N の裁定と W-4 の spec 承認が残る)。
- **not obtained (未取得)** — A-5 と B-2〜B-6。部分的な実走・試走・修復の着地が無いという意味ではない (B-5 は試走と段階認可、B-6 は pair の driver 修復)。
- **状態の選び方の優先順位:** 項目の要件の証拠そのものが未取得なら not obtained を選び、要件の証拠が揃っていて裁定・人間手番だけが残る場合に
  awaiting を選ぶ。人間手番が残っても要件の証拠が無い項目 (B-6: pair の再投入はユーザー手番だがリーク制御の完備は別に未取得) は not obtained、
  材料があり認証されていない項目 (A-1: 追加 attempt の認可はユーザー手番) は uncertified とする (fig3b の先例どおり)。

fig3b (2026-09-19 版の状態) から状態・ラベル・副ラベルが変わった項目は次のとおりである (いずれも 2026-09-21c 版の本文から写した)。**この列挙は
JSON の写しの差分 (版の差) の記録であり、論文で fig3b と fig3c を前後比較する材料ではない** (同版 §7: fig3b と fig3c を合成・比較しない)。

- **B-8: not obtained → obtained** (ラベル「Seed-varied long-run check」、副ラベル「pass under effective preregistration; operational definitions;
  observed runs only; no performance claim」。fig3b のラベル「Independent long-run validation」は、obtained と並べると独立性・長時間性が検証されたと
  読まれうるので本文の項目名に寄せた)。B-8 事前登録 v1 の
  3 値判定 `pass` (D2202、entry 1791) の記録であり、主張の支持を意味しない (obtained の定義は「支持するとは限らない」)。限定は B-8 単独稿 §4 の 11 項で、図には描かない。
- **B-7: uncertified → obtained** (副ラベル「fulfilled with limitations: single attempt; descriptive; non-certifying; repeat stability undetermined」)。
  D2174 項 3 の限定付き充足 (2026-09-20b 版)。同版 §8 B-7 が「充足」に必ず添えると定める 4 語の限定をすべて載せた。
- **A-4: awaiting ruling / human action のまま、副ラベルを更新** (「effective; historical reverify passes; live launch rejected; ruling pending」)。
  凍結 v2 g1 は発効済み (D2180) で、候補文書の削除後に historical reverify は成功した ([T-2824]) が、live launch は現行 policy 照合で拒否され、
  択 S' / O' / N (D2201) の裁定と W-4 の spec 承認 (人間手番) が残る。
- **A-1 / A-5 / B-4 / B-5 / B-6 / B-9 の副ラベル**を 2026-09-21c 版の【状態】へ写し直した — A-1 は「further attempts require human action」(3 本目の
  認可ほかはユーザー手番)、A-5 は「Pegasus cannot establish separate-boot reproduction」、B-4 は「eligible precursor absent; carrier ruled, not implemented」(未了の主因の
  適格な赤 precursor 0 件と、carrier の裁定までで未実装)、B-5 は「staged approval only; main run not authorized」、B-6 は「pair driver repaired; pair rerun
  not submitted」、B-9 は「originals lost」(K2 round 2 / 3 の campaign 原本の消失、F1034) を足した。
- **第 3 幕の行:** fig3b の「Silo-only scope」の行は載せない — C 群は図の対象外で、2026-09-21c 版の §0 もこの版の変化として挙げていない (Silo 固定
  スコープの解除 D2114 は同版 §1 と §8 C-1 にある)。代わりに §0 の項 1 (B-8) を「Final-candidate check」(副ラベル「B-8 pass; correctness check on
  observed runs; no performance claim」) の行として載せた。A-1 の行はラベルを「A-1 descriptive attempts」、副ラベルを「completed; non-certifying;
  observations only」へ改め、出所は §8 A-1 とした (fig3b では §0 の項 1)。

上段の 3 幕は §0 の要約で、第 1 幕・第 2 幕は `complete`、第 3 幕は `in progress`。第 3 幕の「Mechanism work」の行は証拠の状態ではないので
中立の横線を付け、4 状態のマーカーを付けない。

**この図は判定を作らない。** 状態は人が同版 §8 の各項冒頭【状態】と §0 の実文から読んで JSON に写したもので、生成器は JSON を描くだけであり、
判定・値・認証を再計算しない (規律 2 は影響を受けない)。A-2 / A-6 の判定は当時の identity 層の下のものとして残り、後の identity 修正で遡って
強くならない (規律 7)。図を variant 採用や認可の根拠にしない。**「A-1 の値がある」「B-5 の本走が認可された」「g1 の launch validation が通った」
「K2 の対照が取れた」「B-10 を閉じた」とは、この図からも読めない。B-8 の obtained は、観測した 30 枠の trace についての判定の記録であり、未観測の
条件・性能・S-1 の充足へ広げない。**

## 既存図との関係

- **`fig3b_arc_status_2026-09-20` (2026-09-19 版の状態) の後継図。** fig3b の 3 成果物と状態 JSON `arc_status_story_2026-09-19.json` の bytes は
  1 byte も変えていない。fig3b の provenance の `generator.sha256` は fig3b を生成した当時の生成器の記録であり、生成器の現行 bytes とは一致しない
  (この wave で生成器を最小修正したため)。その記録は書き換えない (規律 7)。既定 JSON (2026-09-19) に対する生成器の表示内容 (drawn_items と
  caption の全文) は不変で、単体 test T7 と T9 が固定する。fig3b を生成した当時の生成器の bytes は、fig3b 節の proof chain にある commit
  `152c1d99d` で辿れる。
- `fig3_arc_status.png` (2026-07-10 版) も凍結物のまま。fig1 / fig2 / fig2b / fig2c / fig4〜fig13 の bytes も変わらない。
- **2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637)。

## 入力

- **状態 JSON** `docs/paper-story/figures/arc_status_story_2026-09-21c.json` (schema `izanagi-arc-status/v1`、key 集合は 2026-09-19 版と同じ)。
  状態語の意味の正本は同版本文であり、JSON はその射影である。各項目の `source_anchor` は本文の項目見出しを指し、生成器はその見出し行が同版本文の
  該当節にちょうど 1 行あることを検査する (意味の一致は検査しない — それは本 wave の read-only レビューが担った)。
- **本文** `docs/paper-story/2026-09-21c.md`。`story_version` は `2026-09-21c` (同日の 3 版目。生成器は英小文字 1 字の接尾辞を受理し、暦日検査は
  日付部分に掛ける)。`story_path` は `docs/paper-story/2026-09-21c.md`。`figure_created` は `2026-09-21`。
- FIGURE_CONVENTIONS §1 (入力は WAL/dat のみ) との関係は fig3b 節と同じ限定 (値を持たない模式図に限った限定であり、数値図への一般的な免除ではない)。
- 拒否条件は fig3b 節と同じ。ただし `story_version` だけは英小文字 1 字の接尾辞を受理するようになった (大文字・2 字以上の接尾辞・暦日として
  無効な日付部分は拒否する。単体 test T11)。

## 再現

repo root から、**計測機の外** (login node) で次を実行する。出力 prefix は着地済み file と衝突しないものにする (既存の 3 出力があれば
生成器が拒否する)。

```bash
python3 tools/plotting/plot_arc_status.py --states docs/paper-story/figures/arc_status_story_2026-09-21c.json /path/to/reproduction/fig3c_arc_status_2026-09-21
```

作成時は `docs/paper-story/figures/fig3c_arc_status_2026-09-21` を prefix にした (provenance の `argv` に逐語)。図番号は prefix の
`fig<N><letters>_` から取る (`3c`)。`--states` を省略すると既定 (2026-09-19 版の JSON) になり fig3b の再現になるので、fig3c では必ず指定する。
再現できるのは「状態と表示内容」であって「配置」や「バイト列」ではない (fig3b 節と同じ)。

## 作図規約への適合

fig3b 節と同じ (§1 の限定、§5 のラベル、§6 の provenance、§7 の login 生成、§8 の自己完結、§9 の保存前 layout check)。§10 について:
生成器の最小修正 (版名の接尾辞の受理、2026-09-19 版以外での状態非依存の固定 caption) には単体 test T9〜T13 を足したが、**単体 test の実寸 fixture は
2026-09-19 版の JSON とその本文の複製であり、2026-09-21c 版の JSON を読む test は無い。** 2026-09-21c 版の JSON (副ラベルが長い) が収まることは、
生成時の保存前 layout check (fail-closed) と実走の rc=0 で確かめた。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列である (生成器の固定 template に図番号と版名を差し込む)。英文で書く。
2026-09-19 版以外の版では、項目の状態を述べる文を持たない固定 caption を使う (項目固有の判定語・限定は各項目の副ラベルが担う)。**副ラベルは
本文の【状態】の要約であり、限定を網羅しない** (たとえば B-8 の限定は単独稿 §4 の 11 項、B-7 は本文 §8 の 4 語)。caption の「each item's sublabel
carries the recorded judgment words and limitations」もこの意味で読み、正本は同版本文の §8 である (caption 文言の修正は生成器の変更になるので
この wave では行っていない — 段 6 レビュー B の should-fix、Codex の利用上限のため)。

> Figure 3c. Status of the paper-story arc read from the frozen 2026-09-21c story: act summaries from section 0 and evidence-item states from section 8. Colors and marker shapes distinguish obtained, uncertified, awaiting ruling / human action, and not obtained. Obtained records that a judgment or completion exists, not that a claim is supported; each item's sublabel carries the recorded judgment words and limitations. This figure summarizes recorded statuses; it does not evaluate correctness, certify performance, or authorize further work. Recorded judgments keep the identity layer used at the time; later identity fixes do not strengthen them retrospectively. No measurement values are drawn and no judgments are recomputed. Successor to fig3; the original remains frozen.

## proof chain

- 図に描いた 27 項目 (Act 見出し 3・Act 行 8・証拠項目 16) → provenance JSON の `drawn_items` (ID・状態・実表示文字列。生成器は
  JSON から期待される集合と保存前に照合する)
- 各項目の状態と副ラベル → `docs/paper-story/figures/arc_status_story_2026-09-21c.json` (provenance `inputs[kind=states]` の SHA-256
  `e8a6b3e5cf12946d2d58cb4abe7a26ad09ab281a6113036d2ac9c317c12cba62`)
- 状態の出所 → `docs/paper-story/2026-09-21c.md` の §8 各項冒頭【状態】と §0 (provenance `inputs[kind=story]` の SHA-256
  `0317911a7791badeb4c29693dabf729bf85fde05bf12d787eff8e5d217133b40`、各項目の `source_anchor` が指す見出し行の一意な存在を生成器が検査)
- 状態の写しが本文の意味と一致すること → 本 wave の段 6 read-only レビュー B (生成器・状態 JSON・本節の草稿) と焦点再レビュー 2 巡。
  **Codex の利用上限のため Claude opus の独立 context が担った** (別系統モデルによる独立性はこの分だけ弱い)。一次資料は
  `output/insights/2026-09-21/paper-story-20260921c/README.md`
- 生成器 → `tools/plotting/plot_arc_status.py` (最小修正の統合 commit `76b60f6e1` (段 5、Codex author)、provenance `generator.sha256`
  `076ad3828cae8cc1cd1d9ff97f418f128984a5b7914fe3f9096da594d1b51548`)
- 実走 → login node、2026-09-21 16:25 JST (provenance `generated_utc` 2026-09-21T07:25:58Z)、rc=0、3 成果物。単体テスト
  `orchestrator/tests/test_plot_arc_status.py` を含む焦点走は計算ノード job `15122.nqsv` で 607 passed / 1 failed / 3 skipped (赤 1 件は
  作業木の未追跡の版下書きを worktree 清浄検査が数えたもので、生成器とは無関係)。変異 M1〜M8 は独立 clone (commit `76b60f6e1`) で
  probe → final の 2 段、final は 8/8 KILLED・期待 node 完全一致、M0 (等価変異) は SURVIVED (一次資料は同 insight の `mutation-final-results.json`)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256 (記録)

次の 3 行は着地時点の bytes の記録である。fig3b と同じく、着地後の一致を検査する test は**本図には作っていない** (gate の新設は
本 wave の scope 外)。着地後の同一性は git の履歴が担う。

- `fig3c_arc_status_2026-09-21.png` SHA-256: `34d2b5e67377dfe8f914ae7034d3f9cc493eaa98f747f52b8135184c9d52fd1b`
- `fig3c_arc_status_2026-09-21.pdf` SHA-256: `3ba27096c11f70a7a402d3565c3a37ecf117339137aaa9f72a0d941f9e9b4213`
- `fig3c_arc_status_2026-09-21.provenance.json` SHA-256: `82b531113b18cb34d65653279e6ca6e4309a337d3b36b9b7924db07bebb839e0`

---

# `fig10_b7_fixed5_three_workload_regression` — 採用候補 fixed 5 µs の 3 workload 同時期測定と床値判定 (B-7 の材料図)

## 何を示す図か

study `paper-story-b7-fixed5-regression` の attempt `b7f5-20260919a` (2026-09-19、request `10807.nqsv` / `10808.nqsv` / `10809.nqsv`、
3 workload × 2 cell × 5 標本) について、稿 `results/2026-09-19-b7-fixed5-three-workload-regression.md` の主表 (§2.1) と床値判定 (§1.4) を
そのまま図にした**記述図**である。

- 上段 3 panel (write-heavy rr5 / balanced rr50 / read-heavy rr95): cell ごとの trace-disabled 性能標本 5 点、短い横棒が median、ひし形と誤差棒が
  標本平均と t 分布 95% 信頼区間 (df 4)、灰色の破線が同 workload の stock (無 backoff) median = 効果の分母。y は workload ごとの尺度で、panel 間で高さを比べない。
- 下段 1 panel: workload ごとの median 効果 (`effects[w]` = adopted median / stock median − 1、certification.json の値を写す) を marker で、
  0 線と、各 workload の `−floor_w` (D1639 の between-run 床値 = 床値 JSON `between_run.cv` の全桁) を短い破線で置く。
  結果を見る前に固定した規則 (`effect_w < −floor_w`、strict) の判定を label で示す — write-heavy 退行なし、balanced 退行なし、**read-heavy は床値超の退行**。

**この図が言えるのは稿の床値判定まで**である。「退行なし」は優越でも差が無いことの証明でもなく、床は旧 stock の session-median の変動係数であって
効果の標準誤差ではない。有意差判定、効果・median・床値判定の区間推定 (標本平均の t95 CI は描くが、それは標本の記述である)、
B-7 (全 workload の退行込み報告) の要件充足の判定、certification の昇格、反復 attempt の安定性は含めない (D2044 項 3、D2162)。機構の outer status `reject` は 3 workload の論理積の出力で read-heavy の負の効果の帰結であり、研究の失敗宣告ではない
(D12)。図を variant 採用の根拠にしない (絶対規律 2)。

## 既存図との関係

- 既存図 (fig1〜fig9) のいずれの後継でもない独立した新図。fig5〜fig7 は A-2 の 4 cell (workload 別の採用値 10 / 5 µs、または内蔵 backoff の有効/無効)、
  本図は**同一候補 fixed 5 µs** を 3 workload で同一 attempt に測った別 study instance の 6 cell で、値も条件も別である。前後比較として読まない (絶対規律 7)。
- 既存材料 (2026-09-16 稿の 10 / 5 / 2 µs) は描かない。併記もプールも比較もしない (D1993 項 6)。
- **2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637)。

## 入力

- 権威 bytes (repo 内、tracked): `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json`
  (`paper-story-a2-certification-result/v4`、6 cell の median・`effects`・`status`・`a4_noise_floor_status`・correctness・`src_token`・binary digest) と
  同 dir の `raw-manifest.json` (`paper-story-a2-full-raw-manifest/v4`、durable raw の SHA-256)。
- 床値 (repo 内、tracked、D1639): `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json` の `between_run.cv`。
- policy (repo 内、tracked): `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` (測定条件の出所。certification の `policy_sha256` と一致を要求)。
- 生成器は repo 所有の pin 表で上の 6 file の SHA-256 を照合する。**pin は CLI から渡せない。** SHA-256 の値は稿 §5.1 (certification / raw-manifest) と同じで、
  `orchestrator/tests/test_plot_b7_fixed5_regression.py` が稿の表・§1.4 の床値 3 値・§2.1 の `effect_w` と判定との一致を検査する。
- 外部入力 (repo 外、durable authority): attempt の raw cell JSON 6 本
  (`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/jobs/<w>/raw/<cell>.json`)。
  root 相対 path と SHA-256 を provenance の `external_inputs` に記録し、tracked `raw-manifest.json` の `files` と一致を要求する。
  5 標本 (`performance.samples_tps`) の出所はここだけで、certification.json は median しか持たない。
- 再計算と照合: 各 cell の median は 5 標本から再計算して certification の `median_tps` と一致を要求する。効果は certification の `effects` を写し、
  median の比からの再計算と `abs_tol = 1e-12` で照合する (`effect_crosschecks`)。**図に出す判定の出所は稿 §2.1 の転記** (定数 `RECORDED_JUDGMENT`) であり、
  生成器は述語 `effect_w < −cv_w` を評価するが、それは転記と権威 bytes・床値 JSON との整合検査にだけ使い、判定の出所にはしない (fig9 の classification と同型)。
- 拒否条件: SHA-256 不一致 (tracked 6 file、raw 6 file)、schema / study / attempt / cell 順序の不一致、`source_binding_status` ≠ bound、adopted の `src_token` が
  `stock` または 3 workload で不一致、`correctness.status` ≠ certified、raw の verify 記録 (legacy 1 + performance 5) に `serializable` / `certified` でないものがある、
  raw の性能標本が trace-enabled、`unstable`、標本数 ≠ 5、median / effect の不一致、判定の不一致、床値 JSON の genome / 条件の不一致、caption_source の不在。
  いずれでも成果物を出さない。
- **caption_source:** provenance の `tracked_inputs` に `kind: "caption_source"` として稿
  `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` の path と SHA-256 を記録する
  (`authority_scope` = 記録判定 (`RECORDED_JUDGMENT`) の転記元と、限定・条件の言い方の出所であって、測定値・効果の一次権威ではない)。稿は provenance の SHA-256 を持たない (F36 の自己参照回避)。
  稿は凍結物なので着地後に変わらない。

## 再現

```bash
python3 tools/plotting/plot_b7_fixed5_regression.py \
  --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a \
  docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression
```

`--repo-root` は省略時に生成器の位置から repo root を決める。repo 内入力は repo 相対で固定 (CLI から別の leaf を渡せない)。
`--measurement-root` は省略時に上の durable path を使う。図番号は出力 prefix の `fig<N>_` から導く。`fig<N>_` の形でない prefix は出力前に拒否する。
生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font 解決に依存する。
着地したバイト列の同一性は provenance JSON が記録した `outputs[].sha256` と
`test_landed_fig10_repo_closure_and_caption_when_present` が守る。着地後の closure 検査は repo 内の tracked 入力と出力の SHA-256、
`external_inputs` と raw-manifest の一致、provenance の cells から作り直した artist / caption との一致、provenance の 30 標本・6 median と稿 §2.2 の一致を見る (durable root を読まない。
durable root が読めるときは `validate_external_sources` が raw 6 本の SHA-256 も照合する)。生成器の `generator.sha256` は生成時点の記録であり、
現行 source を縛る pin ではない (規律 7)。

## 作図規約への適合

- §1: 数値は raw cell JSON の 5 標本と certification.json の `effects`・床値 JSON の `cv` からその場で読み、median と効果を再計算して記録値と fail-closed で照合する。
- §2: 5 標本の生値と、標本平均 ± t 分布 95% CI (df 4) を描く。CI は標本の記述であって、効果・median・判定の区間ではないと caption に明記する。
- §3: 比較対象 (stock median、0、−floor) を水平の破線・実線で描き、標本・効果と目で比べられる。
- §5: 図中ラベルは `stock` / `fixed 5 us` / `median` / `mean ± t95 CI` / `stock median` / `effect` / `-floor` と workload 名 (rr) だけ。内部識別子は出さない。
- §6: provenance に tracked 入力 6 file + caption_source の path と SHA-256、外部入力 6 file、study / attempt / source commit / pin / request、測定条件、
  6 cell (標本・median・平均・CI・correctness 要約・digest)、`effects` と `effect_crosschecks`、`floors`、`judgments`、`artist_series`、caption、展開済み再現 argv を記録する。
- §9: 保存前に renderer-backed layout check を走らせ、text の重なり・逸脱があれば 3 成果物を 1 つも出さない。
- §10: 単体テストの fixture は実寸 (3 workload × 2 cell × 5 標本、床値 3 本、raw 6 本) で、本物の matplotlib Figure を layout check へ通す。
  実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、
`orchestrator/tests/test_plot_b7_fixed5_regression.py` が本 README への収録と生成器の決定的な組み立てとの一致を検査する。
英文で書く。値 (効果 % / −floor % / 判定 / request / pin / source commit / 条件) は生成器が certification.json・床値 JSON・policy から書式化し、
限定の固定文 9 つ (B-7 の充足判定ではない / 規則と床の出自 / 退行なしは優越でも差の不在の証明でもない / outer status は論理積の出力 /
単一 attempt・昇格しない / 正しさは別走行で性能の認証ではない / CI は標本の記述 / 上段 y は workload 別 / 既存材料とプール・比較しない) を逐語で含む。

> Figure 10. B-7 material: static backoff fixed 5 us versus stock (no backoff) in three workloads, attempt b7f5-20260919a (study paper-story-b7-fixed5-regression; outer status reject; a4_noise_floor_status open). Columns: write-heavy (rr5, request 10807.nqsv), balanced (rr50, request 10808.nqsv), read-heavy (rr95, request 10809.nqsv), each an independent campaign in its own request, with the stock control measured in the same campaign immediately before the adopted cell. Top row: all five trace-disabled performance samples per cell; short bars are medians; diamonds with error bars are sample means with t-distribution 95% confidence intervals (df 4); the gray dashed line is the workload's stock median and the effect denominator. Bottom row: median effects copied from certification (adopted median / stock median - 1): write-heavy +67.8968%, balanced +12.6717%, read-heavy -11.3787%; dashed ticks mark -floor per workload: write-heavy -0.9536%, balanced -0.7250%, read-heavy -0.2228%. The rule fixed before the results were seen classifies a workload as regression when effect < -floor (strict), floor being the D1639 between-run noise floor: the coefficient of variation of the per-session medians of the stock genome across 8 earlier sessions of 5 repetitions under the same settings, recorded as a lower bound; identity of binary, toolchain and node between that floor measurement and this attempt is not established. Result of that rule: write-heavy no regression, balanced no regression, read-heavy regression (below -floor). No regression is neither superiority nor proof of no difference; the floor is not the standard error of the effect, and no significance decision is made. The outer status is the protocol's conjunction over the three workloads and follows from the negative read-heavy effect; it is not a research verdict. This is B-7 material, not a B-7 satisfaction decision (D2044 item 3). This figure reports a single attempt of five samples per cell; it does not promote the certification and does not speak to repeated attempts. Correctness comes from separate trace-enabled verify runs under the recorded check configuration, not the performance configuration: all 6 cells are recorded as certified with serializable verdicts (1 legacy and 5 performance records each); certified means serializability of the observed traces under that check configuration and nothing beyond, the correctness workload argv was not independently recorded, and this is not a performance certification. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s per repetition, 5 repetitions, silo, CCBench pin 511c953, source commit c18a80967, no perf, trace-disabled performance; the adopted cells share one source bytes digest across workloads but each workload is a separate build (binaries differ). M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, medians, or the floor judgment. Top-row y axes are workload-local and must not be compared across panels. Existing materials with other adopted values are neither pooled nor compared.

## proof chain

- 図に描いた標本・median・平均・CI・stock median・効果・−floor・判定 → provenance JSON の `artist_series` と `cells` / `effects` / `floors` / `judgments`
- 効果と outer status → `certification.json` の `effects` / `status` / `a4_noise_floor_status`。生成器は再計算せず、`effect_crosschecks` に raw median の比との一致を記録する
  (3 workload とも `authority_matches` が真)
- 判定 → 稿 §2.1 の判定を生成器の定数 `RECORDED_JUDGMENT` として写し、`judgments[w].computed_matches_recorded` に述語 `effect < −floor (strict)` との一致を記録する
  (床 = 床値 JSON `between_run.cv` の全桁、`floors[w]`)。判定の出所は稿の転記で、述語は整合検査にだけ使う
- 標本の由来 → durable authority の raw cell JSON 6 本 (provenance の `external_inputs` に root 相対 path と SHA-256)、その先は campaign WAL (稿 §5.2)
- 入力の束縛 → tracked `raw-manifest.json` の `files` と生成器の pin 表 (`tracked_inputs`)、稿 §5.1 の表
- 正しさの記録 → raw cell JSON の `correctness.legacy` (1 記録) と `correctness.performance` (5 記録) が 6 cell とも `verdict = serializable`・`certified = true`
  (`cells[].correctness`)。性能の認証ではない
- 限定と条件の言い方 → 稿 (provenance の `caption_source`、SHA-256 束縛)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_b7_fixed5_regression.py`。着地後の closure 検査 (`validate_repo_closure`) が見るのは、着地 PNG / PDF の
  SHA-256・pin 表・`external_inputs` と raw-manifest の一致・provenance の cells から作り直した artist / caption との一致・caption_source の現 SHA-256 である
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`
- 判定規則と床の裁定 → D2162 (判定規則 v2、B-7 充足判定なし)、D1639 (床値 = between-run noise floor)、D2044 項 3
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256

次の 3 行が着地 bytes の正本である。`orchestrator/tests/test_plot_b7_fixed5_regression.py` の着地 test が、この 3 行の値と
着地 file の現物 SHA-256 の一致を検査する (行の形は `- \`<basename>\` SHA-256: \`<64 hex>\`` で固定)。

- `fig10_b7_fixed5_three_workload_regression.png` SHA-256: `583e94f642a9892a66791b9e0dff5ed37bd7babedf3f4da644b1245af15d1d5d`
- `fig10_b7_fixed5_three_workload_regression.pdf` SHA-256: `d2011717817a94da32cbbfdd9120043d34df23fab77ea32f7228c6355ceaaa46`
- `fig10_b7_fixed5_three_workload_regression.provenance.json` SHA-256: `263b04d30f66bec6e24086be75d59c4b9b0013f5f05cbe1f260fc1ad41eef8e4`

provenance が `caption_source` として束縛する稿の SHA-256 は `6585d446a07d798d87c352a1b41eb5b195ee70ba453976aa5ec0f46daef4b6f9`
(稿は凍結物で、着地後に変わらない)。

## 追補 — B-7 の限定付き充足 (2026-09-20、D2174 項 3、[T-2610])

着地後のユーザー裁定 D2174 項 3 (択 (a)) は、B-7 (論文の失敗条件 (e) = target workload では勝つが他の workload で床値超の退行があるなら
退行込みで全 workload を報告する) を、同一候補 fixed 5 µs の 3 workload 同時期測定と床値判定 (D2162、稿 §2.1、read-heavy が床値超の退行) と本図により、
**単一 attempt・descriptive・非認証・反復間安定性は未判定**という限定付きで満たしたと扱い、D2044 項 3 (要件充足へ昇格させない) をこの限定付き充足で
supersede した。反復 attempt は認可されず (択 (b) 不採用)、certified 昇格・有意差判定・新規測定は含まない。

- **本図の bytes・caption・provenance は変えない。** caption の固定文 "This is B-7 material, not a B-7 satisfaction decision (D2044 item 3)." は
  着地時点の記録として真のまま残す — 充足の裁定は図の外で D2174 項 3 が行ったのであり、図自身が B-7 の充足を判定したのではない。
  同じく稿 (`caption_source`) の冒頭「本稿が判定しないこと」も凍結のまま (稿の SHA-256 は上の値から動かない)。
- **本図で言えることは変わらない。** 図の統計的な解釈 (何を判定し何を判定しないか) と、図を variant 採用の根拠にしない制限は、上の「何を示す図か」のとおり変わらない。
- **「充足」の射程。** 満たしたのは報告要件 (退行込みの全 workload 報告) であって、候補の採用・性能主張・正しさの認証ではない。
  B-7 の充足裁定に付く限定は上の 4 語である (D2174 項 3)。稿・図の既存の限定はそのまま残る。
- ストーリー版 2026-09-20 版の該当文 (§8 B-7、§6 「言えないこと」) が古くなった扱いは `docs/paper-story/README.md` の stale 注記が持つ (版・claim-evidence 稿は凍結のまま)。
- 裁定の一次資料 → D2174 項 3。本追補の記録 → `output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md`。

---

# `fig11_a6_certification_reject` — A-6 read-heavy 正式 certification (attempt `a6-20260908b`、outer `reject`) の exact 2 cell 図

## 何を示す図か

study `paper-story-a6-certification` の attempt `a6-20260908b` (2026-09-08、request `982234.nqsv`、bnode031、1 workload × 2 cell × 5 標本) を、
fig6 (A-2) と同じ生成器・同じ描画契約で描いた**結果図**である。単独稿 `results/2026-09-18-a6-certification-reject.md` の表 (§2.1〜§2.3) と同じ権威 bytes から作る。

- 上段 1 panel (read-heavy rr95): cell ごとの trace-disabled 性能標本 5 点、短い横棒が median、ひし形と誤差棒が標本平均と t 分布 95% 信頼区間 (df 4)、
  灰色の破線が stock (無 backoff、`BACK_OFF=0`) の median = 効果の分母。adopted は採用静的 backoff fixed 2 µs (`BACK_OFF=1`, `BACKOFF_FIXED=2`)。
  median 比の効果 −5.7841% (`effects.rr95 = -0.057841193339621455`、certification.json の値を写す) を直接ラベルで置く。
- 下段 1 panel: 記述的な先行指標として cell あたり 1 点の abort 率 (stock 0.1547、adopted 0.145)。5 rep の集約値ではなく、**5 rep のうち throughput が median に最も近い rep の値**
  (runner の代表 rep 規則、稿 §2.3・§4 限定 6)。信頼区間は付けず、因果の機序も主張しない。

**言えるのは protocol の status まで**である。A-6 は policy の workload が rr95 の 1 つなので、outer status `reject` はその 1 問 (adopted の median が stock を上回るか)
の答えそのものである。1 attempt・5 標本の中央値比較であり、有意差・between-run floor 超の退行・別走行での再現性・研究の失敗は判定しない (D12、稿 §0・§4 限定 1)。
read-heavy で stock が最良であることの証明でも、静的 backoff 一般が read-heavy で有害であることの証明でもない (稿 §4 限定 3)。
**性能の `reject` と正しさの `certified` は別の段である** (D1993 項 2): 正しさは別の trace-enabled 走行から来て 2 cell とも certified (legacy 1 + performance 条件 5)、
これは性能の認証ではない。性能の `reject` は取得済みの正しさ証拠を取り消さない (稿 §2.2)。正しさ証拠の射程は稿 §4 限定 4 の (i)〜(v)
(L01 の point-key trace、D1257 の argv 未記録、artifact hash 単独は compile-out の証明でない、条件関門は記録まで、`src_token` 一致は翻訳単位全体の意味一致を保証しない) に従う。
図を variant 採用の根拠にしない (絶対規律 2)。

## 既存図との関係

- **`fig5_` / `fig6_` / `fig7_` (A-2) の後継でも前身でもない。** A-2 は write-heavy / balanced の 4 cell、本図は read-heavy の 2 cell で、別 policy・別 attempt・別 workload である。
  A-2 と集計せず (稿 §3.4)、前後比較として読まない (絶対規律 7)。
- **B-10 read-heavy 本走の 3 block (同符号・同程度、[T-2430]) は描かない。** それは近接条件の別実行の履歴的照合であって独立再現ではなく (稿 §3.1・§4 限定 7)、pool も併記もしない。
  caption で「pool しない」と 1 文触れるだけである。
- 実行基盤測定で得た −4.876% (D1870) と旧環境の read-heavy の値は attempt に数えず、描かない (稿 §3.3・§3.5)。
- 論文ストーリー 2026-09-20 版 §8 第 2 (A-6) と単独稿の限定 11「図は無い」を埋める図である。稿の bytes は変えない (凍結物)。
  稿の限定 11 への追補は `docs/paper-story/README.md` の results 系列の節にある。2 本目の論文と共用しない (D1637)。

## 入力

- 権威 bytes (repo 内、tracked): `output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json`
  (`paper-story-a2-certification-result/v4`、SHA-256 `3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab`) と同 dir の `raw-manifest.json`
  (`paper-story-a2-full-raw-manifest/v4`、SHA-256 `8d17953575afc4594df052d5b5b778291c4d41a1564bb1fbc2d29e8d1df94ef9`)。
  生成器は repo 所有の pin 表 (`CANONICAL_SHA256`) でこの 2 つを照合する。**pin は CLI から渡せない。** 値は稿 §5.1 の表と同じ。
- 外部入力 (repo 外、durable authority): root `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b` の
  campaign WAL 1 本、raw cell 2 本、campaign lock 1 本、campaign claim 1 本、条件関門の受領証 1 本の計 6 file (1 workload なので fig6 の 12 file の半分)。
  root 相対 path と SHA-256 を provenance の `external_inputs` に記録し、tracked `raw-manifest.json` の `files` と一致を要求する。
  5 標本 (`performance.samples_tps` / WAL `bench_done.tps`) の出所はここだけで、certification.json は median しか持たない。
- 再計算と照合: 各 cell の median は 5 標本から再計算して certification の `median_tps` と一致を要求する。効果は certification の `effects` を写し、
  median の比からの再計算と `abs_tol = 1e-12` で照合する (`effect_crosschecks`)。生成器は判定を作らない。
- identity: 受領証 / raw / WAL / certification の 4 者で `src_token` が一致し、stock cell は `stock`、adopted cell は非 `stock` の SHA-256、
  両 cell とも `source_binding_status = bound` であることを要求する (fig6 と同じ)。この一致が言えるのは identity 層までで、証明力の上限は稿 §4 限定 4 (iii)(v) のとおり
  (artifact hash 単独は compile-out の証明でなく、`src_token` 一致は翻訳単位全体の意味一致を保証しない)。
- 拒否条件: SHA-256 不一致 (tracked 2 file、外部 6 file)、certification / raw-manifest の leaf が pin 表 `CANONICAL_SHA256` (A-2 の 2 attempt + A-6 = 3 leaf) に無い、
  study が `STUDY_PROFILES` の exact 2 件 (A-2 / A-6) に無い (legacy profile は A-2 のみ)、schema / attempt / cell 順序 / policy identity の不一致、
  6 file 閉包の過不足、`source_binding_status` ≠ bound、`src_token` の 4 者不一致、`correctness.status` ≠ certified、median / effect の不一致、
  raw の性能標本が trace-enabled、caption_source (稿) の不在。いずれでも成果物を出さない。
- **caption_source:** provenance の `tracked_inputs` に `kind: "caption_source"` として稿 `docs/paper-story/results/2026-09-18-a6-certification-reject.md` の
  path と SHA-256 を記録する (`authority_scope` = caption の固定文と限定の言い方の出所であって、測定値・protocol status の一次権威ではない)。
  稿は provenance の SHA-256 を持たない (F36 の自己参照回避)。稿は凍結物なので着地後に変わらない。

## 再現

```bash
python3 tools/plotting/plot_a2_certification.py \
  --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b \
  --certification output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json \
  --raw-manifest output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json \
  docs/paper-story/figures/fig11_a6_certification_reject
```

図番号は出力 prefix の `fig<N>_` から導く。`fig<N>_` の形でない prefix は出力前に拒否する。生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font 解決に依存する。
着地したバイト列の同一性は provenance JSON が記録した `outputs[].sha256` と `orchestrator/tests/test_plot_a2_certification.py` の
`test_landed_fig11_repo_closure_and_caption_when_present` が守る。`validate_repo_closure` が見るのは provenance の自己整合と hash
(repo 内の tracked 入力 = 権威 bytes 2 file + 稿と出力の SHA-256、`external_inputs` の各 path が raw-manifest に同じ SHA-256 で載ること、provenance の cells から
作り直した artist / caption との一致) までで、権威 bytes との値の再照合は同 test の直接照合 (provenance の `study` / `outer_status` / `effects` / `cells[].median_tps` が
tracked certification.json と一致、`external_inputs` の path 集合が raw-manifest の `files` と完全一致) が担う。durable root は読まない
(root が読めるときは `validate_external_sources` が 6 file の SHA-256 も照合する)。生成器の `generator.sha256` は生成時点の記録であり、
現行 source を縛る pin ではない (規律 7)。

## 条件関門についてこの図が言えること

raw manifest は `use_class="paper"` かつ `admitted=true` と記録する canonical な admission record を 2 cell 分束縛している。
**成果物が保存しているのはそこまでで、元の supply / meaning records は残らない** (稿 §1.4・§4 限定 5)。したがって caption は
「関門を実施し通過した」ではなく「そう記録された受領証が束縛されている」と書く (fig6 と同じ)。

## 作図規約への適合

fig6 と同じ生成器なので適合の形は同じである — §1 は 5 標本・median・効果をその場で再計算して hash 束縛の certification と照合する (判定は凍結 report を権威として読む。fig5 節の「作図規約への適合」が書く限定例外と同じ)、§2 標本 + 平均 ± t95 CI (df 4、標本の記述)、§3 stock median の破線、§6 provenance (入力の path と SHA-256・測定条件・主要数値・caption・再現 argv)、§9 保存前の layout check。本図で違うのは次だけ。

- §5: 図中ラベルは `no backoff` / `fixed 2 us`、panel 題と脚注の workload 名 (read-heavy、rratio 95 / rr95) だけ。
- §9: layout check は 2 行 × 1 列 (axes 数の不一致も拒否)。
- §10: fixture は実寸 (1 workload × 2 cell × 5 標本、verify 12 記録、receipt 2 frame × 2 cell、6 file) で本物の Figure を layout check へ通す。実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、`orchestrator/tests/test_plot_a2_certification.py` が本 README への収録と
生成器の決定的な組み立てとの一致を検査する。英文で書く。値 (attempt / status / request / host / 時刻 / 効果 / 条件 / pin) は生成器が
certification.json・raw manifest・WAL から書式化し、限定の固定文 (1 workload なので outer status はその判定そのもの / 正しさ certified は性能の認証でなく
性能 reject は正しさ証拠を取り消さない / 1 attempt・5 標本で floor 超・再現性・研究の成否・read-heavy 一般を判定しない / B-10 は履歴的照合で pool しない・A-2 と pool も前後比較もしない /
CI は標本の記述) を逐語で含む。

> Figure 11. A-6 formal certification attempt a6-20260908b (outer status: reject). The single workload campaign was request 982234.nqsv on bnode031, campaign claim recorded at 2026-09-07T16:29:41.491476+00:00; with one policy workload, the outer status is that workload's verdict itself. The top row shows all five trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff median and the effect denominator. The median effect copied from certification is read-heavy (rr95) fixed 2 us -5.7841%. M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision. The displayed outer status is the protocol status based on the predefined median ratio: the adopted cell's median did not exceed the stock cell's median. This is one attempt of five samples per cell; it does not decide a between-run floor exceedance, repeated-attempt reproducibility, or research success or failure, and it does not show that stock is best for read-heavy or that static backoff is harmful for read-heavy in general. The value is not extrapolated to other read ratios, machines, CCBench pins, or concurrency-control protocols. The bottom row is a descriptive leading indicator: one abort-rate observation per cell, taken from the repetition whose throughput is closest to the median (the runner's representative-repetition rule), with no confidence interval and no causal mechanism claim. Correctness comes from separate trace-enabled runs: all 2 cells were certified. This is not a performance certification. The performance reject does not withdraw that correctness evidence. That evidence is limited: L01 limits it to point-key traces; under D1257 the correctness argv was not independently recorded; artifact hashes alone are not compile-out proof (the evidence is source-routed); and src_token equality does not by itself establish semantic identity of the whole translation unit (limitations (i) to (v) of the results note). The raw manifest binds canonical condition-admission records reporting use_class="paper" and admitted=true for all 2 policy cells; the original supply and meaning records are not retained in this artifact. Conditions: 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, CCBench pin 511c953, no perf, trace-disabled performance. The same-sign B-10 read-heavy blocks are a historical concordance under nearby conditions, not an independent reproduction, and are not pooled here; the A-2 attempts measured other workloads and are neither pooled nor compared as before/after.

## proof chain

- 図に描いた標本・median・平均・CI・abort 率・効果 → provenance JSON の `cells` と `artist_series`
- 判定と効果 → `certification.json` の `status` / `effects`。生成器は再計算せず、`effect_crosschecks` に再計算値との一致を記録する (rr95 の `authority_matches` が真)
- 標本の由来 → durable authority の WAL `bench_done` と raw cell JSON (provenance の `external_inputs` に root 相対 path と SHA-256)
- 入力の束縛 → tracked `raw-manifest.json` の `files` (provenance の `tracked_inputs`) と生成器の pin 表、稿 §5.1 の表
- source identity → 受領証 / raw / WAL / certification の 4 者で `src_token` が一致すること、stock cell は `stock`、adopted cell は非 `stock` であること
- 正しさの記録 → `certification.json` の `cells[].correctness` (2 cell とも `status = certified`、legacy 1・performance 5)。性能の認証ではなく、射程は稿 §4 限定 4 (i)〜(v)
- 限定と条件の言い方 → 稿 (provenance の `caption_source`、SHA-256 束縛)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_a2_certification.py` (`test_landed_fig11_repo_closure_and_caption_when_present`: 着地 bytes の SHA-256、caption の逐語収録、
  caption_source の現 SHA-256、provenance と tracked certification.json / raw-manifest の値の直接照合)
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-18-a6-certification-reject.md`
- 判定の性質と関係の裁定 → D12 (protocol status を成否の宣告へ拡張しない)、D1993 項 2 (性能 reject は正しさ証拠の欠落でない)、[T-2430] (B-10 との整合は履歴的照合、反復 attempt は行わない)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256

次の 3 行が着地 bytes の正本である。`orchestrator/tests/test_plot_a2_certification.py` の着地 test が、この 3 行の値と
着地 file の現物 SHA-256 の一致を検査する (行の形は `- \`<basename>\` SHA-256: \`<64 hex>\`` で固定)。

- `fig11_a6_certification_reject.png` SHA-256: `6781f24be93699c7443b784ec5167a7ab1b590c6d7a89fa07fc68504b6fd1549`
- `fig11_a6_certification_reject.pdf` SHA-256: `dcaf1b26d5153c650ea12f8b49773239a12a8a4cbc6d967d1e7399af4701df26`
- `fig11_a6_certification_reject.provenance.json` SHA-256: `3f57baff302c43d9dede1e4c48ee94c011e3befe964928ec2283895eaeb22f16`

provenance が `caption_source` として束縛する稿の SHA-256 は `34a968428f867ce26479abe37320946b6eb8149007244dfe1d18a18446633850`
(稿は凍結物で、着地後に変わらない)。

---

# `fig12_k2_manual_loop_dataflow` — K2 手動 loop 3 巡のデータフロー (稿 `results/2026-09-20-k2-manual-loop-three-rounds.md` の説明図、値なし)

## 何を示す図か

稿 `results/2026-09-20-k2-manual-loop-three-rounds.md` (凍結物、B-6 の材料) が記録した **K2 手動 loop の 3 巡** (§0.1: 1 巡 = 提案 (planner + coder) →
評価 1 本 → critic) の**データフロー**を、1 枚の模式図にしたものである。fig2 系 (機序の説明図) と同じ「説明図」の扱いで、fig3b と同じく**性能値を 1 つも描かない**。
横 = 4 列 (巡 1 / 巡 2 / 「巡 2 の後 (巡ではない)」= 未評価の proposal-3 / 巡 3)、縦 = 6 lane (親の射影 → planner → coder → 提案 → 評価 → critic)。描くのは次だけである。

- **役割と遮断の所在** (§1.4): 親 session が型付き JSON を射影して inline で渡す → `planner-v4` (role 定義が `tools: []`、tool access の構造遮断) →
  `coder-v4-autonomous-k2` (同) → 提案 file (backoff hole の literal 1 つ) → Pegasus 計算ノード job 1 本 (trace-enabled の verify build と trace-disabled の
  bench build は別 build・別 run、campaign WAL の terminal record) → `critic` (**Bash を持つ legacy role**。tool なしではなく、B-4 の材料にならない理由)。
  生成器は 3 role の定義 file の frontmatter `tools:` を読み、JSON の宣言 (`tools_none`) と一致することを検査する (不一致は成果物を出さない)。
- **親が射影する入力の key** (§1.4): planner = `current_perf` / `leading_indicators` / `whiteboard` / `knowledge_input`、coder = `baseline` / `planner_direction` /
  `whiteboard` / `knowledge_input` / `leakproof_context`。巡 3 だけ両方に `k2_critic_diagnosis` (exact 6 field: `attribution` / `recommend` / `avoid` / `uncertainty` /
  `data_boundary` / `source_sha256`、D2155) が加わる。K2 知識源 (別機体の測定 WAL 1 件、3 巡とも同一 bytes、受領証は job 内で verified、data boundary 宣言) は全巡共通の帯。
- **還流の矢印** (§0.1、§2.2、§2.3): 実測の還流 2 回 (巡 1 の評価 → 巡 2 の提案入力 = m1、巡 2 の評価 → proposal-3 と巡 3 の提案入力 = m2a / m2b。還流元の評価で
  数えて 2 回、描く経路は 3 本)、診断の還流 1 回 (critic-2 → 巡 3 の入力、型付き経路 = d1)。描くべき否定も描く (点線 + ×) — critic-1 → 巡 2 の型付き入力は無い
  (経路未実装、a1)、proposal-3 は診断 key 無しで既知値 20 を再提案し未評価 (a2)、巡 3 の後に提案は無い (a3)、同 job の stock 対照は未達 ([T-2795] 裁定待ち、破線枠)。
- **規律 6 の検査点** (§2.4): 各 role cell の右上の盾形 marker と `data boundary: none detected` の 1 行。role の**自己申告**で形式が role ごとに違い
  (coder = 構造化 field `data_boundary_report.instruction_like_content_detected`、planner = `uncertainty` の散文、critic = 信頼境界検査の節)、機械 gate ではない。
  JSON は role ごとに typed (`form` は role 固定、`instruction_like_detected` は bool) で、true なら赤 × の marker と `data boundary: detected` に変わる
  (記録された 12 出力はすべて false)。

図に出る数は backoff の提案 literal (20 / 25 / 20 / 10、提案の同一性で proposal cell に 1 度だけ) と job id (1216 / 4947 / 4954 / 10761) と日付だけで、いずれも結果ではない。
列見出しの提案日は「各巡の記録による」(per round records)、評価日は job log による。

**この図が言わないこと** (稿の限定 1〜6 と同じ。caption にも逐語で置く): 性能の改善・退行・比較 (3 走は非同時刻の別 tree で、同 job の stock 対照が無い)、
知識・診断の因果効果 (各条件 1 回の別起動、統制なし。診断は「届いた」「参照したと申告した」までで「効いた」ではない、§2.3)、**B-6 の充足**、B-4 の材料
(critic が legacy)、`certified` の性能認証 (正しさ gate が `serializable` / anomaly 0 を返した意味だけ、§2.5)、遮断の完備 (tool access の遮断であって
リーク制御の完備ではない)、起動・送付・生成日・細かな順序の独立確認 (各巡の記録による。保存 prompt は送達証明ではない)。図を variant 採用の根拠にしない (絶対規律 2)。

## 既存図との関係

- 既存図 (fig1〜fig11) のいずれの後継でもない独立した新図。fig2 (機序の説明図) と同じ「説明図」の扱いで、fig3b (状態の模式図) と同じ値なしの JSON 駆動。
- 稿 §2.1 の表の値 (tps / abort 率 / CV / latency) は描かない。前後比較として読まない (絶対規律 7)。
- **2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637)。

## 入力

- **流れ JSON** `tools/plotting/k2_loop_flow_2026-09-20.json` (schema `izanagi-k2-loop-flow/v1`)。稿から人が写した射影で、**意味の正本は稿**である。各要素は
  `source_anchor` (`§1.4` / `§2.2 巡 1` の形) を持ち、生成器はその見出し行が稿に**ちょうど 1 行**あることだけを検査する (意味の一致は本 wave の段 6 レビュー B が
  逐語照合で担った。下の proof chain)。JSON は凍結物ではない (凍結物は PNG / PDF / provenance JSON) が、再現入力として残す。
- **caption_source = 稿** `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md`。path は生成器に固定 (CLI から別の稿を渡せない)。生成器は稿の bytes を
  1 回読み、anchor の検査と SHA-256 の記録にだけ使う。**値・判定を稿から再計算しない。** 稿は provenance の SHA-256 を持たない (F36 の自己参照回避)。稿は凍結物なので
  着地後に変わらない。
- **role 定義 3 file** `.claude/agents/{planner-v4,coder-v4-autonomous-k2,critic}.md`。frontmatter の `tools:` 行だけを読み (`[]` ⇔ `tools_none: true`)、
  3 file の SHA-256 を provenance `inputs` (kind `role_definition`) と `roles[]` に記録する。**これは生成時点の記録であり、着地後の一致を要求しない**
  (role 定義は凍結物ではない。着地 test は稿の SHA-256 だけを現物と照合する)。
- **FIGURE_CONVENTIONS §1 (入力は WAL/dat のみ) との関係:** §1 は数値を描く図の規約である。本図は値を持たない模式図で、入力は「人が凍結稿から写した射影」に限る。
  fig3b と同型の、本図に限った限定であり、数値図への一般的な免除ではない。
- **拒否条件 (生成器は成果物を出さない):** schema / key 集合の不一致 (未知・不足・重複 key、NaN / Infinity)、enum 外 (direction / magnitude / kind / verdict / stop /
  discipline6 の form)、value が整数 1..1000 でない・coder と proposal で不一致、`evaluated` と evaluation / critic / 評価日の不整合、`not-a-round` 列の制約違反、
  巡 3 以外の `k2_critic_diagnosis`、planner / coder / diagnosis の key 配列の不一致、矢印の端点不在・id 重複、job / instance の重複、anchor の不正・不在・非一意、
  role frontmatter との不一致、自由文の数量 (`=`、`%`、単位語、数詞、宣言外の数字入り token)、prefix が `fig<N><letters>_` の形でない、既存の 3 出力のいずれかが
  存在する (上書きしない)、保存前の layout check (全 Text の figure 内包・所属領域内包・相互非交差・兄弟領域非交差・marker の非交差・**矢印線分と Text の非交差**) の違反、
  描いた矢印と JSON の矢印の不一致。

## 再現

repo root から、**計測機の外** (login node で生成した) で次を実行する。出力 prefix は着地済み file と衝突しないものにする (既存の 3 出力があれば生成器が拒否する)。

```bash
python3 tools/plotting/plot_k2_loop_flow.py /path/to/reproduction/fig12_k2_manual_loop_dataflow
```

作成時は `docs/paper-story/figures/fig12_k2_manual_loop_dataflow` を prefix にした (provenance の `argv` に逐語)。図番号は prefix の `fig<N><letters>_` から取る (`12`)。
`--flow` 省略時の既定は上の JSON、`--repo-root` 省略時は生成器の位置から repo root を決める。

### 再現できるのは「内容」であって「配置」や「バイト列」ではない

再現の対象は、記録された流れ (列・lane・cell の表示文字列 50 件、矢印 7 本の id / kind / 端点、marker の形、caption) である。**配置は描画環境に依存する** —
折返しと行位置は font の実測幅・高さから決まり、matplotlib の版と font 解決 (DejaVu Sans) が違えば改行や位置が変わりうる (収まらなければ layout check が
保存前に拒否する)。provenance JSON は生成時刻 (`generated_utc`) を持ち、PDF は matplotlib が生成日時を埋めるので、byte 一致も保証しない。着地 bytes の SHA-256 は
下に記録し、着地 test が現物と照合する。

## 作図規約への適合

- §1: 値を描かない模式図なので WAL/dat の再計算は無い (上の「入力」の限定)。数値の混入は生成器が自由文検査で拒否する。
- §2 / §3 / §4: 反復・基準線・二軸を持たない (数値図の項目は該当しない)。
- §5: 図中ラベルは role 名・入力 key 名・instance 名・job id・固定語だけで、内部識別子は JSON の key 名 (稿 §1.4 と同じ) に限る。凡例と脚注で一度だけ展開する。
- §6: provenance に入力 5 file (JSON・稿・role 定義 3 本) と生成器・出力 2 file の SHA-256、描いた 50 項目 (`drawn_items`: id・kind・実表示文字列)、
  描いた矢印 7 本 (`arrows`: id・kind・端点・可視)、role の遮断宣言 (`roles`)、caption、展開済み argv、matplotlib / numpy の版を記録する。
- §7: login node で生成 (計測機の外)。
- §8: matplotlib / numpy のみ、自己完結 (既存生成器を import しない)。PNG (200 dpi) と PDF を出す。
- §9: 保存前に Agg renderer で layout check を走らせ、違反があれば 3 成果物を 1 つも出さない。
- §10: 単体テスト `orchestrator/tests/test_plot_k2_loop_flow.py` は**実 JSON そのもの**を実寸 fixture として本物の Figure を layout check へ通し、
  provenance を独立に照合する。実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、`orchestrator/tests/test_plot_k2_loop_flow.py` の着地 test が本 README への収録を検査する。
英文で書く。回数語 (twice / three times / once) は JSON の矢印から生成器が組み、限定の固定文 8 つ (schematic で性能値なし・3 走を比較しない / certified は正しさ gate の
意味だけ / planner・coder は tool なし・critic は legacy で B-4 の材料でない / 規律 6 の marker は自己申告 / 知識・診断の因果効果を主張しない / 同 job stock 対照は未達・
提案値は literal であって結果でない / 手続きは各巡の記録による・保存 prompt は送達証明でない / B-6 を判定しない・遮断は tool access に限る) を逐語で含む。

> Figure 12. Data flow of the K2 manual synthesis loop over three recorded rounds, read from the frozen results note 2026-09-20-k2-manual-loop-three-rounds.md. In each round the parent session projects typed JSON inputs (planner: current_perf, leading_indicators, whiteboard, knowledge_input; coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context) to planner-v4 and coder-v4-autonomous-k2; the proposal is one backoff literal evaluated by one Pegasus compute-node job with separate trace-enabled verify and trace-disabled bench builds and a campaign WAL terminal record; critic reads the digest and the WAL. Measurement reflux occurred twice between the recorded rounds (the first evaluation into the second proposal inputs; the second evaluation into the inputs of an unevaluated proposal and of the third round), and diagnosis reflux occurred once (the second critic into the third-round inputs as the typed key k2_critic_diagnosis with fields attribution, recommend, avoid, uncertainty, data_boundary, source_sha256, identical for planner and coder). Three measurement arrows are drawn because the second evaluation feeds both the unevaluated proposal and the third-round proposal; three dotted arrows mark absent paths. The unevaluated proposal, generated without a diagnosis key, re-proposed a known value. The planner and coder role definitions declare no tools (structural blockade); critic is a legacy role with Bash access, so these rounds are not material for the B-4 leak-control ablation. Certified means only that the trace-enabled verify run found the observed trace serializable with no anomaly; it is not a performance certification and not a choice among candidates. Discipline-six marks are role self-reports that external inputs contained no instruction-like strings; none is reported in the recorded rounds. Their form differs by role and they are not a mechanical gate. No causal effect of the knowledge source or of the diagnosis on the proposed values is claimed: each condition was launched once, without a control. The same-job stock control was not achieved and awaits a ruling; proposal values are backoff literals, not results. This is a schematic of recorded data flow; no performance values are drawn and the three runs are not compared. Role launch times, inline delivery, proposal dates, and the fine ordering of steps rest on each round's records; saved prompts and inputs are not proof of delivery. This figure does not judge whether B-6 is met; the tool-less declaration concerns tool access only, and leak control is not complete.

## proof chain

- 図に描いた 50 項目と矢印 7 本 → provenance JSON の `drawn_items` / `arrows` (生成器は JSON から期待される集合と描いた artist を保存前に照合する)
- 各項目の文字列・還流の端点・role の遮断・日付 → `tools/plotting/k2_loop_flow_2026-09-20.json` (provenance `inputs[kind=flow]` の SHA-256)
- 写しの出所 → 稿 `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` (provenance `caption_source` の SHA-256。各要素の `source_anchor` が指す
  見出し行の一意な存在を生成器が検査)
- 写しが稿の意味と一致すること → 本 wave の段 6 read-only レビュー B (drawn_items 50 件・矢印 label 7 件・caption 全文の逐語照合表、不一致 1 件 = 提案日の留保の
  脱落を fix1 で是正) と焦点再レビュー。一次資料は `output/insights/2026-09-20/k2-loop-fig12/README.md`
- role の遮断 → `.claude/agents/{planner-v4,coder-v4-autonomous-k2,critic}.md` の frontmatter (provenance `roles[].sha256`、生成時点の記録)
- 生成器 → `tools/plotting/plot_k2_loop_flow.py` (provenance `generator.sha256`)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`
- 稿の限定 → 同稿冒頭の限定 1〜6 と §3

- 実走 → login node (pegasus02、計測機の外)、2026-09-20 15:02 JST (provenance `generated_utc` 2026-09-20T06:02:37Z)、rc=0、3 成果物。wave 中の単体 test・焦点走・変異の実測値は一次資料 `output/insights/2026-09-20/k2-loop-fig12/README.md` に置く (本節は着地時点の記録を持たない)

## 着地 bytes の SHA-256

次の 3 行が着地 bytes の正本である。`orchestrator/tests/test_plot_k2_loop_flow.py` の着地 test が、この 3 行の値と着地 file の現物 SHA-256 の一致、
provenance の `caption_source.sha256` と稿の現物の一致、caption の本 README への収録を検査する (行の形は `- \`<basename>\` SHA-256: \`<64 hex>\`` で固定)。

- `fig12_k2_manual_loop_dataflow.png` SHA-256: `a6f2b550bd67ddfd05db193493736ef388b2a9f24d60916cb8964607dc3df991`
- `fig12_k2_manual_loop_dataflow.pdf` SHA-256: `c280037fe72fb60c4420864f1de1df1b28bbf5a7b5ed1c104d13244f2493cfcf`
- `fig12_k2_manual_loop_dataflow.provenance.json` SHA-256: `76c03b92cb106fa0d73417c1f6357d5b0ded1a6e915ca210013fdb509dd1aaea`

---

# `fig13_b10_waiting_grid_forest` — B-10 待ち方 grid 正式走 (report `978195.nqsv`) の 3 族 Holm 判定と 36 cell の効果量・95% 区間・等価域 ±3.0% の forest 図

## 何を示す図か

事前登録 `docs/b10-backoff-shape-preregistration.md` の発効版 (commit `77b33e37d`、blob `ea910de32…`) に対して report phase (request `978195.nqsv`、2026-09-05 JST、解析コード commit `2a338449b`) が出した
**1 つの判定** — 登録した `constant` 対 `symmetric-modulo` の contrast を write-heavy / balanced / read-heavy の 3 族 × 18 対で検定し、36 cell の効果量と 95% paired-block 区間を等価域 ±3.0% と並べたもの —
を、単独稿 `results/2026-09-20-b10-waiting-grid-formal.md` (§2.2・§2.4) と同じ一次資料 (report の provenance JSON) から描いた**結果図**である。

- 1 行 × 3 panel (左から write-heavy / balanced / read-heavy)。各 panel の縦軸は登録 grid の μ 6 行 (2 / 5 / 10 / 25 / 50 / 100 µs、上から下)、横軸は `symmetric-modulo` の中央値 throughput ÷ `constant` の中央値 throughput − 1 (%) で、
  3 panel 共通の範囲。帯は事前登録の等価域 ±3.0%、縦線は 0 (= `constant` 参照)。
- 各行: 空丸 = `constant` 参照 cell (効果 0、区間 [0, 0]。自分自身との対なので構成上 0。report にそのまま並ぶ 18 cell)。塗り印 + 横線 = `symmetric-modulo` cell の効果 (3 block の対相対効果の平均) と 95% paired-block 区間
  (student-t、自由度 2、平均 ± 4.302652729911275 × 標本標準偏差 / √3)。灰色の小さい縦 tick = 区間の材料である 3 block の対相対効果 (稿 §2.3 の 54 対のうち当該 cell の 3 つ)。
  `overlaps-equivalence-boundary` の 4 cell (write-heavy μ 2・μ 25、balanced μ 2・μ 25) は印の形を変えて凡例で区別する。
- panel 題 = 族の判定 (`outcome` `different`、Holm p、raw p の 2^18 分母の分数表記、対 18、18 対の和の符号)。3 族とも `testable` / `different`、方向は 3 族とも `symmetric-modulo` が高い側 (稿 §2.2)。

**言えるのは事前登録 §3 の「書ける主張」まで**である。登録した 2 つの特定の実装の間で待ち方の違いが throughput を動かすかを事前登録した手続きで検定し、3 族とも `different` だった。
方向・効果量・区間は**この contrast に限って**述べる。**区間が ±3.0% の帯の内側にあること (32 cell) は「区間の位置」の分類名であって等価性の成立ではなく、等価性検定は行っていない** (稿 §3 限定 16)。
**36 cell の個別の有意差は判定しない** — 検定は 3 族の族水準の exact 符号反転 permutation + Holm だけで、cell の区間は記述である。境界を跨ぐ 4 cell も外側 0 も同じ意味で読む。
`different` は protocol の出力であって成否の宣告ではない (D12)。機序 (なぜ `symmetric-modulo` が高い側か) は述べない (D1097、D1678、稿 §3 限定 3)。`binary` / 3 水準 ladder / 用量反応 / 直交切り分けの一般化について何も言わない (事前登録 §3・§8・§9)。
**`official_certification` は `false` で、この性能値を根拠に variant を採用してはならない** (絶対規律 2)。正しさは trace 有効ビルドの別走行 (135 / 135 cell certified) についてで、性能の認証ではない (稿 §1.6・§3 限定 8)。
3 workload は別 job・別日・別 driver 版で、workload 間の絶対 throughput は比べない (稿 §3 限定 6)。判定は 2026-09-07 の D1678 で閉じており、本図はそれを改めない。

## 既存図との関係

- **`fig8_` / `fig8b_` (静的右 tail の 2 cohort) と合成・比較しない。** 右 tail は別の事前登録 (`docs/b10-backoff-static-tail-preregistration.md`)・別の格子 (1000〜9999 µs)・別の driver・別の判定述語の事実である (D2157 の精神を待ち方 grid との間にも当てる、稿 §0・§3 限定 10)。
- **`fig2b_` / `fig2c_` (別系列の backoff sweep) も本判定の図ではない** (稿 §3 限定 11)。A-2 / A-6 / B-7 / [T-1998] の図 (fig5〜fig7、fig10、fig11) の certification・退行判定とも合成しない (絶対規律 7)。
- 既存図の後継ではなく独立した新図。稿 §3 限定 11「論文図は無い」は起草時点 (2026-09-20) の事実で、本図はその後に作られた。**稿の bytes は変えない** (凍結物。provenance が現 SHA-256 で束縛する)。
  `docs/paper-story/README.md` の results 表の当該行は触っていない (ユーザー指示。同行の「図は無い」は起草時点の記述)。2 本目の論文と共用しない (D1637)。

## 入力

- 権威 bytes (repo 内、tracked、生成器の pin 表 `PINNED_SHA256` で SHA-256 束縛。pin は CLI から渡せない):
  `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json` (`b10-backoff-shape-provenance/v2`、SHA-256 `a4390603f20fbc8fdb74c482a17ae880f292e340e79846c31f5d923d71789fca`。
  判定 `judgement.families[]` / `judgement.cell_effects[]`、135 record、事前登録 spec、submission の束縛を含む) と
  `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_report_978195.nqsv-23409962b76b.md` (SHA-256 `e237d17db4f02818ea27049165fa90da4c19adea1bc8bca9b165b73b77e8e768`)。値は稿 §4.1 の表と同じ。
- 外部入力 (repo 外、稿 §4.2 の report 行): root `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape` の `submissions/23409962b76be959bb523a0cd5a31bc1/submit-receipt.json` (受領証、SHA-256 `93a1cd74…` = provenance JSON の `submission.receipt_sha256`) と
  `submissions/23409962b76be959bb523a0cd5a31bc1/job-attempts/978195.nqsv/job-result.json` (job 結果、SHA-256 `d5d4a0ee…`、`driver_rc` 0)。生成器は両 file の SHA-256 を定数で持ち、request / nonce / phase / commit が provenance JSON の `submission` と一致することを要求する。
- 再計算と照合 (生成器は判定を作らない): 135 record の `median_tps` から 54 対の対相対効果を block-major / μ-minor の順に組み立て `judgement.families[].differences` と一致、Holm p を昇順から再計算して一致、raw p × 2^18 が整数、
  18 cell の効果 (3 block の平均) と区間 (± 4.302652729911275 × 標本 sd / √3) を再計算して一致、等価域 ±3.0% との関係を区間の位置から再分類して `equivalence_relation` と一致、`constant` 18 cell が 0 / [0, 0]、
  全 135 record が `correctness_certified` / 非 `missing` / 非 `unstable`、登録 108 cell の曝露 (backoff 呼び出し ≥ 10,000)。report .md については Holm 3 行の値 (outcome / 対 / raw p / Holm p の丸め) の照合と、cell effects 節が 36 行あるという行数の照合だけを行う
  (cell の値は report .md でなく provenance JSON 側で 135 record から全件再計算する)。**raw p 自体 (全 2^18 列挙) は再計算しない** (report の仕事)。
- 拒否条件: SHA-256 不一致 (tracked 2 file、外部 2 file)、schema / alpha / spec SHA / 格子 / 族構成 / 受領証 identity の不一致、族数 ≠ 3、対 ≠ 18、`outcome` ≠ `different`、`status` ≠ `testable`、Holm p > α、対差の順序または値の不一致、raw p が 2^18 分母の分数でない、
  Holm 再計算の不一致、cell 数 ≠ 36、効果 / 区間 / 等価域関係の不一致、`constant` cell が 0 でない、record 数 ≠ 135、median と 5 rep の不一致、未認証 / missing / unstable の record、登録 cell の曝露不足、`official_certification` が `true`、較正 (records / threads / env) と workload 条件 (skew / rratio / rmw / max_ope / extime) の定数不一致、caption_source (稿) の不在。いずれでも成果物を出さない。
- **caption_source:** provenance の `tracked_inputs` に `kind: "caption_source"` として稿 `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` の path と SHA-256 を記録する (`authority_scope` = 限定・条件の言い方の出所であって、測定値・判定の一次権威ではない)。
  稿は provenance の SHA-256 を持たない (F36 の自己参照回避)。稿は凍結物なので着地後に変わらない。

## 再現

```bash
python3 tools/plotting/plot_b10_waiting_grid_forest.py \
  --evidence-root /work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape \
  docs/paper-story/figures/fig13_b10_waiting_grid_forest
```

図番号は出力 prefix の `fig<N>_` から導く。`fig<N>_` の形でない prefix は出力前に拒否する。生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font 解決に依存する。
着地したバイト列の同一性は provenance JSON が記録した `outputs[].sha256` と `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` の
`test_landed_fig13_repo_closure_and_caption_when_present` が守る。`validate_repo_closure` が見るのは provenance の自己整合と hash (repo 内の tracked 入力 = 権威 bytes 2 file + 稿と出力の SHA-256、
provenance の値から作り直した artist / caption との一致、tracked JSON からの再計算との一致) までで、repo 外の受領証は読まない (root が読めるときは `validate_external_sources` が 2 file の SHA-256 も照合する)。
生成器の `generator.sha256` は生成時点の記録であり、現行 source を縛る pin ではない (規律 7)。

## 作図規約への適合

- §1: 図の数値は report provenance JSON の判定を写し、135 record の `median_tps` からその場で再計算して一致を要求する (判定は凍結 report を権威として読み、生成器は作らない。fig5 節の限定例外と同型)。
- §2: 反復の不確かさは cell の 95% paired-block 区間 (3 block、df 2) で描き、区間の材料 (3 block の対相対効果) も点で見せる。
- §3: 比較対象 `constant` は 0 の縦線 + 各行の空丸 (参照 cell) として、主系列と同じ軸上に置く。
- §5: 図中ラベルは `constant` / `symmetric-modulo` / workload 名 / μ と判定名だけ。展開は caption で 1 回。
- §6: provenance に入力の path と SHA-256・測定条件 (スレッド数 48、レコード数 1,000,000、Zipf skew 0.9、read ratio、rmw、max operations、1 rep の秒数、env = Pegasus 計算ノード。report provenance JSON の `calibration` と `preregistration.spec.workloads` / `spec.execution` から読み、定数と一致を要求する)・主要数値 (3 族の p、36 cell の効果と区間、summary)・caption・再現 argv。測定条件は図の脚注と caption の `Conditions:` 文にも出す (段 6 review B の must-fix で追加)。
- §7: login で生成。§8: matplotlib + numpy のみ。§9: 保存前の renderer-backed layout check (axes ちょうど 3、text の重なり・逸脱・隣 panel 侵入で 3 成果物を 1 つも出さない)。
- §10: fixture は実寸 (135 record、36 cell、3 族、report .md の Holm 3 行 + cell 36 行) で本物の Figure を検査へ通す。実データで実走して 3 成果物を確かめた (下の proof chain)。

## キャプション正文

日本語キャプション正文 (論文の結果節に置く文。値は provenance と稿 §2.2 / §2.4 の転記):

> 図 13. B-10 待ち方 grid の正式走 (report phase、request `978195.nqsv`) — 登録した `constant` 対 `symmetric-modulo` の 1 contrast についての 3 族 Holm 判定と 36 cell の効果量。
> 3 panel は write-heavy / balanced / read-heavy、各行は登録 grid の μ (2 / 5 / 10 / 25 / 50 / 100 µs)。横軸は `symmetric-modulo` の中央値 throughput を `constant` の中央値 throughput で割った比 − 1 (%)。
> 空丸は `constant` 参照 cell (効果 0、区間 [0, 0])、塗り印と横線は `symmetric-modulo` cell の効果 (3 block の対相対効果の平均) と 95% paired-block 区間 (student-t、自由度 2)、灰色の小さい縦 tick はその 3 block の対相対効果、帯は事前登録の等価域 ±3.0%。
> 3 族とも事前登録した手続き (18 対の両側 exact 符号反転 permutation、全 2^18 列挙、3 族 Holm、α 0.05) で `different` (write-heavy raw p 6702 / 2^18 = Holm p 0.02557、balanced raw p 70 / 2^18・Holm p 0.000534、read-heavy raw p 2 / 2^18・Holm p 2.29 × 10⁻⁵)、方向は 3 族とも `symmetric-modulo` が高い側。
> 36 cell の区間は等価域の内側 32・境界を跨ぐ 4 (write-heavy μ 2・μ 25、balanced μ 2・μ 25)・外側 0、判定不能 0。点推定が負なのは write-heavy μ 5 の 1 cell (−0.97%、区間は 0 を含む)。
> 区間が帯の内側にあることは区間の位置の分類名であって等価性の成立ではなく、等価性検定は行っていない。cell ごとの有意差は判定しない (検定は 3 族の族水準だけ)。`different` は protocol の出力であって成否の宣告ではない。機序は述べない。
> 静的右 tail の 2 cohort (fig8 / fig8b) と合成・比較しない。`official_certification` は `false` で、この性能値は variant 採用の根拠にならない。正しさは trace 有効ビルドの別走行 (135 / 135 cell certified) で、性能の認証ではない。
> 条件: Pegasus 計算ノード、48 スレッド、silo、レコード数 1,000,000、Zipf skew 0.9、read ratio 5 / 50 / 95 (write-heavy / balanced / read-heavy)、read-modify-write 無し、max operations 10、1 rep 3 秒、各 cell 5 rep × 3 block、CCBench pin `511c953`、3 workload は別 job・別日・別 driver 版で workload 間の絶対 throughput は比べない。

英文の caption 正文は provenance JSON の `caption` と同一文字列であり、`orchestrator/tests/test_plot_b10_waiting_grid_forest.py` が本 README への収録と生成器の決定的な組み立てとの一致を検査する。
値 (3 族の p / 対 / 和の符号、36 cell の集計、境界を跨ぐ 4 cell、負の点推定、条件、request、commit、pin) は生成器が provenance JSON から書式化し、限定の固定文 8 文
(族の outcome は事前登録手続きの分類名で研究判定ではない / 帯の内側は等価性ではなく等価性検定はしていない / cell ごとの有意差は判定せず検定は族水準 3 つだけ / 右 tail cohort と pool も比較もしない /
`official_certification` false・採用根拠にしない / この 1 contrast に限り一般・`binary`・用量反応・直交切り分けを言わない / 正しさは別走行で性能認証ではない / 3 workload は別 job・別日・別 driver 版、絶対 throughput を比べず機序を言わない) を逐語で含む。

> Figure 13. B-10 waiting-shape grid, preregistered contrast constant vs symmetric-modulo. write-heavy: different, raw p = 6702/2^18 = 0.02556610107421875, Holm p = 0.02556610107421875, 18 pairs, sum of paired effects +0.11202543669460518 (symmetric-modulo higher); balanced: different, raw p = 70/2^18 = 0.00026702880859375, Holm p = 0.0005340576171875, 18 pairs, sum of paired effects +0.13167898485090257 (symmetric-modulo higher); read-heavy: different, raw p = 2/2^18 = 7.62939453125e-06, Holm p = 2.288818359375e-05, 18 pairs, sum of paired effects +0.087727340019642996 (symmetric-modulo higher). Cell effects and 95% paired-block intervals: 36 estimable, inside 32, overlaps 4, outside 0, indeterminate 0; 1 negative point estimates and 8 positive interval lower bounds. Boundary overlaps: write-heavy mu 2 and 25, balanced mu 2 and 25. Constant cells are constructional references at zero with intervals [0, 0]; gray ticks show the three block-level paired effects. Conditions: Pegasus compute nodes, 48 threads, silo, 1,000,000 records, Zipf skew 0.9, read ratio 5 / 50 / 95 (write-heavy / balanced / read-heavy), read-modify-write disabled, max operations 10, 3 s per repetition, YCSB write-heavy / balanced / read-heavy, commanded mean wait mu 2, 5, 10, 25, 50, 100 us, 5 reps x 3 blocks, CCBench pin 511c953, report request 978195.nqsv, preregistration commit 77b33e37d, source commit 2a338449b. Each family's outcome is the preregistered procedure's classification and is not a research verdict. Intervals lying inside the +/-3.0% margin are reported as the position of the interval and are not a finding of equivalence; no equivalence test was performed. Per-cell intervals are descriptive and no per-cell significance decision is made; the only tests are the three family-level permutation tests with Holm adjustment. The static right-tail cohorts (separate preregistration, grid and driver) are neither pooled nor compared with this grid. official_certification is false; these performance values are not a basis for adopting a variant. Direction and effect sizes are stated for this one contrast only; nothing is claimed about waiting-shape effects in general, about binary, about a dose response of dispersion, or about a general separation of waiting shape from waiting amount. Correctness is recorded from separate trace-enabled runs (135 of 135 cells certified) and is not a performance certification. The three workloads ran as separate jobs on different days and driver versions; absolute throughput is not compared across workloads, and no mechanism is claimed for the direction.

## proof chain

- 図に描いた 36 cell の効果・区間・等価域との関係・3 block の対相対効果 → provenance JSON (図の) の `cells` と `artist_series`
- 3 族の判定 (`status` / `outcome` / raw p / Holm p / 対 18 / 対差 18 × 3) → report provenance JSON の `judgement.families[]`。生成器は再計算して一致を記録する (`crosschecks`)
- 36 cell の効果・区間・等価域関係 → 同 `judgement.cell_effects[]`。135 record の `median_tps` からの再計算との一致を `crosschecks` に記録
- 等価域 ±3.0%・自由度 2 の臨界値・α・全 2^18 列挙 → 同 `preregistration.spec.analysis` (事前登録 発効版 commit `77b33e37d` §5 の機械可読 spec)
- report phase の投入と完了 → repo 外の受領証と job 結果 (provenance の `external_inputs` に root 相対 path と SHA-256、`report` に request / nonce / phase / epoch / `driver_rc`)
- 入力の束縛 → 生成器の pin 表 `PINNED_SHA256` / `EXTERNAL_SHA256`、稿 §4.1・§4.2 の表
- 正しさの記録 → 135 record の `correctness_certified` (全 true)。性能の認証ではない (稿 §1.6・§3 限定 8)
- 限定と条件の言い方 → 稿 (provenance の `caption_source`、SHA-256 束縛)、事前登録 発効版 §3・§8・§9
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (`test_landed_fig13_repo_closure_and_caption_when_present`: 着地 bytes の SHA-256、caption の逐語収録、caption_source の現 SHA-256、
  `test_document_values_match_report_json`: 稿 §2.2 / §2.4 の値と tracked JSON の一致、`test_pins_match_results_document`: pin 2 値と稿 §4.1 の一致)
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md`
- 判定の地位と関係の裁定 → D1678 (現行 report で閉じる、§9 の 5 項目は見送り)、D12 (protocol 出力を成否へ拡張しない)、D2157 (右 tail cohort を合成しない)、D1092 / D1094 / D1097 (制約 3 つ)、D1637 (2 本目と共用しない)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256

次の 3 行が着地 bytes の正本である。`orchestrator/tests/test_plot_b10_waiting_grid_forest.py` の着地 test が、この 3 行の値と
着地 file の現物 SHA-256 の一致を検査する (行の形は `- \`<basename>\` SHA-256: \`<64 hex>\`` で固定)。

- `fig13_b10_waiting_grid_forest.png` SHA-256: `018bd8e9cbd86268f6e26d7d33b5d5b55bbe2fe7bf043f3832c43e001f23bde6`
- `fig13_b10_waiting_grid_forest.pdf` SHA-256: `8105d3dc918b85c62fa20c3d6374db8987de69d6c2e7c09f32ec7d8ff04675d5`
- `fig13_b10_waiting_grid_forest.provenance.json` SHA-256: `e5ee8147d8eac46f86359ac3556d739ae43ef64f36fd3fda6e5ae66d8cf5bb6c`

provenance が `caption_source` として束縛する稿の SHA-256 は `8dc6d69538c6785c0e3e56073ccc86c97e82699972265d5c521159a6cf72045a`
(稿は凍結物で、着地後に変わらない)。

---

# `fig14_a1_balanced5_sized_attempt2` — A-1 balanced5 sized 本走 attempt-0002 の対差平均 ± 登録済み区間 (非認証 lane の記述図、fig9 の兄弟)

## 何を示す図か

study `paper-story-a1-20260901-balanced5-sized-v1` の sized 本走 **attempt-0002** (2026-09-20 18:11 JST 投入、job `13220.nqsv` / `13221.nqsv` /
`13222.nqsv`、host bnode035 / bnode039 / bnode040、各 30 対 × 2 arm。D2172 項 2 が 1 attempt 限定で認可した、attempt-0001 と同じ policy・同じ root seed・
同じ物理順の独立の観測) について、fig9 と同じ形で描いた**記述図**である。3 workload (write-heavy rr5: `fixed10` − `no-backoff`、balanced rr50: `fixed5` −
`no-backoff`、read-heavy rr95: `fixed2` − `no-backoff`) の各 panel は x = pair index (0〜29)、y = 対差 (variant − baseline、M tps) で、30 対の差を open marker、
対差の算術平均を実線、登録済み区間 (平均 ± h、`h = k·s/√n`、`k = 2.8315526875186725`、df 29) を帯、0 を細い実線、登録済み床 ±B (B = baseline arm 平均の 3 %) を破線で描く。
y は workload ごとの尺度で、panel 間で高さを比べない。

fig9 との違いは次の 2 点だけである。

- **各 panel 題の 2・3 行目に `variance_plan_breach` を描く。** write-heavy と read-heavy は `variance_plan_breach=true`、balanced は `false`。3 行目は
  30 対の差の標本標準偏差 (sd) と事前登録の計画 sigma を 2 つの量として併記する (write-heavy sd 80,148.44 / planned sigma 66,403.45 tps、balanced 49,427.36 /
  56,697.44、read-heavy 80,752.99 / 74,668.49。稿 §2.1 の表と同じ値)。**比は作らない。**
- **図の上端に 1 行** `sized run attempt-0002; attempt-0001 is neither pooled nor compared with this attempt` を描く。attempt-0001 の値は図にも caption にも無い。

**この lane は `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` である。**
登録済み解析の分類は 3 workload とも `resolved-above-floor` (対差平均の符号は write-heavy 正 / balanced 正 / read-heavy 負) だが、これは事前登録した分類規則の
descriptive な出力であって、仮説検定でも性能認証でもない。write-heavy / read-heavy では標本 sd が計画 sigma を超えたので `h` が計画時の想定より広いが、
`abs(mean) − h > B` が成り立つので分類は変わらない。**`variance_plan_breach` の原因 (node・時間帯・bench 順・baseline arm の変動) は帰属しない** (稿 §3 L-A1S2-8)。
図と caption が言うのは「この attempt でこの値だった」までで、**headline 値・workload 横断の結論・C1 の再現判定にせず、単一 attempt を反復間の安定性へ一般化しない。
attempt-0001 とプールせず、2 attempt の差・比・区間の重なり・再現判定を描かない・書かない** (D1993 項 6、D2194 項 6、稿 §0.3 / §2.7 / L-A1S2-3)。
**A-1 の充足・formal 化・L-A1S-4 の解除・3 本目の attempt の認可は判定しない** (D2172 項 2、D2194 項 6)。図を variant 採用の根拠にしない (絶対規律 2)。

## 既存図との関係

- **fig9 (attempt-0001) の兄弟であって後継ではない。** fig9 は凍結のまま有効で、png / pdf / provenance の bytes は変えていない。生成器
  `tools/plotting/plot_a1_sized_paired.py` を attempt ごとの exact pin 表で拡張したが、attempt-0001 の出力 (`load_leaf` の返り値・caption・描画・既定 CLI) は不変で、
  fig9 の着地 test (`test_landed_fig9_repo_closure_and_caption_when_present`) が現行生成器で作り直した値と着地 provenance の一致を今も検査する。
- **2 attempt を並べた図は作らない** (D2194 項 6 (2)、2026-09-21 のユーザー再裁定)。本図は同項の「必要になれば単独図 (fig9 と同形、`caption_source` = 本稿) を先に作る」にあたる。
  fig9 と本図を並べて読むときも、2 つの観測を横に置くだけで、差・比・合成区間・再現判定を作らない。
- 稿 `results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` §2.6 と L-A1S2-11 の「図は無い」は起草時点 (2026-09-20) の事実で、本図はその後に作られた。
  **稿の bytes は変えない** (凍結物。provenance が現 SHA-256 で束縛する)。
- pilot の観測値は入っていない。A-2 / A-6 / [T-1998] の図とプールしない (D1993 項 6)。**2 本目の論文 (`docs/paper-story-backoff/`) と共用しない** (D1637)。

## 入力

- 権威 bytes (repo 内、tracked): `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` の `result.json` (SHA-256 `b7e0518e197500f2daf875e841acabf63f5eddb82bc14e072dd28e3431fe5f74`)、
  `receipt.json` (`98c35cca4fe0e9f12559b8f9dc3acb4c6c5c4c597e5f5cc01a6449533918ecbf`)、`.complete.json` (`7ad34232eaf920babd783140c47018b5c9d2f7665635872d4c2ee3be6f464fb3`) と、
  attempt-0001 と共通の policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` (`a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`)。値は稿 §5.1 の表と同じで、
  `orchestrator/tests/test_plot_a1_sized_paired.py` が両者の一致を検査する。生成器は attempt 表 (`ATTEMPTS`、`attempt-0001` / `attempt-0002` の 2 entry だけ) から leaf・pin・caption_source を引く。
  **pin は CLI から渡せない** (D1752)。CLI が選べるのは `--attempt` の 2 値だけで、未知の値は拒否し既定へ落とさない。
- 統計 (mean / variance / sd / h / baseline mean / B / 区間) は `statistics.pairs` の 30 対から再計算し、`statistics` の記録値と fail-closed で照合する。分類は記録値をコピーし、
  述語との一致だけを検査する。`variance_plan_breach` は述語 (`sd > planned sigma`) との一致を検査して記録値を写す。**attempt-0001 では従来どおり breach true を拒否する** (fig9 の scope)。
- 拒否条件: fig9 と同じ (SHA-256 不一致、lane の 3 値、`valid` / `errors`、n、対の差、`pairs` と `raw_tps`、genome、統計、分類の述語、breach の述語、`correctness_evidence`、
  policy SHA-256、caption_source の不在) に加え、未知の attempt と pin の key 集合の不一致。いずれでも成果物を出さない。
- **caption_source:** provenance の `tracked_inputs` に `kind: "caption_source"` として稿 `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` の path と
  SHA-256 を記録する (`authority_scope` = 限定と条件の言い方の出所であって、数値・分類の出所ではない)。稿は provenance の SHA-256 を持たない (稿と provenance が互いの hash を持つ循環を避けるため)。

## 再現

```bash
python3 tools/plotting/plot_a1_sized_paired.py --attempt attempt-0002 \
  docs/paper-story/figures/fig14_a1_balanced5_sized_attempt2
```

`--attempt` を省くと attempt-0001 (fig9 の再現コマンド) になる。`--repo-root` は省略時に生成器の位置から repo root を決める。図番号は出力 prefix の `fig<N>_` から導き、
`fig<N>_` の形でない prefix は出力前に拒否する。生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font 解決に依存する。着地したバイト列の同一性は provenance JSON が記録した
`outputs[].sha256` と `test_landed_fig14_repo_closure_and_caption_when_present` が守る。生成器の `generator.sha256` は生成時点の記録であり、現行 source を縛る pin ではない (規律 7)。

## 作図規約への適合

- §1: 数値は `result.json` の `pairs` からその場で再計算し、記録値とは fail-closed で照合する。
- §2: 30 対の生値と登録済み区間 (平均 ± h) を描く。区間は事前登録が固定した k による幅で、95% CI とは書かない。
- §3: 床 ±B と 0 を水平の破線・実線で描き、差の帯と目で比べられる。
- §5: 図中ラベルは fig9 と同じ短い語に、`variance_plan_breach=true|false` と sd / planned sigma の値、上端の 1 行だけを足した。
- §6: provenance に入力 4 file + caption_source の path と SHA-256、study / source commit / pin、測定条件、3 workload の cells、`artist_series`
  (実際に描いた y 値と題の表示文字列)、`limitations`、caption、展開済み再現 argv、`attempt` を記録する。
- §9: 保存前に renderer-backed layout check を走らせ、text の重なり・逸脱があれば 3 成果物を 1 つも出さない。breach と上端の 1 行は画像に描かれる実 artist で、
  test は `fig.findobj(Text)` の可視 text を検査する (F872)。
- §10: 単体テストの fixture は実寸 (3 workload × 30 対 × 2 arm、write-heavy / read-heavy は breach true) で、本物の matplotlib Figure を layout check へ通す。実データで実走して 3 成果物を確かめた。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、`orchestrator/tests/test_plot_a1_sized_paired.py` が本 README への収録と生成器の決定的な組み立てとの一致を検査する。
英文で書く。値 (mean / h / B / baseline mean / job / host / 分類 / 符号 / breach / sd / planned sigma) は生成器が `result.json` / `receipt.json` から書式化する。

> Figure 14. A-1 balanced five-rep paired comparison, sized run attempt-0002 (study paper-story-a1-20260901-balanced5-sized-v1; formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only). Columns: write-heavy (rr5, fixed10 minus no-backoff), balanced (rr50, fixed5 minus no-backoff), read-heavy (rr95, fixed2 minus no-backoff), each an independent campaign in its own job (job IDs, respectively: 13220.nqsv, 13221.nqsv, 13222.nqsv; hosts bnode035, bnode039, bnode040). What is drawn: 30 paired differences (variant minus baseline, one per pair index under the balanced five-rep schedule, ten-pair groups in the order A^5 B^5 B^5 A^5 or B^5 A^5 A^5 B^5) as open markers; the arithmetic mean as a solid line with the registered interval mean ± h, h = k·s/√n, k = 2.8315526875186725 (t quantile at 1 − (1/120)/2 with df 29), s the sample standard deviation of the 30 differences; the zero line; and the registered floor boundary ±B, B = 3 % of the baseline-arm mean, as dashed lines. M tps means million transactions per second. Values: write-heavy mean +1.538 M tps (h 0.041 M, B 0.073 M, baseline mean 2.432 M); balanced mean +0.548 M tps (h 0.026 M, B 0.111 M, baseline mean 3.694 M); read-heavy mean -0.561 M tps (h 0.042 M, B 0.305 M, baseline mean 10.169 M). The registered classification is resolved-above-floor in all three workloads (sign positive, positive and negative, respectively). The interval and the classification are the descriptive outputs of the preregistered rule; they are not a hypothesis test and are not a performance certification. This figure reports a single attempt of a non-certified lane: it is not a headline value, no cross-workload conclusion is drawn (preregistration section 7.2), it is not a reproduction of C1, and one attempt does not speak to stability across repeated attempts. Attempt-0001 is neither pooled nor compared with this attempt; no between-attempt difference, ratio, or reproducibility judgment is made. write-heavy: variance_plan_breach=true, sample sd=80,148.44 tps, planned sigma=66,403.45 tps; balanced: variance_plan_breach=false, sample sd=49,427.36 tps, planned sigma=56,697.44 tps; read-heavy: variance_plan_breach=true, sample sd=80,752.99 tps, planned sigma=74,668.49 tps. No cause is attributed to variance_plan_breach. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s per repetition, 30 pairs per workload, silo, CCBench pin 511c953, measurement source commit fec4a8187, no perf, trace-disabled performance. Correctness comes from separate trace-enabled verify runs under the recorded legacy check configuration, not the performance configuration: all 6 arms are recorded as certified (result.json correctness_evidence, verify_done frames bound by SHA-256); certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification. Panel y scales are workload-local and must not be compared across panels. Pilot observations did not enter the estimate; the estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state effect.

## proof chain

- 図に描いた 30 点・平均・帯・±B・0・題の breach / sd / planned sigma → provenance JSON の `artist_series` と `workloads[]` (cells)
- cells の統計 → `result.json` の `workloads[].statistics` (生成器は `pairs` から再計算して照合。分類と breach は述語一致を検査した記録値)
- 標本の由来 → `result.json` の `statistics.pairs` と `arms.<name>.raw_tps` (対応を検査)、その先は campaign WAL (稿 §5.2)
- 入力の束縛 → `.complete.json` の `files` map、生成器の attempt 表の pin、稿 §5.1 の表
- 正しさの記録 → `result.json` の `arms.<name>.correctness_evidence` (6 arm とも `certified: [true]`、`legacy`。性能の認証ではない。稿 §2.4)
- 限定と条件の言い方 → 稿 (provenance の `caption_source`、SHA-256 束縛)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_a1_sized_paired.py` (`test_landed_fig14_repo_closure_and_caption_when_present`: 着地 bytes の SHA-256、caption の逐語収録、
  現行 leaf から作り直した cells / artist / caption との一致。`test_attempt2_pinned_input_hashes_match_results_document` / `test_attempt2_real_leaf_loads_and_matches_results_document`: 稿 §5.1 / §2.1 との一致)
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`
- 事前登録 → `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` (§3 推定対象、§5.1 区間、§5.2 分類、§7.2 できないこと)
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256

次の 3 行が着地 bytes の正本である。`orchestrator/tests/test_plot_a1_sized_paired.py` の着地 test が、この 3 行の値と
着地 file の現物 SHA-256 の一致を検査する (行の形は `- \`<basename>\` SHA-256: \`<64 hex>\`` で固定)。

- `fig14_a1_balanced5_sized_attempt2.png` SHA-256: `1b44427aec1dbcb49659c9b53cca3c31ae4f17de5d1cc058f035f67e5966d017`
- `fig14_a1_balanced5_sized_attempt2.pdf` SHA-256: `626fa1b71d192ecfac5a880cb2a592acec1f4237e991a9f82109a9165b59efa8`
- `fig14_a1_balanced5_sized_attempt2.provenance.json` SHA-256: `b128c6e8f9e15541882d4ddfa8d37c0a0c283440df177a2df75859f14cdddbd7`

provenance が `caption_source` として束縛する稿の SHA-256 は `52b66f268823837914475261feafa77377a7fe947c879c59143da17af717e4b1`
(稿は凍結物で、着地後に変わらない)。

---

# `fig15_mocc_witlight_four_arm` — stock mocc の軽量 witness 4 arm × 60 走 (本走 4 block W1〜W4) の G2 signal 検出率・Clopper–Pearson 区間と曝露量 (非 certifying の観測の記述図)

## 何を示す図か

1 wave (`dev-wave-mocc-witlight-arm-run`) の本走 4 block (W1〜W4、bnode122 / bnode119 / bnode121 / bnode109、2026-09-19 22:35〜23:02 JST) × 15 round × 4 arm = 240 走 (arm ごと 60 走) について、
単独稿 `results/2026-09-20-mocc-witlight-four-arm.md` §2.2 / §2.3 / §2.6 と同じ値を描いた**記述図**である。4 arm は軽量 witness の on / off × `BACK_OFF` 0 / 1 で、
同じ合成 source (pin `e9e477ca` + X/P patch + witlight patch) を arm ごとに build し、on / off は実行時の環境変数だけが違う (稿 §1.5)。

- 1 axes の forest。縦に 4 arm (上から `on / BACK_OFF=0`、`off / BACK_OFF=0`、`on / BACK_OFF=1`、`off / BACK_OFF=1`)、横軸は G2 signal 検出率 (%)。点 = k/m、横線 = Clopper–Pearson 両側 95% 区間。
- 右側の数値列は稿 §2.2 の逐語 (`k/m`、率、CP 区間、走あたり commit 数の平均) と、稿 §2.6 の on/off 曝露比 (`BACK_OFF=0` 0.8636、`BACK_OFF=1` 0.8450)。
- 図の下の注記 (画像に描く): 非 certifying・TRACE=1 build、commit 数は曝露量であって性能ではない、片側 Fisher (on が低い方向、未調整) p = 0.500 (`BACK_OFF=0` / `1`)、
  有意でないことは同等性ではなく検出力 0.105 は設計仮定下の計算値、G2 signal は verifier の検出で根因を同定しない。

値は on の 2 arm が 0/60 (CP [0%, 5.963%])、off の 2 arm が 1/60 (1.667%、CP [0.042%, 8.940%])。G2 signal 2 走はどちらも witness off で、W1 の `e9-witlight-nowit` (round 5) と
W3 の `e9-witlight-nowit-bo1` (round 2) にある (block 内の分母は 15)。

**言えるのは稿 §2.8 の「識別できた」列まで**である。BACK_OFF=0 でも BACK_OFF=1 でも on/off の率差は検出しなかった (片側 Fisher p = 0.500)。
**非有意は同等性の証明ではなく、0 件は不在の証明ではない** — on の 0/60 は「率 0.017〜0.042 の事象を 60 走で引けなかった」とも両立し、設計仮定下の検出力 0.105 は
認可枠 60/arm の上限として明記する計算値であって実測ではない (稿 §1.3、§3 限定 1・2)。**「軽量 witness が観測者効果を消した」「witness on では G2 が出ない」とは描かない・書かない。**
**commit 数は TRACE=1 build の曝露量であって性能値ではない** (絶対規律 1、稿 §2.6・§3 限定 7)。on/off 比は曝露量の記録で、性能の比ではない。
**G2 signal は verifier の検出であって根因の同定ではない** — off の 2 件は witness が無いので payload lineage による実 anomaly / torn read の識別ができず、discriminator は 0 件発火で
問い (ii) は未到達である (稿 §2.4・§2.5・§3 限定 6)。**非 certifying の観測**で、個別 verifier の `certified=true` (238 走) と arm 属性 `observational_only=false` は本 wave・MOCC・
軽量 witness の認証を意味しない。certified 昇格・pin 前進・変異探索の解禁は認可されていない (稿 §1.1・§3 限定 3)。図を variant 採用や pin 前進の根拠にしない (絶対規律 2)。

## 既存図との関係

- 既存図 (fig1〜fig14) のいずれの後継でもない独立した新図。results 系列に mocc の図はこれまで無かった。
- **[T-1892] 5/42、[T-1943] `no-g2`、[T-2774] Q1 / Q2、[T-2779] 5/120・0/120・2/120 の値と合算・比較しない** (規律 7、稿 §3 限定 4・5)。4 arm に旧 heavyweight on arm を含まないので、
  軽量化の改善量は推定しない。off を 2 arm 合算した 2/120 も描かない (稿は arm 別に 1/60 ずつ書く)。
- **smoke (request `10799.nqsv`、4 走) は第 5 block として数えない** (稿 §0.1・§2.7)。生成器は smoke の file を入力にせず、`summary.json` の `inputs` が W1〜W4 の 4 件と exact に一致することを要求する。
- 稿の bytes は変えない (凍結物。provenance が現 SHA-256 で束縛する)。2 本目の論文と共用しない (D1637)。

## 入力

- 権威入力 (repo 外、稿 §5.1 の表): root `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W` の `summary.json` (SHA-256 `b1be3ebde10c20ea26de3956495f927d2baa8c06ecc1b7e2d7222f2795310698`)、
  `W1/result.json` (`ca8ab3ff579e3fb55b97447ebb7b647d34806a6fd452ad410051aca9e5bd4b50`)、`W2/result.json` (`473063aa741cc4c349931d987c902facbc5dcf6499b3692ea2cad3a27ac1e584`)、
  `W3/result.json` (`f68876600f1cd5b7300b030fb3cfa75509cc7a687858d6f12985051ce46e3642`)、`W4/result.json` (`197a2798de5ef53a7f6a32460f7ecfa5adbba8e853778b315d3b6e1839c36a6c`) の 5 file だけ。
  生成器は 5 件の SHA-256 を定数 (`EXTERNAL_SHA256`) で持ち、**CLI から渡せない**。`--evidence-root` は読み出し場所で、既定は上の root。`smoke/`・`parent-accounting.json`・走ごとの dir は開かない。
- 再計算と照合: 240 走が benchmark `rc = 0` かつ verifier (rc, status) が (0, `no-g2`) か (1, `g2`) であることを要求し (failure・indeterminate は拒否)、arm 別の N / m / k / decisive_m、
  位置の配分 (各 arm 各位置 15)、Clopper–Pearson 両側 95%、片側 Fisher (on が低い方向)、走あたり commit 数の平均と on/off 比を `runs[]` から計算する。`summary.json` が持つ量 (N / m / k / failure /
  indeterminate / decisive_m / k_over_m / cp95 / discriminator_counts / identification) とは fail-closed で照合する。**Fisher p と commit 数平均は `summary.json` に無い**ので照合先は稿 §2.3 / §2.6 だけで、
  `orchestrator/tests/test_plot_mocc_witlight_four_arm.py` が稿の表セルとの逐語一致を検査する。検出力 0.105 は稿 §1.3 の計算値を caption と注記の固定文に置いたもので、生成器は計算しない。
- block の検査: block ID W1〜W4、`status=completed`、rounds 15、planned 60、`not_started` 0、runs 60、round ごとの 4 arm と回転、run と `bindings` の arm / witness / `BACK_OFF`、4 block で同じ `workload_argv`。
- 拒否条件: 5 file の SHA-256 不一致、`summary.json.inputs` の余剰・重複・欠落・順序・path・digest の不一致、block・run・回転・bindings の不一致、failure / indeterminate / 未知 status、集計の不一致、
  caption_source (稿) の不在。いずれでも成果物を出さない。
- **caption_source:** provenance の `tracked_inputs` に `kind: "caption_source"` として稿 `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md` の path と SHA-256 を記録する (稿は provenance の SHA-256 を持たない。稿と provenance が互いの hash を持つ循環を避けるため)。
  repo 外の 5 file は `external_inputs` (root 相対 path・kind・SHA-256) と `source_inputs` (`summary.json` が記録する原保存先の絶対 path) に分けて記録する。

## 再現

```bash
python3 tools/plotting/plot_mocc_witlight_four_arm.py \
  --evidence-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W \
  docs/paper-story/figures/fig15_mocc_witlight_four_arm
```

図番号は出力 prefix の `fig<N>_` から導く。`fig<N>_` の形でない prefix は出力前に拒否する。生成は login node で行う (計測機の外、FIGURE_CONVENTIONS §7)。

### 再現できるのは「値」であって「バイト列」ではない

provenance JSON は生成時刻を持ち、PDF は matplotlib が生成日時を埋め、PNG は matplotlib の版と font 解決に依存する。着地したバイト列の同一性は provenance JSON が記録した
`outputs[].sha256` と `test_landed_fig15_repo_closure_and_caption_when_present` が守る。**検査は 2 層で、射程が違う。** `validate_repo_closure` は repo 外を読まず、稿の現 SHA-256・出力の SHA-256・
provenance に記録した arm 統計から作り直した caption / artist との一致を見る (provenance の自己整合であって、外部原本との一致の証明ではない)。外部原本との一致は `validate_external_sources`
(5 file の SHA-256 と、原本から再導出した統計・書式・条件が provenance と一致すること) が見て、`test_landed_fig15_external_closure_when_root_present` は root が無い環境でだけ skip する。
repo 内の逐語写し (`output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/` の W1〜W4 `result.json` と `summary.json`) は原本と SHA-256 が一致するが、生成器はそれを入力にしない。
生成器の `generator.sha256` は生成時点の記録であり、現行 source を縛る pin ではない (規律 7)。

## 作図規約への適合

- §1: 数値は W1〜W4 の `runs[]` からその場で計算し、`summary.json` の集計とは fail-closed で照合する。表示は稿 §2 と同じ書式の文字列 (稿との逐語一致は test)。
- §2: 検出率の不確かさは Clopper–Pearson 両側 95% 区間で描く (独立・同率 Bernoulli の参考値で、node 内相関・回転順・時間変動はモデル化しない。caption に明記)。
  **走あたり commit 数の平均は、稿 §2.2 / §2.6 の記録値を数値の列として示すだけで、区間を付けず推論に使わない** (曝露量の記述であって性能の推定ではない。本図での局所の適用判断で、段 3 相談の所見による)。
- §3: on と off を同じ軸の隣り合う行に置き、区間の重なりから判定しない。
- §5: 図中ラベルは `on / off`・`BACK_OFF`・数値列の見出しだけ。arm ID (`e9-witlight-wit` 等) との対応は caption で 1 回展開する。
- §6: provenance に入力 (repo 外 5 file の path と SHA-256、原保存先、caption_source)・測定条件 (48 threads、10,000 records、Zipf 0.9、read ratio 50、rmw 0、max operations 10、3 s、TRACE=1、
  pin `e9e477ca` + patches、Pegasus 計算ノード、4 block × 15 round)・arm 統計・block 別 k/m と host・Fisher・曝露比・caption・再現 argv を記録する。条件は caption の `Conditions:` 文にも出す。
- §7: login で生成。§8: matplotlib + numpy + 標準 library (CP・Fisher は標準 library で計算し scipy に依存しない)。
- §9: 保存前の renderer-backed layout check (axes ちょうど 1、text の重なり・逸脱で 3 成果物を 1 つも出さない)。注記は実 artist として描き、test は `fig.findobj(Text)` の可視 text を検査する (F872)。
  caption と可視 text の両方を肯定形の禁止句 (同等性・効果なし・性能・根因の同定・認証など) で走査する。
- §10: fixture は実寸 (4 block × 60 走 = 15 round × 4 arm、回転、G2 signal 2 走、commit 数は非一様) で本物の Figure を検査へ通す。実データで実走して 3 成果物を確かめた。

## キャプション正文

キャプション正文は provenance JSON の `caption` と同一文字列であり、`orchestrator/tests/test_plot_mocc_witlight_four_arm.py` が本 README への収録と生成器の決定的な組み立てとの一致を検査する。
英文で書く。値 (k/m・率・CP・commit 数平均・Fisher p・曝露比・G2 signal の所在・条件) は生成器が 5 file から書式化し、限定の固定文 (非有意 ≠ 同等性、検出力 0.105 は計算値、TRACE=1 の commit 数は
曝露量、G2 signal ≠ 根因、非 certifying、smoke を分母に入れない、CP / Fisher の独立性仮定) を逐語で含む。

> Figure 15. Stock MOCC lightweight witness observations: G2 signal detection rates with two-sided 95% Clopper–Pearson (CP) intervals and descriptive mean commits per run. e9-witlight-wit (on / BACK_OFF=0): 0/60, 0%, CP [0%, 5.963%], mean commits per run 613,741.5. e9-witlight-nowit (off / BACK_OFF=0): 1/60, 1.667%, CP [0.042%, 8.940%], mean commits per run 710,659.4. e9-witlight-wit-bo1 (on / BACK_OFF=1): 0/60, 0%, CP [0%, 5.963%], mean commits per run 788,885.6. e9-witlight-nowit-bo1 (off / BACK_OFF=1): 1/60, 1.667%, CP [0.042%, 8.940%], mean commits per run 933,621.8. Primary comparison BACK_OFF=0: one-sided Fisher (on lower), unadjusted p = 0.500; on/off exposure ratio 0.8636. Secondary comparison BACK_OFF=1: one-sided Fisher (on lower), unadjusted p = 0.500; on/off exposure ratio 0.8450. G2 signal locations: W1 e9-witlight-nowit (1/15); W3 e9-witlight-nowit-bo1 (1/15). Non-significance does not establish equivalence, and zero detections do not establish absence. Power 0.105 is a calculation under the design assumptions, not a measured quantity: independent Bernoulli trials, 60 runs per arm, off probability 0.0417, on probability 0, and a one-sided Fisher test at alpha 0.05. TRACE=1 commit counts are exposure, not performance. G2 signals do not identify a root cause or distinguish a real anomaly from a torn read. This is a non-certifying observation; individual verifier certified flags and observational_only=false do not certify this wave, MOCC, or the witness. The denominator includes only 4 blocks x 15 rounds x 4 arms; smoke runs are excluded. CP intervals and Fisher p values assume independent Bernoulli trials and do not model within-node dependence, rotation order, or temporal variation. The discriminator was not reached: no on-arm G2 signals occurred, so it fired zero times and made zero comparisons. Detection rates are per fixed-time 3 s run, not a comparison at equal commit exposure. Values from earlier waves [T-1892], [T-2774], and [T-2779] are neither pooled nor compared here. Conditions: 48 threads, 10,000 records, Zipf 0.9, read ratio 50, rmw 0, max operations 10, 3 s, TRACE=1 build, pin e9e477ca + X/P + witlight patches, Pegasus compute nodes, 4 blocks W1–W4 x 15 rounds x 4 arms, smoke excluded.

## proof chain

- 図に描いた 4 点・4 区間・数値列・曝露比・注記 → provenance JSON の `artist_series` (描画へ渡した値と文字列) と `arms` / `comparisons` / `exposure_ratios`
- arm 別の k / m / CP → W1〜W4 `result.json` の `runs[].verifier.status` から再計算し、`summary.json` の `arms.<arm>` と照合 (稿 §2.2、§5.4)
- block 別の k/m と host → provenance の `blocks` (W1〜W4 `result.json`、稿 §2.1)
- Fisher p と commit 数平均・曝露比 → `runs[]` からの計算 (稿 §2.3 / §2.6 と test が逐語照合)
- 入力の束縛 → 生成器の `EXTERNAL_SHA256`、`summary.json.inputs` の exact 照合、稿 §5.1 の表
- 条件・束縛 (pin、patch、runner、toolchain、configure) → 各 block の `bindings` (稿 §1.5)
- 限定と条件の言い方 → 稿 (provenance の `caption_source`、SHA-256 束縛)
- それらが着地後もずれないこと → `orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (`test_landed_fig15_repo_closure_and_caption_when_present`: 着地 bytes の SHA-256・caption の逐語収録・repo 側閉包、
  `test_landed_fig15_external_closure_when_root_present`: 外部原本からの再導出、`test_production_pins_match_results_document`: 5 pin と稿 §5.1、
  `test_real_evidence_matches_results_document_when_root_present`: 稿 §2.2 / §2.3 / §2.6 の表セル)
- 結果節・表・限定の材料 → `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md`、記録 insight `output/insights/2026-09-19/mocc-witlight-arm-run/README.md`
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`

## 着地 bytes の SHA-256

次の 3 行が着地 bytes の正本である。`orchestrator/tests/test_plot_mocc_witlight_four_arm.py` の着地 test が、この 3 行の値と
着地 file の現物 SHA-256 の一致を検査する (行の形は `- \`<basename>\` SHA-256: \`<64 hex>\`` で固定)。

- `fig15_mocc_witlight_four_arm.png` SHA-256: `11f28201017df6fbefc2422a51d72bbd751560b97a427cdd8fde29004894e966`
- `fig15_mocc_witlight_four_arm.pdf` SHA-256: `4af678483c544ecbbee63e12d1df32d3980f78a476672ea7d570d0377101d018`
- `fig15_mocc_witlight_four_arm.provenance.json` SHA-256: `fb1c04606aa6dc84c74b3ca82754e54a8896c44634f4cbf5c26b0373f35f996a`

provenance が `caption_source` として束縛する稿の SHA-256 は `77662b55f2b1f113626293ee530d5e0466249192ba2f6babefe4db4e74241d96`
(稿は凍結物で、着地後に変わらない)。
