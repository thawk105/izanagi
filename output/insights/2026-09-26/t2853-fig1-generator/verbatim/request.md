/dev-wave [T-2853] 残り (5''): 論文図 fig1 (docs/paper-story/figures/fig1_phase2_negative.png、P2-5 誘導探索の否定的結果)
  の生成器を作って描き直す。値の出所は追跡下の output/campaigns/p2-5-summary.json と P2-2 の 3 campaign で、新規計測 0 (再実行計画
  output/insights/2026-09-23/t2853-figure-rerun-plan/README.md §2.1・§3.1)。作図は tools/plotting/FIGURE_CONVENTIONS.md
  を正本に計測機の外で行う。凍結済み fig1 の bytes は上書きせず、後継は別 filename + provenance (docs/paper-story/figures/README.md
  の後継図の作法)。値が旧図と一致するかを照合して記録する (前回の 17 図描き直し
  output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md と同じ型)。実装は Codex author (D95)。着手直前の local main から
  fresh worktree を作る。本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
