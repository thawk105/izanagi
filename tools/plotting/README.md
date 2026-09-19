# plot_backoff.py — backoff sweep campaign の論文品質作図

`output/campaigns/<id>` の artifact から、論文品質の backoff sweep 図を生成する
共通スクリプト。図の数値は WAL (throughput の n 反復生値) と dat (abort%/IPC 集約値) から
その場で計算し、CCBench commit は campaign の lock file から読む。生成した図の provenance には
入力・生成器・出力の SHA-256 と、**実際に描いた基準線の label・値・genome** を記録する —
「どの WAL からどの図を作り、図のどの線が何を指しているか」が閉じる (proof-chain 思想と整合)。

## 使い方

```
python plot_backoff.py [--baselines LIST] OUT_PREFIX CAMPAIGN_DIR [CAMPAIGN_DIR ...]
```

`--baselines` は `no-backoff` / `stock-adaptive` の comma 区切り部分集合。**既定は
`no-backoff` の 1 本**である (2026-09-02 に `no-backoff,stock-adaptive` から狭めた、D1506)。
`stock-adaptive` は **CCBench 既定 3 定数** (刻み 100 µs / 上限 1000 µs / 更新間隔 10 µs) の
適応 backoff であり、調整済み adaptive ではない。D1506 は既定 adaptive を測ること自体を
禁じないので、明示すれば今も描ける。**禁じているのは、既定 adaptive を単独の適応基準線に置いた
比較から機構の優劣を言うことである。**未知の値はエラーになる。
既定 adaptive も併記したいときは次のように明示する。

```
python plot_backoff.py --baselines no-backoff,stock-adaptive OUT_PREFIX CAMPAIGN_DIR [CAMPAIGN_DIR ...]
```

例 (3 workload を 1 枚に統合):

```
python plot_backoff.py --baselines no-backoff figures/backoff_sweep \
    output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9 \
    output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e \
    output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7
```

campaign を複数指定するとその順で横並び (workload 比較) になる。1 つだけ渡せば単独図。

## 出力

- `OUT_PREFIX.png` / `.pdf` — 図 (上段 throughput+95%CI・baseline、下段 abort%+IPC)
- `OUT_PREFIX.provenance.json` — schema `izanagi-backoff-figure-provenance/v2`。
  campaign ごとに WAL・dat・lock file の repo-relative path と **full SHA-256**、
  生成器自身の path と SHA-256、出力 PNG / PDF の SHA-256、測定条件 (`conditions`)、
  そして `baselines[]` を記録する。`baselines[]` は **実際に図へ描いた基準線だけ**を、
  図中の label 文字列・その線の y 値 (tps)・95% CI 半幅・genome の組で持つ。
  この list が「図のどの線が何を指しているか」の機械可読な正本である。

## 設計上の約束

作法の全文は `FIGURE_CONVENTIONS.md` (図種に依存しない規約の本体)。本スクリプトはその backoff sweep 向け実装。

- **入力は WAL・dat・campaign の lock file の 3 種**。図の数値はすべてその場で再計算する
  (記憶・手写しなし)。3 種とも provenance で SHA-256 束縛する。
- **95% CI は throughput の n 反復生値から** (点推定 = 標本平均、半幅 = 小 n では
  t 分布 `t_{0.975,n-1}·s/√n`、n≥30 は `1.96·s/√n` の正規近似。正本は
  `FIGURE_CONVENTIONS.md` §2)。n<2 は分散を推定できず CI 計算不能なので、その点は
  誤差棒を描かない (幅ゼロの棒を「95% CI」と偽装しない)。
- **abort%/IPC は dat の集約値** (現状 1 点集約 — 反復値が保存されれば CI 化可能)。
- **依存は matplotlib/numpy のみ**。外部スタイル非依存で自己完結。
- **計測機上では走らせない** (どのマシンが計測機かは時期で変わる — 環境タグの正本を参照)。
  図生成に計測は不要で、単一テナント直列の計測窓を汚さないため、WAL/dat を計測機外に
  取り出して実行する。

## 拡張ポイント

- abort%/IPC の反復値が WAL に入れば、下段にもエラーバーを足せる (`load_campaign` の
  `abort_ipc` を reps ベースに変える)。
- backoff 以外の軸 (sort-strategy 等) は genome パースを差し替えれば流用可能。

## B-10 extended backoff figure

