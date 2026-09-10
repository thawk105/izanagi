# 変異 matrix 結果 (本走)

- anchor commit: `a9cb2ab4c821d139e0da039b420401c8637e1643`
- spec sha256: `db42f0d0467e77911a16cd7a08a46ac66968b950fdcd1dfeb66cba58da055e97`
- 走行日: 2026-08-31T16:30:55.576577+00:00
- runner: `{'command': ['python3', 'tools/run_tests.py', '--force-dispatch', 'orchestrator/tests/test_s8b_compiler_input.py', 'orchestrator/tests/test_buildcache_v2.py', 'orchestrator/tests/test_s8b_binary_admission.py', 'orchestrator/tests/test_s8b_floor_campaign.py', '-q', '-rf', '-p', 'no:cacheprovider'], 'dispatch_entrypoint_path': '/work/1/SFC/tanab/mutation-scratch-t2027d1192/.izanagi-mutation-worktree/repo/tools/pegasus/dispatch_compute.py', 'dispatch_entrypoint_sha256': 'be9a55c2867e988804900a2b32f9b9a17676640aa8a2b113c6db09ac62a83c62', 'dispatch_head_blob_sha256': 'be9a55c2867e988804900a2b32f9b9a17676640aa8a2b113c6db09ac62a83c62', 'entrypoint_kind': 'izanagi-run-tests', 'entrypoint_path': '/work/1/SFC/tanab/mutation-scratch-t2027d1192/.izanagi-mutation-worktree/repo/tools/run_tests.py', 'entrypoint_sha256': '65f7f84f36827d912556b5537cc31130edb815a521895bb6d89163c6d7ab1523', 'executable_path': '/usr/bin/python3.10', 'executable_sha256': '7d51cd6b48b521277f5caa4610a82126e315fa2be4df069823a8b1eeb5bd4a86', 'head_blob_sha256': '65f7f84f36827d912556b5537cc31130edb815a521895bb6d89163c6d7ab1523', 'pytest_distribution_sha256': '57e75bdc6fae07156ff0fd2d58eee5ac82d236cfaf81d454d46f09ebc86cb1d1', 'repo_path': 'tools/run_tests.py', 'repo_tree': 'c8c56a791103006ae53cb546d5aad47583703a09', 'runner_mode': 'dispatch'}`
- runner argv: `python3 tools/run_tests.py --force-dispatch test_s8b_compiler_input.py test_buildcache_v2.py test_s8b_binary_admission.py test_s8b_floor_campaign.py -q -rf`

## 集計

```json
{"KILLED": 10, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0, "completed": 10, "matching": 10, "recorded": 10, "registered": 10}
```

baseline の失敗 node: なし (緑)

## 変異ごとの判定と期待 node (完全集合)

### M1-SCHEMA-PIN-OMITTED — KILLED

- 編集面: `orchestrator/campaign/buildcache.py`
- 期待 node:
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_collects_manifest_before_staging_discard`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_descriptor_runs_gate_inside_build_and_returns_both_digests`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_fresh_completion_and_result_expose_compiler_input_manifest`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_rebinds_fetchcontent_inputs_to_current_root`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_rejects_completion_without_compiler_input_proof`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_revalidates_compiler_input_bytes_without_rebuilding`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_validation_failure_never_rebuilds[hash]`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_validation_failure_never_rebuilds[missing]`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_validation_failure_never_rebuilds[symlink]`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_identity_optional_snapshot_preserves_legacy_digest_and_separates_proof`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_rejects_snapshot_changed_during_build`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_schema_pin_separates_legacy_completion_without_fallback`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_snapshot_only_bound_build_collects_without_masstree_keys`

### M2-FETCH-ROOT-AS-FILESYSTEM — KILLED

- 編集面: `orchestrator/campaign/s8b_compiler_input.py`
- 期待 node:
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_current_fetchcontent_bytes_drift_is_rejected`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_current_fetchcontent_nonregular_leaf_is_rejected`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_current_fetchcontent_symlink_component_is_rejected[component]`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_current_fetchcontent_symlink_component_is_rejected[leaf]`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_manifest_classifies_fetchcontent_root_relative`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_missing_current_fetchcontent_input_is_rejected`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_rejects_noncanonical_root_tag`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_validator_rebinds_fetchcontent_inputs_to_current_root`

### M3-CURRENT-BASE-IGNORED — KILLED

- 編集面: `orchestrator/campaign/buildcache.py`
- 期待 node:
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_rebinds_fetchcontent_inputs_to_current_root`

### M7-ROOT-CANONICALITY-SKIPPED — KILLED

- 編集面: `orchestrator/campaign/s8b_compiler_input.py`
- 期待 node:
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_rejects_noncanonical_root_tag`

### M8-RECEIPT-RECHECK-OMITTED — KILLED

- 編集面: `orchestrator/campaign/s8b_binary_admission.py`
- 期待 node:
  - `orchestrator/tests/test_s8b_binary_admission.py::test_issue_v2_receipt_rechecks_current_fetchcontent_root`
  - `orchestrator/tests/test_s8b_binary_admission.py::test_portable_validator_accepts_v1_and_v2_without_live_paths`
  - `orchestrator/tests/test_s8b_binary_admission.py::test_portable_validator_rejects_nonexact_v2_manifest_after_resealing`
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`

### M10-NON-SORT-CURRENT-ROOT-OMITTED — KILLED

- 編集面: `orchestrator/campaign/s8b_floor_campaign.py`
- 期待 node:
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`

### M11-DOT-PATH-ACCEPTED — KILLED

- 編集面: `orchestrator/campaign/s8b_compiler_input.py`
- 期待 node:
  - `orchestrator/tests/test_s8b_compiler_input.py::test_v2_manifest_rejects_dot_path_as_compiler_input_error`

### M12-MASSTREE-ROOT-ALWAYS-REQUIRED — KILLED

- 編集面: `orchestrator/campaign/buildcache.py`
- 期待 node:
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_collects_manifest_before_staging_discard`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_fresh_completion_and_result_expose_compiler_input_manifest`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_rejects_completion_without_compiler_input_proof`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_hit_revalidates_compiler_input_bytes_without_rebuilding`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_rejects_snapshot_changed_during_build`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_schema_pin_separates_legacy_completion_without_fallback`
  - `orchestrator/tests/test_buildcache_v2.py::test_v2_snapshot_only_bound_build_collects_without_masstree_keys`

### M13-SYMLINK-ROOT-REJECTED — KILLED

- 編集面: `orchestrator/campaign/s8b_compiler_input.py`
- 期待 node:
  - `orchestrator/tests/test_s8b_compiler_input.py::test_symlink_spelled_root_collects_and_validates_identically`

### M14-DOUBLE-SLASH-ACCEPTED — KILLED

- 編集面: `orchestrator/campaign/s8b_compiler_input.py`
- 期待 node:
  - `orchestrator/tests/test_s8b_compiler_input.py::test_double_slash_input_matches_single_slash_manifest_and_digest`
  - `orchestrator/tests/test_s8b_compiler_input.py::test_double_slash_unknown_fetchcontent_root_is_compiler_input_error`

## probe 走行 (期待 node の採取)

```json
{"KILLED": 0, "MISMATCH": 10, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0, "completed": 10, "matching": 0, "recorded": 10, "registered": 10}
```

- probe spec sha256: `f603760a88f58d9db4c3d19b189cc5a0925db3da8eb34b97e4e2af8fed449ca6`
- 全件 SURVIVED 期待で登録したので MISMATCH 10 は期待どおりであり、これが観測 node の採取である (`DW-M07`)。
- 生結果は repo 外の job directory に保全してある。

