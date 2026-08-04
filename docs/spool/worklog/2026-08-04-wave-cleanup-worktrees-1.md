---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-cleanup-worktrees
seq: 1
title: repo サイズ診断と worktree 残骸 16 本の掃除 (運用のみ、tracked 差分なし)
---

## 本文

- repo 実測: 全体 5.6GB の 96% が `.claude/worktrees/` 残骸 26 本 (1 本 ≈ 208MB。git 管理下の
  `output/` ≈ 190MB が worktree 作成のたび checkout されるのが機序)。docs/ は 6.1MB (archive 3.4MB)
  で、読み方規律と check_docs 予算により token 消費への寄与は限定的と診断した。
- ユーザー指示「最終更新から 1 日以上の worktree は削除可、並行セッション使用は `/proc` で実測」
  に従い、cleanup-branches の F26 手順で 16 本を削除 (t428-child-*/t428-fix-* 15 本 +
  wave-a-transport-smoke)。削除前に t428 系 15 本の全 commit (cherry 等価) と dirty 82 file の blob が
  wave 枝 `worktree-dev-wave-t428-reflux-wiring` の履歴に全部含まれることを検査し、固有内容ゼロを
  確認した。`.claude/` は 5.4GB → 1.7GB。
- プロセス滞在中の wave 系 worktree 8 本は残した。t428 系 branch 15 本は main 未取り込み
  (内容は wave 枝に等価保存) のため -D せず残置 — T-428 land 後の掃除で回収する。
- 生 trace 124MB (T-139 evidence) と insights 変異台帳 49MB の保管方針は別途ユーザー裁定待ち
  (本 wave では触っていない)。

## 次の一手差分
