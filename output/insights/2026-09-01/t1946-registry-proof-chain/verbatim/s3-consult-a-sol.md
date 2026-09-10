## 所見

### 1. production では v5 gate が stuck-false になり、D1114 が発火する

- `重大度`: blocker
- `根拠 file:line`: `orchestrator/campaign/s8b_floor_campaign.py:5984-6034,6584-6585,7702-7779`、`orchestrator/campaign/s8b_floor_attempt_launcher.py:648-670`、`plan.md:79,91-98,109-138`、`rulings-verbatim.md:96-109`
- `再現する条件`: 通常 campaign を attempt registry の無い共有 root で完走させる。現行測定は `self.measure_fn()` を直接呼び registry を作らない。plan の v5 producer は発行前 inspector で不在を拒否する。
- `成果物への影響 1 行`: `.result.json.pending` 以前で停止するため、新規 certified 選択、floor report、その参照は一件も発行されず、束縛保証は空の受理集合に対して恒真になる。

public `launch_floor_attempt()` の production 呼出しは 0、production import 元も 0 だった。test は `test_s8b_floor_attempt_launcher.py:20` の alias import 1 件、public 呼出しが `:664` の 1 件、test-only helper 呼出しが `:317,393,436,486,626` の 5 件である。production 全 Python AST について alias import、`__import__`、`importlib.import_module`、`getattr`、文字列解決も調べたが追加経路は無かった。

### 2. s8c の最終 inspector は plan の live gate を通らない

- `重大度`: must-fix
- `根拠 file:line`: `orchestrator/campaign/s8c_result_judge.py:2103-2163,2166-2209,2384-2409`、`orchestrator/campaign/s8b_ratified_freeze.py:1399-1418,3262-3275`
- `再現する条件`: ratified 済み v5 floor source の registry を削除後、`verify_floor_bytes()` の receipt を `publish_result_table()` へ渡す。前者は ratified path/hash と bytes hashだけを検査し、後者も `load_ratified_freeze()` との参照一致しか再検査しない。
- `成果物への影響 1 行`: registry が存在しなくても `official_status` と `selection_evaluation` 表を発行でき、certified 選択とレポートが registry 不在の floor source を参照する。

D538 はこの入口を出所検証専用にしているが、registry の live 再検証を行わない根拠にはならない。床値を `judge()` の数値入力へ渡さず、`ReverifiedFreeze` を出所 receipt の前提にする形なら D538 の値分離は維持できる。

### 3. 変異事前登録の複数候補に帰属がない

- `重大度`: must-fix
- `根拠 file:line`: `plan.md:234-248`、`orchestrator/campaign/attempt_registry_core.py:442-463,1022-1037`、`orchestrator/campaign/s8b_floor_stats.py:759-768`
- `再現する条件`: 次の変異を単独で適用する。
  - `plan.md:245` の expected binding 比較を削除しても、正常 artifact と別 freeze の live proof は reported/live 比較で先に拒否される。artifact proof も別 freeze に揃えなければ、この行の必要性を検査できない。
  - `plan.md:242` の inspector 呼出しを削除しても、v5 pure verifier の expected proof 欠落拒否で赤のままになりうる。
  - `plan.md:243` の missing→zero head は、正の `row_count` 要求 (`plan.md:89`) が先に拒否しうる。
  - `plan.md:246` の producer field 削除候補に対し、予定 test は「field を落とす assembler を注入」するため、変異対象の本来の挿入行を実行しない。
  - `plan.md:244` は event hash 再計算削除と previous hash 比較削除を一つの tamper testへ束ねており、一方の gate が他方の変異を隠す。
- `成果物への影響 1 行`: expected binding 検査が欠けても mutation matrix が合格扱いになり、artifact proof と別 freeze の registry を同時に揃えた certified 入力が受理されうる。

特に別 freeze 負例は、registry と artifact proof の両方を別 freeze に揃え、top-level result の expected freeze だけを元の値に残す必要がある。これなら explicit expected-binding gate を消したときだけ通る。

