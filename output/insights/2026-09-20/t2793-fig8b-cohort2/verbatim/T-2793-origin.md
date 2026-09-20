# [T-2793] 依頼文 (ユーザー、2026-09-20、dev-wave 引数の逐語)

[T-2793] fig8 (B-10 静的右 tail) に第 2 cohort の再現欄を足した後継図を作る。着手直前の local main から fresh
worktree。凍結済み fig8 の bytes は上書きせず、後継図 (別 filename、例 `fig8b_b10_static_tail_cohort2`) を Codex author
(D95) が `tools/plotting/plot_b10_static_tail_formal.py` の拡張 (cohort 引数) で生成し、provenance JSON と
`docs/paper-story/figures/README.md` の節を足す。材料は `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md`
§2.6 / §4.1 (group `b10-backoff-grid-20260919T131526Z-2235286`、事前登録追記込み commit `8737cacb4` に束縛)。主結果 cohort
1 と区別して併記し、合成・プール・統合 verdict は作らない。言い方は事前登録 §4.5 の固定表現に限る。規律 2
を緩めない。本題の作図だけ — gate・検査・台帳・一般化の追加は scope 外。
