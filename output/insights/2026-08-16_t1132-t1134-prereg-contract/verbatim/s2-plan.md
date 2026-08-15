# プラン v1

## 0. 読んだファイルと確認した行

必読資料は両方とも全文読了した。

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-t1134-prereg-contract/brief.md:1-125`
- 親実測ログ: `/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-t1134-prereg-contract/artifacts/parent-measurements.md:1-112`
- `docs/phase3-8c-preregistration.md:1-341`、特に `:25-42`, `:44-115`, `:162-254`, `:317-340`
- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:1-489`
- `orchestrator/campaign/s8c_preregistration_evidence.py:21-752`
- `orchestrator/campaign/s8c_preregistration.py:38-115`, `:173-191`, `:866-916`, `:1030-1107`, `:1243-1493`, `:1685-1793`, `:1847-1887`
- 指定された 3 テストファイルは全文
- g1 / g2 は各 `:1` の canonical JSON 全 field と raw SHA-256 を確認
- `docs/decisions.md:4269-4296` の D96
- 閉じた射影の実体確認として、追加で次を読んだ。
  - `orchestrator/campaign/p3_autonomous_workload_trial.py:118-145`, `:389-398`, `:1013-1040`, `:2332-2493`, `:2778`, `:3233`
  - `orchestrator/campaign/s8c_generation_projection.py:37-86`, `:231-241`, `:458-551`, `:734-815`
  - `orchestrator/campaign/trial_registry.py:59-66`, `:133-160`, `:851-865`, `:1311-1349`, `:2401-2496`

worktree は `worktree-dev-wave-t1132-t1134-prereg-contract`、確認時点で未コミット差分なし。pytest は実行しておらず、緑とは記録しない。

## 1. 衝突 (a) の解消 — file:line

`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` では、次の 6 箇所だけを `true` にする。

- C01 `:42`
- C04 `:150`
- C09 `:332`
- C10 `:374`
- C11 `:427`
- C12 `:485`

C02 `:71`、C03 `:114`、C05 `:191`、C06 `:228`、C07 `:264`、C08 `:300` は `false` のままにする。

`orchestrator/campaign/s8c_preregistration_evidence.py` は次の設計にする。

- `:613-621` に、`_MACHINE_EVALUATORS` から導出する
  `MACHINE_CHECKABLE_CONDITION_IDS = frozenset({"C01","C04","C09","C10","C11","C12"})`
  を追加する。
- `SATISFIABLE_CONDITION_IDS` は空集合から `frozenset({"C11"})` へ変更する。機械評価可能集合と充足可能集合を同一視しない。
- `PredicateRegistry.evaluate_all:699-710` の dispatch 自体は正しい。上記 JSON の反転により、6 条件は `_MACHINE_EVALUATORS` へ入り、残り 6 条件だけが `_evaluate_undefined` へ入る。
- `_evaluate_undefined:624-669` の `number in _MACHINE_EVALUATORS` 分岐は削除しない。g3 契約では到達不能になるが、旧契約や明示的に `machine_checkable:false` とした fixture の履歴意味論を維持するために必要である。この到達性を境界テストで固定する。
- 評価器を持たない条件を `true` にした場合は `:703-707` で必ず ERROR にする。現在は内部の `contract-machine-evaluator` が `:711-717` で `commit-blob-read-error` に潰れるため、固定 enum 値 `contract-machine-evaluator` を `ReasonCode:48-85` に追加し、同例外だけをその reason code へ写像する。
- C11 の成功用に固定 enum 値 `generation-policy-satisfied` を追加する。自由文や契約由来の文字列を reason code にしない。

`docs/phase3-8c-preregistration.md:225-237` は、「12 条件すべて評価不能」という現在地を廃止し、次を明記する。

- 6 条件は machine evaluator へ dispatch される。
- C11 だけが本改訂後に SATISFIED へ到達しうる。
- 他の 5 evaluator は検査不合格なら UNSATISFIED、全検査通過後も証明不足なら EVIDENCE_UNDEFINED。
- evaluator のない 6 条件は引き続き EVIDENCE_UNDEFINED。
- したがって衝突 (a) は解消するが、12 条件全体の発効を意味しない。

## 2. 衝突 (b) の解消 — file:line

`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:378-428` を次の形へ改訂する。

- `generation_supervisor.field_paths:383-390` から
  `_run_workload.sample_plan_sha256` と `_run_workload.cap_lift_sha256` を削除する。
