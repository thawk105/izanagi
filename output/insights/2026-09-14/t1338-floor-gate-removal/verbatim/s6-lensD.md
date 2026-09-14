## 結論 (採否と最重要 3 件)

**現状は不採用。静的検査で must-fix 2 件を確認しました。**

1. **real：focus 外の consumer test に行番号参照の破損があります。** `test_ccbench_spawn_sites.py` は旧行 1793 を辞書キーにしていますが、対象呼出しは 1783 に移動しています。
2. **real：driver の退役 1 本は過剰です。** 撤去した hash 供給ではなく、残存する abort → outcome 変換を検査していました。
3. **real：MU7 の登録先が誤っています。** 指定位置は store hash 負例です。receipt 検査の例外握り潰しを kill する既存テストは別にあります。

以下、`M` は `orchestrator/campaign/s8b_oracle_manifest.py`、`D` は同ディレクトリの `s8b_oracle_driver.py`、`TM`・`TD` は対応する `orchestrator/tests/test_*.py` を指します。削除箇所の旧行番号は `integrated.diff` によります。

## must-fix

**1. real：既存 consumer の sink 参照が破損。**

`orchestrator/tests/test_ccbench_spawn_sites.py:2939` は `_BuildSink(..., 1793, "campaign")` を生成し、`:2951` で `classifications[s8b_sink]` を参照します。`_BuildSink` は行番号を比較対象に含む frozen dataclass（`:668`）で、実際の収集は `node.lineno` を使います（`:811`）。現在の `pipeline.evaluate` は **D:1783** です。

既存参照を現物へ合わせる修正が必要です。新しい検査は不要です。

**放置時：sink の参照キーが実体と一致せず、既存の分類結果を取得できません。**

**2. real：残存する outcome 契約のテストを退役させています。**

削除された `test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome`（TD 旧:6296）は `_fake_abort_evaluate_factory("bench-binary-mismatch")` を注入します。この helper は理由を直接 WAL に書き（TD:2409）、実 pipeline の hash 比較を通りません。検査対象は、現在も残る **D:868 の `binary-mismatch` への変換**です。

このテストの退役を取り消す必要があります。段 4 裁定の退役指定とは食い違いますが、その指定の根拠である「撤去対象の正例」という同定が現物と一致しません。

**放置時：成果物の値は直ちには変わりませんが、残存する trial-result の outcome 変換の回帰検出を失います。**

## real と判定した所見

**変異 matrix：MU7 の登録先は kill 不能。MU5 は両 null 分岐を個別には固定していません。**

| 変異 | 静的判定と既存 kill 先 |
|---|---|
| MU1 | **成立見込み。** `test_verify_detects_freeze_byte_tampering`（TM:821）。改行追加だけなので JSON 内容は不変。M:975 の比較を外すと期待するエラーが消えます。 |
| MU2 | **エラー文一致による kill は成立見込み。** `test_missing_holdout_build_stays_accepted_but_verify_rejects`（TM:450）。ただし M:995 を外しても M:1002 の cell product 比較で拒否されます。単独の受理障壁を示す負例ではありません。 |
| MU3 | **エラー文一致による kill は成立見込み。** `test_subset_manifest_build_stays_accepted_but_verify_choke_point_rejects`（TM:413）。ただし `spec_sha256="a"*64` と `_verify` の承認 snapshot fallback（TM:305）を使うため、cell gate を外した先の承認検証まで通る正例ではありません。 |
| MU4 | **成立見込み。** 新設 `test_verify_manifest_rejects_retired_floor_budget_snapshot_key`（TM:797）。許可 key ⊆ document key へ緩めれば、固定したエラー文が消えます。ただし承認 pin 未設定と manifest ID 未更新のため、変異後の受理までは示しません。 |
| MU5 | **一括変異への kill は成立見込み。** `test_current_freeze_is_rejected_as_non_executable_manifest`（TM:319）。実 freeze は floor・budget とも null（`output/s8b-freeze/holdout_freeze.json:622`）。現在発火するのは floor 分岐だけです。**budget-null 分岐だけを無効化しても、このテストは kill しません。** 両分岐を外した場合は外形検査の別エラーになり、regex 不一致で kill します。 |
| MU6 | **成立見込み。** `test_v2_store_bytes_are_checked_against_admission_subject_independently`（TD:5572）。実 launch validation 後に store bytes だけを改変し、実 `_prepare_v2_execution` の D:1054 へ到達します。 |
| MU7 | **登録先では不成立。** 裁定が指す旧 TD:6233 は `test_v2_store_hash_mismatch_is_refused`（現 TD:6194）内です。receipt は正常なので、例外捕捉を握り潰しても store mismatch 拒否は残ります。使用可能なのは **`test_v2_foreign_cell_admission_receipt_is_refused_before_store_read`（TD:5505）**。receipt swap 後、実 validator の例外を D:1041 が翻訳します。握り潰すと store 読込み禁止 stub が発火し、テストは失敗します。 |

