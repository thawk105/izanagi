## 差分の要約

変更は次の4ファイルのみ。`git diff --check` と4ファイルの AST parse は成功した。pytest は実走していない。

- `orchestrator/campaign/s8b_ratified_freeze.py:3558-3641`
  - g1 限定の `assert_g1_floor_selection_identity` を追加。
- `orchestrator/campaign/s8c_result_judge.py:26-30,2067-2070,2118,2172-2175,2202-2208`
  - 共通 loader/gate と、verify/publish 両経路への配線を追加。
- `orchestrator/tests/test_s8b_ratified_verify.py:872-891,1461-1478`
  - g1 mismatch、valid g1、g2 no-op の3 test を追加。
- `orchestrator/tests/test_s8c_result_judge.py:437-479,1564,1584-1627,1655,1758-1802`
  - fixture を新 API に追随させ、verify/publish の拒否と正例を追加。

## 所見

1. **対象 `orchestrator/campaign/s8b_ratified_freeze.py:3591-3607,3625-3629`**  
   **何が誤りか:** `_assert_floor_selection_identity` は supplied `selected_rel` の namespace をそのまま探索するが、その path の `env_tag` / `proto8` を記録 protocol に束縛していない。さらに `validate_selected_certificate=False` のため、path 起動秒と selected certificate も束縛されない。launch 経路ではこれらは選択検査より前に検証されるが、この狭い helper にはその前提がない。別 namespace や前倒し時刻の path を持つ approved g1 なら、真の namespace に earlier eligible run があっても探索から外せる。  
   **放置時の成果物影響:** `verify_floor_bytes` が receipt を発行し、`publish_result_table` が3表を生成できる。DW-G05 の拒否集合が閉じない。  
   **must-fix か nit か:** must-fix。段4裁定の修正も必要。  
   **推奨する直し方:** historical protocol の canonical hashを求め、selected path の `env_tag` / `proto8` と protocol、generation の `env_tag` を照合する。加えて selected certificate と path 起動秒を検証する。いずれも current admission ではなく、失敗は許可済みの `floor-selection-unverifiable` に畳む。

2. **対象 `orchestrator/tests/test_s8c_result_judge.py:437-449,1692-1728`**  
   **何が誤りか:** `_verified_floor` が loader と selection stub を同じ object に束縛した後、`test_publish_requires_current_ratified_floor_receipt` は loader だけを別 object へ上書きする。publish は receipt 比較へ到達せず、古い selection stub の `candidate is ratified` assertion で落ちる。test は例外理由を検査しないため緑になる。  
   **放置時の成果物影響:** current receipt の equality gate が退行しても test が検出せず、foreign receipt から3表を生成する回帰を許し得る。  
   **must-fix か nit か:** must-fix。  
   **推奨する直し方:** current document に対して `_patch_ratified_floor` を使い loader/gate を一緒に更新し、`match="floor receipt is not from the current ratified freeze"` を要求する。

3. **対象 `orchestrator/tests/test_s8b_ratified_verify.py:1461-1478`**  
   **何が誤りか:** M3 は `_source_record_path_sha` を AssertionError sentinel に置換して kill する。しかし実体の g2 fixture は新しい protocol namespace に earlier run がなく、枝を無条件実行しても自然状態では受理されたままになる。赤は内部観測 sentinel によるもので、DW-M03 が要求する受理集合または domain fail-closed の変化ではない。  
   **放置時の成果物影響:** 書けない。変異帰属を実際より強く報告する。  
   **must-fix か nit か:** must-fix。  
   **推奨する直し方:** g2 の同一 namespace に earlier eligible run を置き、baseline は no-op で受理、M3 は `floor-selection-rule-mismatch` で拒否される入力へ再照準する。

