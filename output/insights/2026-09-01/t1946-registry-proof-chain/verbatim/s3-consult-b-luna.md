静的検査のみ実施した。base は `11b44e2d1ad4a62aa41aebc74daf8a9df9bb51e2`。pytest は未実走であり、テスト結果を緑とは判定していない。

## 所見

### 1. D1114 の両条件が成立し、本 wave 単独 land は禁止される

- 重大度: blocker
- 根拠 file:line: `rulings-verbatim.md:98-109`、`s8b_floor_attempt_launcher.py:648-670`、`test_s8b_floor_attempt_launcher.py:20,317,393,436,486,626,664`
- 再現する条件: registry writer を production campaign へ配線せず、plan の v5 producer と registry 必須 inspector だけを導入する。
- 成果物への影響 1 行: registry 不在の既存 campaign は v5 `result.json` を発行できず、新規 certified 選択の入力集合が空になる。

AST と文字列検索では、production の `launch_floor_attempt()` 呼び手は 0 件、launcher module の production import 元も 0 件だった。動的 import、`getattr`、`__import__`、文字列解決も見つからない。詳細は `## D1114 判定` に示す。

### 2. exact な live tail 比較は、後続 append で既発行 v5 を無効化する

- 重大度: blocker
- 根拠 file:line: `plan.md:22-30,41-43,102-106`、`s8b_attempt_profile.py:378-382`、`s8b_ratified_freeze.py:3262-3275,3558-3565`
- 再現する条件: v5 artifact が `{row_count=N, chain_head=Hn}` を記録した後、同じ freeze-wide registry へ正当な行を 1 件 append し、`reverify_published_freeze()` を呼ぶ。
- 成果物への影響 1 行: 既に certified だった v5 freeze が、後続の正当な試行だけで oracle judge と verdict から参照不能になる。

plan は reported proof と現在の live proof の完全一致を要求する。registry は freeze 単位の append 対象なので、後続行で row count と tail head は必ず変わる。比較すべきなのは「現在の registry の先頭 N 行が artifact の head に一致すること」であり、現在 tail との完全一致ではない。

### 3. D1193 が留保した registry namespace と予算配置を暗黙に決めている

- 重大度: blocker
- 根拠 file:line: `rulings-verbatim.md:120-140`、`plan.md:91-98`、`s8b_attempt_profile.py:378-382,405-408,447-456`、`attempt_registry_core.py:1019,1120-1129`
- 再現する条件: plan どおり freeze hash だけで決まる既存 path を proof identity とし、その後 D1193 どおり registry を protocol 世代別に分割する。
- 成果物への影響 1 行: 後続 protocol は binding 衝突で停止するか、ledger 分割後に予算 count が世代ごとにリセットされる。

現行 budget は同じ registry の replay 中に数えられる。plan の単一 `row_count` / `chain_head` は、台帳と予算が同じ freeze-wide chain にある設計を固定する。D1193 の「台帳は世代別、予算は凍結単位」を実現するには、cross-ledger budget authority の配置を先に裁定する必要がある。

### 4. plan の既存 test 閉包に pure verifier の v5 正例 2 件が欠ける

- 重大度: must-fix
- 根拠 file:line: `test_s8b_floor_campaign.py:787-824,9154-9179,12841-12868`、`plan.md:166-192`
- 再現する条件: helper が registry を作って campaign 自体は完走する一方、v5 result を pure `verify_floor_artifact()` へ `expected_attempt_registry` 無しで渡す。
- 成果物への影響 1 行: v5 を常に拒否する verifier でも負例だけ通り、certified 受理集合が空になる退行を検出できない。

plan が落としている既存 node は次の 2 件。

- `test_end_to_end_golden_floor_values_and_tamper_detection`
- `test_verify_floor_artifact_binaries_positive_and_negative`

`_live_holdout_admission_for_outcome()` は holdout receipt しか返さない。registry proof も独立再読し、positive call に渡す必要がある。

### 5. “sole connection owner” は plan の read-only inspector と矛盾する

- 重大度: must-fix
- 根拠 file:line: `s8b_attempt_registry.py:2-16`、`plan.md:91-98,160-164`、`s8b_holdout_admission.py:4960-4990`
- 再現する条件: admission が registry path を導出し、raw registry を直接読んで proof を返す。
- 成果物への影響 1 行: certified result の registry 参照主体が admission に増えるのに、proof-chain ownership の正本は launcher-only のまま残る。

実装するなら同じ commit で、launcher を「sole adapter/mutation owner」と限定し、admission の read-only verifier ownership を明記する必要がある。`floor campaign and holdout admission do not import this adapter directly` は引き続き正しい。