`plot_b10_extended_backoff.py` は、完走済み B-10 拡張格子専用の生成器である。
B-10 対応を `plot_backoff.py` 側へ足すのではなく、その WAL admission、style、
campaign condition 抽出を**依存として再利用する**形にした。

**この分離は「`plot_backoff.py` を今後も変更してはならない」という意味ではない**
(2026-09-02 訂正)。fig2b と fig2c の provenance が持つ `plot_backoff.py` の SHA-256 は
**その図を生成した時点の bytes**の記録であり、現行 bytes を縛る pin ではない。
実際、現行 bytes は記録値と既に異なり、それでも
`orchestrator/tests/test_backoff_figure_provenance.py` と
`test_b10_extended_figure_provenance.py` は緑である — 両テストは記録された生成時定数どうしを
照合し、live source を再 hash しないためである。凍結図の bytes・数値・provenance は
`plot_backoff.py` を編集しても変わらない。

```
python3 tools/plotting/plot_b10_extended_backoff.py OUT_PREFIX MEASUREMENT_ROOT
```

- 3 workload の raw 29 点を検査し、F718 の 1000 µs だけを除外して有効 28 点を描く。
- static 0 µs を保持するため x 軸は symlog。表示 tick は疎だが全 28 点を artist に持つ。
- 上段は WAL 5 反復の mean + t95 CI、下段は dat の abort fraction。latency は描かない。
- y 軸は workload-local。パネル間の高さ・傾きを比較しない文を図と provenance に持つ。
- provenance v1 は外部入力 22 file、receipt chain、campaign identity、測定条件、除外値、
  generator/dependency/output hash、D1107 の記述的 claim 境界を記録する。
- `IZANAGI_B10_MEASUREMENT_ROOT` で検査時の canonical root を差し替えられる。

論文図の再現コマンド、caption、job/campaign 表は
`docs/paper-story/figures/README.md` の fig2c 節を正本とする。

## A-2 4-cell certification figure

`plot_a2_certification.py` は、完走済み attempt `t2022-20260828c` の 4 cell を
2 workload × 2 段 (throughput / abort rate) で描く専用生成器である。

```bash
python3 tools/plotting/plot_a2_certification.py \
    [--measurement-root PATH] \
    [--certification PATH] [--raw-manifest PATH] OUT_PREFIX
```

measurement root は option、`IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT`、既定の
durable authority の順で決まる。入力は root 配下の WAL 2 本と raw cell JSON 4 本、
tracked `certification.json` と `raw-manifest.json` の計 6 + 2 本である。外部 6 本は
manifest の root-relative path と SHA-256、tracked 2 本は canonical SHA-256 で束縛する。

WAL では `bench_done.payload.tps` だけを標本として読み、raw JSON と順序込みで照合する。
各 cell は n=5 を必須とし、median、sample mean、sample standard deviation、CV、
`t_(0.975,4) * s / sqrt(5)` の 95% CI 半幅を生値から計算する。abort rate は
`leading_indicators.abort_rate` の集約 1 点であり、CI と因果機序の主張を持たない。

outer protocol status と effects は hash 束縛された certification からコピーする。
生成器は `reject`、効果、研究上の成功・失敗を導出・昇格・書換えしない。再計算した
median / CV / effect は authority との fail-closed な相互検算にだけ使う。

出力は `OUT_PREFIX.png`、`.pdf`、`.provenance.json` の 3 本。保存前に実寸 4 axis の
renderer-backed layout check を実行し、text の重なり・逸脱・隣 panel 侵入があれば
成果物を publish しない。provenance は外部入力、測定条件、4 cell の生値と統計、
artist と genome の対応、caption、展開済み再現 argv を記録する。
再現 argv は repo 配下の certification、raw manifest、出力 prefix を repo-relative で、measurement root を絶対 path で記録する。

provenance の generator SHA-256 は**図を生成した時点の bytes の記録**であり、後日の
現行 source を縛る pin ではない。landed artifact の検査も live generator の再 hash を
要求せず、生成時記録として扱う。

## B-10 static-backoff right tail (09-15 formal cohort) figure

`plot_b10_static_tail_formal.py` は、完走済み B-10 右 tail 正式 cohort (group
`b10-backoff-grid-20260915T061814Z-545445`、事前登録 §4.1 の 8 点 × 3 workload × 5 反復) を
3 列 × 2 段 (throughput / abort 率) で描く専用生成器である。既存生成器を import しない (自己完結)。

