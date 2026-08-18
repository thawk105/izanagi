## 実装プラン

### 1. 宣言の所在と波及

[実測] `run_campaign(` の広域検索結果は `production_call_sites=16`、`test_call_sites=179`、合計 `195`。ただし `s8b_floor_campaign.py:5585` の別関数と同ファイルの呼出しを除く `orchestrator.campaign.loop.run_campaign` は、既存 inventory の本番 15 箇所 (`orchestrator/tests/test_campaign.py:4721-4741`) と AST 上の test 30 箇所である。

[提案] 採用する形は次の二層構造とする。

- 実効的な fail-closed は `orchestrator/campaign/loop.py:123-180` の keyword-only 必須引数 `declared_use_class: str` で実施する。既定値は置かない。
- 5 producer は各 module-level に `DECLARED_USE_CLASS = "exploration"` を持ち、呼出し時は `declared_use_class=DECLARED_USE_CLASS` とする。
- module-level 定数は族の宣言資料と meta-test の対象であり、runtime の唯一の強制点にはしない。
- `orchestrator/campaign/p2_2.py:144-146`、`backoff_repro.py:113`、`backoff_sweep.py:173`、`demo.py:57,66`、`s6_sort_sweep.py:367`、`s8a_trigger_sweep.py:469`、`sanity_silo.py:59` など既存 official caller も明示的に `"official"` を渡す。
- 5 producer の定数は `p3_kickoff.py:46`、`p3_s4_loop.py:91`、`p3_s4_red.py:63`、`p3_s4_loop_sort.py:98`、`p3_s4_loop_trigger_gating.py:93` 付近に置く。

module-level 定数だけでは、現在の実装が `campaign_namespace` だけを読む `loop.py:162-167` を通過できるため、宣言なし producer を実際には止められない。従って brief の P2 は部分的に反証し、必須 kwarg を実効契約とする。

### 2. 閉表と layout

[実測] `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1248` は `official`、`exploration`、`qualification`、`dry` の 4 値を列挙する。D162 は producer が宣言できるものを利用意図と raw 事実に限定している (`docs/decisions.md:8010-8016`)。

[提案] campaign sink で許可するのは次だけとする。

| `declared_use_class` | 処理 |
|---|---|
| `official` | `campaign_layout` |
| `exploration` | `exploration_campaign_layout` |
| `qualification` | layout 生成前に拒否 |
| `dry` | layout 生成前に拒否 |

2 種の constructor は既存の `orchestrator/campaign/layout.py:222-225` と `:479-487` をそのまま利用する。`qualification` は「適格性に提出した」意味であり、合格結果ではない (`docs/decisions.md:8010-8012`)。`dry` も qsub 事実の免除ではない (`docs/decisions.md:20738-20742`)。従って既存 2 layout へ暗黙変換せず、別 layout を新設もしない。

`loop.py:162-180` で値を検証し、拒否は `ident.campaign_id` の計算 (`loop.py:179`) と `layout.ensure()` より前に行う。

### 3. fail-closed の検査

[提案] 必須 kwarg と producer registry 相当の meta-test を併用する。

- 引数省略は Python の signature binding で `TypeError` とする。これは `loop.py:123-135` の既定値削除が実際の拒否行になる。
- 値検証は `loop.py:162-167` に置き、未知値、`qualification`、`dry` を `ValueError` で拒否する。
- `orchestrator/tests/test_campaign.py:4721-4824` の本番 caller inventory を拡張し、15 本すべてが `declared_use_class` を持つことを AST で検査する。
- `orchestrator/tests/test_p3_exploration_namespace.py:39-47` のファイル名依存の `_CAMPAIGN_DRIVERS = _DRIVERS[:-1]` は、5 module の `DECLARED_USE_CLASS` を読み、値が `exploration` のものを族として列挙する形へ変える。
- `:430-465` の AST 検査は補助検査とし、runtime の必須引数検査を代替させない。

正例は、明示した `declared_use_class="official"` と `"exploration"` がそれぞれ既存 root に到達すること。負例は、引数省略、`qualification`、`dry`、未知文字列で、`cid` と output directory が作られないこととする。現在の default official を検査する `test_campaign.py:8408-8425` は、既定値の正例テストから省略負例へ置換する。現在の未知 namespace 検査 `:8478-8496` も新しい field の負例へ更新する。

### 4. path と凍結 bytes

[実測] `output/campaigns` の検索は `16 files / 194 hits`、`output/exploration` は `6 files`。`orchestrator/campaign/s1_known_axes_freeze.py:340,375,427,461,529` には glob/join が 5 箇所ある。

