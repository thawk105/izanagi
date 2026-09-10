結論は **NO-GO** です。指定10ファイルと実装4ファイルの差分を確認しました。新規 Skill 2ファイルは通常の `git diff` に出ないため `--no-index` でも確認しています。編集・pytest 実走はしていません。

### 1. Skill の安全契約が位置・意味に束縛されていない

- 判定: **real**
- 優先度: **blocker**
- 成果物影響: checker green のまま local `main`、primary、foreign worktree を削除候補へ戻せます。並行セッション成果や共有 Git metadata を失い得ます。

checker は SKILL.md 全文への単純な `literal in skill_text` だけです。[check_docs.py:1589](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1589)

例えば次はすべて green のままです。

- 「local `main` と primary worktree は**無条件に保持**」を「**削除候補に含める**」へ変える。[SKILL.md:23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:23)
- `/proc/*/cwd` の miss を「非使用の証拠に**数える**」へ反転する。[SKILL.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:24)
- 本文を削り、全 literal を HTML comment、コードフェンス、否定例へ移す。

独立 pin も token 集合しか固定しておらず、位置・肯定的意味は固定しません。[test_check_docs.py:2210](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2210)

段6 fix では、H2節ごとの完全な安全句・箇条書きに束縛し、comment/fence/引用を満足扱いしない検査が必要です。

### 2. 共通 command の safety guard も恒真 substring のまま

- 判定: **real**
- 優先度: **blocker**
- 成果物影響: F26 手順、submodule deinit 禁止、merged-only 条件を削除しても checker が green になり、worktree/submodule破損や未統合成果の喪失につながります。

command 側も全文への単純な substring 検査です。[check_docs.py:1877](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1877)

実 command では `F26` が複数箇所にあり、F26 の実手順を削除しても後段の言及が残ります。[cleanup-branches.md:27](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:27) [cleanup-branches.md:40](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:40)

また literal 集合は次を直接守っていません。

- `ahead=0` のみ削除
- clean worktreeかつHEAD取り込み済み
- ``git submodule deinit`` 禁止
- `discard_changes: true` 禁止

synthetic command は安全 token を1回ずつ並べただけなので、実 command の重複 decoy を再現しません。[test_check_docs.py:248](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:248)

完全な安全句を該当節へ束縛し、「実効句を削除して同じ token を別位置へ残す」負例を追加すべきです。

### 3. 8負例は first-element checker と予算無効化を殺せない

- 判定: **real**
- 優先度: **must-fix**
- 成果物影響: checker の検出範囲が一部へ縮んでも138件が green のままになり、将来の安全退行を恒久テストが止めません。

adapter 負例は literal tuple の先頭 `AGENTS.md` だけを消します。[test_check_docs.py:1896](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1896) command safety も先頭だけです。[test_check_docs.py:1912](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1912)

したがって、次の変異は静的に survivor です。

- `for literal in literals[:1]`
- `for literal in CLEANUP_COMMAND_SAFETY_LITERALS[:1]`

limits は値を pin するだけで、SKILL.md の byte超過・最長行超過の負例がありません。[test_check_docs.py:2197](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2197) よって Skill 用のサイズ検査本体を削除しても既存負例は赤になりません。[check_docs.py:1545](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1545)

全安全句の削除・移動・反転、byte超過、最長行超過を恒久負例にしてください。

### 4. synthetic fixture は checker 自身から生成され、正例として独立していない

- 判定: **real**
- 優先度: **must-fix**
- 成果物影響: checker と fixture が同じ誤った契約へ動いても baseline green となり、正しい Skill の受理と過剰拒否を区別できません。

description、body literals、metadata のすべてを `check_docs` 定数から生成しています。[test_check_docs.py:295](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:295)

この fixture は「命令として正しい Skill」ではなく literal の羅列です。現在の実 Skill を模した独立した正例 fixtureを置き、節配置まで含めて受理することを固定する必要があります。`test_real_repo_clean` は正例ではありますが、全 repo 依存で赤理由を分離できません。[test_check_docs.py:3228](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:3228)

### 5. exact description と explicit-only policy が自己矛盾

- 判定: **real**
- 優先度: **must-fix**
- 成果物影響: 自然言語で明示的に cleanup を依頼した利用者へ Skill が提供されない一方、description は対応を約束します。通常推論だけで cleanup が進めば Codex overlay を通らない可能性があります。

description は `$cleanup-branches` の明示起動に加え「明示的な cleanup 依頼」でも使うとしています。[SKILL.md:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/SKILL.md:3)

一方、policy false は既定注入を止め、明示 `$skill` でのみ利用できる契約です。[openai.yaml:7](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills/cleanup-branches/agents/openai.yaml:7) [openai_yaml.md:47](/home/SFC/tanab/.codex/skills/.system/skill-creator/references/openai_yaml.md:47) 段4裁定も保持する経路を明示 `$cleanup-branches` としています。[s4-adjudication-plan-v2.md:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s4-adjudication-plan-v2.md:35)

安全側の fix は policy false を維持し、description から自然言語起動の約束を除くことです。

### 6. Skill byte予算が薄い adapter の不変条件に対して緩すぎる

- 判定: **real**
- 優先度: **must-fix**
- 成果物影響: 共通 dispatcher の手順を Skill へ大量複製して第二正本を作っても予算内になり、将来の cleanup 対象・報告内容が drift します。

