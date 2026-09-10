## 親の実測の再測結果

1. **支持 — load-only 3 群のアンカー。** 現 HEAD `2bf9cf387` では次の行が正しい。

   - oracle manifest: `orchestrator/campaign/s8b_oracle_manifest.py:1205`
   - s8c verifier/publish: `orchestrator/campaign/s8c_result_judge.py:2108,2188`
   - C06 budget: `orchestrator/campaign/p3_autonomous_workload_trial.py:4640`

2. **支持（到達可能な production 経路に限定）— 第4の load-only consumer は見つからない。**

   - judge/report/verdict は load 後に historical `reverify_published_freeze` を通る: `s8b_oracle_judge.py:749-750`、`s8b_oracle_report.py:2547-2550`、`s8b_verdict.py:828-829`。
   - oracle driver は public v2 経路で `launch_validate` を通る: `s8b_oracle_driver.py:636-656,1328-1344`。
   - 同 driver の `:488` に bare load はあるが、private `_gate_check_core` の全 repo 内 caller からは、非 v2・既存 error・既に launch-validated のいずれかでしか到達せず、第4の到達可能 consumer ではない。
   - alias、属性参照、`getattr`、`import_module`、文字列参照を含む静的走査でも追加経路はない。

3. **訂正 — 強制済み 2 点は構文上・fixture 上は到達可能だが、現 repository では発火不能。**

   - candidate 強制は `s8b_holdout_freeze.py:2053`。合成 fixture では実際に拒否されることが `test_s8b_holdout_freeze.py:2160-2190` に固定されている。
   - ただし production 現物では `BUDGET_APPROVAL_SHA256=None` (`s8b_holdout_freeze.py:52`) のため、`:2018` → `_budget_approval_authority:1298-1305` で先に停止する。
   - current launch 強制は `s8b_ratified_freeze.py:3305`。合成 fixture は `test_s8b_ratified_verify.py:854-869` で到達する。
   - g2 は先行 gate `s8b_ratified_freeze.py:3107-3110` で拒否されるため `:3305` へ到達しない。現物の active generation と official floor result も 0 件で、live 発火実績はない。

4. **支持 — historical reverify への間接伝播はない。**

   `_launch_validate` の選択検査は `result_type is LaunchValidatedFreeze` の枝だけ (`s8b_ratified_freeze.py:3303-3321`)。historical は `ReverifiedFreeze` を渡す (`:3558-3568`)。既存負例も `test_s8b_ratified_verify.py:890-895` で固定されている。plan は loader とこの共通 core を編集しない。

5. **支持。ただし一般化は訂正 — `s8c_result_judge` の production importer/caller は 0 件。**

   公開関数は `judge:1947`、`verify_floor_bytes:2103`、`publish_result_table:2384`。直接 import、alias import、動的 import、production call は見つからない。一方で production の静的 source consumer は存在する。`s8c_preregistration_evidence_contract.v1.json:272-296` が module と3関数を名指しし、`s8c_preregistration_evidence.py:3021-3317` が AST と loader 到達性を検査する。したがって「production 依存も 0」ではない。

6. **支持 — production module 名による Python test grep は plan の列挙と一致。**

   - `s8c_result_judge`: `test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、`test_s8c_result_judge.py`
   - `p3_autonomous_workload_trial`: `test_attempt_registry_core_s8b_profile.py`、`test_autonomous_trial_completeness.py`、`test_campaign.py`、`test_claude_transport.py`、`test_layer3_admission_diagnosis.py`、`test_layer3_report.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_trigger_gating.py`、`test_reflux_formal_consumer.py`、`test_reflux_origin_binding.py`、`test_reflux_originless_compatibility.py`、`test_role_session_isolation.py`、`test_s8c_arm_inputs.py`、`test_s8c_budget.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、`test_trial_registry.py`
   - `s8b_oracle_manifest`: `s8b_oracle_spec_fixture.py`、`s8b_v2_freeze_fixture.py`、`test_s8b_binding_driftguards.py`、`test_s8b_experiment_numbers.py`、`test_s8b_holdout_admission.py`、`test_s8b_materialization.py`、`test_s8b_oracle_artifacts.py`、`test_s8b_oracle_driver.py`、`test_s8b_oracle_judge.py`、`test_s8b_oracle_manifest.py`、`test_s8b_oracle_manifest_contract.py`、`test_s8b_oracle_n_pilot.py`、`test_s8b_oracle_report.py`、`test_s8b_ratified_freeze.py`、`test_s8b_verdict.py`