```bash
python3 tools/plotting/plot_b10_static_tail_formal.py \
    [--measurement-root PATH] OUT_PREFIX
```

measurement root は option、`IZANAGI_B10_TAIL_MEASUREMENT_ROOT`、既定の
`/work/1/SFC/tanab/b10-backoff-grid-t2500-formal` の順で決まる。入力は root 配下の集団報告 3 file
(`group-report-20260915/t2500-backoff-static-tail-formal.json` / `.dat` / `-complete.json`) で、
root 相対 path と生成器の pin 表 (SHA-256) で束縛する。pin は CLI から渡せない。

- 判定 (`verdict`、workload の `state`、区間の `state` / `qhat` / `qL` / `qU` / `L` / `U`) は集団報告から
  コピーし、再計算しない。`L = 1 − 2^qU` と `U = 1 − 2^qL` の一致だけを検査する。
- 平均・t 分布 95% CI・abort 率 (整数カウンタから全精度)・変動係数・端点比は reps の生値から再計算する。
  集団報告の `statistics` と fail-closed で照合するのは平均 2 種・変動係数 2 種・abort 率の標本標準偏差で、
  CI と端点比は再計算だけで照合相手を持たない。
- `performance_certified` が `false` 以外、正しさ記録 120 件のいずれかが `certified` でない、区間集合に
  境界参照 1000 が入る、`.dat` が 120 行でない、SHA-256 不一致のいずれでも成果物を出さない。
- 保存前に実寸 6 axis の renderer-backed layout check を実行し、text の重なり・逸脱があれば
  3 成果物を 1 つも出さない。
- 言い方は事前登録 §4.5 の固定表現の英訳に限り、caption に `performance_certified: false` を残す。

出力は `OUT_PREFIX.png`、`.pdf`、`.provenance.json` の 3 本。provenance の schema は
`izanagi-b10-static-tail-formal-figure-provenance/v1`。論文図の再現コマンド、caption、proof chain は
`docs/paper-story/figures/README.md` の fig8 節を正本とする。

## A-1 balanced5 sized attempt-0001 (対差平均 ± 登録済み区間) figure

`plot_a1_sized_paired.py` は、A-1 balanced5 sized 本走 attempt-0001 (study
`paper-story-a1-20260901-balanced5-sized-v1`、3 workload × 30 対 × 2 arm) の対差 (variant − baseline) を
3 列 1 段で描く専用生成器である。既存生成器を import しない (自己完結)。

```bash
python3 tools/plotting/plot_a1_sized_paired.py [--repo-root PATH] OUT_PREFIX
```

入力は repo 内 tracked の公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` の 3 file
(`result.json` / `receipt.json` / `.complete.json`) と policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` で、
repo 相対 path と生成器の pin 表 (SHA-256) で束縛する。pin は CLI から渡せない (test は `expected_hashes` 注入 seam を使う)。

- 統計 (mean / variance / sd / h / baseline mean / B / 区間) は `statistics.pairs` の 30 対から再計算し、`statistics` の記録値と
  fail-closed で照合する。分類 (`classification`) は記録値をコピーし、述語との一致だけを検査する。
- `formal` が false 以外、`promotion_prohibited` が true 以外、`valid` が true 以外、`errors` 非空、n ≠ 30、対の差の不整合、
  両 arm の `correctness_evidence.certified` が `[true]` 以外、policy SHA-256 と `policy_sha256` の不一致、`variance_plan_breach`
  true、results 稿 (caption_source) の不在のいずれでも成果物を出さない。
- 保存前に renderer-backed layout check を実行し、text の重なり・逸脱があれば 3 成果物を 1 つも出さない。
- caption は lane の 3 値 (`formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only`) と
  「単一 attempt・headline 値でない・workload 横断の結論を作らない・C1 の再現ではない・反復間の安定性を言わない」の固定文を
  逐語で含み、`improvement` / `regression` / 有意性の語を使わない。

出力は `OUT_PREFIX.png`、`.pdf`、`.provenance.json` の 3 本。provenance の schema は
`izanagi-a1-sized-paired-figure-provenance/v1`。`tracked_inputs` には results 稿
`docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` を `caption_source` として SHA-256 付きで記録する
(稿は provenance の SHA-256 を持たない、F36)。論文図の再現コマンド、caption、proof chain は
`docs/paper-story/figures/README.md` の fig9 節を正本とする。

