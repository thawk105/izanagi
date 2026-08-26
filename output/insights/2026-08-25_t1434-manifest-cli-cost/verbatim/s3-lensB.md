## 所見

### B-1 — `task_manifest` の関数閉包は、段 2 プランどおりなら単一 CLI 呼出し内では閉じる

- **対象:** `brief.md:9-12`、`s2-plan-2.md:3-17,23-41,74-79`、`tools/codex_reasoning_ab.py:8748,8847,8988,9289,9310,9373,9482,10091,10554,10591,10604,10783,10825,10890,10972`
- **重大度:** MEDIUM
- **帰結:** brief の前提は誤っているが、段 2 プランの伝播を全部実装すれば、単一 invocation 内に「引数はあるが外部 manifest が届かない」関数は残らない。ただし B-2 の invocation 間束縛は閉じない。
- **根拠:** brief は「`supervise_pair` ... は既に `task_manifest` 引数を持つ」とするが、段 2 プラン自身が「現在の署名に `task_manifest` を持っていない」と訂正している。

現物で名前が exact に `task_manifest` の引数を持つ関数は 15 個である。

1. `_slot_dimensions` — `:8748`
2. `_validate_schedule` — `:8847`
3. `_load_adjudication` — `:8988`
4. `_slot_dimension_map` — `:9289`
5. `_attempt_slot_dimensions` — `:9310`
6. `_aggregate_token_usage_observations` — `:9373`
7. `_aggregate_verified` — `:9482`
8. `_replay_manifest` — `:10091`
9. `verify_manifest` — `:10554`
10. `aggregate_manifest` — `:10591`
11. `make_packets` — `:10604`
12. `_validate_verdict_row` — `:10783`
13. `append_verdicts` — `:10825`
14. `freeze_verdicts` — `:10890`
15. `reveal_mapping` — `:10972`

このうち現在の verb 関数は 6 個で、brief が数えた 7 個から `supervise_pair` を除いた集合である。

段 2 プランはさらに 10 関数へ引数を追加する。

`derive_independent_golden`、`_snapshot_spec`、`_prepare_snapshot_case`、`_finish_snapshot_case`、`_derive_snapshot_from_base`、`build_snapshot`、`verify_snapshot`、`render_prompt`、`_supervise_one`、`supervise_pair`。

したがって実装後の literal な関数集合は 25 個になる。CLI verb の関数へ直接渡す集合は次の 10 個である。

`build_snapshot`、`verify_snapshot`、`render_prompt`、`supervise_pair`、`verify_manifest`、`aggregate_manifest`、`make_packets`、`append_verdicts`、`freeze_verdicts`、`reveal_mapping`。

差集合は次の 15 個である。

`derive_independent_golden`、`_snapshot_spec`、`_prepare_snapshot_case`、`_finish_snapshot_case`、`_derive_snapshot_from_base`、`_supervise_one`、`_slot_dimensions`、`_validate_schedule`、`_load_adjudication`、`_slot_dimension_map`、`_attempt_slot_dimensions`、`_aggregate_token_usage_observations`、`_aggregate_verified`、`_replay_manifest`、`_validate_verdict_row`。

これらはすべて direct verb からの内部呼出しで到達する計画になっている。`collect-run` は 11 番目の option 対象だが、`collect_run` 自身には引数を追加せず、`main()` が外部 manifest で alias を解決して `legacy_case` だけを渡す計画である (`s2-plan-2.md:26,74-79`)。

なお、引数名が `manifest` で既定値が `TASK_MANIFEST` の helper も 7 個ある。`resolve_benchmark_task_id:2476`、`_manifest_task:2525`、`_validate_task_manifest:2551`、`normalize_legacy_schedule:2761`、`normalize_schedule:2796`、`expected_schedule_from_manifest:2841`、`known_finding_ids_for_manifest:2896` である。プランはこれらにも明示値を渡す。

結論は、**invocation-local な入力口は作れるが、それだけでは実験全体の入力口とは言えない**、である。

### B-2 — task manifest の identity が invocation 間で凍結されず、受理集合を途中で交換できる