- `sample_plan` ブロック `:396-407` と `cap_lift` ブロック `:408-419` を全体削除する。
- 新しい `required_evidence` として次を追加する。
  - `artifact_kind`: `generation_projection`
  - `path`: `orchestrator/campaign/s8c_generation_projection.py`
  - `field_paths`: `_CRITIC_KEYS`、`_SOURCE_METRIC_KEYS`、`_DIAGNOSTIC_METRICS`、`_CRITIC_PROJECTION_KEYS`、`apply_critic_feedback.planner_projection`、`_validate_critic_projection`、`validate_planner_payload.critic_feedback`
  - `reachable_from`: `_run_workload -> apply_critic_feedback -> planner_projection` と `_run_workload -> validate_planner_payload -> _validate_critic_projection -> _assert_expected_tree`
- `consumer_requirement.proof:421-424` は、正確な `G=2`、3 入口での budget validation、critic 自由文を捨てた閉じた射影、次世代 planner payload の exact 検証、独立負例を証拠とする文へ置換する。
- `negative_control_id:426` は `nc_c11_generation_cap_reverts_to_one` のまま維持する。これが第 4 の証拠面であり、境界テストが実在と検出力を固定する。
- `static_only_note:428` は、sample-plan / cap-lift や実走結果を証拠にせず、指定 commit の supervisor blob と generation-projection blobだけを検査する旨へ変更する。
- `machine_checkable:427` は `true`。

「閉じた射影」の実体は `_role_metric_payloads` ではない。次の一体である。

- `s8c_generation_projection.py:74-86`: 入出力の閉じた key 集合と固定 diagnostic 順序
- `:231-241`: exact-key 検査
- `:458-508`: critic 自由文を捨て、supervisor metrics から固定 4 field の `planner_projection` を作る `apply_critic_feedback`
- `:511-551`: source generation、固定長・固定順 diagnostic、有限値を検査する `_validate_critic_projection`
- `:734-815`: generation 1 では feedback 禁止、generation 2 以降では必須、外部期待値との exact tree 一致を要求する `validate_planner_payload`
- `p3_autonomous_workload_trial.py:2422-2442`, `:2480-2493`: 上記射影を次世代 planner payload にだけ入れ、`_invoke` 前に検証する production wiring

`_evaluate_c11:528-575` は次のように強化する。

- `MAX_APPROVED_GENERATIONS` は `>=2` ではなく、文書 `docs/phase3-8c-preregistration.md:78-82` に従って exact `2` を要求する。
- `_validate_generation_budget:389-398` が exact int、範囲、承認上限超過を拒否する構造を検査する。
- `main:3233`、`run_trial:2778`、`_run_workload:2332` の各 call が後続 launch／generation loop より前で支配的に実行されることを AST で検査する。単なる関数名の出現だけでは充足させない。
- `generation_projection` blob を AST parse し、上記の exact key 集合、自由文非伝播、fixed diagnostic、expected-tree 照合を検査する。
- `_run_workload` について、generation 2 以降の `apply_critic_feedback`、`planner_projection` の取得、planner payload への格納、`validate_planner_payload`、`_invoke` の順序を確認する。
- AST から支配関係や唯一の代入経路を証明できない場合は `UNSATISFIED / critic-feedback-consumer-absent` へ倒す。
- sample-plan / cap-lift を読む `:545-570` と、専用の `_artifact_object:517-525` は削除する。
- 全検査通過時だけ `SATISFIED / generation-policy-satisfied` を返す。

`docs/phase3-8c-preregistration.md:187` の条件 11 は、単なる「裁定済み」から、exact `G=2`、3 入口 validator、`apply_critic_feedback` と `validate_planner_payload` による閉じた第二層射影、独立負例が揃うことへ変更する。`:238-241` の衝突 (b) は「g3 で解消済み。ただし成果物 2 件を作ったとは主張しない」と更新する。

## 3. 衝突 (c) の解消 — file:line

P3 の二つの名前は採用するが、両識別子を manifest 自身へ埋め込んではならない。次の二段束縛に修正する。

1. 内容 commit `P` が 6 cell manifest の exact bytes を導入する。manifest は commit ID も自分自身の `manifest_sha256` も持たない。
2. 発効 commit `C` は単一親 `P` の直子であり、`output/s8c-preregistration/prereg-effective-binding.v1.json` だけを導入する。この record は `prereg_content_commit=P`、manifest path、manifest bytes の SHA-256 を持つ。`C` 自身の ID は record に埋め込まない。
3. `prereg_effective_commit=C` は、C の成立後に作られる registry、run-start、terminal report、acceptance receipt へ記録する。
4. P/C 関係は `is-ancestor` ではなく「C の親集合が exact `{P}`」で検査する。測定 HEAD に対する ancestry は C から検査する。

