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

**A-6 (read-heavy、1 workload × 2 cell) の図 fig11 (2026-09-20):** 同じ生成器が study
`paper-story-a6-certification` の attempt `a6-20260908b` も描く。受理する study は `STUDY_PROFILES` の
exact 2 件 (A-2 / A-6)、pin 表 `CANONICAL_SHA256` は 3 leaf (A-2 の 2 attempt + A-6)。workload 数 N は
embedded policy から導き、外部入力は 6 × N file、request / 時刻の一意検査は N、layout check は 2 行 × N 列
(A-2 は 12 file・4 axes のまま)。A-6 の caption は稿 `docs/paper-story/results/2026-09-18-a6-certification-reject.md`
を `caption_source` として SHA-256 束縛する。**着地済み fig5 / fig6 / fig7 の bytes・caption・artist 射影は不変**
(着地 test が守る)。**再生成する current-full の provenance には top-level `study` が加わる** (A-2 を再生成しても
同じ。着地済み provenance は key を持たないので読取側は無ければ A-2 と扱う)。

```bash
python3 tools/plotting/plot_a2_certification.py \
    --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b \
    --certification output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json \
    --raw-manifest output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json \
    docs/paper-story/figures/fig11_a6_certification_reject
```

再現コマンド、caption、proof chain は `docs/paper-story/figures/README.md` の fig11 節を正本とする。

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

**再現欄付きの後継図 (fig8b、2026-09-20):** `OUT_PREFIX` の後ろに `--reproduction-cohort 2` を付けると、
**主結果 cohort 1 (上 block) と独立再現 cohort 2** (group `b10-backoff-grid-20260919T131526Z-2235286`、
`group-report-20260919-cohort2/` の 3 file、下 block) を縦 2 block (4 行 × 3 列、7.2 × 10.6 in) で
区別して併記する。cohort 2 単独の図は作らない (受理する値は `2` だけ)。役割 (1 = primary、2 = reproduction)
と順序は生成器の `COHORTS` 表で固定し、CLI からも provenance の改変からも入れ替えられない。拒否条件と
pin (CLI から渡せない) は両 cohort に同じ。provenance の schema は `.../v2` で、`cohorts[]` に cohort ごとの
記録を持ち、top-level に cohort をまたぐ統計 field は無い (`claim_boundary.cohorts_pooled: false`)。caption は
事前登録 §4.5 の固定表現を各 cohort へ独立に適用し、合成・プール・一致度評価をしない旨を含む。省略時は
上の単 cohort 経路 (fig8 の形) のままで、その受理集合・射影は変えていない。図番号の英字 suffix (`fig8b_`) を
受理するのは `--reproduction-cohort 2` の経路だけ。正本は同 README の fig8b 節。

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

## A-1 balanced5 sized attempt-0002 (対差平均 ± 登録済み区間、`variance_plan_breach` 表示) figure

`plot_a1_sized_paired.py` は attempt ごとの repo 所有 exact pin 表 (`ATTEMPTS`、`attempt-0001` / `attempt-0002` の 2 entry だけ) を持ち、`--attempt` で
sized 本走の 1 attempt を選んで単独の記述図を描く。attempt-0001 (上の節、fig9) の定数・返り値・caption・描画・既定 CLI は変えていない。2 attempt をプールした図・差・比・
再現判定を描く経路は持たない (D1993 項 6、D2194 項 6)。

```bash
python3 tools/plotting/plot_a1_sized_paired.py [--repo-root PATH] [--attempt {attempt-0001,attempt-0002}] OUT_PREFIX
```

- attempt-0002 の入力は `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` の 3 file と共通 policy の 4 件で、pin 表で SHA-256 束縛する。
  pin は CLI から渡せない (D1752、test は `expected_hashes` 注入 seam)。未知の attempt・pin の key 集合の不一致は拒否する。
- `variance_plan_breach` は両 attempt で述語 (`sd > planned sigma`) との一致を検査する。true の拒否は attempt-0001 だけに残し、attempt-0002 は記録値を写して
  panel 題の 2・3 行目 (`variance_plan_breach=true|false`、sd と planned sigma の 2 量。比は作らない) に描く。図の上端に「attempt-0001 とプールも比較もしない」旨の 1 行を描く。
