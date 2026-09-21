# 依頼の逐語 (2026-09-21、/dev-wave の引数)

受入全走を 2 回以上投入した wave の原因を直近 landed wave 20 本の acceptance-receipt-*.json と acceptance-*.log (job dir)
  から分類する (診断のみ、着手直前の local main から fresh worktree)。分類 = 自分起因の赤 (fix → 最終 tip で再投入)、非帰属の既知間欠赤 (flaky
  hold 未登録)、F1013 同型 (三軸語走査の出力 file が holdout hit)、post-claim merge の terminal-merge、記録 commit 後の tip 変更 (rc=23
  型)、lease の失効。各分類の件数と追加 wall (受入 1 走 + lease 待ち) を出し、防げた分類ごとに既存手順 (受入前の main 取り込み位置、DW-O18 の
  hold 登録、三軸語走査の出力を insight に写さない) の何が守られなかったかを書く。受入の受理集合・門番・hold
  の意味論は変えない。結果は裁定パッケージ。規律 2 を緩めない。診断だけ。gate・台帳・一般化の追加は scope 外。
