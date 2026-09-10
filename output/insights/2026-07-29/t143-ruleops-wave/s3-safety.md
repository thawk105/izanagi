## 前提検証

指定7ファイルはすべて絶対パスから読了した。`docs/decisions.md` は索引から D94・D96 のみを参照した。依頼はクラス1の read-only 敵対レビューとして扱った。

静的確認時点は `HEAD=eaa2dd2ae806983e186672c94faa738992c77ce4`、non-shallow。編集・commit・pytest・`tools/run_tests.py`・checker は一切実行していない。したがって緑の受入結果はない。

## findings

### A-1 — BLOCKER: typed receipt が実行証拠ではなく自己申告 JSON で成立する

- 根拠: receipt の必須内容は `candidate_excluded=true`、`rc=0`、`KILLED`、失敗 node 等の結果フィールドに留まり、実行 argv、collection/execution/skip 数、変異 patch、注入確認、復元 bytes、受理方向を束縛していない。[s2-plan.md:77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:77) [s2-plan.md:124](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:124)
- 既存台帳は「単に赤いだけでは kill でない」、注入一意性、実変更、復元確認を要求している。[backlog-guard-mutation-ledger.json:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-20_backlog-guard-mutation-ledger.json:5) また過剰決定変異を単独検出力の証拠から除外している。[t094-placeholder-gate-mutation-ledger.json:552](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-25_t094-placeholder-gate-mutation-ledger.json:552)
- 放置時の成果物影響: 未実走、全 skip、collection error、無関係な赤、捏造 receipt でも候補 package が通り、唯一の test を退役可能に見せられる。
- 最小修正: receipt に実行 argv、producer/blob、collection・executed・skip 集合、候補同時除外 manifest、変異前後 blob/diff、期待する受理方向、注入・復元確認、失敗理由を必須化する。過剰決定、import/collection failure、可用性 kill は代替証拠から除外し、保存 replacement node だけで判別する変異を最低1件要求する。

### A-2 — BLOCKER: test の同時候補循環を拒否していない

- 根拠: replacement node は「当該候補 file 外」であればよく、他の test 候補であることは禁じていない。[s2-plan.md:67](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:67) テスト案も自己 replacement だけを拒否し、同時候補拒否は insight 側にしかない。[s2-plan.md:123](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:123) [s2-plan.md:125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:125)
- 放置時の成果物影響: A を除外した receipt では B、B を除外した receipt では A が代替となり、両方の個別 package が通る。両方を退役すると防壁が消える。
- 最小修正: ledger 全候補を一つの集合として検査し、全候補を同時除外した receipt を要求する。replacement guard/node/receipt/source は候補集合のどの要素にも属してはならない。

### A-3 — BLOCKER: reference closure が非空 package 自身と矛盾する

- 根拠: ledger は候補の `path` を必ず含み、receipt も候補を束縛する一方、他の HEAD blob に target の full path または basename があれば拒否する設計である。[s2-plan.md:62](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:62) [s2-plan.md:77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:77) [s2-plan.md:86](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:86)
- ledger/receipt を除外しなければ、commit 済みの非空 ledger は自分自身への hit で常に赤になる。暗黙に除外すれば、何を evidence-package reference として免除するかが未定義になる。
- さらに full path/basename 検索は、分割文字列、相対 alias、旧 rename 名、hash 参照、glob consumer を閉じない。実在 checker にも `output/insights/*.md` の動的列挙がある。[check_docs.py:776](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:776) [check_docs.py:814](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:814)
- 放置時の成果物影響: validator が恒常的に拒否するか、場当たり的除外によって本物の consumer を見落とす。
- 最小修正: ledger とその exact typed receipt だけを「package 内参照」として明示除外し、除外 hit も出力する。それ以外は `literal_hits` と呼び、`reference closure` や安全証明とは呼ばない。split path、rename、同時候補、package 自己参照の境界テストを置く。

### A-4 — MUST: semantic search と Git history を完全列挙として扱えない