- caption は attempt-0002 用の組み立て (固定文 `Attempt-0001 is neither pooled nor compared with this attempt; ...` と `No cause is attributed to variance_plan_breach.`、
  lane の 3 値、workload ごとの breach・sd・planned sigma) で、`docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` を `caption_source` として SHA-256 付きで記録する。
  provenance は同じ schema に `attempt` を足す (attempt-0001 の provenance には足さない)。
- 論文図 fig14 の再現コマンド、caption、proof chain は `docs/paper-story/figures/README.md` の fig14 節を正本とする。

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
  再計算と照合する。図に出す判定の出所は稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` §2.1 の転記
  (定数) で、生成器は述語 `effect < −floor` (床 = 床値 JSON の `between_run.cv` 全桁、strict) を転記との整合検査にだけ使う。
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

## 論文ストーリーの現況図 (3 幕 + §8 A/B 群の状態、値なし) figure

`plot_arc_status.py` は、論文ストーリー文書の凍結版 (fig3b は `docs/paper-story/2026-09-19.md`、fig3c は `docs/paper-story/2026-09-21c.md`) の
§0 の 3 幕の要約と §8 の証拠項目 (A 系列 5 + B 群 11) の【状態】だけを、値を 1 つも描かずに 1 枚の模式図にする専用生成器である
(`fig3_arc_status.png` の後継図 `fig3b_` と、その後継図 `fig3c_`)。既存生成器を import しない (自己完結)。

```bash
python3 tools/plotting/plot_arc_status.py [--repo-root PATH] [--states PATH] OUT_PREFIX
```

入力は状態 JSON (`--states` 省略時は `tools/plotting/arc_status_story_2026-09-19.json`、schema `izanagi-arc-status/v1`) と、
JSON の `story_path` が指す凍結本文である。状態語の意味の正本は本文で、JSON は人がそこから写した射影である。
`story_version` は `YYYY-MM-DD` に英小文字 1 字の接尾辞を許す (同日の版 `2026-09-21c` など。暦日検査は日付部分に掛け、`story_path` は
接尾辞込みで `docs/paper-story/<story_version>.md` と一致させる)。`figure_created` は接尾辞の無い日付だけを受理する。

- 4 状態 `obtained` / `uncertified` / `awaiting-ruling` / `not-obtained` を色とマーカー形 (塗り丸 / 中抜き菱形 / 中抜き三角 / ×)
  で描く。`obtained` は「判定または完了の記録がある」であって主張の支持ではない (B-1 の `not met`、A-6 の `reject` も obtained)。
- 各項目の `source_anchor` (`§8 A-1` / `§0 item 3` / `§0 act 3`) が本文の該当節にちょうど 1 行の項目見出しとして存在することを
  検査する。意味の一致は検査しない。
- 自由文 (label / sublabel / 状態定義文) に数量が混じると拒否する: `=`、`%`、単位語、数詞、および JSON で宣言した証拠項目 ID と
  `reference_ids` 以外の数字入り token。caption と脚注の節番号・版名・図番号は構造 field から組み立てる。
- key 集合の不一致 (未知・不足・重複 key、NaN / Infinity)、4 状態以外の `state`、ID 重複、`story_path` の不一致、prefix が
  `fig<N><letters>_` でない、既存の 3 出力のいずれかが存在する (上書きしない)、保存前の layout check (全 Text の figure 内包・
  所属領域内包・相互非交差・兄弟セル非交差・marker 非交差) の違反、のいずれでも成果物を出さない。
- 判定・値・認証を再計算しない。図は「記録された状態の要約」であり、採用・認可・certification の根拠にしない。
- caption は固定 template である。`story_version` が `2026-09-19` のときだけ fig3b の caption (2026-09-19 版の項目の状態を述べる文を含む) を
  1 文字も変えずに使い、それ以外の版では項目の状態に依存しない固定 caption を使う (項目固有の判定語・限定は各項目の副ラベルが担い、正本は本文 §8)。

出力は `OUT_PREFIX.png` (200 dpi)、`.pdf`、`.provenance.json` の 3 本。provenance の schema は
`izanagi-arc-status-figure-provenance/v1` で、入力 2 file (JSON・本文) と生成器・出力の SHA-256、描いた項目 (`drawn_items`: ID・
状態・実表示文字列)、状態定義、caption、展開済み argv、matplotlib / numpy の版を持つ。論文図の再現コマンド、caption、proof chain、
次の版との整合手順は `docs/paper-story/figures/README.md` の fig3b 節と fig3c 節を正本とする。

## K2 手動 loop 3 巡のデータフロー (説明図、値なし) figure

`plot_k2_loop_flow.py` は、凍結稿 `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` が記録した K2 手動 loop の
3 巡 (提案 → 評価 → critic) のデータフロー — 役割と遮断の所在、親が射影する入力 key、評価経路、実測の還流 2 回・診断の還流 1 回
(exact 6 field)、規律 6 の自己申告 marker — を、性能値を 1 つも描かずに 4 列 × 6 lane の模式図にする専用生成器である (`fig12_`)。
既存生成器を import しない (自己完結)。

```bash
python3 tools/plotting/plot_k2_loop_flow.py [--repo-root PATH] [--flow PATH] OUT_PREFIX
```

入力は流れ JSON (`--flow` 省略時は `tools/plotting/k2_loop_flow_2026-09-20.json`、schema `izanagi-k2-loop-flow/v1`)、
生成器に path 固定の稿 (caption_source)、role 定義 3 file (`.claude/agents/{planner-v4,coder-v4-autonomous-k2,critic}.md`) である。
JSON は人が稿から写した射影で、意味の正本は稿である。

- 各要素の `source_anchor` (`§1.4` / `§2.2 巡 1` の形) が稿の見出し行としてちょうど 1 行あることを検査する。意味の一致は検査しない。
  稿の bytes は anchor の検査と SHA-256 の記録にだけ使い、値・判定を再計算しない。
- role 定義の frontmatter `tools:` (`[]` ⇔ `tools_none: true`) が JSON の宣言と一致することを検査し、3 file の SHA-256 を記録する
  (生成時点の記録で、着地後の一致は要求しない)。
- 提案の literal・job id・日付・入力 key・diagnosis の 6 field 名・規律 6 の自己申告 (`form` は role 固定、`instruction_like_detected` は
  bool で marker の形が変わる) は typed field から固定 template で描き、自由文に数量が混じると拒否する (`=`、`%`、単位語、数詞、宣言 ID・
  instance・`job <id>` 以外の数字入り token)。
- この凍結図の矢印 7 組 (実測の還流 m1 / m2a / m2b、診断の還流 d1、不在 a1 / a2 / a3) は生成器の定数と完全一致を要求し、描いた artist
  から provenance の `arrows` を組む。caption の回数語は固定文である。
- key 集合の不一致、enum 外、value の範囲・不一致、未評価列の制約違反、anchor の不正・非一意、role 不一致、prefix が `fig<N><letters>_`
  でない、既存の 3 出力のいずれかが存在する (上書きしない)、保存前の layout check (全 Text の figure 内包・所属領域内包・相互非交差・
  兄弟領域非交差・marker 非交差・**矢印線分と Text の非交差**) の違反、のいずれでも成果物を出さない。

出力は `OUT_PREFIX.png` (200 dpi)、`.pdf`、`.provenance.json` の 3 本。provenance の schema は
`izanagi-k2-loop-flow-figure-provenance/v1` で、入力 5 file (JSON・稿・role 定義 3 本) と生成器・出力の SHA-256、`caption_source`、
描いた項目 (`drawn_items`: id・kind・実表示文字列)、矢印 (`arrows`)、role の遮断宣言 (`roles`)、caption、展開済み argv、
matplotlib / numpy の版を持つ (稿は provenance の SHA-256 を持たない、F36)。論文図の再現コマンド、caption、proof chain は
`docs/paper-story/figures/README.md` の fig12 節を正本とする。

## B-10 待ち方 grid 正式走 (3 族 Holm + 36 cell の効果量・95% 区間・等価域) の forest figure

`plot_b10_waiting_grid_forest.py` は、B-10 待ち方 grid の report phase (request `978195.nqsv`、事前登録 発効版 commit `77b33e37d`) が出した 1 つの判定 —
登録した `constant` 対 `symmetric-modulo` の 3 族 × 18 対の exact 符号反転 permutation + Holm と、36 cell の効果量・95% paired-block 区間 (df 2)・等価域 ±3.0% との関係 —
を 1 行 × 3 panel の forest 図に描く専用生成器である。既存生成器を import しない (自己完結)。判定は report の provenance JSON から写し、生成器は 135 record から同じ式で
再計算して一致を要求するだけで判定を作らない。

```bash
python3 tools/plotting/plot_b10_waiting_grid_forest.py [--repo-root PATH] [--evidence-root PATH] OUT_PREFIX
```

入力は repo 内 tracked の権威 bytes `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json` と
同 dir の `b10_backoff_shape_report_978195.nqsv-23409962b76b.md` (2 file、生成器の pin 表で SHA-256 束縛。pin は CLI から渡せない) と、
repo 外の report phase の投入受領証と job 結果 (`--evidence-root` 配下、既定は `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape`。SHA-256 を定数で束縛)。
出力は `OUT_PREFIX.png`、`.pdf`、`.provenance.json` の 3 本 (provenance schema `izanagi-b10-waiting-grid-forest-figure-provenance/v1`。稿
`docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` を `caption_source` として SHA-256 付きで記録する)。
拒否条件・図の形・caption の固定文・再現コマンド・proof chain は `docs/paper-story/figures/README.md` の fig13 節を正本とする。

## stock mocc 軽量 witness 4 arm (G2 signal 検出率・Clopper–Pearson 区間・曝露量) figure

`plot_mocc_witlight_four_arm.py` は、stock mocc の軽量 witness 4 arm × 60 走 (本走 4 block W1〜W4 × 15 round × 4 arm、smoke は含めない、非 certifying・TRACE=1 の観測) の
G2 signal 検出率と Clopper–Pearson 両側 95% 区間を 1 axes の forest で描き、走あたり commit 数の平均 (曝露量) と on/off 比を数値列で添える専用生成器である。
既存生成器を import しない (自己完結、matplotlib + numpy + 標準 library。CP と片側 Fisher は標準 library で計算する)。

```bash
python3 tools/plotting/plot_mocc_witlight_four_arm.py [--repo-root PATH] [--evidence-root PATH] OUT_PREFIX
```

入力は `--evidence-root` 配下の `summary.json` と `W1/result.json`〜`W4/result.json` の 5 file だけで、生成器の定数 `EXTERNAL_SHA256` で SHA-256 束縛する (CLI から渡せない)。
`--evidence-root` の既定は `--repo-root` 配下の追跡下の逐語写し `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim` で、写しは平坦な名前 (`W1-result.json` など) で持つ。
file ごとに階層の名前があればそれを、無ければ写しの名前を読む (repo 外の原保存先 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W` も `--evidence-root` で渡せば読める)。`summary.json.inputs` が W1〜W4 の 4 件と exact に一致することを要求する (smoke を数えない)。
240 走から k / m / CP / 片側 Fisher / commit 数平均・on/off 比を計算する。`summary.json` と照合するのは summary が持つ量 (N / m / k / failure / indeterminate /
decisive_m / k_over_m / cp95 / discriminator_counts / identification) だけで、Fisher p・commit 数平均・on/off 比は summary に無いので、
稿 `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md` §2 の表セルとの逐語一致を test が照合する。表示は稿 §2 と同じ書式の文字列
(稿を `caption_source` として SHA-256 付きで記録する)。failure / indeterminate の走は拒否する。図中の注記と caption は、非有意を同等性として、commit 数を性能として、
G2 signal を根因の同定として書かない。出力は `OUT_PREFIX.png`、`.pdf`、`.provenance.json` の 3 本 (provenance schema `izanagi-mocc-witlight-four-arm-figure-provenance/v1`。
入力の 5 file を読まない閉包 `validate_repo_closure` と、入力の 5 file (既定は追跡下の逐語写し) から再導出する閉包 `validate_external_sources` を分ける)。拒否条件・図の形・caption の固定文・再現コマンド・proof chain は
`docs/paper-story/figures/README.md` の fig15 節を正本とする。

