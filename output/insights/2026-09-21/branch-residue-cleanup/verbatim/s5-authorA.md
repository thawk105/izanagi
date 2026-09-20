## 変更前の挙動 / 変更後の挙動

- **変更前**: 統合済み子 branch も保持。未統合は rc=20。`-D` は全面拒否。
- **変更後の実装**: 履歴 bundle の作成・verify 後、木と admin を撤去し、子専用 `-D` で branch を削除。共通 runner は `-D` を拒否し、wave 本体は `-d` のまま。**実走未確認・仕様衝突が1件残っています。**

## file:line の変更一覧

- [tools/dev_wave_cleanup.py:231](/work/1/SFC/tanab/izanagi/.codex/worktrees/branch-residue-author-a/tools/dev_wave_cleanup.py:231): 固定 argv の検査、bundle の evidence 配下制限、共通 runner の `-D` 拒否。
- 同 `:1756`、`:1847`、`:1898`: receipt の再出現 ref・digest 検査、bundle 退避、削除直前 tip 照合、専用削除と削除後不在確認、新 receipt fields。
- [orchestrator/tests/test_dev_wave_cleanup.py:172](/work/1/SFC/tanab/izanagi/.codex/worktrees/branch-residue-author-a/orchestrator/tests/test_dev_wave_cleanup.py:172): 中間 commit の復元、branch 削除、失敗・順序・再実行の検査を追加。

統合・履歴の述語と wave `_delete_branch` は AST 比較で変更なし。変更は所有2ファイルのみ。commit・push はしていません。

## テスト実走結果

**実走0件、緑の nodeid なし。** `tools/run_tests.py` 経由の本ファイル走行、meta-test 2件、収集のみの試行はいずれも `qstat -Q preflight rc=1` により runner rc=16。pytest は起動していません。

新設・改名した次の node はすべて**実装済み・未実走**です。接頭辞は `orchestrator/tests/test_dev_wave_cleanup.py::`。

```text
test_remove_child_archives_dirty_integrated_author_and_deletes_branch
test_common_git_runner_rejects_force_delete
test_wave_cleanup_uses_only_lowercase_d
test_remove_child_ancestry_child_skips_bundle_and_deletes_branch
test_remove_child_bundle_verify_failure_is_partial[create]
test_remove_child_bundle_verify_failure_is_partial[verify]
test_remove_child_branch_delete_failure_is_partial
test_remove_child_receipt_rejects_recreated_branch
test_remove_child_deletes_branch_after_admin_removal
test_bundle_argv_requires_exact_evidence_path[create]
test_bundle_argv_requires_exact_evidence_path[verify]
```

既存 `test_remove_child_rejects_unintegrated_author_commit` も未実走です。構文解析と `git diff --check` は成功しました。`test_check_docs.py` は指示どおり未実行です。

## 波及の静的列挙

- `test_pytest_collection_config.py` に対象ファイルを固定する meta-test を発見。`test_permanent_exclusion_table_is_exact_and_target_remains_a_file` と `test_cleanup_collection_positive_control_with_empty_production_exclusions` を実行試行しましたが、上記理由で未実走。
- `orchestrator/test_selection_contract.py` はファイルパスを参照。今回の改名対象 node の外部参照は見つかりませんでした。
- `tools/dev_wave_land.py` に cleanup の直接呼出しは見つかりませんでした。
- `tools/check_branch_rescue.py` の `COVERAGE_BOUNDARY` は DW-O28 自動撤去を対象外とするまま。`test_branch_rescue_ledger.py:340` の対応契約も変更していません。
- `_make_child_repo` は変更せず、中間 commit は改名した正例内で追加しました。

## 未解決の仕様衝突

`test_remove_child_reflog_retained_by_other_branch` は、**HEAD は main 上、過去 reflog は別 branch が保持**する正例です。全 reflog の ancestry は成立しないため指定条件では bundle 必須ですが、`HEAD ^main` は空なので作成に失敗し、rc=30 になると静的に判断しています。

成功期待値は緩和していません。HEAD が main の祖先の場合も bundle 省略を許すか、親の判断が必要です。これは実走で観測した赤ではありません。

## 総括

bundle 退避・子専用 `-D`・receipt 検査と対応テストを実装しました。  
全テストは起動前の基盤障害で未実走です。  
最大の risk は既存 reflog 保持正例と空 bundle 条件の衝突です。  
未完了として親へ返します。