[提案] `layout.py`、`s1_known_axes_freeze.py`、次の凍結 artifact は変更しない。

- `output/s1-freeze/known_axes_freeze.json`
- `output/s1-freeze/measurement_freeze.json`
- `output/s8b-freeze/holdout_freeze.json`

既存 5 producer の runtime test を `declared_use_class="exploration"` で実行し、`exploration_campaign_layout(str(cid), output_root).root` と一致すること、`output/campaigns/<cid>` が選ばれないことを固定する。対象の既存 test は `test_p3_exploration_namespace.py:223-245`、`:384-427`、および `test_campaign.py:8428-8476` である。bytes の比較対象を新たに再生成せず、既存 artifact の内容には触れない。

### 5. campaign-id

[実測] `orchestrator/campaign/ident.py:151-190` の `canonical_preimage` と `campaign_id` は `CampaignConfig` の spec、ccbench、search、trial のみを入力にする。既存の `test_campaign.py:8499-8521` は namespace が違っても同一 campaign-id になることを検査している。

[提案] `declared_use_class` を `CampaignConfig`、canonical preimage、campaign-id のいずれにも渡さない。上記既存 test の keyword を置換して維持すれば、追加の ID テストは必須ではない。`loop.py:136-141` の「path selector であり identity ではない」という契約も field 名に合わせて更新する。

### 6. 9 層の現状被覆

D162 の RF positive-artifact vertical slice は 0/9 であり (`docs/decisions.md:8049-8055`)、D500 も本 wave での実装を禁止している (`docs/decisions.md:20717-20742`)。以下は所在の実測であり、本 wave では変更しない。

| 層 | 実在する所在 | 現状被覆 |
|---|---|---|
| 計測 producer | `orchestrator/campaign/pipeline.py:592-616,1237-1311`、`orchestrator/qualification/collector.py:1120-1151` | RF receipt producer は不在。既存 campaign/T126 計測のみ |
| attempt registry | `orchestrator/qualification/attempt_ledger.py:312-373`、`s8b_floor_campaign.py:4592-4615` | T126 用は存在するが RF の 3-arm registry ではない |
| schedule validator | `s8b_oracle_manifest.py:278-315`、`s8b_oracle_driver.py:325-344` | oracle manifest 用で、RF receipt には未接続 |
| RF calculator | `orchestrator/qualification/contract.py:332-353`、`series.py:181-191,322-333` | T126 の relative 観測はある。RF calculator は不在 |
| 適格性権威 | `s8b_floor_stats.py:682-700`、`s8b_oracle_judge.py:478-505,680-694` | 既存 floor/oracle 権威はあるが RF artifact の authority ではない |
| 層 3 の次版 | `layer3_report.py:46-48,448-565,576-580` | 現行 report v3 のみ。certified selection consumer は未実装 |
| selector consumer | `s8b_selector_input.py:102-135`、`s8b_oracle_judge.py:680-700` | oracle selector はあるが RF artifact を消費しない |
| 材料レポート consumer | `layer3_report.py:430-436,500-517` | qualification lineage を拒否する既存 report のみ。RF consumer は不在 |
| 双射・変異検査 | `layer3_report.py:217-234,565`、`test_layer3_report.py:1605,1621`、`test_s8b_oracle_report.py:2829,3033` | 既存 protocol の検査はあるが RF 用の双射・変異 matrix は不在 |

D500 の指示どおり、この表の層には実装を広げない。

### 7. 新 D の条文案

[提案] 実ファイルは作成せず、`docs/spool/decisions/` 配下の次 wave decision fragment として起草する。README の placeholder 規則 (`docs/spool/decisions/README.md:5,28-35`) に従い、決定番号は未確定のままとする。

> campaign producer の利用意図 field 名を `declared_use_class` と確定する。値の閉表は `official`、`exploration`、`qualification`、`dry` とし、この field は利用意図と raw 事実の宣言に限り、適格性、admission、validator の結果を表さない。  
>
> T-318/T-337 の campaign producer 種別指定にある literal `artifact_role` は本決定で明示 supersede し、`declared_use_class` に置換する。ただし `artifact_role` は `orchestrator/campaign/s8b_oracle_exploration.py:24-35,48,61-63` と `s8b_oracle_artifacts.py:24-34,284-290` で探索 oracle 文書種別として現用であり、T-479 の裁定どおり改名しない。  
>
> `run_campaign` は `declared_use_class` を既定値なしの必須 keyword-only 引数として要求する。campaign sink が materialize できるのは `official` と `exploration` だけであり、`qualification` と `dry` は別途承認された layout、validator、consumer がない限り拒否する。  
>
> `declared_use_class` は `CampaignConfig`、canonical preimage、campaign-id に入れない。D162 の 9 層の実装禁止と D500 の RF 実装禁止は維持し、D162 決定 (11) の land 禁止だけを本 field の campaign declaration に限って解除する。既存 output path、凍結 artifact、既存 bytes は変更しない。

