# 親の実測 (段 6 fix 第 1 巡の後、2026-08-25 23:2x)

## 状況変化 — 対象 branch 8 本が wave 実行中に別経路で削除された

wave 開始時 (20:16 の依頼、親の実測 21:2x) に存在した 9 本のうち、
**`worktree-cleanup-branches-20260825` を除く 8 本が消えた。**
`git for-each-ref refs/heads/` で 0 件。

消えた branch と、その tip commit の現況:

```
t1484-backup-before-trailer-fix          39407cfd  OBJECT-ALIVE  main から到達不能
worktree-agent-ab4539bed30390c7f         b3611129  OBJECT-ALIVE  main から到達不能
worktree-roadmap-workload-hint           15b5c389  OBJECT-ALIVE  main から到達不能
worktree-rulings-20260818-floor-measurement fe56f5f7 OBJECT-ALIVE main から到達不能
worktree-rulings-20260818-second         a6a9f2b7  OBJECT-ALIVE  main から到達不能
worktree-t1458-side-ccbench-provenance-fix 028a5e2d OBJECT-ALIVE main から到達不能
worktree-workload-policy-hint-impl-unitB/C 500f47a6 OBJECT-ALIVE main から到達不能
```

`worktree-dev-wave-t441-backoff-hole-grammar`、`worktree-dev-wave-t425-d716-carry-note`、
`worktree-dev-wave-t1629-ratification-execution`、`worktree-rulings-20260825-all` も消えている。

**削除の結果は親の正解データと一致する。** 親が唯一「真に未着地」と判定した
`worktree-cleanup-branches-20260825` だけが残された。他 8 本は親の判定でも着地済みだった。

## これが設計へ課す新しい要求

判定器は今 **local branch 名しか受け取らない**。branch が消えた後は
`git rev-parse --verify refs/heads/<name>^{commit}` が
`fatal: Needed a single revision` で落ち、`git-command-error` として `indeterminate` になる。

しかし**取り残しの実体は、削除後は「到達不能 commit」である。**
判定が最も必要になるのは削除の直前と直後であり、削除後に判定できない道具は
`git gc` までの猶予期間に何もできない。
`tools/audit_dangling_commits.py` は「既存ファイルへの変更・削除・同名別内容・gitlink 更新」を
検出対象外と明記しており、この穴を埋めない。

## fix 第 1 巡の実走結果

`orchestrator/tests/test_check_branch_landed.py` は **46 passed / 1 failed**。

```
FAILED test_history_scan_limit_is_indeterminate_and_measured
  期待 decision.reason = "history-scan-limit-exceeded"
  実際 decision.reason = "one-or-more-states-unproven"
  verdict はどちらも indeterminate、rc=2 も一致
```

F14 (全履歴の完走要求を positive proof の事前 gate から外す) を実装した結果、
履歴上限超過は branch 単位の理由でなくなり unit 単位の理由になった。
**実装の変更が正しく、テストの期待値が追随していない。**
unit 側が `history-scan-limit-exceeded` と打ち切り実測値を持つことを
assert する形へ直すのが正しい (F10 の要求を落とさないこと)。
