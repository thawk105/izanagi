[receipt-schema-v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json) を作成しました。ただし、作業中に別セッションが要件文書自身を変更したため、現在の worktree に対する exact 1:1 と「新規1ファイルだけ」の条件は未達です。

開始時の `git status --short` は空でした。作業中に出現した所有外変更は上書き・復元していません。

## object path と key 集合

共通 object を参照する複数 path は波括弧でまとめています。

| § | object path | key数 | key一覧 |
|---|---|---:|---|
| 2 | `$` | 18 | schema_version, study_id, declared_use_class, study_stage, series_id, parent_series_id, preregistration, environment, measurement_checkout, dependency_pins, arms, allocations, planned_execution, actual_runs, correctness_evidence, liveness, admission_telemetry, attempts |
| 3 | `fileRecord` 使用箇所 | 3 | path, size, sha256 |
| 3 | `blobRef` 使用箇所 | 3 | path, commit, sha256 |
| 4.2 | `preregistration` | 8 | core, addendum_a, addendum_b, fold_commit, errata, approval_manifest, receipt_schema, composed_core_sha256 |
| 4.2 | `preregistration.errata[]` | 5 | erratum_id, path, commit, sha256, approval_fold_commit |
| 4.3 | `environment` | 3 | env_tag, attestation_mode, attestations |
| 4.3 | `environment.attestations[]` | 4 | ordinal, profile_kind, schema_version, raw |
| 4.4 | `measurement_checkout` | 2 | repository_head, ccbench_head |
| 4.5 | `dependency_pins[]` | 2 | name, commit |
| 4.6 | `arms` | 3 | stock, mode1, modeX |
| 4.6 | `arms.{stock,mode1,modeX}` | 4 | compile, binary, built_outside_allocation, toolchain |
| 4.6 | `arms.*.compile` | 9 | source, mode_macro, configure_argv, translation_units, identity_sha256, trace_enabled, analysis_enabled, cmake_cache, compile_commands |
| 4.6 | `arms.*.compile.source` | 5 | repo_commit, ccbench_pin, base_tree_sha, patch_path, patch_sha256 |
| 4.6 | `arms.*.compile.cmake_cache` | 2 | trace, add_analysis |
| 4.6 | `arms.*.compile.translation_units` | 0 | 固定 key なし。repo-relative path の `patternProperties` のみ |
| 4.6 | `arms.*.compile.translation_units.*` | 2 | normalized_argv, sha256 |
| 4.6 | `arms.*.built_outside_allocation` | 3 | artifact_path, size, sha256 |
| 4.6 | `arms.*.toolchain` | 6 | compiler_path, compiler_version, compiler_sha256, link_argv, dynamic_deps, elf_interpreter |
| 4.6 | `arms.*.toolchain.dynamic_deps[]` | 3 | soname, resolved_path, sha256 |
| 4.7 | `allocations[]` | 16 | allocation_id, allocation_role, cluster_slot_or_null, scheduler_request_id, path_choice, path_choice_intent, node, requested_walltime_s, internal_deadline_s, started_at_monotonic_ns, ended_at_monotonic_ns, accounting_trace, exclusivity, phase_caps, phase_events, binary_rehash |
| 4.7 | `allocations[].exclusivity` | 2 | method, raw |
| 4.7 | `allocations[].phase_caps[]` | 3 | phase, cap_s, sub_cap_s_or_null |
| 4.7 | `allocations[].phase_events[]` | 3 | phase, event, monotonic_ns |
| 4.7 | `allocations[].binary_rehash[]` | 4 | point, arm, sha256, monotonic_ns |
| 4.8 | `planned_execution` | 8 | workloads, schedule_seed, schedule_algorithm, schedule_table, schedule_sha256, pilot_cluster_slots, cluster_slots, runs |
| 4.8 | `planned_execution.workloads` | 2 | W1, W2 |
| 4.8 | `planned_execution.workloads.{W1,W2}` | 3 | driver_argv, effective_flags, opt_parameters |
| 4.8 | `planned_execution.workloads.*.effective_flags` | 9 | clocks_per_us, epoch_time, extime, thread_num, ycsb_max_ope, ycsb_rmw, ycsb_rratio, ycsb_tuple_num, ycsb_zipf_skew |
| 4.8 | `planned_execution.workloads.*.opt_parameters` | 10 | ADD_ANALYSIS, BACK_OFF, KEY_SIZE, MASSTREE_USE, NO_WAIT_LOCKING_IN_VALIDATION, PARTITION_TABLE, PROCEDURE_SORT, SLEEP_READ_PHASE, VAL_SIZE, WAL |
| 4.8 | `planned_execution.cluster_slots[]` | 4 | cluster_slot, workload, block_index, permutation |
| 4.8 | `planned_execution.runs[]` | 10 | run_id, cluster_slot, workload, block_index, permutation, planned_ordinal, position, predecessor_arm, arm, preceding_wait |
| 4.8 | `planned_execution.runs[].preceding_wait` | 2 | kind, required_s |
| 4.9 | `actual_runs[]` | 19 | run_id, attempt_id, allocation_id, cluster_slot, workload, block_index, permutation, actual_ordinal, position, predecessor_arm, arm, preceding_wait, started_at_monotonic_ns, ended_at_monotonic_ns, binary_sha256, exec_witness, argv_sha256, argv_raw, run_log |
| 4.9 | `actual_runs[].preceding_wait` | 4 | kind, required_s, monotonic_start_ns, monotonic_end_ns |
| 4.9 | `actual_runs[].exec_witness` | 5 | path, inode, size, sha256, monotonic_ns |
| 4.10 | `correctness_evidence[]` | 6 | ordinal, arm, workload, build, run_scope, outputs |
| 4.10 | `correctness_evidence[].build` | 3 | source, compile, binary |
| 4.10 | `correctness_evidence[].build.source` | 5 | repo_commit, ccbench_pin, base_tree_sha, patch_path, patch_sha256 |
| 4.10 | `correctness_evidence[].build.compile` | 6 | identity_sha256, argv, trace_enabled, analysis_enabled, cmake_cache, compile_commands |
| 4.10 | `correctness_evidence[].build.compile.cmake_cache` | 2 | trace, add_analysis |
| 4.10 | `correctness_evidence[].run_scope` | 2 | allocation_id, run_ordinal |
| 4.11 | `liveness[]` | 7 | ordinal, allocation_id, probe, arm_or_null, workload_or_null, monotonic_ns, raw |
| 4.12 | `admission_telemetry[]` | 5 | ordinal, kind, receipt, fixed_inputs, ledger_evidence |
| 4.12 | `admission_telemetry[].fixed_inputs` | 3 | input_sha256, B_or_null, seed_or_null |
| 4.12 | `admission_telemetry[].ledger_evidence` | 5 | ledger_path, family_root, ordinal, reservation_entry_sha256, reservation_commit |
| 4.13 | `attempts[]` | 12 | attempt_id, cluster_slot_or_null, reason_code, replaces_attempt_id, parent_attempt_id, allocation_id, submitted_at_monotonic_ns, intent_ref, qsub_result, performance_started_marker, environment_observations, failure_evidence |
| 4.13 | `attempts[].qsub_result` | 2 | returncode, raw |
| 4.13 | `attempts[].performance_started_marker` | 4 | path, size, sha256, created_at_monotonic_ns |
| 4.13 | `attempts[].failure_evidence` | 2 | kind, pointer |
| 4.14 | `attempts[].environment_observations[]` | 11 | ordinal, scope, run_id_or_null, stat_before_raw, stat_after_raw, stat_before, stat_after, monotonic_start_ns, monotonic_end_ns, load1_diagnostic, malformed_reason |

