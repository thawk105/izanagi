実装は完了しました。指定2ファイル以外は変更しておらず、docs 編集・stage・commit はしていません。静的検査は通過しましたが、pytest は Pegasus の dispatch infrastructure failure（rc=16）により開始前に停止したため、緑とは報告しません。

## 総括

### 1. 変更ファイルと関数

- [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:344)
  - `_assert_no_nul_in_contract_paths()` を追加。
  - `evidence_contract_sha256()` に、canonicalization 成功後・hash 前の NUL 検査を追加。
- [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:530)
  - 裁定 §2.3 の11テスト定義、計53 parameterized nodeid を追加。
  - 全38 path はテスト側の独立した再帰走査で列挙。
  - legacy bytes/hash、現行 hash、g1 pins、正例 hash は literal 固定。
  - 既存 fixture・既存期待値は変更なし。

契約JSON、既存g1、`s8c_preregistration_evidence.py` は `git diff --exit-code` で無変更を確認済みです。

### 2. 追加した nodeid 全列挙

```text
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/0/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/0/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/0/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/1/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/1/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/2/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/2/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/2/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/3/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/3/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/3/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/4/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/4/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/4/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/5/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/5/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/5/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/6/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/6/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/6/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/7/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/7/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/7/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/8/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/8/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/8/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/9/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/9/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/9/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/10/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/10/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/10/required_evidence/2/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/10/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/11/required_evidence/0/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/11/required_evidence/1/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/11/required_evidence/2/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/11/required_evidence/3/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_every_consumed_path[/conditions/11/consumer_requirement/path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_nul_path_controls[required-cr]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_nul_path_controls[required-lf]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_nul_path_controls[consumer-cr]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_nul_path_controls[consumer-lf]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_path_nul
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_in_malformed_shape_path[conditions-dict]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_in_malformed_shape_path[non-dict-required-evidence-wrapper]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_in_malformed_shape_path[unknown-metadata-path]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_preserves_canonicalization_reason_before_nul
orchestrator/tests/test_s8c_preregistration_core.py::test_current_evidence_contract_hash_is_frozen
orchestrator/tests/test_s8c_preregistration_core.py::test_existing_g1_record_pins_are_unchanged
orchestrator/tests/test_s8c_preregistration_core.py::test_prepare_revision_rejects_nul_path_contract_before_create
orchestrator/tests/test_s8c_preregistration_core.py::test_prepare_revision_rejects_nul_path_contract_with_existing_freeze
orchestrator/tests/test_s8c_preregistration_core.py::test_validate_condition_freeze_at_rejects_legacy_frozen_nul_path_contract
orchestrator/tests/test_s8c_preregistration_core.py::test_activation_report_marks_legacy_nul_bound_freeze_invalid
```

### 3. 実走コマンドと結果

リポジトリ規律により素の `python3 -m pytest` は使わず、同一範囲を runner 経由で試行しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_core.py -q -rf
```

- rc=16、pytest開始前停止。
- passed=0 / failed=0 / 実行テスト=0。
- 原因: `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`。

```text
python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_predicates.py orchestrator/tests/test_s8c_preregistration_invariant.py -q -rf
```

- rc=16、passed=0 / failed=0 / 実行テスト=0。同じ infrastructure failure。

```text
python3 tools/run_tests.py orchestrator/tests/test_plain_runner_coverage.py -q -rf
```

- meta-test。rc=16、passed=0 / failed=0 / 実行テスト=0。同じ infrastructure failure。

追加11関数の nodeid prefix を直接指定した runner 実行と、core の `--collect-only` も試行しましたが、いずれも同じ rc=16 で pytest 起動前に停止しました。

実行できた検査:

```text
python3 -m py_compile orchestrator/campaign/s8c_preregistration.py orchestrator/tests/test_s8c_preregistration_core.py
```

- 成功。2ファイルとも構文エラーなし。

```text
python3 tools/check_codex_agents.py
```

- rc=0、OK。

```text
python3 tools/check_docs.py
```

- rc=0、`check_docs: 違反なし`。親 docs 未 land による期待赤も今回はありませんでした。

```text
git diff --check
```

- rc=0。

独立標準ライブラリ probe:

- legacy literal hash = `5203daa58be7cc33303ded109851d9ab9feabc34177a5aa0afef8488ccb6ba7b`。
- 実契約 path 数 = 38。
- いずれも assertion 成功。

### 4. 未実走・未解決事項

- core 全体、predicates + invariant、meta-test は未実走です。テスト赤ではなく runner infrastructure failure です。
- 親環境で上記3本を再実走する必要があります。
- mutation matrix と受入全走は実装子の権限外であり未実施です。
- commit・provenance 監査は、commit 禁止のため未実施です。
- git 状態は指定2ファイルのみ未 stage の変更です。

### 5. 波及可能性

- 所有外 caller:
  - `validate_condition_freeze_at()`：履歴上の legacy NUL-bound freeze を新 reason で拒否。
  - `prepare_revision()`：g1新設・既存freeze後の双方で作成前に拒否。
  - `s8c_preregistration_evidence.semantic_contract_sha256()`：通常は loader が先に拒否するため reason 順序は不変。
- 下流 consumer:
  - `activation_report_at()`、`effective_at()`、`require_effective_preregistration()`。
  - `trial_registry.py` を含む activation-report consumer。
  - `test_s8c_preregistration_predicates.py`、`test_s8c_preregistration_invariant.py`、`test_trial_registry.py`、`test_p3_autonomous_workload_trial.py`。
- 共有 fixture:
  - `_init_repo`、`_write`、`_commit`、`_record_raw`、`_install_g1` は未変更。
- 診断値:
  - production module bytes の変更により、commit後の `core_module_blob_sha256` と activation report digest は変化しうる。
  - 現行 evidence hash、g1 `protected_sha256`、generation は不変。
- 受理集合:
  - 裁定 §2.2 の exact `path` + `str` + NUL のみ新規拒否。
  - CR/LF、非-path NUL、NULを含まないschema違反は従来どおり受理。