## B-7 fixed 5 µs 三 workload 退行 (床値判定の記述図) figure

`plot_b7_fixed5_regression.py` は、採用候補 fixed 5 µs を 3 workload で同一 attempt に測った study
`paper-story-b7-fixed5-regression` (attempt `b7f5-20260919a`、3 workload × 2 cell × 5 標本) の標本・median・効果と、
D1639 の between-run 床値との比較を 2 段 (上段 3 panel の標本、下段 1 panel の効果と −floor) で描く専用生成器である。
既存生成器を import しない (自己完結)。

```bash
python3 tools/plotting/plot_b7_fixed5_regression.py [--repo-root PATH] [--measurement-root PATH] OUT_PREFIX
```

入力は repo 内 tracked の権威 bytes `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json` と
`raw-manifest.json`、床値 JSON `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json`、
policy `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` (6 file、生成器の pin 表で SHA-256 束縛。pin は CLI から渡せない) と、
raw-manifest が SHA-256 で束縛する repo 外の raw cell JSON 6 本 (`--measurement-root` 配下、既定は durable authority の path)。

- median は raw の 5 標本から再計算し certification の `median_tps` と一致を要求する。効果は certification の `effects` を写し、median の比からの
  再計算と照合する。判定は生成器が作らず、稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` §2.1 の判定を
  定数として写し、述語 `effect < −floor` (床 = 床値 JSON の `between_run.cv` 全桁、strict) との一致だけを fail-closed で検査する。
- SHA-256 不一致、schema / study / attempt / cell 順序の不一致、`source_binding_status` ≠ bound、adopted の `src_token` 不整合、
  `correctness.status` ≠ certified、raw の verify 記録の不整合、性能標本が trace-enabled、`unstable`、標本数 ≠ 5、median / 効果 / 判定の不一致、
  床値 JSON の genome / 条件の不一致、caption_source の不在のいずれでも成果物を出さない。
- 保存前に renderer-backed layout check を実行し、text の重なり・逸脱があれば 3 成果物を 1 つも出さない。
- caption は英文で、「B-7 の充足判定ではない」「規則 (effect < −floor、strict) と D1639 の床の出自」「退行なしは優越でも差が無いことの証明でもない、
  有意差判定はしない」「outer status は論理積の出力で研究の判定ではない」「単一 attempt、昇格しない」「正しさは別走行、性能の認証ではない」
  「CI は標本の記述」「上段 y は workload 別」「既存材料とプール・比較しない」の固定文を逐語で含む。

出力は `OUT_PREFIX.png`、`.pdf`、`.provenance.json` の 3 本。provenance の schema は
`izanagi-b7-fixed5-regression-figure-provenance/v1`。`tracked_inputs` には稿を `caption_source` として SHA-256 付きで記録する
(稿は provenance の SHA-256 を持たない、F36)。`external_inputs` には raw 6 本の root 相対 path と SHA-256 を記録する。
論文図の再現コマンド、caption、proof chain は `docs/paper-story/figures/README.md` の fig10 節を正本とする。

## S-1a 9 対 (失敗報告図) command example

`plot_s1_9pair.py` は、縮小主張 S' の登録 9 対を凍結 report と admission 済み WAL から描く。
標本・測定条件・相対中央値差は WAL から再計算し、凍結 report の accepted evidence と全行照合する。
**judgment と p 値は凍結 report だけを権威とし、WAL 側の gate 再計算は一致検査にしか使わない**
(作図側が判定を作り直さないため)。

```bash
python3 tools/plotting/plot_s1_9pair.py \
    docs/paper-story/figures/fig4_s1a_9pair_direct_comparison \
    output/reports/s1_direct_comparison/report.json \
    --develop output/campaigns/s1-direct-develop-direct-comparison-d0f495bf \
    --floor   output/campaigns/s1-direct-floor-direct-comparison-b82b9229 \
    --block1  output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2 \
    --block2  output/campaigns/s1-direct-block2-direct-comparison-9645b16a
