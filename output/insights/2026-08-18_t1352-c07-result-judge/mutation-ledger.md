# [T-1352] C07 consumer wave — 変異台帳

対象 commit: `51cd42c9` (fix C まで)。走行日時 2026-08-18 21:39〜22:01 JST。
harness: `tools/mutation_harness.py`、`--runner-mode dispatch`、`--detached`。
runner argv: `/usr/bin/python3 <worktree>/tools/run_tests.py --force-dispatch <test files> -q -rf`。

## 確定した結果 (KILLED 7 件、冗長 gate 1 件)

| # | 変異位置 | 無効化した検査 | 判定 | 検出した node |
|---|---|---|---|---|
| M1 | `s8c_result_judge.py` C3 成立式 | `mean_delta > delta_min` → `>=` | KILLED | `test_mean_delta_equal_delta_min_is_not_satisfied` |
| M2 | `s8c_result_judge.py` 標本 SD | `statistics.stdev` → `pstdev` (分母 n-1 → n) | KILLED | `test_n_two_uses_sample_sd_denominator_n_minus_one` |
| M3 | `s8c_result_judge.py` cell 集合 | 生成行と事前宣言集合の完全一致検査 | KILLED | `test_publish_cell_missing_extra_duplicate_leaves_no_table[extra]` / `[missing]` / `test_publish_rejects_predeclared_set_mutation_without_deriving_it_from_rows` |
| M4 | `s8c_result_judge.py` publish | 床 receipt の型検査 (publish の必須前提) | KILLED | `test_publish_requires_current_ratified_floor_receipt` |
| M5b | `_evaluate_c07` | 床 field 4 種と床 artifact 2 種の集合一致 | KILLED | `test_c07_negative_control_removes_one_floor_field_only` / `test_c07_literal_floor_fields_without_verification_are_incomplete` |
| M6b | `_evaluate_c07` | validator 戻り値の消費検査 | KILLED | `test_c07_discarded_validator_return_is_incomplete` / `test_c07_dead_validator_assignment_is_not_a_consumer` |
| M7c | `_evaluate_c07` | ratified loader の呼出し実在と戻り値使用の**両層** | KILLED | `test_c07_removed_ratified_loader_call_is_not_a_consumer` |

## erratum (DW-M02 / DW-M04 に従う記録)

初回登録の 6 件は全件 SURVIVED 期待の probe である (DW-M07: KILLED 期待で期待 node が空の spec は
起動前に中止されるため)。観測結果は次のとおりで、初回結果は消さずここに残す。

- **M5 (entrypoint 実在検査) は SURVIVED した。** 注入は実在する (anchor 一意、置換 1 件)。
  等価変異ではなく**他層 mask** である — entrypoint を欠く fixture は後段の床 field 検査や
  条件 ID 検査にも同時に落ちるため、単独無効化では受理集合が変わらない。
  実効 gate である床 field/artifact 集合 (M5b) へ再照準して kill を確認した。
- **M6 (3 entrypoint の返り値検査) も同じ理由で SURVIVED した。** validator 戻り値の消費検査
  (M6b) へ再照準して kill を確認した。
- **M7 (ratified loader) は 1 回目が PARSE_ERROR。** 親が書いた置換が括弧の対応を崩し、
  harness が「rc=1 だが canonical stdout から failed node を確実に抽出できない」として
  fail-closed で停止した。harness が正しく働いた形であり、実装の欠陥ではない。
- **M7b (戻り値使用のみ無効化) は SURVIVED した。** 外側の「loader 呼出しが 1 件も無い」検査が
  同じ負の対照を先に捕まえるための mask である。DW-M02 に従い**両層同時変異 (M7c)** を
  kill 期待つきで事前登録し、期待 node と完全一致で KILLED を確認した。

## 走行 artifact

- 1 巡目 (M1-M6): `mut-probe.json` — summary KILLED=0 / MISMATCH=4 / SURVIVED=2
- 2 巡目 (M5b/M6b/M7): `mut-probe2.json` — MISMATCH=2 / PARSE_ERROR=1
- 3 巡目 (M7b): `mut-probe3.json` — SURVIVED=1
- 4 巡目 (M7c): `mut-probe4.json` — KILLED=1 (期待 node と完全一致)

いずれも job dir `/work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/` にある。

## この台帳が主張しないこと

- M5 / M6 / M7b の生存は**等価変異ではない**。他層に mask されているだけであり、
  当該検査が無意味だという証拠ではない。冗長 gate として残す判断であり、
  単独変異の検出力の証拠からは外す (DW-M03)。
- `_evaluate_c07` は `_MACHINE_EVALUATORS` へ登録していないため、production の
  `evaluate_all` からは到達しない。上表の kill はすべて専用テストによる検出であって、
  実効 gate としての発火を示すものではない。
