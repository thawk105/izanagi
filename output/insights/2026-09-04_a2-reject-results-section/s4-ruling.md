# 段 4 裁定 — A-2 reject の結果節化 (2026-09-04、親 = Claude)

入力: 段 2 plan (`verbatim/s2-plan.md`)、段 3 レンズ A (`verbatim/s3-lens-a.md`、10 件)、レンズ B (`verbatim/s3-lens-b.md`、10 件)。
裁定 inbox の再走査: main は `df8b9d1e7` → `1b7822110` へ進んだ (rulings 第 7 回 D1616〜D1622)。A-2 / paper-story / 作図に触れる新裁定は無し。

## 1. plan の brief 訂正 7 件 — 全件 real、採用

fixture の stage 総数は全体で 2 倍 (workload 当たり `build_start=2, build_done=2, verify_done=12, bench_done=2, commit=2`)。
`bench_done` は cell 当たり 1 行で `payload.tps` に 5 標本。raw JSON に `workload` / `role` は無く、`cell_id` / `variant` / `build_attempt_id` で対応付け、
workload と role は certification から読む。raw-manifest は 10 entry で消費するのは 6 本。certification hash の独立 pin。abort 下段は共通 0〜1 軸。
results 系列規則は README で正本化 (下記 B9 / A9 と併せて {{D}} fragment に記録)。

## 2. レンズ B (論文の読み違い) — 10/10 real

| # | 裁定 | 採否と実装 |
|---|---|---|
| B1 旧値の先置きが comparator を作る | real | **採用。** 結果節を「A-2 の性能」「別走行の correctness」「旧系列との関係 (禁止推論)」の順に組み替え、旧値の数値 (+38.3% / +11.3%) を本文・図から外し、2026-09-02 版 §8 の exact claim への参照だけ残す |
| B2 「現行 Pegasus」への一般化 | real | **採用。** 主張を attempt `t2022-20260828c` の 2 本の独立 campaign (request / host / 時刻) に束縛し、caption に D1169 の論理積を書く |
| B3 T-2228 未完了で「再解釈不要」を断定 | real (部分) | **採用 (部分)。** `.status = reject` は当時の protocol 出力として不変。brief の断定を「意味関門の証拠範囲は本走行について未確立 (T-2228 の結果待ち)。後日の緑は本走行を遡及的に認証しない。逆の結果が出れば新しい日付の results file で改める」へ弱める。**T-2228 の結果を本 wave の必須入力にはしない** (command は起動時確認を求め、待機を求めていない。append-only 系列で訂正可能) |
| B4 限定が本文へ未配置 | real | **採用。** register とは別に artifact 別配置を実文で入れる (correctness 段と表脚注: D1257・legacy 1 回・L01。効果の直後: noise floor open・minimality false・有意差なし。A-2 条件段と caption: D1198 未適用・D1169。§0: D1263) |
| B5 correctness の染み出し (図・表) | real | **採用。** 図の figure-level text を 1 文に統合「correctness: separate trace-enabled runs, all 4 cells certified — not a performance certification」。表の欄名を「correctness の証拠 (別の trace-enabled run)」にし脚注に L01 / D1257 |
| B6 mean-CI と median 判定の但し書き | real | **採用。** caption に「菱形と誤差棒は標本平均の記述。効果・判定・median の信頼区間ではない。成果物に有意差判定は無い。`reject` は事前定義の median 比による protocol status」を入れる |
| B7 abort 下段の機序主張 | real | **採用。** 本文から over-throttling を外す。下段は「descriptive leading indicator、cell 当たり集約 1 点、因果機序を同定しない」と図中注記と caption に書く |
| B8 D12 材料レポートの呼称 | real | **採用。** results 文書は「一次資料に束縛した執筆者向け統制稿」と再分類。README の列名を `protocol status` に。表の数値は provenance JSON の `cells` から転記し、その provenance の SHA-256 を本文に書く (A1 も参照) |
| B9 stale 注記の却下は根拠が弱い | real | **採用。** README の「最新スナップショット以後に確定したこと」へ 1 件追加: 2026-09-02 版の A-2 は D1198 関門族 (09-01 義務化) が本走行に未適用であることを述べない |
| B10 生成器の過剰 hardening | real | **採用。** 必須に絞る: 6 外部入力の hash 照合、tracked 2 authority の canonical hash 照合、生値再計算、certification との相互検算、status のコピー、caption / provenance、実寸 Figure と保存前 layout check、file 単位の temp→replace。一般 path containment、TOCTOU 再 hash、duplicate-key 拒否、3 file commit protocol は落とす。目安: 生成器 ≤ 550 行、テスト ≤ 450 行 |

