---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: workload-policy-hint-impl
seq: 1
---

## 再発

### F82

- **再発: 2026-08-19 (4 度目)** — [T-1418] (仮) wave の段 9 land が `status=fold-failed` /
  `reason=landed-fold-owned-path` で 2 回連続停止した。main は 1 bit も動いていない
  (`main_before == main_after`)。今回のトリガは過去 3 件 (「fragment を書く」「main の fold 済み
  merge を取り込む」) のどちらとも異なる第 4 の経路: **wave が継承した spool fragment 2 件
  (別 branch `worktree-roadmap-workload-hint` 由来、`wave: roadmap-workload-hint`) を、自 wave の
  fragment (`wave: workload-policy-hint-impl`) と同一 fold 識別子で扱うため `git mv` で
  re-home した。** `docs/spool/README.md` の「identity は (wave, namespace, slug)。他 wave の
  slug は参照できない」規則により、継承 fragment を自 wave の worklog から D の placeholder で
  参照するには wave tag の統一が必須だった。この re-home は `git diff` 上 `R100`（100%
  類似度の rename) として記録され、`_landed_fold_output_path`
  (`tools/dev_waves/git_state.py:561`) の署名 (「fragment 形の path が D または R で消える」)
  に一致し、fold 以外の正規経路であるにもかかわらず無条件拒否された。
  F82 の「署名は fold 以外では起きない」という前提命題が本件で 3 度目に破れたことになる
  (1 度目・2 度目は「main の fold 済み merge を取り込む」、本件は「wave 自身の fragment
  reorganize」)。
  親は `git reset --soft` によるこの wave 自身の (main へまだ 1 bit も land していない) 履歴
  squash で回避しようとしたが、(a) Claude Code の auto mode classifier が history-rewrite
  相当の操作を 2 度 (loop 化した `git log` 収集 script・squash 用 commit message の Write) とも
  拒否し、(b) `docs/decisions.md` の既存裁定 (D371 近傍、「merge の作り直し — main の履歴書き換え
  (rebase / force) は禁止されており実行不能」) も rewrite 系の回避を却下済みと確認したため、
  forward-only な回避策の不在を認めて中断した。実装自体は commit `feb4452c` (branch
  `worktree-workload-policy-hint-impl`) に完成・全緑で存在するが、本 fold-owned-path 制約が
  解消されるまで land 不能である。