### 4. 一部の負例は proof-chain 束縛ではなく部品検査の負例である

- `重大度`: nit
- `根拠 file:line`: `plan.md:205-232`
- `再現する条件`: `test_attempt_registry_inspection_rejects_row_hash_chain_tamper` や producer の field 欠落 test だけを残し、certified verifier から inspector 呼出しまたは reported/live 比較を外す。前者は standalone inspector、後者は exact-key gateだけで依然拒否する。
- `成果物への影響 1 行`: runtime の値は直ちに変わらないが、テスト成果物が「certified 選択が registry に束縛された」という主張を単独では支えない。

正しい向きなのは、少なくとも reported head 改竄、end-to-end registry 不在、新規 candidate の v4 downgrade である。chain tamper と missing/empty inspector test は部品の正当性検査としては有用だが、束縛の負例とは分けるべきである。

### 5. 規律 2 の問いには、文字どおりには「既存拒否→受理」がある

- `重大度`: nit
- `根拠 file:line`: 現行拒否は `orchestrator/campaign/s8b_floor_stats.py:734-748`、`orchestrator/campaign/s8b_ratified_freeze.py:2333-2356,2385-2390`。受理追加は `plan.md:83-89,102-106,125-130`。
- `再現する条件`: exact v5 shape、正常 registry proof、正常 live registry を持つ同一 bytes を変更前後へ渡す。変更前は未知 schemaまたは余分 keyで拒否され、変更後は受理される。
- `成果物への影響 1 行`: 受理集合には新しい v5 成果物が追加されるが、既存 v4 の拒否集合を受理へ変える計画ではない。

これは厳しい v5 の新設そのものであり、規律 2 の実質的な弱体化ではない。ただし `brief.md:30-33` の「既存の拒否が1件でも受理へ」は文字どおりには満たせないため、「既存 v4 input の受理面」と限定すべきである。

## 層の網羅表

| 層 | 実経路 | plan の対応 | 判定 |
|---|---|---|---|
| producer | `s8b_floor_campaign.py:5984-6034,6584-6622,7702-7779` | v5 proof取得、field挿入、自己検査を追加 | 部分実装。registry writerは無く、通常経路は停止 |
| pure verifier | `s8b_floor_stats.py:682-768` | v5 exact fieldと reported/expected 完全一致 | 実装予定。単独では live 実在を保証しない |
| live verifier | `s8b_floor_stats.py:1036-1082` | v5 のみ inspector を呼び pure verifierへ渡す | 実装予定。caller proof注入面を作らない点は妥当 |
| holdout 経路 | `s8b_holdout_freeze.py:1429-1439,1620-1630,2047-2052` | 新規 candidate は current v5限定、共通 live wrapperを使用 | 実装予定。通常 producerの v4 downgrade は閉じる |
| ratified 経路 | `s8b_ratified_freeze.py:3253-3302,3548-3555` | schema-aware key検査後に共通 live wrapper | 実装予定 |
| historical reverify | `s8b_ratified_freeze.py:3558-3568` → `:3262-3275` | v4は現行規則、v5はregistry必須 | 実装予定。非遡及を維持 |
| s8b 最終 consumer | `s8b_oracle_report.py:2547-2559`、`s8b_oracle_judge.py:749-758`、`s8b_verdict.py:826-840` | いずれも `reverify_published_freeze()` 経由 | 共通 core により間接的に実装 |
| s8c 最終 inspector | `s8c_result_judge.py:2103-2209,2384-2409` | planに記載なし | 未実装。registry不在でも公式3表を発行可能 |

名指しされた7層に加え、実際に certified 選択表を発行する s8c 最終経路があるため、実効上は8層である。plan は verifier 系6層と producer の proof emitterを扱うが、producer writerと s8c 最終 inspectorを扱わない。