`fileRecord` は preregistration の blob 以外の raw/artifact pointer、binary、compile commands、schedule table、run log、outputs、各 evidence pointer に再利用しています。

## 曖昧点・schema に落とさなかった制約

- 作業開始後、`record-items-v2.md` に「pilot は planned run 合計288件」という変更が入りました。schema は直接依頼および開始時文書の `runs[] == 36` に従っています。現在の変更後文書とは1箇所不一致です。
- 本文は自己完結を宣言していますが、`mode_macro`、`configure_argv`、dependency pin、`effective_flags`、`opt_parameters` の exact 値を掲載せず、追補 A `a07`/`a08`/`a09` に委ねています。推測した const は追加していません。特に `effective_flags` は key 集合だけを閉じ、値 schema は空 schema としました。
- draft-07 では、無制限長配列における discriminator ごとの「ちょうどN件」を一般には表せません。このため `attestations[]` の expected exactly 1 と、`liveness[]` の liveness_run exactly 6 は必要組合せの存在までを検査し、余分な同種要素の排除は落としています。
- `errata[].erratum_id` の field 単位一意性、各配列の ordinal 連番・欠番なしは draft-07 単独では表現できません。`errata[]` には、正当な instance を狭めない部分検査として `uniqueItems: true` を入れています。
- `malformed_reason` と raw bytes の一致、post-performance 経路2/3、pre-performance の actual run 0件・a03不成立なし、completed の planned/actual 双射は、raw解析または配列間参照を要するため schema から除外しました。
- §6 の foreign key、一意性・双射・prefix、binary非同一、実待機・観測窓、schedule再導出、台帳全履歴、時間算術、writer認可は指示どおりすべて除外しました。
- duplicate JSON key の拒否は JSON parse 前段の責務であり、schema では表現していません。