- 根拠: query は候補作成者が選び、履歴検査は HEAD 祖先の `git log -S` とされている。[s2-plan.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:31) [s2-plan.md:68](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:68) `-S` は文字列出現数が変わる差分を探すもので、全履歴 snapshot の意味 hit、別表現、rename alias、HEAD 祖先外の deleted history を列挙しない。
- shallow だけを拒否するが、既存の履歴証明実装は replace refs と grafts が object 解決・親関係を書き換えるため、無効化と存在拒否を行っている。[s8b_ratified_freeze.py:282](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:282) [s8b_ratified_freeze.py:320](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:320)
- 放置時の成果物影響: 無意味な query や改変された履歴 viewから「実発火なし」を作れ、D94 の意味検索条件を過大充足する。[decisions.md:4216](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/decisions.md:4216)
- 最小修正: path、旧 path、test symbol、主要 assertion/diagnostic token を機械導出した必須集合とし、自由語は人間レビュー対象とする。replace refs/grafts を拒否し、Git query を harden する。履歴範囲と `-S` の限界を receipt に明記し、「完全列挙」ではなく「指定 token の観測 hit」とする。

### A-5 — MUST: receipt の祖先 HEAD 許容では証拠 epoch が閉じない

- 根拠: receipt は run の `head` を持つが、テスト案は「非祖先」を拒否するだけで、現在 HEAD との一致や許容差分を要求していない。[s2-plan.md:77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:77) [s2-plan.md:124](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:124)
- 放置時の成果物影響: candidate/guard/replacement の直接 blob が同じでも、runner、pytest config、import dependency、共通 fixture が後続 commit で変わった古い receipt を再利用できる。
- 最小修正: `evaluated_tree` を固定し、receipt 導入 commit までの差分を receipt/ledger/docs の exact allowlist に限定する二段 commit 契約を置く。限定できなければ現 HEAD で再走を要求する。

### A-6 — MUST: `authority: none` は「削除可能な派生物」を意味しない

- 根拠: `output/README.md` は marker を「可変状態の正本ではない」宣言として要求するだけで、証拠価値の不存在とはしていない。また再現根拠は insight に残し得る。[output/README.md:46](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/README.md:46) [output/README.md:71](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/README.md:71)
- 実例として D96 の材料正本は `authority: none` / `default_effect: no-state-change` の insight である。[decisions.md:4294](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/decisions.md:4294) [2026-07-26_t106-t107-parser-authoritative.md:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-26_t106-t107-parser-authoritative.md:3)
- marker 構文も統一されていない。さらに「marker が欠落」と指摘する本文自体が marker 文字列を含むため、簡易検索では偽 marker になる。[s6-r2.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t139-ladder-verbatim/s6-r2.md:15)
- `artifact_class: derived-report` は候補 ledger の自己申告であり、source pin も任意の tracked path を引用すれば構造上は満たせる。[s2-plan.md:72](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:72)
- 放置時の成果物影響: primary evidence、mutation/provenance JSON、再現不能な口頭相談記録を派生 report と誤分類し、proof/material chain を失う。
- 最小修正: `state_authority` と `retention_class/reproducibility` を分離する。v1 の JSON・provenance・mutation receipt は inventory-only とし、Markdown は byte 先頭の正準 frontmatter のみ認識する。legacy 分類は target 外の human-reviewed blob-pin 台帳を用い、source path citation は「由来の証明」ではなく構造情報と明記する。

### A-7 — MUST: D96 の手続境界が plan に入っていない

- 根拠: plan は D94 だけを読んだと明記し、受理集合変更を scope 外と書いている。[s2-plan.md:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:3) [s2-plan.md:163](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:163)
- D96 は受理集合を変える改修に、新規 D と境界テストの同時更新を要求し、意味論の機械保証は新設しないと明記する。[decisions.md:4271](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/decisions.md:4271) [decisions.md:4281](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/decisions.md:4281)
- 放置時の成果物影響: 有限個の mutant receipt を受理集合同値の証明と誤認し、実際には gate を緩める test retirement が D96 を通らない。
- 最小修正: RuleOps 文書に D96 の人間 checkpoint を置く。receipt は受理集合不変を証明しないと明記し、潜在的変更なら新 D と境界テストを同じ変更単位で要求する。D96 に反して意味判定を validator へ実装しない。

### A-8 — MUST: CLI・ledger・receipt・docs・tests が一つの実効 gate になっていない

- 根拠: plan は runner・既存 checker・hooks へ接続しない。[s2-plan.md:113](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:113) 境界テストは synthetic repo 中心で、実 ledger の検査は standalone command に依存する。[s2-plan.md:119](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:119) [s2-plan.md:150](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:150)
- 既存全走 gate は未 stage 削除だけを止め、削除を stage すれば続行するよう案内する。[run_tests.py:453](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:453) [run_tests.py:499](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:499)
- 放置時の成果物影響: populated ledger や staged retirement が RuleOps 未検査のまま親 brief の「全走受入」を通る。空 ledger の `check rc=0` も安全承認に見える。
- 最小修正: full acceptance から現行 tracked ledger/receipt の少なくとも構造検査を必ず通す。高価な履歴・意味検査は候補追加時の必須 standalone gateとして結果を保存する。出力は `structurally_valid=true / candidate_count=N / human_approved=false` とし、`safe` や `eligible` を出さない。

