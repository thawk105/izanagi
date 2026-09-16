# 受入全走 post-1 (tip cb64c51ed、2026-09-17 01:33〜01:44 JST) の赤 2 node と親の帰属判定

集計: 2 failed / 24401 passed / 67 skipped (3 shard、計算ノード)。受入 wrapper は走行後の clean-tree 検査 (`postrun-clean`) で rc=70 を返した。
その原因は親が走行中に `output/insights/.../verbatim/` (untracked 13 file) を書いたことで、これは親起因の手順誤りであり、再走で解消する。

## 赤 1: `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`

```
KeyError: _BuildSink(relative_path='orchestrator/campaign/s8b_oracle_driver.py', scope='<module>.run_block', lineno=1783, kind='campaign')
        s8b_sink = _BuildSink(
            "orchestrator/campaign/s8b_oracle_driver.py",
            "<module>.run_block",
            1783,
            "campaign",
        )
        ...
>       assert classifications[s8b_sink] == Counter({"covered": 38})
E       KeyError: ...
orchestrator/tests/test_ccbench_spawn_sites.py:2990: KeyError
```

親の帰属判定: **本 wave 起因 (行番号 pin の追随漏れ)。** 本 wave の production 差分で `run_block` 内の `result = pipeline.evaluate(` が
旧 1783 行 → 1775 行へ移った (base `1042a1bc9` の 1783 行と現 HEAD の 1775 行が同一内容であることを親が実測)。
過去 wave (T-548 `0165027e0`) も同 test の行番号 pin を production の行シフトに合わせて更新している。sink の集合・分類件数は不変。

## 赤 2: `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`

```
AssertionError: 素の runner で 0 件実行の偽緑になりうる (自走 harness も pytest 専用 allowlist 記載も無い):
['test_s8b_gate_core_exact_launch_validated.py']. _run()/__main__ を足すか README の allowlist に追加せよ
orchestrator/tests/test_plain_runner_coverage.py:72: AssertionError
```

親の帰属判定: **本 wave 起因 (新規 test file の allowlist 未登録)。** 新規 file は pytest fixture (`tmp_path` / `capsys`) と parametrize に
依存する pytest 専用 file なので、`orchestrator/tests/README.md` の `PYTEST_ONLY_ALLOWLIST_START`〜`END` に追加する
(`- test_s8b_floor_stats.py` の直後)。自走 harness は足さない。
