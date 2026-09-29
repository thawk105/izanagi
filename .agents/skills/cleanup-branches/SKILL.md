---
name: cleanup-branches
description: Safely back up and clean up merged or stale local Izanagi branches and worktrees through the shared dispatcher. Use for branch or worktree cleanup; deletion needs explicit $cleanup-branches.
---

# Cleanup Branches

共通の cleanup dispatcher を読み、その手順を複製せず Codex 固有の安全縮退を重ねて実行する。

## 共通 dispatcher を使う

1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読む。`$cleanup-branches` で明示起動された
   掃除だけクラス 2 とし、質問・相談・説明・レビューはクラス 1 の read-only として何も削除しない。
2. `.claude/commands/cleanup-branches.md` を全文読み、冒頭の最優先 mutation boundary から末尾の
   自己改善終端までを全工程へ不可分に適用する。クラス 2 や外側の作業種別は許可集合を拡張しない。
   command が不在または読取不能なら停止する。
3. command の `$ARGUMENTS` は本 Skill に渡された対象限定と読み替える。未指定なら command の全量棚卸し契約に従う。
4. command と本 overlay が衝突する場合は、削除範囲が狭くなる安全側へ縮退して対象と未実行操作を報告する。

## Codex 固有の安全 overlay

- Claude 固有の `ExitWorktree` が使えると仮定しない。cwd を対象外へ固定できなければ F51 とし、
  現在の worktree directory の削除と prune を行わない。
- `/proc/*/cwd` の miss は非使用の証拠に数えず、この Codex session の所有を証明できない
  worktree は command の foreign/unknown として保持する。
- 各破壊操作の直前に dispatcher の全 eligibility と canonical path、process residency を再評価する。
  unknown、棚卸し後の change、新しい residency があれば停止する。
- `git worktree prune --dry-run --verbose` は報告用 preview としてだけ実行する。Codex は real
  `git worktree prune` を実行せず、preview と残作業を人間へ引き渡す。
- 未追跡 `output/` (`exploration/`・`env/`) を抱える worktree は、command §2 の原本確認 (insight
  「証拠の所在」節) を経るまで foreign/unknown と同じく保持して報告する。
- dirty の撤去や引き渡し script は command §3 の退避検算 (tar の `-C` 順・非 dir entry 数照合) を前提にし、
  検算を欠く撤去手順を人間へ渡さない (F1034)。
- sandbox または shared Git metadata の権限が不足する場合は権限を拡大しない。安全に実行できた操作、
  対象、未実行操作を人間へ返す。

## 境界を守る

hook の配線と限界は `hooks/README.md` が正本である。設定の存在を防護の証拠に数えず、
同文書の保護境界を手動で守る。push と remote branch 操作は人間に残す。

自己改善候補も共有 command の終端に従い final で報告するだけとし、別 dev-wave へ自動移行しない。
