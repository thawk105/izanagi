この依頼は `cleanup-branches` のクラス1 read-only 説明です。したがって、Git 状態の棚卸し、候補判定、事後検査、handoff、worklog 更新を含め、実操作は何も行いませんでした。

実行時の想定ワークフローは次のとおりです。

- ローカルブランチと worktree を棚卸しする。
- ahead/cherry、clean、HEAD が `main` に含まれるか、recent、lock、canonical path、プロセス使用中か、ownership を確認する。
- 削除直前にも全条件を再評価し、不明点・状態変化・新しいプロセス使用があれば停止する。
- 条件をすべて満たす、マージ済みのローカルブランチ／所有が確認できる worktree だけを対象にする。
- prune は `git worktree prune --dry-run --verbose` の preview と報告までに留め、残作業を人間へ引き渡す。

意図的に残す操作・対象は以下です。

- local `main` と primary worktree
- remote branch の変更・削除、および push
- real `git worktree prune`
- locked worktree の unlock、削除、prune
- このセッションが作成・所有したと証明できない foreign worktree
- dirty、未マージ、ahead/cherry が残る、recent、非 canonical、使用中、または判定不能な対象
- cwd を安全に対象外へ固定できない場合の現在の worktree（F51）
- 権限不足時の権限拡大
- `/proc/*/cwd` の miss だけを根拠にした「未使用」判定

ロードできた exact file は、依頼本文に全文提示された次の2つです。

- `AGENTS.md`
- `.agents/skills/cleanup-branches/SKILL.md`

Skill が共有 dispatcher として指定する exact file は `.claude/commands/cleanup-branches.md` です。ただし、その本文は依頼に添付されておらず、「コマンドを実行しない」という制約を守ったため今回はロードしていません。したがって、上記はロード済み Skill の明示的な契約だけの説明であり、dispatcher 固有の追加条件を推測してはいません。

## 総括