- **対象:** `s2-plan-2.md:70,74-79`、`tools/codex_reasoning_ab.py:8207-8214,10393-10410,10727-10743,10803-10813,10932-10938`
- **重大度:** CRITICAL
- **帰結:** `supervise-pair`、`make-packets`、`append-verdicts`、`freeze-verdicts`、`reveal-mapping`、`verify` を異なる task manifest で順に実行できる。特に `known_finding_ids` だけを変えた manifest へ交換すると、`equivalent_to` の受理集合が変わるが、packet state や verdict freeze はその交換を検出しない。
- **根拠:** プランが保証するのは「parse 後に manifest を一度だけ load」「その同一 manifest を対象 verb ... へ渡す」までであり、複数 CLI invocation をまたぐ hash 束縛ではない。

`collect_run` の receipt は `case` と `arm` を保存するだけで、canonical `benchmark_task_id` や task-manifest SHA を持たない (`:8207-8214`)。canonical task 軸は replay 時に、その時点の schedule と manifest から後付けされる (`:10393-10410`)。

さらに次の frozen artifact に task-manifest descriptor/hash が無い。

- packet state: `schema_version`、`mask_strength`、`packets` だけ (`:10727-10731`)
- private mapping: `schema_version`、`mask_strength`、`mapping` だけ (`:10736-10743`)
- verdict freeze: packet state SHA、verdict log SHA、packet digest、時刻だけ (`:10932-10938`)

一方、verdict の受理集合は実行時に渡された manifest の union から計算する (`:10803-10813`)。したがって「外部入力を受けられる」ことは成立しても、「同じ入力が実験全工程を支配した」ことは証明できない。

閉じるには少なくとも次が必要である。

- canonical task-manifest bytes の SHA-256 と schema version を schedule/run manifest に保存する。
- packet state、private mapping、verdict freeze、revealed map、aggregate reportへ同じ digest を連鎖させる。
- downstream verb の `--task-manifest` は predecessor artifact の digest と exact 一致するときだけ受理する。
- command 間で manifest を交換する mutation test を追加する。

### B-3 — cost は ledger に書かれるだけで、resource 指標にも §12 gate にも届かない

- **対象:** `brief.md:94-95`、`s2-plan-2.md:98-103,196-208,281`、`tools/codex_reasoning_ab.py:9752-9790,9867-9890,10532-10550`
- **重大度:** CRITICAL
- **帰結:** `normalized_cost` と `normalized_cost_axis_ledger` は report の装飾値になる。§11.2 の resource 指標、resource-overall gate、§12 の gate 表、`decision`、overall の受理集合は一切変化しない。
- **根拠:** brief は「resource-overall gate が値を持てない」と問題を定義するが、プランの接続先は `resource_ledger` と新しい top-level axis ledgerだけである。

現物の流れは次で止まる。

`receipt token fields` → `attempt` → `resource_ledger` / `normalized_cost_axis_ledger` → **reader なし**

`tools/codex_reasoning_ab.py` 内の `resource_ledger` 参照は生成箇所だけであり、gate evaluator は存在しない。既存 `decision` は品質・false finding・reliability から構築され (`:9646-9750`)、resources を読まない。

さらに certification scope は `"certified_report_fields": ["valid"]` のままである (`:10532-10550`)。新 cost ledger は certified field にもならない。

実効化に必要なのは次である。

- §11.2 のどの統計量へ `accounted_amount` を変換するかを実装する。
- arm/axis ごとの分母、retry、technical failure、欠測の扱いを固定する。
- `coverage_status="partial"` を pass、fail、inconclusive のどれにするか登録する。
- §12 の具体的な threshold と gate row を評価し、overallへ接続する。
- gate 入力と結果を certification scope に含める。

これらの意味規則は射影された資料に存在しないため、実装子が推測して足してはならない。裁定または既存 protocol の exact な reader 仕様が必要である。

### B-4 — model slug の gate 入力は実在し、SKU 集合と exact 一致する

- **対象:** `tools/t189_price_snapshot.py:49-50,517-560,711-735`、`tools/codex_reasoning_ab.py:94,3459,8784-8791`
- **重大度:** LOW
- **帰結:** 有効な schedule slot の `requested_model` は必ず price snapshot の SKU を引ける。model slug 不一致によって cost が永久に生成されない問題はない。
- **根拠:** 原典はそれぞれ `TARGET_MODELS = ("gpt-5.6-sol", "gpt-5.6-luna")` と `MODEL_ALLOWLIST = frozenset((MODEL, "gpt-5.6-luna"))` で、`MODEL` は `"gpt-5.6-sol"` である。

import-level の実測結果も次のとおりだった。