```

出力は `<OUT_PREFIX>.{png,pdf,provenance.json}`。provenance の schema は
`izanagi-s1-9pair-figure-provenance/v1` で、`reproduction.argv` に上の argv を、
`caption` にキャプション正文を持つ。図と入力の対応・版差・文脈セルの扱いは
`docs/paper-story/figures/README.md` の該当節が正本。

## Cicada adaptive backoff の 3 定数 (T-2187)

`plot_t2187_adaptive_consts.py` は、`tools/pegasus/probes/t2187_adaptive_const_probe.py` が出す
`izanagi-cicada-adaptive-3const-probe/v1` の結果 JSON を描く。**入力は 1 file = 1 ノード = 1 rep**
なので、同じ段の全 rep を並べて渡す。集約は生値から計算し、集約済みの値を孫引きしない。

```bash
python3 tools/plotting/plot_t2187_adaptive_consts.py grid OUT_PREFIX \
    /path/to/results/stage1-rep0-*.json /path/to/results/stage1-rep1-*.json ...

python3 tools/plotting/plot_t2187_adaptive_consts.py threads OUT_PREFIX \
    /path/to/results/stage2-rep0-*.json /path/to/results/stage2-rep1-*.json ...
```

- `grid` は刻み × 更新間隔の 2 次元 (対数×対数) を 3 workload 分並べ、**上段 throughput /
  下段 abort 率**の縦積みで描く。2 次元図に誤差棒は描けないので、各セルの 95% CI 半幅を
  相対値 (%) で注記する。陽性対照 (stock adaptive) のセルは枠線で明示する。
- `threads` はスレッド数を横軸に、系列をセルにして同じ縦積みで描く。95% CI はエラーバー。
  `no backoff` と `stock adaptive` は役割語でなくそれが何かで名指した系列として必ず描く。
- **95% CI は t 分布** (`t_{0.975,n-1}·s/√n`)。t 分位点は正則化不完全ベータ関数から自前で求め、
  `scipy` に依存しない。`1.96` の正規近似は小 n では使わない。n=1 のセルは CI を描かず
  `CI n/a` と明記する。
- 保存後にレイアウトを機械検査し、テキストの重なり・スパイン外へのはみ出し・隣パネルへの
  被りがあれば **rc 非 0 で落ちる**。
- provenance の schema は `izanagi-t2187-adaptive-const-figure-provenance/v1`。入力全 file の
  絶対パスと SHA256、`ccbench_commit`、`patch_sha256`、全 `pbs_jobid`、測定条件、
  図に出した主要数値、そして**認証されていない旨**を記録する。
- **この図の数値は認証されていない** — trace-disabled の性能測定のみで直列性の検査を通しておらず、
  variant 採用の根拠にしてはならない (規律 2)。図中にもその旨を出す。

## 動的 adaptive backoff (dynamic-backoff-mechanism)

`plot_dynamic_backoff.py` は、拡張 cell 書式の probe (`t2187_adaptive_const_probe.py`、結果 schema は
`izanagi-cicada-adaptive-3const-probe/v2` (A+B) または
`izanagi-cicada-adaptive-3const-probe/v3` (A+B+C)) が出す性能 JSON 6 または 7 file
(1 file = 1 ノード = 1 block、相異なる `rep_index`) と、`--backoff-trace` の診断 JSON 1 file
(`izanagi-dynamic-backoff-trace/v2` (A+B) または
`izanagi-dynamic-backoff-trace/v3` / `v4` (A+B+C)) から 3 図を描く。
事前登録は `docs/dynamic-backoff-preregistration.md`。

```bash
python3 tools/plotting/plot_dynamic_backoff.py OUT_PREFIX --trace-json DIAG.json PERF_REP0.json ... PERF_REP6.json
```

診断入力は schema ごとに閉じた契約を持つ。v2 は legacy の 11-field 3 cell、v3 は legacy または
cohort 1 の 12-field policy 3 cell で、どちらも観測長は 3 秒、3 workload x 2 thread の exact
18 row である。v4 は cohort 2 の 12-field policy 3 cell、観測長 6 秒、同じ exact 18 row を要求する。
v4 の通常 event は count-closed であり、`terminal_flush=1` の terminal event は 0 件、または末尾に
1 件だけを受理する。0 件なら summary は `updates=retained=len(trace_events)`、`dropped=0`、
`flushes=0`、1 件なら `updates=retained=通常 event 数`、`dropped=0`、`flushes=1` でなければならない。
全性能入力と診断入力では、repo / CCBench / driver / PBS / ordered patch stack を含む common identity と
観測長が逐語一致しなければならない。

cohort 2 の図を実際に出力するには、診断 JSON とは別に、観測長 6 秒かつ同一 identity の
trace-disabled performance JSON が 6 または 7 本必要である。本 wave はこの performance 計測を
行っていないため、cohort 2 診断成果物だけでは公開 CLI を起動できず、図も出力できない。
この制約を迂回する診断-only CLI mode は提供しない。

- `OUT_PREFIX-thread-axis.*` — スレッド軸 7 系列 (none / stock / tuned / tuned-u10240 / cw / cw-as / cw-as-dyn)、
  上段 throughput / 下段 abort 率、t 分布 95% CI。基準線は D1506 の `none` と `tuned`。`stock` は陽性対照。
- `OUT_PREFIX-contrasts.*` — 事前登録 §4 の対比 (対内 log 比、t 分布 95% CI、±3% の等価域) の forest plot。
  判定語と H1〜H7 の複合判定は provenance に書く (閾値は CLI で変えられない)。
- `OUT_PREFIX-diagnostic.*` — 診断 build の `Backoff_` 軌跡と方向的中率。**診断 build の throughput は描かない**
  (headline 不適格)。
- `OUT_PREFIX.provenance.json` (`izanagi-dynamic-backoff-figure-provenance/v1`) — 全 8 入力の sha256、
  対比ごとの 24 点 (平均・CI・判定語)、`repo_head` / `prereg_sha256` / patch stack、認証されていない旨。

**この図の数値は認証されていない** (規律 2)。計測機の外で走らせる。

## SS2PL lock study command example

```bash
python3 tools/plotting/plot_ss2pl_lock_study.py \
    --sweep /path/to/sweep.json \
    --controls /path/to/controls.json \
    --replication /path/to/replication.json \
    --output-dir /path/to/figures