契約 JSON は次のように変える。

- C03 `:75-115`
  - manifest の `field_paths:80-87` から `prereg_commit` を削除する。
  - 上記 binding record を `required_evidence` に追加し、`prereg_content_commit` と外部計算した `manifest_sha256` を置く。
  - registry `field_paths:96-100` を `registry.prereg_content_commit` と `registry.prereg_effective_commit` に分ける。
  - proof は exact manifest set、binding record、append-only registry の三者照合を要求する。
- C08 `:268-301`
  - manifest の `field_paths:273` から自己参照する `prereg_commit` と `manifest_sha256` を削除し、manifest の実 field だけを列挙する。
  - binding recordを追加する。
  - registry `field_paths:282-286` は run-start、terminal report、registry のそれぞれについて `prereg_content_commit` と `prereg_effective_commit` を別 field にする。
  - proof は単一親 exact equality、P の manifest blob と binding digest の一致、exact C の `EffectivePreregistration`、C から measurement HEAD への ancestry を要求する。
- C03 / C08 の `machine_checkable` は `false` のまま。今回、親履歴まで検証する新 evaluator を追加したふりはしない。`_evaluate_undefined:638-644`, `:660-666` も維持する。

文書は次を追随させる。

- `docs/phase3-8c-preregistration.md:27-42` で P=`prereg_content_commit`、C=`prereg_effective_commit` を定義し、成果物が両方を別 field で記録すると書く。
- 条件 3 `:170-171` に、P が manifest bytes を導入し、C の binding と registry が exact set を束縛することを書く。
- 条件 8 `:181` に、P/C/measurement HEAD の三者束縛、C の単一親が exact P であること、C の祖先を P の代用にできないことを書く。
- `:144-146` の manifest 欄解除条件を二段束縛へ合わせる。
- 衝突 (c) `:242-245` は解消形へ置換する。
- 正式起動形 `:322-326` の「すべて同じ commit」を、内容を P、binding と導出発効を C に置く二段構成へ変更する。

この設計なら `prereg_commit` を二義化せず、manifest の commit 自己参照と manifest digest 自己参照の両方を避けられる。

## 4. g3 世代記録 — 全 field と算出経路

`condition-freeze.v1.g3.json` は `s8c_preregistration.py:_record_document:1685-1710` が作る 13 field の canonical JSON とする。

| field | 値・算出方法 |
|---|---|
| `schema_version` | exact `s8c-prereg-condition-freeze/v1`。`:46`, `:1694` |
| `normalization_version` | exact `s8c-prereg-markdown/v2`。`:47`, `:1695` |
| `generation_number` | `3`。`prepare_revision:1751-1753` が検証済み g2 の次を選ぶ |
| `supersedes_sha256` | g2 raw bytes の SHA-256。exact `d3c6a3dea39e8d05560091c1286f9a0b803e42b70512f7bf8cac009ed4244225`。`:1753-1755` |
| `source_path` | exact `docs/phase3-8c-preregistration.md`。`:38`, `:1698` |
| `section5_field_names_sha256` | 欄名を変えないため exact `4d082de6c6a19691dd8bad27127e9ebb03fdacc500aab555310c7883b7ba2635`。`:893-894` |
| `section6_conditions_sha256` | §6 条件 1〜12 の normalized 文書列を `_DOMAIN_CONDITIONS` 付きで hash。`:895-896` |
| `section6_condition_hashes` | 各 `{number,text}` を `_DOMAIN_CONDITION` 付きで個別 hash。`:897-905` |
| `normative_body_sha256` | §1,2,3,4,6,7 の normalized body を `_DOMAIN_NORMATIVE` 付きで hash。`:881-907` |
| `evidence_contract_sha256` | strict JSON を semantic canonical JSON 化し `_DOMAIN_EVIDENCE` 付きで hash。`evidence_contract_sha256:374-382` |
| `protected_sha256` | field-name hash、条件集合 hash、normative hash、evidence hash の canonical object を `_DOMAIN_PROTECTED` 付きで hash。`MarkdownContract.protected_sha256:183-191` |
| `revision_reason` | exact 文案: `2026-08-16 ユーザー裁定 T-1132/T-1133/T-1134: 6 評価器の到達可能化、条件 11 の既存 G=2・3 入口・閉じた射影・負例への証拠改訂、条件 3/8 の内容 commit と発効 commit の二段束縛` |
| `ruling_reference` | `D96`。ただし同じ land 単位に本改訂固有の新 D の spool fragment と境界テストを必須とする |