MU7 の代わりに `test_oracle_driver_accepts_conditional_sort_receipt_and_rejects_its_absence`（TD:5542）を使うのも不適切です。欠落させる `sort_swo_oracle` は **例外捕捉より前の exact key 検査 D:1025** で拒否されます。

**focus 集合の不足も real です。**

参照先・helper の実体まで追って確認した追加対象は次です。未実行であり、破損を確認したのは上記 sink 行番号参照です。

| file | 参照の根拠 |
|---|---|
| `test_ccbench_spawn_sites.py` | `:2928` → `_production_build_sources` → AST sink 分類。上述の破損あり。 |
| `test_official_perf_closure.py` | `:154`、`:176` の述語表が driver／verdict の関数内呼出しを検査。 |
| `test_env_contract.py` | `:83` の検査対象表が driver source を含む（`:94`）。 |
| `test_s1_known_axes_freeze.py` | `test_historical_oracle_nonadapter_reaches_current_semantics`（`:1135）が実 driver gate を呼ぶ。 |
| `test_real_repo_serialization.py` | `:2392` で driver test を import し、`:2395`、`:2410` の関数参照を消費。 |
| `test_campaign.py` | `:6892`、`:6909`、`:6917`、`:6932` が、今回供給元を失った generic pipeline 引数の契約を検査。 |

## refuted と判定した所見

**refuted：新設負例は前段の別エラーで緑になっている。**

TM:812 は実 `verify_manifest` を直接呼びます。freeze 引数は非 null、入力は正常な JSON object で、最初の拒否は **M:965 の top-level exact key 比較**です。期待文も `^...$` で固定されています。validator の stub はありません。hash は TM:803、`:816` で実行時に計算し、揮発 payload を期待値へ焼き込んでいません。

ただし「それ以外は最終受理まで正常な負例」ではないことは、MU4 欄のとおりです。

**refuted：共有 fixture の値を弱めた。**

`integrated.diff` の fixture 差分は冒頭 docstring だけです。値を生成する `s8b_v2_freeze_fixture.py:31`、`:51`、`:63` は変更されていません。

**refuted：manifest の退役 11 本に過剰な削除がある。**

削除された関数は以下です。いずれも変更入力・専用 assertion は撤去した per-pair 述語に対応します。

| 旧 TM 行 | 関数名 |
|---|---|
| 935 | `test_snapshot_accepts_valid_per_pair_floor` |
| 946 | `test_snapshot_accepts_explicit_null_pair` |
| 957 | `test_snapshot_rejects_null_pair_with_nonnull_scalar_alt` |
| 967 | `test_snapshot_accepts_all_null_holdout` |
| 977 | `test_snapshot_rejects_scalar_v1_floor` |
| 986 | `test_snapshot_rejects_stock_key_in_pairs` |
| 994 | `test_snapshot_rejects_missing_pair` |
| 1003 | `test_snapshot_rejects_extra_pair` |
| 1011 | `test_snapshot_rejects_scale_ref_null_with_finite_pair` |
| 1020 | `test_snapshot_rejects_scalar_alt_not_max` |
| 1037 | `test_snapshot_rejects_nonfinite_pair_value` |

正例は残存 validator も通りますが、それら別契約に対する独立した assertion はありません。driver の丸ごと退役 1 本については must-fix のとおりです。

**refuted：happy-path の assertion 削除が別契約まで落とした。**

`test_v2_gate_happy_path_completes_and_binds_env_store_receipt` から外した assertion は `expected_perf_sha256` の membership 比較だけです。completed、trial 数、clocks、numactl、execution receipt の assertion は TD:5489 に残っています。

**refuted：撤去によって残存テストが新たに恒真化したことを確認できた。**

該当する残存テストは**確認範囲ではゼロ**です。ただし、次を production 呼出し維持の証拠には数えられません。

- TM:954 の `test_snapshot_rejects_oracle_shared_false`
- TM:961 の `test_snapshot_rejects_extra_top_level_floor_key`

両者は TM:948 の helper から validator を直接呼ぶ unit test です。production の呼出し削除を検出しませんが、今回その呼出しは M:1016 に残っています。

また TM:324 の `test_each_replicate_is_complete_product_and_each_cell_occurs_n_times` は builder 出力の独立計数であり、verifier の発火証拠ではありません。これは今回の撤去による劣化ではありません。

## scope 外の裁定候補

- **real：D:869 のコメントが撤去後も「TOCTOU 第二防壁」を現行経路として説明しています。** 今回の供給撤去とは整合しません。残存 outcome 契約の位置づけとして親へ返します。
- **refuted：`test_holdout_observation.py:804` は driver consumer である。** caller 名を parameter にしていますが、実行は `runner.measure_point`（`:827`）で、caller は `assert caller`（`:839`）にしか使いません。driver 経路の実効証拠には数えられません。

新しい gate・台帳・互換層の提案はありません。

## 総括

旧 key 負例と fixture 維持は妥当です。一方、**sink 行番号参照の修正、残存 outcome テストの退役取消し、MU7 の照準訂正**が必要です。MU2〜MU5 は、変異を kill することと単独の受理障壁を証明することを区別して報告してください。

pytest・編集・commit は行っていません。