## 3. レンズ A (数値・provenance・検査) — 10/10 real

| # | 裁定 | 採否と実装 |
|---|---|---|
| A1 結果表が機械照合されない | real (部分採用) | 表外の平均比の数値を削除。表は provenance `cells` からの転記と明記し provenance SHA-256 を書く。**Markdown 表を parse する専用 test は不採用** (本題外の検査新設。DW-G05: 放置時に変わるのは docs の転記精度であり、転記は親が provenance と突き合わせて 1 回検算する。裁定パッケージ候補として記録) |
| A2 D1074 の証拠鎖 | real | **採用。** 生成器の canonical certification hash literal は run README (`2026-08-28_t2022-a2-certification-run/README.md`) が記録した値と一致することをテストが機械照合する。現行 bytes をその場で hash した値を信頼根にしない |
| A3 tracked hash gate の負例・変異なし | real | **採用。** certification / raw-manifest の whitespace 変更 copy で CLI が非 0・成果物ゼロになる負例 2 件。変異 M11 / M12 を登録 |
| A4 generator hash の live pin 化 | real | **採用。** landed test は生成時 golden (provenance に記録された値) だけを照合し、現行 source との一致を要求しない。README にも同旨 |
| A5 durable root 部分欠落 | real | **採用。** root 不在だけ skip、root 存在で 6 file の欠落・hash 不一致は failure の専用 helper |
| A6 偽 field の fixture | real | **採用。** 全 stage の key set を実 WAL と同一にする。無視の sentinel は `commit.payload.fitness_tps` (bench median と異なる値) と `verify_done.payload.aborts` |
| A7 変異の単一理由性 | real | **採用。** 一置換一変異へ分割、status 固定は diagnostic 枠、probe を全件 SURVIVED 期待で走らせ観測 node を本登録 (下記 §5) |
| A8 `source_commit` の二義 | real | **採用。** provenance は `izanagi_source_commit` (certification `source_commit`) と `ccbench_pin` (certification `current_pin`) に分け、raw `build_evidence.source_commit == current_pin` を照合 |
| A9 results 系列は未裁定の一般化 | real | **採用 (案 A、AI 裁定として記録)。** 系列の対象・append-only・再導出単位・版履歴非登録・数値出所を `{{D:paper-story-results-series}}` fragment で記録する。D1013 と同じ AI 側の設計判断であり、可逆 (directory 1 つ) なのでユーザー裁定待ちで止めない。数値 block の機械生成は上記 A1 の範囲 |
| A10 brief の一般化に証拠がない | real | **採用。** 本 insight に query と hit を残す (§6)。「pin 閉包ゼロ」は「FROZEN_MANIFEST 非包含 + `git grep` の path hit は既存 fig の test だけ」に狭める。T-2228 稼働は `git worktree list` の locked worktree と `dev-wave-jobs/dev-wave-t2228-a2-gate-layers/submit-tree` の存在で示す |

## 4. プラン v2 (段 5 へ渡す確定形)

実装単位 (Codex author、1 本): `tools/plotting/plot_a2_certification.py`、`orchestrator/tests/test_plot_a2_certification.py`、`tools/plotting/README.md` の A-2 節。

- CLI: `plot_a2_certification.py [--measurement-root PATH] [--certification PATH] [--raw-manifest PATH] OUT_PREFIX`。
  env `IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT`、既定 root は durable authority。
- 入力: certification.json と raw-manifest.json は canonical SHA-256 literal と照合 (受理はこの 2 bytes だけ。合成 fixture 用の期待 hash 注入は Python API のみ)。
  外部 6 file (WAL 2 + raw 4) は root-relative path で開き raw-manifest `files` の SHA-256 と照合。WAL は `stage == "bench_done"` だけを測定値として読む。
