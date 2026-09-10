# T-277 mutation ledger

- 開始: 2026-08-01T16:01:56.119151+00:00
- 状態: COMPLETED
- repo: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure`

## anchor 事前検査

### M1 replacement 1

- 対象: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:287`
- 一致数: `1` (一意)
- old:

```python
    return site in {site_policy.OTHER, site_policy.PEGASUS_COMPUTE}
```

- new:

```python
    return site in {site_policy.OTHER}
```

### M3-11 replacement 1

- 対象: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:79`
- 一致数: `1` (一意)
- old:

```python
    site_policy.PEGASUS_COMPUTE: "pegasus",
```

- new:

```python
    site_policy.PEGASUS_COMPUTE: ENV_TAG,
```

### M4 replacement 1

- 対象: `orchestrator/campaign/loop.py:79`
- 一致数: `1` (一意)
- old:

```python
    receipt = execution_guard.attest_and_build_receipt(env_contract, verified)
```

- new:

```python
    receipt = {}
```

### M5 replacement 1

- 対象: `orchestrator/campaign/loop.py:79`
- 一致数: `1` (一意)
- old:

```python
    receipt = execution_guard.attest_and_build_receipt(env_contract, verified)
```

- new:

```python
    raise execution_guard.ExecutionGuardError("M5 forced attestation failure")
```

### M6 replacement 1

- 対象: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:313`
- 一致数: `1` (一意)
- old:

```python
    if contract.isolation_policy.allow_resume:
        return
    existing = [
        path for path in (
            layout.lock_file, L.loop_state_path(layout), layout.wal_file,
            _provenance_path(layout),
        )
        if os.path.lexists(path)
    ]
    if existing:
        raise execution_guard.ExecutionGuardError(
            f"env {contract.env_tag} は allow_resume=False: 既存 campaign artifact を拒否: "
            + ", ".join(existing)
        )
```

- new:

```python
    return
```

### M7 replacement 1

- 対象: `orchestrator/campaign/buildcache.py:234`
- 一致数: `1` (一意)
- old:

```python
        "site": site,
```

- new:

```python

```

### M8-9 replacement 1

- 対象: `orchestrator/campaign/buildcache.py:235`
- 一致数: `1` (一意)
- old:

```python
        "dependency_prefix": dependency_prefix,
```

- new:

```python

```

### M10 replacement 1

- 対象: `orchestrator/campaign/buildcache.py:399`
- 一致数: `1` (一意)
- old:

```python
    ] + prefix_define + defines
```

- new:

```python
    ] + defines
```

### M12 replacement 1

- 対象: `orchestrator/campaign/loop.py:162`
- 一致数: `1` (一意)
- old:

```python
            _, resolved_cxx = _compilers_for_current_site()
            if resolved_cxx == _DEFAULT_CXX:
                src_tok = source_digest.resolve(g, cfg.ccbench_commit, ccbench_dir)
            else:
                src_tok = source_digest.resolve(
                    g, cfg.ccbench_commit, ccbench_dir, resolved_cxx,
                )
```

- new:

```python
            src_tok = source_digest.resolve(g, cfg.ccbench_commit, ccbench_dir)
```

### M12 replacement 2

- 対象: `orchestrator/campaign/pipeline.py:533`
- 一致数: `1` (一意)
- old:

```python
            _, resolved_cxx = _compilers_for_current_site()
            if resolved_cxx == _DEFAULT_CXX:
                src_tok = source_digest.resolve(genome, ccbench_commit, ccbench_dir)
            else:
                src_tok = source_digest.resolve(
                    genome, ccbench_commit, ccbench_dir, resolved_cxx,
                )
```

- new:

```python
            src_tok = source_digest.resolve(genome, ccbench_commit, ccbench_dir)
```

### M13 replacement 1

- 対象: `orchestrator/campaign/buildcache.py:529`
- 一致数: `1` (一意)
- old:

```python
        site=actual_site, dependency_prefix=effective_dependency_prefix,
```

- new:

```python
        site=resolved_site, dependency_prefix=effective_dependency_prefix,
```

## 実行台帳

