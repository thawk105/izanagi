(ユーザー直接起動の `/dev-wave` の引数、2026-09-27 19:1x JST、逐語)

[T-2865] silo-function-policy 軸の 2 iteration 目以降を回す。手順は docs/phase3-silo-policy-runbook.md §1 (特に (g) critic の spawn
  と --critic-output)、段階 F の記録 output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md、D2270。先に同 insight §3.4 の所見 (骨格
  patch patches/silo-function-policy-variant.patch の thread_local
  乱数状態の初期値が全スレッドで同じで、乱数で待ちを散らす方策の効果が弱まる。正しさには影響しない) を最小修正するかを段 3
  で決め、直すなら変更前後を別条件として記録して 1 iteration 目の結果と混ぜない (骨格の変更は Codex author、stock build
  の同一性は崩さない)。iteration 数は 1 iteration = pair job Elapse 765 秒 + LLM 約 6 分の実測から見積もり、検査込みの job 合計が 2 node
  時間以上ならユーザー確認後に投入。firewall (D2243 項 1: 小比較の点 ID・因子・比・順位を coder / critic の入力へ渡さない) と、auditor gate
  の閉じた出力形の prompt 明記 (runbook §1(d)) を守る。[T-2870] の role 本文改訂はユーザー承認待ちなので触らない。規律 2 を緩めない。着手直前の
  local main から fresh worktree。本題だけ、仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