個別条件 hash は C03、C08、C11 だけを再計算する。他の 9 個は g2 と同値である。

- C01 `81d30fac5b7b961324d5b898bb8f148661f36f8e72b223e6cc7355012033470e`
- C02 `b799c36358e3ba43181a73f5f333ce5ca03ad497fe297bcd92662d1a8597a5b6`
- C04 `4ae2f59ce487ecd61f666bd091e26c7ab4696c295b62b12aa933509bc7532a6d`
- C05 `516785d0b2b076e44af16d56ed27b3740dfb7faeaaee10e8d6cd7d5a20c26e2b`
- C06 `603171dde649b4bace512b518df3c0d360c1ea99379f75b32de156035bf3ca35`
- C07 `5d4857d82d3050f6006914055a8bf37b5bcd6bd45e3f0c40ac1d087f9bbb8fef`
- C09 `e1dd164d59b4316e87003b4b2e18df2091879520e0eb1b7d31deeae89c275b9d`
- C10 `10f7e5f981b07b67e95a0aa35f4aa85f59260f2d556d2939f6765f5df169f783`
- C12 `b46191ef2921fb6381373269983301bf3f2bba878f26cab94041a827b90965d3`

生成 argv は、doc と契約 JSON の最終 bytes を確定した後に次とする。

```text
python3 -m orchestrator.campaign.s8c_preregistration prepare-revision --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract --commit HEAD --ruling-reference D96 --revision-reason '2026-08-16 ユーザー裁定 T-1132/T-1133/T-1134: 6 評価器の到達可能化、条件 11 の既存 G=2・3 入口・閉じた射影・負例への証拠改訂、条件 3/8 の内容 commit と発効 commit の二段束縛'
```

`prepare_revision:1725-1755` が g2 と supersedes を、`:1758-1775` が worktree の新 doc / JSON から全 hash を算出し、`:1776-1793` が g3 を exclusive-create する。hash を手入力しない。

## 5. 境界テスト・既存テストの追随 (網羅列挙)

このプランどおり C11 だけを SATISFIED にすると、既存テストで赤になるのは次の 13 nodeid である。

1. `test_s8c_preregistration_core.py:609`  
   C03/C08 に binding path を各 1 件追加し、C11 で 2 path 削除・1 path 追加するため、path 数は 38 から 39。`:610` を 39 へ更新する。

2. `test_s8c_preregistration_core.py:1123`  
   `test_current_evidence_contract_hash_is_frozen` の literal を、新しい `evidence_contract_sha256` へ更新する。g1 pin `:1129-1137` は歴史値なので変更しない。

3. `test_s8c_preregistration_predicates.py:98`  
   zero satisfied を exact `{"C11"}`／件数 1 へ変更し、テスト名も追随させる。

4. `test_s8c_preregistration_predicates.py:107`  
   gap snapshot `:119-130` を次へ更新する。
   - C01 `UNSATISFIED / workload-projection-mismatch`
   - C04 `UNSATISFIED / crash-policy-cell-partial`
   - C09 `UNSATISFIED / formal-acceptance-layer3-consumer-absent`
   - C10 `UNSATISFIED / cross-binding-verifier-incomplete`
   - C11 `SATISFIED / generation-policy-satisfied`
   - C12 `UNSATISFIED / environment-contract-consumer-absent`
   - C02/C03/C05/C06/C07/C08 は現行 expected のまま。

5. `test_s8c_preregistration_predicates.py:500`  
   `:506` の三者等値を分解する。
   - `machine_checkable == M.MACHINE_CHECKABLE_CONDITION_IDS == {"C01","C04","C09","C10","C11","C12"}`
   - `M.SATISFIABLE_CONDITION_IDS == {"C11"}`
   - satisfiable は machine-checkable の部分集合
   - 6 条件すべてに登録済み negative control があること

6. `test_noop_and_token_only_fixtures_never_satisfy[nc_c01_perf_scale_regression-C01]`  
   baseline は EVIDENCE_UNDEFINED のまま、mutation は `UNSATISFIED / workload-projection-mismatch` へ更新。

7. 同 `[nc_c04_partial_crash_survives-C04]`  
   mutation は `UNSATISFIED / crash-policy-cell-partial`。