## 所有外への波及可能性

実行可能コードについて `receipt-schema-v1.json` および `t139-receipt/v1` の静的参照を検索しましたが、この新ファイルを直接読む既存 consumer は見つかりませんでした。

同名を参照する既存文書は次の6系統です。

- `docs/spool/worklog/2026-08-11-dev-wave-t139-manifest-land1-1.md`
- `output/insights/2026-08-11_t139-manifest-land1/README.md`
- `output/insights/2026-08-11_t139-manifest-land1/package.md`
- `output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md`
- `output/insights/2026-08-11_t139-manifest-land1/verbatim/s2-plan.md`
- `output/insights/2026-08-11_t139-manifest-land1/verbatim/s4-adjudication.md`

これらは package metadata、要件、worklog、過去の計画・裁定記録であり、実行時 consumer ではありません。

## 指定された4検査

1. JSON parse

```text
command: python3 -c "import json;json.load(open('/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json'))"
rc: 0
output: なし
```

2. draft-07 schema 検査

```text
command: python3 -c "import json,jsonschema;jsonschema.Draft7Validator.check_schema(json.load(open('/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json')))"
rc: 0
output: なし
```

3. object schema 走査

走査 script は指定どおり repo 外の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/check_receipt_object_schemas.py` に置きました。

```text
command: python3 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/check_receipt_object_schemas.py
rc: 0
output:
object_schema_count=51
missing_additionalProperties_false=0
missing_required=0
```

4. 最終 status

```text
command: git -C /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1 status --short
rc: 0
output:
 M output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md
?? docs/spool/worklog/2026-08-11-dev-wave-t139-manifest-land1-1.md
?? output/insights/2026-08-11_t139-manifest-land1/README.md
?? output/insights/2026-08-11_t139-manifest-land1/package.md
?? output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json
?? output/insights/2026-08-11_t139-manifest-land1/verbatim/
```

したがって command 自体は rc 0 ですが、「新規1ファイルだけ」という検査条件は不成立です。私が repo 内で書いたのは `receipt-schema-v1.json` だけです。pytest は実行していません。

## 総括

書いた行数: 1259  
object schema の総数: 51  
`additionalProperties: false` を持たない object schema: 0  
要件文書との 1:1 が崩れている箇所: 1（作業中に変更された `planned_execution.runs` の件数規定）