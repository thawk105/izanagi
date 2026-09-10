## 総括

- 絞り込みは限定反証する。carry compact 化自体は支持するが、「これが最大の安全削減箇所」は不成立。
- 最重要 1: 単独 reviewer が full-wave Skill に再突入し、最低 25,663 bytes の管理者用文脈を余分に読む。
- 最重要 2: P1′の現末尾に対する削減は 5,214 bytes・34.38%。59% は占有率で、rotation 2.5 倍改善は不成立。
- 最重要 3: `CLAUDE.md` と `rulings.md` の読者契約がプランから漏れ、compact 行を実体本文へ解決できない。

## B-01 — より大きく安全な削減箇所がある

[CLAUDE.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/CLAUDE.md:24) は read-only review を class 1 とする一方、[dev-wave/SKILL.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.agents/skills/dev-wave/SKILL.md:12) は単独段 worker か manager かを分けず、無条件に class 3 起動、worklog、dispatcher、自己改善契約へ進める。本レビューでもこの経路が実際に発火した。

単独の段 2/3/6 worker に不要な最低読了量は次の通り。

- worklog 末尾: 15,167 bytes
- `.claude/commands/dev-wave.md`: 8,907 bytes
- `skill-self-improvement.md` の発火 gate + dev-wave 終端: 1,589 bytes
- 合計: **25,663 bytes/reviewer**。さらに manager 用 dispatch 抜粋が最大 5,650 bytesある。

これは [D94:4203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/decisions.md:4203) の「節を別ファイルへ移しても 0 bytes」とは別問題である。Skill 冒頭に「親から単一段 worker/reviewer として dispatch 済みなら class 1 とし、親 prompt の必読だけに従う」分岐を置けば、安全義務を削らず carry 案の約5倍を削減できる。

**成果物影響:** certified 選択等は不変。reviewer の無関係な可変状態による汚染と入力文脈だけを減らす。段 4 の別 scope 候補にすべきである。

## B-02 — campaign の session 再利用除外は支持、cache 一括除外は根拠不足

session 再利用の除外は正しい。[claude_projected_provider.py:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/campaign/claude_projected_provider.py:215) は `--no-session-persistence` を指定し、同 [298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/campaign/claude_projected_provider.py:298) と [308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/campaign/claude_projected_provider.py:308) が一 turn・session ID 重複を拒否する。

ただし「cache 化も品質を落とす」は広すぎる。会話・出力の再利用ではなく、byte-identical な固定 prompt prefix の cache は fresh session と直交する。同 [156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/campaign/claude_projected_provider.py:156) が毎回組み立てる固定 effective prompt は4役合計 **36,713 bytes**。[p3_autonomous_workload_trial.py:1719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/campaign/p3_autonomous_workload_trial.py:1719) の既定3 workloadの正常経路では110,139 bytes送られ、初回以外の同一 prefix は **73,426 bytes**である。

一方、repo 内には prefix cache の提供能力・hit・token会計の証拠がないため、これは実現済み削減として数えてはならない。出力 cache、session reuse、payload を欠く cache key は引き続き禁止でよい。

なお brief の planner/coder/critic/selector 列挙と、現行 [ROLE_FILES:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/campaign/p3_autonomous_workload_trial.py:166) の planner/coder/**auditor**/critic は一致していない。最大固定 prompt は auditor の18,917 bytesである。

**成果物影響:** byte-identical prefix cacheなら出力意味は不変。ただし platform 実証と cache 使用量 provenance がない現段階では裁定候補に留める。

## B-03 — 件数と削減量の再計測

[brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/token-economy/brief.md:8) と [s2-plan.md:152](/work/1/SFC/tanab/dev-wave-jobs/token-economy/codex/s2-plan.md:152) を独立に数え直した。

| 対象 | 実測 | 判定 |
|---|---:|---|
| `docs/worklog.md` | 98,391 bytes / 2,045行 | 一致 |
| exact旧carry | 1,671行 / 63,498 bytes | planが正しい。briefの1,673行は書式説明2行を含む |
| 末尾entry、見出しからEOF | 15,167 bytes | brief/planの15,168との差1 byteは境界改行の数え方 |
| 末尾exact旧carry | 237行 / 9,006 bytes | 一致、末尾の59.3789% |
| P1へ置換 | 8,531 bytes | **6,636 bytes削減、43.7529%** |
| P1′へ置換 | 9,953 bytes | **5,214 bytes削減、34.3773%** |

