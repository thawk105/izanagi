単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md (親 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/codex-artifacts/author-out.md (実装子の報告。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908 (作業 root。commit d42f2bec5 と 48837186c を `git show` で読む。読めなければ即停止)

## レンズ C — 受理集合・予算・fixture の整合 (敵対レビュー、read-only)
書込可能 tmp は無い。pytest 緑は要求しない。静的検査と `git show` / `grep` / `python3 tools/check_docs.py` (読取専用) でよい。
予算が尽きそうなら途中結論を下の出力形式で書いて終われ (無出力が最悪)。

攻撃対象 (commit d42f2bec5):
1. `tools/check_docs.py` の `COMMAND_LIMITS` に `.claude/commands/next-tasks.md: TextLimit(27_100, 100)`、
   `COMMAND_INTERFACES` に `{frontmatter_keys: {description, argument-hint}, arguments_count: 0}` を登録した。
   - 他の場所で command 集合を数える・列挙する検査 (層予算、dispatch 契約、whole-file sha pin、
     `_ENUMERATED_DOCS`、docs/README の地図、`docs/skill-self-improvement.md` の対象列挙 等) が
     4 件目の command を黙って外していないか、または既存 3 件前提の恒真検査が生まれていないか。
   - `arguments_count=0` は `$ARGUMENTS` の件数契約であり、現物は `$1` を使う。Claude Code の command
     で `$1` が引数として解釈される前提が正しいか、`$ARGUMENTS` を要求する既存契約と矛盾しないか。
   - 予算 27_100 / 最長行 100 は既存 3 件 (現物 +3〜16 bytes) と整合するか。過大・過小なら理由付きで。
2. `orchestrator/tests/test_check_docs.py`: 合成 fixture に next-tasks を足し、
   `test_next_tasks_command_budget_literal_is_exact` を足した。
   - 合成 fixture の追加で恒真化する既存 test (「不在で赤」を確かめる test が対象を rulings に固定している等) はないか。
   - 新 test が M1 (登録行の削除) と M2 (予算 27_101) を単一理由で殺すか。他に赤になる node があるなら列挙する
     (DW-M08 は期待 node の完全集合を要求する)。実 repo を読む assertion (27_054 bytes) の脆さ。
3. `.claude/commands/next-tasks.md` を bytes 同一で置いた。本文に repo 内 command として矛盾する記述
   (「本ファイル (repo 外)」、絶対 path `/work/1/SFC/tanab/scripts/` 等) があれば、直すべきか裁定へ返すべきかを
   scope (ユーザー依頼 = 移動と git 管理) に照らして判定する。

各所見に、放置時に成果物 (checker の受理集合・受入・land) の何が変わるかを 1 行で書く (書けない所見は nit)。
仮想リスクだけの gate・台帳・一般化の提案はしない。

## 出力形式
- 所見ごとに: `[must-fix|should|nit] <題>` / 根拠 (file:line) / 成果物影響 1 行 / 推奨。
- 最後に `## 総括` 節: must-fix 件数、should 件数、確信の無い点。
