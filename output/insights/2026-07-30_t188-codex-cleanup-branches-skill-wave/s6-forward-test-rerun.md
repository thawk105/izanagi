読み込んだ正本は次の4ファイルです。

- Project Skill: [.agents/skills/cleanup-branches/SKILL.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md)
- Shared dispatcher: [.claude/commands/cleanup-branches.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md)
- Repository entrypoint: [AGENTS.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/AGENTS.md)
- Common AI policy: [CLAUDE.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/CLAUDE.md)

実際のcleanup実行なら、ワークフローは以下のように進みます。

1. 全ローカルブランチとworktreeを棚卸しし、mainに対するahead/behind、未コミット差分、HEADの取り込み状況を調べます。
2. aheadが残るブランチではcherry相当性も確認し、rebaseやcherry-pick後に見かけ上aheadとなったコミットと、本当に未取り込みのコミットを区別します。
3. ブランチは`ahead=0`の場合だけ通常削除します。強制削除は使わず、通常削除が拒否した場合は停止して報告します。
4. worktreeは、クリーン、HEADがmainに包含済み、直近利用でない、滞在プロセスがない、正規パスを確認できる、という条件を満たす場合だけ候補になります。
5. submoduleを含むworktreeは、F26手順に従い、HEADのdetach、ブランチの通常削除、ディレクトリ処理という順序で扱います。
6. 各破壊操作の直前に条件を再評価し、棚卸し後の変化、新しい滞在プロセス、判定不能事項があれば、その操作だけ停止します。
7. 最後にブランチ・worktree、submodule、作業ツリーの状態を再確認し、実行できた操作と残作業を報告します。

意図的に行わない操作も明確です。

- 今回は「説明」のためクラス1です。したがって、Git状態の棚卸しを含む一切のGitコマンド、削除、編集、権限拡大を行っていません。
- ローカル`main`とprimary worktreeは無条件に保持します。
- aheadが残るブランチ、dirtyなworktree、mainに未包含のHEAD、最近使用されたworktree、滞在プロセスがあるworktree、判定不能な対象は削除しません。
- `git branch -D`による強制削除は行いません。
- locked worktreeや、このCodexセッションが所有したと証明できないforeign worktreeは報告だけに留め、unlock、ディレクトリ削除、pruneを行いません。
- `/proc/*/cwd`でプロセスを発見できなかったことだけを「未使用」の証拠にはしません。
- 現在のworktreeから安全に退出できない場合はF51として、そのworktreeのディレクトリ削除とpruneを行いません。
- `git worktree prune`の実処理はCodexでは行いません。dry-run previewだけを許し、実処理は人間へ引き渡します。
- `git submodule deinit`は使用しません。
- `discard_changes`で変更を押し切るworktree削除は行いません。
- remote branchの削除、mainのpushを含むpush操作はすべて人間に残します。
- sandboxや共有Git metadataの権限が不足しても、権限拡大は要求しません。

## 総括

このcleanupは「安全性を証明できる、mainへ取り込み済みのローカル資産だけを通常手段で整理する」手順です。不明・使用中・未取り込み・外部所有の対象は残し、強制削除、実prune、remote操作、pushは意図的に人間へ引き渡します。