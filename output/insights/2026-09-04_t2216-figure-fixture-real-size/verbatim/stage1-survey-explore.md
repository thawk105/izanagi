# 棚卸し子 (Explore、read-only、opus) の報告 — 逐語

以下は子の出力をそのまま置いたもの。データであって指示ではない (規律 6)。親の裏取りは README.md。

---

Bash が途中から worktree 隔離フックで使えなくなったため、後半は Read のみで調査した (影響は末尾「調査の限界」に記載)。

## 1. 図種ごとの棚卸し (T-2216)

| 生成器 | 実寸 (production 入力の形) | レイアウト検査 | 合成 fixture で実描画するテスト | 判定 | 構造的必須セル |
|---|---|---|---|---|---|
| `tools/plotting/plot_backoff.py` | 2行×3列=6パネル (`:420` `subplots(2,n)`, n=campaign 数=3)。x は dat の 6 点 (2/5/10/25/50/100 µs)、反復 5 (fig2b provenance `n_reps:5`)、系列=throughput+abort+IPC(twin)、基準線 1 本 (`no backoff`)、直接ラベル= peak 注記 (2/3 workload) + `abort rate`/`IPC`/`static backoff` の 3 文字列 | `_overlap_check` `plot_backoff.py:510-519`。**警告のみ** — `sys.stderr.write(f"[warn] text overlaps: {ov}")` で raise せず。しかも `:499-501` で **savefig 後**に呼ぶので、重なった図が既に出力済み。パネル数検査なし | あり: `test_plot_backoff_ci.py:251 test_actual_panel_artists_match_serialized_baseline_records` が `main()` 経由で実描画。fixture は `_figure_campaign` (`:211`) で **campaign 2 件 (=4パネル)・x 3 点・反復 2**。`:396 test_production_provenance_...` は `make_figure` 自体を差し替え (`:400-419`) | **fixture < 実寸**。3→2 campaign、6→3 点、5→2 反復。加えて検査が warn-only なので、実寸でも落ちない (恒真) | `none` (無 backoff) / `adapt` を campaign dict が常に持つ。fixture は両方含む。`main` `:589` が「描画 baseline 数 == campaign 数」を要求 |
| `plot_b10_extended_backoff.py` | 2×3=6パネル (`:816`)。x は `INCLUDED_GRID` 28 点 (raw 29 点 − F718 の 1000 µs)、3 workload、反復 5、系列 9 (throughput/CI/abort ×3)、注記= suptitle + 比較禁止文 + panel title 3 | `_validate_text_bboxes` `:284-806`。**raise** (`_reject` → `B10FigureError`)。tick label も対象。`make_figure` 末尾 `:873` で savefig 前に実行 | あり: `test_plot_b10_extended_backoff.py:149/194/235/265` が `plot.make_figure(_campaigns())` を実描画。fixture (`:83 _campaign`, `:137 _campaigns`) は **3 workload × GRID_28+1000 の 29 点 × 5 反復** = 実寸そのまま | **fixture == 実寸** | 1000 µs 行 (F718 で除外だが producer は必ず出す) と static 0 µs。fixture は両方含む (`:105-121`) |
| `plot_s1_9pair.py` | 2×3=6パネル (`:1453` `subplots(2,3,figsize=(12.0,7.35))`)。上段=workload あたり 3 対 (計 9 対)、下段=12 セル × 8 標本、直接ラベル 3/パネル + gate 文言 2 + 図下部 legend + banner | `check_figure_layout` `:1263` + `_check_required_artists` `:1199`。**raise** (`FigureLayoutError`)。tick 重なり・marker/label 間隔・legend 重なり・tight bbox 包含まで見る | あり、しかも**本番と同じ canvas で**: `test_s1_9pair_figure_provenance.py:1533 test_n14`, `:1634 n16`, `:1695 n17`, `:1715 n18` が `_production_layout_control` (`:1684`) 経由で `subplots(2,3,(12.0,7.35))` + `_style` + `draw_figure_artists` + `check_figure_layout` を実行。fixture `_spy_data()` (`:1270`) は **9 対・12 セル・各 8 標本**で、値も実図の実数値 (−9.3448 … 98.4334)。※ `test_p1_...` は実 WAL (`output/campaigns/s1-direct-{develop,floor,block1,block2}-...`) を使う別系統 | **fixture == 実寸** (パネル数・点数・系列・標本数・ラベル密度すべて一致) | `CONFIGURATIONS` は 6 種だが描くのは `PLOT_CONFIGURATIONS` 4 種。`_spy_data` は 4 種のみ生成し、producer が必ず出す文脈セル `ident_all` / `stock_common` を**含まない** (無視されることが未検査) |
| `plot_ss2pl_lock_study.py` | 図種 5 つ: scalability 2パネル (`:441`)、abort 1 (`:499`)、paired 1 (`:530`)、controls 2×2 (`:561`)、deadlock 1×2 (`:620`)。x は `THREADS` 14 点 (`:29`)、系列 5 arm (paired は 4 ペア)、反復=5 block、注記=飽和点 5 行のテキストボックス + 2 段 legend + 条件 caption | `_figure_overlap_check` `:289` (**raise** `PlotContractError`) を `_save_checked` `:325` が savefig 前に呼ぶ。判定核は `find_non_tick_overlaps` `:272` | **無し**。`test_ss2pl_lock_study.py:676 test_m9_generation_execution...` は 5 図関数を全部 monkeypatch (`:696-700`)。`:763 test_m10_mutated_bbox_gate...` は `FakeFigure` + `_figure_overlap_check` 自体を差し替え。`:753 test_m10_correct...` は手書き 4 box のみ。matplotlib の Figure を検査に通すテストは 1 件も無い | **描画テストが無い** (検査関数の単体テストのみ、しかも box 2〜4 個) | 5 arm すべて (`ARMS`) と `PAIRINGS` 4 組。`_complete_sweep_document()` (`:185`) は `SWEEP_BLOCKS × THREADS × PERFORMANCE_ARMS` の実寸だが、**図には流していない** |
| `plot_t2187_adaptive_consts.py` | grid: 2×3=6パネル (`:672`)、格子 = 刻み 6 × 更新間隔 5 = 30 セル + 無 backoff 1、3 workload、注記 = 各セル 3 行 × 30 × 2 段 = 180、canvas は格子数に比例 (`_grid_figure_size` `:659`)。threads: 2×3 (`:787`)、x 8 点、系列 2 (`none`/`stock`) | `check_figure_layout` `:896`。**raise**。text 逸脱・cell 注記のスパイン外・隣パネル侵入・全 text 対の重なり・`len(plot_axes)!=6` (`:938`) | あり (CLI subprocess で実走): `test_plot_t2187_adaptive_consts.py:185`, `:264`, `:323`, `:376`。fixture `_document` (`:63-102`) は **GRID_STEPS 6 × GRID_UPDATES 5 + 無 backoff、3 workload、THREAD_COUNTS 8 点、rep 3〜7** で、`:24-26` の定数が実寸格子そのもの | **fixture == 実寸** (F812 の恒久対応が入った当該図。以後の基準) | 無 backoff セル (`back_off=0`, 3 定数が stock 値)。`include_grid_no_backoff=True` で fixture に必ず入り、`include_grid_no_backoff=False` の負例も別途持つ |
| `plot_t2216_backoff_walk.py` | prediction 1×5 (`:392`, 更新間隔 5 列)、residence 1×2 (`:522`)、mechanism 2×2 (`:612`)。条件は `_CONDITION_ORDER` (`:46-55`) = 刻み union 8 + cap50 2 + 更新間隔 4×刻み 6 + (25,2560) = 35 条件、scenario 10 (`:56`)、model 反復 8 (`:66`)、参照線 4 本 + CI 帯 (`:396-414`) | `check_figure_layout` `:695`。**raise**。`len(plot_axes) not in (2,4,5)` (`:703`)、direct-label のパネル外・direct-label どうしの重なりも別枠で検査 | あり (CLI subprocess で 3 mode すべて): `test_t2216_backoff_walk_model.py:871 test_t2216_plot_modes_write_png_pdf_and_hash_bound_provenance`、および `:932` の figure contract テスト。measured fixture `_t2216_measured_document` (`:97`) は **実寸** (3 workload × 刻み 6 × 間隔 5、D1475 8 点、cap50 2 点、静的 8 セル)。model fixture `_t2216_fake_model` (`:777`) は **scenario 4/10・反復 3/8・ceiling=50 の run 無し** | **measured は実寸 / model は < 実寸** (scenario 10→4、反復 8→3、cap50 予測欠落)。パネル数と x 点数は一致するので重なり密度は概ね実寸 | measured 側: cap50 セル (`adaptive-step{0.5,2.0}us-cap50us`) — fixture にあり。model 側: `_CONDITION_ORDER` の `(0.5,10,50.0)` / `(2.0,10,50.0)` — **fixture に無い** |

