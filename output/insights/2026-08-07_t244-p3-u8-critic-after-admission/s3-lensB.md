現プランは **NO-GO** です。U-8 の呼出し移動に、未裁定の event・schema 互換性・generation 統治を抱き合わせており、barrier も主張する durable 順序を証明できません。

静的検査のみで、ファイル変更・pytest 実行はしていません。

## 1. 裁定射程

| 提案 | 判定 | 理由 | 成果物影響 |
|---|---|---|---|
| `critic-admission-barrier` | **R-01 real / 未裁定統治** | U-8 正本は critic の移動を決めただけです（[設計正本:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-05_t244-p3-design/README.md:253)、[同:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-05_t244-p3-design/README.md:329)）。新 event の受理、新 event 必須化、barrier-only partial の受理は別の受理集合変更です（[plan:200](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:200)、[同:420](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:420)）。D96 は手続義務であり、この新統治の実体を承認してはいません。 | critic と `run-finish` の `seq`、role event の canonical ref、journal SHA、report bytes が変わり、barrier のない build trial が新たに拒否されます。 |
| v3→v4 | **R-02 real / 未裁定の互換性変更** | U-8 の最小移動では role payload の field・意味は変わりません。過去の schema bump は「payload の意味変更」を理由にしていました（[D118:5647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/decisions.md:5647)、[D192:9369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/decisions.md:9369)）。journal event の追加を全 role payload の版上げへ波及させるのは別判断です。 | 全 role payload bytes と `input_payload_sha256` が変わり、現 verifier は旧 v3 journal を拒否します。 |
| `MAX_POST_ADMISSION_CRITIC_GENERATIONS=1` | **R-03 real / 未裁定かつ既存裁定と衝突** | D114 は研究上限を `MAX_APPROVED_GENERATIONS` 一個に集約し、「解除はこの定数一個と境界テストの同時変更」と決めています（[D114:5331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/decisions.md:5331)）。新 cap はその解除を無効化します。 | 現在の通常入力集合 `{1}` は既存 cap が先に拒否するため即時には縮みませんが、既存 cap を正当に引き上げても 2〜10 世代が拒否される latent over-rejection になります。 |

特に R-03 は裁定パッケージへ戻すべきです。C11 evaluator も `MAX_APPROVED_GENERATIONS` だけを cap-lift の入口として読んでいます（[s8c_preregistration_evidence.py:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/s8c_preregistration_evidence.py:525)）。新 cap を追加すると、C11 が次の条件へ進む一方、実運転は 1 世代で拒否されるという consumer/producer 不一致になります。

## 2. Barrier は順序証明にならない

**R-04 real / must-fix**

現在の critic は、durable Layer 3 report より前でも `require_admitted_campaign()` から同じ admission decision を取得できます（[producer:1753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1753)、[artifact_admission.py:723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/artifact_admission.py:723)）。durable write は `_finalize_build_cell_admission()` が呼ぶ `layer3_report.render()` の fsync/link で初めて起きます（[producer:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1197)、[layer3_report.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/layer3_report.py:570)）。

したがって decision hash 付き barrier が示すのは「producer が barrier と名付けた event を書いた」ことだけです。同じ hash は report fsync 前にも作れるので、critic が durable Layer 3 書込み後だったことの独立証拠にはなりません。

代替案の評価は次のとおりです。

| 案 | 十分性 |
|---|---|
| callback 順序を記録する producer test | **字義どおりの U-8 実装には十分。最安。** finalizer の sentinel 設定後にだけ critic provider が呼ばれることを検査する。 |
| 既存 `admission_decision` の report 内存在 | 不十分。最終的に存在したことしか示さず、時間順を示さない。callback 内 sentinel として使うなら十分。 |
| critic role event への decision/report hash field | barrier より安いが、やはり自己申告で durable 時系列を証明しない。必須検査にすれば別の受理集合変更。 |
| report cell の `order` field | 不十分。全処理後に作る宣言値である。 |
| filesystem mtime | 不十分。canonical artifact に束縛されず、時計・copy で変わる。 |
| finalizer 発行の非偽造 receipt/capability | offline 証明にはなり得るが、新 proof/schema 統治そのものであり U-8 の射程外。 |

**成果物影響:** barrier を採ると journal/report bytes は変わるのに、proof chain の順序保証は強くなりません。

