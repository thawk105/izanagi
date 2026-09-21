# 依頼文の逐語 (2026-09-21 20:4x JST、/dev-wave の引数)

論文の結果節の図を 2 枚、1 wave で作る (台帳 ID 未起票、`tools/plotting/FIGURE_CONVENTIONS.md` に従う)。(1) A-1 sized attempt-0002
  の記述図 (fig9 の兄弟): 入力は tracked の公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` (result.json
  sha256 `b7e0518e…`)、caption_source は `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` (§2.6
  が「図は無い」と記録)。既存生成器 `tools/plotting/plot_a1_sized_paired.py` (attempt-0001 の hash を固定) を attempt ごとの exact な pin
  表で拡張し、fig9 と既存稿の bytes は変えない。2 attempt をプールせず、差・比・再現判定を描かない。`variance_plan_breach` は図に出す。(2) mocc
  witlight 4 arm の図: 入力は repo 外の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/` の W1〜W4 `result.json` と
  `summary.json` (results 稿 `2026-09-20-mocc-witlight-four-arm.md` §5.1 の SHA-256 と一致を確認済み) を束縛する新規生成器。本走は W1〜W4 の 4
  block で、smoke は第 5 block として数えない。値は同稿 §2 の G2 検出数・CP 区間・曝露量を逐語で使い、非有意を同等性として、TRACE=1
  の曝露量を性能として、G2 signal を根因の同定として描かない。生成器と test は Codex author (D95)、作図は login で行う (規律
  4)。`tools/plotting/README.md` と `docs/paper-story/figures/README.md` への節追加は、この wave が両方とも持つ。results 稿と版の bytes
  は変えない。本題の作図だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
