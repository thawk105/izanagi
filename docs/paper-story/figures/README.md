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