4. **対象 `orchestrator/campaign/s8c_result_judge.py:2172-2175`**  
   **何が誤りか:** `load_ratified_freeze` 自体の `no-active`、dirty、schema error などもすべて `"ratified floor selection is invalid"` と表示される。新 gate の理由は広い `except` に飲まれていないが、既存 loader failure が selection failure にすり替わる。  
   **放置時の成果物影響:** 書けない。診断上の誤分類のみ。  
   **must-fix か nit か:** nit。  
   **推奨する直し方:** loader と selection assertion の例外境界を分け、selection assertion 由来の3 reason だけを selection error として保持する。

## 発火の判定

両経路で発火する。

```text
verify_floor_bytes
└─ _load_selection_checked_ratified_floor
   ├─ load_ratified_freeze
   └─ assert_g1_floor_selection_identity
      └─ g1: _hf._assert_floor_selection_identity
```

- gate は candidate path の解析や床値 bytes 読込みより前。
- `RatifiedFreezeError` は `s8c_result_judge.py:2172` で広い `except Exception` より先に捕捉される。

```text
publish_result_table
└─ _validate_verified_floor
   └─ _load_selection_checked_ratified_floor
      ├─ load_ratified_freeze
      └─ assert_g1_floor_selection_identity
         └─ g1: _hf._assert_floor_selection_identity
```

- `publish_result_table:2411` で発火し、output path の検査・transaction directory・3表書込みより前。
- `RatifiedFreezeError` は `:2203` で広い `except Exception` より先に捕捉される。
- mismatch test は3 pathすべてを個別に不在確認している。

したがって配線は実効。ただし所見1の前提欠落により、検査内容そのものが不完全である。

## 偽緑の判定

| test | 実体／stub | 対象実装を戻した場合 | 判定 |
|---|---|---|---|
| `test_g1_selection_helper_rejects_rule_mismatch` | 実 helper・実 RatifiedFreeze | g1 gateをno-op化すると例外が消えて赤 | 有効 |
| `test_g1_selection_helper_accepts_valid_selection` | 実 helper・実 RatifiedFreeze | no-opでも緑 | 過剰拒否の正例として妥当 |
| `test_g1_only_selection_helper_is_noop_for_g2` | 実 g2、内部 sentinel | M3で赤 | DW-M03上は偽 kill |
| `test_floor_verification_rejects_selection_mismatch` | loader/gateともstub | verify callをbare loaderへ戻すと成功して赤 | M1配線testとして有効 |
| `test_publish_rejects_when_selection_mismatch` | loader/gateともstub | publish側をbare loaderへ戻すと3表が作られて赤 | M2配線testとして有効 |
| `test_valid_g1_selection_still_verifies_and_publishes_three_tables` | loader/gateともstub | consumer配線を戻すと call count 0 で赤 | 配線正例のみ。実 gate の統合証明ではない |
| `test_floor_verification_derives_expectations_from_ratified_freeze` | 新 no-op stubへ追随 | gate配線を戻しても緑 | 既存性質testとして妥当 |
| `test_floor_bytes_mismatch_raises_dedicated_exception` | 新 no-op stubへ追随 | gate配線を戻しても緑 | 既存性質testとして妥当 |
| `test_publish_requires_current_ratified_floor_receipt` | loaderのみ後から上書き | 新 gate有無にかかわらず例外になり得る | 偽緑。所見2 |

正例は実 helper testとstub配線testに分離されており、完全な実体統合 test ではない。

## 変異の帰属

| 変異 | 判定 | 理由／再照準 |
|---|---|---|
| M1 | 殺せる | gateを外すとstub loader、binding、bytesがすべて有効なので `verify_floor_bytes` が成功する。他の拒否による mask はない。 |
| M2 | 殺せる | evidenceとcurrent bindingは一致する。gateを外すとpublishが成功して3表を作るため、赤理由は一意。 |
| M3 | 殺せない | 現 fixtureでは無条件実行しても自然な受理集合は変わらず、sentinelによる内部観測だけが赤になる。同一 namespace の earlier eligible runを持つg2へ再照準し、mutantだけを domain reasonで拒否させるべき。 |

## 回帰の波及

`s8b_ratified_freeze` を名指す consumer test は全18本:

