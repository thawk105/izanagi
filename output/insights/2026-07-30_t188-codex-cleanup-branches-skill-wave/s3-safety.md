判定は **NO-GO**。現 plan のまま段5へ進むと、Codex 固有の `/proc` 可視性と権限境界を満たせず、さらに共通 dispatcher 自体に primary worktree を削除候補へ入れ得る穴があります。編集・cleanup・pytest は実施していません。

## Real findings

1. **[blocker] primary worktree と local `main` が削除候補から除外されていない**

   棚卸しは全 worktree・全 local branch を対象にし、削除条件は `ahead=0` と clean/merged だけです（[cleanup-branches.md:11](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:11)、[cleanup-branches.md:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:20)、[cleanup-branches.md:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:22)）。`main..<main>` は常に 0 で、linked worktree から実行すれば primary checkout は「自分が居る worktree」でもありません。

   その primary checkoutを detach → `git branch -d main` → directory削除へ送れる構造です（[cleanup-branches.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:31)）。`-d` は `-D` より安全ですが、detach 後の `main` に特別な保護はありません。primary directory の削除は共有 `.git` まで失わせ得ます。

   `refs/heads/main` と primary worktree は無条件除外が必要です。

2. **[blocker] Codex では `/proc/*/cwd` の負例が他セッション不在を証明しない**

   dispatcher は他セッション使用中判定を `/proc/*/cwd` に依存します（[cleanup-branches.md:23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:23)）。read-only 実測では：

   - `git worktree list` は 13 worktree
   - 1件は `locked claude session ... (pid 2562978 ...)`
   - この sandbox の `/proc/[0-9]*/cwd` は2件しか見えず、PID 2562978 は不可視

   したがって Codex の PID namespace 内で「hitなし」は使用中でない証拠になりません。F51 は自分自身の固定 cwd だけを扱い（[cleanup-branches.md:41](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:41)、[failures.md:947](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/failures.md:947)）、不可視な他セッションは守りません。

   Codex adapter では少なくとも、`locked` は無条件保持、foreign worktree は `/proc` の負例だけで削除不可、foreign lock を unlock しない、という縮退が必要です。cwd 比較も canonical path の完全一致だけでなく子孫を含める必要があります。

3. **[blocker] target限定と `git worktree prune` の作用域が一致しない**

   plan は `$ARGUMENTS` を対象限定として固定します（[s2-plan.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:49)）が、`git worktree prune` は全 worktree 管理記録を対象とする global 操作です（[cleanup-branches.md:33](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:33)）。指定外の stale record を変更し得るため、対象限定の削除権限を越えます。

   また、inventory後から detach/directory削除までの間に dirty・HEAD・lock・cwdを再確認する義務もありません。削除直前の再検証、canonical exact path、symlink・ancestor・primary拒否が必要です。prune は dry-run 結果が対象1件だけと証明できなければ人間へ引き渡すのが安全です。

4. **[blocker] checker は共通 dispatcher の安全意味論を守らない**

   `_check_codex_skill_guard` が見るのは Skill 内の substring と metadata bytesだけです（[check_docs.py:1433](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1433)、[check_docs.py:1524](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1524)）。cleanup command 側は frontmatter、`$ARGUMENTS`、自己改善文書への到達性しか固定されません（[check_docs.py:1638](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1638)）。

   実際、synthetic cleanup command は `$ARGUMENTS` と自己改善文書名しか持たないのに（[test_check_docs.py:248](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:248)）、baseline clean です（[test_check_docs.py:421](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:421)）。

   したがって dispatcher から `-D` 禁止、F26/F51、`/proc`、remote/main push禁止を消しても、新規 Skill の文字列が残れば plan の検査は通り得ます。「drift を拒否する checker」という brief の主張（[s1-brief.md:14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s1-brief.md:14)）には未到達です。

5. **[must-fix] 自己改善 gate は経路として意図されているだけで、checkerに保持されない**

   現行 command は「今回実測した場合だけ」「発火しなければ編集しない」を持ちます（[cleanup-branches.md:58](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:58)）。共通契約も同じです（[skill-self-improvement.md:13](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/skill-self-improvement.md:13)、[skill-self-improvement.md:63](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/skill-self-improvement.md:63)）。

   しかし plan の必須 literal は文書パスだけで（[s2-plan.md:109](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:109)）、発火条件や非発火時の編集禁止を固定しません。予定 mutation にも自己改善 gate の除去がありません。よって Skill→dispatcher 経路は初版の prose では成立しても、guard が証明しません。

