## 実装内容

A-1〜A-5 と親-1を指定 3 path に実装しました。

- nested `performance.build_attempt_id` の identity gate を追加
- M4b/M4c/M4d を単一条件の負例へ分割
- landed bundle の存在条件と raw-manifest 照合を強化
- fresh provenance v1 の全必須項目・hash・再現 argv を検査
- M11/M12 を実スクリプトの subprocess 検査へ変更
- `_bench_done_rows` の直接検査を追加
- repo 内の再現 argv を repo-relative 化

## 検証結果

静的検査は成功しました。

- Python AST parse: 成功
- `git diff --check`: 成功
- U+0300〜U+036F: 3 file とも不在
- 所有 path 外の source diff: なし

指定 pytest argv はリポジトリ規律に従い `tools/run_tests.py` 経由で試行しましたが、`qstat -Q` preflight が失敗し、pytest child は起動されませんでした。

- runner rc: `16`
- `child_started`: `false`
- 実行済み test: 0 件
- green nodeid: なし
- pytest 所要秒: N/A
- 状態: 実装済み・未実走

runner は診断 receipt を `output/pegasus-dispatch/4b960a7859006cea4a8231db81ca3e52/receipt.json` に自動生成しました。source diff には含まれず、その後は編集・削除していません。

## 波及可能性

所有外で静的に確認した caller・fixture・consumer は次のとおりです。

- `docs/paper-story/figures/README.md`: CLI 再現コマンド、landed marker、caption の consumer
- `docs/paper-story/results/2026-09-04-a2-certification-reject.md`: provenance `cells` と fig5 bundle の consumer
- canonical `certification.json` / `raw-manifest.json`: tracked authority fixture
- `output/insights/2026-08-28_t2022-a2-certification-run/README.md`: certification hash pin
- durable measurement root: WAL 2 本と raw JSON 4 本
- `orchestrator/tests/skiputil.py`: durable root 不在時の skip helper

所有 test 以外に、この生成器を import する Python caller は見つかりませんでした。landed provenance の生成時 generator hash は live pin にせず、既存成果物も変更していません。

## 総括

**変更 file と行数**

| File | 本 fix 差分 | 現在行数 |
|---|---:|---:|
| [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/plot_a2_certification.py:190) | +14 / -1 | 561 |
| [test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:213) | +66 / -18 | 443 |
| [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/README.md:100) | +1 / -0 | 234 |

commit、`git add`、stash、branch 操作は行っていません。

**所見対応表**

| 所見 | 状態 | 実装 |
|---|---|---|
| A-1 | partial | nested build ID gate と M4b/M4c/M4d 負例を実装。未実走 |
| A-2 | partial | 3 file または README marker を起点とする landed closure を実装。未実走 |
| A-3 | partial | fresh provenance exact schema、件数、output hash、分離 pin、manifest 照合を実装。未実走 |
| A-4 | partial | M11/M12 を実 subprocess CLI 経路へ変更。未実走 |
| A-5 | partial | `_bench_done_rows` の件数 2・stage 集合を直接検査。未実走 |
| 親-1 | partial | cert、manifest、prefix の repo-relative 化と検査を実装。未実走 |
| regressed | なし | 静的差分上はなし。runtime は未確認 |

**変異位置と対 test**

| 変異 | 位置 | 対 nodeid |
|---|---|---|
| M1 | `plot_a2_certification.py:_bench_done_rows:119` | `test_plot_a2_certification.py::test_m1_bench_done_rows_ignore_real_nonbench_stage_keys` |
| M2 | `plot_a2_certification.py:_summarize_samples:122` | `test_plot_a2_certification.py::test_m2_five_samples_are_required_when_all_projections_agree` |
| M3 | `plot_a2_certification.py:_load_external_inputs:179` | `test_plot_a2_certification.py::test_m3_external_sha256_mismatch_is_rejected` |
| M4a | `plot_a2_certification.py:_validate_raw_cell:210` | `test_plot_a2_certification.py::test_m4a_raw_samples_must_match_wal_after_manifest_rebind` |
| M4b | `plot_a2_certification.py:_validate_raw_cell:202` | `test_plot_a2_certification.py::test_m4b_raw_build_attempt_must_match_wal_after_manifest_rebind` |
| M4c | `plot_a2_certification.py:_validate_raw_cell:206` | `test_plot_a2_certification.py::test_m4c_raw_variant_must_match_wal_after_manifest_rebind` |
| M4d | `plot_a2_certification.py:_validate_raw_cell:204` | `test_plot_a2_certification.py::test_m4d_nested_performance_build_attempt_must_match_raw_after_manifest_rebind` |
| M5 | `plot_a2_certification.py:_crosscheck_certification:255` | `test_plot_a2_certification.py::test_m5_certification_median_mismatch_is_rejected` |
| M6 | `plot_a2_certification.py:_crosscheck_certification:260` | `test_plot_a2_certification.py::test_m6_certification_effect_mismatch_is_rejected` |
| M7 | `plot_a2_certification.py:build_provenance:466` | `test_plot_a2_certification.py::test_m7_outer_status_is_copied_into_provenance` |
| M8 | `plot_a2_certification.py:_artist_series:365` | `test_plot_a2_certification.py::test_m8_artist_baseline_is_stock_median_with_stock_genome` |
| M9 | `plot_a2_certification.py:_caption:342` | `test_plot_a2_certification.py::test_m9_caption_distinguishes_correctness_from_performance` |
| M10 | `plot_a2_certification.py:_publish_outputs:479` | `test_plot_a2_certification.py::test_m10_layout_failure_publishes_no_outputs` |
| M11 | `plot_a2_certification.py:_load_tracked_authority:99` | `test_plot_a2_certification.py::test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs` |
| M12 | `plot_a2_certification.py:_load_tracked_authority:101` | `test_plot_a2_certification.py::test_m12_whitespace_changed_raw_manifest_fails_cli_with_zero_outputs` |
| M13 | `plot_a2_certification.py:_validate_raw_cell:212` | `test_plot_a2_certification.py::test_m13_raw_source_commit_must_equal_current_pin_after_manifest_rebind` |

未対応事項は、pytest 全体の実走と、親による fig5 三成果物の再生成です。現行 landed provenance の絶対 argv は編集禁止に従って変更していません。