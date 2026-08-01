---
name: cleanup-branches
description: Safely inventory and clean up merged local Izanagi branches and worktrees through the shared dispatcher. Use only for an explicit $cleanup-branches invocation; implicit invocation is disabled.
---

# Cleanup Branches

共通の cleanup dispatcher を読み、その手順を複製せず Codex 固有の安全縮退を重ねて実行する。

## 共通 dispatcher を使う

1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読む。`$cleanup-branches` で明示起動された
   掃除だけクラス 2 とし、質問・相談・説明・レビューはクラス 1 の read-only として何も削除しない。
2. `.claude/commands/cleanup-branches.md` を全文読み、棚卸し、削除条件、F26/F51、事後検査、
   引き渡し、自己改善の共通 dispatcher としてそのまま実行する。command が不在または読取不能なら停止する。
3. command の `$ARGUMENTS` は本 Skill に渡された対象限定と読み替える。未指定なら command の全量棚卸し契約に従う。
4. command と本 overlay が衝突する場合は、削除範囲が狭くなる安全側へ縮退して対象と未実行操作を報告する。

## Codex 固有の安全 overlay

- Claude 固有の `ExitWorktree` が使えると仮定しない。cwd を対象外へ固定できなければ F51 とし、
  現在の worktree directory の削除と prune を行わない。
- local `main` と primary worktree は無条件に保持する。
- `/proc/*/cwd` の miss は非使用の証拠に数えない。locked worktree と、この Codex session が作成・
  所有したと証明できない foreign worktree は inventory / report のみにし、unlock、directory 削除、
  prune を行わない。
- 各破壊操作の直前に dispatcher §2 と overlay の全 eligibility（ahead / cherry、clean、HEAD の
  main 包含、recent、lock、canonical path、local `main` / primary、ownership / foreign、
  `/proc/*/cwd` の process residency）を再評価する。unknown、棚卸し後の change、新しい process
  residency のいずれかがあればその操作を停止する。
- `git worktree prune --dry-run --verbose` は報告用 preview としてだけ実行する。Codex は real
  `git worktree prune` を実行せず、preview と残作業を人間へ引き渡す。
- sandbox または shared Git metadata の権限が不足する場合は権限を拡大しない。安全に実行できた操作、
  対象、未実行操作を人間へ返す。

## 境界を守る

Codex には `hooks/README.md` の PreToolUse hook が未配線であるため、hook が発火したと主張せず、
同文書の保護境界を手動で守る。push と remote branch 操作は人間に残す。

今回の実行で記載と実挙動の食い違い、新しい罠、手順不足を実測した場合だけ
`docs/skill-self-improvement.md` の cleanup-branches routing と commit 境界に従う。