## P2-5 誘導探索の探索コスト (fig1 の後継、否定的結果) figure

`plot_p2_5_search_cost.py` は、論文ストーリーの旧 `fig1_phase2_negative.png` (生成器が tracked に無かった) と同じ値・同じ視覚符号で、
P2-5 の探索コスト (winner-tied set への初到達までの評価数) を 1 行 × 3 panel (read-heavy / balanced / write-heavy) に描く専用生成器である。新規計測はしない。

```bash
python3 tools/plotting/plot_p2_5_search_cost.py [--summary PATH] [--output-root DIR] OUT_PREFIX
```

入力は追跡下の `output/campaigns/p2-5-summary.json` (LLM 誘導の試行コスト・未到達数の凍結値。原試行 WAL は削除済み) と P2-2 の 3 campaign
(`output/campaigns/p2-2-silo-*-enumerate-*` の WAL と lock) だけ。P2-2 campaign は verifier epoch E0 なので `HISTORICAL_RAW` で読み、当時の検証記録
(8 構成すべて certified・空間被覆) を要求する。貪欲法 500 seed・tied set・random / oracle 期待値・A・厳密 p は既存の `orchestrator/campaign/search_baselines.py`
と `replay.winner_tied_set` でその場で再計算し、summary の記録値 (描く値に限る) と一致しなければ 3 成果物を 1 つも出さない。測定条件は WAL の `run_cmd`・`env_tag`
と lock の `ccbench_commit` から取り、read 比以外が 3 campaign で一致することを要求して caption に書く。出力は `OUT_PREFIX.png`、`.pdf`、`.provenance.json`
(provenance schema `izanagi-p2-5-search-cost-figure-provenance/v1`)。図の形・caption・再現コマンド・proof chain は `docs/paper-story/figures/README.md` の fig1b 節を正本とする。