6. **[must-fix] SkillへのF26/F51等の再掲は drift防止ではなく、第二の規範面になる**

   brief は手順をSkillへ複製しないとします（[s1-brief.md:8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s1-brief.md:8)）が、plan はF26、F51、remote/main境界をSkillへ再掲します（[s2-plan.md:53](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:53)）。共通契約は短い cleanup 手順をcommandへ置き、同内容を複数箇所へ全文複製しないと定めます（[skill-self-improvement.md:34](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/skill-self-improvement.md:34)）。

   checker は両者の同値性・優先順位・矛盾を検査しないため、これはbelt-and-suspendersではなく二重正本です。Skillに残すべきなのは、Codex hook未配線、PID namespace、sandbox権限非昇格など製品固有差分だけです。共通安全条項はdispatcherで固定し、checkerもdispatcherを直接検査すべきです。

7. **[blocker] destructive trigger と実行権限が曖昧**

   description案の「明示起動または同等依頼」は広すぎます（[s2-plan.md:40](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:40)）。相談・説明・レビューはクラス1です（[CLAUDE.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/CLAUDE.md:24)）。cleanupについて尋ねただけの依頼をSkillが拾い、クラス2へ進めてはなりません。helperもdescription非空しか検査しません（[check_docs.py:1522](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1522)）。

   またSkill metadataには権限付与面がなく、Codex hookも未配線です（[AGENTS.md:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/AGENTS.md:18)、[hooks/README.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/hooks/README.md:15)）。現 worktreeの `git --git-common-dir` は workspace外の `/home/SFC/tanab/github/izanagi/.git` でした。Skillは共有ref・兄弟worktreeへの書込権限を取得できません。権限不足時は昇格せず停止・手順引き渡し、と明記すべきです。

## Refuted / confirmed

- F26の `git submodule deinit` 禁止と復旧・事後確認は現行正本にあります（[cleanup-branches.md:27](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:27)、[failures.md:332](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/failures.md:332)）。
- `git branch -d` 使用、`-D` 禁止、拒否時停止は明記済みです（[cleanup-branches.md:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:20)）。ただし finding 1 の primary/main 穴は防ぎません。
- F51の「固定cwdではdirectory削除・pruneをしない」は現行正本にあります（[cleanup-branches.md:41](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:41)）。
- remote branch削除とmain push禁止は現行commandとplanの両方にあります（[cleanup-branches.md:52](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:52)、[s2-plan.md:108](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:108)）。
- Codex hook未配線の認識は正しく、`.codex/hooks.json` も不在でした。
- existing Skill/guardは dev-wave・rulings の2件で、cleanup Skillは未作成です（[check_docs.py:1780](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1780)）。
- 現在の作業木はwave artifact directoryだけが未追跡で、submoduleは初期化済みでした。本レビューでもcleanupは実行していません。歴史的な startup `rc=1→0` は [s1-brief.md:23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s1-brief.md:23) の記録とは整合しますが、指定wave directory内に独立receiptは見当たらず、遷移そのものは再証明していません。

## 裁定待ち候補

1. **共通dispatcherをT-173のscopeへ入れるか。**
   推奨は「入れる」。自己改善契約はcleanup実走での実測時だけcommand編集を許すため（[skill-self-improvement.md:13](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/skill-self-improvement.md:13)）、今回の静的安全 finding を根拠に変更する権限を親だけで仮定しないでください。許可しない場合、Skillはinventory/report-onlyとして出すか、T-173を停止すべきです。

2. **foreign worktreeの削除権限モデル。**
   推奨は、`locked` は常時保持、その他のforeign worktreeもinventory後にexact targetをユーザーが再確認した場合だけ削除です。`/proc` hitなしを承認の代替にしないでください。

3. **Codex sandbox外操作の扱い。**
   推奨は、Skillは権限を昇格させず、shared `.git` または対象directoryへの書込が許されない場合はexact commandと残対象を人間へ引き渡す契約です。

## 総括

**NO-GO。** 段5前のblockerは、primary/main除外欠落、Codexから見えない他セッション、global pruneとTOCTOU、destructive trigger・権限境界、dispatcherを守らないcheckerです。

plan v2では、共通dispatcherを安全化して直接guardする、SkillはCodex固有adapterだけに薄く戻す、descriptionの明示的削除意思・権限非昇格・`/proc`不完全時の縮退をexactに固定する、各安全条項と自己改善gateの独立mutationを追加する、の4点が必要です。dispatcherを変更できない裁定なら、cleanup実行能力を出さずinventory-onlyにしてください。