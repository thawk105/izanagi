/dev-wave [T-2853] 残り (5'') のうち fig15 (mocc_witlight_four_arm) の入力を閉じる。現状、生成器の既定入力は repo 外の
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/ (summary.json・W1〜W4/result.json) で、job dir
  の撤去で失われる型にある。同じ SHA-256 の逐語写しが追跡下の output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/
  にあるので、生成器がこの追跡下の写しを入力に取れるようにする。sha256 の一致を確かめてから描き直し、旧図との値の差 0 を確認して insight
  に記録する。正本: output/insights/2026-09-23/t2853-figure-rerun-plan/README.md (§2.3 と fig15 の行)、output/insights/2026-09-26/t2853-archive
  -inventory-figure-redraw/README.md、tools/plotting/FIGURE_CONVENTIONS.md。作図は計測機の外で行う。R2 の投入と fig15 の観測の再実施は scope 外
  (再実施には改めて認可が要る)。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh
  worktree を作る。
