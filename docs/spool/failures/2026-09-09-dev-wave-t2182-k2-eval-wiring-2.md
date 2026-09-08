---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2182-k2-eval-wiring
seq: 2
---

## 新規

### {{F:review-children-read-a-mutating-worktree}}. 段 6 の敵対レビュー 2 本を fix 子が編集中の worktree へ向け、既に直った赤が must-fix で戻った [手順漏れ] [偽の所見]

- 事象: [T-2182] の段 6 で、親が fix 子 1 本とレビュー子 2 本を同時に同じ worktree
  (`.codex/worktrees/t2182-fix1`) へ向けて起動した。fix 子が編集している最中に 2 本が読んだため、
  片方は fix 後の実装を、もう片方は fix 前の実装を読んだ。後者は親が既に実測で確認して直した赤
  (`buildcache._v2_commands` の呼び出し順による既存 consumer test の破壊) を must-fix として報告し、
  前者は「snapshot が live source と食い違う」ことを別の must-fix として報告した。**どちらの所見も
  最終 bytes に対しては成立しない。** 親は 2 件とも refuted に裁定し直した。
- 根本原因: 段 6 の契約は「異なるレンズで 2 本並列」を定めるが、**レビュー対象の木が読み取り中に
  不変であることを要求していない。** `DW-M05` は変異走行についてだけ「変異中は親の編集と worktree へ
  書きうる子の起動を止める」と定めており、レビューは射程外だった。親は fix と review を同時に流して
  wall-clock を詰めようとして、この穴を踏んだ。
- 恒久対応: memory `no-dispatch-from-worktree-while-child-edits` に本事象を追記済み。
  **`docs/dev-wave/workers.md` の `DW-S06-A` への手順統合は、L1.5 層の byte 予算が満杯
  (9694/9696 bytes) で入らなかった。** 追記すると 9864 bytes で `tools/check_docs.py` が赤になる。
  上限は上げていない。予算に空きが出た改訂で `DW-S06-A` へ「レビュー子と fix 子を同じ worktree へ
  同時に向けない」を統合する。
- 再発検知: レビュー子の報告が、親が既に閉じた赤を must-fix として挙げたら本型を疑う。
  親は所見を裁定する前に、レビュー子が読んだ木の状態を最終 bytes と照合する。
