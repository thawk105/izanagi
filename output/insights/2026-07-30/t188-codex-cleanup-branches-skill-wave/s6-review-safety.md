## 所見

1. **[real / blocker] `implicit=false` と trigger description が矛盾する。**
   [SKILL.md:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:3) は通常文の「明示的な cleanup 依頼」でも Skill を使うと主張する一方、[openai.yaml:7](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/agents/openai.yaml:7) は implicit invocation を禁止する。公式契約では `false` の場合、user prompt による自動起動はなく、明示的な `$cleanup-branches` だけが起動する。[OpenAI skills metadata](https://learn.chatgpt.com/docs/build-skills#optional-metadata)
   さらに checker がこの矛盾を正解として exact 固定している（[check_docs.py:218](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:218)、[test_check_docs.py:2203](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2203)）。
   **成果物影響:** `$` なしの明示 cleanup 依頼では安全 overlay の到達性がなく、T-173 が主張する安全な Codex 経路が成立しない。段6では `false` を維持し、description を `$cleanup-branches` 明示起動専用へ直すべき。通常文依頼も routing したいなら別裁定が必要。

2. **[real / blocker] TOCTOU 再検査が安全述語の全体を再評価していない。**
   dispatcher の `/proc/*/cwd` 検査は初回棚卸しにある（[cleanup-branches.md:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:22)）。overlay は namespace miss を証拠にしないと正しく縮退するが（[SKILL.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:24)）、破壊直前の再検査集合は `dirty / HEAD / branch / lock / cwd` だけで、新しい `/proc` 滞在、ownership/foreign 判定、main への包含、安全候補集合を再検査しない（[SKILL.md:29](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:29)）。
   **成果物影響:** 初回走査後に別プロセスが target へ入っても列挙5項目は不変のままになり、使用中 worktree の directory・未永続成果物を失わせ得る。各破壊ステップ直前に全 eligibility を再評価し、未知・変化・新規滞在のどれでも停止する必要がある。

3. **[real / must-fix] prune dry-run が実 prune の候補集合へ束縛されていない。**
   共通手順は directory 削除後に global `git worktree prune` を行う（[cleanup-branches.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:31)）。overlay は dry-run を要求するが、いつ target を stale 化した後に行うか、dry-run結果と実 prune の候補をどう同一化するかを定めず、直前再検査にも候補集合がない（[SKILL.md:27](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:27)）。`git worktree prune` には target operand がなく作用域は共有 metadata 全体である。
   **成果物影響:** preview 後に foreign record が候補化すると、その登録・lock・回復経路まで実 prune が除去し得る。target directory 削除後かつ実 prune 直前の再 preview、exact allowlist 一致、差分ゼロを必須にし、一意性を保てなければ prune を引き渡すべき。

4. **[real / must-fix] drift checker は安全の極性を検査せず、危険な反転を green にできる。**
   adapter/command の安全契約は語句集合（[check_docs.py:224](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:224)、[check_docs.py:256](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:256)）を単純な `literal in text` で探すだけ（[check_docs.py:1589](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1589)、[check_docs.py:1877](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1877)）。禁止を否定する文や廃止説明へ変えても単語が残れば通る。
   **成果物影響:** main/primary、foreign/locked、permission、push の安全極性が反転しても drift gate の受理集合に残る。重要節は exact clause/block または極性を含む構造検査で固定し、反転負例を追加すべき。

5. **[real / must-fix] 恒久 positive control が各 literal を検証していない。**
   adapter 負例は配列の `[0]`、すなわち `AGENTS.md` だけを削る（[test_check_docs.py:1896](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1896)）。command 側も最初の1件だけである（[test_check_docs.py:1912](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1912)）。exact surface pin は定数集合を固定するだけで、その全要素を checker が走査することを証明しない（[test_check_docs.py:2210](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2210)）。
   **成果物影響:** checker が先頭要素だけを見る退行でも全恒久テストが通り、foreign、prune、TOCTOU、push 等の drift 検出力が蒸発する。adapter と command の全 literal を個別に変異する parameterized control が必要。

6. **[real / nit / scope外の裁定候補] 薄いadapterに共通契約が一部再掲されている。**
   「手順を複製しない」とする [SKILL.md:8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:8) に対し、F51 と push/remote 境界が dispatcher と重複する（[SKILL.md:21](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:21)、[SKILL.md:36](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:36)、[cleanup-branches.md:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:38)、[cleanup-branches.md:52](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:52)）。
   [SKILL.md:17](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:17) の「狭い側」規則により現状の安全拡大は refuted。成果物への即時影響はない。共通境界を dispatcher のみに残すかは、Claude command変更がscope外なので将来裁定候補とする。

## 追加攻撃の裁定

- **main/primary — refuted:** 無条件保持が明記される（[SKILL.md:23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:23)）。ただし機械固定の弱さは所見4。
- **foreign/locked — refuted:** inventory/report 限定で unlock・directory削除・pruneを禁止する（[SKILL.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:24)）。
- **ExitWorktree — refuted:** Codexに存在すると仮定せず、cwd固定不能時はF51縮退する（[SKILL.md:21](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:21)）。
- **権限非昇格・hook差 — refuted:** 権限拡大を禁止し、Codex hook未配線も正直に明示する（[SKILL.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:31)、[SKILL.md:36](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:36)）。
- **remote/push — refuted:** 人間へ残す境界は一致する（[SKILL.md:37](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:37)）。checkerの極性は所見4。
- **質問時の削除 — refuted once loaded:** 質問・レビューをクラス1 read-onlyへ落とす（[SKILL.md:12](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:12)）。Skill到達前の製品routingは所見1。

実cleanup、Claude command修正、hook配線、runtime discovery、pytestは実施しておらず、greenも主張しない。

## 総括

**NO-GO。** 段6 fix対象は所見1〜5：explicit-only metadata整合、全安全述語の破壊直前再検査、prune候補の束縛、極性を含むdrift検査、全literalの独立負例化。所見6は現状安全なscope外裁定候補であり、今回のfix対象には含めない。