- `MODEL_ALLOWLIST = {"gpt-5.6-sol", "gpt-5.6-luna"}`
- `PRICE_SNAPSHOT.TARGET_MODELS = {"gpt-5.6-sol", "gpt-5.6-luna"}`
- 集合一致: `True`

関連 field の実在範囲は次のとおりである。

| field | artifact / consumer | 実環境で受理される値 |
|---|---|---|
| `requested_model` | schedule slot、`:8784-8791` | `gpt-5.6-sol` または `gpt-5.6-luna`。欠落時は sol |
| `sku_mapping` key | price artifact、`t189_price_snapshot.py:711-735` | 上記 2 key exact |
| `price_version` | schedule slot、`:8732-8745` | 全 slot `null` または全 slot exact `FROZEN_PRICE_VERSION` |
| token fields | receipt、`:8248-8255` | `input_tokens`、`cached_input_tokens`、`output_tokens`、`reasoning_output_tokens` |
| mapping operation | price artifact、`t189_price_snapshot.py:81-98,617-624` | `identity`、`input_tokens-minus-cached_input_tokens`、`None` |
| coverage | price artifact、`:556-559` | `cache_write` は常に未計上。完全 coverage は到達不能 |

したがって model gate は有効だが、`coverage_status == "complete"` を要求する gate を作ると pass は到達不能になる。

### B-5 — prelaunch failure の 0 は観測 token ではないのに、計画どおりなら 0 cost へ化ける

- **対象:** `s2-plan-2.md:206`、`tools/codex_reasoning_ab.py:10210-10214,10228-10273,10443-10472`
- **重大度:** HIGH
- **帰結:** process が開始されなかった attempt が、軸 ledger の `attempt_count` に入り、`accounted_amount = 0.00000000` として集計され得る。resource 比較をゼロ方向へ歪める。
- **根拠:** プランは「実際に token が観測されていれば resource 消費へ含める」とする。一方、prelaunch failure row は token 4 field を `supervisor_row.get(..., 0)` で人工的に埋める (`:10244-10250`)。

replay failure は token を `None` にするため (`:10459-10462`)、プランの unavailable 処理に入る。しかし prelaunch failure は exact int の 0 を持つため、型 gate だけでは「観測されたゼロ」と区別できない。

cost helper の前に少なくとも次を検査すべきである。

- `process_started is False` または `prelaunch_failure is not None` なら `status="unavailable"`。
- token 値だけでなく token observation provenance があることを要求する。
- この attempt を axis `attempt_count` に含めるかを明示する。

### B-6 — 実装子 A/B は source の主 hunk は分離できるが、成果物全体では並列投入できない

- **対象:** `s2-plan-2.md:261-275`、`orchestrator/tests/test_codex_reasoning_ab.py:8260-8545`、`prereg-s5.md:39-55`、`prereg-s10.md:58-83`
- **重大度:** MEDIUM
- **帰結:** source の非重複 hunkだけなら merge 可能だが、同じ integration test と到達度表を両者が変更する。並列 branch を機械的に統合すると fake signature、cost assertion、文書状態のどれかを失う危険がある。
- **根拠:** プラン自身も `test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers` を両者の衝突面として認めている (`s2-plan-2.md:270-273`)。

具体的な衝突域は次である。

- `test_codex_reasoning_ab.py:8337-8342` と `:8491-8500`: A は `verify_snapshot` fake に `task_manifest=` を受けさせ、B は同じ test fixture の receipt/cost assertion を変更する。
- 同 test の `:8520-8545`: A は external manifest propagation を検査し、B は同じ `result` の resource/cost を検査する。
- `prereg-s5.md:42-53`: A が `:42,47,50`、B が `:53` を更新する。同一 Markdown table の近接 hunkである。
- `prereg-s10.md:58-83`: B の cost 状態更新と、親の lock 限定追記が同じ段落を触る。

`codex_reasoning_ab.py` の論理 hunkはおおむね分離されているが、同じ 11456 行の file なので line drift も大きい。**Aを先に、Bをその結果の上へ順次投入し、文書は親が最後に一回更新する**のが妥当である。

### B-7 — `resource_ledger` に key を 1 つ足すだけで落ちる既存テストは 0 件

