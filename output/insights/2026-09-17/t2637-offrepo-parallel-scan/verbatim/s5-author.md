## 変更一覧

変更は指定の 2 ファイルのみ。docs 編集、git add、commit は行っていません。

`tools/audit_dangling_commits.py`:

| 行 | 変更・役割 |
|---|---|
| 30 | `OFFREPO_SCAN_WORKERS = 16` と env 名定数を追加 |
| 872 | `_OffrepoCounts`: 各走査の directories / files / failures |
| 881 | `_OffrepoCountSlot`: lock 付き累積計数の公開・読取 |
| 897 | `_offrepo_scan_workers`: 列挙時の env 解決と正整数検証 |
| 908 | `_process_offrepo_iteration`: 逐次・並列で共有する候補照合 |
| 966 | `_scan_offrepo_subtree`: 部分木 walk とローカル結果・計数 |
| 990 | `_merge_offrepo_candidates`: first-seen を保持し owners / aliases を union |
| 1004 | `_enumerate_offrepo_candidates`: root 処理、並列実行、主 thread の heartbeat、順序付き merge |

`orchestrator/tests/test_audit_dangling_commits.py`:

- 30: env を clear する autouse fixture。
- 1189: 旧並列禁止テストを同じ位置で列挙等価性テストに置換。
- 1252: 小規模 tree の共有 helper。
- 1259〜1527: 残る新設 9 テスト。

## 実走結果

実行コマンド:

```text
PYTHONPATH=. python3 orchestrator/tests/test_audit_dangling_commits.py
```

**153 passed、0 failed、0 skipped、9.52 秒、rc=0。**

以下の nodeid はすべて `orchestrator/tests/test_audit_dangling_commits.py::` を接頭辞とし、各 1 件 passed です。

```text
test_parallel_offrepo_scan_preserves_enumeration
test_parallel_offrepo_scan_preserves_report
test_parallel_offrepo_scan_uses_multiple_threads
test_parallel_offrepo_scan_preserves_failure_counts
test_parallel_offrepo_scan_preserves_first_seen
test_parallel_offrepo_scan_propagates_worker_exception
test_parallel_offrepo_scan_heartbeat_runs_on_caller
test_offrepo_scan_worker_configuration
test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool
test_parallel_offrepo_scan_unreadable_subdirectory
```

指定された既存の焦点 node も、同じ全件走で passed:

```text
test_offrepo_walk_emits_internal_rate_limited_heartbeat
test_flat_offrepo_filename_loop_emits_heartbeat
test_candidate_comparison_emits_file_and_read_chunk_heartbeats
test_stage_instrumentation_reports_separate_cost_surfaces
test_stage_instrumentation_covers_root_suppression_and_final_report
test_candidate_session_materialization_is_inside_comparison_stage
test_negative_unreachable_symlink_is_not_suppressed
test_offrepo_scan_is_skipped_without_candidate_basenames
test_negative_unreadable_offrepo_root_keeps_finding
test_negative_external_file_changed_during_comparison_is_not_suppressed
test_negative_external_file_ctime_change_during_comparison_is_not_suppressed
test_blob_contents_are_loaded_only_after_basename_size_mode_prefilter
test_comparison_mode_check_rejects_post_prefilter_mode_change
test_same_oid_external_file_is_compared_once_and_fanned_out
test_distinct_same_bytes_external_files_are_all_fanned_out
```

`git diff --check` も rc=0。consumer テスト、変異実走、実根での等価性・性能測定、親の統合検査は未実走です。

## 期待値変更

既存テストの変更は、旧 1183〜1186 の `test_initial_patch_contains_no_parallel_execution` を同じ位置で置換した **1 件のみ**です。

HEAD と作業中ファイルの AST を比較し、残存する既存テスト関数はすべて不変と確認しました。flat heartbeat の期待文字列と monotonic 3 値も不変です。

production の既存関数で変更したのは `_enumerate_offrepo_candidates` だけです。

## 波及可能性

指定 3 語を `rg` と tracked 全体の `git grep` で検索しました。