実測は以下です。

- SKILL.md: 2,878 bytes / 予算5,500
- openai.yaml: 277 bytes / 予算600
- 共通 command: 3,959 bytes / 予算4,000

5,500 bytes は現 Skill に約91%の余白を与え、薄い adapter が共通 command より大きくなれます。[check_docs.py:211](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:211) brief の「手順を複製しない」と整合しません。[s1-brief.md:8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s1-brief.md:8)

現サイズに根拠ある小幅 headroomを加えた値へ締め、増額を独立レビュー対象にすべきです。metadata は exact byte equality が先に全変更を拒否するため、600-byte budget自体は実効証拠になっていません。

### 7. case registry と pin の同時縮小は green

- 判定: **real**
- 優先度: **must-fix**
- 成果物影響: positive control の一分類、または guard call と関連ケースを同時に落とすと、検出力が消えたまま suite が green になります。

8ケース registry とその exact pin が同じテストファイル内の可変な2箇所です。[test_check_docs.py:1953](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1953) [test_check_docs.py:2246](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2246)

両方から同じIDを消すと、期待件数も registry から導出されるため赤になりません。[test_check_docs.py:2084](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2084)

完全な悪意あるテスト削除を in-repo oracle だけで防ぐことはできませんが、少なくとも case IDs、mutation branch、needle map、param collection の exact key集合を別所有面から相互検査する必要があります。

### 8. mutation の期待赤 node が事前登録されていない

- 判定: **real**
- 優先度: **must-fix**
- 成果物影響: 無関係な赤を kill と誤認し、段6 mutation ledgerへ検出力を過大記録できます。

段4のV1は「positive-control test 赤」としか書かれていません。[s4-adjudication-plan-v2.md:79](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s4-adjudication-plan-v2.md:79) `DW-M08` は exact node の事前登録を要求します。[mutation.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/dev-wave/mutation.md:49)

静的に予想されるものは次です。

- V1を全走する場合: cleanup 8ケース中、command safety以外の7 parameter node。
- V2をfixtureへ全域注入すると、多数の `_build_min_repo()` consumerが連鎖赤。単一理由にするなら `test_synthetic_repo_baseline_clean` だけを対象化する。
- V3–V6: 現状では広い `test_real_repo_clean` が主な赤で、専用 node ではない。
- V7: `test_codex_cleanup_branches_skill_contract_pins_exact_surface`。

fix前に exact node/subsetを登録し、専用のfocused nodeを追加すべきです。

### 9. 新規2ファイルは未追跡で、親の `git diff --check` green は4成果物を覆わない

- 判定: **real**
- 優先度: **must-fix（統合時）**
- 成果物影響: checker/testsだけをcommitし、Skill本体がcommitから欠落しても、working tree上の未追跡Skillを `check_docs` が読んで green になり得ます。結果として `$cleanup-branches` は成果物に存在しません。

現在 `tools/check_docs.py` と test は tracked modification、Skill 2ファイルは `??` です。段5報告の `git diff --check` green [s5-author-rerun.md:17](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/output/insights/2026-07-29_t173-codex-cleanup-branches-skill-wave/s5-author-rerun.md:17) は新規2ファイルを検査していません。

commit前に正確な4ファイルをstageし、cached 4-file diff、`git diff --cached --check`、commit tree内の2ファイル実在を確認する必要があります。

### 反証できた攻撃

- **refuted / nit・fix不要:** exact description の検査自体は全文substringではなく、解析した frontmatter fieldとの完全一致です。[check_docs.py:1582](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1582)
- **refuted / nit・fix不要:** implicit policy は full-file byte equalityで固定され、`false` を別位置へ移す逃げはありません。[check_docs.py:1600](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1600)
- **refuted / nit・fix不要:** forbidden `[TODO` は raw SKILL.md 全域で検査され、comment/fenceへ移しても拒否されます。[check_docs.py:1594](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1594)
- **refuted / nit・fix不要:** helper の既存consumer後方互換は成立しています。新引数はkeyword-onlyかつ既定値付きで、既存dev-wave/rulings呼出しのdescription・forbidden挙動は変わりません。[check_docs.py:1488](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1488)
- **refuted / nit:** 現 metadata のinterface 3 fields、quoted strings、`$cleanup-branches` default prompt、policy構造は仕様に適合します。ただし generator はpolicyを生成せずinterfaceだけを書きます。[generate_openai_yaml.py:40](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py:40) [generate_openai_yaml.py:171](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py:171) 段4が明示した「生成後にpolicyを決定的追記」の二段契約なので現在値のblockerではありませんが、単一producerがない保守上のnitは残ります。
- **refuted / nit:** 現在のcanonical 2ファイルが予算・exact metadata・placeholder検査から過剰拒否される事実はありません。問題は、独立した正しい fixture がなく、今後の過剰拒否をfocusedに検出できない点です。

## 総括

**NO-GO**。段6 fix対象は、①Skill/commandのsubstring guardを節・完全安全句へ束縛、②literal移動・否定反転・duplicate decoy・全句・limitsの恒久負例追加、③policy falseとdescriptionの整合、④Skill予算の縮小、⑤case oracleとmutation期待nodeの独立固定です。統合時には新規2ファイルを含むcached 4-file diffも必須です。