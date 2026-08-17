## 総括

競合 11 hunk を意味合成し、指定 3 ファイルの競合マーカーをすべて除去しました。C12 は env/guard を先に cross-module 判定し、その後 `read_binding` / `check_reservation` を cross-module 判定します。

実装済み・未実走です。git add、commit、merge などの git 状態変更、pytest 実走、所有外ファイル編集は行っていません。3 ファイルが `UU` のままなのは stage を親へ残したためです。

### 11 hunk の解決

1. evidence hunk 1: HEAD の `_ReachabilityExplorer` graph と env/guard 第1 gateを採り、main の allocation helperを後段へ合成。
2. evidence hunk 2: HEAD の旧 `single_process_required`・属性検査を除去し、main の `read_binding` / `check_reservation` 述語を `_declared_call` による cross-module 判定へ変更。
3. core hunk 1: generation mutation値は HEAD の `_different_decider_version()`。
4. core hunk 2: mismatch fixture生成も HEAD の動的 helper。
5. core hunk 3: mismatch report assertionは生成した動的値。
6. core hunk 4: invalid runtime時の report identityは main の literal `"s8c-decider/v2"`。
7. core hunk 5: hostile `str` subclass時も main の literal。
8. core hunk 6: report digest mutation値は HEAD の動的 helper。
9. predicates hunk 1: `io` と `ast` の両 importを保持。
10. predicates hunk 2: `TOKEN_ONLY_C12` は main の予約 binding呼び出しへ、HEAD の cross-module import・alias構造を合成。
11. predicates hunk 3: C12 negative controlは main の予約検査 bypassを採り、qualified callへ適合。

主要箇所は [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1530)、[core test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:317)、[predicates test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:491) です。

### 宙に浮いた負例

削除はせず、すべて main の述語へ作り直しました。

- `nc_c12_resume_or_multi_process_allowed`
  - `nc_c12_reservation_check_bypassed` へ置換。
  - `check_reservation` callだけを `is_reservation_required` に変え、baseline terminal undefinedと単一理由性を維持。
- `test_c12_allocation_target_requires_exact_imported_definition`
  - `missing-definition`: `check_reservation` 定義だけを欠落。
  - `unimported-same-name`: 定義を未 import decoyへ移動。
- `test_c12_allocation_absence_shapes_are_independent_from_definition`
  - `call-edge` → `read-binding-call-edge`
  - `single-process-attribute` → `check-reservation-call-edge`
  - `allow-resume-attribute` → `unbound-check-reservation`
  - いずれも baselineから1要素だけを壊す形。
- `test_cross_module_import_forms_resolve_exact_bound_target` と `VALUE_FLOW_C12` を、両 allocation callを持つ positive baselineへ更新。
- `TOKEN_ONLY_C12` 変更で `module-rebind` paramの `class Policy:` 置換が no-opになったため、一意な `environ = {}` anchorへ修正。

`.replace()` は静的に評価可能な48式すべてで実置換を確認しました。既存の mutation差分 assertと代入数 assertも保持しています。

### 実 tree の終状態

静的 graph probeの結果:

- `env_contract.lookup`: 到達
- `execution_guard.attest_and_build_receipt`: 到達
- `reservation.read_binding`: 不到達
- `reservation.check_reservation`: 不到達
- allocation module内の両関数定義: 存在
- C12: `UNSATISFIED / allocation-enforcement-consumer-absent`

production call点も次の4 callだけでした。

- `s8b_oracle_driver.py:920-921`
- `s8b_floor_campaign.py:5644-5645`

C01/C04/C09/C10/C11 の評価器本文は変更していないため、status/reason変更はありません。C12もmain取り込み前後で終端値は同じですが、env/guard gateが実 treeで実際に通過し、allocationで停止するようになりました。

### 受理・拒否挙動

- 変更前HEAD: `single_process_required` callと `single_process` / `allow_resume` 属性を要求。
- 変更後: `allocation_consumer` に `read_binding` / `check_reservation` の定義があり、両 targetへcross-module到達することを要求。
- mainとの差: 両 gate失敗時は、mainのallocation優先からR3のenv/guard優先へ変更。
- 実 treeの受理・拒否結果は不変。変更される可能性があるのは両 gateが同時に失敗する合成treeのreasonだけです。

mainから入ったallocation優先テストはR3と直接矛盾したため、incoming merge内容としてenv優先テストへ改めました。期待値緩和ではなく、裁定されたgate順を固定する変更です。

### 所有外への波及

- `test_s8c_preregistration_invariant.py`: candidate evaluatorとg5/v2束縛を実評価するため直接影響。ただし `effective=False`、SATISFIED 0件は維持見込み。
- `test_reflux_originless_compatibility.py`: evidence ref増加により ActivationReport digest goldenが変わる可能性が高く、親の実走値による確認・別author対応が必要。
- `test_reflux_origin_binding.py`: predicates空の合成ActivationReportを使うため直接影響なし。
- `test_p3_autonomous_workload_trial.py`: 同様に合成済みeffective capabilityを注入し、評価器を走らせないため直接影響なし。
- `s8c_preregistration.py`: evaluatorの動的loader/ActivationReport digest consumer。ファイル自体は未変更。
- predicates内の共有fixture consumers: import-form、value-flow、dict-carrier、entrypoint、shadow、test-only、unimported-decoy各テストへ波及するため、全baselineを新allocation述語へ揃えました。

静的検査はAST parse 3/3、import整合、競合マーカーなし、`git diff --check`、結合文字なし、fixture変異検査に成功しています。pytestは指示どおり実行していません。