7. **反証 — 編集面の親実測は現在では古い。**

   - plan 宣言 7 path と交差する全 worktree の未 commit 差分は現在 0 件。
   - t1999 worktree も clean。現在は branch 固有 commit が `s8b_oracle_driver.py`、`test_s8b_oracle_driver.py`、`test_s8b_oracle_manifest.py` を変更しており、「37 file 未 commit」は成立しない。production `s8b_oracle_manifest.py` は依然非接触。
   - literal `main..<branch>` では、README のみが6 branch、Unit A の4 file＋README が `worktree-dev-wave-t1506-mocc-trace0` と交差する。ただし全7 branchについて `main...branch` の予定 path 差分は 0。すべて main 側の後続変更による tree 差で、branch 固有の編集競合ではない。
   - Unit B は予定 path と直接交差しないが、既存 `test_s8b_oracle_manifest.py` の fixture 追随を必要とするため、t1999 land 後の rebase/所有更新が依然必要。

## 所見

### 1. `launch_validate` の全面再利用は新しい g2 拒否枝を3群へ密輸する

- **対象:** plan 残件1、特に `plan.md:46,59,87,216,229`
- **何が誤りか:** plan は「既存 gate の再利用なので新しい g2 述語ではない」とするが、consumer の受理集合から見れば新規拒否である。static loader は otherwise-valid g2 を受理する (`test_s8b_ratified_verify.py:1266-1273`)。一方 `launch_validate` は artifact I/O より前に g2 を拒否する (`s8b_ratified_freeze.py:3107-3110`、`test_s8b_ratified_verify.py:1402-1410`)。この call を3群へ追加すれば、各 consumer に新しい g2 挙動が生じる。
- **放置時の成果物影響:** 将来 g2 が active になった場合、oracle manifest candidate は作られず、s8c floor receipt/table は作られず、C06 は C05 authority にすら到達しない。certified 選択は増えないが、公開物・参照・受理集合は狭まる。
- **親が採るべき対応:** 現 plan のまま実装へ送らない。少なくとも current validation の適用を g1 に限定して既存 g2 経路を変えない設計へ直す。g2 の新しい受理・拒否を決める必要が出るなら段4でユーザー裁定へ返す。

### 2. 選択強制の scope を越えて full current admission と新しい主張を持ち込む

- **対象:** `plan.md:31-46,55-74,81-91,216`
- **何が誤りか:** `launch_validate` は選択だけでなく activation HEAD、generation scope、current contract/build admission、artifact binding、live scan 等を通す (`s8b_ratified_freeze.py:3073-3545`)。plan 自身も selection mismatch より広く受理集合を狭めると認めている。D1312 は loader/historical へ current policy を入れない境界を定めたもので、load-only consumer 全体を full current admission に昇格する積極的許可ではない。さらに「公開物が current admission に束縛された」「current launch validation 済み」という新しい主張は D1313 の (a)(b)(c) に含まれない。
- **放置時の成果物影響:** earliest selection は正しい static-valid g1 でも、HEAD drift・current policy drift 等で manifest、s8c table、C06 の参照が新たに消える。拒否理由・レポートは「current launch validation」を主張する一方、D1241 の certified 上限を解除する証拠にはならない。
- **親が採るべき対応:** 「selection だけを強制する」のか「全 current launch admission を consumer 契約にする」のかを段4で裁定する。後者なら、non-certifying 上限を維持したまま許される追加主張を明示的に追加裁定する必要がある。

### 3. oracle の identity `assert` は恒真で、保護として数えられない

- **対象:** `plan.md:30-34` の `assert validated.ratified is ratified`
- **何が誤りか:** production `launch_validate` は入力 `ratified` をそのまま結果へ格納する (`s8b_ratified_freeze.py:3538-3544`)。成功後にこの assert だけが落ちる production 入力は構成できず、`python -O` では消える。
- **放置時の成果物影響:** 受理集合・成果物値・参照は変わらない。identity 防護が1本増えたという説明だけが過大になる。
- **親が採るべき対応:** 削除するか、単なる内部 sanity check と明記して gate・変異・保証数へ数えない。

### 4. t1999 との調整根拠が「未 commit 所有」のまま古い

- **対象:** brief 実測1、plan `:5,48,157,210`
- **何が誤りか:** t1999 は現在 clean で、関連3 file は branch commit 済みである。予定 production file との直接交差はないが、Unit B を緑にするにはその branch が変更した既存 manifest test の fixture 追随が必要である。
- **放置時の成果物影響:** 古い「未 commit 37 file」を根拠に待ち続けるか、逆に既存 test を無視して oracle production だけ変更し、既存正例を赤にする。
- **親が採るべき対応:** t1999 の land 状態を段4/実装直前に再取得し、land 済みなら rebase 後に既存 fixture を正規に更新する。未 land なら Unit B を停止する。

## 恒真判定