### 8. 変異事前登録

以下は実装前に登録する候補であり、変異実測は未実施である。

| 壊す production 行 | 落ちるべき test nodeid |
|---|---|
| `orchestrator/campaign/loop.py:132` に `="official"` を戻す | `orchestrator/tests/test_campaign.py::test_run_campaign_requires_declared_use_class` |
| `loop.py:162-167` で `qualification` を許可する | `...::test_run_campaign_rejects_unsupported_declared_use_class[qualification]` |
| `loop.py:162-167` で `dry` を許可する | `...::test_run_campaign_rejects_unsupported_declared_use_class[dry]` |
| `loop.py:162-165` の official mapping を exploration に変える | `...::test_run_campaign_official_declaration_preserves_root` |
| `loop.py:164-165` の exploration mapping を official に変える | `orchestrator/tests/test_campaign.py::test_run_campaign_exploration_namespace_reaches_lock_wal_and_pipeline` |
| `loop.py:179-180` で declaration を cfg に混ぜる | `...::test_run_campaign_namespace_does_not_change_campaign_id` |
| `p3_kickoff.py:111-121` の declaration を削除する | `orchestrator/tests/test_p3_exploration_namespace.py::test_driver_ast_supplements_runtime_namespace_gate[kickoff]` |
| `p3_s4_loop.py:958-962` を official に変える | `...::test_iteration_public_entry_routes_runtime_layout_and_selector[loop]` |
| `p3_s4_loop_sort.py:328-332` を official に変える | `...::test_iteration_public_entry_routes_runtime_layout_and_selector[sort]` |
| `p3_s4_loop_trigger_gating.py:640-648` の declaration を削除する | `...::test_iteration_public_entry_routes_runtime_layout_and_selector[trigger_gating]` |
| `p3_s4_red.py:168-181` の declaration を削除する | `...::test_main_public_entry_routes_runtime_layout_and_selector[red]` |
| `p2_2.py:144-146` の explicit official を削除する | `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` |
| `p3_kickoff.py:46` の定数を `"official"` に変える | `...::test_main_public_entry_routes_runtime_layout_and_selector[kickoff]` |

最初の行が、wave 前の暗黙 official (`loop.py:132`) を必ず捕捉する負例である。

### 9. P1-P5 の判定

| brief | 判定 | 根拠 |
|---|---|---|
| P1 | 賛成 | D500 は RF producer と周辺 3 kill を本 wave の対象外とする (`docs/decisions.md:20717-20750`)。5 p3 producer は `p3_kickoff.py:111-121`、`p3_s4_loop.py:958-962` などに実在する |
| P2 | 反証 | module-level 定数だけでは `loop.py:162-167` の runtime gate に届かない。実測上、広域 195 箇所に対し対象 caller は本番 15、test 30 |
| P3 | 賛成 | schema の 4 値は `receipt-schema-v1.json:1248`、D162 の意味制約は `docs/decisions.md:8010-8016` |
| P4 | 修正賛成 | official/exploration は `layout.py:222-225,479-487` に対応するが、qualification/dry は D162 `:8010-8012` と D500 `:20738-20742` により拒否する |
| P5 | 両方採用 | 必須 kwarg が実効 fail-closed、caller inventory と `test_p3_exploration_namespace.py:430-465` が網羅性の補助検査となる |

テスト、pytest、mutation 実測は実施していない。親 wave が実行する前提で、ここでは `rg`、行番号確認、AST の静的集計だけを根拠とした。

## 総括

[提案] 実効契約は `run_campaign` の必須 `declared_use_class` とする (`loop.py:123-180`)。  
[提案] 5 producer の module-level 定数は族の宣言と meta-test に使う。  
[実測] 対象 caller は本番 15、test 30で、広域検索は 195 箇所だった。  
[提案] campaign sink は official/exploration のみ layout 化し、qualification/dry は拒否する。  
[提案] layout、campaign-id、canonical preimage、凍結 bytes は変更しない。  
[実測] RF の 9 層は既存の別 protocol を除き、positive-artifact vertical slice として未被覆である。  
[提案] D162 の field land 禁止だけを解除し、D500 の RF 実装禁止は維持する。