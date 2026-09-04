## 実装結果

段 4 裁定 §4 と変異事前登録 M1〜M13 を所有 3 path に実装しました。

- A-2 専用 CLI、canonical authority hash、外部 6 file の manifest hash 検査
- WAL/raw/certification の統計・identity・effect 相互検算
- status/effects の certification からのコピー
- 2×2 Figure、保存前 fail-closed layout check、temp→`os.replace`
- provenance v1、決定的 caption、展開済み再現 argv
- production-size fixture と各変異に対応する検査
- plotting README の A-2 節（34 行）

A-2 driver、policy、既存 test は変更しておらず、現行の受理・拒否挙動と受理集合は変えていません。commit、git add、stash、branch 操作も行っていません。

## 検証結果

指定された exact pytest コマンドは、Pegasus ログインノードの実行防護により起動前に拒否されました。

```text
python3 -m pytest orchestrator/tests/test_plot_a2_certification.py -q -p no:cacheprovider -rf
```

`tools/run_tests.py` 経由も試しましたが、`qstat -Q` の infrastructure error、child 未起動、rc=16 でした。したがって pytest は「実装済み・未実走」であり、closed とは申告しません。

補助的な直接関数ハーネスでは、専用 test の assertion を実行して 2.3 秒で `20 passed / 0 failed / 1 skipped` でした。skip は親所有の landed fig5 が未配置であることによるものです。`py_compile` と実寸 Figure layout check も成功しています。

durable authority を使った最終 CLI 実走は 1.45 秒で成功し、次の 3 成果物を生成・schema 検査しました。

- `/tmp/izanagi-a2-author-20260904-004/fig5.png`
- `/tmp/izanagi-a2-author-20260904-004/fig5.pdf`
- `/tmp/izanagi-a2-author-20260904-004/fig5.provenance.json`

provenance は tracked 2、external 6、cells 4、artist series 20、`outer_status=reject` を記録しています。

F42 の検索では、test file 集合を動的列挙する `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` が該当しました。関数単位では pass。plotting generator 一覧を exact pin する別 meta-test は見つかりませんでした。

## 総括

変更 file は次の 3 本です。

- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/plot_a2_certification.py) — 548 行
- [test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py) — 395 行
- [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/README.md:100) — 全 233 行、A-2 節 +34 行

変異位置と対応 test は以下です。

| 変異 | 位置 | 対応する負例・感度 test |
|---|---|---|
| M1 | `plot_a2_certification.py:_bench_done_rows:112` | `test_m1_bench_done_rows_ignore_real_nonbench_stage_keys` |
| M2 | `plot_a2_certification.py:_summarize_samples:121` | `test_m2_five_samples_are_required_when_all_projections_agree` |
| M3 | `plot_a2_certification.py:_load_external_inputs:169` | `test_m3_external_sha256_mismatch_is_rejected` |
| M4a | `plot_a2_certification.py:_validate_raw_cell:190` | `test_m4a_raw_samples_must_match_wal_after_manifest_rebind` |
| M4b | `plot_a2_certification.py:_validate_raw_cell:190` | `test_m4b_raw_build_attempt_must_match_wal_after_manifest_rebind` |
| M5 | `plot_a2_certification.py:_crosscheck_certification:250` | `test_m5_certification_median_mismatch_is_rejected` |
| M6 | `plot_a2_certification.py:_crosscheck_certification:250` | `test_m6_certification_effect_mismatch_is_rejected` |
| M7 | `plot_a2_certification.py:build_provenance:449` | `test_m7_outer_status_is_copied_into_provenance`（diagnostic sensitivity pin） |
| M8 | `plot_a2_certification.py:_artist_series:349` | `test_m8_artist_baseline_is_stock_median_with_stock_genome` |
| M9 | `plot_a2_certification.py:_caption:324` | `test_m9_caption_distinguishes_correctness_from_performance` |
| M10 | `plot_a2_certification.py:_publish_outputs:472` | `test_m10_layout_failure_publishes_no_outputs` |
| M11 | `plot_a2_certification.py:_load_tracked_authority:92` | `test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs` |
| M12 | `plot_a2_certification.py:_load_tracked_authority:92` | `test_m12_whitespace_changed_raw_manifest_fails_cli_with_zero_outputs` |
| M13 | `plot_a2_certification.py:_validate_raw_cell:190` | `test_m13_raw_source_commit_must_equal_current_pin_after_manifest_rebind` |

関数ハーネスで pass した追加 node は、fixture shape/statistics、実寸 Figure、CLI 3 出力、canonical authority literal、部分欠落 failure、実 durable input の各 test です。landed fig5 closure node だけは親成果物待ちで skip でした。

静的な波及可能性は次のとおりです。

- 親が生成する fig5 三成果物と `figures/README.md` の caption byte copy が新 provenance/CLI の consumer。
- 新 test は `skiputil` を利用するが、共有 fixture は変更していない。
- pytest collection の動的 test-file 列挙に新 test が加わるが、該当 exclusion meta-check は関数単位で通過。
- 既存 plotting generator、A-2 driver/policy、frozen artifact 一覧への変更はない。
- parent-owned docs/results/decision/insight の既存変更は保持し、編集していない。

未対応事項は、正式 pytest 実走、mutation harness、親所有 fig5 closure test、親の全走です。また runner 試行時に git-ignored の dispatch receipt `output/pegasus-dispatch/57a11f47998907ba4909731741b01643/receipt.json` が自動生成されましたが、所有外なので削除していません。