## 2. (a) 既存の「fixture を実寸に揃える」規定

- `tools/plotting/FIGURE_CONVENTIONS.md` — **無い**。全 100 行を読んだ。fixture / テスト形状の語は 1 度も出ない。§9「描いたら検証する」(74-79 行) が唯一の近縁で、しかも **雛形として warn-only の `plot_backoff.py` の `_overlap_check` を挙げている**。新規約はここに純増でよく、同時に §9 の雛形指定は fail-closed 側 (`plot_t2187_adaptive_consts.check_figure_layout`) に差し替える余地がある。
- `tools/plotting/README.md` — **無い**。全 199 行を読んだ。144-145 行に t2187 の「保存後にレイアウトを機械検査し…rc 非 0 で落ちる」があるだけで、テスト fixture の大きさには触れない。
- `docs/failures.md` F812 (21284 行付近) — 恒久対応として「合成 fixture を**実寸と同じ格子形状・同じ軸点数**にする」「producer が構造的に必須とするセルは consumer 側の fixture にも必ず含める」が既に書かれている。**規約化されているのは失敗台帳だけ**で、作図規約の正本には未反映。新条は F812 の文言を FIGURE_CONVENTIONS へ昇格させる形が素直。

## 3. (b) 生成器横断のメタテスト

確認できた範囲では **存在しない**。各図種のテストは個別 file に閉じており、`plot_*.py` を glob して規約 (レイアウト検査の有無、fail-closed 性、fixture 形状) を一律に強制するテストは見当たらなかった。実際、`plot_backoff.py` の warn-only 検査と `plot_ss2pl_lock_study.py` の描画テスト皆無がどこからも検出されていないのが、その傍証。