| ID | 対象 file:line | rc | 赤 node 数 | 判定 | 根拠 |
|---|---|---:|---:|---|---|
| M1 | orchestrator/campaign/p3_s4_loop_trigger_gating.py:287 | 1 | 16 | KILLED | compute admission 正例が拒否へ変わる受理集合の縮小; 期待 node 一致=['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_measurement_sink_admits_compute_with_pegasus_contract_and_identity', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_site_admission_matrix'] |
| M3-11 | orchestrator/campaign/p3_s4_loop_trigger_gating.py:79 | 1 | 12 | KILLED | 同じ閉 map に束縛された compute contract tag と campaign ID がともに変わる; 期待 node 一致=['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_campaign_identity_is_unchanged_for_other_and_split_for_compute'] |
| M4 | orchestrator/campaign/loop.py:79 | 1 | 1 | KILLED | required contract の measurement 前 attestation 順序が欠落する; 期待 node 一致=['orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink'] |
| M5 | orchestrator/campaign/loop.py:79 | 1 | 1 | KILLED | 実 sink の強制失敗が layout/evaluate 前に伝播し required 成功正例を拒否する; 期待 node 一致=['orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink'] |
| M6 | orchestrator/campaign/p3_s4_loop_trigger_gating.py:313 | 1 | 6 | KILLED | freshness を neutral 化した fixture で resume の受理集合が拡大する; 期待 node 一致=['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_existing_loop_state_rejected_after_neutralized_freshness'] |
| M7 | orchestrator/campaign/buildcache.py:234 | 1 | 1 | KILLED | actual site 差の cache miss が cache hit へ変わる; 期待 node 一致=['orchestrator/tests/test_buildcache_v2.py::test_m7_v2_actual_site_change_is_cache_miss'] |
| M8-9 | orchestrator/campaign/buildcache.py:235 | 1 | 4 | KILLED | 同一 pre-image field が担う explicit/ambient prefix binding がともに消える; 期待 node 一致=['orchestrator/tests/test_buildcache_v2.py::test_m8_v2_explicit_dependency_prefix_change_is_cache_miss', 'orchestrator/tests/test_buildcache_v2.py::test_m9_v2_ambient_dependency_prefix_change_is_cache_miss'] |
| M10 | orchestrator/campaign/buildcache.py:399 | 1 | 2 | KILLED | explicit dependency prefix が configure subprocess 条件から消える; 期待 node 一致=['orchestrator/tests/test_buildcache_v2.py::test_m10_explicit_prefix_is_one_argv_token_and_removes_ambient_env'] |
| M12 | orchestrator/campaign/loop.py:162<br>orchestrator/campaign/pipeline.py:533 | 1 | 2 | KILLED | compute identity の両 consumer で source_digest へ g++ が渡らなくなる; 期待 node 一致=['orchestrator/tests/test_campaign.py::test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix', 'orchestrator/tests/test_campaign.py::test_m12_pipeline_compute_uses_gxx_for_source_digest_and_v2_builds'] |
| M13 | orchestrator/campaign/buildcache.py:529 | 1 | 1 | KILLED | caller 注入 site が同一 actual site の digest を分岐させる; 期待 node 一致=['orchestrator/tests/test_buildcache_v2.py::test_m13_caller_injected_site_does_not_change_v2_identity'] |
| POS | (変異なし) | 0 | 0 | SURVIVED | 無変異の対象 3 test file が全緑なら過剰拒否なしの正例 SURVIVED |

### M1 — KILLED

- 期待 node: `['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_site_admission_matrix', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_measurement_sink_admits_compute_with_pegasus_contract_and_identity']`
- 実 node: `['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_site_admission_matrix', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[diff-quarantine]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[syntax]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_rejects_wal_only_crash_tail_without_mutation', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[auditor]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_quarantine_and_audit_raises_on_digest_mismatch', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_quarantine_and_audit_dry_pass_when_clean_and_digest_matches', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_default_path_resolves_pegasus_contract_from_site_policy', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_clean_dry_pass_still_admitted_on_pegasus', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_reject_sink_compute_records_pegasus_without_attestation[diff-quarantine]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_forwards_required_contract_and_records_sink_receipt', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_reject_sink_compute_records_pegasus_without_attestation[auditor]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_reject_sink_compute_records_pegasus_without_attestation[syntax]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_measurement_sink_admits_compute_with_pegasus_contract_and_identity', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_drive_entry_stop_and_provenance', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_existing_loop_state_rejected_after_neutralized_freshness']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/2e590157ff56b6defbafdd8f4191c71b/izdw-2e590157ff.o877643`
- timeout: `False`
- 復元内容比較: `True`

### M3-11 — KILLED

- 期待 node: `['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_campaign_identity_is_unchanged_for_other_and_split_for_compute', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_measurement_sink_admits_compute_with_pegasus_contract_and_identity']`
- 実 node: `['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[auditor]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[syntax]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[diff-quarantine]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_campaign_identity_is_unchanged_for_other_and_split_for_compute', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_clean_dry_pass_still_admitted_on_pegasus', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_default_path_resolves_pegasus_contract_from_site_policy', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_reject_sink_compute_records_pegasus_without_attestation[auditor]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_reject_sink_compute_records_pegasus_without_attestation[syntax]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_reject_sink_compute_records_pegasus_without_attestation[diff-quarantine]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_rejects_wal_only_crash_tail_without_mutation', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_forwards_required_contract_and_records_sink_receipt', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_drive_entry_stop_and_provenance']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/a3bcacd47bdbbeff1da99c6452048220/izdw-a3bcacd47b.o877646`
- timeout: `False`
- 復元内容比較: `True`

### M4 — KILLED

- 期待 node: `['orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink']`
- 実 node: `['orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/3536ddc88cf6502cdf1013f585a451dd/izdw-3536ddc88c.o877647`
- timeout: `False`
- 復元内容比較: `True`

### M5 — KILLED

- 期待 node: `['orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink']`
- 実 node: `['orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/7b849951d6d1ef88eb480d1d75df632c/izdw-7b849951d6.o877649`
- timeout: `False`
- 復元内容比較: `True`

### M6 — KILLED

- 期待 node: `['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_existing_loop_state_rejected_after_neutralized_freshness']`
- 実 node: `['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[syntax]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[auditor]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_drive_entry_stop_and_provenance', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_precedes_all_reject_writes[diff-quarantine]', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_no_resume_rejects_wal_only_crash_tail_without_mutation', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_compute_existing_loop_state_rejected_after_neutralized_freshness']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/f90cb8a80f368d90b5b36274f05e9aba/izdw-f90cb8a80f.o877650`
- timeout: `False`
- 復元内容比較: `True`

### M7 — KILLED

- 期待 node: `['orchestrator/tests/test_buildcache_v2.py::test_m7_v2_actual_site_change_is_cache_miss']`
- 実 node: `['orchestrator/tests/test_buildcache_v2.py::test_m7_v2_actual_site_change_is_cache_miss']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/392acd1e7b119c9f599ca81f7a947f97/izdw-392acd1e7b.o877651`
- timeout: `False`
- 復元内容比較: `True`

### M8-9 — KILLED

- 期待 node: `['orchestrator/tests/test_buildcache_v2.py::test_m8_v2_explicit_dependency_prefix_change_is_cache_miss', 'orchestrator/tests/test_buildcache_v2.py::test_m9_v2_ambient_dependency_prefix_change_is_cache_miss']`
- 実 node: `['orchestrator/tests/test_buildcache_v2.py::test_m9_v2_ambient_dependency_prefix_change_is_cache_miss', 'orchestrator/tests/test_buildcache_v2.py::test_explicit_relative_prefix_is_bound_to_effective_cwd', 'orchestrator/tests/test_buildcache_v2.py::test_m8_v2_explicit_dependency_prefix_change_is_cache_miss', 'orchestrator/tests/test_buildcache_v2.py::test_ambient_prefix_path_list_encoding_is_injective']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/fff107d74c039850971529c871d10c38/izdw-fff107d74c.o877652`
- timeout: `False`
- 復元内容比較: `True`

### M10 — KILLED

- 期待 node: `['orchestrator/tests/test_buildcache_v2.py::test_m10_explicit_prefix_is_one_argv_token_and_removes_ambient_env']`
- 実 node: `['orchestrator/tests/test_buildcache_v2.py::test_explicit_relative_prefix_is_bound_to_effective_cwd', 'orchestrator/tests/test_buildcache_v2.py::test_m10_explicit_prefix_is_one_argv_token_and_removes_ambient_env']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/446de104d18fd7a4d3c56181fd4f26d9/izdw-446de104d1.o877653`
- timeout: `False`
- 復元内容比較: `True`

### M12 — KILLED

- 期待 node: `['orchestrator/tests/test_campaign.py::test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix', 'orchestrator/tests/test_campaign.py::test_m12_pipeline_compute_uses_gxx_for_source_digest_and_v2_builds']`
- 実 node: `['orchestrator/tests/test_campaign.py::test_m12_pipeline_compute_uses_gxx_for_source_digest_and_v2_builds', 'orchestrator/tests/test_campaign.py::test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/5d6dfb90bd538ab52e798ebb59a4d5f1/izdw-5d6dfb90bd.o877654`
- timeout: `False`
- 復元内容比較: `True`

### M13 — KILLED

- 期待 node: `['orchestrator/tests/test_buildcache_v2.py::test_m13_caller_injected_site_does_not_change_v2_identity']`
- 実 node: `['orchestrator/tests/test_buildcache_v2.py::test_m13_caller_injected_site_does_not_change_v2_identity']`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/b9cf06e39290730096892212b5bff49d/izdw-b9cf06e392.o877655`
- timeout: `False`
- 復元内容比較: `True`

### POS — SURVIVED

- 期待 node: `['orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_contract_sentinel_flows_to_run_campaign', 'orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_campaign_identity_is_unchanged_for_other_and_split_for_compute', 'orchestrator/tests/test_campaign.py::test_pipeline_green_commits_with_fitness', 'orchestrator/tests/test_buildcache_v2.py::test_v2_never_hits_legacy_entry']`
- 実 node: `[]`
- job stdout 正本: `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/output/pegasus-dispatch/8a2c0799d594441ea255ed3b0bfb35f5/izdw-8a2c0799d5.o877656`
- timeout: `False`
- 復元内容比較: `True`