### A-9 — SHOULD: 親の byte 実測は誤りで、348 は eligibility 分母ではない

- 根拠: 親は 97 / 2,896,319 bytes、251 / 7,922,057 bytes とする。[parent-brief.md:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:22) HEAD tree の静的再集計は plan 記載どおり 97 / 2,726,974、251 / 7,860,617 だった。[s2-plan.md:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:5)
- 251件は Markdown 199、JSON 47、patch 2、Python 2、shell 1 であり、単一の derived-report 族ではない。[s2-plan.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:15)
- 放置時の成果物影響: brief の実測 provenance が偽のまま残り、348件が全て retirement 候補であるかのような誤読を生む。
- 最小修正: brief に HEAD、列挙規則、正しい bytes を記録し、`inventory_count` と `eligible_candidate_count` を分離する。固定値を実装へ転写しないという plan の方針は維持する。

## positive controls

- PC-1: P1 の「この wave では削除しない」は実際に安全側である。CLI は `inventory/inspect/check` のみで、`delete` の拒否テストも予定されている。[parent-brief.md:10](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:10) [parent-brief.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:15) [s2-plan.md:126](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:126)

- PC-2: HEAD tree 基準、worktree `stat()` 非依存、target blob drift 拒否は正しい。[s2-plan.md:81](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:81) 現 HEAD の348対象はすべて mode `100644` で、direct test 97件・nested test 0件だった。

- PC-3: duplicate JSON key、unknown field、非UTF-8、symlink、gitlink、path traversal を fail-closed にするテスト面は妥当である。[s2-plan.md:87](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:87) [s2-plan.md:122](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:122) 既存 strict JSON 実装にも duplicate key・UTF-8・BOM・NFC 拒否の先例がある。[schema.py:129](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/task_runs/schema.py:129)

- PC-4: `check rc=0` を「package 構造成立」であって削除安全・承認ではないと限定した設計文言自体は正しい。[s2-plan.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:24) A-8 は、この限定を CLI 出力と実効 gate にも固定せよという指摘である。

- PC-5: campaign WAL/lock、freeze、正式 report、CCBench submodule を inventory 外に置く path 境界は現 wave の proof-chain bytes を直接変更しない。[parent-brief.md:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:5) [s2-plan.md:164](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:164)

- PC-6: plan は pytest・checker 未実走を緑と記録していない。[s2-plan.md:4](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:4) [s2-plan.md:144](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:144)

## scope 外の裁定候補

### A-10 — MUST（scope 外）: 承認 package から実削除までの状態遷移が未設計

- 根拠: 実削除・移動・apply は明示的に scope 外で、個別ユーザー裁定へ残されている。[parent-brief.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:15) [s2-plan.md:160](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:160)
- 放置時の成果物影響: 後続 wave が古い package や口頭承認を現在 HEAD の削除へ流用できる。
- 最小裁定案: `proposed → human-approved receipt（exact tree pin）→ deletion commit → D96/全走確認` の別設計をユーザー裁定に出す。自動 delete は追加しない。

### A-11 — SHOULD（scope 外）: RuleOps の test 外延と pytest の実収集外延が将来ずれ得る

- 根拠: runner はディレクトリ全体を pytest target にする一方、RuleOps と既存 plain-runner meta-test は直下だけを列挙する。[run_tests.py:41](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:41) [s2-plan.md:81](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:81) [test_plain_runner_coverage.py:44](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_plain_runner_coverage.py:44)
- 現 HEAD は nested test 0件なので即時欠陥ではない。
- 最小裁定案: 「nested `test_*.py` を禁止する境界 pin」か「pytest の実収集外延へ RuleOps を広げる」かを別途決める。

## 総括

P1 と HEAD 動的 inventory を使う P3 は、現在 wave が read-only・削除ゼロである限り成立する。一方、P2 は安全な retirement proof になっていない。

実装着手前の停止条件は A-1〜A-3。typed receipt の実行束縛、同時候補閉包、package 自己参照の定義がないままでは、validator は「危険な候補を通す」か「非空候補を一件も通せない」のどちらかになる。A-4〜A-8も author plan へ反映が必要である。pytest は未実走で、緑の受入結果はない。