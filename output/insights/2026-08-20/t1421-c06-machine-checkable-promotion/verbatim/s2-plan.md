## 総括

C06 の昇格は、契約反転・registry 登録・v6 bump・g10 発行を同一 commit に含める。
generation record は契約 JSON 内ではなく、`output/.../condition-freeze.v1.g10.json` の別ファイルである。
C06 の既存負対照は、staged 専用表から machine negative-control 表へ移す必要がある。
`_evaluate_c06` 本体には reachability の弱点があるため、今回の修正対象外として段4で裁定する。

### 変更点一覧

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json: condition_number == 6`

  `machine_checkable: false` → `true`。field path、consumer entrypoint、`nc_c06_one_arm_reservation_removed` は変更しない。

- `orchestrator/campaign/s8c_preregistration_evidence.py:3056 の _MACHINE_EVALUATORS`

  現状は `{1,2,4,5,7,9,10,11,12}`。`5` と `7` の間に `6: _evaluate_c06` を追加する。

  ただし現状の map は `_evaluate_c06:3477` より前に評価されるため、単純挿入では import 時に `NameError` になる。map と `MACHINE_CHECKABLE_CONDITION_IDS` を `_evaluate_c06` 定義後へ移動して登録する。

- `orchestrator/campaign/s8c_preregistration_evidence.py:3537`

  `_STAGED_EVALUATORS = _MappingProxyType({6: _evaluate_c06})` → 空の mapping proxy。`_evaluate_c06` の判定本体、`SATISFIABLE_CONDITION_IDS` は変更しない。

- `orchestrator/campaign/s8c_preregistration.py:51`

  `DECIDER_VERSION = "s8c-decider/v5"` → `"s8c-decider/v6"`。

- `orchestrator/tests/test_s8c_preregistration_core.py:801-818,1195-1198,2403-2477`

  C06 反転後の契約 hash を pin する。

  - current contract: `dafd8d61807360c333288a00730e7c9ae13a086b61c770e7faf47fb5dd1f701a`
  - NUL: `be5cfef1199864717098bd90fa8ad98ca65ebb83cd9f66d10045c3e1d0e8e410`
  - CR: `42a3ca1d8b072fcd84aba3ef51ed1ed1981c12246e477103a84fded4e35f70ee`
  - LF: `063ed271b875777d86811b221189360bfc66baf5753b961a64e348f8e025c126`

  v5 固定の test 名と期待値3箇所を v6 へ更新する。

- `orchestrator/tests/test_s8c_preregistration_invariant.py:45-143`

  exact set に次を追加する。

  ```text
  checks:
  (C06, orchestrator/campaign/s8b_ratified_freeze.py, load_ratified_freeze)
  (C06, orchestrator/campaign/s8c_budget.py, reserve_all_cells)
  (C06, orchestrator/campaign/s8c_budget.py, settle)
  (C06, orchestrator/campaign/s8c_budget.py, symmetric_indeterminate)

  exclusions:
  (C06, orchestrator/campaign/s8b_ratified_freeze.py, reserve_all_cells, different-module-token)
  (C06, orchestrator/campaign/s8b_ratified_freeze.py, run_trial, different-module-token)
  (C06, orchestrator/campaign/s8c_budget.py, bench launch, non-identifier-token)
  (C06, orchestrator/campaign/s8c_budget.py, bench terminal, non-identifier-token)
  (C06, orchestrator/campaign/s8c_budget.py, run_trial, different-module-token)
  ```

  C03/C08 の集合は変更しない。

- `orchestrator/tests/test_s8c_preregistration_predicates.py`

  - `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`: C06 の reason を `budget-consumer-contract-undefined` → `completion-proof-not-machine-checkable`。
  - `NEGATIVE_CONTROL_CASES:1191`: `nc_c06_one_arm_reservation_removed` を追加。
  - `test_satisfiable_predicate_requires_negative_control:2676`: machine 集合へ `C06` を追加し、件数を `9` → `10`。
  - `test_noop_and_token_only_fixtures_never_satisfy:2727`: C06 の期待 reason `budget-consumer-contract-undefined` を追加。
  - 既存の C06 staged fixture/test (`:3611-3713`) は production registry を使う形へ変更し、`_STAGED_EVALUATORS[6]` 参照を除去する。
  - `test_current_contract_keeps_c06_staged_only:3670` は指定どおり期待値だけを反転する。

  ```python
  machine_checkable is True
  6 in M._MACHINE_EVALUATORS
  set(M._STAGED_EVALUATORS) == set()
  len(M.MACHINE_CHECKABLE_CONDITION_IDS) == 10
  ```

### 新世代 condition-freeze record

`git show 73b66eca` と `git show 9f89da3d` の追加差分は、いずれも次の別ファイルだった。

```text
output/s8c-preregistration/condition-freeze/condition-freeze.v1.g8.json
output/s8c-preregistration/condition-freeze/condition-freeze.v1.g9.json
```

したがって今回の発行先は次で確定する。

```text
output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json:1
```

`generation_path:1165-1170`、`prepare_revision:2035-2115`、CLI `prepare-revision:2176-2206` に従い、コード・契約を未 commit の状態で次を実行する。

```text
python3 -m orchestrator.campaign.s8c_preregistration prepare-revision \
  --repo-root . --commit HEAD --ruling-reference D529 \
  --revision-reason 'T-1421/T-1384: 8c 条件 6 (budget consumer) の machine-checkable 昇格と decider v6 への改訂'