したがって、brief の「6,399 bytes」は237行すべてで1 byteずつ過小であり、段2の6,636が正しい。ただし採用案はP1′なので、land判断に使う数字は5,214である。「59%」は削除率でなく、ID・ordinalを含む旧carryブロックの占有率である。

さらに [worklog.md:1754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:1754) の active T は **245件**であり、237件ではない。237本は旧carry、残り8件は実体本文である。[spool_fold.py:1327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1327) は未操作の全activeを次entryでcarry化するため、無操作なら次entryの差は P1′で `245×22 = 5,390 bytes`。実際の式は `22 × そのentryでcarryされる件数` であり、固定5,214ではない。

削除される日本語句は過去entryから通常セッションへ再掲されないため、読者契約を直せば5,214 bytesはそのまま最新tail読了量から消える。ただしUTF-8 bytesを入力token数と同一視はできず、token実測はまだない。また [CLAUDE.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/CLAUDE.md:38) 上、worklogを必ず読むのはclass 3で、class 2全件ではない。

**成果物影響:** 台帳の意味は不変だが、削減率・対象セッション数・投資判断の見積りが変わる。実tokenは親の受入計測で別記すべきである。

**nit:** 15,167対15,168の1 byte差に成果物影響はない。

## B-04 — 読者契約の追随が2面不足

必要な追随面は次の通り。

| 面 | 判定 | 壊れ方 |
|---|---|---|
| [docs/worklog.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:18)、[26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:26) | 必須・plan記載済み | reader向け現行書式と旧書式互換を定義する |
| [docs/spool/README.md:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/README.md:86) | 必須・plan記載済み | producerの生成形が旧記述のままになる |
| [docs/spool/worklog/README.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/worklog/README.md:81) | 必須・plan記載済み | base digestが新stubを遡る契約を説明できない |
| [CLAUDE.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/CLAUDE.md:38) | **必須・plan漏れ** | class 3は冒頭規約を読まずtailだけ読むため、`(181)`を参照ordinalと認識できない |
| [.claude/commands/rulings.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.claude/commands/rulings.md:13) | **必須・plan漏れ** | 旧「変わらず」だけをcarryと認識し、新stubを実体へ遡れず裁定待ちを落とす |
| [docs/README.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/README.md:22) | 変更不要 | 既に書式正本をworklog冒頭へ委譲している |
| [.claude/commands/dev-wave.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.claude/commands/dev-wave.md:13) | CLAUDE追随なら変更不要 | 共通解決手順を入口へ重複させない |
| `cleanup-branches.md` | 変更不要 | carry consumerではない |

`CLAUDE.md` にはexact書式を複製せず、「compact carryの行内ordinalを指すentryへ、実体itemまで遡る。書式正本はworklog冒頭」とだけ置くのがよい。`rulings.md` も同じ正本を指す形へ置換すれば二重正本を避けられる。

P1′は、従来は実体として受理できた `- [T-NNN] (正整数)` をcarry予約形へ再分類する。現行worklogと全archiveを走査した結果、このexact形は **0件**だったため移行衝突はない。ただし新規書式規約で予約形だと明記しないと、将来の短い実体項目がcarryとして誤解決される。

**成果物影響:** 漏れるとAIがTの実体を読まず、誤ったタスク選択・裁定漏れ・誤base生成を起こす。worklog整合性へ直接影響する。

## B-05 — 予算・rotationとの干渉

[check_docs.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:167) の文書予算では、`rulings.md` は現在 **4,988 / 5,000 bytes**で余裕が12 bytesしかない。B-04の追随は追記ではなく、既存13〜15行の同長以下への置換が必要である。段2プランはこの制約を扱っていない。

worklogは個別最長行予算の対象ではなく、[check_docs.py:3332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:3332) の100,000-byte rotation閾値だけが関係する。現在余裕は1,609 bytesで、compactな245 carryだけでも3,920 bytesあるため、**次foldは新旧どちらでもrotationする**。

rotation頻度の比は、非carry bytesをB、carry件数をCとすると、

`(B + 38C) / (B + 16C)`

