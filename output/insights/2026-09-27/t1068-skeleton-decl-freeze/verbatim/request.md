/dev-wave の引数 (2026-09-27 14:3x JST、ユーザー直接起動、逐語):

[T-1068] trigger 骨格の宣言側と呼出依存を凍結する (2026-08-16 /rulings 全件 第 3 回の裁定)。R4 (prologue での izanagi_gate_pass
  の再宣言による代入・真理値の無効化)、R5 (宣言と BEGIN の間の制御流変更による非到達化)、R7 (Backoff / FLAGS_clocks_per_us の local shadowing)
  の 3 経路は、block と epilogue を逐語一致させたまま gate を無効化できる。実証差分は
  output/insights/2026-08-13_t1048-trigger-freeze-epilogue/verbatim/ の consult-b.md 所見 1・consult-a2.md 所見 2・review-b.md 所見 2。3
  経路それぞれの負例 (受理されないこと) と既存の凍結済み差分の正例 (引き続き受理されること) を同じ単位で置く。dangling else (R6、[T-1069]) は
  scope 外。実装は Codex author (D95)。規律 2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope
  外。着手直前の local main から fresh worktree を作る。

(注: 実在の insight path は output/insights/2026-08-13/t1048-trigger-freeze-epilogue/verbatim/ — 依頼文の `2026-08-13_t1048-...` は旧 path 表記)
