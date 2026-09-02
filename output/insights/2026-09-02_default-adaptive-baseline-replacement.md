# 既定 adaptive を単独基準線に使っている箇所の洗い出しと差し替え (D1506)

**種別:** 台帳の是正記録。**新規計測なし・新規図なし。** 本文書は測定原典ではなく、
既存の裁定 (D1505 / D1506) を生きた成果物へ行き渡らせた作業の記録である。
数値の出所はすべて `output/insights/2026-09-02_cicada-adaptive-three-constants.md` と
`docs/decisions.md` の D1505 / D1506 で、本文書は数値を新しく作らない。

## なぜやったか

D1506 は「backoff 機構の性能比較では無 backoff と調整済み adaptive
(刻み 1 µs / 更新間隔 2560 µs / 上限 1000 µs) の 2 本を基準線に置く。**既定 adaptive を単独の
基準線に使った比較は、機構の優劣を何も言っていないものとして扱う**」と定めた。
裁定は台帳に着地したが、**既定 adaptive を「適応側」の代表として扱っている記述と既定値は
repo のあちこちに残っていた。** それを洗い出して差し替えたのが本作業である。

**D1506 は既定 adaptive を測ること自体を禁じていない。** 上流を素のまま使うとどうなるかは
還元判断に要る事実であり、禁じているのは「既定 adaptive に対する優位だけを機構の優位として
報告すること」である。したがって差し替えの方向は「既定 adaptive を消す」ではなく
**「既定にしない・何の定数の話かを名乗る・機構の優劣を言わない」**である。

## 該当箇所と、旧基準線で書いた結論が変わるか

**差し替えた 10 単位。** 「結論」欄は、その箇所が旧基準線を前提に述べていた結論が
変わるか変わらないかである。

| # | 箇所 | 何が既定 adaptive を単独基準線にしていたか | 結論 |
|---|---|---|---|
| 1 | `tools/plotting/plot_backoff.py` | `--baselines` の既定が `no-backoff,stock-adaptive` で、省略起動が既定 adaptive を唯一の適応基準線として描いていた | **変わる** — 既定で描く線が 1 本減る。既に描かれた図 (fig2b) は `--baselines no-backoff` を明示していたので、その bytes・数値・結論は 1 つも変わらない |
| 2 | `orchestrator/tests/test_plot_backoff_ci.py` | 上の既定を固定していた | **変わらない** — 期待値を新しい既定へ更新しただけで、判定の意味は変わらない。明示 opt-in が今も描けることを固定する正例を足した |
| 3 | `orchestrator/campaign/backoff_sweep_report.py` | 「stock 適応 backoff」を唯一の適応参照線にし、「適応が逃した sweet spot」を verdict として出していた | **変わる** — 「既定 adaptive が sweet spot を逃したことが機構の直接証拠」という結論を撤回する。静的最良 対 無 backoff の数式・閾値・数値表は不変 |
| 4 | `orchestrator/tests/test_backoff_consumers.py` | 上の正文を固定していた | **変わらない** — 期待値を新しい正文へ更新しただけ。既存の abort/IPC 期待値は緩めていない |
| 5 | `orchestrator/campaign/backoff_sweep.py` | driver の説明が、測定集合に既定 adaptive しか無いことを機構の文脈として書いていた | **変わらない** — 測定集合も genome も変えていない。説明を「既定 3 定数の文脈点。機構 verdict に使わない」へ限定しただけ |
| 6 | `tools/plotting/README.md` | CLI 既定の記述、および「fig2b が pin するので `plot_backoff.py` は変更しない」という誤った前提 | **変わらない (数値)。変わる (可否の判断)** — pin は生成時 bytes の記録であって現行 bytes を縛らない。現行 hash は記録値と既にずれ、それでもテストは緑である (実測) |
| 7 | `tools/plotting/FIGURE_CONVENTIONS.md` §5 | 短い label `stock adaptive` の展開を「Cicada 標準の適応 backoff」と定めていた | **変わる** — 展開が「機構そのもの」を指していた。「CCBench 既定 3 定数の適応 backoff」へ改める。label 自体は変えない |
| 8 | `patches/README.md` | 「Cicada 由来の適応 backoff が 48 スレッド高競合で throughput を殺す値に収束している」と、機構の性質として読める書き方 | **変わる** — 収束は既定 3 定数の下での観測であって機構一般の劣位ではない。`BACKOFF_FIXED` 導入の動機そのものは変わらない |
| 9 | `docs/paper-story/figures/README.md` | fig2b 再現節の「生成器の既定 (無 backoff と適応 backoff の 2 本)」、fig2c 冒頭の「適応 backoff の帯域を静的点で覆う」 | **変わらない (測定値)。変わる (目標の名乗り)** — fig2c の 28 点、F718 の 1000 µs 除外、性能地形の解釈は不変。11 状態が既定定数から導いた格子であることを明記する |
| 10 | `docs/paper-story/README.md` の stale 注記 | 凍結スナップショット `2026-09-02.md` が既定 adaptive の診断を機構一般の性質として書いている 2 箇所を、腐らない入口が指していなかった | **変わらない (P2-4 論文値)。変わる (機構主張)** — 下の「非対称」を参照 |