- 検算: computed median == WAL `payload.median_tps` == certification `median_tps`、computed cv ≈ WAL `cv`、WAL samples == raw `samples_tps`、
  build_attempt_id / variant / genome の一致、raw `build_evidence.source_commit == certification current_pin`、
  computed `adopted/stock − 1` ≈ certification `effects` (abs_tol 1e-12)。不一致は fail-closed。
- 統計: median、mean、stdev、CI 半幅 = `_T975[4] · s / √5` (固定表)、cv。n != 5 は拒否。abort rate は `leading_indicators.abort_rate` の 1 点。
- 判定: `outer_status` と `effects` は certification からコピー。生成器は判定を作らない。
- 図: 2 列 (rr5 write-heavy / rr50 balanced) × 2 行。上段: 5 標本の点、標本平均の菱形 + t 分布 95% CI、各 arm の median 短線、
  no-backoff median の灰色破線 (分母)、効果の直接ラベル、y は 0 始まりで workload 独立。下段: abort rate 1 点、共通 0〜1 軸、
  注記「descriptive; 1 aggregate per cell; no CI; no causal claim」。figure-level text: `outer status: reject (protocol status, median ratio)`、
  `correctness: separate trace-enabled runs, all 4 cells certified — not a performance certification`。緑を使わない。
- layout check: `check_figure_layout` 同型、保存前、axis 4 面、text 重なり・逸脱で `FigureLayoutError`。出力は file 単位 temp→`os.replace`、provenance を最後に。
- provenance (`izanagi-a2-certification-figure-provenance/v1`): generator (path, sha256 = 生成時記録)、outputs、tracked_inputs、external_source_locator、
  external_inputs (6 本)、measurement_conditions (attempt、protocol sha、`izanagi_source_commit`、`ccbench_pin`、workload 条件、toolchain、host/request/campaign)、
  cells、artist_series (label↔値↔genome)、outer_status、effects、effect_crosschecks、correctness (status、反復数、argv observation limit)、
  correctness_performance_note、gate_note (D1198 未適用の固定文)、caption、reproduction (展開済み argv)。
- caption (`_caption(data)` が決定的に組み立て): 構成 (attempt、2 independent campaigns、request/host/別時刻、outer = 論理積)、上段の読み方 (標本、median、平均 + CI、
  破線 = no-backoff median = 分母)、効果 2 値、「平均 CI は効果・判定・median の CI ではない。成果物に有意差判定は無い。reject は median 比の protocol status」、
  下段は descriptive 1 点で機序を同定しない、correctness は別 run で 4 cell certified だが性能の判定ではない (L01: point-key trace の射程、D1257: argv 独立記録なし)、
  D1198 関門族は本走行に未適用、条件 (48 thread、1M records、Zipf 0.9、rmw 無効、max_ope 10、3 s、5 反復、pin 511c953、perf 無し、trace-disabled)、
  上段の縦軸は workload 独立、旧系列は comparator ではなく符号差の原因は未同定。
- テスト: 実寸 fixture (2 workload × 2 arm × 5 標本 + abort 1 点 + 実 WAL と同じ stage/key set、10-entry manifest)、本物の Figure を layout check へ通す 1 本、
  負例 (median 不一致、effect 不一致、外部 sha 不一致、tracked 2 authority の whitespace 変更で CLI 非 0 + 成果物ゼロ、n=4、bench_done 以外を使わない、
  status のコピー、caption 必須句、layout 失敗で出力ゼロ、source_commit 不一致)、canonical hash literal == run README の記録値、
  landed fig5 の closure (root 不在 skip / 部分欠落 failure)。所要は数十秒以内。

親 docs 単位: `docs/paper-story/results/2026-09-04-a2-certification-reject.md` (組み替え)、`docs/paper-story/README.md` (results 系列節 + stale 注記 1 件)、
`docs/paper-story/figures/README.md` (fig5 行・節・caption byte copy・再現コマンド)、fig5 三成果物 (親が login node で生成)、fragment (worklog 1、decisions 1)、insight。

## 5. 変異の事前登録 (DW-M01。anchor は実装後に DW-M07 で再検証。probe は全件 SURVIVED 期待で走らせ観測 node を本登録)