- **対象:** `orchestrator/tests/test_codex_reasoning_ab.py:8202-8246,8260-8545,11266-11328,11455-11513,11554-11577,11934-11954`、`s2-plan-2.md:250-259`
- **重大度:** LOW
- **帰結:** additive な `normalized_cost` key と conditional な top-level ledgerだけでは既存 exact-schema test は落ちない。プランの「壊れうる既存テスト」列挙は、key 追加の blast radius と signature 変更の blast radius を混同している。
- **根拠:** resource 関連 assertion は長さ、個別 field、包含性しか検査していない。

該当テストは次の 7 件である。

1. `test_verify_replays_complete_fake_codex_experiment` — `:8221`、行数だけ
2. `test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers` — `:8528-8545`、行数・既存 field・verify/aggregate の生成物同士の equality
3. `test_aggregate_verified_uses_oracle_kind_and_keeps_task_model_axes_separate` — `:11315-11323`、既存 fieldだけ
4. `test_m9_post_treatment_failure_remains_in_denominator` — `:11469`、行数だけ
5. `test_asymmetric_technical_pair_retry_marks_mate_and_keeps_resources` — `:11512-11513`、行数と failure class
6. `test_incomplete_or_verifier_reason_nulls_quality_ledgers` — `:11577`、行数だけ
7. `test_single_turn_constant_is_not_emitted_as_resource_metric` — `:11948-11949`、特定 key の有無だけ

`test_bound_price...:8545` は exact equality だが、同じ aggregator が作る verify/aggregate 結果同士を比較しているため、両方へ同じ key が加われば落ちない。top-level aggregate result の key 集合を exact 比較するテストも存在しない。

ただし A の signature 変更では、`verify_snapshot` fake が新 keyword を受けない `:8340` と `:8494` などが実際に落ち得る。これは cost key 追加とは別件である。

### B-8 — 到達度文書は限定更新が必要で、§13 まで一括更新する P1 は広すぎる

- **対象:** `prereg-s5.md:32-55,58-59,61-104`、`prereg-s10.md:58-98`、`brief.md:71-75`
- **重大度:** HIGH
- **帰結:** parser optionや cost ledgerを追加しただけで「機構完了」「resource gate 完了」「price lock 完了」と更新すると、後続の受理集合を不当に広げる。正しい中間状態を記録する必要がある。
- **根拠:** §5.2 は「実装済み」を「内部 API と CLI の双方から到達できる」と定義するが (`prereg-s5.md:34-37`)、実験全体の manifest hash 束縛や cost gate consumer はない。

「更新しないと嘘になる」行は次である。ただし B-2/B-3 を残したまま単純に「実装済み」へ変えてはならない。

| 行 | 分類 | 必要な記述 |
|---|---|---|
| `prereg-s5.md:42` | 更新しないと嘘 | 「CLI 未接続」から「CLI 接続あり、invocation 間 manifest identity 未束縛」へ |
| `prereg-s5.md:47` | 更新しないと嘘 | `supervise_pair` の external manifest 到達を記録。ただし end-to-end 完了とはしない |
| `prereg-s5.md:50` | 更新しないと嘘 | task-specific selector の CLI 接続を記録 |
| `prereg-s5.md:53` | 更新しないと嘘 | 「cost 計算未実装」から「partial accounted cost ledger は実装、resource gate reader は未実装」へ |
| `prereg-s10.md:81-83` | 更新しないと嘘 | 同上。version 束縛、partial cost、gate 未接続を分離して記録 |

次は現状と食い違わず、変更すると protocol 改訂または虚偽になる。

| 行 | 分類 | 理由 |
|---|---|---|
| `prereg-s5.md:86-95` | 更新すると protocol 改訂 | acceptance `unbound` と fix/overall `inconclusive` の規定。今回の2機構では変わらない |
| `prereg-s5.md:96-104` | 更新すると protocol 改訂 | task-specific oracle、ledger、hash/count 束縛の要求。今回 scope 外 |
| `prereg-s10.md:79-80` | 更新すると虚偽 | §13 lock は power simulation で停止中 |
| `prereg-s10.md:90-98` | 更新すると protocol 改訂 | 全 run の凍結 version、価格改定時の新登録世代などの実験規則 |
| §13 の lock/gate 本文 | 更新すると protocol 改訂 | lock 完了、estimand、margin、gate 表を変えるなら新登録世代が必要 |

射影されたファイルには §13 本文そのものが含まれていないため、§13 の file:line 単位の分類はできない。確認できる正本引用は `prereg-s10.md:79-80` の「登録世代 lock 手続きは ... power simulation の段で停止」と、`s2-plan-2.md:279` の「cost 実装で完了扱いにしてはならない」である。

