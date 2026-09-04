# [T-2216] 作図の検査用 fixture と実寸の棚卸し — 一次資料

wave `dev-wave-t2216-figure-fixture-real-size`、branch `worktree-dev-wave-t2216-figure-fixture-real-size`。
base commit `764fdf202`。2026-09-04。裁定は D1546 (2026-09-03 ユーザー裁定)、起点の事故は F812。

`verbatim/` に段 1 brief、read-only 子の棚卸し報告、段 4 裁定を逐語で置く。
本 wave は docs-only (実装面の差分 0)。規約は `tools/plotting/FIGURE_CONVENTIONS.md` §10 へ入れた。
以下の表は **2026-09-04 時点の snapshot** であり、規約書へは再掲しない。

## 何を数えたか

「実寸」= production 入力が生む形。パネル数、格子形状、軸の点数、系列数、反復数、注記密度。
値の実数一致は求めない (値は provenance が束縛する)。出所は生成器の定数、production の
dat / probe JSON の実物、既存図の provenance。

## 棚卸し (6 図種)

| 生成器 | 実寸 | レイアウト検査 | 実 Figure を通す test と fixture の形 | 判定 |
|---|---|---|---|---|
| `plot_backoff.py` | 2 行 × campaign 数 (論文図は 3) = 6 パネル。x 6 点 (2/5/10/25/50/100 µs、dat 実物)。反復 5 (fig2b provenance)。基準線 1 本、peak 注記 | `_overlap_check` (510-519 行)。**保存後に stderr へ警告するだけ**で raise しない | `test_plot_backoff_ci.py::test_actual_panel_artists_match_serialized_baseline_records` が `main()` で実描画。fixture `_figure_campaign` は **campaign 2 件・x 3 点・反復 2** | **fixture < 実寸** (3→2 campaign、6→3 点、5→2 反復)。加えて検査が警告どまりなので実寸でも落ちない |
| `plot_b10_extended_backoff.py` | 2 × 3 = 6 パネル。x 28 点 (raw 29 − F718 の 1000 µs)。3 workload、反復 5 | `_validate_text_bboxes` (784-806 行)。raise。tick label も対象。保存前 | `test_plot_b10_extended_backoff.py` の 4 test が `make_figure(_campaigns())` を実描画。fixture は **3 workload × 29 点 × 5 反復**、除外前の 1000 µs 行と static 0 µs を含む | **fixture == 実寸** |
| `plot_s1_9pair.py` | 2 × 3 = 6 パネル。上段 9 対、下段 12 セル × 8 標本、直接ラベル 3/パネル + gate 文言 + 図下 legend | `check_figure_layout` (1263 行) + `_check_required_artists`。raise。tick・legend・tight bbox まで | `test_s1_9pair_figure_provenance.py` の n14/n16/n17/n18 が本番と同じ canvas (2×3、12.0×7.35) で `draw_figure_artists` + `check_figure_layout` を実行。fixture `_spy_data` は **9 対・12 セル・各 8 標本**、値も実図の実数 | **レイアウト面は fixture == 実寸**。ただし producer が必ず出す文脈セル `ident_all` / `stock_common` (`CONFIGURATIONS` 6 種のうち `PLOT_CONFIGURATIONS` 外の 2 種) を fixture が持たず、無視経路が未検査 |
| `plot_ss2pl_lock_study.py` | 5 図種 (scalability 2 パネル、abort 1、paired 1、controls 2×2、deadlock 1×2)。x = `THREADS` 14 点、5 arm、反復 5 block、飽和点テキストボックス 5 行 + 2 段 legend | `_figure_overlap_check` (289 行)。raise。`_save_checked` が保存前に呼ぶ | **無し**。`test_m9_generation_execution...` は 5 図関数を全部 monkeypatch。`test_m10_*` は手書き bbox 2〜4 個か `FakeFigure` で検査関数だけを試す | **実 Figure を通す test が無い**。実寸 fixture (`_complete_sweep_document`) は存在するが図へ流していない |
| `plot_t2187_adaptive_consts.py` | grid: 2 × 3、刻み 6 × 更新間隔 5 = 30 セル + 無 backoff、注記 3 行 × 30 × 2 段。threads: 2 × 3、x 8 点、系列 2 | `check_figure_layout` (896 行)。raise。パネル数 6 も検査 | `test_plot_t2187_adaptive_consts.py` の 4 test が CLI subprocess で実走。fixture `_document` は **GRID_STEPS 6 × GRID_UPDATES 5 + 無 backoff、3 workload、THREAD_COUNTS 8 点、rep 3〜7**、定数から組み立て | **fixture == 実寸** (F812 の恒久対応そのもの) |
| `plot_t2216_backoff_walk.py` | prediction 1 × 5、residence 1 × 2、mechanism 2 × 2。条件 35 (`_CONDITION_ORDER`)、scenario 10、model 反復 8、参照線 4 本 + CI 帯 | `check_figure_layout` (695 行)。raise。パネル数 (2, 4, 5) と direct-label も検査 | `test_t2216_backoff_walk_model.py` の plot test 2 本が CLI subprocess で 3 mode を実走。measured fixture は**実寸** (3 workload × 6 × 5、D1475 8 点、cap50 2 点)。model fixture `_t2216_fake_model` は **scenario 4/10、反復 3/8、cap50 (`(0.5,10,50)` / `(2.0,10,50)`) の run 無し** | **measured は実寸、model は < 実寸**。パネル数・x 点数は一致するので重なり密度はほぼ実寸 |