## exact 述語 consumer の全数表

| production consumer | exact 述語 file:line | expected 集合の由来 | plan が直すか |
|---|---|---|---|
| `s8b_floor_stats.verify_floor_artifact` | `s8b_floor_stats.py:734-743` | `_floor_contract.result_keys_for_mode()` | 直す。`plan.md:100-107` |
| `s8b_holdout_freeze._validate_floor_inputs` | `s8b_holdout_freeze.py:1429-1436` | `s8b_floor_contract.result_keys_for_mode()` | 直す。`plan.md:118-123` |
| `s8b_ratified_freeze._validate_result_top_level_keys` | `s8b_ratified_freeze.py:2333-2356` | `_floor_contract.result_keys_for_mode()` | 直す。`plan.md:125-130` |

独自 key 集合、別名束縛、動的取得、shell 内埋め込みを含めて検索したが、result top-level の第 4 consumer は無い。top-level key literal の単一源も `s8b_floor_contract.py:81-87` だけである。plan は 3/3 件を変更対象にしている。

schema 版については、result と manifest / journal / cert / freeze の版を tuple で exact 比較する production 箇所は無い。各版は個別に固定される。

- manifest v3: `s8b_floor_contract.py:271-272`、`s8b_ratified_freeze.py:1862-1866`
- journal v3: `s8b_floor_contract.py:827-829`、`s8b_ratified_freeze.py:2114-2117`
- cert v1: `s8b_launch_cert.py:14,50-66`
- freeze v1/v2: `s8b_floor_contract.py:32`、`s8b_floor_campaign.py:7145-7146`、`s8b_holdout_freeze.py:2072-2098`

v5 result の raw hash は `s8b_holdout_freeze.py:2091-2094` の `floor_source.sha256` に束縛されるが、他 schema の版上げは不要である。

## 赤になる既存 test (独立列挙)

直接 pin は以下。

| 既存 test | 根拠 | plan 一覧との差分 |
|---|---|---|
| `test_floor_campaign_directly_reexports_shared_leaf_objects` | `test_s8b_floor_contract.py:164-180` の v4 literal | plan 記載済み |
| `test_pure_verifier_rejects_legacy_result_schema` | `test_s8b_floor_stats.py:1321-1325` の exact 文言 | plan 記載済み |
| `test_official_result_rejects_perf_preflight_receipt_fail_closed` | `test_s8b_floor_campaign.py:5963-6005` の direct assembler 3 call | plan 記載済み |
| `test_official_degraded_result_records_strict_perf_observation` | `test_s8b_floor_campaign.py:6008-6054` の direct assembler 2 call | plan 記載済み |
| `test_producer_rejects_incomplete_binary_coverage[result-*]` | `test_s8b_floor_campaign.py:12760-12778` | plan 記載済み |
| `test_end_to_end_golden_floor_values_and_tamper_detection` | `test_s8b_floor_campaign.py:9175-9179` の v5 positive pure verify | plan から欠落 |
| `test_verify_floor_artifact_binaries_positive_and_negative` | `test_s8b_floor_campaign.py:12864-12868` の v5 positive pure verify | plan から欠落 |

fixture 閉包は plan の列挙と一致する。

- `test_s8b_floor_campaign.py:734-784` の完走 helper
- `s8b_v2_freeze_fixture.py:337-475`
- `test_s8b_ratified_verify.py:459-475,609-617`
- `test_s8b_ratified_freeze.py:966-1086,1225-1265`
- `test_s8b_holdout_freeze.py:1702-1754`

特に `test_s8b_holdout_freeze.py:1730-1741` は shared admission root 全体を削除して holdout evidence だけを再構築するため、registry も再生成しなければならない。

次は静的には赤にならない。

- `_RESULT_KEYS` pin (`test_s8b_floor_contract.py:366-383`) は current alias と helper を同時参照する coupled pin。
- `test_official_perf_closure.py:197-217,329` は 3 consumer の関数名と call を維持するため不変。
- literal v4 fixture `test_s8b_floor_stats.py:596` は後方互換正例として維持できる。
- meta-test、live-wrapper 3-caller glob、spawn-site scanner は、新しい subprocess や forbidden adapter tokenを入れない限り不変。
- acceptance duration ledger の既存 node 名 pin は rename しなければ不変。新規 node の実測値は親のテスト実測後に更新対象となる。

## 親 brief と親実測への異議

