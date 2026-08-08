現行の受理・拒否挙動は次の形です。

- certified config は `build_admission` と exact lowercase 64hex の環境契約 hash を要求します。異なる事前束縛値は `None` や大文字も含めて上書きせず拒否します。
- guided/raw lane は明示的な非 certified 経路として、環境契約 key の欠落を引き続き受理します。
- lock に hash がなければ従来の COMMIT を受理し、hash があれば全 COMMIT の欠落・型・形式・不一致・未知契約・`env_tag` 不一致を拒否します。
- tail repair と interrupted recovery は、拒否対象 WAL の bytes・repair receipt を変更する前に検証を終えます。
- qualification event sink の受理集合と payload は変更していません。

実装内容:

- [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/model.py) に共有 wire key を追加。
- [ident.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py) に環境契約 binder、certified identity 必須検査、guided lane の明示的 exemption を実装。lock top-level は exact 5 key のままです。
- [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py) で認可済み contract を identity へ束縛してから ID/layout を作成。
- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py) の `wal.log` COMMIT 2 口だけに hash を追加。既存 AST gate の `len == 2` は維持しています。
- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py) に共有 validator と repair/recovery/replay/consumer 配線を実装し、topology の4呼出し元へ lock を渡しました。
- direct-ID caller 14系統と screening/S1/trigger site projectionを新 identity に追随させました。historical 分類、raw reader、S8b、qualification ledger は変更していません。

変異事前登録8件の対応 nodeid:

1. `test_bind_environment_contract_rejects_conflicting_prebound_hash`
2. `test_pipeline_no_bench_wal_commit_binds_authorized_contract`
3. `test_pipeline_bench_wal_commit_binds_authorized_contract`
4. `test_commit_contract_validator_rejects_missing_field_without_defaulting`
5. `test_commit_contract_requirement_is_derived_from_lock_not_record_presence`
6. `test_commit_contract_rejection_precedes_tail_repair_mutation`
7. `test_commit_contract_validator_rejects_unknown_ever_active_hash`
8. `test_commit_contract_validator_rejects_contract_env_tag_mismatch`

正例は `test_replay_accepts_matching_contract_bound_commit_and_skips_evaluation` と `test_unbound_legacy_and_guided_campaigns_remain_readable` です。前者は evaluate/build の双方を spy しています。

campaign-id literal を更新した nodeid:

- `test_campaign.py::{test_campaign_id_binds_admission_policy,test_screening_search_config_omits_none_and_binds_current_admission_policy,test_screening_none_keeps_representative_legacy_campaign_ids_unchanged}`
- `test_p3_autonomous_workload_trial.py::test_no_build_campaign_identity_binds_shared_policy_context`
- `test_p3_s4_loop_trigger_gating.py::{test_campaign_identity_is_unchanged_for_other_and_split_for_compute,test_fixture_cli_uses_authoritative_layout_and_preserves_legacy_bytes,test_clean_dry_pass_still_admitted_on_pegasus}`
- `test_s8a_trigger_sweep.py::test_default_off_campaign_ids_remain_historical_values`
- `test_autonomous_trial_completeness.py::test_campaign_identity_is_pinned_without_producer_helper_oracle`
- `test_autonomous_trial_completeness.py::test_t428_workload_campaign_epoch_and_old_root_nonwrite` の `ycsb-a`、`ycsb-b`、`ycsb-c` 3 parameter nodeid

`_PRE_T343_*` / `_T343_*` / `_T428_*` は残し、明示した generation-1 contract から導いた `_T530_*` を追加しました。ambient `authorize()` の値から golden は導出していません。

静的検査では、新設14テストがすべて引数なしで、`test_campaign.py::_run` の素 runner 自動収集対象であることを確認しました。専用 nodeid allowlist はなく、collection 全体は `test_pytest_collection_config.py`、COMMIT writer は既存 AST meta-test が制約します。

波及先は direct-ID caller、screening/critic/autonomous completeness の共有 fixture、artifact admission、trial completeness、trigger/S6/S8a consumer です。historical artifact literal は凍結値のため更新していません。

## 総括

- plan v2 1〜7、変異8件、正例2件を実装しました。
- production 19ファイル、test 9ファイルを変更しました。
- docs は変更していません。
- commit は作成していません。
- pytest・build・計測は未実走です。
- production/test module の import 検査と `git diff --check` は成功しました。
- 状態は「実装済み・未実走」であり、緑とは報告しません。
- 主な残存リスクは共有 fixture と全 direct-ID consumer の計算ノード実走時の波及です。