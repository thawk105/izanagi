# T-173 Codex cleanup-branches Skill 移植 — 段 1 brief

- scope: Claude `/cleanup-branches` command を共通 dispatcher として再利用する repo-scoped Codex Skill、
  UI metadata、drift を拒否する `check_docs.py` / tests、Phase 3 / worklog 記録を追加する
- ユーザー裁定: 既存の Claude 版を Codex でも使えるようにする
- 不変条件: cleanup はクラス 2 の破壊的操作として扱い、安全条件を満たさない branch / worktree を
  残し、remote branch 削除・main push を人間へ残す
- 不変条件: `.claude/commands/cleanup-branches.md` を実行手順の共通正本とし、Skill 側へ手順を複製しない
- 不変条件: Codex の PreToolUse hook は未配線として、Claude hook の発火を主張せず
  `hooks/README.md` の保護境界を手動で守る
- 不変条件: 本 wave では branch / worktree の実掃除を行わず、既存セッションの worktree / branch /
  handoff を変更しない
- 成果物: `.agents/skills/cleanup-branches/SKILL.md` と `agents/openai.yaml`
- 成果物: checker の 2 file 閉包、frontmatter / interface、必須 adapter literal の fail-closed 検査と負例
- 成果物影響: 現状は Codex の Skill 発見面に `cleanup-branches` が無く、安全な共通 dispatcher を
  `$cleanup-branches` として明示起動できない
- 分割: 段 2 plan 1 本、段 3 は破壊操作安全と checker 実効性の 2 レンズ、段 5 は単一
  workspace-write Codex author、段 6 は独立 2 review と必要時の単一 fix
- gate 新設条件: `check_docs.py` の既存 Skill guard を 3 Skill 目へ拡張するため成立。
  gate 入力は repo 内の regular file bytes、frontmatter fields、exact file closure、生成済み
  `openai.yaml` bytes、Skill 本文の必須 literal であり、実成果物に存在する
- freeze / oracle / proof chain、凍結 bytes、producer write-path、performance 計測には触れない
- 初回開始検査: 新規 worktree の submodule 未初期化で rc=1。専用 worktree の submodule を初期化後、
  同じ external handoff で再実行して rc=0