8. 同 `[nc_c09_acceptance_skips_layer3-C09]`  
   mutation は `UNSATISFIED / formal-acceptance-layer3-consumer-absent`。

9. 同 `[nc_c10_raw_response_unbound-C10]`  
   mutation は `UNSATISFIED / cross-binding-verifier-incomplete`。

10. 同 `[nc_c11_generation_cap_reverts_to_one-C11]`  
    token-only baseline は projection blob を欠くため `UNSATISFIED / critic-feedback-consumer-absent`、cap=1 mutation は `UNSATISFIED / generation-cap-not-lifted`。`:455-470` の廃止成果物 fixture は削除する。

11. 同 `[nc_c12_resume_or_multi_process_allowed-C12]`  
    mutation は `UNSATISFIED / allocation-enforcement-consumer-absent`。

12. `test_s8c_preregistration_predicates.py:572`  
    prohibition ruling only は `EVIDENCE_UNDEFINED` ではなく `UNSATISFIED / generation-cap-not-lifted` を期待する。

13. `test_s8c_preregistration_invariant.py:191`  
    zero satisfied を exact `{"C11"}`／件数 1 に変更する。`effective is False` は他 11 条件と §5 により維持する。

追加すべき境界テストは次である。

- evaluator のない C02 を一時的に `machine_checkable:true` にし、`ERROR / contract-machine-evaluator` になる負例。
- 6 evaluator を `false` にした旧契約 fixture で `_evaluate_undefined` が引き続き使われる履歴互換テスト。
- current snapshot の C11 が SATISFIED になり、`MAX_APPROVED_GENERATIONS = 1` mutation だけで指定負例が KILL される正負対。
- critic 自由文を projection に混入、exact-key 検査を削除、`expected_critic_feedback` 照合を迂回、validator call を launch 後へ移動、の各 mutation が C11 を充足させない検査。
- C03/C08 の契約 field に裸の `prereg_commit` がなく、manifest 自身に content/effective commit や manifest SHA が入らない境界テスト。
- g3 の `generation_number=3`、`ruling_reference=D96`、g2 raw SHA に対する supersedes を固定する candidate invariant。

## 6. commit 分割

凍結範囲の変更と g3 は同一 commit が必須である。

- doc / evidence contract だけを先に commit すると、`validate_condition_freeze_at:1450-1457` が g2 と新 protected contract の不一致を `record-protected-mismatch` で拒否する。
- 後続 commit で g3 を足しても、validator は全祖先 commitを検査するため、壊れた中間 commit は修復できない。
- g3 だけを先に追加すると、`_assert_history_transition:1283-1285` が protected hash 不変の世代増加を `spurious-revision` として拒否する。

したがって次を 1 commit にまとめる。

- evidence contract JSON
- 8c preregistration doc の全追随
- C11 evaluator と dispatch 定数・reason code
- 3 テストファイル
- `condition-freeze.v1.g3.json`
- D96 が要求する境界テスト

評価器だけを非凍結の先行 commit に分けることは技術上可能だが、C11 の受理集合、契約、境界テストを同一変更単位に置く D96 の目的に反するため採らない。親の P4 はこの条件付きで正しい。

なお、条件 3/8 が将来要求する内容 commit P と発効 commit C は、この wave の実装 commit 分割ではなく、事前登録を実際に発効させる将来の production protocol である。

## 7. (P1)(P2)(P3) への評価と推奨

P1 は、提示 3 案では親案を推奨する。

- P1 `ruling_reference=D96`: 採用。既存 validator の受理集合を変えず、導入 commit 時点に実在する D を参照できる。D96 が要求する本改訂固有の新 D と境界テストは同じ land 単位へ必ず含め、`revision_reason` に直接のユーザー裁定と T 番号を残す。
- P1b spool fragment 受理: 却下。`_RULING_RE:55`、record schema `:1080-1085`、`_assert_rulings_exist:1352-1374` の受理集合を広げ、未 fold fragment を裁定 authority に昇格させる別の統治変更になる。
- P1c D だけ先行 land: 却下。成果を二 wave に割るうえ、D96 の「新 D と境界テストを同じ変更単位」に対して弱い。
- 第 4 案として、land lock 内で D 番号を予約し、g3 を再生成して同一 commit を構成する仕組みは理論上可能。ただし land 手続と再検査を変更する別 wave の対象であり、今回は採らない。

P2 の discharge 判定は次のとおり。

