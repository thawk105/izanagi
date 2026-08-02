[mutation_harness.py](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/mutation_harness.py) を作成しました。repo 内は変更していません。構文解析のみ `AST_OK` を確認済みです。

## Anchor と一意性

すべて現行 working tree で逐語一致 `1` 件です。

### M1 — `p3_s4_loop_trigger_gating.py:287`

```python
    return site in {site_policy.OTHER, site_policy.PEGASUS_COMPUTE}
```

### M3-11 — `p3_s4_loop_trigger_gating.py:79`

```python
    site_policy.PEGASUS_COMPUTE: "pegasus",
```

### M4 — `loop.py:79`

```python
    receipt = execution_guard.attest_and_build_receipt(env_contract, verified)
```

### M5 — `loop.py:79`

```python
    receipt = execution_guard.attest_and_build_receipt(env_contract, verified)
```

### M6 — `p3_s4_loop_trigger_gating.py:313`

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

### M7 — `buildcache.py:234`

```python
        "site": site,
```

### M8-9 — `buildcache.py:235`

```python
        "dependency_prefix": dependency_prefix,
```

### M10 — `buildcache.py:399`

```python
    ] + prefix_define + defines
```

### M12 — 2 consumer

`loop.py:162`、逐語一致 `1` 件:

```python
            _, resolved_cxx = _compilers_for_current_site()
            if resolved_cxx == _DEFAULT_CXX:
                src_tok = source_digest.resolve(g, cfg.ccbench_commit, ccbench_dir)
            else:
                src_tok = source_digest.resolve(
                    g, cfg.ccbench_commit, ccbench_dir, resolved_cxx,
                )
```

`pipeline.py:533`、逐語一致 `1` 件:

```python
            _, resolved_cxx = _compilers_for_current_site()
            if resolved_cxx == _DEFAULT_CXX:
                src_tok = source_digest.resolve(genome, ccbench_commit, ccbench_dir)
            else:
                src_tok = source_digest.resolve(
                    genome, ccbench_commit, ccbench_dir, resolved_cxx,
                )
```

### M13 — `buildcache.py:529`

```python
        site=actual_site, dependency_prefix=effective_dependency_prefix,
```

POS は無変異のため anchor はありません。

## 期待 node

- M1
  - `test_p3_s4_loop_trigger_gating.py::test_site_admission_matrix`
  - `test_p3_s4_loop_trigger_gating.py::test_measurement_sink_admits_compute_with_pegasus_contract_and_identity`
- M3-11
  - `test_p3_s4_loop_trigger_gating.py::test_campaign_identity_is_unchanged_for_other_and_split_for_compute`
  - `test_p3_s4_loop_trigger_gating.py::test_measurement_sink_admits_compute_with_pegasus_contract_and_identity`
- M4
  - `test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink`
- M5
  - `test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink`
- M6
  - `test_p3_s4_loop_trigger_gating.py::test_compute_existing_loop_state_rejected_after_neutralized_freshness`
- M7
  - `test_buildcache_v2.py::test_m7_v2_actual_site_change_is_cache_miss`
- M8-9
  - `test_buildcache_v2.py::test_m8_v2_explicit_dependency_prefix_change_is_cache_miss`
  - `test_buildcache_v2.py::test_m9_v2_ambient_dependency_prefix_change_is_cache_miss`
- M10
  - `test_buildcache_v2.py::test_m10_explicit_prefix_is_one_argv_token_and_removes_ambient_env`
- M12
  - `test_campaign.py::test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix`
  - `test_campaign.py::test_m12_pipeline_compute_uses_gxx_for_source_digest_and_v2_builds`
- M13
  - `test_buildcache_v2.py::test_m13_caller_injected_site_does_not_change_v2_identity`
- POS
  - OTHER legacy、campaign identity、legacy pipeline、legacy cache の正例 4 node

## 実行方法

```bash
python3 /home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/mutation_harness.py
```

harness は `flock`、累積置換時の一意性検査、`finally` 復元と内容比較、変異別 timeout、計算ノード job stdout 全文からの赤 node 抽出、SURVIVED diff、JSON/Markdown 台帳の逐次保存を実装しています。

## 実行状況

harness、pytest、Pegasus dispatch は実行していません。したがって kill 数やテスト緑は報告しません。`mutation-ledger.json` と `.md` もまだ生成されていません。

## 総括

- 裁定済み 10 mutant と無変異 POS を 1 本の harness に収録した。
- M2/M14 は除外し、M3-11・M8-9 は統合した。
- M5 は `loop` の実 attestation sink を強制例外へ再照準した。
- repo 内の既存 working tree 差分には触れていない。
- 実走と台帳生成は親に残した。