---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2216-figure-fixture-real-size
seq: 1
title: [T-2216] 作図の 6 図種を棚卸しし、検査用 fixture を実寸へ揃える規約を作図規約書へ足した — 実在の欠陥 0 件、被覆漏れ 4 件は次の一手へ (docs のみ、branch worktree-dev-wave-t2216-figure-fixture-real-size、実装面の差分 0)
---

## 本文

- D1546 (2026-09-03 ユーザー裁定) に従い、`tools/plotting/` の 6 図種について「production 入力が生む形」と
  「単体テストの合成 fixture の形」を突き合わせた。一次資料は
  `output/insights/2026-09-04_t2216-figure-fixture-real-size/` (棚卸し表・親の裏取り・逐語)。
- 規約は `tools/plotting/FIGURE_CONVENTIONS.md` §10 として純増した。合わせて §9 の雛形指定を訂正した —
  以前は保存後に警告を出すだけの `plot_backoff.py` の検査を雛形に挙げており、穴を雛形として伝播させる
  記述だった。fail-closed 側 (`plot_t2187_adaptive_consts.py`) へ差し替えた。
- 棚卸しの結果: fixture が実寸なのは b10 拡張と t2187 の 2 種。s1_9pair はレイアウト面で実寸。
  被覆漏れは 4 件で、いずれも F812 と同型 (テストが緑でも実寸で初めて出る欠陥を通しうる)。
  実データで落ちる欠陥は 0 件 — 全 6 図種の実図は生成済みで、fail-closed 検査を持つ 5 種はそれを通っている。
- 軽量版・docs-only・子ゼロ (段 2・3・6 の codex 子を省略)。棚卸しは read-only の Explore 子 1 本で行い、
  要所 (検査の位置と種別、fixture の点数・反復数、dat の実物、scenario 数) を親が source で裏取りした。
  子は途中で Bash が使えなくなり、横断 grep は親が代行した。
- 実装面 (test / generator) の修正は command 引数の scope (棚卸しと規約追記だけ) の外なので行わず、
  4 件を新規 T にした。生成器横断の meta test の新設も仮想リスク向け検査として不採用にした。
- 段 8: dev-wave 改善候補 1 件 — read-only の棚卸し子を親の worktree 隔離 (EnterWorktree) より前に
  起動したため、隔離後に子の Bash が worktree 隔離 hook で全拒否になり、横断 grep を親が代行した。
  docs の欠落ではなく起動順の作法 (隔離を先に済ませてから子を出す) なので、docs は変えず
  親の memory へ記録した。

## 次の一手差分

### 完了

- [T-2216] 6 図種を棚卸しし、規約 §10 と §9 訂正を作図規約書へ入れた (D1546)。被覆漏れ 4 件は下の新規へ分けた。
  remaining: none
  base: 0eb0aa3b43e7d66b1e60f61951495855cf6303553bcf675aed8f415867dabfed

### 新規

- {{T:plot-backoff-layout-check-fail-closed-and-real-size-fixture}} **P3・新規**: `plot_backoff.py` のレイアウト検査を
  保存前の fail-closed (rc 非 0) にし、`test_plot_backoff_ci.py` の fixture を実寸 (campaign 3 件・x 6 点・反復 5) へ
  揃える (FIGURE_CONVENTIONS §9/§10)。凍結図 fig2b/fig2c の bytes・provenance は変えない。Codex author (D95)。
- {{T:ss2pl-lock-study-real-figure-rendering-test}} **P3・新規**: `plot_ss2pl_lock_study.py` の 5 図種を、実寸の
  `_complete_sweep_document` (14 スレッド点・5 arm・5 block) で本物の Figure として描き `_figure_overlap_check` へ
  通すテストを足す。現状は 5 図関数を全部差し替えており、6 図種で最も注記が密なのに検査を一度も踏んでいない。Codex author。
- {{T:t2216-walk-model-fixture-real-size}} **P3・新規**: `test_t2216_backoff_walk_model.py` の model fixture を実寸
  (scenario 10 種、反復 8、cap50 の 2 条件を含む `_CONDITION_ORDER` 全 35 条件) へ揃える。measured 側は既に実寸。Codex author。
- {{T:s1-9pair-fixture-context-cells}} **P3・新規**: `test_s1_9pair_figure_provenance.py` の `_spy_data` に、producer が
  必ず出す文脈セル `ident_all` / `stock_common` を加え、図が描かずに無視する経路を fixture 上で踏ませる。Codex author。