| 条件 | 現行 evaluator は完全 discharge するか | 本プラン |
|---|---|---|
| C01 | しない。`:420-434` は数値 literal と属性名の存在だけで、同じ ratified hash が 3 sink の所定 field に届くことを証明しない | 終端は EVIDENCE_UNDEFINED のまま |
| C04 | しない。`:446-451` は call 名の到達だけで、catch 節、全体判定不能、順序、再起動 preflight を証明しない | 同上 |
| C09 | しない。`:461-470` は call と文字列の存在だけで、publish 前・全 build report・no-build 非認証を証明しない | 同上 |
| C10 | しない。`:500-509` は field 文字列と call の存在だけで、全 bytes の reread と registry append 前の束縛を証明しない | 同上 |
| C11 | 現行はしない。artifact 検査を外すだけでは call 名だけの token fixture が通る | §2 の AST・支配関係・閉じた射影検査を追加した後だけ SATISFIED |
| C12 | しない。`:591-605` は関数・属性名だけで、登録環境・calibration・allocation receipt と launch 前拒否を完全には証明しない | 終端は EVIDENCE_UNDEFINED のまま |

したがって、6 終端を一律 SATISFIED にする P2 は却下し、C11 だけを条件付きで SATISFIED にする。

P3 は名前の分離には賛成だが、「manifest が、それを含む content commit の ID を持つ」形は却下する。修正版は §3 のとおり、P の manifest は自己識別子を持たず、C の binding record が P を指し、C は後続成果物が記録する。

## 8. 親 brief の誤り・見落とし

- M4 が示す `_role_metric_payloads:1013-1040` は初期 role metrics の射影であり、critic の閉じた第二層射影そのものではない。正本は `s8c_generation_projection.py:458-551`, `:734-815`。
- 現行 `_evaluate_c11:532-534` は cap `3` 以上も通すが、doc `:78-80` は exact `G=2` で `G>=3` を禁止している。
- P3 を二つの field 名へ置換するだけでは、manifest 内に content commit ID を置いた場合の自己参照が残る。
- C08 契約 `:273` の `manifest_sha256` も manifest 自身の field と解釈すると自己参照になる。実装 `trial_registry.py:62`, `:134-139` は正しく bytes から外部計算しており、契約側を合わせる必要がある。
- 現行 6 evaluator は、C11 を含め consumer proof を完全 discharge していない。終端だけ SATISFIED に変える P2 は token-only fixture を受理する。
- SATISFIED に対応する成功 reason code が現 enum にない。
- `contract-machine-evaluator` は内部例外名であり、公開結果は現在 `commit-blob-read-error` に潰れる。
- C03 の `static_only_note:115` は trial registry module 自体が不在と書くが、現在は module が存在する。欠けているのは二段 binding capability である。
- C11 の evidence path 入替えと C03/C08 の binding path 追加により、contract path inventory は 39 になるため、`:609-610` も追随対象である。
- 衝突 (d) は一切解消しない。arm 未束縛はそのまま残る。

## 9. 残るリスクと未解決点

- C11 の AST evaluator が支配関係や唯一の dataflow を証明できない場合、SATISFIED にしてはならない。その場合は本改訂中でも EVIDENCE_UNDEFINED に戻し、`SATISFIABLE_CONDITION_IDS` を空へ戻す。
- C03/C08 の二段束縛は構成可能な契約を定義するだけで、`trial_registry.py` の現行単一 `prereg_commit` 実装は変更しない。両条件は未充足のままである。
- g3 の新 hash 値は最終 doc / JSON bytes に依存する。レビュー後の文言変更があれば g3 を作り直し、古い g3 を使わない。
- g3 が D96 を参照するため、本改訂固有の新 D が同じ land 単位に実在することを人間レビューで確認する必要がある。
- `s8c_generation_projection.py` は今後 C11 の live evidence blob になる。将来の変更は C11 判定への影響を伴う。
- pytest、`check_docs`、freeze candidate 検査はこの read-only 段では未実走である。

## 総括

6 evaluator だけを到達可能にし、評価器のない 6 条件は false のまま維持する。  
SATISFIED へ進めるのは、閉じた射影まで静的に discharge した C11 だけである。  
条件 3/8 は manifest 自己参照を避ける P/C 二段束縛へ改め、祖先代用を exact-parent 検査で禁止する。  
g3 は D96 を参照し、protected 変更・境界テストと同じ commit に置く。  
既存で追随が必要なのは 13 nodeid。衝突 (d) と残り 11 条件の未充足は解消しない。