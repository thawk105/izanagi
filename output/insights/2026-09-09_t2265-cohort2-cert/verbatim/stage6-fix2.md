## 変更

- [test_ccbench_spawn_sites.py:922](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:922): `3375` → `3657`
- [test_ccbench_spawn_sites.py:934](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:934): `3749` → `4029`
- [test_ccbench_spawn_sites.py:2674](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:2674): `3375` → `3657`
- [test_ccbench_spawn_sites.py:2678](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:2678): `3749` → `4029`

行番号以外は変更していません。

## 実測

```text
$ grep -n "buildcache.build(" tools/pegasus/probes/t2187_adaptive_const_probe.py
3657:                    return buildcache.build(
4029:                build = buildcache.build(
```

## テスト

次の3 nodeidは実装済み・未実走です。

```text
test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink
test_define_sink_cross_product_classifies_t2155_production_sinks_exactly
test_define_sink_cross_product_has_no_unreviewed_ungated_member
```

`tools/run_tests.py` は rc=16 で終了しました。`qstat -Q preflight rc=1` による dispatch infrastructure failureで、`child_started=false`、`child_rc=null` でした。

## 総括

4箇所の行番号 pinだけを現在の sink位置へ更新しました。  
grep実測との一致を確認済みです。  
テストはdispatch障害のため未実走です。