## 親の裏取り

子 (Explore、read-only) の報告のうち、次を親が source で確かめた。

- `plot_backoff.py` 494-501 行: `savefig` 2 回の**後**に `_overlap_check(fig)`。510-519 行は `sys.stderr.write("[warn] ...")` のみ。
- `test_plot_backoff_ci.py` 211-249 行: `_figure_campaign` の `pts` は 3 点、各 2 反復、`none` / `adapt` も 2 反復。
- read-heavy / balanced の dat 実物: 非コメント行 6 点 (2/5/10/25/50/100)。
- `test_ss2pl_lock_study.py` 696-700 行: 5 図関数を `lambda _document, _prefix: {"fixture": True}` で差し替え。
- `plot_s1_9pair.py` 51-67 行: `CONFIGURATIONS` 6 種、`PLOT_CONFIGURATIONS` は `ident_all` / `stock_common` を除く 4 種。
- `tools/t2216_backoff_walk_model.py` 172-186 行: Scenario 10 種 (`M_exact` … `M_fano4`)、`REPETITIONS = 8`。`_t2216_fake_model` は `M_exact` / `M_no_trunc` / `M_flat_tail` / `M_linear_zero` の 4 種のみ。
- 既存規定の不在: `FIGURE_CONVENTIONS.md`・`tools/plotting/README.md`・`docs/dev-wave/`・`docs/roadmap.md`・`docs/phase3.md` に「実寸 / 格子形状 / 軸点数」の規定なし (D1546 本文を除く)。恒久対応文言は F812 だけが持っていた。
- 生成器横断の meta test は無い。`orchestrator/tests` で `tools/plotting` を参照する 10 file はすべて図種別。

## 判定

- 実在の欠陥 (実データで落ちる) は今回 **0 件**。全 6 図種の実図は既に生成済みで、fail-closed 検査を持つ 5 種はそれを通っている。
- 被覆漏れは 4 件。いずれも「テストが緑でも実寸で初めて出る欠陥を通しうる」型で、F812 と同型。優先度は P3 (受理集合・certified 選択・レポートの値は変わらない、DW-G05)。
  1. `plot_backoff.py`: 検査が警告どまり + 保存後、fixture が実寸の半分以下。
  2. `plot_ss2pl_lock_study.py`: 実 Figure を検査へ通す test が無い (注記密度は 6 図種で最大)。
  3. `plot_t2216_backoff_walk.py`: model fixture の scenario / 反復 / cap50 欠落。
  4. `plot_s1_9pair.py`: 文脈セル 2 種が fixture に無い。
- 規約書 §9 が warn-only の `_overlap_check` を雛形に挙げていたのは、穴を雛形として伝播させる記述だった。§9 を fail-closed 側 (`plot_t2187_adaptive_consts.check_figure_layout`) へ正した。

## 本 wave でやらなかったこと

- 上記 4 件の test / generator の修正。実装面は Codex `role=author` (D95) が要り、command 引数の scope (棚卸しと規約追記だけ) の外。次の一手に 1 件ずつ登録した。
- 生成器横断の meta test の新設。仮想リスク向けの検査追加は scope 外 (command 引数、DW-G05)。

## 限界

- 子の調査は途中から Bash が使えず Read のみで進んだ。横断 grep は親が代行した。
- `plot_backoff.py` の実寸 x 6 点は read-heavy と balanced の dat で確認した。write-heavy は同格子と仮定 (fig2b の 3 campaign は同じ sweep 設定)。
- 図の数値・認証状態には触れていない。本 insight は test 被覆の棚卸しであり、性能主張の根拠ではない。