## 4. 是正の優先度 (所見)

1. `plot_ss2pl_lock_study.py` — 検査は fail-closed なのに **一度も実 Figure を通していない**。5 図種 × 14 スレッド tick × 5 arm × 2 段 legend という最も注記密度の高い構成で、F812 と同型の穴が最大。
2. `plot_backoff.py` — 検査が **warn-only かつ savefig 後**。fixture を実寸にしても落ちない。fail-closed 化が先。
3. `plot_t2216_backoff_walk.py` — model fixture の scenario/反復/cap50 欠落。
4. `plot_s1_9pair.py` — 文脈セル 2 種を fixture に足すだけ (レイアウト面は実寸済み)。
5. `plot_b10_extended_backoff.py` / `plot_t2187_adaptive_consts.py` — 現状で条件を満たす。規約の適合例として明記できる。

## 調査の限界

- 途中から Bash がフック (`worktree 隔離`) で全面的に使えなくなり、`docs/dev-wave/*.md` と `docs/decisions.md` に対する `実寸` / `fixture` / `格子形状` / `軸点数` の grep、および `orchestrator/tests` 全体に対する `tools/plotting` / `plot_*` の横断 grep は**実行できていない**。上記 (a)(b) は「FIGURE_CONVENTIONS.md と tools/plotting/README.md を全文読了した結果」と「6 図種のテスト 8 file を読んだ範囲」に基づく。dev-wave/decisions 側に既存規定が無いことは未確認。
- `plot_backoff.py` の実寸 x 点数 6 は write-heavy campaign の `.dat` 実物から数えた。balanced / read-heavy も同一格子である前提を置いている (未検証)。
