## 所見別の対応表

| 所見 | 状態 | 変更箇所 |
|---|---|---|
| B-1 | closed | `_authority_data` の条件検査・provenance、`_caption`、`make_figure` の2行脚注。fixture・条件期待値・不一致拒否テストを追加 |
| B-2 | closed | `test_relation_boundaries_match_producer_rule` と `test_cell_interval_on_margin_edge_is_inside` を追加。分類実装は変更なし |

## 実走した検査

self-run harness：**52 passed / 1 failed / 0 skipped / 0 errors、rc=1**。[全53 nodeid と結果](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/probe-fig13/fix1-test-results.txt)。

追加した以下の nodeid はすべて PASS（共通 prefix：`test_plot_b10_waiting_grid_forest.py::`）。

- `test_calibration_records_or_threads_mismatch_is_rejected`
- `test_workload_skew_or_rratio_mismatch_is_rejected`
- `test_relation_boundaries_match_producer_rule`
- `test_cell_interval_on_margin_edge_is_inside`

`test_plain_runner_coverage.py`：**3 passed / 0 failed / 0 skipped**。

- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_this_metatest_is_itself_self_runnable`

生成器・test への `_python_has_perf_predicate` は両方 **False**。条件検査4件の除去と端点比較4件の変異は、直接呼び出しですべて **KILLED**（[結果](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/probe-fig13/fix1-mutations.txt)）。

実データ CLI：**rc=0**。PNG・PDF・provenance を生成し、レイアウト検査と `validate_repo_closure(prov, REPO)` / `validate_external_sources(prov, EVIDENCE_ROOT)` は成功しました。

`measurement_conditions`：

```json
{
  "environment": "Pegasus compute nodes",
  "threads": 48,
  "protocol": "silo",
  "workloads": ["write-heavy", "balanced", "read-heavy"],
  "means_us": [2, 5, 10, 25, 50, 100],
  "reps": 5,
  "blocks": 3,
  "records": 1000000,
  "zipf_skew": "0.9",
  "rratios": {"write-heavy": "5", "balanced": "50", "read-heavy": "95"},
  "rmw": "0",
  "max_ope": "10",
  "extime_s": 3
}
```

caption の逐語：

> Conditions: Pegasus compute nodes, 48 threads, silo, 1,000,000 records, Zipf skew 0.9, read ratio 5 / 50 / 95 (write-heavy / balanced / read-heavy), read-modify-write disabled, max operations 10, 3 s per repetition, YCSB write-heavy / balanced / read-heavy, commanded mean wait mu 2, 5, 10, 25, 50, 100 us, 5 reps x 3 blocks, CCBench pin 511c953, report request 978195.nqsv, preregistration commit 77b33e37d, source commit 2a338449b.

## 未実走・期待赤

`test_plot_b10_waiting_grid_forest.py::test_landed_fig13_repo_closure_and_caption_when_present` が期待赤です。実際の失敗理由は `fig13 integration bundle is incomplete`。skip / xfail 化していません。

指定に従い `tools/run_tests.py`・pytest は未実行。全変異 matrix と着地後検査は親側に残ります。

## 受理・拒否の含意

hash override 下でも、records・threads・skew・rratio の不一致を新たに拒否し、env・workload 順・rmw・max_ope・実行時間・反復数も指定条件との一致を要求します。固定 pin の実データ受理と producer の端点分類は変わりません。

正例：実 report `978195.nqsv` は生成・両閉包検査まで成功しました。

## 総括

実装済み：B-1 / B-2、指定2ファイルと scratch のみ変更、commit なし。
検査：52 passed、期待赤1、skip 0。実データ生成・両閉包成功。
未実走：pytest・全変異 matrix・着地後検査。
親への依頼：最終図の再生成、README の caption / SHA 更新、着地検査・commit。