最も安い十分な案は、既存 build public-entry test を共有 `order`/sentinel で拡張し、`admission → critic` を直接 pin することです。offline artifact だけで時系列を認定する強い要件まで欲しいなら、barrier では足りず、別裁定が必要です。

## 3. Schema bump の全波及

**R-05 real / must-fix**

`SCHEMA_VERSION` は journal 専用版ではありません。[producer:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:143) の一定数が、全 role payload（同:1063）と `run-start`（同:2013）の双方へ入ります。

実 grep で確認できた波及は以下です。

- Consumer:

  - completeness は `run-start.schema_version == producer.SCHEMA_VERSION` を厳密要求します（[completeness:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:450)）。bump 後は既存 v3 artifact を読みません。
  - trial registry は acceptance 前にこの completeness を呼びます（[trial_registry.py:1807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/trial_registry.py:1807)、同:1852）。従って旧 v3 trial は台帳受入にも進めません。
  - `verify_autonomous_trial_files()` も同じ strict consumer です（[completeness:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:1191)）。

- Literal test/fixed value:

  - producer test の3箇所（[test_p3:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:706)）。
  - completeness fixture 定数（[test_completeness:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_autonomous_trial_completeness.py:40)）。
  - schema literal pin（[同:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_autonomous_trial_completeness.py:742)）。

- 動的追随で直ちには赤くならない箇所:

  - `test_claude_transport.py` は `A.SCHEMA_VERSION` を参照します（[同:1258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_claude_transport.py:1258)）。
  - `test_trial_registry.py` も producer 定数を参照します（[同:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_trial_registry.py:165)）。これらは自動追随するため、v3 後方互換性の独立 pin にはなりません。

- Docs:

  - live docs に完全な literal `p3-autonomous-workload-trial/v3` は見つかりませんでした。
  - ただし新 event を採るなら、journal と completeness の契約を説明する runbook（[runbook:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/phase3-s8c-autonomous-trial-runbook.md:158)、同:173）を更新する必要があります。プランの変更ファイル一覧にはありません。
  - repo 内 `output/**/*.json{,l}` に現行 v3 実走 artifact は見つかりませんでした。外部保存分の有無は不明です。

**成果物影響:** v4 にすると、no-build を含む全 role payload、payload hash、journal hash、report bytes が変わり、旧 v3 trial の台帳受理集合が消えます。

**bump しない案は成立します。** Barrier を削り、呼出し順だけを変えるなら serialized field と role payload の意味は同じなので v3 を維持できます。Barrier を必須 artifact にするなら v3 据置きは正直でなく、v4-only と v3/v4 dual-read のどちらを採るか自体を裁定へ返す必要があります。

## 4. File:line と具体プランの不整合

数値 anchor の大半は現物と一致しました。ずれ・誤った性格付けは以下です。

- **R-06a real:** plan は `P:1743-1801` を critic block として削除しますが（[plan:307](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:307)）、harness terminal branch は [producer:1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1800)〜1802 です。記述どおりなら 1802 の `break` だけ残り、複数世代経路が無条件で第1世代終了になります。  
  **成果物影響:** monkeypatch/cap-lift 経路の generation 2 以降、role attempts、campaign WAL、report cell が消えます。

- **R-06b real:** `_pending_critics` を必須引数にするのに、プランが挙げる追随先は wrapper と transport call だけです（[plan:534](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:534)）。直接 call は少なくとも [test_p3:1466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1466)、同:1486、3427、3453 にもあります。Python の引数 binding が先に失敗し、意図した run-scope gate へ届きません。また direct helper test の critic call-count pin（[同:1763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1763)、同:1828）も追随が必要です。  
  **成果物影響:** direct invocation の受理/API 契約が `TrialRegistryError` から引数 `TypeError` へ変わり、critic attempt を持つはずの direct journal が作れません。

- **R-06c real:** 新 cap の追随から、`MAX_APPROVED_GENERATIONS=3` を使う invalid-role test（[test_p3:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1364)）が漏れています。  
  **成果物影響:** invalid planner の `role-invalid`/partial artifact を検査する前に generation gate が拒否します。

- **R-06d real:** `TP:633-755` は build/no-build 別 test ではなく `do_build=False` の no-build test です（[test_p3:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:633)、同:646）。build public-entry test は finalizer を fake にし、campaign chain も無効化しています（[同:1908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1908)、同:1917）。`TC:499` の positive fixture も `do_build=False` です（[test_completeness:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_autonomous_trial_completeness.py:255)）。  
  **成果物影響:** fake decision/barrier は通っても、実 `layer3_report.json` が critic 前に durable になったことは未検査のままです。

