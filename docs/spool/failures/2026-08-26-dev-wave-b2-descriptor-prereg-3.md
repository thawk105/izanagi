---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-b2-descriptor-prereg
seq: 3
---

## 再発

### F646

- **再発: 2026-08-26** — fresh worktree の**初回**受入全走で 3 node が同時に落ちた
  (`test_real_repo_serialization.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`、
  `test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes`、
  `test_s8b_oracle_driver.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`)。
  赤の本文は 3 件とも `assert 'runs' in ('insights/2026-08-05_t471-restore-bound/driver/__pycache__',
  'pegasus-dispatch')`。**本エントリの根本原因の記述は 1 点ずれていた** — 当該 worktree には
  `output/runs/` が**実在していた**。落ちたのは dir が**空**だったからで、
  `git ls-files -o -i --exclude-standard --directory` は untracked entry を含まない dir を返さない。
  したがって「環境側で `output/runs/` を作る」という前回の回避は、**空の dir を作っただけでは
  効かない**。
- **同じ受入走行が自分で前提を満たす。** 落ちた走行が `output/runs/pytest-launcher-failures/` を
  作るため、直後に同じ 3 node を単独走すると `3 passed` になり、2 回目の受入全走は緑になる。
  すなわち**新しい worktree の初回受入全走は構造的に必ず 1 回赤になり、lease 窓を 1 つ捨てる**。
  本 wave はこの 1 回を捨てて再走した (実装差分は docs のみで、3 node のどれにも到達しない)。
- 恒久対応の候補に 1 つ足す: (d) 判定器が要求する ignored dir を、テストが
  **untracked entry ごと**自分で用意してから判定する。実在確認だけでは足りないことが本再発で確定した。