- `test_autonomous_trial_completeness.py`
- `test_ccbench_spawn_sites.py`
- `test_official_perf_closure.py`
- `test_p3_autonomous_workload_trial.py`
- `test_s8b_approved.py`
- `test_s8b_binding_driftguards.py`
- `test_s8b_floor_stats.py`
- `test_s8b_holdout_admission.py`
- `test_s8b_oracle_driver.py`
- `test_s8b_oracle_manifest.py`
- `test_s8b_oracle_report.py`
- `test_s8b_protocol_builder.py`
- `test_s8b_ratified_freeze.py`
- `test_s8b_ratified_verify.py`
- `test_s8b_verdict.py`
- `test_s8c_acceptance_receipt_v2.py`
- `test_s8c_preregistration_invariant.py`
- `test_s8c_preregistration_predicates.py`

`s8c_result_judge` を名指す consumer test は全3本:

- `test_s8c_preregistration_invariant.py`
- `test_s8c_preregistration_predicates.py`
- `test_s8c_result_judge.py`

実装子の列挙漏れはない。

赤になり得る／静的確認が必要なもの:

- `test_s8c_result_judge.py`: 所見2の偽緑あり。
- `test_ccbench_spawn_sites.py`: 新しい process API call はなく、count変化なし。
- `test_official_perf_closure.py`: 監視対象 functionへの変更なし。
- `test_s8b_ratified_freeze.py`: 同 module 内を除外する constructor scanに影響なし。
- s8b moduleには `__all__` や公開名exact-set testは見つからず、新API追加による一覧赤はなし。
- s8cの `__all__` は3名のままで、`test_public_names_are_exactly_three` に影響なし。

C07は静的には引き続き `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`:

- 新 helperは private functionなのでpublic function集合を変えない。
- `verify_floor_bytes` から新 helperへ到達し、その内部の `load_ratified_freeze()` はliveかつ戻り値が assertion と return に使用される。
- 新 importはC07のpublic名・condition/table集合を変えない。
- `UNSATISFIED` へ落ちる構造変化はない。

新規 test file はない。file集合メタテスト・自走 harness・allowlistへの登録は不要。duration ledgerは未登録nodeidをfail-softに扱うため必須更新ではない。

## scope 逸脱

なし。

変更は裁定済みのproduction 2ファイルと既存test 2ファイルだけ。oracle manifest群、C06群、残件2、残件3のfileには差分がない。

## 裁定への反論

段4 A1の「`validate_selected_certificate` は既定False」が誤っている。

launch側はこの呼出し以前にselected certificate、protocol hash、path namespace、起動秒を検査するため、Falseでも選択関数の前提が成立する。新しい狭いhelperにはその前段がない。これはD1312自身の「起動時刻を検証しなければpath時刻はただの名前」という理由とも衝突する。

裁定パッケージ候補は、g1限定のまま以下だけを許可する修正:

- selected pathのenv/protoとrecorded protocolを束縛する。
- selected certificateのprotocol/run-id/起動秒を束縛する。
- current contract/build admission、closure、activation HEAD、live scanは持ち込まない。
- 失敗は既存3理由のうち `floor-selection-unverifiable` に限定する。

C06群の「成果物影響0」判定には反論なし。C05前後で受理集合は空のままで、変わるのは診断理由だけである。

## 残る不確実性

- read-only指示に従いpytestは未実走。緑とは申告しない。
- C07 statusはAST規則との静的照合による推論で、evaluator自体は未実走。
- 所見1のcrafted approved g1は実行 fixtureで再現していない。
- 全consumer suiteのimport・collection結果は親の実走確認が必要。

## 総括

両public経路へのgate配線と例外順序は実効である。  
最重所見は、selected path／certificateの束縛がなく、earlier-run探索のnamespaceと時刻を回避できる点。  
既存current-receipt testには新stub由来の明確な偽緑がある。  
M1・M2は帰属できるが、M3はDW-M03基準では殺せない。  
段4裁定を修正してから実装とtestを直すべきである。