- **N-01 nit:** `C:949 直後` は admission 検査後ではなく cell loop の開始位置です（[completeness:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:949)）。検査後なら同:971 の後です。成果物影響は実装位置を確定するまで不明です。

存在しない code symbol (`_PendingCriticAttempt`、4 helper、`MAX_POST_ADMISSION_CRITIC_GENERATIONS`、`_pending_critics`) は、plan 本文では新設と明記されています。ここ自体は架空既存 symbol の誤引用ではありません。

## 5. 変異 M1〜M6

**R-07 real / preregistration を作り直す必要あり**

| 変異 | 帰属検査 | kill node | 判定 |
|---|---|---|---|
| M1 呼出し順交換 | barrier を残した full `run_trial` では、callback test だけでなく barrier order checker も拒否します。plan は一方で `run_trial` を通すと書き（[plan:467](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:467)）、他方で「direct helper・completeness を介さない」と書いており（同:550）、自己矛盾です。 | 現在不存在。新設名は本文で明示。 | **要再登録。** barrier なしの純粋な callback 順序 test に絞る。 |
| M2 barrier append 削除 | 設計を採るなら missing-barrier gate の単一理由にできる。前後の既存 gate は同じ入力を拒否しない。 | 不存在。`test_producer_requires...` という exact 名は §5 で新設明記されていない。 | **落とす。** Barrier 自体を裁定へ返すため。 |
| M3 比較反転 | seq/hashを再計算し、critic-before-barrier 以外を正しくすれば単一理由化可能。 | 不存在。exact 名の新設明記なし。 | **落とす。** Barrier 採用後に再登録可能。 |
| M4 decision SHA 比較削除 | report decision 自体を変える fixture なら既存 artifact-admission/campaign-chain にも拒否されます。barrier 側 hash だけを変える、と限定しない限り帰属不能です。 | 不存在。exact 名の新設明記なし。 | **落として再設計。** |
| M5 `role-invalid` 代入削除 | full producer test では後段の fixed-budget valid-role gate（[completeness:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:771)）が先に赤くし、狙った stop/status assert へ返りません。 | 現在不存在だが、§5 で新設明記あり。 | **direct postcritic helper test に置換。** completeness を介さず stop、decision 保持を検査する。 |
| M6 prefix equality→subset | 現 fixture は prefix gate だけが拒否理由で、既存 node は実在します（[test_completeness:1201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_autonomous_trial_completeness.py:1201)）。 | 既存。 | **U-8 の変異候補から落とす。** 変更予定行でなく、既存 test が既に殺すため。回帰 test 自体は残す。 |

代替の照準先は次です。

- finalizer callback の完了前に critic を呼ぶ変異 → 純粋な order-spy test。
- finalizer failure 後にも critic を呼ぶ変異 → critic call count 0、report 不在を検査。
- invalid critic の `role-invalid` を落とす変異 → direct postcritic helper で検査。
- critic 後の status 再計算を飛ばす変異 → partial/status の focused test。
- postcritic 内部例外で generation を二重 append する変異 → generation exactly-one test。

**成果物影響:** 現 preregistration のままでは、wrong-order mutant が別 gate に殺されても「順序 test が帰属を証明した」と誤記録され、mutation ledger の kill reason が偽になります。

## 6. 親 brief の実測・一般化