| plan が足す検査 | 実際に拒否できる入力 | 判定 |
|---|---|---|
| oracle manifest の `launch_validate` | static-valid g1だが、同 namespace に導出適格な earlier run がある入力 | 非恒真 |
| `assert validated.ratified is ratified` | production `launch_validate` 成功後に拒否される入力を名指しできない | **恒真・装飾** |
| s8c `verify_floor_bytes` の current validation | bytes/ratified refs は一致するが selection mismatch の active g1 | 非恒真 |
| s8c publish 時の再 validation | verify 後に earlier eligible run が加わり、receipt binding 自体は同じ入力 | 非恒真 |
| C06 の current validation | static-valid selection-mismatch g1。C05 authority 呼出し前に拒否 | 非恒真 |
| 上記すべての wholesale `launch_validate` | otherwise-valid active g2 | 非恒真だが、D1325 により追加してはいけない拒否 |

## 受理集合の変化

| 入力の型 | 現在 | 実装後 | 方向 |
|---|---|---|---|
| static・current full admission・selection がすべて valid な g1 | 受理 | 受理 | 不変 |
| static-valid、earlier eligible が存在する g1 | oracle/s8c は受理、C06 は C05 まで進む | 各 consumer で拒否 | 狭める |
| selection は valid だが activation HEAD/current admission が不一致の g1 | static consumer は受理し得る | full validation で拒否 | 狭める |
| otherwise-valid active g2 | static consumer は受理し得る。C06 は C05 まで進む | `certificate-generation-scope` で拒否 | 狭める。ただし裁定違反 |
| historical g1で current selection mismatch | `reverify_published_freeze` は受理 | 同じ | 不変 |
| static loader 自体が拒否する壊れた generation | 拒否 | 拒否 | 不変 |
| 残件2・3の入力 | 現行どおり | 実装なし | 不変 |

広げる方向の変化は見つからない。規律2を緩める変更もない。ただし「狭める変更だから許される」とは限らず、g2 と full-current-admission の追加拒否は別途裁定境界に抵触する。

## 既裁定との抵触

- **D1241:** 直接の上限解除は見つからない。戻り値型 `OfficialManifest`、`official_status` table、verified receipt は既存で、新しい certifying 成功状態は足していない。ただし worklog・拒否理由で「current admission を通ったから certified」と一般化してはならない。

- **D1312:** loader `_verify_generation_semantics` と historical reverify は変更されず、選択述語自体も current `_launch_validate` 枝に残るため、この狭い境界は支持する。ただし full current admission を新 consumer 契約にする権限までは同裁定から導けない。

- **D1313:** 抵触する。逐語は「**追加で主張してよいのは、(a)…、(b)…、(c)…、の3点だけである**」(`rulings-verbatim.md:111-114`)。plan の「oracle/s8c/C06 公開境界が current launch admission を通った」は第4の主張である。上限を維持するだけでは足りない。

- **D1325:** 直接抵触する。逐語は「**現時点では『戻さない・g1 のみ』で固定する。g2 が実在してから設計する**」(`rulings-verbatim.md:129-136`)。既存 `launch_validate` の g2 拒否を新しい consumer へ伝播させることも、新しい拒否挙動の定義である。

- **D95:** このレビュー自体は read-only。実装面は段5の Codex author が担当し、親の直接 fix や review 代替を行わなければ抵触しない。

- **順序・前提:** D811/D1161/D1334 の official 実行・人間承認・予算数値保留は未充足であり、candidate 強制点の live 発火を主張できない。D1279/D1336 の予算配置・trial ledger 順序は今回決めていない。D1284 も独立 g2 設計を禁じており、D1325 所見を補強する。

## 残る不確実性

- read-only 静的検査のみ。pytest、acceptance、checker は実走しておらず、緑とは判定しない。
- plan は擬似設計段階なので、最終的な例外翻訳・helper の正確な型と順序は未確定。
- production g2 と active g1 は現存しない。g2 の受理集合差は既存 production-emitter fixture と call graph による静的再構成である。
- worktree・branch 交差は今回の取得時点の状態であり、段5開始前に再取得が必要。
- 完全に計算された動的 import 名は静的に絶対否定できないが、AST、文字列、alias、属性参照の各軸で追加 caller は見つからない。

## 総括

最も重い所見は、`launch_validate` の全面再利用が3群へ新しい g2 拒否を伝播させ、D1325 に抵触すること。  
loader と historical reverify 自体は不変で、D1312 の直接違反や受理集合の拡大、規律2の緩和は見つからない。  
一方、full current admission の追加拒否と「current validation 済み」という主張は、D1313 の許可済み3点を越える。  
親は段4で現 plan をそのまま採らず、g1 限定設計へ修正し、full admission を consumer 契約にするかを裁定へ戻すべきである。  
pytest・acceptanceは未実走であり、本結果を緑として扱ってはならない。