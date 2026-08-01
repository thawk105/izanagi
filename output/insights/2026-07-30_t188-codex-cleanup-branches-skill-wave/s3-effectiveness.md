指定10ファイルはすべて全文読了しました。編集・Skill 初期化・pytest/checker 実走はしていません。静的判定は、現行 plan のままでは段5へ `NO-GO` です。

## Real findings

1. Blocker — 実 command に存在しない変換を固定し、実在する製品差を落としている

   Plan は `/cleanup-branches` → `$cleanup-branches` を adapter 契約にしますが、command 内に `/cleanup-branches` は存在しません。実在する差分は `$ARGUMENTS` と、Claude 固有の `ExitWorktree` / cwd 非持続です。[s2-plan.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:49)、[cleanup-branches.md:7](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:7)、[cleanup-branches.md:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:38)、[cleanup-branches.md:41](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:41)

   現案の invocation mutation は、実行効果ゼロの文を消して checker が赤になるだけです。これを削り、次を明示・pin すべきです。

   - Codex で `ExitWorktree` が使えると仮定しない。
   - cwd を永続的に main checkout へ移せない場合は F51 縮退へ進み、自 worktree の削除・prune を行わない。
   - command 不在・読取不能・矛盾時は推測せず停止する。

2. Blocker — trigger description が未確定で、checker は利用可能性を検査しない

   Skill の発火を決めるのは frontmatter の `description` ですが、plan は意味の箇条書きだけで exact 文を決めていません。[skill-creator/SKILL.md:79](/home/SFC/tanab/.codex/skills/.system/skill-creator/SKILL.md:79)、[s2-plan.md:37](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:37)

   checker は description の非空しか見ず、独立 pin も file set・adapter literals・openai.yaml だけです。[check_docs.py:1522](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1522)、[s2-plan.md:139](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:139)

   したがって、発火しない任意の非空 description でも全検査が緑になります。exact description 定数を設け、frontmatter の値として比較する必要があります。「明示的に local branch/worktree の棚卸し・掃除を依頼した場合」に絞り、一般的な Git 相談を削除権限と解釈しない文言が必要です。

3. Blocker候補 — implicit invocation 方針を黙って default=true にしている

   `policy.allow_implicit_invocation` は未指定時 true です。[openai_yaml.md:47](/home/SFC/tanab/.codex/skills/.system/skill-creator/references/openai_yaml.md:47) 現 plan の exact YAML には policy がなく、自然言語の「同等依頼」でも発火させる方針を暗黙採用しています。[s2-plan.md:40](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:40)、[s2-plan.md:67](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:67)

   クラス2の削除 Skill なので、これは exact bytes を凍結する前に明示裁定すべきです。推奨は Claude slash command と同じ明示起動寄りの `allow_implicit_invocation: false`。自然言語起動を採るなら、「ユーザーが明示的に local cleanup を依頼した場合」に限定し、負の forward-test が必要です。なお現 generator の許可 interface key に policy はないため、false 採用時は生成後の決定的な追記方法も plan に要ります。[generate_openai_yaml.py:40](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py:40)

4. Major — 「共通正本へ委譲」と安全手順の複製が自己矛盾している

   Brief は Skill に手順を複製しないとしていますが、plan は F26、F51、remote delete/main push、自己改善を再掲して literal 固定します。[s1-brief.md:8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s1-brief.md:8)、[s2-plan.md:53](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:53)

   これらは既に command の正本にあります。[cleanup-branches.md:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:35)、[cleanup-branches.md:54](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:54)、[cleanup-branches.md:60](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:60)

   Skill には「Codex 固有の読み替え」だけを残すべきです。共通安全手順を複製すると、将来 command だけが改訂されても checker は stale adapter を緑にします。

5. Major — 独立 pin は limits・trigger・negative-case 登録を固定しない

   Plan の独立 pin は3面だけで、`TextLimit(3000/500)` の値を固定しません。[s2-plan.md:83](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:83)、[s2-plan.md:139](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:139)

   さらに positive-control の parameterization と期待件数は同じ `_COMMAND_GUARD_CASES` から導出されます。[test_check_docs.py:1895](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1895)、[test_check_docs.py:2006](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2006) guard callと cleanup case登録を同時に落とすと、現案の surface pin は殺せません。

   独立 pin に次を追加すべきです。

   - exact `SKILL_LIMITS` の path→値
   - exact frontmatter description
   - cleanup 用 positive-control case ID 集合
   - forbidden initializer placeholder、少なくとも `[TODO`