で、最大でも `38/16 = 2.375`。現末尾をそのまま比較すれば1.5239倍であり、briefの「約2.5倍」は全entry bytesから導出されていない。

rotationが遅れても検査蒸発はない。[check_docs.py:1506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1506) は現行の全隣接遷移を、同 [1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1526) と [1613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1613) は全archive内部・archive間・archive/current境界を閾値と無関係に検査する。`check_docs.py`本体を無改変とする判断は正しい。

**成果物影響:** 検査適用範囲は変わらない。ただし`rulings.md`を安易に追記すると予算赤、rotation効果の過大記録は運用判断を誤らせる。

## B-06 — 段2プランの手順整合

file:line、関数・欄、並列依存を照合した結果、次は問題なかった。

- `carry_re`、`substantive_digest`、`prior_ordinal`、`_global_ordinal_entries` は記載位置に実在する。
- archive読込→resolver→全entry描画→rotationの順序も [spool_fold.py:1723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1723)、[1792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1792)、[1849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1849) と一致する。
- briefは実装面を一所有単位としており、planも依存するproducer/resolverを並列所有に分けていない。

実手順上の不足は、B-03の245件、B-04のconsumer 2面、B-05の12-byte予算、および次節の変異漏れである。これらを反映したplan v2が必要。

**成果物影響:** staleなfile:lineや架空関数による実装不能はないが、現planのままでは読者契約と予算検査が統合時に破れる。

## B-07 — 変異事前登録

以下は、既存期待値をcompactへ更新した後なら既存テストが確実にkillする。

| 変異 | killする既存テスト |
|---|---|
| producerを旧形/P1へ戻す、carry順序・件数を壊す | [test_spool_fold.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:441) のbyte exact、[485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:485)、[1353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1353) |
| compactを実体digestとして扱う | [test_parallel_new_then_existing_update:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:502)。最初のfoldをapplyし、元実体baseで次foldするため認識漏れをkillする |
| legacy分岐を削る | [global carry:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:257)、[legacy-only拒否:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:289)、[real corpus:1592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1592) |
| activeを暗黙脱落・並べ替え | byte exact N08と既存conservation postcondition |

次は既存テストをすり抜ける。段2の新設案で塞がるものと、なお不足するものを分ける。

| すり抜ける変異 | 最小テスト |
|---|---|
| `prior_ordinal`を`ordinal - 1`にする | plan記載のordinal gap fixture |
| 2 fragment間の`prior_ordinal = ordinal`を削る | plan記載の即時prior 2-entry fixture |
| compact missing entry/taskをstub digestへ救済 | plan記載のmissing entry/task各1件 |
| compactのself/future参照を許す | plan記載のself/future負例 |
| rotation後のarchive参照を解決しない | plan記載のapply→次foldまで行うarchive境界テスト |
| stub自身のbaseも受理する | plan記載の`compact_stub_digest_cannot_satisfy_mutating_base` |
| `fullmatch`を`match`へ変え、先頭がcompact風の複数行実体をcarry扱いする | **plan漏れ**: `- [T-001] (1)\n  詳細\n`全体のdigestで更新が成功するテスト |
| compact側だけT ID/ordinalを3桁固定する | **plan漏れ**: T-1000かつordinal 1000のcompact chain回帰 |
| `CLAUDE.md`/`rulings.md`追随を落とす | **plan漏れ**: reader契約がworklog冒頭のcompact解決規約を指す構造テスト、または段6の必須docs敵対検査 |

既存 `test_parallel_new_then_existing_update_uses_substantive_base_digest` はcompact分岐削除を既にkillできるため、変異matrixで明示的に帰属させ、fix時に弱めてはならない。

**成果物影響:** 未登録の2コード変異はbase guardの意味を壊し、誤更新または未解決carryのfail-openを許す。reader契約変異は裁定漏れを起こす。

## 対象外判断

- D94の単なるファイル外出しは削減0という判断を支持する。
- archive遡及圧縮は凍結履歴を変え、通常セッションはarchive全文を読まないためscope外を支持する。
- active Tの整理も意味判断を要するため自動削減対象外を支持する。ただし件数は237ではなく245へ訂正が必要。

read-only静的検査のみ実施した。pytest、`check_docs.py`、変異は走らせておらず、テスト緑は主張しない。