- `F-P4` の「admission に registry 参照を足すと確実に meta-test が赤」は過剰一般化である。`test_s8b_attempt_registry.py:1553-1577` が検出するのは exact token `s8b_attempt_registry` であり、plan の `attempt_registry_core`、`s8b_attempt_profile`、`inspect_floor_attempt_registry_evidence` は該当しない。対象 2 file と positive control の実測自体は正しい。
- `F-P4` の「producer へ値を届けるには campaign 外から渡すしかない」も広すぎる。campaign は既存どおり admission の read-only inspector を呼べる。
- `F-CHAIN` の「空 registry と genesis-only を head で区別できない可能性」は誤り。genesis は `attempt_registry_core.py:1497-1500` で chained row になり、`previous_event_sha256()` は `:253-259` でその非 zero event hash を返す。空 rows だけが zero になる。
- `F-SCHEMA` の「4 + 3 = 7 predicates」は数え方が不正確である。schema を拒否する consumer 述語は stats / holdout / ratified の 3 件。campaign の別名束縛と result 書込みは必要な変更面だが predicate ではない。
- `F-ARTIFACT` の「tracked certified artifact 0 件」は再現した。ただし、これだけから repo 外・別 checkout・計算ノードにも qualifying artifact が無いとは一般化できない。実際、insight は過去の v2 pilot path を記録しているが、v5・certified・registry 付きではないため D1114 (a) を満たさない。
- `F-P5`、`F-EXACT`、`F-NESTED`、production launcher 呼び手 0 件の実測には異議なし。

## plan に同意する点

- current v5 と readable v4/v5 を分離し、新規 candidate 入口だけを v5-only にする方針は正しい。
- `reverify_published_freeze()` の共通経路で v4 は registry inspector を呼ばず、既存条件を維持できる。呼び手は `s8b_oracle_judge.py:749-750` と `s8b_verdict.py:828-829`。
- top-level exact consumer 3 件を全て schema-aware にする点は正しい。
- adapter 直接 import を避け、pure verifier と live wrapper を分ける点も正しい。
- D1113 について、plan は新しい reason 引数を追加しない。既存 classification reason は launcher 内で `s8b_floor_attempt_launcher.py:378-385,590-604` から導出され、recovery は `s8b_attempt_registry.py:1725-1753` で sealed receipt bytes から読むため、新たな違反はない。

## D1114 判定

1. **(a) は成立する。** 現行 schema はまだ v4 (`s8b_floor_contract.py:34`) で、current checkout に `s8b-floor-*/result.json` と `floor-attempt-registries/*/registry.jsonl` は 0 件だった。v5 gate を満たす artifact path または計測 ID は名指しできない。

2. **(b) は成立する。** production で public launcher を呼ぶ箇所と launcher module を import する箇所はいずれも 0 件。呼び手は test のみである。registry 不在は現行 raw reader の `s8b_holdout_admission.py:4969-4975` で検出でき、plan の新 inspector はここを `attempt-registry-missing` に倒す。fresh は `s8b_floor_campaign.py:7702-7724`、resume は `:7557-7571` で assembly 前に停止し、`:7771-7779` / `:7592-7599` の publish へ到達しない。registry 不在で v5 result を発行する別経路は無い。

   なお現在の production CLI は pilot (`tools/pegasus/floor_campaign.sh:1226-1230`) だけで、official 自体も `s8b_floor_campaign.py:453-463,8368-8375` で既に拒否される。厳密には「既存 certified 発行が新たに失われる」のではなく、唯一生きている pilot campaign まで停止し、将来 official を開いても同じ位置で停止する。

3. **D1194 と D1114 は両立する。** D1194 は最終的に必要な前向き束縛を定め、D1114 は writer と gate の片側だけを先行 land する順序を禁じる。D1194 は D1114 を解除していない。

4. **D1193 の留保に踏み込んでいる。** `s8b_attempt_profile.py:378-382` の freeze-only registry path と、同じ replay 内の budget count (`attempt_registry_core.py:1019,1120-1129`) をそのまま proof identity に採るためである。protocol 世代別 ledger と freeze-wide budget authority の置き場所を裁定せず固定している。

5. **結論: 設計を凍結して裁定へ返すべき。**  
   (a) と (b) はともに成立する。  
   writer 配線、protocol 世代別 registry、freeze-wide budget authority、prefix 検証を同じ設計単位にする必要がある。  
   現 plan の検査側だけを land してはならない。

## 総括

- exact consumer は 3 件で網羅され、plan は 3/3 を直している。
- v4 の既存受理面を保つ schema 分岐は妥当。
- ただし D1114 と D1193 が blocker で、live tail 完全一致も既発行 v5 を壊す。
- 結論は land 不可、設計凍結・裁定返し。