### 非対称 — 何が変わらず、何が変わるか

**変わらないもの。**

- **P2-4 の論文値 +38.3% / +11.3% / −6.6% は変わらない。** 分母は同一 sweep 内の
  無 backoff 対照 (`BACK_OFF=0`) であって既定 adaptive ではない。D1506 はこの分母を動かさない。
- **fig2b / fig2c が描いた点、95% 信頼区間、F718 による 1000 µs の除外、
  性能地形の解釈は変わらない。**
- **格子 `{0, 100, …, 1000}` µs に sweet spot 5〜10 µs が含まれないという到達不能性の
  構造論証も、既定定数についての事実としてはそのまま成り立つ。**
- 「適応を分母に取れば write-heavy の利得は +147.4%」という診断値の位置づけも変わらない
  (以前から論文の headline 利得ではないと明記されていた)。

**変わるもの。**

- **これらを adaptive backoff という機構一般の性質として読むことができなくなった。**
  同じ機構でも定数を変えれば最適帯へ寄る。48 スレッドで刻みを 0.1〜5 µs に振ったときの
  throughput の最大/最小比は、更新間隔が既定の 10 µs では 2.55x (write) / 3.28x (balanced) /
  3.66x (read) だが、間隔を 40 µs へ 1 段広げるだけで 1.37x / 1.05x / 1.06x へ潰れる。
  **律速は刻みではなく更新間隔であり、刻みはその症状である** (D1505)。
- **既定 adaptive と調整済み adaptive の差 — 48 スレッドで +186.6% / +244.4% / +335.2% —
  は定数の選択だけで出る** (D1506)。この差を機構の優劣として報告してはならない。
- したがって `fig2c` を「適応機構が取りうる状態を静的点で覆った図」と引用してはならない。
  正しくは「**既定定数の** adaptive が取りうる状態を覆うことを目標にした図」である。

## 差し替えられなかったこと (正直な限界)

- **旧 `linux-baremetal` の図に調整済み adaptive の線を足すことはできない。**
  当時の campaign 3 件にそのセルが無いからである。足すには新規計測が要る。
- **調整済みの値は Pegasus `gen_S` で測ったものであり、旧環境の図へ混ぜてはならない。**
  違うのは環境だけではない。CCBench の版 (`6656e93` と `511c9538` +
  `patches/cicada-adaptive-params.patch`)、`max_ope` の記録の有無、thread 軸、
  反復設計 (campaign 内 5 反復と 7 ノード × 1 rep)、集約 (median 比と標本平均)、
  `clocks_per_us` (1800 と 2100)、`numactl` と `perf stat` の有無が違う。
- **調整済みの値は trace-disabled の性能測定のみで、直列性の検査を通していない。**
  variant 採用の根拠には使えない (絶対規律 2)。正しさの検査は [T-2189] の担当である。
- したがって本 wave が達成したのは「**既定 adaptive を単独の適応基準線として使わせない**」
  ところまでで、「**調整済み adaptive を実際の対照として同じ図に並べる**」ところまでではない。
  後者は新規計測を伴う別の作業である。

## 該当しないと判断したもの

**凍結物・過去記録** — 規律 7 に従い、測定時点の事実として残す。訂正は腐らない入口が担う。