6. Major — mutation matrix の「単一理由」と実際の finding が一致しない

   M6 で metadata を budget+1 にすると、byte budget と exact interface mismatch の2件が同時発火します。[check_docs.py:1488](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1488)、[check_docs.py:1530](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1530) 「各変異は単一理由」という plan と不一致です。[s2-plan.md:147](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:147)

   M6 は SKILL.md だけを改行 padding で3001 bytesにしてください。M9 は mutation ではなく survivor/正例として別欄に分けるべきです。また、一時 mutation の M3/M4/M5 は永久負例5件より広いため、個々の変異・期待件数・実行 nodeid を列挙しないと「事前登録」になりません。

7. Major — quick/focused/full は静的契約には概ね有効だが、実利用には不足する

   `quick_validate.py` は SKILL.md の frontmatterしか見ず、本文 TODO、`agents/openai.yaml`、trigger 実効性を検査しません。[quick_validate.py:15](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/quick_validate.py:15) initializer は大きな TODO template を生成します。[init_skill.py:26](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/init_skill.py:26)

   追加が必要です。

   - initializer placeholder 不在の恒久検査
   - fresh read-only context での明示 `$cleanup-branches` discovery smoke
   - implicit=trueなら、自然言語の明示的 local cleanup 正例と、remote delete/main push 依頼の負例
   - Git 操作は開始せず、dispatcher path・adapter変換を報告した時点で停止する smoke
   - 新規未追跡ファイルも見るため、stage後の `git diff --cached --check`。現 plan の `git diff --check` だけでは新規 Skill を確実に対象化しません。[s2-plan.md:201](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:201)

8. Major — T-172 の T-058/T-059 発火記録が既に欠落している

   Phase の現記録は T-058/T-059 に T-171 までしか載せていません。[phase3.md:514](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/phase3.md:514)、[phase3.md:515](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/phase3.md:515) 一方、直後の T-172 完了記録と worklog は、同型の checker guard・負例・surface pin を追加したと明記しています。[phase3.md:519](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/phase3.md:519)、[worklog.md:970](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/worklog.md:970)

   Plan は T-173 だけを追記するため、この欠落を温存します。[s2-plan.md:169](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s2-plan.md:169) T-172 を遡及的に発火記録へ追加し、coverage/mutation は証拠がなければ「未観測」と正直に書くべきです。T-173 完了記録も、forward-testを行わないなら「runtime discovery・implicit trigger・実 cleanup は未実走」と限定してください。

## Refuted

- initializer の使い方自体は正しいです。指定先は明確で、既存ディレクトリを上書きせず、SKILL.md と openai.yaml を生成し、resources未指定なら追加資材を作りません。[init_skill.py:275](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/init_skill.py:275)、[init_skill.py:287](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/init_skill.py:287)、[init_skill.py:299](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/init_skill.py:299)

- UI YAML は構文面では妥当です。short description は実測36文字で25–64制約内、default prompt は `$cleanup-branches` を明示しています。[openai_yaml.md:34](/home/SFC/tanab/.codex/skills/.system/skill-creator/references/openai_yaml.md:34)

- command は実測3959 bytesで、4000-byte上限まで41 bytesという親観測は正しいです。[check_docs.py:148](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:148) 本 wave で変更しない判断も妥当です。

- generic helper は、狭い主張なら再利用可能です。recursive file closure、regular/UTF-8、budget、frontmatter、literal、exact metadataを実装済みです。[check_docs.py:1433](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1433)

- M7 は cleanup case が登録されたままなら guard call削除を殺せます。M8も現在記述された「constants＋fixture同時縮小」だけなら独立 literal pin が殺します。[test_check_docs.py:2138](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2138) 問題は、それより広い同時縮小を plan が固定していないことです。

## 裁定待ち候補

1件です。

- `allow_implicit_invocation` を false にして `$cleanup-branches` 明示起動専用にするか、true のまま明示的な自然言語 cleanup 依頼にも発火させるか。

推奨は false です。破壊的なクラス2操作であり、元の Claude slash command と権限面を揃えられます。true を選ぶ場合は exact trigger description と正例・負例の fresh-context forward-testを段5/6の必須受入にしてください。

## 総括

`NO-GO`。段5前の blocker は、①恒真な `/cleanup-branches` 変換を実在する `ExitWorktree` adapterへ置換、②exact trigger descriptionと implicit invocation裁定、③limits・case registry・descriptionを含む独立 pin、④mutation単一理由の是正、⑤T-172発火記録の補正です。

Plan v2では、共通手順の複製を削ってCodex固有変換だけを残し、read-only discovery forward-test、placeholder検査、staged diff-checkを追加してください。これらが入れば段5へ進めます。