| # | 位置 (関数) | 変異 (一置換) | 期待方向 | 単一理由性の担保 |
|---|---|---|---|---|
| M1 | `_bench_done_rows` | stage 述語を外す (全行を測定値として読む) | KILLED | 非 bench 行に `tps` が無いことで loader が赤。fixture は実 key set |
| M2 | `_summarize_samples` | `n != 5` の拒否を外す | KILLED | 負例 fixture は raw / cert / manifest すべてを 4 標本で整合させ、標本数だけが不正 |
| M3 | `_load_external_inputs` | 外部 6 file の SHA-256 照合を外す | KILLED | 負例は 1 file の bytes だけ変更、manifest は元のまま |
| M4a | `_validate_raw_cell` | WAL samples == raw samples の照合を外す | KILLED | 負例は raw samples を変え manifest hash も追随 (hash gate は通る) |
| M4b | `_validate_raw_cell` | build_attempt_id / variant の対応照合を外す | KILLED | 負例は raw の build_attempt_id だけ入替、manifest hash 追随 |
| M5 | `_crosscheck_certification` | median 照合を外す | KILLED | 負例は certification median だけ変更 (API 経由で期待 hash 注入) |
| M6 | `_crosscheck_certification` | effects 照合を外す | KILLED | 負例は certification effect だけ変更 |
| M7 | `build_provenance` | `outer_status` を `"reject"` 定数にする | **diagnostic sensitivity pin** (kill に数えない) | canonical 入力では等価。sentinel status の propagation test だけが反応 |
| M8 | `_artist_series` | 基準線の値を stock median でなく adopted median から取る | KILLED | artist↔provenance 対応 1 件だけ不一致 |
| M9 | `_caption` | correctness / performance 区別文を落とす | KILLED | caption 必須句 test だけ |
| M10 | `_publish_outputs` | layout check の例外を握り潰す | KILLED | layout 失敗 fixture で出力ゼロを期待する test |
| M11 | `_load_tracked_authority` | certification canonical hash 照合を外す | KILLED | whitespace 変更 copy の CLI 負例 |
| M12 | `_load_tracked_authority` | raw-manifest canonical hash 照合を外す | KILLED | 同上 (raw-manifest 側) |
| M13 | `_validate_raw_cell` | `build_evidence.source_commit == current_pin` の照合を外す | KILLED | 負例は raw の source_commit だけ変更、manifest hash 追随 |

KILLED 期待 12 + diagnostic 1。冗長 gate で mask された変異は DW-M03 に従い単独証拠から外し erratum に残す。

## 6. brief の一般化の証拠 (A10)

- `FROZEN_MANIFEST`: `orchestrator/tests/test_frozen_artifacts.py` の 23 件に `docs/paper-story/figures/*` と `output/insights/2026-08-2[48]_*a2*` は無い (親が list を読んだ)。
- `git grep -n "paper-story/figures" -- orchestrator tools hooks` の hit は `test_plot_b10_extended_backoff.py:32`、`test_s1_9pair_figure_provenance.py:44`、`tools/plotting/README.md:120` の 3 件で、いずれも既存 fig の test / README。fig5 の path を pin するものは無い。
- `grep -rln f685b40d orchestrator/tests tools docs` = 0 件 (certification.json の bytes を pin する test は無い。run README の記録だけ)。
- 稼働 wave: `git worktree list` (2026-09-04 21:2x JST) の locked worktree は t1851-unit-a / t2107 / t2153 / t2202 / t2228 / t2253 / t2262 / t822 / rulings-all。
  `git diff --stat main...<branch> -- docs/paper-story tools/plotting docs/spool` は t2228 / t2266 / t2202 / t2189 / t2262 で空、`git -C <wt> status --short` も t2228 / t2202 / t2266 で空。
  T-2228 の稼働: `worktree-dev-wave-t2228-a2-gate-layers` (locked) と `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-a2-gate-layers/submit-tree` (detached) の実在。
- これらは 2026-09-04 21:2x JST 時点の snapshot であり、段 5 投入前に main を再読する。

## 7. 裁定パッケージ候補 (本 wave では実装しない)

- results 文書の表を parse して provenance / certification と機械照合する test (A1)。採るなら generator が表の Markdown を吐く形が先。
- 生成器の一般 hardening (path containment、TOCTOU 再 hash、3 file commit protocol) (B10)。
- T-2228 の結果が A-2 経路の意味関門に赤を出した場合の results 系列の改訂手順 (B3)。