版の決定者は通常 producerではなく共有定数である。`assemble_result()` は schema 引数を持たず (`s8b_floor_campaign.py:6474-6477`)、`s8b_floor_contract.py:34` を `s8b_floor_campaign.py:163` で束縛して `:6585` に書く。新規 candidate は `s8b_holdout_freeze.py:1437-1440` で current schemaを強制するため、通常の新規発行経路に v4 自称回避は見つからない。

## 親 brief と親実測への異議

- `brief.md:9-14` は writer配線を scope外にする一方、`:121-126` で post-wave の新規 certified 選択が束縛されると一般化している。production writer 0件が確定した以上、この組合せは「新規選択0件」による恒真であり、D1114 と両立しない。
- `parent-findings.md:80-82` の「genesisしか無い registry と空 registryを headで区別できない可能性」は誤り。s8b genesis は chain key必須 (`s8b_attempt_profile.py:267-289`) で、index 0 の hashを持つ (`attempt_registry_core.py:1497-1500`)。zero headになるのは chained rowが無い入力だけ (`:253-259`) で、正規 readerは空自体を拒否する (`:986-1004`)。
- brief と parent-findings の consumer閉包は s8c の `verify_floor_bytes()`／`publish_result_table()` を含めていない。これは公式選択表を発行する最終参照面であり、層網羅として不足している。
- production caller 0件という親実測自体には同意する。ただし「呼び手6件」は public API 1件と test-only helper 5件の合計であり、public `launch_floor_attempt()` の直接呼び手は `test_s8b_floor_attempt_launcher.py:664` の1件だけである。
- tracked repository に発火済み floor result／registry が無い点も独立確認と一致した。repo外未確認という `parent-findings.md:68` の限定は必要である。

## plan に同意する点

- v5 exact keyで fieldを無条件に要求し、v4では禁止するため、「fieldがあれば検査する」分岐はない。
- producerは schemaを引数で選べず、新規 holdout candidateの current-v5境界もある。
- pure verifierと shared filesystemを読む live wrapperを分離し、live wrapperに expected proof注入面を作らない方針は妥当である。
- historical v4をregistry検査から外す非遡及設計もD1194と一致する。

## D1114 判定

1. **(a) は成立する。** 現行 schema は v4だけで proof fieldも無い (`s8b_floor_contract.py:34,81-87`)。tracked `registry.jsonl` は0件で、tracked `result.json` 12件にも floor-result schemaは無かった。必読文書にも発火済み artifact path／計測IDの名指しはない。

2. **(b) は成立する。** production import／public callerはともに0件で、通常 campaignは `self.measure_fn()` を直接呼ぶ (`s8b_floor_campaign.py:6031-6034`)。planどおり currentをv5にして inspectorを結果組立前へ置くと、missingを `s8b_holdout_admission.py:4969-4975` から拒否へ変換し、通常経路では `:7724` の組立前、遅くとも live self-check `:7741-7761` で止まる。staging `:7772` と publish `:6818` へ到達しない。registry不在のまま v5 resultを発行する経路はない。

3. **D1194 と D1114 は両立する。** D1194は完成形の意味を「新規成果物だけ束縛」と決め、D1114は writer／consumerの片側だけを先行 landしない順序規則である。writer配線と検査を同じ到達可能な単位にすれば両方を満たせるが、D1193が留保した予算配置の裁定が先に必要である。

4. **結論: 設計を凍結して裁定へ返すべき。**  
   (a) と (b) がともに成立する。  
   現 plan は既存 campaignを停止させ、成功例をtest fixtureだけで人工生成する片側実装である。  
   writer配線を scopeへ加える権限と予算配置を裁定してから、到達可能な一体設計として再開すべきである。

## 総括

- D1114 が発火するため、本 wave は land 不可。
- plan の v5述語自体は恒真ではないが、production受理集合が空になり保証全体が恒真化する。
- s8c 最終 inspectorと変異帰属に追加欠陥がある。
- pytestは未実走で、以上は base `11b44e2d1` の静的検査結果である。