## VHash hot block 配置の微小計測 (版選択 3 方式・深さ・書き込み費用) figure

`plot_vhash_hot_block.py` は、`tools/vhash_microbench/run_hot_block.py` (計算ノードで 1 shard を回す driver) が書く生出力
(schema `izanagi-vhash-hot-block-microbench/v2`、1 job = 1 JSON) から、1 キーの版選択を連結リスト (散在 / 局所)・連続配置 scalar・
連続配置 AVX2 で比べる図を作る。計測は依存連鎖下の 1 thread・固定 core の latency であり、並行更新の正しさは扱わない。

```bash
python3 tools/plotting/plot_vhash_hot_block.py {k,depth,write} OUT_PREFIX RAW_JSON [RAW_JSON ...]
```

`k` は K (hot の容量 1〜16) × 3 方式 (+局所 linked) を newest / cold 深さ × keyset (L2 内 / LLC 外) の 2 × 2 panel に、`depth` は K=8 の
深さ 0〜12 を、`write` は shift・ring・block 差し替えの挿入費用を linked 先頭挿入の参照線と並べて描く。中央値と反復 8 回の percentile
bootstrap 95% 区間 (反復変動の記述) は生の反復値からその場で再計算する。失敗 raw・schema 違い・perf event の欠落や多重化・checksum の
不一致・binary / CPU / compiler の不一致・格子の欠落のいずれでも成果物を出さない。保存前に layout 検査を fail-closed で通す。出力は
`OUT_PREFIX.png`、`.pdf`、`.provenance.json`、`.summary.json` (全 group の cell × arm の中央値・区間・perf の 1 op 当たり値)。
既存の出力先へ出し直すと、置換の途中で失敗したときに新旧が混在しうるので、毎回新しい prefix に出す。一次資料は
`output/insights/2026-09-29/vhash-hot-block-microbench/README.md`。