- `docs/paper-story/` の各版 (`2026-07-03` / `2026-07-10` / `2026-08-23` / `2026-08-26` /
  `2026-09-02`) と `claim-evidence/2026-08-26.md` — 同ディレクトリ README の運用ルールで
  上書き禁止。訂正は README の stale 注記が担う (上表 #10)。
- `docs/paper-story/figures/` の `.png` / `.pdf` / `.provenance.json` — 凍結物。
  誤 label を持つ `fig2_backoff_mechanism.png` の訂正も、既に figures README の erratum が担う。
- `docs/decisions.md` の D1106 (11 状態の定義)、worklog、archive、failures、
  既存 insight、生成済み campaign report — 当時の判断と実測の記録。

**bytes を pin されていて触れないもの**

- `docs/phase3-main-experiment.md` — 3 台帳が sha256 で pin する (下の閉包表)。
  同 25 行の「grid 定数を調整した適応 backoff とも未比較」は T-2187 で**部分的に**埋まったが、
  本文は触らない。埋まったことは本文書と worklog が記録する。
  なお「部分的に」というのは、T-2187 が同じ CC (silo) を別環境・別 CCBench 版で測ったものであり、
  主実験の headline 比較対象として登録された 4 対照の中で測り直したものではないからである。
- `docs/b10-backoff-shape-preregistration.md` — 事前登録。参照アーム `adaptive`
  (`BACK_OFF=1, BACKOFF_FIXED=-1`) は既定定数だが、改訂は登録ハッシュを動かす。

**既に正しいもの**

- `orchestrator/campaign/paper_story_a1_paired.py` — A-1 の contrast は **D1262 が既に**
  `static10 − adaptive` から `variant − baseline` (固定 backoff − 無 backoff) へ差し替え済み。
  残る `adaptive` 語は v2 legacy 経路と凍結 policy の exact 一致検査であり、触らない。
- `tools/plotting/plot_t2187_adaptive_consts.py` — 既定と調整済みを併記する生成器。
  既定 adaptive は陽性対照として置かれている。
- `orchestrator/campaign/backoff_extended_sweep.py`、`b10_backoff_shape_sweep.py`、
  `backoff_requested_us.py` — 既定 adaptive を参照点・診断として測るだけで、機構の優劣を判定しない。
- `orchestrator/campaign/s1_known_axes_freeze.py`、`condition_meaning_gate.py`、
  `docs/phase3.md` — `BACKOFF_FIXED=-1` の分岐意味と過去の reference point の記録。

**採用しなかった是正 (nit)**

DW-G05 の「放置したとき成果物の何がどう変わるか」を 1 行で書けないため、nit として記録に留めた。

- `orchestrator/tests/test_backoff_extended_sweep.py` の `all_adaptive_discrete_states` —
  `default_adaptive_discrete_states` が正確。
- `patches/silo-backoff-fixed.patch` の help 文字列 `-1=stock adaptive` —
  CCBench へ当たる bytes であり D16 / D18 / D20 の射程。

**採用しなかった gate 強化 (scope 外)**

`orchestrator/tests/test_backoff_figure_provenance.py` の genome→label 対応は
`("1","-1") → ("stock-adaptive","stock adaptive")` であり、3 定数を開く patch の下では
**既定 adaptive と調整済み adaptive を区別できない**。段 2 のプランはこれを 5 値同定へ広げる案を
出したが、段 4 で**不採用**とした。理由は 3 つある。

1. **その形の producer が実在しない。** 既存 3 campaign の WAL に `BACKOFF_INCR_MILLI` は
   **grep 実測 0 件**であり、現行 driver も 3 定数を genome に出さない。
2. **要求すると既定でない明示起動まで失敗する。** 既存 campaign を描けなくなるだけで、
   調整済みの対照は 1 本も増えない。
3. **ユーザーが「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示した。**

**この限界はここに記録して残す。** もし将来、調整済み adaptive の系列を
`plot_backoff.py` の入力へ流す producer を作るなら、**その系列を描く前に**この対応表を
拡張しなければならない。拡張前に描くと、調整済みの線に `stock adaptive` という label が付く —
`fig2_backoff_mechanism.png` で起きた誤 label 事故と同じ形になる。

## pin 閉包 (DW-O09、実測)

編集した各 path について、bytes・path・識別子を束縛する台帳・test・trust root を数え直した。

| 対象 | 束縛 | 本 wave の扱い |
|---|---|---|
| `docs/phase3-main-experiment.md` | `output/s1-freeze/known_axes_freeze.json`、`output/s1-freeze/measurement_freeze.json`、`output/s8b-freeze/holdout_freeze.json` が sha256 を記録。現行 bytes は記録値 `e544de19…` と一致 | **編集しない** |
| `tools/plotting/plot_backoff.py` | `fig2b_backoff_sweep_3workload.provenance.json` の `generator_source`、`fig2c_b10_extended_backoff.provenance.json` の `dependencies[0]` (role `admitted-wal-conditions-t95-ci-style`)。いずれも記録値 `bdb3c223…` | **編集した。** 両検査とも記録された生成時定数どうしを照合し live source を再 hash しない。現行 hash `f02f682d…` は編集前から記録値とずれており、それでも緑 (変更前 baseline 87 件緑を実測) |
| `orchestrator/campaign/backoff_sweep.py` | 上記 3 台帳の source record に出現 (grep 実測 3 / 3 / 5 行) | **編集した。** ただし記録 hash は**編集前から**現行 bytes とずれており、本 wave が新たに壊したものは無い |
| `backoff_sweep_report.py`、変更した test 2 file、`patches/README.md`、paper-story の 2 README、`tools/plotting/` の 2 docs | 固定 byte SHA は見つからなかった。明示的な `xdist_group` 名も無い | 編集した |

byte 以外の束縛は、公開識別子 `stock-adaptive`、`--baselines` の受理集合、
provenance schema `izanagi-backoff-figure-provenance/v2`、label↔genome 対応、
fig2c の dependency role、`FIGURE_CONVENTIONS.md` の label 規約である。
**このうち label↔genome 対応と v2 schema は本 wave で変えていない。**

## 探索の方法 (不在の根拠)

対象は `orchestrator/`、`tools/`、`patches/`、生きた `docs/`、および全 `*.provenance.json`。
検索語は `stock-adaptive`、`stock adaptive`、`stock 適応`、`既定 adaptive`、`適応 backoff`、
`BACKOFF_FIXED=-1`、`adaptive_tps`、`BACKOFF_INCR_MILLI`、`BACKOFF_MAX_US`、`BACKOFF_UPDATE_US`、
`kIncrBackoff`、`kMaxBackoff`。観点は 4 つ — (a) 既定定数の adaptive を適応側の代表として扱う記述、
(b) `BACK_OFF=1` かつ `BACKOFF_FIXED=-1` を無条件に `stock` / `適応` と名付ける対応、
(c) 既定 adaptive の到達可能集合を「適応機構の状態集合」として使う設計、
(d) 既定 adaptive に対する優位を機構の優位として述べる文。

`docs/archive/`、worklog、decisions の既存 D、handoff、日付付き paper-story、既存 insight、
生成済み campaign report は過去記録として別に確認し、生きた該当箇所には数えていない。

## 検証

- 変更前 baseline: 図 provenance 4 file = **87 passed** (`tools/run_tests.py` 経由)。
- 変更したテスト 2 file の単独走: `test_plot_backoff_ci.py` = **17 passed**、
  `test_backoff_consumers.py` = **14 passed**。
- consumer 9 file の焦点走: **181 passed / 9 skipped** (skip はすべて既存の growth hold)。
- 敵対レビューの fix 後: `test_backoff_consumers.py` 単独走 = **18 passed**。
- **変異 matrix (本走、HEAD = `aef3f725d`): baseline PASSED、KILLED 5 / SURVIVED 0 /
  MISMATCH 0 / TIMEOUT 0、期待 node は完全一致 (matching 5/5)。**
  台帳は `2026-09-02_default-adaptive-baseline-replacement-mutation/` に置いた。
- 受入全走の結果は worklog エントリに記録する。

### 変異が暴いたもの (probe → 本走の差)

**probe (全件 SURVIVED 期待で観測 node を集める走) で 1 件が生存した。**
判定閾値 `nf = BETWEEN_RUN_CV` を `nf = 0.19` へ置き換えても、
`test_backoff_report_verdict_pins_all_branches_and_noise_boundary` の 3 分岐が
すべて通ってしまった。

敵対レビューは静的にこの穴を名指ししていた (「閾値も 3% から 20% 未満へ動かせば、
この test は同じ正分岐のまま通る」) が、1 回目の fix は
`assert BETWEEN_RUN_CV == 0.03` という**定数の値の pin**で閉じたつもりになっていた。
**定数の値を固定しても、その定数が判定に使われていることは固定されない。**
fixture の +20% / +2% / -20% はいずれも 0.03 と 0.19 で同じ分岐へ落ちるからである。

2 回目の fix で **0.03 と 0.19 の間に落ちる +5% のケース** (parametrize id
`between-thresholds`) を 1 つ足し、本走で KILLED になった。
**実装・数式・`BETWEEN_RUN_CV` の値・分岐条件は 1 行も変えていない。**

### 変異の内訳

| ID | 変異 | 期待 | 観測 | 種別 |
|---|---|---|---|---|
| MUT-T2187B-DEFAULT-BASELINES | 既定 baseline を `no-backoff,stock-adaptive` へ戻す | KILLED | KILLED | 受理集合 (描画集合) |
| MUT-T2187B-EXPLICIT-OPT-IN | 明示指定した `stock-adaptive` を無視させる | KILLED | KILLED | **過剰拒否の正例** — 能力ごと削って D1506 を満たしたことにする経路を塞ぐ |
| MUT-T2187B-VERDICT-MECHANISM-CLAIM | verdict 正文を旧い機構主張へ戻す | KILLED | KILLED | report 内容 pin |
| MUT-T2187B-PROVENANCE-KEY | provenance key を `adaptive_tps(stock Cicada)` へ戻す | KILLED | KILLED | report 内容 pin |
| MUT-T2187B-NOISE-FLOOR-BOUNDARY | `nf = BETWEEN_RUN_CV` を `nf = 0.19` へ | KILLED | KILLED | 判定境界が実際に使われていることの pin |

report 内容 pin の 2 件は certified 受理集合の変更ではない (DW-M08 の区別)。