| 親の主張 | 判定 | 機序 | 成果物影響 |
|---|---|---|---|
| generations=1 なので critic 出力は制御流へ還らない | **R-08a real / 一般化過剰** | valid な `reverse_recommended` に次世代 consumer がない点だけは正しいです。しかし critic response の shape/parse invalid は `None` となり、直ちに `stop_reason=role-invalid` へ行きます（[producer:1792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1792)）。さらに injected critic provider は共有 closure を変え、次 workload の injected drive に影響可能です。D114 自身も injection を保証外としています（[D114:5390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/decisions.md:5390)）。 | critic invalid は cell stop、trial status、attempt/report を complete から partial へ変えます。共有 side effect なら後続 cell の harness outcome/候補も変えられます。 |
| 3 anchor のうち現存は Layer 3 だけ | **事実部分は正しいが、完了への一般化は誤り** | D201 は ledger wiring を実装しないと明記します（[D201:9719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/decisions.md:9719)）。proof sidecar も不在です。ただしそれは「Layer 3 後置だけで U-8 完了」を意味しません。また現コードには pre-critic の raw artifact admission と post-critic の durable Layer 3 render があり、単に「Layer 3 admission」と呼ぶと二者を混同します。 | critic は依然 ledger seal/proof issuance 前に metrics を受け取るため、commit-reveal/proof chain は閉じず、P3 FAIL のままです。今回を「U-8 完了」と記録してはいけません。 |
| 既存 fixture path で発火は足りる | **R-08b real / 限定すれば正しい** | control-flow callback test の seam としては足ります。しかし full fixture は no-build、build test は finalizer/chain を fake にしており、実 durable Layer 3 anchor は発火していません。 | wrong-order 実装でも、fake decision を最終的に設定すれば report/journal の既存検査を通し得ます。 |
| 実装上限10の経路 | **誤り** | `main`、`run_trial`、`_run_workload` の全入口が同じ current cap を通ります（[producer:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:306)）。2世代到達は monkeypatch test だけです。 | 通常 trial artifact への現在影響はありません。新 cap は発火しない dead governance になります。 |

なお §5.4 は proof 書込みまで含めますが、裁定表 U-8 行は Layer 3・seal までしか書いていません。今回のユーザー指示が三 anchor と明示しているため本レビューではそれを優先しましたが、正本内の省略は後続記録で解消すべきです。

## 7. 作業量

**R-09 real:** 約565行は U-8 の目的に対して過大です。増分の大半は U-8 ではなく barrier/schema/new-cap の自己派生です。

削れるもの:

- completeness production 約90行の barrier/cap 追随。
- barrier negative matrix、decision hash tests、M2〜M4。
- schema v4 literal 更新。
- new-cap test と既存 multi-generation test の置換。
- nonprefix test 拡張と M6。
- scope 外の inner wall-budget 追加 test。
- barrier/new-cap を記録する新 D の部分。最小案では受理集合が変わらず、D96 は発火しません。

残すもの:

- producer の precritic/postcritic phase 分割。
- critic 後の status 計算。
- invalid critic の `role-invalid` と admission decision 保持。
- focused order test、invalid critic test、finalizer failure test、postcritic exception の generation exactly-one test。
- cell 単位を採るなら、複数 workload で `admission1 < critic1 < admission2 < critic2` を固定する test。

逆に現在の広いプランで足りないものは、runbook 更新、漏れた direct call/test の追随、`MAX_APPROVED_GENERATIONS=3` test、実 Layer 3 write を発火する test です。したがって565行案は「大きいのに完結していない」状態です。

**成果物影響:** 最小案なら既存 schema、journal event 集合、trial ledger 受理集合を維持しつつ、build producer の実呼出し順だけを変えられます。

## 疑い

- **S-01 疑い:** plan は per-cell finalization を現行 try/except のどちら側へ置くか明示していません（[plan:320](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:320)、現行 try は [producer:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1295)）。try 内なら finalizer error が `supervisor-error` 化され、fallback で再試行される可能性があります。現行は finalizer error で report 非公開です。  
  **成果物影響:** transient finalizer failure が「report 不在」から「positive decision を持つ partial report」へ変わる可能性があります。実装前なので疑いに留めます。

- **S-02 疑い:** repo 内に保存済み v3 JSON/JSONL は見つかりませんでしたが、repo 外の実走 artifact の有無は確認できません。  
  **成果物影響:** 外部 v3 trial があれば v4-only verifier/registry から参照不能になります。

## 総括

- **(a) 判定: NO-GO。** U-8 の呼出し移動に未裁定の barrier・v4-only 互換性・第二 generation cap を抱き合わせ、barrier 自体も durable Layer 3 順序を証明できないため。
- **(b) must-fix:** R-01、R-02、R-03、R-04、R-05、R-06a〜R-06d、R-07、R-08a、R-08b、R-09。
- **(c) 最も安い十分な実装案:** schema/event/completeness/cap を変えず、cell の harness 後に Layer 3 finalizer を完了してから critic を呼び、既存 build public-entry test の shared sentinel で `admission → critic` を pin する。
- **(d) 親 brief の誤った前提:** 「critic 出力全体が制御流へ還らない」「通常到達可能な実装上限10経路がある」「既存 fixture が実 Layer 3 durable write を発火する」は誤り。三 anchor 中二つが不在という実測自体は正しいが、Layer 3-only 変更を U-8 完了へ一般化してはいけません。