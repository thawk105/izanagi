結論は **NO-GO** です。Skill本文の安全修正は概ね成立していますが、exact-clause checkerに安全極性を再びgreenにできるblockerが残っています。

### accepted findings 1〜9

| finding | 裁定 | 根拠 | 残る成果物影響 |
|---|---|---|---|
| 1. explicit-only整合 | closed | descriptionは明示 `$cleanup-branches` 専用、metadataはimplicit=false。[SKILL.md:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:3) [openai.yaml:7](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/agents/openai.yaml:7) | なし |
| 2. 全eligibility再検査 | closed | ahead/cherry、clean、HEAD包含、recent、lock、canonical path、main/primary、ownership/foreign、process residencyを各破壊操作直前に再評価し、unknown/change/new residencyで停止。[SKILL.md:27](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:27) | なし |
| 3. real prune非実行 | closed | dry-runを報告専用とし、real pruneは人間へ移管。[SKILL.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:31) | なし |
| 4. H2/exact clause・comment/fence | **partial** | 単純comment/fence、句重複、H2重複は拒否する。一方、H2本文をwhitespace正規化してsubstring countしており、blockquote、indented code、非規範H3、危険な但書、fence-info edgeを受理する。[check_docs.py:779](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:779) [check_docs.py:812](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:812) [check_docs.py:868](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:868) | checker greenのままmain/primary保持、foreign保護、real-prune禁止を危険側へ上書きできる |
| 5. 全句individual controls | closed | Skill 12句・command 10句をstable ID付きで個別除去するため、first-element-only退行は生存しない。[test_check_docs.py:2579](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2579) | parserの意味的穴はfinding 4に残る |
| 6. 独立fixture | closed | Skill・metadata・command本文はtest側の独立literalで、checker定数から生成していない。[test_check_docs.py:134](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:134) | なし |
| 7. byte/line予算 | closed | Skillは3004/3100 bytes・205/210 chars。CB-N15/N16がbyteとlineを別理由で攻撃する。[check_docs.py:217](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:217) [test_check_docs.py:2057](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2057) | metadata予算はexact bytesと重なるが、安全上の穴ではない |
| 8. registry相互pin | **partial** | production/testのID集合は一致するが、16件がparameter collectionへ含まれることをmeta-testが検査していない。[test_check_docs.py:2161](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2161) [test_check_docs.py:2629](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2629) | spread 1行の脱落でfile/metadata/limit等16負例が全消失する |
| 9. mutation期待node | **partial** | fix報告はrange表記のnode族のみで、V1〜V7ごとのfully-qualified期待node、subset、erratumが未登録。[s6-fix.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s6-fix.md:31) 実ファイルを変えるV3〜V6は依然として広い `test_real_repo_clean` が主な検出先。[test_check_docs.py:3558](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:3558) | 無関係な赤をkillと誤認でき、mutation ledgerの証明力が確定しない |

### 新しいreal findings

1. **blocker / scope: `tools/check_docs.py` + `test_check_docs.py`**

   Exact clauseは「exact block」ではなく、正規化H2本文中のsubstringです。インメモリ攻撃では次をfindingなしで受理しました。

   - 危険なlive bullet + canonical安全句をblockquoteへ置く
   - canonical句へ「ただし削除する」を追記
   - indented code、非規範H3内へ移す
   - `````text <!--`` のinfo string後に置いたfenced clause

   実Skillのblockquote攻撃は **3073/3100 bytes、205/210 chars** のままです。command側も非exactなfrontmatter descriptionを短縮すれば **3898/4000 bytes、87/110 chars** で同じ攻撃が成立します。

   **成果物影響:** checker greenのまま破壊Skillへmain/primary/foreign削除やreal prune指示を導入でき、worktree成果と共有Git metadataを失わせ得る。

2. **must-fix / scope: `test_check_docs.py`**

   `_CLEANUP_BRANCHES_GUARD_CASES` のspreadをインメモリで除去しても、既存2本のregistry meta-testは通過し、**16/16件がparameter collectionから消失**しました。

   **成果物影響:** checker branchが退行しても恒久負例が実行されず、安全保証を過大記録する。

3. **nit / scope: checker説明・段7 docs整合**

   checkerは今や義務本文をexact pinしますが、冒頭と自己改善正本は「文言と意味はlintしない」と記載したままです。[check_docs.py:7](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:7) [skill-self-improvement.md:83](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/skill-self-improvement.md:83)

   **成果物影響:** 即時の削除リスクはないが、checkerの責務境界を誤認させる。

### parser・consumer・規律5の裁定

- 重複句と重複H2は現実装では正しく拒否します。ただし、その分岐を固定する恒久controlはありません。
- simple comment/fenceは拒否しますが、fence opener判定よりHTML comment処理が先なのでinfo-string edgeで破れます。
- `re.sub(r"\s+", " ", ...)` は「改行・indentだけ」より広く、indented codeの構造まで消します。
- 既存dev-wave/rulings consumerへの受理集合回帰は見つかりませんでした。追加引数はkeyword-only・既定値付きで、新parserの呼出先もcleanup Skill/commandの2面だけです。
- checker 307行変更・test 523行変更は、独立fixtureと22句controlを含む限定surfaceなので、仕組み自体を規律5違反とは裁定しません。ただし現状はLOCに見合う検出力を達成していません。汎用Markdown parserへ拡張せず、対象H2の許可されたtop-level block集合を構造付きでexact照合する狭い修正が妥当です。

なお、新規2ファイルはintent-to-addの空blobで、cached内容はまだありません。accepted finding 10のcached 4-file確認は引き続き親統合事項です。

編集、pytest、cleanup、check_docs実走はしていません。実施したのは全ファイル・全差分の読取り、`python -B`によるファイル非生成のインメモリ攻撃、最終`git status`確認だけで、作業状態は不変です。

## 総括

**NO-GO。**

再fixのexact対象は次の4点です。

1. H2本文substringではなく、対象H2の許可top-level block集合を構造込みでexact照合し、blockquote・indented code・H3・追加但書・追加危険句を拒否する。
2. fence openerをcomment処理より先に判定し、fence-info `<!--` bypassを閉じる。duplicate H2/句、合法rewrapを含む恒久controlsを追加する。
3. registry meta-testで16 IDの `_COMMAND_GUARD_CASES` 収載と、needle/count key集合をexact照合する。
4. mutation本走前にV1〜V7ごとのfully-qualified期待node/subsetとerratumを明記する。cached 4-file確認はその後に行う。