## 変更の要約

指定の新規2ファイルだけを追加しました。commit は作成していません。

- [b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a2/orchestrator/campaign/b5_generator_contrast_report.py)：511行。統計・台帳検査・anomaly訂正・pilot記述・CLI。
- [test_b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a2/orchestrator/tests/test_b5_generator_contrast_report.py)：512行、54ケース。

## 逐語適合の確認

| 規則 | 実装 |
|---|---|
| §6 endpoint固定、fresh 5 sessionのmedian、探索最大値を流用しない | `_validate`、`_project` |
| anomalyの全arm・全系列への波及、履歴保持、日付付き結果訂正 | `build_report`、`_project` |
| 同workload・同blockのstock共有fallback、欠測との区別 | `_project` |
| §7.1 系列番号で対形成、12系列・3blockの配置検査 | `_validate`、`pair_differences` |
| §7.2 標本CVの4値最大、floor、精度gateの厳密な超過条件 | `stock_cv_floor`、`decide_comparison` |
| §7.3 inclusive exact permutation、族6固定のHolm | `exact_sign_flip_p`、`holm_six` |
| fallback 2対以上で副解析へ切替、全統計を再計算 | `decide_comparison` |
| 両baselineの連言、独立性の限定文、副解析の除外側・数 | `build_report`、`decide_comparison` |
| §7.4 判定順1〜8 | `decide_comparison` |
| pilotは記述のみ、登録判定禁止 | `build_report` のpilot経路 |

発効束との照合、実行順の均衡、block間の1時間隔離は、現行台帳だけでは検証できません。報告にも検証範囲を明記しました。

## 新 test 一覧

主要な固定例と変異対応です。名前はすべて `test_` 始まりです。

| テスト名 | 根拠・検出対象 |
|---|---|
| `test_sign_flip_equal_absolute_fixed_counts` | 固定値13/4096、79/4096 |
| `test_sign_flip_independent_small_enumeration_and_inclusive_ties` | 独立した小標本全列挙、同値tail |
| `test_holm_fixed_six_kills_m16` | **M16**：0.009は族5なら通り、族6では不成立 |
| `test_holm_stage_threshold_and_family_dependence` | 段階閾値、他比較への依存 |
| `test_holm_unavailable_holes_and_stepdown_stop` | p=1穴埋め、段階停止 |
| `test_stock_floor_four_cvs_and_sample_denominator` | 4 CV最大、**標本→母CV変異** |
| `test_precision_boundary_equality_is_accepted` | CV=2fの等号 |
| `test_fallback_one_to_two_recomputes_all_statistics` | **fallback閾値2→3変異** |
| `test_secondary_five_pairs_and_empty_block` | 残存5対、block空 |
| `test_order_protocol_before_missing_before_generation_before_precision` | **判定順1/2・3/4の変異** |
| `test_later_decision_order_and_equivalence_is_not_nonsignificance` | 優越・同等・逆差・残り |
| `test_registered_twelve_pairs_three_blocks` | 正差・零差・逆差 |
| `test_one_baseline_win_is_not_workload_superiority` | **片baseline勝利の採用変異** |
| `test_pilot_json_descriptive_only_kills_m17` | **M17**：実JSON、n=1、stock 5件 |
| `test_registered_mutants_killed_independently` | 上記7変異をメモリ上に注入し、対応テストの失敗を確認 |

その他の検査：

- 入力・floor：`test_sign_flip_rejects_invalid_sample`、`test_floor_missing_or_nonfinite`、`test_nonfinite_floor_precedes_generation_and_precision`
- endpoint・anomaly：`test_fresh_median_not_search_max_and_slow_endpoint_not_replaced`、`test_anomaly_cross_arm_cross_series_order_independent_and_workload_local`、`test_score_anomaly_no_reselection_and_stock_anomaly_invalidates_floor`
- fallback・欠測：`test_missing_score_never_uses_fallback`、`test_fallback_uses_shared_block_and_retains_missing_stock`、`test_stock_identity_mismatch_is_not_fallback_data`
- 台帳：`test_invalid_categories_fail_closed_without_exception`、`test_missing_json_and_duplicate_series`、`test_malformed_event_shapes_report_invalid`、`test_invalid_comparison_stays_in_family_without_poisoning_other_cells`
- attempt・pilot：`test_submission_duplicates_do_not_double_count_attempts`、`test_a1_opportunity_before_physical_attempt_and_retry_accounting`、`test_pilot_cannot_be_relabelled_registered`

## 実走結果

| 対象nodeid／実行形 | 結果 |
|---|---|
| `test_b5_generator_contrast_report.py::*`：指定plain harness | **54 passed、rc=0** |
| 同 `test_registered_mutants_killed_independently[...]` | **7変異検出**（54件に含む） |
| `test_official_perf_closure.py`：指定plain harness | **7 passed、rc=0** |
| `test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap` | **未実走** |
| 同 `::test_real_campaign_package_uses_relative_sibling_imports` | **未実走** |
| `git diff --check` | 通過 |

CLI形の2件は、正規ランナーが `qstat -Q` 事前確認でrc=16、`child_started=false` となりました。

## 波及

- perf inventory述語の直接評価：**False**。既存inventory変更は不要です。
- import方向はreport→A1のみ。build・qsub・追加測定・WAL直接読取りはありません。
- A1への要望：job Elapse、失敗・timeoutを含むLLM待機時間、登録配置と発効束の照合材料。未記録項目は推測せず欠測表示します。
- stock成立判定にはA1の純粋な `_stock_established` を再利用しています。

## 未了・懸念

- campaign CLI形の2検査は、**実装済み・当該検査未実走**です。
- 実台帳との統合、登録配置・発効束の外部証拠との照合は未確認です。
- 本走の認可・統計的独立性の実証を、この実装や合成テストの通過から主張しません。

## 総括

指定2ファイルの実装と54ケースの検証を完了しました。M16/M17を含む7変異を独立したテストで検出し、未commitの差分を残しています。

自動実行前審査の `guard_bash` は、CLI形検査の直接pytest実行を「Pegasusログインノード上の重量処理」として拒否しました。正規ランナーもdispatch事前確認で停止したため、その2件は合格扱いにしていません。