- production の直接 caller は `tools/audit_dangling_commits.py:1705` の `audit_with_offrepo` のみ。
- 直接呼出し・stub は対象テストファイル内のみ。既存参照は現在の 1031、1054、1076、1168、2564、2598、2637、2697 行。
- 新 env の fixture は対象テストモジュール内のみ。共有 `conftest.py` は変更なし。
- 所有外の一致は次の記録上の言及のみ:
  - `docs/archive/worklog-phase3-0827-1019-1020.md:979`
  - `output/insights/2026-09-16/t2637-offrepo-scan-yield/README.md:83`
  - 同 `parent-measurements.md:34`

間接 consumer は `tools/check_branch_rescue.py:58` の監査 subprocess。220 行の env allowlist に新 env はないため、rescue 経由には workers override が伝わらず既定 16 になります。

波及しうる consumer テストは `test_check_branch_rescue.py`、`test_branch_rescue_ledger.py`、`test_check_docs.py`。変更・実走はしていません。

## 受理集合の自己申告

**抑止の受理集合を変更していません。**

basename→size→executable、`lstat`、`S_ISREG`、symlink 非追跡、root 検査、first-seen、既存 alias 配布を維持しました。workers=1 / 4 の列挙結果と、抑止・未参照 copy・残存 finding・scan failure を含む `AuditReport` 全体が、独立期待値に一致しました。

境界照合、比較処理、抑止集約は未変更です。実根の旧版との逐語一致は未確認です。

## 変異 matrix の対象行と予想 killer

以下の `A` は `tools/audit_dangling_commits.py`。old は現在の実装の逐語引用です。killer の接頭辞は上記テストファイルの nodeid と同じです。**予想であり、変異実走結果ではありません。**

| ID | 対象と old | 変異・予想 |
|---|---|---|
| M0 | A:1010 `"""blob を読まず basename・size・mode が一致する外部実体を列挙する。"""` | 意味不変の言い換え。SURVIVED 予想 |
| M1 | A:1103 `counts.failures += failures` | worker failures 合算を除去。`test_parallel_offrepo_scan_preserves_failure_counts` |
| M2 | A:1068 `slots = [_OffrepoCountSlot() for _ in subtrees]` | この直前で `subtrees = subtrees[:-1]`。`test_parallel_offrepo_scan_preserves_enumeration` の末尾固有候補が欠落 |
| M3 | A:1057 `root, iteration, by_basename, possible, counts, pulse` | 並列 root 処理に渡す filenames を空へ。`test_parallel_offrepo_scan_preserves_enumeration`、flat heartbeat テスト |
| M4 | A:980 `subtree, topdown=True, onerror=counts.record_error, followlinks=False` | `followlinks=True`。`test_parallel_offrepo_scan_preserves_enumeration` |
| M5 | A:1000 `existing.owners.update(group.owners)` | 既存 group への merge 時に `existing.external = group.external` を追加。`test_parallel_offrepo_scan_preserves_first_seen` |
| M6 | A:1085 `found, final_counts = future.result()` | worker 例外を捕捉し空結果・ゼロ計数に置換。`test_parallel_offrepo_scan_propagates_worker_exception` |
| M7 | A:1075 `_scan_offrepo_subtree, subtree, root, by_basename, slots[index]` | submit 対象を、progress callback を直接呼んでから本物 worker を呼ぶ wrapper に変更。`test_parallel_offrepo_scan_heartbeat_runs_on_caller` |
| M8 | A:30 `OFFREPO_SCAN_WORKERS = 16` | 16→0。`test_offrepo_scan_worker_configuration` |
| M9 | A:1011–1012 `if not candidates:` / `return {}, 0, False` | 早期 return より前に executor を生成。`test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool` |

## 総括

裁定 §2 の実装と指定 10 テストを完了し、対象モジュール全 **153 件 passed** を確認しました。既存期待値の変更は指定の置換 1 件だけです。

段 5 の実装を親へ返します。prototype、実根等価性、D958 性能条件、変異実走は未判定であり、wave の受理・closed は主張しません。
