## 実装した物

- `tools/plotting/plot_b7_fixed5_regression.py`：指定 pin・schema・raw／床値／correctness 検査、記録判定との整合検査、上段3＋下段1 panel、9固定文 caption、layout 検査、CLI、原子的 publish を実装。provenance に `tracked_inputs`、`external_inputs`、`cells`、`effects`、`effect_crosschecks`、`floors`、`judgments`、`artist_series`、`caption`、`reproduction` を記録します。
- `orchestrator/tests/test_plot_b7_fixed5_regression.py`：実寸 fixture、本物の描画・closure・CLI、拒否条件、稿照合、着地検査、自走 harness の40テストを実装しました。

## 実走した検査

| 対象 | passed | failed | skipped |
|---|---:|---:|---:|
| 新規 test 全40 nodeid・自走 harness | 39 | 1（未着地） | 0 |
| 同40 nodeid・`pytest.main` | 39 | 1（未着地） | 0 |
| `test_plain_runner_coverage.py` 全3 nodeid | 3 | 0 | 0 |
| `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` | 1 | 0 | 0 |

全40 nodeid と個別結果は [self-run.log](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/probe-t2610/self-run.log)、pytest 結果は [pytest.log](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/probe-t2610/pytest.log) に保存しました。`py_compile` は2ファイルとも rc=0 です。

実データ生成は **rc=0**。成果物：

- [PNG](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/probe-t2610/fig10_b7_fixed5_three_workload_regression.png)
- [PDF](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/probe-t2610/fig10_b7_fixed5_three_workload_regression.pdf)
- [provenance.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/probe-t2610/fig10_b7_fixed5_three_workload_regression.provenance.json)

稿から値を抽出し、生成後 provenance と Python で照合しました。以下はすべて一致です。

| workload | stock median | fixed5 median | effect | floor CV | judgment |
|---|---:|---:|---:|---:|---|
| rr5 | 2354846 | 3953710 | 0.6789675418265144 | 0.009536033056996148 | no-regression |
| rr50 | 3832768 | 4318443 | 0.12671651401806727 | 0.00725042525457718 | no-regression |
| rr95 | 10334945 | 9158963 | -0.11378696258180376 | 0.0022283754708938273 | regression |

標本も30/30一致。repo closure・external sources 検査も PASS。[照合結果](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/probe-t2610/document-crosscheck.json)

## 未実走・期待赤

期待赤は次の1件だけです。**未着地のため赤**であり、skip／xfail 化していません。

`orchestrator/tests/test_plot_b7_fixed5_regression.py::test_landed_fig10_repo_closure_and_caption_when_present`

変異 matrix の dispatch 実走、親担当の最終着地・受入・commit は未実施です。指定の構文確認と `pytest.main` は拒否されず実走できました。

## 受理・拒否の含意

受理する入力は、指定 SHA-256 に束縛され、6 cell×5標本・測定条件・正しさ記録・median・effect・記録判定が整合する証拠です。

欠落、hash 不一致、標本不備、trace-enabled 性能値、未 certified、床値や記録判定との不整合は拒否します。

通る正例は、指定 durable root の実データによる今回の3成果物生成です。

## 所有外への波及

既存 caller・共有 fixture・consumer の変更は無し。参照検索では新規2ファイル以外に生成器の利用箇所はありません。

列挙型 meta-test は自走 harness 検査と verifier/oracle 名の除外集合検査を確認・実走済みです。着地検査は親担当の図3ファイルと figures README に依存します。

tracked 差分は空で、新規2ファイルと `probe-t2610/` のみ untracked。docs・入力・既存コードの編集、git add／commit 等は禁止操作を行っていません。

## 変異事前登録への対応

以下の nodeid 接頭辞はすべて `orchestrator/tests/test_plot_b7_fixed5_regression.py::` です。対応テストは実走済みですが、変異自体の KILLED／SURVIVED は未実測です。

| id | 対応 test |
|---|---|
| m0-equivalent-docstring | `test_generator_comment_change_preserves_provenance_closure`（正例。事前登録の expected_nodes は空） |
| m1-drop-cert-hash-check | `test_certification_hash_drift_is_rejected`、`test_manifest_hash_drift_is_rejected`、`test_floor_hash_drift_is_rejected` |
| m2-drop-raw-manifest-check | `test_raw_sha_mismatch_is_rejected` |
| m3-drop-median-crosscheck | `test_median_mismatch_is_rejected` |
| m4-drop-effect-crosscheck | `test_effect_mismatch_is_rejected` |
| m5-drop-judgment-check | `test_judgment_mismatch_is_rejected` |
| m6-drop-certified-check | `test_uncertified_cell_is_rejected` |
| m7-drop-trace-disabled-check | `test_trace_enabled_samples_are_rejected` |
| m8-drop-adopted-token-check | `test_adopted_stock_token_is_rejected` |
| m9-bypass-layout-overlap | `test_bbox_overlap_is_a_failure` |
| m10-landed-skip-on-missing | `test_landed_fig10_rejects_all_missing_outputs` |
| m11-drop-caption-literal | `test_caption_contains_fixed_literals` |
| m12-drop-floor-genome-check | `test_floor_genome_mismatch_is_rejected` |

単一理由性への対処として、m3 は両 arm の標本を同率で変更して effect 比を維持し、m8 は全 adopted token と対応 raw を揃えて変更しています。意味検査の負例では manifest・fixture hash を再封印し、先行する hash 拒否との混同を避けています。最終確認は親の変異 probe が必要です。

## 総括

実装済み：生成器・40テスト・実データ3成果物・稿との全値照合。
検査結果：自走／pytest とも39 passed、1期待赤、0 skipped。
期待赤：fig10 未着地の integration test のみ。
未実走：変異 matrix・最終受入・commit。
親への依頼：scratch 退避、図とREADMEの着地、変異実走・受入・commit。