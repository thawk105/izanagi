## 実装した物

- [生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/tools/plotting/plot_b10_waiting_grid_forest.py)：定数・pin、指定7項目の入力検査、3 panel forest 図、保存前レイアウト検査、固定8文を含む caption、provenance、2種類の閉包検査、atomic publish、CLI。
- [単体テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/orchestrator/tests/test_plot_b10_waiting_grid_forest.py)：指定された **49 test 全件**。135 records・36 cells・3 families の実寸 fixture と自走 harness。

provenance は指定の `tracked_inputs` 3行、`external_inputs` 2行、report・analysis・families・cells・summary・crosschecks・measurement_conditions・outputs・artist_series・caption・reproduction を記録します。

実物の job 結果に無い `prereg_commit` / `job_script_sha256` は受領証で照合します。repo closure 用の投入・完了時刻は、pin された受領証の値を定数化し、外部読込時にも一致を要求しています。

## 実走した検査

自走 harness：**48 passed / 1 failed / 0 skipped / 0 errors、rc=1**。全 nodeid と結果は[自走ログ](/tmp/fig13-tests.log)。失敗は下記の未着地 test のみです。

実データ CLI：**rc=0**。成果物：

- [PNG](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/probe-fig13/fig13_b10_waiting_grid_forest.png)
- [PDF](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/probe-fig13/fig13_b10_waiting_grid_forest.pdf)
- [provenance.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/probe-fig13/fig13_b10_waiting_grid_forest.provenance.json)

稿 §2.2 / §2.4 と一致：

| workload | outcome | raw p | Holm p |
|---|---|---|---|
| write-heavy | different | 6702/2^18 = 0.02556610107421875 | 0.02556610107421875 |
| balanced | different | 70/2^18 = 0.00026702880859375 | 0.0005340576171875 |
| read-heavy | different | 2/2^18 = 7.62939453125e-06 | 2.288818359375e-05 |

- 各族18対、和はすべて正。
- summary：inside **32** / overlaps **4** / outside **0** / indeterminate **0** / estimable **36**。
- write-heavy μ5：effect **−0.009738229292106326**。
- caption：固定8文、禁句不在、境界4 cell、負の点推定1件・正の区間下限8件を確認。
- `validate_repo_closure` / `validate_external_sources`：生成済み provenance で両方成功。

SHA-256 は稿・現物と一致：

| 入力 | SHA-256 |
|---|---|
| caption_source | `8dc6d69538c6785c0e3e56073ccc86c97e82699972265d5c521159a6cf72045a` |
| report_receipt | `93a1cd74ce279c6c8c876a7ab60fb772b216f25cf59f4eff70d0b0e2b8b429b4` |
| report_job_result | `d5d4a0ee4c503c1b4b6a811f998949f7a76434a575c4ed8d0bfad849eafd082b` |

追加検査：

- `test_plain_runner_coverage.py`：**3 passed**。
- `test_check_subprocess_bytecode_guard.py::test_real_repo_clean`：`DIRECT_CALL_PASS`。
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`：`DIRECT_CALL_PASS`。
- `test_official_perf_closure.py`：**7 passed**。[ログ](/tmp/fig13-perf.log)
- 新生成器への `_python_has_perf_predicate`：**False**。
- 新2ファイルの `compile()` 構文確認：成功。

シェル追記と検査用 heredoc 各1件が guard に拒否されました。指定ファイルへの `apply_patch` と個別直接呼出しで完了しています。

## 未実走・期待赤

**未着地のため赤：**
`test_plot_b10_waiting_grid_forest.py::test_landed_fig13_repo_closure_and_caption_when_present`

skip / xfail 化していません。全欠落・部分欠落を拒否する2 test は成功しました。

指定に従い `tools/run_tests.py`、`python -m pytest` は未実行。計算ノードでの全変異 matrix・着地後検査は親側に残ります。

## 受理・拒否の含意

受理するのは、この report の固定 bytes、またはテスト専用 hash override の下で同じ schema・格子・族構成と再計算一致を満たす fixture です。

hash drift、品質不成立、格子欠損、差分順序・効果・区間・Holm の不一致、外部 identity 不一致、描画の重なりを拒否します。

正例は実 report `978195.nqsv`：読込・作図・両閉包検査まで成功しました。

## 所有外への波及

所有外の編集は**無し**。最終 `git status` は指定2ファイルと `probe-fig13/` の untracked のみです。禁止された git 操作も実行していません。

既存 caller・共有 fixture・consumer から新モジュールへの参照はありません。列挙型の harness、収集時の命名、bytecode、perf 走査について上記検査を実行しました。新 test は subprocess を起動しません。

## 変異事前登録への対応

以下は対象関数の直接実行による観測です。[変異ログ](/tmp/fig13-mutations.log)
nodeid の共通 prefix は `test_plot_b10_waiting_grid_forest.py::`。

| id | 対応 test | 観測 |
|---|---|---|
| m0 | `test_generator_comment_change_preserves_provenance_closure` | SURVIVED |
| m1 | `test_pinned_hashes_are_used_when_no_override` | KILLED |
| m2 | `test_receipt_sha_not_matching_submission_is_rejected` | KILLED |
| m3 | `test_differences_order_mismatch_is_rejected` | KILLED |
| m4 | `test_cell_interval_mismatch_is_rejected` | KILLED、先行 spec 検査 |
| m5 | `test_equivalence_relation_mismatch_is_rejected` | KILLED |
| m6 | `test_holm_p_mismatch_is_rejected` | KILLED |
| m7 | `test_caption_contains_fixed_literals` | KILLED |
| m8 | `test_bbox_overlap_is_a_failure` / `test_layout_failure_publishes_nothing` | 両方 KILLED |
| m9 | `test_constant_cell_nonzero_is_rejected` | KILLED |
| m10 | `test_official_certification_true_is_rejected` | KILLED |
| m11 | `test_family_count_mismatch_is_rejected` | KILLED |
| m12 | `test_raw_p_not_dyadic_is_rejected` | KILLED |
| m13 | `test_underexposed_registered_cell_is_rejected` | 削除・`>` 化とも KILLED |
| m14 | `test_cli_rejects_prefix_without_fig_number` | KILLED |

m4 は定数変更だと spec 照合が先に拒否します。**定数照合と CI 式を分割**するのが適切です。CI 式だけを `1.96` に変えた追加確認では、`test_fixture_has_production_shape_and_recomputes_statistics` が `cell interval recalculation` で検出しました。

m13 は境界正例と下回る負例を同一 test に持ちます。m0 は上記焦点 test での対照確認であり、全 suite の変異観測ではありません。

## 総括

実装済み：生成器・指定49 test・実データ3成果物・両閉包検査。
検査結果：48 passed、未着地の期待赤1、skip 0。
未実走：計算ノードの全変異 matrix・着地後検査。
親への依頼：scratch 退避、docs と最終図の着地、期待赤解消後の受入・commit。