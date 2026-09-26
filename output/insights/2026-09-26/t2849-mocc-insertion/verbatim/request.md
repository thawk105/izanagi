/dev-wave 引数 (逐語、2026-09-26):

[T-2849] 残り (2) = 単位 8 (MOCC の差し込み) を行う。前提の pin 前進は済み (main の gitlink = C 68106660)。同じ wave の先頭で MOCC
  の動作点を較正する。設計は D2220 と output/insights/2026-09-22/t2849-comparison-harness-design/README.md §9、既存実装は D2233 と
  output/insights/2026-09-23/t2849-comparison-harness-impl/README.md
  (orchestrator/campaign/t2849_comparison_harness.py・t2849_generators.py)。残り (3) の第 2 プロトコルでの疎通 (検証だけで 8〜16 node 時間)
  はこの wave に含めない。較正を含む計算が 1 タスクで 2 node 時間以上なら、job Elapse の実測単価で見積りを示してユーザー確認を取る (D2212 項
  4)。着手直前の local main から fresh worktree を作る。実装は Codex author (D95)。規律 2 は緩めない。本題の実装だけで、仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。
