---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2267-exec-site-class
seq: 3
---

## 新規

### {{F:ff-only-fails-when-main-commit-is-replaced}}. local main の commit が同内容・別 SHA へ差し替わると `--ff-only` 追従が不能になる [手順漏れ]

- 事象: wave 開始直後に local main の tip から fresh worktree を作った直後、別 session の land が
  main の先頭 commit を**同じ件名・同じ親・別 SHA** の commit へ差し替えた。worktree の branch は
  main から消えた側の commit に載り、`DW-O20` が指示する `git merge --ff-only main` が
  `fatal: Not possible to fast-forward, aborting.` で失敗した。開始 gate も
  `NG: HEAD != local main` を返し続けた。
- 根本原因: `DW-O20` の追従手順は「main が**進んだ**」場合だけを想定している。main の commit が
  置き換わると worktree の HEAD は main の祖先でなくなるため、ff-only は原理的に成立しない。
  `git merge-base --is-ancestor <worktree HEAD> main` が偽になることで判別できる。
- 恒久対応: 手順として残す。ff-only が失敗したら、まず祖先性を検査する。祖先でなければ追従ではなく
  **branch の作り直し**で復旧する — worktree 内で `git checkout --detach main` →
  `git branch -D <wave branch>` → `git checkout -b <wave branch>`。
  `git reset` は使わない (reflog に reset が残ると land が拒否する)。
  作り直しは wave 側に自前 commit が無い間だけ安全であり、commit 済みなら別手順が要る。
- 再発検知: 開始 gate の `NG: HEAD != local main` が `--ff-only` 1 回で解消しないこと。
  併せて `git merge-base --is-ancestor` の偽を確認する。
