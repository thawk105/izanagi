## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| A-S1 | closed | supply赤／meaning赤で実 family admission による拒否、evidence保存、campaign未到達を検査。候補値20も確認。 |
| B-S1 | closed | `--no-build --value 20` の実 main から cfg を捕捉し、変更していない固定 preimage と一致。 |
| B-S2 | closed | stock／候補の layout 入力IDを記録し、それぞれの campaign ID と両経路間の一致を検査。 |
| B-N1 | closed | 共通の実行 helper を抽出し、転送検査と lock 復元比較を別 node に分離。 |
| red 1 | closed | AST実測は layout **11**、run_campaign **2**。runtime pin は1を維持。 |
| red 2 | partial | 49への更新は成功。ただし実測した追加 module は指定と異なるため、由来コメントを実測に合わせた。 |

## 変更の要約

指定の3 test file のみ変更しました。production・docs・固定 preimage 定数は変更していません。`git add`／`git commit` は実行せず、差分を作業木に残しています。

## 実走結果

指定の `PYTHONPATH=. python3 -c "...pytest.main(...)"` 形式で実行しました。

| 対象 | 結果 | rc |
|---|---|---:|
| `orchestrator/tests/test_p3_s4_loop.py` 全件・修正後 | **553 passed** | 0 |
| `test_p3_exploration_namespace.py`＋`test_p3_b4_wiring_probe.py` 全件 | **99 passed, 1 failed** | 1 |
| `test_plain_runner_coverage.py` 全件 | **3 passed** | 0 |

変更対象の成功 nodeid（先頭は `orchestrator/tests/test_p3_s4_loop.py::`）：

- `test_stock_condition_gate_red_rejects_before_campaign[supply-effectuation]`
- `test_stock_condition_gate_red_rejects_before_campaign[runtime-meaning]`
- `test_default_cli_preserves_preimage_bytes`
- `test_stock_and_candidate_share_manifest_campaign_identity`
- `test_verify_opt_in_reaches_real_loop_evaluate_options[False/True]`：2件
- `test_campaign_lock_preimage_reconstructs_performance_correctness[False/True]`：2件

inventory 更新対象の2 node も成功しました。

- `test_p3_exploration_namespace.py::test_driver_ast_supplements_runtime_namespace_gate[p3_s4_loop]`
- `test_p3_b4_wiring_probe.py::test_source_segment_helper_matches_stdlib_for_all_static_ifs`

初回S4全走は551 passed／2 failedでした。追加fixtureの evidence ディレクトリ未作成を修正し、対象2件成功後、全件を再実行しています。構文検査と `git diff --check` も成功しました。

## 波及

sort／trigger driver は各自の condition gate を持ちます。S4 main を参照する `p3_b4_launcher`、TJ helper／consumer への変更はありません。

README は親担当のままです。既存説明の置換対象は、stock env、manifest転送、候補優先rc、fresh layout、別worktree、digest更新です。

## 未了・懸念

残存失敗は `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` です。この既存テストは未commit変更を wiring probe の2ファイルに限定するため、今回許可された他の2 test file の差分を拒否します。期待値の緩和はしていません。

`_load_static_modules()` を旧base `371674ea6` の全module sourceと比較した結果は **47→49**、追加は **`orchestrator.campaign.p2_2` と `orchestrator.campaign.genome`**、削除なしでした。`source_digest` は旧47件に含まれています。このため、指定コメントの `source_digest` を `genome` に訂正しています。

## 総括

修正は実装・実走済みです。S4全553件は成功しました。inventory側には作業木状態を制限する既存テストの失敗1件と、指定されたmodule差分との事実上の相違が残ります。