```

## T-2216 event-driven backoff walk

`plot_t2216_backoff_walk.py` は、静的 fixed-backoff セルだけで校正した
event-driven walk model の JSON と、その元になった Pegasus probe 結果 JSON を描く。
図は計測機の外で生成する。3 mode は同じ入力契約を持つ。

```bash
python3 tools/t2216_backoff_walk_model.py \
    /path/to/measured.json /path/to/backoff.hh.txt /path/to/t2216-model.json

python3 tools/plotting/plot_t2216_backoff_walk.py prediction OUT_PREFIX \
    /path/to/t2216-model.json /path/to/measured.json /path/to/backoff.hh.txt

python3 tools/plotting/plot_t2216_backoff_walk.py residence OUT_PREFIX \
    /path/to/t2216-model.json /path/to/measured.json /path/to/backoff.hh.txt

python3 tools/plotting/plot_t2216_backoff_walk.py mechanism OUT_PREFIX \
    /path/to/t2216-model.json /path/to/measured.json /path/to/backoff.hh.txt
```

- `prediction` は更新間隔ごとの観測 raw 反復と model 反復を別系列にし、いずれも
  Student-t 95% CI を付ける。stage1 と D1475 は別 dataset として表示し、順位判定では混ぜない。
- `residence` は時間重み付き survivor と `P(Backoff > 100 us)` を表示する。
- `mechanism` は source-exact、切り捨て除去、tail 感度、勾配符号の中間量を 2x2 で表示する。
- 出力は `<OUT_PREFIX>.{png,pdf,provenance.json}`。provenance は model、probe JSON、
  pinned backoff copy の絶対パスと SHA256、PBS job id、seed、条件順、raw 反復から再計算した
  主要値、PNG/PDF hash、再現 argv を持つ。入力が作図中に変わった場合は非0で終了する。
- 数値は認証されていない。trace-disabled の Silo 性能測定を使う純解析であり、
  直列性検査を通しておらず、variant 採用の根拠には使えない。

段 6 fix 後の入力契約では、model generator の live SHA256 と、8 反復・3 秒を含む固定 config を
loader が照合し、不一致を fail-closed にする。model 側も元測定 JSON の期待 SHA256 を literal に
固定する。status の到達上限は write-heavy の `shape_match` であり、H1、balanced / read-heavy、
中間量は status とは独立した整合検査または予測として出力する。

現行の作図規約に合わせ、prediction 図の水平参照線は raw 反復から再計算した Student-t 95% CI 帯を
伴う。適応機構との比較用に、no backoff と調整済み adaptive (刻み 1 µs / 更新間隔 2560 µs /
上限 1000 µs) をともに表示し、10 µs panel は 8 点格子固有の tick も省略しない。
