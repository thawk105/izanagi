実装済み・未実走です。変更は許可された 2 ファイルだけです。

## 実装

[tools/codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9238)

- `_load_adjudication`
  - 変更前: `equivalent_to` は manifest 全体の union 検査のみでした。
  - 変更後: union 検査を維持し、join 後に task 別集合で parent、second-reader の raw 行を両方検査します。
  - `_slot_dimension_map` を再利用し、dimension join 失敗時は reason を追加して当該 packet を `joined` から除外します。
  - `oracle_kind` を combined verdict に入れ、`combined_verdict_sha256` の計算対象にしました。
- `_aggregate_verified`
  - 変更前: verdict 側の `oracle_kind` は未検査でした。
  - 変更後: schedule/manifest 由来の値と exact 比較し、wrong と missing の両方を拒否します。分類 authority は引き続き dimensions 側です。
  - 既存の task 別 `equivalent_to` ゲートは保持しています。

受理の含意: 各 reader の finding が packet の task 集合内にあり、combined verdict の `oracle_kind` が schedule と一致する場合だけ新ゲートを通ります。通る正例として、alpha 2 slot は `alpha-finding/positive`、beta 2 slot は `beta-finding/negative` とする 4-slot replay を追加しました。

拒否の含意: manifest union 内でも対象 task 外の finding、wrong/missing `oracle_kind`、または dimension join 不能を reason 付きで fail-closed にします。

`_load_adjudication` の signature、`TASK_MANIFEST`、`_manifest_task_entry` の source は HEAD と一致することを静的確認済みです。

## テスト

追加 nodeid:

- `orchestrator/tests/test_codex_reasoning_ab.py::test_replay_manifest_forwards_external_task_manifest_to_real_adjudication_loader`
  - 外部 manifest CLI、D931 digest 連鎖、4-slot paired schedule、schedule descriptor、実 `_replay_manifest` と実 loader の正例。
- `...::test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union[parent]`
- `...::test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union[second-reader]`
  - blind append は union により成功し、post-reveal raw-row 検査だけが拒否する負例。
- `...::test_load_adjudication_dimension_join_failure_is_reasoned_and_not_joined`
- `...::test_aggregate_verified_rejects_cross_task_equivalent_from_manifest_union`
  - 既存 aggregate task 別ゲートの削除変異を検出。
- `...::test_aggregate_verified_rejects_adjudication_oracle_kind_mismatch[wrong]`
- `...::test_aggregate_verified_rejects_adjudication_oracle_kind_mismatch[missing]`

追随変更した主な node:

- `test_aggregate_verified_uses_oracle_kind_and_keeps_task_model_axes_separate`
- `test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers`
- `test_bound_price_aggregate_rejects_attempt_price_mismatch`
- `test_m08_p02_p04_null_v3_and_legacy_emit_no_cost_keys`
- `test_schedule_descriptor_absence_emits_no_cost_keys`
- `test_f4_aggregate_uses_loaded_descriptor_state_without_manifest_reread`

`_full_manifest`、`_aggregate_rows`、`_verdict_packet_swap_restore_fixture`、`_bound_cost_aggregate` の hash/verdict 期待値も、現行結果の直書きではなく slot/manifest 由来の `oracle_kind` から導出する形へ更新しました。

## 実走状況

pytest は runner 経由で 2 回試行しましたが、どちらも `qstat -Q preflight rc=1`、runner rc=16、`child_started=false` でテスト本体は起動していません。したがって緑とは報告しません。

静的には以下を確認済みです。

- 両ファイルの AST parse
- `git diff --check`
- 変更 path が許可された 2 ファイルだけ
- `_load_adjudication` signature と保護対象 source の不変
- union validator、`_slot_dimension_map`、既存 aggregate equivalent gate の存在
- `oracle_kind` が row hash より前に入ること
- 新規 test 名の存在、一意性、parametrize 軸

意図的に赤のまま残したテストはありません。

## 制約 meta-test

新規 test 追加で影響し得るものとして、次を静的に洗い出しました。

- import 時の `growth_test_holds.enforce_held_functions`
- `test_growth_test_holds_contract.py::test_inventory_count_and_key_digest_are_independently_pinned`
- `test_growth_test_holds_contract.py::test_complete_collection_rejects_valid_shape_function_typo`
- `test_pytest_collection_config.py::test_bare_pytest_collection_is_scoped_by_testpaths`
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
- `test_pytest_collection_config.py::test_sanctioned_runner_ignore_keeps_growth_hold_completeness_guard`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- receipt/oracle memo consumer inventory tests
- pytest の `test_` 命名・parametrize ID・重複 node 収集

新規 node は growth-hold、real-repo fixture、receipt/oracle memo の登録対象ではないと静的判定しました。これら meta-test も未実走です。

## 波及可能性

production の直接 caller は `_replay_manifest` だけで、その下流は `verify_manifest` と `aggregate_manifest` です。repo 内の他ファイルには `_load_adjudication`、`_aggregate_verified`、`combined_verdict_sha256` の追加 caller は見つかりませんでした。

共有 fixture の主な consumer は次です。

- `_full_manifest`: complete replay、manifest exchange、snapshot evidence forwarding、pre/post snapshot replay。
- `_aggregate_rows`: token accounting、post-treatment、pair invalidation、false-finding、decision branches、turn accounting。
- `_verdict_packet_swap_restore_fixture`: snapshot evidence と digest-layer redundancy。
- `_bound_cost_aggregate`: price snapshot、unavailable/not-incurred、replay failure、malformed cost 系。
- 外部の material producer が `judgments[].combined_verdict_sha256` を生成する場合、今後は `oracle_kind` を含める必要があります。

既存の未追跡 `output/insights/2026-08-27_t1434-adjudication-task-oracle/` は触れていません。runner は失敗時に ignored な `output/pegasus-dispatch/.../receipt.json` を自動生成しましたが、編集・削除していません。commit、add、stash 等も行っていません。

## 総括

R1、R5からR13の実装面と回帰テストを、許可された 2 ファイルへ反映しました。受理集合は union 検査との AND で task 別に狭まり、oracle binding と dimension failure は fail-closed です。

状態は実装済み・未実走です。compute 側で追加 node、共有 fixture consumer、制約 meta-test の実走確認が必要です。