P1 は、上記 5 箇所の事実更新に限定するなら耐える。§5.3や§13を「この wave で閉じた」方向へ更新する裁定としては耐えない。

### B-9 — この wave 後も、事前登録された実験の実走可能性は上がったとは言い切れない

- **対象:** `brief.md:19-20,26,91-95`、`prereg-s5.md:89-108`、`prereg-s10.md:79-86`
- **重大度:** HIGH
- **帰結:** (a) は external manifest を各 invocation へ注入できるようにし、(c) は partial accounted cost を計算できるようにする。しかし certified held-out experiment の開始条件、gate 判定、overall の受理集合は変わらない。
- **根拠:** task-specific oracle は未実装、stage acceptance は `unbound`、fix gate と overall は `inconclusive`、price lock は未完了と原典が明記している。

未解消なのは少なくとも次である。

- `_load_adjudication` の task-specific oracle 対応と独立 oracle ledger
- task manifest の invocation 間 identity 束縛
- partial cost を読む resource metric/gate evaluator
- `cache_write` 欠測時の gate policy
- stage2/stage5 acceptance
- D674 により未実施の power simulationと §13 lock

したがって「事前登録の実走に一歩近づいた」という無限定の記述はできない。正確には、**「実走装置の局所的な未配線を減らしたが、登録 lock と acceptance/gate は動いていない」**である。

## 親 brief の P1〜P4 への評価

- **P1: 条件付き支持。** `prereg-s5.md:42,47,50,53` と `prereg-s10.md:81-83` の factual status 更新は必要。ただし §5.3 の acceptance や §13 lock を更新対象に含めるのは反対。blanket な P1 は誤りである。
- **P2: 条件付き支持。** `--task-manifest PATH` と未指定時の `TASK_MANIFEST` は妥当。しかし invocation 間で同じ bytes/hash を束縛しない設計では、実験レベルの入力口を閉じない。artifact chain への manifest digest 追加が条件である。
- **P3: 反対。** version 検査と cost 計算を別関数にする点は支持するが、resources 行と軸 ledgerへ載せるだけでは §11.2/§12 に効かない。P3を「費用機構を閉じる仕様」とするのは誤りである。
- **P4: 条件付き支持。** USD と decimal string は正しい。ただし生成値は `cache_write` を含まない `accounted_amount` であり、完全な cost、実請求額、resource gate 値とは呼べない。

誤りの中心は P3、次いで blanket な P1 である。P2は閉包不足、P4は命名・coverage 条件付きで成立する。

## scope 外だが real な所見

- `brief.md:19-20` と `prereg-s5.md:96-104` の task-specific oracle manifest、独立 oracle ledger、`_load_adjudication` 対応は依然必要である。今回は実装せず裁定パッケージへ回すべきである。
- partial cost を §12 gate でどう扱うかは protocol semantics である。`cache_write` 欠測を pass、fail、inconclusive のどれにするか、実装子が決めてはならない。
- D674 により power simulation と標本数下限が実施されず、§13 lock は停止中である。cost 実装を理由に再開・完了扱いしてはならない。
- `prereg-s5.md:89-95` の stage acceptance `unbound` と stage5 CLI 実行 verb 不在は残る。
- `prereg-s5.md:108` の served-model attest 不在、`:104` の cache control 不在も、model slug の一致では解決しない。
- 独立 custodian は D674 で見送られている。今回の task manifest/cost wave が補ったとは記録できない。

## 総括

段 2 プランは、brief の誤った「既存7 verb」前提を修正し、単一 CLI invocation 内の `task_manifest` 伝播はほぼ閉じている。しかし、task manifest の digest が schedule、packet、verdict freeze、aggregate reportへ保存されないため、工程途中で authority を交換できる。これを直さず「CLI 入力口を閉じた」と記録するのは危険である。

cost 側は model slug と SKU の集合が exact 一致しており、計算自体は発火可能である。ただし出力の reader、§11.2 resource metric、§12 gate、overall 接続が存在しない。さらに prelaunch failure の人工的な 0 token を実測ゼロとして価格化する穴がある。現プランのままでは「費用の正規化計算を成果判定へ接続した」とは言えない。

A/B は順次投入が妥当である。既存テストについて、resource row に additive key を 1 個足すだけで落ちる exact-schema test は 0 件である。pytest は実行しておらず、緑とは評価していない。