```

期待する検算値は以下。

```text
generation_number: 10
decider_version: s8c-decider/v6
evidence_contract_sha256: dafd8d61807360c333288a00730e7c9ae13a086b61c770e7faf47fb5dd1f701a
protected_sha256: 46811db02eff5d452aee0026f2d7eb04b8d28c7142291ad14646a950db5595b0
supersedes_sha256: ef24bdd64fd9fb50ac3652f3c766a2aa99e81f3b18bebd546dd33029f5ac90dd
ruling_reference: D529
```

`supersedes_sha256` は g9 record 自身の `supersedes_sha256` ではなく、現行 g9 raw bytes の SHA-256 である。normative body と section 6 hashes は不変。

### 負の対照の評価

`_negative_control_c06:3632-3649` は `_EXPECTED_CELL_ROWS` の

```text
("H2", "swapped")
```

を1行削除する。`_c06_field_path_verdict:3370-3466` は

```python
if _c06_expected_rows(tree) != _C06_EXPECTED_CELL_ROWS:
    return False
```

でこの差分を検出し、`_c06_unsatisfied` により `UNSATISFIED / budget-consumer-contract-undefined` になる。既存 staged test も baseline `EVIDENCE_UNDEFINED`、mutation `UNSATISFIED` を確認する構造であり、machine registry 移行後も維持する。

一方、reachability 検査には次の抜けがある。

- `supervisor is None` の場合に reachability 検査をスキップする。
- `reachable_calls` の集合だけを見ており、予約が bench launch より前か、settlement が停止処理へ流れるかを見ない。
- `load_ratified_freeze().sha256` と `reserve_all_cells` のデータフロー結合を検査しない。
- `_ledger_lock`、`_check_limit_state` は存在だけを検査する。

これは named negative control は検出するが、実 runtime の一腕削除全般を証明するものではない。`SATISFIABLE_CONDITION_IDS` が空で、評価器も `SATISFIED` を返さないため、今回の昇格で受理ゲートは緩まない。評価器本体の強化は本 wave の scope 外として、段4で後続 wave へ送る。

### 記録成果物と除外

次を C06 版として同一 commit に含める。

```text
docs/spool/decisions/2026-08-20-dev-wave-t1421-c06-machine-checkable-promotion-2.md
docs/spool/failures/2026-08-20-dev-wave-t1421-c06-machine-checkable-promotion-3.md
docs/spool/worklog/2026-08-20-dev-wave-t1421-c06-machine-checkable-promotion-1.md
output/insights/2026-08-20_t1421-c06-machine-checkable-promotion/
```

insight package は過去 commit と同じく `README.md`、`mutation/mutation-spec.json`、`mutation/mutation-out.json`、`verbatim/s1-brief.md` から `s6-reviewB-output.md` までを含める。

C03/C08 の evaluator、contract flag、negative-control 集合、staged registry は変更しない。pytest 実測は read-only 段2では行わず、親が実施する。