# 焦点走・単独再走・補助変異走の要約 (親の実走、計算ノード dispatch)

生 log は job dir (`/home/SFC/tanab/.claude/jobs/0a534e2c/tmp/focus*.log`)。ここは集計行と赤 node だけ。

| TAG | 対象 | tip | 結果 | 備考 |
|---|---|---|---|---|
| focus1 | `test_t1259_scan_bound.py` + `test_t1259_qsub_env_delivery_probe.py` | 4208bf332 (未 commit の同内容) | 54 passed / 11.70 秒 | request 11285.nqsv、Elapse 17 秒 |
| focus2 | `test_acceptance_schedule_order.py` + `test_plain_runner_coverage.py` + `test_paper_story_a1_headline.py` + `test_real_repo_serialization.py` | 4208bf332 | 223 passed / 1 skipped / 1 failed (35.76 秒) | 赤 = `test_real_repo_serialization.py::test_real_repo_writers_do_not_materialize_oracle_environment_candidates` → 内側で直接呼ぶ `test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls` の lock identity preimage 不一致 (`identity_preimage` の `ccbench_commit` 以降)。本 wave の差分は到達しない。G5 (duration 台帳 90% 被覆) は緑 = 新 3 node の台帳登録は不要 |
| focus3 | 上の赤 2 node の単独再走 | 4208bf332 | 2 passed / 21.94 秒 | 非再現 = 非帰属 (DW-O18、同一 tip で 1 回) |
| focus-m2aux | `test_t1259_qsub_env_delivery_probe.py` (helper を M2 形へ DW-O19 一時変異) | 4208bf332 + 一時変異 | **16 failed / 35 passed** (5.23 秒) | 復元後 sha256 = HEAD と一致。赤 16 node は下表 |

## focus-m2aux の赤 16 node (fixture の実走査が `head` / `source_sha256` 経由で持つ検査力)

- `test_r1_binds_all_three_explicit_values_and_skips_real_driver` — `assert None == PosixPath(...)`
- `test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal` — 同上
- `test_r3_records_only_the_observed_ambient_approval_condition[not-delivered]` / `[delivered-mismatching-literal]` — 同上
- `test_r1_projection_follows_observed_approval_not_request_identity[approval-missing]` / `[approval-mismatch]` — `KeyError: 'floor_section8_source_projection'`
- `test_r2_unexpected_approval_presence_is_unbound_and_not_green` — 同 KeyError
- `test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE]` / `[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN]` — `KeyError: 'explicit_env_comparisons'`
- `test_swapped_r2_hex_values_fail_exact_binding` — 同 KeyError
- `test_submission_source_digests_are_bound_to_runtime_bytes[campaign-bytes]` / `[repo-pbs-bytes]` / `[executing-pbs-bytes]` — `assert False`
- `test_r1_manifest_rejects_approval_that_does_not_equal_nonce` / `test_r3_manifest_rejects_nonliteral_ambient_approval` — `Regex pattern did not match`
- `test_main_emits_one_prefixed_stdout_line_and_auxiliary_result` — `assert 1 == 0`

35 passed の側 (`test_job_start_requires_manifest_head_detached_and_clean_repository[*]` を含む) は snapshot を test 内で差し替える、
または snapshot を読まない test であり、fixture の実走査に依存しない。

## 受入 (計測走、TAG meas-1)

- 投入 2026-09-20 00:38:46 JST、終了 00:49:41、tested main `60bbe8a65a6f1634e0833bed74677e994a33e957`、tip `78b2c2690888f488473712a9f1d7743d9fbf8045`
  (4208bf332 + main 取り込み 2 回)。門番: 他 leader ≤ 2 ∧ load1 ≤ 60 (投入時 load 7.3、他 leader 2)。
- 結果 **25,327 passed / 69 skipped / 赤 0、child-green (受領証 `acceptance-receipt-meas-1.json`)**。session root
  `/work/1/SFC/tanab/.izanagi-acceptance-shards/da379915ed116c8b5c6937cbe325b601`。
- shard-0 (bnode009、testsuite time 507.8 秒、開始 00:40:50): t1259 51 case、fixture を含む case は 1 件 (`test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo` 9.20 秒)、他 50 case は 2 秒未満、error 0。新 test 3 本は shard-1 (合計 0.2 秒)。
