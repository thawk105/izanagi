## 変更の要約 (file:line)

**指定2ファイルに実装済み・pytest未実走です。commitは作成していません。**

- [condition_meaning_gate.py:351](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-rus-author/orchestrator/campaign/condition_meaning_gate.py:351)：主2＋副2の宣言、総数導出、複数file計装、深いshadow、個別観測、副証拠の保存・再検証を実装。
- [test_condition_meaning_gate.py:1671](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-rus-author/orchestrator/tests/test_condition_meaning_gate.py:1671)：独立fixture・期待表、正負例、schema、CLI、既存pinを追加・追随。

`git diff --check` は問題なし。変更pathは指定2ファイルだけです。

## 現行の受理・拒否挙動 (scope 前)

REQUESTED_US 1/0は、供給成立時も意味が `meaning-witness-undeclared` のままadmitされていました。

今回、この組を4箇所成立時のgreen admit／不成立時のred rejectへ変更しました。非対値、旧BACKOFF_FIXED宣言経路、他macroの受理条件は維持しています。

## 新設・変更 node 一覧

新設9関数：

- `test_requested_us_multifile_supply_meaning_and_admission`
- `test_requested_us_multifile_site_count_mismatch`
- `test_requested_us_multifile_include_counts`
- `test_requested_us_multifile_owner_site_inactive`
- `test_requested_us_multifile_rejects_compensated_missing_sites`
- `test_requested_us_multifile_shadow_instruments_all_files`
- `test_requested_us_multifile_green_schema`
- `test_single_file_green_schema_rejects_companion_sources`
- `test_requested_us_cli_establishes_multifile_meaning`

既存7関数を変更：registry／patch束縛、全registry正例、field/key pin、非対値factory、旧CLI拒否、domain集合、docstring pin。

## 直接呼出し検査と反実仮想

test moduleをimportし、`tempfile.mkdtemp()`のpathで直接呼出ししました。以下のparameter集合内は各ケースPASSです。**pytest実走結果ではありません。**

```text
DIRECT_CALL: test_requested_us_multifile_supply_meaning_and_admission PASS
DIRECT_CALL: test_requested_us_multifile_site_count_mismatch[owner,header-verbatim] PASS
DIRECT_CALL: test_requested_us_multifile_include_counts[missing,twice,pragma-once] PASS
DIRECT_CALL: test_requested_us_multifile_owner_site_inactive PASS
DIRECT_CALL: test_requested_us_multifile_rejects_compensated_missing_sites PASS
DIRECT_CALL: test_requested_us_multifile_shadow_instruments_all_files PASS
DIRECT_CALL: test_requested_us_multifile_green_schema[全31変異] PASS
DIRECT_CALL: test_single_file_green_schema_rejects_companion_sources[両key] PASS
DIRECT_CALL: test_requested_us_cli_establishes_multifile_meaning PASS
DIRECT_CALL: test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches PASS
DIRECT_CALL: test_compile_time_branch_selection_accepts_each_registry_macro[全22macro] PASS
DIRECT_CALL: test_compile_time_branch_field_and_existing_evidence_keys_are_unchanged PASS
DIRECT_CALL: test_compile_time_factory_rejects_nonpaired_values[REQUESTED_US:1/None,1/1,0/0,0/1] PASS
DIRECT_CALL: test_legacy_meaning_declaration_and_cli_stay_backoff_fixed_only[PERMUTATION,REQUESTED_US] PASS
DIRECT_CALL: test_v1_domain_and_claim_boundaries_are_exact PASS
DIRECT_CALL: test_module_claim_names_the_exact_38_define_supply_domain PASS
```

schemaの全31値は[所有test:1786](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-rus-author/orchestrator/tests/test_condition_meaning_gate.py:1786)に列挙しています。直接呼出しの対象は計75ケースです。

検査をメモリ上で一時変更し、対応する拒否nodeの赤化も確認しました。変更は復元済みです。

```text
COUNTERFACTUAL: 箇所ごとの等値検査を除去 DID NOT RAISE
COUNTERFACTUAL: 副sourceのdigest束縛を除去 DID NOT RAISE
COUNTERFACTUAL: 副schemaの適用をrecordのkey依存へ変更 DID NOT RAISE
```

## 波及の静的列挙

- MOCC 3件：`test_mocc_mutation_proof.py:177`、`test_mocc_template_proof.py:267`、`test_mocc_proof_surface.py:569`。既存2-tuple契約を維持。
- S1 helper：`test_s1_direct_comparison.py:719`。主fileのNを維持。複数file対応済みとは主張しません。
- 共有fixture installer・fixture dir・driver：編集なし。REQUESTED_USのcache既定0とTU mappingは所有test内だけに追加。
- spawn目録：`subprocess.run`は既存 `_run_process` 内の1箇所。
- B-4目録：production import・module追加なし、49件pinの追随不要。
- AST比較で既存21 entryの値・順序、dataclass、`DEFINE_SPECS`、factory、CLIの不変を確認。

## 未了・限界

pytest、consumer実走、実patch TUのlogin／計算ノード観測、SORT・RUNG1・NOINLINEの変更前後比較、正式変異matrix、親docs・完了checkerは未了です。既存21macro全体のrecord bytes同一を実証したとは主張しません。

直接呼出しで予期しない失敗はありません。副証拠の主張範囲は、指定owner TUと当該configureのinclude文脈までです。

## 総括

**実装済み・未実走として引き継ぎます。** 合成fixtureでは4箇所観測とCLI admissionを確認し、相殺拒否・副証拠検証の反実仮想も成立しました。